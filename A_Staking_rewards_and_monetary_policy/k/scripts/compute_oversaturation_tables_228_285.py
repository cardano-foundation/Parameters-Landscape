#!/usr/bin/env python3
"""
Oversaturation snapshot tables for the past k increment (epochs 228, 285).

At epoch 228: report k=150 (pre) and k=500 (post increment).
At epoch 285: report k=500 only.

T from Koios /totals (supply). S from pool stake in CSV.
z0(k)=T/k; E(k)=sum max(sigma_i - z0, 0).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

DIR = Path(__file__).resolve().parent
KOIOS = "https://api.koios.rest/api/v1"
TOKEN_PATH = DIR / ".koios_api_token"


def load_token() -> str | None:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text(encoding="utf-8").strip() or None
    return None


def fetch_T_ada(epoch: int, token: str | None) -> float:
    headers = {"accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.get(f"{KOIOS}/totals", params={"_epoch_no": epoch}, headers=headers, timeout=60)
    r.raise_for_status()
    supply_lov = float(r.json()[0]["supply"])
    return supply_lov / 1e6


def load_sigma_ada(epoch: int) -> np.ndarray:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}_merged.csv")
    stake_lov = df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]).astype(float)
    return (stake_lov / 1e6).fillna(0.0).to_numpy()


def metrics_for_k(sigma: np.ndarray, T: float, S: float, n_active: int, k: int) -> dict[str, Any]:
    z0 = T / k
    over = sigma > z0
    E = float(np.maximum(sigma - z0, 0.0).sum())
    return {
        "k": k,
        "z0_ada": z0,
        "z0_M_ada": z0 / 1e6,
        "oversaturated_pools_count": int(over.sum()),
        "oversaturated_pools_pct_of_active": 100.0 * int(over.sum()) / n_active,
        "E_k_ada": E,
        "E_k_B_ada": E / 1e9,
        "E_k_pct_of_S": 100.0 * E / S,
    }


def fmt_b(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}B"


def main() -> None:
    token = load_token()
    epochs = (228, 285)
    snap: dict[int, dict[str, Any]] = {}
    by_case: dict[str, dict[str, Any]] = {}

    for epoch in epochs:
        T = fetch_T_ada(epoch, token)
        sigma = load_sigma_ada(epoch)
        active = sigma > 0
        n_active = int(active.sum())
        S = float(sigma[active].sum())
        snap[epoch] = {
            "epoch": epoch,
            "T_ada": T,
            "T_B_ada": T / 1e9,
            "S_ada": S,
            "S_B_ada": S / 1e9,
            "S_over_T": S / T,
            "S_over_T_pct": 100.0 * S / T,
            "n_pools_sigma_gt_0": n_active,
            "n_pools_total": int(len(sigma)),
        }
        ks = (150, 500) if epoch == 228 else (500,)
        for k in ks:
            key = f"ep{epoch}_k{k}"
            by_case[key] = metrics_for_k(sigma, T, S, n_active, k)
            by_case[key]["epoch"] = epoch

    # Persist machine-readable
    payload = {"snapshots": snap, "by_case": by_case}
    (DIR / "oversaturation_past_k_228_285.json").write_text(json.dumps(payload, indent=2))

    s228, s285 = snap[228], snap[285]
    c150 = by_case["ep228_k150"]
    c500_228 = by_case["ep228_k500"]
    c500_285 = by_case["ep285_k500"]

    md = f"""# Oversaturation — past $k$ increment (epochs 228, 285)

Source stake: `staking_pools_full_epoch_{{228,285}}_merged.csv` (`epochs.0.data.epoch_stake`, lovelace→ADA).
Supply $T$ from Koios `/totals` (`supply`).

Denote $z_0(k)=T/k$. Aggregate stake above saturation:
$E(k)=\\sum_{{i:\\sigma_i>0}}\\max\\{{\\sigma_i-z_0(k),0\\}}$.

Historically $k=150$ through epoch 228; $k$ rose to $500$ effective epoch 234 (so epoch 285 is at $k=500$).

## Snapshot

| Quantity | Epoch 228 | Epoch 285 |
| :--- | ---: | ---: |
| $T$ | {fmt_b(s228['T_B_ada'])} ADA | {fmt_b(s285['T_B_ada'])} ADA |
| $S$ | {fmt_b(s228['S_B_ada'])} ADA | {fmt_b(s285['S_B_ada'])} ADA |
| $S / T$ | {s228['S_over_T_pct']:.1f}% | {s285['S_over_T_pct']:.1f}% |
| Pools with $\\sigma_i>0$ | {s228['n_pools_sigma_gt_0']:,} | {s285['n_pools_sigma_gt_0']:,} |

## Oversaturation vs $k$

| Quantity | Epoch 228, $k=150$ | Epoch 228, $k=500$ | Epoch 285, $k=500$ |
| :--- | ---: | ---: | ---: |
| $z_0(k)$ (M ADA) | {c150['z0_M_ada']:.2f} | {c500_228['z0_M_ada']:.2f} | {c500_285['z0_M_ada']:.2f} |
| Oversaturated pools (count) | {c150['oversaturated_pools_count']} | {c500_228['oversaturated_pools_count']} | {c500_285['oversaturated_pools_count']} |
| Oversaturated pools (% of pools) | {c150['oversaturated_pools_pct_of_active']:.2f}% | {c500_228['oversaturated_pools_pct_of_active']:.2f}% | {c500_285['oversaturated_pools_pct_of_active']:.2f}% |
| $E(k)$ - Stake above saturation (B ADA) | {c150['E_k_B_ada']:.2f} | {c500_228['E_k_B_ada']:.2f} | {c500_285['E_k_B_ada']:.2f} |
| $E(k)$ (% of $S$) | {c150['E_k_pct_of_S']:.2f}% | {c500_228['E_k_pct_of_S']:.2f}% | {c500_285['E_k_pct_of_S']:.2f}% |
"""
    out_md = DIR / "oversaturation_past_k_228_285.md"
    out_md.write_text(md)
    print(md)
    print(f"Wrote {out_md}")

    pd.DataFrame(
        [
            {
                "Quantity": "T (B ADA)",
                "Epoch 228": s228["T_B_ada"],
                "Epoch 285": s285["T_B_ada"],
            },
            {
                "Quantity": "S (B ADA)",
                "Epoch 228": s228["S_B_ada"],
                "Epoch 285": s285["S_B_ada"],
            },
            {
                "Quantity": "S / T (%)",
                "Epoch 228": s228["S_over_T_pct"],
                "Epoch 285": s285["S_over_T_pct"],
            },
            {
                "Quantity": "Pools with sigma_i>0",
                "Epoch 228": s228["n_pools_sigma_gt_0"],
                "Epoch 285": s285["n_pools_sigma_gt_0"],
            },
        ]
    ).to_csv(DIR / "oversaturation_snapshot_228_285.csv", index=False)

    pd.DataFrame(
        [
            {
                "Quantity": "z0(k) (M ADA)",
                "Epoch 228 k=150": c150["z0_M_ada"],
                "Epoch 228 k=500": c500_228["z0_M_ada"],
                "Epoch 285 k=500": c500_285["z0_M_ada"],
            },
            {
                "Quantity": "Oversaturated pools (count)",
                "Epoch 228 k=150": c150["oversaturated_pools_count"],
                "Epoch 228 k=500": c500_228["oversaturated_pools_count"],
                "Epoch 285 k=500": c500_285["oversaturated_pools_count"],
            },
            {
                "Quantity": "Oversaturated pools (% of pools)",
                "Epoch 228 k=150": c150["oversaturated_pools_pct_of_active"],
                "Epoch 228 k=500": c500_228["oversaturated_pools_pct_of_active"],
                "Epoch 285 k=500": c500_285["oversaturated_pools_pct_of_active"],
            },
            {
                "Quantity": "E(k) - Stake above saturation (B ADA)",
                "Epoch 228 k=150": c150["E_k_B_ada"],
                "Epoch 228 k=500": c500_228["E_k_B_ada"],
                "Epoch 285 k=500": c500_285["E_k_B_ada"],
            },
            {
                "Quantity": "E(k) (% of S)",
                "Epoch 228 k=150": c150["E_k_pct_of_S"],
                "Epoch 228 k=500": c500_228["E_k_pct_of_S"],
                "Epoch 285 k=500": c500_285["E_k_pct_of_S"],
            },
        ]
    ).to_csv(DIR / "oversaturation_vs_k_228_285.csv", index=False)


if __name__ == "__main__":
    main()
