#!/usr/bin/env python3
"""
Among fixed-cost reducers (426→500), aggregate Δσ by initial stake bin (epoch 426):
gains, losses, and net = gain + loss per bin.

Companion to cost_reducer_gainer_agg_stake_by_bin_426_500 (gainers only).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "cost_reducer_net_stake_by_bin_426_500.png"
OUT_CSV = DIR / "cost_reducer_net_stake_by_bin_426_500.csv"

E0 = 426
E1 = 500
FONT_SIZE = 11
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_NET = "#2f5d85"
COLOR_S0 = "#2a9d8f"
COLOR_S1 = "#e76f51"

# Same bins as the gainer-only companion plot (M ADA at epoch 426)
BINS = [
    (0.0, 1.0, "0–1"),
    (1.0, 5.0, "1–5"),
    (5.0, 15.0, "5–15"),
    (15.0, 30.0, "15–30"),
    (30.0, np.inf, "≥30"),
]


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
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

    reducers = fb < fa
    sa_r = sa[reducers]
    d_r = sb[reducers] - sa_r  # ADA

    T0 = float(sa.sum())
    T1 = float(sb.sum())

    rows = []
    for lo, hi, lab in BINS:
        stake_m = sa_r / 1e6
        in_bin = (stake_m >= lo) & (stake_m < hi) if np.isfinite(hi) else (stake_m >= lo)
        d_bin = d_r[in_bin]
        g_mask = d_bin > 0
        l_mask = d_bin < 0
        f_mask = d_bin == 0
        gain = float(d_bin[g_mask].sum()) if g_mask.any() else 0.0
        lose = float(d_bin[l_mask].sum()) if l_mask.any() else 0.0
        flat = float(d_bin[f_mask].sum()) if f_mask.any() else 0.0
        net = gain + lose + flat
        rows.append(
            {
                "bin_m_ada": lab,
                "bin_lo_m": lo,
                "bin_hi_m": hi if np.isfinite(hi) else None,
                "n_pools": int(in_bin.sum()),
                "n_gain": int(g_mask.sum()),
                "n_lose": int(l_mask.sum()),
                "n_flat": int(f_mask.sum()),
                "sum_delta_gain_ada": gain,
                "sum_delta_lose_ada": lose,
                "sum_delta_net_ada": net,
                "sum_delta_gain_m_ada": gain / 1e6,
                "sum_delta_lose_m_ada": lose / 1e6,
                "sum_delta_net_m_ada": net / 1e6,
                "net_share_of_total_stake_426_pct": 100.0 * net / T0 if T0 else np.nan,
                "net_share_of_total_stake_500_pct": 100.0 * net / T1 if T1 else np.nan,
            }
        )

    tab = pd.DataFrame(rows)
    tab.to_csv(OUT_CSV, index=False)

    labels = tab["bin_m_ada"].tolist()
    x = np.arange(len(labels))
    gain_m = tab["sum_delta_gain_m_ada"].to_numpy()
    lose_m = tab["sum_delta_lose_m_ada"].to_numpy()
    net_m = tab["sum_delta_net_m_ada"].to_numpy()
    ns = tab["n_pools"].to_numpy()
    n_g = tab["n_gain"].to_numpy()
    n_l = tab["n_lose"].to_numpy()
    sh0 = tab["net_share_of_total_stake_426_pct"].to_numpy()
    sh1 = tab["net_share_of_total_stake_500_pct"].to_numpy()
    total_net = float(tab["sum_delta_net_ada"].sum())

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)

    ax = axes[0]
    w = 0.28
    b_g = ax.bar(x - w, gain_m, width=w, color=COLOR_GAIN, label="gainers (Σ Δσ)")
    b_l = ax.bar(x, lose_m, width=w, color=COLOR_LOSE, label="losers (Σ Δσ)")
    b_n = ax.bar(x + w, net_m, width=w, color=COLOR_NET, label="net (gain+lose)")
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE
    )
    ax.set_xlabel("Initial stake bin at epoch 426 (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$\sum\Delta\sigma_i$ (M ADA)", fontsize=FONT_SIZE)
    ax.set_title("Gain, loss, and net by initial size", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.legend(fontsize=9, frameon=False, loc="best")
    ax.grid(axis="y", alpha=0.25)

    span = max(abs(float(v)) for v in np.concatenate([gain_m, lose_m, net_m])) or 1.0
    pad = span * 0.03
    for bars, vals, counts in (
        (b_g, gain_m, n_g),
        (b_l, lose_m, n_l),
        (b_n, net_m, ns),
    ):
        for bar, v, n in zip(bars, vals, counts):
            h = bar.get_height()
            xc = bar.get_x() + bar.get_width() / 2
            label = f"{v:+.0f}"
            if bars is b_g:
                label = f"{v:+.0f}\n(n={n})"
            elif bars is b_l:
                label = f"{v:+.0f}\n(n={n})"
            if h >= 0:
                ax.text(xc, h + pad, label, ha="center", va="bottom", fontsize=7)
            else:
                ax.text(xc, h - pad, label, ha="center", va="top", fontsize=7)

    ax = axes[1]
    w = 0.38
    ax.bar(x - w / 2, sh0, width=w, color=COLOR_S0, label=f"net / total stake @ {E0}")
    ax.bar(x + w / 2, sh1, width=w, color=COLOR_S1, label=f"net / total stake @ {E1}")
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE)
    ax.set_xlabel("Initial stake bin at epoch 426 (M ADA)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"net $\sum\Delta\sigma_i$ / total stake (%)", fontsize=FONT_SIZE)
    ax.set_title("Net flow as share of system stake", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.legend(fontsize=9, frameon=False, loc="best")
    ax.grid(axis="y", alpha=0.25)
    for i, (v0, v1) in enumerate(zip(sh0, sh1)):
        off0 = 0.04 if v0 >= 0 else -0.04
        off1 = 0.04 if v1 >= 0 else -0.04
        ax.text(
            i - w / 2,
            v0 + off0,
            f"{v0:+.2f}",
            ha="center",
            va="bottom" if v0 >= 0 else "top",
            fontsize=7,
        )
        ax.text(
            i + w / 2,
            v1 + off1,
            f"{v1:+.2f}",
            ha="center",
            va="bottom" if v1 >= 0 else "top",
            fontsize=7,
        )

    fig.suptitle(
        f"Cost reducers ({E0}→{E1}): net stake flow by initial size\n"
        f"n={int(reducers.sum())} reducers; "
        f"net $\\sum\\Delta\\sigma$={total_net/1e6:+.0f} M ADA "
        f"({100*total_net/T0:+.2f}% of stake@{E0}, "
        f"{100*total_net/T1:+.2f}% of stake@{E1})",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_CSV}")
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
