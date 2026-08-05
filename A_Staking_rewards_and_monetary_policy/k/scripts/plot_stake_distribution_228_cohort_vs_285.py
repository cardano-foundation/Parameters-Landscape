#!/usr/bin/env python3
"""
Stake-distribution ECDF for the epoch-228 pool cohort.

Lines:
  - green dashed: epoch 228, all pools (incl. those that exit by 285)
  - green solid:  epoch 228, only continuing pools
  - coral:        epoch 285 stake of those continuing pools
                  (new-at-285 pools excluded)
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


def summarize(label: str, s: np.ndarray, **extra) -> dict:
    row = {
        "series": label,
        "n": int(len(s)),
        "median_ADA": float(np.median(s)) if len(s) else float("nan"),
        "mean_ADA": float(s.mean()) if len(s) else float("nan"),
        "p90_ADA": float(np.percentile(s, 90)) if len(s) else float("nan"),
        "p99_ADA": float(np.percentile(s, 99)) if len(s) else float("nan"),
        "max_ADA": float(s.max()) if len(s) else float("nan"),
        "sum_ADA": float(s.sum()) if len(s) else 0.0,
    }
    row.update(extra)
    return row


def main() -> None:
    a = load_epoch(E0)
    b = load_epoch(E1)

    ids_228 = a.index[a["stake_ada"] >= MIN_STAKE]
    continuing = ids_228.intersection(b.index)
    exited = ids_228.difference(b.index)

    s0_all = a.loc[ids_228, "stake_ada"].to_numpy()
    s0_cont = a.loc[continuing, "stake_ada"].to_numpy()
    s1_cont = b.loc[continuing, "stake_ada"].to_numpy()
    s1_cont = s1_cont[s1_cont >= MIN_STAKE]

    rows = [
        summarize(f"epoch_{E0}_all", s0_all, n_exited=int(len(exited))),
        summarize(f"epoch_{E0}_continuing_to_{E1}", s0_cont),
        summarize(
            f"epoch_{E1}_among_epoch_{E0}_continuing",
            s1_cont,
            n_exited_omitted=int(len(exited)),
        ),
    ]
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x_all, f_all = ecdf(s0_all)
    x_c0, f_c0 = ecdf(s0_cont)
    x_c1, f_c1 = ecdf(s1_cont)

    fig, ax = plt.subplots(figsize=(9.2, 5.4), constrained_layout=True)
    ax.step(
        x_all,
        f_all,
        where="post",
        color=COLOR_228,
        linewidth=2.0,
        linestyle="--",
        label=(
            f"Epoch {E0} — all pools "
            f"(n={len(s0_all)}; median={np.median(s0_all)/1e6:.2f} M)"
        ),
    )
    ax.step(
        x_c0,
        f_c0,
        where="post",
        color=COLOR_228,
        linewidth=2.2,
        linestyle="-",
        label=(
            f"Epoch {E0} — continuing to {E1} "
            f"(n={len(s0_cont)}; median={np.median(s0_cont)/1e6:.2f} M)"
        ),
    )
    ax.step(
        x_c1,
        f_c1,
        where="post",
        color=COLOR_285,
        linewidth=2.0,
        label=(
            f"Epoch {E1} — only pools present at {E0} that continue "
            f"(n={len(s1_cont)}; median={np.median(s1_cont)/1e6:.2f} M)"
        ),
    )
    ax.axhline(0.5, color="0.55", linestyle=":", linewidth=1.0)
    ax.axvline(np.median(s0_all), color=COLOR_228, linestyle="--", linewidth=1.0, alpha=0.7)
    ax.axvline(np.median(s0_cont), color=COLOR_228, linestyle="-", linewidth=1.0, alpha=0.85)
    ax.axvline(np.median(s1_cont), color=COLOR_285, linestyle="--", linewidth=1.0, alpha=0.85)

    ax.set_xscale("log")
    ax.set_xlim(MIN_STAKE, max(s0_all.max(), s1_cont.max()) * 1.05)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Epoch stake (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel("Fraction of pools ≤ stake", fontsize=FONT_SIZE)
    ax.set_title(
        f"Stake distribution of the epoch-{E0} pool cohort\n"
        f"(solid green = {E0} continuing pools; dashed green = all {E0}, "
        f"incl. {len(exited)} exits; orange = those continuing pools at {E1})",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="upper left")
    ax.grid(alpha=0.25)

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    for r in rows:
        print(
            f"  {r['series']}: n={r['n']} median={r['median_ADA']/1e6:.3f}M"
        )


if __name__ == "__main__":
    main()
