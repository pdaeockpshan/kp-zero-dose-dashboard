"""EPI coverage tab: year coverage, dose numbers (district / UC) and a custom month/year download.

Three additions to the p-eov pane, all reading payloads that are already proved:

  * const EPIUC  - UC x month dose counts for Jan-Dec 2025, built by extract_epi_ucm.py and
                   anchored to the embedded EPI rows (extract_epi_ucm.py re-adds every district
                   month back to EPIM before it will write the file).
  * "Antigen coverage by year" - 2024 / 2025 / 2026 YTD coverage for every antigen, with the
    year's dose count under each percentage. 2024-2025 come from EPIM (district months); 2026
    is the EPI year-to-date payload, never a sum of the 2026 monthly archive.
  * "Doses given" - absolute doses for the selected EPI month (or year to date) at district
    or UC grain. UC numbers exist only for the months EPIUC carries (2025) and for the 2026
    year to date; the card says so instead of showing a district number under a UC heading.
  * "Download antigen coverage" - any mix of months and the 2026 YTD chip, district or UC,
    doses and coverage % for all 19 antigens, written as a formatted Excel sheet with its own
    Read-me (CSV fallback when ExcelJS cannot load or the selection is too big for the browser).

Every new table also gets its own formatted Excel download. Master only: the other three
variants follow push_master.py, which needs the owner's word.

  python _refresh/patch_epi_numbers_ui.py [--dry-run]
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

PAYLOAD = os.path.join(srcutil.OUT, 'epi_ucm.json')

A_CONST = 'const EMETA = {'
A_JS = "const matchEM=r=>(!fDiv.value||r.dv===fDiv.value)&&((r.ds||[]).some(d=>dOK(d)));\r\n"
A_RENDER = ("slice(0,1500),'p_'+a.k,1);}\r\n}\r\n"
            '// ---------- EPI-MIS dropout report (district level, published as reported) ----------')
A_TEG_CARD = ('<div class="cap">Coverage % = doses given ÷ target for Jan 2026 – Sep 2026 '
              '(newborns for BCG and OPV-0, surviving infants for the rest). Over 100% usually '
              'means the target is set too low or children from other areas were vaccinated here. '
              'Dropout = share of children who got the first dose but not the later one.</div>\r\n'
              '</div>\r\n'
              '<div class="card" style="margin-bottom:16px">\r\n'
              '<div class="tblhdr"><h3 style="margin:0">Dropout report by district (as published)</h3>')
A_EU_CARD = ('<div class="cap">One row per EPI-MIS union council. "Polio UC" shows whether the UC '
             'was matched to the polio UC list (used for the comparison with zero-dose data). '
             'Click a column header to sort.</div>\r\n</div>\r\n</section>')

CARDS = """<div class="card" style="margin-bottom:16px">
<div class="tblhdr"><h3 style="margin:0">Antigen coverage by year</h3><div style="display:flex;gap:10px;align-items:center"><span class="cnt">2024 · 2025 · 2026 year to date</span><button class="btn" id="btnEYxls">Download (Excel)</button></div></div>
<div class="scroll" style="max-height:520px"><table id="tEY"></table></div>
<div class="cap" id="capeY"></div>
</div>
<div class="card" style="margin-bottom:16px">
<div class="tblhdr"><h3 style="margin:0">Doses given — numbers by district and UC</h3><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><div class="pills" id="eNpills"><button class="btn on" data-g="d">District</button><button class="btn" data-g="u">UC</button></div><span class="cnt" id="cntEN"></span><button class="btn" id="btnENxls">Download (Excel)</button></div></div>
<div class="scroll" style="max-height:520px"><table id="tEN"></table></div>
<div class="cap" id="capEN"></div>
</div>
"""

EXPORT_CARD = """<div class="card">
<div class="tblhdr"><h3 style="margin:0">Download antigen coverage — pick the months</h3><span class="cnt" id="cntEX"></span></div>
<div class="note">Tick any month, a whole year, or the <b>YTD</b> chip. Every download carries <b>doses and coverage %</b> for all 19 antigens. District rows cover 2024–2026; UC rows cover <b>Jan–Dec 2025</b> and the <b>2026 year to date</b>, because the 2024 exports are district-level and the 2026 report exists only as year to date.</div>
<div id="exMonths"></div>
<div class="nbar" id="exGrain" style="margin:6px 0"><span class="cnt">Rows:</span><button class="btn on" data-g="d">District</button><button class="btn" data-g="u">UC</button><span class="cnt">UC rows are skipped for periods that have no UC export</span></div>
<div class="nbar" style="margin:6px 0"><button class="btn" id="btnEXxls">Download Excel</button><button class="btn" id="btnEXcsv">Download CSV</button></div>
<div class="cap">Coverage % = doses ÷ target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses). The <b>Sep 2026</b> month is the archived part-report (about 65% of a normal month) and the <b>YTD</b> chip carries the complete Jan–Sep 2026 figures — do not add the two together. The browser Excel writer handles about 250,000 cells; larger selections come out as CSV.</div>
</div>
"""

JS1 = r"""// ---------- EPI: year coverage, dose numbers (district / UC) and custom downloads ----------
const EUCM=(typeof EPIUC!=='undefined')?EPIUC:null;
const EUCOK=!!EUCM&&!!EUCM.rows&&EUCM.rows.length===EPI.length;
const EUCI=EUCM?Object.fromEntries(EUCM.k.map((k,i)=>[k,i])):{};
const eucMi=mo=>EUCM?EUCM.mo.findIndex(m=>m.mo===mo):-1;
const eucRow=(r,i,mi)=>{const o={...r};if(EUCOK&&mi>=0){const w=EUCM.rows[i];EUCM.k.forEach((k,j)=>{o[k]=w[j][mi];});}return o;};
const eDim='<span style="color:var(--color-text-muted)">–</span>';
let EN='d', EYD=[];
const enNum=(k,l)=>({k,l,n:1,f:r=>r[k]==null?eDim:fmt(r[k])});
const enRows=()=>{
 if(EN==='u'){
  if(!EM)return cur;
  const mi=eucMi(EM);
  return mi<0?null:EPI.map((r,i)=>eucRow(r,i,mi)).filter(matchE);
 }
 return EM?groupE(EPIM.filter(r=>r.mo===EM&&matchEM(r)),'ed'):groupE(cur,'ed');
};
function renderEN(){
 el('eNpills').querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.g===EN));
 const rows=enRows(), cap=el('capEN'), btn=el('btnENxls');
 if(rows==null){
  el('tEN').innerHTML='<tr><td class="empty">No UC-level numbers for '+esc(emLab(EM))+' — the 2024 exports are district-level and the 2026 report is year to date only. Switch to <b>District</b>, pick a 2025 month, or set <b>EPI month</b> to Year to date.</td></tr>';
  el('cntEN').textContent='UC numbers unavailable for this month';
  btn.disabled=true;
  cap.textContent='UC doses exist for Jan–Dec 2025 (UC-wise monthly exports) and for the 2026 year to date.';
  return;
 }
 btn.disabled=false;
 const dc=EAG.map(a=>({k:a.k,l:a.l,n:1,tt:'Coverage basis: '+(a.t==='n'?'newborns':'surviving infants'),f:r=>r[a.k]==null?eDim:fmt(r[a.k])}));
 const cols=EN==='d'
  ?[{k:'k',l:'District',f:r=>dz(r.k)},{k:'dv',l:'Division'},enNum('n','Newborns'),enNum('s','Surviving infants'),...dc]
  :[{k:'d',l:'District',f:r=>dz(r.d)},{k:'t',l:'Tehsil'},{k:'en',l:'UC (EPI-MIS)'},{k:'ec',l:'Code'},enNum('n','Newborns'),enNum('s','Surviving infants'),...dc];
 drawTable('tEN',cols,rows,EN==='d'?'k':'d',1);
 el('cntEN').textContent=fmt(rows.length)+(EN==='d'?' districts':' UCs')+' · '+(EM?emLab(EM):EPER);
 if(EN==='u'){
  cap.textContent='Doses given by each UC for '+(EM?emLab(EM):EPER)+', from the UC-wise '+(EM?'single-month':'year-to-date')+' export.';
 }else{
  cap.textContent='Doses given in each district for '+(EM?emLab(EM):EPER)+', from the '+(EM?'district-level single-month':'UC-wise year-to-date')+' EPI-MIS export.';
  if(EM&&EM.slice(0,4)==='2026')cap.textContent+=' The 2026 monthly archive carries only the eleven core doses, so the other doses show –.';
 }
}
function enExport(){
 const rows=enRows();
 if(rows==null||!rows.length){toast('Nothing to download for this selection');return;}
 const per=EM?emLab(EM):EPER;
 const H=['Period','Grain','Division','District','Tehsil','UC (EPI-MIS)','EPI-MIS code','Target newborns','Target surviving infants',...EAG.flatMap(a=>[a.l+' doses',a.l+' %'])];
 const data=rows.map(r=>EN==='d'
  ?[per,'District',r.dv,r.k,'','','',r.n,r.s,...EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)])]
  :[per,'UC',r.dv,r.d,r.t,r.en,r.ec,r.n,r.s,...EAG.flatMap(a=>{const p=eP(r,a.k);return [r[a.k]==null?'':r[a.k],p==null?'':+p.toFixed(1)];})]);
 xlsxDownload('EPI_Doses_by_'+(EN==='d'?'District':'UC')+'_'+_slug()+'.csv',H,data);
}
"""
JS2 = r"""function renderEY(){
 const a24=aggE(EPIM.filter(r=>r.mo.slice(0,4)==='2024'&&matchEM(r)));
 const a25=aggE(EPIM.filter(r=>r.mo.slice(0,4)==='2025'&&matchEM(r)));
 const a26=aggE(cur);
 const cell=(p,d)=>(p==null&&d==null)?eDim:'<b style="color:'+colE(p)+'">'+(p==null?'–':pc(p))+'</b><div style="font-size:10.5px;color:var(--color-text-muted)">'+(d==null?'–':fmt(d)+' doses')+'</div>';
 EYD=EAG.map((a,i)=>{const y24=a24['p_'+a.k],y25=a25['p_'+a.k],y26=a26['p_'+a.k];
  return {o:i+1,k:a.k,l:a.l,y24,y25,y26,d24:a24[a.k],d25:a25[a.k],d26:a26[a.k],dl:(y25!=null&&y26!=null)?y26-y25:null};});
 drawTable('tEY',[{k:'o',l:'#',n:1,f:r=>r.o},{k:'l',l:'Antigen',f:r=>'<b>'+esc(r.l)+'</b>'},
  {k:'y24',l:'2024',n:1,sv:r=>r.y24==null?-1:r.y24,f:r=>cell(r.y24,r.d24)},
  {k:'y25',l:'2025',n:1,sv:r=>r.y25==null?-1:r.y25,f:r=>cell(r.y25,r.d25)},
  {k:'y26',l:'2026 YTD',n:1,tt:'Jan – Sep 2026',sv:r=>r.y26==null?-1:r.y26,f:r=>cell(r.y26,r.d26)},
  {k:'dl',l:'Δ 2025→26',n:1,tt:'Change in coverage from 2025 to Jan–Sep 2026, in percentage points',sv:r=>r.dl==null?-999:r.dl,f:r=>r.dl==null?'–':'<span style="color:'+(r.dl>=0?C.high:C.crit)+'">'+sgn(r.dl,1)+' pts</span>'}],EYD,'o',1);
 el('capeY').textContent='Coverage % = doses ÷ target for each year’s months. 2024 and 2025 are the monthly EPI-MIS exports added up (2024 published district by district, 2025 UC by UC); 2026 is the Jan – Sep year to date from the UC-wise export. Doses sit under each percentage.'+((fTeh.value||q.value.trim())?' The tehsil/UC filters do not apply to 2024–2025: those exports are district-level.':'');
}
function eyExport(){
 const H=['#','Antigen','2024 coverage %','2024 doses','2025 coverage %','2025 doses','2026 YTD coverage %','2026 YTD doses','Change 2025 to 2026 (pts)'];
 const data=EYD.map(r=>[r.o,r.l,r.y24==null?'':+r.y24.toFixed(1),r.d24==null?'':r.d24,r.y25==null?'':+r.y25.toFixed(1),r.d25==null?'':r.d25,r.y26==null?'':+r.y26.toFixed(1),r.d26==null?'':r.d26,r.dl==null?'':+r.dl.toFixed(1)]);
 xlsxDownload('EPI_Antigen_Coverage_by_Year_'+_slug()+'.csv',H,data);
}
const EXS=new Set(['YTD']); let EXG='d';
const exYears=[2024,2025,2026];
const exPeriods=()=>{const ps=[...EXS].filter(x=>x!=='YTD').sort().map(mo=>({mo,lab:emLab(mo),type:'Month'}));if(EXS.has('YTD'))ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date'});return ps;};
function renderEX(){
 const ms=eMonths();
 el('exMonths').innerHTML=exYears.map(y=>{
  const list=ms.filter(m=>m.mo.slice(0,4)===''+y); if(!list.length)return '';
  const all=list.every(m=>EXS.has(m.mo));
  return '<div class="nbar" style="margin:4px 0"><b style="min-width:42px">'+y+'</b><button class="btn'+(all?' on':'')+'" data-y="'+y+'">'+(all?'Clear':'All')+' '+y+'</button>'+
   list.map(m=>'<button class="btn'+(EXS.has(m.mo)?' on':'')+'" data-mo="'+m.mo+'" title="'+esc(m.l)+(m.pt?' · part-report (about '+(m.rp||'?')+'% of a normal month)':'')+'">'+esc(m.l.slice(0,3))+(m.pt?'*':'')+'</button>').join('')+
   (y===2026?'<button class="btn'+(EXS.has('YTD')?' on':'')+'" data-mo="YTD" title="Jan – Sep 2026 year to date (the complete nine months)">YTD</button>':'')+'</div>';
 }).join('');
 el('exMonths').querySelectorAll('button[data-mo]').forEach(b=>b.onclick=()=>{const k=b.dataset.mo;if(EXS.has(k))EXS.delete(k);else EXS.add(k);renderEX();});
 el('exMonths').querySelectorAll('button[data-y]').forEach(b=>b.onclick=()=>{const list=ms.filter(m=>m.mo.slice(0,4)===b.dataset.y).map(m=>m.mo),all=list.every(m=>EXS.has(m.mo));list.forEach(m=>{if(all)EXS.delete(m);else EXS.add(m);});renderEX();});
 el('exGrain').querySelectorAll('button[data-g]').forEach(b=>{b.classList.toggle('on',b.dataset.g===EXG);b.onclick=()=>{EXG=b.dataset.g;renderEX();};});
 const n=EXS.size;
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' selected · '+(EXG==='d'?'district rows':'UC rows'):'Nothing selected';
}
"""
JS3 = r"""function exData(ps){
 const H=['Period','Period type','Grain and source','Division','District','Tehsil','UC (EPI-MIS)','EPI-MIS code','Target newborns','Target surviving infants',...EAG.flatMap(a=>[a.l+' doses',a.l+' %'])];
 const data=[],skip=[];
 ps.forEach(p=>{
  if(EXG==='d'){
   const rs=p.mo?groupE(EPIM.filter(r=>r.mo===p.mo&&matchEM(r)),'ed'):groupE(cur,'ed');
   rs.forEach(r=>data.push([p.lab,p.type,'District · EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.k,'','',r.n,r.s,...EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)])]));
  }else{
   let rs=null;
   if(!p.mo)rs=cur;
   else{const mi=eucMi(p.mo);if(mi>=0)rs=EPI.map((r,i)=>eucRow(r,i,mi)).filter(matchE);}
   if(!rs){skip.push(p.lab);return;}
   rs.forEach(r=>data.push([p.lab,p.type,'UC · EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.d,r.t,r.en,r.ec,r.n,r.s,...EAG.flatMap(a=>{const q=eP(r,a.k);return [r[a.k]==null?'':r[a.k],q==null?'':+q.toFixed(1)];})]));
  }
 });
 return {H,data,skip};
}
const exStem=ps=>{
 const ms=ps.filter(p=>p.type==='Month').map(p=>p.mo); let s;
 if(!ms.length)s='2026_YTD';
 else if(ms.length===1)s=ms[0];
 else if(ms.length===12&&new Set(ms.map(m=>m.slice(0,4))).size===1)s=ms[0].slice(0,4);
 else s=ms[0]+'_'+ms.length+'months';
 if(ps.some(p=>p.type!=='Month')&&ms.length)s+='_plus_YTD';
 return s;
};
function exBook(file,H,data,ps,skip){
 return xlLib().then(X=>{
  const wb=new X.Workbook();wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title='EPI coverage';
  const ws=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
  ws.getColumn(1).width=30;ws.getColumn(2).width=110;
  const add=(a,b)=>{const r=ws.addRow([a,String(b==null?'':b)]);r.getCell(1).font={bold:true};r.alignment={vertical:'top',wrapText:true};};
  add('Workbook','EPI-MIS antigen coverage and dose numbers from the EPI routine coverage tab of the KP Polio and Synergy Dashboard.');
  add('Periods',ps.map(p=>p.lab).join(' · '));
  add('Rows',EXG==='d'?'One row per district and period':'One row per EPI-MIS union council and period');
  add('Division / district filter',_slug().replace(/_/g,' '));
  add('Sources','2024: district-level single-month EPI-MIS exports · 2025: UC-wise single-month exports · 2026: UC-wise year-to-date export (Jan – Sep).');
  add('Coverage %','Doses given ÷ target for the same period. BCG and OPV-0 use newborns; the other 17 doses use surviving infants.');
  add('Sep 2026','The Sep 2026 month is the archived part-report (about 65% of a normal month). The year-to-date row carries the complete Jan – Sep 2026 figures — do not add the two together.');
  add('Blank cells','A blank dose or % means that export does not publish the figure. The 2026 monthly archive carries only the eleven core doses.');
  if(skip.length)add('Not available at UC grain',skip.join(' · ')+'. The 2024 exports are district-level and the 2026 report is year to date only.');
  add('Made',new Date().toLocaleString());
  xlSheet(wb,{sheet:'Coverage data',H,rows:data});
  return wb.xlsx.writeBuffer();
 }).then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();});
}
function exDownload(xls){
 const ps=exPeriods();
 if(!ps.length){toast('Pick at least one month or the YTD chip');return;}
 const r=exData(ps);
 if(!r.data.length){toast('No rows exist for that selection'+(r.skip.length?' — '+r.skip.join(', ')+' have no UC data':''));return;}
 const stem='EPI_Coverage_'+exStem(ps)+'_by_'+(EXG==='d'?'District':'UC')+'_'+_slug();
 const cells=r.data.length*r.H.length;
 if(xls&&cells<=250000){toast('Building Excel…');
  exBook(stem+'.xlsx',r.H,r.data,ps,r.skip).then(()=>toast('Excel downloaded ('+fmt(r.data.length)+' rows)'))
   .catch(()=>{csvRaw(stem+'.csv',r.H,r.data);toast('Excel library did not load, so the same table went out as CSV');});
 }else{
  csvRaw(stem+'.csv',r.H,r.data);
  if(xls)toast('That selection is too large for the browser Excel writer ('+fmt(cells)+' cells) — CSV downloaded instead');
 }
}
el('eNpills').querySelectorAll('button').forEach(b=>b.onclick=()=>{EN=b.dataset.g;renderEN();});
el('btnENxls').onclick=enExport;
el('btnEYxls').onclick=eyExport;
el('btnEXxls').onclick=()=>exDownload(1);
el('btnEXcsv').onclick=()=>exDownload(0);
"""
JS = JS1 + JS2 + JS3
TEXT = [
    ('In the month view the extra doses exist only for the 2024 and 2025 monthly exports.',
     'In the month view the extra doses exist only for the 2024 and 2025 monthly exports — '
     '2025 is UC-level, 2024 district-level — and the year table below adds each year up.'),
    ("'Month view uses district-level EPI-MIS monthly data (division and district filters apply); "
     "UC-level tables stay on the year-to-date.'",
     "'Month view uses district-level EPI-MIS monthly data (division and district filters apply). "
     "UC doses exist for Jan–Dec 2025 and the 2026 year to date; the All UCs coverage table stays "
     "year-to-date.'"),
    ("'Monthly charts use district-level EPI-MIS data; UC-level tables are year-to-date.'",
     "'Monthly charts use district-level EPI-MIS data; UC doses exist for Jan–Dec 2025 and the "
     "2026 year to date.'"),
    ("only — district-level EPI-MIS monthly data. The UC table below and the Priority UCs page "
     "remain year-to-date.",
     "only — district-level EPI-MIS monthly data. The All UCs table and the Priority UCs page "
     "remain year-to-date; the doses table below has UC numbers for 2025 months."),
    ("' · month view (UC tables YTD)'", "' · month view (UC coverage table is YTD)'"),
]

T_OLD = ("if(EM){el('tEU').innerHTML='<tr><td class=\"empty\">UC-level detail is year-to-date — set "
         "<b>EPI month</b> to “Year to date” to view it.</td></tr>';el('cntEU').textContent='UC "
         "detail: set EPI month to Year to date';el('btnEUCSV').disabled=true;el('btnEUCSV').title="
         "'Set EPI month to Year to date to download UC-level data';}")
T_NEW = ("if(EM){const nu=eucMi(EM)>=0;el('tEU').innerHTML='<tr><td class=\"empty\">'+(nu?"
         "'UC coverage here stays year-to-date — the <b>doses table</b> above has this month at UC "
         "level.':'No UC-level detail exists for '+esc(emLab(EM))+' — the 2024 exports are "
         "district-level and the 2026 report is year to date only. Use the <b>doses table</b> for "
         "district numbers, or set <b>EPI month</b> to Year to date.')+'</td></tr>';"
         "el('cntEU').textContent=nu?'UC coverage: year to date':'UC detail unavailable for this "
         "month';el('btnEUCSV').disabled=true;el('btnEUCSV').title='Set EPI month to Year to date to "
         "download UC coverage';}")


def crlf(s):
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    return s.replace('\n', '\r\n')


# Corrections found while verifying the page against the exports:
#  - the district numbers caption claimed a district-level monthly export for 2025,
#    which is the UC-wise file added up to district;
#  - the 250k-cell cap kept a full UC-year (12 x 1,459 rows) off the Excel writer;
#  - the year chip's clear test ran EXS.has() on month ids from a mapped array,
#    so "Clear 2025" only ever added.
FIXES = [
    ("cap.textContent='Doses given in each district for '+(EM?emLab(EM):EPER)+"
     "', from the '+(EM?'district-level single-month':'UC-wise year-to-date')"
     "+' EPI-MIS export.';",
     "cap.textContent='Doses given in each district for '+(EM?emLab(EM):EPER)+"
     "', from '+(!EM?'the UC-wise year-to-date export':(EM.slice(0,4)==='2024'?"
     "'the district-level single-month export':(EM.slice(0,4)==='2025'?"
     "'the UC-wise single-month exports added up to district'"
     ":'the 2026 monthly archive')))+'.';"),
    ('if(xls&&cells<=250000){', 'if(xls&&cells<=1000000){'),
    ('The browser Excel writer handles about 250,000 cells; larger selections come out as CSV.',
     'The browser Excel writer handles about a million cells, so a full UC-year fits; '
     'larger selections come out as CSV.'),
    ('.map(m=>m.mo),all=list.every(m=>EXS.has(m.mo));',
     '.map(m=>m.mo),all=list.every(m=>EXS.has(m));'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    lit = srcutil.read_text(PAYLOAD).strip()
    json.loads(lit.replace('<\\/', '</'))
    print('payload: %s chars from %s' % (format(len(lit), ','), os.path.basename(PAYLOAD)))

    cfg, vs = dashpatch.load_variants()
    v = vs[0]
    v.require('const EPIUC = ' not in v.text, 'const EPIUC is already in %s' % v.rel)
    v.require(v.text.count(A_CONST) == 1, 'const EMETA anchor found %d times' % v.text.count(A_CONST))
    v.require(v.text.count(A_JS) == 1, 'matchEM anchor found %d times' % v.text.count(A_JS))
    v.require(v.text.count(A_RENDER) == 1, 'renderEOv tail found %d times' % v.text.count(A_RENDER))
    v.require(v.text.count(A_TEG_CARD) == 1, 'tEG card tail found %d times' % v.text.count(A_TEG_CARD))
    v.require(v.text.count(A_EU_CARD) == 1, 'All UCs card tail found %d times' % v.text.count(A_EU_CARD))
    for old, _ in TEXT:
        v.require(v.text.count(old) == 1, 'text anchor found %d times: %s' % (v.text.count(old), old[:60]))
    v.require(v.text.count(T_OLD) == 1, 'month-mode tEU message found %d times' % v.text.count(T_OLD))

    i = v.text.index(A_CONST)
    v.text = v.text[:i] + 'const EPIUC = ' + lit + ';\r\n' + v.text[i:]
    v.changes.append('const EPIUC %s chars' % format(len(lit), ','))

    v.text = v.text.replace(A_TEG_CARD, A_TEG_CARD.replace(
        '\r\n<div class="card" style="margin-bottom:16px">\r\n<div class="tblhdr"><h3 style="margin:0">Dropout',
        '\r\n' + crlf(CARDS) + '<div class="card" style="margin-bottom:16px">\r\n<div class="tblhdr"><h3 style="margin:0">Dropout'))
    v.changes.append('cards: coverage by year + doses by district/UC')

    v.text = v.text.replace(A_EU_CARD, A_EU_CARD.replace(
        '\r\n</section>', '\r\n' + crlf(EXPORT_CARD) + '</section>'))
    v.changes.append('card: custom month/year download')

    v.text = v.text.replace(A_JS, A_JS + crlf(JS) + '\r\n')
    v.changes.append('JS: renderEY / renderEN / renderEX + Excel writers')

    v.text = v.text.replace(A_RENDER, A_RENDER.replace(
        '\r\n}\r\n', '\r\n renderEY();\r\n renderEN();\r\n renderEX();\r\n}\r\n'))
    v.changes.append('renderEOv: renderEY / renderEN / renderEX')

    for old, new in TEXT:
        v.text = v.text.replace(old, new)
    v.changes.append('text: %d EPI notes' % len(TEXT))
    v.text = v.text.replace(T_OLD, T_NEW)
    v.changes.append('text: month-mode UC coverage message')

    for old, new in FIXES:
        if old in v.text:
            v.text = v.text.replace(old, new, 1)
            v.changes.append('fix: %s' % new[:52])
    dashpatch.assert_crlf(v)
    print('master %s: %s chars (%+d)' % (v.rel, format(len(v.text), ','), v.delta()))
    for c in v.changes:
        print('  - %s' % c)
    if a.dry_run:
        print('dry run - nothing written')
        return
    dashpatch.write_variants([v])
    print('OK wrote %s - the other three variants are synced by push_master.py, '
          'which needs the owner\'s word' % v.rel)


if __name__ == '__main__':
    main()
