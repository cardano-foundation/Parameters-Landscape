"""Shared epoch-644 Active-pool loading for minPoolCost scripts.

Active = complement of Inactive.
Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs
(epochs 630–644). Flag file: inactive_pool_flags_koios_epoch_644_last15.csv
(`in_union==0` is Active).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
POOLS_CSV = ROOT / "staking_pools_full_epoch_644_merged.csv"
FLAGS_CSV = ROOT / "inactive_pool_flags_koios_epoch_644_last15.csv"
PARAMS_JSON = ROOT / "f_reward_params_epoch_644.json"

MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD


def load_active_pools() -> pd.DataFrame:
    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")
    return df.loc[df["in_union"] == 0].copy()


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    pledge_share = np.clip(
        np.divide(
            active_pledge,
            sigma,
            out=np.zeros_like(active_pledge),
            where=sigma > 0,
        ),
        0.0,
        1.0,
    )
    operator_share = margin + (1.0 - margin) * pledge_share
    profitable = fixed_cost + (f - fixed_cost) * operator_share
    return np.where(f > fixed_cost, profitable, f)
