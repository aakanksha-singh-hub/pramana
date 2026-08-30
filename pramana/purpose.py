"""Purpose taxonomy and the declaration model.

A payment has a *true* economic purpose, fixed by the payer-payee
relationship. What the payer *declares* is a noisy function of that truth
(legitimate case) or a function of the scam narrative and the attacker's
coaching effectiveness rho (fraud case). Nothing here reads the fraud label
in order to choose a legitimate declaration, and nothing reads the payee's
role in order to choose a fraudulent one: at rho = 0 the victim declares
what the narrative told them, whatever payee they happen to be paying.
"""

from __future__ import annotations

import numpy as np

PURPOSES: list[str] = [
    "rent",              # strong signature: periodic, stable payee
    "salary_reimburse",  # inbound-light payee, employer-like
    "family_support",    # recurring, reciprocal, small payer set
    "friend_transfer",   # low signature, bidirectional, sporadic
    "education_fees",    # institutional payee, seasonal, high fan-in LEGIT
    "utility_bill",      # institutional, periodic, huge fan-in LEGIT
    "merchant_purchase", # commercial, high fan-in LEGIT
    "loan_repayment",    # periodic, institutional or individual
    "investment",        # no strong legit signature in P2P - scam favourite
    "medical",           # sporadic, institutional
    "other",             # deliberate null category
]

PURPOSE_INDEX: dict[str, int] = {p: i for i, p in enumerate(PURPOSES)}

# ---------------------------------------------------------------------------
# Legitimate declaration: true purpose -> declared purpose
# ---------------------------------------------------------------------------

#: Row-stochastic confusion matrix. Diagonal mass is the probability the payer
#: declares the true purpose; off-diagonal mass is honest mislabelling, driven
#: by menu design, haste and category ambiguity rather than by deception.
CONFUSION: dict[str, dict[str, float]] = {
    "rent":              {"rent": 0.82, "other": 0.10, "loan_repayment": 0.04, "family_support": 0.04},
    "salary_reimburse":  {"salary_reimburse": 0.78, "other": 0.12, "friend_transfer": 0.06, "family_support": 0.04},
    "family_support":    {"family_support": 0.74, "friend_transfer": 0.16, "other": 0.10},
    "friend_transfer":   {"friend_transfer": 0.65, "family_support": 0.20, "other": 0.15},
    "education_fees":    {"education_fees": 0.88, "other": 0.12},
    "utility_bill":      {"utility_bill": 0.91, "other": 0.07, "merchant_purchase": 0.02},
    "merchant_purchase": {"merchant_purchase": 0.84, "other": 0.12, "friend_transfer": 0.04},
    "loan_repayment":    {"loan_repayment": 0.80, "other": 0.12, "family_support": 0.04, "friend_transfer": 0.04},
    "investment":        {"investment": 0.76, "other": 0.16, "loan_repayment": 0.08},
    "medical":           {"medical": 0.72, "other": 0.18, "family_support": 0.10},
    "other":             {"other": 1.00},
}

for _true, _row in CONFUSION.items():
    assert abs(sum(_row.values()) - 1.0) < 1e-9, f"CONFUSION[{_true}] does not sum to 1"
    assert set(_row) <= set(PURPOSES), f"CONFUSION[{_true}] has an unknown target"

# Pre-flattened for fast vectorised sampling.
_CONF_KEYS = {t: list(r) for t, r in CONFUSION.items()}
_CONF_PROBS = {t: np.array(list(r.values())) for t, r in CONFUSION.items()}


def declare_legit(true_purpose: str, rng: np.random.Generator) -> str:
    keys = _CONF_KEYS[true_purpose]
    return keys[int(rng.choice(len(keys), p=_CONF_PROBS[true_purpose]))]


def declare_legit_vec(true_purposes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Vectorised legitimate declaration over an array of true purposes."""
    out = np.empty(len(true_purposes), dtype=object)
    for tp in np.unique(true_purposes):
        idx = np.flatnonzero(true_purposes == tp)
        keys = np.array(_CONF_KEYS[tp], dtype=object)
        out[idx] = keys[rng.choice(len(keys), size=len(idx), p=_CONF_PROBS[tp])]
    return out


# ---------------------------------------------------------------------------
# Fraudulent declaration: the rho mechanism
# ---------------------------------------------------------------------------

#: What the scam narrative tells the victim they are paying for. The victim
#: declares this in good faith; it is the *uncoached* declaration.
SCAM_NARRATIVE_PURPOSE: dict[str, str] = {
    "digital_arrest":  "other",
    "investment_scam": "investment",
    "task_scam":       "investment",
    "impersonation":   "family_support",
    "fake_fees":       "education_fees",
    "refund_scam":     "other",
}

#: Purposes whose legitimate beneficiary distribution a mule account does not
#: badly violate: thin history, few payers, no periodicity, or no institutional
#: signature. A competent scammer steers the declaration into this set.
COACHED_SAFE_SET: list[str] = ["friend_transfer", "other", "investment"]


def declare_fraud(scam_type: str, rho: float, rng: np.random.Generator) -> str:
    """rho = coaching effectiveness.

    With probability rho the attacker successfully steers the victim's
    declaration into a purpose class whose legitimate beneficiary profile the
    mule payee does *not* contradict. Otherwise the victim declares the scam
    narrative's own purpose, which may be structurally implausible for that
    payee - and that implausibility is the entire signal B4 is being tested on.
    """
    if rng.random() < rho:
        return COACHED_SAFE_SET[int(rng.integers(0, len(COACHED_SAFE_SET)))]
    return SCAM_NARRATIVE_PURPOSE[scam_type]


def declare_fraud_vec(scam_types: np.ndarray, rho: float, rng: np.random.Generator,
                      safe_weights: np.ndarray | None = None) -> np.ndarray:
    """Vectorised fraudulent declaration.

    ``safe_weights`` selects the adversary model.

    ``None`` is the pre-registered adversary: a coached declaration is drawn
    uniformly from COACHED_SAFE_SET. Because legitimate "investment" is rare,
    a uniform draw leaves a base-rate trace, so even perfect coaching does not
    make the declaration information-free.

    Supplying weights gives the *prevalence-matched* adversary: the coached
    declaration is drawn in proportion to the legitimate frequency of each
    safe purpose, so at rho = 1 the declared code carries no marginal
    information about the label at all and any remaining B4 value must come
    from the purpose-beneficiary interaction rather than from the code itself.
    This is a secondary analysis; it never touches the primary surface.
    """
    coached = rng.random(len(scam_types)) < rho
    safe = np.array(COACHED_SAFE_SET, dtype=object)
    out = np.array([SCAM_NARRATIVE_PURPOSE[s] for s in scam_types], dtype=object)
    n_c = int(coached.sum())
    if n_c:
        if safe_weights is None:
            out[coached] = safe[rng.integers(0, len(safe), size=n_c)]
        else:
            w = np.asarray(safe_weights, dtype=float)
            w = w / w.sum()
            out[coached] = safe[rng.choice(len(safe), size=n_c, p=w)]
    return out


ADVERSARIES = ("uniform", "prevalence")


# ---------------------------------------------------------------------------
# Cardinality collapse (the K sweep)
# ---------------------------------------------------------------------------

COLLAPSE_K6: dict[str, str] = {
    "rent": "housing",
    "utility_bill": "bills_services",
    "education_fees": "bills_services",
    "medical": "bills_services",
    "family_support": "personal_transfer",
    "friend_transfer": "personal_transfer",
    "merchant_purchase": "commerce",
    "loan_repayment": "financial",
    "investment": "financial",
    "salary_reimburse": "financial",
    "other": "other",
}

COLLAPSE_K3: dict[str, str] = {
    "rent": "personal",
    "family_support": "personal",
    "friend_transfer": "personal",
    "salary_reimburse": "personal",
    "medical": "personal",
    "loan_repayment": "personal",
    "utility_bill": "commercial",
    "education_fees": "commercial",
    "merchant_purchase": "commercial",
    "investment": "commercial",
    "other": "other",
}


def collapse(declared: np.ndarray, K: int) -> np.ndarray:
    """Project declared purposes onto a coarser taxonomy of cardinality K."""
    if K == 11:
        return declared
    table = {6: COLLAPSE_K6, 3: COLLAPSE_K3}.get(K)
    if table is None:
        raise ValueError(f"K must be one of 3, 6, 11; got {K}")
    return np.array([table[d] for d in declared], dtype=object)


def taxonomy(K: int) -> list[str]:
    if K == 11:
        return list(PURPOSES)
    table = {6: COLLAPSE_K6, 3: COLLAPSE_K3}[K]
    seen: list[str] = []
    for p in PURPOSES:
        if table[p] not in seen:
            seen.append(table[p])
    return seen
