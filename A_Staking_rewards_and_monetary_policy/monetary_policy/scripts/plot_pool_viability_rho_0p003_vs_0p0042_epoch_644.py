#!/usr/bin/env python3
"""Epoch 644 — pool viability bar chart: rho=0.003 vs rho=0.0042."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rho_comparison_common import (
    CATEGORY_LABELS, CATEGORY_ORDER, C_STAR_ADA, FONT_SIZE,
    RHO_BASE, RHO_NEW, load_and_compute,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_viability_rho_0p003_vs_0p0042_epoch_644.png"


def main():
    d = load_and_compute()
    pledge_met = d["pledge_met"]
    ratio_base, ratio_new = d["ratio_base"], d["ratio_new"]
    cat_base, cat_new = d["cat_base"], d["cat_new"]
    R_base, R_new = d["R_base"], d["R_new"]

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
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
