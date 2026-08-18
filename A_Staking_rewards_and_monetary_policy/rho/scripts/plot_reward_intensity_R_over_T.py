#!/usr/bin/env python3
"""Reward intensity R/T by epoch, with R = (1-τ)(ρ·reserves + fees)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "epoch_tokenomics_shelley_era.csv"
OUT = DIR / "reward_intensity_R_over_T.png"
FONT_SIZE = 12
RHO = 0.003
TAU = 0.2
COLOR = "#1f4e79"


def main() -> None:
    df = pd.read_csv(CSV)
    reserves = pd.to_numeric(df["reserves_lovelace"], errors="coerce")
    fees = pd.to_numeric(df["fees_pot_lovelace"], errors="coerce")
    supply = pd.to_numeric(df["supply_lovelace"], errors="coerce")
    reward_pot = (1.0 - TAU) * (RHO * reserves + fees)
    intensity = reward_pot / supply

    fig, ax = plt.subplots(1, 1, figsize=(10, 5), constrained_layout=True)
    ax.plot(df["epoch_no"], intensity, color=COLOR, linewidth=2.0)
    ax.set_xlabel("Epoch", fontsize=FONT_SIZE)
    ax.set_ylabel(r"$R/T$", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(int(df["epoch_no"].min()), int(df["epoch_no"].max()))
    ax.set_ylim(bottom=0.0)
    ax.grid(alpha=0.25)
    ax.set_title(
        r"Reward intensity $R/T$"
        "\n"
        rf"$R=(1-\tau)(\rho\cdot\mathrm{{reserves}}+\mathrm{{fees}})$, "
        rf"$\rho={RHO}$, $\tau={TAU}$",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
