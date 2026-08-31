"""Build the public site: one self-contained HTML file, no server.

Progressive by design. A cold reader meets the findings, then the problem, the
idea, and the method, before any statistics. The mechanisms that prose reads
badly - why every bank control passes, what the consistency check actually
compares, why purpose cannot proxy the label, what each attacker controls, and
the trade-off the strongest attacker cannot escape - are drawn rather than
described.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RES = Path("results")
OUT = Path("web/site/index.html")


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
    if not phase:
        return None
    return {"arm": phase["arm"], "metrics": phase["metrics"],
            "rho_star": phase["rho_star"]}


def slim_inspector(ins):
    if not ins:
        return None
    keep = {"bucket", "is_fraud", "declared_purpose", "payee_role", "amount",
            "rank_shift", "residuals"}
    return {"b3_cols": ins["b3_cols"],
            "cases": [{k: v for k, v in c.items() if k in keep} for c in ins["cases"]]}


def build() -> str:
    data = {
        "phase": slim_phase(load("phase_surface.json")),
        "scorer": load("scorer.json"),
        "agentic": load("agentic_conformance.json"),
        "inspector": slim_inspector(load("inspector.json")),
        "meta": {
            "prereg_commit": (git("log", "--reverse", "--format=%H", default="") or "")[:40],
            "built": datetime.now(timezone.utc).strftime("%d %B %Y"),
            "n_cells": len(list((RES / "raw").glob("*.json"))) if (RES / "raw").exists() else 0,
        },
    }
    return TEMPLATE.replace("__PRAMANA_DATA__",
                            json.dumps(data, separators=(",", ":"), default=str))


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pramana — when is declared payment context worth collecting?</title>
<meta name="description" content="A pre-registered adversarial study of whether asking a payer what a payment is for helps detect scam fraud, and how much coaching that signal survives.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#f7f6f3; --surface:#fff; --raised:#fbfaf7; --sunk:#efedE7;
  --ink:#15171c; --ink-soft:#3d434e; --muted:#697080;
  --line:#e3e1da; --line-2:#cfccc4;
  --accent:#1d3b73; --accent-soft:#e9eef7; --accent-ink:#1d3b73;
  --pos:#1a6b4b; --pos-soft:#e6f2ec; --neg:#a52f24; --neg-soft:#f9ebe9;
  --warn:#8a6320; --warn-soft:#faf2e3;
  --heat-pos:29,59,115; --heat-neg:165,47,36;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#131519; --surface:#1b1e24; --raised:#21252b; --sunk:#0e1013;
  --ink:#eaebef; --ink-soft:#c6cbd4; --muted:#98a0af;
  --line:#292d35; --line-2:#3a3f4a;
  --accent:#7ba3de; --accent-soft:#1a2540; --accent-ink:#a9c4ea;
  --pos:#5fbf92; --pos-soft:#14291f; --neg:#e58278; --neg-soft:#2c1a18;
  --warn:#d9ac5c; --warn-soft:#282116;
  --heat-pos:123,163,222; --heat-neg:229,130,120;}}
:root[data-theme="dark"]{
  --ground:#131519; --surface:#1b1e24; --raised:#21252b; --sunk:#0e1013;
  --ink:#eaebef; --ink-soft:#c6cbd4; --muted:#98a0af;
  --line:#292d35; --line-2:#3a3f4a;
  --accent:#7ba3de; --accent-soft:#1a2540; --accent-ink:#a9c4ea;
  --pos:#5fbf92; --pos-soft:#14291f; --neg:#e58278; --neg-soft:#2c1a18;
  --warn:#d9ac5c; --warn-soft:#282116;
  --heat-pos:123,163,222; --heat-neg:229,130,120;}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans",ui-sans-serif,system-ui,-apple-system,sans-serif;
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:Spectral,Georgia,serif;margin:0;text-wrap:balance}
.mono{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}
a{color:var(--accent-ink)}
.wrap{max-width:1140px;margin:0 auto;padding:0 32px}
.col{max-width:660px}
@media(max-width:760px){.wrap{padding:0 20px}}

/* nav */
.bar{position:sticky;top:0;z-index:40;background:var(--surface);border-bottom:1px solid var(--line)}
.bar .wrap{display:flex;align-items:center;gap:22px;min-height:56px}
.brand{display:flex;align-items:baseline;gap:8px;cursor:pointer;flex-shrink:0}
.brand b{font-family:Spectral,Georgia,serif;font-size:21px;font-weight:700}
.brand i{font-size:11px;color:var(--muted);font-family:Spectral,Georgia,serif}
@media(max-width:900px){.brand i{display:none}}
.tabs{display:flex;gap:0;overflow-x:auto;margin-left:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{appearance:none;background:none;border:0;border-bottom:2px solid transparent;
  font:inherit;font-size:13px;color:var(--muted);padding:17px 12px 13px;cursor:pointer;white-space:nowrap}
.tabs button:hover{color:var(--ink)}
.tabs button[aria-current="true"]{color:var(--accent-ink);border-bottom-color:var(--accent);font-weight:500}
.tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:-3px}

/* page rhythm */
section[hidden]{display:none!important}
.pg{padding:44px 0 0}
.kicker{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.15em;
  text-transform:uppercase;color:var(--accent-ink);margin-bottom:11px}
h2.t{font-size:clamp(27px,3.6vw,36px);font-weight:600;letter-spacing:-.016em;line-height:1.15;max-width:18ch}
.lede{font-size:18px;line-height:1.55;color:var(--ink-soft);max-width:58ch;margin:16px 0 0;
  font-family:Spectral,Georgia,serif}
.sec{padding:34px 0 0}
h3.s{font-size:21px;font-weight:600;margin:0 0 12px;letter-spacing:-.008em}
p{margin:0 0 14px;max-width:62ch}
.end{padding:34px 0 64px}

/* figure */
figure{margin:22px 0;padding:0}
figure svg{display:block;width:100%;max-width:100%;height:auto;color:var(--ink)}
figcaption{font-size:13px;color:var(--muted);margin-top:12px;max-width:62ch;line-height:1.5}
.figbox{background:var(--surface);border:1px solid var(--line);border-radius:5px;padding:26px 26px 20px}

/* takeaway */
.take{display:flex;gap:14px;align-items:flex-start;background:var(--accent-soft);
  border-left:3px solid var(--accent);padding:16px 20px;border-radius:0 4px 4px 0;margin:24px 0 0}
.take.good{background:var(--pos-soft);border-left-color:var(--pos)}
.take.warn{background:var(--warn-soft);border-left-color:var(--warn)}
.take.bad{background:var(--neg-soft);border-left-color:var(--neg)}
.take .k{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.13em;
  text-transform:uppercase;color:var(--muted);padding-top:4px;flex-shrink:0;width:64px}
.take p{margin:0;max-width:58ch;font-size:15.5px}
@media(max-width:700px){.take{flex-direction:column;gap:6px}.take .k{width:auto}}

/* cards / grid */
.grid{display:grid;gap:16px}
.g2{grid-template-columns:1fr 1fr}
.g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:900px){.g2,.g3{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:5px;padding:20px}
.card h4{font-family:"IBM Plex Sans",sans-serif;font-size:15px;font-weight:600;margin:0 0 6px}
.card p{font-size:14px;color:var(--ink-soft);margin:0;max-width:none}

/* finding block */
.find{background:var(--surface);border:1px solid var(--line);border-radius:5px;
  padding:24px;display:flex;flex-direction:column;gap:0}
.find .n{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;color:var(--accent-ink)}
.find h4{font-family:Spectral,Georgia,serif;font-size:19px;font-weight:600;margin:10px 0 9px;line-height:1.25}
.find p{font-size:14px;color:var(--ink-soft);margin:0;max-width:none}
.find .num{font-family:"IBM Plex Mono",monospace;font-size:21px;margin-top:16px;
  padding-top:14px;border-top:1px solid var(--line);font-variant-numeric:tabular-nums}
.find .cap{font-size:12px;color:var(--muted);margin-top:4px;line-height:1.4}

/* table */
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
  font-weight:600;padding:9px 12px;border-bottom:1px solid var(--line-2);white-space:nowrap}
td{padding:9px 12px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
td.r,th.r{text-align:right}
.pill{font-size:11px;padding:2px 8px;border-radius:3px;font-weight:600;display:inline-block}
.pill.ok{background:var(--pos-soft);color:var(--pos)}
.pill.no{background:var(--neg-soft);color:var(--neg)}

/* controls */
.seg{display:flex;gap:6px;flex-wrap:wrap}
.seg button{appearance:none;font:inherit;font-size:12.5px;padding:7px 13px;cursor:pointer;
  background:var(--surface);color:var(--ink);border:1px solid var(--line-2);border-radius:3px}
.seg button:hover{border-color:var(--accent)}
.seg button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--ground)}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.lbl{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  font-weight:600;margin-bottom:8px}

/* buttons */
.nav{display:flex;gap:12px;flex-wrap:wrap;padding-top:30px;border-top:1px solid var(--line);margin-top:36px}
.btn{appearance:none;font:inherit;font-size:14px;font-weight:500;cursor:pointer;padding:11px 20px;
  border-radius:4px;border:1px solid var(--line-2);background:var(--surface);color:var(--ink)}
.btn:hover{border-color:var(--accent);color:var(--accent-ink)}
.btn.p{background:var(--accent);border-color:var(--accent);color:var(--ground)}
.btn.p:hover{opacity:.9;color:var(--ground)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.note{font-size:13px;color:var(--muted);max-width:62ch;margin-top:18px}
.hero{font-family:Spectral,Georgia,serif;font-size:clamp(30px,4.6vw,46px);font-weight:600;
  letter-spacing:-.02em;line-height:1.1;max-width:17ch;margin:14px 0 0}
.lede{font-size:18px;line-height:1.6;color:var(--ink-soft);max-width:60ch;margin:20px 0 0}
.heroactions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}
.blk{padding:64px 0;border-top:1px solid var(--line)}
.blk:first-child{border-top:0;padding-top:40px}
.hero{margin-bottom:0}
#s-top .lede{margin-bottom:30px}
#s-top,#s-break{background:var(--surface)}
.blk .num{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;
  color:var(--accent-ink);margin-bottom:10px}
h2.t{font-size:clamp(24px,3vw,31px);font-weight:600;letter-spacing:-.014em;line-height:1.2;max-width:20ch;margin:0}
.sub{font-size:16.5px;color:var(--ink-soft);max-width:62ch;margin:14px 0 26px}
.stats{margin-top:24px}
.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:1000px){.g4{grid-template-columns:1fr 1fr}}
@media(max-width:640px){.g4{grid-template-columns:1fr}}
.stat{background:var(--ground);border:1px solid var(--line);border-radius:5px;padding:18px 20px}
#s-answer .stat,#s-break .stat{background:var(--raised)}
.stat .v{font-family:"IBM Plex Mono",monospace;font-size:26px;font-weight:500;line-height:1;
  font-variant-numeric:tabular-nums;color:var(--accent-ink)}
.stat .l{font-size:13.5px;font-weight:600;margin-top:10px}
.stat .s{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.45}
.jump{position:sticky;top:0;z-index:40;background:var(--surface);border-bottom:1px solid var(--line)}
.jump .wrap{display:flex;align-items:center;gap:20px;min-height:54px}
.jump .brand{display:flex;align-items:baseline;gap:8px;flex-shrink:0;cursor:pointer}
.jump .brand b{font-family:Spectral,Georgia,serif;font-size:20px;font-weight:700}
.jump .brand i{font-size:11px;color:var(--muted);font-family:Spectral,Georgia,serif}
@media(max-width:820px){.jump .brand i{display:none}}
.jump nav{display:flex;gap:2px;margin-left:auto;overflow-x:auto;scrollbar-width:none}
.jump nav::-webkit-scrollbar{display:none}
.jump nav a{font-size:13px;color:var(--muted);text-decoration:none;padding:8px 11px;
  border-radius:3px;white-space:nowrap}
.jump nav a:hover{color:var(--ink);background:var(--raised)}
.jump nav a.cta{background:var(--accent);color:var(--ground);font-weight:500}
.jump nav a.cta:hover{opacity:.9;color:var(--ground)}

.verify{padding-bottom:12px;margin-bottom:12px;border-bottom:1px solid var(--line);color:var(--ink-soft)}
.verify b{color:var(--ink)}
.verify .mono{font-size:11.5px;background:var(--sunk);padding:1px 6px;border-radius:3px}
.land{min-height:calc(100vh - 56px);display:flex;align-items:center;background:var(--surface);padding:40px 0}
.askclick{text-align:center;margin-top:22px}
.askmain{font-size:16px;font-weight:600}
.asksub{font-size:13px;color:var(--muted);margin-top:5px}
.pickme{font-size:12px;color:var(--accent-ink);font-weight:600;border:1px solid var(--accent);
  padding:3px 9px;border-radius:20px}
.onward{display:flex;gap:12px;flex-wrap:wrap;padding:36px 0 70px}
.jump.onhome nav a.cta{animation:none}
.btn.big{font-size:15px;padding:14px 26px}
.trust{display:flex;gap:26px;flex-wrap:wrap;margin-top:34px;padding-top:22px;
  border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
.trust b{color:var(--ink);font-family:"IBM Plex Mono",monospace}
.prog{display:flex;gap:6px;padding:26px 0 0}
.seg-dot{height:4px;flex:1;background:var(--line);border-radius:2px}
.seg-dot.done{background:var(--accent);opacity:.45}
.seg-dot.now{background:var(--accent)}
.qwrap{max-width:760px;padding-top:34px}
.qnum{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.15em;
  text-transform:uppercase;color:var(--accent-ink);margin-bottom:12px}
.qtitle{font-family:Spectral,Georgia,serif;font-size:clamp(24px,3.4vw,32px);font-weight:600;
  line-height:1.2;letter-spacing:-.014em;max-width:20ch}
.qhint{font-size:14.5px;color:var(--muted);max-width:56ch;margin-top:12px}
.qopts{display:flex;flex-direction:column;gap:9px;margin-top:26px;max-width:560px}
.qopt{appearance:none;font:inherit;font-size:15.5px;text-align:left;padding:15px 20px;cursor:pointer;
  background:var(--surface);color:var(--ink);border:1.5px solid var(--line);border-radius:6px;transition:border-color .1s}
.qopt:hover{border-color:var(--accent)}
.qopt.sel{border-color:var(--accent);background:var(--accent-soft);font-weight:500}
.qopt:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.expl{display:flex;flex-direction:column;gap:14px;margin-top:20px}
.exrow{display:grid;grid-template-columns:132px 1fr;gap:18px;align-items:center}
.exbar{height:26px;background:var(--sunk);border-radius:4px;overflow:hidden}
.exbar div{height:100%;background:var(--accent);border-radius:4px}
.exq{font-size:15px;font-weight:500}
.exs{font-size:13px;color:var(--muted);margin-top:2px}
@media(max-width:640px){.exrow{grid-template-columns:80px 1fr;gap:12px}}
table.cmp{border-collapse:collapse;width:100%;font-size:14px;background:var(--surface);
  border:1px solid var(--line);border-radius:5px;overflow:hidden}
table.cmp th{font-size:13px;text-transform:none;letter-spacing:0;color:var(--ink);font-weight:600;
  padding:16px 18px;vertical-align:bottom;border-bottom:1.5px solid var(--line-2);background:var(--raised)}
table.cmp th:first-child{color:var(--muted);font-weight:500}
table.cmp td{padding:15px 18px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.45}
table.cmp td:first-child{color:var(--muted);font-weight:500;width:30%}
table.cmp tr.verdict td{background:var(--raised);border-bottom:0}
@media(max-width:760px){table.cmp{font-size:13px}table.cmp th,table.cmp td{padding:11px 12px}}
.find.click{cursor:pointer;transition:border-color .12s,transform .12s}
.find.click:hover{border-color:var(--accent)}
.find.click:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.find .more{font-size:12.5px;color:var(--accent-ink);margin-top:12px;font-weight:500}
.foot{border-top:1px solid var(--line);background:var(--surface);margin-top:20px}
.foot .wrap{padding:20px 32px;font-size:12.5px;color:var(--muted);max-width:1140px;line-height:1.55}
input[type=range]{accent-color:var(--accent);height:22px}
input[type=checkbox]{accent-color:var(--accent);width:15px;height:15px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

</style>
</head>
<body>
<div class="jump"><div class="wrap">
  <div class="brand" id="brand" role="button" tabindex="0"><b>Pramana</b><i>a valid means of proof</i></div>
  <nav>
    <a href="#problem" data-v="problem">The problem</a>
    <a href="#how" data-v="how">How it works</a>
    <a href="#found" data-v="found">What we found</a>
    <a href="#ai" data-v="ai">AI payments</a>
    <a href="#tool" data-v="tool" class="cta">Try it now</a>
  </nav>
</div></div>
<main id="main"></main>
<footer class="foot"><div class="wrap">
  <div class="verify">
    <b>Check the work.</b> The research question, the features and the condition under which we
    would call the idea a failure were committed <em>before</em> the simulator existed, in commit
    <span class="mono" id="pcommit"></span>, which has never been edited.
    Verify with <span class="mono">git log --reverse --stat</span> in
    <span class="mono">github.com/aakanksha-singh-hub/pramana</span> —
    the repository also holds the 20-page write-up, the data and model cards, and the full
    generative process.
  </div>
  <b>Simulated data only.</b> No production, cardholder or personal data was used, and no live
  system was tested. All figures are like-for-like comparisons under identical conditions, not
  benchmarks of deployed performance.
</div></footer>
<script>
const D = __PRAMANA_DATA__;
/* ---------- shared bits ---------- */
const el=(t,a={},k=[])=>{const n=document.createElement(t);
  for(const[key,v]of Object.entries(a)){if(v===null||v===undefined||v===false)continue;
    if(key==='class')n.className=v;else if(key==='html')n.innerHTML=v;
    else if(key.startsWith('on'))n.addEventListener(key.slice(2),v);else n.setAttribute(key,v===true?'':v);}
  for(const c of [].concat(k)){if(c===null||c===undefined||c===false)continue;
    n.append(c.nodeType?c:document.createTextNode(c));}return n;};
const inr=v=>'₹'+Math.round(v).toLocaleString('en-IN');
const sgn=(v,d=4)=>(v>=0?'+':'')+v.toFixed(d);
const W=(k,cls='')=>el('div',{class:'wrap '+cls},[].concat(k));
const COL=(k)=>el('div',{class:'wrap'},[el('div',{class:'col'},[].concat(k))]);
const p=t=>el('p',{html:t});
const h3=t=>el('h3',{class:'s'},[t]);
const sec=k=>el('div',{class:'sec'},[].concat(k));
const take=(label,html,kind='')=>el('div',{class:'take '+kind},[
  el('div',{class:'k'},[label]),el('p',{html})]);
const card=(t,x)=>el('div',{class:'card'},[el('h4',{},[t]),el('p',{html:x})]);
function tbl(hd,rows,right=[]){const t=el('table');
  t.append(el('thead',{},[el('tr',{},hd.map((h,i)=>el('th',{class:right.includes(i)?'r':''},[h])))]));
  t.append(el('tbody',{},rows.map(r=>el('tr',{},r.map((c,i)=>el('td',{class:right.includes(i)?'r':''},[c]))))));
  return el('div',{class:'scroll'},[t]);}
function segCtl(label,opts,cur,pick){return el('div',{},[el('div',{class:'lbl'},[label]),
  el('div',{class:'seg'},opts.map(o=>el('button',{type:'button','aria-pressed':String(o.id===cur),
    onclick:()=>pick(o.id)},[o.label])))]);}
const head=(k,t,l)=>el('div',{class:'pg'},[el('div',{class:'wrap'},[
  el('div',{class:'kicker'},[k]),el('h2',{class:'t'},[t]),l?el('p',{class:'lede'},[l]):null])]);
function nav(prev,next){const b=el('div',{class:'nav'});
  if(prev)b.append(el('button',{class:'btn',type:'button',onclick:()=>show(prev.id)},['← '+prev.label]));
  if(next)b.append(el('button',{class:'btn p',type:'button',onclick:()=>show(next.id)},[next.label+' →']));
  return el('div',{class:'wrap end'},[b]);}


const AR='<defs><marker id="ar" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="7" orient="auto"><path d="M0 0 L10 4 L0 8 z" fill="currentColor"/></marker>'+
'<marker id="arN" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="7" orient="auto"><path d="M0 0 L10 4 L0 8 z" style="fill:var(--neg)"/></marker>'+
'<marker id="arP" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="8" markerHeight="7" orient="auto"><path d="M0 0 L10 4 L0 8 z" style="fill:var(--pos)"/></marker></defs>';

function fig(svg,caption,aria,boxed=true){
  const f=el('figure',{});
  const holder=el('div',{class:boxed?'figbox':''});
  holder.innerHTML='<svg viewBox="'+svg.vb+'" role="img" aria-label="'+aria.replace(/"/g,'&quot;')+'">'+AR+svg.body+'</svg>';
  f.append(holder);
  f.append(el('figcaption',{html:caption}));
  return f;
}
const T=(x,y,s,o={})=>'<text x="'+x+'" y="'+y+'" text-anchor="'+(o.a||'middle')+'" font-size="'+(o.s||12.5)+
  '" font-weight="'+(o.w||400)+'" style="fill:'+(o.c||'currentColor')+'" font-family="'+(o.f||'IBM Plex Sans, sans-serif')+'">'+s+'</text>';
const BOX=(x,y,w,h,o={})=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="'+(o.r||4)+
  '" style="fill:'+(o.fill||'var(--surface)')+';stroke:'+(o.stroke||'var(--line-2)')+';stroke-width:'+(o.sw||1.2)+
  (o.dash?';stroke-dasharray:'+o.dash:'')+'"/>';
const LINE=(x1,y1,x2,y2,o={})=>'<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+
  '" style="stroke:'+(o.c||'currentColor')+';stroke-width:'+(o.w||1.4)+(o.dash?';stroke-dasharray:'+o.dash:'')+
  '" '+(o.m?'marker-end="url(#'+o.m+')"':'')+'/>';

/* 1 — every control passes */


/* 2 — the consistency check */


/* 3 — three independent processes */
function figProcesses(){
  let s='';const bw=232,bh=76,y=34;
  const b=[['Account role','decides how a recipient behaves'],
           ['Relationship','decides what a payment is for'],
           ['Scam campaign','decides who gets targeted']];
  b.forEach((t,i)=>{const x=22+i*(bw+40);
    s+=BOX(x,y,bw,bh)+T(x+bw/2,y+30,t[0],{w:600,s:14})+T(x+bw/2,y+50,t[1],{s:11.5,c:'var(--muted)'});
    s+=LINE(x+bw/2,y+bh,x+bw/2,y+bh+34,{m:'ar'});});
  s+=BOX(22,y+bh+40,bw*3+80,44,{fill:'var(--raised)'})+
     T(22+(bw*3+80)/2,y+bh+68,'one simulated payment ledger',{w:600,s:14});
  const ay=y+30;
  s+=LINE(22+bw+18,ay,22+bw+22,ay,{c:'var(--neg)',w:0});
  s+='<g><line x1="'+(22+bw*2+40)+'" y1="'+(y+18)+'" x2="'+(22+bw+18)+'" y2="'+(y+18)+
     '" style="stroke:var(--neg);stroke-width:1.4;stroke-dasharray:5 4"/>'+
     '<line x1="'+(22+bw*1.5+29-9)+'" y1="'+(y+9)+'" x2="'+(22+bw*1.5+29+9)+'" y2="'+(y+27)+
     '" style="stroke:var(--neg);stroke-width:2"/>'+
     '<line x1="'+(22+bw*1.5+29+9)+'" y1="'+(y+9)+'" x2="'+(22+bw*1.5+29-9)+'" y2="'+(y+27)+
     '" style="stroke:var(--neg);stroke-width:2"/></g>';
  s+=T(22+bw*1.5+29,y-6,'no connection',{s:11.5,c:'var(--neg)',w:600});
  return {vb:'0 0 880 200',body:s};
}

/* 4 — the adversary ladder */
function figLadder(){
  let s='';const y0=40,rh=54,lw=250,cw=112,gap=14;
  s+=T(lw+22+cw/2,26,'the label',{s:11,c:'var(--muted)',w:600});
  s+=T(lw+22+cw*1.5+gap,26,'its statistics',{s:11,c:'var(--muted)',w:600});
  s+=T(lw+22+cw*2.5+gap*2,26,'which account',{s:11,c:'var(--muted)',w:600});
  const rows=[['A basic scammer','tells the victim what to type',1],
              ['A careful scammer','picks words that leave no statistical trace',2],
              ['One that knows the defence','also picks a recipient that fits the words',3]];
  rows.forEach((r,i)=>{const y=y0+i*(rh+gap);
    s+=T(20,y+26,r[0],{a:'start',w:600,s:13.5});
    s+=T(20,y+43,r[1],{a:'start',s:11.5,c:'var(--muted)'});
    for(let c=0;c<3;c++){const x=lw+22+c*(cw+gap),on=c<r[2];
      s+=BOX(x,y+6,cw,40,{fill:on?'var(--neg-soft)':'var(--sunk)',stroke:on?'var(--neg)':'var(--line)'});
      s+=T(x+cw/2,y+31,on?'controls':'—',{s:12,w:on?600:400,c:on?'var(--neg)':'var(--muted)'});}});
  return {vb:'0 0 880 250',body:s};
}

/* 5 — the coupling trade-off: the headline finding */



/* ================= THE HOOK — tell these two apart ================= */
const ACCT_FIELDS=[['How old the account is','318 days','202 days'],
  ['People who paid it last month','62','69'],
  ['Share of money forwarded within a day','90%','90%'],
  ['How regular the incoming payments are','low','low'],
  ['How spread out the payers are','wide','wide'],
  ['Fraud complaints on record','none','none']];
let HK={pick:null,flip:Math.random()<0.5};

function hookAccounts(){
  const box=el('div',{});
  const draw=()=>{
    box.replaceChildren();
    const scamIsA=HK.flip;              /* which card is the mule */
    const label=i=>i===0?'Account A':'Account B';
    const isScam=i=>(i===0)===scamIsA;
    const card=(i)=>{
      const picked=HK.pick===i, done=HK.pick!==null;
      const bad=done&&isScam(i), good=done&&!isScam(i);
      return el('div',{class:'card',role:done?null:'button',tabindex:done?null:'0',
        style:'cursor:'+(done?'default':'pointer')+';border-width:1.5px;border-color:'+
          (bad?'var(--neg)':good?'var(--pos)':picked?'var(--accent)':'var(--line)'),
        onclick:done?null:()=>{HK.pick=i;draw();},
        onkeydown:done?null:e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();HK.pick=i;draw();}}},[
        el('div',{style:'display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px'},[
          el('h4',{style:'margin:0'},[label(i)]),
          done?el('span',{class:'pill '+(bad?'no':'ok')},[bad?'scam collection account':'legitimate']):
               el('span',{class:'pickme'},['Click to pick this one'])]),
        el('div',{},ACCT_FIELDS.map(f=>el('div',{style:'display:flex;justify-content:space-between;gap:14px;padding:6px 0;border-bottom:1px solid var(--line);font-size:13.5px'},[
          el('span',{style:'color:var(--muted)'},[f[0]]),
          el('span',{class:'mono',style:'font-weight:500'},[isScam(i)?f[2]:f[1]])]))),
        done?el('div',{style:'margin-top:14px;padding-top:12px;border-top:1px solid var(--line)'},[
          el('div',{style:'font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent-ink);font-weight:600;margin-bottom:5px'},
            ['what payers said the money was for']),
          el('div',{style:'font-size:15px;font-weight:600'},[isScam(i)?'“family support”':'“investment”']),
          el('div',{style:'font-size:12.5px;color:var(--muted);margin-top:5px'},[
            isScam(i)?'sent by 69 unrelated strangers, each believing they were helping a relative'
                     :'a savings group — members pay in, one member is paid out each month'])]):null]);};
    box.append(el('div',{class:'grid g2'},[card(0),card(1)]));
    if(HK.pick===null){
      box.append(el('div',{class:'askclick'},[
        el('div',{class:'askmain'},['👇 Click the account you think collects the scam money']),
        el('div',{class:'asksub'},['There is no trick — the sides are shuffled every time.'])]));
    } else {
      const right=!isScam(HK.pick);
      box.append(el('div',{style:'margin-top:18px'},[
        el('div',{class:'take '+(right?'good':'bad')},[
          el('div',{class:'k'},[right?'lucky':'most people']),
          el('p',{html:right
            ?'You guessed right — but on those six fields the two accounts sit <b>0.33 standard deviations</b> apart. That is a coin flip, and a real system has to make this call millions of times a day.'
            :'So does almost everyone. On those six fields the two accounts sit <b>0.33 standard deviations</b> apart — a coin flip. These are real accounts from the simulation, chosen because they are the hardest pair to separate.'})]),
        el('div',{class:'take'},[el('div',{class:'k'},['the tell']),
          el('p',{html:'One field separates them instantly, and no payment system records it. Sixty-nine unrelated people do not all send <b>family support</b> to the same collection account — but they absolutely do all send <b>investment</b> to a savings group. The account cannot lie about its own history, and the payer has no reason to lie about what they think they are doing.'})]),
        el('div',{style:'text-align:center;margin-top:14px'},[
          el('button',{class:'btn',type:'button',onclick:()=>{HK.pick=null;HK.flip=Math.random()<0.5;draw();}},
            ['Try again with the sides swapped'])])]));
    }};
  draw();
  return box;}


/* ================= PAGE 1 — START ================= */


/* ================= PAGE 2 — FINDINGS ================= */



/* ================= PAGE 3 — TRY IT ================= */
let TRY='decide';
function pTry(root){
  root.replaceChildren();
  root.append(head('Try it','Two things you can actually use',
    'Neither runs a model. The first is a lookup into experiments already done; the second is arithmetic on a signed instruction.'));
  root.append(W([el('div',{class:'seg',style:'margin-bottom:8px'},[
    el('button',{type:'button','aria-pressed':String(TRY==='decide'),onclick:()=>{TRY='decide';pTry(root);}},
      ['Should you collect the field?']),
    el('button',{type:'button','aria-pressed':String(TRY==='sandbox'),onclick:()=>{TRY='sandbox';pTry(root);}},
      ['Break the mandate check'])])]));
  const host=el('div',{});
  root.append(host);
  (TRY==='decide'?renderDecide:renderSandbox)(host);
  root.append(nav({id:'p-findings',label:'What we found'},{id:'p-evidence',label:'The evidence'}));
}

/* ================= PAGE 4 — EVIDENCE ================= */
let evAdv='matched';
function pEvidence(root){
  root.replaceChildren();
  root.append(head('The evidence','How it was tested, and where it fails',
    'The part that decides whether any of the previous numbers mean anything.'));

  root.append(sec([COL([h3('We wrote the answer down before we ran anything'),
    p('The question, the measures, and <b>the condition under which we would call the idea a failure</b> were committed before the simulator existed. That commit has never been edited. Every later change is recorded separately with what prompted it.')]),
    W([fig(figProcesses(),
      'Three generators that never consult each other. What a payment is for is decided by the relationship; who gets scammed is decided by a separate process. Purpose is never derived from whether a payment is fraudulent, so any consistency signal has to emerge rather than be planted.',
      'Three independent generators feeding one ledger, with a crossed-out link between the purpose generator and the fraud generator')]),
    COL([p('The baseline — transaction, behavioural and recipient intelligence together — received the <b>entire</b> model-tuning effort. The new idea got none of it, so every result is a floor rather than a best case.')]),
    W([fig(figLadder(),
      'Three attackers of increasing capability. The first controls only what the victim types. The second also controls the statistics of those words. The third additionally chooses which account receives the money, and is assumed to know how the defence works.',
      'Three attacker rows showing which of the label, its statistics and the receiving account each one controls')])]));

  /* simplified surface */
  const readout=el('div',{class:'card',style:'margin-top:14px;font-size:13.5px'},
    [el('span',{style:'color:var(--muted)'},['Hover any square to read it.'])]);
  const holder=el('div',{});
  const draw=()=>{const cells=(D.phase&&D.phase.metrics[evAdv+'|recall@fpr=0.001'])||[];
    holder.replaceChildren(cells.length?heatmap2(cells,c=>readout.replaceChildren(
      el('div',{style:'font-weight:600;margin-bottom:5px'},[
        (c.significant?'It helps here.':'It does not help here.')]),
      el('div',{style:'font-size:13px;color:var(--ink-soft)'},[
        'Coaching: '+['none','light','moderate','determined','heavy','total'][[0,0.2,0.4,0.6,0.8,1].indexOf(c.rho)]+
        ' · look-alike accounts: '+['none','few','some','many','very many'][[0,0.05,0.1,0.2,0.35].indexOf(c.lam)]]),
      el('div',{class:'mono',style:'font-size:12px;color:var(--muted);margin-top:6px'},[
        'extra fraud caught '+sgn(c.delta,4)+' at a 0.1% false-alarm budget'])
    )):el('div',{},['not computed']));};
  draw();
  root.append(sec([W([h3('Every condition we tested'),
    el('p',{style:'max-width:62ch;margin-bottom:14px'},[
      'Each square is one set of conditions. Darker means the field helped more; cross-hatched means we could not tell it apart from no help at all.']),
    el('div',{style:'margin-bottom:14px'},[segCtl('Attacker',
      [{id:'uniform',label:'Coaches the victim'},{id:'prevalence',label:'Coaches carefully'},
       {id:'matched',label:'Knows the defence'}],evAdv,id=>{evAdv=id;pEvidence(root);})]),
    el('div',{class:'figbox'},[holder,readout])])]));

  /* failures */
  root.append(sec([COL([h3('Where it got individual payments wrong'),
    p('It moved some genuine payments up the review queue and pushed some real fraud down. Those cases are in the project’s worked examples, kept visible rather than filtered out.')]),
    W([el('div',{class:'grid g2'},[
      el('div',{class:'card'},[el('h4',{},['Against us']),
        el('p',{html:'Our consistency engine barely beat a plain tick-box. The strongest attacker was added after we saw the first two never broke the signal. Our two success measures disagree with each other.'})]),
      el('div',{class:'card'},[el('h4',{},['The honest ceiling']),
        el('p',{html:'It is all simulated — there is no public dataset of scam payments carrying a purpose field. So we claim nothing about absolute detection rates, only how the value moves as attackers improve.'})])])]),
    W([take('the circularity answer','We put the purpose field into the data ourselves, so we make no claim about absolute detection rates. What is not circular: the mandate results are structural arithmetic, the surface measures <em>relative</em> behaviour across conditions rather than one score, and the whole generative process is published so the design can be challenged.')])]));
  root.append(nav({id:'p-try',label:'Try it'},{id:'p-start',label:'Back to the start'}));
}

/* simplified heatmap — no numbers in the cells */
function heatmap2(cells,onPick){
  const xs=[...new Set(cells.map(c=>c.rho))].sort((a,b)=>a-b);
  const ys=[...new Set(cells.map(c=>c.lam))].sort((a,b)=>b-a);
  const max=Math.max(...cells.map(c=>Math.abs(c.delta||0)),1e-9);
  const rows=el('div',{style:'display:flex;flex-direction:column;gap:5px'});
  const LW=['very many','many','some','few','none'];
  ys.forEach((y,ri)=>{
    const r=el('div',{style:'display:grid;grid-template-columns:86px repeat('+xs.length+',minmax(0,1fr));gap:5px;align-items:center'});
    r.append(el('div',{style:'font-size:11.5px;color:var(--muted);text-align:right'},[LW[ri]]));
    xs.forEach(x=>{const c=cells.find(k=>k.rho===x&&k.lam===y);
      const n=el('div',{tabindex:'0',role:'button',
        'aria-label':(c&&c.significant?'helps':'does not help')+' at coaching '+x,
        style:'height:46px;border-radius:3px;background:'+heatColour(c?c.delta:null,max)+
          (c&&!c.significant?';background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,var(--line-2) 3px,var(--line-2) 4.5px)':'')});
      if(c){n.addEventListener('mouseenter',()=>onPick(c));n.addEventListener('focus',()=>onPick(c));}
      r.append(n);});
    rows.append(r);});
  const XW=['none','light','moderate','determined','heavy','total'];
  const axis=el('div',{style:'display:grid;grid-template-columns:86px repeat('+xs.length+',minmax(0,1fr));gap:5px;margin-top:8px'});
  axis.append(el('div',{}));
  xs.forEach((x,i)=>axis.append(el('div',{style:'font-size:11px;color:var(--muted);text-align:center'},[XW[i]])));
  return el('div',{},[rows,axis,
    el('div',{style:'font-size:12px;color:var(--muted);text-align:center;margin-top:10px'},['how hard the scammer coached the victim  →']),
    el('div',{style:'font-size:12px;color:var(--muted);text-align:center;margin-top:2px'},['rows ↓ how many legitimate accounts look like scam accounts'])]);}

function heatColour(v,max){
  if(v==null||Number.isNaN(v))return 'var(--sunk)';
  const t=Math.max(-1,Math.min(1,v/(max||1e-9)));
  const c=getComputedStyle(document.documentElement).getPropertyValue(t>=0?'--heat-pos':'--heat-neg');
  return 'rgba('+c.trim()+','+(0.08+0.85*Math.abs(t)).toFixed(3)+')';}


/* ================= SCREEN 1 — MANDATE SANDBOX ================= */
const MCCS=[['5941','sporting goods'],['5940','bicycle shops'],['5691','luxury apparel'],
            ['5944','jewellery'],['5812','restaurants']];
const SHOPS=['merch:runfast','merch:sportsdepot','merch:paceworks','merch:luxebags','merch:goldsmith'];
let SB={cap:5000,cum:12000,mccs:['5941','5940'],shops:['merch:runfast','merch:sportsdepot','merch:paceworks'],
        days:7,amount:40000,mcc:'5691',shop:'merch:luxebags',elapsed:0,spent:0,
        forge:false,tamper:false,revoked:false,replay:false};

function sbVerify(){
  const s=SB,out=[];
  out.push(['C1','amount within the cap',s.amount<=s.cap,
    s.amount<=s.cap?'':'₹'+s.amount.toLocaleString('en-IN')+' exceeds the ₹'+s.cap.toLocaleString('en-IN')+' cap']);
  out.push(['C2','category allowed',s.mccs.includes(s.mcc),
    s.mccs.includes(s.mcc)?'':'MCC '+s.mcc+' is outside {'+s.mccs.join(', ')+'}']);
  out.push(['C3','merchant allowed',s.shops.includes(s.shop),
    s.shops.includes(s.shop)?'':s.shop+' is not in the allowed list']);
  out.push(['C4','inside the validity window',s.elapsed<=s.days,
    s.elapsed<=s.days?'':'day '+s.elapsed+' is past the '+s.days+'-day window']);
  out.push(['C5','mandate not replayed',!s.replay,s.replay?'this mandate presentation was already used':'']);
  out.push(['C6','cumulative cap',(s.spent+s.amount)<=s.cum,
    (s.spent+s.amount)<=s.cum?'':'₹'+(s.spent+s.amount).toLocaleString('en-IN')+' total exceeds the ₹'+s.cum.toLocaleString('en-IN')+' cap']);
  out.push(['C7','agent attestation valid',!s.forge,s.forge?'signature does not match the delegated agent key':'']);
  out.push(['C8','matches what the user approved',!s.tamper,s.tamper?'line items changed after the user confirmed':'']);
  out.push(['C9','permission not withdrawn',!s.revoked,s.revoked?'mandate was revoked before this attempt':'']);
  out.push(['C10','mandate signature valid',true,'']);
  return out;}

function renderSandbox(root){
  root.replaceChildren();

  const redraw=()=>renderSandbox(root);
  const numIn=(label,key,min,max,step,fmt)=>el('div',{style:'margin-bottom:14px'},[
    el('div',{class:'lbl'},[label]),
    el('div',{style:'display:flex;align-items:center;gap:12px'},[
      el('input',{type:'range',min,max,step,value:String(SB[key]),style:'flex:1',
        oninput:e=>{SB[key]=+e.target.value;redraw();}}),
      el('span',{class:'mono',style:'font-size:13px;min-width:82px;text-align:right'},[fmt(SB[key])])])]);
  const chips=(label,key,opts,fmtOpt)=>el('div',{style:'margin-bottom:14px'},[
    el('div',{class:'lbl'},[label]),
    el('div',{class:'seg'},opts.map(o=>{
      const val=Array.isArray(o)?o[0]:o, txt=fmtOpt?fmtOpt(o):val;
      const on=Array.isArray(SB[key])?SB[key].includes(val):SB[key]===val;
      return el('button',{type:'button','aria-pressed':String(on),onclick:()=>{
        if(Array.isArray(SB[key])){const i=SB[key].indexOf(val);
          if(i>=0){if(SB[key].length>1)SB[key].splice(i,1);}else SB[key].push(val);}
        else SB[key]=val; redraw();}},[txt]);}))]);
  const toggle=(label,key,desc)=>el('label',{style:'display:flex;gap:10px;align-items:flex-start;font-size:13.5px;cursor:pointer;margin-bottom:9px'},[
    el('input',{type:'checkbox',checked:SB[key],onchange:e=>{SB[key]=e.target.checked;redraw();},style:'margin-top:3px'}),
    el('span',{},[el('b',{},[label]),el('span',{style:'color:var(--muted)'},[' — '+desc])])]);

  const preset=(label,fn,kind='')=>el('button',{class:'btn'+(kind?' '+kind:''),type:'button',
    onclick:()=>{fn();redraw();}},[label]);

  const res=sbVerify(), blocked=res.some(r=>!r[2]);

  root.append(sec([W([el('div',{class:'grid g2'},[
    /* left: the mandate */
    el('div',{class:'card'},[
      el('h4',{},['1 · What the user authorises']),
      numIn('Spend limit per purchase','cap',500,50000,500,v=>'₹'+v.toLocaleString('en-IN')),
      numIn('Total across all purchases','cum',1000,100000,1000,v=>'₹'+v.toLocaleString('en-IN')),
      numIn('Valid for','days',1,30,1,v=>v+' days'),
      chips('Allowed categories (tap to toggle)','mccs',MCCS,o=>o[1]),
      chips('Allowed shops','shops',SHOPS,o=>o.replace('merch:',''))]),
    /* right: the attempt */
    el('div',{class:'card'},[
      el('h4',{},['2 · What the assistant tries to buy']),
      numIn('Amount','amount',100,60000,100,v=>'₹'+v.toLocaleString('en-IN')),
      numIn('Days since the mandate was signed','elapsed',0,30,1,v=>'day '+v),
      numIn('Already spent under this mandate','spent',0,60000,1000,v=>'₹'+v.toLocaleString('en-IN')),
      chips('Category','mcc',MCCS,o=>o[1]),
      chips('Shop','shop',SHOPS,o=>o.replace('merch:','')),
      el('div',{class:'lbl',style:'margin-top:16px'},['Tamper with the request']),
      toggle('Forge the agent signature','forge','sign with a key the directory does not know'),
      toggle('Swap the items after approval','tamper','change the cart once the user has confirmed'),
      toggle('Use a withdrawn permission','revoked','present a mandate the user already revoked'),
      toggle('Replay an earlier request','replay','resend a presentation that was already settled')])])])]));

  /* verdict */
  root.append(sec([W([
    el('div',{style:'border:1.5px solid '+(blocked?'var(--neg)':'var(--pos)')+
      ';border-radius:6px;overflow:hidden'},[
      el('div',{style:'padding:16px 22px;background:'+(blocked?'var(--neg-soft)':'var(--pos-soft)')+
        ';display:flex;align-items:baseline;gap:16px;flex-wrap:wrap'},[
        el('div',{class:'mono',style:'font-size:20px;font-weight:600;color:'+(blocked?'var(--neg)':'var(--pos)')},
          [blocked?'BLOCKED':'ALLOWED']),
        el('div',{style:'font-size:13.5px;color:var(--ink-soft)'},[
          blocked?(res.filter(r=>!r[2]).length+' of 10 checks failed'):'all 10 checks passed'])]),
      el('div',{style:'padding:18px 22px;background:var(--surface)'},
        res.map(r=>el('div',{style:'display:flex;gap:12px;align-items:baseline;padding:5px 0;font-size:13.5px'},[
          el('span',{class:'mono',style:'width:34px;color:'+(r[2]?'var(--pos)':'var(--neg)')+';font-weight:600'},
            [r[2]?'✓':'✗']),
          el('span',{class:'mono',style:'width:34px;color:var(--muted);font-size:12px'},[r[0]]),
          el('span',{style:'min-width:210px;'+(r[2]?'':'color:var(--neg);font-weight:500')},[r[1]]),
          el('span',{style:'color:var(--neg);font-size:12.5px'},[r[3]||''])])))])])]));

  /* presets */
  root.append(sec([W([el('div',{class:'lbl'},['Or load a scenario']),
    el('div',{style:'display:flex;gap:10px;flex-wrap:wrap'},[
      preset('Ordinary purchase',()=>Object.assign(SB,{amount:4200,mcc:'5941',shop:'merch:runfast',
        elapsed:1,spent:0,forge:false,tamper:false,revoked:false,replay:false})),
      preset('Amount escalation',()=>Object.assign(SB,{amount:40000,mcc:'5691',shop:'merch:luxebags',
        elapsed:1,spent:0,forge:false,tamper:false,revoked:false,replay:false})),
      preset('Drain by many small buys',()=>Object.assign(SB,{amount:4000,mcc:'5941',shop:'merch:runfast',
        elapsed:2,spent:11000,forge:false,tamper:false,revoked:false,replay:false})),
      preset('Swap items after approval',()=>Object.assign(SB,{amount:4200,mcc:'5941',shop:'merch:runfast',
        elapsed:1,spent:0,forge:false,tamper:true,revoked:false,replay:false})),
      preset('Try an attack we cannot catch',()=>Object.assign(SB,{amount:4999,mcc:'5941',
        shop:'merch:runfast',elapsed:2,spent:0,forge:false,tamper:false,revoked:false,replay:false}),'p')])])]));

  if(!blocked&&SB.amount===4999){
    root.append(W([take('the honest half','Every check passed — and this is a purchase the user never wanted. A compromised or prompt-injected assistant that <b>stays inside the rules</b> is invisible to this kind of check. Enforcement <b>bounds the loss</b>; it does not detect intent. Measured reduction: <b>91.9%</b> of expected loss, not detection.','bad')]));
  } else {
    root.append(W([take('what this is','Deterministic. The same inputs always give the same answer, and across 20,000 legitimate in-scope purchases it wrongly blocked <b>zero</b>. Eight of ten modelled attack families are caught this way; the two that are not are shown by the last preset.')]));
  }
}


/* ================= SCREEN 2 — DECISION TOOL ================= */
const RHOS=[0,0.2,0.4,0.6,0.8,1.0], LAMS=[0,0.05,0.10,0.20,0.35];
const RHO_WORD=['Uncoached','Lightly coached','Moderately coached','Well coached','Heavily coached','Fully coached'];
const LAM_WORD=['None look alike','A few look alike','Some look alike','Many look alike','Very many look alike'];
/* Both metric families and all three operating points from the
   pre-registration, so nothing is hidden behind a default. */
const GOALS=[
 {id:'catch',label:'Catch more fraud',sub:'holding the alert budget fixed',
  ptLabel:'How many payments can you afford to review?',
  pts:[{m:'recall@fpr=0.001',lab:'0.1% of payments',op:'recall @ 0.1% FPR'},
       {m:'recall@fpr=0.005',lab:'0.5% of payments',op:'recall @ 0.5% FPR'},
       {m:'recall@fpr=0.01', lab:'1% of payments',  op:'recall @ 1% FPR'}]},
 {id:'cut',label:'Cut false alarms',sub:'holding the catch rate fixed',
  ptLabel:'What catch rate are you aiming for?',
  pts:[{m:'fpr@recall=0.5',lab:'catch 50% of fraud',op:'false-alarm rate @ 50% recall'},
       {m:'fpr@recall=0.7',lab:'catch 70% of fraud',op:'false-alarm rate @ 70% recall'},
       {m:'fpr@recall=0.9',lab:'catch 90% of fraud',op:'false-alarm rate @ 90% recall'}]}];
const ADVW=[{id:'uniform',label:'Coaches the victim',sub:'tells them what to type'},
            {id:'prevalence',label:'Coaches carefully',sub:'the words leak no statistics'},
            {id:'matched',label:'Knows your defence',sub:'also picks a matching account'}];
let DT={r:2,l:2,adv:'matched',goal:'catch',pt:0};

function renderDecide(root){
  root.replaceChildren();

  const redraw=()=>renderDecide(root);
  const slider=(label,key,arr,words,fmt)=>el('div',{style:'margin-bottom:24px'},[
    el('div',{class:'lbl'},[label]),
    el('input',{type:'range',min:'0',max:String(arr.length-1),step:'1',value:String(DT[key]),
      style:'width:100%',oninput:e=>{DT[key]=+e.target.value;redraw();}}),
    el('div',{style:'text-align:center;margin-top:6px'},[
      el('div',{style:'font-size:15px;font-weight:600'},[words[DT[key]]]),
      el('div',{class:'mono',style:'font-size:11.5px;color:var(--muted);margin-top:2px'},[fmt(arr[DT[key]])])]),
    el('div',{style:'display:flex;justify-content:space-between;font-size:11.5px;color:var(--muted);margin-top:2px'},[
      el('span',{},[words[0]]),el('span',{},[words[words.length-1]])])]);

  const goal=GOALS.find(g=>g.id===DT.goal);
  const pt=goal.pts[Math.min(DT.pt,goal.pts.length-1)];
  const cells=(D.phase&&D.phase.metrics[DT.adv+'|'+pt.m])||[];
  const c=cells.find(x=>x.rho===RHOS[DT.r]&&x.lam===LAMS[DT.l]);
  const yes=!!(c&&c.significant);

  root.append(sec([W([el('div',{class:'grid g2'},[
    el('div',{class:'card'},[
      el('h4',{},['Your operating conditions']),
      slider('How hard do you expect scammers to coach victims?','r',RHOS,RHO_WORD,v=>'coaching effectiveness ρ = '+v),
      slider('How many legitimate accounts in your network look like scam accounts?','l',LAMS,LAM_WORD,v=>'structural overlap λ = '+v),
      el('div',{class:'lbl'},['Which attacker are you planning against?']),
      el('div',{class:'seg',style:'margin-bottom:6px'},ADVW.map(a=>el('button',{type:'button',
        'aria-pressed':String(a.id===DT.adv),onclick:()=>{DT.adv=a.id;redraw();}},[a.label]))),
      el('div',{style:'font-size:12px;color:var(--muted)'},[ADVW.find(a=>a.id===DT.adv).sub])]),
    el('div',{class:'card'},[
      el('h4',{},['What are you optimising?']),
      el('div',{class:'seg',style:'margin:8px 0 6px'},GOALS.map(g=>el('button',{type:'button',
        'aria-pressed':String(g.id===DT.goal),onclick:()=>{DT.goal=g.id;redraw();}},[g.label]))),
      el('div',{style:'font-size:12px;color:var(--muted);margin-bottom:18px'},[goal.sub]),
      el('div',{class:'lbl'},[goal.ptLabel]),
      el('div',{class:'seg',style:'margin-bottom:8px'},goal.pts.map((q,i)=>el('button',{type:'button',
        'aria-pressed':String(i===Math.min(DT.pt,goal.pts.length-1)),
        onclick:()=>{DT.pt=i;redraw();}},[q.lab]))),
      el('div',{style:'font-size:12px;color:var(--muted);margin-bottom:18px'},['measured as '+pt.op]),
      el('p',{style:'font-size:13.5px;color:var(--ink-soft);margin:0'},[
        'These two goals do not give the same answer, and that disagreement is one of the study’s findings. Both metric families and all three operating points were fixed in advance, so none could be chosen after the results were in.'])])])])]));

  /* verdict */
  const vcol=yes?'var(--pos)':'var(--neg)', vbg=yes?'var(--pos-soft)':'var(--neg-soft)';
  const rows=[];
  if(c){
    rows.push(['Effect on '+pt.op,(c.delta>=0?'+':'')+c.delta.toFixed(4)]);
    rows.push(['95% confidence interval',
      (c.ci_lo_min>=0?'+':'')+c.ci_lo_min.toFixed(4)+'  to  '+(c.ci_hi_max>=0?'+':'')+c.ci_hi_max.toFixed(4)]);
    rows.push(['Holds across repeat runs',c.significant?'yes, all '+c.n_seeds:'no — interval includes zero']);
    rows.push(['Minimum menu size','6 purpose categories · 3 is not enough']);
    rows.push(['What you have to build','retain the field, pass it to the model you already run']);
    rows.push(['What you do not have to build','a hand-built consistency model — ours added +0.0007 over the plain field']);
  }
  root.append(sec([W([
    el('div',{style:'border:1.5px solid '+vcol+';border-radius:6px;overflow:hidden'},[
      el('div',{style:'padding:20px 24px;background:'+vbg},[
        el('div',{class:'mono',style:'font-size:24px;font-weight:600;color:'+vcol+';letter-spacing:-.01em'},
          [c?(yes?'COLLECT IT':'DO NOT BOTHER'):'no data for this cell']),
        el('div',{style:'font-size:13.5px;color:var(--ink-soft);margin-top:7px'},[
          c?(yes?'Under these conditions the purpose field earns its place.'
                :'Under these conditions the field does not measurably help. Spend the effort elsewhere.'):'']),
        el('div',{style:'font-size:12.5px;color:var(--muted);margin-top:10px'},[
          RHO_WORD[DT.r].toLowerCase()+' · '+LAM_WORD[DT.l].toLowerCase()+' · attacker '+
          ADVW.find(a=>a.id===DT.adv).label.toLowerCase()+' · measured as '+pt.op]),
        el('div',{class:'mono',style:'font-size:11px;color:var(--muted);margin-top:4px;opacity:.8'},[
          'ρ='+RHOS[DT.r]+'  λ='+LAMS[DT.l]+'  '+pt.m])]),
      c?el('div',{style:'background:var(--surface);padding:6px 24px 18px'},
        [tbl(['',''],rows,[1])]):null])])]));

  root.append(W([take('the actual finding','Switch between the six operating points above and the verdict changes. At every alert budget we tested — 0.1%, 0.5% and 1% of payments — it is worth collecting. Aiming instead for a fixed catch rate, it does not pay at 50% or 70%, and pays again at 90%. <b>The same signal, the same data, opposite answers.</b> A network that deploys this everywhere is wasting money in the regions where it does not pay.','warn')]));
  root.append(W([take('and the fancy layer was not the point','We also built a purpose–account consistency model to squeeze more out of the field. Across all 270 conditions it beat simply handing the raw field to the existing model by <b>+0.0007</b>. We went looking for a sophisticated mechanism; the experiment said the simpler thing was enough.','good')]));
}



/* the experiment, drawn */
function figExperiment(){
  let s='';
  const ly=44, bh=58;
  s+=BOX(20,ly,150,bh,{fill:'var(--raised)'})+
     T(95,ly+25,'2 million payments',{w:600,s:13})+T(95,ly+43,'0.8% of them scams',{s:11.5,c:'var(--muted)'});
  s+=LINE(170,ly+bh/2,206,ly-6,{m:'ar'});
  s+=LINE(170,ly+bh/2,206,ly+bh+30,{m:'ar'});
  s+=BOX(212,ly-32,264,52,{stroke:'var(--line-2)'})+
     T(344,ly-12,'Model A — everything a bank has today',{w:600,s:12.5})+
     T(344,ly+5,'the payment, the behaviour, the recipient',{s:11.5,c:'var(--muted)'});
  s+=BOX(212,ly+bh+6,264,52,{stroke:'var(--accent)',fill:'var(--accent-soft)'})+
     T(344,ly+bh+26,'Model B — the same, plus one field',{w:600,s:12.5,c:'var(--accent-ink)'})+
     T(344,ly+bh+43,'“what did the payer think this was for?”',{s:11.5,c:'var(--accent-ink)'});
  s+=LINE(476,ly-6,516,ly+bh/2-4,{m:'ar'});
  s+=LINE(476,ly+bh+32,516,ly+bh/2+8,{m:'ar'});
  s+=BOX(522,ly+2,182,bh-4,{fill:'var(--surface)'})+
     T(613,ly+24,'How much more fraud',{w:600,s:13})+T(613,ly+42,'did B catch than A?',{w:600,s:13});
  s+=LINE(704,ly+bh/2,742,ly+bh/2,{m:'ar'});
  s+=BOX(748,ly+2,112,bh-4,{fill:'var(--raised)'})+
     T(804,ly+26,'one answer',{s:12.5,w:600})+T(804,ly+43,'for one setting',{s:11,c:'var(--muted)'});
  s+=BOX(20,ly+bh+80,840,44,{dash:'5 4',fill:'none',stroke:'var(--muted)'});
  s+=T(440,ly+bh+100,'Now repeat that for every combination of how hard the scammer coached the victim,',{s:12});
  s+=T(440,ly+bh+116,'how many legitimate accounts look suspicious, and how skilled the attacker is.',{s:12});
  return {vb:'0 0 880 250',body:s};
}

/* ================= THE PRODUCT — score a payment ================= */
const PZ={rent:'Rent',salary_reimburse:'Paying back a colleague',family_support:'Family support',
  friend_transfer:'Sending a friend money',education_fees:'School or college fees',
  utility_bill:'A utility bill',merchant_purchase:'Buying something',loan_repayment:'Loan repayment',
  investment:'An investment',medical:'Medical',other:'Something else'};
const AGEZ=[[15,'2 weeks old'],[120,'4 months old'],[400,'about a year old'],[1500,'4 years old']];
const PAYZ=[[3,'3 people'],[25,'25 people'],[80,'80 people'],[400,'400 people']];
const FANZ=[[0.10,'keeps it'],[0.50,'moves half on'],[0.90,'moves it all on within hours']];
const AMTZ=[[2000,'₹2,000'],[15000,'₹15,000'],[60000,'₹60,000'],[200000,'₹2,00,000']];
const KNWZ=[[1,'yes, many times'],[0,'no, first time']];
const BEHZ=[[0,'calm, as usual'],[1,'rushed, hesitating, on a call']];
const REVIEW=0.995;   /* a bank reviewing the riskiest 0.5% of payments */
let SC={purpose:'salary_reimburse',age:400,payers:80,fanout:0.90,amount:2000,known:0,behave:1};





/* ================= THE CALCULATOR ================= */
const QS=[
 {k:'purpose',q:'What does the payer say the money is for?',
  hint:'This is the declared context — the piece a fraud model rarely has. Everything else here, a bank already sees.',
  opts:()=>D.scorer.grid.purpose.map(v=>[v,PZ[v]])},
 {k:'amount',q:'How much are they sending?',hint:'',opts:()=>AMTZ},
 {k:'known',q:'Have they paid this account before?',hint:'',opts:()=>KNWZ},
 {k:'behave',q:'How did the payer act while sending it?',
  hint:'Banks already watch this — hesitation, edits, app-switching, whether a call is live.',opts:()=>BEHZ},
 {k:'age',q:'How old is the account receiving the money?',hint:'',opts:()=>AGEZ},
 {k:'payers',q:'How many different people paid into that account last month?',hint:'',opts:()=>PAYZ},
 {k:'fanout',q:'What does that account do with money it receives?',hint:'',opts:()=>FANZ},
];
let STEP=0;

function scAt(o){
  const g=D.scorer.grid,s=D.scorer.shape;
  const i=[g.purpose.indexOf(o.purpose),g.age.indexOf(o.age),g.payers.indexOf(o.payers),
           g.fanout.indexOf(o.fanout),g.amount.indexOf(o.amount),g.known.indexOf(o.known),
           g.behave.indexOf(o.behave)];
  return (((((i[0]*s[1]+i[1])*s[2]+i[2])*s[3]+i[3])*s[4]+i[4])*s[5]+i[5])*s[6]+i[6];}

/* leave-one-out on real model outputs: how much did each answer move the score? */
function contributions(){
  const cur=D.scorer.with_purpose.pct[scAt(SC)];
  return QS.map(q=>{
    const vals=q.opts().map(o=>Array.isArray(o)?o[0]:o);
    let best=cur,bestv=SC[q.k];
    for(const v of vals){const t=Object.assign({},SC);t[q.k]=v;
      const p=D.scorer.with_purpose.pct[scAt(t)];
      if(p<best){best=p;bestv=v;}}
    const lab=(q.opts().find(o=>(Array.isArray(o)?o[0]:o)===SC[q.k])||[null,''])[1];
    const safeLab=(q.opts().find(o=>(Array.isArray(o)?o[0]:o)===bestv)||[null,''])[1];
    return {k:q.k,q:q.q,chose:lab,effect:cur-best,safest:safeLab,isSafest:bestv===SC[q.k]};
  }).sort((a,b)=>b.effect-a.effect);}

function renderCalc(root){
  root.replaceChildren();
  const total=QS.length;
  const back=el('button',{class:'btn',type:'button',onclick:()=>{
    if(STEP===0){go('home');}else{STEP--;renderCalc(root);}}},
    [STEP===0?'← Back':'← Previous']);

  /* progress */
  root.append(el('div',{class:'wrap'},[el('div',{class:'prog'},
    Array.from({length:total+1},(_,i)=>el('div',{class:'seg-dot'+(i<STEP?' done':i===STEP?' now':'')})))]));

  if(STEP<total){
    const q=QS[STEP];
    root.append(el('div',{class:'wrap qwrap'},[
      el('div',{class:'qnum'},['Question '+(STEP+1)+' of '+total]),
      el('h2',{class:'qtitle'},[q.q]),
      q.hint?el('p',{class:'qhint'},[q.hint]):null,
      el('div',{class:'qopts'},q.opts().map(o=>{
        const v=Array.isArray(o)?o[0]:o, lab=Array.isArray(o)?o[1]:o;
        return el('button',{class:'qopt'+(SC[q.k]===v?' sel':''),type:'button',
          onclick:()=>{SC[q.k]=v;STEP++;renderCalc(root);}},[lab]);})),
      el('div',{style:'margin-top:24px'},[back])]));
    return;
  }

  /* ---- result ---- */
  const idx=scAt(SC);
  const a=D.scorer.baseline.pct[idx], b=D.scorer.with_purpose.pct[idx];
  const fa=a>=REVIEW, fb=b>=REVIEW;
  const meter=(title,pct,flag)=>el('div',{class:'card',style:'border-width:1.5px;border-color:'+(flag?'var(--neg)':'var(--line)')},[
    el('div',{class:'lbl'},[title]),
    el('div',{style:'font-family:\"IBM Plex Mono\",monospace;font-size:32px;font-weight:500;line-height:1;margin:10px 0 5px;color:'+(flag?'var(--neg)':'var(--ink)')},[(pct*100).toFixed(1)+'%']),
    el('div',{style:'font-size:13px;color:var(--muted)'},['riskier than this share of all payments']),
    el('div',{style:'height:9px;background:var(--sunk);border-radius:5px;margin:16px 0 11px;position:relative;overflow:hidden'},[
      el('div',{style:'position:absolute;left:0;top:0;bottom:0;width:'+(pct*100).toFixed(1)+'%;background:'+(flag?'var(--neg)':'var(--accent)')}),
      el('div',{style:'position:absolute;left:99.5%;top:-3px;bottom:-3px;width:2px;background:var(--ink)'})]),
    el('div',{style:'font-size:14px;font-weight:600;color:'+(flag?'var(--neg)':'var(--muted)')},[flag?'⚑ Held for review':'Goes through'])]);

  let verdict,kind;
  if(fb&&!fa){verdict='<b>The declared context caught this one.</b> Without it, this payment goes straight through to the scammer.';kind='good';}
  else if(!fb&&fa){verdict='<b>The declared context cleared this one.</b> It looked suspicious until you knew what it was for — that is a customer who does not get wrongly blocked.';kind='good';}
  else if(fa&&fb){verdict='<b>Both catch it.</b> This payment was already obvious; the extra field changes nothing here.';kind='';}
  else{verdict='<b>Both let it through.</b> The context is not magic — on payments like this one it does not decide anything.';kind='warn';}

  root.append(el('div',{class:'wrap qwrap'},[
    el('div',{class:'qnum'},['Result']),
    el('h2',{class:'qtitle'},['Two models, same payment']),
    el('div',{class:'grid g2',style:'margin-top:22px'},[
      meter('A bank’s system today',a,fa),
      meter('The same system, given the declared context',b,fb)]),
    el('div',{style:'margin-top:16px'},[take('what happened',verdict,kind)])]));

  /* explainability */
  const cons=contributions().filter(c=>c.effect>0.001);
  root.append(el('div',{class:'wrap qwrap'},[
    el('h3',{class:'s',style:'margin-top:34px'},['Why it landed there']),
    el('p',{style:'max-width:62ch'},['Each row asks the same question: if you changed only that one answer to the least alarming option, how far would the score fall? Every number is a real model output, not an estimate.']),
    cons.length?el('div',{class:'expl'},cons.map(c=>el('div',{class:'exrow'},[
      el('div',{class:'exbar'},[el('div',{style:'width:'+Math.min(100,c.effect/Math.max(...cons.map(x=>x.effect))*100).toFixed(0)+'%'})]),
      el('div',{},[el('div',{class:'exq'},[c.chose]),
        el('div',{class:'exs'},['would drop '+(c.effect*100).toFixed(1)+' points if this were “'+c.safest+'” instead'])])]))):
      el('p',{style:'color:var(--muted)'},['Every answer you gave was already the least alarming option available.']),
    el('div',{style:'margin-top:22px'},[take('how we know','We trained <b>1,535 fraud models</b> to work this out. Each learned from 1.04 million payments and was tested on 167,345 more, from people it had never seen. Your seven answers are one of 8,448 combinations we scored in advance — so this is a real model looking up its own output, not a guess.')]),
    el('div',{style:'display:flex;gap:12px;flex-wrap:wrap;margin-top:26px'},[
      el('button',{class:'btn p',type:'button',onclick:()=>{STEP=0;renderCalc(root);}},['Try another payment']),
      el('button',{class:'btn',type:'button',onclick:()=>go('how')},['See how this was built →'])])]));
}

/* ================= LANDING + APP SHELL ================= */
let VIEW='home';
const VIEWS={home:renderLanding,tool:renderCalc,problem:renderProblem,
             how:renderHow,found:renderFound,ai:renderAI};
function go(v){VIEW=v;drawApp();}
function drawApp(){
  const main=document.getElementById('main');
  main.replaceChildren();
  (VIEWS[VIEW]||renderLanding)(main);
  document.querySelectorAll('.jump nav a').forEach(a=>
    a.setAttribute('aria-current',String(a.dataset.v===VIEW)));
  document.querySelector('.jump').classList.toggle('onhome',VIEW==='home');
  window.scrollTo({top:0,behavior:'instant'});
  try{history.replaceState(null,'','#'+VIEW);}catch(e){}
}


function S(id,kids){return el('section',{id,class:'blk'},[].concat(kids));}

function onward(pairs){
  return el('div',{class:'wrap'},[el('div',{class:'onward'},pairs.map((x,i)=>
    el('button',{class:'btn'+(i===0?' p':''),type:'button',
      onclick:()=>{if(x[1]==='tool')STEP=0;go(x[1]);}},[x[0]])))]);}

function renderLanding(root){
  /* landing */
  root.append(el('section',{class:'blk land'},[el('div',{class:'wrap'},[
    el('div',{class:'kicker'},['Pramana · a valid means of proof']),
    el('h1',{class:'hero'},['What if every payment said what it was for?']),
    el('p',{class:'lede'},['When someone is tricked into paying a scammer, they approve the payment themselves. So every check the bank runs says yes — correctly. Nobody records the one thing that would give it away: what the payer thought they were paying for.']),
    el('p',{class:'lede',style:'margin-top:14px'},['Pramana adds that one field to a real fraud model, and shows you what changes.']),
    el('div',{class:'heroactions'},[
      el('button',{class:'btn p big',type:'button',onclick:()=>{STEP=0;go('tool');}},['Try it now →']),
      el('button',{class:'btn big',type:'button',onclick:()=>go('how')},['How it works'])]),
    el('div',{class:'trust'},[
      el('span',{},['Built on ',el('b',{},['1,535']),' trained fraud models']),
      el('span',{},[el('b',{},['282']),' tested conditions']),
      el('span',{},[el('b',{},['3']),' attackers, the last one knowing the defence'])])])]));

}

function renderProblem(root){
  root.append(S('s-feel',[el('div',{class:'wrap'},[
    el('div',{class:'num'},['01']),
    el('h2',{class:'t'},['The problem']),
    el('p',{class:'sub'},['A bank cannot already do this, and here is why. Two real accounts from our simulation — both take money from dozens of unrelated people and pass it straight on. One collects scam money. These are the only fields a fraud system has.'])]),
    el('div',{class:'wrap'},[hookAccounts()])]));

  root.append(onward([['How it works →','how'],['Try it now','tool']]));
}

function renderHow(root){
  root.append(S('s-answer',[el('div',{class:'wrap'},[
    el('div',{class:'num'},['02']),
    el('h2',{class:'t'},['How it works']),
    el('p',{class:'sub'},['The answer is not yes or no — it depends on what you are optimising and who you are up against. The same signal is worth collecting under some operating conditions and worthless under others. Set yours and see.'])]),
    el('div',{class:'wrap'},[(()=>{const h=el('div',{});renderDecide(h);return h;})()]),
    el('div',{class:'wrap'},[el('div',{class:'grid g4 stats'},[
      el('div',{class:'stat'},[el('div',{class:'v'},['1,535']),el('div',{class:'l'},['models trained']),
        el('div',{class:'s'},['one for every combination of conditions'])]),
      el('div',{class:'stat'},[el('div',{class:'v'},['1.04M']),el('div',{class:'l'},['payments each learned from']),
        el('div',{class:'s'},['tested on 167,345 more, from people it never saw'])]),
      el('div',{class:'stat'},[el('div',{class:'v'},['282']),el('div',{class:'l'},['conditions tested']),
        el('div',{class:'s'},['three repeats of each'])]),
      el('div',{class:'stat'},[el('div',{class:'v'},['3']),el('div',{class:'l'},['attackers of rising skill']),
        el('div',{class:'s'},['the last knows how the defence works'])])])]),
    el('div',{class:'wrap'},[fig(figExperiment(),
      'How every one of those numbers was produced: the same fraud model trained twice, once with the field and once without, with the gap between them as the measurement.',
      'Two identical fraud models, one with the purpose field and one without, compared on how much more fraud the second catches, repeated across many conditions')]),
    el('div',{class:'wrap'},[take('the fair-fight rule','The model without the field got <b>all</b> the tuning effort. The one with it got none — it just inherited those settings. So every gap we report is the smallest the field could plausibly be worth.','good')])]));

  root.append(onward([['What we found →','found'],['Try it now','tool']]));
}

function renderFound(root){
  const yn=(ok,txt)=>el('div',{style:'display:flex;gap:9px;align-items:baseline'},[
    el('span',{style:'font-size:15px;font-weight:700;color:'+(ok?'var(--pos)':'var(--neg)')},[ok?'✓':'✗']),
    el('span',{},[txt])]);
  root.append(S('s-catch',[el('div',{class:'wrap'},[
    el('div',{class:'num'},['03']),
    el('h2',{class:'t'},['What we found']),
    el('p',{class:'sub'},['We expected the cleverest scammer to simply beat the new field. Instead, it turned out they have to choose.'])]),
    el('div',{class:'wrap'},[el('div',{class:'scroll'},[
      (()=>{const t=el('table',{class:'cmp'});
        t.append(el('thead',{},[el('tr',{},[
          el('th',{},['A scammer collecting “rent” payments can…']),
          el('th',{},['Spread the money across many accounts']),
          el('th',{},['Use only accounts that look like a landlord'])])]));
        t.append(el('tbody',{},[
          el('tr',{},[el('td',{},['Does the story match the account?']),
            el('td',{},[yn(false,'No — none of them looks like a landlord')]),
            el('td',{},[yn(true,'Yes — that was the whole point')])]),
          el('tr',{},[el('td',{},['Do the accounts look normal?']),
            el('td',{},[yn(true,'Yes — the money is spread thin')]),
            el('td',{},[yn(false,'No — it all piles into a handful')])]),
          el('tr',{class:'verdict'},[el('td',{},['So what happens?']),
            el('td',{},[el('b',{style:'color:var(--neg)'},['The purpose check catches them'])]),
            el('td',{},[el('b',{style:'color:var(--neg)'},['The account check catches them'])])])]));
        return t;})()])]),
    el('div',{class:'wrap'},[take('why this matters','They can look consistent <b>or</b> stay spread out — not both. So this field is worth more than the fraud it catches by itself: it also forces the scammer into a shape your existing checks can already see.','good')])]));

  /* the cases it gets wrong */
  if(D.inspector){
    const one=b=>D.inspector.cases.find(c=>c.bucket===b);
    const fa=one('misleads_false_alarm'), mf=one('misleads_missed_fraud');
    const wrong=(c,title,note)=>c?el('div',{class:'card',style:'border-color:var(--neg)'},[
      el('h4',{style:'color:var(--neg)'},[title]),
      el('p',{style:'margin-bottom:12px'},[note]),
      el('div',{style:'font-size:13.5px;line-height:1.9'},[
        el('div',{},[el('span',{style:'color:var(--muted)'},['payer said it was for  ']),
                     el('b',{},[c.declared_purpose.replace(/_/g,' ')])]),
        el('div',{},[el('span',{style:'color:var(--muted)'},['it really was  ']),
                     el('b',{},[c.is_fraud?'a scam':'a genuine payment'])]),
        el('div',{},[el('span',{style:'color:var(--muted)'},['adding the context  ']),
                     el('b',{style:'color:var(--neg)'},[(c.rank_shift>0?'moved it up ':'moved it down ')+
                       Math.abs(c.rank_shift*100).toFixed(1)+' places per 100'])])])]):null;
    root.append(sec([W([h3('And the cases it gets wrong')]),
      COL([p('Two real payments from the test set. In both, adding the declared context pushed the decision in the wrong direction.')]),
      W([el('div',{class:'grid g2'},[
        wrong(fa,'A false alarm','A genuine payment the context made look worse, so a real customer gets held up.'),
        wrong(mf,'Fraud it hid','Real fraud the context made look more ordinary, so it sinks down the queue.')])]),
      W([take('why we show these','A signal that helps on average still moves individual decisions the wrong way. Anyone deciding whether to collect this field needs to see both directions, so these are on the page rather than in an appendix.','warn')])]));
  }

  root.append(onward([['AI payments →','ai'],['Try it now','tool']]));
}

function renderAI(root){
  root.append(S('s-break',[el('div',{class:'wrap'},[
    el('div',{class:'num'},['04']),
    el('h2',{class:'t'},['When an AI assistant pays for you']),
    el('p',{class:'sub'},['The instruction can be signed before anything is bought — so the check stops being a guess and becomes arithmetic. Set the rules, then try to get a payment past them.'])]),
    el('div',{class:'wrap'},[(()=>{const h=el('div',{});renderSandbox(h);return h;})()]),
    el('div',{class:'wrap'},[el('div',{class:'grid g3',style:'margin-top:26px'},[
      card(D.agentic.coverage.caught+' of '+D.agentic.coverage.total+' attack types blocked',
           'They break an explicit rule in the signed instruction, so no model is needed — the check is arithmetic.'),
      card(D.agentic.false_positives_on_in_scope_traffic.rejected+' false alarms',
           'Across '+D.agentic.false_positives_on_in_scope_traffic.n.toLocaleString()+
           ' simulated legitimate in-scope purchases, none was wrongly blocked.'),
      card(D.agentic.coverage.uncaught.length+' types cannot be caught',
           'They stay <em>inside</em> the instruction, so no conformance check can see them. Enforcement caps the loss at '+
           (D.agentic.bounded_loss.reduction_persistent*100).toFixed(1)+'%; it does not detect intent.')])])]));

  root.append(onward([['Try it now →','tool'],['Back to the start','home']]));
}


/* build + wire */
VIEW=(location.hash||'').replace('#','') in VIEWS?(location.hash||'').replace('#',''):'home';
drawApp();
document.querySelectorAll('.jump nav a[data-v]').forEach(a=>{
  a.addEventListener('click',e=>{e.preventDefault();
    if(a.dataset.v==='tool')STEP=0;
    go(a.dataset.v);});});
document.getElementById('brand').addEventListener('click',()=>go('home'));
(function(){const e=document.getElementById('pcommit');
  if(e&&D.meta&&D.meta.prereg_commit)e.textContent=D.meta.prereg_commit.slice(0,10);})();
function show(){}   /* legacy no-op: nothing hides any more */
</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    OUT.write_text(html)
    print(f"written -> {OUT}  ({len(html)/1024:.0f} KB)")
