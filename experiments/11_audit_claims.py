"""Check every number shown on the site against the artefacts it came from.

A mismatch between a claim on screen and the experiment that produced it is
worse than a weak result, so this runs as a test rather than a review.
"""

from __future__ import annotations

import glob, json, re, sys
from pathlib import Path

SITE = Path("web/site/index.html").read_text()
res = lambda n: json.loads(Path("results", n).read_text())

ok, bad = [], []
def check(claim, shown, actual, tol=0):
    good = abs(shown - actual) <= tol if isinstance(shown, (int, float)) else shown == actual
    (ok if good else bad).append((claim, shown, actual))

def on_site(text):
    return text in SITE

# ---- sources -------------------------------------------------------------
cells   = glob.glob("results/raw/*.json")
tune    = json.loads(Path("config/frozen_params.json").read_text())
abl     = res("ablation.json")
agentic = res("agentic_conformance.json")
fid     = res("fidelity.json")
scorer  = res("scorer.json")
phase   = res("phase_surface.json")
prereg  = Path("PREREGISTRATION.md").read_text()

ARMS = 5
# ---- 1. scale claims -----------------------------------------------------
check("conditions tested = 282", 282, len(cells))
check("models trained = 1,535", 1535, len(cells) * ARMS + tune["n_candidates"] * 5 + ARMS)
check("training payments = 1.04M", 1.04, round(abl["_meta"]["n_train"] / 1e6, 2))
check("test payments = 167,345", 167345, abl["_meta"]["n_test"])
check("attackers = 3", 3, len({k.split("|")[0] for k in phase["metrics"]}))
check("repeats = 3", 3, max(c["n_seeds"] for c in phase["metrics"]["uniform|recall@fpr=0.001"]))
check("simulated payments = 2 million", 2.0, round(fid["class_balance"]["n_transactions"] / 1e6, 1))
check("scam share = 0.8%", 0.8, round(fid["class_balance"]["fraud_share_of_volume"] * 100, 1))

# ---- 2. agentic claims ---------------------------------------------------
fp = agentic["false_positives_on_in_scope_traffic"]
check("attack types blocked = 8 of 10", (8, 10), (agentic["coverage"]["caught"], agentic["coverage"]["total"]))
check("false-alarm trials = 20,000", 20000, fp["n"])
check("false alarms = 0", 0, fp["rejected"])
check("loss reduction = 91.9%", 91.9, round(agentic["bounded_loss"]["reduction_persistent"] * 100, 1))
check("uncaught families = A9, A10", ["A9", "A10"], agentic["coverage"]["uncaught"])

# ---- 3. scorer claims ----------------------------------------------------
n_combos = 1
for v in scorer["shape"]:
    n_combos *= v
check("scored combinations = 8,448", 8448, n_combos)
check("review cut = riskiest 0.5%", 0.995, scorer["review_threshold_pct"])

# ---- 4. the B4a vs B4b claim --------------------------------------------
sys.path.insert(0, ".")
from pramana.sweep import collect
df = collect()
g = df[(df.metric == "recall@fpr=0.001") & (df.K == 11) & (df.beta == 0.5)]
gap = (g[g.arm == "B1+B2+B3+B4b"].delta.mean() - g[g.arm == "B1+B2+B3+B4a"].delta.mean())
check("consistency engine adds +0.0007", 0.0007, round(gap, 4))

# ---- 5. the menu-size claim ---------------------------------------------
k = df[(df.arm == "B1+B2+B3+B4b") & (df.metric == "recall@fpr=0.001")
       & (df.adversary == "uniform") & (df.rho == 0.4) & (df.lam == 0.10) & (df.beta == 0.5)]
k3 = k[k.K == 3]; k6 = k[k.K == 6]
check("K=3 carries no measurable value", False, bool(k3.significant.all()))
check("K=6 works", True, bool(k6.significant.all()))

# ---- 6. pre-registration agreement --------------------------------------
for m, label in [("recall@fpr=0.001", "0.1% of payments"), ("recall@fpr=0.005", "0.5% of payments"),
                 ("recall@fpr=0.01", "1% of payments"), ("fpr@recall=0.5", "catch 50% of fraud"),
                 ("fpr@recall=0.7", "catch 70% of fraud"), ("fpr@recall=0.9", "catch 90% of fraud")]:
    have = all(f"{a}|{m}" in phase["metrics"] for a in ("uniform", "prevalence", "matched"))
    check(f"operating point {m} present on every surface", True, have)
    check(f"operating point {m} offered on the site", True, on_site(label))
check("pre-registration names recall @ 0.1/0.5/1.0", True,
      "recall @ FPR = 0.1%, 0.5%, 1.0%" in prereg)
check("pre-registration names FPR @ 50/70/90", True,
      "FPR @ recall = 50%, 70%, 90%" in prereg)

# ---- 7. figures that are written into the copy by hand ------------------
for phrase in ["1,535", "8,448", "167,345", "+0.0007", "0.33 standard deviations"]:
    check(f"site shows “{phrase}”", True, on_site(phrase))

# ---- 8. figures that must be read from the artefacts, not typed ---------
# Stronger than a literal match: if the value is rendered from results/, it
# cannot drift when the experiment is re-run.
for expr, label in [("D.agentic.coverage.caught", "attack coverage"),
                    ("D.agentic.false_positives_in_scope" if False else
                     "D.agentic.false_positives_on_in_scope_traffic.rejected", "false alarms"),
                    ("D.agentic.bounded_loss.reduction_persistent", "loss reduction"),
                    ("D.meta.prereg_commit", "pre-registration commit")]:
    check(f"{label} is read from results, not hardcoded", True, on_site(expr))
for literal, label in [("8 of 10 attack types", "attack coverage"),
                       ("20,000 simulated legitimate", "false-alarm trials"),
                       ("91.9%", "loss reduction")]:
    check(f"{label} is NOT hardcoded in the copy", False, on_site(literal))

# ---- report --------------------------------------------------------------
print(f"{len(ok)} checks passed, {len(bad)} failed\n")
for c, shown, actual in bad:
    print(f"  MISMATCH  {c}\n            site says {shown!r}, artefacts say {actual!r}")
if not bad:
    for c, shown, _ in ok:
        print(f"  ok  {c}")
sys.exit(1 if bad else 0)
