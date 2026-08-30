"""B3 - beneficiary intelligence.

Payee-level network aggregates are drawn from the payee's *latent* activity
parameters rather than counted off the simulated panel. This is a deliberate
modelling choice, recorded in docs/DATA_CARD.md: the 25,000 simulated payers
are a sample of each payee's true inbound payer base, so counting in-sample
in-degree would understate a utility biller by three orders of magnitude while
leaving a mule roughly correct. The aggregates are re-drawn per payee-month,
so they carry realistic within-account variability rather than being a fixed
function of role.

Pair-level features (relationship age, prior count, reciprocity) *are* counted
off the panel, and ``payee_report_count`` is evaluated strictly as of the
transaction day: report timestamps are stored and searched, never summed
ahead of time.

This is the group the experiment must beat. It is built to be strong.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..entities import MULE_ROLES, PAYEE_ROLES
from ..population import Population
from . import B3_COLS

#: Mean inbound ticket size by role, used to turn a fan-in count into an
#: inflow value. Independent of the fraud label.
ROLE_TICKET: dict[str, float] = {
    "individual_friend": 1200.0, "family_member": 5400.0,
    "landlord_individual": 14000.0, "property_manager": 15500.0,
    "education_institution": 26000.0, "utility_biller": 1600.0,
    "merchant_small": 950.0, "merchant_large": 1400.0, "employer": 4200.0,
    "settlement_agent": 3500.0, "gig_worker": 900.0,
    "chit_fund_collector": 4500.0,
    "mule_fresh": 42000.0, "mule_aged": 38000.0, "scam_collection": 30000.0,
}

#: Expected number of distinct onward payees in 30 days. Cash-out accounts
#: forward to a handful of destinations; merchants pay many suppliers.
ROLE_OUTFLOW: dict[str, float] = {
    "individual_friend": 4.0, "family_member": 3.0, "landlord_individual": 5.0,
    "property_manager": 22.0, "education_institution": 40.0,
    "utility_biller": 30.0, "merchant_small": 14.0, "merchant_large": 70.0,
    "employer": 60.0, "settlement_agent": 45.0, "gig_worker": 6.0,
    "chit_fund_collector": 4.0, "mule_fresh": 3.5, "mule_aged": 4.5,
    "scam_collection": 5.0,
}

#: Probability the beneficiary has ever paid this payer back.
ROLE_RECIPROCITY: dict[str, float] = {
    "individual_friend": 0.55, "family_member": 0.45,
    "landlord_individual": 0.06, "property_manager": 0.04,
    "education_institution": 0.02, "utility_biller": 0.01,
    "merchant_small": 0.05, "merchant_large": 0.03, "employer": 0.35,
    "settlement_agent": 0.04, "gig_worker": 0.20,
    "chit_fund_collector": 0.30,
    "mule_fresh": 0.01, "mule_aged": 0.01, "scam_collection": 0.01,
}

#: Share of a month's inflow still held at month end.
#:
#: Generated from its own per-role process rather than as ``1 - fanout``.
#: The two are correlated across roles, as they would be in production, but a
#: purely algebraic link would have put the same evidence into B3 twice and
#: overstated how much beneficiary intelligence a real system actually has.
ROLE_RETENTION: dict[str, float] = {
    "individual_friend": 0.72, "family_member": 0.80,
    "landlord_individual": 0.70, "property_manager": 0.55,
    "education_institution": 0.62, "utility_biller": 0.58,
    "merchant_small": 0.45, "merchant_large": 0.50, "employer": 0.85,
    "settlement_agent": 0.12, "gig_worker": 0.22,
    "chit_fund_collector": 0.18,
    "mule_fresh": 0.06, "mule_aged": 0.10, "scam_collection": 0.08,
}


def payee_month_panel(pop: Population, months: int,
                      rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Draw network-observed aggregates for every (payee, month) cell."""
    n_p = len(pop.payees)
    role = pop.payee_role
    fan = np.array([p.fan_in_30d for p in pop.payees])
    fanout = np.array([p.fanout_ratio for p in pop.payees])
    period = np.array([p.periodicity for p in pop.payees])
    geo = np.array([p.geo_dispersion for p in pop.payees])
    ticket = np.array([ROLE_TICKET[r] for r in role])
    outflow = np.array([ROLE_OUTFLOW[r] for r in role])

    shape = (n_p, months)
    # month-to-month variability shrinks as periodicity rises
    wobble = np.exp(rng.normal(0.0, (0.85 * (1.0 - period))[:, None], shape))
    inflow_n = np.maximum(rng.poisson(np.maximum(fan[:, None] * wobble, 0.05)), 0)
    inflow_amt = inflow_n * ticket[:, None] * np.exp(rng.normal(0.0, 0.45, shape))

    fanout_obs = np.clip(fanout[:, None] + rng.normal(0.0, 0.07, shape), 0.0, 1.0)
    outflow_n = rng.poisson(np.maximum(outflow[:, None] * wobble ** 0.5, 0.05))

    # coefficient of variation of inflow value, computed across the payee's own
    # observed months up to and including the current one (expanding, no lookahead)
    cs = np.cumsum(inflow_amt, axis=1)
    cs2 = np.cumsum(inflow_amt ** 2, axis=1)
    k = np.arange(1, months + 1)[None, :]
    mean = cs / k
    var = np.maximum(cs2 / k - mean ** 2, 0.0)
    cv = np.sqrt(var) / np.maximum(mean, 1.0)

    period_obs = np.clip(period[:, None] + rng.normal(0.0, 0.09, shape), 0.0, 1.0)
    geo_obs = np.clip(geo[:, None] + rng.normal(0.0, 0.06, shape), 0.0, 1.0)
    ret_mu = np.array([ROLE_RETENTION[r] for r in role])
    retention = np.clip(
        ret_mu[:, None] + rng.normal(0.0, 0.16, shape)
        # a heavier-than-usual inflow month leaves more behind at month end
        + 0.06 * np.log(np.maximum(wobble, 1e-3)),
        0.0, 1.0)

    return {
        "inflow_n": inflow_n.astype(np.float32),
        "inflow_amt": inflow_amt.astype(np.float32),
        "fanout": fanout_obs.astype(np.float32),
        "outflow_n": outflow_n.astype(np.float32),
        "cv": cv.astype(np.float32),
        "period": period_obs.astype(np.float32),
        "geo": geo_obs.astype(np.float32),
        "retention": retention.astype(np.float32),
    }


def build(df: pd.DataFrame, pop: Population, cfg: dict,
          rng: np.random.Generator) -> pd.DataFrame:
    months = cfg["population"]["months"]
    panel = payee_month_panel(pop, months, rng)

    pe = df["payee_id"].to_numpy()
    mo = df["month"].to_numpy().astype(np.int64) - 1
    day = df["day"].to_numpy().astype(np.float64)

    res = pd.DataFrame(index=df.index)
    birth = np.array([p.birth_day for p in pop.payees], dtype=np.float32)
    res["payee_account_age_days"] = np.maximum(day - birth[pe], 0.0).astype(np.float32)
    res["payee_unique_inflow_payers_30d"] = panel["inflow_n"][pe, mo]
    res["payee_inflow_amount_30d"] = panel["inflow_amt"][pe, mo]
    res["payee_fanout_ratio_24h"] = panel["fanout"][pe, mo]
    res["payee_unique_outflow_payees_30d"] = panel["outflow_n"][pe, mo]
    res["payee_inflow_amount_cv"] = panel["cv"][pe, mo]
    res["payee_inflow_periodicity_score"] = panel["period"][pe, mo]
    res["payee_payer_geo_dispersion"] = panel["geo"][pe, mo]
    res["payee_balance_retention_ratio"] = panel["retention"][pe, mo]

    recip_p = np.array([ROLE_RECIPROCITY[r] for r in pop.payee_role])
    res["payee_reciprocity_flag"] = (
        rng.random(len(df)) < recip_p[pe]).astype(np.int8)

    res["payer_payee_prior_txn_count"] = df["payer_payee_prior_txn_count"].astype(np.float32)
    res["payer_payee_relationship_months"] = df["payer_payee_relationship_months"].astype(np.float32)
    res["payee_report_count"] = _report_count_asof(df, pop).astype(np.float32)
    return res[B3_COLS]


def _report_count_asof(df: pd.DataFrame, pop: Population) -> np.ndarray:
    """Number of fraud reports already filed against the payee at the moment
    of the transaction. No lookahead: reports filed later are invisible."""
    pe = df["payee_id"].to_numpy()
    day = df["day"].to_numpy().astype(np.float64)
    out = np.zeros(len(df), dtype=np.int32)
    have = np.array([bool(p.report_days) for p in pop.payees])
    rel = np.flatnonzero(have[pe])
    if rel.size == 0:
        return out
    order = np.argsort(pe[rel], kind="stable")
    rel = rel[order]
    keys = pe[rel]
    bounds = np.flatnonzero(np.concatenate([[True], keys[1:] != keys[:-1], [True]]))
    for a, b in zip(bounds[:-1], bounds[1:]):
        rows = rel[a:b]
        rd = np.sort(np.asarray(pop.payees[int(keys[a])].report_days))
        out[rows] = np.searchsorted(rd, day[rows], side="left")
    return out


def apply_noise(b3: pd.DataFrame, beta: float, rng: np.random.Generator) -> pd.DataFrame:
    """Add beta-sigma gaussian noise on the standardised scale of each B3
    feature. Applied *before* the consistency model is fitted, so B4b never
    sees a cleaner view of the beneficiary than B3 itself does."""
    if beta <= 0.0:
        return b3
    out = b3.copy()
    for c in B3_COLS:
        v = out[c].to_numpy(dtype=np.float64)
        sd = np.nanstd(v)
        if sd <= 0:
            continue
        out[c] = (v + rng.normal(0.0, beta * sd, len(v))).astype(np.float32)
    return out
