import React from 'react'

const cache = new Map()

export async function load(name) {
  if (cache.has(name)) return cache.get(name)
  const p = fetch(`/api/${name}`).then(async (r) => {
    if (!r.ok) throw new Error(`${name}: ${r.status}`)
    return r.json()
  })
  cache.set(name, p)
  return p
}

export function useResource(name) {
  const [state, setState] = React.useState({ loading: true })
  React.useEffect(() => {
    let live = true
    load(name)
      .then((data) => live && setState({ loading: false, data }))
      .catch((error) => live && setState({ loading: false, error }))
    return () => { live = false }
  }, [name])
  return state
}

export const fmt = {
  pct: (v, d = 1) => `${(v * 100).toFixed(d)}%`,
  delta: (v, d = 4) => `${v >= 0 ? '+' : ''}${v.toFixed(d)}`,
  inr: (v) => `₹${Math.round(v).toLocaleString('en-IN')}`,
  num: (v, d = 3) => v.toFixed(d),
}
