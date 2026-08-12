#!/usr/bin/env python3
r"""
Characteristics of NEW ENTRANTS to losing / edge groups when k: 500 -> 1000.

Same three aggregated groups as pool_viability_losing_vs_edge_traits_epoch_644.png:
  - Losing ($r<0.5$):     losing_lt_025, losing_025_050
  - Losing ($0.5\leq r<1$): losing_050_075, losing_075_100
  - Edge ($1\leq r<2$):   edge

A pool is an entrant to group G at k=1000 if category_k1000 is in G and
category_k500 is not in G. Leavers and comfortable/strong bins are excluded.

Writes:
  pool_viability_k1000_bin_movers_traits_epoch_644.png
  pool_viability_k1000_bin_movers_epoch_644.csv
  pool_viability_k1000_bin_movers_epoch_644.md
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
VIABILITY_CSV = DIR / "pool_viability_k500_vs_k1000_epoch_644.csv"
OUT_PLOT = DIR / "pool_viability_k1000_bin_movers_traits_epoch_644.png"
OUT_CSV = DIR / "pool_viability_k1000_bin_movers_epoch_644.csv"
OUT_MD = DIR / "pool_viability_k1000_bin_movers_epoch_644.md"

FONT_SIZE = 12
C_STAR_ADA = 667.0 / 6.0 / 0.15
MEDIAN_COLOR = "#111111"

ALL_CATS = frozenset(
    {
        "losing_lt_025",
        "losing_025_050",
        "losing_050_075",
        "losing_075_100",
        "edge",
        "comfortable",
        "strong",
    }
)

GROUPS: tuple[tuple[str, frozenset[str], str], ...] = (
    (
        "losing_deep",
        frozenset({"losing_lt_025", "losing_025_050"}),
        r"Losing" "\n" r"($r<0.5$)",
    ),
    (
        "losing_near",
        frozenset({"losing_050_075", "losing_075_100"}),
        r"Losing" "\n" r"($0.5\leq r<1$)",
    ),
    (
        "edge",
        frozenset({"edge"}),
        "Edge\n" r"($1\leq r<2$)",
    ),
)
GROUP_COLORS = ("#67000d", "#de2d26", "#e76f51")


def in_group(series: pd.Series, cats: frozenset[str]) -> pd.Series:
    return series.isin(cats)


def entrants_for_group(df: pd.DataFrame, group_id: str, cats: frozenset[str]) -> pd.DataFrame:
    entered = in_group(df["category_k1000"], cats) & ~in_group(df["category_k500"], cats)
    out = df[entered].copy()
    out["target_group"] = group_id
    return out


def main() -> None:
    pools = pd.read_csv(POOLS_CSV)
    via = pd.read_csv(VIABILITY_CSV)

    extra = pools[
        ["pool_id", "epochs.0.data.delegators", "epochs.0.data.block.minted"]
    ].copy()
    extra["delegators"] = pd.to_numeric(
        extra["epochs.0.data.delegators"], errors="coerce"
    )
    extra["blocks_minted"] = pd.to_numeric(
        extra["epochs.0.data.block.minted"], errors="coerce"
    ).fillna(0.0)

    df = via.merge(extra[["pool_id", "delegators", "blocks_minted"]], on="pool_id")
    df = df[
        df["pledge_met"]
        & df["category_k500"].isin(ALL_CATS)
        & df["category_k1000"].isin(ALL_CATS)
    ].copy()

    entrant_frames: list[pd.DataFrame] = []
    group_counts: dict[str, int] = {}
    for group_id, cats, _label in GROUPS:
        sub = entrants_for_group(df, group_id, cats)
        group_counts[group_id] = len(sub)
        entrant_frames.append(sub)

    entrants = pd.concat(entrant_frames, ignore_index=True)
    entrants = entrants.sort_values(
        ["target_group", "ratio_k1000"], ascending=[True, False]
    )
    entrants.to_csv(OUT_CSV, index=False)

    md_lines = [
        "# Epoch 644 — new entrants to losing / edge groups ($k=500 \\to k=1000$)\n",
        f"$C^*={C_STAR_ADA:.1f}$ ADA/epoch. Pledge-met pools only. Entrants only.\n",
    ]
    for group_id, _cats, label in GROUPS:
        label_flat = label.replace("\n", " ")
        n = group_counts[group_id]
        md_lines.append(f"\n## {label_flat} — {n} new entrants\n")
        sub = entrants[entrants["target_group"] == group_id]
        if sub.empty:
            md_lines.append("_No entrants._\n")
            continue
        md_lines.append(
            "| Ticker | Pool ID | $r$ ($k=500$) | $r$ ($k=1000$) | "
            "From | To | Stake (M ADA) |\n"
            "|:---|:---|---:|---:|:---|:---|---:|\n"
        )
        for _, row in sub.iterrows():
            ticker = row["pool_ticker"] if pd.notna(row["pool_ticker"]) else "—"
            md_lines.append(
                f"| {ticker} | `{row['pool_id']}` | "
                f"{row['ratio_k500']:.3f} | {row['ratio_k1000']:.3f} | "
                f"{row['category_k500']} | {row['category_k1000']} | "
                f"{row['sigma_ada']/1e6:.2f} |\n"
            )
    OUT_MD.write_text("".join(md_lines))

    trait_groups = [
        (label, entrants[entrants["target_group"] == group_id], color)
        for (group_id, _cats, label), color in zip(GROUPS, GROUP_COLORS)
    ]
    labels_with_n = [
        f"{label}\n(n={group_counts[group_id]})"
        for (group_id, _cats, label) in GROUPS
    ]

    fig, axes = plt.subplots(3, 3, figsize=(13.5, 9.5), constrained_layout=True)

    def series_by_group(col: str, transform=None) -> list[np.ndarray]:
        out: list[np.ndarray] = []
        for _label, sub, _color in trait_groups:
            if sub.empty:
                out.append(np.array([]))
                continue
            vals = sub[col].astype(float)
            if transform is not None:
                vals = transform(vals)
            out.append(vals.dropna().to_numpy())
        return out

    def box_groups(ax, data: list[np.ndarray], ylabel: str, title: str) -> None:
        bp = ax.boxplot(
            data,
            tick_labels=labels_with_n,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        )
        for patch, color in zip(bp["boxes"], GROUP_COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE - 1)

    box_groups(
        axes[0, 0],
        series_by_group("sigma_ada", lambda s: s / 1e6),
        "Epoch stake (M ADA)",
        "Epoch stake",
    )
    box_groups(
        axes[0, 1],
        series_by_group("active_pledge_ada", lambda s: s / 1e3),
        "Active pledge (k ADA)",
        "Active pledge",
    )
    box_groups(
        axes[0, 2],
        series_by_group("declared_pledge_ada", lambda s: s / 1e3),
        "Declared pledge (k ADA)",
        "Declared pledge",
    )
    box_groups(
        axes[1, 0],
        series_by_group("margin", lambda s: s * 100.0),
        "Declared margin (%)",
        "Margin",
    )
    box_groups(
        axes[1, 1],
        series_by_group("blocks_minted"),
        "Blocks minted (epoch)",
        "Blocks",
    )
    box_groups(
        axes[1, 2],
        series_by_group("delegators"),
        "Delegators",
        "Delegators",
    )
    box_groups(
        axes[2, 0],
        series_by_group("declared_fixed_cost_ada"),
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
    )
    axes[2, 1].axis("off")
    axes[2, 2].axis("off")
    axes[2, 1].text(
        0.0,
        0.9,
        f"New entrants only ($k=500 \\to k=1000$):\n"
        f"• Losing ($r<0.5$): {group_counts['losing_deep']}\n"
        f"• Losing ($0.5\\leq r<1$): {group_counts['losing_near']}\n"
        f"• Edge ($1\\leq r<2$): {group_counts['edge']}\n"
        f"Total unique: {len(entrants)}",
        ha="left",
        va="top",
        fontsize=FONT_SIZE,
    )

    fig.suptitle(
        "Epoch 644 — characteristics of new entrants to losing / edge groups\n"
        rf"($k=500 \to k=1000$, $C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; "
        "pledge-met pools)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)

    print(f"entrants: losing_deep={group_counts['losing_deep']}, "
          f"losing_near={group_counts['losing_near']}, edge={group_counts['edge']}")
    print(f"total unique entrants: {len(entrants)}")
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
