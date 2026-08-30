"""Select LightGBM hyperparameters on the BASELINE arm only, then freeze them.

The whole tuning budget goes to B1+B2+B3, the arm the experiment is trying to
beat. The chosen parameters are written to config/frozen_params.json and
reused verbatim for every arm in every cell, including the ones containing
B4. This is the answer to "you compared against a strawman": the strawman got
the search and the challenger got nothing.
"""

from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold

from pramana.dataset import build_base
from pramana.features import CATEGORICAL, columns_for
from pramana.harness import prepare_cell, temporal_group_split

N_CANDIDATES = 24
N_FOLDS = 5
TUNE_ROWS = 450_000
OUT = Path("config/frozen_params.json")


def sample_space(rng: np.random.Generator) -> dict:
    return {
        "n_estimators": int(rng.choice([300, 400, 600, 800])),
        "learning_rate": float(rng.choice([0.03, 0.05, 0.08, 0.12])),
        "num_leaves": int(rng.choice([31, 63, 127, 255])),
        "min_child_samples": int(rng.choice([20, 40, 80, 150])),
        "colsample_bytree": float(rng.choice([0.6, 0.8, 1.0])),
        "subsample": float(rng.choice([0.7, 0.85, 1.0])),
        "subsample_freq": 1,
        "reg_lambda": float(rng.choice([0.0, 1.0, 5.0, 20.0])),
        "max_depth": int(rng.choice([-1, 8, 12])),
    }


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    base = build_base(cfg, cfg["population"]["lam"], 0)
    df = prepare_cell(base, cfg, cfg["fraud"]["rho"], cfg["population"]["lam"],
                      cfg["features"]["K"], cfg["features"]["beta"], 0)
    tr, _ = temporal_group_split(df, cfg, seed=0)

    if len(tr) > TUNE_ROWS:
        tr = tr.sample(n=TUNE_ROWS, random_state=0)
    cols = columns_for(["b1", "b2", "b3"])          # BASELINE ARM ONLY
    X = tr[cols].copy()
    X["channel"] = X["channel"].astype("category")
    y = tr["is_fraud"].to_numpy()
    groups = tr["payer_id"].to_numpy()
    print(f"tuning on {len(X):,} rows, {len(cols)} baseline features, "
          f"{y.mean():.4%} fraud, {len(np.unique(groups)):,} payers", flush=True)

    rng = np.random.default_rng(7)
    gkf = GroupKFold(n_splits=N_FOLDS)
    trials = []
    for i in range(N_CANDIDATES):
        params = sample_space(rng)
        t0 = time.time()
        scores = []
        for tr_i, va_i in gkf.split(X, y, groups):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = lgb.LGBMClassifier(random_state=0, n_jobs=10, verbose=-1, **params)
                m.fit(X.iloc[tr_i], y[tr_i],
                      categorical_feature=[c for c in cols if c in CATEGORICAL])
                p = m.predict_proba(X.iloc[va_i])[:, 1]
            scores.append(average_precision_score(y[va_i], p))
        trial = {"params": params, "pr_auc_mean": float(np.mean(scores)),
                 "pr_auc_std": float(np.std(scores)), "seconds": time.time() - t0}
        trials.append(trial)
        print(f"[{i+1:2d}/{N_CANDIDATES}] PR-AUC {trial['pr_auc_mean']:.5f} "
              f"+/- {trial['pr_auc_std']:.5f}  ({trial['seconds']:.0f}s)  {params}",
              flush=True)

    best = max(trials, key=lambda t: t["pr_auc_mean"])
    OUT.write_text(json.dumps({
        "params": best["params"],
        "selected_on": "B1+B2+B3 (baseline arm only)",
        "criterion": f"mean PR-AUC over {N_FOLDS}-fold GroupKFold on payer_id",
        "n_candidates": N_CANDIDATES,
        "tune_rows": int(len(X)),
        "best_pr_auc_mean": best["pr_auc_mean"],
        "best_pr_auc_std": best["pr_auc_std"],
        "all_trials": trials,
    }, indent=2))
    print(f"\nfrozen -> {OUT}\n{json.dumps(best['params'], indent=2)}")


if __name__ == "__main__":
    main()
