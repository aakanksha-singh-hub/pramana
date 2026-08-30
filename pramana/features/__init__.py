"""Feature dictionary and the one-bucket invariant.

Every model input belongs to exactly one feature group. This is the single
most important implementation guard in the project: if B4 silently re-encoded
B3, a measured gain would only mean "we gave the model beneficiary
information twice". The dictionary below is the authority, it matches
PREREGISTRATION.md line for line, and ``validate()`` fails loudly if any
column appears in two groups or if a group's realised columns drift from the
pre-registered list.
"""

from __future__ import annotations

B1_COLS: list[str] = [
    "amount", "log_amount", "hour_of_day", "day_of_week", "day_of_month",
    "channel", "is_first_payment_to_payee", "payer_txn_count_24h",
    "payer_txn_count_7d", "payer_amount_sum_24h",
    "amount_z_vs_payer_history", "amount_over_balance_ratio",
    "days_since_payer_last_txn",
]

B2_COLS: list[str] = [
    "session_duration_s", "time_on_confirm_screen_s",
    "n_amount_edits", "n_payee_field_edits", "n_app_switches",
    "typing_speed_cps", "is_new_device", "device_age_days",
    "paste_used_for_payee", "screen_on_time_before_txn_s",
    "concurrent_call_active",
]

B3_COLS: list[str] = [
    "payee_account_age_days", "payee_unique_inflow_payers_30d",
    "payee_inflow_amount_30d", "payee_fanout_ratio_24h",
    "payee_unique_outflow_payees_30d", "payee_reciprocity_flag",
    "payer_payee_relationship_months", "payer_payee_prior_txn_count",
    "payee_report_count", "payee_payer_geo_dispersion",
    "payee_inflow_amount_cv", "payee_inflow_periodicity_score",
    "payee_balance_retention_ratio",
]

#: Variant a - the honest floor: the declared code and nothing else.
B4A_COLS: list[str] = ["purpose_code"]

#: Variant b - the declared code plus its conditional consistency residuals.
#: The residual columns are *derived from* B3 values but are not B3 values:
#: each is a deviation of this payee from the purpose-conditional legitimate
#: reference distribution. A model given B3 alone cannot compute them, because
#: it is never given the purpose. A model given purpose alone cannot compute
#: them either. They exist only in the interaction, which is the hypothesis
#: under test.
B4B_COLS: list[str] = (
    ["purpose_code", "consistency_mahalanobis", "consistency_loglik"]
    + [f"resid_{c}" for c in B3_COLS]
)

GROUPS: dict[str, list[str]] = {
    "b1": B1_COLS, "b2": B2_COLS, "b3": B3_COLS,
    "b4a": B4A_COLS, "b4b": B4B_COLS,
}

#: Columns that are never model inputs: identifiers, generative latents, the
#: label, and any raw truth a production system would not observe.
FORBIDDEN_AS_INPUT: frozenset[str] = frozenset({
    "txn_id", "payer_id", "payee_id", "day", "month", "is_fraud",
    "scam_type", "coerced", "true_purpose", "payee_role", "payee_legit",
    "declared_purpose", "_coached",
})

CATEGORICAL: frozenset[str] = frozenset({"channel", "purpose_code"})


def validate() -> None:
    """Assert the one-bucket invariant.

    b4a is a strict subset of b4b by construction (both carry purpose_code),
    so the invariant is checked over the arms that are ever combined:
    {b1, b2, b3} must be pairwise disjoint, and neither b4 variant may
    reintroduce a B1/B2/B3 column.
    """
    base = {"b1": B1_COLS, "b2": B2_COLS, "b3": B3_COLS}
    seen: dict[str, str] = {}
    for g, cols in base.items():
        for c in cols:
            if c in seen:
                raise AssertionError(
                    f"one-bucket violation: {c!r} is in both {seen[c]} and {g}")
            seen[c] = g

    for g, cols in (("b4a", B4A_COLS), ("b4b", B4B_COLS)):
        for c in cols:
            if c in seen:
                raise AssertionError(
                    f"one-bucket violation: {g} reintroduces {seen[c]} column {c!r}")
            if c in FORBIDDEN_AS_INPUT:
                raise AssertionError(f"{g} contains forbidden column {c!r}")

    for g, cols in GROUPS.items():
        if len(set(cols)) != len(cols):
            raise AssertionError(f"{g} contains a duplicate column")


def columns_for(groups: list[str]) -> list[str]:
    """Ordered, de-duplicated column list for an experimental arm."""
    out: list[str] = []
    for g in groups:
        for c in GROUPS[g]:
            if c not in out:
                out.append(c)
    return out


validate()
