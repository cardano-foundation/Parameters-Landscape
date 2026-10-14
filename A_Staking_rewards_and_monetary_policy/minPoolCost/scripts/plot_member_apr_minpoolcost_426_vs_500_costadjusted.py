#!/usr/bin/env python3
"""
Member APR around the minPoolCost reduction (epoch 426 -> 500).

Baseline:
  epoch-426 stake, pledged/declared pledge, margin, and declared cost;
  protocol parameters fixed at T, R, a0, k=500.

Counterfactual (survivors only):
  same epoch-426 stake, pledge, and margin;
  declared cost replaced by each pool's epoch-500 declared cost.

  ρ = (1 - m) * max(f(σ, p) - c, 0) / σ
  APR ≈ 73 * ρ

Writes CSV, summary MD, and a two-panel APR scatter plot.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pastreduction_common import load_active

DIR = Path(__file__).resolve().parent
OUT_CSV = DIR / "member_apr_minpoolcost_426_vs_500_costadjusted.csv"
OUT_SUMMARY = DIR / "member_apr_minpoolcost_426_vs_500_costadjusted_summary.csv"
OUT_MD = DIR / "member_apr_minpoolcost_426_vs_500_costadjusted.md"
OUT_PLOT = DIR / "member_apr_minpoolcost_426_vs_500_costadjusted.png"

FONT_SIZE = 12
A0 = 0.3
K = 500
T_ADA = 36.01e9
R_ADA = 21.6e6
Z0_ADA = T_ADA / K
EPOCHS_PER_YEAR = 73.0
COLOR_SURVIVOR = "#2a9d8f"
COLOR_EXIT = "#b23a3a"
COLOR_ZERO = "#6b7280"


def load_epoch(epoch: int) -> pd.DataFrame:
    df = load_active(epoch)
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
        errors="coerce",
    )
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": stake.fillna(0.0) / 1e6,
            "pledge_ada": pd.to_numeric(
                df["pool_update.active.pledge"], errors="coerce"
            )
            / 1e6,
            "margin": pd.to_numeric(
                df["pool_update.active.margin"], errors="coerce"
            ),
            "fixed_cost_ada": pd.to_numeric(
                df["pool_update.active.fixed_cost"], errors="coerce"
            )
            / 1e6,
        }
    ).set_index("pool_id")


def gross_pool_reward(sigma: np.ndarray, pledge: np.ndarray) -> np.ndarray:
    sigma = np.asarray(sigma, dtype=float)
    pledge = np.asarray(pledge, dtype=float)
    sigma_t = np.minimum(np.maximum(sigma, 0.0), Z0_ADA)
    pledge_t = np.minimum(np.minimum(np.maximum(pledge, 0.0), Z0_ADA), sigma_t)
    inner = sigma_t - pledge_t * (Z0_ADA - sigma_t) / Z0_ADA
    return (R_ADA / T_ADA) / (1.0 + A0) * (
        sigma_t + A0 * pledge_t * inner / Z0_ADA
    )


def member_apr(
    sigma: np.ndarray,
    pledge: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    f = gross_pool_reward(sigma, pledge)
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    rho = np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)
    return f, rho, EPOCHS_PER_YEAR * rho


def positive_summary(apr: pd.Series) -> tuple[int, int, float, float]:
    observed = apr.dropna()
    positive = observed[observed > 0]
    return (
        int(len(observed)),
        int(len(positive)),
        float(100.0 * positive.median()) if len(positive) else float("nan"),
        float(100.0 * positive.mean()) if len(positive) else float("nan"),
    )


def plot_points(
    ax: plt.Axes,
    frame: pd.DataFrame,
    apr_column: str,
    color: str,
    label: str,
    marker: str = "o",
) -> None:
    observed = frame.dropna(subset=[apr_column, "sigma_ada_426"])
    positive = observed[observed[apr_column] > 0]
    zero = observed[observed[apr_column] <= 0]
    ax.scatter(
        positive["sigma_ada_426"] / 1e6,
        100.0 * positive[apr_column],
        s=16,
        alpha=0.4,
        color=color,
        marker=marker,
        edgecolors=None if marker == "x" else "none",
        label=f"{label}, return > 0 (n={len(positive)})",
    )
    if len(zero):
        ax.scatter(
            zero["sigma_ada_426"] / 1e6,
            np.full(len(zero), 0.055),
            s=13,
            alpha=0.3,
            color=COLOR_ZERO if marker == "o" else color,
            marker=marker,
            edgecolors=None if marker == "x" else "none",
            label=f"{label}, return = 0 (n={len(zero)})",
        )


def main() -> None:
    e426 = load_epoch(426)
    e500 = load_epoch(500)

    # Baseline sample: Active epoch-426 pools with usable fields.
    baseline = e426[
        (e426["sigma_ada"] > 0)
        & e426["margin"].notna()
        & e426["fixed_cost_ada"].notna()
        & e426["pledge_ada"].notna()
    ].copy()

    survivors_ids = baseline.index.intersection(e500.index)
    exit_ids = baseline.index.difference(e500.index)
    survivors = baseline.loc[survivors_ids].copy()
    exits = baseline.loc[exit_ids].copy()

    # Epoch-500 costs for survivors (cost-adjusted counterfactual).
    cost_500 = e500.loc[survivors_ids, "fixed_cost_ada"]
    margin_500 = e500.loc[survivors_ids, "margin"]
    cost_ok = cost_500.notna()
    survivors = survivors.loc[cost_ok]
    cost_500 = cost_500.loc[cost_ok]
    margin_500 = margin_500.loc[cost_ok]

    sigma = baseline["sigma_ada"].to_numpy()
    pledge = baseline["pledge_ada"].to_numpy()
    cost_426 = baseline["fixed_cost_ada"].to_numpy()
    margin_426 = baseline["margin"].to_numpy()
    f_base, rho_base, apr_base = member_apr(sigma, pledge, cost_426, margin_426)

    sigma_s = survivors["sigma_ada"].to_numpy()
    pledge_s = survivors["pledge_ada"].to_numpy()
    margin_s = survivors["margin"].to_numpy()
    cost_s426 = survivors["fixed_cost_ada"].to_numpy()
    cost_s500 = cost_500.to_numpy()
    f_cf, rho_cf, apr_cf = member_apr(sigma_s, pledge_s, cost_s500, margin_s)

    out = pd.DataFrame(
        {
            "pool_id": baseline.index,
            "ticker": baseline["ticker"].to_numpy(),
            "survives_to_500": baseline.index.isin(survivors.index),
            "sigma_ada_426": sigma,
            "declared_pledge_ada_426": pledge,
            "fixed_cost_ada_426": cost_426,
            "margin_426": margin_426,
            "f_ada_epoch426_costs": f_base,
            "member_return_per_ada_epoch426_costs": rho_base,
            "member_apr_simple_epoch426_costs": apr_base,
        },
        index=baseline.index,
    )
    for col in [
        "fixed_cost_ada_500",
        "margin_500",
        "f_ada_costadjusted",
        "member_return_per_ada_costadjusted",
        "member_apr_simple_costadjusted",
        "delta_member_apr_simple",
        "cost_changed",
        "margin_changed",
    ]:
        out[col] = np.nan
    out["cost_changed"] = pd.Series(pd.NA, index=out.index, dtype="boolean")
    out["margin_changed"] = pd.Series(pd.NA, index=out.index, dtype="boolean")

    out.loc[survivors.index, "fixed_cost_ada_500"] = cost_s500
    out.loc[survivors.index, "margin_500"] = margin_500.to_numpy()
    out.loc[survivors.index, "f_ada_costadjusted"] = f_cf
    out.loc[survivors.index, "member_return_per_ada_costadjusted"] = rho_cf
    out.loc[survivors.index, "member_apr_simple_costadjusted"] = apr_cf
    out.loc[survivors.index, "delta_member_apr_simple"] = (
        apr_cf - out.loc[survivors.index, "member_apr_simple_epoch426_costs"].to_numpy()
    )
    out.loc[survivors.index, "cost_changed"] = cost_s500 != cost_s426
    out.loc[survivors.index, "margin_changed"] = (
        margin_500.to_numpy() != margin_s
    )
    out.to_csv(OUT_CSV, index=False)

    apr_col_base = "member_apr_simple_epoch426_costs"
    apr_col_cf = "member_apr_simple_costadjusted"
    rows = [
        ("Epoch-426 costs: Active pools", *positive_summary(out[apr_col_base])),
        (
            "Epoch-426 costs: survivors",
            *positive_summary(out.loc[survivors.index, apr_col_base]),
        ),
        (
            "Epoch-500 costs: survivors (cost-adjusted)",
            *positive_summary(out.loc[survivors.index, apr_col_cf]),
        ),
        (
            "Epoch-426 costs: Active at 426, not Active at 500",
            *positive_summary(out.loc[exit_ids, apr_col_base]),
        ),
    ]

    paired = out.loc[survivors.index, [apr_col_base, apr_col_cf]].dropna()
    delta_pp = 100.0 * (paired[apr_col_cf] - paired[apr_col_base])
    both_pos = paired.loc[(paired[apr_col_base] > 0) & (paired[apr_col_cf] > 0)]
    delta_both = 100.0 * (both_pos[apr_col_cf] - both_pos[apr_col_base])

    n_cost_changed = int(out.loc[survivors.index, "cost_changed"].fillna(False).sum())
    n_margin_changed = int(
        out.loc[survivors.index, "margin_changed"].fillna(False).sum()
    )
    n_340_to_170 = int(
        (
            (out.loc[survivors.index, "fixed_cost_ada_426"] == 340.0)
            & (out.loc[survivors.index, "fixed_cost_ada_500"] == 170.0)
        ).sum()
    )

    summary_rows = [
        {"quantity": "n_baseline", "value": len(baseline)},
        {"quantity": "n_survivors", "value": len(survivors)},
        {"quantity": "n_exits", "value": len(exit_ids)},
        {"quantity": "n_cost_changed_survivors", "value": n_cost_changed},
        {"quantity": "n_margin_changed_survivors", "value": n_margin_changed},
        {"quantity": "n_340_to_170_survivors", "value": n_340_to_170},
        {"quantity": "paired_median_delta_pp", "value": float(delta_pp.median())},
        {
            "quantity": "both_positive_median_delta_pp",
            "value": float(delta_both.median()) if len(both_pos) else float("nan"),
        },
        {"quantity": "n_both_positive", "value": len(both_pos)},
        {"quantity": "T_ada", "value": T_ADA},
        {"quantity": "R_ada", "value": R_ADA},
        {"quantity": "a0", "value": A0},
        {"quantity": "k", "value": K},
        {"quantity": "z0_ada", "value": Z0_ADA},
    ]
    for label, n, npos, med, mean in rows:
        summary_rows.extend(
            [
                {"quantity": f"{label}::pools", "value": n},
                {"quantity": f"{label}::return_gt0", "value": npos},
                {"quantity": f"{label}::median_apr_pos_pct", "value": med},
                {"quantity": f"{label}::mean_apr_pos_pct", "value": mean},
            ]
        )
    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)

    table_lines = [
        "| Sample and scenario | Pools | Return $>0$ | Median APR, positive | Mean APR, positive |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, n, npos, med, mean in rows:
        table_lines.append(
            f"| {label} | {n} | {npos} | {med:.2f}% | {mean:.2f}% |"
        )

    surv_pos_base = out.loc[survivors.index, apr_col_base]
    surv_pos_cf = out.loc[survivors.index, apr_col_cf]
    all_pos_share = rows[0][2] / rows[0][1] if rows[0][1] else float("nan")
    surv_pos_share = rows[1][2] / rows[1][1] if rows[1][1] else float("nan")
    exit_pos_share = rows[3][2] / rows[3][1] if rows[3][1] else float("nan")

    table_md = "\n".join(table_lines)
    md = f"""# Member APR around the minPoolCost reduction

To evaluate how the reduction in $\\textit{{minPoolCost}}$ affects delegator returns, we calculate the annualized delegator yield

$$
\\mathrm{{APR}}_i \\approx 73(1-m_i)\\frac{{\\max\\{{f(\\sigma_i,p_i)-c_i,0\\}}}}{{\\sigma_i}}.
$$

This measures net yield per ADA after deducting fixed costs ($c_i$) and variable margins ($m_i$). Calculations use Active pools at epoch 426 with $T={T_ADA/1e9:.2f}$B ADA, $R={R_ADA/1e6:.1f}$M ADA, $a_0={A0}$, and $k={K}$. Declared $p_i$ is the certificate active at 426. Of the {len(baseline):,} Active pools with complete baseline fields, {len(survivors):,} remain Active at epoch 500, while {len(exit_ids):,} leave the Active set. For the counterfactual, continuing Active pools hold their epoch-426 stake, declared pledge, and margin fixed while adopting their actual epoch-500 declared cost. This captures operators' fixed-cost responses without allowing subsequent delegation changes to affect the comparison. Pools that leave the Active set remain in the epoch-426 baseline to avoid survivorship bias, but are excluded from the cost-adjusted scenario.

{table_md}

The data shows that surviving pools were inherently higher-yielding at baseline, with ${100*surv_pos_share:.1f}\\%$ (${rows[1][2]}/{rows[1][1]}$) generating positive returns (median positive APR of ${rows[1][3]:.2f}\\%$), whereas only ${100*exit_pos_share:.1f}\\%$ (${rows[3][2]}/{rows[3][1]}$) of exiting pools produced positive returns (median positive APR of ${rows[3][3]:.2f}\\%$). Among survivors, {n_cost_changed:,} changed declared cost between epochs 426 and 500 ({n_340_to_170:,} moved directly from 340 to 170 ADA); {n_margin_changed:,} also changed margin over the same window (margin is held fixed in the counterfactual). The cost-adjusted counterfactual leaves median and mean positive APR essentially unchanged ({rows[1][3]:.2f}% → {rows[2][3]:.2f}% median; {rows[1][4]:.2f}% → {rows[2][4]:.2f}% mean). The paired median APR change across all {len(paired):,} survivors is {delta_pp.median():+.3f} percentage points; among the {len(both_pos):,} pools with positive returns in both scenarios, it is {delta_both.median():+.3f} percentage points. Thus, once stake and margin are held fixed, the historical fixed-cost reductions associated with lower $\\textit{{minPoolCost}}$ do not produce an economically meaningful shift in delegator APR.

"""
    OUT_MD.write_text(md, encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    plot_points(axes[0], out.loc[survivors.index], apr_col_base, COLOR_SURVIVOR, "Survivors")
    plot_points(axes[0], out.loc[exit_ids], apr_col_base, COLOR_EXIT, "Exits", marker="x")
    plot_points(axes[1], out.loc[survivors.index], apr_col_cf, COLOR_SURVIVOR, "Survivors")

    axes[0].set_title(
        "Epoch-426 declared costs\n"
        f"Active pools (n={len(baseline)}; exits from Active included)",
        fontsize=FONT_SIZE,
    )
    axes[1].set_title(
        "Epoch-500 declared costs\n"
        f"survivors only; same $\\sigma,p,m$ as 426 (n={len(survivors)})",
        fontsize=FONT_SIZE,
    )
    for ax in axes:
        ax.axvline(
            Z0_ADA / 1e6,
            color="0.35",
            linestyle=":",
            linewidth=1.2,
            label=rf"$z_0(k=500)={Z0_ADA/1e6:.2f}$M",
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(1e-5, 80)
        ax.set_ylim(0.05, 20)
        ax.set_xlabel(
            "Delegation $\\sigma_i$ at epoch 426 (million ADA, log scale)",
            fontsize=FONT_SIZE,
        )
        ax.set_ylabel("Simple member APR (%)", fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="lower right")
    fig.suptitle(
        "Member APR around the minPoolCost reduction\n"
        rf"(epoch-426 $\sigma,p,m$ fixed; $k={K}$; "
        rf"$R={R_ADA/1e6:.1f}$M; APR $=73\rho$)",
        fontsize=FONT_SIZE + 1,
    )
    fig.savefig(OUT_PLOT, dpi=300)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_PLOT}")
    print("\n".join(table_lines))
    print(
        f"survivors={len(survivors)} exits={len(exit_ids)} "
        f"cost_changed={n_cost_changed} 340->170={n_340_to_170} "
        f"margin_changed={n_margin_changed}"
    )
    print(
        f"paired median delta={delta_pp.median():+.4f} pp; "
        f"both-pos median delta={delta_both.median():+.4f} pp"
    )


if __name__ == "__main__":
    main()
