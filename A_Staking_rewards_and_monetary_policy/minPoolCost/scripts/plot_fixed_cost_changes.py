#!/usr/bin/env python3
"""Fixed-cost behavior for 426->500 using root CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

DIR = Path(__file__).resolve().parent
OUT = DIR / "fixed_cost_changes.png"

E0 = 426
E1 = 500
FONT_SIZE = 11
COLOR_DOWN = "#2a9d8f"
COLOR_UP = "#e76f51"
COLOR_SAME = "#9ca3af"
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake": pd.to_numeric(df["active_stake"], errors="coerce"),
            "delegators": pd.to_numeric(df["epochs.0.data.delegators"], errors="coerce"),
            "fixed_cost": pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce"),
        }
    ).set_index("pool_id")
    return out


def window_stats(a: pd.DataFrame, b: pd.DataFrame) -> dict[str, int | float]:
    common = a.index.intersection(b.index)
    fa = a.loc[common, "fixed_cost"]
    fb = b.loc[common, "fixed_cost"]
    sa = a.loc[common, "stake"]
    sb = b.loc[common, "stake"]
    da = a.loc[common, "delegators"]
    db = b.loc[common, "delegators"]

    down = fb < fa
    up = fb > fa
    same = fb == fa
    d_stake = sb - sa
    d_pct = np.where(sa > 0, d_stake / sa * 100.0, np.nan)
    d_del = db - da

    return {
        "common": int(len(common)),
        "n_down": int(down.sum()),
        "n_up": int(up.sum()),
        "n_same": int(same.sum()),
        "down_gain_stake": int((d_stake[down] > 0).sum()),
        "down_lose_stake": int((d_stake[down] < 0).sum()),
        "down_flat_stake": int((d_stake[down] == 0).sum()),
        "down_gain_del": int((d_del[down] > 0).sum()),
        "down_lose_del": int((d_del[down] < 0).sum()),
        "down_flat_del": int((d_del[down] == 0).sum()),
        "down_median_dstake_ada": float(d_stake[down].median() / 1e6)
        if down.any()
        else float("nan"),
        "down_median_dpct": float(np.nanmedian(d_pct[down])) if down.any() else float("nan"),
        "down_median_ddel": float(d_del[down].median()) if down.any() else float("nan"),
        "down_sum_ddel": float(d_del[down].sum()) if down.any() else 0.0,
    }


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)
    st = window_stats(a, b)

    common = a.index.intersection(b.index)
    fa = a.loc[common, "fixed_cost"]
    fb = b.loc[common, "fixed_cost"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), constrained_layout=True)

    ax = axes[0]
    labels = ["cost ↓", "cost ↑", "same"]
    vals = [st["n_down"], st["n_up"], st["n_same"]]
    cols = [COLOR_DOWN, COLOR_UP, COLOR_SAME]
    bars = ax.bar(labels, vals, color=cols)
    ax.set_ylabel("Pools", fontsize=FONT_SIZE)
    ax.set_title("Fixed-cost change counts (426→500)", fontsize=FONT_SIZE)
    for bbar, v in zip(bars, vals):
        ax.text(bbar.get_x() + bbar.get_width() / 2, v + 8, str(v), ha="center", fontsize=9)
    ax.text(
        0.01,
        0.98,
        f"Continuing pools = present in both epochs: {st['common']}",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
        color="0.35",
    )

    ax = axes[1]
    labels2 = ["gain stake", "lose stake", "flat stake", "gain delegators", "lose delegators", "flat delegators"]
    vals2 = [
        st["down_gain_stake"],
        st["down_lose_stake"],
        st["down_flat_stake"],
        st["down_gain_del"],
        st["down_lose_del"],
        st["down_flat_del"],
    ]
    cols2 = [COLOR_GAIN, COLOR_LOSE, COLOR_FLAT, COLOR_GAIN, COLOR_LOSE, COLOR_FLAT]
    x2 = np.arange(len(labels2))
    bars2 = ax.bar(x2, vals2, color=cols2)
    ax.set_xticks(x2)
    ax.set_xticklabels(labels2, rotation=20, ha="right", fontsize=FONT_SIZE - 1)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(f"Among {st['n_down']} pools with fixed cost ↓", fontsize=FONT_SIZE)
    for bbar, v in zip(bars2, vals2):
        if v > 0:
            ax.text(bbar.get_x() + bbar.get_width() / 2, v + 3, str(int(v)), ha="center", fontsize=8)

    fig.suptitle("Fixed-cost lever, 426→500", fontsize=FONT_SIZE + 1)
    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
