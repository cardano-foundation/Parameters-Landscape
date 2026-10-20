#!/usr/bin/env python3
"""Epoch 644 — split Δf into operator Π and delegator rewards f-Π, a0=0.3→0.6.

Active pledge-met pools, merged snapshot. a0 changes f; k=500 and
declared c_i, m_i, σ, p, p̂ held fixed.

Writes:
  delta_f_split_operator_delegator_a0_epoch_644.png
  delta_f_split_operator_delegator_a0_epoch_644.csv
  delta_f_split_operator_delegator_a0_epoch_644.md
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from a0_common import PARAMS_JSON, gross_pool_reward, load_active_pools

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_f_split_operator_delegator_a0_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_a0_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_a0_epoch_644.md"

FONT_SIZE = 12
A0_0, A0_1 = 0.3, 0.6
COLOR_PI = "#4c78a8"
COLOR_DEL = "#e76f51"

Q_BINS = (0.0, 0.01, 0.25, 1.01)
Q_LABELS = (r"$q<0.01$", r"$0.01\leq q<0.25$", r"$q\geq 0.25$")
P_ORDER = ("p_lt_100k", "p_100k_1m", "p_ge_1m")
P_LABELS = ("p < 100k", "100k ≤ p < 1M", "p ≥ 1M")
P_MD = (
    r"$p<100$k ADA",
    r"$100$k$\leq p<1$M ADA",
    r"$p\geq 1$M ADA",
)


def operator_reward(f, fixed_cost, margin, active_pledge, sigma):
    pledge_share = np.clip(
        np.divide(
            active_pledge,
            sigma,
            out=np.zeros_like(active_pledge),
            where=sigma > 0,
        ),
        0.0,
        1.0,
    )
    s = margin + (1.0 - margin) * pledge_share
    return np.where(f > fixed_cost, fixed_cost + (f - fixed_cost) * s, f)


def load_arrays():
    params = json.loads(PARAMS_JSON.read_text())
    k = int(params["k"])
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
    return {
        "k": k,
        "R": R,
        "T": T,
        "sigma": sigma[complete].to_numpy(dtype=float),
        "declared": declared[complete].to_numpy(dtype=float),
        "active": active[complete].to_numpy(dtype=float),
        "cost": cost[complete].to_numpy(dtype=float),
        "margin": margin[complete].to_numpy(dtype=float),
        "pledge_met": (
            (active[complete].to_numpy(dtype=float) >= declared[complete].to_numpy(dtype=float))
            & (sigma[complete].to_numpy(dtype=float) > 0)
        ),
    }


def f_at(snap, a0: float) -> np.ndarray:
    z0 = snap["T"] / snap["k"]
    f = gross_pool_reward(
        snap["sigma"], snap["declared"], z0=z0, r_over_t=snap["R"] / snap["T"], a0=a0
    )
    return np.where(snap["pledge_met"], np.maximum(f, 0.0), 0.0)


def pool_frame(snap) -> pd.DataFrame:
    f0 = f_at(snap, A0_0)
    f1 = f_at(snap, A0_1)
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
            "declared": snap["declared"],
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
    d["q_bin"] = pd.cut(d["q"], Q_BINS, right=False, include_lowest=True)
    d["p_bin"] = np.where(
        d["declared"] < 1e5,
        "p_lt_100k",
        np.where(d["declared"] < 1e6, "p_100k_1m", "p_ge_1m"),
    )
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
        "median_p": float(g["declared"].median()),
        "n_margin_one": int((g["margin"] >= 0.999).sum()),
        "n_cross_down": int(((g["f0"] > g["cost"]) & (g["f1"] <= g["cost"])).sum()),
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
        "median $\\Delta f$ | median $q$ | median $m$ | median $s$ |\n"
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    lines = [header]
    for r in rows:
        lines.append(
            "| {label} | {n} | {sf} | {sp} | {sd} | {sh} | {mf} | {q} | {m} | {s} |".format(
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


def grouped_panel(ax, rows, keys, labels, title):
    w = 0.36
    x = np.arange(len(keys))
    pi = [next(r for r in rows if r["group"] == k)["sum_delta_pi"] / 1e3 for k in keys]
    deleg = [next(r for r in rows if r["group"] == k)["sum_delta_delegator"] / 1e3 for k in keys]
    ns = [next(r for r in rows if r["group"] == k)["n"] for k in keys]
    b1 = ax.bar(x - w / 2, pi, w, color=COLOR_PI, edgecolor="white", label=r"$\Delta\Pi$ (operator)")
    b2 = ax.bar(
        x + w / 2, deleg, w, color=COLOR_DEL, edgecolor="white",
        label=r"$\Delta(f-\Pi)$ (delegators)",
    )
    ax.axhline(0.0, color="0.3", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f"{lab}\n(n={n})" for lab, n in zip(labels, ns)],
        fontsize=FONT_SIZE - 1,
    )
    ax.set_ylabel(r"ADA/epoch (thousands)", fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
    ax.legend(fontsize=FONT_SIZE - 1, loc="lower right")
    ax.grid(alpha=0.2, axis="y")
    ax.set_ylim(-900, 50)
    annotate_bars(ax, list(b1) + list(b2))


def main() -> None:
    snap = load_arrays()
    d = pool_frame(snap)

    all_row = summarize(d, "all", "All Active")
    q_rows = []
    q_cats = list(d["q_bin"].cat.categories)
    q_keys = []
    for cat, lab in zip(q_cats, Q_LABELS):
        key = f"q_{cat}"
        q_keys.append(key)
        q_rows.append(summarize(d.loc[d["q_bin"] == cat], key, lab))
    p_rows = []
    for key, lab in zip(P_ORDER, P_MD):
        p_rows.append(summarize(d.loc[d["p_bin"] == key], key, lab))

    out = pd.DataFrame([all_row] + q_rows + p_rows)
    out.insert(0, "section", ["all"] + ["q"] * len(q_rows) + ["declared_p"] * len(p_rows))
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    grouped_panel(axes[0], q_rows, q_keys, Q_LABELS, r"By $q=\hat p/\sigma$")
    grouped_panel(axes[1], p_rows, list(P_ORDER), P_LABELS, r"By declared pledge $p$")
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        rf"($a_0={A0_0}\to{A0_1}$; $k={snap['k']}$; "
        r"snapshot $\sigma,p,\hat p,c,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    n_cross = int(((d["f0"] > d["cost"]) & (d["f1"] <= d["cost"])).sum())
    md = f"""# $\\Delta f$ split into operator $\\Pi$ and delegator rewards — $a_0$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. $a_0={A0_0}\\to{A0_1}$, $k={snap['k']}$.
$R={snap['R']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
Declared $c_i$, $m_i$, $\\sigma$, $p$, $\\hat p$ held fixed.
$q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.
Pools that cross $f>c$ to $f\\le c$: ${n_cross}$.

## All Active

{md_table([all_row])}

## By $q=\\hat p/\\sigma$

{md_table(q_rows)}

## By declared pledge $p$

{md_table(p_rows)}
"""
    OUT_MD.write_text(md)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    print(
        f"all n={all_row['n']} sum_df={all_row['sum_delta_f']:.1f} "
        f"sum_dPi={all_row['sum_delta_pi']:.1f} "
        f"share={all_row['share_pi_of_delta_f']:.3f} n_cross={n_cross}"
    )


if __name__ == "__main__":
    main()
