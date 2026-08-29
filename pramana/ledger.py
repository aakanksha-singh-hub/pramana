"""Transaction stream generation.

Legitimate payments are emitted from the relationship portfolio. Session
(B2) features are attached *after* the legitimate and fraudulent streams are
merged, and depend on a duress latent plus payment novelty - never on the
fraud label directly. P(coercion | legit) is nonzero and P(coercion | scam) is
below one, so B2 is genuinely informative without being a label proxy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .population import EDUCATION_MONTHS, Population
from .purpose import PURPOSE_INDEX, PURPOSES

CHANNELS = ["upi_p2p", "upi_p2m", "imps", "neft", "card"]
CHANNEL_INDEX = {c: i for i, c in enumerate(CHANNELS)}

#: Channel mix by true purpose. Correlated with purpose (a real property of
#: how Indian rails are used) but never with the fraud label directly.
CHANNEL_BY_PURPOSE: dict[str, list[float]] = {
    "rent":              [0.42, 0.06, 0.34, 0.16, 0.02],
    "utility_bill":      [0.10, 0.62, 0.06, 0.04, 0.18],
    "education_fees":    [0.14, 0.34, 0.24, 0.22, 0.06],
    "merchant_purchase": [0.16, 0.58, 0.04, 0.02, 0.20],
    "salary_reimburse":  [0.58, 0.06, 0.24, 0.10, 0.02],
    "family_support":    [0.74, 0.02, 0.16, 0.06, 0.02],
    "friend_transfer":   [0.82, 0.04, 0.10, 0.03, 0.01],
    "loan_repayment":    [0.30, 0.22, 0.22, 0.20, 0.06],
    "investment":        [0.30, 0.16, 0.28, 0.24, 0.02],
    "medical":           [0.34, 0.36, 0.14, 0.08, 0.08],
    "other":             [0.60, 0.12, 0.16, 0.08, 0.04],
}

#: cadence codes
MONTHLY, SPORADIC, SEASONAL = 0, 1, 2

CORE_COLUMNS = [
    "txn_id", "payer_id", "payee_id", "day", "month", "amount",
    "channel", "true_purpose", "is_fraud", "scam_type", "coerced",
]


def _cadence_code(c: str) -> int:
    return {"monthly": MONTHLY, "sporadic": SPORADIC, "seasonal": SEASONAL}[c]


def generate_legit_ledger(pop: Population, cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    months = cfg["population"]["months"]
    rels = pop.relationships
    n_rel = len(rels)

    payer_id = np.fromiter((r.payer_id for r in rels), dtype=np.int32, count=n_rel)
    payee_id = np.fromiter((r.payee_id for r in rels), dtype=np.int32, count=n_rel)
    purpose_i = np.fromiter((PURPOSE_INDEX[r.purpose] for r in rels), dtype=np.int8, count=n_rel)
    cadence = np.fromiter((_cadence_code(r.cadence) for r in rels), dtype=np.int8, count=n_rel)
    amt_mu = np.fromiter((r.amount_mu for r in rels), dtype=np.float64, count=n_rel)
    amt_sig = np.fromiter((r.amount_sigma for r in rels), dtype=np.float64, count=n_rel)
    start = np.fromiter((r.start_day for r in rels), dtype=np.float64, count=n_rel)
    rate = np.fromiter((r.rate_per_month for r in rels), dtype=np.float64, count=n_rel)
    dom = np.fromiter((r.day_of_month for r in rels), dtype=np.float64, count=n_rel)

    # A relationship's payment size is stable across its own history; only the
    # jitter differs by cadence. This is what gives "rent" a periodic, stable
    # signature that a mule inflow cannot reproduce.
    base_amount = np.exp(rng.normal(amt_mu, amt_sig))
    jitter = np.where(cadence == MONTHLY, 0.05, np.where(cadence == SEASONAL, 0.25, 0.55))

    chunks = []
    for m in range(1, months + 1):
        month_start, month_end = (m - 1) * 30.0, m * 30.0
        active = start < month_end

        counts = np.zeros(n_rel, dtype=np.int16)
        mm = active & (cadence == MONTHLY)
        counts[mm] = (rng.random(mm.sum()) < np.minimum(rate[mm], 1.0)).astype(np.int16)
        sp = active & (cadence == SPORADIC)
        counts[sp] = rng.poisson(rate[sp]).astype(np.int16)
        if m in EDUCATION_MONTHS:
            se = active & (cadence == SEASONAL)
            counts[se] = rng.poisson(rate[se] * 3.0).astype(np.int16)

        if counts.sum() == 0:
            continue
        idx = np.repeat(np.arange(n_rel), counts)
        n = idx.size

        day = np.where(
            cadence[idx] == MONTHLY,
            month_start + dom[idx] + rng.normal(0.0, 1.4, n),
            month_start + rng.uniform(0.0, 30.0, n),
        )
        day = np.clip(day, month_start, month_end - 1e-6)
        # a relationship cannot transact before it starts
        keep = day >= start[idx]
        idx, day = idx[keep], day[keep]
        if idx.size == 0:
            continue

        amount = base_amount[idx] * np.exp(rng.normal(0.0, jitter[idx]))
        chunks.append(
            pd.DataFrame({
                "payer_id": payer_id[idx],
                "payee_id": payee_id[idx],
                "day": day.astype(np.float32),
                "month": np.int8(m),
                "amount": np.round(amount, 2).astype(np.float32),
                "true_purpose_i": purpose_i[idx],
            })
        )

    df = pd.concat(chunks, ignore_index=True)
    df = pd.concat([df, _adhoc_payments(pop, cfg, rng)], ignore_index=True)

    tp = np.array(PURPOSES, dtype=object)[df["true_purpose_i"].to_numpy()]
    df["true_purpose"] = tp
    df.drop(columns=["true_purpose_i"], inplace=True)
    df["channel"] = _sample_channels(tp, rng)
    df["is_fraud"] = np.int8(0)
    df["scam_type"] = None
    df["coerced"] = rng.random(len(df)) < cfg["fraud"]["p_coercion_given_legit"]
    return df


def _adhoc_payments(pop: Population, cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    """One-off payments to payees the payer has no standing relationship with.

    These are the legitimate noise floor: unfamiliar payee, no history, often
    pasted identifiers. They are where false positives live, and without them
    "first payment to this payee" would be an almost perfect fraud rule.
    """
    months = cfg["population"]["months"]
    n_payers = len(pop.payers)
    rate = cfg["ledger"]["adhoc_rate"]

    legit_ids = np.array([p.payee_id for p in pop.payees if p.legit])
    fan = np.array([p.fan_in_30d for p in pop.payees if p.legit])
    w = fan / fan.sum()

    counts = rng.poisson(rate, size=(n_payers, months))
    total = int(counts.sum())
    payer_idx = np.repeat(np.arange(n_payers), counts.sum(axis=1))
    month_idx = np.concatenate([np.repeat(np.arange(1, months + 1), counts[i]) for i in range(n_payers)])

    incomes = np.array([p.monthly_income for p in pop.payers])
    shift = np.log(incomes[payer_idx]) - cfg["payer"]["income_mu"]
    amount = np.exp(rng.normal(7.0 + 0.55 * shift, 1.2))

    purpose = rng.choice(
        np.array(["merchant_purchase", "friend_transfer", "other", "medical"], dtype=object),
        size=total, p=[0.46, 0.26, 0.20, 0.08],
    )
    return pd.DataFrame({
        "payer_id": payer_idx.astype(np.int32),
        "payee_id": rng.choice(legit_ids, size=total, p=w).astype(np.int32),
        "day": ((month_idx - 1) * 30.0 + rng.uniform(0, 30, total)).astype(np.float32),
        "month": month_idx.astype(np.int8),
        "amount": np.round(amount, 2).astype(np.float32),
        "true_purpose_i": np.array([PURPOSE_INDEX[p] for p in purpose], dtype=np.int8),
    })


def _sample_channels(true_purpose: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    out = np.empty(len(true_purpose), dtype=object)
    for p in np.unique(true_purpose):
        m = np.flatnonzero(true_purpose == p)
        out[m] = np.array(CHANNELS, dtype=object)[
            rng.choice(len(CHANNELS), size=m.size, p=CHANNEL_BY_PURPOSE[p])
        ]
    return out


# ---------------------------------------------------------------------------
# Session (B2) features
# ---------------------------------------------------------------------------


def attach_sessions(df: pd.DataFrame, pop: Population, cfg: dict,
                    rng: np.random.Generator) -> pd.DataFrame:
    """Generate B2 raw session telemetry from the duress latent.

    ``paste_used_for_payee`` and ``is_new_device`` also depend on payment
    novelty, so that no single session feature is a clean coercion proxy.
    """
    n = len(df)
    c = df["coerced"].to_numpy()
    novel = df["is_first_payment_to_payee"].to_numpy().astype(bool)

    typing = np.array([p.typing_speed_cps for p in pop.payers], dtype=np.float32)
    dev_age = np.array([p.device_age_days for p in pop.payers], dtype=np.float32)
    pid = df["payer_id"].to_numpy()

    out = pd.DataFrame(index=df.index)
    out["session_duration_s"] = np.where(
        c, rng.gamma(9.0, 40.0, n), rng.gamma(3.0, 15.0, n)).astype(np.float32)
    out["time_on_confirm_screen_s"] = np.where(
        c, rng.gamma(4.0, 6.0, n), rng.gamma(1.6, 2.5, n)).astype(np.float32)
    out["screen_on_time_before_txn_s"] = np.where(
        c, rng.gamma(6.0, 50.0, n), rng.gamma(2.0, 20.0, n)).astype(np.float32)
    out["n_amount_edits"] = np.where(
        c, rng.poisson(1.8, n), rng.poisson(0.25, n)).astype(np.int16)
    out["n_payee_field_edits"] = np.where(
        c, rng.poisson(1.4, n), rng.poisson(0.30, n)).astype(np.int16)
    out["n_app_switches"] = np.where(
        c, rng.poisson(3.2, n), rng.poisson(0.50, n)).astype(np.int16)
    out["typing_speed_cps"] = (
        typing[pid] * np.where(c, 0.75, 1.0) * np.exp(rng.normal(0, 0.12, n))
    ).astype(np.float32)
    out["concurrent_call_active"] = (
        rng.random(n) < np.where(c, 0.72, 0.03)).astype(np.int8)
    p_paste = np.where(c, 0.80, np.where(novel, 0.45, 0.12))
    out["paste_used_for_payee"] = (rng.random(n) < p_paste).astype(np.int8)
    p_newdev = np.where(c, 0.09, 0.035)
    is_new = rng.random(n) < p_newdev
    out["is_new_device"] = is_new.astype(np.int8)
    out["device_age_days"] = np.where(
        is_new, rng.uniform(0, 14, n), dev_age[pid]).astype(np.float32)
    return out
