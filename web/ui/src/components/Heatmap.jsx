import React, { useState } from 'react'

// Diverging red→white→blue. Blue = declared context helped.
function colour(v, max) {
  if (v == null || Number.isNaN(v)) return '#f0f2f5'
  const t = Math.max(-1, Math.min(1, v / (max || 1e-9)))
  const mix = (a, b, k) => a.map((x, i) => Math.round(x + (b[i] - x) * k))
  const white = [255, 255, 255]
  const blue = [24, 68, 116]
  const red = [150, 30, 26]
  const c = t >= 0 ? mix(white, blue, t) : mix(white, red, -t)
  return `rgb(${c.join(',')})`
}

export default function Heatmap({ cells, xKey = 'rho', yKey = 'lam', valueKey = 'delta',
                                  xLabel, yLabel, format = (v) => v.toFixed(4), onHover }) {
  const [hover, setHover] = useState(null)
  const xs = [...new Set(cells.map((c) => c[xKey]))].sort((a, b) => a - b)
  const ys = [...new Set(cells.map((c) => c[yKey]))].sort((a, b) => b - a)
  const max = Math.max(...cells.map((c) => Math.abs(c[valueKey] ?? 0)), 1e-9)
  const at = (x, y) => cells.find((c) => c[xKey] === x && c[yKey] === y)

  return (
    <div className="relative">
      <div className="flex">
        <div className="flex flex-col justify-between pr-2 pt-0 pb-6 text-[11px] text-slate tabular-nums text-right"
             style={{ width: 34 }}>
          {ys.map((y) => <div key={y} style={{ height: 46, lineHeight: '46px' }}>{y}</div>)}
        </div>
        <div className="flex-1">
          <div className="grid gap-[2px]" style={{ gridTemplateColumns: `repeat(${xs.length}, minmax(0,1fr))` }}>
            {ys.map((y) => xs.map((x) => {
              const c = at(x, y)
              const v = c?.[valueKey]
              const sig = c?.significant
              const isHover = hover && hover.x === x && hover.y === y
              return (
                <div
                  key={`${x}-${y}`}
                  onMouseEnter={() => { setHover({ x, y, c }); onHover?.(c) }}
                  onMouseLeave={() => { setHover(null); onHover?.(null) }}
                  className={`relative h-[46px] flex items-center justify-center text-[11px] font-medium tabular-nums cursor-default rounded-[3px] transition-shadow ${isHover ? 'ring-2 ring-ink z-10' : ''}`}
                  style={{ background: colour(v, max) }}
                >
                  {!sig && c && (
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden>
                      <defs>
                        <pattern id={`h-${x}-${y}`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                          <line x1="0" y1="0" x2="0" y2="6" stroke="rgba(30,35,45,.45)" strokeWidth="1.6" />
                        </pattern>
                      </defs>
                      <rect width="100%" height="100%" fill={`url(#h-${x}-${y})`} rx="3" />
                    </svg>
                  )}
                  <span className="relative" style={{ color: Math.abs(v ?? 0) > max * 0.55 ? '#fff' : '#11161f' }}>
                    {c ? format(v) : '—'}
                  </span>
                </div>
              )
            }))}
          </div>
          <div className="grid gap-[2px] mt-1.5 text-[11px] text-slate tabular-nums text-center"
               style={{ gridTemplateColumns: `repeat(${xs.length}, minmax(0,1fr))` }}>
            {xs.map((x) => <div key={x}>{x}</div>)}
          </div>
          <div className="text-center text-[11.5px] text-slate mt-1.5">{xLabel}</div>
        </div>
      </div>
      <div className="absolute left-0 top-1/2 -translate-y-1/2 -rotate-90 origin-center text-[11.5px] text-slate"
           style={{ left: -26 }}>{yLabel}</div>

      {hover?.c && (
        <div className="mt-4 card p-3 text-[12px]">
          <div className="font-semibold mb-1.5 tabular-nums">
            ρ = {hover.x} · λ = {hover.y}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-5 gap-y-1 tabular-nums">
            <div><span className="text-slate">Δ mean </span>{format(hover.c.delta)}</div>
            <div><span className="text-slate">95% CI </span>[{format(hover.c.ci_lo_min)}, {format(hover.c.ci_hi_max)}]</div>
            <div><span className="text-slate">seeds </span>{hover.c.n_seeds}</div>
            <div><span className="text-slate">test fraud </span>{Math.round(hover.c.n_test_fraud)}</div>
          </div>
          <div className={`mt-1.5 text-[11.5px] font-medium ${hover.c.significant ? 'text-good' : 'text-slate'}`}>
            {hover.c.significant
              ? 'CI lower bound above zero on every seed'
              : 'CI includes zero on at least one seed — declared context does not pay here'}
          </div>
        </div>
      )}
    </div>
  )
}
