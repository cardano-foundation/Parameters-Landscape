# Parameters Affecting Operator and Delegator Incentives

This file present a table of the key parameters affecting incentives. It is based on the uploaded original-design papers and reports in [References/papers](References/papers) and [References/reports](References/reports).

Notation has not been consistent for some parametes accross different papers and reports. In this case, the table will be explicit about this issue, showing the different notations.

Before introducing the table, we present the main formulas that drives incentives and from where we extract the key parameters.

<!-- The most explicit definitions come from the CIP-50 report, which states that for pool $i$, $p_i$ is the declared pledge, $\sigma_i$ is the total stake, $z_0 = T/k$ is the saturation point, $\tilde{\sigma}_i = \min(\sigma_i, z_0)$ is reward-bearing stake, $\tilde{p}_i = \min(p_i, z_0)$ is reward-bearing pledge, $R$ is the reward pot, and $a_0$ is the pledge influence parameter. The reward-sharing paper uses a generic reward function $r(\sigma, \lambda)$, while the 2024 paper defines $\beta_j$, $\lambda_j$, and $\sigma_j$ for pool $j$. -->

## Reserves, treasury, and reward pot


## Reward function

The gross reward of pool $i$ can be written as:

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right].$$

This reward is then adjusted for a pool's performance factor that we denote here with $\lambda_i$. Then, the realized gross reward is

$$\lambda_i f(\sigma_i,p_i).$$

Assume $\lambda_i = 1$, let $c_i\ge 0$ denote the fixed cost charged by the pool and $m_i\in[0,1)$ its margin. For pool $i$, the protocol first pays the fixed cost $c_i$ whenever $f(\sigma_i,p_i) > c_i$. The remaining amount, $\bigl[f(\sigma_i,p_i)-c_i\bigr]_+$, is then allocated as follows: a fraction $m_i$ is taken by the operator as the pool margin, that is, as a commission on delegation rewards, and the residual fraction $(1-m_i)$ is distributed proportionally among all stake delegated to the pool, including the operator's own pledged stake. Thus, the pool operator gets:

$$
\begin{cases}
c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], & \text{if } f(\sigma_i,p_i)>c_i, \\
f(\sigma_i,p_i), & \text{otherwise}
\end{cases}
$$

where $\hat{p}_i$ denotes the operator's active pledge, and a delegator $d$ with stake $\sigma_d$ receives:

$$
\begin{cases}
(1-m_i)(f(\sigma_i,p_i)-c_i)\frac{\sigma_d}{\sigma_i}, & \text{if } f(\sigma_i,p_i)>c_i, \\
0, & \text{otherwise}
\end{cases}
$$

The expressions above inform how the current design rewards operators and delegators based on stake and pledge.

## Notation and normalization

Unless stated otherwise, stake variables are measured as fractions of total ADA supply \(T\).

Thus,

\[
\sigma_i = \frac{\text{pool } i \text{ stake in ADA}}{T},
\qquad
p_i = \frac{\text{pool } i \text{ pledge in ADA}}{T},
\qquad
z_0 = \frac{1}{k}.
\]

If variables are measured directly in ADA, use the ADA-denominated versions:

\[
Z_0 = \frac{T}{k},
\qquad
\Sigma_i = T\sigma_i,
\qquad
P_i = Tp_i,
\qquad
\Beta_i = T\beta_i.
\]

In that case, saturation is written as:

\[
\bar{\Sigma}_i = \min\{\Sigma_i,Z_0\},
\qquad
\bar{P}_i = \min\{P_i,Z_0\}.
\]

Notation is not fully standardized across the literature. In particular, pledge is sometimes denoted by \(p_i\), \(\lambda_i\), or \(s_i\). Here we use \(p_i\) for declared pledge.



## Parameters table

| Symbol | Parameter | Definition  | Why it matters |
| --- | --- | --- | --- |
| $R$ | Reward pot | The total reward budget available in the epoch |  It scales the gross reward assigned to each pool. |
| $T$ | Total circulation supply | Total ADA supply in the system |  It sets the scale of the saturation point and the reward-bearing quantities. |
| $S$ | Total stake | Total stake that is actively participating in staking |  It is used to compare total supply vs. active participation. |
| $k$ | Target pool count / saturation parameter | The intended number of pools in equilibrium and the parameter that determines saturation |  The parameter determines the saturation point given $T$. A higher $k$ lowers the saturation point and changes pool competitiveness. |
| $z_0 = 1/k$ | Saturation point measured as a fraction of $T$ (measured in ADA is $z_0=T/k$ | The common reward-bearing stake cap per pool | It is the key cap that determines how much stake per pool can earn rewards. |
| $\sigma_i$ | Stake delegated to pool $i$ as a fraction of $T$ | Total stake associated with pool $i$ | This is the pool’s stake base and the main input for reward-bearing capacity. |
| $\bar{\sigma}_i=\min\\{\sigma_i,z_0\\}$ | Reward-bearing / effective delegation on pool $i$ as a fraction of $T$ | The portion of pool stake that remains reward-bearing after the saturation cap | This is the effective delegated stake that can actually earn rewards. |
| $p_i$ | Operator declared pledge of pool $i$ as a fraction of $T$ (sometimes denoted by $\lambda_i$) | The pledge declared by the pool operator |  This is the pool-level pledge variable used in the pool reward model. |
| $\bar{p}_i=\min\\{p_i,z_0\\}$ | Reward-bearing pledge / effective pledge | The portion of declared pledge that is reward-bearing after the saturation cap |  This is the effective pledge that matters for the reward function. |
| $\hat{p}_i$ | Operator active pledge of pool $i$  as a fraction of $T$ | This is the ``self-delegation'' by the pool operator. It takes into account declared pledge |  This is used to calculate how much of the rewards to split among delegators corresponds to the pool operator. A pool with $\hat{p}_i<p_i$ gets $f(\sigma_i,p_i)=0$. |
| $\beta_i$ | External sum of stake delegated to pool $i$. | Total stake delegated to pool $i$ from outside the operator |  Distinguishes operator pledge from delegated stake. |
| $\sigma_i = \hat{p}_i + \beta_i$ | Total stake of pool $j$ | Sum of operator pledge and delegated stake | This is the full pool stake variable used in the reward-sharing model. |
| $a_0$ | Pledge influence parameter | The parameter that governs how strongly pledge affects reward |  It directly changes the reward advantage of well-pledged pools. |

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
