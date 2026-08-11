#!/usr/bin/env python3
"""
Boxplots of pool characteristics by delegation outcome (gain / lose / flat / exit)
among pools unsaturated under k=500 at epoch 228.

Characteristics are from the epoch-228 snapshot (initial values).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

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
KOIOS = "https://api.koios.rest/api/v1"
TOKEN_PATH = DIR / ".koios_api_token"


def fetch_T_ada(epoch: int) -> float:
    headers = {"accept": "application/json"}
    if TOKEN_PATH.exists():
        tok = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    r = requests.get(
        f"{KOIOS}/totals", params={"_epoch_no": epoch}, headers=headers, timeout=60
    )
    r.raise_for_status()
    return float(r.json()[0]["supply"]) / 1e6


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
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake_ada": stake,
            "declared_pledge_ada": declared_pledge,
            "active_pledge_ada": active_pledge,
            "margin": margin,
            "fixed_cost_ada": fixed_cost,
            "delegators": delegators,
        }
    ).set_index("pool_id")


def main() -> None:
    T = fetch_T_ada(E0)
    z0 = T / K_POST

    a = load_epoch(E0)
    b_stake = load_epoch(E1)[["stake_ada"]]

    unsat = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    continuing = unsat.intersection(b_stake.index)
    exited = unsat.difference(b_stake.index)

    d = b_stake.loc[continuing, "stake_ada"] - a.loc[continuing, "stake_ada"]

    gain_idx = d[d > 0].index
    lose_idx = d[d < 0].index
    flat_idx = d[d == 0].index
    exit_idx = exited

    groups = [
        (f"Gain\n($n={len(gain_idx)}$)", a.loc[gain_idx], COLOR_GAIN),
        (f"Lose\n($n={len(lose_idx)}$)", a.loc[lose_idx], COLOR_LOSE),
        (f"Flat\n($n={len(flat_idx)}$)", a.loc[flat_idx], COLOR_FLAT),
        (f"Exit\n($n={len(exit_idx)}$)", a.loc[exit_idx], COLOR_EXIT),
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
        # Annotate medians
        for i, arr in enumerate(data_lists, start=1):
            if arr.size == 0:
                continue
            med = float(np.median(arr))
            q1, q3 = np.percentile(arr, [25.0, 75.0])
            iqr = q3 - q1
            top = float(min(arr.max(), q3 + 1.5 * iqr))
            ylim = ax.get_ylim()
            span = ylim[1] - ylim[0] if ylim[1] > ylim[0] else 1.0
            y_text = top + 0.04 * span
            fmt = "{:.1f}" if col != "fixed_cost_ada" else "{:.0f}"
            ax.text(
                i,
                y_text,
                fmt.format(med),
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
                color=MEDIAN_COLOR,
            )
        # Expand ylim to fit text
        cur_ylim = ax.get_ylim()
        ax.set_ylim(cur_ylim[0], cur_ylim[1] * 1.15 if cur_ylim[1] > 0 else cur_ylim[1])

    fig.suptitle(
        "Epoch 228 — characteristics of pools by delegation outcome (228→285)\n"
        rf"(unsaturated under $k={K_POST}$, $z_0={z0/1e6:.1f}$M ADA; "
        f"$n={len(unsat)}$ pools). Numbers above boxes are medians.",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT, dpi=160)
    plt.close(fig)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
