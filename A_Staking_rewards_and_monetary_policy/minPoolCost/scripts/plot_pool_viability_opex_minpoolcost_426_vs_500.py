#!/usr/bin/env python3
"""
Theoretical operator viability around the minPoolCost reduction, 426 -> 500.

Use the cohort of pools present in both snapshots. Hold epoch-426 stake,
pledges, and margin fixed. Compute f(sigma,p) once with k=500, then compare
operator reward using each pool's declared fixed cost in:

  - epoch 426 (minPoolCost = 340 ADA)
  - epoch 500 (minPoolCost = 170 ADA)

Parameters:
  T = 36.01B ADA, R = 21.6M ADA, a0 = 0.3, k = 500
  C* = (667/6)/0.31 = 358.6 ADA per epoch

Important data limitation:
  The CSV pledge columns were stamped from a later pool_list and are not
  historical epoch-426 pledges. They are used as fixed proxies in both cases,
  so the comparison isolates the declared-cost change but levels should be
  interpreted cautiously.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
E426_CSV = DIR / "staking_pools_full_epoch_426.csv"
E500_CSV = DIR / "staking_pools_full_epoch_500.csv"
OUT_PLOT = DIR / "pool_viability_opex_categories_minpoolcost_426_vs_500.png"
OUT_CSV = DIR / "pool_viability_opex_minpoolcost_426_vs_500.csv"
OUT_SUMMARY = DIR / "pool_viability_opex_minpoolcost_426_vs_500_summary.csv"
OUT_MD = DIR / "pool_viability_opex_minpoolcost_426_vs_500.md"

FONT_SIZE = 12
A0 = 0.3
K = 500
T_ADA = 36.01e9
R_ADA = 21.6e6
Z0_ADA = T_ADA / K
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.31
C_STAR = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

CAT_ORDER = ("losing", "edge", "comfortable", "strong")
CAT_LABELS = (
    "Losing\n($r<1$)",
    "Edge\n($1\\leq r<2$)",
    "Comfortable\n($2\\leq r<5$)",
    "Strong\n($r\\geq5$)",
)
CAT_COLORS = ("#d62828", "#e76f51", "#4c78a8", "#2a9d8f")


def gross_pool_reward(
    sigma: np.ndarray, pledge: np.ndarray
) -> np.ndarray:
    """Theoretical f(sigma,p) in ADA."""
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), Z0_ADA)
    pledge_tilde = np.minimum(np.maximum(pledge, 0.0), Z0_ADA)
    # All analyzed rows satisfy pledge <= sigma, but retain numerical safety.
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = (
        sigma_tilde
        - pledge_tilde * (Z0_ADA - sigma_tilde) / Z0_ADA
    )
    return (R_ADA / T_ADA) / (1.0 + A0) * (
        sigma_tilde + A0 * pledge_tilde * inner / Z0_ADA
    )


def operator_reward(
    f: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
    fixed_cost: np.ndarray,
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
    share = margin + (1.0 - margin) * pledge_share
    return np.where(
        f > fixed_cost,
        fixed_cost + (f - fixed_cost) * share,
        f,
    )


def classify(ratio: float) -> str:
    if ratio < 1.0:
        return "losing"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def category_counts(categories: pd.Series) -> dict[str, int]:
    counts = categories.value_counts()
    return {
        category: int(counts.get(category, 0))
        for category in CAT_ORDER
    }


def draw_panel(
    ax: plt.Axes,
    counts: dict[str, int],
    title: str,
    note: str,
) -> None:
    heights = [counts[category] for category in CAT_ORDER]
    x = np.arange(len(CAT_ORDER))
    ax.bar(
        x,
        heights,
        width=0.72,
        color=CAT_COLORS,
        edgecolor="white",
    )
    ymax = max(heights)
    for xi, height in zip(x, heights):
        ax.text(
            xi,
            height + ymax * 0.012,
            str(height),
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(CAT_LABELS)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_ylim(0, ymax * 1.18)
    ax.text(
        0.98,
        0.97,
        note,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )


def pct_change(old: int, new: int) -> float:
    return 100.0 * (new - old) / old if old else float("nan")


def fmt_change(value: float) -> str:
    return "—" if not np.isfinite(value) else f"{value:+.1f}%"


def main() -> None:
    e426 = pd.read_csv(E426_CSV).set_index("pool_id")
    e500 = pd.read_csv(E500_CSV).set_index("pool_id")
    common = e426.index.intersection(e500.index)

    sigma = (
        pd.to_numeric(
            e426.loc[common, "epochs.0.data.epoch_stake"],
            errors="coerce",
        )
        / 1e6
    )
    declared_pledge = (
        pd.to_numeric(
            e426.loc[common, "pool_update.active.pledge"],
            errors="coerce",
        )
        / 1e6
    )
    active_pledge = (
        pd.to_numeric(e426.loc[common, "pledged"], errors="coerce")
        / 1e6
    )
    margin = pd.to_numeric(
        e426.loc[common, "pool_update.active.margin"], errors="coerce"
    )
    cost_426 = (
        pd.to_numeric(
            e426.loc[common, "pool_update.active.fixed_cost"],
            errors="coerce",
        )
        / 1e6
    )
    cost_500 = (
        pd.to_numeric(
            e500.loc[common, "pool_update.active.fixed_cost"],
            errors="coerce",
        )
        / 1e6
    )

    complete = (
        sigma.notna()
        & declared_pledge.notna()
        & active_pledge.notna()
        & margin.notna()
        & cost_426.notna()
        & cost_500.notna()
    )
    pledge_feasible = declared_pledge <= sigma
    analyzed = complete & pledge_feasible & (sigma > 0)

    ids = common[analyzed]
    sigma_a = sigma[analyzed].to_numpy(dtype=float)
    declared_a = declared_pledge[analyzed].to_numpy(dtype=float)
    active_a = active_pledge[analyzed].to_numpy(dtype=float)
    margin_a = margin[analyzed].to_numpy(dtype=float)
    cost426_a = cost_426[analyzed].to_numpy(dtype=float)
    cost500_a = cost_500[analyzed].to_numpy(dtype=float)

    f = gross_pool_reward(sigma_a, declared_a)
    pi_426 = operator_reward(
        f, margin_a, active_a, sigma_a, cost426_a
    )
    pi_500 = operator_reward(
        f, margin_a, active_a, sigma_a, cost500_a
    )
    ratio_426 = pi_426 / C_STAR
    ratio_500 = pi_500 / C_STAR
    categories_426 = pd.Series(
        [classify(value) for value in ratio_426], index=ids
    )
    categories_500 = pd.Series(
        [classify(value) for value in ratio_500], index=ids
    )
    counts_426 = category_counts(categories_426)
    counts_500 = category_counts(categories_500)

    changed_all = cost_426.notna() & cost_500.notna() & (
        cost_426 != cost_500
    )
    down_all = cost_426.notna() & cost_500.notna() & (
        cost_500 < cost_426
    )
    up_all = cost_426.notna() & cost_500.notna() & (
        cost_500 > cost_426
    )
    changed_analyzed = cost426_a != cost500_a
    down_analyzed = cost500_a < cost426_a
    up_analyzed = cost500_a > cost426_a
    transition_340_to_170_all = (cost_426 == 340.0) & (
        cost_500 == 170.0
    )
    transition_340_to_170_analyzed = (cost426_a == 340.0) & (
        cost500_a == 170.0
    )

    n_common = len(common)
    n_complete = int(complete.sum())
    n_infeasible = int((complete & ~pledge_feasible).sum())
    n_analyzed = int(analyzed.sum())
    n_viable_426 = int((ratio_426 >= 1.0).sum())
    n_viable_500 = int((ratio_500 >= 1.0).sum())

    out = pd.DataFrame(
        {
            "pool_id": ids,
            "epoch_stake_426_ada": sigma_a,
            "declared_pledge_proxy_ada": declared_a,
            "active_pledge_proxy_ada": active_a,
            "margin_426": margin_a,
            "declared_cost_426_ada": cost426_a,
            "declared_cost_500_ada": cost500_a,
            "cost_changed": changed_analyzed,
            "cost_decreased": down_analyzed,
            "theoretical_f_ada": f,
            "Pi_cost426_ada": pi_426,
            "coverage_ratio_cost426": ratio_426,
            "category_cost426": categories_426.to_numpy(),
            "Pi_cost500_ada": pi_500,
            "coverage_ratio_cost500": ratio_500,
            "category_cost500": categories_500.to_numpy(),
            "Cstar_ada_per_epoch": C_STAR,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    rows: list[dict[str, float | int | str]] = [
        {"quantity": "common_pools", "value": n_common},
        {"quantity": "complete_proxy_fields", "value": n_complete},
        {"quantity": "pledge_exceeds_stake_excluded", "value": n_infeasible},
        {"quantity": "analyzed_fixed_cohort", "value": n_analyzed},
        {"quantity": "T_ada", "value": T_ADA},
        {"quantity": "R_ada", "value": R_ADA},
        {"quantity": "a0", "value": A0},
        {"quantity": "k", "value": K},
        {"quantity": "z0_ada", "value": Z0_ADA},
        {"quantity": "ada_usd", "value": ADA_USD},
        {"quantity": "opex_ada_per_epoch", "value": C_STAR},
        {"quantity": "cost_changed_common_cohort", "value": int(changed_all.sum())},
        {"quantity": "cost_decreased_common_cohort", "value": int(down_all.sum())},
        {"quantity": "cost_increased_common_cohort", "value": int(up_all.sum())},
        {
            "quantity": "cost_340_to_170_common_cohort",
            "value": int(transition_340_to_170_all.sum()),
        },
        {"quantity": "cost_changed_analyzed", "value": int(changed_analyzed.sum())},
        {"quantity": "cost_decreased_analyzed", "value": int(down_analyzed.sum())},
        {"quantity": "cost_increased_analyzed", "value": int(up_analyzed.sum())},
        {
            "quantity": "cost_340_to_170_analyzed",
            "value": int(transition_340_to_170_analyzed.sum()),
        },
        {"quantity": "viable_cost426", "value": n_viable_426},
        {"quantity": "viable_cost500", "value": n_viable_500},
    ]
    for category in CAT_ORDER:
        rows.extend(
            [
                {
                    "quantity": f"{category}_cost426",
                    "value": counts_426[category],
                },
                {
                    "quantity": f"{category}_cost500",
                    "value": counts_500[category],
                },
            ]
        )
    pd.DataFrame(rows).to_csv(OUT_SUMMARY, index=False)

    fig, axes = plt.subplots(
        1, 2, figsize=(14.5, 5.4), constrained_layout=True
    )
    draw_panel(
        axes[0],
        counts_426,
        "Declared costs at epoch 426\n(minPoolCost = 340 ADA)",
        f"Fixed cohort: {n_analyzed}\n"
        f"Cover OpEx: {n_viable_426}\n"
        f"Median declared cost: {np.median(cost426_a):.0f} ADA",
    )
    draw_panel(
        axes[1],
        counts_500,
        "Declared costs at epoch 500\n(minPoolCost = 170 ADA)",
        f"Fixed cohort: {n_analyzed}\n"
        f"Cover OpEx: {n_viable_500}\n"
        f"Cost changed: {int(changed_analyzed.sum())}\n"
        f"Cost decreased: {int(down_analyzed.sum())}",
    )
    fig.suptitle(
        "Theoretical operator viability after the minPoolCost reduction\n"
        rf"(epoch-426 $\sigma,p,\hat p,m$ fixed; $k=500$, "
        rf"$C^*={C_STAR:.1f}$ ADA/epoch, $r=\Pi_i/C^*$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=300)

    changes = {
        "Pools": 0.0,
        "Cover OpEx ($r\\geq1$)": pct_change(
            n_viable_426, n_viable_500
        ),
        "Losing ($r<1$)": pct_change(
            counts_426["losing"], counts_500["losing"]
        ),
        "Edge ($1\\leq r<2$)": pct_change(
            counts_426["edge"], counts_500["edge"]
        ),
        "Comfortable ($2\\leq r<5$)": pct_change(
            counts_426["comfortable"], counts_500["comfortable"]
        ),
        "Strong ($r\\geq5$)": pct_change(
            counts_426["strong"], counts_500["strong"]
        ),
    }
    md = f"""# Pool viability around the minPoolCost reduction

We use the {n_analyzed:,} pools in the fixed analysis cohort and hold each
pool's epoch-426 stake $\\sigma_i$, pledge proxies $p_i$ and $\\hat p_i$, and
margin $m_i$ fixed. We compute $f(\\sigma_i,p_i)$ with
$T={T_ADA/1e9:.2f}$B ADA, $R={R_ADA/1e6:.1f}$M ADA, $a_0={A0}$, and $k={K}$.
Operator reward is evaluated first with the pool's epoch-426 declared cost and
then with its epoch-500 declared cost.

Monthly OpEx is $\\$667$ and ADA is $\\${ADA_USD}$, hence

$$
C^*=\\frac{{667/6}}{{{ADA_USD}}}={C_STAR:.1f}
\\quad\\text{{ADA per epoch}}.
$$

Let $r=\\Pi_i/C^*$. In the common snapshot cohort, {int(changed_all.sum()):,}
of {n_common:,} pools changed declared cost from epoch 426 to epoch 500:
{int(down_all.sum()):,} decreased it and {int(up_all.sum()):,} increased it;
{int(transition_340_to_170_all.sum()):,} moved directly from 340 to 170 ADA.
Within the {n_analyzed:,}-pool analysis cohort, {int(changed_analyzed.sum()):,}
changed cost ({int(down_analyzed.sum()):,} decreases and
{int(up_analyzed.sum()):,} increases), including
{int(transition_340_to_170_analyzed.sum()):,} direct 340-to-170 changes.

| | Epoch-426 costs (minPoolCost 340) | Epoch-500 costs (minPoolCost 170) | Variation |
| :--- | ---: | ---: | ---: |
| Pools | {n_analyzed} | {n_analyzed} | — |
| Cover OpEx ($r\\geq1$) | {n_viable_426} | {n_viable_500} | {fmt_change(changes["Cover OpEx ($r\\geq1$)"])} |
| Losing ($r<1$) | {counts_426["losing"]} | {counts_500["losing"]} | {fmt_change(changes["Losing ($r<1$)"])} |
| Edge ($1\\leq r<2$) | {counts_426["edge"]} | {counts_500["edge"]} | {fmt_change(changes["Edge ($1\\leq r<2$)"])} |
| Comfortable ($2\\leq r<5$) | {counts_426["comfortable"]} | {counts_500["comfortable"]} | {fmt_change(changes["Comfortable ($2\\leq r<5$)"])} |
| Strong ($r\\geq5$) | {counts_426["strong"]} | {counts_500["strong"]} | {fmt_change(changes["Strong ($r\\geq5$)"])} |

The historical CSVs contain historical stake, margin, and fixed cost, but their
pledge columns were stamped from a later `pool_list`. The pledge values are
therefore fixed proxies—not historical epoch-426 pledges. Of {n_common:,}
common pools, {n_common - n_complete:,} lack complete proxy fields and
{n_infeasible:,} additional pools have declared pledge above epoch-426 stake,
leaving {n_analyzed:,} pools in the analysis.
"""
    OUT_MD.write_text(md)

    print(f"Common cohort: {n_common}")
    print(f"Analyzed cohort: {n_analyzed}")
    print(
        f"Cost changed (common): {int(changed_all.sum())}; "
        f"down={int(down_all.sum())}; up={int(up_all.sum())}"
    )
    print(
        f"Cost changed (analyzed): {int(changed_analyzed.sum())}; "
        f"down={int(down_analyzed.sum())}; up={int(up_analyzed.sum())}"
    )
    print("Epoch-426 costs:", counts_426, "viable", n_viable_426)
    print("Epoch-500 costs:", counts_500, "viable", n_viable_500)
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
