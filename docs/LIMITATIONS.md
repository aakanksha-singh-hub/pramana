# Limitations

Stated before the results, not after them.

## 1. There is no labelled public APP-fraud dataset

Every number in this repository comes from a simulator. The declared-purpose
field the project exists to evaluate does not appear in any public transaction
dataset, so no external benchmark exists to validate against.

**Consequence.** No claim is made about absolute detection rates. The results
characterise *relative* behaviour across parameter regimes — how the
incremental value of declared context moves as adversarial coaching and
structural overlap change — not a point estimate anyone should deploy against.

## 2. Absolute performance is higher than any deployed system

The B1+B2+B3 baseline reaches ~0.90 recall at 0.1% FPR on the base
configuration. Real APP-fraud detection is nowhere near this.

Two reasons, both deliberate. Session telemetry (B2) is generated with
P(coercion | scam) = 0.75 and strongly separated duress distributions, because
a weak baseline would have made the comparison a strawman. And beneficiary
intelligence (B3) is generated from clean role latents, degraded only by the
`beta` noise parameter.

**Consequence.** Recall at 0.5% and 1.0% FPR is saturated near 1.0 for the B4
arms, so those two pre-registered operating points carry little information.
Recall at 0.1% FPR and FPR at fixed recall are the operating points with
headroom, and they are reported as such. The operating points themselves were
**not** changed after seeing results — that is on the pre-registered list of
things this project will not do.

## 3. Production systems already capture much of B2 and B3

Session telemetry and beneficiary network intelligence are not novel. Payment
service providers and card networks already build both. The experiment is
therefore not "does fraud detection work" but the narrower and more useful
question of whether a *further* signal earns its collection cost once those
are in place. A bank reading this should assume its own B2/B3 are better than
the simulator's in some dimensions and worse in others.

## 4. The consumer population rate of a purpose field is unverified

ISO 20022 `<Purp><Cd>` exists and travels in `pain.001` and `pacs.008`. What
is *not* established from any primary source available here is how often the
field is populated on consumer-initiated flows, or whether it survives
end-to-end rather than being discarded at a gateway. The feasibility argument
in the write-up depends on retention, and that dependency is a real one.

## 5. Results are conditional on the generative model

`rho*` is a property of this simulator under this threat model and this
parameterisation. It is **not** a universal threshold. Every reported figure
should be read with that conditioning attached, and the write-up phrases it
that way throughout. The generative process is published in full precisely so
the partition can be challenged.

## 6. The `rho` mechanism is one adversary among many

The pre-registered adversary draws coached declarations uniformly from a
three-purpose safe set. Because legitimate "investment" is rare, that leaves a
base-rate trace, and declared context retains measurable value even at
rho = 1. A stronger adversary — one who samples the safe set in proportion to
legitimate frequencies, making the declared code marginally uninformative by
construction — is run as a clearly separated secondary surface. Neither is the
worst case. An adversary who also controls *which* mule receives the payment,
choosing one whose profile matches the declared purpose, is not modelled.

## 7. The agentic module bounds loss; it does not detect intent

Eight of ten attack families are caught deterministically at zero false
positives on in-scope traffic. The remaining two — an in-scope malicious
purchase and a prompt-injected but in-scope purchase — pass every check by
construction. Mandate enforcement bounds the expected loss (91.9% reduction
against the cumulative cap in our parameterisation); it does not identify that
anything is wrong. This limit is reported in the results table rather than
buried, because it is the honest boundary of what conformance checking buys.

## 8. What was changed after the pre-registration

`CHANGELOG.md` records every post-hoc change to the generative model, what was
observed that prompted it, and why it is a correction to realism rather than a
move toward a preferred result. `PREREGISTRATION.md` itself has never been
edited; it was the sole content of the repository's first commit and can be
verified with `git log --reverse --stat`.

## 9. Scope

Synthetic data only. No live-system testing. No operational attack tooling.
The agentic module signs and verifies mandates against a local key directory
and never contacts a payment network, a merchant, or an agent platform.
