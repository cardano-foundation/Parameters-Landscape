#!/usr/bin/env python3
"""Epoch 644 — boxplots of traits for pools gaining/losing desirability rank (rho change)."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rho_comparison_common import FONT_SIZE, RHO_BASE, RHO_NEW, load_and_compute

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_desirability_rank_traits_rho_epoch_644.png"


def main():
    d = load_and_compute()
    pledge_met = d["pledge_met"]
    d_base, d_new = d["d_base"], d["d_new"]
    sigma_a = d["sigma_a"]
    declared_a = d["declared_a"]
    active_a = d["active_a"]
    margin_a = d["margin_a"]
    cost_a = d["cost_a"]

    mask = pledge_met & ((d_base > 0) | (d_new > 0))
    d_b = d_base[mask]
    d_n = d_new[mask]
    rank_base = np.argsort(np.argsort(-d_b)) + 1
    rank_new = np.argsort(np.argsort(-d_n)) + 1
    rank_diff = rank_new.astype(int) - rank_base.astype(int)

    threshold = 5
    gainer_mask = rank_diff <= -threshold
    loser_mask = rank_diff >= threshold
    stable_mask = np.abs(rank_diff) < threshold

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
        (sigma_sub, "Epoch stake (M ADA)", "Epoch stake", 1e6),
        (declared_sub, "Declared pledge (k ADA)", "Declared pledge", 1e3),
        (active_sub, "Active pledge (k ADA)", "Active pledge", 1e3),
        (margin_sub, "Margin (%)", "Margin", "margin"),
        (cost_sub, "Fixed cost (ADA)", "Fixed cost", 1.0),
        (d_base_sub, r"Initial desirability $D_i$ ($\rho=0.003$)", "Desirability", 1.0),
    ]

    median_color = "#111111"
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), constrained_layout=True)
    axes_flat = axes.flatten()

    for idx, (data_arr, ylabel, title, divisor) in enumerate(traits):
        ax = axes_flat[idx]
        if divisor == "margin":
            values = [data_arr[m] * 100.0 for _, m, _ in groups]
        elif divisor != 1.0:
            values = [data_arr[m] / divisor for _, m, _ in groups]
        else:
            values = [data_arr[m] for _, m, _ in groups]

        labels = [f"{name}\n(n={int(m.sum())})" for name, m, _ in groups]
        box = ax.boxplot(
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
        for i, line in enumerate(box["medians"]):
            med_val = line.get_ydata()[0]
            ax.text(
                i + 1, med_val, f" {med_val:.1f}",
                va="bottom", ha="center", fontsize=FONT_SIZE - 2, color=median_color,
            )
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)

    fig.suptitle(
        rf"Epoch 644 — traits of pools gaining vs losing desirability rank ($\rho$: {RHO_BASE} → {RHO_NEW})",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)
    print(f"Gainers: {gainer_mask.sum()}, Stable: {stable_mask.sum()}, Losers: {loser_mask.sum()}")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
