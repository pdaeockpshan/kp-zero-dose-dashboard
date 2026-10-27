# -*- coding: utf-8 -*-
"""HRA: notes in a popover, a campaign/month source for every chart, upload coverage, and an owner lock.

The owner asked, 27-Oct-2026:

  "Also adjust the notes section in HRA it should be popover as it is covering huge area and same goes
   for map in HRA section there should be campaign/month filter option and same for all related charts
   in HRA section. Also it should tell that out of total 1412 UCs that much ucs data is received and
   that much is awaited and from that division/districts. One more thing i want that nobody else can
   delete data except me or anyone using the dashboard link cant delete any data only I had that option"

What this module does, in the order of that message:

  * Notes. The "where the card as printed and the card as compiled disagree" block used to print every
    warning inline - 250px of prose above the grid on every visit. It is now a one-line bar with a
    "Read the notes" button that opens the same text in the tab's existing popover (ntOpen), which is
    already used by the long hint and caption blocks. Nothing is deleted from the page: the text lives
    in #hratRuleSrc and is copied into the popover on request.

  * Campaign / month. The at-a-glance section (band mix, score curve, indicator chart, district map,
    district table, CSV) read const HRA only - one published reading, always the whole province. It now
    carries a source picker: the published reading, the compiled sheet for the period in the picker at
    the top of the tab (which follows the campaign/year/month selects), or any other compile this
    browser has saved. A compiled source is scored by the card's own formulas against the same 36
    districts, so every chart, the map legend, the table and the CSV switch together. The publish
    reading is never blended with a compiled one; the hint says which is on screen.

  * Coverage. A card above the grid states the register - the 1,418 councils the HRA payload holds,
    in 36 districts - and splits this period's sheet against it by division and district: register,
    received, awaited, received %. A council counts as received when the sheet carries its UC code, or
    its district and UC name when the code is blank; rows outside the register are counted separately.
    The panel follows the division / district selects and the CSV carries the same rows; it is
    labelled with the register it is measured against, never with the ZD register (1,417) or any other.

  * Owner lock. Delete the rows in the filter, Seed councils in view, Clear this period and Clear all
    periods stay disabled until the owner key is entered. The key is compared against a SHA-256 digest
    (FNV fallback when crypto.subtle is unavailable) and is never written to the page or localStorage.
    This is a gate, not encryption: the sheet is in the visitor's own browser, so a delete can only
    ever touch their copy - but no visitor gets the delete controls at all without the key.

Applied to index.html after patch_hrat_scope.py; un-apply this module FIRST. `--unpatch` restores the
previous file byte for byte.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


HELPERS = crlf(r"""
// ---------- HRA round 2: owner lock, campaign / month source, upload coverage ----------
// The owner asked, 27-Oct-2026: "nobody else can delete data except me or anyone using the dashboard
// link cant delete any data only I had that option". The sheet lives in this browser (localStorage), so
// a delete only ever touches the copy in front of the visitor; this lock still keeps the delete
// controls dead on every browser that has not been given the owner key. It is a gate, not encryption -
// anyone who can open this file can read that browser's copy - so the key is compared against a digest
// and is never written to the page or to storage.
var HRA_OWN_SHA='829187022aaa519462abd95ffa80ce6bdc96fb82cbda11e11c8507dff5560e16',
 HRA_OWN_FNV='e53499fc',_hraOwn=false;
function hraFNV(s){var h=0x811c9dc5;for(var i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),0x01000193)>>>0;}
 return ('0000000'+h.toString(16)).slice(-8);}
function hraKeyOK(k){
 if(window.crypto&&crypto.subtle&&window.TextEncoder){
  return crypto.subtle.digest('SHA-256',new TextEncoder().encode(k)).then(function(b){
   var a=new Uint8Array(b),x='';for(var i=0;i<a.length;i++)x+=('0'+a[i].toString(16)).slice(-2);
   return x===HRA_OWN_SHA;});}
 return Promise.resolve(hraFNV(k)===HRA_OWN_FNV);}
function hraOwnUI(){
 const on=!!_hraOwn,b=el('btnHRTOWN');
 if(b){b.textContent=on?'Owner mode: on':'Owner mode';b.classList.toggle('on',on);}
 ['btnHRTSeed','btnHRTCLEAR','btnHRTCLEARALL','btnHRTDEL'].forEach(function(id){
  const x=el(id);if(!x)return;
  if(!x.dataset.bt)x.dataset.bt=x.title||'';
  if(id==='btnHRTDEL'){
   const dv=el('hrtDiv'),dd=el('hrtDist');
   x.disabled=!(on&&dv&&dd&&(dv.value||dd.value));
  }else x.disabled=!on;
  x.title=on?x.dataset.bt:'Owner only - unlock with the Owner mode button';});}
function hraOwnAsk(fn){
 if(_hraOwn){if(fn)fn();return;}
 const k=window.prompt('Owner key\n\nOnly the owner of this dashboard may delete compiled rows. '
  +'Enter the key to unlock the delete buttons for this visit.');
 if(k==null)return;
 hraKeyOK(k).then(function(ok){
  if(!ok){toast('That is not the owner key');return;}
  _hraOwn=true;hraOwnUI();toast('Owner mode on for this visit');
  if(fn)fn();});}
function hrvDk(s){return HRTN(s).replace(/ /g,'');}
let _HRVDIX=null,_HRVREG=null;
function hrvDix(){if(_HRVDIX)return _HRVDIX;const m={};
 (HRA.d||[]).forEach(function(c,i){m[hrvDk(c)]=i;m[hrvDk(DNAME(c))]=i;});
 return _HRVDIX=m;}
// The register the coverage panel measures: the councils the HRA payload itself holds, with the
// division the dashboard files each district under. It is not the ZD / missed-children register - the
// two differ by a few councils and this tab never mixes them.
function hrvReg(){
 if(_HRVREG)return _HRVREG;
 const D=(typeof HRA!=='undefined'&&HRA.d)||[],kg={};
 (typeof KPGEO!=='undefined'?KPGEO.d:[]).forEach(function(p){kg[p.c]=p.v;});
 const dvOf=function(c){const k=kg[c]||(typeof D2DV!=='undefined'?(D2DV[c]||null):null)||'Other';
  return HRV_DV[k]||k;};
 const R={n:0,byDist:{},byCode:{},byName:{},dvOf:dvOf};
 ((typeof HRA!=='undefined'&&HRA.u)||[]).forEach(function(r){
  const d=D[r[0]];if(!d)return;const c=String(r[2]==null?'':r[2]).trim();if(!c)return;
  const dv=dvOf(d),o=R.byDist[d]||(R.byDist[d]={c:d,dv:dv,n:0,got:0});
  o.n++;R.n++;
  R.byCode[c]={c:c,d:d,dv:dv};
  R.byName[hrvDk(d)+'|'+HRTN(r[1])]=c;});
 return _HRVREG=R;}
function hrvSlugLbl(sl){const m=/_(\d{4})-(\d{2})$/.exec(String(sl));
 return m?String(sl).slice(0,m.index)+' \u00b7 '+HRV_MO[+m[2]-1]+' '+m[1]:String(sl);}
function hrvPer(){const s=el('hrvPer');return s&&s.value?s.value:'pub';}
function hrvPerFill(){
 const s=el('hrvPer');if(!s)return;
 const keep=s.value||'pub',opts=[['pub','Published reading \u00b7 '+hrvD(HRA.asof)+' \u00b7 '
  +fmt(HRA.n)+' councils']];
 opts.push(['cur','Compiled sheet \u00b7 '+hrvSlugLbl(hrtSlug())+' \u00b7 '+fmt(hrtRows.length)
  +' councils (follows the picker above)']);
 const seen={cur:1};
 try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);
  if(!k||k.indexOf(HRTKEY(''))!==0)continue;const sl=k.slice(HRTKEY('').length);
  if(seen[sl])continue;seen[sl]=1;
  let n=0;try{const d=JSON.parse(localStorage.getItem(k)||'null');n=d&&d.rows?d.rows.length:0;}catch(e){}
  opts.push([sl,'Saved compile \u00b7 '+hrvSlugLbl(sl)+' \u00b7 '+fmt(n)+' councils']);}}catch(e){}
 s.innerHTML=opts.map(function(o){return '<option value="'+esc(o[0])+'">'+esc(o[1])+'</option>';})
  .join('');
 s.value=opts.some(function(o){return o[0]===keep;})?keep:'pub';}
// A saved period, or the one on screen, scored the way the payload is: one row per council, the 27
// indicator scores, marks earned over marks charged, the card's own band cuts.
function hrvCompiled(pid){
 const cur=pid==='cur',slug=cur?hrtSlug():pid;let rows=null;
 if(cur)rows=hrtRows.slice();
 else{try{const d=JSON.parse(localStorage.getItem(HRTKEY(slug))||'null');
  if(d&&Array.isArray(d.rows))rows=d.rows.map(function(r){const o=hrtBlankRow();
   HRTIN.forEach(function(c){if(r&&r[c.L]!==undefined)o[c.L]=r[c.L];});return o;});}catch(e){}}
 const meta={v:pid,pub:false,slug:slug,lbl:hrvSlugLbl(slug),date:slug,asof:slug,
  rows:rows?rows.length:0,skip:0,off:0,blank:0,dupe:0};
 if(!rows||!rows.length)return {U:[],meta:meta};
 const mk=hratMake(HRAT,rows),di=hrvDix(),seen={},out=[];
 rows.forEach(function(r,i){
  const k=hrvDk(r.B),dx=di[k];
  if(dx===undefined){meta.off++;return;}
  const v=mk.compute(i).v,ss=[];let ach=0,pos=0,ans=0;
  HRAT.i.forEach(function(x){const q=v[x.sc];
   if(typeof q==='number'&&isFinite(q)&&q>=0){ss.push(q);ach+=q;pos+=3;ans++;}else ss.push(-1);});
  if(!ans){meta.blank++;return;}
  const code=String(r.D==null?'':r.D).trim(),nk=code||('n|'+k+'|'+HRTN(r.C));
  if(seen[nk]){meta.dupe++;return;}
  seen[nk]=1;
  const pct=ach/pos*100;
  out.push([dx,String(r.C==null?'':r.C),code,ach,pos,Math.round(pct*10)/10,
   hrtBand(pct/100),0,ss]);});
 meta.skip=meta.off+meta.blank;
 return {U:out,meta:meta};}
function hrvPerMeta(P,CP){
 const pub=P==='pub';
 if(pub)return {v:'pub',pub:true,slug:'',lbl:'published reading',date:hrvD(HRA.asof),
  asof:HRA.asof,rows:HRA.n,skip:0,off:0,blank:0,dupe:0};
 return CP?CP.meta:{v:P,pub:false,slug:P,lbl:hrvSlugLbl(P),date:P,asof:P,
  rows:0,skip:0,off:0,blank:0,dupe:0};}
function hrtCovRows(){
 const R=hrvReg(),got={},gb={},seen={};let off=0;
 hrtRows.forEach(function(r){
  const code=String(r.D==null?'':r.D).trim(),dk=hrvDk(r.B),nm=HRTN(r.C);
  const key=code||('n|'+dk+'|'+nm);
  if(seen[key])return;seen[key]=1;
  let rg=code&&R.byCode[code]?R.byCode[code]:null;
  if(!rg){const k2=R.byName[dk+'|'+nm];rg=k2&&R.byCode[k2]?R.byCode[k2]:null;}
  if(!rg){off++;return;}
  if(!got[rg.c]){got[rg.c]=1;gb[rg.d]=(gb[rg.d]||0)+1;}});
 const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';
 const sdv=dv?HRTN(dv):'',sdd=dd?HRTN(dd):'';
 const list=Object.keys(R.byDist).map(function(d){
  const o=R.byDist[d],g=gb[d]||0;
  return {d:d,dv:o.dv,n:o.n,got:g,await:o.n-g};})
  .filter(function(o){
   if(sdv&&HRTN(o.dv)!==sdv&&HRTN(o.dv).indexOf(sdv)!==0)return false;
   if(sdd&&HRTN(DNAME(o.d))!==sdd&&HRTN(o.d)!==sdd&&hrvDk(DNAME(o.d))!==hrvDk(sdd))return false;
   return true;})
  .sort(function(a,b){return a.dv===b.dv?(DNAME(a.d)<DNAME(b.d)?-1:1):(a.dv<b.dv?-1:1);});
 const N=list.reduce(function(s,o){return s+o.n;},0),G=list.reduce(function(s,o){return s+o.got;},0);
 return {R:R,list:list,N:N,G:G,off:off,dv:dv,dd:dd};}
function hrtCov(){
 const T=el('hratCovT');if(!T)return;
 const C=hrtCovRows(),R=C.R,pc=C.N?C.G/C.N*100:0;
 const kp=function(l,v,s){return '<span>'+l+' <b style="font-size:15px">'+v+'</b> '
  +'<span style="color:var(--color-text-secondary)">'+s+'</span></span>';};
 el('hratCovK').innerHTML=kp('Register',fmt(C.N),'councils in '+fmt(C.list.length)+' district'
   +(C.list.length===1?'':'s')+(C.dv||C.dd?' in scope':''))
  +kp('Received',fmt(C.G),pc.toFixed(1)+'% of that register')
  +kp('Awaited',fmt(C.N-C.G),'no row on this period&rsquo;s sheet')
  +kp('Rows in view',fmt(hrtView().length),C.off?fmt(C.off)+' outside the register':'all matched');
 el('hratCovNote').innerHTML='Measured against the '+fmt(R.n)+' union councils on the HRA card&rsquo;s own '
  +'roster ('+fmt(Object.keys(R.byDist).length)+' districts). A council counts as received when this '
  +'period&rsquo;s sheet carries its UC code - or its district and UC name when the code is blank.'
  +(C.dv||C.dd?' Scope: <b>'+esc(C.dd||C.dv)+'</b>.':'')
  +(C.off?' '+fmt(C.off)+' row(s) on the sheet name a council outside the register.':'');
 T.innerHTML='<thead><tr><th>Division</th><th>District</th><th>Register</th><th>Received</th>'
  +'<th>Awaited</th><th>Received %</th></tr></thead><tbody>'
  +(C.list.length?C.list.map(function(o){
   return '<tr><td>'+esc(o.dv)+'</td><td>'+esc(DNAME(o.d))+'</td><td>'+fmt(o.n)+'</td><td>'
    +fmt(o.got)+'</td><td>'+fmt(o.await)+'</td><td>'+(o.n?(o.got/o.n*100).toFixed(1):'-')
    +'</td></tr>';}).join('')
   :'<tr><td colspan="6" class="cnt">Nothing in the register matches the selected division or '
    +'district.</td></tr>')
  +'</tbody><tfoot><tr class="tot"><td>All in scope</td><td>'+fmt(C.list.length)+' district'
  +(C.list.length===1?'':'s')+'</td><td>'+fmt(C.N)+'</td><td>'+fmt(C.G)+'</td><td>'+fmt(C.N-C.G)
  +'</td><td>'+(C.N?pc.toFixed(1):'-')+'</td></tr></tfoot>';}
function hrtCovCSV(){
 const C=hrtCovRows();
 const H=['Division','District','Register','Received','Awaited','Received %'];
 const rows=C.list.map(function(o){return [o.dv,DNAME(o.d),o.n,o.got,o.await,
  o.n?Math.round(o.got/o.n*1000)/10:''];});
 rows.push(['All',C.list.length+' district'+(C.list.length===1?'':'s'),C.N,C.G,C.N-C.G,
  C.N?Math.round(C.G/C.N*1000)/10:'']);
 csvDownload('HRA_coverage_'+(C.dv?C.dv+'_':'')+(C.dd?C.dd+'_':'')+hrtSlug()+'.csv',H,rows);}
""")

COV_HTML = crlf(r"""
<div class="card" id="hratCov" style="margin-bottom:14px">
<div class="tblhdr" style="margin-bottom:6px"><h3 style="margin:0">Upload coverage for this period</h3>
<span style="flex:1"></span>
<button class="btn" id="btnHRTcov" title="Register, received and awaited councils for every division and district on this period's sheet">Coverage (CSV)</button></div>
<div class="cnt" id="hratCovNote" style="display:block;margin:0 0 8px"></div><div id="hratCovK" style="display:flex;gap:20px;flex-wrap:wrap;font-size:13px;margin:2px 0 10px"></div>
<div style="overflow:auto;max-height:300px"><table class="shtbl" id="hratCovT"></table></div>
</div>
<div class="card" id="hratRule" style="padding:8px 12px"></div>
<div id="hratRuleSrc" style="display:none"></div>
""")

HRT_RULE = crlf(r"""function hrtRule(){
 const w=HRAT.warn||[];
 el('hratRuleSrc').innerHTML='<ul class="hrul">'+w.map(function(x){
  return '<li><b>'+x.col+(x.raw?' reads '+esc(x.raw):'')+'</b>'
   +(x.to&&x.to!=='the rows on the sheet'?' \u2192 <code>'+esc(x.to)+'</code>':'')
   +'<div>'+esc(x.why)+'</div></li>';}).join('')+'</ul>';
 el('hratRule').innerHTML='<div class="tblhdr" style="margin:0"><h3 style="margin:0">Notes on how this '
  +'card is read</h3><span class="cnt">'+w.length+' rule'+(w.length===1?'':'s')
  +' this sheet reads differently</span><span style="flex:1"></span>'
  +'<button type="button" class="btn ntbtn" id="btnHRTRULE" aria-expanded="false" '
  +'style="margin:0">Read the notes</button></div>';
 const b=el('btnHRTRULE');
 b.onclick=function(){
  if(b.classList.contains('on')){ntClose();return;}
  ntOpen(b,el('hratRuleSrc'));};}""")

HRV_HINT = crlf(r"""function hrvHint(X){
 const dvn=Object.keys(X.div).length,P=X.per||{pub:true,lbl:'published reading'};
 const lead=(X.scope?'<b>'+esc(X.sdv||'All divisions')+(X.sdd?' / '+esc(X.sdd):'')
  +' selected:</b> ':'')+'<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' district'
  +(X.nd===1?'':'s')+' and '+dvn+' division'+(dvn===1?'':'s');
 if(!P.pub){
  el('hrvHint').innerHTML=lead+' compiled for '+esc(P.lbl)+'.</b> The scores are read from the copies '
   +'of the card this browser holds for that period, through the card&rsquo;s own formulas. On the '
   +'card&rsquo;s axis '+fmt(X.bt[0])+' are Low Risk, '+fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])
   +' High ('+(X.bt[2]/X.n*100).toFixed(1)+'%). Marks earned counts an indicator only where the sheet '
   +'carries an answer, so a half-filled row is graded over the marks it charged. '
   +(P.skip?'<b>'+fmt(P.skip)+' row(s)</b> on the sheet are not charted: '
     +(P.off?fmt(P.off)+' name a district outside the register':'')
     +(P.off&&P.blank?' and ':'')+(P.blank?fmt(P.blank)+' carry no answer yet':'')+'. ':'')
   +'This is the compiled sheet, not the published province reading, and the two are never blended.';
  return;}
 const mix=X.mixed.map(function(o){
  return DNAME(o.c)+': '+o.old+' of '+o.n+' still on the March sheet';}).join('; ');
 el('hrvHint').innerHTML=lead+' carry an HRA reading dated '+esc(hrvD(HRA.asof))+'.</b> On the card&rsquo;s own axis '
  +fmt(X.bt[0])+' are Low Risk, '+fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])+' High ('
  +(X.bt[2]/X.n*100).toFixed(1)+'%). A high percentage here is a safe council &mdash; this is not the '
  +'combined UC risk score used on the Cross-cutting pages, and the two are never blended. '
  +fmt(X.vint[0])+' councils carry the 26 Oct Mardan-division sheets and '+fmt(X.vint[1])
  +' still carry the 26-Mar sheet'+(mix?' ('+esc(mix)+')':'')+'. The '+HRA.nx.length
  +' criteria the card leaves unscored are not in these figures, and neither is anything typed into the '
  +'card above: that sheet belongs to its own year, month and campaign.';}""")

HRV_RENDER = crlf(r"""function hrvRender(){
 const h=el('hrvHint');
 if(!h)return;
 hrvPerFill();
 const X=hrvData(),P=X.per||{pub:true};
 const s=el('hrvSrc');
 if(s)s.textContent=P.pub?'Read from the dashboard payload: one province reading dated '+hrvD(HRA.asof)
  :'Read from the sheet this browser holds for '+hrvSlugLbl(P.slug)+', scored by the card itself';
 if(!X.n){
  h.innerHTML=!P.pub?('The compiled sheet for '+esc(hrvSlugLbl(P.slug))+' holds no scored row'
   +(X.scope?' in the selected division or district':'')+'. Upload a filled sheet above, or pick '
   +'another campaign or the published reading.')
   :(X.scope?'No council in the selected division or district carries an HRA reading in the published '
    +'payload.':'The HRA payload is empty, so there is nothing to chart.');
  el('chrv1').textContent='';el('chrv2').textContent='';el('chrv3').textContent='';['hrv1','hrv2','hrv3'].forEach(function(id){const c=el(id);if(!c)return;try{(Highcharts.charts||[]).forEach(function(ch){if(ch&&ch.renderTo===c)ch.destroy();});}catch(e){}c.innerHTML='';});
  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  if(el('hrvTbl'))el('hrvTbl').innerHTML='';if(el('hrv3cap'))el('hrv3cap').textContent='';
  const S0=el('hrvPer');if(S0)S0.onchange=function(){hrvRender();};if(typeof ntPass==='function')ntPass();
  return;}
 hrvHint(X);
 hrvBand(X);
 hrvCurve(X);
 hrvInd(X);
 hrvMap(X);
 hrvTable(X);
 const K=el('hrvMK');
 if(K)K.onchange=function(){hrvMap(hrvData());};
 const B=el('btnHRVcsv');
 if(B)B.onclick=hrvCSV;
 const S=el('hrvPer');
 if(S)S.onchange=function(){hrvRender();};
 _HRVR=true;if(typeof ntPass==='function')ntPass();}""")

EDITS = [
    ('coverage-card-and-notes', '<div class="card" id="hratRule"></div>', COV_HTML),

    ('owner-button',
     '<span class="cnt" id="hrtUcnt"></span></div>',
     '<button class="btn" id="btnHRTOWN" title="Only the owner can delete compiled rows; unlock with '
     'the owner key">Owner mode</button><span class="cnt" id="hrtUcnt"></span></div>'),

    ('at-a-glance-source',
     '<span style="font-size:12px;color:var(--color-text-secondary)">The province&rsquo;s HRA sheets as '
     'they stand &mdash; read from the dashboard payload, not from the sheet compiled above</span>',
     crlf(r"""<select class="hrc" id="hrvPer" aria-label="Campaign or month the HRA charts read" style="max-width:320px"></select>
<span id="hrvSrc" style="font-size:12px;color:var(--color-text-secondary)"></span>""")),

    ('hrt-rule', crlf(r"""function hrtRule(){
 el('hratRule').innerHTML='<div class="tblhdr"><h3 style="margin:0">Where the card as printed and '
  +'the card as compiled disagree \u2014 and what this sheet does about each</h3></div><ul class="hrul">'
  +(HRAT.warn||[]).map(w=>'<li><b>'+w.col+(w.raw?' reads '+esc(w.raw):'')+'</b>'
   +(w.to&&w.to!=='the rows on the sheet'?' \u2192 <code>'+esc(w.to)+'</code>':'')
   +'<div>'+esc(w.why)+'</div></li>').join('')
  +'</ul>';}"""), HRT_RULE),

    ('helpers',
     crlf(r"""function hrvScope(){const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';
 return {dv:dv,dd:dd,k:HRTN(dv)+'\u0001'+HRTN(dd)};}"""),
     HELPERS + crlf(r"""function hrvScope(){const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';
 return {dv:dv,dd:dd,k:HRTN(dv)+'\u0001'+HRTN(dd)};}""")),

    ('data-head',
     crlf(r"""function hrvData(){
 const SC=hrvScope();
 if(_HRVD&&_HRVD.k===SC.k)return _HRVD;
 const U0=(typeof HRA!=='undefined'&&HRA.u)||[],D=(typeof HRA!=='undefined'&&HRA.d)||[];
 if(!U0.length){_HRVD={n:0,k:SC.k};return _HRVD;}"""),
     crlf(r"""function hrvData(){
 const SC=hrvScope(),P=hrvPer(),K=SC.k+'\u0001'+P,PUB=P==='pub';
 if(_HRVD&&_HRVD.k===K)return _HRVD;
 const CP=PUB?null:hrvCompiled(P);
 const U0=PUB?((typeof HRA!=='undefined'&&HRA.u)||[]):(CP?CP.U:[]),
  D=(typeof HRA!=='undefined'&&HRA.d)||[];
 if(!U0.length){_HRVD={n:0,k:K,per:hrvPerMeta(P,CP),empty:true};return _HRVD;}""")),

    ('data-result',
     ' _HRVD={k:SC.k,scope:!!(SC.dv||SC.dd),sdv:SC.dv,sdd:SC.dd,',
     ' _HRVD={k:K,per:hrvPerMeta(P,CP),pub:PUB,scope:!!(SC.dv||SC.dd),sdv:SC.dv,sdd:SC.dd,'),

    ('hint', crlf(r"""function hrvHint(X){
 const dvn=Object.keys(X.div).length;
 const mix=X.mixed.map(function(o){
  return DNAME(o.c)+': '+o.old+' of '+o.n+' still on the March sheet';}).join('; ');
 el('hrvHint').innerHTML=(X.scope?'<b>'+esc(X.sdv||'All divisions')+(X.sdd?' / '+esc(X.sdd):'')
  +' selected:</b> ':'')+'<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' district'
  +(X.nd===1?'':'s')+' and '+dvn+' division'+(dvn===1?'':'s')
  +' carry'
  +' an HRA reading dated '+esc(hrvD(HRA.asof))+'.</b> On the card&rsquo;s own axis '
  +fmt(X.bt[0])+' are Low Risk, '+fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])+' High ('
  +(X.bt[2]/X.n*100).toFixed(1)+'%). A high percentage here is a safe council &mdash; this is not the '
  +'combined UC risk score used on the Cross-cutting pages, and the two are never blended. '
  +fmt(X.vint[0])+' councils carry the 26 Oct Mardan-division sheets and '+fmt(X.vint[1])
  +' still carry the 26-Mar sheet'+(mix?' ('+esc(mix)+')':'')+'. The '+HRA.nx.length
  +' criteria the card leaves unscored are not in these figures, and neither is anything typed into the '
  +'card above: that sheet belongs to its own year, month and campaign.';}"""), HRV_HINT),

    ('render', crlf(r"""function hrvRender(){
 const h=el('hrvHint');
 if(!h)return;
 const X=hrvData();
 if(!X.n){h.innerHTML=X.scope?'No council in the selected division or district carries an HRA '
  +'reading in the published payload.':'The HRA payload is empty, so there is nothing to chart.';
  el('chrv1').textContent='';el('chrv2').textContent='';el('chrv3').textContent='';
  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  if(el('hrvTbl'))el('hrvTbl').innerHTML='';if(el('hrv3cap'))el('hrv3cap').textContent='';
  return;}
 hrvHint(X);
 hrvBand(X);
 hrvCurve(X);
 hrvInd(X);
 hrvMap(X);
 hrvTable(X);
 const K=el('hrvMK');
 if(K)K.onchange=function(){hrvMap(hrvData());};
 const B=el('btnHRVcsv');
 if(B)B.onclick=hrvCSV;
 _HRVR=true;}"""), HRV_RENDER),

    ('map-tip',
     crlf(r"""  if(!o2||!o2.n)return DNAME(c)+(X.scope?'\noutside the selected division / district'
   :'\nno HRA sheet');"""),
     crlf(r"""  if(!o2||!o2.n)return DNAME(c)+(X.scope?'\noutside the selected division / district'
   :(X.pub?'\nno HRA sheet':'\nno compiled row for this period'));""")),

    ('map-legend',
     crlf(r"""  +'border-radius:2px;background:#f1f5f9"></i>'+(X.scope?'not in the selected division / '
   +'district':'no sheet')+'</span></span>'"""),
     crlf(r"""  +'border-radius:2px;background:#f1f5f9"></i>'+(X.scope?'not in the selected division / '
   +'district':(X.pub?'no sheet':'no row this period'))+'</span></span>'""")),

    ('ind-caption',
     crlf(r""" el('hrv3cap').textContent='Marks earned as a share of the marks the card charges, '+fmt(X.n)
  +' council'+(X.n===1?'':'s')+(X.scope?' in the selected division / district':'')+' in the '
  +'published reading';"""),
     crlf(r""" el('hrv3cap').textContent='Marks earned as a share of the marks the card charges, '+fmt(X.n)
  +' council'+(X.n===1?'':'s')+(X.scope?' in the selected division / district':'')
  +(X.pub?' in the published reading':' in the compiled sheet for '+esc(hrvSlugLbl(X.per.slug)));""")),

    ('csv-sheets',
     crlf(r"""   o.ach,o.pos,o.dates];});"""),
     crlf(r"""   o.ach,o.pos,(X.pub?o.dates:X.per.slug+' (compiled)')];});""")),

    ('csv-name',
     crlf(r""" csvDownload('HRA_district_rollup_'+(X.sdv?X.sdv+'_':'')+(X.sdd?X.sdd+'_':'')+HRA.asof
  +'.csv',H,rows);}"""),
     crlf(r""" csvDownload('HRA_district_rollup_'+(X.sdv?X.sdv+'_':'')+(X.sdd?X.sdd+'_':'')
  +(X.pub?HRA.asof:X.per.slug)+'.csv',H,rows);}""")),

    ('note-coverage',
     crlf(r"""  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';}"""),
     crlf(r"""  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';
 if(typeof hrtCov==='function')hrtCov();}""")),

    ('scope-delete-disabled',
     " const bd=el('btnHRTDEL');if(bd)bd.disabled=!(dv.value||dd.value);}",
     " const bd=el('btnHRTDEL');if(bd)bd.disabled=!(_hraOwn&&(dv.value||dd.value));}"),

    ('scope-handlers',
     crlf(r"""  el('hrtDiv').onchange=()=>{hrtPage=0;hrtScope();hrtPaint(hrtVals());hrvRender();};
  el('hrtDist').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());hrvRender();};"""),
     crlf(r"""  el('hrtDiv').onchange=()=>{hrtPage=0;hrtScope();hrtPaint(hrtVals());hrtCov();hrvRender();};
  el('hrtDist').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());hrtCov();hrvRender();};""")),

    ('delete-gate',
     "  el('btnHRTDEL').onclick=hrtDel;",
     "  el('btnHRTDEL').onclick=()=>hraOwnAsk(hrtDel);"),

    ('seed-gate',
     crlf(r"""  el('btnHRTSeed').onclick=()=>{const R=hrtRoster(true);
   if(!R.length){toast('The dashboard holds no councils for that division and district');return;}
   hrtRows=R;hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());
   toast('Seeded '+fmt(R.length)+' councils');};"""),
     crlf(r"""  el('btnHRTSeed').onclick=()=>hraOwnAsk(()=>{const R=hrtRoster(true);
   if(!R.length){toast('The dashboard holds no councils for that division and district');return;}
   hrtRows=R;hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());
   _HRVD=null;hrtNote();hrvRender();
   toast('Seeded '+fmt(R.length)+' councils');});""")),

    ('clear-gate',
     crlf(r"""  el('btnHRTCLEAR').onclick=()=>{
   if(!hrtRows.length){toast('This period is already empty');return;}
   if(!window.confirm('Empty the '+fmt(hrtRows.length)+' councils compiled for '+hrtSlug()
    +' in this browser? A file you already downloaded is untouched.'))return;
   hrtRows=[];try{localStorage.removeItem(HRTKEY(hrtSlug()));}catch(e){}
   hrtRefresh();toast('This period is empty now');};"""),
     crlf(r"""  el('btnHRTCLEAR').onclick=()=>hraOwnAsk(()=>{
   if(!hrtRows.length){toast('This period is already empty');return;}
   if(!window.confirm('Empty the '+fmt(hrtRows.length)+' councils compiled for '+hrtSlug()
    +' in this browser? A file you already downloaded is untouched.'))return;
   hrtRows=[];try{localStorage.removeItem(HRTKEY(hrtSlug()));}catch(e){}
   hrtRefresh();toast('This period is empty now');});""")),

    ('clearall-gate',
     crlf(r"""  el('btnHRTCLEARALL').onclick=()=>{
   const ks=[];try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);
    if(k&&k.indexOf(HRTKEY(''))===0)ks.push(k);}}catch(e){}
   if(!ks.length){toast('This browser holds no saved HRA sheet');return;}
   if(!window.confirm('Remove the HRA sheets this browser saved for '+ks.length+' period'
    +(ks.length===1?'':'s')+' ('+ks.map(k=>k.slice(HRTKEY('').length)).join(', ')
    +')? A file you already downloaded is untouched.'))return;
   ks.forEach(k=>{try{localStorage.removeItem(k);}catch(e){}});
   hrtRefresh();toast('Removed every saved HRA sheet from this browser');};"""),
     crlf(r"""  el('btnHRTCLEARALL').onclick=()=>hraOwnAsk(()=>{
   const ks=[];try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);
    if(k&&k.indexOf(HRTKEY(''))===0)ks.push(k);}}catch(e){}
   if(!ks.length){toast('This browser holds no saved HRA sheet');return;}
   if(!window.confirm('Remove the HRA sheets this browser saved for '+ks.length+' period'
    +(ks.length===1?'':'s')+' ('+ks.map(k=>k.slice(HRTKEY('').length)).join(', ')
    +')? A file you already downloaded is untouched.'))return;
   ks.forEach(k=>{try{localStorage.removeItem(k);}catch(e){}});
   hrtRefresh();toast('Removed every saved HRA sheet from this browser');});""")),

    ('wire-tail',
     crlf(r"""  el('hrtFile').onchange=e=>{const f=e.target.files&&e.target.files[0];if(f)hrtImport(f);
   e.target.value='';};}}"""),
     crlf(r"""  el('hrtFile').onchange=e=>{const f=e.target.files&&e.target.files[0];if(f)hrtImport(f);
   e.target.value='';};
  el('btnHRTOWN').onclick=()=>{if(_hraOwn){_hraOwn=false;hraOwnUI();toast('Owner mode off');return;}
   hraOwnAsk(null);};
  el('btnHRTcov').onclick=hrtCovCSV;
  el('hrvPer').onchange=()=>hrvRender();}
 hraOwnUI();}""")),

    ('refresh-rerender',
     crlf(r""" const st=hrtLoad();
 hrtPage=0;hrtScope();
 hrtLogAdd(st==='kept'?'Loaded the sheet this browser saved for this period.'
  :'This period is empty in this browser.');
 hrtPaint(hrtVals());
 hrtNote();}"""),
     crlf(r""" const st=hrtLoad();
 hrtPage=0;hrtScope();
 hrtLogAdd(st==='kept'?'Loaded the sheet this browser saved for this period.'
  :'This period is empty in this browser.');
 hrtPaint(hrtVals());
 hrtNote();
 _HRVD=null;hrvRender();}""")),

    ('import-rerender',
     "  hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());hrtNote();\r\n"
     "  toast('Imported '",
     "  hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());hrtNote();\r\n"
     "  _HRVD=null;hrvRender();\r\n"
     "  toast('Imported '"),

    ('delete-rerender',
     " hrtPaint(hrtVals());hrtNote();hrvRender();",
     " hrtPaint(hrtVals());hrtNote();_HRVD=null;hrvRender();"),
]


def apply(t, edits):
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times - the master no longer matches what this '
                             'patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times - not undoing something this patch '
                             'did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    for once in ('id="hratCovT"', 'function hrtCov()', 'function hrtCovCSV()',
                 'function hrvCompiled(', 'function hrvPerFill()', 'id="hrvPer"',
                 'id="btnHRTOWN"', 'function hraOwnAsk(', 'id="hratRuleSrc"',
                 'id="btnHRTRULE"', "HRA_OWN_SHA=", 'hraOwnAsk(hrtDel)',
                 "el('btnHRTSeed').onclick=()=>hraOwnAsk(",
                 "el('btnHRTCLEAR').onclick=()=>hraOwnAsk(",
                 "el('btnHRTCLEARALL').onclick=()=>hraOwnAsk(",
                 'function hrvPerMeta(P,CP){', "el('btnHRTcov').onclick=hrtCovCSV"):
        if t.count(once) != 1:
            raise SystemExit('ERR the round-2 patch is missing %r (%d copies)' % (once, t.count(once)))
    if 'if(_HRVD&&_HRVD.k===SC.k)return _HRVD;' in t:
        raise SystemExit('ERR hrvData() still caches without the source picker')
    if "el('hratRule').innerHTML='<div class=\"tblhdr\"><h3" in t:
        raise SystemExit('ERR the notes block is still printed inline')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='apply in memory, report, write nothing')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'id="hratCovT"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the round-2 patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (hratCovT present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA round 2 %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                   v.delta(), 'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
