#!/usr/bin/env python3
"""
Declared pledge vs fixed cost (epoch 644).

Motivation: a0 tilts the reward function toward declared pledge, so pools that
commit more pledge already enjoy a larger f(σ,p). If operators use that
advantage to compete for delegators, we would expect high-pledge pools to also
set lower declared fixed costs (lower fees).

Declared pledge p = pool_update.active.pledge
Fixed cost      c = pool_update.active.fixed_cost

Plot: log(p) vs c scatter. No OLS line: fixed cost is discrete (policy
notches) and a few extreme c values make a fitted slope misleading.

Usage:
  python3 plot_declared_pledge_vs_fixed_cost_epoch_644.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
OUT_PLOT = DIR / "declared_pledge_vs_fixed_cost_epoch_644.png"
OUT_CSV = DIR / "declared_pledge_vs_fixed_cost_epoch_644.csv"

FONT_SIZE = 12
# Statistics use every pool; the axis is capped so the common cost notches stay readable.
COST_Y_MAX = 400.0


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    p = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    c = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "pool_ticker": df["pool_name.ticker"],
            "declared_pledge_ada": p,
            "fixed_cost_ada": c,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    ok = out["declared_pledge_ada"].gt(0) & out["fixed_cost_ada"].notna()
    plot_df = out.loc[ok].copy()
    x = plot_df["declared_pledge_ada"].to_numpy(dtype=float)
    y = plot_df["fixed_cost_ada"].to_numpy(dtype=float)
    lx = np.log10(x)

    spearman = float(pd.Series(x).corr(pd.Series(y), method="spearman"))
    pearson_log = float(pd.Series(lx).corr(pd.Series(y)))
    pearson = float(pd.Series(x).corr(pd.Series(y)))
    n = len(plot_df)

    print(f"pools plotted (declared pledge>0): {n}")
    print(f"pools above the {COST_Y_MAX:.0f} ADA axis cap (still in stats): {int((y > COST_Y_MAX).sum())}")
    print(f"Spearman(p, c)              = {spearman:.4f}")
    print(f"Pearson(log10 p, c)         = {pearson_log:.4f}")
    print(f"Pearson(p, c)               = {pearson:.4f}")
    print("OLS omitted: c is notch-dominated; a few extreme costs distort the fit.")

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

    ax.set_xscale("log")
    ax.set_ylim(0.0, COST_Y_MAX)
    ax.set_xlabel(r"Declared pledge $p_i$ (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"Declared fixed cost $c_i$ (ADA)", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — declared pledge vs fixed cost\n"
        r"($a_0$ weights pledge in $f$; do high-$p$ pools also set lower $c$?)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="upper left")
    fig.savefig(OUT_PLOT, dpi=160)
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
