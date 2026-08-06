#!/usr/bin/env python3
"""
Box-plot characteristics at epoch 426 for margin-change cohorts (426→500).

Writes two figures (three panels each):
  1. Margin reducers vs increasers vs same: stake, declared pledge, active pledge
  2. Among margin reducers, stake gainers vs losers: same three metrics

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
OUT_GROUPS = DIR / "margin_change_groups_characteristics_426.png"
OUT_OUTCOMES = DIR / "margin_reducer_stake_outcome_characteristics_426.png"

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


def save_three_panel(
    path: Path,
    *,
    series_by_metric: dict[str, pd.Series],
    groups: list[tuple[str, pd.Series]],
    suptitle: str,
    figsize: tuple[float, float] = (12.5, 4.2),
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=figsize, constrained_layout=True)
    for ax, (key, title, ylabel, scale) in zip(axes, METRICS):
        series = series_by_metric[key]
        draw_boxes(
            ax,
            [(name, series[mask]) for name, mask in groups],
            title=title,
            ylabel=ylabel,
            scale=scale,
        )
    fig.suptitle(suptitle, fontsize=FONT_SIZE + 1)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)
    common = a.index.intersection(b.index)

    ma = a.loc[common, "margin"]
    mb = b.loc[common, "margin"]
    sa = a.loc[common, "stake"]
    sb = b.loc[common, "stake"]

    reducers = mb < ma
    increasers = mb > ma
    same = mb == ma
    gainers = reducers & (sb > sa)
    losers = reducers & (sb < sa)

    series_by_metric = {key: a.loc[common, key] for key, *_ in METRICS}

    save_three_panel(
        OUT_GROUPS,
        series_by_metric=series_by_metric,
        groups=[
            ("Reducers", reducers),
            ("Increasers", increasers),
            ("Same", same),
        ],
        suptitle=(
            f"Margin reducers vs increasers vs same ({E0}→{E1}): "
            f"characteristics at epoch {E0}"
        ),
        figsize=(13.5, 4.2),
    )
    save_three_panel(
        OUT_OUTCOMES,
        series_by_metric=series_by_metric,
        groups=[("Gainers", gainers), ("Losers", losers)],
        suptitle=(
            f"Among margin reducers ({E0}→{E1}): stake gainers vs losers, "
            f"characteristics at epoch {E0}"
        ),
    )
    print(
        f"Reducers={int(reducers.sum())}, increasers={int(increasers.sum())}, "
        f"same={int(same.sum())}, gainers={int(gainers.sum())}, "
        f"losers={int(losers.sum())}"
    )


if __name__ == "__main__":
    main()
