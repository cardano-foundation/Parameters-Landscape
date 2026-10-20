#!/usr/bin/env python3
"""C.1 — changes vs baseline: n with r≥1 and median APR.

Writes: scoreboard_deltas_epoch_644.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from comparison_common import FONT_SIZE, compute_scoreboard, load_snapshot

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "scoreboard_deltas_epoch_644.png"

COLORS = {
    "k": "#4c78a8",
    "a0": "#4c78a8",
    "c": "#4c78a8",
    "rho": "#4c78a8",
    "k_c": "#e76f51",
    "k_a0": "#e76f51",
    "a0_c": "#e76f51",
    "k_after": "#2a9d8f",
}
LABELS = {
    "k": r"$k=1000$",
    "a0": r"$a_0=0.6$",
    "c": r"$c_i=75$",
    "rho": r"$\rho=0.0042$",
    "k_c": r"$k{+}c$",
    "k_a0": r"$k{+}a_0$",
    "a0_c": r"$a_0{+}c$",
    "k_after": r"$k$ after $D_i$",
}


def annotate(ax, x, vals, *, fmt):
    ymax = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]), 1.0)
    for i, v in zip(x, vals):
        va = "bottom" if v >= 0 else "top"
        off = 0.03 * ymax if v >= 0 else -0.03 * ymax
        ax.text(i, v + off, fmt(v), ha="center", va=va, fontsize=FONT_SIZE - 2)


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    base = board.iloc[0]
    d = board.loc[board["key"] != "base"].copy()
    x = np.arange(len(d))
    cols = [COLORS[k] for k in d["key"]]
    labels = [LABELS[k] for k in d["key"]]
    dn = d["n_r_ge1"] - base["n_r_ge1"]
    da = 100.0 * (d["median_apr"] - base["median_apr"])

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.4), constrained_layout=True)

    axes[0].bar(x, dn, color=cols, edgecolor="white")
    axes[0].axhline(0.0, color="0.3", lw=0.8)
    axes[0].set_ylabel(r"$\Delta n$ with $r\geq 1$", fontsize=FONT_SIZE)
    axes[0].set_title(r"$C^*=741$ ADA/epoch", fontsize=FONT_SIZE)
    pad = 0.22 * max(abs(float(dn.min())), abs(float(dn.max())), 1.0)
    axes[0].set_ylim(float(dn.min()) - pad, float(dn.max()) + pad)
    annotate(axes[0], x, dn, fmt=lambda v: f"{int(v):+d}")

    axes[1].bar(x, da, color=cols, edgecolor="white")
    axes[1].axhline(0.0, color="0.3", lw=0.8)
    axes[1].set_ylabel(r"$\Delta$ median APR (pp)", fontsize=FONT_SIZE)
    axes[1].set_title(r"Pools with $f>c$", fontsize=FONT_SIZE)
    pad = 0.22 * max(abs(float(da.min())), abs(float(da.max())), 1.0)
    axes[1].set_ylim(float(da.min()) - pad, float(da.max()) + pad)
    annotate(axes[1], x, da, fmt=lambda v: f"{v:+.2f}")

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=FONT_SIZE - 1)
        ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
        ax.grid(axis="y", alpha=0.25)

    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        "Epoch 644 — Active pools: change versus baseline\n"
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
