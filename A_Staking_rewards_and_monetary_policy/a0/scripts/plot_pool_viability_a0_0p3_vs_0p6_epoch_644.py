#!/usr/bin/env python3
"""
Theoretical pool viability at epoch 644: a0=0.3 vs a0=0.6.

U_i = Pi_i - C*,  r_i = Pi_i / C*, with C* = 741.1 ADA/epoch (667 USD/month,
six epochs, ADA at 0.15 USD). Only a0 changes; σ, p, p̂, c, m held fixed.

Writes:
  pool_viability_a0_0p3_vs_0p6_epoch_644.png          (paired category bars)
  pool_viability_losing_vs_edge_traits_a0_0p6_epoch_644.png
  pool_viability_a0_0p3_vs_0p6_epoch_644.csv
  pool_viability_a0_0p3_vs_0p6_epoch_644.md
  pool_viability_a0_section_epoch_644.md              (copy-paste section)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"
OUT_PLOT = DIR / "pool_viability_a0_0p3_vs_0p6_epoch_644.png"
OUT_TRAITS = DIR / "pool_viability_losing_vs_edge_traits_a0_0p6_epoch_644.png"
OUT_CSV = DIR / "pool_viability_a0_0p3_vs_0p6_epoch_644.csv"
OUT_MD = DIR / "pool_viability_a0_0p3_vs_0p6_epoch_644.md"
OUT_SECTION = DIR / "pool_viability_a0_section_epoch_644.md"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD
A0_BASE = 0.3
A0_ALT = 0.6

CATEGORY_ORDER = (
    "losing_lt_025",
    "losing_025_050",
    "losing_050_075",
    "losing_075_100",
    "edge",
    "comfortable",
    "strong",
)
CATEGORY_LABELS = (
    r"$r<0.25$",
    r"$0.25\leq r<0.5$",
    r"$0.5\leq r<0.75$",
    r"$0.75\leq r<1$",
    "Edge\n" r"($1\leq r<2$)",
    "Comfortable\n" r"($2\leq r<5$)",
    "Strong\n" r"($r\geq5$)",
)
CATEGORY_COLORS = (
    "#67000d",
    "#a50f15",
    "#de2d26",
    "#fc9272",
    "#e76f51",
    "#4c78a8",
    "#2a9d8f",
)


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
    s = margin + (1.0 - margin) * pledge_share
    return np.where(f > fixed_cost, fixed_cost + (f - fixed_cost) * s, f)


def classify(ratio: float) -> str:
    if ratio < 0.25:
        return "losing_lt_025"
    if ratio < 0.5:
        return "losing_025_050"
    if ratio < 0.75:
        return "losing_050_075"
    if ratio < 1.0:
        return "losing_075_100"
    if ratio < 2.0:
        return "edge"
    if ratio < 5.0:
        return "comfortable"
    return "strong"


def scenario_arrays(
    sigma: np.ndarray,
    declared: np.ndarray,
    active: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    pledge_met = (active >= declared) & (sigma > 0)
    f_raw = gross_pool_reward(
        sigma, declared, z0=z0, r_over_t=r_over_t, a0=a0
    )
    f = np.where(pledge_met, np.maximum(f_raw, 0.0), 0.0)
    pi = operator_reward(f, cost, margin, active, sigma)
    u = pi - C_STAR_ADA
    r = pi / C_STAR_ADA
    return f, pi, u, r, pledge_met


def counts_for(categories: np.ndarray, mask: np.ndarray) -> list[int]:
    ser = pd.Series(categories[mask]).value_counts()
    return [int(ser.get(c, 0)) for c in CATEGORY_ORDER]


def traits_table_md(
    df: pd.DataFrame,
    cat_col: str,
    *,
    r_col: str,
    pi_col: str,
) -> tuple[str, dict[str, int]]:
    deep = df[df[cat_col].isin(("losing_lt_025", "losing_025_050"))]
    near = df[df[cat_col].isin(("losing_050_075", "losing_075_100"))]
    edge = df[df[cat_col] == "edge"]
    strong = df[df[cat_col].isin(("comfortable", "strong"))]
    groups = [
        (rf"Losing \(r<0.5\) (n={len(deep)})", deep),
        (rf"Losing \(0.5\leq r<1\) (n={len(near)})", near),
        (rf"Edge (n={len(edge)})", edge),
        (rf"Comfortable+Strong (n={len(strong)})", strong),
    ]

    header = "| | " + " | ".join(g[0] for g in groups) + " |"
    sep = "|---|" + "|".join(["---:"] * len(groups)) + "|"
    rows_spec = [
        ("Epoch stake (M ADA), median", lambda g: g["sigma_ada"].median() / 1e6, "{:.2f}"),
        ("Active pledge (k ADA), median", lambda g: g["active_pledge_ada"].median() / 1e3, "{:.1f}"),
        ("Declared pledge (k ADA), median", lambda g: g["declared_pledge_ada"].median() / 1e3, "{:.1f}"),
        ("Declared fixed cost (ADA), median", lambda g: g["fixed_cost_ada"].median(), "{:.0f}"),
        ("Margin (%), median", lambda g: g["margin"].median() * 100.0, "{:.1f}"),
        ("Theoretical operator reward (ADA), median", lambda g: g[pi_col].median(), "{:,.0f}"),
        (r"Coverage ratio \(r\), median", lambda g: g[r_col].median(), "{:.3f}"),
    ]
    lines = [header, sep]
    for name, fn, fmt in rows_spec:
        cells = []
        for _, g in groups:
            if len(g) == 0:
                cells.append("—")
            else:
                cells.append(fmt.format(float(fn(g))))
        lines.append("| " + name + " | " + " | ".join(cells) + " |")
    sizes = {
        "deep": len(deep),
        "near": len(near),
        "edge": len(edge),
        "strong": len(strong),
    }
    return "\n".join(lines), sizes


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

    f0, pi0, u0, r0, met = scenario_arrays(
        sigma_a,
        declared_a,
        active_a,
        cost_a,
        margin_a,
        z0=z0,
        r_over_t=r_over_t,
        a0=A0_BASE,
    )
    f1, pi1, u1, r1, _ = scenario_arrays(
        sigma_a,
        declared_a,
        active_a,
        cost_a,
        margin_a,
        z0=z0,
        r_over_t=r_over_t,
        a0=A0_ALT,
    )
    cat0 = np.array(
        [classify(v) if m else "pledge_not_met" for v, m in zip(r0, met)]
    )
    cat1 = np.array(
        [classify(v) if m else "pledge_not_met" for v, m in zip(r1, met)]
    )

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].to_numpy(),
            "ticker": df.loc[complete, "pool_name.ticker"].to_numpy(),
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "active_pledge_ada": active_a,
            "fixed_cost_ada": cost_a,
            "margin": margin_a,
            "declared_pledge_met": met,
            "f_ada_a0_0p3": f0,
            "pi_ada_a0_0p3": pi0,
            "U_ada_a0_0p3": u0,
            "coverage_ratio_a0_0p3": r0,
            "category_a0_0p3": cat0,
            "f_ada_a0_0p6": f1,
            "pi_ada_a0_0p6": pi1,
            "U_ada_a0_0p6": u1,
            "coverage_ratio_a0_0p6": r1,
            "category_a0_0p6": cat1,
            "delta_U_ada": u1 - u0,
            "delta_r": r1 - r0,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    n_met = int(met.sum())
    n_unmet = int((~met).sum())
    heights0 = counts_for(cat0, met)
    heights1 = counts_for(cat1, met)
    n_losing0 = sum(heights0[:4])
    n_losing1 = sum(heights1[:4])
    n_viable0 = int((r0[met] >= 1.0).sum())
    n_viable1 = int((r1[met] >= 1.0).sum())
    n_edge0 = heights0[4]
    n_edge1 = heights1[4]

    # --- Elasticity metrics (pledge-met only) ---
    da0 = A0_ALT - A0_BASE
    share0 = n_viable0 / n_met
    share1 = n_viable1 / n_met
    # Extensive: change in viable share per unit a0 (pp if ×100)
    eta_ext = (share1 - share0) / da0
    # Intensive: mean/median Δr / Δa0
    dr = (r1 - r0)[met]
    eta_int_mean = float(np.mean(dr) / da0)
    eta_int_med = float(np.median(dr) / da0)
    # Arc elasticity of aggregate net surplus U = Pi - C*
    sum_u0 = float(u0[met].sum())
    sum_u1 = float(u1[met].sum())
    avg_u = 0.5 * (sum_u0 + sum_u1)
    avg_a0 = 0.5 * (A0_BASE + A0_ALT)
    if avg_u != 0 and da0 != 0:
        e_agg_u = ((sum_u1 - sum_u0) / abs(avg_u)) / (da0 / avg_a0)
    else:
        e_agg_u = float("nan")
    # Among currently viable (r0>=1): share that lose viability
    was_viable = met & (r0 >= 1.0)
    lost_viability = was_viable & (r1 < 1.0)
    gained_viability = met & (r0 < 1.0) & (r1 >= 1.0)
    n_lost = int(lost_viability.sum())
    n_gained = int(gained_viability.sum())

    # Paired bar chart
    fig, ax = plt.subplots(figsize=(12.0, 5.4), constrained_layout=True)
    x = np.arange(len(CATEGORY_ORDER))
    w = 0.38
    bars0 = ax.bar(
        x - w / 2,
        heights0,
        width=w,
        color=CATEGORY_COLORS,
        edgecolor="white",
        label=rf"$a_0={A0_BASE}$",
    )
    bars1 = ax.bar(
        x + w / 2,
        heights1,
        width=w,
        color=CATEGORY_COLORS,
        edgecolor="0.25",
        hatch="//",
        alpha=0.85,
        label=rf"$a_0={A0_ALT}$",
    )
    ymax = max(max(heights0), max(heights1)) * 1.18
    ax.set_ylim(0.0, ymax)
    for bars in (bars0, bars1):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + ymax * 0.01,
                f"{int(h)}",
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORY_LABELS, fontsize=FONT_SIZE - 1)
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.legend(fontsize=FONT_SIZE, loc="upper right")
    fig.suptitle(
        "Epoch 644 — theoretical viability vs OpEx: "
        rf"$a_0={A0_BASE}$ vs $a_0={A0_ALT}$"
        "\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; "
        r"$\sigma,p,\hat p,c,m$ fixed)",
        fontsize=FONT_SIZE,
    )
    ax.text(
        0.02,
        0.97,
        f"Pledge-met: {n_met}\n"
        rf"$a_0={A0_BASE}$: Losing={n_losing0}, Cover={n_viable0}, Edge={n_edge0}"
        "\n"
        rf"$a_0={A0_ALT}$: Losing={n_losing1}, Cover={n_viable1}, Edge={n_edge1}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=FONT_SIZE - 1,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "0.75",
            "alpha": 0.95,
        },
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    # Traits under a0=0.6 (Losing deep / near / Edge), matching original style
    analysis = out.loc[met].copy()
    analysis["category"] = analysis["category_a0_0p6"]
    analysis["blocks_minted"] = pd.to_numeric(
        df.loc[complete, "epochs.0.data.block.minted"], errors="coerce"
    ).to_numpy()[met]
    analysis["delegators"] = pd.to_numeric(
        df.loc[complete, "epochs.0.data.delegators"], errors="coerce"
    ).to_numpy()[met]

    losing_deep = analysis[
        analysis["category"].isin(("losing_lt_025", "losing_025_050"))
    ]
    losing_near = analysis[
        analysis["category"].isin(("losing_050_075", "losing_075_100"))
    ]
    edge = analysis[analysis["category"] == "edge"]
    trait_groups = [
        (r"Losing" "\n" r"($r<0.5$)", losing_deep, CATEGORY_COLORS[0]),
        (r"Losing" "\n" r"($0.5\leq r<1$)", losing_near, CATEGORY_COLORS[2]),
        ("Edge\n" r"($1\leq r<2$)", edge, CATEGORY_COLORS[4]),
    ]
    fig_t, axes = plt.subplots(3, 3, figsize=(13.5, 9.5), constrained_layout=True)
    median_color = "#111111"

    def box_groups(
        ax: plt.Axes,
        series_by_group: list[pd.Series],
        ylabel: str,
        title: str,
    ) -> None:
        values = [s.dropna().to_numpy() for s in series_by_group]
        labels = [f"{name}\n(n={len(df_g)})" for name, df_g, _ in trait_groups]
        box = ax.boxplot(
            values,
            tick_labels=labels,
            patch_artist=True,
            widths=0.55,
            showfliers=False,
            medianprops={"color": median_color, "linewidth": 2.0},
        )
        for patch, (_, _, color) in zip(box["boxes"], trait_groups):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        ax.set_ylabel(ylabel, fontsize=FONT_SIZE)
        ax.set_title(title, fontsize=FONT_SIZE)
        ax.tick_params(axis="both", labelsize=FONT_SIZE - 1)

    box_groups(
        axes[0, 0],
        [
            losing_deep["sigma_ada"] / 1e6,
            losing_near["sigma_ada"] / 1e6,
            edge["sigma_ada"] / 1e6,
        ],
        "Epoch stake (M ADA)",
        "Epoch stake",
    )
    box_groups(
        axes[0, 1],
        [
            losing_deep["active_pledge_ada"] / 1e3,
            losing_near["active_pledge_ada"] / 1e3,
            edge["active_pledge_ada"] / 1e3,
        ],
        "Active pledge (k ADA)",
        "Active pledge",
    )
    box_groups(
        axes[0, 2],
        [
            losing_deep["declared_pledge_ada"] / 1e3,
            losing_near["declared_pledge_ada"] / 1e3,
            edge["declared_pledge_ada"] / 1e3,
        ],
        "Declared pledge (k ADA)",
        "Declared pledge",
    )
    box_groups(
        axes[1, 0],
        [
            losing_deep["margin"] * 100.0,
            losing_near["margin"] * 100.0,
            edge["margin"] * 100.0,
        ],
        "Declared margin (%)",
        "Margin",
    )
    box_groups(
        axes[1, 1],
        [
            losing_deep["blocks_minted"],
            losing_near["blocks_minted"],
            edge["blocks_minted"],
        ],
        "Blocks minted (epoch)",
        "Blocks",
    )
    box_groups(
        axes[1, 2],
        [
            losing_deep["delegators"],
            losing_near["delegators"],
            edge["delegators"],
        ],
        "Delegators",
        "Delegators",
    )
    box_groups(
        axes[2, 0],
        [
            losing_deep["fixed_cost_ada"],
            losing_near["fixed_cost_ada"],
            edge["fixed_cost_ada"],
        ],
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
    )
    axes[2, 1].axis("off")
    axes[2, 1].text(
        0.0,
        0.9,
        f"Categories under $a_0={A0_ALT}$.\n"
        f"Not included:\n"
        f"• pledge not met: {n_unmet}",
        ha="left",
        va="top",
        fontsize=FONT_SIZE,
    )
    axes[2, 2].axis("off")
    fig_t.suptitle(
        rf"Epoch 644 — Losing vs Edge traits under $a_0={A0_ALT}$"
        "\n"
        rf"($C^*={C_STAR_ADA:.1f}$ ADA/epoch, $r=\Pi_i/C^*$; pledge-met pools)",
        fontsize=FONT_SIZE,
    )
    fig_t.savefig(OUT_TRAITS, dpi=160)
    plt.close(fig_t)

    traits_md_0, _ = traits_table_md(
        out.loc[met],
        "category_a0_0p3",
        r_col="coverage_ratio_a0_0p3",
        pi_col="pi_ada_a0_0p3",
    )
    traits_md_1, sizes1 = traits_table_md(
        out.loc[met],
        "category_a0_0p6",
        r_col="coverage_ratio_a0_0p6",
        pi_col="pi_ada_a0_0p6",
    )

    cat_table = "\n".join(
        [
            f"| Category | $a_0={A0_BASE}$ | $a_0={A0_ALT}$ | Δ |",
            "|---|---:|---:|---:|",
            f"| Losing ($r<0.25$) | {heights0[0]} | {heights1[0]} | {heights1[0]-heights0[0]:+d} |",
            f"| Losing ($0.25\\le r<0.5$) | {heights0[1]} | {heights1[1]} | {heights1[1]-heights0[1]:+d} |",
            f"| Losing ($0.5\\le r<0.75$) | {heights0[2]} | {heights1[2]} | {heights1[2]-heights0[2]:+d} |",
            f"| Losing ($0.75\\le r<1$) | {heights0[3]} | {heights1[3]} | {heights1[3]-heights0[3]:+d} |",
            f"| Edge ($1\\le r<2$) | {heights0[4]} | {heights1[4]} | {heights1[4]-heights0[4]:+d} |",
            f"| Comfortable ($2\\le r<5$) | {heights0[5]} | {heights1[5]} | {heights1[5]-heights0[5]:+d} |",
            f"| Strong ($r\\ge5$) | {heights0[6]} | {heights1[6]} | {heights1[6]-heights0[6]:+d} |",
            f"| **Cover OpEx ($r\\ge1$)** | **{n_viable0}** | **{n_viable1}** | **{n_viable1-n_viable0:+d}** |",
            f"| **Losing ($r<1$)** | **{n_losing0}** | **{n_losing1}** | **{n_losing1-n_losing0:+d}** |",
        ]
    )

    md = f"""# Epoch 644 theoretical viability — $a_0={A0_BASE}$ vs $a_0={A0_ALT}$

- Monthly OpEx: {MONTHLY_OPEX_USD:.0f} USD
- ADA price: {ADA_USD:.2f} USD/ADA
- $C^*={C_STAR_ADA:.1f}$ ADA per epoch
- Pledge-met pools: {n_met}; pledge not met: {n_unmet}
- Protocol: $k={k}$, $R={R/1e6:.2f}$M, $T={T/1e9:.2f}$B
- Only $a_0$ changes; $\\sigma,p,\\hat p,c,m$ fixed

$$
U_i=\\Pi_i-C^*,\\qquad r_i=\\Pi_i/C^*.
$$

{cat_table}

Transitions (pledge-met): lose viability ($r\\ge1\\to r<1$): {n_lost};
gain viability: {n_gained}.

## Characteristics under $a_0={A0_ALT}$ (pledge-met)

{traits_md_1}

## Elasticity of viability w.r.t. $a_0$

With $\\Delta a_0={da0:.1f}$:

| Metric | Definition | Value |
|---|---|---:|
| Extensive semi-elasticity $\\eta^{{\\mathrm{{ext}}}}$ | $(\\Delta$ share with $r\\ge1)/\\Delta a_0$ | {eta_ext:.4f} (share points per unit $a_0$) |
|  | same in percentage points | {100*eta_ext:.2f} pp per unit $a_0$ |
| Intensive semi-elasticity (mean) $\\eta^{{\\mathrm{{int}}}}$ | mean$(\\Delta r_i)/\\Delta a_0$ | {eta_int_mean:.4f} per unit $a_0$ |
| Intensive semi-elasticity (median) | median$(\\Delta r_i)/\\Delta a_0$ | {eta_int_med:.4f} per unit $a_0$ |
| Arc elasticity of aggregate $U$ | $\\dfrac{{\\Delta(\\sum U_i)/|\\overline{{\\sum U}}|}}{{\\Delta a_0/\\bar a_0}}$ | {e_agg_u:.3f} |

Interpretation: a unit increase in $a_0$ changes the viable-pool share by
about ${100*eta_ext:.2f}$ percentage points and shifts typical coverage $r$ by
about ${eta_int_med:.3f}$ (median).

Plots: `{OUT_PLOT.name}`, `{OUT_TRAITS.name}`.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    section = f"""#### Entry or exit of pools

Entry or exit can be analyzed with the participation constraint, which needs to take into account the actual fixed costs $\\hat c_i$ and opportunity costs (or outside options). Let

$$
U_i=\\Pi_i-\\hat c_i,
\\qquad
\\Pi_i=c_i+(f(\\sigma_i,p_i;a_0)-c_i)\\left[m_i+(1-m_i)\\frac{{\\hat p_i}}{{\\sigma_i}}\\right],
\\qquad
s_i\\equiv m_i+(1-m_i)\\frac{{\\hat p_i}}{{\\sigma_i}}\\in[0,1].
$$

It follows that a pool decides to participate when

$$
U_i\\ge \\underline{{U}}_i \\iff f_i\\ge f_i^{{\\star}} \\equiv \\frac{{\\underline{{U}}_i+\\hat c_i-(1-s_i)c_i}}{{s_i}},
$$

where $\\underline{{U}}_i$ denotes the outside option. For simplicity, let's assume $\\underline{{U}}_i=0$, however, a realistic outside option could be an annual return of $3\\%-5\\%$.

Notice that if there is truthful cost reporting ($c_i=\\hat c_i$), then the previous condition becomes $f_i\\ge c_i$. However, we have already argued that the data do not suggest truthful reporting.

Using actual data from epoch $644$, we hold delegation, pledges, margins, and declared fixed costs fixed, and recompute $\\Pi_i$ under $a_0={A0_BASE}$ and $a_0={A0_ALT}$. We assume that declared fixed cost is not the actual operating cost. In particular, all pools face the same OpEx

$$
C^*=667/6/0.15={C_STAR_ADA:.1f}\\text{{ ADA per epoch}}.
$$

We report $r_i=\\Pi_i/C^*$ (equivalently $U_i=\\Pi_i-C^*$, so $r_i<1\\iff U_i<0$). Among ${n_met}$ pledge-met pools, raising $a_0$ from ${A0_BASE}$ to ${A0_ALT}$ reduces the number that cover OpEx from ${n_viable0}$ to ${n_viable1}$ (${n_viable1-n_viable0:+d}$), and increases the Losing ($r<1$) count from ${n_losing0}$ to ${n_losing1}$. ${n_lost}$ pools cross from viable to losing; ${n_gained}$ move the other way.

<p align="center">
<img src="plots/{OUT_PLOT.name}" alt="Pools theoretical viability a0=0.3 vs 0.6" width="72%">
</p>

{cat_table}

The next chart shows characteristics of Losing and Edge pools under $a_0={A0_ALT}$.

<p align="center">
<img src="plots/{OUT_TRAITS.name}" alt="Pools characteristics losing and edge under a0=0.6" width="62%">
</p>

{traits_md_1}

Relative to $a_0={A0_BASE}$, the qualitative split between deep-losing ($r<0.5$) and near-edge losing ($0.5\\le r<1$) remains: tiny pools dominate the bottom of the distribution, while mid-sized pools populate $0.5\\le r<1$. Raising $a_0$ compresses operator rewards through $1/(1+a_0)$ for typical low-pledge pools, so more mass shifts into deeper Losing bins even though pledge intensity can cushion high-pledge pools.

##### Elasticity of viability with respect to $a_0$

Let $\\Delta a_0={A0_ALT}-{A0_BASE}={da0:.1f}$. A simple **extensive-margin semi-elasticity** of viability is

$$
\\eta^{{\\mathrm{{ext}}}}
=\\frac{{s({A0_ALT})-s({A0_BASE})}}{{\\Delta a_0}},
\\qquad
s(a_0)=\\frac{{\\#\\{{i:\\,r_i(a_0)\\ge 1\\}}}}{{N}},
$$

with $N={n_met}$ pledge-met pools. Empirically $\\eta^{{\\mathrm{{ext}}}}={eta_ext:.4f}$ (about ${100*eta_ext:.2f}$ percentage points of the viable share per unit of $a_0$).

An **intensive-margin semi-elasticity** of coverage is

$$
\\eta^{{\\mathrm{{int}}}}
=\\mathrm{{median}}_i\\left(\\frac{{r_i({A0_ALT})-r_i({A0_BASE})}}{{\\Delta a_0}}\\right)
={eta_int_med:.4f}
$$

(mean ${eta_int_mean:.4f}$). Finally, an arc elasticity of aggregate net surplus $U_i=\\Pi_i-C^*$ is

$$
E_{{\\sum U}}
=\\frac{{(\\sum_i U_i({A0_ALT})-\\sum_i U_i({A0_BASE}))/|\\overline{{\\sum U}}|}}{{\\Delta a_0/\\bar a_0}}
={e_agg_u:.3f}.
$$

These metrics summarize how one unit of $a_0$ maps into (i) how many pools clear the participation threshold and (ii) how far coverage ratios move for the typical pool.
"""
    OUT_SECTION.write_text(section, encoding="utf-8")

    print(f"C*={C_STAR_ADA:.4f}")
    print(f"pledge-met={n_met}, unmet={n_unmet}")
    print(f"a0={A0_BASE}: losing={n_losing0}, cover={n_viable0}, edge={n_edge0}")
    print(f"a0={A0_ALT}: losing={n_losing1}, cover={n_viable1}, edge={n_edge1}")
    print(f"lost viability={n_lost}, gained={n_gained}")
    print(f"eta_ext={eta_ext:.4f} ({100*eta_ext:.2f} pp/unit a0)")
    print(f"eta_int mean={eta_int_mean:.4f}, med={eta_int_med:.4f}")
    print(f"E_agg_U={e_agg_u:.3f}")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_TRAITS}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_SECTION}")


if __name__ == "__main__":
    main()
