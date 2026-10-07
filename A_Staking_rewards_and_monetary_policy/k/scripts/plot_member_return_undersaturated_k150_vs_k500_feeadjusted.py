#!/usr/bin/env python3
"""
Compare member APR before and after the increase from k=150 to k=500,
restricting the epoch-228 cohort to pools below the new saturation cap.

Selection:
    sigma_228 <= z0(k=500) = 64.07M ADA

Exiting pools are retained in the k=150 baseline and identified separately.
The fee-adjusted k=500 calculation is available only for pools observed at
epoch 285 because it uses their epoch-285 fixed cost and margin.

Writes:
    member_return_undersaturated_k150_vs_k500_feeadjusted.csv
    member_return_undersaturated_k150_vs_k500_feeadjusted.png
    member_return_undersaturated_k150_vs_k500_feeadjusted.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
INPUT_CSV = DIR / "member_return_k150_vs_k500_feeadjusted_epoch_228.csv"
OUT_CSV = DIR / "member_return_undersaturated_k150_vs_k500_feeadjusted.csv"
OUT_PLOT = DIR / "member_return_undersaturated_k150_vs_k500_feeadjusted.png"
OUT_MD = DIR / "member_return_undersaturated_k150_vs_k500_feeadjusted.md"

Z0_K500 = 64.07e6
FONT_SIZE = 12
COLOR_SURVIVOR = "#2a9d8f"
COLOR_EXIT = "#b23a3a"
COLOR_ZERO = "#6b7280"


def summary(apr: pd.Series) -> tuple[int, int, float, float]:
    observed = apr.dropna().clip(lower=0.0)
    positive = observed[observed > 0]
    return (
        len(observed),
        len(positive),
        100 * observed.median(),
        100 * observed.mean(),
    )


def plot_points(
    ax: plt.Axes,
    frame: pd.DataFrame,
    apr_column: str,
    color: str,
    label: str,
    marker: str = "o",
) -> None:
    observed = frame.dropna(subset=[apr_column])
    positive = observed[observed[apr_column] > 0]
    zero = observed[observed[apr_column] <= 0]
    ax.scatter(
        positive["sigma_ada_228"] / 1e6,
        100 * positive[apr_column],
        s=16,
        alpha=0.4,
        color=color,
        marker=marker,
        edgecolors=None if marker == "x" else "none",
        label=f"{label}, return > 0 (n={len(positive)})",
    )
    if len(zero):
        ax.scatter(
            zero["sigma_ada_228"] / 1e6,
            np.full(len(zero), 0.055),
            s=13,
            alpha=0.3,
            color=COLOR_ZERO if marker == "o" else color,
            marker=marker,
            edgecolors=None if marker == "x" else "none",
            label=f"{label}, return = 0 (n={len(zero)})",
        )


def main() -> None:
    all_pools = pd.read_csv(INPUT_CSV)
    cohort = all_pools.loc[all_pools["sigma_ada_228"] <= Z0_K500].copy()
    cohort["cohort_status"] = np.where(
        cohort["survives_to_285"], "Survives to epoch 285", "Exited by epoch 285"
    )
    cohort.to_csv(OUT_CSV, index=False)

    survivors = cohort.loc[cohort["survives_to_285"]].copy()
    exits = cohort.loc[~cohort["survives_to_285"]].copy()
    apr_150 = "member_apr_simple_k150"
    apr_500 = "member_apr_simple_k500_feeadjusted"

    rows = [
        ("$k=150$: all undersaturated pools", *summary(cohort[apr_150])),
        ("$k=150$: survivors", *summary(survivors[apr_150])),
        (
            "$k=500$: survivors, fees adjusted",
            *summary(survivors[apr_500]),
        ),
        ("$k=150$: pools exiting by epoch 285", *summary(exits[apr_150])),
    ]

    paired = survivors[[apr_150, apr_500]].dropna()
    delta_pp = 100 * (paired[apr_500] - paired[apr_150])
    both_positive = paired.loc[(paired[apr_150] > 0) & (paired[apr_500] > 0)]
    positive_delta_pp = 100 * (
        both_positive[apr_500] - both_positive[apr_150]
    )

    table_lines = [
        "| Sample and scenario | Pools | Return $>0$ | Median APR | Mean APR |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for label, count, positive_count, median_apr, mean_apr in rows:
        table_lines.append(
            f"| {label} | {count} | {positive_count} | "
            f"{median_apr:.2f}% | {mean_apr:.2f}% |"
        )

    description = (
        f"The sample is restricted to the {len(cohort):,} Active pools whose epoch-228 "
        f"stake was no greater than the new $k=500$ saturation cap "
        f"($\\sigma_{{228}}\\le z_0=64.07$M ADA). This removes the mechanical "
        f"return penalty caused by oversaturation. Of these pools, "
        f"{len(survivors):,} remained active at epoch 285 and {len(exits):,} "
        f"exited. Exiting pools are retained in the $k=150$ baseline, but no "
        f"fee-adjusted $k=500$ return is assigned to them because their epoch-285 "
        f"fees are unobserved. Among surviving pools, median APR (including "
        f"$f\\le c$, where APR $=0$) changes from "
        f"{100*survivors[apr_150].clip(lower=0).median():.2f}% "
        f"under $k=150$ to "
        f"{100*survivors[apr_500].clip(lower=0).median():.2f}% "
        f"under the fee-adjusted $k=500$ counterfactual. The paired median change "
        f"across all {len(paired):,} survivors is {delta_pp.median():+.3f} "
        f"percentage points; among the {len(both_positive):,} pools with positive "
        f"returns in both scenarios, it is {positive_delta_pp.median():+.3f} "
        f"percentage points. Thus, once pools exposed to oversaturation are "
        f"excluded, there is no economically meaningful decline in member APR. "
        f"The decline in the unrestricted comparison is therefore principally "
        f"associated with pools above the lower saturation threshold, rather "
        f"than with fee changes among pools that remain undersaturated."
    )

    OUT_MD.write_text(
        "# Member APR among Active pools undersaturated under $k=500$\n\n"
        + "\n".join(table_lines)
        + "\n\n"
        + description
        + "\n",
        encoding="utf-8",
    )

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), constrained_layout=True)
    plot_points(
        axes[0], survivors, apr_150, COLOR_SURVIVOR, "Survivors"
    )
    plot_points(
        axes[0], exits, apr_150, COLOR_EXIT, "Exits", marker="x"
    )
    plot_points(
        axes[1],
        survivors,
        apr_500,
        COLOR_SURVIVOR,
        "Survivors",
    )

    axes[0].set_title(
        "$k=150$ with epoch-228 fees\n"
        f"all Active undersaturated pools (n={len(cohort)}; exits included)",
        fontsize=FONT_SIZE,
    )
    axes[1].set_title(
        "$k=500$ with epoch-285 fees\n"
        f"Active undersaturated survivors (n={len(survivors)})",
        fontsize=FONT_SIZE,
    )
    for ax in axes:
        ax.axvline(
            Z0_K500 / 1e6,
            color="0.35",
            linestyle=":",
            linewidth=1.2,
            label="$z_0(k=500)=64.07$M",
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(1e-5, 72)
        ax.set_ylim(0.05, 20)
        ax.set_xlabel(
            "Delegation $\\sigma_i$ at epoch 228 (million ADA, log scale)",
            fontsize=FONT_SIZE,
        )
        ax.set_ylabel("Simple member APR (%)", fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE)
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=FONT_SIZE - 2, loc="lower right")
    fig.suptitle(
        "Member APR for Active pools remaining below the $k=500$ saturation cap\n"
        "Epoch-228 stake and pledge held fixed",
        fontsize=FONT_SIZE + 1,
    )
    fig.savefig(OUT_PLOT, dpi=300)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_PLOT}")
    print("\n".join(table_lines))
    print(description)


if __name__ == "__main__":
    main()
