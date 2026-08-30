# Data card — Pramana synthetic payment population

## What this is

A fully synthetic 12-month payment ledger for a population of 25,000 payers
and 20,000 beneficiaries, together with session telemetry, beneficiary
network aggregates, and an injected APP/scam fraud process. No real payment
data, no real accounts, and no live system were used at any point.

Approximately 2.04 million transactions per (lambda, seed) ledger, of which
0.80% are fraudulent by volume and ~5.3% by value.

## Why it is synthetic

There is no labelled public dataset of authorised push-payment fraud. The
declared-purpose field this project exists to evaluate is not present in any
public transaction dataset at all. A simulator is therefore the only way to
ask the research question, and the cost of that choice is stated plainly in
`LIMITATIONS.md`: no claim is made about absolute detection rates.

## Generative structure

Three processes run independently. This is the design decision the whole
experiment rests on.

1. **Beneficiary behaviour is a function of payee role.** Fifteen roles, each
   with latent parameters for account age, inbound fan-in, onward fanout,
   inflow periodicity, geographic dispersion of payers, and balance retention.
2. **The true economic purpose of a payment is a function of the payer-payee
   relationship.** Relationship formation picks a beneficiary role appropriate
   to the purpose. It never inspects fraud status.
3. **Victimisation is a function of an independent scam-campaign process.**
   Victims are drawn from a personal susceptibility latent; the scam type is
   drawn from a campaign mix; the beneficiary is drawn from the mule
   population. Nothing in it reads a payer's relationship portfolio.

The purpose-beneficiary consistency signal that B4 is meant to capture is
therefore *emergent* from the interaction of (1) and (2). It is never planted,
and no generative step conditions purpose on the fraud label.

## Declared purpose

A payer declares a purpose from an 11-class taxonomy. For legitimate
payments the declaration is the true purpose passed through a row-stochastic
confusion matrix (aggregate mislabel rate ~18%): honest confusion from menu
design, haste and category ambiguity, not deception.

For fraudulent payments the declaration is governed by `rho`, coaching
effectiveness. With probability `1 - rho` the victim declares what the scam
narrative told them in good faith. With probability `rho` the attacker steers
the declaration into `{friend_transfer, other, investment}` — purposes whose
legitimate beneficiary profile a mule account does not badly violate.

## The lambda mechanism

`lambda` is the combined population share of seven legitimate roles that
structurally resemble mule accounts:

| role | why it looks like a mule |
| --- | --- |
| `property_manager` | high fan-in from unrelated payers |
| `education_institution` | very high fan-in, seasonal |
| `utility_biller` | enormous fan-in |
| `merchant_small` | high fan-in, moderate fanout, young accounts |
| `settlement_agent` | forwards 88% of inflow within 24h |
| `gig_worker` | young account, sweeps balance out, thin file |
| `chit_fund_collector` | many unrelated payers, sweeps the pot straight out, declared as "investment" |

`chit_fund_collector` is the sharpest case in the population: legitimate,
collecting from many unrelated payers, forwarding the pot to that month's
member, and declared under the same purpose code a coached scammer steers
toward. Without roles like these, beneficiary intelligence alone separates
fraud almost perfectly and the experiment tests nothing. See `CHANGELOG.md`
for the run in which exactly that happened, and what was changed.

At `lambda = 0` these roles are absent and relationships fall back to
individual and large-merchant beneficiaries; the purpose taxonomy stays at
K = 11 so that lambda varies structural overlap alone.

## Amount calibration

Fraud case losses are lognormal with mu = 8.9364, sigma = 2.1803. These two
parameters were *solved*, not tuned, against two published figures: a mean
case loss of INR 22,931 crore / 28 lakh cases = INR 81,896, and the 45% of
cases above INR 10,000 reported in the RBI discussion paper *Exploring
Safeguards in Digital Payments to Curb Frauds* (9 April 2026 — proposed, not
law; comments closed 8 May 2026), citing NCRP 2025 figures.

Achieved on the base population:

| quantity | observed | anchor | error |
| --- | ---: | ---: | ---: |
| share of cases above INR 10,000 | 0.4495 | 0.450 | 0.0005 |
| share of fraud value above INR 10,000 | 0.9791 | 0.985 | 0.0059 |
| mean case loss | INR 80,872 | INR 81,896 | 1.3% |

The residual on the value share is reported rather than fitted away.

## Modelling choices a reviewer should know about

**Payee network aggregates are drawn from latents, not counted off the panel.**
The 25,000 simulated payers are a *sample* of each beneficiary's true inbound
payer base. Counting in-sample in-degree would understate a utility biller by
three orders of magnitude while leaving a mule roughly correct. Aggregates are
therefore drawn per payee-month from the role's latent parameters. The
fidelity scorecard reports a Spearman correlation of 0.658 between in-sample
observed in-degree and the generated aggregates, which is what licenses the
choice. Pair-level features (relationship age, prior transaction count,
reciprocity) *are* counted off the panel.

**`payee_report_count` is strictly as-of-time.** Report timestamps are stored
and searched at the transaction day, never summed ahead of time, so no test
row can see a report filed after it. Reports carry a filing and propagation
lag (gamma, mean ~18 days) and only 35% of victims file. Legitimate
beneficiaries attract spurious disputes at a rate scaled by fan-in, so the
feature is not a perfect label.

**Bank history predates the observation window.** A five-year-old landlord
relationship must not look as unfamiliar as a fresh mule in month 1, so
pair-level history is seeded with the tie's pre-window age. Ad-hoc and
fraudulent pairs get no seed, because they genuinely have none.

**Mule accounts carry cover traffic.** 35% of mule accounts also receive
ordinary legitimate payments — accounts that were a real person's before they
were sold, rented or coerced. 4.65% of legitimate payments land on an account
that is also a mule, so "this payee is a mule" is not equivalent to "this
payment is fraud".

**Session telemetry comes from a duress latent, not the label.**
P(coercion | scam) = 0.75 and P(coercion | legitimate) = 0.02, and
`paste_used_for_payee` and `is_new_device` also depend on payment novelty, so
no single session feature is a clean coercion proxy.

## Fidelity scorecard

Run `make fidelity`. Reference values are published primary-source statistics
only. A discriminator-AUC check against real transaction data is **not** run:
no labelled public APP-fraud dataset exists, and matching a second synthetic
generator would demonstrate nothing. The omission is recorded, not
substituted.

Observed on the base population: payee in-degree CCDF log-log slope -1.56
(heavy tailed), median inter-transaction gap 2.93 days, 21.4% of gaps under a
day, maximum absolute correlation between distinct B3 features 0.834.

## Reproduction

```
make test        # 16 hygiene and conformance tests
make fidelity    # scorecard
```

Every ledger is deterministic given (lambda, seed) and `config/base.yaml`.
