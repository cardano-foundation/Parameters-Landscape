# Parameters and Levers Affecting Operator and Delegator Incentives

This version expands beyond the narrow example of Sybil resistance. It is grounded in the reward-system analysis in [spo-incentives-cloned/reward-system-spec/solution-evaluation/operator-delegator/README.md](../spo-incentives-cloned/reward-system-spec/solution-evaluation/operator-delegator/README.md), [spo-incentives-cloned/reward-system-spec/solution-evaluation/pools-distribution/README.md](../spo-incentives-cloned/reward-system-spec/solution-evaluation/pools-distribution/README.md), [spo-incentives-cloned/reward-system-spec/implementation-scope/README.md](../spo-incentives-cloned/reward-system-spec/implementation-scope/README.md), and [spo-incentives-cloned/reward-system-spec/diagnostic/findings.md](../spo-incentives-cloned/reward-system-spec/diagnostic/findings.md), and it also takes into account the broader reference set collected in [References/readme.md](References/readme.md).

That broader set includes the papers in [References/papers](References/papers), such as the delegation-incentives and reward-sharing analyses, the reports in [References/reports](References/reports), and the external links listed in [References/readme.md](References/readme.md), including the Lopez de Lara analysis and the Cardano Economic Parameter Insights repo.

The repo repeatedly argues that these parameters matter not only for anti-Sybil or commitment effects, but also for:

- operator viability and entry;
- delegator yield and the ability to differentiate between pools;
- concentration among MPO fleets and large entities;
- reserve use, reward sustainability, and the share of rewards that return to the reserve;
- whether the mechanism can attract or re-engage non-participating ADA.

## Parameter table

| Parameter / lever | Main reason it exists in the original design | Other incentive effects discussed in the references |
| --- | --- | --- |
| `minPoolCost` | Ensure a minimum operator income and cover fixed costs | Creates a viability floor, but it is regressive for small pools and produces a $1/\sigma$ drag that can keep productive small pools below a sustainable income threshold. It also reduces delegator net yield and can make the pool market look less attractive to retail delegators. |
| Margin / operator fee rate | Let operators earn income from service and fund infrastructure | Primarily redistributes the pool reward between operators and delegators. It affects operator profitability and delegator yield, but the repo argues that changing margins alone does not fix the deeper profitability structure, because delegation may not migrate to small pools even when yield looks better. |
| Effective pledge amount / pledge ratio | Signal skin in the game and increase commitment | Changes the operator’s economic exposure and can alter whether a pool appears credible to delegators. It also influences the strength of the pledge signal, the willingness to pledge, and the amount of unused pledge budget that returns to reserve. |
| `a0` | Balance size-based rewards against pledge-based rewards | Affects the relative weight of raw size versus commitment. Raising it can make pledge more visible to delegators and operators, but if the underlying pledge curve is weak or mis-shaped, it can also amplify the wrong incentives rather than improve the intended game. |
| `lambda_size` | Reward participation and pool size | Increases the reward advantage of large or well-known pools. It can help large operators capture more rewards, weaken the pledge signal, and make the reward landscape more size-driven rather than commitment-driven. |
| `lambda_pledge` | Make pledge a meaningful economic signal | Affects whether pledge becomes visible and whether pledge budget is actually activated. If too weak, the pledge mechanism remains economically irrelevant; if too strong, it can worsen small-pool viability or reduce delegator yield. |
| Pledge-bonus curve `A(nu, pi)` | Make pledge matter in a structured way | This is not only an anti-Sybil lever. The repo argues that its shape governs whether small pools are punished, whether under-commitment is rewarded in some regions, whether pledge budget is left unused, and whether the system can support a healthy operator population. It strongly affects pool entry, small-SPO viability, and the credibility of the pledge signal. |
| `k` | Control the target pool count and saturation level | Changes average pool size and the number of pools that can be competitive. Higher `k` can support more pools in principle, but the repo notes it can also shrink average pool size and hurt viability if the fee and pledge problems remain unresolved. It also interacts with concentration and MPO fleet structure. |
| `rho` | Fund rewards from reserve expansion and bootstrap staking | Mostly affects reward budget and sustainability. It changes operator revenue and delegator yield in the short run, but it does not repair the underlying mechanism and may simply defer the reserve-depletion problem. |
| `tau` | Split the epoch pot between pools and treasury | Affects how much reward is available to pools and how much is diverted to treasury accumulation. It is a funding trade-off more than a direct commitment lever, but it strongly shapes long-run sustainability and reward generosity. |
| Viability-support slice / `lambda_viability` or `b0` | Support genuinely small but productive pools | This is a direct viability lever. The repo treats it as a way to preserve small operators, reduce the “production but not viable” problem, and avoid relying entirely on fee-layer pricing to solve viability. It also affects whether delegators see a meaningful yield spread among pool types. |
| Alternative viability share `mu` | Provide a separate viability channel rather than overloading the existing reward split | Offers a more explicit degree of freedom for viability support. It can improve the entry path for small operators while keeping the reward formula from being overloaded, but it also changes how much reward remains available for size and pledge channels. |
| Stake-cap levers from CIP-0037 / CIP-0050 | Make pledge binding on reward-eligible stake and reduce concentration | These are not only about Sybil resistance. They affect whether low-capital operators can participate, whether custodial or non-pledging entities are clipped, and how strongly the reward formula rewards real pledge rather than merely pool visibility. They can also alter the degree of concentration among MPO fleets. |
| Fee-layer levers from CIP-0023 / CIP-0082 | Improve fairness in the fee layer and reduce exploitative pricing | The repo sees them mostly as downstream tools. They can affect operator take, delegator yield, and the ability of small pools to remain competitive, but they do not resolve the deeper reward-surface problems on their own. They may also shift rewards between large and small operators without necessarily changing the underlying profitability structure. |

## Secondary effects that the repo highlights repeatedly

The repo’s discussion is broader than “does this deter Sybil behavior?” It repeatedly emphasizes the following side effects:

- Viability and entry: some parameters affect whether small productive operators can survive, not merely whether they can be rewarded at all.
- Delegator differentiation: parameters change whether delegators can see meaningful differences between pools, which matters because the repo says delegation often follows visibility and brand rather than small yield differences.
- Concentration: parameters can either reinforce or soften the concentration of rewards in MPO fleets or large entities.
- Funding sustainability: parameters affect how much of the reward budget is paid out, how much is returned to reserve, and whether the system is moving toward self-sufficiency.
- Non-participation: some levers can help re-engage ADA that is currently outside delegation, but others mostly redistribute rewards among existing participants.

## Main takeaway

The key lesson from the repo is that these parameters are not only “security tools.” They are also structural levers for:

- the shape of the operator population;
- the distribution of rewards between operators and delegators;
- the strength of the pledge signal;
- the sustainability of the reward budget; and
- the extent of concentration and non-participation.

So a parameter landscape should evaluate them along these dimensions, not only along a narrow anti-Sybil axis.
