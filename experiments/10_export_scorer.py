"""Export a live payment scorer.

Trains the two real models - the baseline a bank runs today, and the same
model given the declared-purpose field - then scores a grid of realistic
payments with both and exports the predictions.

The page can then score a payment the visitor builds, using genuine outputs
from the trained model rather than a re-implementation or an approximation.
"""

from __future__ import annotations

import itertools, json, warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

from pramana.dataset import build_base
from pramana.features import B3_COLS, CATEGORICAL, columns_for
from pramana.features.b4_context import ConsistencyModel
from pramana.harness import ARMS, BASELINE, frozen_params, prepare_cell, temporal_group_split
from pramana.purpose import PURPOSES, taxonomy

OUT = Path("results/scorer.json")

# what the visitor can change
GRID = {
    "purpose":  PURPOSES,
    "age":      [15, 120, 400, 1500],          # recipient account age, days
    "payers":   [3, 25, 80, 400],              # distinct payers into it, 30d
    "fanout":   [0.10, 0.50, 0.90],            # share forwarded within 24h
    "amount":   [2000, 15000, 60000, 200000],
    "known":    [1, 0],                        # have you paid them before
    "behave":   [0, 1],                        # 0 calm, 1 hesitant and distracted
}


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    lam, rho = cfg["population"]["lam"], cfg["fraud"]["rho"]
    K, beta = cfg["features"]["K"], cfg["features"]["beta"]

    base = build_base(cfg, lam, 0)
    df = prepare_cell(base, cfg, rho, lam, K, beta, 0)
    tr, te = temporal_group_split(df, cfg, seed=0)

    cm = ConsistencyModel(seed=0).fit(tr)
    tr = pd.concat([tr, cm.transform(tr).drop(columns=["purpose_code"])], axis=1)
    te = pd.concat([te, cm.transform(te).drop(columns=["purpose_code"])], axis=1)

    cats = {"channel": list(base["channel"].cat.categories),
            "purpose_code": taxonomy(K)}
    params = frozen_params()

    models, scores = {}, {}
    for arm in (BASELINE, "B1+B2+B3+B4b"):
        cols = columns_for(ARMS[arm])
        def mk(d):
            out = {}
            for c in cols:
                out[c] = (pd.Categorical(d[c], categories=cats[c]) if c in CATEGORICAL
                          else d[c].to_numpy(dtype=np.float32, copy=False))
            return pd.DataFrame(out, index=d.index, copy=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = lgb.LGBMClassifier(random_state=0, n_jobs=10, verbose=-1, **params)
            m.fit(mk(tr), tr["is_fraud"].to_numpy(),
                  categorical_feature=[c for c in cols if c in CATEGORICAL])
        models[arm] = (m, cols, mk)
        scores[arm] = m.predict_proba(mk(te))[:, 1]
        print(f"trained {arm}: {len(cols)} features", flush=True)

    # Everything the visitor does not control is held at a realistic median.
    # Behaviour is the exception: a bank already sees how the payer acted, and
    # pinning that to "calm" made the baseline model blind to every scenario -
    # its highest probability across the whole grid was 0.0046. The visitor
    # therefore sets it, and the two behavioural profiles are taken from the
    # test set rather than invented.
    from pramana.features import B2_COLS
    tmpl = te[te.is_fraud == 0].median(numeric_only=True)
    calm = te.loc[~te["coerced"].astype(bool), B2_COLS].median(numeric_only=True)
    tense = te.loc[te["coerced"].astype(bool), B2_COLS].median(numeric_only=True)
    combos = list(itertools.product(*GRID.values()))
    G = pd.DataFrame([dict(zip(GRID, c)) for c in combos])
    n = len(G)
    print(f"scoring {n:,} payment combinations", flush=True)

    rows = pd.DataFrame(np.tile(tmpl.values, (n, 1)), columns=tmpl.index)
    for c in te.columns:
        if c not in rows.columns:
            rows[c] = te[c].iloc[0]
    rows["amount"] = G["amount"].values
    rows["log_amount"] = np.log1p(G["amount"].values)
    rows["payee_account_age_days"] = G["age"].values
    rows["payee_unique_inflow_payers_30d"] = G["payers"].values
    rows["payee_fanout_ratio_24h"] = G["fanout"].values
    rows["payee_balance_retention_ratio"] = 1.0 - G["fanout"].values * 0.8
    rows["is_first_payment_to_payee"] = (1 - G["known"]).astype(np.int8).values
    rows["payer_payee_prior_txn_count"] = np.where(G["known"].values == 1, 9.0, 0.0)
    rows["payer_payee_relationship_months"] = np.where(G["known"].values == 1, 14.0, 0.0)
    rows["payee_inflow_amount_30d"] = G["payers"].values * 2400.0
    for c in B2_COLS:
        rows[c] = np.where(G["behave"].values == 1, tense[c], calm[c])
    rows["purpose_code"] = G["purpose"].values
    rows["channel"] = te["channel"].mode()[0]
    rows["is_fraud"] = 0

    res = cm.transform(rows)
    for c in res.columns:
        if c != "purpose_code":
            rows[c] = res[c].values

    out = {}
    for arm in (BASELINE, "B1+B2+B3+B4b"):
        m, cols, mk = models[arm]
        p = m.predict_proba(mk(rows))[:, 1]
        # express as a percentile of the live score distribution: "this payment
        # is riskier than X% of payments", which is what a review queue uses
        ref = np.sort(scores[arm])
        pctile = np.searchsorted(ref, p) / len(ref)
        out[arm] = {"p": np.round(p, 6).tolist(), "pct": np.round(pctile, 5).tolist()}

    payload = {
        "grid": GRID,
        "shape": [len(v) for v in GRID.values()],
        "baseline": out[BASELINE],
        "with_purpose": out["B1+B2+B3+B4b"],
        "note": ("Genuine predictions from the two trained models. Everything not "
                 "listed in the grid is held at the median of a legitimate payment."),
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    thr = float(np.quantile(scores[BASELINE], 0.995))
    payload["review_threshold_pct"] = 0.995
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    b, w = np.array(out[BASELINE]["pct"]), np.array(out["B1+B2+B3+B4b"]["pct"])
    print(f"  rows a bank would review — baseline {(b>=0.995).sum()}, "
          f"with purpose {(w>=0.995).sum()} of {n}")
    print(f"\nwritten -> {OUT}  ({OUT.stat().st_size/1024:.0f} KB)")
    print(f"combinations: {n:,}")
    print(f"purpose field moved the ranking on {(np.abs(w-b)>0.01).mean():.1%} of them")
    print(f"largest upward move: {(w-b).max():+.3f}   largest downward: {(w-b).min():+.3f}")


if __name__ == "__main__":
    main()
