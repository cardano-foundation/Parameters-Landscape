#!/usr/bin/env python3
"""
Delegation gain/loss/exit among Active pools unsaturated under k=500 at
epoch 228, by epoch-228 stake bins (M ADA).

Active = not (σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs).
Exited = Active-unsaturated at 228 but not Active at 285.
Continuing pools: gain / lose / flat stake vs 285.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "unsaturated_delegation_by_stake_bin_228_285.png"
OUT_CSV = DIR / "unsaturated_delegation_by_stake_bin_228_285.csv"
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
COLOR_EXIT = "#7c3aed"
T_228_ADA = 32.03687470708404e9

BINS = [
    (0.0, 5.0, "0–5"),
    (5.0, 10.0, "5–10"),
    (10.0, 15.0, "10–15"),
    (15.0, 30.0, "15–30"),
    (30.0, 45.0, "30–45"),
    (45.0, 60.0, "45–60"),
    (60.0, np.inf, ">60"),
]


def load_epoch(epoch: int) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}.csv")
    flags = pd.read_csv(DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv")
    stake_lov = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    )
    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "stake_ada": stake_lov.fillna(0.0) / 1e6,
        }
    )
    out = out.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    out["active"] = out["in_union"] == 0
    return out.set_index("pool_id")


def main() -> None:
    z0 = T_228_ADA / K_POST
    a = load_epoch(E0)
    b = load_epoch(E1)
    active_285 = b.index[b["active"]]

    unsat_all = a[(a["stake_ada"] > 0) & (a["stake_ada"] <= z0)]
    unsat = unsat_all.index[unsat_all["active"]]
    inactive = unsat_all.index[~unsat_all["active"]]
    continuing = unsat.intersection(active_285)
    exited = unsat.difference(active_285)
    ina_cont = inactive.intersection(b.index)
    ina_exit = inactive.difference(b.index)

    sa_c = a.loc[continuing, "stake_ada"]
    sb_c = b.loc[continuing, "stake_ada"]
    d_c = sb_c - sa_c
    sa_x = a.loc[exited, "stake_ada"]
    d_ina = b.loc[ina_cont, "stake_ada"] - a.loc[ina_cont, "stake_ada"]

    stake_m_c = sa_c / 1e6
    stake_m_x = sa_x / 1e6
    labels = ["Inactive"] + [lab for _, _, lab in BINS]
    rows = []
    gain_vals, lose_vals, flat_vals, exit_vals, ns = [], [], [], [], []

    g_i = int((d_ina > 0).sum()) if len(ina_cont) else 0
    l_i = int((d_ina < 0).sum()) if len(ina_cont) else 0
    f_i = int((d_ina == 0).sum()) if len(ina_cont) else 0
    x_i = int(len(ina_exit))
    n_i = g_i + l_i + f_i + x_i
    gain_vals.append(g_i)
    lose_vals.append(l_i)
    flat_vals.append(f_i)
    exit_vals.append(x_i)
    ns.append(n_i)
    rows.append(
        {
            "stake_bin_M_ADA": "Inactive",
            "n_pools": n_i,
            "n_continuing": int(len(ina_cont)),
            "gain_delegation": g_i,
            "lose_delegation": l_i,
            "flat_delegation": f_i,
            "exited": x_i,
            "median_dstake_continuing_ADA": (
                float(d_ina.median()) if len(ina_cont) else float("nan")
            ),
        }
    )

    for lo, hi, lab in BINS:
        mask_c = (stake_m_c >= lo) & (stake_m_c < hi)
        mask_x = (stake_m_x >= lo) & (stake_m_x < hi)
        g = int((d_c[mask_c] > 0).sum())
        l = int((d_c[mask_c] < 0).sum())
        f = int((d_c[mask_c] == 0).sum())
        x = int(mask_x.sum())
        n = g + l + f + x
        gain_vals.append(g)
        lose_vals.append(l)
        flat_vals.append(f)
        exit_vals.append(x)
        ns.append(n)
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": n,
                "n_continuing": int(mask_c.sum()),
                "gain_delegation": g,
                "lose_delegation": l,
                "flat_delegation": f,
                "exited": x,
                "median_dstake_continuing_ADA": (
                    float(d_c[mask_c].median()) if mask_c.any() else float("nan")
                ),
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    x = np.arange(len(labels))
    width = 0.2
    fig, ax = plt.subplots(figsize=(12.4, 5.4), constrained_layout=True)
    offs = (-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width)
    series = [
        (offs[0], gain_vals, COLOR_GAIN, "gain stake"),
        (offs[1], lose_vals, COLOR_LOSE, "lose stake"),
        (offs[2], flat_vals, COLOR_FLAT, "flat stake"),
        (offs[3], exit_vals, COLOR_EXIT, "exited by 285"),
    ]
    bar_artists = []
    for off, vals, col, lab in series:
        bar_artists.append(ax.bar(x + off, vals, width, color=col, label=lab))

    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE)
    ax.set_xlabel(
        "Epoch-228 stake bin (M ADA); leftmost = Inactive at 228",
        fontsize=FONT_SIZE,
    )
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(
        f"Delegation outcomes 228→285 among unsaturated pools under $k={K_POST}$ at epoch 228\n"
        f"(Active n={len(unsat)}: {len(continuing)} continuing, {len(exited)} exited; "
        f"Inactive n={len(inactive)}; $z_0={z0/1e6:.1f}$ M ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(gain_vals + lose_vals + flat_vals + exit_vals + [1])
    for bars in bar_artists:
        for bar in bars:
            v = int(bar.get_height())
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    v + ymax * 0.02,
                    str(v),
                    ha="center",
                    fontsize=FONT_SIZE - 3,
                )

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    print(
        {
            "z0_M": z0 / 1e6,
            "n_unsat": len(unsat),
            "n_continuing": len(continuing),
            "n_exited": len(exited),
            "rows": rows,
        }
    )


if __name__ == "__main__":
    main()
