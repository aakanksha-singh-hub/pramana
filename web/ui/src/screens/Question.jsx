import React from 'react'
import { useResource, fmt } from '../api'
import { Section, Card, Stat, Note, Table } from '../components/ui'

export default function Question({ onNavigate }) {
  const fid = useResource('fidelity')

  return (
    <div>
      <Section eyebrow="The problem, today, in India">
        <h1 className="text-[27px] font-bold leading-[1.25] max-w-[820px] mb-5">
          A payment rail can prove you authorised a transfer. It cannot prove you
          understood what you were paying for.
        </h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Stat value="₹22,931 cr" label="Reported to NCRP in 2025" sub="cited in the RBI discussion paper" />
          <Stat value="28 lakh" label="Reported cases" sub="mean case loss ₹81,896" />
          <Stat value="~45%" label="Of cases above ₹10,000" sub="by volume" />
          <Stat value="~98.5%" label="Of value above ₹10,000" sub="by value" tone="accent" />
        </div>
        <Note>
          The RBI published <em>Exploring Safeguards in Digital Payments to Curb Frauds</em> on
          9 April 2026, proposing four controls — a one-hour lag above ₹10,000, trusted-person
          authentication, a ₹25 lakh credit cap, and a kill switch. Comments closed 8 May 2026.
          These are <strong>proposed, not law</strong>. None of them is a detection improvement.
        </Note>
      </Section>

      <Section eyebrow="The research question" title="Frozen before any code was written">
        <Card className="border-l-[3px] border-l-accent">
          <p className="text-[15px] leading-relaxed">
            Under what levels of adversarially degraded payment-context reliability does
            declared payment context provide incremental fraud-detection value beyond
            transaction, behavioural, and beneficiary intelligence?
          </p>
        </Card>
        <p className="text-[12.5px] text-slate mt-3 leading-relaxed">
          The pre-registration was the <strong>sole content of this repository's first commit</strong>,
          written before the simulator existed and never edited since. It fixes the feature groups,
          both metric families, the operating points, the sweep grid, and — critically — the
          condition under which we would conclude the signal does not work.
        </p>
      </Section>

      <Section eyebrow="The design" title="Four feature groups, one model class, one tuning budget">
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <Table
              head={['Group', 'Content', 'n']}
              align={['l', 'l', 'r']}
              rows={[
                ['B1 transaction', 'amount, timing, channel, velocity', '13'],
                ['B2 payer session', 'duration, hesitation, edits, device', '11'],
                ['B3 beneficiary', 'age, topology, network position, reports', '13'],
                ['B4 declared context', 'purpose code; + consistency residuals', '1 / 16'],
              ]}
            />
          </Card>
          <div className="space-y-3">
            <Note tone="good">
              <strong>The baseline gets the advantage.</strong> Hyperparameters were selected by a
              24-candidate search under 5-fold payer-grouped CV on the <em>B1+B2+B3 arm alone</em>,
              then frozen and reused verbatim for every arm including the ones containing B4.
              The incumbent got the search; the challenger got nothing.
            </Note>
            <Note>
              <strong>Every feature belongs to exactly one group.</strong> A build-failing test
              enforces it. If B4 silently re-encoded B3, a measured gain would only mean
              "we gave the model beneficiary information twice".
            </Note>
          </div>
        </div>
      </Section>

      <Section eyebrow="What is not being claimed" title="Stated up front, before the results">
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-2 text-[12.5px] leading-relaxed">
          {[
            ['That structured purpose fields don\'t exist.', 'ISO 20022 <Purp><Cd> exists and travels in pain.001 and pacs.008.'],
            ['That banks don\'t ask purpose.', 'UK banks do, under the Consumer Standard of Caution.'],
            ['That purpose is never used in decisions.', 'BIS Nexus guidance notes a destination PSP may consider purpose codes.'],
            ['That UPI lacks signed intents.', 'It signs payment-request parameters, though not semantic purpose.'],
            ['That AP2 lacks mandate verification.', 'AP2 v0.2 specifies open and closed mandates with deterministic conformance checking.'],
            ['That purpose × beneficiary is novel.', 'It is ordinary feature engineering.'],
          ].map(([a, b], i) => (
            <div key={i} className="flex gap-2 py-1">
              <span className="text-bad font-semibold shrink-0">not</span>
              <div><span className="font-medium">{a}</span> <span className="text-slate">{b}</span></div>
            </div>
          ))}
        </div>
        <Note tone="warn" >
          A global negative cannot be proven, so we do not claim one. What can be said:
          <strong> we found no publicly documented production system that models
          purpose–beneficiary consistency as a standalone feature class.</strong>
        </Note>
      </Section>

      {fid.data && (
        <Section eyebrow="The population" title="Calibrated against primary sources, not another simulator">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat
              value={fmt.num(fid.data.case_level_asymmetry.observed.share_of_cases_above_10k, 4)}
              label="Cases above ₹10,000" sub="anchor 0.450" />
            <Stat
              value={fmt.num(fid.data.case_level_asymmetry.observed.share_of_value_above_10k, 4)}
              label="Value above ₹10,000" sub="anchor 0.985" />
            <Stat
              value={fmt.inr(fid.data.case_level_asymmetry.observed.mean_case_loss_inr)}
              label="Mean case loss" sub="anchor ₹81,896" />
            <Stat
              value={(fid.data.class_balance.n_transactions / 1e6).toFixed(2) + 'M'}
              label="Transactions" sub={`${fmt.pct(fid.data.class_balance.fraud_share_of_volume, 2)} fraud by volume`} />
          </div>
          <p className="text-[12px] text-slate mt-3 leading-relaxed">
            The case-size distribution has two parameters, and they were <em>solved</em> — not
            tuned — against the published mean case loss and the 45% of cases above ₹10,000.
            The residual on the value share is reported, not fitted away.
          </p>
        </Section>
      )}

      <div className="flex gap-3">
        <button onClick={() => onNavigate('phase')}
          className="bg-accent text-white text-[13px] font-medium px-5 py-2.5 rounded-md hover:opacity-90">
          See where the signal pays →
        </button>
        <button onClick={() => onNavigate('agentic')}
          className="border border-line bg-white text-[13px] font-medium px-5 py-2.5 rounded-md hover:border-accent hover:text-accent">
          Skip to the mandate check
        </button>
      </div>
    </div>
  )
}
