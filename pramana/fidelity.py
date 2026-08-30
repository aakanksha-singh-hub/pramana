"""Realism scorecard.

If the population is not credible, the phase diagram is worthless - so this
runs before any result is reported, not after.

The reference values are published primary-source statistics, not another
simulator. A discriminator-AUC check against real transaction data is NOT
run: no labelled public APP-fraud dataset exists, and matching a second
synthetic generator would demonstrate nothing. That omission is recorded here
and in docs/LIMITATIONS.md rather than substituted for.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: Published anchors. Sources are named in docs/DATA_CARD.md; all are primary.
ANCHORS = {
    # RBI, "Exploring Safeguards in Digital Payments to Curb Frauds",
    # 9 April 2026 (proposed, not law), citing NCRP 2025 figures.
    "share_of_cases_above_10k": 0.450,
    "share_of_value_above_10k": 0.985,
    # INR 22,931 crore across 28 lakh reported cases, 2025 (NCRP, cited in the
    # same RBI discussion paper).
    "mean_case_loss_inr": 22931e7 / 28e5,
    "total_reported_loss_inr": 22931e7,
    "total_reported_cases": 28e5,
}


def case_level_asymmetry(df: pd.DataFrame) -> dict:
    """The strongest external-validity check available: does synthetic fraud
    reproduce the published Indian volume-versus-value asymmetry above
    INR 10,000?"""
    f = df[df.is_fraud == 1]
    cases = f.groupby(["payer_id", "payee_id"])["amount"].sum()
    big = cases > 10_000
    obs = {
        "n_cases": int(len(cases)),
        "share_of_cases_above_10k": float(big.mean()),
        "share_of_value_above_10k": float(cases[big].sum() / cases.sum()),
        "mean_case_loss_inr": float(cases.mean()),
        "median_case_loss_inr": float(cases.median()),
    }
    out = {"observed": obs, "anchor": {}, "abs_error": {}}
    for k in ("share_of_cases_above_10k", "share_of_value_above_10k",
              "mean_case_loss_inr"):
        out["anchor"][k] = ANCHORS[k]
        out["abs_error"][k] = float(abs(obs[k] - ANCHORS[k]))
    out["rel_error_mean_case"] = float(
        abs(obs["mean_case_loss_inr"] - ANCHORS["mean_case_loss_inr"])
        / ANCHORS["mean_case_loss_inr"])
    return out


def class_balance(df: pd.DataFrame) -> dict:
    f = df.is_fraud == 1
    return {
        "n_transactions": int(len(df)),
        "fraud_share_of_volume": float(f.mean()),
        "fraud_share_of_value": float(df.loc[f, "amount"].sum() / df["amount"].sum()),
        "target_share_of_volume": 0.008,
        "target_share_of_value": 0.06,
        "note": ("Volume is targeted directly. Value share is an emergent "
                 "consequence of the RBI-calibrated case-size distribution and "
                 "the legitimate amount distribution; it is reported, not fitted."),
    }


def amount_distribution(df: pd.DataFrame) -> dict:
    out = {}
    for label, sub in (("legitimate", df[df.is_fraud == 0]), ("fraudulent", df[df.is_fraud == 1])):
        a = sub["amount"].to_numpy(dtype=float)
        out[label] = {
            "n": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)),
            "p90": float(np.quantile(a, 0.90)), "p99": float(np.quantile(a, 0.99)),
            "share_above_10k": float((a > 10_000).mean()),
            "gini": float(_gini(a)),
        }
    return out


def _gini(x: np.ndarray) -> float:
    s = np.sort(x)
    n = s.size
    return float((2 * np.arange(1, n + 1) - n - 1).dot(s) / (n * s.sum()))


def inter_transaction_times(df: pd.DataFrame) -> dict:
    d = df.sort_values(["payer_id", "day"])
    gap = d.groupby("payer_id")["day"].diff().dropna().to_numpy()
    gap = gap[gap > 0]
    return {"n": int(gap.size), "mean_days": float(gap.mean()),
            "median_days": float(np.median(gap)),
            "cv": float(gap.std() / gap.mean()),
            "share_under_1_day": float((gap < 1).mean())}


def degree_distribution(df: pd.DataFrame) -> dict:
    """In-sample payee in-degree, and its log-log tail slope.

    Payment beneficiary in-degree is heavy tailed in every real network. A
    slope near -1.5 to -2.5 on the complementary CDF is the regime reported for
    financial transaction graphs; the point of the check is that the synthetic
    graph is heavy tailed at all, not that it hits a particular exponent.
    """
    deg = df.groupby("payee_id")["payer_id"].nunique().to_numpy()
    deg = np.sort(deg[deg > 0])[::-1]
    k = np.unique(deg)
    k = k[k >= max(2, np.quantile(deg, 0.5))]
    ccdf = np.array([(deg >= x).mean() for x in k])
    ok = ccdf > 0
    slope = float(np.polyfit(np.log(k[ok]), np.log(ccdf[ok]), 1)[0])
    return {"n_payees_active": int(deg.size), "max_in_degree": int(deg.max()),
            "median_in_degree": float(np.median(deg)),
            "p99_in_degree": float(np.quantile(deg, 0.99)),
            "ccdf_loglog_slope": slope,
            "share_of_payees_holding_half_the_volume": float(_top_share(deg))}


def _top_share(deg: np.ndarray) -> float:
    c = np.cumsum(np.sort(deg)[::-1])
    return float((np.searchsorted(c, c[-1] / 2) + 1) / deg.size)


def redundancy(df: pd.DataFrame, cols: list[str]) -> dict:
    """Near-duplicate features inside a group would overstate how much
    independent evidence that group carries. This is the check that caught
    balance-retention being generated as one minus fanout."""
    C = df[cols].corr().abs()
    np.fill_diagonal(C.values, 0.0)
    pairs = (C.stack().sort_values(ascending=False).head(8))
    return {"max_abs_corr": float(C.values.max()),
            "top_pairs": [{"a": a, "b": b, "abs_corr": float(v)}
                          for (a, b), v in pairs.items()]}


def latent_recovery(df: pd.DataFrame) -> dict:
    """Does in-sample observed in-degree track the latent fan-in the payee
    aggregates were drawn from? This is what licenses generating payee-level
    network features from latents rather than counting the simulated panel."""
    obs = df.groupby("payee_id")["payer_id"].nunique()
    lat = df.groupby("payee_id")["payee_unique_inflow_payers_30d"].mean()
    j = pd.concat([obs.rename("obs"), lat.rename("lat")], axis=1).dropna()
    j = j[(j.obs > 0) & (j.lat > 0)]
    return {"n": int(len(j)),
            "spearman": float(j["obs"].corr(j["lat"], method="spearman")),
            "log_pearson": float(np.log(j["obs"]).corr(np.log(j["lat"])))}


def scorecard(df: pd.DataFrame, b3_cols: list[str]) -> dict:
    return {
        "class_balance": class_balance(df),
        "case_level_asymmetry": case_level_asymmetry(df),
        "amount_distribution": amount_distribution(df),
        "inter_transaction_times": inter_transaction_times(df),
        "degree_distribution": degree_distribution(df),
        "b3_redundancy": redundancy(df, b3_cols),
        "latent_recovery": latent_recovery(df),
        "not_run": {
            "discriminator_auc_vs_real_data":
                "No labelled public APP-fraud transaction dataset exists. "
                "Comparing against another synthetic generator would "
                "demonstrate nothing, so this check is omitted rather than "
                "substituted. See docs/LIMITATIONS.md.",
        },
    }
