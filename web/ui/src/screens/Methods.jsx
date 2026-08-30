import React, { useState } from 'react'
import { useResource, fmt } from '../api'
import { Section, Card, Note, Loading, Table, Stat } from '../components/ui'

const DOCS = [
  { id: 'preregistration', label: 'Pre-registration', note: 'first commit, never edited' },
  { id: 'changelog', label: 'Changelog', note: 'every post-hoc change, with cause' },
  { id: 'limitations', label: 'Limitations', note: 'read before the results' },
  { id: 'data_card', label: 'Data card', note: 'population and calibration' },
  { id: 'model_card', label: 'Model card', note: 'model and tuning protocol' },
]

export default function Methods() {
  const prov = useResource('provenance')
  const fid = useResource('fidelity')
  const [doc, setDoc] = useState('preregistration')

  if (prov.loading) return <Loading what="provenance" />

  const params = prov.data?.frozen_params || {}

  return (
    <div>
      <Section eyebrow="Provenance" title="Everything needed to check the work">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Stat value="1st" label="Commit holding the pre-registration"
                sub="its sole content; verify with git log --reverse --stat" />
          <Stat value={params.n_estimators ? '24' : '—'} label="Tuning candidates"
                sub="all spent on the B1+B2+B3 baseline" />
          <Stat value={params.best_pr_auc_mean ? '' : (prov.data?.frozen_params?.best_pr_auc_mean ?? '').toString() || '5-fold'}
                label="CV protocol" sub="GroupKFold on payer_id" />
          <Stat value="1000" label="Bootstrap resamples" sub="clustered on test payers" />
        </div>

        <Card className="mb-4">
          <div className="text-[12px] font-medium mb-2">Frozen hyperparameters — selected on the baseline arm alone</div>
          <pre className="mono bg-[#f6f8fa] border border-line rounded p-3 overflow-x-auto">
{JSON.stringify(prov.data?.frozen_params?.params ?? params, null, 2)}
          </pre>
        </Card>

        <div className="flex flex-wrap gap-1.5 mb-3">
          {DOCS.map((d) => (
            <button key={d.id} onClick={() => setDoc(d.id)} title={d.note}
              className={`px-3 py-1.5 text-[12px] rounded-md border ${doc === d.id
                ? 'bg-accent text-white border-accent' : 'bg-white border-line hover:border-accent'}`}>
              {d.label}
            </button>
          ))}
        </div>
        <Card className="max-h-[520px] overflow-y-auto">
          <pre className="mono whitespace-pre-wrap leading-relaxed">{prov.data?.[doc] || '—'}</pre>
        </Card>
      </Section>

      {fid.data && (
        <Section eyebrow="Fidelity" title="Calibrated against published primary sources only">
          <div className="grid md:grid-cols-2 gap-5">
            <Card>
              <Table
                head={['Quantity', 'Observed', 'Anchor', '|error|']}
                align={['l', 'r', 'r', 'r']}
                rows={Object.keys(fid.data.case_level_asymmetry.anchor).map((k) => [
                  k.replace(/_/g, ' '),
                  fid.data.case_level_asymmetry.observed[k].toFixed(k.includes('inr') ? 0 : 4),
                  fid.data.case_level_asymmetry.anchor[k].toFixed(k.includes('inr') ? 0 : 4),
                  fid.data.case_level_asymmetry.abs_error[k].toFixed(k.includes('inr') ? 0 : 4),
                ])}
              />
            </Card>
            <Card>
              <Table
                head={['Graph / stream statistic', 'Value']}
                align={['l', 'r']}
                rows={[
                  ['payee in-degree CCDF log-log slope', fid.data.degree_distribution.ccdf_loglog_slope.toFixed(2)],
                  ['median payee in-degree', fid.data.degree_distribution.median_in_degree.toFixed(0)],
                  ['max payee in-degree', fid.data.degree_distribution.max_in_degree.toLocaleString()],
                  ['median inter-transaction gap (days)', fid.data.inter_transaction_times.median_days.toFixed(2)],
                  ['share of gaps under a day', fmt.pct(fid.data.inter_transaction_times.share_under_1_day)],
                  ['max |corr| between distinct B3 features', fid.data.b3_redundancy.max_abs_corr.toFixed(3)],
                  ['latent recovery (Spearman)', fid.data.latent_recovery.spearman.toFixed(3)],
                ]}
              />
            </Card>
          </div>
          <Note tone="warn">
            <strong>Not run:</strong> {fid.data.not_run.discriminator_auc_vs_real_data}
          </Note>
        </Section>
      )}

      <Section eyebrow="The circularity answer" title="Asked before you can ask it">
        <Card className="border-l-[3px] border-l-accent">
          <p className="text-[13.5px] leading-relaxed">
            We plant context metadata, so we make <strong>no claim about absolute detection
            rates</strong>. What is not circular: the deterministic results are structural, the
            phase diagram measures relative behaviour across parameter regimes rather than a
            point estimate, and we have published the generative process so the partition can be
            challenged. We are characterising when a control is worth deploying, not claiming a
            benchmark win.
          </p>
        </Card>
      </Section>
    </div>
  )
}
