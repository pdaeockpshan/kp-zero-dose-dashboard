"""Consolidated high-risk / need-focus Districts module for the upcoming campaign.

The owner asked, 26-Oct-2026: "there is strong need to create a module for high risk Districts
identification in Campaign section based on Last three campaign comparison analysis mixed with other
indicators so that core team can easily assign monitors to supervise campaign activities in those
districts", and again in the same instruction for "a consolidated module for high risk/need focus
districts for upcoming campaign".

What it does: a `hrd` tab in the Campaigns nav group that puts the portal's own UC-level High Risk
Assessment (`const HRA`, from extract_hra.py - the payload had no UI before this patch) beside five
other district-level channels the dashboard already computes: the last-three-campaigns roll-up
(`c3UC`), the Nov-26 pre-campaign readiness snapshot (`NEAP.d`) with the assigned micro-plan sample
(`MPQA.d`), the selected round's monitoring (`cqDist(CQI)`: ICM recall, LQAS lots, performance
class), routine OPV-3 from the EPI file (`EPI`), and structural exposure (the EOC master
categorization `UCC` plus the polio case / sewage / watch-list flags `cqDist` already carries). A
district is placed by how many of the six channels fire, never by an average of them.

Two rules the module must keep, both from standing owner instruction:

* HRA's Low/Medium/High axis is the portal's own instrument and the combined UC risk score
  (`riskAll`) is a different one. They are never blended, and the pane says so, because a reader
  who opens both pages has to be able to see the two answers disagree rather than an averaged third.
* A channel with no row for a district is reported as "no data" and excluded from the count in both
  directions - NEAP and MPQA carry 27 of the 36 HRA districts and BAR SWAT has no HRA row at all, so
  a dash means the export has no row, not a zero. Per-district vintage divergence is stated in the
  note: only the districts the 26-Oct-2026 Mardan Division file re-scored are fresh, the rest are
  still on the March province-wide sheet.

Monitor assignment is a `<select>` per district, saved to localStorage on this browser only: the
site is public GitHub Pages, so nothing typed here can go into a payload or be uploaded, and the
download carries the number the core team chose as their own working file.

Two scoping facts this module depends on, both verified in the browser rather than assumed: the
global district-name helper is `const DNAME`, while `DNb` is a `const` local to `renderNEP()` and
throws from here. And the campaign picker this pane shows is the shared `CQI`, which reaches the
module only through `cqDist(CQI)` - so it moves the Monitoring and Exposure channels, while the
coverage, still-missed and zero-dose columns stay on `LCP` (the last completed round). The hint says
exactly that, because a picker that silently re-tiered a table labelled with one round would be a
mislabelled total.

Applied to the index.html master only; the other three variants get it through
`_refresh/push_master.py`, which is the owner-approved route for propagating a hand-edited master.
`--unpatch` restores the previous file byte for byte. Every anchor is asserted to occur exactly
once, all inserted text uses CRLF, and ids stay unique.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

# The ids this patch owns - asserted present exactly once after applying.
NEW_IDS = ['p-hrd', 'bHRD', 'hrdHint', 'hrdPills', 'hrdCap', 'hrdg1', 'capHRDg1', 'tHRD',
           'hrdUcnt', 'hrdUCap', 'tHRDU', 'hd1', 'hd1s', 'hd2', 'hd2s', 'hd3', 'hd3s',
           'hd4', 'hd4s', 'hd5', 'hd5s', 'btnHRDx', 'btnHRDUx']

PANE = """<!-- HIGH-RISK DISTRICT FOCUS: HRA council scores x the last three campaigns ---------- -->
<section class="pane" id="p-hrd">
<div class="cqbar"><b>High-risk district focus &middot; SNID Nov-26</b><select class="cqsel" aria-label="Campaign"></select><span class="cnt cqnote"></span></div>
<div class="hint" id="hrdHint"></div>
<div class="kpis">
<div class="card"><div class="kl">Districts needing monitors</div><div class="kv" id="hd1" style="color:#9a3412">&ndash;</div><div class="ks" id="hd1s"></div></div>
<div class="card"><div class="kl">HRA High Risk councils</div><div class="kv" id="hd2" style="color:#b91c1c">&ndash;</div><div class="ks" id="hd2s"></div></div>
<div class="card"><div class="kl">HRA Medium Risk councils</div><div class="kv" id="hd3">&ndash;</div><div class="ks" id="hd3s"></div></div>
<div class="card"><div class="kl">Monitors suggested</div><div class="kv" id="hd4">&ndash;</div><div class="ks" id="hd4s"></div></div>
<div class="card"><div class="kl">Monitors assigned</div><div class="kv" id="hd5">&ndash;</div><div class="ks" id="hd5s"></div></div>
</div>
<div class="hubchips"><button data-hl="c3">Comparison &amp; monitoring</button><button data-hl="cpre">Pre-campaign readiness</button><button data-hl="hcamp">Campaign overview</button><button data-hl="risk">Combined UC risk score</button></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">Districts ranked for supportive supervision</h3><span class="pills" id="hrdPills"></span><span style="flex:1"></span><button class="btn" id="btnHRDx">Download (Excel)</button></div>
<div class="cap" id="hrdCap"></div>
<div id="hrdg1" class="ch"></div><div class="cap" id="capHRDg1"></div>
<div class="scroll"><table id="tHRD"></table></div></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">The councils a monitor should be sent to</h3><span class="cnt" id="hrdUcnt"></span><span style="flex:1"></span><button class="btn" id="btnHRDUx">Download (Excel)</button></div>
<div class="cap" id="hrdUCap"></div>
<div class="scroll"><table id="tHRDU"></table></div></div>
</section>
"""

JS = """// ---------- HIGH-RISK DISTRICT FOCUS: HRA council scores x the last three campaigns ----------
// Six independent channels are read beside each other and a district is placed by how many of them
// fire. They are never averaged into one score: the HRA axis is the portal's own High Risk
// Assessment instrument and the combined UC risk score on the Cross-cutting pages is a different
// one, so a reader comparing the two must see two answers, not a blended third.
const HRDMAX=6, HRDKEY='kp.hrd.assign', hrN=(n,w)=>fmt(n)+' '+w+(n===1?'':'s');
const HRDCH=[['hra','HRA risk'],['camp','Last 3 rounds'],['rdy','Nov-26 readiness'],
 ['mon','Monitoring'],['epi','Routine EPI'],['exp','Exposure']];
const HRDTT=['councils the HRA template itself scores High Risk',
 'the latest round with data left coverage under 90%, or 3%+ of the target still missed, or 5%+ not reached',
 'Nov-26 NEAP readiness under 95%, micro-plan reviews still owed, or a micro-plan already scored under 70',
 'in the round selected above ICM recall under 90%, LQAS lots passed under 80%, or the district is classed poor or needs focus',
 'routine OPV-3 under 80% in EPI-MIS for the same district',
 'Afghan-bordering, core, endemic or high-risk categorization, or a polio case, positive sewage or a watch-list flag'];
const HRDTR={A:['t-crit','Assign monitors now'],B:['t-low','One monitor this round'],
 C:['t-mod','Watch'],D:['t-none','Routine oversight']};
let _HRDH=null,_HRDR=null,_HRDCI=-1,HRDT='';
const hrdLoad=()=>{try{return JSON.parse(localStorage.getItem(HRDKEY)||'{}')||{};}catch(e){return {};}};
function hrdSave(d,v){const a=hrdLoad(); if(v>0)a[d]=v; else delete a[d];
 try{localStorage.setItem(HRDKEY,JSON.stringify(a));}catch(e){}}
function hrdHRA(){ if(_HRDH)return _HRDH; _HRDH={};
 if(typeof HRA==='undefined'||!HRA||!(HRA.u||[]).length)return _HRDH;
 HRA.u.forEach(r=>{const d=HRA.d[r[0]],o=_HRDH[d]=_HRDH[d]||{n:0,lo:0,me:0,hi:0,ach:0,pos:0,v:{},uc:[]};
  o.n++; if(r[6]===2)o.hi++; else if(r[6]===1)o.me++; else o.lo++;
  o.ach+=r[3]||0; o.pos+=r[4]||0; o.v[r[7]]=(o.v[r[7]]||0)+1; if(r[6]>=1)o.uc.push(r);});
 return _HRDH;}
function hrdCamp(){ const G={},B={};
 c3UC().forEach(r=>{ B[String(r.c)]=r; if(!r.d)return;
  const g=G[r.d]=G[r.d]||{ucs:0,tg:0,vc:0,st:0,lo:0,rf:0,pri:0,zr:0,zrc:0,zc:0};
  g.ucs++; if(r['tg'+LCP]!=null){g.tg+=r['tg'+LCP];g.vc+=r['vc'+LCP]||0;g.st+=r['st'+LCP]||0;g.lo+=r['lo'+LCP]||0;}
  g.rf+=r['rf'+LCP]||0; if(r.top)g.pri++; g.zr+=r['r'+LCP]||0;
  if(r['c'+LCP]!=null){g.zc+=r['c'+LCP];g.zrc+=r['r'+LCP]||0;}});
 return {G:G,B:B};}
function hrdEPI(){ const G={};
 (typeof EPI==='undefined'||!EPI?[]:EPI).forEach(r=>{ if(!r.d||!(r.s>0)||r.opv3==null)return;
  const g=G[r.d]=G[r.d]||{s:0,o3:0,n:0}; g.s+=r.s; g.o3+=r.opv3; g.n++;});
 return G;}
function hrdNE(){ if(typeof NEAP==='undefined'||!NEAP||!NEAP.k)return null;
 const M={}; NEAP.k.forEach((x,j)=>{M[x[0]]=j;});
 return {g:(d,k)=>{const v=(NEAP.d||{})[d]; if(!v)return null; const j=M[k];
  return j==null||v[j]==null||v[j]<0?null:v[j];}};}
function hrdRows(){ if(_HRDR&&_HRDCI===CQI)return _HRDR; _HRDCI=CQI;
 const H=hrdHRA(), CP=hrdCamp(), EP=hrdEPI(), NE=hrdNE(),
  MQ=(typeof MPQA!=='undefined'&&MPQA&&MPQA.d)?MPQA.d:{},
  X=cqDist(CQI), Q={}; X.R.forEach(o=>{Q[o.d]=o;});
 const set=new Set([].concat(Object.keys(H),Object.keys(CP.G),Object.keys(Q)));
 _HRDR=[...set].map(d=>{
  const h=H[d]||null, cg=CP.G[d]||null, q=Q[d]||null, e=EP[d]||null, mq=MQ[d]||null;
  const vp=cg&&cg.tg?cg.vc/cg.tg*100:null, stp=cg&&cg.tg?cg.st/cg.tg*100:null,
   lop=cg&&cg.tg?cg.lo/cg.tg*100:null, zpc=cg&&cg.zrc?cg.zc/cg.zrc*100:null,
   zgap=cg?Math.max(0,cg.zr-cg.zc):0, ep=e&&e.s?e.o3/e.s*100:null,
   cat=critIx(d), cb=(typeof UCC!=='undefined'&&UCC.a)?UCC.a.filter(x=>x[0]===d).length:0,
   rdn=NE?avg([NE.g(d,'dpec'),NE.g(d,'must'),NE.g(d,'aic'),NE.g(d,'trn'),NE.g(d,'mpv')]):null,
   owe=mq?Math.max(0,mq[0]-mq[1]):null, ser=mq?mq[4]:null, hp=h&&h.pos?h.ach/h.pos*100:null;
  const ch={}, wd=[];
  ch.hra=h?(h.hi>0?1:0):null;
  if(ch.hra)wd.push('<b>HRA</b>: '+fmt(h.hi)+' of '+fmt(h.n)+' councils scored High Risk'
   +(h.me?', '+fmt(h.me)+' Medium':''));
  ch.camp=cg&&cg.tg?((vp<90||stp>=3||lop>=5)?1:0):null;
  if(ch.camp)wd.push('<b>Last 3 rounds</b>: '+esc(CAMP[LCP])+' coverage '+pc(vp)+', '+pc(stp)
   +' of the target still missed'+(lop>=5?', '+pc(lop)+' left not reached':''));
  ch.rdy=(rdn==null&&!mq)?null:(((rdn!=null&&rdn<95)||owe>0||ser>0)?1:0);
  if(ch.rdy)wd.push('<b>Nov-26 readiness</b>: '+(rdn==null?'no NEAP row filed yet':'readiness '+pc(rdn))
   +(owe>0?', '+fmt(owe)+' micro-plan review'+(owe===1?'':'s')+' still to file':'')
   +(ser>0?', '+fmt(ser)+' micro-plan'+(ser===1?'':'s')+' already scored under 70':''));
  ch.mon=q?(((q.rec!=null&&q.rec<90)||(q.lqp!=null&&q.lqp<80)||q.cls==='r'||q.cls==='f')?1:0):null;
  if(ch.mon)wd.push('<b>Monitoring</b> \\u00b7 '+esc((X.C&&X.C.l)||CAMP[LCP])+': ICM recall '+pc(q.rec)+', LQAS lots passed '+pc(q.lqp)
   +(q.F&&q.F.length?', '+fmt(q.F.length)+' source disagreement'+(q.F.length===1?'':'s'):''));
  ch.epi=ep==null?null:(ep<80?1:0);
  if(ch.epi)wd.push('<b>Routine EPI</b>: OPV-3 '+pc(ep)+' over '+fmt(e.n)+' councils with a target');
  ch.exp=(cat==null&&!q&&cb===0)?null:(((cat!=null&&cat<=3)||cb>0||(q&&(q.wpv>0||q.esPos||q.watch)))?1:0);
  if(ch.exp){const p=[cat!=null&&cat<=3?critLab(d):'', cb>0?fmt(cb)+' Afghan-bordering councils':'',
    q&&q.wpv>0?q.wpv+' polio case'+(q.wpv>1?'s':'')+' in '+X.yr:'', q&&q.esPos?'positive sewage '+X.yr:'',
    q&&q.watch?'polio watch district':''].filter(Boolean);
   wd.push('<b>Exposure</b>: '+esc(p.join(', ')));}
  const n=HRDCH.reduce((s,c)=>s+(ch[c[0]]===1?1:0),0),
   nd=HRDCH.reduce((s,c)=>s+(ch[c[0]]==null?1:0),0);
  const o={d,dv:D2DV[d]||'',h:h,cg:cg,q:q,vp:vp,stp:stp,lop:lop,zpc:zpc,zgap:zgap,ep:ep,rdn:rdn,
   mq:mq,owe:owe,ser:ser,hp:hp,cat:cat,cb:cb,ch:ch,n:n,nd:nd,wd:wd,hi:h?h.hi:0,me:h?h.me:0};
  o.tier=(n>=5||(ch.hra===1&&n>=3))?'A':(n===4||(ch.hra===1&&n>=1))?'B':(n>=2)?'C':'D';
  o.sug=Math.min(HRDMAX,o.hi+(cg?cg.pri:0)); if(o.tier==='A'&&!o.sug)o.sug=1;
  o.ord='DCBA'.indexOf(o.tier)*1000+n*10+Math.min(9,o.hi);
  return o;}).sort((a,b)=>b.ord-a.ord||b.hi-a.hi||String(a.d).localeCompare(String(b.d)));
 return _HRDR;}
function hrdUCs(R){ const out=[], CP=hrdCamp();
 if(typeof HRA==='undefined'||!HRA||!(HRA.u||[]).length)return out;
 const tr={}; R.forEach(o=>{tr[o.d]=o.tier;});
 HRA.u.forEach(r=>{ const d=HRA.d[r[0]], t=tr[d]; if(!t)return;
  if(!(r[6]===2||(r[6]===1&&(t==='A'||t==='B'))))return;
  const c=CP.B[String(r[2])]||{}, sc=r[8]||[], dr=[];
  sc.forEach((v,j)=>{ if(v===0&&HRA.k[j])dr.push(HRA.k[j][0]+' \\u00b7 '+HRA.k[j][1]); });
  out.push({d,uc:r[1],code:r[2],pct:r[5],band:r[6],ach:r[3],pos:r[4],vin:HRA.v[r[7]],tier:t,
   dr:dr,nz:sc.filter(v=>v==null).length,vp:c['vp'+LCP]==null?null:c['vp'+LCP],
   st:c['st'+LCP]||0,lo:c['lo'+LCP]||0,zr:c['r'+LCP]||0,zc:c['c'+LCP]==null?null:c['c'+LCP]});});
 return out.sort((a,b)=>b.band-a.band||a.pct-b.pct||String(a.d).localeCompare(String(b.d)));}
function hrdBadge(){ const b=el('bHRD'); if(!b)return;
 const R=hrdRows().filter(o=>crInD()(o.d));
 b.textContent=fmt(R.filter(o=>o.tier==='A').length)+' priority';}
function renderHRD(){
 cqSel();
 const inD=crInD(), ALL=hrdRows(), R0=ALL.filter(o=>inD(o.d)), AS=hrdLoad(),
  A=R0.filter(o=>o.tier==='A'), B=R0.filter(o=>o.tier==='B'),
  D=R0.filter(o=>!HRDT||o.tier===HRDT), UC=hrdUCs(D),
  hiS=R0.reduce((s,o)=>s+o.hi,0), meS=R0.reduce((s,o)=>s+o.me,0),
  scored=R0.reduce((s,o)=>s+(o.h?o.h.n:0),0), sugS=D.reduce((s,o)=>s+o.sug,0),
  ad=Object.keys(AS).filter(d=>inD(d)&&AS[d]>0), adS=ad.reduce((s,d)=>s+(AS[d]||0),0),
  HW=(typeof HRA!=='undefined'&&HRA)?HRA:null,
  noH=ALL.filter(o=>!o.h).map(o=>o.d),
  fresh=HW?Object.keys(hrdHRA()).filter(d=>(hrdHRA()[d].v[0]||0)>0):[];
 el('hrdHint').innerHTML='<b>Which districts to put a monitor on for SNID Nov-26.</b> Six independent'
  +' channels are read beside each other and a district is placed by how many of them fire. They are'
  +' <b>never averaged into one score</b>: '+((HW&&HW.b)?'the HRA template\\u2019s own axis ('
  +esc(HW.b.join(' / '))+', thresholds '+HW.thr[0]+'+ and '+HW.thr[1]+')':'the HRA axis')+
  +' is a different instrument from the combined UC risk score on the Cross-cutting pages, and the two'
  +' are deliberately kept apart so that a reader who opens both can see them disagree rather than see'
  +' a blended third number. Channels: '+HRDCH.map((c,j)=>(j+1)+'. '+c[1]+' \\u2014 '+HRDTT[j]).join(' ')
  +' \\u00b7 a channel with no row for a district is <b>not counted at all</b>, in either direction.'
  +(HW?' \\u00b7 Source: '+esc((HW.src[0]||'').split('] ')[0]+']')+
  ', '+fmt(HW.n)+' councils scored, '+HW.zj+' of them ('+HW.zr+'%) matched to the campaign UC codes.'
  :'')+(HW&&HW.v&&HW.v.length>1?' \\u00b7 <b>Vintage:</b> the freshest file ('+esc(HW.v[0])+') re-scored '
  +(fresh.length===1?'only <b>'+esc(DNAME(fresh[0]))+'</b>':fresh.length?fmt(fresh.length)+' districts ('
  +esc(fresh.map(DNAME).join(', '))+')':'no district')+
  '; every other council here is still on the earlier sheet ('+esc(HW.v[HW.v.length-1])+'). The two'
  +' vintages are not the same assessment round, so a district score is only ever compared with its'
  +' own file.':'')
  +(typeof NEAP!=='undefined'&&NEAP&&NEAP.d&&typeof MPQA!=='undefined'&&MPQA&&MPQA.d?' \\u00b7 NEAP'
  +' and MPQA file rows for '+Object.keys(NEAP.d).length+' and '+Object.keys(MPQA.d).length+' of the '
  +fmt(ALL.length)+' districts in this table, and the HRA template scores '+fmt(ALL.length-noH.length)
  +' of them'+(noH.length?' \\u2014 no HRA row at all for '+esc(noH.map(DNAME).join(', ')):'')+
  '. A dash means that source has no row for the district, never a zero, and it is dropped from the '
  +'channel count in both directions.'
  :'')+((SCOV)?' \\u00b7 The zero-dose covered figures are '+esc(CAMP[LCP])+'\\u2019s own UC-wise export,'
  +' same-round self-reported and not yet confirmed by a later round.':'')+
  ' \\u00b7 The campaign picker above moves only the Monitoring and Exposure channels, which come from the '
  +'portal ICM / LQAS tables for the round chosen; the coverage, still-missed and zero-dose '
  +'columns stay on '+esc(CAMP[LCP])+', the last completed round, because this table plans the next one.'
  +' \\u00b7 <b>Suggested monitors</b> = one for each council the HRA template scored High Risk in that'
  +' district, plus one for each council the last-three-campaigns page ranks in its priority 10%,'
  +' capped at '+HRDMAX+'. The <b>Assigned</b> box writes to this browser only (localStorage): nothing'
  +' typed here is uploaded, and no person name is held anywhere in this file.';
 el('hrdPills').innerHTML=[['','All tiers',R0.length],
  ...['A','B','C','D'].map(t=>[t,HRDTR[t][1],R0.filter(o=>o.tier===t).length])].map(p=>
  '<button class="pill'+(p[0]===HRDT?' on':'')+'" data-t="'+p[0]+'">'+esc(p[1])+' ('+fmt(p[2])+')</button>').join('');
 el('hrdPills').querySelectorAll('button').forEach(b=>b.onclick=()=>{HRDT=b.dataset.t;renderHRD();});
 el('hrdPills').querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.t===HRDT));
 el('hd1').textContent=fmt(A.length+B.length);
 el('hd1s').textContent=fmt(A.length)+' in the assign-now tier \\u00b7 '+fmt(B.length)
  +' in the next tier \\u00b7 '+fmt(R0.length)+' of '+fmt(ALL.length)+' KP districts in view, follows the filter';
 el('hd2').textContent=fmt(hiS);
 el('hd2s').textContent=hrN(R0.filter(o=>o.hi>0).length,'district')+' \\u00b7 of '+fmt(scored)
  +' councils the HRA template scored';
 el('hd3').textContent=fmt(meS);
 el('hd3s').textContent=hrN(R0.filter(o=>o.me>0).length,'district')+' carry the Medium Risk load';
 el('hd4').textContent=fmt(sugS);
 el('hd4s').textContent='for the '+fmt(D.length)
  +(D.length===1?' district shown':' districts shown')+' \\u00b7 one per High-Risk or priority council, capped at '+HRDMAX;
 el('hd5').textContent=fmt(adS);
 el('hd5s').textContent=ad.length?fmt(ad.length)+' district'+(ad.length===1?'':'s')
  +' written in on this browser \\u00b7 not uploaded anywhere':'nothing assigned yet \\u00b7 use the box in the table';
 const HW_=HW, hb=(v,g,a)=>v==null?'<span class="cnt">\\u2013</span>':'<span class="rg '
  +(v>=g?'g':v>=a?'a':'r')+'">'+v.toFixed(1)+'%</span>',
  lw=(v,g,a)=>v==null?'<span class="cnt">\\u2013</span>':'<span class="rg '
  +(v<=g?'g':v<=a?'a':'r')+'">'+v.toFixed(1)+'%</span>';
 drawTable('tHRD',[
  {k:'d',l:'District',f:o=>'<b>'+esc(DNAME(o.d))+'</b>'+(o.dv?'<span class="cnt"> '+esc(DNAME(o.dv))+' div.</span>':'')},
  {k:'ord',l:'Tier',sv:o=>'DCBA'.indexOf(o.tier),
   f:o=>'<span class="tag '+HRDTR[o.tier][0]+'">'+o.tier+' \\u00b7 '+HRDTR[o.tier][1]+'</span>'},
  {k:'n',l:'Ch.',n:1,sv:o=>o.n,
   tt:'How many of the six independent channels flag this district \\u2014 '+
    HRDCH.map((c,j)=>(j+1)+' '+c[1]+': '+HRDTT[j]).join(' \\u00b7 ')+
    ' \\u00b7 a channel with no row for the district is counted in neither direction',
   f:o=>o.n?('<b style="color:'+(o.n>=4?'#991B1B':o.n>=3?'#c2410c':'#d97706')+'">'+o.n+' / 6</b>'
    +(o.nd?'<span class="cnt"> '+fmt(o.nd)+' no data</span>':'')):'<span class="cnt">0 / 6'+(o.nd?' \\u00b7 '+fmt(o.nd)+' no data':'')+'</span>'},
  {k:'hi',l:'HRA High / Med',n:1,
   tt:'Councils the HRA template scored High Risk, then Medium Risk, of the councils it scored at all'
    +(HW_?' (its own axis: '+(HW_.thr[0]+'+ = Low, '+HW_.thr[1]+'-'+(HW_.thr[0]-1)+' Medium, under '+HW_.thr[1]+' High)'):''),
   f:o=>o.h?('<b'+(o.hi?' class="dn"':'')+'>'+fmt(o.hi)+'</b> / '+fmt(o.me)
    +'<span class="cnt"> of '+fmt(o.h.n)+'</span>'):'<span class="cnt">no HRA row</span>'},
  {k:'hp',l:'HRA score',n:1,
   tt:'Achieved \\u00f7 possible points across the district\\u2019s own councils, on the HRA scale. Not a'
    +' campaign coverage figure and not the combined UC risk score',
   f:o=>hb(o.hp,HW_?HW_.thr[0]:79,HW_?HW_.thr[1]:60)},
  {k:'vp',l:CAMP[LCP]+' coverage',n:1,
   tt:'Vaccinated \\u00f7 target rolled from the same UC rows as the Last 3 campaigns page',
   f:o=>hb(o.vp,90,80)},
  {k:'stp',l:'Still missed',n:1,tt:'Children still missed after catch-up, as a share of the target',
   f:o=>lw(o.stp,2,4)},
  {k:'zpc',l:'ZD covered',n:1,
   tt:'Zero-dose children covered \\u00f7 reported, over the councils that carry a covered figure. '
    +(SCOV?CAMP[LCP]+'\\u2019s own export, same-round self-reported':'')+' A gap is children reported with no covered figure behind them',
   f:o=>o.zpc==null?'<span class="cnt">\\u2013</span>':hb(o.zpc,90,80)
    +(o.zgap?'<span class="cnt"> \\u00b7 '+fmt(o.zgap)+' no figure</span>':'')},
  {k:'rdn',l:'Nov-26 readiness',n:1,
   tt:'Mean of DPEC on time, mandatory members, AICs trained, teams trained and micro-plans validated, from the '+esc(NEAP.camp||'Nov-26')+' NEAP snapshot',
   f:o=>hb(o.rdn,95,85)},
  {k:'ep',l:'OPV-3 %',n:1,tt:'Routine EPI-MIS OPV-3, '+esc(EPER||'the current EPI window')+' \\u00b7 can exceed 100% where doses run ahead of the recorded target',
   f:o=>hb(o.ep,90,80)},
  {k:'cat',l:'Category',sv:o=>o.cat==null?99:o.cat,tt:'EOC master categorization for the district, '+esc((typeof UCC!=='undefined'&&UCC)?UCC.camp:'')+' scope',
   f:o=>critTag(o.d)},
  {k:'sug',l:'Suggested monitors',n:1,
   tt:'One per High-Risk council plus one per priority council from the last three campaigns, capped at '+HRDMAX,
   f:o=>o.sug?('<b>'+fmt(o.sug)+'</b>'):'<span class="cnt">\\u2013</span>'},
  {k:'as',l:'Monitors assigned',ns:1,
   f:o=>'<select class="hrdas" data-d="'+esc(o.d)+'" aria-label="Monitors assigned to '+esc(DNAME(o.d))+'">'
    +'<option value="0"'+(!(AS[o.d]||0)?' selected':'')+'>\\u2013</option>'
    +[1,2,3,4,5,6].map(v=>'<option value="'+v+'"'+((AS[o.d]||0)===v?' selected':'')+'>'+v
    +(v===6?'+' :'')+'</option>').join('')+'</select>'},
  {k:'wd',l:'Why it is here',ns:1,f:o=>o.wd.length?o.wd.join('<br>'):'<span class="cnt">no channel flags it</span>'}],
  D,'ord',-1);
 el('tHRD').querySelectorAll('.hrdas').forEach(s=>{s.onchange=()=>{hrdSave(s.dataset.d,+s.value);renderHRD();};});
 el('hrdCap').textContent='Sorted by tier, then by channels flagged, then by High-Risk councils. '
  +CAMP[LCP]+' coverage, still missed and zero-dose columns are rolled from the same UC rows as the '
  +'Last 3 campaigns page; readiness is the '+(NEAP.camp||'Nov-26')+' NEAP snapshot ('+(NEAP.asof||'?')+') '
  +'and MPQA the assigned sample, which is problem-selected on purpose so its bands are not a '
  +'micro-plan quality rate. '+fmt(A.length)+' districts sit in tier A ('+HRDTR.A[1].toLowerCase()+'), '
  +fmt(B.length)+' in tier B. Follows the division / district filter and the campaign picker above, '
  +'which changes the Monitoring channel only.';
 const GD=D.slice(0,24);
 el('hrdg1').style.height=hFor(GD.length,24)+'px';
 const hm=[]; GD.forEach((g,y)=>HRDCH.forEach((c,x)=>hm.push(
  {x,y,value:g.ch[c[0]]==null?null:g.ch[c[0]]})));
 HC('hrdg1',{chart:{type:'heatmap',marginTop:74},
  title:{text:'Which channel flags each district'},
  subtitle:{text:'\\u201cflag\\u201d = that channel fires for the district \\u00b7 \\u201cak\\u201d = the source has a row '
   +'and does not fire \\u00b7 a grey dash = that source has no row for the district, which is never read as a zero'},
  xAxis:{categories:HRDCH.map(c=>c[1]),opposite:true,labels:{autoRotation:false,style:{fontSize:'11px'}}},
  yAxis:{categories:GD.map(g=>DNAME(g.d)),reversed:true,title:{text:null},gridLineWidth:0,
   labels:{style:{fontSize:'11px'}}},
  colorAxis:{dataClasses:[{from:-0.5,to:0.5,color:'#dcfce7',name:'has a row, does not fire'},
   {from:0.5,to:1.5,color:'#dc2626',name:'flagged'}]},
  legend:{align:'left',verticalAlign:'bottom'},
  tooltip:{formatter(){const g=GD[this.point.y]; return '<b>'+esc(DNAME(g.d))+'</b><br>'
   +HRDCH[this.point.x][1]+': <b>'+(this.point.value==null?'no row in this source'
   :this.point.value?'flagged':'clean')+'</b><br>'+(this.point.value?HRDTT[this.point.x]:'');}},
  series:[{name:'Channel',borderWidth:1,borderColor:'#fff',nullColor:'#f3f4f6',data:hm,
   dataLabels:{enabled:true,style:{textOutline:'none',fontWeight:'600',fontSize:'10.5px'},
    formatter(){return this.point.value==null?'\\u2013':this.point.value?'flag':'ok';}}}]});
 el('capHRDg1').textContent=(D.length>24?fmt(D.length-24)+' lower-tier districts are off this chart but '
  +'stay in the table and the download. ':'')+'A whole grey row is a district no source here covers, '
  +'not a district that has been checked and found clean.';
 el('hrdUcnt').textContent=hrN(UC.length,'council')+' \\u00b7 '+hrN(new Set(UC.map(x=>x.d)).size,'district');
 el('hrdUCap').textContent='Every council the HRA template scored High Risk in the tiers shown, plus the '
  +'Medium Risk councils inside tiers A and B \\u2014 the named targets a monitor should be sent to. '
  +'"Scored 0 of 3" columns are the portal\\u2019s own indicator rows that came out worst for that council; '
  +(HW_?'the template leaves '+fmt(HW_.nx.length)+' criteria un-scored across the file and those carry no points either way. ':'')
  +'Coverage and missed children are the same council in '+CAMP[LCP]+', from the campaign data.';
 drawTable('tHRDU',[
  {k:'tier',l:'Tier',sv:x=>'DCBA'.indexOf(x.tier),
   f:x=>'<span class="tag '+HRDTR[x.tier][0]+'">'+x.tier+'</span>'},
  {k:'d',l:'District',f:x=>esc(DNAME(x.d))},
  {k:'uc',l:'Union council',f:x=>'<b>'+esc(x.uc)+'</b>'},
  {k:'code',l:'UC code',f:x=>'<span class="cnt">'+esc(x.code)+'</span>'},
  {k:'band',l:'HRA band',sv:x=>x.band,
   f:x=>'<span class="tag '+['t-high','t-low','t-crit'][x.band]+'">'+esc(HW_?HW_.b[x.band]:'')+'</span>'},
  {k:'pct',l:'HRA score',n:1,
   tt:'Achieved \\u00f7 possible points on this council\\u2019s own HRA row, on the template\\u2019s scale: '
    +(HW_?HW_.thr[0]+'+ = '+esc(HW_.b[0])+', '+HW_.thr[1]+'\\u2013'+(HW_.thr[0]-1)+' = '+esc(HW_.b[1])
     +', under '+HW_.thr[1]+' = '+esc(HW_.b[2]):'see the criteria card')
    +'. Not a coverage figure and not the combined UC risk score.',
   f:x=>hb(x.pct,HW_?HW_.thr[0]:79,HW_?HW_.thr[1]:60)},
  {k:'dr',l:'What makes it risky',ns:1,
   tt:'Indicators the portal scored 0 of 3 on this council\\u2019s own HRA row',
   f:x=>x.dr.length?('<span title="'+esc(x.dr.join(' | '))+'">'+x.dr.slice(0,2)
    .map(s=>esc(s.length>42?s.slice(0,42)+'\\u2026':s)).join(' \\u00b7 ')+'</span>'
    +(x.dr.length>2?'<span class="cnt"> +'+fmt(x.dr.length-2)+' more</span>':''))
   :'<span class="cnt">nothing scored 0 of 3'+(x.nz?' \\u00b7 '+fmt(x.nz)+' left un-scored':'')+'</span>'},
  {k:'vin',l:'Scored',f:x=>'<span class="cnt">'+esc(x.vin)+'</span>'},
  {k:'vp',l:CAMP[LCP]+' coverage',n:1,f:x=>hb(x.vp,90,80)},
  {k:'st',l:'Still missed',n:1,f:x=>fmt(x.st)},
  {k:'lo',l:'Not reached',n:1,tt:'Children left outside the round at this council in '+CAMP[LCP],
   f:x=>x.lo?('<b class="dn">'+fmt(x.lo)+'</b>'):'<span class="cnt">0</span>'},
  {k:'zr',l:'ZD reported',n:1,f:x=>fmt(x.zr)},
  {k:'zc',l:'ZD covered',n:1,tt:SCOV?CAMP[LCP]+'\\u2019s own covered figure for this council, same-round self-reported':'',
   f:x=>x.zc==null?'<span class="cnt">no figure</span>':(x.zc?fmt(x.zc):'<b class="dn">0</b>')}],
  UC,'pct',1);
 el('btnHRDx').onclick=()=>csvDownload('hrd_districts_'+_slug()+'.csv',
  ['Division','District','Tier','Channels flagged (of 6)','No-data channels',
   'HRA councils scored','HRA High Risk','HRA Medium Risk','HRA Low Risk','HRA achieved points',
   'HRA possible points','HRA score %','HRA vintage(s) in this district',
   (CAMP[LCP]+' coverage %')+'','Children still missed',
   'Still missed % of target','Children not reached','Zero-dose reported','Zero-dose covered',
   'Zero-dose covered %','Children reported with no covered figure','Priority councils (last 3)',
   'Nov-26 readiness %','MPQA assigned','MPQA reported','MPQA owed','MPQA under 70',
   'Routine OPV-3 %','EOC category','Afghan-bordering councils','Suggested monitors',
   'Monitors assigned (this browser)','Why it is here'],
  R0.map(o=>[o.dv?DNAME(o.dv):'',DNAME(o.d),o.tier,o.n,o.nd,o.h?o.h.n:'',o.hi,o.me,o.h?o.h.lo:'',
   o.h?o.h.ach:'',o.h?o.h.pos:'',o.hp==null?'':rnd(o.hp,1),
   o.h?Object.keys(o.h.v).map(j=>HW?HW.v[j]:'').join(' + '):'',
   o.vp==null?'':rnd(o.vp,1),o.cg?Math.round(o.cg.st):'',o.stp==null?'':rnd(o.stp,2),
   o.cg?Math.round(o.cg.lo):'',o.cg?o.cg.zr:'',o.cg?o.cg.zc:'',o.zpc==null?'':rnd(o.zpc,1),o.zgap,
   o.cg?o.cg.pri:'',o.rdn==null?'':rnd(o.rdn,1),o.mq?o.mq[0]:'',o.mq?o.mq[1]:'',
   o.owe==null?'':o.owe,o.ser==null?'':o.ser,o.ep==null?'':rnd(o.ep,1),critLab(o.d),o.cb,o.sug,
   AS[o.d]||0,o.wd.map(s=>s.replace(/<[^>]+>/g,'')).join(' | ')]));
 el('btnHRDUx').onclick=()=>csvDownload('hrd_union_councils_'+_slug()+'.csv',
  ['Tier','Division','District','Union council','UC code','HRA band','HRA score %',
   'HRA achieved','HRA possible','Indicators scored 0 of 3','Criteria left un-scored',
   'HRA file date',CAMP[LCP]+' coverage %','Still missed','Not reached','Zero-dose reported',
   'Zero-dose covered'],
  UC.map(x=>[x.tier,D2DV[x.d]?DNAME(D2DV[x.d]):'',DNAME(x.d),x.uc,x.code,HW?HW.b[x.band]:'',rnd(x.pct,1),x.ach,x.pos,
   x.dr.join(' | '),x.nz,x.vin,x.vp==null?'':rnd(x.vp,1),x.st,x.lo,x.zr,
   x.zc==null?'no figure filed':x.zc]));
}
"""


def crlf(s):
    return s.replace('\n', '\r\n')


EDITS = [
    # 1. tab id enters the allowlist.
    ('tabs', "'hcamp','c3','cpre'", "'hcamp','hrd','c3','cpre'"),
    # 2. nav button, straight after the merged comparison pane.
    ('nav',
     '   <button class="tab" data-tab="c3"><span class="tl">Comparison &amp; monitoring</span>'
     '<span class="badge" id="bC3">\u2013</span></button>\r\n',
     '   <button class="tab" data-tab="c3"><span class="tl">Comparison &amp; monitoring</span>'
     '<span class="badge" id="bC3">\u2013</span></button>\r\n'
     '   <button class="tab" data-tab="hrd"><span class="tl">High-risk district focus</span>'
     '<span class="badge" id="bHRD">\u2013</span></button>\r\n'),
    # 3. the pane's own accent, next to the c3 accent rule it follows.
    ('css', '.tab[data-tab="c3"],#p-c3{--tc:#c2410c}',
     '.tab[data-tab="c3"],#p-c3{--tc:#c2410c}\r\n'
     '.tab[data-tab="hrd"],#p-hrd{--tc:#9a3412}\r\n'
     '#p-hrd .pill.on{background:var(--tc);border-color:var(--tc)}\r\n'
     '#p-hrd select.hrdas{font:12.5px var(--font-sans);padding:3px 6px;border-radius:7px;'
     'border:1px solid var(--color-border);background:#fff}\r\n'
     '#p-hrd td .cnt{margin-left:4px}'),
    # 4. pane markup, appended after the merged c3 pane closes.
    ('pane', '<div class="cap" id="pcmc5"></div>\r\n</div>\r\n</div>\r\n</section>\r\n',
     '<div class="cap" id="pcmc5"></div>\r\n</div>\r\n</div>\r\n</section>\r\n' + crlf(PANE)),
    # 5. nav icon + render dispatch + badge chain.
    ('tabico', "Object.assign(TABICO,{hcamp:'flag',", "Object.assign(TABICO,{hrd:'target',hcamp:'flag',"),
    ('dispatch', 'c3:renderC3Half,', 'c3:renderC3Half,hrd:renderHRD,'),
    ('badges', 'c3Badge(); pcmBadge();', 'c3Badge(); hrdBadge(); pcmBadge();'),
    # 6. the two downloads go out as workbooks, like the other briefing tables.
    ('xlp', 'const XLP=/^(ptp_|hrmp_|nov26_focus_)/;', 'const XLP=/^(ptp_|hrmp_|nov26_focus_|hrd_)/;'),
    ('xltab', "nov26_focus_union_councils:'Focus union councils'};",
     "nov26_focus_union_councils:'Focus union councils',\r\n"
     " hrd_districts:'High-risk districts',hrd_union_councils:'HRA councils'};"),
    # 7. module JS, in front of the campaign-overview code it borrows cqDist from.
    ('js', '// ---------- Campaign overview (district performance + triangulation) ----------',
     crlf(JS) + '\r\n// ---------- Campaign overview (district performance + triangulation) ----------'),
    # 8. route into the new module from the campaign hub.
    ('hubchip', '<div class="hubchips"><button data-hl="cpre">Pre-campaign</button>',
     '<div class="hubchips"><button data-hl="hrd">High-risk district focus</button>'
     '<button data-hl="cpre">Pre-campaign</button>'),
]


def apply(t):
    for name, old, new in EDITS:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times (expected 1) - the master no longer '
                             'matches what this patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t):
    for name, old, new in reversed(EDITS):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times (expected 1) - not undoing '
                             'something this patch did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('ERR duplicate element ids after the new tab: %s' % ', '.join(dup[:12]))
    miss = [i for i in NEW_IDS if ids.count(i) != 1]
    if miss:
        raise SystemExit('ERR the new pane is missing an anchor id: %s' % ', '.join(miss))
    for fn in ('function hrdRows()', 'function renderHRD()', 'function hrdBadge()',
               'function hrdUCs(', 'hrd:renderHRD,'):
        if t.count(fn) != 1:
            raise SystemExit('ERR the module lost %r (%d copies)' % (fn, t.count(fn)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='report only')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'id="p-hrd"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the district focus module is not applied')
        v.text = unapply(v.text)
    else:
        v.require(not built, 'already applied (id="p-hrd" present)')
        v.text = apply(v.text)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  tab hrd %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                               v.delta(), 'added' if not a.unpatch else 'removed'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    print('OK hrd module master only - the other three variants are synced by push_master.py, '
          "which needs the owner's word")
    return 0


if __name__ == '__main__':
    sys.exit(main())
