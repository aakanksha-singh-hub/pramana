# Pramana

*Sanskrit: a valid means of proof.*

Payments can verify that a transaction was authorised without knowing whether
it matched what the payer believed they were paying for. Pramana measures when
adding that context is worth it, and how much adversarial pressure it
survives.

## Research question (frozen before any code was written)

> Under what levels of adversarially degraded payment-context reliability does
> declared payment context provide incremental fraud-detection value beyond
> transaction, behavioural, and beneficiary intelligence?

`PREREGISTRATION.md` was the **sole content of this repository's first
commit**, written before the simulator existed and never edited since. Verify:

```
git log --reverse --stat | head -20
```

## What this is not claiming

- **Not** that structured purpose fields don't exist. ISO 20022 `<Purp><Cd>`
  exists and travels in `pain.001` and `pacs.008`.
- **Not** that banks don't ask purpose. UK banks do, under the Consumer
  Standard of Caution.
- **Not** that purpose is never used in decisions. BIS Nexus guidance notes a
  destination PSP may consider purpose codes.
- **Not** that UPI lacks signed intents. It signs payment-request parameters,
  though not semantic purpose.
- **Not** that AP2 lacks mandate verification. AP2 v0.2 specifies open and
  closed mandates with deterministic conformance checking.
- **Not** that purpose x beneficiary is a novel technique. It is ordinary
  feature engineering.
- **Not** that nobody does this. A global negative cannot be proven. What can
  be said: we found no publicly documented production system that models
  purpose-beneficiary consistency as a standalone feature class.

The contribution is a **framework for deciding when collecting and using
declared payment context is operationally worth it**, with the adversarial
tolerance characterised rather than assumed.

## The experiment

Four feature groups, one model class, one tuning budget — spent entirely on
the baseline.

| group | content |
| --- | --- |
| **B1** transaction | amount, timing, channel, velocity, payer-relative anomaly |
| **B2** payer session | duration, hesitation, edits, app-switching, device |
| **B3** beneficiary | account age, inflow/outflow topology, network position, prior reports |
| **B4** declared context | purpose code (variant a); purpose + conditional consistency residuals (variant b) |

Every feature belongs to **exactly one** group. `pramana/features/__init__.py`
is the authority and `tests/test_feature_hygiene.py` fails the build if any
column appears twice — because if B4 silently re-encoded B3, a measured gain
would only mean "we gave the model beneficiary information twice".

**The baseline gets the advantage.** LightGBM hyperparameters were selected by
24-candidate random search under 5-fold payer-grouped CV **on the B1+B2+B3 arm
alone**, then frozen and reused verbatim for every arm including the ones
containing B4.

**Both metrics are reported, neither pre-selected as the headline.** Recall at
fixed FPR (0.1%, 0.5%, 1%) and FPR at fixed recall (50%, 70%, 90%), all with
1000-resample bootstrap 95% CIs clustered on test *payers*.

## Why B4b cannot leak the label

The consistency residuals are an unsupervised conditional density over
beneficiary features, estimated per purpose class on **training legitimate
rows only**. The label is used in exactly one place — to exclude known fraud
from the reference set — which is what a bank does in production when it
builds a profile from confirmed-good history. It is never a target, never
enters the transform, and is never touched at test time.

And a residual is not a beneficiary feature. It is a *distance between a
beneficiary and a purpose*. A model holding B3 alone cannot compute it (it is
never shown the purpose); a model holding the purpose alone cannot compute it
either (it is never shown the beneficiary). It exists only in the interaction,
which is the hypothesis under test.

## The sweep

| axis | values | role |
| --- | --- | --- |
| `rho` coaching effectiveness | 0.0 … 1.0 | **primary** |
| `lambda` structural overlap | 0.0 … 0.35 | secondary |
| `K` purpose cardinality | 3, 6, 11 | secondary |
| `beta` beneficiary noise | 0.0, 0.5, 1.0 | secondary |
| adversary | uniform (pre-registered), prevalence, beneficiary-matched | secondary |

The adversary axis is a ladder in which each rung adds exactly one capability,
so the surfaces decompose:

| adversary | declaration | beneficiary routing |
| --- | --- | --- |
| `uniform` (pre-registered) | uniform over the coached safe set | random mule |
| `prevalence` | proportional to legitimate frequencies, so the code carries no marginal information at rho = 1 | random mule |
| `matched` | as `prevalence` | mule chosen to fit the declared purpose |

`matched` is assumed to **know the defence** — it scores candidate mules
against the defender's own purpose-conditional reference. It cannot change what
a mule account fundamentally is, and it cannot manufacture pair history with
the victim. See `CHANGELOG.md` for why it was added and why making the
adversary stronger biases the study *against* its own hypothesis.

3 seeds per cell, 282 cells. The reported quantity is **rho\***: the coaching
threshold above which the incremental value of declared context ceases to be
significant. It is a threshold, not a percentage improvement — and it is a
property of *this* threat model and parameterisation, never a universal fact.

## The agentic surface

Same consistency question, different evidential strength. A human declaration
is probabilistic and possibly deceptive; a signed mandate is cryptographic and
constraint-bounded. Ten deterministic checks (Ed25519, scope, nonce
freshness, cumulative cap, confirmation binding, revocation) against ten
attack families.

Eight are caught structurally at **0 / 20,000** false positives on in-scope
traffic. Two are not, by construction: an in-scope malicious purchase and a
prompt-injected but in-scope purchase pass every check. Enforcement bounds the
loss; it does not detect the intent. Those two rows are the most important in
the table.

## Running it

```
uv venv --python 3.12 .venv && uv pip install -r requirements.txt
make test        # 16 hygiene and conformance tests
make tune        # select and freeze baseline hyperparameters
make ablation    # base-configuration table with CIs
make sweep       # 192-cell phase study, 6 workers
make agentic     # conformance coverage and bounded loss
make fidelity    # realism scorecard against primary-source anchors
make figures     # phase diagrams
```

## Documents

- `PREREGISTRATION.md` — frozen, first commit, never edited
- `CHANGELOG.md` — every post-hoc change to the generative model, with cause
- `docs/DATA_CARD.md` — population, calibration, modelling choices
- `docs/MODEL_CARD.md` — model, tuning protocol, evaluation
- `docs/LIMITATIONS.md` — read this before the results

## Rules this project held to

Synthetic data only. No live-system testing. No operational attack tooling.
Primary sources only. If the result is negative, it is reported as the result.

## Licence

MIT.
