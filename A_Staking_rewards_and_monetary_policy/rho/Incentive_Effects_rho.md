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



## Direct mechanical effects 
In this section we consider the direct effects of **changing** $\rho$ while holding everything else equal (ceteris paribus). 

### Gross pool rewards



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







