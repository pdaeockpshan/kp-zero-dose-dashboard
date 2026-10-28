# -*- coding: utf-8 -*-
"""Keep the 2026 UC year-to-date total in the period list whatever year is selected.

EPI-MIS published 2026 UC rows only as one Jan-Sep total. The card reached that total only by
setting Year=2026, which is also the year where every month is switched off - so in practice the
owner could not find or download 2026 UC data at all ("2026 uc wise downloads are not published").
The Jan-Sep 2026 chip is now always listed for the UC and Tehsil grains, and it is the default
pick, so a UC download can always include the 2026 figures. Periods carry their own year so the
workbook name and the read-me Year line stay truthful when a selection spans years.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

AVAIL_OLD = r""" if(exUCG()){
  const ps=exYearMonths(EXY).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:!exUCMonthOK(m.mo)}));
  if(exUCYTD(EXY))ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date',off:false});
  return ps;
 }
 const ps=exYearMonths(EXY).map(m=>({mo:m.mo,lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:false}));
 if(EXY===2026)ps.push({mo:'',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date',off:false});
 return ps;"""

AVAIL_NEW = r""" if(exUCG()){
  const ps=exYearMonths(EXY).map(m=>({mo:m.mo,yr:m.mo.slice(0,4),lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:!exUCMonthOK(m.mo)}));
  // 2026 exists only as one Jan-Sep UC total, so it stays in the list whatever year the dropdown
  // shows: it is the only 2026 UC figure EPI-MIS published and must not hide behind the year pick.
  ps.push({mo:'',yr:'2026',lab:'Jan–Sep 2026',type:'Year to date',mn:'Jan–Sep 2026 (year to date)',off:false});
  return ps;
 }
 const ps=exYearMonths(EXY).map(m=>({mo:m.mo,yr:m.mo.slice(0,4),lab:emLab(m.mo),type:'Month',mn:exMonName(m.mo),off:false}));
 if(EXY===2026)ps.push({mo:'',yr:'2026',lab:'Jan–Sep 2026',type:'Year to date',mn:'Year to date',off:false});
 return ps;"""

STEM_OLD = r"""const exStem=()=>{
 const ps=exPeriods(),ms=ps.filter(p=>p.type==='Month').map(p=>p.mo);
 let s;
 if(!ms.length)s=EXY+'_YTD';
 else if(ms.length===1)s=ms[0];
 else if(ms.length===12)s=''+EXY;
 else s=ms[0]+'_'+ms.length+'months';"""

STEM_NEW = r"""const exStem=()=>{
 const ps=exPeriods(),ms=ps.filter(p=>p.type==='Month').map(p=>p.mo),ys=uniq(ps.map(p=>p.yr));
 let s;
 if(!ms.length)s=(ys[0]||EXY)+'_YTD';
 else if(ms.length===1)s=ms[0];
 else if(ms.length===12&&ys.length===1)s=ys[0];
 else s=ms[0]+'_'+ms.length+'months';"""

YEAR_OLD = r"""add('Year',EXY);"""
YEAR_NEW = r"""add('Year',uniq(ps.map(p=>p.yr)).join(' / '));"""

HINT_OLD = r"""hint.textContent=offN?'UC rows are published month by month for 2023 and 2025 only. EPI-MIS gives 2026 as one Jan–Sep year-to-date total, so the '+EXY+' months above are switched off — tick "Year to date", or change Year to 2023 or 2025 for month-by-month UC rows.':'';}"""
HINT_NEW = r"""hint.textContent=offN?'UC rows are published month by month for 2023 and 2025 only. EPI-MIS gives 2026 as one Jan–Sep year-to-date total, so the '+EXY+' months above are switched off — tick "Jan–Sep 2026 (year to date)" for the 2026 UC figures, or change Year to 2023 or 2025 for month-by-month UC rows.':'';}"""

EDITS = [
    (AVAIL_OLD, AVAIL_NEW, 'the 2026 UC total is always listed', 1),
    (STEM_OLD, STEM_NEW, 'workbook name follows the periods\' own years', 1),
    (YEAR_OLD, YEAR_NEW, 'read me Year lists every year in the selection', 1),
    (HINT_OLD, HINT_NEW, 'hint points at the Jan-Sep 2026 chip', 1),
]


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    todo = []
    for old, new, label, expect in EDITS:
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
        v.changes.append('EPI UC download: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars (%d edit(s))' % (v.delta(), len(todo)))


if __name__ == '__main__':
    main()
