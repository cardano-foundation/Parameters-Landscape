#!/usr/bin/env python3
"""
Boxplot: theoretical member APR — current snapshot vs after idealized redelegation.

Current:  epoch-644 stakes, k=500, declared c_i, pledge-met, f > c.
After:    post-redelegation stakes (k=1000 cap-40M exercise), k=1000, same rules.

APR_i = 73 (1-m_i) max{f - c_i, 0} / sigma_i

Writes:
  member_apr_redelegation_current_vs_after_epoch_644.png
  member_apr_redelegation_current_vs_after_epoch_644.csv
  member_apr_redelegation_current_vs_after_epoch_644.md
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
REDEP_CSV = DIR / "redelegation_rank_k1000_cap40M_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_PLOT = DIR / "member_apr_redelegation_current_vs_after_epoch_644.png"
OUT_CSV = DIR / "member_apr_redelegation_current_vs_after_epoch_644.csv"
OUT_MD = DIR / "member_apr_redelegation_current_vs_after_epoch_644.md"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
K_CURRENT = 500
K_AFTER = 1000
COLOR_CURRENT = "#4c78a8"
COLOR_AFTER = "#e76f51"
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


def scenario_apr(
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
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross_pool_reward(
        sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0
    )
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    apr = member_apr(sigma, f, cost, margin)
    eligible = pledge_met & (f > cost)
    return apr, eligible, f


def network_apr_pct(
    sigma: np.ndarray, apr: np.ndarray, eligible: np.ndarray
) -> float:
    if not eligible.any():
        return float("nan")
    sig = sigma[eligible]
    vals = apr[eligible]
    return 100.0 * float(np.average(vals, weights=sig))


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_current = T / K_CURRENT
    z0_after = T / K_AFTER

    df = pd.read_csv(REDEP_CSV)
    sigma = df["sigma_ada"].to_numpy(dtype=float)
    sigma_after = df["sigma_after_ada"].to_numpy(dtype=float)
    declared = df["declared_pledge_ada"].to_numpy(dtype=float)
    active = df["active_pledge_ada"].to_numpy(dtype=float)
    cost = df["fixed_cost_ada"].to_numpy(dtype=float)
    margin = df["margin"].to_numpy(dtype=float)

    apr_cur, elig_cur, f_cur = scenario_apr(
        sigma, declared, active, cost, margin,
        z0=z0_current, r_over_t=r_over_t, a0=a0,
    )

    active_after = sigma_after > 0
    apr_aft, elig_aft, f_aft = scenario_apr(
        sigma_after,
        declared,
        active,
        cost,
        margin,
        z0=z0_after,
        r_over_t=r_over_t,
        a0=a0,
    )
    elig_aft = elig_aft & active_after

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["ticker"],
            "role": df["role"],
            "sigma_ada_current": sigma,
            "sigma_ada_after": sigma_after,
            "declared_pledge_ada": declared,
            "active_pledge_ada": active,
            "fixed_cost_ada": cost,
            "margin": margin,
            "f_ada_k500_current": f_cur,
            "member_apr_k500_current": apr_cur,
            "f_gt_c_k500_current": elig_cur,
            "f_ada_k1000_after": np.where(active_after, f_aft, 0.0),
            "member_apr_k1000_after": np.where(active_after, apr_aft, 0.0),
            "f_gt_c_k1000_after": elig_aft,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    cur_vals = 100.0 * apr_cur[elig_cur]
    aft_vals = 100.0 * apr_aft[elig_aft]
    net_cur = network_apr_pct(sigma, apr_cur, elig_cur)
    net_aft = network_apr_pct(sigma_after, apr_aft, elig_aft)

    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    labels = [
        f"Current\n($k={K_CURRENT}$, $n={len(cur_vals)}$)",
        f"After redelegation\n($k={K_AFTER}$, $n={len(aft_vals)}$)",
    ]
    bp = ax.boxplot(
        [cur_vals, aft_vals],
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        widths=0.55,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.2},
        whiskerprops={"color": "0.15", "linewidth": 1.1},
        capprops={"color": "0.15", "linewidth": 1.1},
        boxprops={"linewidth": 1.1},
    )
    for box, color in zip(bp["boxes"], (COLOR_CURRENT, COLOR_AFTER)):
        box.set_facecolor(color)
        box.set_alpha(0.75)
        box.set_edgecolor("0.2")

    ymax = max(float(np.max(cur_vals)), float(np.max(aft_vals))) * 1.08
    ax.set_ylim(0.0, max(ymax, 3.0))
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    fig.suptitle(
        "Epoch 644 — theoretical member APR: current vs after redelegation\n"
        r"(pledge-met pools with $f>c$; declared $c_i$; APR$=73(1-m)\max\{f-c,0\}/\sigma$)",
        fontsize=FONT_SIZE,
    )
    ax.text(
        0.98,
        0.97,
        f"Median APR:\n"
        f"  Current: {np.median(cur_vals):.2f}%\n"
        f"  After: {np.median(aft_vals):.2f}%\n"
        f"Network APR (stake-weighted):\n"
        f"  Current: {net_cur:.2f}%\n"
        f"  After: {net_aft:.2f}%",
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

    md = f"""# Member APR — current vs after redelegation (epoch 644)

Current: epoch-644 stakes, $k={K_CURRENT}$, $z_0={z0_current/1e6:.2f}$M ADA.
After: post-redelegation stakes ($k={K_AFTER}$ cap-40M exercise), $k={K_AFTER}$, $z_0={z0_after/1e6:.2f}$M ADA.

Pledge-met pools with $f>c$ only.

| Case | Pools ($f>c$) | Median APR | Mean APR | Network APR |
|:---|---:|---:|---:|---:|
| Current ($k=500$) | {len(cur_vals)} | {np.median(cur_vals):.2f}% | {np.mean(cur_vals):.2f}% | {net_cur:.2f}% |
| After redelegation ($k=1000$) | {len(aft_vals)} | {np.median(aft_vals):.2f}% | {np.mean(aft_vals):.2f}% | {net_aft:.2f}% |
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"Current: n={len(cur_vals)}, median={np.median(cur_vals):.2f}%, network={net_cur:.2f}%")
    print(f"After:   n={len(aft_vals)}, median={np.median(aft_vals):.2f}%, network={net_aft:.2f}%")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
