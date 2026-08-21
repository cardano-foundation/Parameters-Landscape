#!/usr/bin/env python3
"""Iso-reward curve for F_t = 0: rho(tau) that keeps R_t = R_bar constant.

With F_t = 0 and eta_t = 1:
    R_bar = (1 - tau_0) * rho_0 * Q_t
    rho(tau) = R_bar / ((1 - tau) * Q_t)

Current point: tau_0 = 0.2, rho_0 = 0.003, Q_t = 6.2B ADA.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "iso_reward_curve_Ft0.png"

FONT_SIZE = 12
Q_T = 6.2e9
TAU0 = 0.2
RHO0 = 0.003
ETA = 1.0
F_T = 0.0

R_BAR = (1.0 - TAU0) * RHO0 * min(ETA, 1.0) * Q_T

tau = np.linspace(0.0, 0.80, 400)
rho = (R_BAR / (1.0 - tau) - F_T) / (min(ETA, 1.0) * Q_T)

tau_pct = tau * 100.0
rho_pct = rho * 100.0

fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)

# Regions: above curve => R > R_bar; below curve => R < R_bar
y_max = float(rho_pct.max()) * 1.05
y_min = 0.0
ax.fill_between(tau_pct, rho_pct, y_max, color="#16a34a", alpha=0.18, linewidth=0.0, zorder=0)
ax.fill_between(tau_pct, y_min, rho_pct, color="#dc2626", alpha=0.18, linewidth=0.0, zorder=0)

ax.plot(tau_pct, rho_pct, color="#1f4e79", linewidth=2.2, zorder=2, label=r"Iso-reward curve $\rho(\tau)$")
ax.scatter(
    [TAU0 * 100.0],
    [RHO0 * 100.0],
    color="#111111",
    s=55,
    zorder=3,
    label=rf"Current: $\tau={100*TAU0:.0f}\%$, $\rho={100*RHO0:.1f}\%$",
)
ax.axvline(TAU0 * 100.0, color="0.55", linestyle=":", linewidth=1.0, zorder=1)
ax.axhline(RHO0 * 100.0, color="0.55", linestyle=":", linewidth=1.0, zorder=1)

# Center labels in each region
ax.text(
    0.32, 0.78, r"$R_t > \bar R$",
    transform=ax.transAxes, ha="center", va="center",
    fontsize=FONT_SIZE + 1, color="#166534", fontweight="bold",
)
ax.text(
    0.70, 0.28, r"$R_t < \bar R$",
    transform=ax.transAxes, ha="center", va="center",
    fontsize=FONT_SIZE + 1, color="#991b1b", fontweight="bold",
)

ax.set_xlim(tau_pct.min(), tau_pct.max())
ax.set_ylim(y_min, y_max)
ax.set_xlabel(r"Treasury share $\tau$ (%)", fontsize=FONT_SIZE)
ax.set_ylabel(r"Reserve decay $\rho$ (%)", fontsize=FONT_SIZE)
ax.set_title(
    r"Iso-reward curve ($F_t=0$, $\bar R$ fixed at current $R_t$)"
    "\n"
    rf"$Q_t={Q_T/1e9:.1f}$B ADA, $\eta_t=1$, $\bar R={R_BAR/1e6:.2f}$M ADA/epoch",
    fontsize=FONT_SIZE,
)
ax.tick_params(axis="both", labelsize=FONT_SIZE)
ax.grid(alpha=0.25)
ax.legend(fontsize=FONT_SIZE, loc="upper left")

fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"R_bar = {R_BAR:,.0f} ADA/epoch")
print(f"Saved: {OUT_PNG}")
