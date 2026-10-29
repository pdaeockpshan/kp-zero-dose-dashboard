# -*- coding: utf-8 -*-
"""Read the owner's district/UC campaign-indicator workbook into const CIN.

`Khyber Pakhtunkhwa District and UCs Wise Campaign Indicators.xlsx` has one tab per grain
(`District Wise`, `UC Wise`) and four 2026 rounds in each. Three of those rounds are the compiled
portal export the dashboard already carries - Feb/Apr/May 2026 reproduce `INDIC` row for row at both
grains - and the Sept-26 admin block reproduces `INDA` exactly. What the workbook really adds is
SNID Sept 2026 with the ICM and LQAS columns standing beside the admin ones, at district and UC
grain: the data pack keeps those in three separate tables and has no Sept-26 row for them.

Only that round is emitted. Earlier rounds stay in `INDIC` and are merged into the same 17 columns
at render time, so the one-plate table and the data pack can never disagree, and no second copy of
95 campaigns is pushed into the page.

The two tabs do not carry the same columns: the UC tab has no ICM TVBCM, the district tab no ICM
Total Missed, so each holds 16 of the 17. A row therefore keeps -1 in the slot its tab lacks, and the
page leaves a column out (writing which one into its caption) when no campaign in the selection
reports it.

The workbook is not consistent inside itself, so the unit of each block is declared here and then
proved against the payloads the dashboard already trusts (`check_*` below aborts the run on any
disagreement):

  District tab   Feb/Apr/May  SM%, ICM%, LQAS% are fractions       x100
  District tab   Sept          already percent                      x1
  UC tab         Feb/Apr/May   SM%, ICM%, LQAS% are fractions       x100
  UC tab         Sept          SM% is percent, ICM%/LQAS% fractions x1 / x100

Layout. District rows are keyed by absolute district index (`INDIC.dn` + `INDA.dn`), UC rows by
absolute UC index (`INDIC.ucs` + `INDA.ucs`), matching how `INDA` already addresses the BAR SWAT UCs.

Usage: python _refresh/extract_cin.py [--source PATH] [--out PATH]
Prints: SRC cin wb <path> | NOTE cin uc ... (a row the workbook keeps but the portal cannot match)
        | OK cin <json chars> <summary> | ERR cin <reason>
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'cin'
SHEET_D = 'District Wise'
SHEET_U = 'UC Wise'
NEW = 'SNID Sept 2026'
OLD = ('NID FEB 2026', 'NID APR 2026', 'SNID May 2026')

# The workbook's own column order, which is the order the owner reads. The UC tab carries all 17;
# the district tab carries all of them except ICM Total Missed (asserted in build()).
COLS = [('Administrative Target', 'n'), ('Adm HH Coverage', 'n'), ('HH %of Total MP', 'p'),
        ('Adm Still NA', 'n'), ('Adm Still Refusal', 'n'), ('Still Leftover', 'n'),
        ('SM % of Target', 'p'), ('ICM Recall %', 'p'),
        ('ICM Total Missed', 'n'), ('ICM Team No Visit', 'n'), ('ICM TVBCM', 'n'),
        ('Pass', 'n'), ('Intermediate', 'n'), ('Fail', 'n'), ('LQAS Pass %', 'p'),
        ('LQAS_NT', 'n'), ('LQAS_TVBMC', 'n')]
PCT = {'SM % of Target', 'ICM Recall %', 'LQAS Pass %'}
# Blocks whose percent columns are already in percent and must not be scaled.
PERCENT_ASIS = {(SHEET_D, NEW): set(PCT),
                (SHEET_U, NEW): {'SM % of Target'}}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def hdr(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(',', '').strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def scale(tab, camp, col):
    if col not in PCT:
        return 1.0
    return 1.0 if col in PERCENT_ASIS.get((tab, camp), ()) else 100.0


def read_sheet(wb, name):
    it = wb[name].iter_rows(values_only=True)
    head = [hdr(h) for h in next(it)]
    out, last = [], None
    for r in it:
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in r):
            continue
        d = dict(zip(head, r))
        c = d.get('Campaign')
        last = str(c).strip() if c is not None and str(c).strip() else last
        d['Campaign'] = last
        out.append(d)
    return head, out


def record(d, tab, camp):
    o = {}
    for c, t in COLS:
        v = num(d.get(c))
        if v is None:
            o[c] = -1
        elif t == 'p':
            o[c] = round(v * scale(tab, camp, c), 1)
        else:
            o[c] = int(round(v))
    return o


def const(text, name):
    i = text.find('const %s = ' % name)
    if i < 0:
        raise SystemExit('ERR cin const %s not found in index.html' % name)
    j = text.find('\n', i)
    raw = text[i + len('const %s = ' % name):j].rstrip().rstrip(';').replace('<\\/', '</')
    return json.loads(raw)


def section(indic, key, col):
    cols = [c[0] for c in indic['S'][key]['k']]
    return cols.index(col) if col in cols else -1


def merged(indic, ix, ci, di=None, key=None, uckey=None):
    """The 17 columns for one INDIC row - the same merge the page's renderer performs.

    Older rounds keep target/coverage in the admin table, ICM in its own and LQAS in a third, so a
    single row means reading across three sections. Still Leftover is not a portal column at all: it
    is the part of still-missed that is neither NA nor refusal. District rows are addressed by index;
    UC rows by (district, name), because the workbook and the portal directory number the odd UC
    differently.
    """
    def vals(st):
        s = indic['S'][st]
        if key is not None:
            for p in s['uu'].get(str(ci)) or []:
                if uckey(p[0]) == key:
                    return p[1]
            return []
        return (s['dd'].get(str(ci)) or {}).get(str(di)) or []
    A, I, L = vals('admin'), vals('icm'), vals('lqas')
    out = []
    for c, t in COLS:
        if c == 'Still Leftover':
            if len(A) <= max(ix['sm'], ix['na'], ix['ref']):
                out.append(-1)
                continue
            sm, n, r = A[ix['sm']], A[ix['na']], A[ix['ref']]
            out.append(sm - n - r if sm > -1 and n > -1 and r > -1 else -1)
            continue
        sec, j = ix['map'].get(c, (None, -1))
        v = {'admin': A, 'icm': I, 'lqas': L}.get(sec)
        out.append(v[j] if v is not None and len(v) > j else -1)
    return out


def index_map(indic):
    cols = {s: [c[0] for c in indic['S'][s]['k']] for s in indic['S']}
    m = {}
    for c, t in COLS:
        if c == 'Still Leftover':
            continue
        for s in ('admin', 'icm', 'lqas'):
            if c in cols[s]:
                m[c] = (s, cols[s].index(c))
                break
    return {'map': m,
            'na': cols['admin'].index('Adm Still NA'),
            'ref': cols['admin'].index('Adm Still Refusal'),
            'sm': cols['admin'].index('Adm Still Missed')}


def cmp_v(a, b):
    if a == -1 or b in (None, -1):
        return None
    return abs(a - b)


def check(title, pairs, tol=0.51):
    """Abort on any row the workbook and the existing payload disagree about."""
    bad = []
    n = 0
    for label, mine, theirs in pairs:
        d = cmp_v(mine, theirs)
        if d is None:
            continue
        n += 1
        if d > tol:
            bad.append((label, mine, theirs))
    if bad:
        raise SystemExit('ERR cin %s: %d of %d rows disagree, first %s' % (title, len(bad), n, bad[:4]))
    return n


def build(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for name in (SHEET_D, SHEET_U):
        if name not in wb.sheetnames:
            raise SystemExit('ERR cin workbook has no %r tab' % name)
    hd, D = read_sheet(wb, SHEET_D)
    hu, U = read_sheet(wb, SHEET_U)

    # The two tabs do not carry the same 17 columns: the district tab has no ICM Total Missed (only
    # the UC tab does), so a district row holds -1 in that slot and the page leaves the column out
    # rather than printing 37 dashes under it. Asserted here so a re-cut of the sheet cannot change
    # the plate silently.
    # Neither tab carries all 17: the district tab has no ICM Total Missed, the UC tab no ICM TVBCM.
    # The slot a tab lacks holds -1, and the page leaves a column out (naming it in the caption) when
    # no campaign in the current selection reports it. Asserted so a re-cut cannot change it silently.
    absent = {'ICM Total Missed': SHEET_D, 'ICM TVBCM': SHEET_U}
    for name, head in ((SHEET_D, hd), (SHEET_U, hu)):
        need = [c for c, t in COLS if absent.get(c) != name]
        missing = [c for c in need if c not in head]
        if missing:
            raise SystemExit('ERR cin %s tab is missing %s' % (name, missing))
        extra = [c for c, tab in absent.items() if tab == name and c in head]
        if extra:
            raise SystemExit('ERR cin the %s tab now carries %s - widen the plate' % (name, extra))

    text = srcutil.read_text(os.path.join(srcutil.repo_root(), 'index.html'))
    indic = json.load(open(os.path.join(srcutil.OUT, 'indic.json'), encoding='utf-8'))
    inda = const(text, 'INDA')

    dn = {norm(x): i for i, x in enumerate(indic['dn'])}
    dnx = {norm(x): len(indic['dn']) + i for i, x in enumerate(inda['dn'])}
    # INDIC.ucs is a growing directory: a UC added late appears again at a higher index (AMANDI is
    # both 0 and 1872). Campaign rows address the first occurrence, so the join must too.
    ucs, ucx = {}, {}
    for i, u in enumerate(indic['ucs']):
        ucs.setdefault((u[1], norm(u[0])), i)
    for i, u in enumerate(inda['ucs']):
        ucx.setdefault((u[1], norm(u[0])), len(indic['ucs']) + i)

    def dist(name):
        k = norm(name)
        return dn.get(k, dnx.get(k))

    def uci(name, di):
        return ucs.get((di, norm(name)), ucx.get((di, norm(name))))

    # ---- golden test 1: the Sept block against INDA (admin columns only, INDA has no ICM/LQAS)
    ia = {c[0]: i for i, c in enumerate(indic['S']['admin']['k'])}
    n = 0
    for r in [x for x in D if x['Campaign'] == NEW]:
        di = dist(r['District'])
        if di is None or str(di) not in inda['dd']:
            raise SystemExit('ERR cin Sept district %r has no INDA row' % r['District'])
        rec = record(r, SHEET_D, NEW)
        v = inda['dd'][str(di)]
        n += check('Sept district ' + str(r['District']),
                   [(c, rec[c], v[ia[c]]) for c in ('Administrative Target', 'Adm HH Coverage',
                                                    'HH %of Total MP', 'Adm Still NA',
                                                    'Adm Still Refusal', 'SM % of Target')])
        left = v[ia['Adm Still Missed']] - v[ia['Adm Still NA']] - v[ia['Adm Still Refusal']]
        if rec['Still Leftover'] not in (-1, left):
            raise SystemExit('ERR cin Sept district %r still-leftover %s, INDA implies %s'
                             % (r['District'], rec['Still Leftover'], left))
    nun = len([x for x in D if x['Campaign'] == NEW])
    if nun != len(inda['dd']):
        raise SystemExit('ERR cin Sept district rows %d, INDA has %d' % (nun, len(inda['dd'])))

    # INDA addresses the Sept UCs by absolute index; the directory repeats some of them, so the
    # join back to the workbook is made on (district, UC name), not on the index.
    def uc_name(i):
        return indic['ucs'][i][0] if i < len(indic['ucs']) else inda['ucs'][i - len(indic['ucs'])][0]

    def uc_dist(i):
        return indic['ucs'][i][1] if i < len(indic['ucs']) else inda['ucs'][i - len(indic['ucs'])][1]

    def uckey(i):
        return (uc_dist(i), norm(uc_name(i)))
    inda_rows = {uckey(p[0]): p[1] for p in inda['uu']}

    hit, unmatched = set(), []
    for r in [x for x in U if x['Campaign'] == NEW]:
        di = dist(r['District'])
        if di is None:
            raise SystemExit('ERR cin Sept UC %r has no district index' % (r['District'],))
        rec = record(r, SHEET_U, NEW)
        k = (di, norm(r['UC_NAME']))
        v = inda_rows.get(k)
        if v is None:
            # The workbook and the Sept summary report carry different UC rosters in a few districts
            # (renamed or newly split UCs). The workbook is the newer roster; its row stands and only
            # the admin columns go uncross-checked for that UC.
            unmatched.append((r['District'], r['UC_NAME']))
            continue
        hit.add(k)
        n += check('Sept UC ' + str(r['UC_NAME']),
                   [(c, rec[c], v[ia[c]]) for c in ('Administrative Target', 'Adm HH Coverage',
                                                    'HH %of Total MP', 'Adm Still NA',
                                                    'Adm Still Refusal', 'SM % of Target')])
    for row in unmatched:
        print('NOTE cin uc %s/%s: not in the Sept summary report, kept from the workbook' % row)

    # ---- golden test 2: Feb/Apr/May against INDIC, which also proves the scaling of each block
    ix = index_map(indic)
    cn = {c['l']: i for i, c in enumerate(indic['camps'])}
    # The workbook's UC tab is grouped by district + UC name; the portal export behind INDIC keeps
    # same-named UCs of different tehsils apart (Bannu carries AMANDI twice). Those keys have no
    # one-to-one partner, so they are counted and skipped instead of being silently tolerated.
    twin = {k for k, v in collections.Counter((u[1], norm(u[0])) for u in indic['ucs']).items()
            if v > 1}
    skipped = 0
    for camp in OLD:
        ci = cn[camp]
        for r in [x for x in D if x['Campaign'] == camp]:
            di = dist(r['District'])
            if di is None or str(di) not in indic['S']['admin']['dd'].get(str(ci), {}):
                continue
            rec = record(r, SHEET_D, camp)
            ref = merged(indic, ix, ci, di)
            n += check('%s district %s' % (camp, r['District']),
                       [(a, rec[a], ref[k]) for a, k in
                        (('Administrative Target', 0), ('Adm Still NA', 3), ('SM % of Target', 6),
                         ('ICM Recall %', 7), ('LQAS Pass %', 14))])
        for r in [x for x in U if x['Campaign'] == camp]:
            di = dist(r['District'])
            if di is None:
                continue
            if (di, norm(r['UC_NAME'])) in twin:
                skipped += 1
                continue
            rec = record(r, SHEET_U, camp)
            ref = merged(indic, ix, ci, key=(di, norm(r['UC_NAME'])), uckey=uckey)
            n += check('%s UC %s' % (camp, r['UC_NAME']),
                       [(a, rec[a], ref[k]) for a, k in
                        (('Administrative Target', 0), ('SM % of Target', 6), ('ICM Recall %', 7))])
    if skipped:
        print('NOTE cin uc %d same-name rows: the workbook groups by district+UC name, '
              'the portal keeps the tehsil split' % skipped)

    # ---- emit the Sept round
    dd, seen = {}, set()
    for r in [x for x in D if x['Campaign'] == NEW]:
        di = dist(r['District'])
        if di in seen:
            raise SystemExit('ERR cin duplicate Sept district %r' % r['District'])
        seen.add(di)
        rec = record(r, SHEET_D, NEW)
        dd[str(di)] = [rec[c] for c, t in COLS]

    uu, seen = [], set()
    for r in [x for x in U if x['Campaign'] == NEW]:
        di = dist(r['District'])
        ui = uci(r['UC_NAME'], di)
        if ui in seen:
            raise SystemExit('ERR cin duplicate Sept UC %r/%r' % (r['District'], r['UC_NAME']))
        seen.add(ui)
        rec = record(r, SHEET_U, NEW)
        uu.append([ui, [rec[c] for c, t in COLS]])

    mtime = datetime.date.fromtimestamp(os.path.getmtime(path))
    return {
        'src': os.path.basename(path),
        'asof': mtime.isoformat(),
        'camp': {'l': NEW, 'y': '2026'},
        'k': [[c, t] for c, t in COLS],
        'dd': dd,
        'uu': uu,
        'n': len(uu),
    }, '%d districts, %d UC rows, %s, %d values checked' % (len(dd), len(uu), NEW, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if a.source:
        path = a.source
    else:
        cand = srcutil.discover(cfg['auto'][DS])
        if not cand:
            raise SystemExit('ERR cin no campaign-indicator workbook under %s'
                             % cfg['auto'][DS]['roots'])
        path = cand[0]['path']
    payload, summary = build(path)
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'cin.json')
    srcutil.write_text(dest, js)
    print('SRC cin wb %s' % path)
    print('OK cin %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
