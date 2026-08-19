#!/usr/bin/env python3
"""Fee path required to keep the gross APR constant over many epochs.

Starting conditions (epoch 649 approx.):
    T_0   = 38.8 B ADA   (circulating supply)
    Res_0 =  6.2 B ADA   (reserves)
    F_0   = 23,270 ADA   (fee pot)
    rho   = 0.003

Reserve dynamics:   Res_n = Res_0 (1 - rho)^n
Supply dynamics:    T_n   = (T_0 + Res_0) - Res_n

Constant-APR condition:
    (F_n + rho Res_n) / T_n  =  (F_0 + rho Res_0) / T_0  ≡ c

Fee path:  F_n = c * T_n - rho * Res_n
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "fee_path_constant_apr.png"

RHO = 0.003
T0 = 38.8e9
RES0 = 6.2e9
F0 = 23_270
TOTAL = T0 + RES0  # 45 B ADA

C = (F0 + RHO * RES0) / T0

N_EPOCHS = 1500  # ~20 years
epochs = np.arange(N_EPOCHS + 1)

res_n = RES0 * (1 - RHO) ** epochs
t_n = TOTAL - res_n
f_required = C * t_n - RHO * res_n

FONT_SIZE = 12

fig, ax = plt.subplots(1, 1, figsize=(10, 5), constrained_layout=True)

ax.plot(epochs, f_required / 1e6, color="#1f4e79", linewidth=2,
        label=r"Required fee path $F_n$")
ax.axhline(F0 / 1e6, color="grey", linestyle=":", linewidth=1, alpha=0.6,
           label=rf"Current fees $F_0 = {F0:,}$ ADA")
ax.set_xlabel("Epochs from now", fontsize=FONT_SIZE)
ax.set_ylabel("Required fees (M ADA)", fontsize=FONT_SIZE)
ax.tick_params(axis="both", labelsize=FONT_SIZE)
ax.set_title(
    r"Fee path to maintain APR constant"
    "\n"
    rf"$T_0={T0/1e9:.1f}$B, $\mathrm{{Res}}_0={RES0/1e9:.1f}$B, "
    rf"$F_0={F0:,}$ ADA, $\rho={RHO}$",
    fontsize=FONT_SIZE,
)
ax.legend(fontsize=FONT_SIZE)
ax.grid(alpha=0.25)

fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"Saved: {OUT_PNG}")
print()
print("Sample fee path (ADA):")
for n in [0, 50, 100, 200, 400, 730, 1000, 1460]:
    if n <= N_EPOCHS:
        print(f"  n={n:5d}  ({n/73:.1f} yr):  F={f_required[n]:>14,.0f} ADA  ({f_required[n]/F0:>7.0f}x F_0)")


if __name__ == "__main__":
    pass
