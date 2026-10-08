#!/usr/bin/env python3
"""
Counterfactual redelegation at epoch 644 under k=1000, Active pools only.

Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in epochs 630–644.
Inactive pools are excluded as receivers (and none are donors: max stake 7.2M).
They appear as a leftmost orange bin, unchanged before vs after.

Donors: Active pools with σ > CAP (40M ADA); their entire stake redelegates.
Receivers: Active pools with 0 < σ ≤ CAP, ranked by member return per ADA:

    D_i = (1 - m_i) * max{f(σ_i, p_i) - c_i, 0} / σ_i

where p_i is declared pledge (`pool_update.active.pledge`), and f uses z0 = T/k
with k=1000.

Free space on receiver i is CAP - σ_i. Stake from oversized pools is poured
into receivers in rank order until each hits CAP.
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
OUT_CSV = DIR / "redelegation_rank_k1000_cap40M_epoch_644.csv"
OUT_SUMMARY = DIR / "redelegation_rank_k1000_cap40M_epoch_644_summary.csv"
OUT_BINS = DIR / "stake_distribution_by_bin_k1000_redelegation_epoch_644.csv"
OUT_PLOT = DIR / "stake_distribution_by_bin_k1000_redelegation_epoch_644.png"

FONT_SIZE = 12
K_NEW = 1000
CAP_ADA = 40e6
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
COLOR_BASE = "#4c78a8"
COLOR_NEW = "#e76f51"
COLOR_INACTIVE = "#e07a3d"


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
    if len(stake_m) == 0:
        z = np.zeros(len(labels))
        return labels, z, z
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
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")

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
    active_pledge = pd.to_numeric(df["live_pledge"], errors="coerce").fillna(0.0) / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0)
        / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    all_pools = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": sigma,
            "declared_pledge_ada": declared,
            "active_pledge_ada": active_pledge,
            "fixed_cost_ada": cost,
            "margin": margin,
            "inactive": df["in_union"] == 1,
        }
    )

    inactive = all_pools.loc[all_pools["inactive"]].copy()
    inactive["role"] = "inactive"
    inactive["desirability"] = np.nan
    inactive["free_space_ada"] = 0.0
    inactive["rank"] = np.nan
    inactive["received_ada"] = 0.0
    inactive["sigma_after_ada"] = inactive["sigma_ada"]

    base = all_pools.loc[~all_pools["inactive"]].copy()
    complete = base["margin"].notna() & base["fixed_cost_ada"].notna()
    n_incomplete = int((~complete).sum())
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

    receivers = (
        base[base["role"] == "receiver"]
        .sort_values(
            ["desirability", "sigma_ada", "pool_id"],
            ascending=[False, False, True],
        )
        .copy()
    )
    receivers["rank"] = np.arange(1, len(receivers) + 1)

    donors = base[base["role"] == "donor"].copy()
    donors["rank"] = np.nan
    stake_to_allocate = float(donors["sigma_ada"].sum())
    capacity = float(receivers["free_space_ada"].sum())
    capacity_dpos = float(
        receivers.loc[receivers["desirability"] > 0, "free_space_ada"].sum()
    )

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
    donors["sigma_after_ada"] = 0.0

    d0 = receivers["desirability"] <= 0
    n_d0 = int(d0.sum())
    n_d0_got = int((d0 & (receivers["received_ada"] > 0)).sum())
    ada_d0_got = float(receivers.loc[d0, "received_ada"].sum())
    n_dpos = int((receivers["desirability"] > 0).sum())
    n_dpos_got = int(
        ((receivers["desirability"] > 0) & (receivers["received_ada"] > 0)).sum()
    )

    out = pd.concat([receivers, donors], ignore_index=True)
    out["_role_ord"] = np.where(out["role"] == "receiver", 0, 1)
    out = out.sort_values(
        ["_role_ord", "rank", "desirability"], ascending=[True, True, False]
    ).drop(columns=["_role_ord"])
    out.to_csv(OUT_CSV, index=False)

    stake0 = base["sigma_ada"].to_numpy() / 1e6
    stake1 = out.loc[out["sigma_after_ada"] > 0, "sigma_after_ada"].to_numpy() / 1e6
    labels, c0, s0 = bin_counts_and_stake(stake0)
    _, c1, s1 = bin_counts_and_stake(stake1)
    n_inactive = int(len(inactive))

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

    n_after_active = int((out["sigma_after_ada"] > 0).sum())
    n_after_all = n_after_active + n_inactive
    n_filled = int(np.isclose(receivers["sigma_after_ada"], CAP_ADA).sum())

    summary = pd.DataFrame(
        [
            {"quantity": "k_new", "value": K_NEW},
            {"quantity": "T_ada", "value": T},
            {"quantity": "z0_k1000_ada", "value": z0},
            {"quantity": "cap_ada", "value": CAP_ADA},
            {"quantity": "n_active", "value": len(base)},
            {"quantity": "n_inactive", "value": n_inactive},
            {"quantity": "n_incomplete_active_dropped", "value": n_incomplete},
            {"quantity": "n_receivers", "value": len(receivers)},
            {"quantity": "n_donors", "value": len(donors)},
            {"quantity": "stake_to_allocate_ada", "value": stake_to_allocate},
            {"quantity": "receiver_capacity_ada", "value": capacity},
            {"quantity": "receiver_capacity_D_gt_0_ada", "value": capacity_dpos},
            {"quantity": "unallocated_ada", "value": remaining},
            {"quantity": "n_receivers_D_eq_0", "value": n_d0},
            {"quantity": "n_receivers_D_eq_0_that_received", "value": n_d0_got},
            {"quantity": "ada_received_by_D_eq_0", "value": ada_d0_got},
            {"quantity": "n_receivers_D_gt_0", "value": n_dpos},
            {"quantity": "n_receivers_D_gt_0_that_received", "value": n_dpos_got},
            {"quantity": "total_stake_active_before_ada", "value": float(base["sigma_ada"].sum())},
            {"quantity": "total_stake_active_after_ada", "value": float(out["sigma_after_ada"].sum())},
            {"quantity": "n_pools_after_active_sigma_gt_0", "value": n_after_active},
            {"quantity": "n_pools_after_including_inactive", "value": n_after_all},
            {"quantity": "n_receivers_filled_to_cap", "value": n_filled},
            {"quantity": "stake_inactive_ada", "value": float(inactive["sigma_ada"].sum())},
        ]
    )
    summary.to_csv(OUT_SUMMARY, index=False)

    x = np.arange(len(labels))
    width = 0.42
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 7.8), constrained_layout=True, sharex=True)
    ax_n, ax_s = axes

    ax_n.bar(
        x - width / 2, c0, width, color=COLOR_BASE, edgecolor="0.2", label="Current"
    )
    ax_n.bar(
        x + width / 2,
        c1,
        width,
        color=COLOR_NEW,
        edgecolor="0.2",
        label="After redelegation",
    )
    ax_n.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax_n.set_title("Pools per stake bin", fontsize=FONT_SIZE)
    ax_n.tick_params(labelsize=FONT_SIZE - 1)
    ax_n.grid(axis="y", alpha=0.25)
    ymax_n = max(float(np.max(c0)), float(np.max(c1))) * 1.18
    ax_n.set_ylim(0, ymax_n)
    for i, (n_cur, n_aft) in enumerate(zip(c0, c1)):
        for xpos, n in ((i - width / 2, n_cur), (i + width / 2, n_aft)):
            if n > 0:
                ax_n.text(
                    xpos,
                    n + ymax_n * 0.01,
                    str(int(n)),
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 3,
                )
    ax_n.legend(fontsize=FONT_SIZE - 1, frameon=False, loc="upper right")

    s0_b = s0 / 1e3  # M ADA → B ADA
    s1_b = s1 / 1e3
    ax_s.bar(
        x - width / 2, s0_b, width, color=COLOR_BASE, edgecolor="0.2", label="Current"
    )
    ax_s.bar(
        x + width / 2,
        s1_b,
        width,
        color=COLOR_NEW,
        edgecolor="0.2",
        label="After redelegation",
    )
    ax_s.set_ylabel("Aggregate stake (B ADA)", fontsize=FONT_SIZE)
    ax_s.set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)
    ax_s.set_title("Aggregate stake per bin", fontsize=FONT_SIZE)
    ax_s.tick_params(labelsize=FONT_SIZE - 1)
    ax_s.grid(axis="y", alpha=0.25)
    ax_s.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ymax_s = max(float(np.max(s0_b)), float(np.max(s1_b))) * 1.18
    ax_s.set_ylim(0, ymax_s)
    for i, (v_cur, v_aft) in enumerate(zip(s0_b, s1_b)):
        for xpos, v in ((i - width / 2, v_cur), (i + width / 2, v_aft)):
            if v > 0:
                ax_s.text(
                    xpos,
                    v + ymax_s * 0.01,
                    f"{v:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 3,
                )

    ax_s.set_xticks(x)
    ax_s.set_xticklabels(labels, fontsize=FONT_SIZE - 2, rotation=45, ha="right")

    fig.suptitle(
        "Epoch 644 — stake distribution: current vs after redelegation "
        r"($k=1000$) — Active pools only"
        "\n"
        rf"Donors $n={len(donors)}$ (${stake_to_allocate/1e9:.2f}$B redelegated); "
        rf"receivers with $D_i>0$ $n={n_dpos}$ "
        rf"(free space on ${capacity_dpos/1e9:.2f}$B)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_BINS}")
    print(f"Wrote {OUT_PLOT}")
    print(f"z0(k=1000)={z0/1e6:.3f}M ADA; cap={CAP_ADA/1e6:.0f}M")
    print(f"active={len(base)}, inactive={n_inactive}, incomplete_dropped={n_incomplete}")
    print(
        f"donors={len(donors)}, receivers={len(receivers)}, "
        f"to_allocate={stake_to_allocate/1e9:.3f}B, "
        f"capacity={capacity/1e9:.3f}B, "
        f"capacity_D>0={capacity_dpos/1e9:.3f}B, "
        f"unallocated={remaining/1e6:.2f}M"
    )
    print(
        f"D=0 receivers: n={n_d0}, of which received inflow: n={n_d0_got}, "
        f"ADA={ada_d0_got:.2f}"
    )
    print(
        f"D>0 receivers: n={n_dpos}, of which received inflow: n={n_dpos_got}"
    )
    print(
        f"filled_to_cap={n_filled}, n_after_active={n_after_active}, "
        f"n_after_incl_inactive={n_after_all}"
    )
    n0_cur, n0_aft = int(c0[1]), int(c1[1])
    print(f"active 0-5M bin: current n={n0_cur}, after n={n0_aft}")


if __name__ == "__main__":
    main()
