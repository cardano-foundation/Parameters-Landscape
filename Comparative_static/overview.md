# Goal
This section covers comparative statics, specifically analyzing how changes in key parameters affect operator and delegator rewards.

# Increment in k

The direct effect ot an increment in **k** is to reduce the saturation threshold **$z_0$** and, hence, the maximum reward a pool can reach.
The following plots show its consequence in the reward formula **$f()$**. From the plot illustrtating the difference, it is clear that large pools will be negatively affected since their rewards are capped a a lower threshold (see the figure below). On the other hand, after the increment in **k**, medium-size pools become closer to the new saturation thershold where their rewards are maximized.
![Heatmap Reward function when k changes](output_plots/heatmap_reward_function_k_cases.png)



A lower saturation threshold when **k** raises has several key implications. First, smaller or newer pools require less pledge and delegation to reach maximum reward, making it easier and less costly to compete with established, large pools. However, a lower saturation threshold also caps the maximum rewards a single pool can earn. As a result, while small pools improve their competitivness for delegators (that do not want to leave the ecosystem), the lower reward ceiling may make the overall ecosystem less appealing to investors looking to maximize their staking returns.

This last point highlights a critical design dilemma: Should the mechanism prioritize small operator viability or delegator attraction? While a balanced approach sounds ideal, the precise definition of 'balance' is rarely specified. Furthermore, protocol design must account for long-term feedback loops. For example, a policy that boosts small operator viability at the expense of delegator returns risks triggering a negative spiral: higher operator viability leads to reduced delegator yields $\rightarrow$ delegators exit $\rightarrow$ network security declines $\rightarrow$ adoption drops $\rightarrow$ token price falls $\rightarrow$ operator viability ultimately collapses under lower prices and fewer remaining delegators.
