# Goal
This section covers comparative statics, specifically analyzing how changes in key parameters affect operator and delegator rewards.

# Preliminaries
Although the following was already introduce in other files of this report, we repeat it here to make this section selfcontent.

## Reward function
The gross reward of pool $i$ can be written as:

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right].$$

This reward is then adjusted for a pool's performance factor that we denote here with $\lambda_i$. Then, the realized gross reward is

$$\lambda_i f(\sigma_i,p_i).$$

Assume $\lambda_i = 1$, let $c_i\ge 0$ denote the fixed cost charged by the pool and $m_i\in[0,1)$ its margin. For pool $i$, the protocol first pays the fixed cost $c_i$ whenever $f(\sigma_i,p_i) > c_i$. The remaining amount, $\bigl[f(\sigma_i,p_i)-c_i\bigr]_+$, is then allocated as follows: a fraction $m_i$ is taken by the operator as the pool margin, that is, as a commission on delegation rewards, and the residual fraction $(1-m_i)$ is distributed proportionally among all stake delegated to the pool, including the operator's own pledged stake. Thus, **the pool operator gets**:

$$
\begin{cases}
c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], & \text{if } f(\sigma_i,p_i)>c_i, \\
f(\sigma_i,p_i), & \text{otherwise}
\end{cases}
$$

where $\hat{p}_i$ denotes the operator's active pledge, and **a delegator $d$ with stake $\sigma_d$ receives**:

$$
\begin{cases}
(1-m_i)(f(\sigma_i,p_i)-c_i)\frac{\sigma_d}{\sigma_i}, & \text{if } f(\sigma_i,p_i)>c_i, \\
0, & \text{otherwise}
\end{cases}
$$

### Notation and normalization
Unless stated otherwise, stake variables are measured as fractions of total ADA supply ($T$).
Thus,

$$\sigma_i = \frac{\text{pool } i \text{ stake in ADA}}{T}, \qquad p_i = \frac{\text{pool } i \text{ pledge in ADA}}{T}, \qquad z_0 = \frac{1}{k}.$$

If variables are measured directly in ADA, we use the ADA-denominated versions, e.g., with some abuse of notation, $z_0=\frac{T}{k}$.  

Notation is not fully standardized across the literature. In particular, pledge is sometimes denoted by $p_i$, $\lambda_i$, or $s_i$. Here we use $p_i$ for declared pledge.

# Increment in k
## Impact over operators
The direct effect of increasing $k$ is a reduction in the saturation threshold, $z_0$, which consequently lowers the maximum reward a pool can achieve. The following plots illustrate this impact on the reward function, $f(\sigma_i,p_i;z_0)$. As shown in the difference plot below, larger pools are negatively affected because their rewards are capped at a lower threshold. On the other hand, after the increase in $k$, medium-sized pools stay closer to the new saturation point where their rewards are maximized.
![Heatmap Reward function when k changes](output_plots/heatmap_reward_function_k_cases.png)
<p align="center">
  <img src="output_plots/Reward_function_vs_sigma.png" alt="Reward function when k changes" width="60%">
</p>

Note that this formula presents an incomplete picture, as an operator's total reward must also account for their declared fixed costs. The following plots illustrate the operator rewards when their fixed cost is $c_i=170$ ADA and the margin (the commision retained to delegators) is $m_i=5\\%$. 
![Heatmap Operator Reward when k changes](output_plots/heatmap_operator_reward_k_cases.png)

Because the protocol reimburses operators for their declared fixed costs ($c_i$), incorporating fixed-cost income mitigates the impact of increasing $k$, particularly for pools with low pledge. The latter occurs because fixed costs are deducted from the total pool rewards before remaining returns are distributed to delegators—effectively reducing the delegators' share of pool rewards, which are given by $f(\sigma_i, p_i; z_0) - c_i$. Hence, pools with lower pledge (and higher proportion of third-party delegations) redirect a larger relative portion of delegator returns toward the operator.

## Impact over delegators
![Heatmap Delegator Reward when k changes](output_plots/heatmap_delegator_reward_k_cases.png)


# Increment in $c_{min}$

## Impact over operators
![Heatmap Operator Reward when c changes](output_plots/heatmap_operator_reward_c_cases.png)

## Impact over delegators
![Heatmap Delegator Reward when c changes](output_plots/heatmap_delegator_reward_c_cases.png)


# Increment in $a_0$

## Impact over operators

## Impact over delegators

# Discussion
A lower saturation threshold when $k$ raises has several key implications. First, smaller or newer pools require less pledge and delegation to reach maximum reward, making it easier and less costly to compete with established, large pools. However, a lower saturation threshold also caps the maximum rewards a single pool can earn. As a result, while small pools improve their competitivness for delegators (that do not want to leave the ecosystem), the lower reward ceiling may make the overall ecosystem less appealing to investors looking to maximize their staking returns.

This last point highlights a critical design dilemma: Should the mechanism prioritize small operator viability or delegator attraction? While a balanced approach sounds ideal, the precise definition of 'balance' is rarely specified. Furthermore, protocol design must account for long-term feedback loops. For example, a policy that boosts small operator viability at the expense of delegator returns risks triggering a negative spiral: higher operator viability leads to reduced delegator yields $\rightarrow$ delegators exit $\rightarrow$ network security declines $\rightarrow$ adoption drops $\rightarrow$ token price falls $\rightarrow$ operator viability ultimately collapses under lower prices and fewer remaining delegators.
