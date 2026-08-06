#!/usr/bin/env python3
"""Margin behavior for 426->500 using root CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

DIR = Path(__file__).resolve().parent
OUT = DIR / "margin_changes.png"

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
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
        }
    ).set_index("pool_id")
    return out


def window_stats(a: pd.DataFrame, b: pd.DataFrame) -> dict[str, int | float]:
    common = a.index.intersection(b.index)
    ma = a.loc[common, "margin"]
    mb = b.loc[common, "margin"]
    sa = a.loc[common, "stake"]
    sb = b.loc[common, "stake"]
    da = a.loc[common, "delegators"]
    db = b.loc[common, "delegators"]

    down = mb < ma
    up = mb > ma
    same = mb == ma
    d_stake = sb - sa
    d_pct = np.where(sa > 0, d_stake / sa * 100.0, np.nan)
    d_del = db - da

    def group(mask: pd.Series) -> dict[str, int | float]:
        if not mask.any():
            return {
                "n": 0,
                "gain_stake": 0,
                "lose_stake": 0,
                "flat_stake": 0,
                "gain_del": 0,
                "lose_del": 0,
                "flat_del": 0,
                "median_dstake_ada": float("nan"),
                "median_dpct": float("nan"),
                "median_ddel": float("nan"),
                "sum_ddel": 0.0,
            }
        return {
            "n": int(mask.sum()),
            "gain_stake": int((d_stake[mask] > 0).sum()),
            "lose_stake": int((d_stake[mask] < 0).sum()),
            "flat_stake": int((d_stake[mask] == 0).sum()),
            "gain_del": int((d_del[mask] > 0).sum()),
            "lose_del": int((d_del[mask] < 0).sum()),
            "flat_del": int((d_del[mask] == 0).sum()),
            "median_dstake_ada": float(d_stake[mask].median() / 1e6),
            "median_dpct": float(np.nanmedian(d_pct[mask])),
            "median_ddel": float(d_del[mask].median()),
            "sum_ddel": float(d_del[mask].sum()),
        }

    return {
        "common": int(len(common)),
        "n_down": int(down.sum()),
        "n_up": int(up.sum()),
        "n_same": int(same.sum()),
        "down": group(down),
        "up": group(up),
    }


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)
    st = window_stats(a, b)

    common = a.index.intersection(b.index)
    ma = a.loc[common, "margin"]
    mb = b.loc[common, "margin"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2), constrained_layout=True)

    ax = axes[0]
    labels = ["margin ↓", "margin ↑", "same"]
    vals = [st["n_down"], st["n_up"], st["n_same"]]
    cols = [COLOR_DOWN, COLOR_UP, COLOR_SAME]
    bars = ax.bar(labels, vals, color=cols)
    ax.set_ylabel("Pools", fontsize=FONT_SIZE)
    ax.set_title("Margin change counts (426→500)", fontsize=FONT_SIZE)
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
        st["down"]["gain_stake"],
        st["down"]["lose_stake"],
        st["down"]["flat_stake"],
        st["down"]["gain_del"],
        st["down"]["lose_del"],
        st["down"]["flat_del"],
    ]
    cols2 = [COLOR_GAIN, COLOR_LOSE, COLOR_FLAT, COLOR_GAIN, COLOR_LOSE, COLOR_FLAT]
    x2 = np.arange(len(labels2))
    bars2 = ax.bar(x2, vals2, color=cols2)
    ax.set_xticks(x2)
    ax.set_xticklabels(labels2, rotation=20, ha="right", fontsize=FONT_SIZE - 1)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(f"Among {st['n_down']} pools with margin ↓", fontsize=FONT_SIZE)
    for bbar, v in zip(bars2, vals2):
        if v > 0:
            ax.text(bbar.get_x() + bbar.get_width() / 2, v + 2, str(int(v)), ha="center", fontsize=8)

    fig.suptitle("Margin lever, 426→500", fontsize=FONT_SIZE + 1)
    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
