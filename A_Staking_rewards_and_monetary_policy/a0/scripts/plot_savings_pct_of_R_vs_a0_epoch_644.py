#!/usr/bin/env python3
"""
Share of R impacted by a change in a0 (epoch 644).

Active pools only (not σ=0, not unmet pledge, not zero blocks in
epochs 630–644). Merged snapshot (unique-owner live pledge).

Recomputes per-pool and aggregate f(σ,p; a0), then writes:
  - pools_f_vs_a0_epoch_644.csv
  - aggregate_f_vs_a0_epoch_644.csv
  - aggregate_f_vs_a0_continuous_epoch_644.csv
  - savings_pct_of_R_vs_a0_epoch_644.csv
  - savings_pct_of_R_vs_a0_epoch_644.png
  - sum_f_vs_a0_epoch_644.png

Definition (relative to baseline a0=0.3):
  savings % of R = 100 * (sum_f(0.3) - sum_f(a0)) / R

Usage:
  python3 plot_savings_pct_of_R_vs_a0_epoch_644.py
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
OUT_POOLS = DIR / "pools_f_vs_a0_epoch_644.csv"
OUT_DISCRETE = DIR / "aggregate_f_vs_a0_epoch_644.csv"
OUT_CONT = DIR / "aggregate_f_vs_a0_continuous_epoch_644.csv"
OUT_CSV = DIR / "savings_pct_of_R_vs_a0_epoch_644.csv"
OUT_PLOT = DIR / "savings_pct_of_R_vs_a0_epoch_644.png"
OUT_SUM = DIR / "sum_f_vs_a0_epoch_644.png"

A0_BASE = 0.3
A0_GRID = np.round(np.arange(0.100, 0.601, 0.001), 6)
DISCRETE = [
    ("a0_0.1", 0.1, "0.1"),
    ("a0_0.3", 0.3, "0.3"),
    ("a0_0.3_plus_1pct", 0.3 * 1.01, "+1%"),
    ("a0_0.3_plus_10pct", 0.3 * 1.10, "+10%"),
    ("a0_0.3_plus_25pct", 0.3 * 1.25, "+25%"),
    ("a0_0.3_plus_50pct", 0.3 * 1.50, "+50%"),
    ("a0_0.3_plus_75pct", 0.3 * 1.75, "+75%"),
    ("a0_0.3_plus_100pct", 0.3 * 2.00, "+100%"),
]
DISCRETE_MARKERS = [
    (0.1, "0.1"),
    (0.3, "0.3"),
    (0.3 * 1.10, "+10%"),
    (0.3 * 1.25, "+25%"),
    (0.3 * 1.50, "+50%"),
    (0.3 * 1.75, "+75%"),
    (0.3 * 2.00, "+100%"),
]


def pool_fields(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sigma = (
        pd.to_numeric(
            df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
            errors="coerce",
        )
        / 1e6
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    complete = sigma.notna() & declared.notna() & active.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    ids = df.loc[complete, "pool_id"].to_numpy()
    tickers = df.loc[complete, "pool_name.ticker"].to_numpy()
    names = df.loc[complete, "pool_name.name"].to_numpy() if "pool_name.name" in df else np.array([""] * len(ids))
    return (
        sigma_a,
        declared_a,
        active_a,
        ids,
        tickers,
        names,
        complete,
    )


def f_for_a0(
    sigma: np.ndarray,
    declared: np.ndarray,
    active: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    met = (active >= declared) & (sigma > 0)
    raw = gross_pool_reward(sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0)
    return np.where(met, np.maximum(raw, 0.0), 0.0)


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    k = int(params["k"])
    z0 = float(params["z0_ada"])
    r_over_t = R / T

    df = load_active_pools()
    sigma, declared, active, ids, tickers, names, _ = pool_fields(df)

    # Per-pool discrete a0
    discrete_f: dict[str, np.ndarray] = {}
    for label, a0, _ in DISCRETE:
        discrete_f[label] = f_for_a0(
            sigma, declared, active, z0=z0, r_over_t=r_over_t, a0=a0
        )

    pools = pd.DataFrame(
        {
            "pool_id": ids,
            "pool_name.ticker": tickers,
            "pool_name.name": names,
            "sigma_ada": sigma,
            "pledge_ada": declared,
            "sigma_over_T": sigma / T,
            "pledge_over_T": declared / T,
            "R_ada": R,
            "T_ada": T,
            "z0_ada": z0,
            "k": k,
            "f_a0_0.1": discrete_f["a0_0.1"],
            "f_a0_0.3": discrete_f["a0_0.3"],
            "f_a0_0.3_plus_1pct": discrete_f["a0_0.3_plus_1pct"],
            "f_a0_0.3_plus_10pct": discrete_f["a0_0.3_plus_10pct"],
            "f_a0_0.3_plus_25pct": discrete_f["a0_0.3_plus_25pct"],
            "f_a0_0.3_plus_50pct": discrete_f["a0_0.3_plus_50pct"],
            "f_a0_0.3_plus_75pct": discrete_f["a0_0.3_plus_75pct"],
            "f_a0_0.3_plus_100pct": discrete_f["a0_0.3_plus_100pct"],
        }
    )
    pools.to_csv(OUT_POOLS, index=False)

    sum_base = float(discrete_f["a0_0.3"].sum())
    n = len(sigma)
    disc_rows = []
    for label, a0, _ in DISCRETE:
        s = float(discrete_f[label].sum())
        disc_rows.append(
            {
                "label": label,
                "a0": a0,
                "sum_f_ada": s,
                "mean_f_ada": s / n if n else float("nan"),
                "pct_vs_a0_0.3": 100.0 * (s - sum_base) / sum_base if sum_base else float("nan"),
            }
        )
    pd.DataFrame(disc_rows).to_csv(OUT_DISCRETE, index=False)

    sums = np.array(
        [
            float(
                f_for_a0(
                    sigma, declared, active, z0=z0, r_over_t=r_over_t, a0=float(a0)
                ).sum()
            )
            for a0 in A0_GRID
        ]
    )
    pd.DataFrame({"a0": A0_GRID, "sum_f_ada": sums}).to_csv(OUT_CONT, index=False)

    idx0 = int(np.argmin(np.abs(A0_GRID - A0_BASE)))
    sum_base_c = float(sums[idx0])
    savings_pct = 100.0 * (sum_base_c - sums) / R
    unalloc_pct = 100.0 * (R - sums) / R
    pd.DataFrame(
        {
            "a0": A0_GRID,
            "sum_f_ada": sums,
            "sum_f_baseline_a0_0.3": sum_base_c,
            "savings_vs_baseline_ada": sum_base_c - sums,
            "savings_vs_baseline_pct_of_R": savings_pct,
            "unallocated_pct_of_R": unalloc_pct,
        }
    ).to_csv(OUT_CSV, index=False)

    # Savings plot
    fig, ax = plt.subplots(1, 1, figsize=(9, 5.2), constrained_layout=True)
    ax.plot(A0_GRID, savings_pct, color="C0", linewidth=2.2)
    ax.axhline(0.0, color="0.4", linestyle="--", linewidth=1.0)
    ax.axvline(0.3, color="0.45", linestyle=":", linewidth=1.3)

    ymin, ymax = float(np.min(savings_pct)), float(np.max(savings_pct))
    pad = 0.12 * (ymax - ymin) if ymax > ymin else 1.0
    ax.set_ylim(ymin - pad, ymax + 1.15 * pad)
    ax.set_xlim(0.00, 0.64)
    xmin, xmax = ax.get_xlim()
    y0, y1 = ax.get_ylim()

    ax.text(
        0.285,
        -0.45 * abs(ymin) if ymin else 0.0,
        "Current value",
        rotation=90,
        va="center",
        ha="right",
        fontsize=10,
        color="0.35",
    )

    def y_lab(y_pct: float, a0_lab: str) -> str:
        if a0_lab == "0.3":
            return "baseline"
        return f"{y_pct:+.1f}% R"

    y_nudge = {"0.3": -0.35, "+10%": 0.35}

    for a0, lab in DISCRETE_MARKERS:
        i = int(np.argmin(np.abs(A0_GRID - a0)))
        x, y = float(A0_GRID[i]), float(savings_pct[i])
        ax.scatter([x], [y], zorder=4, s=50, color="C1")
        ax.plot([xmin, x], [y, y], color="0.55", linestyle="--", linewidth=0.9, zorder=1)
        ax.text(
            xmin + 0.01,
            y + y_nudge.get(lab, 0.0),
            y_lab(y, lab),
            ha="left",
            va="center",
            fontsize=9,
            color="0.2",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
            zorder=5,
        )
        ax.plot([x, x], [y0, y], color="0.55", linestyle="--", linewidth=0.9, zorder=1)
        ax.text(
            x,
            y0 + 0.035 * (y1 - y0),
            lab,
            ha="center",
            va="bottom",
            fontsize=9,
            color="0.2",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.9),
            zorder=5,
        )

    ax.set_xlabel(r"$a_0$", fontsize=12)
    ax.set_ylabel(r"Savings as % of $R$", fontsize=12)
    ax.set_title(
        r"Share of $R$ impacted by a change in $a_0$"
        "\n"
        rf"(epoch 644, Active pools, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.1f}$B ADA, $k={k}$)",
        fontsize=12,
    )
    ax.grid(alpha=0.25)
    fig.savefig(OUT_PLOT, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # Sum f vs a0
    fig2, ax2 = plt.subplots(1, 1, figsize=(9, 5.2), constrained_layout=True)
    ax2.plot(A0_GRID, sums / 1e6, color="C0", linewidth=2.2)
    ax2.axvline(0.3, color="0.45", linestyle=":", linewidth=1.3)
    for a0, lab in DISCRETE_MARKERS:
        i = int(np.argmin(np.abs(A0_GRID - a0)))
        ax2.scatter([A0_GRID[i]], [sums[i] / 1e6], zorder=4, s=50, color="C1")
    ax2.set_xlabel(r"$a_0$", fontsize=12)
    ax2.set_ylabel(r"$\sum_i f_i$ (M ADA)", fontsize=12)
    ax2.set_title(
        r"Aggregate gross pool reward vs $a_0$"
        "\n"
        rf"(epoch 644, Active pools, $n={n}$)",
        fontsize=12,
    )
    ax2.grid(alpha=0.25)
    fig2.savefig(OUT_SUM, dpi=300, bbox_inches="tight")
    plt.close(fig2)

    print(f"Active pools in f-sum: {n}")
    print(f"R = {R:,.3f} ADA; baseline sum_f(a0=0.3) = {sum_base_c:,.3f} ADA")
    print(f"Wrote {OUT_POOLS}")
    print(f"Wrote {OUT_DISCRETE}")
    print(f"Wrote {OUT_CONT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_SUM}")


if __name__ == "__main__":
    main()
