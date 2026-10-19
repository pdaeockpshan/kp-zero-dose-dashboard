"""Extract the UC criteria payload (const UCC) from the EOC master categorization workbook.

Usage: python _refresh/extract_ucc.py [--source PATH] [--out PATH]
Prints one status line: OK ucc <json chars> <summary> | ERR ucc <reason>

Source: `Master Sheet*.xlsx` (tab `Master Sheet`, two-row header - a merged group row
above the real names). One row per UC with the IDIMS UC code, Division / District /
Tehsil / UC, the COMNet block, the `EOC Cat` block (Region, SKP/Rest KP, Risk
Categorization, Corridor, Boardering UC, ARCamp, ...) and the PDA / IDIMS blocks.

Only two master columns are read - `Boardering UC` (province the UC borders) and
`SKP/Rest KP` - plus the geo columns. Everything else stays out of the payload.

The criteria vocabulary is the campaign-scope one the EOC uses for the upcoming round
(Core District / Endemic / Afg Bordering / High Risk / Rest of KP), so district
categories come from the dashboard's own `const SND` rather than from the workbook.
Per UC the label is:

  1. `Afghan bordering` when the master flags the UC as bordering Afghanistan
     (`Boardering UC` contains AFG) - this promotes UCs whose district sits in another
     category, e.g. the 8 border UCs of KHYBER (a Core District);
  2. otherwise the SNID scope category of its district;
  3. otherwise `config.fallback` - the districts outside the upcoming round's scope.
     Every UC of such a district must carry `config.fallback_scp` in `SKP/Rest KP`,
     asserted here so a revised master cannot be silently mislabelled.

Payload: {"src":..,"asof":..,"sheet":..,"camp":..,"n":<UCs>,
          "k":[label,..],"d":[[district,critIdx],..],
          "al":[[alias district,critIdx],..],"a":[[district,"UC NAME"],..],
          "ac":["UC code",..]}
`a`/`ac` are the Afghan-bordering UCs by name and by code; the page tries the code
first because a few datasets spell UC names differently from the master.
"""
import argparse
import datetime
from collections import Counter
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'ucc'

NEED = {'code': 'uccode', 'dist': 'district', 'uc': 'uc',
        'skp': 'skprestkp', 'bord': 'boarderinguc'}


def norm(h):
    return re.sub(r'[^a-z0-9]', '', str(h or '').lower())


def snd_scope(repo):
    """(district -> SNID scope category, campaign label) from the dashboard's own SND."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SND = ')
    if i < 0:
        raise SystemExit('ERR ucc const SND not found in index.html')
    j = s.find('\n', i)
    snd = json.loads(s[i + len('const SND = '):j].rstrip().rstrip(';'))
    return {r[0]: r[2] for r in snd['d']}, (snd.get('n') or '')


def zd_districts(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR ucc const ZD not found in index.html')
    j = s.find('\n', i)
    zd = json.loads(s[i + len('const ZD = '):j].rstrip().rstrip(';'))
    return {r['d'] for r in zd}


def ucname(v):
    return re.sub(r'\s+', ' ', str(v or '')).strip().upper()


def uccode(v):
    t = str(v if v is not None else '').strip()
    if t.endswith('.0'):
        t = t[:-2]
    return t


def header_row(rows):
    for i, r in enumerate(rows[:8]):
        cells = [norm(c) for c in r]
        if cells and cells[0] == NEED['code']:
            idx = {}
            for key, want in NEED.items():
                if want not in cells:
                    raise SystemExit('ERR ucc master header has no %r column (got %s)'
                                     % (want, [c for c in cells if c]))
                idx[key] = cells.index(want)
            return i, idx
    raise SystemExit('ERR ucc header row (first cell "UC Code") not found in the first 8 rows')


def build(path, cfg, repo):
    import openpyxl
    ds = cfg['auto'][DS]
    k = ds['config']
    labels, smap = k['labels'], k['scope_map']
    fb, fbscp = k['fallback'], k['fallback_scp']
    toks = [t.upper() for t in (k.get('afg_tokens') or ['AFG'])]
    alias = k.get('alias') or {}
    sheet = (ds.get('sheets') or ['Master Sheet'])[0]

    bad = [c for c, i in smap.items() if not (0 <= i < len(labels))]
    if bad:
        raise SystemExit('ERR ucc config.scope_map points outside labels: %s' % bad)
    if not (0 <= fb < len(labels)):
        raise SystemExit('ERR ucc config.fallback %r outside labels' % fb)

    scope, camp = snd_scope(repo)
    unknown_cat = sorted({c for c in scope.values() if c not in smap})
    if unknown_cat:
        raise SystemExit('ERR ucc %s scope categories not in config.scope_map: %s'
                         % (camp or 'SND', unknown_cat))
    zdd = zd_districts(repo)
    rename = (cfg['auto'].get('snd', {}).get('config', {}) or {}).get('rename') or {}

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        wb.close()
        raise SystemExit('ERR ucc sheet %r missing (has %s)' % (sheet, wb.sheetnames))
    rows = [r for r in wb[sheet].iter_rows(values_only=True)]
    wb.close()
    hi, ix = header_row(rows)
    body = rows[hi + 1:]

    seen, a_list, a_code, skp_by_d = {}, [], [], {}
    for r in body:
        code = uccode(r[ix['code']]) if len(r) > ix['code'] else ''
        dist = str(r[ix['dist']] or '').strip() if len(r) > ix['dist'] else ''
        dist = rename.get(dist.upper(), dist)
        uc = ucname(r[ix['uc']]) if len(r) > ix['uc'] else ''
        if not dist or not uc:
            continue
        skp = str(r[ix['skp']] or '').strip() if len(r) > ix['skp'] else ''
        bord = str(r[ix['bord']] or '').strip().upper() if len(r) > ix['bord'] else ''
        key = (dist, uc)
        if key in seen:
            raise SystemExit('ERR ucc duplicate UC row %s / %s' % (dist, uc))
        seen[key] = code
        skp_by_d.setdefault(dist, set()).add(skp)
        if any(t in bord for t in toks):
            a_list.append([dist, uc])
            if code:
                a_code.append(code)

    if not seen:
        raise SystemExit('ERR ucc no UC rows read from %s' % sheet)

    d = []
    for dist in sorted(skp_by_d):
        if dist not in zdd:
            raise SystemExit('ERR ucc master district %r is not in the dashboard ZD data' % dist)
        if dist in scope:
            d.append([dist, smap[scope[dist]]])
            continue
        off = sorted(x for x in skp_by_d[dist] if x != fbscp)
        if off:
            raise SystemExit('ERR ucc %s is outside the %s scope but its master SKP/Rest KP '
                             'values are %s, not all %r - set config.fallback/scope_map'
                             % (dist, camp or 'SND', off, fbscp))
        d.append([dist, fb])

    lack = sorted(zdd - set(skp_by_d))
    if lack:
        raise SystemExit('ERR ucc dashboard districts absent from the master sheet: %s' % lack)
    al = [[a, smap.get(b, b) if isinstance(b, str) else b] for a, b in sorted(alias.items())]
    for a, i in al:
        if not (0 <= i < len(labels)):
            raise SystemExit('ERR ucc alias %r points at criteria index %r' % (a, i))

    ucc = {'src': os.path.basename(path),
           'asof': datetime.datetime.fromtimestamp(os.stat(path).st_mtime).date().isoformat(),
           'sheet': sheet, 'camp': camp, 'n': len(seen), 'k': labels,
           'd': d, 'al': al, 'a': sorted(a_list), 'ac': sorted(a_code)}

    mix = Counter(labels[i] for _, i in d)
    summary = ('%d UCs, %d districts (%s), %d Afghan-bordering UCs%s'
               % (len(seen), len(d),
                  ', '.join('%s %d' % (lab, mix[lab]) for lab in labels if mix[lab]),
                  len(a_list),
                  (', aliases: ' + ', '.join(x[0] for x in al)) if al else ''))
    return ucc, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR ucc no master categorization workbook found under %s'
                         % cfg['auto'][DS]['roots'])
    ucc, summary = build(rec['path'], cfg, cfg['repo'])
    js = srcutil.dumps(ucc)
    dest = a.out or os.path.join(srcutil.OUT, 'ucc.json')
    srcutil.write_text(dest, js)
    print('SRC ucc %s' % rec['path'])
    print('OK ucc %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
