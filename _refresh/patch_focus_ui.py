# -*- coding: utf-8 -*-
"""Build the "Where to focus for Nov-26" card on the transit-point tab (master only).

What it does
  * reads the two triangulation tables the tab already publishes (#tPTa district inventory, #tPTb the
    same union councils through the campaign and routine channels) and turns them into two shortlists:
    district units and union councils that more than one independent channel flags;
  * a district unit is counted once per channel that flags it, out of five: the transit-point channel
    itself (listed but silent, gone quiet, or filing in under a quarter of the month slots), the last
    campaign round (its transit councils reported zero-dose children and covered under half of them),
    routine EPI (OPV-3 under 80% across the same councils), the combined UC risk score (three or more
    very-high or high councils), and the HRMP field checks (20+ unvaccinated under-5s per 100 spot-survey
    checklists with 100+ checklists);
  * a union council is counted out of six: risk tier, campaign coverage, routine OPV-3, findings filed in
    two months or fewer, cross-border weight, and findings recorded under a council the KP map does not
    carry;
  * the SNID Nov-26 pre-campaign readiness gaps (NEAP) and the Nov-26 district scope (SND) ride beside
    the need count as execution columns, because the point of the list is who can act, not who scores.

Rules this build keeps
  * no PTP coverage percentage anywhere: the panel counts reports, not distinct children, and its own
    Coverage column is still unconfirmed with IDIMS;
  * the HRMP survey evidence is stated as children per 100 checklists, never as a percentage, and it can
    honestly pass 100 (DIKHAN logs 526 children over 511 checklists);
  * thresholds are the published bands already used on the tab and the risk page (covered 80/50, OPV-3 80,
    risk tier bands, the front-page map's very-high+high count), not new invented cut-offs - see
    _focus/focus_probe.py in the session directory for the distributions they were chosen against;
  * the district join uses PTP.dr, the raw IDIMS spelling. CHITRAL and the two unsplit WAZIR-S units have
    no campaign district of that name, so their risk and readiness cells read a dash rather than a guess;
  * campaign covered figures for the last round are the round's own self-report, and routine OPV-3 is a
    cumulative EPI window - both stated in every caption and on every slide.
Only the master is touched; the other three variants carry no PTPM payload and syncing them is a
publishing action that needs the owner's word.
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = lambda x: x.replace('\n', '\r\n')
REL = 'index.html'

HTML_OLD = '<div class="cap" id="capPTu"></div>\r\n</div>\r\n</section>'
HTML_NEW = """<div class="cap" id="capPTu"></div>
</div>
<div class="card" id="cFOC">
<div class="tblhdr"><h3 style="margin:0">Where to focus for SNID Nov-26: district units the channels flag</h3><div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntFOCd"></span><button class="btn" id="btnFOCd" title="Every district unit in scope with its channel flags, not only the ones on the shortlist">Download (CSV)</button></div></div>
<div class="cap" id="focLead" style="margin-top:0"></div>
<div class="rkpills" id="focPills"></div>
<div class="scroll"><table id="tFOCd"></table></div>
<div class="cap" id="capFOCd"></div>
<div class="tblhdr" style="margin-top:16px"><h3 style="margin:0">Union councils to brief teams on</h3><div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntFOCu"></span><button class="btn" id="btnFOCu" title="Every union council the transit point panel reports, with its flags">Download (CSV)</button></div></div>
<div class="rkpills" id="focUPills"></div>
<div class="scroll"><table id="tFOCu"></table></div>
<div class="cap" id="capFOCu"></div>
</div>
</section>""".replace('\n', '\r\n') + '\r\n'

TAIL_OLD = (' PTPX={sig:ptpSig(),R:R,UR:UR,DI:DI,SLab:SLab,')
TAIL_NEW = (' const RF=focDist(R,{one:one,SLab:SLab,camp:CAMP[LCP]}), UF=focUC(UR,{one:one});\r\n'
            ' PTPX={sig:ptpSig(),RF:RF,UF:UF,R:R,UR:UR,DI:DI,SLab:SLab,')
TAIL_T3 = ('sF:sF};\r\n')
TAIL_T4 = ('sF:sF};\r\n drawFOC(PTPX,RF,UF);\r\n')

JS_START = '// ---------- FOCUS FOR THE NEXT ROUND: district and union-council shortlists'
JS = JS_START + ''' ----------
// Five independent channels decide whether a district unit is on this list and six decide whether a union
// council is. Each channel is a different source measuring a different thing, so a unit appears only where
// the sources disagree or agree on a gap. None of it is a coverage measure of the transit-point network:
// the panel counts reports, not distinct children, and its own Coverage column stays unconfirmed.
// The flags are judged on the whole reporting window, not on the period picked above: this is a list of who
// can act before the round, and a one-month view would otherwise drop units for a January with no filing.
var FOCX=null;
const FOC={min:100,thin:25,cover:50,epi:80,hv:3,zmin:5,cb:5000,ucap:150};
function focHv(){const H={};riskAll().forEach(r=>{const g=H[r.d]=H[r.d]||{vh:0,hi:0};
 if(r.tier==='vh')g.vh++;else if(r.tier==='hi')g.hi++;});return H;}
function focRiskByCode(){const B={};riskAll().forEach(r=>{B[r.c]=r;});return B;}
function focWin(i){const KI={};PTP.k.forEach((k,j)=>{KI[k]=j});let rows=0,mon=0,last=-1;
 (PTP.d[i][3]||[]).forEach(b=>{const a=b[1]||[];rows+=(a[KI.rows]||0);mon+=(a[KI.months]||0);
  if((a[KI.rows]||0)>0&&b[0]>last)last=b[0];});
 return{rows:rows,mon:mon,last:last,monp:mon/(PTP.yr.length*12)*100};}
function focRdy(raw){
 if(typeof NEAP==='undefined'||!NEAP||!NEAP.d||!NEAP.d[raw])return null;
 const v=NEAP.d[raw], g=k=>{const j=NEPK.indexOf(k); return j<0||v[j]==null||v[j]<0?null:v[j];}, miss=[];
 [['dpec','the DPEC',100],['must','mandatory members',100],['aic','AIC training',90],['mpv','micro-plan validation',90]]
  .forEach(p=>{const x=g(p[0]); if(x==null||x<p[2])miss.push(p[1]+' '+(x==null?'is not reported':pc(x)));});
 return {dpec:g('dpec'),must:g('must'),aic:g('aic'),mpv:g('mpv'),miss:miss};}
function focInScope(raw){return (typeof SND==='undefined'||!SND||!SND.d)?null:SND.d.some(r=>r[0]===raw);}
function focDist(R,C){
 const H=focHv(), S=ptpRiskSignals(), LY=PTP.yr.length-1;
 return R.map(x=>{
  const w=focWin(x.i), h=H[x.raw], sv=S.d[x.raw], rd=focRdy(x.raw);
  const quiet=x.posts>0&&!w.rows, lapsed=x.posts>0&&w.last>=0&&w.last<LY&&!quiet,
   thin=!quiet&&!lapsed&&w.monp<FOC.thin;
  const gap=Math.max(0,(x.zrc||0)-(x.zcv||0)), ev=[], act=[];
  if(quiet){ev.push(fmt(x.posts)+' transit points listed with nothing filed since '+PTP.yr[0]);
   act.push('restart the IDIMS entry chain at those posts');}
  else if(lapsed){ev.push('transit reporting stopped in '+PTP.yr[w.last]+' ('+fmt(x.posts)+' points still listed)');
   act.push('confirm which points still operate, then restart daily filing');}
  else if(thin){ev.push('filed in only '+pc(w.monp)+' of the month slots the window offers');
   act.push('fix the reporting cadence, because every finding under this row is an undercount');}
  if(x.zn>=FOC.zmin&&x.zp!=null&&x.zp<FOC.cover){
   ev.push(fmt(gap)+' of the '+fmt(x.zrc)+' zero-dose children its transit councils reported in '+C.camp+' have no covered figure behind them ('+pc(x.zp)+' covered)');
   act.push('put a standing team and a register check on the '+fmt(gap)+' children the round left uncovered');}
  if(x.euc>=FOC.zmin&&x.ep!=null&&x.ep<FOC.epi){
   ev.push('routine OPV-3 '+pc(x.ep)+' across the '+fmt(x.euc)+' transit councils the EPI file carries');
   act.push('run a routine catch-up with the facilities, not a campaign sweep alone');}
  if(h&&h.vh+h.hi>=FOC.hv){
   ev.push(fmt(h.vh)+' very-high and '+fmt(h.hi)+' high-risk councils on the combined score');
   act.push('carry those councils into the micro-plan review as named targets');}
  if(sv&&sv.srv>=FOC.min&&sv.rate!=null&&sv.rate>=20){
   ev.push(fmt(Math.round(sv.rate))+' unvaccinated under-5s found per 100 HRMP spot-survey checklists ('+fmt(sv.srv)+' checklists)');
   act.push('survey the same posts a second time during the round');}
  return {i:x.i, raw:x.raw, dn:x.dn, dv:x.dv, posts:x.posts, ucs:x.ucs, onmap:x.onmap, rep:x.rep, ucS:x.ucS,
   mon:x.mon, monp:w.monp, rows:x.rows, zd:x.zd, zpr:x.zpr, zn:x.zn, zrc:x.zrc, zcv:x.zcv, zp:x.zp, gap:gap,
   euc:x.euc, ep:x.ep, hv:h?h.vh+h.hi:null, vh:h?h.vh:null, srv:sv?sv.srv:null, srate:sv?sv.rate:null,
   last:w.last, quiet:quiet, lapsed:lapsed, thin:thin, yld:x.rows>=100&&x.zpr!=null&&x.zpr<=S.cap?x.zpr:null,
   rdy:rd?rd.miss:null, scope:focInScope(x.raw), n:ev.length, ev:ev, act:act};})
  .sort((a,b)=>b.n-a.n||b.gap-a.gap||((b.hv||0)-(a.hv||0)));}
function focUC(UR,C){
 const B=focRiskByCode();
 return UR.map(x=>{
  const r=B[x.c], gap=Math.max(0,(x.zr||0)-(x.zc||0)), ev=[], act=[];
  if(r&&(r.tier==='vh'||r.tier==='hi')){
   ev.push('combined risk '+pc(r.pct)+' ('+RTL[r.tier][0]+(r.why.length?': '+r.why.slice(0,2).join(', '):'')+')');
   act.push('hold its risk drivers as named targets in the council micro-plan');}
  if(x.zr!=null&&x.zr>=FOC.zmin&&(x.zc==null||(x.zp!=null&&x.zp<FOC.cover))){
   ev.push(fmt(x.zr)+' zero-dose reported in '+CAMP[LCP]+' with '+(x.zc==null?'no covered figure filed at all':fmt(x.zc)+' covered, '+pc(x.zp)));
   act.push('a house-to-house register check on the '+fmt(gap)+' children left uncovered');}
  if(x.ep!=null&&x.ep<FOC.epi){ev.push('routine OPV-3 '+pc(x.ep));
   act.push('line-listing for the routine catch-up');}
  if(!C.one&&x.zd>0&&x.mon<=2){ev.push(fmt(x.zd)+' zero-dose findings filed in only '+x.mon+' month'+(x.mon===1?'':'s'));
   act.push('keep the post reporting daily so the findings can be followed up');}
  if(!C.one&&x.cbu>=FOC.cb){ev.push(fmt(x.cbu)+' cross-border under-10 children counted');
   act.push('a standing team at the crossing plus the border register');}
  if(x.zd>0&&!x.map){ev.push('findings recorded, but the council is not on the KP union-council map');
   act.push('fix the council code before the round, or the micro-plan cannot see it');}
  return {c:x.c, u:x.u, t:x.t, dn:x.dn, dv:x.dv, posts:x.posts, mon:x.mon, rows:x.rows, zd:x.zd,
   cbu:x.cbu, map:x.map, zr:x.zr, zc:x.zc, zp:x.zp, ep:x.ep, gap:gap, n:ev.length, ev:ev, act:act,
   tier:r?r.tier:'', pct:r?r.pct:null, pts:r?r.pts:null, mx:r?r.max:null, cd:r?r.d:''};})
  .sort((a,b)=>b.n-a.n||b.gap-a.gap||b.zd-a.zd);}
let FOCMIN=2, FUCMIN=2;
function drawFOC(X,RF,UF){
 const p1=v=>v==null?'\\u2013':(Math.round(v*10)/10).toFixed(1);
 const cb=(v,hi,lo)=>v==null?'\\u2013':'<span style="color:'+(v>=hi?'#047857':v>=lo?'#92400E':'#991B1B')+';font-weight:600">'+p1(v)+'</span>';
 const D=RF.filter(x=>x.n>=FOCMIN), U=UF.filter(x=>x.n>=FUCMIN);
 const two=RF.filter(x=>x.n>=2), three=RF.filter(x=>x.n>=3), sil=RF.filter(x=>x.quiet||x.lapsed||x.thin);
 const gapAll=RF.reduce((s,x)=>s+x.gap,0), ur=UF.filter(x=>x.n>=2),
  ug=UF.reduce((s,x)=>s+x.gap,0), ugF=ur.reduce((s,x)=>s+x.gap,0), unm=UF.filter(x=>x.zd>0&&!x.map).length;
 el('focLead').innerHTML='<b>'+fmt(two.length)+' of '+fmt(RF.length)+' district units in scope are flagged by two or more independent channels'+
  (three.length?', '+fmt(three.length)+' of them by three or more':'')+'.</b> The channels are the transit-point panel itself, '+
  esc(X.camp||CAMP[LCP])+' zero-dose coverage, routine OPV-3 in the same union councils, the combined UC risk score and the HRMP field checks - '+
  'five sources that count different things, so a unit only appears here when they agree on a gap. '+
  fmt(gapAll)+' zero-dose children reported on transit councils have no covered figure behind them, and '+
  fmt(sil.length)+' units have a transit channel that has never filed, stopped filing, or files in less than a quarter of the months. '+
  'Nothing on this card is a coverage percentage of the transit network.';
 el('focPills').innerHTML=[[3,'Priority (3+ channels)'],[2,'Two or more'],[1,'Any channel'],[0,'Every unit in scope']]
  .map(p=>'<button data-f="'+p[0]+'" class="'+(FOCMIN===p[0]?'on':'')+'">'+p[1]+' ('+fmt(RF.filter(x=>x.n>=p[0]).length)+')</button>').join('');
 el('focPills').querySelectorAll('button').forEach(b=>b.onclick=()=>{FOCMIN=+b.dataset.f;drawFOC(X,RF,UF);});
 drawTable('tFOCd',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'dv',l:'Division'},
  {k:'cr',l:'UC criteria',sv:x=>{const v=critIx(x.raw); return v==null?99:v;},f:x=>critTag(x.raw)},
  {k:'n',l:'Channels',n:1,sv:x=>x.n,f:x=>x.n?('<b style="color:'+(x.n>=3?'#9f1239':x.n===2?'#dc2626':'#d97706')+'">'+x.n+' of 5</b>'):'<span class="cnt">\\u2013</span>',
   tt:'How many of the five independent channels flag this unit: transit-point channel, campaign coverage, routine OPV-3, combined risk score, HRMP field checks'},
  {k:'scope',l:'Nov-26 scope',sv:x=>x.scope===null?-1:x.scope?0:1,f:x=>x.scope===null?'<span class="cnt">not in the NEAP list</span>':(x.scope?'<span class="tag t-high">In</span>':'<span class="tag t-none">Out</span>'),
   tt:'Whether the district unit is one of the SNID Nov-26 campaign districts in the scope file'},
  {k:'gap',l:'Uncovered zero-dose',n:1,f:x=>x.gap?('<b class="dn">'+fmt(x.gap)+'</b>'):'<span class="cnt">\\u2013</span>',
   tt:'Zero-dose children reported on this unit\\u2019s transit councils in the last round minus those the same round recorded as covered'},
  {k:'zp',l:'Covered %',n:1,f:x=>cb(x.zp,80,50),tt:'Covered / reported over the transit councils that carry both figures'},
  {k:'ep',l:'OPV-3 %',n:1,f:x=>pE(x.ep),tt:'Routine OPV-3 across the same councils \\u00b7 cumulative EPI window, not the selected period'},
  {k:'monp',l:'Channel months %',n:1,f:x=>cb(x.monp,75,50),tt:'Share of the month slots in the whole '+PTP.win+' window for which the unit filed at least one report - the channel flag ignores the period above so the shortlist stays the same whichever month is picked'},
  {k:'yld',l:'ZD per 100 reports',n:1,f:x=>x.yld==null?'<span class="cnt">\\u2013</span>':fmt(Math.round(x.yld)),tt:'Only where 100+ reports are logged and the rate is plausible; report counts, never children'},
  {k:'hv',l:'Very-high + high UCs',n:1,f:x=>x.hv==null?'<span class="cnt">no campaign match</span>':(x.hv?('<b class="dn">'+fmt(x.hv)+'</b>'):'0'),tt:'Councils on the combined UC risk score; a dash means IDIMS files this unit under a name the campaign data does not use'},
  {k:'srate',l:'Unvacc. per 100 surveys',n:1,f:x=>x.srate==null?'<span class="cnt">\\u2013</span>':(x.srv<FOC.min?'<span class="cnt">'+fmt(Math.round(x.srate))+' of '+fmt(x.srv)+'</span>':fmt(Math.round(x.srate))),tt:'HRMP spot surveys: unvaccinated under-5s per 100 checklists. The two units are checklists and children, so one child per survey reads 100 - never a percentage'},
  {k:'rdy',l:'Nov-26 readiness gaps',ns:1,f:x=>x.rdy==null?'<span class="cnt">no NEAP row</span>':(x.rdy.length?x.rdy.map(s=>'<span class="tag t-crit">'+esc(s)+'</span>').join(' '):'<span class="tag t-high">Complete</span>')},
  {k:'why',l:'Why it is on the list',ns:1,f:x=>esc(x.ev.join(' \\u00b7 '))||'<span class="cnt">no channel flags it</span>'},
  {k:'act',l:'What to do before the round',ns:1,f:x=>esc(x.act.join('; '))||'<span class="cnt">nothing to escalate</span>'}],
  D,'n',-1);
 el('cntFOCd').textContent=fmt(D.length)+' of '+fmt(RF.length)+' units \\u00b7 '+X.SLab;
 el('capFOCd').textContent='Sorted by channels flagged, then by the number of children the last round reported and did not cover. '+
  'A channel flags a unit on the whole '+PTP.win+' window, so the shortlist does not change with the period above; the report, finding, '+
  'post and council-count columns do follow it, which is why a month view can leave the flags filled while those columns empty. '+
  'Covered figures are '+esc(CAMP[LCP])+'\\u2019s own export, not yet confirmed by a later round. '+
  'A unit IDIMS files under a name the campaign data does not use ('+esc(['KOLAIPALAS','CHITRAL','WAZIR-S'].filter(d=>PTP.dr.indexOf(d)>=0).join(', '))+') '+
  'can still be flagged on its own channel and findings, but it carries no risk or readiness cell, because the split cannot be recovered from the name. '+
  'Nov-26 readiness is the four pre-campaign gates the core team still has to close: the DPEC, mandatory members, AIC training and validated micro-plans.';
 el('btnFOCd').onclick=()=>csvDownload('nov26_focus_districts_'+_slug()+'.csv',
  ['Division','District','IDIMS district code','UC criteria','Channels flagged (of 5)','In Nov-26 campaign scope',
   'Transit points listed','PTPs reporting in period','UCs reporting in period','UCs in roster','Channel months % (whole window)',
   'Reports logged','Zero-dose findings','Zero-dose per 100 reports','Campaign zero-dose reported on transit councils',
   'Campaign covered','Children with no covered figure','Campaign covered %','UCs in EPI data','Routine OPV-3 %',
   'Very-high UCs','Very-high plus high UCs','HRMP spot-survey checklists','Unvaccinated under-5s per 100 checklists',
   'Nov-26 readiness gaps','Why it is on the list','What to do before the round'],
  RF.map(x=>[x.dv,x.dn,x.raw,critLab(x.raw),x.n,x.scope===null?'':(x.scope?'Yes':'No'),x.posts,x.rep,x.ucS,x.ucs,
   p1(x.monp),x.rows,x.zd,x.yld==null?'':p1(x.yld),x.zrc,x.zcv,x.gap,x.zp==null?'':p1(x.zp),x.euc,
   x.ep==null?'':p1(x.ep),x.vh==null?'':x.vh,x.hv==null?'':x.hv,x.srv==null?'':x.srv,
   x.srate==null?'':p1(x.srate),(x.rdy||[]).join('; '),x.ev.join(' | '),x.act.join(' | ')]));
 el('focUPills').innerHTML=[[3,'Priority (3+ flags)'],[2,'Two or more'],[1,'Any flag'],[0,'Every council the panel reports']]
  .map(p=>'<button data-f="'+p[0]+'" class="'+(FUCMIN===p[0]?'on':'')+'">'+p[1]+' ('+fmt(UF.filter(x=>x.n>=p[0]).length)+')</button>').join('');
 el('focUPills').querySelectorAll('button').forEach(b=>b.onclick=()=>{FUCMIN=+b.dataset.f;drawFOC(X,RF,UF);});
 drawTable('tFOCu',[
  {k:'u',l:'Union council',f:x=>'<b>'+esc(x.u)+'</b>'},
  {k:'dn',l:'District'},
  {k:'t',l:'Tehsil'},
  {k:'c',l:'UC code',f:x=>'<span class="cnt">'+esc(x.c)+'</span>'},
  {k:'n',l:'Flags',n:1,sv:x=>x.n,f:x=>x.n?('<b style="color:'+(x.n>=3?'#9f1239':x.n===2?'#dc2626':'#d97706')+'">'+x.n+' of 6</b>'):'<span class="cnt">\\u2013</span>',
   tt:'Risk tier, campaign coverage, routine OPV-3, thin filing with findings, cross-border weight, findings outside the UC map'},
  {k:'tier',l:'Risk',sv:x=>['vh','hi','me','lo',''].indexOf(x.tier),f:x=>x.tier?rkTag(x.tier):'<span class="cnt">no score</span>'},
  {k:'zd',l:'Zero-dose found',n:1,tt:'Report counts in the selected period, not distinct children'},
  {k:'posts',l:'PTPs',n:1},
  {k:'mon',l:'Months filed',n:1},
  {k:'zr',l:'Campaign reported',n:1,f:x=>x.zr==null?'<span class="cnt">\\u2013</span>':fmt(x.zr)},
  {k:'zc',l:'Campaign covered',n:1,f:x=>x.zc==null?'<span class="cnt">\\u2013</span>':fmt(x.zc)},
  {k:'gap',l:'With no covered figure',n:1,f:x=>x.gap?('<b class="dn">'+fmt(x.gap)+'</b>'):'<span class="cnt">\\u2013</span>'},
  {k:'ep',l:'OPV-3 %',n:1,f:x=>pE(x.ep)},
  {k:'cbu',l:'CB under-10',n:1},
  {k:'map',l:'On UC map',sv:x=>-x.map,f:x=>x.map?'<span class="tag t-high">Yes</span>':'<span class="tag t-crit">No</span>'},
  {k:'why',l:'Why it is on the list',ns:1,f:x=>esc(x.ev.join(' \\u00b7 '))||'<span class="cnt">no channel flags it</span>'},
  {k:'act',l:'What to do',ns:1,f:x=>esc(x.act.join('; '))||'<span class="cnt">nothing to escalate</span>'}],
  U.slice(0,FOC.ucap),'n',-1);
 el('cntFOCu').textContent=fmt(U.length)+' councils flagged \\u00b7 top '+fmt(Math.min(U.length,FOC.ucap))+' shown \\u00b7 '+X.SLab;
 el('capFOCu').textContent='Councils the transit panel reports, ranked by how many channels flag them and then by the children the last round '+
  'left uncovered. '+fmt(ur.length)+' councils are flagged by two or more of the six checks and hold '+fmt(ugF)+
  ' of the '+fmt(ug)+' children the panel reports with no covered figure; '+unm+' councils have findings recorded under a code the KP union-council map does not carry, '+
  'so they cannot reach a micro-plan until the coding is fixed. The thin-filing and cross-border checks only fire on a whole-window view, because a single month '+
  'cannot show a cadence; posts, months and findings follow the period above, while risk, campaign and routine columns are the published rosters and do not. '+
  'A dash means that source has no row for the council, not that it found nothing. '+
  'The campaign covered figures are the round\\u2019s own export and routine OPV-3 is a cumulative EPI window; neither is a measure of the transit point.';
 el('btnFOCu').onclick=()=>csvDownload('nov26_focus_union_councils_'+_slug()+'.csv',
  ['Division','District','Tehsil','Union council','UC code','Flags (of 6)','Risk tier','Risk score %','Risk points',
   'Points possible','PTPs reporting','Months filed','Reports logged','Zero-dose findings','Cross-border under-10',
   'Campaign reported','Campaign covered','Children with no covered figure','Campaign covered %','Routine OPV-3 %',
   'On UC map','Why it is on the list','What to do'],
  UF.map(x=>[x.dv,x.dn,x.t,x.u,x.c,x.n,x.tier?RTL[x.tier][0]:'',x.pct==null?'':p1(x.pct),x.pts,x.mx,x.posts,x.mon,
   x.rows,x.zd,x.cbu,x.zr==null?'':x.zr,x.zc==null?'':x.zc,x.gap,x.zp==null?'':p1(x.zp),x.ep==null?'':p1(x.ep),
   x.map?'Yes':'No',x.ev.join(' | '),x.act.join(' | ')]));
 FOCX={sig:X.sig,RF:RF,UF:UF,D:D,U:U,two:two,three:three,sil:sil,gapAll:gapAll,ug:ug,ugF:ugF,ur:ur.length,unm:unm,
  SLab:X.SLab,camp:CAMP[LCP],one:X.one,MDen:X.MDen,MSl:X.MSl};
}
function focCtx(){if(typeof PTP==='undefined'||!PTP||!PTP.d||!PTP.d.length)return null;
 if(!FOCX||!PTPX||PTPX.sig!==ptpSig()||FOCX.sig!==ptpSig())renderPTP();
 return FOCX&&FOCX.sig===ptpSig()?FOCX:null;}
'''
JS_LAST = 'return FOCX&&FOCX.sig===ptpSig()?FOCX:null;}\n'

EDITS = [(HTML_OLD, HTML_NEW), (TAIL_OLD, TAIL_NEW), (TAIL_T3, TAIL_T4)]


def patch(v, dry):
    s = v.text
    for probe in ('focDist', 'drawFOC', 'tFOCd', 'focPills', 'FOCX'):
        v.require(s.count(probe) == 0, 'already present (%s)' % probe)
    v.require(s.count(JS_START) == 0, 'the js block anchor is not usable')
    v.require(s.count('function renderSurv(){') == 1, 'the js insertion anchor is not unique')
    for old, new in EDITS:
        v.require(s.count(old) == 1, 'anchor found %d times: %r' % (s.count(old), old[:70]))
    js = CRLF(JS.lstrip('\n'))
    v.require(js.startswith(JS_START) and js.endswith(CRLF(JS_LAST)), 'the js block lost its shape')
    v.require('\r\r' not in js, 'the js block carries a doubled CR')
    s = s.replace('function renderSurv(){', js + 'function renderSurv(){', 1)
    for old, new in EDITS:
        s = s.replace(old, new, 1)
    for probe, n in (('function focDist', 1), ('function focUC', 1), ('function drawFOC', 1),
                     ('function focCtx', 1), ("drawFOC(PTPX,RF,UF)", 1), ('RF:focDist(R,', 0),
                     ("const RF=focDist(R,", 1), ("'Channels',n:1", 1), ('of 6</b>', 1),
                     ('nov26_focus_districts_', 1), ('nov26_focus_union_councils_', 1),
                     ('id="tFOCd"', 1), ('id="tFOCu"', 1), ('focUPills', 3)):
        v.require(s.count(probe) == n, '%r occurs %d times after the patch (want %d)' % (probe, s.count(probe), n))
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    print('   js +%d chars, %d anchors, net %+d chars'
          % (len(js), len(EDITS) + 1, sum(len(n) - len(o) for o, n in EDITS) + len(js)))
    if not dry:
        dashpatch.write_variants([v])


def unpatch(v, dry):
    """Strip an applied card so the thresholds can be revised and re-applied."""
    s = v.text
    a, b = s.find(JS_START), s.find('function renderSurv(){')
    v.require(a > 0 and b > a, 'not applied: the js block is not delimited')
    s = s[:a] + s[b:]
    for old, new in EDITS:
        v.require(s.count(new) == 1, 'reversal did not match: %r' % new[:70])
        s = s.replace(new, old, 1)
    for probe in ('focDist', 'focUC', 'drawFOC', 'focCtx', 'tFOCd', 'focPills', 'FOCX', 'nov26_focus'):
        v.require(probe not in s, '%s survived the removal' % probe)
    v.text = s
    dashpatch.assert_crlf(v)
    print('   removed the Nov-26 focus card')
    if not dry:
        dashpatch.write_variants([v])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true',
                    help='remove a previously applied card so the thresholds can be revised')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    print('variants: ' + ', '.join('%s %s' % (v.rel, v.md5()[:8]) for v in vs))
    sel = [x for x in vs if x.rel == REL]
    if len(sel) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % REL)
    v = sel[0]
    if 'const PTP = ' not in v.text or 'const PTPM = ' not in v.text:
        raise SystemExit('%s has no PTP or PTPM payload' % v.rel)
    print('%s master only (%s)' % ('un-patching' if a.unpatch else 'patching', v.rel))
    (unpatch if a.unpatch else patch)(v, a.dry_run)
    print('   %s: %.1f KB -> %.1f KB (%+.1f KB)'
          % (v.rel, len(v.orig) / 1024.0, len(v.text) / 1024.0, v.delta() / 1024.0))
    print('   md5 %s' % v.md5())
    if a.dry_run:
        print('DRY RUN: nothing written.')
    else:
        print("master only: the other three variants follow only on the owner's word.")


if __name__ == '__main__':
    main()
