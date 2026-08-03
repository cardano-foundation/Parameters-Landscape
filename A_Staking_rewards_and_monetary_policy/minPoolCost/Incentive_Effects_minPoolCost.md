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

It follows that the operator's profit drops with a lower $c_i$. A potential consequence is that very small pool operators will not have room to reduce their fixed costs without losing economic viability. 


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


## Behavioral and equilibrium effects

Changing $c_{\min}$ does not modify gross rewards $f(\sigma_i,p_i)$ directly, but it changes feasible declared costs $c_i$, which feed into pool desirability, operator revenue, and participation constraints. The equilibrium forces are therefore mostly mediated by redelegation and strategic pool-level adjustments.

### Rational behavior

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

#### Delegators moving stake

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

#### Operators changing pledge, margin, or declared fixed cost

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

When the floor is lowered, some operators use lower $c_i$ to gain delegation. We should expect a stronger competition for delegations by reducing the fixed cost or the margin when reducing the fixed cost is not convenient. 

Actual data shows a different behavior to the one theoretically predicted. We already pointed out that a potential consequence of reducing $c_{min}$ is that very small pool operators will not have room to reduce their fixed costs without losing economic viability. How important may this drop in the operator profit be? The [histogram](fig-min-pool-cost-644) shows that many pools prefer to stay with $c_i = 340$ ADA instead of reducing it to $170$ ADA and gain competitiveness. The next plot shows the $n=559$ pools that get a reward during epoch 644 (i.e., they produced a block). The plot shows how much reward (in percentage) these operators would lose if they report $170$ ADA instead of $340$ ADA. The figures are considerable. Note that in the first bin there are 86 pools: 64 of them lose exactly 0% because they all have a margin $m_i=100\%$, while 22 losses belongs to the range $(0,2.5\%).

Empirical data reveals behavior that diverges from theoretical predictions. As previously noted, a lower declared fixed cost may make small pools more attractive for delegators but they may find it difficult to reduce their $c_i$ without compromising their economic viability. How significant is this potential loss in operator margin? As illustrated in the [histogram](fig-min-pool-cost-644), many operators choose to retain $c_i = 340\text{ ADA}$ rather than lowering it to $170\text{ ADA}$ to gain competitive yield for delegators. To quantify the financial impact, the subsequent plot analyzes the set of $n = 559$ reward-receiving pools in epoch 644 (i.e., those that produced at least one block). It plots the percentage loss in operator rewards resulting from a reduction to $170\text{ ADA}$. The revenue impact is substantial. Notably, the first bin contains 86 pools: 64 experience exactly a $0\%$ loss due to setting a margin of $m_i = 100\%$, while the remaining 22 pools incur losses within the $(0, 2.5\%]$ range.

<p align="center" id="fig-loss-reward-hist-644">
  <img src="plots/fixed_cost_340_to_170_loss_hist_epoch_644.png" alt="Histogram loss 340 to 170 epoch 644" width="62%">
</p>

The subsequent plot demonstrates that pools adopting the lowest allowable fixed cost ($170\text{ ADA}$) tend to hold significantly higher delegation levels. Conversely, nearly $54\%$ of pools retaining $340\text{ ADA}$ command less than $100\text{k ADA}$ in stake, compared to only $21\%$ among those setting $170\text{ ADA}$.

<p align="center" id="fig-bubble-c-versus-size">
  <img src="plots/fixed_cost_170_vs_340_stake_bubbles_epoch_644.png" alt="Bubbles fixed costs versus size" width="62%">
</p>

The theoretical model also predicts intensified competition in margins ($m_i$) following a reduction in $c_{min}$. However, as shown in the next plot, this price competition is mainly observed among pools declaring $c_i = 170\text{ ADA}$. In contrast, many pools retaining $340\text{ ADA}$ continue to charge high margins. Despite commanding low delegation levels, these operators show no tendency to lower their margins to improve their attractivness for delegators.

<p align="center" id="fig-bubble-c-versus-margin">
  <img src="plots/fixed_cost_margin_bubbles_epoch_644.png" alt="Bubbles fixed costs versus margin" width="62%">
</p>

As an intriguing side note, in the preceding figures—[fixed cost versus stake size](id="fig-bubble-c-versus-size") and [fixed cost versus size](fig-bubble-c-versus-margin)—the total number of pools choosing the minimum allowable fixed cost ($170\text{ ADA}$) approaches $500$, aligning remarkably well with the target pool parameter $k$.

#### Entry or exit of pools

Entry or exit can be analyzed in two layers: first, a direct viability threshold in expected rewards (or expected blocks), and second, the redelegation channel that shifts pools across that threshold.

Using

$$
U_i=\Pi_i-\hat c_i,
\qquad
\Pi_i=c_i+(f(\sigma_i,p_i)-c_i)\left[m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\right],
$$

define

$$
s_i\equiv m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\in[0,1].
$$

For the region $f(\sigma_i,p_i)>c_i$, expected viability is

$$
\mathbb E[U_i]\ge 0
\iff
\mathbb E[f_i]\ge f_i^{\star}
\equiv
\frac{\hat c_i-(1-s_i)c_i}{s_i}.
$$

If we write expected gross reward as $\mathbb E[f_i]=\bar r_{\text{blk}}\,\lambda_i$ with $\lambda_i=\mathbb E[B_i]$ (expected blocks per epoch), then

$$
\lambda_i\ge \lambda_i^{\star}
\equiv
\frac{\hat c_i-(1-s_i)c_i}{s_i\,\bar r_{\text{blk}}}.
$$

Under the rational benchmark used in this section (truthful costs, $c_i=\hat c_i$, and floor-binding pools $c_i=c_{\min}$), this simplifies to

$$
f_i^{\star}=c_i,
\qquad
\lambda_i^{\star}=\frac{c_i}{\bar r_{\text{blk}}}.
$$

Using values close to the examples in Lopez de Lara-style calibrations (as in this repository: $R\approx 15$--$16$M ADA, $k=500$, $a_0=0.3$), take an illustrative average reward per produced block of $\bar r_{\text{blk}}\approx 700$ ADA. Then, for a floor-binding truthful-cost pool:

$$
\lambda_i^{\star}(c_i=170)=\frac{170}{700}\approx 0.243
\quad\text{blocks/epoch},
$$

$$
\lambda_i^{\star}(c_i=75)=\frac{75}{700}\approx 0.107
\quad\text{blocks/epoch}.
$$

So the direct threshold drops by about $56\%$ when $c_{\min}$ moves from $170$ to $75$ ADA. In pure threshold terms (holding stake fixed), this points to more entry / less exit.

If we also map this to stake using $\lambda_i\approx N_{\text{blk}}\,\sigma_i/S$ with an illustrative $N_{\text{blk}}=21{,}600$ active slots/epoch and $S\approx 21.4$B ADA, the break-even stake moves from roughly

$$
\sigma_i^{\star}(170)\approx 0.243\cdot\frac{21.4\text{B}}{21{,}600}\approx 241\text{k ADA}
$$

to

$$
\sigma_i^{\star}(75)\approx 0.107\cdot\frac{21.4\text{B}}{21{,}600}\approx 106\text{k ADA}.
$$

So, holding delegation fixed, reducing $c_{\min}$ lowers the direct break-even threshold and should mechanically favor more entry / less exit.

Now include redelegation. Participation constraints should be evaluated at post-redelegation stake:

$$
U_i\big(c_{\min},\sigma_i'\big)\ge 0,
\qquad
U_i^{\text{entry}}\big(c_{\min},\sigma_i'\big)-F_i\ge 0.
$$

Equivalently, with the block-based view, viability depends on $\lambda_i'$ after stake reallocation, not only on the direct change in $\lambda_i^{\star}$. Hence, a lower floor can reduce thresholds but still produce exits for pools that lose stake and drift below $\lambda_i^{\star}$, while attracting entry/survival for pools that gain stake. This is why the net entry-versus-exit prediction is ultimately an equilibrium question, even though the direct threshold effect of $c_{\min}\downarrow$ is entry-friendly under truthful-cost assumptions.

#### Pool splitting by multi-pool operators

For an MPO controlling $n$ pools,

$$
\Pi^{\text{MPO}}(n)=\sum_{j=1}^{n}\Pi_j\big(c_{\min},\sigma_j',\hat p_j,m_j,c_j\big),
\qquad c_j\ge c_{\min}.
$$

Splitting is attractive if $\Pi^{\text{MPO}}(n+1)-\Pi^{\text{MPO}}(n)>0$. Lower $c_{\min}$ weakens the fixed-cost barrier per additional pool and can strengthen splitting incentives; higher $c_{\min}$ does the opposite.

#### Changes in staking participation

Let total active stake be $S=\sum_i\sigma_i$. A reduced-form aggregate response is

$$
\Delta S=\chi\,\big(\bar r_{\text{exp}}(c_{\min})-r_{\text{alt}}\big),
$$

where $\bar r_{\text{exp}}$ is expected network staking return net of fee/cost pass-through. Because $c_{\min}$ is mostly redistributive within staking, first-order effects are on allocation across pools, with aggregate participation moving mainly through perceived net-return changes.

### Behavioral deviations from the rational benchmark

We now keep the same five channels but allow market frictions, bounded rationality, and coordination limits.

#### Delegators moving stake

With search and attention frictions, observed migration is dampened:

$$
\Delta\sigma_i^{\text{obs}}=\lambda_i\,\Delta\sigma_i^D,
\qquad 0<\lambda_i<1.
$$

Under this friction, even large changes in $c_{\min}$ can translate into slow redelegation if delegators are inert.

#### Operators changing pledge, margin, or declared fixed cost

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

#### Entry or exit of pools

Inertia can be represented by hysteresis thresholds around participation:

$$
U_i(c_{\min},\sigma_i')<-H_i^{\text{exit}},
\qquad
U_i^{\text{entry}}(c_{\min},\sigma_i')>H_i^{\text{entry}},
$$

with $H_i^{\text{entry}},H_i^{\text{exit}}>0$. This allows weak pools to remain active and viable entrants to delay launch, even when rational static constraints indicate immediate adjustment.

#### Pool splitting by multi-pool operators

Include organizational frictions in expansion value:

$$
V^{\text{split}}(n)=\Pi^{\text{MPO}}(n)-K(n),
$$

where $K(n)$ is increasing and convex. A lower floor may still fail to induce extra splits for operators with high coordination costs.

#### Changes in staking participation

If delegators overweight short-run payout changes, participation reacts to a salience-weighted objective:

$$
\Delta S_t=\chi_s\big(r_t-r_{\text{alt},t}\big)+\chi_l\,\mathbb E_t\!\left[\sum_{h\ge 1}\beta^h\big(r_{t+h}-r_{\text{alt},t+h}\big)\right],
$$

with $\chi_s>\chi_l$ under short-term salience. This can amplify short-run participation responses to changes in $c_{\min}$ even when long-run effects are limited.

## Decentralization



## Interaction effects

See the file analysis in the [interaction effects file](Interaction-effects/interaction_effects.md)






