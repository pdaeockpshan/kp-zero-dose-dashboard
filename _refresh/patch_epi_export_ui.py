"""Rebuild "Download antigen coverage" as year / months / grain dropdowns (master only).

The chip strip meant every month of every year sat on the card at once, and a download
combined all ticked months into one block of rows. This replaces the chips with a year
select, a multi-month select and a Division / District / UC select, and writes one
worksheet per selected month so a multi-month file is month by month rather than one
stack. index.html is the master; push_master.py derives the other three variants.
Idempotent: a block already carrying its new text is skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CARD_OLD = '''<div class="tblhdr"><h3 style="margin:0">Download antigen coverage \u2014 pick the months</h3><span class="cnt" id="cntEX"></span></div>
<div class="note">Tick any month, a whole year, or the <b>YTD</b> chip. Every download carries <b>doses and coverage %</b> for all 19 antigens. District rows cover 2023\u20132026; UC rows cover <b>Jan\u2013Dec 2023</b>, <b>Jan\u2013Dec 2025</b> and the <b>2026 year to date</b> \u2014 2024 is district-level only and 2026 has no single-month UC export, so UC rows are skipped for those periods.</div>
<div id="exMonths"></div>
<div class="nbar" id="exGrain" style="margin:6px 0"><span class="cnt">Rows:</span><button class="btn on" data-g="d">District</button><button class="btn" data-g="u">UC</button><span class="cnt">UC rows are skipped for periods that have no UC export</span></div>
<div class="nbar" style="margin:6px 0"><button class="btn" id="btnEXxls">Download Excel</button><button class="btn" id="btnEXcsv">Download CSV</button></div>
<div class="cap">Coverage % = doses \u00f7 target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses). The <b>Sep 2026</b> month is the archived part-report (about 65% of a normal month) and the <b>YTD</b> chip carries the complete Jan\u2013Sep 2026 figures \u2014 do not add the two together. The browser Excel writer handles about a million cells, so a full UC-year fits; larger selections come out as CSV.</div>'''

CARD_NEW = '''<div class="tblhdr"><h3 style="margin:0">Download antigen coverage \u2014 pick year, months and rows</h3><span class="cnt" id="cntEX"></span></div>
<div class="note">Choose the <b>year</b>, the <b>months</b> (Ctrl/\u2318-click for more than one, or <b>All months</b>) and the row grain \u2014 <b>Division</b>, <b>District</b> or <b>UC</b>. Each selected month is written as its own sheet in the Excel file and its own block of rows, so months are never added together. District rows cover 2023\u20132026; UC rows cover <b>Jan\u2013Dec 2023</b>, <b>Jan\u2013Dec 2025</b> and the <b>2026 year to date</b> \u2014 2024 is district-level only and 2026 has no single-month UC export, so UC rows are skipped for those periods.</div>
<div class="nbar" style="margin:6px 0;align-items:flex-end;flex-wrap:wrap">
<span><span class="cnt" style="display:block">Year</span><select id="exYear" aria-label="Download year" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">Months</span><select id="exMonthsSel" multiple aria-label="Download months" style="font:13px var(--font-sans);padding:4px 6px;border:1px solid var(--color-border);border-radius:8px;background:#fff;min-width:210px;vertical-align:top"></select></span>
<span><button class="btn" id="exAll">All months</button> <button class="btn" id="exNone">Clear</button></span>
<span><span class="cnt" style="display:block">Rows</span><select id="exGrainSel" aria-label="Download grain" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"><option value="dv">Division</option><option value="d">District</option><option value="u">UC</option></select></span>
</div>
<div class="nbar" style="margin:6px 0"><button class="btn" id="btnEXxls">Download Excel</button><button class="btn" id="btnEXcsv">Download CSV</button><span class="cnt">Excel: one sheet per month \u00b7 CSV: the months stacked as rows</span></div>
<div class="cap">Coverage % = doses \u00f7 target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses). A <b>Division</b> row re-adds its districts for that month; it does not average their rates. The <b>Sep 2026</b> month is the archived part-report (about 65% of a normal month) and <b>Year to date</b> carries the complete Jan\u2013Sep 2026 figures \u2014 do not add the two together. The browser Excel writer handles about a million cells, so a full UC-year fits; larger selections come out as CSV.</div>'''

# the month listbox is nine rows tall when a year is picked, so leaving it in the same flex row
# as the other controls bottom-aligns them under a column of dead space; split it onto its own row
LAYOUT_OLD = '''<div class="nbar" style="margin:6px 0;align-items:flex-end;flex-wrap:wrap">
<span><span class="cnt" style="display:block">Year</span><select id="exYear" aria-label="Download year" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">Months</span><select id="exMonthsSel" multiple aria-label="Download months" style="font:13px var(--font-sans);padding:4px 6px;border:1px solid var(--color-border);border-radius:8px;background:#fff;min-width:210px;vertical-align:top"></select></span>
<span><button class="btn" id="exAll">All months</button> <button class="btn" id="exNone">Clear</button></span>
<span><span class="cnt" style="display:block">Rows</span><select id="exGrainSel" aria-label="Download grain" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"><option value="dv">Division</option><option value="d">District</option><option value="u">UC</option></select></span>
</div>'''

LAYOUT_NEW = '''<div class="nbar" style="margin:6px 0;align-items:flex-end">
<span><span class="cnt" style="display:block">Year</span><select id="exYear" aria-label="Download year" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">Rows</span><select id="exGrainSel" aria-label="Download grain" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"><option value="dv">Division</option><option value="d">District</option><option value="u">UC</option></select></span>
<span><button class="btn" id="exAll">All months</button> <button class="btn" id="exNone">Clear</button></span>
</div>
<div style="margin:6px 0 2px"><span class="cnt" style="display:block;margin-bottom:3px">Months</span>
<select id="exMonthsSel" multiple aria-label="Download months" style="font:13px var(--font-sans);padding:4px 6px;border:1px solid var(--color-border);border-radius:8px;background:#fff;width:100%;max-width:440px;vertical-align:top"></select></div>'''

# states that legitimately replace an earlier fix's result, so a re-run skips instead of aborting
SUPERSEDED = [LAYOUT_NEW]

STATE_OLD = "const EXS=new Set(['YTD']); let EXG='d';"

STATE_NEW = '''const EXG_L={dv:'Division',d:'District',u:'UC'};
const EXP={2023:new Set(),2024:new Set(),2025:new Set(),2026:new Set(['YTD'])};
let EXY=2026, EXG='d';
const exSel=()=>EXP[EXY];'''

PERIODS_OLD = "const exPeriods=()=>{const ps=[...EXS].filter(x=>x!=='YTD').sort().map(mo=>({mo,lab:emLab(mo),type:'Month'}));if(EXS.has('YTD'))ps.push({mo:'',lab:'Jan\u2013Sep 2026',type:'Year to date'});return ps;};"

PERIODS_NEW = "const exPeriods=()=>{const S=exSel(),ps=[];eMonths().filter(m=>m.mo.slice(0,4)===''+EXY&&S.has(m.mo)).forEach(m=>ps.push({mo:m.mo,lab:emLab(m.mo),type:'Month'}));if(EXY===2026&&S.has('YTD'))ps.push({mo:'',lab:'Jan\u2013Sep 2026',type:'Year to date'});return ps;};"

RENDER_OLD = '''function renderEX(){
 const ms=eMonths();
 el('exMonths').innerHTML=exYears.map(y=>{
  const list=ms.filter(m=>m.mo.slice(0,4)===''+y); if(!list.length)return '';
  const all=list.every(m=>EXS.has(m.mo));
  return '<div class="nbar" style="margin:4px 0"><b style="min-width:42px">'+y+'</b><button class="btn'+(all?' on':'')+'" data-y="'+y+'">'+(all?'Clear':'All')+' '+y+'</button>'+
   list.map(m=>'<button class="btn'+(EXS.has(m.mo)?' on':'')+'" data-mo="'+m.mo+'" title="'+esc(m.l)+(m.pt?' \u00b7 part-report (about '+(m.rp||'?')+'% of a normal month)':'')+'">'+esc(m.l.slice(0,3))+(m.pt?'*':'')+'</button>').join('')+
   (y===2026?'<button class="btn'+(EXS.has('YTD')?' on':'')+'" data-mo="YTD" title="Jan \u2013 Sep 2026 year to date (the complete nine months)">YTD</button>':'')+'</div>';
 }).join('');
 el('exMonths').querySelectorAll('button[data-mo]').forEach(b=>b.onclick=()=>{const k=b.dataset.mo;if(EXS.has(k))EXS.delete(k);else EXS.add(k);renderEX();});
 el('exMonths').querySelectorAll('button[data-y]').forEach(b=>b.onclick=()=>{const list=ms.filter(m=>m.mo.slice(0,4)===b.dataset.y).map(m=>m.mo),all=list.every(m=>EXS.has(m));list.forEach(m=>{if(all)EXS.delete(m);else EXS.add(m);});renderEX();});
 el('exGrain').querySelectorAll('button[data-g]').forEach(b=>{b.classList.toggle('on',b.dataset.g===EXG);b.onclick=()=>{EXG=b.dataset.g;renderEX();};});
 const n=EXS.size;
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' selected \u00b7 '+(EXG==='d'?'district rows':'UC rows'):'Nothing selected';
}'''

RENDER_NEW = '''function renderEX(){
 const S=exSel(),ms=eMonths().filter(m=>m.mo.slice(0,4)===''+EXY),ys=el('exYear');
 if(!ys.options.length)ys.innerHTML=exYears.map(y=>'<option value="'+y+'">'+y+'</option>').join('');
 ys.value=''+EXY;
 const o=ms.map(m=>'<option value="'+esc(m.mo)+'"'+(S.has(m.mo)?' selected':'')+'>'+esc(m.l)+(m.pt?' *':'')+'</option>');
 if(EXY===2026)o.push('<option value="YTD"'+(S.has('YTD')?' selected':'')+'>Year to date (Jan\u2013Sep)</option>');
 const msel=el('exMonthsSel');msel.innerHTML=o.join('');msel.size=Math.min(Math.max(o.length,3),9);
 el('exGrainSel').value=EXG;
 const n=exPeriods().length;
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' \u00b7 '+EXG_L[EXG].toLowerCase()+' rows':'Nothing selected';
}'''

DATA_OLD = '''function exData(ps){
 const H=['Period','Period type','Grain and source','Division','District','Tehsil','UC (EPI-MIS)','EPI-MIS code','Target newborns','Target surviving infants',...EAG.flatMap(a=>[a.l+' doses',a.l+' %'])];
 const data=[],skip=[];
 ps.forEach(p=>{
  if(EXG==='d'){
   const rs=p.mo?groupE(EPIM.filter(r=>r.mo===p.mo&&matchEM(r)),'ed'):groupE(cur,'ed');
   rs.forEach(r=>data.push([p.lab,p.type,'District \u00b7 EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.k,'','','',r.n,r.s,...EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)])]));
  }else{
   let rs=null;
   if(!p.mo)rs=cur;
   else{const mi=eucMi(p.mo);if(mi>=0)rs=EPI.map((r,i)=>eucRow(r,i,mi)).filter(matchE);}
   if(!rs){skip.push(p.lab);return;}
   rs.forEach(r=>data.push([p.lab,p.type,'UC \u00b7 EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.d,r.t,r.en,r.ec,r.n,r.s,...EAG.flatMap(a=>{const q=eP(r,a.k);return [r[a.k]==null?'':r[a.k],q==null?'':+q.toFixed(1)];})]));
  }
 });
 return {H,data,skip};
}'''

DATA_NEW = '''function exData(ps){
 const H=['Period','Period type','Grain and source','Division','District','Tehsil','UC (EPI-MIS)','EPI-MIS code','Target newborns','Target surviving infants',...EAG.flatMap(a=>[a.l+' doses',a.l+' %'])];
 const blocks=[],skip=[];
 ps.forEach(p=>{
  const src=' \u00b7 EPI-MIS '+(p.mo?'single-month':'year to date'),rows=[];
  if(EXG==='dv'){
   const rs=p.mo?groupE(EPIM.filter(r=>r.mo===p.mo&&matchEM(r)),'dv'):groupE(cur,'dv');
   rs.forEach(r=>rows.push([p.lab,p.type,'Division'+src,r.k,'','','','',r.n,r.s,...EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)])]));
  }else if(EXG==='d'){
   const rs=p.mo?groupE(EPIM.filter(r=>r.mo===p.mo&&matchEM(r)),'ed'):groupE(cur,'ed');
   rs.forEach(r=>rows.push([p.lab,p.type,'District'+src,r.dv,r.k,'','','',r.n,r.s,...EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)])]));
  }else{
   let rs=null;
   if(!p.mo)rs=cur;
   else{const mi=eucMi(p.mo);if(mi>=0)rs=EPI.map((r,i)=>eucRow(r,i,mi)).filter(matchE);}
   if(!rs){skip.push(p.lab);return;}
   rs.forEach(r=>rows.push([p.lab,p.type,'UC'+src,r.dv,r.d,r.t,r.en,r.ec,r.n,r.s,...EAG.flatMap(a=>{const q=eP(r,a.k);return [r[a.k]==null?'':r[a.k],q==null?'':+q.toFixed(1)];})]));
  }
  if(rows.length)blocks.push({p,rows});
 });
 return {H,blocks,skip};
}'''

BOOK_OLD = '''function exBook(file,H,data,ps,skip){
 return xlLib().then(X=>{
  const wb=new X.Workbook();wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title='EPI coverage';
  const ws=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
  ws.getColumn(1).width=30;ws.getColumn(2).width=110;
  const add=(a,b)=>{const r=ws.addRow([a,String(b==null?'':b)]);r.getCell(1).font={bold:true};r.alignment={vertical:'top',wrapText:true};};
  add('Workbook','EPI-MIS antigen coverage and dose numbers from the EPI routine coverage tab of the KP Polio and Synergy Dashboard.');
  add('Periods',ps.map(p=>p.lab).join(' \u00b7 '));
  add('Rows',EXG==='d'?'One row per district and period':'One row per EPI-MIS union council and period');
  add('Division / district filter',_slug().replace(/_/g,' '));
  add('Sources','2023 and 2025: UC-wise single-month EPI-MIS exports \u00b7 2024: district-level single-month exports \u00b7 2026: UC-wise year-to-date export (Jan \u2013 Sep).');
  add('Coverage %','Doses given \u00f7 target for the same period. BCG and OPV-0 use newborns; the other 17 doses use surviving infants.');
  add('Sep 2026','The Sep 2026 month is the archived part-report (about 65% of a normal month). The year-to-date row carries the complete Jan \u2013 Sep 2026 figures \u2014 do not add the two together.');
  add('Blank cells','A blank dose or % means that export does not publish the figure. The 2026 monthly archive carries only the eleven core doses.');
  if(skip.length)add('Not available at UC grain',skip.join(' \u00b7 ')+'. UC rows exist for the 2023 and 2025 monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no single-month UC export.');
  add('Made',new Date().toLocaleString());
  xlSheet(wb,{sheet:'Coverage data',H,rows:data});
  return wb.xlsx.writeBuffer();
 }).then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();});
}'''

BOOK_NEW = '''function exBook(file,H,blocks,ps,skip){
 return xlLib().then(X=>{
  const wb=new X.Workbook();wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title='EPI coverage';
  const ws=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
  ws.getColumn(1).width=30;ws.getColumn(2).width=110;
  const add=(a,b)=>{const r=ws.addRow([a,String(b==null?'':b)]);r.getCell(1).font={bold:true};r.alignment={vertical:'top',wrapText:true};};
  add('Workbook','EPI-MIS antigen coverage and dose numbers from the EPI routine coverage tab of the KP Polio and Synergy Dashboard.');
  add('Year',EXY);
  add('Periods',ps.map(p=>p.lab).join(' \u00b7 '));
  add('Sheets','One sheet per selected period, named by its month. Months are never added together; the Period column repeats the month on every row if you stack the sheets.');
  add('Rows',EXG==='dv'?'One row per division and period; a division re-adds its district rows for that period, so its % is doses \u00f7 target over the whole division, not an average of district rates.':EXG==='d'?'One row per district and period':'One row per EPI-MIS union council and period');
  add('Division / district filter',_slug().replace(/_/g,' '));
  add('Sources','2023 and 2025: UC-wise single-month EPI-MIS exports \u00b7 2024: district-level single-month exports \u00b7 2026: UC-wise year-to-date export (Jan \u2013 Sep).');
  add('Coverage %','Doses given \u00f7 target for the same period. BCG and OPV-0 use newborns; the other 17 doses use surviving infants.');
  add('Sep 2026','The Sep 2026 month is the archived part-report (about 65% of a normal month). The year-to-date row carries the complete Jan \u2013 Sep 2026 figures \u2014 do not add the two together.');
  add('Blank cells','A blank dose or % means that export does not publish the figure. The 2026 monthly archive carries only the eleven core doses.');
  if(skip.length)add('Not available at UC grain',skip.join(' \u00b7 ')+'. UC rows exist for the 2023 and 2025 monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no single-month UC export.');
  add('Made',new Date().toLocaleString());
  blocks.forEach(b=>xlSheet(wb,{sheet:b.p.lab,H,rows:b.rows}));
  return wb.xlsx.writeBuffer();
 }).then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();});
}'''

DL_OLD = '''function exDownload(xls){
 const ps=exPeriods();
 if(!ps.length){toast('Pick at least one month or the YTD chip');return;}
 const r=exData(ps);
 if(!r.data.length){toast('No rows exist for that selection'+(r.skip.length?' \u2014 '+r.skip.join(', ')+' have no UC data':''));return;}
 const stem='EPI_Coverage_'+exStem(ps)+'_by_'+(EXG==='d'?'District':'UC')+'_'+_slug();
 const cells=r.data.length*r.H.length;
 if(xls&&cells<=1000000){toast('Building Excel\u2026');
  exBook(stem+'.xlsx',r.H,r.data,ps,r.skip).then(()=>toast('Excel downloaded ('+fmt(r.data.length)+' rows)'))
   .catch(()=>{csvRaw(stem+'.csv',r.H,r.data);toast('Excel library did not load, so the same table went out as CSV');});
 }else{
  csvRaw(stem+'.csv',r.H,r.data);
  if(xls)toast('That selection is too large for the browser Excel writer ('+fmt(cells)+' cells) \u2014 CSV downloaded instead');
 }
}'''

DL_NEW = '''function exDownload(xls){
 const ps=exPeriods();
 if(!ps.length){toast('Pick at least one month or the year to date');return;}
 const r=exData(ps),total=r.blocks.reduce((s,b)=>s+b.rows.length,0);
 if(!total){toast('No rows exist for that selection'+(r.skip.length?' \u2014 '+r.skip.join(', ')+' have no UC data':''));return;}
 const stem='EPI_Coverage_'+exStem(ps)+'_by_'+EXG_L[EXG]+'_'+_slug();
 const cells=total*r.H.length;
 if(xls&&cells<=1000000){toast('Building Excel\u2026');
  exBook(stem+'.xlsx',r.H,r.blocks,ps,r.skip).then(()=>toast('Excel downloaded ('+r.blocks.length+' sheet'+(r.blocks.length===1?'':'s')+', '+fmt(total)+' rows)'))
   .catch(()=>{csvRaw(stem+'.csv',r.H,r.blocks.flatMap(b=>b.rows));toast('Excel library did not load, so the same table went out as CSV');});
 }else{
  csvRaw(stem+'.csv',r.H,r.blocks.flatMap(b=>b.rows));
  if(xls)toast('That selection is too large for the browser Excel writer ('+fmt(cells)+' cells) \u2014 CSV downloaded instead');
 }
}'''

WIRE_OLD = "el('btnEXcsv').onclick=()=>exDownload(0);"

WIRE_NEW = '''el('btnEXcsv').onclick=()=>exDownload(0);
el('exYear').onchange=()=>{EXY=+el('exYear').value;renderEX();};
el('exMonthsSel').onchange=()=>{const S=exSel();S.clear();[...el('exMonthsSel').selectedOptions].forEach(o=>S.add(o.value));renderEX();};
el('exAll').onclick=()=>{const S=exSel();eMonths().filter(m=>m.mo.slice(0,4)===''+EXY).forEach(m=>S.add(m.mo));renderEX();};
el('exNone').onclick=()=>{exSel().clear();renderEX();};
el('exGrainSel').onchange=()=>{EXG=el('exGrainSel').value;renderEX();};'''

# "uc rows" read badly next to "district rows"; UC is an abbreviation, so keep its case
CNT_OLD = "' · '+EXG_L[EXG].toLowerCase()+' rows'"
CNT_NEW = "' · '+(EXG==='u'?'UC':EXG_L[EXG].toLowerCase())+' rows'"

FIXES = [
    (CARD_OLD, CARD_NEW),
    (LAYOUT_OLD, LAYOUT_NEW),
    (STATE_OLD, STATE_NEW),
    (PERIODS_OLD, PERIODS_NEW),
    (RENDER_OLD, RENDER_NEW),
    (CNT_OLD, CNT_NEW),
    (DATA_OLD, DATA_NEW),
    (BOOK_OLD, BOOK_NEW),
    (DL_OLD, DL_NEW),
    (WIRE_OLD, WIRE_NEW),
]


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    for old, new in FIXES:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
        if new in v.text:
            print('  skip (already applied): %s' % new[:62].replace('\r\n', ' / '))
            continue
        n = v.text.count(old)
        if not n and any(s.replace('\n', '\r\n') in v.text for s in SUPERSEDED):
            print('  skip (superseded): %s' % old[:62].replace('\r\n', ' / '))
            continue
        if n != 1:
            raise SystemExit('ABORT: %d matches for %r' % (n, old[:90]))
        v.text = v.text.replace(old, new, 1)
        v.changes.append('export ui: %s' % new[:62].replace('\r\n', ' / '))
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), len(v.changes)))
    for c in v.changes:
        print('  %s' % c)


if __name__ == '__main__':
    main()
