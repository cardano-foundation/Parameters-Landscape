#!/usr/bin/env python3
"""Reserves, total supply T, and active stake S by epoch (Shelley onward)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "epoch_tokenomics_shelley_era.csv"
OUT = DIR / "reserves_supply_stake.png"
FONT_SIZE = 12
LOVELACE = 1e6
BILLION = 1e9
COLOR_RESERVES = "#8c6d31"
COLOR_T = "#1f4e79"
COLOR_S = "#2f6f4e"


def main() -> None:
    df = pd.read_csv(CSV)
    epoch = df["epoch_no"]
    reserves = pd.to_numeric(df["reserves_lovelace"], errors="coerce") / LOVELACE / BILLION
    supply = pd.to_numeric(df["supply_lovelace"], errors="coerce") / LOVELACE / BILLION
    stake = pd.to_numeric(df["active_stake_lovelace"], errors="coerce") / LOVELACE / BILLION

    fig, ax = plt.subplots(1, 1, figsize=(10, 5), constrained_layout=True)
    ax.plot(epoch, reserves, color=COLOR_RESERVES, linewidth=2.0, label=r"Reserves")
    ax.plot(epoch, supply, color=COLOR_T, linewidth=2.0, label=r"$T$ (supply)")
    ax.plot(epoch, stake, color=COLOR_S, linewidth=2.0, label=r"$S$ (active stake)")
    ax.set_xlabel("Epoch", fontsize=FONT_SIZE)
    ax.set_ylabel(r"ADA ($\times 10^{9}$)", fontsize=FONT_SIZE)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.set_xlim(int(epoch.min()), int(epoch.max()))
    ax.set_ylim(bottom=0.0)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="upper left")
    ax.set_title(
        r"Reserves, supply $T$, and active stake $S$"
        "\n"
        rf"Epochs {int(epoch.min())}–{int(epoch.max())} (Shelley onward)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved:", OUT)


if __name__ == "__main__":
    main()
