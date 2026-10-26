"""Shared epoch-644 Active-pool calculator for C.1 frozen-σ scoreboard."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent
POOLS_CSV = ROOT / "staking_pools_full_epoch_644_merged.csv"
FLAGS_CSV = ROOT / "inactive_pool_flags_koios_epoch_644_last15.csv"
PARAMS_JSON = ROOT / "f_reward_params_epoch_644.json"
REDEP_CSV = ROOT / "k" / "redelegation_rank_k1000_cap40M_excess_epoch_644.csv"

FONT_SIZE = 12
EPOCHS_PER_MONTH = 6.0
EPOCHS_PER_YEAR = 73.0
ADA_USD = 0.15
USD_MONTH = 667.0
C_STAR = USD_MONTH / EPOCHS_PER_MONTH / ADA_USD

K0, K1 = 500, 1000
A0_0, A0_1 = 0.3, 0.6
C_FORCE = 75.0
RHO_0, RHO_1 = 0.003, 0.0042
STAKE_GE5M = 5.0e6
BIN_WIDTH_M = 5.0
BIN_MAX_M = 80.0
PRICES = (0.10, 0.15, 0.25, 0.30, 0.50)
OPEX = (
    {"usd_month": 39.0 * 0.25 * EPOCHS_PER_MONTH, "label": "58.5 USD/mo", "short": "58.5"},
    {"usd_month": 171.0 * 0.25 * EPOCHS_PER_MONTH, "label": "256.5 USD/mo", "short": "256.5"},
    {"usd_month": 667.0, "label": "667 USD/mo", "short": "667"},
    {"usd_month": 986.0 * 0.25 * EPOCHS_PER_MONTH, "label": "1479 USD/mo", "short": "1479"},
)
R_ORDER = ("r_lt_05", "r_05_1", "r_1_2", "r_ge_2")
R_LABELS = (
    r"$r<0.5$",
    r"$0.5\leq r<1$",
    r"$1\leq r<2$",
    r"$r\geq 2$",
)
R_COLORS = ("#a50f15", "#fc9272", "#b7e4c7", "#2a9d8f")
NORHO_SHOCKS = ("k", "a0", "c")


def load_active_pools() -> pd.DataFrame:
    df = pd.read_csv(POOLS_CSV)
    flags = pd.read_csv(FLAGS_CSV)
    df = df.merge(flags[["pool_id", "in_union"]], on="pool_id", how="left")
    if df["in_union"].isna().any():
        raise RuntimeError("Missing inactivity flags for some pools")
    return df.loc[df["in_union"] == 0].copy()


def gross_pool_reward(sigma, declared_pledge, *, z0, r_over_t, a0):
    sigma_tilde = np.minimum(np.maximum(sigma, 0.0), z0)
    pledge_tilde = np.minimum(np.maximum(declared_pledge, 0.0), z0)
    pledge_tilde = np.minimum(pledge_tilde, sigma_tilde)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(f, fixed_cost, margin, active_pledge, sigma):
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


def member_apr(sigma, f, cost, margin):
    pot = (1.0 - margin) * np.maximum(f - cost, 0.0)
    return EPOCHS_PER_YEAR * np.divide(
        pot, sigma, out=np.zeros_like(pot), where=sigma > 0
    )


def nakamoto_coefficient(stakes, threshold: float = 0.5) -> int:
    s = np.sort(np.asarray(stakes, dtype=float))
    s = s[s > 0][::-1]
    if s.size == 0:
        return 0
    c = np.cumsum(s)
    return int(np.searchsorted(c, threshold * c[-1], side="left") + 1)


def c_star(usd_month: float, price: float) -> float:
    return usd_month / EPOCHS_PER_MONTH / price


def stake_bin_labels() -> tuple[np.ndarray, list[str]]:
    edges = np.arange(0.0, BIN_MAX_M + BIN_WIDTH_M, BIN_WIDTH_M)
    labels = [f"{int(lo)}–{int(hi)}" for lo, hi in zip(edges[:-1], edges[1:])]
    labels.append(f"≥{int(BIN_MAX_M)}")
    return edges, labels


def assign_stake_bins(stake_m: np.ndarray, edges: np.ndarray) -> np.ndarray:
    idx = np.digitize(stake_m, edges, right=False) - 1
    idx = np.clip(idx, 0, len(edges) - 1)
    return np.where(stake_m >= BIN_MAX_M, len(edges) - 1, idx)


def classify_r(ratio) -> str:
    if not np.isfinite(ratio) or ratio < 0.5:
        return "r_lt_05"
    if ratio < 1.0:
        return "r_05_1"
    if ratio < 2.0:
        return "r_1_2"
    return "r_ge_2"


def nakamoto_of_total(subset_stakes, total: float, threshold: float = 0.5):
    s = np.asarray(subset_stakes, dtype=float)
    s = s[s > 0]
    if s.size == 0 or float(s.sum()) < threshold * total:
        return np.nan
    order = np.argsort(s)[::-1]
    c = np.cumsum(s[order])
    return int(np.searchsorted(c, threshold * total, side="left") + 1)


def herfindahl(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[x > 0]
    if x.size == 0:
        return float("nan")
    s = x / x.sum()
    return float((s**2).sum())


SCALAR_SHOCKS = {
    "k": dict(x0=float(K0), x1=float(K1)),
    "a0": dict(x0=float(A0_0), x1=float(A0_1)),
    "rho": dict(x0=float(RHO_0), x1=float(RHO_1)),
}

OBJECTIVES = (
    ("n_r_ge1", r"$n$ with $r\geq 1$", "viability"),
    ("network_apr", "network APR", "apr"),
    ("median_apr", "median APR", "apr"),
    ("nakamoto_n", r"$N$ (stake)", "decentralization"),
    ("nakamoto_f", r"$N(f)$", "decentralization"),
    ("sum_f", r"$\sum f$", "pie"),
)
OBJECTIVES_NORHO = OBJECTIVES + (
    ("nakamoto_sigma_rge1", r"$N(\sigma\mid r\geq 1)$", "decentralization"),
)


def load_snapshot() -> dict:
    params = json.loads(PARAMS_JSON.read_text())
    r0 = float(params["R_ada"])
    t = float(params["T_supply_ada"])
    df = load_active_pools()
    sigma = pd.to_numeric(
        df["epochs.0.data.epoch_stake"].fillna(df["active_stake"]), errors="coerce"
    ) / 1e6
    declared = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active = pd.to_numeric(df["live_pledge"].fillna(df["pledged"]), errors="coerce") / 1e6
    cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")
    complete = (
        sigma.notna()
        & declared.notna()
        & active.notna()
        & cost.notna()
        & margin.notna()
        & df["pool_id"].notna()
    )
    snap = {
        "pool_id": df.loc[complete, "pool_id"].to_numpy(),
        "R0": r0,
        "R1": r0 * (RHO_1 / RHO_0),
        "T": t,
        "sigma": sigma[complete].to_numpy(dtype=float),
        "declared": declared[complete].to_numpy(dtype=float),
        "active": active[complete].to_numpy(dtype=float),
        "cost": cost[complete].to_numpy(dtype=float),
        "margin": margin[complete].to_numpy(dtype=float),
        "c_star": float(C_STAR),
    }
    redep = pd.read_csv(REDEP_CSV)
    aligned = pd.DataFrame({"pool_id": snap["pool_id"]}).merge(
        redep[["pool_id", "sigma_after_ada"]], on="pool_id", how="left"
    )
    if aligned["sigma_after_ada"].isna().any():
        raise RuntimeError("Redelegation file missing Active pool_ids")
    snap["sigma_after"] = aligned["sigma_after_ada"].to_numpy(dtype=float)
    return snap


def f_pi(snap, *, k: int, a0: float, cost, r_ada: float, sigma=None):
    if sigma is None:
        sigma = snap["sigma"]
    z0 = snap["T"] / k
    pledge_met = (snap["active"] >= snap["declared"]) & (sigma > 0)
    f = gross_pool_reward(
        sigma, snap["declared"], z0=z0, r_over_t=r_ada / snap["T"], a0=a0
    )
    f = np.where(pledge_met, np.maximum(f, 0.0), 0.0)
    pi = operator_reward(f, cost, snap["margin"], snap["active"], sigma)
    return f, pi, pledge_met


def summarize(snap, *, key, label, k, a0, cost, r_ada, sigma=None, f0=None, pi0=None) -> dict:
    frozen = sigma is None
    if sigma is None:
        sigma = snap["sigma"]
    f, pi, met = f_pi(snap, k=k, a0=a0, cost=cost, r_ada=r_ada, sigma=sigma)
    r = np.divide(pi, snap["c_star"], out=np.full_like(pi, np.nan), where=snap["c_star"] > 0)
    r_m = r[met]
    s_m = sigma[met]
    apr = member_apr(sigma, f, cost, snap["margin"])
    elig = met & (f > cost)
    apr_e = apr[elig]
    if elig.any():
        median_apr = float(np.median(apr_e))
        mean_apr = float(np.mean(apr_e))
        network_apr = float(np.average(apr_e, weights=sigma[elig]))
    else:
        median_apr = mean_apr = network_apr = float("nan")
    orig = (snap["active"] >= snap["declared"]) & (snap["sigma"] > 0)
    if f0 is None:
        df_sum = dpi = ddel = 0.0
    else:
        df_sum = float((f - f0)[orig].sum())
        dpi = float((pi - pi0)[orig].sum())
        ddel = df_sum - dpi
    n_sigma = int((sigma > 0).sum())
    return {
        "key": key,
        "label": label,
        "k": k,
        "a0": a0,
        "R": r_ada,
        "frozen_sigma": frozen,
        "n_sigma_pos": n_sigma,
        "n_pledge_met": int(met.sum()),
        "n_r_ge1": int((r_m >= 1.0).sum()),
        "n_r_ge2": int((r_m >= 2.0).sum()),
        "median_r": float(np.median(r_m)) if r_m.size else float("nan"),
        "stake_r_ge1": float(s_m[r_m >= 1.0].sum()),
        "stake_total": float(s_m.sum()),
        "n_f_gt_c": int(elig.sum()),
        "median_apr": median_apr,
        "mean_apr": mean_apr,
        "network_apr": network_apr,
        "nakamoto_n": nakamoto_coefficient(sigma),
        "nakamoto_f": nakamoto_coefficient(f),
        "nakamoto_pi": nakamoto_coefficient(pi),
        "hhi_f": herfindahl(f),
        "nakamoto_sigma_rge1": nakamoto_coefficient(sigma[met & (r >= 1.0)]),
        "nakamoto_sigma_ge5m": nakamoto_coefficient(sigma[sigma >= STAKE_GE5M]),
        "nakamoto_f_ge5m": nakamoto_coefficient(f[sigma >= STAKE_GE5M]),
        "nakamoto_f_rge1": nakamoto_coefficient(f[met & (r >= 1.0)]),
        "stake_share_rge1": (
            float(sigma[met & (r >= 1.0)].sum() / sigma[met].sum())
            if met.any() and float(sigma[met].sum()) > 0
            else float("nan")
        ),
        "nakamoto_total_via_rge1": nakamoto_of_total(
            sigma[met & (r >= 1.0)], float(sigma[met].sum())
        ),
        "sum_f": float(f[met].sum()),
        "sum_pi": float(pi[met].sum()),
        "sum_delta_f": df_sum,
        "sum_delta_pi": dpi,
        "sum_delta_delegator": ddel,
        "n_oversaturated": int((sigma > snap["T"] / k).sum()),
        "E_k": float(np.maximum(sigma - snap["T"] / k, 0.0).sum()),
        "c_star": snap["c_star"],
    }


def scenario_specs(snap: dict) -> list[dict]:
    c0 = snap["cost"]
    c75 = np.full_like(c0, C_FORCE)
    return [
        dict(key="base", label=r"Baseline", k=K0, a0=A0_0, cost=c0, r_ada=snap["R0"]),
        dict(key="k", label=r"$k=1000$", k=K1, a0=A0_0, cost=c0, r_ada=snap["R0"]),
        dict(key="a0", label=r"$a_0=0.6$", k=K0, a0=A0_1, cost=c0, r_ada=snap["R0"]),
        dict(key="c", label=r"$c_i=75$", k=K0, a0=A0_0, cost=c75, r_ada=snap["R0"]),
        dict(key="rho", label=r"$\rho=0.0042$", k=K0, a0=A0_0, cost=c0, r_ada=snap["R1"]),
        dict(key="k_c", label=r"$k=1000$, $c_i=75$", k=K1, a0=A0_0, cost=c75, r_ada=snap["R0"]),
        dict(key="k_a0", label=r"$k=1000$, $a_0=0.6$", k=K1, a0=A0_1, cost=c0, r_ada=snap["R0"]),
        dict(key="a0_c", label=r"$a_0=0.6$, $c_i=75$", k=K0, a0=A0_1, cost=c75, r_ada=snap["R0"]),
        dict(
            key="k_after",
            label=r"$k=1000$ after $D_i$",
            k=K1,
            a0=A0_0,
            cost=c0,
            r_ada=snap["R0"],
            sigma=snap["sigma_after"],
        ),
    ]


def compute_scoreboard(snap: dict) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    f0, pi0, _ = f_pi(
        snap, k=K0, a0=A0_0, cost=snap["cost"], r_ada=snap["R0"]
    )
    rows = []
    for spec in scenario_specs(snap):
        sigma = spec.get("sigma")
        kwargs = {k: v for k, v in spec.items() if k != "sigma"}
        rows.append(summarize(snap, f0=f0, pi0=pi0, sigma=sigma, **kwargs))
    return pd.DataFrame(rows), f0, pi0


def pct_change(y1, y0) -> float:
    y0 = float(y0)
    y1 = float(y1)
    if y0 == 0.0:
        return float("nan")
    return (y1 - y0) / y0


def elasticity(y1, y0, x1, x0) -> float:
    dx = pct_change(x1, x0)
    dy = pct_change(y1, y0)
    if np.isnan(dx) or np.isnan(dy) or dx == 0.0:
        return float("nan")
    return dy / dx


def relative_impacts(board: pd.DataFrame) -> pd.DataFrame:
    base = board.loc[board["key"] == "base"].iloc[0]
    rows = []
    for key, spec in SCALAR_SHOCKS.items():
        row = board.loc[board["key"] == key].iloc[0]
        dx = pct_change(spec["x1"], spec["x0"])
        rec = {
            "key": key,
            "label": row["label"],
            "x0": spec["x0"],
            "x1": spec["x1"],
            "dx_over_x": dx,
        }
        for col, _, _ in OBJECTIVES_NORHO:
            rec[f"d_{col}"] = float(row[col] - base[col])
            rec[f"pct_{col}"] = pct_change(row[col], base[col])
            rec[f"e_{col}"] = elasticity(row[col], base[col], spec["x1"], spec["x0"])
        rows.append(rec)
    return pd.DataFrame(rows)


def spec_by_key(snap: dict, key: str) -> dict:
    for spec in scenario_specs(snap):
        if spec["key"] == key:
            return spec
    raise KeyError(key)


def outcomes_from_spec(snap: dict, spec: dict, cstar: float | None = None) -> dict:
    sigma = spec.get("sigma")
    if sigma is None:
        sigma = snap["sigma"]
    kwargs = {k: v for k, v in spec.items() if k not in ("sigma", "key", "label")}
    f, pi, met = f_pi(snap, sigma=sigma, **kwargs)
    if cstar is None:
        cstar = snap["c_star"]
    r = np.divide(pi, cstar, out=np.full_like(pi, np.nan), where=cstar > 0)
    return {"f": f, "pi": pi, "met": met, "r": r, "sigma": sigma}
