#!/usr/bin/env python3
"""
Pool desirability D_i vs actual cost ĉ_i, for minPoolCost c_min ∈ {170, 75}.

Notation:
  ĉ_i  = actual (preferred) cost
  c_min = minPoolCost
  c_i  = declared cost = max{ĉ_i, c_min}

    D_i = (1-m_i) max{f(σ_i,p_i) - c_i, 0} / σ_i
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

R = 14.9e6
T = 38.8e9
k = 500
a0 = 0.3
m_i = 0.05
# Smaller pool so D levels and slope sit mid-scale once axes are zoomed
sigma_i = 1.5e6
p_i = 500_000.0
C_MIN_OLD = 170.0
C_MIN_NEW = 75.0
# x-range: green kink (75) near centre; small margin past old c_min for its declining segment
C_MAX = 185.0
N_POINTS = 3000
STAKE_UNIT = 1_000.0

COLOR_OLD = "#e76f51"  # orange
COLOR_NEW = "#2a9d8f"  # green

z0 = T / k
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "delegator_reward_vs_c_cmin_cases.png"


def gross_pool_reward(
    sigma: float,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
) -> float:
    sigma_tilde = min(sigma, z0_ada)
    p_tilde = min(p, z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return float(
        (r_scale / (1.0 + a0_value))
        * (sigma_tilde + a0_value * p_tilde * inner / z0_ada)
    )


def D_i(
    c_hat: np.ndarray | float,
    c_min: float,
    f_val: float,
    sigma: float,
    m: float,
) -> np.ndarray:
    """Desirability: uses declared cost c_i = max{ĉ_i, c_min}."""
    c_hat_arr = np.asarray(c_hat, dtype=float)
    c_i = np.maximum(c_hat_arr, c_min)
    return np.where(
        f_val > c_i,
        (1.0 - m) * (f_val - c_i) / sigma,
        0.0,
    )


def main() -> None:
    f_val = gross_pool_reward(sigma_i, p_i, z0, r_over_t, a0)
    c_hat = np.linspace(0.0, C_MAX, N_POINTS)

    y_old = D_i(c_hat, C_MIN_OLD, f_val, sigma_i, m_i) * STAKE_UNIT
    y_new = D_i(c_hat, C_MIN_NEW, f_val, sigma_i, m_i) * STAKE_UNIT

    # Centre the y-scale on the two constrained flats
    y_flat_old = float(y_old[0])
    y_flat_new = float(y_new[0])
    y_mid = 0.5 * (y_flat_old + y_flat_new)
    y_span = max(abs(float(y_old.min()) - y_mid), abs(float(y_new.max()) - y_mid))
    ylim = (y_mid - 1.35 * y_span, y_mid + 1.35 * y_span)
    y_label = y_mid

    fig, ax = plt.subplots(1, 1, figsize=(9, 5), constrained_layout=True)

    # Green only where policies differ; orange alone (in front) after old c_min
    c_green = c_hat[c_hat < C_MIN_OLD]
    y_green = D_i(c_green, C_MIN_NEW, f_val, sigma_i, m_i) * STAKE_UNIT
    ax.plot(
        c_green,
        y_green,
        color=COLOR_NEW,
        linewidth=2.4,
        label=rf"$c_{{\min}}={C_MIN_NEW:.0f}$ (new)",
        zorder=2,
    )
    ax.plot(
        c_hat,
        y_old,
        color=COLOR_OLD,
        linewidth=2.8,
        label=rf"$c_{{\min}}={C_MIN_OLD:.0f}$ (old)",
        zorder=5,
    )

    ax.axvline(
        C_MIN_NEW,
        color=COLOR_NEW,
        linestyle="--",
        linewidth=1.4,
        alpha=0.9,
        zorder=1,
    )
    ax.axvline(
        C_MIN_OLD,
        color=COLOR_OLD,
        linestyle="--",
        linewidth=1.4,
        alpha=0.9,
        zorder=1,
    )
    # Short horizontal labels below the curves (avoid title overlap from tall rotated text)
    ax.text(
        C_MIN_NEW,
        y_flat_old - 0.012,
        rf"new $c_{{\min}}={C_MIN_NEW:.0f}$",
        color=COLOR_NEW,
        fontsize=FONT_SIZE - 1,
        ha="center",
        va="top",
        zorder=4,
    )
    ax.text(
        C_MIN_OLD,
        y_flat_old - 0.012,
        rf"old $c_{{\min}}={C_MIN_OLD:.0f}$",
        color=COLOR_OLD,
        fontsize=FONT_SIZE - 1,
        ha="center",
        va="top",
        zorder=4,
    )

    ax.set_xlim(0.0, C_MAX)
    ax.set_ylim(*ylim)
    ax.set_xlabel(r"$c_i$ (ADA) [declared cost]", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$D_i$" "\n(ADA per 1000 ADA staked)", fontsize=FONT_SIZE)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE - 1, loc="upper right")
    ax.set_title(
        r"Pool desirability $D_i(c_i)$ vs declared cost $c_i$"
        "\n"
        rf"($k={k}$, $\sigma_i={sigma_i/1e6:.1f}$M, $p_i={p_i/1e3:.0f}$K, "
        rf"$a_0={a0}$, $m_i={100*m_i:.0f}\%$; "
        r"$c_i=\max\{\hat{c}_i,c_{\min}\}$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)
    print(f"f(σ,p) = {f_val:.2f} ADA")
    print(f"ylim = {ylim}")


if __name__ == "__main__":
    main()
