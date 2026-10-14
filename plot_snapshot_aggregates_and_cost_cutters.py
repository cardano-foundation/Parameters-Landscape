#!/usr/bin/env python3
"""
Snapshot aggregate view (Active pools) + 445->500 fixed-cost-cutter outcomes.
Declared pledge is the certificate active at each epoch.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pastreduction_common import load_active

DIR = Path(__file__).resolve().parent
OUT = DIR / "snapshot_aggregates_and_cost_cutters.png"

EPOCHS = (426, 445, 500)
FONT_SIZE = 11
COLOR_STAKE = "#2f5d85"
COLOR_PLEDGE = "#b23a3a"
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"


def load_epoch(epoch: int) -> pd.DataFrame:
    return load_active(epoch)


def main() -> None:
    dfs = {e: load_epoch(e) for e in EPOCHS}

    total_stake_b = [
        pd.to_numeric(dfs[e]["active_stake"], errors="coerce").fillna(0).sum() / 1e15
        for e in EPOCHS
    ]
    total_pledge_b = [
        pd.to_numeric(dfs[e]["pool_update.active.pledge"], errors="coerce").fillna(0).sum()
        / 1e15
        for e in EPOCHS
    ]

    a = dfs[445].set_index("pool_id")
    b = dfs[500].set_index("pool_id")
    common = a.index.intersection(b.index)
    fa = pd.to_numeric(a.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    fb = pd.to_numeric(b.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    sa = pd.to_numeric(a.loc[common, "active_stake"], errors="coerce")
    sb = pd.to_numeric(b.loc[common, "active_stake"], errors="coerce")
    da = pd.to_numeric(a.loc[common, "epochs.0.data.delegators"], errors="coerce")
    db = pd.to_numeric(b.loc[common, "epochs.0.data.delegators"], errors="coerce")

    cut = fb < fa
    d_stake = sb - sa
    d_del = db - da
    n_cut = int(cut.sum())
    gain_stake = int((d_stake[cut] > 0).sum())
    lose_stake = int((d_stake[cut] < 0).sum())
    flat_stake = int((d_stake[cut] == 0).sum())
    gain_del = int((d_del[cut] > 0).sum())
    lose_del = int((d_del[cut] < 0).sum())
    flat_del = int((d_del[cut] == 0).sum())

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0), constrained_layout=True)

    ax = axes[0]
    x = np.array(EPOCHS)
    ax.plot(x, total_stake_b, marker="o", color=COLOR_STAKE, label="Total active stake")
    ax.plot(
        x,
        total_pledge_b,
        marker="s",
        linestyle="--",
        color=COLOR_PLEDGE,
        label="Total declared pledge",
    )
    ax.set_title("Snapshot aggregates (Active)", fontsize=FONT_SIZE + 1)
    ax.set_xlabel("Epoch", fontsize=FONT_SIZE)
    ax.set_ylabel("ADA (billions)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1]
    labels = ["Gain stake", "Lose stake", "Flat stake", "Gain dels", "Lose dels", "Flat dels"]
    vals = [gain_stake, lose_stake, flat_stake, gain_del, lose_del, flat_del]
    cols = [COLOR_GAIN, COLOR_LOSE, COLOR_FLAT, COLOR_GAIN, COLOR_LOSE, COLOR_FLAT]
    bars = ax.bar(np.arange(len(labels)), vals, color=cols)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(f"Pools that cut fixed cost 445→500, Active (n={n_cut})", fontsize=FONT_SIZE + 1)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, str(v), ha="center", va="bottom", fontsize=9)

    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")
    print(f"Totals stake (B ADA): {dict(zip(EPOCHS, total_stake_b))}")
    print(
        "445→500 fixed-cost cutters:",
        {
            "n": n_cut,
            "gain_stake": gain_stake,
            "lose_stake": lose_stake,
            "flat_stake": flat_stake,
            "gain_dels": gain_del,
            "lose_dels": lose_del,
            "flat_dels": flat_del,
        },
    )


if __name__ == "__main__":
    main()
