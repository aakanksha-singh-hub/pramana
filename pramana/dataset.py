"""Assemble and cache the base ledger.

A *base ledger* is everything that does not depend on the sweep parameters
rho, K or beta: the population, the legitimate and fraudulent transaction
streams, session telemetry, and the clean B1/B3 feature blocks. It is
therefore cached per (lambda, seed) and reused across all 36 cells of the
primary surface that share those two values, which is what makes a 108-cell
phase study tractable.

Declared purpose (rho, K), beneficiary noise (beta) and the B4 blocks are
constructed per cell in harness.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from .features import b1_transaction, b2_session, b3_beneficiary
from .fraud import inject_scams
from .ledger import attach_sessions, generate_legit_ledger
from .population import build_population

CACHE_DIR = Path(os.environ.get("PRAMANA_CACHE", "data/cache"))

META_COLS = [
    "txn_id", "payer_id", "payee_id", "day", "month", "amount", "channel",
    "true_purpose", "is_fraud", "scam_type", "coerced",
    "is_first_payment_to_payee", "payer_payee_prior_txn_count",
    "payer_payee_relationship_months", "payee_role", "payee_legit",
]


def _cache_key(cfg: dict, lam: float, seed: int) -> str:
    relevant = {
        "population": cfg["population"], "payer": cfg["payer"],
        "relationships": cfg["relationships"], "amounts": cfg["amounts"],
        "ledger": cfg["ledger"],
        "fraud": {k: v for k, v in cfg["fraud"].items() if k != "rho"},
        "lam": lam, "seed": seed,
    }
    blob = json.dumps(relevant, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _pair_history(df: pd.DataFrame, pop) -> pd.DataFrame:
    """Observed pair history, seeded with the tie's pre-window age.

    A bank's records predate a 12-month observation window, so a five-year-old
    landlord relationship must not look as unfamiliar as a fresh mule in
    month 1. Ad-hoc and fraudulent pairs get no seed, which is correct: they
    genuinely have no prior history.
    """
    df = df.sort_values(["payer_id", "payee_id", "day"], kind="stable").reset_index(drop=True)
    pair = df["payer_id"].to_numpy().astype(np.int64) * (10 ** 7) + df["payee_id"].to_numpy()
    new = np.concatenate([[True], pair[1:] != pair[:-1]])
    starts = np.flatnonzero(new)
    sizes = np.diff(np.concatenate([starts, [len(df)]]))
    within = np.arange(len(df)) - np.repeat(starts, sizes)
    first_day = np.repeat(df["day"].to_numpy()[starts], sizes)

    seed_months = np.zeros(len(df), dtype=np.float64)
    seed_count = np.zeros(len(df), dtype=np.float64)
    if pop.relationships:
        rel = pd.DataFrame({
            "payer_id": [r.payer_id for r in pop.relationships],
            "payee_id": [r.payee_id for r in pop.relationships],
            "start_day": [r.start_day for r in pop.relationships],
            "rate": [r.rate_per_month for r in pop.relationships],
        })
        rel = rel.groupby(["payer_id", "payee_id"], as_index=False).agg(
            start_day=("start_day", "min"), rate=("rate", "sum"))
        rel["pre_months"] = np.clip(-rel["start_day"] / 30.0, 0.0, 24.0)
        m = df[["payer_id", "payee_id"]].merge(rel, on=["payer_id", "payee_id"], how="left")
        seed_months = m["pre_months"].fillna(0.0).to_numpy()
        seed_count = (m["pre_months"].fillna(0.0) * m["rate"].fillna(0.0)).round().to_numpy()

    df["is_first_payment_to_payee"] = ((within == 0) & (seed_count == 0)).astype(np.int8)
    df["payer_payee_prior_txn_count"] = (within + seed_count).astype(np.float32)
    df["payer_payee_relationship_months"] = (
        (df["day"].to_numpy() - first_day) / 30.0 + seed_months).astype(np.float32)
    return df


def build_base(cfg: dict, lam: float, seed: int, use_cache: bool = True) -> pd.DataFrame:
    key = _cache_key(cfg, lam, seed)
    path = CACHE_DIR / f"base_{key}.parquet"
    if use_cache and path.exists():
        return pd.read_parquet(path)

    rng = np.random.default_rng(1_000_003 * seed + 17)
    pop = build_population(cfg, lam, rng)
    legit = generate_legit_ledger(pop, cfg, rng)
    fraud = inject_scams(pop, cfg, len(legit), rng)
    df = pd.concat([legit, fraud], ignore_index=True)

    df = _pair_history(df, pop)
    df = df.sort_values("day", kind="stable").reset_index(drop=True)
    df["txn_id"] = np.arange(len(df), dtype=np.int64)
    df["payee_role"] = pop.payee_role[df["payee_id"].to_numpy()]
    df["payee_legit"] = pop.payee_legit[df["payee_id"].to_numpy()]

    sess = attach_sessions(df, pop, cfg, rng)
    df = pd.concat([df, sess], axis=1)

    balance = np.array([p.balance for p in pop.payers], dtype=np.float64)
    b1 = b1_transaction.build(df, balance)
    b2 = b2_session.build(df)
    b3 = b3_beneficiary.build(df, pop, cfg, rng)

    out = pd.concat([df[META_COLS], b1, b2, b3], axis=1)
    out = out.loc[:, ~out.columns.duplicated()]

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        out.to_parquet(path, index=False, compression="zstd")
        with open(CACHE_DIR / f"pop_{key}.pkl", "wb") as fh:
            pickle.dump({"lam": lam, "seed": seed,
                         "n_payers": len(pop.payers), "n_payees": len(pop.payees)}, fh)
    return out
