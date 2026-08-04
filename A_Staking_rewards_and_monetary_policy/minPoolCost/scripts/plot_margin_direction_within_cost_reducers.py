#!/usr/bin/env python3
"""Among fixed-cost reducers (426->500), count margin down/up/same."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "margin_direction_within_cost_reducers_426_500.png"

E0 = 426
E1 = 500
FONT_SIZE = 11


def main() -> None:
    a = pd.read_csv(DIR / f"staking_pools_full_epoch_{E0}.csv").set_index("pool_id")
    b = pd.read_csv(DIR / f"staking_pools_full_epoch_{E1}.csv").set_index("pool_id")

    common = a.index.intersection(b.index)
    fa = pd.to_numeric(a.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    fb = pd.to_numeric(b.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    ma = pd.to_numeric(a.loc[common, "pool_update.active.margin"], errors="coerce")
    mb = pd.to_numeric(b.loc[common, "pool_update.active.margin"], errors="coerce")

    cut = fb < fa
    m_down = int((mb[cut] < ma[cut]).sum())
    m_up = int((mb[cut] > ma[cut]).sum())
    m_same = int((mb[cut] == ma[cut]).sum())
    n_cut = int(cut.sum())

    labels = ["margin ↓", "margin ↑", "margin same"]
    vals = [m_down, m_up, m_same]
    cols = ["#2a9d8f", "#e76f51", "#9ca3af"]

    fig, ax = plt.subplots(1, 1, figsize=(7.6, 4.8), constrained_layout=True)
    bars = ax.bar(labels, vals, color=cols)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        f"Margin changes among pools with fixed cost ↓ ({E0}→{E1})\n"
        f"(fixed-cost reducers n={n_cut})",
        fontsize=FONT_SIZE,
    )
    for bbar, v in zip(bars, vals):
        ax.text(bbar.get_x() + bbar.get_width() / 2, v + 3, str(v), ha="center", fontsize=10)

    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")
    print(
        {
            "fixed_cost_reducers": n_cut,
            "margin_down": m_down,
            "margin_up": m_up,
            "margin_same": m_same,
        }
    )


if __name__ == "__main__":
    main()
