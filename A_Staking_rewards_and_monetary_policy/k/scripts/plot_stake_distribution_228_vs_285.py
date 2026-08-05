#!/usr/bin/env python3
"""
Compare pool stake distributions at epoch 228 vs epoch 285 via ECDFs
(empirical CDFs) on a log stake axis.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "stake_distribution_228_vs_285.png"
OUT_CSV = DIR / "stake_distribution_228_vs_285_summary.csv"

E0, E1 = 228, 285
FONT_SIZE = 12
COLOR_228 = "#2a9d8f"
COLOR_285 = "#e76f51"
MIN_STAKE = 1.0  # ADA


def load_stake(epoch: int) -> np.ndarray:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    stake = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce")
        / 1e6
    )
    return stake.fillna(0.0).to_numpy()


def ecdf(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs = np.sort(x)
    ys = np.arange(1, len(xs) + 1) / len(xs)
    return xs, ys


def summarize(epoch: int, s_all: np.ndarray, s: np.ndarray) -> dict:
    return {
        "epoch": epoch,
        "n_pools_total": int(len(s_all)),
        "n_pools_sigma_gt_0": int((s_all > 0).sum()),
        "n_in_plot": int(len(s)),
        "n_excluded_lt_min_stake": int((s_all > 0).sum() - len(s)),
        "mean_ADA": float(s.mean()) if len(s) else float("nan"),
        "median_ADA": float(np.median(s)) if len(s) else float("nan"),
        "p90_ADA": float(np.percentile(s, 90)) if len(s) else float("nan"),
        "p99_ADA": float(np.percentile(s, 99)) if len(s) else float("nan"),
        "max_ADA": float(s.max()) if len(s) else float("nan"),
        "sum_ADA": float(s_all[s_all > 0].sum()),
    }


def main() -> None:
    s0_all = load_stake(E0)
    s1_all = load_stake(E1)
    s0 = s0_all[s0_all >= MIN_STAKE]
    s1 = s1_all[s1_all >= MIN_STAKE]

    rows = [summarize(E0, s0_all, s0), summarize(E1, s1_all, s1)]
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x0, f0 = ecdf(s0)
    x1, f1 = ecdf(s1)

    fig, ax = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    ax.step(
        x0,
        f0,
        where="post",
        color=COLOR_228,
        linewidth=2.0,
        label=f"Epoch {E0} (n={len(s0)}; median={np.median(s0)/1e6:.2f} M)",
    )
    ax.step(
        x1,
        f1,
        where="post",
        color=COLOR_285,
        linewidth=2.0,
        label=f"Epoch {E1} (n={len(s1)}; median={np.median(s1)/1e6:.2f} M)",
    )
    ax.axhline(0.5, color="0.55", linestyle=":", linewidth=1.0)
    ax.axvline(np.median(s0), color=COLOR_228, linestyle="--", linewidth=1.0, alpha=0.85)
    ax.axvline(np.median(s1), color=COLOR_285, linestyle="--", linewidth=1.0, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlim(MIN_STAKE, max(s0.max(), s1.max()) * 1.05)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Epoch stake (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel("Fraction of pools ≤ stake", fontsize=FONT_SIZE)
    ax.set_title(
        f"Pool stake distribution: epoch {E0} vs epoch {E1}",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 1, loc="lower right")
    ax.grid(alpha=0.25)

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    for r in rows:
        print(
            f"  ep{r['epoch']}: n={r['n_in_plot']}  "
            f"median={r['median_ADA']/1e6:.3f}M  "
            f"mean={r['mean_ADA']/1e6:.3f}M  "
            f"S={r['sum_ADA']/1e9:.2f}B"
        )


if __name__ == "__main__":
    main()
