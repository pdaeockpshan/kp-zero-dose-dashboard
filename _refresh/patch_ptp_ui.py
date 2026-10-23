"""Insert the Permanent Transit Points block (const PTP) into the index.html master.

Adds, in the master:
  1. `const PTP = {...}` before `const SURVW = `, filled from _refresh/out/ptp.json so the
     section is live the moment the master is patched; later refreshes go through
     `refresh.py run --only ptp`.
  2. A Cross-cutting tab button, pane markup, colour, icon and TABS / render / badge wiring.
  3. `renderPTP()`: a Reporting period control (year, month, or both), KPI strip, four charts
     (post status by district, reporting cadence, zero-dose records found, cross-border
     children), the district inventory table, the district triangulation table (same UCs through
     the campaign and routine-EPI channels) and the UC list, each with a CSV download.

The period control reads the payload month cells (d[i][4], one row per district per reporting
month). It is a Year picker with a month picker that cascades off it: the month list holds the months
of the chosen year that the district units in scope actually filed, and is disabled until a year is
picked, so a period is always Year or Year/month and never one month summed across years. Views that
compare whole rosters - the post-status chart, the post listing, the UC list and the campaign / EPI
joins - stay window-wide inside the Division / District filter and say so.

Only the master is written. preview.html, public/index.html and the internal build pick the
block up through `_refresh/push_master.py`, which is the owner-approved route for propagating a
hand-edited master and is run together with publishing, not before it.

Every figure keeps its own denominator and says so. The PTP panel counts reports, not children;
the campaign zero-dose figures are the round's own reported and covered counts; routine EPI
coverage is a Jan-2024 to Sep-2026 cumulative window that cannot be year-matched to a PTP year.
The Coverage and OPV columns of the source export are not in the payload at all until the owner
confirms what they count, so nothing here presents PTP vaccination coverage.

All inserted text uses CRLF so the file's line endings stay uniform.
Every anchor is asserted to occur exactly once before editing; nothing is written unless the
patch applies cleanly.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'ptp.json')

HTML = (
 '<!-- ================= PERMANENT TRANSIT POINTS (IDIMS) ================= -->\r\n'
 '<section class="pane" id="p-ptp">\r\n'
 '<div class="hint" id="ptHint"></div>\r\n'
 '<div class="cqbar"><b>Reporting period</b><select id="fPTY" title="IDIMS reports one row per '
 'post per day; pick a year, then a month of that year"></select>'
 '<select id="fPTM" title="Months of the year picked on the left - pick a year first"></select>'
 '<span class="cnt" id="ptNote"></span></div>\r\n'
 '<div class="kpis" id="kPT"></div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="pt1" class="ch" style="height:360px"></div><div class="cap" id="cappt1"></div></div>\r\n'
 '<div class="card"><div id="pt2" class="ch" style="height:360px"></div><div class="cap" id="cappt2"></div></div>\r\n'
 '</div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="pt3" class="ch" style="height:340px"></div><div class="cap" id="cappt3"></div></div>\r\n'
 '<div class="card"><div id="pt4" class="ch" style="height:340px"></div><div class="cap" id="cappt4"></div></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">PTP inventory, reporting and findings by district</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntPTa"></span>'
 '<button class="btn" id="btnPTa">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTa"></table></div>\r\n'
 '<div class="cap" id="capPTa"></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The same union councils through the other channels</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntPTb"></span>'
 '<button class="btn" id="btnPTb">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTb"></table></div>\r\n'
 '<div class="cap" id="capPTb"></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Union councils with the most zero-dose children found at a PTP</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntPTu"></span>'
 '<button class="btn" id="btnPTu">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTu"></table></div>\r\n'
 '<div class="cap" id="capPTu"></div>\r\n'
 '</div>\r\n'
 '</section>\r\n'
)

JS = r"""
// ---------- Permanent Transit Points (IDIMS PTP panel) ----------
var _PTC=null, _PTU=null, _PTJ=null, _PTM=null;
function ptpCells(){
 if(_PTC&&_PTC.d===PTP.d.length&&_PTC.y===PTP.yr.length)return _PTC;
 _PTC={d:PTP.d.length, y:PTP.yr.length, a:PTP.d.map(r=>{const a=new Array(PTP.yr.length).fill(null);
  r[3].forEach(c=>{a[c[0]]=c[1];}); return a;})};
 return _PTC;
}
function ptpMonths(){
 if(_PTM&&_PTM.d===PTP.d.length&&_PTM.y===PTP.yr.length)return _PTM;
 const nY=PTP.yr.length;
 const a=PTP.d.map(r=>{const x=new Array(nY*12).fill(null);
  (r[4]||[]).forEach(c=>{x[c[0]]=c[1];}); return x;});
 return _PTM={d:PTP.d.length, y:nY, a:a};
}
function ptpUCs(){
 if(_PTU&&_PTU.n===PTP.u.length&&_PTU.d===PTP.d.length)return _PTU;
 const g=PTP.d.map(()=>[]);
 PTP.u.forEach(r=>{if(g[r[1]])g[r[1]].push(r);});
 return _PTU={n:PTP.u.length, d:PTP.d.length, g:g};
}
function ptpIdx(){
 if(_PTJ)return _PTJ;
 const z={}, e={};
 (ZD||[]).forEach(r=>{if(r.c)z[String(r.c)]=r;});
 (EPI||[]).forEach(r=>{if(r.c)e[String(r.c)]=r;});
 return _PTJ={z:z, e:e, v:(typeof VUC!=='undefined'?VUC:{})};
}
function ptBadge(){const b=el('bPT'); if(!b)return; b.textContent=fmt((PTP&&PTP.n||{}).posts||0)+' posts';}
function renderPTP(){
 if(typeof PTP==='undefined'||!PTP||!PTP.d||!PTP.d.length)return;
 const KI={}; PTP.k.forEach((k,i)=>{KI[k]=i});
 const CEL=ptpCells(), MON=ptpMonths(), UCG=ptpUCs().g, IX=ptpIdx(), N=PTP.n||{};
 const SEL=el('fPTY'), MSL=el('fPTM'), nY=PTP.yr.length, ALLJ=PTP.yr.map((y,j)=>j);
 if(SEL&&!SEL.options.length){
  SEL.innerHTML='<option value="0">Whole window '+esc(PTP.win)+'</option>'+
   PTP.yr.map(y=>'<option value="'+y+'">'+y+'</option>').join('');
  SEL.onchange=()=>render();
 }
 const yv=SEL?+SEL.value:0, yi=PTP.yr.indexOf(yv);
 const all=yi<0, one=!all, sJ=all?ALLJ:[yi];
 const whole=!fDiv.value&&!fDist.value&&!DSEL;
 const DI=[];
 PTP.d.forEach(r=>{const i=r[0];
  if(!dOK(PTP.dr[i]))return;
  if(fDiv.value&&PTP.dv[i]!==fDiv.value)return;
  DI.push(i);});
 // the month list cascades off the year: only months the district units in scope actually filed
 if(MSL){
  const ms=one?_MON.map((mn,m)=>m+1).filter(m=>DI.some(i=>!!MON.a[i][yi*12+m-1])):[];
  const keep=ms.indexOf(+MSL.value)>-1?+MSL.value:0;
  MSL.innerHTML=one
   ?('<option value="0">All of '+yv+'</option>'+ms.map(m=>'<option value="'+m+'">'+_MON[m-1]+'</option>').join(''))
   :'<option value="0">Pick a year first</option>';
  MSL.value=String(keep);
  MSL.disabled=!one;
  MSL.title=one?('Month of '+yv+' \u00b7 '+ms.length+' of 12 months filed by the district units in scope')
   :'Pick a year on the left first, then a month of that year';
  MSL.onchange=()=>render();
 }
 const mv=one&&MSL?+MSL.value:0;
 const MDen=one?(mv?1:12):nY*12;
 const MSl=MDen===1?'month':'months', MSs=MDen===1?'month slot':'month slots';
 const SLab=one?(mv?(_MON[mv-1]+'/'+yv):('all of '+yv)):('whole window '+PTP.win);
 const perSet=one;
 const dRep=i=>one?(mv?!!MON.a[i][yi*12+mv-1]:!!CEL.a[i][yi]):(PTP.d[i][4]||[]).length>0;
 const agg=i=>{const a=new Array(PTP.k.length).fill(0); let rep=0, ucS=0;
  sJ.forEach(j=>{const c=mv?MON.a[i][j*12+mv-1]:CEL.a[i][j]; if(!c)return;
   for(let m=0;m<a.length;m++)a[m]+=(c[m]||0);});
  if(one){const c=mv?MON.a[i][yi*12+mv-1]:CEL.a[i][yi]; rep=c?c[KI.posts]:0; ucS=c?c[KI.ucs]:0;}
  else{rep=PTP.d[i][2]; ucS=PTP.d[i][1];}
  return{a:a, rep:rep, ucS:ucS};};
 const sF=PTP.st.indexOf('Functional');
 const T=(x,j)=>((PTP.pd[x]||[])[j]||[]);
 const SM=a=>a.reduce((s,v)=>s+(v||0),0);
 const QQ=(typeof q!=='undefined'&&q.value||'').trim().toLowerCase();
 const R=DI.map(i=>{
  const g=agg(i), a=g.a, st=T(i,1), inv=SM(st), uc=UCG[i]||[];
  let zn=0, zrc=0, zcv=0, znc=0;
  uc.forEach(r=>{const x=IX.z[r[0]]; if(!x||x['r'+LCP]==null)return;
   zn++; if(x['c'+LCP]!=null){zrc+=x['r'+LCP]; zcv+=x['c'+LCP]; znc++;}});
  const ER=uc.map(r=>IX.e[r[0]]).filter(Boolean);
  const E=ER.length?aggE(ER):null;
  return{i, raw:PTP.dr[i], dn:PTP.ds[i], dv:PTP.dv[i],
   posts:PTP.d[i][2], ucs:uc.length, onmap:uc.filter(r=>r[6]).length,
   inv:inv, fn:inv&&sF>=0?(st[sF]||0)/inv*100:null,
   rep:g.rep, ucS:g.ucS, mon:a[KI.months], monp:MDen?Math.min(100,a[KI.months]/MDen*100):null,
   rows:a[KI.rows], zd:a[KI.zd],
   zpr:a[KI.rows]?a[KI.zd]/a[KI.rows]*100:null,
   cin:a[KI.cbu_in]+a[KI.cbo_in], cout:a[KI.cbu_out]+a[KI.cbo_out],
   nbv:a[KI.nbv], expd:a[KI.expd], teams:a[KI.teams], sup:a[KI.sup],
   zn:zn, zrc:zrc, zcv:zcv, znc:znc, zp:zrc?zcv/zrc*100:null,
   euc:ER.length, ep:E?E['p_opv3']:null};});
 const K=k=>R.reduce((s,x)=>s+(x[k]||0),0);
 const INV=K('inv'), FNP=K('inv')?(function(){let f=0; R.forEach(x=>{f+=(T(x.i,1)[sF]||0);}); return f;})():0;
 const FPP=INV&&sF>=0?FNP/INV*100:null;
 const REP=DI.filter(i=>dRep(i)).length;
 const p1=v=>v==null?'\u2013':(Math.round(v*10)/10).toFixed(1);
 const rt=(a,b)=>(a==null||!b)?null:100.0*a/b;
 const band=(v,hi,lo)=>v==null?C.none:v>=hi?C.high:v>=lo?C.mod:C.crit;
 const cc=(v,hi,lo)=>v==null?'\u2013':'<span style="color:'+(v>=hi?'#047857':v>=lo?'#92400E':'#991B1B')+';font-weight:600">'+p1(v)+'</span>';
 el('ptHint').innerHTML='<b>'+fmt(N.posts||0)+' Permanent Transit Points</b> in the IDIMS PTP panel, '
  +'reported one row per post per day across '+PTP.win+'. This page reads what the panel counts '
  +'reliably \u2014 posts, whether they report, zero-dose children found, cross-border children '
  +'counted \u2014 and triangulates the same union councils against the campaign zero-dose data and '
  +'routine EPI. <b>The panel counts reports, not distinct children</b>: a child seen at a post '
  +'twice in a week is in the tally twice, so findings columns are read as signal, not as a '
  +'coverage figure. The period control takes a year and then a month of that year \u2014 the panel '
  +'reports in bursts, so a single month is a fair unit to compare, and a month is never summed '
  +'across years.'
  +' Post names and locations are excluded, and the export\u2019s Coverage and OPV '
  +'columns are left out entirely until their definition is confirmed ('+PTP.hold.join(', ')+'). '
  +'Source: '+esc(PTP.src)+', as at '+esc(PTP.asof)+(N.drop||Object.keys(PTP.drop||{}).length?
   ' \u00b7 '+fmt(N.read)+' rows read, '+fmt(N.kept)+' kept':'')+'.';
 el('ptNote').textContent=DI.length+' of '+PTP.ds.length+' district units \u00b7 '+SLab+
  (whole?'':' \u00b7 scoped by the Division / District filters')+
  ' \u00b7 '+K('ucS')+' of '+K('ucs')+' UCs reporting'+(perSet?' in this period':' across the window')+
  ' \u00b7 '+fmt(K('rows'))+' reports';
 el('kPT').innerHTML=[
  ['Permanent Transit Points',fmt(K('posts')),(DI.length+' district units \u00b7 '+PTP.win+' \u00b7 status as last reported'+(whole?'':(' (out of '+fmt(N.posts)+' province-wide)')))],
  ['Reported functional',pc(FPP),fmt(FNP)+' of '+fmt(INV)+' posts carrying a status'],
  ['Reports logged',fmt(K('rows')),SLab+' \u00b7 '+REP+' of '+DI.length+' district units reporting in it'],
  ['Zero-dose children found',fmt(K('zd')),p1(rt(K('zd'),K('rows')))+' per 100 reports \u00b7 counts reports, not children',C.crit],
  ['Cross-border children',fmt(K('cin')),fmt(K('cout'))+' counted leaving \u00b7 both age bands, '+SLab],
  ['Union councils reached',fmt(K('ucS')),'of the '+fmt(K('ucs'))+' UCs the panel files reports under \u00b7 '+K('onmap')+' of them sit on the KP UC map'+(whole?(', '+fmt(N.uc_scope||0)+' inside the campaign scope'):(' \u00b7 campaign-scope total '+fmt(N.uc_scope||0)+' is province-wide'))]
 ].map(x=>'<div class="card"><div class="kl">'+x[0]+'</div><div class="kv"'+(x[3]?' style="color:'+x[3]+'"':'')+'>'
  +x[1]+'</div><div class="ks">'+x[2]+'</div></div>').join('');
 // pt1 - post status by district
 const RS=R.slice().sort((a,b)=>(a.fn==null)-(b.fn==null)||a.fn-b.fn);
 const STC={Functional:'#15803d', 'Non Functional':'#d97706', Closed:'#b91c1c'};
 HC('pt1',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'PTPs by functional status as last reported \u00b7 '+(whole?'whole province':'current scope'),style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:RS.map(x=>x.dn),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'Posts'}},legend:{enabled:false},
  tooltip:{shared:true,useHTML:true,formatter:function(){const x=RS[this.point.index];
   return '<b>'+esc(x.dn)+'</b><br>'+fmt(x.posts)+' posts in the panel<br>'
    +(x.fn==null?'no status reported':'<b>'+pc(x.fn)+'</b> reported functional');}},
  plotOptions:{column:{stacking:'normal',borderRadius:1}},
  series:PTP.st.map((s,j)=>({name:s,color:STC[s]||'#94a3b8',data:RS.map(x=>T(x.i,1)[j]||0)}))});
 CKEY('pt1',PTP.st.map(s=>[STC[s]||'#94a3b8',s]));
 el('cappt1').textContent=fmt(INV)+' of '+fmt(K('posts'))+' posts in scope carry a functional status, of which '
  +fmt(FNP)+' ('+pc(FPP)+') were reported functional at their last record. '
  +(RS.filter(x=>x.fn!=null&&x.fn<100).length?
   'Weakest: '+RS.filter(x=>x.fn!=null&&x.fn<100).slice(0,3).map(x=>esc(x.dn)+' '+pc(x.fn)).join(', ')+'. ':'')
  +(RS.filter(x=>x.fn==null).length?
   (RS.filter(x=>x.fn==null).length)+' district units report posts but no status at all \u2014 '+
   RS.filter(x=>x.fn==null).slice(0,3).map(x=>esc(x.dn)).join(', ')+' among them. ':'')+
  'Counts are the whole '+PTP.win+' roster for the district units in scope, because a post is listed once whatever the period; '
  +'neither the year nor the month selector changes this chart.';
 // pt2 - reporting cadence: by month inside the chosen year, by year across the window
 const CD=one?_MON.map((mn,m)=>({lab:mn, j:yi, m:m})):PTP.yr.map((y,j)=>({lab:String(y), j:j, m:-1}));
 CD.forEach(x=>{let rows=0, zd=0, dd=0, mon=0, mx=0;
  DI.forEach(i=>{const c=x.m<0?CEL.a[i][x.j]:MON.a[i][x.j*12+x.m];
   if(!c)return; dd++; rows+=c[KI.rows]; zd+=c[KI.zd];
   if(x.m<0){mon+=c[KI.months]; if(c[KI.months]>mx)mx=c[KI.months];}});
  x.rows=rows; x.zd=zd; x.dd=dd; x.full=x.m<0?(dd?mx>=11:null):null;});
 const CMAX=Math.max.apply(null,CD.map(x=>x.rows))||1;
 const CCOL=x=>!x.rows?null:(x.full===null
  ?(mv?(x.m===mv-1?'#1F497D':'#94a3b8'):(DI.length&&x.dd/DI.length<0.5?'#d97706':'#1F497D'))
  :(x.full?(x.rows>CMAX*0.5?'#1F497D':'#94a3b8'):'#d97706'));
 const CZ=CD.filter(x=>!x.rows).map(x=>x.lab);
 HC('pt2',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:(one?('Daily reports logged in '+yv+' by month'):('Daily reports logged by year'))
   +(mv?', '+_MON[mv-1]+' is the selected month':''),
   style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:CD.map(x=>x.lab),labels:{style:{color:'#1f2937',fontSize:one?'10.5px':'10px'}}},
  yAxis:{title:{text:'Reports logged'},max:Math.ceil(CMAX*1.14/1000)*1000},legend:{enabled:false},
  tooltip:{useHTML:true,formatter:function(){const x=CD[this.point.index];
   return '<b>'+esc(x.lab)+(one?(' '+yv):'')+'</b><br>'+fmt(x.rows)+' reports<br>'
    +fmt(x.dd)+' district units reporting'
    +(x.full===null?'':'<br>'+fmt(x.mon)+' district-months reported')
    +'<br>'+fmt(x.zd)+' zero-dose children found';}},
  plotOptions:{column:{borderRadius:2,dataLabels:{...dl,format:'{y:,.0f}'}}},
  series:[{name:'Reports',data:CD.map(x=>({y:x.rows,color:CCOL(x)}))}]});
 CKEY('pt2',one?(mv?[['#1F497D','The month picked in the period filter'],
   ['#94a3b8','Other months that year reported in']]
  :[['#1F497D','At least half the district units in scope reported that month'],
   ['#d97706','Thin month: fewer than half of them reported']])
  :[['#1F497D','More than half the best year, with a district reaching 11 of 12 months'],
   ['#94a3b8','Light year, with a district reaching 11 of 12 months'],
   ['#d97706','Partial or thin year (no district reached 11 reporting months)']]);
 const CNZ=CD.filter(x=>x.rows);
 const CMIN=CNZ.reduce((b,x)=>x.rows<b.rows?x:b,CNZ[0]);
 const CPEAK=CNZ.reduce((b,x)=>x.rows>b.rows?x:b,CNZ[0]);
 el('cappt2').textContent=one
  ?('Bar height is the number of daily reports logged in each month of '+yv+', so a gap is a month the panel '
   +'was not used, not a district that stopped working. '
   +(CZ.length?(CZ.length+' of the 12 months of '+yv+' have no report: '+CZ.join(', ')+'.'):'All 12 months of '+yv+' carry reports.')
   +(CPEAK?(' Busiest month: '+CPEAK.lab+' with '+fmt(CPEAK.rows)+' reports.'):'')
   +(mv?(' The period filter is on '+_MON[mv-1]+'/'+yv+', so every figure above and below this chart reads that month alone.'):'')
   +(CZ.length?(' The month picker offers only the '+(CD.length-CZ.length)+' months of '+yv+' that filed.'):'')
   +' Counts follow the Division / District filters.')
  :('The panel does not report at a steady rate: '
   +(CMIN?fmt(CMIN.rows)+' reports in '+CMIN.lab:'no reports')+' against '
   +(CPEAK?fmt(CPEAK.rows)+' in '+CPEAK.lab:'none')
   +', so a district that looks weak in one period may simply be in a period the panel barely used. '
   +'A bar is amber when no district in it reached 11 of 12 reporting months \u2014 the export is dated '+PTP.asof
   +', so the latest year is a part year by construction.'
   +' Counts follow the Division / District filters.');
 // pt3 - zero-dose findings per 100 reports, coloured by reporting depth
 const RZ=R.slice().sort((a,b)=>(b.zpr==null?-1e9:b.zpr)-(a.zpr==null?-1e9:a.zpr));
 const ZTOP=R.slice().sort((a,b)=>b.zd-a.zd)[0];
 HC('pt3',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Zero-dose children found per 100 daily reports\u00b7 '+SLab,style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:RZ.map(x=>x.dn),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'Zero-dose reports per 100 reports'}},legend:{enabled:false},
  tooltip:{useHTML:true,formatter:function(){const x=RZ[this.point.index];
   return '<b>'+esc(x.dn)+'</b><br>'+fmt(x.zd)+' zero-dose children found<br>'
    +p1(x.zpr)+' per 100 reports \u00b7 '+fmt(x.rows)+' reports<br>'
    +fmt(x.mon)+' of '+MDen+' reporting '+MSl+' ('+p1(x.monp)+'%)';}},
  plotOptions:{column:{borderRadius:2,pointPadding:0.12}},
  series:[{name:'Found per 100 reports',data:RZ.map(x=>({y:x.zpr,color:band(x.monp,75,50)}))}]});
 CKEY('pt3',[[C.high,'District unit reported 75% or more of the months in the period'],
  [C.mod,'50\u201375%'],[C.crit,'under 50%'],[C.none,'no reports in the period']]);
 el('cappt3').textContent='Plotted per 100 daily reports so one large district does not flatten the rest; '
  +'the absolute count is in the tooltip. Colour is reporting depth, not performance: a pale bar means the '
  +'district unit reported in only part of the '+MDen+' '+MSs+' this period offers ('+SLab+'), so what '
  +'sits under it is an undercount, and a district with a handful of reports has an unstable rate. '
  +fmt(K('zd'))+' zero-dose children were found across '+fmt(K('rows'))+' reports in scope ('
  +p1(rt(K('zd'),K('rows')))+' per 100 reports), the largest absolute total in scope being '
  +(ZTOP?esc(ZTOP.dn)+' with '+fmt(ZTOP.zd):'none')+'. These are report counts, not unique children, '
  +'and they are not a denominator for coverage.';
 // pt4 - cross-border movement, top district units with the rest bucketed
 const CB=R.slice().sort((a,b)=>(b.cin+b.cout)-(a.cin+a.cout)), CBT=CB.slice(0,10), CBO=CB.slice(10);
 const CBOth=k=>CBO.reduce((s,x)=>s+x[k],0);
 const CBrest=CB.length>CBT.length&&K('cin')+K('cout')?((K('cin')+K('cout'))-CBT.reduce((s,x)=>s+x.cin+x.cout,0))/(K('cin')+K('cout'))*100:null;
 HC('pt4',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Cross-border children counted at PTPs \u00b7 '+SLab,style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:CBT.map(x=>x.dn).concat(CBO.length?['All other district units']:[]),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'Children counted (reports)'}},legend:{enabled:false},
  tooltip:{shared:true},plotOptions:{column:{borderRadius:1}},
  series:[{name:'Counted entering',color:'#1F497D',data:CBT.map(x=>x.cin).concat(CBO.length?[CBOth('cin')]:[])},
          {name:'Counted leaving',color:'#c2410c',data:CBT.map(x=>x.cout).concat(CBO.length?[CBOth('cout')]:[])}]});
 CKEY('pt4',[['#1F497D','Cross-border children counted entering (both age bands)'],
  ['#c2410c','Counted leaving (both age bands)']]);
 el('cappt4').textContent='Under-10 and above-10 cross-border columns are added together: '
  +fmt(K('cin'))+' entering against '+fmt(K('cout'))+' leaving in '+SLab+'. The two directions come from the same '
  +'daily reports, so a child crossing twice is counted twice, and the age bands stop at 10 \u2014 they are not a '
  +'population estimate. Use them to see which district units sit on a live crossing route.'
  +(CBrest==null?'':' The district units left out of the chart carry '+(CBrest<0.1?'less than 0.1%':p1(CBrest)+'%')+' of the cross-border reports in this selection, so a flat bar means no transit route on it rather than weak reporting.');
 // district inventory table
 drawTable('tPTa',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'dv',l:'Division'},
  {k:'cr',l:'UC criteria',sv:x=>{const v=critIx(x.raw); return v==null?99:v;},f:x=>critTag(x.raw)},
  {k:'posts',l:'PTPs',n:1,tt:'Permanent Transit Points listed for this district across '+PTP.win},
  {k:'fn',l:'Functional %',n:1,f:x=>cc(x.fn,90,75),tt:'Posts reported Functional at their last record / posts carrying any status'},
  {k:'rep',l:'Reporting PTPs',n:1,tt:'Posts with at least one report in '+SLab},
  {k:'monp',l:'Reporting months %',n:1,f:x=>cc(x.monp,75,50),sv:x=>x.monp==null?-1:x.monp,
   tt:x=>fmt(x.mon)+' of '+MDen+' '+MSl+' in '+SLab},
  {k:'ucS',l:'UCs reporting',n:1,tt:'Union councils with at least one report in '+SLab},
  {k:'ucs',l:'UCs reached',n:1,tt:'Union councils the reporting posts filed under, over '+PTP.win},
  {k:'rows',l:'Reports',n:1,tt:'Daily post reports logged in '+SLab},
  {k:'zd',l:'Zero-dose found',n:1,tt:'ZeroDose summed over reports \u2014 counts reports, not distinct children'},
  {k:'zpr',l:'Found per 100 reports',n:1,f:x=>x.zpr==null?'\u2013':p1(x.zpr),tt:'Zero-dose reports per 100 daily reports'},
  {k:'cin',l:'CB entering',n:1,tt:'Cross-border children counted entering, under-10 + above-10 columns'},
  {k:'cout',l:'CB leaving',n:1,tt:'Cross-border children counted leaving, under-10 + above-10 columns'},
  {k:'nbv',l:'Newborn vacc',n:1,tt:'new_born_vaccination summed over reports'},
  {k:'expd',l:'Expected child-days',n:1,tt:'ExpChildrenDay summed over reports \u2014 the panel\u2019s own denominator'}],
  R,'monp',1);
 el('cntPTa').textContent=R.length+' district units \u00b7 '+SLab;
 el('capPTa').textContent='Sorted by reporting depth, weakest first. "PTPs" is the panel listing over the whole '
  +'window; "Reporting PTPs", "UCs reporting", reports and findings follow the period selectors, which is why a '
  +'month view can show a district with posts listed but nothing reporting. Three district units are kept as IDIMS '
  +'reports them because the dashboard\u2019s EPI split cannot be recovered from them \u2014 '
  +esc(PTP.dr.filter(d=>['KURRAM','CHITRAL','WAZIR-S'].indexOf(d)>=0).join(', '))+
  ' \u2014 and Kohistan Palas appears in the campaign and EPI data but has no PTP report at all. '
  +'Zero-dose and cross-border columns count reports, so they cannot be turned into coverage.';
 el('btnPTa').onclick=()=>csvDownload('ptp_district_inventory_'+_slug()+'.csv',
  ['Division','District','IDIMS district code','UC criteria','PTPs in panel','Posts with a status','Reported functional',
   'Functional %','Reporting PTPs','Reporting months','Months possible','Reporting months %',
   'UCs reporting in period','UCs reached','UCs on map',
   'Reports logged','Zero-dose found','Found per 100 reports','Cross-border entering','Cross-border leaving',
   'Newborn vaccinations','Expected child-days','Teams','Supervisors'],
  R.map(x=>[x.dv,x.dn,x.raw,critLab(x.raw),x.posts,x.inv,T(x.i,1)[sF]||0,x.fn==null?'':p1(x.fn),x.rep,
   x.mon,MDen,p1(x.monp),x.ucS,x.ucs,x.onmap,x.rows,x.zd,x.zpr==null?'':p1(x.zpr),x.cin,x.cout,x.nbv,x.expd,x.teams,x.sup]));
 // triangulation table
 drawTable('tPTb',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'dv',l:'Division'},
  {k:'cr',l:'UC criteria',sv:x=>{const v=critIx(x.raw); return v==null?99:v;},f:x=>critTag(x.raw)},
  {k:'ucs',l:'UCs with a PTP',n:1,tt:'Union councils the PTP panel files reports under, over '+PTP.win+' \u2014 the campaign and EPI columns beside them are rosters, not period figures'},
  {k:'onmap',l:'On the UC map',n:1,tt:'UCs whose code matches the dashboard UC map'},
  {k:'zn',l:'In campaign ZD data',n:1,tt:'PTP UCs that appear in the zero-dose campaign export'},
  {k:'zd',l:'PTP zero-dose found',n:1,tt:'Reports in '+SLab+', not distinct children'},
  {k:'zrc',l:'Campaign reported ('+esc(CAMP[LCP])+')',n:1,tt:'Zero-dose children reported in the campaign, over the same UCs'},
  {k:'zcv',l:'Campaign covered',n:1,tt:'Covered, over the UCs that reported a covered figure'},
  {k:'zp',l:'Covered %',n:1,f:x=>cc(x.zp,80,50),tt:'Covered / reported over the PTP UCs that carry both figures'},
  {k:'euc',l:'In EPI data',n:1,tt:'PTP UCs appearing in the KP EPI-MIS UC file'},
  {k:'ep',l:'OPV-3 %',n:1,f:x=>pE(x.ep),tt:'Routine OPV-3 over the same UCs \u00b7 cumulative '+esc(EMETA.per||'')+', not year-matched to the PTP selection; above 100% is more doses than their recorded target, the same over-entry the EPI pages carry'}],
  R,'zd',-1);
 el('cntPTb').textContent=R.length+' district units \u00b7 '+K('ucs')+' PTP UCs';
 el('capPTb').textContent='Every row compares the same union councils, not the same children. '
  +fmt(K('zn'))+' of '+K('ucs')+' PTP UCs also appear in the campaign zero-dose export, and '+fmt(K('euc'))+
  ' appear in the routine EPI file, matched by UC code exactly as the cross-cutting pages do it: EPI-MIS numbers '
  +'union councils in its own coding, so a blank OPV-3 cell means no EPI row carried that code, not zero doses given. '
  +'Campaign covered % uses only UCs that reported a covered figure, and for '
  +esc(CAMP[LCP])+' that figure is the round\u2019s own export, not yet independently confirmed. Routine OPV-3 is a '
  +esc(EMETA.per||'')+' cumulative window and cannot be narrowed to the selected PTP period. '
  +'The PTP zero-dose column is the period above the table; the UC counts are the whole-window roster. '
  +'Where the PTP channel is busy but the campaign covered share is low, mobile children are being reached once and '
  +'missed again; where PTP UCs are few but EPI coverage is weak, the fixed transit network is not there to catch them.'
  +' An OPV-3 figure above 100% is more doses reported than the recorded target for those UCs, the same over-entry the EPI pages carry.';
 el('btnPTb').onclick=()=>csvDownload('ptp_triangulation_'+_slug()+'.csv',
  ['Division','District','IDIMS district code','UC criteria','UCs with a PTP','UCs on the UC map','UCs in campaign ZD data',
   'UCs with a covered figure','PTP zero-dose found','Campaign reported ('+CAMP[LCP]+')','Campaign covered',
   'Campaign covered %','UCs in EPI data','OPV-3 %'],
  R.map(x=>[x.dv,x.dn,x.raw,critLab(x.raw),x.ucs,x.onmap,x.zn,x.znc,x.zd,x.zrc,x.zcv,x.zp==null?'':p1(x.zp),x.euc,
   x.ep==null?'':p1(x.ep)]));
 // UC table
 const UR=[];
 DI.forEach(i=>{(UCG[i]||[]).forEach(r=>{
  const v=IX.v[r[0]], z=IX.z[r[0]], e=IX.e[r[0]];
  const nm=v?v[3]:(z?z.u:(e?e.u:''));
  if(QQ&&!((nm||'')+' '+PTP.ds[i]).toLowerCase().includes(QQ))return;
  UR.push({c:r[0], dn:PTP.ds[i], dv:PTP.dv[i], t:v?v[2]:'', u:nm||'(name not in the dashboard UC files)',
   posts:r[2], mon:r[3], zd:r[4], cbu:r[5], map:r[6],
   zr:z?z['r'+LCP]:null, zc:z?z['c'+LCP]:null,
   zp:z&&z['r'+LCP]?((z['c'+LCP]==null?null:z['c'+LCP]/z['r'+LCP]*100)):null,
   ep:e?eP(e,'opv3'):null});});});
 UR.sort((a,b)=>b.zd-a.zd);
 const UT=UR.slice(0,120);
 drawTable('tPTu',[
  {k:'u',l:'Union council',f:x=>'<b>'+esc(x.u)+'</b>'},
  {k:'dn',l:'District'},
  {k:'t',l:'Tehsil'},
  {k:'c',l:'UC code',f:x=>'<span class="cnt">'+esc(x.c)+'</span>'},
  {k:'posts',l:'PTPs',n:1},
  {k:'mon',l:'Months reported',n:1,tt:'Distinct post-months reported for this UC over '+PTP.win},
  {k:'zd',l:'Zero-dose found',n:1,tt:'Reports, not distinct children'},
  {k:'cbu',l:'CB under-10',n:1,tt:'Cross-border under-10 children counted, both directions'},
  {k:'map',l:'On UC map',sv:x=>-x.map,f:x=>x.map?'<span class="tag t-high">Yes</span>':'<span class="cnt">\u2013</span>'},
  {k:'zr',l:'Campaign reported',n:1,f:x=>x.zr==null?'<span class="cnt">\u2013</span>':fmt(x.zr)},
  {k:'zc',l:'Campaign covered',n:1,f:x=>x.zc==null?'<span class="cnt">\u2013</span>':fmt(x.zc)},
  {k:'zp',l:'Covered %',n:1,f:x=>cc(x.zp,80,50)},
  {k:'ep',l:'OPV-3 %',n:1,f:x=>pE(x.ep)}],
  UT,'zd',-1);
 el('cntPTu').textContent=fmt(UR.length)+' UCs \u00b7 top '+fmt(UT.length)+' shown \u00b7 '+PTP.win;
 el('capPTu').textContent='Union councils the PTP panel reports, ranked by zero-dose children found over the whole '
  +PTP.win+' window. This table is the roster, so neither the year nor the month selector splits it: a UC is listed '
  +'once and its months and findings cover the window. '
  +fmt(UR.filter(x=>x.zr!=null).length)+' of them are in the '+esc(CAMP[LCP])+' zero-dose export and '+
  fmt(UR.filter(x=>x.ep!=null).length)+' carry a routine OPV-3 figure in the EPI file; a dash means that source has no row for the UC, '
  +'not that it found nothing. Post-level detail is not published: the export names each transit point and its location, '
  +'and those are left out on purpose.';
 el('btnPTu').onclick=()=>csvDownload('ptp_union_councils_'+_slug()+'.csv',
  ['Division','District','Tehsil','Union council','UC code','PTPs','Months reported','Zero-dose found',
   'Cross-border under-10','On UC map','Campaign reported ('+CAMP[LCP]+')','Campaign covered','Campaign covered %','OPV-3 %'],
  UR.map(x=>[x.dv,x.dn,x.t,x.u,x.c,x.posts,x.mon,x.zd,x.cbu,x.map?'Yes':'No',x.zr==null?'':x.zr,
   x.zc==null?'':x.zc,x.zp==null?'':p1(x.zp),x.ep==null?'':p1(x.ep)]));
}""".replace('\n', '\r\n')

MASTER = 'index.html'
A_CONST = 'const SURVW = '
A_MAIN = '</section>\r\n\r\n</main>'
A_NAV = '<button class="tab" data-tab="risk">'
A_TABS = ",'closed'], ZTABS="
A_DISP = 'closed:renderClosed,'
A_ICON = "erv:'map'};"
A_BADGE = 'atBadge();\r\n'
A_CSS = '#p-hx{--tc:#475569}'
A_FUNC = 'function renderSurv(){'
NAVBTN = ('<button class="tab" data-tab="ptp"><span class="tl">Permanent Transit Points</span>'
          '<span class="badge" id="bPT">\u2013</span></button>\r\n   ')
TABADD = ",'ptp'], ZTABS="
DISPADD = 'closed:renderClosed,ptp:renderPTP,'
ICONADD = "erv:'map',ptp:'map'};"
BADGEADD = 'atBadge(); ptBadge();\r\n'
CSSADD = '#p-hx{--tc:#475569}.tab[data-tab="ptp"],#p-ptp{--tc:#0e7490}'


def patch(v, js):
    t = v.text
    for a in (A_CONST, A_MAIN, A_NAV, A_TABS, A_DISP, A_ICON, A_BADGE, A_CSS, A_FUNC):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1): %r' % (t.count(a), a[:48]))
    t = t.replace(A_CONST, 'const PTP = %s;\r\n' % js + A_CONST)
    t = t.replace(A_MAIN, '</section>\r\n\r\n' + HTML + '</main>')
    t = t.replace(A_NAV, NAVBTN + A_NAV)
    t = t.replace(A_TABS, TABADD)
    t = t.replace(A_DISP, DISPADD)
    t = t.replace(A_ICON, ICONADD)
    t = t.replace(A_BADGE, BADGEADD)
    t = t.replace(A_CSS, CSSADD)
    t = t.replace(A_FUNC, JS + '\r\n' + A_FUNC)
    v.text = t
    v.changes.append('PTP block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for needle in ('const PTP = {', 'id="p-ptp"', 'id="fPTY"', 'id="fPTM"', 'Reporting period',
                   'id="kPT"', 'id="pt1"', 'id="pt2"',
                   'id="pt3"', 'id="pt4"', 'id="tPTa"', 'id="tPTb"', 'id="tPTu"',
                   '<button class="tab" data-tab="ptp">', 'function renderPTP(){', 'function ptBadge(){',
                   'function ptpMonths(){', "MON.a[i][j*12+mv-1]", 'k:\'ucS\'',
                   'ptBadge();', 'ptp:renderPTP,', "ptp:'map'", "'ptp'], ZTABS="):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    v.require(t.count("CKEY('pt") == 4, 'expected 4 chart colour keys, found %d' % t.count("CKEY('pt"))
    v.require(t.count('csvDownload(') > 3, 'expected the three PTP downloads to be present')
    v.require(t.count('id="fPTY"') == 1 and t.count('_MON[mv-1]') > 2,
              'the period control lost its month selector')
    v.require(t.count('MSL.disabled=!one;') == 1 and t.count('Pick a year first') == 1,
              'the month picker no longer cascades off the selected year')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_ptp.py first' % PAYLOAD)
    js = srcutil.read_text(PAYLOAD).strip()
    json.loads(js)                      # the payload must be valid JSON before it is embedded
    if '\n' in js or '\r' in js:
        raise SystemExit('ptp.json must be a single line for the <script> embed')
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'const PTP = ' in v.text:
        raise SystemExit('%s already has a PTP const - not patching twice' % v.rel)
    patch(v, js)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK ptp-ui master only - preview / public / internal builds pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
