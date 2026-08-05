#!/usr/bin/env python3
"""
Delegation gain/loss/exit among pools unsaturated under k=500 at epoch 228,
by epoch-228 stake bins (M ADA).

Includes pools that exited by epoch 285 (separate "exited" bar).
Continuing pools: gain / lose / flat stake vs 285.
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
OUT = DIR / "unsaturated_delegation_by_stake_bin_228_285.png"
OUT_CSV = DIR / "unsaturated_delegation_by_stake_bin_228_285.csv"
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
COLOR_EXIT = "#7c3aed"
KOIOS = "https://api.koios.rest/api/v1"
TOKEN_PATH = DIR / ".koios_api_token"

BINS = [
    (0.0, 15.0, "0–15"),
    (15.0, 30.0, "15–30"),
    (30.0, 45.0, "30–45"),
    (45.0, 60.0, "45–60"),
    (60.0, np.inf, ">60"),
]


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
        }
    ).set_index("pool_id")


def main() -> None:
    T = fetch_T_ada(E0)
    z0 = T / K_POST
    a = load_epoch(E0)
    b = load_epoch(E1)

    unsat = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    continuing = unsat.intersection(b.index)
    exited = unsat.difference(b.index)

    sa_c = a.loc[continuing, "stake_ada"]
    sb_c = b.loc[continuing, "stake_ada"]
    d_c = sb_c - sa_c
    sa_x = a.loc[exited, "stake_ada"]

    stake_m_c = sa_c / 1e6
    stake_m_x = sa_x / 1e6
    labels = [lab for _, _, lab in BINS]
    rows = []
    gain_vals, lose_vals, flat_vals, exit_vals, ns = [], [], [], [], []
    for lo, hi, lab in BINS:
        mask_c = (stake_m_c >= lo) & (stake_m_c < hi)
        mask_x = (stake_m_x >= lo) & (stake_m_x < hi)
        g = int((d_c[mask_c] > 0).sum())
        l = int((d_c[mask_c] < 0).sum())
        f = int((d_c[mask_c] == 0).sum())
        x = int(mask_x.sum())
        n = g + l + f + x
        gain_vals.append(g)
        lose_vals.append(l)
        flat_vals.append(f)
        exit_vals.append(x)
        ns.append(n)
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": n,
                "n_continuing": int(mask_c.sum()),
                "gain_delegation": g,
                "lose_delegation": l,
                "flat_delegation": f,
                "exited": x,
                "median_dstake_continuing_ADA": (
                    float(d_c[mask_c].median()) if mask_c.any() else float("nan")
                ),
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x = np.arange(len(labels))
    width = 0.2
    fig, ax = plt.subplots(figsize=(11.5, 5.4), constrained_layout=True)
    offs = (-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width)
    series = [
        (offs[0], gain_vals, COLOR_GAIN, "gain stake"),
        (offs[1], lose_vals, COLOR_LOSE, "lose stake"),
        (offs[2], flat_vals, COLOR_FLAT, "flat stake"),
        (offs[3], exit_vals, COLOR_EXIT, "exited by 285"),
    ]
    bar_artists = []
    for off, vals, col, lab in series:
        bar_artists.append(ax.bar(x + off, vals, width, color=col, label=lab))

    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE)
    ax.set_xlabel("Epoch-228 stake bin (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        f"Delegation outcomes 228→285 among pools unsaturated under $k={K_POST}$ at epoch 228\n"
        f"(n={len(unsat)} unsaturated; {len(continuing)} continuing, {len(exited)} exited; "
        f"$z_0={z0/1e6:.1f}$ M ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(gain_vals + lose_vals + flat_vals + exit_vals + [1])
    for bars in bar_artists:
        for bar in bars:
            v = int(bar.get_height())
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    v + ymax * 0.02,
                    str(v),
                    ha="center",
                    fontsize=FONT_SIZE - 3,
                )

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    print(
        {
            "z0_M": z0 / 1e6,
            "n_unsat": len(unsat),
            "n_continuing": len(continuing),
            "n_exited": len(exited),
            "rows": rows,
        }
    )


if __name__ == "__main__":
    main()
