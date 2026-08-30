"""Mandate schema, canonical encoding and Ed25519 signing.

The shapes follow AP2 v0.2's open/closed mandate split: an IntentMandate is
the *open* mandate a principal signs to delegate a bounded shopping task, and
a CartMandate is the *closed* mandate binding one specific purchase. Nothing
here claims to have invented conformance checking - AP2 already specifies it.
What this module exists to do is measure what conformance checking buys, and
where it stops buying anything.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

UNSIGNED = ("signature", "agent_attestation")


def canonical(obj: dict, drop: tuple[str, ...] = UNSIGNED) -> bytes:
    """Deterministic byte encoding: the thing that is actually signed."""
    clean = {k: v for k, v in obj.items() if k not in drop}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"),
                      default=str).encode("utf-8")


@dataclass
class IntentMandate:
    """Open mandate: the constraints the principal is willing to be bound by."""

    mandate_id: str
    principal_id: str
    agent_id: str
    max_amount: int
    allowed_mcc: list[str]
    allowed_merchants: list[str] | None
    valid_from: datetime
    valid_until: datetime
    max_cumulative: int
    nonce: str
    signature: bytes = b""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["valid_from"] = self.valid_from.isoformat()
        d["valid_until"] = self.valid_until.isoformat()
        d.pop("signature", None)
        return d

    def sign(self, key: SigningKey) -> "IntentMandate":
        self.signature = key.sign(canonical(self.to_dict())).signature
        return self


@dataclass
class CartMandate:
    """Closed mandate: one specific purchase, bound to a parent intent."""

    cart_id: str
    parent_mandate_id: str
    amount: int
    mcc: str
    merchant_id: str
    line_items_hash: str
    agent_attestation: bytes = b""
    user_confirmation_hash: str | None = None
    signature: bytes = b""

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in UNSIGNED:
            d.pop(k, None)
        return d

    def attest(self, agent_key: SigningKey) -> "CartMandate":
        self.agent_attestation = agent_key.sign(canonical(self.to_dict())).signature
        return self

    def sign(self, key: SigningKey) -> "CartMandate":
        self.signature = key.sign(canonical(self.to_dict())).signature
        return self


@dataclass
class Directory:
    """Key material and revocation state a verifier is assumed to hold."""

    principal_keys: dict[str, VerifyKey] = field(default_factory=dict)
    agent_keys: dict[str, VerifyKey] = field(default_factory=dict)
    revocations: dict[str, datetime] = field(default_factory=dict)

    def revoke(self, mandate_id: str, when: datetime) -> None:
        self.revocations[mandate_id] = when

    def revoked_before(self, now: datetime) -> set[str]:
        return {m for m, t in self.revocations.items() if t <= now}


def verify_sig(signature: bytes, message: bytes, key: VerifyKey | None) -> bool:
    if key is None or not signature:
        return False
    try:
        key.verify(message, signature)
        return True
    except BadSignatureError:
        return False


def new_nonce() -> str:
    return secrets.token_hex(16)


def demo_scenario(now: datetime | None = None):
    """The mandate used in the demonstration: running shoes, under INR 5,000,
    sports retailers, valid seven days."""
    now = now or datetime.now(timezone.utc)
    principal, agent = SigningKey.generate(), SigningKey.generate()
    directory = Directory(principal_keys={"user:aakanksha": principal.verify_key},
                          agent_keys={"agent:shopper-1": agent.verify_key})
    mandate = IntentMandate(
        mandate_id="im_" + secrets.token_hex(6),
        principal_id="user:aakanksha",
        agent_id="agent:shopper-1",
        max_amount=5000,
        allowed_mcc=["5940", "5941"],          # bicycle shops, sporting goods
        allowed_merchants=["merch:runfast", "merch:sportsdepot", "merch:paceworks"],
        valid_from=now - timedelta(minutes=5),
        valid_until=now + timedelta(days=7),
        max_cumulative=12000,
        nonce=new_nonce(),
    ).sign(principal)
    return mandate, principal, agent, directory
