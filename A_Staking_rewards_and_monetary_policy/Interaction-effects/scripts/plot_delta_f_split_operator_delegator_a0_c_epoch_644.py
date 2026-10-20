#!/usr/bin/env python3
"""Epoch 644 — Δf split, a0=0.3→0.6 and all c_i=75.

Writes:
  delta_f_split_operator_delegator_a0_c_epoch_644.png
  delta_f_split_operator_delegator_a0_c_epoch_644.csv
  delta_f_split_operator_delegator_a0_c_epoch_644.md
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
    A0_1,
    C_FORCE,
    C_LABELS,
    C_ORDER,
    FONT_SIZE,
    K0,
    Q_LABELS,
    c_rows,
    grouped_panel,
    load_snapshot,
    md_table,
    pool_frame,
    q_rows,
    summarize,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "delta_f_split_operator_delegator_a0_c_epoch_644.png"
OUT_CSV = DIR / "delta_f_split_operator_delegator_a0_c_epoch_644.csv"
OUT_MD = DIR / "delta_f_split_operator_delegator_a0_c_epoch_644.md"


def main() -> None:
    snap = load_snapshot()
    d = pool_frame(
        snap,
        k0=K0, a0_0=A0_0, cost0=snap["cost"],
        k1=K0, a0_1=A0_1, cost1=np.full_like(snap["cost"], C_FORCE),
    )
    all_row = summarize(d, "all", "All Active")
    qq = q_rows(d)
    cc = c_rows(d)
    pd.DataFrame([all_row] + qq + cc).assign(
        section=["all"] + ["q"] * len(qq) + ["c"] * len(cc)
    ).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.2), constrained_layout=True)
    grouped_panel(
        axes[0], qq, [r["group"] for r in qq], Q_LABELS,
        r"By $q=\hat p/\sigma$", legend_loc="lower right",
    )
    grouped_panel(
        axes[1], cc, list(C_ORDER), C_LABELS,
        r"By declared $c_i$", legend_loc="lower right",
    )
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        rf"($a_0={A0_0}\to{A0_1}$ and all $c_i={int(C_FORCE)}$; $k={K0}$; "
        r"snapshot $\sigma,p,\hat p,m$ held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)

    OUT_MD.write_text(
        f"""# $\\Delta f$ split into operator $\\Pi$ and delegator rewards — $a_0$ and $c_i=75$ (epoch 644)

Active pledge-met pools, $n={all_row['n']}$. $a_0={A0_0}\\to{A0_1}$,
all $c_i={int(C_FORCE)}$, $k={K0}$.
$R={snap['R']:,.2f}$ ADA, $T={snap['T']:,.2f}$ ADA.
Declared $p$, $\\hat p$, $m_i$, and $\\sigma$ held fixed.
$q_i=\\hat p_i/\\sigma_i$, $s_i=m_i+(1-m_i)q_i$.
Sums are ADA/epoch. Median is the typical pool in the row.

## All Active

{md_table([all_row])}

## By $q=\\hat p/\\sigma$

{md_table(qq)}

## By declared $c_i$

{md_table(cc)}
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
