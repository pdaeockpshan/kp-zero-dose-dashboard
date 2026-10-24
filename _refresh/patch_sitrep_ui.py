"""Patch the pre-campaign daily SITREP deck into the dashboard master.

Design rules this build keeps:
  * the deck follows the shape of the programme's own daily SITREPs (the Sept-2026
    "SIA Updates (Daily SITREP)" and "SNID SEPT SITREP" packs in Downloads): cover,
    executive summary at a glance, then numbered sections - scope, preparation status,
    countdown, MPQA, push list, asks - with the source named on every slide;
  * it is a *daily* report: the countdown (D-x to campaign start), which calendar windows
    have closed and which are in window today all move with the day the button is clicked;
  * scope follows the two controls that already exist on the Pre-campaign readiness
    block - the division picker in the briefing card (NEPDV) and the district picked in
    the UC-wise card (NEPUD) - because that section is the only place NEAP is scoped;
  * NEAP is what districts self-report to the EOC portal: a red or grey cell means
    nothing was filed, which is a reporting gap, not proof the activity did not happen.
    Every slide says so where it matters and the last slide names each source with its
    own as-of date;
  * readiness stays the dashboard's own five-indicator mean (DPEC held, must-members,
    AICs trained, teams trained, microplans validated) - no new composite is invented;
  * MPQA stays counts of UCs, not rates, and the bands split only the scored UCs;
  * no coverage percentage is claimed from pre-campaign status, and no child names
    appear - UC names are as reported to the NEAP portal.
Only the master is touched; syncing the other three variants is a publishing action.
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

REL = 'index.html'

A_JS = ("PTP_DECK_BTNS.forEach(p=>{const b=el(p[0]); "
        "if(b)b.onclick=()=>runPTPDeck(b,el(p[1]));});\r\n")

A_BTN = '<button class="btn" id="btnNEPBcopy">Copy briefing</button>'

A_CARD = ('<div class="card"><div class="nbar" style="margin:0;align-items:center">'
          '<button class="btn pri" id="btnPPT"')

BTN_NEW = ('<button class="btn pri" id="btnSITREP">\u25b6 Daily SITREP (pptx)</button>'
           '<span class="cnt" id="sitStatus"></span>')

JS_START = '// ---------- PRE-CAMPAIGN DAILY SITREP'
JS_END = ("SIT_DECK_BTNS.forEach(p=>{const b=el(p[0]); "
          "if(b)b.onclick=()=>runSITREP(b,el(p[1]));});\r\n")
CARD_OPEN = '<div class="card" style="margin-bottom:14px;border-top:5px solid #4338ca">'

CARD_NEW = (
    '<div class="card" style="margin-bottom:14px;border-top:5px solid #4338ca">'
    '<h3 style="margin:0">Pre-campaign daily SITREP</h3>'
    '<div class="bgrid"><div class="bcard" style="--bc:#4338ca;grid-column:1/-1">'
    '<b>\U0001f4c5 Pre-campaign SITREP</b><small>A daily situation report in the house '
    'SITREP shape, for the core-team call: executive summary at a glance, Section 1 scope '
    'and resource plan, Section 2 preparation status (NEAP indicator board, every indicator '
    'by district, readiness spread), Section 3 the countdown calendar against what districts '
    'have actually filed, Section 4 micro-plan quality, the fIPV overlay for Peshawar &amp; '
    'Khyber, Section 5 push list and Section 6 the decisions asked of the core team. Scoped '
    'by the division picker on the Pre-campaign tab. About 12 slides.</small>'
    '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'
    '<button class="btn pri" id="btnSITREP2">\u25b6 Prepare SITREP</button>'
    '<span class="cnt" id="sitStatus2"></span></div></div></div></div>')

JS = r'''

// ---------- PRE-CAMPAIGN DAILY SITREP: SLIDE CONTEXT AND STANDALONE DECK ----------
const nactIso=x=>x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0');
const nactDl=(d,t)=>Math.round((new Date(d+'T00:00:00')-new Date(t+'T00:00:00'))/864e5);
const nactDm=d=>d?NACT_MN[+d.slice(5,7)-1]+' '+(+d.slice(8)):'\u2013';
const SIT_DV={DIKHAN:'D.I. Khan'};
const sitDv=s=>SIT_DV[s]||(s?s.charAt(0)+s.slice(1).toLowerCase():'');
const sitLbl=(o,f)=>String(o||f).replace(/[^A-Za-z0-9]+/g,'_');
const SIT_FI=['PESHAWAR','KHYBER'];
const SIT_BM={dpec:[100,100],dc:[100,100],dho:[100,100],must:[100,100],ucmo:[100,100],ucsec:[100,100],
 aic:[100,100],trn:[100,100],mpv:[100,100],adult:[95,85],loc:[75,50],gov:[75,50],fem:[75,50]};
function sitrepData(){
 if(typeof NEAP==='undefined'||!NEAP||!NEAP.d)return null;
 const dns=Object.keys(NEAP.d); if(!dns.length)return null;
 const di=(typeof NEPUD==='number'&&NEPUD>=0&&NEPUD<dns.length)?dns[NEPUD]:'';
 const dv=di?'':(NEPDV||'');
 const inD=d=>di?(d===di):(dv?(D2DV[d]===dv):true);
 const ALL=nepRows(), R=ALL.filter(r=>inD(r.d)); if(!R.length)return null;
 const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;
 const ixk=k=>NEPK.indexOf(k);
 const mx=k=>avg(R.map(r=>r[k]).filter(v=>v!=null));
 const kp=k=>{const v=(NEAP.tot||[])[ixk(k)];return (v==null||v<0)?null:v;};
 const at100=k=>R.filter(r=>r[k]!=null&&r[k]>=100).length;
 const stt=k=>R.filter(r=>r[k]!=null&&r[k]>0).length;
 const rd=avg(R.filter(r=>r.rd!=null).map(r=>r.rd)), rdAll=avg(ALL.filter(r=>r.rd!=null).map(r=>r.rd));
 const U=(NEAP.u&&NEAP.u.r)?NEAP.u.r:[], UT=(NEAP.u&&NEAP.u.t)?NEAP.u.t:[], uS=U.filter(a=>inD(a[0]));
 const uBy={}; U.forEach(a=>{const b=uBy[a[0]]||(uBy[a[0]]=[0,0,0,0]); b[0]++; if(a[3]>=100)b[1]++; if(a[9]>0)b[2]++;});
 const ucOf=d=>uBy[d]?uBy[d][0]:0;
 const UC=uS.map(a=>{const o={d:a[0],t:UT[a[1]]||'',u:a[2]};NEPK.forEach((k,i)=>o[k]=a[3+i]<0?null:a[3+i]);
  const ms=NEPRD.map(k=>o[k]).filter(v=>v!=null); o.rd=ms.length?avg(ms):null; return o;});
 const IND=NEPK.map(k=>({k:k,l:(NEAP.k[ixk(k)]||[k,k])[1],m:mx(k),q:kp(k),c:at100(k),s:stt(k),
  z:R.filter(r=>r[k]==null).length,bm:SIT_BM[k]||null}));
 const DVS=[...new Set(ALL.map(r=>D2DV[r.d]).filter(Boolean))].sort();
 const DV=DVS.filter(v=>!dv||v===dv).map(v=>{const g=R.filter(r=>D2DV[r.d]===v);
  return {v:v,n:g.length,rd:avg(g.filter(x=>x.rd!=null).map(x=>x.rd)),dpec:g.filter(x=>x.dpec===100).length,
   aic:g.filter(x=>x.aic>0).length,trn:g.filter(x=>x.trn>0).length,mpv:g.filter(x=>x.mpv>0).length,
   uc:g.reduce((a,x)=>a+ucOf(x.d),0)};}).filter(x=>x.n);
 const T1=R.filter(r=>r.dpec==null||r.dpec===0), T1f=T1.filter(r=>SIT_FI.indexOf(r.d)>=0), T1o=T1.filter(r=>SIT_FI.indexOf(r.d)<0);
 const T2=R.filter(r=>r.dpec===100&&!r.aic).sort((a,b)=>ucOf(b.d)-ucOf(a.d));
 const T3=R.filter(r=>r.aic!=null&&r.aic>0&&r.aic<90).sort((a,b)=>a.aic-b.aic);
 const noFem=R.filter(r=>!(r.fem>0)).map(r=>r.d), dhoMiss=R.filter(r=>r.dpec===100&&!r.dho).map(r=>r.d);
 const inacc=R.filter(r=>r.inacc>0), noAtt=R.filter(r=>!(r.ucmo>0)&&!(r.ucsec>0)).map(r=>r.d);
 const noRD=R.filter(r=>r.rd==null).map(r=>r.d);
 const now=new Date(), tIso=nactIso(now);
 const A=(typeof NACT!=='undefined'&&NACT&&NACT.a)?NACT.a:[];
 const CAL=A.map(a=>{const k=NACTMAP[a.n],v=k?mx(k):null,ds=nactDl(a.s,tIso),de=nactDl(a.e,tIso);
  return {n:a.n,t:a.t,s:a.s,e:a.e,x:a.x||'',k:k,v:v,ds:ds,de:de,stt:(de<0?'closed':(ds<=0?'running':'ahead'))};});
 const LATE=CAL.filter(a=>a.stt==='closed'&&a.k&&!(a.v>=100)).sort((a,b)=>a.de-b.de);
 const RUN=CAL.filter(a=>a.stt==='running');
 const NEXT=CAL.filter(a=>a.stt==='ahead').sort((a,b)=>(a.ds-b.ds)||(a.n-b.n));
 const M=(typeof MPQA!=='undefined'&&MPQA&&MPQA.d)?MPQA:null;
 const mr=M?Object.keys(M.d).filter(inD).map(d=>{const v=M.d[d],o={d:d,pl:v[0]||0,sc:v[1]||0,ps:v[2]||0,ni:v[3]||0,si:v[4]||0};
  o.un=o.pl-o.sc; o.sp=o.pl?o.sc/o.pl*100:null; o.pp=o.sc?o.ps/o.sc*100:null; o.u9=o.sc?(o.ni+o.si)/o.sc*100:null; return o;})
  .sort((a,b)=>(b.un-a.un)||(a.pp==null?-1:0)-(b.pp==null?-1:0)||a.pp-b.pp):[];
 const MS=k=>mr.reduce((a,x)=>a+(x[k]||0),0);
 const MP={pl:MS('pl'),sc:MS('sc'),ps:MS('ps'),ni:MS('ni'),si:MS('si')};
 MP.un=MP.pl-MP.sc; MP.sp=MP.pl?MP.sc/MP.pl*100:null; MP.pp=MP.sc?MP.ps/MP.sc*100:null;
 const V=(typeof NOVR!=='undefined'&&NOVR&&NOVR.d)?NOVR:null;
 const SD=((SND&&SND.d)||[]).filter(r=>inD(r[0]));
 const vr=V?Object.keys(V.d).filter(inD).map(dn=>{const arr=V.d[dn],o={d:dn};V.k.forEach((k,i)=>o[k]=arr[i]||0);
  const sd=SD.filter(x=>x[0]===dn)[0]; o.tgS=sd?sd[4]:null; o.dd=o.tgS==null?null:o.tg-o.tgS; return o;})
  .sort((a,b)=>Math.abs(b.dd||0)-Math.abs(a.dd||0)):[];
 const Vsum=k=>vr.reduce((a,x)=>a+(x[k]||0),0);
 const target=SD.reduce((a,r)=>a+(r[4]||0),0), ucsScope=SD.reduce((a,r)=>a+(r[3]||0),0);
 const FI=(typeof FIPV!=='undefined'&&FIPV&&FIPV.tot)?FIPV:null, fiTouch=R.filter(r=>SIT_FI.indexOf(r.d)>=0);
 const campSt=(typeof SND!=='undefined'&&SND&&SND.st)||'';
 const dTo=campSt?Math.ceil((new Date(campSt+'T00:00:00')-now)/864e5):null;
 const dTxt=(dTo==null?'':(dTo>0?('D-'+dTo+' \u00b7 '+dTo+' days to campaign start ('+nactDm(campSt)+')')
  :(dTo===0?('Campaign starts today \u00b7 '+nactDm(campSt))
   :('Campaign under way \u00b7 day '+(1-dTo)+' since '+nactDm(campSt)))));
 const dayL=dTxt?dTxt+' \u00b7 ':'';
 const lb=di?(DNAME(di)+' district'+(D2DV[di]?', '+sitDv(D2DV[di])+' division':''))
  :(dv?sitDv(dv)+' division':'Khyber Pakhtunkhwa (all districts)');
 return {camp:NEAP.camp||((typeof SND!=='undefined'&&SND)?SND.n:'')||'',src:NEAP.src||'',asof:NEAP.asof||'',
  uasrc:(NEAP.u&&NEAP.u.src)||'',uasof:(NEAP.u&&NEAP.u.asof)||'',n:R.length,nAll:ALL.length,di:di,dv:dv,scope:lb,
  R:R,IND:IND,DV:DV,ucOf:ucOf,rd:rd,rdAll:rdAll,mx:mx,at100:at100,stt:stt,
  UC:UC,uN:uS.length,uDpec:uS.filter(a=>a[3]>=100).length,uAic:uS.filter(a=>a[9]>0).length,
  T1o:T1o,T1f:T1f,T2:T2,T3:T3,noFem:noFem,dhoMiss:dhoMiss,inacc:inacc,noAtt:noAtt,noRD:noRD,
  CAL:CAL,LATE:LATE,RUN:RUN,NEXT:NEXT,calSrc:(typeof NACT!=='undefined'&&NACT&&NACT.src)||'',calN:A.length,
  calAsof:(typeof NACT!=='undefined'&&NACT&&NACT.asof)||'',calSt:(typeof NACT!=='undefined'&&NACT&&NACT.st)||'',
  calEn:(typeof NACT!=='undefined'&&NACT&&NACT.en)||'',
  M:M,mr:mr,MP:MP,mpGen:(M&&M.gen)||'',mpSrc:(M&&M.src)||'',mpBand:(M&&M.band)||[],
  V:V,vr:vr,Vsum:Vsum,vSrc:(V&&V.src)||'',vAsof:(V&&V.asof)||'',
  SD:SD,target:target,ucsScope:ucsScope,n5:(typeof SND!=='undefined'&&SND&&SND.n5)||5,
  n3:(typeof SND!=='undefined'&&SND&&SND.n3)||3,d5:(typeof SND!=='undefined'&&SND&&SND.d5)||[],
  sndSrc:(typeof SND!=='undefined'&&SND&&SND.src)||'',
  FI:FI,fiTouch:fiTouch,dFipv:FI?Math.ceil((new Date(FI.st+'T00:00:00')-now)/864e5):null,
  dTo:dTo,campSt:campSt,tIso:tIso,dayL:dayL,
  date:now.toLocaleDateString('en-GB',{day:'2-digit','month':'short',year:'numeric'})};
}
function renderSITREPDeck(P,X){
 const pptx=new P(); pptx.layout='LAYOUT_WIDE';
 pptx.title='Pre-campaign SITREP: '+X.scope+' \u00b7 '+X.camp; pptx.company='KP Polio Programme';
 const IND='4338CA',TEAL='0F766E',GRN='15803D',BLU='1D4ED8',AMB='B45309',RED='DC2626',ORA='C2410C',PUR='6D28D9',
  GRY='6B7280',TXT='1F2937',F='Segoe UI';
 const p1=bp1,n0=bn0,RV=v=>v==null?null:Math.round(v*10)/10,dm=nactDm,dn=DNAME;
 const cut=(t,n)=>{t=t==null?'':String(t);return t.length>n?t.slice(0,n-1)+'\u2026':t;};
 const ABB={dpec:'DPEC %',dc:'DC %',dho:'DHO %',must:'Must %',ucmo:'UCMO %',ucsec:'UC sec %',aic:'AIC %',
  trn:'Team %',mpv:'MP val %',adult:'18+ %',loc:'Local %',gov:'Govt %',fem:'Female %',inacc:'Inacc %'};
 const LBL={}; X.IND.forEach(i=>{LBL[i.k]=i.l;});
 const SC=X.mx('trn'), MPV=X.mx('mpv'), AIC=X.mx('aic');
 const actName=t=>cut(String(t).split(' + ')[0].split(' (')[0],42);
 let pg=0;
 const base=(title,col,sub)=>{const s=pptx.addSlide(); pg++; s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.12,fill:{color:col},line:{color:col}});
  s.addText(title,{x:0.5,y:0.28,w:12.3,h:0.6,fontFace:F,fontSize:23,bold:true,color:col});
  if(sub)s.addText(sub,{x:0.5,y:0.86,w:12.3,h:0.36,fontFace:F,fontSize:11,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText('Pre-campaign SITREP \u00b7 '+X.scope+' \u00b7 '+X.camp+' \u00b7 '+X.date+' \u00b7 NEAP as at '+X.asof,{x:0.5,y:7.02,w:10.5,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'});
  return s;};
 const kpis=(s,items,col,y)=>{const n=items.length,gp=0.2,w=(12.33-gp*(n-1))/n;
  items.forEach((it,i)=>{const x=0.5+i*(w+gp),c=it.c||col;
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:1.3,fill:{color:'F9FAFB'},line:{color:'E5E7EB',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:0.07,fill:{color:c},line:{color:c}});
   s.addText(it.l.toUpperCase(),{x:x+0.13,y:y+0.14,w:w-0.26,h:0.3,fontFace:F,fontSize:8.5,bold:true,color:GRY});
   s.addText(it.v,{x:x+0.13,y:y+0.42,w:w-0.26,h:0.5,fontFace:F,fontSize:it.fs||21,bold:true,color:it.vc||TXT});
   if(it.s)s.addText(it.s,{x:x+0.13,y:y+0.92,w:w-0.26,h:0.32,fontFace:F,fontSize:8.5,color:GRY});});};
 const note=(s,t,o)=>s.addText(t,{x:o.x,y:o.y,w:o.w,h:o.h||0.5,fontFace:F,fontSize:o.fs||11,color:o.c||GRY,italic:!!o.i,valign:'top'});
 const bars=(s,labels,values,col,o)=>{
  if(!labels.length){note(s,'No data for this selection.',{x:o.x,y:o.y+1.5,w:o.w,fs:13});return;}
  const fs=labels.length>26?7:labels.length>16?8:10;
  const op={x:o.x,y:o.y,w:o.w,h:o.h,barDir:'bar',chartColors:[col],showTitle:true,title:o.title,titleFontSize:12,titleColor:TXT,titleFontFace:F,
   showValue:true,dataLabelFontSize:fs,dataLabelColor:TXT,dataLabelFormatCode:o.fmt||'0.0',dataLabelPosition:'outEnd',
   catAxisLabelFontSize:fs,catAxisLabelFontFace:F,catAxisLabelColor:TXT,catAxisOrientation:'maxMin',
   valAxisLabelFontSize:9,valAxisLabelColor:GRY,valAxisLabelFormatCode:'#,##0',valAxisMinVal:o.min!=null?o.min:0,
   valGridLine:{color:'E5E7EB',size:0.5},showLegend:false,barGapWidthPct:45};
  if(o.max!=null)op.valAxisMaxVal=o.max;
  if(o.vt){op.showValAxisTitle=true;op.valAxisTitle=o.vt;op.valAxisTitleFontSize=9;op.valAxisTitleColor=GRY;}
  s.addChart(pptx.ChartType.bar,[{name:o.name||'Value',labels:labels,values:values}],op);};
 const RAG={g:['DCFCE7','166534'],b:['DBEAFE','1E40AF'],a:['FEF3C7','92400E'],r:['FEE2E2','991B1B'],n:['F3F4F6','4B5563']};
 const C_=(t,c,b)=>({t:t,c:c,b:!!b});
 const rdd=v=>v==null?RAG.n:(v>=95?RAG.g:v>=85?RAG.b:RAG.r);
 const stc=v=>v==null?RAG.n:(v>=100?RAG.g:(v>0?RAG.a:RAG.r));
 const inv=v=>v==null?RAG.n:(v>0?RAG.a:RAG.g);
 const cmp=(v,bm)=>v==null?RAG.n:(bm&&bm[0]<100?(v>=bm[0]?RAG.g:v>=bm[1]?RAG.b:RAG.a):stc(v));
 const cell=(r,k)=>{const v=r[k];
  return C_(v==null?'\u2013':p1(v), k==='inacc'?inv(v):(SIT_BM[k]?cmp(v,SIT_BM[k]):stc(v)));};
 const table=(s,head,rows,o)=>{
  if(!rows.length){note(s,o.empty||'No data for this selection.',{x:o.x,y:o.y,w:o.w,fs:o.fs||11});return;}
  const fs=o.fs||10;
  const hdr=head.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.col},fontSize:fs-1,align:j?'center':'left',valign:'middle'}}));
  const body=rows.map((r,i)=>r.map((c,j)=>{const cc=(c&&typeof c==='object')?c:{t:c};
   return {text:String(cc.t==null||cc.t===''?'\u2013':cc.t),options:{fontSize:fs,bold:!!cc.b,color:cc.c?cc.c[1]:TXT,
    fill:{color:cc.c?cc.c[0]:(i%2?'FFFFFF':'F9FAFB')},align:j?'center':'left',valign:'middle'}};}));
  s.addTable([hdr,...body],{x:o.x,y:o.y,w:o.w,colW:o.colW,fontFace:F,rowH:[0.45,...rows.map(()=>o.rh||0.3)],
   border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false,margin:0.03});
  if(o.more)note(s,o.more,{x:o.x,y:o.y+0.45+rows.length*(o.rh||0.3)+0.05,w:o.w,h:0.3,fs:9,i:true});};
 const bullets=(s,items,o)=>s.addText(items.map(t=>({text:t,options:{bullet:{indent:18},breakLine:true}})),
  {x:o.x,y:o.y,w:o.w,h:o.h,fontFace:F,fontSize:o.fs||13,color:TXT,valign:'top',paraSpaceAfter:8});
 const h3=(s,t,y,c)=>s.addText(t,{x:0.5,y:y,w:12.33,h:0.32,fontFace:F,fontSize:12,bold:true,color:c||TXT});
 const blist=(a,f,n)=>{n=n||3;const s=a.slice(0,n).map(f).join(', ');return s+(a.length>n?' and '+(a.length-n)+' more':'');};
 const plu=(n,s)=>n===1?s:s+'s';
 const fiDt=X.FI?dm(X.FI.st):'';

 // 1 Cover
 {const s=pptx.addSlide(); pg++; s.background={color:IND};
  s.addText('PRE-CAMPAIGN DAILY SITREP',{x:0.8,y:1.05,w:11.7,h:0.5,fontFace:F,fontSize:16,bold:true,color:'FFFFFF',charSpacing:3});
  s.addText(X.camp+' \u2014 '+X.scope,{x:0.8,y:1.5,w:11.7,h:1.0,fontFace:F,fontSize:(X.camp+X.scope).length>40?28:32,bold:true,color:'FFFFFF'});
  s.addText(X.dayL?(X.dayL+'report date '+X.date):('Report date '+X.date),{x:0.8,y:2.5,w:11.7,h:0.5,fontFace:F,fontSize:18,color:'C7D2FE'});
  s.addText([{text:'NEAP district status as at '+X.asof+' ('+X.src+')',options:{breakLine:true}},
   {text:X.n+' '+plu(X.n,'district')+' reporting to NEAP in this scope \u00b7 '+n0(X.uN)+' union councils on the UC sheet \u00b7 '+n0(X.ucsScope)+' UCs and '+n0(X.target)+' children in the final scope',options:{breakLine:true}},
   {text:'Campaign '+X.n5+' days in '+X.d5.map(dn).join(' & ')+' and '+X.n3+' days elsewhere \u00b7 activity calendar '+dm(X.calSt)+'\u2013'+dm(X.calEn)+' ('+X.calN+' activities)',options:{breakLine:true}},
   {text:'Readiness = mean of DPEC held, must-members attended, AICs trained, teams trained and microplans validated \u2014 it measures what districts have filed, not children reached',options:{breakLine:true}},
   {text:'Nothing on these slides is a coverage percentage, and no child name appears: UC names are as reported to the NEAP portal',options:{breakLine:true}}],
   {x:0.8,y:3.2,w:11.7,h:2.5,fontFace:F,fontSize:13,color:'E0E7FF',valign:'top',paraSpaceAfter:7});
  s.addText('KP Polio Programme \u00b7 prepared for the core team \u00b7 '+X.date,{x:0.8,y:6.4,w:11.7,h:0.4,fontFace:F,fontSize:12,color:'C7D2FE'});}

 // 2 Executive summary
 {const s=base('Executive summary \u2014 preparation at a glance',IND,X.dayL+'NEAP as at '+X.asof+' \u00b7 '+X.n+' '+plu(X.n,'district')+' in scope');
  const fullN=v=>v===X.n?GRN:(v>0?AMB:RED);
  const femAt=X.R.filter(r=>r.fem!=null&&r.fem>=SIT_BM.fem[0]).length;
  kpis(s,[{l:'Days to campaign',v:(X.dTo==null?'\u2013':(X.dTo>0?('D-'+X.dTo):'Open')),vc:(X.dTo!=null&&X.dTo<=7?RED:TXT),s:dm(X.campSt)+' start'},
   {l:'DPEC held on time',v:X.at100('dpec')+'/'+X.n,vc:fullN(X.at100('dpec')),s:'mean '+p1(X.mx('dpec'))},
   {l:'AICs trained',v:X.at100('aic')+'/'+X.n,vc:fullN(X.at100('aic')),s:'mean '+p1(AIC)},
   {l:'Teams trained',v:X.at100('trn')+'/'+X.n,vc:fullN(X.at100('trn')),s:'mean '+p1(SC)},
   {l:'Microplans validated',v:X.at100('mpv')+'/'+X.n,vc:fullN(X.at100('mpv')),s:'mean '+p1(MPV)},
   {l:'Female member 75%+',v:femAt+'/'+X.n,vc:fullN(femAt),s:'mean '+p1(X.mx('fem'))}],IND,1.4);
  h3(s,'Flags for the core team',2.86,IND);
  const MM=[];
  const nMiss=X.n-X.at100('dpec');
  MM.push(X.dTo<=0?(X.dTo===0?'The round starts today \u2014 this SITREP now reports against the campaign itself.'
    :'The round is under way (day '+(1-X.dTo)+') \u2014 pre-campaign gaps are now in-round risks.')
   :(nMiss?'D-'+X.dTo+' before the '+dm(X.campSt)+' start: '+nMiss+' of '+X.n+' '+plu(X.n,'district')+' in scope '+(nMiss===1?'has':'have')+' no DPEC filed as held on time'
     :'Every one of the '+X.n+' '+plu(X.n,'district')+' in scope has filed a DPEC held on time.')
    +(X.T1f.length?(nMiss===X.T1f.length?' \u2014 '+blist(X.T1f,r=>dn(r.d),2)+', '+(X.T1f.length===1?'which is':'which are')+' in fIPV preparation and '+(X.T1f.length===1?'starts':'start')+' the SNID countdown late by design'
      :', of which '+blist(X.T1f,r=>dn(r.d),2)+' '+(X.T1f.length===1?'is':'are')+' in fIPV preparation')+'.':''));
  MM.push('Mean readiness is '+p1(X.rd)+' against '+p1(X.rdAll)+' for all '+X.nAll+' NEAP districts; teams trained at '+p1(SC)+', micro-plan field validation at '+p1(MPV)+', AIC training at '+p1(AIC)+' with '+X.at100('aic')+' of '+X.n+' districts complete.');
  MM.push(X.LATE.length?(X.LATE.length+' calendar '+(X.LATE.length===1?'window has':'windows have')+' closed with the NEAP figure still short of 100% \u2014 longest: '+blist(X.LATE.slice(0,3),a=>actName(a.t)+' ('+(-a.de)+' days past close)',3)+'.')
   :'No tracked activity has closed with its NEAP figure under 100% \u2014 the risk is all in what is still ahead.');
  if(X.RUN.length)MM.push('In window today: '+blist(X.RUN,a=>actName(a.t),3)+'.');
  if(X.M)MM.push('Micro-plan reviews: '+n0(X.MP.sc)+' of '+n0(X.MP.pl)+' picked UCs reported'+(X.MP.un?' \u2014 '+n0(X.MP.un)+' still to review':' \u2014 all picked UCs reported')+', '+n0(X.MP.ps)+' pass, '+n0(X.MP.ni)+' need improvement, '+n0(X.MP.si)+' with serious issues.');
  MM.push(X.noFem.length?('Team composition is still unfiled in '+X.noFem.length+' district'+(X.noFem.length>1?'s':'')+' ('+blist(X.noFem,dn,3)+') \u2014 female, local and 18+ shares are needed before teams deploy.')
   :'Every district in scope has filed team composition.');
  bullets(s,MM.slice(0,6),{x:0.5,y:3.24,w:12.3,h:3.6,fs:11});}

 // 3 Section 1 - scope and the resource plan
 {const s=base('Section 1 \u2014 campaign scope and the resource plan behind it',GRN,X.camp+' \u00b7 scope '+X.sndSrc+' \u00b7 plan '+X.vSrc+' (as at '+X.vAsof+')');
  const dd=X.Vsum('tg')-X.target;
  kpis(s,[{l:'Districts',v:n0(X.SD.length),s:X.n+' filing to NEAP'},
   {l:'Union councils',v:n0(X.ucsScope),s:n0(X.uN)+' UCs on the NEAP sheet'},
   {l:'Children in scope',v:n0(X.target),s:'final scope workbook'},
   {l:'Plan admin target',v:n0(X.Vsum('tg')),vc:dd===0?GRN:AMB,s:dd===0?'matches the scope':((dd>0?'+':'')+n0(dd)+' against scope')},
   {l:'Mobile team members',v:n0(X.Vsum('mtm')),s:'transit '+n0(X.Vsum('mtt'))+' \u00b7 fixed-site '+n0(X.Vsum('mtf'))},
   {l:'Female AICs planned',v:n0(X.Vsum('mtfa')+X.Vsum('smfa')+X.Vsum('cba')),s:'MT '+n0(X.Vsum('mtfa'))+' \u00b7 SMT '+n0(X.Vsum('smfa'))+' \u00b7 CBV '+n0(X.Vsum('cba'))}],GRN,1.4);
  const vr=X.vr.slice(0,11);
  table(s,['District','UCs','Scope target','Plan target','\u0394 plan vs scope','MT members','MT transit','MT female AICs','CBV members'],
   vr.map(x=>[C_(dn(x.d),null,true),n0(x.uc),n0(x.tgS),n0(x.tg),
    C_(x.dd==null?'\u2013':((x.dd>0?'+':'')+n0(x.dd)),x.dd==null?RAG.n:(x.dd===0?RAG.g:(x.dd>0?RAG.a:RAG.r))),
    n0(x.mtm),n0(x.mtt),n0(x.mtfa),n0(x.cbm)]),
   {x:0.5,y:3.05,w:12.33,colW:[2.05,0.8,1.5,1.4,1.7,1.3,1.1,1.55,0.93],col:GRN,fs:9,rh:0.29,
    more:X.vr.length>11?('Showing 11 of '+X.vr.length+' districts in the plan, largest target difference first.'):''});
  note(s,'The plan is what each district sized its teams against when the scope was issued, for '+X.n5+' campaign days in '+(X.d5.map(dn).join(' & '))+' and '+X.n3+' days elsewhere. A difference between the plan and the final scope workbook is a reconciliation item, not an error in either file.',
   {x:0.5,y:6.4,w:12.33,h:0.55,fs:11});}

 // 4 Section 2 - NEAP indicator board
 {const s=base('Section 2 \u2014 NEAP indicator board',BLU,X.scope+' \u00b7 '+X.n+' '+plu(X.n,'district')+' \u00b7 green = filed complete, amber = under way, red = nothing filed');
  const rows=X.IND.map(x=>{const isI=x.k==='inacc';
   return [C_(x.l,null,true),
    C_(isI?(x.m==null?'not filed':(x.m>0?RV(x.m)+'%':'0%')):(x.m==null?'nothing filed':p1(x.m)),isI?inv(x.m):cmp(x.m,x.bm)),
    x.q==null?'\u2013':p1(x.q),x.c+'/'+X.n,x.s+'/'+X.n,x.z,
    isI?'0% is good':(x.bm?(x.bm[0]===x.bm[1]?(x.bm[0]+'%'):(x.bm[0]+'\u2013'+x.bm[1]+'%')):'100%')];});
  table(s,['Indicator','This scope','All KP (EOC)','Districts at target','Districts started','Districts not filing','Target'],rows,
   {x:0.5,y:1.4,w:12.33,colW:[3.2,1.5,1.35,1.7,1.5,1.63,1.45],col:BLU,fs:10,rh:0.34});
  note(s,'This scope is the mean over the districts in this selection; All KP is the EOC aggregate the dashboard reports. Composition indicators use the programme bands (members 18+ 95\u201385, local / government-accountable / female 75\u201350). Inaccessible areas are better at zero.',
   {x:0.5,y:6.4,w:12.33,h:0.55,fs:11,i:true});}

 // 5 Section 2 - preparation status, every indicator
 {const s=base(X.di?'Section 2 \u2014 preparation status by union council':'Section 2 \u2014 preparation status by district',TEAL,
   'As filed to NEAP \u00b7 grey = nothing filed, red = filed as zero, amber = under way, green = complete \u00b7 '+X.scope);
  if(X.di){
   const ks=['dpec','must','aic','trn','mpv','fem','inacc'], cap=22;
   const U=X.UC.slice().sort((a,b)=>(a.rd==null?-1:a.rd)-(b.rd==null?-1:b.rd));
   table(s,['Union council','Tehsil','Ready'].concat(ks.map(k=>ABB[k])),
    U.slice(0,cap).map(u=>[C_(cut(u.u,34),null,true),cut(u.t,18),C_(p1(u.rd),rdd(u.rd))].concat(ks.map(k=>cell(u,k)))),
    {x:0.5,y:1.32,w:12.33,colW:[3.3,1.6,0.9].concat(ks.map(()=>0.935)),col:TEAL,fs:9,rh:0.215,
     more:U.length>cap?('Showing the '+cap+' weakest of '+U.length+' union councils on this district\u2019s NEAP sheet \u2014 the dashboard lists all.'):''});
   note(s,'These rows are the district\u2019s own NEAP union-council sheet: they show where reporting is thin, not which children were missed. Ready = mean of the five readiness indicators.',
    {x:0.5,y:6.5,w:12.33,h:0.45,fs:11,i:true});
  } else {
   const nD=X.R.length, fs=nD>20?7:8, rh=nD>20?0.185:0.22;
   const ks=X.IND.map(i=>i.k);
   const G=X.R.slice().sort((a,b)=>(a.rd==null?-1:a.rd)-(b.rd==null?-1:b.rd));
   table(s,['District','Ready'].concat(ks.map(k=>ABB[k])),
    G.map(r=>[C_(dn(r.d),null,true),C_(p1(r.rd),rdd(r.rd))].concat(ks.map(k=>cell(r,k)))),
    {x:0.5,y:1.32,w:12.33,colW:[1.85,0.66].concat(ks.map(()=>0.702)),col:TEAL,fs:fs,rh:rh});
   note(s,'Sorted by readiness, weakest first. A grey cell means the district has filed nothing for that indicator \u2014 a reporting chase, not proof the activity was missed. Composition bands: 18+ 95\u201385, local / government-accountable / female 75\u201350; inaccessible areas are better at zero.',
    {x:0.5,y:6.5,w:12.33,h:0.45,fs:10,i:true});}}

 // 6 Section 2 - readiness spread (skipped for a single district, where slide 5 already goes UC-level)
 if(!X.di){const low=X.R.filter(r=>r.rd!=null).sort((a,b)=>a.rd-b.rd);
  const s=base('Section 2 \u2014 readiness spread across the scope',IND,X.dayL+'Mean of the five NEAP readiness indicators \u00b7 target 95% \u00b7 lowest first');
  if(X.di||low.length<=20){
   const cap=18, gg=low.slice(0,cap);
   bars(s,gg.map(r=>cut(dn(r.d),17)),gg.map(r=>RV(r.rd)),IND,{x:0.5,y:1.4,w:12.33,h:Math.min(4.8,0.27*gg.length+1.1),max:100,
    min:Math.min(60,Math.floor(((gg[0]||{rd:90}).rd)/10)*10),fmt:'0.0',
    title:'Readiness % by district ('+gg.length+' of '+low.length+' shown'+(low.length>cap?', lowest first':'')+')',vt:'Readiness (%)'});
   note(s,(X.rdAll==null?'':'Scope average '+p1(X.rd)+' against '+p1(X.rdAll)+' for all '+X.nAll+' NEAP districts. ')
    +(X.noRD.length?X.noRD.length+' district'+(X.noRD.length>1?'s have':' has')+' no readiness figure at all ('+blist(X.noRD,dn,3)+') \u2014 nothing has been filed, which is a chase, not a score. '
     :'Every district in scope has filed at least some readiness. ')
    +(low.length>1?'Lowest: '+dn(low[0].d)+' '+p1(low[0].rd)+', highest: '+dn(low[low.length-1].d)+' '+p1(low[low.length-1].rd)+'.':''),
    {x:0.5,y:6.4,w:12.33,h:0.55,fs:11});
  } else {
   const DV=X.DV.filter(x=>x.rd!=null).sort((a,b)=>a.rd-b.rd), DT=X.DV.slice().sort((a,b)=>(a.rd==null?-1:a.rd)-(b.rd==null?-1:b.rd));
   bars(s,DV.map(x=>cut(sitDv(x.v)+' division',20)),DV.map(x=>RV(x.rd)),IND,{x:0.5,y:1.4,w:6.3,h:4.9,max:100,
    title:'Mean readiness by division',vt:'Readiness (%)'});
   table(s,['Division','Districts','Readiness','DPEC','AIC','Teams','Microplans','UCs'],
    DT.map(x=>[C_(sitDv(x.v),null,true),n0(x.n),C_(p1(x.rd),rdd(x.rd)),x.dpec+'/'+x.n,x.aic+'/'+x.n,x.trn+'/'+x.n,x.mpv+'/'+x.n,n0(x.uc)]),
    {x:6.93,y:1.4,w:5.9,colW:[1.55,0.78,0.95,0.66,0.6,0.62,0.84,0.9],col:IND,fs:9,rh:0.34,empty:'No division data.'});
   note(s,'Division means weight districts equally, so a small division can swing on one district. Readiness is the mean of DPEC held, must-members attended, AICs trained, teams trained and microplans validated.',
    {x:0.5,y:6.5,w:12.33,h:0.45,fs:11});}}

 // 7 Section 3 - countdown calendar against NEAP
 {const s=base('Section 3 \u2014 countdown calendar against what districts filed',TEAL,X.calN+' activities \u00b7 calendar '+X.calSrc+' (as at '+X.calAsof+') \u00b7 NEAP as at '+X.asof);
  const head=['Activity','Planned window','NEAP indicator','Filed in scope','Where this day stands'];
  const rowOf=a=>[C_(a.n+' \u00b7 '+cut(a.t,46),null,true),dm(a.s)+(a.s===a.e?'':' \u2013 '+dm(a.e)),
   a.k?(LBL[a.k]||a.k):'not NEAP-tracked',a.k?(a.v==null?'nothing filed':p1(a.v)):'\u2013',
   C_(a.de<0?('closed '+(-a.de)+'d ago'):(a.de===0?'closes today':(a.ds<=0?'in window':'opens in '+a.ds+'d')),
    a.stt==='closed'?((a.k&&!(a.v>=100))?RAG.r:RAG.g):(a.stt==='running'?RAG.b:RAG.n))];
  const L=X.LATE.slice(0,7);
  h3(s,'Windows closed with the figure still short of 100%',1.35,L.length?RED:GRN);
  if(L.length)table(s,head,L.map(rowOf),{x:0.5,y:1.7,w:12.33,colW:[4.9,2.0,2.0,1.55,1.88],col:RED,fs:9,rh:0.27,
   more:X.LATE.length>7?('Showing 7 of '+X.LATE.length+' slipped windows, longest first.'):''});
  else note(s,'Every activity whose planned window has closed reports 100%, or is not an NEAP-tracked activity. Nothing has slipped on paper.',{x:0.5,y:1.7,w:12.33,fs:12});
  const y2=1.7+0.45+L.length*0.27+(X.LATE.length>7?0.28:0)+0.42;
  const Nx=X.NEXT.slice(0,5);
  h3(s,'Next on the calendar',(y2<2.7?2.7:y2),TEAL);
  table(s,['Activity','Planned window','Opens in','Closes','NEAP tracked?'],
   Nx.map(a=>[C_(a.n+' \u00b7 '+cut(a.t,54),null,true),dm(a.s)+' \u2013 '+dm(a.e),a.ds+' days',dm(a.e),a.k?('yes \u2014 '+(LBL[a.k]||a.k)):'no']),
   {x:0.5,y:(y2<2.7?2.7:y2)+0.34,w:12.33,colW:[4.9,1.9,1.15,1.3,3.08],col:TEAL,fs:9,rh:0.26,
    empty:'Nothing is scheduled ahead \u2014 the calendar window has run out.'});
  note(s,'A closed window with a short figure is a reporting slippage, not proof the activity was missed: NEAP only moves when a district files it.',
   {x:0.5,y:6.5,w:12.33,h:0.45,fs:11,i:true});}

 // 8 Section 4 - micro-plan quality assessment
 {const s=base('Section 4 \u2014 micro-plan quality assessment (MPQA)',PUR,(X.mpGen||X.asof)+' \u00b7 '+X.scope+' \u00b7 counts of UCs, not rates'+(X.MP.un?' \u00b7 '+n0(X.MP.un)+' UCs still to report':''));
  if(!X.M||!X.mr.length){note(s,'No micro-plan quality assessment covers this scope in this build.',{x:0.5,y:3.2,w:12.33,fs:13});}
  else{
   kpis(s,[{l:'UCs planned for MPQA',v:n0(X.MP.pl),s:X.mr.length+' '+plu(X.mr.length,'district')+' in scope'},
    {l:'MPQA reported',v:n0(X.MP.sc),s:p1(X.MP.sp)+' of planned'},
    {l:'MPQA pending',v:n0(X.MP.un),vc:X.MP.un?RED:GRN,s:'not yet reviewed'},
    {l:'Pass (90+)',v:n0(X.MP.ps),s:p1(X.MP.pp)+' of reported'},
    {l:'Needs improvement',v:n0(X.MP.ni),vc:AMB,s:'70\u201389'},
    {l:'Serious issues',v:n0(X.MP.si),vc:X.MP.si?RED:GRN,s:'under 70'}],PUR,1.4);
   const rr=X.mr.slice(0,12);
   table(s,['District','UCs planned','UCs reported','Report %','Pass','Needs improvement','Serious issues','Under 90 % of reported'],
    rr.map(x=>[C_(dn(x.d),null,true),n0(x.pl),n0(x.sc),C_(p1(x.sp),x.sp==null?RAG.n:(x.sp>=60?RAG.g:RAG.r)),
     n0(x.ps),n0(x.ni),C_(n0(x.si),x.si?RAG.r:RAG.g),p1(x.u9)]),
    {x:0.5,y:3.05,w:12.33,colW:[2.1,0.9,0.9,1.65,0.9,1.9,1.5,1.68],col:PUR,fs:9,rh:0.28,
     more:X.mr.length>12?('Showing 12 of '+X.mr.length+' districts with picked UCs, most pending first.'):''});
   note(s,'UCs planned is the list the Federal office assigned to the district, UCs reported is what it has assessed, and the three band columns ('+X.mpBand.join(', ')+') split only the UCs already reported \u2014 so a district can pass everything it has looked at and still be behind on the review.',
    {x:0.5,y:6.4,w:12.33,h:0.55,fs:11,i:true});}}

 // 9 fIPV overlay, only when the scope touches Peshawar or Khyber
 if(X.FI&&X.fiTouch.length){
  const s=base('fIPV overlay \u2014 Peshawar & Khyber',ORA,(X.dFipv>0?('launches in '+X.dFipv+' days ('+dm(X.FI.st)+')')
   :(X.dFipv===0?('launches today ('+dm(X.FI.st)+')'):('launched '+(-X.dFipv)+' days ago ('+dm(X.FI.st)+')')))+' \u00b7 '+X.scope);
  const FI=X.FI, fpd=FI.u.filter(r=>r[0]===0).length, fkd=FI.u.filter(r=>r[0]===1).length;
  const newP=FI.u.filter(r=>r[0]===0&&r[2]).length, newK=FI.u.filter(r=>r[0]===1&&r[2]).length;
  kpis(s,[{l:'fIPV launch',v:dm(FI.st),fs:16,s:FI.n},
   {l:'UCs in fIPV scope',v:n0(FI.tot.uc),s:'Peshawar '+n0(fpd)+' \u00b7 Khyber '+n0(fkd)},
   {l:'Children '+FI.age,v:n0(FI.tot.fipv),s:'fIPV target'},
   {l:'Households under 5',v:n0(FI.tot.hh),s:'door-to-door rounds'},
   {l:'School target',v:n0(FI.tot.sch),s:'school rounds'},
   {l:'New to fIPV scope',v:n0(FI.tot.new),vc:AMB,s:FI.tot.exist+' already in scope'}],ORA,1.4);
  const fiN=blist(X.fiTouch,r=>dn(r.d),2), fiOne=X.fiTouch.length===1;
  bullets(s,[fiN+' '+(fiOne?'is':'are')+' in fIPV preparation up to '+dm(FI.st)+', so '+(fiOne?'its':'their')+' '+X.camp+' DPEC, AIC and team training and micro-plan validation start late \u2014 read '+(fiOne?'its':'their')+' NEAP status against that, not as stalled.',
   'All '+n0(FI.tot.uc)+' fIPV union councils are already inside the '+X.camp+' full-district scope: fIPV is an additional activity, not a change to SNID coverage.',
   'New to the fIPV list this round: Peshawar '+n0(newP)+' UCs, Khyber '+n0(newK)+' UCs \u2014 these have no previous fIPV micro-plan to build on.',
   (fiOne?'The figures above cover the whole fIPV activity (Peshawar and Khyber together), not only the district in this deck; the rest of the province keeps the normal countdown.'
    :'The rest of the province continues on the normal countdown, so a province-wide readiness average is dragged down by these two districts by design.'),
   'Schedule the SNID DPEC and training push for '+fiN+' after the fIPV teams are deployed, and agree which AICs carry both rounds.'],
   {x:0.5,y:3.05,w:12.3,h:3.2,fs:13});}

 // 10 Section 5 - push list
 {const s=base('Section 5 \u2014 push list: who needs the call today',AMB,'One entry per district, in the tier that blocks it first \u00b7 '+X.scope);
  const det=r=>{const o=[];
   if(!(r.dpec>=100))o.push('DPEC '+(r.dpec==null?'not filed':p1(r.dpec)));
   if(!(r.aic>0))o.push('AIC training not started'); else if(r.aic<90)o.push('AICs '+p1(r.aic));
   if(!(r.trn>0))o.push('teams not trained'); else if(r.trn<90)o.push('teams '+p1(r.trn));
   if(!(r.mpv>0))o.push('microplans not validated');
   if(!(r.fem>0))o.push('no female member filed');
   if(SIT_FI.indexOf(r.d)>=0)o.push(fiDt?('fIPV preparation until '+fiDt):'in fIPV preparation');
   return cut(o.slice(0,3).join(' \u00b7 '),86);};
  const tier=(y,title,rows,col,empty)=>{h3(s,title,y,col);
   if(rows.length)table(s,['District','Division','UCs','Ready','What blocks it'],
    rows.map(r=>[C_(dn(r.d),null,true),sitDv(D2DV[r.d]||'\u2013'),n0(X.ucOf(r.d)),C_(p1(r.rd),rdd(r.rd)),det(r)]),
    {x:0.5,y:y+0.33,w:12.33,colW:[1.9,1.5,0.7,0.85,7.38],col:col,fs:9,rh:0.27,
     more:rows.length>5?('Showing 5 of '+rows.length+'.'):''});
   else note(s,empty,{x:0.5,y:y+0.33,w:12.33,fs:12});};
  const t1=X.T1o.concat(X.T1f).slice(0,5);
  tier(1.3,'Tier 1 \u2014 no DPEC filed as held on time',t1,RED,'None \u2014 every district in scope has filed a DPEC held on time.');
  tier(3.1,'Tier 2 \u2014 DPEC held, AIC training not started',X.T2.slice(0,5),ORA,'None \u2014 no district holds a DPEC while waiting to start AIC training.');
  tier(4.9,'Tier 3 \u2014 AIC training started but under 90%',X.T3.slice(0,5),AMB,'None \u2014 every district that started AIC training is at or above 90%.');
  note(s,(X.T1f.length?blist(X.T1f,r=>dn(r.d),2)+' '+(X.T1f.length===1?'stays':'stay')+' in Tier 1 with the fIPV note attached, because the SNID countdown there starts after '+(fiDt?('the '+fiDt+' launch'):'the fIPV launch')+'. ':'')+
   (X.dhoMiss.length?'DPEC held with no DHO on record: '+blist(X.dhoMiss,dn,3)+'. ':'')+
   (X.noAtt.length?'UCMO / UC-secretary attendance unfiled in '+blist(X.noAtt,dn,3)+'.':''),
   {x:0.5,y:6.6,w:12.33,h:0.35,fs:9,i:true});}

 // 11 Section 6 - decisions asked of the core team
 {const s=base('Section 6 \u2014 decisions asked of the core team',IND,X.scope+' \u00b7 '+X.dayL+'NEAP as at '+X.asof);
  const A=[];
  if(X.T1o.length)A.push('DC-level intervention in '+blist(X.T1o,r=>dn(r.d)+' ('+n0(X.ucOf(r.d))+' UCs)',3)+' \u2014 no DPEC filed'+(X.dTo>0?' with '+X.dTo+' days to go':', round already open')+'. Ask for a dated DPEC and a named owner today.');
  else if(X.T1f.length)A.push('Nothing to chase outside the fIPV districts \u2014 '+blist(X.T1f,r=>dn(r.d),2)+' '+(X.T1f.length===1?'files':'file')+' no DPEC because fIPV preparation comes first'+(fiDt?' until '+fiDt:'')+'; agree '+(X.T1f.length===1?'its':'their')+' SNID catch-up dates rather than a push.');
  else A.push('No DPEC chase needed in scope \u2014 every district has filed one held on time.');
  if(X.T2.length)A.push('AIC training to start within 48 hours in '+blist(X.T2,r=>dn(r.d)+' ('+n0(X.ucOf(r.d))+' UCs)',3)+' \u2014 largest UC load first: '+dn(X.T2[0].d)+'.');
  if(X.T3.length)A.push('Close out AIC training before the next report in '+blist(X.T3,r=>dn(r.d)+' '+p1(r.aic),4)+'.');
  A.push(SC>0?('Team training is at '+p1(SC)+': fix a dated plan for '+(X.n>1?'every district in scope':'this district')+(X.dTo>0?' that finishes before '+dm(X.campSt):'')+'.')
   :('Team training has not started anywhere in scope ('+p1(SC)+'): every district needs a named training date this week'+(X.dTo>0?', leaving '+(X.dTo-7)+' days between training and the round':'')+'.'));
  A.push(MPV>0?('Micro-plan field validation is at '+p1(MPV)+': '+(X.n>1?'chase the districts below 100% for their remaining UCs.':'name the UCs still unvalidated and file them before the round.'))
   :'Micro-plan validation shows nothing filed ('+p1(MPV)+'): confirm on the call whether validation happened and was not filed.');
  if(X.M&&X.MP.un)A.push('Clear the '+n0(X.MP.un)+' pending micro-plan review'+(X.MP.un>1?'s':'')+' \u2014 furthest behind: '+blist(X.mr.filter(r=>r.un>0),r=>dn(r.d)+' ('+n0(r.un)+' left)',3)+'.');
  if(X.noFem.length)A.push('Female, local and 18+ composition to be filed with the next NEAP update by '+blist(X.noFem,dn,3)+' \u2014 teams cannot deploy without it.');
  if(X.inacc.length)A.push('Inaccessible areas filed in '+blist(X.inacc,r=>dn(r.d)+' ('+RV(r.inacc)+'%)',3)+' \u2014 agree security escorts and market-based strategies before the round.');
  if(X.dhoMiss.length)A.push('Ask the DHO'+(X.dhoMiss.length>1?'s':'')+' of '+blist(X.dhoMiss,dn,3)+' why no DHO is on record for a DPEC that was held.');
  bullets(s,A.slice(0,8),{x:0.5,y:1.45,w:12.3,h:5.3,fs:A.slice(0,8).length>6?12:13});}

 // 12 Provenance and limits
 {const s=base('What this SITREP can and cannot say',GRY,'Report date '+X.date+' \u00b7 every source named with its own as-of date');
  bullets(s,[X.camp+' district NEAP: '+X.src+', as at '+X.asof+(X.uasrc?'; UC-wise '+X.uasrc+', as at '+X.uasof:'')+'. This is what districts file to the EOC portal \u2014 a red or grey cell means nothing was filed, which is a reporting gap, not proof the activity did not happen.',
   'Readiness = mean of DPEC held on time, must-members attended, AICs trained, teams trained and microplans validated \u2014 the same five the dashboard table uses. A district with blanks averages only what it filed.',
   'Activity calendar: '+X.calSrc+' (as at '+X.calAsof+'); planned windows are as drawn by PEOC/NEOC, campaign days '+dm(X.calSt)+'\u2013'+dm(X.calEn)+'. A closed window with a short NEAP figure is a slippage in reporting.',
   X.M?('Micro-plan quality: '+X.mpSrc+', generated '+X.mpGen+' \u2014 counts of UCs, and the bands ('+X.mpBand.join(', ')+') split only the UCs already reported.'):'No micro-plan assessment in this build.',
   X.V?('Resource plan: '+X.vSrc+', as at '+X.vAsof+', issued with the scope ('+X.sndSrc+', campaign start '+dm(X.campSt)+'): team counts are what districts planned against, not who is on the ground today.'):'No resource plan in this build.',
   'Generated on '+X.tIso+' \u2014 the countdown, the closed windows, the tiers and the asks all move daily, so re-download it rather than reusing yesterday\u2019s file.',
   'No coverage percentage is derived from pre-campaign status: readiness measures reporting completion, not children reached. Nothing here counts protected children, and no child name appears \u2014 UC names are as reported to the NEAP portal.',
   'Scope follows the controls on the Pre-campaign readiness tab: the division picker and the district picked in the UC-wise card. '+X.n+' of '+X.nAll+' NEAP districts are in this deck.'],
   {x:0.5,y:1.5,w:12.3,h:5.2,fs:12});}
 return pptx;
}
async function runSITREP(btn,st){
 const X=sitrepData();
 if(!X){st.textContent='No NEAP pre-campaign data in this build.';toast('Pre-campaign data missing');return;}
 btn.disabled=true; st.textContent='Preparing the pre-campaign SITREP\u2026';
 try{await loadPptx(); const pptx=renderSITREPDeck(window.PptxGenJS,X);
  const fn='PreCampaign_SITREP_'+sitLbl(X.di||X.dv||'KP')+'_'+new Date().toISOString().slice(0,10)+'.pptx';
  await saveDeck(pptx,fn); st.textContent='Downloaded '+fn+' \u00b7 '+X.dayL+'NEAP as at '+X.asof; toast('Pre-campaign SITREP ready');}
 catch(e){console.error(e);
  st.textContent=(e&&e.message==='load')?'Could not load the presentation tool. Check your internet connection and try again.':'Could not create the SITREP: '+((e&&e.message)||e);
  toast('Pre-campaign SITREP failed');}
 finally{btn.disabled=false;}
}
const SIT_DECK_BTNS=[['btnSITREP','sitStatus'],['btnSITREP2','sitStatus2']];
SIT_DECK_BTNS.forEach(p=>{const b=el(p[0]); if(b)b.onclick=()=>runSITREP(b,el(p[1]));});
'''


def patch(v, dry):
    s = v.text
    for probe in ('function sitrepData', 'btnSITREP', 'Pre-campaign daily SITREP', 'nactIso'):
        v.require(s.count(probe) == 0, 'already present (%s)' % probe)
    for anchor in (A_JS, A_BTN, A_CARD):
        v.require(s.count(anchor) == 1, 'anchor found %d times: %r' % (s.count(anchor), anchor[:60]))

    js = JS.lstrip('\n').replace('\n', '\r\n')
    v.require(js.startswith(JS_START) and js.endswith(JS_END),
              'the js block no longer sits between the un-patch markers')
    s = s.replace(A_JS, A_JS + js, 1)
    s = s.replace(A_BTN, BTN_NEW + A_BTN, 1)
    s = s.replace(A_CARD, CARD_NEW + A_CARD, 1)
    v.require(s.count('function sitrepData') == 1, 'sitrepData insert failed')
    v.require(s.count('function renderSITREPDeck') == 1, 'renderSITREPDeck insert failed')
    v.require(s.count('id="btnSITREP"') == 1, 'pre-campaign button insert failed')
    v.require(s.count('id="btnSITREP2"') == 1, 'presentations button insert failed')
    v.require(s.count('PreCampaign_SITREP_') == 1, 'filename convention missing')
    v.require(s.count('runSITREP(b,el(p[1]))') == 1, 'button wiring missing')
    v.require(s.count("st.textContent='Preparing the pre-campaign SITREP") == 1, 'status wiring missing')
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    print('   sitrep js +%d chars, pre-campaign button +%d, presentations card +%d'
          % (len(js), len(BTN_NEW), len(CARD_NEW)))
    if not dry:
        dashpatch.write_variants([v])


def unpatch(v, dry):
    """Strip an applied SITREP block by its markers, so a revision can be re-applied."""
    s = v.text
    for probe in ('function sitrepData', 'PreCampaign_SITREP_', 'id="btnSITREP"',
                  'id="btnSITREP2"', 'Pre-campaign daily SITREP'):
        v.require(probe in s, 'not applied: %r' % probe)
    a = s.find(JS_START)
    b = s.find(JS_END)
    v.require(a > 0 and b > a, 'the inserted js region is not delimited by %r / %r' % (JS_START, JS_END))
    s = s[:a] + s[b + len(JS_END):]
    v.require(s.count(BTN_NEW) == 1, 'the pre-campaign button is not where it was inserted')
    s = s.replace(BTN_NEW, '', 1)
    c = s.find(CARD_OPEN)
    v.require(c > 0, 'the presentations card is not where it was inserted')
    n = s.find(A_CARD, c)
    v.require(n > c, 'the card after the SITREP card is missing - refusing to guess its end')
    s = s[:c] + s[n:]
    for probe in ('sitrepData', 'renderSITREPDeck', 'btnSITREP', 'nactIso', 'SIT_BM', CARD_OPEN):
        v.require(probe not in s, '%s survived the removal' % probe)
    v.text = s
    dashpatch.assert_crlf(v)
    print('   removed the SITREP block')
    if not dry:
        dashpatch.write_variants([v])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true',
                    help='remove a previously applied SITREP block so the deck can be revised')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    print('variants: ' + ', '.join('%s %s' % (v.rel, v.md5()[:8]) for v in vs))
    sel = [x for x in vs if x.rel == REL]
    if len(sel) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % REL)
    v = sel[0]
    if 'function renderNEP' not in v.text:
        raise SystemExit('the pre-campaign NEAP block is not in %s yet' % v.rel)
    if a.unpatch:
        print('un-patching master only (%s)' % v.rel)
        unpatch(v, a.dry_run)
    else:
        print('patching master only (%s)' % v.rel)
        patch(v, a.dry_run)
    print('   %s: %.1f KB -> %.1f KB (%+.1f KB)'
          % (v.rel, len(v.orig) / 1024.0, len(v.text) / 1024.0, v.delta() / 1024.0))
    print('   md5 %s' % v.md5())
    if a.dry_run:
        print('DRY RUN: nothing written.')
    else:
        print('master only: push_master.py needs the owner\u2019s word before the other three variants follow.')


if __name__ == '__main__':
    main()
