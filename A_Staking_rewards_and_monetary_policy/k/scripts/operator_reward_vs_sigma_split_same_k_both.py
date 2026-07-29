#!/usr/bin/env python3
"""Operator reward vs sigma: same-k split for k=500 (blue) and k=1000 (orange)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = 14.9e6
T = 38.8e9
k = 500
k_alt = 1000
a0 = 0.3
c_i = 170.0
m_i = 0.05
p_i = 770_000.0
SIGMA_MIN = 1.0
SIGMA_MAX = 100e6
N_POINTS = 3000

z0 = T / k
z0_alt = T / k_alt
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "operator_reward_vs_sigma_split_same_k_both.png"


def gross_pool_reward(
    sigma: np.ndarray | float,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
) -> np.ndarray:
    sigma_arr = np.asarray(sigma, dtype=float)
    sigma_tilde = np.minimum(sigma_arr, z0_ada)
    p_tilde = min(p, z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return (r_scale / (1.0 + a0_value)) * (
        sigma_tilde + a0_value * p_tilde * inner / z0_ada
    )


def operator_reward(
    sigma: np.ndarray | float,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    sigma_arr = np.asarray(sigma, dtype=float)
    f_val = gross_pool_reward(sigma_arr, p, z0_ada, r_scale, a0_value)
    share = m + (1.0 - m) * (p / sigma_arr)
    reward_if_profitable = c + (f_val - c) * share
    return np.where(f_val > c, reward_if_profitable, f_val)


def main() -> None:
    sigma = np.linspace(SIGMA_MIN, SIGMA_MAX, N_POINTS)
    cases = [
        (k, z0, "C0"),
        (k_alt, z0_alt, "C1"),
    ]

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    feasible = sigma >= p_i
    for k_val, z0_val, color in cases:
        y_single = operator_reward(sigma, p_i, z0_val, r_over_t, a0, c_i, m_i)
        y_split = 2.0 * operator_reward(
            sigma / 2.0, p_i / 2.0, z0_val, r_over_t, a0, c_i, m_i
        )
        y_single = np.where(feasible, y_single, np.nan)
        y_split = np.where(feasible, y_split, np.nan)
        ax.plot(
            sigma,
            y_single,
            linewidth=2.2,
            color=color,
            linestyle="-",
            label=rf"$k={k_val}$ one pool ($z_0={z0_val/1e6:.1f}$M)",
        )
        ax.plot(
            sigma,
            y_split,
            linewidth=2.2,
            color=color,
            linestyle="--",
            label=rf"$k={k_val}$ split: $2\times\Pi(\sigma/2,p/2)$",
        )
        ax.axvline(z0_val, linestyle=":", color=color, linewidth=1.2, alpha=0.7)

    ax.set_xlim(0.0, float(sigma[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$\sigma_i$ (ADA) [pre-split total stake]", fontsize=FONT_SIZE)
    ax.set_ylabel(r"Operator reward $\Pi_i$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE - 1, loc="lower right")
    ax.set_title(
        r"Operator reward vs pool size: $k=500$ vs $k=1000$"
        "\n"
        rf"$a_0={a0}$, $p_i={p_i/1e3:.0f}$K, $c={c_i:.0f}$, $m={100*m_i:.0f}\%$"
        r"; solid = one pool, dashed = split",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
