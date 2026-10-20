#!/usr/bin/env python3
"""C.2 — elasticity heatmap for scalar protocol parameters.

Writes: elasticities_heatmap_epoch_644.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from comparison_common import (
    FONT_SIZE,
    OBJECTIVES,
    SCALAR_SHOCKS,
    compute_scoreboard,
    load_snapshot,
    relative_impacts,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "elasticities_heatmap_epoch_644.png"

COL_LABELS = (r"$k$", r"$a_0$", r"$\rho$")
ROW_LABELS = (
    r"$n$ with $r\geq 1$",
    "network APR",
    "median APR",
    r"$N$ (stake)",
    r"$N(f)$",
    r"$\sum f$",
)


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    el = relative_impacts(board)
    keys = list(SCALAR_SHOCKS)
    cols = [col for col, _, _ in OBJECTIVES]
    mat = np.array(
        [[float(el.loc[el["key"] == k, f"e_{col}"].iloc[0]) for k in keys] for col in cols],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(8.2, 6.2), constrained_layout=True)
    vmax = max(0.35, float(np.nanmax(np.abs(mat))))
    im = ax.imshow(mat, cmap="RdBu", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(keys)))
    ax.set_xticklabels(COL_LABELS, fontsize=FONT_SIZE)
    ax.set_yticks(np.arange(len(cols)))
    ax.set_yticklabels(ROW_LABELS, fontsize=FONT_SIZE)
    ax.tick_params(top=False, bottom=True, labeltop=False, labelbottom=True)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            label = "0" if abs(v) < 5e-4 else f"{v:+.2f}"
            color = "white" if abs(v) >= 0.55 * vmax else "black"
            ax.text(j, i, label, ha="center", va="center", fontsize=FONT_SIZE, color=color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r"elasticity $\varepsilon_{y,x}$", fontsize=FONT_SIZE)
    cbar.ax.tick_params(labelsize=FONT_SIZE - 1)
    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        r"Epoch 644 — Active pools: elasticities $\varepsilon_{y,x}$"
        "\n"
        r"(effects consider only the change in the relevant parameter; $c_i=75$ omitted)"
        "\n"
        rf"($C^*=741$ ADA/epoch; $R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
