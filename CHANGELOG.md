# Changelog

This file records every change made to the generative model *after* the
pre-registration was committed. `PREREGISTRATION.md` is never edited. Each
entry states what was observed, what was changed, and why the change is a
correction to realism rather than a move toward a preferred result.

---

## 2026-08-30 — Legitimate high-fanout accounts, account openings, and cover traffic

**Observed.** The first end-to-end run at rho=0.4, lambda=0.10, beta=0.5 gave
the B1+B2+B3 baseline PR-AUC 0.9982 and 99.75% recall at 0.1% FPR. The
baseline was saturated, so every cell of the phase study would have read zero
for reasons that had nothing to do with coaching.

**Diagnosed.** `payee_fanout_ratio_24h` alone scored AUC 0.9957. In the role
table as originally specified, every legitimate role had a fanout ratio
between 0.05 and 0.45 and every mule role between 0.85 and 0.92 — the two
sets did not overlap at all. 0.7% of legitimate payments went to a payee
forwarding more than 70% of inflow within 24 hours, against 88.5% of
fraudulent ones. `payee_balance_retention_ratio` was generated as
`1 - fanout`, so it carried the same giveaway a second time. Separately,
2.3% of legitimate payees were under 120 days old against 47.9% of
fraudulent ones, and *every* payment to a mule account was fraudulent, which
made "is this payee a mule" equivalent to the label.

**Changed.**

1. Three legitimate roles with mule-range fanout were added, and joined the
   lambda set: `settlement_agent` (0.88), `gig_worker` (0.80),
   `chit_fund_collector` (0.84). All three exist in real networks —
   aggregators that settle nightly, gig workers who sweep their balance, and
   rotating savings groups that pass the pot straight to the month's member.
2. A 14% account-opening rate was applied to the legitimate roles for which a
   new account is plausible, so that a thin file is not by itself evidence of
   a mule. Institutional roles are excluded: a three-week-old utility biller
   with five thousand inbound payers is not a real object.
3. 35% of mule accounts now also carry ordinary legitimate traffic — accounts
   that were a real person's before they were sold, rented or coerced.
   4.65% of legitimate payments now land on an account that is also a mule.
4. `payee_balance_retention_ratio` is generated from its own per-role process
   instead of as an algebraic transform of fanout.

**Effect.** Top single-feature B3 AUC fell from 0.9957 to 0.9077. The
baseline remains strong (PR-AUC 0.961, recall 0.895 at 0.1% FPR) and is still
given the entire tuning budget.

**Why this is not tuning toward a result.** `PREREGISTRATION.md` defines
lambda as the "structural-overlap rate" without naming which beneficiary
features overlap. Extending it to govern overlap on fanout and account age,
as well as fan-in, specifies that definition rather than changing it. The
changes were made once, before the sweep, on stated realism grounds, and were
not iterated on. No feature was reassigned between groups, no feature was
added to B4, no metric or operating point was altered, and the falsification
condition stands as written.

---

## 2026-08-30 — Beneficiary-matched adversary added as a third surface

**Observed.** With 109 of 192 cells complete, the pre-registered surface had no
zero-crossing anywhere: declared context remained significant at every value of
rho, on every seed, at every lambda, under both the pre-registered adversary
and the prevalence-matched one. rho* — the pre-registered primary reported
quantity — was therefore undefined (`> 1.0`) across the whole grid.

**Diagnosed.** Both modelled adversaries control only what the victim
*declares*. Neither controls *which mule receives the money*. A real scammer
controls both, and would route a payment to an account whose beneficiary
profile is plausible for the purpose the victim has been coached to declare.
That attacks the purpose–beneficiary consistency mechanism directly rather than
merely the base rate of the declared code. It was already recorded in
`docs/LIMITATIONS.md` as an unmodelled adversary before the results were seen.

**Added.** A third adversary, `matched`, forming a ladder in which each rung
adds exactly one capability:

| adversary | declaration | beneficiary routing |
| --- | --- | --- |
| `uniform` (pre-registered) | uniform over the coached safe set | random mule |
| `prevalence` | in proportion to legitimate frequencies, so the code carries no marginal information at rho = 1 | random mule |
| `matched` | as `prevalence` | mule chosen to fit the declared purpose |

The matched adversary is assumed to **know the defence**: it scores candidate
mules against the same purpose-conditional reference the defender uses. That is
a deliberate worst case — the security of a declared-context control should not
depend on the attacker's ignorance of how it works.

Two constraints keep the attack honest. It can only choose among accounts that
are actually mules, so the best available match to an institutional purpose is
still a poor one. And it cannot manufacture pair history: a victim has no prior
relationship with any mule, whichever is chosen, so only the eleven
*payee-level* beneficiary features are swapped and the two *pair-level* ones
are left untouched.

Selection is uniform over the best 5% of available mules for that
purpose-month, with a floor of ten. Taking only the single best match drove
fraud to look *more* typical of its declared purpose than legitimate payments
did (median Mahalanobis 2.89 against a legitimate 3.50), which a defender could
then exploit in reverse. That is an artefact of an omniscient attack model
rather than a property of the control, so it was designed out.

**Effect on the consistency signal**, at rho = 1.0, lambda = 0.10:

| adversary | fraud median Mahalanobis | legit median | fraud above legit p95 |
| --- | ---: | ---: | ---: |
| `uniform` | 4.07 | 3.50 | 14.6% |
| `prevalence` | 4.00 | 3.50 | 12.4% |
| `matched` | 3.01 | 3.50 | 0.3% |

**Why this is not tuning toward a result.** The change makes the adversary
*stronger*, not weaker, and is therefore biased against the hypothesis under
test. It was named as a limitation before any result was seen. The
pre-registered surface is reported unchanged and remains the primary analysis;
this is a third, clearly labelled surface. No feature was reassigned, no metric
or operating point was altered, and the falsification condition stands as
written.
