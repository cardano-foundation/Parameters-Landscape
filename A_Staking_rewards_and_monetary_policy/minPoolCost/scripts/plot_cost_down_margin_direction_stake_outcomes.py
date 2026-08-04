#!/usr/bin/env python3
"""Stake outcomes for cost↓+margin↓ vs cost↓+margin↑ pools (426→500)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "cost_down_margin_direction_stake_outcomes_426_500.png"

E0 = 426
E1 = 500
FONT_SIZE = 11
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"


def stake_outcomes(mask: pd.Series, d_stake: pd.Series) -> tuple[int, list[int]]:
    n = int(mask.sum())
    vals = [
        int((d_stake[mask] > 0).sum()),
        int((d_stake[mask] < 0).sum()),
        int((d_stake[mask] == 0).sum()),
    ]
    return n, vals


def draw_panel(ax, title: str, n: int, vals: list[int]) -> None:
    labels = ["gain stake", "lose stake", "flat stake"]
    cols = [COLOR_GAIN, COLOR_LOSE, COLOR_FLAT]
    x = np.arange(len(labels))
    bars = ax.bar(x, vals, color=cols)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(f"{title}\n(n={n})", fontsize=FONT_SIZE)
    ymax = max(vals) if vals else 1
    for bbar, v in zip(bars, vals):
        if v > 0:
            ax.text(
                bbar.get_x() + bbar.get_width() / 2,
                v + ymax * 0.03,
                str(v),
                ha="center",
                fontsize=9,
            )


def main() -> None:
    a = pd.read_csv(DIR / f"staking_pools_full_epoch_{E0}.csv").set_index("pool_id")
    b = pd.read_csv(DIR / f"staking_pools_full_epoch_{E1}.csv").set_index("pool_id")
    common = a.index.intersection(b.index)

    fa = pd.to_numeric(a.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    fb = pd.to_numeric(b.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    ma = pd.to_numeric(a.loc[common, "pool_update.active.margin"], errors="coerce")
    mb = pd.to_numeric(b.loc[common, "pool_update.active.margin"], errors="coerce")
    sa = pd.to_numeric(a.loc[common, "active_stake"], errors="coerce")
    sb = pd.to_numeric(b.loc[common, "active_stake"], errors="coerce")
    d_stake = sb - sa

    mask_down = (fb < fa) & (mb < ma)
    mask_up = (fb < fa) & (mb > ma)
    n_down, vals_down = stake_outcomes(mask_down, d_stake)
    n_up, vals_up = stake_outcomes(mask_up, d_stake)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), constrained_layout=True)
    draw_panel(axes[0], "Fixed cost ↓ and margin ↓", n_down, vals_down)
    draw_panel(axes[1], "Fixed cost ↓ and margin ↑", n_up, vals_up)
    fig.suptitle(f"Stake outcomes among cost reducers ({E0}→{E1})", fontsize=FONT_SIZE + 1)

    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")
    print({"cost_down_margin_down": {"n": n_down, "vals": vals_down}})
    print({"cost_down_margin_up": {"n": n_up, "vals": vals_up}})


if __name__ == "__main__":
    main()
