"""Entity definitions for the Pramana payment ecosystem.

Three independent generative processes drive the simulation:

  1. payee behaviour is a function of *payee role* only;
  2. the true economic purpose of a payment is a function of the
     *payer-payee relationship* only;
  3. fraud victimisation is a function of a *scam campaign* process that
     never inspects a payer's relationship portfolio or a payee's role
     beyond "this payee is a mule".

The purpose-beneficiary consistency signal that B4 is meant to capture is
therefore emergent from the interaction of (1) and (2); it is never
planted, and no generative step conditions purpose on the fraud label.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Payee roles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoleSpec:
    """Latent behavioural parameters for a class of beneficiary account."""

    share: float                 # base population share (pre-lambda)
    age_days: tuple[int, int]    # account age at simulation start
    fan_in_30d: tuple[int, int]  # distinct inbound payers per 30 days
    fanout_ratio: float          # fraction of inflow forwarded within 24h
    periodicity: float           # regularity of inbound cadence in [0, 1]
    legit: bool                  # is this a legitimate beneficiary class
    geo_dispersion: float        # spread of inbound payers across regions


# share, age_days, fan_in_30d, fanout, periodicity, legit, geo_dispersion
PAYEE_ROLES: dict[str, RoleSpec] = {
    "individual_friend":     RoleSpec(0.300, (400, 2500),  (1, 8),       0.15, 0.10, True,  0.18),
    "family_member":         RoleSpec(0.120, (600, 3000),  (1, 5),       0.10, 0.60, True,  0.22),
    "landlord_individual":   RoleSpec(0.060, (500, 3000),  (1, 6),       0.20, 0.85, True,  0.12),
    # --- lambda classes: legitimate, structurally mule-like -----------------
    "property_manager":      RoleSpec(0.020, (700, 3000),  (40, 400),    0.30, 0.80, True,  0.30),
    "education_institution": RoleSpec(0.010, (1000, 4000), (100, 2000),  0.25, 0.55, True,  0.55),
    "utility_biller":        RoleSpec(0.010, (1500, 5000), (500, 5000),  0.20, 0.90, True,  0.75),
    "merchant_small":        RoleSpec(0.150, (200, 2000),  (20, 300),    0.45, 0.30, True,  0.45),
    # Legitimate accounts that sweep funds onward as fast as a mule does.
    # They exist in every real network and they are why beneficiary
    # intelligence cannot be an oracle; see CHANGELOG.md.
    "settlement_agent":      RoleSpec(0.015, (120, 1800),  (60, 900),    0.88, 0.25, True,  0.65),
    "gig_worker":            RoleSpec(0.040, (30, 900),    (3, 40),      0.80, 0.18, True,  0.40),
    "chit_fund_collector":   RoleSpec(0.020, (90, 1500),   (15, 120),    0.84, 0.45, True,  0.35),
    # ------------------------------------------------------------------------
    "merchant_large":        RoleSpec(0.050, (1000, 4000), (300, 5000),  0.35, 0.35, True,  0.80),
    "employer":              RoleSpec(0.020, (1000, 4000), (0, 3),       0.05, 0.95, True,  0.20),
    "mule_fresh":            RoleSpec(0.040, (2, 45),      (8, 60),      0.92, 0.05, False, 0.72),
    "mule_aged":             RoleSpec(0.015, (180, 900),   (10, 80),     0.85, 0.08, False, 0.68),
    "scam_collection":       RoleSpec(0.005, (30, 400),    (20, 200),    0.88, 0.10, False, 0.70),
}

#: The four legitimate high-fan-in roles whose combined population share is
#: controlled by lambda. Their structural resemblance to mule accounts is the
#: ambiguity that declared purpose is being tested against.
LAMBDA_ROLES: tuple[str, ...] = (
    "property_manager",
    "education_institution",
    "utility_biller",
    "merchant_small",
    "settlement_agent",
    "gig_worker",
    "chit_fund_collector",
)

#: Roles for which a newly opened account is plausible. A payment network sees
#: a steady stream of account openings, so "thin file" is not by itself
#: evidence of a mule. Institutional roles are excluded: a three-week-old
#: utility biller with five thousand inbound payers is not a real object.
NEW_ACCOUNT_ELIGIBLE: frozenset[str] = frozenset({
    "individual_friend", "family_member", "landlord_individual",
    "property_manager", "merchant_small", "settlement_agent",
    "gig_worker", "chit_fund_collector",
})

#: Fraction of eligible legitimate accounts opened during the window.
P_NEW_ACCOUNT: float = 0.14

#: Fraction of mule accounts that also carry ordinary legitimate traffic -
#: accounts that were a real person's before they were sold, rented or
#: coerced, and that keep receiving payments from friends and customers.
P_MULE_HAS_COVER_TRAFFIC: float = 0.35

MULE_ROLES: tuple[str, ...] = ("mule_fresh", "mule_aged", "scam_collection")

#: Roles a legitimate payer relationship may be formed with.
LEGIT_ROLES: tuple[str, ...] = tuple(r for r, s in PAYEE_ROLES.items() if s.legit)


def role_mixture(lam: float) -> dict[str, float]:
    """Population share per payee role at structural-overlap rate ``lam``.

    Pre-registered semantics (PREREGISTRATION.md, decision 1): the four
    lambda classes take a *combined* share of exactly ``lam``, divided among
    themselves in the proportions of the base table; the remaining eight
    roles are renormalised to ``1 - lam``.
    """
    if not 0.0 <= lam <= 1.0:
        raise ValueError(f"lam must be in [0, 1], got {lam}")

    lam_base = sum(PAYEE_ROLES[r].share for r in LAMBDA_ROLES)
    other_base = sum(s.share for r, s in PAYEE_ROLES.items() if r not in LAMBDA_ROLES)

    mix: dict[str, float] = {}
    for role, spec in PAYEE_ROLES.items():
        if role in LAMBDA_ROLES:
            mix[role] = lam * spec.share / lam_base
        else:
            mix[role] = (1.0 - lam) * spec.share / other_base

    total = sum(mix.values())
    assert abs(total - 1.0) < 1e-9, f"role mixture sums to {total}"
    return mix


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Payer:
    payer_id: int
    geo_region: int
    monthly_income: float
    balance: float
    tenure_days: int
    device_age_days: float
    typing_speed_cps: float      # stable per-person typing rate
    care_level: float            # per-person susceptibility modifier in [0, 1]


@dataclass
class Payee:
    payee_id: int
    role: str
    account_age_days: float      # age at simulation start (day 0)
    birth_day: float             # day the account was opened (negative = pre-window)
    use_day: float               # for mule roles: start of the account's active life
    fan_in_30d: float            # latent distinct inbound payers per 30 days
    fanout_ratio: float
    periodicity: float
    geo_dispersion: float
    legit: bool
    geo_region: int
    # accumulated fraud reports, keyed by the day they were filed; used to
    # build a strictly as-of-time payee_report_count with no lookahead.
    report_days: list[float] = field(default_factory=list)


@dataclass
class Relationship:
    """A stable economic tie between one payer and one payee.

    ``purpose`` is the *true* economic purpose. What the payer declares is a
    noisy function of it (see purpose.py) and is never the truth itself.
    """

    payer_id: int
    payee_id: int
    purpose: str
    cadence: str                 # "monthly" | "sporadic" | "seasonal"
    amount_mu: float
    amount_sigma: float
    start_day: float
    rate_per_month: float = 1.0  # for sporadic cadences
    day_of_month: int = 1        # for monthly cadences


# ---------------------------------------------------------------------------
# Samplers
# ---------------------------------------------------------------------------


def sample_payees(n: int, lam: float, rng: np.random.Generator,
                  horizon: float = 360.0) -> list[Payee]:
    """Draw a payee population at structural-overlap rate ``lam``.

    Legitimate accounts predate the observation window by their sampled age.
    Mule accounts instead have a short active life: an account opened
    ``age_at_use`` days before it starts receiving proceeds, and used over a
    narrow campaign window. Without this, a "fresh" mule would drift to an
    account age of several hundred days by month 12 and the structural
    collision with property managers and small merchants - the thing lambda
    exists to create - would quietly disappear.
    """
    mix = role_mixture(lam)
    roles = list(mix)
    probs = np.array([mix[r] for r in roles])
    drawn = rng.choice(len(roles), size=n, p=probs)

    payees: list[Payee] = []
    for i, ri in enumerate(drawn):
        role = roles[ri]
        spec = PAYEE_ROLES[role]
        lo, hi = spec.age_days
        # log-uniform: account ages are heavy tailed, not flat
        age = float(np.exp(rng.uniform(np.log(max(lo, 1)), np.log(hi))))
        f_lo, f_hi = spec.fan_in_30d
        fan_in = float(np.exp(rng.uniform(np.log(max(f_lo, 0.5)), np.log(max(f_hi, 1)))))
        if spec.legit:
            if role in NEW_ACCOUNT_ELIGIBLE and rng.random() < P_NEW_ACCOUNT:
                birth_day = float(rng.uniform(-60.0, horizon - 25.0))
                age = max(-birth_day, 1.0)
                fan_in *= 0.55        # a new account has not built its base yet
            else:
                birth_day = -age
            use_day = float("nan")
        else:
            use_day = float(rng.uniform(15.0, horizon - 5.0))
            birth_day = use_day - age
        payees.append(
            Payee(
                payee_id=i,
                role=role,
                account_age_days=age,
                birth_day=birth_day,
                use_day=use_day,
                fan_in_30d=fan_in,
                fanout_ratio=float(np.clip(rng.normal(spec.fanout_ratio, 0.09), 0.0, 1.0)),
                periodicity=float(np.clip(rng.normal(spec.periodicity, 0.11), 0.0, 1.0)),
                geo_dispersion=float(np.clip(rng.normal(spec.geo_dispersion, 0.10), 0.0, 1.0)),
                legit=spec.legit,
                geo_region=int(rng.integers(0, 40)),
            )
        )
    return payees


def make_payer(i: int, cfg: dict, rng: np.random.Generator) -> Payer:
    p = cfg["payer"]
    income = float(rng.lognormal(p["income_mu"], p["income_sigma"]))
    mult = float(rng.lognormal(p["balance_multiple_mu"], p["balance_multiple_sigma"]))
    return Payer(
        payer_id=i,
        geo_region=int(rng.integers(0, p["n_geo_regions"])),
        monthly_income=income,
        balance=income * mult / np.exp(p["balance_multiple_mu"]),
        tenure_days=int(rng.integers(p["tenure_days_min"], p["tenure_days_max"])),
        device_age_days=float(max(1.0, rng.normal(p["device_age_days_mu"], p["device_age_days_sigma"]))),
        typing_speed_cps=float(np.clip(rng.normal(3.4, 0.9), 0.8, 8.0)),
        care_level=float(rng.beta(2.0, 2.0)),
    )
