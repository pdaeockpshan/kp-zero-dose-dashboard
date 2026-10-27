# -*- coding: utf-8 -*-
"""Dump the parity fixture for _refresh/hrat_eval.js.

Every row of two compiled HRA workbooks is written out as what staff typed (the 33 input columns) and
what the sheet's own formulas produced (the cached value of each of the 39 computed columns). The Node
test reads that fixture, evaluates the payload's formula text over the same inputs and compares, cell
by cell - so the evaluator is proved against the divisions' own arithmetic, not against a model of it.

Two workbooks, because they disagree about everything else:
  * KP HRA UC Level (2).xlsx - 26-Mar-2026 province-wide, 1,418 rows, every aggregate still a formula.
  * HRA UC Level for September 2026 (Mardan Division).xlsx - the freshest round, 132 rows, whose
    eleven epidemiology score columns arrive as pasted values. Those pasted marks are what the
    division published, so they are the expected side of the comparison for that file.

Usage: python _refresh/dump_hrat_parity.py [--spec out/hrat.json] [--out out/hrat_parity.json]
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil  # noqa: E402
from build_hrat import check_shape, clean  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = [
    (r'C:\Users\HD\Downloads\KP HRA UC Level (2).xlsx', 'UC Level HRA Template'),
    (r'C:\Users\HD\Downloads\HRA UC Level for September 2026 (Mardan Division).xlsx',
     'UC Level HRA Template (Sep)'),
]
INPUTS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'I', 'K', 'M',
          'Q', 'S', 'U', 'W', 'Y', 'AA', 'AC', 'AE', 'AG', 'AI', 'AK',
          'AO', 'AQ', 'AS', 'AU', 'AW', 'AY', 'BA',
          'BE', 'BG', 'BI', 'BK', 'BM']


def ci(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def value(v):
    """What openpyxl hands back, in the small vocabulary the evaluator also speaks.

    An empty string stays an empty string: Excel's COUNTA counts a cell holding "" as filled while a
    truly empty cell is blank, and ISBLANK is FALSE for it - so flattening "" into None here would
    hide a real difference between the sheet's arithmetic and the evaluator's.
    """
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return v
    return ' '.join(str(v).split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--spec', default=os.path.join(HERE, 'out', 'hrat.json'))
    ap.add_argument('--out', default=os.path.join(HERE, 'out', 'hrat_parity.json'))
    a = ap.parse_args()
    spec = json.loads(srcutil.read_text(a.spec))
    want = ([x['sc'] for x in spec['i']]
            + [b['sub'] for b in spec['B'] if b['sub']]
            + [b['pct'] for b in spec['B'] if b['pct']]
            + [spec['tail'][k] for k in ('max', 'ovr', 'rank', 'risk')])
    if len(want) != 39 or len(set(want)) != 39:
        raise SystemExit('ERR parity fixture: %d distinct computed columns, want 39'
                         % len(set(want)))

    files = []
    for path, sheet in SOURCES:
        if not os.path.exists(path):
            raise SystemExit('ERR parity fixture: %s is not on disk' % path)
        wbv = load_workbook(path, read_only=True, data_only=True)
        wsf = load_workbook(path, read_only=True, data_only=False)
        vs, fs = wbv[sheet], wsf[sheet]
        head = [' '.join(str(c.value).split()) if c.value is not None else ''
                for c in next(vs.iter_rows(min_row=2, max_row=2))]
        for L in INPUTS + want:
            i = ci(L)
            if i >= len(head):
                raise SystemExit('ERR parity fixture: %s [%s] stops at column %d, no %s'
                                 % (os.path.basename(path), sheet, len(head), L))
        # the letters must mean the same column in this file as in the spec, or the fixture compares
        # the wrong cells; the spec's header is the template's, which carries no numbering
        drift = []
        for L in INPUTS + want:
            want_h = next(c['h'] for c in spec['c'] if c['L'] == L)
            got_h = head[ci(L)]
            if got_h and got_h.rstrip('0123456789 ') != want_h.rstrip('0123456789 '):
                drift.append((L, want_h[:34], got_h[:34]))
        if drift:
            print('NOTE %s: %d columns are headed differently from the template - %s'
                  % (os.path.basename(path), len(drift),
                     '; '.join('%s %r vs %r' % d for d in drift[:4])))
        rows, live, fxo = [], 0, {}
        for sno, (vr, fr) in enumerate(
                zip(vs.iter_rows(min_row=spec['r0'], values_only=True),
                    fs.iter_rows(min_row=spec['r0'], values_only=True)),
                spec['r0']):
            def at(row, L):
                i = ci(L)
                return value(row[i]) if i < len(row) else None
            uc = at(vr, 'D')
            if not uc or not (isinstance(uc, float) or str(uc).isdigit()):
                continue
            code = str(int(uc)) if isinstance(uc, float) else str(uc)
            if len(code) != 8:
                continue
            exp = {L: at(vr, L) for L in want}
            # which of the 39 still carry the sheet's own formula: a pasted cell is a published
            # number, not a claim about the inputs, and the test must say which it compares
            fl = [L for L in want
                  if isinstance(at(fr, L), str) and at(fr, L).startswith('=')]
            live += 1 if fl else 0
            if fl and not fxo:
                # the first live row also gives this file's own formula text per column, so a
                # disagreement can be read as a different vintage rather than a broken evaluator
                for L in fl:
                    t = clean(at(fr, L))
                    if t is None:
                        continue
                    try:
                        check_shape(t, '%s [%s] %s' % (os.path.basename(path), sheet, L))
                    except SystemExit as e:
                        print('SKIP %s %s: %s' % (os.path.basename(path), L, e))
                        continue
                    fxo[L] = t
            rows.append({'r': sno, 'code': code,
                         'in': {L: at(vr, L) for L in INPUTS}, 'exp': exp, 'fl': fl})
        wbv.close()
        wsf.close()
        gap = len(rows) > 1 and rows[-1]['r'] - rows[0]['r'] != len(rows) - 1
        files.append({'name': os.path.basename(path), 'sheet': sheet, 'live': live,
                      'fx': fxo, 'rows': rows})
        pub = {c['L']: c['x'] for c in spec['c'] if c['x']}
        tdiff = [L for L in fxo if pub.get(L) != fxo[L]]
        print('DUMP %s [%s]: %d rows, %d still carrying formulas, %d of 39 columns ever live, '
              '%d of those read with different text than the published spec'
              % (os.path.basename(path), sheet, len(rows), live, len(fxo), len(tdiff)))
        for L in sorted(tdiff, key=ci)[:8]:
            print('     %s  this file: %s' % (L, fxo[L][:120]))
            print('     %s  published: %s' % (L, (pub.get(L) or '')[:120]))
        if gap:
            print('NOTE %s: rows are not contiguous on the sheet, so the fixed rank range cannot be '
                  'compared here' % os.path.basename(path))

    fixture = {'spec': spec, 'files': files, 'want': want, 'inputs': INPUTS}
    js = srcutil.dumps(fixture)
    srcutil.write_text(a.out, js)
    print('OK fixture %d chars, %d rows over %d files'
          % (len(js), sum(len(f['rows']) for f in files), len(files)))


if __name__ == '__main__':
    main()
