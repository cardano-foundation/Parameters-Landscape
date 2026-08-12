#!/usr/bin/env python3
"""
Theoretical pool viability — epoch 644 snapshot, k=500 vs k=1000.

Side-by-side grouped bars: same colour palette per bin, k=1000 bars hatched.
Same formula and C* as plot_pool_viability_before_redelegation_epoch_644.py.

Writes:
  pool_viability_k500_vs_k1000_epoch_644.png
  pool_viability_k500_vs_k1000_epoch_644.csv
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
OUT_PLOT = DIR / "pool_viability_k500_vs_k1000_epoch_644.png"
OUT_CSV = DIR / "pool_viability_k500_vs_k1000_epoch_644.csv"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

CATEGORY_ORDER = (
    "losing_lt_025",
    "losing_025_050",
    "losing_050_075",
    "losing_075_100",
    "edge",
    "comfortable",
    "strong",
)
CATEGORY_LABELS = (
    r"$r<0.25$",
    r"$0.25\leq r<0.5$",
    r"$0.5\leq r<0.75$",
    r"$0.75\leq r<1$",
    "Edge\n" r"($1\leq r<2$)",
    "Comfortable\n" r"($2\leq r<5$)",
    "Strong\n" r"($r\geq5$)",
)
CATEGORY_COLORS = (
    "#67000d",
    "#a50f15",
    "#de2d26",
    "#fc9272",
    "#e76f51",
    "#4c78a8",
    "#2a9d8f",
)


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
    s = margin + (1.0 - margin) * pledge_share
    return np.where(f > fixed_cost, fixed_cost + (f - fixed_cost) * s, f)


def classify(ratio: float) -> str:
    if ratio < 0.25:
        return "losing_lt_025"
    if ratio < 0.5:
        return "losing_025_050"
    if ratio < 0.75:
        return "losing_050_075"
    if ratio < 1.0:
        return "losing_075_100"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def compute_viability(
    sigma_a, declared_a, active_a, cost_a, margin_a, pledge_met, z0, r_over_t, a0
):
    f_formula = gross_pool_reward(
        sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=a0
    )
    f_a = np.where(pledge_met, np.maximum(f_formula, 0.0), 0.0)
    pi_a = operator_reward(f_a, cost_a, margin_a, active_a, sigma_a)
    ratio = pi_a / C_STAR_ADA
    categories = np.array(
        [
            classify(value) if met else "pledge_not_met"
            for value, met in zip(ratio, pledge_met)
        ]
    )
    eligible = categories[pledge_met]
    eligible_ratio = ratio[pledge_met]
    counts = pd.Series(eligible).value_counts()
    heights = [int(counts.get(c, 0)) for c in CATEGORY_ORDER]
    n_analyzed = int(pledge_met.sum())
    n_viable = int((eligible_ratio >= 1.0).sum())
    n_losing = sum(heights[:4])
    return heights, n_analyzed, n_viable, n_losing, ratio, categories


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T

    df = pd.read_csv(POOLS_CSV)
    sigma = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    ) / 1e6
    declared_pledge = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active_pledge = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    fixed_cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna()
        & declared_pledge.notna()
        & active_pledge.notna()
        & fixed_cost.notna()
        & margin.notna()
    )
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared_pledge[complete].to_numpy(dtype=float)
    active_a = active_pledge[complete].to_numpy(dtype=float)
    cost_a = fixed_cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)
    n_pledge_unmet = int((~pledge_met).sum())

    z0_500 = T / 500
    z0_1000 = T / 1000

    h500, n_an500, n_v500, n_l500, r500, cat500 = compute_viability(
        sigma_a, declared_a, active_a, cost_a, margin_a, pledge_met, z0_500, r_over_t, a0
    )
    h1000, n_an1000, n_v1000, n_l1000, r1000, cat1000 = compute_viability(
        sigma_a, declared_a, active_a, cost_a, margin_a, pledge_met, z0_1000, r_over_t, a0
    )

    # CSV
    out = pd.DataFrame({
        "pool_id": df.loc[complete, "pool_id"].values,
        "pool_ticker": df.loc[complete, "pool_name.ticker"].values,
        "sigma_ada": sigma_a,
        "declared_pledge_ada": declared_a,
        "active_pledge_ada": active_a,
        "declared_fixed_cost_ada": cost_a,
        "margin": margin_a,
        "pledge_met": pledge_met,
        "ratio_k500": r500,
        "category_k500": cat500,
        "ratio_k1000": r1000,
        "category_k1000": cat1000,
    })
    out.to_csv(OUT_CSV, index=False)

    # Grouped bar plot
    x = np.arange(len(CATEGORY_ORDER))
    width = 0.38

    fig, ax = plt.subplots(figsize=(13.0, 5.8), constrained_layout=True)
    bars_500 = ax.bar(
        x - width / 2, h500, width,
        color=CATEGORY_COLORS, edgecolor="white", linewidth=0.6,
        label=rf"$k=500$ ($z_0={z0_500/1e6:.1f}$M)",
    )
    bars_1000 = ax.bar(
        x + width / 2, h1000, width,
        color=CATEGORY_COLORS, edgecolor="0.3", linewidth=0.8,
        hatch="//", alpha=0.80,
        label=rf"$k=1000$ ($z_0={z0_1000/1e6:.1f}$M)",
    )

    ymax = max(max(h500), max(h1000))
    for xi, (h5, h10) in enumerate(zip(h500, h1000)):
        ax.text(xi - width / 2, h5 + ymax * 0.012, str(h5),
                ha="center", va="bottom", fontsize=FONT_SIZE - 2)
        ax.text(xi + width / 2, h10 + ymax * 0.012, str(h10),
                ha="center", va="bottom", fontsize=FONT_SIZE - 2)

    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORY_LABELS, fontsize=FONT_SIZE - 1)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_ylim(0, ymax * 1.18)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE, frameon=True, loc="upper right",
              bbox_to_anchor=(0.99, 0.72))
    ax.set_title(
        "Epoch 644 — theoretical viability: $k=500$ vs $k=1000$\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; same pools & parameters)",
        fontsize=FONT_SIZE,
    )
    ax.text(
        0.98, 0.97,
        f"Pledge-met pools: {n_an500}\n"
        f"$k=500$: cover OpEx {n_v500}, losing {n_l500}\n"
        f"$k=1000$: cover OpEx {n_v1000}, losing {n_l1000}\n"
        f"Pledge not met (excluded): {n_pledge_unmet}",
        transform=ax.transAxes,
        ha="right", va="top", fontsize=FONT_SIZE,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="0.75", alpha=0.95),
    )
    fig.savefig(OUT_PLOT, dpi=160)

    print(f"C*={C_STAR_ADA:.4f} ADA/epoch")
    print(f"k=500:  cover OpEx={n_v500}, losing={n_l500}")
    print(f"k=1000: cover OpEx={n_v1000}, losing={n_l1000}")
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
