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


# k with minPoolCost ($c_{\min}$)

## Direct combined mechanical effects

The discussion combines a lower minimum fixed cost, $c_{\min}$, with a higher pool target, $k$. In the reward-sharing model, the two parameters act on different margins: $k$ changes the saturation threshold $z_0(k)=1/k,$ while $c_{\min}$ changes the feasible declared fixed cost $c_i$. 

### Gross pool rewards $f(\sigma_i,p_i)$

Gross pool rewards are

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\\{\sigma_i,z_0\\},\quad \widetilde{p}_i=\min\\{p_i,z_0\\}.
$$

Note that $c_{\min}$ does not enter $f(\cdot)$. Hence, there is not direct combined effect over $f_i$. The [incentive effects of a change in k](k/Incentive_Effects_k.md) analyses the change of $k$ over $f_i$. 

### Operator gross revenue $\Pi_i$

The pool operator gross revenue function is

$$\Pi_i=\begin{cases} c_i + (f(\sigma_i,p_i)-c_i) \left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], & \text{if }  f(\sigma_i,p_i)>c_i, \\ 
f(\sigma_i,p_i), & \text{otherwise} \end{cases}$$

where $\hat{p}_i$ is the operator's active pledge (the stake/delegation owned by the operator). We assume declared and active pledge coincide $p_i=\hat p_i.$

Note that 

$$
\frac{\partial \Pi_i}{\partial c_i}=1-s_i\ge 0,\qquad s_i= m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\in[0,1].
$$


After a combined shock ($k\uparrow$, $c_{\min}\downarrow$), will all pools be benefited? Suppose a combined shock while $(m_i,\hat p_i,\sigma_i)$ remain fixed. and let

$$
\Delta f_i=f_i' - f_i ,
\qquad
\Delta c_i=c_i'-c_i\le 0.
$$

Then

$$
\Delta\Pi_i=s_i\,\Delta f_i+(1-s_i)\,\Delta c_i>0 \quad \iff
s_i(\Delta f_i-\Delta c_i)>-\Delta c_i.
$$

When $\Delta f_i>\Delta c_i$, this gives a threshold on $s_i$:

$$
s_i>s_i^*\equiv\frac{-\Delta c_i}{\Delta f_i-\Delta c_i}.
$$

Using $s_i=m_i+(1-m_i)q_i$ where $q_i\equiv\hat p_i/\sigma_i=p_i/\sigma_i$ (since we assumed $p_i=\hat p_i$), the equivalent pledge-share threshold is

$$
q_i > q_i^{\*}\equiv\frac{s_i^{\*}-m_i}{1-m_i} =\frac{\frac{-\Delta c_i}{\Delta f_i-\Delta c_i}-m_i}{1-m_i}.
$$

Interpretation: pools far from the initial saturation point can have $\Delta f_i>0$ after $k$ increases, so they may offset the revenue loss from lowering $c_i$. Pools with low $q_i$ (and low effective $s_i$) are less able to offset that loss and are more likely to be harmed by the combined change, and they will probably not choose a lower $c_i$ after a reduction in `minPoolCost`.

> *Example:* As a numerical illustration, take the baseline margin $m_i=5\\%$ and a binding fixed-cost reduction from $170$ ADA to $75$ ADA, so
> $$\Delta c_i=75-170=-95\text{ ADA}.$$
> Suppose that, for a given pool below the new saturation point, the direct effect of increasing $k$ from $500$ to $1000$ raises gross rewards by
> $$\Delta f_i=150\text{ ADA}.$$
> Then the operator-revenue threshold becomes
> $$s_i^\*=\frac{95}{150+95}=\frac{95}{245}\approx 0.388,$$
> and, using $m_i=0.05$,
> $$q_i^\*=\frac{0.388-0.05}{0.95}\approx 0.356.$$
> Therefore, under this example, a pool benefits mechanically from the combined shock only if its pledge share satisfies $p_i/\sigma_i=\hat p_i/\sigma_i\gtrsim 35.6\%$. Pools with lower pledge share are still hurt in operator revenue terms, even though their gross reward rises with the higher $k$.

The following heatmap illustrates the previous discussion for different combinations of pledge and delegation.

<p align="center">
  <img src="plots/heatmap_operator_reward_pct_k1000_c75_epoch_644.png" alt="Heatmap combined effect minPoolCost and high k epoch644" width="62%">
</p>


## Behavioral and equilibrium effects

### Delegators moving stake

From a purely rational perspective (more precisely, following the model in [Brünjes et al. (2020)](References/papers/reward-sharing-schemes_brunjes-kiayias-et-al_2020.pdf) ), the delegators choose pools based on pools' desirability $D_i(k)$ that may change when there is a change in $k$ and $c_i$ (recall that, while the former is a change imposed by the protocol, the latter is a decision of each pool):

$$
D_i(k, c_i)=(1-m_i)\frac{\max\\{f(\sigma_i,p_i;k)-c_i,0\\}}{\sigma_i}.
$$

Once $k$ increases, the saturation threshold falls and many pools become oversaturated, so delegators in those pools may have incentives to redelegate. The figure shows the immediate change in pools' desirability rankings when $k$ increases from $500$ to $1,000$, before any redelegation occurs. The increase in $k$ alone already produces substantial reshuffling of the ranking (Panel A), driven especially by pools that become oversaturated, whose desirability deteriorates sharply relative to unsaturated pools. By comparison, reducing declared fixed costs (when `minPoolCost` is reducing and assuming that all pools choose $c_i=$`minPoolCost`) while keeping $k=500$ has a much smaller effect on the ranking (Panel C). When the increase in $k$ is combined with a common lower fixed cost (Panels B and D), the ranking changes even more. Overall, the figure suggests that the change in the saturation threshold is the main source of the immediate redistribution of pool competitiveness, while changes in fixed costs can further amplify these effects.

<p align="center">
  <img src="plots/desirability_rank_interaction_with_oversaturated_epoch_644.png" alt="Change desirability when k and minPoolCost changes epoch644" width="62%">
</p>

To isolate whether a higher $k$ affects pool competitiveness beyond the mechanical effect of creating newly oversaturated pools, the following figure repeats the previous exercise after excluding pools that would be oversaturated under $k=1,000$. This restriction is informative because it separates the effect of the lower saturation threshold from changes in desirability among pools that remain unsaturated. Panel A shows that, for these pools, increasing $k$ alone leaves the desirability ranking virtually unchanged. This indicates that the large reshuffling observed in the previous figure is driven overwhelmingly by pools crossing the new saturation threshold, rather than by a general change in the relative attractiveness of unsaturated pools. By contrast, reducing declared fixed costs produces substantially more reordering (Panels B–D), showing that changes in $c_i$ can alter relative competitiveness even among pools unaffected by saturation. Thus, the two parameters operate through different channels: a higher $k$ mainly changes rankings through saturation, whereas lower fixed costs can reshuffle rankings more broadly among unsaturated pools.

<p align="center">
  <img src="plots/desirability_rank_interaction_effects_epoch_644.png" alt="Change desirability when k and minPoolCost changes epoch644 w/o oversaturated pools" width="62%">
</p>


### Pools viability. Entry or exit of pools.


We study the pools viability given the current distribution of stakes, and pools snapshot. We take the case of increasing $k$ from $500$ to $1,000$, and reducing the `minPoolCost` from $170$ ADA to $75`ADA. 

Pool rewards are determined by the standard function:

$$\Pi_i = \begin{cases} 
f_i, & f_i \le c_i, \\ 
c_i + (f_i - c_i)\left[m_i + (1 - m_i)\dfrac{\hat{p}_i}{\sigma_i}\right], & f_i > c_i 
\end{cases}$$

using epoch 644 snapshots for margins ($m_i$), total stake ($\sigma_i$), pledge ($\hat{p}_i$), and declared fixed costs ($c_i$). Rather than assuming truthful cost reporting, we assign all pools a uniform operational cost:

$$C^* = \frac{667\text{ USD/month}}{6\text{ epochs/month} \times 0.15\text{ USD/ADA}} \approx 741.1\text{ ADA/epoch}$$


The next plot shows the pools' viability comparison for $k=500$ and $k=1,000$ before any redelegation occurs, for different fixed cost declaration. Panel A shows only the increment in $k$ with the declared fixed cost of the snapshot. Panels B assumes all pools declared the minimum feasible fixed cost $c_i=170$ ADA. Panels C-D consider the case in which the `minPoolCost`was reduced to $75$ ADA and that all pools declare $c_i=75$ ADA. Note the worsen in the viability across all groups.

<p align="center">
  <img src="plots/pool_viability_interaction_effects_epoch_644.png" alt="Pools viability interaction minPoolCost and k for e644" width="62%">
</p>


| Panel | Scenario | Cover | Losing |
|:---|:---|---:|---:|
| Baseline | $k=500$, declared $c_i$ | 274 | 1949 |
| A | $k\to1000$, $c_i$ unchanged | 254 | 1969 |
| B | $k\to1000$, all $c_i\to170$ | 165 | 2058 |
| C | $k=500$, all $c_i\to75$ | 193 | 2030 |
| D | $k\to1000$, all $c_i\to75$ | 152 | 2071 |

Lowering $c_i$ diminishes the operator's net payoff $\Pi_i$ by allocating a larger share of the total fee rewards $f_i$ to delegators, thereby reducing the number of pools capable of covering baseline operating costs $C^*$. Concurrently increasing the target pool parameter $k$ exacerbates this shortfall.

A primary driver of this result is the inclusion of all pools without accounting for stake rebalancing, particularly those that become saturated as $k$ increases. In the absence of redelegation, two competing dynamics emerge. First, newly oversaturated pools suffer a reduction in fee rewards $f_i$ due to saturation caps. Second, in a dynamic setting, this reward dilution would trigger delegators to migrate toward unsaturated pools, potentially restoring their viability.

Isolating pools that remain unsaturated throughout isolates the parameter effects: increasing $k$ alone has no impact on pool viability, whereas lowering $c_i$ systematically reduces the number of pools covering baseline costs $C^*$, as detailed in the table below.

| Panel | Scenario | Covering $C^*$ | Deficit |
|:---|:---|---:|---:|
| Baseline | $k=500$, declared $c_i$ | 140 | 1872 |
| A | $k\to1000$, $c_i$ unchanged | 140 | 1872 |
| B | $k\to1000$, all $c_i\to170$ | 99 | 1913 |
| C | $k=500$, all $c_i\to75$ | 90 | 1922 |
| D | $k\to1000$, all $c_i\to75$ | 90 | 1922 |

### Changes in staking participation. Delegators APR

We measure the effect of an increment in $k$ together with a reduction in `minPoolCost` over the delegators' APR using,

$$\text{APR}_i \approx 73(1-m_i)\frac{\max\\{f(\sigma_i,p_i)-c_i,0\\}}{\sigma_i},$$

where $a_0=0.3$, $R=14.9M$ ADA, and $T=38.8B$ ADA. We take the snapshot of epoch 644 and we calculate what would be the APR after the shocks, i.e., without any redelegation and operators response that the shock may trigger. Additionally, we focus only on those pools that remain unsaturated after the change in $k$, which would be the ones that may attract new delegators (or redelegation).

<p align="center">
  <img src="plots/member_apr_interaction_unsaturated_epoch_644.png" alt="Delegators APR interaction minPoolCost and k for e644" width="62%">
</p>


In Panel A, the effect over APR is negligible because most (post-k-increment) unsaturated pools sit far below the new saturation point, so shrinking \(z_0\) barely moves the pledge term $a_0 \tilde p_i\cdot\frac{\tilde\sigma_i-\tilde p_i(z_0-\tilde\sigma_i)/z_0}{z_0}$, and most also have a low pledge share \(p/\sigma\). Large absolute gains in \(f\) are rare and concentrated in a few high-pledge pools near the new cap. Thus APR is not invariant to \(k\) for unsaturated pools—they improve slightly when pledge is positive—but the improvement is too small to appear in the two-decimal median APR.





<!-- ##### Pool splitting by multi-pool operators

For an MPO controlling $n$ pools,

$$
\Pi^{\text{MPO}}(n)=\sum_{j=1}^{n}\Pi_j\big(k,c_{\min},\sigma_j',\hat p_j,m_j,c_j\big),
\qquad c_j\ge c_{\min}.
$$

Splitting is attractive if $\Pi^{\text{MPO}}(n+1)-\Pi^{\text{MPO}}(n)>0$. Raising $k$ increases the pressure to split because it lowers the saturation threshold, while lowering $c_{\min}$ reduces the fixed-cost penalty of maintaining additional pools. The combined reform therefore strengthens split incentives for medium-to-large operators, especially those able to reallocate pledge across multiple pools. -->


# k with a0

In this part, the discussion combines a higher $a_0$ (to induce more skin in the game) and a higher pool target $k$ (to reduce concentration among larger pools).

## Direct combined mechanical effects

### Gross pool rewards $f(\sigma_i,p_i)$

Again, the gross pool rewards are given by:

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\\{\sigma_i,z_0\\},\quad \widetilde{p}_i=\min\\{p_i,z_0\\}.
$$

The next plot shows the effect of both increments into a pools with different combinations of pledge and delegation.

<p align="center">
  <img src="plots/heatmap_f_k1000_a0_0p6_interaction.png" alt="Heatmap f when k and a0 increase" width="62%">
</p>

## Behavioral and equilibrium effects

As we did for the case with $k$ and `minPoolCost`, we here study the combined effects of $k$ and $a_0$ given the pools snapshot of epoch 644.

### Delegators moving stake

To assess how parameter changes affect delegator incentives before market participants can respond (redelegations, new pools margins, new pools creation, etc), we evaluate pool desirability rankings using snapshot data from epoch 644. In the full pool population (first figure), increasing $k$ drastically disrupts relative desirability. As highlighted by the red markers, this change is heavily driven by newly oversaturated pools. Conversely, raising $a_0$ alone to $0.6$ (Panel C) preserves relative ranks. This could indicate that large pledges are uncommon, which would limit the reach of $a_0$ to only a few pools

<p align="center">
  <img src="plots/desirability_rank_k_a0_interaction_all_epoch_644.png" alt="Desirability when k and a0 increase, epoch644" width="62%">
</p>

We next isolate pools that remain unsaturated ($\sigma \le z_0(1000)$). Examining this unsaturated cohort ($n = 684$) reveals where delegators would actually find stable incentives during a transition. As shown below, once oversaturated pools are excluded, raising $k$ alone (Panel A) produces a near-perfect rank preservation. Similar for the case of increasing $a_0$, with or without $k$ (Panels B and C). This demonstrates that the severe desirability change triggered by $k$ are mainly localized in pools exceeding the new cap, while the relative attractiveness among unsaturated options remains robust.

<p align="center">
  <img src="plots/desirability_rank_k_a0_interaction_unsaturated_epoch_644.png" alt="Desirability when k and a0 increase only unsaturated pools, epoch644" width="62%">
</p>


### Pools viability. Entry or exit of pools.

We next assess the static impact over pool viability of parameter changes prior to any operator adjustment or delegator rebalancing. 

Although we already presented the equations above, we present them here again for completeness. Pool rewards comes from:

$$\Pi_i = \begin{cases} 
f_i, & f_i \le c_i, \\ 
c_i + (f_i - c_i)\left[m_i + (1 - m_i)\dfrac{\hat{p}_i}{\sigma_i}\right], & f_i > c_i ,
\end{cases}$$

and the (uniform) actual operational cost is

$$C^* = \frac{667\text{ USD/month}}{6\text{ epochs/month} \times 0.15\text{ USD/ADA}} \approx 741.1\text{ ADA/epoch}.$$

We evaluate  using actual margins, pledges, and delegations recorded in the epoch $644$ snapshot. As shown in the figure below, raising from $k=500$ to $k=1000$ in isolation (Panel A) slightly reduces the number of pools covering baseline operating expenditure ($C^* = 741.1\text{ ADA}$) from $274$ to $254$, primarily because newly oversaturated pools face capped rewards. Increasing the pledge influence parameter from $a_0 = 0.3$ to $0.6$ produces a more pronounced contraction: viable pools drop to $240$ under $k=500$ (Panel C) and further to $219$ when combined with $k=1000$ (Panel B). Therefore, in the absence of dynamic redelegation, strengthening pledge requirements (higher $a_0$) harms low-pledge pools while increasing $k$ penalizes pools that cross the lowered saturation cap.

<p align="center">
  <img src="plots/pool_viability_k_a0_interaction_all_epoch_644.png" alt="Pools viability when k and a0 increase, all pools, epoch644" width="62%">
</p>

When restricting the analysis exclusively to the set of pools that remain unsaturated after raising $k$, the direct effect of $k$ disappears entirely. In contrast, increasing pledge influence to $a_0 = 0.6$ (Panels B and C) reduces viable pools identically. This confirms that the viability losses observed from higher $k$ in the full population are strictly an artifact of saturation capping on static stake distributions, whereas increasing $a_0$ exerts a direct, structural penalty on unsaturated pools with insufficient pledge.

<p align="center">
  <img src="plots/pool_viability_k_a0_interaction_unsaturated_epoch_644.png" alt="Pools viability when k and a0 increase, unsaturated pools, epoch644" width="62%">
</p>


### Changes in staking participation. Delegators APR.

To quantify delegator returns under higher saturation targets ($k$) and strengthened pledge influence ($a_0$), we estimate the annual percentage rate for pool $i$ as:

$$\text{APR}_i \approx 73(1-m_i)\frac{\max\{f(\sigma_i,p_i)-c_i,0\}}{\sigma_i},$$

using fixed macroeconomic network values of $R=14.9\text{M}$ ADA and $T=38.8\text{B}$ ADA. We apply these parameter shocks directly to the static distribution of margins, pledges, and delegations recorded at epoch $644$. We abstain of considering potential reallocation fo delegation and other player responses. We consider the subset of pools that remains unsaturated under the increased $k$, as these represent the viable targets that would naturally absorb migrating stake in subsequent rebalancing phases.

Under the baseline pledge influence parameter ($a_0 = 0.3$), doubling the target pool parameter from $k=500$ to $k=1000$ (Panel A) produces zero change in member returns, maintaining an identical median APR of $1.69\%$. On the other hand, increasing the pledge influence factor to $a_0 = 0.6$ (Panels B and C) triggers a noticeable systemic decline in member profitability: the median APR falls from $1.69\%$ to $1.34\%$. 

<p align="center">
  <img src="plots/member_apr_k_a0_interaction_unsaturated_epoch_644.png" alt="Delegators APR when k and a0 increase, unsaturated pools, epoch644" width="62%">
</p>


# a0 with minPoolCost

## Direct combined mechanical effects
### Gross pool rewards $f(\sigma_i,p_i)$

From the gross pool rewards:

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\\{\sigma_i,z_0\\},\quad \widetilde{p}_i=\min\\{p_i,z_0\\},
$$

we plot

<p align="center">
  <img src="plots/heatmap_f_a0_0p6_c75_interaction.png" alt="Heatmap when a0 increase and minPooCost decreases" width="62%">
</p>


## Behavioral and equilibrium effects.

As we did for the case with $k$ and `minPoolCost`, we here study the combined effects of increasing $a_0$ and reducing `minPoolCost` given the pools snapshot of epoch $644$.

### Delegators moving stake.

<p align="center">
  <img src="plots/desirability_rank_a0_c_interaction_all_epoch_644.png" alt="Desirability a0 increase and minPooCost decreases, all pools, epoch644" width="62%">
</p>

<p align="center">
  <img src="plots/desirability_rank_a0_c_interaction_unsaturated_epoch_644.png" alt="Desirability a0 increase and minPooCost decreases, unsaturated pools, epoch644" width="62%">
</p>

### Pools viability. Entry or exit of pools.

<p align="center">
  <img src="plots/pool_viability_a0_c_interaction_all_epoch_644.png" alt="Pools viability a0 increase and minPooCost decreases, all pools, epoch644" width="62%">
</p>

<p align="center">
  <img src="plots/pool_viability_a0_c_interaction_unsaturated_epoch_644.png" alt="Pools viability a0 increase and minPooCost decreases, unsaturated pools, epoch644" width="62%">
</p>

### Changes in staking participation. Delegators APR.

<p align="center">
  <img src="plots/member_apr_a0_c_interaction_unsaturated_epoch_644.png" alt="Delegators APR when a0 increase and minPooCost decreases, unsaturated pools, epoch644" width="62%">
</p>

