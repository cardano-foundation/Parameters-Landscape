# Incentive effects of changing `minPoolCost` ($c_{min}$)
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

The parameter $c_{\min}$ sets the minimum fixed cost that a stake pool operator may declare. It does not affect the pool's gross reward. Instead, the declared fixed cost is paid to the operator before the remaining rewards are divided between the operator and delegators.

The main objective of $c_{\min}$ is to support economically viable pool operation and provide some protection against Sybil attacks. Without a minimum fixed cost, an operator could create many pools, declare negligible costs, and offer returns that other operators may be unable to match.

The main trade-off is that a fixed cost affects small pools more strongly because it is spread over less stake. Its burden per unit of stake is approximately proportional to

$$
\frac{c_i}{\sigma_i}.
$$

A higher $c_{\min}$ can therefore protect operator revenues and discourage small, undercapitalized Sybil pools, but it also reduces the competitiveness of small and new pools and may push delegation toward larger pools. A lower $c_{\min}$ facilitates entry and improves small-pool returns, but may intensify fee competition and make it easier for multi-pool operators to expand.

The appropriate level of $c_{\min}$ therefore balances operator viability and Sybil resistance against entry, competition, and decentralization.

## Effects of change in $c_{min}$


### Direct mechanical effects 
In this section we consider the direct effects of changing the parameter while holding everything else equal (ceteris paribus). 

- **Gross pool rewards**

    The gross pool reward function does not depend on $c_{min}$:

  
- **Operator gross revenue**

  ![Heatmap Operator Reward when c changes](plots/heatmap_operator_reward_c_cases.png)
  
- **Delegator return per unit of stake**

  ![Heatmap Delegator Reward when c changes](plots/heatmap_delegator_reward_c_cases.png)
  
- **Oversaturated stake**
- **Reward-pot and treasury flows**



### Behavioral and equilibrium effects

### Decentralization

### 


### Interaction effects

### 


------
Increment in $c_{min}$
This parameter acts as a lower bound on the fixed costs an operator can declare for their pool(s). That is, while $c_{min}$ may change, each operator $i$ ultimately decides whether to update their declared fixed cost $c_i$ (this is particularly true if the $c_{min}$ is reduced, while operators may need to update if the $c_{min}$). In this subsection, we assume operators always set their fixed costs equal to $c_{min}$.



