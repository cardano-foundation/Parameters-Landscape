#!/usr/bin/env python3
"""
Box plots of simple member APR around the minPoolCost reduction (426→500).

Same cost-adjusted design as plot_member_apr_minpoolcost_426_vs_500_costadjusted.py:
  σ, p, m fixed at epoch 426; only declared cost c changes to epoch-500 values
  for survivors.

Plot 1 — three groups:
  epoch-426 costs, all baseline pools
  epoch-426 costs, survivors
  epoch-500 costs, survivors (cost-adjusted)

Plot 2 — fixed-cost reducers only (survivors with c_500 < c_426):
  before (epoch-426 cost)
  after  (epoch-500 cost, same σ,p,m)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV_426 = DIR / "staking_pools_full_epoch_426.csv"
CSV_500 = DIR / "staking_pools_full_epoch_500.csv"
OUT_COHORT = DIR / "member_apr_boxplot_cohort_426_500.png"
OUT_CUTTERS = DIR / "member_apr_boxplot_cost_reducers_426_500.png"

FONT_SIZE = 11
A0 = 0.3
K = 500
T_ADA = 36.01e9
R_ADA = 21.6e6
Z0_ADA = T_ADA / K
EPOCHS_PER_YEAR = 73.0

BOX_FACE = "#f4c4a8"
BOX_EDGE = "0.15"
MEDIAN_COLOR = "#e76f51"


def load_epoch(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
        errors="coerce",
    )
    return pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "sigma_ada": stake.fillna(0.0) / 1e6,
            "pledge_ada": pd.to_numeric(
                df["pool_update.active.pledge"], errors="coerce"
            )
            / 1e6,
            "margin": pd.to_numeric(
                df["pool_update.active.margin"], errors="coerce"
            ),
            "fixed_cost_ada": pd.to_numeric(
                df["pool_update.active.fixed_cost"], errors="coerce"
            )
            / 1e6,
        }
    ).set_index("pool_id")


def gross_pool_reward(sigma: np.ndarray, pledge: np.ndarray) -> np.ndarray:
    sigma = np.asarray(sigma, dtype=float)
    pledge = np.asarray(pledge, dtype=float)
    sigma_t = np.minimum(np.maximum(sigma, 0.0), Z0_ADA)
    pledge_t = np.minimum(np.minimum(np.maximum(pledge, 0.0), Z0_ADA), sigma_t)
    inner = sigma_t - pledge_t * (Z0_ADA - sigma_t) / Z0_ADA
    return (R_ADA / T_ADA) / (1.0 + A0) * (
        sigma_t + A0 * pledge_t * inner / Z0_ADA
    )


def member_apr(
    sigma: np.ndarray,
    pledge: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    f = gross_pool_reward(sigma, pledge)
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    rho = np.divide(pot, sigma, out=np.zeros_like(pot), where=sigma > 0)
    return EPOCHS_PER_YEAR * rho


def draw_boxes(
    ax: plt.Axes,
    groups: list[tuple[str, np.ndarray]],
    *,
    ylabel: str,
    title: str,
    suptitle: str | None = None,
) -> None:
    data = []
    labels = []
    for name, values in groups:
        vals = np.asarray(values, dtype=float)
        vals = vals[np.isfinite(vals)]
        data.append(vals)
        labels.append(f"{name}\n(n={len(vals)})")

    bp = ax.boxplot(
        data,
        tick_labels=labels,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        whiskerprops={"color": BOX_EDGE, "linewidth": 1.1},
        capprops={"color": BOX_EDGE, "linewidth": 1.1},
        boxprops={"color": BOX_EDGE, "linewidth": 1.1},
    )
    for box in bp["boxes"]:
        box.set_facecolor(BOX_FACE)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_ylim(bottom=0.0)
    ax.grid(axis="y", alpha=0.25)
    if suptitle:
        ax.figure.suptitle(suptitle, fontsize=FONT_SIZE + 1)


def main() -> None:
    e426 = load_epoch(CSV_426)
    e500 = load_epoch(CSV_500)

    baseline = e426[
        (e426["sigma_ada"] > 0)
        & e426["margin"].notna()
        & e426["fixed_cost_ada"].notna()
        & e426["pledge_ada"].notna()
    ].copy()

    survivors_ids = baseline.index.intersection(e500.index)
    cost_500 = e500.loc[survivors_ids, "fixed_cost_ada"]
    survivors_ids = survivors_ids[cost_500.notna().to_numpy()]
    survivors = baseline.loc[survivors_ids].copy()
    cost_500 = e500.loc[survivors_ids, "fixed_cost_ada"]

    apr_all_426 = member_apr(
        baseline["sigma_ada"].to_numpy(),
        baseline["pledge_ada"].to_numpy(),
        baseline["fixed_cost_ada"].to_numpy(),
        baseline["margin"].to_numpy(),
    )
    apr_surv_426 = member_apr(
        survivors["sigma_ada"].to_numpy(),
        survivors["pledge_ada"].to_numpy(),
        survivors["fixed_cost_ada"].to_numpy(),
        survivors["margin"].to_numpy(),
    )
    apr_surv_500 = member_apr(
        survivors["sigma_ada"].to_numpy(),
        survivors["pledge_ada"].to_numpy(),
        cost_500.to_numpy(),
        survivors["margin"].to_numpy(),
    )

    # Plot 1: positive APR only (overall median is 0 when zeros are included)
    fig1, ax1 = plt.subplots(figsize=(9.5, 5.0), constrained_layout=True)
    draw_boxes(
        ax1,
        [
            ("Epoch 426 costs\n(all pools)", 100.0 * apr_all_426[apr_all_426 > 0]),
            ("Epoch 426 costs\n(survivors)", 100.0 * apr_surv_426[apr_surv_426 > 0]),
            (
                "Epoch 500 costs\n(survivors, cost-adj.)",
                100.0 * apr_surv_500[apr_surv_500 > 0],
            ),
        ],
        ylabel="Member APR (%)",
        title="",
        suptitle=(
            "Member APR around minPoolCost reduction\n"
            rf"($k={K}$; $\sigma,p,m$ fixed at epoch 426)"
            "\n"
            r"Calculations based on positive APR pools "
            r"($f(\sigma_i,p_i)>c_i$)"
        ),
    )
    fig1.savefig(OUT_COHORT, dpi=200, bbox_inches="tight")
    plt.close(fig1)

    # Plot 2: cost reducers — include zeros (many cutters move off zero)
    cut = cost_500.to_numpy() < survivors["fixed_cost_ada"].to_numpy()
    apr_cut_before = apr_surv_426[cut]
    apr_cut_after = apr_surv_500[cut]
    n_cut = int(cut.sum())

    fig2, ax2 = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    draw_boxes(
        ax2,
        [
            ("Before\n(epoch-426 cost)", 100.0 * apr_cut_before),
            ("After\n(epoch-500 cost)", 100.0 * apr_cut_after),
        ],
        ylabel="Member APR (%)",
        title=f"Member APR among fixed-cost reducers (n={n_cut})",
        suptitle=(
            "Cost reducers only: isolated impact of declared-cost change\n"
            rf"($\sigma,p,m$ fixed at epoch 426; $c$ from 426 vs 500)"
        ),
    )
    fig2.savefig(OUT_CUTTERS, dpi=200, bbox_inches="tight")
    plt.close(fig2)

    print(f"Wrote {OUT_COHORT}")
    print(f"Wrote {OUT_CUTTERS}")
    print(
        f"baseline={len(baseline)} survivors={len(survivors)} "
        f"cutters={n_cut}"
    )
    print(
        "positive medians (%): "
        f"all={100*np.median(apr_all_426[apr_all_426>0]):.2f}, "
        f"surv426={100*np.median(apr_surv_426[apr_surv_426>0]):.2f}, "
        f"surv500={100*np.median(apr_surv_500[apr_surv_500>0]):.2f}"
    )
    print(
        "cutters median APR % (incl. zeros): "
        f"before={100*np.median(apr_cut_before):.2f}, "
        f"after={100*np.median(apr_cut_after):.2f}; "
        f"pos before={(apr_cut_before>0).sum()}, "
        f"pos after={(apr_cut_after>0).sum()}"
    )


if __name__ == "__main__":
    main()
