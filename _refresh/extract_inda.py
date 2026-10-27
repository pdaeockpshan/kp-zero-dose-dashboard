# -*- coding: utf-8 -*-
"""Supplement the campaign data pack's Admin table with SNID Sept 2026.

The EOC compiled-indicators export (`Indicators to be included in dashboard as
record.csv`) still ends at SNID May 2026, so the data pack's campaign picker has
no Sept option. The EOC summary coverage report (UC-wise, one file per round -
`cov_SNID Sept 2026.xls` as saved from the portal, or the direct
`summary_SNID Sept 2026_<date>_<time>.xls` export) carries the admin coverage and
missed-children fields for that round.

The same name pattern also arrives district-wise (province / division / district plus one measure
column, as on 26-Oct-2026). Shape decides which file is read, so the newest file on disk is not
necessarily the one used, and every file skipped for shape is printed as
`SKIP inda <name>: <reason>` for refresh.py to credit the real source. The district-wise cut is not
new information: its zero-dose reported column reproduces this file's own district roll-up exactly.

Payload `const INDA`:
  camp  campaign label
  asof  coverage report date
  n     UC rows
  dn/teh/ucs  directory entries that do not exist in INDIC (BAR SWAT split)
  dd    district rows keyed by absolute district index (INDIC.dn + this dn)
  uu    [ucIndex, [21 admin values]] with ucIndex absolute (INDIC.ucs + this ucs)

Columns follow INDIC.S.admin.k (21 values - the Sept report has no MP-target,
same-day-coverage, guest, HRMP-mobile or school figures, so those stay -1 = not
reported; the report's new "Zero Dose Covered" column has no slot in that key list
and is carried by ZD/ADV instead). Total Adm Covered and AdmTotalCoverage % use the
report's household children vaccinated, the same coverage definition as the Missed
children tab.

Usage: python _refresh/extract_inda.py [--source PATH] [--out PATH]
Prints: SRC inda cov <path> | OK inda <chars> <summary> | ERR inda <reason>
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import covsept
import srcutil

DS = 'inda'
INDIC = os.path.join(srcutil.OUT, 'indic.json')

# admin value slots, in INDIC.S.admin.k order
ADMIN_N = 21


def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def code(v):
    s = str(v).strip()
    return s[:-2] if s.endswith('.0') else s


def r1(v):
    return round(v, 1) if v is not None else -1


def load_indic():
    with open(INDIC, encoding='utf-8') as fh:
        return json.load(fh)


def s(rows, key):
    return sum(r[key] or 0 for r in rows)


def admin_vals(rows):
    tgt, hh, rmiss = s(rows, 'tgt'), s(rows, 'vacc'), s(rows, 'rtot')
    rna, rrf = s(rows, 'rna'), s(rows, 'rrf')
    sna, srf, still = s(rows, 'sna'), s(rows, 'srf'), s(rows, 'stot')
    cover = 100.0 * hh / tgt if tgt else None
    return [
        tgt, hh, r1(cover), -1, hh, r1(cover), -1,
        rna, rrf, rmiss, sna, srf, still, -1,
        r1(100.0 * still / rmiss) if rmiss else -1,
        r1(100.0 * still / tgt) if tgt else -1,
        -1, -1, -1, s(rows, 'zrep'), s(rows, 'afp'),
    ]


def build(path):
    ind = load_indic()
    dn = list(ind['dn'])
    teh = list(ind['teh'])
    ucs = [list(u) for u in ind['ucs']]
    dmap = {norm(x): i for i, x in enumerate(dn)}
    tmap = {norm(x): i for i, x in enumerate(teh)}
    cmap = {}
    for i, u in enumerate(ucs):
        cmap.setdefault(code(u[3]), i)

    book = covsept.read(path)
    rows = book['uc']
    if not rows:
        raise SystemExit('ERR inda no UC rows in %s' % path)

    extra_d, extra_t, extra_u = [], [], []
    district_bucket, uc_rows = {}, []
    for r in rows:
        dname, tname, uname, ucode = r['dist'], r['teh'], r['uc'], r['code']
        if norm(dname) in dmap:
            di = dmap[norm(dname)]
        else:
            if dname not in extra_d:
                extra_d.append(dname)
            di = len(dn) + extra_d.index(dname)
        if norm(tname) in tmap:
            ti = tmap[norm(tname)]
        else:
            if tname not in extra_t:
                extra_t.append(tname)
            ti = len(teh) + extra_t.index(tname)
        if ucode in cmap:
            ui = cmap[ucode]
        else:
            hit = next((i for i, u in enumerate(ucs)
                        if norm(u[0]) == norm(uname) and u[1] == di and u[2] == ti), None)
            if hit is None:
                key = (uname, di, ti, ucode)
                if key not in [tuple(x) for x in extra_u]:
                    extra_u.append([uname, di, ti, ucode])
                ui = len(ucs) + [tuple(x) for x in extra_u].index(key)
            else:
                ui = hit
                ucode = ucs[ui][3]
        district_bucket.setdefault(di, []).append(r)
        uc_rows.append((ui, r))

    # one row per UC; a duplicate absolute index means the directory already had it
    seen = set()
    for ui, r in uc_rows:
        if ui in seen:
            raise SystemExit('ERR inda duplicate UC row %r (%s)' % (ui, r['uc']))
        seen.add(ui)

    dd = {str(di): admin_vals(rs) for di, rs in sorted(district_bucket.items())}
    uu = [[ui, admin_vals([r])] for ui, r in uc_rows]
    for k, v in list(dd.items()) + list(uu):
        if len(v) != ADMIN_N:
            raise SystemExit('ERR inda admin row %s has %d values, expected %d' % (k, len(v), ADMIN_N))

    mt = datetime.datetime.fromtimestamp(os.path.getmtime(book['file']))
    p = {
        'camp': {'l': 'SNID Sept 2026', 'y': '2026'},
        'asof': mt.date().isoformat(),
        'src': os.path.basename(path),
        'n': len(uc_rows),
        'dn': extra_d,
        'teh': extra_t,
        'ucs': extra_u,
        'dd': dd,
        'uu': uu,
    }
    # invariants against the workbook's own totals row
    tot = book['tot']
    if tot:
        want = (tot['tgt'], tot['vacc'], tot['rna'], tot['rrf'], tot['stot'])
        got = (sum(v[0] for v in dd.values()), sum(v[1] for v in dd.values()),
               sum(v[7] for v in dd.values()), sum(v[8] for v in dd.values()),
               sum(v[12] for v in dd.values()))
        if want != got:
            raise SystemExit('ERR inda totals %r != workbook %r' % (got, want))
    else:
        raise SystemExit('ERR inda workbook totals row not found in %s' % book['file'])
    notes = covsept.check_totals(book['uc'], tot, ['zrep', 'afp', 'rtot'])
    for n in notes:
        print('WARN inda %s' % n)
    summary = ('%d UCs, %d districts, target %s, vaccinated %s, still missed %s, ZD reported %s'
               % (len(uu), len(dd), format(sum(v[0] for v in dd.values()), ','),
                  format(sum(v[1] for v in dd.values()), ','),
                  format(sum(v[12] for v in dd.values()), ','),
                  format(sum(v[19] for v in dd.values()), ',')))
    return p, summary


def _uc_rows(path):
    try:
        return len(covsept.read(path)['uc'])
    except SystemExit as e:
        print('SKIP inda %s: %s' % (os.path.basename(path), str(e).strip()))
    except Exception as e:
        print('SKIP inda %s: unreadable (%s)' % (os.path.basename(path), e))
    return 0


def pick(source, entry):
    """Newest file that really carries UC rows, naming every skip.

    The portal saves one round in two shapes under the same name pattern - the UC-wise table this
    payload needs and a district-wise roll-up of it. Newest-mtime-wins alone would abort the run on the
    roll-up or credit it in state.json, so the shape decides and each rejected file is named.
    """
    probed = set()
    if source:
        probed.add(os.path.normcase(source))
        if _uc_rows(source):
            return srcutil.stat_rec(source)
    for cand in srcutil.discover(entry):
        if os.path.normcase(cand['path']) in probed:
            continue
        if _uc_rows(cand['path']):
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = pick(a.source, cfg['auto'][DS])
    if not rec:
        raise SystemExit('ERR inda no UC-wise coverage report found under %s' % cfg['auto'][DS]['roots'])
    payload, summary = build(rec['path'])
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'inda.json')
    srcutil.write_text(dest, js)
    print('SRC inda cov %s' % rec['path'])
    print('OK inda %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
