#!/usr/bin/env python3
"""Epoch 644: traits of pools improving viability under rho increase.

Groups:
1) Pools that move to a better viability category when rho goes 0.003 -> 0.0042.
2) Pools that cross from losing (r<1) to viable (r>=1).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rho_comparison_common import (
    CATEGORY_ORDER,
    FONT_SIZE,
    RHO_BASE,
    RHO_NEW,
    load_and_compute,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_viability_improvers_traits_rho_epoch_644.png"


def main() -> None:
    d = load_and_compute()
    pledge_met = d["pledge_met"]

    sigma = d["sigma_a"]
    declared = d["declared_a"]
    active = d["active_a"]
    margin = d["margin_a"]
    fixed_cost = d["cost_a"]
    ratio_base = d["ratio_base"]
    ratio_new = d["ratio_new"]
    cat_base = d["cat_base"]
    cat_new = d["cat_new"]

    # Category improvement: moved to a higher viability bin.
    cat_to_idx = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    idx_base = np.array([cat_to_idx.get(c, -1) for c in cat_base])
    idx_new = np.array([cat_to_idx.get(c, -1) for c in cat_new])

    improved_category = pledge_met & (idx_base >= 0) & (idx_new > idx_base)
    crossed_losing_to_viable = pledge_met & (ratio_base < 1.0) & (ratio_new >= 1.0)
    other_pledge_met = pledge_met & (~improved_category)

    groups = [
        ("Improved\ncategory", improved_category, "#2a9d8f"),
        ("Losing\n→ viable", crossed_losing_to_viable, "#e76f51"),
        ("Other\npools", other_pledge_met, "#4c78a8"),
    ]

    traits = [
        (sigma, "Epoch stake (M ADA)", "Epoch stake", 1e6),
        (declared, "Declared pledge (k ADA)", "Declared pledge", 1e3),
        (active, "Active pledge (k ADA)", "Active pledge", 1e3),
        (margin, "Margin (%)", "Margin", "pct"),
        (fixed_cost, "Fixed cost (ADA)", "Fixed cost", 1.0),
        (ratio_base, r"Initial coverage ratio $r=\Pi_i/C^*$", "Initial viability", 1.0),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), constrained_layout=True)
    axes_flat = axes.flatten()
    median_color = "#111111"

    for ax, (arr, ylabel, title, scale) in zip(axes_flat, traits):
        if scale == "pct":
            values = [arr[m] * 100.0 for _, m, _ in groups]
        elif scale != 1.0:
            values = [arr[m] / scale for _, m, _ in groups]
        else:
            values = [arr[m] for _, m, _ in groups]

        labels = [f"{name}\n(n={int(mask.sum())})" for name, mask, _ in groups]
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
                i + 1,
                med_val,
                f" {med_val:.2f}",
                va="bottom",
                ha="center",
                fontsize=FONT_SIZE - 2,
                color=median_color,
            )
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)

    fig.suptitle(
        rf"Epoch 644 — traits of pools improving viability ($\rho$: {RHO_BASE} → {RHO_NEW})",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)

    print(f"Improved category pools: {int(improved_category.sum())}")
    print(f"Crossed losing->viable pools: {int(crossed_losing_to_viable.sum())}")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
