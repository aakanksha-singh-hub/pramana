"""The beneficiary-matched adversary.

The pre-registered adversary controls only what the victim *declares*. A real
scammer also controls *which mule account receives the money*, and would pick
one whose beneficiary profile is plausible for the purpose the victim has been
coached to declare. That attacks the purpose-beneficiary consistency mechanism
directly rather than merely the base rate of the declared code, and it is the
adversary most likely to have a finite rho*.

Threat model, stated explicitly
-------------------------------
This adversary is assumed to know the defence. It scores candidate mules
against the *same* purpose-conditional reference the defender uses. That is a
deliberate worst case in the Kerckhoffs sense: the security of a declared-
context control should not depend on the attacker's ignorance of how the
control works.

What the adversary cannot do
----------------------------
It can only choose among accounts that are actually mules. A mule cannot
become a three-year-old utility biller with five thousand inbound payers, so
the best available match to an institutional purpose is still a poor one.
That constraint is the honest limit of the attack, and it is why the surface
is worth measuring rather than assuming.

It also cannot manufacture pair history: a victim has no prior relationship
with any mule, whichever one is chosen. Pair-level features are therefore left
untouched and only the eleven payee-level beneficiary features are swapped.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .features import B3_COLS

#: Beneficiary features that belong to the account, and which the attacker
#: changes by routing to a different mule.
PAYEE_LEVEL_B3: list[str] = [
    "payee_account_age_days", "payee_unique_inflow_payers_30d",
    "payee_inflow_amount_30d", "payee_fanout_ratio_24h",
    "payee_unique_outflow_payees_30d", "payee_reciprocity_flag",
    "payee_report_count", "payee_payer_geo_dispersion",
    "payee_inflow_amount_cv", "payee_inflow_periodicity_score",
    "payee_balance_retention_ratio",
]

#: Features of the payer-payee tie, which routing cannot change: a victim has
#: no history with any mule.
PAIR_LEVEL_B3: list[str] = [
    "payer_payee_relationship_months", "payer_payee_prior_txn_count",
]

assert set(PAYEE_LEVEL_B3) | set(PAIR_LEVEL_B3) == set(B3_COLS)


class BeneficiaryMatcher:
    """Chooses, per (declared purpose, month), the mule accounts whose profile
    best fits that purpose's legitimate reference."""

    def __init__(self, top_frac: float = 0.05, min_k: int = 10, seed: int = 0):
        # A real attacker picks a reasonable account from the stable it
        # controls; it does not solve a global optimisation over every mule in
        # the country. Selecting uniformly from the best 5% (at least ten) is
        # strong without being degenerate: taking only the single best match
        # drives fraud to look *more* typical of the declared purpose than
        # legitimate payments do, which a defender could then exploit in
        # reverse. That artefact is an artefact of the attack model, not a
        # property of the control, so it is designed out rather than reported.
        self.top_frac = top_frac
        self.min_k = min_k
        self.rng = np.random.default_rng(7_000_003 + seed)
        self.pool: dict[tuple[str, int], np.ndarray] = {}
        self.n_candidates: int = 0

    def fit(self, df: pd.DataFrame, cm) -> "BeneficiaryMatcher":
        """Build the candidate pool from every mule-month in the ledger and
        rank it against each purpose's reference."""
        mules = df.loc[~df["payee_legit"].to_numpy().astype(bool),
                       ["payee_id", "month"] + B3_COLS]
        if mules.empty:
            return self
        cand = mules.groupby(["payee_id", "month"], as_index=False).first()
        self.n_candidates = len(cand)

        # score the candidate as the victim would present it: a fresh tie, so
        # pair history is zero whichever mule is chosen
        X = cand[B3_COLS].copy()
        for c in PAIR_LEVEL_B3:
            X[c] = 0.0
        Z = cm.qt.transform(X.to_numpy(dtype=np.float64))

        values = cand[PAYEE_LEVEL_B3].to_numpy(dtype=np.float32)
        months = cand["month"].to_numpy()

        for purpose in cm.models:
            mm = cm.models[purpose]
            dev = Z - mm["mu"]
            d = np.einsum("ij,jk,ik->i", dev, mm["prec"], dev)
            for m in np.unique(months):
                sel = np.flatnonzero(months == m)
                if sel.size == 0:
                    continue
                k = min(sel.size, max(self.min_k, int(round(self.top_frac * sel.size))))
                best = sel[np.argsort(d[sel])[:k]]
                self.pool[(purpose, int(m))] = values[best]
        return self

    def apply(self, frame: pd.DataFrame) -> int:
        """Re-route coached fraudulent payments to a well-matched mule.

        Returns the number of rows re-routed. Only fraudulent rows flagged as
        coached are touched; legitimate rows are never modified, so the
        purpose-conditional reference is unaffected.
        """
        if not self.pool:
            return 0
        mask = ((frame["is_fraud"].to_numpy() == 1)
                & frame["_coached"].to_numpy().astype(bool))
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            return 0

        purposes = frame["purpose_code"].to_numpy()
        months = frame["month"].to_numpy()
        block = frame[PAYEE_LEVEL_B3].to_numpy(dtype=np.float32).copy()

        n = 0
        for key in set(zip(purposes[idx], months[idx].astype(int))):
            cands = self.pool.get(key)
            if cands is None or len(cands) == 0:
                continue
            rows = idx[(purposes[idx] == key[0]) & (months[idx].astype(int) == key[1])]
            pick = self.rng.integers(0, len(cands), size=rows.size)
            block[rows] = cands[pick]
            n += rows.size

        for j, c in enumerate(PAYEE_LEVEL_B3):
            frame[c] = block[:, j]
        return n
