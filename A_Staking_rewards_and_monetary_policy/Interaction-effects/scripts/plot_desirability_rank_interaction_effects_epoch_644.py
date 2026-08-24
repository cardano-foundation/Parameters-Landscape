#!/usr/bin/env python3
"""Epoch 644 — interaction effects on desirability ranking (2x2 panel).

Baseline: k=500, declared c_i (current minPoolCost=170 regime).

Comparisons (y-axis ranks vs baseline x-axis ranks):
  A) k=1000, same c_i — only pools unsaturated under k=1000 (σ ≤ T/1000)
  B) k=1000, all c_i → 170 — same unsaturated filter
  C) k=500, all c_i → 75
  D) k=1000, all c_i → 75 — same unsaturated filter

Desirability: D_i = (1 - m_i) max{f(σ_i, p_i) - c_i, 0} / σ_i

R, T, a0 from f_reward_params_epoch_644.json.
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
OUT_PNG = DIR / "desirability_rank_interaction_effects_epoch_644.png"
OUT_CSV = DIR / "desirability_rank_interaction_effects_epoch_644.csv"
OUT_MD = DIR / "desirability_rank_interaction_effects_epoch_644.md"

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
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (D, f, pledge_met)."""
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross_pool_reward(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    d = np.where(sigma > 0, pot / sigma, 0.0)
    d = np.where(pledge_met, d, 0.0)
    return d, f, pledge_met


def ranks_from_d(d: np.ndarray) -> np.ndarray:
    return np.argsort(np.argsort(-d)) + 1


def scatter_panel(
    ax: plt.Axes,
    d_base: np.ndarray,
    d_alt: np.ndarray,
    mask: np.ndarray,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
) -> dict:
    db = d_base[mask]
    da = d_alt[mask]
    # Keep pools with positive desirability in at least one scenario
    pos = (db > 0) | (da > 0)
    db = db[pos]
    da = da[pos]
    rb = ranks_from_d(db)
    ra = ranks_from_d(da)

    ax.scatter(rb, ra, s=6, alpha=0.35, color="#4c78a8")
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
        f"Max |Δrank|: {changes.max()}\n"
        f"n={len(rb)}",
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
    return {
        "n": int(len(rb)),
        "rank_corr": corr,
        "mean_abs_rank_change": float(changes.mean()) if len(changes) else float("nan"),
        "max_abs_rank_change": int(changes.max()) if len(changes) else 0,
    }


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
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0)
        / 1e6
    ).to_numpy(dtype=float)
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0).to_numpy(
        dtype=float
    )

    # Baseline: k=500, declared c_i
    d_base, f_base, pledge_met = desirability(
        sigma, declared, active, cost, margin, z0=z0_500, r_over_t=r_over_t, a0=a0
    )

    # A: k=1000, same c_i
    d_a, f_a, _ = desirability(
        sigma, declared, active, cost, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    # B: k=1000, c_i = 170 for all
    cost_170 = np.full_like(cost, C_FORCE_170)
    d_b, f_b, _ = desirability(
        sigma, declared, active, cost_170, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    # C: k=500, c_i = 75 for all
    cost_75 = np.full_like(cost, C_FORCE_75)
    d_c, f_c, _ = desirability(
        sigma, declared, active, cost_75, margin, z0=z0_500, r_over_t=r_over_t, a0=a0
    )

    # D: k=1000, c_i = 75 for all
    d_d, f_d, _ = desirability(
        sigma, declared, active, cost_75, margin, z0=z0_1000, r_over_t=r_over_t, a0=a0
    )

    # Unsaturated under k=1000: can absorb redelegation / stay below new saturation
    unsaturated_k1000 = sigma <= z0_1000
    mask_k1000 = pledge_met & unsaturated_k1000
    mask_k500 = pledge_met

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": sigma,
            "declared_pledge_ada": declared,
            "active_pledge_ada": active,
            "margin": margin,
            "fixed_cost_ada": cost,
            "pledge_met": pledge_met,
            "unsaturated_k1000": unsaturated_k1000,
            "f_base_k500_c_declared": f_base,
            "D_base_k500_c_declared": d_base,
            "f_A_k1000_c_declared": f_a,
            "D_A_k1000_c_declared": d_a,
            "f_B_k1000_c170": f_b,
            "D_B_k1000_c170": d_b,
            "f_C_k500_c75": f_c,
            "D_C_k500_c75": d_c,
            "f_D_k1000_c75": f_d,
            "D_D_k1000_c75": d_d,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 12.0), constrained_layout=True)

    stats = {}
    stats["A"] = scatter_panel(
        axes[0, 0],
        d_base,
        d_a,
        mask_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, declared $c_i$",
        title=r"A: $k\!:\,500\to1000$, $c_i$ unchanged"
        "\n"
        r"(unsaturated under $k=1000$ only)",
    )
    stats["B"] = scatter_panel(
        axes[0, 1],
        d_base,
        d_b,
        mask_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, $c_i=170$",
        title=r"B: $k\!:\,500\to1000$, all $c_i\to170$"
        "\n"
        r"(unsaturated under $k=1000$ only)",
    )
    stats["C"] = scatter_panel(
        axes[1, 0],
        d_base,
        d_c,
        mask_k500,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=500$, $c_i=75$",
        title=r"C: $k=500$, all $c_i\to75$",
    )
    stats["D"] = scatter_panel(
        axes[1, 1],
        d_base,
        d_d,
        mask_k1000,
        xlabel=r"Rank: $k=500$, declared $c_i$",
        ylabel=r"Rank: $k=1000$, $c_i=75$",
        title=r"D: $k\!:\,500\to1000$, all $c_i\to75$"
        "\n"
        r"(unsaturated under $k=1000$ only)",
    )

    fig.suptitle(
        "Epoch 644 — desirability ranking under interaction effects\n"
        + rf"$D_i=(1-m_i)\max\{{f(\sigma_i,p_i)-c_i,0\}}/\sigma_i$; "
        + rf"$R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B, $a_0={a0}$, "
        + rf"$z_0(500)={z0_500/1e6:.1f}$M, $z_0(1000)={z0_1000/1e6:.1f}$M",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    n_over = int((pledge_met & ~unsaturated_k1000).sum())
    md = f"""# Desirability ranking — interaction effects (epoch 644)

## Parameters used
- $R = {R:,.2f}$ ADA (from `f_reward_params_epoch_644.json`)
- $T = {T:,.2f}$ ADA
- $a_0 = {a0}$
- $z_0(k=500) = T/500 = {z0_500:,.2f}$ ADA
- $z_0(k=1000) = T/1000 = {z0_1000:,.2f}$ ADA
- Baseline: $k=500$, declared $c_i$ (current minPoolCost $=170$ regime)
- For $k=1000$ panels: only pledge-met pools with $\\sigma \\le z_0(1000)$ (unsaturated; oversaturated pools are assumed to shed stake to saturation and cannot absorb redelegation). Excluded oversaturated pledge-met pools: {n_over}.

## Desirability
$$D_i = (1-m_i)\\frac{{\\max\\{{f(\\sigma_i,p_i)-c_i,0\\}}}}{{\\sigma_i}}$$

## Rank-change summary
| Panel | Scenario | n | Rank corr | Mean \\|Δrank\\| | Max \\|Δrank\\| |
|:---|:---|---:|---:|---:|---:|
| A | $k:500\\to1000$, $c_i$ unchanged | {stats['A']['n']} | {stats['A']['rank_corr']:.4f} | {stats['A']['mean_abs_rank_change']:.1f} | {stats['A']['max_abs_rank_change']} |
| B | $k:500\\to1000$, all $c_i\\to170$ | {stats['B']['n']} | {stats['B']['rank_corr']:.4f} | {stats['B']['mean_abs_rank_change']:.1f} | {stats['B']['max_abs_rank_change']} |
| C | $k=500$, all $c_i\\to75$ | {stats['C']['n']} | {stats['C']['rank_corr']:.4f} | {stats['C']['mean_abs_rank_change']:.1f} | {stats['C']['max_abs_rank_change']} |
| D | $k:500\\to1000$, all $c_i\\to75$ | {stats['D']['n']} | {stats['D']['rank_corr']:.4f} | {stats['D']['mean_abs_rank_change']:.1f} | {stats['D']['max_abs_rank_change']} |
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"R={R:.2f}, T={T:.2f}, a0={a0}")
    print(f"z0_500={z0_500/1e6:.2f}M, z0_1000={z0_1000/1e6:.2f}M")
    print(f"Excluded oversaturated (pledge-met): {n_over}")
    for key, s in stats.items():
        print(f"  {key}: n={s['n']}, corr={s['rank_corr']:.4f}, mean|Δ|={s['mean_abs_rank_change']:.1f}")
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
