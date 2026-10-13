#!/usr/bin/env python3
"""
Compare pools with declared fixed cost 170 vs 340 ADA (epoch 644).

Active pools only (not σ=0, not unmet pledge, not zero blocks in
epochs 630–644). Merged snapshot (unique-owner live pledge).

Writes figures:
  1) log-stake density / overlapping histogram
  2) margin histogram
  3) stake vs margin scatter (color = fixed cost)

Bubble charts live in separate scripts:
  - plot_fixed_cost_170_vs_340_stake_bubbles_epoch_644.py
  - plot_fixed_cost_170_vs_340_stake_bubbles_ex_m100_epoch_644.py

Usage:
  python3 plot_fixed_cost_170_vs_340_characteristics_epoch_644.py
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
OUT_STAKE = DIR / "fixed_cost_170_vs_340_stake_density_epoch_644.png"
OUT_MARGIN = DIR / "fixed_cost_170_vs_340_margin_hist_epoch_644.png"
OUT_SCATTER = DIR / "fixed_cost_170_vs_340_stake_vs_margin_epoch_644.png"

FONT_SIZE = 12
COLOR_170 = "#2a9d8f"
COLOR_340 = "#e76f51"


def load_groups() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = load_active_pools()
    cost_ada = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    out = pd.DataFrame(
        {
            "cost_ada": cost_ada,
            "stake_ada": pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce")
            / 1e6,
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
            "pledge_ada": pd.to_numeric(df["pool_update.active.pledge"], errors="coerce")
            / 1e6,
            "delegators": pd.to_numeric(
                df["epochs.0.data.delegators"], errors="coerce"
            ),
        }
    )
    g170 = out[out["cost_ada"] == 170].dropna(subset=["stake_ada", "margin"])
    g340 = out[out["cost_ada"] == 340].dropna(subset=["stake_ada", "margin"])
    return g170, g340


def plot_stake_density(g170: pd.DataFrame, g340: pd.DataFrame) -> None:
    # Drop dust / empty pools so the density scale is readable on log stake
    min_stake = 1.0  # ADA
    s170 = g170.loc[g170["stake_ada"] >= min_stake, "stake_ada"].to_numpy()
    s340 = g340.loc[g340["stake_ada"] >= min_stake, "stake_ada"].to_numpy()
    n170_ex = int(len(g170) - len(s170))
    n340_ex = int(len(g340) - len(s340))

    lo = np.log10(min(s170.min(), s340.min()))
    hi = np.log10(max(s170.max(), s340.max()))
    bins = np.logspace(lo, hi, 35)

    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    ax.hist(
        s340,
        bins=bins,
        density=True,
        alpha=0.55,
        color=COLOR_340,
        edgecolor="white",
        linewidth=0.3,
        label=f"c = 340 ADA (n={len(s340)}; median={np.median(s340):,.0f})",
    )
    ax.hist(
        s170,
        bins=bins,
        density=True,
        alpha=0.55,
        color=COLOR_170,
        edgecolor="white",
        linewidth=0.3,
        label=f"c = 170 ADA (n={len(s170)}; median={np.median(s170):,.0f})",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Epoch stake (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel("Density", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — stake distribution by declared fixed cost (Active)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1)
    ax.text(
        0.02,
        0.98,
        f"Excluded stake < {min_stake:g} ADA: {n170_ex} at c=170, {n340_ex} at c=340",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="0.35",
    )
    fig.savefig(OUT_STAKE, dpi=160)
    print(f"wrote {OUT_STAKE}")


def plot_margin_hist(g170: pd.DataFrame, g340: pd.DataFrame) -> None:
    m170 = g170["margin"].clip(0, 1).to_numpy()
    m340 = g340["margin"].clip(0, 1).to_numpy()
    bins = np.arange(0, 1.05, 0.05)

    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    ax.hist(
        m340,
        bins=bins,
        density=True,
        alpha=0.55,
        color=COLOR_340,
        edgecolor="white",
        linewidth=0.3,
        label=f"c = 340 ADA (n={len(m340)}; median={np.median(m340):.2%})",
    )
    ax.hist(
        m170,
        bins=bins,
        density=True,
        alpha=0.55,
        color=COLOR_170,
        edgecolor="white",
        linewidth=0.3,
        label=f"c = 170 ADA (n={len(m170)}; median={np.median(m170):.2%})",
    )
    ax.set_xlabel("Declared margin m", fontsize=FONT_SIZE)
    ax.set_ylabel("Density", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — margin distribution by declared fixed cost (Active)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1)
    fig.savefig(OUT_MARGIN, dpi=160)
    print(f"wrote {OUT_MARGIN}")


def plot_stake_vs_margin(g170: pd.DataFrame, g340: pd.DataFrame) -> None:
    # Jitter margin slightly for visibility at discrete values; keep stake as-is
    rng = np.random.default_rng(644)

    def scatter(ax, g, color, label):
        stake = g["stake_ada"].to_numpy()
        margin = g["margin"].clip(0, 1).to_numpy()
        # tiny vertical jitter so overlapping points separate
        jitter = rng.normal(0.0, 0.004, size=len(margin))
        ax.scatter(
            np.clip(stake, 1.0, None),
            np.clip(margin + jitter, -0.02, 1.02),
            s=14,
            alpha=0.35,
            color=color,
            edgecolors="none",
            label=f"{label} (n={len(g)})",
        )

    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    scatter(ax, g340, COLOR_340, "c = 340 ADA")
    scatter(ax, g170, COLOR_170, "c = 170 ADA")
    ax.set_xscale("log")
    ax.set_xlabel("Epoch stake (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel("Declared margin m", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — stake vs margin by declared fixed cost (Active)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="upper right")
    fig.savefig(OUT_SCATTER, dpi=160)
    print(f"wrote {OUT_SCATTER}")


def main() -> None:
    g170, g340 = load_groups()
    print(f"c=170: n={len(g170)}; c=340: n={len(g340)}")
    print(
        "median stake ADA:",
        f"170={g170['stake_ada'].median():.0f}, 340={g340['stake_ada'].median():.0f}",
    )
    print(
        "median margin:",
        f"170={g170['margin'].median():.4f}, 340={g340['margin'].median():.4f}",
    )
    plot_stake_density(g170, g340)
    plot_margin_hist(g170, g340)
    plot_stake_vs_margin(g170, g340)


if __name__ == "__main__":
    main()
