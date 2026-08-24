#!/usr/bin/env python3
"""Pool viability under a0–c interaction (epoch 644).

k=500 throughout. Baseline: a0=0.3, declared c_i.
  A) a0:0.3->0.6, declared c_i
  B) a0:0.3->0.6, all c_i -> 170
  C) a0=0.3, all c_i -> 75
  D) a0:0.3->0.6, all c_i -> 75

Writes all-pools and unsaturated-only figures + markdown tables.
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
OUT_ALL = DIR / "pool_viability_a0_c_interaction_all_epoch_644.png"
OUT_UNSAT = DIR / "pool_viability_a0_c_interaction_unsaturated_epoch_644.png"
OUT_CSV = DIR / "pool_viability_a0_c_interaction_epoch_644.csv"
OUT_MD = DIR / "pool_viability_a0_c_interaction_epoch_644.md"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD
A0_0, A0_1 = 0.3, 0.6
K = 500
C_FORCE_170 = 170.0
C_FORCE_75 = 75.0

CATEGORY_ORDER = (
    "losing_lt_025", "losing_025_050", "losing_050_075", "losing_075_100",
    "edge", "comfortable", "strong",
)
CATEGORY_LABELS = (
    r"$r<0.25$", r"$0.25\leq r<0.5$", r"$0.5\leq r<0.75$", r"$0.75\leq r<1$",
    "Edge\n" r"($1\leq r<2$)", "Comfortable\n" r"($2\leq r<5$)", "Strong\n" r"($r\geq5$)",
)
CATEGORY_COLORS = (
    "#67000d", "#a50f15", "#de2d26", "#fc9272", "#e76f51", "#4c78a8", "#2a9d8f",
)


def gross(sigma, declared, *, z0, r_over_t, a0):
    st = np.minimum(np.maximum(sigma, 0.0), z0)
    pt = np.minimum(np.maximum(declared, 0.0), z0)
    pt = np.minimum(pt, st)
    inner = st - pt * (z0 - st) / z0
    return (r_over_t / (1.0 + a0)) * (st + a0 * pt * inner / z0)


def operator_reward(f, cost, margin, active, sigma):
    share = np.clip(
        np.divide(active, sigma, out=np.zeros_like(active), where=sigma > 0),
        0.0, 1.0,
    )
    s = margin + (1.0 - margin) * share
    return np.where(f > cost, cost + (f - cost) * s, f)


def classify(ratio):
    if ratio < 0.25:
        return "losing_lt_025"
    if ratio < 0.5:
        return "losing_025_050"
    if ratio < 0.75:
        return "losing_050_075"
    if ratio < 1.0:
        return "losing_075_100"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def compute(sigma, declared, active, cost, margin, eligible, z0, r_over_t, a0):
    f_raw = gross(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    f = np.where(eligible, np.maximum(f_raw, 0.0), 0.0)
    pi = operator_reward(f, cost, margin, active, sigma)
    ratio = pi / C_STAR
    cats = np.array([classify(v) if m else "excluded" for v, m in zip(ratio, eligible)])
    heights = [int(pd.Series(cats[eligible]).value_counts().get(c, 0)) for c in CATEGORY_ORDER]
    n = int(eligible.sum())
    viable = int((ratio[eligible] >= 1.0).sum())
    losing = int(sum(heights[:4]))
    return heights, n, viable, losing, ratio, cats, f, pi


def draw_panel(ax, h0, h1, *, title, legend0, legend1, v0, l0, v1, l1):
    x = np.arange(len(CATEGORY_ORDER))
    w = 0.38
    ax.bar(x - w / 2, h0, w, color=CATEGORY_COLORS, edgecolor="white", lw=0.6, label=legend0)
    ax.bar(
        x + w / 2, h1, w, color=CATEGORY_COLORS, edgecolor="0.3", lw=0.8,
        hatch="//", alpha=0.80, label=legend1,
    )
    ymax = max(max(h0), max(h1), 1)
    for xi, (a, b) in enumerate(zip(h0, h1)):
        ax.text(xi - w / 2, a + ymax * 0.012, str(a), ha="center", va="bottom", fontsize=FONT_SIZE - 2)
        ax.text(xi + w / 2, b + ymax * 0.012, str(b), ha="center", va="bottom", fontsize=FONT_SIZE - 2)
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORY_LABELS, fontsize=FONT_SIZE - 1)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_ylim(0, ymax * 1.22)
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, loc="upper right")
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.grid(alpha=0.2, axis="y")
    ax.text(
        0.02, 0.97,
        f"Cover OpEx: {v0} → {v1}\nLosing: {l0} → {l1}",
        transform=ax.transAxes, ha="left", va="top", fontsize=FONT_SIZE - 1,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.75", "alpha": 0.95},
    )


def make_plot(h0, hA, hB, hC, hD, stats, out_path, subtitle):
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 10.5), constrained_layout=True)
    v0, l0 = stats["base"]
    draw_panel(
        axes[0, 0], h0, hA,
        title=r"A: $a_0\!:\,0.3\to0.6$, $c_i$ unchanged",
        legend0=r"$a_0=0.3$, decl. $c_i$", legend1=r"$a_0=0.6$, decl. $c_i$",
        v0=v0, l0=l0, v1=stats["A"][0], l1=stats["A"][1],
    )
    draw_panel(
        axes[0, 1], h0, hB,
        title=r"B: $a_0\!:\,0.3\to0.6$, all $c_i\to170$",
        legend0=r"$a_0=0.3$, decl. $c_i$", legend1=r"$a_0=0.6$, $c_i=170$",
        v0=v0, l0=l0, v1=stats["B"][0], l1=stats["B"][1],
    )
    draw_panel(
        axes[1, 0], h0, hC,
        title=r"C: $a_0=0.3$, all $c_i\to75$",
        legend0=r"$a_0=0.3$, decl. $c_i$", legend1=r"$a_0=0.3$, $c_i=75$",
        v0=v0, l0=l0, v1=stats["C"][0], l1=stats["C"][1],
    )
    draw_panel(
        axes[1, 1], h0, hD,
        title=r"D: $a_0\!:\,0.3\to0.6$, all $c_i\to75$",
        legend0=r"$a_0=0.3$, decl. $c_i$", legend1=r"$a_0=0.6$, $c_i=75$",
        v0=v0, l0=l0, v1=stats["D"][0], l1=stats["D"][1],
    )
    fig.suptitle(
        r"Epoch 644 — theoretical viability under $a_0$–$c$ interaction ($k=500$)"
        "\n" + subtitle,
        fontsize=FONT_SIZE,
    )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    r_over_t = R / T
    z0 = T / K

    df = pd.read_csv(POOLS_CSV)
    sigma = pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    complete = sigma.notna() & declared.notna() & active.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    cost_170 = np.full_like(cost_a, C_FORCE_170)
    cost_75 = np.full_like(cost_a, C_FORCE_75)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)
    unsat = sigma_a <= z0

    def run(eligible):
        h0, n0, v0, l0, r0, c0, f0, pi0 = compute(
            sigma_a, declared_a, active_a, cost_a, margin_a, eligible, z0, r_over_t, A0_0
        )
        hA, nA, vA, lA, rA, cA, fA, piA = compute(
            sigma_a, declared_a, active_a, cost_a, margin_a, eligible, z0, r_over_t, A0_1
        )
        hB, nB, vB, lB, rB, cB, fB, piB = compute(
            sigma_a, declared_a, active_a, cost_170, margin_a, eligible, z0, r_over_t, A0_1
        )
        hC, nC, vC, lC, rC, cC, fC, piC = compute(
            sigma_a, declared_a, active_a, cost_75, margin_a, eligible, z0, r_over_t, A0_0
        )
        hD, nD, vD, lD, rD, cD, fD, piD = compute(
            sigma_a, declared_a, active_a, cost_75, margin_a, eligible, z0, r_over_t, A0_1
        )
        return dict(
            h0=h0, hA=hA, hB=hB, hC=hC, hD=hD,
            n0=n0,
            stats={"base": (v0, l0), "A": (vA, lA), "B": (vB, lB), "C": (vC, lC), "D": (vD, lD)},
            ratios=(r0, rA, rB, rC, rD),
            cats=(c0, cA, cB, cC, cD),
        )

    all_ = run(pledge_met)
    uns_ = run(pledge_met & unsat)

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].values,
            "ticker": df.loc[complete, "pool_name.ticker"].values,
            "sigma_ada": sigma_a,
            "pledge_met": pledge_met,
            "unsaturated_k500": unsat,
            "r_base": all_["ratios"][0],
            "category_base": all_["cats"][0],
            "r_A": all_["ratios"][1],
            "category_A": all_["cats"][1],
            "r_B": all_["ratios"][2],
            "category_B": all_["cats"][2],
            "r_C": all_["ratios"][3],
            "category_C": all_["cats"][3],
            "r_D": all_["ratios"][4],
            "category_D": all_["cats"][4],
        }
    )
    out.to_csv(OUT_CSV, index=False)

    sub_common = (
        rf"$r=\Pi_i/C^*$, $C^*={C_STAR:.1f}$; $R={R/1e6:.2f}$M, $T={T/1e9:.2f}$B, $k={K}$"
    )
    make_plot(
        all_["h0"], all_["hA"], all_["hB"], all_["hC"], all_["hD"], all_["stats"], OUT_ALL,
        sub_common + f"; all pledge-met pools: {all_['n0']}",
    )
    n_ex = int((pledge_met & ~unsat).sum())
    make_plot(
        uns_["h0"], uns_["hA"], uns_["hB"], uns_["hC"], uns_["hD"], uns_["stats"], OUT_UNSAT,
        sub_common + rf"; unsaturated only: {uns_['n0']} (excluded oversat.: {n_ex})",
    )

    def table_block(label, s):
        v0, l0 = s["base"]
        rows = [
            ("Baseline", r"$a_0=0.3$, declared $c_i$", v0, l0),
            ("A", r"$a_0\to0.6$, declared $c_i$", s["A"][0], s["A"][1]),
            ("B", r"$a_0\to0.6$, all $c_i\to170$", s["B"][0], s["B"][1]),
            ("C", r"$a_0=0.3$, all $c_i\to75$", s["C"][0], s["C"][1]),
            ("D", r"$a_0\to0.6$, all $c_i\to75$", s["D"][0], s["D"][1]),
        ]
        lines = [
            f"### {label}",
            "",
            "| Panel | Scenario | Cover | Losing |",
            "|:---|:---|---:|---:|",
        ]
        for p, sc, v, l in rows:
            lines.append(f"| {p} | {sc} | {v} | {l} |")
        return "\n".join(lines)

    md = f"""# Pool viability — $a_0$–$c$ interaction (epoch 644)

$C^*={C_STAR:.1f}$ ADA/epoch, $R={R:,.2f}$ ADA, $T={T:,.2f}$ ADA, $k={K}$.

{table_block("All pledge-met pools", all_["stats"])}

{table_block(f"Unsaturated only ($\\sigma \\leq z_0({K})$)", uns_["stats"])}
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
