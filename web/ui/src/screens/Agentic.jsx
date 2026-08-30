import React, { useState } from 'react'
import { useResource, fmt } from '../api'
import { Section, Card, Note, Loading, Missing, Table, Stat } from '../components/ui'

const CHECK_LABEL = {
  C1_amount_scope: 'amount within cap',
  C2_category_scope: 'MCC within allowed set',
  C3_merchant_scope: 'merchant within allowed set',
  C4_temporal_validity: 'inside validity window',
  C5_nonce_freshness: 'nonce fresh',
  C6_cumulative_cap: 'cumulative cap',
  C7_agent_binding: 'agent attestation valid',
  C8_confirmation_bind: 'confirmation binds line items',
  C9_revocation_state: 'not revoked',
  C10_mandate_sig: 'mandate signature valid',
}

export default function Agentic() {
  const { loading, data, error } = useResource('agentic')
  const [frameIdx, setFrameIdx] = useState(0)

  if (loading) return <Loading what="the conformance results" />
  if (error) return <Missing what="The agentic results" how="make agentic" />

  const frame = data.demo_frames[frameIdx]
  const bl = data.bounded_loss
  const fp = data.false_positives_on_in_scope_traffic

  return (
    <div>
      <Section eyebrow="The forward surface"
        title="The same question, with cryptographic rather than probabilistic evidence">
        <p className="text-[13px] text-slate max-w-[820px] leading-relaxed mb-5">
          A human declaration of purpose is probabilistic and possibly deceptive. A signed
          mandate is cryptographic and constraint-bounded. These are not the same claim and
          this project does not blur them — but they are the same underlying question about
          whether a payment matched what the payer intended.
        </p>

        <div className="flex gap-1.5 mb-4">
          {data.demo_frames.map((f, i) => (
            <button key={f.label} onClick={() => setFrameIdx(i)}
              className={`px-3.5 py-1.5 text-[12px] rounded-md border ${frameIdx === i
                ? 'bg-ink text-white border-ink' : 'bg-white border-line hover:border-ink'}`}>
              {f.label === 'violating' ? 'Out-of-scope purchase' : 'In-scope purchase the user did not want'}
            </button>
          ))}
        </div>

        <Card className="p-0 overflow-hidden">
          <div className="grid md:grid-cols-2">
            <div className="p-5 border-r border-line">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-2">Mandate</div>
              <div className="mono leading-relaxed space-y-1">
                <div>max_amount        <span className="font-semibold">₹{frame.mandate.max_amount.toLocaleString('en-IN')}</span></div>
                <div>allowed_mcc       [{frame.mandate.allowed_mcc.join(', ')}]</div>
                <div>allowed_merchants [{(frame.mandate.allowed_merchants || []).join(', ')}]</div>
                <div>max_cumulative    ₹{frame.mandate.max_cumulative.toLocaleString('en-IN')}</div>
                <div>valid_until       {frame.mandate.valid_until.slice(0, 16).replace('T', ' ')}</div>
              </div>
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mt-5 mb-2">Agent attempts</div>
              <div className="mono leading-relaxed">
                <div>amount   <span className="font-semibold">₹{frame.attempt.amount.toLocaleString('en-IN')}</span></div>
                <div>mcc      {frame.attempt.mcc}</div>
                <div>merchant {frame.attempt.merchant_id}</div>
              </div>
            </div>

            <div className={`p-5 ${frame.accepted ? 'bg-[#fdf8ec]' : 'bg-[#fdf3f2]'}`}>
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-2">Verification</div>
              <div className="space-y-[3px] mono">
                {frame.checks.map((c) => (
                  <div key={c.id} className="flex gap-2 items-baseline">
                    <span className={c.passed ? 'text-good' : 'text-bad font-bold'}>{c.passed ? '✓' : '✗'}</span>
                    <span className="w-[42px] shrink-0">{c.id.split('_')[0]}</span>
                    <span className={c.passed ? 'text-slate' : 'text-bad font-medium'}>
                      {CHECK_LABEL[c.id]}
                    </span>
                  </div>
                ))}
              </div>
              <div className={`mt-4 pt-3 border-t text-[14px] font-bold ${frame.accepted ? 'border-[#e8dcc0] text-[#8a6d1f]' : 'border-[#f0d5d3] text-bad'}`}>
                {frame.accepted ? '→ PASSES' : '→ REJECTED'}
              </div>
              <div className="text-[12px] mt-1.5 leading-relaxed">{frame.note}</div>
            </div>
          </div>
        </Card>

        {frameIdx === 1 && (
          <Note tone="warn">
            <strong>This is the honest half of the demonstration.</strong> An agent that spends
            inside the mandate — whether compromised or steered by a prompt injection — passes
            every check. Conformance checking does not detect that. It bounds the loss at the
            cap, and nothing more. Volunteering that limit is what makes the other eight rows
            credible.
          </Note>
        )}
      </Section>

      <Section eyebrow="Coverage" title="Ten attack families against ten deterministic checks">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Stat value={`${data.coverage.caught} / ${data.coverage.total}`} label="Families caught"
                sub="structurally, no model involved" tone="good" />
          <Stat value={fp.false_positive_rate.toFixed(4)} label="False-positive rate"
                sub={`${fp.rejected} of ${fp.n.toLocaleString()} in-scope carts rejected`} tone="good" />
          <Stat value={fmt.inr(bl.mean_loss_unenforced)} label="Mean loss, unenforced"
                sub="RBI-calibrated case-size distribution" tone="bad" />
          <Stat value={fmt.pct(bl.reduction_persistent)} label="Loss reduction, enforced"
                sub={`p95 capped at ${fmt.inr(bl.p95_persistent)}`} tone="accent" />
        </div>

        <Card>
          <Table
            head={['ID', 'Attack family', 'Caught by', 'Outcome']}
            align={['l', 'l', 'l', 'l']}
            rows={data.attacks.map((a) => [
              <span className="mono font-semibold">{a.attack_id}</span>,
              a.name,
              <span className="mono text-[11.5px]">{a.failed_checks.join(', ') || '—'}</span>,
              a.caught
                ? <span className="text-good font-medium">caught</span>
                : <span className="text-bad font-medium">not caught — {a.note}</span>,
            ])}
          />
        </Card>

        <Note>
          A9 and A10 are the most important rows in this table. They are uncaught
          <strong> by construction, not by omission</strong>, and they are the direct answer to
          "AP2 already specifies mandate verification": the contribution here is not the checks,
          it is the measurement of what they do and do not buy under adversarial conditions.
        </Note>
      </Section>

      <Section eyebrow="Bounded loss" title="What enforcement buys on the families it cannot catch">
        <Card>
          <Table
            head={['Scenario', 'Mean loss', 'p95 loss', 'Reduction']}
            align={['l', 'r', 'r', 'r']}
            rows={[
              ['No mandate enforcement', fmt.inr(bl.mean_loss_unenforced), fmt.inr(bl.p95_unenforced), '—'],
              ['Enforced, single cart', fmt.inr(bl.mean_loss_single_cart), fmt.inr(bl.cap), fmt.pct(bl.reduction_single_cart)],
              ['Enforced, persistent attacker', fmt.inr(bl.mean_loss_persistent), fmt.inr(bl.p95_persistent), fmt.pct(bl.reduction_persistent)],
            ]}
          />
          <p className="text-[11.5px] text-slate mt-3 leading-relaxed">
            The attacker's desired spend is drawn from the same lognormal case-size
            distribution calibrated against the RBI-cited figures, so the comparison is against
            a realistic loss profile rather than a convenient one. A persistent attacker issues
            repeated in-scope carts until the cumulative cap stops it.
          </p>
        </Card>
      </Section>
    </div>
  )
}
