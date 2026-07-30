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

    Analyzing the pool reward function $f(\sigma_i,p_i) $ in isolation gives an incomplete picture of an operator’s position. While a larger pledge might appear to cushion the impact of increasing $a_0$ by substituting delegation with pledge, this smoothing applies only to **gross pool rewards $f(\sigma_i,p_i) $**. To assess the true direct mechanical impact on pool operators, we must instead evaluate **operator gross revenue ($\Pi_i$)**.

    The following heatmaps illustrate this dynamic. Total pool stake $\sigma_i$ is mapped along the $x$-axis and operator pledge $p_i$ along the $y$-axis, with the grey region indicating the infeasible domain ($p_i > \sigma_i$). The left and center panels show operator revenue $\Pi_i$ under $a_0 = 0.3$ and $a_0 = 0.6$, respectively (evaluated at $k=500$, $c_i=170\text{ ADA}$, and $m_i=5\%$), while the right panel highlights the direct net change ($\Delta \Pi_i = \Pi_i\vert{}_{a_0=0.6} - \Pi_i\vert{}_{a_0=0.3}$). In this difference plot, red gradients signify a net reduction in operator revenue ($\Delta \Pi_i < 0$), with darker shades marking larger absolute losses.

    ![Heatmap Operator Reward when a0 changes](plots/heatmap_operator_reward_a0_cases.png)

    The difference heatmap shows that in a broad range of staking level, increasing the pledge does not compensate for the the increment in $a_0$. To see the reason, let's consider a simple case in which $\sigma=z_0$ in $f(\sigma_i,p_i) $:

    $$f(\sigma_i,p_i) = \frac{R}{1+a_0}\bigl(z_0+a_0 p_i\bigr).$$

    Increasing $a_0$ introduces two competing mechanical forces on $f(\sigma_i,p_i) $:
    * The scaling factor $\frac{1}{1+a_0}$ reduces baseline rewards across all pools.
    * The $a_0 p_i$ term strengthens the weight of pledge, mitigating the contraction as $p_i$ increases.

    When we check the **operator gross revenue**, the operator receives

    $$\Pi_i=c_i+s_i\cdot(f(\sigma_i,p_i) -c_i),\quad \text{where} \quad s_i=m_i+(1-m_i)\frac{p_i}{\sigma_i}.$$

    Hence, the change in the **operator gross revenue** (or, equivalently, the change in the operator utility/profit if $c_i$ and $\hat{c}_i$ remain constant after the parameter change) is:

    $$\Delta \Pi_i=s_i\cdot\Delta f(\sigma_i,p_i) =\Delta U_i$$
    
    As pledge rises, $s_i$ rises toward $1$. Even if $|\Delta f|$ shrinks, the operator’s **share** of that loss grows. So, $\Delta\Pi_i$ can become **more negative** even while $\Delta f$ becomes **less negative**. Away from saturation (e.g. $\sigma=50$M), $\Delta f$ never fully recovers, so $\Delta\Pi$ can stay more negative all the way up the pledge axis.

    As an example, let $\sigma_i=50M$ ADA, $k=500$, $c_i=170$, and $m_i=5\\%$. Suppose $a_0$ increases from $0.3$ to $0.6$:

    | $p_i/\sigma_i$ | $\Delta f$ | $\Delta\Pi_i$ |
    |---|---|---|
    | $0$ | $-2922$ | $-146$ |
    | $0.5$ | $-2140$ | $-1123$ |
    | $1$ | $-1690$ | $-1690$ |

     Bottom line: Higher pledge cushions the reward function $f(\sigma_i,p_i) $ under a larger $a_0$. However, for the **operator**, a larger $a_0$ also means owning a larger slice of a still-smaller pie, so the operator comparison can look worse when pledge is very high.

- **Delegator return per unit of stake**
- **Oversaturated stake**
- **Reward-pot and treasury flows**


### Impact over operators


### Impact over delegators
![Heatmap Delegator Reward when a0 changes](plots/heatmap_delegator_reward_a0_cases.png)


# Discussion
