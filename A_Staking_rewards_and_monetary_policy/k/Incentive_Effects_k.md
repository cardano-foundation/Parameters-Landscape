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

- **Gross pool rewards**
  
  The following plots illustrate the impact of the increment in $k$ on the reward function,

  $$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right].$$

  where
 
  $$\tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\}.$$
  
  The plot illustrates the case for an increment from $k=500$ to $k=1000$. Larger pools are negatively affected since their rewards are capped at a lower threshold. On the other hand, medium-sized pools closer to the new saturation point are now near the range where their rewards are maximized.
  
<p align="center">
  <img src="plots/heatmap_reward_function_k_cases.png" alt="Heatmap Reward function when k changes" width="80%">
</p>

- **Operator gross revenue**

    The previous plots present an incomplete picture, as an operator's total reward must also account for their declared fixed costs.     The following plots illustrate the operator rewards when their fixed cost is $c_i=170$ ADA and the margin (the commission retained to delegators) is $m_i=5\\%$. 

    <p align="center">
  <img src="plots/heatmap_operator_reward_k_cases.png" alt="Heatmap Operator Reward when k changes" width="80%">
    </p>

    Because the protocol reimburses operators for their declared fixed costs ($c_i$), incorporating fixed-cost income mitigates the impact of increasing $k$, particularly for pools with low pledge, even if the pool becomes oversaturated. This mitigation occurs because fixed costs are deducted from the total pool rewards before they are distributed to delegators—effectively reducing the delegators' share of pool rewards, which are given by $f(\sigma_i, p_i; z_0) - c_i$. Hence, pools with lower pledge (and higher proportion of third-party delegations) redirect a larger relative portion of delegator returns toward the operator.


- **Delegator return per unit of stake**

    Shifting the focus to delegator returns, the following plot illustrates how rewards per unit of stake change before delegators take action (e.g., migrating from an oversaturated, post-$k$-increment pool to a newly saturated pool). The interpretation of these plots follows directly from our previous formulas. Delegators remaining in now-oversaturated pools suffer immediate yield losses. Conversely, those who happen to be aligned with pools that have newly reached the lower saturation threshold experience yield gains, particularly if those pools feature high operator pledge.

    <p align="center">
  <img src="plots/heatmap_delegator_reward_k_cases.png" alt="Heatmap Delegator Reward when k changes" width="80%">
    </p>



- **Oversaturated stake**

    This part is built on per-pool data of epoch 616. To be consistent, it should be done with the the same data of the snapshot reported in [Parameter-Landscape.md](../../Parameter-Landscape.md). However, there should not be important changes with respect to the figures presented below.

  Denote the per-pool saturation point as $z_0(k) = \frac{T}{k},$ and the saturation level as

  $$s_i(k) = \frac{\sigma_i}{z_0(k)} = \frac{\sigma_i k}{T}.$$

    Pool $i$ is oversaturated if $s_i(k)>1$, i.e., $\sigma_i>z_0(k)$. The aggregate stake/delegation above saturation is calculated with
  
  $$E(k) = \sum_{i : \sigma_i>0} \max\\{\sigma_i - z_0(k),0\\}.$$

  The tables below summarize how doubling $k$ drives oversaturation, quantifying both the affected pool count and the aggregate delegation impacted by the change.
  
    | Quantity | Value |
    | :--- | ---: |
    | $T$  | $38.5B$ ADA |
    | $S$  | $21.6B$ ADA|
    | $S / T$ | 56.0% |
    | Pools with $\sigma_i>0$ | 2,717 |

    | Quantity | $k=500$ | $k=1000$ | 
    | :--- | ---: | ---: | 
    | $z_0(k)$ (M ADA) | 77.00 | 38.50 |
    | Oversaturated pools (count) | 8 | 212 | 
    | Oversaturated pools (% of pools) | 0.29% | 7.80% | 
    | $E(k)$ - Stake above saturation (B ADA) | 0.17 | 4.92 | 
    | $E(k)$ (% of $S$) | 0.77% | 22.79% | 


- **Reward-pot and treasury flows**

    Raising $k$ does not have a direct mechanical effect in the total size of the reward pot or the treasury's share. It only changes how the rewards are split among pools, which may affect (due to second order effects, like changes in the staking level) how much is actually paid out.

### Behavioral and equilibrium effects

    Currently, this section only identifies potential behavioral (or second-order) effects—primarily concerning delegator and operator decisions. To provide a clearer breakdown, the section below adopts a more granular approach rather than relying on these two broad categories.

    
- **Delegators moving stake**

    Yield-sensitive delegators typically leave oversaturated pools for those with available capacity. However, a mechanical increase in oversaturation does not guarantee an immediate or equivalent outflow. A slightly oversaturated pool can remain appealing if it offers lower reward variance, better fixed-cost dilution, or a strong reputation. Furthermore, identifying alternative pools requires effort: spare capacity is often fragmented across many operators, introducing search and coordination friction. Additional barriers—such as switching costs, rational inattention, or brand loyalty—can further delay adjustments, leading to persistent mild oversaturation and herding toward a small subset of pools. 
  
- **Operators changing pledge, margin, or declared fixed cost**

    Margin fees ($m_i$) and declared fixed costs ($c_i$) may face downward pressure, as pools have less stake over which to spread these costs. The impact on declared pledge ($p_i$) is more ambiguous: while an existing pledge becomes larger relative to the lower $z_0$—requiring less total pledge to reach the new saturation point—operators expanding into multi-pool operations will have to split their pledge across multiple pools.
  
- **Entry or exit of pools**

    A higher $k$ creates room for more pools, but also reduces maximum revenue per pool.
    
- **Pool splitting by multi-pool operators**

    MPOs can split stake across additional pools to remain below the new $z_0$. This may increase the pool count without materially reducing operator-level concentration. Splitting is favored by economies of scope, brand portability, and the possibility of collecting fixed cost in several pools; it is constrained by additional real costs and pledge dilution
    
- **Changes in staking participation**

     Increasing k does not create a direct incentive for currently unstaked ADA to enter staking. It mainly changes the allocation of stake across pools by lowering the saturation threshold. Therefore, its expected effect on aggregate staking participation is small, while its effect on redelegation patterns may be substantial.
    

## Discussion and open questions



