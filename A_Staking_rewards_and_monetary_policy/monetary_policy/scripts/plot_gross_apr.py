#!/usr/bin/env python3
"""Theoretical gross APR bounds by epoch using 73R/T and 73R/((1+a0)T)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "epoch_tokenomics_shelley_era.csv"
OUT = DIR / "gross_apr.png"
FONT_SIZE = 12
RHO = 0.003
TAU = 0.2
A0 = 0.3
EPOCHS_PER_YEAR = 73.0
COLOR_UPPER = "#1f4e79"
COLOR_LOWER = "#2f6f4e"
COLOR_BAND = "#93c5fd"


def main() -> None:
    df = pd.read_csv(CSV)
    reserves = pd.to_numeric(df["reserves_lovelace"], errors="coerce")
    fees = pd.to_numeric(df["fees_pot_lovelace"], errors="coerce")
    supply = pd.to_numeric(df["supply_lovelace"], errors="coerce")
    reward_pot = (1.0 - TAU) * (RHO * reserves + fees)
    upper_bound = EPOCHS_PER_YEAR * reward_pot / supply
    lower_bound = EPOCHS_PER_YEAR * reward_pot / ((1.0 + A0) * supply)

    fig, ax = plt.subplots(1, 1, figsize=(10, 5), constrained_layout=True)
    epoch = df["epoch_no"]
    upper_pct = 100.0 * upper_bound
    lower_pct = 100.0 * lower_bound
    ax.fill_between(epoch, lower_pct, upper_pct, color=COLOR_BAND, alpha=0.25, linewidth=0.0)
    ax.plot(epoch, upper_pct, color=COLOR_UPPER, linewidth=2.0, label="Upper bound: $73R/T$")
    ax.plot(
        epoch,
        lower_pct,
        color=COLOR_LOWER,
        linewidth=2.0,
        linestyle="--",
        label=r"Lower bound: $73R/((1+a_0)T)$",
    )
    ax.set_xlabel("Epoch", fontsize=FONT_SIZE)
    ax.set_ylabel("APR (%)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(int(df["epoch_no"].min()), int(df["epoch_no"].max()))
    ax.set_ylim(bottom=0.0)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="upper right")
    ax.set_title(
        r"Theoretical gross APR bounds"
        "\n"
        rf"$R=(1-\tau)(\rho\cdot\mathrm{{reserves}}+\mathrm{{fees}})$, "
        rf"$\rho={RHO}$, $\tau={TAU}$, $a_0={A0}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
