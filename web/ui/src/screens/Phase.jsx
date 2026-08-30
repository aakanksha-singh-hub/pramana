import React, { useState, useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
         LineChart, Line, ErrorBar, Legend } from 'recharts'
import { useResource } from '../api'
import { Section, Card, Note, Loading, Missing, Table, Stat } from '../components/ui'
import Heatmap from '../components/Heatmap'

const METRICS = [
  { id: 'recall@fpr=0.001', label: 'Δ recall @ FPR 0.1%', better: 'higher' },
  { id: 'recall@fpr=0.005', label: 'Δ recall @ FPR 0.5%', better: 'higher' },
  { id: 'recall@fpr=0.01', label: 'Δ recall @ FPR 1%', better: 'higher' },
  { id: 'fpr@recall=0.5', label: 'Δ FPR @ recall 50%', better: 'lower' },
  { id: 'fpr@recall=0.7', label: 'Δ FPR @ recall 70%', better: 'lower' },
  { id: 'fpr@recall=0.9', label: 'Δ FPR @ recall 90%', better: 'lower' },
]

const ADVERSARIES = [
  { id: 'uniform', label: 'Pre-registered adversary', sub: 'uniform over the coached safe set' },
  { id: 'prevalence', label: 'Prevalence-matched (secondary)', sub: 'declared code carries no marginal information at ρ=1' },
]

export default function Phase() {
  const { loading, data, error } = useResource('phase')
  const [metric, setMetric] = useState('recall@fpr=0.001')
  const [adversary, setAdversary] = useState('uniform')

  if (loading) return <Loading what="the phase surface" />
  if (error) return <Missing what="The phase surface" how="make sweep && make figures" />

  const key = `${adversary}|${metric}`
  const cells = data.metrics[key] || []
  const rhoStar = data.rho_star[key] || []
  const available = new Set(Object.keys(data.metrics).map((k) => k.split('|')[0]))
  const digits = metric.startsWith('fpr') ? 5 : 4
  const fmtv = (v) => (v == null || Number.isNaN(v) ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(digits)}`)

  return (
    <div>
      <Section eyebrow="The result"
        title="Where declared payment context pays, and where it does not">
        <div className="flex flex-wrap gap-6 mb-5">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-1.5">Adversary</div>
            <div className="flex gap-1.5">
              {ADVERSARIES.filter((a) => available.has(a.id)).map((a) => (
                <button key={a.id} onClick={() => setAdversary(a.id)} title={a.sub}
                  className={`px-3 py-1.5 text-[12px] rounded-md border ${adversary === a.id
                    ? 'bg-accent text-white border-accent' : 'bg-white border-line hover:border-accent'}`}>
                  {a.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate mb-1.5">Metric</div>
            <div className="flex flex-wrap gap-1.5">
              {METRICS.map((m) => (
                <button key={m.id} onClick={() => setMetric(m.id)}
                  className={`px-3 py-1.5 text-[12px] rounded-md border ${metric === m.id
                    ? 'bg-ink text-white border-ink' : 'bg-white border-line hover:border-ink'}`}>
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <Card className="pb-4">
          <div className="pl-7 pr-2 pt-1">
            <Heatmap cells={cells} xLabel="ρ  coaching effectiveness"
              yLabel="λ  structural overlap" format={fmtv} />
          </div>
          <div className="flex items-center gap-5 mt-4 pt-3 border-t border-line text-[11.5px] text-slate">
            <span className="flex items-center gap-1.5">
              <span className="w-4 h-3.5 rounded-sm" style={{ background: 'rgb(24,68,116)' }} />
              declared context helps
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-4 h-3.5 rounded-sm" style={{ background: 'rgb(150,30,26)' }} />
              declared context hurts
            </span>
            <span className="flex items-center gap-1.5">
              <svg width="16" height="14"><rect width="16" height="14" fill="#fff" stroke="#e3e7ed" />
                <line x1="0" y1="14" x2="16" y2="-2" stroke="rgba(30,35,45,.45)" strokeWidth="1.6" />
                <line x1="0" y1="20" x2="22" y2="-2" stroke="rgba(30,35,45,.45)" strokeWidth="1.6" /></svg>
              CI includes zero — not significant
            </span>
          </div>
        </Card>

        <Note tone="warn">
          Hatched cells are part of the result, not missing data. Regions where the
          confidence interval includes zero are exactly the regions a payment network should
          <em> not</em> spend money collecting this field.
        </Note>
      </Section>

      <Section eyebrow="The headline number" title="ρ*, the coaching level at which the signal stops paying">
        <div className="grid md:grid-cols-[1.15fr_1fr] gap-5 items-start">
          <Card>
            <Table
              head={['λ  structural overlap', 'ρ* bracket', 'Reading']}
              align={['l', 'l', 'l']}
              rows={rhoStar.map((r) => [
                <span className="tabular-nums">{r.lam}</span>,
                <span className="tabular-nums font-medium">
                  {r.status === 'never significant' ? '< 0.0'
                    : r.status === 'significant throughout' ? '> 1.0'
                    : `${r.rho_star_lo} – ${r.rho_star_hi}`}
                </span>,
                <span className="text-slate text-[12px]">
                  {r.status === 'never significant' ? 'no measurable value at any coaching level'
                    : r.status === 'significant throughout' ? 'no coaching level in range removes the signal'
                    : 'value disappears between these two grid points'}
                </span>,
              ])}
            />
          </Card>
          <Note>
            <p className="mb-2">
              ρ* is <strong>bracketed by the sweep grid</strong>, not interpolated. It is known
              to lie between the last coaching level at which the confidence interval clears
              zero on every seed, and the first at which it does not. A finer number would be
              an interpolation this design does not support.
            </p>
            <p className="font-medium text-ink">
              This is a threshold under our specified threat model and parameterisation. It is
              not a universal fact about payment fraud, and it should never be quoted as one.
            </p>
          </Note>
        </div>
      </Section>

      <AblationPanel ablation={data.ablation} />
      <SecondaryPanel cells={data.cells} />
    </div>
  )
}

function AblationPanel({ ablation }) {
  const rows = useMemo(() => {
    const base = (ablation || []).filter(
      (r) => r.rho === 0.4 && r.lam === 0.1 && r.K === 11 && r.beta === 0.5 && r.adversary === 'uniform')
    const order = ['B1', 'B1+B2', 'B1+B2+B3', 'B1+B2+B3+B4a', 'B1+B2+B3+B4b']
    return order.map((arm) => {
      const g = base.filter((r) => r.arm === arm)
      if (!g.length) return null
      const mean = (k) => g.reduce((s, r) => s + r[k], 0) / g.length
      return { arm, recall: mean('recall@fpr=0.001'), prauc: mean('pr_auc'),
               feats: g[0].n_features, baseline: arm === 'B1+B2+B3' }
    }).filter(Boolean)
  }, [ablation])

  if (!rows.length) return null
  return (
    <Section eyebrow="Ablation" title="Each group added in turn, at ρ = 0.4, λ = 0.10">
      <div className="grid md:grid-cols-[1.1fr_1fr] gap-5 items-start">
        <Card>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={rows} margin={{ top: 8, right: 8, left: -14, bottom: 4 }}>
              <CartesianGrid strokeDasharray="2 3" stroke="#e9edf2" vertical={false} />
              <XAxis dataKey="arm" tick={{ fontSize: 10.5 }} interval={0} angle={-12} textAnchor="end" height={48} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 10.5 }} />
              <Tooltip formatter={(v) => v.toFixed(4)} contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="recall" name="recall @ FPR 0.1%" radius={[3, 3, 0, 0]}
                   fill="#1f4e79" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <Table
            head={['Arm', 'Feat.', 'PR-AUC', 'R @ FPR 0.1%']}
            align={['l', 'r', 'r', 'r']}
            rows={rows.map((r) => [
              <span className={r.baseline ? 'font-semibold' : ''}>{r.arm}{r.baseline ? '  ← baseline' : ''}</span>,
              r.feats, r.prauc.toFixed(4), r.recall.toFixed(4),
            ])}
          />
          <p className="text-[11.5px] text-slate mt-3 leading-relaxed">
            Recall at 0.5% and 1% FPR is saturated near 1.0 for the B4 arms, so those two
            pre-registered operating points carry little information. They were not changed
            after seeing results — the saturation is reported instead.
          </p>
        </Card>
      </div>
    </Section>
  )
}

function SecondaryPanel({ cells }) {
  const data = useMemo(() => {
    const pick = (col) => {
      const sel = (cells || []).filter(
        (c) => c.arm === 'B1+B2+B3+B4b' && c.metric === 'recall@fpr=0.001'
          && c.adversary === 'uniform' && c.rho === 0.4 && c.lam === 0.1)
      const keys = [...new Set(sel.map((c) => c[col]))].sort((a, b) => a - b)
      return keys.map((k) => {
        const g = sel.filter((c) => c[col] === k)
        const mean = g.reduce((s, c) => s + c.delta, 0) / g.length
        return { x: k, delta: mean, lo: Math.min(...g.map((c) => c.ci_lo)),
                 hi: Math.max(...g.map((c) => c.ci_hi)) }
      })
    }
    return { K: pick('K'), beta: pick('beta') }
  }, [cells])

  if (data.K.length < 2 && data.beta.length < 2) return null
  const panel = (rows, label) => (
    <Card>
      <div className="text-[12px] font-medium mb-2">{label}</div>
      <ResponsiveContainer width="100%" height={190}>
        <LineChart data={rows} margin={{ top: 8, right: 10, left: -12, bottom: 4 }}>
          <CartesianGrid strokeDasharray="2 3" stroke="#e9edf2" />
          <XAxis dataKey="x" tick={{ fontSize: 10.5 }} />
          <YAxis tick={{ fontSize: 10.5 }} />
          <Tooltip formatter={(v) => (typeof v === 'number' ? v.toFixed(4) : v)} contentStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="delta" stroke="#1f4e79" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )
  return (
    <Section eyebrow="Secondary sweeps" title="Purpose cardinality and beneficiary-feature noise">
      <div className="grid md:grid-cols-2 gap-5">
        {data.K.length > 1 && panel(data.K, 'Δ recall @ FPR 0.1% vs purpose cardinality K')}
        {data.beta.length > 1 && panel(data.beta, 'Δ recall @ FPR 0.1% vs beneficiary noise β')}
      </div>
    </Section>
  )
}
