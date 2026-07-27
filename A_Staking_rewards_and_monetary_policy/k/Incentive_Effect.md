# Incentive effects of changing k
For numercial analysis in this section, we use the following values of parameters unless stated the contrary.



## Design

$k$ denotes the target number of economically relevant stake pools. It is not a hard cap on the number of pools that may be registered; rather, it shifts the reward function through the saturation threshold

$$
z_0 = \frac{1}{k}.
$$

The motivation is to limit the increasing-returns pattern that appears when rewards are proportional to stake. Below saturation, delegation tends to increase the reward available to the pool and to the delegators. Above saturation, additional stake no longer increases gross rewards, which weakens the advantage of very large pools. Choosing $k$ therefore trades off decentralization and economic viability: a higher $k$ creates room for more competitive pools, while a lower $k$ makes it easier for each pool to reach a viable scale.

## Change in k

The parameter change considered here is an increase in $k$, which lowers the saturation threshold and therefore changes the reward profile before any behavioral response occurs.

## 6. Incentive Effects

### 6.1 Direct mechanical effects 
In this section we consider the direct effects of changing the parameter while holding everything else equal (ceteris paribus).

- **Gross pool rewards**

The following plots illustrate the impact of the increment in $k$ on the reward function, $f(\sigma_i,p_i;z_0)$. The plot illustrates the case for an increment from $k=500$ to $k=1000$. As expected, larger pools are negatively affected since their rewards are capped at a lower threshold. On the other hand, medium-sized pools closer to the new saturation point are now near the range where their rewards are maximized.


<p align="center">
  <img src="plots/heatmap_reward_function_k_cases.png" alt="Heatmap Reward function when k changes" width="80%">
</p>

- **Operator gross revenue**

- **Delegator return per unit of stake**

- **Oversaturated stake**

- **Reward-pot and treasury flows**

The direct mechanical effect of increasing $k$ is to lower the saturation threshold, $z_0$, and thereby reduce the maximum reward that a pool can receive at a given stake level:

$$f(\sigma_i,p_i;z_0) > f(\sigma_i,p_i;z_0') \quad \text{for any} \quad z_0 > z_0'.$$

This is the immediate ledger effect before any actor adjusts its behavior. The plots below hold pools, stake, pledge, costs, margins, and performance fixed and recompute the consequences of the parameter change.

Larger pools are more exposed to the new cap because their rewards are clipped at a lower saturation point, while medium-sized pools near the new threshold can move into a more favorable region. Operator rewards are partly cushioned by the reimbursement of declared fixed costs, $c_i$, which reduces the impact for pools with low pledge and a high share of third-party delegation.

<p align="center">
  <img src="output_plots/heatmap_reward_function_k_cases.png" alt="Heatmap Reward function when k changes">
</p>

<p align="center">
  <img src="output_plots/Reward_function_vs_sigma.png" alt="Reward function when k changes" width="60%">
</p>

The next plots incorporate declared fixed costs with $c_i=170$ ADA and $m_i=5\%$. In this setting, the operator's effective reward is partly protected because the reimbursement reduces the share of pool rewards that must be passed to delegators.

<p align="center">
  <img src="output_plots/heatmap_operator_reward_k_cases.png" alt="Heatmap Operator Reward when k changes">
</p>

For delegators, the direct effect appears as a change in reward per unit of stake. Delegators remaining in pools that become oversaturated after the increase in $k$ experience lower yields immediately, while those in pools that newly reach the lower threshold can experience higher returns, especially when the pool has high pledge.

<p align="center">
  <img src="output_plots/heatmap_delegator_reward_k_cases.png" alt="Heatmap Delegator Reward when k changes">
</p>

### 6.2 Behavioral and equilibrium effects

The direct mechanical effects above are only the first-order impact. The total effect can be written as

$$\text{total effect} = \text{direct mechanical effect} + \text{behavioral response} + \text{system feedback}.$$

Once actors respond, the system may change through delegators moving stake, operators adjusting pledge, margin, or declared fixed cost, entry or exit of pools, pool splitting by multi-pool operators, and other participation changes. These responses are not captured by the heatmaps alone.

The pool-splitting example illustrates why behavioral effects matter. A large pool that is penalized by the new $k$ may split into smaller pools in order to preserve or increase its total reward. The basic intuition is that, for some delegation ranges, splitting can reduce the saturation penalty for each sub-pool, while fixed-cost reimbursement may further increase the operator's overall return.

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_k_split.png" alt="Operator Reward when split" width="60%">
</p>

The same logic applies when comparing splitting under unchanged $k$ and under different $k$ values. The relevant question is therefore not only whether the mechanical reward formula changes, but whether operators and delegators respond in ways that alter the equilibrium.

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k.png" alt="Operator Reward when split same k" width="60%">
</p>

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k_both.png" alt="Operator Reward when split under different k" width="60%">
</p>

## 7. Discussion and open questions

The most relevant questions are those that require modeling or empirical evidence rather than a purely mechanical comparison.

- Whether larger operators find it profitable to split pools even when $k$ is unchanged.
- Whether a higher $k$ genuinely improves the competitiveness of small pools once operators and delegators adjust.
- Whether the pledge bonus remains economically meaningful under realistic delegation and pledge configurations, especially in the presence of multi-pool operators and fixed-cost reimbursement.


