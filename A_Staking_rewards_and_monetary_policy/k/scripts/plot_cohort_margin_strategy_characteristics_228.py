#!/usr/bin/env python3
"""
Box-plot characteristics at epoch 228 for margin-change cohorts (228→285).

Three panels: stake, declared pledge, active pledge — comparing
margin reducers / increasers / no-change among Active pools that remain
Active at 285.

Active = not (σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs).
Style matches cost_reducer_vs_nonreducer_characteristics_426.png
(peach boxes, orange medians).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "cohort_margin_strategy_characteristics_228.png"

E0, E1 = 228, 285
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
    flags = pd.read_csv(DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv")
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    )
    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake": stake.fillna(0.0) / 1e6,
            "declared_pledge": pd.to_numeric(
                df["pool_update.active.pledge"], errors="coerce"
            )
            / 1e6,
            "active_pledge": pd.to_numeric(df["pledged"], errors="coerce") / 1e6,
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
        }
    )
    out = out.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    out["active"] = out["in_union"] == 0
    return out.set_index("pool_id")


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

    # Annotate medians above each box; expand ylim for headroom.
    tops = []
    for i, arr in enumerate(data, start=1):
        if arr.size == 0:
            continue
        med = float(np.median(arr))
        q1, q3 = np.percentile(arr, [25.0, 75.0])
        iqr = q3 - q1
        top = float(min(arr.max(), q3 + 1.5 * iqr))
        tops.append(top)
        ax.text(
            i,
            top,
            f"{med:.1f}",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE - 1,
            color="0.15",
        )
    if tops:
        y_hi = max(tops)
        ax.set_ylim(0.0, y_hi * 1.18 if y_hi > 0 else 1.0)


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)

    cohort = a.index[a["active"]]
    surviving = cohort.intersection(b.index[b["active"]])
    aa = a.loc[surviving]
    bb = b.loc[surviving]
    ok = aa["margin"].notna() & bb["margin"].notna()
    aa, bb = aa.loc[ok], bb.loc[ok]

    dm = bb["margin"] - aa["margin"]
    reducers = dm < 0
    increasers = dm > 0
    no_change = dm == 0

    groups = [
        ("Reducers", reducers),
        ("Increasers", increasers),
        ("No change", no_change),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), constrained_layout=True)
    for ax, (key, title, ylabel, scale) in zip(axes, METRICS):
        series = aa[key]
        draw_boxes(
            ax,
            [(name, series[mask]) for name, mask in groups],
            title=title,
            ylabel=ylabel,
            scale=scale,
        )
    fig.suptitle(
        f"Active pools: margin reducers / increasers / no change ({E0}→{E1}): "
        f"characteristics at epoch {E0}\n"
        f"(continuing Active $n={len(aa)}$; numbers above boxes are medians)",
        fontsize=FONT_SIZE + 1,
    )
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUT}")
    print(
        f"Reducers={int(reducers.sum())}, "
        f"Increasers={int(increasers.sum())}, "
        f"No change={int(no_change.sum())}"
    )
    for name, mask in groups:
        st = aa.loc[mask, "stake"]
        dec = aa.loc[mask, "declared_pledge"]
        act = aa.loc[mask, "active_pledge"]
        print(
            f"  {name}: n={int(mask.sum())} "
            f"stake Q1/med/Q3={st.quantile(0.25)/1e6:.2f}/{st.median()/1e6:.2f}/{st.quantile(0.75)/1e6:.2f}M "
            f"decl med={dec.median()/1e3:.1f}k act med={act.median()/1e3:.1f}k"
        )


if __name__ == "__main__":
    main()
