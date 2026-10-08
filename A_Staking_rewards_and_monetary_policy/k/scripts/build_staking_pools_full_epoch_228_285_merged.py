#!/usr/bin/env python3
"""
Build staking_pools_full_epoch_{228,285}_merged.csv from the CExplorer spines
plus unique-owner Koios live pledge.

Does not overwrite the CExplorer downloads.

CExplorer pledged at these epochs is declared pledge, not live p-hat.
Owners come from the epoch-583 Koios pool_updates dump (covers every pool
in the 228/285 spines). Live pledge is the unique-owner sum of
account_history at the target epoch, clipped to sigma when sigma>0.

Usage:
  python3 build_staking_pools_full_epoch_228_285_merged.py
  python3 build_staking_pools_full_epoch_228_285_merged.py --resume
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

KOIOS_BASE = "https://api.koios.rest/api/v1"
EPOCHS = (228, 285)
ACCOUNT_BATCH = 50
PAGE_SIZE = 1000

DIR = Path(__file__).resolve().parent
UPDATES_CHECKPOINT = (
    DIR.parent / "Data_epoch583" / ".koios_download_checkpoint.json"
)
PLEDGE_CHECKPOINT = DIR / ".koios_epoch228_285_pledge_checkpoint.json"
OUT_MD = DIR / "staking_pools_full_epoch_228_285_merged.md"


class RateLimiter:
    def __init__(self, requests_per_second: float) -> None:
        self._interval = 1.0 / max(requests_per_second, 0.1)
        self._lock = None
        self._next = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        if now < self._next:
            time.sleep(self._next - now)
        self._next = max(time.monotonic(), self._next) + self._interval


_limiter: Optional[RateLimiter] = None
_session: Optional[requests.Session] = None
_AUTH_TOKEN: Optional[str] = None


def load_koios_token() -> Optional[str]:
    env = os.environ.get("KOIOS_API_TOKEN", "").strip()
    if env:
        return env
    for path in (
        DIR / ".koios_api_token",
        DIR.parent / "Data_Pastreduction_minPoolCost" / ".koios_api_token",
        DIR.parent / "Data_epoch644" / ".koios_api_token",
        DIR.parent / "Data_epoch583" / ".koios_api_token",
    ):
        if path.exists():
            tok = path.read_text(encoding="utf-8").strip()
            if tok:
                return tok
    return None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "cardano-parameters-landscape-228-285-merged/1.0",
        }
        if _AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {_AUTH_TOKEN}"
        s.headers.update(headers)
        _session = s
    return _session


def api_call(
    method: str,
    path: str,
    *,
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
    retries: int = 6,
    timeout: float = 90.0,
) -> Any:
    assert _limiter is not None
    url = f"{KOIOS_BASE}/{path}"
    session = get_session()
    last_err: Exception | None = None
    for i in range(retries):
        _limiter.wait()
        try:
            if method == "GET":
                r = session.get(url, params=params, timeout=timeout)
            else:
                r = session.post(url, json=json_body, timeout=timeout)
            if r.status_code == 429:
                last_err = RuntimeError(f"429 Too Many Requests for {path}")
                time.sleep(min(45.0, 3.0 * (i + 1)))
                continue
            if r.status_code >= 500:
                last_err = RuntimeError(f"HTTP {r.status_code} for {path}")
                time.sleep(min(20.0, 1.5 * (i + 1)))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_err = exc
            if i == retries - 1:
                raise
            time.sleep(min(12.0, 1.2 * (i + 1)))
    raise RuntimeError(f"API call failed for {path}: {last_err}")


def fetch_paginated(path: str, label: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    offset = 0
    while True:
        chunk = api_call(
            "GET",
            path,
            params={"limit": PAGE_SIZE, "offset": offset},
            timeout=90.0,
        )
        if not chunk:
            break
        if not isinstance(chunk, list):
            raise RuntimeError(f"Unexpected {path} payload")
        out.extend(chunk)
        print(
            f"  {label or path} offset={offset} got={len(chunk)} total={len(out)}",
            flush=True,
        )
        if len(chunk) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return out


def chunks(xs: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def to_int(v: Any) -> Optional[int]:
    if v is None or v == "" or (isinstance(v, float) and v != v):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None


def cex_path(epoch: int) -> Path:
    downloaded = DIR / f"staking_pools_full_epoch_{epoch}_downloaded_cexplorer.csv"
    original = DIR / f"staking_pools_full_epoch_{epoch}.csv"
    if downloaded.exists():
        return downloaded
    return original


def merged_path(epoch: int) -> Path:
    return DIR / f"staking_pools_full_epoch_{epoch}_merged.csv"


def flags_path(epoch: int) -> Path:
    return DIR / f"inactive_pool_flags_epoch_{epoch}_last15.csv"


def flags_backup_path(epoch: int) -> Path:
    return DIR / f"inactive_pool_flags_epoch_{epoch}_last15_before_pledge_fix.csv"


def load_updates() -> List[Dict[str, Any]]:
    if UPDATES_CHECKPOINT.exists():
        state = json.loads(UPDATES_CHECKPOINT.read_text(encoding="utf-8"))
        updates = state.get("updates") or []
        if updates:
            print(
                f"Reusing {len(updates)} pool_updates from {UPDATES_CHECKPOINT}",
                flush=True,
            )
            return updates
    print("Downloading pool_updates (583 checkpoint had none)...", flush=True)
    raw = fetch_paginated("pool_updates", label="pool_updates")
    compact = []
    for u in raw:
        compact.append(
            {
                "pool_id_bech32": u.get("pool_id_bech32"),
                "update_type": u.get("update_type"),
                "active_epoch_no": u.get("active_epoch_no"),
                "retiring_epoch": u.get("retiring_epoch"),
                "block_time": u.get("block_time"),
                "pledge": u.get("pledge"),
                "margin": u.get("margin"),
                "fixed_cost": u.get("fixed_cost"),
                "owners": u.get("owners") or [],
            }
        )
    print(f"pool_updates: {len(compact)}", flush=True)
    return compact


def latest_registration_at_epoch(
    rows: List[Dict[str, Any]], epoch: int
) -> Tuple[Optional[Dict[str, Any]], bool]:
    rows_sorted = sorted(
        rows,
        key=lambda u: (
            int(u.get("block_time") or 0),
            int(u.get("active_epoch_no") or u.get("retiring_epoch") or 0),
        ),
    )
    effective: Optional[Dict[str, Any]] = None
    retired = False
    for u in rows_sorted:
        ut = u.get("update_type")
        if ut == "registration":
            ae = to_int(u.get("active_epoch_no"))
            if ae is not None and ae <= epoch:
                effective = u
                retired = False
        elif ut == "deregistration":
            re = to_int(u.get("retiring_epoch"))
            if re is not None and re <= epoch:
                retired = True
    return effective, retired


def unique_owner_pledge(
    pool_id: str,
    owners: List[str],
    owner_hist: Dict[str, List[Dict[str, Any]]],
    epoch: int,
) -> Tuple[Optional[int], bool]:
    total = 0
    any_hit = False
    for addr in dict.fromkeys(owners or []):
        hist = owner_hist.get(addr) or []
        for h in hist:
            if h.get("pool_id") != pool_id:
                continue
            ep = to_int(h.get("epoch_no"))
            if ep is not None and ep != epoch:
                continue
            amt = to_int(h.get("active_stake"))
            if amt is not None:
                total += amt
                any_hit = True
    if not owners:
        return None, False
    return (total if any_hit else 0), any_hit


def fetch_owner_stake_at_epoch(
    owners: List[str], epoch: int
) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    pending = list(dict.fromkeys(owners))
    print(
        f"Fetching account_history for {len(pending)} owners at epoch {epoch}...",
        flush=True,
    )
    done = 0
    for batch in chunks(pending, ACCOUNT_BATCH):
        try:
            rows = api_call(
                "POST",
                "account_history",
                json_body={"_stake_addresses": batch, "_epoch_no": epoch},
                retries=5,
                timeout=90.0,
            )
        except Exception as exc:  # noqa: BLE001
            print(
                f"  account_history batch failed ({exc}); retrying one-by-one",
                flush=True,
            )
            rows = []
            for addr in batch:
                try:
                    one = api_call(
                        "POST",
                        "account_history",
                        json_body={"_stake_addresses": [addr], "_epoch_no": epoch},
                        retries=3,
                        timeout=45.0,
                    )
                    if isinstance(one, list):
                        rows.extend(one)
                except Exception:  # noqa: BLE001
                    continue
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            addr = row.get("stake_address")
            hist = row.get("history") or []
            if addr:
                out[str(addr)] = hist if isinstance(hist, list) else []
        done += len(batch)
        if done % 500 == 0 or done >= len(pending):
            print(f"  owners {done}/{len(pending)}", flush=True)
    return out


def rebuild_flags(epoch: int, merged: pd.DataFrame) -> Tuple[int, int, int]:
    flags_in = flags_path(epoch)
    if not flags_in.exists():
        return -1, -1, -1
    flags = pd.read_csv(flags_in)
    bak = flags_backup_path(epoch)
    if bak.exists():
        old_unmet_map = pd.read_csv(bak).set_index("pool_id")["unmet_pledge"].astype(int)
        old_unmet = flags["pool_id"].map(old_unmet_map).fillna(flags["unmet_pledge"]).astype(int)
    else:
        flags.to_csv(bak, index=False)
        old_unmet = flags["unmet_pledge"].astype(int)

    live = pd.to_numeric(merged["live_pledge"], errors="coerce")
    declared = pd.to_numeric(merged["pool_update.active.pledge"], errors="coerce")
    unmet_new = (live.notna() & declared.notna() & (live < declared)).astype(int)
    fix = merged[["pool_id"]].copy()
    fix["unmet_pledge_new"] = unmet_new.to_numpy()
    flags = flags.merge(fix, on="pool_id", how="left")
    flags["unmet_pledge"] = flags["unmet_pledge_new"].fillna(old_unmet).astype(int)
    flags.drop(columns=["unmet_pledge_new"], inplace=True)
    zero_col = (
        "zero_blocks_last15"
        if "zero_blocks_last15" in flags.columns
        else "zero_blocks_last15_through_644"
    )
    flags["in_union"] = (
        (flags["sigma0"].astype(int) == 1)
        | (flags["unmet_pledge"].astype(int) == 1)
        | (flags[zero_col].astype(int) == 1)
    ).astype(int)
    flags.to_csv(flags_in, index=False)
    n_unmet_old = int(old_unmet.sum())
    n_unmet_new = int(flags["unmet_pledge"].sum())
    n_active = int((flags["in_union"] == 0).sum())
    return n_unmet_old, n_unmet_new, n_active


def merge_epoch(
    epoch: int,
    by_pool: Dict[str, List[Dict[str, Any]]],
    owner_hist: Dict[str, List[Dict[str, Any]]],
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    src = cex_path(epoch)
    if not src.exists():
        raise SystemExit(f"Missing CExplorer spine: {src}")
    df = pd.read_csv(src)
    rows = []
    n_unique = 0
    n_clip = 0
    n_zero = 0
    n_no_owners = 0
    n_changed = 0
    n_retired = 0
    n_dup_owner_rows = 0

    for rec in df.to_dict(orient="records"):
        pid = str(rec["pool_id"])
        effective, retired = latest_registration_at_epoch(by_pool.get(pid) or [], epoch)
        owners = list((effective or {}).get("owners") or [])
        uniq_owners = list(dict.fromkeys(owners))
        if len(owners) != len(uniq_owners):
            n_dup_owner_rows += 1
        if retired:
            n_retired += 1

        cex_pledged = to_int(rec.get("pledged"))
        live, any_hit = unique_owner_pledge(pid, uniq_owners, owner_hist, epoch)
        if not uniq_owners:
            live = None
            source = "no_owners"
            n_no_owners += 1
            n_zero += 1
        elif not any_hit:
            live = None
            source = "zero_or_missing"
            n_zero += 1
        else:
            source = "unique_owner_koios"
            n_unique += 1

        sigma = to_int(rec.get("epochs.0.data.epoch_stake") or rec.get("active_stake")) or 0
        if live is not None and sigma > 0 and live > sigma:
            live = sigma
            source = source + "+clipped_to_sigma"
            n_clip += 1

        if cex_pledged is None or live != cex_pledged:
            n_changed += 1

        out = dict(rec)
        out["pledged"] = live
        out["live_pledge"] = live
        out["pledged_cexplorer"] = "" if cex_pledged is None else cex_pledged
        out["active_pledge_source"] = source
        out["n_owners_listed"] = len(owners)
        out["n_owners_unique"] = len(uniq_owners)
        out["pool_retired_at_epoch"] = int(retired)
        rows.append(out)

    merged = pd.DataFrame(rows)
    preferred = [
        "pool_id",
        "pool_name.name",
        "pool_name.ticker",
        "pool_name.description",
        "active_stake",
        "live_stake",
        "pledged",
        "live_pledge",
        "blocks.epoch",
        "delegators",
        "epochs.0.no",
        "epochs.0.data.epoch_stake",
        "epochs.0.data.delegators",
        "epochs.0.data.block.minted",
        "epochs.0.data.reward.member_lovelace",
        "epochs.0.data.reward.leader_lovelace",
        "pool_update.active.margin",
        "pool_update.active.fixed_cost",
        "pool_update.active.pledge",
        "saturation",
        "pledged_cexplorer",
        "active_pledge_source",
        "n_owners_listed",
        "n_owners_unique",
        "pool_retired_at_epoch",
    ]
    extra = [c for c in merged.columns if c not in preferred]
    merged = merged[[c for c in preferred if c in merged.columns] + extra]
    stats = {
        "n": len(merged),
        "n_unique": n_unique,
        "n_clip": n_clip,
        "n_zero": n_zero,
        "n_no_owners": n_no_owners,
        "n_changed": n_changed,
        "n_retired": n_retired,
        "n_dup_owner_rows": n_dup_owner_rows,
        "n_owners_union": len(
            {
                addr
                for rec in df.to_dict(orient="records")
                for addr in dict.fromkeys(
                    (
                        latest_registration_at_epoch(
                            by_pool.get(str(rec["pool_id"])) or [], epoch
                        )[0]
                        or {}
                    ).get("owners")
                    or []
                )
            }
        ),
    }
    return merged, stats


def write_codebook(all_stats: Dict[int, Dict[str, int]], flag_stats: Dict[int, Tuple[int, int, int]]) -> None:
    lines = [
        "# Epochs 228 and 285 merged pool snapshots",
        "",
        "These are the **canonical** pool files for plots, tables, and scripts",
        "in `Data_PastIncrement_k`. CExplorer is the spine; Koios supplies",
        "unique-owner live pledge (p-hat) at each epoch.",
        "",
        "CSVs:",
        "",
        "- [`staking_pools_full_epoch_228_merged.csv`](staking_pools_full_epoch_228_merged.csv)",
        "- [`staking_pools_full_epoch_285_merged.csv`](staking_pools_full_epoch_285_merged.csv)",
        "",
        "## Source files (not overwritten)",
        "",
        "| File | What it is |",
        "|---|---|",
        "| `staking_pools_full_epoch_228.csv` / `_285.csv` | CExplorer extracts (spine) |",
        "| `Data_epoch583/.koios_download_checkpoint.json` | Full `pool_updates` (owners, declared, retirements) |",
        "| `.koios_epoch228_285_pledge_checkpoint.json` | `account_history` at 228 and 285 |",
        "",
        "## What was wrong in the CExplorer extracts",
        "",
        "At epochs 228 and 285, CExplorer `pledged` equals **declared** pledge",
        "(`pool_update.active.pledge`) on every row. `live_pledge` is empty.",
        "That file cannot see unmet pledge or over-pledge, so operator-reward",
        "formulas that need p-hat were using declared $p$ as a stand-in.",
        "",
        "This is a different problem from epoch 644 (there Koios double-counted",
        "repeated owner addresses). Here the Koios owner lists still contain",
        "duplicates; the merge **uniquifies** owners before summing.",
        "",
        "## How the merged columns are built",
        "",
        "Universe: **CExplorer rows** (stake, declared pledge, margin, fixed cost,",
        "blocks, delegators, realized rewards).",
        "",
        "| Column | Rule |",
        "|---|---|",
        "| `live_pledge` and `pledged` | Same value. Unique-owner Koios `account_history` at the epoch, matching `pool_id`; clip to $\\sigma$ if $\\sigma>0$. Empty if owner history is missing (not treated as unmet). No CExplorer fallback (that column is declared, not live). |",
        "| `pool_update.active.pledge` | Unchanged CExplorer declared pledge |",
        "| `pledged_cexplorer` | Audit copy of the CExplorer `pledged` column |",
        "| `active_pledge_source` | `unique_owner_koios`, `zero_or_missing`, `no_owners`; `+clipped_to_sigma` if clipped |",
        "| `n_owners_listed` / `n_owners_unique` | Owner-array length before/after uniquify |",
        "| `pool_retired_at_epoch` | 1 if Koios last update by that epoch is a deregistration |",
        "",
        "Scripts may read either `pledged` or `live_pledge`; both are the corrected",
        "active pledge (p-hat).",
        "",
        "## Counts from this build",
        "",
    ]
    for epoch in EPOCHS:
        s = all_stats[epoch]
        u_old, u_new, n_active = flag_stats[epoch]
        lines.extend(
            [
                f"### Epoch {epoch}",
                "",
                f"- Pools in merged file: **{s['n']}**",
                f"- Active pledge from unique-owner Koios: **{s['n_unique']}**",
                f"- Zero/missing live pledge: **{s['n_zero']}**",
                f"- No owners in updates: **{s['n_no_owners']}**",
                f"- Clipped to σ: **{s['n_clip']}**",
                f"- Pledge value changed vs CExplorer `pledged`: **{s['n_changed']}**",
                f"- Pools with duplicate owner listings: **{s['n_dup_owner_rows']}**",
                f"- Unique owner addresses: **{s['n_owners_union']}**",
                f"- Koios-retired by epoch (still in CExplorer spine): **{s['n_retired']}**",
                f"- Unmet-pledge flags before → after: **{u_old} → {u_new}**",
                f"- Active pools (`in_union=0`) after flag rebuild: **{n_active}**",
                "",
            ]
        )
    lines.extend(
        [
            "Last-15 inactivity flags: `sigma0` and `zero_blocks_last15` are",
            "unchanged (they do not use pledge). `unmet_pledge` and `in_union`",
            "were recomputed. Previous flags files are",
            "`inactive_pool_flags_epoch_{228,285}_last15_before_pledge_fix.csv`.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global _limiter, _AUTH_TOKEN

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rps", type=float, default=10.0)
    args = parser.parse_args()

    _AUTH_TOKEN = load_koios_token()
    _limiter = RateLimiter(args.rps)
    print(
        f"Koios auth: {'Bearer token' if _AUTH_TOKEN else 'public (unauthenticated)'}",
        flush=True,
    )

    updates = load_updates()
    by_pool: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for u in updates:
        pid = u.get("pool_id_bech32")
        if pid:
            by_pool[str(pid)].append(u)

    pledge_state: Dict[str, Any] = {}
    if args.resume and PLEDGE_CHECKPOINT.exists():
        pledge_state = json.loads(PLEDGE_CHECKPOINT.read_text(encoding="utf-8"))
        print(
            f"Resuming pledge checkpoint: "
            f"228={len(pledge_state.get('owner_hist_228') or {})} "
            f"285={len(pledge_state.get('owner_hist_285') or {})}",
            flush=True,
        )

    all_stats: Dict[int, Dict[str, int]] = {}
    flag_stats: Dict[int, Tuple[int, int, int]] = {}

    for epoch in EPOCHS:
        src = cex_path(epoch)
        df = pd.read_csv(src)
        owners: List[str] = []
        missing_updates = 0
        for pid in df["pool_id"].astype(str):
            effective, _retired = latest_registration_at_epoch(by_pool.get(pid) or [], epoch)
            if effective is None:
                missing_updates += 1
            owners.extend(list(dict.fromkeys((effective or {}).get("owners") or [])))
        print(
            f"Epoch {epoch}: spine={src.name} n={len(df)} "
            f"unique_owners={len(set(owners))} missing_updates={missing_updates}",
            flush=True,
        )

        key = f"owner_hist_{epoch}"
        owner_hist = pledge_state.get(key)
        if not owner_hist:
            owner_hist = fetch_owner_stake_at_epoch(owners, epoch)
            pledge_state[key] = owner_hist
            PLEDGE_CHECKPOINT.write_text(json.dumps(pledge_state), encoding="utf-8")
            print(f"Wrote {PLEDGE_CHECKPOINT} ({key} n={len(owner_hist)})", flush=True)
        else:
            print(f"Using cached {key} n={len(owner_hist)}", flush=True)

        merged, stats = merge_epoch(epoch, by_pool, owner_hist)
        out = merged_path(epoch)
        merged.to_csv(out, index=False)
        print(
            f"Wrote {out} n={stats['n']} unique={stats['n_unique']} "
            f"zero={stats['n_zero']} clip={stats['n_clip']} "
            f"changed_vs_cex={stats['n_changed']}",
            flush=True,
        )
        flag_stats[epoch] = rebuild_flags(epoch, merged)
        u_old, u_new, n_active = flag_stats[epoch]
        print(
            f"  flags unmet {u_old} -> {u_new}; Active n={n_active}",
            flush=True,
        )
        all_stats[epoch] = stats

    write_codebook(all_stats, flag_stats)
    print(f"Wrote {OUT_MD}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
