#!/usr/bin/env python3
"""Epoch 644 — Δf split into Π and f-Π, rho=0.003→0.0042.

Active pledge-met pools, merged snapshot. rho scales R and therefore f;
declared c_i, m_i, σ, p, p̂, k, a0 held fixed.

Writes:
  delta_f_split_operator_delegator_rho_epoch_644.png
  delta_f_split_operator_delegator_rho_epoch_644.csv
  delta_f_split_operator_delegator_rho_epoch_644.md
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rho_comparison_common import (
    FONT_SIZE,
    PARAMS_JSON,
    POOLS_CSV,
    RHO_BASE,
    RHO_NEW,
    gross_pool_reward,
    operator_reward,
)

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
FLAGS_CSV = ROOT / "inactive_pool_flags_koios_epoch_644_last15.csv"
OUT_PNG = DIR / "delta_f_split_operator_delegator_rho_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_rho_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_rho_epoch_644.md"

COLOR_PI = "#4c78a8"
COLOR_DEL = "#e76f51"
Q_BINS = (0.0, 0.01, 0.25, 1.01)
Q_LABELS = (r"$q<0.01$", r"$0.01\leq q<0.25$", r"$q\geq 0.25$")
FC_ORDER = ("still", "newly", "already")
FC_LABELS = (r"Still" "\n" r"$f\leq c$", r"Newly" "\n" r"$f>c$", r"Already" "\n" r"$f>c$")
FC_MD = (
    r"Still $f\le c$",
    r"Newly $f>c$",
    r"Already $f>c$",
)


def load_active_pools() -> pd.DataFrame:
    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")
    return df.loc[df["in_union"] == 0].copy()


def load_arrays():
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    k = int(params["k"])
    r0 = float(params["R_ada"])
    t = float(params["T_supply_ada"])
    r1 = r0 * (RHO_NEW / RHO_BASE)
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
        "R0": r0,
        "R1": r1,
        "T": t,
        "sigma": sigma_a,
        "declared": declared_a,
        "active": active_a,
        "cost": cost_a,
        "margin": margin_a,
        "pledge_met": pledge_met,
    }


def f_at(snap, r_ada: float) -> np.ndarray:
    z0 = snap["T"] / snap["k"]
    f = gross_pool_reward(
        snap["sigma"], snap["declared"], z0=z0, r_over_t=r_ada / snap["T"], a0=snap["a0"]
    )
    return np.where(snap["pledge_met"], np.maximum(f, 0.0), 0.0)


def pool_frame(snap) -> pd.DataFrame:
    f0 = f_at(snap, snap["R0"])
    f1 = f_at(snap, snap["R1"])
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
    d["fc"] = np.where(
        d["f1"] <= d["cost"],
        "still",
        np.where(d["f0"] <= d["cost"], "newly", "already"),
    )
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
        "share_pi_of_delta_f": (dpi / df_sum) if df_sum != 0 else float("nan"),
        "median_delta_f": float(g["delta_f"].median()),
        "median_delta_pi": float(g["delta_pi"].median()),
        "median_delta_delegator": float(g["delta_delegator"].median()),
        "median_q": float(g["q"].median()),
        "median_margin": float(g["margin"].median()),
        "median_s": float(g["s"].median()),
        "n_margin_one": int((g["margin"] >= 0.999).sum()),
    }


def fmt_ada(x: float) -> str:
    return f"{x:,.0f}"


def fmt_median(x: float) -> str:
    if abs(x) < 0.05:
        return "0.00"
    if abs(x) < 10:
        return f"{x:,.2f}"
    return f"{x:,.0f}"


def fmt_pct(x: float) -> str:
    if not np.isfinite(x) or x < 0.0 or x > 1.0:
        return "—"
    return f"{100.0 * x:.1f}%"


def md_table(rows: list[dict]) -> str:
    header = (
        "| Group | $n$ | $\\sum\\Delta f$ | $\\sum\\Delta\\Pi$ | "
        "$\\sum\\Delta(f-\\Pi)$ | $\\sum\\Delta\\Pi/\\sum\\Delta f$ | "
        "median $\\Delta f$ | median $\\Delta\\Pi$ | median $\\Delta(f-\\Pi)$ | "
        "median $q$ | median $s$ |\n"
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    lines = [header]
    for r in rows:
        lines.append(
            "| {label} | {n} | {sf} | {sp} | {sd} | {sh} | {mf} | {mp} | {mdv} | {q} | {s} |".format(
                label=r["label"],
                n=f"{r['n']:,}",
                sf=fmt_ada(r["sum_delta_f"]),
                sp=fmt_ada(r["sum_delta_pi"]),
                sd=fmt_ada(r["sum_delta_delegator"]),
                sh=fmt_pct(r["share_pi_of_delta_f"]),
                mf=fmt_median(r["median_delta_f"]),
                mp=fmt_median(r["median_delta_pi"]),
                mdv=fmt_median(r["median_delta_delegator"]),
                q=f"{r['median_q']:.3f}",
                s=f"{r['median_s']:.3f}",
            )
        )
    return "\n".join(lines)


def annotate_bars(ax, bars) -> None:
    ymax = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]), 1.0)
    for bar in bars:
        h = bar.get_height()
        if abs(h) < 10.0:
            continue
        va = "bottom" if h >= 0 else "top"
        offset = 0.02 * ymax if h >= 0 else -0.02 * ymax
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + offset,
            f"{h:,.0f}",
            ha="center",
            va=va,
            fontsize=FONT_SIZE - 2,
        )


def grouped_panel(ax, rows, keys, labels, title, *, legend_loc="upper right"):
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
    ax.legend(fontsize=FONT_SIZE - 1, loc=legend_loc)
    ax.grid(alpha=0.2, axis="y")
    vals = list(pi) + list(deleg)
    hi = max(0.0, max(vals))
    lo = min(0.0, min(vals))
    pad = 0.22 * max(abs(lo), abs(hi), 1.0)
    if lo >= -1e-9:
        ax.set_ylim(0.0, hi + pad)
    else:
        ax.set_ylim(lo - pad, hi + pad)
    annotate_bars(ax, list(b1) + list(b2))


def main() -> None:
    snap = load_arrays()
    d = pool_frame(snap)
    all_row = summarize(d, "all", "All Active")
    fc_rows = [summarize(d.loc[d["fc"] == key], key, lab) for key, lab in zip(FC_ORDER, FC_MD)]
    q_rows = []
    for cat, lab in zip(list(d["q_bin"].cat.categories), Q_LABELS):
        q_rows.append(summarize(d.loc[d["q_bin"] == cat], f"q_{cat}", lab))

    pd.DataFrame([all_row] + fc_rows + q_rows).assign(
        section=["all"] + ["fc"] * len(fc_rows) + ["q"] * len(q_rows)
    ).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    grouped_panel(
        axes[0], fc_rows, list(FC_ORDER), FC_LABELS,
        r"By $f$ vs declared $c$", legend_loc="upper left",
    )
    grouped_panel(
        axes[1], q_rows, [r["group"] for r in q_rows], Q_LABELS,
        r"By $q=\hat p/\sigma$", legend_loc="upper right",
    )
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        rf"($\rho={RHO_BASE}\to{RHO_NEW}$; $k={snap['k']}$; "
        r"snapshot $\sigma,p,\hat p,c,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    OUT_MD.write_text(
        f"""# $\\Delta f$ split into operator $\\Pi$ and delegator rewards — $\\rho$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. $\\rho={RHO_BASE}\\to{RHO_NEW}$, $k={snap['k']}$.
$R={snap['R0']:,.2f}\\to{snap['R1']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
Declared $c_i$, $m_i$, $\\sigma$, $p$, $\\hat p$ held fixed.
$q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.

## All Active

{md_table([all_row])}

## By $f$ vs declared $c$

{md_table(fc_rows)}

## By $q=\\hat p/\\sigma$

{md_table(q_rows)}
"""
    )
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")
    print(
        f"all n={all_row['n']} df={all_row['sum_delta_f']:.1f} "
        f"dPi={all_row['sum_delta_pi']:.1f} dM={all_row['sum_delta_delegator']:.1f} "
        f"share={all_row['share_pi_of_delta_f']:.3f}"
    )
    for r in fc_rows:
        print(f"  {r['group']} n={r['n']} df={r['sum_delta_f']:.1f} dPi={r['sum_delta_pi']:.1f}")


if __name__ == "__main__":
    main()
