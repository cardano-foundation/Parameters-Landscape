"""Shared data loading and computation for rho=0.003 vs rho=0.0042 analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent
POOLS_CSV = DIR / "staking_pools_full_epoch_644.csv"
PARAMS_JSON = DIR / "f_reward_params_epoch_644.json"

FONT_SIZE = 12
MONTHLY_OPEX_USD = 667.0
EPOCHS_PER_MONTH = 6.0
ADA_USD = 0.15
C_STAR_ADA = MONTHLY_OPEX_USD / EPOCHS_PER_MONTH / ADA_USD

RHO_BASE = 0.003
RHO_NEW = 0.0042
TAU = 0.2

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


def gross_pool_reward(sigma, declared_pledge, *, z0, r_over_t, a0):
    sigma_tilde = np.minimum(sigma, z0)
    pledge_tilde = np.minimum(declared_pledge, z0)
    inner = sigma_tilde - pledge_tilde * (z0 - sigma_tilde) / z0
    return (r_over_t / (1.0 + a0)) * (
        sigma_tilde + a0 * pledge_tilde * inner / z0
    )


def operator_reward(f, fixed_cost, margin, active_pledge, sigma):
    pledge_share = np.clip(
        np.divide(active_pledge, sigma, out=np.zeros_like(active_pledge), where=sigma > 0),
        0.0, 1.0,
    )
    operator_share = margin + (1.0 - margin) * pledge_share
    profitable = fixed_cost + (f - fixed_cost) * operator_share
    return np.where(f > fixed_cost, profitable, f)


def desirability(f, fixed_cost, margin, sigma):
    """Per-ADA member reward: D = (1 - m) * max(f - c, 0) / sigma."""
    return np.where(
        sigma > 0,
        (1.0 - margin) * np.maximum(f - fixed_cost, 0.0) / sigma,
        0.0,
    )


def classify(ratio):
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


def load_and_compute():
    """Load data and compute both scenarios. Returns a dict with all arrays."""
    params = json.loads(PARAMS_JSON.read_text())
    a0 = float(params["a0"])
    reserves = float(params["reserves_ada"])
    T = float(params["T_supply_ada"])
    z0 = float(params["z0_ada"])

    R_base = (1 - TAU) * RHO_BASE * reserves
    R_new = (1 - TAU) * RHO_NEW * reserves

    df = pd.read_csv(POOLS_CSV)
    sigma = pd.to_numeric(df["epochs.0.data.epoch_stake"], errors="coerce") / 1e6
    declared_pledge = pd.to_numeric(df["pool_update.active.pledge"], errors="coerce") / 1e6
    active_pledge = pd.to_numeric(df["pledged"], errors="coerce") / 1e6
    fixed_cost = pd.to_numeric(df["pool_update.active.fixed_cost"], errors="coerce") / 1e6
    margin = pd.to_numeric(df["pool_update.active.margin"], errors="coerce")

    complete = sigma.notna() & declared_pledge.notna() & active_pledge.notna() & fixed_cost.notna() & margin.notna()
    sigma_a = sigma[complete].to_numpy(dtype=float)
    declared_a = declared_pledge[complete].to_numpy(dtype=float)
    active_a = active_pledge[complete].to_numpy(dtype=float)
    cost_a = fixed_cost[complete].to_numpy(dtype=float)
    margin_a = margin[complete].to_numpy(dtype=float)
    pledge_met = (active_a >= declared_a) & (sigma_a > 0)

    f_base = np.where(
        pledge_met,
        np.maximum(gross_pool_reward(sigma_a, declared_a, z0=z0, r_over_t=R_base / T, a0=a0), 0.0),
        0.0,
    )
    pi_base = operator_reward(f_base, cost_a, margin_a, active_a, sigma_a)
    ratio_base = pi_base / C_STAR_ADA
    cat_base = np.array([classify(v) if m else "pledge_not_met" for v, m in zip(ratio_base, pledge_met)])

    f_new = np.where(
        pledge_met,
        np.maximum(gross_pool_reward(sigma_a, declared_a, z0=z0, r_over_t=R_new / T, a0=a0), 0.0),
        0.0,
    )
    pi_new = operator_reward(f_new, cost_a, margin_a, active_a, sigma_a)
    ratio_new = pi_new / C_STAR_ADA
    cat_new = np.array([classify(v) if m else "pledge_not_met" for v, m in zip(ratio_new, pledge_met)])

    d_base = desirability(f_base, cost_a, margin_a, sigma_a)
    d_new = desirability(f_new, cost_a, margin_a, sigma_a)

    return {
        "df": df, "complete": complete, "pledge_met": pledge_met,
        "sigma_a": sigma_a, "declared_a": declared_a, "active_a": active_a,
        "cost_a": cost_a, "margin_a": margin_a,
        "f_base": f_base, "f_new": f_new,
        "pi_base": pi_base, "pi_new": pi_new,
        "ratio_base": ratio_base, "ratio_new": ratio_new,
        "cat_base": cat_base, "cat_new": cat_new,
        "d_base": d_base, "d_new": d_new,
        "R_base": R_base, "R_new": R_new,
    }
