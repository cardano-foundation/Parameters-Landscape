#!/usr/bin/env python3
"""
Stake / delegation distribution at epoch 644 in 5M-ADA bins.

Bins: [0,5), [5,10), ..., [75,80), and ≥80 M ADA.
Uses epoch stake (epochs.0.data.epoch_stake), falling back to active_stake.
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
OUT_PLOT = DIR / "stake_distribution_by_bin_epoch_644.png"
OUT_CSV = DIR / "stake_distribution_by_bin_epoch_644.csv"

FONT_SIZE = 12
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
COLOR = "#4c78a8"


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    stake_ada = (
        pd.to_numeric(
            df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
            errors="coerce",
        ).fillna(0.0)
        / 1e6
    )
    stake_m = stake_ada / 1e6  # M ADA
    active = stake_m > 0
    stake_m = stake_m[active]

    edges = np.arange(0.0, BIN_MAX_M + BIN_WIDTH_M, BIN_WIDTH_M)
    labels = [f"{int(lo)}–{int(hi)}" for lo, hi in zip(edges[:-1], edges[1:])]
    labels.append(f"≥{int(BIN_MAX_M)}")

    # Assign bin index: 0..(n-2) for finite bins, n-1 for ≥80
    idx = np.digitize(stake_m.to_numpy(), edges, right=False) - 1
    idx = np.clip(idx, 0, len(labels) - 1)
    # digitize puts values == 80 in the last finite bin edge case: treat ≥80 as last
    idx = np.where(stake_m.to_numpy() >= BIN_MAX_M, len(labels) - 1, idx)

    n_bins = len(labels)
    counts = np.bincount(idx, minlength=n_bins)
    stake_sum_m = np.bincount(idx, weights=stake_m.to_numpy(), minlength=n_bins)

    rows = []
    for i, lab in enumerate(labels):
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": int(counts[i]),
                "share_of_pools_pct": 100.0 * counts[i] / len(stake_m),
                "agg_stake_M_ADA": float(stake_sum_m[i]),
                "share_of_stake_pct": 100.0 * stake_sum_m[i] / float(stake_m.sum()),
            }
        )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.2), constrained_layout=True, sharex=True)

    x = np.arange(n_bins)
    # Top: pool counts
    ax = axes[0]
    bars = ax.bar(x, counts, color=COLOR, edgecolor="0.2", width=0.85)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title("Pools per stake bin", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE - 1)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(counts) * 1.18 if max(counts) else 1.0
    ax.set_ylim(0, ymax)
    for bar, n in zip(bars, counts):
        if n > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                n + ymax * 0.01,
                str(int(n)),
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 3,
            )

    # Bottom: aggregate stake
    ax = axes[1]
    bars = ax.bar(x, stake_sum_m, color="#2a9d8f", edgecolor="0.2", width=0.85)
    ax.set_ylabel("Aggregate stake (M ADA)", fontsize=FONT_SIZE)
    ax.set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)
    ax.set_title("Aggregate stake per bin", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE - 1)
    ax.grid(axis="y", alpha=0.25)
    ymax2 = max(stake_sum_m) * 1.18 if max(stake_sum_m) else 1.0
    ax.set_ylim(0, ymax2)
    for bar, v in zip(bars, stake_sum_m):
        if v > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + ymax2 * 0.01,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 3,
            )

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=FONT_SIZE - 2, rotation=45, ha="right")

    fig.suptitle(
        f"Epoch 644 — stake / delegation distribution by bin\n"
        f"(pools with $\\sigma_i>0$: $n={len(stake_m)}$; "
        f"total stake ${stake_m.sum()/1e3:.2f}$B ADA; bins of ${BIN_WIDTH_M:.0f}$M ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"n_active={len(stake_m)}, total_stake_B={stake_m.sum()/1e3:.3f}")
    for r in rows:
        print(
            f"  {r['stake_bin_M_ADA']}: n={r['n_pools']} "
            f"({r['share_of_pools_pct']:.1f}%), "
            f"stake={r['agg_stake_M_ADA']:.1f}M "
            f"({r['share_of_stake_pct']:.1f}%)"
        )


if __name__ == "__main__":
    main()
