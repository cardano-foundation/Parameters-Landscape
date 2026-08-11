#!/usr/bin/env python3
"""
Margin changes among epoch-228 cohort pools that survive to epoch 285,
and stake outcomes (gain / lose / flat) within each margin strategy.

Sample: all pools with σ>0 at epoch 228 that are still present at 285
(not restricted to unsaturated pools).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
E0, E1 = 228, 285
FONT_SIZE = 12
COLOR_DOWN = "#2a9d8f"
COLOR_UP = "#e76f51"
COLOR_SAME = "#9ca3af"
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"

OUT_PLOT = DIR / "cohort_margin_change_stake_outcomes_228_285.png"
OUT_CSV = DIR / "cohort_margin_change_stake_outcomes_228_285.csv"
OUT_MD = DIR / "cohort_margin_change_stake_outcomes_228_285.md"


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
        }
    ).set_index("pool_id")


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)

    cohort = a[a["stake_ada"] > 0].index
    surviving = cohort.intersection(b.index)
    exited = cohort.difference(b.index)

    aa = a.loc[surviving]
    bb = b.loc[surviving]
    ok = aa["margin"].notna() & bb["margin"].notna()
    aa, bb = aa.loc[ok], bb.loc[ok]

    d_stake = bb["stake_ada"] - aa["stake_ada"]
    dm = bb["margin"] - aa["margin"]

    groups = [
        ("margin ↓", dm < 0, COLOR_DOWN),
        ("margin ↑", dm > 0, COLOR_UP),
        ("margin =", dm == 0, COLOR_SAME),
    ]

    rows = []
    stake_counts: list[tuple[str, int, list[int]]] = []
    for lab, mask, _ in groups:
        n = int(mask.sum())
        g = int((d_stake[mask] > 0).sum())
        l = int((d_stake[mask] < 0).sum())
        f = int((d_stake[mask] == 0).sum())
        stake_counts.append((lab, n, [g, l, f]))
        rows.append(
            {
                "margin_strategy": lab,
                "n_pools": n,
                "share_of_surviving_pct": 100.0 * n / len(aa) if len(aa) else float("nan"),
                "stake_gain": g,
                "stake_lose": l,
                "stake_flat": f,
                "agg_dstake_gain_ADA": float(d_stake[mask & (d_stake > 0)].sum()),
                "agg_dstake_lose_ADA": float(d_stake[mask & (d_stake < 0)].sum()),
                "agg_dstake_net_ADA": float(d_stake[mask].sum()),
                "median_dstake_ADA": float(d_stake[mask].median()) if n else float("nan"),
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    # --- Plot: left = margin change counts; right = stake outcomes by margin ---
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), constrained_layout=True)

    # Left panel
    ax = axes[0]
    labs = [r[0] for r in stake_counts]
    ns = [r[1] for r in stake_counts]
    colors = [c for _, _, c in groups]
    bars = ax.bar(labs, ns, color=colors, edgecolor="0.2", width=0.65)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(r"Margin $m_i$ change (228→285)", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(ns) * 1.15 if ns else 1.0
    ax.set_ylim(0, ymax)
    for bar, n in zip(bars, ns):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            n + ymax * 0.02,
            f"{n}\n({100*n/len(aa):.1f}%)",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE - 2,
        )

    # Right panel: grouped bars gain/lose/flat within each margin strategy
    ax = axes[1]
    x = np.arange(len(labs))
    width = 0.25
    gain_vals = [r[2][0] for r in stake_counts]
    lose_vals = [r[2][1] for r in stake_counts]
    flat_vals = [r[2][2] for r in stake_counts]
    b1 = ax.bar(x - width, gain_vals, width, color=COLOR_GAIN, label="stake gain", edgecolor="0.2")
    b2 = ax.bar(x, lose_vals, width, color=COLOR_LOSE, label="stake lose", edgecolor="0.2")
    b3 = ax.bar(x + width, flat_vals, width, color=COLOR_FLAT, label="stake flat", edgecolor="0.2")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labs, ns)], fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title("Stake outcome by margin strategy", fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ymax2 = max(gain_vals + lose_vals + flat_vals + [1]) * 1.18
    ax.set_ylim(0, ymax2)
    for bars in (b1, b2, b3):
        for bar in bars:
            v = int(bar.get_height())
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    v + ymax2 * 0.015,
                    str(v),
                    ha="center",
                    fontsize=FONT_SIZE - 3,
                )

    fig.suptitle(
        f"Epoch 228 cohort survivors at 285: margin changes and stake outcomes\n"
        f"(cohort $n={len(cohort)}$; surviving $n={len(surviving)}$; "
        f"with complete margins $n={len(aa)}$; exited $n={len(exited)}$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    md_lines = [
        "# Cohort 228 → 285: margin changes and stake outcomes",
        "",
        f"Sample: all pools with $\\sigma_i>0$ at epoch 228 that survive to epoch 285 "
        f"($n={len(aa)}$ with complete margins; cohort $n={len(cohort)}$, "
        f"exited $n={len(exited)}$).",
        "",
        "| Margin strategy | Pools | Share | Stake gain | Stake lose | Stake flat | "
        "Net $\\Delta\\sigma$ (M ADA) | Median $\\Delta\\sigma$ (ADA) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md_lines.append(
            f"| {r['margin_strategy']} | {r['n_pools']} | "
            f"{r['share_of_surviving_pct']:.1f}% | "
            f"{r['stake_gain']} | {r['stake_lose']} | {r['stake_flat']} | "
            f"{r['agg_dstake_net_ADA']/1e6:+.1f} | "
            f"{r['median_dstake_ADA']:,.0f} |"
        )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    for r in rows:
        print(
            f"  {r['margin_strategy']}: n={r['n_pools']} "
            f"(gain={r['stake_gain']}, lose={r['stake_lose']}, flat={r['stake_flat']})"
        )


if __name__ == "__main__":
    main()
