# -*- coding: utf-8 -*-
"""HRA card: make the round picker drive the coverage panel, the findings and the deck.

The owner asked, 25-Nov-2026: "when i select SNID MAY-2026 why data is still showing awaited as i
have shared compiled HRA file and its incorporated and why i cant see recommendations for SNID
MAY-2026 and PPTX. Kindly fix this and also SNID NOV-2026 is repeated with 2026 and 26 kindly
remove one".

Three defects, one cause: the lower half of the tab ignored the period picker.

  1. "SNID Nov-26" (from SND) and "SNID Nov 2026" (from the campaign list) are the same round, but
     hrtPeriods() deduped on the raw label. It now keys on the campaign prefix plus CQK's year and
     month, so one round is one entry; SND's spelling is the one kept.
  2. The coverage panel always measured the sheet this browser holds, so a round compiled into the
     dashboard (May and Sep 2026) read as "awaited" on every browser but the one that imported it.
     For a period the payload carries and this browser does not, the panel now reads the workbook:
     every council in it is received, nothing is owed.
  3. Findings, recommendations and the PPTX were rebuildable only from a browser-held sheet, so
     the May round produced an empty card. They now follow the same source the "HRA at a glance"
     charts read, and say which one they read.

The "HRA at a glance" picker also follows the period picker when the period changes: the sheet
this browser holds, else the payload's round for that month, else the published reading. A saved
sheet the reader picks by hand stays picked.

Rules kept:
  * One source per reading, never blended: the payload round and a browser sheet are separate.
  * No invented figure: every number is a roll-up of HRA.u / HRA.may.u or of the sheet's own rows.
  * Nothing is written to the compiled card by this module.

Applied to all four variants in one pass (the public trio must stay byte-identical). `--unpatch`
restores the previous text; `--check` prints what would change.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch


def nl(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


# ---------------------------------------------------------------- edits

PERIODS = (r''' const out=[],seen={};
 const add=(l,y,m)=>{if(!l||!y)return;l=String(l).trim();if(seen[l])return;seen[l]=1;
  out.push({l:l,y:+y,m:m?+m:null});};
''', r''' const out=[],seen={};
 // One entry per round. SND and the campaign list spell the same campaign differently
 // ("SNID Nov-26" / "SNID Nov 2026"), so the key is the campaign prefix plus CQK's year and
 // month, not the raw label; SND is added first, so its spelling is the one kept.
 const add=(l,y,m)=>{if(!l||!y)return;l=String(l).trim();
  const p=/^\s*(S?NID)/i.exec(l),k=(p?p[1].toUpperCase():'')+((typeof CQK==='function'&&CQK(l))||'');
  const key=k||l;
  if(seen[key])return;seen[key]=1;
  out.push({l:l,y:+y,m:m?+m:null});};
''')

SLUGLBL = (r'''function hrvSlugLbl(sl){const m=/_(\d{4})-(\d{2})$/.exec(String(sl));
 return m?String(sl).slice(0,m.index)+' \u00b7 '+HRV_MO[+m[2]-1]+' '+m[1]:String(sl);}
''', r'''function hrvSlugLbl(sl){const s=String(sl),m=/_(\d{4})-(\d{2})$/.exec(s);
 if(!m)return s;
 // The label usually carries the year already ("SNID-Nov-26"); printing the month and year
 // after it reads as a repeat, so only a label without a year gets the suffix.
 const b=s.slice(0,m.index);
 return /\b(19|20)\d{2}\b/.test(b)?b:b+' \u00b7 '+HRV_MO[+m[2]-1]+' '+m[1];}
''')

PERFILL = (r'''  +' councils (follows the picker above)']);
 const seen={cur:1};
''', r'''  +' councils (follows the picker above)']);
 // the current period's saved copy is the same sheet, so 'cur' stands for it
 const seen={};seen[hrtSlug()]=1;
''')

REFRESH = (r'''function hrtRefresh(){
 hrtWire();
 hrtImpBox('');
 const st=hrtLoad();
 hrtPage=0;hrtScope();
 hrtLogAdd(st==='kept'?'Loaded the sheet this browser saved for this period.'
  :'This period is empty in this browser.');
 hrtPaint(hrtVals());
 hrtNote();
 _HRVD=null;hrvRender();}
''', r'''// The period picker and the "HRA at a glance" picker are two questions, and a reader who changes
// the first expects the lower half to follow. On a period change the glance takes this browser's
// sheet if it holds one, else the round the payload carries for the same month, else the
// published reading; a saved sheet the reader picked by hand is left alone.
function hrtPerRound(){
 const P=HRT_P(),ym=P[0]+'-'+('0'+P[1]).slice(-2);
 const rd=(typeof HRA!=='undefined'&&HRA&&HRA.rd)||[];
 for(let i=0;i<rd.length;i++)if(rd[i][0]===ym)return rd[i];
 return null;}
function hrtPerAuto(){
 const s=el('hrvPer');if(!s)return;
 const cur=s.value||'pub';
 if(cur!=='pub'&&cur!=='cur'&&cur.indexOf('rnd:')!==0)return;
 const R=hrtPerRound(),rd=(typeof HRA!=='undefined'&&HRA&&HRA.rd)||[];
 let want='pub';
 if(hrtRows.length)want='cur';
 else if(R&&rd[1]&&rd[1][0]===R[0])want='rnd:'+R[0];
 if(cur!==want&&[].some.call(s.options,function(o){return o.value===want;}))s.value=want;}
function hrtRefresh(){
 hrtWire();
 hrtImpBox('');
 const st=hrtLoad();
 hrtPage=0;hrtScope();
 hrtLogAdd(st==='kept'?'Loaded the sheet this browser saved for this period.'
  :'This period is empty in this browser.');
 _HRVD=null;
 hrvPerFill();hrtPerAuto();
 hrtPaint(hrtVals());
 hrtNote();
 hrvRender();}
''')

COV_HEAD = (r'''<h3 style="margin:0">Upload coverage for this period</h3>''',
            r'''<h3 style="margin:0" id="hratCovH">Upload coverage for this period</h3>''')

COVROWS = (r'''function hrtCovRows(){
 const R=hrvReg(),got={},gb={},seen={};let off=0;
''', r'''// A round compiled into the dashboard has nothing to await: the workbook is the register. When
// this browser holds no sheet for the period but the payload carries the round, the panel reads
// that round's own rows instead of an empty tracker.
function hrtCovRound(){
 if(hrtRows.length)return null;
 const R=hrtPerRound();if(!R)return null;
 const rd=(typeof HRA!=='undefined'&&HRA&&HRA.rd)||[];
 const cur=!!(rd[0]&&rd[0][0]===R[0]);
 const U=cur?((HRA.u)||[]):((hrvRound('rnd:'+R[0])||{}).u||[]);
 if(!U.length)return null;
 return {R:R,U:U,cur:cur};}
function hrtCovRowsPub(PB){
 const D=(typeof HRA!=='undefined'&&HRA.d)||[],kg={};
 (typeof KPGEO!=='undefined'?KPGEO.d:[]).forEach(function(p){kg[p.c]=p.v;});
 const dvOf=function(c){const k=kg[c]||(typeof D2DV!=='undefined'?(D2DV[c]||null):null)||'Other';
  return HRV_DV[k]||k;};
 const seen={},by={};
 PB.U.forEach(function(r){
  const d=D[r[0]];if(!d)return;
  const code=String(r[2]==null?'':r[2]).trim(),k=code||(d+'|'+HRTN(r[1]));
  if(seen[k])return;seen[k]=1;
  const o=by[d]||(by[d]={d:d,dv:dvOf(d),n:0,got:0});o.n++;o.got++;});
 const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';
 const sdv=dv?HRTN(dv):'',sdd=dd?HRTN(dd):'';
 const list=Object.keys(by).map(function(d){const o=by[d];
  return {d:d,dv:o.dv,n:o.n,got:o.got,await:0};})
  .filter(function(o){
  if(sdv&&HRTN(o.dv)!==sdv&&HRTN(o.dv).indexOf(sdv)!==0)return false;
  if(sdd&&HRTN(DNAME(o.d))!==sdd&&HRTN(o.d)!==sdd&&hrvDk(DNAME(o.d))!==hrvDk(sdd))return false;
  return true;})
  .sort(function(a,b){return a.dv===b.dv?(DNAME(a.d)<DNAME(b.d)?-1:1):(a.dv<b.dv?-1:1);});
 const N=list.reduce(function(s,o){return s+o.n;},0),G=list.reduce(function(s,o){return s+o.got;},0);
 return {R:{n:N,lbl:PB.R[1]},list:list,N:N,G:G,off:0,dv:dv,dd:dd,wb:true,
  note:'This period was compiled into the dashboard from the HRA workbook ('+esc(PB.R[1])+', dated '
   +esc(hrvD(PB.R[2]))+'): every council in it is received, so nothing is awaited. The card in this '
   +'browser holds no sheet for this period, so the tracker below has nothing to measure &mdash; '
   +'download the blank card and import a division&rsquo;s file to compile or correct it here. A '
   +'council counts once, by UC code.'
   +(dv||dd?' Scope: <b>'+esc(dd||dv)+'</b>.':'')};}
function hrtCovRows(){
 const PB=hrtCovRound();
 if(PB)return hrtCovRowsPub(PB);
 const R=hrvReg(),got={},gb={},seen={};let off=0;
''')

COV_RETURN = (r''' const N=list.reduce(function(s,o){return s+o.n;},0),G=list.reduce(function(s,o){return s+o.got;},0);
 return {R:R,list:list,N:N,G:G,off:off,dv:dv,dd:dd};}
''', r''' const N=list.reduce(function(s,o){return s+o.n;},0),G=list.reduce(function(s,o){return s+o.got;},0);
 return {R:R,list:list,N:N,G:G,off:off,dv:dv,dd:dd,
  note:'Measured against the '+fmt(R.n)+' union councils on the HRA card&rsquo;s own roster ('
   +fmt(Object.keys(R.byDist).length)+' districts). A council counts as received when this period&rsquo;s '
   +'sheet carries its UC code - or its district and UC name when the code is blank.'
   +(dv||dd?' Scope: <b>'+esc(dd||dv)+'</b>.':'')
   +(off?' '+fmt(off)+' row(s) on the sheet name a council outside the register.':'')};}
''')

COV_BODY = (r''' const C=hrtCovRows(),R=C.R,pc=C.N?C.G/C.N*100:0;
''', r''' const C=hrtCovRows(),pc=C.N?C.G/C.N*100:0;
 const H=el('hratCovH');
 if(H)H.textContent=C.wb?'Coverage in the compiled workbook':'Upload coverage for this period';
''')

COV_KP = (r''' el('hratCovK').innerHTML=kp('Register',fmt(C.N),'councils in '+fmt(C.list.length)+' district'
   +(C.list.length===1?'':'s')+(C.dv||C.dd?' in scope':''))
  +kp('Received',fmt(C.G),pc.toFixed(1)+'% of that register')
  +kp('Awaited',fmt(C.N-C.G),'no row on this period&rsquo;s sheet')
  +kp('Rows in view',fmt(hrtView().length),C.off?fmt(C.off)+' outside the register':'all matched');
 el('hratCovNote').innerHTML='Measured against the '+fmt(R.n)+' union councils on the HRA card&rsquo;s own '
  +'roster ('+fmt(Object.keys(R.byDist).length)+' districts). A council counts as received when this '
  +'period&rsquo;s sheet carries its UC code - or its district and UC name when the code is blank.'
  +(C.dv||C.dd?' Scope: <b>'+esc(C.dd||C.dv)+'</b>.':'')
  +(C.off?' '+fmt(C.off)+' row(s) on the sheet name a council outside the register.':'');
''', r''' el('hratCovK').innerHTML=kp(C.wb?'In the workbook':'Register',fmt(C.N),'councils in '
   +fmt(C.list.length)+' district'+(C.list.length===1?'':'s')+(C.dv||C.dd?' in scope':''))
  +kp('Received',fmt(C.G),pc.toFixed(1)+'% of that register')
  +kp('Awaited',fmt(C.N-C.G),C.wb?'nothing owed &mdash; the workbook is the register'
   :'no row on this period&rsquo;s sheet')
  +(C.wb?kp('Rows in the workbook',fmt(C.G),'one row a council, nothing outside it')
   :kp('Rows in view',fmt(hrtView().length),C.off?fmt(C.off)+' outside the register':'all matched'));
 el('hratCovNote').innerHTML=C.note;
''')

PAINT = (r'''function hrtPaint(V){hrtAll=V;hrtTable(V);hrtKpi(V);hrtBadge();hrvRep(V);}
''', r'''function hrtPaint(V){hrtAll=V;hrtTable(V);hrtKpi(V);hrtBadge();hrvRep();}
''')

REPORT_HEAD = (r'''function hrvRep(V){
 const box=el('hrvRep');if(!box)return;
 const D=hrvRepData(V||hrtVals()),B=D.band,tot=D.comp.length;
 const scope=(D.dv||D.dd?[(D.dv||'All divisions'),(D.dd||'All districts')].join(' / ')
  :'All divisions and districts')+' \u00b7 '+D.per
  +(D.n?' \u00b7 '+fmt(D.n)+' of '+fmt(hrtRows.length)+' councils':'');
''', r'''// The findings card and the deck follow the source the "HRA at a glance" picker names, like every
// chart above them: this browser's sheet, or the payload's own roll-up for a published round.
// hrvRepData() scores the sheet; hrvRepFromX() reads the round's roll-ups without re-scoring it.
function hrvRep(){
 const P=(el('hrvPer')&&hrvPer())||'pub';
 _HRVRD=(P==='pub'||P.indexOf('rnd:')===0)?hrvRepFromX(hrvData()):hrvRepData(hrtVals());
 hrvRepDraw(_HRVRD);}
function hrvRepFromX(X){
 const per=X.per||{pub:true,lbl:'published reading'},D=(typeof HRA!=='undefined'&&HRA.d)||[],
  bt=X.bt||[0,0,0,0],ann=X.ann||[],inds=X.ind||[],blks=X.blocks||[],sorted=X.sorted||[],rep=X.rep||{};
 const nm=function(i){return i==null?'(no district)':DNAME(D[i]);};
 const comp=[],districts={},blocks={};
 let sum=0,nb=0;
 sorted.forEach(function(x){comp.push({r:{C:x.u,B:nm(x.d)},p:x.p/100,b:x.b});});
 ann.forEach(function(o,i){if(!o.n)return;
  districts[nm(i)]={n:o.nb,sum:o.sum/100,hi:o.b[2],lo:o.b[0]};
  sum+=o.sum;nb+=o.nb;});
 HRVBK.forEach(function(x,i){const b=blks[i];if(!b||!b.pos)return;
  blocks[i+1]={name:b.l,got:b.got,k:b.pos/3,ach:b.p};});
 return {n:X.n||0,dv:X.sdv,dd:X.sdd,per:per.lbl,tot:per.rows||X.n||0,
  slug:(X.pub?'published-'+HRA.asof:('round-'+X.asof)).replace(/[^A-Za-z0-9-]+/g,'_'),
  band:bt.slice(0,3),comp:comp,over:bt[3]||0,other:0,
  districts:districts,blocks:blocks,inds:inds.map(function(o){
   return {name:o.nm,blk:o.blk,k:o.ap,blank:0,got:o.got,ach:o.ach};}),
  textCols:{},offCols:{},dupe:0,nocode:0,
  blanks:rep.blanks||0,full:rep.full||0,marked:rep.marked||0,none:rep.none||0,
  mean:nb?sum/nb:null,wb:true,
  srcTxt:'the HRA workbook compiled into the dashboard',
  exNote:(bt[3]?fmt(bt[3])+' council(s) are carried as Excluded: their sheet earns marks in a block '
   +'beyond that block&rsquo;s own maximum, or the sheet itself labels them excluded, so no percentage '
   +'can be formed. They are counted in the KPIs on this card and left out of every share, average '
   +'and district score above, exactly as on the HRA at a glance charts.':'')};}
function hrvRepDraw(D){
 const box=el('hrvRep');if(!box)return;
 const B=D.band,tot=D.comp.length;
 const scope=(D.dv||D.dd?[(D.dv||'All divisions'),(D.dd||'All districts')].join(' / ')
  :'All divisions and districts')+' \u00b7 '+D.per
  +(D.n?' \u00b7 '+fmt(D.n)+' of '+fmt(D.tot)+' councils':'');
''')

REPORT_EMPTY = (r''' if(!D.n){box.innerHTML='<div class="hint" style="margin:0">This period is empty in this browser, so '
  +'there is nothing to read yet. Import a card or seed the sheet above.</div>';_HRVRT='';return;}
''', r''' if(!D.n){box.innerHTML='<div class="hint" style="margin:0">'
  +(D.wb?'No council in the selected division or district carries a reading in this round.'
   :'This period is empty in this browser, so there is nothing to read yet. Import a card or seed '
    +'the sheet above.')+'</div>';_HRVRT='';return;}
''')

MIX_KPI = (r'''  +(ex?' (the KPI row above counts every marked row, including the '+fmt(ex)
   +' left out below)':'')+'. Mean overall score '+pc(D.mean)+'. The card\u2019s axis runs the other way: '+HRAT.band.hi
''', r'''  +(ex&&!D.wb?' (the KPI row above counts every marked row, including the '+fmt(ex)
   +' left out below)':'')+'. Mean overall score '+pc(D.mean)+'. The card\u2019s axis runs the other way: '+HRAT.band.hi
''')

EX_NOTE = (r''' if(ex)F.push({h:'Rows the card cannot compare.',t:fmt(D.over)+' marked row(s) score above 100% of '
''', r''' if(ex)F.push({h:'Rows the card cannot compare.',t:D.exNote||(fmt(D.over)+' marked row(s) score above 100% of '
''')

EX_NOTE2 = (r'''  +'Complete them and re-import or edit them in place.'});
''', r'''  +'Complete them and re-import or edit them in place.')});
''')

HEADER = (r'''  +' from the sheet held in this browser.\n';
''', r'''  +' from '+(D.srcTxt||'the sheet held in this browser')+'.\n';
''')

NOTE = (r'''  +'\n\nNote: this report reads only the cells on this sheet. It does not verify them against the UC '
''', r'''  +'\n\nNote: this report reads only '+(D.wb?'the rows of that compiled workbook':'the cells on this sheet')
  +'. It does not verify them against the UC '
''')

SAVE_NAME = (r''' a.href=u;a.download='HRA_findings_'+hrtSlug()+'.txt';
''', r''' a.href=u;a.download='HRA_findings_'+((_HRVRD&&_HRVRD.slug)||hrtSlug())+'.txt';
''')

RT_DECL = (r'''let _HRVRT='';
''', r'''let _HRVRT='',_HRVRD=null;
''')

PARTS = (r''' const dm=/^Generated (.*?) from the sheet/.exec(lines[2]||'');
''', r''' const dm=/^Generated (.*?) from (.*?)\.?\s*$/.exec(lines[2]||'');
''')

PARTS_RET = (r''' return {per:per,scope:scope,date:dm?dm[1]:'',F:F,R:R,note:nt};
''', r''' return {per:per,scope:scope,date:dm?dm[1]:'',src:dm?dm[2]:'the sheet held in this browser',
  F:F,R:R,note:nt};
''')

DECK_D = (r''' const D=hrvRepData(hrtVals()),B=D.band,tot=D.comp.length;
''', r''' const D=_HRVRD||hrvRepData(hrtVals()),B=D.band,tot=D.comp.length;
''')

COVER = (r'''  s.addText('HRA COMPILATION \u00b7 '+X.per.toUpperCase(),{x:0.8,y:1.0,w:11.7,h:0.4,fontFace:F,
''', r'''  s.addText('HRA FINDINGS \u00b7 '+X.per.toUpperCase(),{x:0.8,y:1.0,w:11.7,h:0.4,fontFace:F,
''')

COVER_SRC = (r'''  s.addText([{text:'Compiled  ',options:{bold:true,color:'A5F3FC'}},
   {text:(X.date||'today')+' from the sheet held in this browser',options:{color:'FFFFFF'}}],
   {x:0.8,y:4.0,w:11.7,h:0.4,fontFace:F,fontSize:13});
  s.addText('Every figure is a roll-up of the cells on this sheet. A high percentage is a safe council \u2014 '
''', r'''  s.addText([{text:'Compiled  ',options:{bold:true,color:'A5F3FC'}},
   {text:(X.date||'today'),options:{color:'FFFFFF'}}],
   {x:0.8,y:3.95,w:11.7,h:0.4,fontFace:F,fontSize:13});
  s.addText([{text:'Read from  ',options:{bold:true,color:'A5F3FC'}},
   {text:X.src,options:{color:'FFFFFF'}}],
   {x:0.8,y:4.35,w:11.7,h:0.4,fontFace:F,fontSize:13});
  s.addText('Every figure is a roll-up of '+X.src+'. A high percentage is a safe council \u2014 '
''')

COVER_LEAD = (r'''  s.addText('What the '+fmt(D.n)+' compiled councils in scope say, and what to do before the next round',
''', r'''  s.addText('What the '+fmt(D.n)+' councils in scope say, and what to do before the next round',
''')

PPTX_NAME = (r'''  await saveDeck(pptx,'HRA_findings_'+hrtSlug()+'.pptx');
''', r'''  await saveDeck(pptx,'HRA_findings_'+((_HRVRD&&_HRVRD.slug)||hrtSlug())+'.pptx');
''')

TXT_FALLBACK = (r'''  hrvRepTxt();
''', r'''  hrvRepSave();
''')

RENDER_EMPTY = (r'''  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  hrvMig(X);
''', r'''  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  hrvMig(X);
  hrvRep();
''')

RENDER_CALL = (r''' hrvMap(X);
 hrvTable(X);
''', r''' hrvMap(X);
 hrvTable(X);
 hrvRep();
''')

DATA_REP = (r''' _HRVD={k:K,per:hrvPerMeta(P,CP),pub:PUB,rnd:!!RND,asof:asof,
''', r''' // Completeness for the findings card: a row counts as full when all 27 answers are there
 let rFull=0,rMark=0,rNone=0,rBlank=0;
 U.forEach(function(r){const ss=r[8]||[];let a=0;
  ss.forEach(function(v){if(v!=null&&v>=0)a++;});
  if(a===HRA.k.length)rFull++;if(a)rMark++;else rNone++;rBlank+=HRA.k.length-a;});
 _HRVD={k:K,per:hrvPerMeta(P,CP),pub:PUB,rnd:!!RND,asof:asof,
  rep:{full:rFull,marked:rMark,none:rNone,blanks:rBlank},
''')

TITLE = (r'''title="A short PowerPoint deck built from the sheet compiled above and the division / district filter on it"''',
         r'''title="A short PowerPoint deck built from the source selected under HRA at a glance, through the division / district filter on it"''')

FOOT = (r'''<div class="cap" id="hrvRepFoot">Read from the cells on this sheet only, and from the filter above it.''',
        r'''<div class="cap" id="hrvRepFoot">Read from the source picked under HRA at a glance, through the division / district filter on it.''')

REP_TOT = (r''' const out={n:n,dv:dv,dd:dd,slug:hrtSlug(),per:(P[2]||'Campaign')+' '+P[0]+'-'+P[1],
''', r''' const out={n:n,dv:dv,dd:dd,slug:hrtSlug(),tot:hrtRows.length,
  per:(P[2]||'Campaign')+' '+P[0]+'-'+P[1],
''')

# The migration chart compared the earlier round's matched councils with the later round's whole
# register, so a reader saw 71 High in May where the round itself has 87. Each bar now carries its
# own round's register (scoped like the rest of the card), and the caption says so.
MIG_FULL = (r'''  const old={};HRA.may.u.forEach(function(r){old[String(r[2])]={b:r[6]};});
  const t={imp:0,wor:0,same:0,newu:0,nc:0},
''', r'''  const old={},mb=[0,0,0,0];
  HRA.may.u.forEach(function(r){old[String(r[2])]={b:r[6]};
   const o=ann[ix[D[r[0]]]];if(o&&inS(o))mb[r[6]]++;});
  const t={imp:0,wor:0,same:0,newu:0,nc:0},
''')

MIG_OBJ = (r'''  mig={tot:t,by:by,mx:mx,lbl:HRA.may.lbl||'the earlier round'};''',
           r'''  mig={tot:t,by:by,mx:mx,oldB:mb,lbl:HRA.may.lbl||'the earlier round'};''')

MIG_OLDB = (r''' const oldB=[0,1,2,3].map(function(i){return mx[0][i]+mx[1][i]+mx[2][i]+mx[3][i];});''',
            r''' const oldB=(M.oldB&&M.oldB.length===4)?M.oldB
  :[0,1,2,3].map(function(i){return mx[0][i]+mx[1][i]+mx[2][i]+mx[3][i];});''')

MIG_CAP = (r''' el('chrv4').innerHTML='The same two rounds the table is cut from, as counts: '+fmt(oldB[2])
  +' High-Risk councils in '+esc(oldLbl)+' against '+fmt(colS[2])+' in '+esc(newLbl)
  +'. The bars are absolute counts, so a round that assessed more councils shows a taller bar.';
''', r''' el('chrv4').innerHTML='Each bar is a round&rsquo;s own register, band by band: '+fmt(oldB[2])
  +' High-Risk councils in '+esc(oldLbl)+' against '+fmt(colS[2])+' in '+esc(newLbl)
  +'. The bars are absolute counts, so a round that assessed more councils shows a taller bar. '
  +'The table beside this chart follows only the '+fmt(M.tot.imp+M.tot.wor+M.tot.same+M.tot.nc)
  +' councils present in both rounds.';
''')

MIG_TBL = (r''' el('chrvMv').innerHTML='Each cell counts councils; the diagonal (bold) held its band. '
''', r''' el('chrvMv').innerHTML='Rows count only the councils present in both rounds; the last row is new to '
  +esc(newLbl)+'. Each cell counts councils; the diagonal (bold) held its band. '
''')

EDITS = [
    ('periods', PERIODS),
    ('slug label', SLUGLBL),
    ('glance picker', PERFILL),
    ('period auto', REFRESH),
    ('coverage heading', COV_HEAD),
    ('coverage rows', COVROWS),
    ('coverage return', COV_RETURN),
    ('coverage body', COV_BODY),
    ('coverage kpis', COV_KP),
    ('paint', PAINT),
    ('report dispatch', REPORT_HEAD),
    ('report total', REP_TOT),
    ('report empty', REPORT_EMPTY),
    ('mix kpi note', MIX_KPI),
    ('ex note', EX_NOTE),
    ('ex note 2', EX_NOTE2),
    ('report header', HEADER),
    ('report note', NOTE),
    ('save name', SAVE_NAME),
    ('report state', RT_DECL),
    ('parts parse', PARTS),
    ('parts return', PARTS_RET),
    ('deck data', DECK_D),
    ('deck cover', COVER),
    ('deck source', COVER_SRC),
    ('deck lead', COVER_LEAD),
    ('deck name', PPTX_NAME),
    ('txt fallback', TXT_FALLBACK),
    ('render empty', RENDER_EMPTY),
    ('render call', RENDER_CALL),
    ('data rep', DATA_REP),
    ('button title', TITLE),
    ('card footer', FOOT),
    ('mig full band', MIG_FULL),
    ('mig oldB', MIG_OBJ),
    ('mig bar source', MIG_OLDB),
    ('mig caption', MIG_CAP),
    ('mig table caption', MIG_TBL),
]


def apply(text, pairs, strict=True):
    for name, (old, new) in pairs:
        o, n = nl(old), nl(new)
        c = text.count(o)
        if c != 1:
            raise AssertionError('%s: anchor found %d times (want 1)' % (name, c))
        text = text.replace(o, n, 1)
    return text


def unapply(text, pairs):
    for name, (old, new) in reversed(pairs):
        o, n = nl(old), nl(new)
        c = text.count(n)
        if c != 1:
            raise AssertionError('%s: patched text found %d times (want 1)' % (name, c))
        text = text.replace(n, o, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    pairs = EDITS
    for v in vs:
        v.require('id="hrvHint"' in v.text, 'HRA visuals are not applied in %s' % v.rel)
        v.text = unapply(v.text, pairs) if a.unpatch else apply(v.text, pairs)
    if all(not v.changed for v in vs):
        print('NO CHANGE')
        return 0
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    for v in vs:
        print('%s %-42s %+8d chars' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel, v.delta()))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants(vs)
    print('WROTE %d variants' % sum(1 for v in vs if v.changed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
