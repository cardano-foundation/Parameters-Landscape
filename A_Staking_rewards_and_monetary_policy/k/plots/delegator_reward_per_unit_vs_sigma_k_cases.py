#!/usr/bin/env python3
"""Net pool reward per unit of stake (f - c)/sigma vs sigma for k=500 vs k=1000."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

R = 14.9e6
T = 38.8e9
a0 = 0.3
p_i = 770_000.0
c_i = 170.0
K_CASES = (500, 1000)
SIGMA_MIN = 1.0
SIGMA_MAX = 100e6
N_POINTS = 3000
STAKE_UNIT = 1_000.0

r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "delegator_reward_per_unit_vs_sigma_k_cases.png"
OUTPUT_PATH_ZOOM = OUT_DIR / "delegator_reward_per_unit_vs_sigma_k_cases_zoom.png"


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

    series: list[tuple[int, np.ndarray]] = []
    for k_val in K_CASES:
        z0 = T / k_val
        y = net_reward_per_unit(sigma, p_i, z0, r_over_t, a0, c_i) * STAKE_UNIT
        y = np.where(feasible, y, np.nan)
        series.append((k_val, y))

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    for k_val, y in series:
        ax.plot(
            sigma,
            y,
            linewidth=2.2,
            label=rf"$k={k_val}$, $c_i={c_i:.0f}$",
        )

    ax.axvline(T / K_CASES[0], linestyle=":", color="0.45", linewidth=1.2)
    ax.set_xlim(0.0, float(sigma[-1]))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(
        r"$\dfrac{\max\{f(\sigma_i,p_i)-c_i,\,0\}}{\sigma_i}$"
        "\n(ADA per 1000 ADA staked)",
        fontsize=FONT_SIZE,
    )
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="upper right")

    ax.set_title(
        "Per-epoch delegator rewards per unit of stake\n"
        rf"($k\in\{{{', '.join(str(k) for k in K_CASES)}\}}$, "
        rf"$p_i={p_i/1e3:.0f}$K, $a_0={a0}$; $c={c_i:.0f}$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)

    # Zoomed view around sigma ~= 0.4e8 with requested y-range.
    fig_z, ax_z = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)
    for k_val, y in series:
        ax_z.plot(
            sigma,
            y,
            linewidth=2.2,
            label=rf"$k={k_val}$, $c_i={c_i:.0f}$",
        )
    ax_z.axvline(0.4e8, linestyle=":", color="0.45", linewidth=1.2)
    ax_z.set_xlim(0.0, 1.0e8)
    ax_z.set_ylim(0.25, 0.30)
    ax_z.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax_z.set_ylabel(
        r"$\dfrac{\max\{f(\sigma_i,p_i)-c_i,\,0\}}{\sigma_i}$"
        "\n(ADA per 1000 ADA staked)",
        fontsize=FONT_SIZE,
    )
    ax_z.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax_z.tick_params(axis="both", labelsize=FONT_SIZE)
    ax_z.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax_z.grid(alpha=0.25)
    ax_z.legend(fontsize=FONT_SIZE, loc="lower right")
    ax_z.set_title(
        r"$\mathbf{Zoom}$: Per-epoch delegator rewards per unit of stake" "\n"
        rf"($k\in\{{{', '.join(str(k) for k in K_CASES)}\}}$, "
        rf"$p_i={p_i/1e3:.0f}$K, $a_0={a0}$; $c={c_i:.0f}$, "
        r"$0\leq\sigma_i\leq10^8$)",
        fontsize=FONT_SIZE,
    )
    fig_z.savefig(OUTPUT_PATH_ZOOM, dpi=300, bbox_inches="tight")
    plt.close(fig_z)
    print("Saved:", OUTPUT_PATH_ZOOM)


if __name__ == "__main__":
    main()
