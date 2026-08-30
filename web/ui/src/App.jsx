import React, { useState } from 'react'
import Question from './screens/Question'
import Phase from './screens/Phase'
import Inspector from './screens/Inspector'
import Agentic from './screens/Agentic'
import Methods from './screens/Methods'

const SCREENS = [
  { id: 'question', label: 'The question', el: Question },
  { id: 'phase', label: 'Phase diagram', el: Phase },
  { id: 'inspector', label: 'Consistency inspector', el: Inspector },
  { id: 'agentic', label: 'Mandate check', el: Agentic },
  { id: 'methods', label: 'Methods & limitations', el: Methods },
]

export default function App() {
  const [active, setActive] = useState('question')
  const Screen = SCREENS.find((s) => s.id === active).el

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white sticky top-0 z-20">
        <div className="max-w-[1120px] mx-auto px-6">
          <div className="flex items-baseline gap-3 pt-5 pb-1">
            <div className="text-[20px] font-bold tracking-tight">Pramana</div>
            <div className="text-[12px] text-slate italic">Sanskrit: a valid means of proof</div>
          </div>
          <p className="text-[12.5px] text-slate max-w-[760px] leading-relaxed pb-4">
            Payments can verify that a transaction was authorised without knowing whether it
            matched what the payer believed they were paying for. Pramana measures when adding
            that context is worth it, and how much adversarial pressure it survives.
          </p>
          <nav className="flex gap-1 -mb-px overflow-x-auto">
            {SCREENS.map((s, i) => (
              <button
                key={s.id}
                onClick={() => setActive(s.id)}
                className={`px-3.5 py-2 text-[12.5px] font-medium border-b-2 whitespace-nowrap transition-colors ${
                  active === s.id
                    ? 'border-accent text-accent'
                    : 'border-transparent text-slate hover:text-ink'
                }`}
              >
                <span className="tabular-nums opacity-50 mr-1.5">{i + 1}</span>
                {s.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-[1120px] mx-auto px-6 py-9">
        <Screen onNavigate={setActive} />
      </main>

      <footer className="border-t border-line mt-8">
        <div className="max-w-[1120px] mx-auto px-6 py-5 text-[11.5px] text-slate leading-relaxed">
          Synthetic data only. No live-system testing. No operational attack tooling.
          Every figure on this site is read from precomputed JSON produced by the experiment
          scripts in the repository — nothing is trained or generated at request time.
        </div>
      </footer>
    </div>
  )
}
