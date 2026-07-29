#!/usr/bin/env python3
"""Update Parameter-Landscape tables from a dated mainnet snapshot markdown file.

Usage:
  python3 update_snapshot_tables.py
  python3 update_snapshot_tables.py --snapshot mainnet-parameter-snapshot-2026-07-29.md
  python3 update_snapshot_tables.py --dry-run
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import re
from typing import Dict


@dataclass
class SnapshotValues:
    snapshot_file: str
    epoch: int
    total_supply_lovelace: int
    active_stake_lovelace: int
    reserves_lovelace: int
    epoch_fees_lovelace: int
    k: int
    a0: Decimal
    c_min_lovelace: int
    tau: Decimal
    rho: Decimal


def parse_snapshot(path: Path) -> SnapshotValues:
    text = path.read_text(encoding="utf-8")

    def must(pattern: str) -> str:
        m = re.search(pattern, text, flags=re.MULTILINE)
        if not m:
            raise ValueError(f"Could not find pattern: {pattern}")
        return m.group(1)

    return SnapshotValues(
        snapshot_file=path.name,
        epoch=int(must(r"- Source epoch: (\d+)")),
        total_supply_lovelace=int(must(r"- total_supply \(T\): (\d+)")),
        active_stake_lovelace=int(must(r"- active_stake \(S\): (\d+)")),
        reserves_lovelace=int(must(r"- reserves: (\d+)")),
        epoch_fees_lovelace=int(must(r"- epoch_fees \(epoch \d+\): (\d+)")),
        k=int(must(r"- optimal_pool_count \(k\): (\d+)")),
        a0=Decimal(must(r"- influence \(a0\): ([0-9.]+)")),
        c_min_lovelace=int(must(r"- min_pool_cost: (\d+)")),
        tau=Decimal(must(r"- treasury_growth_rate \(tau\): ([0-9.]+)")),
        rho=Decimal(must(r"- monetary_expand_rate \(rho\): ([0-9.]+)")),
    )


def quant2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt_with_commas_2(x: Decimal) -> str:
    return f"{quant2(x):,.2f}"


def percent(x: Decimal) -> str:
    return f"{quant2(x * Decimal(100)):.2f}%"


def update_first_line_start(text: str, startswith: str, new_line: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(startswith):
            lines[i] = new_line
            return "\n".join(lines) + "\n"
    raise ValueError(f"Line starting with not found: {startswith}")


def update_parameter_landscape(root: Path, values: SnapshotValues) -> None:
    path = root / "Parameter-Landscape.md"
    text = path.read_text(encoding="utf-8")

    t_ada = Decimal(values.total_supply_lovelace) / Decimal(1_000_000)
    s_ada = Decimal(values.active_stake_lovelace) / Decimal(1_000_000)
    s_over_t = Decimal(values.active_stake_lovelace) / Decimal(values.total_supply_lovelace)

    r_lovelace = (Decimal(1) - values.tau) * (
        Decimal(values.epoch_fees_lovelace) + values.rho * Decimal(values.reserves_lovelace)
    )
    r_ada = r_lovelace / Decimal(1_000_000)

    c_min_ada = Decimal(values.c_min_lovelace) / Decimal(1_000_000)
    z0 = Decimal(1) / Decimal(values.k)

    r_m = quant2(r_ada / Decimal(1_000_000))
    t_b = quant2(t_ada / Decimal(1_000_000_000))
    s_b = quant2(s_ada / Decimal(1_000_000_000))

    source_line = (
        f"Snapshot source: [{values.snapshot_file}]({values.snapshot_file}) "
        f"(mainnet, epoch {values.epoch})."
    )

    # Update source line if present.
    text = re.sub(
        r"^Snapshot source: \[mainnet-parameter-snapshot-[^\]]+\]\([^\)]+\) \(mainnet, epoch \d+\)\.$",
        source_line,
        text,
        flags=re.MULTILINE,
    )

    replacements: Dict[str, str] = {
        "| $R$ | Reward pot |": (
            "| $R$ | Reward pot | "
            f"{r_m}M ADA | "
            "Total rewards available in an epoch (using the simplified expression in this repository). | "
            "Scales gross rewards to pools, operators, and delegators. |"
        ),
        "| $T$ | Total ADA supply |": (
            "| $T$ | Total ADA supply | "
            f"{t_b}B ADA | "
            "Measures all ADA in circulation + unclaimed rewards + deposits + fees + treasury. | "
            "Reference ADA base used to normalize stake variables. |"
        ),
        "| $S$ | Active stake |": (
            "| $S$ | Active stake | "
            f"{s_b}B ADA | "
            "Total ADA actively delegated or pledged. | "
            "Measures staking participation. |"
        ),
        "| $S/T$ | Staking participation rate |": (
            "| $S/T$ | Staking participation rate | "
            f"{percent(s_over_t)} | "
            "Share of total supply participating in staking. | "
            "Captures effectivness of the incentive to stake rather than remain liquid. |"
        ),
        "| $k$ | Target number of stake pools |": (
            "| $k$ | Target number of stake pools | "
            f"{values.k} | "
            "Sets the saturation threshold $z_0$. <br> Determines how many pools are expected to attract delegation. <br> "
            "Affects the scale of pool rewards. <br> Decentralization-design parameter. | "
            "It does not impose a limit on the number of pools. Its role in the reward function is to induce an equilibrium with nearly k economically relevant pools. |"
        ),
        "| $z_0 = 1/k$ | Saturation threshold.": (
            "| $z_0 = 1/k$ | Saturation threshold. Maximum reward-bearing stake per pool, as a fraction of $T$. | "
            f"1/{values.k} ({z0.normalize()}) | Caps the stake that can earn rewards in one pool. | --- |"
        ),
        "| $a_0$ | Pledge influence.": (
            "| $a_0$ | Pledge influence. Strength of pledge in the reward formula. | "
            f"{values.a0} | Higher $a_0$ favors high-pledge pools. Desincentivize Sybil behavior. | --- |"
        ),
        "| $c_{min}$ | Minimum fixed cost": (
            "| $c_{min}$ | Minimum fixed cost (`minPoolCost`). Minimum fixed fee a pool operator can charge. | "
            f"{int(c_min_ada)} ADA | Affects small-pool viability and delegator returns. | --- |"
        ),
        "| $\\tau$ | Treasury share.": (
            "| $\\tau$ | Treasury share. Fraction of rewards allocated to the treasury. | "
            f"{percent(values.tau)} | Trades off staking rewards against ecosystem funding. | --- |"
        ),
        "| $\\rho$ | Reserve decay rate.": (
            "| $\\rho$ | Reserve decay rate. Rate at which reserves are deployed into rewards. | "
            f"{percent(values.rho)}  | Main contributor to operators and delegators rewards. Affects long-run reward sustainability. | --- |"
        ),
    }

    for start, new_line in replacements.items():
        text = update_first_line_start(text, start, new_line)

    path.write_text(text, encoding="utf-8")


def find_latest_snapshot(root: Path) -> Path:
    candidates = sorted(root.glob("mainnet-parameter-snapshot-*.md"))
    if not candidates:
        raise FileNotFoundError("No snapshot files found: mainnet-parameter-snapshot-*.md")
    return candidates[-1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Update Parameter-Landscape tables from snapshot markdown.")
    parser.add_argument("--snapshot", help="Snapshot filename in Parameters-Landscape folder.")
    parser.add_argument("--dry-run", action="store_true", help="Validate parsing and print values only.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    snapshot = root / args.snapshot if args.snapshot else find_latest_snapshot(root)

    values = parse_snapshot(snapshot)

    if args.dry_run:
        print(f"Using snapshot: {snapshot.name}")
        print(f"Epoch: {values.epoch}")
        print(f"k={values.k}, a0={values.a0}, c_min_lovelace={values.c_min_lovelace}")
        print(f"rho={values.rho}, tau={values.tau}")
        return

    update_parameter_landscape(root, values)
    print(f"Updated Parameter-Landscape tables using {snapshot.name}")


if __name__ == "__main__":
    main()
