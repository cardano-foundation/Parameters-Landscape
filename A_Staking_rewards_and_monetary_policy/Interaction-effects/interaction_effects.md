# Interaction effects among parameters

## Summary:

**Pros**
1. **$k$ with lower `minPoolCost`:**
   1. Delegator APR improves, particularly for small pools.
   2. The interaction induces redelegation from initially large pools toward smaller ones.
   3. Higher $k$ leaves unsaturated-pool viability largely unchanged.
2. **$k$ with larger $a_0$:**
   1. Higher $k$ tends to favor mid-sized, highly pledged pools near the new saturation point.
   2. A larger $a_0$ reinforces this benefit through the pledge channel.
3. **$a_0$ with lower `minPoolCost`:**
   1. This interaction improves delegator APR, particularly for small pools.
   2. The effect is stronger for highly pledged pools because a larger $a_0$ amplifies the pledge channel.

**Risks**
1. **$k$ with lower `minPoolCost`:**
   1. Small-pool viability is negatively affected if they reduce their declared fixed cost.
   2. Small pools may not reduce their declared fixed cost, so they do not benefit from greater delegator attractiveness and do not attract migration.
2. **$k$ with larger $a_0$:**
   1. The positive effect on highly pledged pools is limited because relatively few pools satisfy the condition.
   2. All other pools are harmed in terms of viability and delegator APR.
3. **$a_0$ with lower `minPoolCost`:**
   1. Higher $a_0$ with lower fixed costs reduces operator viability.
   2. These operators would benefit only if they can attract new delegations.

**Theoretical exercises given the current state**
1. Fixed-cost changes reorder unsaturated-pool rankings more than $a_0$ changes.
2. Higher $k$ alone does not change viability among unsaturated pools.
3. Higher $a_0$ reduces viability among unsaturated pools.

**Policy interpretation**
1. **$k$ with lower `minPoolCost`:** Raising $k$ and lowering declared $c_i$ together improves unsaturated-pool delegator APR, which $k$ alone does not. The same joint change reduces operator viability by more than raising $k$ alone, because a lower $c_i$ reallocates $f_i$ toward members.
2. **$k$ with larger $a_0$:** A higher $a_0$ can reinforce a higher $k$ for well-pledged pools near the new saturation cap, but few pools have that pledge. For the snapshot as a whole, the joint change reduces viability and median APR by more than raising $k$ alone.
3. **$a_0$ with lower `minPoolCost`:** Lowering declared $c_i$ only partly offsets the APR loss from a higher $a_0$; the joint change still leaves median APR below the current snapshot and is harsher on operator viability than either change alone.

## Parameter values at the current state

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


## Increment in $k$ with a reduction in `minPoolCost` ($c_{\min}$)

The individual effects can be found in the corresponding files for [parameter $k$](../k/Incentive_Effects_k.md) and [`minPoolCost`](../minPoolCost/Incentive_Effects_minPoolCost.md).

### Joint parameter mechanics: A design perspective

This section combines a lower minimum fixed cost, $c_{\min}$, with a higher pool target, $k$. In the reward-sharing model, the two parameters act on different margins: $k$ changes the saturation threshold $z_0(k)=1/k$, while $c_{\min}$ changes the feasible declared fixed cost $c_i$.

#### Gross pool rewards $f(\sigma_i,p_i)$

Gross pool rewards are

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\{\sigma_i,z_0\},\quad \widetilde{p}_i=\min\{p_i,z_0\}.
$$

Note that $c_{\min}$ does not enter $f(\cdot)$. Hence, there is no direct combined effect on $f_i$. The [incentive effects of a change in $k$](../k/Incentive_Effects_k.md) analyze the effect of $k$ on $f_i$.

#### Operator gross revenue $\Pi_i$

The pool operator gross revenue function is

$$\Pi_i=\begin{cases} c_i + (f(\sigma_i,p_i)-c_i) \left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], & \text{if } f(\sigma_i,p_i)>c_i, \\ 
f(\sigma_i,p_i), & \text{otherwise} \end{cases}$$

where $\hat{p}_i$ is the operator's active pledge (the stake or delegation owned by the operator). We assume that declared and active pledge coincide, so $p_i=\hat p_i$.

Note that

$$
\frac{\partial \Pi_i}{\partial c_i}=1-s_i\ge 0,\qquad s_i= m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\in[0,1].
$$

After a combined shock ($k\uparrow$, $c_{\min}\downarrow$), will all pools benefit? Suppose a combined shock while $(m_i,\hat p_i,\sigma_i)$ remain fixed, and let

$$
\Delta f_i=f_i' - f_i,
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

Using $s_i=m_i+(1-m_i)q_i$, where $q_i\equiv\hat p_i/\sigma_i=p_i/\sigma_i$ (since we assumed $p_i=\hat p_i$), the equivalent pledge-share threshold is

$$
q_i > q_i^{\*}\equiv\frac{s_i^{\*}-m_i}{1-m_i} =\frac{\frac{-\Delta c_i}{\Delta f_i-\Delta c_i}-m_i}{1-m_i}.
$$

Interpretation: pools far from the initial saturation point can have $\Delta f_i>0$ after $k$ increases, so they may offset the revenue loss from lowering $c_i$. Pools with low $q_i$ (and low effective $s_i$) are less able to offset that loss and are more likely to be harmed by the combined change; they will probably not choose a lower $c_i$ after a reduction in `minPoolCost`.

> *Example:* As a numerical illustration, take the baseline margin $m_i=5\%$ and a binding fixed-cost reduction from $170$ ADA to $75$ ADA, so
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
  <img src="plots/heatmap_operator_reward_pct_k1000_c75_epoch_644.png" alt="Heatmap of the combined effect of minPoolCost and high $k$ in epoch 644" width="62%">
</p>

### Effects given the current state

#### Delegators moving stake

From a purely rational perspective (more precisely, following the model in [Brünjes et al. (2020)](../../References/papers/reward-sharing-schemes_brunjes-kiayias-et-al_2020.pdf)), delegators choose pools based on their desirability $D_i(k)$, which may change when $k$ and $c_i$ change (recall that the former is imposed by the protocol, while the latter is a decision of each pool):

$$
D_i(k, c_i)=(1-m_i)\frac{\max\{f(\sigma_i,p_i;k)-c_i,0\}}{\sigma_i}.
$$

Once $k$ increases, the saturation threshold falls and many pools become oversaturated, so delegators in those pools may have incentives to redelegate. The figure shows the immediate change in pool desirability rankings when $k$ increases from $500$ to $1,000$, before any redelegation occurs. The increase in $k$ alone already produces substantial reshuffling of rankings (Panel A), driven especially by pools that become oversaturated, whose desirability deteriorates sharply relative to unsaturated pools. By comparison, reducing declared fixed costs while keeping $k=500$ has a much smaller effect on the ranking (Panel C). When the increase in $k$ is combined with a common lower fixed cost (Panels B and D), the ranking changes even more. Overall, the figure suggests that the change in the saturation threshold is the main source of the immediate redistribution of pool competitiveness, while changes in fixed costs can further amplify these effects.

<p align="center">
  <img src="plots/desirability_rank_interaction_with_oversaturated_epoch_644.png" alt="Change in desirability when $k$ and minPoolCost change in epoch 644" width="62%">
</p>

To isolate whether a higher $k$ affects pool competitiveness beyond the mechanical effect of creating newly oversaturated pools, the following figure repeats the previous exercise after excluding pools that would be oversaturated under $k=1,000$. This restriction separates the effect of the lower saturation threshold from changes in desirability among pools that remain unsaturated. Panel A shows that, for these pools, increasing $k$ alone leaves the desirability ranking virtually unchanged. This indicates that the large reshuffling observed in the previous figure is driven overwhelmingly by pools crossing the new saturation threshold, rather than by a general change in the relative attractiveness of unsaturated pools. By contrast, reducing declared fixed costs produces substantially more reordering (Panels B–D), showing that changes in $c_i$ can alter relative competitiveness even among pools unaffected by saturation. Thus, the two parameters operate through different channels: a higher $k$ mainly changes rankings through saturation, whereas lower fixed costs can reshuffle rankings more broadly among unsaturated pools.

<p align="center">
  <img src="plots/desirability_rank_interaction_effects_epoch_644.png" alt="Change in desirability when $k$ and minPoolCost change in epoch 644, excluding oversaturated pools" width="62%">
</p>

#### Pools viability. Entry or exit of pools.

We study pool viability given the current distribution of stakes and the pool snapshot. We consider the case of increasing $k$ from $500$ to $1,000$ and reducing `minPoolCost` from $170$ ADA to $75$ ADA.

Pool rewards are determined by the standard function:

$$\Pi_i = \begin{cases} 
 f_i, & f_i \le c_i, \\ 
 c_i + (f_i - c_i)\left[m_i + (1 - m_i)\dfrac{\hat{p}_i}{\sigma_i}\right], & f_i > c_i 
\end{cases}$$

using epoch-$644$ snapshots for margins ($m_i$), total stake ($\sigma_i$), pledge ($\hat{p}_i$), and declared fixed costs ($c_i$). Rather than assuming truthful cost reporting, we assign all pools a uniform operational cost:

$$C^* = \frac{667\text{ USD/month}}{6\text{ epochs/month} \times 0.15\text{ USD/ADA}} \approx 741.1\text{ ADA/epoch}.$$

The next plot shows the pool viability comparison for $k=500$ and $k=1,000$ before any redelegation occurs, under different fixed-cost declarations. Panel A shows only the increase in $k$ with the declared fixed costs from the snapshot. Panel B assumes that all pools declare the minimum feasible fixed cost $c_i=170$ ADA. Panels C and D consider the case in which `minPoolCost` is reduced to $75$ ADA and all pools declare $c_i=75$ ADA. Note the worsening of viability across all groups.

<p align="center">
  <img src="plots/pool_viability_interaction_effects_epoch_644.png" alt="Pool viability under interaction of minPoolCost and $k$ in epoch 644" width="62%">
</p>

| Panel | Scenario | Cover | Losing |
|:---|:---|---:|---:|
| Baseline | $k=500$, declared $c_i$ | 274 | 988 |
| A | $k\to1000$, $c_i$ unchanged | 253 | 1009 |
| B | $k\to1000$, all $c_i\to170$ | 164 | 1098 |
| C | $k=500$, all $c_i\to75$ | 192 | 1070 |
| D | $k\to1000$, all $c_i\to75$ | 152 | 1110 |

Lowering $c_i$ diminishes the operator's net payoff $\Pi_i$ by allocating a larger share of the total fee rewards $f_i$ to delegators, thereby reducing the number of pools capable of covering baseline operating costs $C^*$. Concurrently increasing the target pool parameter $k$ exacerbates this shortfall.

A primary driver of this result is the inclusion of all pools without accounting for stake rebalancing, particularly those that become saturated as $k$ increases. In the absence of redelegation, two competing dynamics emerge. First, newly oversaturated pools suffer a reduction in fee rewards $f_i$ due to saturation caps. Second, in a dynamic setting, this reward dilution would trigger delegators to migrate toward unsaturated pools, potentially restoring their viability.

Isolating pools that remain unsaturated throughout isolates the parameter effects: increasing $k$ alone has no impact on pool viability, whereas lowering $c_i$ systematically reduces the number of pools covering baseline costs $C^*$, as detailed in the table below.

| Panel | Scenario | Covering $C^*$ | Deficit |
|:---|:---|---:|---:|
| Baseline | $k=500$, declared $c_i$ | 137 | 911 |
| A | $k\to1000$, $c_i$ unchanged | 137 | 911 |
| B | $k\to1000$, all $c_i\to170$ | 95 | 953 |
| C | $k=500$, all $c_i\to75$ | 86 | 962 |
| D | $k\to1000$, all $c_i\to75$ | 86 | 962 |

The previous exercise with $C^\*=741.1$ ADA uses one USD opex ($667$/month) and one ADA price ($0.15$). We next consider different ADA prices and operational costs. In particular, the following heatmap uses $P\in\{0.10,0.15,0.25,0.30,0.50\}$ and four monthly opex levels: $58.5$ USD, $256.5$ USD, $667$ USD (our previous baseline), and $1,479$ USD. Cells indicate the number of Active pools with $r=\Pi_i/C^\*(P)\ge 1$; the right panel is the change when $k$ goes from $500$ to $1,000$ and every pool is forced to $c_i=75$.

<p align="center">
<img src="plots/pool_viability_price_cost_heatmap_cover_k_c_epoch_644.png" alt="Active pools with r>=1 vs ADA price and USD opex, k=1000 and c_i=75" width="100%">
</p>

The joint shock is dominated by the $c_i=75$ channel: a lower declared fixed cost reallocates $f_i$ toward members and cuts $\Pi_i$ for every pool with $f_i>c_i$, while raising $k$ only caps newly oversaturated pools. At $58.5$ USD/month and ADA at $0.15$ or higher, the gap vanishes. At $667$ USD/month and $0.15$ USD/ADA, the count falls from $274$ to $152$, more than either shock alone ($-21$ for $k$, $-82$ for $c_i=75$). The loss is largest in the middle of the $C^\\*$ range (for example $-452$ at $256.5$ USD/month and $0.25$ USD/ADA). When $C^*$ is very high (cheap ADA and $1,479$ USD/month), almost nobody has $r\ge 1$ either way, so the joint gap shrinks again.

### Operator and delegator shares when $k=1000$ and $c_i=75$

Declared $c_i$ does not enter $f(\sigma,p)$, so $\sum\Delta f=$-1,463,591$ ADA/epoch is the $k=500\to 1000$ cap. What the lower fee changes is how that $f$ is split. With all $c_i=75$, $\sum\Delta\Pi=$-634,909$ ($43.4\%$ of $\Delta f$) and $\sum\Delta(f-\Pi)=$-828,681$. Pools that remain unsaturated ($n=$1,048$) show the fee channel almost on its own: $\sum\Delta f=$1,906$, while $\sum\Delta\Pi=$-142,618$ and $\sum\Delta(f-\Pi)=$144,523$. Newly oversaturated pools ($n=$207$) still carry the $k$ cut ($\sum\Delta f=$-1,384,907$). At $q<0.01$, most of the loss sits in $f-\Pi$; at $q\geq 0.25$, operators absorb $98.5\%$ of $\Delta f$. The typical Active pool has median $\Delta f=$0.01$ but median $\Delta\Pi=$-163$ and median $\Delta(f-\Pi)=$88$. $191$ pools newly have $f>c$; $144$ still have $f\le 75$.

<p align="center">
<img src="plots/delta_f_split_operator_delegator_k_c_epoch_644.png" alt="Delta f split into operator and delegator rewards, k=1000 and c_i=75" width="90%">
</p>

| Group | $n$ | $\sum\Delta f$ | $\sum\Delta\Pi$ | $\sum\Delta(f-\Pi)$ | $\sum\Delta\Pi/\sum\Delta f$ | median $\Delta f$ | median $\Delta\Pi$ | median $\Delta(f-\Pi)$ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| All Active | $1,262$ | $-1,463,591$ | $-634,909$ | $-828,681$ | $43.4\%$ | $0.01$ | $-163$ | $88$ |
| Remain unsaturated | $1,048$ | $1,906$ | $-142,618$ | $144,523$ | — | $0.02$ | $-93$ | $94$ |
| Newly oversaturated | $207$ | $-1,384,907$ | $-485,947$ | $-898,960$ | $35.1\%$ | $-6,530$ | $-442$ | $-3,918$ |
| Already oversaturated | $7$ | $-80,589$ | $-6,344$ | $-74,245$ | $7.9\%$ | $-11,513$ | $-780$ | $-10,733$ |

#### Changes in staking participation: delegator APR

We measure the effect of an increase in $k$ together with a reduction in `minPoolCost` on delegators' APR using

$$\text{APR}_i \approx 73(1-m_i)\frac{\max\{f(\sigma_i,p_i)-c_i,0\}}{\sigma_i},$$

where $a_0=0.3$, $R=14.9\text{M}$ ADA, and $T=38.8\text{B}$ ADA. We take the epoch-$644$ snapshot and compute the APR after the shocks, i.e., without any redelegation or operator response. Additionally, we focus only on pools that remain unsaturated after the change in $k$, because these are the pools that may attract new delegators or redelegation.

<p align="center">
  <img src="plots/member_apr_interaction_unsaturated_epoch_644.png" alt="Delegator APR under interaction of minPoolCost and $k$ in epoch 644" width="62%">
</p>

In Panel A, the effect on APR is negligible because most post-$k$-increase unsaturated pools sit far below the new saturation point, so shrinking $z_0$ barely moves the pledge term $a_0 \tilde p_i\cdot\frac{\tilde\sigma_i-\tilde p_i(z_0-\tilde\sigma_i)/z_0}{z_0}$, and most also have a low pledge share $p/\sigma$. Large absolute gains in $f$ are rare and concentrated in a few high-pledge pools near the new cap. Thus APR is not invariant to $k$ for unsaturated pools: it improves slightly when pledge is positive, but the improvement is too small to appear in the two-decimal median APR.


## Increments in $k$ and $a_0$

In this part, the discussion combines a higher $a_0$ (to induce more skin in the game) and a higher pool target $k$ (to reduce concentration among larger pools).

The individual effects can be found in the corresponding files for the [parameter k](../k/Incentive_Effects_k.md) and for the [parameter a0](../a0/Incentive_Effects_a0.md).

### Joint parameter mechanics: A design perspective

#### Gross pool rewards $f(\sigma_i,p_i)$

Again, the gross pool rewards are given by:

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\\{\sigma_i,z_0\\},\quad \widetilde{p}_i=\min\\{p_i,z_0\\}.
$$

We next want to  evaluate the interaction effect between a marginal increment in $k$ and a marginal increment in $a_0$. In particular, we want to show that, in some cases, increasing $a_0$ reinforces the effect of a larger $k$.

When the pool remains below the saturation point ($p_i \le \sigma_i < 1/k$), the gross pool reward can be written as:

$$f_i = \frac{R}{1+a_0} \left[ \sigma_i + a_0\left( p_i k(\sigma_i-p_i) + p_i^2\sigma_i k^2 \right) \right],$$

therefore:

$$\frac{\partial f_i}{\partial k} = \frac{Ra_0}{1+a_0} \left[ p_i(\sigma_i-p_i) + 2p_i^2\sigma_i k \right] > 0 \quad (\text{for } p_i > 0).$$

The reason is that those unsaturated pools becomes closer to the saturation point once $k$ increases. 

Next, differentiating with respect to $a_0$ demonstrates that increasing $a_0$ reinforces the positive reward effect of raising $k$:

$$\frac{\partial^2 f_i}{\partial a_0 \partial k} = \frac{R}{(1+a_0)^2} \left[ p_i(\sigma_i-p_i) + 2p_i^2\sigma_i k \right] > 0$$

When the pool's stake exceeds the saturation point but its pledge does not ($p_i < 1/k \le \sigma_i$), the reward function becomes:

$$f_i = \frac{R}{1+a_0} \left( \frac{1}{k} + a_0 p_i \right)$$

Now, the marginal effect of $k$ is negative, but a higher $a_0$ mitigates this decline since:

$$\frac{\partial f_i}{\partial k} = -\frac{R}{(1+a_0)k^2} < 0, \qquad \frac{\partial^2 f_i}{\partial a_0 \partial k} = \frac{R}{(1+a_0)^2k^2} > 0$$

Finally, when both stake and pledge meet or exceed the saturation threshold ($1/k \le p_i \le \sigma_i$), the reward simplifies to 

$$f_i = \frac{R}{k}, \implies \frac{\partial f_i}{\partial k} = \frac{-R}{k^2}<0 \implies \frac{\partial^2 f_i}{\partial a_0 \partial k} = 0,$$ 

and the cross-effect vanishes entirely. 

Summarizing:

$$
\frac{\partial f_i}{\partial k} =  
\begin{cases} 
\frac{Ra_0}{1+a_0} \left[ p_i(\sigma_i-p_i) + 2p_i^2\sigma_i k \right] > 0, & \text{if } \sigma_i < 1/k, \\ 
-\frac{R}{(1+a_0)k^2} < 0,  & \text{if } p_i < 1/k \le \sigma_i, \\ 
\frac{-R}{k^2}<0, & \text{if } 1/k \le p_i \le \sigma_i. 
\end{cases}
$$

$$
\frac{\partial^2 f_i}{\partial a_0 \partial k} =  
\begin{cases} 
\dfrac{R}{(1+a_0)^2} \left[ p_i(\sigma_i-p_i) + 2p_i^2\sigma_i k \right] > 0, & \text{if } \sigma_i < 1/k, \\ 
\dfrac{R}{(1+a_0)^2k^2} > 0,  & \text{if } p_i < 1/k \le \sigma_i, \\ 
0, & \text{if } 1/k \le p_i \le \sigma_i. 
\end{cases}
$$


Previous local derivatives describe marginal adjustments around a fixed state. Now, we want to evaluate pools that cross saturation thresholds. For this purpose, we use a discrete shift from $(k_0, a_{0,0})$ to $(k_1, a_{0,1})$. In particular, consider pools located in the transition interval:

$$\frac{1}{k_1} \le \sigma_i < \frac{1}{k_0}, \qquad k_1 > k_0$$

These pools were unsaturated under $k_0$ but become saturated under $k_1$. Holding $a_0$ constant, the discrete reward difference becomes:

$$\Delta_k f_i = \frac{R}{1+a_0} \left[ \left(\frac{1}{k_1} - \sigma_i\right) + a_0 \left( \min\left\\{p_i, \frac{1}{k_1}\right\\} - A_i \right) \right]$$

where $A_i = p_i k_0(\sigma_i - p_i) + p_i^2 \sigma_i k_0^2$. The first term, $1/k_1 - \sigma_i \le 0$, captures the mechanical loss from the lower saturation ceiling, while the second term captures the pledge incentive.  When $p_i < 1/k_1$:

$$\Delta_k f_i = \frac{R}{1+a_0} \left[ -\left(\sigma_i - \frac{1}{k_1}\right) + a_0 p_i (1 - k_0 \sigma_i)(1 + k_0 p_i) \right]>0$$

if and only if:

$$\sigma_i - \frac{1}{k_1} < a_0 p_i (1 - k_0 \sigma_i)(1 + k_0 p_i)$$

The right-hand side is strictly increasing in $p_i$. Hence, a higher pledge expand the feasible stake interval $\frac{1}{k_1} \le \sigma_i < \bar{\sigma}_i$ over which a pool benefits from increasing $k$, where the upper boundary is defined as:

$$\bar{\sigma}_i = \frac{\frac{1}{k_1} + a_0 p_i (1 + k_0 p_i)}{1 + a_0 k_0 p_i (1 + k_0 p_i)}$$

On the other hand, from the expression for $\Delta_k f_i $, we have $\min\left\\{p_i, 1/k_1\right\\}=1/k_1$ when $p_i \ge 1/k_1$. Thus, in that case, a post-change pledge no longer yields marginal gains (as we saw with the local derivatives).

Supose now a simultaneous increase in $k$ and $a_0$ from $(k_0, a_{0,0})$ to $(k_1, a_{0,1})$. The discrete interaction effect is defined by the difference-in-differences:

$$I_i = \left[ f_i(k_1, a_{0,1}) - f_i(k_0, a_{0,1}) \right] - \left[ f_i(k_1, a_{0,0}) - f_i(k_0, a_{0,0}) \right]$$

For pools crossing the saturation threshold, $I_i > 0$. Increasing $a_0$ mitigates saturation losses or amplifies gains, directly explaining the rightmost panel of the heatmap (see below). In the heatmap, pools with $\sigma_i \ge 1/k_1 \approx 38.8\text{M}$ ADA and high pledge ($p_i \approx 35\text{M}$–$40\text{M}$ ADA) fall within the positive boundary $\sigma_i < \bar{\sigma}_i$, yielding a net gain of $+20\%$ to $+40\%$ (green region) despite reaching the lower saturation threshold. The next plot shows that results by showing the effect of both increments into a pool with different combinations of pledge and delegation.

<p align="center">
  <img src="plots/heatmap_f_k1000_a0_0p6_interaction.png" alt="Heatmap f when k and a0 increase" width="62%">
</p>

### Effects given the current state

As we did for the case with $k$ and `minPoolCost`, we here study the combined effects of $k$ and $a_0$ given the pools snapshot of epoch 644.

#### Delegators moving stake

To assess how parameter changes affect delegator incentives before market participants can respond (redelegations, new pools margins, new pools creation, etc), we evaluate pool desirability rankings using snapshot data from epoch 644. In the full pool population (first figure), increasing $k$ drastically disrupts relative desirability. As highlighted by the red markers, this change is heavily driven by newly oversaturated pools. Conversely, raising $a_0$ alone to $0.6$ (Panel C) preserves relative ranks. This could indicate that large pledges are uncommon, which would limit the reach of $a_0$ to only a few pools

<p align="center">
  <img src="plots/desirability_rank_k_a0_interaction_all_epoch_644.png" alt="Desirability when k and a0 increase, epoch644" width="62%">
</p>

We next isolate pools that remain unsaturated ($\sigma \le z_0(1000)$). Examining this unsaturated cohort ($n = 670$) reveals where delegators would actually find stable incentives during a transition. As shown below, once oversaturated pools are excluded, raising $k$ alone (Panel A) produces a near-perfect rank preservation. Similar for the case of increasing $a_0$, with or without $k$ (Panels B and C). This demonstrates that the severe desirability change triggered by $k$ are mainly localized in pools exceeding the new cap, while the relative attractiveness among unsaturated options remains robust.

<p align="center">
  <img src="plots/desirability_rank_k_a0_interaction_unsaturated_epoch_644.png" alt="Desirability when k and a0 increase only unsaturated pools, epoch644" width="62%">
</p>


#### Pools viability. Entry or exit of pools.

We next assess the static impact over pool viability of parameter changes prior to any operator adjustment or delegator rebalancing. 

Although we already presented the equations above, we present them here again for completeness. Pool rewards comes from:

$$\Pi_i = \begin{cases} 
f_i, & f_i \le c_i, \\ 
c_i + (f_i - c_i)\left[m_i + (1 - m_i)\dfrac{\hat{p}_i}{\sigma_i}\right], & f_i > c_i ,
\end{cases}$$

and the (uniform) actual operational cost is

$$C^* = \frac{667\text{ USD/month}}{6\text{ epochs/month} \times 0.15\text{ USD/ADA}} \approx 741.1\text{ ADA/epoch}.$$

We evaluate using actual margins, pledges, and delegations recorded in the epoch $644$ snapshot. As shown in the figure below, raising from $k=500$ to $k=1000$ in isolation (Panel A) slightly reduces the number of pools covering baseline operating expenditure ($C^* = 741.1\text{ ADA}$) from $274$ to $253$, primarily because newly oversaturated pools face capped rewards. Increasing the pledge influence parameter from $a_0 = 0.3$ to $0.6$ produces a more pronounced contraction: viable pools drop to $239$ under $k=500$ (Panel C) and further to $218$ when combined with $k=1000$ (Panel B). Therefore, in the absence of dynamic redelegation, strengthening pledge requirements (higher $a_0$) harms low-pledge pools while increasing $k$ penalizes pools that cross the lowered saturation cap.

<p align="center">
  <img src="plots/pool_viability_k_a0_interaction_all_epoch_644.png" alt="Pools viability when k and a0 increase, all pools, epoch644" width="62%">
</p>

When restricting the analysis exclusively to the set of pools that remain unsaturated after raising $k$, the direct effect of $k$ disappears entirely. In contrast, increasing pledge influence to $a_0 = 0.6$ (Panels B and C) reduces viable pools identically. This confirms that the viability losses observed from higher $k$ in the full population are strictly an artifact of saturation capping on static stake distributions, whereas increasing $a_0$ exerts a direct, structural penalty on unsaturated pools with insufficient pledge.

<p align="center">
  <img src="plots/pool_viability_k_a0_interaction_unsaturated_epoch_644.png" alt="Pools viability when k and a0 increase, unsaturated pools, epoch644" width="62%">
</p>

The previous exercise with $C^\*=741.1$ ADA uses one USD opex ($667$/month) and one ADA price ($0.15$). We could also consider a grid of different ADA prices and operational costs. The following heatmap varies $P\in\{0.10,0.15,0.25,0.30,0.50\}$ and four monthly opex levels: $58.5$ USD, $256.5$ USD, $667$ USD (our previous baseline), and $1,479$ USD. Cells indicate the number of Active pools with $r=\Pi_i/C^*(P)\ge 1$; the right panel is the change when $k$ goes from $500$ to $1,000$ and $a_0$ goes from $0.3$ to $0.6$.

<p align="center">
<img src="plots/pool_viability_price_cost_heatmap_cover_k_a0_epoch_644.png" alt="Active pools with r>=1 vs ADA price and USD opex, k=1000 and a0=0.6" width="100%">
</p>

At the cost $667$ USD per month and ADA price $0.15$, the count falls from $274$ to $218$ ($\Delta=-56$), which is the sum of the isolated $k$ and $a_0$ gaps ($-21$ and $-35$). The two channels do different things: raising $a_0$ compresses $f_i$ for low-pledge pools through $1/(1+a_0)$, and that tax does not vanish at cheap opex (still $-30$ at $58.5$ USD/month and $0.15$ USD/ADA, as with $a_0$ alone). Raising $k$ is second-order and shows up when $C^\*$ is more demanding, because newly oversaturated pools then drop below a higher ADA coverage threshold. When $C^\*$ is very high (cheap ADA and $1,479$ USD/month), almost nobody covers either way, so the joint gap shrinks again.

### Operator and delegator shares when $k=1000$ and $a_0=0.6$

The two instruments both enter $f$, so unsaturated pools are no longer approximately silent. Among Active pledge-met pools, $\sum\Delta f=$-2,321,080$ ADA/epoch, of which operators take $25.7\%$ ($\sum\Delta\Pi=$-596,496$) and delegators $\sum\Delta(f-\Pi)=$-1,724,584$. Pools that remain unsaturated ($n=$1,048$) now lose $\sum\Delta f=$-452,799$ through $1/(1+a_0)$. Newly oversaturated pools ($n=$207$) still dominate the total ($\sum\Delta f=$-1,772,582$). Low pledge intensity carries most of the cut: $q<0.01$ has $\sum\Delta f=$-1,700,515$, and operators absorb only $10.7\%$ of it; at $q\geq 0.25$, operators absorb $96.4\%$. $\Delta f<0$ for $1,261$ of $1,262$ Active pools. Median $\Delta f=$-253$, median $\Delta\Pi=$-24$, median $\Delta(f-\Pi)=$-126$. $43$ pools cross from $f>c$ to $f\le c$. The joint $\sum\Delta f$ is smaller in magnitude than adding the two isolated $f$ cuts, because $a_0$ and $z_0$ enter $f$ together.

<p align="center">
<img src="plots/delta_f_split_operator_delegator_k_a0_epoch_644.png" alt="Delta f split into operator and delegator rewards, k=1000 and a0=0.6" width="90%">
</p>

| Group | $n$ | $\sum\Delta f$ | $\sum\Delta\Pi$ | $\sum\Delta(f-\Pi)$ | $\sum\Delta\Pi/\sum\Delta f$ | median $\Delta f$ | median $\Delta\Pi$ | median $\Delta(f-\Pi)$ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| All Active | $1,262$ | $-2,321,080$ | $-596,496$ | $-1,724,584$ | $25.7\%$ | $-253$ | $-24$ | $-126$ |
| Remain unsaturated | $1,048$ | $-452,799$ | $-92,168$ | $-360,631$ | $20.4\%$ | $-141$ | $-18$ | $-82$ |
| Newly oversaturated | $207$ | $-1,772,582$ | $-498,298$ | $-1,274,284$ | $28.1\%$ | $-8,610$ | $-307$ | $-6,214$ |
| Already oversaturated | $7$ | $-95,699$ | $-6,031$ | $-89,668$ | $6.3\%$ | $-13,671$ | $-820$ | $-12,851$ |


#### Changes in staking participation. Delegators APR.

To quantify delegator returns under higher saturation targets ($k$) and strengthened pledge influence ($a_0$), we estimate the annual percentage rate for pool $i$ as:

$$\text{APR}_i \approx 73(1-m_i)\frac{\max\{f(\sigma_i,p_i)-c_i,0\}}{\sigma_i},$$

using fixed macroeconomic network values of $R=14.9\text{M}$ ADA and $T=38.8\text{B}$ ADA. We apply these parameter shocks directly to the static distribution of margins, pledges, and delegations recorded at epoch $644$. We abstain of considering potential reallocation fo delegation and other player responses. We consider the subset of pools that remains unsaturated under the increased $k$, as these represent the viable targets that would naturally absorb migrating stake in subsequent rebalancing phases.

Under the baseline pledge influence parameter ($a_0 = 0.3$), doubling the target pool parameter from $k=500$ to $k=1000$ (Panel A) produces zero change in delegator returns, maintaining an identical median APR of $1.69\%$. On the other hand, increasing the pledge influence factor to $a_0 = 0.6$ (Panels B and C) triggers a noticeable systemic decline in delegators profitability: the median APR falls from $1.69\%$ to $1.34\%$. 

<p align="center">
  <img src="plots/member_apr_k_a0_interaction_unsaturated_epoch_644.png" alt="Delegators APR when k and a0 increase, unsaturated pools, epoch644" width="62%">
</p>


## Increment of $a_0$ with reduction of `minPoolCost`

The individual effects can be found in the corresponding files for [parameter $a_0$](../a0/Incentive_Effects_a0.md) and [`minPoolCost`](../minPoolCost/Incentive_Effects_minPoolCost.md).

### Joint parameter mechanics: A design perspective

#### Gross pool rewards $f(\sigma_i,p_i)$

From the gross pool rewards:

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\{\sigma_i,z_0\},\quad \widetilde{p}_i=\min\{p_i,z_0\},
$$

we plot

<p align="center">
  <img src="plots/heatmap_f_a0_0p6_c75_interaction.png" alt="Heatmap when $a_0$ increases and minPoolCost decreases" width="62%">
</p>

### Effects given the current state

As we did for the case with $k$ and `minPoolCost`, we here study the combined effects of increasing $a_0$ and reducing `minPoolCost` given the pool snapshot from epoch $644$.

#### Delegators moving stake

As we did above, we measure the incentive of delegators to migrate to another pool by considering the desirability $D_i$ of each pool. Following the theoretical model, delegators should choose those pools that are more desirable, and we define desirability as

$$
D_i(k, c_i)=(1-m_i)\frac{\max\{f(\sigma_i,p_i;k)-c_i,0\}}{\sigma_i}.
$$

The four-panel comparison demonstrates that standardizing and lowering the declared fixed cost ($c_i$) is a far stronger driver of pool rank mobility than increasing the pledge factor ($a_0$). Simply raising the pledge factor while preserving declared costs (Panel A) leaves relative desirability rankings virtually unchanged. In contrast, reducing fixed costs across the network (Panels B, C, and D) dramatically increases rank dispersion, particularly for mid-tier pools.

<p align="center">
  <img src="plots/desirability_rank_a0_c_interaction_all_epoch_644.png" alt="Desirability under $a_0$ increase and minPoolCost reduction, all pools, epoch 644" width="62%">
</p>

#### Pools viability. Entry or exit of pools.

From the operator perspective, the vast majority of pools already operate at a deficit under baseline conditions, failing to cover basic operational expenses ($C^*$). Increasing the pledge factor $a_0$ further concentrates operator rewards into a small subset of heavily pledged pools, driving more marginal pools into unprofitability. When low fixed costs are used, operator margins contract even more. Therefore, lower declared fixed costs combined with higher pledge ($a_0$) severely degrade the economic viability of smaller and mid-sized stake pool operators, making long-term sustainability attainable only for elite, high-pledge, and heavily delegated operations. Note, however, that our model fixes each pool's declared cost at $c_i=\text{minPoolCost}$. Smaller pools that rely heavily on fixed fee revenue would not voluntarily lower this parameter. Yet, as demonstrated in the next subsection and in the desirability discussion, maintaining higher fixed fees directly depresses delegator APR, eroding the pool's competitive appeal.

<p align="center">
  <img src="plots/pool_viability_a0_c_interaction_all_epoch_644.png" alt="Pool viability under $a_0$ increase and minPoolCost reduction, all pools, epoch 644" width="62%">
</p>

Removing oversaturated pools does not alter the dynamic mentioned above.

<p align="center">
  <img src="plots/pool_viability_a0_c_interaction_unsaturated_epoch_644.png" alt="Pool viability under $a_0$ increase and minPoolCost reduction, unsaturated pools, epoch 644" width="62%">
</p>

As before we now consider the viability question under different ADA prices and operational costs:$P\in\{0.10,0.15,0.25,0.30,0.50\}$, $C^\*\in\{58.5,256.5, 667, 1,470\}$ USD.

<p align="center">
<img src="plots/pool_viability_price_cost_heatmap_cover_a0_c_epoch_644.png" alt="Active pools with r>=1 vs ADA price and USD opex, a0=0.6 and c_i=75" width="100%">
</p>

This joint shock is again dominated by $c_i=75$, with $a_0$ adding a smaller widespread tax on low-pledge $f_i$. At $58.5$ USD/month and ADA at $0.15$ or higher, the $c_i$ gap vanishes and only the $a_0$ gap remains ($-30$ at $0.15$ USD/ADA). The loss is largest in the middle of the $C^\*$ range (for example $-490$ at $256.5$ USD/month and $0.30$ USD/ADA). When $C^*$ is very high, almost nobody covers either way, so the joint gap shrinks again.

### Operator and delegator shares when $a_0=0.6$ and $c_i=75$

$k$ is unchanged, so there is no saturation regrouping. $\sum\Delta f=$-1,085,986$ ADA/epoch is the $a_0=0.3\to 0.6$ compression of $f$; every Active pledge-met pool has $\Delta f<0$. Setting all $c_i=75$ then reallocates what remains: $\sum\Delta\Pi=$-355,704$ ($32.8\%$ of $\Delta f$) and $\sum\Delta(f-\Pi)=$-730,282$. For the typical pool, median $\Delta f=$-230$ and median $\Delta\Pi=$-247$, while median $\Delta(f-\Pi)=$0$, because the lower fee offsets the delegator share of the $a_0$ tax in many pools. Most of the $f$ cut is still at $q<0.01$ ($\sum\Delta f=$-866,964$, $\sum\Delta\Pi=$-214,389$). Pools that already declare $c_i=340$ ($n=$744$) account for $\sum\Delta f=$-719,462$ and $\sum\Delta\Pi=$-264,818$. $169$ pools newly have $f>c$; $166$ still have $f\le 75$.

<p align="center">
<img src="plots/delta_f_split_operator_delegator_a0_c_epoch_644.png" alt="Delta f split into operator and delegator rewards, a0=0.6 and c_i=75" width="90%">
</p>

| Group | $n$ | $\sum\Delta f$ | $\sum\Delta\Pi$ | $\sum\Delta(f-\Pi)$ | $\sum\Delta\Pi/\sum\Delta f$ | median $\Delta f$ | median $\Delta\Pi$ | median $\Delta(f-\Pi)$ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| All Active | $1,262$ | $-1,085,986$ | $-355,704$ | $-730,282$ | $32.8\%$ | $-230$ | $-247$ | $0.00$ |
| $q<0.01$ | $638$ | $-866,964$ | $-214,389$ | $-652,575$ | $24.7\%$ | $-858$ | $-272$ | $-454$ |
| $0.01\leq q<0.25$ | $433$ | $-141,893$ | $-66,579$ | $-75,314$ | $46.9\%$ | $-82$ | $-105$ | $0.00$ |
| $q\geq 0.25$ | $191$ | $-77,129$ | $-74,736$ | $-2,393$ | $96.9\%$ | $-42$ | $-72$ | $0.00$ |
| $c_i=340$ | $744$ | $-719,462$ | $-264,818$ | $-454,644$ | $36.8\%$ | $-379$ | $-267$ | $0.00$ |
| $c_i=170$ | $382$ | $-246,463$ | $-45,088$ | $-201,376$ | $18.3\%$ | $-91$ | $-95$ | $0.00$ |
| other $c_i>75$ | $136$ | $-120,061$ | $-45,799$ | $-74,262$ | $38.1\%$ | $-396$ | $-322$ | $0.00$ |

#### Changes in staking participation: delegator APR

These four boxplots illustrate how adjusting the pledge influence factor ($a_0$) and pool fixed costs ($c_i$) affect delegator returns (APR) under fixed Cardano network parameters ($k=500$, $R=14.97\text{M}$, $T=38.76\text{B}$).

Increasing the pledge influence factor from $a_0=0.3$ to $a_0=0.6$ without adjusting pool costs causes a substantial decline in overall delegator APR (Panel A): the median falls from $1.83\%$ to $1.46\%$. Because higher $a_0$ values shift reward distribution toward operator pledge, this drop suggests that the majority of active pools do not hold enough pledge to benefit from the change, thereby penalizing delegator returns across most pools under current configurations.

Conversely, lowering pool fixed costs counteracts this decline: reducing fixed costs across all pools to $c_i=75$ under the current $a_0$ increases median APR from $1.83\%$ to $1.96\%$ (Panel C), while pairing low fixed costs ($c_i=170$ or $c_i=75$) with $a_0=0.6$ cushions the yield drop for delegators (Panels B and D; medians $1.53\%$ and $1.58\%$).

<p align="center">
  <img src="plots/member_apr_a0_c_interaction_unsaturated_epoch_644.png" alt="Delegator APR when $a_0$ increases and minPoolCost decreases, unsaturated pools, epoch 644" width="62%">
</p>

