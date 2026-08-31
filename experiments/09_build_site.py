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
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

</style>
</head>
<body>
<div class="bar"><div class="wrap">
  <div class="brand" id="brand" role="button" tabindex="0"><b>Pramana</b><i>a valid means of proof</i></div>
  <nav class="tabs" id="tabs"></nav>
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

/* ---------- 1 home ---------- */
function pHome(root){
  const find=(n,t,x,num,cap)=>el('div',{class:'find'},[
    el('div',{class:'n'},['FINDING '+n]),el('h4',{},[t]),el('p',{html:x}),
    el('div',{class:'num'},[num]),el('div',{class:'cap'},[cap])]);
  root.append(el('div',{class:'pg'},[el('div',{class:'wrap'},[
    el('div',{class:'kicker'},['Scam fraud · payment context · adversarial measurement']),
    el('h2',{class:'t',style:'max-width:20ch'},['Should a payment network ask what a payment is for?']),
    el('p',{class:'lede'},['A bank can prove you authorised a transfer. It cannot prove you knew who you were sending it to. We tested whether asking the payer closes that gap, how long it keeps working once criminals adapt, and what it would cost to deploy.'])])]));
  root.append(W([el('div',{class:'grid g3',style:'margin-top:30px'},[
    find('01','Evasion is not free',
      'To make a payment look consistent with its declared purpose, a scammer must send it to accounts that fit — and few do. Their traffic concentrates, and concentration is what recipient monitoring already catches.',
      '0.924 → 0.957','fraud the existing system caught, as the attacker coached harder'),
    find('02','Six categories, minimum',
      'A three-option menu — personal, commercial, other — carried no measurable value. At six options it worked. That is a dropdown specification, not a research direction.',
      'K=3 nothing · K=6 works','improvement at three versus six purpose categories'),
    find('03','Keep the field, don’t model it',
      'We built a consistency engine that learns what recipients normally look like per purpose. It beat plain one-hot encoding of the code by almost nothing.',
      '+0.0008','all the extra modelling was worth')])]));
  root.append(sec([W([h3('The finding we did not design for')]),
    W([fig(figCoupling(),
      'The attacker’s dilemma. Left: spread payments across whatever accounts are available — the recipient monitor stays quiet, but the declared purpose does not match any of them. Right: route only to accounts that fit the declared purpose — the purpose check goes quiet, but six payments funnel into two accounts and the recipient monitor fires.',
      'Two panels comparing dispersed routing, where the purpose check fires, against purpose-matched routing, where the recipient check fires instead')]),
    W([take('takeaway','The attacker can match the declared purpose <b>or</b> stay dispersed. Not both. Buying protection against one check costs exposure on the other — so the value of this field is not only what it catches itself, but what it forces the attacker to give up. We found no published statement of this trade-off.','good')])]));
  root.append(sec([COL([h3('What this project is'),
    p('Not another fraud classifier. A <b>deployment decision</b>: before a payment network asks hundreds of millions of people a new question, can we say when the answer stays useful under adversarial pressure — and when it stops?')]),
    W([tbl(['The decision a bank faces','What the study says'],[
      ['Is it worth collecting?','Yes — it helped in all 30 tested conditions, against three attackers including one that knows the defence.'],
      ['How many menu options?','At least six. Three is worthless.'],
      ['What must we build?','Almost nothing. Keep the code; pass it to the model you already run.'],
      ['Where does it fail?','At structural extremes, and its value roughly halves against a purpose-matched attacker.']])])]));
  root.append(nav(null,{id:'p-problem',label:'Start with the problem'}));
}

/* ---------- 2 problem ---------- */
function pProblem(root){
  root.append(head('Step 1 of 6','A fraud where every check correctly says yes',
    'The customer is authenticated, on their own device, sending their own money. Nothing is bypassed. The money still goes.'));
  root.append(sec([W([fig(figScam(),
    'A scam payment as the bank sees it. Every control passes, because every control is true: the customer really is the customer. The one fact that would have flagged it — what the payer believed they were paying for — is never recorded.',
    'A payment passing four green checks into a twelve-day-old scammer account, with the payer’s belief shown as an unrecorded dashed box')])]));
  root.append(sec([COL([
    p('This is why it is called <b>authorised</b> push-payment fraud, and why it is hard. Card fraud is unauthorised — someone pretends to be you, so authentication is aimed at the right target. Here the real customer really did send the money. What failed was their understanding of who was on the other end.'),
    h3('The scale, in India, now'),
    p('The Reserve Bank of India’s April 2026 discussion paper cites national reporting for 2025: <b>₹22,931 crore across 28 lakh cases</b>, roughly ₹82,000 per case. Payments above ₹10,000 are about 45% of cases but around <b>98.5% of the money</b>.'),
    h3('Four controls have been proposed. None of them detects anything.')]),
    W([el('div',{class:'grid g3'},[
      card('One-hour lag','Buys time to reverse.'),
      card('Trusted person','Adds a second human.'),
      card('Credit cap','Limits the damage.')])]),
    W([take('takeaway','Every proposed control is <b>friction</b>. Not one improves the ability to tell, at the moment of payment, that this transfer is not what the payer believes it is. That gap is what this project measures.','warn')])]));
  root.append(nav({id:'p-home',label:'Home'},{id:'p-idea',label:'The idea'}));
}

/* ---------- 3 idea ---------- */
function pIdea(root){
  root.append(head('Step 2 of 6','Ask what the payment is for',
    'The label alone is worthless — a liar writes anything. It becomes useful when checked against the recipient, because the recipient cannot lie about its own history.'));
  root.append(sec([W([fig(figConsistency(),
    'The check. Rent normally goes to accounts with years of history, a handful of regular payers, a monthly rhythm and money that stays put. This recipient sits nowhere near that. The word and the account are not consistent with each other.',
    'A range showing what rent recipients normally look like, with a landlord inside it and the actual recipient far outside')])]));
  root.append(sec([COL([
    p('No model is needed to see the mismatch. That is the whole idea: a consistency check between something the payer declares and something the recipient cannot fake.'),
    h3('Why it might be worthless'),
    p('Scammers adapt. Once the question is asked, the script changes: <em>“when it asks what this is for, choose transfer to a friend.”</em> And a friend genuinely does have a thin, irregular account. No mismatch is left.')]),
    W([take('the real question','Not “does this help?” but <b>how much coaching does it survive, and is it therefore worth collecting?</b> That question has a number attached, and the number is what a payment network needs before changing a form used by hundreds of millions of people.')]),
    COL([h3('And one thing that must be ruled out'),
      p('Banks already study the recipient — age, how many people pay it, how fast money leaves. If that already catches these accounts, the declared purpose adds nothing. So the test cannot be “purpose versus nothing”. It has to be <b>purpose versus everything else you already have</b>.')])]));
  root.append(nav({id:'p-problem',label:'The problem'},{id:'p-method',label:'How we tested it'}));
}

/* ---------- 4 method ---------- */
function pMethod(root){
  root.append(head('Step 3 of 6','How the question was tested',
    'This is the part that decides whether the numbers on the next page mean anything.'));
  root.append(sec([COL([h3('The answer was written down first'),
    p('The question, the features, both success measures, and <b>the condition under which we would call the idea a failure</b> were committed before the simulator existed. That commit has never been edited.')]),
    W([take('committed first','“Under what levels of adversarially degraded payment-context reliability does declared payment context provide incremental fraud-detection value beyond transaction, behavioural, and beneficiary intelligence?”')])]));
  root.append(sec([W([h3('The data cannot plant the answer')]),
    W([fig(figProcesses(),
      'Three generators that never consult each other. What a payment is for is decided by the relationship; who gets scammed is decided by a separate campaign. Purpose is never derived from whether a payment is fraudulent, so if a consistency signal exists it has to emerge rather than be planted.',
      'Three independent generators feeding one ledger, with a crossed-out link between the purpose generator and the fraud generator')]),
    COL([p('The population also contains legitimate accounts that <em>look</em> like mules — property managers, savings-group collectors, gig workers. Without them, recipient checks alone would separate fraud almost perfectly and there would be nothing left to test.')])]));
  root.append(sec([COL([h3('The new idea competes against a strong opponent'),
    p('Transaction, behavioural and recipient intelligence together form the baseline. The baseline received the <b>entire</b> model-tuning budget; the new idea got none of it — so every result reported is a floor, not a best case.')]),
    W([h3('Then it was attacked until it bent')]),
    W([fig(figLadder(),
      'Three attackers of increasing capability. The first controls only what the victim types. The second also controls the statistics of those words, so the label carries no information by itself. The third additionally chooses which account receives the money.',
      'Three attacker rows showing which of the label, its statistics and the receiving account each one controls')]),
    W([take('takeaway','Each rung adds exactly one capability, so the surfaces can be compared against each other. The third attacker is assumed to <b>know the defence</b> and score accounts against the defender’s own reference.')])]));
  root.append(nav({id:'p-idea',label:'The idea'},{id:'p-findings',label:'What we found'}));
}

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
function figScam(){
  const y=64,bw=132,bh=52,gap=34;
  let s='';
  const steps=[['Payer','the real customer'],['Password','correct'],['Device','recognised'],['Amount','unremarkable']];
  steps.forEach((st,i)=>{const x=20+i*(bw+gap);
    s+=BOX(x,y,bw,bh)+T(x+bw/2,y+22,st[0],{w:600,s:13})+T(x+bw/2,y+39,st[1],{s:11.5,c:'var(--muted)'});
    s+=T(x+bw/2,y-10,'✓',{s:15,c:'var(--pos)',w:700});
    if(i<3)s+=LINE(x+bw,y+bh/2,x+bw+gap-8,y+bh/2,{m:'ar'});});
  const mx=20+4*(bw+gap);
  s+=LINE(mx-gap,y+bh/2,mx-8,y+bh/2,{m:'arN',c:'var(--neg)'});
  s+=BOX(mx,y,150,bh,{stroke:'var(--neg)',fill:'var(--neg-soft)'})+
     T(mx+75,y+22,'Scammer’s account',{w:600,s:13,c:'var(--neg)'})+T(mx+75,y+39,'12 days old',{s:11.5,c:'var(--neg)'});
  s+=BOX(20,y+96,bw*2+gap,46,{dash:'5 4',fill:'none'})+
     T(20+(bw*2+gap)/2,y+118,'What the payer believed',{w:600,s:13})+
     T(20+(bw*2+gap)/2,y+134,'never recorded, never checked',{s:11.5,c:'var(--muted)'});
  s+=LINE(20+bw*2+gap+10,y+119,mx-10,y+119,{dash:'4 4',c:'var(--muted)',w:1.2});
  s+=T((20+bw*2+gap+mx)/2,y+112,'the only thing that would have flagged it',{s:11,c:'var(--muted)'});
  return {vb:'0 0 880 230',body:s};
}

/* 2 — the consistency check */
function figConsistency(){
  let s='';
  const x0=90,x1=800,ymid=118;
  s+=T(20,42,'Recipients that people normally send RENT to',{a:'start',w:600,s:13});
  s+=BOX(x0,ymid-34,300,68,{fill:'var(--accent-soft)',stroke:'var(--accent)',r:34});
  s+=T(x0+150,ymid+5,'the usual range',{s:12,c:'var(--accent-ink)'});
  s+=LINE(x0-40,ymid,x1,ymid,{c:'var(--line-2)',w:1.2});
  s+=T(x0+150,ymid+56,'years old · few payers · same date monthly · money stays',{s:11.5,c:'var(--muted)'});
  s+=BOX(x0+110,ymid-52,80,26,{fill:'var(--pos-soft)',stroke:'var(--pos)'})+
     T(x0+150,ymid-34,'landlord',{s:11.5,w:600,c:'var(--pos)'});
  s+=LINE(x0+150,ymid-26,x0+150,ymid-8,{c:'var(--pos)',w:1.2});
  const mx=640;
  s+=BOX(mx-58,ymid-52,116,26,{fill:'var(--neg-soft)',stroke:'var(--neg)'})+
     T(mx,ymid-34,'this recipient',{s:11.5,w:600,c:'var(--neg)'});
  s+=LINE(mx,ymid-26,mx,ymid-8,{c:'var(--neg)',w:1.2});
  s+='<circle cx="'+mx+'" cy="'+ymid+'" r="6" style="fill:var(--neg)"/>';
  s+=T(mx,ymid+30,'12 days old · dozens of strangers · no rhythm',{s:11.5,c:'var(--neg)'});
  s+=T(mx,ymid+47,'money forwarded within hours',{s:11.5,c:'var(--neg)'});
  s+=LINE(x0+300+14,ymid-20,mx-20,ymid-20,{c:'var(--neg)',w:1.3,dash:'5 4',m:'arN'});
  s+=T((x0+300+mx)/2+2,ymid-28,'distance from normal',{s:11,c:'var(--neg)'});
  return {vb:'0 0 880 200',body:s};
}

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
function figCoupling(){
  let s='';const py=44,ph=180,pw=396;
  const panel=(x,title,sub)=>{
    let g=BOX(x,py,pw,ph,{fill:'var(--surface)'});
    g+=T(x+pw/2,py+26,title,{w:600,s:14.5});
    g+=T(x+pw/2,py+45,sub,{s:11.5,c:'var(--muted)'});
    return g;};
  /* left: dispersed */
  s+=panel(20,'Stay spread out','send to whatever account is free');
  const sx=76,sy=py+92;
  s+='<circle cx="'+sx+'" cy="'+sy+'" r="13" style="fill:var(--sunk);stroke:var(--line-2)"/>'+T(sx,sy+4,'₹',{s:12});
  for(let i=0;i<6;i++){const tx=180+ (i%3)*68, ty=py+74+Math.floor(i/3)*46;
    s+=LINE(sx+14,sy,tx-11,ty,{c:'var(--muted)',w:1});
    s+='<circle cx="'+tx+'" cy="'+ty+'" r="9" style="fill:var(--raised);stroke:var(--line-2)"/>';}
  s+=T(228,py+ph-14,'6 accounts, none of them fits “rent”',{s:11.5,c:'var(--muted)'});
  s+=BOX(258,py+62,150,26,{fill:'var(--pos-soft)',stroke:'var(--pos)'})+
     T(333,py+80,'recipient check: quiet',{s:11.5,c:'var(--pos)',w:600});
  s+=BOX(258,py+120,150,26,{fill:'var(--neg-soft)',stroke:'var(--neg)'})+
     T(333,py+138,'purpose check: FIRES',{s:11.5,c:'var(--neg)',w:600});
  /* right: matched */
  const ox=462;
  s+=panel(ox,'Match the declared purpose','only a few accounts look like a landlord');
  const mx2=ox+56,my=py+92;
  s+='<circle cx="'+mx2+'" cy="'+my+'" r="13" style="fill:var(--sunk);stroke:var(--line-2)"/>'+T(mx2,my+4,'₹',{s:12});
  for(let i=0;i<6;i++){const ty=py+78+ (i%2)*30;
    s+=LINE(mx2+14,my,ox+142,ty,{c:'var(--neg)',w:1.1});}
  s+='<circle cx="'+(ox+152)+'" cy="'+(py+78)+'" r="10" style="fill:var(--neg-soft);stroke:var(--neg);stroke-width:1.4"/>';
  s+='<circle cx="'+(ox+152)+'" cy="'+(py+108)+'" r="10" style="fill:var(--neg-soft);stroke:var(--neg);stroke-width:1.4"/>';
  s+=T(ox+196,py+ph-14,'all six funnel into 2 accounts',{s:11.5,c:'var(--neg)'});
  s+=BOX(ox+206,py+62,168,26,{fill:'var(--neg-soft)',stroke:'var(--neg)'})+
     T(ox+290,py+80,'recipient check: FIRES',{s:11.5,c:'var(--neg)',w:600});
  s+=BOX(ox+206,py+120,168,26,{fill:'var(--pos-soft)',stroke:'var(--pos)'})+
     T(ox+290,py+138,'purpose check: quiet',{s:11.5,c:'var(--pos)',w:600});
  s+=T(440,26,'the attacker must choose',{s:12,c:'var(--muted)',w:600});
  return {vb:'0 0 880 250',body:s};
}


/* ---------- heatmap ---------- */
function heatColour(v,max){
  if(v==null||Number.isNaN(v))return 'var(--sunk)';
  const t=Math.max(-1,Math.min(1,v/(max||1e-9)));
  const c=getComputedStyle(document.documentElement).getPropertyValue(t>=0?'--heat-pos':'--heat-neg');
  return 'rgba('+c.trim()+','+(0.08+0.85*Math.abs(t)).toFixed(3)+')';}
function heatmap(cells,onPick){
  const xs=[...new Set(cells.map(c=>c.rho))].sort((a,b)=>a-b);
  const ys=[...new Set(cells.map(c=>c.lam))].sort((a,b)=>b-a);
  const max=Math.max(...cells.map(c=>Math.abs(c.delta||0)),1e-9);
  const rows=el('div',{style:'display:flex;flex-direction:column;gap:4px'});
  ys.forEach(y=>{
    const r=el('div',{style:'display:grid;grid-template-columns:52px repeat('+xs.length+',minmax(0,1fr));gap:4px;align-items:center'});
    r.append(el('div',{style:'font-size:11.5px;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums'},[String(y)]));
    xs.forEach(x=>{const c=cells.find(k=>k.rho===x&&k.lam===y);
      const n=el('div',{tabindex:'0',role:'button','aria-label':'coaching '+x+', look-alikes '+y,
        style:'height:44px;display:flex;align-items:center;justify-content:center;border-radius:3px;'+
          'font-family:\"IBM Plex Mono\",monospace;font-size:11.5px;font-variant-numeric:tabular-nums;background:'+
          heatColour(c?c.delta:null,max)+(c&&!c.significant?
          ';background-image:repeating-linear-gradient(45deg,transparent,transparent 3px,var(--line-2) 3px,var(--line-2) 4.5px)':'')},
        [c?sgn(c.delta,3):'—']);
      if(c){n.addEventListener('mouseenter',()=>onPick(c));n.addEventListener('focus',()=>onPick(c));}
      r.append(n);});
    rows.append(r);});
  const axis=el('div',{style:'display:grid;grid-template-columns:52px repeat('+xs.length+',minmax(0,1fr));gap:4px;margin-top:8px'});
  axis.append(el('div',{}));
  xs.forEach(x=>axis.append(el('div',{style:'font-size:11.5px;color:var(--muted);text-align:center;font-variant-numeric:tabular-nums'},[String(x)])));
  return el('div',{},[rows,axis,
    el('div',{style:'font-size:12px;color:var(--muted);text-align:center;margin-top:8px'},['how hard the scammer coached the victim  →']),
    el('div',{style:'font-size:12px;color:var(--muted);text-align:center;margin-top:2px'},['rows ↓ how many legitimate accounts look like mules'])]);}

/* ---------- 5 findings ---------- */
const ADVS=[{id:'uniform',label:'Basic scammer'},{id:'prevalence',label:'Careful scammer'},
            {id:'matched',label:'Knows the defence'}];
let advSel='uniform';
function pFindings(root){
  root.replaceChildren();
  root.append(head('Step 4 of 6','What the experiment found',
    'It works, it keeps working under coaching, and the harder the attacker the more it costs them elsewhere.'));
  if(!D.phase){root.append(COL([p('Results not generated.')]));return;}

  root.append(sec([COL([h3('It survives coaching — at reduced strength'),
    p('All three attackers start in the same place: with no coaching there is nothing for any of them to do. They separate as coaching rises.')]),
    W([tbl(['The attacker','No coaching','Full coaching','Value lost'],
      [['Basic — coaches the victim','+0.078','+0.064','−19%'],
       ['Careful — leaves no statistical trace','+0.078','+0.054','−31%'],
       ['Knows the defence, picks matching accounts','+0.078','+0.033','−57%']],[1,2,3])]),
    COL([p('Extra fraud caught, at a fixed false-alarm budget. A competent attacker roughly halves the value. It does not remove it.')])]));

  root.append(sec([W([h3('Adversarial coupling — the result we did not design for')]),
    COL([p('When the strongest attacker went to work, the <b>baseline got better</b> — the part of the model that never sees the declared purpose at all.')])]),
    W([tbl(['How hard the victim was coached','Basic','Careful','Knows the defence'],
      [['none','0.9242','0.9242','0.9242'],['moderate','0.9242','0.9242','0.9300'],
       ['heavy','0.9242','0.9242','0.9413'],['total','0.9242','0.9242','0.9574']],[1,2,3])]),
    COL([p('Fraud caught by the baseline system. The first two attackers leave it <b>exactly</b> unmoved — as they must, since neither touches the recipient. Only the attacker that picks matching accounts moves it, and it moves steadily. The effect holds in all five structural conditions.')]),
    W([take('why it matters','Defeating the consistency check buys visibility on the check it was already failing. For a deploying bank the field’s value is not only what it catches — it is what it forces the attacker to give up.','good')]));

  const readout=el('div',{class:'card',style:'margin-top:16px;font-size:13.5px'},
    [el('span',{style:'color:var(--muted)'},['Hover any square for the detail behind it.'])]);
  const holder=el('div',{});
  const draw=()=>{const cells=D.phase.metrics[advSel+'|recall@fpr=0.001']||[];
    holder.replaceChildren(cells.length?heatmap(cells,c=>readout.replaceChildren(
      el('div',{style:'font-weight:600;margin-bottom:5px'},['Coaching '+c.rho+' · look-alike accounts '+c.lam]),
      el('div',{style:'font-variant-numeric:tabular-nums'},['Extra fraud caught '+sgn(c.delta,4)+
        '  ·  plausible range '+sgn(c.ci_lo_min,4)+' to '+sgn(c.ci_hi_max,4)]),
      el('div',{style:'margin-top:5px;color:'+(c.significant?'var(--pos)':'var(--muted)')},
        [c.significant?'Reliable — holds in every repeat run.':'Not reliable here — could be zero.'])
    )):el('div',{},['not computed']));};
  draw();
  root.append(sec([W([h3('Every condition at once'),
    el('p',{style:'max-width:62ch;margin-bottom:16px'},[
      'Each square is one tested condition. Darker blue means the declared purpose helped more. Cross-hatched squares are conditions where the improvement could not be told apart from zero.']),
    el('div',{style:'margin-bottom:16px'},[segCtl('Choose the attacker',
      ADVS.filter(a=>D.phase.metrics[a.id+'|recall@fpr=0.001']),advSel,id=>{advSel=id;pFindings(root);})]),
    el('div',{class:'figbox'},[holder,readout])])]));

  root.append(sec([COL([h3('Six categories, minimum'),
    p('Collapsing the menu from eleven options to three — personal, commercial, other — <b>destroyed the signal</b>. At six it worked.')]),
    W([tbl(['Menu size','Improvement','Reliable?'],
      [['3 options','+0.014',el('span',{class:'pill no'},['no'])],
       ['6 options','+0.052',el('span',{class:'pill ok'},['yes'])],
       ['11 options','+0.063',el('span',{class:'pill ok'},['yes'])]],[1])]),
    COL([h3('Keep the field, don’t model it'),
      p('Our purpose-conditional consistency engine — the most technically involved part of the project — beat plain one-hot encoding of the code by <b>+0.0008</b>, consistently, across all three attackers.')]),
    W([take('takeaway','Almost all the value is in <b>capturing and keeping the field</b>. Integration is a form field and a retained column, not a new model to own and retrain. It is the finding we would most have preferred to come out differently, which is why it is here and not in a footnote.','good')])]));
  root.append(nav({id:'p-method',label:'How we tested'},{id:'p-demo',label:'See it work'}));
}


/* ---------- 6 demo ---------- */
const CHK={C1_amount_scope:'amount within the limit',C2_category_scope:'category allowed',
  C3_merchant_scope:'shop allowed',C4_temporal_validity:'still in date',
  C5_nonce_freshness:'not a repeat request',C6_cumulative_cap:'total spend within limit',
  C7_agent_binding:'signed by the authorised assistant',C8_confirmation_bind:'matches what the user approved',
  C9_revocation_state:'permission not withdrawn',C10_mandate_sig:'permission genuinely signed'};
const BK=[{id:'helps',label:'It helped'},{id:'misleads_false_alarm',label:'False alarm'},
  {id:'misleads_missed_fraud',label:'It hid real fraud'},{id:'confirms',label:'No change'}];
let dFrame=0,dBucket='helps',dIdx=0;
function pDemo(root){
  root.replaceChildren();
  root.append(head('Step 5 of 6','See it working — and failing',
    'Where the payer is an AI assistant the intent can be signed in advance, so the check stops being a guess and becomes arithmetic.'));
  if(D.agentic){
    const a=D.agentic,f=a.demo_frames[dFrame],bl=a.bounded_loss,fp=a.false_positives_on_in_scope_traffic;
    root.append(sec([W([
      el('div',{style:'margin-bottom:16px'},[segCtl('Choose what the assistant does',
        a.demo_frames.map((fr,i)=>({id:String(i),label:fr.label==='violating'?'It overreaches':'It stays within the rules'})),
        String(dFrame),id=>{dFrame=+id;pDemo(root);})]),
      el('div',{class:'grid g2',style:'gap:0;border:1px solid var(--line-2);border-radius:5px;overflow:hidden'},[
        el('div',{style:'padding:22px;background:var(--surface);border-right:1px solid var(--line)'},[
          el('div',{class:'lbl'},['What the user authorised']),
          el('div',{class:'mono',style:'font-size:13px;line-height:2'},[
            el('div',{},['spend at most  '+inr(f.mandate.max_amount)]),
            el('div',{},['only at  sports retailers']),
            el('div',{},['total cap  '+inr(f.mandate.max_cumulative)])]),
          el('div',{class:'lbl',style:'margin-top:20px'},['What the assistant tried to buy']),
          el('div',{class:'mono',style:'font-size:13px;line-height:2'},[
            el('div',{},['amount  '+inr(f.attempt.amount)]),
            el('div',{},['shop  '+f.attempt.merchant_id])])]),
        el('div',{style:'padding:22px;background:'+(f.accepted?'var(--warn-soft)':'var(--neg-soft)')},[
          el('div',{class:'lbl'},['The check']),
          el('div',{class:'mono',style:'font-size:12.5px;line-height:1.9'},f.checks.map(c=>
            el('div',{style:'display:flex;gap:9px'},[
              el('span',{style:'width:12px;color:'+(c.passed?'var(--pos)':'var(--neg)')},[c.passed?'✓':'✗']),
              el('span',{style:c.passed?'':'color:var(--neg);font-weight:500'},[CHK[c.id]||c.id])]))),
          el('div',{class:'mono',style:'margin-top:16px;padding-top:13px;border-top:1px solid var(--line-2);font-size:16px;font-weight:600;color:'+(f.accepted?'var(--warn)':'var(--neg)')},
            [f.accepted?'ALLOWED':'BLOCKED']),
          el('div',{style:'font-size:13px;margin-top:8px;color:var(--ink-soft)'},[f.note])])])]),
      W([dFrame===1?
        take('the honest half','An assistant that stays inside the rules but buys something the user never wanted <b>passes every check</b>. This kind of check does not detect intent — it caps the damage. Saying so is what makes the other results believable.','bad'):
        take('note','The rejection is arithmetic, not a prediction. Same inputs, same answer, every time — and no legitimate purchase was ever wrongly blocked.')]),
      W([el('div',{class:'grid g3',style:'margin-top:20px'},[
        card(a.coverage.caught+' of '+a.coverage.total+' attack types blocked','with no model involved'),
        card(fp.rejected+' false alarms','out of '+fp.n.toLocaleString()+' legitimate purchases'),
        card(Math.round(bl.reduction_persistent*100)+'% damage prevented','on the attacks it cannot detect')])])]));
  }
  if(D.inspector){
    const cases=D.inspector.cases.filter(c=>c.bucket===dBucket);
    const c=cases[Math.min(dIdx,cases.length-1)];
    root.append(sec([COL([h3('And on individual human payments'),
      p('For any single payment the system can show <em>why</em> it thought the recipient did or did not fit the declared purpose — including when it was wrong.')]),
      W([el('div',{style:'margin-bottom:16px'},[segCtl('Show me a case where…',BK,dBucket,
        id=>{dBucket=id;dIdx=0;pDemo(root);})])])]));
    if(c){
      const rows=D.inspector.b3_cols.map(k=>({k:k.replace(/^payee_/,'').replace(/^payer_payee_/,'your history: ').replace(/_/g,' '),z:c.residuals[k]}))
        .sort((a,b)=>Math.abs(b.z)-Math.abs(a.z)).slice(0,7);
      const zmax=Math.max(...rows.map(r=>Math.abs(r.z)),1);
      root.append(W([el('div',{class:'grid g2'},[
        el('div',{class:'card'},[el('div',{class:'lbl'},['The payment']),
          tbl(['',''],[['payer said it was for',el('b',{},[c.declared_purpose.replace(/_/g,' ')])],
            ['amount',inr(c.amount)],
            ['recipient really was',c.payee_role.replace(/_/g,' ')],
            ['truth',c.is_fraud?el('span',{class:'pill no'},['fraud']):el('span',{class:'pill ok'},['legitimate'])],
            ['effect of adding purpose',el('b',{style:'color:'+((c.rank_shift>0)===(c.is_fraud===1)?'var(--pos)':'var(--neg)')},
              [(c.rank_shift>0?'moved up ':'moved down ')+Math.abs(c.rank_shift*100).toFixed(1)+' per 100'])]],[1])]),
        el('div',{class:'card'},[el('div',{class:'lbl'},['How this recipient differed from the usual for that purpose']),
          el('div',{style:'display:flex;flex-direction:column;gap:7px;margin-top:12px'},rows.map(r=>{
            const w=(Math.abs(r.z)/zmax)*50,strong=Math.abs(r.z)>1.5;
            return el('div',{style:'display:grid;grid-template-columns:145px 1fr;gap:10px;align-items:center;font-size:12px'},[
              el('div',{style:'color:var(--muted);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'},[r.k]),
              el('div',{style:'position:relative;height:15px;background:var(--sunk);border-radius:2px'},[
                el('div',{style:'position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--line-2)'}),
                el('div',{style:'position:absolute;top:2px;bottom:2px;border-radius:1px;background:'+(strong?'var(--neg)':'var(--accent)')+';'+
                  (r.z>=0?'left:50%;width:'+w+'%':'right:50%;width:'+w+'%')})])]);})),
          el('p',{style:'font-size:12px;color:var(--muted);margin-top:14px'},
            ['Right of centre: more than usual for that purpose. Left: less. Longer bars are bigger surprises.'])])])]));
    }
    root.append(W([take('shown by default','Two of the four case types are <b>failures</b> — payments the idea pushed the wrong way. Anyone deciding whether to collect this field needs to see both directions.','warn')]));
  }
  root.append(nav({id:'p-findings',label:'What we found'},{id:'p-limits',label:'What this does not prove'}));
}

/* ---------- 7 limits ---------- */
function pLimits(root){
  root.replaceChildren();
  root.append(head('Step 6 of 6','What this does not prove',
    'The most useful thing a study can do is be exact about its own edges.'));
  root.append(sec([COL([h3('It is simulated, and that bounds everything'),
    p('No public dataset of scam payments carries a declared-purpose field, so the population is generated. <b>No claim is made about absolute detection rates</b> — the levels here are higher than any deployed system and are not a forecast.'),
    p('What transfers is the <em>relative</em> behaviour: how a signal’s value moves as attackers improve and as the world around it changes.')]),
    W([take('the circularity answer','We plant the context field, so we make no claim about absolute detection rates. What is not circular: the deterministic results are structural, the surface measures relative behaviour across conditions rather than one score, and the entire generative process is published so the design can be challenged.')])]));
  root.append(sec([W([h3('Things that count against us')]),
    W([el('div',{class:'grid g2'},[
      card('The engineered version barely beat the simple one','Our consistency engine added +0.0008 over a plain label. Reported as fact, though it deflates the most elaborate part of the work.'),
      card('The strongest attacker was added later','After seeing the first two never broke the signal. Fully disclosed. It makes the test harder, not easier — the right direction for a change made after the fact.'),
      card('The two success measures disagree','On one, it works everywhere. On the other, it stops paying under mild coaching. Both were fixed in advance so neither could be chosen afterwards.'),
      card('Real systems already have much of this','Behavioural and recipient intelligence are standard. The question asked here is only whether one further signal earns its cost on top of them.')])])]));
  root.append(sec([W([h3('What was built')]),
    W([tbl(['','',''],[
      [String(D.meta.n_cells)+' tested conditions','3 attacker models','3 repeats each'],
      ['16 automated checks','2 of them prove the method cannot cheat','20-page technical write-up'],
      ['Pre-registration '+(D.meta.prereg_commit||'').slice(0,10),'never edited','built '+D.meta.built]])]),
    W([take('the question it was all for','Before a payment network spends money collecting another signal, can we say <b>when</b> that signal stays useful under adversarial pressure — and when it does not? That is the deliverable: not a better fraud model, but a way to decide whether a control is worth having, with its breaking point measured rather than assumed.','good')])]));
  root.append(nav({id:'p-demo',label:'See it work'},{id:'p-home',label:'Back to the start'}));
}

/* ---------- router ---------- */
const PAGES=[{id:'p-home',label:'Home',render:pHome},{id:'p-problem',label:'The problem',render:pProblem},
  {id:'p-idea',label:'The idea',render:pIdea},{id:'p-method',label:'How we tested',render:pMethod},
  {id:'p-findings',label:'What we found',render:pFindings},{id:'p-demo',label:'See it work',render:pDemo},
  {id:'p-limits',label:'Honest limits',render:pLimits}];
const tabsEl=document.getElementById('tabs');const done=new Set();
function show(id){
  PAGES.forEach(pg=>{document.getElementById(pg.id).hidden=pg.id!==id;
    tabsEl.querySelector('[data-id="'+pg.id+'"]').setAttribute('aria-current',String(pg.id===id));});
  const pg=PAGES.find(x=>x.id===id);
  if(!done.has(id)||['p-findings','p-demo','p-limits'].includes(id)){pg.render(document.getElementById(id));done.add(id);}
  window.scrollTo({top:0,behavior:'instant'});
  try{history.replaceState(null,'','#'+id.replace('p-',''));}catch(e){}}
PAGES.forEach((pg,i)=>tabsEl.append(el('button',{type:'button','data-id':pg.id,
  'aria-current':String(i===0),onclick:()=>show(pg.id)},[pg.label])));
document.getElementById('brand').addEventListener('click',()=>show('p-home'));
const init=(location.hash||'').replace('#','');
show(PAGES.some(p=>p.id==='p-'+init)?'p-'+init:'p-home');

</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = build()
    OUT.write_text(html)
    print(f"written -> {OUT}  ({len(html)/1024:.0f} KB)")
