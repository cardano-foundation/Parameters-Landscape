#!/usr/bin/env python3
"""
Margin vs fixed cost (epoch 644).

Active pools only (not σ=0, not unmet pledge, not zero blocks in
epochs 630–644). Merged snapshot (unique-owner live pledge).

Motivation: a0 tilts rewards toward declared pledge; fee competition then
operates through the two declared fee instruments (margin and fixed cost).
This plot asks whether the two fee levers move together — e.g. whether
low-margin pools also choose low fixed cost — as context for interpreting
pledge–fee correlations.

Margin     m = pool_update.active.margin
Fixed cost c = pool_update.active.fixed_cost

Plot: m vs c scatter with OLS on levels.

Usage:
  python3 plot_margin_vs_fixed_cost_epoch_644.py
"""

from __future__ import annotations

from pathlib import Path

from minpoolcost_common import load_active_pools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT_PLOT = DIR / "margin_vs_fixed_cost_epoch_644.png"
OUT_CSV = DIR / "margin_vs_fixed_cost_epoch_644.csv"

FONT_SIZE = 12
# Statistics use every pool; the axis is capped so the common cost notches stay readable.
COST_Y_MAX = 400.0


def main() -> None:
    df = load_active_pools()
    m = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    c = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "pool_ticker": df["pool_name.ticker"],
            "margin": m,
            "fixed_cost_ada": c,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    ok = out["margin"].notna() & out["fixed_cost_ada"].notna()
    plot_df = out.loc[ok].copy()
    x = plot_df["margin"].to_numpy(dtype=float)
    y = plot_df["fixed_cost_ada"].to_numpy(dtype=float)

    spearman = float(pd.Series(x).corr(pd.Series(y), method="spearman"))
    pearson = float(pd.Series(x).corr(pd.Series(y)))
    n = len(plot_df)

    print(f"pools plotted: {n}")
    print(f"pools above the {COST_Y_MAX:.0f} ADA axis cap (still in stats): {int((y > COST_Y_MAX).sum())}")
    print(f"Spearman(m, c) = {spearman:.4f}")
    print(f"Pearson(m, c)  = {pearson:.4f}")

    fig, ax = plt.subplots(figsize=(8.5, 5.4), constrained_layout=True)
    ax.scatter(
        x,
        y,
        s=14,
        alpha=0.40,
        color="#4c78a8",
        edgecolors="none",
        zorder=2,
        label=rf"pools (n={n})",
    )

    coef = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 200)
    ax.plot(
        x_line,
        coef[0] * x_line + coef[1],
        color="#e76f51",
        linewidth=2.0,
        zorder=3,
        label=rf"OLS (slope={coef[0]:.1f})",
    )

    ax.set_ylim(0.0, COST_Y_MAX)
    ax.set_xlabel(r"Margin $m_i$", fontsize=FONT_SIZE)
    ax.set_ylabel(r"Declared fixed cost $c_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — margin vs fixed cost (Active)\n"
        r"(do the two fee levers move together?)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="upper left")
    fig.savefig(OUT_PLOT, dpi=160)
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
