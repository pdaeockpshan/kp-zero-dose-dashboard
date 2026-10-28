"""Rebuild the EPI "Download antigen coverage" card into five plain dropdowns.

The owner's report: picking months and UC rows ends in "No rows exist for that selection".
Two causes - (1) UC rows only exist for Jan-Dec 2023, Jan-Dec 2025 and the 2026 year to
date, so 2024 and 2026 single months produced nothing; (2) the old export read the global
`cur`, which the active section and the global EPI filter bar rebuild, so unrelated UI state
could empty it.

This module replaces the card and its JS block with: Year, Month (month names only),
Division, District, Rows (Province total / District / Tehsil / UC). The export reads EPIM and
EPI directly with its own filters, the month list only offers periods that exist at the chosen
grain, and UC/Tehsil are switched off (with the reason on the option) for 2024 - so no reachable
selection can produce an empty download.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

HTML_NEW = r'''<div class="tblhdr"><h3 style="margin:0">Download antigen coverage — pick year, month and rows</h3><span class="cnt" id="cntEX"></span></div>
<div class="note">Pick a <b>year</b>, one or more <b>months</b> (Ctrl/⌘-click for several, or <b>All months</b>), narrow by <b>division</b> and <b>district</b> if you need to, then choose the rows. Every month becomes its own sheet in the Excel file, so two months are never added together. <b>UC and Tehsil rows exist for Jan–Dec 2023, Jan–Dec 2025 and the 2026 year to date</b>; for 2024 those two grains are switched off because the UC-wise export was not published that year.</div>
<div class="nbar" style="margin:6px 0;align-items:flex-end">
<span><span class="cnt" style="display:block">Year</span><select id="exYear" aria-label="Download year" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">Division</span><select id="exDiv" aria-label="Download division" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">District</span><select id="exDist" aria-label="Download district" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"></select></span>
<span><span class="cnt" style="display:block">Rows</span><select id="exGrainSel" aria-label="Download grain" style="font:13px var(--font-sans);padding:5px 8px;border:1px solid var(--color-border);border-radius:8px;background:#fff"><option value="p">Province total</option><option value="d">District</option><option value="t">Tehsil</option><option value="u">UC</option></select></span>
</div>
<div style="margin:6px 0 2px"><span class="cnt" style="display:block;margin-bottom:3px">Months — Ctrl/⌘-click for more than one</span>
<select id="exMonth" multiple aria-label="Download months" style="font:13px var(--font-sans);padding:4px 6px;border:1px solid var(--color-border);border-radius:8px;background:#fff;width:100%;max-width:440px;vertical-align:top"></select></div>
<div class="nbar" style="margin:6px 0"><button class="btn" id="exAll">All months</button> <button class="btn" id="exNone">Clear</button> <button class="btn" id="btnEXxls">Download Excel</button><button class="btn" id="btnEXcsv">Download CSV</button><span class="cnt">Excel: one sheet per month · CSV: the months stacked as rows</span></div>
<div class="cap">Coverage % = doses ÷ target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses). A <b>Province total</b> row adds up every district in the chosen division/district and a <b>Tehsil</b> row adds up its UCs — no row averages the rates of the row above it. <b>Sep 2026</b> is the archived part-report (about 65% of a normal month) and <b>Year to date</b> carries the complete Jan–Sep 2026 figures — do not add the two together. The browser Excel writer handles about a million cells, so a full UC-year fits; larger selections come out as CSV.</div>
</div>
</section>

'''

JS_NEW = r'''// ---------- EPI download: year, month, division, district, rows ----------
const EXG_L={p:'Province total',d:'District',t:'Tehsil',u:'UC'};
const EXG_F={p:'Province',d:'District',t:'Tehsil',u:'UC'};
const EXDV={HAZARA:'Hazara',MALAKAND:'Malakand',BANNU:'Bannu',PESHAWAR:'Peshawar',DIKHAN:'DI Khan',KOHAT:'Kohat',MARDAN:'Mardan'};
const EXMON=['January','February','March','April','May','June','July','August','September','October','November','December'];
const exYears=[2023,2024,2025,2026];
let EXY=2026,EXG='d',EXDIV='',EXDIST='',EXPER=new Set(['YTD']);
const exDvL=d=>EXDV[d]||d;
const exMonName=mo=>EXMON[+mo.slice(5,7)-1];
const exYearMonths=y=>(EMETA.months||[]).filter(m=>m.mo.slice(0,4)===''+y);
const exUCMonthOK=mo=>EUCOK&&eucMi(mo)>=0;
// UC-wise rows are published for Jan-Dec 2023, Jan-Dec 2025 and the 2026 year to date only.
const exHasUC=y=>y===2026||exYearMonths(y).some(m=>exUCMonthOK(m.mo));
const exUCG=()=>EXG==='t'||EXG==='u';
const exAvail=()=>{
 if(exUCG()){
  if(EXY===2026)return [{mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date'}];
  return exYearMonths(EXY).filter(m=>exUCMonthOK(m.mo)).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo)}));
 }
 const ps=exYearMonths(EXY).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo)}));
 if(EXY===2026)ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date'});
 return ps;
};
const exPeriods=()=>exAvail().filter(p=>EXPER.has(p.mo||'YTD'));
const exPerOK=(r,p)=>p.mo?r.mo===p.mo:r.mo.slice(0,4)===''+EXY;
const exDivOK=r=>!EXDIV||r.dv===EXDIV;
const exDistOK=r=>!EXDIST||r.ed===EXDIST;
const exDistricts=()=>uniq(EPIM.filter(exDivOK).map(r=>r.ed));
const exUCRows=p=>{
 const f=r=>exDivOK(r)&&exDistOK(r);
 if(!p.mo)return EPI.filter(f);
 const mi=eucMi(p.mo);
 return mi<0?[]:EPI.map((r,i)=>eucRow(r,i,mi)).filter(f);
};
// Tehsil rows re-add their UC rows; the same tehsil name can sit in two districts, so key on both.
const exTehRows=p=>{
 const G={};exUCRows(p).forEach(r=>{(G[r.ed+'|'+r.t]=G[r.ed+'|'+r.t]||[]).push(r);});
 return Object.entries(G).map(([k,v])=>({ed:v[0].ed,t:v[0].t,dv:v[0].dv,...aggE(v)}))
  .sort((a,b)=>a.dv.localeCompare(b.dv)||a.ed.localeCompare(b.ed)||a.t.localeCompare(b.t));
};
const exScope=()=>EXDIST||EXDIV||'All_districts';
const exResetSel=()=>{EXPER.clear();const a=exAvail();if(a.length)EXPER.add(a[a.length-1].mo||'YTD');};
function renderEX(){
 const ys=el('exYear');
 if(!ys.options.length)ys.innerHTML=exYears.map(y=>'<option value="'+y+'">'+y+'</option>').join('');
 ys.value=''+EXY;
 if(exUCG()&&!exHasUC(EXY)){EXG='d';exResetSel();}
 const gs=el('exGrainSel');
 [...gs.options].forEach(o=>{const uc=o.value==='t'||o.value==='u',off=uc&&!exHasUC(EXY);
  o.disabled=off;o.textContent=EXG_L[o.value]+(off?' · not published for '+EXY:'');});
 gs.value=EXG;
 const ds=el('exDiv');
 if(!ds.options.length)ds.innerHTML='<option value="">All divisions</option>'+uniq(EPIM.map(r=>r.dv)).map(d=>'<option value="'+esc(d)+'">'+esc(exDvL(d))+'</option>').join('');
 ds.value=EXDIV;
 const dl=exDistricts();
 if(EXDIST&&!dl.includes(EXDIST))EXDIST='';
 const dd=el('exDist');
 dd.innerHTML='<option value="">All districts</option>'+dl.map(d=>'<option value="'+esc(d)+'">'+esc(d)+'</option>').join('');
 dd.value=EXDIST;
 const av=exAvail();
 const ms=el('exMonth');
 ms.innerHTML=av.map(p=>{const k=p.mo||'YTD';return '<option value="'+esc(k)+'"'+(EXPER.has(k)?' selected':'')+'>'+esc(p.mn)+'</option>';}).join('');
 ms.size=Math.min(Math.max(av.length,3),9);
 const n=exPeriods().length;
 ['btnEXxls','btnEXcsv'].forEach(id=>{const b=el(id);if(b){b.disabled=!n;b.title=n?'':'Pick at least one month first';}});
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' · '+EXG_L[EXG]+' rows'+(EXDIV?' · '+exDvL(EXDIV):'')+(EXDIST?' · '+EXDIST:''):'Pick at least one month';
}
function exData(ps){
 const H=['Period','Period type','Grain and source','Division','District','Tehsil','UC (EPI-MIS)','EPI-MIS code','Target newborns','Target surviving infants',...EAG.flatMap(a=>[a.l+' doses',a.l+' %'])];
 const N=r=>EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)]);
 const blocks=[],skip=[];
 ps.forEach(p=>{
  const src=' · EPI-MIS '+(p.mo?'single-month':'year to date'),rows=[];
  if(EXG==='p'){
   const r=aggE(EPIM.filter(x=>exPerOK(x,p)&&exDivOK(x)&&exDistOK(x)));
   const lab=EXDIST?'District total · '+EXDIST:EXDIV?'Division total · '+exDvL(EXDIV):'Province total';
   rows.push([p.lab,p.type,lab+src,EXDIV?exDvL(EXDIV):'All divisions',EXDIST||'','','','',r.n,r.s,...N(r)]);
  }else if(EXG==='d'){
   groupE(EPIM.filter(x=>exPerOK(x,p)&&exDivOK(x)&&exDistOK(x)),'ed')
    .sort((a,b)=>a.dv.localeCompare(b.dv)||a.k.localeCompare(b.k))
    .forEach(r=>rows.push([p.lab,p.type,'District'+src,exDvL(r.dv),r.k,'','','',r.n,r.s,...N(r)]));
  }else if(EXG==='t'){
   exTehRows(p).forEach(r=>rows.push([p.lab,p.type,'Tehsil'+src,exDvL(r.dv),r.ed,r.t,'','',r.n,r.s,...N(r)]));
  }else{
   exUCRows(p).sort((a,b)=>a.dv.localeCompare(b.dv)||a.ed.localeCompare(b.ed)||a.t.localeCompare(b.t)||(a.en||'').localeCompare(b.en||''))
    .forEach(r=>rows.push([p.lab,p.type,'UC'+src,exDvL(r.dv),r.ed,r.t,r.en,r.ec,r.n,r.s,...N(r)]));
  }
  if(rows.length)blocks.push({p,rows});else skip.push(p.lab);
 });
 return {H,blocks,skip};
}
const exStem=()=>{
 const ps=exPeriods(),ms=ps.filter(p=>p.type==='Month').map(p=>p.mo);
 let s;
 if(!ms.length)s=EXY+'_YTD';
 else if(ms.length===1)s=ms[0];
 else if(ms.length===12)s=''+EXY;
 else s=ms[0]+'_'+ms.length+'months';
 if(ms.length&&ps.some(p=>p.type!=='Month'))s+='_plus_YTD';
 return s;
};
function exBook(file,H,blocks,ps,skip){
 return xlLib().then(X=>{
  const wb=new X.Workbook();wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title='EPI coverage';
  const ws=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
  ws.getColumn(1).width=30;ws.getColumn(2).width=110;
  const add=(a,b)=>{const r=ws.addRow([a,String(b==null?'':b)]);r.getCell(1).font={bold:true};r.alignment={vertical:'top',wrapText:true};};
  add('Workbook','EPI-MIS antigen coverage and dose numbers from the EPI routine coverage tab of the KP Polio and Synergy Dashboard.');
  add('Year',EXY);
  add('Periods',ps.map(p=>p.lab).join(' · '));
  add('Sheets','One sheet per selected period, named by its month. Months are never added together; the Period column repeats the month on every row if you stack the sheets.');
  add('Rows',EXG==='p'?'One total row per period for the selected division/district; it adds up the district rows, so its % is doses ÷ target for the whole area, not an average of district rates.':EXG==='d'?'One row per district and period':EXG==='t'?'One row per tehsil and period; a tehsil re-adds its UC rows, so its % is doses ÷ target for the whole tehsil.':'One row per EPI-MIS union council and period');
  add('Division / district filter',(EXDIV?exDvL(EXDIV):'All divisions')+(EXDIST?' · '+EXDIST:''));
  add('Sources','2023 and 2025 months: UC-wise single-month EPI-MIS exports · 2024 and 2026 months: district-level EPI-MIS monthly exports · 2026 year to date: UC-wise year-to-date export (Jan – Sep).');
  add('Coverage %','Doses given ÷ target for the same period. BCG and OPV-0 use newborns; the other 17 doses use surviving infants.');
  add('Sep 2026','The Sep 2026 month is the archived part-report (about 65% of a normal month). The year-to-date row carries the complete Jan – Sep 2026 figures — do not add the two together.');
  add('Blank cells','A blank dose or % means that export does not publish the figure. The 2026 monthly archive carries only the eleven core doses.');
  if(skip.length)add('No UC detail',skip.join(' · ')+' — the UC-wise export has no rows for that district and period.');
  add('Made',new Date().toLocaleString());
  blocks.forEach(b=>xlSheet(wb,{sheet:b.p.lab,H,rows:b.rows}));
  return wb.xlsx.writeBuffer();
 }).then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();});
}
function exDownload(xls){
 const ps=exPeriods();
 if(!ps.length){toast('Pick at least one month or the year to date');return;}
 const r=exData(ps),total=r.blocks.reduce((s,b)=>s+b.rows.length,0);
 if(!total){toast('No UC rows for '+(EXDIST||exDvL(EXDIV)||'this selection')+' in '+r.skip.join(', '));return;}
 const stem='EPI_Coverage_'+exStem()+'_by_'+EXG_F[EXG]+'_'+exScope();
 const cells=total*r.H.length;
 if(xls&&cells<=1000000){toast('Building Excel…');
  exBook(stem+'.xlsx',r.H,r.blocks,ps,r.skip).then(()=>toast('Excel downloaded ('+r.blocks.length+' sheet'+(r.blocks.length===1?'':'s')+', '+fmt(total)+' rows)'))
   .catch(()=>{csvRaw(stem+'.csv',r.H,r.blocks.flatMap(b=>b.rows));toast('Excel library did not load, so the same table went out as CSV');});
 }else{
  csvRaw(stem+'.csv',r.H,r.blocks.flatMap(b=>b.rows));
  if(xls)toast('That selection is too large for the browser Excel writer ('+fmt(cells)+' cells) — CSV downloaded instead');
 }
}
el('exYear').onchange=()=>{EXY=+el('exYear').value;exResetSel();renderEX();};
el('exMonth').onchange=()=>{EXPER.clear();[...el('exMonth').selectedOptions].forEach(o=>EXPER.add(o.value));renderEX();};
el('exAll').onclick=()=>{exAvail().forEach(p=>EXPER.add(p.mo||'YTD'));renderEX();};
el('exNone').onclick=()=>{EXPER.clear();renderEX();};
el('exDiv').onchange=()=>{EXDIV=el('exDiv').value;EXDIST='';renderEX();};
el('exDist').onchange=()=>{EXDIST=el('exDist').value;renderEX();};
el('exGrainSel').onchange=()=>{EXG=el('exGrainSel').value;exResetSel();renderEX();};

'''

HTML_START = '<div class="tblhdr"><h3 style="margin:0">Download antigen coverage'
HTML_END = '<!-- ================= ④ EPI ROUTINE COVERAGE: PRIORITY UCs'

JS_START = "const EXG_L={dv:'Division',d:'District',u:'UC'};"
JS_END = '// polio warning threshold: top quarter of UCs by zero-dose children reported per 100 target infants'

MARK = 'const EXG_F={'


def splice(text, start, end, new, *, label, done):
    if done in text:
        print('  skip (already applied): %s' % label)
        return text, 0
    if text.count(start) != 1 or text.count(end) != 1:
        raise SystemExit('ABORT: markers not unique for %r (%d / %d)'
                         % (label, text.count(start), text.count(end)))
    i = text.index(start)
    j = text.index(end, i)
    print('  spliced %s (%d chars -> %d)' % (label, j - i, len(new)))
    return text[:i] + new + text[j:], 1


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edited = 0
    v.text, n = splice(v.text, HTML_START, HTML_END, HTML_NEW.replace('\n', '\r\n'),
                       label='download card', done='id="exMonth"')
    edited += n
    if n:
        v.changes.append('EPI download: five-dropdown card')
    v.text, n = splice(v.text, JS_START, JS_END, JS_NEW.replace('\n', '\r\n'),
                       label='download JS', done=MARK)
    edited += n
    if n:
        v.changes.append('EPI download: EPIM/EPI-sourced export with own filters')
    if not edited:
        print('nothing to do')
        return
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d splices' % (v.delta(), edited))


if __name__ == '__main__':
    main()
