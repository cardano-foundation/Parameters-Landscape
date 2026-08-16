#!/usr/bin/env python3
"""
Pool-split operator-reward comparison at epoch 644 under a0=0.3 vs a0=0.6.

Same 1→2 split as the minPoolCost exercise:
  σ' = σ/2,  p' = p/2 (declared),  p̂' = p̂/2 (active),
  same margin m, same declared fixed cost c in each half.

Scenario A: a0 = 0.3 (current).
Scenario B: a0 = 0.6 (same split rule; declared c unchanged).

Writes per-pool CSV, summary MD, increase/decrease bar chart, and
characteristic boxplots (increase vs decrease) for each a0 scenario.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_CSV = DIR / "pool_split_operator_reward_a0_epoch_644.csv"
OUT_MD = DIR / "pool_split_operator_reward_a0_epoch_644.md"
OUT_PLOT = DIR / "pool_split_operator_reward_a0_epoch_644.png"
OUT_TRAITS_A = DIR / "pool_split_traits_increase_vs_decrease_a0_0p3_epoch_644.png"
OUT_TRAITS_B = DIR / "pool_split_traits_increase_vs_decrease_a0_0p6_epoch_644.png"
OUT_SECTION = DIR / "pool_split_a0_section_epoch_644.md"

FONT_SIZE = 12
EPS = 1e-12
A0_BASE = 0.3
A0_ALT = 0.6
COLOR_INC = "#2a9d8f"
COLOR_DEC = "#e76f51"
MEDIAN_COLOR = "#111111"


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(
    f: np.ndarray,
    fixed_cost: np.ndarray,
    margin: np.ndarray,
    active_pledge: np.ndarray,
    sigma: np.ndarray,
) -> np.ndarray:
    pledge_share = np.clip(
        np.divide(
            active_pledge,
            sigma,
            out=np.zeros_like(active_pledge),
            where=sigma > 0,
        ),
        0.0,
        1.0,
    )
    operator_share = margin + (1.0 - margin) * pledge_share
    profitable = fixed_cost + (f - fixed_cost) * operator_share
    return np.where(f > fixed_cost, profitable, f)


def theoretical_pi(
    sigma: np.ndarray,
    declared: np.ndarray,
    active: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pledge_met = (active >= declared) & (sigma > 0)
    f_formula = gross_pool_reward(
        sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0
    )
    f = np.where(pledge_met, np.maximum(f_formula, 0.0), 0.0)
    pi = operator_reward(f, cost, margin, active, sigma)
    return f, pi, pledge_met


def classify_delta(delta: np.ndarray) -> tuple[int, int, int]:
    inc = int((delta > EPS).sum())
    dec = int((delta < -EPS).sum())
    same = int(len(delta) - inc - dec)
    return inc, dec, same


def _boxplot_whisker_ylim(
    series_list: list[pd.Series | np.ndarray],
) -> tuple[float, float]:
    lows: list[float] = []
    highs: list[float] = []
    for s in series_list:
        a = np.asarray(s, dtype=float)
        a = a[np.isfinite(a)]
        if a.size == 0:
            continue
        q1, q3 = np.percentile(a, [25.0, 75.0])
        iqr = q3 - q1
        lows.append(float(max(a.min(), q1 - 1.5 * iqr)))
        highs.append(float(min(a.max(), q3 + 1.5 * iqr)))
    if not lows:
        return 0.0, 1.0
    lo, hi = min(lows), max(highs)
    if hi <= lo:
        pad = abs(hi) * 0.05 + 1.0
        return lo - pad, hi + pad
    pad = 0.05 * (hi - lo)
    return lo - pad, hi + pad


def traits_series_bundle(df: pd.DataFrame) -> dict[str, list[pd.Series]]:
    return {
        "stake": [df["sigma_ada"] / 1e6],
        "active_pledge": [df["active_pledge_ada"] / 1e3],
        "declared_pledge": [df["declared_pledge_ada"] / 1e3],
        "margin": [df["margin"] * 100.0],
        "fixed_cost": [df["fixed_cost_ada"]],
    }


def shared_traits_ylims(
    group_dfs: list[pd.DataFrame],
) -> dict[str, tuple[float, float]]:
    keys = (
        "stake",
        "active_pledge",
        "declared_pledge",
        "margin",
        "fixed_cost",
    )
    ylims: dict[str, tuple[float, float]] = {}
    for key in keys:
        series: list[pd.Series] = []
        for g in group_dfs:
            series.extend(traits_series_bundle(g)[key])
        lo, hi = _boxplot_whisker_ylim(series)
        if key == "stake":
            lo = 0.0
            hi = float(np.ceil(hi / 10.0) * 10.0)
            if hi <= 0:
                hi = 10.0
            hi += 10.0
        else:
            span = hi - lo
            pad = 0.18 * span if span > 0 else abs(hi) * 0.1 + 1.0
            hi = hi + pad
            if lo > 0:
                lo = max(0.0, lo - 0.02 * span)
        ylims[key] = (lo, hi)
    return ylims


def plot_traits_inc_vs_dec(
    df: pd.DataFrame,
    inc_mask: np.ndarray,
    dec_mask: np.ndarray,
    *,
    out_path: Path,
    subtitle: str,
    note_line: str,
    ylims: dict[str, tuple[float, float]],
) -> None:
    inc = df.loc[inc_mask]
    dec = df.loc[dec_mask]
    groups = [
        (r"$\Pi$ increases" f"\n($n={len(inc)}$)", inc, COLOR_INC),
        (r"$\Pi$ decreases" f"\n($n={len(dec)}$)", dec, COLOR_DEC),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(11.5, 7.2), constrained_layout=True)

    def box_groups(
        ax: plt.Axes,
        series_by_group: list[pd.Series],
        ylabel: str,
        title: str,
        ylim: tuple[float, float],
        y_major: float | None = None,
        median_fmt: str = "{:.2f}",
    ) -> None:
        values = [s.dropna().to_numpy() for s in series_by_group]
        labels = [name for name, _, _ in groups]
        box = ax.boxplot(
            values,
            tick_labels=labels,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": MEDIAN_COLOR, "linewidth": 2.0},
        )
        for patch, (_, _, color) in zip(box["boxes"], groups):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
            patch.set_edgecolor("0.2")
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE - 1)
        ax.set_ylim(*ylim)
        if y_major is not None:
            ax.yaxis.set_major_locator(MultipleLocator(y_major))
        y0, y1 = ylim
        span = y1 - y0
        for i, arr in enumerate(values, start=1):
            if arr.size == 0:
                continue
            med = float(np.median(arr))
            q1, q3 = np.percentile(arr, [25.0, 75.0])
            iqr = q3 - q1
            top = float(min(arr.max(), q3 + 1.5 * iqr))
            y_text = top + 0.04 * span
            if y_text > y1 - 0.06 * span:
                y_text = y1 - 0.06 * span
            ax.text(
                i,
                y_text,
                median_fmt.format(med),
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
                color=MEDIAN_COLOR,
                clip_on=False,
            )

    box_groups(
        axes[0, 0],
        [inc["sigma_ada"] / 1e6, dec["sigma_ada"] / 1e6],
        "Epoch stake (M ADA)",
        "Delegation (epoch stake)",
        ylims["stake"],
        y_major=10.0,
        median_fmt="{:.2f}",
    )
    box_groups(
        axes[0, 1],
        [inc["active_pledge_ada"] / 1e3, dec["active_pledge_ada"] / 1e3],
        "Active pledge (k ADA)",
        "Active pledge",
        ylims["active_pledge"],
        median_fmt="{:.1f}",
    )
    box_groups(
        axes[0, 2],
        [inc["declared_pledge_ada"] / 1e3, dec["declared_pledge_ada"] / 1e3],
        "Declared pledge (k ADA)",
        "Declared pledge",
        ylims["declared_pledge"],
        median_fmt="{:.1f}",
    )
    box_groups(
        axes[1, 0],
        [inc["margin"] * 100.0, dec["margin"] * 100.0],
        "Declared margin (%)",
        "Margin",
        ylims["margin"],
        median_fmt="{:.1f}",
    )
    box_groups(
        axes[1, 1],
        [inc["fixed_cost_ada"], dec["fixed_cost_ada"]],
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
        ylims["fixed_cost"],
        median_fmt="{:.0f}",
    )
    axes[1, 2].axis("off")
    axes[1, 2].text(
        0.0,
        0.85,
        "Groups exclude pools with\n"
        r"unchanged $\Pi$ after the split."
        "\n\n"
        "Characteristics are from the\n"
        "unsplit epoch-644 snapshot\n"
        f"({note_line})."
        "\n\n"
        "Numbers above each box are\n"
        "the group median.",
        ha="left",
        va="top",
        fontsize=FONT_SIZE,
    )
    fig.suptitle(
        "Epoch 644 — characteristics of pools by split outcome\n" + subtitle,
        fontsize=FONT_SIZE,
    )
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _med(s: pd.Series) -> float:
    return float(s.median()) if len(s) else float("nan")


def traits_medians_md(inc: pd.DataFrame, dec: pd.DataFrame) -> str:
    rows = [
        ("Delegation (M ADA)", inc["sigma_ada"] / 1e6, dec["sigma_ada"] / 1e6),
        (
            "Active pledge (k ADA)",
            inc["active_pledge_ada"] / 1e3,
            dec["active_pledge_ada"] / 1e3,
        ),
        (
            "Declared pledge (k ADA)",
            inc["declared_pledge_ada"] / 1e3,
            dec["declared_pledge_ada"] / 1e3,
        ),
        ("Margin (%)", inc["margin"] * 100.0, dec["margin"] * 100.0),
        ("Declared fixed cost (ADA)", inc["fixed_cost_ada"], dec["fixed_cost_ada"]),
    ]
    lines = [
        "| Characteristic | Median ($\\Pi$↑) | Median ($\\Pi$↓) |",
        "|---|---:|---:|",
    ]
    for name, s_inc, s_dec in rows:
        lines.append(f"| {name} | {_med(s_inc):.2f} | {_med(s_dec):.2f} |")
    return "\n".join(lines)


def outcome_table(
    inc: int, dec: int, same: int, n: int, inc_m: int, dec_m: int, same_m: int, n_met: int
) -> str:
    return "\n".join(
        [
            "| Outcome | All complete pools | Pledge-met only |",
            "|---|---:|---:|",
            f"| $\\Pi$ increases after split | {inc} ({100 * inc / n:.1f}%) | "
            f"{inc_m} ({100 * inc_m / n_met:.1f}%) |",
            f"| $\\Pi$ decreases after split | {dec} ({100 * dec / n:.1f}%) | "
            f"{dec_m} ({100 * dec_m / n_met:.1f}%) |",
            f"| Unchanged | {same} ({100 * same / n:.1f}%) | "
            f"{same_m} ({100 * same_m / n_met:.1f}%) |",
        ]
    )


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])
    k = int(params["k"])
    r_over_t = R / T

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    )
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce")
        / 1e6
    )
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = (
        sigma.notna()
        & (sigma > 0)
        & declared.notna()
        & active.notna()
        & cost.notna()
        & margin.notna()
    )
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared[complete].to_numpy(dtype=float)
    active_a = active[complete].to_numpy(dtype=float)
    cost_a = cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)

    def split_delta(a0: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        kw = dict(z0=z0, r_over_t=r_over_t, a0=a0)
        f0, pi0, met0 = theoretical_pi(
            sigma_a, declared_a, active_a, cost_a, margin_a, **kw
        )
        f_h, pi_h, _ = theoretical_pi(
            sigma_a / 2.0,
            declared_a / 2.0,
            active_a / 2.0,
            cost_a,
            margin_a,
            **kw,
        )
        pi_split = 2.0 * pi_h
        return f0, pi0, f_h, pi_split, met0

    f0a, pi0a, f_ha, pi_splita, met0 = split_delta(A0_BASE)
    f0b, pi0b, f_hb, pi_splitb, _ = split_delta(A0_ALT)
    d_a = pi_splita - pi0a
    d_b = pi_splitb - pi0b

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].to_numpy(),
            "ticker": df.loc[complete, "pool_name.ticker"].to_numpy(),
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "active_pledge_ada": active_a,
            "fixed_cost_ada": cost_a,
            "margin": margin_a,
            "declared_pledge_met": met0,
            "f_unsplit_a0_0p3_ada": f0a,
            "pi_unsplit_a0_0p3_ada": pi0a,
            "f_half_a0_0p3_ada": f_ha,
            "pi_split_sum_a0_0p3_ada": pi_splita,
            "delta_pi_a0_0p3_ada": d_a,
            "split_increases_pi_a0_0p3": d_a > EPS,
            "split_decreases_pi_a0_0p3": d_a < -EPS,
            "f_unsplit_a0_0p6_ada": f0b,
            "pi_unsplit_a0_0p6_ada": pi0b,
            "f_half_a0_0p6_ada": f_hb,
            "pi_split_sum_a0_0p6_ada": pi_splitb,
            "delta_pi_a0_0p6_ada": d_b,
            "split_increases_pi_a0_0p6": d_b > EPS,
            "split_decreases_pi_a0_0p6": d_b < -EPS,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    n = len(out)
    n_met = int(met0.sum())
    inc_a, dec_a, same_a = classify_delta(d_a)
    inc_b, dec_b, same_b = classify_delta(d_b)
    d_a_m = d_a[met0]
    d_b_m = d_b[met0]
    inc_am, dec_am, same_am = classify_delta(d_a_m)
    inc_bm, dec_bm, same_bm = classify_delta(d_b_m)

    med_d_a = float(np.median(d_a))
    med_d_b = float(np.median(d_b))
    mean_d_a = float(np.mean(d_a))
    mean_d_b = float(np.mean(d_b))

    inc_a_df = out.loc[d_a > EPS]
    dec_a_df = out.loc[d_a < -EPS]
    inc_b_df = out.loc[d_b > EPS]
    dec_b_df = out.loc[d_b < -EPS]

    table_a = outcome_table(
        inc_a, dec_a, same_a, n, inc_am, dec_am, same_am, n_met
    )
    table_b = outcome_table(
        inc_b, dec_b, same_b, n, inc_bm, dec_bm, same_bm, n_met
    )
    traits_a = traits_medians_md(inc_a_df, dec_a_df)
    traits_b = traits_medians_md(inc_b_df, dec_b_df)

    md = rf"""# Epoch 644 — operator reward if each pool splits in two ($a_0$ scenarios)

Protocol parameters: $k={k}$, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B ADA.
Sample: $n={n}$ pools with complete fields ($\sigma>0$); $n={n_met}$ meet declared pledge.
Declared fixed costs and margins are held at the snapshot values in both scenarios.

For each pool we compute theoretical

$$
\Pi_i = c_i + (f_i-c_i)\bigl[m_i+(1-m_i)\hat p_i/\sigma_i\bigr]
\quad\text{{if }}f_i>c_i,\quad
\Pi_i=f_i\text{{ otherwise}},
$$

with $f_i=f(\sigma_i,p_i;a_0)$ and $f_i=0$ if active pledge is below declared pledge.

**Split counterfactual.** Each pool becomes two halves with

$$
\sigma'=\sigma_i/2,\quad p'=\hat p'=p_i/2,\quad
\text{{same }}m_i\text{{ and declared }}c_i\text{{ in each half}}.
$$

We compare $\Pi_i$ to $\Pi'+\Pi'=2\Pi(\sigma',p',\hat p',c_i,m_i;a_0)$.

## Scenario A — $a_0={A0_BASE}$ (current)

{table_a}

Median $\Delta\Pi=\Pi_{{\mathrm{{split}}}}-\Pi_{{\mathrm{{unsplit}}}}$: {med_d_a:.2f} ADA/epoch; mean: {mean_d_a:.2f} ADA/epoch.

### Characteristics (medians): $\Pi$↑ vs $\Pi$↓

{traits_a}

Plot: `{OUT_TRAITS_A.name}`.

## Scenario B — $a_0={A0_ALT}$

{table_b}

Median $\Delta\Pi$: {med_d_b:.2f} ADA/epoch; mean: {mean_d_b:.2f} ADA/epoch.

### Characteristics (medians): $\Pi$↑ vs $\Pi$↓

{traits_b}

Plot: `{OUT_TRAITS_B.name}`.

Per-pool detail: `{OUT_CSV.name}`.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    # Copy-paste section for the parameter landscape write-up
    section = f"""An increase in $a_0$ can affect the incentive to split one pool into multiple pools through opposing channels. On one side, splitting still collects declared fixed cost $c_i$ in each child pool, so the mechanical duplication gain from fixed cost remains. On the other side, $a_0$ governs how strongly pledge enters the gross reward $f(\\sigma_i,p_i)$. Raising $a_0$ intensifies the pledge channel while also shrinking rewards through the factor $1/(1+a_0)$. Because a $1\\to 2$ split halves both stake and pledge in each half, a higher $a_0$ changes how costly that pledge fragmentation is for operator rewards.

Pool desirability remains

$$
D_i=(1-m_i)\\frac{{f(\\sigma_i,p_i)-c_i}}{{\\sigma_i}},
$$

so the $a_0$ effect on post-split attractiveness is ambiguous: the pledge bonus can cushion losses for high-pledge halves, but the $1/(1+a_0)$ compression lowers $f$ for many pools. Operators must still divide pledge and existing stake, and delegator reallocation is not fully under their control.

Thus, increasing $a_0$ has an ambiguous overall effect on multi-pool operation: the fixed-cost duplication motive is unchanged in the declared-$c_i$ exercise, while the reward-function response to halved $(\\sigma,p)$ becomes more pledge-sensitive. Which effect dominates depends on pledge intensity, pool size relative to saturation, margins, and realized delegation responses.

We illustrate this with the same simple exercise as for $\\min$PoolCost. For each pool we compute the theoretical

$$
\\Pi_i = c_i + (f_i-c_i)\\bigl[m_i+(1-m_i)\\hat p_i/\\sigma_i\\bigr]
\\quad\\text{{if }}f_i>c_i,\\quad
\\Pi_i=f_i\\text{{ otherwise}},
$$

with $f_i=f(\\sigma_i,p_i;a_0)$ and $f_i=0$ if active pledge is below declared pledge.

Suppose each pool becomes two halves with

$$
\\sigma'=\\sigma_i/2,\\quad p'=p_i/2,\\quad \\hat p'=\\hat p_i/2,\\quad
\\text{{same }}m_i\\text{{ and declared }}c_i\\text{{ in each half}}.
$$

We then compare the unsplit reward $\\Pi_i$ with the split outcome $\\Pi'+\\Pi'=2\\Pi(\\sigma',p',\\hat p',c_i,m_i;a_0)$.

*Scenario A — current $a_0={A0_BASE}$*

{table_a}

Median $\\Delta\\Pi=\\Pi_{{\\mathrm{{split}}}}-\\Pi_{{\\mathrm{{unsplit}}}}$: {med_d_a:.2f} ADA/epoch; mean: {mean_d_a:.2f} ADA/epoch.

Under this scenario with $a_0={A0_BASE}$, a $1\\to 2$ split reduces operator reward for a majority of pledge-met pools ({100 * dec_am / n_met:.1f}% decrease vs {100 * inc_am / n_met:.1f}% increase). The next plot shows that gainers are much larger and more pledged.

<p align="center">
<img src="plots/{OUT_TRAITS_A.name}" alt="Operators incentives to split when a0=0.3" width="62%">
</p>

*Scenario B — $a_0={A0_ALT}$*

Declared fixed costs and margins are unchanged; only $a_0$ in $f(\\cdot)$ is raised.

{table_b}

Median $\\Delta\\Pi$: {med_d_b:.2f} ADA/epoch; mean: {mean_d_b:.2f} ADA/epoch.

When $a_0$ rises from {A0_BASE} to {A0_ALT}, the fraction of pledge-met pools that gain from splitting is {100 * inc_bm / n_met:.1f}% (vs {100 * inc_am / n_met:.1f}% under $a_0={A0_BASE}$), and the fraction that lose is {100 * dec_bm / n_met:.1f}% (vs {100 * dec_am / n_met:.1f}%). Mean $\\Delta\\Pi$ moves from {mean_d_a:.2f} to {mean_d_b:.2f} ADA/epoch. Gainers remain larger and more pledged than losers.

<p align="center">
<img src="plots/{OUT_TRAITS_B.name}" alt="Operators incentives to split when a0=0.6" width="62%">
</p>
"""
    OUT_SECTION.write_text(section, encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    scenarios = [
        (axes[0], rf"A: $a_0={A0_BASE}$", [inc_a, dec_a, same_a]),
        (axes[1], rf"B: $a_0={A0_ALT}$", [inc_b, dec_b, same_b]),
    ]
    colors = [COLOR_INC, COLOR_DEC, "#9e9e9e"]
    labels = [r"$\Pi$ increases", r"$\Pi$ decreases", "Unchanged"]
    for ax, title, counts in scenarios:
        x = np.arange(3)
        bars = ax.bar(x, counts, color=colors, edgecolor="0.2", width=0.72)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=FONT_SIZE - 1)
        ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(labelsize=FONT_SIZE - 1)
        ymax = max(counts) * 1.12 if max(counts) else 1.0
        ax.set_ylim(0, ymax)
        for bar, c in zip(bars, counts):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{c}\n({100 * c / n:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
            )
    fig.suptitle(
        r"Epoch 644: operator reward $\Pi$ after 1$\to$2 pool split"
        "\n"
        rf"($a_0\in\{{{A0_BASE},{A0_ALT}\}}$; same $m$, same declared $c_i$ per half; "
        r"half $\sigma$, $p$, $\hat p$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    ylims = shared_traits_ylims(
        [
            out.loc[d_a > EPS],
            out.loc[d_a < -EPS],
            out.loc[d_b > EPS],
            out.loc[d_b < -EPS],
        ]
    )
    plot_traits_inc_vs_dec(
        out,
        d_a > EPS,
        d_a < -EPS,
        out_path=OUT_TRAITS_A,
        subtitle=rf"Scenario A: $a_0={A0_BASE}$",
        note_line=rf"$a_0={A0_BASE}$",
        ylims=ylims,
    )
    plot_traits_inc_vs_dec(
        out,
        d_b > EPS,
        d_b < -EPS,
        out_path=OUT_TRAITS_B,
        subtitle=rf"Scenario B: $a_0={A0_ALT}$",
        note_line=rf"$a_0={A0_ALT}$",
        ylims=ylims,
    )

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_SECTION}")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_TRAITS_A}")
    print(f"Wrote {OUT_TRAITS_B}")
    print(f"Scenario A (a0={A0_BASE}): +{inc_a} / -{dec_a} / ={same_a}")
    print(f"Scenario B (a0={A0_ALT}): +{inc_b} / -{dec_b} / ={same_b}")
    print(
        f"Pledge-met A: +{inc_am} ({100*inc_am/n_met:.1f}%) / "
        f"-{dec_am} ({100*dec_am/n_met:.1f}%)"
    )
    print(
        f"Pledge-met B: +{inc_bm} ({100*inc_bm/n_met:.1f}%) / "
        f"-{dec_bm} ({100*dec_bm/n_met:.1f}%)"
    )
    print(f"Mean ΔΠ A={mean_d_a:.2f}, B={mean_d_b:.2f}")


if __name__ == "__main__":
    main()
