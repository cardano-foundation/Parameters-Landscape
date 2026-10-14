#!/usr/bin/env python3
"""
Among fixed-cost reducers that gained stake (426→500), aggregate Δσ by
initial stake bin (epoch 426).

Reports absolute ADA gained and shares of continuing-Active stake at 426 and 500.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pastreduction_common import load_active

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "cost_reducer_gainer_agg_stake_by_bin_426_500.png"
OUT_CSV = DIR / "cost_reducer_gainer_agg_stake_by_bin_426_500.csv"

E0 = 426
E1 = 500
FONT_SIZE = 11
COLOR_ABS = "#2f5d85"
COLOR_S0 = "#2a9d8f"
COLOR_S1 = "#e76f51"

# Initial stake at epoch 426, in millions of ADA
BINS = [
    (0.0, 1.0, "0–1"),
    (1.0, 5.0, "1–5"),
    (5.0, 15.0, "5–15"),
    (15.0, 30.0, "15–30"),
    (30.0, np.inf, "≥30"),
]


def load_epoch(epoch: int) -> pd.DataFrame:
    df = load_active(epoch)
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake_ada": pd.to_numeric(df["active_stake"], errors="coerce") / 1e6,
            "fixed_cost": pd.to_numeric(
                df["pool_update.active.fixed_cost"], errors="coerce"
            ),
        }
    ).set_index("pool_id")


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)
    common = a.index.intersection(b.index)

    fa = a.loc[common, "fixed_cost"]
    fb = b.loc[common, "fixed_cost"]
    sa = a.loc[common, "stake_ada"]
    sb = b.loc[common, "stake_ada"]

    gainers = (fb < fa) & (sb > sa)
    sa_g = sa[gainers]
    d_g = sb[gainers] - sa_g  # ADA

    # Totals over continuing pools (same universe as the rest of this folder)
    T0 = float(sa.sum())
    T1 = float(sb.sum())
    total_gain = float(d_g.sum())

    rows = []
    for lo, hi, lab in BINS:
        mask = (sa_g / 1e6 >= lo) & (sa_g / 1e6 < hi) if np.isfinite(hi) else (
            sa_g / 1e6 >= lo
        )
        n = int(mask.sum())
        gain = float(d_g[mask].sum()) if n else 0.0
        rows.append(
            {
                "bin_m_ada": lab,
                "bin_lo_m": lo,
                "bin_hi_m": hi if np.isfinite(hi) else None,
                "n_pools": n,
                "sum_delta_stake_ada": gain,
                "sum_delta_stake_m_ada": gain / 1e6,
                "share_of_total_stake_426_pct": 100.0 * gain / T0 if T0 else np.nan,
                "share_of_total_stake_500_pct": 100.0 * gain / T1 if T1 else np.nan,
                "share_of_gainer_total_gain_pct": (
                    100.0 * gain / total_gain if total_gain else np.nan
                ),
            }
        )

    tab = pd.DataFrame(rows)
    tab.to_csv(OUT_CSV, index=False)

    labels = tab["bin_m_ada"].tolist()
    x = np.arange(len(labels))
    abs_m = tab["sum_delta_stake_m_ada"].to_numpy()
    sh0 = tab["share_of_total_stake_426_pct"].to_numpy()
    sh1 = tab["share_of_total_stake_500_pct"].to_numpy()
    ns = tab["n_pools"].to_numpy()

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6), constrained_layout=True)

    ax = axes[0]
    bars = ax.bar(x, abs_m, color=COLOR_ABS, width=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE)
    ax.set_xlabel(r"Initial stake bin at epoch 426 (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$\sum\Delta\sigma_i$ (M ADA)", fontsize=FONT_SIZE)
    ax.set_title("Absolute stake gained", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    for bar, v, n in zip(bars, abs_m, ns):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + max(abs_m) * 0.02,
            f"{v:.0f}\n(n={n})",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax = axes[1]
    w = 0.38
    ax.bar(x - w / 2, sh0, width=w, color=COLOR_S0, label=f"share of total stake @ {E0}")
    ax.bar(x + w / 2, sh1, width=w, color=COLOR_S1, label=f"share of total stake @ {E1}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE)
    ax.set_xlabel(r"Initial stake bin at epoch 426 (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$\sum\Delta\sigma_i$ / total stake (%)", fontsize=FONT_SIZE)
    ax.set_title("Gain as share of system stake", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.legend(fontsize=9, frameon=False, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    for i, (v0, v1) in enumerate(zip(sh0, sh1)):
        ax.text(i - w / 2, v0 + 0.05, f"{v0:.2f}", ha="center", va="bottom", fontsize=7)
        ax.text(i + w / 2, v1 + 0.05, f"{v1:.2f}", ha="center", va="bottom", fontsize=7)

    fig.suptitle(
        f"Cost-reducer gainers ({E0}→{E1}, Active): aggregate stake gained by initial size\n"
        f"n={int(gainers.sum())} pools; "
        f"total $\\sum\\Delta\\sigma$={total_gain/1e6:.0f} M ADA "
        f"({100*total_gain/T0:.2f}% of stake@{E0}, "
        f"{100*total_gain/T1:.2f}% of stake@{E1})",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_CSV}")
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
