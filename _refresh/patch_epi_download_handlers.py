# -*- coding: utf-8 -*-
"""Re-bind the EPI tab's download buttons and the District/UC pill pair.

Commit 8703c69 rewrote the EPI download card's handlers and dropped the five bindings that sat
just above them, so `exDownload`, `enExport` and `eyExport` were still defined but never called:
the owner picked 2026 / month-wise / UC-wise and both "Download Excel" and "Download CSV" did
nothing. The same deletion also left the "Doses given - numbers by district and UC" download and
the "Antigen coverage by year" download dead, and the District/UC pills in that card unresponsive.

Master only: push_master.py derives the other three variants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

ANCHOR = r"""el('exYear').onchange=()=>{EXY=+el('exYear').value;exResetSel();renderEX();};"""

ANCHOR_NEW = r"""el('eNpills').querySelectorAll('button').forEach(b=>b.onclick=()=>{EN=b.dataset.g;renderEN();});
el('btnENxls').onclick=enExport;
el('btnEYxls').onclick=eyExport;
el('btnEXxls').onclick=()=>exDownload(1);
el('btnEXcsv').onclick=()=>exDownload(0);
el('exYear').onchange=()=>{EXY=+el('exYear').value;exResetSel();renderEX();};"""

EDITS = [
    (ANCHOR, ANCHOR_NEW, 'the EPI download buttons and the District/UC pills are bound again', 1),
]


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    todo = []
    for old, new, label, expect in EDITS:
        o, n = crlf(old), crlf(new)
        cn = v.text.count(n)
        if cn == expect:
            continue
        if cn or v.text.count(o) != expect:
            raise SystemExit('ABORT: %d old / %d new matches for %s, expected %d'
                             % (v.text.count(o), cn, label, expect))
        todo.append((o, n, label))
    if not todo:
        print('nothing to do')
        return
    for o, n, label in todo:
        v.text = v.text.replace(o, n)
        v.changes.append('EPI tab: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars (%d edit(s))' % (v.delta(), len(todo)))


if __name__ == '__main__':
    main()
