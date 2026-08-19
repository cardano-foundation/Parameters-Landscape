#!/usr/bin/env python3
"""
Effect of increasing rho from 0.003 to 0.0042 on pool viability (epoch 644).

Panel 1: side-by-side bar chart of viability categories before/after.
Panel 2: desirability ranking change — scatter of rank(rho=0.003) vs rank(rho=0.0042).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_VIABILITY = DIR / "pool_viability_rho_0p003_vs_0p0042_epoch_644.png"
OUT_DESIRABILITY = DIR / "pool_desirability_rho_0p003_vs_0p0042_epoch_644.png"
OUT_CSV = DIR / "pool_viability_rho_0p003_vs_0p0042_epoch_644.csv"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

RHO_BASE = 0.003
RHO_NEW = 0.0042
TAU = 0.2

CATEGORY_ORDER = (
    "losing_lt_025",
    "losing_025_050",
    "losing_050_075",
    "losing_075_100",
    "edge",
    "comfortable",
    "strong",
)
CATEGORY_LABELS = (
    r"$r<0.25$",
    r"$0.25\leq r<0.5$",
    r"$0.5\leq r<0.75$",
    r"$0.75\leq r<1$",
    "Edge\n" r"($1\leq r<2$)",
    "Comfortable\n" r"($2\leq r<5$)",
    "Strong\n" r"($r\geq5$)",
)


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    pledge_share = np.clip(
        np.divide(active_pledge, sigma, out=np.zeros_like(active_pledge), where=sigma > 0),
        0.0, 1.0,
    )
    operator_share = margin + (1.0 - margin) * pledge_share
    profitable = fixed_cost + (f - fixed_cost) * operator_share
    return np.where(f > fixed_cost, profitable, f)


def desirability(f: np.ndarray, fixed_cost: np.ndarray, margin: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Per-ADA member reward: D = (1 - m) * max(f - c, 0) / sigma."""
    return np.where(
        sigma > 0,
        (1.0 - margin) * np.maximum(f - fixed_cost, 0.0) / sigma,
        0.0,
    )


def classify(ratio: float) -> str:
    if ratio < 0.25:
        return "losing_lt_025"
    if ratio < 0.5:
        return "losing_025_050"
    if ratio < 0.75:
        return "losing_050_075"
    if ratio < 1.0:
        return "losing_075_100"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    reserves = float(params["reserves_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])

    R_base = (1 - TAU) * RHO_BASE * reserves
    R_new = (1 - TAU) * RHO_NEW * reserves

    r_over_t_base = R_base / T
    r_over_t_new = R_new / T

    # z0 = 1/k * T for saturation cap; rho change doesn't affect z0
    # (z0 depends on total supply which changes only marginally within one epoch)

    df = pd.read_csv(POOLS_CSV)
    sigma = pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    declared_pledge = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active_pledge = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    fixed_cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = sigma.notna() & declared_pledge.notna() & active_pledge.notna() & fixed_cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared_pledge[complete].to_numpy(dtype=float)
    active_a = active_pledge[complete].to_numpy(dtype=float)
    cost_a = fixed_cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)

    # Base scenario (rho=0.003)
    f_base = np.where(
        pledge_met,
        np.maximum(gross_pool_reward(sigma_a, declared_a, z0=z0, r_over_t=r_over_t_base, a0=a0), 0.0),
        0.0,
    )
    pi_base = operator_reward(f_base, cost_a, margin_a, active_a, sigma_a)
    ratio_base = pi_base / C_STAR_ADA
    cat_base = np.array([classify(v) if m else "pledge_not_met" for v, m in zip(ratio_base, pledge_met)])

    # New scenario (rho=0.0042)
    f_new = np.where(
        pledge_met,
        np.maximum(gross_pool_reward(sigma_a, declared_a, z0=z0, r_over_t=r_over_t_new, a0=a0), 0.0),
        0.0,
    )
    pi_new = operator_reward(f_new, cost_a, margin_a, active_a, sigma_a)
    ratio_new = pi_new / C_STAR_ADA
    cat_new = np.array([classify(v) if m else "pledge_not_met" for v, m in zip(ratio_new, pledge_met)])

    # Desirability
    d_base = desirability(f_base, cost_a, margin_a, sigma_a)
    d_new = desirability(f_new, cost_a, margin_a, sigma_a)

    # Save CSV
    out_df = pd.DataFrame({
        "pool_id": df.loc[complete, "pool_id"].values,
        "ticker": df.loc[complete, "pool_name.ticker"].values,
        "sigma_ada": sigma_a,
        "pledge_met": pledge_met,
        "f_base": f_base,
        "f_new": f_new,
        "pi_base": pi_base,
        "pi_new": pi_new,
        "ratio_base": ratio_base,
        "ratio_new": ratio_new,
        "category_base": cat_base,
        "category_new": cat_new,
        "desirability_base": d_base,
        "desirability_new": d_new,
    })
    out_df.to_csv(OUT_CSV, index=False)

    # ---- Plot 1: Viability bar chart ----
    counts_base = pd.Series(cat_base[pledge_met]).value_counts()
    counts_new = pd.Series(cat_new[pledge_met]).value_counts()
    h_base = [int(counts_base.get(c, 0)) for c in CATEGORY_ORDER]
    h_new = [int(counts_new.get(c, 0)) for c in CATEGORY_ORDER]

    fig, ax = plt.subplots(figsize=(12, 5.5), constrained_layout=True)
    x = np.arange(len(CATEGORY_ORDER))
    w = 0.35
    bars1 = ax.bar(x - w / 2, h_base, w, color="#4c78a8", edgecolor="white", label=rf"$\rho={RHO_BASE}$ (current)")
    bars2 = ax.bar(x + w / 2, h_new, w, color="#2a9d8f", edgecolor="white", label=rf"$\rho={RHO_NEW}$")

    for bar_set in [bars1, bars2]:
        for bar in bar_set:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + max(max(h_base), max(h_new)) * 0.01,
                        str(int(h)), ha="center", va="bottom", fontsize=FONT_SIZE - 2)

    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORY_LABELS, fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        rf"Epoch 644 — pool viability: $\rho={RHO_BASE}$ vs $\rho={RHO_NEW}$"
        "\n"
        rf"($C^*={C_STAR_ADA:.0f}$ ADA/epoch, $r=\Pi_i/C^*$)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE)
    ax.grid(alpha=0.2, axis="y")

    n_losing_base = sum(h_base[:4])
    n_losing_new = sum(h_new[:4])
    n_viable_base = int((ratio_base[pledge_met] >= 1.0).sum())
    n_viable_new = int((ratio_new[pledge_met] >= 1.0).sum())
    ax.text(
        0.98, 0.97,
        f"Losing pools: {n_losing_base} → {n_losing_new}\n"
        f"Cover OpEx: {n_viable_base} → {n_viable_new}\n"
        f"R increases by {(R_new/R_base - 1)*100:.0f}%",
        transform=ax.transAxes, ha="right", va="top", fontsize=FONT_SIZE,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
    )
    fig.savefig(OUT_VIABILITY, dpi=160)
    plt.close(fig)

    # ---- Plot 2: Desirability ranking ----
    # Only pledge-met pools with positive desirability in at least one scenario
    mask = pledge_met & ((d_base > 0) | (d_new > 0))
    d_b = d_base[mask]
    d_n = d_new[mask]
    rank_base = np.argsort(np.argsort(-d_b)) + 1
    rank_new = np.argsort(np.argsort(-d_n)) + 1

    fig2, ax2 = plt.subplots(figsize=(7, 7), constrained_layout=True)
    ax2.scatter(rank_base, rank_new, s=8, alpha=0.4, color="#4c78a8")
    lim = max(rank_base.max(), rank_new.max()) + 10
    ax2.plot([1, lim], [1, lim], color="grey", linestyle="--", linewidth=1, alpha=0.6)
    ax2.set_xlabel(rf"Desirability rank ($\rho={RHO_BASE}$)", fontsize=FONT_SIZE)
    ax2.set_ylabel(rf"Desirability rank ($\rho={RHO_NEW}$)", fontsize=FONT_SIZE)
    ax2.set_title(
        rf"Epoch 644 — desirability ranking: $\rho={RHO_BASE}$ vs $\rho={RHO_NEW}$",
        fontsize=FONT_SIZE,
    )
    ax2.tick_params(axis="both", labelsize=FONT_SIZE)
    ax2.set_xlim(0, lim)
    ax2.set_ylim(0, lim)
    ax2.set_aspect("equal")
    ax2.grid(alpha=0.2)

    rank_corr = np.corrcoef(rank_base, rank_new)[0, 1]
    rank_changes = np.abs(rank_new.astype(int) - rank_base.astype(int))
    ax2.text(
        0.05, 0.95,
        f"Spearman rank corr: {rank_corr:.6f}\n"
        f"Max rank change: {rank_changes.max()}\n"
        f"Mean |rank change|: {rank_changes.mean():.1f}\n"
        f"Pools plotted: {mask.sum()}",
        transform=ax2.transAxes, ha="left", va="top", fontsize=FONT_SIZE,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
    )
    fig2.savefig(OUT_DESIRABILITY, dpi=160)
    plt.close(fig2)

    # ---- Plot 3: Boxplots of gainers vs losers ----
    OUT_TRAITS = DIR / "pool_desirability_rank_traits_rho_epoch_644.png"
    rank_diff = rank_new.astype(int) - rank_base.astype(int)
    # Gainers = rank decreased (negative diff), Losers = rank increased (positive diff)
    # Use a threshold to exclude negligible moves
    threshold = 5
    gainer_mask = rank_diff <= -threshold
    loser_mask = rank_diff >= threshold
    stable_mask = np.abs(rank_diff) < threshold

    # Build DataFrames for the three groups from the masked subset
    sigma_sub = sigma_a[mask]
    declared_sub = declared_a[mask]
    active_sub = active_a[mask]
    margin_sub = margin_a[mask]
    cost_sub = cost_a[mask]
    d_base_sub = d_b

    groups = [
        (f"Gainers\n(rank ↓ ≥ {threshold})", gainer_mask, "#2a9d8f"),
        (f"Stable\n(|Δrank| < {threshold})", stable_mask, "#4c78a8"),
        (f"Losers\n(rank ↑ ≥ {threshold})", loser_mask, "#dc2626"),
    ]

    traits = [
        ("sigma_sub", "Epoch stake (M ADA)", "Epoch stake", 1e6),
        ("declared_sub", "Declared pledge (k ADA)", "Declared pledge", 1e3),
        ("active_sub", "Active pledge (k ADA)", "Active pledge", 1e3),
        ("margin_sub", "Margin (%)", "Margin", 0.01),
        ("cost_sub", "Fixed cost (ADA)", "Fixed cost", 1.0),
        ("d_base_sub", r"Initial desirability $D_i$ ($\rho=0.003$)", "Desirability", 1.0),
    ]

    fig3, axes3 = plt.subplots(2, 3, figsize=(14, 8.5), constrained_layout=True)
    axes_flat = axes3.flatten()
    median_color = "#111111"

    for idx, (var_name, ylabel, title, divisor) in enumerate(traits):
        ax3 = axes_flat[idx]
        data_arr = locals()[var_name]
        if var_name == "margin_sub":
            values = [data_arr[m] * 100.0 for _, m, _ in groups]
        elif divisor != 1.0:
            values = [data_arr[m] / divisor for _, m, _ in groups]
        else:
            values = [data_arr[m] for _, m, _ in groups]

        labels = [f"{name}\n(n={int(m.sum())})" for name, m, _ in groups]
        box = ax3.boxplot(
            values,
            tick_labels=labels,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": median_color, "linewidth": 2.0},
        )
        for patch, (_, _, color) in zip(box["boxes"], groups):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        # Annotate medians
        for i, line in enumerate(box["medians"]):
            med_val = line.get_ydata()[0]
            ax3.text(
                i + 1, med_val, f" {med_val:.1f}",
                va="bottom", ha="center", fontsize=FONT_SIZE - 2, color=median_color,
            )
        ax3.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax3.set_title(title, fontsize=FONT_SIZE)
        ax3.tick_params(axis="both", labelsize=FONT_SIZE)

    fig3.suptitle(
        rf"Epoch 644 — traits of pools gaining vs losing desirability rank ($\rho$: {RHO_BASE} → {RHO_NEW})",
        fontsize=FONT_SIZE,
    )
    fig3.savefig(OUT_TRAITS, dpi=160)
    plt.close(fig3)

    print(f"R_base = {R_base:,.0f} ADA,  R_new = {R_new:,.0f} ADA  (+{(R_new/R_base-1)*100:.0f}%)")
    print(f"Losing pools: {n_losing_base} -> {n_losing_new}")
    print(f"Cover OpEx:   {n_viable_base} -> {n_viable_new}")
    print(f"Rank correlation: {rank_corr:.6f}")
    print(f"Mean |rank change|: {rank_changes.mean():.1f}")
    print(f"Gainers (rank ↓≥{threshold}): {gainer_mask.sum()}, Losers (rank ↑≥{threshold}): {loser_mask.sum()}")
    print(f"Saved: {OUT_VIABILITY}")
    print(f"Saved: {OUT_DESIRABILITY}")
    print(f"Saved: {OUT_TRAITS}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
