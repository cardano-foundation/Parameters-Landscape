# Goal
This section covers comparative statics, specifically analyzing how changes in key parameters affect operator and delegator rewards.

# Preliminaries
While the following formulas were detailed in other sections, they are restated below to ensure this section remains standalone.

## Reward function
The reward function for pool $i$ is defined as:

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
Shifting the focus to delegator returns, the following charts illustrate how rewards per unit of stake change before delegators take action (e.g., migrating from an oversaturated, post-$k$-increment pool to a newly saturated pool). The interpretation of these plots follows directly from our previous formulas. Delegators remaining in now-oversaturated pools suffer immediate yield losses. Conversely, those who happen to be aligned with pools that have newly reached the lower saturation threshold experience yield gains, particularly if those pools feature high operator pledge.
![Heatmap Delegator Reward when k changes](output_plots/heatmap_delegator_reward_k_cases.png)




# Increment in $c_{min}$
This parameter acts as a lower bound on the fixed costs an operator can declare for their pool(s). That is, while $c_{\min}$ may change, each operator $i$ ultimately decides whether to update their declared fixed cost $c_i$ (this is particularly true if the $c_{min}$ is reduced, while operators may need to update if the $c_{min}$). In this subsection, we assume operators always set their fixed costs equal to $c_{\min}$.

## Impact over operators
![Heatmap Operator Reward when c changes](output_plots/heatmap_operator_reward_c_cases.png)

## Impact over delegators
![Heatmap Delegator Reward when c changes](output_plots/heatmap_delegator_reward_c_cases.png)


# Increment in $a_0$
Increasing $a_0$ directly reduces the rewards assigned to a given pool by the protocol through $f()$. For a fixed level of pledge, this negative impact is more significant for larger pools (left plot). However, right plot suggest that an operator can mitigate this effect by replacing delegations with operator pledge. We will see that the latter is not the case. 

<p align="center">
  <img src="output_plots/Reward_function_vs_sigma_a0_cases.png" alt="Reward function when a0 changes versus delegation" width="48%">
  <img src="output_plots/Reward_function_vs_pledge_a0_cases.png" alt="Reward function when a0 changes versus pledge" width="48%">
</p>

## Impact over operators
From the previous plots, we could expect that a pool with larger pledge can mitigate the negative effect of the increment of $a_0$ by replacing delegations with pledge. However, the previous plots only illustrate the effect over the **reward function $f()$** while to address the effect over the operator we have to check the **operator rewards**.
![Heatmap Operator Reward when a0 changes](output_plots/heatmap_operator_reward_a0_cases.png)

To see the aparent discrepancy between the two plots, let's consider the case of $\sigma=z_0$ in $f()$:

$$ f=\frac{R}{1+a_0}\bigl(z_0+a_0 p_i\bigr).$$

Raising $a_0$ has two effects:
1. the factor $1/(1+a_0)$ shrinks the reward, and
2. the $a_0 p_i$ term rewards pledge more.

It is easy to see that this function is more increasing in $p_i$ when $a_0$ growth.

When we check the **operator reward**, the operator receives approximately

$$\Pi_i=s_i\cdot(f-c_i),\quad where \quad s_i=m_i+(1-m_i)\frac{p_i}{\sigma_i}.$$

Hence, the change in the **operator reward** ($\Delta\Pi$) is approximately:

$$s_i\cdot\Delta f()$$

As pledge rises, $s_i$ rises toward $1$. Even if $|\Delta f|$ shrinks, the operator’s **share** of that loss grows. So, $\Delta\Pi_i$ can become **more negative** even while $\Delta f$ becomes **less negative**. Away from saturation (e.g. $\sigma=50$M), $\Delta f()$ never fully recovers, so $\Delta\Pi$ can stay more negative all the way up the pledge axis.

As an example, let $\sigma_i=50M$ ADA, $k=500$, $c_i=170$, and $m_i=5\\%$. Suppose $a_0$ increases from $0.3$ to $0.6$:

| $p_i/\sigma_i$ | $\Delta f(\cdot)$ | $\Delta\Pi_i$ |
|---|---|---|
| $0$ | $-2922$ | $-146$ |
| $0.5$ | $-2140$ | $-1123$ |
| $1$ | $-1690$ | $-1690$ |

Bottom line: Higher pledge cushions the reward function $f()$ under a larger $a_0$. For the **operator**, it also means owning a larger slice of a still-smaller pie, so the operator comparison can look worse when pledge is very high.

## Impact over delegators
![Heatmap Delegator Reward when a0 changes](output_plots/heatmap_delegator_reward_a0_cases.png)


# Discussion
A lower saturation threshold when $k$ raises has several key implications. First, smaller or newer pools require less pledge and delegation to reach maximum reward, making it easier and less costly to compete with established, large pools. However, a lower saturation threshold also caps the maximum rewards a single pool can earn. As a result, while small pools improve their competitivness for delegators (that do not want to leave the ecosystem), the lower reward ceiling may make the overall ecosystem less appealing to investors looking to maximize their staking returns.

This last point highlights a critical design dilemma: Should the mechanism prioritize small operator viability or delegator attraction? While a balanced approach sounds ideal, the precise definition of 'balance' is rarely specified. Furthermore, protocol design must account for long-term feedback loops. For example, a policy that boosts small operator viability at the expense of delegator returns risks triggering a negative spiral: higher operator viability leads to reduced delegator yields $\rightarrow$ delegators exit $\rightarrow$ network security declines $\rightarrow$ adoption drops $\rightarrow$ token price falls $\rightarrow$ operator viability ultimately collapses under lower prices and fewer remaining delegators.
