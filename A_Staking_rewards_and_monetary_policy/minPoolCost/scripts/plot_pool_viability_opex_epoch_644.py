#!/usr/bin/env python3
"""
Pool viability vs real OpEx (epoch 644) — category bars + losing/edge traits.

Assumptions
-----------
  OpEx per epoch C* = (667 / 6) / 0.15 ≈ 741.11 ADA
  r = leader_ADA / C*
  leader_ADA = epochs.0.data.reward.leader_lovelace / 1e6

Categories
  no_rewards  : leader = 0
  losing      : 0 < r < 1
  edge        : 1 ≤ r < 2
  comfortable : 2 ≤ r < 5
  strong      : r ≥ 5

Counterfactual declare c=75:
  Π(75) uses active pledge (`pledged`) in the operator share.

Writes
  pool_viability_opex_categories_epoch_644.png   (bar chart)
  pool_viability_losing_vs_edge_traits_epoch_644.png
  pool_viability_opex_epoch_644.csv
  pool_viability_opex_summary_epoch_644.csv

Usage:
  python3 plot_pool_viability_opex_epoch_644.py
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
OUT_BARS = DIR / "pool_viability_opex_categories_epoch_644.png"
OUT_TRAITS = DIR / "pool_viability_losing_vs_edge_traits_epoch_644.png"
OUT_CSV = DIR / "pool_viability_opex_epoch_644.csv"
OUT_SUMMARY = DIR / "pool_viability_opex_summary_epoch_644.csv"
# keep older combined figure name updated too
OUT_COMBINED = DIR / "pool_viability_opex_epoch_644.png"

FONT_SIZE = 12
OPEX_EPOCH_USD = 667.0 / 6.0
ADA_USD = 0.15
C_STAR_ADA = OPEX_EPOCH_USD / ADA_USD
C75 = 75.0

COLOR_LOSING = "#d62828"
COLOR_EDGE = "#e76f51"
COLOR_COMF = "#4c78a8"
COLOR_STRONG = "#2a9d8f"
COLOR_NONE = "#adb5bd"


def operator_reward(
    f: np.ndarray, m: np.ndarray, p_hat: np.ndarray, sigma: np.ndarray, c: float
) -> np.ndarray:
    share = m + (1.0 - m) * np.clip(
        np.divide(p_hat, sigma, out=np.zeros_like(p_hat), where=sigma > 0), 0.0, 1.0
    )
    return np.where(f > c, c + (f - c) * share, f)


def classify_ratio(r: float) -> str:
    if not np.isfinite(r) or r <= 0:
        return "no_rewards"
    if r < 1.0:
        return "losing"
    if r < 2.0:
        return "edge"
    if r < 5.0:
        return "comfortable"
    return "strong"


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    leader = pd.to_numeric(df["epochs.0.data.reward.leader_lovelace"], errors="coerce").fillna(0.0) / 1e6
    member = pd.to_numeric(df["epochs.0.data.reward.member_lovelace"], errors="coerce").fillna(0.0) / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0)
    p_decl = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0) / 1e6
    p_hat = pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6  # active pledge
    stake = pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce").fillna(0.0) / 1e6
    declared = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    delegators = pd.to_numeric(df["epochs.0.data.delegators"], errors="coerce")
    blocks = pd.to_numeric(df["epochs.0.data.block.minted"], errors="coerce").fillna(0.0)

    f = leader + member
    pi75 = operator_reward(
        f.to_numpy(), margin.to_numpy(), p_hat.to_numpy(), stake.to_numpy(), C75
    )
    ratio = leader / C_STAR_ADA

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "pool_ticker": df["pool_name.ticker"],
            "declared_fixed_cost_ada": declared,
            "margin": margin,
            "declared_pledge_ada": p_decl,
            "active_pledge_ada": p_hat,
            "epoch_stake_ada": stake,
            "delegators": delegators,
            "blocks_minted": blocks,
            "leader_reward_ada": leader,
            "member_reward_ada": member,
            "f_ada": f,
            "opex_epoch_ada": C_STAR_ADA,
            "coverage_ratio": ratio,
            "category": [classify_ratio(float(x)) for x in ratio],
            "viable_now": leader >= C_STAR_ADA,
            "operator_reward_c75_ada": pi75,
            "viable_at_declared_c75": pi75 >= C_STAR_ADA,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    counts = out["category"].value_counts()
    n_rewarded = int((out["leader_reward_ada"] > 0).sum())
    n_viable_now = int(out["viable_now"].sum())
    # among pools currently viable, how many remain viable at c=75
    currently_viable = out["viable_now"]
    n_remain_75 = int((currently_viable & out["viable_at_declared_c75"]).sum())
    n_lose_75 = int((currently_viable & ~out["viable_at_declared_c75"]).sum())

    summary = pd.DataFrame(
        [
            {"quantity": "opex_epoch_usd", "value": OPEX_EPOCH_USD},
            {"quantity": "ada_usd", "value": ADA_USD},
            {"quantity": "opex_epoch_ada_Cstar", "value": C_STAR_ADA},
            {"quantity": "n_pools", "value": len(out)},
            {"quantity": "n_no_rewards", "value": int(counts.get("no_rewards", 0))},
            {"quantity": "n_losing", "value": int(counts.get("losing", 0))},
            {"quantity": "n_edge_1_to_2x", "value": int(counts.get("edge", 0))},
            {"quantity": "n_comfortable_2_to_5x", "value": int(counts.get("comfortable", 0))},
            {"quantity": "n_strong_ge_5x", "value": int(counts.get("strong", 0))},
            {"quantity": "n_rewarded", "value": n_rewarded},
            {"quantity": "n_viable_now", "value": n_viable_now},
            {"quantity": "n_viable_now_remain_at_c75", "value": n_remain_75},
            {"quantity": "n_viable_now_lose_at_c75", "value": n_lose_75},
        ]
    )
    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"C* = {C_STAR_ADA:.4f} ADA/epoch")
    print(summary.to_string(index=False))

    # ------------------------------------------------------------------ bars
    cat_order = ["no_rewards", "losing", "edge", "comfortable", "strong"]
    cat_labels = [
        "No rewards",
        r"Losing" "\n" r"($r<1$)",
        r"Edge" "\n" r"($1\leq r<2$)",
        r"Comfortable" "\n" r"($2\leq r<5$)",
        r"Strong" "\n" r"($r\geq 5$)",
    ]
    cat_colors = [COLOR_NONE, COLOR_LOSING, COLOR_EDGE, COLOR_COMF, COLOR_STRONG]
    heights = [int(counts.get(c, 0)) for c in cat_order]

    fig, ax = plt.subplots(figsize=(9.5, 5.2), constrained_layout=True)
    x = np.arange(len(cat_order))
    ax.bar(x, heights, color=cat_colors, edgecolor="white", width=0.72)
    for xi, h in zip(x, heights):
        ax.text(xi, h + max(heights) * 0.012, str(h), ha="center", va="bottom", fontsize=FONT_SIZE)
    ax.set_xticks(x)
    ax.set_xticklabels(cat_labels, fontsize=FONT_SIZE)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        "Epoch 644 — viability vs OpEx\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.text(
        0.98,
        0.97,
        f"Rewarded pools: {n_rewarded}\n"
        f"Cover OpEx now: {n_viable_now}\n"
        f"If declare $c=75$ ADA:\n"
        f"  remain viable: {n_remain_75}\n"
        f"  lose viability: {n_lose_75}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE,
        color="0.2",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="0.75", alpha=0.95),
    )
    fig.savefig(OUT_BARS, dpi=160)
    print(f"wrote {OUT_BARS}")

    # also refresh combined (bars + ratio hist) for continuity
    fig2, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), constrained_layout=True)
    rewarded = out[out["leader_reward_ada"] > 0]
    r = rewarded["coverage_ratio"].to_numpy()
    bins = np.concatenate(
        [np.arange(0.0, 5.25, 0.25), np.array([6, 8, 10, 15, 20, 30, 50, max(50.0, float(r.max()) + 1)])]
    )
    axes[0].hist(r, bins=bins, color=COLOR_COMF, edgecolor="white", linewidth=0.4)
    axes[0].axvline(1.0, color=COLOR_LOSING, linewidth=1.5, label=r"$r=1$")
    axes[0].axvline(2.0, color=COLOR_EDGE, linewidth=1.5, linestyle="--", label=r"$r=2$")
    axes[0].axvline(5.0, color=COLOR_STRONG, linewidth=1.5, linestyle=":", label=r"$r=5$")
    axes[0].set_xlabel(r"Coverage ratio $r=\Pi_i/C^*$", fontsize=FONT_SIZE)
    axes[0].set_ylabel("Number of pools", fontsize=FONT_SIZE)
    axes[0].set_title(f"Rewarded pools (n={n_rewarded})", fontsize=FONT_SIZE)
    axes[0].tick_params(axis="both", labelsize=FONT_SIZE)
    axes[0].set_xlim(0.0, min(20.0, max(5.0, float(np.percentile(r, 99)) * 1.05)))
    axes[0].legend(frameon=False, fontsize=FONT_SIZE)

    axes[1].bar(x, heights, color=cat_colors, edgecolor="white", width=0.72)
    for xi, h in zip(x, heights):
        axes[1].text(xi, h + max(heights) * 0.01, str(h), ha="center", va="bottom", fontsize=FONT_SIZE)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(cat_labels, fontsize=FONT_SIZE)
    axes[1].set_ylabel("Number of pools", fontsize=FONT_SIZE)
    axes[1].set_title("Viability categories", fontsize=FONT_SIZE)
    axes[1].tick_params(axis="both", labelsize=FONT_SIZE)
    axes[1].text(
        0.98,
        0.98,
        f"Cover OpEx now: {n_viable_now}/{n_rewarded}\n"
        f"At $c=75$: remain {n_remain_75}, lose {n_lose_75}",
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE,
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="0.8", alpha=0.95),
    )
    fig2.suptitle(
        "Epoch 644 — viability vs OpEx\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$)",
        fontsize=FONT_SIZE,
    )
    fig2.savefig(OUT_COMBINED, dpi=160)
    print(f"wrote {OUT_COMBINED}")

    # ------------------------------------------------ losing vs edge traits
    losing = out[out["category"] == "losing"]
    edge = out[out["category"] == "edge"]
    print("\nLosing vs edge medians:")
    for name, col, scale in [
        ("stake_ADA", "epoch_stake_ada", 1),
        ("active_pledge_ADA", "active_pledge_ada", 1),
        ("margin", "margin", 1),
        ("declared_c", "declared_fixed_cost_ada", 1),
        ("blocks", "blocks_minted", 1),
        ("delegators", "delegators", 1),
        ("leader_ADA", "leader_reward_ada", 1),
        ("r", "coverage_ratio", 1),
    ]:
        print(
            f"  {name}: losing={losing[col].median():.4g}, edge={edge[col].median():.4g}"
        )

    fig3, axes = plt.subplots(3, 3, figsize=(12.5, 9.5), constrained_layout=True)

    def box_pair(ax, data, ylabel: str, title: str) -> None:
        bp = ax.boxplot(
            data,
            tick_labels=[f"Losing\n(n={len(losing)})", f"Edge\n(n={len(edge)})"],
            patch_artist=True,
            widths=0.55,
            showfliers=False,
        )
        for patch, color in zip(bp["boxes"], [COLOR_LOSING, COLOR_EDGE]):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)

    # Stake: linear M ADA
    box_pair(
        axes[0, 0],
        [
            (losing["epoch_stake_ada"] / 1e6).dropna().to_numpy(),
            (edge["epoch_stake_ada"] / 1e6).dropna().to_numpy(),
        ],
        "Epoch stake (M ADA)",
        "Epoch stake",
    )
    # Pledges: linear k ADA (not log)
    box_pair(
        axes[0, 1],
        [
            (losing["active_pledge_ada"] / 1e3).dropna().to_numpy(),
            (edge["active_pledge_ada"] / 1e3).dropna().to_numpy(),
        ],
        "Active pledge (k ADA)",
        "Active pledge",
    )
    box_pair(
        axes[0, 2],
        [
            (losing["declared_pledge_ada"] / 1e3).dropna().to_numpy(),
            (edge["declared_pledge_ada"] / 1e3).dropna().to_numpy(),
        ],
        "Declared pledge (k ADA)",
        "Declared pledge",
    )
    box_pair(
        axes[1, 0],
        [losing["margin"].dropna().to_numpy(), edge["margin"].dropna().to_numpy()],
        "Declared margin m",
        "Margin",
    )
    box_pair(
        axes[1, 1],
        [
            losing["blocks_minted"].dropna().to_numpy(),
            edge["blocks_minted"].dropna().to_numpy(),
        ],
        "Blocks minted (epoch)",
        "Blocks",
    )
    box_pair(
        axes[1, 2],
        [losing["delegators"].dropna().to_numpy(), edge["delegators"].dropna().to_numpy()],
        "Delegators",
        "Delegators",
    )
    box_pair(
        axes[2, 0],
        [
            losing["declared_fixed_cost_ada"].dropna().to_numpy(),
            edge["declared_fixed_cost_ada"].dropna().to_numpy(),
        ],
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
    )
    # Hide unused panels
    axes[2, 1].axis("off")
    axes[2, 2].axis("off")

    fig3.suptitle(
        "Epoch 644 — characteristics of Losing vs Edge pools\n"
        rf"($r=\Pi_i/C^*$, $C^*={C_STAR_ADA:.1f}$ ADA/epoch)",
        fontsize=FONT_SIZE,
    )
    fig3.savefig(OUT_TRAITS, dpi=160)
    print(f"wrote {OUT_TRAITS}")
    print(
        "declared pledge medians (ADA): "
        f"losing={losing['declared_pledge_ada'].median():.4g}, "
        f"edge={edge['declared_pledge_ada'].median():.4g}"
    )
    print(
        "declared fixed cost medians: "
        f"losing={losing['declared_fixed_cost_ada'].median():.4g}, "
        f"edge={edge['declared_fixed_cost_ada'].median():.4g}"
    )


if __name__ == "__main__":
    main()
