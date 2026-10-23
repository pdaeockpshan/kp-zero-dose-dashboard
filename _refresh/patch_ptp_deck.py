#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Patch the Permanent Transit Point presentations into the dashboard master.

Three things are added, all in index.html only:

1. two PTP slides inside the existing custom presentation deck, placed after the
   ⑨ Missed children slide, so "Recommended actions" and "⑩ Action follow-up" move one
   place down the checkbox numbering (px16 becomes the new pair, px17 / px18 the tail);
2. a standalone, all-detail PTP presentation (renderPTPDeck) with a button on the PTP tab
   and a card on the Presentations tab;
3. a snapshot (PTPX) stashed at the end of the already verified renderPTP, so both decks
   read exactly the figures the tab shows for the same reporting period and the same
   Division / District filters instead of re-deriving the scope a second way.

The period is never re-invented here: ptpCtx() re-runs renderPTP() only when the filter
signature changed, which is what produced the cascading year/month picker in the first
place. Held-out IDIMS columns (Coverage, the OPV fields, post names and locations) stay
out of the slides, and no child name can appear because the payload has none.

All inserted text uses CRLF so the file's line endings stay uniform. Every anchor is
asserted to occur exactly once before editing, and nothing is written unless the whole
patch applies.

Usage: python _refresh/patch_ptp_deck.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

# ---------- 1. PTP_SLIDES entry ----------
A_SLIDES = ("['\u2468 Missed children & surveillance','Still missed, refusals and AFP "
            "surveillance sensitivity','#c2410c'],\r\n"
            " ['Recommended actions','Next steps based on the data','#b45309'],")
SLIDESADD = ("['\u2468 Missed children & surveillance','Still missed, refusals and AFP "
             "surveillance sensitivity','#c2410c'],\r\n"
             " ['Permanent transit points (2 slides)','IDIMS posts, reporting depth, zero-dose signal "
             "and the cross-border counts','#0e7490'],\r\n"
             " ['Recommended actions','Next steps based on the data','#b45309'],")

# ---------- 2. slide counter: the PTP entry renders two slides ----------
A_COUNT = "+(()=>{const c=el('px11');return !c||c.checked!==false?1:0;})();"
COUNTADD = ("+(()=>{const c=el('px11');return !c||c.checked!==false?1:0;})()"
            "+(()=>{const c=el('px16');return !c||c.checked!==false?1:0;})();")

# ---------- 3. deck data carries the PTP context ----------
A_RET = "return {act:atRows().filter(atScope()),mis:"
RETADD = "return {act:atRows().filter(atScope()),ptp:ptpDeckData(),mis:"

# ---------- 4. title slide source block ----------
A_SRC = "+' and EOC line list'}],"
SRCADD = ("+' and EOC line list'},{text:'Permanent transit points: IDIMS PTP panel, '"
          "+(typeof PTP!=='undefined'&&PTP?PTP.win:'panel window'),options:{breakLine:true}}],")

# ---------- 5. the two new slides, and the two renamed blocks ----------
A_ACT = (" // 16 Actions\r\n"
         " if(D.sel[16]){const s=base('Recommended actions'")

A_FU = (" // 17 Action follow-up\r\n"
        " if(D.sel[17]){const s=base('\u2469 Action follow-up'")
FUADD = (" // 18 Action follow-up\r\n"
         " if(D.sel[18]){const s=base('\u2469 Action follow-up'")

# ---------- 6. stash the renderer context ----------
A_STASH = ("   x.zc==null?'':x.zc,x.zp==null?'':p1(x.zp),x.ep==null?'':p1(x.ep)]));\r\n}")
STASHADD = ("   x.zc==null?'':x.zc,x.zp==null?'':p1(x.zp),x.ep==null?'':p1(x.ep)]));\r\n"
            " PTPX={sig:ptpSig(),R:R,UR:UR,DI:DI,SLab:SLab,MDen:MDen,MSl:MSl,MSs:MSs,one:one,mv:mv,"
            "yv:yv,nY:nY,REP:REP,INV:INV,FNP:FNP,FPP:FPP,sF:sF};\r\n}")

# ---------- 7. new top-level JS ----------
A_BRIEFS = "// ---------- QUICK BRIEFS: EOC / DIVISION / DISTRICT ----------"

# ---------- 8. buttons ----------
A_PTNOTE = '<span class="cnt" id="ptNote"></span></div>'
PTNOTEADD = ('<span class="cnt" id="ptNote"></span>'
             '<button class="btn" id="btnPTPDeck" title="Build a PowerPoint of everything on this '
             'tab, for the period picked above">\u25b6 PTP presentation</button>'
             '<span class="cnt" id="ptDeckStatus"></span></div>')

A_PLIST = '<div class="pgrid" id="pList"></div></div>'
PLISTADD = (A_PLIST + '\r\n'
 '<div class="card" style="margin-bottom:14px;border-top:5px solid #0e7490"><h3 style="margin:0">'
 'Permanent transit points</h3>\r\n'
 '<div class="bgrid"><div class="bcard" style="--bc:#0e7490;grid-column:1/-1"><b>\U0001f6e3 PTP '
 'brief</b><small>Everything the IDIMS transit point panel supports on its own: the reporting '
 'calendar by year, reporting depth by district unit, the district league, the zero-dose signal, '
 'the cross-border counts, the post network by status and type, and the same union councils '
 'triangulated against the campaign zero-dose data and routine EPI. Follows the reporting period '
 'on the PTP tab and the Division / District filters above. About 14 slides.</small>\r\n'
 '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'
 '<button class="btn pri" id="btnPTPDeck2">\u25b6 Prepare PTP presentation</button>'
 '<span class="cnt" id="ptDeckStatus2"></span></div></div></div></div>')

MAIN = r"""
 // 16 Permanent transit points (IDIMS)
 if(D.sel[16]){const PT=D.ptp;
  if(!PT){const s=base('Permanent transit points (IDIMS)','0E7490','IDIMS permanent transit point panel');
   note(s,'No permanent transit point data in this build.',{x:0.5,y:2,w:12.3,fs:14});}
  else{const T=PT.tot, cutb=(t,n)=>{t=t==null?'':String(t);return t.length>n?t.slice(0,n-1)+'…':t;};
   const s=base('Permanent transit points (IDIMS)','0E7490','IDIMS PTP panel · '+PT.SLab+' · reports counted, not distinct children');
   kpis(s,[{l:'Transit points',v:n0(T.posts),s:n0(T.rep)+' filed at least one report in the period'},
    {l:'Reports logged',v:n0(T.rows),s:PT.REP+' of '+PT.nd+' district units reporting'},
    {l:'Zero-dose found',v:n0(T.zd),vc:RED,s:p1(T.zpr)+' per 100 reports'},
    {l:'Cross-border counted',v:n0(T.cin),s:n0(T.cout)+' counted leaving'},
    {l:'UCs reporting',v:n0(T.ucS),s:'of '+n0(T.ucs)+' the panel files reports under'}],'0E7490',1.4);
   const RR=PT.R.slice().sort((a,b)=>b.rows-a.rows).slice(0,12);
   bars(s,RR.map(x=>x.dn),RR.map(x=>R(x.zpr)),'0E7490',{x:0.5,y:2.9,w:6.4,h:3.4,title:'Zero-dose found per 100 reports · district units with the most reporting',vt:'Per 100 reports'});
   s.addText('Largest absolute zero-dose totals',{x:7.1,y:2.9,w:5.73,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
   const ZZ=PT.R.slice().sort((a,b)=>b.zd-a.zd).slice(0,8);
   table(s,['District','Reports','Found','Per 100'],ZZ.map(x=>[cutb(x.dn,15),n0(x.rows),n0(x.zd),p1(x.zpr)]),
    {x:7.1,y:3.28,w:5.73,colW:[2.43,1.1,1.1,1.1],col:'0E7490'});
   note(s,'A transit point reports once per day it is open, so these are tallies of reports, not unique children, and they are never a coverage figure. Colour of the bars is the district unit, not performance.',
    {x:0.5,y:6.4,w:12.3,h:0.5,fs:10,i:true});
   const s2=base('Transit points, campaign and routine EPI','0E7490','The same union councils read three ways · '+PT.SLab);
   const G=PT.R.slice().sort((a,b)=>b.zd-a.zd).slice(0,11);
   table(s2,['District','Division','PTP UCs','In campaign data','Covered %','In EPI data','OPV-3 %'],
    G.map(x=>[cutb(x.dn,16),cutb(x.dv,11),n0(x.ucs),n0(x.zn),p1(x.zp),n0(x.euc),p1(x.ep)]),
    {x:0.5,y:1.45,w:8.0,colW:[2.05,1.4,0.9,1.3,0.95,0.85,0.55],col:'0E7490'});
   s2.addText('How to read the pairing',{x:8.75,y:1.45,w:4.08,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
   bullets(s2,['Across these union councils the campaign reported '+n0(T.zrc)+' zero-dose children and covered '+n0(T.zcv)+' ('+p1(T.zp)+'%), while the transit point channel found '+n0(T.zd)+' in '+PT.SLab+'.',
    n0(T.zn)+' of '+n0(T.ucs)+' PTP union councils also appear in the campaign zero-dose export; '+n0(T.euc)+' appear in the KP EPI-MIS file.',
    'Where the transit point channel is busy but the campaign covered share is low, mobile children are reached once and missed again.',
    'Routine OPV-3 is a cumulative window ('+(PT.eper||'the current EPI page')+') and cannot be narrowed to the selected period; above 100% is more doses than the recorded target.',
    'Post names and locations are excluded, and the panel own Coverage and OPV columns are held out until IDIMS confirms what they count.'],
    {x:8.75,y:1.85,w:4.08,h:4.9,fs:11});}
 }

 // 17 Actions
 if(D.sel[17]){const s=base('Recommended actions'"""

PTPJS = r"""
// ---------- PERMANENT TRANSIT POINTS: SLIDE CONTEXT AND STANDALONE DECK ----------
var PTPX=null;
function ptpSig(){
 const dsel=(typeof DSEL==='undefined'||!DSEL)?0:(DSEL.size!=null?DSEL.size:(DSEL.length||0));
 const qq=(typeof q!=='undefined'&&q&&q.value)?q.value.trim():'';
 const yy=el('fPTY')?el('fPTY').value:'0', mm=el('fPTM')?el('fPTM').value:'0';
 return [fDiv.value,fDist.value,dsel,qq,yy,mm].join('|');
}
function ptpCtx(){
 if(typeof PTP==='undefined'||!PTP||!PTP.d||!PTP.d.length)return null;
 if(!PTPX||PTPX.sig!==ptpSig())renderPTP();
 return PTPX;
}
function ptpDeckData(){
 const X=ptpCtx(); if(!X)return null;
 const R=X.R, KI={}, S=k=>R.reduce((s,x)=>s+(x[k]||0),0);
 PTP.k.forEach((k,i)=>{KI[k]=i});
 const CEL=ptpCells();
 const Y=PTP.yr.map((y,j)=>{const a=PTP.k.map(()=>0);
  X.DI.forEach(i=>{const c=CEL.a[i][j]; if(!c)return; for(let m=0;m<a.length;m++)a[m]+=(c[m]||0);});
  return {y:y,rows:a[KI.rows],zd:a[KI.zd],posts:a[KI.posts],ucs:a[KI.ucs],mon:a[KI.months],
   cin:a[KI.cbu_in]+a[KI.cbo_in],cout:a[KI.cbu_out]+a[KI.cbo_out],nbv:a[KI.nbv],expd:a[KI.expd],
   teams:a[KI.teams],sup:a[KI.sup],rep:X.DI.filter(i=>!!CEL.a[i][j]).length};});
 const slot=k=>{const j=PTP.pdk.indexOf(k); return j<0?-1:j;};
 const split=(j,labels)=>labels.map((l,c)=>({l:l,n:X.DI.reduce((s,i)=>s+((((PTP.pd[i]||[])[j]||[])[c])||0),0)}));
 const jt=slot('type'), js=slot('last status'), jr=slot('last security risk');
 const tot={posts:S('posts'),rep:S('rep'),ucS:S('ucS'),ucs:S('ucs'),onmap:S('onmap'),rows:S('rows'),zd:S('zd'),
  cin:S('cin'),cout:S('cout'),nbv:S('nbv'),expd:S('expd'),teams:S('teams'),sup:S('sup'),mon:S('mon'),
  zn:S('zn'),zrc:S('zrc'),zcv:S('zcv'),znc:S('znc'),euc:S('euc'),inv:X.INV,fn:X.FNP};
 tot.zpr=tot.rows?tot.zd/tot.rows*100:null;
 tot.zp=tot.zrc?tot.zcv/tot.zrc*100:null;
 tot.fpp=tot.inv?tot.fn/tot.inv*100:null;
 const zsig=R.filter(x=>x.zpr!=null&&x.rows>=100).sort((a,b)=>b.zpr-a.zpr);
 const quiet=R.filter(x=>x.posts&&!x.rep);
 return {R:R,Y:Y,TY:jt>=0?split(jt,PTP.ty):[],ST:js>=0?split(js,PTP.st):[],RK:jr>=0?split(jr,PTP.rk):[],
  tot:tot,zsig:zsig,quiet:quiet,SLab:X.SLab,MDen:X.MDen,MSl:X.MSl,MSs:X.MSs,one:X.one,mv:X.mv,yv:X.yv,
  nY:X.nY,REP:X.REP,nd:R.length,N:PTP.n||{},win:PTP.win,src:PTP.src,asof:PTP.asof,
  hold:PTP.hold||[],drop:PTP.drop||{},UR:X.UR.slice(),scope:pptScope(),
  camp:(typeof CAMP!=='undefined'&&CAMP[LCP])||'',
  eper:(typeof EMETA!=='undefined'&&EMETA.per)||'',
  odd:(PTP.dr||[]).filter(d=>['KURRAM','CHITRAL','WAZIR-S'].indexOf(d)>=0).join(', '),
  date:new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})};
}
function renderPTPDeck(P,X){
 const pptx=new P(); pptx.layout='LAYOUT_WIDE';
 pptx.title='Permanent Transit Points: '+X.scope; pptx.company='KP Polio and Synergy Dashboard';
 const CYN='0E7490',TEAL='0F766E',GRN='15803D',BLU='1D4ED8',AMB='B45309',RED='DC2626',ORA='C2410C',
  PUR='6D28D9',GRY='6B7280',TXT='1F2937',F='Segoe UI';
 const p1=v=>v==null?'–':v.toFixed(1)+'%', n0=v=>v==null?'–':Math.round(v).toLocaleString('en-US');
 const R=v=>v==null?null:Math.round(v*10)/10;
 const cut=(t,n)=>{t=t==null?'':String(t);return t.length>n?t.slice(0,n-1)+'…':t;};
 let pg=0;
 const base=(title,col,sub)=>{const s=pptx.addSlide(); pg++; s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.12,fill:{color:col},line:{color:col}});
  s.addText(title,{x:0.5,y:0.28,w:12.3,h:0.6,fontFace:F,fontSize:24,bold:true,color:col});
  if(sub)s.addText(sub,{x:0.5,y:0.86,w:12.3,h:0.36,fontFace:F,fontSize:12,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText('Permanent Transit Points · '+X.scope+' · '+X.SLab,{x:0.5,y:7.02,w:10.5,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'});
  return s;};
 const kpis=(s,items,col,y)=>{const n=items.length,gp=0.2,w=(12.33-gp*(n-1))/n;
  items.forEach((it,i)=>{const x=0.5+i*(w+gp),c=it.c||col;
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:1.3,fill:{color:'F9FAFB'},line:{color:'E5E7EB',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:0.07,fill:{color:c},line:{color:c}});
   s.addText(it.l.toUpperCase(),{x:x+0.15,y:y+0.14,w:w-0.3,h:0.3,fontFace:F,fontSize:9,bold:true,color:GRY});
   s.addText(it.v,{x:x+0.15,y:y+0.42,w:w-0.3,h:0.5,fontFace:F,fontSize:it.fs||22,bold:true,color:it.vc||TXT});
   if(it.s)s.addText(it.s,{x:x+0.15,y:y+0.92,w:w-0.3,h:0.3,fontFace:F,fontSize:9,color:GRY});});};
 const note=(s,t,o)=>s.addText(t,{x:o.x,y:o.y,w:o.w,h:o.h||0.4,fontFace:F,fontSize:o.fs||11,color:o.c||GRY,italic:!!o.i,valign:'top'});
 const bars=(s,labels,values,col,o)=>{
  if(!labels.length){note(s,'No data for this selection.',{x:o.x,y:o.y+1.5,w:o.w,fs:13});return;}
  const fs=labels.length>26?7:labels.length>16?8:10, dir=o.dir||'bar';
  const op={x:o.x,y:o.y,w:o.w,h:o.h,barDir:dir,chartColors:[col],showTitle:true,title:o.title,titleFontSize:12,titleColor:TXT,titleFontFace:F,
   showValue:true,dataLabelFontSize:fs,dataLabelColor:TXT,dataLabelFormatCode:o.fmt||'0.0',dataLabelPosition:'outEnd',
   catAxisLabelFontSize:fs,catAxisLabelFontFace:F,catAxisLabelColor:TXT,catAxisOrientation:dir==='bar'?'maxMin':'minMax',
   valAxisLabelFontSize:9,valAxisLabelColor:GRY,valAxisLabelFormatCode:'#,##0',valAxisMinVal:o.min!=null?o.min:0,
   valGridLine:{color:'E5E7EB',size:0.5},showLegend:false,barGapWidthPct:45};
  if(o.max!=null)op.valAxisMaxVal=o.max;
  if(o.vt){op.showValAxisTitle=true;op.valAxisTitle=o.vt;op.valAxisTitleFontSize=9;op.valAxisTitleColor=GRY;}
  s.addChart(pptx.ChartType.bar,[{name:o.name||'Value',labels,values}],op);};
 const table=(s,head,rows,o)=>{
  const hdr=head.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.col},fontSize:9,align:j?'right':'left'}}));
  const body=rows.map((r,i)=>r.map((c,j)=>({text:String(c),options:{fontSize:9,color:TXT,fill:{color:i%2?'FFFFFF':'F9FAFB'},align:j?'right':'left'}})));
  if(!rows.length){note(s,'No data for this selection.',{x:o.x,y:o.y,w:o.w});return;}
  s.addTable([hdr,...body],{x:o.x,y:o.y,w:o.w,colW:o.colW,fontFace:F,rowH:0.3,border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false});};
 const bullets=(s,items,o)=>s.addText(items.map(t=>({text:t,options:{bullet:{indent:16},breakLine:true}})),{x:o.x,y:o.y,w:o.w,h:o.h,fontFace:F,fontSize:o.fs||14,color:TXT,valign:'top',paraSpaceAfter:9});
 const T=X.tot;

 // 1 Cover
 {const s=pptx.addSlide(); pg++; s.background={color:CYN};
  s.addText('Permanent Transit Points',{x:0.8,y:1.45,w:11.7,h:1.0,fontFace:F,fontSize:40,bold:true,color:'FFFFFF'});
  s.addText('IDIMS PTP panel · '+X.scope,{x:0.8,y:2.42,w:11.7,h:0.6,fontFace:F,fontSize:20,color:'A5F3FC'});
  s.addText([{text:'Reporting period: '+X.SLab+'  ·  panel window '+X.win,options:{breakLine:true}},
   {text:'Source: '+X.src+'  ·  data as at '+X.asof,options:{breakLine:true}},
   {text:n0(X.N.read)+' daily rows read, '+n0(X.N.kept)+' kept  ·  '+n0(T.posts)+' transit points  ·  '+n0(X.N.ucs)+' union councils  ·  '+X.nd+' district units',options:{breakLine:true}},
   {text:'Post names and locations are excluded; the panel Coverage and OPV columns are held out until IDIMS confirms what they count',options:{breakLine:true}},
   {text:'Slides never include children names: every figure on these pages is an aggregate',options:{breakLine:true}}],
   {x:0.8,y:3.2,w:11.7,h:2.3,fontFace:F,fontSize:13,color:'BAE6FD',valign:'top',paraSpaceAfter:6});
  s.addText('Prepared '+X.date,{x:0.8,y:6.3,w:8,h:0.4,fontFace:F,fontSize:12,color:'BAE6FD'});}

 // 2 Summary
 {const s=base('Summary',CYN,X.SLab+' · '+X.nd+' district units · '+n0(T.posts)+' transit points');
  kpis(s,[{l:'Transit points',v:n0(T.posts),s:n0(T.rep)+' filed a report in the period'},
   {l:'Reports logged',v:n0(T.rows),s:X.REP+' of '+X.nd+' district units reporting'},
   {l:'Zero-dose found',v:n0(T.zd),vc:RED,s:p1(T.zpr)+' per 100 reports'},
   {l:'Cross-border counted',v:n0(T.cin),s:n0(T.cout)+' counted leaving'},
   {l:'Union councils',v:n0(T.ucS),s:'reporting, of '+n0(T.ucs)+' filed under'}],CYN,1.4);
  const BR=X.R.slice().sort((a,b)=>b.rows-a.rows), DB=X.R.slice().sort((a,b)=>(a.monp==null?-1:a.monp)-(b.monp==null?-1:b.monp));
  const full=X.R.filter(x=>x.monp!=null&&x.monp>=100).length;
  const zs=X.zsig.slice(0,3).map(x=>x.dn+' ('+p1(x.zpr)+')').join(', ');
  bullets(s,['IDIMS logs one report per transit point per day it is open, so every finding here counts reports, not distinct children: a child seen twice in a week is in the tally twice.',
   n0(T.rows)+' reports were logged in '+X.SLab+(BR[0]?', the most in '+BR[0].dn+' ('+n0(BR[0].rows)+' reports, '+n0(BR[0].zd)+' zero-dose finds)':'')+'.',
   full+' of '+X.nd+' district units filed for every month the period offers'+(DB[0]&&DB[0].monp<100?'; the shallowest is '+DB[0].dn+' at '+p1(DB[0].monp):'')+'.',
   zs?'The strongest zero-dose signal per 100 reports, among district units with at least 100 reports, is '+zs+'.':'No district unit reached 100 reports in this period, so per-100 rates are unstable.',
   'Campaign overlap: '+n0(T.zn)+' of '+n0(T.ucs)+' PTP union councils also carry a campaign zero-dose row, covering '+n0(T.zcv)+' of '+n0(T.zrc)+' reported ('+p1(T.zp)+'%).',
   'Routine EPI overlap: '+n0(T.euc)+' of the same union councils have a row in the KP EPI-MIS file.'],
   {x:0.5,y:3.0,w:12.3,h:3.8,fs:12});}

 // 3 Reporting cadence by year
 {const s=base('Reporting cadence by year',TEAL,'Whole panel window '+X.win+' · every year the export holds, for the district units in scope');
  bars(s,X.Y.map(x=>String(x.y)),X.Y.map(x=>x.rows),TEAL,{x:0.5,y:1.45,w:6.2,h:4.3,fmt:'#,##0',title:'Daily reports logged, by year',vt:'Reports'});
  bars(s,X.Y.map(x=>String(x.y)),X.Y.map(x=>x.zd),RED,{x:6.9,y:1.45,w:5.93,h:4.3,fmt:'#,##0',title:'Zero-dose children found, by year',vt:'Findings (reports)'});
  const by=X.Y.slice().sort((a,b)=>b.rows-a.rows)[0], la=X.Y[X.Y.length-1];
  note(s,(by?'The busiest year logged '+n0(by.rows)+' reports in '+by.y+' across '+by.rep+' district units. ':'')+
   (la?'The last year in the window logged '+n0(la.rows)+' reports and '+n0(la.zd)+' zero-dose findings. ':'')+
   'The export is dated '+X.asof+', so the most recent years are shorter than the older ones and a fall is not automatically a decline in activity. Year totals always cover the whole window and are not narrowed by the period selector.',
   {x:0.5,y:5.95,w:12.33,h:0.9,fs:11,i:true});}

 // 4 Reporting depth
 {const s=base('Reporting depth by district unit',CYN,'Share of the months in '+X.SLab+' for which the district unit filed at least one report');
  const DD=X.R.slice().sort((a,b)=>(a.monp==null?-1:a.monp)-(b.monp==null?-1:b.monp));
  bars(s,DD.map(x=>x.dn),DD.map(x=>R(x.monp)),CYN,{x:0.5,y:1.45,w:12.33,h:4.7,min:0,max:100,title:'Reporting months % by district unit ('+X.MSl+' in period: '+X.MDen+')',vt:'% of months reported'});
  note(s,'At 0% the district unit has posts in the panel listing but filed nothing in '+X.SLab+': '+X.quiet.length+' of '+X.nd+' units. Depth is not performance - it is whether the reporting channel is switched on, and every findings column sitting under a shallow bar is an undercount.',
   {x:0.5,y:6.3,w:12.33,h:0.6,fs:11});}

 // 5 District league
 {const s=base('District league: who files what',TEAL,'Sorted by reports logged in '+X.SLab);
  const G=X.R.slice().sort((a,b)=>b.rows-a.rows).slice(0,13);
  table(s,['District','Division','PTPs','Reporting PTPs','Reports','Zero-dose','Per 100','CB entering','CB leaving','Expected child-days'],
   G.map(x=>[cut(x.dn,18),cut(x.dv,12),n0(x.posts),n0(x.rep),n0(x.rows),n0(x.zd),p1(x.zpr),n0(x.cin),n0(x.cout),n0(x.expd)]),
   {x:0.5,y:1.45,w:12.33,colW:[2.2,1.4,0.8,1.15,1.05,1.05,0.9,1.1,1.1,1.58],col:TEAL});
  note(s,'"PTPs" is the panel listing over '+X.win+'; the rest follows the selected period. Expected child-days is the panel own denominator for a day of transit coverage, not a population estimate. Teams active in reports: '+n0(T.teams)+'; supervisor visits: '+n0(T.sup)+'.',
   {x:0.5,y:5.95,w:12.33,h:0.7,fs:11});}

 // 6 Zero-dose signal
 {const s=base('Zero-dose signal at transit points',RED,'Found per 100 daily reports · district units with at least 100 reports in '+X.SLab);
  const Z=X.zsig.slice(0,18);
  bars(s,Z.map(x=>x.dn),Z.map(x=>R(x.zpr)),RED,{x:0.5,y:1.45,w:7.6,h:4.9,title:'Zero-dose found per 100 reports',vt:'Per 100 reports'});
  const TT=X.R.slice().sort((a,b)=>b.zd-a.zd).slice(0,8);
  s.addText('Largest absolute totals',{x:8.35,y:1.45,w:4.48,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  table(s,['District','Found','Reports'],TT.map(x=>[cut(x.dn,16),n0(x.zd),n0(x.rows)]),
   {x:8.35,y:1.83,w:4.48,colW:[2.28,1.1,1.1],col:RED});
  note(s,'Per 100 reports stops one large district from flattening the rest, but a unit with few reports has an unstable rate. Total '+n0(T.zd)+' findings over '+n0(T.rows)+' reports. These are report counts, not unique children, and never a coverage denominator.',
   {x:8.35,y:4.6,w:4.48,h:2.1,fs:11,i:true});}

 // 7 Cross-border
 {const s=base('Cross-border children counted at transit points',BLU,'Under-10 and above-10 columns added together · '+X.SLab);
  const CB=X.R.slice().sort((a,b)=>(b.cin+b.cout)-(a.cin+a.cout)).slice(0,10);
  bars(s,CB.map(x=>x.dn),CB.map(x=>x.cin),BLU,{x:0.5,y:1.45,w:6.2,h:4.2,fmt:'#,##0',title:'Counted entering',vt:'Children counted'});
  bars(s,CB.map(x=>x.dn),CB.map(x=>x.cout),ORA,{x:6.9,y:1.45,w:5.93,h:4.2,fmt:'#,##0',title:'Counted leaving',vt:'Children counted'});
  note(s,'Both directions come from the same daily reports, so a child crossing twice is counted twice, and the age bands stop at 10 - these are not population estimates. In this selection: '+n0(T.cin)+' counted entering against '+n0(T.cout)+' leaving. Read them as which district units sit on a live crossing route, and put the mobile teams and register checks there.',
   {x:0.5,y:5.85,w:12.33,h:0.9,fs:11});}

 // 8 The network itself
 {const s=base('The transit point network',PUR,n0(T.posts)+' posts listed over '+X.win+' · status and security risk are as last reported');
  const RK=X.RK.reduce((a,x)=>a+x.n,0);
  kpis(s,[{l:'Posts listed',v:n0(T.posts),s:X.nd+' district units'},
   {l:'Carry a status',v:n0(T.inv),s:p1(T.fpp)+' recorded functional'},
   {l:'Carry a risk record',v:n0(RK),s:'of '+n0(T.posts)+' posts'},
   {l:'Teams in reports',v:n0(T.teams),s:X.SLab},
   {l:'Supervisor visits',v:n0(T.sup),s:X.SLab}],PUR,1.4);
  s.addText('Status as last reported',{x:0.5,y:2.95,w:4.0,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  table(s,['Status','Posts'],X.ST.map(x=>[x.l,n0(x.n)]),{x:0.5,y:3.3,w:4.0,colW:[2.5,1.5],col:PUR});
  s.addText('Type of transit point',{x:4.7,y:2.95,w:4.0,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  table(s,['Type','Posts'],X.TY.map(x=>[x.l,n0(x.n)]),{x:4.7,y:3.3,w:4.0,colW:[2.7,1.3],col:PUR});
  s.addText('Security risk as last recorded',{x:8.9,y:2.95,w:3.93,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  table(s,['Risk','Posts'],X.RK.map(x=>[x.l,n0(x.n)]),{x:8.9,y:3.3,w:3.93,colW:[2.43,1.5],col:PUR});
  note(s,'Only '+n0(T.inv)+' of '+n0(T.posts)+' posts carry a status at all, so the functional share is read on that subset and silence is not the same as closed. Newborn vaccinations reported at the posts in '+X.SLab+': '+n0(T.nbv)+'.',
   {x:0.5,y:6.0,w:12.33,h:0.6,fs:11});}

 // 9 Campaign triangulation
 {const s=base('Transit points and the campaign zero-dose data',GRN,'The same union councils, not the same children · campaign '+X.camp);
  const G=X.R.slice().sort((a,b)=>b.zd-a.zd).slice(0,13);
  table(s,['District','Division','PTP UCs','In campaign data','Covered figure','PTP zero-dose','Campaign reported','Campaign covered','Covered %'],
   G.map(x=>[cut(x.dn,16),cut(x.dv,11),n0(x.ucs),n0(x.zn),n0(x.znc),n0(x.zd),n0(x.zrc),n0(x.zcv),p1(x.zp)]),
   {x:0.5,y:1.45,w:12.33,colW:[2.1,1.35,1.05,1.3,1.25,1.35,1.5,1.45,0.98],col:GRN});
  note(s,'Across every PTP union council in scope the campaign reported '+n0(T.zrc)+' zero-dose children and covered '+n0(T.zcv)+' ('+p1(T.zp)+'%), against '+n0(T.zd)+' findings logged by the transit point channel in '+X.SLab+'. The covered figure for '+X.camp+' is what that round itself reported and is not yet independently confirmed. A dash means the campaign file has no row for those councils.',
   {x:0.5,y:6.0,w:12.33,h:0.8,fs:11});}

 // 10 EPI triangulation
 {const s=base('Transit points and routine EPI',BLU,'OPV-3 over the same union councils · cumulative '+(X.eper||'EPI window'));
  const G=X.R.filter(x=>x.euc).sort((a,b)=>(a.ep==null?999:a.ep)-(b.ep==null?999:b.ep)).slice(0,13);
  table(s,['District','Division','PTP UCs','UCs in EPI data','Share matched','OPV-3 %'],
   G.map(x=>[cut(x.dn,20),cut(x.dv,13),n0(x.ucs),n0(x.euc),p1(x.ucs?x.euc/x.ucs*100:null),p1(x.ep)]),
   {x:0.5,y:1.45,w:8.0,colW:[2.0,1.45,1.05,1.35,1.1,1.05],col:BLU});
  const NO=X.R.filter(x=>x.ucs&&!x.euc).map(x=>x.dn);
  s.addText('Where the EPI file has nothing',{x:8.75,y:1.45,w:4.08,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  note(s,(NO.length?NO.join(', ')+'. ':'Every district unit with a PTP also has EPI rows. ')+
   'EPI-MIS numbers union councils in its own coding, so a blank cell means no EPI row carried that code, not zero doses given. OPV-3 above 100% is more doses reported than the recorded target for those councils, the same over-entry the EPI pages carry. The routine window is cumulative ('+(X.eper||'current')+') and cannot be narrowed to '+X.SLab+'.',
   {x:8.75,y:1.85,w:4.08,h:4.6,fs:11,i:true,c:TXT});}

 // 11 Focus union councils
 {const s=base('Union councils the panel reports',RED,'Top 13 of '+n0(X.UR.length)+' by zero-dose found over '+X.win+' · the roster is the whole window, not the selected period');
  const U=X.UR.slice(0,13);
  table(s,['Union council','District','Tehsil','UC code','PTPs','Months','Zero-dose found','CB under-10','Campaign covered %','OPV-3 %'],
   U.map(x=>[cut(x.u,22),cut(x.dn,13),cut(x.t,11),String(x.c),n0(x.posts),n0(x.mon),n0(x.zd),n0(x.cbu),p1(x.zp),p1(x.ep)]),
   {x:0.5,y:1.45,w:12.33,colW:[2.3,1.3,1.1,0.95,0.6,0.65,1.2,1.05,1.7,1.48],col:RED});
  note(s,'Council names come from the dashboard UC files, never from the PTP export, which is why a row can read "(name not in the dashboard UC files)". A dash means that source has no row for the council. '+n0(T.ucS)+' of the '+n0(T.ucs)+' councils filed something in '+X.SLab+'; '+n0(T.onmap)+' of the roster sit on the KP UC map.',
   {x:0.5,y:6.0,w:12.33,h:0.7,fs:11});}

 // 12 Silence and gaps
 {const s=base('Where the transit point channel is silent',AMB,'Posts listed but nothing filed in '+X.SLab+', and the mapping gaps behind them');
  const Q=X.quiet.slice(0,12);
  table(s,['District','Division','PTPs listed','UCs in roster','UCs on map','Reports in period'],
   Q.map(x=>[cut(x.dn,18),cut(x.dv,12),n0(x.posts),n0(x.ucs),n0(x.onmap),n0(x.rows)]),
   {x:0.5,y:1.45,w:6.7,colW:[1.7,1.3,1.0,1.0,0.9,0.8],col:AMB});
  s.addText('What a silence can mean',{x:7.45,y:1.45,w:5.38,h:0.35,fontFace:F,fontSize:12,bold:true,color:TXT});
  bullets(s,['The post stopped operating, and the listing was never updated.',
   'It operates but no report was entered in IDIMS for these '+X.MSl+'.',
   'The district unit is one of the IDIMS spellings the dashboard cannot map to the EPI split ('+X.odd+'), so it reports under a code the other pages do not use.',
   'Kohistan Palas appears in the campaign and EPI data but has no PTP report at all in the export.',
   n0(T.ucs-T.ucS)+' union councils in the roster filed nothing in '+X.SLab+' - that is a reporting gap, not proof of no transit traffic.'],
   {x:7.45,y:1.85,w:5.38,h:4.6,fs:11});
  note(s,'Nothing here is presented as vaccination coverage: the panel reports no usable coverage denominator while the Coverage columns stay unconfirmed.',
   {x:0.5,y:6.3,w:12.33,h:0.4,fs:11,i:true});}

 // 13 Limits
 {const s=base('What these numbers can and cannot say',GRY,'Read every column with these limits attached');
  const DP=Object.keys(X.drop).map(k=>k+' ('+n0(X.drop[k])+')').join(', ');
  bullets(s,['The panel counts reports, not distinct children. Findings and cross-border columns cannot be turned into coverage and have no denominator here.',
   'Source '+X.src+', data as at '+X.asof+', generated for the window '+X.win+'. The most recent years are partial.',
   'Rows dropped during extraction: '+(DP||'none')+'. A row is only dropped for an unreadable or impossible year and month - never re-dated.',
   'Held out of the dashboard and these slides until IDIMS confirms the definition: '+X.hold.join(', ')+'.',
   'Post names and post locations are excluded, so a slide can name a union council but never a specific checkpoint.',
   'Expected child-days ('+n0(T.expd)+') is the panel own day-of-transit denominator, not a population; teams '+n0(T.teams)+' and supervisor visits '+n0(T.sup)+' count report entries.',
   'Campaign figures for '+X.camp+' are the same-round self-report, not yet verified by an independent round.',
   'Routine EPI is a cumulative '+(X.eper||'window')+' and cannot be narrowed to '+X.SLab+'; UC coding differs between sources, so a blank is a missing row, not a zero.'],
   {x:0.5,y:1.5,w:12.3,h:5.2,fs:13});}

 // 14 Actions
 {const s=base('Recommended actions',CYN,'Generated from the transit point data for '+X.scope);
  const A=[], top3=(a,f)=>a.slice(0,3).map(f).join(', ')+(a.length>3?' and '+(a.length-3)+' more':'');
  if(X.quiet.length)A.push('Reporting: '+X.quiet.length+' district units have posts listed but filed nothing in '+X.SLab+' ('+top3(X.quiet,x=>x.dn)+'). Confirm whether the points are operating, and fix the entry chain first.');
  const sh=X.R.filter(x=>x.monp!=null&&x.monp<50&&x.rows>0);
  if(sh.length)A.push('Depth: '+top3(sh,x=>x.dn+' ('+p1(x.monp)+')')+' reported in under half the months the period offers, so every figure under them is an undercount.');
  const cl=X.ST.filter(x=>x.n&&/Closed|Non/.test(x.l));
  if(cl.length)A.push('Network: '+cl.map(x=>x.l+' '+n0(x.n)).join(', ')+' of '+n0(T.posts)+' posts are not recorded functional. Re-open them on the busiest routes or drop them from the listing.');
  if(X.zsig.length)A.push('Zero-dose: the strongest signal per 100 reports is '+top3(X.zsig,x=>x.dn+' ('+p1(x.zpr)+')')+'. Pair those points with catch-up rounds and a permanent register check rather than more transit reporting.');
  const CB=X.R.slice().sort((a,b)=>(b.cin+b.cout)-(a.cin+a.cout)).slice(0,3);
  if(CB.length&&T.cin+T.cout)A.push('Cross-border: '+top3(CB,x=>x.dn+' ('+n0(x.cin+x.cout)+')')+' carry most of the counted movement. Put standing teams and door-to-door follow-up on those routes.');
  const lowC=X.R.filter(x=>x.zn>=5&&x.zp!=null&&x.zp<50).sort((a,b)=>a.zp-b.zp);
  if(lowC.length)A.push('Campaign: '+top3(lowC,x=>x.dn+' ('+p1(x.zp)+')')+' have PTP union councils the campaign reports heavily but covers under 50%. These are the districts where mobile children are reached once and missed again.');
  const noE=X.R.filter(x=>x.ucs&&!x.euc);
  if(noE.length)A.push('EPI: '+top3(noE,x=>x.dn)+' has no PTP union council in the routine file. Check the UC coding before concluding the transit network is not catching those children.');
  if(X.RK.length&&T.onmap!=null)A.push('Mapping: '+n0(T.onmap)+' of '+n0(T.ucs)+' PTP union councils sit on the KP UC map; finish the mapping so transit findings can be joined to house-to-house plans.');
  A.push('Definitions: confirm with IDIMS what the panel Coverage, Coverage under-5 and above-5 and OPVGiven columns count. Until then no PTP coverage percentage is published here or on any slide.');
  bullets(s,A.slice(0,9),{x:0.5,y:1.5,w:12.3,h:5.2,fs:A.slice(0,9).length>7?12:13});}
 return pptx;
}
function ptpDeckSlug(){const a=(fTeh.value||fDist.value||fDiv.value||'KP');return a.replace(/[^A-Za-z0-9]+/g,'_');}
async function runPTPDeck(btn,st){
 const X=ptpDeckData();
 if(!X){st.textContent='No permanent transit point data in this build.';toast('PTP data missing');return;}
 if(!X.R.length){st.textContent='No district unit in the current selection has transit point reports.';toast('Nothing in this selection');return;}
 btn.disabled=true; st.textContent='Preparing the transit point presentation…';
 try{await loadPptx(); const pptx=renderPTPDeck(window.PptxGenJS,X);
  const fn='PTP_Update_'+ptpDeckSlug()+'_'+new Date().toISOString().slice(0,10)+'.pptx';
  await saveDeck(pptx,fn); st.textContent='Downloaded '+fn; toast('Transit point presentation ready');}
 catch(e){console.error(e);
  st.textContent=(e&&e.message==='load')?'Could not load the presentation tool. Check your internet connection and try again.':'Could not create the presentation: '+((e&&e.message)||e);
  toast('PTP presentation failed');}
 finally{btn.disabled=false;}
}
const PTP_DECK_BTNS=[['btnPTPDeck','ptDeckStatus'],['btnPTPDeck2','ptDeckStatus2']];
PTP_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runPTPDeck(b,el(p[1]));});
""".replace('\n', '\r\n')

MAIN = MAIN.replace('\n', '\r\n')
# MAIN already carries the renamed Actions header, so the CRLF that opens the raw string goes
ACTADD = MAIN[2:]


def patch(v):
    t = v.text
    anchors = (A_SLIDES, A_COUNT, A_RET, A_SRC, A_ACT, A_FU, A_BRIEFS, A_STASH,
               A_PTNOTE, A_PLIST)
    for a in anchors:
        v.require(t.count(a) == 1,
                  'anchor occurs %d times (want 1): %r' % (t.count(a), a[:56]))
    v.require('function renderPTPDeck(' not in t, 'the PTP deck is already patched in')
    v.require('function ptpDeckData(' not in t, 'the PTP slide context is already patched in')

    t = t.replace(A_SLIDES, SLIDESADD)
    t = t.replace(A_COUNT, COUNTADD)
    t = t.replace(A_RET, RETADD)
    t = t.replace(A_SRC, SRCADD)
    t = t.replace(A_ACT, ACTADD)
    t = t.replace(A_FU, FUADD)
    t = t.replace(A_STASH, STASHADD)
    t = t.replace(A_BRIEFS, PTPJS + '\r\n' + '\r\n' + A_BRIEFS)
    t = t.replace(A_PTNOTE, PTNOTEADD)
    t = t.replace(A_PLIST, PLISTADD)
    v.text = t
    v.changes.append('PTP presentations (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)

    for needle in ('px16', 'ptp:ptpDeckData()', 'PTPX={sig:ptpSig()',
                   'function renderPTPDeck(P,X){', 'async function runPTPDeck(btn,st){',
                   'id="btnPTPDeck"', 'id="btnPTPDeck2"', 'id="ptDeckStatus"',
                   'id="ptDeckStatus2"', "'Permanent transit points (2 slides)'"):
        v.require(needle in t, 'missing after patch: %s' % needle)
    v.require(t.count(' // 18 Action follow-up') == 1 and t.count(' // 17 Actions') == 1,
              'the deck slide numbering did not shift cleanly')
    v.require(t.count('if(D.sel[17]){const s=base(') == 1,
              'two slides claim slot 17')
    v.require(t.count('if(D.sel[18]){const s=base(') == 1,
              'the action follow-up slide lost slot 18')
    v.require(t.count('if(D.sel[16]){const PT=D.ptp;') == 1, 'the PTP pair did not take slot 16')
    v.require(t.count('function renderPTP(') == 1, 'the PTP renderer was duplicated')
    v.require(t.count('PPT_SLIDES=') == 1, 'the slide list was duplicated')


def main():
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'function renderPTP(' not in v.text:
        raise SystemExit('the PTP tab is not in %s yet - run _refresh/patch_ptp_ui.py first'
                         % v.rel)
    patch(v)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK ptp-deck master only - the main deck gained a PTP pair, the standalone PTP '
          'deck is wired to the PTP tab and the Presentations tab')


if __name__ == '__main__':
    main()
