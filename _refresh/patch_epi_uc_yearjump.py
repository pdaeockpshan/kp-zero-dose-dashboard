# -*- coding: utf-8 -*-
"""Make choosing the UC (or Tehsil) grain land on a year that actually has UC months.

The 28-Oct-2026 period fix stopped the month list from collapsing, but the card still opens on
Year 2026. EPI-MIS publishes UC rows month by month for 2023 and 2025 only, so at 2026 every month
is listed-but-switched-off and the reader sees nothing to tick - reported again as "I cannot select
months for UC wise data". Picking the UC grain now jumps the Year to the newest year with
month-wise UC rows (2025) and says why, so twelve months are immediately selectable; choosing 2026
afterwards still gives the Jan-Sep year-to-date row.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

OLD = r"""el('exGrainSel').onchange=()=>{EXG=el('exGrainSel').value;exResetSel();renderEX();};"""

NEW = r"""el('exGrainSel').onchange=()=>{EXG=el('exGrainSel').value;
 // UC rows exist month by month for 2023 and 2025 only; 2024 has no UC grain and 2026 is one
 // Jan-Sep total. Landing on such a year would show every month switched off, so start the reader
 // on the newest year that has UC months and say so.
 if(exUCG()&&!exYearMonths(EXY).some(m=>exUCMonthOK(m.mo))){
  const y=exYears.slice().reverse().find(y=>exYearMonths(y).some(m=>exUCMonthOK(m.mo)));
  if(y&&y!==EXY){EXY=y;toast('UC rows exist month by month for 2023 and 2025 — switched Year to '+y);}
 }
 exResetSel();renderEX();};"""

EXPECT = 1


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    o, n = crlf(OLD), crlf(NEW)
    c = v.text.count(o)
    if c == 0 and v.text.count(n) == EXPECT:
        print('nothing to do')
        return
    if c != EXPECT:
        raise SystemExit('ABORT: %d matches for the grain-change handler, expected %d' % (c, EXPECT))
    v.text = v.text.replace(o, n)
    v.changes.append('EPI download: UC grain jumps the Year to a year with UC months')
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars' % v.delta())


if __name__ == '__main__':
    main()
