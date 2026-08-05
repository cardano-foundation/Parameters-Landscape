#!/usr/bin/env python3
"""
Theoretical viability of all pools in the epoch-644 snapshot.

Unlike the observed-reward analysis, this script does not restrict the sample
to pools that minted a block. It computes, for every pool with complete data,

    f_i = f(sigma_i, p_i)

using declared pledge p_i, and

    Pi_i = c_i + (f_i - c_i)
           * [m_i + (1 - m_i) * p_hat_i / sigma_i]

using active pledge p_hat_i. A pool whose active pledge is below its declared
pledge is assigned f_i = 0 (the pledge is not met). If f_i <= c_i, the
implementable operator reward is Pi_i = f_i: the operator cannot take more
than the pool reward.

Epoch-644 reward parameters are loaded from f_reward_params_epoch_644.json.

Usage:
  python3 plot_pool_viability_theoretical_all_pools_epoch_644.py
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
OUT_PLOT = DIR / "pool_viability_theoretical_all_pools_epoch_644.png"
OUT_CSV = DIR / "pool_viability_theoretical_all_pools_epoch_644.csv"
OUT_SUMMARY = DIR / "pool_viability_theoretical_all_pools_epoch_644.md"
OUT_TRAITS = DIR / "pool_viability_losing_vs_edge_traits_epoch_644.png"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

CATEGORY_ORDER = ("losing", "edge", "comfortable", "strong")
CATEGORY_LABELS = (
    "Losing\n($r<1$)",
    "Edge\n($1\\leq r<2$)",
    "Comfortable\n($2\\leq r<5$)",
    "Strong\n($r\\geq5$)",
)
CATEGORY_COLORS = ("#d62828", "#e76f51", "#4c78a8", "#2a9d8f")


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    """Return theoretical f(sigma, p) in ADA."""
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    """Return theoretical operator reward Pi in ADA."""
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


def classify(ratio: float) -> str:
    if ratio < 1.0:
        return "losing"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    )
    declared_pledge = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active_pledge = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    fixed_cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna()
        & declared_pledge.notna()
        & active_pledge.notna()
        & fixed_cost.notna()
        & margin.notna()
    )
    analysis = df.loc[complete, ["pool_id", "pool_name.ticker"]].copy()
    analysis["delegators"] = pd.to_numeric(
        df.loc[complete, "epochs.0.data.delegators"], errors="coerce"
    ).to_numpy()
    analysis["blocks_minted"] = pd.to_numeric(
        df.loc[complete, "epochs.0.data.block.minted"], errors="coerce"
    ).to_numpy()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared_pledge[complete].to_numpy(dtype=float)
    active_a = active_pledge[complete].to_numpy(dtype=float)
    cost_a = fixed_cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)

    pledge_met = (active_a >= declared_a) & (sigma_a > 0)
    f_formula = gross_pool_reward(
        sigma_a,
        declared_a,
        z0=z0,
        r_over_t=R / T,
        a0=a0,
    )
    # The reward formula presumes a feasible, met pledge. Pools that do not
    # meet their declared pledge are not eligible for rewards.
    f_a = np.where(pledge_met, np.maximum(f_formula, 0.0), 0.0)
    pi_a = operator_reward(
        f_a, cost_a, margin_a, active_a, sigma_a
    )
    ratio = pi_a / C_STAR_ADA
    categories = np.array(
        [
            classify(value) if met else "pledge_not_met"
            for value, met in zip(ratio, pledge_met)
        ]
    )

    analysis["sigma_ada"] = sigma_a
    analysis["declared_pledge_ada"] = declared_a
    analysis["active_pledge_ada"] = active_a
    analysis["declared_fixed_cost_ada"] = cost_a
    analysis["margin"] = margin_a
    analysis["declared_pledge_met"] = pledge_met
    analysis["theoretical_f_ada"] = f_a
    analysis["theoretical_operator_reward_ada"] = pi_a
    analysis["opex_ada_per_epoch"] = C_STAR_ADA
    analysis["coverage_ratio"] = ratio
    analysis["category"] = categories
    analysis.to_csv(OUT_CSV, index=False)

    eligible_categories = categories[pledge_met]
    eligible_ratio = ratio[pledge_met]
    counts = pd.Series(eligible_categories).value_counts()
    heights = [int(counts.get(category, 0)) for category in CATEGORY_ORDER]
    n_complete = len(analysis)
    n_incomplete = int((~complete).sum())
    n_analyzed = int(pledge_met.sum())
    n_viable = int((eligible_ratio >= 1.0).sum())
    n_risk = int(
        ((eligible_ratio >= 1.0) & (eligible_ratio < 2.0)).sum()
    )
    n_pledge_unmet = int((~pledge_met).sum())

    fig, ax = plt.subplots(figsize=(9.2, 5.2), constrained_layout=True)
    x = np.arange(len(CATEGORY_ORDER))
    ax.bar(
        x,
        heights,
        width=0.72,
        color=CATEGORY_COLORS,
        edgecolor="white",
    )
    for xi, height in zip(x, heights):
        ax.text(
            xi,
            height + max(heights) * 0.015,
            f"{height}",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORY_LABELS)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — theoretical viability vs OpEx\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.text(
        0.98,
        0.97,
        f"Pledge-met pools analyzed: {n_analyzed}\n"
        f"Cover OpEx: {n_viable}\n"
        f"At risk ($1\\leq r<2$): {n_risk}\n"
        f"Not counted (pledge not met): {n_pledge_unmet}\n"
        f"Incomplete rows: {n_incomplete}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )
    fig.savefig(OUT_PLOT, dpi=160)

    # Losing-vs-edge characteristics under the same theoretical approach.
    losing = analysis[analysis["category"] == "losing"]
    edge = analysis[analysis["category"] == "edge"]
    fig_traits, axes = plt.subplots(
        3, 3, figsize=(12.5, 9.5), constrained_layout=True
    )

    def box_pair(
        ax: plt.Axes,
        losing_values: pd.Series,
        edge_values: pd.Series,
        ylabel: str,
        title: str,
    ) -> None:
        values = [
            losing_values.dropna().to_numpy(),
            edge_values.dropna().to_numpy(),
        ]
        box = ax.boxplot(
            values,
            tick_labels=[
                f"Losing\n(n={len(losing)})",
                f"Edge\n(n={len(edge)})",
            ],
            patch_artist=True,
            widths=0.55,
            showfliers=False,
        )
        for patch, color in zip(
            box["boxes"], (CATEGORY_COLORS[0], CATEGORY_COLORS[1])
        ):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)

    box_pair(
        axes[0, 0],
        losing["sigma_ada"] / 1e6,
        edge["sigma_ada"] / 1e6,
        "Epoch stake (M ADA)",
        "Epoch stake",
    )
    box_pair(
        axes[0, 1],
        losing["active_pledge_ada"] / 1e3,
        edge["active_pledge_ada"] / 1e3,
        "Active pledge (k ADA)",
        "Active pledge",
    )
    box_pair(
        axes[0, 2],
        losing["declared_pledge_ada"] / 1e3,
        edge["declared_pledge_ada"] / 1e3,
        "Declared pledge (k ADA)",
        "Declared pledge",
    )
    box_pair(
        axes[1, 0],
        losing["margin"] * 100.0,
        edge["margin"] * 100.0,
        "Declared margin (%)",
        "Margin",
    )
    box_pair(
        axes[1, 1],
        losing["blocks_minted"],
        edge["blocks_minted"],
        "Blocks minted (epoch)",
        "Blocks",
    )
    box_pair(
        axes[1, 2],
        losing["delegators"],
        edge["delegators"],
        "Delegators",
        "Delegators",
    )
    box_pair(
        axes[2, 0],
        losing["declared_fixed_cost_ada"],
        edge["declared_fixed_cost_ada"],
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
    )
    axes[2, 1].axis("off")
    axes[2, 1].text(
        0.0,
        0.9,
        f"Not included in these categories:\n"
        f"• pledge not met: {n_pledge_unmet}\n"
        f"• incomplete rows: {n_incomplete}",
        ha="left",
        va="top",
        fontsize=FONT_SIZE,
    )
    axes[2, 2].axis("off")
    fig_traits.suptitle(
        "Epoch 644 — characteristics of theoretical Losing vs Edge pools\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; pledge-met pools)",
        fontsize=FONT_SIZE,
    )
    fig_traits.savefig(OUT_TRAITS, dpi=160)

    summary = (
        "# Epoch 644 theoretical viability — all pools\n\n"
        f"- Monthly OpEx: {MONTHLY_OPEX_USD:.0f} USD\n"
        f"- Epoch OpEx: {MONTHLY_OPEX_USD / EPOCHS_PER_MONTH:.2f} USD\n"
        f"- ADA price: {ADA_USD:.2f} USD/ADA\n"
        f"- \\(C^*={C_STAR_ADA:.1f}\\) ADA per epoch\n"
        f"- Pledge-met pools analyzed: {n_analyzed}\n"
        f"- Pools not counted because declared pledge was not met: {n_pledge_unmet}\n"
        f"- Incomplete rows excluded: {n_incomplete}\n\n"
        "| Category | Condition | Pools |\n"
        "|---|---:|---:|\n"
        f"| Losing | \\(r<1\\) | {heights[0]} |\n"
        f"| Edge | \\(1\\le r<2\\) | {heights[1]} |\n"
        f"| Comfortable | \\(2\\le r<5\\) | {heights[2]} |\n"
        f"| Strong | \\(r\\ge5\\) | {heights[3]} |\n\n"
        f"Thus, {n_viable} of {n_analyzed} pledge-met pools cover the assumed OpEx, "
        f"and {n_risk} are in the edge category.\n"
    )
    OUT_SUMMARY.write_text(summary)

    print(f"R={R:.6f}, T={T:.6f}, z0={z0:.6f}, a0={a0}")
    print(f"C*={C_STAR_ADA:.4f} ADA/epoch")
    print(f"analyzed={n_complete}; incomplete={n_incomplete}")
    print(f"pledge-met pools analyzed={n_analyzed}")
    print(f"declared pledge not met (not counted)={n_pledge_unmet}")
    print(dict(zip(CATEGORY_ORDER, heights)))
    print(f"cover OpEx={n_viable}; edge={n_risk}")
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_SUMMARY}")
    print(f"wrote {OUT_TRAITS}")


if __name__ == "__main__":
    main()
