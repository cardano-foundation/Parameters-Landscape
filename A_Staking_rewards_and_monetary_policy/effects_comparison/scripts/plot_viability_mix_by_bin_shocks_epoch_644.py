#!/usr/bin/env python3
"""C.2 — viability mix by 5M stake bin: baseline, k, a0, c_i=75.

Writes:
  viability_mix_by_bin_shocks_epoch_644.png
  viability_mix_by_bin_shocks_epoch_644.csv
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
    R_COLORS,
    R_LABELS,
    R_ORDER,
    assign_stake_bins,
    classify_r,
    load_snapshot,
    outcomes_from_spec,
    spec_by_key,
    stake_bin_labels,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "viability_mix_by_bin_shocks_epoch_644.png"
OUT_CSV = DIR / "viability_mix_by_bin_shocks_epoch_644.csv"

PANELS = (
    ("base", "Baseline"),
    ("k", r"$k=1000$"),
    ("a0", r"$a_0=0.6$"),
    ("c", r"$c_i=75$"),
)


def stacked_percentages(ax, x, pct) -> None:
    bottom = np.zeros(len(x))
    for row, color, lab in zip(pct, R_COLORS, R_LABELS):
        ax.bar(x, row, bottom=bottom, color=color, edgecolor="0.2", width=0.85, label=lab)
        hex_c = color.lstrip("#")
        rr, gg, bb = (int(hex_c[i : i + 2], 16) for i in (0, 2, 4))
        label_color = "0.15" if (0.299 * rr + 0.587 * gg + 0.114 * bb) > 160 else "white"
        for xi, h, b in zip(x, row, bottom):
            if h >= 10.0:
                ax.text(
                    xi, b + h / 2.0, f"{h:.0f}",
                    ha="center", va="center", fontsize=FONT_SIZE - 5, color=label_color,
                )
        bottom = bottom + row
    ax.set_ylim(0, 100)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax.tick_params(labelsize=FONT_SIZE - 2)
    ax.grid(axis="y", alpha=0.25)


def mix_for(r, bin_idx, n_bins):
    n_pools = np.zeros((len(R_ORDER), n_bins), dtype=float)
    r_index = {name: i for i, name in enumerate(R_ORDER)}
    for ratio, b in zip(r, bin_idx):
        n_pools[r_index[classify_r(float(ratio))], b] += 1.0
    n_tot = n_pools.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        n_pct = np.where(n_tot > 0, 100.0 * n_pools / n_tot, 0.0)
    return n_pools, n_pct, n_tot


def main() -> None:
    snap = load_snapshot()
    edges, labels = stake_bin_labels()
    n_bins = len(labels)
    stake_m = snap["sigma"] / 1e6
    bin_idx = assign_stake_bins(stake_m, edges)
    x = np.arange(n_bins)

    rows = []
    mixes = {}
    for key, _ in PANELS:
        out = outcomes_from_spec(snap, spec_by_key(snap, key))
        r = np.where(out["met"], out["r"], np.nan)
        n_pools, n_pct, n_tot = mix_for(r, bin_idx, n_bins)
        mixes[key] = n_pct
        for j, lab in enumerate(labels):
            for i, name in enumerate(R_ORDER):
                rows.append(
                    {
                        "shock": key,
                        "stake_bin_M_ADA": lab,
                        "r_class": name,
                        "n_pools": int(n_pools[i, j]),
                        "n_bin": int(n_tot[j]),
                        "share_of_pools_in_bin_pct": float(n_pct[i, j]),
                    }
                )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(14.6, 8.4), sharex=True, sharey=True)
    for ax, (key, title) in zip(axes.ravel(), PANELS):
        stacked_percentages(ax, x, mixes[key])
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=FONT_SIZE - 4, rotation=45, ha="right")
    axes[0, 0].set_ylabel("% of pools in bin", fontsize=FONT_SIZE)
    axes[1, 0].set_ylabel("% of pools in bin", fontsize=FONT_SIZE)
    axes[1, 0].set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)
    axes[1, 1].set_xlabel("Epoch stake bin (M ADA)", fontsize=FONT_SIZE)

    handles, labs = axes[0, 0].get_legend_handles_labels()
    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        r"Epoch 644 — viability mix by stake bin"
        "\n"
        r"(effects consider only the change in the relevant parameter; $\rho$ omitted)"
        "\n"
        rf"($C^*=741$ ADA/epoch; $R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.tight_layout()
    fig.subplots_adjust(top=0.84, bottom=0.16, hspace=0.32, wspace=0.12)
    fig.legend(
        handles, labs, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 0.01),
        frameon=False, fontsize=FONT_SIZE - 1, columnspacing=1.4, handletextpad=0.5,
    )
    fig.savefig(OUT_PNG, dpi=160)
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
