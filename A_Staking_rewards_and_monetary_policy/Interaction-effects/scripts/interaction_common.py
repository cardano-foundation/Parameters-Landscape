"""Shared epoch-644 Active-pool loading for interaction-effect scripts.

Active = complement of Inactive.
Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in the prior 15 epochs
(epochs 630–644). Flag file: inactive_pool_flags_koios_epoch_644_last15.csv
(`in_union==0` is Active).

Pool snapshot: staking_pools_full_epoch_644_merged.csv
(unique-owner active pledge in live_pledge/pledged).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
POOLS_CSV = ROOT / "staking_pools_full_epoch_644_merged.csv"
FLAGS_CSV = ROOT / "inactive_pool_flags_koios_epoch_644_last15.csv"
PARAMS_JSON = ROOT / "f_reward_params_epoch_644.json"


def load_active_pools() -> pd.DataFrame:
    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")
    return df.loc[df["in_union"] == 0].copy()
