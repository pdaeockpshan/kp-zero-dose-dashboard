"""Build the routine-dropout payload (const EPIDROP) from the KP EPI-MIS "Dropouts Report"
export (district level, one row per district plus a province Total row).

The report publishes dropout % per district for five dose pairs, split by sex (TT-1 -> TT-2 by
PLW / CBA). These are the programme's own published rates and are kept exactly as reported -
including negative values, which mean more later doses than first doses (catch-up of older
children). Do NOT average them up to a division or a multi-district scope: the report carries
no denominators, so only its own Total row can stand for all KP.

The dashboard's own Penta-1->3 / MR-1->2 columns are different arithmetic: they are computed
from the UC-level doses given in const EPI, so they follow the division/district filters and
can drill down to UCs. Where the two disagree the page shows both rather than blending them.

  python _refresh/extract_epi_drop.py --out _refresh/out/epi_drop.json
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
import srcutil

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# payload key -> the report's column stem and the label used on the page
GROUPS = [('p1m1', 'Penta1-MR-1', 'Penta-1 → MR-1'), ('p1p3', 'Penta1-Penta3', 'Penta-1 → Penta-3'),
          ('mr12', 'MR-1-MR-2', 'MR-1 → MR-2'), ('tt12', 'TT1-TT2', 'TT-1 → TT-2'),
          ('ipv', 'IPV1-IPV2', 'IPV-1 → IPV-2')]
TOTAL_ROW = 'TOTAL:'


def _mo(label):
    y, m = label.split('-')
    return '%s %s' % (MONTHS[int(m) - 1], y)


def _pct(v, col, who):
    x = pd.to_numeric(v, errors='coerce')
    if pd.isna(x):
        raise SystemExit('ABORT: %s blank for %s' % (col, who))
    return int(round(float(x)))


def read_report(path):
    raw = open(path, 'rb').read()
    head = re.sub(r'<[^>]+>', '\n', raw[:20000].decode('utf-8', 'replace'))
    per = re.search(r'Period:?\s*(\d{4}-\d{2})\s*-\s*(\d{4}-\d{2})', head, re.I)
    typ = re.search(r'Report Type:\s*(\S{2,40})', head)
    t = max(pd.read_html(io.BytesIO(raw)), key=len)
    t.columns = [' '.join(dict.fromkeys(str(x) for x in c)) for c in t.columns]
    t.columns = [str(c).strip() for c in t.columns]
    if 'District Name' not in t.columns:
        raise SystemExit('ABORT: %s has no "District Name" column - layout changed' % os.path.basename(path))
    cols = {}
    for c in t.columns:
        for key, stem, _ in GROUPS:
            if c.startswith(stem):
                cols.setdefault(key, []).append(c)
    for key, stem, _ in GROUPS:
        got = cols.get(key) or []
        if len(got) != 3:
            raise SystemExit('ABORT: expected 3 "%s" columns, found %d (%s)' % (stem, len(got), got))
    return t, cols, (per.group(1), per.group(2)) if per else (None, None), (typ.group(1) if typ else '')


def build(source, epi_rows):
    t, cols, (pfrom, pto), rtype = read_report(source)
    place = {}
    for r in epi_rows:
        place.setdefault(r['ed'], (set(), r['dv']))[0].add(r['d'])
    rows, kp = [], None
    for _, x in t.iterrows():
        name = str(x['District Name']).strip()
        if not name or name.upper() == 'DISTRICT NAME':
            continue
        vals = {k: [_pct(x[c], c, name) for c in cols[k]] for k, _, _ in GROUPS}
        if name.upper() == TOTAL_ROW:
            kp = vals
            continue
        if name not in place:
            raise SystemExit('ABORT: dropout report district "%s" is not in the EPI-MIS district list' % name)
        ds, dv = place[name]
        rows.append(dict(vals, ed=name, code=str(x['District Code']).strip(), dv=dv, ds=sorted(ds)))
    if kp is None:
        raise SystemExit('ABORT: no "Total:" row found in the dropout report')
    if len(rows) < 20:
        raise SystemExit('ABORT: only %d district rows parsed' % len(rows))
    rec = srcutil.stat_rec(source)
    meta = {'per': '%s - %s' % (_mo(pfrom), _mo(pto)) if pfrom else '', 'from': pfrom, 'to': pto,
            'asof': datetime.date.fromtimestamp(rec['mtime']).isoformat(), 'got': srcutil.mtime_str(rec),
            'src': rec['name'], 'dists': len(rows), 'type': rtype}
    return {'g': [[k, lab] for k, _, lab in GROUPS], 'm': meta, 'rows': rows, 'kp': kp}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--source', help='default: newest Dropouts_Report*.xls in the configured roots')
    a = ap.parse_args()
    rec = srcutil.stat_rec(a.source) if a.source else \
        srcutil.newest(srcutil.load_sources()['manual']['epidrop'])
    if not rec:
        raise SystemExit('ABORT: no dropout report found; pass --source')
    _, vs = dashpatch.load_variants()
    epi = json.loads(dashpatch.get_payload(vs[0].text, 'EPI').replace('<\\/', '</'))
    payload = build(rec['path'], epi)
    js = srcutil.dumps(payload)
    srcutil.write_text(a.out, js)
    kp = payload['kp']
    top = sorted(payload['rows'], key=lambda r: -r['p1p3'][2])[:3]
    print('OK epidrop %s districts, period %s (source %s): report KP totals Penta-1->3 %s%%, '
          'MR-1->2 %s%%, IPV-1->2 %s%%, TT-1->2 %s%%; highest Penta-1->3 %s'
          % (payload['m']['dists'], payload['m']['per'], payload['m']['src'],
             kp['p1p3'][2], kp['mr12'][2], kp['ipv'][2], kp['tt12'][2],
             ', '.join('%s %s%%' % (r['ed'], r['p1p3'][2]) for r in top)))
    print('wrote %s (%s chars)' % (a.out, format(len(js), ',')))


if __name__ == '__main__':
    main()
