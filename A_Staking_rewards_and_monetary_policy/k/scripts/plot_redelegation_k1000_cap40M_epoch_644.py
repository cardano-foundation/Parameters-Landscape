#!/usr/bin/env python3
"""
Counterfactual redelegation at epoch 644 under k=1000.

Assume pools with σ > CAP (40M ADA) must redelegate their entire stake.
Receiving pools are those with 0 < σ ≤ CAP, ranked by member return per ADA:

    D_i = (1 - m_i) * max{f(σ_i, p_i) - c_i, 0} / σ_i

where p_i is declared pledge (`pool_update.active.pledge`), and f uses z0 = T/k
with k=1000.

Free space on receiver i is CAP - σ_i. Stake from oversized pools is poured
into receivers in rank order until each hits CAP.

Writes:
  - ranked receiver CSV (+ donor rows)
  - overlaid bin distribution plot (current vs post-reallocation)
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
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_CSV = DIR / "redelegation_rank_k1000_cap40M_epoch_644.csv"
OUT_SUMMARY = DIR / "redelegation_rank_k1000_cap40M_epoch_644_summary.csv"
OUT_BINS = DIR / "stake_distribution_by_bin_k1000_redelegation_epoch_644.csv"
OUT_PLOT = DIR / "stake_distribution_by_bin_k1000_redelegation_epoch_644.png"

FONT_SIZE = 12
K_NEW = 1000
CAP_ADA = 40e6  # redelegation soft cap (near z0≈38.8M)
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
COLOR_BASE = "#4c78a8"
COLOR_NEW = "#e76f51"


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def member_return_per_ada(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)


def bin_counts_and_stake(stake_m: np.ndarray) -> tuple[list[str], np.ndarray, np.ndarray]:
    edges = np.arange(0.0, BIN_MAX_M + BIN_WIDTH_M, BIN_WIDTH_M)
    labels = [f"{int(lo)}–{int(hi)}" for lo, hi in zip(edges[:-1], edges[1:])]
    labels.append(f"≥{int(BIN_MAX_M)}")
    idx = np.digitize(stake_m, edges, right=False) - 1
    idx = np.clip(idx, 0, len(labels) - 1)
    idx = np.where(stake_m >= BIN_MAX_M, len(labels) - 1, idx)
    counts = np.bincount(idx, minlength=len(labels))
    stake_sum = np.bincount(idx, weights=stake_m, minlength=len(labels))
    return labels, counts.astype(float), stake_sum.astype(float)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = T / K_NEW
    r_over_t = R / T

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(
            df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
            errors="coerce",
        ).fillna(0.0)
        / 1e6
    )
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0) / 1e6
    )
    active_pledge = pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0)
        / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    base = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": sigma,
            "declared_pledge_ada": declared,
            "active_pledge_ada": active_pledge,
            "fixed_cost_ada": cost,
            "margin": margin,
        }
    )
    base = base[base["sigma_ada"] > 0].copy()
    complete = base["margin"].notna() & base["fixed_cost_ada"].notna()
    base = base.loc[complete].copy()

    f = gross_pool_reward(
        base["sigma_ada"].to_numpy(),
        base["declared_pledge_ada"].to_numpy(),
        z0=z0,
        r_over_t=r_over_t,
        a0=a0,
    )
    base["f_ada_k1000"] = f
    base["desirability"] = member_return_per_ada(
        base["sigma_ada"].to_numpy(),
        f,
        base["fixed_cost_ada"].to_numpy(),
        base["margin"].to_numpy(),
    )
    base["role"] = np.where(base["sigma_ada"] > CAP_ADA, "donor", "receiver")
    base["free_space_ada"] = np.where(
        base["role"] == "receiver",
        np.maximum(CAP_ADA - base["sigma_ada"], 0.0),
        0.0,
    )

    receivers = base[base["role"] == "receiver"].sort_values(
        ["desirability", "sigma_ada", "pool_id"],
        ascending=[False, False, True],
    ).copy()
    receivers["rank"] = np.arange(1, len(receivers) + 1)

    donors = base[base["role"] == "donor"].copy()
    donors["rank"] = np.nan
    stake_to_allocate = float(donors["sigma_ada"].sum())
    capacity = float(receivers["free_space_ada"].sum())

    received = np.zeros(len(receivers), dtype=float)
    remaining = stake_to_allocate
    for i, free in enumerate(receivers["free_space_ada"].to_numpy()):
        if remaining <= 0:
            break
        take = min(free, remaining)
        received[i] = take
        remaining -= take

    receivers["received_ada"] = received
    receivers["sigma_after_ada"] = receivers["sigma_ada"] + receivers["received_ada"]
    donors["received_ada"] = 0.0
    donors["sigma_after_ada"] = 0.0  # entire stake redelegated away

    out = pd.concat([receivers, donors], ignore_index=True)
    # Receivers first (by rank), then donors
    out["_role_ord"] = np.where(out["role"] == "receiver", 0, 1)
    out = out.sort_values(
        ["_role_ord", "rank", "desirability"], ascending=[True, True, False]
    ).drop(columns=["_role_ord"])
    out.to_csv(OUT_CSV, index=False)

    # --- Distributions ---
    stake0 = base["sigma_ada"].to_numpy() / 1e6  # M ADA
    stake1 = out.loc[out["sigma_after_ada"] > 0, "sigma_after_ada"].to_numpy() / 1e6
    labels, c0, s0 = bin_counts_and_stake(stake0)
    _, c1, s1 = bin_counts_and_stake(stake1)

    bin_rows = []
    for i, lab in enumerate(labels):
        bin_rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools_current": int(c0[i]),
                "n_pools_after": int(c1[i]),
                "agg_stake_current_M_ADA": float(s0[i]),
                "agg_stake_after_M_ADA": float(s1[i]),
            }
        )
    pd.DataFrame(bin_rows).to_csv(OUT_BINS, index=False)

    summary = pd.DataFrame(
        [
            {"quantity": "k_new", "value": K_NEW},
            {"quantity": "T_ada", "value": T},
            {"quantity": "z0_k1000_ada", "value": z0},
            {"quantity": "cap_ada", "value": CAP_ADA},
            {"quantity": "declared_pledge_column", "value": "pool_update.active.pledge"},
            {"quantity": "n_pools_sigma_gt_0_complete", "value": len(base)},
            {"quantity": "n_receivers", "value": len(receivers)},
            {"quantity": "n_donors", "value": len(donors)},
            {"quantity": "stake_to_allocate_ada", "value": stake_to_allocate},
            {"quantity": "receiver_capacity_ada", "value": capacity},
            {"quantity": "unallocated_ada", "value": remaining},
            {"quantity": "total_stake_before_ada", "value": float(base["sigma_ada"].sum())},
            {
                "quantity": "total_stake_after_ada",
                "value": float(out["sigma_after_ada"].sum()),
            },
            {
                "quantity": "n_pools_after_sigma_gt_0",
                "value": int((out["sigma_after_ada"] > 0).sum()),
            },
            {
                "quantity": "n_receivers_filled_to_cap",
                "value": int(np.isclose(receivers["sigma_after_ada"], CAP_ADA).sum()),
            },
        ]
    )
    summary.to_csv(OUT_SUMMARY, index=False)

    # --- Plot: broken y-axis for pool counts; stake panel below ---
    x = np.arange(len(labels))
    width = 0.42

    fig = plt.figure(figsize=(12.5, 8.0), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.05, 1.35, 2.4])
    ax_top = fig.add_subplot(gs[0, 0])      # high pool counts (first bin)
    ax_bot = fig.add_subplot(gs[1, 0], sharex=ax_top)  # low pool counts
    ax_stake = fig.add_subplot(gs[2, 0], sharex=ax_top)

    y_lo_max = 550.0
    y_hi_min = 1750.0
    y_hi_max = max(float(np.max(c0)), float(np.max(c1)), 2000.0) * 1.02
    y_hi_max = max(y_hi_max, 2100.0)

    for ax in (ax_top, ax_bot):
        ax.bar(
            x - width / 2, c0, width, color=COLOR_BASE, edgecolor="0.2", label="Current"
        )
        ax.bar(
            x + width / 2,
            c1,
            width,
            color=COLOR_NEW,
            edgecolor="0.2",
            label="After redelegation",
        )
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(labelsize=FONT_SIZE - 1)

    ax_top.set_ylim(y_hi_min, y_hi_max)
    ax_bot.set_ylim(0.0, y_lo_max)
    ax_top.spines["bottom"].set_visible(False)
    ax_bot.spines["top"].set_visible(False)
    ax_top.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    ax_bot.xaxis.tick_bottom()

    # Diagonal break marks
    d = 0.015
    kwargs = dict(transform=ax_top.transAxes, color="0.2", clip_on=False, linewidth=1.0)
    ax_top.plot((-d, +d), (-d, +d), **kwargs)
    ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)
    kwargs.update(transform=ax_bot.transAxes)
    ax_bot.plot((-d, +d), (1 - d, 1 + d), **kwargs)
    ax_bot.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

    # Count labels on the visible segment of each bar
    for i, (n_cur, n_aft) in enumerate(zip(c0, c1)):
        for xpos, n, color in (
            (i - width / 2, n_cur, COLOR_BASE),
            (i + width / 2, n_aft, COLOR_NEW),
        ):
            if n <= 0:
                continue
            if n >= y_hi_min:
                ax_top.text(
                    xpos,
                    n + (y_hi_max - y_hi_min) * 0.02,
                    str(int(n)),
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 3,
                    color="0.15",
                )
            elif n <= y_lo_max:
                ax_bot.text(
                    xpos,
                    n + y_lo_max * 0.02,
                    str(int(n)),
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 3,
                    color="0.15",
                )

    ax_top.set_title("Pools per stake bin (broken y-axis)", fontsize=FONT_SIZE)
    ax_bot.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax_top.legend(fontsize=FONT_SIZE - 1, frameon=False, loc="upper right")

    ax_stake.bar(
        x - width / 2, s0, width, color=COLOR_BASE, edgecolor="0.2", label="Current"
    )
    ax_stake.bar(
        x + width / 2,
        s1,
        width,
        color=COLOR_NEW,
        edgecolor="0.2",
        label="After redelegation",
    )
    ax_stake.set_ylabel("Aggregate stake (M ADA)", fontsize=FONT_SIZE)
    ax_stake.set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)
    ax_stake.set_title("Aggregate stake per bin", fontsize=FONT_SIZE)
    ax_stake.tick_params(labelsize=FONT_SIZE - 1)
    ax_stake.grid(axis="y", alpha=0.25)
    ax_stake.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ax_stake.set_xticks(x)
    ax_stake.set_xticklabels(labels, fontsize=FONT_SIZE - 2, rotation=45, ha="right")

    n_after = int((out["sigma_after_ada"] > 0).sum())
    fig.suptitle(
        rf"Epoch 644 — stake distribution: current vs $k={K_NEW}$ redelegation "
        rf"(cap ${CAP_ADA/1e6:.0f}$M $\approx z_0={z0/1e6:.1f}$M)"
        "\n"
        rf"Donors $\sigma>40$M: $n={len(donors)}$ "
        rf"(${stake_to_allocate/1e9:.2f}$B redelegated); "
        rf"receivers $n={len(receivers)}$; "
        rf"pools after: $n={n_after}$; "
        rf"unallocated ${remaining/1e6:.1f}$M",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_BINS}")
    print(f"Wrote {OUT_PLOT}")
    print(f"Declared pledge column: pool_update.active.pledge")
    print(f"z0(k=1000)={z0/1e6:.3f}M ADA; cap={CAP_ADA/1e6:.0f}M")
    print(
        f"donors={len(donors)}, receivers={len(receivers)}, "
        f"to_allocate={stake_to_allocate/1e9:.3f}B, "
        f"capacity={capacity/1e9:.3f}B, unallocated={remaining/1e6:.2f}M"
    )
    print(
        f"total before={base['sigma_ada'].sum()/1e9:.6f}B, "
        f"after={out['sigma_after_ada'].sum()/1e9:.6f}B, "
        f"n_after={n_after}"
    )


if __name__ == "__main__":
    main()
