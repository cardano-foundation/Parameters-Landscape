# Epochs 426, 445, and 500 merged pool snapshots

These are the **canonical** pool files for plots, tables, and scripts
in `Data_Pastreduction_minPoolCost`. Koios `pool_history` is the spine;
Koios `pool_updates` supplies the certificate active at each epoch;
Koios `account_history` supplies unique-owner live pledge ($\hat p$).

CSVs:

- [`staking_pools_full_epoch_426_merged.csv`](staking_pools_full_epoch_426_merged.csv)
- [`staking_pools_full_epoch_445_merged.csv`](staking_pools_full_epoch_445_merged.csv)
- [`staking_pools_full_epoch_500_merged.csv`](staking_pools_full_epoch_500_merged.csv)

## Source files (not overwritten)

| File | What it is |
|---|---|
| `staking_pools_full_epoch_{426,445,500}.csv` | Original Koios `pool_history` extracts (spine) |
| `Data_epoch583/.koios_download_checkpoint.json` | Full `pool_updates` (owners, declared, retirements) |
| `.koios_epoch426_445_500_pledge_checkpoint.json` | `account_history` at 426, 445, and 500 |

## What was wrong in the original extracts

The download script stamped the **current** `pool_list.pledge` into both
`pledged` and `pool_update.active.pledge`. Those two columns were
identical, `live_pledge` was empty, and the same declared value appeared
at 426, 445, and 500 for every pool that had a stamp. That is a later
certificate, not the one active at the historical epoch, and it is not
$\hat p$.

Owner lists in `pool_updates` can repeat the same stake address. The
merge uniquifies owners with `dict.fromkeys` before summing, then clips
$\hat p$ to $\sigma$ if $\sigma>0$.

## How the merged columns are built

Universe: **Koios `pool_history` rows** (stake, margin, fixed cost,
blocks, delegators, realized rewards). Pledge columns are replaced.

| Column | Rule |
|---|---|
| `live_pledge` and `pledged` | Same value. Unique-owner Koios `account_history` at the epoch, matching `pool_id`; clip to $\sigma$ if $\sigma>0$. Empty if owner history is missing (not treated as unmet). |
| `pool_update.active.pledge` | Declared $p$ from the Koios certificate active at the epoch (latest registration with `active_epoch_no` $\le t$). Falls back to the original stamp only if no certificate is found. |
| `pledged_koios_stamp` / `declared_pledge_koios_stamp` | Audit copies of the original `pledged` and `pool_update.active.pledge` stamps |
| `active_pledge_source` | `unique_owner_koios`, `zero_or_missing`, `no_owners`; `+clipped_to_sigma` if clipped |
| `declared_pledge_source` | `certificate` or `pool_list_stamp` |
| `n_owners_listed` / `n_owners_unique` | Owner-array length before/after uniquify |
| `pool_retired_at_epoch` | 1 if Koios last update by that epoch is a deregistration |

Scripts may read either `pledged` or `live_pledge`; both are the corrected
active pledge ($\hat p$). Use `pool_update.active.pledge` for declared $p$.

## Counts from this build

### Epoch 426

- Pools in merged file: **2931**
- Declared $p$ from certificate: **2931** (missing cert: 0)
- Declared $p$ changed vs pool_list stamp: **1043**
- Active pledge from unique-owner Koios: **2730**
- Zero/missing live pledge: **201**
- No owners in updates: **0**
- Clipped to σ: **0**
- Live pledge changed vs original `pledged` stamp: **2903**
- Pools with duplicate owner listings: **1464**
- Unique owner addresses: **3609**
- Koios-retired by epoch (still in spine): **11**
- Unmet-pledge flags before → after: **0 → 267**
- Active pools (`in_union=0`) after flag rebuild: **1516**

### Epoch 445

- Pools in merged file: **2886**
- Declared $p$ from certificate: **2886** (missing cert: 0)
- Declared $p$ changed vs pool_list stamp: **1022**
- Active pledge from unique-owner Koios: **2695**
- Zero/missing live pledge: **191**
- No owners in updates: **0**
- Clipped to σ: **0**
- Live pledge changed vs original `pledged` stamp: **2861**
- Pools with duplicate owner listings: **1451**
- Unique owner addresses: **3559**
- Koios-retired by epoch (still in spine): **7**
- Unmet-pledge flags before → after: **0 → 258**
- Active pools (`in_union=0`) after flag rebuild: **1469**

### Epoch 500

- Pools in merged file: **2884**
- Declared $p$ from certificate: **2884** (missing cert: 0)
- Declared $p$ changed vs pool_list stamp: **969**
- Active pledge from unique-owner Koios: **2659**
- Zero/missing live pledge: **225**
- No owners in updates: **0**
- Clipped to σ: **0**
- Live pledge changed vs original `pledged` stamp: **2864**
- Pools with duplicate owner listings: **1494**
- Unique owner addresses: **3501**
- Koios-retired by epoch (still in spine): **6**
- Unmet-pledge flags before → after: **0 → 285**
- Active pools (`in_union=0`) after flag rebuild: **1434**

## Continuing Active after pledge fix

- Active 426 ∩ 445: **1360**
- Active 426 ∩ 500: **1251**
- Active throughout 426–445–500: **1226**

Last-15 inactivity flags: `sigma0` and `zero_blocks_last15` are
unchanged (they do not use pledge). `unmet_pledge` and `in_union`
were recomputed. Previous flags files are
`inactive_pool_flags_epoch_{426,445,500}_last15_before_pledge_fix.csv`.
