#!/usr/bin/env python3
"""
Margin / fixed-cost strategy changes among pools unsaturated under k=500 at
epoch 228, and stake outcomes 228→285 by strategy.

Produces multiple panels from one script.
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
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12  # match heatmap / theory plots in Cardano-Parameters-Landscape
COLOR_DOWN = "#2a9d8f"
COLOR_UP = "#e76f51"
COLOR_SAME = "#9ca3af"
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
KOIOS = "https://api.koios.rest/api/v1"
TOKEN_PATH = DIR / ".koios_api_token"

OUT_COUNTS = DIR / "unsaturated_mi_ci_change_counts_228_285.png"
OUT_STRAT = DIR / "unsaturated_strategy_stake_outcomes_228_285.png"
OUT_CSV = DIR / "unsaturated_mi_ci_strategies_228_285.csv"


def fetch_T_ada(epoch: int) -> float:
    headers = {"accept": "application/json"}
    if TOKEN_PATH.exists():
        tok = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
    r = requests.get(f"{KOIOS}/totals", params={"_epoch_no": epoch}, headers=headers, timeout=60)
    r.raise_for_status()
    return float(r.json()[0]["supply"]) / 1e6


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    stake_lov = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    )
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake_ada": stake_lov.fillna(0.0) / 1e6,
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
            "fixed_cost": pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce"),
        }
    ).set_index("pool_id")


def dir_label(delta: pd.Series, name: str) -> pd.Series:
    out = pd.Series("same", index=delta.index, dtype=object)
    out[delta < 0] = f"{name}↓"
    out[delta > 0] = f"{name}↑"
    out[delta == 0] = f"{name}="
    return out


def stake_outcome_counts(mask: pd.Series, d_stake: pd.Series) -> tuple[int, list[int]]:
    n = int(mask.sum())
    vals = [
        int((d_stake[mask] > 0).sum()),
        int((d_stake[mask] < 0).sum()),
        int((d_stake[mask] == 0).sum()),
    ]
    return n, vals


def annotate_bars(ax, bars, ymax: float, *, fontsize: float | None = None) -> None:
    fs = FONT_SIZE if fontsize is None else fontsize
    for bar in bars:
        v = int(bar.get_height())
        if v > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + ymax * 0.02,
                str(v),
                ha="center",
                fontsize=fs,
            )


def main() -> None:
    T = fetch_T_ada(E0)
    z0 = T / K_POST
    a = load_epoch(E0)
    b = load_epoch(E1)

    unsat = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    common = unsat.intersection(b.index)
    aa = a.loc[common]
    bb = b.loc[common]

    # Drop rows missing fee params in either epoch
    ok = aa["margin"].notna() & bb["margin"].notna() & aa["fixed_cost"].notna() & bb["fixed_cost"].notna()
    aa, bb = aa.loc[ok], bb.loc[ok]
    d_stake = bb["stake_ada"] - aa["stake_ada"]
    dm = bb["margin"] - aa["margin"]
    dc = bb["fixed_cost"] - aa["fixed_cost"]

    m_down, m_up, m_same = dm < 0, dm > 0, dm == 0
    c_down, c_up, c_same = dc < 0, dc > 0, dc == 0
    both_change = (dm != 0) & (dc != 0)
    only_m = (dm != 0) & (dc == 0)
    only_c = (dm == 0) & (dc != 0)
    neither = (dm == 0) & (dc == 0)

    # Strategy labels for stake-outcome panels
    strategies = [
        ("m↓ only", m_down & c_same),
        ("c↓ only", c_down & m_same),
        ("m↓ & c↓", m_down & c_down),
        ("no change", neither),
        ("m↑ only", m_up & c_same),
        ("c↑ only", c_up & m_same),
        ("m↑ & c↑", m_up & c_up),
        ("m↓ & c↑", m_down & c_up),
        ("m↑ & c↓", m_up & c_down),
    ]

    rows = []
    for name, mask in [
        ("margin↓", m_down),
        ("margin↑", m_up),
        ("margin=", m_same),
        ("cost↓", c_down),
        ("cost↑", c_up),
        ("cost=", c_same),
        ("only margin changes", only_m),
        ("only cost changes", only_c),
        ("both change", both_change),
        ("neither changes", neither),
        *strategies,
    ]:
        n, vals = stake_outcome_counts(mask, d_stake)
        rows.append(
            {
                "group": name,
                "n": n,
                "gain_stake": vals[0],
                "lose_stake": vals[1],
                "flat_stake": vals[2],
            }
        )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    # --- Figure 1: change counts for m_i and c_i ---
    fig1, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), constrained_layout=True)

    ax = axes[0]
    vals = [int(m_down.sum()), int(m_up.sum()), int(m_same.sum())]
    bars = ax.bar(["margin ↓", "margin ↑", "same"], vals, color=[COLOR_DOWN, COLOR_UP, COLOR_SAME])
    ax.set_ylabel("Pools", fontsize=FONT_SIZE)
    ax.set_title("Margin $m_i$ changes", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    annotate_bars(ax, bars, max(vals + [1]))

    ax = axes[1]
    vals = [int(c_down.sum()), int(c_up.sum()), int(c_same.sum())]
    bars = ax.bar(["cost ↓", "cost ↑", "same"], vals, color=[COLOR_DOWN, COLOR_UP, COLOR_SAME])
    ax.set_ylabel("Pools", fontsize=FONT_SIZE)
    ax.set_title("Fixed cost $c_i$ changes", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    annotate_bars(ax, bars, max(vals + [1]))

    ax = axes[2]
    vals = [int(only_m.sum()), int(only_c.sum()), int(both_change.sum()), int(neither.sum())]
    bars = ax.bar(
        ["only $m_i$", "only $c_i$", "both", "neither"],
        vals,
        color=[COLOR_DOWN, COLOR_UP, "#264653", COLOR_SAME],
    )
    ax.set_ylabel("Pools", fontsize=FONT_SIZE)
    ax.set_title("Which levers moved", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    annotate_bars(ax, bars, max(vals + [1]))

    fig1.suptitle(
        f"Fee-parameter changes 228→285 among unsaturated pools under $k={K_POST}$ at 228 "
        f"(n={len(aa)})",
        fontsize=FONT_SIZE,
    )
    fig1.savefig(OUT_COUNTS, dpi=160)
    print(f"Wrote {OUT_COUNTS}")

    # --- Figure 2: stake outcomes by strategy ---
    # Keep panels with n>0; arrange in a grid; shared y-scale across panels
    active_strats = [(name, mask) for name, mask in strategies if int(mask.sum()) > 0]
    panel_vals = [stake_outcome_counts(mask, d_stake) for _, mask in active_strats]
    y_max = max((max(vals) for _, vals in panel_vals), default=1)
    y_top = y_max * 1.18

    ncols = 3
    nrows = int(np.ceil(len(active_strats) / ncols))
    fig2, axes2 = plt.subplots(
        nrows, ncols, figsize=(15.0, 4.6 * nrows), constrained_layout=True
    )
    axes_flat = np.atleast_1d(axes2).ravel()
    for ax in axes_flat:
        ax.set_visible(False)

    for ax, (name, mask), (n, vals) in zip(axes_flat, active_strats, panel_vals):
        ax.set_visible(True)
        labels = ["gain stake", "lose stake", "flat stake"]
        cols = [COLOR_GAIN, COLOR_LOSE, COLOR_FLAT]
        x = np.arange(len(labels))
        bars = ax.bar(x, vals, color=cols)
        ax.set_xticks(x)
        # Slightly larger than heatmap base (12): each panel is smaller in a 3x3 grid
        panel_fs = FONT_SIZE + 2
        ax.set_xticklabels(labels, fontsize=panel_fs, rotation=15, ha="right")
        ax.set_ylabel("Pools", fontsize=panel_fs)
        ax.set_title(f"{name}\n(n={n})", fontsize=panel_fs)
        ax.tick_params(labelsize=panel_fs)
        ax.set_ylim(0, y_top)
        ax.grid(axis="y", alpha=0.25)
        annotate_bars(ax, bars, y_max, fontsize=panel_fs)

    fig2.suptitle(
        f"Stake outcomes by fee strategy, unsaturated under $k={K_POST}$ at 228 (228→285)",
        fontsize=FONT_SIZE + 3,
    )
    fig2.savefig(OUT_STRAT, dpi=300)
    print(f"Wrote {OUT_STRAT}")
    print(f"Wrote {OUT_CSV}")
    print({"n": len(aa), "z0_M": z0 / 1e6})


if __name__ == "__main__":
    main()
