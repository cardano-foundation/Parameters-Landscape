#!/usr/bin/env python3
"""C.2 tables: without-ρ ranking, coarse bins, conditional Nakamoto.

Writes: conditional_nakamoto_c2_epoch_644.md
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from comparison_common import (
    STAKE_GE5M,
    compute_scoreboard,
    load_snapshot,
    outcomes_from_spec,
    spec_by_key,
)

DIR = Path(__file__).resolve().parent
OUT_MD = DIR / "conditional_nakamoto_c2_epoch_644.md"

KEYS = ("base", "k", "a0", "c", "rho")


def fmt_n(x) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"${int(x)}$"


def coarse_counts(sigma, r, met):
    stake_m = sigma / 1e6
    bands = (
        ("$<10$M", stake_m < 10),
        ("$10$–$40$M", (stake_m >= 10) & (stake_m < 40)),
        (r"$\geq 40$M", stake_m >= 40),
    )
    out = []
    for lab, m in bands:
        n = int(m.sum())
        g = int((m & met & (r >= 1.0)).sum())
        out.append((lab, n, g))
    return out


def main() -> None:
    snap = load_snapshot()
    board, _, _ = compute_scoreboard(snap)
    by = {row["key"]: row for _, row in board.iterrows()}
    sigma = snap["sigma"]

    lines = [
        "# C.2 without $\\rho$, bins, and conditional Nakamoto — epoch 644\n\n",
        "## Conditional Nakamoto at paper $C^*=741.1$\n\n",
        "| Shock | $n$ with $r\\ge 1$ | $N$ (stake) | $N(\\sigma\\mid r\\ge 1)$ | "
        "stake share $r\\ge 1$ | $N$ of total via $r\\ge 1$ | "
        r"$N(\sigma\mid\sigma\ge 5\mathrm{M})$ | $N(f)$ | $N(f\mid\sigma\ge 5\mathrm{M})$ |"
        "\n",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|\n",
    ]
    for key in KEYS:
        row = by[key]
        ntot = row["nakamoto_total_via_rge1"]
        lines.append(
            "| {lab} | {n} | {ns} | {nr} | {sh} | {nt} | {n5} | {nf} | {nf5} |\n".format(
                lab=row["label"],
                n=f"{int(row['n_r_ge1']):,}",
                ns=f"{int(row['nakamoto_n'])}",
                nr=f"{int(row['nakamoto_sigma_rge1'])}",
                sh=f"{100.0 * row['stake_share_rge1']:.1f}\\%",
                nt="—" if not np.isfinite(ntot) else f"{int(ntot)}",
                n5=f"{int(row['nakamoto_sigma_ge5m'])}",
                nf=f"{int(row['nakamoto_f'])}",
                nf5=f"{int(row['nakamoto_f_ge5m'])}",
            )
        )

    lines += ["\n## $n$ with $r\\ge 1$ by coarse stake band\n\n"]
    header = "| Band | $n$ | Baseline | $k=1000$ | $a_0=0.6$ | $c_i=75$ |\n|:---|---:|---:|---:|---:|---:|\n"
    lines.append(header)
    base_out = outcomes_from_spec(snap, spec_by_key(snap, "base"))
    bands0 = coarse_counts(sigma, base_out["r"], base_out["met"])
    others = {
        key: coarse_counts(
            sigma,
            outcomes_from_spec(snap, spec_by_key(snap, key))["r"],
            outcomes_from_spec(snap, spec_by_key(snap, key))["met"],
        )
        for key in ("k", "a0", "c")
    }
    for i, (lab, n, g0) in enumerate(bands0):
        gk = others["k"][i][2]
        ga = others["a0"][i][2]
        gc = others["c"][i][2]
        lines.append(
            f"| {lab} | {n} | {g0} | {gk} ({gk-g0:+d}) | {ga} ({ga-g0:+d}) | {gc} ({gc-g0:+d}) |\n"
        )

    lines += [
        "\n",
        f"Pools with $\\sigma\\ge 5$M: ${int((sigma >= STAKE_GE5M).sum())}$. ",
        "At frozen $\\sigma$, $N(\\sigma\\mid\\sigma\\ge 5\\mathrm{M})$ does not move.\n",
    ]
    OUT_MD.write_text("".join(lines))
    print(OUT_MD.read_text())
    print(f"Saved: {OUT_MD}")


if __name__ == "__main__":
    main()
