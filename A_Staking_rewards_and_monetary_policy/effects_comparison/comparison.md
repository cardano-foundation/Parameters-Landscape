In this section, we compare the relative impacts of shocks across different parameters on key objectives, allowing us to identify the strongest drivers.

# Comparison of effects given the current state

This note puts the epoch-$644$ parameter shocks on **one sample** and **one cost cell**. The sample is the Active, pledge-met pools ($n=1,262$). Active is the complement of Inactive; Inactive is $\sigma=0$, unmet pledge, or zero blocks in the prior $15$ epochs. Declared pledge is the certificate active at the epoch ($p$); active pledge is $\hat p$, clipped to $\sigma$. The cost cell is $C^*=741.1$ ADA/epoch ($667$ USD/month at $0.15$ USD/ADA). Gross rewards use the snapshot $R=14,966,501.84$ ADA and $T=38,763,957,566.43$ ADA, except the $\rho$ column, which scales $R$ by $0.0042/0.003=1.4$. Stake, declared pledge, active pledge, and margins are held at the snapshot except in the last column.

The columns are:

- baseline: $k=500$, $a_0=0.3$, each pool's own declared $c_i$, $\rho=0.003$;
- $k=1000$;
- $a_0=0.6$;
- every declared $c_i$ set to $75$ ADA/epoch (this is **not** a move in $c_{\min}$; it forces the declared cost of every Active pool);
- $\rho=0.0042$;
- the three two-way joints $k{+}c$, $k{+}a_0$, and $a_0{+}c$;
- $k=1000$ after the idealized $D_i$ reallocation used in the $k$ note (empty pools with $\sigma>40$ million ADA into higher-$D_i$ receivers, cap $40$ million ADA, $\lambda=1$, no ecosystem exit).

The last column is the only one in which $\sigma$ moves. Frozen $\sigma$ does not change the pool-stake Nakamoto coefficient $N$; $c_i$ does not enter $f$, so $\sum\Delta f=0$ under $c_i=75$ and the change is a transfer between $\Pi$ and $f-\Pi$. A pool is counted as $r\ge 1$ when operator reward $\Pi$ covers $C^*$. Member APR is reported among pledge-met pools with $f>c$.

<p align="center">
<img src="plots/scoreboard_levels_epoch_644.png" alt="Scoreboard levels: n with r at least 1, median APR, Nakamoto N" width="95%">
</p>

<p align="center">
<img src="plots/scoreboard_deltas_epoch_644.png" alt="Scoreboard changes versus baseline" width="88%">
</p>

| Shock | $n$ ($\sigma>0$) | $n$ with $r\ge 1$ | $n$ with $r\ge 2$ | median $r$ | stake with $r\ge 1$ (B) | median APR | network APR | $n$ with $f>c$ | Nakamoto $N$ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | $1,262$ | $274$ | $125$ | $0.483$ | $11.91$ | $1.83\%$ | $1.66\%$ | $927$ | $159$ |
| $k=1000$ | $1,262$ | $253$ | $109$ | $0.480$ | $10.57$ | $1.54\%$ | $1.29\%$ | $927$ | $159$ |
| $a_0=0.6$ | $1,262$ | $239$ | $108$ | $0.470$ | $10.81$ | $1.46\%$ | $1.34\%$ | $884$ | $159$ |
| $c_i=75$ | $1,262$ | $192$ | $118$ | $0.171$ | $8.75$ | $1.96\%$ | $1.71\%$ | $1,118$ | $159$ |
| $\rho=0.0042$ | $1,262$ | $333$ | $170$ | $0.512$ | $13.72$ | $2.63\%$ | $2.35\%$ | $975$ | $159$ |
| $k=1000$, $c_i=75$ | $1,262$ | $152$ | $106$ | $0.170$ | $6.02$ | $1.80\%$ | $1.34\%$ | $1,118$ | $159$ |
| $k=1000$, $a_0=0.6$ | $1,262$ | $218$ | $100$ | $0.468$ | $9.39$ | $1.25\%$ | $1.04\%$ | $884$ | $159$ |
| $a_0=0.6$, $c_i=75$ | $1,262$ | $173$ | $104$ | $0.156$ | $7.93$ | $1.58\%$ | $1.39\%$ | $1,096$ | $159$ |
| $k=1000$ after $D_i$ | $1,052$ | $227$ | $68$ | $0.472$ | $7.45$ | $1.97\%$ | $1.88\%$ | $717$ | $267$ |

| Shock | $\Delta(n$ with $r\ge 1)$ | $\Delta(n$ with $r\ge 2)$ | $\Delta$ median APR (pp) | $\Delta$ network APR (pp) | $\Delta N$ | $\sum\Delta f$ | $\sum\Delta\Pi$ | $\sum\Delta(f-\Pi)$ |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| $k=1000$ | $-21$ | $-16$ | $-0.29$ | $-0.37$ | $0$ | $-1,463,591$ | $-453,971$ | $-1,009,619$ |
| $a_0=0.6$ | $-35$ | $-17$ | $-0.37$ | $-0.32$ | $0$ | $-1,085,986$ | $-180,128$ | $-905,858$ |
| $c_i=75$ | $-82$ | $-7$ | $+0.14$ | $+0.05$ | $0$ | $0$ | $-180,935$ | $180,935$ |
| $\rho=0.0042$ | $+59$ | $+45$ | $+0.80$ | $+0.69$ | $0$ | $2,585,033$ | $637,038$ | $1,947,995$ |
| $k=1000$, $c_i=75$ | $-122$ | $-19$ | $-0.03$ | $-0.32$ | $0$ | $-1,463,591$ | $-634,909$ | $-828,681$ |
| $k=1000$, $a_0=0.6$ | $-56$ | $-25$ | $-0.58$ | $-0.62$ | $0$ | $-2,321,080$ | $-596,496$ | $-1,724,584$ |
| $a_0=0.6$, $c_i=75$ | $-101$ | $-21$ | $-0.25$ | $-0.27$ | $0$ | $-1,085,986$ | $-355,704$ | $-730,282$ |
| $k=1000$ after $D_i$ | $-47$ | $-57$ | $+0.15$ | $+0.22$ | $+108$ | $-306,075$ | $-1,049,789$ | $743,714$ |

<p align="center">
<img src="plots/scoreboard_delta_f_split_epoch_644.png" alt="Delta f split into operator and delegator shares" width="88%">
</p>

The $\Delta f$ figure omits the after-$D_i$ column because $\sigma$ is not frozen there; that row is in the table.

### Frozen $\sigma$

Among the four single-parameter columns, **only** $\rho=0.0042$ raises both the count with $r\ge 1$ ($274\to 333$) and member APRs (median $1.83\%\to 2.63\%$, network $1.66\%\to 2.35\%$). It is also the only single shock with $\sum\Delta f>0$ ($\sum\Delta f=2,585,033$). Operators receive $24.6\%$ of that extra ADA ($\sum\Delta\Pi=637,038$); the rest is $f-\Pi$. The expansion in $n$ with $f>c$ is modest ($927\to 975$): most of the extra $f$ lands in pools that already cleared $c$.

The other three singles cut the count with $r\ge 1$, but they do not do the same thing.

- $c_i=75$ is the largest single cut in that count ($274\to 192$, $\Delta=-82$) and in median $r$ ($0.483\to 0.171$). Because $c$ does not enter $f$, $\sum\Delta f=0$ and $\sum\Delta\Pi=-180,935=-\sum\Delta(f-\Pi)$. More pools have $f>c$ ($927\to 1,118$), so the APR sample is not the same $927$ pools; median APR among $f>c$ rises to $1.96\%$. That is a transfer plus a change in who is in the APR set, not a larger pie.
- $k=1000$ cuts the count with $r\ge 1$ only to $253$ ($\Delta=-21$), but it is the larger single cut in **network** APR ($-0.37$ pp, to $1.29\%$). Newly oversaturated pools ($n=214$, $E(k)=4.81$ billion ADA above $z_0$) account for almost all of $\sum\Delta f=-1,463,591$. The count with $f>c$ stays $927$: $k$ does not move $c$, and the pools that already had $f\le c$ are not the ones saturating. Operators receive $31.0\%$ of the lost $f$ ($\sum\Delta\Pi=-453,971$).
- $a_0=0.6$ hits the whole sample through $f(\sigma,p;a_0)$, not only the newly oversaturated tail. The count with $r\ge 1$ falls to $239$ ($\Delta=-35$); $n$ with $f>c$ falls to $884$; median APR falls to $1.46\%$. $\sum\Delta f=-1,085,986$, of which operators take $16.6\%$ ($\sum\Delta\Pi=-180,128$). Stake Nakamoto $N$ is $159$ in every frozen-$\sigma$ column.

The joints are not sums of the singles.

- $k{+}c$ has the fewest pools with $r\ge 1$ ($152$). $\sum\Delta f$ equals the $k$ column ($-1,463,591$); $c$ only reallocates that $f$. $\sum\Delta\Pi=-634,909$ is the $k$ operator loss plus the $c$ transfer. Median APR is almost unchanged ($-0.03$ pp) because the two singles move it in opposite directions; network APR still falls $0.32$ pp.
- $k{+}a_0$ is the worst frozen-$\sigma$ column for APRs (median $1.25\%$, network $1.04\%$) and for $|\sum\Delta f|$ ($\sum\Delta f=-2,321,080$). That joint cut is **smaller** than the sum of the isolated $k$ and $a_0$ cuts ($1,463,591+1,085,986=2,549,577$): the two $f$-shocks overlap on the same pools. Operators receive $25.7\%$ of the joint $\Delta f$.
- $a_0{+}c$ inherits $\sum\Delta f$ from $a_0$ ($-1,085,986$). $\sum\Delta\Pi=-355,704$ is more negative than $a_0$ alone by about the $c$ transfer. The count with $r\ge 1$ is $173$.

### After $D_i$ ($k=1000$ only)

The last column is not a frozen-$\sigma$ parameter shock. It takes $k=1000$ and moves snapshot stake under the $D_i$ rule of the $k$ note. Two hundred ten donors are emptied, so $n$ with $\sigma>0$ is $1,052$. Median APR among remaining $f>c$ is $1.97\%$ and network APR is $1.88\%$ — both **above** the $k=500$ baseline. Nakamoto $N$ rises from $159$ to $267$. The count with $r\ge 1$ is $227$, still below $274$: covering large pools are among the emptied donors, and receivers are filled only to $40$ million ADA.

Relative to baseline, $\sum\Delta f=-306,075$: most of the frozen $k=1000$ cut of $1,463,591$ is recovered once stake leaves the cap. Operators as a group still lose ($\sum\Delta\Pi=-1,049,789$) because emptied pools take $\Pi$ to zero; remaining $f-\Pi$ rises ($\sum\Delta(f-\Pi)=743,714$). This column is the only one in which $N$ moves. The same $D_i$ rule is **not** applied here to $a_0$, $c_i$, or $\rho$: those levers do not create a new saturation cap, so there is no analogous emptying of $\sigma>40$ million ADA.
