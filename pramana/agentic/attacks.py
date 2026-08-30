"""Attack families run against the deterministic checks.

Eight of the ten families are caught structurally, at zero false positives on
in-scope traffic. Two are not, and they are the most important rows in the
table: an agent that spends inside the mandate - whether because it was
compromised, or because a prompt injection steered it to a purchase the user
never wanted - passes every check. Conformance checking does not detect that.
What it does is bound the loss at the mandate cap, and A9/A10 quantify by how
much.

Volunteering that limit is the point. It is also the direct answer to "AP2
already does mandate verification": the contribution is not the checks, it is
the measurement of what they do and do not buy.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from nacl.signing import SigningKey

from .mandate import CartMandate, IntentMandate, demo_scenario, new_nonce
from .verify import VerificationContext, settle, verify

IN_SCOPE_MCC = "5941"
IN_SCOPE_MERCHANT = "merch:runfast"


@dataclass
class AttackResult:
    attack_id: str
    name: str
    expected_catcher: str | None
    caught: bool
    failed_checks: list[str]
    note: str = ""


def _cart(m: IntentMandate, agent: SigningKey, amount: int = 4200,
          mcc: str = IN_SCOPE_MCC, merchant: str = IN_SCOPE_MERCHANT,
          confirm: str | None = "h_ok", items: str = "h_ok") -> CartMandate:
    return CartMandate(
        cart_id="cart_" + secrets.token_hex(4), parent_mandate_id=m.mandate_id,
        amount=amount, mcc=mcc, merchant_id=merchant, line_items_hash=items,
        user_confirmation_hash=confirm,
    ).attest(agent)


def run_all(now: datetime | None = None) -> list[AttackResult]:
    now = now or datetime.now(timezone.utc)
    out: list[AttackResult] = []

    def fresh():
        m, principal, agent, directory = demo_scenario(now)
        return m, principal, agent, VerificationContext(now=now, directory=directory)

    # A1 amount escalation
    m, _, ag, ctx = fresh()
    v = verify(_cart(m, ag, amount=40000), m, ctx)
    out.append(AttackResult("A1", "Amount escalation beyond mandate cap",
                            "C1_amount_scope", not v.accepted, v.failed))

    # A2 category violation
    m, _, ag, ctx = fresh()
    v = verify(_cart(m, ag, mcc="5691", merchant="merch:luxebags"), m, ctx)
    out.append(AttackResult("A2", "Category violation", "C2_category_scope",
                            not v.accepted, v.failed))

    # A3 mandate replay
    m, _, ag, ctx = fresh()
    settle(_cart(m, ag), m, ctx)
    v = verify(_cart(m, ag), m, ctx)
    out.append(AttackResult("A3", "Mandate replay", "C5_nonce_freshness",
                            not v.accepted, v.failed))

    # A4 cumulative aggregation across individually in-scope carts.
    # The mandate is re-presented legitimately: a fresh nonce, re-signed by the
    # principal, so C5 and C10 both pass and only the cumulative cap can stop
    # it. Each cart on its own is well inside every scope check.
    m, principal, ag, ctx = fresh()
    caught_at = None
    for i in range(5):
        m.nonce = new_nonce()
        m.sign(principal)
        v = settle(_cart(m, ag, amount=4000), m, ctx)
        if not v.accepted:
            caught_at = i + 1
            break
    out.append(AttackResult("A4", "Cumulative aggregation across in-scope carts",
                            "C6_cumulative_cap", caught_at is not None,
                            v.failed, f"blocked at cart {caught_at}"))

    # A5 expired mandate reuse
    m, principal, ag, ctx = fresh()
    ctx.now = m.valid_until + timedelta(days=1)
    v = verify(_cart(m, ag), m, ctx)
    out.append(AttackResult("A5", "Expired mandate reuse", "C4_temporal_validity",
                            not v.accepted, v.failed))

    # A6 forged agent attestation
    m, _, _, ctx = fresh()
    rogue = SigningKey.generate()
    v = verify(_cart(m, rogue), m, ctx)
    out.append(AttackResult("A6", "Forged agent attestation", "C7_agent_binding",
                            not v.accepted, v.failed))

    # A7 line-item substitution after user confirmation. The substitution is
    # re-attested by the agent, so the attestation is valid and only the
    # binding between what the user confirmed and what is in the cart can
    # catch it.
    m, _, ag, ctx = fresh()
    c = _cart(m, ag, confirm="h_user_saw", items="h_user_saw")
    c.line_items_hash = "h_swapped_after_confirmation"
    c.attest(ag)
    v = verify(c, m, ctx)
    out.append(AttackResult("A7", "Line-item substitution post-confirmation",
                            "C8_confirmation_bind", not v.accepted, v.failed))

    # A8 post-revocation burst
    m, _, ag, ctx = fresh()
    ctx.directory.revoke(m.mandate_id, now - timedelta(minutes=1))
    v = verify(_cart(m, ag), m, ctx)
    out.append(AttackResult("A8", "Post-revocation burst", "C9_revocation_state",
                            not v.accepted, v.failed))

    # A9 in-scope malicious purchase -- NOT CAUGHT, by construction
    m, _, ag, ctx = fresh()
    v = verify(_cart(m, ag, amount=4999), m, ctx)
    out.append(AttackResult(
        "A9", "In-scope malicious purchase", None, not v.accepted, v.failed,
        "passes every check; loss bounded at the mandate cap, not detected"))

    # A10 prompt-injected but in-scope purchase -- NOT CAUGHT, by construction
    m, _, ag, ctx = fresh()
    v = verify(_cart(m, ag, amount=4850, merchant="merch:sportsdepot"), m, ctx)
    out.append(AttackResult(
        "A10", "Prompt-injected but in-scope purchase", None, not v.accepted,
        v.failed,
        "the injection changes what is bought, not whether it conforms"))

    return out


def false_positive_check(n: int = 20000, seed: int = 0) -> dict:
    """Legitimate, in-scope carts must never be rejected.

    Deterministic checks are only worth anything if their false-positive rate
    on conforming traffic is exactly zero. This measures it rather than
    asserting it.
    """
    rng = np.random.default_rng(seed)
    now = datetime.now(timezone.utc)
    rejected = 0
    for _ in range(n):
        m, _, ag, directory = demo_scenario(now)
        ctx = VerificationContext(now=now, directory=directory)
        amount = int(rng.integers(100, m.max_amount + 1))
        mcc = str(rng.choice(m.allowed_mcc))
        merch = str(rng.choice(m.allowed_merchants))
        v = verify(_cart(m, ag, amount=amount, mcc=mcc, merchant=merch), m, ctx)
        rejected += (not v.accepted)
    return {"n": n, "rejected": rejected, "false_positive_rate": rejected / n}


def bounded_loss(n: int = 20000, seed: int = 0, cap: int = 5000,
                 cumulative_cap: int = 12000) -> dict:
    """Expected loss from A9/A10 with and without mandate enforcement.

    Without enforcement the compromised agent spends what it wants, drawn from
    the same heavy-tailed case-loss distribution calibrated against the
    RBI-cited figures. With enforcement it can still spend - it simply cannot
    exceed the cap it was given, or the cumulative cap across carts.
    """
    from ..fraud import CASE_LOSS_MU, CASE_LOSS_SIGMA
    rng = np.random.default_rng(seed)
    desired = rng.lognormal(CASE_LOSS_MU, CASE_LOSS_SIGMA, n)
    enforced = np.minimum(desired, cap)
    # a persistent attacker issues repeated in-scope carts until the cumulative
    # cap stops it
    enforced_persistent = np.minimum(desired, cumulative_cap)
    return {
        "n": n, "cap": cap, "cumulative_cap": cumulative_cap,
        "mean_loss_unenforced": float(desired.mean()),
        "mean_loss_single_cart": float(enforced.mean()),
        "mean_loss_persistent": float(enforced_persistent.mean()),
        "reduction_single_cart": float(1 - enforced.mean() / desired.mean()),
        "reduction_persistent": float(1 - enforced_persistent.mean() / desired.mean()),
        "p95_unenforced": float(np.quantile(desired, 0.95)),
        "p95_persistent": float(np.quantile(enforced_persistent, 0.95)),
    }
