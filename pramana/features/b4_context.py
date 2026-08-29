"""B4 - declared payment context.

Variant a is the honest floor: the declared purpose code and nothing else.

Variant b adds *conditional consistency residuals*: how far this beneficiary
sits from the beneficiaries people normally send this purpose to.

Why this cannot leak the label
------------------------------
The reference distribution is an unsupervised conditional density over B3,
estimated per purpose class on TRAINING LEGITIMATE rows only. The label is
used in exactly one place - to exclude known fraud from the reference set -
which is what a bank does in production when it builds a profile from
confirmed-good history. The label is never a target, never enters the
transform, and is never touched at test time. The quantile transform and every
per-class moment are fitted on training data alone and then frozen, so no test
row influences its own residual.

Why this is not B3 again
------------------------
A residual is not a beneficiary feature. It is a distance between a
beneficiary and a purpose. A model holding B3 alone cannot compute it (it is
never shown the purpose); a model holding the purpose alone cannot compute it
either (it is never shown the beneficiary). It exists only in the interaction,
which is precisely the hypothesis under test.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from sklearn.preprocessing import QuantileTransformer

from . import B3_COLS, B4A_COLS, B4B_COLS

#: A purpose class needs at least this many legitimate training rows before it
#: gets its own reference distribution; rarer classes fall back to the global
#: legitimate distribution.
MIN_CLASS_N = 400


class ConsistencyModel:
    """Purpose-conditional reference distribution over beneficiary features."""

    def __init__(self, min_class_n: int = MIN_CLASS_N, seed: int = 0):
        self.min_class_n = min_class_n
        self.seed = seed
        self.qt: QuantileTransformer | None = None
        self.models: dict[str, dict] = {}
        self.global_: dict | None = None
        self.b3_cols: list[str] = list(B3_COLS)

    # -- fitting ------------------------------------------------------------

    def _moments(self, X: np.ndarray) -> dict:
        mu = X.mean(axis=0)
        cov = LedoitWolf(assume_centered=False).fit(X).covariance_
        cov = cov + np.eye(cov.shape[0]) * 1e-6
        prec = np.linalg.inv(cov)
        sign, logdet = np.linalg.slogdet(cov)
        sd = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
        return {"mu": mu, "prec": prec, "logdet": float(logdet), "sd": sd, "n": len(X)}

    def fit(self, train_df: pd.DataFrame, purpose_col: str = "purpose_code") -> "ConsistencyModel":
        legit = train_df.loc[train_df["is_fraud"] == 0]
        if len(legit) == 0:
            raise ValueError("no legitimate training rows to build a reference from")

        self.qt = QuantileTransformer(
            n_quantiles=min(1000, len(legit)), output_distribution="normal",
            subsample=200_000, random_state=self.seed, copy=True,
        )
        Xl = self.qt.fit_transform(legit[self.b3_cols].to_numpy(dtype=np.float64))
        self.global_ = self._moments(Xl)

        purposes = legit[purpose_col].to_numpy()
        for p in pd.unique(purposes):
            m = purposes == p
            if m.sum() < self.min_class_n:
                continue
            self.models[p] = self._moments(Xl[m])
        return self

    # -- scoring ------------------------------------------------------------

    def transform(self, df: pd.DataFrame, purpose_col: str = "purpose_code") -> pd.DataFrame:
        if self.qt is None or self.global_ is None:
            raise RuntimeError("ConsistencyModel.transform called before fit")

        X = self.qt.transform(df[self.b3_cols].to_numpy(dtype=np.float64))
        n, d = X.shape
        maha = np.empty(n, dtype=np.float64)
        loglik = np.empty(n, dtype=np.float64)
        resid = np.empty((n, d), dtype=np.float64)

        purposes = df[purpose_col].to_numpy()
        const = d * np.log(2.0 * np.pi)
        for p in pd.unique(purposes):
            m = np.flatnonzero(purposes == p)
            mm = self.models.get(p, self.global_)
            dev = X[m] - mm["mu"]
            q = np.einsum("ij,jk,ik->i", dev, mm["prec"], dev)
            maha[m] = np.sqrt(np.maximum(q, 0.0))
            loglik[m] = -0.5 * (q + mm["logdet"] + const)
            resid[m] = dev / mm["sd"]

        out = pd.DataFrame(index=df.index)
        out["purpose_code"] = pd.Categorical(purposes)
        out["consistency_mahalanobis"] = maha.astype(np.float32)
        out["consistency_loglik"] = loglik.astype(np.float32)
        for j, c in enumerate(self.b3_cols):
            out[f"resid_{c}"] = resid[:, j].astype(np.float32)
        return out[B4B_COLS]

    # -- introspection for the web prototype --------------------------------

    def reference(self, purpose: str) -> dict:
        """Purpose-conditional reference moments, on the quantile scale."""
        mm = self.models.get(purpose, self.global_)
        return {"mu": mm["mu"].tolist(), "sd": mm["sd"].tolist(),
                "n": int(mm["n"]), "cols": list(self.b3_cols),
                "is_fallback": purpose not in self.models}


def build_a(df: pd.DataFrame, purpose_col: str = "purpose_code") -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["purpose_code"] = pd.Categorical(df[purpose_col])
    return out[B4A_COLS]
