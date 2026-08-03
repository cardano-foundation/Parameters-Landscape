# Incentive effects of changing `minPoolCost` ($c_{min}$)
For the numerical analysis in this section, we use the parameter values below unless stated otherwise. These values may differ from the snapshot values reported in [Parameter-Landscape.md](../../Parameter-Landscape.md), because this comparative-statics exercise is anchored to a single reference state.

| Symbol | Parameter | Value |
| --- | --- | --- | 
| $R$ | Reward pot | $14.9M$ ADA| 
| $T$ | Total ADA supply | $38.8B$ ADA | 
| $k$ | Target number of stake pools | 500 | 
| $a_0$ | Pledge influence. | 0.3 | 
| $c_{min}$ | Minimum fixed cost (`minPoolCost`). | 170 ADA |
| $m_i$ | Operator margin/commission deducted from delegator rewards. | 5%  |
| $\rho$ | Reserve decay rate.  | 0.3%  |
| $\tau$ | Treasury share.| 20% |

## Design

The parameter $c_{\min}$ sets the minimum fixed cost that a stake pool operator may declare. The following plot shows the histogram of the fixed cost declarations at epoch 644.

<p align="center" id="fig-min-pool-cost-644">
  <img src="plots/min_pool_cost_hist_epoch_644.png" alt="Histogram c_i epoch 644" width="62%">
</p>

A change in $c_{\min}$ or in the declared fixed cost $c_i$ does not affect the pool's gross reward. Instead, the declared fixed cost is paid to the operator before the remaining rewards are divided between the operator and delegators.

The main objective of $c_{\min}$ is to support economically viable pool operation and provide some protection against Sybil attacks. Without a minimum fixed cost to declare, an operator could create many pools, declare negligible costs, and offer returns to delegators that other operators (that needs to declare their cost) may be unable to match.

The main trade-off comes from the incentive that a pool has to declare a larger fixed cost to cover their actual cost versus to declare less to become more attractive for delegators. That is, a higher $c_{\min}$ can therefore protect operator revenues and discourage small, undercapitalized Sybil pools, but it also reduces the competitiveness of small and new pools and may push delegation toward larger pools. A lower $c_{\min}$ facilitates entry and improves small-pool returns, but may intensify fee competition and make it easier for multi-pool operators to expand.

The appropriate level of $c_{\min}$ therefore balances operator viability and Sybil resistance against entry, competition, and decentralization.

Next, these effects and trade-off are explained with more details

## Direct mechanical effects 
In this section we consider the direct effects of **reducing** `minPoolCost` while holding everything else equal (ceteris paribus). 

### Gross pool rewards

Notice that the gross pool reward function does not depend on $c_{min}$:

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right], \qquad \tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\},$$

However, minPoolCost operates through two distinct channels: it guarantees fixed cost recovery for the operator while simultaneously dictating net delegator yield, thereby driving both operator profitability and pool competitiveness.

### Operator gross revenue

The pool operator gross revenue function is

$$\begin{cases} c_i + (f(\sigma_i,p_i)-c_i) \left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], & \text{if }  f(\sigma_i,p_i)>c_i, \\ 
f(\sigma_i,p_i), & \text{otherwise} \end{cases}$$

where it is assume that the  operator's active pledge is equal to its declared pledge, $\hat{p}_i=p_i$.
    
Consider a reduction in `minPoolCost` and that the operator declares $c_i=$`minPoolCost`. Note that this assumption contrasts with [Brünjes et al. (2020)](References/papers/reward-sharing-schemes_brunjes-kiayias-et-al_2020.pdf) setting where there is incentive compatibility, i.e., each operator declares their actual cost. However, the heavy concentration at 340 and 170 ADA in the [histogram](fig-min-pool-cost-644) suggests parameter inertia or active competitive optimization rather than truthful cost revelation. 

The next plot shows the effect of a reduction in `minPoolCost` change in the pool operator gross reward.

<p align="center">
<img src="plots/heatmap_operator_reward_c_cases.png" alt="Heatmap Operator Reward when c changes" width="80%">
</p>

The plot shows that a reduction in the declared fixed cost (from $170$ ADA to $75$ ADA) reduces pool operator revenues, with the effect being particularly strong for small pools. This is because the fixed cost plays an important role in operator's revenues. To see this, take

$$
\Pi_i = c_i+(f(\sigma_i,p_i)-c_i)\underbrace{[m_i +(1-m_i)\frac{p_i}{\sigma_i}]}_{s\in[0,1]},
$$

Hence,

$$\Pi_i=sf(\sigma_i,p_i)+(1-s)c_i$, \quad \text{and} \quad $\partial \Pi_i/\partial c_i=(1-s)\geq 0.$$

It follows that the operator's profit drops with a lower $c_i$. A potential consequence is that very small pool operators will not have room to reduce their fixed costs without losing economic viability. How important may this operator profit be? The [histogram](fig-min-pool-cost-644) shows that many pools prefer to stay with $c_i = 340$ ADA instead of reducing it to $170$ ADA and gain competitiveness. The next plot shows the $n=559$ pools that get a reward during epoch 644 (i.e., they produced a block). the plot shows how much reward (in percentage) these operators would lose if they report $170$ ADA instead of $340$ ADA. The figures are considerable. Note that in the first bin there are 86 pools: 64 of them lose exactly 0% because they all have a margin $m_i=100\%$, while 22 do not lose too much rewards $(0,2.5\%).


  

### Delegator return per unit of stake

Reducing the fixed cost increases the net reward that a pool can distribute among its delegators since

$$\frac{f(\sigma_i,p_i)-c_i}{\sigma_i},$$

Next plot illustrates this benefit comparing the net rewards per unit of stake for different $c_i$. For that comparison, let's first define the net rewards per unit of stake:

<p align="center">
<img src="plots/delegator_reward_per_unit_vs_sigma_c_cases.png" alt="Delegator Reward per unit of stake when c changes" width="62%">
</p>

  
The plot suggests that cost reductions have a more significant positive impact on the competitiveness of small pools than on that of large ones. Nevertheless, large pools may still remain more attractive for delegators.

<p align="center">
<img src="plots/heatmap_delegator_reward_c_cases.png" alt="Heatmap Delegator Reward when c changes" width="80%">
</p>


### Behavioral and equilibrium effects

Changing $c_{\min}$ does not modify gross rewards $f(\sigma_i,p_i)$ directly, but it changes feasible declared costs $c_i$, which feed into pool desirability, operator revenue, and participation constraints. The equilibrium forces are therefore mostly mediated by redelegation and strategic pool-level adjustments.

#### Rational behavior

We start from a frictionless non-myopic benchmark (consistent with the reward-sharing game): forward-looking delegators and operators, truthful cost declaration ($c_i=\hat c_i$), and binding floor $c_i\ge c_{\min}$.

For competitive ranking, use

$$
P_i(c_{\min})=f(z_0,p_i)-c_i,
\qquad
D_i(c_{\min})=(1-m_i)\,[P_i(c_{\min})]_+.
$$

If the floor binds for pool $i$ (that is, $c_i=c_{\min}$), then

$$
\frac{\partial P_i}{\partial c_{\min}}=-1,
\qquad
\frac{\partial D_i}{\partial c_{\min}}=-(1-m_i)\,\mathbf 1\{P_i>0\},
$$

so increasing $c_{\min}$ directly lowers desirability for floor-binding pools.

##### Delegators moving stake

Delegators allocate by expected net return per unit stake,

$$
r_i^D=(1-m_i)\frac{\max\{f(\sigma_i,p_i)-c_i,0\}}{\sigma_i}.
$$

With a floor change, a simple reallocation equation is

$$
\Delta\sigma_i^D=\eta\,\sigma_i\big(r_i^D-\bar r^D\big),
\qquad
\sigma_i'=\sigma_i+\Delta\sigma_i^D.
$$

Hence, raising $c_{\min}$ tends to push stake away from small/floor-binding pools (where $c_i/\sigma_i$ is large), while reducing $c_{\min}$ relaxes that pressure.

##### Operators changing pledge, margin, or declared fixed cost

Operator utility remains

$$
U_i=\Pi_i-\hat c_i,
\qquad
\Pi_i=c_i+(f(\sigma_i,p_i)-c_i)\left[m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\right],
$$

with feasibility $c_i\ge c_{\min}$. A reduced-form best response is

$$
(c_i^{\*},m_i^{\*},\hat p_i^{\*})\in\arg\max_{c_i,m_i,\hat p_i}\;U_i\big(c_{\min},\sigma_i'(c_i,m_i,\hat p_i),c_i,m_i,\hat p_i\big)
\quad\text{s.t. }c_i\ge c_{\min}.
$$

When the floor is lowered, some operators use lower $c_i$ to recover delegation; when the floor rises, margin and pledge become relatively more important strategic levers.

##### Entry or exit of pools

Participation constraints should be evaluated at post-redelegation stake:

$$
U_i\big(c_{\min},\sigma_i'\big)\ge 0,
\qquad
U_i^{\text{entry}}\big(c_{\min},\sigma_i'\big)-F_i\ge 0.
$$

This captures both channels: the direct effect of $c_{\min}$ through feasible $c_i$ and the indirect effect through redelegation ($\sigma_i'$). A higher floor may support incumbent revenue per pool but can tighten entry conditions for small newcomers if delegator net returns fall enough.

##### Pool splitting by multi-pool operators

For an MPO controlling $n$ pools,

$$
\Pi^{\text{MPO}}(n)=\sum_{j=1}^{n}\Pi_j\big(c_{\min},\sigma_j',\hat p_j,m_j,c_j\big),
\qquad c_j\ge c_{\min}.
$$

Splitting is attractive if $\Pi^{\text{MPO}}(n+1)-\Pi^{\text{MPO}}(n)>0$. Lower $c_{\min}$ weakens the fixed-cost barrier per additional pool and can strengthen splitting incentives; higher $c_{\min}$ does the opposite.

##### Changes in staking participation

Let total active stake be $S=\sum_i\sigma_i$. A reduced-form aggregate response is

$$
\Delta S=\chi\,\big(\bar r_{\text{exp}}(c_{\min})-r_{\text{alt}}\big),
$$

where $\bar r_{\text{exp}}$ is expected network staking return net of fee/cost pass-through. Because $c_{\min}$ is mostly redistributive within staking, first-order effects are on allocation across pools, with aggregate participation moving mainly through perceived net-return changes.

#### Behavioral deviations from the rational benchmark

We now keep the same five channels but allow market frictions, bounded rationality, and coordination limits.

##### Delegators moving stake

With search and attention frictions, observed migration is dampened:

$$
\Delta\sigma_i^{\text{obs}}=\lambda_i\,\Delta\sigma_i^D,
\qquad 0<\lambda_i<1.
$$

Under this friction, even large changes in $c_{\min}$ can translate into slow redelegation if delegators are inert.

##### Operators changing pledge, margin, or declared fixed cost

Rather than jumping to the optimum, operators partially adjust controls:

$$
c_{i,t+1}=\max\{c_{\min},\;c_{i,t}+\rho_c(c_i^{\*}-c_{i,t})\},
$$
$$
m_{i,t+1}=m_{i,t}+\rho_m(m_i^{\*}-m_{i,t}),
\qquad
\hat p_{i,t+1}=\hat p_{i,t}+\rho_p(\hat p_i^{\*}-\hat p_{i,t}),
$$

with $0<\rho_c,\rho_m,\rho_p\le 1$. This generates transitional dynamics and temporary mispricing after a floor change.

##### Entry or exit of pools

Inertia can be represented by hysteresis thresholds around participation:

$$
U_i(c_{\min},\sigma_i')<-H_i^{\text{exit}},
\qquad
U_i^{\text{entry}}(c_{\min},\sigma_i')>H_i^{\text{entry}},
$$

with $H_i^{\text{entry}},H_i^{\text{exit}}>0$. This allows weak pools to remain active and viable entrants to delay launch, even when rational static constraints indicate immediate adjustment.

##### Pool splitting by multi-pool operators

Include organizational frictions in expansion value:

$$
V^{\text{split}}(n)=\Pi^{\text{MPO}}(n)-K(n),
$$

where $K(n)$ is increasing and convex. A lower floor may still fail to induce extra splits for operators with high coordination costs.

##### Changes in staking participation

If delegators overweight short-run payout changes, participation reacts to a salience-weighted objective:

$$
\Delta S_t=\chi_s\big(r_t-r_{\text{alt},t}\big)+\chi_l\,\mathbb E_t\!\left[\sum_{h\ge 1}\beta^h\big(r_{t+h}-r_{\text{alt},t+h}\big)\right],
$$

with $\chi_s>\chi_l$ under short-term salience. This can amplify short-run participation responses to changes in $c_{\min}$ even when long-run effects are limited.

### Decentralization



### Interaction effects

See the file analysis in the [interaction effects file](Interaction-effects/interaction_effects.md)






