"""Extract the zero-dose advance reports (const ADV) from the IDIMS advance_reports exports.

Every advance_reports_*.xls under the configured roots is loaded - each file is a
self-contained per-campaign dump, and for campaigns present in several exports the
newest file wins. A new year's file just gets dropped alongside the others.
Some exports (the 202610xx re-exports) are small .xls "shells" whose table lives in a
sibling <name>_files/sheet001.htm - those are read from the companion file. The newest
layout carries explicit ZERO DOSE REPORTED / ZERO DOSE COVERED columns.
The Sept-2026-era export leaves the reported column empty and puts the tracked children
in the covered column; for campaigns also tracked by the dashboard's ZD reported &
covered dataset (NID Apr 26, SNID May 2026, SNID Sept 2026) both figures are filled
from that dataset, other such campaigns keep the tracked children as reported with
coverage unknown.
Campaign names without a readable month/year abort the extract (add them to
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

# campaigns that also appear on the dashboard's ZD reported & covered page, with the
# ZD row keys for this campaign's reported/covered (labels mirror the ZD tab).
ZD_CAMPS = {'NID APR 26': ('rA', 'cA'), 'SNID MAY 2026': ('rM', 'cM'),
            'SNID SEPT 2026': ('rS', None)}


def norm_label(s):
    return re.sub(r'\s+', ' ', str(s)).strip().upper()


def zd_rows(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR adv const ZD not found in index.html')
    j = s.find('\n', i)
    return json_load(s[i + len('const ZD = '):j].rstrip().rstrip(';'))


def zd_divisions(repo):
    """district -> division, taken from the dashboard's own ZD payload so filters line up."""
    div = {}
    for r in zd_rows(repo):
        div[r['d']] = r['dv']
    return div


def zd_reported_covered(repo):
    """ZD_CAMPS campaign -> {(district, uc): (reported, covered or None)} from const ZD."""
    rows = zd_rows(repo)
    out = {}
    for cname, (rk, ck) in ZD_CAMPS.items():
        m = {}
        for r in rows:
            rep = r.get(rk)
            if rep is None:
                continue
            cv = r.get(ck) if ck else None
            m[(norm_label(r['d']), norm_label(r['u']))] = (
                int(rep), None if cv is None else int(cv))
        out[cname] = m
    return out


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


def shell_table_path(path):
    """The companion table file IDIMS writes next to the small .xls shells, if present."""
    h = os.path.join(os.path.splitext(path)[0] + '_files', 'sheet001.htm')
    return h if os.path.exists(h) else None


def read_frame(rec):
    import pandas as pd
    tables, err = None, 'no tables in file'
    for path in (rec['path'], shell_table_path(rec['path'])):
        if not path:
            continue
        try:
            tables = pd.read_html(path, header=0)
        except Exception as ex:
            err = 'cannot read: %s' % ex
            continue
        if tables:
            break
    if not tables:
        return None, err
    df = tables[0]
    cols = [str(c).strip() for c in df.columns]
    def find(*prefixes):
        for p in prefixes:
            for i, c in enumerate(cols):
                if c.lower().startswith(p.lower()):
                    return i
        return -1
    ix = {k: find(*p) for k, p in (('camp', ('Campaign',)), ('dist', ('District',)),
                                   ('teh', ('Tehsil',)), ('uc', ('UC',)),
                                   ('rep', ('Zero dose children', 'Zero dose reported')),
                                   ('cov', ('Zero dose (', 'Zero dose covered')))}
    if min(ix.values()) < 0 or ix['uc'] < 0:
        missing = [k for k, v in ix.items() if v < 0]
        return None, 'missing columns %s' % (missing or ['UC'])
    keep = ['camp', 'dist', 'teh', 'uc', 'rep', 'cov']
    df = df.iloc[:, [ix[k] for k in keep]]
    df.columns = keep
    # the shell-HTML layout pads names with doubled spaces - collapse so both layouts
    # produce the same labels and the same (district, tehsil, UC) triples.
    df['camp'] = df['camp'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    df = df[df.camp != 'Campaign']
    for c in ('dist', 'teh', 'uc'):
        df[c] = df[c].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
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

    # IDIMS Sept-2026-era layout: the reported column is empty and the tracked children
    # sit in the covered column. For campaigns tracked by the dashboard's ZD reported &
    # covered dataset, fill both figures (and UCs missing from this export) from it.
    deficient = [c for c, rows in rows_by_camp.items()
                 if sum(r[3] for r in rows) == 0 and sum(r[4] for r in rows) > 0]
    if deficient:
        zdmap = zd_reported_covered(cfg['repo'])
        triples = {}
        for rows in rows_by_camp.values():
            for d, t, uc, rp, cv in rows:
                triples.setdefault((norm_label(d), norm_label(uc)), (d, t, uc))
        for c in sorted(deficient):
            m = zdmap.get(norm_label(c))
            if m is None:
                rows_by_camp[c] = [(d, t, uc, cv, None) for d, t, uc, rp, cv in rows_by_camp[c]]
                print('WARN adv %s: reported column empty in the newest export - took the tracked '
                      'children from the second column; covered-in-round is not in that export' % c)
                continue
            new, seen, added, miss = [], set(), 0, 0
            for d, t, uc, rp, cv in rows_by_camp[c]:
                key = (norm_label(d), norm_label(uc))
                seen.add(key)
                z = m.get(key)
                if z is None:
                    miss += 1
                    new.append((d, t, uc, 0, None))
                else:
                    new.append((d, t, uc, z[0], z[1]))
            for key, (rp, cv) in m.items():
                if key in seen:
                    continue
                tri = triples.get(key)
                if tri is None:
                    miss += 1
                    continue
                new.append((tri[0], tri[1], tri[2], rp, cv))
                added += 1
            rows_by_camp[c] = new
            print('WARN adv %s: reported column empty in the newest export - filled from the dashboard '
                  'ZD reported & covered data (%d UCs, %d added%s)'
                  % (c, len(new), added, ', %d UCs unmatched' % miss if miss else ''))

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
        meta[n] = {'n': n, 'y': y, 'm': m, 't': t}
    if not meta:
        raise SystemExit('ERR adv no campaigns found')
    order = sorted(meta, key=lambda n: (meta[n]['y'], 99 if meta[n]['m'] is None else meta[n]['m'], n))

    cs, rs = [], []
    for n in order:
        rows = sorted([ui[(d, t, uc)], rp, cv] for d, t, uc, rp, cv in rows_by_camp[n])
        cs.append(meta[n])
        rs.append(rows)

    rep = sum(r[1] for rows in rs for r in rows)
    cov = sum(r[2] or 0 for rows in rs for r in rows)
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
