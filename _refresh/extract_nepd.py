"""Extract the live NID Dec-26 pre-campaign readiness grid (const NEPD).

Usage: python _refresh/extract_nepd.py [--source PATH] [--out PATH]
Prints one status line: OK nepd <json chars> <summary> | ERR nepd <reason>

Source: EOC dashboard > Campaign > Pre Campaign > NEAP readiness, saved from the portal as
`NEAP*.xls` (an HTML table). The grid opened for NID Dec-26 on 24-Nov-2026 as two exports:
district-wise (~47 KB: Province, District, DPEC held intime, DC, DHO, ...) and UC-wise
(~1.8 MB: Province, District, Tehsil, UC, then the same 14 indicator columns).

`const NEAP` keeps the closed SNID Nov-26 round as the benchmark record; this payload is the
new grid only. The export carries no campaign column, so the label follows the dashboard's own
upcoming-round plan (NRMP): campaign name and start date are read from it, never guessed.

Scope: the 36 districts of the dashboard register (SOPS zr.d). The portal also reports Bar Swat
as its own row inside Swat; it is kept as a separate row (never merged or dropped) and named in
`extra`. Any other name, or a missing register district, aborts the extract.

Payload: {"src":..,"srcu":..,"asof":..,"camp":..,"start":..,"n":..,"nd":..,"extra":[..],
          "xp":{"BAR SWAT":"SWAT"},"k":[[key,label],..],"d":{district:[14 values]},"tot":[14 means],
          "u":{"src":..,"asof":..,"t":[tehsils],"r":[[district,tehsil-idx,uc,14 values]]}}

`xp` is the sub-unit -> parent district map, so the UC-wide totals can count every UC row
under the district it belongs to even though the portal splits Bar Swat out of Swat.
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
import extract_neap as E

DS = 'nepd'
K = E.K
# portal rows that are reporting units inside a register district, not districts of their own
EXTRA = {'BAR SWAT': 'SWAT'}


def const(repo, name):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const %s = ' % name)
    if i < 0:
        raise SystemExit('ERR nepd const %s not found in index.html' % name)
    j = s.find('\n', i)
    head = 'const %s = ' % name
    return json.loads(s[i + len(head):j].rstrip().rstrip(';'))


def register(repo):
    zr = (const(repo, 'SOPS').get('zr') or {})
    keys = set((zr.get('d') or {}).keys())
    if len(keys) < 30:
        raise SystemExit('ERR nepd the SOPS district register has %d keys, expected the 36 districts' % len(keys))
    return keys


def nid_meta(repo):
    nrmp = const(repo, 'NRMP')
    camp = (nrmp.get('cam') or '').strip()
    start = (nrmp.get('start') or '').strip()
    if not camp or not re.search(r'dec', camp, re.I) or not re.match(r'^\d{4}-\d{2}-\d{2}$', start):
        raise SystemExit('ERR nepd NRMP does not describe a December round with a start date (camp=%r start=%r)'
                         % (camp, start))
    return 'NID Dec-26', start


def check_scope(names, reg):
    extra = sorted(n for n in names if n not in reg)
    bad = [n for n in extra if n not in EXTRA]
    missing = sorted(reg - set(names))
    if bad or missing:
        raise SystemExit('ERR nepd district names do not match the dashboard register: unknown=%s missing=%s'
                         % (bad, missing))
    return extra


def build_district(path, repo, reg):
    got = E.parse(path)
    if not got:
        raise SystemExit('ERR nepd %s is not a district-wise NEAP readiness export' % os.path.basename(path))
    hdr = E.norm_head(got[0])
    if len(hdr) < 2 + len(K):
        raise SystemExit('ERR nepd %s header has %d columns, want >= %d'
                         % (os.path.basename(path), len(hdr), 2 + len(K)))
    for j in (2, 3, 2 + len(K) - 1):
        if hdr[j] != E.SRC_HEAD[j]:
            raise SystemExit('ERR nepd %s column %d is %r, want %r'
                             % (os.path.basename(path), j, hdr[j], E.SRC_HEAD[j]))
    d = {}
    for r in got[1]:
        if len(r) < 2:
            continue
        if len(r) < 2 + len(K):
            r = list(r) + [''] * (2 + len(K) - len(r))
        name = E.RENAME.get(r[1].strip().upper(), r[1].strip())
        if not name or name.upper() in ('TOTAL', 'GRAND TOTAL', 'KP'):
            continue
        if name in d:
            raise SystemExit('ERR nepd duplicate district row %r' % name)
        d[name] = [E.num(r[j]) for j in range(2, 2 + len(K))]
    if not d:
        raise SystemExit('ERR nepd no district rows found')
    extra = check_scope(set(d), reg)
    return {k: d[k] for k in sorted(d)}, extra


def build_uc(path, repo, reg):
    got = E.parse_uc(path)
    if not got:
        raise SystemExit('ERR nepd %s is not a UC-wise NEAP readiness export' % os.path.basename(path))
    hdr, body = got
    want = 4 + len(K)
    if len(hdr) < want:
        raise SystemExit('ERR nepd UC export %s has %d columns, want >= %d'
                         % (os.path.basename(path), len(hdr), want))
    for j in range(len(K)):
        if hdr[4 + j] != E.SRC_HEAD[2 + j]:
            raise SystemExit('ERR nepd UC export %s column %d is %r, want %r'
                             % (os.path.basename(path), 4 + j, hdr[4 + j], E.SRC_HEAD[2 + j]))
    t, tr, r = [], {}, []
    for row in body:
        if len(row) < want:
            row = list(row) + [''] * (want - len(row))
        dn = E.RENAME.get(row[1].strip().upper(), row[1].strip())
        if not dn or dn.upper() in ('TOTAL', 'GRAND TOTAL', 'KP'):
            continue
        if dn not in reg and dn not in EXTRA:
            raise SystemExit('ERR nepd UC export district %r is not in the dashboard register' % dn)
        tn = re.sub(r'\s+', ' ', row[2]).strip()
        ti = tr.get(tn)
        if ti is None:
            ti = tr[tn] = len(t)
            t.append(tn)
        r.append([dn, ti, re.sub(r'\s+', ' ', row[3]).strip()] + [E.num(row[4 + j]) for j in range(len(K))])
    if not r:
        raise SystemExit('ERR nepd UC-wise export has no district rows')
    return t, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    repo = cfg['repo']
    cands = srcutil.discover(cfg['auto'][DS])
    if a.source:
        s_abs = os.path.normcase(os.path.abspath(a.source))
        cands = [srcutil.stat_rec(a.source)] + [
            c for c in cands if os.path.normcase(os.path.abspath(c['path'])) != s_abs]
    if not cands:
        raise SystemExit('ERR nepd no NEAP files found under %s' % cfg['auto'][DS]['roots'])

    reg = register(repo)
    camp, start = nid_meta(repo)

    dist = None
    for rec in cands:
        p = rec['path']
        if not os.path.exists(p):
            continue
        try:
            d, extra = build_district(p, repo, reg)
        except SystemExit as e:
            if str(e).startswith('ERR nepd %s is not a district-wise' % os.path.basename(p)):
                continue
            raise
        dist = (p, d, extra)
        break
    if not dist:
        raise SystemExit('ERR nepd no district-wise NEAP export among %d candidates' % len(cands))
    dp, d, extra = dist

    uc = None
    for rec in cands:
        p = rec['path']
        if not os.path.exists(p):
            continue
        try:
            t, r = build_uc(p, repo, reg)
        except SystemExit as e:
            if str(e).startswith('ERR nepd %s is not a UC-wise' % os.path.basename(p)):
                continue
            raise
        uc = (p, t, r)
        break
    if not uc:
        raise SystemExit('ERR nepd no UC-wise NEAP export among %d candidates' % len(cands))
    up, t, r = uc

    tot = []
    for k in range(len(K)):
        vals = [v[k] for v in d.values() if v[k] >= 0]
        tot.append(round(sum(vals) / len(vals), 1) if vals else -1)

    dm = datetime.datetime.fromtimestamp(os.stat(dp).st_mtime)
    um = datetime.datetime.fromtimestamp(os.stat(up).st_mtime)
    payload = {'src': os.path.basename(dp), 'srcu': os.path.basename(up), 'asof': dm.date().isoformat(),
               'camp': camp, 'start': start, 'n': len(d), 'nd': len(set(d) & reg), 'extra': extra,
               'xp': {k: v for k, v in EXTRA.items() if k in d},
               'k': [[x, y] for x, y in K], 'd': d, 'tot': tot,
               'u': {'src': os.path.basename(up), 'asof': um.date().isoformat(), 't': t, 'r': r}}

    held = [x for x in sorted(d) if d[x][0] >= 100]
    uheld = sum(1 for x in r if x[3] >= 100)
    uby = {}
    for x in r:
        if x[3] >= 100:
            uby[x[0]] = uby.get(x[0], 0) + 1
    aic = sum(1 for v in d.values() if v[6] > 0)
    summary = ('%s grid (start %s): %d portal rows = %d districts%s, DPEC held in %d (%s), '
               'AIC training started in %d, teams trained in %d; UC-wise %d UCs, DPEC held in %d (%s)'
               % (camp, start, len(d), len(set(d) & reg),
                  (' + ' + ', '.join(extra)) if extra else '', len(held), ', '.join(held) or 'none',
                  aic, sum(1 for v in d.values() if v[7] > 0), len(r), uheld,
                  ', '.join('%s %d' % (k, uby[k]) for k in sorted(uby)) or 'none'))

    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'nepd.json')
    srcutil.write_text(dest, js)
    print('SRC nepd district %s' % dp)
    print('SRC nepd uc %s' % up)
    print('OK nepd %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
