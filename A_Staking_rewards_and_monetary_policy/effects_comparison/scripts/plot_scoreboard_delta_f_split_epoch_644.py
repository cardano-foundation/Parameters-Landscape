#!/usr/bin/env python3
"""C.1 — Δf split into ΔΠ and Δ(f-Π) across shocks.

Writes: scoreboard_delta_f_split_epoch_644.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from comparison_common import FONT_SIZE, compute_scoreboard, load_snapshot

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "scoreboard_delta_f_split_epoch_644.png"

COLOR_PI = "#4c78a8"
COLOR_DEL = "#e76f51"
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


def annotate_bars(ax, bars) -> None:
    ymax = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]), 1.0)
    for bar in bars:
        h = bar.get_height()
        if abs(h) < 20:
            continue
        va = "bottom" if h >= 0 else "top"
        off = 0.02 * ymax if h >= 0 else -0.02 * ymax
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h + off,
            f"{h:,.0f}",
            ha="center",
            va=va,
            fontsize=FONT_SIZE - 3,
        )


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    d = board.loc[~board["key"].isin(("base", "k_after"))].copy()
    x = np.arange(len(d))
    w = 0.36
    pi = d["sum_delta_pi"].to_numpy() / 1e3
    deleg = d["sum_delta_delegator"].to_numpy() / 1e3
    labels = [LABELS[k] for k in d["key"]]

    fig, ax = plt.subplots(figsize=(13.6, 5.6), constrained_layout=True)
    b1 = ax.bar(x - w / 2, pi, w, color=COLOR_PI, edgecolor="white", label=r"$\Delta\Pi$ (operator)")
    b2 = ax.bar(
        x + w / 2, deleg, w, color=COLOR_DEL, edgecolor="white",
        label=r"$\Delta(f-\Pi)$ (delegators)",
    )
    ax.axhline(0.0, color="0.3", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=FONT_SIZE - 1)
    ax.set_ylabel(r"ADA/epoch (thousands)", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
    ax.legend(fontsize=FONT_SIZE - 1, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    vals = list(pi) + list(deleg)
    lo, hi = min(0.0, min(vals)), max(0.0, max(vals))
    pad = 0.22 * max(abs(lo), abs(hi), 1.0)
    ax.set_ylim(lo - pad, hi + pad)
    annotate_bars(ax, list(b1) + list(b2))
    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        r"Epoch 644 — Active pools: $\Delta f$ split into $\Delta\Pi$ and $\Delta(f-\Pi)$"
        "\n"
        r"(effects consider only the change in the relevant parameter; $k$ after $D_i$ omitted)"
        "\n"
        rf"($C^*=741$ ADA/epoch; $R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
