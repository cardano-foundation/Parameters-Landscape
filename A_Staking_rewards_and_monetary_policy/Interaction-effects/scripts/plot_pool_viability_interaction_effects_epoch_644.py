#!/usr/bin/env python3
"""Epoch 644 — pool viability (r = Pi / C*) under interaction effects.

2x2 grouped bars vs baseline (k=500, declared c_i):
  A) k: 500 -> 1000, c_i unchanged
  B) k: 500 -> 1000, all c_i -> 170
  C) k=500, all c_i -> 75
  D) k: 500 -> 1000, all c_i -> 75
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
PARENT = DIR.parent
POOLS_CSV = PARENT / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = PARENT / "f_reward_params_epoch_644.json"
OUT_PNG = DIR / "pool_viability_interaction_effects_epoch_644.png"
OUT_CSV = DIR / "pool_viability_interaction_effects_epoch_644.csv"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD
C_FORCE_170 = 170.0
C_FORCE_75 = 75.0

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
    "[0.25," "\n" "0.5)",
    "[0.5," "\n" "0.75)",
    "[0.75," "\n" "1)",
    "Edge" "\n" r"$[1,2)$",
    "Comf." "\n" r"$[2,5)$",
    "Strong" "\n" r"$\geq5$",
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


def gross_pool_reward(sigma, declared_pledge, *, z0, r_over_t, a0):
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(f, fixed_cost, margin, active_pledge, sigma):
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


def compute_viability(sigma, declared, active, cost, margin, pledge_met, z0, r_over_t, a0):
    f_raw = gross_pool_reward(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    pi = operator_reward(f, cost, margin, active, sigma)
    ratio = pi / C_STAR_ADA
    categories = np.array(
        [classify(value) if met else "pledge_not_met" for value, met in zip(ratio, pledge_met)]
    )
    eligible = categories[pledge_met]
    eligible_ratio = ratio[pledge_met]
    counts = pd.Series(eligible).value_counts()
    heights = [int(counts.get(c, 0)) for c in CATEGORY_ORDER]
    n_analyzed = int(pledge_met.sum())
    n_viable = int((eligible_ratio >= 1.0).sum())
    n_losing = int(sum(heights[:4]))
    return heights, n_analyzed, n_viable, n_losing, ratio, categories, f, pi


def draw_panel(ax, h_base, h_alt, *, title, legend_base, legend_alt, n_v_base, n_l_base, n_v_alt, n_l_alt):
    x = np.arange(len(CATEGORY_ORDER))
    width = 0.38
    ax.bar(
        x - width / 2,
        h_base,
        width,
        color=CATEGORY_COLORS,
        edgecolor="white",
        linewidth=0.6,
        label=legend_base,
    )
    ax.bar(
        x + width / 2,
        h_alt,
        width,
        color=CATEGORY_COLORS,
        edgecolor="0.3",
        linewidth=0.8,
        hatch="//",
        alpha=0.80,
        label=legend_alt,
    )
    ymax = max(max(h_base), max(h_alt), 1)
    for xi, (hb, ha) in enumerate(zip(h_base, h_alt)):
        ax.text(
            xi - width / 2,
            hb + ymax * 0.012,
            str(hb),
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE - 2,
        )
        ax.text(
            xi + width / 2,
            ha + ymax * 0.012,
            str(ha),
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE - 2,
        )
    ax.set_xticks(x)
    ax.set_xticklabels(
        CATEGORY_LABELS,
        fontsize=FONT_SIZE - 2,
        linespacing=0.95,
    )
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_ylim(0, ymax * 1.22)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.tick_params(axis="x", labelsize=FONT_SIZE - 2, pad=2)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("center")
    ax.legend(fontsize=FONT_SIZE - 1, loc="upper right")
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.grid(alpha=0.2, axis="y")
    ax.text(
        0.02,
        0.97,
        f"Cover OpEx: {n_v_base} → {n_v_alt}\nLosing: {n_l_base} → {n_l_alt}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_500 = T / 500
    z0_1000 = T / 1000

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = sigma.notna() & declared.notna() & active.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)

    cost_170 = np.full_like(cost_a, C_FORCE_170)
    cost_75 = np.full_like(cost_a, C_FORCE_75)

    h0, n0, v0, l0, r0, cat0, f0, pi0 = compute_viability(
        sigma_a, declared_a, active_a, cost_a, margin_a, pledge_met, z0_500, r_over_t, a0
    )
    hA, nA, vA, lA, rA, catA, fA, piA = compute_viability(
        sigma_a, declared_a, active_a, cost_a, margin_a, pledge_met, z0_1000, r_over_t, a0
    )
    hB, nB, vB, lB, rB, catB, fB, piB = compute_viability(
        sigma_a, declared_a, active_a, cost_170, margin_a, pledge_met, z0_1000, r_over_t, a0
    )
    hC, nC, vC, lC, rC, catC, fC, piC = compute_viability(
        sigma_a, declared_a, active_a, cost_75, margin_a, pledge_met, z0_500, r_over_t, a0
    )
    hD, nD, vD, lD, rD, catD, fD, piD = compute_viability(
        sigma_a, declared_a, active_a, cost_75, margin_a, pledge_met, z0_1000, r_over_t, a0
    )

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].values,
            "ticker": df.loc[complete, "pool_name.ticker"].values,
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "active_pledge_ada": active_a,
            "margin": margin_a,
            "fixed_cost_ada": cost_a,
            "pledge_met": pledge_met,
            "f_base_k500_c_declared": f0,
            "Pi_base_k500_c_declared": pi0,
            "r_base_k500_c_declared": r0,
            "category_base": cat0,
            "f_A_k1000_c_declared": fA,
            "Pi_A_k1000_c_declared": piA,
            "r_A_k1000_c_declared": rA,
            "category_A": catA,
            "f_B_k1000_c170": fB,
            "Pi_B_k1000_c170": piB,
            "r_B_k1000_c170": rB,
            "category_B": catB,
            "f_C_k500_c75": fC,
            "Pi_C_k500_c75": piC,
            "r_C_k500_c75": rC,
            "category_C": catC,
            "f_D_k1000_c75": fD,
            "Pi_D_k1000_c75": piD,
            "r_D_k1000_c75": rD,
            "category_D": catD,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(18.5, 11.0), constrained_layout=True)
    draw_panel(
        axes[0, 0],
        h0,
        hA,
        title=r"A: $k\!:\,500\to1000$, $c_i$ unchanged",
        legend_base=r"$k=500$, declared $c_i$",
        legend_alt=r"$k=1000$, declared $c_i$",
        n_v_base=v0,
        n_l_base=l0,
        n_v_alt=vA,
        n_l_alt=lA,
    )
    draw_panel(
        axes[0, 1],
        h0,
        hB,
        title=r"B: $k\!:\,500\to1000$, all $c_i\to170$",
        legend_base=r"$k=500$, declared $c_i$",
        legend_alt=r"$k=1000$, $c_i=170$",
        n_v_base=v0,
        n_l_base=l0,
        n_v_alt=vB,
        n_l_alt=lB,
    )
    draw_panel(
        axes[1, 0],
        h0,
        hC,
        title=r"C: $k=500$, all $c_i\to75$",
        legend_base=r"$k=500$, declared $c_i$",
        legend_alt=r"$k=500$, $c_i=75$",
        n_v_base=v0,
        n_l_base=l0,
        n_v_alt=vC,
        n_l_alt=lC,
    )
    draw_panel(
        axes[1, 1],
        h0,
        hD,
        title=r"D: $k\!:\,500\to1000$, all $c_i\to75$",
        legend_base=r"$k=500$, declared $c_i$",
        legend_alt=r"$k=1000$, $c_i=75$",
        n_v_base=v0,
        n_l_base=l0,
        n_v_alt=vD,
        n_l_alt=lD,
    )

    fig.suptitle(
        "Epoch 644 — theoretical viability under interaction effects\n"
        + rf"$r=\Pi_i/C^*$, $C^*={C_STAR_ADA:.1f}$ ADA/epoch; "
        + rf"$R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B, $a_0={a0}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"C*={C_STAR_ADA:.4f} ADA/epoch")
    print(f"Baseline k=500 declared c: cover={v0}, losing={l0}")
    print(f"A k=1000 declared c:       cover={vA}, losing={lA}")
    print(f"B k=1000 c=170:            cover={vB}, losing={lB}")
    print(f"C k=500  c=75:             cover={vC}, losing={lC}")
    print(f"D k=1000 c=75:             cover={vD}, losing={lD}")
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
