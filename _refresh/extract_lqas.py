"""Extract the post-campaign E-LQAS payloads (const LQR lots + const LQM campaign list).

Usage: python _refresh/extract_lqas.py [--uc XLS] [--dist XLS] [--out PATH]
Prints: SRC lines + `OK lqas <lots> lots ...` | ERR lqas <reason>

Sources (newest of each under the configured roots, both EOC portal downloads):
  * `lqas_<date>_<time>.xls` - "Post-campaign LQAS, UC wise": one row per lot (one lot = one
    UC), at least within the 2026 rounds. A UC row carries the round, province, division,
    district, tehsil, UC, code, UC type, total lots and the lot result together with seven
    missed-child reason counts (child away, newborn, newly arrived/migrant, refused, team did
    not visit, team missed child, others) and their percentages.
  * the sibling `lqas_<date>_<time>.xls` exported at district grain - the same round summarised
    per district with the same seven reasons. Both files are HTML tables saved with an .xls
    name (the portal's table export), so they are read as text, not with xlrd.

The two grains are reconciled before anything is written: lots, pass/intermediate/fail and every
reason count must agree per district, and the district file's own Grand Total row must re-add
from its district rows. A mismatch aborts - a partially written file would silently disagree
with the UC table the dashboard plots.

Payload shape (unchanged from the hand-built one this replaces):
  LQR = one row per lot: dv division, d district, t tehsil, u UC, c UC code, ci campaign index,
        r P|I|F, aw/nb/mg/rf/dn/tm/ot reason counts, tt their sum.
  LQM = {asof, camps:[...]}, newest round first; `ci` indexes `camps`.

Re-running against a revised export of the same round replaces that round's lots and leaves the
earlier rounds untouched (campaign names, not indices, decide what is replaced).
"""
import argparse
import datetime as dt
import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

REASONS = ['aw', 'nb', 'mg', 'rf', 'dn', 'tm', 'ot']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
CQK_RE = re.compile(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\-]*(?:20)?(\d{2})\b', re.I)


def cqk(s):
    m = CQK_RE.search(str(s or ''))
    return (m.group(1).upper() + m.group(2)) if m else ''


def table(path):
    """Read an HTML-in-.xls export into a list of rows of clean cell strings."""
    with open(path, encoding='utf-8', errors='replace') as f:
        s = f.read()
    out = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', s, re.S | re.I):
        cells = []
        for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, re.S | re.I):
            c = re.sub(r'<[^>]+>', '', c)
            c = html.unescape(c).replace('\xa0', ' ')
            cells.append(' '.join(c.split()))
        if cells:
            out.append(cells)
    return out


def num(v, where=''):
    v = str(v or '').replace(',', '').strip()
    if not v:
        return 0
    try:
        f = float(v)
    except ValueError:
        raise SystemExit('ERR lqas %s: %r is not a number' % (where, v))
    return int(f) if f == int(f) else f


def load_payload(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    ml = re.search(r'const LQR = (\[.*?\]);\r?\nconst LQM = (\{.*?\});\r?\n', s, re.S)
    if not ml:
        raise SystemExit('ERR lqas cannot find const LQR / const LQM in index.html')
    return json.loads(ml.group(1)), json.loads(ml.group(2))


def parse_uc(path):
    rows = table(path)
    hi = None
    for i, r in enumerate(rows[:6]):
        if 'District' in r and 'UC' in r and 'Round' in r[0]:
            hi = i
            break
    if hi is None:
        raise SystemExit('ERR lqas %s is not the UC-wise export (no Round/District/UC header)'
                         % os.path.basename(path))
    head, sub = rows[hi], rows[hi + 1]
    if head[:8] != ['LQAS Round', 'Province', 'Division', 'District', 'Tehsil', 'UC', 'Code',
                    'Type of UC']:
        raise SystemExit('ERR lqas UC header changed: %s' % head[:8])
    # the second header row starts after the eight row-spanned identity columns; its labels are
    # then located by name, never by position
    cols = [''] * 8 + sub
    rix = {}
    for j, lbl in enumerate(cols):
        key = {'Child Away': 'aw', 'Newborn': 'nb', 'Newly Arrived/Migrant': 'mg',
               'Refused': 'rf', 'Team Did Not Visit': 'dn', 'Team Missed Child': 'tm',
               'Others': 'ot'}.get(lbl)
        if key:
            rix[key] = j
    if len(rix) != 7:
        raise SystemExit('ERR lqas UC export does not carry all seven reasons: %s'
                         % sorted(set(sub)))
    itot = cols.index('Grand Total') if 'Grand Total' in cols else len(cols) - 1
    ilots, ires = cols.index('Total Lots'), cols.index('Lot Result')
    lots, rounds, grand = [], set(), None
    for r in rows[hi + 2:]:
        if not r or not r[0]:
            continue
        if r[0].lower().startswith('grand total'):
            grand = r
            continue
        if len(r) <= itot:
            raise SystemExit('ERR lqas UC row is short (%d cells, need %d): %s'
                             % (len(r), itot + 1, r[:6]))
        rounds.add(r[0])
        rr = str(r[ires]).strip().lower()
        res = 'P' if rr.startswith('pass') else 'I' if rr.startswith('inter') else 'F' if rr.startswith('fail') else None
        if res is None:
            raise SystemExit('ERR lqas unknown lot result %r (%s)' % (r[ires], r[5]))
        vals = {k: num(r[j], 'reason %s' % k) for k, j in rix.items()}
        tt = num(r[itot], 'lot total')
        if sum(vals.values()) != tt:
            raise SystemExit('ERR lqas lot %s (%s) totals %s but its reasons sum to %s'
                             % (r[6], r[5], tt, sum(vals.values())))
        if num(r[ilots], 'total lots') != 1:
            raise SystemExit('ERR lqas lot %s carries %s lots - the payload assumes one lot per row'
                             % (r[6], r[ilots]))
        rec = {'dv': r[2], 'd': r[3], 't': r[4], 'u': r[5], 'c': r[6], 'r': res}
        rec.update(vals)
        rec['tt'] = tt
        lots.append(rec)
    if len(rounds) != 1:
        raise SystemExit('ERR lqas UC export mixes rounds %s' % sorted(rounds))
    rnd = rounds.pop()
    if grand:
        if num(grand[ilots], 'grand lots') != len(lots) or \
                num(grand[itot], 'grand total') != sum(x['tt'] for x in lots):
            raise SystemExit('ERR lqas UC Grand Total row (%s lots, %s missed) does not re-add '
                             'from the lots (%d lots, %d missed)'
                             % (grand[ilots], grand[itot], len(lots),
                                sum(x['tt'] for x in lots)))
    return lots, rnd


def parse_dist(path):
    rows = table(path)
    hi = None
    for i, r in enumerate(rows[:5]):
        if r and r[0] == 'LQAS Round' and 'District' in r:
            hi = i
            break
    if hi is None:
        raise SystemExit('ERR lqas %s is not the district summary' % os.path.basename(path))
    # the summary spends three header rows: groups, labels, then '#/%' sub-labels
    h1 = rows[hi]
    j = 0
    hdr = []
    for lbl in h1:
        if lbl == 'Lots Breakdown':
            hdr += ['lots', 'pass', 'passp', 'inter', 'interp', 'fail', 'failp']
        elif lbl == 'Reasons Missed':
            hdr += ['aw', 'awp', 'nb', 'nbp', 'mg', 'mgp', 'rf', 'rfp', 'dn', 'dnp',
                    'tm', 'tmp', 'ot', 'otp']
        else:
            hdr.append(lbl)
    hdr.append('Grand Total')  # the summary puts it after the reason pairs, unlabelled in the group row
    d = {h: i for i, h in enumerate(hdr)}
    need = ['LQAS Round', 'District', 'lots', 'pass', 'inter', 'fail'] + REASONS + ['Grand Total']
    miss = [k for k in need if k not in d]
    if miss:
        raise SystemExit('ERR lqas district header lacks %s' % miss)
    out, rounds, grand = {}, set(), None
    for r in rows[hi + 3:]:
        if not r or not r[0]:
            continue
        if r[0].lower().startswith('grand total'):
            grand = r
            continue
        rounds.add(r[d['LQAS Round']])
        vals = {k: num(r[d[k]], 'district %s' % k) for k in ['lots', 'pass', 'inter', 'fail']
                + REASONS + ['Grand Total']}
        out[r[d['District']]] = vals
    if len(rounds) != 1:
        raise SystemExit('ERR lqas district export mixes rounds %s' % sorted(rounds))
    return out, rounds.pop(), grand, d


def reconcile(lots, dist):
    by = {}
    for x in lots:
        g = by.setdefault(x['d'], {'n': 0, 'P': 0, 'I': 0, 'F': 0, 'aw': 0, 'nb': 0, 'mg': 0,
                                   'rf': 0, 'dn': 0, 'tm': 0, 'ot': 0, 'tt': 0})
        g['n'] += 1
        g[x['r']] += 1
        for k in REASONS:
            g[k] += x[k]
        g['tt'] += x['tt']
    if set(by) != set(dist):
        raise SystemExit('ERR lqas district sets differ: UC-only %s / summary-only %s'
                         % (sorted(set(by) - set(dist)), sorted(set(dist) - set(by))))
    bad = []
    for d, g in by.items():
        s = dist[d]
        pairs = [('lots', g['n'], s['lots']), ('pass', g['P'], s['pass']),
                 ('inter', g['I'], s['inter']), ('fail', g['F'], s['fail'])]
        pairs += [(k, g[k], s[k]) for k in REASONS]
        pairs += [('total', g['tt'], s['Grand Total'])]
        for label, a, b in pairs:
            if a != b:
                bad.append('%s %s %s!=%s' % (d, label, a, b))
    if bad:
        raise SystemExit('ERR lqas UC and district grains disagree: %s' % '; '.join(bad[:6]))
    return by


def asof_of(path):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(path))
    if not m:
        raise SystemExit('ERR lqas cannot read the export date from %s' % os.path.basename(path))
    return '%s-%s-%s' % m.groups()


def pick(cfg_roots=None):
    """Newest UC file and newest district summary under Downloads (largest file is UC-wise)."""
    roots = cfg_roots or [os.path.expanduser('~/Downloads')]
    files = []
    for root in roots:
        files += glob.glob(os.path.join(root, 'lqas_*.xls*'))
    files = sorted(set(files), key=os.path.getmtime, reverse=True)
    uc = dist = None
    for f in files:
        try:
            head = table(f)[0]
        except Exception:
            continue
        if 'UC' in head and uc is None:
            uc = f
        elif 'District' in head and dist is None:
            dist = f
        if uc and dist:
            break
    return uc, dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--uc', help='UC-wise export (default: newest lqas_*.xls in Downloads)')
    ap.add_argument('--dist', help='district summary export (default: its sibling)')
    ap.add_argument('--source', help='accepted for a single-file route; routed by --uc/--dist')
    ap.add_argument('--out')
    a = ap.parse_args()
    repo = os.path.dirname(srcutil.HERE)

    uc, dist = a.uc, a.dist
    if not uc or not dist:
        d_uc, d_dist = pick()
        uc, dist = uc or d_uc, dist or d_dist
    if not uc or not dist:
        raise SystemExit('ERR lqas need both the UC-wise export and its district summary '
                         '(lqas_*.xls in Downloads)')
    print('SRC uc   %s' % uc)
    print('SRC dist %s' % dist)

    lots, rnd_uc = parse_uc(uc)
    dist_rows, rnd_d, grand_d, dh = parse_dist(dist)
    if cqk(rnd_uc) != cqk(rnd_d):
        raise SystemExit('ERR lqas rounds differ: UC %r vs summary %r' % (rnd_uc, rnd_d))
    by = reconcile(lots, dist_rows)
    n = len(lots)
    pc = {k: sum(1 for x in lots if x['r'] == k) for k in 'PIF'}
    print('OK round %s: %d lots, %d pass / %d intermediate / %d fail, %d districts'
          % (rnd_uc, n, pc['P'], pc['I'], pc['F'], len(by)))
    if grand_d:
        tl = num(grand_d[dh['lots']], 'grand lots')
        tp = sum(s['pass'] for s in dist_rows.values())
        if tl != tp + sum(s['inter'] for s in dist_rows.values()) + \
                sum(s['fail'] for s in dist_rows.values()):
            raise SystemExit('ERR lqas district Grand Total (%s lots) does not re-add from the '
                             'district rows' % tl)

    old_rows, old_m = load_payload(repo)
    old_camps = list(old_m.get('camps') or [])
    if not old_camps:
        raise SystemExit('ERR lqas the embedded LQM carries no camps')
    if any(x['ci'] < 0 or x['ci'] >= len(old_camps) for x in old_rows):
        raise SystemExit('ERR lqas an embedded lot points past LQM.camps (%d camps)' % len(old_camps))
    keep = [c for c in old_camps if cqk(c) != cqk(rnd_uc)]
    camps = [rnd_uc] + keep
    idx = {c: i for i, c in enumerate(camps)}
    for x in lots:
        x['ci'] = 0
    carried = 0
    for x in old_rows:
        name = old_camps[x['ci']]
        if cqk(name) == cqk(rnd_uc):
            continue  # a revised export of the same round replaces its own lots
        y = dict(x)
        y['ci'] = idx[name]
        lots.append(y)
        carried += 1
    # key order the dashboard's own rows use
    keys = ['dv', 'd', 't', 'u', 'c', 'ci', 'r'] + REASONS + ['tt']
    rows = [{k: x[k] for k in keys} for x in lots]
    lqm = {'asof': asof_of(uc), 'camps': camps}
    txt = 'OK lqas %d lots on %s (%d pass / %d intermediate / %d fail), %d earlier lots carried ' \
          'across %d rounds' % (len(rows), rnd_uc, pc['P'], pc['I'], pc['F'], carried, len(camps))

    dest = a.out or os.path.join(srcutil.OUT, 'lqr.json')
    srcutil.write_text(dest, json.dumps(rows, ensure_ascii=False, separators=(', ', ': ')))
    dest2 = os.path.join(os.path.dirname(dest), 'lqm.json')
    srcutil.write_text(dest2, json.dumps(lqm, ensure_ascii=False, separators=(', ', ': ')))
    print('WROTE %s (%s chars)' % (dest, format(os.path.getsize(dest), ',')))
    print('WROTE %s (%s chars)' % (dest2, format(os.path.getsize(dest2), ',')))
    print(txt)


if __name__ == '__main__':
    main()
