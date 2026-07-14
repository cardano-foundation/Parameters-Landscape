#!/usr/bin/env python3
"""
Cardano reward comparative-static heatmaps (current design).

Same reward objects as the vs-pledge line-plot companion:
  1) Gross pool reward f(sigma, p; z0)
  2) Operator reward Pi(sigma, p; z0, c, m)
  3) Delegator reward per unit of stake

Heatmaps over (sigma, p) with shared axes:
  sigma in (0, z0 + epsilon]  (baseline z0 = T/k with k=500, ~77M)
  pledge in [0, sigma_max]
Feasibility: p <= sigma (gray otherwise). Case-specific saturation
(z0 or z0_alt) enters only in the reward formula.

Line plots live in the sibling folder Rewards_Static-Comparison_vs_pledge.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import ScalarFormatter

# Shared color semantics across all heatmaps:
#   - Absolute plots (rewards >= 0): yellow = low, green = mid/high, blue = very high.
#     Red/orange is NOT used, so small positive values are never shown as red.
#   - Difference plots: red/orange = negative, yellow = zero, green = positive,
#     blue = very positive. Same yellow/green/blue meaning as absolute plots.
HEATMAP_CMAP_ABS = LinearSegmentedColormap.from_list(
    "yellow_green_blue",
    ["#ffffbf", "#d9ef8b", "#66bd63", "#1a9850", "#2166ac"],
)
HEATMAP_CMAP_DIFF = LinearSegmentedColormap.from_list(
    "red_yellow_green_blue",
    ["#d73027", "#fc8d59", "#ffffbf", "#1a9850", "#2166ac"],
)


# =============================================================================
# PARAMETERS (edit here)
# =============================================================================
# R : epoch reward pot (ADA)
R = 15.6e6

# T : total ADA supply
T = 38.5e9

# k : desired number of pools (baseline)
k = 500

# Alternative desired number of pools for comparison plots
k_alt = 1000

# a0 : pledge influence parameter
a0 = 0.3

# c_i : pool fixed cost (ADA), baseline
c_i = 170.0

# Additional fixed cost scenario for comparison plots
c_i_alt = 340.0

# m_i : operator margin / commission in [0, 1)
m_i = 0.05

# Heatmap resolution and extension beyond saturation
N_HEATMAP = 280
# epsilon : small extension so x-axis includes a neighborhood above z0
Z0_EPSILON_FRAC = 0.05

# Derived saturation points: z0 = T / k
z0 = T / k
z0_alt = T / k_alt

# Scale factor used when sigma, p, z0 are expressed in ADA
r_over_t = R / T

OUT_DIR = Path(__file__).resolve().parent
FONT_SIZE = 12


# =============================================================================
# REWARD GRIDS
# =============================================================================
# Gross:
#   sigma_tilde = min(sigma, z0)
#   p_tilde     = min(p, z0)
#   f = (R/(1+a0)) * [
#         sigma_tilde
#         + a0 * p_tilde * (sigma_tilde - p_tilde * (z0 - sigma_tilde)/z0) / z0
#       ]
#
# Operator:
#   Pi = c + (f - c) * [ m + (1-m) * p/sigma ]   if f > c
#      = f                                       otherwise
#
# Delegator per unit:
#   r_del = (1 - m) * max(f - c, 0) / sigma
# =============================================================================
def _sigma_p_grids() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Common (sigma, p) grid up to baseline z0 + epsilon (~77M)."""
    sigma_max = z0 * (1.0 + Z0_EPSILON_FRAC)
    sigma_1d = np.linspace(1.0, sigma_max, N_HEATMAP)
    p_1d = np.linspace(0.0, sigma_max, N_HEATMAP)
    S, P = np.meshgrid(sigma_1d, p_1d)
    return sigma_1d, p_1d, S, P


def _gross_grid(S: np.ndarray, P: np.ndarray, z0_ada: float, r_scale: float, a0_value: float) -> np.ndarray:
    sigma_tilde = np.minimum(S, z0_ada)
    p_tilde = np.minimum(P, z0_ada)
    inner = sigma_tilde - p_tilde * (z0_ada - sigma_tilde) / z0_ada
    return (r_scale / (1.0 + a0_value)) * (
        sigma_tilde + a0_value * p_tilde * inner / z0_ada
    )


def _operator_grid(
    S: np.ndarray,
    P: np.ndarray,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = _gross_grid(S, P, z0_ada, r_scale, a0_value)
    share = m + (1.0 - m) * (P / S)
    reward_if_profitable = c + (f_val - c) * share
    return np.where(f_val > c, reward_if_profitable, f_val)


def _delegator_grid(
    S: np.ndarray,
    P: np.ndarray,
    z0_ada: float,
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
) -> np.ndarray:
    f_val = _gross_grid(S, P, z0_ada, r_scale, a0_value)
    return np.where(f_val > c, (1.0 - m) * (f_val - c) / S, 0.0)


def _finite_max(values: np.ndarray, S: np.ndarray, P: np.ndarray) -> float:
    masked = np.ma.masked_where(P > S, values)
    finite_vals = masked.compressed()
    if finite_vals.size == 0:
        return 1.0
    return float(np.nanmax(np.abs(finite_vals)))


def _draw_heatmap_panel(
    ax,
    S: np.ndarray,
    P: np.ndarray,
    values: np.ndarray,
    z0_case: float,
    title: str,
    cbar_label: str,
    scientific_y: bool = False,
    diverging: bool = False,
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    infeasible = P > S
    masked = np.ma.masked_where(infeasible, values)

    if diverging:
        cmap = HEATMAP_CMAP_DIFF.copy()
        cmap.set_bad(color="lightgray")
        if vmin is None or vmax is None:
            v_lim = _finite_max(values, S, P)
            v_lim = max(v_lim, 1e-12)
            vmin, vmax = -v_lim, v_lim
        im = ax.pcolormesh(
            S, P, masked, shading="auto", cmap=cmap, vmin=vmin, vmax=vmax
        )
    else:
        # Absolute rewards: yellow at 0, green mid-range, blue at max. No red.
        cmap = HEATMAP_CMAP_ABS.copy()
        cmap.set_bad(color="lightgray")
        if vmin is None:
            vmin = 0.0
        if vmax is None:
            finite_vals = masked.compressed()
            vmax = float(np.nanmax(finite_vals)) if finite_vals.size else 1.0
            vmax = max(vmax, 1e-12)
        im = ax.pcolormesh(
            S, P, masked, shading="auto", cmap=cmap, vmin=vmin, vmax=vmax
        )

    ax.plot([0.0, float(S.max())], [0.0, float(S.max())], "k--", linewidth=1.2, alpha=0.85)
    ax.axvline(z0_case, color="0.3", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.text(
        0.98 * float(S.max()),
        0.98 * float(S.max()),
        "p=sigma (feasibility limit)",
        fontsize=FONT_SIZE - 1,
        ha="right",
        va="top",
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
    if scientific_y:
        cbar.formatter = ScalarFormatter(useMathText=True)
        cbar.formatter.set_powerlimits((-4, -4))
        cbar.update_ticks()


# =============================================================================
# HEATMAP 1: Gross pool reward — k comparison (+ difference)
# =============================================================================
def heatmap_gross_k_cases(r_scale: float, a0_value: float, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    _, _, S, P = _sigma_p_grids()
    vals_500 = _gross_grid(S, P, z0, r_scale, a0_value)
    vals_1000 = _gross_grid(S, P, z0_alt, r_scale, a0_value)
    vals_diff = vals_1000 - vals_500
    vmax = max(_finite_max(vals_500, S, P), _finite_max(vals_1000, S, P))

    _draw_heatmap_panel(
        axes[0],
        S,
        P,
        vals_500,
        z0,
        title=rf"$k={k}$, $z_0={z0/1e6:.1f}$M",
        cbar_label=r"$f(\sigma_i,p_i;z_0)$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[1],
        S,
        P,
        vals_1000,
        z0_alt,
        title=rf"$k={k_alt}$, $z_0={z0_alt/1e6:.1f}$M",
        cbar_label=r"$f(\sigma_i,p_i;z_0)$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[2],
        S,
        P,
        vals_diff,
        z0_alt,
        title=rf"Difference: $k={k_alt}$ minus $k={k}$",
        cbar_label=r"$\Delta f$ (ADA)",
        diverging=True,
    )
    fig.suptitle(
        rf"Gross pool rewards $f(\cdot)$ when $k$ changes"
        "\n"
        rf"$a_0={a0_value}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output_path)


# =============================================================================
# HEATMAP 2: Operator reward — k comparison (+ difference)
# =============================================================================
def heatmap_operator_k_cases(
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    _, _, S, P = _sigma_p_grids()
    vals_500 = _operator_grid(S, P, z0, r_scale, a0_value, c, m)
    vals_1000 = _operator_grid(S, P, z0_alt, r_scale, a0_value, c, m)
    vals_diff = vals_1000 - vals_500
    vmax = max(_finite_max(vals_500, S, P), _finite_max(vals_1000, S, P))

    _draw_heatmap_panel(
        axes[0],
        S,
        P,
        vals_500,
        z0,
        title=rf"$k={k}$, $z_0={z0/1e6:.1f}$M",
        cbar_label=r"Operator reward $\Pi_i$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[1],
        S,
        P,
        vals_1000,
        z0_alt,
        title=rf"$k={k_alt}$, $z_0={z0_alt/1e6:.1f}$M",
        cbar_label=r"Operator reward $\Pi_i$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[2],
        S,
        P,
        vals_diff,
        z0_alt,
        title=rf"Difference: $k={k_alt}$ minus $k={k}$",
        cbar_label=r"$\Delta\Pi_i$ (ADA)",
        diverging=True,
    )
    fig.suptitle(
        "Operator rewards when $k$ changes\n"
        rf"$a_0={a0_value}$, $c={c:.0f}$, $m={100*m:.0f}\%$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output_path)


# =============================================================================
# HEATMAP 3: Operator reward — c comparison (+ difference)
# =============================================================================
def heatmap_operator_c_cases(
    r_scale: float,
    a0_value: float,
    c: float,
    c_alt: float,
    m: float,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    _, _, S, P = _sigma_p_grids()
    vals_c = _operator_grid(S, P, z0, r_scale, a0_value, c, m)
    vals_c_alt = _operator_grid(S, P, z0, r_scale, a0_value, c_alt, m)
    vals_diff = vals_c_alt - vals_c
    vmax = max(_finite_max(vals_c, S, P), _finite_max(vals_c_alt, S, P))

    _draw_heatmap_panel(
        axes[0],
        S,
        P,
        vals_c,
        z0,
        title=rf"$c={c:.0f}$",
        cbar_label=r"Operator reward $\Pi_i$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[1],
        S,
        P,
        vals_c_alt,
        z0,
        title=rf"$c={c_alt:.0f}$",
        cbar_label=r"Operator reward $\Pi_i$ (ADA)",
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[2],
        S,
        P,
        vals_diff,
        z0,
        title=rf"Difference: $c={c_alt:.0f}$ minus $c={c:.0f}$",
        cbar_label=r"$\Delta\Pi_i$ (ADA)",
        diverging=True,
    )
    fig.suptitle(
        "Operator rewards when reported $c$ changes\n"
        rf"$a_0={a0_value}$, $k={k}$, $m={100*m:.0f}\%$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output_path)


# =============================================================================
# HEATMAP 4: Delegator reward — k comparison (+ difference)
# =============================================================================
def heatmap_delegator_k_cases(
    r_scale: float,
    a0_value: float,
    c: float,
    m: float,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)

    # Common axes: baseline z0 + epsilon (~77M) for all panels.
    # Case-specific saturation enters only in the reward formula.
    _, _, S, P = _sigma_p_grids()
    vals_500 = _delegator_grid(S, P, z0, r_scale, a0_value, c, m)
    vals_1000 = _delegator_grid(S, P, z0_alt, r_scale, a0_value, c, m)
    vals_diff = vals_1000 - vals_500

    vmax = max(_finite_max(vals_500, S, P), _finite_max(vals_1000, S, P))

    _draw_heatmap_panel(
        axes[0],
        S,
        P,
        vals_500,
        z0,
        title=rf"$k={k}$, $z_0={z0/1e6:.1f}$M",
        cbar_label=r"Delegator reward / unit stake",
        scientific_y=True,
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[1],
        S,
        P,
        vals_1000,
        z0_alt,
        title=rf"$k={k_alt}$, $z_0={z0_alt/1e6:.1f}$M",
        cbar_label=r"Delegator reward / unit stake",
        scientific_y=True,
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[2],
        S,
        P,
        vals_diff,
        z0_alt,
        title=rf"Difference: $k={k_alt}$ minus $k={k}$",
        cbar_label=r"$\Delta$ reward / unit stake",
        scientific_y=True,
        diverging=True,
    )

    fig.suptitle(
        f"Delegator rewards per unit when k changes\n"
        f"$a_0={a0_value}$, $c={c:.0f}$, $m={100*m:.0f}\\%$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output_path)


# =============================================================================
# HEATMAP 5: Delegator reward — c comparison (+ difference)
# =============================================================================
def heatmap_delegator_c_cases(
    r_scale: float,
    a0_value: float,
    c: float,
    c_alt: float,
    m: float,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    _, _, S, P = _sigma_p_grids()
    vals_c = _delegator_grid(S, P, z0, r_scale, a0_value, c, m)
    vals_c_alt = _delegator_grid(S, P, z0, r_scale, a0_value, c_alt, m)
    # Difference: rewards at c_alt=340 minus rewards at c=170
    vals_diff = vals_c_alt - vals_c
    vmax = max(_finite_max(vals_c, S, P), _finite_max(vals_c_alt, S, P))

    _draw_heatmap_panel(
        axes[0],
        S,
        P,
        vals_c,
        z0,
        title=rf"$c={c:.0f}$",
        cbar_label=r"Delegator reward / unit stake",
        scientific_y=True,
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[1],
        S,
        P,
        vals_c_alt,
        z0,
        title=rf"$c={c_alt:.0f}$",
        cbar_label=r"Delegator reward / unit stake",
        scientific_y=True,
        vmin=0.0,
        vmax=vmax,
    )
    _draw_heatmap_panel(
        axes[2],
        S,
        P,
        vals_diff,
        z0,
        title=rf"Difference: $c={c_alt:.0f}$ minus $c={c:.0f}$",
        cbar_label=r"$\Delta$ reward / unit stake",
        scientific_y=True,
        diverging=True,
    )
    fig.suptitle(
        f"Delegator rewards per unit when reported c changes\n"
        f"$a_0={a0_value}$, $m={100*m:.0f}\\%$, $k={k}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", output_path)


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    print("Parameters:")
    print(f"  R={R:,.0f}, T={T:,.0f}, k={k}, z0={z0:,.0f}")
    print(f"  k_alt={k_alt}, z0_alt={z0_alt:,.0f}")
    print(f"  a0={a0}, c_i={c_i}, c_i_alt={c_i_alt}, m_i={m_i}")
    print(f"  Heatmap axes: sigma, p in (0, z0*(1+{Z0_EPSILON_FRAC}))]")

    heatmap_gross_k_cases(
        r_scale=r_over_t,
        a0_value=a0,
        output_path=OUT_DIR / "heatmap_gross_pool_reward_k_cases.png",
    )
    heatmap_operator_k_cases(
        r_scale=r_over_t,
        a0_value=a0,
        c=c_i,
        m=m_i,
        output_path=OUT_DIR / "heatmap_operator_reward_k_cases.png",
    )
    heatmap_operator_c_cases(
        r_scale=r_over_t,
        a0_value=a0,
        c=c_i,
        c_alt=c_i_alt,
        m=m_i,
        output_path=OUT_DIR / "heatmap_operator_reward_c_cases.png",
    )
    heatmap_delegator_k_cases(
        r_scale=r_over_t,
        a0_value=a0,
        c=c_i,
        m=m_i,
        output_path=OUT_DIR / "heatmap_delegator_reward_k_cases.png",
    )
    heatmap_delegator_c_cases(
        r_scale=r_over_t,
        a0_value=a0,
        c=c_i,
        c_alt=c_i_alt,
        m=m_i,
        output_path=OUT_DIR / "heatmap_delegator_reward_c_cases.png",
    )


if __name__ == "__main__":
    main()
