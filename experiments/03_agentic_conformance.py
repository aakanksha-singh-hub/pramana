"""Deterministic conformance: coverage, false positives, and bounded loss.

Reports three numbers, in this order of importance:
  1. what the checks catch, and at what false-positive rate on in-scope traffic;
  2. what they do NOT catch (A9, A10);
  3. how much the loss from the uncaught families is bounded by anyway.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from pramana.agentic.attacks import bounded_loss, false_positive_check, run_all
from pramana.agentic.mandate import demo_scenario
from pramana.agentic.verify import VerificationContext, verify
from pramana.agentic.attacks import _cart

OUT = Path("results/agentic_conformance.json")


def demo_frames() -> list[dict]:
    """The two panels of the demonstration screen, rendered from real runs."""
    now = datetime.now(timezone.utc)
    frames = []
    for label, kw, note in [
        ("violating", dict(amount=40000, mcc="5691", merchant="merch:luxebags"),
         "Deterministic rejection. Zero false positives on this class."),
        ("in_scope_unwanted", dict(amount=4999),
         "Passes every check. Loss bounded at the mandate cap, not detected."),
    ]:
        m, _, ag, directory = demo_scenario(now)
        ctx = VerificationContext(now=now, directory=directory)
        cart = _cart(m, ag, **kw)
        v = verify(cart, m, ctx)
        frames.append({
            "label": label,
            "mandate": {"max_amount": m.max_amount, "allowed_mcc": m.allowed_mcc,
                        "allowed_merchants": m.allowed_merchants,
                        "valid_until": m.valid_until.isoformat(),
                        "max_cumulative": m.max_cumulative},
            "attempt": {"amount": cart.amount, "mcc": cart.mcc,
                        "merchant_id": cart.merchant_id},
            "accepted": v.accepted, "checks": v.checks, "note": note,
        })
    return frames


def main() -> None:
    results = run_all()
    fp = false_positive_check(20000)
    bl = bounded_loss(50000)
    caught = [r for r in results if r.caught]

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "coverage": {"caught": len(caught), "total": len(results),
                     "uncaught": [r.attack_id for r in results if not r.caught]},
        "false_positives_on_in_scope_traffic": fp,
        "bounded_loss": bl,
        "attacks": [asdict(r) for r in results],
        "demo_frames": demo_frames(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))

    print(f"coverage: {len(caught)}/{len(results)} attack families caught "
          f"deterministically at FPR {fp['false_positive_rate']:.4f} "
          f"({fp['rejected']}/{fp['n']} in-scope carts rejected)")
    print(f"uncaught: {payload['coverage']['uncaught']} - by construction, not by omission")
    print(f"\nbounded loss on the uncaught families:")
    print(f"  unenforced mean loss      INR {bl['mean_loss_unenforced']:>12,.0f}")
    print(f"  single cart, enforced     INR {bl['mean_loss_single_cart']:>12,.0f}"
          f"   ({bl['reduction_single_cart']:.1%} reduction)")
    print(f"  persistent, enforced      INR {bl['mean_loss_persistent']:>12,.0f}"
          f"   ({bl['reduction_persistent']:.1%} reduction)")
    print(f"  p95 unenforced            INR {bl['p95_unenforced']:>12,.0f}")
    print(f"  p95 persistent enforced   INR {bl['p95_persistent']:>12,.0f}")
    print(f"\nwritten -> {OUT}")


if __name__ == "__main__":
    main()
