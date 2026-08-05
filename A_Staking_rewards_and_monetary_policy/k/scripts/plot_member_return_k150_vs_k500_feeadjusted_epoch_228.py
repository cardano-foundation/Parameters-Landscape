#!/usr/bin/env python3
"""
Member return per ADA for the epoch-228 pool cohort under:
  (A) k=150 with epoch-228 fees (c, m)
  (B) k=500 fee-adjusted: same σ and declared pledge as epoch 228,
      but c and m taken from epoch 285 (pools that continue to 285)

  ρ = (1 - m) * max(f(σ, p) - c, 0) / σ     (ADA per ADA, per epoch)
  APR ≈ 73 * ρ                               (simple annualization)

Sample: pools present in both epoch 228 and 285 (so 285 fees exist),
with σ_228 > 0.

Writes
  member_return_k150_vs_k500_feeadjusted_epoch_228.csv
  member_return_k150_vs_k500_feeadjusted_epoch_228.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV_228 = DIR / "staking_pools_full_epoch_228.csv"
CSV_285 = DIR / "staking_pools_full_epoch_285.csv"
OUT_CSV = DIR / "member_return_k150_vs_k500_feeadjusted_epoch_228.csv"
OUT_PLOT = DIR / "member_return_k150_vs_k500_feeadjusted_epoch_228.png"

FONT_SIZE = 12
A0 = 0.3
T_ADA = 32.04e9
R_ADA = 29.7e6
Z0_K150 = 213.58e6
Z0_K500 = 64.07e6
EPOCHS_PER_YEAR = 73.0  # 365 / 5
COLOR_POS = "#4c78a8"
COLOR_ZERO = "0.7"


def load_epoch(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    )
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": stake.fillna(0.0) / 1e6,
            "pledge_ada": pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0)
            / 1e6,
            "margin": pd.to_numeric(df["pool_update.active.margin"], errors="coerce"),
            "fixed_cost_ada": pd.to_numeric(
                df["pool_update.active.fixed_cost"], errors="coerce"
            ).fillna(0.0)
            / 1e6,
        }
    ).set_index("pool_id")


def gross_pool_reward(
    sigma: np.ndarray, p: np.ndarray, z0: float, R: float, T: float, a0: float
) -> np.ndarray:
    sigma = np.asarray(sigma, dtype=float)
    p = np.asarray(p, dtype=float)
    sigma_t = np.minimum(np.maximum(sigma, 0.0), z0)
    p_t = np.minimum(np.minimum(np.maximum(p, 0.0), z0), sigma_t)
    inner = sigma_t - p_t * (z0 - sigma_t) / z0
    return (R / T) / (1.0 + a0) * (sigma_t + a0 * p_t * inner / z0)


def member_return_per_ada(
    sigma: np.ndarray, p: np.ndarray, c: np.ndarray, m: np.ndarray, z0: float
) -> tuple[np.ndarray, np.ndarray]:
    f = gross_pool_reward(sigma, p, z0, R_ADA, T_ADA, A0)
    # infeasible if declared pledge > stake
    f = np.where(p > sigma, np.nan, f)
    pot = (1.0 - m) * np.maximum(f - c, 0.0)
    rho = np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)
    rho = np.where(np.isfinite(f), rho, np.nan)
    return f, rho


def draw_panel(
    ax,
    sigma: np.ndarray,
    rho: np.ndarray,
    z0: float,
    title: str,
) -> None:
    ok = np.isfinite(rho) & (sigma > 0)
    pos = ok & (rho > 0)
    zero = ok & (rho <= 0)
    ax.scatter(
        sigma[zero],
        np.full(zero.sum(), 1e-12),  # placeholder; hidden by ylim when rho=0
        s=10,
        alpha=0.0,
    )
    # plot zeros near bottom of log scale as light points at a floor marker
    if zero.any():
        ax.scatter(
            sigma[zero],
            np.full(int(zero.sum()), 1.05e-6),
            s=10,
            alpha=0.25,
            color=COLOR_ZERO,
            edgecolors="none",
            label=rf"return $=0$ (n={int(zero.sum())})",
            zorder=1,
        )
    ax.scatter(
        sigma[pos],
        rho[pos],
        s=12,
        alpha=0.35,
        color=COLOR_POS,
        edgecolors="none",
        label=rf"return $>0$ (n={int(pos.sum())})",
        zorder=2,
    )
    ax.axvline(z0, color="0.45", linestyle=":", linewidth=1.2, label=rf"$z_0={z0/1e6:.1f}$M")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Delegation $\sigma_i$ at epoch 228 (ADA, log scale)", fontsize=FONT_SIZE)
    ax.set_ylabel(
        r"$(1-m)\max(f-c,0)/\sigma$  (ADA per ADA / epoch)",
        fontsize=FONT_SIZE,
    )
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(1e3, max(Z0_K150 * 1.15, float(np.nanmax(sigma)) * 1.05))
    ax.set_ylim(1e-6, 3e-3)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="lower right")
    ax.grid(alpha=0.25)


def main() -> None:
    a = load_epoch(CSV_228)
    b = load_epoch(CSV_285)

    # Continuing cohort: need 285 fees; hold 228 σ and pledge fixed
    common = a.index.intersection(b.index)
    a = a.loc[common]
    b = b.loc[common]
    mask = (a["sigma_ada"] > 0) & a["margin"].notna() & b["margin"].notna()
    a = a.loc[mask]
    b = b.loc[mask]

    sigma = a["sigma_ada"].to_numpy()
    pledge = a["pledge_ada"].to_numpy()
    c228 = a["fixed_cost_ada"].to_numpy()
    m228 = a["margin"].fillna(0.0).to_numpy()
    c285 = b["fixed_cost_ada"].to_numpy()
    m285 = b["margin"].fillna(0.0).to_numpy()

    f150, rho150 = member_return_per_ada(sigma, pledge, c228, m228, Z0_K150)
    f500, rho500 = member_return_per_ada(sigma, pledge, c285, m285, Z0_K500)

    out = pd.DataFrame(
        {
            "pool_id": a.index,
            "ticker": a["ticker"].to_numpy(),
            "sigma_ada_228": sigma,
            "declared_pledge_ada_228": pledge,
            "fixed_cost_ada_228": c228,
            "margin_228": m228,
            "fixed_cost_ada_285": c285,
            "margin_285": m285,
            "z0_k150_ada": Z0_K150,
            "z0_k500_ada": Z0_K500,
            "f_ada_k150": f150,
            "f_ada_k500_feeadjusted": f500,
            "member_return_per_ada_epoch_k150": rho150,
            "member_return_per_ada_epoch_k500_feeadjusted": rho500,
            "member_apr_simple_k150": EPOCHS_PER_YEAR * rho150,
            "member_apr_simple_k500_feeadjusted": EPOCHS_PER_YEAR * rho500,
            "delta_member_return_epoch": rho500 - rho150,
            "delta_member_apr_simple": EPOCHS_PER_YEAR * (rho500 - rho150),
            "cost_changed": c285 != c228,
            "margin_changed": m285 != m228,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    draw_panel(
        axes[0],
        sigma,
        rho150,
        Z0_K150,
        title=rf"$k=150$ with epoch-228 fees ($c,m$)" "\n"
        rf"(n={len(out)}; median $\rho={np.nanmedian(rho150[rho150>0])*1e6:.2f}\times 10^{{-6}}$)",
    )
    draw_panel(
        axes[1],
        sigma,
        rho500,
        Z0_K500,
        title=rf"$k=500$ fee-adjusted ($c,m$ from epoch 285)" "\n"
        rf"(same $\sigma,p$ as 228; n={len(out)}; "
        rf"median $\rho={np.nanmedian(rho500[rho500>0])*1e6:.2f}\times 10^{{-6}}$)",
    )
    fig.suptitle(
        "Member return per ADA — epoch-228 stake/pledge held fixed\n"
        rf"($\rho=(1-m)\max(f-c,0)/\sigma$; $R={R_ADA/1e6:.1f}$M, $a_0={A0}$; "
        rf"simple APR $= {EPOCHS_PER_YEAR:.0f}\,\rho$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=300)
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")

    def summarize(name: str, rho: np.ndarray) -> None:
        ok = np.isfinite(rho)
        pos = ok & (rho > 0)
        print(
            f"{name}: n={ok.sum()}  return>0={pos.sum()}  "
            f"median ρ (pos)={np.nanmedian(rho[pos]):.3e}  "
            f"median APR (pos)={EPOCHS_PER_YEAR*np.nanmedian(rho[pos])*100:.2f}%  "
            f"mean APR (pos)={EPOCHS_PER_YEAR*np.nanmean(rho[pos])*100:.2f}%"
        )

    summarize("k=150", rho150)
    summarize("k=500 fee-adjusted", rho500)
    print(
        f"fee changes among cohort: cost≠ {int((c285!=c228).sum())}, "
        f"margin≠ {int((m285!=m228).sum())}, either≠ "
        f"{int(((c285!=c228)|(m285!=m228)).sum())}"
    )


if __name__ == "__main__":
    main()
