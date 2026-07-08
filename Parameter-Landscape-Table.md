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

The rows below now reflect not only the repo’s own diagnosis but also the evidence from the papers, reports, and external links collected in [References/readme.md](References/readme.md).

| Parameter / lever | Main reason it exists in the original design | Other incentive effects discussed in the references |
| --- | --- | --- |
| `minPoolCost` | Ensure a minimum operator income and cover fixed costs | The Beccuti report treats lowering it as a “pull” effect for small pools because it improves the net rewards they can distribute. That can increase small-pool attractiveness, but it may be insufficient on its own if larger pools remain more profitable. |
| Margin / operator fee rate | Let operators earn income from service and fund infrastructure | The fee-layer analysis argues that margins mainly redistribute rewards between operators and delegators. They affect profitability and visible yield, but changing them alone does not solve the deeper viability problem if delegation does not actually move toward smaller pools. |
| Effective pledge amount / pledge ratio | Signal skin in the game and increase commitment | The original design spec and the broader incentive papers frame this as both a commitment signal and a protection against pool-level Sybil behavior. In practice it also changes how much pledge is economically attractive and whether the pledge budget is activated rather than returned to reserve. |
| `a0` | Balance size-based rewards against pledge-based rewards | The CIP-50 report argues that a stronger pledge-based margin can improve the relative position of well-pledged pools and reduce the appeal of large low-pledge pools, but the effect depends heavily on the leverage parameter and the capacity of the pool set to absorb reallocation. |
| `lambda_size` | Reward participation and pool size | The Kiayias et al. reward-sharing work shows that this is part of a broader trade-off between participation and decentralization. Increasing size weight can strengthen the reward advantage of larger pools, but it can also crowd out the pledge signal and reduce the system’s ability to balance participation with decentralization. |
| `lambda_pledge` | Make pledge a meaningful economic signal | The design and the papers suggest that pledge weight matters not only for commitment but also for whether the mechanism can support a healthy operator population and keep the pledge budget from going unused. Too little weight leaves pledge economically weak; too much can hurt small-pool entry or reduce net delegator yield. |
| Pledge-bonus curve `A(nu, pi)` | Make pledge matter in a structured way | The repo’s diagnostic and the referenced papers both stress that the shape of this function matters for more than Sybil resistance. It affects whether small pools are punished, whether under-commitment is rewarded in some regions, whether the pledge budget is left unused, and whether the system can sustain a viable small-operator base. |
| `k` | Control the target pool count and saturation level | Beccuti’s report finds that increasing `k` can help small and medium pools gain stake relative to the network, especially in a fixed cohort, but the effect is not universal and may be amplified by market conditions. The same discussion also notes that some affected stake may not migrate at all if it belongs to large entities or custodial structures. |
| `rho` | Fund rewards from reserve expansion and bootstrap staking | The repo’s sustainability analysis and the economic parameter work frame this as a funding lever as much as an incentive lever. It changes operator revenue and delegator yield in the short run, but it does not repair the underlying reward structure and may simply defer reserve depletion. |
| `tau` | Split the epoch pot between pools and treasury | The sustainability discussion treats this as a funding trade-off that affects how much reward reaches pools versus treasury. It is mostly a macro-allocation lever, but it strongly shapes reward generosity and long-run sustainability. |
| Viability-support slice / `lambda_viability` or `b0` | Support genuinely small but productive pools | This is a direct viability lever. The repo’s implementation-scope analysis and the fee-layer discussion both treat it as the right place to solve the “production but not viable” problem, rather than relying only on pricing tools such as `minPoolCost` or margins. |
| Alternative viability share `mu` | Provide a separate viability channel rather than overloading the existing reward split | The implementation-scope discussion presents this as a design alternative for keeping viability support explicit and separate from the main reward split. It can strengthen small-pool entry while preserving a clearer distinction between reward-sharing and viability support. |
| Stake-cap levers from CIP-0037 / CIP-0050 | Make pledge binding on reward-eligible stake and reduce concentration | The CIP-50 report highlights that the effect depends critically on leverage. If leverage is too low, the mechanism may not provide enough reward-bearing capacity and may produce severe transition pressure; if it is too high, the intended pledge-based benefits are diluted. |
| Fee-layer levers from CIP-0023 / CIP-0082 | Improve fairness in the fee layer and reduce exploitative pricing | The fee-layer synthesis treats these as downstream tools rather than root-cause fixes. They can help small pools become more competitive and improve net yield comparability, but they do not by themselves resolve the underlying reward-surface and concentration problems. |

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
