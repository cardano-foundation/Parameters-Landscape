#!/usr/bin/env python3
"""Member APR under k–a0 interaction, unsaturated pools only (epoch 644).

3 panels vs current (k=500, a0=0.3):
  A) k:500->1000, a0=0.3
  B) k:500->1000, a0=0.6
  C) k=500, a0:0.3->0.6
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
OUT_PNG = DIR / "member_apr_k_a0_interaction_unsaturated_epoch_644.png"
OUT_CSV = DIR / "member_apr_k_a0_interaction_unsaturated_epoch_644.csv"
OUT_MD = DIR / "member_apr_k_a0_interaction_unsaturated_epoch_644.md"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
A0_0, A0_1 = 0.3, 0.6
K0, K1 = 500, 1000
COLOR_BASE = "#4c78a8"
COLOR_ALT = "#e76f51"
MEDIAN_COLOR = "#111111"


def gross(sigma, declared, *, z0, r_over_t, a0):
    st = np.minimum(np.maximum(sigma, 0.0), z0)
    pt = np.minimum(np.maximum(declared, 0.0), z0)
    pt = np.minimum(pt, st)
    inner = st - pt * (z0 - st) / z0
    return (r_over_t / (1.0 + a0)) * (st + a0 * pt * inner / z0)


def member_apr(sigma, f, cost, margin):
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)


def scenario(sigma, declared, active, cost, margin, *, z0, r_over_t, a0, include):
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    apr = member_apr(sigma, f, cost, margin)
    eligible = include & pledge_met & (f > cost)
    return f, apr, eligible


def draw_pair(ax, vals0, vals1, *, label0, label1, title):
    labels = [f"{label0}\n($n={len(vals0)}$)", f"{label1}\n($n={len(vals1)}$)"]
    bp = ax.boxplot(
        [vals0, vals1],
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
    ymax = max(float(np.max(vals0)), float(np.max(vals1))) * 1.12
    ax.set_ylim(0.0, max(ymax, 3.0))
    for i, vals in enumerate((vals0, vals1), start=1):
        med = float(np.median(vals))
        upper = float(bp["caps"][2 * (i - 1) + 1].get_ydata()[0])
        ax.text(
            i, upper + 0.04 * ax.get_ylim()[1], f"Median: {med:.2f}%",
            ha="center", va="bottom", fontsize=FONT_SIZE, color=MEDIAN_COLOR,
        )
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0_500 = T / K0
    z0_1000 = T / K1

    df = pd.read_csv(POOLS_CSV)
    sigma = pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    complete = sigma.notna() & (sigma > 0) & declared.notna() & active.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    unsat = sigma_a <= z0_1000
    n_ex = int(((active_a >= declared_a) & ~unsat).sum())

    f0, apr0, e0 = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_500, r_over_t=r_over_t, a0=A0_0, include=unsat,
    )
    fA, aprA, eA = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_1000, r_over_t=r_over_t, a0=A0_0, include=unsat,
    )
    fB, aprB, eB = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_1000, r_over_t=r_over_t, a0=A0_1, include=unsat,
    )
    fC, aprC, eC = scenario(
        sigma_a, declared_a, active_a, cost_a, margin_a,
        z0=z0_500, r_over_t=r_over_t, a0=A0_1, include=unsat,
    )

    pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].values,
            "ticker": df.loc[complete, "pool_name.ticker"].values,
            "sigma_ada": sigma_a,
            "unsaturated_k1000": unsat,
            "apr_base": apr0,
            "f_gt_c_base": e0,
            "apr_A": aprA,
            "f_gt_c_A": eA,
            "apr_B": aprB,
            "f_gt_c_B": eB,
            "apr_C": aprC,
            "f_gt_c_C": eC,
        }
    ).to_csv(OUT_CSV, index=False)

    v0, vA, vB, vC = 100 * apr0[e0], 100 * aprA[eA], 100 * aprB[eB], 100 * aprC[eC]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2), constrained_layout=True)
    draw_pair(
        axes[0], v0, vA,
        label0=r"Current" "\n" r"($k=500$, $a_0=0.3$)",
        label1=r"$k=1000$" "\n" r"($a_0=0.3$)",
        title=r"A: $k\!:\,500\to1000$, $a_0=0.3$",
    )
    draw_pair(
        axes[1], v0, vB,
        label0=r"Current" "\n" r"($k=500$, $a_0=0.3$)",
        label1=r"$k=1000$" "\n" r"($a_0=0.6$)",
        title=r"B: $k\!:\,500\to1000$, $a_0\!:\,0.3\to0.6$",
    )
    draw_pair(
        axes[2], v0, vC,
        label0=r"Current" "\n" r"($k=500$, $a_0=0.3$)",
        label1=r"$k=500$" "\n" r"($a_0=0.6$)",
        title=r"C: $k=500$, $a_0\!:\,0.3\to0.6$",
    )
    fig.suptitle(
        r"Epoch 644 — member APR under $k$–$a_0$ interaction (unsaturated if $k\to1000$)"
        "\n"
        + rf"$R={R/1e6:.2f}$M, $T={T/1e9:.2f}$B; excluded oversaturated: {n_ex}; "
        + r"APR$=73(1-m)\max\{f-c,0\}/\sigma$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)

    cases = [
        (r"Current ($k=500$, $a_0=0.3$)", v0),
        (r"$k=1000$, $a_0=0.3$", vA),
        (r"$k=1000$, $a_0=0.6$", vB),
        (r"$k=500$, $a_0=0.6$", vC),
    ]
    rows = [f"| {n} | {len(v)} | {np.median(v):.2f}% |" for n, v in cases]
    md = f"""# Member APR — $k$–$a_0$ interaction, unsaturated only (epoch 644)

$R={R:,.2f}$ ADA, $T={T:,.2f}$ ADA. Only pools with $\\sigma\\leq z_0(1000)$.
Excluded oversaturated: {n_ex}.

| Case | Pools ($f>c$) | Median APR |
|:---|---:|---:|
{chr(10).join(rows)}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    for n, v in cases:
        print(f"{n}: n={len(v)}, median={np.median(v):.2f}%")
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
