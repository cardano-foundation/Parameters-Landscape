#!/usr/bin/env python3
"""
Member return per ADA for the epoch-228 pool cohort under:
  (A) k=150 with epoch-228 fees (c, m)
  (B) k=500 fee-adjusted: same σ and declared pledge as epoch 228,
      but c and m taken from epoch 285 (pools that continue to 285)

  ρ = (1 - m) * max(f(σ, p) - c, 0) / σ     (ADA per ADA, per epoch)
  APR ≈ 73 * ρ                               (simple annualization)

Samples:
  - k=150: all pools at epoch 228 with σ_228 > 0
  - k=500 fee-adjusted: the subset surviving to epoch 285, because 285 fees
    are required; σ and pledge remain fixed at their epoch-228 values.

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
    pot = (1.0 - m) * np.maximum(f - c, 0.0)
    rho = np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)
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
    ax.set_xlim(1.0, max(Z0_K150 * 1.15, float(np.nanmax(sigma)) * 1.05))
    ax.set_ylim(1e-6, 3e-3)
    ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="lower right")
    ax.grid(alpha=0.25)


def main() -> None:
    a_all = load_epoch(CSV_228)
    b = load_epoch(CSV_285)

    # Starting point: every active pool in the epoch-228 snapshot.
    a_all = a_all[(a_all["sigma_ada"] > 0) & a_all["margin"].notna()]
    continuing = a_all.index.intersection(b.index)
    exited = a_all.index.difference(b.index)
    a_cont = a_all.loc[continuing]
    b_cont = b.loc[continuing]
    fee_ok = b_cont["margin"].notna()
    a_cont = a_cont.loc[fee_ok]
    b_cont = b_cont.loc[fee_ok]

    sigma150 = a_all["sigma_ada"].to_numpy()
    pledge150 = a_all["pledge_ada"].to_numpy()
    c228_all = a_all["fixed_cost_ada"].to_numpy()
    m228_all = a_all["margin"].to_numpy()

    sigma500 = a_cont["sigma_ada"].to_numpy()
    pledge500 = a_cont["pledge_ada"].to_numpy()
    c285 = b_cont["fixed_cost_ada"].to_numpy()
    m285 = b_cont["margin"].to_numpy()

    f150, rho150 = member_return_per_ada(
        sigma150, pledge150, c228_all, m228_all, Z0_K150
    )
    f500, rho500 = member_return_per_ada(
        sigma500, pledge500, c285, m285, Z0_K500
    )

    # One row per epoch-228 pool; fee-adjusted fields are blank for exits.
    out = pd.DataFrame(
        {
            "pool_id": a_all.index,
            "ticker": a_all["ticker"].to_numpy(),
            "survives_to_285": a_all.index.isin(a_cont.index),
            "sigma_ada_228": sigma150,
            "declared_pledge_ada_228": pledge150,
            "effective_pledge_ada_228": np.minimum(pledge150, sigma150),
            "fixed_cost_ada_228": c228_all,
            "margin_228": m228_all,
            "z0_k150_ada": Z0_K150,
            "z0_k500_ada": Z0_K500,
            "f_ada_k150": f150,
            "member_return_per_ada_epoch_k150": rho150,
            "member_apr_simple_k150": EPOCHS_PER_YEAR * rho150,
        },
        index=a_all.index,
    )
    for col in [
        "fixed_cost_ada_285",
        "margin_285",
        "f_ada_k500_feeadjusted",
        "member_return_per_ada_epoch_k500_feeadjusted",
        "member_apr_simple_k500_feeadjusted",
        "delta_member_return_epoch",
        "delta_member_apr_simple",
    ]:
        out[col] = np.nan
    out["cost_changed"] = pd.Series(pd.NA, index=out.index, dtype="boolean")
    out["margin_changed"] = pd.Series(pd.NA, index=out.index, dtype="boolean")

    out.loc[a_cont.index, "fixed_cost_ada_285"] = c285
    out.loc[a_cont.index, "margin_285"] = m285
    out.loc[a_cont.index, "f_ada_k500_feeadjusted"] = f500
    out.loc[a_cont.index, "member_return_per_ada_epoch_k500_feeadjusted"] = rho500
    out.loc[a_cont.index, "member_apr_simple_k500_feeadjusted"] = (
        EPOCHS_PER_YEAR * rho500
    )
    rho150_cont = out.loc[
        a_cont.index, "member_return_per_ada_epoch_k150"
    ].to_numpy()
    out.loc[a_cont.index, "delta_member_return_epoch"] = rho500 - rho150_cont
    out.loc[a_cont.index, "delta_member_apr_simple"] = (
        EPOCHS_PER_YEAR * (rho500 - rho150_cont)
    )
    out.loc[a_cont.index, "cost_changed"] = (
        c285 != a_cont["fixed_cost_ada"].to_numpy()
    )
    out.loc[a_cont.index, "margin_changed"] = m285 != a_cont["margin"].to_numpy()
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    draw_panel(
        axes[0],
        sigma150,
        rho150,
        Z0_K150,
        title=rf"$k=150$ with epoch-228 fees ($c,m$)" "\n"
        rf"(all epoch-228 pools; n={len(rho150)}; "
        rf"median APR among positive returns="
        rf"{EPOCHS_PER_YEAR*np.median(rho150[rho150>0])*100:.2f}\%)",
    )
    draw_panel(
        axes[1],
        sigma500,
        rho500,
        Z0_K500,
        title=rf"$k=500$ fee-adjusted ($c,m$ from epoch 285)" "\n"
        rf"(survivors only; same $\sigma,p$ as 228; n={len(rho500)}; "
        rf"median APR among positive returns="
        rf"{EPOCHS_PER_YEAR*np.median(rho500[rho500>0])*100:.2f}\%)",
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
            f"median APR (all)={EPOCHS_PER_YEAR*np.nanmedian(rho[ok])*100:.2f}%  "
            f"median ρ (pos)={np.nanmedian(rho[pos]):.3e}  "
            f"median APR (pos)={EPOCHS_PER_YEAR*np.nanmedian(rho[pos])*100:.2f}%  "
            f"mean APR (pos)={EPOCHS_PER_YEAR*np.nanmean(rho[pos])*100:.2f}%"
        )

    summarize("k=150", rho150)
    summarize("k=500 fee-adjusted", rho500)
    rho_exit = out.loc[exited, "member_return_per_ada_epoch_k150"].to_numpy()
    summarize("k=150, pools exiting by 285", rho_exit)
    print(
        f"epoch-228 pools={len(a_all)}, survivors={len(a_cont)}, exits={len(exited)}"
    )
    c228_cont = a_cont["fixed_cost_ada"].to_numpy()
    m228_cont = a_cont["margin"].to_numpy()
    print(
        f"fee changes among survivors: cost≠ {int((c285!=c228_cont).sum())}, "
        f"margin≠ {int((m285!=m228_cont).sum())}, either≠ "
        f"{int(((c285!=c228_cont)|(m285!=m228_cont)).sum())}"
    )


if __name__ == "__main__":
    main()
