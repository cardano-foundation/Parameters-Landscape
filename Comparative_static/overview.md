# Goal
This section covers comparative statics, specifically analyzing how changes in key parameters affect operator and delegator rewards.

# Increment in k

![](output_plots/plot.png)


An increase in **k** lowers the saturation threshold, which has several key implications. First, smaller or newer pools require less pledge and delegation to reach maximum reward, making it easier and less costly to compete with established, large pools. However, a lower saturation threshold also caps the maximum rewards a single pool can earn. As a result, while small pools improve their competitivness for delegators (that do not want to leave the ecosystem), the lower reward ceiling may make the overall ecosystem less appealing to investors looking to maximize their staking returns.

This last point highlights a critical design dilemma: Should the mechanism prioritize small operator viability or delegator attraction? While a balanced approach sounds ideal, the precise definition of 'balance' is rarely specified. Furthermore, protocol design must account for long-term feedback loops. For example, a policy that boosts small operator viability at the expense of delegator returns risks triggering a negative spiral: higher operator viability leads to reduced delegator yields $\rightarrow$ delegators exit $\rightarrow$ network security declines $\rightarrow$ adoption drops $\rightarrow$ token price falls $\rightarrow$ operator viability ultimately collapses under lower prices and fewer remaining delegators.
