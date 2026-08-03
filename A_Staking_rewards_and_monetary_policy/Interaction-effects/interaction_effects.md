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

# Current design

This part studies the combined effects of changes in two or more parameters of the current rewards scheme design.

## k with minPoolCost ($c_{\min}$)

### Direct combined effects

The discussion combines a lower minimum fixed cost, $c_{\min}$, with a higher pool target, $k$. In the reward-sharing model, the two parameters act on different margins: $k$ changes the saturation threshold

$$
z_0(k)=\frac{1}{k},
$$

while $c_{\min}$ changes the feasible declared fixed cost $c_i$ and therefore the net reward available to delegators. 

Gross pool rewards are

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\tilde\sigma_i+a_0\tilde p_i\frac{\tilde\sigma_i-\tilde p_i\frac{z_0-\tilde\sigma_i}{z_0}}{z_0}\right],
\qquad
	ilde\sigma_i=\min\{\sigma_i,z_0\},\quad \tilde p_i=\min\{p_i,z_0\},
$$

implying


Holding gross rewards fixed, a lower $c_i$ raises the delegator return per unit stake. Gross pool rewards are still given by

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\tilde\sigma_i+a_0\tilde p_i\frac{\tilde\sigma_i-\tilde p_i\frac{z_0-\tilde\sigma_i}{z_0}}{z_0}\right],
\qquad
	ilde\sigma_i=\min\{\sigma_i,z_0\},\quad \tilde p_i=\min\{p_i,z_0\},
$$

On the other hand, holding gross pool rewards fixed, a lower $c_i$ raises the delegator return per unit stake since the delegator-facing return per unit stake depends on both the gross pool reward and the fixed-cost,

$$
r_i^D(k,c_i)=(1-m_i)\frac{\max\\{f(\sigma_i,p_i;k)-c_i,0\\}}{\sigma_i}.
$$

A combined increment in $k$ and a reduction in `minPoolCost` creates a push-pull effect on delegation incentives. Lowering $c_{\min}$ increases the net reward available on the pools that choose to reduce their fixed cost since $\partial{r}_i^D / \partial c_i<0$, while increasing $k$ lowers $z_0$ and makes large pools oversaturate sooner, pushing out delegators. The two changes are therefore complementary: the first improves the destination quality of smaller pools, and the second increases the incentive to leave large pools looking for better returns per unit of stake.

At the operator level, the direct mechanical effect is negative on operator gross revenues for both policy changes:

$$\Pi_i = c_i+(f(\sigma_i,p_i)-c_i)\left[m_i +(1-m_i)\frac{\hat{p}_i}{\sigma_i}\right], \qquad \partial \Pi_i/\partial c_i \geq 0.$$


A lower $c_{\min}$ reduces operator revenue, and a higher $k$ lowers gross rewards for pools above the new saturation threshold. 

Any improvement in the relative competitiveness of smaller pools comes form delegators and operators responding strategically.

### Behavioral and equilibrium effects

#### Rational behavior

We start from the frictionless non-myopic benchmark used throughout the reward-sharing analysis: forward-looking delegators and operators, truthful cost declaration ($c_i=\hat c_i$), and best responses after the parameters change.

The joint effect of $k$ and $c_{\min}$ enters through the post-shock ranking term

$$
P_i(k,c_{\min})=f(z_0(k),p_i)-c_i,
\qquad
D_i(k,c_{\min})=(1-m_i)\,[P_i(k,c_{\min})]_+.
$$

If the floor binds, $c_i=c_{\min}$, and the comparative statics are immediate:

$$
\frac{\partial P_i}{\partial k}<0,\qquad \frac{\partial P_i}{\partial c_{\min}}=-1.
$$

So the two changes reinforce each other for large pools and low-margin pools. The higher $k$ makes large pools less attractive through the smaller saturation threshold, while the lower $c_{\min}$ makes small pools more competitive by easing their fixed-cost burden.

##### Delegators moving stake

Delegators choose pools by expected net return per unit stake,

$$
r_i^D=(1-m_i)\frac{\max\{f(\sigma_i,p_i;k)-c_i,0\}}{\sigma_i}.
$$

A simple adjustment rule is

$$
\Delta\sigma_i^D=\eta\,\sigma_i\big(r_i^D-\bar r^D\big),
\qquad
\sigma_i'=\sigma_i+\Delta\sigma_i^D.
$$

Under the combined proposal, delegators leave oversaturated large pools more readily and are more willing to reallocate toward smaller pools because the new destination set is both larger (due to higher $k$) and better compensated (due to lower $c_{\min}$).

##### Operators changing pledge, margin, or declared fixed cost

Operator utility is still

$$
U_i=\Pi_i-\hat c_i,
\qquad
\Pi_i=c_i+(f(\sigma_i,p_i;k)-c_i)\left[m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\right].
$$

The relevant reduced-form best response is

$$
(c_i^*,m_i^*,\hat p_i^*)\in\arg\max_{c_i,m_i,\hat p_i}\;U_i\big(k,c_{\min},\sigma_i'(c_i,m_i,\hat p_i),c_i,m_i,\hat p_i\big)
\quad\text{s.t. }c_i\ge c_{\min}.
$$

The two parameters push different margins: a higher $k$ rewards higher pledge and smaller pool size, while a lower $c_{\min}$ gives operators more room to cut fixed fees and preserve delegation. For large pools, the dominant response is often split-and-reprice; for smaller pools, the relevant question is whether lower fixed costs are enough to offset the weaker reward level generated by the lower saturation threshold.

##### Entry or exit of pools

Entry and survival are governed by participation constraints evaluated at post-redelegation stake:

$$
U_i(k,c_{\min},\sigma_i')\ge 0,
\qquad
U_i^{\text{entry}}(k,c_{\min},\sigma_i')-F_i\ge 0.
$$

The interaction is important: a lower $c_{\min}$ relaxes the fixed-cost burden, but a higher $k$ can still make very large pools less attractive and free up delegation. The combined effect is strongest when the pool is close to the viability margin, because then the entry-exit decision depends on both direct profitability and the stake it can retain after redelegation.

##### Pool splitting by multi-pool operators

For an MPO controlling $n$ pools,

$$
\Pi^{\text{MPO}}(n)=\sum_{j=1}^{n}\Pi_j\big(k,c_{\min},\sigma_j',\hat p_j,m_j,c_j\big),
\qquad c_j\ge c_{\min}.
$$

Splitting is attractive if $\Pi^{\text{MPO}}(n+1)-\Pi^{\text{MPO}}(n)>0$. Raising $k$ increases the pressure to split because it lowers the saturation threshold, while lowering $c_{\min}$ reduces the fixed-cost penalty of maintaining additional pools. The combined reform therefore strengthens split incentives for medium-to-large operators, especially those able to reallocate pledge across multiple pools.

##### Changes in staking participation

Let total active stake be $S=\sum_i\sigma_i$. A reduced-form aggregate response is

$$
\Delta S=\chi\,\big(\bar r_{\text{exp}}(k,c_{\min})-r_{\text{alt}}\big).
$$

The increase in $k$ can raise the incentives to re-delegate and can therefore support higher participation if delegators view the new set of pools as more attractive. The lower $c_{\min}$ works in the same direction by improving the net returns of the small pools that become more relevant after the increase in $k$. In the rational benchmark, the combined effect is therefore more likely to redistribute stake across pools than to reduce total staking participation.

#### Behavioral deviations from the rational benchmark

We now keep the same five channels but allow market frictions, bounded rationality, and coordination limits.

##### Delegators moving stake

Observed migration is dampened by search costs and inattention:

$$
\Delta\sigma_i^{\text{obs}}=\lambda_i\,\Delta\sigma_i^D,
\qquad 0<\lambda_i<1.
$$

This matters more under the combined reform because the new destination set is larger but also more fragmented; even if the rational benchmark favors reallocation, actual migration can remain slow if acceptable alternatives are hard to find.

##### Operators changing pledge, margin, or declared fixed cost

With partial adjustment, operators move gradually toward the new optimum:

$$
c_{i,t+1}=\max\{c_{\min},\;c_{i,t}+\rho_c(c_i^*-c_{i,t})\},
$$
$$
m_{i,t+1}=m_{i,t}+\rho_m(m_i^*-m_{i,t}),
\qquad
\hat p_{i,t+1}=\hat p_{i,t}+\rho_p(\hat p_i^*-
\hat p_{i,t}),
$$

with $0<\rho_c,\rho_m,\rho_p\le 1$. In practice, this means that fee cuts, pledge reshuffling, and pool splitting need not happen at the same speed.

##### Entry or exit of pools

Hysteresis can be represented by thresholds around participation:

$$
U_i(k,c_{\min},\sigma_i')<-H_i^{\text{exit}},
\qquad
U_i^{\text{entry}}(k,c_{\min},\sigma_i')>H_i^{\text{entry}},
$$

with $H_i^{\text{entry}},H_i^{\text{exit}}>0$. This allows weak pools to persist longer than the rational benchmark predicts, especially when delegators are slow to reallocate from large pools after $k$ increases.

##### Pool splitting by multi-pool operators

Include coordination costs in expansion value:

$$
V^{\text{split}}(n)=\Pi^{\text{MPO}}(n)-K(n),
$$

where $K(n)$ is increasing and convex. The combined proposal can make splitting attractive, but only for operators with enough organizational capacity to keep the coordination cost below the added revenue from a larger $k$ and a lower fixed-cost floor.

##### Changes in staking participation

If delegators overweight short-run gains or losses, participation reacts to a salience-weighted objective:

$$
\Delta S_t=\chi_s\big(r_t-r_{\text{alt},t}\big)+\chi_l\,\mathbb E_t\!\left[\sum_{h\ge 1}\beta^h\big(r_{t+h}-r_{\text{alt},t+h}\big)\right],
$$

with $\chi_s>\chi_l$ under short-term salience. This can delay the full reallocation implied by the rational benchmark, even when the combined reform improves the long-run positioning of smaller pools.

## k with a0

## rho with tau

# Interaction with potential new parameters

## a0 with pledge leverage L
