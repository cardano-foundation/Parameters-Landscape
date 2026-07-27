## Discussion (Alternative version) 
(ToDo: revise and improve. If k increases with $1<q<2$ or not and integer, can the operator maintain rewards by having 2 pools?)

The preceding analysis isolates the immediate effect of increasing $k$, holding pool structure, pledge, fees, and delegation fixed. A lower saturation threshold reduces the scale required for a pool to operate near saturation. 

Since $z_0=\frac{1}{k},$ an increase in $k$ lowers the saturation threshold. Consequently, pools require less total stake to reach saturation and, for a given pledge ratio, less absolute pledge to operate at the scale at which rewards are maximized.

This direct comparative-static effect does not necessarily translate one-for-one into changes in operator income or market structure. Operators may react to the lower saturation threshold by reallocating pledge, adjusting their fees, or creating additional pools. Delegators may then respond by moving stake across the resulting pool structure. Pool splitting is therefore an important potential response to an increase in $k$.

### Pool splitting after an increase in $k$

Suppose that $k$ increases by a factor $q>1$. The new value of $k$ and the new saturation threshold are $k'=qk$ and $
z_0'=\frac{1}{k'}=\frac{z_0}{q}.$

The reward function satisfies the proportionality property

$$
f\left(
\frac{\sigma_i}{q},
\frac{p_i}{q};
\frac{z_0}{q}
\right) = \frac{1}{q}f(\sigma_i,p_i;z_0).
$$

This identity holds for any real $q>0$: proportionally reducing the pool's stake, pledge, and saturation threshold by the same factor reduces the reward assigned through $f(\cdot)$ by that factor.

However, the interpretation of this identity as a pool-splitting strategy requires $q$ to be an integer. If $q\in\mathbb{N}$, the operator can divide the original pool into $q$ identical pools, assigning stake $\sigma_i/q$ and pledge $p_i/q$ to each pool. Aggregate rewards assigned through $f(\cdot)$ are then

$$
qf\left(
\frac{\sigma_i}{q},
\frac{p_i}{q};
\frac{z_0}{q}
\right)=f(\sigma_i,p_i;z_0).
$$

Thus, proportional splitting preserves the aggregate reward assigned by the protocol when the proportional increase in $k$ coincides with the number of resulting pools. (ToDo: what if the operator does not split 50-50 but he splits by making one pool saturated and the rest of delegation and pledge goes to the other pool??)


This result concerns the aggregate reward assigned through $f(\cdot)$. It does not imply that the operator's revenue remains unchanged, because operator revenue also includes the fixed-cost payment.

Define the operator's share of the reward remaining after the fixed cost as

$$
\omega_i = m_i + (1-m_i)\frac{\hat p_i}{\sigma_i}.
$$

Before the change in $k$, operator revenue is

$$
Y_i^{\mathrm{single}} = c_i+ \left[f(\sigma_i,p_i;z_0)-c_i\right]\omega_i.
$$

Equivalently,

$$
Y_i^{\mathrm{single}} = f(\sigma_i,p_i;z_0)\omega_i + c_i(1-\omega_i).
$$

Under proportional splitting, the active pledge ratio remains unchanged:

$$
\frac{\hat p_i/q}{\sigma_i/q}= \frac{\hat p_i}{\sigma_i}.
$$

Therefore, the operator's share $\omega_i$ is the same in every resulting pool. If the operator creates $q$ identical pools and each pool declares the same fixed cost $c_i$, aggregate operator revenue becomes

$$
\begin{aligned}
Y_i^{\mathrm{split}}
&=q\left[c_i+\left(\frac{f(\sigma_i,p_i;z_0)}{q}-c_i\right)\omega_i\right],\\
&=f(\sigma_i,p_i;z_0)\omega_i+qc_i(1-\omega_i).
\end{aligned}
$$

The difference in gross operator revenue is consequently

$$
Y_i^{\mathrm{split}}-Y_i^{\mathrm{single}}=(q-1)c_i(1-\omega_i).
$$

Provided that each resulting pool earns enough to receive its declared fixed cost, splitting increases operator revenue whenever $c_i>0$ and $\omega_i<1.$

Therefore, when proportional splitting preserves aggregate rewards from $f(\cdot)$, it does more than neutralize the direct effect of the increase in $k$ on operator revenue. The operator receives the fixed-cost payment from each resulting pool and is therefore better off in gross-revenue terms.

The following plot illustrates this result for the case in which $k$ doubles and the original pool is divided into two identical pools:

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_k_split.png" alt="Operator revenue after an increase in k and pool splitting" width="60%">
</p>

Two qualifications are important.

First, the proportional increase in $k$ need not be an integer. For example, it may satisfy $
1<q<2.$ The proportionality identity remains mathematically valid, but the operator cannot create a non-integer number of pools. To analyze this case, it is necessary to distinguish the proportional change in $k$ from the number of pools created.

Let $n\in\mathbb{N}$ denote the number of identical pools operated after the change. Aggregate rewards assigned through $f(\cdot)$ are then

$$
F_n(q) = n f\left(\frac{\sigma_i}{n}, \frac{p_i}{n}; \frac{z_0}{q}\right).
$$

Exact replication of the original reward occurs when $n=q.$ When $q$ is not an integer, this adjustment cannot be implemented through an integer number of identical pools. For instance, if $k$ increases by $50%$, then $q=1.5.$

Splitting into two pools need not preserve the original aggregate reward. Nevertheless, it may still improve the operator's outcome relative to remaining in one pool under the new saturation threshold. The relevant comparison is therefore between

$$
n
f\left(
\frac{\sigma_i}{n},
\frac{p_i}{n};
\frac{z_0}{q}
\right)
$$

and

$$
f\left(
\sigma_i,p_i;
\frac{z_0}{q}
\right),
$$

rather than only between the post-splitting reward and the reward earned before the change in $k$.

Second, the operator directly controls the allocation of pledge but not the allocation of third-party delegation. The proportional-splitting calculation assumes that delegators follow the operator and redistribute their stake across the newly created pools. Whether this occurs depends on delegator mobility, loyalty, information, operator reputation, pool performance, and the ease with which delegators identify pools controlled by the same operator.

### Operator revenue and operator profit

The previous result concerns operator revenue rather than net profit. Operating an additional pool may allow the operator to collect another fixed-cost payment, but it may also create additional operating expenditure.

Suppose first that declared fixed costs are not directly tied to the operator's actual incremental costs. Under proportional splitting, gross operator revenue increases by

$$
(q-1)c_i(1-\omega_i).
$$

In that case, collecting the fixed-cost payment from several pools strengthens the incentive to split.

The conclusion changes under the assumed incentive-compatible benchmark in which each pool declares its actual operating cost. If the actual cost of operating each pool is $c_i$, profit from the original pool is

$$
\begin{aligned}
\Pi_i^{\mathrm{single}}
&=
c_i+
\left[
f(\sigma_i,p_i;z_0)-c_i
\right]\omega_i
-c_i,
\
&=
\left[
f(\sigma_i,p_i;z_0)-c_i
\right]\omega_i.
\end{aligned}
$$

After proportional splitting into $q$ pools, aggregate profit is

$$
\begin{aligned}
\Pi_i^{\mathrm{split}}
&=
q
\left[
c_i+
\left(
\frac{f(\sigma_i,p_i;z_0)}{q}-c_i
\right)\omega_i
-c_i
\right],
\
&=
\left[
f(\sigma_i,p_i;z_0)-qc_i
\right]\omega_i.
\end{aligned}
$$

The difference relative to the original pool is

$$
\Pi_i^{\mathrm{split}}-\Pi_i^{\mathrm{single}}-(q-1)c_i\omega_i.
$$

Thus, when aggregate rewards from $f(\cdot)$ are exactly preserved and operating costs are fully duplicated across pools, proportional splitting increases gross revenue but reduces net profit. The additional fixed-cost payments compensate the operator for the additional operating costs rather than constituting pure profit.

More generally, let $C_i(n)$ denote the actual total cost of operating $n$ pools. The change in profit from moving from one pool to $n$ pools is

$$
\Pi_i(n)-\Pi_i(1) = \left[
Y_i(n)-Y_i(1)
\right] - \left[
C_i(n)-C_i(1)
\right].
$$

Splitting is profitable whenever the additional operator revenue exceeds the incremental cost of operating the additional pools:

$$
Y_i(n)-Y_i(1) > C_i(n)-C_i(1).
$$

This distinction is important because multi-pool operators may experience economies of scale. An established operator may reuse infrastructure, monitoring systems, technical expertise, branding, and administrative resources across several pools. The incremental cost of operating an additional pool may therefore be lower than the cost of establishing the first pool.

If the incremental cost is below the additional fixed-cost revenue, splitting may increase net profit even after accounting for operating expenditures. Conversely, if costs are fully duplicated and truthfully declared, the apparent revenue advantage generated by the additional fixed-cost payment is offset by the cost of operating the additional pool.

### Incentives to split under a constant value of $k$

The previous analysis raises a separate question: can an operator find it profitable to split even when $k$ remains unchanged?

Holding $z_0$ fixed, compare the gross reward of a single pool with the aggregate gross reward obtained from two identical pools:

$$
f(\sigma_i,p_i;z_0)
$$

and

$$
2f\left(
\frac{\sigma_i}{2},
\frac{p_i}{2};
z_0
\right).
$$

There exists a threshold $\sigma_i^*>z_0$ such that

$$
f(\sigma_i,p_i;z_0) > 2f\left(\frac{\sigma_i}{2}, \frac{p_i}{2}; z_0 \right)
$$

for

$$
\sigma_i<\sigma_i^*,
$$

whereas the inequality reverses for

$$
\sigma_i>\sigma_i^*.
$$

Consequently, splitting does not increase aggregate rewards from $f(\cdot)$ while the original pool remains below saturation. It may also remain unattractive for pools that are only slightly oversaturated. Once the original pool becomes sufficiently oversaturated, however, splitting increases aggregate pool rewards because the two resulting pools make better use of stake below their respective saturation caps.

This is an intended implication of the saturation mechanism. Once additional delegation no longer increases the reward of the original pool, the operator may obtain a larger aggregate reward by reallocating pledge and delegation to an additional pool.

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k.png" alt="Operator revenue from one pool and two identical pools under the same k" width="60%">
</p>

The comparison changes when operator revenue, rather than only $f(\cdot)$, is considered.

Let

$$
f_i^{\mathrm{single}}=f(\sigma_i,p_i;z_0)
$$

and

$$
f_i^{\mathrm{half}}=f\left(\frac{\sigma_i}{2},\frac{p_i}{2};z_0\right).
$$

Revenue from the original pool is

$$
Y_i^{\mathrm{single}} = f_i^{\mathrm{single}}\omega_i + c_i(1-\omega_i),
$$

whereas aggregate revenue from two identical pools is

$$
Y_i^{\mathrm{split}} = 2f_i^{\mathrm{half}}\omega_i + 2c_i(1-\omega_i).
$$

Therefore,

$$
Y_i^{\mathrm{split}} - Y_i^{\mathrm{single}} \omega_i\left(2f_i^{\mathrm{half}}-f_i^{\mathrm{single}}
\right)
+
c_i(1-\omega_i).
$$

The first term captures the change in aggregate rewards assigned through $f(\cdot)$. The second term captures the additional fixed-cost revenue obtained from the second pool.

As a result, fixed-cost revenue strengthens the incentive to split. Splitting may increase operator revenue even when the increase in aggregate rewards from $f(\cdot)$ is small, or when aggregate rewards from $f(\cdot)$ decline moderately.

Under the incentive-compatible benchmark in which each pool's actual cost equals its declared fixed cost, the corresponding change in profit is

$$
\Pi_i^{\mathrm{split}} - \Pi_i^{\mathrm{single}}\omega_i\left(2f_i^{\mathrm{half}}-f_i^{\mathrm{single}}c_i
\right).
$$

Thus, under truthful cost declaration and fully duplicated costs, splitting is profitable only if the increase in aggregate rewards from $f(\cdot)$ is sufficiently large to cover the additional operating cost:

$$
2f_i^{\mathrm{half}}- f_i^{\mathrm{single}}>c_i.
$$

The following plot compares the returns from splitting under different values of $k$:

<p align="center">
  <img src="output_plots/operator_reward_vs_sigma_split_same_k_both.png" alt="Operator revenue from splitting under different values of k" width="60%">
</p>

A change in $k$ should not be interpreted as creating the incentive to split. Sufficiently oversaturated pools may already have an incentive to split under a constant value of $k$. Instead, increasing $k$ lowers the saturation threshold and changes which pools are oversaturated. It may therefore expand the range of pool sizes for which splitting becomes relevant.

### Implications for small-pool competitiveness

Increasing $k$ generates two potentially opposing effects on small-pool competitiveness.

The first is a **lower-scale effect**. A lower saturation threshold reduces the stake required for an independent small or new operator to operate near saturation. For a given pledge ratio, it also reduces the absolute pledge required to reach that scale. This lowers the scale at which a pool can compete with pools established under the previous value of $k$.

The second is an **incumbent-replication effect**. Established operators can respond to the lower saturation threshold by creating additional pools and reallocating pledge across them. These operators may have an advantage over independent entrants because they can transfer reputation, branding, technical infrastructure, and existing delegator relationships to their new pools.

If operating several pools increases aggregate operator revenue or generates economies of scope, the operator may also be able to reduce margins or declared fixed costs, subject to the protocol minimum. The resulting pools may therefore remain highly competitive for delegation even though the saturation threshold was lowered partly to create room for smaller pools.

Delegator behavior is central to the final effect. A splitting strategy is successful only if the operator can attract sufficient delegation to the additional pools. Delegators may follow an established operator because of its reputation and historical performance, but they may instead select independent pools if they value operator diversity or if those pools offer higher expected returns.

Consequently, an increase in $k$ does not necessarily transfer stake or revenue from large operators to independent small operators. It may instead redistribute stake across a larger number of pools controlled by the same operators.

This distinction is important when interpreting decentralization. A higher $k$ may produce:

1. a larger number of registered pools;
2. a less concentrated distribution of stake across pools; but
3. a much smaller change in the number of independent operators controlling those pools.

The comparative statics presented here do not determine which effect dominates. They show that increasing $k$ lowers the economic scale of an individual pool and changes the incentives of operators whose pools become oversaturated. Determining whether the resulting adjustment benefits independent small operators requires additional evidence on delegator mobility, common pool ownership, fee adjustments, reputation transfer, and the incremental cost of operating multiple pools.

Accordingly, a reduction in pool-level concentration should not automatically be interpreted as an equivalent reduction in operator-level concentration. The decentralization effect of increasing $k$ depends not only on how many pools exist and how stake is distributed among them, but also on who controls those pools.
