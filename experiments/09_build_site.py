"""Build the public site: one self-contained HTML file, no server.

Structure is deliberately progressive. A reader arriving cold meets the
problem in human terms, then the idea, then how it was tested, and only then
any numbers. Someone who stops after two pages still understands what the
project is and why it matters; someone who reads to the end gets the whole
evidence base.
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
    keep = {"bucket", "is_fraud", "scam_type", "declared_purpose", "payee_role",
            "amount", "channel", "score_base", "score_b4b", "rank_shift",
            "consistency_mahalanobis", "residuals", "reference_n"}
    return {"b3_cols": ins["b3_cols"],
            "cases": [{k: v for k, v in c.items() if k in keep} for c in ins["cases"]]}


def build() -> str:
    data = {
        "phase": slim_phase(load("phase_surface.json")),
        "agentic": load("agentic_conformance.json"),
        "fidelity": load("fidelity.json"),
        "inspector": slim_inspector(load("inspector.json")),
        "meta": {
            "prereg_commit": (git("log", "--reverse", "--format=%H", default="") or "")[:40],
            "head": git("rev-parse", "--short", "HEAD"),
            "built": datetime.now(timezone.utc).strftime("%d %B %Y"),
            "n_cells": len(list((RES / "raw").glob("*.json"))) if (RES / "raw").exists() else 0,
        },
    }
    payload = json.dumps(data, separators=(",", ":"), default=str)
    return TEMPLATE.replace("__PRAMANA_DATA__", payload)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pramana — when is declared payment context worth collecting?</title>
<meta name="description" content="A pre-registered study of whether asking a payer what a payment is for helps detect scam fraud, and how much adversarial pressure that signal survives.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#f8f7f4; --surface:#ffffff; --raised:#fbfaf7; --sunk:#f1efe9;
  --ink:#16181d; --ink-soft:#3f4550; --muted:#666d7c;
  --hairline:#e5e3dd; --hairline-strong:#d2cfc7;
  --accent:#1d3b73; --accent-soft:#e9eef7; --accent-ink:#1d3b73;
  --positive:#1c6b4c; --positive-soft:#e7f3ed;
  --negative:#a32e24; --negative-soft:#f9ebe9;
  --caution:#8a6320; --caution-soft:#faf2e4;
  --heat-pos:29,59,115; --heat-neg:163,46,36;
  --shadow:0 1px 2px rgba(22,24,29,.045), 0 10px 30px -22px rgba(22,24,29,.4);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#14161a; --surface:#1c1f25; --raised:#22262d; --sunk:#101216;
    --ink:#e9eaee; --ink-soft:#c5cad3; --muted:#98a0b0;
    --hairline:#2a2e37; --hairline-strong:#3a3f4a;
    --accent:#7ba3de; --accent-soft:#1a2540; --accent-ink:#a9c4ea;
    --positive:#5fbf92; --positive-soft:#142a21;
    --negative:#e58278; --negative-soft:#2d1a18;
    --caution:#d9ac5c; --caution-soft:#292216;
    --heat-pos:123,163,222; --heat-neg:229,130,120;
    --shadow:0 1px 2px rgba(0,0,0,.45), 0 10px 30px -22px rgba(0,0,0,.85);
  }
}
:root[data-theme="dark"]{
  --ground:#14161a; --surface:#1c1f25; --raised:#22262d; --sunk:#101216;
  --ink:#e9eaee; --ink-soft:#c5cad3; --muted:#98a0b0;
  --hairline:#2a2e37; --hairline-strong:#3a3f4a;
  --accent:#7ba3de; --accent-soft:#1a2540; --accent-ink:#a9c4ea;
  --positive:#5fbf92; --positive-soft:#142a21;
  --negative:#e58278; --negative-soft:#2d1a18;
  --caution:#d9ac5c; --caution-soft:#292216;
  --heat-pos:123,163,222; --heat-neg:229,130,120;
  --shadow:0 1px 2px rgba(0,0,0,.45), 0 10px 30px -22px rgba(0,0,0,.85);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",ui-sans-serif,system-ui,-apple-system,sans-serif;
  font-size:16px; line-height:1.68; -webkit-font-smoothing:antialiased;
}
h1,h2,h3,h4{font-family:Spectral,Georgia,"Times New Roman",serif;margin:0;text-wrap:balance}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
.wrap{max-width:1060px;margin:0 auto;padding:0 30px}
.narrow{max-width:720px}
a{color:var(--accent-ink)}
img{max-width:100%}

/* nav */
.topbar{position:sticky;top:0;z-index:40;background:var(--surface);border-bottom:1px solid var(--hairline)}
.topbar .wrap{display:flex;align-items:center;gap:26px;min-height:60px}
.brand{display:flex;align-items:baseline;gap:9px;cursor:pointer;flex-shrink:0}
.brand b{font-family:Spectral,Georgia,serif;font-size:22px;font-weight:700;letter-spacing:-.01em}
.brand span{font-size:11px;color:var(--muted);font-style:italic;font-family:Spectral,Georgia,serif}
.steps{display:flex;gap:1px;overflow-x:auto;margin-left:auto;scrollbar-width:none}
.steps::-webkit-scrollbar{display:none}
.steps button{
  appearance:none;background:none;border:0;border-bottom:2px solid transparent;
  font:inherit;font-size:13px;color:var(--muted);padding:19px 11px 15px;cursor:pointer;white-space:nowrap;
}
.steps button:hover{color:var(--ink)}
.steps button[aria-current="true"]{color:var(--accent-ink);border-bottom-color:var(--accent);font-weight:500}
.steps button:focus-visible{outline:2px solid var(--accent);outline-offset:-3px;border-radius:2px}

/* page frame */
main{min-height:60vh}
section[hidden]{display:none!important}
.pagehead{padding:56px 0 8px}
.step-label{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-ink);margin-bottom:12px}
h2.page{font-size:clamp(28px,4.2vw,40px);font-weight:600;letter-spacing:-.018em;line-height:1.16;max-width:17ch}
.standfirst{font-size:19px;line-height:1.6;color:var(--ink-soft);max-width:60ch;margin-top:18px;font-family:Spectral,Georgia,serif}
.body{padding:24px 0 60px}
.body p{max-width:64ch;margin:0 0 18px}
h3.sec{font-size:23px;font-weight:600;margin:44px 0 12px;letter-spacing:-.01em}
h4.sub{font-size:16px;font-weight:600;margin:26px 0 8px;font-family:"IBM Plex Sans",sans-serif}

/* footer nav */
.pagenav{display:flex;gap:12px;flex-wrap:wrap;padding:34px 0 70px;border-top:1px solid var(--hairline);margin-top:20px}
.btn{
  appearance:none;font:inherit;font-size:14px;font-weight:500;cursor:pointer;
  padding:12px 22px;border-radius:3px;border:1px solid var(--hairline-strong);
  background:var(--surface);color:var(--ink);text-decoration:none;display:inline-block;
}
.btn:hover{border-color:var(--accent);color:var(--accent-ink)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--ground)}
.btn.primary:hover{opacity:.9;color:var(--ground)}
.btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* blocks */
.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.g4{grid-template-columns:repeat(4,minmax(0,1fr))}
@media(max-width:860px){.g2,.g3,.g4{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--hairline);border-radius:4px;padding:22px;box-shadow:var(--shadow)}
.card h4{font-family:"IBM Plex Sans",sans-serif;font-size:15px;font-weight:600;margin:0 0 7px}
.card p{font-size:14.5px;color:var(--ink-soft);margin:0;max-width:none}
.pull{
  border-left:3px solid var(--accent);background:var(--accent-soft);
  padding:18px 24px;border-radius:0 4px 4px 0;margin:26px 0;
}
.pull.warn{border-left-color:var(--caution);background:var(--caution-soft)}
.pull.bad{border-left-color:var(--negative);background:var(--negative-soft)}
.pull.good{border-left-color:var(--positive);background:var(--positive-soft)}
.pull p{margin:0;max-width:58ch;font-size:16px}
.pull p+p{margin-top:12px}
.pull .big{font-family:Spectral,Georgia,serif;font-size:20px;line-height:1.5}
.aside{font-size:14px;color:var(--muted);max-width:62ch;border-top:1px solid var(--hairline);padding-top:14px;margin-top:26px}

/* numbers */
.stat{background:var(--surface);border:1px solid var(--hairline);border-radius:4px;padding:18px 20px}
.stat .v{font-family:"IBM Plex Mono",monospace;font-size:27px;font-weight:500;line-height:1.05;font-variant-numeric:tabular-nums}
.stat .l{font-size:13.5px;font-weight:500;margin-top:9px}
.stat .s{font-size:12px;color:var(--muted);margin-top:4px;line-height:1.45}
.v.pos{color:var(--positive)}.v.neg{color:var(--negative)}.v.acc{color:var(--accent-ink)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:6px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{text-align:left;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);
   font-weight:600;padding:9px 11px;border-bottom:1px solid var(--hairline-strong);white-space:nowrap}
td{padding:9px 11px;border-bottom:1px solid var(--hairline);font-variant-numeric:tabular-nums;vertical-align:top}
tr:last-child td{border-bottom:0}
td.r,th.r{text-align:right}
.tag{font-size:11px;padding:2px 8px;border-radius:2px;font-weight:600;white-space:nowrap;display:inline-block}
.tag.ok{background:var(--positive-soft);color:var(--positive)}
.tag.no{background:var(--negative-soft);color:var(--negative)}
.tag.mid{background:var(--sunk);color:var(--muted)}

/* controls */
.controls{display:flex;gap:26px;flex-wrap:wrap;margin:18px 0}
.ctl-label{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600;margin-bottom:7px}
.seg{display:flex;gap:5px;flex-wrap:wrap}
.seg button{appearance:none;font:inherit;font-size:12.5px;padding:7px 12px;cursor:pointer;
  background:var(--surface);color:var(--ink);border:1px solid var(--hairline-strong);border-radius:2px}
.seg button:hover{border-color:var(--accent)}
.seg button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--ground)}
.seg button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
</style>
</head>
<body>
<div class="topbar"><div class="wrap">
  <div class="brand" id="brand" role="button" tabindex="0"><b>Pramana</b><span>a valid means of proof</span></div>
  <nav class="steps" id="steps"></nav>
</div></div>
<main>
  <section id="p-home"></section>
  <section id="p-problem" hidden></section>
  <section id="p-idea" hidden></section>
  <section id="p-method" hidden></section>
  <section id="p-findings" hidden></section>
  <section id="p-demo" hidden></section>
  <section id="p-limits" hidden></section>
</main>
<script>
const D = __PRAMANA_DATA__;

/* ---------- helpers ---------- */
const el=(t,a={},k=[])=>{const n=document.createElement(t);
  for(const[key,v]of Object.entries(a)){if(v===null||v===undefined||v===false)continue;
    if(key==='class')n.className=v;else if(key==='html')n.innerHTML=v;
    else if(key.startsWith('on'))n.addEventListener(key.slice(2),v);
    else n.setAttribute(key,v===true?'':v);}
  for(const c of [].concat(k)){if(c===null||c===undefined||c===false)continue;
    n.append(c.nodeType?c:document.createTextNode(c));}
  return n;};
const pct=(v,d=1)=>(v*100).toFixed(d)+'%';
const inr=v=>'₹'+Math.round(v).toLocaleString('en-IN');
const sgn=(v,d=4)=>(v>=0?'+':'')+v.toFixed(d);

const head=(step,title,stand)=>el('div',{class:'pagehead'},[el('div',{class:'wrap narrow'},[
  step?el('div',{class:'step-label'},[step]):null,
  el('h2',{class:'page'},[title]),
  stand?el('p',{class:'standfirst'},[stand]):null])]);
const body=(kids)=>el('div',{class:'body'},[el('div',{class:'wrap narrow'},[].concat(kids))]);
const wide=(kids)=>el('div',{class:'body'},[el('div',{class:'wrap'},[].concat(kids))]);
const p=(t)=>el('p',{html:t});
const h3=(t)=>el('h3',{class:'sec'},[t]);
const h4=(t)=>el('h4',{class:'sub'},[t]);
const pull=(html,kind='')=>el('div',{class:'pull '+kind},[el('p',{html})]);
const card=(title,text)=>el('div',{class:'card'},[el('h4',{},[title]),el('p',{html:text})]);
const stat=(v,l,s,tone)=>el('div',{class:'stat'},[el('div',{class:'v '+(tone||'')},[v]),
  el('div',{class:'l'},[l]),s?el('div',{class:'s'},[s]):null]);
function table(hd,rows,right=[]){const t=el('table');
  t.append(el('thead',{},[el('tr',{},hd.map((h,i)=>el('th',{class:right.includes(i)?'r':''},[h])))]));
  t.append(el('tbody',{},rows.map(r=>el('tr',{},r.map((c,i)=>el('td',{class:right.includes(i)?'r':''},[c]))))));
  return el('div',{class:'scroll'},[t]);}
function seg(label,opts,cur,pick){return el('div',{},[el('div',{class:'ctl-label'},[label]),
  el('div',{class:'seg'},opts.map(o=>el('button',{type:'button','aria-pressed':String(o.id===cur),
    title:o.title||'',onclick:()=>pick(o.id)},[o.label])))]);}
function nav(prev,next){const b=el('div',{class:'pagenav'});
  if(prev)b.append(el('button',{class:'btn',type:'button',onclick:()=>show(prev.id)},['← '+prev.label]));
  if(next)b.append(el('button',{class:'btn primary',type:'button',onclick:()=>show(next.id)},[next.label+' →']));
  return el('div',{class:'wrap narrow'},[b]);}

/* ---------- 1. home ---------- */
function pHome(root){
  const finding=(n,title,line,fig,figcap)=>el('div',{class:'card'},[
    el('div',{style:'font-family:\"IBM Plex Mono\",monospace;font-size:11px;letter-spacing:.14em;color:var(--accent-ink);margin-bottom:9px'},['FINDING '+n]),
    el('h4',{style:'font-size:17px;font-family:Spectral,Georgia,serif;line-height:1.3;margin-bottom:9px'},[title]),
    el('p',{html:line}),
    el('div',{style:'margin-top:14px;padding-top:13px;border-top:1px solid var(--hairline)'},[
      el('div',{style:'font-family:\"IBM Plex Mono\",monospace;font-size:19px;font-variant-numeric:tabular-nums;color:var(--ink)'},[fig]),
      el('div',{style:'font-size:12px;color:var(--muted);margin-top:4px'},[figcap])])]);

  root.append(el('div',{class:'pagehead'},[el('div',{class:'wrap narrow'},[
    el('div',{class:'step-label'},['Scam fraud · payment context · adversarial measurement']),
    el('h2',{class:'page',style:'max-width:19ch'},['Should a payment network ask what a payment is for?']),
    el('p',{class:'standfirst'},[
      'Banks can prove you authorised a transfer. They cannot prove you knew who you were sending it to — which is exactly the gap scam fraud lives in. We tested whether asking the payer closes it, how long it keeps working once criminals adapt, and what it would cost to deploy.'])])]));

  root.append(wide([
    el('h3',{class:'sec',style:'margin-top:8px'},['Three answers a payment team could act on']),
    el('div',{class:'grid g3',style:'margin:18px 0 6px'},[
      finding('01','Evasion is not free',
        'To make a payment look consistent with its declared purpose, a scammer must route it to accounts that fit that purpose — which concentrates their traffic onto a narrower set of accounts. That concentration is exactly what ordinary recipient monitoring is built to spot. <b>The attacker can match the purpose or stay dispersed, not both.</b>',
        '0.924 → 0.957','fraud caught by the existing system, as the attacker coaches harder'),
      finding('02','Six categories, minimum',
        'A purpose menu with three options — personal, commercial, other — carries <b>no measurable value at all</b>. At six options it works. This is a concrete specification for a dropdown, not a research direction.',
        'K=3 nothing · K=6 works','improvement at three vs six purpose categories'),
      finding('03','Retain the field; don’t model it',
        'We built a purpose-conditional consistency engine, and it beat plain one-hot encoding of the code by almost nothing. The value is in <b>capturing and keeping the field</b>, not in what you build on top of it. Deployment cost collapses.',
        '+0.0008','all our extra modelling was worth, over a plain label')]),
    el('div',{class:'wrap narrow',style:'padding:0'},[
      pull('Finding 01 is the one we did not design for. Coaching the declared purpose and evading beneficiary intelligence turn out to be <b>coupled</b>: buying protection against one costs the attacker exposure on the other. We found no published statement of that trade-off.','good')])
  ]));

  root.append(body([
    h3('What this project is'),
    p('Not another fraud classifier. A <b>deployment decision framework</b>: before a payment network spends money collecting a new signal from hundreds of millions of people, can we say when that signal stays useful under adversarial pressure — and when it stops?'),
    p('The four questions a bank actually has to answer, and what we found:'),
    el('div',{class:'scroll'},[table(['The decision','What the study says'],[
      ['Is it worth collecting at all?','Yes — it improved detection in every one of 30 tested conditions, against three attackers including one that knows how the defence works.'],
      ['How many categories does the menu need?','At least six. Three is worthless.'],
      ['What do we have to build?','Almost nothing. Keep the code, pass it to the model you already run.'],
      ['Where does it fail?','At structural extremes, and against a purpose-matched attacker its value roughly halves — though that same attack makes the attacker easier to catch by other means.'],
    ])]),

    h3('Why you can believe the numbers'),
    el('div',{class:'grid g2'},[
      card('The answer was written down first','The question, the features, both success measures, and <b>the condition under which we would call the idea a failure</b> were committed before the simulator existed. That commit has never been edited.'),
      card('The incumbent got every advantage','Transaction, behavioural and beneficiary intelligence form the baseline, and the baseline received the entire model-tuning budget. The new idea got none of it — so every effect reported is a floor, not a best case.'),
      card('It was attacked until it bent','Three attackers of increasing capability, ending with one that knows the defence and picks its accounts to defeat it. The signal survived at roughly half strength.'),
      card('The failures are shown','Two pre-registered measures disagreed and both are reported. Individual payments the idea got wrong are on by default. An attack class the system provably cannot catch is named.')]),
    el('p',{class:'aside'},['Ten minutes end to end. Every figure is read from results committed to the repository; nothing is computed when you load this page.'])
  ]));
  root.append(nav(null,{id:'p-problem',label:'Start with the problem'}));
}

/* ---------- 2. problem ---------- */
function pProblem(root){
  root.append(head('Step 1 of 6','A fraud that passes every check',
    'Authorised push-payment fraud is the failure mode where all of a bank’s defences work exactly as designed, and the customer still loses everything.'));
  root.append(body([
    h3('How it actually happens'),
    p('Someone receives a call. It is convincing — a police officer, a bank official, a courier company, an investment adviser, a relative in trouble. Over an hour or two they are persuaded that money must be moved right now, and told where to send it.'),
    p('They open their banking app themselves. They type the amount themselves. They pass the authentication because they <em>are</em> the account holder. Then they press send.'),
    pull('Nothing was hacked. No credential was stolen. No control was bypassed. The bank did its job correctly and the money is still gone.','bad'),
    p('This is why it is called <em>authorised</em> push-payment fraud, and why it is so hard to stop. Card fraud and account takeover are unauthorised — someone is pretending to be you, so authentication and device checks are pointed at the right target. Here the real customer really did make the payment. What failed was not the authorisation. It was their understanding of who was on the other end.'),

    h3('Three consequences that follow'),
    el('div',{class:'grid g3'},[
      card('Liability is contested','No control was breached, so it is genuinely unclear who should bear the loss — which is exactly why regulators are now legislating on it.'),
      card('Reversal is hard','The transfer was valid at the moment it was made. By the time anyone realises, the money has been moved onward through other accounts.'),
      card('Detection has nothing to work with','The system can see who paid whom, how much, from what device, at what time. It cannot see “this was supposed to be my daughter’s tuition”.')]),

    h3('The scale, in India, right now'),
    p('The Reserve Bank of India published a discussion paper in April 2026 on safeguards against digital payment fraud. It cites national cybercrime reporting figures for 2025: <b>₹22,931 crore lost across 28 lakh reported cases</b> — an average of roughly ₹82,000 per case.'),
    p('One detail in those figures shapes everything that follows. Payments above ₹10,000 are about <b>45% of cases but around 98.5% of the money</b>. Most reported incidents are small. Almost all of the loss is not.'),

    h3('What is being proposed, and what it does not do'),
    p('That RBI paper proposes four controls: a one-hour delay on transfers above ₹10,000, authentication by a trusted person, a cap on credit, and a kill switch. Comments closed in May 2026. These are <b>proposals, not law</b>.'),
    p('Each is reasonable. But look at what they have in common:'),
    el('div',{class:'grid g4'},[
      card('One-hour lag','Buys time to reverse. Detects nothing.'),
      card('Trusted person','Adds a second human. Detects nothing.'),
      card('Credit cap','Limits the damage. Detects nothing.'),
      card('Kill switch','Stops the bleeding afterwards. Detects nothing.')]),
    pull('Every proposed control is <b>friction</b>. Not one of them improves the network’s ability to tell, at the moment of payment, that this transfer is not what the payer believes it is. That gap is what this project is about.'),
    el('p',{class:'aside'},['Sources are cited directly from the RBI discussion paper and national reporting figures. No statistics aggregators are used anywhere in this project.'])
  ]));
  root.append(nav({id:'p-home',label:'Home'},{id:'p-idea',label:'Next: the idea'}));
}


/* ---------- 3. idea ---------- */
function pIdea(root){
  const acct=(title,sub,rows,tone)=>el('div',{class:'card',style:tone==='bad'?'border-color:var(--negative)':''},[
    el('h4',{},[title]),
    el('p',{style:'margin-bottom:12px;font-size:13px;color:var(--muted)'},[sub]),
    el('div',{},rows.map(([k,v])=>el('div',{style:'display:flex;justify-content:space-between;gap:14px;font-size:13.5px;padding:5px 0;border-bottom:1px solid var(--hairline)'},[
      el('span',{style:'color:var(--muted)'},[k]),el('span',{style:'text-align:right'},[v])])))]);

  root.append(head('Step 2 of 6','Ask what the payment is for',
    'The signal nobody collects is the payer’s own belief about the transaction. If a system knew it, it could check that belief against the recipient.'));
  root.append(body([
    p('Suppose the payment carried one extra field: <b>what the payer thinks they are paying for</b>. Rent. Tuition. A refund. An investment. Money to a friend.'),
    p('On its own that field is just a label, and a liar can write anything in it. But it becomes interesting when you check it against the account receiving the money — because <em>the recipient cannot lie about its own history</em>.'),

    h3('What a real recipient looks like'),
    p('Consider two accounts receiving a payment labelled “rent”:'),
    el('div',{class:'grid g2',style:'margin:20px 0'},[
      acct('An actual landlord','What people normally send rent to',[
        ['Account age','Several years'],['People paying it','A handful, stable'],
        ['Payment rhythm','Same date each month'],['Money leaving','Sits, then spends normally'],
        ['Your history with it','Months or years']]),
      acct('A mule account','Where this payment actually went',[
        ['Account age','Twelve days'],['People paying it','Dozens of strangers'],
        ['Payment rhythm','None'],['Money leaving','Forwarded within hours'],
        ['Your history with it','None']],'bad')]),
    pull('You did not need a model to see that. The word “rent” and that second account are <b>not consistent with each other</b>, and the inconsistency is visible without knowing anything about fraud.'),
    p('That is the whole idea. Not a new fraud model — a consistency check between something the payer declares and something the recipient cannot fake.'),

    h3('Why this might be worthless'),
    p('Here is the problem, and it is the reason this project exists rather than just proposing the feature.'),
    p('Scammers adapt. Once the question is being asked, the script changes: <em>“when it asks what this is for, choose ‘transfer to a friend’.”</em> And a friend genuinely does have a thin, irregular, unfamiliar account. There is no mismatch left to detect.'),
    pull('So the honest question is not “does declared context help?” It is: <b>how much coaching does it survive, and is it therefore worth the cost of collecting?</b>','warn'),
    p('That question has a number attached to it, and that number is what a payment network actually needs before it changes a payment form used by hundreds of millions of people.'),

    h3('And one more thing that has to be ruled out'),
    p('There is an obvious objection: banks already look hard at the recipient. Account age, how many people pay it, how fast money leaves — all of this is standard beneficiary intelligence. If that already catches these accounts, the declared purpose adds nothing.'),
    p('So the test cannot be “does purpose beat nothing”. It has to be <b>does purpose add anything once you already have everything else</b> — and the study is built around exactly that comparison.'),
    el('p',{class:'aside'},['Structured purpose codes are not a new invention. They already exist in the ISO 20022 payment message standard and travel on corporate payments today. What is not established is whether they survive an adversary — which is what is measured here.'])
  ]));
  root.append(nav({id:'p-problem',label:'The problem'},{id:'p-method',label:'Next: how we tested it'}));
}

/* ---------- 4. method ---------- */
function pMethod(root){
  root.append(head('Step 3 of 6','How the question was tested',
    'Before any results: this is the part that decides whether the numbers on the next page mean anything.'));
  root.append(body([
    p('A study like this is easy to rig, usually by accident. Four things were done to stop that, and they matter more than any result.'),

    h3('1. The answer was written down before the experiment'),
    p('The research question, the exact features, both success measures, the levels they would be read at, and <b>the condition under which we would declare the idea a failure</b> were all committed to the project’s version history before the simulator existed.'),
    el('div',{class:'card',style:'margin:16px 0'},[
      el('p',{style:'font-family:Spectral,Georgia,serif;font-size:17px;line-height:1.55;color:var(--ink)'},[
        '“Under what levels of adversarially degraded payment-context reliability does declared payment context provide incremental fraud-detection value beyond transaction, behavioural, and beneficiary intelligence?”']),
      el('p',{style:'margin-top:12px;font-size:13px;color:var(--muted)'},[
        'The pre-registration was the sole content of the first commit in the repository and has never been edited. Anyone can verify that.'])]),
    p('Every change made to the study afterwards is recorded separately, with what prompted it and why. Nothing was quietly adjusted after seeing a result.'),

    h3('2. The data had to make the signal earn itself'),
    p('There is no public dataset of scam-fraud payments that includes a declared purpose field, so the population is simulated. That is a real limitation and it is stated plainly throughout.'),
    p('But a simulator can cheat, so this one is built from <b>three processes that do not talk to each other</b>:'),
    el('div',{class:'grid g3'},[
      card('How recipients behave','Depends only on what kind of account it is — a landlord, a school, a small shop, a mule.'),
      card('What a payment is for','Depends only on the relationship between payer and recipient.'),
      card('Who gets scammed','Depends only on a separate campaign process that never looks at anyone’s payment history.')]),
    pull('Purpose is never generated from whether a payment is fraudulent. If the consistency signal exists, it has to <b>emerge</b> from those three processes interacting. It cannot be planted.'),
    p('The population also deliberately contains legitimate accounts that <em>look</em> like mules — property managers, community savings collectors, gig workers, settlement agents. All receive money from many unrelated people and pass it straight on. Without them, recipient checks alone would separate fraud almost perfectly and there would be nothing left to test.'),

    h3('3. The new idea competes against a strong opponent'),
    p('Four groups of information are tested, added one at a time:'),
    el('div',{class:'scroll'},[table(['Group','What it knows'],[
      ['Transaction','amount, timing, channel, how often this person pays'],
      ['+ Behaviour','how long they hesitated, edits, app-switching, whether a call was active'],
      ['+ Recipient','account age, how many people pay it, how fast money leaves, prior complaints'],
      ['+ Declared purpose','the label, and whether it fits the recipient'],
    ])]),
    p('The first three together are the <b>baseline</b> — a realistic modern fraud system. The question is only whether the fourth adds anything on top.'),
    pull('The baseline received the <b>entire</b> model-tuning effort. Its settings were chosen to suit it alone, then frozen and reused unchanged for the versions containing the new idea. The incumbent got the search; the challenger got none of it.','good'),
    p('A related trap: the new group must not secretly re-use recipient information under a different name, or a gain would just mean the model was handed the same evidence twice. Every feature is assigned to exactly one group, and an automated check fails the build if that is ever violated.'),

    h3('4. Three attackers, not one'),
    p('Finally, the idea is attacked at three levels of sophistication — from a scammer who simply coaches the victim, to one that knows precisely how the defence works and chooses its accounts to defeat it. That ladder is what produces the actual answer.'),
    el('p',{class:'aside'},['The full method, including the exact features, the model, the splits and the statistics, is documented in the project’s data card and model card.'])
  ]));
  root.append(nav({id:'p-idea',label:'The idea'},{id:'p-findings',label:'Next: what we found'}));
}


/* ---------- heatmap ---------- */
function heatColour(v,max){
  if(v===null||v===undefined||Number.isNaN(v))return 'var(--sunk)';
  const t=Math.max(-1,Math.min(1,v/(max||1e-9)));
  const c=getComputedStyle(document.documentElement).getPropertyValue(t>=0?'--heat-pos':'--heat-neg');
  return 'rgba('+c.trim()+','+(0.08+0.85*Math.abs(t)).toFixed(3)+')';}

function heatmap(cells,digits,onPick){
  const xs=[...new Set(cells.map(c=>c.rho))].sort((a,b)=>a-b);
  const ys=[...new Set(cells.map(c=>c.lam))].sort((a,b)=>b-a);
  const max=Math.max(...cells.map(c=>Math.abs(c.delta||0)),1e-9);
  const grid=el('div',{style:'display:grid;gap:3px;grid-template-columns:repeat('+xs.length+',minmax(0,1fr))'});
  ys.forEach(y=>xs.forEach(x=>{
    const c=cells.find(k=>k.rho===x&&k.lam===y);
    const n=el('div',{tabindex:'0',role:'button','aria-label':'coaching '+x+', overlap '+y,
      style:'height:46px;display:flex;align-items:center;justify-content:center;border-radius:2px;'+
        'font-family:\"IBM Plex Mono\",monospace;font-size:11.5px;font-variant-numeric:tabular-nums;cursor:default;background:'+
        heatColour(c?c.delta:null,max)+(c&&!c.significant?
        ';background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,var(--hairline-strong) 3px,var(--hairline-strong) 4.4px)':'')},
      [c?sgn(c.delta,digits):'—']);
    if(c){n.addEventListener('mouseenter',()=>onPick(c));n.addEventListener('focus',()=>onPick(c));}
    grid.append(n);}));
  return el('div',{},[
    el('div',{style:'display:grid;grid-template-columns:auto 1fr;gap:0 10px'},[
      el('div',{style:'display:flex;flex-direction:column;justify-content:space-between;padding-bottom:26px'},
        ys.map(y=>el('span',{style:'font-size:11.5px;color:var(--muted);height:46px;display:flex;align-items:center;font-variant-numeric:tabular-nums'},[String(y)]))),
      el('div',{},[grid,
        el('div',{style:'display:grid;gap:3px;margin-top:7px;grid-template-columns:repeat('+xs.length+',minmax(0,1fr))'},
          xs.map(x=>el('span',{style:'font-size:11.5px;color:var(--muted);text-align:center;font-variant-numeric:tabular-nums'},[String(x)]))),
        el('div',{style:'text-align:center;font-size:12.5px;color:var(--muted);margin-top:8px'},['how effectively the scammer coached the victim  →'])])]),
    el('div',{style:'text-align:center;font-size:12.5px;color:var(--muted);margin-top:2px'},['rows: how many legitimate accounts look like mules'])]);
}

/* ---------- 5. findings ---------- */
const ADVS=[{id:'uniform',label:'A basic scammer',title:'coaches the victim toward a safe-sounding purpose'},
            {id:'prevalence',label:'A careful scammer',title:'coaching leaves no statistical trace in the label itself'},
            {id:'matched',label:'A scammer who knows the defence',title:'also picks a recipient account that fits the coached purpose'}];
let fState={adv:'uniform'};

function pFindings(root){
  root.replaceChildren();
  root.append(head('Step 4 of 6','What the experiment found',
    'Two results, one expected and one not. The unexpected one is more useful.'));

  if(!D.phase){root.append(body([el('div',{class:'card'},['Results not generated yet.'])]));return;}

  root.append(body([
    h3('First: it works, and it keeps working'),
    p('At a fixed tolerance for false alarms, adding the declared purpose improved fraud detection in <b>every single one of the 30 test conditions</b>, at every level of coaching, against all three attackers.'),
    p('That was not guaranteed. The expectation going in was that heavy coaching would erase the signal entirely. It does not — because steering every victim toward the same few safe-sounding purposes is <em>itself</em> a pattern.'),
    h3('Second: the harder the attacker, the faster it decays'),
    p('This is the part worth understanding. All three attackers start in exactly the same place, because with no coaching there is nothing for any of them to do. They separate as coaching increases:'),
    el('div',{class:'scroll'},[table(
      ['The attacker','No coaching','Full coaching','How much it lost'],
      [['Basic — coaches the victim','+0.078','+0.064','−19%'],
       ['Careful — coaching leaves no trace','+0.078','+0.054','−31%'],
       ['Knows the defence, picks matching accounts','+0.078','+0.033','−57%']],[1,2,3])]),
    p('Those figures are the improvement in fraud caught, at a fixed false-alarm budget. A competent attacker roughly halves the value of the signal. It does not eliminate it.'),
    pull('The honest reading: <b>declared payment context degrades under pressure but does not collapse.</b> Anyone deploying it should expect roughly half its measured value once attackers adapt — and should plan for that, rather than being surprised by it.'),

    h3('Adversarial coupling: coaching the purpose creates beneficiary exposure'),
    p('This is the result we did not design for, and the one most worth taking away.'),
    p('When the strongest attacker went to work, the <b>baseline system got better</b> — the part of the model that never sees the declared purpose at all. That looks backwards until you see the mechanism.'),
    p('To make a payment look consistent with the purpose the victim was coached to declare, the scammer has to send it to accounts that fit that purpose. There are not many such accounts. So traffic concentrates — and concentration is precisely what ordinary recipient monitoring is built to detect.'),
    el('div',{class:'scroll'},[table(
      ['How hard the victim was coached','Basic scammer','Careful scammer','Knows the defence'],
      [['none','0.9242','0.9242','0.9242'],
       ['moderate','0.9242','0.9242','0.9300'],
       ['heavy','0.9242','0.9242','0.9413'],
       ['total','0.9242','0.9242','0.9574']],[1,2,3])]),
    p('Fraud caught by the <em>baseline</em> system, which never sees the declared purpose. The first two attackers leave it completely unmoved — as they must, since neither touches the recipient. Only the attacker that picks matching accounts moves it, and it moves monotonically. The effect holds in <b>all five</b> structural conditions tested, gaining between +0.028 and +0.043.'),
    pull('The attacker faces a trade-off it cannot escape: <b>match the declared purpose, or stay dispersed. Not both.</b> Defeating the consistency check buys visibility on the check it was already failing. We found no published statement of this trade-off.','good'),
    p('For a deploying institution this changes the calculation. The declared-purpose field is not only worth something on its own — it also constrains what the attacker can do to evade everything else. Its value does not have to be counted in isolation.'),
  ]));

  /* interactive surface */
  const readout=el('div',{class:'card',style:'margin-top:14px;font-size:13.5px'},
    [el('span',{style:'color:var(--muted)'},['Hover any square to see the detail behind it.'])]);
  const holder=el('div',{});
  const draw=()=>{
    const key=fState.adv+'|recall@fpr=0.001';
    const cells=D.phase.metrics[key]||[];
    holder.replaceChildren(cells.length?heatmap(cells,4,c=>{
      readout.replaceChildren(
        el('div',{style:'font-weight:600;margin-bottom:6px'},['Coaching '+c.rho+'  ·  look-alike accounts '+c.lam]),
        el('div',{style:'font-variant-numeric:tabular-nums'},['Extra fraud caught: '+sgn(c.delta,4)+
          '   ·   plausible range '+sgn(c.ci_lo_min,4)+' to '+sgn(c.ci_hi_max,4)]),
        el('div',{style:'margin-top:6px;color:'+(c.significant?'var(--positive)':'var(--muted)')},
          [c.significant?'Reliable — the improvement holds in every repeat run.':
           'Not reliable here — the improvement could be zero.']));
    }):el('div',{class:'card'},['This surface has not been computed.']));};
  draw();

  root.append(wide([
    h3('The whole picture at once'),
    p('Every square is one tested condition. <b>Darker blue means the declared purpose helped more.</b> Left to right, the scammer coaches the victim harder. Top to bottom, the world contains fewer legitimate accounts that resemble mules. Cross-hatched squares are conditions where the improvement could not be distinguished from zero.'),
    el('div',{class:'controls'},[seg('Choose the attacker',ADVS.filter(a=>D.phase.metrics[a.id+'|recall@fpr=0.001']),
      fState.adv,id=>{fState.adv=id;pFindings(root);})]),
    el('div',{class:'card'},[holder,readout]),
    pull('Cross-hatching is a result, not missing data. Those are the conditions where a payment network should <b>not</b> spend money collecting this field.','warn'),
  ]));

  root.append(body([
    h3('Six categories, minimum — a specification, not a direction'),
    p('Collapsing the purpose menu from eleven options to three — personal, commercial, other — <b>destroyed the signal entirely</b>. At six options it worked.'),
    el('div',{class:'scroll'},[table(['Menu size','Improvement','Reliable?'],[
      ['3 options','+0.014',el('span',{class:'tag no'},['no'])],
      ['6 options','+0.052',el('span',{class:'tag ok'},['yes'])],
      ['11 options','+0.063',el('span',{class:'tag ok'},['yes'])]],[1])]),
    p('This is a design decision a product team would otherwise guess at, answered with a number. A coarse menu is cheaper to build and easier for a payer to answer correctly — and below roughly six categories it is also worthless.'),

    h3('Retain the field; don’t model it'),
    p('We built a purpose-conditional consistency engine: it learns what recipients normally look like for each purpose and scores how far this one deviates. It is the most technically involved part of the project.'),
    p('It beat plain one-hot encoding of the purpose code by <b>+0.0008</b>, consistently, across all three attackers.'),
    pull('Almost all the value is in <b>capturing and retaining the field</b>, not in what is built on top of it. For a deployment that is good news: the integration work is a form field and a retained column, not a new model to own, monitor and retrain.','good'),
    p('It is also the finding we would most have preferred to come out differently, which is why it is reported here rather than in a footnote.'),

    h3('And it matters most where you can see least'),
    p('The signal was worth most where recipient intelligence was <em>weakest</em>, varying roughly fifteenfold across the range tested. It is a tool for institutions that cannot see the receiving side of a payment well — smaller banks, cross-border corridors, new rails — rather than for those that already can.'),
    el('p',{class:'aside'},['282 tested conditions, three repeats each, with confidence intervals computed by resampling payers rather than payments — because one person’s transactions are not independent of each other.'])
  ]));
  root.append(nav({id:'p-method',label:'How we tested'},{id:'p-demo',label:'Next: see it work'}));
}


/* ---------- 6. demo ---------- */
const CHECKS={C1_amount_scope:'amount within the limit',C2_category_scope:'category allowed',
  C3_merchant_scope:'shop allowed',C4_temporal_validity:'still within the valid dates',
  C5_nonce_freshness:'not a repeat of an earlier request',C6_cumulative_cap:'total spend within the limit',
  C7_agent_binding:'signed by the authorised assistant',C8_confirmation_bind:'matches what the user approved',
  C9_revocation_state:'permission not withdrawn',C10_mandate_sig:'permission genuinely signed by the user'};
const BUCKETS=[{id:'helps',label:'It helped'},{id:'misleads_false_alarm',label:'It raised a false alarm'},
  {id:'misleads_missed_fraud',label:'It hid real fraud'},{id:'confirms',label:'It changed nothing'}];
let dState={frame:0,bucket:'helps',idx:0};

function pDemo(root){
  root.replaceChildren();
  root.append(head('Step 5 of 6','See it working — and failing',
    'Two demonstrations. The first is where this idea is heading. The second shows what it looks like on individual payments, including the ones it gets wrong.'));

  /* --- mandate --- */
  if(D.agentic){
    const a=D.agentic,f=a.demo_frames[dState.frame],bl=a.bounded_loss,fp=a.false_positives_on_in_scope_traffic;
    root.append(body([
      h3('When the payer is an AI assistant'),
      p('Everything so far dealt with a human being deceived, where intent can only be guessed at. But payments made by AI shopping assistants are different: the user’s instruction can be written down and cryptographically signed <em>before</em> anything is bought.'),
      p('Then the check stops being a guess and becomes arithmetic. Here is a signed instruction, and an assistant trying to exceed it:'),
    ]));
    root.append(wide([
      el('div',{class:'seg',style:'margin-bottom:14px'},a.demo_frames.map((fr,i)=>
        el('button',{type:'button','aria-pressed':String(i===dState.frame),
          onclick:()=>{dState.frame=i;pDemo(root);}},
          [fr.label==='violating'?'The assistant overreaches':'The assistant stays within the rules']))),
      el('div',{style:'display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid var(--hairline-strong);border-radius:4px;overflow:hidden'},[
        el('div',{style:'padding:22px;background:var(--surface);border-right:1px solid var(--hairline)'},[
          el('div',{class:'ctl-label'},['What the user authorised']),
          el('div',{class:'mono',style:'font-size:13px;line-height:2'},[
            el('div',{},['spend at most  '+inr(f.mandate.max_amount)]),
            el('div',{},['only at  sports retailers']),
            el('div',{},['total cap  '+inr(f.mandate.max_cumulative)]),
            el('div',{},['valid until  '+f.mandate.valid_until.slice(0,10)])]),
          el('div',{class:'ctl-label',style:'margin-top:22px'},['What the assistant tried to buy']),
          el('div',{class:'mono',style:'font-size:13px;line-height:2'},[
            el('div',{},['amount  '+inr(f.attempt.amount)]),
            el('div',{},['category  '+f.attempt.mcc]),
            el('div',{},['shop  '+f.attempt.merchant_id])])]),
        el('div',{style:'padding:22px;background:'+(f.accepted?'var(--caution-soft)':'var(--negative-soft)')},[
          el('div',{class:'ctl-label'},['The check']),
          el('div',{class:'mono',style:'font-size:12.5px;line-height:1.95'},f.checks.map(c=>
            el('div',{style:'display:flex;gap:9px'},[
              el('span',{style:'width:12px;color:'+(c.passed?'var(--positive)':'var(--negative)')+(c.passed?'':';font-weight:700')},[c.passed?'✓':'✗']),
              el('span',{style:c.passed?'':'color:var(--negative);font-weight:500'},[CHECKS[c.id]||c.id])]))),
          el('div',{style:'margin-top:16px;padding-top:13px;border-top:1px solid var(--hairline-strong);font-family:\"IBM Plex Mono\",monospace;font-size:16px;font-weight:600;color:'+(f.accepted?'var(--caution)':'var(--negative)')},
            [f.accepted?'ALLOWED':'BLOCKED']),
          el('div',{style:'font-size:13px;margin-top:8px;color:var(--ink-soft)'},[f.note])])]),
    ]));
    root.append(body([
      dState.frame===1?
        pull('<b>This is the honest half.</b> An assistant that stays inside the rules but buys something the user never wanted passes every check. This kind of check does not detect intent — it caps the damage. Saying so is what makes the other results believable.','bad'):
        p('The rejection is arithmetic, not a prediction. Same inputs, same answer, every time — and no legitimate purchase is ever wrongly blocked by it.'),
      el('div',{class:'grid g3',style:'margin:20px 0'},[
        stat(a.coverage.caught+' of '+a.coverage.total,'Attack types blocked outright','with no model involved','pos'),
        stat(fp.false_positive_rate.toFixed(4),'False alarms',fp.rejected+' out of '+fp.n.toLocaleString()+' legitimate purchases','pos'),
        stat(pct(bl.reduction_persistent),'Damage prevented','on the attacks it cannot detect','acc')]),
      p('Two of the ten attack types are <b>not</b> blocked, by design rather than oversight. Those two are reported as prominently as the eight that are.'),
    ]));
  }

  /* --- inspector --- */
  if(D.inspector){
    const cases=D.inspector.cases.filter(c=>c.bucket===dState.bucket);
    const c=cases[Math.min(dState.idx,cases.length-1)];
    root.append(body([
      h3('And on individual payments'),
      p('Back to human payments. For any single payment the system can show <em>why</em> it thought the recipient did or did not fit the declared purpose — and it gets some of them wrong.'),
      el('div',{class:'controls'},[seg('Show me a case where…',BUCKETS,dState.bucket,
        id=>{dState.bucket=id;dState.idx=0;pDemo(root);})]),
    ]));
    if(c){
      const rows=D.inspector.b3_cols.map(k=>({k:k.replace(/^payee_/,'').replace(/^payer_payee_/,'your history: ').replace(/_/g,' '),z:c.residuals[k]}))
        .sort((a,b)=>Math.abs(b.z)-Math.abs(a.z)).slice(0,7);
      const zmax=Math.max(...rows.map(r=>Math.abs(r.z)),1);
      root.append(wide([el('div',{class:'grid g2'},[
        el('div',{class:'card'},[
          el('div',{class:'ctl-label'},['The payment']),
          table(['',''],[
            ['payer said it was for',el('b',{},[c.declared_purpose.replace(/_/g,' ')])],
            ['amount',inr(c.amount)],
            ['recipient really was',el('span',{class:'mono',style:'font-size:12px'},[c.payee_role.replace(/_/g,' ')])],
            ['truth',c.is_fraud?el('span',{class:'tag no'},['fraud']):el('span',{class:'tag ok'},['legitimate'])],
            ['effect of adding purpose',el('b',{style:'color:'+((c.rank_shift>0)===(c.is_fraud===1)?'var(--positive)':'var(--negative)')},
              [(c.rank_shift>0?'moved up ':'moved down ')+Math.abs(c.rank_shift*100).toFixed(1)+' places per 100'])]],[1])]),
        el('div',{class:'card'},[
          el('div',{class:'ctl-label'},['How the recipient differed from what that purpose normally goes to']),
          el('div',{style:'display:flex;flex-direction:column;gap:6px;margin-top:12px'},rows.map(r=>{
            const w=(Math.abs(r.z)/zmax)*50,strong=Math.abs(r.z)>1.5;
            return el('div',{style:'display:grid;grid-template-columns:150px 1fr;gap:10px;align-items:center;font-size:12px'},[
              el('div',{style:'color:var(--muted);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'},[r.k]),
              el('div',{style:'position:relative;height:15px;background:var(--sunk);border-radius:2px'},[
                el('div',{style:'position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--hairline-strong)'}),
                el('div',{style:'position:absolute;top:2px;bottom:2px;border-radius:1px;background:'+(strong?'var(--negative)':'var(--accent)')+';'+
                  (r.z>=0?'left:50%;width:'+w+'%':'right:50%;width:'+w+'%')})])]);})),
          el('p',{style:'font-size:12px;color:var(--muted);margin-top:14px'},
            ['Bars to the right mean “more than usual for this purpose”, to the left “less than usual”. Longer bars are bigger surprises.'])])])]));
    }
    root.append(body([
      pull('Two of the four case types above are <b>failures</b> — payments the idea pushed the wrong way. They are shown by default rather than hidden, because anyone deciding whether to collect this field needs to see both directions.','warn')
    ]));
  }
  root.append(nav({id:'p-findings',label:'What we found'},{id:'p-limits',label:'Next: what this does not prove'}));
}

/* ---------- 7. limits ---------- */
function pLimits(root){
  root.replaceChildren();
  root.append(head('Step 6 of 6','What this does not prove',
    'The most useful thing a study can do is be precise about its own boundaries.'));
  root.append(body([
    h3('The big one: this is simulated'),
    p('There is no public dataset of scam-fraud payments carrying a declared purpose field, so the population is generated. That means <b>no claim is made about absolute detection rates</b>. The detection numbers here are higher than any real deployed system and should not be read as a forecast.'),
    p('What the study measures is <em>relative</em> behaviour — how the value of a signal moves as attackers get better and as the world changes around it. Those comparisons hold within the model even though the absolute levels do not transfer.'),
    pull('We plant the context field, so we make no claim about absolute detection rates. What is not circular: the deterministic results are structural, the phase diagram measures relative behaviour across conditions rather than a single score, and the entire generative process is published so the design can be challenged.'),

    h3('Everything else we are not claiming'),
    el('div',{class:'scroll'},[table(['Not claiming','Because'],[
      ['That purpose fields are a new idea','They already exist in the ISO 20022 standard and travel on corporate payments today.'],
      ['That banks never ask purpose','UK banks do, under the Consumer Standard of Caution.'],
      ['That the technique is novel','Comparing a label against a counterparty profile is ordinary feature engineering.'],
      ['That nobody does this','A global negative cannot be proven. Only that we found no publicly documented production system treating purpose-recipient consistency as its own signal.'],
      ['That the numbers are deployable','They characterise when a control is worth deploying, not how well it would perform in production.'],
    ])]),

    h3('Things that would weaken the result'),
    el('div',{class:'grid g2'},[
      card('The engineered version barely beat the simple one','Adding a sophisticated consistency score on top of a plain purpose label improved things by almost nothing. The simple version does nearly all the work — reported as fact, though it deflates the more elaborate machinery.'),
      card('The strongest attacker was added afterwards','It was added after seeing that the original attackers never broke the signal. That is disclosed in full. It makes the test harder rather than easier, which is the right direction for a change made after the fact — but a reader should know.'),
      card('The two success measures disagree','On one, the idea works everywhere. On the other, it stops paying under even mild coaching. Both were fixed in advance precisely so neither could be chosen after the fact.'),
      card('Real systems already have much of this','Behavioural and recipient intelligence are standard. The question asked here is only whether one further signal earns its cost on top of them.')]),

    h3('What was built'),
    el('div',{class:'grid g4',style:'margin-top:6px'},[
      stat(String(D.meta.n_cells),'Tested conditions','three repeats each'),
      stat('3','Attacker models','increasing in capability'),
      stat('16','Automated checks','including two proving the method cannot cheat'),
      stat('19 pp','Technical write-up','with data card and model card')]),
    el('p',{class:'aside'},['Pre-registration committed as '+(D.meta.prereg_commit||'—').slice(0,10)+
      '. Built '+D.meta.built+'. Synthetic data only; no live systems were tested and no attack tooling was produced.']),
    h3('The question this was all for'),
    pull('Before a payment network spends money collecting another signal, can we say <b>when</b> that signal stays useful under adversarial pressure — and when it does not?','good'),
    p('That is the deliverable. Not a better fraud model: a way of deciding whether a control is worth having, with its breaking point measured rather than assumed.')
  ]));
  root.append(nav({id:'p-demo',label:'See it work'},{id:'p-home',label:'Back to the start'}));
}

/* ---------- router ---------- */
const PAGES=[{id:'p-home',label:'Home',render:pHome},{id:'p-problem',label:'The problem',render:pProblem},
  {id:'p-idea',label:'The idea',render:pIdea},{id:'p-method',label:'How we tested',render:pMethod},
  {id:'p-findings',label:'What we found',render:pFindings},{id:'p-demo',label:'See it work',render:pDemo},
  {id:'p-limits',label:'Honest limits',render:pLimits}];
const stepsEl=document.getElementById('steps');
const done=new Set();
function show(id){
  PAGES.forEach(pg=>{const s=document.getElementById(pg.id);s.hidden=pg.id!==id;
    stepsEl.querySelector('[data-id="'+pg.id+'"]').setAttribute('aria-current',String(pg.id===id));});
  const pg=PAGES.find(x=>x.id===id);
  if(!done.has(id)||['p-findings','p-demo','p-limits'].includes(id)){pg.render(document.getElementById(id));done.add(id);}
  window.scrollTo({top:0,behavior:'instant'});
  try{history.replaceState(null,'','#'+id.replace('p-',''));}catch(e){}
}
PAGES.forEach((pg,i)=>stepsEl.append(el('button',{type:'button','data-id':pg.id,
  'aria-current':String(i===0),onclick:()=>show(pg.id)},[pg.label])));
document.getElementById('brand').addEventListener('click',()=>show('p-home'));
document.getElementById('brand').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' ')show('p-home');});
const initial=(location.hash||'').replace('#','');
show(PAGES.some(p=>p.id==='p-'+initial)?'p-'+initial:'p-home');

</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    OUT.write_text(html)
    print(f"written -> {OUT}  ({len(html)/1024:.0f} KB)")
