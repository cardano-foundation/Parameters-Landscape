# Incentive effects of changing k
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

$k$ denotes the target number of economically relevant stake pools. It is not a hard cap on the number of pools that may be registered; rather, it shifts the reward function through the saturation threshold

$$
z_0 = \frac{1}{k}.
$$

The motivation is to limit the increasing-returns pattern that appears when rewards are proportional to stake. Below saturation, delegation tends to increase the reward available to the pool and to the delegators. Above saturation, additional stake no longer increases gross rewards, which weakens the advantage of very large pools. 


Choosing $k$ therefore trades off decentralization and economic viability. A higher $k$ lowers the saturation threshold ($z_0$), reducing the stake and pledge required for a pool to become competitive and making room for more economically relevant pools. However, it also lowers the maximum gross reward available to each saturated pool, which may weaken operator profitability. A lower $k$ has the opposite effect: it allows larger rewards per pool and may improve viability, but reaching saturation—and making pledge fully effective—requires more stake and substantially more pledge, favoring larger or better-capitalized operators.




## Direct mechanical effects 
In this section we consider the direct effects of changing the parameter while holding everything else equal (ceteris paribus).

The parameter change considered here is an increase in $k$, which lowers the saturation threshold and therefore changes the reward profile before any behavioral response occurs.


### Gross pool rewards
  
The following plots illustrate the impact of the increment in $k$ on the reward function,

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right].$$

where
 
$$\tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\}.$$
  
The figure illustrates the impact of increasing $k$ from $500$ (left) to $1000$ (center), with the net difference shown on the right. Each heatmap displays the gross reward $f(\sigma_i, p_i)$ for a pool as a function of its delegation ($x$-axis) and pledge ($y$-axis), where darker green indicates higher rewards. Doubling $k$ halves the saturation threshold from $z_0 = 77\text{M ADA}$ to $z_0 = 38.5\text{M ADA}$ (marked by the vertical line in the center plot). Consequently, rewards for pools exceeding $38.5\text{M ADA}$ decrease—reflected in the muted green tones—because their rewards are capped earlier. The difference plot on the right highlights this shift: while larger pools experience reduced yields, medium-sized pools operating near the new $z_0$ now occupy the optimal reward band.
  
<p align="center">
  <img src="plots/heatmap_reward_function_k_cases.png" alt="Heatmap Reward function when k changes" width="80%">
</p>

### Operator gross revenue

While gross rewards provide a baseline, a pool operator's actual earnings depend on their specific fee structure. To capture this, the following figure plots net operator rewards under a fixed cost of $c_i = 170\text{ ADA}$ and a margin of $m_i = 5\%$. As in the previous figure, the panels compare $k = 500$ (left) and $k = 1000$ (center) across total delegation ($x$-axis) and pledge ($y$-axis), with the rightmost panel showing the net change between the two scenarios. 

<p align="center">
<img src="plots/heatmap_operator_reward_k_cases.png" alt="Heatmap Operator Reward when k changes" width="80%">
</p>

Because the protocol reimburses operators for their declared fixed costs ($c_i$), incorporating fixed-cost income mitigates the impact of increasing $k$, particularly for pools with low pledge, even if the pool becomes oversaturated. This mitigation occurs because fixed costs are deducted from the total pool rewards before they are distributed to delegators—effectively reducing the delegators' share of pool rewards, which are given by $f(\sigma_i, p_i; z_0) - c_i$. Hence, pools with lower pledge (and higher proportion of third-party delegations) redirect a larger relative portion of delegator returns toward the operator.

### Delegator return per unit of stake

Maintaining the same delegation ($x$-axis) and pledge ($y$-axis) layout as the previous figures, the following plot maps the immediate shift in delegator yield per unit of stake prior to any behavioral rebalancing (such as stake migration). As predicted by our analytical model, delegators remaining in now-oversaturated pools—those to the right of the vertical $z_0 = 38.5\text{M ADA}$ threshold—suffer immediate yield losses. Conversely, delegators aligned with pools operating near the new saturation boundary experience yield gains, with the most pronounced improvements concentrated in the high-pledge region along the upper area of the plot.

<p align="center">
<img src="plots/heatmap_delegator_reward_k_cases.png" alt="Heatmap Delegator Reward when k changes" width="80%">
</p>


### Oversaturated stake

Denote the per-pool saturation point as $z_0(k) = \frac{T}{k},$ and the saturation level as

$$s_i(k) = \frac{\sigma_i}{z_0(k)} = \frac{\sigma_i k}{T}.$$

Pool $i$ is oversaturated if $s_i(k)>1$, i.e., $\sigma_i>z_0(k)$. The aggregate stake/delegation above saturation is calculated with
  
$$E(k) = \sum_{i : \sigma_i>0} \max\\{\sigma_i - z_0(k),0\\}.$$

The tables below summarize how doubling $k$ drives oversaturation, quantifying both the affected pool count and the aggregate delegation impacted by the change.
  
| Quantity | Value |
| :--- | ---: |
| $T$  | $38.8B$ ADA |
| $S$  | $21.4B$ ADA|
| $S / T$ | 55.2% |
| Pools with $\sigma_i>0$ | 2,694 |

| Quantity | $k=500$ | $k=1000$ | 
| :--- | ---: | ---: | 
| $z_0(k)$ (M ADA) | 77.5 | 38.8 |
| Oversaturated pools (count) | 7 | 211 | 
| Oversaturated pools (% of pools) | 0.26% | 7.8% | 
| $E(k)$ - Stake above saturation (B ADA) | 0.08 | 4.79 | 
| $E(k)$ (% of $S$) | 0.4% | 22.4% | 


### Reward-pot and treasury flows

Raising $k$ does not have a direct mechanical effect in the total size of the reward pot or the treasury's share. It only changes how the rewards are split among pools, which may affect (due to second order effects, like changes in the staking level) how much is actually paid out.

## Past Evidence

As past evidence of a change in $k$, there is the realized historical jump ($150\rightarrow500$, i.e., $3.33\times$) around epoch $228$. This section collects data about the consequence of that change. It is important to note that the consequences and behaviors observed in that jump do not need to replicate in a new one, since market conditions and sentiments may differ. 

Next, the section reports oversaturated-pool counts and stake above saturation $E(k)$ using the same definitions introduced in **Oversaturated stake** above:

  
$$E(k) = \sum_{i : \sigma_i>0} \max\\{\sigma_i - z_0(k),0\\}.$$

| Quantity | Epoch 228 | Epoch 285 |
| :--- | ---: | ---: |
| $T$ | 32.04B ADA | 33.03B ADA |
| $S$ | 17.35B ADA | 23.16B ADA |
| $S / T$ | 54.2% | 70.1% |
| Pools with $\sigma_i>0$ | 1,161 | 2,813 |

| Quantity | Epoch 228, $k=150$ | Epoch 228, $k=500$ | Epoch 285, $k=500$ |
| :--- | ---: | ---: | ---: |
| $z_0(k)$ (M ADA) | 213.58 | 64.07 | 66.06 |
| Oversaturated pools (count) | 0 | 109 | 4 |
| Oversaturated pools (% of pools) | 0.00% | 9.39% | 0.14% |
| $E(k)$ - Stake above saturation (B ADA) | 0.00 | 6.14 | 0.02 |
| $E(k)$ (% of $S$) | 0.00% | 35.41% | 0.09% |


Main observations from epoch $228$:

- Before the change ($k=150$), oversaturation was effectively zero.
- The historical $3.33\times$ jump to $k=500$ moved the system to $109$ oversaturated pools and $E(k)=6.14$B ADA ($35.71\%$ of $S$).

<p align="center">
  <img src="plots/unsaturated_delegation_by_stake_bin_228_285.png" alt="Unsaturated Pools change delegation when k raises" width="80%">
</p>

<p align="center">
  <img src="plots/unsaturated_mi_ci_change_counts_228_285.png" alt="Unsaturated Pools change in parameters when k raises" width="80%">
</p>


**Evidence on decentralization**

Nakamoto $N$: minimum number of pools (ranked by active stake) whose aggregate exceeds 50% of total active stake.

| Epoch | Nakamoto \(N\) | Snapshot pools | Aggregate stake of \(N\) | Total active stake | Share | Min-agg declared pledge | Min-agg active pledge |
|------:|---------------:|---------------:|-------------------------:|-------------------:|------:|------------------------:|----------------------:|
| 228 | 57 | 1,161 | 8.76B ADA | 17.35B ADA | 50.48% | 59.0M ADA | 101.6M ADA |
| 285 | 195 | 2,813 | 11.59B ADA | 23.16B ADA | 50.06% | 1.09B ADA | 1.23B ADA |

## Behavioral and equilibrium effects

This section identifies potential behavioral (or second-order) effects—primarily concerning delegator and operator decisions. To provide a clearer breakdown, the section below adopts a more granular approach rather than relying on these two broad categories.
    
### Rational behavior

We first discuss the equilibrium effects of increasing $k$ ($500 \to 1000$) following [Brünjes et al. (2020)](References/papers/reward-sharing-schemes_brunjes-kiayias-et-al_2020.pdf). Doubling $k$ halves the pool saturation threshold:

$$z_0(k) = \frac{1}{k}: \qquad \frac{1}{500} \longrightarrow \frac{1}{1000}$$, 

The maximum potential gross pool reward is given by:

$$f_i(\sigma_i=z_0,p_i) = \frac{R}{1+a_0} \left[ z_0 + a_0 \min\\{p_i, z_0\\} \right].$$

The active set of pools $G_{1000}$ consists of the top $1,000$ operators ranked by their desirability $(1-m_i)(f_i(z_0,p_i)-c_i)$. The following dynamics is induced:
- Stake Reallocation: Delegators shift stake to saturate all $i \in G_{1000}$. Incumbent pools lose half their stake ($\frac{1}{500} \to \frac{1}{1000}$), freeing exactly enough aggregate stake to saturate 500 new pools.
- Staking Participation: Unchanged since the model assumes that there is full active stake $\sum_i ​\sigma_i​ = T$
* **Pledge:** Operators declared as pledge all their their available stake ($p_i = \hat{p}_i$).
* **Margin:** Operators adjust their margin $m_i$ to remain competitive. The direction of the margin changes are ambiguous as $k$ alters both gross pool rewards and the marginal competitor's profit threshold.
* **Declared Cost:** Truthful reporting remains optimal.
* **Net Entry:** New pools enter in the ecosystem.

This model has several key assumptions:
- Full active stake and frictionless redelegation;
- No switching costs, search frictions, reward uncertainty, or externalities;
- Each operator manages at most one pool with stake $p_i \le \frac{1}{1000}$;
- There are sufficiently many potential operators;
- Enough profitable candidates to support the new $k$;

Overall, the stylized equilibrium changes from $500$ pools of size $T/500$ to $1000$ pools of size $T/1000$. Delegation is redistributed, the pool-leader ranking and margins are recalculated, and net pool entry equals $500$. Pool splitting may occur, but an increase in independent operators is not guaranteed. Aggregate staking participation remains unchanged.

In the reality, this benchmark is constrained by market frictions. Several observations show that the assumptions of the model do not hold in reality (however, it should be notice that the equilibrium predicted does not consider the path until reaching it, while a snapshot of the current state could be just a point in that path). 

For instance, only a fraction of $T$ is active stake $S$. With current active stake $S \approx 21.4B$ ADA and $T \approx 38.8B$ ADA, the maximum number of simultaneously saturated pools is bounded by

$$
N_{\text{sat}}^{\max}(k)=\frac{S}{T/k}=\frac{S}{T}k\approx 0.552 k,
$$

which is about $276$ for $k=500$ and about $552$ for $k=1000$. 

    
### Delegators moving stake

After an increment in $k$, several pools will become oversaturated. Yield-sensitive delegators typically leave oversaturated pools for those with available capacity. However, a mechanical increase in oversaturation does not guarantee an immediate or equivalent outflow. A slightly oversaturated pool can remain appealing if it offers lower reward variance, better fixed-cost dilution, or a strong reputation. Furthermore, identifying alternative pools requires effort: spare capacity is often fragmented across many operators, introducing search and coordination friction. Additional barriers—such as switching costs, rational inattention, or brand loyalty—can further delay adjustments, leading to persistent mild oversaturation and herding toward a small subset of pools.

**1. Why a slightly oversaturated pool may remain attractive**

Consider a simplified capped-gross-reward approximation (ignoring pledge and performance differences):

$$g_i(\sigma_i)=\bar{R} \min\\{\sigma_i,z_0\\},$$

where $\bar{R}>0$ is a constant gross reward rate per unit of reward-bearing stake. In this reduced-form approximation, $\bar{R}$ plays the role of $f(\sigma_i,p_i)/\sigma_i$ for a sub-saturated pool when pledge and performance are held fixed. The delegator net return per unit stake is

$$y_i(\sigma_i)=(1-m_i) \frac{\big[g_i(\sigma_i)-c_i\big]_+}{\sigma_i}.$$

When the pool is below saturation ($\sigma_i<z_0$),

$$y_i(\sigma_i)=(1-m_i)\left(\bar{R}-\frac{c_i}{\sigma_i}\right),$$

so returns rise with size because fixed cost is diluted. When the pool is above saturation ($\sigma_i>z_0$),

$$y_i(\sigma_i)=(1-m_i)\left(\frac{\bar{R}z_0-c_i}{\sigma_i}\right),$$

so returns decline with additional stake because gross rewards are capped at $\bar{R}z_0$. Therefore, a *slightly* oversaturated pool can still dominate a much smaller unsaturated one if fixed-cost dilution and reputation/variance effects remain favorable. The next plot shows this case:

<p align="center">
<img src="plots/slightly_oversaturated_vs_small_pool.png" alt="A slightly oversaturated pool can remain preferred" width="62%">
</p>


<!-- A possible empirical test is to estimate delegation outflows as a function of oversaturation while controlling for expected return, reward variance, margin, fixed cost, pool age, historical performance, and operator reputation. -->

**2. Fragmented capacity and search frictions.**

After $k$ increases, the saturation threshold falls. Define the spare capacity of pool $j$ as

$$q_j=\max\\{z_0-\sigma_j,0\\}.$$

Aggregate spare capacity is

$$Q=\sum_j q_j.$$

However, a delegator cannot move stake into aggregate capacity. They must identify a specific pool that:

1. has enough available capacity;
2. offers an acceptable expected return;
3. satisfies their quality, performance, or reputation requirements.

For a delegator with stake $x_d$, define the set of acceptable pools as

$$A_d(x_d) = \left\\{j : q_j\geq x_d \quad \text{and} \quad U_{dj}\geq U_{di}+\epsilon_d \right\\},$$

where $i$ is the delegator's current pool and $\epsilon_d$ is the minimum improvement required to justify moving.

Delegator-specific usable capacity is therefore

$$Q_d^{use} = \sum_{j\in A_d(x_d)}q_j.$$

This quantity may be much smaller than aggregate capacity $Q$. Spare capacity may be spread across many small pools, some of which:

- cannot absorb the delegator's full stake;
- have high fees or low expected returns;
- have insufficient operating history;
- have high reward variance;
- are difficult to discover.

Suppose that a fraction $\alpha_d$ of the pools inspected by delegator \(d\) are acceptable. After inspecting $n$ pools, the probability of finding at least one acceptable alternative is

$$P_d(n) = 1-(1-\alpha_d)^n,$$

which is increasing in $n$. When spare capacity is highly fragmented, $\alpha_d$ is small, and the delegator must inspect many pools before finding a suitable alternative. However, inspecting/searching is costly.

**Coordination friction**

Suppose several delegators identify the same attractive pool. Its remaining capacity becomes

$$q_j^{\mathrm{remaining}} = q_j-\sum_{d\in D_j}x_d,$$

where $D_j$ is the set of delegators moving to pool $j$.

Delegators may make decisions using the initial value of $q_j$. For an incoming delegation \(x_d\), the relevant return should therefore be evaluated at the post-delegation stake:

$$ y_j(\sigma_j+x_d) = (1-m_j)\,\frac{\big[\bar{R}\min\{\sigma_j+x_d,z_0\}-c_j\big]_+}{\sigma_j+x_d}. $$

However, simultaneous inflows can eliminate the available capacity or push the receiving pool above saturation. This can generate:

- herding toward well-known pools;
- overshooting;
- repeated redelegation;
- unused capacity in less visible pools;
- temporary oscillations around the saturation threshold.

Hence, a pool close to saturation may be highly attractive for a small delegator but unattractive—or unable to accommodate the delegation without oversaturation—for a large delegator or when many small delegators arrive simultaneously to the same pool.

**3. Switching costs, rational inattention, and brand loyalty.**

Let

$$\Delta_d = \max_j U_{dj}-U_{di}$$

denote the maximum utility gain available to delegator $d$ from leaving their current pool $i$ and migrating to the pool $j$.

The delegator switches only when $\Delta_d > \kappa_d,$ where $\kappa_d$ denotes switching costs . Thus, when $\kappa_d>0$, small return improvements do not justify moving.


If $\kappa_d$ is heterogeneous across delegators with cumulative distribution $F_\kappa$, the fraction willing to switch for a gain $\Delta_d$ is $F_\kappa(\Delta_d)$.

Suppose that $a_d\in[0,1]$ denotes the probability that delegator $d$ notices and evaluates the change. Thus, when $a_d<1$, some delegators do not reconsider their delegation. The probability of switching is then

$$P_d(\text{switch}\mid\Delta_d)=a_d F_\kappa(\Delta_d).$$

Aggregate stake leaving pool $i$ is

$$M_i = \sum_{d\in i} \sigma_d a_dF_\kappa(\Delta_d),$$

and a mechanical increase in oversaturation will not produce an equivalent outflow. 


### Operators changing pledge, margin, or declared fixed cost

After a rise in $k$, pools near or above the new $z_0$ face lower reward per unit of stake at the margin, which intensifies fee competition. To organize operator incentives, let

$$
f_i=f(\sigma_i,p_i),
$$

where $p_i$ is the declared pledge. If $f_i>c_i$, operator gross revenue is

$$
\Pi_i = c_i + (f_i-c_i)\left[m_i + (1-m_i)\frac{\hat p_i}{\sigma_i}\right],
$$

where $\hat p_i$ is active operator pledge and operator utility/profit is

$$
U_i = \Pi_i - \hat c_i.
$$

This makes the main strategic margins explicit:

- **Margin ($m_i$):** holding stake fixed, higher $m_i$ raises operator revenue but reduces delegator return $y_i=(1-m_i)(f_i-c_i)/\sigma_i$. So margin helps short-run extraction but weakens delegation demand.
- **Declared fixed cost ($c_i$):** higher $c_i$ mechanically raises operator take from rewarded pools, but also lowers delegator returns and competitiveness.
- **Pledge ($p_i$, $\hat p_i$):** a higher pledge share increases operator capture ceteris paribus, but under higher $k$ the effective pledge choice is constrained by pool splitting: one pool needs less pledge to be competitive, while multi-pool expansion requires pledge to be spread across more pools.

Hence, after a $k$ increase, we expect heterogeneous operator responses: some pools cut margins/costs to defend delegation, while others increase extraction and accept smaller delegated stake.
  
### Entry or exit of pools

A higher $k$ creates room for more active pools, but it also lowers the per-pool reward ceiling from about $R/500$ to $R/1000$ in the $500\rightarrow1000$ case. Entry is therefore more likely for low-cost operators (or operators with shared infrastructure), while high-cost marginal pools face higher exit risk.

Using $f_i=f(\sigma_i,p_i)$, we summarize entry/exit with an operator participation constraint.

If $f_i>c_i$, operator gross revenue is

$$
\Pi_i = c_i + (f_i-c_i)\left[m_i + (1-m_i)\frac{\hat p_i}{\sigma_i}\right],
$$

and utility is $U_i=\Pi_i-\hat c_i$. Pool $i$ remains active when $U_i\geq 0$, equivalently when $\Pi_i\geq \hat c_i$.

This implies

$$
f_i\geq f_i^E\equiv c_i+\frac{\hat c_i-c_i}{\left[m_i + (1-m_i)\frac{\hat p_i}{\sigma_i}\right]}.
$$

Hence, $f_i^E$ is the minimum gross reward required for viability.

The direct effect of increasing $k$ comes from the reward ceiling. With $z_0(k)=1/k$ (or $T/k$ in ADA units), a useful upper bound is

$$
\bar f(k)\approx\frac{R}{k}.
$$

So a necessary viability condition is $R/k\geq f_i^E$, and a pool-specific limit is

$$
k_i^{\max}=\frac{R}{f_i^E}.
$$

Pools with

$$
\frac{R}{1000}<f_i^E\leq\frac{R}{500}
$$

can be viable under $k=500$ but not under $k=1000$, even if saturated.

This ceiling effect is not the full story, because delegation reallocates after the shock. Let $\sigma_i(k)$ be post-adjustment stake. Then

$$
\Pi_i(k) = c_i + \left[f\big(\sigma_i(k),p_i\big)-c_i\right]\left[m_i+(1-m_i)\frac{\hat p_i}{\sigma_i(k)}\right],
$$

and therefore

$$
U_i(k)=\Pi_i(k)-\hat c_i.
$$

For weak subsaturated pools, incoming delegation can improve viability while $\partial f_i/\partial\sigma_i>0$. Once saturated, $\partial f_i/\partial\sigma_i=0$, so extra stake no longer relaxes the participation constraint.

At equilibrium, if $A(k)$ is the active set,

$$
U_i(k)\geq 0\quad\text{for }i\in A(k),
$$

and non-active pools cannot profitably enter under their best response. The central prediction is therefore: **more active pools, but less than a proportional increase in $k$**, with entry concentrated among low-cost and shared-infrastructure operators rather than necessarily among new independent operators.
    
### Pool splitting by multi-pool operators

MPOs can split stake across additional pools to keep each pool closer to the new, lower $z_0$. This can increase pool count without proportionally reducing operator-level concentration. Splitting is favored by economies of scope, brand portability, and repeated fixed-cost collection, but constrained by extra operating complexity, pledge dilution across pools, and delegator-side search/coordination frictions.
    
### Changes in staking participation

Increasing $k$ does not create a direct incentive for currently unstaked ADA to enter staking. It mainly changes the allocation of stake across pools by lowering the saturation threshold. Therefore, its expected effect on aggregate staking participation is small, while its effect on redelegation patterns may be substantial.
    



## Interaction effects

See the file analysis in the [interaction effects file](Interaction-effects/interaction_effects.md)
