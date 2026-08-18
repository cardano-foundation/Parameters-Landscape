#!/usr/bin/env python3
"""Reward intensity R/S by epoch, full sample and post-bootstrap zoom."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "epoch_tokenomics_shelley_era.csv"
OUT = DIR / "reward_intensity_R_over_S.png"
FONT_SIZE = 12
RHO = 0.003
TAU = 0.2
ZOOM_FROM = 300
COLOR = "#2f6f4e"
COLOR_FIT = "0.35"


def main() -> None:
    df = pd.read_csv(CSV)
    reserves = pd.to_numeric(df["reserves_lovelace"], errors="coerce")
    fees = pd.to_numeric(df["fees_pot_lovelace"], errors="coerce")
    stake = pd.to_numeric(df["active_stake_lovelace"], errors="coerce")
    reward_pot = (1.0 - TAU) * (RHO * reserves + fees)
    ratio = reward_pot / stake
    epoch = df["epoch_no"]

    fig, (ax0, ax1) = plt.subplots(
        2,
        1,
        figsize=(10, 7.2),
        sharex=False,
        gridspec_kw={"height_ratios": [1.15, 1.0]},
        constrained_layout=True,
    )
    ax0.plot(epoch, ratio, color=COLOR, linewidth=2.0)
    ax0.set_ylabel(r"$R/S$", fontsize=FONT_SIZE)
    ax0.tick_params(axis="both", labelsize=FONT_SIZE)
    ax0.set_xlim(int(epoch.min()), int(epoch.max()))
    ax0.set_ylim(bottom=0.0)
    ax0.grid(alpha=0.25)
    ax0.set_title(
        r"Reward intensity $R/S$"
        "\n"
        rf"$R=(1-\tau)(\rho\cdot\mathrm{{reserves}}+\mathrm{{fees}})$, "
        rf"$\rho={RHO}$, $\tau={TAU}$",
        fontsize=FONT_SIZE,
    )

    z = epoch >= ZOOM_FROM
    e = epoch[z].to_numpy(dtype=float)
    y = ratio[z].to_numpy(dtype=float)
    mask = np.isfinite(y)
    e, y = e[mask], y[mask]
    slope, intercept = np.polyfit(e, y, 1)
    fit = intercept + slope * e
    r2 = 1.0 - np.sum((y - fit) ** 2) / np.sum((y - y.mean()) ** 2)

    ax1.plot(e, y, color=COLOR, linewidth=2.0, label=r"$R/S$")
    ax1.plot(
        e,
        fit,
        color=COLOR_FIT,
        linewidth=1.4,
        linestyle="--",
        label=rf"linear fit ($R^2={r2:.2f}$)",
    )
    ax1.set_xlabel("Epoch", fontsize=FONT_SIZE)
    ax1.set_ylabel(r"$R/S$", fontsize=FONT_SIZE)
    ax1.tick_params(axis="both", labelsize=FONT_SIZE)
    ax1.set_xlim(ZOOM_FROM, int(epoch.max()))
    ax1.grid(alpha=0.25)
    ax1.legend(fontsize=FONT_SIZE, loc="upper right")
    ax1.set_title(rf"Same series from epoch {ZOOM_FROM} (scale not forced through 0)", fontsize=FONT_SIZE)

    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
