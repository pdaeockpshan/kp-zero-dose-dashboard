# -*- coding: utf-8 -*-
"""Add the campaign indicators one-plate page (const CIN + tab `cind`) to the index.html master.

The owner's workbook `Khyber Pakhtunkhwa District and UCs Wise Campaign Indicators.xlsx` puts every
campaign indicator on one plate - coverage, still-missed, same-day, ICM and E-LQAS - with a district
tab and a UC tab. Three of its four 2026 rounds are the compiled portal export the dashboard already
carries (proved in extract_cin.py), so only SNID Sept 2026 is embedded here as `const CIN`; the
earlier rounds are merged from `INDIC` at render time into the same 17 columns.

Edits, all in the master:
  1. `const CIN = {...}` before `const ICMD = ...`, filled from _refresh/out/cin.json.
  2. `#p-cind`, a pane with the campaign picker, the Districts / UC detail switch and `#cinT`.
  3. a nav button under Campaigns and a `cind` hub chip on the Campaign overview page.
  4. `cind` in TABS and in the render dispatch.
  5. the renderer module after the data-pack block (`// <<PACKJS`), self-contained so the working
     `pk*` family is untouched.

One panel per grain, one source per column per campaign: Sept-26 from the sheet, every earlier round
from the data pack, and a column a round does not report is dashes, never zero. Nothing is summed
across campaigns - a multi-campaign plate adds a Campaign column instead.

Later on 29-Oct-2026 the master gained three things this one-shot patch does not build: the
cascading Division / District selects (`cinFSync`, `CINS.div` / `CINS.dist`), the MPQA columns
(`cinMQ*`), and the owner gate on the daily-reminder button (`remOwnUI` / `remOwnAsk`,
`#btnRemindOwn`). Those edits went straight into index.html and are noted here only so replaying
this script is not mistaken for a full rebuild of the plate - it aborts when the CIN block already
exists in any case.

The MPQA join moved the same day from the single Nov-26 `MPQA` payload to `MPQAH`, the per-campaign
carry (11 portal rounds, NID FEB 2025 to SNID Nov 2026) built by `extract_mpqa_hist.py` from the
harvest in `_refresh/cache/mpqa_hist_*.json`, so each row reads its own campaign's round. That
payload is a cache rebuild, not a Downloads pickup, and this patch still does not build it.

Master only: preview / public / internal pick the block up through push_master.py, which needs the
owner's word.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

MASTER = 'index.html'
PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'cin.json')

A_CONST = 'const ICMD = {"src":"ICM Sheet (EOC Dashboard UC Wise Data).xlsx"'
A_END = '<!--/PKHC-->\r\n</section>'
A_NAV = '<button class="tab" data-tab="hcamp">'
A_TABS = "'hcamp','hrd','hrat','c3','cpre'"
A_DISP = 'hcamp:renderHCamp,'
A_CHIP = '<div class="hubchips"><button data-hl="hrd">High-risk district focus</button>'
A_JS = '// <<PACKJS'

NAV = (chr(10) + '   <button class="tab" data-tab="cind"><span class="tl">Campaign indicators</span>'
       '<span class="badge">District &amp; UC</span></button>')

PANE = """<!-- ================= CAMPAIGN INDICATORS: ONE PLATE ================= -->
<section class="pane" id="p-cind">
<div class="cqbar"><b>Campaign indicators &mdash; one plate</b><span class="cnt" id="cinHd">17 indicators &middot; district and UC grain</span></div>
<div class="hint">Every indicator of the compiled campaign sheet on one table &mdash; administrative coverage, still missed, same-day coverage, ICM and E-LQAS &mdash; for one campaign or several, at district or UC grain. <b>SNID Sept 2026</b> is read from the compiled sheet; the rounds before it are merged from the dashboard&rsquo;s own campaign data pack into the same 17 columns, so this plate and the data pack can never disagree. Counts are never summed across campaigns.</div>
<div class="card">
 <div class="tblhdr"><h3 style="margin:0">District-wise and UC-wise campaign indicators</h3>
  <div class="hmcwrap"><button type="button" class="hmcbtn" id="cinPB" aria-haspopup="true" aria-expanded="false" style="min-width:200px;max-width:270px" title="Choose one campaign or several &mdash; the table and the CSV download then carry every selected campaign"><span id="cinPBT">Campaign</span><svg width="10" height="7" viewBox="0 0 10 7" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button><div class="hmcpop" id="cinPP" hidden style="min-width:250px"></div></div>
  <button class="btn pkseg" id="cinLD">Districts</button><button class="btn pkseg" id="cinLU">UC detail</button>
  <span class="cnt" id="cinCnt"></span><span style="flex:1"></span>
  <button class="btn" id="cinDl" title="The table as CSV, exactly as shown">Download (CSV)</button><button class="btn" id="cinXl" title="The same table as a formatted Excel workbook: numbers stay numbers and percent columns keep their sign">Download (Excel)</button></div>
 <div class="scroll"><table id="cinT"></table></div>
 <div class="cap" id="cinCap"></div>
</div>
</section>
"""

JS = """// >>CINJS (campaign indicators one-plate: the compiled sheet, 17 columns x campaign x grain)
// SNID Sept 2026 comes from const CIN; every earlier round is merged here from INDIC into the same
// 17 columns by column name. One source per column per campaign -- nothing is blended, and a
// column a round does not report is dashes, not zero.
const CINCL=[CIN.camp].concat(INDIC.camps);
const CINS={one:0,msel:null,lvl:'d'};
const CINUMS={};
let CINIX=null;
const CINTT={'Administrative Target':'Children in the campaign administrative target',
 'Adm HH Coverage':'Children covered in the administrative (household) register',
 'HH %of Total MP':'Administrative coverage as a share of the total micro-plan target',
 'Adm Still NA':'Still not available at the end of the round',
 'Adm Still Refusal':'Still refusing at the end of the round',
 'Still Leftover':'Still missed minus still not available minus still refusing',
 'SM % of Target':'Same-day coverage as a share of the target',
 'ICM Recall %':'ICM 0-59 recall: verified divided by checked',
 'ICM Total Missed':'Missed children recorded by the ICM monitor',
 'ICM Team No Visit':'Children the team did not visit, as reported by ICM',
 'ICM TVBCM':'Portal column ICM TVBCM',
 'Pass':'E-LQAS lots passed',
 'Intermediate':'E-LQAS lots intermediate',
 'Fail':'E-LQAS lots failed',
 'LQAS Pass %':'Lots passed as a share of lots assessed',
 'LQAS_NT':'Portal column LQAS_NT',
 'LQAS_TVBMC':'Portal column LQAS_TVBMC'};
// The sheet heads its LQAS block Pass / Intermediate / Fail with nothing naming the instrument, so the
// three print as LQAS lots; the two portal codes lose their underscore. CIN.k keeps the sheet's own
// labels, because those are the join keys into INDIC.
const CINLB={'Pass':'LQAS Pass','Intermediate':'LQAS Intermediate','Fail':'LQAS Fail',
 'LQAS_NT':'LQAS NT','LQAS_TVBMC':'LQAS TVBMC'};
function cinLab(s){return CINLB[s]||s;}
function cinIdx(){
 if(CINIX)return CINIX;
 const cols={admin:INDIC.S.admin.k.map(x=>x[0]),icm:INDIC.S.icm.k.map(x=>x[0]),lqas:INDIC.S.lqas.k.map(x=>x[0])};
 const map={};
 CIN.k.forEach(c=>{
  if(c[0]==='Still Leftover')return;
  ['admin','icm','lqas'].forEach(s=>{const j=cols[s].indexOf(c[0]);if(j>=0&&!map[c[0]])map[c[0]]=[s,j];});
 });
 const miss=CIN.k.filter(c=>c[0]!=='Still Leftover'&&!map[c[0]]).map(c=>c[0]);
 if(miss.length)console.warn('campaign indicators: columns missing from INDIC',miss);
 CINIX={map:map,na:cols.admin.indexOf('Adm Still NA'),ref:cols.admin.indexOf('Adm Still Refusal'),
        sm:cols.admin.indexOf('Adm Still Missed')};
 return CINIX;
}
function cinMerge(A,I,L){
 const ix=cinIdx(),out=[];
 CIN.k.forEach(c=>{
  if(c[0]==='Still Leftover'){
   const ok=!!A&&A.length>ix.sm&&ix.sm>=0&&A[ix.sm]>-1&&A[ix.na]>-1&&A[ix.ref]>-1;
   out.push(ok?A[ix.sm]-A[ix.na]-A[ix.ref]:-1);return;
  }
  const m=ix.map[c[0]];
  if(!m){out.push(-1);return;}
  const v=m[0]==='admin'?A:m[0]==='icm'?I:L;
  out.push(v&&v.length>m[1]?v[m[1]]:-1);
 });
 return out;
}
function cinDDKeys(ci){
 return ci===0?Object.keys(CIN.dd):Object.keys(INDIC.S.admin.dd[String(ci-1)]||{});
}
function cinDVals(ci,di){
 if(ci===0)return CIN.dd[String(di)]||null;
 const j=String(ci-1),ad=INDIC.S.admin.dd[j]||{};
 if(!ad[String(di)])return null;
 return cinMerge(ad[String(di)],(INDIC.S.icm.dd[j]||{})[String(di)],
                 (INDIC.S.lqas.dd[j]||{})[String(di)]);
}
function cinUMaps(ci){
 if(CINUMS[ci])return CINUMS[ci];
 const j=String(ci-1),m={icm:new Map(),lqas:new Map()};
 ['icm','lqas'].forEach(s=>{(INDIC.S[s].uu[j]||[]).forEach(p=>m[s].set(p[0],p[1]));});
 CINUMS[ci]=m;return m;
}
// UC rows are the campaign's own rows, not a left join on the UC directory: the sheet groups same-named
// UCs of one district into one row while the portal keeps the tehsils apart, so each roster stands.
function cinURows(ci){
 if(ci===0)return CIN.uu;
 const j=String(ci-1),m=cinUMaps(ci);
 return (INDIC.S.admin.uu[j]||[]).map(p=>[p[0],cinMerge(p[1],m.icm.get(p[0])||null,m.lqas.get(p[0])||null)]);
}
function cinSel(){return (CINS.msel&&CINS.msel.length)?CINS.msel:[CINS.one];}
const CINUCOK=[0].concat(INDIC.ucmin.map(i=>i+1));
function cinUCSel(){const s=cinSel();return s.filter(i=>CINUCOK.indexOf(i)>=0);}
function cinPSync(){
 const p=el('cinPP'),b=el('cinPBT'),sel=cinSel();
 if(!p)return;
 p.querySelectorAll('input[type=checkbox]').forEach(x=>{x.checked=sel.indexOf(+x.value)>=0;});
 if(b)b.textContent=sel.length>1?(sel.length+' campaigns'):pkCampLab(CINCL[sel[0]]||{l:''});
}
function cinPRead(){
 const p=el('cinPP');
 const arr=[...p.querySelectorAll('input[type=checkbox]')].filter(x=>x.checked).map(x=>+x.value).sort((a,z)=>a-z);
 if(arr.length===1){CINS.one=arr[0];CINS.msel=null;}else CINS.msel=arr.length?arr:null;
 cinDraw();cinPSync();
}
function cinPBuild(){
 const p=el('cinPP'),b=el('cinPB');
 if(!p||!b||p.dataset.built)return;
 p.innerHTML='<div class="hmcacts"><button type="button" data-a="all">All '+CINCL.length+'</button><button type="button" data-a="none">Clear</button></div>'
  +'<div class="hmcacts" style="border-bottom:0;margin-bottom:2px">'+[...new Set(CINCL.map(c=>c.y))].map(y=>'<button type="button" data-a="y'+y+'">'+y+'</button>').join('')+'</div>'
  +CINCL.map((c,i)=>({c:c,i:i})).map(x=>'<label class="hmcopt"><input type="checkbox" value="'+x.i+'"><span>'+esc(pkCampLab(x.c))+'</span></label>').join('');
 p.dataset.built='1';
 p.addEventListener('change',e=>{if(e.target&&e.target.type==='checkbox')cinPRead();});
 p.addEventListener('click',e=>{const bt=e.target.closest('button[data-a]');if(!bt)return;e.preventDefault();
  const a=bt.dataset.a,bx=[...p.querySelectorAll('input[type=checkbox]')];
  if(a==='all')bx.forEach(x=>x.checked=true);
  else if(a==='none')bx.forEach(x=>x.checked=false);
  else{const y=a.slice(1);bx.forEach(x=>x.checked=String(CINCL[+x.value].y)===y);}
  cinPRead();});
 b.onclick=e=>{e.stopPropagation();p.hidden=!p.hidden;b.setAttribute('aria-expanded',p.hidden?'false':'true');};
 document.addEventListener('click',e=>{if(p.hidden)return;if(p.contains(e.target)||b.contains(e.target))return;p.hidden=true;b.setAttribute('aria-expanded','false');});
}
function cinRows(){
 const sel=cinSel(),multi=sel.length>1,uc=CINS.lvl==='u',ucSel=cinUCSel(),ucOK=ucSel.length>0;
 if(uc&&!ucOK)CINS.lvl='d';
 const onD=CINS.lvl==='d',rows=[];
 if(!onD){
  (multi?ucSel:sel).forEach(ci=>{
   cinURows(ci).forEach(pr=>{const u=pkUC(pr[0]);if(!u)return;
    rows.push({cn:CINCL[ci].l,cs:ci,d:pkDN(u[1]),t:pkTEH(u[2]),u:u[0],c:u[3],v:pr[1]});});
  });
 }else{
  sel.forEach(ci=>{
   cinDDKeys(ci).forEach(di=>{const v=cinDVals(ci,+di);if(!v)return;
    rows.push({cn:CINCL[ci].l,cs:ci,d:pkDN(+di),v:v});});
  });
 }
 // A column no row in this selection reports is left out and named in the caption, rather than
 // printed as a run of dashes. The sheet itself is uneven: its district tab has no ICM Total Missed.
 const keep=CIN.k.map((c,j)=>rows.some(r=>r.v[j]!=null&&r.v[j]>-1));
 const drop=CIN.k.filter((c,j)=>!keep[j]).map(c=>cinLab(c[0]));
 const V=CIN.k.map((c,j)=>({k:'v'+j,l:cinLab(c[0]),n:1,tt:CINTT[c[0]]||'',
  sv:r=>{const v=r.v[j];return (v==null||v===-1)?null:v;},f:r=>pkVal(r.v[j],c[1])})).filter((c,j)=>keep[j]);
 const CP=multi?[{k:'cp',l:'Campaign',sv:r=>-r.cs,f:r=>esc(r.cn)}]:[];
 const cols=onD
  ?CP.concat([{k:'d',l:'District',f:r=>multi?esc(r.d):'<b>'+esc(r.d)+'</b>'}],V)
  :CP.concat([{k:'d',l:'District',f:r=>esc(r.d)},{k:'t',l:'Tehsil',f:r=>esc(r.t)},
    {k:'u',l:'UC',f:r=>esc(r.u)},{k:'c',l:'UC Code',f:r=>esc(r.c)},critCol(r=>r.d,r=>r.u,r=>r.c)],V);
 return {cols:cols,rows:rows,sel:sel,multi:multi,onD:onD,ucSel:ucSel,ucOK:ucOK,keep:keep,drop:drop};
}
function cinDraw(){
 if(typeof CIN==='undefined'||typeof INDIC==='undefined'||!INDIC||!CIN)return;
 cinPBuild();cinPSync();
 const r=cinRows(),sel=r.sel,multi=r.multi,onD=r.onD,ucSel=r.ucSel;
 pkSeg(el('cinLD'),onD,false);pkSeg(el('cinLU'),!onD,!r.ucOK);
 if(el('cinLU'))el('cinLU').title=r.ucOK?'':'UC rows are embedded for the 2025-26 campaigns only';
 drawTable('cinT',r.cols,r.rows,multi?'cp':'d',1);
 const lab=multi?(sel.length+' campaigns'):pkCampLab(CINCL[sel[0]]||{l:''});
 const nInd=CIN.k.length-r.drop.length;
 el('cinCnt').textContent=lab+' · '+r.rows.length+(onD?' district rows':' UC rows');
 el('cinHd').textContent=nInd+' indicators · district and UC grain · as of '+CIN.asof;
 let cap='<b>'+esc(lab)+'</b> · '+nInd+' indicators at '+(onD?'district':'UC')+' grain. '+
  '<b>SNID Sept 2026</b> is the compiled campaign sheet ('+esc(CIN.src)+', '+esc(CIN.asof)+
  ', '+fmt(CIN.n)+' UCs); every earlier round is merged from the dashboard campaign data pack ('+
  esc(INDIC.asof)+') into the same columns, so this table and the data pack cannot disagree. '+
  'Counts are never summed across campaigns — a multi-campaign table adds a Campaign column. '+
  '&ldquo;&ndash;&rdquo; = not reported for that campaign.';
 if(r.drop.length)cap+=' Left out because no campaign in this selection reports it: <b>'+esc(r.drop.join(', '))+'</b>.';
 if(!onD)cap+=' UC rows are embedded for '+fmt(CINUCOK.length)+' of the '+fmt(CINCL.length)+' campaigns; '+
  (ucSel.length?('the selection carries '+fmt(ucSel.length)+'.'):'none of the selected campaigns carries UC rows.');
 else cap+=' <b>SNID Sept 2026</b> covers 37 districts: the Sept coverage report does not carry the old Wazir-S district, only its Lower and Upper districts.';
 el('cinCap').innerHTML=cap;
}
function cinGrid(){
 const r=cinRows(),sel=r.sel,multi=r.multi,onD=r.onD,ucSel=r.ucSel;
 const KI=CIN.k.map((c,j)=>j).filter(j=>r.keep[j]);
 const H0=KI.map(j=>cinLab(CIN.k[j][0])),rows=[];
 const uc=!onD&&ucSel.length>0;
 if(uc){
  const H=(multi?['Campaign']:[]).concat(['District','Tehsil','UC','UC Code','UC criteria'],H0);
  (multi?ucSel:sel).forEach(ci=>{
   cinURows(ci).forEach(pr=>{const u=pkUC(pr[0]);if(!u)return;
    rows.push((multi?[CINCL[ci].l]:[]).concat([pkDN(u[1]),pkTEH(u[2]),u[0],u[3],
     critLab(pkDN(u[1]),u[0],u[3])],KI.map(j=>pkNum(pr[1][j],CIN.k[j][1]))));});
  });
  return {H:H,rows:rows,uc:true,stem:'Campaign_indicators_'+
   (multi?(ucSel.length+' campaigns'):(CINCL[sel[0]]||{l:'campaign'}).l)+'_UC'};
 }
 const H=(multi?['Campaign']:[]).concat(['District'],H0);
 sel.forEach(ci=>{
  cinDDKeys(ci).forEach(di=>{const v=cinDVals(ci,+di);if(!v)return;
   rows.push((multi?[CINCL[ci].l]:[]).concat([pkDN(+di)],KI.map(j=>pkNum(v[j],CIN.k[j][1]))));});
 });
 return {H:H,rows:rows,uc:false,stem:'Campaign_indicators_'+
  (multi?(sel.length+' campaigns'):(CINCL[sel[0]]||{l:'campaign'}).l)};
}
function cinCSV(){
 if(typeof CIN==='undefined'||typeof INDIC==='undefined'||!INDIC||!CIN)return;
 const g=cinGrid();
 cqCSV(g.stem,g.H,g.rows);
}
function cinXlsx(){
 if(typeof CIN==='undefined'||typeof INDIC==='undefined'||!INDIC||!CIN)return;
 const g=cinGrid();
 // xlSheet picks each column's number format from its header and only a trailing '%' counts, while
 // three of these labels carry the sign mid-string ('HH %of Total MP'). Build the sheet from a marked
 // header, then put the printed labels back so the workbook reads exactly like the page.
 const mk=g.H.map(h=>/%/.test(h)&&!/%$/.test(h)?h+' %':h);
 xlLib().then(X=>{
  const wb=new X.Workbook();
  wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title=g.stem;
  const ws=xlSheet(wb,{sheet:'Campaign indicators'+(g.uc?' UC detail':''),H:mk,rows:g.rows});
  ws.getRow(1).values=g.H;
  return wb.xlsx.writeBuffer();
 }).then(buf=>{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=g.stem+'.xlsx';document.body.appendChild(a);a.click();a.remove();
  toast('Excel downloaded ('+fmt(g.rows.length)+' rows)');
 }).catch(()=>{cqCSV(g.stem,g.H,g.rows);
  toast('Excel library did not load, so the same table went out as CSV');});
}
function renderCIN(){try{cinDraw();}catch(e){console.warn('campaign indicators',e);}}
try{
 cinPBuild();cinPSync();
 const ld=el('cinLD'),lu=el('cinLU'),dl=el('cinDl'),xl=el('cinXl');
 if(ld)ld.onclick=()=>{CINS.lvl='d';cinDraw();};
 if(lu)lu.onclick=()=>{if(!cinUCSel().length)return;CINS.lvl='u';cinDraw();};
 if(dl)dl.onclick=()=>cinCSV();
 if(xl)xl.onclick=()=>cinXlsx();
}catch(e){console.warn('campaign indicators init',e);}
// <<CINJS
"""


def _x(text):
    return text.replace('\n', '\r\n')


def patch(v, js, obj):
    t = v.text
    for anchor, label in ((A_CONST, 'ICMD const'), (A_END, 'end of the Campaigns hub'),
                          (A_NAV, 'hcamp nav button'), (A_TABS, 'TABS list'),
                          (A_DISP, 'render dispatch'), (A_CHIP, 'hub chips'),
                          (_x(A_JS), 'PACKJS end')):
        v.require(t.count(anchor) == 1, '%s anchor occurs %d times' % (label, t.count(anchor)))

    t = t.replace(A_CONST, 'const CIN = ' + js + ';\r\n' + A_CONST)
    t = t.replace(A_END, A_END + '\r\n' + _x(PANE))
    j = t.index(A_NAV)
    j = t.index('</button>', j) + len('</button>')
    t = t[:j] + _x(NAV) + t[j:]
    t = t.replace(A_TABS, "'hcamp','cind','hrd','hrat','c3','cpre'")
    t = t.replace(A_DISP, 'hcamp:renderHCamp,cind:renderCIN,')
    t = t.replace(A_CHIP, A_CHIP.replace('<div class="hubchips">',
                                         '<div class="hubchips"><button data-hl="cind">'
                                         'Campaign indicators (one plate)</button>'))
    t = t.replace(_x(A_JS), _x(JS) + _x(A_JS))
    v.text = t

    for needle in ('const CIN = {"src"', 'id="p-cind"', 'id="cinT"', 'id="cinPP"',
                   'id="cinXl"', 'function cinGrid(){', 'function cinXlsx(){',
                   'function renderCIN(){', 'const CINCL=[CIN.camp].concat(INDIC.camps);',
                   "'hcamp','cind','hrd'", 'cind:renderCIN,',
                   'data-hl="cind"', '// >>CINJS',
                   'function cinLab(s){return CINLB[s]||s;}', 'l:cinLab(c[0])'):
        v.require(t.count(needle) == 1, '%s occurs %d times (want 1)' % (needle, t.count(needle)))
    v.require(t.count('data-tab="cind"') == 1, 'the cind nav button is not exactly one')
    v.require(t.index('id="bHC"') < t.index('data-tab="cind"'),
              'the cind nav button must follow the Campaign overview button, not nest inside it')
    v.require(t.index('const INDIC = ') < t.index('const CIN = ') < t.index('const ICMD = '),
              'CIN must sit between INDIC and ICMD')
    v.require(t.index('id="p-hcamp"') < t.index('id="p-cind"') < t.index('id="p-c3"'),
              'the cind pane is not between the Campaigns hub and the comparison pane')
    v.require(t.index('// >>CINJS') < t.index('// <<CINJS') < t.index('// <<PACKJS'),
              'the CIN module must follow the data pack block')
    v.require(len(obj['dd']) == 37 and obj['n'] == len(obj['uu']),
              'payload shape: %d districts, %d UCs' % (len(obj['dd']), obj['n']))
    dashpatch.assert_crlf(v)
    v.changes.append('campaign indicators one-plate page (%+d chars)' % v.delta())


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_cin.py first' % PAYLOAD)
    obj = json.loads(srcutil.read_text(PAYLOAD))
    js = srcutil.dumps(obj)
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'const CIN = ' in v.text or 'id="p-cind"' in v.text:
        raise SystemExit('%s already has the campaign indicators page - not patching twice' % v.rel)
    patch(v, js, obj)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('payload CIN %d chars, %d districts, %d UC rows, %d columns'
          % (len(js), len(obj['dd']), len(obj['uu']), len(obj['k'])))
    print('OK campaign indicators master only - the other three variants are synced by '
          "push_master.py, which needs the owner's word")


if __name__ == '__main__':
    main()
