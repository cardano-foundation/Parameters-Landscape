#!/usr/bin/env python3
"""Illustrate: a slightly oversaturated pool can beat a very small pool for delegators."""

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
p_i = 770_000.0
c_i = 170.0
m_i = 0.05
SIGMA_MIN = 1.0
SIGMA_MAX = 100e6
N_POINTS = 4000

# Pool A: unsaturated at k=500, slightly oversaturated at k=1000
SIGMA_A = 1.10 * (T / k_alt)

z0 = T / k
z0_alt = T / k_alt
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "slightly_oversaturated_vs_small_pool.png"


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


def delegator_reward_per_unit(
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
    return np.where(f_val > c, (1.0 - m) * (f_val - c) / sigma_arr, 0.0)


def main() -> None:
    sigma = np.linspace(SIGMA_MIN, SIGMA_MAX, N_POINTS)
    feasible = sigma >= p_i
    y_500 = np.where(
        feasible,
        delegator_reward_per_unit(sigma, p_i, z0, r_over_t, a0, c_i, m_i),
        np.nan,
    )
    y_1000 = np.where(
        feasible,
        delegator_reward_per_unit(sigma, p_i, z0_alt, r_over_t, a0, c_i, m_i),
        np.nan,
    )

    y_a_500 = float(
        delegator_reward_per_unit(SIGMA_A, p_i, z0, r_over_t, a0, c_i, m_i)
    )
    y_a_1000 = float(
        delegator_reward_per_unit(SIGMA_A, p_i, z0_alt, r_over_t, a0, c_i, m_i)
    )

    # Stake threshold on k=1000 curve where reward equals Pool A's oversaturated return
    # (rising side, sigma < z0_alt): pools below this are worse than A at k=1000
    rising = (sigma < z0_alt) & np.isfinite(y_1000)
    below = rising & (y_1000 <= y_a_1000)
    sigma_threshold = float(sigma[below][-1]) if np.any(below) else float("nan")

    fig, ax = plt.subplots(1, 1, figsize=(9.5, 5.2), constrained_layout=True)

    if np.isfinite(sigma_threshold):
        ax.axvspan(
            0.0,
            sigma_threshold / 1e6,
            color="0.82",
            alpha=0.55,
            zorder=0,
            label=rf"Worse than A at $k={k_alt}$ "
            rf"($\sigma\lesssim {sigma_threshold/1e6:.1f}$M or "
            rf"$\sigma\gtrsim {SIGMA_A/1e6:.1f}$M)",
        )
        ax.axvline(
            sigma_threshold / 1e6,
            color="0.35",
            linestyle="-",
            linewidth=1.6,
            zorder=1,
        )

    # Beyond Pool A on the k=1000 curve, returns keep falling with oversaturation
    ax.axvspan(
        SIGMA_A / 1e6,
        SIGMA_MAX / 1e6,
        color="0.82",
        alpha=0.55,
        zorder=0,
    )

    ax.plot(
        sigma / 1e6,
        y_500,
        linewidth=2.2,
        color="C0",
        zorder=2,
        label=rf"$k={k}$ ($z_0={z0/1e6:.1f}$M)",
    )
    ax.plot(
        sigma / 1e6,
        y_1000,
        linewidth=2.2,
        color="C1",
        linestyle="--",
        zorder=2,
        label=rf"$k={k_alt}$ ($z_0={z0_alt/1e6:.1f}$M)",
    )

    ax.axvline(z0 / 1e6, linestyle=":", color="C0", linewidth=1.2, alpha=0.8, zorder=1)
    ax.axvline(
        z0_alt / 1e6, linestyle=":", color="C1", linewidth=1.2, alpha=0.8, zorder=1
    )
    ax.axhline(
        y_a_1000,
        linestyle="--",
        color="0.2",
        linewidth=2.0,
        zorder=3,
        label=rf"Pool A return at $k={k_alt}$ (threshold)",
    )

    ax.scatter(
        [SIGMA_A / 1e6],
        [y_a_500],
        s=70,
        color="C0",
        zorder=5,
        label=rf"Pool A at $k={k}$ ({SIGMA_A/1e6:.1f}M, unsaturated)",
    )
    ax.scatter(
        [SIGMA_A / 1e6],
        [y_a_1000],
        s=70,
        facecolors="none",
        edgecolors="C1",
        linewidths=2.0,
        zorder=5,
        label=rf"Pool A at $k={k_alt}$ ({SIGMA_A/1e6:.1f}M, slightly oversat.)",
    )

    ax.annotate(
        "Pool A\n$k=500$",
        xy=(SIGMA_A / 1e6, y_a_500),
        xytext=(SIGMA_A / 1e6 + 8, y_a_500 - 0.35e-4),
        fontsize=FONT_SIZE - 1,
        arrowprops=dict(arrowstyle="->", color="0.35", lw=1.0),
    )
    ax.annotate(
        "Pool A\n$k=1000$",
        xy=(SIGMA_A / 1e6, y_a_1000),
        xytext=(SIGMA_A / 1e6 + 10, y_a_1000 - 0.85e-4),
        fontsize=FONT_SIZE - 1,
        arrowprops=dict(arrowstyle="->", color="0.35", lw=1.0),
    )
    if np.isfinite(sigma_threshold):
        ax.annotate(
            rf"not preferred vs A"
            "\n"
            rf"($\sigma\lesssim {sigma_threshold/1e6:.1f}$M)",
            xy=(sigma_threshold / 2e6, y_a_1000 * 0.45),
            fontsize=FONT_SIZE - 1,
            color="0.25",
            ha="center",
            va="center",
        )
        ax.annotate(
            "not preferred vs A\n(more oversaturated)",
            xy=((SIGMA_A + SIGMA_MAX) / 2e6, y_a_1000 * 0.45),
            fontsize=FONT_SIZE - 1,
            color="0.25",
            ha="center",
            va="center",
        )

    ax.set_xlim(0.0, SIGMA_MAX / 1e6)
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(r"stake (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(
        r"$\dfrac{(1-m)\,\max\{f(\sigma_i,p_i;z_0)-c,\,0\}}{\sigma_i}$",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE - 1, loc="lower right")
    ax.set_title(
        "A slightly oversaturated pool can remain preferred\n"
        rf"($a_0={a0}$, $p_i={p_i/1e3:.0f}$K, $c={c_i:.0f}$, $m={100*m_i:.0f}\%$; "
        rf"$k={k}$ vs $k={k_alt}$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)
    print(
        f"Pool A: sigma={SIGMA_A/1e6:.2f}M, "
        f"y(k=500)={y_a_500:.6e}, y(k=1000)={y_a_1000:.6e}"
    )
    print(f"Threshold stake on rising k=1000 curve: {sigma_threshold/1e6:.2f}M")


if __name__ == "__main__":
    main()
