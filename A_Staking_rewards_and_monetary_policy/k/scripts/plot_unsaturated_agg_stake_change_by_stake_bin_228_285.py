#!/usr/bin/env python3
"""
Aggregate stake change (228→285) among Active pools unsaturated under k=500
at epoch 228, by epoch-228 stake bins.

Active = not (σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs).
Exited = Active-unsaturated at 228 but not Active at 285: their full
epoch-228 stake is counted as a loss (Δσ = −σ_228) in the red bar.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
OUT = DIR / "unsaturated_agg_stake_change_by_stake_bin_228_285.png"
OUT_CSV = DIR / "unsaturated_agg_stake_change_by_stake_bin_228_285.csv"
E0, E1 = 228, 285
K_POST = 500
FONT_SIZE = 12
COLOR_GAIN = "#2f6f4e"
COLOR_LOSE = "#b23a3a"
COLOR_FLAT = "#6b7280"
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
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}_merged.csv")
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


def fmt_m(x: float) -> str:
    if abs(x) < 1e-9:
        return "0"
    return f"{x / 1e6:+.1f}"


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
    d_x = -sa_x  # full stake lost upon exit
    d_ina = b.loc[ina_cont, "stake_ada"] - a.loc[ina_cont, "stake_ada"]
    d_ina_x = -a.loc[ina_exit, "stake_ada"]

    stake_m_c = sa_c / 1e6
    stake_m_x = sa_x / 1e6
    labels = ["Inactive"] + [lab for _, _, lab in BINS]
    rows = []
    gain_agg, lose_agg, flat_agg, ns = [], [], [], []

    g_mask_i = d_ina > 0
    l_mask_i = d_ina < 0
    f_mask_i = d_ina == 0
    g_sum_i = float(d_ina[g_mask_i].sum()) if g_mask_i.any() else 0.0
    l_cont_i = float(d_ina[l_mask_i].sum()) if l_mask_i.any() else 0.0
    x_sum_i = float(d_ina_x.sum()) if len(ina_exit) else 0.0
    l_sum_i = l_cont_i + x_sum_i
    f_sum_i = float(d_ina[f_mask_i].sum()) if f_mask_i.any() else 0.0
    n_i = int(len(inactive))
    gain_agg.append(g_sum_i)
    lose_agg.append(l_sum_i)
    flat_agg.append(f_sum_i)
    ns.append(n_i)
    rows.append(
        {
            "stake_bin_M_ADA": "Inactive",
            "n_pools": n_i,
            "n_continuing": int(len(ina_cont)),
            "n_exited": int(len(ina_exit)),
            "n_gain": int(g_mask_i.sum()),
            "n_lose_continuing": int(l_mask_i.sum()),
            "n_flat": int(f_mask_i.sum()),
            "agg_dstake_gain_ADA": g_sum_i,
            "agg_dstake_lose_continuing_ADA": l_cont_i,
            "agg_dstake_exit_ADA": x_sum_i,
            "agg_dstake_lose_or_exit_ADA": l_sum_i,
            "agg_dstake_flat_ADA": f_sum_i,
            "agg_dstake_net_ADA": g_sum_i + l_sum_i + f_sum_i,
        }
    )

    for lo, hi, lab in BINS:
        mask_c = (stake_m_c >= lo) & (stake_m_c < hi)
        mask_x = (stake_m_x >= lo) & (stake_m_x < hi)
        g_mask = mask_c & (d_c > 0)
        l_mask = mask_c & (d_c < 0)
        f_mask = mask_c & (d_c == 0)
        g_sum = float(d_c[g_mask].sum()) if g_mask.any() else 0.0
        l_cont = float(d_c[l_mask].sum()) if l_mask.any() else 0.0
        x_sum = float(d_x[mask_x].sum()) if mask_x.any() else 0.0
        l_sum = l_cont + x_sum  # continuing losers + exited
        f_sum = float(d_c[f_mask].sum()) if f_mask.any() else 0.0
        n = int(mask_c.sum() + mask_x.sum())
        gain_agg.append(g_sum)
        lose_agg.append(l_sum)
        flat_agg.append(f_sum)
        ns.append(n)
        rows.append(
            {
                "stake_bin_M_ADA": lab,
                "n_pools": n,
                "n_continuing": int(mask_c.sum()),
                "n_exited": int(mask_x.sum()),
                "n_gain": int(g_mask.sum()),
                "n_lose_continuing": int(l_mask.sum()),
                "n_flat": int(f_mask.sum()),
                "agg_dstake_gain_ADA": g_sum,
                "agg_dstake_lose_continuing_ADA": l_cont,
                "agg_dstake_exit_ADA": x_sum,
                "agg_dstake_lose_or_exit_ADA": l_sum,
                "agg_dstake_flat_ADA": f_sum,
                "agg_dstake_net_ADA": g_sum + l_sum + f_sum,
            }
        )

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    gain_m = [v / 1e6 for v in gain_agg]
    lose_m = [v / 1e6 for v in lose_agg]
    flat_m = [v / 1e6 for v in flat_agg]

    x = np.arange(len(labels))
    width = 0.26
    fig, ax = plt.subplots(figsize=(12.2, 5.6), constrained_layout=True)
    b1 = ax.bar(x - width, gain_m, width, color=COLOR_GAIN, label="gainers (Σ Δσ)")
    b2 = ax.bar(
        x,
        lose_m,
        width,
        color=COLOR_LOSE,
        label="lose / exit (Σ Δσ; includes exited)",
    )
    b3 = ax.bar(x + width, flat_m, width, color=COLOR_FLAT, label="flat (Σ Δσ)")
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, ns)], fontsize=FONT_SIZE)
    ax.set_xlabel(
        "Epoch-228 stake bin (M ADA); leftmost = Inactive at 228",
        fontsize=FONT_SIZE,
    )
    ax.set_ylabel("Aggregate stake change (M ADA)", fontsize=FONT_SIZE)
    ax.set_title(
        f"Aggregate Δstake 228→285 among unsaturated pools under $k={K_POST}$ at epoch 228\n"
        f"(Active n={len(unsat)}: {len(continuing)} continuing, {len(exited)} exited; "
        f"Inactive n={len(inactive)}; $z_0={z0/1e6:.1f}$ M ADA)",
        fontsize=FONT_SIZE,
    )
    ax.tick_params(labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE - 1, frameon=False, loc="best")
    ax.grid(axis="y", alpha=0.25)

    all_m = gain_m + lose_m + flat_m
    span = max(abs(v) for v in all_m) if all_m else 1.0
    y_lo = min(all_m) - span * 0.06
    y_hi = max(all_m) + span * 0.10
    ax.set_ylim(y_lo, y_hi)

    pad = span * 0.025
    for bars, vals_ada in ((b1, gain_agg), (b2, lose_agg), (b3, flat_agg)):
        for bar, v_ada in zip(bars, vals_ada):
            if abs(v_ada) < 1.0 and abs(bar.get_height()) < 1e-9:
                continue
            h = bar.get_height()
            xc = bar.get_x() + bar.get_width() / 2
            if h >= 0:
                ax.text(
                    xc,
                    h + pad,
                    fmt_m(v_ada),
                    ha="center",
                    va="bottom",
                    fontsize=FONT_SIZE - 2,
                    color="0.15",
                )
            else:
                ax.text(
                    bar.get_x() + bar.get_width() + 0.03,
                    h,
                    fmt_m(v_ada),
                    ha="left",
                    va="center",
                    fontsize=FONT_SIZE - 2,
                    color=COLOR_LOSE,
                )

    fig.savefig(OUT, dpi=300)
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_CSV}")
    print({"n_unsat": len(unsat), "n_continuing": len(continuing), "n_exited": len(exited)})
    for r in rows:
        print(
            f"  {r['stake_bin_M_ADA']}: gain={r['agg_dstake_gain_ADA']/1e6:+.1f}M "
            f"lose+exit={r['agg_dstake_lose_or_exit_ADA']/1e6:+.1f}M "
            f"(cont={r['agg_dstake_lose_continuing_ADA']/1e6:+.1f}, "
            f"exit={r['agg_dstake_exit_ADA']/1e6:+.1f}) "
            f"net={r['agg_dstake_net_ADA']/1e6:+.1f}M"
        )


if __name__ == "__main__":
    main()
