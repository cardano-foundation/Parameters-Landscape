#!/usr/bin/env python3
"""
Delegation gain/loss among pools that were unsaturated under k=500 at epoch 228,
comparing stake 228→285, by epoch-228 stake bins (M ADA).

Bins: 0–15, 15–30, 30–45, 45–60, >60.
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
FONT_SIZE = 11
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
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


def bin_label(stake_m: float) -> str:
    for lo, hi, lab in BINS:
        if lo <= stake_m < hi:
            return lab
    return BINS[-1][2]


def main() -> None:
    T = fetch_T_ada(E0)
    z0 = T / K_POST
    a = load_epoch(E0)
    b = load_epoch(E1)

    # Unsaturated after k increment (under new k=500), with positive stake at 228
    unsat = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    common = unsat.intersection(b.index)
    sa = a.loc[common, "stake_ada"]
    sb = b.loc[common, "stake_ada"]
    d = sb - sa

    stake_m = sa / 1e6  # M ADA
    labels = [lab for _, _, lab in BINS]
    rows = []
    gain_vals, lose_vals, flat_vals, ns = [], [], [], []
    for lo, hi, lab in BINS:
        mask = (stake_m >= lo) & (stake_m < hi)
        n = int(mask.sum())
        g = int((d[mask] > 0).sum())
        l = int((d[mask] < 0).sum())
        f = int((d[mask] == 0).sum())
        gain_vals.append(g)
        lose_vals.append(l)
        flat_vals.append(f)
        ns.append(n)
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": n,
                "gain_delegation": g,
                "lose_delegation": l,
                "flat_delegation": f,
                "median_dstake_ADA": float(d[mask].median()) if n else float("nan"),
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x = np.arange(len(labels))
    width = 0.26
    fig, ax = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    b1 = ax.bar(x - width, gain_vals, width, color=COLOR_GAIN, label="gain stake")
    b2 = ax.bar(x, lose_vals, width, color=COLOR_LOSE, label="lose stake")
    b3 = ax.bar(x + width, flat_vals, width, color=COLOR_FLAT, label="flat stake")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE)
    ax.set_xlabel("Epoch-228 stake bin (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        f"Delegation outcomes 228→285 among pools unsaturated under $k={K_POST}$ at epoch 228\n"
        f"(n={len(common)} continuing; $z_0={z0/1e6:.1f}$ M ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(gain_vals + lose_vals + flat_vals + [1])
    for bars in (b1, b2, b3):
        for bar in bars:
            v = int(bar.get_height())
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    v + ymax * 0.02,
                    str(v),
                    ha="center",
                    fontsize=8,
                )

    fig.savefig(OUT, dpi=160)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    print({"z0_M": z0 / 1e6, "n_unsat_continuing": len(common), "rows": rows})


if __name__ == "__main__":
    main()
