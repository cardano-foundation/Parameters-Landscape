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

### Notation and normalization

Unless stated otherwise, stake variables are measured as fractions of total ADA supply ($T$).
Thus,

$$\sigma_i = \frac{\text{pool } i \text{ stake in ADA}}{T}, \qquad p_i = \frac{\text{pool } i \text{ pledge in ADA}}{T}, \qquad z_0 = \frac{1}{k}.$$

If variables are measured directly in ADA, we use the ADA-denominated versions, e.g., with some abuse of notation, $z_0=\frac{T}{k}$.  

Notation is not fully standardized across the literature. In particular, pledge is sometimes denoted by $p_i$, $\lambda_i$, or $s_i$. Here we use $p_i$ for declared pledge.


## Parameters tables

### 1. System-wide variables

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $R$ | Reward pot | Total rewards available in an epoch. | Scales gross rewards to pools, operators, and delegators. |
| $T$ | Total ADA supply | Measures all ADA in circulation + unclaimed rewards + deposits + fees + treasury  | Reference ADA base used to normalize stake variables. |
| $S$ | Active stake | Total ADA actively delegated or pledged. | Measures staking participation. |
| $S/T$ | Staking participation rate | Share of total supply participating in staking. | Captures effectivness of the incentive to stake rather than remain liquid. |

### 2. Protocol parameters

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $k$ | Target pool count | Intended number of saturated pools. | Higher $k$ lowers saturation and changes pool competitiveness. |
| $z_0 = 1/k$ | Saturation threshold | Maximum reward-bearing stake per pool, as a fraction of $T$. | Caps the stake that can earn rewards in one pool. |
| $a_0$ | Pledge influence | Strength of pledge in the reward formula. | Higher $a_0$ favors high-pledge pools. |
| $c_{\min}$ | Minimum fixed cost | Minimum fixed fee a pool operator can charge. | Affects small-pool viability and delegator returns. |
| $\tau$ | Treasury share | Fraction of rewards allocated to the treasury. | Trades off staking rewards against ecosystem funding. |
| $\rho$ | Reserve decay rate | Rate at which reserves are released into rewards. | Affects long-run reward sustainability. |

### 3. Pool-level stake and pledge variables

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $\sigma_i$ | Pool stake | Total stake assigned to pool $i$, as a fraction of $T$. | Main input for pool rewards and saturation. |
| $p_i$ | Declared pledge | Pledge declared by the pool operator. | Enters the pool reward formula. |
| $\hat p_i$ | Active operator pledge | Actual operator-controlled stake delegated to pool $i$. | Determines whether the declared pledge is honored. |
| $\beta_i$ | External delegation | Stake delegated by non-operator delegators. | Measures dependence on outside delegators. |
| $\sigma_i = \hat p_i + \beta_i$ | Pool stake identity | Total pool stake equals operator pledge plus external delegation. | Links pledge, delegation, and pool size. |

### 4. Effective reward-bearing variables

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $\bar{\sigma}_i = \min\\{\sigma_i,z_0\\}$ | Effective pool stake | Reward-bearing pool stake after the saturation cap. | Stake above saturation does not increase pool rewards. |
| $\bar p_i = \min\\{p_i,z_0\\}$ | Effective pledge | Reward-bearing pledge after the saturation cap. | Pledge above saturation does not further increase rewards. |
| $f(\sigma_i,p_i)$ | Pool reward function | Gross reward assigned to pool $i$. | Central link between parameters and incentives. |
| $f(\sigma_i,p_i)=0\)$ if $\hat{p}_i < p_i$ | Pledge constraint | Pool receives no rewards if active pledge is below declared pledge. | Makes pledge declarations incentive-relevant. |

### 5. Pool fees and reward sharing

| Symbol | Parameter | Definition | Why it matters |
| --- | --- | --- | --- |
| $c_i$ | Fixed pool cost | Fixed ADA amount retained by the operator before margin sharing. | Reduces rewards available to delegators. |
| $m_i$ | Pool margin | Percentage fee charged by the operator after fixed cost. | Splits residual rewards between operator and delegators. |
| $\mathrm{ROS}_i$ | Delegator return | Net return received by delegators in pool $i$. | Main variable guiding delegation choices. |
| $\Pi_i$ | Operator profit | Net reward retained by pool operator $i$. | Determines pool entry, exit, and survival. |

### 6. Incentive and decentralization outcomes

| Symbol | Outcome | Definition | Why it matters |
| --- | --- | --- | --- |
| $\mathrm{APR}$ | Network staking return | Average annualized staking return. | Affects the incentive to stake. |
| $\sigma_i/z_0$ | Saturation ratio | Pool stake relative to the saturation threshold. | Measures whether a pool is under-, near-, or over-saturated. |
| $N_{\mathrm{active}}$ | Active pool count | Number of pools with positive active stake. | Basic measure of pool participation. |
| $N_{\mathrm{viable}}$ | Viable pool count | Number of pools with enough stake/profit to remain competitive. | Better measure of effective decentralization. |
| $H$ | Stake concentration | Concentration of stake across pools or operators. | Captures decentralization risk. |
| $\beta_i/p_i$ | Pledge leverage | External delegation attracted per unit of pledge. | Measures how strongly pledge attracts outside stake. |
| $M_i$ | Multi-pool footprint | Number of pools controlled by operator $i$. | Captures pool-splitting incentives. |

## Incentive-channel

| Parameter change | Mechanical effect | Delegator incentive | SPO incentive | Decentralization effect |
| --- | --- | --- | --- | --- |
| Increase $k$ | Lowers $z_0$. | Move away from saturated pools. | Smaller pools become more competitive. | May reduce concentration, but can increase pool splitting. |
| Decrease $k$ | Raises $z_0$. | More stake can remain in large pools. | Large pools become more attractive. | May increase concentration. |
| Increase $a_0$ | Raises pledge premium. | Prefer high-pledge pools. | Operators need more pledge. | May favor capital-rich operators. |
| Decrease $a_0$ | Lowers pledge premium. | Pledge matters less for returns. | Easier entry for low-pledge pools. | May improve entry but weaken skin-in-the-game. |
| Increase $c_{\min}$ | Raises minimum operator fee. | Lowers returns in small pools. | Protects operator revenue. | May hurt small-pool competitiveness. |
| Increase $\tau$ | Reduces staking rewards. | Lower incentive to stake. | Lower pool profitability. | May reduce participation. |
| Increase $\rho$ | Releases reserves faster. | Higher short-run staking rewards. | Higher short-run pool profitability. | Improves short-run incentives but weakens long-run sustainability. |



