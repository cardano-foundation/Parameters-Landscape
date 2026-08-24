#!/usr/bin/env python3
"""
Difference in pool operator rewards (%) when (k, c) move from
(k=500, c=170) to (k=1000, c=75), epoch-644 R and T.

Pi = c + (f - c) * [m + (1-m) p/sigma]  if f > c, else f.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

DIR = Path(__file__).resolve().parent
PARENT = DIR.parent
PARAMS_JSON = PARENT / "f_reward_params_epoch_644.json"
OUT_PNG = DIR / "heatmap_operator_reward_pct_k1000_c75_epoch_644.png"

FONT_SIZE = 12
K0 = 500
K1 = 1000
C0 = 170.0
C1 = 75.0
M = 0.05
N_HEATMAP = 280
SIGMA_MAX_ADA = 70e6
PCT_LIM = 60.0

HEATMAP_CMAP_DIFF = LinearSegmentedColormap.from_list(
    "red_yellow_green_blue",
    ["#d73027", "#fc8d59", "#ffffbf", "#1a9850", "#2166ac"],
)


def gross_grid(S: np.ndarray, P: np.ndarray, z0: float, r_over_t: float, a0: float) -> np.ndarray:
    sigma_tilde = np.minimum(S, z0)
    p_tilde = np.minimum(P, z0)
    inner = sigma_tilde - p_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * p_tilde * inner / z0
    )


def operator_grid(
    S: np.ndarray,
    P: np.ndarray,
    z0: float,
    r_over_t: float,
    a0: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = gross_grid(S, P, z0, r_over_t, a0)
    share = m + (1.0 - m) * (P / S)
    reward_if_profitable = c + (f_val - c) * share
    return np.where(f_val > c, reward_if_profitable, f_val)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_500 = T / K0
    z0_1000 = T / K1

    sigma_1d = np.linspace(1.0, SIGMA_MAX_ADA, N_HEATMAP)
    p_1d = np.linspace(0.0, SIGMA_MAX_ADA, N_HEATMAP)
    S, P = np.meshgrid(sigma_1d, p_1d)

    pi0 = operator_grid(S, P, z0_500, r_over_t, a0, C0, M)
    pi1 = operator_grid(S, P, z0_1000, r_over_t, a0, C1, M)
    pct = np.where(pi0 > 0, 100.0 * (pi1 - pi0) / pi0, np.nan)

    infeasible = P > S
    masked = np.ma.masked_where(infeasible | ~np.isfinite(pct), pct)

    cmap = HEATMAP_CMAP_DIFF.copy()
    cmap.set_bad(color="lightgray")

    fig, ax = plt.subplots(figsize=(8.2, 6.4), constrained_layout=True)
    im = ax.pcolormesh(
        S, P, masked, shading="auto", cmap=cmap, vmin=-PCT_LIM, vmax=PCT_LIM
    )

    ax.plot([0.0, SIGMA_MAX_ADA], [0.0, SIGMA_MAX_ADA], "k--", linewidth=1.2, alpha=0.85)
    ax.axvline(z0_1000, color="0.15", linestyle="--", linewidth=1.2, alpha=0.9)
    ax.text(
        z0_1000 * 1.02,
        0.12 * SIGMA_MAX_ADA,
        "new saturation level",
        fontsize=FONT_SIZE,
        rotation=90,
        va="bottom",
        ha="left",
        color="0.15",
    )

    # Centroid of the infeasible triangle (0, ymax) -- (0, 0) -- (ymax, ymax)
    ax.text(
        SIGMA_MAX_ADA / 3.0,
        2.0 * SIGMA_MAX_ADA / 3.0,
        "infeasible area",
        fontsize=FONT_SIZE,
        ha="center",
        va="center",
        color="0.15",
    )

    ax.set_xlim(0.0, SIGMA_MAX_ADA)
    ax.set_ylim(0.0, SIGMA_MAX_ADA)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(6, 6))
    ax.ticklabel_format(axis="y", style="sci", scilimits=(6, 6))
    ax.set_title(
        "Difference in Pool Operator Rewards (%)\n"
        rf"Initial cond.: $k={K0}$, $c={C0:.0f}$ ADA; "
        rf"Final cond.: $k={K1}$, $c={C1:.0f}$ ADA",
        fontsize=FONT_SIZE,
    )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Percentage difference (%)", fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE)

    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    finite = masked.compressed()
    print(f"R={R:.2f}, T={T:.2f}, a0={a0}, m={M}")
    print(f"z0_500={z0_500/1e6:.2f}M, z0_1000={z0_1000/1e6:.2f}M")
    print(f"pct range (feasible): {float(np.nanmin(finite)):.1f}% to {float(np.nanmax(finite)):.1f}%")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
