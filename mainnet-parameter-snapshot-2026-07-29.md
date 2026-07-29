# Mainnet Parameter Snapshot — 2026-07-29

## Snapshot metadata
- Date (UTC): 2026-07-29
- Network: Cardano mainnet
- Source epoch: 646
- Era: Conway
- Snapshot block: 2140825fb204667a231869422169b823281e58020d1e3aeed73816b6d95e2660
- Snapshot slot: 193749299
- Data sources (ledger-derived API):
  - https://api.koios.rest/api/v1/tip
  - https://api.koios.rest/api/v1/epoch_params?_epoch_no=646
  - https://api.koios.rest/api/v1/totals
  - https://api.koios.rest/api/v1/epoch_info?_epoch_no=646

## Raw values (lovelace unless noted)
- total_supply (T): 38783811807088789
- active_stake (S): 21399489281177386
- reserves: 6216188192911211
- epoch_fees (epoch 646): 2773242221
- optimal_pool_count (k): 500
- influence (a0): 0.3
- min_pool_cost: 170000000
- treasury_growth_rate (tau): 0.2
- monetary_expand_rate (rho): 0.003

## Derived values used in tables
- T: 38,783,811,807.09 ADA
- S: 21,399,489,281.18 ADA
- S/T: 55.18%
- z0: 1/k = 1/500 = 0.002
- c_min: 170 ADA
- tau: 20%
- rho: 0.3%

### Reward pot approximation used in this repository
Using the simplified expression already used in `Parameter-Landscape.md`:

R = (1 - tau) * (fees + rho * reserves)

With epoch 646 values:
- R = 14,921,070.26 ADA

Note: This approximation excludes non-refundable deposits and uses the same modeling choice as the current repository formulas.
