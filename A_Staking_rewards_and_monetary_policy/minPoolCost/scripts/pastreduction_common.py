"""Shared Active-pool loading for the minPoolCost past-reduction epochs.

Canonical pool files: `staking_pools_full_epoch_{426,445,500}_merged.csv`.
Declared $p$ is the certificate active at the epoch.
Live $\\hat p$ is unique-owner `account_history` (`pledged` = `live_pledge`).

Active = complement of Inactive.
Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs.
Flag files: `inactive_pool_flags_epoch_{epoch}_last15.csv` (`in_union==0`).

Pairwise 426→500 and 445→500 plots use the continuing Active intersection.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DIR = Path(__file__).resolve().parent
EPOCHS = (426, 445, 500)

MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.31
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD


def merged_path(epoch: int) -> Path:
    return DIR / f"staking_pools_full_epoch_{epoch}_merged.csv"


def flags_path(epoch: int) -> Path:
    return DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv"


def load_merged(epoch: int) -> pd.DataFrame:
    path = merged_path(epoch)
    if not path.exists():
        raise FileNotFoundError(f"Missing merged snapshot: {path}")
    return pd.read_csv(path)


def load_active(epoch: int) -> pd.DataFrame:
    df = load_merged(epoch)
    flags = pd.read_csv(flags_path(epoch))
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError(f"Missing inactivity flags for some pools at epoch {epoch}")
    return df.loc[df["in_union"] == 0].copy()


def load_continuing_active(*epochs: int) -> dict[int, pd.DataFrame]:
    if len(epochs) < 2:
        raise ValueError("Need at least two epochs")
    frames = {e: load_active(e).set_index("pool_id") for e in epochs}
    common = frames[epochs[0]].index
    for e in epochs[1:]:
        common = common.intersection(frames[e].index)
    return {e: frames[e].loc[common].copy() for e in epochs}
