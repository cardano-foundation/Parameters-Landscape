#!/usr/bin/env python3
"""
Histogram of declared pool fixed cost (epoch 644).

Column: pool_update.active.fixed_cost (lovelace)
  = each pool's declared fixed cost (must be >= protocol parameter minPoolCost).
  Not the protocol floor itself; that is minPoolCost on-chain.

Usage:
  python3 plot_min_pool_cost_hist_epoch_644.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
OUT_PLOT = DIR / "min_pool_cost_hist_epoch_644.png"
COL = "pool_update.active.fixed_cost"

FOCUS_MAX_ADA = 1000.0
FONT_SIZE = 12  # match other Cardano-Parameters-Landscape plots
HIGHLIGHT = {
    170.0: "#2a9d8f",  # teal
    340.0: "#e76f51",  # coral
}
DEFAULT_COLOR = "#4c78a8"


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    cost_lov = pd.to_numeric(df[COL], errors="coerce").dropna()
    cost_ada = (cost_lov / 1e6).to_numpy(dtype=float)
    n = len(cost_ada)
    focus = cost_ada[cost_ada <= FOCUS_MAX_ADA]
    n_focus = len(focus)
    n_tail = n - n_focus

    print(f"pools with fixed_cost: {n}")
    print(f"min / median / mean / max (ADA): "
          f"{cost_ada.min():.0f} / {np.median(cost_ada):.0f} / "
          f"{cost_ada.mean():.1f} / {cost_ada.max():.0f}")
    print(f"<= {FOCUS_MAX_ADA:.0f} ADA: {n_focus}; > {FOCUS_MAX_ADA:.0f} ADA: {n_tail}")
    vc = pd.Series(cost_ada).value_counts().sort_index()
    print("top declared values (ADA -> count):")
    for v, c in vc.nlargest(10).items():
        print(f"  {v:g}: {c}")

    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    bins = np.arange(0, FOCUS_MAX_ADA + 25, 25)
    counts, edges, patches = ax.hist(
        focus, bins=bins, color=DEFAULT_COLOR, edgecolor="white", linewidth=0.4
    )

    for patch, left, right, count in zip(patches, edges[:-1], edges[1:], counts):
        for value, color in HIGHLIGHT.items():
            if left <= value < right:
                patch.set_facecolor(color)
                # Label the bar with the exact value and pool count at that value
                n_exact = int((focus == value).sum())
                ax.annotate(
                    f"{value:g}\n(n={n_exact})",
                    xy=((left + right) / 2, count),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="semibold",
                    color=color,
                )
                break

    ax.set_xticks([0, 170, 340, 500, 750, 1000])
    ax.set_xlabel("Declared fixed cost (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — declared pool fixed cost (≤ 1,000 ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.text(
        0.98,
        0.95,
        f"{n_tail} pools with fixed cost above 1,000 ADA\n"
        f"(of {n} pools; column: {COL})",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        color="0.3",
    )
    # Headroom for annotations above the tallest bar
    ax.set_ylim(0, max(counts) * 1.18)

    fig.savefig(OUT_PLOT, dpi=160)
    print(f"wrote {OUT_PLOT}")


if __name__ == "__main__":
    main()
