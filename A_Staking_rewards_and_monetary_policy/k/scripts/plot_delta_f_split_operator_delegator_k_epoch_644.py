#!/usr/bin/env python3
"""Epoch 644 — split Δf into operator Π and delegator rewards f-Π, k=500→1000.

Active pledge-met pools, merged snapshot. k changes z0 and therefore f;
declared c_i, m_i, σ, p, p̂ held fixed.

Writes:
  delta_f_split_operator_delegator_k_epoch_644.png
  delta_f_split_operator_delegator_k_epoch_644.csv
  delta_f_split_operator_delegator_k_epoch_644.md
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from viability_price_cost_k_common import (
    FONT_SIZE,
    PARAMS_JSON,
    gross_pool_reward,
    load_active_pools,
    operator_reward,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_f_split_operator_delegator_k_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_k_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_k_epoch_644.md"

K0, K1 = 500, 1000
COLOR_PI = "#4c78a8"
COLOR_DEL = "#e76f51"

SAT_ORDER = ("unsat", "newly", "already")
SAT_LABELS = (
    "Remain\nunsaturated",
    "Newly\noversaturated",
    "Already\noversaturated",
)
SAT_MD = (
    r"Remain unsaturated ($\sigma\le z_0(1000)$)",
    r"Newly oversaturated ($z_0(1000)<\sigma\le z_0(500)$)",
    r"Already oversaturated ($\sigma>z_0(500)$)",
)
Q_BINS = (0.0, 0.01, 0.25, 1.01)
Q_LABELS = (r"$q<0.01$", r"$0.01\leq q<0.25$", r"$q\geq 0.25$")


def load_arrays():
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    df = load_active_pools()
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce") / 1e6
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["live_pledge"].fillna(df["pledged"]), errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    complete = sigma.notna() & declared.notna() & active.notna() & cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)
    return {
        "a0": a0,
        "R": R,
        "T": T,
        "sigma": sigma_a,
        "declared": declared_a,
        "active": active_a,
        "cost": cost_a,
        "margin": margin_a,
        "pledge_met": pledge_met,
    }


def f_at(snap, k: int) -> np.ndarray:
    z0 = snap["T"] / k
    f = gross_pool_reward(
        snap["sigma"], snap["declared"], z0=z0, r_over_t=snap["R"] / snap["T"], a0=snap["a0"]
    )
    return np.where(snap["pledge_met"], np.maximum(f, 0.0), 0.0)


def pool_frame(snap) -> pd.DataFrame:
    f0 = f_at(snap, K0)
    f1 = f_at(snap, K1)
    pi0 = operator_reward(f0, snap["cost"], snap["margin"], snap["active"], snap["sigma"])
    pi1 = operator_reward(f1, snap["cost"], snap["margin"], snap["active"], snap["sigma"])
    q = np.clip(
        np.divide(
            snap["active"],
            snap["sigma"],
            out=np.zeros_like(snap["active"]),
            where=snap["sigma"] > 0,
        ),
        0.0,
        1.0,
    )
    d = pd.DataFrame(
        {
            "sigma": snap["sigma"],
            "q": q,
            "margin": snap["margin"],
            "cost": snap["cost"],
            "f0": f0,
            "f1": f1,
            "pi0": pi0,
            "pi1": pi1,
            "delta_f": f1 - f0,
            "delta_pi": pi1 - pi0,
            "delta_delegator": (f1 - pi1) - (f0 - pi0),
            "pledge_met": snap["pledge_met"],
        }
    )
    d = d.loc[d["pledge_met"]].copy()
    d["s"] = d["margin"] + (1.0 - d["margin"]) * d["q"]
    z0_0 = snap["T"] / K0
    z0_1 = snap["T"] / K1
    d["sat"] = np.where(
        d["sigma"] <= z0_1,
        "unsat",
        np.where(d["sigma"] <= z0_0, "newly", "already"),
    )
    d["q_bin"] = pd.cut(d["q"], Q_BINS, right=False, include_lowest=True)
    return d


def summarize(g: pd.DataFrame, group: str, label: str) -> dict:
    df_sum = float(g["delta_f"].sum())
    return {
        "group": group,
        "label": label,
        "n": int(len(g)),
        "sum_delta_f": df_sum,
        "sum_delta_pi": float(g["delta_pi"].sum()),
        "sum_delta_delegator": float(g["delta_delegator"].sum()),
        "share_pi_of_delta_f": float(g["delta_pi"].sum() / df_sum) if df_sum != 0 else float("nan"),
        "median_delta_f": float(g["delta_f"].median()),
        "median_delta_pi": float(g["delta_pi"].median()),
        "median_delta_delegator": float(g["delta_delegator"].median()),
        "median_q": float(g["q"].median()),
        "median_margin": float(g["margin"].median()),
        "median_s": float(g["s"].median()),
        "median_sigma": float(g["sigma"].median()),
        "n_margin_one": int((g["margin"] >= 0.999).sum()),
    }


def fmt_ada(x: float) -> str:
    return f"{x:,.0f}"


def fmt_pct(x: float) -> str:
    if not np.isfinite(x):
        return "—"
    return f"{100.0 * x:.1f}%"


def md_table(rows: list[dict]) -> str:
    header = (
        "| Group | $n$ | $\\sum\\Delta f$ | $\\sum\\Delta\\Pi$ | "
        "$\\sum\\Delta(f-\\Pi)$ | $\\sum\\Delta\\Pi/\\sum\\Delta f$ | "
        "median $\\Delta f$ | median $q$ | median $m$ | median $s$ | $n$ with $m=1$ |\n"
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    lines = [header]
    for r in rows:
        lines.append(
            "| {label} | {n} | {sf} | {sp} | {sd} | {sh} | {mf} | {q} | {m} | {s} | {nm} |".format(
                label=r["label"],
                n=r["n"],
                sf=fmt_ada(r["sum_delta_f"]),
                sp=fmt_ada(r["sum_delta_pi"]),
                sd=fmt_ada(r["sum_delta_delegator"]),
                sh=fmt_pct(r["share_pi_of_delta_f"]),
                mf=f"{r['median_delta_f']:,.2f}",
                q=f"{r['median_q']:.3f}",
                m=f"{100.0 * r['median_margin']:.1f}\\%",
                s=f"{r['median_s']:.3f}",
                nm=r["n_margin_one"],
            )
        )
    return "\n".join(lines)


def annotate_bars(ax, bars) -> None:
    ymax = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]), 1.0)
    for bar in bars:
        h = bar.get_height()
        if abs(h) < 2.0:
            continue
        va = "bottom" if h >= 0 else "top"
        offset = 0.012 * ymax if h >= 0 else -0.012 * ymax
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + offset,
            f"{h:,.0f}",
            ha="center",
            va=va,
            fontsize=FONT_SIZE - 2,
        )


def main() -> None:
    snap = load_arrays()
    d = pool_frame(snap)
    z0_0 = snap["T"] / K0
    z0_1 = snap["T"] / K1

    sat_rows = []
    sat_rows.append(summarize(d, "all", "All Active"))
    for key, lab in zip(SAT_ORDER, SAT_MD):
        sat_rows.append(summarize(d.loc[d["sat"] == key], key, lab))

    newly = d.loc[d["sat"] == "newly"]
    q_rows = []
    q_cats = list(newly["q_bin"].cat.categories)
    for cat, lab in zip(q_cats, Q_LABELS):
        q_rows.append(summarize(newly.loc[newly["q_bin"] == cat], f"newly_{cat}", lab))

    out = pd.DataFrame(sat_rows + q_rows)
    out.insert(0, "section", ["saturation"] * len(sat_rows) + ["newly_q"] * len(q_rows))
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    w = 0.36
    x = np.arange(len(SAT_ORDER))
    pi_sat = [next(r for r in sat_rows if r["group"] == k)["sum_delta_pi"] / 1e3 for k in SAT_ORDER]
    del_sat = [
        next(r for r in sat_rows if r["group"] == k)["sum_delta_delegator"] / 1e3 for k in SAT_ORDER
    ]
    n_sat = [next(r for r in sat_rows if r["group"] == k)["n"] for k in SAT_ORDER]
    b1 = axes[0].bar(
        x - w / 2, pi_sat, w, color=COLOR_PI, edgecolor="white", label=r"$\Delta\Pi$ (operator)"
    )
    b2 = axes[0].bar(
        x + w / 2, del_sat, w, color=COLOR_DEL, edgecolor="white",
        label=r"$\Delta(f-\Pi)$ (delegators)",
    )
    axes[0].axhline(0.0, color="0.3", lw=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(
        [f"{lab}\n(n={n})" for lab, n in zip(SAT_LABELS, n_sat)],
        fontsize=FONT_SIZE - 1,
    )
    axes[0].set_ylabel(r"ADA/epoch (thousands)", fontsize=FONT_SIZE)
    axes[0].set_title(r"By saturation status", fontsize=FONT_SIZE)
    axes[0].tick_params(axis="y", labelsize=FONT_SIZE - 1)
    axes[0].legend(fontsize=FONT_SIZE - 1, loc="lower left")
    axes[0].grid(alpha=0.2, axis="y")
    axes[0].set_ylim(-1100, 80)
    annotate_bars(axes[0], list(b1) + list(b2))

    xq = np.arange(len(Q_LABELS))
    pi_q = [r["sum_delta_pi"] / 1e3 for r in q_rows]
    del_q = [r["sum_delta_delegator"] / 1e3 for r in q_rows]
    n_q = [r["n"] for r in q_rows]
    b3 = axes[1].bar(
        xq - w / 2, pi_q, w, color=COLOR_PI, edgecolor="white", label=r"$\Delta\Pi$ (operator)"
    )
    b4 = axes[1].bar(
        xq + w / 2, del_q, w, color=COLOR_DEL, edgecolor="white",
        label=r"$\Delta(f-\Pi)$ (delegators)",
    )
    axes[1].axhline(0.0, color="0.3", lw=0.8)
    axes[1].set_xticks(xq)
    axes[1].set_xticklabels(
        [f"{lab}\n(n={n})" for lab, n in zip(Q_LABELS, n_q)],
        fontsize=FONT_SIZE - 1,
    )
    axes[1].set_ylabel(r"ADA/epoch (thousands)", fontsize=FONT_SIZE)
    axes[1].set_title(r"Newly oversaturated, by $q=\hat p/\sigma$", fontsize=FONT_SIZE)
    axes[1].tick_params(axis="y", labelsize=FONT_SIZE - 1)
    axes[1].legend(fontsize=FONT_SIZE - 1, loc="lower left")
    axes[1].grid(alpha=0.2, axis="y")
    axes[1].set_ylim(-1100, 80)
    annotate_bars(axes[1], list(b3) + list(b4))

    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        rf"($k={K0}\to{K1}$; $z_0={z0_0/1e6:.1f}$M$\to{z0_1/1e6:.1f}$M ADA; "
        r"snapshot $\sigma,p,\hat p,c,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    all_row = sat_rows[0]
    newly_row = next(r for r in sat_rows if r["group"] == "newly")
    md = f"""# $\\Delta f$ split into operator $\\Pi$ and delegator rewards — $k$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. $k={K0}\\to{K1}$,
$z_0={z0_0/1e6:.2f}$M$\\to{z0_1/1e6:.2f}$M ADA.
$R={snap['R']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
Declared $c_i$, $m_i$, $\\sigma$, $p$, $\\hat p$ held fixed.
$q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.

## By saturation status

{md_table(sat_rows)}

## Newly oversaturated, by $q=\\hat p/\\sigma$

{md_table(q_rows)}

All Active: $\\sum\\Delta f={fmt_ada(all_row['sum_delta_f'])}$,
$\\sum\\Delta\\Pi={fmt_ada(all_row['sum_delta_pi'])}$
({fmt_pct(all_row['share_pi_of_delta_f'])} of $\\Delta f$),
$\\sum\\Delta(f-\\Pi)={fmt_ada(all_row['sum_delta_delegator'])}$.
Newly oversaturated ($n={newly_row['n']}$):
$\\sum\\Delta f={fmt_ada(newly_row['sum_delta_f'])}$.
"""
    OUT_MD.write_text(md)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    print(
        f"all n={all_row['n']} sum_df={all_row['sum_delta_f']:.1f} "
        f"sum_dPi={all_row['sum_delta_pi']:.1f} "
        f"share={all_row['share_pi_of_delta_f']:.3f}"
    )
    print(
        f"newly n={newly_row['n']} sum_df={newly_row['sum_delta_f']:.1f} "
        f"share={newly_row['share_pi_of_delta_f']:.3f}"
    )


if __name__ == "__main__":
    main()
