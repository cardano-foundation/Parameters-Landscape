#!/usr/bin/env python3
"""
Plot: share of R impacted by a change in a0 (epoch 644).

Reads the continuous aggregate curve produced earlier and writes:
  - savings_pct_of_R_vs_a0_epoch_644.png
  - savings_pct_of_R_vs_a0_epoch_644.csv

Definition (relative to baseline a0=0.3):
  savings % of R = 100 * (sum_f(0.3) - sum_f(a0)) / R

Usage:
  python3 plot_savings_pct_of_R_vs_a0_epoch_644.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DIR = Path(__file__).resolve().parent
CONT = DIR / "aggregate_f_vs_a0_continuous_epoch_644.csv"
PARAMS = DIR / "f_reward_params_epoch_644.json"
OUT_PLOT = DIR / "savings_pct_of_R_vs_a0_epoch_644.png"
OUT_CSV = DIR / "savings_pct_of_R_vs_a0_epoch_644.csv"

# Display / accounting constants for epoch 644 (fees ignored)
R = 14_966_501.840557  # ADA; R = (1-tau)*rho*reserves

# Discrete markers (exclude +1%)
DISCRETE = [
    (0.1, "0.1"),
    (0.3, "0.3"),
    (0.3 * 1.10, "+10%"),
    (0.3 * 1.25, "+25%"),
    (0.3 * 1.50, "+50%"),
    (0.3 * 1.75, "+75%"),
    (0.3 * 2.00, "+100%"),
]


def load_continuous() -> tuple[np.ndarray, np.ndarray]:
    if not CONT.exists():
        raise FileNotFoundError(
            f"Missing {CONT.name}. Generate it first (pools_f_vs_a0 / continuous aggregate)."
        )
    a0s: list[float] = []
    sums: list[float] = []
    with CONT.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            a0s.append(float(row["a0"]))
            sums.append(float(row["sum_f_ada"]))
    return np.asarray(a0s), np.asarray(sums)


def main() -> None:
    a0s, sums = load_continuous()
    idx0 = int(np.argmin(np.abs(a0s - 0.3)))
    sum_base = float(sums[idx0])
    savings_pct = 100.0 * (sum_base - sums) / R
    unalloc_pct = 100.0 * (R - sums) / R

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "a0",
                "sum_f_ada",
                "sum_f_baseline_a0_0.3",
                "savings_vs_baseline_ada",
                "savings_vs_baseline_pct_of_R",
                "unallocated_pct_of_R",
            ],
        )
        w.writeheader()
        for a0, s, sp, up in zip(a0s, sums, savings_pct, unalloc_pct):
            w.writerow(
                {
                    "a0": f"{a0:.6f}",
                    "sum_f_ada": f"{s:.10f}",
                    "sum_f_baseline_a0_0.3": f"{sum_base:.10f}",
                    "savings_vs_baseline_ada": f"{(sum_base - s):.10f}",
                    "savings_vs_baseline_pct_of_R": f"{sp:.8f}",
                    "unallocated_pct_of_R": f"{up:.8f}",
                }
            )

    fig, ax = plt.subplots(1, 1, figsize=(9, 5.2), constrained_layout=True)
    ax.plot(a0s, savings_pct, color="C0", linewidth=2.2)
    ax.axhline(0.0, color="0.4", linestyle="--", linewidth=1.0)
    ax.axvline(0.3, color="0.45", linestyle=":", linewidth=1.3)

    ymin, ymax = float(np.min(savings_pct)), float(np.max(savings_pct))
    pad = 0.12 * (ymax - ymin)
    ax.set_ylim(ymin - pad, ymax + 1.15 * pad)
    # Extra left margin so y-axis savings labels do not sit on the a0=0.1 point
    ax.set_xlim(0.00, 0.64)
    xmin, xmax = ax.get_xlim()
    y0, y1 = ax.get_ylim()

    ax.text(
        0.285,
        -0.45 * abs(ymin),
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

    # Small vertical nudges for nearby y-labels (baseline vs +10%)
    y_nudge = {
        "0.3": -0.35,
        "+10%": 0.35,
    }

    for a0, lab in DISCRETE:
        i = int(np.argmin(np.abs(a0s - a0)))
        x, y = float(a0s[i]), float(savings_pct[i])
        ax.scatter([x], [y], zorder=4, s=50, color="C1")

        # horizontal guide to y-axis + savings label
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

        # vertical guide to x-axis + a0-change label
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
        r"(epoch 644, $R=14.97$M ADA, $T=38.8$B ADA, $k=500$, fees ignored)",
        fontsize=12,
    )
    ax.grid(alpha=0.25)

    fig.savefig(OUT_PLOT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUT_PLOT)
    print("Saved:", OUT_CSV)
    if PARAMS.exists():
        print(f"(R used = {R:,.3f} ADA; baseline sum_f(a0=0.3) = {sum_base:,.3f} ADA)")


if __name__ == "__main__":
    main()
