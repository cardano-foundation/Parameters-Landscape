#!/usr/bin/env python3
"""
Pool-split operator-reward comparison at epoch 644.

For each pool with complete fields, compute theoretical operator reward Π_i,
then the sum of rewards if the pool splits into two identical halves:

  σ' = σ/2,  p' = p/2 (declared),  p̂' = p̂/2 (active),
  same margin m, same declared fixed cost c in each half.

Scenario A: original declared costs.
Scenario B: both the unsplit pool and each half use c' = 0.5 c.

Writes per-pool CSV, summary MD, increase/decrease bar chart, and
characteristic boxplots (increase vs decrease) for each cost scenario.
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
OUT_CSV = DIR / "pool_split_operator_reward_epoch_644.csv"
OUT_MD = DIR / "pool_split_operator_reward_epoch_644.md"
OUT_PLOT = DIR / "pool_split_operator_reward_epoch_644.png"
OUT_TRAITS_A = DIR / "pool_split_traits_increase_vs_decrease_epoch_644.png"
OUT_TRAITS_B = DIR / "pool_split_traits_increase_vs_decrease_c50_epoch_644.png"

FONT_SIZE = 12
EPS = 1e-12
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


def plot_traits_inc_vs_dec(
    df: pd.DataFrame,
    inc_mask: np.ndarray,
    dec_mask: np.ndarray,
    *,
    out_path: Path,
    subtitle: str,
) -> None:
    """Boxplots of pool characteristics: Π increases vs decreases."""
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

    box_groups(
        axes[0, 0],
        [inc["sigma_ada"] / 1e6, dec["sigma_ada"] / 1e6],
        "Epoch stake (M ADA)",
        "Delegation (epoch stake)",
    )
    box_groups(
        axes[0, 1],
        [inc["active_pledge_ada"] / 1e3, dec["active_pledge_ada"] / 1e3],
        "Active pledge (k ADA)",
        "Active pledge",
    )
    box_groups(
        axes[0, 2],
        [inc["declared_pledge_ada"] / 1e3, dec["declared_pledge_ada"] / 1e3],
        "Declared pledge (k ADA)",
        "Declared pledge",
    )
    box_groups(
        axes[1, 0],
        [inc["margin"] * 100.0, dec["margin"] * 100.0],
        "Declared margin (%)",
        "Margin",
    )
    box_groups(
        axes[1, 1],
        [inc["fixed_cost_ada"], dec["fixed_cost_ada"]],
        "Declared fixed cost (ADA)",
        "Declared fixed cost",
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
        r"(original declared $c_i$).",
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


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])
    k = int(params["k"])
    r_over_t = R / T
    kw = dict(z0=z0, r_over_t=r_over_t, a0=a0)

    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    )
    declared = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    )
    active = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    cost = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
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

    # Scenario A: original costs
    f0, pi0, met0 = theoretical_pi(
        sigma_a, declared_a, active_a, cost_a, margin_a, **kw
    )
    f_h, pi_h, met_h = theoretical_pi(
        sigma_a / 2.0,
        declared_a / 2.0,
        active_a / 2.0,
        cost_a,
        margin_a,
        **kw,
    )
    pi_split = 2.0 * pi_h
    d_a = pi_split - pi0

    # Scenario B: declared cost cut 50% before and after the split
    cost_half = 0.5 * cost_a
    f0b, pi0b, met0b = theoretical_pi(
        sigma_a, declared_a, active_a, cost_half, margin_a, **kw
    )
    f_hb, pi_hb, met_hb = theoretical_pi(
        sigma_a / 2.0,
        declared_a / 2.0,
        active_a / 2.0,
        cost_half,
        margin_a,
        **kw,
    )
    pi_split_b = 2.0 * pi_hb
    d_b = pi_split_b - pi0b

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
            "f_unsplit_ada": f0,
            "pi_unsplit_ada": pi0,
            "f_half_ada": f_h,
            "pi_half_ada": pi_h,
            "pi_split_sum_ada": pi_split,
            "delta_pi_ada": d_a,
            "split_increases_pi": d_a > EPS,
            "split_decreases_pi": d_a < -EPS,
            "f_unsplit_c50_ada": f0b,
            "pi_unsplit_c50_ada": pi0b,
            "f_half_c50_ada": f_hb,
            "pi_half_c50_ada": pi_hb,
            "pi_split_sum_c50_ada": pi_split_b,
            "delta_pi_c50_ada": d_b,
            "split_increases_pi_c50": d_b > EPS,
            "split_decreases_pi_c50": d_b < -EPS,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    n = len(out)
    n_met = int(met0.sum())
    inc_a, dec_a, same_a = classify_delta(d_a)
    inc_b, dec_b, same_b = classify_delta(d_b)
    # Among pledge-met only (unsplit pledge status)
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

    md = rf"""# Epoch 644 — operator reward if each pool splits in two

Protocol parameters: $k={k}$, $a_0={a0}$, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B ADA.
Sample: $n={n}$ pools with complete fields ($\sigma>0$); $n={n_met}$ meet declared pledge.

For each pool we compute theoretical

$$
\Pi_i = c_i + (f_i-c_i)\bigl[m_i+(1-m_i)\hat p_i/\sigma_i\bigr]
\quad\text{{if }}f_i>c_i,\quad
\Pi_i=f_i\text{{ otherwise}},
$$

with $f_i=f(\sigma_i,p_i)$ and $f_i=0$ if active pledge is below declared pledge.

**Split counterfactual.** Each pool becomes two halves with

$$
\sigma'=\sigma_i/2,\quad p'=\hat p'=p_i/2,\quad
\text{{same }}m_i\text{{ and declared }}c\text{{ in each half}}.
$$

We compare $\Pi_i$ to $\Pi'+\Pi'=2\Pi(\sigma',p',\hat p',c,m_i)$.

## Scenario A — original declared fixed costs

| Outcome | All complete pools | Pledge-met only |
|---|---:|---:|
| $\Pi$ increases after split | {inc_a} ({100*inc_a/n:.1f}%) | {inc_am} ({100*inc_am/n_met:.1f}%) |
| $\Pi$ decreases after split | {dec_a} ({100*dec_a/n:.1f}%) | {dec_am} ({100*dec_am/n_met:.1f}%) |
| Unchanged | {same_a} ({100*same_a/n:.1f}%) | {same_am} ({100*same_am/n_met:.1f}%) |

Median $\Delta\Pi=\Pi_{{\mathrm{{split}}}}-\Pi_{{\mathrm{{unsplit}}}}$: {med_d_a:.2f} ADA/epoch; mean: {mean_d_a:.2f} ADA/epoch.

### Characteristics (medians): $\Pi$↑ vs $\Pi$↓

{traits_medians_md(inc_a_df, dec_a_df)}

Plot: `{OUT_TRAITS_A.name}`.

## Scenario B — declared fixed cost cut 50% before and after the split

Both the unsplit pool and each half use $c'=c_i/2$ (no `minPoolCost` floor applied).

| Outcome | All complete pools | Pledge-met only |
|---|---:|---:|
| $\Pi$ increases after split | {inc_b} ({100*inc_b/n:.1f}%) | {inc_bm} ({100*inc_bm/n_met:.1f}%) |
| $\Pi$ decreases after split | {dec_b} ({100*dec_b/n:.1f}%) | {dec_bm} ({100*dec_bm/n_met:.1f}%) |
| Unchanged | {same_b} ({100*same_b/n:.1f}%) | {same_bm} ({100*same_bm/n_met:.1f}%) |

Median $\Delta\Pi$: {med_d_b:.2f} ADA/epoch; mean: {mean_d_b:.2f} ADA/epoch.

### Characteristics (medians): $\Pi$↑ vs $\Pi$↓

{traits_medians_md(inc_b_df, dec_b_df)}

Plot: `{OUT_TRAITS_B.name}`.

Per-pool detail: `{OUT_CSV.name}`.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    scenarios = [
        (
            axes[0],
            "A: original $c_i$",
            [inc_a, dec_a, same_a],
        ),
        (
            axes[1],
            r"B: $c'=c_i/2$ (before & after)",
            [inc_b, dec_b, same_b],
        ),
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
                f"{c}\n({100*c/n:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=FONT_SIZE - 2,
            )
    fig.suptitle(
        r"Epoch 644: operator reward $\Pi$ after 1$\to$2 pool split"
        "\n"
        r"(same $m$, same declared $c$ per half; half $\sigma$, $p$, $\hat p$)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=160)
    plt.close(fig)

    plot_traits_inc_vs_dec(
        out,
        d_a > EPS,
        d_a < -EPS,
        out_path=OUT_TRAITS_A,
        subtitle=r"Scenario A: original declared $c_i$",
    )
    plot_traits_inc_vs_dec(
        out,
        d_b > EPS,
        d_b < -EPS,
        out_path=OUT_TRAITS_B,
        subtitle=r"Scenario B: $c'=c_i/2$ before and after the split",
    )

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_TRAITS_A}")
    print(f"Wrote {OUT_TRAITS_B}")
    print("Scenario A (original c):", f"+{inc_a} / -{dec_a} / ={same_a}")
    print("Scenario B (c/2):       ", f"+{inc_b} / -{dec_b} / ={same_b}")


if __name__ == "__main__":
    main()
