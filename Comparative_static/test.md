## Discussion (Alternative version) 
(ToDo: revise and improve. If k increases with $1<q<2$ or not and integer, can the operator maintain rewards by having 2 pools?)

The preceding analysis isolates the immediate effect of increasing $k$, holding pool structure, pledge, fees, and delegation fixed. A lower saturation threshold reduces the scale required for a pool to operate near saturation. 

These direct effects do not necessarily translate one-for-one into changes in operator revenue. Operators may adjust their pool structure, fees, and pledge allocation in response to the new saturation threshold. Pool splitting is a particularly relevant adjustment.

### Pool splitting as a response to an increase in $k$

Suppose that $k$ increases by a factor $q=2$, so that the saturation threshold changes from $z_0$ to $z_0'=\frac{z_0}{q}.$

Consider an operator who responds by dividing the original pool into $q$ identical pools, allocating $\sigma_i/q$ stake and $p_i/q$ pledge to each one. The reward function satisfies the proportionality property

$$
f\left(\frac{\sigma_i}{q},\frac{p_i}{q};\frac{z_0}{q}\right)=\frac{1}{q}f(\sigma_i,p_i;z_0).
$$

Consequently,

$$
qf\left(\frac{\sigma_i}{q},\frac{p_i}{q};\frac{z_0}{q}\right)=f(\sigma_i,p_i;z_0).
$$

Thus, under proportional splitting, the operator can preserve the original aggregate gross pool reward.

This result provides a useful benchmark: an increase in $k$ may reduce the reward of a large pool without producing an equivalent loss for the operator controlling it. If the operator can divide both pledge and delegation across additional pools, splitting can neutralize the direct effect of the lower saturation threshold.

However, the operator controls the allocation of pledge but does not directly control delegated stake. The calculation therefore assumes that delegators follow the operator into the newly created pools and redistribute their stake accordingly. The equality identifies a feasible reward-preserving configuration, not a prediction that this adjustment will necessarily occur.

The following plot compares the operator's revenue before the increase in $k$ with the revenue obtained after splitting into two identical pools:

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_k_split.png" alt="Operator reward after an increase in k and pool splitting" width="60%">
</p>

### Splitting incentives under a constant value of $k$

The previous result raises a separate question: is pool splitting attractive only as a response to an increase in $k$, or does the reward function already encourage sufficiently large pools to split when $k$ remains constant?

Holding $z_0$ fixed, compare the gross reward of one pool with the aggregate reward of two identical pools:

$$
f(\sigma_i,p_i;z_0) \quad\text{and}\quad 2f\left(\frac{\sigma_i}{2},\frac{p_i}{2};z_0\right).
$$

The comparison yields a threshold $\sigma_i^*>z_0$ such that

$$
f(\sigma_i,p_i;z_0)>2f\left(\frac{\sigma_i}{2},\frac{p_i}{2};z_0\right)\qquad\text{for } \sigma_i<\sigma_i^*,
$$

whereas the inequality reverses for $\sigma_i>\sigma_i^*$. Thus, splitting does not increase gross pool rewards while the original pool is unsaturated. It becomes beneficial only once the pool is sufficiently oversaturated.

This is an intended implication of the saturation mechanism. Once additional delegation no longer increases the reward of the original pool, the operator may obtain a higher aggregate reward by moving pledge and delegation into an additional pool.

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k.png" alt="Operator reward from one pool and two identical pools under the same k" width="60%">
</p>

The plot compares the revenue obtained from operating one pool with the total revenue obtained from two identical pools. The curves begin at $\sigma_i\geq p_i=700\text{k}$ ADA. Once the original pool becomes sufficiently oversaturated, splitting becomes more attractive because the two resulting pools make better use of the available stake below their respective saturation caps.

These results distinguish two effects:

1. **Reward preservation after an increase in $k$.** Proportional splitting can allow an operator to reproduce the aggregate reward obtained before the parameter change.
2. **The general incentive to split.** Even without a change in $k$, a sufficiently oversaturated pool may increase its aggregate reward by splitting.

An increase in $k$ is therefore not the source of the splitting incentive. Rather, by lowering $z_0$, it reduces the absolute pool size at which saturation and potential splitting become relevant. Accordingly, the following plot should not be interpreted as establishing that $k$ has no effect on splitting incentives in general. It compares the splitting premium under a particular parameterization:

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k_both.png" alt="Operator reward from splitting under different values of k" width="60%">
</p>

### Fixed-cost revenue and operator profit

The previous comparisons concern gross pool rewards or operator revenues rather than net profits. Operating an additional pool may generate another fixed-cost payment, but it may also require additional expenditure.

Let $Y_i^{(1)}$ denote the operator's revenue from one pool and $Y_i^{(2)}$ their aggregate revenue from two pools. Let $C_i(1)$ and $C_i(2)$ denote the corresponding actual operating costs. The profitability of splitting is determined by

$$
\Pi_i^{(2)}-\Pi_i^{(1)}
=======================

## \left[Y_i^{(2)}-Y_i^{(1)}\right]

\left[C_i(2)-C_i(1)\right].
$$

Consequently, receiving the fixed-cost payment twice does not by itself imply that splitting increases profit. Under the benchmark in which the additional declared fixed cost exactly equals the incremental cost of operating the second pool, the additional fixed-cost payment is offset by the additional expenditure.

For example, if the declared fixed cost equals the actual operating cost of one pool, operator profit can be written as

$$
\begin{aligned}
\Pi_i
&=
c_i+
\left(f(\sigma_i,p_i)-c_i\right)
\left[
m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}
\right]
-c_i,\
&=
\left(f(\sigma_i,p_i)-c_i\right)
\left[
m_i+(1-m_i)\frac{\hat p_i}{\sigma_i}
\right].
\end{aligned}
$$

Whether this benchmark is appropriate for a multi-pool operator depends on the incremental cost of opening another pool. An established operator may be able to reuse infrastructure, monitoring systems, technical expertise, branding, and administrative resources. If these economies of scope imply that

$$
C_i(2)-C_i(1)
$$

is smaller than the additional fixed-cost revenue, splitting becomes more profitable. Conversely, substantial additional operating costs may offset the revenue advantage.

This distinction may help explain the coexistence of medium-sized multi-pool operators with relatively few fully saturated pools, but establishing such a relationship requires empirical evidence on pool ownership and operating costs.

### Implications for small-pool competitiveness

Increasing $k$ creates two potentially opposing channels.

First, the **lower-scale channel** reduces the stake required to reach saturation. This may allow independent small or new operators to compete without attracting the amount of delegation required under the previous value of $k$.

Second, the **incumbent-replication channel** allows established operators to respond by creating additional pools. These operators may have advantages in attracting delegation because they can transfer reputation, branding, technical infrastructure, and existing delegator relationships to the new pools. If splitting raises their aggregate revenue or lowers their average operating cost, they may also be able to offer lower margins or declared fixed costs, subject to the protocol minimum.

Therefore, a higher $k$ does not necessarily transfer stake or revenue from large operators to independent small operators. It may instead redistribute stake across a larger number of pools controlled by the same operators. The relevant decentralization outcome consequently depends on whether the additional pools represent independent entry or replication by existing multi-pool operators.

The comparative statics alone cannot determine which channel dominates. They show that increasing $k$ lowers the efficient scale of an individual pool and creates incentives for affected operators to adjust their pool structure. Evaluating the resulting effect on small-pool competitiveness requires additional information about delegator mobility, operator ownership, reputation transfer, and the incremental cost of operating multiple pools.

Accordingly, changes in the number of pools or in pool-level stake concentration should not automatically be interpreted as equivalent changes in operator-level decentralization.
