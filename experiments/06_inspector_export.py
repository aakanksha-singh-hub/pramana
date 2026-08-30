"""Worked consistency cases for the inspector screen.

Exports individual test payments with the beneficiary's B3 vector, the
purpose-conditional legitimate reference the consistency model compares it
against, and the scores from the baseline and the B4b arm.

Deliberately includes cases where declared context **misleads**: fraud the
consistency signal pushed down the ranking, and legitimate payments it pushed
up. Showing a failure case is the point.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

from pramana.dataset import build_base
from pramana.features import B3_COLS, CATEGORICAL, columns_for
from pramana.features.b4_context import ConsistencyModel
from pramana.harness import BASELINE, ARMS, frozen_params, prepare_cell, temporal_group_split
from pramana.purpose import taxonomy

OUT = Path("results/inspector.json")
N_PER_BUCKET = 4


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    lam, rho = cfg["population"]["lam"], cfg["fraud"]["rho"]
    K, beta = cfg["features"]["K"], cfg["features"]["beta"]

    base = build_base(cfg, lam, 0)
    df = prepare_cell(base, cfg, rho, lam, K, beta, 0)
    tr, te = temporal_group_split(df, cfg, seed=0)

    cm = ConsistencyModel(seed=0).fit(tr)
    for frame in (tr, te):
        res = cm.transform(frame)
        for c in res.columns:
            if c != "purpose_code":
                frame[c] = res[c]

    cats = {"channel": sorted(pd.unique(df["channel"])), "purpose_code": taxonomy(K)}
    params = frozen_params()
    scores = {}
    for name in (BASELINE, "B1+B2+B3+B4b"):
        cols = columns_for(ARMS[name])
        def frame(d):
            X = d[cols].copy()
            for c in cols:
                if c in CATEGORICAL:
                    X[c] = pd.Categorical(X[c], categories=cats[c])
            return X
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = lgb.LGBMClassifier(random_state=0, n_jobs=10, verbose=-1, **params)
            m.fit(frame(tr), tr["is_fraud"].to_numpy(),
                  categorical_feature=[c for c in cols if c in CATEGORICAL])
            scores[name] = m.predict_proba(frame(te))[:, 1]

    te = te.copy()
    te["score_base"] = scores[BASELINE]
    te["score_b4b"] = scores["B1+B2+B3+B4b"]
    # rank percentile, so "moved up the queue" is comparable across arms
    te["rank_base"] = pd.Series(te["score_base"]).rank(pct=True).to_numpy()
    te["rank_b4b"] = pd.Series(te["score_b4b"]).rank(pct=True).to_numpy()
    te["rank_shift"] = te["rank_b4b"] - te["rank_base"]

    buckets = {
        "helps": te[(te.is_fraud == 1) & (te.rank_base < 0.995)]
                 .nlargest(N_PER_BUCKET, "rank_shift"),
        "misleads_missed_fraud": te[te.is_fraud == 1].nsmallest(N_PER_BUCKET, "rank_shift"),
        "misleads_false_alarm": te[(te.is_fraud == 0)]
                 .nlargest(N_PER_BUCKET, "rank_shift"),
        "confirms": te[(te.is_fraud == 0) & (te.rank_shift.abs() < 0.001)]
                 .nsmallest(N_PER_BUCKET, "score_b4b"),
    }

    refs = {p: cm.reference(p) for p in pd.unique(te["purpose_code"])}
    cases = []
    for bucket, rows in buckets.items():
        for _, r in rows.iterrows():
            ref = refs[r["purpose_code"]]
            cases.append({
                "bucket": bucket,
                "txn_id": int(r["txn_id"]),
                "is_fraud": int(r["is_fraud"]),
                "scam_type": None if pd.isna(r["scam_type"]) else str(r["scam_type"]),
                "declared_purpose": str(r["purpose_code"]),
                "payee_role": str(r["payee_role"]),
                "payee_is_legit": bool(r["payee_legit"]),
                "amount": float(r["amount"]),
                "channel": str(r["channel"]),
                "score_base": float(r["score_base"]),
                "score_b4b": float(r["score_b4b"]),
                "rank_base": float(r["rank_base"]),
                "rank_b4b": float(r["rank_b4b"]),
                "rank_shift": float(r["rank_shift"]),
                "consistency_mahalanobis": float(r["consistency_mahalanobis"]),
                "b3": {c: float(r[c]) for c in B3_COLS},
                "residuals": {c: float(r[f"resid_{c}"]) for c in B3_COLS},
                "reference_n": ref["n"],
                "reference_is_fallback": ref["is_fallback"],
            })

    # population-level context for the radar/bar overlay
    legit_tr = tr[tr.is_fraud == 0]
    dist = {}
    for p in refs:
        sub = legit_tr[legit_tr.purpose_code == p]
        if len(sub) < 50:
            continue
        dist[p] = {c: {"p10": float(sub[c].quantile(0.10)),
                       "p50": float(sub[c].quantile(0.50)),
                       "p90": float(sub[c].quantile(0.90))} for c in B3_COLS}

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "config": {"rho": rho, "lam": lam, "K": K, "beta": beta, "seed": 0},
        "b3_cols": B3_COLS,
        "purpose_reference_distribution": dist,
        "cases": cases,
        "note": ("Buckets are selected by change in ranking percentile between the "
                 "baseline and the B4b arm. 'misleads' buckets are included "
                 "deliberately: they are the cases where declared context made the "
                 "decision worse."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))

    print(f"{len(cases)} cases across {len(buckets)} buckets -> {OUT}")
    for b, rows in buckets.items():
        if len(rows):
            print(f"  {b:<24} n={len(rows)}  mean rank shift "
                  f"{rows['rank_shift'].mean():+.4f}")


if __name__ == "__main__":
    main()
