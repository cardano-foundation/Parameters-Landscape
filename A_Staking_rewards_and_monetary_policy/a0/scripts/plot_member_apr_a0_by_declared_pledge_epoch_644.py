#!/usr/bin/env python3
"""
Member APR by declared-pledge group: a0=0.3 vs a0=0.6 (epoch 644).

Declared pledge column: pool_update.active.pledge (lovelace → ADA).
Three absolute-pledge bins (among complete pools):
  Low:  p < 100k
  Mid:  100k ≤ p < 1M
  High: p ≥ 1M

For each pool and each a0:
  f_i(a0) from declared pledge; f=0 if active < declared.
  APR_i = 73 (1-m_i) max{f_i - c_i, 0} / σ_i

Boxplot: within each pledge bin, compare a0=0.3 vs 0.6 among
pledge-met pools with f>c under that a0.

Also reports median APR and subset (stake-weighted) APR per bin × a0.

Writes:
  member_apr_a0_by_declared_pledge_epoch_644.png
  member_apr_a0_by_declared_pledge_epoch_644.csv
  member_apr_a0_by_declared_pledge_epoch_644_summary.csv
  member_apr_a0_by_declared_pledge_epoch_644.md
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
OUT_PLOT = DIR / "member_apr_a0_by_declared_pledge_epoch_644.png"
OUT_CSV = DIR / "member_apr_a0_by_declared_pledge_epoch_644.csv"
OUT_SUMMARY = DIR / "member_apr_a0_by_declared_pledge_epoch_644_summary.csv"
OUT_MD = DIR / "member_apr_a0_by_declared_pledge_epoch_644.md"

FONT_SIZE = 12
EPOCHS_PER_YEAR = 73.0
A0_BASE = 0.3
A0_ALT = 0.6
# Absolute declared-pledge bins (ADA)
BIN_EDGES = (100_000.0, 1_000_000.0)
BIN_LABELS = (
    r"$p<100$K",
    r"$100$K$\leq p<1$M",
    r"$p\geq 1$M",
)
BIN_NAMES = ("low_lt_100k", "mid_100k_to_1M", "high_ge_1M")
COLOR_BASE = "#4c78a8"
COLOR_ALT = "#e76f51"
MEDIAN_COLOR = "#111111"


def gross_pool_reward(
    sigma: np.ndarray,
    declared_pledge: np.ndarray,
    *,
    z0: float,
    r_over_t: float,
    a0: float,
) -> np.ndarray:
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def member_apr(
    sigma: np.ndarray,
    f: np.ndarray,
    cost: np.ndarray,
    margin: np.ndarray,
) -> np.ndarray:
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def pledge_bin(declared: np.ndarray) -> np.ndarray:
    """0 = low, 1 = mid, 2 = high."""
    out = np.zeros(len(declared), dtype=int)
    out[declared >= BIN_EDGES[0]] = 1
    out[declared >= BIN_EDGES[1]] = 2
    return out


def subset_apr_pct(
    sigma: np.ndarray, apr: np.ndarray, mask: np.ndarray
) -> float:
    if not mask.any():
        return float("nan")
    return 100.0 * float(np.average(apr[mask], weights=sigma[mask]))


def main() -> None:
    params = json.loads(PARAMS_JSON.read_text())
    R = float(params["R_ada"])
    T = float(params["T_supply_ada"])
    k = int(params["k"])
    z0 = float(params["z0_ada"])
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
    bins = pledge_bin(declared_a)

    pledge_met = active_a >= declared_a
    f_base = np.where(
        pledge_met,
        np.maximum(
            gross_pool_reward(
                sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=A0_BASE
            ),
            0.0,
        ),
        0.0,
    )
    f_alt = np.where(
        pledge_met,
        np.maximum(
            gross_pool_reward(
                sigma_a, declared_a, z0=z0, r_over_t=r_over_t, a0=A0_ALT
            ),
            0.0,
        ),
        0.0,
    )
    apr_base = member_apr(sigma_a, f_base, cost_a, margin_a)
    apr_alt = member_apr(sigma_a, f_alt, cost_a, margin_a)
    elig_base = pledge_met & (f_base > cost_a)
    elig_alt = pledge_met & (f_alt > cost_a)

    out = pd.DataFrame(
        {
            "pool_id": df.loc[complete, "pool_id"].to_numpy(),
            "ticker": df.loc[complete, "pool_name.ticker"].to_numpy(),
            "sigma_ada": sigma_a,
            "declared_pledge_ada": declared_a,
            "declared_pledge_bin": [BIN_NAMES[b] for b in bins],
            "active_pledge_ada": active_a,
            "declared_pledge_met": pledge_met,
            "margin": margin_a,
            "fixed_cost_ada": cost_a,
            "f_ada_a0_0p3": f_base,
            "member_apr_a0_0p3": apr_base,
            "f_gt_c_a0_0p3": elig_base,
            "f_ada_a0_0p6": f_alt,
            "member_apr_a0_0p6": apr_alt,
            "f_gt_c_a0_0p6": elig_alt,
            "delta_member_apr": apr_alt - apr_base,
        }
    )
    out.to_csv(OUT_CSV, index=False)

    summary_rows: list[dict[str, float | int | str]] = []
    box_data: list[np.ndarray] = []
    box_labels: list[str] = []
    box_colors: list[str] = []

    for b, (bname, blabel) in enumerate(zip(BIN_NAMES, BIN_LABELS)):
        in_bin = bins == b
        for a0_val, apr, elig, color, tag in (
            (A0_BASE, apr_base, elig_base, COLOR_BASE, "0p3"),
            (A0_ALT, apr_alt, elig_alt, COLOR_ALT, "0p6"),
        ):
            mask = in_bin & elig
            vals_pct = 100.0 * apr[mask]
            med = float(np.median(vals_pct)) if mask.any() else float("nan")
            mean = float(np.mean(vals_pct)) if mask.any() else float("nan")
            subset = subset_apr_pct(sigma_a, apr, mask)
            summary_rows.append(
                {
                    "pledge_bin": bname,
                    "pledge_bin_label": blabel.replace("$", ""),
                    "a0": a0_val,
                    "n_pools_f_gt_c": int(mask.sum()),
                    "n_pools_in_bin_complete": int(in_bin.sum()),
                    "median_apr_pct": med,
                    "mean_apr_pct": mean,
                    "subset_apr_pct": subset,
                    "stake_ada": float(sigma_a[mask].sum()),
                }
            )
            box_data.append(vals_pct)
            box_labels.append(f"{blabel}\n$a_0={a0_val}$\n$(n={mask.sum()})$")
            box_colors.append(color)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, index=False)

    fig, ax = plt.subplots(figsize=(12.5, 5.4), constrained_layout=True)
    positions = []
    pos = 1.0
    for b in range(3):
        positions.extend([pos, pos + 0.85])
        pos += 2.4

    bp = ax.boxplot(
        box_data,
        positions=positions,
        widths=0.7,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": MEDIAN_COLOR, "linewidth": 2.2},
        whiskerprops={"color": "0.15", "linewidth": 1.1},
        capprops={"color": "0.15", "linewidth": 1.1},
        boxprops={"linewidth": 1.1},
    )
    for box, color in zip(bp["boxes"], box_colors):
        box.set_facecolor(color)
        box.set_alpha(0.75)
        box.set_edgecolor("0.2")

    ax.set_xticks(positions)
    ax.set_xticklabels(box_labels, fontsize=FONT_SIZE - 1)
    ymax = max((float(np.max(v)) for v in box_data if len(v)), default=3.0)
    ax.set_ylim(0.0, max(ymax * 1.08, 3.0))
    ax.set_ylabel("Member APR (%)", fontsize=FONT_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)

    # Light separators between pledge groups
    for x in (2.925, 5.325):
        ax.axvline(x, color="0.85", linewidth=1.0, zorder=0)

    from matplotlib.patches import Patch

    ax.legend(
        handles=[
            Patch(facecolor=COLOR_BASE, alpha=0.75, edgecolor="0.2", label=rf"$a_0={A0_BASE}$"),
            Patch(facecolor=COLOR_ALT, alpha=0.75, edgecolor="0.2", label=rf"$a_0={A0_ALT}$"),
        ],
        loc="upper right",
        fontsize=FONT_SIZE - 1,
    )
    fig.suptitle(
        "Epoch 644 — member APR by declared pledge: "
        rf"$a_0={A0_BASE}$ vs $a_0={A0_ALT}$"
        "\n"
        rf"($k={k}$; declared pledge = pool_update.active.pledge; "
        r"pledge-met, $f>c$; $\sigma,p,c,m$ fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_PLOT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    def pct_chg(new: float, old: float) -> str:
        if old == 0 or not np.isfinite(old) or not np.isfinite(new):
            return "—"
        return f"{100.0 * (new - old) / old:+.1f}%"

    table_lines = [
        "| Pledge bin | $a_0$ | Pools ($f>c$) | Median APR | Subset APR | Δ subset vs $a_0=0.3$ |",
        "|:---|---:|---:|---:|---:|---:|",
    ]
    for bname, blabel in zip(BIN_NAMES, BIN_LABELS):
        row0 = summary[
            (summary["pledge_bin"] == bname) & (summary["a0"] == A0_BASE)
        ].iloc[0]
        row1 = summary[
            (summary["pledge_bin"] == bname) & (summary["a0"] == A0_ALT)
        ].iloc[0]
        table_lines.append(
            f"| {blabel} | {A0_BASE} | {int(row0['n_pools_f_gt_c'])} | "
            f"{row0['median_apr_pct']:.2f}% | {row0['subset_apr_pct']:.2f}% | — |"
        )
        table_lines.append(
            f"| {blabel} | {A0_ALT} | {int(row1['n_pools_f_gt_c'])} | "
            f"{row1['median_apr_pct']:.2f}% | {row1['subset_apr_pct']:.2f}% | "
            f"{pct_chg(float(row1['subset_apr_pct']), float(row0['subset_apr_pct']))} |"
        )

    md = f"""# Member APR by declared pledge — $a_0={A0_BASE}$ vs $a_0={A0_ALT}$ (epoch 644)

**Declared pledge** is taken from `pool_update.active.pledge` (lovelace → ADA).
Active pledge (for the pledge-met check) is `pledged`.

Pledge bins (absolute declared pledge):
- Low: $p < 100$K
- Mid: $100$K $\\leq p < 1$M
- High: $p \\geq 1$M

$$
\\mathrm{{APR}}_i(a_0)
= 73\\,(1-m_i)\\,\\frac{{\\max\\{{f(\\sigma_i,p_i;a_0)-c_i,0\\}}}}{{\\sigma_i}},
$$

with $f=0$ when active pledge is below declared. Within each bin, statistics use
pledge-met pools with $f>c$ under that $a_0$.

**Subset APR** is the stake-weighted mean of $\\mathrm{{APR}}_i$ inside the bin
(same construction as network APR, restricted to the subset).

{chr(10).join(table_lines)}

Protocol: $k={k}$, $z_0={z0/1e6:.2f}$M ADA, $R={R/1e6:.2f}$M ADA, $T={T/1e9:.2f}$B ADA.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"Wrote {OUT_PLOT}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
