"""Construct the payer/payee ecosystem and the relationship portfolio.

Relationship formation is the *only* process that knows a payment's true
economic purpose. It never inspects fraud status: mule accounts form no
legitimate relationships, and victims are selected later by an independent
campaign process (fraud.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .entities import (
    LAMBDA_ROLES,
    PAYEE_ROLES,
    Payee,
    Payer,
    Relationship,
    make_payer,
    sample_payees,
)

#: True economic purpose -> the payee roles that purpose is normally paid to,
#: with mixing weights. The second entry of each pair is the fallback used when
#: the preferred role is absent from the population (lambda = 0). Pre-registered
#: decision 2: the taxonomy does not shrink with lambda, so every purpose keeps
#: a home and lambda varies structural overlap alone.
PURPOSE_ROLE_PREFERENCE: dict[str, tuple[dict[str, float], dict[str, float]]] = {
    "rent":              ({"landlord_individual": 0.60, "property_manager": 0.40},
                          {"landlord_individual": 1.00}),
    "utility_bill":      ({"utility_biller": 1.00},
                          {"merchant_large": 1.00}),
    "education_fees":    ({"education_institution": 1.00},
                          {"merchant_large": 1.00}),
    "merchant_purchase": ({"merchant_small": 0.70, "merchant_large": 0.30},
                          {"merchant_large": 1.00}),
    "salary_reimburse":  ({"employer": 1.00}, {"employer": 1.00}),
    "family_support":    ({"family_member": 1.00}, {"family_member": 1.00}),
    "friend_transfer":   ({"individual_friend": 1.00}, {"individual_friend": 1.00}),
    "loan_repayment":    ({"merchant_large": 0.50, "individual_friend": 0.50},
                          {"merchant_large": 0.50, "individual_friend": 0.50}),
    "investment":        ({"merchant_large": 0.40, "merchant_small": 0.30,
                           "individual_friend": 0.30},
                          {"merchant_large": 0.55, "individual_friend": 0.45}),
    "medical":           ({"merchant_small": 0.60, "merchant_large": 0.40},
                          {"merchant_large": 1.00}),
}

#: Months in which education fees are actually paid (Indian academic calendar:
#: two term-fee peaks). Seasonality is a purpose signature B4 can use and a
#: mule payee cannot reproduce.
EDUCATION_MONTHS: tuple[int, ...] = (4, 5, 10, 11)


@dataclass
class Population:
    payers: list[Payer]
    payees: list[Payee]
    relationships: list[Relationship]
    lam: float

    #: payee_id -> role, as a numpy array for fast joins
    payee_role: np.ndarray
    payee_legit: np.ndarray


class _RolePicker:
    """Samples payees within a role with probability proportional to their
    latent fan-in, so that in-sample beneficiary in-degree inherits the heavy
    tail of the underlying population rather than being uniform."""

    def __init__(self, payees: list[Payee], rng: np.random.Generator):
        self.rng = rng
        self.by_role: dict[str, np.ndarray] = {}
        self.weights: dict[str, np.ndarray] = {}
        ids = np.array([p.payee_id for p in payees])
        roles = np.array([p.role for p in payees], dtype=object)
        fan = np.array([p.fan_in_30d for p in payees])
        for role in PAYEE_ROLES:
            m = roles == role
            if not m.any():
                continue
            w = fan[m]
            self.by_role[role] = ids[m]
            self.weights[role] = w / w.sum()

    def has(self, role: str) -> bool:
        return role in self.by_role

    def pick(self, role: str) -> int:
        pool = self.by_role[role]
        return int(self.rng.choice(pool, p=self.weights[role]))

    def pick_mixture(self, mixture: dict[str, float], fallback: dict[str, float]) -> int | None:
        mix = mixture if all(self.has(r) for r in mixture) else fallback
        mix = {r: w for r, w in mix.items() if self.has(r)}
        if not mix:
            return None
        roles = list(mix)
        probs = np.array([mix[r] for r in roles], dtype=float)
        probs /= probs.sum()
        role = roles[int(self.rng.choice(len(roles), p=probs))]
        return self.pick(role)


def _amount_params(cfg: dict, purpose: str, payer: Payer) -> tuple[float, float]:
    """Relationship-level amount distribution, scaled by payer income so that
    payment size tracks means rather than being drawn from a global pool."""
    a = cfg["amounts"]
    key = {
        "rent": "rent", "utility_bill": "utility", "education_fees": "education",
        "friend_transfer": "friend", "family_support": "family",
        "merchant_purchase": "merchant", "loan_repayment": "loan",
        "medical": "medical", "investment": "investment",
        "salary_reimburse": "salary_reimburse",
    }[purpose]
    mu = a[f"{key}_mu"]
    sigma = a[f"{key}_sigma"]
    income_shift = np.log(payer.monthly_income) - cfg["payer"]["income_mu"]
    return mu + 0.55 * income_shift, sigma


def build_population(cfg: dict, lam: float, rng: np.random.Generator) -> Population:
    n_payers = cfg["population"]["n_payers"]
    n_payees = cfg["population"]["n_payees"]
    months = cfg["population"]["months"]
    r = cfg["relationships"]
    horizon = months * 30.0

    payers = [make_payer(i, cfg, rng) for i in range(n_payers)]
    payees = sample_payees(n_payees, lam, rng, horizon=horizon)
    picker = _RolePicker(payees, rng)

    rels: list[Relationship] = []

    def add(payer: Payer, purpose: str, cadence: str, rate: float) -> None:
        pref, fallback = PURPOSE_ROLE_PREFERENCE[purpose]
        pid = picker.pick_mixture(pref, fallback)
        if pid is None:
            return
        mu, sigma = _amount_params(cfg, purpose, payer)
        # staggered starts: a minority of ties begin part-way through the
        # window, so "legitimate but unfamiliar payee" exists at all times
        if rng.random() < r["p_relationship_starts_midwindow"]:
            start = float(rng.uniform(0.0, horizon - 30.0))
        else:
            start = float(-rng.exponential(400.0))  # predates the window
        rels.append(
            Relationship(
                payer_id=payer.payer_id, payee_id=pid, purpose=purpose,
                cadence=cadence, amount_mu=mu, amount_sigma=sigma,
                start_day=start, rate_per_month=rate,
                day_of_month=int(rng.integers(1, 29)),
            )
        )

    for payer in payers:
        if rng.random() < r["p_has_rent"]:
            add(payer, "rent", "monthly", r["rate_rent"])
        if rng.random() < r["p_has_utility"]:
            for _ in range(max(1, int(rng.poisson(r["n_utility_lambda"])))):
                add(payer, "utility_bill", "monthly", r["rate_utility"])
        if rng.random() < r["p_has_employer"]:
            add(payer, "salary_reimburse", "sporadic", r["rate_salary_reimburse"])
        if rng.random() < r["p_has_loan"]:
            add(payer, "loan_repayment", "monthly", r["rate_loan"])
        if rng.random() < r["p_has_education"]:
            add(payer, "education_fees", "seasonal", r["rate_education"])
        if rng.random() < r["p_has_investment"]:
            add(payer, "investment", "sporadic", r["rate_investment"])
        for _ in range(int(rng.poisson(r["n_friends_lambda"]))):
            add(payer, "friend_transfer", "sporadic", r["rate_friend"])
        for _ in range(int(rng.poisson(r["n_family_lambda"]))):
            add(payer, "family_support", "sporadic", r["rate_family"])
        for _ in range(int(rng.poisson(r["n_merchant_lambda"]))):
            add(payer, "merchant_purchase", "sporadic", r["rate_merchant"])
        for _ in range(int(rng.poisson(r["n_medical_lambda"]))):
            add(payer, "medical", "sporadic", r["rate_medical"])

    payee_role = np.array([p.role for p in payees], dtype=object)
    payee_legit = np.array([p.legit for p in payees], dtype=bool)
    return Population(payers, payees, rels, lam, payee_role, payee_legit)
