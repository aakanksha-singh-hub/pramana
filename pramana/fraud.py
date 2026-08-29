"""Scam injection: an independent victimisation process.

Nothing in this module reads a payer's relationship portfolio or a payment's
declared purpose. Victims are drawn by a campaign process from a personal
susceptibility latent; the scam type is drawn from a campaign mix; the
beneficiary is drawn from the mule population. The declared purpose of a
fraudulent payment is decided separately, at feature-construction time, by
purpose.declare_fraud_vec under the coaching parameter rho - which is what
makes rho sweepable without regenerating the ledger.

Case-size calibration
---------------------
Episode (case) losses are lognormal with mu = 8.9364, sigma = 2.1803. These
two parameters were solved, not tuned, to reproduce two published figures
simultaneously: a mean case loss of INR 22,931 crore / 28 lakh cases =
INR 81,896, and the 45% of cases lying above INR 10,000 reported in the RBI
discussion paper of 9 April 2026. The resulting share of fraud *value* above
INR 10,000 is 98.0%, against the 98.5% reported. That residual is recorded in
the fidelity scorecard rather than fitted away.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .entities import MULE_ROLES
from .ledger import CHANNELS
from .population import Population

#: Solved against RBI-cited case statistics; see module docstring.
CASE_LOSS_MU = 8.9364
CASE_LOSS_SIGMA = 2.1803

SCAM_TYPES = [
    "digital_arrest", "investment_scam", "task_scam",
    "impersonation", "fake_fees", "refund_scam",
]
SCAM_MIX = [0.18, 0.26, 0.20, 0.14, 0.10, 0.12]

#: Scam proceeds are pushed down person-to-person rails, not card rails.
FRAUD_CHANNEL_MIX = [0.44, 0.06, 0.28, 0.20, 0.02]

#: Probability an in-sample victim files a report that reaches the network.
P_REPORT_FILED = 0.35
#: Probability a legitimate beneficiary attracts a spurious dispute, scaled by
#: its fan-in. Without this, payee_report_count would be a perfect label.
BACKGROUND_REPORT_RATE = 0.0022


def inject_scams(pop: Population, cfg: dict, n_legit: int,
                 rng: np.random.Generator) -> pd.DataFrame:
    f = cfg["fraud"]
    months = cfg["population"]["months"]
    horizon = months * 30.0

    n_target = int(round(f["target_rate_volume"] / (1.0 - f["target_rate_volume"]) * n_legit))
    mean_txn_per_episode = 1.0 + f["txns_per_episode_lambda"] - 1.0
    n_episodes = max(1, int(round(n_target / max(mean_txn_per_episode, 1e-9))))

    # --- victim selection: susceptibility only, never portfolio ------------
    care = np.array([p.care_level for p in pop.payers])
    w = np.exp(-2.2 * care)
    w = w / w.sum()
    victims = rng.choice(len(pop.payers), size=n_episodes, replace=True, p=w)

    # --- beneficiary selection: from the mule population -------------------
    mule_mask = np.array([p.role in MULE_ROLES for p in pop.payees])
    mule_ids = np.array([p.payee_id for p in pop.payees])[mule_mask]
    mule_fan = np.array([p.fan_in_30d for p in pop.payees])[mule_mask]
    mule_w = mule_fan / mule_fan.sum()
    mules = rng.choice(mule_ids, size=n_episodes, p=mule_w)

    scam_type = np.array(SCAM_TYPES, dtype=object)[
        rng.choice(len(SCAM_TYPES), size=n_episodes, p=SCAM_MIX)]

    # --- episode structure -------------------------------------------------
    n_txn = 1 + rng.poisson(f["txns_per_episode_lambda"] - 1.0, n_episodes)
    case_loss = rng.lognormal(CASE_LOSS_MU, CASE_LOSS_SIGMA, n_episodes)
    # a mule account has a short active life; episodes cluster just after the
    # account is brought into use, which is what keeps its observed age low
    use_day = np.array([pop.payees[int(m)].use_day for m in mules])
    ep_start = np.clip(use_day + rng.exponential(6.0, n_episodes), 0.0, horizon - 2.0)
    ep_coerced = rng.random(n_episodes) < f["p_coercion_given_scam"]

    idx = np.repeat(np.arange(n_episodes), n_txn)
    n = idx.size

    # split the case loss across the episode's transactions; the first
    # transaction is typically the largest ("verification" payments follow)
    raw = rng.gamma(1.6, 1.0, n)
    denom = np.bincount(idx, weights=raw, minlength=n_episodes)[idx]
    amount = case_loss[idx] * raw / denom

    # transactions in an episode land within hours to a couple of days
    offset = np.zeros(n)
    seq = np.arange(n) - np.repeat(np.cumsum(np.concatenate([[0], n_txn[:-1]])), n_txn)
    offset = np.cumsum(rng.exponential(0.35, n)) * 0.0 + seq * rng.exponential(0.30, n)
    day = np.clip(ep_start[idx] + offset, 0.0, horizon - 1e-6)

    df = pd.DataFrame({
        "payer_id": np.array([pop.payers[v].payer_id for v in victims], dtype=np.int32)[idx],
        "payee_id": mules[idx].astype(np.int32),
        "day": day.astype(np.float32),
        "month": (np.floor(day / 30.0) + 1).astype(np.int8),
        "amount": np.round(amount, 2).astype(np.float32),
        "true_purpose": None,
        "channel": np.array(CHANNELS, dtype=object)[
            rng.choice(len(CHANNELS), size=n, p=FRAUD_CHANNEL_MIX)],
        "is_fraud": np.int8(1),
        "scam_type": scam_type[idx],
        "coerced": ep_coerced[idx],
    })

    _accrue_reports(pop, mules, ep_start, n_txn, rng)
    return df


def _accrue_reports(pop: Population, mules: np.ndarray, ep_start: np.ndarray,
                    n_txn: np.ndarray, rng: np.random.Generator) -> None:
    """Record fraud reports with a filing delay, plus a background dispute
    rate on legitimate accounts.

    Report *days* are stored, not counts, so that B3 can compute a strictly
    as-of-transaction-time count with no lookahead into the test period.
    """
    filed = rng.random(len(mules)) < P_REPORT_FILED
    # victim realisation, NCRP filing and network propagation: weeks, not days
    delay = rng.gamma(2.2, 8.0, len(mules))
    for pid, d in zip(mules[filed], (ep_start + delay)[filed]):
        pop.payees[int(pid)].report_days.append(float(d))

    horizon = 360.0
    for p in pop.payees:
        if not p.legit:
            continue
        lam_bg = BACKGROUND_REPORT_RATE * np.sqrt(p.fan_in_30d)
        k = rng.poisson(lam_bg)
        for _ in range(int(k)):
            p.report_days.append(float(rng.uniform(0.0, horizon)))
