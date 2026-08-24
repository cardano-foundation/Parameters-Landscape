#!/usr/bin/env python3
"""Heatmaps of theoretical f and Pi when (k, a0) move from (500, 0.3) to (1000, 0.6).

R=14.9M, T=38.8B, c=170, m=5%. Each figure: baseline | counterfactual | % difference.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

DIR = Path(__file__).resolve().parent
OUT_F = DIR / "heatmap_f_k1000_a0_0p6_interaction.png"
OUT_PI = DIR / "heatmap_Pi_k1000_a0_0p6_interaction.png"

FONT_SIZE = 12
R = 14.9e6
T = 38.8e9
A0_0 = 0.3
A0_1 = 0.6
K0 = 500
K1 = 1000
C = 170.0
M = 0.05
N = 280
SIGMA_MAX = 70e6
PCT_LIM = 60.0

CMAP_ABS = LinearSegmentedColormap.from_list(
    "yellow_green_blue",
    ["#ffffbf", "#d9ef8b", "#66bd63", "#1a9850", "#2166ac"],
)
CMAP_DIFF = LinearSegmentedColormap.from_list(
    "red_yellow_green_blue",
    ["#d73027", "#fc8d59", "#ffffbf", "#1a9850", "#2166ac"],
)


def gross(S, P, z0, r_over_t, a0):
    st = np.minimum(S, z0)
    pt = np.minimum(P, z0)
    inner = st - pt * (z0 - st) / z0
    return (r_over_t / (1.0 + a0)) * (st + a0 * pt * inner / z0)


def operator(S, P, z0, r_over_t, a0, c, m):
    f = gross(S, P, z0, r_over_t, a0)
    share = m + (1.0 - m) * (P / S)
    return np.where(f > c, c + (f - c) * share, f)


def draw_abs(ax, S, P, values, z0_line, title, cbar_label, vmax):
    infeasible = P > S
    masked = np.ma.masked_where(infeasible, values)
    cmap = CMAP_ABS.copy()
    cmap.set_bad("lightgray")
    im = ax.pcolormesh(S, P, masked, shading="auto", cmap=cmap, vmin=0.0, vmax=vmax)
    ax.plot([0, SIGMA_MAX], [0, SIGMA_MAX], "k--", lw=1.2, alpha=0.85)
    ax.axvline(z0_line, color="0.15", ls="--", lw=1.2, alpha=0.9)
    ax.text(
        SIGMA_MAX / 3.0,
        2.0 * SIGMA_MAX / 3.0,
        "infeasible area",
        fontsize=FONT_SIZE,
        ha="center",
        va="center",
        color="0.15",
    )
    ax.set_xlim(0, SIGMA_MAX)
    ax.set_ylim(0, SIGMA_MAX)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="both", style="sci", scilimits=(6, 6))
    ax.set_title(title, fontsize=FONT_SIZE)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label, fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE)


def draw_pct(ax, S, P, pct, z0_line, title):
    infeasible = P > S
    masked = np.ma.masked_where(infeasible | ~np.isfinite(pct), pct)
    cmap = CMAP_DIFF.copy()
    cmap.set_bad("lightgray")
    im = ax.pcolormesh(S, P, masked, shading="auto", cmap=cmap, vmin=-PCT_LIM, vmax=PCT_LIM)
    ax.plot([0, SIGMA_MAX], [0, SIGMA_MAX], "k--", lw=1.2, alpha=0.85)
    ax.axvline(z0_line, color="0.15", ls="--", lw=1.2, alpha=0.9)
    ax.text(
        z0_line * 1.02,
        0.12 * SIGMA_MAX,
        "new saturation level",
        fontsize=FONT_SIZE,
        rotation=90,
        va="bottom",
        ha="left",
        color="0.15",
    )
    ax.text(
        SIGMA_MAX / 3.0,
        2.0 * SIGMA_MAX / 3.0,
        "infeasible area",
        fontsize=FONT_SIZE,
        ha="center",
        va="center",
        color="0.15",
    )
    ax.set_xlim(0, SIGMA_MAX)
    ax.set_ylim(0, SIGMA_MAX)
    ax.set_xlabel(r"$\sigma_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="both", style="sci", scilimits=(6, 6))
    ax.set_title(title, fontsize=FONT_SIZE)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Percentage difference (%)", fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE)


def main() -> None:
    r_over_t = R / T
    z0_0 = T / K0
    z0_1 = T / K1
    s1d = np.linspace(1.0, SIGMA_MAX, N)
    p1d = np.linspace(0.0, SIGMA_MAX, N)
    S, P = np.meshgrid(s1d, p1d)

    f0 = gross(S, P, z0_0, r_over_t, A0_0)
    f1 = gross(S, P, z0_1, r_over_t, A0_1)
    pi0 = operator(S, P, z0_0, r_over_t, A0_0, C, M)
    pi1 = operator(S, P, z0_1, r_over_t, A0_1, C, M)
    pct_f = np.where(f0 > 0, 100.0 * (f1 - f0) / f0, np.nan)
    pct_pi = np.where(pi0 > 0, 100.0 * (pi1 - pi0) / pi0, np.nan)

    vmax_f = float(np.nanmax(np.ma.masked_where(P > S, np.maximum(f0, f1))))
    vmax_pi = float(np.nanmax(np.ma.masked_where(P > S, np.maximum(pi0, pi1))))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    draw_abs(
        axes[0], S, P, f0, z0_0,
        title=rf"$k={K0}$, $a_0={A0_0}$",
        cbar_label=r"$f(\sigma_i,p_i)$ (ADA)",
        vmax=vmax_f,
    )
    draw_abs(
        axes[1], S, P, f1, z0_1,
        title=rf"$k={K1}$, $a_0={A0_1}$",
        cbar_label=r"$f(\sigma_i,p_i)$ (ADA)",
        vmax=vmax_f,
    )
    draw_pct(
        axes[2], S, P, pct_f, z0_1,
        title=r"% difference: final minus initial",
    )
    fig.suptitle(
        r"Gross pool reward $f$: $(k,a_0)=(500,0.3)\to(1000,0.6)$"
        "\n"
        + rf"$R={R/1e6:.1f}$M, $T={T/1e9:.1f}$B",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_F, dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    draw_abs(
        axes[0], S, P, pi0, z0_0,
        title=rf"$k={K0}$, $a_0={A0_0}$",
        cbar_label=r"$\Pi_i$ (ADA)",
        vmax=vmax_pi,
    )
    draw_abs(
        axes[1], S, P, pi1, z0_1,
        title=rf"$k={K1}$, $a_0={A0_1}$",
        cbar_label=r"$\Pi_i$ (ADA)",
        vmax=vmax_pi,
    )
    draw_pct(
        axes[2], S, P, pct_pi, z0_1,
        title=r"% difference: final minus initial",
    )
    fig.suptitle(
        r"Operator reward $\Pi$: $(k,a_0)=(500,0.3)\to(1000,0.6)$"
        "\n"
        + rf"$R={R/1e6:.1f}$M, $T={T/1e9:.1f}$B, $c={C:.0f}$, $m={100*M:.0f}\%$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PI, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {OUT_F}")
    print(f"Saved: {OUT_PI}")


if __name__ == "__main__":
    main()
