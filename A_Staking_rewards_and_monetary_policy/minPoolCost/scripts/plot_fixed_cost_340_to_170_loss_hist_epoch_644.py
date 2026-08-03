#!/usr/bin/env python3
"""
Histogram: % operator-reward loss if pools with fixed cost 340 ADA
had declared 170 ADA instead (epoch 644).

For each pool with declared fixed cost = 340 ADA and positive epoch rewards:
  f = member_lovelace + leader_lovelace   (total pool rewards, held fixed)
  Π(c) = f                         if f ≤ c
       = c + (f - c) * share       if f > c
  share = m + (1 - m) * (p / σ)    (margin + pledge share of remainder)

  loss % = 100 * (Π(340) - Π(170)) / Π(340)

This matches the operator_reward definition used elsewhere in
Cardano-Parameters-Landscape (fees + operator's member share via pledge).

Usage:
  python3 plot_fixed_cost_340_to_170_loss_hist_epoch_644.py
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
OUT_PLOT = DIR / "fixed_cost_340_to_170_loss_hist_epoch_644.png"
OUT_CSV = DIR / "fixed_cost_340_to_170_loss_epoch_644.csv"

FONT_SIZE = 12
C_FROM = 340.0 * 1e6  # lovelace
C_TO = 170.0 * 1e6


def operator_reward(
    f: np.ndarray, m: np.ndarray, p: np.ndarray, sigma: np.ndarray, c: float
) -> np.ndarray:
    share = m + (1.0 - m) * np.clip(p / sigma, 0.0, 1.0)
    return np.where(f > c, c + (f - c) * share, f)


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce")
    m = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0)
    leader = pd.to_numeric(df["epochs.0.data.reward.leader_lovelace"], errors="coerce")
    member = pd.to_numeric(df["epochs.0.data.reward.member_lovelace"], errors="coerce")
    pledge = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0)
    stake = pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce")

    f = leader + member
    mask = (
        (cost == C_FROM)
        & f.notna()
        & (f > 0)
        & stake.notna()
        & (stake > 0)
        & m.notna()
    )
    sub = df.loc[mask].copy()
    f_ = f[mask].to_numpy(dtype=float)
    m_ = m[mask].to_numpy(dtype=float)
    p_ = pledge[mask].to_numpy(dtype=float)
    s_ = stake[mask].to_numpy(dtype=float)

    pi340 = operator_reward(f_, m_, p_, s_, C_FROM)
    pi170 = operator_reward(f_, m_, p_, s_, C_TO)
    loss_pct = 100.0 * (pi340 - pi170) / pi340

    out = pd.DataFrame(
        {
            "pool_id": sub["pool_id"].to_numpy(),
            "pool_ticker": sub["pool_name.ticker"].to_numpy(),
            "margin": m_,
            "pledge_lovelace": p_,
            "epoch_stake_lovelace": s_,
            "f_lovelace": f_,
            "operator_reward_c340_lovelace": pi340,
            "operator_reward_c170_lovelace": pi170,
            "loss_pct": loss_pct,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    print(f"pools with fixed_cost=340 ADA: {(cost == C_FROM).sum()}")
    print(f"of which with f>0 and stake>0: {len(out)}")
    print("loss % describe:")
    print(out["loss_pct"].describe().to_string())
    print(
        "quantiles:",
        out["loss_pct"].quantile([0, 0.25, 0.5, 0.75, 0.95, 1.0]).to_string(),
    )

    fig, ax = plt.subplots(figsize=(8.5, 5.0), constrained_layout=True)
    bins = np.arange(0, 52.5, 2.5)
    ax.hist(loss_pct, bins=bins, color="#4c78a8", edgecolor="white", linewidth=0.4)
    ax.axvline(
        float(np.median(loss_pct)),
        color="#e76f51",
        linewidth=1.6,
        label=f"median = {np.median(loss_pct):.1f}%",
    )
    ax.set_xlabel(
        r"Operator reward reduction if $c$: $340\to 170$ ADA (%)",
        fontsize=FONT_SIZE,
    )
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — pools with declared fixed cost 340 ADA\n"
        r"($f$, margin, pledge held fixed; $n=" + f"{len(out)}$"
        r" pools with rewards)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(0, 50)
    ax.legend(frameon=False, fontsize=FONT_SIZE)
    fig.savefig(OUT_PLOT, dpi=160)
    print(f"wrote {OUT_PLOT}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
