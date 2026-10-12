"""Extract the 2024-2025 zero-dose advance reports (const ADV) from the IDIMS advance_reports exports.

Every advance_reports_*.xls under the configured roots is loaded - each file is a
self-contained per-campaign dump, so a new year's file just gets dropped alongside
the others. Unknown campaign names abort the extract (add them to
auto.adv.config.campaigns in sources.json).

Usage: python _refresh/extract_adv.py [--out PATH] [--allow-unknown-districts]
Prints: SRC adv <path> | OK adv <json chars> <summary> | ERR adv <reason>
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'adv'
MONTHS = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
          'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
MONTH_RE = re.compile(r'\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT|SEP|OCT|NOV|DEC)[A-Z]*')
YEAR_RE = re.compile(r'\b(20\d\d|\d\d)\b')
ASOF_RE = re.compile(r'(20\d{6})T(\d{6})')
# completed years only: the current cycle is owned by the live ZD Reported & Covered tab
CUR_YEAR = 2026


def zd_divisions(repo):
    """district -> division, taken from the dashboard's own ZD payload so filters line up."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR adv const ZD not found in index.html')
    j = s.find('\n', i)
    zd = json_load(s[i + len('const ZD = '):j].rstrip().rstrip(';'))
    div = {}
    for r in zd:
        div[r['d']] = r['dv']
    return div


def json_load(s):
    import json
    return json.loads(s.replace('<\\/', '</'))


def campaign_meta(name, overrides):
    o = overrides.get(name)
    if o:
        return int(o['y']), o.get('m'), o.get('t')
    nm = name.upper()
    mm = MONTH_RE.search(nm)
    ym = YEAR_RE.search(nm)
    if not mm or not ym:
        raise SystemExit('ERR adv cannot read year/month from campaign %r - '
                         'add it to auto.adv.config.campaigns in sources.json' % name)
    y = int(ym.group(1))
    if y < 100:
        y += 2000
    mon = MONTHS[mm.group(1)[:3].upper()]
    t = ('NID' if nm.startswith('NID') else 'SNID' if nm.startswith('SNID')
         else 'CR' if nm.startswith('CR') else 'OBR' if nm.startswith('OBR') else 'ACT')
    return y, mon, t


def file_key(rec):
    """Sort key: filename export timestamp (20261012T173908380Z) newest first, mtime as fallback."""
    m = ASOF_RE.search(rec['name'])
    if m:
        return (0, m.group(1) + m.group(2))
    return (1, '%d' % int(rec['mtime'] * 1000))


def read_frame(rec):
    import pandas as pd
    try:
        tables = pd.read_html(rec['path'], header=0)
    except Exception as ex:
        return None, 'cannot read: %s' % ex
    df = tables[0]
    cols = [str(c).strip() for c in df.columns]
    def find(prefix):
        for i, c in enumerate(cols):
            if c.lower().startswith(prefix.lower()):
                return i
        return -1
    ix = {k: find(p) for k, p in (('camp', 'Campaign'), ('dist', 'District'), ('teh', 'Tehsil'),
                                  ('uc', 'UC'), ('rep', 'Zero dose children'),
                                  ('cov', 'Zero dose ('))}
    if min(ix.values()) < 0 or ix['uc'] < 0:
        missing = [k for k, v in ix.items() if v < 0]
        return None, 'missing columns %s' % (missing or ['UC'])
    keep = ['camp', 'dist', 'teh', 'uc', 'rep', 'cov']
    df = df.iloc[:, [ix[k] for k in keep]]
    df.columns = keep
    df['camp'] = df['camp'].astype(str).str.strip()
    df = df[df.camp != 'Campaign']
    for c in ('dist', 'teh', 'uc'):
        df[c] = df[c].astype(str).str.strip()
    for c in ('rep', 'cov'):
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df, None


def build(cfg, allow_unknown=False):
    e = cfg['auto'][DS]
    files = sorted(srcutil.discover(e), key=file_key, reverse=True)
    if not files:
        raise SystemExit('ERR adv no advance_reports files under %s' % e['roots'])
    div = zd_divisions(cfg['repo'])

    camps, rows_by_camp, skipped, files_used = {}, {}, [], []
    for rec in files:
        df, err = read_frame(rec)
        if df is None:
            skipped.append('%s (%s)' % (rec['name'], err.split(':')[0]))
            continue
        fresh = [c for c in df.camp.unique() if c not in camps]
        if not fresh:
            continue
        files_used.append(rec['name'])
        sub = df[df.camp.isin(fresh)]
        for c, g in sub.groupby('camp'):
            camps[c] = True
            rows_by_camp[c] = [(d, t, uc, int(rp), int(cv))
                               for d, t, uc, rp, cv in g[['dist', 'teh', 'uc', 'rep', 'cov']].itertuples(index=False)]
    for w in skipped:
        print('WARN adv skipped %s' % w)

    unknown = sorted({r[0] for rows in rows_by_camp.values() for r in rows} - set(div))
    if unknown and not allow_unknown:
        raise SystemExit('ERR adv districts not in dashboard ZD data: %s '
                         '(pass --allow-unknown-districts to override)' % unknown)

    ds = sorted({r[0] for rows in rows_by_camp.values() for r in rows})
    di = {d: i for i, d in enumerate(ds)}
    triples = sorted({(r[0], r[1], r[2]) for rows in rows_by_camp.values() for r in rows})
    ui, u = {}, []
    for d, t, uc in triples:
        ui[(d, t, uc)] = len(u)
        u.append([di[d], t, uc])

    ovr = (e.get('config') or {}).get('campaigns') or {}
    meta = {}
    for n in sorted(camps):
        y, m, t = campaign_meta(n, ovr)
        if y >= CUR_YEAR:
            print('WARN adv excluding %s (%d - current cycle lives on the ZD Reported & Covered tab)' % (n, y))
            continue
        meta[n] = {'n': n, 'y': y, 'm': m, 't': t}
    if not meta:
        raise SystemExit('ERR adv no completed-year campaigns found (nothing older than %d)' % CUR_YEAR)
    order = sorted(meta, key=lambda n: (meta[n]['y'], 99 if meta[n]['m'] is None else meta[n]['m'], n))

    cs, rs = [], []
    for n in order:
        rows = sorted([ui[(d, t, uc)], rp, cv] for d, t, uc, rp, cv in rows_by_camp[n])
        cs.append(meta[n])
        rs.append(rows)

    rep = sum(r[1] for rows in rs for r in rows)
    cov = sum(r[2] for rows in rs for r in rows)
    m = ASOF_RE.search(files[0]['name'])
    asof = '%s-%s-%s' % (m.group(1)[:4], m.group(1)[4:6], m.group(1)[6:]) if m else None
    note = '; skipped: %s' % ', '.join(skipped) if skipped else ''
    out = {'src': 'IDIMS advance reports (%d files used, newest %s%s)' % (
               len(files_used), files_used[0] if files_used else '-', note),
           'asof': asof, 'ds': ds, 'dv': [div[d] for d in ds], 'u': u, 'c': cs, 'r': rs}
    summary = '%d campaigns %d-%d, %d districts, %d UCs, %d rows, reported %s, covered %s' % (
        len(cs), cs[0]['y'], cs[-1]['y'], len(ds), len(u),
        sum(len(x) for x in rs), format(rep, ','), format(cov, ','))
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # accepted for interface parity; all matches are loaded
    ap.add_argument('--out')
    ap.add_argument('--allow-unknown-districts', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    out, summary = build(cfg, a.allow_unknown_districts)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'adv.json')
    srcutil.write_text(dest, js)
    print('OK adv %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
