#!/usr/bin/env python3
"""
Among fixed-cost reducers (426→500), box-plot characteristics at epoch 426
by combined margin strategy: margin ↓ / ↑ / same.

Declared pledge = pool_update.active.pledge
Active pledge   = pledged (epoch snapshot)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "cost_reducer_margin_strategy_characteristics_426.png"

E0 = 426
E1 = 500
FONT_SIZE = 11
BOX_FACE = "#f4c4a8"
BOX_EDGE = "0.15"
MEDIAN_COLOR = "#e76f51"

METRICS = [
    ("stake", "Stake", "Stake (M ADA)", 1e6),
    ("declared_pledge", "Declared pledge", "Declared pledge (k ADA)", 1e3),
    ("active_pledge", "Active pledge", "Active pledge (k ADA)", 1e3),
]


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake": pd.to_numeric(df["active_stake"], errors="coerce") / 1e6,
            "declared_pledge": pd.to_numeric(
                df["pool_update.active.pledge"], errors="coerce"
            )
            / 1e6,
            "active_pledge": pd.to_numeric(df["pledged"], errors="coerce") / 1e6,
            "fixed_cost": pd.to_numeric(
                df["pool_update.active.fixed_cost"], errors="coerce"
            ),
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
        }
    ).set_index("pool_id")
    return out


def draw_boxes(
    ax,
    groups: list[tuple[str, pd.Series]],
    *,
    title: str,
    ylabel: str,
    scale: float,
) -> None:
    data = []
    labels = []
    for name, series in groups:
        vals = series.dropna().to_numpy(dtype=float) / scale
        vals = vals[np.isfinite(vals)]
        data.append(vals)
        labels.append(f"{name}\n(n={len(vals)})")

    bp = ax.boxplot(
        data,
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        whiskerprops={"color": BOX_EDGE, "linewidth": 1.1},
        capprops={"color": BOX_EDGE, "linewidth": 1.1},
        boxprops={"color": BOX_EDGE, "linewidth": 1.1},
    )
    for box in bp["boxes"]:
        box.set_facecolor(BOX_FACE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_ylim(bottom=0.0)
    ax.grid(axis="y", alpha=0.25)


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)
    common = a.index.intersection(b.index)

    fa = a.loc[common, "fixed_cost"]
    fb = b.loc[common, "fixed_cost"]
    ma = a.loc[common, "margin"]
    mb = b.loc[common, "margin"]

    cost_down = fb < fa
    m_down = cost_down & (mb < ma)
    m_up = cost_down & (mb > ma)
    m_same = cost_down & (mb == ma)

    series_by_metric = {key: a.loc[common, key] for key, *_ in METRICS}
    groups = [
        ("margin ↓", m_down),
        ("margin ↑", m_up),
        ("margin same", m_same),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), constrained_layout=True)
    for ax, (key, title, ylabel, scale) in zip(axes, METRICS):
        series = series_by_metric[key]
        draw_boxes(
            ax,
            [(name, series[mask]) for name, mask in groups],
            title=title,
            ylabel=ylabel,
            scale=scale,
        )

    fig.suptitle(
        f"Among fixed-cost reducers ({E0}→{E1}): characteristics at epoch {E0}\n"
        f"by combined margin strategy (cost reducers n={int(cost_down.sum())})",
        fontsize=FONT_SIZE + 1,
    )
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT}")
    print(
        {
            "cost_reducers": int(cost_down.sum()),
            "cost_down_margin_down": int(m_down.sum()),
            "cost_down_margin_up": int(m_up.sum()),
            "cost_down_margin_same": int(m_same.sum()),
        }
    )


if __name__ == "__main__":
    main()
