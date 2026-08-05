#!/usr/bin/env python3
"""
Stake-distribution ECDF for the epoch-228 pool cohort only:
  - teal: stake at epoch 228 (all pools present then)
  - coral: stake at epoch 285 among those same pools that still exist
    (new pools that appear only at 285 are excluded)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "stake_distribution_228_cohort_vs_285.png"
OUT_CSV = DIR / "stake_distribution_228_cohort_vs_285_summary.csv"

E0, E1 = 228, 285
FONT_SIZE = 12
COLOR_228 = "#2a9d8f"
COLOR_285 = "#e76f51"
MIN_STAKE = 1.0  # ADA


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    stake = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce")
        / 1e6
    )
    return pd.DataFrame(
        {"pool_id": df["pool_id"], "stake_ada": stake.fillna(0.0)}
    ).set_index("pool_id")


def ecdf(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xs = np.sort(x)
    ys = np.arange(1, len(xs) + 1) / len(xs)
    return xs, ys


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)

    ids_228 = a.index[a["stake_ada"] >= MIN_STAKE]
    continuing = ids_228.intersection(b.index)
    exited = ids_228.difference(b.index)

    s0 = a.loc[ids_228, "stake_ada"].to_numpy()
    # Epoch-285 curve: only pools that already existed at 228 (and still exist)
    s1 = b.loc[continuing, "stake_ada"].to_numpy()
    s1 = s1[s1 >= MIN_STAKE]

    rows = [
        {
            "series": f"epoch_{E0}_all_pools",
            "n": int(len(s0)),
            "median_ADA": float(np.median(s0)),
            "mean_ADA": float(s0.mean()),
            "p90_ADA": float(np.percentile(s0, 90)),
            "p99_ADA": float(np.percentile(s0, 99)),
            "max_ADA": float(s0.max()),
            "sum_ADA": float(s0.sum()),
        },
        {
            "series": f"epoch_{E1}_among_epoch_{E0}_continuing_pools",
            "n": int(len(s1)),
            "n_exited_from_228_excluded": int(len(exited)),
            "median_ADA": float(np.median(s1)),
            "mean_ADA": float(s1.mean()),
            "p90_ADA": float(np.percentile(s1, 90)),
            "p99_ADA": float(np.percentile(s1, 99)),
            "max_ADA": float(s1.max()),
            "sum_ADA": float(s1.sum()),
        },
    ]
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x0, f0 = ecdf(s0)
    x1, f1 = ecdf(s1)

    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    ax.step(
        x0,
        f0,
        where="post",
        color=COLOR_228,
        linewidth=2.0,
        label=f"Epoch {E0} — all pools then (n={len(s0)}; median={np.median(s0)/1e6:.2f} M)",
    )
    ax.step(
        x1,
        f1,
        where="post",
        color=COLOR_285,
        linewidth=2.0,
        label=(
            f"Epoch {E1} — only pools present at {E0} that continue "
            f"(n={len(s1)}; median={np.median(s1)/1e6:.2f} M)"
        ),
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
        f"Stake distribution of the epoch-{E0} pool cohort\n"
        f"(epoch-{E1} curve excludes pools new after {E0}; "
        f"{len(exited)} pools from {E0} exited by {E1} and are omitted from that curve)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="lower right")
    ax.grid(alpha=0.25)

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    print(f"  ep{E0} all: n={len(s0)} median={np.median(s0)/1e6:.3f}M")
    print(
        f"  ep{E1} among ep{E0} continuing: n={len(s1)} "
        f"median={np.median(s1)/1e6:.3f}M  exited_omitted={len(exited)}"
    )


if __name__ == "__main__":
    main()
