#!/usr/bin/env python3
"""
Stake / delegation distribution at epoch 644 in 5M-ADA bins, among Active pools.

Active = not in the union of:
  - σ_i = 0 or missing
  - unmet pledge (live_pledge < declared pledge)
  - zero blocks in epochs 630–644 (15-epoch window)

A leftmost Inactive bin (orange) shows the complementary union on both panels.
Uses the Koios snapshot (staking_pools_koios_epoch_644.csv).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_koios_epoch_644.csv"
FLAGS_CSV = DIR / "inactive_pool_flags_koios_epoch_644_last15.csv"
OUT_PLOT = DIR / "stake_distribution_by_bin_excl_inactive_pools_epoch644.png"
OUT_CSV = DIR / "stake_distribution_by_bin_excl_inactive_pools_epoch644.csv"

FONT_SIZE = 12
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
COLOR_ACTIVE_N = "#4c78a8"
COLOR_ACTIVE_STAKE = "#2a9d8f"
COLOR_INACTIVE = "#e07a3d"


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")

    stake_lov = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
        errors="coerce",
    )
    stake_m_all = stake_lov.fillna(0.0) / 1e6 / 1e6  # M ADA

    inactive = df["in_union"] == 1
    active = ~inactive
    n_inactive = int(inactive.sum())
    n_active = int(active.sum())
    stake_inactive_m = float(stake_m_all.loc[inactive].sum())
    stake_active_m = float(stake_m_all.loc[active].sum())

    stake_m = stake_m_all.loc[active]

    edges = np.arange(0.0, BIN_MAX_M + BIN_WIDTH_M, BIN_WIDTH_M)
    labels = ["Inactive"]
    labels.extend(f"{int(lo)}–{int(hi)}" for lo, hi in zip(edges[:-1], edges[1:]))
    labels.append(f"≥{int(BIN_MAX_M)}")

    idx = np.digitize(stake_m.to_numpy(), edges, right=False) - 1
    idx = np.clip(idx, 0, len(edges) - 1)
    idx = np.where(stake_m.to_numpy() >= BIN_MAX_M, len(edges) - 1, idx)

    n_active_bins = len(edges)
    counts_active = np.bincount(idx, minlength=n_active_bins)
    stake_active_bins = np.bincount(
        idx, weights=stake_m.to_numpy(), minlength=n_active_bins
    )

    counts = np.concatenate([[n_inactive], counts_active])
    stake_sum_m = np.concatenate([[stake_inactive_m], stake_active_bins])
    n_bins = len(labels)
    colors_n = [COLOR_INACTIVE] + [COLOR_ACTIVE_N] * n_active_bins
    colors_s = [COLOR_INACTIVE] + [COLOR_ACTIVE_STAKE] * n_active_bins

    rows = []
    for i, lab in enumerate(labels):
        is_inactive = i == 0
        n = int(counts[i])
        s = float(stake_sum_m[i])
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "group": "inactive" if is_inactive else "active",
                "n_pools": n,
                "share_of_pools_pct": 100.0 * n / (n_active if not is_inactive else n_inactive + n_active),
                "agg_stake_M_ADA": s,
                "share_of_stake_pct": (
                    100.0 * s / stake_active_m
                    if (not is_inactive and stake_active_m > 0)
                    else 100.0 * s / (stake_active_m + stake_inactive_m)
                ),
            }
        )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(13.2, 7.2), constrained_layout=True, sharex=True)

    x = np.arange(n_bins)
    ax = axes[0]
    bars = ax.bar(x, counts, color=colors_n, edgecolor="0.2", width=0.85)
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

    ax = axes[1]
    bars = ax.bar(x, stake_sum_m, color=colors_s, edgecolor="0.2", width=0.85)
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

    xtick_labels = ["Inactive"] + labels[1:]
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(xtick_labels, fontsize=FONT_SIZE - 2, rotation=45, ha="right")
    fig.canvas.draw()
    for ax in axes:
        ticks = ax.get_xticklabels()
        if ticks:
            ticks[0].set_color(COLOR_INACTIVE)
            ticks[0].set_fontweight("bold")

    fig.suptitle(
        "Epoch 644 — stake / delegation distribution by bin\n"
        f"(only Active pools; $n={n_active}$; "
        f"Total stake ${stake_active_m/1e3:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(
        f"n_inactive={n_inactive}, n_active={n_active}, "
        f"stake_active_B={stake_active_m/1e3:.3f}, "
        f"stake_inactive_M={stake_inactive_m:.2f}"
    )
    for r in rows:
        print(
            f"  {r['stake_bin_M_ADA']}: n={r['n_pools']} "
            f"({r['share_of_pools_pct']:.1f}%), "
            f"stake={r['agg_stake_M_ADA']:.1f}M "
            f"({r['share_of_stake_pct']:.1f}%)"
        )


if __name__ == "__main__":
    main()
