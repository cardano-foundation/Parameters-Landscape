#!/usr/bin/env python3
r"""
Characteristics of pools that move across viability groups when k: 500 -> 1000.

Groups (same aggregation as the traits plot):
  - Losing ($r<0.5$)
  - Losing ($0.5\leq r<1$)
  - Edge ($1\leq r<2$)
  - Comfortable ($2\leq r<5$)
  - Strong ($r\geq5$)

For each group, n in the tick label is the net change in group size
(k=1000 minus k=500). Negative n means the group shrank.
Boxplots show the pools that drove that change: entrants if n≥0,
leavers if n<0.

Active pools only.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_koios_epoch_644.csv"
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
    (
        "comfortable",
        frozenset({"comfortable"}),
        "Comfortable\n" r"($2\leq r<5$)",
    ),
    (
        "strong",
        frozenset({"strong"}),
        "Strong\n" r"($r\geq5$)",
    ),
)
GROUP_COLORS = ("#67000d", "#de2d26", "#e76f51", "#4c78a8", "#2a9d8f")


def in_group(series: pd.Series, cats: frozenset[str]) -> pd.Series:
    return series.isin(cats)


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

    mover_frames: list[pd.DataFrame] = []
    plotted: dict[str, pd.DataFrame] = {}
    n_net: dict[str, int] = {}
    n_in: dict[str, int] = {}
    n_out: dict[str, int] = {}

    for group_id, cats, _label in GROUPS:
        was = in_group(df["category_k500"], cats)
        now = in_group(df["category_k1000"], cats)
        entrants = df[now & ~was].copy()
        leavers = df[was & ~now].copy()
        n_in[group_id] = len(entrants)
        n_out[group_id] = len(leavers)
        n_net[group_id] = int(now.sum()) - int(was.sum())
        if n_net[group_id] >= 0:
            sub = entrants
            sub["move"] = "entrant"
        else:
            sub = leavers
            sub["move"] = "leaver"
        sub["target_group"] = group_id
        plotted[group_id] = sub
        if not sub.empty:
            mover_frames.append(sub)

    movers = (
        pd.concat(mover_frames, ignore_index=True)
        if mover_frames
        else pd.DataFrame()
    )
    if not movers.empty:
        movers = movers.sort_values(
            ["target_group", "ratio_k1000"], ascending=[True, False]
        )
    movers.to_csv(OUT_CSV, index=False)

    md_lines = [
        "# Epoch 644 — viability-group movers ($k=500 \\to k=1000$)\n\n",
        "Active pools only. Tick-label $n$ is net group-size change. "
        "Boxes are entrants if $n\\ge 0$, leavers if $n<0$.\n",
    ]
    for group_id, _cats, label in GROUPS:
        label_flat = label.replace("\n", " ")
        md_lines.append(
            f"\n## {label_flat} — net $n={n_net[group_id]:+d}$ "
            f"(in {n_in[group_id]}, out {n_out[group_id]})\n"
        )
        sub = plotted[group_id]
        if sub.empty:
            md_lines.append("_No movers plotted._\n")
            continue
        md_lines.append(
            "| Ticker | Pool ID | $r$ ($k=500$) | $r$ ($k=1000$) | "
            "From | To | Stake (M ADA) | Move |\n"
            "|:---|:---|---:|---:|:---|:---|---:|:---|\n"
        )
        for _, row in sub.iterrows():
            ticker = row["pool_ticker"] if pd.notna(row["pool_ticker"]) else "—"
            md_lines.append(
                f"| {ticker} | `{row['pool_id']}` | "
                f"{row['ratio_k500']:.3f} | {row['ratio_k1000']:.3f} | "
                f"{row['category_k500']} | {row['category_k1000']} | "
                f"{row['sigma_ada']/1e6:.2f} | {row['move']} |\n"
            )
    OUT_MD.write_text("".join(md_lines))

    trait_groups = [
        (label, plotted[group_id], color)
        for (group_id, _cats, label), color in zip(GROUPS, GROUP_COLORS)
    ]
    labels_with_n = [
        f"{label}\n(n={n_net[group_id]})"
        for (group_id, _cats, label) in GROUPS
    ]

    fig, axes = plt.subplots(3, 3, figsize=(16.0, 9.8), constrained_layout=True)

    def series_by_group(col: str, transform=None) -> list[np.ndarray]:
        out: list[np.ndarray] = []
        for _label, sub, _color in trait_groups:
            if sub.empty:
                out.append(np.array([np.nan]))
                continue
            vals = sub[col].astype(float)
            if transform is not None:
                vals = transform(vals)
            arr = vals.dropna().to_numpy()
            out.append(arr if len(arr) else np.array([np.nan]))
        return out

    def box_groups(
        ax, data: list[np.ndarray], ylabel: str, title: str, *, log_y: bool = False
    ) -> None:
        plot_data = data
        if log_y:
            plot_data = [np.clip(np.nan_to_num(v, nan=1e-3), 1e-3, None) for v in data]
        bp = ax.boxplot(
            plot_data,
            tick_labels=labels_with_n,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        )
        for patch, color in zip(bp["boxes"], GROUP_COLORS):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        if log_y:
            ax.set_yscale("log")
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE - 2)

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
        log_y=True,
    )
    box_groups(
        axes[0, 2],
        series_by_group("declared_pledge_ada", lambda s: s / 1e3),
        "Declared pledge (k ADA)",
        "Declared pledge",
        log_y=True,
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
    note_lines = ["Net change $n$ ($k=500\\to k=1000$):"]
    for group_id, _cats, label in GROUPS:
        lab = label.replace("\n", " ")
        note_lines.append(
            f"• {lab}: $n={n_net[group_id]}$ "
            f"(in {n_in[group_id]}, out {n_out[group_id]})"
        )
    note_lines.append("Boxes: entrants if $n\\geq 0$, leavers if $n<0$.")
    axes[2, 1].text(
        0.0,
        0.95,
        "\n".join(note_lines),
        ha="left",
        va="top",
        fontsize=FONT_SIZE - 1,
    )

    fig.suptitle(
        "Epoch 644 — characteristics of pools moving across viability groups\n"
        rf"($k=500 \to k=1000$, $C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; "
        "Active pools only)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)

    print(
        "net n: "
        + ", ".join(f"{gid}={n_net[gid]}" for gid, *_ in GROUPS)
    )
    print(
        "in/out: "
        + ", ".join(
            f"{gid}=+{n_in[gid]}/-{n_out[gid]}" for gid, *_ in GROUPS
        )
    )
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
