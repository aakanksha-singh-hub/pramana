# Model card

## Model

LightGBM gradient-boosted trees (`lightgbm==4.5.0`), binary objective, raw
probability output. One model class for every arm; the arms differ only in
which feature groups they are given.

## Arms

| arm | feature groups | features |
| --- | --- | ---: |
| `B1` | transaction | 13 |
| `B1+B2` | + payer session | 24 |
| **`B1+B2+B3`** | **+ beneficiary** — the baseline | **37** |
| `B1+B2+B3+B4a` | + declared purpose code | 38 |
| `B1+B2+B3+B4b` | + purpose + conditional consistency residuals | 53 |

## Hyperparameter selection — the whole budget went to the baseline

24-candidate random search under 5-fold `GroupKFold` on `payer_id`, scored by
mean PR-AUC, fitted on 450,000 training rows of the base configuration
(rho = 0.4, lambda = 0.10, K = 11, beta = 0.5, seed = 0), using **the
B1+B2+B3 feature set alone**.

Selected (`config/frozen_params.json`, with the full 24-trial log):

```json
{"n_estimators": 600, "learning_rate": 0.03, "num_leaves": 255,
 "min_child_samples": 150, "colsample_bytree": 0.6, "subsample": 0.85,
 "subsample_freq": 1, "reg_lambda": 0.0, "max_depth": -1}
```

Best baseline CV PR-AUC 0.94991 +/- 0.00358.

These parameters are then **frozen and reused verbatim for every arm**,
including both B4 variants, in every cell of the sweep. The arms containing
declared context received no search of their own. This is deliberate: if the
challenger still adds measurable value under parameters chosen to suit the
incumbent, the comparison cannot be called a strawman.

## Splits

Two constraints simultaneously, as pre-registered:

- **Grouped.** A payer appears on exactly one side. 30% of payers are held
  out. This stops the model memorising individuals.
- **Temporal.** Training is months 1–9, test is months 10–12. This stops it
  learning from the future.

Base configuration: ~1.04M training rows / 17,500 payers, ~167k test rows /
7,500 payers, ~1,390 test fraud transactions at a 0.72% test fraud rate.

Class balance is **never** rebalanced. No resampling, no `scale_pos_weight`,
no `is_unbalance`.

## The B4b consistency model

Fitted independently inside every cell, on that cell's training split.

1. Take training rows with `is_fraud == 0`.
2. Fit a `QuantileTransformer` (normal output) on their B3 block.
3. Per declared-purpose class with at least 400 rows, estimate a mean and a
   Ledoit-Wolf shrunk covariance on the transformed block. Rarer classes fall
   back to a global legitimate reference.
4. At scoring time emit a Mahalanobis distance, a Gaussian log-likelihood, and
   13 per-feature standardised residuals.

The label is used in exactly one place — step 1, to exclude known fraud from
the reference set — which is what a bank does in production when it builds a
profile from confirmed-good history. It is never a target, never enters the
transform, and is never touched at test time. Every moment and the transformer
itself are fitted on training data alone and then frozen, so no test row
influences its own residual.

`beta` beneficiary noise is applied **before** the consistency model is
fitted, so B4b never sees a cleaner view of the beneficiary than the B3 arm it
is being compared against.

Two hygiene tests enforce this. One permutes the B3 values of the fraud rows
the model excludes and asserts every residual is bit-identical. The other
asserts that scoring a test set leaves the fitted reference unchanged.

## Evaluation

Both pre-registered metric families, neither pre-selected as the headline:

- recall at FPR = 0.1%, 0.5%, 1.0%
- FPR at recall = 50%, 70%, 90%

Secondary: PR-AUC, ROC-AUC, value-weighted detection rate at each FPR.

**Bootstrap.** 1000 resamples, clustered on test **payers** rather than rows,
because a payer's transactions are correlated and row-level resampling would
understate the variance of everything reported. The same resample weights are
shared across all arms, which is what makes the *paired* delta CI tight enough
to resolve a small effect. Deltas are signed so that positive always means
declared context helped.

## Saturation

At the base configuration, recall at 0.5% and 1.0% FPR is at or near 1.0 for
the B4 arms, so those two operating points carry little information. Recall at
0.1% FPR and FPR at fixed recall are the points with headroom. The operating
points were **not** changed after seeing results; the saturation is reported
instead. See `docs/LIMITATIONS.md` §2.

## Intended use

Research artefact. Not a fraud model, not deployable, and not calibrated
against any real population. It exists to compare feature groups against each
other under controlled adversarial pressure, and its outputs are meaningful
only as differences between arms within the same cell.
