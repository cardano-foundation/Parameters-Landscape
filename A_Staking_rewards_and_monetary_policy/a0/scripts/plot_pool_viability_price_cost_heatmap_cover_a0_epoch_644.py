#!/usr/bin/env python3
"""Epoch 644 — r≥1 heatmap vs ADA price and USD opex, a0=0.3 vs a0=0.6.

k=500 held fixed. Active pools, merged snapshot.

Writes:
  pool_viability_price_cost_heatmap_cover_a0_epoch_644.png
  pool_viability_price_cost_a0_epoch_644.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from a0_common import PARAMS_JSON, gross_pool_reward, load_active_pools

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_viability_price_cost_heatmap_cover_a0_epoch_644.png"
OUT_CSV = DIR / "pool_viability_price_cost_a0_epoch_644.csv"

FONT_SIZE = 12
EPOCHS_PER_MONTH = 6.0
A0_0 = 0.3
A0_1 = 0.6
PRICES = (0.10, 0.15, 0.25, 0.30, 0.50)
OPEX = (
    {"usd_month": 39.0 * 0.25 * EPOCHS_PER_MONTH, "label": "58.5 USD/mo"},
    {"usd_month": 171.0 * 0.25 * EPOCHS_PER_MONTH, "label": "256.5 USD/mo"},
    {"usd_month": 667.0, "label": "667 USD/mo"},
    {"usd_month": 986.0 * 0.25 * EPOCHS_PER_MONTH, "label": "1479 USD/mo"},
)
HEAT_CMAP = LinearSegmentedColormap.from_list(
    "cover_teal",
    ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#084594"],
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


def c_star(usd_month: float, price: float) -> float:
    return usd_month / EPOCHS_PER_MONTH / price


def n_ge1(pi: np.ndarray, pledge_met: np.ndarray, cstar: float) -> int:
    r = np.divide(pi, cstar, out=np.full_like(pi, np.nan), where=cstar > 0)
    return int((r[pledge_met] >= 1.0).sum())


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    k = int(params["k"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = T / k
    r_over_t = R / T

    df = load_active_pools()
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["live_pledge"].fillna(df["pledged"]), errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    complete = sigma.notna() & declared.notna() & active.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)

    def pi_at(a0):
        f = gross_pool_reward(sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=a0)
        f = np.where(pledge_met, np.maximum(f, 0.0), 0.0)
        return operator_reward(f, cost_a, margin_a, active_a, sigma_a)

    pi0 = pi_at(A0_0)
    pi1 = pi_at(A0_1)

    rows = []
    mat0 = np.zeros((len(OPEX), len(PRICES)))
    mat1 = np.zeros((len(OPEX), len(PRICES)))
    for i, opex in enumerate(OPEX):
        for j, p in enumerate(PRICES):
            cs = c_star(opex["usd_month"], p)
            n0 = n_ge1(pi0, pledge_met, cs)
            n1 = n_ge1(pi1, pledge_met, cs)
            mat0[i, j] = n0
            mat1[i, j] = n1
            rows.append(
                {
                    "ada_usd": p,
                    "usd_month": opex["usd_month"],
                    "opex_label": opex["label"],
                    "c_star_ada": cs,
                    "n_r_ge1_a0_0p3": n0,
                    "n_r_ge1_a0_0p6": n1,
                    "delta_a0_0p6_minus_0p3": n1 - n0,
                    "n_active": int(pledge_met.sum()),
                }
            )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16.2, 4.8), constrained_layout=True)
    ylabels = [o["label"] for o in OPEX]
    xlabels = [f"${p:.2f}" for p in PRICES]
    vmax = max(mat0.max(), mat1.max())
    panels = (
        (mat0, rf"$r\geq 1$, $a_0={A0_0}$"),
        (mat1, rf"$r\geq 1$, $a_0={A0_1}$"),
    )
    for ax, (mat, title) in zip(axes[:2], panels):
        im = ax.imshow(mat, cmap=HEAT_CMAP, vmin=0.0, vmax=vmax, aspect="auto")
        ax.set_xticks(np.arange(len(PRICES)))
        ax.set_xticklabels(xlabels, fontsize=FONT_SIZE - 1)
        ax.set_yticks(np.arange(len(OPEX)))
        ax.set_yticklabels(ylabels, fontsize=FONT_SIZE - 1)
        ax.set_xlabel("ADA price (USD)", fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        for i in range(len(OPEX)):
            for j in range(len(PRICES)):
                ax.text(
                    j, i, f"{int(mat[i, j])}",
                    ha="center", va="center", fontsize=FONT_SIZE - 1, color="0.1",
                )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 1)

    delta = mat1 - mat0
    lim = max(abs(float(delta.min())), abs(float(delta.max())), 1.0)
    im = axes[2].imshow(delta, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
    axes[2].set_xticks(np.arange(len(PRICES)))
    axes[2].set_xticklabels(xlabels, fontsize=FONT_SIZE - 1)
    axes[2].set_yticks(np.arange(len(OPEX)))
    axes[2].set_yticklabels(ylabels, fontsize=FONT_SIZE - 1)
    axes[2].set_xlabel("ADA price (USD)", fontsize=FONT_SIZE)
    axes[2].set_title(rf"$\Delta$: $a_0={A0_1}$ minus $a_0={A0_0}$", fontsize=FONT_SIZE)
    for i in range(len(OPEX)):
        for j in range(len(PRICES)):
            axes[2].text(
                j, i, f"{int(delta[i, j]):+d}",
                ha="center", va="center", fontsize=FONT_SIZE - 1, color="0.1",
            )
    fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 1)

    fig.suptitle(
        r"Epoch 644 — Active pools with $r=\Pi_i/C^*(P)\geq 1$"
        "\n"
        rf"($k={k}$; $a_0={A0_0}$ vs $a_0={A0_1}$; snapshot $\sigma,p,\hat p,c,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    paper = [r for r in rows if r["usd_month"] == 667.0 and r["ada_usd"] == 0.15][0]
    print(
        f"paper cell $667, $0.15: a0=0.3 n={paper['n_r_ge1_a0_0p3']}, "
        f"a0=0.6 n={paper['n_r_ge1_a0_0p6']}, "
        f"delta={paper['delta_a0_0p6_minus_0p3']}, C*={paper['c_star_ada']:.1f}"
    )


if __name__ == "__main__":
    main()
