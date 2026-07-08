# Parameters Affecting Operator and Delegator Incentives

This file present a table of the key parameters affecting incentives. It is based on the uploaded original-design papers and reports in [References/papers](References/papers) and [References/reports](References/reports).

Notation has not been consistent for some parametes accross different papers and reports. In this case, the table will be explicit about this issue, showing the different notations.

Before introducing the table, we present the main formulas that drives incentives and from where we extract the key parameters.

<!-- The most explicit definitions come from the CIP-50 report, which states that for pool $i$, $p_i$ is the declared pledge, $\sigma_i$ is the total stake, $z_0 = T/k$ is the saturation point, $\tilde{\sigma}_i = \min(\sigma_i, z_0)$ is reward-bearing stake, $\tilde{p}_i = \min(p_i, z_0)$ is reward-bearing pledge, $R$ is the reward pot, and $a_0$ is the pledge influence parameter. The reward-sharing paper uses a generic reward function $r(\sigma, \lambda)$, while the 2024 paper defines $\beta_j$, $\lambda_j$, and $\sigma_j$ for pool $j$. -->

## Reserves, treasury, and reward pot

## Reward function


## Parameters table

| Symbol | Parameter / lever | Definition as used in the source papers | Where it appears in the uploaded PDFs | Why it matters |
| --- | --- | --- | --- | --- |
| $\sigma_i$ | Stake delegated to pool $i$ | Total stake associated with pool $i$ | CIP-50 report; 2024 balancing paper | This is the pool’s stake base and the main input for reward-bearing capacity. |
| $\beta_j$ | External stake delegated to pool $j$ | Stake delegated to pool $j$ from outside the operator | 2024 balancing paper | Distinguishes operator pledge from delegated stake. |
| $\lambda_j$ | Operator pledge of pool $j$ | The pledge contributed by the pool operator | 2024 balancing paper | This is the pool-level pledge variable used in the pool reward model. |
| $\sigma_j = \lambda_j + \beta_j$ | Total stake of pool $j$ | Sum of operator pledge and delegated stake | 2024 balancing paper | This is the full pool stake variable used in the reward-sharing model. |
| $T$ | Total circulation supply | Total ADA supply in the system | CIP-50 report; Beccuti reports | It sets the scale of the saturation point and the reward-bearing quantities. |
| $S$ | Total stake | Total stake that is actively participating in staking | Beccuti reports | It is used to compare total supply and active participation. |
| $k$ | Target pool count / saturation parameter | The intended number of pools and the parameter that determines saturation | CIP-50 report; Beccuti reports | A higher $k$ lowers the saturation point and changes pool competitiveness. |
| $z_0 = T/k$ | Saturation point | The common reward-bearing stake cap per pool | CIP-50 report | It is the key cap that determines how much stake per pool can earn rewards. |
| $p_i$ | Declared pledge | The pledge declared by pool $i$ | CIP-50 report | It is the commitment amount that the design uses as the starting point for pledge-based rewards. |
| $\tilde{\sigma}_i = \min(\sigma_i, z_0)$ | Reward-bearing stake / effective delegation | The portion of pool stake that remains reward-bearing after the saturation cap | CIP-50 report | This is the effective delegated stake that can actually earn rewards. |
| $\tilde{p}_i = \min(p_i, z_0)$ | Reward-bearing pledge / effective pledge | The portion of declared pledge that is reward-bearing after the saturation cap | CIP-50 report | This is the effective pledge that matters for the reward function. |
| $R$ | Reward pot | The total reward budget available in the epoch | CIP-50 report | It scales the gross reward assigned to each pool. |
| $a_0$ | Pledge influence parameter | The parameter that governs how strongly pledge affects reward | CIP-50 report | It directly changes the reward advantage of well-pledged pools. |
| $q_i$ | Effective reward-bearing quota | The effective quota that determines how much of the pool’s reward-bearing stake is eligible | CIP-50 report | This is the pool-specific reward-bearing capacity term in the reward formula. |
| $L$ | Leverage parameter | The parameter that determines how strongly pledge-linked reward capacity is amplified under CIP-50 | CIP-50 report | It governs the transition pressure and feasibility of the reform. |
| $r(\sigma, \lambda)$ | Generic pool reward function | A reward function that maps pool stake and pledged stake into pool rewards | 2020 reward-sharing schemes paper | This is the general reward-sharing abstraction used in the paper. |

## Symbols that are not present verbatim in the uploaded PDFs

The following symbols are mentioned in later repo summaries and in the broader Cardano reward discussion, but they are not present as literal notation in the uploaded original-design PDFs:

- $\lambda_{size}$ and $\lambda_{pledge}$
- $A(\nu, \pi)$
- $\lambda_{viability}$

The closest source material in the uploaded set is the generic reward function $r(\sigma, \lambda)$ in the 2020 reward-sharing paper, together with the explicit CIP-50 definitions of $\sigma_i$, $p_i$, $z_0$, $\tilde{\sigma}_i$, $\tilde{p}_i$, $R$, $a_0$, and $L$.

## Why this matters

The original-design papers do not just discuss general incentives. They also define the core state variables of the system:

- how much stake a pool has;
- how much of that stake is reward-bearing;
- how much pledge the pool declares;
- how much of that pledge is reward-bearing;
- what the total supply and the saturation level are; and
- how the reward pot is distributed across pools.

That is why any serious parameter landscape has to start from these variables before moving to later policy levers such as viability support or fee-layer reform.
