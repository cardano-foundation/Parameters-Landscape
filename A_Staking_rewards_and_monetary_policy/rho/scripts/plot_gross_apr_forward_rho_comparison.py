#!/usr/bin/env python3
"""Forward path of gross APR bounds over the next 1000 epochs.

Baseline:  rho = 0.003, tau = 0.2
Counterfactual: rho = 0.0042, tau = 0.2 (unchanged)

Starting from the latest Shelley-era snapshot:
    Q_0 = reserves, T_0 = supply, F_t held fixed at current fee pot.

Dynamics (each epoch):
    Q_{n+1} = (1 - rho) Q_n
    T_{n+1} = T_n + rho Q_n
    R_n     = (1 - tau) (rho Q_n + F)

Gross APR bounds:
    upper = 73 R / T
    lower = 73 R / ((1 + a0) T)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
CSV = DIR / "epoch_tokenomics_shelley_era.csv"
OUT_PNG = DIR / "gross_apr_forward_rho_comparison.png"

FONT_SIZE = 12
TAU = 0.2
A0 = 0.3
EPOCHS_PER_YEAR = 73.0
N_EPOCHS = 1000
RHOS = (0.003, 0.006)
STYLES = {
    0.003: {"band": "#93c5fd", "line": "#1f4e79"},
    0.006: {"band": "#fcd34d", "line": "#b45309"},
}


def forward_path(q0: float, t0: float, fees: float, rho: float) -> tuple[np.ndarray, np.ndarray]:
    epochs = np.arange(N_EPOCHS + 1)
    q = q0 * (1.0 - rho) ** epochs
    t = (t0 + q0) - q
    r = (1.0 - TAU) * (rho * q + fees)
    upper = 100.0 * EPOCHS_PER_YEAR * r / t
    lower = 100.0 * EPOCHS_PER_YEAR * r / ((1.0 + A0) * t)
    return upper, lower


def main() -> None:
    df = pd.read_csv(CSV)
    row = df.iloc[-1]
    q0 = float(row["reserves_lovelace"]) / 1e6
    t0 = float(row["supply_lovelace"]) / 1e6
    fees = float(row["fees_pot_lovelace"]) / 1e6
    epoch0 = int(row["epoch_no"])

    paths = {rho: forward_path(q0, t0, fees, rho) for rho in RHOS}
    x = np.arange(N_EPOCHS + 1)

    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)

    for rho in RHOS:
        upper, lower = paths[rho]
        style = STYLES[rho]
        ax.fill_between(
            x, lower, upper,
            color=style["band"], alpha=0.30, linewidth=0.0,
            label=rf"Band $\rho={rho}$",
        )
        ax.plot(
            x, 0.5 * (lower + upper),
            color=style["line"], linewidth=2.0,
            label=rf"Midpoint $\rho={rho}$",
        )

    ax.set_xlabel("Epochs from now", fontsize=FONT_SIZE)
    ax.set_ylabel("Gross APR (%)", fontsize=FONT_SIZE)
    ax.set_xlim(0, N_EPOCHS)
    ax.set_ylim(bottom=0.0)
    ax.tick_params(axis="both", labelsize=FONT_SIZE)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=FONT_SIZE, loc="upper right", ncol=2)
    ax.set_title(
        rf"Gross APR path under alternative $\rho$ ($\tau={TAU}$, $a_0={A0}$)"
        "\n"
        rf"Start: epoch {epoch0}, $T_0={t0/1e9:.2f}$B, $Q_0={q0/1e9:.2f}$B, "
        rf"$F$ fixed at {fees:,.0f} ADA",
        fontsize=FONT_SIZE,
    )

    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Start epoch {epoch0}: T0={t0/1e9:.3f}B, Q0={q0/1e9:.3f}B, F={fees:.0f}")
    for rho in RHOS:
        upper, lower = paths[rho]
        mid0 = 0.5 * (lower[0] + upper[0])
        midN = 0.5 * (lower[-1] + upper[-1])
        print(f"rho={rho}: APR mid n=0 -> {mid0:.3f}%, n={N_EPOCHS} -> {midN:.3f}%")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
