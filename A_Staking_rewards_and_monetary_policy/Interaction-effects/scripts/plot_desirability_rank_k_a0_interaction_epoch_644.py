#!/usr/bin/env python3
"""Desirability ranking: k and a0 interaction (epoch 644).

3 panels vs baseline (k=500, a0=0.3):
  A) k:500->1000, a0=0.3
  B) k:500->1000, a0=0.6
  C) k=500, a0:0.3->0.6

Writes two figures: all pledge-met pools (oversaturated in red), and unsaturated only.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
PARENT = DIR.parent
POOLS_CSV = PARENT / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = PARENT / "f_reward_params_epoch_644.json"
OUT_ALL = DIR / "desirability_rank_k_a0_interaction_all_epoch_644.png"
OUT_UNSAT = DIR / "desirability_rank_k_a0_interaction_unsaturated_epoch_644.png"
OUT_CSV = DIR / "desirability_rank_k_a0_interaction_epoch_644.csv"

FONT_SIZE = 12
A0_0 = 0.3
A0_1 = 0.6
K0 = 500
K1 = 1000


def gross(sigma, declared, *, z0, r_over_t, a0):
    st = np.minimum(np.maximum(sigma, 0.0), z0)
    pt = np.minimum(np.maximum(declared, 0.0), z0)
    pt = np.minimum(pt, st)
    inner = st - pt * (z0 - st) / z0
    return (r_over_t / (1.0 + a0)) * (st + a0 * pt * inner / z0)


def desirability(sigma, declared, active, cost, margin, *, z0, r_over_t, a0):
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    d = np.where(sigma > 0, pot / sigma, 0.0)
    d = np.where(pledge_met, d, 0.0)
    return d, f, pledge_met


def ranks(d):
    return np.argsort(np.argsort(-d)) + 1


def scatter_panel(ax, d_base, d_alt, mask, oversaturated, *, xlabel, ylabel, title, show_over):
    db = d_base[mask]
    da = d_alt[mask]
    over = oversaturated[mask]
    pos = (db > 0) | (da > 0)
    db, da, over = db[pos], da[pos], over[pos]
    rb, ra = ranks(db), ranks(da)

    if show_over:
        unsat = ~over
        ax.scatter(rb[unsat], ra[unsat], s=6, alpha=0.35, color="#4c78a8", label=r"$\sigma\leq z_0(1000)$")
        ax.scatter(
            rb[over], ra[over], s=12, alpha=0.6, color="#dc2626",
            label=r"Would oversaturate at $k=1000$",
        )
        n_over = int(over.sum())
    else:
        ax.scatter(rb, ra, s=6, alpha=0.35, color="#4c78a8")
        n_over = 0

    lim = int(max(rb.max(), ra.max())) + 10
    ax.plot([1, lim], [1, lim], color="grey", ls="--", lw=1, alpha=0.6)
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

    corr = float(np.corrcoef(rb, ra)[0, 1]) if len(rb) > 1 else float("nan")
    changes = np.abs(ra.astype(int) - rb.astype(int))
    note = f"Rank corr: {corr:.4f}\nMean |Δrank|: {changes.mean():.1f}\nn={len(rb)}"
    if show_over:
        note += f"\n(would oversat.: {n_over})"
    ax.text(
        0.05, 0.95, note,
        transform=ax.transAxes, ha="left", va="top", fontsize=FONT_SIZE - 1,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
    )
    if show_over:
        ax.legend(fontsize=FONT_SIZE - 1, loc="lower right", markerscale=1.5)


def make_figure(d0, dA, dB, dC, pledge_met, oversat, include_mask, show_over, out_path, subtitle):
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.6), constrained_layout=True)
    scatter_panel(
        axes[0], d0, dA, include_mask, oversat, show_over=show_over,
        xlabel=r"Rank: $k=500$, $a_0=0.3$",
        ylabel=r"Rank: $k=1000$, $a_0=0.3$",
        title=r"A: $k\!:\,500\to1000$, $a_0=0.3$",
    )
    scatter_panel(
        axes[1], d0, dB, include_mask, oversat, show_over=show_over,
        xlabel=r"Rank: $k=500$, $a_0=0.3$",
        ylabel=r"Rank: $k=1000$, $a_0=0.6$",
        title=r"B: $k\!:\,500\to1000$, $a_0\!:\,0.3\to0.6$",
    )
    scatter_panel(
        axes[2], d0, dC, include_mask, oversat, show_over=show_over,
        xlabel=r"Rank: $k=500$, $a_0=0.3$",
        ylabel=r"Rank: $k=500$, $a_0=0.6$",
        title=r"C: $k=500$, $a_0\!:\,0.3\to0.6$",
    )
    fig.suptitle(
        "Epoch 644 — desirability ranking under $k$–$a_0$ interaction\n" + subtitle,
        fontsize=FONT_SIZE,
    )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_500 = T / K0
    z0_1000 = T / K1

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce").fillna(0.0) / 1e6
    ).to_numpy(dtype=float)
    declared = (pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0) / 1e6).to_numpy(dtype=float)
    active = (pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6).to_numpy(dtype=float)
    cost = (pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0) / 1e6).to_numpy(dtype=float)
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0).to_numpy(dtype=float)

    d0, f0, pledge_met = desirability(sigma, declared, active, cost, margin, z0=z0_500, r_over_t=r_over_t, a0=A0_0)
    dA, fA, _ = desirability(sigma, declared, active, cost, margin, z0=z0_1000, r_over_t=r_over_t, a0=A0_0)
    dB, fB, _ = desirability(sigma, declared, active, cost, margin, z0=z0_1000, r_over_t=r_over_t, a0=A0_1)
    dC, fC, _ = desirability(sigma, declared, active, cost, margin, z0=z0_500, r_over_t=r_over_t, a0=A0_1)

    oversat = sigma > z0_1000
    unsat = sigma <= z0_1000

    pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": sigma,
            "pledge_met": pledge_met,
            "unsaturated_k1000": unsat,
            "D_base_k500_a0_0p3": d0,
            "D_A_k1000_a0_0p3": dA,
            "D_B_k1000_a0_0p6": dB,
            "D_C_k500_a0_0p6": dC,
            "f_base": f0,
            "f_A": fA,
            "f_B": fB,
            "f_C": fC,
        }
    ).to_csv(OUT_CSV, index=False)

    sub = (
        rf"$R={R/1e6:.2f}$M, $T={T/1e9:.2f}$B; "
        rf"$z_0(500)={z0_500/1e6:.1f}$M, $z_0(1000)={z0_1000/1e6:.1f}$M; "
        r"$D_i=(1-m_i)\max\{f-c,0\}/\sigma_i$"
    )
    make_figure(
        d0, dA, dB, dC, pledge_met, oversat, pledge_met, True, OUT_ALL,
        sub + r"; red: would oversaturate at $k=1000$",
    )
    make_figure(
        d0, dA, dB, dC, pledge_met, oversat, pledge_met & unsat, False, OUT_UNSAT,
        sub + rf"; only $\sigma\leq z_0(1000)$",
    )
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
