# Summary

This file is a short guide to what this repository is about. It uses only the
material already present in this repo.

## What This Repo Is About

The repository studies Cardano's staking reward and delegation mechanism. Its
main question is whether the incentive system that was designed for Shelley is
still producing the intended game on mainnet: enough independent operators,
meaningful pledge, active delegator oversight, sustainable rewards, and a path
from reserve-funded bootstrapping to fee-funded self-sufficiency.

The repo is organized as a sequence:

1. [`reward-system-spec/the-intended-game/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/the-intended-game/README.md) explains the intended mechanism in plain language: transaction submitters fund the game, operators commit infrastructure and pledge, and delegators allocate stake and discipline operators.
2. [`reward-system-spec/diagnostic/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/diagnostic/README.md) and [`reward-system-spec/diagnostic/findings.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/diagnostic/findings.md) compare that intended game with mainnet observations.
3. [`reward-system-spec/generated-website/problem-statements.html`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/generated-website/problem-statements.html) turns the observations into induced problems.
4. [`reward-system-spec/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/README.md) proposes a sequence of solution directions.
5. [`reward-system-spec/solution-evaluation/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/solution-evaluation/README.md) evaluates existing CIPs against the induced problems.
6. [`reward-system-spec/implementation-scope/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/implementation-scope/README.md) estimates what the first recommended V2 reward reform would take to build.

The core reward-envelope framing used throughout the repo is:

```text
E(nu, pi) = lambda_size * nu + lambda_pledge * A(nu, pi)
```

where `nu` is normalized pool size, `pi` is pledge ratio, and `A(nu, pi)` is
the pledge-bonus function. The repo argues that much of the current incentive
failure comes from the shape and weight of this reward surface.

At the epoch-pot level, the repo describes the system as reserve-heavy:

```text
Pot_epoch = transaction_fees + non_refundable_deposits + eta * rho * reserve
PoolsPot  = (1 - tau) * Pot_epoch
Treasury  = tau * Pot_epoch
```

Here `rho` is monetary expansion, `tau` is the treasury cut, and `eta` reflects
block-production performance.

## Main Observations

| Area | What the repo observes |
| --- | --- |
| Reserve funding | Rewards are still funded almost entirely by monetary expansion from the reserve, not transaction fees. The reserve has crossed its half-life and reward pressure is expected to increase as it declines. |
| Fees | Transaction fees contribute only a tiny share of the epoch pot. The repo says fee revenue would need to grow by roughly two orders of magnitude to replace reserve funding. |
| Pledge | Pledge is intended to be the operator commitment signal, but the pledge reward is economically weak. The diagnostic says pledge yield is below passive delegation and most of the pledge-bonus budget returns unused. |
| Pool distribution | The pool landscape is stratified. Many registered pools are below reliable block-production or viability thresholds, while only a small group is near saturation. |
| SPO viability | The repo finds that many small or single-pool operators cannot earn a competitive operator income, even if they are productive. |
| Delegator yield | Delegator yield has fallen from earlier Shelley levels and closely tracks reserve depletion. The repo treats this as a structural clock, not a temporary fluctuation. |
| Delegator behavior | Delegation does not appear to move mainly on yield. The repo says capital follows visibility, wallet integration, brand, and inertia more than small yield differences. |
| Concentration | Multi-pool operators and large delegators control a large share of productive stake. The repo distinguishes pool-level decentralization from entity-level control. |
| Non-participation | A large amount of ADA is outside delegation. The repo says most of it is not easy to reach with ordinary reward tweaks because it sits in enterprise addresses, scripts, custody, or dormant wallets. |
| Macro layer | ADA/fiat volatility changes real operator income, delegator attractiveness, and transaction affordability, but the current reward mechanism does not react to price observations. |

## Main Problems and Reasons Given

| Problem | Reason given in the repo | Why it matters |
| --- | --- | --- |
| Long-term reward funding is not sustainable on the current path. | The epoch pot is mostly reserve-funded, while the reserve is finite and fees are not yet large enough to replace it. Parameters `rho` and `tau` have also been static since Shelley in the repo's account. | If fees do not grow or the mechanism is not recalibrated, the reward budget continues shrinking. |
| Pledge does not work as intended. | The repo traces this to the current `A(nu, pi)` shape and low effective pledge weight. It says the function punishes small pools, can reward under-commitment in some regions, and leaves most pledge budget unused. | Pledge is supposed to signal skin in the game and resist Sybil behavior. If it is ignored, the security argument weakens. |
| Small productive operators are not viable. | The flat `minPoolCost` structure behaves regressively: it takes a much larger effective share from small pools than from near-saturated pools. Small operators also face fixed infrastructure and labor costs. | The intended path from new operator to established operator becomes hard to walk, and the single-pool operator base declines. |
| Delegator yield is falling and weakly differentiated. | Yield tracks reserve depletion, and yield spreads between many pool choices are too narrow to drive delegation decisions. | Delegators are meant to be the oversight layer, but they need visible, meaningful signals to discipline operators. |
| Existing pool-count and pledge levers can backfire if used alone. | Raising `k` shrinks average pool size and can worsen viability if the fee and pledge problems remain. Raising `a0` before repairing `A(nu, pi)` can amplify a broken pledge surface. Hard pledge caps can hit all operator types before they can comply. | Single-parameter fixes can move the bottleneck rather than solve it. |
| Entity-level concentration is under-modeled. | The Constitution and protocol parameters operate mainly at pool level, while many economic decisions happen at entity or fleet level. | A network can look decentralized by pool count while being more concentrated by controlling entity. |
| Fee growth is not only a parameter problem. | The submitter base is not expanding enough, script and enterprise addresses contribute fees but may not be able to delegate, and fee revenue is far below the level needed for self-sufficiency. | The long-run funding transition requires actual demand and transaction volume, not just reward-parameter changes. |
| The mechanism lacks macro feedback. | The repo says the system passively absorbs ADA/fiat moves and has no on-chain instrument for price-aware recalibration. | Real-world operator costs and delegator opportunity costs are not denominated only in ADA. |

## Suggested Solutions

The repo's main solution principle is: repair root causes before scaling the
system up. Its recommended direction is not to stack isolated CIPs immediately,
but to fix the reward-distribution layer first.

The first-stage reward repair is described as four moves:

1. Repair `A(nu, pi)` so pledge is no longer a dominated or weak strategy. A
   repaired pledge function should help smaller pools enter, avoid privileging
   fully private pools, and reward balanced commitment.
2. Reduce the dominance of raw size by shifting weight from `lambda_size`
   toward `lambda_pledge`, using `a0` only after `A(nu, pi)` is repaired.
3. Add a viability support mechanism for genuine smaller productive pools,
   funded from the existing reward envelope rather than by printing new ADA.
4. Activate the pledge budget that currently returns unused to the reserve.

The repo also argues for keeping fee parameters as flexible market levers:
`minPoolCost`, margins, and related fee settings should not be the main place
where operator viability is solved. Viability support should sit before the
operator/delegator fee split, not after it.

The broader sequence in `reward-system-spec/README.md` is:

1. Repair pledge and small-SPO viability.
2. Maintain and diversify delegator yield, including possible smart-contract
   based products such as lock-up tiers, liquid staking derivatives, and
   automated delegation strategies.
3. Build a Pool Alliance style entry path and make the productive threshold
   explicit, so sub-threshold operators have a route into productive consensus.
4. Re-engage non-participating ADA where address type, custody, scripts, or
   wallet design currently keep capital outside staking.
5. Research entity-level mechanisms and titan-delegator effects after the
   active-player ground has been repaired.
6. Add a governance dashboard that tracks operators, delegators, submitters,
   and non-participants, so parameter changes are evidence-driven rather than
   ad hoc.

The existing CIPs are not treated as useless. The repo says CIP-0023,
CIP-0037, CIP-0050, and CIP-0082 identify real problems. Its critique is about
layer and sequencing: they act one step away from the source, so the root-level
reward repair should land first and the CIPs should then be reassessed.

## How A Parameter Landscape Would Overlap

A Cardano parameter landscape would overlap strongly with this repo, but it
would not duplicate it.

This repo provides the diagnosis and design logic: what is broken, why it is
broken, which incentives matter, and which fixes should be sequenced first. A
parameter landscape would turn that into a systematic map of parameter changes
and their incentive effects.

The overlap is direct because the repo already identifies the key parameters:

| Parameter or lever | Role in this repo | What a landscape would analyze |
| --- | --- | --- |
| `minPoolCost` | Flat per-pool fee floor. The repo says it is regressive for small pools but still a live governance lever. | Effects on small-pool operator income, delegator net yield, fee competition, and pool survival. |
| `a0` | Pledge influence. It controls the balance between size and pledge in the reward envelope. | Effects on pledge incentives, operator commitment, delegator-visible yield differences, and whether raising `a0` helps or hurts under different `A(nu, pi)` shapes. |
| `k` | Target pool count / saturation parameter. Higher `k` means smaller saturation size. | Effects on concentration, average pool size, small-pool viability, MPO fleet absorption, and interaction with stake caps or pledge requirements. |
| `rho` | Monetary expansion rate from the reserve. | Effects on reserve runway, delegator yield, operator revenue, and long-run fee-replacement pressure. |
| `tau` | Treasury cut from the epoch pot. | Effects on pool rewards, treasury accumulation, sustainability, and possible treasury-funded interventions. |
| `lambda_size` | Weight of pool size in the reward envelope. | How much the mechanism rewards raw stake access versus commitment. |
| `lambda_pledge` | Weight of pledge in the reward envelope. | Whether pledge becomes a visible economic signal or remains mostly ignored. |
| `lambda_viability` / `b0` | Proposed viability slice inside the reward formula in the implementation-scope document. | How much support is needed to make productive small pools viable, who qualifies, and how much delegator yield is affected. |
| `mu` | Alternative proposed viability-channel share in the V2 whiteboard. | Whether viability is better modeled as a separate channel rather than as a third slice inside the reward envelope. |
| Stake-cap levers from CIP-0037 / CIP-0050 | Pledge-linked limits on reward-eligible stake. | Whether pledge caps reduce Sybil behavior, whether they harm low-capital operators, and when they become safe after pledge repair. |
| Fee-layer levers from CIP-0023 / CIP-0082 | Minimum margin or rate mechanisms after pool reward is calculated. | Whether fee floors improve fairness or merely transfer reward from delegators to large operators. |

The important overlap is interaction effects. The repo repeatedly argues that
isolated parameter moves are dangerous:

```text
raise k alone      -> more pool slots, but smaller average pool size
raise a0 alone     -> stronger pledge weighting, but through a broken A(nu, pi)
remove fixed fees  -> better delegator comparability, but weaker operator income
hard pledge caps   -> stronger commitment pressure, but possible viability shock
```

So a useful parameter landscape should compare combinations, not just one-dial
changes. The repo implies that each scenario should be judged against at least
these outcome dimensions:

- operator viability;
- delegator net yield;
- pledge participation and pledge-budget utilization;
- single-pool versus multi-pool operator share;
- entity-level concentration, not only pool count;
- reserve draw and fee-replacement pressure;
- non-participant re-engagement;
- constitutional guardrail compatibility;
- whether the change acts at the root reward-distribution layer or only at a
  downstream fee/stake-cap layer.

In short: this repo is the qualitative and empirical foundation for a parameter
landscape. The landscape would be the quantitative decision surface built on top
of it.

## Repo Sources Used

- [`README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/README.md)
- [`reward-system-spec/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/README.md)
- [`reward-system-spec/the-intended-game/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/the-intended-game/README.md)
- [`reward-system-spec/diagnostic/findings.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/diagnostic/findings.md)
- [`reward-system-spec/solution-evaluation/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/solution-evaluation/README.md)
- [`reward-system-spec/solution-evaluation/v2-proposal/new-CIP.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/solution-evaluation/v2-proposal/new-CIP.md)
- [`reward-system-spec/implementation-scope/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/implementation-scope/README.md)
- [`reward-system-spec/whats-next/README.md`](https://github.com/input-output-hk/spo-incentives/blob/main/reward-system-spec/whats-next/README.md)
- [`report-november-2025/report.tex`](https://github.com/input-output-hk/spo-incentives/blob/main/report-november-2025/report.tex)
