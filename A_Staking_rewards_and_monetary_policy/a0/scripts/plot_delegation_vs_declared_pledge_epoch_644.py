#!/usr/bin/env python3
"""
Correlation: third-party delegation vs declared pledge (epoch 644).

Declared pledge        = pool_update.active.pledge   (registered commitment)
Active pledge          = pledged                    (owner stake actually on chain)
Third-party delegation = active_stake - pledged      (stake from non-owners)

Third-party delegation removes the operator's own stake, so the y-axis is not
mechanically inflated by the pledge itself. Pools with a non-positive residual
cannot appear on a logarithmic axis and are reported separately; a robustness
variant subtracting the declared pledge instead is also reported.

Plot: log–log scatter of declared pledge (x) vs third-party delegation (y),
OLS fit on log10 scales, Spearman (levels) and Pearson (log10) annotated.

Usage:
  python3 plot_delegation_vs_declared_pledge_epoch_644.py
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
OUT_PLOT = DIR / "delegation_vs_declared_pledge_epoch_644.png"
OUT_CSV = DIR / "delegation_vs_declared_pledge_epoch_644.csv"

FONT_SIZE = 12


def corr_triplet(x: pd.Series, y: pd.Series) -> tuple[float, float, float]:
    """Spearman on levels, Pearson on log10, Pearson on levels."""
    return (
        float(x.corr(y, method="spearman")),
        float(np.log10(x).corr(np.log10(y))),
        float(x.corr(y)),
    )


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    declared_pledge_ada = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active_pledge_ada = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    stake_ada = pd.to_numeric(df["active_stake"], errors="coerce") / 1e6

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "pool_ticker": df["pool_name.ticker"],
            "declared_pledge_ada": declared_pledge_ada,
            "active_pledge_ada": active_pledge_ada,
            "active_stake_ada": stake_ada,
            "third_party_delegation_ada": stake_ada - active_pledge_ada,
            "third_party_delegation_vs_declared_ada": stake_ada - declared_pledge_ada,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    ok = (
        out["declared_pledge_ada"].notna()
        & out["third_party_delegation_ada"].notna()
        & (out["declared_pledge_ada"] > 0)
        & (out["third_party_delegation_ada"] > 0)
    )
    plot_df = out.loc[ok].copy()

    x = plot_df["declared_pledge_ada"]
    y = plot_df["third_party_delegation_ada"]
    spearman, pearson_log, pearson_raw = corr_triplet(x, y)
    n = len(plot_df)

    alt = out.loc[
        out["declared_pledge_ada"].gt(0)
        & out["third_party_delegation_vs_declared_ada"].gt(0)
    ]
    alt_spearman, alt_pearson_log, _ = corr_triplet(
        alt["declared_pledge_ada"], alt["third_party_delegation_vs_declared_ada"]
    )

    nonpositive_residual = int(
        (out["declared_pledge_ada"].gt(0) & out["third_party_delegation_ada"].le(0)).sum()
    )
    pledge_pairs = out[["declared_pledge_ada", "active_pledge_ada"]].dropna()
    equal = int(
        pledge_pairs["declared_pledge_ada"].eq(pledge_pairs["active_pledge_ada"]).sum()
    )
    over_pledged = int(
        pledge_pairs["active_pledge_ada"].gt(pledge_pairs["declared_pledge_ada"]).sum()
    )
    under_pledged = len(pledge_pairs) - equal - over_pledged

    print(f"pools plotted (declared pledge>0, third-party delegation>0): {n}")
    print(f"declared pledge>0 pools with non-positive residual: {nonpositive_residual}")
    print(
        "declared == active pledge: "
        f"{equal}/{len(pledge_pairs)} ({equal / len(pledge_pairs):.1%}); "
        f"active above declared: {over_pledged}; active below declared: {under_pledged}"
    )
    print(f"Spearman(declared pledge, third-party delegation)            = {spearman:.4f}")
    print(f"Pearson(log10 declared pledge, log10 third-party delegation) = {pearson_log:.4f}")
    print(f"Pearson(declared pledge, third-party delegation)             = {pearson_raw:.4f}")
    print(
        "robustness (stake - declared pledge, n="
        f"{len(alt)}): Spearman={alt_spearman:.4f}, Pearson_log={alt_pearson_log:.4f}"
    )

    lx = np.log10(x.to_numpy(dtype=float))
    ly = np.log10(y.to_numpy(dtype=float))

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

    # OLS on log10 scales (visual guide for log–log association)
    coef = np.polyfit(lx, ly, 1)
    lx_line = np.linspace(lx.min(), lx.max(), 200)
    ly_line = coef[0] * lx_line + coef[1]
    ax.plot(
        10**lx_line,
        10**ly_line,
        color="#e76f51",
        linewidth=2.0,
        zorder=3,
        label=rf"OLS on $\log_{{10}}$ (slope={coef[0]:.2f})",
    )

    ref_lo = min(x.min(), y.min())
    ref_hi = max(x.max(), y.max())
    ax.plot(
        [ref_lo, ref_hi],
        [ref_lo, ref_hi],
        color="0.45",
        linestyle="--",
        linewidth=1.2,
        zorder=1,
        label=r"third-party delegation $=$ declared pledge",
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Declared pledge (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel(r"Third-party delegation (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — third-party delegation vs declared pledge\n"
        r"(declared $=$ pool_update.active.pledge; "
        r"third-party $=$ active_stake $-$ pledged)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="upper left")
    fig.savefig(OUT_PLOT, dpi=160)
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
