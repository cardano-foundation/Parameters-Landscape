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

### Direct combined mechanical effects

The discussion combines a lower minimum fixed cost, $c_{\min}$, with a higher pool target, $k$. In the reward-sharing model, the two parameters act on different margins: $k$ changes the saturation threshold $z_0(k)=1/k,$ while $c_{\min}$ changes the feasible declared fixed cost $c_i$. 

#### Gross pool rewards $f(\sigma_i,p_i)$

Gross pool rewards are

$$
f(\sigma_i,p_i)=\frac{R}{1+a_0}\left[\widetilde{\sigma}_i+a_0\widetilde{p}_i\frac{\widetilde{\sigma}_i-\widetilde{p}_i\frac{z_0-\widetilde{\sigma}_i}{z_0}}{z_0}\right],
\qquad
\widetilde{\sigma}_i=\min\\{\sigma_i,z_0\\},\quad \widetilde{p}_i=\min\\{p_i,z_0\\}.
$$

Note that $c_{\min}$ does not enter $f(\cdot)$. Hence, there is not direct combined effect over $f_i$. The [incentive effects of a change in k](k/Incentive_Effects_k.md) analyses the change of $k$ over $f_i$. 

#### Operator gross revenue $\Pi_i$

Operator gross revenue is

$$
\Pi_i=c_i+(f(\sigma_i,p_i)-c_i)\underbrace{\left[m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}\right]}_{s_i\in[0,1]}, \qquad
\frac{\partial \Pi_i}{\partial c_i}=1-s_i\ge 0
$$

for the region where $f(\sigma_i,p_i)>c_i$. In this direct-effects comparison, we assume declared and active pledge coincide $p_i=\hat p_i.$


To isolate the direct combined shock ($k\uparrow$, $c_{\min}\downarrow$), keep $(m_i,\hat p_i,\sigma_i)$ fixed and let

$$
\Delta f_i=f_i' - f_i,
\qquad
\Delta c_i=c_i'-c_i\le 0.
$$

Then

$$
\Delta\Pi_i=s_i\,\Delta f_i+(1-s_i)\,\Delta c_i>0 \quad \iff
s_i(\Delta f_i-\Delta c_i)>-\Delta c_i.
$$

When $\Delta f_i>\Delta c_i$, this gives a threshold on $s_i$:

$$
s_i>s_i^*\equiv\frac{-\Delta c_i}{\Delta f_i-\Delta c_i}.
$$

Using $s_i=m_i+(1-m_i)\,q_i$ with $q_i\equiv\hat p_i/\sigma_i=p_i/\sigma_i$, the equivalent pledge-share threshold is

$$
q_i > q_i^{\*}\equiv\frac{s_i^{\*}-m_i}{1-m_i} =\frac{\frac{-\Delta c_i}{\Delta f_i-\Delta c_i}-m_i}{1-m_i}.
$$

Interpretation: pools far from the initial saturation point can have $\Delta f_i>0$ after $k$ increases, so they may offset the revenue loss from lowering $c_i$. Pools with low $q_i$ (and low effective $s_i$) are less able to offset that loss and are more likely to be harmed under the direct-effect comparison.

As a numerical illustration, take the baseline margin $m_i=5\\%$ and a binding fixed-cost reduction from $170$ ADA to $75$ ADA, so

$$
\Delta c_i=75-170=-95\text{ ADA}.
$$

Suppose that, for a given pool below the old saturation point, the direct effect of increasing $k$ from $500$ to $1000$ raises gross rewards by

$$
\Delta f_i=150\text{ ADA}.
$$

Then the operator-revenue threshold becomes

$$
s_i^*=\frac{95}{150+95}=\frac{95}{245}\approx 0.388,
$$

and, using $m_i=0.05$,

$$
q_i^*=\frac{0.388-0.05}{0.95}\approx 0.356.
$$

Therefore, under this example, a pool benefits mechanically from the combined shock only if its pledge share satisfies $p_i/\sigma_i=\hat p_i/\sigma_i\gtrsim 35.6\%$. Pools with lower pledge share are still hurt in direct operator revenue terms, even though their gross reward rises with the higher $k$.

#### Delegator return per unit stake $r_i^D$

Delegator-facing return per unit stake depends on both gross rewards and fixed costs,

$$
r_i^D(k,c_i)=(1-m_i)\frac{\max\{f(\sigma_i,p_i;k)-c_i,0\}}{\sigma_i}.
$$

For pools with positive distributable rewards ($f(\sigma_i,p_i;k)>c_i$),

$$
\frac{\partial r_i^D}{\partial c_i}<0.
$$

Hence, lowering $c_{\min}$ raises delegator returns for pools that reduce $c_i$, while increasing $k$ can reduce returns in now-oversaturated large pools. This is the direct push-pull mechanism on delegation incentives.

In summary, at the direct mechanical level, lowering $c_{\min}$ hurts operator gross revenue but helps delegator returns (for pools that cut costs), while increasing $k$ can reduce gross rewards and returns for oversaturated pools. Any net competitiveness gain for smaller pools in realized allocations comes from the equilibrium responses of delegators and operators, which we analyze next.

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
(c_i^{\*},m_i^{\*},\hat p_i^{\*})\in\arg\max_{c_i,m_i,\hat p_i}\;U_i\big(k,c_{\min},\sigma_i'(c_i,m_i,\hat p_i),c_i,m_i,\hat p_i\big)
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
c_{i,t+1}=\max\{c_{\min},\;c_{i,t}+\rho_c(c_i^{\*}-c_{i,t})\},
$$
$$
m_{i,t+1}=m_{i,t}+\rho_m(m_i^{\*}-m_{i,t}),
\qquad
\hat p_{i,t+1}=\hat p_{i,t}+\rho_p(\hat p_i^{\*}-
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
