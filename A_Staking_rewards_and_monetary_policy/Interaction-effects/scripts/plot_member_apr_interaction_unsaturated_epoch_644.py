#!/usr/bin/env python3
"""Epoch 644 — member APR under (k, c) interaction effects.

Same as plot_member_apr_interaction_effects_epoch_644.py, but only pools that
remain unsaturated if k rises to 1000 (sigma <= T/1000).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
PARENT = DIR.parent
POOLS_CSV = PARENT / "staking_pools_full_epoch_644.csv"
OUT_PNG = DIR / "member_apr_interaction_unsaturated_epoch_644.png"
OUT_CSV = DIR / "member_apr_interaction_unsaturated_epoch_644.csv"
OUT_MD = DIR / "member_apr_interaction_unsaturated_epoch_644.md"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
R = 14.9e6
T = 38.8e9
A0 = 0.3
K_BASE = 500
K_NEW = 1000
C_FORCE_170 = 170.0
C_FORCE_75 = 75.0
COLOR_BASE = "#4c78a8"
COLOR_ALT = "#e76f51"
MEDIAN_COLOR = "#111111"


def gross_pool_reward(sigma, declared_pledge, *, z0, r_over_t, a0):
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def member_apr(sigma, f, cost, margin):
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def scenario(sigma, declared, active, cost, margin, *, z0, r_over_t, a0, include):
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross_pool_reward(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    apr = member_apr(sigma, f, cost, margin)
    eligible = include & pledge_met & (f > cost)
    return f, apr, eligible, pledge_met


def draw_pair(ax, vals_base, vals_alt, *, label_base, label_alt, title):
    labels = [
        f"{label_base}\n($n={len(vals_base)}$)",
        f"{label_alt}\n($n={len(vals_alt)}$)",
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

    ymax = max(float(np.max(vals_base)), float(np.max(vals_alt))) * 1.12
    ax.set_ylim(0.0, max(ymax, 3.0))
    for i, vals in enumerate((vals_base, vals_alt), start=1):
        med = float(np.median(vals))
        upper_cap_y = float(bp["caps"][2 * (i - 1) + 1].get_ydata()[0])
        y_text = upper_cap_y + 0.04 * ax.get_ylim()[1]
        ax.text(
            i,
            y_text,
            f"Median: {med:.2f}%",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE,
            color=MEDIAN_COLOR,
        )
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)


def main() -> None:
    r_over_t = R / T
    z0_500 = T / K_BASE
    z0_1000 = T / K_NEW

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna() & (sigma > 0)
        & declared.notna() & active.notna()
        & cost.notna() & margin.notna()
    )
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)

    cost_170 = np.full_like(cost_a, C_FORCE_170)
    cost_75 = np.full_like(cost_a, C_FORCE_75)
    unsaturated = sigma_a <= z0_1000
    n_excluded = int(((active_a >= declared_a) & (sigma_a > 0) & ~unsaturated).sum())

    f0, apr0, elig0, pledge_met = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_500, r_over_t=r_over_t, a0=A0, include=unsaturated,
    )
    fA, aprA, eligA, _ = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_1000, r_over_t=r_over_t, a0=A0, include=unsaturated,
    )
    fB, aprB, eligB, _ = scenario(
        sigma_a, declared_a, active_a, cost_170, margin_a,
        z0=z0_1000, r_over_t=r_over_t, a0=A0, include=unsaturated,
    )
    fC, aprC, eligC, _ = scenario(
        sigma_a, declared_a, active_a, cost_75, margin_a,
        z0=z0_500, r_over_t=r_over_t, a0=A0, include=unsaturated,
    )
    fD, aprD, eligD, _ = scenario(
        sigma_a, declared_a, active_a, cost_75, margin_a,
        z0=z0_1000, r_over_t=r_over_t, a0=A0, include=unsaturated,
    )

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].values,
            "ticker": df.loc[complete, "pool_name.ticker"].values,
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "active_pledge_ada": active_a,
            "margin": margin_a,
            "fixed_cost_ada": cost_a,
            "pledge_met": pledge_met,
            "unsaturated_k1000": unsaturated,
            "f_current_k500_c_declared": f0,
            "apr_current_k500_c_declared": apr0,
            "f_gt_c_current": elig0,
            "f_A_k1000_c_declared": fA,
            "apr_A_k1000_c_declared": aprA,
            "f_gt_c_A": eligA,
            "f_B_k1000_c170": fB,
            "apr_B_k1000_c170": aprB,
            "f_gt_c_B": eligB,
            "f_C_k500_c75": fC,
            "apr_C_k500_c75": aprC,
            "f_gt_c_C": eligC,
            "f_D_k1000_c75": fD,
            "apr_D_k1000_c75": aprD,
            "f_gt_c_D": eligD,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    vals0 = 100.0 * apr0[elig0]
    valsA = 100.0 * aprA[eligA]
    valsB = 100.0 * aprB[eligB]
    valsC = 100.0 * aprC[eligC]
    valsD = 100.0 * aprD[eligD]

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 10.5), constrained_layout=True)
    draw_pair(
        axes[0, 0], vals0, valsA,
        label_base=r"Current" "\n" r"($k=500$, decl. $c_i$)",
        label_alt=r"$k=1000$" "\n" r"(declared $c_i$)",
        title=r"A: $k\!:\,500\to1000$, $c_i$ unchanged",
    )
    draw_pair(
        axes[0, 1], vals0, valsB,
        label_base=r"Current" "\n" r"($k=500$, decl. $c_i$)",
        label_alt=r"$k=1000$" "\n" r"($c_i=170$)",
        title=r"B: $k\!:\,500\to1000$, all $c_i\to170$",
    )
    draw_pair(
        axes[1, 0], vals0, valsC,
        label_base=r"Current" "\n" r"($k=500$, decl. $c_i$)",
        label_alt=r"$k=500$" "\n" r"($c_i=75$)",
        title=r"C: $k=500$, all $c_i\to75$",
    )
    draw_pair(
        axes[1, 1], vals0, valsD,
        label_base=r"Current" "\n" r"($k=500$, decl. $c_i$)",
        label_alt=r"$k=1000$" "\n" r"($c_i=75$)",
        title=r"D: $k\!:\,500\to1000$, all $c_i\to75$",
    )

    fig.suptitle(
        r"Epoch 644 — theoretical member APR (unsaturated if $k\to1000$)"
        "\n"
        + rf"$R={R/1e6:.1f}$M ADA, $T={T/1e9:.1f}$B, $a_0={A0}$; "
        + rf"$\sigma\leq z_0(1000)$; excluded oversaturated: {n_excluded}; "
        + r"APR$=73(1-m)\max\{f-c,0\}/\sigma$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    cases = [
        ("Current ($k=500$, declared $c_i$)", vals0),
        (r"$k=1000$, declared $c_i$", valsA),
        (r"$k=1000$, all $c_i=170$", valsB),
        (r"$k=500$, all $c_i=75$", valsC),
        (r"$k=1000$, all $c_i=75$", valsD),
    ]
    rows = []
    for name, vals in cases:
        rows.append(
            f"| {name} | {len(vals)} | {np.median(vals):.2f}% |"
        )

    md = f"""# Member APR — interaction effects, unsaturated only (epoch 644)

Snapshot stakes and declared margins/pledges held fixed.
$R={R/1e6:.1f}$M ADA, $T={T/1e9:.1f}$B ADA, $a_0={A0}$.

Only pledge-met pools with $\\sigma \\leq z_0(1000)={z0_1000/1e6:.2f}$M ADA
(would remain unsaturated if $k\\to1000$). Excluded oversaturated: {n_excluded}.

$$
\\mathrm{{APR}}_i = 73\\,(1-m_i)\\,\\frac{{\\max\\{{f(\\sigma_i,p_i)-c_i,0\\}}}}{{\\sigma_i}}
$$

Pools with $f>c$ only.

| Case | Pools ($f>c$) | Median APR |
|:---|---:|---:|
{chr(10).join(rows)}
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"Excluded oversaturated pledge-met: {n_excluded}")
    for name, vals in cases:
        print(f"{name}: n={len(vals)}, median={np.median(vals):.2f}%")
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
