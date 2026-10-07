#!/usr/bin/env python3
"""Operator reward vs stake: k=500 and k=1000, matching the gross-reward figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = 14.9e6
T = 38.8e9
K_CASES = (500, 1000)
a0 = 0.3
p_i = 20_000_000.0
c_i = 170.0
m_i = 0.05
SIGMA_MAX = 300e6
N_POINTS = 4000
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "pool_operator_reward_vs_sigma_k500_k1000.png"
COLORS = ("#1f77b4", "#ff7f0e")
STYLES = ("-", "--")


def gross_pool_reward(
    sigma: np.ndarray,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0_ada)
    p_tilde = np.minimum(np.minimum(p, sigma_tilde), z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return (r_scale / (1.0 + a0_value)) * (
        sigma_tilde + a0_value * p_tilde * inner / z0_ada
    )


def operator_reward(
    sigma: np.ndarray,
    p: float,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = gross_pool_reward(sigma, p, z0_ada, r_scale, a0_value)
    p_hat = np.minimum(np.minimum(p, np.maximum(sigma, 0.0)), z0_ada)
    pledge_share = np.divide(
        p_hat, sigma, out=np.ones_like(sigma), where=sigma > 0
    )
    pledge_share = np.clip(pledge_share, 0.0, 1.0)
    share = m + (1.0 - m) * pledge_share
    profitable = c + (f_val - c) * share
    return np.where(f_val > c, profitable, f_val)


def main() -> None:
    sigma = np.linspace(0.0, SIGMA_MAX, N_POINTS)
    z0_by_k = {k: T / k for k in K_CASES}

    fig, ax = plt.subplots(1, 1, figsize=(10.5, 5.4), constrained_layout=True)
    for k, color, style in zip(K_CASES, COLORS, STYLES):
        z0 = z0_by_k[k]
        y = operator_reward(sigma, p_i, z0, r_over_t, a0, c_i, m_i)
        ax.plot(
            sigma,
            y,
            color=color,
            linestyle=style,
            linewidth=2.2,
            label=rf"$k={k}$, $z_0={z0/1e6:.1f}$M",
        )
        ax.axvline(z0, linestyle=":", color="0.45", linewidth=1.2)

    ax.set_xlim(0.0, SIGMA_MAX)
    ax.set_ylim(0.0, 30_000.0)
    ax.set_xlabel(r"Pool Stake in ADA ($\sigma_i$)", fontsize=FONT_SIZE)
    ax.set_ylabel(
        r"Operator reward per epoch in ADA ($\Pi_i$)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(8, 8))
    ax.grid(alpha=0.35)
    ax.legend(fontsize=FONT_SIZE, loc="upper left", frameon=True)
    ax.set_title("Pool operator reward vs pool stake", fontsize=FONT_SIZE)

    z0_500 = z0_by_k[500]
    z0_1000 = z0_by_k[1000]
    ax.text(
        0.98,
        0.97,
        "\n".join(
            [
                rf"$R = {R/1e6:.1f}$M ADA/epoch",
                rf"$T = {T/1e9:.1f}$B ADA",
                rf"$k = 500$, $z_0 = {z0_500/1e6:.1f}$M",
                rf"$k = 1000$, $z_0 = {z0_1000/1e6:.1f}$M",
                rf"$a_0 = {a0}$, $p_i=\hat p_i = {p_i/1e6:.0f}$M",
                rf"$c_i = {c_i:.0f}$ ADA, $m_i = {100*m_i:.0f}$%",
            ]
        ),
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "0.55",
            "alpha": 0.95,
        },
    )
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
