# Incentive effects of changing $a_0$
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

# Design

The parameter $a_0$ determines how strongly a pool’s pledge affects its rewards. When $a_0=0$, pledge has no special role beyond contributing to total pool stake. As $a_0$ increases, pools with more pledge receive higher rewards than otherwise comparable low-pledge pools.

Without a pledge incentive, an operator with little capital could attract large amounts of delegation or create several pools while committing little stake of their own. A higher $a_0$ makes such strategies more costly because an operator splitting into multiple pools must also divide their pledge, reducing the reward potential of each pool. It therefore strengthens Sybil resistance and encourages operators to have more “skin in the game.”

The main trade-off is between Sybil resistance and accessibility. A higher $a_0$ discourages highly leveraged and multi-pool strategies, but it also favors wealthy operators and makes it harder for operators with limited capital to compete. A lower $a_0$ reduces barriers to entry and allows competition to depend more on performance, costs, and margins, but provides weaker protection against operators controlling large amounts of delegated stake with little pledge.

## Effects of change in $a_0$


### Direct mechanical effects 
In this section we consider the direct effects of changing the parameter while holding everything else equal (ceteris paribus). 

- **Gross pool rewards**

    This is study using the partial derivative which measures how $f(\sigma_i,p_i)$ changes when $a_0$ changes, holding all other variables constant. Since, 

    $$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right], \qquad \tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\},$$

    then
    
    $$\frac{\partial f}{\partial a_0} = -\frac{R}{(1+a_0)^2} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right] + \frac{R}{1+a_0} \left[ \tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right]\leq 0,$$

    with equality when $\tilde{p}_i = \tilde{\sigma}_i = z_0$.

    Increasing $a_0$ reduces total rewards for pools that rely primarily on external delegation rather than operator pledge, as $a_0$ penalizes low-pledge pools relative to high-pledge ones.

    For a fixed level of pledge, this negative impact is more significant for larger pools (left plot). However, right plot shows that an operator can mitigate this effect by replacing delegations with operator pledge. We will see that the latter is not the case. 

    <p align="center">
  <img src="plots/Reward_function_vs_sigma_a0_cases.png" alt="Reward function when a0 changes versus delegation" width="48%">
  <img src="plots/Reward_function_vs_pledge_a0_cases.png" alt="Reward function when a0 changes versus pledge" width="48%">
    </p>

- **Operator gross revenue**

    Analyzing the pool reward function $f(\sigma_i,p_i)$ in isolation gives an incomplete picture of an operator’s position. While a larger pledge might appear to cushion the impact of increasing $a_0$ by substituting delegation with pledge, this smoothing applies only to **gross pool rewards $f(\sigma_i,p_i)$**. To assess the true direct mechanical impact on pool operators, we must instead evaluate **operator gross revenue ($\Pi_i$)**.

    The following heatmaps illustrate this dynamic. Total pool stake $\sigma_i$ is mapped along the $x$-axis and operator pledge $p_i$ along the $y$-axis, with the grey region indicating the infeasible domain ($p_i > \sigma_i$). The left and center panels show operator revenue $\Pi_i$ under $a_0 = 0.3$ and $a_0 = 0.6$, respectively (evaluated at $k=500$, $c_i=170\text{ ADA}$, and $m_i=5\%$), while the right panel highlights the direct net change ( $\Delta \Pi_i = \Pi_i(a_0=0.6) - \Pi_i(a_0=0.3)$ ). In this difference plot, red gradients signify a net reduction in operator revenue ($\Delta \Pi_i < 0$), with darker shades marking larger absolute losses.

    ![Heatmap Operator Reward when a0 changes](plots/heatmap_operator_reward_a0_cases.png)

    The difference heatmap shows that, over a broad range of stake levels, increasing pledge does not compensate for the increase in ($a_0$). To understand why, first consider a saturated pool, ($\sigma_i=z_0$):
  
    $$f(z_0,p_i) = \frac{R}{1+a_0}\bigl(z_0+a_0 p_i\bigr).$$

    Increasing $a_0$ introduces two competing mechanical forces on $f(z_0,p_i)$:
    1. The scaling factor $\frac{1}{1+a_0}$ reduces baseline rewards.
    2. The term $a_0p_i$ gives greater weight to pledge, mitigating this reduction as $p_i$ increases and fully offsetting it when $p_i=z_0$.

    When we check any **operator gross revenue**, the operator receives

    $$\Pi_i=c_i+s_i\cdot(f(\sigma_i,p_i) -c_i),\quad \text{where} \quad s_i=m_i+(1-m_i)\frac{p_i}{\sigma_i}.$$

    Hence, the change in the **operator gross revenue** (or, equivalently, the change in the operator utility/profit if $c_i$ and $\hat{c}_i$ remain constant after the parameter change) is:

    $$\Delta \Pi_i=s_i\cdot\Delta f(\sigma_i,p_i) =\Delta U_i$$
    
    As pledge rises, $s_i$ rises toward $1$. Thus, even though the absolute reduction in pool gross rewards, $|\Delta f|$, becomes smaller, the operator bears a larger share of that reduction. Consequently, $\Delta\Pi_i$ can become more negative even while $\Delta f$ becomes less negative.

   Away from saturation—for example, when $\sigma_i=50\text{M ADA}$—the decline in $f$ is never fully offset as pledge increases. As a result, $\Delta\Pi_i$ may remain increasingly negative throughout the pledge range.

    As an example, let $\sigma_i = 50M$ ADA, $k=500$, $c_i=170$, and $m_i=5\\%$. Suppose $a_0$ increases from $0.3$ to $0.6$:

    | $p_i/\sigma_i$ | $\Delta f$ | $\Delta\Pi_i$ |
    |---|---|---|
    | $0$ | $-2922$ | $-146$ |
    | $0.5$ | $-2140$ | $-1123$ |
    | $1$ | $-1690$ | $-1690$ |

     Bottom line: Higher pledge cushions the decline in the pool gross reward function $f(\sigma_i,p_i)$ following an increase in $a_0$. For the operator, however, higher pledge also means bearing a larger share of the remaining reward reduction. Operator gross revenue can therefore fall by more at high pledge, even though the decline in total pool rewards is smaller.

- **Delegator return per unit of stake**

    The following heatmaps show the return received by delegators per unit of stake. Total pool stake $\sigma_i$ is displayed on the $x$-axis and operator pledge $p_i$ on the $y$-axis, while the grey region represents the infeasible domain $p_i > \sigma_i$. The left and center panels report delegator returns under $a_0 = 0.3$ and $a_0 = 0.6$, respectively. The right panel shows the direct change resulting from the increase in $a_0$. Red regions indicate a reduction in delegator returns, with darker shades representing larger losses.

    ![Heatmap Delegator Reward when a0 changes](plots/heatmap_delegator_reward_a0_cases.png)

    The heatmap shows that increasing $a_0$ generally reduces delegator returns per unit of stake, but that this negative effect becomes smaller as pledge increases. This contrasts with the result for operator gross revenue, since the change in the delegator return per unit of stake depends only in the changes on $f(\sigma_i,p_i)$.

    This can be seen analytically. After deducting the declared fixed cost and the operator margin, the return received by delegators per unit of stake is

    $$r_i^{D} = (1-m_i) \frac{\max\left\\{f(\sigma_i,p_i)-c_i, 0\right\\}}{\sigma_i},$$

    and, when $a_0$ changes, the direct change in the delegator return is

    $$\Delta r_i^{D} = \frac{1-m_i}{\sigma_i} \Delta f(\sigma_i,p_i).$$

    Consequently, higher pledge mitigates the negative effect of an increase in $a_0$ on delegator returns, even though it may amplify the reduction in operator gross revenue.

- **Oversaturated stake**

    Since $a_0$ does not have a direct effect over $z_0$, there is no direct change on oversaturated stakes.
  
- **Reward-pot and treasury flows**

    The parameter $a_0$ directly influences reward pot dynamics and treasury flows. In particular, it normalizes the total reward $R$ distributed among pools by a factor of roughly $1 + a_0$. Consequently, larger values of $a_0$ reduce the overall amount of $R$ paid out to pools, directing the remaining fraction back to the reserve. By allowing more rewards to remain unspent, an increase in $a_0$ slows reserve depletion and enhances the long-term sustainability of the reward model.

    An analysis of epoch 644 demonstrates how varying $a_0$ influences reserve reward retention during that specific period. The analysis considers the actual distribution of stake and pledge across the different pools (see [Pools Data e644](../../staking_pools_full_epoch_644.csv)), and calculates the gross reward $f(\sigma_i,p_i)$ per each pool for different values of $a_0$ (see [Pool Rewards vs a0](../../pools_f_vs_a0_epoch_644.csv) and [R Savings vs a0](../../savings_pct_of_R_vs_a0_epoch_644.csv) ). The effect exhibits slight concavity: for small adjustments, each $1\%$ increase in $a_0$ yields a reward savings of roughly $0.1\%$.

    <p align="center">
  <img src="plots/savings_pct_of_R_vs_a0_epoch_644.png" alt="Saving R when a0 changes" width="80%">
    </p>


