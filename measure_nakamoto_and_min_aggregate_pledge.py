#!/usr/bin/env python3
"""
Nakamoto coefficient and min-aggregate pledge for epochs 426 and 500.

Universe: Active pools on the merged snapshots.
Nakamoto coefficient: minimum number of pools (ranked by active_stake desc)
whose aggregate active_stake exceeds 50% of total Active stake.

For that minimal set:
  - declared pledge: certificate active at the epoch
  - active pledge: unique-owner $\\hat p$ (`pledged` = `live_pledge`)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from pastreduction_common import load_active

DIR = Path(__file__).resolve().parent
EPOCHS = (426, 500)
OUT_JSON = DIR / "nakamoto_and_min_aggregate_pledge_426_500.json"
OUT_CSV = DIR / "nakamoto_and_min_aggregate_pledge_426_500.csv"


def lovelace_to_ada(x: float | int) -> float:
    return float(x) / 1e6


def nakamoto_set(stake: pd.Series) -> tuple[int, pd.Index, float, float]:
    s = stake.fillna(0).astype(float).sort_values(ascending=False)
    total = float(s.sum())
    if total <= 0:
        raise ValueError("total stake is zero")
    cum = s.cumsum()
    n = int((cum <= 0.5 * total).sum()) + 1
    ids = s.index[:n]
    agg = float(s.iloc[:n].sum())
    return n, ids, agg, total


def analyze_epoch(epoch: int) -> dict[str, Any]:
    df = load_active(epoch).set_index("pool_id")
    stake = pd.to_numeric(df["active_stake"], errors="coerce")
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce")
    live = pd.to_numeric(df["pledged"], errors="coerce")
    n, ids, agg_stake, total_stake = nakamoto_set(stake)

    declared_vals = declared.loc[ids]
    live_vals = live.loc[ids]
    sum_declared = float(declared_vals.fillna(0).sum())
    sum_active = float(live_vals.fillna(0).sum())
    missing_declared = int(declared_vals.isna().sum())
    missing_live = int(live_vals.isna().sum())

    rows = []
    for rank, pid in enumerate(ids, 1):
        n_owners = df.loc[pid, "n_owners_unique"] if "n_owners_unique" in df.columns else ""
        rows.append(
            {
                "epoch": epoch,
                "rank": rank,
                "pool_id": pid,
                "ticker": df.loc[pid, "pool_name.ticker"]
                if "pool_name.ticker" in df.columns
                else "",
                "active_stake_lovelace": float(stake.loc[pid]),
                "declared_pledge_lovelace": None
                if pd.isna(declared.loc[pid])
                else float(declared.loc[pid]),
                "active_pledge_lovelace": None
                if pd.isna(live.loc[pid])
                else float(live.loc[pid]),
                "n_owners": None if pd.isna(n_owners) else int(n_owners),
            }
        )

    print(
        f"\nEpoch {epoch}: Nakamoto N={n}  share={100 * agg_stake / total_stake:.2f}%",
        flush=True,
    )
    return {
        "epoch": epoch,
        "n_pools_in_snapshot": int(len(df)),
        "universe": "active_merged",
        "nakamoto_coefficient": n,
        "total_active_stake_ada": lovelace_to_ada(total_stake),
        "nakamoto_aggregate_stake_ada": lovelace_to_ada(agg_stake),
        "nakamoto_stake_share": agg_stake / total_stake,
        "min_aggregate_declared_pledge_ada": lovelace_to_ada(sum_declared),
        "min_aggregate_active_pledge_ada": lovelace_to_ada(sum_active),
        "pools_missing_declared_pledge": missing_declared,
        "pools_missing_active_pledge": missing_live,
        "pools": rows,
    }


def main() -> None:
    summaries = []
    all_pool_rows = []
    for epoch in EPOCHS:
        summary = analyze_epoch(epoch)
        summaries.append({k: v for k, v in summary.items() if k != "pools"})
        all_pool_rows.extend(summary["pools"])
        print(
            f"  declared pledge (ADA): {summary['min_aggregate_declared_pledge_ada']:,.2f}"
        )
        print(
            f"  active pledge (ADA):   {summary['min_aggregate_active_pledge_ada']:,.2f}"
        )

    payload = {"summaries": summaries, "nakamoto_pools": all_pool_rows}
    OUT_JSON.write_text(json.dumps(payload, indent=2))
    pd.DataFrame(all_pool_rows).to_csv(OUT_CSV, index=False)

    print("\n=== Summary ===")
    for s in summaries:
        print(
            f"epoch {s['epoch']}: N={s['nakamoto_coefficient']}  "
            f"stake={s['nakamoto_aggregate_stake_ada']/1e9:.3f}B/"
            f"{s['total_active_stake_ada']/1e9:.3f}B "
            f"({100*s['nakamoto_stake_share']:.2f}%)  "
            f"declared_pledge={s['min_aggregate_declared_pledge_ada']:,.0f} ADA  "
            f"active_pledge={s['min_aggregate_active_pledge_ada']:,.0f} ADA"
        )
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
