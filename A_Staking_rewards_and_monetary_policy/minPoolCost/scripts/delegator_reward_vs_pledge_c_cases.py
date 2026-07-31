#!/usr/bin/env python3
"""Delegator reward per unit vs pledge when reported min pool cost c changes (k=500)."""

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
c_i = 170.0
c_i_alt = 340.0
m_i = 0.05
SIGMA_FIXED = 20e6
P_MIN = 0.0
P_MAX = 77e6
N_POINTS = 3000

z0 = T / k
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "delegator_reward_vs_pledge_c_cases.png"


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


def delegator_reward_per_unit(
    sigma: float,
    p: np.ndarray | float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = gross_pool_reward(sigma, p, z0_ada, r_scale, a0_value)
    return np.where(f_val > c, (1.0 - m) * (f_val - c) / sigma, 0.0)


def main() -> None:
    p = np.linspace(P_MIN, P_MAX, N_POINTS)
    cases = [
        (SIGMA_FIXED, c_i, "-"),
        (z0, c_i, "-"),
        (SIGMA_FIXED, c_i_alt, "--"),
        (z0, c_i_alt, "--"),
    ]

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    for sigma_val, c_val, style in cases:
        y = delegator_reward_per_unit(sigma_val, p, z0, r_over_t, a0, c_val, m_i)
        y = np.where(p <= sigma_val, y, np.nan)
        ax.plot(
            p,
            y,
            linewidth=2.2,
            linestyle=style,
            label=rf"$\sigma={sigma_val/1e6:.1f}$M, $c={c_val:.0f}$",
        )

    ax.axvline(z0, linestyle=":", color="0.45", linewidth=1.2)
    ax.set_xlim(0.0, float(p[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Delegator reward per unit of stake", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(6, 6))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="lower right")
    ax.set_title(
        "Delegator reward per unit of stake vs pledge (k=500)\n"
        f"a0={a0}, m={100*m_i:.0f}%; "
        f"sigma in {{20M, z0}}, c in {{{c_i:.0f}, {c_i_alt:.0f}}}",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
