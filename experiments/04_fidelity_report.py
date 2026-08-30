"""Fidelity scorecard for the base population."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from pramana.dataset import build_base
from pramana.features import B3_COLS
from pramana.fidelity import scorecard

OUT = Path("results/fidelity.json")


def main() -> None:
    cfg = yaml.safe_load(open("config/base.yaml"))
    lam = cfg["population"]["lam"]
    df = build_base(cfg, lam, 0)
    sc = scorecard(df, B3_COLS)
    sc["generated"] = datetime.now(timezone.utc).isoformat()
    sc["config"] = {"lam": lam, "seed": 0,
                    "n_payers": cfg["population"]["n_payers"],
                    "n_payees": cfg["population"]["n_payees"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sc, indent=2))

    cb, ca = sc["class_balance"], sc["case_level_asymmetry"]
    print(f"transactions {cb['n_transactions']:,}   fraud "
          f"{cb['fraud_share_of_volume']:.4%} of volume / "
          f"{cb['fraud_share_of_value']:.2%} of value "
          f"(targets 0.80% / 6%)")
    print("\ncase-level asymmetry vs RBI-cited figures:")
    for k, v in ca["observed"].items():
        if k in ca["anchor"]:
            print(f"  {k:<28} {v:>12,.4f}   anchor {ca['anchor'][k]:>12,.4f}"
                  f"   |err| {ca['abs_error'][k]:,.4f}")
    print(f"  {'n_cases':<28} {ca['observed']['n_cases']:>12,}")
    dd = sc["degree_distribution"]
    print(f"\npayee in-degree: median {dd['median_in_degree']:.0f}, "
          f"p99 {dd['p99_in_degree']:.0f}, max {dd['max_in_degree']:,}, "
          f"CCDF log-log slope {dd['ccdf_loglog_slope']:.2f}")
    lr = sc["latent_recovery"]
    print(f"latent recovery: spearman {lr['spearman']:.3f} between observed "
          f"in-sample in-degree and generated payee aggregates")
    rd = sc["b3_redundancy"]
    print(f"\nB3 max |correlation| between distinct features: {rd['max_abs_corr']:.3f}")
    for p in rd["top_pairs"][:3]:
        print(f"  {p['a']:<34} {p['b']:<34} {p['abs_corr']:.3f}")
    it = sc["inter_transaction_times"]
    print(f"\ninter-transaction gap: median {it['median_days']:.2f}d, "
          f"mean {it['mean_days']:.2f}d, CV {it['cv']:.2f}, "
          f"{it['share_under_1_day']:.1%} under a day")
    print(f"\nwritten -> {OUT}")


if __name__ == "__main__":
    main()
