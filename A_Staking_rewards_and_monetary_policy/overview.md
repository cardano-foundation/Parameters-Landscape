# Goal
This section analyzes how varying parameter values affects key protocol outcomes—such as operator and delegator rewards, decentralization, etc—while **keeping the underlying design fixed**. Structural changes—such as introducing new parameters or varying `minPoolCost` across pool sizes—are addressed in a separate section.

Generally, a parameter change can directly affect one type of actor, prompting a reaction that propagates through the network and influences other agents. For example, a change impacting operators may provoke a strategic response that subsequently affects other operators and delegators. While we discuss these broader feedback dynamics where relevant, this section focuses primarily on the direct impact of parameter changes on a given agent type.

# Summary of incentive-channel findings
(ToDo: update table based on the results and findings)

| Parameter Change | Mechanical Effect | Delegator Incentive | Operator Incentive | Decentralization Effect | Comments |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Increase $k$** | Lowers $z_0$. | Shift away from oversaturated pools. | - Operator of oversaturated pools may open new pools and redistribute delegation (whenever possible) and pledge. <br> - Does this measure improve small pool competitiveness? | Does it reduce stake concentration? | Does it lower efficiency? (More pools $\rightarrow$ higher aggregate fixed costs $\rightarrow$ higher aggregate reward dilution). |
| **Decrease $k$** | Raises $z_0$. | Stake can remain in larger pools. | Large pools gain appeal. | May increase concentration? | — |
| **Increase $a_0$** | Increases pledge premium. | Prefer high-pledge pools. | Operators need higher pledge to compete. | May favor capital-rich operators. | — |
| **Decrease $a_0$** | Lowers pledge premium. | Pledge impacts returns less. | Lowers entry barrier for low-pledge pools. | May improve entry, but weakens skin-in-the-game. | — |
| **Increase $c_{min}$** | Raises minimum operator fee. | Lowers net returns in small pools. | Protects minimum operator revenue. | May hurt small-pool competitiveness. | — |
| **Increase $\tau$** | Reduces staking reward pot. | Lowers staking yields. | Reduces pool profitability. | May reduce overall participation. | — |
| **Increase $\rho$** | Releases reserves faster. | Boosts short-term staking yields. | Boosts short-term pool profitability. | Improves immediate incentives, but risks long-term sustainability. | — |

