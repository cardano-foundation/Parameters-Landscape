#!/usr/bin/env python3
"""
Theoretical delegator APR at epoch 644: baseline vs uniform minPoolCost floors.

For each pool with complete fields:
  f_i = f(σ_i, p_i) using declared pledge; f_i = 0 if active pledge < declared.
  APR_i = 73 (1-m_i) max{f_i - c_i, 0} / σ_i

Network APR is the stake-weighted mean of APR_i among pools with f_i > c_i.

Counterfactuals: same σ, p, m; every pool's declared cost set to 170, 75, or 25 ADA.

Writes per-pool CSV, summary MD/CSV, and a multi-group APR boxplot (f>c only).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_CSV = DIR / "member_apr_theoretical_c170_counterfactual_epoch_644.csv"
OUT_SUMMARY_CSV = DIR / "member_apr_theoretical_c170_counterfactual_epoch_644_summary.csv"
OUT_MD = DIR / "member_apr_theoretical_c170_counterfactual_epoch_644.md"
OUT_PLOT = DIR / "member_apr_theoretical_c170_counterfactual_epoch_644.png"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
C_CASES = (170.0, 75.0, 25.0)
# Same OpEx benchmark as pool_viability_theoretical_all_pools_epoch_644.py
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD
BOX_FACE = "#f4c4a8"
BOX_EDGE = "0.15"
MEDIAN_COLOR = "#111111"


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def member_apr(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    pledge_share = np.clip(
        np.divide(
            active_pledge,
            sigma,
            out=np.zeros_like(active_pledge),
            where=sigma > 0,
        ),
        0.0,
        1.0,
    )
    operator_share = margin + (1.0 - margin) * pledge_share
    profitable = fixed_cost + (f - fixed_cost) * operator_share
    return np.where(f > fixed_cost, profitable, f)


def network_stats(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    apr: np.ndarray,
    pledge_met: np.ndarray,
) -> dict[str, float | int]:
    eligible = f > cost
    n_elig = int(eligible.sum())
    n_all = int(len(sigma))
    # Viability Losing: r = Pi/C* < 1 among pledge-met pools
    pi = operator_reward(f, cost, margin, active_pledge, sigma)
    r = pi / C_STAR_ADA
    n_losing = int(((r < 1.0) & pledge_met).sum())
    n_pledge_met = int(pledge_met.sum())
    if n_elig == 0:
        return {
            "n_pools": n_all,
            "n_pledge_met": n_pledge_met,
            "n_f_gt_c": 0,
            "n_losing_r_lt_1": n_losing,
            "stake_eligible_ada": 0.0,
            "stake_eligible_share": 0.0,
            "network_apr_pct": float("nan"),
            "median_apr_pct": float("nan"),
            "mean_apr_pct": float("nan"),
        }
    sig_e = sigma[eligible]
    apr_e = apr[eligible]
    stake_e = float(sig_e.sum())
    stake_all = float(sigma.sum())
    net = float(np.average(apr_e, weights=sig_e))
    return {
        "n_pools": n_all,
        "n_pledge_met": n_pledge_met,
        "n_f_gt_c": n_elig,
        "n_losing_r_lt_1": n_losing,
        "stake_eligible_ada": stake_e,
        "stake_eligible_share": stake_e / stake_all if stake_all else float("nan"),
        "network_apr_pct": 100.0 * net,
        "median_apr_pct": 100.0 * float(np.median(apr_e)),
        "mean_apr_pct": 100.0 * float(np.mean(apr_e)),
    }


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])
    k = int(params["k"])

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    )
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna()
        & (sigma > 0)
        & declared.notna()
        & active.notna()
        & cost.notna()
        & margin.notna()
    )
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)

    pledge_met = active_a >= declared_a
    f_raw = gross_pool_reward(
        sigma_a, declared_a, z0=z0, r_over_t=R / T, a0=a0
    )
    f_a = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)

    apr_base = member_apr(sigma_a, f_a, cost_a, margin_a)
    stats_base = network_stats(
        sigma_a, f_a, cost_a, margin_a, active_a, apr_base, pledge_met
    )

    apr_by_c: dict[float, np.ndarray] = {}
    stats_by_c: dict[float, dict[str, float | int]] = {}
    for c_val in C_CASES:
        cost_cf = np.full_like(cost_a, c_val)
        apr_cf = member_apr(sigma_a, f_a, cost_cf, margin_a)
        apr_by_c[c_val] = apr_cf
        stats_by_c[c_val] = network_stats(
            sigma_a, f_a, cost_cf, margin_a, active_a, apr_cf, pledge_met
        )

    out_cols: dict[str, np.ndarray | object] = {
        "pool_id": df.loc[complete, "pool_id"].to_numpy(),
        "ticker": df.loc[complete, "pool_name.ticker"].to_numpy(),
        "sigma_ada": sigma_a,
        "declared_pledge_ada": declared_a,
        "active_pledge_ada": active_a,
        "declared_pledge_met": pledge_met,
        "margin": margin_a,
        "fixed_cost_ada": cost_a,
        "theoretical_f_ada": f_a,
        "member_apr_baseline": apr_base,
        "f_gt_c_baseline": f_a > cost_a,
    }
    for c_val in C_CASES:
        tag = f"{c_val:.0f}"
        out_cols[f"member_apr_c{tag}"] = apr_by_c[c_val]
        out_cols[f"f_gt_c_c{tag}"] = f_a > c_val
    pd.DataFrame(out_cols).to_csv(OUT_CSV, index=False)

    summary_rows = [{"scenario": "baseline_declared_costs", **stats_base}]
    for c_val in C_CASES:
        summary_rows.append(
            {"scenario": f"all_costs_set_to_{c_val:.0f}", **stats_by_c[c_val]}
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY_CSV, index=False)

    def pct_chg(new: float, old: float) -> str:
        if old == 0 or not np.isfinite(old) or not np.isfinite(new):
            return "—"
        return f"{100.0 * (new - old) / old:+.1f}%"

    b = stats_base
    table_lines = [
        (
            "| Scenario | Pools with $f>c$ | Change (%) | Mean APR ($f>c$) | Change (%) | "
            "Median APR ($f>c$) | Change (%) | "
            "Losing ($r<1$)<br>$C^*="
            f"{C_STAR_ADA:.1f}$ ADA/epoch | Change (%) |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| Baseline (declared $c_i$) | {int(b['n_f_gt_c'])} | — | "
            f"{float(b['mean_apr_pct']):.2f}% | — | "
            f"{float(b['median_apr_pct']):.2f}% | — | "
            f"{int(b['n_losing_r_lt_1'])} | — |"
        ),
    ]
    note_lines = [
        f"Losing counts use $r=\\Pi_i/C^*$ among pledge-met pools only "
        f"($n={b['n_pledge_met']}$; complete pools $n={b['n_pools']}$). "
        f"Change (%) is relative to baseline."
    ]
    for c_val in C_CASES:
        st = stats_by_c[c_val]
        table_lines.append(
            f"| Counterfactual ($c_i={c_val:.0f}$ for all) | "
            f"{int(st['n_f_gt_c'])} | "
            f"{pct_chg(float(st['n_f_gt_c']), float(b['n_f_gt_c']))} | "
            f"{float(st['mean_apr_pct']):.2f}% | "
            f"{pct_chg(float(st['mean_apr_pct']), float(b['mean_apr_pct']))} | "
            f"{float(st['median_apr_pct']):.2f}% | "
            f"{pct_chg(float(st['median_apr_pct']), float(b['median_apr_pct']))} | "
            f"{int(st['n_losing_r_lt_1'])} | "
            f"{pct_chg(float(st['n_losing_r_lt_1']), float(b['n_losing_r_lt_1']))} |"
        )

    md = rf"""# Epoch 644 — theoretical delegator APR: baseline vs uniform $c_i$

For each pool with complete fields we compute

$$
\mathrm{{APR}}_i = 73\,(1-m_i)\,\frac{{\max\{{f(\sigma_i,p_i)-c_i,0\}}}}{{\sigma_i}},
$$

with $f=0$ when active pledge is below declared pledge (same rule as the theoretical viability analysis). Protocol parameters: $k={k}$, $a_0={a0}$, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B ADA.

**Network APR** is the stake-weighted mean of $\mathrm{{APR}}_i$ among pools with $f_i>c_i$.

{chr(10).join(table_lines)}

{chr(10).join(note_lines)}
"""
    OUT_MD.write_text(md, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11.0, 5.2), constrained_layout=True)
    groups: list[tuple[str, np.ndarray]] = [
        (
            "Baseline\n(declared "
            r"$c_i$)",
            100.0 * apr_base[f_a > cost_a],
        ),
    ]
    for c_val in C_CASES:
        apr_cf = apr_by_c[c_val]
        groups.append(
            (
                rf"$c_i={c_val:.0f}$"
                "\n(all pools)",
                100.0 * apr_cf[f_a > c_val],
            )
        )
    data = [vals for _, vals in groups]
    labels = [f"{name}\n(n={len(vals)})" for name, vals in groups]
    bp = ax.boxplot(
        data,
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.2},
        whiskerprops={"color": BOX_EDGE, "linewidth": 1.1},
        capprops={"color": BOX_EDGE, "linewidth": 1.1},
        boxprops={"color": BOX_EDGE, "linewidth": 1.1},
    )
    for box in bp["boxes"]:
        box.set_facecolor(BOX_FACE)
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.set_ylim(bottom=0.0)
    ax.set_xlim(0.4, 5.7)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    fig.suptitle(
        "Epoch 644 — theoretical member APR\n"
        rf"($k={k}$, $a_0={a0}$; $\sigma,p,m$ fixed; "
        rf"uniform $c_i\in\{{{', '.join(f'{c:.0f}' for c in C_CASES)}\}}$)"
        "\n"
        r"Calculations based on pools with $f(\sigma_i,p_i)>c_i$",
        fontsize=FONT_SIZE,
    )
    net_lines = [f"baseline {stats_base['network_apr_pct']:.2f}%"]
    for c_val in C_CASES:
        net_lines.append(
            rf"$c_i={c_val:.0f}$ {stats_by_c[c_val]['network_apr_pct']:.2f}%"
        )
    ax.text(
        5.55,
        0.08,
        "Network APR\n(stake-weighted):\n" + "\n".join(net_lines),
        ha="right",
        va="bottom",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
        zorder=5,
    )
    fig.savefig(OUT_PLOT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_PLOT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
