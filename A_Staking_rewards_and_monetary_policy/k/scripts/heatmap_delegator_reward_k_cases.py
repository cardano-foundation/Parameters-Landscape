#!/usr/bin/env python3
"""Delegator reward per unit heatmaps: k=500 vs k=1000 (+ difference)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import ScalarFormatter

HEATMAP_CMAP_ABS = LinearSegmentedColormap.from_list(
    "yellow_green_blue",
    ["#ffffbf", "#d9ef8b", "#66bd63", "#1a9850", "#2166ac"],
)
HEATMAP_CMAP_DIFF = LinearSegmentedColormap.from_list(
    "red_yellow_green_blue",
    ["#d73027", "#fc8d59", "#ffffbf", "#1a9850", "#2166ac"],
)

R = 14.9e6
T = 38.8e9
a0 = 0.3
k = 500
k_alt = 1000
c_i = 170.0
m_i = 0.05
N_HEATMAP = 280
Z0_EPSILON_FRAC = 0.05

z0 = T / k
z0_alt = T / k_alt
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12
OUTPUT_PATH = OUT_DIR / "heatmap_delegator_reward_k_cases.png"


def sigma_p_grids() -> tuple[np.ndarray, np.ndarray]:
    sigma_max = z0 * (1.0 + Z0_EPSILON_FRAC)
    sigma_1d = np.linspace(1.0, sigma_max, N_HEATMAP)
    p_1d = np.linspace(0.0, sigma_max, N_HEATMAP)
    return np.meshgrid(sigma_1d, p_1d)


def gross_grid(
    S: np.ndarray, P: np.ndarray, z0_ada: float, r_scale: float, a0_value: float
) -> np.ndarray:
    sigma_tilde = np.minimum(S, z0_ada)
    p_tilde = np.minimum(P, z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return (r_scale / (1.0 + a0_value)) * (
        sigma_tilde + a0_value * p_tilde * inner / z0_ada
    )


def delegator_grid(
    S: np.ndarray,
    P: np.ndarray,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = gross_grid(S, P, z0_ada, r_scale, a0_value)
    return np.where(f_val > c, (1.0 - m) * (f_val - c) / S, 0.0)


def finite_max(values: np.ndarray, S: np.ndarray, P: np.ndarray) -> float:
    masked = np.ma.masked_where(P > S, values)
    finite_vals = masked.compressed()
    if finite_vals.size == 0:
        return 1.0
    return float(np.nanmax(np.abs(finite_vals)))


def draw_panel(
    ax,
    S: np.ndarray,
    P: np.ndarray,
    values: np.ndarray,
    z0_case: float,
    title: str,
    cbar_label: str,
    *,
    diverging: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    masked = np.ma.masked_where(P > S, values)
    if diverging:
        cmap = HEATMAP_CMAP_DIFF.copy()
        cmap.set_bad(color="lightgray")
        if vmin is None or vmax is None:
            v_lim = max(finite_max(values, S, P), 1e-12)
            vmin, vmax = -v_lim, v_lim
    else:
        cmap = HEATMAP_CMAP_ABS.copy()
        cmap.set_bad(color="lightgray")
        if vmin is None:
            vmin = 0.0
        if vmax is None:
            finite_vals = masked.compressed()
            vmax = float(np.nanmax(finite_vals)) if finite_vals.size else 1.0
            vmax = max(vmax, 1e-12)
    im = ax.pcolormesh(S, P, masked, shading="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.plot([0.0, float(S.max())], [0.0, float(S.max())], "k--", linewidth=1.2, alpha=0.85)
    ax.axvline(z0_case, color="0.3", linestyle=":", linewidth=1.2, alpha=0.9)
    s_max = float(S.max())
    ax.text(
        s_max / 3.0,
        2.0 * s_max / 3.0,
        r"$p_i>\sigma_i$" "\n(infeasible region)",
        fontsize=FONT_SIZE - 1,
        ha="center",
        va="center",
    )
    ax.set_xlim(0.0, float(S.max()))
    ax.set_ylim(0.0, float(S.max()))
    ax.set_xlabel(r"$\sigma_i$ (ADA) [total stake]", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$p_i$ (ADA)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(6, 6))
    ax.ticklabel_format(axis="y", style="sci", scilimits=(6, 6))
    ax.set_title(title, fontsize=FONT_SIZE)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label, fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE)
    if diverging and vmin is not None and vmax is not None:
        ticks = np.linspace(vmin, vmax, 5)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f"{int(t)}%" for t in ticks])
    elif not diverging:
        cbar.formatter = ScalarFormatter(useMathText=True)
        cbar.formatter.set_powerlimits((-4, -4))
        cbar.update_ticks()


def pct_diff(new: np.ndarray, base: np.ndarray) -> np.ndarray:
    out = np.full_like(base, np.nan, dtype=float)
    ok = np.abs(base) > 1e-12
    out[ok] = 100.0 * (new[ok] - base[ok]) / base[ok]
    return out


def main() -> None:
    S, P = sigma_p_grids()
    vals_500 = delegator_grid(S, P, z0, r_over_t, a0, c_i, m_i)
    vals_1000 = delegator_grid(S, P, z0_alt, r_over_t, a0, c_i, m_i)
    vals_pct = pct_diff(vals_1000, vals_500)
    vmax = max(finite_max(vals_500, S, P), finite_max(vals_1000, S, P))

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    draw_panel(
        axes[0], S, P, vals_500, z0,
        title=rf"$k={k}$, $z_0={z0/1e6:.1f}$M",
        cbar_label=r"Delegator reward / unit stake",
        vmin=0.0, vmax=vmax,
    )
    draw_panel(
        axes[1], S, P, vals_1000, z0_alt,
        title=rf"$k={k_alt}$, $z_0={z0_alt/1e6:.1f}$M",
        cbar_label=r"Delegator reward / unit stake",
        vmin=0.0, vmax=vmax,
    )
    draw_panel(
        axes[2], S, P, vals_pct, z0_alt,
        title=rf"Percentage difference: $k={k_alt}$ vs $k={k}$",
        cbar_label=r"Percentage difference (%)",
        diverging=True,
        vmin=-50.0,
        vmax=50.0,
    )
    fig.suptitle(
        f"Delegator rewards per unit when k changes\n"
        f"$a_0={a0}$, $c={c_i:.0f}$, $m={100*m_i:.0f}\\%$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
