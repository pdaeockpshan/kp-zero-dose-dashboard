"""Rebuild the UC-level routine EPI payload (const EPI) from a KP EPI-MIS year-to-date
coverage export, and produce the dated metadata payload (const EPIYTD).

The export is the UC-wise 'Consolidated Facility Wise Vaccination of Children and Women'
report opened for a period (e.g. 2026-01 - 2026-09) with Report Type = all_ucs. It is an
HTML table saved as .xls.

This script never invents UC identities: every row must already exist in the embedded EPI
payload with the same Union Council name and district, so the polio UC matching (mt, c, zr,
zp) stays exactly as reviewed. Run the monthly archive extractors (epm/epim) separately -
a year-to-date file cannot prove anything about individual months.

  python _refresh/extract_epi_ytd.py --out _refresh/out/epi_ytd.json
  python _refresh/extract_epi_ytd.py --source "C:\\path\\to\\file.xls" --out ... --meta-out ...
"""
import argparse
import datetime
import io
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import epi_ag
import srcutil

AG = epi_ag.AG  # (key, source column, label, target, core) - the shared EPI panel
TN, TS = 'Target Newborns', 'Target Surviving Infants'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
BAD_DISTRICT = {'0', '', 'NAN', 'NA'}


def _mo(label):
    y, m = label.split('-')
    return '%s %s' % (MONTHS[int(m) - 1], y)


def read_export(path):
    """(table, (from, to), [(key, source column)]) from the UC-wise HTML-table export."""
    raw = open(path, 'rb').read()
    head = re.sub(r'<[^>]+>', ' ', raw[:20000].decode('utf-8', 'replace'))
    per = re.search(r'Period:\s*(\d{4}-\d{2})\s*-\s*(\d{4}-\d{2})', head)
    if not per:
        raise SystemExit('ABORT: no "Period: YYYY-MM - YYYY-MM" header found in %s' % os.path.basename(path))
    t = max(pd.read_html(io.BytesIO(raw)), key=len)
    t.columns = [' '.join(dict.fromkeys(str(x) for x in c)) for c in t.columns]
    t.columns = [str(c).strip() for c in t.columns]
    need = ['S No.', 'District', 'Tehsil', 'Union Council', 'Uncode', TN, TS] \
           + [a[1] for a in AG if a[4]]
    miss = [c for c in need if c not in t.columns]
    if miss:
        raise SystemExit('ABORT: export layout changed, missing ' + ', '.join(miss))
    # optional doses are read only when this export carries them - a slimmer file must
    # not block the refresh, the dashboard shows those meters as having no data.
    have = [(a[0], a[1]) for a in AG if a[1] in t.columns]
    skipped = [a[2] for a in AG if a[1] not in t.columns and not a[4]]
    if skipped:
        print('  note: export has no %s columns - those doses stay unpublished'
              % ', '.join(skipped))
    # the total/footer row only looks like a UC after the colspan flattening shifts numbers
    # left - the serial number is the one column that cannot be shifted into.
    t['S No.'] = pd.to_numeric(t['S No.'], errors='coerce')
    t = t[t['S No.'].notna()].copy()
    t['Uncode'] = t['Uncode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    if t['Uncode'].duplicated().any():
        raise SystemExit('ABORT: duplicate Uncode values in the export')
    return t, (per.group(1), per.group(2)), have


def _num(x, what):
    v = pd.to_numeric(x, errors='coerce')
    if pd.isna(v):
        raise SystemExit('ABORT: %s is blank for %s' % (what, x))
    v = int(round(float(v)))
    if v < 0:
        raise SystemExit('ABORT: negative value (%s = %d)' % (what, v))
    return v


def build(source, base_rows):
    t, (pfrom, pto), agc = read_export(source)
    named = lambda v: str(v).strip().upper() not in BAD_DISTRICT

    blank = t[~t['District'].apply(named)].copy()
    ok = t[t['District'].apply(named)].copy()
    if len(blank):
        for c in [TN, TS] + [col for _, col in agc]:
            blank[c] = pd.to_numeric(blank[c], errors='coerce').fillna(0)
            if float(blank[c].max()) > 0:
                raise SystemExit('ABORT: %d row(s) without a district carry %s - cannot place them'
                                 % (len(blank), c))
        print('  note: excluded %d rows with no district (%s), all zero-valued'
              % (len(blank), ', '.join(sorted(str(x) for x in blank['Uncode']))))
    if len(ok) < 200:
        raise SystemExit('ABORT: export has only %d usable UC rows' % len(ok))

    base = {r['ec']: r for r in base_rows}
    fresh = {}
    for _, x in ok.iterrows():
        ec = x['Uncode']
        d0 = str(x['District']).strip()
        r = base.get(ec)
        if r is None:
            raise SystemExit('ABORT: UC code %s (%s / %s) is not in the embedded EPI payload - '
                             'new UCs need polio matching first' % (ec, d0, x['Union Council']))
        if str(x['Union Council']).strip().upper() != str(r['en']).upper() or d0 != r['ed']:
            raise SystemExit('ABORT: UC %s changed identity (%s / %s vs stored %s / %s) - '
                             're-check the polio matching before publishing'
                             % (ec, d0, x['Union Council'], r['ed'], r['en']))
        row = dict(r)  # keep dv/d/t/u/c/en/ec/ed/mt (and zr/zp) exactly as reviewed
        for k in epi_ag.KEYS:
            row.pop(k, None)  # never carry a last-period dose forward as if it were current
        row['n'] = _num(x[TN], '%s / %s' % (ec, TN))
        row['s'] = _num(x[TS], '%s / %s' % (ec, TS))
        for k, col in agc:
            row[k] = _num(x[col], '%s / %s' % (ec, col))
        fresh[ec] = row

    gone = [ec for ec in base if ec not in fresh]
    if gone:
        raise SystemExit('ABORT: %d UCs present in the dashboard are missing from the export '
                         '(first: %s)' % (len(gone), ', '.join(gone[:5])))

    rows = [fresh[r['ec']] for r in base_rows]
    tot = {k: sum(r[k] for r in rows) for k, _ in agc}
    tot['n'] = sum(r['n'] for r in rows)
    tot['s'] = sum(r['s'] for r in rows)
    rec = srcutil.stat_rec(source)
    meta = {
        'per': '%s - %s' % (_mo(pfrom), _mo(pto)),
        'from': pfrom, 'to': pto,
        'asof': datetime.date.fromtimestamp(rec['mtime']).isoformat(),
        'got': srcutil.mtime_str(rec),
        'src': rec['name'],
        'ucs': len(rows), 'dists': len(set(r['ed'] for r in rows)),
        'excluded': int(len(blank)), 'matched': sum(1 for r in rows if r.get('mt')),
    }
    return rows, meta, tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, help='JSON file for the EPI array')
    ap.add_argument('--meta-out', help='JSON file for the EPIYTD metadata (default: <out>.meta.json)')
    ap.add_argument('--source', help='UC-wise YTD export; default: newest match under the configured roots')
    a = ap.parse_args()

    rec = srcutil.stat_rec(a.source) if a.source else \
        srcutil.newest(srcutil.load_sources()['manual']['epi'])
    if not rec:
        raise SystemExit('ABORT: no UC-wise export found; pass --source')
    source = rec['path']
    _, vs = dashpatch.load_variants()
    base_rows = json.loads(dashpatch.get_payload(vs[0].text, 'EPI').replace('<\\/', '</'))
    print('source: %s (%s bytes, saved %s)'
          % (source, format(rec['size'], ','), srcutil.mtime_str(rec)))
    print('embedded EPI rows: %d' % len(base_rows))
    rows, meta, tot = build(source, base_rows)

    old = {k: sum(r.get(k) or 0 for r in base_rows) for k in list(tot)}
    print('')
    print('%-6s %12s %12s %10s' % ('field', 'new', 'embedded', 'delta'))
    for k in ['n', 's'] + [x for x in list(tot) if x not in ('n', 's')]:
        print('%-6s %12s %12s %10s' % (k, format(tot[k], ','), format(old[k], ','),
                                       format(tot[k] - old[k], '+,d')))
    print('coverage-derived dropouts: Penta-1->3 %.1f%%, MR-1->2 %.1f%%, IPV-1->2 %.1f%%'
          % ((tot['p1'] - tot['p3']) / tot['p1'] * 100, (tot['mr1'] - tot['mr2']) / tot['mr1'] * 100,
             (tot['ipv1'] - tot['ipv2']) / tot['ipv1'] * 100))

    meta_js = srcutil.dumps(meta)
    rows_js = srcutil.dumps(rows)
    srcutil.write_text(a.out, rows_js)
    meta_out = a.meta_out or (os.path.splitext(a.out)[0] + '.meta.json')
    srcutil.write_text(meta_out, meta_js)
    print('OK epi %s rows, %s districts, period %s (source %s, excluded %d zero rows without a district)'
          % (format(meta['ucs'], ','), meta['dists'], meta['per'], meta['src'], meta['excluded']))
    print('wrote %s (%s chars) and %s (%s chars)'
          % (a.out, format(len(rows_js), ','), meta_out, format(len(meta_js), ',')))


if __name__ == '__main__':
    main()
