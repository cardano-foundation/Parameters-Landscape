#!/usr/bin/env python3
"""C.2 — change in share of pools with r≥1 by 5M stake bin, k / a0 / c.

Writes:
  delta_rge1_share_by_bin_epoch_644.png
  delta_rge1_share_by_bin_epoch_644.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comparison_common import (
    FONT_SIZE,
    assign_stake_bins,
    load_snapshot,
    outcomes_from_spec,
    spec_by_key,
    stake_bin_labels,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_rge1_share_by_bin_epoch_644.png"
OUT_CSV = DIR / "delta_rge1_share_by_bin_epoch_644.csv"

SHOCKS = (
    ("k", r"$k=1000$", "#4c78a8"),
    ("a0", r"$a_0=0.6$", "#f2a65a"),
    ("c", r"$c_i=75$", "#e76f51"),
)


def share_rge1(r, met, bin_idx, n_bins):
    n = np.zeros(n_bins)
    g = np.zeros(n_bins)
    for b in range(n_bins):
        m = bin_idx == b
        n[b] = float(m.sum())
        g[b] = float((m & met & (r >= 1.0)).sum())
    with np.errstate(invalid="ignore", divide="ignore"):
        pct = np.where(n > 0, 100.0 * g / n, np.nan)
    return n, g, pct


def main() -> None:
    snap = load_snapshot()
    edges, labels = stake_bin_labels()
    n_bins = len(labels)
    bin_idx = assign_stake_bins(snap["sigma"] / 1e6, edges)
    base = outcomes_from_spec(snap, spec_by_key(snap, "base"))
    n0, g0, p0 = share_rge1(base["r"], base["met"], bin_idx, n_bins)

    rows = []
    deltas = {}
    for key, lab, _ in SHOCKS:
        out = outcomes_from_spec(snap, spec_by_key(snap, key))
        n1, g1, p1 = share_rge1(out["r"], out["met"], bin_idx, n_bins)
        d = p1 - p0
        deltas[key] = d
        for j, blab in enumerate(labels):
            rows.append(
                {
                    "shock": key,
                    "stake_bin_M_ADA": blab,
                    "n_bin": int(n0[j]),
                    "n_r_ge1_base": int(g0[j]),
                    "n_r_ge1": int(g1[j]),
                    "share_r_ge1_base_pct": float(p0[j]),
                    "share_r_ge1_pct": float(p1[j]),
                    "delta_share_pp": float(d[j]),
                }
            )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x = np.arange(n_bins)
    w = 0.26
    offsets = (-w, 0.0, w)
    fig, ax = plt.subplots(figsize=(13.6, 5.6), constrained_layout=True)
    for off, (key, lab, col) in zip(offsets, SHOCKS):
        d = deltas[key]
        ax.bar(x + off, d, w, color=col, edgecolor="white", label=lab)
    ax.axhline(0.0, color="0.3", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=FONT_SIZE - 2)
    ax.set_ylabel(r"$\Delta$ share of pools with $r\geq 1$ (pp)", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
    ax.legend(
        fontsize=FONT_SIZE - 1, ncol=3, loc="upper center",
        bbox_to_anchor=(0.5, -0.18), frameon=False,
    )
    ax.grid(axis="y", alpha=0.25)
    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        r"Epoch 644 — change in bin viability share, without $\rho$"
        "\n"
        r"(effects consider only the change in the relevant parameter)"
        "\n"
        rf"($C^*=741$ ADA/epoch; $R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
