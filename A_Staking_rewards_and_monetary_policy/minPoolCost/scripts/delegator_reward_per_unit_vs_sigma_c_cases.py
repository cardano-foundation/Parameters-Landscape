#!/usr/bin/env python3
"""Net pool reward per unit of stake (f - c)/sigma vs sigma for different min pool costs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = 14.9e6
T = 38.8e9
k = 500
a0 = 0.3
p_i = 770_000.0
C_CASES = (340.0, 170.0, 75.0)
SIGMA_MIN = 1.0
SIGMA_MAX = 100e6
N_POINTS = 3000

z0 = T / k
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "delegator_reward_per_unit_vs_sigma_c_cases.png"


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


def net_reward_per_unit(
    sigma: np.ndarray,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
) -> np.ndarray:
    f_val = gross_pool_reward(sigma, p, z0_ada, r_scale, a0_value)
    return np.maximum(f_val - c, 0.0) / sigma


def main() -> None:
    sigma = np.linspace(SIGMA_MIN, SIGMA_MAX, N_POINTS)
    feasible = sigma >= p_i

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    for c_val in C_CASES:
        y = net_reward_per_unit(sigma, p_i, z0, r_over_t, a0, c_val)
        y = np.where(feasible, y, np.nan)
        ax.plot(
            sigma,
            y,
            linewidth=2.2,
            label=rf"$k={k}$, $c_i={c_val:.0f}$",
        )

    ax.axvline(z0, linestyle=":", color="0.45", linewidth=1.2)
    ax.set_xlim(0.0, float(sigma[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(
        r"$\dfrac{\max\{f(\sigma_i,p_i;z_0)-c_i,\,0\}}{\sigma_i}$",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="upper right")
    ax.set_title(
        "Delegator rewards per unit of stake\n"
        rf"($k={k}$, $p_i={p_i/1e3:.0f}$K, $a_0={a0}$; "
        rf"$c\in{{{', '.join(f'{c:.0f}' for c in C_CASES)}}}$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
