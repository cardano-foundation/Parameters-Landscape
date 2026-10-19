#!/usr/bin/env python3
"""Epoch 644 — Cover (r≥1) heatmap vs ADA price and USD opex, k=500 vs k=1000.

Writes:
  pool_viability_price_cost_heatmap_cover_k_epoch_644.png
  pool_viability_price_cost_k_epoch_644.csv
  pool_viability_price_cost_k_epoch_644.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from viability_price_cost_k_common import (
    FONT_SIZE,
    K_VALUES,
    OPEX,
    OPEX_MD,
    PRICES,
    build_grid,
    c_star,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_viability_price_cost_heatmap_cover_k_epoch_644.png"
OUT_CSV = DIR / "pool_viability_price_cost_k_epoch_644.csv"
OUT_MD = DIR / "pool_viability_price_cost_k_epoch_644.md"

HEAT_CMAP = LinearSegmentedColormap.from_list(
    "cover_teal",
    ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#084594"],
)


def ada_b(x: float) -> str:
    return f"{x / 1e9:.2f}"


def md_table_cstar() -> str:
    header = (
        "| ADA price | 58.5 USD/mo (39 ADA @ 0.25) | 256.5 USD/mo (171 ADA @ 0.25) "
        "| 667 USD/mo (paper) | 1,479 USD/mo (986 ADA @ 0.25) |\n"
        "|---:|---:|---:|---:|---:|\n"
    )
    lines = [header]
    for p in PRICES:
        cells = [f"{p:.2f}"]
        for opex in OPEX:
            cells.append(f"{c_star(opex['usd_month'], p):.1f}")
        lines.append("| " + " | ".join(cells) + " |\n")
    return "".join(lines)


def md_k_table(df, k: int) -> str:
    sub = df[df["k"] == k]
    lines = [
        "| ADA price | Opex | $C^*$ (ADA) | $n$ ($r<1$) | $n$ ($1\\leq r<2$) | $n$ ($r\\geq 2$) | "
        "Stake $r<1$ (B ADA) | Stake $1\\leq r<2$ | Stake $r\\geq 2$ | Median $r$ |\n",
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for opex, opex_md in zip(OPEX, OPEX_MD):
        for p in PRICES:
            hit = sub[
                np.isclose(sub["usd_month"], opex["usd_month"]) & np.isclose(sub["ada_usd"], p)
            ].iloc[0]
            lines.append(
                f"| {p:.2f} | {opex_md} | {hit['c_star_ada']:.1f} | "
                f"{int(hit['n_deficit'])} | {int(hit['n_edge'])} | {int(hit['n_cover2'])} | "
                f"{ada_b(hit['stake_deficit'])} | {ada_b(hit['stake_edge'])} | "
                f"{ada_b(hit['stake_cover2'])} | {hit['median_r']:.2f} |\n"
            )
    return "".join(lines)


def main() -> None:
    grid = build_grid()
    grid.to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 3, figsize=(16.2, 4.8), constrained_layout=True)
    ylabels = [o["label"] for o in OPEX]
    xlabels = [f"${p:.2f}" for p in PRICES]

    mats = []
    for k in K_VALUES:
        mat = np.zeros((len(OPEX), len(PRICES)))
        for i, opex in enumerate(OPEX):
            for j, p in enumerate(PRICES):
                hit = grid[
                    (grid["k"] == k)
                    & np.isclose(grid["usd_month"], opex["usd_month"])
                    & np.isclose(grid["ada_usd"], p)
                ].iloc[0]
                mat[i, j] = hit["n_cover"]
        mats.append(mat)

    vmax = max(m.max() for m in mats)
    for ax, mat, k in zip(axes[:2], mats, K_VALUES):
        im = ax.imshow(mat, cmap=HEAT_CMAP, vmin=0.0, vmax=vmax, aspect="auto")
        ax.set_xticks(np.arange(len(PRICES)))
        ax.set_xticklabels(xlabels, fontsize=FONT_SIZE - 1)
        ax.set_yticks(np.arange(len(OPEX)))
        ax.set_yticklabels(ylabels, fontsize=FONT_SIZE - 1)
        ax.set_xlabel("ADA price (USD)", fontsize=FONT_SIZE)
        ax.set_title(rf"Cover $r\geq 1$, $k={k}$", fontsize=FONT_SIZE)
        for i in range(len(OPEX)):
            for j in range(len(PRICES)):
                ax.text(
                    j, i, f"{int(mat[i, j])}",
                    ha="center", va="center", fontsize=FONT_SIZE - 1, color="0.1",
                )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 1)

    delta = mats[1] - mats[0]
    lim = max(abs(float(delta.min())), abs(float(delta.max())), 1.0)
    im = axes[2].imshow(delta, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
    axes[2].set_xticks(np.arange(len(PRICES)))
    axes[2].set_xticklabels(xlabels, fontsize=FONT_SIZE - 1)
    axes[2].set_yticks(np.arange(len(OPEX)))
    axes[2].set_yticklabels(ylabels, fontsize=FONT_SIZE - 1)
    axes[2].set_xlabel("ADA price (USD)", fontsize=FONT_SIZE)
    axes[2].set_title(r"$\Delta$ Cover: $k=1000$ minus $k=500$", fontsize=FONT_SIZE)
    for i in range(len(OPEX)):
        for j in range(len(PRICES)):
            axes[2].text(
                j, i, f"{int(delta[i, j]):+d}",
                ha="center", va="center", fontsize=FONT_SIZE - 1, color="0.1",
            )
    fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 1)

    fig.suptitle(
        r"Epoch 644 — Active pools covering $C^*(P)=\mathrm{opex}/(6P)$"
        "\n"
        r"($k=500$ vs $k=1000$; snapshot $\Pi_i$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    n_active = int(grid["n"].iloc[0])
    R = float(grid["R_ada"].iloc[0])
    T = float(grid["T_ada"].iloc[0])
    md = f"""# Viability vs ADA price and USD opex — $k$ (epoch 644, Active pools)

Snapshot $\\Pi_i$ is held fixed (declared $c_i$, $m_i$, $\\sigma_i$, $p_i$, $\\hat p_i$).
$k$ changes $z_0$ and therefore $\\Pi_i$; ADA price $P$ and USD opex change only
$$C^*(P)=\\frac{{\\text{{USD/month}}}}{{6P}},\\qquad r_i=\\Pi_i/C^*(P).$$
$n={n_active}$ Active pledge-met pools. $R={R:,.2f}$ ADA, $T={T:,.2f}$ ADA.

USD opex levels: 58.5 USD/month ($39$ ADA/epoch at $0.25$ USD/ADA), 256.5 USD/month
($171$ ADA/epoch at $0.25$), 667 USD/month (paper baseline), 1,479 USD/month
($986$ ADA/epoch at $0.25$).

## $C^*$ (ADA/epoch)

{md_table_cstar()}

## $k=500$

{md_k_table(grid, 500)}

## $k=1000$

{md_k_table(grid, 1000)}
"""
    OUT_MD.write_text(md)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
