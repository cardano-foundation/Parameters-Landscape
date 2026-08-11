#!/usr/bin/env python3
"""
Operator viability at epoch 228 under k=150 vs counterfactual k=500.

Uses theoretical gross pool reward f(σ,p;z0) (not realized epoch rewards),
holding each pool's σ, pledges, margin, and declared cost fixed.

  f = (R/T)/(1+a0) * [σ̃ + a0 p̃ * inner / z0]
  σ̃ = min(σ, z0),  p̃ = min(p_declared, z0)
  inner = σ̃ - p̃ (z0 - σ̃)/z0

  Π = c + (f-c)[m + (1-m) p̂/σ]   if f > c, else Π = f
  r = Π / C*

  C* = (667/6) / 0.11  ADA/epoch   (OpEx $667 / month, ADA @ $0.11)

Writes CSV + side-by-side category bar charts into Data_PastIncrement_k/.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_228.csv"
OUT_CSV = DIR / "pool_viability_opex_k150_vs_k500_epoch_228.csv"
OUT_SUMMARY = DIR / "pool_viability_opex_k150_vs_k500_epoch_228_summary.csv"
OUT_BARS = DIR / "pool_viability_opex_categories_k150_vs_k500_epoch_228.png"
OUT_MD = DIR / "pool_viability_opex_k150_vs_k500_epoch_228.md"

FONT_SIZE = 12
A0 = 0.3
T_ADA = 32.04e9
R_ADA = 29.7e6
Z0_K150 = 213.58e6
Z0_K500 = 64.07e6
OPEX_EPOCH_USD = 667.0 / 6.0
ADA_USD = 0.11
C_STAR = OPEX_EPOCH_USD / ADA_USD  # ≈ 1010.61 ADA/epoch

COLOR_NONE = "#adb5bd"
# Darker red = worse (lower r); same palette as epoch-644 / minPoolCost viability
COLOR_LOSING_LT_025 = "#67000d"
COLOR_LOSING_025_050 = "#a50f15"
COLOR_LOSING_050_075 = "#de2d26"
COLOR_LOSING_075_100 = "#fc9272"
COLOR_EDGE = "#e76f51"
COLOR_COMF = "#4c78a8"
COLOR_STRONG = "#2a9d8f"

CAT_ORDER = [
    "no_rewards",
    "losing_lt_025",
    "losing_025_050",
    "losing_050_075",
    "losing_075_100",
    "edge",
    "comfortable",
    "strong",
]
CAT_LABELS = [
    "No rewards",
    r"$r<0.25$",
    r"$0.25\leq r<0.5$",
    r"$0.5\leq r<0.75$",
    r"$0.75\leq r<1$",
    "Edge\n"
    r"($1\leq r<2$)",
    "Comfortable\n"
    r"($2\leq r<5$)",
    "Strong\n"
    r"($r\geq5$)",
]
CAT_COLORS = [
    COLOR_NONE,
    COLOR_LOSING_LT_025,
    COLOR_LOSING_025_050,
    COLOR_LOSING_050_075,
    COLOR_LOSING_075_100,
    COLOR_EDGE,
    COLOR_COMF,
    COLOR_STRONG,
]


def gross_pool_reward(
    sigma: np.ndarray, p: np.ndarray, z0: float, R: float, T: float, a0: float
) -> np.ndarray:
    """Absolute-ADA form used in Plots-Parameter-k (r_scale = R/T)."""
    sigma = np.asarray(sigma, dtype=float)
    p = np.asarray(p, dtype=float)
    sigma_t = np.minimum(np.maximum(sigma, 0.0), z0)
    p_t = np.minimum(np.maximum(p, 0.0), z0)
    # pledge cannot exceed apparent stake for the inner term
    p_t = np.minimum(p_t, sigma_t)
    inner = sigma_t - p_t * (z0 - sigma_t) / z0
    r_scale = R / T
    return (r_scale / (1.0 + a0)) * (sigma_t + a0 * p_t * inner / z0)


def operator_reward(
    f: np.ndarray, m: np.ndarray, p_hat: np.ndarray, sigma: np.ndarray, c: np.ndarray
) -> np.ndarray:
    share = m + (1.0 - m) * np.clip(
        np.divide(p_hat, sigma, out=np.zeros_like(p_hat), where=sigma > 0), 0.0, 1.0
    )
    return np.where(f > c, c + (f - c) * share, f)


def classify_ratio(r: float) -> str:
    if not np.isfinite(r) or r <= 0:
        return "no_rewards"
    if r < 0.25:
        return "losing_lt_025"
    if r < 0.5:
        return "losing_025_050"
    if r < 0.75:
        return "losing_050_075"
    if r < 1.0:
        return "losing_075_100"
    if r < 2.0:
        return "edge"
    if r < 5.0:
        return "comfortable"
    return "strong"


def category_counts(cats: pd.Series) -> dict[str, int]:
    vc = cats.value_counts()
    return {c: int(vc.get(c, 0)) for c in CAT_ORDER}


def draw_panel(ax, counts: dict[str, int], title: str, note: str) -> None:
    heights = [counts[c] for c in CAT_ORDER]
    x = np.arange(len(CAT_ORDER))
    ax.bar(x, heights, color=CAT_COLORS, edgecolor="white", width=0.72)
    ymax = max(heights) if heights else 1
    for xi, h in zip(x, heights):
        ax.text(
            xi, h + ymax * 0.012, str(h), ha="center", va="bottom", fontsize=FONT_SIZE - 1
        )
    ax.set_xticks(x)
    ax.set_xticklabels(CAT_LABELS, fontsize=FONT_SIZE - 2, rotation=28, ha="right")
    ax.set_ylabel("Number of pools", fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE)
    ax.tick_params(axis="y", labelsize=FONT_SIZE)
    ax.tick_params(axis="x", labelsize=FONT_SIZE - 2, pad=2)
    ax.set_ylim(0, ymax * 1.18)
    ax.text(
        0.98,
        0.97,
        note,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=FONT_SIZE - 1,
        color="0.2",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="0.75", alpha=0.95),
    )


def main() -> None:
    df = pd.read_csv(POOLS_CSV)
    sigma = (
        pd.to_numeric(df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce")
        .fillna(0.0)
        / 1e6
    ).to_numpy()
    p_decl = (
        pd.to_numeric(df["pool_update.active.pledge"], errors="coerce").fillna(0.0) / 1e6
    ).to_numpy()
    # CSV `pledged` used as active pledge proxy (same convention as epoch-644 script)
    p_hat = (pd.to_numeric(df["pledged"], errors="coerce").fillna(0.0) / 1e6).to_numpy()
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce").fillna(0.0).to_numpy()
    c_decl = (
        pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce").fillna(0.0) / 1e6
    ).to_numpy()

    cases = {
        150: Z0_K150,
        500: Z0_K500,
    }

    out = pd.DataFrame(
        {
            "pool_id": df["pool_id"],
            "pool_ticker": df["pool_name.ticker"],
            "epoch_stake_ada": sigma,
            "declared_pledge_ada": p_decl,
            "active_pledge_ada": p_hat,
            "margin": margin,
            "declared_fixed_cost_ada": c_decl,
            "T_ada": T_ADA,
            "R_ada": R_ADA,
            "a0": A0,
            "opex_epoch_ada_Cstar": C_STAR,
            "ada_usd": ADA_USD,
        }
    )

    summary_rows: list[dict] = [
        {"quantity": "epoch", "value": 228},
        {"quantity": "n_pools", "value": len(out)},
        {"quantity": "T_ada", "value": T_ADA},
        {"quantity": "R_ada", "value": R_ADA},
        {"quantity": "a0", "value": A0},
        {"quantity": "ada_usd", "value": ADA_USD},
        {"quantity": "opex_month_usd", "value": 667.0},
        {"quantity": "opex_epoch_usd", "value": OPEX_EPOCH_USD},
        {"quantity": "opex_epoch_ada_Cstar", "value": C_STAR},
        {"quantity": "z0_k150_ada", "value": Z0_K150},
        {"quantity": "z0_k500_ada", "value": Z0_K500},
    ]

    panel_data: dict[int, dict] = {}

    for k, z0 in cases.items():
        f = gross_pool_reward(sigma, p_decl, z0, R_ADA, T_ADA, A0)
        # infeasible if pledge > stake
        f = np.where(p_decl > sigma, np.nan, f)
        pi = operator_reward(f, margin, p_hat, sigma, c_decl)
        r = pi / C_STAR
        cats = pd.Series([classify_ratio(float(x) if np.isfinite(x) else 0.0) for x in r])

        # treat non-finite f as no rewards
        cats = cats.where(np.isfinite(f) & (sigma > 0), "no_rewards")
        r = np.where(cats == "no_rewards", 0.0, r)
        pi = np.where(cats == "no_rewards", 0.0, pi)

        out[f"z0_k{k}_ada"] = z0
        out[f"f_ada_k{k}"] = f
        out[f"Pi_ada_k{k}"] = pi
        out[f"coverage_ratio_k{k}"] = r
        out[f"category_k{k}"] = cats.to_numpy()
        out[f"viable_k{k}"] = pi >= C_STAR

        counts = category_counts(cats)
        n_rewarded = int((cats != "no_rewards").sum())
        n_viable = int((pi >= C_STAR).sum())

        for cname, n in counts.items():
            summary_rows.append({"quantity": f"k{k}_n_{cname}", "value": n})
        summary_rows.extend(
            [
                {"quantity": f"k{k}_n_rewarded", "value": n_rewarded},
                {"quantity": f"k{k}_n_viable", "value": n_viable},
                {"quantity": f"k{k}_median_Pi_ada", "value": float(np.nanmedian(pi))},
                {"quantity": f"k{k}_median_f_ada", "value": float(np.nanmedian(f))},
            ]
        )
        panel_data[k] = {
            "counts": counts,
            "n_rewarded": n_rewarded,
            "n_viable": n_viable,
            "z0": z0,
        }

    # transition among continuing classifications
    for from_c in CAT_ORDER:
        for to_c in CAT_ORDER:
            n = int(
                ((out["category_k150"] == from_c) & (out["category_k500"] == to_c)).sum()
            )
            if n:
                summary_rows.append(
                    {"quantity": f"transition_{from_c}_to_{to_c}", "value": n}
                )

    out.to_csv(OUT_CSV, index=False)
    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(17.5, 6.2), constrained_layout=True)
    for ax, k in zip(axes, (150, 500)):
        d = panel_data[k]
        note = (
            f"Rewarded (theory): {d['n_rewarded']}\n"
            f"Cover OpEx: {d['n_viable']}"
        )
        draw_panel(
            ax,
            d["counts"],
            title=rf"$k={k}$ ($z_0={d['z0']/1e6:.2f}$ M ADA)",
            note=note,
        )

    fig.suptitle(
        "Epoch 228 — theoretical viability vs OpEx under $k=150$ vs $k=500$\n"
        rf"($C^*={C_STAR:.1f}$ ADA/epoch from $\$667$/mo at $\$0.11$/ADA; "
        rf"$r=\Pi_i/C^*$; $R={R_ADA/1e6:.1f}$M, $a_0={A0}$; stake/pledge held fixed)",
        fontsize=FONT_SIZE,
    )
    fig.savefig(OUT_BARS, dpi=300)
    print(f"Wrote {OUT_BARS}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"C* = {C_STAR:.4f} ADA/epoch")

    # markdown blurb
    c150, c500 = panel_data[150], panel_data[500]

    def losing_total(counts: dict[str, int]) -> int:
        return sum(counts[c] for c in CAT_ORDER if c.startswith("losing_"))

    md = f"""# Theoretical operator viability — epoch 228 ($k=150$ vs $k=500$)

Hold each pool's epoch-228 stake $\\sigma_i$, declared pledge $p_i$, active pledge $\\hat p_i$,
margin $m_i$, and declared fixed cost $c_i$ fixed. Recompute gross reward $f(\\sigma_i,p_i;z_0)$
and operator reward $\\Pi_i$ under $z_0=T/k$ for $k\\in\\{{150,500\\}}$.

Assumptions: $T={T_ADA/1e9:.2f}$B ADA, $R={R_ADA/1e6:.1f}$M ADA, $a_0={A0}$,
ADA price $\\$ {ADA_USD}$, monthly OpEx $\\$667$ ⇒
$C^*=(667/6)/{ADA_USD}={C_STAR:.1f}$ ADA/epoch.
$r=\\Pi_i/C^*$.

| | $k=150$ ($z_0={Z0_K150/1e6:.2f}$M) | $k=500$ ($z_0={Z0_K500/1e6:.2f}$M) |
| :--- | ---: | ---: |
| Pools (theory rewarded) | {c150['n_rewarded']} | {c500['n_rewarded']} |
| Cover OpEx ($r\\ge 1$) | {c150['n_viable']} | {c500['n_viable']} |
| Losing ($r<0.25$) | {c150['counts']['losing_lt_025']} | {c500['counts']['losing_lt_025']} |
| Losing ($0.25\\le r<0.5$) | {c150['counts']['losing_025_050']} | {c500['counts']['losing_025_050']} |
| Losing ($0.5\\le r<0.75$) | {c150['counts']['losing_050_075']} | {c500['counts']['losing_050_075']} |
| Losing ($0.75\\le r<1$) | {c150['counts']['losing_075_100']} | {c500['counts']['losing_075_100']} |
| Losing (all $0<r<1$) | {losing_total(c150['counts'])} | {losing_total(c500['counts'])} |
| Edge ($1\\le r<2$) | {c150['counts']['edge']} | {c500['counts']['edge']} |
| Comfortable ($2\\le r<5$) | {c150['counts']['comfortable']} | {c500['counts']['comfortable']} |
| Strong ($r\\ge 5$) | {c150['counts']['strong']} | {c500['counts']['strong']} |

Note: pledge columns in the historical CSV may be stamped from a later `pool_list`;
active pledge uses the `pledged` field (same convention as the epoch-644 viability script).
"""
    OUT_MD.write_text(md)
    print(f"Wrote {OUT_MD}")
    print(md)


if __name__ == "__main__":
    main()
