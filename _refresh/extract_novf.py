# -*- coding: utf-8 -*-
"""Extract the SNID Nov-2026 final coverage summary (const NOVF) from the portal export.

`summary_<campaign>_<yyyy-mm-dd>_<hhmmss>.xls` is the district-grain final close-out of a round:
household (planning) target, UCs, vaccinated, recorded missed (NA / Ref / total), covered during
campaign / catch-up / extended catch-up, still missed (NA / Ref / left over / total and % of
target), zero routine dose reported, zero dose covered by the next round, AFP cases, vials
received and remaining sealed usable vials.

Unlike the UC-wise summary this file has no Tehsil / UC columns and no ICM or LQAS figures, so it
supersedes only the district coverage layer. The UC rows of the same round stay at their own last
UC-wise read.

The workbook totals row must re-add from its own 27 district rows, column by column, or the
extract aborts: a totals row that does not reconcile is a different basis, not a rounding slip.

Usage: python _refresh/extract_novf.py [--path <xls>] [--out PATH]
Prints: SRC novf <path> | OK novf <chars> <summary> | ERR novf <reason>
"""
import argparse
import io
import json
import os
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'novf'
NAME_RE = re.compile(r'^summary_(.+?)_(\d{4}-\d{2}-\d{2})_(\d{6})(?:\s*\(\d+\))?\.xlsx?$', re.I)

# (key, column position, exact four-row header tuple) as the 10-Nov-2026 export prints it
COLS = [
    ('tgt', 3, ('Household Target (Planning)',) * 3 + ('n',)),
    ('ucs', 4, ('Total UCs',) * 3 + ('n',)),
    ('vac', 5, ('Household Children Vaccinated', 'Total', 'Total', 'n')),
    ('pct', 6, ('Household Children Vaccinated', '% among HH Target', '% among HH Target', '%')),
    ('rna', 7, ('Recorded Missed Children (based on HH Target)',) * 2 + ('NA', 'n')),
    ('rrf', 8, ('Recorded Missed Children (based on HH Target)',) * 2 + ('Ref', 'n')),
    ('rec', 9, ('Recorded Missed Children (based on HH Target)',) * 2 + ('Total', 'n')),
    ('cna', 10, ('Covered during Campaign',) * 2 + ('NA', 'n')),
    ('crf', 11, ('Covered during Campaign',) * 2 + ('Ref', 'n')),
    ('cam', 12, ('Covered during Campaign',) * 2 + ('Total Covered (NA+Ref)', 'Total')),
    ('ccna', 14, ('Covered during Catchup',) * 2 + ('NA', 'n')),
    ('ccrf', 15, ('Covered during Catchup',) * 2 + ('Ref', 'n')),
    ('cu', 16, ('Covered during Catchup',) * 2 + ('Total Covered (NA+Ref)', 'Total')),
    ('cena', 18, ('Covered Extended CatchUP',) * 2 + ('NA', 'n')),
    ('cerf', 19, ('Covered Extended CatchUP',) * 2 + ('Ref', 'n')),
    ('ex', 20, ('Covered Extended CatchUP',) * 2 + ('Total Covered (NA+Ref)', 'Total')),
    ('sna', 22, ('Still Missed (based on HH Target)',) * 2 + ('Still NA', 'n')),
    ('srf', 23, ('Still Missed (based on HH Target)',) * 2 + ('Still Ref', 'n')),
    ('slo', 24, ('Still Missed (based on HH Target)',) * 2 + ('Still Left Over', 'n')),
    ('stl', 25, ('Still Missed (based on HH Target)',) * 2 + ('Total', 'n')),
    ('stp', 26, ('Still Missed (based on HH Target)',) * 2 + ('Total', '% Out of HH Target')),
    ('zd', 27, ('Zero Routine dose children reported',) * 3 + ('n',)),
    ('zcv', 28, ('Zero Dose Children Covered by Next Round',) * 3 + ('n',)),
    ('afp', 29, ('No. 0f AFP Cases',) * 3 + ('n',)),
    ('vials', 30, ('Received Vials for Campaign',) * 3 + ('n',)),
    ('sealed', 31, ('Remaining Sealed Usable Vials',) * 3 + ('n',)),
]
ALT = {
    28: ('Zero Dose Children Covered before Next Round',) * 3 + ('n',),
    29: ('No. of AFP Cases',) * 3 + ('n',),   # the 10-Nov export typed "0f"
}
KEYS = ['div', 'd', 'di'] + [c[0] for c in COLS]
PCT = ('pct', 'stp')
# columns that must re-add from the district rows (percent columns are recomputed, not summed)
ADDITIVE = ['tgt', 'ucs', 'vac', 'rna', 'rrf', 'rec', 'cna', 'crf', 'cam', 'ccna', 'ccrf', 'cu',
            'cena', 'cerf', 'ex', 'sna', 'srf', 'slo', 'stl', 'zd', 'zcv', 'afp', 'vials', 'sealed']


def dn_names(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const INDIC = ')
    j = s.find('\n', i)
    obj = json.loads(s[i + len('const INDIC = '):j].rstrip().rstrip(';'))
    return obj['dn']


def find_summary(cfg):
    """The newest SNID Nov summary export among the registered roots."""
    best = None
    for rec in srcutil.discover(cfg['auto']['novf']):
        m = NAME_RE.match(rec['name'])
        if not m or 'NOV' not in m.group(1).upper():
            continue
        when = m.group(2) + ' ' + m.group(3)
        if best is None or when > best[0]:
            best = (when, rec['path'])
    if not best:
        raise SystemExit('ERR novf no SNID Nov summary export among the registered roots')
    return best[1]


def num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def fnum(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--path')
    ap.add_argument('--out')
    ap.add_argument('--live', action='store_true',
                    help='table was serialised from the live District-Wise page because the '
                         'Export button returned province grain; recorded in the payload source')
    a = ap.parse_args(argv)
    cfg = srcutil.load_sources()
    repo = cfg['repo']
    path = a.path or find_summary(cfg)
    print('SRC novf %s' % path)

    m = NAME_RE.match(os.path.basename(path))
    if not m:
        raise SystemExit('ERR novf unrecognised filename %s' % os.path.basename(path))
    camp, asof = m.group(1).strip(), m.group(2)

    d = pd.read_html(path, header=[0, 1, 2, 3])[0]
    if d.shape[1] != 32:
        raise SystemExit('ERR novf expected 32 columns, got %d' % d.shape[1])
    for key, pos, want in COLS:
        got = tuple(re.sub(r'\s+', ' ', str(x)).strip() for x in d.columns[pos])
        # the portal relabelled zcv from "by Next Round" to "before Next Round" on 11-Nov-2026;
        # the column position and units are unchanged, so both labels are accepted
        labels = {tuple(x.lower() for x in want),
                  tuple(x.lower() for x in ALT.get(pos, want))}
        # the portal also changed "CatchUP" to "Catchup" between exports
        if tuple(x.lower() for x in got) not in labels:
            raise SystemExit('ERR novf column %d is not %s: %r' % (pos, key, got))
    dn = dn_names(repo)
    idx = {n.upper(): i for i, n in enumerate(dn)}

    def di_of(name):
        n = re.sub(r'\s+', ' ', str(name)).strip().upper()
        if n in idx:
            return idx[n]
        # the export upper-cases the two Wazir-S successor districts
        for cand in (n.title(), n.replace(' LOWER', ' Lower'), n.replace(' UPPER', ' Upper')):
            if cand.upper() in idx:
                return idx[cand.upper()]
        raise SystemExit('ERR novf district %r not in the dashboard district list' % name)

    rows, tot = [], None
    for _, r in d.iterrows():
        name = re.sub(r'\s+', ' ', str(r.iloc[2])).strip()
        vals = {c[0]: (fnum(r.iloc[c[1]]) if c[0] in PCT else num(r.iloc[c[1]])) for c in COLS}
        if str(r.iloc[0]).strip().upper() == 'TOTAL' or name == '-':
            if tot is not None:
                raise SystemExit('ERR novf more than one totals row')
            tot = vals
            continue
        if not name or name.lower() == 'nan':
            continue
        rows.append([str(r.iloc[1]).strip(), name, di_of(name)]
                    + [vals[c[0]] for c in COLS])

    if len(rows) != 27:
        raise SystemExit('ERR novf expected 27 district rows, got %d' % len(rows))
    if not tot:
        raise SystemExit('ERR novf totals row not found')

    # derived figures must reconcile from their own counts
    rec = tot['rec'] or 0
    covered = (tot['cam'] or 0) + (tot['cu'] or 0) + (tot['ex'] or 0)
    for lo, hi, s in (('cna', 'crf', tot['cam']), ('ccna', 'ccrf', tot['cu']),
                      ('cena', 'cerf', tot['ex'])):
        if (tot[lo] or 0) + (tot[hi] or 0) != (s or 0):
            raise SystemExit('ERR novf %s + %s does not equal %s' % (lo, hi, s))
    # recorded missed = covered in all three phases + still NA/Ref; left-over children were never
    # recorded, so they widen the still-missed total without belonging to the recorded list
    if covered + (tot['sna'] or 0) + (tot['srf'] or 0) != rec:
        raise SystemExit('ERR novf recorded / covered / still missed do not reconcile: %s + %s + %s'
                         % (covered, (tot['sna'] or 0) + (tot['srf'] or 0), rec))
    for x in [dict(zip(KEYS[3:], row[3:])) for row in rows] + [tot]:
        if (x['sna'] or 0) + (x['srf'] or 0) + (x['slo'] or 0) != (x['stl'] or 0):
            raise SystemExit('ERR novf still-missed parts do not add to %s' % (x['stl'],))
    for key in ADDITIVE:
        s = sum((x[KEYS.index(key)] or 0) for x in rows)
        if tot[key] != s:
            raise SystemExit('ERR novf totals row does not re-add %s: file %s vs rows %s'
                             % (key, tot[key], s))

    src = ('EOC portal summary coverage export, %s, district-grain final close-out read %s'
           % (camp, asof))
    if a.live:
        src += (' (serialised from the live District-Wise table on the same portal page; the '
                'Export button returned province grain)')
    payload = {
        'src': src,
        'camp': camp, 'asof': asof, 'k': KEYS,
        'u': rows,
        'tot': [tot[c[0]] for c in COLS],
    }
    js = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    out = a.out or os.path.join(srcutil.OUT, 'novf.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(js + '\n')
    print('OK novf %d %d districts · target %s · vaccinated %s (%s%%) · recorded %s · covered %s '
          '(%.2f%%) · still missed %s (%.2f%%) · ZD %s'
          % (len(js), len(rows), '{:,}'.format(tot['tgt']), '{:,}'.format(tot['vac']), tot['pct'],
             '{:,}'.format(rec), '{:,}'.format(covered), covered / rec * 100,
             '{:,}'.format(tot['stl']), tot['stp'], '{:,}'.format(tot['zd'])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
