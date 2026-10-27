# -*- coding: utf-8 -*-
"""Put the HRA compilation card online: `const HRAT` + the evaluator + a `hrat` tab in Campaigns.

The owner asked, 27-Oct-2026: "i have placed a template for HRA which needs to be compiled after every
campaign, i want you to create same template online in dashboard... make import and export option so
that divisional staff can just upload data and download. There should be year/month/campaign option as
well with this template. Also make it a new button in campaign section... template must contain formulas
design them in a way that it computes automatically and dont disturb the order of template."

What this patch adds to the index.html master:

  1. `const HRAT = {...}` straight before `const HRA = {...}`, filled from _refresh/out/hrat.json, so
     the card is live the moment the master is patched; later rebuilds go through `refresh.py run
     --only hrat`. It carries the 72 columns in the template's own order, the printed rule beside each
     of the 27 indicators, the 39 formula texts and the block/tail structure.
  2. The evaluator proven by _refresh/hrat_parity.js, read out of _refresh/hrat_eval.js at patch time -
     one source of truth, so the page cannot compute a row differently from the workbook it hands back.
  3. A `hrat` tab in the Campaigns group: year / month / campaign pickers, each combination its own
     compiled sheet in this browser's localStorage; the card as a 72-column grid whose typed cells are
     the 33 inputs and whose other 39 columns compute live (27 scores, four block subtotals and
     percentages, the adaptive maximum, the percentage, the rank and the Risk label); an .xlsx/.csv
     import that finds the card's header row; a blank-template download prefilled with the UC roster the
     dashboard already holds; and a filled-sheet export that writes the 39 computed columns back as live
     Excel formulas in the same column order.

Three rules the module keeps, each already argued in build_hrat.py and proven by the parity run:

  * The exported card recomputes in Excel. The 39 computed columns go out as formulas, never as the
    numbers the browser computed, and the RANK range is rewritten over the rows actually written - the
    template's own `$BR$3:$BR$38` anchor prints #N/A from row 39 down on a 1,418-row sheet, and the
    province copy and the Mardan copy of the template disagree about it.
  * Order is the template's order: A-E, F-P, Q-AN, AO-BD, BE-BP, BQ-BT, with the five row-1 block titles
    merged as the card has them. The import trusts that order when the header row lines up, falls back
    to matching by printed header text when a division moved a column, and says which it did.
  * Nothing typed here leaves the browser. The site is public GitHub Pages, so the compiled sheet lives
    in localStorage under the campaign period and travels only as the file a division downloads. The
    card's Remarks column is not in the payload and not on this grid.

The two risk axes stay apart: HRA's own bands say BR>79% = Low Risk and BR<60% = High Risk, so a high
percentage is a safe council - the opposite direction to the dashboard's combined UC risk score. The
hint says so in words, because the number looks comparable and is not.

Applied to the index.html master only; the other three variants get it through `_refresh/push_master.py`
when the owner gives the word. `--unpatch` restores the previous file byte for byte. Every anchor is
asserted to occur exactly once, all inserted text uses CRLF, and ids stay unique.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

MASTER = 'index.html'
HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, 'out', 'hrat.json')
EVAL = os.path.join(HERE, 'hrat_eval.js')

NEW_IDS = ['p-hrat', 'bHRT', 'hratHint', 'hratRule', 'fHRC', 'fHRY', 'fHRM', 'hratNote',
           'hrtFile', 'hrtFileL', 'hrtDiv', 'hrtDist', 'hratCap', 'hrtWrap', 'tHRT',
           'hrtPager', 'hrtPageNote', 'hk1', 'hk1s', 'hk2', 'hk2s', 'hk3', 'hk3s',
           'hk4', 'hk4s', 'hk5', 'hk5s', 'hk6', 'hk6s', 'hrtLog', 'hrtUcnt',
           'btnHRTBlank', 'btnHRX', 'btnHRTSeed', 'btnHRTRow', 'btnHRTCLEAR', 'btnHRThide']

PANE = """<!-- HRA COMPILATION CARD: the template divisional staff fill in after every campaign ---------- -->
<section class="pane" id="p-hrat">
<div class="hint" id="hratHint"></div>
<div class="cqbar"><b>Compiled after</b><select class="hrc" id="fHRC" aria-label="Campaign"></select><select class="hrc" id="fHRY" aria-label="Year"></select><select class="hrc" id="fHRM" aria-label="Month"></select><span class="cnt" id="hratNote"></span></div>
<div class="cqbar"><b>Card</b><button class="btn" id="btnHRTBlank" title="The card with the UC roster prefilled in columns A-D and every score cell empty, one worksheet plus a Read-me">Download blank template (Excel)</button><label class="btn" id="hrtFileL" title="An .xlsx of this card, or the CSV of the same columns. The 33 input columns are read back; the 39 score columns in the file are compared with the formulas here and any disagreement is reported">Upload filled sheet<input type="file" id="hrtFile" accept=".xlsx,.xls,.csv" style="display:none"></label><button class="btn" id="btnHRX" title="Every council on this sheet, with all 39 computed columns written as live Excel formulas">Download filled sheet (Excel)</button><button class="btn" id="btnHRTSeed" title="Fill the grid with the councils the dashboard holds for the districts picked in the grid's own division and district boxes">Seed councils in view</button><button class="btn" id="btnHRTRow" title="Append one empty council row">Add one council</button><button class="btn" id="btnHRTCLEAR" title="Empty this period in this browser - a file you already downloaded is untouched">Clear this period</button><span class="cnt" id="hrtUcnt"></span></div>
<div class="card" id="hratRule"></div>
<div class="kpis">
<div class="card"><div class="kl">Councils in view</div><div class="kv" id="hk1">&ndash;</div><div class="ks" id="hk1s"></div></div>
<div class="card"><div class="kl">Every indicator answered</div><div class="kv" id="hk2">&ndash;</div><div class="ks" id="hk2s"></div></div>
<div class="card"><div class="kl">Low Risk councils</div><div class="kv" id="hk3" style="color:#15803d">&ndash;</div><div class="ks" id="hk3s"></div></div>
<div class="card"><div class="kl">Medium Risk</div><div class="kv" id="hk4" style="color:#b45309">&ndash;</div><div class="ks" id="hk4s"></div></div>
<div class="card"><div class="kl">High Risk</div><div class="kv" id="hk5" style="color:#b91c1c">&ndash;</div><div class="ks" id="hk5s"></div></div>
<div class="card"><div class="kl">Scored off an empty cell</div><div class="kv" id="hk6">&ndash;</div><div class="ks" id="hk6s"></div></div>
</div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">The card, in the template&rsquo;s own column order</h3><select class="hrc" id="hrtDiv" aria-label="Division shown"></select><select class="hrc" id="hrtDist" aria-label="District shown"></select><span style="flex:1"></span><button class="btn" id="btnHRThide">Hide the computed columns</button></div>
<div class="cap" id="hratCap"></div>
<div class="hrwrap" id="hrtWrap"><table class="hrgrid" id="tHRT"></table></div>
<div class="cqbar"><span class="cnt" id="hrtPager"></span><span class="cnt" id="hrtPageNote"></span></div></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">What the last import read</h3></div><div class="cap" id="hrtLog"></div></div>
</section>
"""

JS = r"""// ---------- HRA COMPILATION CARD: one council per row, the card's own formulas behind it ----------
// The 72 columns are the template's, in the template's order: A-E profile, F-P Geographic Terrain and
// Security Access, Q-AN Epidemiology & Surveillance, AO-BD SIA Operations, BE-BP Essential Immunization
// / EPI-PEI Synergy, then BQ-BT. Staff type into the 33 raw cells; the other 39 are computed here by the
// same formula text the exported workbook carries, so the screen and the file cannot disagree.
const HRTIN=HRAT.c.filter(c=>c.k!=='computed'),HRTFX=HRAT.c.filter(c=>c.k==='computed'),
 HRT_L={},HRT_PG=60,HRT_DG={PLAIN:0,HILLY:0};
HRAT.c.forEach(c=>{HRT_L[c.L]=c;});
HRAT.i.forEach(x=>{if(x.f.indexOf('ISBLANK')>=0)HRT_DG[x.raw[0]]=1;});
const HRTL=HRAT.tail,HRTKEY=p=>'kp.hrat.'+p,
 HRTMO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
 HRTN=s=>String(s==null?'':s).toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const HRTRAW=HRAT.i.filter(x=>x.raw&&x.raw.length).map(x=>HRT_L[x.raw[0]]||{L:x.raw[0]});
let hrtRows=[],hrtLog=[],hrtPage=0,hrtAll=[],_HRTC=null,hrtTimer=null,hrtHide=false;
const HRT_P=()=>[el('fHRY').value,el('fHRM').value,el('fHRC').value];
const hrtSlug=()=>{const p=HRT_P();
 return String(p[2]).replace(/[^A-Za-z0-9]+/g,'-').replace(/^-|-$/g,'')+'_'+p[0]+'-'+p[1];};
const hrtTitle=()=>'HRA UC Level '+hrtSlug();
function hrtPeriods(){
 const out=[],seen={};
 const add=(l,y,m)=>{if(!l||!y)return;l=String(l).trim();if(seen[l])return;seen[l]=1;
  out.push({l:l,y:+y,m:m?+m:null});};
 if(typeof SND!=='undefined'&&SND&&SND.n&&SND.st){const p=String(SND.st).split('-');
  add(SND.n,p[0],p[1]);}
 (typeof CQ!=='undefined'&&CQ&&CQ.camps||[]).forEach(c=>{const k=CQK(c.l||c.v||'');
  if(k)add(c.l||c.v,2000+ +k.slice(3),{'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,'JUL':7,
   'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}[k.slice(0,3)]||null);});
 if(!out.length&&typeof CAMP!=='undefined')['A','M','S'].forEach(k=>{const c=CAMP[k],m=CQK(c);
  if(m)add(c,2000+ +m.slice(3),{'APR':4,'MAY':5,'SEP':9}[m.slice(0,3)]||null);});
 return out.sort((a,b)=>(b.y*100+(b.m||0))-(a.y*100+(a.m||0)));}
// one evaluator per rows array: a fresh arrays means an import or a period change, an edited cell is
// the same array mutated in place, which compute() reads on the next call.
function hrtMk(){if(!_HRTC||_HRTC.rows!==hrtRows)_HRTC={rows:hrtRows,mk:hratMake(HRAT,hrtRows)};
 return _HRTC.mk;}
function hrtVals(){
 const mk=hrtMk(),v=hrtRows.map((_,i)=>mk.compute(i));
 const br=v.map(o=>typeof o.v[HRTL.ovr]==='number'?o.v[HRTL.ovr]:null),rk=hratRank(br,false);
 v.forEach((o,i)=>{o.rank=rk[i];o.v[HRTL.rank]=rk[i]==null?'#N/A':rk[i];});
 return v;}
function hrtCellV(c){let v=c?c.value:null;
 if(v==null)return null;
 if(v instanceof Date)return null;
 if(typeof v==='object'){
  if(Array.isArray(v.richText))v=v.richText.map(x=>x.text).join('');
  else if(v.result!==undefined)v=v.result;
  else if(v.text!==undefined)v=v.text;
  else if(v.hyperlink)v=v.hyperlink;
  else v=null;}
 if(typeof v==='string'){const t=v.trim();return t===''?null:t;}
 return v;}
// entry=true is a cell typed on this page: there "38%" means the percent, as the column reads it.
// An import passes entry=false and keeps whatever Excel stored, because that is the cell the grader sees.
function hrtIn(c,v,entry){
 if(v===null||v===undefined)return null;
 if(c.k==='pct'&&typeof v==='number'&&v>1)return v/100;
 if(typeof v!=='string')return v;
 const t=v.trim(),o=c.o.filter(Boolean);
 if(c.k==='pct'||c.k==='rate'){
  if(entry&&/^-?\d+(\.\d+)?%$/.test(t))return parseFloat(t)/100;
  if(/^-?\d+(\.\d+)?$/.test(t)){const n=+t;return c.k==='pct'&&n>1?n/100:n;}
  return t;}
 if(o.length){const m=o.find(x=>HRTN(x)===HRTN(t));if(m)return m;
  const a=HRAT.alias[t];
  if(a&&o.some(x=>HRTN(x)===HRTN(String(a))))return a;
  return t;}
 if(c.k==='yesno'&&HRAT.alias[t])return HRAT.alias[t];
 if(c.k==='cnt'&&/^-?\d+(\.\d+)?$/.test(t))return +t;
 return t;}
function hrtBlankRow(){const o={};HRTIN.forEach(c=>{o[c.L]=null;});return o;}
function hrtStore(){
 try{localStorage.setItem(HRTKEY(hrtSlug()),JSON.stringify({v:1,asof:HRAT.asof,rows:hrtRows}));}
 catch(e){hrtLogAdd('This browser would not keep the sheet (localStorage is full or blocked). The '
  +'download still works; the sheet will not be here on the next visit.');}}
function hrtLoad(){
 let d=null;
 try{d=JSON.parse(localStorage.getItem(HRTKEY(hrtSlug()))||'null');}catch(e){}
 if(!d||!Array.isArray(d.rows)){hrtRows=[];return 'none';}
 hrtRows=d.rows.map(r=>{const o=hrtBlankRow();
  HRTIN.forEach(c=>{if(r&&r[c.L]!==undefined)o[c.L]=r[c.L];});return o;});
 return hrtRows.length?'kept':'none';}
function hrtLogAdd(m){hrtLog.unshift(m);hrtLog=hrtLog.slice(0,10);
 if(el('hrtLog'))el('hrtLog').innerHTML=hrtLog.map(x=>'<div>&middot; '+esc(x)+'</div>').join('');}
function hrtRoster(view){
 const out=[],seen={},inD=view?(()=>true):(typeof crInD==='function'?crInD():(()=>true));
 const dv=view&&el('hrtDiv')?el('hrtDiv').value:'',dd=view&&el('hrtDist')?el('hrtDist').value:'';
 const push=(v,d,u,c)=>{if(!c)return;const k=String(c).trim();
  if(!k||seen[k]||!inD(d)||(dv&&String(v||'')!==dv)||(dd&&String(d||'')!==dd))return;
  seen[k]=1;const o=hrtBlankRow();o.A=v||'';o.B=d||'';o.C=u||'';o.D=k;out.push(o);};
 try{c3UC().forEach(r=>push(r.dv,r.d,r.u,r.c));}catch(e){}
 if(!out.length&&typeof ZD!=='undefined')ZD.forEach(r=>push(r.dv,r.d,r.u,r.c));
 if(!out.length&&typeof EPI!=='undefined')EPI.forEach(r=>push(r.dv,r.d,r.u,r.c));
 return out;}
// band.hi/lo are printed as percentages (79/60) while BR is stored as a fraction (0.79/0.60)
const hrtBand=v=>v==null?null:(v*100>HRAT.band.hi?0:v*100<HRAT.band.lo?2:1);
const hrtNum=v=>typeof v==='number'&&isFinite(v);
function hrtShow(c,v){
 if(v&&typeof v==='object'&&v.e)return v.e;
 if(v===null||v===undefined||v==='')return '';
 if(typeof v!=='number')return String(v);
 const f=String(c.f||'');
 if(f.indexOf('%')>=0){const m=/0\.(0+)/.exec(f),dg=m?m[1].length:0;
  return (v*100).toFixed(dg)+'%';}
 return String(Math.round(v*1e6)/1e6);}
function hrtScope(){
 const dv=el('hrtDiv'),dd=el('hrtDist'),k0=dv.value,k1=dd.value,D={},B={};
 hrtRows.forEach(r=>{if(r.A)D[r.A]=1;if(r.B)B[r.B]=1;});
 dv.innerHTML='<option value="">All divisions</option>'+Object.keys(D).sort()
  .map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
 dd.innerHTML='<option value="">All districts</option>'+Object.keys(B).sort()
  .map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
 dv.value=D[k0]?k0:'';dd.value=B[k1]?k1:'';}
function hrtView(){
 const dv=el('hrtDiv').value,dd=el('hrtDist').value,out=[];
 hrtRows.forEach((r,i)=>{if(dv&&String(r.A||'')!==dv)return;if(dd&&String(r.B||'')!==dd)return;
  out.push(i);});
 return out;}
function hrtHead(){
 const blk=HRAT.B.map(b=>{const w=HRAT.c.findIndex(c=>c.L===b.g[1])-HRAT.c.findIndex(c=>c.L===b.g[0])+1;
  const t=b.t||(b.g[0]==='BQ'?'Total score':b.g[0]==='BR'?'% Score Achieved'
   :b.g[0]==='BS'?'Rank':'Risk');
  return '<th class="blk" colspan="'+w+'">'+esc(t)+'</th>';}).join('');
 const hd=HRAT.c.map(c=>{
  if(c.k==='computed'&&hrtHide)return '';
  const x=HRAT.i.filter(y=>y.sc===c.L)[0]||HRAT.i.filter(y=>y.raw[0]===c.L)[0];
  const rule=x&&x.rule?' &middot; printed rule: '+x.rule:'';
  return '<th class="hd'+(c.k==='computed'?' cf':'')+'" title="'+esc(c.L+': '+c.h+rule)+'">'
   +'<span class="cl">'+c.L+'</span>'+esc(c.h)+'</th>';}).join('');
 return '<thead><tr>'+blk+'</tr><tr>'+hd+'</tr></thead>';}
function hrtInCell(c,i,r){
 const v=r[c.L]==null?'':String(r[c.L]),o=c.o.filter(Boolean);
 if(o.length){
  const off=v&&!o.some(x=>HRTN(x)===HRTN(v));
  return '<td class="'+(off?'hrt-off':'')+'"><select class="hrt-i" data-i="'+i+'" data-c="'+c.L
   +'" aria-label="'+esc(c.h)+'"><option value=""></option>'
   +o.map(x=>'<option value="'+esc(x)+'"'+(HRTN(x)===HRTN(v)?' selected':'')+'>'+esc(x)
    +'</option>').join('')
   +(off?'<option value="'+esc(v)+'" selected>'+esc(v)+' \u2014 not on the list</option>':'')
   +'</select></td>';}
 const num=c.k==='pct'||c.k==='rate'||c.k==='cnt';
 return '<td><input class="hrt-i'+(num?' num':'')+'" data-i="'+i+'" data-c="'+c.L+'" value="'
  +esc(v)+'" aria-label="'+esc(c.h)+'"'+(num?' inputmode="decimal"':'')+'></td>';}
function hrtRowHTML(i,V){
 let s='<tr data-i="'+i+'">';
 HRAT.c.forEach(c=>{
  if(c.k!=='computed'){s+=hrtInCell(c,i,hrtRows[i]);return;}
  if(hrtHide)return;
  const v=V.v[c.L],err=v&&typeof v==='object'&&v.e,txt=hrtShow(c,v);
  const cls='hrt-c'+(err?' err':'')
   +(typeof v==='number'&&c.L===HRTL.ovr?' band':'')
   +(typeof v==='number'&&v===0&&c.L!==HRTL.max&&c.h!==HRTL.risk?' zero':'');
  s+='<td class="'+cls+'" data-c="'+c.L+'"'+(txt?' title="'+esc(c.h+': '+txt)+'"':'')+'>'
   +esc(txt)+'</td>';});
 return s+'</tr>';}
function hrtTable(V){
 const idx=hrtView(),n=Math.max(1,Math.ceil(idx.length/HRT_PG));
 if(hrtPage>=n)hrtPage=n-1;
 if(hrtPage<0)hrtPage=0;
 const slice=idx.slice(hrtPage*HRT_PG,(hrtPage+1)*HRT_PG),
  cols=HRAT.n-(hrtHide?HRTFX.length:0);
 el('tHRT').innerHTML=hrtHead()+'<tbody>'+(slice.length
  ?slice.map(i=>hrtRowHTML(i,V[i])).join('')
  :'<tr><td class="cnt" colspan="'+cols+'">Nothing compiled for this period yet. Download the blank '
   +'template and fill it in Excel, upload a filled sheet, or seed the councils the dashboard holds.'
   +'</td></tr>')+'</tbody>';
 el('tHRT').querySelectorAll('.hrt-i').forEach(x=>{
  const set=()=>{const i=+x.dataset.i,c=HRT_L[x.dataset.c];
   hrtRows[i][c.L]=hrtIn(c,x.value,true);hrtTouch();};
  x.oninput=set;if(x.tagName==='SELECT')x.onchange=set;});
 const btn=j=>'<button class="pill'+(j===hrtPage?' on':'')+'" data-p="'+j+'">'
  +(j*HRT_PG+1)+'\u2013'+Math.min(idx.length,(j+1)*HRT_PG)+'</button>';
 el('hrtPager').innerHTML=idx.length>HRT_PG?Array.from({length:n},(_,j)=>btn(j)).join(''):'';
 el('hrtPager').querySelectorAll('button').forEach(b=>b.onclick=()=>{hrtPage=+b.dataset.p;
  hrtPaint(hrtVals());el('hrtWrap').scrollTop=0;});
 el('hrtPageNote').textContent=slice.length+' of '+idx.length+' rows on screen \u00b7 the download '
  +'always carries all '+hrtRows.length+' rows on the sheet.';}
function hrtTouch(){hrtStore();if(hrtTimer)clearTimeout(hrtTimer);
 hrtTimer=setTimeout(()=>{hrtTimer=null;hrtPaint(hrtVals());},320);}
function hrtPaint(V){hrtAll=V;hrtTable(V);hrtKpi(V);hrtBadge();}
function hrtKpi(V){
 const idx=hrtView(),R=idx.map(i=>V[i]);
 const done=idx.filter(i=>HRTRAW.every(c=>r0(hrtRows[i],c))).length,
  marks=idx.filter(i=>HRTRAW.some(c=>r0(hrtRows[i],c)));
 const num=marks.map(i=>V[i]).filter(o=>hrtNum(o.v[HRTL.ovr])),b=[0,0,0];
 num.forEach(o=>{const x=hrtBand(o.v[HRTL.ovr]);if(x!=null)b[x]++;});
 const mean=num.length?num.reduce((s,o)=>s+o.v[HRTL.ovr],0)/num.length*100:null;
 const bl=R.reduce((s,o)=>s+(o.blanks||0),0);
 el('hk1').textContent=fmt(idx.length);
 el('hk1s').textContent=idx.length===hrtRows.length?'every row on this sheet'
  :fmt(idx.length)+' of '+fmt(hrtRows.length)+' \u00b7 all '+fmt(hrtRows.length)+' download';
 el('hk2').textContent=fmt(done);
 el('hk2s').textContent='of '+fmt(idx.length)+' \u00b7 '+fmt(HRTRAW.length)+' indicators a council, '
  +'a blank in one of them is not a zero';
 el('hk3').textContent=fmt(b[0]);
 el('hk3s').textContent=HRAT.band.labels[0]+' \u00b7 over '+HRAT.band.hi+'% of the maximum \u00b7 '
  +'of the '+fmt(marks.length)+' rows carrying at least one mark';
 el('hk4').textContent=fmt(b[1]);
 el('hk4s').textContent=HRAT.band.labels[2]+' \u00b7 between the two thresholds';
 el('hk5').textContent=fmt(b[2]);
 el('hk5s').textContent=HRAT.band.labels[1]+' \u00b7 under '+HRAT.band.lo+'%'
  +(mean==null?'':' \u00b7 mean '+mean.toFixed(1)+'% here');
 el('hk6').textContent=fmt(bl);
 el('hk6s').textContent='indicators this sheet scores on a cell nobody filled'
  +(HRAT.blank?' \u00b7 the province sheet left '+fmt(HRAT.blank.cells)+' over '
   +fmt(HRAT.blank.rows)+' rows':'');}
const r0=(o,c)=>{const v=(o&&o.v?o.v:o)[c.L];return v!==null&&v!==undefined&&v!=='';};
function hrtBadge(){const b=el('bHRT');if(!b)return;
 b.textContent=hrtRows.length?fmt(hrtRows.length)+' rows':'\u2013';
 const x=el('hrtUcnt');
 if(x)x.textContent=hrtRows.length?'this sheet is stored in this browser only':'';}
function hrtRule(){
 el('hratRule').innerHTML='<div class="tblhdr"><h3 style="margin:0">Where the card as printed and '
  +'the card as compiled disagree \u2014 and what this sheet does about each</h3></div><ul class="hrul">'
  +(HRAT.warn||[]).map(w=>'<li><b>'+w.col+(w.raw?' reads '+esc(w.raw):'')+'</b>'
   +(w.to&&w.to!=='the rows on the sheet'?' \u2192 <code>'+esc(w.to)+'</code>':'')
   +'<div>'+esc(w.why)+'</div></li>').join('')
  +'</ul>';}
function renderHRT(){
 hrtWire();
 // hrtScope() builds both selects from hrtRows, so it has to run after the saved sheet is read;
 // ahead of hrtLoad() it left the division and district lists empty on every first visit.
 const st=hrtLoad(),V=hrtVals();
 hrtScope();
 if(!hrtLog.length)hrtLogAdd(st==='kept'?'This browser had a sheet saved for this period.'
  :'No sheet saved for this period yet \u2014 nothing is invented to fill it.');
 el('hratHint').innerHTML='<b>The card every division compiles after a campaign, online.</b> '
  +HRAT.n+' columns in the template\u2019s own order \u00b7 '+HRAT.nsc+' indicators at '+HRAT.perind
  +' marks each \u00b7 '+HRTIN.length+' cells typed and '+HRTFX.length+' computed here from the same '
  +'formula text the download carries, so the screen cannot report a council differently from the file '
  +'it hands back. '+HRAT.fixed+' indicators always apply and '+HRAT.nmax+' more are charged when '
  +'answered with a number, so the printed maximum is '+HRAT.full+'. Risk follows the card\u2019s own axis: '
  +HRAT.band.labels[0]+' over '+HRAT.band.hi+'%, '+HRAT.band.labels[1]+' under '+HRAT.band.lo+'%, '
  +HRAT.band.labels[2]+' between \u2014 <b>a high percentage is a safe council</b>, the opposite '
  +'direction to the combined UC risk score on the Cross-cutting pages. The two are never blended.'
  +' <b>Nothing here is uploaded:</b> this site is public, so the sheet lives in this browser only, '
  +'under the year, month and campaign above, and travels as the file you download. The card\u2019s '
  +'Remarks column is not on this grid and not in the dashboard payload.';
 el('hratCap').textContent='One row is one union council; the 33 white cells are the only place a figure '
  +'is entered and the grey ones are the card\u2019s own formulas. A cell left empty earns nothing, '
  +'but the maximum is charged on the answers that are numbers, so a row with a blank or a word is '
  +'graded over fewer marks '
  +'\u2014 that is the template\u2019s rule and this sheet keeps it. Type a percent as 38% or 0.38 in '
  +'a percent column.';
 el('btnHRThide').textContent=hrtHide?'Show the computed columns':'Hide the computed columns';
 hrtRule();hrtPaint(V);
 el('hratNote').innerHTML=esc(HRT_P().join(' \u00b7 '))+' \u00b7 '+fmt(hrtRows.length)+' councils \u00b7 '
  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';}
function hrtWire(){
 const PS=hrtPeriods(),C=el('fHRC'),Y=el('fHRY'),M=el('fHRM');
 if(!C.options.length){
  if(PS.length){C.innerHTML=PS.map(p=>'<option value="'+esc(p.l)+'" data-y="'+p.y+'" data-m="'
   +(p.m||'')+'">'+esc(p.l)+'</option>').join('');
   const yy=PS.map(p=>p.y).filter((v,i,a)=>a.indexOf(v)===i);
   const ny=new Date().getFullYear();if(yy.indexOf(ny)<0)yy.push(ny);
   Y.innerHTML=yy.sort().map(y=>'<option value="'+y+'">'+y+'</option>').join('');
   C.value=PS[0].l;Y.value=String(PS[0].y);}
  else{Y.innerHTML='<option value="'+new Date().getFullYear()+'">'+new Date().getFullYear()
   +'</option>';}
  M.innerHTML=HRTMO.map((m,i)=>'<option value="'+(i<9?'0':'')+(i+1)+'">'+m+'</option>').join('');
  if(PS.length&&PS[0].m)M.value=(PS[0].m<10?'0':'')+PS[0].m;
  C.onchange=()=>{const o=C.options[C.selectedIndex]||{dataset:{}};
   if(o.dataset.y)Y.value=o.dataset.y;
   if(o.dataset.m)M.value=(String(o.dataset.m).length<2?'0':'')+o.dataset.m;
   hrtRefresh();};
  Y.onchange=hrtRefresh;M.onchange=hrtRefresh;
  el('hrtDiv').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());};
  el('hrtDist').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());};
  el('btnHRThide').onclick=()=>{hrtHide=!hrtHide;
   el('btnHRThide').textContent=hrtHide?'Show the computed columns':'Hide the computed columns';
   hrtPaint(hrtVals());};
  el('btnHRTBlank').onclick=()=>hrtExport(hrtRoster(false),true);
  el('btnHRX').onclick=()=>hrtExport(hrtRows,false);
  el('btnHRTSeed').onclick=()=>{const R=hrtRoster(true);
   if(!R.length){toast('The dashboard holds no councils for that division and district');return;}
   hrtRows=R;hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());
   toast('Seeded '+fmt(R.length)+' councils');};
  el('btnHRTRow').onclick=()=>{hrtRows.push(hrtBlankRow());
   hrtPage=Math.floor((hrtRows.length-1)/HRT_PG);hrtStore();hrtScope();hrtPaint(hrtVals());
   toast('One council row added');};
  el('btnHRTCLEAR').onclick=()=>{
   if(!hrtRows.length){toast('This period is already empty');return;}
   if(!window.confirm('Empty the '+fmt(hrtRows.length)+' councils compiled for '+hrtSlug()
    +' in this browser? A file you already downloaded is untouched.'))return;
   hrtRows=[];try{localStorage.removeItem(HRTKEY(hrtSlug()));}catch(e){}
   hrtRefresh();toast('This period is empty now');};
  el('hrtFile').onchange=e=>{const f=e.target.files&&e.target.files[0];if(f)hrtImport(f);
   e.target.value='';};}}
function hrtRefresh(){
 hrtWire();
 const st=hrtLoad();
 hrtPage=0;hrtScope();
 hrtLogAdd(st==='kept'?'Loaded the sheet this browser saved for this period.'
  :'This period is empty in this browser.');
 hrtPaint(hrtVals());
 el('hratNote').innerHTML=esc(HRT_P().join(' \u00b7 '))+' \u00b7 '+fmt(hrtRows.length)+' councils \u00b7 '
  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';}
function hrtCsv(txt){
 const out=[],row=[];let s='',q=false;
 for(let i=0;i<txt.length;i++){const ch=txt.charAt(i);
  if(q){if(ch==='"'){if(txt.charAt(i+1)==='"'){s+='"';i++;}else q=false;}else s+=ch;continue;}
  if(ch==='"'){q=true;continue;}
  if(ch===','){row.push(s);s='';continue;}
  if(ch==='\n'){row.push(s);out.push(row);row.length=0;s='';continue;}
  if(ch==='\r')continue;
  s+=ch;}
 if(s!==''||row.length){row.push(s);out.push(row);}
 return out.map(r=>r.map(x=>{const t=String(x).trim();return t===''?null:t;}));}
function hrtHeaderRow(cells,n){let m=0;
 HRAT.c.forEach((c,j)=>{if(j<n&&HRTN(cells(j))===HRTN(c.h))m++;});
 return m;}
function hrtCsvRows(grid){
 let hdr=-1,best=0;
 for(let r=0;r<Math.min(8,grid.length);r++){
  const m=hrtHeaderRow(j=>grid[r][j],grid[r].length);
  if(m>best){best=m;hdr=r;}}
 if(hdr<0||best<Math.max(20,HRAT.n*0.4))return null;
 const out=[];
 for(let r=hdr+1;r<grid.length;r++){
  const row=grid[r],o=hrtBlankRow();let any=false;
  HRAT.c.forEach((c,j)=>{const v=row[j];
   if(v===null||c.k==='computed')return;o[c.L]=hrtIn(c,v,false);any=true;});
  if(!o.D&&!o.C)continue;
  out.push(o);}
 hrtLogAdd('Read '+fmt(out.length)+' councils from a CSV whose header line matched '+best+' of '
  +HRAT.n+' columns in the template order. The 39 score columns in the file were not trusted: they are '
  +'recomputed here from the cells typed beside them.');
 return out;}
function hrtSheetMap(ws,hdr){
 // trust the template order where the header row says it is still there, find a column by its printed
 // header where a division moved it, and report what was found by the second rule rather than the first
 const map={},moved=[],row=ws.getRow(hdr),by={};
 for(let j=1;j<=ws.columnCount;j++){const h=HRTN(hrtCellV(row.getCell(j)));
  if(h)(by[h]=by[h]||[]).push(j);}
 let ok=0;
 HRAT.c.forEach((c,j)=>{
  if(HRTN(hrtCellV(row.getCell(j+1)))===HRTN(c.h))ok++;
  map[c.L]={j:j+1,by:'order'};});
 HRAT.c.forEach((c,j)=>{const g=by[HRTN(c.h)]||[];
  if(HRTN(hrtCellV(row.getCell(j+1)))!==HRTN(c.h)&&g.length===1){
   map[c.L]={j:g[0],by:'header text'};moved.push(c.L);}});
 return {map:map,moved:moved,matched:ok,orderOK:ok>=HRAT.n-6};}
function hrtFromSheet(ws,fname){
 let hdr=0,best=0;
 for(let r=1;r<=Math.min(8,ws.rowCount);r++){
  const row=ws.getRow(r),m=hrtHeaderRow(j=>hrtCellV(row.getCell(j+1)),ws.columnCount);
  if(m>best){best=m;hdr=r;}}
 if(best<Math.max(20,HRAT.n*0.4)){
  hrtLogAdd(fname+': no header row of this card was found (best match '+best+' of '+HRAT.n
   +' columns over the first 8 rows), so nothing was imported.');
  hrtRefresh();return;}
 const M=hrtSheetMap(ws,hdr),out=[],pairs=[],odd={},txt={},conv={},seen={};
 let skipped=0,dupe=0;
 for(let r=hdr+1;r<=ws.rowCount;r++){
  const row=ws.getRow(r),o=hrtBlankRow();let any=false;
  HRTIN.forEach(c=>{
   const v=hrtCellV(row.getCell(M.map[c.L].j));
   if(v===null||v===undefined)return;
   o[c.L]=hrtIn(c,v,false);
   any=true;
   if(c.o.length&&c.o.filter(Boolean).every(x=>HRTN(x)!==HRTN(String(o[c.L]))))
    odd[c.L]=(odd[c.L]||0)+1;
   if(c.k==='pct'&&typeof v==='number'&&v>1)conv[c.L]=(conv[c.L]||0)+1;
   if((c.k==='pct'||c.k==='rate'||c.k==='cnt')&&typeof o[c.L]==='string')
    (txt[c.L]=txt[c.L]||[]).push(r);});
  if(!any||(!o.D&&!o.C)){skipped++;continue;}
  if(o.D){const k=String(o.D);if(seen[k])dupe++;else seen[k]=1;}
  out.push(o);pairs.push({r:r,o:o});}
 hrtRows=out;
 const V=hrtVals(),bad=[];
 bad.push(M.orderOK?'the header row matched '+best+' of '+HRAT.n+' columns in the template order'
  :'the header row did not sit in the template order: '+M.moved.length+' column(s) were found by '
    +'their printed header text instead of by position ('+M.moved.slice(0,8).join(', ')
    +(M.moved.length>8?' \u2026':'')+')');
 if(skipped)bad.push(fmt(skipped)+' row(s) carried neither a UC code nor a UC name and were skipped');
 if(dupe)bad.push(fmt(dupe)+' row(s) repeat a UC code already on the sheet');
 const tn=Object.keys(txt).reduce((s,k)=>s+txt[k].length,0);
 if(tn)bad.push(fmt(tn)+' cell(s) in a number or percent column hold text ('
  +Object.keys(txt).slice(0,6).map(k=>k+' x'+txt[k].length).join(', ')
  +'); kept exactly as Excel holds them, because Excel ranks any text above any number and charges '
  +'the cell into the maximum');
 const on=Object.keys(odd).reduce((s,k)=>s+odd[k],0);
 if(on)bad.push(fmt(on)+' cell(s) hold a value their own dropdown does not list ('
  +Object.keys(odd).slice(0,6).map(k=>k+' x'+odd[k]).join(', ')
  +'), shown as \u201cnot on the list\u201d rather than rewritten');
 const cn=Object.keys(conv).reduce((s,k)=>s+conv[k],0);
 if(cn)bad.push(fmt(cn)+' cell(s) in percent columns hold a percent number rather than a fraction ('
  +Object.keys(conv).slice(0,6).map(k=>k+' x'+conv[k]).join(', ')
  +') and were divided by 100, the unit the printed rules and formulas read. The file itself takes '
  +'them at face value (a 0% cell holding 87 shows 8,700%), so its score cells over those answers '
  +'differ from the figures here');
 const diff=[];
 pairs.forEach((p,i)=>{
  const row=ws.getRow(p.r);
  HRTFX.forEach(c=>{
   if(diff.length>=6||c.L===HRTL.rank)return;
   const cv=hrtCellV(row.getCell(M.map[c.L].j)),got=V[i].v[c.L];
   if(cv===null||typeof cv==='object'||got==null)return;
   if(got&&typeof got==='object'){diff.push('r'+p.r+' '+c.L+' file '+cv+' vs '+got.e);return;}
   if(typeof got==='number'&&hrtNum(cv)){if(Math.abs(cv-got)>1e-6)
    diff.push('r'+p.r+' '+c.L+' file '+cv+' vs '+Math.round(got*1e6)/1e6);}
   else if(typeof got==='string'&&String(cv)!==got)
    diff.push('r'+p.r+' '+c.L+' file "'+cv+'" vs "'+got+'"');});});
 if(diff.length)bad.push('computed cells in the file disagree with the card\u2019s own formula over the '
  +'cells typed in it ('+diff.join('; ')+'). The download writes the formula over the cells as this '
  +'page holds them, so Excel will show these figures; the two restated rules (the Rank range and the '
  +'NPEV threshold) are on the note above.');
 hrtLogAdd('Imported '+fmt(out.length)+' councils from '+fname+'. '+bad.join(' \u00b7 '));
 hrtPage=0;hrtStore();hrtScope();hrtPaint(V);}
function hrtImport(file){
 const csv=/\.csv$/i.test(file.name);
 const take=rows=>{if(!rows){hrtLogAdd(file.name+': no header row of this card was found in the CSV, so '
   +'nothing was imported.');hrtRefresh();return;}
  hrtRows=rows;hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());
  toast('Imported '+fmt(rows.length)+' councils');};
 if(csv){const fr=new FileReader();
  fr.onload=()=>take(hrtCsvRows(hrtCsv(String(fr.result||''))));
  fr.onerror=()=>toast('The file could not be read');
  fr.readAsText(file);return;}
 xlLib().then(X=>{const fr=new FileReader();
  fr.onload=()=>{const wb=new X.Workbook();
   wb.xlsx.load(fr.result).then(()=>{
    let ws=null;
    wb.worksheets.forEach(w=>{if(!ws&&String(w.name).toUpperCase().indexOf('HRA')>=0)ws=w;});
    ws=ws||wb.worksheets[0];
    if(!ws){hrtLogAdd(file.name+' holds no readable worksheet');hrtRefresh();return;}
    hrtFromSheet(ws,file.name);})
   .catch(()=>{hrtLogAdd('ExcelJS opened the file but could not read it as a workbook.');
    hrtRefresh();});};
  fr.onerror=()=>toast('The file could not be read');
  fr.readAsArrayBuffer(file);})
 .catch(()=>{hrtLogAdd('The Excel library did not load, so an .xlsx cannot be opened here. In Excel use '
   +'Save as \u2192 CSV and upload that instead.');hrtRefresh();});}
function hrtFx(c,r,last){
 let f=c.x||'';
 if(c.L===HRTL.rank){
  const A=HRAT.rank.anchor;
  f=f.replace(new RegExp('\\$?'+A[0]+'\\$?'+A[1]+':\\$?'+A[0]+'\\$?\\d+'),
   '$'+A[0]+'$'+A[1]+':$'+A[0]+'$'+last);}
 return f.replace(/\{r\}/g,String(r));}
const HRT_RANKNOTE='RANK.EQ is written over the rows this workbook actually holds. The template anchors '
 +'it to a fixed block, which on a longer sheet prints #N/A from the row after that block down.';
const HRT_CORR=(HRAT.warn||[]).map(w=>w.col+' ('+(w.raw||'')+'): '+(w.why||'')).join('   \u00b7   ');
function hrtExport(rows,blank){
 if(!rows||!rows.length){toast('Nothing to write for this period yet');return;}
 const stem=hrtTitle();
 xlLib().then(X=>{
  const wb=new X.Workbook();
  wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title=stem;
  // The score cells leave as formulas with no stored result, so Excel has to be told to run them on open
  // or the sheet reads as blanks until the first edit.
  wb.calcProperties.fullCalcOnLoad=true;
  const ws=wb.addWorksheet(String(HRAT.sh).slice(0,31),
   {views:[{state:'frozen',xSplit:4,ySplit:2}]});
  const last=HRAT.r0+rows.length-1;
  HRAT.B.forEach(b=>{
   const a=HRAT.c.findIndex(c=>c.L===b.g[0])+1,z=HRAT.c.findIndex(c=>c.L===b.g[1])+1;
   const t=b.t||(b.g[0]==='BQ'?'Total score':b.g[0]==='BR'?'% Score Achieved'
    :b.g[0]==='BS'?'Rank':'Risk');
   const cell=ws.getRow(1).getCell(a);
   cell.value=t;cell.font={bold:true};
   cell.alignment={horizontal:'center',vertical:'middle',wrapText:true};
   if(z>a)ws.mergeCells(1,a,1,z);});
  const hrow=ws.getRow(2);
  HRAT.c.forEach((c,j)=>{
   const cell=hrow.getCell(j+1);
   cell.value=c.h;cell.font={bold:true,size:10};
   cell.alignment={wrapText:true,vertical:'bottom'};
   cell.fill={type:'pattern',pattern:'solid',
    fgColor:{argb:c.k==='computed'?'FFE2E8F0':'FFEFF6E6'}};
   ws.getColumn(j+1).width=Math.min(28,Math.max(11,String(c.h).length*0.6+3));});
  [3,3,4,4].forEach((w,j)=>{ws.getColumn(j+1).width=Math.max(ws.getColumn(j+1).width||11,
   ['Division','District','UC Name','UC Code'][j].length+4);});
  rows.forEach((r,i)=>{
   const row=ws.getRow(HRAT.r0+i);
   HRAT.c.forEach((c,j)=>{
    const cell=row.getCell(j+1);
    if(c.k!=='computed'){
     const v=r[c.L];
     if(v!==null&&v!==undefined&&v!=='')cell.value=v;
    } else {
     // RANK.EQ arrived after the 2007 file format, so Excel stores it as `_xlfn.RANK.EQ`; written
     // without the prefix the file opens with #NAME? down the Rank column. The divisions' own sheets
     // carry the prefix too.
     const fx=hrtFx(c,HRAT.r0+i,last);
     cell.value={formula:c.L===HRTL.rank?'_xlfn.'+fx:fx};
     cell.font={color:{argb:'FF334155'}};}
    if(c.f&&c.f!=='General')cell.numFmt=c.f;
    if(typeof cell.value==='number')cell.alignment={horizontal:'right'};});});
  // One picker per answered column, over the whole block: ExcelJS takes the list as `formulae`, and the
  // per-cell form splits the block into overlapping ranges with no list on them.
  HRAT.c.forEach((c,j)=>{
   if(c.k==='computed')return;
   const list=(c.o||[]).filter(Boolean);
   if(!list.length)return;
   const col=ws.getColumn(j+1).letter;
   ws.dataValidations.add(col+HRAT.r0+':'+col+last,
    {type:'list',allowBlank:true,formulae:['"'+list.join(',')+'"']});});
  ws.getRow(1).height=24;ws.getRow(2).height=54;
  const note=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
  note.getColumn(1).width=26;note.getColumn(2).width=112;
  const add=(a,b)=>{const rr=note.addRow([a,String(b==null?'':b)]);
   rr.getCell(1).font={bold:true};rr.alignment={vertical:'top',wrapText:true};};
  add('Card','UC Level High Risk Assessment, '+HRAT.n+' columns in the order the template prints them.');
  add('Compiled after',HRT_P().join(' \u00b7 '));
  add('Councils on this sheet',rows.length+(blank?' \u00b7 blank: only columns A-D are prefilled':''));
  add('Made','KP Polio and Synergy Dashboard, payload of '+HRAT.asof+'. The '+HRTFX.length
   +' score, subtotal, percentage, maximum, rank and risk columns are live formulas in this file, not '
   +'pasted numbers: open it in Excel and they compute from the '+HRTIN.length+' columns staff type.');
  add('Maximum',HRAT.fixed+' indicators always apply at '+HRAT.perind+' marks each and '+HRAT.nmax
   +' more are charged when answered with a number, so the printed maximum is '+HRAT.full+(HRAT.blank?'. The source '
   +'sheets left '+fmt(HRAT.blank.cells)+' marks on cells nobody filled in':'.'));
  add('Rank',HRT_RANKNOTE);
  add('Corrections',HRT_CORR);
  add('Privacy','Nothing on this page is uploaded: the sheet was held in the browser and this workbook '
   +'is the only copy that leaves the machine.');
  return wb.xlsx.writeBuffer();})
 .then(buf=>{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],
   {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=stem+'.xlsx';document.body.appendChild(a);a.click();a.remove();
  toast((blank?'Blank template':'Filled sheet')+' downloaded ('+fmt(rows.length)
   +' rows, formulas live)');})
 .catch(()=>{
  const H=HRAT.c.map(c=>c.L+' '+c.h);
  csvDownload(stem+'.csv',H,rows.map(r=>HRAT.c.map(c=>c.k==='computed'||r[c.L]==null?'':r[c.L])));
  toast('The Excel library did not load, so the rows went out as CSV \u2014 a CSV carries no formulas, '
   +'so the '+HRTFX.length+' score columns have to be recalculated in Excel');});}
"""


def evaluator():
    """The evaluator proven by _refresh/hrat_parity.js, minus its CommonJS tail."""
    src = open(EVAL, encoding='utf-8').read()
    i = src.index("if (typeof module !== 'undefined'")
    return src[:i].rstrip()


def payload():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('%s is missing - run python _refresh/build_hrat.py first' % PAYLOAD)
    with open(PAYLOAD, encoding='utf-8') as f:
        return srcutil.dumps(json.load(f))


A_HRA = 'const HRA = '
A_TABS = "'hcamp','hrd','c3','cpre'"
A_NAV = ('   <button class="tab" data-tab="hrd"><span class="tl">High-risk district focus</span>'
         '<span class="badge" id="bHRD">\u2013</span></button>\r\n')
A_CSS = '.tab[data-tab="hrd"],#p-hrd{--tc:#9a3412}'
A_PANE = 'id="tHRDU"></table></div></div>\r\n</section>\r\n'
A_ICO = "Object.assign(TABICO,{hrd:'target',"
A_DISP = 'hrd:renderHRD,'
A_BADGE = 'c3Badge(); hrdBadge(); pcmBadge();'
A_XLP = 'const XLP=/^(ptp_|hrmp_|nov26_focus_|hrd_)/;'
A_JS = '// ---------- Campaign overview (district performance + triangulation) ----------'
A_HUB = ('<div class="hubchips"><button data-hl="c3">Comparison &amp; monitoring</button>'
         '<button data-hl="cpre">Pre-campaign readiness</button>')
A_HUB2 = ('<div class="hubchips"><button data-hl="hrd">High-risk district focus</button>'
          '<button data-hl="cpre">Pre-campaign</button>')

CSS = [
    '.tab[data-tab="hrat"],#p-hrat{--tc:#86198f}',
    '#p-hrat .cqbar{flex-wrap:wrap}',
    '#p-hrat select.hrc{font:12.5px var(--font-sans);padding:3px 7px;border-radius:7px;'
    'border:1px solid var(--color-border);background:#fff;color:var(--color-text)}',
    '#p-hrat .hrwrap{overflow:auto;max-height:66vh;border:1px solid var(--color-border);'
    'border-radius:8px;background:#fff}',
    '#p-hrat table.hrgrid{border-collapse:separate;border-spacing:0;font-size:11px;min-width:100%}',
    '#p-hrat table.hrgrid th,#p-hrat table.hrgrid td{border:1px solid #e5e7eb;padding:2px 5px;'
    'white-space:nowrap;vertical-align:middle}',
    '#p-hrat table.hrgrid th.blk{position:sticky;top:0;z-index:6;background:#eef2ff;color:#1e293b;'
    'font-size:11.5px;padding:4px 6px;text-align:center}',
    '#p-hrat table.hrgrid th.hd{position:sticky;top:25px;z-index:5;background:#f8fafc;color:#334155;'
    'font-weight:500;text-align:left;max-width:170px;overflow:hidden}',
    '#p-hrat table.hrgrid th.hd.cf{background:#eef2f7}',
    '#p-hrat table.hrgrid th.hd .cl{color:#94a3b8;font-weight:700;margin-right:4px}',
    '#p-hrat table.hrgrid td.hrt-c{background:#f8fafc;color:#334155;text-align:right;min-width:52px}',
    '#p-hrat table.hrgrid td.hrt-c.zero{color:#b91c1c;font-weight:600}',
    '#p-hrat table.hrgrid td.hrt-c.err{color:#7c3aed;font-style:italic}',
    '#p-hrat table.hrgrid td.hrt-c.band{font-weight:600}',
    '#p-hrat table.hrgrid td.hrt-off{background:#fef3c7}',
    '#p-hrat table.hrgrid td input.hrt-i,#p-hrat table.hrgrid td select.hrt-i{'
    'font:11px var(--font-sans);padding:1px 3px;border:1px solid var(--color-border-light);'
    'border-radius:4px;width:118px;background:#fff;color:var(--color-text)}',
    '#p-hrat table.hrgrid td input.hrt-i.num,#p-hrat table.hrgrid td select.hrt-i{width:74px}',
    '#p-hrat table.hrgrid tbody tr:hover td{background:#f0f9ff}',
    '#p-hrat ul.hrul{margin:6px 0 0;padding:0 0 0 18px;font-size:12.5px;'
    'color:var(--color-text-secondary)}',
    '#p-hrat ul.hrul li{margin:0 0 7px}',
    '#p-hrat ul.hrul code{font-size:11.5px;background:#f1f5f9;padding:1px 4px;border-radius:4px}',
    '#p-hrat .pill.on{background:var(--tc);border-color:var(--tc);color:#fff}',
    '#hrtFileL{display:inline-flex;align-items:center;gap:6px;cursor:pointer}',
]


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def build_edits(js_src, pay):
    return [
        ('payload', A_HRA, 'const HRAT = %s;\r\n' % pay + A_HRA),
        ('tabs', A_TABS, "'hcamp','hrd','hrat','c3','cpre'"),
        ('nav', A_NAV, A_NAV
         + '   <button class="tab" data-tab="hrat"><span class="tl">HRA compilation</span>'
           '<span class="badge" id="bHRT">\u2013</span></button>\r\n'),
        ('css', A_CSS, A_CSS + '\r\n' + '\r\n'.join(CSS)),
        ('pane', A_PANE, A_PANE + crlf(PANE)),
        ('tabico', A_ICO, "Object.assign(TABICO,{hrat:'list',hrd:'target',"),
        ('dispatch', A_DISP, A_DISP + 'hrat:renderHRT,'),
        ('badges', A_BADGE, 'c3Badge(); hrdBadge(); hrtBadge(); pcmBadge();'),
        ('xlp', A_XLP, 'const XLP=/^(ptp_|hrmp_|nov26_focus_|hrd_|HRA UC Level)/;'),
        ('js', A_JS, crlf(js_src) + '\r\n\r\n' + crlf(JS) + '\r\n' + A_JS),
        ('hubchip', A_HUB,
         '<div class="hubchips"><button data-hl="hrat">HRA compilation</button>'
         '<button data-hl="c3">Comparison &amp; monitoring</button>'
         '<button data-hl="cpre">Pre-campaign readiness</button>'),
        ('hubchip2', A_HUB2, A_HUB2.replace(
            '</button><button data-hl="cpre">',
            '</button><button data-hl="hrat">HRA compilation</button><button data-hl="cpre">')),
    ]


def apply(t, edits):
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times (expected 1) - the master no longer matches '
                             'what this patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times (expected 1) - not undoing something '
                             'this patch did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('ERR duplicate element ids after the HRA card: %s' % ', '.join(dup[:12]))
    miss = [i for i in NEW_IDS if t.count('id="%s"' % i) != 1]
    if miss:
        raise SystemExit('ERR the HRA card is missing an anchor id: %s' % ', '.join(miss))
    for once in ('const HRAT = {', 'function hratMake(spec, rows)', 'function renderHRT()',
                 'function hrtExport(', 'function hrtImport(', 'function hrtVals()',
                 'function hrtFromSheet(', 'hrat:renderHRT,', 'function hrtBadge(){',
                 'c3Badge(); hrdBadge(); hrtBadge(); pcmBadge();'):
        if t.count(once) != 1:
            raise SystemExit('ERR the HRA card lost %r (%d copies)' % (once, t.count(once)))
    i = t.index('const HRAT = ')
    j = t.index('\n', i)
    line = t[i:j].rstrip('\r')
    if '\r' in line or not line.endswith(';'):
        raise SystemExit('ERR const HRAT is not one terminated line')
    for need in ('"r0":3', '"n":72', '"sh":"UC Level HRA Template"', '3*COUNT(', '"band"'):
        if need not in line:
            raise SystemExit('ERR const HRAT lost %s' % need)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='apply in memory, report, write nothing')
    a = ap.parse_args()
    edits = build_edits(evaluator(), payload())
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'const HRAT = ' in v.text and 'id="p-hrat"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the HRA card is not applied')
        v.text = unapply(v.text, edits)
    else:
        v.require(not built, 'already applied (const HRAT / id="p-hrat" present)')
        v.text = apply(v.text, edits)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA card %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                v.delta(), 'added' if not a.unpatch else 'removed'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    if a.unpatch:
        print('OK hrat card removed from the master')
    else:
        print('OK hrat card in the master - the other three variants are synced by push_master.py, '
              "which needs the owner's word")
    return 0


if __name__ == '__main__':
    sys.exit(main())
