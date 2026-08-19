#!/usr/bin/env python3
"""Epoch 644 — desirability ranking scatter: rho=0.003 vs rho=0.0042."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rho_comparison_common import FONT_SIZE, RHO_BASE, RHO_NEW, load_and_compute

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_desirability_rho_0p003_vs_0p0042_epoch_644.png"


def main():
    d = load_and_compute()
    pledge_met = d["pledge_met"]
    d_base, d_new = d["d_base"], d["d_new"]

    mask = pledge_met & ((d_base > 0) | (d_new > 0))
    d_b = d_base[mask]
    d_n = d_new[mask]
    rank_base = np.argsort(np.argsort(-d_b)) + 1
    rank_new = np.argsort(np.argsort(-d_n)) + 1

    fig, ax = plt.subplots(figsize=(7, 7), constrained_layout=True)
    ax.scatter(rank_base, rank_new, s=8, alpha=0.4, color="#4c78a8")
    lim = max(rank_base.max(), rank_new.max()) + 10
    ax.plot([1, lim], [1, lim], color="grey", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel(rf"Desirability rank ($\rho={RHO_BASE}$)", fontsize=FONT_SIZE)
    ax.set_ylabel(rf"Desirability rank ($\rho={RHO_NEW}$)", fontsize=FONT_SIZE)
    ax.set_title(
        rf"Epoch 644 — desirability ranking: $\rho={RHO_BASE}$ vs $\rho={RHO_NEW}$",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

    rank_corr = np.corrcoef(rank_base, rank_new)[0, 1]
    rank_changes = np.abs(rank_new.astype(int) - rank_base.astype(int))
    ax.text(
        0.05, 0.95,
        f"Rank correlation: {rank_corr:.6f}\n"
        f"Max rank change: {rank_changes.max()}\n"
        f"Mean |rank change|: {rank_changes.mean():.1f}\n"
        f"Pools plotted: {mask.sum()}",
        transform=ax.transAxes, ha="left", va="top", fontsize=FONT_SIZE,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
    )
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
