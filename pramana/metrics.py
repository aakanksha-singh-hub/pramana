"""Operating-point metrics and payer-clustered bootstrap.

Both pre-registered metric families are computed from a single weighted ROC
sweep. Bootstrap resampling is over test *payers*, not rows: a payer's
transactions are correlated, and row-level resampling would understate the
variance of every quantity reported here. The same resample weights are
shared across arms, which is what makes the paired delta CI tight enough to
resolve a small effect.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

FPR_POINTS = (0.001, 0.005, 0.01)
RECALL_POINTS = (0.5, 0.7, 0.9)


def _weighted_curve(y_sorted: np.ndarray, w_sorted: np.ndarray):
    tp = np.cumsum(w_sorted * y_sorted)
    fp = np.cumsum(w_sorted * (1.0 - y_sorted))
    P, N = tp[-1], fp[-1]
    if P <= 0 or N <= 0:
        return None, None
    return tp / P, fp / N


def _recall_at_fpr(recall: np.ndarray, fpr: np.ndarray, target: float) -> float:
    i = np.searchsorted(fpr, target, side="right") - 1
    return float(recall[i]) if i >= 0 else 0.0


def _fpr_at_recall(recall: np.ndarray, fpr: np.ndarray, target: float) -> float:
    i = np.searchsorted(recall, target, side="left")
    return float(fpr[i]) if i < len(fpr) else 1.0


def point_metrics(y: np.ndarray, score: np.ndarray, amount: np.ndarray) -> dict:
    order = np.argsort(-score, kind="mergesort")
    ys, ws = y[order].astype(np.float64), np.ones(len(y))
    recall, fpr = _weighted_curve(ys, ws)
    out: dict = {
        "recall_at_fpr": {f"{f}": _recall_at_fpr(recall, fpr, f) for f in FPR_POINTS},
        "fpr_at_recall": {f"{r}": _fpr_at_recall(recall, fpr, r) for r in RECALL_POINTS},
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)),
    }
    # value-weighted detection: share of fraudulent *value* caught at each FPR
    a = amount[order].astype(np.float64)
    v_tp = np.cumsum(a * ys)
    v_fp = np.cumsum(np.ones(len(y)) * (1.0 - ys))
    v_fpr = v_fp / v_fp[-1]
    out["value_weighted_at_fpr"] = {
        f"{f}": float(v_tp[max(np.searchsorted(v_fpr, f, side="right") - 1, 0)] / v_tp[-1])
        for f in FPR_POINTS
    }
    return out


class PayerBootstrap:
    """Pre-drawn payer-clustered resample weights, shared across arms."""

    def __init__(self, payer_ids: np.ndarray, n_boot: int = 1000, seed: int = 0,
                 chunk: int = 25):
        self.codes, self.inverse = np.unique(payer_ids, return_inverse=True)
        self.n_groups = len(self.codes)
        self.n_boot = n_boot
        self.chunk = chunk
        rng = np.random.default_rng(seed)
        self.counts = rng.multinomial(
            self.n_groups, np.full(self.n_groups, 1.0 / self.n_groups), size=n_boot
        ).astype(np.float32)

    def curves(self, y: np.ndarray, score: np.ndarray):
        """Yield (recall, fpr) arrays for each resample, in sorted-score order."""
        order = np.argsort(-score, kind="mergesort")
        ys = y[order].astype(np.float32)
        inv = self.inverse[order]
        for a in range(0, self.n_boot, self.chunk):
            W = self.counts[a:a + self.chunk][:, inv]
            # weights carried as float32 to halve peak memory, but accumulated
            # in float64: an FPR denominator runs to millions and a float32
            # accumulator would lose precision exactly where the operating
            # points are tightest
            tp = np.cumsum(W * ys, axis=1, dtype=np.float64)
            fp = np.cumsum(W * (1.0 - ys), axis=1, dtype=np.float64)
            P, N = tp[:, -1:], fp[:, -1:]
            ok = (P[:, 0] > 0) & (N[:, 0] > 0)
            yield tp / np.maximum(P, 1e-12), fp / np.maximum(N, 1e-12), ok

    def metrics(self, y: np.ndarray, score: np.ndarray) -> np.ndarray:
        """(n_boot, 6) matrix: recall @ 3 FPRs, then FPR @ 3 recalls.

        Both curves are monotone along the sorted-score axis, so the operating
        point is a count rather than a search: the index of the last column at
        or below the FPR target, and the first column at or above the recall
        target.
        """
        rows = []
        for recall, fpr, ok in self.curves(y, score):
            b = recall.shape[0]
            r = np.arange(b)
            m = np.empty((b, 6), dtype=np.float64)
            for j, f in enumerate(FPR_POINTS):
                idx = np.clip((fpr <= f).sum(axis=1) - 1, 0, None)
                m[:, j] = recall[r, idx]
            for j, rec in enumerate(RECALL_POINTS):
                idx = np.clip((recall < rec).sum(axis=1), 0, recall.shape[1] - 1)
                m[:, 3 + j] = fpr[r, idx]
            m[~ok] = np.nan
            rows.append(m)
        return np.vstack(rows)


def ci(samples: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    s = samples[np.isfinite(samples)]
    if s.size == 0:
        return (float("nan"), float("nan"))
    return (float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2)))


METRIC_NAMES = ([f"recall@fpr={f}" for f in FPR_POINTS]
                + [f"fpr@recall={r}" for r in RECALL_POINTS])
