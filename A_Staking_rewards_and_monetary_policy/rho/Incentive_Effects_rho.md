# Incentive effects of changing the Reserve Decay Rate ($\rho$)

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


Cardano funds staking rewards and its treasury through a combination of transaction fees and predefined monetary expansion from its reserve—the difference between the $45B$ ADA maximum supply and the circulating supply. For each epoch $t$, let's denote the reserve level by $Q_t$, transaction fees by $F_t$, the treasury share parameter by $\tau$ (currently $20\\%$), and the **reserve decay rate** (or monetary expansion parameter) by $\rho$ (currently $0.3\\%$).

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

$$\frac{\partial R_t}{\partial \rho} = (1 - \tau)\min\\{\eta_t, 1\\}\cdot Q_t<1.$$


### Operator gross revenue




### Delegator return per unit of stake




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







