import React, { useState } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip,
         BarChart, Bar, XAxis, YAxis, CartesianGrid, ReferenceLine, Cell } from 'recharts'
import { useResource, fmt } from '../api'
import { Section, Card, Note, Loading, Missing, Table } from '../components/ui'

const BUCKETS = [
  { id: 'helps', label: 'Declared context helped', tone: 'good',
    blurb: 'Fraud the consistency signal moved up the review queue.' },
  { id: 'misleads_missed_fraud', label: 'It pushed fraud down', tone: 'bad',
    blurb: 'Fraud the consistency signal made look more ordinary. A failure case.' },
  { id: 'misleads_false_alarm', label: 'It raised a false alarm', tone: 'bad',
    blurb: 'Legitimate payments the consistency signal moved up the queue. A failure case.' },
  { id: 'confirms', label: 'It changed nothing', tone: 'neutral',
    blurb: 'Ordinary legitimate payments where the signal added no information.' },
]

const SHORT = (c) => c.replace(/^payee_/, '').replace(/^payer_payee_/, 'pair_').replace(/_/g, ' ')

export default function Inspector() {
  const { loading, data, error } = useResource('inspector')
  const [bucket, setBucket] = useState('helps')
  const [idx, setIdx] = useState(0)

  if (loading) return <Loading what="the consistency cases" />
  if (error) return <Missing what="The consistency inspector" how="make inspector" />

  const cases = data.cases.filter((c) => c.bucket === bucket)
  const c = cases[Math.min(idx, cases.length - 1)]
  const meta = BUCKETS.find((b) => b.id === bucket)

  const radar = c ? data.b3_cols.map((k) => ({
    axis: SHORT(k),
    deviation: Math.max(-4, Math.min(4, c.residuals[k])),
  })) : []

  const bars = c ? data.b3_cols
    .map((k) => ({ axis: SHORT(k), z: c.residuals[k] }))
    .sort((a, b) => Math.abs(b.z) - Math.abs(a.z)).slice(0, 8) : []

  return (
    <div>
      <Section eyebrow="Consistency inspector"
        title="Does this beneficiary look like the beneficiaries people normally send this purpose to?">
        <p className="text-[13px] text-slate max-w-[840px] leading-relaxed mb-4">
          The reference distribution is estimated per purpose class on <strong>training
          legitimate payments only</strong>. The label is used in exactly one place — to exclude
          known fraud from the reference set — which is what a bank does when it builds a
          profile from confirmed-good history. Every residual below is a distance between a
          beneficiary and a purpose, not a beneficiary feature.
        </p>

        <div className="flex flex-wrap gap-1.5 mb-2">
          {BUCKETS.map((b) => (
            <button key={b.id} onClick={() => { setBucket(b.id); setIdx(0) }}
              className={`px-3 py-1.5 text-[12px] rounded-md border ${bucket === b.id
                ? (b.tone === 'bad' ? 'bg-bad text-white border-bad'
                  : b.tone === 'good' ? 'bg-good text-white border-good'
                  : 'bg-ink text-white border-ink')
                : 'bg-white border-line hover:border-ink'}`}>
              {b.label}
            </button>
          ))}
        </div>
        <div className="text-[12px] text-slate mb-4">{meta.blurb}</div>

        {!c ? <Card>No cases in this bucket.</Card> : (
          <>
            <div className="flex gap-1.5 mb-3">
              {cases.map((_, i) => (
                <button key={i} onClick={() => setIdx(i)}
                  className={`w-7 h-7 text-[11.5px] rounded border tabular-nums ${idx === i
                    ? 'bg-ink text-white border-ink' : 'bg-white border-line'}`}>{i + 1}</button>
              ))}
            </div>

            <div className="grid md:grid-cols-[1fr_1.15fr] gap-5">
              <Card>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-2">Payment</div>
                <Table
                  head={['Field', 'Value']} align={['l', 'r']}
                  rows={[
                    ['declared purpose', <span className="font-semibold">{c.declared_purpose}</span>],
                    ['amount', fmt.inr(c.amount)],
                    ['channel', c.channel],
                    ['beneficiary role', <span className="mono text-[11.5px]">{c.payee_role}</span>],
                    ['beneficiary is legitimate', c.payee_is_legit ? 'yes' : 'no'],
                    ['ground truth', c.is_fraud
                      ? <span className="text-bad font-semibold">fraud{c.scam_type ? ` · ${c.scam_type}` : ''}</span>
                      : <span className="text-good font-semibold">legitimate</span>],
                    ['reference class size', c.reference_n.toLocaleString() + (c.reference_is_fallback ? ' (global fallback)' : '')],
                    ['Mahalanobis distance', c.consistency_mahalanobis.toFixed(2)],
                  ]}
                />
                <div className="mt-4 pt-3 border-t border-line">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-2">
                    Score, baseline vs + declared context
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                      <div className="text-[19px] font-semibold tabular-nums">{c.score_base.toFixed(4)}</div>
                      <div className="text-[11px] text-slate">B1+B2+B3</div>
                    </div>
                    <div>
                      <div className="text-[19px] font-semibold tabular-nums">{c.score_b4b.toFixed(4)}</div>
                      <div className="text-[11px] text-slate">+ B4b</div>
                    </div>
                    <div>
                      <div className={`text-[19px] font-semibold tabular-nums ${
                        (c.rank_shift > 0) === (c.is_fraud === 1) ? 'text-good' : 'text-bad'}`}>
                        {c.rank_shift >= 0 ? '+' : ''}{(c.rank_shift * 100).toFixed(2)}
                      </div>
                      <div className="text-[11px] text-slate">rank percentile shift</div>
                    </div>
                  </div>
                </div>
              </Card>

              <Card>
                <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-2">
                  Beneficiary deviation from the purpose-conditional legitimate reference
                </div>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={radar} outerRadius="72%">
                    <PolarGrid stroke="#e3e7ed" />
                    <PolarAngleAxis dataKey="axis" tick={{ fontSize: 9 }} />
                    <Radar dataKey="deviation" stroke="#1f4e79" fill="#1f4e79" fillOpacity={0.24} />
                    <Tooltip formatter={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)} σ`}
                             contentStyle={{ fontSize: 12 }} />
                  </RadarChart>
                </ResponsiveContainer>
                <div className="text-[11px] text-slate text-center -mt-2 mb-3">
                  standard deviations from the reference mean; 0 = typical for this purpose
                </div>
                <ResponsiveContainer width="100%" height={170}>
                  <BarChart data={bars} layout="vertical" margin={{ left: 88, right: 12, top: 2, bottom: 2 }}>
                    <CartesianGrid strokeDasharray="2 3" stroke="#eef1f5" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 10 }} />
                    <YAxis type="category" dataKey="axis" tick={{ fontSize: 9.5 }} width={86} />
                    <ReferenceLine x={0} stroke="#9aa3ae" />
                    <Tooltip formatter={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)} σ`}
                             contentStyle={{ fontSize: 12 }} />
                    <Bar dataKey="z" radius={[0, 2, 2, 0]}>
                      {bars.map((b, i) => (
                        <Cell key={i} fill={Math.abs(b.z) > 1.5 ? '#b3261e' : '#1f4e79'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </>
        )}

        <Note tone="warn">
          Two of the four buckets above are failure cases, and they are shown by default rather
          than hidden. A consistency signal that helps on average still moves individual
          decisions in the wrong direction, and a reviewer deciding whether to collect this
          field needs to see both directions.
        </Note>
      </Section>
    </div>
  )
}
