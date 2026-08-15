#!/usr/bin/env python3
"""
Boxplot: theoretical member APR at epoch 644 for a0=0.3 vs a0=0.6.

Snapshot stakes, declared costs/margins/pledges held fixed. For each pool:
  f_i(a0) = f(σ_i, p_i; z0, a0) using declared pledge;
            f_i = 0 if active pledge < declared.
  APR_i(a0) = 73 (1-m_i) max{f_i(a0) - c_i, 0} / σ_i

Boxplot groups are pledge-met pools with f > c under that a0.

Writes:
  member_apr_a0_0p3_vs_0p6_epoch_644.png
  member_apr_a0_0p3_vs_0p6_epoch_644.csv
  member_apr_a0_0p3_vs_0p6_epoch_644.md
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
OUT_PLOT = DIR / "member_apr_a0_0p3_vs_0p6_epoch_644.png"
OUT_CSV = DIR / "member_apr_a0_0p3_vs_0p6_epoch_644.csv"
OUT_MD = DIR / "member_apr_a0_0p3_vs_0p6_epoch_644.md"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
A0_BASE = 0.3
A0_ALT = 0.6
COLOR_BASE = "#4c78a8"
COLOR_ALT = "#e76f51"
MEDIAN_COLOR = "#111111"


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


def member_apr(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def network_apr_pct(
    sigma: np.ndarray, apr: np.ndarray, eligible: np.ndarray
) -> float:
    if not eligible.any():
        return float("nan")
    return 100.0 * float(np.average(apr[eligible], weights=sigma[eligible]))


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    k = int(params["k"])
    z0 = float(params["z0_ada"])
    r_over_t = R / T

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    )
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce")
        / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna()
        & (sigma > 0)
        & declared.notna()
        & active.notna()
        & cost.notna()
        & margin.notna()
    )
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)

    pledge_met = active_a >= declared_a

    f_base_raw = gross_pool_reward(
        sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=A0_BASE
    )
    f_alt_raw = gross_pool_reward(
        sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=A0_ALT
    )
    f_base = np.where(pledge_met, np.maximum(f_base_raw, 0.0), 0.0)
    f_alt = np.where(pledge_met, np.maximum(f_alt_raw, 0.0), 0.0)

    apr_base = member_apr(sigma_a, f_base, cost_a, margin_a)
    apr_alt = member_apr(sigma_a, f_alt, cost_a, margin_a)
    elig_base = pledge_met & (f_base > cost_a)
    elig_alt = pledge_met & (f_alt > cost_a)

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].to_numpy(),
            "ticker": df.loc[complete, "pool_name.ticker"].to_numpy(),
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "active_pledge_ada": active_a,
            "declared_pledge_met": pledge_met,
            "margin": margin_a,
            "fixed_cost_ada": cost_a,
            "f_ada_a0_0p3": f_base,
            "member_apr_a0_0p3": apr_base,
            "f_gt_c_a0_0p3": elig_base,
            "f_ada_a0_0p6": f_alt,
            "member_apr_a0_0p6": apr_alt,
            "f_gt_c_a0_0p6": elig_alt,
            "delta_member_apr": apr_alt - apr_base,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    vals_base = 100.0 * apr_base[elig_base]
    vals_alt = 100.0 * apr_alt[elig_alt]
    net_base = network_apr_pct(sigma_a, apr_base, elig_base)
    net_alt = network_apr_pct(sigma_a, apr_alt, elig_alt)

    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    labels = [
        rf"$a_0={A0_BASE}$"
        f"\n($n={len(vals_base)}$)",
        rf"$a_0={A0_ALT}$"
        f"\n($n={len(vals_alt)}$)",
    ]
    bp = ax.boxplot(
        [vals_base, vals_alt],
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        widths=0.55,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.2},
        whiskerprops={"color": "0.15", "linewidth": 1.1},
        capprops={"color": "0.15", "linewidth": 1.1},
        boxprops={"linewidth": 1.1},
    )
    for box, color in zip(bp["boxes"], (COLOR_BASE, COLOR_ALT)):
        box.set_facecolor(color)
        box.set_alpha(0.75)
        box.set_edgecolor("0.2")

    ymax = max(float(np.max(vals_base)), float(np.max(vals_alt))) * 1.08
    ax.set_ylim(0.0, max(ymax, 3.0))
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    fig.suptitle(
        "Epoch 644 — theoretical member APR: "
        rf"$a_0={A0_BASE}$ vs $a_0={A0_ALT}$"
        "\n"
        rf"($k={k}$, $R={R/1e6:.2f}$M, $T={T/1e9:.2f}$B; "
        r"pledge-met, $f>c$; $\sigma,p,c,m$ fixed)"
        "\n"
        r"APR$=73(1-m)\max\{f-c,0\}/\sigma$",
        fontsize=FONT_SIZE,
    )
    ax.text(
        0.98,
        0.97,
        f"Median APR:\n"
        rf"  $a_0={A0_BASE}$: {np.median(vals_base):.2f}%"
        "\n"
        rf"  $a_0={A0_ALT}$: {np.median(vals_alt):.2f}%"
        "\n"
        "Network APR (stake-weighted):\n"
        rf"  $a_0={A0_BASE}$: {net_base:.2f}%"
        "\n"
        rf"  $a_0={A0_ALT}$: {net_alt:.2f}%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )
    fig.savefig(OUT_PLOT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    def pct_chg(new: float, old: float) -> str:
        if old == 0 or not np.isfinite(old) or not np.isfinite(new):
            return "—"
        return f"{100.0 * (new - old) / old:+.1f}%"

    md = f"""# Member APR — $a_0={A0_BASE}$ vs $a_0={A0_ALT}$ (epoch 644)

Snapshot stakes and declared pool parameters held fixed. Protocol: $k={k}$,
$z_0={z0/1e6:.2f}$M ADA, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B ADA.

$$
\\mathrm{{APR}}_i(a_0)
= 73\\,(1-m_i)\\,\\frac{{\\max\\{{f(\\sigma_i,p_i;a_0)-c_i,0\\}}}}{{\\sigma_i}},
$$

with $f=0$ when active pledge is below declared pledge. Boxplot groups are
pledge-met pools with $f>c$ under that $a_0$.

| Case | Pools ($f>c$) | Median APR | Mean APR | Network APR | Δ network vs $a_0={A0_BASE}$ |
|:---|---:|---:|---:|---:|---:|
| $a_0={A0_BASE}$ | {len(vals_base)} | {np.median(vals_base):.2f}% | {np.mean(vals_base):.2f}% | {net_base:.2f}% | — |
| $a_0={A0_ALT}$ | {len(vals_alt)} | {np.median(vals_alt):.2f}% | {np.mean(vals_alt):.2f}% | {net_alt:.2f}% | {pct_chg(net_alt, net_base)} |
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(
        f"a0={A0_BASE}: n={len(vals_base)}, "
        f"median={np.median(vals_base):.2f}%, network={net_base:.2f}%"
    )
    print(
        f"a0={A0_ALT}: n={len(vals_alt)}, "
        f"median={np.median(vals_alt):.2f}%, network={net_alt:.2f}%"
    )
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
