# -*- coding: utf-8 -*-
"""Lands the control-room trigger reminders and the pre-campaign pendency popover.

Five atomic edits to the index.html master:
  1. `const TRIG = {...};`      - payload from _refresh/out/trig.json
  2. trigger / pendency CSS     - after the SNID popup styles
  3. home reminder strip        - three trigger chips above the immunity-gap section
  4. `#pendPop` dialog markup   - the EOC-style district list, before the SNID popup
  5. renderer + popover JS      - pendTrig / pendNEAP / pendRender, plus a Pendency
                                  button on the SNID Nov-26 NEAP card

Master only: preview / public / internal pick the block up through push_master.py,
which is a publish and needs the owner's go-ahead.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, 'out', 'trig.json')
MASTER = 'index.html'

A_CONST = 'const NEAP = '
A_CSS = '.snpopft{display:flex;flex-wrap:wrap;gap:8px;margin-top:13px}'
A_HOME = '<div class="hsec"><h2>Immunity gap: three questions for leadership</h2>'
A_POP = '<!-- ============ SNID launch popup: countdown + schematic scope map ============ -->'
A_FUNC = 'function renderNEP(){'
A_CALL = ('renderHomeAFP(); renderHomeRisk(); renderHomeWatch(); renderHomeCrit(); '
          'renderHomeMis(); renderHomeAct();')
CALLNEW = A_CALL + ' renderTRIG();'
A_NEPBTN = '<span class="cnt" id="cntNEP"></span><span style="flex:1"></span>'

CSS = """.trigrow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:6px}
.trigbtn{all:unset;box-sizing:border-box;cursor:pointer;position:relative;display:block;padding:11px 15px;border-radius:12px;background:#fff;border:1px solid var(--color-border-light);border-left:5px solid var(--tc);box-shadow:0 1px 4px rgba(0,0,0,.04)}
.trigbtn:hover,.trigbtn:focus-visible{box-shadow:0 6px 16px rgba(0,0,0,.10)}
.trigbtn b{display:block;font:800 26px/1.05 var(--font-mono);color:var(--tc);font-variant-numeric:tabular-nums}
.trigbtn .tl2{display:block;font:600 12.5px/1.3 var(--font-sans);color:var(--color-text);margin-top:2px;padding-right:74px}
.trigbtn .ts2{display:block;font:11.5px/1.4 var(--font-sans);color:var(--color-text-muted);margin-top:3px}
.trigbtn .tgo{position:absolute;top:11px;right:12px;font:600 11px var(--font-sans);color:var(--tc)}
.pndbox{max-width:940px}
.pndtabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
.pndtab{all:unset;cursor:pointer;font:600 12px var(--font-sans);padding:5px 11px;border-radius:20px;border:1px solid var(--color-border);background:var(--color-bg-secondary);color:var(--color-text-muted)}
.pndtab:hover,.pndtab:focus-visible{color:var(--color-text)}
.pndtab.on{background:#0f172a;color:#fff;border-color:#0f172a}
@media(max-width:900px){.trigrow{grid-template-columns:1fr}}"""

HOME = """<div class="hsec"><h2>Control-room triggers — district-wise reminders</h2><span>Click a trigger for the district table · MPQA is the SNID Nov-26 round, ICM and admin coverage are the last round with intra-campaign data (SNID Sept-26) · portal read <b id="trigAsof">–</b></span></div>
<div class="trigrow" id="trigRow"></div>"""

POP = """<div class="snpop" id="pendPop" role="dialog" aria-modal="true" aria-labelledby="pendPopTitle">
 <div class="snpopbox pndbox">
  <div class="snpophd">
   <div style="min-width:0"><h3 id="pendPopTitle">Pendency — district-wise</h3><div class="snpopsub" id="pendPopSub"></div></div>
   <button class="snpopx" id="pendPopX" type="button" title="Close" aria-label="Close">&times;</button>
  </div>
  <div class="pndtabs" id="pendTabs" role="tablist"></div>
  <div class="scroll" style="max-height:52vh"><table id="pendTbl"></table></div>
  <div class="cap" id="pendCap"></div>
  <div class="snpopft">
   <button class="btn" id="pendCsv" type="button">Download (CSV)</button>
   <button class="btn" id="pendGo" type="button">Open the Pre-campaign tab</button>
   <button class="btn" id="pendPopX2" type="button">Close</button>
  </div>
 </div>
</div>"""

JS = """// ---------- pendency: EOC control-room triggers + NEAP readiness, district-wise ----------
// The EOC control room runs seven triggers; three are carried here as reminders. Every figure is a
// UC count for the campaign named on the row, read from the portal on TRIG.asof.
const PENDTABS=[['mpqa','MPQA trigger'],['icm','ICM trigger'],['admin','Admin coverage'],['neap','NEAP readiness']];
const PENDTG={dpec:100,dc:100,dho:100,must:100,ucmo:100,ucsec:100,aic:100,trn:100,mpv:100,adult:100,loc:80,gov:80,fem:80};
const PENDLBL={dpec:'DPEC',dc:'DC attendance',dho:'DHO attendance',must:'Must-members',ucmo:'UCMO',ucsec:'UC secretary',aic:'AICs trained',trn:'Teams trained',mpv:'Microplans validated',adult:'Members 18+',loc:'Local member',gov:'Govt-accountable',fem:'Female member'};
const PENDMN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
let PENDK='mpqa';
const pendDay=s=>{const m=/^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(s||'');return m?m[3]+'-'+PENDMN[+m[2]-1]+'-'+m[1]:String(s||'');};
const pendZero=(v,bad)=>v?'<span class="rg '+(bad?'r':'a')+'">'+fmt(v)+'</span>':'<span class="rg g">0</span>';

function pendTrig(t){
 if(!t)return null;
 const T=t.tot,pend=T[2]-T[3],rows=[];
 Object.keys(t.d).forEach(d=>{const v=t.d[d];rows.push({d:d,a:v[0],b:v[1],t:v[2],f:v[3],p:v[2]-v[3]});});
 const nD=rows.filter(r=>r.t>0).length,ad=pendDay(TRIG.asof);
 const sub='<b>'+fmt(T[2])+'</b> UCs met the trigger: '+esc(t.cols[0])+' <b>'+fmt(T[0])+'</b>, '+esc(t.cols[1])+' <b>'+fmt(T[1])+'</b> · <b>'+fmt(T[3])+'</b> '+(T[3]?'with trigger feedback':'trigger feedback logged')+' · <b>'+fmt(pend)+'</b> pending · '+esc(t.camp)+', portal read '+ad;
 const cap=nD+' of '+rows.length+' districts have at least one flagged UC. Trigger rule: '+t.rule+'. Counts are UCs, not children, and every figure is the '+t.camp+' round as read from the EOC control-room triggers on '+ad+'.'+(t.id==='mpqa'?' The two flag columns are the same counts as the MPQA card on the Pre-campaign tab.':'');
 return {title:t.l+' — pendency by district',sub:sub,cap:cap,
  cols:[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},
   {k:'a',l:esc(t.cols[0]),n:1,tt:t.rule},
   {k:'b',l:esc(t.cols[1]),n:1,tt:t.rule},
   {k:'t',l:'Flagged UCs',n:1,tt:'Union councils that met either flag'},
   {k:'f',l:'Feedback',n:1,tt:'Trigger feedback entered in the portal for those UCs'},
   {k:'p',l:'Pending',n:1,tt:'Flagged UCs with no trigger feedback yet',f:x=>pendZero(x.p,true)}],
  rows:rows,
  csv:['EOC '+t.l+' pendency '+t.camp,['District',t.cols[0],t.cols[1],'Flagged UCs','Feedback','Pending feedback'],
   rows.map(r=>[r.d,r.a,r.b,r.t,r.f,r.p]).concat([['KP total',T[0],T[1],T[2],T[3],pend]])]};
}

function pendNEAP(){
 const R=nepRows(),MQ=(TRIG.t||[]).filter(x=>x.id==='mpqa')[0],ad=pendDay(NEAP.asof);
 let G=0,UN=0,PN=0;
 const rows=R.map(r=>{
  const g=NEPK.filter(k=>PENDTG[k]!=null&&r[k]!=null&&r[k]<PENDTG[k]);
  const m=(MPQA.d&&MPQA.d[r.d])||[0,0,0,0,0];
  const tr=(MQ&&MQ.d[r.d])||[0,0,0,0];
  const o={d:r.d,rd:r.rd,g:g.length,tx:g.map(k=>PENDLBL[k]+' '+rnd(r[k])+'%').join(' · '),unf:m[0]-m[1],pend:tr[2]-tr[3]};
  G+=o.g;UN+=o.unf;PN+=o.pend;return o;});
 const nD=rows.filter(r=>r.g>0).length;
 const sub='<b>'+fmt(G)+'</b> readiness gaps across <b>'+nD+' of '+rows.length+' districts</b> · <b>'+fmt(UN)+'</b> MPQA reports not filed · <b>'+fmt(PN)+'</b> MPQA trigger feedbacks pending · NEAP of '+esc(NEAP.camp)+' read '+ad;
 const cap='A readiness gap is a district indicator below its NEAP target: DPEC held on time, DC and DHO attendance, must-members, UCMO and UC secretary present, AICs and teams trained, microplans field-validated and members 18+ at 100%; local, govt-accountable and female team members at 80%. Inaccessible areas are left out (better at zero). MPQA not filed = UCs assigned for review minus UCs reported; MPQA feedback pending = Nov-26 UCs that met the MPQA trigger with no feedback in the portal. NEAP read '+ad+'.';
 return {title:'Pre-campaign pendency — readiness and MPQA by district',sub:sub,cap:cap,
  cols:[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},
   {k:'rd',l:'Readiness',n:1,tt:'Mean of DPEC, must-members, AICs trained, teams trained and microplans validated',f:x=>x.rd==null?'–':rnd(x.rd)+'%'},
   {k:'g',l:'Readiness gaps',n:1,tt:'Indicators below the NEAP target',f:x=>pendZero(x.g,false)},
   {k:'tx',l:'Indicators short of target',ns:1},
   {k:'unf',l:'MPQA not filed',n:1,tt:'UCs assigned for MPQA minus UCs reported',f:x=>pendZero(x.unf,false)},
   {k:'pend',l:'MPQA feedback pending',n:1,tt:'Nov-26 UCs that met the MPQA trigger with no feedback',f:x=>pendZero(x.pend,true)}],
  rows:rows,
  csv:['NEAP pendency '+NEAP.camp,['District','Readiness %','Readiness gaps','Indicators short of target','MPQA reports not filed','MPQA feedback pending'],
   rows.map(r=>[r.d,r.rd==null?'':rnd(r.rd),r.g,r.tx,r.unf,r.pend]).concat([['KP total','',G,'',UN,PN]])]};
}

function pendRender(){
 const p=el('pendPop');if(!p)return;
 el('pendTabs').innerHTML=PENDTABS.map(t=>'<button class="pndtab'+(t[0]===PENDK?' on':'')+'" type="button" role="tab" aria-selected="'+(t[0]===PENDK)+'" data-k="'+t[0]+'">'+t[1]+'</button>').join('');
 el('pendTabs').querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>{PENDK=b.dataset.k;pendRender();});
 const m=PENDK==='neap'?pendNEAP():pendTrig((TRIG.t||[]).filter(x=>x.id===PENDK)[0]);
 if(!m)return;
 el('pendPopTitle').textContent=m.title;
 el('pendPopSub').innerHTML=m.sub;
 drawTable('pendTbl',m.cols,m.rows,'d',1);
 el('pendCap').textContent=m.cap;
 el('pendCsv').onclick=()=>cqCSV(m.csv[0],m.csv[1],m.csv[2]);
}
function pendOpen(k){const p=el('pendPop');if(!p)return;PENDK=k||'mpqa';pendRender();p.classList.add('on');}
function pendClose(){const p=el('pendPop');if(p)p.classList.remove('on');}

function renderTRIG(){
 const row=el('trigRow'),ad=pendDay(TRIG.asof);if(!row)return;
 const a=el('trigAsof');if(a)a.textContent=ad;
 const CO={mpqa:'#be123c',icm:'#b45309',admin:'#0f766e'};
 row.innerHTML=(TRIG.t||[]).map(t=>{
  const T=t.tot,pend=T[2]-T[3],nD=Object.keys(t.d).filter(d=>t.d[d][2]>0).length;
  return '<button class="trigbtn" type="button" data-trig="'+t.id+'" style="--tc:'+(CO[t.id]||'#0f172a')+'" title="'+esc(t.rule)+' — district-wise">'+
   '<span class="tgo">District table →</span><b>'+fmt(T[2])+'</b>'+
   '<span class="tl2">'+esc(t.l)+' · flagged UCs</span>'+
   '<span class="ts2">'+esc(t.camp)+' · '+(T[3]?fmt(T[3])+' feedbacked · '+fmt(pend)+' pending':'no feedback logged · '+fmt(pend)+' pending')+' · '+nD+' districts</span></button>';
 }).join('');
 row.querySelectorAll('[data-trig]').forEach(b=>b.onclick=()=>pendOpen(b.dataset.trig));
}

{
 const p=el('pendPop');
 if(p){
  el('pendPopX').onclick=pendClose;el('pendPopX2').onclick=pendClose;
  p.onclick=ev=>{if(ev.target===p)pendClose();};
  el('pendGo').onclick=()=>{pendClose();setTab('cpre');};
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&p.classList.contains('on'))pendClose();});
 }
 const b=el('btnPendNep');if(b)b.onclick=()=>pendOpen('neap');
}
"""

_CSS = CSS.replace('\n', '\r\n')
_HOME = HOME.replace('\n', '\r\n')
_POP = POP.replace('\n', '\r\n')
_JS = JS.replace('\n', '\r\n')

PENDBTN = ('<button class="btn" id="btnPendNep" title="District-wise pendency: unmet NEAP '
           'readiness indicators, MPQA reports not filed and MPQA trigger feedback still '
           'pending">Pendency</button>')


def patch(v, js):
    t = v.text
    for a in (A_CONST, A_CSS, A_HOME, A_POP, A_FUNC, A_CALL, A_NEPBTN):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1): %r' % (t.count(a), a[:56]))
    t = t.replace(A_CONST, 'const TRIG = %s;\r\n' % js + A_CONST)
    t = t.replace(A_CSS, A_CSS + '\r\n' + _CSS)
    t = t.replace(A_HOME, _HOME + '\r\n\r\n' + A_HOME)
    t = t.replace(A_POP, _POP + '\r\n\r\n' + A_POP)
    t = t.replace(A_FUNC, _JS + '\r\n' + A_FUNC)
    t = t.replace(A_CALL, CALLNEW)
    t = t.replace(A_NEPBTN, A_NEPBTN + PENDBTN)
    v.text = t
    for needle in ('const TRIG = {', 'id="trigRow"', 'id="trigAsof"', 'id="pendPop"',
                   'id="pendTbl"', 'id="pendCsv"', 'id="btnPendNep"',
                   'function pendTrig(t){', 'function pendNEAP(){', 'function renderTRIG(){',
                   CALLNEW):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    dashpatch.assert_crlf(v)
    v.changes.append('TRIG payload + reminder strip + pendency popover (%+d chars)' % v.delta())


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_trig.py first' % PAYLOAD)
    js = srcutil.read_text(PAYLOAD).strip()
    json.loads(js)
    if '\n' in js or '\r' in js:
        raise SystemExit('trig.json must be a single line for the <script> embed')
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'const TRIG = ' in v.text:
        raise SystemExit('%s already has a TRIG const - not patching twice' % v.rel)
    patch(v, js)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK trig-pendency master only - preview / public / internal pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
