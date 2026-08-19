# Incentive effects of changing monetary policy parameters: Reserve decay rate ($\rho$), Treasury share ($\tau$)

## Summary: Trade-off.


**Pros**

**Risks**


**What the evidence suggests**


**Behavioral and equilibrium discussion**

**Policy interpretation**


## Parameter values at the current state
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


Cardano funds staking rewards and its treasury through a combination of transaction fees and predefined monetary expansion from its reserve—the difference between the $45B$ ADA maximum supply and the circulating supply. For each epoch $t$, let's denote the reserve level by $Q_t$, transaction fees by $F_t$, the **treasury share** parameter by $\tau$ (currently $20\\%$), and the **reserve decay rate** (or monetary expansion parameter) by $\rho$ (currently $0.3\\%$). Because the treasury share and reserve decay rate remain constant across epochs, they do not carry a subscript $t$.

> **Note:** Cardano Constitution constrains monetary-expansion changes: $\rho$ must remain between $0.001$ and $0.005$, and the recommended guardrails say it should not vary by more than $±10\\%$ in any $73\text{-epoch}$ period (roughly a year) and should not be changed more than once in any $36\text{-epoch}$ period ($\approx 6\text{ months}$).

The protocol calculates the amount taken from reserves $M_t$ by scaling $\rho$ by a network performance factor $\eta_t$:

$$M_t = \min\\{\eta_t, 1\\} \cdot\rho Q_t$$

Denote $P_t$ to the gross pot:

$$P_t = F_t + M_t = F_t + \min\\{\eta_t, 1\\} \cdot\rho Q_t.$$

> **Note:** In Cardano's design, transaction fees and reserve depletion should act as funding substitutes; as reserves decline, fees progressively should become the primary source of rewards. However, there is not a parameter or function connecting these two reward sources. It was expected that the substitution occur while the market and Cardano usage matures.


From this gross pot, a fraction $\tau$ goes to und the treasury, i.e., 

$$G_t = \tau P_t = \tau \left[ F_t + \min\\{\eta_t, 1\\} \cdot\rho Q_t \right]$$

The remaining share $(1 - \tau)$ forms the available pool reward pot for that epoch $R_t$:

$$R_t = (1 - \tau) P_t = (1 - \tau) \left[ F_t + \min\\{\eta_t, 1\\} \cdot\rho Q_t \right]$$,

This $R_t=R$ corresponds to the total pot entering the gross pool reward function:

$$f(\tilde{\sigma}_i, \tilde{p}_i) = \frac{R}{1 + a_0} \left[ \tilde{\sigma}_i + a_0 \tilde{p}_i \frac{\tilde{\sigma}_i - \tilde{p}_i \frac{z_0 - \tilde{\sigma}_i}{z_0}}{z_0} \right]$$

Rewards are only distributed on active, staked ADA. If less than $100\\%$ of the circulating supply is staked, unearned rewards return directly to the reserves.


## Direct mechanical effects 
In this section we consider the direct effects of **changing** $\rho$ while holding everything else equal (ceteris paribus). 

### Gross pool rewards

Let $\sigma_i$ denote the total delegation at pool $i$, $p_i$ the declared pledge of the pool, and $z_0$ the saturation threshold. The gross pool reward function is

$$f(\sigma_i,p_i) = \frac{R}{1+a_0} \left[ \tilde{\sigma}_i + a_0\tilde{p}_i \frac{\tilde{\sigma}_i-\tilde{p}_i\frac{z_0-\tilde{\sigma}_i}{z_0}}{z_0} \right], \qquad \tilde{\sigma}_i = \min\\{\sigma_i, z_0\\}, \qquad \tilde{p}_i = \min\\{p_i, z_0\\},$$


A change in the parameter $\rho$ does not translate one-for-one into higher staking rewards, due to the fraction $\tau$ that is taken for the treasury:

$$\frac{\partial R_t}{\partial \rho} = (1 - \tau)\min\\{\eta_t, 1\\}\cdot Q_t\geq 0.$$

On the other hand, a change in the parameter $\tau$ 

$$\frac{\partial R_t}{\partial \tau} = -\left[ F_t + \min\\{\eta_t, 1\\} \cdot\rho Q_t \right]\leq 0.$$

If we change both parameters at the same time, depending on the magnitud of each change, the net effect over $R_t$ could be positive or negative. To find the boundary (such that $R_t$ remains unchanged) for small variations $d\tau$ and $d\rho$, set the total differential $dR_t = 0$:

$$dR_t = \frac{\partial R_t}{\partial \tau} d\tau + \frac{\partial R_t}{\partial \rho} d\rho = 0.$$

Therefore, the partial derivatives are:

$$\frac{\partial R_t}{\partial \tau} = -[F_t + \rho \min\\{\eta_t, 1\\} Q_t], \qquad \frac{\partial R_t}{\partial \rho} = (1 - \tau) \min\\{\eta_t, 1\\} Q_t.$$

and

$$-[F_t + \rho \min\\{\eta_t, 1\\} Q_t]  d\tau + (1 - \tau) \min\\{\eta_t, 1\\} Q_t d\rho = 0,$$

yielding to the relation

$$\frac{d\rho}{d\tau} = \frac{[F_t + \rho \min\\{\eta_t, 1\\} Q_t]}{(1 - \tau) \min\{\eta_t, 1\} Q_t} = \frac{F_t + \rho \min\\{\eta_t, 1\\} Q_t}{(1 - \tau) \min\\{\eta_t, 1\\} Q_t} = \frac{1}{1 - \tau} \left( \frac{F_t}{\min\\{\eta_t, 1\\} Q_t} + \rho \right)$$

For an approach for discrete changes, let's solve for the new value $\rho'$ in terms of the new value $\tau'$:

$$\rho' = \frac{1}{\min\\{\eta_t, 1\\} Q_t$} \left[ \frac{1 - \tau}{1 - \tau'} [F_t + \rho \min\\{\eta_t, 1\\} Q_t] - F_t \right].$$

Equivalently, expressing the change in rho ($\Delta \rho = \rho' - \rho$) in terms of the change in tau ($\Delta \tau = \tau' - \tau$):

$$\Delta \rho = \frac{\Delta \tau}{1 - \tau - \Delta \tau} \cdot \frac{F_t + \rho [\min\\{\eta_t, 1\\} Q_t]}{\min\\{\eta_t, 1\\} Q_t}$$

Therefore, when $\tau$ increases ($\Delta \tau > 0$), $(1 - \tau)$ shrinks, so $\rho$ must increase ($\Delta \rho > 0$) to compensate. The sensitivity depends on the fraction of total rewards coming from $F_t$ versus $\rho [\min\\{\eta_t, 1\\} Q_t]$.



### Operators and delegators revenue

For both types of players, the direct mechanical effect is proportional to the previous description. The operator groos revenue is given by the epxression:

$$
\Pi_i=
\begin{cases}
\underbrace{c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right]}_{\Pi_i=\text{Operator gross revenue}}, & \text{if } f(\sigma_i,p_i)>c_i, \\
f(\sigma_i,p_i), & \text{otherwise}
\end{cases}
$$

where $\hat{p}_i$ denotes the operator's active pledge, while the operator utility is:


$$
U_i=\Pi-\hat{c}_i
$$

where $\hat{c}_i$ is the actual operating cost.

On the other hand a delegator $d$ with stake $\sigma_d$ achieves:

$$
U_d=
\begin{cases}
(1-m_i)(f(\sigma_i,p_i)-c_i)\frac{\sigma_d}{\sigma_i}, & \text{if } f(\sigma_i,p_i)>c_i, \\
0, & \text{otherwise},
\end{cases}
$$

with 

$$\sigma_i=\hat{p}\_i + \sum_{j=1}^{D_i}\sigma_j$$  

being $D_i$ the set of delegators delegating to pool $i$. 


## The evolution of the reward pot

Next plots show how the reward pot those parameters act on ($\rho$ and $\tau$) has moved.

The following plot illustrates the evolution of the reserves, the total supply, and the staking level. As expected, reserves and total supply are perfectly correlated since the total supply is populated by the reserve depletion. We do not observe such a strong pattern with the staking level (in particular, since epoch 400) suggesting that a large fraction of new tokens release to the market is used for different purposes than securing the protocol.

<p align="center">
  <img src="plots/reserves_supply_stake.png" alt="Evolution of Reserves, Supply and Stake" width="62%">
</p>


The reward scheme extract a fixed amount from the reserves ($\tau=0.3\\%$ per epoch) to reward the delegators. Naturally, the design implies a decreasing return for delegators. The next plot shows this idea measured by two metrics of reward intensity. One is $R_t/T_t$ (reward pot over total supply), and the other is $R_t/S_t$ (reward pot over staking level). The former will always be decreasing  because of the identity $Reserves_t+T_t=45B$ ADA, implying $R_t/(45B - Reserves_t)$. Since $R_t=\rho Reserves_{t}$, then

$$\frac{R_t}{T_t}=\frac{\rho}{\frac{45B}{Reserves_t}-1},$$

which is decreasing when $Reserves_t$ decreases.


<p align="center">
  <img src="plots/reward_intensity_R_over_T.png" alt="Evolution of reward intensity over T" width="62%">
</p>

The following plot illustrates reward intensity as a function of total stake. Reward intensity is highest at launch due to low aggregate stake, then gradually flattens as the network matures. As shown in the second plot, the relationship appears nearly linear across the observed period from epoch $300$ onward with a slope that is mainly driven by the reward pot reduction (the OLS slope of $R/S$ is about $-1.14 \times 10^{-6}$ per epoch). During the time window, $R$ is down $45\\%$ while $S$ is down $10\\%$, and the observed slope is about $77\\%$ of the slope that we would have if the staking level $S$ remained constant (and hence, the whole slope was explained by the drop in the reward $R$). This suggests that capital (stakes) was sticky ($S$ does decline, but much less than $R$, so it only partially offsets the reward reduction in $R/S$). If $R$ keeps falling while $S$ falls slowly, gross staking yield will continue trending down.


<p align="center">
  <img src="plots/reward_intensity_R_over_S.png" alt="Evolution of reward intensity over S" width="62%">
</p>


The following plot shows the variation in gross APR over time. We illustrate the lower bound (zero pledge), calculated as $73 \cdot \frac{R}{(1+a_0)T}$, and the upper bound, calculated as $73 \cdot \frac{R}{T}$. The theoretical APR is strictly decreasing across epochs. This is by design: available rewards ($R$) decrease as the reserve shrinks (since the protocol draws a fixed fraction $\rho = 0.3\\%$ from a diminishing reserve pot each epoch), while total circulating supply ($T$) expands as those released tokens enter circulation.

<p align="center">
  <img src="plots/gross_apr.png" alt="Historical APR" width="62%">
</p>


In order to observe an increment in the gross APR, the reward pot $R$ should increase via fees (recall that $R_t=(1 - \tau) \left[ F_t + \rho Q_t \right]$ if we assume that the performance factor is $1$) since this is the only mechanism that allows $R$ to increase. in the following we derive a calculation that shows how much the fees need to increase to keep the APR invariant. Let the annualized staking APR be

$$
APR_t = 73\frac{R_t}{T_t} =73\frac{(1-\tau)[F_t+\rho Q_t]}{T_t},
$$

where:

- $F_t$ = transaction fees in epoch $t$,
- $Q_t$ = reserves,
- $T_t$ = circulating supply,
- $\rho$ = reserve decay rate.

Let the laws of motion be

$$
Q_{t+1}=(1-\rho)Q_t \qquad T_{t+1}=T_t+\rho Q_t.
$$

To keep APR constant,

$$
\frac{F_{t+1}+\rho Q_{t+1}}{T_{t+1}} = \frac{F_t+\rho Q_t}{T_t}, 
$$

giving:

$$
\Delta F_t = F_{t+1}-F_t =\rho^2Q_t+\frac{\rho Q_t}{T_t}R_t.
$$


Hence, maintaining APR can require very large percentage increases in fees given the low level that current fees represent for the reward pot. The following plot illustrate the necessary increment in fees to keep the current APR.

<p align="center">
  <img src="plots/fee_path_constant_apr.png" alt="Necessary Fee increment to keep APR" width="62%">
</p>



## Behavioral and equilibrium effects

This section identifies potential behavioral (or second-order) effects—primarily concerning delegator and operator decisions **given the current state**.



### Rational behavior



#### Delegators moving stake



#### Operators changing pledge, margin, or declared fixed cost



#### Entry or exit of pools



#### Pool splitting by multi-pool operators



#### Changes in staking participation


## Interaction effects (ToDo)

See the file analysis in the [interaction effects file](Interaction-effects/interaction_effects.md)







