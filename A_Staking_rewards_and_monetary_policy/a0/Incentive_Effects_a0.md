# Change in $a_0$
(ToDo: Describe and elaborate on the intended design role of the parameter.)

## Increment in $a_0$
Increasing $a_0$ directly reduces the rewards assigned to a given pool by the protocol through $f()$. For a fixed level of pledge, this negative impact is more significant for larger pools (left plot). However, right plot suggest that an operator can mitigate this effect by replacing delegations with operator pledge. We will see that the latter is not the case. 

<p align="center">
  <img src="output_plots/Reward_function_vs_sigma_a0_cases.png" alt="Reward function when a0 changes versus delegation" width="48%">
  <img src="output_plots/Reward_function_vs_pledge_a0_cases.png" alt="Reward function when a0 changes versus pledge" width="48%">
</p>

### Impact over operators
From the previous plots, we could expect that a pool with larger pledge can mitigate the negative effect of the increment of $a_0$ by replacing delegations with pledge. However, the previous plots only illustrate the effect over the **reward function $f()$** while to address the effect over the operator we have to check the **operator rewards**.
![Heatmap Operator Reward when a0 changes](output_plots/heatmap_operator_reward_a0_cases.png)

To see the aparent discrepancy between the two plots, let's consider the case of $\sigma=z_0$ in $f()$:

$$ f=\frac{R}{1+a_0}\bigl(z_0+a_0 p_i\bigr).$$

Raising $a_0$ has two effects:
1. the factor $1/(1+a_0)$ shrinks the reward, and
2. the $a_0 p_i$ term rewards pledge more.

It is easy to see that this function is more increasing in $p_i$ when $a_0$ growth.

When we check the **operator gross revenue**, the operator receives

$$\Pi_i=c_i+s_i\cdot(f-c_i),\quad where \quad s_i=m_i+(1-m_i)\frac{p_i}{\sigma_i}.$$

Hence, the change in the **operator gross revenue** (or, equivalently, the change in the operator utility/profit if $c_i$ and $\hat{c}_i$ remain constant after the parameter change) is:

$$\Delta \Pi_i=s_i\cdot\Delta f()=\Delta U_i$$

As pledge rises, $s_i$ rises toward $1$. Even if $|\Delta f|$ shrinks, the operator’s **share** of that loss grows. So, $\Delta\Pi_i$ can become **more negative** even while $\Delta f$ becomes **less negative**. Away from saturation (e.g. $\sigma=50$M), $\Delta f()$ never fully recovers, so $\Delta\Pi$ can stay more negative all the way up the pledge axis.

As an example, let $\sigma_i=50M$ ADA, $k=500$, $c_i=170$, and $m_i=5\\%$. Suppose $a_0$ increases from $0.3$ to $0.6$:

| $p_i/\sigma_i$ | $\Delta f(\cdot)$ | $\Delta\Pi_i$ |
|---|---|---|
| $0$ | $-2922$ | $-146$ |
| $0.5$ | $-2140$ | $-1123$ |
| $1$ | $-1690$ | $-1690$ |

Bottom line: Higher pledge cushions the reward function $f()$ under a larger $a_0$. For the **operator**, it also means owning a larger slice of a still-smaller pie, so the operator comparison can look worse when pledge is very high.

### Impact over delegators
![Heatmap Delegator Reward when a0 changes](output_plots/heatmap_delegator_reward_a0_cases.png)


# Discussion
