import React from 'react'

export function Section({ eyebrow, title, children, className = '' }) {
  return (
    <section className={`mb-12 ${className}`}>
      {eyebrow && (
        <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-accent mb-1.5">
          {eyebrow}
        </div>
      )}
      {title && <h2 className="text-[19px] font-semibold mb-4 leading-tight">{title}</h2>}
      {children}
    </section>
  )
}

export function Card({ children, className = '' }) {
  return <div className={`card p-5 ${className}`}>{children}</div>
}

export function Stat({ value, label, sub, tone = 'ink' }) {
  const tones = { ink: 'text-ink', good: 'text-good', bad: 'text-bad', accent: 'text-accent' }
  return (
    <div className="card p-4">
      <div className={`text-[26px] font-semibold tabular-nums leading-none ${tones[tone]}`}>{value}</div>
      <div className="text-[12px] font-medium mt-1.5">{label}</div>
      {sub && <div className="text-[11px] text-slate mt-1 leading-snug">{sub}</div>}
    </div>
  )
}

export function Note({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-[#f4f6f9] border-line text-slate',
    warn: 'bg-[#fdf8ec] border-[#e8dcc0] text-[#6b5518]',
    good: 'bg-[#f0f8f3] border-[#cbe5d7] text-[#175c3c]',
  }
  return (
    <div className={`border rounded-md px-4 py-3 text-[12.5px] leading-relaxed ${tones[tone]}`}>
      {children}
    </div>
  )
}

export function Loading({ what }) {
  return (
    <div className="card p-8 text-center text-slate text-[13px]">
      Loading {what}…
    </div>
  )
}

export function Missing({ what, how }) {
  return (
    <div className="card p-8 text-[13px]">
      <div className="font-semibold mb-1">{what} has not been generated yet.</div>
      <div className="text-slate">Run <code className="mono bg-[#f4f6f9] px-1.5 py-0.5 rounded">{how}</code> and reload.</div>
    </div>
  )
}

export function Table({ head, rows, align = [] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12.5px] border-collapse">
        <thead>
          <tr className="border-b border-line">
            {head.map((h, i) => (
              <th key={i} className={`py-2 px-2.5 font-semibold text-slate text-[11px] uppercase tracking-wide ${align[i] === 'r' ? 'text-right' : 'text-left'}`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-line/60 last:border-0">
              {r.map((c, j) => (
                <td key={j} className={`py-2 px-2.5 tabular-nums ${align[j] === 'r' ? 'text-right' : ''}`}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
