"""Train/evaluate/bootstrap one cell of the phase study.

The baseline B1+B2+B3 is the arm to beat, and it is the only arm that was ever
tuned. Its hyperparameters were selected by 5-fold grouped CV on the baseline
feature set alone (experiments/00_tune_baseline.py), then frozen and reused
verbatim for every arm including the ones containing B4. If B4 adds value
under those conditions, it is not because the comparison was rigged.
"""

from __future__ import annotations

import gc
import json
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from .features import CATEGORICAL, columns_for
from .features.b3_beneficiary import apply_noise
from .features.b4_context import ConsistencyModel, build_a
from .metrics import METRIC_NAMES, PayerBootstrap, ci, point_metrics
from .purpose import (COACHED_SAFE_SET, collapse, declare_fraud_vec,
                      declare_legit_vec, taxonomy)

ARMS: dict[str, list[str]] = {
    "B1":           ["b1"],
    "B1+B2":        ["b1", "b2"],
    "B1+B2+B3":     ["b1", "b2", "b3"],          # THE BASELINE
    "B1+B2+B3+B4a": ["b1", "b2", "b3", "b4a"],
    "B1+B2+B3+B4b": ["b1", "b2", "b3", "b4b"],
}
BASELINE = "B1+B2+B3"

PARAMS_PATH = Path("config/frozen_params.json")

#: Used only until the tuning run writes config/frozen_params.json.
_FALLBACK_PARAMS = {
    "n_estimators": 400, "learning_rate": 0.05, "num_leaves": 63,
    "min_child_samples": 60, "colsample_bytree": 0.8, "subsample": 0.8,
    "subsample_freq": 1, "reg_lambda": 1.0, "max_depth": -1,
}


def frozen_params() -> dict:
    if PARAMS_PATH.exists():
        return json.loads(PARAMS_PATH.read_text())["params"]
    return dict(_FALLBACK_PARAMS)


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------


def temporal_group_split(df: pd.DataFrame, cfg: dict, seed: int = 0,
                         test_payer_frac: float = 0.30):
    """Grouped by payer *and* separated in time, as pre-registered.

    A payer appears in exactly one side, and the test side is restricted to
    months 10-12. Both constraints matter: the group constraint stops the
    model memorising individual payers, the temporal one stops it learning
    from the future.
    """
    rng = np.random.default_rng(90_001 + seed)
    payers = np.unique(df["payer_id"].to_numpy())
    test_payers = set(rng.choice(payers, size=int(len(payers) * test_payer_frac),
                                 replace=False).tolist())
    in_test = df["payer_id"].isin(test_payers).to_numpy()
    m = df["month"].to_numpy()
    tr_m = np.isin(m, cfg["split"]["train_months"])
    te_m = np.isin(m, cfg["split"]["test_months"])
    return df.loc[~in_test & tr_m].copy(), df.loc[in_test & te_m].copy()


# ---------------------------------------------------------------------------
# Per-cell construction
# ---------------------------------------------------------------------------


def declare_purposes(df: pd.DataFrame, rho: float, K: int, lam: float,
                     seed: int, adversary: str = "uniform") -> np.ndarray:
    """Attach a declared purpose to every payment.

    The legitimate declarations are drawn from a stream seeded only by
    (lambda, seed), so they are *identical* across every rho in the sweep. Only
    the fraudulent declarations move with rho. Without this, each cell would
    carry an independent draw of legitimate mislabelling noise and the phase
    surface would be dominated by that variance rather than by coaching.
    """
    legit_rng = np.random.default_rng((hash((round(lam, 6), seed)) & 0xFFFFFFFF) ^ 0xA11CE)
    fraud_rng = np.random.default_rng(
        (hash((round(lam, 6), seed, round(rho, 6))) & 0xFFFFFFFF) ^ 0xF00D)

    is_fraud = df["is_fraud"].to_numpy() == 1
    declared = np.empty(len(df), dtype=object)
    declared[~is_fraud] = declare_legit_vec(
        df["true_purpose"].to_numpy()[~is_fraud], legit_rng)

    safe_weights = None
    if adversary == "prevalence":
        # frequencies of the safe purposes among legitimate declarations, so
        # that a coached declaration is indistinguishable from a legitimate one
        # on its marginal distribution alone
        vals, counts = np.unique(declared[~is_fraud], return_counts=True)
        freq = dict(zip(vals.tolist(), counts.tolist()))
        safe_weights = np.array([freq.get(p, 1) for p in COACHED_SAFE_SET], dtype=float)
    elif adversary != "uniform":
        raise ValueError(f"unknown adversary {adversary!r}")

    declared[is_fraud] = declare_fraud_vec(
        df["scam_type"].to_numpy()[is_fraud], rho, fraud_rng, safe_weights)
    return collapse(declared, K)


def prepare_cell(base: pd.DataFrame, cfg: dict, rho: float, lam: float, K: int,
                 beta: float, seed: int, adversary: str = "uniform") -> pd.DataFrame:
    """Apply the three cell-level parameters to a cached base ledger.

    Beneficiary noise is applied *before* anything else reads B3, so the
    consistency model in B4b sees exactly the degraded beneficiary view that
    the B3 arm sees. B4b is never handed a cleaner beneficiary signal than the
    baseline it is being compared against.
    """
    from .features import B1_COLS, B2_COLS, B3_COLS

    noise_rng = np.random.default_rng(
        (hash((round(lam, 6), seed, round(beta, 6))) & 0xFFFFFFFF) ^ 0xB3B3)
    purpose = declare_purposes(base, rho, K, lam, seed, adversary)

    # Assemble once from column references rather than copying the whole base
    # frame and mutating it. On a two-million-row ledger the difference is
    # roughly 300 MB per worker, which is what decides whether a parallel sweep
    # runs or thrashes.
    keep = ["txn_id", "payer_id", "payee_id", "day", "month", "amount",
            "is_fraud", "payee_role", "payee_legit", "scam_type", "true_purpose"]
    parts = {c: base[c] for c in keep}
    for c in B1_COLS + B2_COLS:
        parts[c] = base[c]
    noisy = apply_noise(base[B3_COLS], beta, noise_rng)
    for c in B3_COLS:
        parts[c] = noisy[c]
    parts["purpose_code"] = pd.Categorical(purpose, categories=taxonomy(K))
    df = pd.DataFrame(parts, copy=False)
    del noisy, parts
    gc.collect()
    return df


def _as_model_frame(df: pd.DataFrame, cols: list[str], cats: dict) -> pd.DataFrame:
    """Model matrix in float32. LightGBM converts to float32 internally anyway,
    so carrying float64 through only doubles peak memory."""
    out = {}
    for c in cols:
        if c in CATEGORICAL:
            out[c] = pd.Categorical(df[c], categories=cats[c])
        else:
            out[c] = df[c].to_numpy(dtype=np.float32, copy=False)
    return pd.DataFrame(out, index=df.index, copy=False)


# ---------------------------------------------------------------------------
# Running a cell
# ---------------------------------------------------------------------------


def run_cell(base: pd.DataFrame, cfg: dict, rho: float, lam: float, K: int,
             beta: float, seed: int, n_boot: int | None = None,
             arms: dict[str, list[str]] | None = None,
             adversary: str = "uniform") -> dict:
    arms = arms or ARMS
    n_boot = n_boot if n_boot is not None else cfg["evaluation"]["bootstrap_n"]
    params = frozen_params()

    df = prepare_cell(base, cfg, rho, lam, K, beta, seed, adversary)
    tr, te = temporal_group_split(df, cfg, seed=seed)

    cats = {"channel": list(base["channel"].cat.categories)
            if hasattr(base["channel"], "cat") else sorted(pd.unique(base["channel"])),
            "purpose_code": taxonomy(K)}

    cm = ConsistencyModel(seed=seed).fit(tr)
    # concat once per split: assigning 15 residual columns one at a time
    # fragments the block manager and silently copies the frame each time
    tr = pd.concat([tr, cm.transform(tr).drop(columns=["purpose_code"])], axis=1)
    te = pd.concat([te, cm.transform(te).drop(columns=["purpose_code"])], axis=1)
    del df
    gc.collect()

    y_tr = tr["is_fraud"].to_numpy()
    y_te = te["is_fraud"].to_numpy()
    amt_te = te["amount"].to_numpy()
    boot = PayerBootstrap(te["payer_id"].to_numpy(), n_boot=n_boot, seed=seed)

    results: dict = {}
    boot_matrices: dict[str, np.ndarray] = {}
    for name, groups in arms.items():
        cols = columns_for(groups)
        X_tr = _as_model_frame(tr, cols, cats)
        X_te = _as_model_frame(te, cols, cats)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = lgb.LGBMClassifier(random_state=seed, n_jobs=1, verbose=-1, **params)
            model.fit(X_tr, y_tr, categorical_feature=[c for c in cols if c in CATEGORICAL])
            score = model.predict_proba(X_te)[:, 1]
        del X_tr, model
        gc.collect()
        results[name] = point_metrics(y_te, score, amt_te)
        M = boot.metrics(y_te, score)
        del X_te
        gc.collect()
        boot_matrices[name] = M
        results[name]["ci"] = {
            nm: list(ci(M[:, j])) for j, nm in enumerate(METRIC_NAMES)}
        results[name]["n_features"] = len(cols)

    # paired deltas against the baseline, on the shared resamples
    base_M = boot_matrices[BASELINE]
    for name in arms:
        if name == BASELINE:
            continue
        D = _improvement(boot_matrices[name], base_M)
        pt = _improvement_point(results[name], results[BASELINE])
        results.setdefault("delta", {})[name] = {
            nm: {"point": pt[j], "ci": list(ci(D[:, j])),
                 "significant": bool(ci(D[:, j])[0] > 0)}
            for j, nm in enumerate(METRIC_NAMES)
        }

    results["_meta"] = {
        "rho": rho, "lam": lam, "K": K, "beta": beta, "seed": seed,
        "adversary": adversary,
        "n_train": int(len(tr)), "n_test": int(len(te)),
        "n_test_fraud": int(y_te.sum()),
        "train_fraud_rate": float(y_tr.mean()),
        "test_fraud_rate": float(y_te.mean()),
        "n_train_payers": int(tr["payer_id"].nunique()),
        "n_test_payers": int(te["payer_id"].nunique()),
        "params": params,
    }
    return results


def _improvement(M_full: np.ndarray, M_base: np.ndarray) -> np.ndarray:
    """Signed so that positive always means "B4 helped".

    Columns 0-2 are recall at fixed FPR, where more is better.
    Columns 3-5 are FPR at fixed recall, where less is better.
    """
    D = np.empty_like(M_full)
    D[:, :3] = M_full[:, :3] - M_base[:, :3]
    D[:, 3:] = M_base[:, 3:] - M_full[:, 3:]
    return D


def _improvement_point(full: dict, base: dict) -> list[float]:
    from .metrics import FPR_POINTS, RECALL_POINTS
    out = [full["recall_at_fpr"][str(f)] - base["recall_at_fpr"][str(f)] for f in FPR_POINTS]
    out += [base["fpr_at_recall"][str(r)] - full["fpr_at_recall"][str(r)] for r in RECALL_POINTS]
    return out
