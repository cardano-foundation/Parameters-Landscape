#!/usr/bin/env python3
"""
Bubble chart: pool counts by declared fixed cost and margin.
All pools. Epoch 644.

Major fixed-cost values are shown separately; sparse values are
grouped as "other".

Usage:
  python3 plot_fixed_cost_margin_bubbles_epoch_644.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
OUT_PLOT = DIR / "fixed_cost_margin_bubbles_epoch_644.png"

FONT_SIZE = 12
MAJOR_COSTS = (170.0, 200.0, 340.0, 345.0, 400.0, 500.0)
COLORS = {
    170.0: "#2a9d8f",
    200.0: "#8ab17d",
    340.0: "#e76f51",
    345.0: "#f4a261",
    400.0: "#e9c46a",
    500.0: "#264653",
    "other": "#6c757d",
}

# Margin bins (right-open except last which includes 1.0)
EDGES = np.array([0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0, 1.0000001])
LABELS = [
    "0–1%",
    "1–2%",
    "2–5%",
    "5–10%",
    "10–20%",
    "20–50%",
    "50–100%",
    "100%",
]
# Place bubbles at bin midpoints on a linear y scale via categorical positions
Y_POS = np.arange(len(LABELS), dtype=float)


def cost_group(cost: float) -> float | str:
    if cost in MAJOR_COSTS:
        return cost
    return "other"


def load() -> pd.DataFrame:
    df = pd.read_csv(POOLS_CSV)
    out = pd.DataFrame(
        {
            "cost_ada": pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce")
            / 1e6,
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
        }
    ).dropna(subset=["cost_ada", "margin"])
    out["margin"] = out["margin"].clip(0.0, 1.0)
    out["group"] = out["cost_ada"].map(cost_group)
    return out


def main() -> None:
    data = load()
    groups: list[float | str] = list(MAJOR_COSTS) + ["other"]
    x_pos = {g: i for i, g in enumerate(groups)}

    rows: list[dict] = []
    for g in groups:
        m = data.loc[data["group"] == g, "margin"].to_numpy()
        # Put exact m=1 into the last bin; np.histogram last edge is exclusive
        # so use 1.0000001 as right edge above.
        counts, _ = np.histogram(m, bins=EDGES)
        for yp, cnt, lab in zip(Y_POS, counts, LABELS):
            if cnt > 0:
                rows.append({"group": g, "x": x_pos[g], "y": yp, "count": int(cnt), "label": lab})
    bub = pd.DataFrame(rows)
    max_count = int(bub["count"].max())

    fig, ax = plt.subplots(figsize=(10.5, 6.0), constrained_layout=True)
    for g in groups:
        part = bub[bub["group"] == g]
        if part.empty:
            continue
        s = 40.0 + 2200.0 * (part["count"].to_numpy() / max_count) ** 0.85
        ax.scatter(
            part["x"],
            part["y"],
            s=s,
            color=COLORS[g],
            alpha=0.75,
            edgecolors="white",
            linewidths=0.8,
            zorder=3,
        )
        for _, r in part.iterrows():
            ax.text(
                r["x"],
                r["y"],
                str(int(r["count"])),
                ha="center",
                va="center",
                fontsize=7.5,
                color="0.1",
                zorder=4,
            )

    totals = {g: int((data["group"] == g).sum()) for g in groups}
    xticklabels = [
        f"{int(c) if isinstance(c, float) else c}\n(n={totals[c]})" for c in groups
    ]
    ax.set_xticks(list(range(len(groups))))
    ax.set_xticklabels(xticklabels)
    ax.set_xlim(-0.6, len(groups) - 0.4)
    ax.set_yticks(Y_POS)
    ax.set_yticklabels(LABELS)
    ax.set_ylim(-0.7, len(LABELS) - 0.3)
    ax.set_xlabel("Declared fixed cost (ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Declared margin m", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — pool counts by fixed cost and margin\n"
        "(all pools; circle area ∝ count; sparse costs → other)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE - 1)
    ax.grid(axis="y", which="major", alpha=0.25, zorder=0)

    for c in sorted({10, 100, max(200, max_count // 2), max_count}):
        s = 40.0 + 2200.0 * (c / max_count) ** 0.85
        ax.scatter([], [], s=s, color="0.55", alpha=0.7, edgecolors="white", label=f"{c} pools")
    ax.legend(
        frameon=False,
        fontsize=FONT_SIZE - 1,
        title="Bubble size",
        title_fontsize=FONT_SIZE - 1,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        labelspacing=1.2,
        handletextpad=1.0,
    )

    other_vals = sorted(data.loc[data["group"] == "other", "cost_ada"].unique())
    ax.text(
        0.02,
        0.02,
        f"n={len(data)} pools; other covers {len(other_vals)} distinct costs",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color="0.35",
    )
    fig.savefig(OUT_PLOT, dpi=160, bbox_inches="tight")
    print(f"wrote {OUT_PLOT}")
    print("column totals:", totals)
    print(bub.pivot_table(index="label", columns="group", values="count", fill_value=0))


if __name__ == "__main__":
    main()
