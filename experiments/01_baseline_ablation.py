"""Ablation at the base configuration, with payer-clustered bootstrap CIs.

One cell, all five arms, full 1000-resample bootstrap. This is the table that
answers "did you compare against a strawman": B1+B2+B3 is reported with its
own confidence interval, at the hyperparameters selected for it alone.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from pramana.harness import ARMS, BASELINE, run_cell, frozen_params
from pramana.dataset import build_base
from pramana.metrics import METRIC_NAMES

OUT = Path("results/ablation.json")


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    lam = cfg["population"]["lam"]
    rho = cfg["fraud"]["rho"]
    K, beta = cfg["features"]["K"], cfg["features"]["beta"]

    base = build_base(cfg, lam, 0)
    res = run_cell(base, cfg, rho=rho, lam=lam, K=K, beta=beta, seed=0,
                   n_boot=cfg["evaluation"]["bootstrap_n"])
    res["generated"] = datetime.now(timezone.utc).isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))

    m = res["_meta"]
    print(f"rho={rho}  lambda={lam}  K={K}  beta={beta}  seed=0")
    print(f"train {m['n_train']:,} rows / {m['n_train_payers']:,} payers   "
          f"test {m['n_test']:,} rows / {m['n_test_payers']:,} payers / "
          f"{m['n_test_fraud']:,} fraud ({m['test_fraud_rate']:.3%})")
    print(f"hyperparameters selected on {BASELINE} only: {json.dumps(frozen_params())}\n")

    hdr = f"{'arm':<14}{'feat':>5}{'PR-AUC':>9}{'R@FPR .1%':>22}{'FPR@recall 70%':>24}"
    print(hdr)
    print("-" * len(hdr))
    for a in ARMS:
        x = res[a]
        r_lo, r_hi = x["ci"]["recall@fpr=0.001"]
        f_lo, f_hi = x["ci"]["fpr@recall=0.7"]
        print(f"{a:<14}{x['n_features']:>5}{x['pr_auc']:>9.4f}"
              f"{x['recall_at_fpr']['0.001']:>10.4f} [{r_lo:.4f},{r_hi:.4f}]"
              f"{x['fpr_at_recall']['0.7']:>10.5f} [{f_lo:.5f},{f_hi:.5f}]")

    print(f"\npaired delta vs {BASELINE}  (positive = declared context helps)")
    for a, d in res["delta"].items():
        if not a.endswith(("B4a", "B4b")):
            continue
        print(f"  {a}")
        for nm in METRIC_NAMES:
            e = d[nm]
            flag = "significant" if e["significant"] else ""
            print(f"    {nm:<20}{e['point']:>+10.5f}  95% CI "
                  f"[{e['ci'][0]:+.5f}, {e['ci'][1]:+.5f}]  {flag}")
    print(f"\nwritten -> {OUT}")


if __name__ == "__main__":
    main()
