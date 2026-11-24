# -*- coding: utf-8 -*-
"""Split the pre-campaign hub into a live NID Dec-26 tab and a
'Pre-campaign readiness (all rounds)' archive that stores the closed
SNID Nov-26 return and the fIPV Peshawar & Khyber pre-campaign scope."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

P = 'index.html'
s = open(P, encoding='utf-8', newline='').read()
assert s.count('\r\n') == s.count('\n') > 0, 'CRLF guard'
ORIG = len(s)


def rep(old, new, n=1):
    global s
    c = s.count(old)
    assert c == n, (c, n, old[:90])
    s = s.replace(old, new, n)


def crlf(t):
    return t.replace('\r\n', '\n').replace('\n', '\r\n')


# ---------------------------------------------------------------- 1. CSS
rep('.tab[data-tab="hcamp"],.tab[data-tab="cpre"],.tab[data-tab="cicm"],.tab[data-tab="cpost"],#p-hcamp,#p-cpre,#p-cicm,#p-cpost{--tc:#c2410c}',
    '.tab[data-tab="hcamp"],.tab[data-tab="cpre"],.tab[data-tab="pcra"],.tab[data-tab="cicm"],.tab[data-tab="cpost"],#p-hcamp,#p-cpre,#p-pcra,#p-cicm,#p-cpost{--tc:#c2410c}')

# ---------------------------------------------------------------- 2. nav tab
rep('   <button class="tab" data-tab="cpre"><span class="tl">Pre-campaign</span><span class="badge" id="bCP">–</span></button>',
    '   <button class="tab" data-tab="cpre"><span class="tl">Pre-campaign</span><span class="badge" id="bCP">–</span></button>\r\n'
    '   <button class="tab" data-tab="pcra"><span class="tl">Pre-campaign readiness</span><span class="badge" id="bPRA">all rounds</span></button>')

# ---------------------------------------------------------------- 3. hub prose
rep('The top block is the live NID Dec-26 readiness grid as districts file it; below it sits the closed SNID Nov-26 round and its final NEAP return. Pick a campaign from the dropdown to read an earlier round — one campaign is shown at a time.',
    'This page carries the live <b>NID Dec-26</b> round as districts file it: the NEAP grid, the core-team briefing and push list, the countdown calendar, a readiness chart and the district map. Closed rounds are stored on <b>Pre-campaign readiness (all rounds)</b> — the SNID Nov-26 final NEAP return with its MPQA, and the fIPV Peshawar &amp; Khyber pre-campaign scope. Pick an older campaign from the dropdown to read its preparatory indicators.')

rep('<div class="hubchips"><button data-hl="hcamp">← Campaign overview</button><button data-hl="cicm">Intra-campaign ops</button><button data-hl="cpost">Post-campaign analysis</button></div>',
    '<div class="hubchips"><button data-hl="hcamp">← Campaign overview</button><button data-hl="pcra">Pre-campaign readiness (all rounds)</button><button data-hl="cicm">Intra-campaign ops</button><button data-hl="cpost">Post-campaign analysis</button></div>')

# ---------------------------------------------------------------- 4. cqbar button
rep('<div class="cqbar"><b>Campaign</b><select id="fCPC" aria-label="Campaign"></select><span class="cnt" id="fCPCnote"></span></div>',
    '<div class="cqbar"><b>Campaign</b><select id="fCPC" aria-label="Campaign"></select><span class="cnt" id="fCPCnote"></span><span style="flex:1"></span><button class="btn" id="btnPRAopen" title="Every stored round&#39;s pre-campaign status in one place">Pre-campaign readiness (all rounds) →</button></div>')

# ---------------------------------------------------------------- 5. extract the Nov block
A = '<div class="hint" id="nepHint">'
B = '</div>\r\n<div id="cpreOld">'
a = s.index(A)
b = s.index(B, a)
NOV = s[a:b]
assert NOV.count('id="cardNEPB"') == 1 and NOV.count('id="cardMPQH"') == 1, 'Nov block bounds'
assert s.count(NOV) == 1, 'Nov block unique'

NOV2 = NOV.replace(
    'The scheduled NEAP refresh now reads the NID Dec-26 grid above: it picks the newest <code>NEAP*.xls</code> in Downloads and republishes that block automatically.',
    'The scheduled NEAP refresh now feeds the NID Dec-26 grid on the Pre-campaign tab: it picks the newest <code>NEAP*.xls</code> in Downloads and republishes that block automatically. This archive keeps the Nov-26 return exactly as it was filed when the round closed and is not refreshed.')
assert NOV2 != NOV and 'Pre-campaign tab:' in NOV2

# ---------------------------------------------------------------- 6. Dec block markup
DEC = crlf('''<div class="hint" id="decHint"></div>
<div class="card" id="cardBDEC" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Core-team briefing — NID Dec-26 pre-campaign progress &amp; push list</h3><span class="cnt" id="cntBDEC"></span><span class="cqbar" style="margin:0;gap:6px"><b>Division</b><select id="fDECdv" aria-label="Division"></select></span><span style="flex:1"></span><button class="btn pri" id="btnSITREPD" title="The NID Dec-26 pre-campaign SITREP deck, built from the live NEAP grid and the countdown calendar">▶ SITREP — NID Dec-26 (pptx)</button><span class="cnt" id="sitStatusD"></span><button class="btn" id="btnBDECcopy">Copy briefing</button></div><div id="bDec" style="font-size:13.5px;line-height:1.6"></div><div class="cap" id="capBDEC"></div></div>
<div class="card" id="cardDACT" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Activity countdown — NID Dec-26 calendar vs the live NEAP grid</h3><span class="cnt" id="cntDACT"></span><span style="flex:1"></span><button class="btn" id="btnDACTcsv">Download (CSV)</button></div><div id="dactG" class="scroll" style="max-height:640px"></div><div class="cap" id="capDACT"></div></div>
<div class="card" id="cardDECCHART" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Districts meeting each readiness column — live NID Dec-26 grid</h3><span class="cnt" id="cntDecChart"></span></div><div id="decChart" class="scroll"></div><div class="cap" id="capDecChart"></div></div>
<div class="card" id="cardDECMAP" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Readiness by district — live NID Dec-26 grid</h3><span class="cnt" id="cntDecMap"></span><span style="flex:1"></span><button class="btn" id="btnDecMapimg">Download (PNG)</button></div><div id="decMap"></div><div class="cap" id="decMapNote"></div><div class="cap" id="capDecMap"></div></div>''')

rep(NOV, DEC)

# ---------------------------------------------------------------- 7. archive pane
ARCH = crlf('''

<!-- ================= HUB: Pre-campaign readiness (all rounds) ================= -->
<section class="pane hubpane" id="p-pcra">
<div class="hubhd"><div><h2>Pre-campaign readiness — all rounds</h2><p>Every closed round&rsquo;s pre-campaign record, stored as it was read, so it does not move when the live round updates. Two stored views: the <b>SNID Nov-26</b> round closed in November with its final NEAP return, briefing, push list and MPQA; and the <b>fIPV Peshawar &amp; Khyber</b> pre-campaign scope. The live <b>NID Dec-26</b> round is not stored here because it is still filing — it sits on the Pre-campaign tab.</p><div class="hubchips"><button data-hl="hcamp">← Campaign overview</button><button data-hl="cpre">Live NID Dec-26 →</button><button data-hl="cicm">Intra-campaign ops</button><button data-hl="cpost">Post-campaign analysis</button></div></div></div>
<div class="cqbar"><b>Stored round</b><select id="fPRA" aria-label="Stored pre-campaign round"></select><span class="cnt" id="fPRAnote"></span><span style="flex:1"></span><button class="btn" id="btnPRAlive" title="Open the live NID Dec-26 pre-campaign tab">Live NID Dec-26 →</button></div>
<div id="praNov">__NOV__
</div>
<div id="praFipv" style="display:none">
<div class="card" id="cardPRAF" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">fIPV — Peshawar &amp; Khyber pre-campaign scope</h3><span class="cnt" id="cntPRAF"></span><span style="flex:1"></span><button class="btn" id="btnPRAFopen" title="Open the full fIPV page">Full fIPV page</button><button class="btn" id="btnPRAFcsv">Download (CSV)</button></div><div class="hint" id="prafHint"></div><div class="scroll"><table id="tPRAF"></table></div><div class="cap" id="capPRAF"></div></div>
</div>
</section>''').replace('__NOV__', NOV2)

rep('</section>\r\n\r\n<!-- ================= HUB: Intra-campaign monitoring (ICM) ================= -->',
    '</section>' + ARCH + '\r\n<!-- ================= HUB: Intra-campaign monitoring (ICM) ================= -->')

# ---------------------------------------------------------------- 8. hub chips (HRA pane)
rep('<button data-hl="hrat">HRA compilation</button><button data-hl="c3">Comparison &amp; monitoring</button><button data-hl="cpre">Pre-campaign readiness</button>',
    '<button data-hl="hrat">HRA compilation</button><button data-hl="c3">Comparison &amp; monitoring</button><button data-hl="cpre">Pre-campaign readiness (live)</button><button data-hl="pcra">Pre-campaign readiness (all rounds)</button>')

# ---------------------------------------------------------------- 9. TABS + dispatch + icon
rep("'c3','cpre','cicm','cpost'", "'c3','cpre','pcra','cicm','cpost'")
rep('cpre:renderCPre,cicm:renderCICM', 'cpre:renderCPre,pcra:renderPRA,cicm:renderCICM')
rep("hcamp:'flag',cpre:'clip',cicm:'search'", "hcamp:'flag',cpre:'clip',pcra:'clip',cicm:'search'")
rep("'Pre-campaign readiness':'clip',", "'Pre-campaign readiness':'clip','Pre-campaign readiness — all rounds':'clip',")

# ---------------------------------------------------------------- 10. campaign picker + renderCPre
rep("((NEAP&&NEAP.camp)||'SNID Nov-26')+' · pre-campaign activities (round closed)</option>'",
    "((NEPD&&NEPD.camp)||'NID Dec-26')+' · pre-campaign activities (live round)</option>'")

rep("if(isN){ el('fCPCnote').textContent='NID Dec-26 NEAP grid'+(NEPD&&NEPD.asof?' · as of '+NEPD.asof:'')+' · SNID Nov-26 final return'+(NEAP&&NEAP.asof?' · as of '+NEAP.asof:''); renderNEPD(); renderNEP(); renderMPQ(); return; }",
    "if(isN){ el('fCPCnote').textContent=((NEPD&&NEPD.camp)||'NID Dec-26')+' NEAP grid'+(NEPD&&NEPD.asof?' · as of '+NEPD.asof:'')+' · countdown calendar '+(typeof NACD!=='undefined'&&NACD?NACD.from+' to '+NACD.en:''); const ob=el('btnPRAopen'); if(ob)ob.onclick=()=>setTab('pcra'); renderNEPD(); renderDEC(); return; }")

# ---------------------------------------------------------------- 11. SITREP wiring
rep("const SIT_DECK_BTNS=[['btnSITREP','sitStatus'],['btnSITREP2','sitStatus2']];\r\nSIT_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runSITREP(b,el(p[1]));});",
    "const SIT_DECK_BTNS=[['btnSITREP','sitStatus']];\r\nSIT_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runSITREP(b,el(p[1]));});\r\n[['btnSITREP2','sitStatus2'],['btnSITREPD','sitStatusD']].forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runDSITREP(b,el(p[1]));});")

# ---------------------------------------------------------------- 12. presentations card
rep('<b>📅 Pre-campaign SITREP</b><small>A daily situation report in the house SITREP shape, for the core-team call: executive summary at a glance, Section 1 scope and resource plan, Section 2 preparation status (NEAP indicator board, every indicator by district, readiness spread), Section 3 the countdown calendar against what districts have actually filed, Section 4 micro-plan quality, the fIPV overlay for Peshawar &amp; Khyber, Section 5 push list and Section 6 the decisions asked of the core team. Scoped by the division picker on the Pre-campaign tab. About 12 slides.</small>',
    '<b>📅 Pre-campaign SITREP</b><small>A daily situation report in the house SITREP shape for the live <b>NID Dec-26</b> round: executive summary at a glance, filing by division, every district against the readiness columns, the countdown calendar against what districts have actually filed, the push list by tier and the decisions asked of the core team. Scoped by the division picker on the Pre-campaign tab. About 8 slides. The closed SNID Nov-26 final SITREP stays on Pre-campaign readiness (all rounds).</small>')

# ---------------------------------------------------------------- 13. archive pointers in prose
rep('This is the closed-round record, not live status — the NID Dec-26 grid above is the live one.',
    'This is the closed-round record, not live status — the live NID Dec-26 grid is on the Pre-campaign tab.')
rep("(t.id==='mpqa'?' The two flag columns are the same counts as the MPQA card on the Pre-campaign tab.':'')",
    "(t.id==='mpqa'?' The two flag columns are the same counts as the MPQA card on the Pre-campaign readiness tab.':'')")

# ---------------------------------------------------------------- 14. new JS block
JS = crlf(r'''// ---------- NID Dec-26 pre-campaign: briefing, countdown, chart and map ----------
let DECV='',PRAC='nov';
const DEC_K=['dpec','dc','dho','must','ucmo','ucsec','aic','trn','mpv','adult','loc','gov','fem','inacc'];
const DEC_L={dpec:'DPEC held',dc:'DC at DPEC',dho:'DHO at DPEC',must:'Must-members',ucmo:'UCMO present',ucsec:'UC secretary',aic:'AICs trained',trn:'Teams trained',mpv:'Microplans validated',adult:'Members 18+',loc:'Local member',gov:'Govt accountable',fem:'Female member',inacc:'Inaccessible areas'};
const DEC_BM={dpec:100,dc:100,dho:100,must:100,ucmo:100,ucsec:100,aic:100,trn:100,mpv:100,adult:95,loc:75,gov:75,fem:75};
const DEC_RD=['dpec','must','aic','trn','mpv'];
const DEC_DV={}; if(typeof KPGEO!=='undefined'&&KPGEO.d)KPGEO.d.forEach(p=>{DEC_DV[p.c]=p.v;});
const DEC_CALMAP={4:'dpec',6:'aic',7:'mpv',14:'trn'};
const DEC_CALN={dpec:'DPEC',aic:'AIC',trn:'Teams',mpv:'MPs'};
const decDvT=v=>v?v.charAt(0)+v.slice(1).toLowerCase():'';
const decAvg=a=>{a=a.filter(v=>v!=null&&!isNaN(v));return a.length?a.reduce((x,y)=>x+y,0)/a.length:null;};
function decNEPD(){return (typeof NEPD!=='undefined'&&NEPD&&NEPD.d)?NEPD:null;}
function decRows(all){
 const D=decNEPD(); if(!D)return [];
 const ex=D.extra||[];
 const out=Object.keys(D.d).map(dn=>{const v=D.d[dn],o={d:dn,dv:DEC_DV[dn]||'',_ex:ex.indexOf(dn)>=0};
  DEC_K.forEach((k,i)=>{o[k]=(v[i]==null||v[i]<0)?null:v[i];});
  const ms=DEC_RD.map(k=>o[k]).filter(x=>x!=null);
  o.rd=ms.length?ms.reduce((a,b)=>a+b,0)/ms.length:null;
  o.nf=DEC_K.filter(k=>k!=='inacc'&&o[k]!=null&&o[k]>0).length;
  o.stg=!o.nf?'n':(o.rd==null||o.rd<=0?'r':(o.rd>=100?'g':'m'));
  return o;});
 return all?out:out.filter(r=>!r._ex);
}
function decUC(){
 const D=decNEPD(), U=(D&&D.u&&D.u.r)||[], o={};
 U.forEach(a=>{const b=o[a[0]]||(o[a[0]]={n:0,f:0,dp:0}); b.n++; if(a.slice(3).some(v=>v>0))b.f++; if(a[3]>=100)b.dp++;});
 return o;
}
function decScope(){
 const RA=decRows(true), R=RA.filter(r=>!r._ex);
 const S=DECV?R.filter(r=>r.dv===DECV):R;
 const mx=k=>decAvg(S.map(r=>r[k]));
 const at100=k=>S.filter(r=>r[k]!=null&&r[k]>=100).length;
 const any=k=>S.filter(r=>r[k]!=null&&r[k]>0).length;
 const D=decNEPD();
 const dTo=D&&D.start?Math.ceil((new Date(D.start+'T00:00:00')-new Date())/864e5):null;
 const UC=decUC();
 const uSum=f=>S.reduce((a,r)=>a+(f(UC[r.d]||{n:0,f:0,dp:0})||0),0);
 return {D:D,RA:RA,R:R,S:S,n:S.length,nAll:R.length,mx:mx,at100:at100,any:any,dTo:dTo,
  dv:DECV,scope:DECV?decDvT(DECV)+' division':'Khyber Pakhtunkhwa (all districts)',
  uN:uSum(u=>u.n),uF:uSum(u=>u.f),uD:uSum(u=>u.dp),
  filed:S.filter(r=>r.nf>0),nothing:S.filter(r=>!r.nf),
  rd:decAvg(S.map(r=>r.rd)),rdAll:decAvg(R.map(r=>r.rd))};
}
function decCal(){
 const A=(typeof NACD!=='undefined'&&NACD&&NACD.a)?NACD.a:[];
 const tIso=nactIso(new Date()), st=NACD.st, en=NACD.en;
 return A.map(a=>{const ds=nactDl(a.s,tIso), de=nactDl(a.e,tIso);
  return {n:a.n,t:a.t,s:a.s,e:a.e,x:a.x||'',k:DEC_CALMAP[a.n]||'',ds:ds,de:de,
   ph:(a.e<st?'pre':(a.s<=en&&a.e>=st?'camp':'post')),
   stt:(de<0?'closed':(ds<=0?'running':'ahead'))};});
}
function renderDEC(){
 const X=decScope(), D=X.D, tb=el('bDec');
 const sel=el('fDECdv');
 const DVS=[...new Set(X.R.map(r=>r.dv).filter(Boolean))].sort();
 if(sel){
  if(sel.dataset.built!=='1'){
   sel.innerHTML='<option value="">All divisions (whole KP)</option>'+DVS.map(v=>'<option value="'+esc(v)+'">'+esc(decDvT(v))+' division ('+X.R.filter(r=>r.dv===v).length+')</option>').join('');
   sel.dataset.built='1'; sel.onchange=()=>{DECV=sel.value;renderDEC();};
  }
  if(DECV&&DVS.indexOf(DECV)<0)DECV='';
  sel.value=DECV;
  sel.title=DECV?'Briefing scoped to '+X.scope+' — '+X.n+' of '+X.nAll+' districts':'Briefing covers every division — all '+X.nAll+' districts';
 }
 if(!tb)return;
 if(!D){
  el('decHint').textContent='No NID Dec-26 NEAP grid is embedded in this build.';
  tb.innerHTML='<div class="empty">No NID Dec-26 grid loaded.</div>';
  ['decChart','decMap','dactG'].forEach(id=>{if(el(id))el(id).innerHTML='';});
  return;
 }
 const n=X.n, at=X.at100, any=X.any, mx=X.mx, dTo=X.dTo;
 const asof=nepDAd(D.asof), startTxt=D.start?nepDAd(D.start):'12-Dec-2026';
 const dToTxt=dTo==null?'':(dTo>0?' ('+dTo+' days)':dTo===0?' (today)':' ('+(-dTo)+' days ago)');
 el('decHint').innerHTML='Live status of the <b>'+esc(D.camp||'NID Dec-26')+'</b> round as districts file the EOC pre-campaign NEAP grid (<b>'+esc(D.src)+'</b> district-wise, <b>'+esc(D.srcu||'')+'</b> UC-wise, downloaded <b>'+esc(asof)+'</b>, campaign starting <b>'+esc(startTxt)+'</b>'+dToTxt+'): DPEC meetings and attendance, AIC and team training, microplan validation and team composition, district by district. Zeros are the portal zeros — a district that has not filed reads 0, not blank — and a dash means the cell was blank in the export. Only <b>'+at('dpec')+' of '+n+'</b> districts and <b>'+fmt(X.uD)+' of '+fmt(X.uN)+'</b> UCs have a DPEC filed so far. Closed rounds are stored on <b>Pre-campaign readiness (all rounds)</b>.';
 const CAL=decCal(), PRE=CAL.filter(a=>a.ph==='pre');
 const closed=PRE.filter(a=>a.stt==='closed'), running=PRE.filter(a=>a.stt==='running'), ahead=PRE.filter(a=>a.stt==='ahead');
 const mapped=PRE.filter(a=>a.k);
 const secs=[];
 const t1=X.nothing, t2=X.S.filter(r=>r.nf&&!(r.aic>0)), t3=X.S.filter(r=>r.aic>0&&r.aic<90);
 const held=X.S.filter(r=>r.dpec>=100);
 secs.push(['Filing status'+(DECV?' — '+X.scope:''),[
  '<b>'+X.filed.length+' of '+X.n+' districts</b> have filed any pre-campaign column; <b>'+held.length+'</b> report a DPEC held on time, DC attended in <b>'+at('dc')+'</b>, DHO in <b>'+at('dho')+'</b>.',
  'AIC training has started in <b>'+any('aic')+'</b> district'+(any('aic')===1?'':'s')+', team training in <b>'+any('trn')+'</b> and microplan validation in <b>'+any('mpv')+'</b> — '+(any('aic')+any('trn')+any('mpv')===0?'none of the three has begun anywhere.':'the countdown is ahead of the filing.'),
  'At UC level <b>'+fmt(X.uF)+' of '+fmt(X.uN)+' UCs</b> have filed anything and <b>'+fmt(X.uD)+'</b> a DPEC — '+pc(X.uN?X.uF/X.uN*100:null)+' of the grid has moved at all.',
  (dTo==null?'No campaign start date in the export.':(dTo>0?'<b>'+dTo+' days</b> to the '+startTxt+' start.':dTo===0?'The round starts today.':'The round started '+(-dTo)+' days ago.'))]]);
 if(!DECV){
  const gd={}; X.S.forEach(r=>{const v=r.dv||'Other'; (gd[v]=gd[v]||[]).push(r);});
  secs.push(['Division-wise filing',Object.keys(gd).sort().map(v=>{const g=gd[v], f=g.filter(r=>r.nf>0).length, h=g.filter(r=>r.dpec>=100).length, m=decAvg(g.map(r=>r.rd));
   return '<b>'+esc(decDvT(v))+'</b> ('+g.length+' districts) — filed '+f+'/'+g.length+', DPEC held '+h+'/'+g.length+', mean readiness '+(m==null?'–':rnd(m)+'%')+'.';})]);
 }else{
  secs.push([decDvT(DECV)+' division — districts',[X.S.map(r=>'<b>'+DNAME(r.d)+'</b> ('+(r.nf?'filed '+r.nf+' of 12 columns':'nothing filed')+', readiness '+(r.rd==null?'–':rnd(r.rd)+'%')+')').join(', ')+'.']]);
 }
 secs.push(['Against the countdown calendar',[
  'The NID Dec-26 calendar runs <b>'+esc(nactDm(NACD.from))+' to '+esc(nactDm(NACD.to))+'</b> with <b>'+CAL.length+' activities</b>, '+PRE.length+' of them before the '+esc(nactDm(NACD.st))+' campaign start: <b>'+closed.length+' closed</b>, <b>'+running.length+' in window today</b>, <b>'+ahead.length+' still ahead</b>.',
  'Four activities carry a NEAP reading: DPEC (4), AIC &amp; UCMO training (6), microplan desk review + field validation (7) and FLW team training (14) — '+(mapped.every(a=>!at(a.k))?'none of the four has a district at target yet.':'at target in '+mapped.map(a=>DEC_CALN[a.k]+' '+at(a.k)+'/'+n).join(', ')+'.'),
  (held.length?'<b>'+held.map(r=>DNAME(r.d)).join(' and ')+'</b> report'+(held.length===1?'s':'')+' a DPEC held on '+esc(nactDm(D.asof))+' — a day before the calendar DPEC window ('+esc(nactDm('2026-11-25'))+'–'+esc(nactDm('2026-11-26'))+') opens, so the dates are filed ahead of the plan, not behind it.':'No district has filed a DPEC yet; the calendar opens that window on 25–26 Nov.'),
  'Calendar source: <b>'+esc((typeof NACD!=='undefined'&&NACD&&NACD.src)||'')+'</b>, read '+esc((typeof NACD!=='undefined'&&NACD&&NACD.asof)?nepDAd(NACD.asof):'')+'.']]);
 secs.push(['Tier 1 — nothing filed yet',[t1.length?('**'+t1.length+' of '+n+' districts** have filed no pre-campaign column — the push list is every district except '+X.filed.map(r=>DNAME(r.d)).join(' and ')+'.').replace(/\*\*/g,'<b>').replace(/\*\*/g,'</b>'):'Every district has filed at least one column.'].map(x=>x.replace(/\*\*/g,''))]);
 // fix tier 1 bold without regex helper
 secs[secs.length-1][1]=[t1.length?('<b>'+t1.length+' of '+n+' districts</b> have filed no pre-campaign column — the push list is every district except '+X.filed.map(r=>DNAME(r.d)).join(' and ')+'.'):'Every district has filed at least one column.'];
 secs.push(['Tier 2 — filed, but AIC training never started',[t2.length?(t2.map(r=>'<b>'+DNAME(r.d)+'</b> ('+r.dv+')').join(', ')+' — start AIC and UCMO training in the 26–28 Nov window.'):'None — every district that filed has started AIC training.']]);
 secs.push(['Tier 3 — AIC training started but under 90%',[t3.length?(t3.map(r=>'<b>'+DNAME(r.d)+'</b> '+rnd(r.aic)+'%').join(', ')+' — close out before FLW training opens on 4-Dec.'):'None — no started district is under 90%.']]);
 secs.push(['What the countdown asks for next',[
  '<b>25–26 Nov</b> DPEC meetings and post-campaign review of SNID Nov-26 — the window every district owes next.',
  '<b>26–28 Nov</b> AIC &amp; UCMO training and the zero-dose list / microplan update.',
  '<b>30-Nov–1-Dec</b> microplan desk review and field validation; <b>2-Dec</b> UPEC; <b>2–3 Dec</b> IDIMS entry and real-time MPQA.',
  '<b>4–8 Dec</b> FLW team training; <b>8–9 Dec</b> logistics; <b>9–10 Dec</b> divisional readiness meeting; <b>12–18 Dec</b> campaign.']]);
 tb.innerHTML=secs.map(s=>'<div style="margin:10px 0 2px"><b>'+s[0]+'</b></div><ul style="margin:2px 0 8px;padding-left:18px">'+s[1].map(x=>'<li>'+x+'</li>').join('')+'</ul>').join('');
 el('cntBDEC').textContent=(D.camp?D.camp+' · ':'')+(DECV?X.scope+' · ':'')+'as of '+asof+(dTo!=null&&dTo>0?' · '+dTo+' days to start':'');
 el('capBDEC').textContent='Read live from '+D.src+' (district-wise) and '+(D.srcu||'')+' (UC-wise), downloaded '+asof+'. Readiness is the mean of DPEC held, must-members attended, AIC training, team training and microplan validation — it measures what districts have filed, not children reached. Zeros are portal zeros; BAR SWAT is the portal sub-unit for Swat and is kept out of the '+n+'-district counts here.';
 const TXT=[(D.camp||'NID Dec-26')+' pre-campaign status'+(DECV?' — '+X.scope:'')+' — as of '+asof+(dTo!=null&&dTo>0?' ('+dTo+' days to campaign start)':'')];
 secs.forEach(s=>{TXT.push('');TXT.push(s[0]+':');s[1].forEach(b=>TXT.push('• '+b.replace(/<[^>]+>/g,'')));});
 const cp=el('btnBDECcopy');
 if(cp)cp.onclick=()=>{const t=TXT.join('\n'); if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(()=>toast('Briefing copied to clipboard'),()=>toast('Could not access clipboard')); else toast('Copy not supported in this browser');};
 const sb=el('btnSITREPD'); if(sb)sb.onclick=()=>runDSITREP(sb,el('sitStatusD'));
 renderDACT(); renderDECChart(); renderDECMap();
}
function renderDACT(){
 const box=el('dactG'); if(!box)return;
 if(typeof NACD==='undefined'||!NACD||!(NACD.a||[]).length){if(el('cardDACT'))el('cardDACT').style.display='none';return;}
 const X=decScope(), D=X.D;
 const D2=x=>/^\d{4}-\d{2}-\d{2}$/.test(x||'')?new Date(x+'T00:00:00'):null;
 const iso=x=>x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0');
 const MN=NACT_MN;
 const days=[]; for(let x=D2(NACD.from),e2=D2(NACD.to);x<=e2;x.setDate(x.getDate()+1))days.push(new Date(x));
 const tIso=nactIso(new Date()), tI=days.findIndex(x=>iso(x)===tIso);
 const CL=NACTCL, WD=['S','M','T','W','T','F','S'];
 const TH='border:1px solid #e5e7eb;padding:1px 2px;font-weight:600;font-size:10.5px;text-align:center;';
 const TD='border:1px solid #eef0f3;padding:0;height:15px;';
 const hol={}; (NACD.notes||[]).forEach(n=>{hol[n.d]=n.t;});
 let ml='',c0=0;
 for(let i=1;i<=days.length;i++){ if(i===days.length||days[i].getMonth()!==days[c0].getMonth()){ ml+='<th colspan="'+(i-c0)+'" style="'+TH+'background:#f8fafc">'+MN[days[c0].getMonth()]+' '+days[c0].getFullYear()+'</th>'; c0=i; } }
 const dayRow=days.map(x=>{const t=iso(x)===tIso, c=x>=D2(NACD.st)&&x<=D2(NACD.en), h=hol[iso(x)];
  return '<th style="'+TH+(t?'background:#fee2e2;color:#b91c1c;':c?'background:#dcfce7;color:#166534;':h?'background:#fef3c7;color:#92400e;':'')+'">'+x.getDate()+'</th>';}).join('');
 const wdRow=days.map(x=>'<th style="'+TH+'font-weight:400;color:'+(iso(x)===tIso?'#b91c1c':'#6b7280')+'">'+WD[x.getDay()]+'</th>').join('');
 const rows=(NACD.a||[]).map(a=>{
  const km={};
  (a.b||[]).forEach(b=>{for(let x=D2(b[0]),e2=D2(b[1]);x<=e2;x.setDate(x.getDate()+1))km[iso(x)]=b[2];});
  const first=(a.b&&a.b[0])?a.b[0][0]:'';
  const cells=days.map((x,i)=>{const k2=km[iso(x)]; let s2=TD;
   if(k2)s2+='background:'+(CL[k2]||'#9ca3af')+';';
   else if(x.getDay()===0)s2+='background:#f3f4f6;';
   if(i===tI) s2+='box-shadow:inset 1px 0 0 #dc2626,inset -1px 0 0 #dc2626;';
   const seg=(a.b||[]).find(b=>b[0]<=iso(x)&&iso(x)<=b[1]);
   const ti=seg?esc(a.n+'. '+a.d+' ('+seg[0]+' to '+seg[1]+')'+(a.x?' | Calendar note: '+a.x:'')):(hol[iso(x)]?esc(hol[iso(x)]):'');
   const mk=(k2&&a.x&&iso(x)===first)?'<span style="color:#fff;font-size:9px;line-height:15px">*</span>':'';
   return '<td style="'+s2+'"'+(ti?' title="'+ti+'"':'')+'>'+mk+'</td>';}).join('');
  const k=DEC_CALMAP[a.n];
  let chip='';
  if(k&&D){const c=X.at100(k), v=X.mx(k), col=c===X.n?'#16a34a':(v>0?'#f59e0b':'#dc2626');
   chip='<span title="'+DEC_CALN[k]+' — NEAP status: '+c+' of '+X.n+' districts at target" style="display:inline-block;padding:1px 7px;border-radius:9px;font-size:10.5px;font-weight:600;color:#fff;background:'+col+'">'+DEC_CALN[k]+' '+c+'/'+X.n+'</span>';}
  const ph=a.e<NACD.st?'pre':(a.s<=NACD.en?'camp':'post');
  return '<tr><td style="border:1px solid #eef0f3;padding:2px 6px;font-size:11.5px;white-space:nowrap;max-width:250px;overflow:hidden;text-overflow:ellipsis" title="'+esc(a.n+'. '+a.d+(a.x?' | Calendar note: '+a.x:''))+'"><b>'+a.n+'</b> '+esc(a.t)+'<span class="cnt"> · '+ph+'</span></td><td style="border:1px solid #eef0f3;padding:1px 6px;white-space:nowrap">'+chip+'</td>'+cells+'</tr>';
 });
 box.innerHTML='<table style="width:auto;table-layout:fixed;border-collapse:collapse"><colgroup><col style="width:250px"><col style="width:96px">'+days.map(()=>'<col style="width:14px">').join('')+'</colgroup><thead><tr><th style="border:none"></th><th style="border:none"></th>'+ml+'</tr><tr><th style="border:none"></th><th style="border:none"></th>'+dayRow+'</tr><tr><th style="border:none"></th><th style="border:none"></th>'+wdRow+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>';
 const notes=(NACD.notes||[]).map(n=>'<b>'+esc(n.d)+'</b> '+esc(n.t));
 el('capDACT').innerHTML='Planned windows read from the countdown calendar <b>'+esc(NACD.src)+'</b> ('+esc(NACD.camp)+(NACD.vac?' · '+esc(NACD.vac):'')+', campaign '+esc(NACD.st)+'–'+esc(NACD.en)+'). Bars: scheduled window (blue), correction / re-do window (light blue), campaign days (green), catch-up day and LQAS/PCM (orange), post-campaign review (red). Sundays carry no activity day in the calendar; amber day cells are declared holidays'+(notes.length?' ('+notes.join('; ')+')':'')+'. Chips carry the live NEAP count for the four mapped activities — green when every district is at target, amber when some are, red when none are.';
 el('cntDACT').textContent=(NACD.a||[]).length+' activities · '+NACD.from+' to '+NACD.to+' · today '+tIso;
 const cb=el('btnDACTcsv');
 if(cb)cb.onclick=()=>{const C=decCal(); cqCSV('NID_Dec-26_calendar_vs_NEAP',['#','Activity','Phase','Start','End','Calendar note','NEAP indicator','Districts at target','Districts filed'],
  C.map(a=>[a.n,a.t,a.ph,a.s,a.e,a.x,a.k?DEC_CALN[a.k]:'',a.k?X.at100(a.k):'',a.k?X.any(a.k):'']));};
}
function renderDECChart(){
 const box=el('decChart'); if(!box)return;
 const X=decScope(); if(!X.D){box.innerHTML='';return;}
 const n=X.n||1, rows=DEC_K.filter(k=>k!=='inacc').map(k=>({k:k,l:DEC_L[k],c:X.at100(k),a:X.any(k),t:DEC_BM[k]||100}));
 const W=1080,LW=250,BW=680,RH=25,TOP=52,H=TOP+rows.length*RH+58;
 const pct=v=>Math.max(0,Math.min(1,v/n));
 let svg='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;display:block;min-width:760px" role="img" aria-label="Districts meeting each NID Dec-26 readiness column">';
 svg+='<text x="8" y="22" font-size="14" font-weight="700" fill="#0f172a">Districts meeting each column — out of '+n+'</text>';
 svg+='<text x="8" y="40" font-size="11.5" fill="#6b7280">NID Dec-26 grid as of '+esc(nepDAd(X.D.asof))+(X.dv?' · '+esc(X.scope):'')+' · amber = filed but below target, green = at target</text>';
 rows.forEach((r,i)=>{
  const y=TOP+i*RH, bw=pct(r.a)*BW, fw=pct(r.c)*BW;
  svg+='<text x="8" y="'+(y+15)+'" font-size="11.5" fill="#1f2937">'+esc(r.l)+(r.t<100?' <tspan fill="#6b7280" font-size="10">(target '+r.t+'%)</tspan>':'')+'</text>';
  svg+='<rect x="'+LW+'" y="'+y+'" width="'+BW+'" height="15" rx="2" fill="#eef2f7"/>';
  if(bw>0)svg+='<rect x="'+LW+'" y="'+y+'" width="'+bw.toFixed(1)+'" height="15" rx="2" fill="#fbbf24"/>';
  if(fw>0)svg+='<rect x="'+LW+'" y="'+y+'" width="'+fw.toFixed(1)+'" height="15" rx="2" fill="#16a34a"/>';
  svg+='<text x="'+(LW+BW+10)+'" y="'+(y+12.5)+'" font-size="11" font-weight="600" fill="#1f2937">'+r.c+' / '+n+'</text>';
 });
 const ly=TOP+rows.length*RH+22;
 svg+='<rect x="8" y="'+(ly-10)+'" width="11" height="11" fill="#eef2f7" stroke="#d1d8e0"/><text x="24" y="'+ly+'" font-size="11" fill="#374151">not filed</text>';
 svg+='<rect x="100" y="'+(ly-10)+'" width="11" height="11" fill="#fbbf24"/><text x="116" y="'+ly+'" font-size="11" fill="#374151">filed, below target</text>';
 svg+='<rect x="248" y="'+(ly-10)+'" width="11" height="11" fill="#16a34a"/><text x="264" y="'+ly+'" font-size="11" fill="#374151">at target</text>';
 svg+='</svg>';
 box.innerHTML=svg;
 if(el('cntDecChart'))el('cntDecChart').textContent=n+' districts · as of '+nepDAd(X.D.asof);
 if(el('capDecChart'))el('capDecChart').textContent='Each bar counts districts, not children, so the column reads "how many of the '+n+' districts have met this target", never a provincial rate. Only '+(X.filed.length||0)+' district'+(X.filed.length===1?' has':'s have')+' filed any column, so every bar is short — that is the state of the round on '+nepDAd(X.D.asof)+', not a failure of the chart. Inaccessible areas is left out because it is a count, not a percentage. BAR SWAT is excluded from the '+n+'-district counts.';
}
function renderDECMap(){
 const box=el('decMap'); if(!box)return;
 if(typeof KPGEO==='undefined'||!KPGEO.d||!KPGEO.d.length){
  box.innerHTML='<div class="empty">District geometry not embedded in this file.</div>';
  if(el('cntDecMap'))el('cntDecMap').textContent='';
  return;}
 const X=decScope(), by={}; X.RA.forEach(r=>{by[r.d]=r;});
 const CL={n:'#f1f5f9',r:'#fca5a5',m:'#fbbf24',g:'#86efac'};
 const tip=r=>{
  if(!r)return '';
  const out=[DNAME(r.d)];
  out.push(r.dv?decDvT(r.dv)+' division':'');
  if(X.dv&&r.dv!==X.dv)out.push('outside the selected division');
  out.push('Filed: '+r.nf+' of 12 columns');
  out.push('DPEC '+(r.dpec==null?'-':rnd(r.dpec,0)+'%')+' · AIC '+(r.aic==null?'-':rnd(r.aic,0)+'%'));
  out.push('Teams '+(r.trn==null?'-':rnd(r.trn,0)+'%')+' · MPs '+(r.mpv==null?'-':rnd(r.mpv,0)+'%'));
  out.push('Readiness '+(r.rd==null?'-':rnd(r.rd)+'%'));
  return out.filter(Boolean).join('\n');};
 const FU=KPGEO.vb[0]/540, LAB=hrvLab();
 let svg='<svg viewBox="0 0 '+KPGEO.vb[0]+' '+KPGEO.vb[1]+'" style="width:100%;display:block;aspect-ratio:'+KPGEO.vb[0]+'/'+KPGEO.vb[1]+'" role="img" aria-label="NID Dec-26 pre-campaign readiness by district">';
 svg+=KPGEO.d.map(p=>{const r=by[p.c], st=(X.dv&&r&&r.dv!==X.dv)?'n':(r?r.stg:'n');
  return '<path d="'+p.p+'" fill="'+CL[st]+'" stroke="#fff" stroke-width="1.1"><title>'+esc(tip(r))+'</title></path>';}).join('');
 svg+=LAB.filter(l=>l.ld).map(l=>'<g pointer-events="none"><line x1="'+l.cx.toFixed(1)+'" y1="'+l.cy.toFixed(1)+'" x2="'+l.x.toFixed(1)+'" y2="'+l.y.toFixed(1)+'" stroke="#334155" stroke-width="'+(0.8*FU).toFixed(2)+'" stroke-opacity=".6"/><circle cx="'+l.cx.toFixed(1)+'" cy="'+l.cy.toFixed(1)+'" r="'+(1.5*FU).toFixed(1)+'" fill="#334155"/></g>').join('');
 svg+=LAB.map(l=>'<text x="'+l.x.toFixed(1)+'" y="'+(l.y+l.fs*0.34).toFixed(1)+'" text-anchor="middle" font-size="'+l.fs.toFixed(1)+'" font-weight="600" fill="#0f172a" stroke="#fff" stroke-width="'+(l.fs*0.3).toFixed(1)+'" stroke-linejoin="round" paint-order="stroke" pointer-events="none">'+esc(l.n)+'</text>').join('');
 svg+='</svg>';
 box.innerHTML=svg;
 const g=X.S.filter(r=>r.stg==='g').length, m=X.S.filter(r=>r.stg==='m').length, rr=X.S.filter(r=>r.stg==='r').length, nf=X.S.filter(r=>r.stg==='n').length;
 const lg=[['#86efac','ready (100%)'],['#fbbf24','partly filed'],['#fca5a5','filed, readiness 0'],['#f1f5f9','nothing filed']];
 el('decMapNote').innerHTML='<span style="display:inline-flex;gap:12px;flex-wrap:wrap;margin-right:8px">'+lg.map(b=>'<span style="display:inline-flex;align-items:center;gap:4px"><i style="width:10px;height:10px;border-radius:2px;background:'+b[0]+'"></i>'+b[1]+'</span>').join('')+'</span>';
 el('cntDecMap').textContent=X.n+' districts · as of '+nepDAd(X.D.asof);
 el('capDecMap').textContent='Shading follows each district’s own filing on the live NID Dec-26 grid: '+g+' ready, '+m+' partly filed, '+rr+' filed with readiness at zero and '+nf+' with nothing filed of the '+X.n+' districts in view. Readiness is the mean of DPEC held, must-members attended, AIC training, team training and microplan validation, so a district can file attendance and still sit at zero. Boundaries are the dashboard’s KP district shapefile; BAR SWAT is drawn as the portal sub-unit for Swat. Hover a district for its filed counts.';
 const b=el('btnDecMapimg'); if(b)b.onclick=decMapImg;
}
async function decMapImg(){
 const box=el('decMap'), svg=box&&box.querySelector('svg');
 if(!svg){toast('The map is not on screen to download');return;}
 const btn=el('btnDecMapimg'); if(btn)btn.disabled=true;
 try{
  const X=decScope();
  const vb=(svg.getAttribute('viewBox')||'').split(/[\s,]+/).map(Number);
  const c=svg.cloneNode(true); c.removeAttribute('style'); c.setAttribute('xmlns','http://www.w3.org/2000/svg');
  c.setAttribute('width',String(vb[2])); c.setAttribute('height',String(vb[3])); c.setAttribute('font-family','"Segoe UI",Arial,sans-serif');
  const url='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(c));
  const img=await new Promise((res,rej)=>{const i=new Image(); i.onload=()=>res(i); i.onerror=()=>rej(new Error('map svg would not raster')); i.src=url;});
  const S=2,W=720,TB=58,MH=Math.round((W-24)*vb[3]/vb[2]),H=TB+MH+46;
  const cv=document.createElement('canvas'); cv.width=W*S; cv.height=H*S;
  const x=cv.getContext('2d'); x.scale(S,S); x.fillStyle='#ffffff'; x.fillRect(0,0,W,H);
  x.fillStyle='#0f172a'; x.font='bold 20px "Segoe UI",Arial,sans-serif'; x.fillText('NID Dec-26 pre-campaign readiness by district',16,30);
  x.fillStyle='#475569'; x.font='12.5px "Segoe UI",Arial,sans-serif'; x.fillText('NEAP as at '+nepDAd(X.D?X.D.asof:'')+' · '+(X.dv?X.scope:'Khyber Pakhtunkhwa, all districts'),16,49);
  x.drawImage(img,12,TB,MH*vb[2]/vb[3],MH);
  const lg=[['#86efac','ready (100%)'],['#fbbf24','partly filed'],['#fca5a5','filed, readiness 0'],['#f1f5f9','nothing filed']];
  let lx=16; const ly=TB+MH+18; x.font='12.5px "Segoe UI",Arial,sans-serif';
  lg.forEach(b=>{x.fillStyle=b[0]; x.fillRect(lx,ly-10,11,11); x.fillStyle='#374151'; x.fillText(b[1],lx+15,ly); lx+=15+x.measureText(b[1]).width+16;});
  const a=document.createElement('a'); a.href=cv.toDataURL('image/png'); a.download='NEAP_Dec-26_readiness_map_'+nactIso(new Date())+'.png'; a.rel='noopener';
  document.body.appendChild(a); a.click(); a.remove(); toast('PNG downloaded');
 }catch(e){console.error(e); toast('Could not create the PNG');}
 finally{if(btn)btn.disabled=false;}
}
function renderPRA(){
 const sel=el('fPRA'); if(!sel)return;
 if(!sel.options.length){
  sel.innerHTML='<option value="nov">SNID Nov-26 · final NEAP return (round closed)</option><option value="fipv">fIPV Peshawar &amp; Khyber · pre-campaign scope</option>';
  sel.onchange=()=>{PRAC=sel.value;renderPRA();};
 }
 sel.value=PRAC;
 const nb=el('praNov'), fb=el('praFipv');
 if(nb)nb.style.display=PRAC==='nov'?'':'none';
 if(fb)fb.style.display=PRAC==='fipv'?'':'none';
 const lb=el('btnPRAlive'); if(lb)lb.onclick=()=>setTab('cpre');
 if(PRAC==='nov'){
  renderNEP(); renderMPQ();
  if(el('fPRAnote'))el('fPRAnote').textContent='SNID Nov-26 · final return as of '+(NEAP&&NEAP.asof?nepDAd(NEAP.asof):'–')+' · stored, not refreshed';
 }else{
  renderPRAFipv();
  if(el('fPRAnote'))el('fPRAnote').textContent='fIPV · Peshawar & Khyber · start '+(typeof FIPV!=='undefined'&&FIPV?nepDAd(FIPV.st):'26-Oct-2026')+' · stored';
 }
}
function renderPRAFipv(){
 const F=(typeof FIPV!=='undefined'&&FIPV)?FIPV:null;
 if(!F||!F.d||!el('tPRAF'))return;
 const R=F.d.map(a=>({d:a[0],uc:a[1],nv:a[2],sv:a[3],hh:a[4],tg:a[5],sch:a[6]}));
 drawTable('tPRAF',[
  {k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},
  {k:'uc',l:'UCs',n:1,f:x=>fmt(x.uc)},
  {k:'nv',l:'New to fIPV',n:1,tt:'UCs newly added to the fIPV scope — not new to SNID',f:x=>fmt(x.nv)},
  {k:'sv',l:'Already in fIPV',n:1,f:x=>fmt(x.sv)},
  {k:'hh',l:'Households <5',n:1,f:x=>fmt(x.hh)},
  {k:'tg',l:'fIPV target',n:1,f:x=>fmt(x.tg)},
  {k:'sch',l:'School target',n:1,f:x=>fmt(x.sch)}],R,'tg',-1,null,
  {cell:{d:esc('Total — '+R.length+' districts'),uc:fmt(F.tot.uc),nv:fmt(F.tot.new),sv:fmt(F.tot.exist),hh:fmt(F.tot.hh),tg:fmt(F.tot.fipv),sch:fmt(F.tot.sch)}});
 el('cntPRAF').textContent=R.length+' districts · '+fmt(F.tot.uc)+' UCs · '+fmt(F.tot.fipv)+' fIPV target';
 el('prafHint').innerHTML='<b>fIPV</b> is a separate distribution plan, not a change to SNID coverage: <b>'+fmt(F.tot.uc)+' UCs</b> across Peshawar ('+R.filter(r=>r.d==='PESHAWAR').map(r=>r.uc)[0]+') and Khyber ('+R.filter(r=>r.d==='KHYBER').map(r=>r.uc)[0]+'), of which <b>'+fmt(F.tot.new)+' are new to the fIPV scope</b>. It targets <b>'+fmt(F.tot.fipv)+' children</b> aged '+esc(F.age)+', '+fmt(F.tot.hh)+' households with a child under 5 and a school target of '+fmt(F.tot.sch)+', and started '+esc(nepDAd(F.st))+'.';
 el('capPRAF').textContent='Stored fIPV pre-campaign scope from '+F.src+' and the scope slide. The bold bottom line adds the district rows. All 78 UCs already sit inside the SNID Nov-26 full-district scope, so fIPV is an additional activity; New means newly added to the fIPV scope, not new to SNID.';
 const ob=el('btnPRAFopen'); if(ob)ob.onclick=()=>setTab('fipv');
 const cb=el('btnPRAFcsv');
 if(cb)cb.onclick=()=>cqCSV('fIPV_Peshawar_Khyber_precampaign',['District','UCs','New to fIPV scope','Already in fIPV scope','Households <5','fIPV target','School target'],
  R.map(x=>[x.d,x.uc,x.nv,x.sv,x.hh,x.tg,x.sch]));
}
function decSitrep(){
 const S=decScope(), D=S.D;
 const CAL=decCal(), PRE=CAL.filter(a=>a.ph==='pre');
 const DVS=[...new Set(S.R.map(r=>r.dv).filter(Boolean))].sort();
 const DV=DVS.map(v=>{const g=S.S.filter(r=>r.dv===v);
  return {v:v,l:decDvT(v),n:g.length,filed:g.filter(r=>r.nf>0).length,dp:g.filter(r=>r.dpec>=100).length,rd:decAvg(g.map(r=>r.rd))};});
 const now=new Date();
 return {camp:(D&&D.camp)||'NID Dec-26',src:D?D.src:'',srcu:D?D.srcu:'',asof:D?nepDAd(D.asof):'',
  uasof:(D&&D.u)?nepDAd(D.u.asof):'',uN:S.uN,uF:S.uF,uD:S.uD,
  n:S.n,nAll:S.nAll,scope:S.scope,dv:S.dv,rd:S.rd,rdAll:S.rdAll,
  S:S.S,R:S.R,mx:S.mx,at100:S.at100,any:S.any,filed:S.filed,nothing:S.nothing,DV:DV,
  t1:S.nothing,t2:S.S.filter(r=>r.nf&&!(r.aic>0)),t3:S.S.filter(r=>r.aic>0&&r.aic<90),
  held:S.S.filter(r=>r.dpec>=100),
  cal:PRE,calSrc:(typeof NACD!=='undefined'&&NACD)?NACD.src:'',calN:CAL.length,
  calSt:(typeof NACD!=='undefined'&&NACD)?NACD.st:'',calEn:(typeof NACD!=='undefined'&&NACD)?NACD.en:'',
  calFrom:(typeof NACD!=='undefined'&&NACD)?NACD.from:'',
  calAsof:(typeof NACD!=='undefined'&&NACD)?nepDAd(NACD.asof):'',
  dTo:S.dTo,startTxt:D&&D.start?nepDAd(D.start):'12-Dec-2026',
  date:now.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}),tIso:nactIso(now)};
}
function renderDSITREPDeck(P,X){
 const pptx=new P(); pptx.layout='LAYOUT_WIDE';
 pptx.title='Pre-campaign SITREP: '+X.scope+' · '+X.camp; pptx.company='KP Polio Programme';
 const IND='4338CA',TEAL='0F766E',GRN='15803D',BLU='1D4ED8',AMB='B45309',RED='DC2626',GRY='6B7280',TXT='1F2937',F='Segoe UI';
 const pct=v=>v==null?'–':(Math.round(v*10)/10).toFixed(1)+'%';
 const num=v=>v==null?'–':String(Math.round(v));
 const cut=(t,n)=>{t=t==null?'':String(t);return t.length>n?t.slice(0,n-1)+'…':t;};
 let pg=0;
 const foot=()=>'Pre-campaign SITREP · '+X.scope+' · '+X.camp+' · '+X.date+' · NEAP as at '+X.asof;
 const base=(title,col,sub)=>{const s=pptx.addSlide(); pg++; s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.12,fill:{color:col},line:{color:col}});
  s.addText(title,{x:0.5,y:0.28,w:12.3,h:0.6,fontFace:F,fontSize:23,bold:true,color:col});
  if(sub)s.addText(sub,{x:0.5,y:0.86,w:12.3,h:0.36,fontFace:F,fontSize:11,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText(foot(),{x:0.5,y:7.02,w:10.5,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'});
  return s;};
 const kpis=(s,items,y)=>{const n=items.length,gp=0.2,w=(12.33-gp*(n-1))/n;
  items.forEach((it,i)=>{const x=0.5+i*(w+gp);
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:1.3,fill:{color:'F9FAFB'},line:{color:'E5E7EB',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:0.07,fill:{color:it.c||IND},line:{color:it.c||IND}});
   s.addText(String(it.l).toUpperCase(),{x:x+0.13,y:y+0.14,w:w-0.26,h:0.3,fontFace:F,fontSize:8.5,bold:true,color:GRY});
   s.addText(String(it.v),{x:x+0.13,y:y+0.42,w:w-0.26,h:0.5,fontFace:F,fontSize:20,bold:true,color:it.vc||TXT});
   if(it.s)s.addText(String(it.s),{x:x+0.13,y:y+0.92,w:w-0.26,h:0.32,fontFace:F,fontSize:8.5,color:GRY});});};
 const tbl=(s,head,rows,o)=>{ if(!rows.length)return;
  const fs=o.fs||8;
  const hdr=head.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.col||IND},fontSize:fs,align:j?'center':'left',valign:'middle'}}));
  const body=rows.map((r,i)=>r.map((c,j)=>{const cc=(c&&typeof c==='object'&&('t' in c))?c:{t:c};
   return {text:String(cc.t==null||cc.t===''?'–':cc.t),options:{fontSize:fs,bold:!!cc.b,color:cc.col||TXT,fill:{color:i%2?'FFFFFF':'F9FAFB'},align:j?'center':'left',valign:'middle'}};}));
  s.addTable([hdr,...body],{x:o.x,y:o.y,w:o.w,colW:o.colW,fontFace:F,rowH:[0.3,...rows.map(()=>o.rh||0.24)],border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false,margin:0.03});};
 const bullets=(s,items,o)=>s.addText(items.map(t=>({text:t,options:{bullet:{indent:16},breakLine:true}})),{x:o.x,y:o.y,w:o.w,h:o.h,fontFace:F,fontSize:o.fs||12,color:TXT,valign:'top',paraSpaceAfter:6});
 const h3=(s,t,y,c)=>s.addText(t,{x:0.5,y:y,w:12.33,h:0.3,fontFace:F,fontSize:12,bold:true,color:c||TXT});
 const cellOf=(v,k)=>v==null?{t:'–',col:GRY}:(v>=(DEC_BM[k]||100)?{t:num(v),col:GRN}:v>0?{t:num(v),col:AMB}:{t:'0',col:RED});

 // 1 Cover
 {const s=pptx.addSlide(); pg++; s.background={color:IND};
  s.addText('PRE-CAMPAIGN DAILY SITREP',{x:0.8,y:1.05,w:11.7,h:0.5,fontFace:F,fontSize:16,bold:true,color:'FFFFFF',charSpacing:3});
  s.addText(X.camp+' — '+X.scope,{x:0.8,y:1.5,w:11.7,h:1.0,fontFace:F,fontSize:(X.camp+X.scope).length>40?26:30,bold:true,color:'FFFFFF'});
  s.addText('Report date '+X.date+(X.dTo!=null&&X.dTo>0?' · D-'+X.dTo:'')+(X.dTo===0?' · round starts today':''),{x:0.8,y:2.5,w:11.7,h:0.5,fontFace:F,fontSize:18,color:'C7D2FE'});
  s.addText([{text:'NEAP district status as at '+X.asof+' ('+X.src+')',options:{breakLine:true}},
   {text:X.n+' of '+X.nAll+' districts in scope ('+(X.dv?X.scope:'all divisions')+') · '+num(X.uF)+' of '+num(X.uN)+' union councils have filed anything',options:{breakLine:true}},
   {text:'Countdown calendar '+X.calFrom+' to '+X.calEn+' · campaign '+X.calSt+'–'+X.calEn+' · '+X.calN+' activities',options:{breakLine:true}},
   {text:'Readiness = mean of DPEC held, must-members attended, AICs trained, teams trained and microplans validated — it measures what districts have filed, not children reached',options:{breakLine:true}},
   {text:'Nothing on these slides is a coverage percentage, and no child name appears: district and UC names are as reported to the NEAP portal',options:{breakLine:true}}],
   {x:0.8,y:3.2,w:11.7,h:2.6,fontFace:F,fontSize:13,color:'E0E7FF',valign:'top',paraSpaceAfter:7});
  s.addText('KP Polio Programme · prepared for the core team · '+X.date,{x:0.8,y:6.4,w:11.7,h:0.4,fontFace:F,fontSize:12,color:'C7D2FE'});}

 // 2 Executive summary
 {const s=base('Executive summary — preparation at a glance',IND,'Live NID Dec-26 grid as at '+X.asof+' · '+X.n+' districts in scope');
  const full=v=>v===X.n?GRN:(v>0?AMB:RED);
  kpis(s,[
   {l:'Days to campaign',v:(X.dTo==null?'–':(X.dTo>0?('D-'+X.dTo):'Open')),c:X.dTo!=null&&X.dTo<=7?RED:IND,s:X.startTxt+' start'},
   {l:'Districts filed',v:X.filed.length+'/'+X.n,c:full(X.filed.length),s:X.nothing.length+' nothing filed'},
   {l:'DPEC held',v:X.at100('dpec')+'/'+X.n,c:full(X.at100('dpec')),s:'mean '+pct(X.mx('dpec'))},
   {l:'AIC training started',v:X.any('aic')+'/'+X.n,c:full(X.any('aic')),s:'mean '+pct(X.mx('aic'))},
   {l:'Teams trained',v:X.any('trn')+'/'+X.n,c:full(X.any('trn')),s:'mean '+pct(X.mx('trn'))},
   {l:'Microplans validated',v:X.any('mpv')+'/'+X.n,c:full(X.any('mpv')),s:'mean '+pct(X.mx('mpv'))}],1.4);
  h3(s,'What the core team needs to know',2.86,IND);
  const mm=[];
  mm.push('D-'+(X.dTo==null?'?':X.dTo)+' to the '+X.startTxt+' start: '+X.filed.length+' of '+X.n+' districts have filed a pre-campaign column and '+X.at100('dpec')+' report a DPEC held on time.');
  mm.push('Mean readiness is '+pct(X.rd)+' in view against '+pct(X.rdAll)+' for all '+X.nAll+' districts; AIC training '+pct(X.mx('aic'))+', team training '+pct(X.mx('trn'))+', microplan validation '+pct(X.mx('mpv'))+'.');
  if(X.held.length)mm.push(X.held.map(r=>DNAME(r.d)).join(' and ')+' report the DPEC held ahead of the calendar window (25–26 Nov) — filed early, not late.');
  mm.push(X.nothing.length?(X.nothing.length+' districts have filed nothing at all; the push list is every district except '+X.filed.map(r=>DNAME(r.d)).join(' and ')+'.'):'Every district has filed at least one column.');
  const nxt=X.cal.filter(a=>a.stt!=='closed'&&(a.k||a.n<=8)).slice(0,3);
  if(nxt.length)mm.push('Next on the calendar: '+nxt.map(a=>cut(a.t,44)+' ('+nactDm(a.s)+(a.s===a.e?'':'–'+nactDm(a.e))+')').join('; ')+'.');
  bullets(s,mm.slice(0,6),{x:0.5,y:3.24,w:12.3,h:3.6,fs:11});}

 // 3 Division-wise
 {const s=base('Division-wise filing — where the grid has moved',IND,X.nAll+' districts · BAR SWAT excluded · as at '+X.asof);
  const rows=X.DV.map(d=>[d.l,d.n,d.filed,{t:d.dp,col:d.dp?GRN:RED},{t:d.rd==null?'–':(Math.round(d.rd*10)/10).toFixed(1)+'%',col:d.rd>=80?GRN:d.rd>0?AMB:RED}]);
  rows.push([{t:'KP total',b:true},X.n,X.filed.length,{t:X.at100('dpec'),col:X.at100('dpec')?GRN:RED,b:true},{t:pct(X.rd),b:true}]);
  tbl(s,['Division','Districts','Filed anything','DPEC held','Mean readiness'],rows,{x:0.5,y:1.35,w:12.33,colW:[2.6,1.6,2.0,2.0,2.0],fs:10,rh:0.34,col:IND});
  h3(s,'Reading the table',4.55,IND);
  bullets(s,[
   'Filed anything counts a district with at least one non-zero readiness column; DPEC held counts a cell of 100 on the DPEC column.',
   'Mean readiness is the mean of the district readiness values in the division — a zero-filed district pulls it down rather than being skipped, because a filed zero and a blank both mean not ready.',
   'The bold line adds districts and recomputes the DPEC count and mean across all '+X.nAll+' districts; it is not a sum of the division percentages.'],{x:0.5,y:4.9,w:12.3,h:1.9,fs:10.5});}

 // 4-5 district grids
 {const S=X.S.slice().sort((a,b)=>(b.nf-a.nf)||((b.rd||0)-(a.rd||0))||a.d.localeCompare(b.d));
  const head=['District','Division','DPEC','DC','DHO','Must','AIC','Teams','MPs','Female','Local','Inacc'];
  const cols=['dpec','dc','dho','must','aic','trn','mpv','fem','loc','inacc'];
  const part=(arr,k)=>arr.map(r=>[{t:DNAME(r.d),b:true},decDvT(r.dv)].concat(cols.map(k2=>cellOf(r[k2],k2))));
  const CW=[1.8,1.2,0.8,0.8,0.8,0.95,0.8,0.95,0.95,0.95,0.95,0.9];
  [[0,18,'Section 1 — district readiness grid (I of II)'],[18,36,'Section 2 — district readiness grid (II of II)']].forEach(pp=>{
   const rows=part(S.slice(pp[0],pp[1]));
   if(!rows.length)return;
   const s=base(pp[2],TEAL,'Values are percentages as filed; green = at target, amber = under way, red = filed zero, grey = blank');
   tbl(s,head,rows,{x:0.5,y:1.3,w:12.0,colW:CW,fs:7,rh:0.24,col:TEAL});
   s.addText('Grid as at '+X.asof+' · '+S.length+' districts, ordered by columns filed then readiness. DPEC / DC / DHO / Must read a 100 cell as held; AIC / Teams / MPs are completion percentages.',{x:0.5,y:6.62,w:12.3,h:0.3,fontFace:F,fontSize:8,color:GRY});
  });}

 // 6 Countdown
 {const s=base('The countdown calendar against what districts have filed',BLU,'NID Dec-26 countdown · '+X.calFrom+' to '+X.calEn+' · chips are the live NEAP count out of '+X.n);
  const rows=X.cal.map(a=>[a.n,cut(a.t,62),nactDm(a.s)+(a.s===a.e?'':'–'+nactDm(a.e)),
   {t:(a.stt==='closed'?'closed':a.stt==='running'?'in window':'ahead'),col:a.stt==='closed'?GRY:(a.stt==='running'?AMB:BLU)},
   a.k?{t:DEC_CALN[a.k]+' '+X.at100(a.k)+'/'+X.n,col:X.at100(a.k)===X.n?GRN:(X.at100(a.k)>0?AMB:RED)}:{t:'–',col:GRY}]);
  tbl(s,['#','Activity','Calendar window','Where it stands','NEAP count'],rows,{x:0.5,y:1.28,w:12.33,colW:[0.5,6.6,2.0,1.6,1.63],fs:7,rh:0.245,col:BLU});
  s.addText('Only four calendar activities carry a NEAP reading: DPEC (4), AIC & UCMO training (6), microplan desk review + validation (7) and FLW training (14). The rest are filed in IDIMS or reported up the chain, not on the NEAP grid.',{x:0.5,y:6.52,w:12.3,h:0.4,fontFace:F,fontSize:8,color:GRY});}

 // 7 Push list
 {const s=base('Push list and what the countdown asks next',RED,X.nothing.length+' districts have filed nothing · '+X.t2.length+' filed but have not started AIC training');
  h3(s,'Tier 1 — nothing filed',1.3,RED);
  s.addText(X.t1.length?(X.t1.length+' districts have no pre-campaign column: every district except '+X.filed.map(r=>DNAME(r.d)).join(' and ')+'.'):'None.',{x:0.5,y:1.6,w:12.3,h:0.35,fontFace:F,fontSize:9.5,color:TXT});
  h3(s,'Tier 2 — filed, AIC training not started',2.0,AMB);
  s.addText(X.t2.length?(X.t2.map(r=>DNAME(r.d)).join(', ')+' — start AIC and UCMO training in the 26–28 Nov window.'):'None.',{x:0.5,y:2.3,w:12.3,h:0.35,fontFace:F,fontSize:9.5,color:TXT});
  h3(s,'Tier 3 — AIC training started but under 90%',2.7,BLU);
  s.addText(X.t3.length?(X.t3.map(r=>DNAME(r.d)+' '+num(r.aic)+'%').join(', ')+' — close out before FLW training opens on 4-Dec.'):'None.',{x:0.5,y:3.0,w:12.3,h:0.35,fontFace:F,fontSize:9.5,color:TXT});
  h3(s,'Decisions asked of the core team',3.45,IND);
  bullets(s,[
   'Confirm the DPEC push in the 25–26 Nov window and ask every district to file the mandatory agenda, with the DC and DHO present.',
   'Direct the '+X.t2.length+' district'+(X.t2.length===1?'':'s')+' that filed attendance to start AIC and UCMO training in the 26–28 Nov window.',
   'Protect the 30-Nov–1-Dec microplan desk review and field validation, then the 2-Dec UPEC, so IDIMS entry and real-time MPQA open on time.',
   'Agree who signs off the 9–10 Dec divisional readiness meeting, and hold the 12–18 Dec campaign start against that sign-off.'],{x:0.5,y:3.8,w:12.3,h:2.8,fs:10.5});}

 // 8 Provenance
 {const s=base('Provenance and definitions',GRY,'What this deck reads, and what it does not say');
  bullets(s,[
   'Pre-campaign grid: '+X.src+' (district-wise) and '+(X.srcu||'')+' (UC-wise), downloaded '+X.asof+' from the EOC pre-campaign NEAP page. UC-wise sheet as at '+(X.uasof||X.asof)+'.',
   'Countdown calendar: '+X.calSrc+', read '+X.calAsof+'. '+X.calN+' activities across the pre-campaign, campaign and post-campaign window.',
   'Readiness is the mean of DPEC held, must-members attended, AIC training, team training and microplan validation. It is a filing measure, not a coverage or quality measure.',
   'Zeros are portal zeros: a district that has not filed reads 0, not blank. A dash means the cell was blank in the export. No readiness mean is claimed for children reached.',
   'BAR SWAT is the portal reporting sub-unit for Swat, shown on the map as its own shape and kept out of the district counts.',
   'No child-level record appears in this deck: names are district and division names only, and UC-wise data stays on the dashboard.'],{x:0.5,y:1.4,w:12.3,h:5.2,fs:11});}
 return pptx;
}
async function runDSITREP(btn,st){
 const X=decSitrep();
 if(!X||!X.n){if(st)st.textContent='No NEAP pre-campaign data in this build.';toast('Pre-campaign data missing');return;}
 if(btn)btn.disabled=true; if(st)st.textContent='Preparing the NID Dec-26 pre-campaign SITREP…';
 try{await loadPptx(); const pptx=renderDSITREPDeck(window.PptxGenJS,X);
  const fn=('PreCampaign_SITREP_'+(X.dv?decDvT(X.dv):'KP')+'_NID_Dec-26_'+X.tIso).replace(/[^A-Za-z0-9]+/g,'_')+'.pptx';
  await saveDeck(pptx,fn); if(st)st.textContent='Downloaded '+fn+' · NEAP as at '+X.asof; toast('NID Dec-26 pre-campaign SITREP ready');}
 catch(e){console.error(e);
  if(st)st.textContent=(e&&e.message==='load')?'Could not load the presentation tool. Check your internet connection and try again.':'Could not create the SITREP: '+((e&&e.message)||e);
  toast('NID Dec-26 SITREP failed');}
 finally{if(btn)btn.disabled=false;}
}

// ---------- Pre-campaign ----------''')

rep('// ---------- Pre-campaign ----------', JS)

# ---------------------------------------------------------------- 15. guards + write
assert s.count('\r\n') == s.count('\n') > 0, 'CRLF guard after patch'
assert '\n' not in s.replace('\r\n', ''), 'bare LF after patch'
assert s.count('id="p-pcra"') == 1 and s.count('data-tab="pcra"') == 1
assert s.count('function renderDEC(') == 1 and s.count('function renderPRA(') == 1
assert s.count('id="cardNEPB"') == 1, 'Nov briefing still single'
assert s.count('id="cardBDEC"') == 1, 'Dec briefing present'
assert s.count('id="decChart"') == 1 and s.count('id="decMap"') == 1

open(P, 'w', encoding='utf-8', newline='').write(s)
print('patched', ORIG, '->', len(s), 'chars')
print('crlf', s.count('\r\n'), 'lf', s.count('\n'))
