# -*- coding: utf-8 -*-
"""Build the standalone SNID Nov-26 focus presentation for the core team (master only).

What it does
  * adds focusDeckData(), renderFocusDeck() and runFocusDeck() to the FOCUS region of the master, so the
    deck is built from the same FOCX shortlists the "Where to focus for SNID Nov-26" card publishes - the
    numbers on a slide are the numbers on the page, never a second calculation;
  * puts a "Focus deck (pptx)" button on that card and a matching card on the Presentations tab, so the
    brief is downloadable without opening the transit point tab;
  * 15 slides: cover, how a unit gets on the list, the district shortlist, what to do with each, channel
    state, the uncovered backlog, register coverage against routine OPV-3, the risk overlay, the HRMP field
    checks, the Nov-26 readiness gates, the priority union councils, the rest of the two-flag councils, the
    data fixes, actions before the round, and sources and limits.

Rules this build keeps
  * no PTP coverage percentage anywhere: the panel counts reports, not distinct children and its own
    Coverage column is still unconfirmed with IDIMS;
  * HRMP evidence is stated as unvaccinated under-5s per 100 spot checklists, never as a percentage, and it
    can honestly pass 100;
  * campaign covered figures are '+round+' own self-report and routine OPV-3 is a cumulative EPI window,
    stated on the slides that use them;
  * the Nov-26 campaign target is the scope file's targeted-children figure, not a zero-dose count;
  * units IDIMS files under a name the campaign data does not use carry no campaign, EPI or risk cell.
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

JS_START = '// ---------- NOV-26 FOCUS DECK: standalone presentation for the core team ----------\n'
JS_LAST = "FOC_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runFocusDeck(b,el(p[1]));});\n"

BTN_OLD = '<button class="btn" id="btnFOCd"'
BTN_NEW = ('<button class="btn pri" id="btnFOCDeck" title="A stand-alone presentation of these shortlists '
           'for the core team">&#9654; Focus deck (pptx)</button>'
           '<span class="cnt" id="focDeckStatus"></span>'
           '<button class="btn" id="btnFOCd"')

CARD_OLD = ('<div class="card" style="margin-bottom:14px;border-top:5px solid #4338ca">'
            '<h3 style="margin:0">Pre-campaign daily SITREP</h3>')
CARD_NEW = """<div class="card" style="margin-bottom:14px;border-top:5px solid #0e7490"><h3 style="margin:0">SNID Nov-26 focus brief</h3>
<div class="bgrid"><div class="bcard" style="--bc:#0e7490;grid-column:1/-1"><b>&#127919; Nov-26 focus brief</b><small>What to put in front of the core team before the round: the district units that two or more independent sources flag - the transit point channel, the last round's zero-dose register and its covered export, routine OPV-3 in the same councils, the combined council risk score and the HRMP spot checks - each with the backlog behind it, the readiness gate still open and the action to take. Then the union councils to brief teams on, the field-check evidence, the data fixes the list depends on, and the sources and limits. Built from the transit point tab, so it follows the Division / District filters and the reporting period there. About 15 slides.</small>
<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button class="btn pri" id="btnFOCDeck2">&#9654; Prepare focus brief</button><span class="cnt" id="focDeckStatus2"></span></div></div></div></div>""" + CARD_OLD
CARD_NEW = CARD_NEW.replace('\n', '\r\n')

JS = JS_START + r'''function focusDeckData(){
 const F=focCtx(), X=ptpCtx(); if(!F||!X)return null;
 const SB={};((typeof SND!=='undefined'&&SND&&SND.d)?SND.d:[]).forEach(r=>{SB[r[0]]={cat:r[2],ucs:r[3],tgt:r[4]};});
 const RF=F.RF.map(x=>{const b=SB[x.raw]||{};
  return Object.assign({},x,{cat:b.cat||'',tgt:b.tgt==null?null:b.tgt,sucs:b.ucs==null?null:b.ucs,rd4:focRdy(x.raw)});});
 const two=RF.filter(x=>x.n>=2), three=RF.filter(x=>x.n>=3), solo=RF.filter(x=>x.n===1),
  sil=RF.filter(x=>x.quiet||x.lapsed||x.thin),
  gapAll=RF.reduce((s,x)=>s+x.gap,0), gapF=two.reduce((s,x)=>s+x.gap,0),
  tgtF=two.reduce((s,x)=>s+(x.tgt||0),0), UF=F.UF,
  u2=UF.filter(x=>x.n>=2), u3=UF.filter(x=>x.n>=3), reg=UF.reduce((s,x)=>s+(x.zr||0),0),
  offmap=UF.filter(x=>x.zd>0&&!x.map), noTgt=RF.filter(x=>!x.tgt),
  noPtp=(typeof SND!=='undefined'&&SND&&SND.d||[]).filter(r=>PTP.dr.indexOf(r[0])<0).map(r=>r[0]),
  noJoin=RF.filter(x=>x.hv==null).map(x=>x.raw),
  PD=ptpDeckData()||{};
 return {RF:RF,UF:UF,two:two,three:three,solo:solo,sil:sil,gapAll:gapAll,gapF:gapF,tgtF:tgtF,
  u2:u2,u3:u3,ug:F.ug,ug2:F.ugF,reg:reg,offmap:offmap,noTgt:noTgt,noPtp:noPtp,noJoin:noJoin,
  camp:F.camp,SLab:F.SLab,MDen:F.MDen,tot:PD.tot,scope:pptScope(),
  win:PTP.win,src:PTP.src,asof:PTP.asof,hold:PTP.hold||[],
  rnd:(typeof SND!=='undefined'&&SND&&SND.n)||'SNID Nov-26',
  rstartD:(typeof SND!=='undefined'&&SND&&SND.st)?new Date(SND.st+'T00:00:00').toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):'2 Nov 2026',rsrc:(typeof SND!=='undefined'&&SND&&SND.src)||'',
  ep:(typeof EMETA!=='undefined'&&EMETA&&EMETA.per)||'',
  date:new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})};
}
function renderFocusDeck(P,X){
 const pptx=new P(); pptx.layout='LAYOUT_WIDE';
 pptx.title='SNID Nov-26 focus: '+X.scope; pptx.company='KP Polio and Synergy Dashboard';
 const NV='0E7490',RED='B91C1C',GRN='15803D',AMB='B45309',ORA='C2410C',PUR='6D28D9',GRY='6B7280',TXT='1F2937',F='Segoe UI';
 const p1=v=>v==null?'\u2013':(Math.round(v*10)/10).toFixed(1), n0=v=>v==null?'\u2013':Math.round(v).toLocaleString('en-US');
 const cut=(t,n)=>{t=t==null?'':String(t);return t.length>n?t.slice(0,n-1)+'\u2026':t;};
 const chg=x=>x.quiet?'Silent since '+PTP.yr[0]:(x.lapsed?'Stopped in '+PTP.yr[Math.max(0,x.last)]:(x.thin?'Shallow ('+p1(x.monp)+'%)':'Filing ('+p1(x.monp)+'%)'));
 let pg=0;
 const base=(t,sub)=>{const s=pptx.addSlide(); pg++; s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.13,fill:{color:NV},line:{color:NV}});
  s.addText(t,{x:0.5,y:0.28,w:12.3,h:0.6,fontFace:F,fontSize:24,bold:true,color:NV});
  if(sub)s.addText(sub,{x:0.5,y:0.86,w:12.3,h:0.4,fontFace:F,fontSize:12,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText('SNID Nov-26 focus brief \u00b7 '+X.scope+' \u00b7 '+X.camp+' figures, panel as at '+X.asof,{x:0.5,y:7.02,w:10.5,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'}); return s;};
 const kpis=(s,it,col,y)=>{const n=it.length,gp=0.2,w=(12.33-gp*(n-1))/n;
  it.forEach((it2,i)=>{const x=0.5+i*(w+gp),c=it2.c||col;
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:1.32,fill:{color:'F9FAFB'},line:{color:'E5E7EB',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:0.07,fill:{color:c},line:{color:c}});
   s.addText(it2.l.toUpperCase(),{x:x+0.15,y:y+0.15,w:w-0.3,h:0.3,fontFace:F,fontSize:9,bold:true,color:GRY});
   s.addText(it2.v,{x:x+0.15,y:y+0.44,w:w-0.3,h:0.5,fontFace:F,fontSize:it2.fs||22,bold:true,color:it2.vc||TXT});
   if(it2.s)s.addText(it2.s,{x:x+0.15,y:y+0.94,w:w-0.3,h:0.34,fontFace:F,fontSize:9,color:GRY});});};
 const note=(s,t,o)=>s.addText(t,{x:o.x,y:o.y,w:o.w,h:o.h||0.4,fontFace:F,fontSize:o.fs||11,color:o.c||GRY,italic:!!o.i,valign:'top'});
 const bullets=(s,a,o)=>s.addText(a.map(t=>({text:t,options:{bullet:{indent:16},breakLine:true}})),
  {x:o.x,y:o.y,w:o.w,h:o.h,fontFace:F,fontSize:o.fs||13,color:TXT,valign:'top',paraSpaceAfter:o.ps||8});
 const table=(s,head,rows,o)=>{const fs=o.fs||9;
  if(!rows.length){note(s,o.empty||'No unit in this selection.',{x:o.x,y:o.y,w:o.w});return;}
  const hdr=head.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.col||NV},fontSize:fs,align:j&&!o.left?'center':'left',valign:'middle'}}));
  const body=rows.map((r,i)=>r.map((c,j)=>({text:String(c==null||c===''?'\u2013':c),
   options:{fontSize:fs,color:TXT,fill:{color:i%2?'FFFFFF':'F1F5F9'},align:(j&&!o.left)?'center':'left',valign:'middle'}})));
  s.addTable([hdr,...body],{x:o.x,y:o.y,w:o.w,colW:o.colW,fontFace:F,rowH:[0.34].concat(rows.map(()=>o.rh||0.28)),
   border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false,margin:0.03});};
 const bars=(s,labs,vals,col,o)=>{
  if(!labs.length){note(s,'No data for this selection.',{x:o.x,y:o.y+1.4,w:o.w,fs:12});return;}
  const op={x:o.x,y:o.y,w:o.w,h:o.h,barDir:'bar',chartColors:[col],showTitle:true,title:o.title,titleFontSize:12,titleColor:TXT,titleFontFace:F,
   showValue:true,dataLabelFontSize:labs.length>12?7:8,dataLabelColor:TXT,dataLabelFormatCode:o.fmt||'0.0',dataLabelPosition:'outEnd',
   catAxisLabelFontSize:labs.length>12?7:9,catAxisLabelFontFace:F,catAxisLabelColor:TXT,catAxisOrientation:'maxMin',
   valAxisLabelFontSize:9,valAxisLabelColor:GRY,valAxisLabelFormatCode:'#,##0',valAxisMinVal:o.min||0,
   valGridLine:{color:'E5E7EB',size:0.5},showLegend:false,barGapWidthPct:40};
  if(o.max!=null)op.valAxisMaxVal=o.max;
  s.addChart(pptx.ChartType.bar,[{name:o.name||'Value',labels:labs,values:vals}],op);};
 // 1 cover
 {const s=pptx.addSlide(); pg++; s.background={color:NV};
  s.addText('SNID NOV-26 FOCUS BRIEF',{x:0.8,y:1.2,w:11.7,h:0.5,fontFace:F,fontSize:16,bold:true,color:'A5F3FC',charSpacing:4});
  s.addText('Where five independent sources agree on a gap',{x:0.8,y:1.72,w:11.7,h:0.9,fontFace:F,fontSize:38,bold:true,color:'FFFFFF'});
  s.addText(X.two.length+' of '+X.RF.length+' transit-point district units are flagged by two or more channels, '+X.three.length+' of them by three or more \u00b7 '+n0(X.u2.length)+' union councils are flagged by two or more checks',{x:0.8,y:2.72,w:11.7,h:0.7,fontFace:F,fontSize:15,color:'CFFAFE'});
  s.addText('Round starts '+X.rstartD+' \u00b7 IDIMS transit point panel '+X.src+', data as at '+X.asof+' \u00b7 campaign figures from '+X.camp+' \u00b7 scope from '+X.rsrc,{x:0.8,y:3.42,w:11.7,h:0.4,fontFace:F,fontSize:11,color:'A5F3FC'});
  kpis(s,[{l:'Districts 2+ channels',v:String(X.two.length),s:X.three.length+' at three or more',vc:'FFFFFF'},
   {l:'Uncovered zero-dose',v:n0(X.gapAll),s:n0(X.gapF)+' at the shortlisted districts',vc:'FCA5A5'},
   {l:'Councils 2+ flags',v:n0(X.u2.length),s:n0(X.u3.length)+' at three or more',vc:'FFFFFF'},
   {l:'Nov-26 target, shortlist',v:n0(X.tgtF),s:'children the round targets',vc:'FFFFFF'},
   {l:'Weak transit channels',v:String(X.sil.length),s:'silent, lapsed or shallow',vc:'FCD34D'}],'135E6B',4.15);
  s.addText('Prepared '+X.date+' \u00b7 KP Polio and Synergy Dashboard \u00b7 built from the Permanent Transit Points tab, so it follows the filters set there',{x:0.8,y:6.5,w:11.7,h:0.4,fontFace:F,fontSize:11,color:'CFFAFE'});}
 // 2 how a unit gets on the list
 {const s=base('How a unit gets on this list','Five channels for a district unit, six checks for a union council - each one a different source measuring a different thing');
  table(s,['Channel','What it measures','Threshold used','Why it belongs here'],
   [['1 Transit point channel','Whether the district actually files to IDIMS','No report ever filed, nothing since the last year of the window, or under '+FOC.thin+'% of the month slots','A gap nobody reports is a gap nobody closes'],
    ['2 '+X.camp+' register','Zero-dose children listed on its transit councils, and how many the round covered','Under '+FOC.cover+'% covered, on at least '+FOC.zmin+' councils','Reached once, missed again between rounds'],
    ['3 Routine EPI','OPV-3 across those same councils','Under '+FOC.epi+'%, on at least '+FOC.zmin+' councils','The routine system is not holding a mobile population'],
    ['4 Combined risk score','Very-high and high-risk councils inside the footprint','3 or more','Named micro-plan targets already exist'],
    ['5 HRMP field checks','Unvaccinated under-5s found per 100 spot checklists','100+ checklists and 20+ per 100','Surveyors keep opening doors the cards never touched']],
   {x:0.5,y:1.4,w:12.33,colW:[1.9,3.0,4.0,3.43],fs:9,rh:0.62,left:true});
  bullets(s,['A unit needs two or more channels to make the shortlist. The coverage and OPV-3 channels only fire where the footprint carries at least '+FOC.zmin+' councils with that source, so a district represented by a single council cannot be flagged on them.',
   'Nov-26 readiness - the DPEC, mandatory staff, AIC training and validated micro-plans - rides beside the need count as an execution column, not as a channel: it says who can act, not who is worst.',
   'Nothing here is a coverage percentage of the transit point network. The panel counts reports, not distinct children, and its own Coverage column is still unconfirmed with IDIMS.'],
   {x:0.5,y:5.05,w:12.33,h:1.5,fs:11});}
 // 3 the shortlist
 {const s=base('The district shortlist',X.two.length?'Two or more channels flag these units. Ranked by channels, then by the children the last round left uncovered.':'No unit carries two channel flags on this selection.');
  const rows=(X.two.length?X.two:X.solo).slice(0,9).map(x=>[cut(x.dn,20),x.dv,x.cat,x.n+' of 5',n0(x.tgt),n0(x.gap),p1(x.zp),p1(x.ep),
   chg(x),x.hv==null?'\u2013':n0(x.hv),x.srv==null?'\u2013':(x.srv<FOC.min?p1(x.srate)+' of '+n0(x.srv):p1(x.srate)),
   x.rdy==null?'\u2013':(x.rdy.length?cut(x.rdy[0],26):'complete')]);
  table(s,['District','Division','Nov-26 category','Ch.','Target children','Uncovered','Covered %','OPV-3 %','Channel state','VH+high UCs','Per 100 surveys','Gate still open'],
   rows,{x:0.5,y:1.42,w:12.33,colW:[1.85,1.05,1.15,0.62,1.05,0.9,0.85,0.8,1.45,0.95,1.05,1.66],fs:8.5,rh:0.42,left:true});
  note(s,'Channel state is judged on the whole '+X.win+' window, so the shortlist does not move with the reporting period on the tab; target children is the '+X.rnd+' scope file\u2019s own figure for the district, not a zero-dose count. Covered % is '+X.camp+'\u2019s own export. A dash in the risk, campaign or EPI columns means IDIMS files that unit under a name the other sources do not use ('+X.noJoin.join(', ')+').',
   {x:0.5,y:6.05,w:12.33,h:0.85,fs:10,i:true});}
 // 4 what to do with each
 {const s=base('What to do with each of them','The action the channels point at, district by district, before '+X.rstartD);
  const A=X.two.slice(0,7).map(x=>cut(x.dn,22)+' ('+x.n+' of 5 channels, '+n0(x.gap)+' children uncovered): '+cut(x.act.join('; ')+'.',230));
  if(!A.length)A.push('No district unit is flagged by two channels on this selection. The single-channel units are listed on the dashboard card.');
  X.three.slice(0,3).forEach(x=>A.push('\u25b8 '+cut(x.dn,22)+' carries '+x.n+' channels: '+cut(x.ev.join(' \u00b7 '),240)));
  bullets(s,A.slice(0,9),{x:0.5,y:1.42,w:12.33,h:4.9,fs:11,ps:7});
  note(s,'Every clause above is generated from the two or more sources that flag that unit, not written by hand: the channel state, the register coverage, routine OPV-3, the risk score and the HRMP spot checks.',
   {x:0.5,y:6.4,w:12.33,h:0.5,fs:10,i:true});}
 // 5 channel state
 {const s=base('The channel itself: who can even see the problem',n0(X.sil.length)+' of '+X.RF.length+' units have a transit point channel that has never filed, stopped filing, or files in under a quarter of the months');
  const w=X.RF.filter(x=>x.posts&&x.n>=1).sort((a,b)=>a.monp-b.monp).slice(0,14);
  bars(s,w.map(x=>cut(x.dn,20)),w.map(x=>Math.round(x.monp*10)/10),AMB,
   {x:0.5,y:1.35,w:7.3,h:5.3,title:'Filed in % of the month slots the window offers',fmt:'0.0',max:100});
  const q=X.RF.filter(x=>x.quiet), l=X.RF.filter(x=>x.lapsed);
  s.addText('What the filing gap means',{x:8.05,y:1.35,w:4.78,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  bullets(s,['Under a quarter of the months is the same guard the PTP section uses: below that, every figure under the row is an undercount rather than a measurement.',
   q.length?n0(q.length)+' unit'+(q.length>1?'s have':' has')+' posts listed in IDIMS with no report at all in the window ('+q.slice(0,3).map(x=>x.dn).join(', ')+(q.length>3?' and '+(q.length-3)+' more':'')+').':'No unit has posts listed with nothing filed at all.',
   l.length?'Stale since the year shown: '+l.slice(0,4).map(x=>x.dn+' ('+PTP.yr[Math.max(0,x.last)]+')').join(', ')+'. A point can still be open with nobody keying anything - this is a reporting fact, not a field visit.':'Every unit with posts has filed at least once in the last year of the window.',
   'A district whose channel is dark cannot be triaged from the panel at all, so its needs are measured by the other four sources alone.'],
   {x:8.05,y:1.75,w:4.78,h:4.6,fs:11});
  note(s,'Bars show the '+X.RF.filter(x=>x.n>=1).length+' units flagged by at least one channel, weakest first, up to 14.',{x:0.5,y:6.68,w:12.33,h:0.3,fs:10,i:true});}
 // 6 the backlog
 {const s=base('The backlog this is chasing',n0(X.gapAll)+' registered zero-dose children on transit point councils had no covered figure after '+X.camp);
  const g=X.RF.filter(x=>x.gap>0).sort((a,b)=>b.gap-a.gap).slice(0,12);
  bars(s,g.map(x=>cut(x.dn,20)),g.map(x=>x.gap),RED,
   {x:0.5,y:1.35,w:7.3,h:5.3,title:'Children reported as zero-dose with no covered figure',fmt:'#,##0'});
  kpis(s,[{l:'Across all units',v:n0(X.gapAll),s:'of '+n0(X.reg)+' children the round reported',vc:RED},
   {l:'Shortlist share',v:X.gapAll?p1(X.gapF/X.gapAll*100)+'%':'\u2013',s:n0(X.gapF)+' children',vc:ORA},
   {l:'At 2+ flag councils',v:n0(X.ug2),s:n0(X.u2.length)+' councils of '+n0(X.ug)+' uncovered',vc:PUR}],AMB,1.35);
  s.addText('Reading it',{x:8.05,y:2.9,w:4.78,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  bullets(s,['The register is the campaign\u2019s own: '+X.camp+' listed these children as never having received a dose, and its covered export does not carry a covered figure for them.',
   'The bars and the first tile add the district rows; the council rows add '+n0(X.ug)+'. A unit whose covered figure runs ahead of what it reported is clamped to zero rather than netted off, so the finer the roll-up the less netting happens.',
   'Councils, not districts, are where the work sits: the '+n0(X.UF.length)+' councils the panel reports hold these '+n0(X.ug)+' children, and the '+n0(X.u2.length)+' flagged by two or more checks hold '+n0(X.ug2)+' of them.'],
   {x:8.05,y:3.3,w:4.78,h:3.1,fs:11});}
 // 7 coverage vs routine
 {const s=base('Register coverage against routine immunity','The same councils measured by the campaign and by routine EPI - a district can look fine on one and fail on the other');
  const g=X.RF.filter(x=>x.gap>0).sort((a,b)=>b.gap-a.gap).slice(0,10);
  bars(s,g.map(x=>cut(x.dn,18)),g.map(x=>x.zp==null?0:Math.round(x.zp*10)/10),ORA,
   {x:0.5,y:1.35,w:6.1,h:4.9,title:X.camp+' covered % of its zero-dose register',fmt:'0.0',max:100});
  bars(s,g.map(x=>cut(x.dn,18)),g.map(x=>x.ep==null?0:Math.round(x.ep*10)/10),GRN,
   {x:6.75,y:1.35,w:5.95,h:4.9,title:'Routine OPV-3 % in the same councils',fmt:'0.0'});
  note(s,'Routine OPV-3 is a cumulative '+X.ep+' window and can exceed 100% where the dose count runs ahead of the recorded surviving-infant denominator; a district with high routine coverage and a large campaign backlog is a register problem, not a refusal problem. '+X.camp+' covered figures are that round\u2019s own export, not yet confirmed by a later round.',
   {x:0.5,y:6.35,w:12.33,h:0.6,fs:10,i:true});}
 // 8 risk overlay
 {const s=base('The risk overlay: councils already named',n0(X.RF.reduce((s2,x)=>s2+(x.hv||0),0))+' very-high or high-risk union councils sit inside the transit point footprint');
  const h=X.RF.filter(x=>x.hv).sort((a,b)=>b.hv-a.hv).slice(0,12);
  bars(s,h.map(x=>cut(x.dn,20)),h.map(x=>x.hv),PUR,
   {x:0.5,y:1.35,w:7.3,h:5.3,title:'Very-high plus high councils on the combined score',fmt:'0'});
  const v=X.RF.filter(x=>x.vh).sort((a,b)=>b.vh-a.vh).slice(0,5);
  s.addText('Why the score is here',{x:8.05,y:1.35,w:4.78,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  bullets(s,['The combined score now folds in the transit point lapse, the register coverage and the HRMP findings, so this column and the channel column are not independent votes for the same district - the risk tier is where the other sources already agree.',
   'Most very-high councils: '+v.map(x=>x.dn+' ('+n0(x.vh)+')').join(', ')+'.',
   X.noJoin.length?'Units with no campaign match ('+X.noJoin.join(', ')+') carry no risk cell: IDIMS files them under a name the campaign district list does not use, and the split cannot be recovered from the name.':'Every unit on the list joins the campaign district list, so each carries a risk cell.',
   'A council already on the risk page needs a named micro-plan target, not a general district reminder.'],
   {x:8.05,y:1.75,w:4.78,h:4.6,fs:11});}
 // 9 HRMP field checks
 {const s=base('What the field checks found','HRMP spot surveys at transit points: unvaccinated under-5s per 100 checklists, never a percentage');
  const f=X.RF.filter(x=>x.srv>=FOC.min&&x.srate!=null).sort((a,b)=>b.srate-a.srate).slice(0,12);
  bars(s,f.map(x=>cut(x.dn,20)),f.map(x=>Math.round(x.srate*10)/10),NV,
   {x:0.5,y:1.35,w:7.3,h:5.3,title:'Unvaccinated under-5s per 100 spot checklists',fmt:'0.0'});
  s.addText('How to read the scale',{x:8.05,y:1.35,w:4.78,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  bullets(s,['The two units are checklists and children, so a survey that finds one unvaccinated child per checklist reads 100. It is a yield, not a coverage rate, and it can pass 100.',
   f.length?'Highest yields: '+f.slice(0,3).map(x=>x.dn+' ('+p1(x.srate)+' per 100 on '+n0(x.srv)+' checklists)').join(', ')+'.':'No unit in this selection reaches the 100-checklist floor the channel uses.',
   'The channel only flags a district at 100+ checklists and 20+ unvaccinated per 100, so a low bar here with a high backlog means the surveys and the transit footprint do not overlap.'],
   {x:8.05,y:1.75,w:4.78,h:4.6,fs:11});
  note(s,'HRMP monitoring data is the freshest field evidence in the build; it is read as a yield per 100 checklists because the survey denominator is checklists, not children.',
   {x:0.5,y:6.5,w:12.33,h:0.4,fs:10,i:true});}
 // 10 readiness
 {const s=base('Nov-26 readiness: can these districts act on it','The four pre-campaign gates, for the units on the shortlist - a need without capacity is not a plan');
  const rows=X.two.filter(x=>x.rd4).slice(0,10).map(x=>[cut(x.dn,22),p1(x.rd4.dpec),p1(x.rd4.must),p1(x.rd4.aic),p1(x.rd4.mpv),
   x.rd4.miss.length?cut(x.rd4.miss.join('; '),72):'All four gates met']);
  table(s,['District','DPEC %','Mandatory staff %','AIC trained %','Micro-plans validated %','Gates still open'],
   rows,{x:0.5,y:1.4,w:12.33,colW:[2.3,1.15,1.6,1.4,2.05,3.83],fs:9,rh:0.4,left:true});
  const miss=X.two.filter(x=>x.rdy&&x.rdy.length);
  bullets(s,[miss.length?n0(miss.length)+' of the '+X.two.length+' shortlisted districts still has a gate open: '+miss.map(x=>x.dn+' - '+x.rdy[0]).join('; ')+'.':'Every shortlisted district with a NEAP row has met all four gates.',
   'Gates below 100 for the DPEC and mandatory members, or below 90 for AIC training and validated micro-plans, count as open in the NEAP reading.',
   X.two.filter(x=>!x.rd4).length?cut(X.two.filter(x=>!x.rd4).map(x=>x.dn).join(', '),200)+' on the shortlist has no NEAP row, so readiness cannot be read for it - ask the district for the returns before the call.':'All shortlisted districts appear in the NEAP return.'],
   {x:0.5,y:5.3,w:12.33,h:1.6,fs:11});}
 // 11 priority councils
 {const s=base('Union councils to brief teams on',n0(X.u3.length)+' councils are flagged by three or more of the six checks - these are the names to read out on the call');
  const rows=X.u3.slice(0,18).map(x=>[cut(x.u,24),cut(x.dn,16),x.t?cut(x.t,12):'',x.n+' of 6',x.tier?(RTL[x.tier][0]):'no score',
   n0(x.zr),n0(x.zc),n0(x.gap),p1(x.ep),x.mon,x.posts,x.map?'yes':'NO']);
  table(s,['Union council','District','Tehsil','Flags','Risk','Reported','Covered','Uncovered','OPV-3 %','Months','PTPs','On map'],
   rows,{x:0.5,y:1.4,w:12.33,colW:[2.5,1.35,0.95,0.6,0.95,0.85,0.8,0.9,0.75,0.62,0.55,0.61],fs:8.5,rh:0.28,left:true});
  note(s,'Reported and covered are '+X.camp+' union-council figures; OPV-3 is the cumulative routine '+X.ep+' window; months and PTPs follow the reporting period on the tab. '+n0(Math.min(X.u3.length,18))+' of '+n0(X.u3.length)+' councils are listed - the rest are on the dashboard card and in its CSV.',
   {x:0.5,y:6.55,w:12.33,h:0.4,fs:10,i:true});}
 // 12 the other two-flag councils
 {const s=base('The rest of the two-flag councils','Two shapes among the '+n0(X.u2.length-X.u3.length)+' councils with exactly two flags - a large uncovered backlog, or a channel barely filing');
  const big=X.u2.filter(x=>x.n===2&&x.gap>=20).sort((a,b)=>b.gap-a.gap).slice(0,9).map(x=>[cut(x.u,24),cut(x.dn,16),n0(x.gap),p1(x.zp),p1(x.ep),x.mon,cut(x.ev[0]||'',48)]);
  table(s,['Union council','District','Uncovered','Covered %','OPV-3 %','Months','Why it is flagged'],big,
   {x:0.5,y:1.4,w:12.33,colW:[2.4,1.4,0.85,0.85,0.8,0.65,5.38],fs:8.5,rh:0.3,left:true});
  const thin=X.u2.filter(x=>x.n===2&&x.gap<20&&x.mon<=2).slice(0,6),
   om=X.offmap.slice().sort((a,b)=>b.zd-a.zd);
  bullets(s,[thin.length?'Thin filing with findings still on the books: '+thin.map(x=>x.u+' ('+x.mon+' month'+(x.mon===1?'':'s')+', '+n0(x.zd)+' '+(x.zd===1?'finding':'findings')+')').join(', ')+'. Keep these posts reporting daily or the findings cannot be followed up.':'No two-flag council here is flagged for thin filing.',
   X.offmap.length?n0(X.offmap.length)+' councils have zero-dose findings recorded under a UC code the KP union-council map does not carry - the biggest are '+om.slice(0,3).map(x=>x.c+' ('+cut(x.dn,16)+', '+n0(x.zd)+' '+(x.zd===1?'finding':'findings')+')').join(', ')+(om.length>3?', and '+(om.length-3)+' more':'')+'. Until that coding is fixed a micro-plan cannot see them.':
    'Every council with findings sits on the KP union-council map.',
   'The '+n0(X.u2.length)+' councils with two or more flags hold '+n0(X.ug2)+' children with no covered figure, inside the '+n0(X.ug)+' the panel reports across its '+n0(X.UF.length)+' councils and a '+n0(X.reg)+'-child register.'],
   {x:0.5,y:4.6,w:12.33,h:2.0,fs:11});}
 // 13 data fixes
 {const s=base('The list depends on these data fixes','Four joins are doing work in the figures above; each one is a decision, not a calculation');
  const A=[];
  if(X.tot&&X.offmap.length)A.push('Mapping: '+n0(X.tot.onmap)+' of '+n0(X.tot.ucs)+' union councils in the panel sit on the KP union-council map. '+n0(X.offmap.length)+' councils with zero-dose findings do not - by findings they are '+X.offmap.slice().sort((a,b)=>b.zd-a.zd).slice(0,4).map(x=>x.c+' ('+n0(x.zd)+')').join(', ')+'. Fix those UC codes first: a finding the map cannot see cannot reach a micro-plan.');
  if(X.noJoin.length)A.push('District naming: IDIMS files '+X.noJoin.join(' and ')+' under names the campaign district list does not use, and the pre-split cannot be recovered. They can still be flagged on their own channel and findings, but they carry no campaign, EPI or risk cell.');
  if(X.noPtp.length)A.push('Missing coverage: '+X.noPtp.join(', ')+' '+(X.noPtp.length>1?'are':'is')+' in the '+X.rnd+' scope with no transit point row in the panel at all, so '+(X.noPtp.length>1?'those districts cannot':'that district cannot')+' appear on this list whatever the field picture.');
  if(X.noTgt.length)A.push(n0(X.noTgt.length)+' of the '+X.RF.length+' transit point units are not in the '+X.rnd+' 27-district scope ('+X.noTgt.slice(0,4).map(x=>x.dn).join(', ')+(X.noTgt.length>4?' and more':'')+'). Their findings are routine-strengthening evidence, not round planning.');
  A.push('Definitions still with IDIMS: '+(X.hold.length?X.hold.join(', '):'the Coverage and OPV columns')+'. Until those are confirmed no PTP coverage percentage appears on any slide in this deck.');
  A.push('Person-level fields are excluded by design: post names, post locations, officer and surveyor names and free-text remarks are not carried into the panel or this deck, because the site is public.');
  bullets(s,A.slice(0,7),{x:0.5,y:1.45,w:12.33,h:5.0,fs:12,ps:10});}
 // 14 actions
 {const s=base('Actions before the round starts on '+X.rstartD,X.two.length?X.two.length+' district units and '+n0(X.u2.length)+' union councils to place':'Nothing is flagged on this selection');
  const A=[], t3=a=>a.slice(0,3).map(x=>x.dn).join(', ')+(a.length>3?' and '+(a.length-3)+' more':'');
  if(X.two.length)A.push('Put '+X.two.length+' districts on the pre-round agenda: '+t3(X.two)+'. Each has two or more independent sources agreeing on the same gap, which is what makes them worth the call time.');
  if(X.three.length)A.push('Start with the '+X.three.length+' at three or more channels: '+t3(X.three)+'. Re-plan house-to-house for their transit councils, not the whole district.');
  if(X.gapF)A.push('Assign the '+n0(X.gapF)+' uncovered children in the shortlist to named teams with a register check, and carry the '+n0(X.u3.length)+' priority councils as named micro-plan targets.');
  const sil2=X.sil; if(sil2.length)A.push('Fix the channel before the count: '+t3(sil2)+' have a transit point channel that is silent, stale or files in under a quarter of the months. Every figure under those rows is an undercount.');
  const rm=X.two.filter(x=>x.rdy&&x.rdy.length);
  if(rm.length)A.push('Escalate readiness: '+rm.map(x=>x.dn+' - '+x.rdy[0]).join('; ')+'. A need without staff is not a plan.');
  if(X.offmap.length)A.push('Correct the '+n0(X.offmap.length)+' council codes the KP map does not carry, or the round will plan around children the panel already found.');
  A.push('Ask IDIMS to confirm what the panel Coverage, Coverage under-5 and above-5 and OPVGiven columns count. Until then no PTP coverage percentage is published here or on any slide.');
  A.push('Re-read this deck after the round: the covered column is '+X.camp+'\u2019s own self-report and is not yet confirmed by an independent pass.');
  bullets(s,A.slice(0,8),{x:0.5,y:1.45,w:12.33,h:5.0,fs:12,ps:10});}
 // 15 sources and limits
 {const s=base('Sources and limits','Read every figure above with these attached');
  bullets(s,['Sources: IDIMS transit point panel '+X.src+', data as at '+X.asof+'; the '+X.camp+' zero-dose report and its own covered export; routine EPI for the '+(X.ep||'window')+'; the combined union-council risk score; HRMP spot surveys and post monitoring; the '+X.rnd+' scope file and the NEAP pre-campaign return.',
   'The panel counts reports, not distinct children. Findings and cross-border columns cannot be turned into coverage and have no denominator here.',
   'Held out until IDIMS confirms the definition: '+(X.hold.length?X.hold.join(', '):'the Coverage, Coverage under-5 and above-5, OPVGiven, OPVUsed, OPVReturned, VacRecvd and aav_cards columns')+'.',
   'Field-check figures are unvaccinated under-5s per 100 spot checklists, not a percentage; one child per checklist reads 100.',
   X.camp+' covered figures are that round\u2019s own export, not yet verified by a later round; routine OPV-3 is cumulative and can exceed 100% where doses run ahead of the recorded denominator.',
   'Union-council coding differs between sources; a dash means the source has no row, not that it found nothing.',
   'Channel flags are judged on the whole '+X.win+' window ('+n0(X.MDen)+' month slots); the report, finding and post counts follow the reporting period set on the tab, currently '+X.SLab+'.',
   'Prepared '+X.date+' from the '+X.scope+' view of the dashboard. This deck is generated, not stored: it is master-only until the owner clears publishing.'],
   {x:0.5,y:1.45,w:12.33,h:5.2,fs:12,ps:9});}
 return pptx;
}
function focusDeckSlug(){const a=(fTeh.value||fDist.value||fDiv.value||'KP');return a.replace(/[^A-Za-z0-9]+/g,'_');}
async function runFocusDeck(btn,st){
 const X=focusDeckData();
 if(!X){st.textContent='No transit point or Nov-26 focus data in this build.';toast('Focus data missing');return;}
 if(!X.RF.length){st.textContent='No district unit in the current selection has transit point reports.';toast('Nothing in this selection');return;}
 btn.disabled=true; st.textContent='Preparing the Nov-26 focus brief\u2026';
 try{await loadPptx(); const pptx=renderFocusDeck(window.PptxGenJS,X);
  const fn='Nov26_Focus_'+focusDeckSlug()+'_'+new Date().toISOString().slice(0,10)+'.pptx';
  await saveDeck(pptx,fn); st.textContent='Downloaded '+fn; toast('Nov-26 focus brief ready');}
 catch(e){console.error(e);
  st.textContent=(e&&e.message==='load')?'Could not load the presentation tool. Check your internet connection and try again.':'Could not create the presentation: '+((e&&e.message)||e);
  toast('Focus brief failed');}
 finally{btn.disabled=false;}
}
const FOC_DECK_BTNS=[['btnFOCDeck','focDeckStatus'],['btnFOCDeck2','focDeckStatus2']];
FOC_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runFocusDeck(b,el(p[1]));});
'''
EDITS = [(BTN_OLD, BTN_NEW), (CARD_OLD, CARD_NEW), ('function renderSurv(){', JS + 'function renderSurv(){')]


def patch(v, dry):
    s = v.text
    v.require('function focDist' in s and 'RF:RF,UF:UF' in s, 'the Nov-26 focus card has to be patched in first')
    v.require(s.count('ugF:ugF') == 1, 'the focus card does not carry ugF, the uncovered total of the flagged councils')
    v.require('function focusDeckData' not in s, 'the focus deck is already in this build')
    v.require(s.count('function renderSurv(){') == 1, 'the js insertion anchor is not unique')
    for old, new in EDITS:
        v.require(s.count(old) == 1, 'anchor found %d times: %r' % (s.count(old), old[:70]))
    js = CRLF(JS.lstrip('\n'))
    v.require(js.startswith(CRLF(JS_START)) and js.endswith(CRLF(JS_LAST)), 'the js block lost its shape')
    v.require('\r\r' not in js, 'the js block carries a doubled CR')
    edits = [(o, n if o != 'function renderSurv(){' else js + o) for o, n in EDITS]
    for old, new in edits:
        s = s.replace(old, new, 1)
    for probe, n in (('function focusDeckData', 1), ('function renderFocusDeck', 1),
                     ('function runFocusDeck', 1), ('FOC_DECK_BTNS', 2),
                     ('id="btnFOCDeck"', 1), ('id="btnFOCDeck2"', 1),
                     ('<button class="btn" id="btnFOCd" title=', 1),
                     ('ug2:F.ugF', 1),
                     ('Nov26_Focus_', 1)):
        v.require(s.count(probe) == n, '%r occurs %d times after the patch (want %d)' % (probe, s.count(probe), n))
    # an id attribute that loses its closing quote silently breaks every wiring line after it
    for bad in ('id="btnFOCd title', 'id="btnFOCDeck title', 'id="btnFOCDeck2 title'):
        v.require(bad not in s, '%s swallows the next attribute' % bad)
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    print('   js +%d chars, %d anchors' % (len(js), len(EDITS)))
    if not dry:
        dashpatch.write_variants([v])


def unpatch(v, dry):
    """Remove the deck by its markers, so wording edits stay reversible."""
    s = v.text
    a, b = s.find(CRLF(JS_START)), s.find('function renderSurv(){')
    v.require(a > 0 and b > a, 'not applied: the js block is not delimited')
    s = s[:a] + s[b:]
    for old, new in EDITS:
        if old == 'function renderSurv(){':
            continue
        v.require(s.count(new) == 1, 'reversal did not match: %r' % new[:70])
        s = s.replace(new, old, 1)
    for probe in ('focusDeckData', 'renderFocusDeck', 'FOC_DECK_BTNS', 'btnFOCDeck', 'Nov26_Focus', 'RF_REG'):
        v.require(probe not in s, '%s survived the removal' % probe)
    v.text = s
    dashpatch.assert_crlf(v)
    print('   removed the Nov-26 focus deck')
    if not dry:
        dashpatch.write_variants([v])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true', help='remove a previously applied focus deck')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    print('variants: ' + ', '.join('%s %s' % (v.rel, v.md5()[:8]) for v in vs))
    sel = [x for x in vs if x.rel == REL]
    if len(sel) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % REL)
    v = sel[0]
    if 'const PTP = ' not in v.text or 'const SND = ' not in v.text:
        raise SystemExit('%s has no PTP or SND payload' % v.rel)
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
