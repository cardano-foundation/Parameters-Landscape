#!/usr/bin/env python3
"""
Epoch-644 stake bins among Active pools, stacked by theoretical viability r.

Active = not (σ=0 ∪ unmet pledge ∪ zero blocks in epochs 630–644).
Inactive pools are excluded.

    C* = (667 / 6) / 0.15 ≈ 741.1 ADA/epoch
    Π_i = c_i + (f-c_i)[m_i + (1-m_i) p̂_i/σ_i]  if f > c_i
        = f                                       if f ≤ c_i
    r_i = Π_i / C*   at k=500 (current snapshot)

Bins match stake_distribution_by_bin_excl_inactive_pools_epoch644.py.
Top panel: % of pools in each r class within the bin.
Bottom panel: % of the bin's aggregate stake in each r class.
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
POOLS_CSV = DIR / "staking_pools_full_epoch_644_merged.csv"
FLAGS_CSV = DIR / "inactive_pool_flags_koios_epoch_644_last15.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_PLOT = DIR / "stake_distribution_by_bin_viability_r_epoch644.png"
OUT_CSV = DIR / "stake_distribution_by_bin_viability_r_epoch644.csv"

FONT_SIZE = 12
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

R_ORDER = ("r_lt_05", "r_05_1", "r_1_2", "r_ge_2")
R_LABELS = (
    r"$r<0.5$",
    r"$0.5\leq r<1$",
    r"$1\leq r<2$",
    r"$r\geq 2$",
)
R_COLORS = ("#a50f15", "#fc9272", "#b7e4c7", "#2a9d8f")


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    pledge_share = np.clip(
        np.divide(
            active_pledge,
            sigma,
            out=np.zeros_like(active_pledge),
            where=sigma > 0,
        ),
        0.0,
        1.0,
    )
    s = margin + (1.0 - margin) * pledge_share
    return np.where(f > fixed_cost, fixed_cost + (f - fixed_cost) * s, f)


def classify_r(ratio: float) -> str:
    if not np.isfinite(ratio) or ratio < 0.5:
        return "r_lt_05"
    if ratio < 1.0:
        return "r_05_1"
    if ratio < 2.0:
        return "r_1_2"
    return "r_ge_2"


def stake_bin_index(stake_m: np.ndarray, edges: np.ndarray) -> np.ndarray:
    idx = np.digitize(stake_m, edges, right=False) - 1
    idx = np.clip(idx, 0, len(edges) - 1)
    return np.where(stake_m >= BIN_MAX_M, len(edges) - 1, idx)


def stacked_percentages(
    ax,
    x: np.ndarray,
    pct: np.ndarray,
    colors: tuple[str, ...],
    labels: tuple[str, ...],
    *,
    show_legend: bool,
) -> None:
    bottom = np.zeros(len(x))
    for row, color, lab in zip(pct, colors, labels):
        ax.bar(
            x,
            row,
            bottom=bottom,
            color=color,
            edgecolor="0.2",
            width=0.85,
            label=lab if show_legend else None,
        )
        hex_c = color.lstrip("#")
        rr, gg, bb = (int(hex_c[i : i + 2], 16) for i in (0, 2, 4))
        label_color = "0.15" if (0.299 * rr + 0.587 * gg + 0.114 * bb) > 160 else "white"
        for xi, h, b in zip(x, row, bottom):
            if h >= 8.0:
                ax.text(
                    xi,
                    b + h / 2.0,
                    f"{h:.0f}",
                    ha="center",
                    va="center",
                    fontsize=FONT_SIZE - 4,
                    color=label_color,
                )
        bottom = bottom + row
    ax.set_ylim(0, 100)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax.tick_params(labelsize=FONT_SIZE - 1)
    ax.grid(axis="y", alpha=0.25)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])
    k = int(params["k"])

    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")

    sigma = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    ).fillna(0.0) / 1e6
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    live_pledge = pd.to_numeric(df["live_pledge"], errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    stake_m = sigma / 1e6

    inactive = df["in_union"] == 1
    active = ~inactive
    n_active = int(active.sum())
    stake_active_m = float(stake_m.loc[active].sum())

    complete = active & sigma.notna() & declared.notna() & live_pledge.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    live_a = live_pledge[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    stake_a = stake_m[complete].to_numpy(dtype=float)
    pledge_met = (live_a >= declared_a) & (sigma_a > 0)
    f_a = np.where(
        pledge_met,
        np.maximum(
            gross_pool_reward(
                sigma_a, declared_a, z0=z0, r_over_t=R / T, a0=a0
            ),
            0.0,
        ),
        0.0,
    )
    pi_a = operator_reward(f_a, cost_a, margin_a, live_a, sigma_a)
    ratio = pi_a / C_STAR_ADA
    r_class = np.array([classify_r(float(x)) for x in ratio])

    edges = np.arange(0.0, BIN_MAX_M + BIN_WIDTH_M, BIN_WIDTH_M)
    labels = [f"{int(lo)}–{int(hi)}" for lo, hi in zip(edges[:-1], edges[1:])]
    labels.append(f"≥{int(BIN_MAX_M)}")
    n_bins = len(labels)
    bin_idx = stake_bin_index(stake_a, edges)

    n_pools = np.zeros((len(R_ORDER), n_bins), dtype=float)
    stake_sum = np.zeros((len(R_ORDER), n_bins), dtype=float)
    r_index = {name: i for i, name in enumerate(R_ORDER)}
    for cls, b, s in zip(r_class, bin_idx, stake_a):
        n_pools[r_index[cls], b] += 1.0
        stake_sum[r_index[cls], b] += s

    n_tot = n_pools.sum(axis=0)
    s_tot = stake_sum.sum(axis=0)
    n_pct = np.zeros_like(n_pools)
    s_pct = np.zeros_like(stake_sum)
    with np.errstate(invalid="ignore", divide="ignore"):
        n_pct = np.where(n_tot > 0, 100.0 * n_pools / n_tot, 0.0)
        s_pct = np.where(s_tot > 0, 100.0 * stake_sum / s_tot, 0.0)

    rows = []
    for j, lab in enumerate(labels):
        for i, name in enumerate(R_ORDER):
            rows.append(
                {
                    "stake_bin_M_ADA": lab,
                    "r_class": name,
                    "n_pools": int(n_pools[i, j]),
                    "share_of_pools_in_bin_pct": float(n_pct[i, j]),
                    "agg_stake_M_ADA": float(stake_sum[i, j]),
                    "share_of_stake_in_bin_pct": float(s_pct[i, j]),
                }
            )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(13.2, 7.8), sharex=True)
    x = np.arange(n_bins)

    stacked_percentages(axes[0], x, n_pct, R_COLORS, R_LABELS, show_legend=True)
    axes[0].set_ylabel("% of pools in bin", fontsize=FONT_SIZE)
    axes[0].set_title("Viability mix of pools in each stake bin", fontsize=FONT_SIZE)

    stacked_percentages(axes[1], x, s_pct, R_COLORS, R_LABELS, show_legend=False)
    axes[1].set_ylabel("% of stake in bin", fontsize=FONT_SIZE)
    axes[1].set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)
    axes[1].set_title("Viability mix of aggregate stake in each bin", fontsize=FONT_SIZE)

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=FONT_SIZE - 2, rotation=45, ha="right")

    handles, labs = axes[0].get_legend_handles_labels()
    fig.suptitle(
        rf"Epoch 644 — stake bins by theoretical viability $r=\Pi_i/C^*$ ($k={k}$)"
        "\n"
        f"(Active $n={n_active}$; "
        rf"$C^*={C_STAR_ADA:.1f}$ ADA/epoch; "
        f"Total Active stake ${stake_active_m/1e3:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.tight_layout()
    fig.subplots_adjust(top=0.84, bottom=0.18, hspace=0.34)
    fig.legend(
        handles,
        labs,
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        frameon=False,
        fontsize=FONT_SIZE - 1,
        columnspacing=1.4,
        handletextpad=0.5,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"n_active={n_active}, C*={C_STAR_ADA:.2f}")
    print(f"Active with r: {int(n_tot.sum())} of {n_active}")
    for name, n in zip(R_LABELS, n_pools.sum(axis=1)):
        print(f"  {name}: n={int(n)}")


if __name__ == "__main__":
    main()
