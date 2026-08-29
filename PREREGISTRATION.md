# Pre-registration

Committed: 2026-08-30T02:07:43+05:30 (2026-08-29T20:37:43Z)
Commit: this file was the *sole* content of the first commit in this
repository. Verify with `git log --reverse --stat | head -20`.

NOT MODIFIED AFTER RESULTS WERE OBSERVED.

## Research question

Under what levels of adversarially degraded payment-context
reliability does declared payment context provide incremental
fraud-detection value beyond transaction, behavioural, and
beneficiary intelligence?

## Feature groups (fixed; every feature assigned before any run)

B1 TRANSACTION
  amount, log_amount, hour_of_day, day_of_week, day_of_month,
  channel, is_first_payment_to_payee, payer_txn_count_24h,
  payer_txn_count_7d, payer_amount_sum_24h,
  amount_z_vs_payer_history, amount_over_balance_ratio,
  days_since_payer_last_txn

B2 PAYER SESSION
  session_duration_s, time_on_confirm_screen_s,
  n_amount_edits, n_payee_field_edits, n_app_switches,
  typing_speed_cps, is_new_device, device_age_days,
  paste_used_for_payee, screen_on_time_before_txn_s,
  concurrent_call_active

B3 BENEFICIARY
  payee_account_age_days, payee_unique_inflow_payers_30d,
  payee_inflow_amount_30d, payee_fanout_ratio_24h,
  payee_unique_outflow_payees_30d, payee_reciprocity_flag,
  payer_payee_relationship_months, payer_payee_prior_txn_count,
  payee_report_count, payee_payer_geo_dispersion,
  payee_inflow_amount_cv, payee_inflow_periodicity_score,
  payee_balance_retention_ratio

B4 DECLARED CONTEXT
  purpose_code (categorical)
  Variant a: purpose_code only
  Variant b: purpose_code + conditional consistency residuals
             (Mahalanobis distance and per-feature z-scores of
             the payee's B3 vector under the purpose-conditional
             distribution estimated on TRAINING LEGITIMATE
             PAYMENTS ONLY. Label is never used.)

## Model

LightGBM. Hyperparameters selected by 5-fold CV on the
B1+B2+B3 baseline ONLY, then frozen and reused for all arms.
Baseline receives >= the tuning budget of the full model.

## Splits

Grouped by payer_id (no payer appears in both splits).
Temporal: months 1-9 train, months 10-12 test.

## Primary metrics (both reported; neither pre-selected as headline)

  M1  recall @ FPR = 0.1%, 0.5%, 1.0%
  M2  FPR @ recall = 50%, 70%, 90%

Secondary: PR-AUC, ROC-AUC, value-weighted detection rate.
All with 1000-resample bootstrap 95% CIs.

## Primary sweep

  rho  = coaching effectiveness in {0.0, 0.2, 0.4, 0.6, 0.8, 1.0}

Secondary sweeps

  lambda = structural-overlap rate in {0.0, 0.05, 0.10, 0.20, 0.35}
  K      = purpose cardinality in {3, 6, 11}
  beta   = beneficiary-feature noise sigma in {0.0, 0.5, 1.0}

3 seeds per cell.

## Primary reported quantity

rho*, the coaching-effectiveness threshold above which the
incremental value of B4 ceases to be significant
(lower bound of the bootstrap 95% CI on delta crosses zero).

## Falsification condition

If, at lambda >= 0.10 and rho <= 0.2 (the most favourable
realistic regime), the 95% CI on delta for BOTH M1 and M2
includes zero across all seeds, we conclude declared payment
context provides no measurable incremental value in this model
and we report that as the result.

## What we will NOT do

- Report only the best-performing sweep cell.
- Add features to B4 after seeing results.
- Reassign a feature between groups after seeing results.
- Change the operating points after seeing results.

## Parameterisation decisions fixed at pre-registration time

These resolve underspecified points in the design. They are recorded
here, before any data was generated, so that they cannot be tuned later.

1. `lambda` is the *combined population share* of the four legitimate
   high-fan-in payee roles (property_manager, education_institution,
   utility_biller, merchant_small), split among those four in the
   proportions of the base role table. The remaining eight roles are
   renormalised to `1 - lambda`.
2. At `lambda = 0` the purpose taxonomy does NOT shrink. Relationships
   that would have used a lambda-class payee fall back to individual or
   large-merchant payees, so K remains 11 at every lambda and lambda
   varies structural overlap alone.
3. The fidelity scorecard is calibrated against published primary-source
   statistics only. No discriminator-AUC-versus-real-data check is run,
   because no labelled public APP-fraud transaction dataset exists; this
   is recorded as a limitation rather than substituted with a comparison
   against another simulator.
