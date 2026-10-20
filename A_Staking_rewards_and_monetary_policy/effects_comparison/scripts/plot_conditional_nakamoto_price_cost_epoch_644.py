#!/usr/bin/env python3
"""C.2 — N(σ | r≥1) vs ADA price and USD opex; baseline and Δ for k, a0, c.

Writes:
  conditional_nakamoto_price_cost_epoch_644.png
  conditional_nakamoto_price_cost_epoch_644.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from comparison_common import (
    FONT_SIZE,
    OPEX,
    PRICES,
    c_star,
    load_snapshot,
    nakamoto_coefficient,
    nakamoto_of_total,
    outcomes_from_spec,
    spec_by_key,
)

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "conditional_nakamoto_price_cost_epoch_644.png"
OUT_CSV = DIR / "conditional_nakamoto_price_cost_epoch_644.csv"

HEAT_CMAP = LinearSegmentedColormap.from_list(
    "n_teal",
    ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#084594"],
)
SHOCKS = ("base", "k", "a0", "c")


def main() -> None:
    snap = load_snapshot()
    sigma = snap["sigma"]
    total = float(sigma.sum())
    cached = {key: outcomes_from_spec(snap, spec_by_key(snap, key)) for key in SHOCKS}

    rows = []
    mats = {key: np.zeros((len(OPEX), len(PRICES))) for key in SHOCKS}
    for i, opex in enumerate(OPEX):
        for j, p in enumerate(PRICES):
            cstar = c_star(opex["usd_month"], p)
            for key in SHOCKS:
                out = cached[key]
                viable = out["met"] & (out["pi"] / cstar >= 1.0)
                n = int(viable.sum())
                n_coeff = nakamoto_coefficient(sigma[viable]) if n else 0
                share = float(sigma[viable].sum() / total) if n else 0.0
                n_tot = nakamoto_of_total(sigma[viable], total)
                mats[key][i, j] = n_coeff
                rows.append(
                    {
                        "shock": key,
                        "usd_month": opex["usd_month"],
                        "opex_label": opex["label"],
                        "ada_usd": p,
                        "c_star_ada": cstar,
                        "n_r_ge1": n,
                        "nakamoto_sigma_rge1": n_coeff,
                        "stake_share_rge1": share,
                        "nakamoto_total_via_rge1": n_tot,
                    }
                )
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    fig, axes = plt.subplots(1, 4, figsize=(17.6, 4.8), constrained_layout=True)
    ylabels = [o["label"] for o in OPEX]
    xlabels = [f"${p:.2f}" for p in PRICES]
    vmax = max(float(mats[k].max()) for k in SHOCKS)

    ax = axes[0]
    im = ax.imshow(mats["base"], cmap=HEAT_CMAP, vmin=0.0, vmax=vmax, aspect="auto")
    ax.set_title(r"Baseline $N(\sigma\mid r\geq 1)$", fontsize=FONT_SIZE)
    for i in range(len(OPEX)):
        for j in range(len(PRICES)):
            ax.text(
                j, i, f"{int(mats['base'][i, j])}",
                ha="center", va="center", fontsize=FONT_SIZE - 2, color="0.1",
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 2)

    lim = 1.0
    deltas = {}
    for key in ("k", "a0", "c"):
        deltas[key] = mats[key] - mats["base"]
        lim = max(lim, abs(float(deltas[key].min())), abs(float(deltas[key].max())))
    titles = {
        "k": r"$\Delta$ $k=1000$",
        "a0": r"$\Delta$ $a_0=0.6$",
        "c": r"$\Delta$ $c_i=75$",
    }
    for ax, key in zip(axes[1:], ("k", "a0", "c")):
        im = ax.imshow(deltas[key], cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
        ax.set_title(titles[key], fontsize=FONT_SIZE)
        for i in range(len(OPEX)):
            for j in range(len(PRICES)):
                v = int(deltas[key][i, j])
                ax.text(
                    j, i, f"{v:+d}",
                    ha="center", va="center", fontsize=FONT_SIZE - 2, color="0.1",
                )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(labelsize=FONT_SIZE - 2)

    for ax in axes:
        ax.set_xticks(np.arange(len(PRICES)))
        ax.set_xticklabels(xlabels, fontsize=FONT_SIZE - 2)
        ax.set_yticks(np.arange(len(OPEX)))
        ax.set_yticklabels(ylabels, fontsize=FONT_SIZE - 2)
        ax.set_xlabel("ADA price (USD)", fontsize=FONT_SIZE - 1)
    axes[0].set_ylabel("USD opex / month", fontsize=FONT_SIZE - 1)

    r_m = snap["R0"] / 1e6
    t_b = snap["T"] / 1e9
    fig.suptitle(
        r"Epoch 644 — conditional Nakamoto $N(\sigma\mid r\geq 1)$ vs price and opex"
        "\n"
        r"(effects consider only the change in the relevant parameter; $\rho$ omitted)"
        "\n"
        rf"($R={r_m:.2f}$M ADA, $T={t_b:.2f}$B ADA; "
        r"$r=\Pi/C^*$, $C^*=\mathrm{opex}/(6P)$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PNG, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_PNG}")
    print(f"Saved: {OUT_CSV}")


if __name__ == "__main__":
    main()
