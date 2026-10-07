#!/usr/bin/env python3
"""
Boxplots of pool characteristics by delegation outcome (gain / lose / flat / exit)
among Active pools unsaturated under k=500 at epoch 228.

Active = not (σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs).
Exited = Active-unsaturated at 228 but not Active at 285.
Characteristics are from the epoch-228 snapshot (initial values).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "unsaturated_characteristics_by_outcome_228_285.png"
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
COLOR_EXIT = "#7c3aed"
MEDIAN_COLOR = "#111111"
T_228_ADA = 32.03687470708404e9


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    ).fillna(0.0) / 1e6
    declared_pledge = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0)
        / 1e6
    )
    active_pledge = (
        pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    fixed_cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0)
        / 1e6
    )
    delegators = pd.to_numeric(
        df["epochs.0.data.delegators"].fillna(df["delegators"]), errors="coerce"
    )
    flags = pd.read_csv(DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv")
    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake_ada": stake,
            "declared_pledge_ada": declared_pledge,
            "active_pledge_ada": active_pledge,
            "margin": margin,
            "fixed_cost_ada": fixed_cost,
            "delegators": delegators,
        }
    )
    out = out.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    out["active"] = out["in_union"] == 0
    return out.set_index("pool_id")


def main() -> None:
    z0 = T_228_ADA / K_POST

    a = load_epoch(E0)
    b = load_epoch(E1)
    active_285 = b.index[b["active"]]

    unsat = a[(a["active"]) & (a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    continuing = unsat.intersection(active_285)
    exited = unsat.difference(active_285)

    d = b.loc[continuing, "stake_ada"] - a.loc[continuing, "stake_ada"]

    gain_idx = d[d > 0].index
    lose_idx = d[d < 0].index
    flat_idx = d[d == 0].index
    exit_idx = exited

    groups = [
        (name, df_g, color)
        for name, df_g, color in [
            (f"Gain\n($n={len(gain_idx)}$)", a.loc[gain_idx], COLOR_GAIN),
            (f"Lose\n($n={len(lose_idx)}$)", a.loc[lose_idx], COLOR_LOSE),
            (f"Flat\n($n={len(flat_idx)}$)", a.loc[flat_idx], COLOR_FLAT),
            (f"Exit\n($n={len(exit_idx)}$)", a.loc[exit_idx], COLOR_EXIT),
        ]
        if len(df_g) > 0
    ]

    panels = [
        ("stake_ada", 1e6, "Epoch stake (M ADA)", "Delegation (epoch 228)"),
        ("declared_pledge_ada", 1e3, "Declared pledge (k ADA)", "Declared pledge"),
        ("active_pledge_ada", 1e3, "Active pledge (k ADA)", "Active pledge"),
        ("margin", 0.01, "Margin (%)", "Margin"),
        ("fixed_cost_ada", 1.0, "Fixed cost (ADA)", "Declared fixed cost"),
        ("delegators", 1.0, "Delegators", "Delegators"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.5), constrained_layout=True)
    axes_flat = axes.flatten()

    for idx, (col, scale, ylabel, title) in enumerate(panels):
        ax = axes_flat[idx]
        data_lists = []
        labels = []
        for name, df_g, _ in groups:
            s = df_g[col].dropna()
            if col == "margin":
                s = s * 100.0
            elif scale != 1.0 and col != "margin":
                s = s / scale
            data_lists.append(s.to_numpy())
            labels.append(name)
        box = ax.boxplot(
            data_lists,
            tick_labels=labels,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        )
        for patch, (_, _, color) in zip(box["boxes"], groups):
            patch.set_facecolor(color)
            patch.set_alpha(0.70)
            patch.set_edgecolor("0.2")
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE - 1)
        medians: list[float] = []
        tops: list[float] = []
        for i, arr in enumerate(data_lists):
            medians.append(float(np.median(arr)) if arr.size else float("nan"))
            cap = box["caps"][2 * i + 1]
            tops.append(float(np.max(cap.get_ydata())))
        y0, y1_auto = ax.get_ylim()
        if col == "margin":
            ax.set_ylim(0.0, 6.0)
        else:
            ax.set_ylim(y0, y1_auto + 0.22 * (y1_auto - y0))
        y0, y1 = ax.get_ylim()
        span = y1 - y0 if y1 > y0 else 1.0
        pad = 0.03 * span
        y_labels = [top + pad for top in tops]
        names = [name for name, _, _ in groups]
        if col == "margin":
            gain_i = next(i for i, n in enumerate(names) if n.startswith("Gain"))
            lose_i = next(i for i, n in enumerate(names) if n.startswith("Lose"))
            y_labels[lose_i] = y_labels[gain_i]
        fmt = "{:.1f}" if col != "fixed_cost_ada" else "{:.0f}"
        for i, med in enumerate(medians, start=1):
            if not np.isfinite(med):
                continue
            ax.text(
                i,
                y_labels[i - 1],
                fmt.format(med),
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
                color=MEDIAN_COLOR,
                clip_on=True,
            )

    fig.suptitle(
        "Epoch 228 — characteristics of Active pools by delegation outcome (228→285)\n"
        rf"(Active, unsaturated under $k={K_POST}$, $z_0={z0/1e6:.1f}$M ADA; "
        f"$n={len(unsat)}$ pools). Numbers above boxes are medians.",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT, dpi=160)
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
