# Parameters Affecting Operator and Delegator Incentives

This file present tables of the key parameters affecting the reward scheme and the agents incentives. It is based on the uploaded original-design papers and reports in [References/papers](References/papers) and [References/reports](References/reports).

Before introducing the table, we present the main formulas that drives incentives and from where we extract the key parameters.

## Reserves, treasury, and reward pot

Cardano has a reserve of tokens—the difference between the maximum supply (45B ADA) and the total supply in circulation—with a predefined monetary expansion across time. Each epoch, a certain amount of the reserve $\rho$ (currently 0.3%) is taken to reward pool operators and fund the treasury.

The fraction of that amount that goes to the treasury is denoted by $\tau$ and is currently set to $\tau=20\%$. Hence, the remaining $80\%$ goes to the reward pot. Additionally, the reward pot for epoch $t$ is populated with the transaction fees collected during the same epoch. However, because the network needs a full epoch to safely calculate everything, this pot is distributed at the start of epoch $t+2$.

Hence, the final reward pot ($R$) available is:

$$R = (1 - \tau) \cdot (\text{fees} + \rho \cdot \text{reserves})$$

Not all of the pot is actually paid out. Rewards are only paid on active, staked ADA. If less than 100% of the circulating supply is staked, a portion goes unearned. The leftovers are automatically sent back to the reserves.

> **Note:** Most of the analysis presented in this document assumes a static environment, omitting the dynamic, inter-epoch feedback effects of return flows to the reserves. While return flows can be evaluated statically for a given state, fully dynamic feedback scenarios will be explicitly indicated.


> **Note:** By design, the final reward pot ($R$) also includes the non-refundable portion of deposits. This component is currently inactive in the implemented reward scheme. In addition, the monetary-expansion term ($\rho \cdot \text{reserves}$) is adjusted by a performance factor. For simplicity, that factor is omitted here and discussed separately below.

## Reward function

The gross reward of pool $i$ is given by:

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right],$$

where
 
  $$\tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\}.$$

See the tables below for a definition and description of each of the parameters and variables entering the equation. 

> **Note:** The parameter $z_0$, and variables $\sigma_i$ and $p_i$ enter the formula as relative fractions of the total supply $T$ (for example, $z_0 = T/k$ simplifies to $1/k$ when normalized), whereas $R$ is measured in absolute ADA. With a slight abuse of notation, we use the same symbols regardless of whether these values are normalized. Consequently, the formula yields the fraction of the reward pot $R$ awarded to pool $i$ in that epoch. A pool whose active pledge falls below its declared pledge receives $f(\sigma_i, p_i) = 0$.

The reward is then adjusted for a pool's performance factor that we denote here with $\lambda_i$. Then, the realized gross reward is

$$\lambda_i f(\sigma_i,p_i).$$

> **Assumption:** Unless stated otherwise, the following analysis assumes that block performance and missed blocks do not affect rewards (i.e., $\lambda_i = 1$) and that pools fully meet their declared pledge. An unmet pledge in a given epoch results in zero rewards for that pool.

Each pool has to declared their operating fixed cost $c_i\ge c_{min}=170$ ADA. This declaration may be equal or different to the real operating fixed cost $\hat{c}_i$.

Additionally, each pool sets the margin or commission $m_i\in[0,1)$. For pool $i$, the protocol first pays the fixed cost $c_i$ whenever $f(\sigma_i,p_i) > c_i$. The remaining amount, $\bigl[f(\sigma_i,p_i)-c_i\bigr]_+$, is then allocated as follows: a fraction $m_i$ is taken by the operator as the pool margin, that is, as a commission on delegation rewards, and the residual fraction $(1-m_i)$ is distributed proportionally among all stake delegated to the pool, including the operator's own pledged stake. Thus, **the pool operator $i$ gets** an utility:


$$
U_i=
\begin{cases}
\underbrace{c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right]}_{\Pi_i=\text{Operator gross revenue}}-\hat{c}_i, & \text{if } f(\sigma_i,p_i)>c_i, \\
f(\sigma_i,p_i)-\hat{c}_i, & \text{otherwise}
\end{cases}
$$

where $\hat{p}_i$ denotes the operator's active pledge. Assuming incentive compatibility (IC)—a property proven by [Brünjes et al. (2020)](References/papers/reward-sharing-schemes_brunjes-kiayias-et-al_2020.pdf) within the context of their game-theoretic model—operators declare their actual fixed costs ($c_i = \hat{c}_i$). This implies that incentive analysis should focus on net profits, 

$$(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right].$$ 

However, our analysis focuses instead on **operator gross revenues**, 

$$c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right].$$

There are several market conditions (beyond the assumptions about perfectly rational delegators and frictionless markets) that support this approach. For instance, some studies has shown evidence that delegators exhibit inertia or rational ignorance: they do not re-delegate immediately when an operator changes margins and/or there are other operators with better returns (e.g., see [Competition in Crypto Staking](https://www.youtube.com/watch?v=GrZ6R_Ozds0) ). Additionally, many real-world pool operators run nodes on pre-existing infrastructure or home hardware where real operational costs are negligible. For these operators, the declared fixed cost acts almost entirely as guaranteed net revenue rather than an expense reimbursement. 

On the other hand **a delegator $d$ with stake $\sigma_d$ achieves**:

$$
U_d=
\begin{cases}
(1-m_i)(f(\sigma_i,p_i)-c_i)\frac{\sigma_d}{\sigma_i}, & \text{if } f(\sigma_i,p_i)>c_i, \\
0, & \text{otherwise},
\end{cases}
$$

with 

$$\sigma_i=\hat{p}_i + \sum_{j=1}^{D_i}\sigma_j$$  

and where $D_i$ denotes the set of delegators delegating to pool $i$. 

The expressions above inform how the current design rewards operators and delegators based on stake and pledge.

### Notation and normalization

Unless stated otherwise, stake variables are measured as fractions of total ADA supply ($T$).
Thus,

$$\sigma_i = \frac{\text{pool } i \text{ stake in ADA}}{T}, \qquad p_i = \frac{\text{pool } i \text{ pledge in ADA}}{T}, \qquad z_0 = \frac{1}{k}.$$

If the variables were instead measured directly in ADA, the ADA-denominated versions should be used, for example, $z_0=\frac{T}{k}$.

Notation is not fully standardized across the literature. For instance, pledge is in some papers/works/documents denoted by $p_i$, while in others by $\lambda_i$, or $s_i$. Here we use $p_i$ for declared pledge, while we reserve $\lambda_i$ for the performance factor.



## Parameters tables

### 1. System-wide variables

| Symbol | Parameter | Definition | Role / Why it matters |
| --- | --- | --- | --- |
| $R$ | Reward pot | Total rewards available in an epoch. | Scales gross rewards to pools, operators, and delegators. |
| $T$ | Total ADA supply | Measures all ADA in circulation + unclaimed rewards + deposits + fees + treasury  | Reference ADA base used to normalize stake variables. |
| $S$ | Active stake | Total ADA actively delegated or pledged. | Measures staking participation. |
| $S/T$ | Staking participation rate | Share of total supply participating in staking. | Captures effectivness of the incentive to stake rather than remain liquid. |

### 2. Protocol parameters

| Symbol | Parameter Definition | Current value | Role / Why it matters | Comments |
| --- | --- | --- |  --- | --- |
| $k$ | Target number of stake pools | 500 | Sets the saturation threshold $z_0$. <br> Determines how many pools are expected to attract delegation. <br> Affects the scale of pool rewards. <br> Decentralization-design parameter. | It does not impose a limit on the number of pools. Its role in the reward function is to induce an equilibrium with nearly k economically relevant pools. |
| $z_0 = 1/k$ | Saturation threshold. Maximum reward-bearing stake per pool, as a fraction of $T$. | 1/500 | Caps the stake that can earn rewards in one pool. | --- |
| $a_0$ | Pledge influence. Strength of pledge in the reward formula. | 0.3 | Higher $a_0$ favors high-pledge pools. Desincentivize Sybil behavior. | --- |
| $c_{min}$ | Minimum fixed cost (`minPoolCost`). Minimum fixed fee a pool operator can charge. | 170 ADA | Affects small-pool viability and delegator returns. | --- |
| $\tau$ | Treasury share. Fraction of rewards allocated to the treasury. | 20% | Trades off staking rewards against ecosystem funding. | --- |
| $\rho$ | Reserve decay rate. Rate at which reserves are deployed into rewards. | 0.3%  | Main contributor to operators and delegators rewards. Affects long-run reward sustainability. | --- |

### 3. Operators and delegators choices

| Symbol | Parameter | Definition | Role / Why it matters |
| --- | --- | --- | --- |
| $\sigma_i$ | Pool stake | Total stake assigned to pool $i$, as a fraction of $T$. | Main input for pool rewards and saturation. |
| $p_i$ | Declared pledge | Pledge declared by the pool operator. | It helps to indicate the "skin-on-the-game" of the operator. It affect pool rewards. |
| $\hat{p}_i$ | Active operator pledge | Actual operator-controlled stake delegated to pool $i$. | Determines whether the declared pledge is honored. |
| $\sigma_i = \hat{p}_i + \sum_{j=1}^{D_i}\sigma_j$ | Pool total delegation | Total pool stake equals operator active pledge plus external delegation. | Links pledge, delegation, and pool size. |
| $c_i$ | Fixed declared pool cost | Fixed ADA amount retained by the operator before margin sharing. | Reduces rewards available to delegators. |
| $\hat{c}_i$ | Real fixed pool cost | Operating cost faced by the pool operator | Declared and real operating costs may differ, affecting the operator's profit. |
| $m_i$ | Pool margin | Percentage fee charged by the operator after fixed cost. | Splits residual rewards between operator and delegators. |

### 4. Effective reward-bearing variables

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $\tilde{\sigma}_i = \min\\{\sigma_i,z_0\\}$ | Effective pool stake | Reward-bearing pool stake after the saturation cap. | Stake above saturation does not increase pool rewards. |
| $\tilde{p}_i = \min\\{p_i,z_0\\}$ | Effective pledge | Reward-bearing pledge after the saturation cap. | Pledge above saturation does not further increase rewards. |

### 5. Outcomes

| Symbol | Outcome | Definition | Why it matters |
| --- | --- | --- | --- |
| $\mathrm{ROS}_i$ | Delegator return | Net return received by delegators in pool $i$. | Main variable guiding delegation choices. |
| $\Pi_i$ | Operator gross revenue | Total rewards obtained by pool operator $i$. | Determines pool profits. |
| $U_i$ | Operator utility/profit | Net reward retained by pool operator $i$. | Determines pool entry, exit, and survival. |
| $\mathrm{APR}$ | Network staking return | Average annualized staking return. | Affects the incentive to stake. |
| $\sigma_i/z_0$ | Saturation ratio | Pool stake relative to the saturation threshold. | Measures whether a pool is under-, near-, or over-saturated. |
| $N_{\mathrm{active}}$ | Active pool count | Number of pools with positive active stake. | Basic measure of pool participation. |
| $N_{\mathrm{viable}}$ | Viable pool count | Number of pools with enough stake/profit to remain competitive. | Better measure of effective decentralization. |
| $H$ | Stake concentration | Concentration of stake across pools or operators. | Captures decentralization risk. |
| $\beta_i/p_i$ | Pledge leverage | External delegation attracted per unit of pledge. | Measures how strongly pledge attracts outside stake. |
| $M_i$ | Multi-pool footprint | Number of pools controlled by operator $i$. | Captures pool-splitting incentives. |




