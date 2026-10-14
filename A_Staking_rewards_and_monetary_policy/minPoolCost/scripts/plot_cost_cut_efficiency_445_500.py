#!/usr/bin/env python3
"""Delegator response to fixed-cost cuts (445->500) on continuing Active pools."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pastreduction_common import load_active

DIR = Path(__file__).resolve().parent
OUT_PNG = DIR / "cost_cut_efficiency_445_500.png"
OUT_CSV = DIR / "cost_cut_efficiency_445_500.csv"


def main() -> None:
    a = load_active(445).set_index("pool_id")
    b = load_active(500).set_index("pool_id")
    common = a.index.intersection(b.index)

    fa = pd.to_numeric(a.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    fb = pd.to_numeric(b.loc[common, "pool_update.active.fixed_cost"], errors="coerce")
    da = pd.to_numeric(a.loc[common, "epochs.0.data.delegators"], errors="coerce")
    db = pd.to_numeric(b.loc[common, "epochs.0.data.delegators"], errors="coerce")
    sa = pd.to_numeric(a.loc[common, "active_stake"], errors="coerce")
    sb = pd.to_numeric(b.loc[common, "active_stake"], errors="coerce")

    cut = fb < fa
    df = pd.DataFrame(
        {
            "pool_id": common,
            "cost_445_lovelace": fa.values,
            "cost_500_lovelace": fb.values,
            "cost_cut_lovelace": (fa - fb).values,
            "delegators_445": da.values,
            "delegators_500": db.values,
            "delta_delegators": (db - da).values,
            "stake_445_lovelace": sa.values,
            "stake_500_lovelace": sb.values,
            "delta_stake_ada": ((sb - sa) / 1e6).values,
        }
    ).set_index("pool_id")
    df = df[cut]
    df["cost_cut_ada"] = df["cost_cut_lovelace"] / 1e6
    # Efficiency in delegators per 1 ADA fixed-cost cut (natural unit for these cuts)
    df["eff_delegators_per_ada_cut"] = df["delta_delegators"] / df["cost_cut_ada"].replace(0, np.nan)
    df = df.sort_values("eff_delegators_per_ada_cut", ascending=False)
    df.to_csv(OUT_CSV)

    cuts = sorted(df["cost_cut_ada"].dropna().unique())
    labels = [f"{int(c):,}" for c in cuts]
    x = np.arange(len(cuts))
    gain_counts = [int(((df["cost_cut_ada"] == c) & (df["delta_delegators"] > 0)).sum()) for c in cuts]
    lose_counts = [int(((df["cost_cut_ada"] == c) & (df["delta_delegators"] < 0)).sum()) for c in cuts]
    flat_counts = [int(((df["cost_cut_ada"] == c) & (df["delta_delegators"] == 0)).sum()) for c in cuts]
    median_delta = [
        float(df.loc[df["cost_cut_ada"] == c, "delta_delegators"].median()) if (df["cost_cut_ada"] == c).any() else np.nan
        for c in cuts
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), constrained_layout=True)

    ax = axes[0]
    w = 0.25
    ax.bar(x - w, gain_counts, width=w, color="#2f6f4e", label="gain")
    ax.bar(x, lose_counts, width=w, color="#b23a3a", label="lose")
    ax.bar(x + w, flat_counts, width=w, color="#6b7280", label="flat")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_xlabel("Fixed-cost cut (ADA)", fontsize=11)
    ax.set_ylabel("Pools", fontsize=11)
    ax.set_title("Pool counts by cut size", fontsize=11)
    ax.legend(frameon=False, fontsize=9)

    ax = axes[1]
    ax.scatter(
        df["cost_cut_ada"],
        df["delta_delegators"],
        s=18,
        alpha=0.65,
        color="#2f5d85",
        edgecolors="none",
    )
    ax.plot(cuts, median_delta, color="#e76f51", marker="o", linewidth=2.0, label="median Δ delegators")
    ax.axhline(0.0, color="0.4", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Fixed-cost cut (ADA)", fontsize=11)
    ax.set_ylabel("Δ delegators (500 - 445)", fontsize=11)
    ax.set_title("Delegator change by cut size", fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(alpha=0.25)

    fig.suptitle(
        "Delegator response to fixed-cost cuts (445→500, Active)\n"
        "Efficiency = Δdelegators / ADA cut (see CSV)",
        fontsize=11,
    )
    fig.savefig(OUT_PNG, dpi=160)

    q = df["eff_delegators_per_ada_cut"].quantile([0.1, 0.5, 0.9]).to_dict()
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_CSV}")
    print(
        "Efficiency quantiles (delegators per ADA cut):",
        {k: float(v) for k, v in q.items()},
    )
    print("n pools with cut:", len(df))


if __name__ == "__main__":
    main()
