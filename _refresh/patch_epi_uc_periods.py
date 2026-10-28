"""Keep the month list on the EPI download card when the UC grain is picked, and fill its % columns.

The owner's report (28-Oct-2026): "pick year, month and rows, if you want to download uc wise data
and select UC, months disappears". Two defects behind it.

1. `exAvail()` returned a single "Year to date" chip for the UC/Tehsil grain in 2026, so the month
   grid collapsed to one entry - the months looked like they had vanished. EPI-MIS really does
   publish UC rows month by month only for 2023 and 2025 (EPIUC carries 24 months, 2023-01 to
   2025-12) and gives 2026 as one Jan-Sep year-to-date total, so the answer is not to invent months
   but to keep them listed, switched off, with the reason written next to them.
2. Every coverage-% column came out blank on UC and Tehsil downloads: `exUCRows` builds its rows
   from the EPI register or the EUCM month slice, and neither carries the `p_<antigen>` fields that
   `N(r)` read. Doses arrived, percentages did not - no use for UC-level analysis. The % is now
   computed with the dashboard's own `eP()` (doses / that row's target) whenever the field is
   absent, so a UC row carries that UC's rate.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MARK_OLD = '''<div style="margin:6px 0 2px"><span class="cnt" style="display:block;margin-bottom:4px">Months — tick one or more</span>
<div id="exMonthBox" role="group" aria-label="Download months" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:3px 14px;max-width:640px;font:13px var(--font-sans)"></div></div>'''

MARK_NEW = '''<div style="margin:6px 0 2px"><span class="cnt" id="exMonthLab" style="display:block;margin-bottom:4px">Months — tick one or more</span>
<div id="exMonthBox" role="group" aria-label="Download months" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:3px 14px;max-width:640px;font:13px var(--font-sans)"></div>
<div id="exHint" style="display:none;margin-top:6px;font:italic 12px var(--font-sans);color:#92400e"></div></div>'''

NOTE_OLD = 'UC and Tehsil rows exist for Jan–Dec 2023, Jan–Dec 2025 and the 2026 year to date</b>; for 2024 those two grains are switched off because the UC-wise export was not published that year.'

NOTE_NEW = 'UC and Tehsil rows exist month by month for Jan–Dec 2023 and Jan–Dec 2025, and for 2026 only as one Jan–Sep year-to-date total</b> — the UC months EPI-MIS never published stay listed but switched off; for 2024 those two grains are switched off altogether because the UC-wise export was not published that year.'

AVAIL_OLD = '''const exUCMonthOK=mo=>EUCOK&&eucMi(mo)>=0;
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
const exPeriods=()=>exAvail().filter(p=>EXPER.has(p.mo||'YTD'));'''

AVAIL_NEW = '''const exUCMonthOK=mo=>EUCOK&&eucMi(mo)>=0;
// EPI-MIS publishes UC rows month by month for 2023 and 2025 only; 2026 arrives as one Jan-Sep
// year-to-date total. A month with no UC export stays in the list but switched off, so choosing the
// UC grain never makes the month list disappear.
const exUCYTD=y=>y===2026;
const exHasUC=y=>exUCYTD(y)||exYearMonths(y).some(m=>exUCMonthOK(m.mo));
const exUCG=()=>EXG==='t'||EXG==='u';
const exAvail=()=>{
 if(exUCG()){
  const ps=exYearMonths(EXY).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:!exUCMonthOK(m.mo)}));
  if(exUCYTD(EXY))ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date',off:false});
  return ps;
 }
 const ps=exYearMonths(EXY).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:false}));
 if(EXY===2026)ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date',off:false});
 return ps;
};
const exPeriods=()=>exAvail().filter(p=>!p.off&&EXPER.has(p.mo||'YTD'));'''

RESET_OLD = "const exResetSel=()=>{EXPER.clear();const a=exAvail();if(a.length)EXPER.add(a[a.length-1].mo||'YTD');};"
RESET_NEW = "const exResetSel=()=>{EXPER.clear();const a=exAvail().filter(p=>!p.off);if(a.length)EXPER.add(a[a.length-1].mo||'YTD');};"

MONTHS_OLD = ''' const av=exAvail(),box=el('exMonthBox');
 box.innerHTML=av.map(p=>{const k=p.mo||'YTD';
  return '<label style="display:flex;align-items:center;gap:6px;cursor:pointer"><input type="checkbox" value="'+esc(k)+'"'+(EXPER.has(k)?' checked':'')+'>'+esc(p.mn)+'</label>';}).join('');
 // Ticking a month only updates the count and the buttons: rebuilding the list here would move
 // the box under the pointer while the reader is still ticking months.
 box.querySelectorAll('input').forEach(c=>c.onchange=()=>{EXPER.clear();box.querySelectorAll('input:checked').forEach(x=>EXPER.add(x.value));exCount();});'''

MONTHS_NEW = ''' const av=exAvail(),box=el('exMonthBox');
 box.innerHTML=av.map(p=>{const k=p.mo||'YTD';
  return '<label title="'+(p.off?'UC month-wise rows are not published for '+p.lab:'')+'" style="display:flex;align-items:center;gap:6px;cursor:'+(p.off?'not-allowed':'pointer')+(p.off?';opacity:.45;':'')+'"><input type="checkbox" value="'+esc(k)+'"'+(p.off?' disabled':'')+(EXPER.has(k)&&!p.off?' checked':'')+'>'+esc(p.mn)+'</label>';}).join('');
 // Ticking a month only updates the count and the buttons: rebuilding the list here would move
 // the box under the pointer while the reader is still ticking months.
 box.querySelectorAll('input').forEach(c=>c.onchange=()=>{EXPER.clear();box.querySelectorAll('input:checked').forEach(x=>EXPER.add(x.value));exCount();});
 const offN=av.filter(p=>p.off).length,lab=el('exMonthLab'),hint=el('exHint');
 if(lab)lab.textContent=(offN?'Periods':'Months')+' — tick one or more';
 if(hint){hint.style.display=offN?'':'none';
  hint.textContent=offN?'UC rows are published month by month for 2023 and 2025 only. EPI-MIS gives 2026 as one Jan–Sep year-to-date total, so the '+EXY+' months above are switched off — tick "Year to date", or change Year to 2023 or 2025 for month-by-month UC rows.':'';}'''

ALL_OLD = "el('exAll').onclick=()=>{exAvail().forEach(p=>EXPER.add(p.mo||'YTD'));renderEX();};"
ALL_NEW = "el('exAll').onclick=()=>{exAvail().filter(p=>!p.off).forEach(p=>EXPER.add(p.mo||'YTD'));renderEX();};"

N_OLD = " const N=r=>EAG.flatMap(a=>[r[a.k]==null?'':r[a.k],r['p_'+a.k]==null?'':+r['p_'+a.k].toFixed(1)]);"
N_NEW = " const N=r=>EAG.flatMap(a=>{const d=r[a.k],p=r['p_'+a.k]!=null?r['p_'+a.k]:eP(r,a.k);return [d==null?'':d,p==null?'':+p.toFixed(1)];});"

CAP_OLD = 'Coverage % = doses ÷ target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses).'
CAP_NEW = "Coverage % = doses ÷ target for the same period (newborns for BCG and OPV-0, surviving infants for the other 17 doses), computed per row — a UC row carries that UC's own rate."

COV_OLD = "  add('Coverage %','Doses given ÷ target for the same period. BCG and OPV-0 use newborns; the other 17 doses use surviving infants.');"
COV_NEW = "  add(\"Coverage %\",\"Doses ÷ the row's own target for the same period, computed by the dashboard: newborns for BCG and OPV-0, surviving infants for the other 17 doses. A UC row therefore carries that UC's rate, not a district average.\");"

BLANK_OLD = "  add('Blank cells','A blank dose or % means that export does not publish the figure. The 2026 monthly archive carries only the eleven core doses.');"
BLANK_NEW = "  add('Blank cells','A blank dose means that export does not publish the figure — the 2026 monthly archive carries only the eleven core doses — and a % is blank when its dose or its target is.');"


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edits = [
        (MARK_OLD, MARK_NEW, 'month label and hint slot', 1),
        (NOTE_OLD, NOTE_NEW, 'note names the UC periods that exist', 1),
        (AVAIL_OLD, AVAIL_NEW, 'unpublished UC months stay listed but switched off', 1),
        (RESET_OLD, RESET_NEW, 'reset picks the last published period', 1),
        (MONTHS_OLD, MONTHS_NEW, 'render disabled months and the reason', 1),
        (ALL_OLD, ALL_NEW, 'All months ticks only published periods', 1),
        (N_OLD, N_NEW, 'compute the coverage % when the row carries none', 1),
        (CAP_OLD, CAP_NEW, 'caption says the % is per row', 1),
        (COV_OLD, COV_NEW, 'read me says the % is computed per row', 1),
        (BLANK_OLD, BLANK_NEW, 'read me explains a blank %', 1),
    ]
    todo = []
    for old, new, label, expect in edits:
        o, n = crlf(old), crlf(new)
        c = v.text.count(o)
        if c == 0 and v.text.count(n) == expect:
            continue
        if c != expect:
            raise SystemExit('ABORT: %d matches for %s, expected %d' % (c, label, expect))
        todo.append((o, n, label))
    if not todo:
        print('nothing to do')
        return
    for o, n, label in todo:
        v.text = v.text.replace(o, n)
        v.changes.append('EPI UC periods: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars (%d edit(s))' % (v.delta(), len(todo)))


if __name__ == '__main__':
    main()
