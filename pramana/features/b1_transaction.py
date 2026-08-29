"""B1 - transaction features.

All velocity and history features are computed strictly from rows that
precede the transaction in time. The payer-sorted key trick below relies on
``day`` never exceeding the payer-id stride, which is asserted.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import B1_COLS

_STRIDE = 1000.0  # > horizon in days, so payer blocks never bleed into each other


def build(df: pd.DataFrame, payer_balance: np.ndarray) -> pd.DataFrame:
    if df["day"].max() >= _STRIDE:
        raise AssertionError("horizon exceeds payer stride; velocity keys would collide")

    order = np.lexsort((df["day"].to_numpy(), df["payer_id"].to_numpy()))
    pid = df["payer_id"].to_numpy()[order]
    day = df["day"].to_numpy().astype(np.float64)[order]
    amt = df["amount"].to_numpy().astype(np.float64)[order]
    key = pid * _STRIDE + day

    n = len(df)
    out = np.empty((n, 6), dtype=np.float64)

    # counts and sums over trailing windows, prior rows only
    for j, win in enumerate((1.0, 7.0)):
        lo = np.searchsorted(key, key - win, side="left")
        out[:, j] = np.arange(n) - lo
        if win == 1.0:
            csum = np.concatenate([[0.0], np.cumsum(amt)])
            out[:, 2] = csum[np.arange(n)] - csum[lo]

    # days since this payer's previous transaction
    new_payer = np.concatenate([[True], pid[1:] != pid[:-1]])
    prev_day = np.concatenate([[np.nan], day[:-1]])
    gap = day - prev_day
    gap[new_payer] = np.nan
    out[:, 3] = gap

    # expanding z-score of log amount against the payer's own prior history
    lamt = np.log1p(amt)
    grp_start = np.flatnonzero(new_payer)
    idx_in_grp = np.arange(n) - np.repeat(grp_start, np.diff(np.concatenate([grp_start, [n]])))
    cs = np.concatenate([[0.0], np.cumsum(lamt)])
    cs2 = np.concatenate([[0.0], np.cumsum(lamt * lamt)])
    base = np.repeat(grp_start, np.diff(np.concatenate([grp_start, [n]])))
    k = idx_in_grp.astype(np.float64)
    s1 = cs[np.arange(n)] - cs[base]
    s2 = cs2[np.arange(n)] - cs2[base]
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = s1 / k
        var = s2 / k - mean * mean
        sd = np.sqrt(np.maximum(var, 0.0))
        z = (lamt - mean) / np.where(sd > 1e-6, sd, np.nan)
    z[k < 3] = np.nan
    out[:, 4] = z
    out[:, 5] = amt / np.maximum(payer_balance[pid], 1.0)

    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n)

    d = df["day"].to_numpy()
    res = pd.DataFrame(index=df.index)
    res["amount"] = df["amount"].astype(np.float32)
    res["log_amount"] = np.log1p(df["amount"]).astype(np.float32)
    res["hour_of_day"] = ((d % 1.0) * 24.0).astype(np.float32)
    res["day_of_week"] = (np.floor(d).astype(np.int64) % 7).astype(np.int8)
    res["day_of_month"] = (np.floor(d).astype(np.int64) % 30 + 1).astype(np.int8)
    res["channel"] = df["channel"].astype("category")
    res["is_first_payment_to_payee"] = df["is_first_payment_to_payee"].astype(np.int8)
    res["payer_txn_count_24h"] = out[inv, 0].astype(np.float32)
    res["payer_txn_count_7d"] = out[inv, 1].astype(np.float32)
    res["payer_amount_sum_24h"] = out[inv, 2].astype(np.float32)
    res["days_since_payer_last_txn"] = out[inv, 3].astype(np.float32)
    res["amount_z_vs_payer_history"] = out[inv, 4].astype(np.float32)
    res["amount_over_balance_ratio"] = out[inv, 5].astype(np.float32)
    return res[B1_COLS]
