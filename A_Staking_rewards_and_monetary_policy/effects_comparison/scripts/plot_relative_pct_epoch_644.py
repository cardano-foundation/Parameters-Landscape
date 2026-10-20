#!/usr/bin/env python3
"""C.2 — percent change versus baseline, including the c_i=75 finite difference.

Writes: relative_pct_epoch_644.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from comparison_common import FONT_SIZE, compute_scoreboard, load_snapshot, pct_change

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "relative_pct_epoch_644.png"

SHOCKS = (
    ("k", r"$k=1000$", "#4c78a8"),
    ("a0", r"$a_0=0.6$", "#f2a65a"),
    ("c", r"$c_i=75$", "#e76f51"),
    ("rho", r"$\rho=0.0042$", "#2a9d8f"),
)
METRICS = (
    ("n_r_ge1", r"$n$ with $r\geq 1$"),
    ("network_apr", "network APR"),
    ("nakamoto_f", r"$N(f)$"),
    ("sum_f", r"$\sum f$"),
)


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    base = board.loc[board["key"] == "base"].iloc[0]
    by_key = {row["key"]: row for _, row in board.iterrows()}

    x = np.arange(len(METRICS))
    n = len(SHOCKS)
    w = 0.18
    offsets = (np.arange(n) - (n - 1) / 2) * (w + 0.02)

    fig, ax = plt.subplots(figsize=(12.4, 5.6), constrained_layout=True)
    for off, (key, lab, col) in zip(offsets, SHOCKS):
        vals = [100.0 * pct_change(by_key[key][m], base[m]) for m, _ in METRICS]
        bars = ax.bar(x + off, vals, w, color=col, edgecolor="white", label=lab)
        for bar, v in zip(bars, vals):
            if abs(v) < 0.15:
                continue
            va = "bottom" if v >= 0 else "top"
            pad = 1.2 if v >= 0 else -1.2
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + pad,
                f"{v:+.1f}",
                ha="center",
                va=va,
                fontsize=FONT_SIZE - 3,
            )
    ax.axhline(0.0, color="0.3", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, lab in METRICS], fontsize=FONT_SIZE)
    ax.set_ylabel("Percent change versus baseline (%)", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE - 1)
    ax.set_ylim(-38, 52)
    ax.legend(
        fontsize=FONT_SIZE - 1,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        frameon=False,
    )
    ax.grid(axis="y", alpha=0.25)
    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        "Epoch 644 — Active pools: percent change versus baseline"
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
