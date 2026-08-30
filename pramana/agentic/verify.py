"""Deterministic conformance checking.

Ten checks, no model, no threshold, no training data. Each returns a boolean
and a human-readable reason. A cart that violates any check is rejected, and
the rejection is reproducible: the same inputs always give the same answer,
which is the property a statistical detector cannot offer.

The honest limit is C1-C10's blind spot, quantified in attacks.py: a purchase
that stays inside the mandate passes every check. Enforcement bounds the loss
at the mandate cap; it does not detect the intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .mandate import CartMandate, Directory, IntentMandate, canonical, verify_sig


@dataclass
class VerificationContext:
    now: datetime
    directory: Directory
    seen_nonces: set[str] = field(default_factory=set)
    spent: dict[str, int] = field(default_factory=dict)

    def principal_key(self, m: IntentMandate):
        return self.directory.principal_keys.get(m.principal_id)

    def revoked_before(self, now: datetime) -> set[str]:
        return self.directory.revoked_before(now)


def _c1(c, m, ctx): return c.amount <= m.max_amount, f"amount {c.amount} vs cap {m.max_amount}"
def _c2(c, m, ctx): return c.mcc in m.allowed_mcc, f"mcc {c.mcc} vs allowed {m.allowed_mcc}"
def _c3(c, m, ctx): return (m.allowed_merchants is None
                            or c.merchant_id in m.allowed_merchants), f"merchant {c.merchant_id}"
def _c4(c, m, ctx): return m.valid_from <= ctx.now <= m.valid_until, f"now {ctx.now.isoformat()}"
def _c5(c, m, ctx): return m.nonce not in ctx.seen_nonces, f"nonce {m.nonce[:8]}..."
def _c6(c, m, ctx):
    total = ctx.spent.get(m.mandate_id, 0) + c.amount
    return total <= m.max_cumulative, f"cumulative {total} vs cap {m.max_cumulative}"
def _c7(c, m, ctx):
    return verify_sig(c.agent_attestation, canonical(c.to_dict()),
                      ctx.directory.agent_keys.get(m.agent_id)), "agent attestation"
def _c8(c, m, ctx):
    return (c.user_confirmation_hash is None
            or c.user_confirmation_hash == c.line_items_hash), "confirmation binding"
def _c9(c, m, ctx): return m.mandate_id not in ctx.revoked_before(ctx.now), "revocation state"
def _c10(c, m, ctx):
    return verify_sig(m.signature, canonical(m.to_dict()),
                      ctx.principal_key(m)), "mandate signature"


CHECKS = [
    ("C1_amount_scope", _c1),
    ("C2_category_scope", _c2),
    ("C3_merchant_scope", _c3),
    ("C4_temporal_validity", _c4),
    ("C5_nonce_freshness", _c5),
    ("C6_cumulative_cap", _c6),
    ("C7_agent_binding", _c7),
    ("C8_confirmation_bind", _c8),
    ("C9_revocation_state", _c9),
    ("C10_mandate_sig", _c10),
]


@dataclass
class Verdict:
    accepted: bool
    checks: list[dict]

    @property
    def failed(self) -> list[str]:
        return [c["id"] for c in self.checks if not c["passed"]]


def verify(cart: CartMandate, mandate: IntentMandate,
           ctx: VerificationContext) -> Verdict:
    results = []
    for cid, fn in CHECKS:
        try:
            ok, detail = fn(cart, mandate, ctx)
        except Exception as exc:                     # a malformed cart is a rejection
            ok, detail = False, f"error: {exc}"
        results.append({"id": cid, "passed": bool(ok), "detail": detail})
    return Verdict(accepted=all(r["passed"] for r in results), checks=results)


def settle(cart: CartMandate, mandate: IntentMandate,
           ctx: VerificationContext) -> Verdict:
    """Verify and, if accepted, record the spend and burn the nonce."""
    v = verify(cart, mandate, ctx)
    if v.accepted:
        ctx.spent[mandate.mandate_id] = ctx.spent.get(mandate.mandate_id, 0) + cart.amount
        ctx.seen_nonces.add(mandate.nonce)
    return v
