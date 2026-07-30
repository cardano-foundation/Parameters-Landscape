#!/usr/bin/env python3
"""Reward function f(sigma, p; z0) vs pledge when a0 changes (k=500, sigma=z0)."""

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
P_MIN = 0.0
P_MAX = 77e6
N_POINTS = 3000

z0 = T / k
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "Reward_function_vs_pledge_a0_cases.png"


def gross_pool_reward(
    sigma: float,
    p: np.ndarray | float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
) -> np.ndarray:
    p_arr = np.asarray(p, dtype=float)
    sigma_tilde = min(sigma, z0_ada)
    p_tilde = np.minimum(p_arr, z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return (r_scale / (1.0 + a0_value)) * (
        sigma_tilde + a0_value * p_tilde * inner / z0_ada
    )


def main() -> None:
    p = np.linspace(P_MIN, P_MAX, N_POINTS)
    sigma_val = z0
    cases = [
        (a0, "-", "C0"),
        (a0_alt, "--", "C0"),
    ]

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    for a0_val, style, color in cases:
        y = gross_pool_reward(sigma_val, p, z0, r_over_t, a0_val)
        y = np.where(p <= sigma_val, y, np.nan)
        ax.plot(
            p,
            y,
            linewidth=2.2,
            linestyle=style,
            color=color,
            label=rf"$a_0={a0_val}$",
        )

    ax.axvline(z0, linestyle=":", color="0.45", linewidth=1.2)
    ax.set_xlim(0.0, float(p[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$f(\sigma_i,p_i;z_0)$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(6, 6))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="lower right")
    ax.set_title(
        r"Reward function $f(\sigma_i,p_i;z_0)$ vs pledge when $a_0$ changes"
        "\n"
        rf"$k={k}$, $\sigma={sigma_val/1e6:.0f}$M",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
