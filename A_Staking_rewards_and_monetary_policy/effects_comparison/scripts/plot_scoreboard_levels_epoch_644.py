#!/usr/bin/env python3
"""C.1 — levels: n with r≥1, median APR, Nakamoto N.

Writes: scoreboard_levels_epoch_644.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from comparison_common import FONT_SIZE, compute_scoreboard, load_snapshot

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "scoreboard_levels_epoch_644.png"

COLORS = {
    "base": "#9e9e9e",
    "k": "#4c78a8",
    "a0": "#4c78a8",
    "c": "#4c78a8",
    "rho": "#4c78a8",
    "k_c": "#e76f51",
    "k_a0": "#e76f51",
    "a0_c": "#e76f51",
    "k_after": "#2a9d8f",
}


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    x = np.arange(len(board))
    cols = [COLORS[k] for k in board["key"]]
    labels = [
        "Baseline",
        r"$k=1000$",
        r"$a_0=0.6$",
        r"$c_i=75$",
        r"$\rho=0.0042$",
        r"$k{+}c$",
        r"$k{+}a_0$",
        r"$a_0{+}c$",
        r"$k$ after $D_i$",
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14.8, 5.4), constrained_layout=True)

    axes[0].bar(x, board["n_r_ge1"], color=cols, edgecolor="white")
    axes[0].set_ylabel(r"$n$ with $r\geq 1$", fontsize=FONT_SIZE)
    axes[0].set_title(r"$C^*=741$ ADA/epoch", fontsize=FONT_SIZE)
    for i, v in enumerate(board["n_r_ge1"]):
        axes[0].text(i, v + 6, f"{int(v)}", ha="center", va="bottom", fontsize=FONT_SIZE - 3)

    axes[1].bar(x, 100.0 * board["median_apr"], color=cols, edgecolor="white")
    axes[1].set_ylabel("Median APR (%)", fontsize=FONT_SIZE)
    axes[1].set_title(r"Pools with $f>c$", fontsize=FONT_SIZE)
    for i, v in enumerate(100.0 * board["median_apr"]):
        axes[1].text(i, v + 0.04, f"{v:.2f}", ha="center", va="bottom", fontsize=FONT_SIZE - 3)

    axes[2].bar(x, board["nakamoto_n"], color=cols, edgecolor="white")
    axes[2].set_ylabel(r"Nakamoto $N$ (stake)", fontsize=FONT_SIZE)
    axes[2].set_title(r"Pool stake", fontsize=FONT_SIZE)
    for i, v in enumerate(board["nakamoto_n"]):
        axes[2].text(i, v + 4, f"{int(v)}", ha="center", va="bottom", fontsize=FONT_SIZE - 3)

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=FONT_SIZE - 2)
        ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
        ax.grid(axis="y", alpha=0.25)
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax * 1.12)

    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        "Epoch 644 — Active pools: scoreboard\n"
        r"(effects consider only the change in the relevant parameter, except $k$ after $D_i$)"
        "\n"
        rf"($C^*=741$ ADA/epoch; $R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
