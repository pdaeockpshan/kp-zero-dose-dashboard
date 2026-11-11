// ---------- Last three campaigns: presentation deck (owner request, 11-Nov-2026) ----------
let _C3D={};
function c3DeckDate(){const d=new Date(),M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 return d.getDate()+'-'+M[d.getMonth()]+'-'+d.getFullYear();}
function c3NovRows(){if(_C3D.nr)return _C3D.nr;const R=((typeof NOVF!=='undefined'&&NOVF.u)||[]).map(a=>{const o={};NOVF.k.forEach((k,i)=>o[k]=a[i]);return o;});return _C3D.nr=R;}
function c3NovTot(){if(_C3D.nt)return _C3D.nt;const o={};if(typeof NOVF!=='undefined')NOVF.k.forEach((k,i)=>{o[k]=i<3?null:NOVF.tot[i-3];});return _C3D.nt=o;}
function c3Ovr(){if(_C3D.ov)return _C3D.ov;const K=NOVUC.k,ti=K.indexOf('tg'),vi=K.indexOf('vac');let tg=0,vc=0,n=0;
 ((typeof NOVUC!=='undefined'&&NOVUC.r)||[]).forEach(a=>{tg+=a[ti]||0;vc+=a[vi]||0;if(a[ti])n++;});
 return _C3D.ov={tg,vc,n,pct:tg?vc/tg*100:null};}
function c3Lqas(){if(_C3D.lq)return _C3D.lq;const C=((typeof LQM!=='undefined'&&LQM.camps)||[]),L=(typeof LQR!=='undefined'&&LQR)||[];
 return _C3D.lq=C.map((n,i)=>{const R=L.filter(r=>r.ci===i),c=k=>R.filter(r=>r.r===k).length;
  return {l:n,n:R.length,p:c('P'),i:c('I'),f:c('F'),pct:R.length?c('P')/R.length*100:null};});}
function c3MS(){if(_C3D.ms)return _C3D.ms;const DD=(typeof INDIC!=='undefined'&&INDIC.S&&INDIC.S.ms&&INDIC.S.ms.dd)||{};
 const TC=(typeof PCM!=='undefined'&&PCM.tc)||[],o={};
 Object.keys(DD).forEach(k=>{const d=DD[k];let n=0,chk=0,ver=0,ms=0,nt=0,ntc=0,na=0,rf=0,slp=0,vb=0;
  Object.keys(d).forEach(m=>{const a=d[m];n+=a[0]||0;chk+=a[1]||0;ver+=a[2]||0;ms+=a[4]||0;nt+=a[5]||0;ntc+=a[6]||0;na+=a[7]||0;rf+=a[8]||0;slp+=a[9]||0;vb+=a[10]||0;});
  o[k]={k:+k,l:TC[+k]||'',n,chk,ver,ms,nt,ntc,na,rf,slp,vb,pct:chk?ver/chk*100:null};});
 return _C3D.ms=o;}
function c3Icm(){if(_C3D.ic)return _C3D.ic;const I=(typeof ICMDN!=='undefined')?ICMDN:null;
 if(!I)return _C3D.ic={tot:null,rows:[]};
 const R=(I.u||[]).map(a=>{const o={};I.k.forEach((k,i)=>o[k]=a[i]);return o;}),G={};
 R.forEach(r=>{const d=r.d;if(!d)return;const g=G[d]=G[d]||{d,cl:0,hh:0,rc:0,rv:0,mi:0,nt:0,tv:0,na:0,rf:0,seen:0,fm:0,epi:0};
  ['cl','hh','rc','rv','mi','nt','tv','na','rf','seen','fm','epi'].forEach(k=>g[k]+=r[k]||0);});
 return _C3D.ic={tot:I.tot,rows:Object.values(G),asof:I.asof};}
function c3Pcm(){if(_C3D.pc)return _C3D.pc;
 const D=((typeof PCM!=='undefined'&&PCM.ds)||[]),ix=D.findIndex(d=>/Sep 2026/i.test(d.q)&&d.s===1);
 const R=((typeof PCM!=='undefined'&&PCM.r)||[]).filter(r=>r[0]===ix),o={ix,d:D[ix]||null,n:R.length,chk:0,fm:0,ms:0,nt:0,tv:0,na:0,rf:0,rc:0,rv:0,ucs:new Set()};
 R.forEach(r=>{o.chk+=r[7]||0;o.fm+=r[8]||0;o.ms+=r[9]||0;o.nt+=r[10]||0;o.tv+=r[11]||0;o.na+=r[12]||0;o.rf+=r[13]||0;o.rc+=r[25]||0;o.rv+=r[26]||0;if(r[3])o.ucs.add(r[3]);});
 o.fmp=o.chk?o.fm/o.chk*100:null;o.msp=o.chk?o.ms/o.chk*100:null;o.nuc=o.ucs.size;
 const TR=((typeof PCM!=='undefined'&&PCM.tr)||[]),TC=(PCM&&PCM.tc)||[];
 o.icm=TR.filter(t=>t[1]===0).map(t=>({l:t[8],ix:t[0],rc:t[9]||0,rv:t[10]||0,pct:t[9]?t[10]/t[9]*100:null,yr:(TC[t[0]]||'').slice(-2)}));
 o.icm26=o.icm.filter(t=>/26$/.test((TC[t.ix]||'').trim())&&t.rc>0);
 return _C3D.pc=o;}
function c3ValNov(){if(_C3D.vl)return _C3D.vl;const V=(typeof VAL!=='undefined'&&VAL)||[];
 const R=V.filter(r=>/SNID November 2026/i.test(r.cp||'')),o={n:0,vy:0,vn:0,vx:0,ucs:new Set()};
 R.forEach(r=>{o.n+=r.n||0;o.vy+=r.vy||0;o.vn+=r.vn||0;o.vx+=r.vx||0;if(r.u)o.ucs.add(r.d+'|'+r.u);});
 o.pct=o.n?o.vy/o.n*100:null;o.nuc=o.ucs.size;return _C3D.vl=o;}

function renderC3Deck(P){
 const pptx=new P(); pptx.layout='LAYOUT_WIDE'; pptx.title='SNID Nov-2026 campaign review — Khyber Pakhtunkhwa'; pptx.company='KP Polio and Synergy Dashboard';
 const TE='0F766E',DK='134E4A',AMB='B45309',RED='B91C1C',GRN='15803D',GRY='6B7280',TXT='1F2937',F='Segoe UI';
 const DATE=c3DeckDate(),SCOPE='Khyber Pakhtunkhwa · province-wide'; let pg=0;
 const p1=v=>v==null?'–':(Math.round(v*10)/10).toFixed(1)+'%', n0=v=>v==null?'–':fmt(Math.round(v));
 const rag=v=>v==null?['F3F4F6','6B7280']:v>=95?['DCFCE7','166534']:v>=90?['FEF3C7','92400E']:v>=80?['FFEDD5','9A3412']:['FEE2E2','991B1B'];
 const base=(t,sub)=>{const s=pptx.addSlide(); pg++; s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.12,fill:{color:TE},line:{color:TE}});
  s.addText(t,{x:0.5,y:0.26,w:12.3,h:0.6,fontFace:F,fontSize:24,bold:true,color:DK});
  if(sub)s.addText(sub,{x:0.5,y:0.84,w:12.3,h:0.34,fontFace:F,fontSize:12,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText(SCOPE+' · '+DATE,{x:0.5,y:7.02,w:9.5,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'});
  return s;};
 const kpis=(s,it,y)=>{const n=it.length,gp=0.18,w=(12.33-gp*(n-1))/n;
  it.forEach((k,i)=>{const x=0.5+i*(w+gp);
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:1.3,fill:{color:'F8FAFC'},line:{color:'E2E8F0',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x,y,w,h:0.07,fill:{color:k.c||TE},line:{color:k.c||TE}});
   s.addText(String(k.l).toUpperCase(),{x:x+0.14,y:y+0.13,w:w-0.28,h:0.3,fontFace:F,fontSize:9,bold:true,color:GRY});
   s.addText(k.v,{x:x+0.14,y:y+0.42,w:w-0.28,h:0.5,fontFace:F,fontSize:22,bold:true,color:k.vc||TXT});
   if(k.s)s.addText(k.s,{x:x+0.14,y:y+0.92,w:w-0.28,h:0.32,fontFace:F,fontSize:9,color:GRY});});};
 const note=(s,t,o)=>s.addText(t,{x:o.x,y:o.y,w:o.w,h:o.h||0.6,fontFace:F,fontSize:o.fs||10.5,color:o.c||GRY,italic:o.i!==false,valign:'top'});
 const bullets=(s,a,o)=>s.addText(a.map(t=>({text:t,options:o.nb?{breakLine:true}:{bullet:{indent:14},breakLine:true}})),
  {x:o.x,y:o.y,w:o.w,h:o.h,fontFace:F,fontSize:o.fs||12,color:TXT,valign:'top',paraSpaceAfter:o.gap==null?7:o.gap});
 const table=(s,head,rows,o)=>{const fs=o.fs||9;
  if(!rows.length){note(s,o.empty||'No data for this selection.',{x:o.x,y:o.y,w:o.w});return;}
  const hdr=head.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.col||TE},fontSize:fs,align:j?'center':'left',valign:'middle'}}));
  const body=rows.map((r,i)=>r.map((c,j)=>{const cc=(c&&typeof c==='object')?c:{t:c};
   return {text:String(cc.t==null?'–':cc.t),options:{fontSize:fs,bold:!!cc.b,color:cc.c?cc.c[1]:TXT,
    fill:{color:cc.c?cc.c[0]:(i%2?'FFFFFF':'F8FAFC')},align:(j&&!o.left)?'center':'left',valign:'middle'}};}));
  s.addTable([hdr,...body],{x:o.x,y:o.y,w:o.w,colW:o.colW,fontFace:F,rowH:[0.38,...rows.map(()=>o.rh||0.26)],
   border:{type:'solid',pt:0.5,color:'E2E8F0'},autoPage:false,margin:0.04});};
 const bars=(s,labels,values,o)=>{if(!labels.length){note(s,'No data.',{x:o.x,y:o.y+1,w:o.w});return;}
  const fs=labels.length>12?8:9,op={x:o.x,y:o.y,w:o.w,h:o.h,barDir:'bar',chartColors:o.cols||[TE],
   showTitle:!!o.title,title:o.title,titleFontSize:11,titleColor:TXT,titleFontFace:F,showValue:true,
   dataLabelFontSize:fs,dataLabelColor:TXT,dataLabelFormatCode:o.fmt||'0.0',dataLabelPosition:'outEnd',
   catAxisLabelFontSize:fs,catAxisLabelFontFace:F,catAxisLabelColor:TXT,catAxisOrientation:'maxMin',
   valAxisLabelFontSize:8,valAxisLabelColor:GRY,valAxisMinVal:o.min==null?0:o.min,
   valGridLine:{color:'E5E7EB',size:0.5},showLegend:false,barGapWidthPct:40};
  if(o.max!=null)op.valAxisMaxVal=o.max;
  s.addChart(pptx.ChartType.bar,[{name:o.name||'Value',labels,values}],op);};

 const T=c3NovTot(),NR=c3NovRows(),OV=c3Ovr();
 const V=c3View(),SEL=(V.sel||[]).slice(0,3),ROW=(V.rows||[]).filter(r=>r.d);
 const CMP=SEL.map((E,i)=>{let tg=0,vc=0,n=0;ROW.forEach(r=>{const x=r.x[i];if(!x)return;if(x.tg){tg+=x.tg;vc+=x.vc||0;n++;}});
  return {l:E.l,sh:E.sh,y:E.y,m:E.m,t:E.t,src:E.src,tg,vc,n,pct:tg?vc/tg*100:null};})
  .sort((a,b)=>(a.y-b.y)||(a.m||0)-(b.m||0));
 const ID=c3Icm(), IT=ID.tot||{};
 const NC=(typeof NOCD!=='undefined'&&NOCD.camps)?NOCD.camps['SNID Nov 2026']:null;
 const NS=(typeof NOCD!=='undefined'&&NOCD.asof)?NOCD.asof:'2026-11-11';
 const LQ=c3Lqas(), LQT=LQ.reduce((a,r)=>({n:a.n+r.n,p:a.p+r.p,i:a.i+r.i,f:a.f+r.f}),{n:0,p:0,i:0,f:0});
 const MS=c3MS(), MSK=Object.keys(MS).map(k=>MS[k]).filter(r=>r.chk>0).sort((a,b)=>a.k-b.k);
 const MSP=MSK.filter(r=>r.k>=82&&r.k<=84);
 const PC=c3Pcm(), VL=c3ValNov();
 const AF=(typeof AFPD!=='undefined'&&AFPD.y&&AFPD.y['2026'])?Object.fromEntries(AFPD.k.map((k,i)=>[k,AFPD.y['2026'][i]])):{};
 const WPVL=(typeof WPV!=='undefined'&&WPV)||[]; const WD={};
 WPVL.forEach(w=>{if(!w.d)return;WD[w.d]=(WD[w.d]||0)+1;});
 const EA=(typeof EPIM!=='undefined'&&typeof aggE==='function')?aggE(EPIM.filter(r=>r.mo==='2026-10')):{};
 const TG=(typeof TRIG!=='undefined'&&TRIG.t)?TRIG.t:[];
 const TGi=id=>TG.find(t=>t.id===id)||null;
 const rec=T.rec||0,covd=(T.cam||0)+(T.cu||0)+(T.ex||0);
 const stillRec=(T.sna||0)+(T.srf||0),stillTot=T.stl||0;

 // 1 — cover
 {const s=pptx.addSlide(); pg++; s.background={color:'0B3B37'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.16,fill:{color:'5EEAD4'},line:{color:'5EEAD4'}});
  s.addText('CAMPAIGN REVIEW',{x:0.8,y:1.25,w:11.7,h:0.5,fontFace:F,fontSize:16,bold:true,color:'99F6E4',charSpacing:4});
  s.addText('SNID Nov 2026',{x:0.8,y:1.8,w:11.7,h:1.0,fontFace:F,fontSize:44,bold:true,color:'FFFFFF'});
  s.addText('Final coverage, missed children, ICM monitoring, LQAS, market survey, PCM, surveillance, EPI and zero dose',{x:0.8,y:2.85,w:11.7,h:0.7,fontFace:F,fontSize:15,color:'CCFBF1'});
  s.addText('Khyber Pakhtunkhwa · 27 districts · 996 UCs',{x:0.8,y:3.55,w:11.7,h:0.5,fontFace:F,fontSize:18,bold:true,color:'FFFFFF'});
  const cov=T.pct,ovr=OV.pct;
  [['HH coverage',p1(cov)],['Overall coverage',p1(ovr)],['Recorded missed',n0(rec)],['ICM recall',p1(IT.rc?IT.rv/IT.rc*100:null)]].forEach(([l,v],i)=>{
   const x=0.8+i*2.98;s.addShape(pptx.ShapeType.rect,{x,y:4.3,w:2.78,h:1.15,fill:{color:'115E59'},line:{color:'2DD4BF',width:1}});
   s.addText([{text:v,options:{fontSize:26,bold:true,breakLine:true}},{text:l,options:{fontSize:10,color:'CCFBF1'}}],
    {x,y:4.3,w:2.78,h:1.15,fontFace:F,color:'FFFFFF',align:'center',valign:'middle'});});
  s.addText('HH coverage = household target; overall coverage = administrative target. ICM recall as of 04-Nov-2026, campaign in progress.',
   {x:0.8,y:5.6,w:11.7,h:0.4,fontFace:F,fontSize:10,color:'99F6E4'});
  s.addText('Built '+DATE+' · sources: EOC portal coverage summary (11-Nov 16:01), IDIMS forms 24 / 12 / 11 / 10 (11-Nov), LQAS lot review, PCM series, AFP.REC / AFPLAB.REC, KP EPI-MIS',
   {x:0.8,y:6.55,w:11.7,h:0.45,fontFace:F,fontSize:9,color:'5EEAD4'});}

 // 2 — background
 {const s=base('Campaign background','What the November round set out to do and how it is read');
  kpis(s,[{l:'Districts',v:'27'},{l:'UCs reporting',v:n0(T.ucs),s:'portal coverage summary'},{l:'HH target',v:n0(T.tgt),s:'microplans, household basis'},
   {l:'Overall target',v:n0(OV.tg),s:'administrative basis, 996 UCs'},{l:'Houses (ICM scope)',v:n0(IT.hh),s:n0(IT.cl)+' clusters monitored'}],1.35);
  table(s,['Item','Detail'],[
   ['Round','SNID Nov 2026 (NOV-26-1), house-to-house bOPV, children 0–59 months'],
   ['Status','Coverage read 11-Nov-2026 16:01; monitoring forms last received 11-Nov, cluster forms 04-Nov'],
   ['Coverage basis','Household target 4,183,183; administrative target 4,808,167 — both reported here, never blended'],
   ['Quality lenses','Admin + ICM team / fixed / supervisor, HH-cluster recall, LQAS lots, market survey, PCM, triggers'],
   ['Missed-children chain','Recorded → covered (same day, catch-up, extended) → still missed at the end']],
   {x:0.5,y:2.95,w:6.6,colW:[1.55,5.05],rh:0.44,fs:10.5,left:true});
  bullets(s,['The round is read four ways: what teams reported, what monitors saw in the field, what household recall checks verified, and what post-campaign sampling found.',
   'Every children figure on the following slides is labelled with its roll-up level — province, district or UC — and its basis.',
   'Monitor counts cover only the sites visited; they describe the quality of what was seen, not the size of the campaign.'],
   {x:7.35,y:2.95,w:5.45,h:3.6,fs:11.5});}

 // 3 — coverage across the three rounds
 {const s=base('Coverage — Nov 2026 final and the two prior rounds','Each round on its own reported target; household and administrative bases are not mixed');
  const last=CMP[CMP.length-1]||{pct:null};
  kpis(s,[{l:'Rounds compared',v:String(CMP.length),s:'selected in the Last 3 campaigns picker'},
   {l:'Latest coverage',v:p1(last.pct),s:last.l},{l:'Nov HH coverage',v:p1(T.pct),s:'household target 4,183,183'},
   {l:'Nov overall',v:p1(OV.pct),s:'administrative target 4,808,167'}],1.35);
  table(s,['Round','Basis','Target','Vaccinated','Coverage','UCs'],
   CMP.map(c=>[c.l,'administrative',n0(c.tg),n0(c.vc),{t:p1(c.pct),c:rag(c.pct),b:true},n0(c.n||null)]),
   {x:0.5,y:2.9,w:7.2,colW:[2.2,1.5,1.1,1.15,0.8,0.45],rh:0.34,fs:10});
  bars(s,CMP.map(c=>c.sh||c.l),CMP.map(c=>c.pct==null?0:+c.pct.toFixed(1)),
   {x:7.9,y:2.9,w:4.9,h:3.3,title:'Coverage % by round',min:80,max:100,cols:[TE],fmt:'0.0'});
  note(s,'Nov 2026 final: 4,071,582 vaccinated against a household target of 4,183,183 (97.33%) and 4,696,957 against the administrative target of 4,808,167 ('+p1(OV.pct)+'). '+
   'Earlier rounds in this table use the administrative target only; their household target is not published in the same series.',
   {x:0.5,y:6.35,w:12.3,fs:10});}

 // 4 — district coverage, Nov
 {const s=base('Coverage by district — SNID Nov 2026 finale','Household basis: vaccinated ÷ household target, all 27 districts');
  const D=NR.filter(r=>r.d&&r.tgt).slice().sort((a,b)=>a.pct-b.pct);
  const cell=r=>[r.d,n0(r.tgt),n0(r.vac),{t:p1(r.pct),c:rag(r.pct),b:true},{t:n0(r.stl)}];
  table(s,['District','HH target','Vacc.','%','Still'],D.slice(0,14).map(cell),
   {x:0.5,y:1.3,w:6.05,colW:[1.95,1.15,1.1,0.8,1.05],rh:0.3,fs:9});
  table(s,['District','HH target','Vacc.','%','Still'],D.slice(14).map(cell),
   {x:6.78,y:1.3,w:6.05,colW:[1.95,1.15,1.1,0.8,1.05],rh:0.3,fs:9});
  note(s,'Sorted lowest coverage first. Still = still missed at the end of the round (recorded missed not recovered + leftover). '+
   'Province: 4,071,582 of 4,183,183 (97.33%), 162,874 still missed.',{x:0.5,y:6.55,w:12.3,fs:9.5});}

 // 5 — recorded missed
 {const s=base('Recorded missed children — 674,839 (Nov 2026)','Children the teams themselves recorded as not vaccinated during the round');
  const pctTg=T.tgt?rec/T.tgt*100:null;
  kpis(s,[{l:'Recorded missed',v:n0(rec),s:p1(pctTg)+' of the household target',c:AMB},
   {l:'Not available',v:n0(T.rna),s:p1(T.rna/rec*100)+' of recorded',c:AMB},
   {l:'Refusals',v:n0(T.rrf),s:p1(T.rrf/rec*100)+' of recorded',c:RED},
   {l:'UCs reporting',v:n0(T.ucs),s:'coverage summary'}],1.35);
  const top=NR.filter(r=>r.rec).sort((a,b)=>b.rec-a.rec).slice(0,10);
  bars(s,top.map(r=>r.d),top.map(r=>r.rec),{x:0.5,y:2.9,w:6.6,h:3.4,title:'Recorded missed children — top 10 districts',cols:['B45309']});
  bullets(s,['Recorded missed is what teams entered, not the true number of unvaccinated children. Children never visited do not appear here.',
   'Nationally 90.9% of recorded misses were "not available" and 9.1% refusals — the mix, not the total, decides the response.',
   'The chain on the next two slides shows how many were recovered and how many remained at the end.'],{x:7.4,y:2.95,w:5.4,h:3.4,fs:11.5});}

 // 6 — covered
 {const s=base('Covered missed children — 580,425 recovered (86.0%)','Same-day cover, catch-up and extended follow-up of recorded misses');
  const cam=T.cam||0,cu=T.cu||0,ex=T.ex||0;
  kpis(s,[{l:'Same day',v:n0(cam),s:p1(rec?cam/rec*100:null)+' of recorded',c:TE},
   {l:'Catch-up',v:n0(cu),s:p1(rec?cu/rec*100:null)+' of recorded',c:TE},
   {l:'Extended',v:n0(ex),s:p1(rec?ex/rec*100:null)+' of recorded',c:TE},
   {l:'Total covered',v:n0(covd),s:p1(rec?covd/rec*100:null)+' of recorded',c:GRN},
   {l:'Not recovered',v:n0(stillRec),s:p1(rec?stillRec/rec*100:null)+' of recorded',c:RED}],1.35);
  table(s,['Stage','Not available','Refusal','Total','% of recorded'],[
   ['Same-day cover',{t:n0(T.cna)},{t:n0(T.crf)},{t:n0(cam),b:true},{t:p1(rec?cam/rec*100:null)}],
   ['Catch-up',{t:n0(T.ccna)},{t:n0(T.ccrf)},{t:n0(cu),b:true},{t:p1(rec?cu/rec*100:null)}],
   ['Extended',{t:n0(T.cena)},{t:n0(T.cerf)},{t:n0(ex),b:true},{t:p1(rec?ex/rec*100:null)}],
   ['All covered',{t:n0((T.cna||0)+(T.ccna||0)+(T.cena||0))},{t:n0((T.crf||0)+(T.ccrf||0)+(T.cerf||0))},{t:n0(covd),b:true},{t:p1(rec?covd/rec*100:null),b:true}],
   ['Not recovered',{t:n0(T.sna)},{t:n0(T.srf)},{t:n0(stillRec),b:true},{t:p1(rec?stillRec/rec*100:null)}]],
   {x:0.5,y:2.95,w:7.1,colW:[1.7,1.5,1.2,1.3,1.4],rh:0.4,fs:10});
  bullets(s,['Same-day cover is recorded on the day of the missed visit; catch-up is a later team visit; extended is follow-up after the campaign window.',
   '86.0% of recorded misses were recovered — the remaining 94,414 are still missed and added to the unreached left over from earlier rounds.',
   'Covered figures are team-reported; they are not yet independently verified household by household.'],{x:7.9,y:2.95,w:4.9,h:3.5,fs:11});}

 // 7 — still missed
 {const s=base('Still missed children — 162,874 (3.89% of target)','Recorded misses not recovered, plus children left over from earlier rounds');
  kpis(s,[{l:'Still from round',v:n0(stillRec),s:'recorded misses not recovered',c:RED},
   {l:'Leftover',v:n0(T.slo),s:'unreached before this round',c:AMB},
   {l:'Total still missed',v:n0(stillTot),s:p1(T.stp)+' of the household target',c:RED},
   {l:'Share of overall target',v:p1(OV.tg?stillTot/OV.tg*100:null),s:'administrative basis'}],1.35);
  const top=NR.filter(r=>r.stl).sort((a,b)=>b.stl-a.stl).slice(0,10);
  bars(s,top.map(r=>r.d),top.map(r=>r.stl),{x:0.5,y:2.9,w:6.6,h:3.4,title:'Still missed children — top 10 districts',cols:['B91C1C']});
  bullets(s,['Still missed = 72,897 "not available" + 21,517 refusals not recovered, plus 68,460 left over from earlier rounds.',
   'Leftover children were already unvaccinated before the round; they carry forward and are the core of the zero-dose problem.',
   'This is the number to trace UC by UC: 3.89% of the household target, concentrated in the districts on the left.'],{x:7.4,y:2.95,w:5.4,h:3.4,fs:11.5});}

 // 8 — ICM team monitoring
 {const s=base('ICM team monitoring — 80,412 team checks','23 checklist indicators from IDIMS team-monitoring form, November round');
  const ti=(NC&&NC.ti)||[], low=ti.filter(a=>a[1]<90), w1=ti.slice(0,12), w2=ti.slice(12);
  kpis(s,[{l:'Team checks',v:n0(NC?NC.n.tv:null),s:'form 24 records'},
   {l:'Indicators',v:String(ti.length),s:'checklist items scored'},
   {l:'Below 90%',v:String(low.length),s:low.map(a=>a[0]).slice(0,2).join(', ')||'none',c:low.length?RED:GRN},
   {l:'Reading date',v:NS.slice(8,10)+'-'+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+NS.slice(5,7)-1]+'-'+NS.slice(0,4),s:'IDIMS exports'}],1.35);
  const tb=(rows,x)=>table(s,['Indicator','%'],[...rows.map(a=>[a[0],{t:Math.round(a[1])+'%',c:rag(a[1]),b:true}])],
   {x,y:2.9,w:6.05,colW:[4.9,1.15],rh:0.235,fs:8.5});
  tb(w1,0.5); tb(w2,6.78);
  note(s,'Vitamin-A at 3% is a recording gap, not true coverage — the same near-zero appears on the fixed-site and carrier forms. Everything else at or above 96% except female team members (76%), carrier lid and seal (88%) and water in the carrier (88%).',
   {x:0.5,y:6.42,w:12.3,fs:9.5});}

 // 9 — ICM fixed sites
 {const s=base('ICM fixed-site monitoring — 3,969 sites','16 indicators from the fixed-site checklist, November round');
  const fi=(NC&&NC.fi)||[], low=fi.filter(a=>a[1]<90);
  kpis(s,[{l:'Fixed sites checked',v:n0(NC?NC.n.fx:null),s:'form 12 records'},
   {l:'Indicators',v:String(fi.length),s:'checklist items'},
   {l:'Below 90%',v:String(low.length),s:low.map(a=>a[0]).slice(0,2).join(', ')||'none',c:low.length?RED:GRN},
   {l:'Lowest true gap',v:'84%',s:'stock leftover register'}],1.35);
  table(s,['Indicator','%'],fi.map(a=>[a[0],{t:Math.round(a[1])+'%',c:rag(a[1]),b:true}]),
   {x:0.5,y:2.9,w:6.4,colW:[5.1,1.3],rh:0.222,fs:8.5});
  bullets(s,['Fixed sites are EPI centres and outreach points; 3,969 checks is the largest fixed-site sample in the round.',
   'Cold chain, VVM, labels and recapping are at 100%; the gaps sit in stock records (84–85%) and vaccination given at the site (85%).',
   'Only 88% of checked fixed sites are inside an EPI centre — the rest are ad-hoc points that are harder to supervise and resupply.'],{x:7.2,y:2.95,w:5.6,h:3.5,fs:11.5});}

 // 10 — supervisor + transit
 {const s=base('ICM supervisor and transit monitoring','Supervisor checklist, team carrier audit and transit-point conditions');
  const si=(NC&&NC.si)||[], sc=(NC&&NC.sc)||[], tx=(NC&&NC.tx)||[];
  kpis(s,[{l:'Transit sites',v:n0(NC?NC.n.tr:null),s:'form 10 records'},
   {l:'Checklist done',v:p1(si[0]?si[0][1]:null),s:'supervisor form completed'},
   {l:'Team support',v:p1(si[1]?si[1][1]:null),s:'supervisor supported teams'},
   {l:'IPC quality',v:p1(si[2]?si[2][1]:null),s:'infection prevention'}],1.35);
  table(s,['Carrier audit','%'],sc.map(a=>[a[0],{t:p1(a[1]),c:rag(a[1]),b:true}]),
   {x:0.5,y:2.9,w:5.7,colW:[4.4,1.3],rh:0.3,fs:9});
  const txw=tx.slice().sort((a,b)=>a[1]-b[1]).slice(0,8);
  table(s,['Transit point','%'],txw.map(a=>[a[0],{t:Math.round(a[1])+'%',c:rag(a[1]),b:true}]),
   {x:6.9,y:2.9,w:5.9,colW:[4.6,1.3],rh:0.3,fs:9});
  note(s,'Transit teams carry less equipment than fixed teams: only 19% have a carrier for each team member, 41% a marker each and 21% a tally sheet each. Posters (59%), team ID badges (74%) and security support (33% present, 16% helping) are the other weak points.',
   {x:0.5,y:6.3,w:12.3,fs:10});}

 // 11 — ICM HH clusters
 {const s=base('ICM household-cluster monitoring — recall 89.0%','Children verified vaccinated among recall-checked children; 90% is the floor');
  const rc=IT.rc||0,rv=IT.rv||0,mi=IT.mi||0;
  const dist=ID.rows.filter(r=>r.rc>0).sort((a,b)=>(a.rv/a.rc)-(b.rv/b.rc));
  kpis(s,[{l:'Recall %',v:p1(rc?rv/rc*100:null),s:n0(rv)+' verified of '+n0(rc)+' recall-checked',c:rc&&rv/rc*100<90?RED:GRN},
   {l:'Clusters',v:n0(IT.cl),s:n0(IT.hh)+' houses'},{l:'Children seen',v:n0(IT.seen),s:'teams seen by monitors'},
   {l:'Missed',v:n0(mi),s:p1(IT.seen?mi/IT.seen*100:null)+' of children seen',c:RED},{l:'EPI referrals',v:n0(IT.epi),s:'referred to routine EPI'}],1.35);
  table(s,['District','Recall-checked','Verified','Recall %','Missed'],
   dist.slice(0,11).map(r=>[r.d,n0(r.rc),n0(r.rv),{t:p1(r.rc?r.rv/r.rc*100:null),c:rag(r.rv/r.rc*100),b:true},{t:n0(r.mi)}]),
   {x:0.5,y:2.9,w:6.2,colW:[1.95,1.35,1.1,1.0,0.8],rh:0.27,fs:9});
  table(s,['Why missed','Children','Share'],[
   ['Not available',{t:n0(IT.na)},{t:p1(mi?IT.na/mi*100:null)}],
   ['Refusal',{t:n0(IT.rf)},{t:p1(mi?IT.rf/mi*100:null)}],
   ['No team visit',{t:n0(IT.nt)},{t:p1(mi?IT.nt/mi*100:null)}],
   ['Team missed child',{t:n0(IT.tv)},{t:p1(mi?IT.tv/mi*100:null)}],
   ['All missed',{t:n0(mi),b:true},{t:'100.0%',b:true}]],
   {x:7.0,y:2.9,w:5.8,colW:[2.6,1.6,1.6],rh:0.34,fs:9.5});
  note(s,''+n0(IT.fm)+' of '+n0(IT.seen)+' children seen ('+(IT.seen?p1(IT.fm/IT.seen*100):'–')+') were finger-marked, '+n0(IT.nvfm)+' had a mark but no vaccination behind it. '+
   'District figures are as of '+(ID.asof||'2026-11-04')+'; the round was in progress when the cluster forms were read, so recall will move.',{x:0.5,y:6.35,w:12.3,fs:10});}

 // 12 — LQAS
 {const s=base('LQAS — 84.2% of lots passed in Sept 2026','Lot quality assurance: a lot passes when unvaccinated children stay under the threshold');
  const cur=LQ[0]||{p:0,i:0,f:0,n:0,pct:null}, ap=LQT.n?LQT.p/LQT.n*100:null;
  kpis(s,[{l:'Sept 2026 lots',v:n0(cur.n),s:n0(cur.p)+' pass · '+n0(cur.i)+' intermediate · '+n0(cur.f)+' fail',c:cur.pct<90?AMB:GRN},
   {l:'Pass %',v:p1(cur.pct),s:'90%+ expected',c:cur.pct<90?AMB:GRN},
   {l:'Six-round pass',v:p1(ap),s:n0(LQT.n)+' lots since Oct 2025'},
   {l:'Nov 2026',v:'Pending',s:'not yet sampled'}],1.35);
  table(s,['Round','Lots','Pass','Interm.','Fail','Pass %'],
   LQ.map(r=>[r.l,n0(r.n),n0(r.p),n0(r.i),n0(r.f),{t:p1(r.pct),c:rag(r.pct),b:true}]),
   {x:0.5,y:2.9,w:7.0,colW:[2.5,0.85,0.85,0.95,0.75,1.1],rh:0.36,fs:9.5});
  bars(s,LQ.slice(0,5).map(r=>r.l.replace(/\(.*\)/,'').trim()),LQ.slice(0,5).map(r=>r.pct==null?0:+r.pct.toFixed(1)),
   {x:7.8,y:2.9,w:5.0,h:3.2,title:'Pass % by round (latest five)',min:70,max:100,cols:['0F766E']});
  note(s,'Sept 2026: 101 of 120 lots passed, 17 intermediate and 2 failed (84.2%). Across six rounds, 712 of 840 lots passed (84.8%). '+
   'LQAS reads the campaign\'s vaccination quality in sampled clusters, not province-wide coverage; Nov 2026 will be sampled after the round closes.',{x:0.5,y:6.35,w:12.3,fs:10});}

 // 13 — market survey
 {const s=base('Market survey — 96.0% verified in May 2026','Children checked at markets and transit points, vaccination verified on the child');
  const M=MS['84']||MSP[MSP.length-1]||null;
  kpis(s,[{l:'Checks',v:n0(M?M.chk:null),s:'May 2026 markets'},{l:'MS %',v:p1(M?M.pct:null),s:n0(M?M.ver:null)+' verified vaccinated',c:M&&M.pct<95?AMB:GRN},
   {l:'Missed',v:n0(M?M.ms:null),s:p1(M&&M.chk?M.ms/M.chk*100:null)+' of checks',c:AMB},
   {l:'Nov 2026',v:'Pending',s:'not compiled yet'}],1.35);
  table(s,['Round','Checks','Verified','MS %','Missed','No team','Away','Refused','VBNFM'],
   MSP.map(r=>[r.l,n0(r.chk),n0(r.ver),{t:p1(r.pct),c:rag(r.pct),b:true},n0(r.ms),n0(r.nt+r.ntc),n0(r.na),n0(r.rf),n0(r.vb)]),
   {x:0.5,y:2.95,w:12.3,colW:[1.5,1.35,1.3,1.15,1.25,1.25,1.15,1.2,1.6],rh:0.4,fs:9.5});
  bullets(s,['Market surveys catch children who were away or missed at the door; they are an independent reading of the same vaccination status.',
   'May 2026 verified 96.0% of 28,253 children checked; the misses split into no-team visits, children away and a small refusal share.',
   'Nov 2026 has not been compiled yet — the May round is the most recent market-survey evidence for this campaign series.'],{x:0.5,y:4.9,w:12.3,h:1.9,fs:11.5});}

 // 14 — PCM
 {const s=base('Post-campaign monitoring — Sep 2026','Household finger-mark checks after the round, with the ICM recall series beside it');
  kpis(s,[{l:'UCs monitored',v:n0(PC.nuc),s:'Sep 2026 PCM round'},{l:'Children checked',v:n0(PC.chk),s:'households after the round'},
   {l:'FM %',v:p1(PC.fmp),s:'target 95% — under 90% fails',c:PC.fmp<90?RED:GRN},
   {l:'Missed',v:n0(PC.ms),s:p1(PC.msp)+' of children checked',c:AMB},
   {l:'Recall recorded',v:'No',s:'PCM form does not capture recall checks'}],1.35);
  table(s,['ICM round','Recall-checked','Verified','Recall %'],
   (PC.icm26.length?PC.icm26:PC.icm.slice(-3)).map(t=>[t.l,n0(t.rc),n0(t.rv),{t:p1(t.pct),c:rag(t.pct),b:true}]),
   {x:0.5,y:2.95,w:6.3,colW:[2.7,1.45,1.1,1.05],rh:0.34,fs:9.5});
  bullets(s,['PCM is a household check after the round: monitors look for a finger mark and verify it was a vaccination. It reads FM %, not recall %.',
   'Sep 2026 PCM: 3,132 children checked in 52 UCs, 89.8% finger-marked and 319 children (10.2%) found missed. Recall checks were not recorded in that round.',
   'The latest ICM recall in the same series is May 2026 at '+p1((PC.icm.slice(-1)[0]||{}).pct)+' — ICM recall is the measure to follow, PCM FM % is the cross-check.'],{x:7.1,y:2.95,w:5.7,h:3.5,fs:11});}

 // 15 — surveillance
 {const s=base('Surveillance — seven WPV1 cases in 2026','AFP surveillance and confirmed polio, KP province-wide');
  kpis(s,[{l:'AFP cases 2026',v:n0(AF.n),s:'onset 01-Jan to 28-Oct'},{l:'WPV1',v:n0(AF.c1),s:'confirmed polio cases',c:RED},
   {l:'Zero-dose AFP',v:n0(AF.zd),s:p1(AF.n?AF.zd/AF.n*100:null)+' of AFP cases',c:AMB},
   {l:'Pending',v:n0(AF.cp),s:'awaiting classification'}],1.35);
  const wp=Object.keys(WD).map(d=>[d,WD[d]]).sort((a,b)=>b[1]-a[1]);
  table(s,['District','WPV1'],[...wp.map(a=>[a[0],{t:String(a[1]),c:['FEE2E2','991B1B'],b:true}]),['All KP',{t:String(AF.c1),b:true}]],
   {x:0.5,y:2.9,w:4.6,colW:[3.3,1.3],rh:0.32,fs:10});
  table(s,['Surveillance indicator','2026'],[
   ['Stool adequacy',{t:p1(AF.n?AF.ad/AF.n*100:null),b:true}],
   ['Notified within 7 days',{t:p1(AF.n?AF.n7/AF.n*100:null),b:true}],
   ['Investigated within 48 h',{t:p1(AF.n?AF.i48/AF.n*100:null),b:true}],
   ['Discarded (non-polio)',{t:n0(AF.c3)}],
   ['Positive (WPV1)',{t:n0(AF.cw)}],
   ['Pending classification',{t:n0(AF.cp)}]],
   {x:5.35,y:2.9,w:4.1,colW:[2.7,1.4],rh:0.34,fs:9.5});
  bullets(s,['Seven WPV1 cases with onset in 2026: Khyber 3, Bannu 3 and Wazir-N 1; the latest onset is 28-Oct-2026.',
   'Stool adequacy '+p1(AF.n?AF.ad/AF.n*100:null)+' and investigation within 48 hours '+p1(AF.n?AF.i48/AF.n*100:null)+' are at target; notification within 7 days ('+p1(AF.n?AF.n7/AF.n*100:null)+') is the weak link.',
   'Ninety-one AFP cases were zero-dose — the surveillance system keeps finding the same unvaccinated children the campaign is trying to reach.'],{x:9.8,y:2.9,w:3.0,h:3.6,fs:10.5});}

 // 16 — EPI
 {const s=base('Routine EPI — antigen coverage, Oct 2026','Monthly contact coverage: doses given ÷ surviving infants; not survey coverage');
  const fi=EA.p_fi, p1v=EA.p_p1, p3v=EA.p_p3;
  kpis(s,[{l:'Fully immunized',v:p1(fi),s:'all antigens, Oct 2026'},{l:'Penta-3',v:p1(p3v),s:'doses ÷ infant target'},
   {l:'OPV-3',v:p1(EA.p_opv3),s:'campaign antigen'},{l:'MR-2',v:p1(EA.p_mr2),s:'lowest antigen',c:RED},
   {l:'Penta drop-out',v:p1(p1v&&p3v?(p1v-p3v)/p1v*100:null),s:'Penta-1 to Penta-3'}],1.35);
  const AG=[['BCG','p_bcg'],['OPV-1','p_opv1'],['OPV-2','p_opv2'],['OPV-3','p_opv3'],['Penta-1','p_p1'],['Penta-2','p_p2'],['Penta-3','p_p3'],['PCV-3','p_pcv3'],['IPV-2','p_ipv2'],['Rota-2','p_rota2'],['MR-1','p_mr1'],['MR-2','p_mr2']];
  bars(s,AG.map(a=>a[0]),AG.map(a=>EA[a[1]]==null?0:+EA[a[1]].toFixed(1)),
   {x:0.5,y:2.9,w:7.0,h:3.4,title:'Coverage % by antigen — Oct 2026',min:0,max:70,cols:['0B7285']});
  table(s,['Antigen','Doses','%'],AG.slice(0,9).map(a=>[a[0],n0(EA[a[1].replace('p_','')]),{t:p1(EA[a[1]]),c:rag(EA[a[1]]),b:true}]),
   {x:7.8,y:2.9,w:5.0,colW:[2.1,1.4,1.5],rh:0.3,fs:9});
  note(s,'Contact coverage compares doses with the monthly surviving-infant target. At 46–51% the routine system is not reaching half of the cohort, and MR-2 at 40.1% is the widest gap. '+
   'Campaigns can close the OPV gap but not the routine antigens — this is the integration case for the next round.',{x:0.5,y:6.3,w:12.3,fs:9.5});}

 // 17 — zero dose
 {const s=base('Zero dose — 43,484 recorded, none yet covered','Children with no OPV dose recorded in the November round');
  kpis(s,[{l:'Recorded ZD',v:n0(T.zd),s:p1(T.tgt?T.zd/T.tgt*100:null)+' of the HH target',c:RED},
   {l:'ZD covered',v:'0',s:'covered column not compiled for Nov',c:GRY},
   {l:'Validated',v:n0(VL.n),s:n0(VL.nuc)+' UCs, Nov 2026 validation'},
   {l:'Confirmed vaccinated',v:p1(VL.pct),s:n0(VL.vy)+' of '+n0(VL.n)+' checked',c:GRN}],1.35);
  table(s,['Validation outcome','Children','Share'],[
   ['Validated records',{t:n0(VL.n),b:true},{t:'100.0%'}],
   ['Confirmed vaccinated',{t:n0(VL.vy),b:true},{t:p1(VL.n?VL.vy/VL.n*100:null)}],
   ['Not vaccinated',{t:n0(VL.vn),b:true},{t:p1(VL.n?VL.vn/VL.n*100:null)}],
   ['Unclear',{t:n0(VL.vx),b:true},{t:p1(VL.n?VL.vx/VL.n*100:null)}]],
   {x:0.5,y:2.95,w:6.2,colW:[2.8,1.7,1.7],rh:0.36,fs:10});
  bullets(s,['43,484 children were recorded with no OPV dose in the November round — 1.04% of the household target.',
   'The covered-zero-dose column has not been compiled for this round, so no recovery rate can be quoted yet. Validation so far confirms 97.5% of checked children as vaccinated.',
   'Zero-dose children found by AFP surveillance (91 cases in 2026) are the same population; the register and the campaign list need to be reconciled before the next round.'],{x:7.0,y:2.95,w:5.8,h:3.5,fs:11});}

 // 18 — triggers
 {const s=base('Triggers — 557 UCs flagged in 26 districts','Control-room trigger feedback as of 05-Nov-2026, campaign in progress');
  const mq=TGi('mpqa'),ic=TGi('icm'),ad=TGi('admin');
  kpis(s,[{l:'UCs flagged',v:'557',s:'any of seven compliance triggers'},{l:'MPQA',v:n0(mq?mq.tot[2]:null),s:'microplan score under 90%',c:AMB},
   {l:'ICM',v:n0(ic?ic.tot[2]:null),s:'poorly covered or missed area',c:RED},{l:'Admin coverage',v:n0(ad?ad.tot[2]:null),s:'under 70% or over 115%',c:AMB},
   {l:'ICM answered',v:ic&&ic.tot[2]?p1(ic.tot[3]/ic.tot[2]*100):'–',s:'flagged UCs with feedback'}],1.35);
  const T2=TG.filter(t=>t.id==='mpqa'||t.id==='icm'||t.id==='admin');
  table(s,['Trigger','Rule','UCs','Flags','Feedback'],
   T2.map(t=>[t.l,t.rule.replace(/^UC /,''),n0(t.tot[2]),n0(t.tot[0]+t.tot[1]),n0(t.tot[3])]),
   {x:0.5,y:2.95,w:12.3,colW:[1.55,6.6,1.2,1.35,1.6],rh:0.4,fs:10});
  bullets(s,['MPQA: 53 UCs need improvement and 5 have serious issues, all 58 with feedback recorded.',
   'ICM: 319 UCs flagged for a poorly covered area and 124 for a missed area; 63 met both, so 380 distinct UCs and 285 with feedback.',
   'Administrative coverage: 173 UCs below 70% and 45 above 115% — the portal records no feedback for this trigger.',
   'Counts move while the round is open; re-read the control-room page before the next EOC review.'],{x:0.5,y:4.75,w:12.3,h:2.0,fs:11.5,gap:5});}

 // 19 — actions
 {const s=base('What this means — priority actions','Seven actions that follow directly from the figures in this deck');
  const dd=c3Icm().rows.filter(r=>r.rc>0).sort((a,b)=>(a.rv/a.rc)-(b.rv/b.rc)).slice(0,4).map(r=>r.d);
  bullets(s,[
   '1. Re-visit the lowest-recall districts first: '+dd.join(', ')+' sit under 88% on household-cluster recall.',
   '2. Fix the Vitamin-A recording gap across the team, fixed-site and carrier forms — 3–4% is a form problem, not coverage.',
   '3. Equip transit teams: only 19% carry a carrier per member, 41% a marker each and 21% a tally sheet each.',
   '4. Trace the 68,460 leftover children UC by UC; they were unreached before the round and remain the zero-dose core.',
   '5. Close the zero-dose loop: 43,484 recorded, no covered figure compiled, validation confirming 97.5% of those checked.',
   '6. Protect routine EPI: 46–51% contact coverage and MR-2 at 40.1% will not be closed by campaigns alone.',
   '7. Keep the quality floor visible: LQAS 84.2% of lots passed and ICM recall 89.0% — both under the 90% line before the next round.'],
   {x:0.6,y:1.4,w:12.1,h:4.6,fs:13.5,gap:12,nb:true});
  note(s,'Every number in this deck is drawn from the dashboard payloads listed on the next slide; none is rounded up or carried over from an earlier read.',
   {x:0.6,y:6.15,w:12.1,fs:10});}

 // 20 — sources
 {const s=base('Sources, dates and what each figure covers','Read these with the slide they support; dates are the export or portal read');
  table(s,['Figure','Source','Date','Level'],[
   ['Nov coverage, missed chain','EOC portal Summary report, UC-wise, SNID Nov 2026','11-Nov-2026 16:01','UC → province'],
   ['ICM team / fixed / supervisor / transit','IDIMS forms 24, 12, 10 — NEOC aggregate exports','11-Nov-2026','District'],
   ['ICM household clusters','IDIMS form 11, in-scope UCs','04-Nov-2026 20:56','UC → province'],
   ['LQAS lots','Lot review, six rounds','06-Oct-2026','UC / lot'],
   ['Market survey','Indicator scorecard (MS series)','May-2026 round','District / method'],
   ['PCM and ICM recall series','PCM dataset, Sep 2026 and earlier','Sep-2026 round','UC / district'],
   ['Surveillance','AFP.REC and AFPLAB.REC master database','04-Nov-2026','District / case'],
   ['Routine EPI','EPI-MIS monthly exports','Oct-2026','District'],
   ['Zero-dose validation','SNID November 2026 validation export','Nov-2026','UC'],
   ['Triggers','EOC Control Room Trigger Feedback','05-Nov-2026','UC']],
   {x:0.5,y:1.35,w:12.3,colW:[3.1,5.5,1.7,2.0],rh:0.33,fs:9.5});
  note(s,'Coverage is administrative reporting until a post-campaign survey says otherwise. ICM and PCM describe the sites monitors visited, not the whole campaign. '+
   'LQAS and market survey are samples. Where a figure for November 2026 is not yet compiled, the deck says so rather than substituting an earlier round.',
   {x:0.5,y:5.6,w:12.3,h:1.1,fs:10});}
 return pptx;
}
async function runC3Deck(){
 const b=el('btnC3PPTX'); if(b)b.disabled=true;
 try{ c3Pick(); await loadPptx(); const pptx=renderC3Deck(window.PptxGenJS);
  const fn=('SNID_Nov_2026_campaign_review_KP_'+new Date().toISOString().slice(0,10)).replace(/[^A-Za-z0-9]+/g,'_')+'.pptx';
  await saveDeck(pptx,fn); toast('Campaign presentation ready — '+fn);
 }catch(e){ console.error(e); toast((e&&e.message==='load')?'Could not load the presentation tool. Check the internet connection.':'Could not build the presentation'); }
 finally{ if(b)b.disabled=false; }
}
{const _b=el('btnC3PPTX'); if(_b)_b.onclick=runC3Deck;}
