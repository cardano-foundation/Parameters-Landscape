#!/usr/bin/env python3
"""Epoch 644 — interaction effects on desirability ranking (2x2 panel).

Same as the base interaction-effects plot but includes ALL pledge-met pools,
with oversaturated pools (sigma > z0(1000)) shown in red.

Desirability: D_i = (1 - m_i) max{f(sigma_i, p_i) - c_i, 0} / sigma_i
f uses sigma as-is (no cap at z0).
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
OUT_PNG = DIR / "desirability_rank_interaction_with_oversaturated_epoch_644.png"

FONT_SIZE = 12
K_BASE = 500
K_NEW = 1000
C_FORCE_170 = 170.0
C_FORCE_75 = 75.0


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


def desirability(
    sigma: np.ndarray,
    declared: np.ndarray,
    active: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (D, pledge_met)."""
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross_pool_reward(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    d = np.where(sigma > 0, pot / sigma, 0.0)
    d = np.where(pledge_met, d, 0.0)
    return d, pledge_met


def ranks_from_d(d: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(-d)) + 1


def scatter_panel(
    ax: plt.Axes,
    d_base: np.ndarray,
    d_alt: np.ndarray,
    mask: np.ndarray,
    oversaturated: np.ndarray,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
) -> None:
    db = d_base[mask]
    da = d_alt[mask]
    over = oversaturated[mask]
    pos = (db > 0) | (da > 0)
    db = db[pos]
    da = da[pos]
    over = over[pos]
    rb = ranks_from_d(db)
    ra = ranks_from_d(da)

    unsat = ~over
    ax.scatter(rb[unsat], ra[unsat], s=6, alpha=0.35, color="#4c78a8", label="Unsaturated")
    ax.scatter(rb[over], ra[over], s=12, alpha=0.6, color="#dc2626", label="Oversaturated")
    lim = int(max(rb.max(), ra.max())) + 10
    ax.plot([1, lim], [1, lim], color="grey", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

    corr = float(np.corrcoef(rb, ra)[0, 1]) if len(rb) > 1 else float("nan")
    changes = np.abs(ra.astype(int) - rb.astype(int))
    ax.text(
        0.05,
        0.95,
        f"Rank corr: {corr:.4f}\n"
        f"Mean |Δrank|: {changes.mean():.1f}\n"
        f"n={len(rb)} (oversat: {int(over.sum())})",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )
    ax.legend(fontsize=FONT_SIZE - 1, loc="lower right", markerscale=1.5)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_500 = T / K_BASE
    z0_1000 = T / K_NEW

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(
            df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
            errors="coerce",
        ).fillna(0.0)
        / 1e6
    ).to_numpy(dtype=float)
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0) / 1e6
    ).to_numpy(dtype=float)
    active = (
        pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6
    ).to_numpy(dtype=float)
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0) / 1e6
    ).to_numpy(dtype=float)
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0).to_numpy(
        dtype=float
    )

    # Baseline: k=500, declared c_i
    d_base, pledge_met = desirability(
        sigma, declared, active, cost, margin, z0=z0_500, r_over_t=r_over_t, a0=a0
    )

    # A: k=1000, same c_i
    d_a, _ = desirability(
        sigma, declared, active, cost, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    # B: k=1000, c_i = 170 for all
    cost_170 = np.full_like(cost, C_FORCE_170)
    d_b, _ = desirability(
        sigma, declared, active, cost_170, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    # C: k=500, c_i = 75 for all
    cost_75 = np.full_like(cost, C_FORCE_75)
    d_c, _ = desirability(
        sigma, declared, active, cost_75, margin, z0=z0_500, r_over_t=r_over_t, a0=a0
    )

    # D: k=1000, c_i = 75 for all
    d_d, _ = desirability(
        sigma, declared, active, cost_75, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    oversaturated_k1000 = sigma > z0_1000
    mask_all = pledge_met

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 12.0), constrained_layout=True)

    scatter_panel(
        axes[0, 0],
        d_base, d_a, mask_all, oversaturated_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, declared $c_i$",
        title=r"A: $k\!:\,500\to1000$, $c_i$ unchanged",
    )
    scatter_panel(
        axes[0, 1],
        d_base, d_b, mask_all, oversaturated_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, $c_i=170$",
        title=r"B: $k\!:\,500\to1000$, all $c_i\to170$",
    )
    scatter_panel(
        axes[1, 0],
        d_base, d_c, mask_all, oversaturated_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=500$, $c_i=75$",
        title=r"C: $k=500$, all $c_i\to75$",
    )
    scatter_panel(
        axes[1, 1],
        d_base, d_d, mask_all, oversaturated_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, $c_i=75$",
        title=r"D: $k\!:\,500\to1000$, all $c_i\to75$",
    )

    fig.suptitle(
        "Epoch 644 — desirability ranking (oversaturated in red)\n"
        + rf"$R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B, $a_0={a0}$, "
        + rf"$z_0(500)={z0_500/1e6:.1f}$M, $z_0(1000)={z0_1000/1e6:.1f}$M",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    n_over = int((pledge_met & oversaturated_k1000).sum())
    print(f"Oversaturated pledge-met pools: {n_over}")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
