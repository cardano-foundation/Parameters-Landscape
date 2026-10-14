#!/usr/bin/env python3
"""
Active-pool flags for the minPoolCost past-reduction epochs 426, 445, 500.

Inactive = σ=0 ∪ unmet pledge ∪ zero blocks in the 15-epoch window
through the target epoch (≈ 3 months).

Block counts: Koios GET /blocks?epoch_no=eq.{e}.
  426: epochs 412–426
  445: epochs 431–445
  500: epochs 486–500

Universe: staking_pools_full_epoch_{426,445,500}_merged.csv.
Declared $p$: certificate active at the epoch.
Live $\\hat p$: unique-owner account_history (pledged = live_pledge).
Unmet pledge: live_pledge < declared, only when live_pledge is observed.

Does not overwrite the original epoch CSVs.

Usage:
  python3 count_active_pools_426_445_500.py
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
EPOCHS = (426, 445, 500)


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
        print(f"  cache hit {cache_path.name} ({len(df)} pools with blocks)", flush=True)
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
    pledged = pd.to_numeric(df["live_pledge"], errors="coerce")
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce")
    window_blocks = df["pool_id"].map(lambda p: int(counts.get(str(p), 0)))
    blocks_epoch = pd.to_numeric(
        df["epochs.0.data.block.minted"].fillna(df["blocks.epoch"]),
        errors="coerce",
    ).fillna(0)

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
            "blocks_this_epoch": blocks_epoch.astype(int),
            "in_union": union.astype(int),
        }
    )
    out_path = DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path}", flush=True)
    return out


def reducer_stats(ids: set[str], e0: int, e1: int) -> dict:
    a = pd.read_csv(DIR / f"staking_pools_full_epoch_{e0}_merged.csv").set_index("pool_id")
    b = pd.read_csv(DIR / f"staking_pools_full_epoch_{e1}_merged.csv").set_index("pool_id")
    ids = ids & set(a.index) & set(b.index)
    fa = pd.to_numeric(a.loc[list(ids), "pool_update.active.fixed_cost"], errors="coerce")
    fb = pd.to_numeric(b.loc[list(ids), "pool_update.active.fixed_cost"], errors="coerce")
    sa = pd.to_numeric(
        a.loc[list(ids), "epochs.0.data.epoch_stake"].fillna(a.loc[list(ids), "active_stake"]),
        errors="coerce",
    )
    sb = pd.to_numeric(
        b.loc[list(ids), "epochs.0.data.epoch_stake"].fillna(b.loc[list(ids), "active_stake"]),
        errors="coerce",
    )
    ok = fa.notna() & fb.notna() & sa.notna() & sb.notna()
    fa, fb, sa, sb = fa[ok], fb[ok], sa[ok], sb[ok]
    down = fb < fa
    n = int(ok.sum())
    nd = int(down.sum())
    gain = int((down & (sb > sa)).sum())
    lose = int((down & (sb < sa)).sum())
    return {
        "n": n,
        "n_reducers": nd,
        "pct_reducers": 100.0 * nd / n if n else float("nan"),
        "n_gain": gain,
        "n_lose": lose,
        "pct_gain_among_reducers": 100.0 * gain / nd if nd else float("nan"),
        "n_340_to_170": int(((fa == 340e6) & (fb == 170e6)).sum()),
    }


def main() -> None:
    token = load_token()
    session = requests.Session()
    headers = {
        "accept": "application/json",
        "user-agent": "cardano-parameters-landscape-active-426-500/1.0",
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
    cont_445 = ids[426] & ids[445]
    cont_500 = ids[426] & ids[500]
    cont_all = ids[426] & ids[445] & ids[500]
    exited_445 = ids[426] - ids[445]
    exited_500 = ids[426] - ids[500]

    summary: dict = {"window": WINDOW, "epochs": {}}
    for e in EPOCHS:
        f = flags[e]
        a = active[e]
        summary["epochs"][e] = {
            "n_universe": int(len(f)),
            "n_sigma0": int(f["sigma0"].sum()),
            "n_unmet_pledge": int(f["unmet_pledge"].sum()),
            "n_zero_blocks_last15": int(f["zero_blocks_last15"].sum()),
            "n_inactive_union": int(f["in_union"].sum()),
            "n_active": int(len(a)),
            "S_active_ada": float(a["sigma_ada"].sum()),
            "window": [e - WINDOW + 1, e],
        }
        print(json.dumps({str(e): summary["epochs"][e]}, indent=2), flush=True)

    summary["continuing"] = {
        "n_active_426": len(ids[426]),
        "n_active_426_and_445": len(cont_445),
        "n_active_426_and_500": len(cont_500),
        "n_active_426_and_445_and_500": len(cont_all),
        "n_active_426_not_active_445": len(exited_445),
        "n_active_426_not_active_500": len(exited_500),
    }
    summary["cost_reducers_426_to_500"] = {
        "all_common_pools": reducer_stats(
            set(pd.read_csv(DIR / "staking_pools_full_epoch_426_merged.csv")["pool_id"])
            & set(pd.read_csv(DIR / "staking_pools_full_epoch_500_merged.csv")["pool_id"]),
            426,
            500,
        ),
        "active_426_and_500": reducer_stats(cont_500, 426, 500),
        "active_throughout_426_445_500": reducer_stats(cont_all, 426, 500),
    }
    print(json.dumps(summary["continuing"], indent=2), flush=True)
    print(json.dumps(summary["cost_reducers_426_to_500"], indent=2), flush=True)

    out_json = DIR / "active_pools_426_445_500.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    s = summary["epochs"]
    c = summary["continuing"]
    r_all = summary["cost_reducers_426_to_500"]["all_common_pools"]
    r_act = summary["cost_reducers_426_to_500"]["active_426_and_500"]
    r_thr = summary["cost_reducers_426_to_500"]["active_throughout_426_445_500"]
    md = f"""# Active pools — epochs 426, 445, 500

Inactive = $\\sigma=0$ $\\cup$ unmet pledge $\\cup$ zero blocks in the 15 epochs
through the target (412–426, 431–445, 486–500). Universe is
`staking_pools_full_epoch_{{426,445,500}}_merged.csv`. Unmet pledge uses
unique-owner `live_pledge` vs the certificate active at the epoch. Empty
live pledge is not treated as unmet.

| Quantity | Epoch 426 | Epoch 445 | Epoch 500 |
| :--- | ---: | ---: | ---: |
| Universe | {s[426]['n_universe']:,} | {s[445]['n_universe']:,} | {s[500]['n_universe']:,} |
| Active | {s[426]['n_active']:,} | {s[445]['n_active']:,} | {s[500]['n_active']:,} |
| Inactive | {s[426]['n_inactive_union']:,} | {s[445]['n_inactive_union']:,} | {s[500]['n_inactive_union']:,} |
| — $\\sigma=0$ | {s[426]['n_sigma0']:,} | {s[445]['n_sigma0']:,} | {s[500]['n_sigma0']:,} |
| — unmet pledge | {s[426]['n_unmet_pledge']:,} | {s[445]['n_unmet_pledge']:,} | {s[500]['n_unmet_pledge']:,} |
| — zero blocks last 15 | {s[426]['n_zero_blocks_last15']:,} | {s[445]['n_zero_blocks_last15']:,} | {s[500]['n_zero_blocks_last15']:,} |
| $S$ (Active, ADA) | {s[426]['S_active_ada']/1e9:.2f}B | {s[445]['S_active_ada']/1e9:.2f}B | {s[500]['S_active_ada']/1e9:.2f}B |

Starting from Active pools at 426 ($n={c['n_active_426']:,}$):

| Continuing set | Pools |
| :--- | ---: |
| Still Active at 445 | {c['n_active_426_and_445']:,} |
| Still Active at 500 | {c['n_active_426_and_500']:,} |
| Active at 426, 445, and 500 | {c['n_active_426_and_445_and_500']:,} |
| Active at 426, not Active at 445 | {c['n_active_426_not_active_445']:,} |
| Active at 426, not Active at 500 | {c['n_active_426_not_active_500']:,} |

Fixed-cost reducers, 426$\\to$500:

| Sample | $n$ | Reducers | Share | Gain stake | Lose stake | $340\\to 170$ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| All common pools | {r_all['n']:,} | {r_all['n_reducers']:,} | {r_all['pct_reducers']:.1f}% | {r_all['n_gain']:,} | {r_all['n_lose']:,} | {r_all['n_340_to_170']:,} |
| Active 426 $\\cap$ Active 500 | {r_act['n']:,} | {r_act['n_reducers']:,} | {r_act['pct_reducers']:.1f}% | {r_act['n_gain']:,} | {r_act['n_lose']:,} | {r_act['n_340_to_170']:,} |
| Active throughout 426–500 | {r_thr['n']:,} | {r_thr['n_reducers']:,} | {r_thr['pct_reducers']:.1f}% | {r_thr['n_gain']:,} | {r_thr['n_lose']:,} | {r_thr['n_340_to_170']:,} |

Among reducers, share that gained stake: all common {r_all['pct_gain_among_reducers']:.1f}%; Active 426$\\cap$500 {r_act['pct_gain_among_reducers']:.1f}%; throughout {r_thr['pct_gain_among_reducers']:.1f}%.
"""
    out_md = DIR / "active_pools_426_445_500.md"
    out_md.write_text(md, encoding="utf-8")
    print(md)
    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()
