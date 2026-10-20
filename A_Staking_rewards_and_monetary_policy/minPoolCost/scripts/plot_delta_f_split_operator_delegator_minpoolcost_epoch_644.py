#!/usr/bin/env python3
"""Epoch 644 — split operator Π vs delegator rewards f-Π, declared c_i vs c_i=75.

Active pledge-met pools, merged snapshot. c does not enter f, so Δf=0;
the shock reallocates a fixed pie. k=500, a0, σ, p, p̂, m held fixed.

Writes:
  delta_f_split_operator_delegator_minpoolcost_epoch_644.png
  delta_f_split_operator_delegator_minpoolcost_epoch_644.csv
  delta_f_split_operator_delegator_minpoolcost_epoch_644.md
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from minpoolcost_common import (
    PARAMS_JSON,
    gross_pool_reward,
    load_active_pools,
    operator_reward,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_f_split_operator_delegator_minpoolcost_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_minpoolcost_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_minpoolcost_epoch_644.md"

FONT_SIZE = 12
C_FORCE = 75.0
COLOR_PI = "#4c78a8"
COLOR_DEL = "#e76f51"

Q_BINS = (0.0, 0.01, 0.25, 1.01)
Q_LABELS = (r"$q<0.01$", r"$0.01\leq q<0.25$", r"$q\geq 0.25$")
C_ORDER = ("c340", "c170", "c_other")
C_LABELS = (r"$c_i=340$", r"$c_i=170$", "other $c_i>75$")
C_MD = (r"$c_i=340$", r"$c_i=170$", r"other $c_i>75$")


def load_arrays():
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
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
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)
    return {
        "a0": a0,
        "k": k,
        "R": R,
        "T": T,
        "sigma": sigma_a,
        "declared": declared_a,
        "active": active_a,
        "cost": cost_a,
        "margin": margin_a,
        "pledge_met": pledge_met,
    }


def pool_frame(snap) -> pd.DataFrame:
    z0 = snap["T"] / snap["k"]
    f = gross_pool_reward(
        snap["sigma"], snap["declared"], z0=z0, r_over_t=snap["R"] / snap["T"], a0=snap["a0"]
    )
    f = np.where(snap["pledge_met"], np.maximum(f, 0.0), 0.0)
    pi0 = operator_reward(f, snap["cost"], snap["margin"], snap["active"], snap["sigma"])
    pi1 = operator_reward(
        f, np.full_like(snap["cost"], C_FORCE), snap["margin"], snap["active"], snap["sigma"]
    )
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
            "f": f,
            "pi0": pi0,
            "pi1": pi1,
            "delta_f": 0.0,
            "delta_pi": pi1 - pi0,
            "delta_delegator": (f - pi1) - (f - pi0),
            "pledge_met": snap["pledge_met"],
        }
    )
    d = d.loc[d["pledge_met"]].copy()
    d["s"] = d["margin"] + (1.0 - d["margin"]) * d["q"]
    d["q_bin"] = pd.cut(d["q"], Q_BINS, right=False, include_lowest=True)
    is_340 = np.isclose(d["cost"], 340.0, atol=0.51)
    is_170 = np.isclose(d["cost"], 170.0, atol=0.51)
    d["c_bin"] = np.where(is_340, "c340", np.where(is_170, "c170", "c_other"))
    return d


def summarize(g: pd.DataFrame, group: str, label: str) -> dict:
    df_sum = float(g["delta_f"].sum())
    dpi = float(g["delta_pi"].sum())
    return {
        "group": group,
        "label": label,
        "n": int(len(g)),
        "sum_delta_f": df_sum,
        "sum_delta_pi": dpi,
        "sum_delta_delegator": float(g["delta_delegator"].sum()),
        "share_pi_of_delta_f": float("nan"),
        "median_delta_f": float(g["delta_f"].median()),
        "median_delta_pi": float(g["delta_pi"].median()),
        "median_delta_delegator": float(g["delta_delegator"].median()),
        "median_q": float(g["q"].median()),
        "median_margin": float(g["margin"].median()),
        "median_s": float(g["s"].median()),
        "median_c": float(g["cost"].median()),
        "n_margin_one": int((g["margin"] >= 0.999).sum()),
        "n_f_le_c0": int((g["f"] <= g["cost"]).sum()),
        "n_new_f_gt_c": int(((g["f"] <= g["cost"]) & (g["f"] > C_FORCE)).sum()),
        "n_f_le_c1": int((g["f"] <= C_FORCE).sum()),
    }


def fmt_ada(x: float) -> str:
    return f"{x:,.0f}"


def md_table(rows: list[dict]) -> str:
    header = (
        "| Group | $n$ | $\\sum\\Delta f$ | $\\sum\\Delta\\Pi$ | "
        "$\\sum\\Delta(f-\\Pi)$ | median $\\Delta\\Pi$ | median $\\Delta(f-\\Pi)$ | "
        "median $q$ | median $m$ | median $s$ |\n"
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    lines = [header]
    for r in rows:
        lines.append(
            "| {label} | {n} | {sf} | {sp} | {sd} | {mp} | {md} | {q} | {m} | {s} |".format(
                label=r["label"],
                n=r["n"],
                sf=fmt_ada(r["sum_delta_f"]),
                sp=fmt_ada(r["sum_delta_pi"]),
                sd=fmt_ada(r["sum_delta_delegator"]),
                mp=f"{r['median_delta_pi']:,.0f}",
                md=f"{r['median_delta_delegator']:,.0f}",
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
        offset = 0.018 * ymax if h >= 0 else -0.018 * ymax
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
    ax.legend(fontsize=FONT_SIZE - 1, loc="upper right")
    ax.grid(alpha=0.2, axis="y")
    ax.set_ylim(-160, 160)
    annotate_bars(ax, list(b1) + list(b2))


def main() -> None:
    snap = load_arrays()
    d = pool_frame(snap)

    all_row = summarize(d, "all", "All Active")
    q_rows = []
    q_keys = []
    for cat, lab in zip(list(d["q_bin"].cat.categories), Q_LABELS):
        key = f"q_{cat}"
        q_keys.append(key)
        q_rows.append(summarize(d.loc[d["q_bin"] == cat], key, lab))
    c_rows = []
    for key, lab in zip(C_ORDER, C_MD):
        c_rows.append(summarize(d.loc[d["c_bin"] == key], key, lab))

    out = pd.DataFrame([all_row] + q_rows + c_rows)
    out.insert(0, "section", ["all"] + ["q"] * len(q_rows) + ["declared_c"] * len(c_rows))
    out.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    grouped_panel(axes[0], q_rows, q_keys, Q_LABELS, r"By $q=\hat p/\sigma$")
    grouped_panel(axes[1], c_rows, list(C_ORDER), C_LABELS, r"By declared $c_i$")
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta\Pi$ and $\Delta(f-\Pi)$ when all $c_i=75$"
        "\n"
        rf"($f$ unchanged; $k={snap['k']}$; snapshot $\sigma,p,\hat p,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    n_new = int(((d["f"] <= d["cost"]) & (d["f"] > C_FORCE)).sum())
    n_still = int((d["f"] <= C_FORCE).sum())
    n_lose = int((d["delta_pi"] < -1e-8).sum())
    n_flat = int((d["delta_pi"].abs() <= 1e-8).sum())
    md = f"""# Operator vs delegator rewards — minPoolCost $c_i=75$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. Declared $c_i$ vs all $c_i={int(C_FORCE)}$.
$k={snap['k']}$. $R={snap['R']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
$f$ is unchanged ($c$ does not enter $f$). $q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.
Operators with $\\Delta\\Pi<0$: {n_lose}. Unchanged: {n_flat}.
Newly $f>c$: {n_new}. Still $f\\le 75$: {n_still}.

## All Active

{md_table([all_row])}

## By $q=\\hat p/\\sigma$

{md_table(q_rows)}

## By declared $c_i$

{md_table(c_rows)}
"""
    OUT_MD.write_text(md)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    print(
        f"all n={all_row['n']} sum_dPi={all_row['sum_delta_pi']:.1f} "
        f"sum_dM={all_row['sum_delta_delegator']:.1f} "
        f"n_new_fgtc={n_new} n_still={n_still} n_lose={n_lose} n_flat={n_flat}"
    )


if __name__ == "__main__":
    main()
