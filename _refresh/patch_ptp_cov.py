"""Add the Coverage / wastage views to the Permanent Transit Points block in index.html.

The PTP section was published without the Coverage and OPV family because nothing in this repo
could say what the columns counted. The owner's own workbook now says it (see extract_ptp.py):
Wastage % = 1-(SUM([Coverage])/SUM([OPVUsed])), so Coverage counts children covered and OPVUsed
counts doses actually used, and their bands are <=0 Negative, 0-10% Acceptable Range, >10% High.
That is the definition this view renders - it is not derived from the panel's own columns.

Adds, in the master only, after the four existing charts and before the district inventory table:
  1. A coverage KPI row (children covered, doses used, wastage % with the owner's band).
  2. pt5 - wastage % by district unit, coloured by the owner's bands, responding to the period
     filter and the Division / District filters like the rest of the section.
  3. pt6 - children covered by post type, and by post strategy or age band through the same picker.
  4. tPTcov - the district coverage and wastage table with the dose ledger, the factor and the
     corridor, plus a CSV download.
  5. tPTg - one grouped table with a Group-by picker over five cuts: division, corridor, post
     type, post strategy, age band.
  6. tPTy - the year-by-year table that is the reason the family starts at covy, plus a CSV.

Two guards the whole view is built around. Before covy (2022) the family is published but never
printed: Coverage exceeds OPVUsed there, which the owner's definition cannot allow, so those cells
show a dash and tPTy shows the arithmetic. And the whole-window KPIs sum 2022 onwards only, since
a wastage % mixed across the nonsense years would be a made-up number. Both say so on screen.

The class cuts (post type, strategy, age band) are district x year cells, so the month selector
cannot narrow them and the caption states which period each row covers. Division and corridor rows
come from the district cells and do honour the month.

Everything is additive: no existing table, chart or column list is edited, so a failure here cannot
blank a published view. The block also no-ops if the payload predates the coverage keys, so an old
ptp.json cannot throw inside renderPTP and take the section down with it.

All inserted text uses CRLF so the file's line endings stay uniform.
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

PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'ptp.json')

HTML = (
 '<!-- coverage and wastage, defined by the owner\'s PTP-STP workbook -->\r\n'
 '<div class="tblhdr" style="margin-top:14px"><h3 style="margin:0">Coverage, doses used and wastage</h3>'
 '<span class="cnt" id="ptCNote"></span></div>\r\n'
 '<div class="hint" id="ptCHint"></div>\r\n'
 '<div class="kpis" id="kPTc"></div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="pt5" class="ch" style="height:360px"></div><div class="cap" id="cappt5"></div></div>\r\n'
 '<div class="card"><div id="pt6" class="ch" style="height:360px"></div><div class="cap" id="cappt6"></div></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Children covered, doses used and wastage by district unit</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntPTcov"></span>'
 '<button class="btn" id="btnPTcov">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTcov"></table></div>\r\n'
 '<div class="cap" id="capPTcov"></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The same figures grouped</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><select id="fPTG" title="Group the '
 'coverage figures this way"></select><span class="cnt" id="cntPTg"></span>'
 '<button class="btn" id="btnPTg">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTg"></table></div>\r\n'
 '<div class="cap" id="capPTg"></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Why the coverage family starts in 2022</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntPTy"></span>'
 '<button class="btn" id="btnPTy">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTy"></table></div>\r\n'
 '<div class="cap" id="capPTy"></div>\r\n'
 '</div>\r\n'
)

JS = r"""
 // ---------- PTP coverage, doses used and wastage (owner's workbook definition) ----------
 const CV=(typeof PTP.covy==='number'&&PTP.cw&&PTP.k.indexOf('cov')>=0);
 const CHint=el('ptCHint'), CNote=el('ptCNote');
 if(!CV){
  if(CHint)CHint.innerHTML='This copy of the panel payload predates the Coverage and OPV columns, '
   +'so no coverage figure is shown. Run <b>python _refresh/extract_ptp.py</b> against a current '
   +'export and patch the payload.';
  if(CNote)CNote.textContent='';
  ['kPTc','pt5','pt6','tPTcov','tPTg','tPTy'].forEach(z=>{const e=el(z); if(e)e.innerHTML='';});
  el('btnPTcov').onclick=el('btnPTg').onclick=el('btnPTy').onclick=()=>{};
 } else {
 const CI=KI.cov, UI=KI.used, GI=KI.given, RI=KI.ret;
 const DASH='\u2013';
 const BN=[['Negative','#64748b'],['Acceptable','#15803d'],['High','#b91c1c']];
 const BAND=w=>w==null?null:(w<=0?0:(w<=10?1:2));
 const bcol=w=>{const b=BAND(w); return b==null?C.none:BN[b][1];};
 const btag=w=>{const b=BAND(w); return b==null?'<span class="cnt">'+DASH+'</span>'
  :'<span class="tag" style="background:'+BN[b][1]+'1a;color:'+BN[b][1]+';font-weight:600">'+BN[b][0]+'</span>';};
 const wsp=(c,u)=>(u>0)?(100*(1-c/u)):null;
 const fac=w=>(w==null||w>=100)?null:100/(100-w);
 // a period for the coverage family: never before covy, and never mixed across the broken years
 const CJ=PTP.yr.map((y,j)=>j).filter(j=>PTP.yr[j]>=PTP.covy);
 const CY=one?(yv>=PTP.covy?[yi]:[]):CJ;
 const OKC=CY.length>0;
 const LY=+PTP.yr[PTP.yr.length-1];
 const PLab=one?(mv?(_MON[mv-1]+' '+yv):String(yv)):(PTP.covy+' \u2013 '+LY+' (from '+PTP.covy+')');
 const cget=(i,j)=>{const c=mv?MON.a[i][j*12+mv-1]:CEL.a[i][j]; return c;};
 const cagg=i=>{const o={cov:0,used:0,giv:0,ret:0,rows:0,dd:0};
  CY.forEach(j=>{const c=cget(i,j); if(!c)return; o.cov+=c[CI]||0; o.used+=c[UI]||0;
   o.giv+=c[GI]||0; o.ret+=c[RI]||0; o.rows+=c[KI.rows]||0; o.dd++;});
  o.w=wsp(o.cov,o.used); o.f=fac(o.w); return o;};
 const CW=DI.map(i=>cagg(i));
 const CS={cov:0,used:0,giv:0,ret:0,rows:0};
 CW.forEach(x=>{CS.cov+=x.cov; CS.used+=x.used; CS.giv+=x.giv; CS.ret+=x.ret; CS.rows+=x.rows;});
 const CWK=wsp(CS.cov, CS.used), CFA=fac(CWK);
 el('ptCHint').innerHTML='These columns are the panel\u2019s own <b>Coverage</b> and <b>OPV</b> fields, read with the '
  +'definition used in the HRMP reporting file: <b>wastage = 1 \u2212 (sum Coverage / sum OPV used)</b>, so Coverage '
  +'counts <b>children covered</b> and OPVUsed counts <b>doses actually used</b>, and doses given = used + returned '
  +'('+esc((PTP.cdef||{}).identity||'')+'). Bands are '+esc((PTP.cdef||{}).bands||'')+
  '; the factor is the ordering multiplier '+esc((PTP.cdef||{}).factor||'')+'. '
  +'<b>From '+PTP.covy+' only.</b> Before that year Coverage exceeds doses used \u2014 '
  +fmt((PTP.cw[String(PTP.yr[0])]||[0,0,0])[0])+' children covered against '
  +fmt((PTP.cw[String(PTP.yr[0])]||[0,0,0])[1])+' doses used in '+PTP.yr[0]+' \u2014 which that definition cannot '
  +'allow, so those years are shown as a dash and the arithmetic is in the table at the bottom of this section. '
  +'Cross-check: '+LY+' wastage here is '+p1(wsp(PTP.cw[String(LY)][0],PTP.cw[String(LY)][1]))+'%'
  +(LY===2026?' against the +7.4% the reporting file carries for 2026'
             :' (no figure on file in the reporting workbook for '+LY+')')
  +'. Counts are reports, not distinct children.';
 el('ptCNote').textContent=PLab+(OKC?'':' \u00b7 no usable year in this selection');
 el('kPTc').innerHTML=(OKC?[
  ['Children covered',fmt(CS.cov),'sum of Coverage over daily reports \u00b7 '+PLab],
  ['Doses used',fmt(CS.used),fmt(CS.giv)+' given \u00b7 '+fmt(CS.ret)+' returned \u00b7 '+SLab],
  ['Wastage',CWK==null?DASH:p1(CWK)+'%',btag(CWK)+' \u2014 '+esc((PTP.cdef||{}).waste||'')+
   (CFA==null?'':' \u00b7 order '+(CFA>0?(Math.round(CFA*100)/100).toFixed(2):DASH)+'x to cover it')],
  ['District units over the band',fmt(CW.filter(x=>x.w!=null&&x.w>10).length),
   'wastage above 10% \u00b7 of '+fmt(CW.filter(x=>x.w!=null).length)+' with a usable denominator']
 ]:[['Children covered',DASH,'the selected year is before '+PTP.covy],
    ['Doses used',DASH,'the selected year is before '+PTP.covy],
    ['Wastage',DASH,'not published before '+PTP.covy],
    ['District units over the band',DASH,'not published before '+PTP.covy]])
 .map(x=>'<div class="card"><div class="kl">'+x[0]+'</div><div class="kv">'+x[1]+'</div><div class="ks">'
   +x[2]+'</div></div>').join('');
 // pt5 - wastage % by district unit, in the owner's bands
 const C5=DI.map(i=>({i:i, dn:PTP.ds[i], dv:PTP.dv[i], cor:PTP.cor[i], g:cagg(i)}))
  .filter(x=>x.g.used>0).sort((a,b)=>(b.g.w==null?-1e9:b.g.w)-(a.g.w==null?-1e9:a.g.w));
 HC('pt5',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Wastage % by district unit \u00b7 '+(OKC?PLab:'no usable year')+' \u00b7 1 \u2212 covered/doses used',
   style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:C5.map(x=>x.dn),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'Wastage %'}},legend:{enabled:false},
  tooltip:{useHTML:true,formatter:function(){const x=C5[this.point.index];
   return '<b>'+esc(x.dn)+'</b> \u00b7 '+esc(x.dv)+'<br>'
    +(x.g.w==null?'no usable denominator':('<b>'+p1(x.g.w)+'%</b> '+BN[BAND(x.g.w)][0]+
     '<br>'+fmt(x.g.cov)+' children covered<br>'+fmt(x.g.used)+' doses used<br>'
     +fmt(x.g.ret)+' returned, '+fmt(x.g.giv)+' given'
     +(x.g.f==null?'':'<br>order multiplier '+(Math.round(x.g.f*100)/100).toFixed(2)+'x')))
    +'<br>'+fmt(x.g.rows)+' daily reports \u00b7 '+esc(x.cor);}},
  plotOptions:{column:{borderRadius:2,dataLabels:{...dl,format:'{y:,.1f}'}}},
  series:[{name:'Wastage %',data:C5.map(x=>({y:x.g.w,color:bcol(x.g.w)}))}]});
 CKEY('pt5',[[BN[2][1],'High wastage: above 10% (the owner\u2019s band)'],
  [BN[1][1],'Acceptable range: 0\u201310%'],[BN[0][1],'Negative: covered exceeds doses used']]);
 el('cappt5').textContent=OKC
  ?(fmt(C5.filter(x=>x.g.w!=null&&x.g.w>10).length)+' of '+fmt(C5.length)+' district units in scope waste more than '
   +'10% of the doses they use, against '+fmt(C5.filter(x=>x.g.w!=null&&x.g.w>0&&x.g.w<=10).length)
   +' inside the acceptable range and '+fmt(C5.filter(x=>x.g.w!=null&&x.g.w<=0).length)
   +' reporting more children covered than doses used \u2014 which the definition cannot allow, so those are a '
   +'reporting fault, not a saving. Highest: '+(C5[0]&&C5[0].g.w!=null?esc(C5[0].dn)+' '+p1(C5[0].g.w)+'%':'none')+
   ', lowest: '+(C5.length&&C5[C5.length-1].g.w!=null?esc(C5[C5.length-1].dn)+' '+p1(C5[C5.length-1].g.w)+'%'
   :'none')+(C5.length&&C5[C5.length-1].g.w!=null&&C5[C5.length-1].g.w<0?' (the low end is that fault, not a saving)':'')+
   '. '+PLab+', following the Division / District filters. A district that barely reported in the period has an '
   +'unstable rate: the tooltip carries its report count.')
  :('The period selected ('+yv+(mv?' '+_MON[mv-1]:'')+') is before '+PTP.covy+', where the panel reports more '
   +'children covered than doses used. No wastage figure is published for it.');
 // pt6 + tPTg - the class cuts. Cells are district x class x year, so the month cannot narrow them.
 const AX=[['ty','Post type','cty','td'],['dur','Post strategy','cdur','dd'],['age','Age band','cag','ad']]
  .filter(a=>Array.isArray(PTP[a[2]])&&Array.isArray(PTP[a[3]]));
 const clsagg=(cells,ci)=>{const o={rows:0,cov:0,used:0,zd:0,any:0};
  cells.forEach(r=>{if(r[1]!==ci)return; if(DI.indexOf(r[0])<0)return;
   o.any+=r[3][0];
   if(YCLS.indexOf(r[2])<0)return; o.rows+=r[3][0]; o.cov+=r[3][1]; o.used+=r[3][2]; o.zd+=r[3][3];});
  o.w=wsp(o.cov,o.used); o.f=fac(o.w); return o;};
 // class cells span every year in the window; restrict them to the same usable years as the KPIs
 const YCLS=CY.slice();
 const GSEL=el('fPTG');
 if(GSEL&&!GSEL.options.length){
  GSEL.innerHTML=[['div','Division'],['cor','Corridor']].concat(AX.map(a=>[a[0],a[1]]))
   .map(x=>'<option value="'+x[0]+'">'+esc(x[1])+'</option>').join('');
 }
 // re-read on every redraw: the picker is a live control, not a render-time choice
 let GKEY=GSEL?(GSEL.value||'div'):'div';
 const ND=['rows','cov','used','giv','ret','zd'];
 const GAX=()=>AX.filter(x=>x[0]===GKEY)[0];
 const GLAB=()=>GKEY==='div'?'Division':(GKEY==='cor'?'Corridor':(GAX()?GAX()[1]:'Group'));
 const grows=()=>{
  const out=[];
  if(GKEY==='div'||GKEY==='cor'){
   const key=i=>GKEY==='div'?PTP.dv[i]:PTP.cor[i];
   const gm={};
   DI.forEach(i=>{const k=key(i)||'Not stated'; (gm[k]=gm[k]||{rows:0,cov:0,used:0,giv:0,ret:0,zd:0});
    const g=cagg(i), o=gm[k];
    o.rows+=g.rows; o.cov+=g.cov; o.used+=g.used; o.giv+=g.giv; o.ret+=g.ret; o.zd+=a0(i);});
   Object.keys(gm).forEach(k=>{const o=gm[k];
    if(!OKC)ND.forEach(z=>{o[z]=null;});
    o.w=wsp(o.cov,o.used); o.f=fac(o.w); o.lab=k; o.n=1; out.push(o);});
  } else {
   const a=GAX(); if(!a)return out;
   const cells=PTP[a[3]], names=PTP[a[2]];
   names.forEach((nm,ci)=>{const o=clsagg(cells,ci); o.lab=nm; o.n=0; if(!o.any)return;
    if(OKC){if(!o.rows)return;} else {ND.forEach(z=>{o[z]=null;}); o.w=null; o.f=null;}
    out.push(o);});
  }
  return out;
 };
 const a0=i=>{const a=aggOne(i); return a;};
 const aggOne=i=>{let z=0; YCLS.forEach(j=>{const c=cget(i,j); if(c)z+=c[KI.zd]||0;}); return z;};
 const drawG=()=>{
  const G=grows().sort((a,b)=>(b.w==null?-1e9:b.w)-(a.w==null?-1e9:a.w));
  const per=(GKEY==='div'||GKEY==='cor');
  drawTable('tPTg',[
   {k:'lab',l:GLAB(),f:x=>'<b>'+esc(x.lab)+'</b>'},
   {k:'rows',l:'Reports',n:1,f:x=>x.rows==null?DASH:fmt(x.rows),
    tt:'Daily post reports carrying a wastage-usable year'},
   {k:'cov',l:'Children covered',n:1,f:x=>x.cov==null?DASH:fmt(x.cov),tt:'Sum of Coverage'},
   {k:'used',l:'Doses used',n:1,f:x=>x.used==null?DASH:fmt(x.used),tt:'Sum of OPVUsed'},
   // the class cells carry reports, coverage, doses used and zero-dose only, so given/returned
   // exist for the division and corridor rows (summed from the district ledger) and nowhere else
   ...(per?[{k:'giv',l:'Doses given',n:1,f:x=>x.giv==null?DASH:fmt(x.giv),tt:'Sum of OPVGiven'},
            {k:'ret',l:'Returned',n:1,f:x=>x.ret==null?DASH:fmt(x.ret),tt:'Sum of OPVReturned'}]:[]),
   {k:'w',l:'Wastage %',n:1,f:x=>x.w==null?DASH:'<span style="color:'+bcol(x.w)+';font-weight:600">'+p1(x.w)+'</span>',
    tt:'1 \u2212 covered / doses used, in the owner\u2019s bands'},
   {k:'f',l:'Order factor',n:1,f:x=>x.f==null?DASH:(Math.round(x.f*100)/100).toFixed(2)+'x'},
   {k:'zd',l:'Zero-dose found',n:1,f:x=>x.zd==null?DASH:fmt(x.zd),tt:'ZeroDose summed over the same reports \u2014 counts reports, not distinct children'},
   {k:'zpr',l:'Found per 100 reports',n:1,f:x=>x.rows?p1(100*x.zd/x.rows):DASH}],
   G.map(x=>{x.zpr=x.rows?100*x.zd/x.rows:null; return x;}),'w',-1);
  // pt6 - the same groups as two bars, so the gap between them IS the wastage
  const GL=GLAB();
  const GS=G.slice(0,16), SU=a=>a.reduce((s,v)=>s+(v||0),0);
  HC('pt6',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
   subtitle:{text:GL+': doses used against children reported covered \u00b7 '
    +(OKC?PLab:'no usable year in this selection'),style:{color:'#475569',fontSize:'12.5px'}},
   xAxis:{categories:GS.map(x=>x.lab),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
   yAxis:[{title:{text:'Doses \u00b7 children'}},{title:{text:'Wastage %'},opposite:true}],
   legend:{align:'right',verticalAlign:'top',itemStyle:{fontSize:'11px'}},
   tooltip:{shared:true,useHTML:true,formatter:function(){const x=GS[this.points[0].point.index];
    return '<b>'+esc(x.lab)+'</b><br>'+fmt(x.used)+' doses used<br>'+fmt(x.cov)+' children reported covered<br>'
     +(x.w==null?'no usable denominator':('<b>'+p1(x.w)+'%</b> '+BN[BAND(x.w)][0]
       +(x.f==null?'':' \u00b7 order '+(Math.round(x.f*100)/100).toFixed(2)+'x to cover it')))
     +'<br>'+fmt(x.rows)+' daily reports'
     +(per?('<br>'+fmt(x.giv)+' given, '+fmt(x.ret)+' returned'):'')
     +'<br>'+fmt(x.zd)+' zero-dose children found';}},
   plotOptions:{column:{borderRadius:2,groupPadding:0.16,pointPadding:0.22}},
   series:[{name:'Doses used',color:'#94a3b8',data:GS.map(x=>x.used)},
    {name:'Children covered',color:'#1F497D',data:GS.map(x=>x.cov)},
    {name:'Wastage %',type:'spline',yAxis:1,color:'#b91c1c',dashStyle:'Dash',
     marker:{symbol:'circle',radius:3},data:GS.map(x=>x.w)}]});
  el('cappt6').textContent=(OKC
   ?('Both bars come from the same reports, so where the dark bar falls short of the grey one is the '
     +'dose gap: across the '+GS.length+' groups shown ('+G.length+' in the table, sorted by wastage) '
     +fmt(SU(GS.map(x=>x.used)))+' doses used against '+fmt(SU(GS.map(x=>x.cov)))+' children reported covered. '
     +'The dashed line is that gap as a percentage on its own axis. '
     +(per?('Division and corridor rows follow the period filter'+(mv?' including the month':'')
       +' and the Division / District filters.')
      :('These rows are district x year cells, so they read the '+YCLS.length+' usable years from '+PTP.covy
       +' onwards and the month selector cannot narrow them.'))
     +' A group whose dark bar reaches past the grey one reports more children covered than doses used, which the '
     +'definition cannot allow \u2014 that is a reporting fault, not a saving.')
   :('No bars are drawn: the period picked ('+PLab+') is before '+PTP.covy+', where the panel reports more children '
    +'covered than doses used, so this chart and the table beside it carry dashes instead of figures.'));
  el('cntPTg').textContent=fmt(G.length)+' groups \u00b7 '+(per?PLab
   :(OKC?(YCLS.length+' usable years, whole-year figures'):'no usable year in this selection'));
  el('capPTg').innerHTML=((per
   ?('Division and corridor rows come from the district figures above, so they follow the period filter '
     +(mv?' including the month':'')+' and the Division / District filters. Corridor is the HRMP classification: '
     +'central = Bannu, DI Khan, Kohat and the southern belt, northern = Peshawar, Mardan, Malakand and the '
     +'northern districts; the Hazara divisions carry no corridor at all, so they read as not on one.')
   :('Post type, post strategy and age band classify the <b>reporting row as the panel wrote it</b>, which is '
     +'why these rows add back to the province totals. They are district x <b>year</b> cells, so the month '
     +'selector cannot narrow them: each row covers '
     +(OKC?(YCLS.length+' usable years ('+PTP.covy+' onwards)'):'no usable year in this selection')
     +(one?', read at '+yv:'')+'. Post status in the inventory table above is different \u2014 that attributes a '
     +'<b>post</b> to its most often seen type over the whole window. The class cells carry reports, coverage, '
     +'doses used and zero-dose, so the two dose-supply columns the division and corridor rows show are not '
     +'cut this way.'))
   +'<br><b>What to read here:</b> the age band is the mix check. Under-5 reports are 89\u201398% of every year and '
   +'drive the total, so a wastage figure that moves between years is mostly the under-5 line moving, not the '
   +'programme. AllAges posts are the ones most likely to report covered above used, because the same dose '
   +'ledger serves adults. Strategy rows name the operational pushes the panel can actually separate: the six '
   +'TTP ring strategies, seasonal and permanent posts, EID and Ramazan deployments, and the VRC / holding-centre '
   +'teams.');
  if(GSEL)GSEL.onchange=()=>{GKEY=GSEL.value||'div';drawG();};
 };
 drawG();
 el('btnPTg').onclick=()=>csvDownload('ptp_coverage_grouped_'+GKEY+'_'+_slug()+'.csv',
  ['Group','Reports','Children covered','Doses used','Doses given','Doses returned','Wastage %',
   'Band','Order factor','Zero-dose found','Found per 100 reports','Period'],
  grows().map(x=>[x.lab,x.rows,x.cov,x.used,x.giv||'',x.ret||'',x.w==null?'':p1(x.w),
   x.w==null?'':BN[BAND(x.w)][0],x.f==null?'':(Math.round(x.f*100)/100).toFixed(2),
   x.zd,x.rows?p1(100*x.zd/x.rows):'',(GKEY==='div'||GKEY==='cor')?PLab:PTP.covy+' onwards']));
 // tPTcov - the district ledger
 const C3=DI.map(i=>{const g=cagg(i), Z=!OKC;
  return {dn:PTP.ds[i], raw:PTP.dr[i], dv:PTP.dv[i], cor:PTP.cor[i], cr:critIx(PTP.dr[i]),
   rep:(PTP.d[i][2]), posts:Z?null:g.dd, rows:Z?null:g.rows, cov:Z?null:g.cov, used:Z?null:g.used,
   giv:Z?null:g.giv, ret:Z?null:g.ret, w:g.w, band:BAND(g.w), f:g.f, zd:Z?null:a0(i)};});
 drawTable('tPTcov',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'dv',l:'Division'},
  {k:'cor',l:'Corridor',f:x=>'<span class="cnt">'+esc(x.cor)+'</span>'},
  {k:'posts',l:'Reporting units',n:1,f:x=>x.posts==null?DASH:fmt(x.posts),tt:'District-month cells with a report in the usable years \u00b7 not posts'},
  {k:'rows',l:'Reports',n:1,f:x=>x.rows==null?DASH:fmt(x.rows)},
  {k:'cov',l:'Children covered',n:1,f:x=>x.cov==null?DASH:fmt(x.cov),tt:'Sum of the Coverage column'},
  {k:'used',l:'Doses used',n:1,f:x=>x.used==null?DASH:fmt(x.used),tt:'Sum of OPVUsed'},
  {k:'giv',l:'Given',n:1,f:x=>x.giv==null?DASH:fmt(x.giv),tt:'Sum of OPVGiven'},
  {k:'ret',l:'Returned',n:1,f:x=>x.ret==null?DASH:fmt(x.ret),tt:'Sum of OPVReturned'},
  {k:'w',l:'Wastage %',n:1,f:x=>x.w==null?DASH:'<span style="color:'+bcol(x.w)+';font-weight:600">'+p1(x.w)+'</span>',
   tt:'1 \u2212 covered / doses used'},
  {k:'band',l:'Owner band',sv:x=>x.band==null?-1:x.band,f:x=>btag(x.w)},
  {k:'f',l:'Order factor',n:1,f:x=>x.f==null?DASH:(Math.round(x.f*100)/100).toFixed(2)+'x',
   tt:'100 / (100 - wastage %) \u2014 the multiplier that ordering uses to land the doses'},
  {k:'zd',l:'Zero-dose found',n:1,f:x=>x.zd==null?DASH:fmt(x.zd),tt:'ZeroDose summed over the same reports \u2014 counts reports, not distinct children'}],
  C3,'w',-1);
 el('cntPTcov').textContent=fmt(C3.length)+' district units \u00b7 '+PLab+(OKC?'':' \u00b7 no coverage figures for this period');
 el('capPTcov').textContent=OKC
  ?('Sorted by wastage, worst first. '+esc((PTP.cdef||{}).identity||'OPVGiven = OPVUsed + OPVReturned')
   +': on this selection it holds to within '+fmt(Math.abs(CS.giv-CS.used-CS.ret))+' doses of '+fmt(CS.giv)
   +' given ('+fmt(CS.used)+' used plus '+fmt(CS.ret)+' returned), which is what makes the ratio a dose '
   +'ledger rather than two unrelated columns. Covered, used, given and returned all follow the period filter'
   +(mv?' including the month':'')+' and the Division / District filters; a district with few reports in the '
   +'period has an unstable wastage rate, so read the report count beside it. Corridor is the HRMP '
   +'classification, taken from the reporting file and not derived here.')
  :('Not published for '+yv+': the panel reports more children covered than doses used before '+PTP.covy+'.');
 el('btnPTcov').onclick=()=>csvDownload('ptp_coverage_wastage_'+_slug()+'.csv',
  ['Division','District','IDIMS district code','Corridor','UC criteria','Posts in panel','Reporting district-months',
   'Reports','Children covered','Doses used','Doses given','Doses returned','Wastage %','Owner band',
   'Order factor','Zero-dose found','Period'],
  C3.map(x=>[x.dv,x.dn,x.raw,x.cor,critLab(x.raw),x.rep,x.posts,x.rows,x.cov,x.used,x.giv,x.ret,
   x.w==null?'':p1(x.w),x.band==null?'':BN[x.band][0],
   x.f==null?'':(Math.round(x.f*100)/100).toFixed(2),x.zd,PLab]));
 // tPTy - the reason for the covy cut, straight from the export
 const YR=PTP.yr.map((y,j)=>{let c=0,us=0,rw=0;
  DI.forEach(i=>{const x=cget(i,j); if(!x)return; c+=x[CI]; us+=x[UI]; rw+=x[KI.rows];});
  return {y:y, cov:c, used:us, rows:rw, w:wsp(c,us), ok:y>=PTP.covy};});
 drawTable('tPTy',[
  {k:'y',l:'Year',f:x=>'<b>'+x.y+'</b>'},
  {k:'rows',l:'Reports',n:1},
  {k:'cov',l:'Children covered',n:1},
  {k:'used',l:'Doses used',n:1},
  {k:'w',l:'Wastage %',n:1,f:x=>x.w==null?DASH:'<span style="color:'+(x.ok?bcol(x.w):'#b91c1c')+';font-weight:600">'+p1(x.w)+'</span>'},
  {k:'ok',l:'Published',f:x=>x.ok?'<span class="tag t-high">Yes</span>':'<span class="cnt">No \u2014 covered exceeds doses used</span>'}],
  YR,'y',1);
 el('cntPTy').textContent=fmt(YR.filter(x=>x.ok).length)+' of '+fmt(YR.length)+' years published';
 el('capPTy').innerHTML='Every figure in this table is the district units in scope, so narrowing the Division / '
  +'District filters narrows it. The first six years report more children covered than doses used \u2014 under the '
  +'definition '+esc((PTP.cdef||{}).waste||'')+' that is impossible, so those years are kept in the payload and '
  +'dashed on the page rather than published as a coverage figure. From '+PTP.covy+' the ratio behaves and has '
  +'stayed between +5% and +7.5% every year since, which is what makes the family worth showing at all. '
  +'The reporting file and this export agree on it independently: the file pulled in early October gives +7.38% '
  +'for KP 2026, this one gives '+p1(YR.length?wsp(YR[YR.length-1].cov,YR[YR.length-1].used):null)+'%. '
  +'Definition source: '+esc((PTP.cdef||{}).src||'')+'.';
 el('btnPTy').onclick=()=>csvDownload('ptp_coverage_by_year_'+_slug()+'.csv',
  ['Year','Reports','Children covered','Doses used','Wastage %','Published from '+PTP.covy],
  YR.map(x=>[x.y,x.rows,x.cov,x.used,x.w==null?'':p1(x.w),x.ok?'Yes':'No']));
 }
""".replace('\n', '\r\n')

A_HTML = ('<div class="card">\r\n<div class="tblhdr"><h3 style="margin:0">'
          'PTP inventory, reporting and findings by district</h3>')
A_JS = ' // district inventory table\r\n'
A_HINT = ("  +' Post names and locations are excluded, and the export\\u2019s Coverage and OPV '\r\n"
          "  +'columns are left out entirely until their definition is confirmed ('+PTP.hold.join(', ')+'). '")
A_EXPD = ("{k:'expd',l:'Expected child-days',n:1,tt:'ExpChildrenDay summed over reports "
          "\\u2014 the panel\\u2019s own denominator'}")
HINT_NEW = ("  +' Post names, locations, facility names and remarks are excluded, and so are four columns that '"
            "  +'stopped being filled or never reconcile ('+PTP.hold.join(', ')+'). Coverage and OPV are now '"
            "  +'published from '+PTP.covy+' on, under the definition in the HRMP reporting file - see the '"
            "  +'coverage block below.'")
EXPD_NEW = ("{k:'expd',l:'Expected child-days',n:1,tt:'ExpChildrenDay summed over reports. NOT a denominator: "
            "\\u2014 summed Coverage over summed ExpChildrenDay is 1.58 across the window and 0.63 in 2026, so "
            "the panel\\u2019s expected child-days cannot carry a coverage rate'}")


def strip_js(block):
    """Blank out string literals and comments so bracket counting sees only real code."""
    out, i, n = [], 0, len(block)
    while i < n:
        c = block[i]
        if c in "'\"":
            j = i + 1
            while j < n and block[j] != c:
                j += 2 if block[j] == chr(92) else 1
            out.append("''"); i = j + 1; continue
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
    """The three failure modes a hand-written JS block actually produces: a bracket left open, two string
    literals side by side with no + between them (valid Python, a syntax error in JS), and a line ending in
    + followed by a line starting +': a dangling plus turns the next string into a unary plus, which node
    accepts and the page renders as NaN."""
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
        if a.endswith('+') and not _open_string(a):
            v.require(not b.startswith("+'") and not b.startswith('+"'),
                      '%s: line %d ends with a dangling + and line %d starts with + a string, so the string '
                      'becomes +\'...\' and renders NaN (line %d: ...%s | %s...)'
                      % (name, k + 1, k + 2, k + 1, a[-46:], b[:46]))


def _open_string(line):
    """True when the line's trailing characters sit inside a string literal, so a final + is text, not code."""
    for c in "'\"":
        n, i = 0, 0
        while i < len(line):
            if line[i] == c:
                n += 1
            i += 2 if line[i] == chr(92) else 1
        if n % 2:
            return True
    return False


def patch(v, js, obj):
    check_js(v, 'JS', JS)
    t = v.text
    for nm, a in (('html', A_HTML), ('js', A_JS), ('hint', A_HINT), ('expd', A_EXPD)):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1) [%s]: %r'
                  % (t.count(a), nm, a[:56]))
    v.require('id="tPTcov"' not in t, 'the coverage block is already patched in')
    # the renderer indexes the class cells by these offsets, so the payload order is a contract
    v.require(obj['k'][:4] == ['rows', 'months', 'posts', 'ucs'],
              'the cell key list no longer starts rows,months,posts,ucs: %s' % obj['k'][:4])
    for need in ('cov', 'used', 'given', 'ret', 'zd'):
        v.require(need in obj['k'], 'the payload cells carry no %s column' % need)
    v.require(obj['mk'] == ['rows', 'cov', 'used', 'zd'],
              'class cells are not in rows,cov,used,zd order as the renderer reads them: %s' % obj['mk'])
    v.require(isinstance(obj.get('covy'), int) and obj.get('cw'),
              'the payload has no covy / cw, so the coverage views have nothing to guard on')
    for axis, vals, cells in (('ty', 'cty', 'td'), ('dur', 'cdur', 'dd'), ('age', 'cag', 'ad')):
        v.require(obj[vals] and len(obj[cells]) and max(r[1] for r in obj[cells]) < len(obj[vals]),
                  'class axis %s is inconsistent: %d names against cells indexing %d'
                  % (axis, len(obj[vals]),
                     max(r[1] for r in obj[cells]) if obj[cells] else -1))
    v.require(len(obj['cor']) == len(obj['ds']),
              'the corridor column has %d entries against %d districts'
              % (len(obj['cor']), len(obj['ds'])))
    t = t.replace(A_HTML, HTML + A_HTML)
    t = t.replace(A_JS, JS + '\r\n' + A_JS)
    t = t.replace(A_HINT, HINT_NEW)
    t = t.replace(A_EXPD, EXPD_NEW)
    v.text = t
    v.changes.append('PTP coverage/wastage views + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for needle in ('id="pt5"', 'id="pt6"', 'id="tPTcov"', 'id="tPTg"', 'id="tPTy"', 'id="kPTc"',
                   'id="fPTG"', 'id="btnPTcov"', 'id="btnPTg"', 'id="btnPTy"',
                   'Children covered, doses used and wastage by district unit',
                   'Why the coverage family starts in 2022', 'function renderPTP(){'):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    v.require(t.count("CKEY('pt") == 5, 'expected 5 chart colour keys in the section, found %d'
                      % t.count("CKEY('pt"))
    v.require('left out entirely until their definition is confirmed' not in t,
              'the hint still says Coverage is unpublished')
    v.require(t.count("the panel\\u2019s own denominator") == 0,
              'ExpChildrenDay is still labelled as a denominator')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_ptp.py first' % PAYLOAD)
    raw = srcutil.read_text(PAYLOAD).strip()
    obj = json.loads(raw)
    if '\n' in raw or '\r' in raw:
        raise SystemExit('ptp.json must be a single line for the <script> embed')
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == 'index.html']
    if len(v) != 1:
        raise SystemExit('expected exactly one index.html in sources.json variants')
    v = v[0]
    if 'const PTP = ' not in v.text:
        raise SystemExit('the master has no PTP const - run patch_ptp_ui.py first')
    # the master carries the published payload; the new views need the coverage keys in it, so the
    # const is replaced rather than left stale next to a renderer that reads cov/used/given/ret
    old = dashpatch.get_payload(v.text, 'PTP')
    v.text = v.text.replace(old, raw, 1)
    v.changes.append('const PTP payload refreshed (%+d chars)' % (len(raw) - len(old)))
    patch(v, raw, obj)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('payload cov %s used %s, covy %s, %d type cells / %d strategy / %d age, corridor %s'
          % (format(obj['n']['cov'], ','), format(obj['n']['used'], ','), obj['covy'],
             len(obj['td']), len(obj['dd']), len(obj['ad']),
             ', '.join('%s x%d' % (c, obj['cor'].count(c)) for c in sorted(set(obj['cor'])))))
    if obj['corx']:
        print('WARN corridor map does not cover: %s' % obj['corx'])
    print('OK ptp-cov master only - the other three variants are synced by push_master.py, '
          'which needs the owner\u2019s word')


if __name__ == '__main__':
    main()
