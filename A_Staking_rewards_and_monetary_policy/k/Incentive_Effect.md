# Change in k

## Design

**$k$** denotes the desired or target number of economically relevant stake pools. It is not a hard cap on the number of pools that may be registered. Instead, it enters the reward function to make an equilibrium with approximately $k$ competitive pools attractive.

A reward scheme in which pools are compensated proportionally to their stake, $\sigma$, tends to encourage centralization. If pool operating costs are largely fixed, larger pools can spread these costs over more delegated stake and offer higher rewards per unit of stake. Delegators therefore have an incentive to move toward already large pools.

> move the following chart to another section

<p align="center">
  <img src="output_plots/delegator_reward_per_unit_vs_sigma.png" alt="Reward function per unit of stake" width="60%">


The parameter **$k$** is introduced to limit this increasing-returns mechanism by determining the saturation threshold

$$
z_0 = \frac{1}{k},
$$

up to which pool rewards increase with stake. This cap introduces the following forces and incentives:

1. **Below saturation**, additional delegation increases a delegator's net return ($\partial U_d/\partial \sigma_d > 0$). A larger delegated stake $\sigma_d$ increases the pool's reward function $f(\cdot)$ while distributing the fixed operating cost across a larger capital base. This virtuous cycle creates an incentive for pool operators to maintain a high active pledge—particularly during initial stages when attracting delegation is critical.
3. **Above saturation**, additional stake does not increase the pool's gross reward ($f()$), discouraging further concentration.

Choosing $k$ therefore involves a trade-off between decentralization and economic viability. A higher $k$ lowers the saturation threshold and creates room for more competitive pools, but reduces the economic scale available to each pool. A lower $k$ makes it easier for pools to cover their operating costs, but allows stake to concentrate among fewer operators.

Thus, $k$ defines the protocol's decentralization target by jointly determining the saturation threshold, the expected number of competitive pools, and the economic scale at which those pools operate.


## Increment in k
The direct effect of increasing $k$ is a reduction in the saturation threshold, $z_0$, which consequently lowers the maximum reward: 

$$f(\sigma_i,p_i;z_0)>f(\sigma_i,p_i;z_0')\quad \text{for any} \quad z_0>z_0'.$$ 

### Impact over operators
Let us first consider the impact of an increase in $k$ on operators prior to any behavioral response—that is, the isolated effect of the change, holding all else constant ($ceteris\ paribus$). Indeed, any subsequent operator response will be driven by how this initial change affects their current state.

The following plots illustrate this impact on the reward function, $f(\sigma_i,p_i;z_0)$. As expected, larger pools are negatively affected since their rewards are capped at a lower threshold. On the other hand, medium-sized pools closer to the new saturation point are now near the range where their rewards are maximized.
![Heatmap Reward function when k changes](output_plots/heatmap_reward_function_k_cases.png)
<p align="center">
  <img src="output_plots/Reward_function_vs_sigma.png" alt="Reward function when k changes" width="60%">
</p>

The previous plots present an incomplete picture, as an operator's total reward must also account for their declared fixed costs. The following plots illustrate the operator rewards when their fixed cost is $c_i=170$ ADA and the margin (the commision retained to delegators) is $m_i=5\\%$. 
![Heatmap Operator Reward when k changes](output_plots/heatmap_operator_reward_k_cases.png)

Because the protocol reimburses operators for their declared fixed costs ($c_i$), incorporating fixed-cost income mitigates the impact of increasing $k$, particularly for pools with low pledge, even if the pool becomes oversaturated. This mitigation occurs because fixed costs are deducted from the total pool rewards before remaining returns are distributed to delegators—effectively reducing the delegators' share of pool rewards, which are given by $f(\sigma_i, p_i; z_0) - c_i$. Hence, pools with lower pledge (and higher proportion of third-party delegations) redirect a larger relative portion of delegator returns toward the operator.

### Impact over delegators
Shifting the focus to delegator returns, the following charts illustrate how rewards per unit of stake change before delegators take action (e.g., migrating from an oversaturated, post-$k$-increment pool to a newly saturated pool). The interpretation of these plots follows directly from our previous formulas. Delegators remaining in now-oversaturated pools suffer immediate yield losses. Conversely, those who happen to be aligned with pools that have newly reached the lower saturation threshold experience yield gains, particularly if those pools feature high operator pledge.
![Heatmap Delegator Reward when k changes](output_plots/heatmap_delegator_reward_k_cases.png)

## Discussion
A lower saturation threshold resulting from an increase in $k$ has several key implications. First, smaller or newer pools require less pledge and delegation to reach maximum rewards, lowering the cost to compete with large, established pools. Additionally, previous plots might suggest that large pools are invariably harmed by the change. However, fully evaluating this parameter change requires analyzing how pools adjust their strategies, as well as how delegators react to these new incentives.

### Pool splitting 
A larger pool that faces its reward negatively affected by the increment in $k$ may split into smaller pools. By doing this, it may achieve, at least, the same reward. To see this, suppose a change that doubles the value of $k$. Before the increment, 

$$f(\sigma_i,p_i;z_0)=\frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right],$$

where we assume $\tilde{\sigma}_i=\sigma_i$ and $\tilde{p}_i=p_i$. 

(ToDo: what happens if the k is not double ($2x$) but increased in $1.5x$ or another non-integer value? Prove that the operator can keep the same total $f()$ if he splits in such a way of have one full saturated pool, with the new $z_0$, and all the pledge there, while having another pool with the residual delegation. In the latter case, would delegators accept that new pool without pledge?)

After doubling $k$, the new saturation threshold becomes $z_0/2$. Suppose an operator responds by splitting their existing pool into two identical pools, each allocated half of the initial stake ($\sigma_i/2$) and pledge ($p_i/2$). Then, in each of these two pools:

$$
\begin{aligned}
f\left(\frac{\sigma_i}{2},\frac{p_i}{2};\frac{z_0}{2}\right) &= \frac{R}{1+a_0} \left[ \frac{\sigma_i}{2} + a_0\frac{p_i}{2} \frac{\frac{\sigma_i}{2}-\frac{p_i}{2}\frac{\frac{z_0}{2}-\frac{\sigma_i}{2}}{\frac{z_0}{2}}}{\frac{z_0}{2}} \right], \\
f\left(\frac{\sigma_i}{2},\frac{p_i}{2};\frac{z_0}{2}\right) &= \frac{f(\sigma_i,p_i;z_0)}{2}.
\end{aligned}
$$

This calculation does not yet account for fixed costs. Managing two separate pools enables the operator to collect fixed fee revenues twice, increasing their total revenues as seen in the following plot:

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_k_split.png" alt="Operator Reward when split" width="60%">
</p>

All these open some questions and comments: (ToDo: once finished, reorder from most relevant)
1. **Incentive to split under constant $k$:** The previous observation raises the question of whether a large pools operator may find it profitbale to split pools even when there is no change in $k$.
    Comparing $f(\sigma_i,p_i;z_0)$ directly with $f\left(\frac{\sigma_i}{2},\frac{p_i}{2};z_0\right)$ shows that

    $$f(\sigma_i,p_i;z_0) >2*f\left(\frac{\sigma_i}{2},\frac{p_i}{2};z_0\right),$$

    holds whenever total delegation is less than or equal to $z_0$ (more strictly, there exists a threshold $\sigma_i^* > z_0$ such that the inequality holds for all $\sigma_i < \sigma_i^*$). Conversely, the inequality reverses when delegation exceeds this threshold. Consequently, pool splitting (or creating an additional pool) is beneficial strictly for oversaturated pools—a result that was intentionally design.

    However, again the income coming from the fixed cost has something to say. By splitting into two identical pools, 

    <p align="center">
    <img src="output_plots/operator_reward_vs_sigma_split_same_k.png" alt="Operator Reward when split same k" width="60%">
    </p>

    The plot compares the total revenue of a single pool operator across varying delegation levels against the revenue achieved by splitting the stake into two identical pools. The curves are plotted starting from $\sigma_i \ge p_i = 700\text{k}$ ADA. Again once the single pool reaches or exceeds the saturation threshold, splitting becomes more advantageous, as neither of the two smaller sub-pools suffers from the saturation cap.

    These observations may explain the prevalence of medium-sized multi-pool operators (MPOs) alongside the relative scarcity of fully saturated (or near-saturated) pools.

2. **Incentives to split after a change in $k$.** A change in $k$ does not increase or decrease the extra revenues that the operator may achieve by splitting the pool, as the following plot shows
    <p align="center">
    <img src="output_plots/operator_reward_vs_sigma_split_same_k_both.png" alt="Operator Reward when split under different k" width="60%">
    </p>

### Small pools competitivness:
Since the operator of a large pool increase their overall returns by splitting into two identical pools, this operator could reduce $m_i$ and/or $c_i$ (whenever feasible) to become more competitive. This raises a critical question: to what extent does an increase in $k$ truly improve the competitiveness of small pools?

### The pledge bonus:
The report The Holistic Reading about SPO incentives identify that the [pledge bonus is inoperative](https://input-output-hk.github.io/spo-incentives/diagnostic.html#:~:text=AT%20REALISTIC%20SCALE-,The,-23%25%20allocated%20to). The report shows that, given a total amount of ADA (e.g., $\sigma_i=20M$ ADA), it is more profitable for the operator to have a "balanced" strategy (e.g., $50\%$ self-delegated and $50\%$ pledge) than being fully pledge. 


