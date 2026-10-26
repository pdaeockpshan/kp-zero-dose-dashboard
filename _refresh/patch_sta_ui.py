# -*- coding: utf-8 -*-
"""Insert the HRMP search-team block (const STA) into the index.html master.

Adds, in the master only:
  1. `const STA = {...}` right after `const MTM = {...};`, filled from _refresh/out/sta.json so the
     block is live the moment the master is patched; later refreshes go through `refresh.py run
     --only sta`.
  2. One card under the mobile-team card with six tables: tSTf (the two forms), tSTd (the same forms
     by district over the 21 measures), tSTl (the antigen ladder), tSTi (the checklist items), tSTk
     (activity reports matched to checklists on district + team + month) and tSTe (the same districts
     in the facility EPI register), each with its own count line and CSV, plus one caption.
  3. `staTab()` next to the other PTP cache helpers, and the render block inside `renderPTP()`, after
     the mobile-team block and before the district inventory table.
  4. Three corrections to the mobile-team caption it makes stale. `const MTM` publishes these same two
     search-team forms from the 21-Apr-2025 export, so its claims that all six forms stopped there and
     that nothing built on the target/coverage family is published while that question is open are both
     true of that pull and no longer true of the page. Each is replaced with a sentence that points at
     this block instead of contradicting it.

Design rules the patch depends on, all established by extract_sta.py:
  - The two workbooks pulled 28-Sep-2026 are the source of record for these forms. They contain the
    April CSV of the same form in full apart from the ids counted in `vint.older_only`, and one of
    those is carried into this payload, so the block says which vintage it reads and the two blocks are
    never added together.
  - The form's bare dose columns are blank in every row. What it carries is the target / coverage pair
    per antigen, so the pair is the measure: target, covered, and the rows that contradicted
    themselves, published beside them as their own column rather than silently dropped.
  - No percentage is drawn from that pair except one per-100 column in the ladder, whose tooltip states
    that the denominator is the same form's own target. A district coverage rate is not claimable from
    it and none appears.
  - A ladder column whose coverage is contradicted in more than a fifth of the rows that recorded it is
    withheld by the extractor and named here with its numbers (`STA.agvoid`), so a withheld antigen is
    a row on the table, not a missing row.
  - The checklist item columns answer 1, 0 or nothing, which is decodable without a report definition,
    so yes / no / left-blank is published per item and the share is taken over answered rows only - a
    blank is not a no. The fields no row ever answered (`STA.inever`) are named, not graphed.
  - Ladder and item cells are district x year, so the month picker cannot narrow those two tables; it
    narrows the district grid and the forms table, and both say which they follow.
  - Teams and union councils are district-scoped unions and the province figure is the sum of those, so
    they are blank in a period view, and the activity-to-checklist link is published as matched counts,
    never as a compliance rate over unmatched months.
  - The EPI comparison puts two registers of the same districts side by side for the months both
    cover. It is a comparison, not a numerator over a denominator, and the extractor aborts if a
    search-team figure exceeds the whole facility register.

All inserted text is written with CRLF so the file's line endings stay uniform.
Every anchor is asserted to occur exactly once before editing; nothing is written unless the patch
applies cleanly.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

MASTER = 'index.html'
PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sta.json')

A_CONST = 'const SURVW = {'
A_CARD = '<div class="cap" id="capMTf"></div>\r\n</div>\r\n'
A_CACHE = 'function ptBadge(){'
A_RENDER = ' // district inventory table\r\n'
A_HINT = ('the two HRMP blocks and the union-council listing. The two HRMP blocks follow the same '
          'pick, but none of those nine forms was still being filed after Apr-2025, so a later period '
          'is a dash there rather than nothing filed.')
HINT_NEW = ('the three HRMP blocks and the union-council listing. All three follow the same pick, but '
            'the mobile-team block stops where its Apr-2025 export stops - four of its six forms were '
            'not being filed after that - while the search-team block below it runs to Sep-2026, so a '
            'late period is a dash in one and a figure in the other.')

# (old, new) applied to the mobile-team caption this block makes stale. Each must occur exactly once.
FIX = [
    ('and never re-pulled since: ',
     'and not re-pulled into this payload since: '),
    ('All six stopped being filed long before the daily reports did: ',
     'All six of these files stop inside Apr-2025, because that is when the pull was taken: '),
    ("'filled in.'),",
     "'filled in. Two of these six - the search-team activity report and its monitoring checklist - "
     "were re-pulled into a September 2026 workbook and are published again in the block below, "
     "antigen by antigen, so read that one for those two forms and this one for the other four.'),"),
    ('on them is published while that question is open. Also held out:',
     'on them is published here while that question is open. For the search-team activity form it has '
     'since been answered inside the owner\'s own workbook, and that block is the one below. Also '
     'held out:'),
]

CARD = (
 '<div class="card" id="cSTa" style="display:none">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Search teams: the same two HRMP forms, read from the '
 'Sep-2026 workbooks instead of the April export</h3><div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTf"></span><button class="btn" id="btnSTf">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTf"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The two forms district by district</h3>'
 '<div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTd"></span><button class="btn" id="btnSTd">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTd"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The antigen ladder: children targeted against children '
 'covered, district by year</h3><div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTl"></span><button class="btn" id="btnSTl">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTl"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">What the monitoring checklists actually answered</h3>'
 '<div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTi"></span><button class="btn" id="btnSTi">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTi"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Activity reports and checklists matched on district, team '
 'number and month</h3><div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTk"></span><button class="btn" id="btnSTk">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTk"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The same districts in the facility EPI register</h3>'
 '<div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntSTe"></span><button class="btn" id="btnSTe">Download (CSV)</button>'
 '</div></div>\r\n'
 '<div class="scroll"><table id="tSTe"></table></div>\r\n'
 '<div class="cap" id="capSTa"></div>\r\n'
 '</div>\r\n'
)

CACHE = r"""var _STA=null;
function staTab(){
 if(_STA&&_STA.v===STA)return _STA;
 const y={},m={},e={},k={},t={},l={},i={};
 STA.d.forEach(r=>{const a={},b={};
  (r[1]||[]).forEach(c=>{a[c[0]]=c[1];}); (r[2]||[]).forEach(c=>{b[c[0]]=c[1];});
  y[r[0]]=a; m[r[0]]=b;});
 STA.ev.forEach(r=>{e[r[0]]=r});
 STA.lnk.forEach(r=>{k[r[0]]=r});
 STA.tri.forEach(r=>{t[r[0]]=r});
 STA.al.forEach(r=>{((l[r[0]]=l[r[0]]||{})[r[1]]=l[r[0]][r[1]]||{})[r[2]]=r;});
 STA.it.forEach(r=>{((i[r[0]]=i[r[0]]||{})[r[1]]=i[r[0]][r[1]]||{})[r[2]]=r;});
 return _STA={v:STA,y:y,m:m,e:e,k:k,t:t,l:l,i:i};
}
"""

RENDER = r""" // HRMP search teams: the two forms the owner re-pulled into the Sep-2026 workbooks
 const SSC=el('cSTa');
 if(SSC){
  if(typeof STA==='undefined'||!STA||!STA.d||!STA.d.length||!STA.mk||!STA.forms
     ||STA.yr.length!==nY){
   SSC.style.display='none';
  }else{
  SSC.style.display='';
  const SS=staTab(), MM={}, OWN={}, SP={}, TRIO={}, MLb={}, YJ=(one&&yi>=0?[yi]:ALLJ);
  STA.mk.forEach((k,x)=>{MM[k]=x; MLb[k]=STA.mkl[x]});
  STA.forms.forEach(f=>{f.cols.forEach(k=>{(OWN[k]=OWN[k]||[]).push(f.id)});
   SP[f.id]=!one||(mv?(STA.first[f.id]<=yv*100+mv&&yv*100+mv<=STA.last[f.id])
    :(STA.first[f.id]<=yv*100+12&&STA.last[f.id]>=yv*100+1));});
  STA.pairs.forEach(p=>{const b=p.id.slice(0,2), k=[b+p.id[2], b+'C', b+'V'];
   TRIO[k[0]]={p:p, w:'target'}; TRIO[k[1]]={p:p, w:'covered'}; TRIO[k[2]]={p:p, w:'voided rows'}});
  const WS={target:'the children the same row said it was aiming at',
   covered:'the children the same row reported reaching',
   'voided rows':'the rows that recorded this pair and contradicted themselves, so they add to '
    +'neither of the two figures beside it'};
  const SCOPE=DI.filter(i=>SS.y[i]);
  const CL=i=>mv?SS.m[i][yi*12+mv-1]:SS.y[i][yi];
  const LV=k=>(OWN[k]||[]).some(s=>SP[s]);
  const V=(i,k)=>{if(!LV(k))return null; const a=MM[k];
   if(!one){let t=0; const yb=SS.y[i]||{}; YJ.forEach(j=>{const c=yb[j]; if(c)t+=(c[a]||0)}); return t;}
   const c=CL(i); return c?(c[a]||0):0;};
  const d0=v=>v==null?'\u2013':fmt(v);
  const P=(a,b)=>(b>0&&a!=null)?(100*a/b):null;
  const q1=v=>v==null?'\u2013':(Math.round(v*10)/10)+' per 100';
  const W=(x,v)=>x.wd?'\u2013':d0(v);
  const EIX=e=>STA.ek.indexOf(e);
  const UN=(i,p)=>{if(one||p==null)return null; const e=SS.e[i]; return e?(e[1+p]||0):null;};
  const SUMU=p=>{if(p==null||one)return null; let t=0;
   SCOPE.forEach(i=>{const v=UN(i,p); if(v)t+=v;}); return t;};
  const SPW=STA.spans.sact;
  const DQ=(f,k)=>fmt(((STA.n[f]||{}).dq||{})[k]||0);
  const X={actR:'One row is one search-team activity report. Every figure in this table is summed '
    +'over those rows, so a busy district files many rows about the same team and no column here is a '
    +'count of distinct children.',
   monR:'One row is one monitoring checklist filed on a search team.',
   sp:'session_plan - the sessions the team said it would run.',
   sc:'session_conducted - and one row writes a negative in it, which a published total cannot hold, '
    +'so that cell is voided and this column is the sum of the usable values, not the raw total.',
   afp:'afp_count - AFP cases the team wrote down. AFP surveillance has its own section on this '
    +'dashboard, built from the case-based line list; this is only what this form recorded.',
   aef:'aefi_count, with the same caveat as the column beside it.'};
  const TT=k=>{const x=TRIO[k];
   return (x?(x.p.label+' \u00b7 '+WS[x.w]+'. A row whose covered figure exceeds its target, or holds '
    +'a negative or an unreadable cell, is counted in the voided rows column and in neither figure '
    +'beside it. ')
    :(MLb[k]+' \u00b7 summed over the rows that survived the row rule. '+(X[k]||'')))
    +'Read as what the team wrote down '+(one?('in '+SLab):('in '+SPW))+', never as a district '
    +'coverage rate. A dash means the form that writes it was not being filed in the period picked.';};
  const FR=STA.forms.map(f=>{const rk=f.cols[0]; let rec=0, dd=0;
   SCOPE.forEach(i=>{const v=V(i,rk); if(v){rec+=v; dd++}});
   return {id:f.id, label:f.label, row:f.row, wb:STA.src[f.id], span:f.span,
    rec:SP[f.id]?rec:null, dist:SP[f.id]?dd:null,
    teams:SUMU(EIX(f.id+'Tm')), ucs:SUMU(EIX(f.id+'Uc')),
    cols:f.cols.slice(1).map(c=>MLb[c]).join(', ')||'nothing but the row count'};});
  drawTable('tSTf',[
   {k:'label', l:'Form', f:x=>'<b>'+esc(x.label)+'</b>'},
   {k:'row', l:'One row is', tt:'How the workbook is keyed. Everything on this card counts rows of '
    +'these two forms, or what those rows wrote down, so no figure here is a count of distinct '
    +'children unless the column says children.'},
   {k:'wb', l:'Workbook it came from', tt:'Pulled '+STA.asof+'. The same two forms are in the export '
    +'above, dated '+STA.older.sact.replace(/_combined.*$/, '')+', and this workbook contains it in '
    +'full - see the caption under the district table for the id-by-id count.'},
   {k:'rec', l:'Rows filed', n:1, f:x=>d0(x.rec),
    tt:'Rows kept for this form '+(one?SLab:('in '+SPW))+', after the source\'s own archive flag, its '
     +'repeated unique_ids and its unreadable entry dates are dropped - a filing volume, not a reach.'},
   {k:'dist', l:'Districts filing', n:1, f:x=>d0(x.dist),
    tt:'District units in scope with at least one kept row of this form in the period picked. The two '
     +'forms do not reach the same districts, so a dash in one row beside figures in the other is a '
     +'form that was not being filed there.'},
   {k:'span', l:'Filed between', tt:'The months this form was actually being written into IDIMS in '
    +'this pull, which is a year and a half longer than the same form in the export above.'},
   {k:'teams', l:'Teams (within district)', n:1, f:x=>d0(x.teams),
    tt:'Distinct team numbers inside their own district, summed over the districts in scope. The '
     +'activity form holds '+fmt(STA.n.sact.teams_any)+' distinct numbers across KP against '+
     fmt(STA.n.sact.teams)+' district-scoped, and the checklist form '+fmt(STA.n.smon.teams_any)+
     ' against '+fmt(STA.n.smon.teams)+', because the export carries no province-wide team id, so '
     +'this is a sum of district counts, not a headcount of teams. Blank in a period view: a team that '
     +'worked in two months is one team.'},
   {k:'ucs', l:'Union councils', n:1, f:x=>d0(x.ucs),
    tt:'Distinct uc_name values inside their own district, summed over the districts in scope. Blank '
     +'in a period view for the same reason as the column beside it.'},
   {k:'cols', l:'Columns it carries',
    tt:'Which of the district table\'s columns this form writes. The checklist form writes exactly '
     +'one: its own row count, because its 25 answered item columns are in the checklist table '
     +'below, not summed into a district figure.'}],
   FR, 'rec', -1);
  const MC=STA.mk.map(k=>({k:k, l:MLb[k], n:1, f:x=>d0(x[k]), tt:TT(k)}));
  const DR=SCOPE.map(i=>{const o={i:i, dn:PTP.ds[i], dv:PTP.dv[i]};
   STA.mk.forEach(k=>{o[k]=V(i,k)});
   o.at=UN(i,EIX('sactTm')); o.au=UN(i,EIX('sactUc'));
   o.mt=UN(i,EIX('smonTm')); o.mu=UN(i,EIX('smonUc')); return o;});
  drawTable('tSTd',[{k:'dn', l:'District', f:x=>'<b>'+esc(x.dn)+'</b>'}, {k:'dv', l:'Division'}]
   .concat(MC, [
   {k:'at', l:'Activity teams', n:1, f:x=>d0(x.at),
    tt:'Team numbers this district used on an activity report, over '+SPW+' only. Blank in a period '
     +'view because the union cannot be taken for a slice of it. The same number on a checklist in '
     +'the same district is the same team, and is counted once in each of the two columns beside it.'},
   {k:'au', l:'Activity UCs', n:1, f:x=>d0(x.au),
    tt:'Distinct uc_name values on this district\'s activity reports, over '+SPW+'.'},
   {k:'mt', l:'Checklist teams', n:1, f:x=>d0(x.mt),
    tt:'Team numbers this district used on a monitoring checklist, over the checklist span '
     +STA.spans.smon+'. A district can show teams here and none in the column beside it - that is '
     +'the mismatch the matched-count table below is built to show.'},
   {k:'mu', l:'Checklist UCs', n:1, f:x=>d0(x.mu),
    tt:'Distinct uc_name values on this district\'s monitoring checklists, over the same span.'}]),
   DR, 'actR', -1);
  const LR=STA.ag.map((ag,x)=>{const vw=STA.agvoid[ag], o={ag:ag, lab:STA.agl[x], wd:vw,
    n:0, t:0, c:0, v:0, d:0};
   if(!vw)SCOPE.forEach(i=>{const yy=SS.l[i]||{};
    YJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.n+=r[3]; o.t+=r[4]; o.c+=r[5]; o.v+=r[6]; o.d++}})});
   o.sh=P(o.c, o.t); o.vh=P(o.v, o.n); return o;});
  drawTable('tSTl',[
   {k:'lab', l:'Antigen the form names', f:x=>'<b>'+esc(x.lab)+'</b>'},
   {k:'pub', l:'Published', f:x=>x.wd?'<b>Withheld</b>':'yes', tt:'A ladder column is withheld when the '
    +'rows that recorded it contradict '
    +'themselves in more than a fifth of them, or when its target column is empty while its coverage '
    +'column is not. A withheld column stays on this table as a row that says so, with its numbers in '
    +'the caption - it is not quietly removed.'},
   {k:'d', l:'District-years', n:1, f:x=>W(x, x.d),
    tt:'District x year cells in scope that hold at least one row recording this pair. This table is '
     +'district x year by construction, so the month picker cannot narrow it; a month view reads the '
     +'whole year and says so in its count line.'},
   {k:'n', l:'Reports recording the pair', n:1, f:x=>W(x, x.n),
    tt:'Activity rows that wrote something in either side of this pair. Rows that left both blank are '
     +'not here, so this is not the same as the report count in the district table above.'},
   {k:'t', l:'Children targeted', n:1, f:x=>W(x, x.t),
    tt:'The form\'s own target column for this antigen, summed over the rows that survived the void '
     +'rule \u00b7 the number the team wrote for what it was aiming at, not a population estimate.'},
   {k:'c', l:'Children covered', n:1, f:x=>W(x, x.c),
    tt:'The form\'s own coverage column for the same antigen, summed over those same rows \u00b7 the '
     +'number the team reported reaching.'},
   {k:'v', l:'Rows voided', n:1, f:x=>W(x, x.v),
    tt:'Rows recording this pair whose covered figure exceeds its target, or holds a negative or an '
     +'unreadable cell. They add to neither figure beside them, which is why those two figures are '
     +'lower than the raw column totals in the file.'},
   {k:'vh', l:'Voided per 100 reports', n:1, f:x=>q1(x.vh),
    tt:'Out of 100 reports that recorded this pair, how many contradicted themselves. Above a fifth, '
     +'the column is withheld.'},
   {k:'sh', l:'Covered per 100 targeted', n:1, f:x=>q1(x.sh),
    tt:'The denominator is the same form\'s own target column, so this is the team\'s own plan, not a '
     +'population and not the campaign denominator. It is not a district coverage rate, it cannot be '
     +'compared with the EPI register below, and where the two figures differ the report is the thing '
     +'being measured, not the children.'}],
   LR, 't', -1);
  const IR=STA.iyes.map(id=>{const x=STA.ik.indexOf(id); if(x<0)return null;
   const o={id:id, lab:STA.ikl[x], y:0, nn:0, b:0, d:0};
   SCOPE.forEach(i=>{const yy=SS.i[i]||{};
    YJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.y+=r[3]; o.nn+=r[4]; o.b+=r[5]; o.d++}})});
   o.sh=P(o.y, o.y+o.nn); return o;}).filter(Boolean);
  drawTable('tSTi',[
   {k:'lab', l:'Checklist item', f:x=>'<b>'+esc(x.lab)+'</b>'},
   {k:'d', l:'District-years', n:1, f:x=>d0(x.d),
    tt:'District x year cells in scope with at least one checklist answering this item. District x '
     +'year by construction, so the month picker cannot narrow this table.'},
   {k:'y', l:'Answered yes', n:1, f:x=>d0(x.y), tt:'Checklist rows that wrote 1 for this item.'},
   {k:'nn', l:'Answered no', n:1, f:x=>d0(x.nn), tt:'Checklist rows that wrote 0 for this item.'},
   {k:'b', l:'Left blank', n:1, f:x=>d0(x.b),
    tt:'Rows that answered neither yes nor no. A blank is not a no, which is why the share beside it '
     +'is taken over answered rows only. No row in this pull answers an item with any other code.'},
   {k:'sh', l:'Yes per 100 answered', n:1, f:x=>q1(x.sh),
    tt:'yes / (yes + no), over the rows that answered at all. This is compliance with a checklist '
     +'item, not immunization coverage, and it says nothing about children.'}],
   IR, 'sh', -1);
  const KR=SCOPE.filter(i=>SS.k[i]).map(i=>{const r=SS.k[i], e=SS.e[i]||[];
   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], a:r[1], b:r[2], o:r[3],
    at:e[1], mt:e[3], rep:Object.keys(SS.y[i]||{}).length};});
  drawTable('tSTk',[
   {k:'dn', l:'District', f:x=>'<b>'+esc(x.dn)+'</b>'},
   {k:'dv', l:'Division'},
   {k:'a', l:STA.lk[0], n:1, tt:'Distinct district + team number + month combinations the activity '
    +'form filed in this district, over '+SPW+'. A team-month is one team working one month in one '
    +'district, so this is not a report count.'},
   {k:'b', l:STA.lk[1], n:1, tt:'The same combination counted from the checklist side, over '
    +STA.spans.smon+'.'},
   {k:'o', l:STA.lk[2], n:1, tt:'On both sides. Published as a count and never as a rate: a district '
    +'with 144 activity team-months and 118 matched is a different finding from one with 1 checklist '
    +'team-month against no activity at all, and a single percentage would flatten both.'},
   {k:'at', l:'Activity teams', n:1, tt:'Team numbers used on activity reports in this district.'},
   {k:'mt', l:'Checklist teams', n:1, tt:'Team numbers used on monitoring checklists in this district.'},
   {k:'rep', l:'Years filed', n:1, tt:'Year slots in the panel window where this district has at '
    +'least one kept search-team row of either form.'}],
   KR, 'o', -1);
  const XR=SCOPE.filter(i=>SS.t[i]).map(i=>{const r=SS.t[i];
   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], e3:r[1], eb:r[2], s3:r[3], sz:r[4], re:r[5],
    h3:P(r[3], r[1]), hz:P(r[4], r[1])};});
  drawTable('tSTe',[
   {k:'dn', l:'District', f:x=>'<b>'+esc(x.dn)+'</b>'},
   {k:'dv', l:'Division'},
   {k:'e3', l:STA.tk[0], n:1, tt:'From the facility EPI register (const EPIM), summed over the '
    +fmt(STA.epi.months.length)+' months both registers cover ('+STA.epi.per+'). Doses administered '
    +'through fixed and mobile sites.'},
   {k:'eb', l:STA.tk[1], n:1, tt:'The same register, BCG, same months.'},
   {k:'s3', l:STA.tk[2], n:1, tt:'From the search-team activity form over the same months - the '
    +'covered side of the OPV-3 pair, after the void rule.'},
   {k:'sz', l:STA.tk[3], n:1, tt:'The covered side of the zero-dose pair from the same form and the '
    +'same months. This is a search team finding a child with no prior dose, not a register of '
    +'children who never got one.'},
   {k:'re', l:STA.tk[4], n:1, tt:'Activity reports behind the two figures beside it.'},
   {k:'h3', l:'Search-team OPV-3 per 100 facility doses', n:1, f:x=>q1(x.h3),
    tt:'Two registers of the same districts set side by side, not a numerator over a denominator: '
     +'one counts what a search team wrote down, the other what facilities recorded. A value is '
     +'readable only as one register being larger than the other, never as coverage - and a '
     +'search-team figure above 100 would have stopped this build rather than being published here.'}],
   XR, 's3', -1);
  const SW2=one?SLab:SPW;
  el('cntSTf').textContent=STA.forms.length+' forms \u00b7 '+SW2+' \u00b7 both pulled '+STA.asof;
  el('cntSTd').textContent=DR.length+' district units in the two workbooks \u00b7 '+SW2;
  el('cntSTl').textContent=STA.ag.length+' antigen pairs \u00b7 '+Object.keys(STA.agvoid).length
   +' withheld \u00b7 district x year, '+(one?String(yv):('all '+YJ.length+' years in scope'))
   +(mv?' \u00b7 the month cannot narrow this table':'');
  el('cntSTi').textContent=IR.length+' of '+STA.ik.length+' item columns answered \u00b7 '
   +STA.inever.length+' no row ever answered \u00b7 district x year, '
   +(one?String(yv):('all '+YJ.length+' years in scope'))+(mv?' \u00b7 the month cannot narrow it':'');
  el('cntSTk').textContent=KR.length+' district units \u00b7 whole window '+SPW
   +' \u00b7 the period picked does not narrow this table';
  el('cntSTe').textContent=XR.length+' district units in both registers \u00b7 '
   +fmt(STA.epi.months.length)+' months of '+STA.epi.per+' \u00b7 not narrowed by the period picked';
  const DRS=f=>{const d=(STA.n[f]||{}).drop||{};
   return Object.keys(d).map(k=>fmt(d[k])+' '+k).join(', ')||'nothing'};
  const NOACT=KR.filter(x=>x.a===0).map(x=>x.dn);
  const AGV=Object.keys(STA.agvoid);
  el('capSTa').textContent=[
   'This is the same two HRMP forms as the mobile-team block above, read from a later pull and at '
    +'greater depth: '+STA.src.sact+' and '+STA.src.smon+', the two Tableau workbooks the owner '
    +'exported from IDIMS on '+STA.asof+'. They hold '+fmt(STA.n.sact.kept)+' activity reports and '
    +fmt(STA.n.smon.kept)+' monitoring checklists across '+STA.ds.length+' district units, filed '
    +SPW+'. The workbooks are the source of record for these two forms, and that is provable rather '
    +'than assumed: of the '+fmt(STA.vint.sact.older_ids)+' row ids in the 21-Apr-2025 export of the '
    +'activity form, '+fmt(STA.vint.sact.shared)+' also appear in the workbook and only '
    +fmt(STA.vint.sact.older_only)+' does not - and that one is carried into these totals rather than '
    +'lost. The workbook adds '+fmt(STA.vint.sact.workbook_only)+' rows filed since April. The '
    +'checklist form is the same shape: '+fmt(STA.vint.smon.shared)+' of '+fmt(STA.vint.smon.older_ids)
    +' ids shared, none missing, '+fmt(STA.vint.smon.workbook_only)+' newer rows. Two vintages of two '
    +'forms, not two more forms, so nothing on this card is ever added to the card above it.',
   'What the owner pointed at is here, and it is not what the column names suggest. The search-team '
    +'activity form has a dose column for every antigen in the ladder and every one of them is blank '
    +'in all '+fmt(STA.vint.sact.wb_rows)+' rows of the workbook. What the form actually carries is a '
    +'target and a coverage figure per antigen, so that pair is the measure on this card: children '
    +'targeted, children covered, and the rows that wrote a pair contradicting themselves. '
    +fmt(STA.n.zdV)+' zero-dose, '+fmt(STA.n.o3V)+' OPV-3 and '+fmt(STA.n.bV)+' BCG rows did exactly '
    +'that, and each pair keeps its own void column rather than having those rows quietly dropped.',
   'This answers, for these two forms, the question the transit-point panel still holds open. The '
    +'target / coverage family is the same one the field-check and mobile-team blocks withhold '
    +'pending an IDIMS report definition, and the reason was arithmetic: in the April export coverage '
    +'exceeded target in 4,245 rows and one target was negative. Here the owner\'s own workbook is '
    +'the definition, the same test is applied row by row, and the rows that fail it are counted in '
    +'the open rather than published as a rate. So the pair appears as two counts and a void count, '
    +'one per-100 column whose tooltip names its own denominator, and no coverage percentage '
    +'anywhere on this card.',
   'The ladder is '+STA.ag.length+' antigen pairs and '+(AGV.length?
    (AGV.length+' had to be withheld: '+AGV.map(a=>{const w=STA.agvoid[a];
     return STA.agl[STA.ag.indexOf(a)]+' ('+a+') is '+w[0]+' - '+fmt(w[1])+' children targeted against '
     +fmt(w[2])+' covered, while '+fmt(w[3])+' of the '+fmt(w[4])+' rows that recorded it contradicted '
     +'themselves'}).join('; ')+'.'):'none had to be withheld.')+' Those rows are on the ladder table as '
    +'a withheld line with their numbers in the caption, not as a missing line, because a column '
    +'whose coverage is filled in where its target is not is a finding about the form, not about the '
    +'programme. The other '+fmt(STA.ag.length-AGV.length)+' columns survive the same test at under a '
    +'twentieth of their rows. The ladder is district x year: a search team that reports a target for '
    +'a month it never worked is exactly the error the row rule exists to catch, so the month picker '
    +'cannot narrow it and says so in its count line.',
   'The monitoring checklist answers 1, 0 or nothing, which is decodable without a report definition - '
    +'unlike the transit-point monitoring export, whose item codes are undecoded and are therefore not '
    +'published at all. '+STA.iyes.length+' of its '+STA.ik.length+' item columns were answered by at '
    +'least one row and are in that table as yes, no, left blank, and a share taken over answered rows '
    +'only, because a blank is not a no. '+STA.inever.length+' were answered by no row at all in '
    +'either pull: '+STA.inever.join(', ')+'. Those are blank form fields, not findings, so they are '
    +'named and not graphed. This table is district x year too.',
   'Teams and union councils are counted inside their own district and the province figure is the sum '
    +'of those: the activity form holds '+fmt(STA.n.sact.teams_any)+' distinct team numbers across KP '
    +'against '+fmt(STA.n.sact.teams)+' once scoped to their district, and the checklist form '+
    fmt(STA.n.smon.teams_any)+' against '+fmt(STA.n.smon.teams)+', because the export carries no '
    +'province-wide team id, so a team numbered 7 in two districts counts twice and says so. Both go '
    +'blank in a period view: a team that worked in two months is still one team.',
   'The link between the two forms is published as matched counts. Over the whole window the activity '
    +'side files '+fmt(STA.n.link[0])+' district + team + month combinations, the checklist side '+
    fmt(STA.n.link[1])+', and '+fmt(STA.n.link[2])+' appear on both. No rate is taken over that: '
    +(NOACT.length?(NOACT.length+' district units ('+NOACT.join(', ')+') file checklists with no '
     +'activity report behind them at all, which is a finding about who monitored whom rather than a '
     +'denominator to divide by'):'every district with a checklist also has activity reports')+'. The '
    +'checklist also reaches '+STA.n.smon.districts+' district units against the activity form\'s '+
    STA.n.sact.districts+', so a dash in one column beside figures in the other means that form was '
    +'not being filed there, not that no search team worked there.',
   'The EPI comparison sets two registers of the same districts side by side for the '+
    fmt(STA.epi.months.length)+' months both cover ('+STA.epi.per+'): what a search team reported '
    +'covering, and what facilities recorded administering. They are not a numerator and a denominator '
    +'and the ratio between them is not a coverage rate - one counts children a team found, the other '
    +'doses given through sites, over the same months and districts. The build aborts rather than '
    +'publishing a search-team figure that exceeds the whole facility register, and none does.',
   'Every month here is the month the entry was made, the same uniform rule as the block above. This '
    +'form also carries its own activity date, and it disagrees with the entry month in '+
    DQ('sact', 'activity month and entry month differ')+' of '+fmt(STA.n.sact.kept)+' rows - a sixth '
    +'of them - is unreadable in '+DQ('sact', 'activity date cannot be read')+', and '+
    DQ('sact', 'activity date after the pull was taken')+' is dated after the pull itself was taken. '
    +'Rows are never re-dated.',
   'How the rows were kept: '+STA.forms.map(f=>'of '+fmt(STA.n[f.id].read)+' '+f.label+' rows read, '+
    DRS(f.id)+' was dropped, '+fmt(STA.n[f.id].kept)+' kept'+(STA.n[f.id].carried
    ?(' and '+fmt(STA.n[f.id].carried)
    +' carried from the April export under its own id'):'')).join('; ')+'. Archived rows are the '
    +'source\'s own is_archive flag, not a judgement made here, and a repeated unique_id is counted '
    +'once. Where the two forms disagree on a district spelling, the workbook is matched to the KP '
    +'district index case-insensitively - WAZIR-S LOWER on this form is the panel\'s SW Wazir Belt - '
    +'and a spelling that matches more than one district would abort the build rather than pick one.',
   'Where the form disagrees with itself, published as found: '+
    DQ('sact', 'sessions conducted exceed sessions planned')+' rows conduct more sessions than they '
    +'planned, one row writes a negative in session_conducted and that single cell is voided while '
    +'the row stands, '+DQ('sact', 'ladder ipv_1: a negative in the pair')+' ladder row holds a '
    +'negative in a target, and '+DQ('sact', 'ladder ipv_booster: a cell that is not a number')+' '
    +'write a value that is not a number at all. Every one of those is counted in the voided column '
    +'beside the figures it contradicts, so the totals on this card are the sums of the usable '
    +'values, not the raw column totals in the workbook.',
   'What the workbooks also carry and this block does not publish: '+STA.hold.join('; ')+'.',
   'Read every figure here as a count of forms and of what those forms wrote down. The district table '
    +'sorts by activity reports, largest first, and follows the Reporting period pick, the Division '
    +'filter and the District filter; the ladder, the item table and the two comparison tables are '
    +'whole-window or district x year and their count lines say which.'
  ].join(' ');
  const CK=['actR','monR','zdT','zdC','zdV','o3T','o3C','o3V','bT','bC','bV','naR','naC','naV',
   'rfR','rfC','rfV','sp','sc','afp','aef'];
  el('btnSTf').onclick=()=>csvDownload('hrmp_search_teams_forms_'+(one?(mv?(yv+'-'+mv):('y'+yv))
    :STA.win)+'_'+_slug()+'.csv',
   ['Form','One row is','Workbook','Rows filed','Districts filing','Filed between',
    'Teams (within district)','Union councils','Columns it carries'],
   FR.map(x=>[x.label,x.row,x.wb,x.rec==null?'':x.rec,x.dist==null?'':x.dist,x.span,
    x.teams==null?'':x.teams,x.ucs==null?'':x.ucs,x.cols]));
  el('btnSTd').onclick=()=>csvDownload('hrmp_search_teams_district_'+(one?(mv?(yv+'-'+mv):('y'+yv))
    :STA.win)+'_'+_slug()+'.csv',
   ['Division','District'].concat(STA.mkl)
    .concat(['Activity teams','Activity UCs','Checklist teams','Checklist UCs','Period']),
   DR.map(x=>[x.dv,x.dn].concat(CK.map(k=>x[k]==null?'':x[k]))
    .concat([x.at,x.au,x.mt,x.mu,SW2])));
  el('btnSTl').onclick=()=>csvDownload('hrmp_search_teams_antigen_ladder_'+(one?String(yv):STA.win)
    +'_'+_slug()+'.csv',
   ['Antigen','Published','District-years','Reports recording the pair','Children targeted',
    'Children covered','Rows voided','Voided per 100 reports','Covered per 100 targeted','Period'],
   LR.map(x=>[x.lab,x.wd?('withheld: '+x.wd[0]):'yes',x.wd?'':x.d,x.wd?'':x.n,x.wd?'':x.t,
    x.wd?'':x.c,x.wd?'':x.v,x.wd?'':q1(x.vh),x.wd?'':q1(x.sh),one?String(yv):SPW]));
  el('btnSTi').onclick=()=>csvDownload('hrmp_search_teams_checklist_items_'+(one?String(yv):STA.win)
    +'_'+_slug()+'.csv',
   ['Checklist item','District-years','Answered yes','Answered no','Left blank',
    'Yes per 100 answered','Never answered by any row','Period'],
   IR.map(x=>[x.lab,x.d,x.y,x.nn,x.b,q1(x.sh),'','' ]).concat(
    STA.inever.map(c=>[STA.ikl[STA.ik.indexOf(c)],'', '', '', '', '', 'yes', ''])));
  el('btnSTk').onclick=()=>csvDownload('hrmp_search_teams_activity_vs_checklist_'+STA.win+'_'+_slug()
    +'.csv',
   ['Division','District','Activity team-months','Checklist team-months','Team-months with both',
    'Activity teams','Checklist teams','Years filed','Window'],
   KR.map(x=>[x.dv,x.dn,x.a,x.b,x.o,x.at,x.mt,x.rep,SPW]));
  el('btnSTe').onclick=()=>csvDownload('hrmp_search_teams_vs_epi_register_'+STA.epi.per.replace('-','to')
    +'.csv',
   ['Division','District','EPI OPV-3 doses','EPI BCG doses','Search-team OPV-3 covered',
    'Search-team zero-dose covered','Activity reports','Search-team OPV-3 per 100 facility doses',
    'Two registers, not a coverage rate'],
   XR.map(x=>[x.dv,x.dn,x.e3,x.eb,x.s3,x.sz,x.re,q1(x.h3),'yes']));
  }
 }
"""


def strip_js(block):
    """Blank out string literals and comments, so bracket counting sees only real code."""
    out, i, n = [], 0, len(block)
    while i < n:
        c = block[i]
        if c in "'\"":
            j = i + 1
            while j < n and block[j] != c:
                j += 2 if block[j] == chr(92) else 1
            out.append("''")
            i = j + 1
            continue
        if c == '/' and i + 1 < n and block[i + 1] == '/':
            while i < n and block[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and block[i + 1] == '*':
            k = block.find('*/', i)
            i = n if k < 0 else k + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def check_js(v, name, block):
    """Two failure modes these patches have already produced once: a bracket left open, and two
    string literals side by side with no + between them (valid Python, a syntax error in JS)."""
    pairs, stack = {'(': ')', '[': ']', '{': '}'}, []
    for ch in strip_js(block):
        if ch in pairs:
            stack.append(ch)
        elif ch in pairs.values():
            v.require(bool(stack) and pairs[stack[-1]] == ch,
                      '%s: a %r closes nothing (depth %d)' % (name, ch, len(stack)))
            stack.pop()
    v.require(not stack, '%s: %d bracket(s) left open: %s' % (name, len(stack), ''.join(stack)))
    lines = block.split('\n')
    for k in range(len(lines) - 1):
        a, b = lines[k].rstrip(), lines[k + 1].lstrip()
        v.require(not (a.endswith("'") and not a.endswith(chr(92) + "'") and b.startswith("'")),
                  '%s: line %d ends a string and line %d starts another with no + between them'
                  % (name, k + 1, k + 2))


def patch(v, js, obj):
    check_js(v, 'CACHE', CACHE)
    check_js(v, 'RENDER', RENDER)
    t = v.text
    for nm, a in (('const', A_CONST), ('card', A_CARD), ('cache', A_CACHE),
                  ('render', A_RENDER), ('hint', A_HINT)):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1) [%s]: %r'
                  % (t.count(a), nm, a[:56]))
    # the three claims the mobile-team caption makes about these two forms: each is still true of that
    # April pull and no longer true of the page once this block is on it
    for old, new in FIX:
        v.require(t.count(old) == 1, 'caption anchor occurs %d times (want 1): %r'
                  % (t.count(old), old[:56]))
    v.require('const STA' not in t and 'id="cSTa"' not in t, 'STA block already patched in')
    # the download has to match the grid column for column, or the CSV reorders the data against its
    # own header with nothing on screen saying so
    names = [x.strip().strip("'") for x in
             re.search(r"const CK=\[(.*?)\];", RENDER, re.S).group(1).split(',')]
    v.require(sorted(names) == sorted(obj['mk']),
              'the CSV key list and STA.mk are not the same columns: %s vs %s'
              % (names, obj['mk']))
    # the district grid's measure columns are generated from the payload, so every measure reaches the
    # screen by construction - but only while that generation is still keyed by STA.mk
    v.require('STA.mk.forEach(k=>{o[k]=V(i,k)})' in RENDER
              and 'const MC=STA.mk.map(k=>({k:k,' in RENDER,
              'the district grid no longer draws one column per STA.mk measure')
    v.require(t.count('const STC=') == 1,
              'STC is already taken in renderPTP - the card const must use another name')
    t = t.replace(A_CONST, 'const STA = %s;\r\n' % js + A_CONST)
    t = t.replace(A_CARD, A_CARD + CARD)
    t = t.replace(A_CACHE, CACHE.replace('\n', '\r\n') + A_CACHE)
    t = t.replace(A_RENDER, RENDER.replace('\n', '\r\n') + A_RENDER)
    t = t.replace(A_HINT, HINT_NEW)
    for old, new in FIX:
        t = t.replace(old, new)
    v.text = t
    v.changes.append('STA search-team block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for once in ('const STA = {', 'function staTab(){', 'id="cSTa"', 'hrmp_search_teams_forms_',
                 'hrmp_search_teams_district_', 'hrmp_search_teams_antigen_ladder_',
                 'hrmp_search_teams_checklist_items_', 'hrmp_search_teams_activity_vs_checklist_',
                 'hrmp_search_teams_vs_epi_register_'):
        v.require(t.count(once) == 1, '%s occurs %d times (want 1)' % (once, t.count(once)))
    for idm in ('tSTf', 'tSTd', 'tSTl', 'tSTi', 'tSTk', 'tSTe'):
        v.require(t.count('id="%s"' % idm) == 1 and t.count("drawTable('%s'" % idm) == 1,
                  '%s is not drawn exactly once' % idm)
    for idm in ('cntSTf', 'cntSTd', 'cntSTl', 'cntSTi', 'cntSTk', 'cntSTe', 'capSTa'):
        v.require(t.count('id="%s"' % idm) == 1 and t.count("'%s'" % idm) >= 1,
                  '%s has no slot on the card or no writer in the renderer' % idm)
    for idb in ('btnSTf', 'btnSTd', 'btnSTl', 'btnSTi', 'btnSTk', 'btnSTe'):
        v.require(t.count('id="%s"' % idb) == 1 and t.count("el('%s').onclick" % idb) == 1,
                  '%s has a button with no download, or a download with no button' % idb)
    for needle in ('WAZIR-S LOWER', 'function staTab()', 'the month cannot narrow this table',
                   'no coverage percentage', 'is carried into these totals rather than'):
        v.require(t.count(needle) >= 1, '%s is missing' % needle)
    v.require(t.index('id="cMTf"') < t.index('id="cSTa"') < t.index('id="tPTa"'),
              'the search-team card is not between the mobile-team card and the district inventory')
    v.require(t.index('const PTPM = ') < t.index('const MTM = ') < t.index('const STA = ')
              < t.index('const SURVW = '), 'the HRMP consts must sit in pull order, before SURVW')
    v.require(t.index("drawTable('tMTf'") < t.index("drawTable('tSTf'"),
              'the search-team render must follow the mobile-team render')
    v.require(t.index('function mtmTab(){') < t.index('function staTab(){')
              < t.index('function ptBadge(){'), 'staTab must sit with the other PTP cache helpers')
    # the mobile-team caption has to point here rather than contradict this block
    v.require(t.count('were re-pulled into a September 2026 workbook') == 1
              and t.count('and not re-pulled into this payload since') == 1
              and t.count('the three HRMP blocks and the union-council listing') == 1,
              'the stale mobile-team claims were not corrected')
    v.require(t.count('All six stopped being filed long before the daily reports did') == 0,
              'the mobile-team caption still says all six forms stopped in Apr-2025')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_sta.py first' % PAYLOAD)
    obj = json.loads(srcutil.read_text(PAYLOAD))
    js = srcutil.dumps(obj)
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    patch(v, js, obj)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('payload STA %d chars, %d forms, %d districts with search-team data, %d measures, %d '
          'antigen pairs (%d withheld), %d checklist items, %d held-out groups'
          % (len(js), len(obj['forms']), len(obj['ds']), len(obj['mk']), len(obj['ag']),
             len(obj['agvoid']), len(obj['iyes']), len(obj['hold'])))
    print('OK sta-ui master only - the other three variants are synced by push_master.py, which '
          "needs the owner's word")


if __name__ == '__main__':
    main()

