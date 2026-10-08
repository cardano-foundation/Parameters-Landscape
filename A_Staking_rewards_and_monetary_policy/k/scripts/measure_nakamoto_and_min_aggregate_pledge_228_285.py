#!/usr/bin/env python3
"""
Nakamoto coefficient and min-aggregate pledge for epochs 228 and 285.

  - N = min number of Active pools (active_stake desc) whose aggregate exceeds 50% of S
  - declared pledge from the merged snapshot (CExplorer pool_update.active.pledge)
  - active pledge from the merged unique-owner Koios live_pledge
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

DIR = Path(__file__).resolve().parent
EPOCHS = (228, 285)
OUT_JSON = DIR / "nakamoto_and_min_aggregate_pledge_228_285.json"
OUT_CSV = DIR / "nakamoto_and_min_aggregate_pledge_228_285.csv"
OUT_MD = DIR / "nakamoto_and_min_aggregate_pledge_228_285.md"


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
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}_merged.csv")
    flags = pd.read_csv(DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv")
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    df = df[df["in_union"] == 0].set_index("pool_id")
    stake = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    )
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce")
    active = pd.to_numeric(
        df["live_pledge"].fillna(df["pledged"]), errors="coerce"
    ).fillna(0.0)
    n, ids, agg_stake, total_stake = nakamoto_set(stake)
    pool_ids = list(ids)

    print(f"\nEpoch {epoch}: Nakamoto N={n}  share={100 * agg_stake / total_stake:.2f}%")

    declared_n = declared.loc[list(ids)]
    active_n = active.loc[list(ids)]
    sum_declared = float(declared_n.fillna(0.0).sum())
    sum_active = float(active_n.sum())
    missing_declared = int(declared_n.isna().sum())

    rows = []
    for rank, pid in enumerate(pool_ids, 1):
        n_own = (
            int(df.loc[pid, "n_owners_unique"])
            if "n_owners_unique" in df.columns and pd.notna(df.loc[pid, "n_owners_unique"])
            else None
        )
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
                "active_pledge_lovelace": float(active.loc[pid]),
                "n_owners": n_own,
            }
        )

    return {
        "epoch": epoch,
        "n_pools_in_snapshot": int(len(df)),
        "nakamoto_coefficient": n,
        "total_active_stake_ada": lovelace_to_ada(total_stake),
        "nakamoto_aggregate_stake_ada": lovelace_to_ada(agg_stake),
        "nakamoto_stake_share": agg_stake / total_stake,
        "min_aggregate_declared_pledge_ada": lovelace_to_ada(sum_declared),
        "min_aggregate_active_pledge_ada": lovelace_to_ada(sum_active),
        "pools_missing_declared_pledge": missing_declared,
        "pools": rows,
    }


def fmt_b_ada(x: float) -> str:
    if x >= 1e9:
        return f"{x / 1e9:.2f}B ADA"
    if x >= 1e6:
        return f"{x / 1e6:.1f}M ADA"
    return f"{x:,.0f} ADA"


def write_md(summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# Concentration — Nakamoto coefficient (epochs 228, 285)",
        "",
        "Nakamoto $N$: minimum number of Active pools (ranked by active stake) whose aggregate exceeds 50% of total active stake.",
        "Declared pledge from CExplorer; active pledge from unique-owner Koios `live_pledge` in the merged snapshots.",
        "",
        r"| Epoch | Nakamoto \(N\) | Snapshot pools | Aggregate stake of \(N\) | Total active stake | Share | Min-agg declared pledge | Min-agg active pledge |",
        "|------:|---------------:|---------------:|-------------------------:|-------------------:|------:|------------------------:|----------------------:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['epoch']} | {s['nakamoto_coefficient']} | {s['n_pools_in_snapshot']:,} | "
            f"{fmt_b_ada(s['nakamoto_aggregate_stake_ada'])} | {fmt_b_ada(s['total_active_stake_ada'])} | "
            f"{100 * s['nakamoto_stake_share']:.2f}% | "
            f"{fmt_b_ada(s['min_aggregate_declared_pledge_ada'])} | "
            f"{fmt_b_ada(s['min_aggregate_active_pledge_ada'])} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(OUT_MD.read_text())


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
    write_md(summaries)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
