#!/usr/bin/env python3
"""Epoch 644 — Δf split, k=500→1000 and all c_i=75.

Writes:
  delta_f_split_operator_delegator_k_c_epoch_644.png
  delta_f_split_operator_delegator_k_c_epoch_644.csv
  delta_f_split_operator_delegator_k_c_epoch_644.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from delta_f_split_interaction_common import (
    A0_0,
    C_FORCE,
    FONT_SIZE,
    K0,
    K1,
    Q_LABELS,
    SAT_LABELS,
    SAT_ORDER,
    grouped_panel,
    load_snapshot,
    md_table,
    pool_frame,
    q_rows,
    sat_rows,
    summarize,
)
DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_f_split_operator_delegator_k_c_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_k_c_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_k_c_epoch_644.md"


def main() -> None:
    snap = load_snapshot()
    d = pool_frame(
        snap,
        k0=K0, a0_0=A0_0, cost0=snap["cost"],
        k1=K1, a0_1=A0_0, cost1=np.full_like(snap["cost"], C_FORCE),
    )
    all_row = summarize(d, "all", "All Active")
    s_rows = sat_rows(d)
    qq = q_rows(d)
    pd.DataFrame([all_row] + s_rows + qq).assign(
        section=["all"] + ["sat"] * len(s_rows) + ["q"] * len(qq)
    ).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    grouped_panel(
        axes[0], s_rows, list(SAT_ORDER), SAT_LABELS,
        r"By saturation status", legend_loc="upper right",
    )
    grouped_panel(
        axes[1], qq, [r["group"] for r in qq], Q_LABELS,
        r"By $q=\hat p/\sigma$", legend_loc="upper right",
    )
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        rf"($k={K0}\to{K1}$ and all $c_i={int(C_FORCE)}$; snapshot $\sigma,p,\hat p,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    z0_0 = snap["T"] / K0
    z0_1 = snap["T"] / K1
    OUT_MD.write_text(
        f"""# $\\Delta f$ split into operator $\\Pi$ and delegator rewards — $k$ and $c_i=75$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. $k={K0}\\to{K1}$,
$z_0={z0_0/1e6:.2f}$M$\\to{z0_1/1e6:.2f}$M ADA, all $c_i={int(C_FORCE)}$.
$R={snap['R']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
Declared $p$, $\\hat p$, $m_i$, and $\\sigma$ held fixed.
$q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.

## All Active

{md_table([all_row])}

## By saturation status

{md_table(s_rows)}

## By $q=\\hat p/\\sigma$

{md_table(qq)}
"""
    )
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")
    print(
        f"all n={all_row['n']} df={all_row['sum_delta_f']:.1f} "
        f"dPi={all_row['sum_delta_pi']:.1f} dM={all_row['sum_delta_delegator']:.1f}"
    )


if __name__ == "__main__":
    main()
