#!/usr/bin/env python3
"""
Box plots of member APR for undersaturated pools around the k=150→500 change.

Three groups (positive APR only, matching the summary table):
  k=150: all undersaturated pools (σ_228 ≤ z0(k=500))
  k=150: survivors to epoch 285
  k=500: survivors, fees adjusted (m,c from epoch 285)

Style matches member_apr_boxplot_cohort_426_500.png (peach boxes, orange medians).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
INPUT_CSV = DIR / "member_return_k150_vs_k500_feeadjusted_epoch_228.csv"
OUT_PLOT = DIR / "member_apr_boxplot_undersaturated_k150_vs_k500.png"

Z0_K500 = 64.07e6
FONT_SIZE = 11
BOX_FACE = "#f4c4a8"
BOX_EDGE = "0.15"
MEDIAN_COLOR = "#e76f51"


def draw_boxes(
    ax: plt.Axes,
    groups: list[tuple[str, np.ndarray]],
) -> None:
    data = []
    labels = []
    for name, values in groups:
        vals = np.asarray(values, dtype=float)
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

    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_ylim(bottom=0.0)
    ax.grid(axis="y", alpha=0.25)

    tops: list[float] = []
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
            f"{med:.2f}",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE - 1,
            color="0.15",
        )
    if tops:
        y_hi = max(tops)
        ax.set_ylim(0.0, y_hi * 1.18 if y_hi > 0 else 1.0)


def main() -> None:
    all_pools = pd.read_csv(INPUT_CSV)
    cohort = all_pools.loc[all_pools["sigma_ada_228"] <= Z0_K500].copy()
    survivors = cohort.loc[cohort["survives_to_285"]].copy()

    apr_150 = "member_apr_simple_k150"
    apr_500 = "member_apr_simple_k500_feeadjusted"

    g_all = 100.0 * cohort[apr_150].dropna()
    g_all = g_all[g_all > 0].to_numpy()

    g_surv_150 = 100.0 * survivors[apr_150].dropna()
    g_surv_150 = g_surv_150[g_surv_150 > 0].to_numpy()

    g_surv_500 = 100.0 * survivors[apr_500].dropna()
    g_surv_500 = g_surv_500[g_surv_500 > 0].to_numpy()

    fig, ax = plt.subplots(figsize=(9.5, 5.0), constrained_layout=True)
    draw_boxes(
        ax,
        [
            ("$k=150$\n(all undersaturated)", g_all),
            ("$k=150$\n(survivors)", g_surv_150),
            ("$k=500$\n(survivors, fees adj.)", g_surv_500),
        ],
    )
    fig.suptitle(
        "Member APR around the $k$ increment (undersaturated pools)\n"
        rf"($\sigma_{{228}}\leq z_0(k=500)={Z0_K500/1e6:.2f}$M ADA; "
        r"positive APR pools only ($f>c$))"
        "\n"
        "(numbers above boxes are medians)",
        fontsize=FONT_SIZE + 1,
    )
    fig.savefig(OUT_PLOT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUT_PLOT}")
    print(
        f"n positive: all={len(g_all)}, surv150={len(g_surv_150)}, "
        f"surv500={len(g_surv_500)}"
    )
    print(
        "medians (%): "
        f"all={np.median(g_all):.2f}, "
        f"surv150={np.median(g_surv_150):.2f}, "
        f"surv500={np.median(g_surv_500):.2f}"
    )


if __name__ == "__main__":
    main()
