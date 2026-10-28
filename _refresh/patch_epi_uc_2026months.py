# -*- coding: utf-8 -*-
"""Publish the 2026 UC months: rewrite every passage that said 2026 has none.

Until the owner downloaded a UC-wise export for each 2026 month, the year existed at UC grain
only as one Jan-Sep total, and September was a part-report (its older export stopped mid-month).
That is no longer true: the nine 2026 monthly exports carry all 1,459 UCs, Sep 2026 is a complete
month, and the months add up exactly to the year-to-date register on every UC and dose. The
download card, the numbers table, the EPI tab's monthly archive and the workbook read-me all
still said otherwise, so this module corrects the words to match the payloads.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

HINT_OLD = r"""hint.textContent=offN?'UC rows are published month by month for 2023 and 2025 only. EPI-MIS gives 2026 as one Jan–Sep year-to-date total, so the '+EXY+' months above are switched off — tick "Jan–Sep 2026 (year to date)" for the 2026 UC figures, or change Year to 2023 or 2025 for month-by-month UC rows.':'';}"""
HINT_NEW = r"""hint.textContent=offN?'UC rows are published month by month for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, so the '+EXY+' months above are switched off. Change Year to 2023, 2025 or 2026 for month-by-month UC rows, or tick "Jan–Sep 2026 (year to date)" for the 2026 UC total.':'';}"""

COMMENT_OLD = r"""// EPI-MIS publishes UC rows month by month for 2023 and 2025 only; 2026 arrives as one Jan-Sep
// year-to-date total. A month with no UC export stays in the list but switched off, so choosing the
// UC grain never makes the month list disappear."""
COMMENT_NEW = r"""// EPI-MIS publishes UC rows month by month for 2023, 2025 and every 2026 month on file; 2024 was
// exported district-level only. A month with no UC export stays in the list but switched off, so
// choosing the UC grain never makes the month list disappear."""

JUMP_OLD = r""" // UC rows exist month by month for 2023 and 2025 only; 2024 has no UC grain and 2026 is one
 // Jan-Sep total. Landing on such a year would show every month switched off, so start the reader
 // on the newest year that has UC months and say so."""
JUMP_NEW = r""" // UC rows exist month by month for 2023, 2025 and 2026; 2024 was exported district-level only.
 // Landing on such a year would show every month switched off, so start the reader on the newest
 // year that has UC months and say so."""

TOAST_OLD = r"""toast('UC rows exist month by month for 2023 and 2025 — switched Year to '+y);"""
TOAST_NEW = r"""toast('UC rows exist month by month for '+y+' — switched Year');"""

TEN_OLD = r"""  el('tEN').innerHTML='<tr><td class="empty">No UC-level numbers for '+esc(emLab(EM))+' — UC rows exist for the 2023 and 2025 monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no single-month UC export. Switch to <b>District</b>, pick a 2023 or 2025 month, or set <b>EPI month</b> to Year to date.</td></tr>';"""
TEN_NEW = r"""  el('tEN').innerHTML='<tr><td class="empty">No UC-level numbers for '+esc(emLab(EM))+' — UC rows exist for the 2023, 2025 and 2026 monthly exports; the 2024 exports are district-level, so that year has no UC grain. Switch to <b>District</b>, pick a 2023, 2025 or 2026 month, or set <b>EPI month</b> to Year to date.</td></tr>';"""

TEU_OLD = r"""' — UC rows exist for the 2023 and 2025 monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no single-month UC export. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> to Year to date.'"""
TEU_NEW = r"""' — UC rows exist for the 2023, 2025 and 2026 monthly exports; the 2024 exports are district-level, so that year has no UC grain. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> to Year to date.'"""

NOTE_OLD = r"""the doses table below has UC numbers for the 2023 and 2025 months.'"""
NOTE_NEW = r"""the doses table below has UC numbers for the 2023, 2025 and 2026 months.'"""

CARD_OLD = r"""<b>UC and Tehsil rows exist month by month for Jan–Dec 2023 and Jan–Dec 2025, and for 2026 only as one Jan–Sep year-to-date total</b> — the UC months EPI-MIS never published stay listed but switched off; for 2024 those two grains are switched off altogether because the UC-wise export was not published that year."""
CARD_NEW = r"""<b>UC and Tehsil rows exist month by month for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026</b> — the 2024 months stay listed but switched off because that year's export was district-level; the Jan–Sep 2026 year-to-date total is always on offer as its own row."""

EPI_OLD = r"""In the month view the extra doses exist only for the 2023, 2024 and 2025 monthly exports — 2024 is district-level, 2023 and 2025 UC-level — and the year table below adds each year up. The month-by-month charts use the separate single-month archive, where the <b>Sep 2026 bar is an older part-report</b> — the year-to-date file above already carries a full month for September."""
EPI_NEW = r"""The month view carries the same 19 doses for every year — 2023, 2025 and 2026 from the UC-wise exports, 2024 from the district-level ones — and the year table below adds each year up. <b>Sep 2026 is now a complete single-month export</b>, not the part-report the archive used to hold: the Jan–Sep months add up exactly to the year-to-date figures above."""

CAP_OLD = r"""<b>Sep 2026</b> is the archived part-report (about 65% of a normal month) and <b>Year to date</b> carries the complete Jan–Sep 2026 figures — do not add the two together."""
CAP_NEW = r"""<b>Sep 2026</b> is the complete single-month export and <b>Year to date</b> is the Jan–Sep 2026 total — the two describe different periods, so do not add them together."""

SRC_OLD = r"""  add('Sources','2023 and 2025 months: UC-wise single-month EPI-MIS exports · 2024 and 2026 months: district-level EPI-MIS monthly exports · 2026 year to date: UC-wise year-to-date export (Jan – Sep).');"""
SRC_NEW = r"""  add('Sources','2023, 2025 and 2026 months: UC-wise single-month EPI-MIS exports · 2024 months: district-level EPI-MIS monthly exports · 2026 year to date: UC-wise year-to-date export (Jan – Sep).');"""

RM_OLD = r"""  add('Sep 2026','The Sep 2026 month is the archived part-report (about 65% of a normal month). The year-to-date row carries the complete Jan – Sep 2026 figures — do not add the two together.');"""
RM_NEW = r"""  add('Sep 2026','The Sep 2026 month is the complete single-month export. The year-to-date row is the Jan – Sep 2026 total — do not add the two together.');"""

CAPY_OLD = r"""  cap.textContent='UC doses exist for Jan–Dec 2023 and Jan–Dec 2025 (UC-wise monthly exports) and for the 2026 year to date.';"""
CAPY_NEW = r"""  cap.textContent='UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026 (UC-wise monthly exports), and as the 2026 year-to-date total.';"""

EMNOTE_OLD = r""" document.querySelectorAll('.emnote').forEach(n=>n.textContent=EM?'Month view uses district-level EPI-MIS monthly data (division and district filters apply). UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and the 2026 year to date; the All UCs coverage table stays year-to-date.':'Monthly charts use district-level EPI-MIS data; UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and the 2026 year to date.');}"""
EMNOTE_NEW = r""" document.querySelectorAll('.emnote').forEach(n=>n.textContent=EM?'Month view uses district-level EPI-MIS monthly data (division and district filters apply). UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year to date; the All UCs coverage table stays year-to-date.':'Monthly charts use district-level EPI-MIS data; UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year to date.');}"""

EDITS = [
    (HINT_OLD, HINT_NEW, 'hint lists the 2026 UC months', 1),
    (COMMENT_OLD, COMMENT_NEW, 'grain comment names 2026', 1),
    (JUMP_OLD, JUMP_NEW, 'year-jump comment names 2026', 1),
    (TOAST_OLD, TOAST_NEW, 'year-jump toast names the year it picked', 1),
    (TEN_OLD, TEN_NEW, 'numbers-table empty state lists 2026', 1),
    (TEU_OLD, TEU_NEW, 'coverage-table empty state lists 2026', 1),
    (NOTE_OLD, NOTE_NEW, 'month-view note lists 2026', 1),
    (CARD_OLD, CARD_NEW, 'download card explains the 2026 months', 1),
    (EPI_OLD, EPI_NEW, 'EPI tab drops the Sep part-report caveat', 1),
    (CAP_OLD, CAP_NEW, 'numbers caption drops the Sep part-report caveat', 1),
    (SRC_OLD, SRC_NEW, 'read me Sources row lists 2026 months as UC-wise', 1),
    (RM_OLD, RM_NEW, 'read me Sep 2026 row says complete month', 1),
    (CAPY_OLD, CAPY_NEW, 'year-table caption lists the 2026 UC months', 1),
    (EMNOTE_OLD, EMNOTE_NEW, 'month-view footnotes list the 2026 UC months', 1),
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
        v.changes.append('EPI UC 2026: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars (%d edit(s))' % (v.delta(), len(todo)))


if __name__ == '__main__':
    main()
