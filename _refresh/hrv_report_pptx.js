// HRA AT A GLANCE (7/7): the findings report as a PowerPoint deck.
// The owner asked, 27-Oct-2026: "The report should be in PPTX." This module builds a seven-slide
// deck through PptxGenJS, which the dashboard already loads and uses for the SITREP, focus, PTP and
// MSRM decks (loadPptx/saveDeck). No figure is new here: the findings and recommendations are the
// ones hrvRep() wrote into _HRVRT, and the summary slide re-reads hrvRepData(), the same evaluation
// the report and the charts above use. The text download stays behind it as the offline fallback.
//
// hrvRep() wires the button only while it has no handler, so binding hrvRepPptx here - before the
// first render - leaves the card's own handler in place and adds no second click path.
function hrvRepParts(){
 const t=_HRVRT||'';if(!t)return null;
 const lines=t.split('\n');
 const per=(lines[0]||'').replace(/^HRA UC-LEVEL FINDINGS - /,'').trim();
 const scope=(lines[1]||'').replace(/^Scope:\s*/,'').trim();
 const dm=/^Generated (.*?) from the sheet/.exec(lines[2]||'');
 const iF=lines.indexOf('FINDINGS'),iR=lines.indexOf('RECOMMENDATIONS');
 if(iF<0||iR<0)return null;
 const F=[];
 lines.slice(iF+1,iR).forEach(function(l){
  const m=/^\d+\.\s+(.+?)\.\s+([\s\S]*)$/.exec(l.trim());
  if(m)F.push({h:m[1]+'.',t:m[2]});
  else if(l.trim()&&F.length)F[F.length-1].t+=' '+l.trim();
 });
 const R=lines.slice(iR+1).filter(function(l){return /^\d+\.\s/.test(l.trim());})
  .map(function(l){return l.trim().replace(/^\d+\.\s+/,'');});
 const nt=lines.filter(function(l){return /^Note: /.test(l);})[0]||'';
 // The risk-mix sentence carries a parenthetical about the dashboard's KPI row; on a slide the row
 // is not there, so the comparison is dropped and the KPI on the summary slide stands on its own.
 F.forEach(function(f){f.t=f.t.replace(/\s*\(the KPI row above[^)]*\)/,'');});
 return {per:per,scope:scope,date:dm?dm[1]:'',F:F,R:R,note:nt};
}

function hrvRepDeck(P){
 const X=hrvRepParts();if(!X)return null;
 const D=hrvRepData(hrtVals()),B=D.band,tot=D.comp.length;
 const F='Segoe UI',NV='0E7490',RED='B91C1C',AMB='B45309',GRN='15803D',GRY='6B7280',TXT='1F2937';
 const bl=[1,2,3,4].map(function(b){return D.blocks[b];}).filter(Boolean)
  .sort(function(a,b){return a.ach-b.ach;});
 const pptx=new P();pptx.layout='LAYOUT_WIDE';
 pptx.title='HRA findings and recommendations - '+X.per;
 pptx.company='KP Polio and Synergy Dashboard';
 let pg=0;
 const base=function(t,sub){
  const s=pptx.addSlide();pg++;s.background={color:'FFFFFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.13,fill:{color:NV},line:{color:NV}});
  s.addText(t,{x:0.5,y:0.3,w:12.33,h:0.55,fontFace:F,fontSize:23,bold:true,color:NV});
  if(sub)s.addText(sub,{x:0.5,y:0.86,w:12.33,h:0.34,fontFace:F,fontSize:11,color:GRY});
  s.addShape(pptx.ShapeType.line,{x:0.5,y:6.98,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
  s.addText('HRA findings \u00b7 '+X.scope,{x:0.5,y:7.02,w:10.7,h:0.3,fontFace:F,fontSize:9,color:GRY});
  s.addText(String(pg),{x:12.23,y:7.02,w:0.6,h:0.3,fontFace:F,fontSize:9,color:GRY,align:'right'});
  return s;};
 const kpis=function(s,it,y){
  const n=it.length,gp=0.2,w=(12.33-gp*(n-1))/n;
  it.forEach(function(o,i){
   const x=0.5+i*(w+gp),c=o.c||NV;
   s.addShape(pptx.ShapeType.rect,{x:x,y:y,w:w,h:1.28,fill:{color:'F9FAFB'},line:{color:'E5E7EB',width:0.75}});
   s.addShape(pptx.ShapeType.rect,{x:x,y:y,w:w,h:0.07,fill:{color:c},line:{color:c}});
   s.addText(o.l.toUpperCase(),{x:x+0.15,y:y+0.16,w:w-0.3,h:0.3,fontFace:F,fontSize:9,bold:true,color:GRY});
   s.addText(o.v,{x:x+0.15,y:y+0.45,w:w-0.3,h:0.46,fontFace:F,fontSize:21,bold:true,color:o.vc||TXT});
   if(o.s)s.addText(o.s,{x:x+0.15,y:y+0.93,w:w-0.3,h:0.3,fontFace:F,fontSize:9,color:GRY});});};
 {const s=pptx.addSlide();pg++;s.background={color:NV};
  s.addText('HRA COMPILATION \u00b7 '+X.per.toUpperCase(),{x:0.8,y:1.0,w:11.7,h:0.4,fontFace:F,
   fontSize:15,bold:true,color:'A5F3FC',charSpacing:3});
  s.addText('Findings and recommendations',{x:0.8,y:1.5,w:11.7,h:1.0,fontFace:F,fontSize:40,
   bold:true,color:'FFFFFF'});
  s.addText('What the '+fmt(D.n)+' compiled councils in scope say, and what to do before the next round',
   {x:0.8,y:2.5,w:11.7,h:0.6,fontFace:F,fontSize:16,color:'CFFAFE'});
  s.addShape(pptx.ShapeType.rect,{x:0.8,y:3.3,w:2.2,h:0.06,fill:{color:'67E8F9'},line:{color:'67E8F9'}});
  s.addText([{text:'Scope  ',options:{bold:true,color:'A5F3FC'}},{text:X.scope,options:{color:'FFFFFF'}}],
   {x:0.8,y:3.55,w:11.7,h:0.4,fontFace:F,fontSize:13});
  s.addText([{text:'Compiled  ',options:{bold:true,color:'A5F3FC'}},
   {text:(X.date||'today')+' from the sheet held in this browser',options:{color:'FFFFFF'}}],
   {x:0.8,y:4.0,w:11.7,h:0.4,fontFace:F,fontSize:13});
  s.addText('Every figure is a roll-up of the cells on this sheet. A high percentage is a safe council \u2014 '
   +'the card\u2019s own axis, not the combined UC risk score used on the Cross-cutting pages.',
   {x:0.8,y:5.0,w:11.7,h:0.8,fontFace:F,fontSize:11,color:'A5F3FC',valign:'top'});}
 {const s=base('At a glance','The compiled card as it stands, and the two roll-ups behind the findings');
  kpis(s,[
   {l:'Councils in scope',v:fmt(D.n),s:D.dv||D.dd?'filtered':'all divisions'},
   {l:'Answer all '+HRAT.nsc,v:fmt(D.full),c:GRN,s:D.n?pc(D.full/D.n*100)+' of scope':''},
   {l:'Comparable on the axis',v:fmt(tot),c:tot<D.marked?AMB:GRN,s:fmt(D.over+D.other)+' marked left out'},
   {l:'High Risk',v:String(B[2]),c:RED,s:tot?pc(B[2]/tot*100)+' of comparable':'none comparable'},
   {l:'Mean score',v:pc(D.mean),c:NV,s:'card\u2019s own total'}
  ],1.3);
  s.addChart(pptx.ChartType.bar,[{name:'Councils',labels:['Low Risk','Medium Risk','High Risk'],
   values:[B[0],B[1],B[2]]}],
   {x:0.5,y:2.95,w:5.7,h:3.7,barDir:'col',chartColors:[NV],showValue:true,dataLabelFontSize:12,
    dataLabelColor:TXT,dataLabelPosition:'outEnd',catAxisLabelFontSize:11,catAxisLabelColor:TXT,
    valAxisLabelFontSize:9,valAxisLabelColor:GRY,valGridLine:{color:'E5E7EB',size:0.5},
    showLegend:false,valAxisMinVal:0,showTitle:false});
  if(bl.length)s.addChart(pptx.ChartType.bar,[{name:'Marks earned',
   labels:bl.map(function(b){return b.name;}),values:bl.map(function(b){return Math.round(b.ach*10)/10;})}],
   {x:6.55,y:2.95,w:6.3,h:3.7,barDir:'bar',chartColors:[NV],showValue:true,
    dataLabelFormatCode:'0.0"%"',dataLabelFontSize:10,dataLabelColor:TXT,dataLabelPosition:'outEnd',
    catAxisLabelFontSize:10,catAxisLabelColor:TXT,catAxisOrientation:'maxMin',
    valAxisLabelFontSize:9,valAxisLabelColor:GRY,valAxisMaxVal:100,
    valGridLine:{color:'E5E7EB',size:0.5},showLegend:false,showTitle:false});}
 {const per=2;
  for(let i=0;i<X.F.length;i+=per){
   const grp=X.F.slice(i,i+per);
   const s=base('Findings',grp.length>1?'Built from the cells compiled above, and the filter on the card':
    'The last finding on this sheet');
   grp.forEach(function(f,j){
    const y=1.3+j*2.72;
    s.addShape(pptx.ShapeType.rect,{x:0.5,y:y,w:0.06,h:2.45,fill:{color:NV},line:{color:NV}});
    s.addText(f.h,{x:0.75,y:y,w:11.9,h:0.4,fontFace:F,fontSize:15,bold:true,color:NV});
    s.addText(f.t,{x:0.75,y:y+0.42,w:11.9,h:2.0,fontFace:F,fontSize:11.5,color:TXT,valign:'top'});
   });
  }}
 {const s=base('Recommendations','In the order they matter for this sheet');
  s.addText(X.R.map(function(t,i){return {text:(i+1)+'.  '+t,options:{breakLine:true}};}),
   {x:0.7,y:1.45,w:11.95,h:4.5,fontFace:F,fontSize:13.5,color:TXT,valign:'top',paraSpaceAfter:13});
  if(X.note)s.addText(X.note,{x:0.7,y:6.05,w:11.95,h:0.7,fontFace:F,fontSize:10,color:GRY,
   italic:true,valign:'top'});}
 return pptx;
}

async function hrvRepPptx(){
 if(!_HRVRT){toast('There is nothing to download yet');return;}
 const btn=el('btnHRVrep'),old=btn?btn.textContent:'';
 if(btn){btn.disabled=true;btn.textContent='Preparing the deck\u2026';}
 try{
  await loadPptx();
  const pptx=hrvRepDeck(window.PptxGenJS);
  if(!pptx)throw new Error('no report');
  await saveDeck(pptx,'HRA_findings_'+hrtSlug()+'.pptx');
  toast('Report downloaded as a PowerPoint deck');
 }catch(e){
  console.error(e);
  toast('Could not build the deck \u2014 downloading the text report instead');
  hrvRepTxt();
 }finally{
  if(btn){btn.disabled=false;btn.textContent=old||'Download the report (.pptx)';}
 }}

(function(){
 const b=document.getElementById('btnHRVrep');
 if(b)b.onclick=hrvRepPptx;
})();
// END OF PART
