#!/usr/bin/env python3
"""Epoch 644 — r≥1 heatmap vs ADA price and USD opex, k and minPoolCost.

Baseline: k=500, declared c_i.
Joint:    k=1000, all c_i=75.

Writes:
  pool_viability_price_cost_heatmap_cover_k_c_epoch_644.png
  pool_viability_price_cost_k_c_epoch_644.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np

from viability_price_cost_interaction_common import (
    A0_0,
    C_FORCE,
    K0,
    K1,
    build_grid,
    draw_heatmap,
    load_snapshot,
    paper_cell,
    pi_at,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "pool_viability_price_cost_heatmap_cover_k_c_epoch_644.png"
OUT_CSV = DIR / "pool_viability_price_cost_k_c_epoch_644.csv"


def main() -> None:
    snap = load_snapshot()
    pi0 = pi_at(snap, k=K0, a0=A0_0, cost=snap["cost"])
    pi1 = pi_at(snap, k=K1, a0=A0_0, cost=np.full_like(snap["cost"], C_FORCE))
    grid, mat0, mat1 = build_grid(
        pi0, pi1, snap,
        "n_r_ge1_k500_declared_c",
        "n_r_ge1_k1000_c75",
        "delta_joint_minus_base",
    )
    grid.to_csv(OUT_CSV, index=False)
    draw_heatmap(
        mat0, mat1,
        title0=rf"$r\geq 1$, $k={K0}$, declared $c_i$",
        title1=rf"$r\geq 1$, $k={K1}$, $c_i={int(C_FORCE)}$",
        title_delta=rf"$\Delta$: joint minus baseline",
        suptitle=(
            r"Epoch 644 — Active pools with $r=\Pi_i/C^*(P)\geq 1$"
            "\n"
            rf"($k={K0}$, declared $c_i$ vs $k={K1}$, $c_i={int(C_FORCE)}$; "
            r"snapshot $\sigma,p,\hat p,m$ held fixed)"
        ),
        out_png=OUT_PNG,
    )
    cell = paper_cell(grid)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(
        f"paper cell $667, $0.15: base n={int(cell['n_r_ge1_k500_declared_c'])}, "
        f"joint n={int(cell['n_r_ge1_k1000_c75'])}, "
        f"delta={int(cell['delta_joint_minus_base'])}, C*={cell['c_star_ada']:.1f}"
    )


if __name__ == "__main__":
    main()
