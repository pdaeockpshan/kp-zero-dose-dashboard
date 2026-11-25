# -*- coding: utf-8 -*-
"""HRA card: two published rounds, the Excluded band, and the movement between them.

The owner asked, 25-Nov-2026: "i have downloaded compiled HRA file for MAY and SEPTEMBER 2026
kindly incorporate it in dashboard, replace for SEPTEMBER data already there as this one is final
and cleaned. Based on HRA files in HRA section kindly insert District wise table of number of UCs
risk category wise, ideal visualizations with charts, graphs and KP map can be used. Also
Incorporate identified risk wise UCs in other sections of dashboard and reports."

The payload (const HRA) now carries the province compilation: the Sep 2026 sheet at the top level
and the May 2026 sheet under `.may`, both read by extract_hra.py. This module teaches the card to
read either, to keep the councils whose sheet cannot be banded out of every share and average
(band 3, "Excluded"), and to draw the movement between the two rounds. The district roll-up and
the CSV gain the Excluded column and the better / worse / new counts, and the high-risk district
focus stops counting an Excluded council as Low Risk.

Rules kept:
  * The card's own axis, never the combined UC risk score: 79%+ is Low Risk, under 60% is High.
  * An Excluded council is in the count and in no share: its sheet earned marks in a block beyond
    that block's own maximum, so its percentage has no readable denominator.
  * Two rounds are never blended: every figure is cut from the round the picker names.
  * No invented data: every number is a roll-up of HRA.u / HRA.may.u.

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

HTML_CARD = (r'''<div class="card"><div class="tblhdr"><h3 style="margin:0">Council scores against the card&rsquo;s thresholds</h3></div><div id="hrv2"></div><div class="cap" id="chrv2"></div></div>
</div>
''', r'''<div class="card"><div class="tblhdr"><h3 style="margin:0">Council scores against the card&rsquo;s thresholds</h3></div><div id="hrv2"></div><div class="cap" id="chrv2"></div></div>
</div>
<div class="grid2" id="hrvMigWrap" style="margin-bottom:16px">
<div class="card"><div class="tblhdr"><h3 style="margin:0">Band mix across the two rounds</h3></div><div id="hrv4"></div><div class="cap" id="chrv4"></div></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">Where each council moved</h3></div><div style="overflow:auto;max-height:420px"><table class="shtbl" id="hrvMv"></table></div><div class="cap" id="chrvMv"></div></div>
</div>
''')

PERFILL = (r''' const keep=s.value||'pub',opts=[['pub','Published reading \u00b7 '+hrvD(HRA.asof)+' \u00b7 '
  +fmt(HRA.n)+' councils']];
''', r''' const keep=s.value||'pub';
 const opts=[['pub',(HRA.lbl||'Published')+' reading \u00b7 '+hrvD(HRA.asof)+' \u00b7 '
  +fmt(HRA.n)+' councils']];
 (HRA.rd||[]).slice(1).forEach(function(r){
  opts.push(['rnd:'+r[0],r[1]+' round \u00b7 '+hrvD(r[2])+' \u00b7 '+fmt(r[3])+' councils']);});
''')

PERMETA = (r'''function hrvPerMeta(P,CP){
 const pub=P==='pub';
 if(pub)return {v:'pub',pub:true,slug:'',lbl:'published reading',date:hrvD(HRA.asof),
  asof:HRA.asof,rows:HRA.n,skip:0,off:0,blank:0,dupe:0};
 return CP?CP.meta:{v:P,pub:false,slug:P,lbl:hrvSlugLbl(P),date:P,asof:P,
  rows:0,skip:0,off:0,blank:0,dupe:0};}
''', r'''function hrvRound(P){
 const id=String(P).replace(/^rnd:/,'');
 if(typeof HRA==='undefined'||!HRA||!HRA.may||!HRA.rd||!HRA.rd[1])return null;
 return HRA.rd[1][0]===id?HRA.may:null;}
function hrvPerMeta(P,CP){
 const pub=P==='pub';
 if(pub)return {v:'pub',pub:true,slug:'',lbl:(HRA.lbl||'published')+' reading',date:hrvD(HRA.asof),
  asof:HRA.asof,rows:HRA.n,skip:0,off:0,blank:0,dupe:0};
 const R=hrvRound(P);
 if(R)return {v:P,pub:false,rnd:true,slug:'',lbl:(R.lbl||'earlier')+' round',
  date:hrvD(R.asof),asof:R.asof,rows:R.n,skip:0,off:0,blank:0,dupe:0};
 return CP?CP.meta:{v:P,pub:false,slug:P,lbl:hrvSlugLbl(P),date:P,asof:P,
  rows:0,skip:0,off:0,blank:0,dupe:0};}
''')

DATA_OLD = r'''function hrvData(){
 const SC=hrvScope(),P=hrvPer(),K=SC.k+'\u0001'+P,PUB=P==='pub';
 if(_HRVD&&_HRVD.k===K)return _HRVD;
 const CP=PUB?null:hrvCompiled(P);
 const U0=PUB?((typeof HRA!=='undefined'&&HRA.u)||[]):(CP?CP.U:[]),
  D=(typeof HRA!=='undefined'&&HRA.d)||[];
 if(!U0.length){_HRVD={n:0,k:K,per:hrvPerMeta(P,CP),empty:true};return _HRVD;}
 const HI=HRA.thr[0],LO=HRA.thr[1];
 const kg={};(typeof KPGEO!=='undefined'?KPGEO.d:[]).forEach(function(p){kg[p.c]=p.v;});
 const dvOf=function(c){
  const k=kg[c]||(typeof D2DV!=='undefined'?(D2DV[c]||null):null)||'Other';
  return HRV_DV[k]||k;};
 const ix={};D.forEach(function(c,i){ix[c]=i;});
 const ann=D.map(function(c){return {c:c,dv:dvOf(c),n:0,b:[0,0,0],oct:0,ach:0,pos:0,sum:0,vm:0};});
 const hvS=function(a,b){a=HRTN(a);b=HRTN(b);
  return a===b||a.indexOf(b+' ')===0||b.indexOf(a+' ')===0;};
 const inS=function(o){return (!SC.dv||hvS(o.dv,SC.dv))
  &&(!SC.dd||hvS(o.c,SC.dd)||hvS(DNAME(o.c),SC.dd));};
 const U=(!SC.dv&&!SC.dd)?U0:U0.filter(function(r){const o=ann[ix[D[r[0]]]];
  return !!o&&inS(o);});
 const div={};
 U.forEach(function(r){
  const o=ann[ix[D[r[0]]]];if(!o)return;
  const b=r[6];
  o.n++;o.b[b]++;o.ach+=r[3];o.pos+=r[4];o.sum+=r[5];o.vm|=(1<<r[7]);
  if(r[7]===0)o.oct++;
  const k=o.dv;
  if(!div[k])div[k]={n:0,b:[0,0,0]};
  div[k].n++;div[k].b[b]++;});
 ann.forEach(function(o){
  o.hi=o.n?o.b[2]/o.n*100:null;
  o.p=o.pos?o.ach/o.pos*100:null;
  o.m=o.n?o.sum/o.n:null;
  o.dates=hrvDates(o.vm).join(' & ');});
 const ind=HRA.k.map(function(k,i){
  let ap=0,got=0,z=0;
  U.forEach(function(r){const s=r[8][i];
   if(s==null||s<0)return;
   ap++;got+=s;if(s===0)z++;});
  return {i:i,nm:k[1],blk:k[0],rule:k[2],ap:ap,got:got,z:z,b:hrvBlk(k[0]),
   ach:ap?got/(3*ap)*100:null,zs:ap?z/ap*100:null};});
 const blocks=HRVBK.map(function(x,i){return {c:x.c,l:x.l,got:0,pos:0,p:null};});
 ind.forEach(function(o){blocks[o.b].got+=o.got;blocks[o.b].pos+=3*o.ap;});
 blocks.forEach(function(o){o.p=o.pos?o.got/o.pos*100:null;});
 const scores=U.map(function(r){return r[5];}).filter(function(v){return v!=null;})
  .sort(function(a,b){return a-b;});
 const q=function(f){return scores.length?scores[Math.min(scores.length-1,Math.floor(f*scores.length))]:null;};
 const bt=[0,0,0],vint=[0,0];let achT=0,posT=0;
 U.forEach(function(r){bt[r[6]]++;vint[r[7]]=(vint[r[7]]||0)+1;achT+=r[3];posT+=r[4];});
 _HRVD={k:K,per:hrvPerMeta(P,CP),pub:PUB,scope:!!(SC.dv||SC.dd),sdv:SC.dv,sdd:SC.dd,
  n:U.length,nd:ann.filter(function(o){return o.n;}).length,ann:ann,div:div,
  ind:ind,blocks:blocks,bt:bt,vint:vint,
  hi:HI,lo:LO,achT:achT,posT:posT,
  min:scores.length?scores[0]:null,max:scores.length?scores[scores.length-1]:null,
  med:q(.5),q1:q(.25),q3:q(.75),
  mixed:ann.filter(function(o){return o.n&&(o.vm&1)&&o.vm!==1;}).map(function(o){
   return {c:o.c,old:o.n-o.oct,n:o.n};}),
  sorted:U.map(function(r){return {p:r[5],d:r[0],u:r[1],b:r[6]};})
   .sort(function(a,b){return b.p-a.p;})};
 return _HRVD;}'''

DATA_NEW = r'''function hrvData(){
 const SC=hrvScope(),P=hrvPer(),K=SC.k+'\u0001'+P,PUB=P==='pub';
 if(_HRVD&&_HRVD.k===K)return _HRVD;
 const RND=PUB?null:hrvRound(P);
 const CP=(PUB||RND)?null:hrvCompiled(P);
 const U0=PUB?((typeof HRA!=='undefined'&&HRA.u)||[]):(RND?RND.u:(CP?CP.U:[])),
  D=(typeof HRA!=='undefined'&&HRA.d)||[];
 if(!U0.length){_HRVD={n:0,k:K,per:hrvPerMeta(P,CP),empty:true};return _HRVD;}
 const HI=HRA.thr[0],LO=HRA.thr[1];
 const kg={};(typeof KPGEO!=='undefined'?KPGEO.d:[]).forEach(function(p){kg[p.c]=p.v;});
 const dvOf=function(c){
  const k=kg[c]||(typeof D2DV!=='undefined'?(D2DV[c]||null):null)||'Other';
  return HRV_DV[k]||k;};
 const ix={};D.forEach(function(c,i){ix[c]=i;});
 const ann=D.map(function(c){return {c:c,dv:dvOf(c),n:0,nb:0,b:[0,0,0,0],oct:0,ach:0,pos:0,sum:0,vm:0,mv:null};});
 const hvS=function(a,b){a=HRTN(a);b=HRTN(b);
  return a===b||a.indexOf(b+' ')===0||b.indexOf(a+' ')===0;};
 const inS=function(o){return (!SC.dv||hvS(o.dv,SC.dv))
  &&(!SC.dd||hvS(o.c,SC.dd)||hvS(DNAME(o.c),SC.dd));};
 const U=(!SC.dv&&!SC.dd)?U0:U0.filter(function(r){const o=ann[ix[D[r[0]]]];
  return !!o&&inS(o);});
 const div={};
 U.forEach(function(r){
  const o=ann[ix[D[r[0]]]];if(!o)return;
  const b=r[6]===3?3:(r[6]===2?2:(r[6]===1?1:0));
  o.n++;o.b[b]++;o.vm|=(1<<r[7]);
  if(r[7]===0)o.oct++;
  const k=o.dv;
  if(!div[k])div[k]={n:0,nb:0,b:[0,0,0,0]};
  div[k].n++;div[k].b[b]++;
  // an Excluded council has no readable percentage: it is counted, never shared or averaged
  if(b===3)return;
  div[k].nb++;o.nb++;o.ach+=r[3];o.pos+=r[4];o.sum+=r[5];});
 const RND2=PUB?null:hrvRound(P), asof=RND2?RND2.asof:HRA.asof;
 ann.forEach(function(o){
  o.hi=o.nb?o.b[2]/o.nb*100:null;
  o.p=o.pos?o.ach/o.pos*100:null;
  o.m=o.nb?o.sum/o.nb:null;
  o.dates=hrvD(asof);});
 const ind=HRA.k.map(function(k,i){
  let ap=0,got=0,z=0;
  U.forEach(function(r){const s=r[8][i];
   if(s==null||s<0)return;
   ap++;got+=s;if(s===0)z++;});
  return {i:i,nm:k[1],blk:k[0],rule:k[2],ap:ap,got:got,z:z,b:hrvBlk(k[0]),
   ach:ap?got/(3*ap)*100:null,zs:ap?z/ap*100:null};});
 const blocks=HRVBK.map(function(x,i){return {c:x.c,l:x.l,got:0,pos:0,p:null};});
 ind.forEach(function(o){blocks[o.b].got+=o.got;blocks[o.b].pos+=3*o.ap;});
 blocks.forEach(function(o){o.p=o.pos?o.got/o.pos*100:null;});
 const scores=U.filter(function(r){return r[6]!==3;}).map(function(r){return r[5];})
  .filter(function(v){return v!=null;}).sort(function(a,b){return a-b;});
 const q=function(f){return scores.length?scores[Math.min(scores.length-1,Math.floor(f*scores.length))]:null;};
 const bt=[0,0,0,0],vint=[];let achT=0,posT=0;
 U.forEach(function(r){bt[r[6]]++;vint[r[7]]=(vint[r[7]]||0)+1;
  if(r[6]!==3){achT+=r[3];posT+=r[4];}});
 let mig=null;
 if(PUB&&typeof HRA!=='undefined'&&HRA.may&&HRA.may.u){
  const old={};HRA.may.u.forEach(function(r){old[String(r[2])]={b:r[6]};});
  const t={imp:0,wor:0,same:0,newu:0,nc:0},
   mx=[0,1,2,3,4].map(function(){return [0,0,0,0];}),by={};
  U.forEach(function(r){
   const o=old[String(r[2])],k=D[r[0]],m=by[k]=by[k]||{imp:0,wor:0,same:0,newu:0,nc:0};
   if(!o){t.newu++;m.newu++;mx[4][r[6]]++;return;}
   mx[o.b][r[6]]++;
   if(r[6]===3||o.b===3){t.nc++;m.nc++;return;}
   if(r[6]<o.b){t.imp++;m.imp++;}
   else if(r[6]>o.b){t.wor++;m.wor++;}
   else {t.same++;m.same++;}});
  mig={tot:t,by:by,mx:mx,lbl:HRA.may.lbl||'the earlier round'};
  ann.forEach(function(o){o.mv=by[o.c]||null;});}
 _HRVD={k:K,per:hrvPerMeta(P,CP),pub:PUB,rnd:!!RND,asof:asof,
  scope:!!(SC.dv||SC.dd),sdv:SC.dv,sdd:SC.dd,
  n:U.length,nb:bt[0]+bt[1]+bt[2],nd:ann.filter(function(o){return o.n;}).length,ann:ann,div:div,
  ind:ind,blocks:blocks,bt:bt,vint:vint,
  hi:HI,lo:LO,achT:achT,posT:posT,
  min:scores.length?scores[0]:null,max:scores.length?scores[scores.length-1]:null,
  med:q(.5),q1:q(.25),q3:q(.75),
  mixed:ann.filter(function(o){return o.n&&(o.vm&1)&&o.vm!==1;}).map(function(o){
   return {c:o.c,old:o.n-o.oct,n:o.n};}),
  mig:mig,
  sorted:U.filter(function(r){return r[6]!==3;}).map(function(r){return {p:r[5],d:r[0],u:r[1],b:r[6]};})
   .sort(function(a,b){return b.p-a.p;})};
 return _HRVD;}'''

RENDER_SRC = (r''' if(s)s.textContent=P.pub?'Read from the dashboard payload: one province reading dated '+hrvD(HRA.asof)
  :'Read from the sheet this browser holds for '+hrvSlugLbl(P.slug)+', scored by the card itself';
''', r''' if(s)s.textContent=P.pub?'Read from the dashboard payload: the '+(HRA.lbl||'province')+' reading dated '+hrvD(HRA.asof)
  :(P.rnd?'Read from the dashboard payload: the '+P.lbl+' dated '+P.date
  :'Read from the sheet this browser holds for '+hrvSlugLbl(P.slug)+', scored by the card itself');
''')

RENDER_CALL = (r''' hrvCurve(X);
 hrvInd(X);
''', r''' hrvCurve(X);
 hrvMig(X);
 hrvInd(X);
''')

RENDER_EMPTY = (r'''  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  _HRVMAP=null;''', r'''  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  hrvMig(X);
  _HRVMAP=null;''')

HINT_OLD = r'''function hrvHint(X){
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
  +'card above: that sheet belongs to its own year, month and campaign.';}'''

HINT_NEW = r'''function hrvHint(X){
 const dvn=Object.keys(X.div).length,P=X.per||{pub:true,lbl:'published reading'};
 const lead=(X.scope?'<b>'+esc(X.sdv||'All divisions')+(X.sdd?' / '+esc(X.sdd):'')
  +' selected:</b> ':'')+'<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' district'
  +(X.nd===1?'':'s')+' and '+dvn+' division'+(dvn===1?'':'s');
 if(!P.pub&&!P.rnd){
  el('hrvHint').innerHTML=lead+' compiled for '+esc(P.lbl)+'.</b> The scores are read from the copies '
   +'of the card this browser holds for that period, through the card&rsquo;s own formulas. On the '
   +'card&rsquo;s axis '+fmt(X.bt[0])+' are Low Risk, '+fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])
   +' High ('+(X.n?(X.bt[2]/X.n*100).toFixed(1):'-')+'%). Marks earned counts an indicator only where the sheet '
   +'carries an answer, so a half-filled row is graded over the marks it charged. '
   +(P.skip?'<b>'+fmt(P.skip)+' row(s)</b> on the sheet are not charted: '
     +(P.off?fmt(P.off)+' name a district outside the register':'')
     +(P.off&&P.blank?' and ':'')+(P.blank?fmt(P.blank)+' carry no answer yet':'')+'. ':'')
   +'This is the compiled sheet, not the published province reading, and the two are never blended.';
  return;}
 const nb=X.nb||0,hp=nb?(X.bt[2]/nb*100).toFixed(1):'-',M=X.mig&&X.mig.tot;
 el('hrvHint').innerHTML=lead+' carry the '+(P.rnd?esc(P.lbl):esc((HRA.lbl||'province')+' HRA reading'))
  +' dated '+esc(hrvD(X.asof))+'.</b> On the card&rsquo;s own axis '+fmt(X.bt[0])+' are Low Risk, '
  +fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])+' High ('+hp+'% of the '+fmt(nb)+' councils with a '
  +'readable band)'
  +(X.bt[3]?'; <b>'+fmt(X.bt[3])+' are carried as Excluded</b> &mdash; their sheet earned marks in a '
   +'block beyond that block&rsquo;s own maximum, so no percentage can be formed and they sit in no band, '
   +'share, average or mean on this card':'')+'. A high percentage here is a safe council &mdash; this is '
  +'not the combined UC risk score used on the Cross-cutting pages, and the two are never blended. '
  +(M&&!P.rnd?'<b>Movement since '+esc(X.mig.lbl)+':</b> '+fmt(M.imp)+' councils moved to a lower-risk '
   +'band, '+fmt(M.wor)+' to a higher one and '+fmt(M.same)+' held; '+fmt(M.newu)+' appear for the first '
   +'time'+(M.nc?'; '+fmt(M.nc)+' carry no readable band in one of the two rounds':'')+'. ':'')
  +(P.rnd?'This is the earlier round, kept for comparison; the published reading is the later one. ':'')
  +'Every band is recomputed from the row&rsquo;s own 27 answers, not copied from the sheet&rsquo;s printed '
  +'Risk label. The '+HRA.nx.length+' criteria the card leaves unscored are not in these figures, and '
  +'neither is anything typed into the card above.';}'''

BAND_ROWS = (r''' const rows=Object.keys(X.div).map(function(k){
  const o=X.div[k];return {k:k,n:o.n,b:o.b,hi:o.b[2]/o.n*100};})
  .sort(function(a,b){return a.hi-b.hi;});
''', r''' const rows=Object.keys(X.div).map(function(k){
  const o=X.div[k];return {k:k,n:o.n,b:o.b,hi:o.nb?o.b[2]/o.nb*100:null};})
  .sort(function(a,b){return (a.hi==null?-1:a.hi)-(b.hi==null?-1:b.hi);});
''')

BAND_SERIES = (r'''  series:[0,1,2].map(function(i){return {name:HRVB[i].l,color:HRVB[i].c,
   data:rows.map(function(r){return r.b[i];})};})});
''', r'''  series:[0,1,2,3].map(function(i){return {name:i===3?'Excluded (no readable band)':HRVB[i].l,
   color:i===3?'#94a3b8':HRVB[i].c,
   data:rows.map(function(r){return r.b[i];})};})});
''')

BAND_CAP = (r''' const top3=desc.slice(0,3).map(function(r){return r.k+' '+r.hi.toFixed(1)+'%';}).join(', ');
''', r''' const top3=desc.slice(0,3).map(function(r){return r.k+' '+(r.hi==null?'-':r.hi.toFixed(1)+'%');}).join(', ');
''')

BAND_CAP2 = (r''' el('chrv1').innerHTML='Each bar is a division&rsquo;s councils split by the band their own score '
  +'falls in. <b>High-Risk share: '+top3+'.</b> '
''', r''' el('chrv1').innerHTML='Each bar is a division&rsquo;s councils split by the band their own score '
  +'falls in; the shares are of the bandable councils, and grey are the councils whose sheet cannot be '
  +'banded. <b>High-Risk share: '+top3+'.</b> '
''')

CURVE_CAP = (r''' el('chrv2').innerHTML='Every council is a point, ranked by its own score, so the width of each shaded '
  +'stretch is how many councils fall in it. Half score above '+X.med.toFixed(1)+'% and a quarter above '
  +X.q3.toFixed(1)+'%. Green is the Low Risk range ('+X.hi+'% and above: '+fmt(X.bt[0])
  +' councils), amber Medium ('+X.lo+'% to '+X.hi+'%: '+fmt(X.bt[1])+') and red below '+X.lo+'% ('
  +fmt(X.bt[2])+' councils). Nothing is binned, so a council just under or over a cut-off is not hidden '
  +'by a wider bucket.';}
''', r''' el('chrv2').innerHTML='Every council is a point, ranked by its own score, so the width of each shaded '
  +'stretch is how many councils fall in it. Half score above '+X.med.toFixed(1)+'% and a quarter above '
  +X.q3.toFixed(1)+'%. Green is the Low Risk range ('+X.hi+'% and above: '+fmt(X.bt[0])
  +' councils), amber Medium ('+X.lo+'% to '+X.hi+'%: '+fmt(X.bt[1])+') and red below '+X.lo+'% ('
  +fmt(X.bt[2])+' councils). Nothing is binned, so a council just under or over a cut-off is not hidden '
  +'by a wider bucket.'
  +(X.bt[3]?' The '+fmt(X.bt[3])+' Excluded councils are not plotted: their score has no readable '
   +'denominator.':'');}
''')

MAP_SW = (r''' const sw=by['SWAT']||null;
 const src=function(c){return by[c]||(c==='BAR SWAT'?sw:null);};
''', r''' const sw=by['SWAT']||null,hasB=!!(by['BAR SWAT']&&by['BAR SWAT'].n);
 const src=function(c){return by[c]||(c==='BAR SWAT'?sw:null);};
''')

MAP_TIP = (r'''  return DNAME(c)+'\n'+o2.dv+' division\n'+fmt(o2.n)+' councils: '+fmt(o2.b[0])+' Low / '
   +fmt(o2.b[1])+' Medium / '+fmt(o2.b[2])+' High'
''', r'''  return DNAME(c)+'\n'+o2.dv+' division\n'+fmt(o2.n)+' councils: '+fmt(o2.b[0])+' Low / '
   +fmt(o2.b[1])+' Medium / '+fmt(o2.b[2])+' High'+(o2.b[3]?' / '+fmt(o2.b[3])+' excluded':'')
''')

MAP_NOSHEET = (r'''   :(X.pub?'no sheet':'no row this period')]]),
''', r'''   :((X.pub||X.rnd)?'no sheet this round':'no row this period')]]),
''')

MAP_TIP2 = (r'''  if(!o2||!o2.n)return DNAME(c)+(X.scope?'\noutside the selected division / district'
   :(X.pub?'\nno HRA sheet':'\nno compiled row for this period'));
''', r'''  if(!o2||!o2.n)return DNAME(c)+(X.scope?'\noutside the selected division / district'
   :((X.pub||X.rnd)?'\nno HRA row for this round':'\nno compiled row for this period'));
''')

MAP_CAP = (r'''  +' no High-Risk council, but that is not the same as '
  +'a clean district'+(ex?' &mdash; '+DNAME(ex.c)+' has none and still earns only '+ex.p.toFixed(1)
   +'% of its marks':'')+', which is why the measure can be switched. Bar Swat is drawn with the Swat '
  +'reading because it has no HRA sheet of its own; boundaries are the dashboard&rsquo;s KP district '
  +'shapefile and every label sits inside its own district.';
''', r'''  +' no High-Risk council, but that is not the same as '
  +'a clean district'+(ex?' &mdash; '+DNAME(ex.c)+' has none and still earns only '+ex.p.toFixed(1)
   +'% of its marks':'')+', which is why the measure can be switched. '
  +(hasB?'':'Bar Swat is drawn with the Swat reading because it has no row in this round; ')
  +'Boundaries are the dashboard&rsquo;s KP district shapefile and every label sits inside its own district.';
''')

MAP_BASE = (r'''   +(X.pub?HRA.asof:(PM.slug||'compiled'))).replace(/[^A-Za-z0-9]+/g,'_')+'_'
''', r'''   +((X.pub||X.rnd)?X.asof:(PM.slug||'compiled'))).replace(/[^A-Za-z0-9]+/g,'_')+'_'
''')

MAP_LEGEND = (r'''  L:lg.concat([['#f1f5f9',X.scope?'not in the selected division / district'
   :(X.pub?'no sheet':'no row this period')]]),
''', r'''  L:lg.concat([['#f1f5f9',X.scope?'not in the selected division / district'
   :((X.pub||X.rnd)?'no sheet this round':'no row this period')]]),
''')

TABLE_OLD = r'''function hrvTable(X){
 const t=el('hrvTbl');if(!t)return;
 const rows=X.ann.filter(function(o){return o.n;}).sort(function(a,b){return (b.hi||0)-(a.hi||0);});
 const td=function(o){return '<tr><td>'+esc(o.dv)+'</td><td>'+esc(DNAME(o.c))+'</td><td>'+fmt(o.n)
  +'</td><td>'+fmt(o.b[0])+'</td><td>'+fmt(o.b[1])+'</td><td>'+fmt(o.b[2])+'</td><td>'
  +(o.hi==null?'-':o.hi.toFixed(1))+'</td><td>'+(o.p==null?'-':o.p.toFixed(1))+'</td><td>'
  +(o.m==null?'-':o.m.toFixed(1))+'</td></tr>';};
 t.innerHTML='<thead><tr><th>Division</th><th>District</th><th>Councils</th><th>Low Risk</th>'
  +'<th>Medium</th><th>High</th><th>High-Risk %</th><th>Marks earned %</th><th>Mean score %</th>'
  +'</tr></thead><tbody>'+(rows.length?rows.map(td).join('')
  :'<tr><td colspan="9" class="cnt">No HRA reading for the selected division and district.</td></tr>')
  +'</tbody>'+(rows.length?'<tfoot><tr class="tot"><td>All in scope</td><td>'+fmt(X.nd)
  +(X.nd===1?' district':' districts')+'</td><td>'+fmt(X.n)+'</td><td>'+fmt(X.bt[0])+'</td><td>'+fmt(X.bt[1])+'</td><td>'
  +fmt(X.bt[2])+'</td><td>'+(X.n?(X.bt[2]/X.n*100).toFixed(1):'-')+'</td><td>'
  +(X.posT?(X.achT/X.posT*100).toFixed(1):'-')+'</td><td>'
  +(X.n?((X.ann.reduce(function(s,o){return s+o.sum;},0))/X.n).toFixed(1):'-')+'</td></tr></tfoot>':'');}'''

TABLE_NEW = r'''function hrvTable(X){
 const t=el('hrvTbl');if(!t)return;
 const rows=X.ann.filter(function(o){return o.n;}).sort(function(a,b){return (b.hi||0)-(a.hi||0);});
 const mv=function(o){const m=o.mv;return m?fmt(m.imp)+' / '+fmt(m.wor)+' / '+fmt(m.newu):'-';};
 const td=function(o){return '<tr><td>'+esc(o.dv)+'</td><td>'+esc(DNAME(o.c))+'</td><td>'+fmt(o.n)
  +'</td><td>'+fmt(o.b[0])+'</td><td>'+fmt(o.b[1])+'</td><td>'+fmt(o.b[2])+'</td><td>'+fmt(o.b[3])
  +'</td><td>'+(o.hi==null?'-':o.hi.toFixed(1))+'</td>'
  +(X.mig?'<td>'+mv(o)+'</td>':'')
  +'<td>'+(o.p==null?'-':o.p.toFixed(1))+'</td><td>'
  +(o.m==null?'-':o.m.toFixed(1))+'</td></tr>';};
 const ncol=X.mig?11:10;
 t.innerHTML='<thead><tr><th>Division</th><th>District</th><th>Councils</th><th>Low Risk</th>'
  +'<th>Medium</th><th>High</th><th>Excluded</th><th>High-Risk %</th>'
  +(X.mig?'<th title="Councils that moved to a lower-risk band / to a higher-risk band / are not in the earlier round">Better / worse / new</th>':'')
  +'<th>Marks earned %</th><th>Mean score %</th>'
  +'</tr></thead><tbody>'+(rows.length?rows.map(td).join('')
  :'<tr><td colspan="'+ncol+'" class="cnt">No HRA reading for the selected division and district.</td></tr>')
  +'</tbody>'+(rows.length?'<tfoot><tr class="tot"><td>All in scope</td><td>'+fmt(X.nd)
  +(X.nd===1?' district':' districts')+'</td><td>'+fmt(X.n)+'</td><td>'+fmt(X.bt[0])+'</td><td>'+fmt(X.bt[1])+'</td><td>'
  +fmt(X.bt[2])+'</td><td>'+fmt(X.bt[3])+'</td><td>'+(X.nb?(X.bt[2]/X.nb*100).toFixed(1):'-')+'</td>'
  +(X.mig?'<td>'+fmt(X.mig.tot.imp)+' / '+fmt(X.mig.tot.wor)+' / '+fmt(X.mig.tot.newu)+'</td>':'')
  +'<td>'+(X.posT?(X.achT/X.posT*100).toFixed(1):'-')+'</td><td>'
  +(X.nb?((X.ann.reduce(function(s,o){return s+o.sum;},0))/X.nb).toFixed(1):'-')
  +'</td></tr></tfoot>':'');}'''

CSV_OLD = r'''function hrvCSV(){
 const X=hrvData();
 if(!X.n){toast('The HRA payload is empty');return;}
 const H=['Division','District','Councils','Low Risk','Medium Risk','High Risk','High Risk %',
  'Marks earned %','Mean council score %','Marks earned','Marks charged','Sheets'];
 const rows=X.ann.filter(function(o){return o.n;}).slice().sort(function(a,b){
  return a.dv===b.dv?(DNAME(a.c)<DNAME(b.c)?-1:1):(a.dv<b.dv?-1:1);}).map(function(o){
  return [o.dv,DNAME(o.c),o.n,o.b[0],o.b[1],o.b[2],
   o.hi==null?'':Math.round(o.hi*10)/10,
   o.p==null?'':Math.round(o.p*10)/10,
   o.m==null?'':Math.round(o.m*10)/10,
   o.ach,o.pos,(X.pub?o.dates:X.per.slug+' (compiled)')];});
 const meanAll=X.ann.reduce(function(s,o){return s+(o.m||0)*o.n;},0)/X.n;
 rows.push(['All','All '+X.nd+' district'+(X.nd===1?'':'s'),X.n,X.bt[0],X.bt[1],X.bt[2],
  Math.round(X.bt[2]/X.n*1000)/10,Math.round(X.achT/X.posT*1000)/10,Math.round(meanAll*10)/10,
  X.achT,X.posT,'']);
 csvDownload('HRA_district_rollup_'+(X.sdv?X.sdv+'_':'')+(X.sdd?X.sdd+'_':'')
  +(X.pub?HRA.asof:X.per.slug)+'.csv',H,rows);}'''

CSV_NEW = r'''function hrvCSV(){
 const X=hrvData();
 if(!X.n){toast('The HRA payload is empty');return;}
 const H=['Division','District','Councils','Low Risk','Medium Risk','High Risk','Excluded','High Risk %',
  'Moved to lower risk','Moved to higher risk','Not in the earlier round',
  'Marks earned %','Mean council score %','Marks earned','Marks charged','Sheet'];
 const rows=X.ann.filter(function(o){return o.n;}).slice().sort(function(a,b){
  return a.dv===b.dv?(DNAME(a.c)<DNAME(b.c)?-1:1):(a.dv<b.dv?-1:1);}).map(function(o){
  const m=o.mv||{};
  return [o.dv,DNAME(o.c),o.n,o.b[0],o.b[1],o.b[2],o.b[3],
   o.hi==null?'':Math.round(o.hi*10)/10,
   m.imp||0,m.wor||0,m.newu||0,
   o.p==null?'':Math.round(o.p*10)/10,
   o.m==null?'':Math.round(o.m*10)/10,
   o.ach,o.pos,((X.pub||X.rnd)?o.dates:X.per.slug+' (compiled)')];});
 const meanAll=X.nb?X.ann.reduce(function(s,o){return s+(o.m||0)*o.nb;},0)/X.nb:null;
 rows.push(['All','All '+X.nd+' district'+(X.nd===1?'':'s'),X.n,X.bt[0],X.bt[1],X.bt[2],X.bt[3],
  X.nb?Math.round(X.bt[2]/X.nb*1000)/10:'',
  X.mig?X.mig.tot.imp:'',X.mig?X.mig.tot.wor:'',X.mig?X.mig.tot.newu:'',
  X.posT?Math.round(X.achT/X.posT*1000)/10:'',meanAll==null?'':Math.round(meanAll*10)/10,
  X.achT,X.posT,'']);
 csvDownload('HRA_district_rollup_'+(X.sdv?X.sdv+'_':'')+(X.sdd?X.sdd+'_':'')
  +((X.pub||X.rnd)?X.asof:X.per.slug)+'.csv',H,rows);}'''

MIG_FN = r'''// Cross-round read: the two published rounds side by side and the movement between them.
function hrvMig(X){
 const box=el('hrvMigWrap'),ch=el('hrv4'),tb=el('hrvMv');
 if(!box||!ch||!tb)return;
 const M=X.mig;
 if(!M){box.style.display='none';if(CH.hrv4){try{CH.hrv4.destroy();}catch(e){}delete CH.hrv4;}
  ch.innerHTML='';tb.innerHTML='';if(el('chrv4'))el('chrv4').textContent='';
  if(el('chrvMv'))el('chrvMv').textContent='';return;}
 box.style.display='';
 const mx=M.mx,L=[HRVB[0].l,HRVB[1].l,HRVB[2].l,'Excluded'];
 const rowS=mx.map(function(r){return r.reduce(function(s,v){return s+v;},0);});
 const colS=[0,0,0,0];mx.forEach(function(r){r.forEach(function(v,i){colS[i]+=v;});});
 const oldLbl=(HRA.may&&HRA.may.lbl)||'Earlier round',newLbl=HRA.lbl||'Latest round';
 const oldB=[0,1,2,3].map(function(i){return mx[0][i]+mx[1][i]+mx[2][i]+mx[3][i];});
 HC('hrv4',{
  chart:{type:'bar',height:260,backgroundColor:'transparent',spacing:[8,10,6,6]},
  title:{text:null},
  xAxis:{categories:[oldLbl,newLbl],labels:{style:{fontSize:'11px'}}},
  yAxis:{min:0,title:{text:null}},
  tooltip:{shared:true,pointFormat:'<b>{series.name}</b>: {point.y} councils'},
  plotOptions:{bar:{stacking:'normal',borderWidth:0,dataLabels:{enabled:true,
   formatter:function(){return this.y>=12?fmt(this.y):'';},
   style:{fontSize:'10px',color:'#fff',textOutline:'none',fontWeight:'600'}}}},
  legend:{enabled:true},
  series:[0,1,2,3].map(function(i){return {name:L[i],color:i===3?'#94a3b8':HRVB[i].c,
   data:[oldB[i],colS[i]]};})});
 el('chrv4').innerHTML='The same two rounds the table is cut from, as counts: '+fmt(oldB[2])
  +' High-Risk councils in '+esc(oldLbl)+' against '+fmt(colS[2])+' in '+esc(newLbl)
  +'. The bars are absolute counts, so a round that assessed more councils shows a taller bar.';
 const cell=function(r,c){const v=mx[r][c];
  return '<td'+(r===c&&r<4?' style="font-weight:600"':'')+'>'+fmt(v)+'</td>';};
 tb.innerHTML='<thead><tr><th>'+esc(oldLbl)+' \\ '+esc(newLbl)+'</th>'
  +'<th>Low</th><th>Medium</th><th>High</th><th>Excluded</th><th>Total</th></tr></thead><tbody>'
  +[0,1,2,3].map(function(r){return '<tr><td>'+esc(L[r])+'</td>'
   +[0,1,2,3].map(function(c){return cell(r,c);}).join('')
   +'<td><b>'+fmt(rowS[r])+'</b></td></tr>';}).join('')
  +'<tr><td>Not in the earlier round</td>'+[0,1,2,3].map(function(c){return cell(4,c);}).join('')
  +'<td><b>'+fmt(rowS[4])+'</b></td></tr>'
  +'</tbody><tfoot><tr class="tot"><td>'+esc(newLbl)+' total</td>'
  +[0,1,2,3].map(function(c){return '<td>'+fmt(colS[c])+'</td>';}).join('')
  +'<td>'+fmt(colS[0]+colS[1]+colS[2]+colS[3])+'</td></tr></tfoot>';
 el('chrvMv').innerHTML='Each cell counts councils; the diagonal (bold) held its band. '
  +fmt(M.tot.imp)+' moved to a lower-risk band, '+fmt(M.tot.wor)+' to a higher one, '
  +fmt(M.tot.same)+' held and '+fmt(M.tot.newu)+' are not in the earlier round'
  +(M.tot.nc?'; '+fmt(M.tot.nc)+' have no readable band in one of the two and appear only in the '
   +'Excluded row or column':'')+'.';}
function hrvTable(X){'''

TABLE_ANCHOR = r'''// HRA AT A GLANCE (5/5): the district roll-up download behind the map card.
// The district roll-up the CSV already carried, on screen and under the same scope.
function hrvTable(X){'''

HRD_OLD = r''' HRA.u.forEach(r=>{const d=HRA.d[r[0]],o=_HRDH[d]=_HRDH[d]||{n:0,lo:0,me:0,hi:0,ach:0,pos:0,v:{},uc:[]};
  o.n++; if(r[6]===2)o.hi++; else if(r[6]===1)o.me++; else o.lo++;
  o.ach+=r[3]||0; o.pos+=r[4]||0; o.v[r[7]]=(o.v[r[7]]||0)+1; if(r[6]>=1)o.uc.push(r);});
'''
HRD_NEW = r''' HRA.u.forEach(r=>{const d=HRA.d[r[0]],o=_HRDH[d]=_HRDH[d]||{n:0,lo:0,me:0,hi:0,ex:0,ach:0,pos:0,v:{},uc:[]};
  o.n++; if(r[6]===2)o.hi++; else if(r[6]===1)o.me++; else if(r[6]===0)o.lo++; else o.ex++;
  o.v[r[7]]=(o.v[r[7]]||0)+1; if(r[6]===1||r[6]===2)o.uc.push(r);
  if(r[6]===3)return;                // no readable percentage: keep it out of the marks ratio
  o.ach+=r[3]||0; o.pos+=r[4]||0;});
'''

HRD_TEXT = (r'''  if(ch.hra)wd.push('<b>HRA</b>: '+fmt(h.hi)+' of '+fmt(h.n)+' councils scored High Risk'
   +(h.me?', '+fmt(h.me)+' Medium':''));
''', r'''  if(ch.hra)wd.push('<b>HRA</b>: '+fmt(h.hi)+' of '+fmt(h.n-h.ex)+' councils scored High Risk'
   +(h.me?', '+fmt(h.me)+' Medium':'')+(h.ex?'; '+fmt(h.ex)+' carried Excluded':''));
''')

FACT_OLD = r'''    hra={n:ucs.length,avg:avg_(byD[dist]),band:{lo:0,me:0,hi:0},worst:worst.slice(0,6),best:worst.slice(-5).reverse(),rank:rank,nDistricts:rankRows.length};
    hraRows.forEach(function(r){ if(r[6]===2)hra.band.hi++; else if(r[6]===1)hra.band.me++; else hra.band.lo++; });
'''
FACT_NEW = r'''    hra={n:ucs.length,avg:avg_(byD[dist]),band:{lo:0,me:0,hi:0,ex:0},worst:worst.slice(0,6),best:worst.slice(-5).reverse(),rank:rank,nDistricts:rankRows.length};
    hraRows.forEach(function(r){ if(r[6]===2)hra.band.hi++; else if(r[6]===1)hra.band.me++; else if(r[6]===0)hra.band.lo++; else hra.band.ex++; });
'''

FACT_LINE = (r'''  ready.push(D.hra?['High-risk UCs',D.hra.band.hi+' high · '+D.hra.band.me+' medium of '+D.hra.n]:['HRA','no UC risk assessment returned']);
''', r'''  ready.push(D.hra?['High-risk UCs',D.hra.band.hi+' high · '+D.hra.band.me+' medium of '+(D.hra.n-D.hra.band.ex)+(D.hra.band.ex?' ('+D.hra.band.ex+' excluded)':'')]:['HRA','no UC risk assessment returned']);
''')

EDITS = [
    ('html card', HTML_CARD),
    ('round picker', PERFILL),
    ('round meta', PERMETA),
    ('data', (DATA_OLD, DATA_NEW)),
    ('render src', RENDER_SRC),
    ('render call', RENDER_CALL),
    ('render empty', RENDER_EMPTY),
    ('hint', (HINT_OLD, HINT_NEW)),
    ('band rows', BAND_ROWS),
    ('band series', BAND_SERIES),
    ('band cap', BAND_CAP),
    ('band cap 2', BAND_CAP2),
    ('curve cap', CURVE_CAP),
    ('map swat', MAP_SW),
    ('map tip', MAP_TIP),
    ('map nosheet', MAP_NOSHEET),
    ('map tip2', MAP_TIP2),
    ('map cap', MAP_CAP),
    ('map base', MAP_BASE),
    ('mig fn', (TABLE_ANCHOR, MIG_FN)),
    ('table', (TABLE_OLD, TABLE_NEW)),
    ('csv', (CSV_OLD, CSV_NEW)),
    ('hrd hra', (HRD_OLD, HRD_NEW)),
    ('hrd text', HRD_TEXT),
    ('fact band', (FACT_OLD, FACT_NEW)),
    ('fact line', FACT_LINE),
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
