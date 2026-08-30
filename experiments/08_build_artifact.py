"""Emit the self-contained single-file version of the prototype.

Same numbers as the FastAPI + React app, but with every result inlined so the
page works as one shareable HTML file with no server and no network calls.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RES = Path("results")
OUT = Path("web/pramana_artifact.html")


def load(name, default=None):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else default


def git(*a, default="—"):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return default


def slim_phase(phase):
    """Drop per-cell rows the page never reads; keeps the file small."""
    if not phase:
        return None
    return {
        "arm": phase["arm"],
        "metrics": phase["metrics"],
        "rho_star": phase["rho_star"],
        "ablation": [r for r in phase["ablation"]
                     if r["rho"] == 0.4 and r["lam"] == 0.1 and r["K"] == 11
                     and r["beta"] == 0.5 and r["adversary"] == "uniform"],
        "secondary": [c for c in phase["cells"]
                      if c["arm"] == phase["arm"] and c["metric"] == "recall@fpr=0.001"
                      and c["adversary"] == "uniform" and c["rho"] == 0.4
                      and c["lam"] == 0.1],
    }


def slim_inspector(ins):
    if not ins:
        return None
    return {"b3_cols": ins["b3_cols"], "cases": ins["cases"]}


DATA_KEYS = ("phase", "ablation", "agentic", "fidelity", "inspector", "meta")


def build() -> str:
    data = {
        "phase": slim_phase(load("phase_surface.json")),
        "ablation": load("ablation.json"),
        "agentic": load("agentic_conformance.json"),
        "fidelity": load("fidelity.json"),
        "inspector": slim_inspector(load("inspector.json")),
        "meta": {
            "prereg_commit": (git("log", "--reverse", "--format=%H", default="") or "")[:40],
            "head": git("rev-parse", "--short", "HEAD"),
            "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        },
    }
    payload = json.dumps(data, separators=(",", ":"), default=str)
    return TEMPLATE.replace("__PRAMANA_DATA__", payload)


TEMPLATE = r"""<title>Pramana</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --ground:#f7f6f3; --surface:#ffffff; --raised:#fbfaf8;
  --ink:#16181d; --ink-soft:#3d4351; --muted:#626878;
  --hairline:#e4e2dc; --hairline-strong:#d3d0c8;
  --accent:#1d3b73; --accent-soft:#e8edf6; --accent-ink:#1d3b73;
  --positive:#1c6b4c; --positive-soft:#e6f2ec;
  --negative:#a32e24; --negative-soft:#f8eae8;
  --caution:#8a6320; --caution-soft:#f9f1e2;
  --heat-pos:29,59,115; --heat-neg:163,46,36;
  --shadow:0 1px 2px rgba(22,24,29,.05), 0 8px 24px -18px rgba(22,24,29,.35);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#15171b; --surface:#1d2026; --raised:#22262d;
    --ink:#e9eaee; --ink-soft:#c3c8d2; --muted:#98a0b0;
    --hairline:#2b2f38; --hairline-strong:#3a3f4a;
    --accent:#7ba3de; --accent-soft:#1b2740; --accent-ink:#a9c4ea;
    --positive:#5fbf92; --positive-soft:#152a22;
    --negative:#e58278; --negative-soft:#2e1a18;
    --caution:#d9ac5c; --caution-soft:#2a2317;
    --heat-pos:123,163,222; --heat-neg:229,130,120;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -18px rgba(0,0,0,.8);
  }
}
:root[data-theme="dark"]{
  --ground:#15171b; --surface:#1d2026; --raised:#22262d;
  --ink:#e9eaee; --ink-soft:#c3c8d2; --muted:#98a0b0;
  --hairline:#2b2f38; --hairline-strong:#3a3f4a;
  --accent:#7ba3de; --accent-soft:#1b2740; --accent-ink:#a9c4ea;
  --positive:#5fbf92; --positive-soft:#152a22;
  --negative:#e58278; --negative-soft:#2e1a18;
  --caution:#d9ac5c; --caution-soft:#2a2317;
  --heat-pos:123,163,222; --heat-neg:229,130,120;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -18px rgba(0,0,0,.8);
}

*{box-sizing:border-box}
body{
  background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, sans-serif;
  font-size:15px; line-height:1.62; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px; margin:0 auto; padding:0 28px}
h1,h2,h3{font-family:Spectral, Georgia, "Times New Roman", serif; text-wrap:balance; margin:0}
.mono{font-family:"IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace}
.num{font-variant-numeric:tabular-nums}
a{color:var(--accent-ink)}

/* ---------- masthead ---------- */
.masthead{border-bottom:1px solid var(--hairline); background:var(--surface)}
.masthead .wrap{padding-top:44px; padding-bottom:32px}
.wordmark{display:flex; align-items:baseline; gap:14px; flex-wrap:wrap}
.wordmark h1{font-size:46px; font-weight:700; letter-spacing:-.018em; line-height:1}
.gloss{font-family:Spectral, Georgia, serif; font-style:italic; color:var(--muted); font-size:16px}
.thesis{
  font-family:Spectral, Georgia, serif; font-size:21px; line-height:1.5;
  max-width:34em; margin-top:20px; color:var(--ink-soft);
}
.stamps{display:flex; gap:10px; flex-wrap:wrap; margin-top:24px}
.stamp{
  border:1px solid var(--hairline-strong); border-radius:2px; padding:5px 10px;
  font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted);
  background:var(--raised);
}
.stamp b{color:var(--ink); font-weight:600; letter-spacing:0; text-transform:none}

/* ---------- nav ---------- */
nav{
  position:sticky; top:0; z-index:20; background:var(--surface);
  border-bottom:1px solid var(--hairline);
}
nav .wrap{display:flex; gap:2px; overflow-x:auto; padding-top:0; padding-bottom:0}
nav button{
  appearance:none; background:none; border:0; border-bottom:2px solid transparent;
  padding:13px 13px 11px; font:inherit; font-size:13px; color:var(--muted);
  cursor:pointer; white-space:nowrap; display:flex; gap:8px; align-items:baseline;
}
nav button .n{font-family:"IBM Plex Mono",monospace; font-size:11px; opacity:.55}
nav button:hover{color:var(--ink)}
nav button[aria-current="true"]{color:var(--accent-ink); border-bottom-color:var(--accent)}
nav button:focus-visible{outline:2px solid var(--accent); outline-offset:-2px}

/* ---------- sections ---------- */
main .wrap{padding-top:40px; padding-bottom:56px}
section[hidden]{display:none !important}
.eyebrow{
  font-size:11px; letter-spacing:.13em; text-transform:uppercase;
  color:var(--accent-ink); font-weight:600; margin-bottom:6px;
}
h2{font-size:27px; font-weight:600; letter-spacing:-.012em; margin-bottom:14px}
h3{font-size:18px; font-weight:600; margin:30px 0 10px}
p{max-width:66ch; margin:0 0 14px}
.lede{font-size:16.5px; color:var(--ink-soft)}
.stack{display:flex; flex-direction:column; gap:0}

/* ---------- panels ---------- */
.panel{
  background:var(--surface); border:1px solid var(--hairline);
  border-radius:3px; padding:22px; box-shadow:var(--shadow);
}
.grid{display:grid; gap:14px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
@media(max-width:820px){.g2,.g4{grid-template-columns:1fr}}
.metric{background:var(--surface); border:1px solid var(--hairline); border-radius:3px; padding:15px 16px}
.metric .v{font-family:"IBM Plex Mono",monospace; font-size:25px; font-weight:600; line-height:1.1; font-variant-numeric:tabular-nums}
.metric .l{font-size:12.5px; font-weight:500; margin-top:7px}
.metric .s{font-size:11.5px; color:var(--muted); margin-top:3px; line-height:1.4}
.v.pos{color:var(--positive)} .v.neg{color:var(--negative)} .v.acc{color:var(--accent-ink)}

.callout{
  border-left:3px solid var(--accent); background:var(--accent-soft);
  padding:14px 18px; border-radius:0 3px 3px 0; margin:18px 0;
}
.callout.warn{border-left-color:var(--caution); background:var(--caution-soft)}
.callout.bad{border-left-color:var(--negative); background:var(--negative-soft)}
.callout p{margin:0; max-width:none; font-size:14px}
.callout p+p{margin-top:9px}

/* ---------- tables ---------- */
.scroll{overflow-x:auto; -webkit-overflow-scrolling:touch}
table{border-collapse:collapse; width:100%; font-size:13px}
th{
  text-align:left; font-size:10.5px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--muted); font-weight:600; padding:8px 10px; border-bottom:1px solid var(--hairline-strong);
  white-space:nowrap;
}
td{padding:8px 10px; border-bottom:1px solid var(--hairline); font-variant-numeric:tabular-nums; vertical-align:top}
tr:last-child td{border-bottom:0}
td.r,th.r{text-align:right}
.tag{font-size:11px; padding:2px 7px; border-radius:2px; font-weight:600; white-space:nowrap}
.tag.ok{background:var(--positive-soft); color:var(--positive)}
.tag.no{background:var(--negative-soft); color:var(--negative)}
.tag.mid{background:var(--raised); color:var(--muted); border:1px solid var(--hairline)}

/* ---------- controls ---------- */
.controls{display:flex; gap:22px; flex-wrap:wrap; margin-bottom:16px}
.ctl-label{font-size:10.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); font-weight:600; margin-bottom:6px}
.seg{display:flex; gap:5px; flex-wrap:wrap}
.seg button{
  appearance:none; font:inherit; font-size:12.5px; padding:6px 11px; cursor:pointer;
  background:var(--surface); color:var(--ink); border:1px solid var(--hairline-strong);
  border-radius:2px;
}
.seg button:hover{border-color:var(--accent)}
.seg button[aria-pressed="true"]{background:var(--accent); border-color:var(--accent); color:var(--ground)}
.seg button:focus-visible{outline:2px solid var(--accent); outline-offset:2px}

/* ---------- heatmap ---------- */
.heat-shell{display:grid; grid-template-columns:auto 1fr; gap:0 10px; align-items:stretch}
.heat-y{display:flex; flex-direction:column; justify-content:space-between; padding-bottom:26px}
.heat-y span{font-size:11.5px; color:var(--muted); font-variant-numeric:tabular-nums; display:flex; align-items:center; height:48px}
.heat-grid{display:grid; gap:3px}
.cell{
  height:48px; display:flex; align-items:center; justify-content:center;
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; font-weight:500;
  border-radius:2px; cursor:default; position:relative; font-variant-numeric:tabular-nums;
}
.cell:focus-visible{outline:2px solid var(--ink); outline-offset:1px}
.cell.sel{outline:2px solid var(--ink); outline-offset:1px}
.heat-x{display:grid; gap:3px; margin-top:7px}
.heat-x span{font-size:11.5px; color:var(--muted); text-align:center; font-variant-numeric:tabular-nums}
.axis-cap{font-size:12px; color:var(--muted); text-align:center; margin-top:6px}
.legend{display:flex; gap:20px; flex-wrap:wrap; align-items:center; margin-top:16px; padding-top:14px; border-top:1px solid var(--hairline); font-size:11.5px; color:var(--muted)}
.legend i{display:inline-block; width:18px; height:13px; border-radius:2px; margin-right:7px; vertical-align:-2px}
.readout{margin-top:14px; background:var(--raised); border:1px solid var(--hairline); border-radius:2px; padding:12px 14px; font-size:12.5px}
.readout .row{display:flex; gap:20px; flex-wrap:wrap; font-variant-numeric:tabular-nums}
.readout .k{color:var(--muted)}

/* ---------- verification receipt ---------- */
.receipt{display:grid; grid-template-columns:1fr 1fr; gap:0; border:1px solid var(--hairline-strong); border-radius:3px; overflow:hidden}
@media(max-width:820px){.receipt{grid-template-columns:1fr}}
.receipt .side{padding:20px 22px}
.receipt .side.mandate{background:var(--surface); border-right:1px solid var(--hairline)}
@media(max-width:820px){.receipt .side.mandate{border-right:0; border-bottom:1px solid var(--hairline)}}
.receipt .side.verdict.reject{background:var(--negative-soft)}
.receipt .side.verdict.pass{background:var(--caution-soft)}
.kv{font-family:"IBM Plex Mono",monospace; font-size:12.5px; line-height:1.95}
.kv .k{color:var(--muted)}
.kv b{font-weight:600}
.checks{font-family:"IBM Plex Mono",monospace; font-size:12.5px; line-height:1.85}
.checks div{display:flex; gap:9px; align-items:baseline}
.checks .g{color:var(--positive); width:11px}
.checks .x{color:var(--negative); width:11px; font-weight:700}
.checks .id{width:42px; color:var(--muted)}
.checks .fail{color:var(--negative); font-weight:500}
.verdict-line{
  margin-top:16px; padding-top:13px; border-top:1px solid var(--hairline-strong);
  font-family:"IBM Plex Mono",monospace; font-size:16px; font-weight:600;
}
.verdict-line.reject{color:var(--negative)} .verdict-line.pass{color:var(--caution)}
.verdict-note{font-size:12.5px; margin-top:7px; color:var(--ink-soft); line-height:1.5}

/* ---------- residual bars ---------- */
.resid{display:flex; flex-direction:column; gap:5px; margin-top:12px}
.resid .r{display:grid; grid-template-columns:150px 1fr 52px; gap:9px; align-items:center; font-size:11.5px}
.resid .name{color:var(--muted); text-align:right; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.resid .track{position:relative; height:15px; background:var(--raised); border-radius:2px}
.resid .mid{position:absolute; left:50%; top:0; bottom:0; width:1px; background:var(--hairline-strong)}
.resid .bar{position:absolute; top:2px; bottom:2px; border-radius:1px}
.resid .val{font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums; text-align:right}

.notrun{font-size:13px; color:var(--muted); font-style:italic}
.pending{background:var(--raised); border:1px dashed var(--hairline-strong); border-radius:3px; padding:26px; text-align:center; color:var(--muted); font-size:13.5px}
footer{border-top:1px solid var(--hairline); background:var(--surface)}
footer .wrap{padding:22px 28px; font-size:12px; color:var(--muted); max-width:1080px}
.doclist{display:flex; flex-direction:column; gap:0; border:1px solid var(--hairline); border-radius:3px; overflow:hidden}
.doclist button{
  appearance:none; text-align:left; font:inherit; font-size:13px; background:var(--surface);
  border:0; border-bottom:1px solid var(--hairline); padding:11px 15px; cursor:pointer; color:var(--ink);
}
.doclist button:last-child{border-bottom:0}
.doclist button[aria-pressed="true"]{background:var(--accent-soft); color:var(--accent-ink); font-weight:600}
pre.doc{
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; line-height:1.62;
  white-space:pre-wrap; word-break:break-word; margin:0; max-height:520px; overflow:auto;
  background:var(--raised); border:1px solid var(--hairline); border-radius:3px; padding:16px;
}
@media (prefers-reduced-motion: reduce){*{transition:none !important; animation:none !important}}
</style>

<header class="masthead">
  <div class="wrap">
    <div class="wordmark">
      <h1>Pramana</h1>
      <span class="gloss">Sanskrit: a valid means of proof</span>
    </div>
    <p class="thesis">Payments can verify that a transaction was authorised without knowing
      whether it matched what the payer believed they were paying for. Pramana measures when
      adding that context is worth it, and how much adversarial pressure it survives.</p>
    <div class="stamps" id="stamps"></div>
  </div>
</header>

<nav><div class="wrap" id="nav"></div></nav>

<main><div class="wrap">
  <section id="s-question"></section>
  <section id="s-phase" hidden></section>
  <section id="s-inspector" hidden></section>
  <section id="s-mandate" hidden></section>
  <section id="s-methods" hidden></section>
</div></main>

<footer><div class="wrap">
  Synthetic data only. No live-system testing. No operational attack tooling.
  Every figure on this page is read from precomputed results committed to the repository —
  nothing is trained or generated when you load it.
</div></footer>

<script>
const D = __PRAMANA_DATA__;

const el = (t, a = {}, kids = []) => {
  const n = document.createElement(t);
  for (const [k, v] of Object.entries(a)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? '' : v);
  }
  for (const k of [].concat(kids)) {
    if (k === null || k === undefined || k === false) continue;
    n.append(k.nodeType ? k : document.createTextNode(k));
  }
  return n;
};
const fmtPct = (v, d = 1) => (v * 100).toFixed(d) + '%';
const fmtINR = (v) => '₹' + Math.round(v).toLocaleString('en-IN');
const sign = (v, d = 4) => (v >= 0 ? '+' : '') + v.toFixed(d);

function metric(v, l, s, tone) {
  return el('div', { class: 'metric' }, [
    el('div', { class: 'v ' + (tone || '') }, [v]),
    el('div', { class: 'l' }, [l]),
    s ? el('div', { class: 's' }, [s]) : null,
  ]);
}
function table(head, rows, rightCols = []) {
  const t = el('table');
  t.append(el('thead', {}, [el('tr', {}, head.map((h, i) =>
    el('th', { class: rightCols.includes(i) ? 'r' : '' }, [h])))]));
  t.append(el('tbody', {}, rows.map((r) => el('tr', {}, r.map((c, i) =>
    el('td', { class: rightCols.includes(i) ? 'r' : '' }, [c]))))));
  return el('div', { class: 'scroll' }, [t]);
}
function seg(label, options, current, onPick) {
  return el('div', {}, [
    el('div', { class: 'ctl-label' }, [label]),
    el('div', { class: 'seg' }, options.map((o) =>
      el('button', {
        type: 'button', 'aria-pressed': String(o.id === current),
        title: o.title || '', onclick: () => onPick(o.id),
      }, [o.label]))),
  ]);
}
function pending(what, how) {
  return el('div', { class: 'pending' }, [
    el('div', { html: '<b>' + what + '</b> has not been generated yet.' }),
    el('div', { class: 'mono', style: 'margin-top:8px;font-size:12px' }, [how]),
  ]);
}

/* ---------------- stamps ---------------- */
document.getElementById('stamps').append(
  el('span', { class: 'stamp', html: 'Pre-registration <b class="mono">' +
      (D.meta.prereg_commit || '—').slice(0, 10) + '</b>' }),
  el('span', { class: 'stamp', html: 'HEAD <b class="mono">' + D.meta.head + '</b>' }),
  el('span', { class: 'stamp', html: 'Built <b>' + D.meta.built + '</b>' }),
  el('span', { class: 'stamp' }, ['Synthetic data only']),
);

/* ---------------- screen 1 ---------------- */
function screenQuestion(root) {
  root.append(el('div', { class: 'eyebrow' }, ['The problem, today, in India']));
  root.append(el('h2', {}, ['A rail can prove you authorised a transfer. It cannot prove you understood what you were paying for.']));

  root.append(el('div', { class: 'grid g4', style: 'margin:20px 0' }, [
    metric('₹22,931 cr', 'Reported loss, 2025', 'NCRP, cited in the RBI discussion paper'),
    metric('28 lakh', 'Reported cases', 'implied mean case loss ₹81,896'),
    metric('~45%', 'Of cases above ₹10,000', 'by volume'),
    metric('~98.5%', 'Of value above ₹10,000', 'by value', 'acc'),
  ]));

  root.append(el('div', { class: 'callout' }, [
    el('p', { html: 'The RBI published <i>Exploring Safeguards in Digital Payments to Curb Frauds</i> on 9 April 2026, proposing four controls — a one-hour lag above ₹10,000, trusted-person authentication, a ₹25 lakh credit cap, and a kill switch. Comments closed 8 May 2026. These are <b>proposed, not law</b>.' }),
    el('p', { html: 'Every one is a friction control. <b>None is a detection improvement.</b> This work asks the adjacent question the paper does not.' }),
  ]));

  root.append(el('h3', {}, ['The research question, frozen before any code was written']));
  root.append(el('div', { class: 'panel', style: 'border-left:3px solid var(--accent)' }, [
    el('p', { style: 'font-family:Spectral,Georgia,serif;font-size:18.5px;line-height:1.55;margin:0;max-width:60ch' }, [
      'Under what levels of adversarially degraded payment-context reliability does declared payment context provide incremental fraud-detection value beyond transaction, behavioural, and beneficiary intelligence?']),
  ]));
  root.append(el('p', { style: 'margin-top:14px' }, [
    'The pre-registration was the sole content of this repository’s first commit, written before the simulator existed and never edited since. It fixes the feature groups, both metric families, the operating points, the sweep grid, and the condition under which we would conclude the signal does not work.']));

  root.append(el('h3', {}, ['Four feature groups, one model class, one tuning budget']));
  root.append(el('div', { class: 'grid g2' }, [
    el('div', { class: 'panel' }, [table(
      ['Group', 'Content', 'n'],
      [['B1 transaction', 'amount, timing, channel, velocity', '13'],
       ['B2 payer session', 'duration, hesitation, edits, device', '11'],
       ['B3 beneficiary', 'age, topology, network position, reports', '13'],
       ['B4 declared context', 'purpose code; + consistency residuals', '1 / 16']],
      [2])]),
    el('div', { class: 'stack', style: 'gap:14px' }, [
      el('div', { class: 'callout', style: 'margin:0' }, [
        el('p', { html: '<b>The baseline gets the advantage.</b> Hyperparameters were selected by a 24-candidate search under 5-fold payer-grouped CV on the <i>B1+B2+B3 arm alone</i>, then frozen and reused verbatim for every arm including the ones containing B4. The incumbent got the search; the challenger got nothing.' })]),
      el('div', { class: 'callout warn', style: 'margin:0' }, [
        el('p', { html: '<b>Every feature belongs to exactly one group.</b> A build-failing test enforces it. If B4 silently re-encoded B3, a measured gain would only mean “we gave the model beneficiary information twice”.' })]),
    ]),
  ]));

  root.append(el('h3', {}, ['What is not being claimed']));
  const claims = [
    ['That structured purpose fields don’t exist.', 'ISO 20022 <Purp><Cd> exists and travels in pain.001 and pacs.008.'],
    ['That banks don’t ask purpose.', 'UK banks do, under the Consumer Standard of Caution.'],
    ['That purpose is never used in decisions.', 'BIS Nexus guidance notes a destination PSP may consider purpose codes.'],
    ['That UPI lacks signed intents.', 'It signs payment-request parameters, though not semantic purpose.'],
    ['That AP2 lacks mandate verification.', 'AP2 v0.2 specifies open and closed mandates with deterministic conformance checking.'],
    ['That purpose × beneficiary is novel.', 'It is ordinary feature engineering.'],
  ];
  root.append(el('div', { class: 'panel' }, [table(['Not claiming', 'Because'],
    claims.map(([a, b]) => [el('span', { style: 'font-weight:500' }, [a]), b]))]));
  root.append(el('div', { class: 'callout warn' }, [
    el('p', { html: 'A global negative cannot be proven, so we do not claim one. What can be said: <b>we found no publicly documented production system that models purpose–beneficiary consistency as a standalone feature class</b> — and, more importantly, no published measurement of such a signal’s adversarial tolerance. That measurement is the contribution.' })]));

  if (D.fidelity) {
    const ca = D.fidelity.case_level_asymmetry, cb = D.fidelity.class_balance;
    root.append(el('h3', {}, ['The population is calibrated against primary sources, not another simulator']));
    root.append(el('div', { class: 'grid g4' }, [
      metric(ca.observed.share_of_cases_above_10k.toFixed(4), 'Cases above ₹10,000', 'anchor 0.450'),
      metric(ca.observed.share_of_value_above_10k.toFixed(4), 'Value above ₹10,000', 'anchor 0.985'),
      metric(fmtINR(ca.observed.mean_case_loss_inr), 'Mean case loss', 'anchor ₹81,896'),
      metric((cb.n_transactions / 1e6).toFixed(2) + 'M', 'Transactions',
             fmtPct(cb.fraud_share_of_volume, 2) + ' fraud by volume'),
    ]));
    root.append(el('p', { style: 'margin-top:12px' }, [
      'The case-size distribution has two parameters, and they were solved — not tuned — against the published mean case loss and the 45% of cases above ₹10,000. The residual on the value share is reported, not fitted away.']));
  }
}

/* ---------------- screen 2 ---------------- */
const METRICS = [
  { id: 'recall@fpr=0.001', label: 'Δ recall @ FPR 0.1%' },
  { id: 'recall@fpr=0.005', label: 'Δ recall @ FPR 0.5%' },
  { id: 'recall@fpr=0.01', label: 'Δ recall @ FPR 1%' },
  { id: 'fpr@recall=0.5', label: 'Δ FPR @ recall 50%' },
  { id: 'fpr@recall=0.7', label: 'Δ FPR @ recall 70%' },
  { id: 'fpr@recall=0.9', label: 'Δ FPR @ recall 90%' },
];
const ADV = [
  { id: 'uniform', label: 'Pre-registered adversary', title: 'uniform over the coached safe set' },
  { id: 'prevalence', label: 'Prevalence-matched', title: 'declared code carries no marginal information at rho = 1' },
  { id: 'matched', label: 'Beneficiary-matched', title: 'the attacker also routes to a mule whose profile fits the declared purpose' },
];
let phaseState = { metric: 'recall@fpr=0.001', adversary: 'uniform' };

function heatColour(v, max) {
  if (v === null || v === undefined || Number.isNaN(v)) return 'var(--raised)';
  const t = Math.max(-1, Math.min(1, v / (max || 1e-9)));
  const c = t >= 0 ? getComputedStyle(document.documentElement).getPropertyValue('--heat-pos')
                   : getComputedStyle(document.documentElement).getPropertyValue('--heat-neg');
  return 'rgba(' + c.trim() + ',' + (0.09 + 0.86 * Math.abs(t)).toFixed(3) + ')';
}

function screenPhase(root) {
  root.replaceChildren();
  root.append(el('div', { class: 'eyebrow' }, ['The result']));
  root.append(el('h2', {}, ['Where declared payment context pays, and where it does not']));

  if (!D.phase) { root.append(pending('The phase surface', 'make sweep && make figures')); return; }

  const avail = new Set(Object.keys(D.phase.metrics).map((k) => k.split('|')[0]));
  root.append(el('div', { class: 'controls' }, [
    seg('Adversary', ADV.filter((a) => avail.has(a.id)), phaseState.adversary,
        (id) => { phaseState.adversary = id; screenPhase(root); }),
    seg('Metric', METRICS, phaseState.metric,
        (id) => { phaseState.metric = id; screenPhase(root); }),
  ]));

  const key = phaseState.adversary + '|' + phaseState.metric;
  const cells = D.phase.metrics[key] || [];
  if (!cells.length) { root.append(pending('This surface', 'make sweep')); return; }

  const digits = phaseState.metric.startsWith('fpr') ? 5 : 4;
  const xs = [...new Set(cells.map((c) => c.rho))].sort((a, b) => a - b);
  const ys = [...new Set(cells.map((c) => c.lam))].sort((a, b) => b - a);
  const max = Math.max(...cells.map((c) => Math.abs(c.delta || 0)), 1e-9);
  const readout = el('div', { class: 'readout' }, [
    el('div', { class: 'k', style: 'font-size:12px' }, ['Hover or focus a cell for its confidence interval.'])]);

  const grid = el('div', { class: 'heat-grid', style: 'grid-template-columns:repeat(' + xs.length + ',minmax(0,1fr))' });
  const showCell = (c, node) => {
    document.querySelectorAll('.cell.sel').forEach((n) => n.classList.remove('sel'));
    if (node) node.classList.add('sel');
    readout.replaceChildren(
      el('div', { style: 'font-weight:600;margin-bottom:5px' },
         ['ρ = ' + c.rho + '  ·  λ = ' + c.lam]),
      el('div', { class: 'row' }, [
        el('span', { html: '<span class="k">Δ mean</span> ' + sign(c.delta, digits) }),
        el('span', { html: '<span class="k">95% CI</span> [' + sign(c.ci_lo_min, digits) + ', ' + sign(c.ci_hi_max, digits) + ']' }),
        el('span', { html: '<span class="k">seeds</span> ' + c.n_seeds }),
        el('span', { html: '<span class="k">test fraud</span> ' + Math.round(c.n_test_fraud) }),
      ]),
      el('div', { style: 'margin-top:6px;font-size:12px;font-weight:500;color:' + (c.significant ? 'var(--positive)' : 'var(--muted)') },
         [c.significant ? 'CI lower bound above zero on every seed'
                        : 'CI includes zero on at least one seed — declared context does not pay here']),
    );
  };

  ys.forEach((y) => xs.forEach((x) => {
    const c = cells.find((k) => k.rho === x && k.lam === y);
    const node = el('div', {
      class: 'cell', tabindex: '0', role: 'button',
      'aria-label': 'rho ' + x + ', lambda ' + y + ', delta ' + (c ? sign(c.delta, digits) : 'missing'),
      style: 'background:' + heatColour(c ? c.delta : null, max) +
             (c && !c.significant ? ';background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,var(--hairline-strong) 3px,var(--hairline-strong) 4.4px)' : ''),
    }, [c ? sign(c.delta, digits) : '—']);
    if (c) {
      node.addEventListener('mouseenter', () => showCell(c, node));
      node.addEventListener('focus', () => showCell(c, node));
    }
    grid.append(node);
  }));

  root.append(el('div', { class: 'panel' }, [
    el('div', { class: 'heat-shell' }, [
      el('div', { class: 'heat-y' }, ys.map((y) => el('span', {}, [String(y)]))),
      el('div', {}, [
        grid,
        el('div', { class: 'heat-x', style: 'grid-template-columns:repeat(' + xs.length + ',minmax(0,1fr))' },
           xs.map((x) => el('span', {}, [String(x)]))),
        el('div', { class: 'axis-cap' }, ['ρ  coaching effectiveness']),
      ]),
    ]),
    el('div', { class: 'axis-cap', style: 'margin-top:2px' }, ['λ  structural overlap rate (rows, top to bottom)']),
    el('div', { class: 'legend' }, [
      el('span', { html: '<i style="background:rgba(var(--heat-pos),.86)"></i>declared context helps' }),
      el('span', { html: '<i style="background:rgba(var(--heat-neg),.86)"></i>declared context hurts' }),
      el('span', { html: '<i style="background:repeating-linear-gradient(45deg,transparent,transparent 3px,var(--hairline-strong) 3px,var(--hairline-strong) 4.4px);border:1px solid var(--hairline)"></i>CI includes zero — not significant' }),
    ]),
    readout,
  ]));

  root.append(el('div', { class: 'callout warn' }, [
    el('p', { html: 'Hatched cells are part of the result, not missing data. They are exactly the regions where a payment network should <b>not</b> spend money collecting this field.' })]));

  const rs = D.phase.rho_star[key] || [];
  if (rs.length) {
    root.append(el('h3', {}, ['ρ*, the coaching level at which the signal stops paying']));
    root.append(el('div', { class: 'grid g2' }, [
      el('div', { class: 'panel' }, [table(
        ['λ structural overlap', 'ρ* bracket', 'Reading'],
        rs.map((r) => [
          String(r.lam),
          el('b', {}, [r.status === 'never significant' ? '< 0.0'
            : r.status === 'significant throughout' ? '> 1.0'
            : r.rho_star_lo + ' – ' + r.rho_star_hi]),
          el('span', { style: 'color:var(--muted)' }, [
            r.status === 'never significant' ? 'no measurable value at any coaching level'
              : r.status === 'significant throughout' ? 'no coaching level in range removes the signal'
              : 'value disappears between these two grid points']
            .concat(r.non_monotonic ? [el('span', { class: 'tag mid', style: 'margin-left:8px' }, ['non-monotonic ' + r.significant_grid])] : [])),
        ]))]),
      el('div', { class: 'callout', style: 'margin:0' }, [
        el('p', { html: 'ρ* is <b>bracketed by the sweep grid</b>, not interpolated. It lies between the last coaching level whose CI clears zero on every seed and the first that does not. A finer number would be an interpolation this design does not support.' }),
        el('p', { html: 'This is a threshold under <b>our specified threat model and parameterisation</b>. It is not a universal fact about payment fraud and should never be quoted as one.' }),
      ]),
    ]));
  }

  const ab = D.phase.ablation || [];
  if (ab.length) {
    const order = ['B1', 'B1+B2', 'B1+B2+B3', 'B1+B2+B3+B4a', 'B1+B2+B3+B4b'];
    const rows = order.map((arm) => {
      const g = ab.filter((r) => r.arm === arm);
      if (!g.length) return null;
      const mean = (k) => g.reduce((s, r) => s + r[k], 0) / g.length;
      return [
        arm === 'B1+B2+B3' ? el('b', {}, [arm + '  ← baseline']) : arm,
        String(g[0].n_features), mean('pr_auc').toFixed(4),
        mean('recall@fpr=0.001').toFixed(4),
      ];
    }).filter(Boolean);
    root.append(el('h3', {}, ['Ablation at ρ = 0.4, λ = 0.10, averaged over three seeds']));
    root.append(el('div', { class: 'panel' }, [
      table(['Arm', 'Features', 'PR-AUC', 'Recall @ FPR 0.1%'], rows, [1, 2, 3]),
      el('p', { style: 'font-size:12px;color:var(--muted);margin:12px 0 0' }, [
        'Recall at 0.5% and 1% FPR is saturated near 1.0 for the B4 arms, so those two pre-registered operating points carry little information. They were not changed after seeing results — the saturation is reported instead.']),
    ]));
  }
}

/* ---------------- screen 3 ---------------- */
const BUCKETS = [
  { id: 'helps', label: 'It helped', blurb: 'Fraud the consistency signal moved up the review queue.' },
  { id: 'misleads_missed_fraud', label: 'It pushed fraud down', blurb: 'Fraud the signal made look more ordinary. A failure case.' },
  { id: 'misleads_false_alarm', label: 'It raised a false alarm', blurb: 'Legitimate payments the signal moved up the queue. A failure case.' },
  { id: 'confirms', label: 'It changed nothing', blurb: 'Ordinary legitimate payments where the signal added no information.' },
];
let insState = { bucket: 'helps', idx: 0 };

function screenInspector(root) {
  root.replaceChildren();
  root.append(el('div', { class: 'eyebrow' }, ['Consistency inspector']));
  root.append(el('h2', {}, ['Does this beneficiary look like the beneficiaries people normally send this purpose to?']));
  root.append(el('p', { class: 'lede' }, [
    'The reference distribution is estimated per purpose class on training legitimate payments only. The label is used in exactly one place — to exclude known fraud from the reference set — which is what a bank does when it builds a profile from confirmed-good history. Every residual below is a distance between a beneficiary and a purpose, not a beneficiary feature.']));

  if (!D.inspector) { root.append(pending('The consistency inspector', 'make inspector')); return; }

  root.append(el('div', { class: 'controls' }, [
    seg('Case type', BUCKETS, insState.bucket,
        (id) => { insState.bucket = id; insState.idx = 0; screenInspector(root); })]));
  const meta = BUCKETS.find((b) => b.id === insState.bucket);
  root.append(el('p', { style: 'color:var(--muted);font-size:13px;margin-top:-6px' }, [meta.blurb]));

  const cases = D.inspector.cases.filter((c) => c.bucket === insState.bucket);
  if (!cases.length) { root.append(el('div', { class: 'panel' }, ['No cases in this bucket.'])); return; }
  const c = cases[Math.min(insState.idx, cases.length - 1)];

  root.append(el('div', { class: 'seg', style: 'margin-bottom:14px' },
    cases.map((_, i) => el('button', {
      type: 'button', 'aria-pressed': String(i === insState.idx),
      onclick: () => { insState.idx = i; screenInspector(root); },
    }, [String(i + 1)]))));

  const rows = D.inspector.b3_cols
    .map((k) => ({ k: k.replace(/^payee_/, '').replace(/^payer_payee_/, 'pair_').replace(/_/g, ' '), z: c.residuals[k] }))
    .sort((a, b) => Math.abs(b.z) - Math.abs(a.z)).slice(0, 9);
  const zmax = Math.max(...rows.map((r) => Math.abs(r.z)), 1);
  const bars = el('div', { class: 'resid' }, rows.map((r) => {
    const w = (Math.abs(r.z) / zmax) * 50;
    const strong = Math.abs(r.z) > 1.5;
    return el('div', { class: 'r' }, [
      el('div', { class: 'name' }, [r.k]),
      el('div', { class: 'track' }, [
        el('div', { class: 'mid' }),
        el('div', { class: 'bar', style: 'background:' + (strong ? 'var(--negative)' : 'var(--accent)') + ';' +
          (r.z >= 0 ? 'left:50%;width:' + w + '%' : 'right:50%;width:' + w + '%') }),
      ]),
      el('div', { class: 'val' }, [sign(r.z, 2)]),
    ]);
  }));

  root.append(el('div', { class: 'grid g2' }, [
    el('div', { class: 'panel' }, [
      table(['Field', 'Value'], [
        ['declared purpose', el('b', {}, [c.declared_purpose])],
        ['amount', fmtINR(c.amount)],
        ['channel', c.channel],
        ['beneficiary role', el('span', { class: 'mono', style: 'font-size:12px' }, [c.payee_role])],
        ['ground truth', c.is_fraud
          ? el('span', { class: 'tag no' }, ['fraud' + (c.scam_type ? ' · ' + c.scam_type : '')])
          : el('span', { class: 'tag ok' }, ['legitimate'])],
        ['reference class size', c.reference_n.toLocaleString() + (c.reference_is_fallback ? ' (global fallback)' : '')],
        ['Mahalanobis distance', c.consistency_mahalanobis.toFixed(2)],
      ], [1]),
      el('div', { class: 'grid', style: 'grid-template-columns:repeat(3,1fr);margin-top:16px;text-align:center' }, [
        metric(c.score_base.toFixed(4), 'B1+B2+B3'),
        metric(c.score_b4b.toFixed(4), '+ B4b'),
        metric(sign(c.rank_shift * 100, 2), 'rank percentile shift', null,
               (c.rank_shift > 0) === (c.is_fraud === 1) ? 'pos' : 'neg'),
      ]),
    ]),
    el('div', { class: 'panel' }, [
      el('div', { class: 'ctl-label' }, ['Deviation from the purpose-conditional legitimate reference']),
      bars,
      el('p', { style: 'font-size:11.5px;color:var(--muted);margin:14px 0 0' }, [
        'Standard deviations from the reference mean. Zero is typical for this purpose; bars beyond 1.5σ are highlighted.']),
    ]),
  ]));

  root.append(el('div', { class: 'callout warn' }, [
    el('p', { html: 'Two of the four case types above are <b>failure cases</b>, and they are shown by default rather than hidden. A consistency signal that helps on average still moves individual decisions in the wrong direction, and a reviewer deciding whether to collect this field needs to see both.' })]));
}

/* ---------------- screen 4 ---------------- */
const CHECK_LABEL = {
  C1_amount_scope: 'amount within cap', C2_category_scope: 'MCC within allowed set',
  C3_merchant_scope: 'merchant within allowed set', C4_temporal_validity: 'inside validity window',
  C5_nonce_freshness: 'nonce fresh', C6_cumulative_cap: 'cumulative cap',
  C7_agent_binding: 'agent attestation valid', C8_confirmation_bind: 'confirmation binds line items',
  C9_revocation_state: 'not revoked', C10_mandate_sig: 'mandate signature valid',
};
let mandateIdx = 0;

function screenMandate(root) {
  root.replaceChildren();
  root.append(el('div', { class: 'eyebrow' }, ['The forward surface']));
  root.append(el('h2', {}, ['The same question, with cryptographic rather than probabilistic evidence']));
  root.append(el('p', { class: 'lede' }, [
    'A human declaration of purpose is probabilistic and possibly deceptive. A signed mandate is cryptographic and constraint-bounded. These are not the same claim and this project does not blur them — but they are the same underlying question about whether a payment matched what the payer intended.']));

  if (!D.agentic) { root.append(pending('The conformance results', 'make agentic')); return; }
  const a = D.agentic, bl = a.bounded_loss, fp = a.false_positives_on_in_scope_traffic;
  const f = a.demo_frames[mandateIdx];

  root.append(el('div', { class: 'seg', style: 'margin-bottom:16px' },
    a.demo_frames.map((fr, i) => el('button', {
      type: 'button', 'aria-pressed': String(i === mandateIdx),
      onclick: () => { mandateIdx = i; screenMandate(root); },
    }, [fr.label === 'violating' ? 'Out-of-scope purchase' : 'In-scope purchase the user did not want']))));

  root.append(el('div', { class: 'receipt' }, [
    el('div', { class: 'side mandate' }, [
      el('div', { class: 'ctl-label' }, ['Mandate']),
      el('div', { class: 'kv', html:
        '<div><span class="k">max_amount</span> <b>' + fmtINR(f.mandate.max_amount) + '</b></div>' +
        '<div><span class="k">allowed_mcc</span> [' + f.mandate.allowed_mcc.join(', ') + ']</div>' +
        '<div><span class="k">allowed_merchants</span> [' + (f.mandate.allowed_merchants || []).join(', ') + ']</div>' +
        '<div><span class="k">max_cumulative</span> ' + fmtINR(f.mandate.max_cumulative) + '</div>' +
        '<div><span class="k">valid_until</span> ' + f.mandate.valid_until.slice(0, 16).replace('T', ' ') + '</div>' }),
      el('div', { class: 'ctl-label', style: 'margin-top:20px' }, ['Agent attempts']),
      el('div', { class: 'kv', html:
        '<div><span class="k">amount</span> <b>' + fmtINR(f.attempt.amount) + '</b></div>' +
        '<div><span class="k">mcc</span> ' + f.attempt.mcc + '</div>' +
        '<div><span class="k">merchant</span> ' + f.attempt.merchant_id + '</div>' }),
    ]),
    el('div', { class: 'side verdict ' + (f.accepted ? 'pass' : 'reject') }, [
      el('div', { class: 'ctl-label' }, ['Verification']),
      el('div', { class: 'checks' }, f.checks.map((c) => el('div', {}, [
        el('span', { class: c.passed ? 'g' : 'x' }, [c.passed ? '✓' : '✗']),
        el('span', { class: 'id' }, [c.id.split('_')[0]]),
        el('span', { class: c.passed ? '' : 'fail' }, [CHECK_LABEL[c.id] || c.id]),
      ]))),
      el('div', { class: 'verdict-line ' + (f.accepted ? 'pass' : 'reject') },
         [f.accepted ? '→ PASSES' : '→ REJECTED']),
      el('div', { class: 'verdict-note' }, [f.note]),
    ]),
  ]));

  if (mandateIdx === 1) {
    root.append(el('div', { class: 'callout bad' }, [
      el('p', { html: '<b>This is the honest half of the demonstration.</b> An agent that spends inside the mandate — whether compromised or steered by a prompt injection — passes every check. Conformance checking does not detect that. It bounds the loss at the cap, and nothing more. Volunteering that limit is what makes the other eight rows credible.' })]));
  }

  root.append(el('h3', {}, ['Ten attack families against ten deterministic checks']));
  root.append(el('div', { class: 'grid g4', style: 'margin-bottom:16px' }, [
    metric(a.coverage.caught + ' / ' + a.coverage.total, 'Families caught', 'structurally, no model involved', 'pos'),
    metric(fp.false_positive_rate.toFixed(4), 'False-positive rate',
           fp.rejected + ' of ' + fp.n.toLocaleString() + ' in-scope carts rejected', 'pos'),
    metric(fmtINR(bl.mean_loss_unenforced), 'Mean loss, unenforced', 'RBI-calibrated case sizes', 'neg'),
    metric(fmtPct(bl.reduction_persistent), 'Loss reduction, enforced',
           'p95 capped at ' + fmtINR(bl.p95_persistent), 'acc'),
  ]));
  root.append(el('div', { class: 'panel' }, [table(
    ['ID', 'Attack family', 'Caught by', 'Outcome'],
    a.attacks.map((x) => [
      el('span', { class: 'mono', style: 'font-weight:600' }, [x.attack_id]),
      x.name,
      el('span', { class: 'mono', style: 'font-size:11.5px;color:var(--muted)' },
         [x.failed_checks.join(', ') || '—']),
      x.caught ? el('span', { class: 'tag ok' }, ['caught'])
               : el('span', { class: 'tag no' }, ['not caught — ' + x.note]),
    ]))]));
  root.append(el('div', { class: 'callout' }, [
    el('p', { html: '<b>A9 and A10 are the most important rows in that table.</b> They are uncaught by construction, not by omission, and they are the direct answer to “AP2 already specifies mandate verification”: the contribution is not the checks, it is the measurement of what they do and do not buy.' })]));

  root.append(el('h3', {}, ['Bounded loss on the families it cannot catch']));
  root.append(el('div', { class: 'panel' }, [table(
    ['Scenario', 'Mean loss', 'p95 loss', 'Reduction'],
    [['No mandate enforcement', fmtINR(bl.mean_loss_unenforced), fmtINR(bl.p95_unenforced), '—'],
     ['Enforced, single cart', fmtINR(bl.mean_loss_single_cart), fmtINR(bl.cap), fmtPct(bl.reduction_single_cart)],
     ['Enforced, persistent attacker', fmtINR(bl.mean_loss_persistent), fmtINR(bl.p95_persistent), fmtPct(bl.reduction_persistent)]],
    [1, 2, 3])]));
}

/* ---------------- screen 5 ---------------- */
function screenMethods(root) {
  root.replaceChildren();
  root.append(el('div', { class: 'eyebrow' }, ['Methods and limitations']));
  root.append(el('h2', {}, ['Read this before the results']));

  const lims = [
    ['No labelled public APP dataset exists.', 'Every number here comes from a simulator. We make no claim about absolute detection rates; the results characterise relative behaviour across parameter regimes.'],
    ['Absolute performance is higher than any deployed system.', 'Session telemetry was deliberately made strong so the baseline would not be a strawman, and recall at 0.5% and 1% FPR is consequently saturated for the B4 arms. Those operating points were not changed after seeing results.'],
    ['Production systems already capture much of B2 and B3.', 'The experiment asks the narrower question of whether a further signal earns its collection cost once those are in place.'],
    ['The consumer population rate of <Purp> is unverified.', 'That the field exists is established. How often it is populated on consumer flows, and whether it survives end-to-end, is not.'],
    ['Results are conditional on the generative model.', 'ρ* is a property of this simulator under this threat model and parameterisation. Not a universal threshold.'],
    ['The ρ mechanism is one adversary among many.', 'An adversary who also controls which mule receives the payment, choosing one whose profile matches the declared purpose, is not modelled.'],
    ['The agentic module bounds loss; it does not detect intent.', 'Two of ten families pass every check by construction.'],
    ['The generative model was corrected after pre-registration.', 'CHANGELOG.md records every change, what prompted it, and why it is a realism correction. PREREGISTRATION.md has never been edited.'],
  ];
  root.append(el('div', { class: 'panel' }, [table(['Limitation', 'Detail'],
    lims.map(([a, b]) => [el('span', { style: 'font-weight:500' }, [a]), b]))]));

  root.append(el('h3', {}, ['The circularity objection, answered before it is asked']));
  root.append(el('div', { class: 'callout' }, [
    el('p', { html: 'We plant context metadata, so we make <b>no claim about absolute detection rates</b>. What is not circular: the deterministic results are structural, the phase diagram measures relative behaviour across parameter regimes rather than a point estimate, and we have published the generative process so the partition can be challenged. We are characterising when a control is worth deploying, not claiming a benchmark win.' })]));

  if (D.fidelity) {
    const f = D.fidelity, ca = f.case_level_asymmetry;
    root.append(el('h3', {}, ['Fidelity scorecard']));
    root.append(el('div', { class: 'grid g2' }, [
      el('div', { class: 'panel' }, [table(['Quantity', 'Observed', 'Anchor', '|err|'],
        Object.keys(ca.anchor).map((k) => [
          k.replace(/_/g, ' '),
          ca.observed[k].toFixed(k.includes('inr') ? 0 : 4),
          ca.anchor[k].toFixed(k.includes('inr') ? 0 : 4),
          ca.abs_error[k].toFixed(k.includes('inr') ? 0 : 4)]), [1, 2, 3])]),
      el('div', { class: 'panel' }, [table(['Structural statistic', 'Value'], [
        ['payee in-degree CCDF log-log slope', f.degree_distribution.ccdf_loglog_slope.toFixed(2)],
        ['median / max payee in-degree', f.degree_distribution.median_in_degree.toFixed(0) + ' / ' + f.degree_distribution.max_in_degree.toLocaleString()],
        ['median inter-transaction gap', f.inter_transaction_times.median_days.toFixed(2) + ' days'],
        ['share of gaps under a day', fmtPct(f.inter_transaction_times.share_under_1_day)],
        ['max |corr| between distinct B3 features', f.b3_redundancy.max_abs_corr.toFixed(3)],
        ['latent recovery (Spearman)', f.latent_recovery.spearman.toFixed(3)],
      ], [1])]),
    ]));
    root.append(el('p', { class: 'notrun', style: 'margin-top:14px' }, [
      'Not run: ' + f.not_run.discriminator_auc_vs_real_data]));
  }

  root.append(el('h3', {}, ['Scope']));
  root.append(el('div', { class: 'panel' }, [table(['Rule', 'What it means here'], [
    ['Synthetic data only', 'No real payment data, no real accounts, no personal data of any kind.'],
    ['No live-system testing', 'Nothing contacts a payment network, bank, merchant, or agent platform.'],
    ['No operational attack tooling', 'The attack families construct malformed mandates against a local verifier with locally generated keys.'],
    ['Primary sources only', 'RBI, ISO 20022, AP2, BIS Nexus and named public statistics. No aggregators.'],
    ['Report the negative result', 'A clean characterisation of when the control does not pay is the result, not a failure.'],
  ])]));
}

/* ---------------- router ---------------- */
const SCREENS = [
  { id: 's-question', label: 'The question', render: screenQuestion },
  { id: 's-phase', label: 'Phase diagram', render: screenPhase },
  { id: 's-inspector', label: 'Consistency inspector', render: screenInspector },
  { id: 's-mandate', label: 'Mandate check', render: screenMandate },
  { id: 's-methods', label: 'Methods & limits', render: screenMethods },
];
const rendered = new Set();
const navEl = document.getElementById('nav');

function show(id) {
  SCREENS.forEach((s) => {
    const sec = document.getElementById(s.id);
    sec.hidden = s.id !== id;
    navEl.querySelector('[data-id="' + s.id + '"]').setAttribute('aria-current', String(s.id === id));
  });
  if (!rendered.has(id)) {
    SCREENS.find((s) => s.id === id).render(document.getElementById(id));
    rendered.add(id);
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
}

SCREENS.forEach((s, i) => navEl.append(el('button', {
  type: 'button', 'data-id': s.id, 'aria-current': String(i === 0), onclick: () => show(s.id),
}, [el('span', { class: 'n' }, [String(i + 1).padStart(2, '0')]), s.label])));

show('s-question');
</script>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    OUT.write_text(html)
    print(f"written -> {OUT}  ({len(html)/1024:.0f} KB)")
