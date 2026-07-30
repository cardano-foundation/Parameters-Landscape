#!/usr/bin/env python3
"""Reward function f(sigma, p; z0) vs pool stake when a0 changes (k fixed)."""

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
a0_alt = 0.6
p_i = 770_000.0
SIGMA_MIN = 1.0
SIGMA_MAX = 100e6
N_POINTS = 3000

z0 = T / k
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "Reward_function_vs_sigma_a0_cases.png"


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


def main() -> None:
    sigma = np.linspace(SIGMA_MIN, SIGMA_MAX, N_POINTS)
    y_base = gross_pool_reward(sigma, p_i, z0, r_over_t, a0)
    y_new = gross_pool_reward(sigma, p_i, z0, r_over_t, a0_alt)
    feasible = sigma >= p_i
    y_base = np.where(feasible, y_base, np.nan)
    y_new = np.where(feasible, y_new, np.nan)

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    ax.plot(sigma, y_base, linewidth=2.2, color="C0", linestyle="-", label=rf"$a_0={a0}$")
    ax.plot(
        sigma, y_new, linewidth=2.2, color="C0", linestyle="--", label=rf"$a_0={a0_alt}$"
    )
    ax.axvline(z0, linestyle=":", color="0.45", linewidth=1.2)
    ax.set_xlim(0.0, float(sigma[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$f(\sigma_i,p_i;z_0)$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="lower right")
    ax.set_title(
        r"Reward function $f(\sigma_i,p_i;z_0)$ vs pool size when $a_0$ changes"
        "\n"
        rf"$k={k}$, $p_i={p_i/1e3:.0f}$K; $a_0={a0}$ vs $a_0={a0_alt}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
