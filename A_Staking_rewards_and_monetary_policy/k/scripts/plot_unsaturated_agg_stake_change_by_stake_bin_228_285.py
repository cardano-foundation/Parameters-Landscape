#!/usr/bin/env python3
"""
Aggregate stake change (228→285) among pools unsaturated under k=500 at epoch 228,
by epoch-228 stake bins — same layout as the pool-count plot, but y-axis is
sum of Δstake within gain / lose / flat groups.

Bins: 0–15, 15–30, 30–45, 45–60, >60 (M ADA).
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
OUT = DIR / "unsaturated_agg_stake_change_by_stake_bin_228_285.png"
OUT_CSV = DIR / "unsaturated_agg_stake_change_by_stake_bin_228_285.csv"
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12
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


def fmt_m(x: float) -> str:
    """Format ADA change as M ADA for bar labels."""
    if abs(x) < 1e-9:
        return "0"
    return f"{x / 1e6:+.1f}"


def main() -> None:
    T = fetch_T_ada(E0)
    z0 = T / K_POST
    a = load_epoch(E0)
    b = load_epoch(E1)

    unsat = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)].index
    common = unsat.intersection(b.index)
    sa = a.loc[common, "stake_ada"]
    sb = b.loc[common, "stake_ada"]
    d = sb - sa  # ADA

    stake_m = sa / 1e6
    labels = [lab for _, _, lab in BINS]
    rows = []
    gain_agg, lose_agg, flat_agg, ns = [], [], [], []
    for lo, hi, lab in BINS:
        mask = (stake_m >= lo) & (stake_m < hi)
        n = int(mask.sum())
        g_mask = mask & (d > 0)
        l_mask = mask & (d < 0)
        f_mask = mask & (d == 0)
        g_sum = float(d[g_mask].sum()) if g_mask.any() else 0.0
        l_sum = float(d[l_mask].sum()) if l_mask.any() else 0.0
        f_sum = float(d[f_mask].sum()) if f_mask.any() else 0.0
        gain_agg.append(g_sum)
        lose_agg.append(l_sum)
        flat_agg.append(f_sum)
        ns.append(n)
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": n,
                "n_gain": int(g_mask.sum()),
                "n_lose": int(l_mask.sum()),
                "n_flat": int(f_mask.sum()),
                "agg_dstake_gain_ADA": g_sum,
                "agg_dstake_lose_ADA": l_sum,
                "agg_dstake_flat_ADA": f_sum,
                "agg_dstake_net_ADA": g_sum + l_sum + f_sum,
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    # Plot in M ADA for readability
    gain_m = [v / 1e6 for v in gain_agg]
    lose_m = [v / 1e6 for v in lose_agg]
    flat_m = [v / 1e6 for v in flat_agg]

    x = np.arange(len(labels))
    width = 0.26
    fig, ax = plt.subplots(figsize=(11.0, 5.6), constrained_layout=True)
    b1 = ax.bar(x - width, gain_m, width, color=COLOR_GAIN, label="gainers (Σ Δσ)")
    b2 = ax.bar(x, lose_m, width, color=COLOR_LOSE, label="losers (Σ Δσ)")
    b3 = ax.bar(x + width, flat_m, width, color=COLOR_FLAT, label="flat (Σ Δσ)")
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE)
    ax.set_xlabel("Epoch-228 stake bin (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel("Aggregate stake change (M ADA)", fontsize=FONT_SIZE)
    ax.set_title(
        f"Aggregate Δstake 228→285 among pools unsaturated under $k={K_POST}$ at epoch 228\n"
        f"(n={len(common)} continuing; $z_0={z0/1e6:.1f}$ M ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False, loc="best")
    ax.grid(axis="y", alpha=0.25)

    all_m = gain_m + lose_m + flat_m
    span = max(abs(v) for v in all_m) if all_m else 1.0
    y_lo = min(all_m) - span * 0.06
    y_hi = max(all_m) + span * 0.10
    ax.set_ylim(y_lo, y_hi)

    pad = span * 0.025
    for bars, vals_ada in ((b1, gain_agg), (b2, lose_agg), (b3, flat_agg)):
        for bar, v_ada in zip(bars, vals_ada):
            if abs(v_ada) < 1.0 and abs(bar.get_height()) < 1e-9:
                continue
            h = bar.get_height()
            xc = bar.get_x() + bar.get_width() / 2
            if h >= 0:
                ax.text(
                    xc,
                    h + pad,
                    fmt_m(v_ada),
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 2,
                    color="0.15",
                )
            else:
                # Place beside the bar tip (right) — avoids xtick overlap for tall
                # negative bars and works for short ones too.
                ax.text(
                    bar.get_x() + bar.get_width() + 0.03,
                    h,
                    fmt_m(v_ada),
                    ha="left",
                    va="center",
                    fontsize=FONT_SIZE - 2,
                    color=COLOR_LOSE,
                )

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    for r in rows:
        print(
            f"  {r['stake_bin_M_ADA']}: gain={r['agg_dstake_gain_ADA']/1e6:+.1f}M "
            f"lose={r['agg_dstake_lose_ADA']/1e6:+.1f}M "
            f"net={r['agg_dstake_net_ADA']/1e6:+.1f}M"
        )


if __name__ == "__main__":
    main()
