"""The conformance checks are only worth reporting if they are exact: every
family caught by the check it is supposed to exercise, and nothing rejected
that conforms."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from nacl.signing import SigningKey

from pramana.agentic.attacks import _cart, bounded_loss, false_positive_check, run_all
from pramana.agentic.mandate import CartMandate, canonical, demo_scenario
from pramana.agentic.verify import CHECKS, VerificationContext, settle, verify

EXPECTED_UNCAUGHT = {"A9", "A10"}


def _ctx(now=None):
    now = now or datetime.now(timezone.utc)
    m, principal, agent, directory = demo_scenario(now)
    return m, principal, agent, VerificationContext(now=now, directory=directory)


def test_conforming_cart_is_accepted():
    m, _, ag, ctx = _ctx()
    assert verify(_cart(m, ag), m, ctx).accepted


def test_each_family_is_caught_by_its_own_check():
    for r in run_all():
        if r.attack_id in EXPECTED_UNCAUGHT:
            assert not r.caught, f"{r.attack_id} should not be catchable"
            assert r.failed_checks == []
        else:
            assert r.caught, f"{r.attack_id} escaped"
            assert r.expected_catcher in r.failed_checks, (
                f"{r.attack_id} was caught by {r.failed_checks}, "
                f"not by {r.expected_catcher}")


def test_coverage_is_eight_of_ten():
    rs = run_all()
    assert sum(r.caught for r in rs) == 8
    assert {r.attack_id for r in rs if not r.caught} == EXPECTED_UNCAUGHT


def test_zero_false_positives_on_in_scope_traffic():
    assert false_positive_check(2000, seed=3)["false_positive_rate"] == 0.0


def test_verification_is_deterministic():
    m, _, ag, ctx = _ctx()
    c = _cart(m, ag)
    a, b = verify(c, m, ctx), verify(c, m, ctx)
    assert [x["passed"] for x in a.checks] == [x["passed"] for x in b.checks]


def test_tampering_with_any_signed_field_breaks_the_mandate_signature():
    for field, value in [("max_amount", 999999), ("agent_id", "agent:rogue"),
                         ("nonce", "deadbeef")]:
        m, _, ag, ctx = _ctx()
        setattr(m, field, value)
        v = verify(_cart(m, ag), m, ctx)
        assert "C10_mandate_sig" in v.failed, f"tampering with {field} went unnoticed"


def test_settle_burns_the_nonce_and_records_the_spend():
    m, _, ag, ctx = _ctx()
    settle(_cart(m, ag, amount=1500), m, ctx)
    assert ctx.spent[m.mandate_id] == 1500
    assert m.nonce in ctx.seen_nonces
    assert "C5_nonce_freshness" in verify(_cart(m, ag), m, ctx).failed


def test_all_ten_checks_run_on_every_verification():
    m, _, ag, ctx = _ctx()
    v = verify(_cart(m, ag), m, ctx)
    assert [c["id"] for c in v.checks] == [cid for cid, _ in CHECKS]


def test_bounded_loss_reduces_expected_loss():
    bl = bounded_loss(5000, seed=1)
    assert bl["mean_loss_persistent"] < bl["mean_loss_unenforced"]
    assert bl["p95_persistent"] <= bl["cumulative_cap"]
