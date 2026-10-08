#!/usr/bin/env python3
"""
Active-pool snapshot for epochs 228 and 285.

Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in the 15-epoch window
through the target epoch (≈ 3 months).

Universe: staking_pools_full_epoch_{228,285}_merged.csv (already σ>0).
Unmet pledge: merged live_pledge (unique-owner Koios p-hat) < declared pledge.
Block counts: Koios GET /blocks?epoch_no=eq.{e}.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

DIR = Path(__file__).resolve().parent
KOIOS = "https://api.koios.rest/api/v1"
TOKEN_PATH = DIR / ".koios_api_token"
PAGE_SIZE = 1000
WINDOW = 15
EPOCHS = (228, 285)

T_ADA = {
    228: 32.03687470708404e9,
    285: 33.02781783380142e9,
}


def load_token() -> Optional[str]:
    if TOKEN_PATH.exists():
        tok = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if tok:
            return tok
    return None


def fetch_window_blocks(
    session: requests.Session, epoch: int, cache_path: Path
) -> Counter:
    if cache_path.exists():
        df = pd.read_csv(cache_path)
        return Counter(
            {
                str(pid): int(n)
                for pid, n in zip(df["pool_id"], df["blocks_last15"])
            }
        )

    epoch_from = epoch - WINDOW + 1
    counts: Counter = Counter()
    n_blocks = 0
    print(f"Fetching blocks epochs {epoch_from}..{epoch}", flush=True)
    for ep in range(epoch_from, epoch + 1):
        offset = 0
        ep_n = 0
        while True:
            r = session.get(
                f"{KOIOS}/blocks",
                params={
                    "epoch_no": f"eq.{ep}",
                    "select": "pool",
                    "limit": PAGE_SIZE,
                    "offset": offset,
                },
                timeout=90,
            )
            if r.status_code == 429:
                time.sleep(3.0)
                continue
            r.raise_for_status()
            chunk = r.json()
            if not chunk:
                break
            for row in chunk:
                pid = row.get("pool")
                if pid:
                    counts[pid] += 1
            ep_n += len(chunk)
            if len(chunk) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            time.sleep(0.05)
        n_blocks += ep_n
        print(f"  epoch {ep}: {ep_n} blocks", flush=True)

    out = pd.DataFrame(
        {"pool_id": list(counts.keys()), "blocks_last15": list(counts.values())}
    )
    out.to_csv(cache_path, index=False)
    print(f"  total blocks={n_blocks}, pools_with_blocks={len(counts)}", flush=True)
    return counts


def flags_for_epoch(epoch: int, counts: Counter) -> pd.DataFrame:
    df = pd.read_csv(DIR / f"staking_pools_full_epoch_{epoch}_merged.csv")
    sigma = (
        pd.to_numeric(
            df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]),
            errors="coerce",
        ).fillna(0.0)
        / 1e6
    )
    pledged = pd.to_numeric(df["live_pledge"].fillna(df["pledged"]), errors="coerce")
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce")
    window_blocks = df["pool_id"].map(lambda p: int(counts.get(str(p), 0)))

    sigma0 = sigma <= 0
    unmet = pledged.notna() & declared.notna() & (pledged < declared)
    zero_win = window_blocks <= 0
    union = sigma0 | unmet | zero_win

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "ticker": df["pool_name.ticker"],
            "sigma_ada": sigma,
            "sigma0": sigma0.astype(int),
            "unmet_pledge": unmet.astype(int),
            "zero_blocks_last15": zero_win.astype(int),
            "blocks_last15": window_blocks,
            "in_union": union.astype(int),
        }
    )
    out.to_csv(DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv", index=False)
    return out


def main() -> None:
    token = load_token()
    session = requests.Session()
    headers = {
        "accept": "application/json",
        "user-agent": "cardano-parameters-landscape-active-228-285/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    session.headers.update(headers)

    flags: dict[int, pd.DataFrame] = {}
    for epoch in EPOCHS:
        cache = DIR / f"blocks_last15_epochs_koios_epoch_{epoch}.csv"
        counts = fetch_window_blocks(session, epoch, cache)
        flags[epoch] = flags_for_epoch(epoch, counts)

    active = {e: f.loc[f["in_union"] == 0].copy() for e, f in flags.items()}
    ids = {e: set(a["pool_id"]) for e, a in active.items()}
    continuing = ids[228] & ids[285]
    exited = ids[228] - ids[285]

    rows = []
    summary: dict = {}
    for e in EPOCHS:
        f = flags[e]
        a = active[e]
        T = T_ADA[e]
        S = float(a["sigma_ada"].sum())
        n_sigma = int((f["sigma_ada"] > 0).sum())
        summary[e] = {
            "n_universe_sigma_gt_0": n_sigma,
            "n_sigma0": int(f["sigma0"].sum()),
            "n_unmet_pledge": int(f["unmet_pledge"].sum()),
            "n_zero_blocks_last15": int(f["zero_blocks_last15"].sum()),
            "n_inactive_union": int(f["in_union"].sum()),
            "n_active": int(len(a)),
            "S_active_ada": S,
            "T_ada": T,
            "S_over_T": S / T,
            "window": [e - WINDOW + 1, e],
        }
        print(json.dumps({str(e): summary[e]}, indent=2))

    print(
        json.dumps(
            {
                "n_active_228_continuing_to_285": len(continuing),
                "n_active_228_exited_by_285": len(exited),
            },
            indent=2,
        )
    )

    n228, n285 = summary[228]["n_active"], summary[285]["n_active"]
    s228, s285 = summary[228]["S_active_ada"], summary[285]["S_active_ada"]
    t228, t285 = summary[228]["T_ada"], summary[285]["T_ada"]
    md = f"""# Active pools — epochs 228 vs 285

Inactive = $\\sigma=0$ $\\cup$ unmet pledge $\\cup$ zero blocks in the 15 epochs
through the target (214–228 and 271–285). Universe is the merged
$\\sigma>0$ snapshots. Unmet pledge uses unique-owner Koios `live_pledge`
vs declared.

| Quantity | Epoch 228 | Epoch 285 |
| :--- | ---: | ---: |
| $T$ | {t228/1e9:.2f}B ADA | {t285/1e9:.2f}B ADA |
| $S$ (Active) | {s228/1e9:.2f}B ADA | {s285/1e9:.2f}B ADA |
| $S / T$ | {100*s228/t228:.1f}% | {100*s285/t285:.1f}% |
| Active pools | {n228:,} | {n285:,} |
|     — continuing to 285 | {len(continuing):,} | — |
|     — exited by 285 | {len(exited):,} | — |
| $\\sigma_i>0$ (old criterion) | {summary[228]['n_universe_sigma_gt_0']:,} | {summary[285]['n_universe_sigma_gt_0']:,} |
| Inactive of $\\sigma>0$ | {summary[228]['n_inactive_union']:,} | {summary[285]['n_inactive_union']:,} |
|     — unmet pledge | {summary[228]['n_unmet_pledge']:,} | {summary[285]['n_unmet_pledge']:,} |
|     — zero blocks last 15 | {summary[228]['n_zero_blocks_last15']:,} | {summary[285]['n_zero_blocks_last15']:,} |
"""
    out_md = DIR / "active_pools_228_vs_285.md"
    out_md.write_text(md, encoding="utf-8")
    print(md)
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
