#!/usr/bin/env python3
"""
Boxplot: theoretical member APR — rho=0.003 vs rho=0.0042 (epoch 644).

Uses the same pool snapshot and pool parameters; only rho changes.
APR_i = 73 (1-m_i) max{f - c_i, 0} / sigma_i

Writes:
  member_apr_rho_0p003_vs_0p0042_epoch_644.png
  member_apr_rho_0p003_vs_0p0042_epoch_644.csv
  member_apr_rho_0p003_vs_0p0042_epoch_644.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from rho_comparison_common import (
    FONT_SIZE,
    RHO_BASE,
    RHO_NEW,
    load_and_compute,
)

DIR = Path(__file__).resolve().parent
OUT_PLOT = DIR / "member_apr_rho_0p003_vs_0p0042_epoch_644.png"
OUT_CSV = DIR / "member_apr_rho_0p003_vs_0p0042_epoch_644.csv"
OUT_MD = DIR / "member_apr_rho_0p003_vs_0p0042_epoch_644.md"

EPOCHS_PER_YEAR = 73.0
COLOR_BASE = "#4c78a8"
COLOR_NEW = "#e76f51"
MEDIAN_COLOR = "#111111"


def member_apr(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def network_apr_pct(
    sigma: np.ndarray, apr: np.ndarray, eligible: np.ndarray
) -> float:
    if not eligible.any():
        return float("nan")
    sig = sigma[eligible]
    vals = apr[eligible]
    return 100.0 * float(np.average(vals, weights=sig))


def main() -> None:
    d = load_and_compute()
    df = d["df"]
    complete = d["complete"]

    sigma = d["sigma_a"]
    cost = d["cost_a"]
    margin = d["margin_a"]
    pledge_met = d["pledge_met"]

    f_base = d["f_base"]
    f_new = d["f_new"]

    apr_base = member_apr(sigma, f_base, cost, margin)
    apr_new = member_apr(sigma, f_new, cost, margin)

    elig_base = pledge_met & (f_base > cost)
    elig_new = pledge_met & (f_new > cost)

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].values,
            "ticker": df.loc[complete, "pool_name.ticker"].values,
            "sigma_ada": sigma,
            "fixed_cost_ada": cost,
            "margin": margin,
            "pledge_met": pledge_met,
            "f_ada_rho_0p003": f_base,
            "f_ada_rho_0p0042": f_new,
            "member_apr_rho_0p003": apr_base,
            "member_apr_rho_0p0042": apr_new,
            "f_gt_c_rho_0p003": elig_base,
            "f_gt_c_rho_0p0042": elig_new,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    base_vals = 100.0 * apr_base[elig_base]
    new_vals = 100.0 * apr_new[elig_new]
    net_base = network_apr_pct(sigma, apr_base, elig_base)
    net_new = network_apr_pct(sigma, apr_new, elig_new)

    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    labels = [
        rf"Current" "\n" rf"($\rho={RHO_BASE}$, $n={len(base_vals)}$)",
        rf"Higher $\rho$" "\n" rf"($\rho={RHO_NEW}$, $n={len(new_vals)}$)",
    ]
    bp = ax.boxplot(
        [base_vals, new_vals],
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        widths=0.55,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.2},
        whiskerprops={"color": "0.15", "linewidth": 1.1},
        capprops={"color": "0.15", "linewidth": 1.1},
        boxprops={"linewidth": 1.1},
    )
    for box, color in zip(bp["boxes"], (COLOR_BASE, COLOR_NEW)):
        box.set_facecolor(color)
        box.set_alpha(0.75)
        box.set_edgecolor("0.2")

    ymax = max(float(np.max(base_vals)), float(np.max(new_vals))) * 1.08
    ax.set_ylim(0.0, max(ymax, 3.0))
    med_base = float(np.median(base_vals))
    med_new = float(np.median(new_vals))
    for i, med in enumerate((med_base, med_new), start=1):
        # Each box has two caps; the upper cap is at index 2*(i-1)+1.
        upper_cap_y = float(bp["caps"][2 * (i - 1) + 1].get_ydata()[0])
        y_text = upper_cap_y + 0.04 * ax.get_ylim()[1]
        ax.text(
            i,
            y_text,
            f"Median: {med:.2f}%",
            ha="center",
            va="bottom",
            fontsize=FONT_SIZE,
            color=MEDIAN_COLOR,
        )
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    fig.suptitle(
        "Epoch 644 — theoretical member APR: rho comparison\n"
        r"(pledge-met pools with $f>c$; declared $c_i$; APR$=73(1-m)\max\{f-c,0\}/\sigma$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    md = f"""# Member APR — rho comparison (epoch 644)

Same epoch-644 pool snapshot and parameters; only $\\rho$ changes from {RHO_BASE} to {RHO_NEW}.

Pledge-met pools with $f>c$ only.

| Case | Pools ($f>c$) | Median APR | Mean APR | Network APR |
|:---|---:|---:|---:|---:|
| Current ($\\rho={RHO_BASE}$) | {len(base_vals)} | {np.median(base_vals):.2f}% | {np.mean(base_vals):.2f}% | {net_base:.2f}% |
| Higher $\\rho$ ($\\rho={RHO_NEW}$) | {len(new_vals)} | {np.median(new_vals):.2f}% | {np.mean(new_vals):.2f}% | {net_new:.2f}% |
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(f"Current rho={RHO_BASE}: n={len(base_vals)}, median={np.median(base_vals):.2f}%, network={net_base:.2f}%")
    print(f"Higher rho={RHO_NEW}: n={len(new_vals)}, median={np.median(new_vals):.2f}%, network={net_new:.2f}%")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
