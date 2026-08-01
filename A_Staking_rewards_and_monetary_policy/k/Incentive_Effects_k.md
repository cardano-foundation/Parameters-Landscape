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

## Effects of change in k

The parameter change considered here is an increase in $k$, which lowers the saturation threshold and therefore changes the reward profile before any behavioral response occurs.

### Direct mechanical effects 
In this section we consider the direct effects of changing the parameter while holding everything else equal (ceteris paribus).

#### Gross pool rewards
  
The following plots illustrate the impact of the increment in $k$ on the reward function,

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right].$$

where
 
$$\tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\}.$$
  
The figure illustrates the impact of increasing $k$ from $500$ (left) to $1000$ (center), with the net difference shown on the right. Each heatmap displays the gross reward $f(\sigma_i, p_i)$ for a pool as a function of its delegation ($x$-axis) and pledge ($y$-axis), where darker green indicates higher rewards. Doubling $k$ halves the saturation threshold from $z_0 = 77\text{M ADA}$ to $z_0 = 38.5\text{M ADA}$ (marked by the vertical line in the center plot). Consequently, rewards for pools exceeding $38.5\text{M ADA}$ decrease—reflected in the muted green tones—because their rewards are capped earlier. The difference plot on the right highlights this shift: while larger pools experience reduced yields, medium-sized pools operating near the new $z_0$ now occupy the optimal reward band.
  
<p align="center">
  <img src="plots/heatmap_reward_function_k_cases.png" alt="Heatmap Reward function when k changes" width="80%">
</p>

#### Operator gross revenue

While gross rewards provide a baseline, a pool operator's actual earnings depend on their specific fee structure. To capture this, the following figure plots net operator rewards under a fixed cost of $c_i = 170\text{ ADA}$ and a margin of $m_i = 5\%$. As in the previous figure, the panels compare $k = 500$ (left) and $k = 1000$ (center) across total delegation ($x$-axis) and pledge ($y$-axis), with the rightmost panel showing the net change between the two scenarios. 

<p align="center">
<img src="plots/heatmap_operator_reward_k_cases.png" alt="Heatmap Operator Reward when k changes" width="80%">
</p>

Because the protocol reimburses operators for their declared fixed costs ($c_i$), incorporating fixed-cost income mitigates the impact of increasing $k$, particularly for pools with low pledge, even if the pool becomes oversaturated. This mitigation occurs because fixed costs are deducted from the total pool rewards before they are distributed to delegators—effectively reducing the delegators' share of pool rewards, which are given by $f(\sigma_i, p_i; z_0) - c_i$. Hence, pools with lower pledge (and higher proportion of third-party delegations) redirect a larger relative portion of delegator returns toward the operator.

#### Delegator return per unit of stake

Maintaining the same delegation ($x$-axis) and pledge ($y$-axis) layout as the previous figures, the following plot maps the immediate shift in delegator yield per unit of stake prior to any behavioral rebalancing (such as stake migration). As predicted by our analytical model, delegators remaining in now-oversaturated pools—those to the right of the vertical $z_0 = 38.5\text{M ADA}$ threshold—suffer immediate yield losses. Conversely, delegators aligned with pools operating near the new saturation boundary experience yield gains, with the most pronounced improvements concentrated in the high-pledge region along the upper area of the plot.

<p align="center">
<img src="plots/heatmap_delegator_reward_k_cases.png" alt="Heatmap Delegator Reward when k changes" width="80%">
</p>


#### Oversaturated stake

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


#### Reward-pot and treasury flows

Raising $k$ does not have a direct mechanical effect in the total size of the reward pot or the treasury's share. It only changes how the rewards are split among pools, which may affect (due to second order effects, like changes in the staking level) how much is actually paid out.

### Behavioral and equilibrium effects

This section identifies potential behavioral (or second-order) effects—primarily concerning delegator and operator decisions. To provide a clearer breakdown, the section below adopts a more granular approach rather than relying on these two broad categories.

    
#### Rational behavior

Assuming **forward-looking, non-myopic rational players**—the equilibrium concept used by Brünjes et al.—increasing \(k\) from \(500\) to \(1000\) halves the saturation threshold:

$$z_0 = \frac{1}{500}\longrightarrow\frac{1}{1000}.$$

Pools above the new saturation threshold lose delegation, while additional operators enter or previously marginal pools become competitive.

Provided that operating $1000$ pools remains profitable, stake reallocates toward a new equilibrium with $1000$ saturated pools, each with total stake

$$
\sigma_i=\frac{1}{1000}.
$$

Total pool stake includes both the operator's pledge and outside delegation:

$$
\sigma_i=p_i+\text{delegation}_i.
$$

The selected pool leaders commit their available stake to their pools, while delegators fill the remaining capacity. These pools are therefore saturated in total stake, but they are not generally fully pledged.

The pool leaders are the $1000$ players with the highest profit,

$$
P_i=r\left(\frac{1}{1000},s_i\right)-c_i,
$$

and each leader chooses the highest margin $m_i$ that keeps the pool among the $1000$ most desirable pools.

**Discussion**

The outcome would probably be less clean. Current evidence shows that with $k=500$, there are $\sim 2'600$ pools, most of them far away from saturation levels. Moreover, the actual staking level could saturate only $\sim 275$ pools.

- The maximum gross reward per fully saturated pool falls from $R/500$ to $R/1000$, while operating costs do not fall proportionally. Therefore, the condition under which pools are profitable may be affected.
- As a response, some incumbents would reduce margins, adjust pledge, or open additional pools. Multi-pool operators with shared operating costs would have a particularly strong incentive to split.
- Delegation would not necessarily leave newly oversaturated pools one-for-one. Large pools may remain attractive because they dilute fixed costs better and have established reputations or lower perceived reward variance.
- Consequently, the likely equilibrium is **more pools near the lower saturation threshold, but not necessarily $1000$ independent operators**. It may include persistent oversaturation, operator entry and exit, and substantial pool splitting by existing multi-pool operators.

Thus, increasing $k$ should decentralize **stake across pool registrations**, but its effect on **independent operator concentration** is theoretically ambiguous. Total staking participation may remain approximately unchanged.
    
#### Delegators moving stake

Yield-sensitive delegators typically leave oversaturated pools for those with available capacity. However, a mechanical increase in oversaturation does not guarantee an immediate or equivalent outflow. A slightly oversaturated pool can remain appealing if it offers lower reward variance, better fixed-cost dilution, or a strong reputation. Furthermore, identifying alternative pools requires effort: spare capacity is often fragmented across many operators, introducing search and coordination friction. Additional barriers—such as switching costs, rational inattention, or brand loyalty—can further delay adjustments, leading to persistent mild oversaturation and herding toward a small subset of pools.

**1. Why a slightly oversaturated pool may remain attractive** (based on CIP-50 report)

Consider the simplified capped reward function

$$r_i(\sigma_i)=\frac{f()}{\sigma_i}\min\\{\sigma_i,z_0\\},$$

where $\frac{f()}{\sigma_i}$ is the gross reward generated per unit of stake. Ignoring pledge for simplicity, the expected delegator return per unit of stake is

$$y_i(\sigma_i) = (1-m_i) \frac{r_i(\sigma_i)-c_i}{\sigma_i},$$

provided that $r_i(\sigma_i)>c_i$.

Below saturation,

$$y_i(\sigma_i) = (1-m_i) \left(\frac{f()}{\sigma_i}-\frac{c_i}{\sigma_i} \right),\qquad \sigma_i < z_0.$$

Returns increase with pool size because the fixed cost is distributed across more stake. Above saturation,

$$y_i(\sigma_i) = (1-m_i) \frac{\frac{f()}{\sigma_i} z_0-c_i}{\sigma_i}, \qquad \sigma_i > z_0.$$

Returns then decrease because additional stake no longer increases the pool's gross reward. A pool slightly above $z_0$ may still offer a higher return than a much smaller unsaturated pool because the former not only have a larger gross reward but also continues to dilute its fixed cost more effectively.


![A slightly oversaturated pool can remain preferred](oversaturated_pool_utility.png)

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

Suppose that a fraction $\pi_d$ of the pools inspected by delegator \(d\) are acceptable. After inspecting $n$ pools, the probability of finding at least one acceptable alternative is

$$P_d(n) = 1-(1-\pi_d)^n.$$

When spare capacity is highly fragmented, $\pi_d$ is small, and the delegator must inspect many pools before finding a suitable alternative.

**Coordination friction**

Suppose several delegators identify the same attractive pool. Its remaining capacity becomes

$$q_j^{\mathrm{remaining}} = q_j-\sum_{d\in D_j}x_d,$$

where $D_j$ is the set of delegators moving to pool $j$.

Delegators may make decisions using the initial value of $q_j$, but simultaneous inflows can eliminate the available capacity or push the receiving pool above saturation. This can generate:

- herding toward well-known pools;
- overshooting;
- repeated redelegation;
- unused capacity in less visible pools;
- temporary oscillations around the saturation threshold.

A natural extension is a search-and-capacity model in which delegators sample a limited number of pools. Below saturation, inflows can increase a pool’s attractiveness through better fixed-cost dilution, but they simultaneously reduce its remaining capacity. Once inflows push the pool above saturation, additional stake reduces the return per unit of stake. This can generate congestion, overshooting, and repeated reallocation around the saturation threshold.

For an incoming delegation \(x_d\), the relevant return should therefore be evaluated at the post-delegation stake:

$$ y_j(\sigma_j+x_d) = (1-m_j) \frac{ \frac{f()}{\sigma_i}\min\{\sigma_j+x_d,z_0\}-c_j}{\sigma_j+x_d}.$$

A pool close to saturation may be highly attractive for a small delegator but unattractive—or unable to accommodate the delegation without oversaturation—for a large delegator.

**3. Switching costs, rational inattention, and brand loyalty.**

Let

$$\Delta_d = \max_j U_{dj}-U_{dA}$$

denote the utility gain available to delegator $d$ from leaving their current pool $A$.

The delegator switches only when

$$\Delta_d > \kappa_d,$$

where $\kappa_d$ denotes the switching cost (cost of acquiring and processing information about alternative pools, brand loyalty, etc). Thus, when $\kappa_d>0$, small return improvements do not justify moving


If $\kappa_d$ is heterogeneous across delegators with cumulative distribution $F_\kappa$, the fraction willing to switch for a gain $\Delta_d$ is $F_\kappa$.

Suppose that $a_d\in[0,1]$ denotes the probability that delegator $d$ notices and evaluates the change. This is a simplistic model of assuming inattention: when $a_d<1\$, some delegators do not reconsider their delegetion . The probability of switching is then

$$P_d(\text{switch}) = a_dF_\kappa.$$

Aggregate stake leaving pool $A$ is

$$M_A = \sum_{d\in A} \sigma_d\,a_dF_T(\Delta_d).$$

This simple model explains why a mechanical increase in oversaturation does not produce an equivalent outflow. Heterogeneous thresholds generate gradual rather than immediate adjustment, and/or loyalty and reputation can make the current delegation better even when another pool offers a slightly higher monetary return.

  
#### Operators changing pledge, margin, or declared fixed cost

Margin fees ($m_i$) and declared fixed costs ($c_i$) may face downward pressure, as pools have less stake over which to spread these costs. The impact on declared pledge ($p_i$) is more ambiguous: while an existing pledge becomes larger relative to the lower $z_0$—requiring less total pledge to reach the new saturation point—operators expanding into multi-pool operations will have to split their pledge across multiple pools.
  
#### Entry or exit of pools

A higher $k$ creates room for more pools, but also reduces maximum revenue per pool.
    
#### Pool splitting by multi-pool operators

MPOs can split stake across additional pools to remain below the new $z_0$. This may increase the pool count without materially reducing operator-level concentration. Splitting is favored by economies of scope, brand portability, and the possibility of collecting fixed cost in several pools; it is constrained by additional real costs and pledge dilution
    
#### Changes in staking participation

Increasing k does not create a direct incentive for currently unstaked ADA to enter staking. It mainly changes the allocation of stake across pools by lowering the saturation threshold. Therefore, its expected effect on aggregate staking participation is small, while its effect on redelegation patterns may be substantial.
    


### Decentralization


