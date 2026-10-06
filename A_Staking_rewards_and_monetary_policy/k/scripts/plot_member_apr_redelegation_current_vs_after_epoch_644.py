#!/usr/bin/env python3
"""
Boxplot: theoretical member APR — current snapshot vs after idealized redelegation.

Active pools only (not σ=0, not unmet pledge, not zero blocks in
epochs 630–644).

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
CAP_ADA = 40e6
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


def nakamoto_coefficient(stakes: np.ndarray, threshold: float = 0.5) -> int:
    s = np.sort(np.asarray(stakes, dtype=float))
    s = s[s > 0][::-1]
    if s.size == 0:
        return 0
    c = np.cumsum(s)
    return int(np.searchsorted(c, threshold * c[-1], side="left") + 1)


def n_at_cap(stakes: np.ndarray) -> int:
    s = np.asarray(stakes, dtype=float)
    return int(((s >= CAP_ADA) & (s < CAP_ADA + 5e6)).sum())


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
        r"(Active, pledge-met pools with $f>c$; declared $c_i$; "
        r"APR$=73(1-m)\max\{f-c,0\}/\sigma$)",
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

    n_active_cur = int((sigma > 0).sum())
    n_active_aft = int((sigma_after > 0).sum())
    n_donors_cur = int((sigma > CAP_ADA).sum())
    n_donors_aft = int((sigma_after > CAP_ADA).sum())
    n_recv_cur = int(((sigma > 0) & (sigma <= CAP_ADA)).sum())
    n_recv_aft = int(((sigma_after > 0) & (sigma_after <= CAP_ADA)).sum())
    n_cap_cur = n_at_cap(sigma)
    n_cap_aft = n_at_cap(sigma_after)
    max_cur = float(sigma.max()) / 1e6
    max_aft = float(sigma_after.max()) / 1e6
    med_stake_cur = float(np.median(sigma[sigma > 0])) / 1e6
    med_stake_aft = float(np.median(sigma_after[sigma_after > 0])) / 1e6
    tot_cur = float(sigma.sum()) / 1e9
    tot_aft = float(sigma_after.sum()) / 1e9
    nak_cur = nakamoto_coefficient(sigma)
    nak_aft = nakamoto_coefficient(sigma_after)
    med_apr_cur = float(np.median(cur_vals))
    med_apr_aft = float(np.median(aft_vals))
    mean_apr_cur = float(np.mean(cur_vals))
    mean_apr_aft = float(np.mean(aft_vals))

    md = f"""# Member APR — current vs after redelegation (epoch 644)

Active pools only. Current: epoch-644 stakes, $k={K_CURRENT}$, $z_0={z0_current/1e6:.2f}$M ADA.
After: post-redelegation stakes ($k={K_AFTER}$ cap-40M exercise), $k={K_AFTER}$, $z_0={z0_after/1e6:.2f}$M ADA.

The theoretical delegator APR for pool $i$ is
$\\mathrm{{APR}}_i = 73\\,(1-m_i)\\,\\max\\{{f(\\sigma_i,p_i)-c_i,\\,0\\}}/\\sigma_i$.
Median APR is evaluated on pledge-met pools with $f_i>c_i$.

| Quantity | Current ($k=500$) | After redelegation ($k=1000$) |
|:---|---:|---:|
| Active pools | {n_active_cur:,} | {n_active_aft:,} |
| Donors $(\\sigma>40$M$)$ | {n_donors_cur:,} | {n_donors_aft:,} |
| Receivers $(0<\\sigma\\le 40$M$)$ | {n_recv_cur:,} | {n_recv_aft:,} |
| Pools at cap $40$M | {n_cap_cur:,} | {n_cap_aft:,} |
| Max pool stake | {max_cur:.1f}M ADA | {max_aft:.1f}M ADA |
| Median pool stake | {med_stake_cur:.2f}M ADA | {med_stake_aft:.2f}M ADA |
| **Median APR** ($f>c$, pledge-met) | **{med_apr_cur:.2f}%** | **{med_apr_aft:.2f}%** |
| Pools with $f>c$ (APR sample) | {len(cur_vals):,} | {len(aft_vals):,} |
| Nakamoto $N$ | {nak_cur:,} | {nak_aft:,} |
| Total stake | {tot_cur:.2f}B ADA | {tot_aft:.2f}B ADA |

| Case | Pools ($f>c$) | Median APR | Mean APR | Network APR |
|:---|---:|---:|---:|---:|
| Current ($k=500$) | {len(cur_vals):,} | {med_apr_cur:.2f}% | {mean_apr_cur:.2f}% | {net_cur:.2f}% |
| After redelegation ($k=1000$) | {len(aft_vals):,} | {med_apr_aft:.2f}% | {mean_apr_aft:.2f}% | {net_aft:.2f}% |
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"Current: n={len(cur_vals)}, median={np.median(cur_vals):.2f}%, network={net_cur:.2f}%")
    print(f"After:   n={len(aft_vals)}, median={np.median(aft_vals):.2f}%, network={net_aft:.2f}%")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
