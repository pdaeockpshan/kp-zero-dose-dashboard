"""Shared per-file parse cache for the EPI-MIS Consolidated monthly exports.

The monthly facility-wise exports are ~7.4 MB HTML-table files that take pandas
tens of seconds each to parse, and several extractors need the same parse, so the
per-district aggregates are cached under _refresh/cache/ keyed by srcutil.file_id
(path + mtime + size). Extractors run sequentially inside refresh.py run, so a
plain dict pickled to disk is safe.
"""
import os
import pickle

import srcutil

CACHE = os.path.join(srcutil.HERE, 'cache')
EPI_CACHE = os.path.join(CACHE, 'epi25mon.pkl')


def load():
    try:
        with open(EPI_CACHE, 'rb') as f:
            return pickle.load(f)
    except (OSError, EOFError, ValueError):
        return {}


def store(cache):
    os.makedirs(CACHE, exist_ok=True)
    tmp = EPI_CACHE + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(cache, f)
    os.replace(tmp, EPI_CACHE)


def read_consolidated(rec):
    """One monthly export -> {'mo': 'YYYY-MM', 'ed': {epi_district: {n,s,+antigens}}}.

    Returns None for files whose period header cannot be read (not single-month).
    """
    import io
    import re

    import pandas as pd

    AG = [('bcg', 'BCG Total'), ('opv0', 'OPV 0 Total'), ('p1', 'Pentavalent I Total'),
          ('p3', 'Pentavalent III Total'), ('pcv3', 'PCV 10 III Total'), ('ipv1', 'IPV Total'),
          ('ipv2', 'IPV II Total'), ('rota2', 'Rota II Total'), ('mr1', 'MR I Total'),
          ('mr2', 'MR II Total'), ('fi', 'Fully Immunized Total')]
    KEEP = ('S No.', 'District', 'Tehsil', 'Union Council', 'Uncode', 'Distcode')

    with open(rec['path'], 'rb') as f:
        head = f.read(4096).decode('utf-8', 'replace')
    m = re.search(r'<h5>\s*(\d{4}-\d{2})\s*-\s*(\d{4}-\d{2})\s*</h5>', head)
    if not m or m.group(1) != m.group(2):
        return None
    mo = m.group(1)

    raw = open(rec['path'], 'rb').read()
    t = max(pd.read_html(io.BytesIO(raw)), key=len)
    cols = []
    for c in t.columns:
        if c[0] in KEEP:
            cols.append(c[0])
        else:
            cols.append(' '.join(dict.fromkeys(str(x) for x in c if str(x) != 'nan')).strip())
    t.columns = cols
    need = ['District', 'Target Newborns', 'Target Surviving Infants'] + [a[1] for a in AG]
    miss = [c for c in need if c not in t.columns]
    if miss:
        raise RuntimeError('monthly export %s is missing columns %s' % (rec['name'], miss))
    # UC-wise exports carry Uncode (numeric per-UC rows, totals lack it); the
    # district-level 2024 exports instead carry Distcode.
    if 'Uncode' in t.columns:
        t = t[pd.to_numeric(t['Uncode'], errors='coerce').notna()].copy()
    elif 'Distcode' in t.columns:
        t = t[pd.to_numeric(t['Distcode'], errors='coerce').notna()].copy()
    num = ['Target Newborns', 'Target Surviving Infants'] + [a[1] for a in AG]
    for c in num:
        t[c] = pd.to_numeric(t[c], errors='coerce').fillna(0)
    t['District'] = t['District'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    out = {}
    junk = {'', '0', '0.0', 'nan', 'none', 'null', 'total'}
    for ed, g in t.groupby('District'):
        if ed.strip().lower() in junk:
            continue
        out[ed] = {'n': int(g['Target Newborns'].sum()), 's': int(g['Target Surviving Infants'].sum()),
                   **{a[0]: int(g[a[1]].sum()) for a in AG}}
    return {'mo': mo, 'ed': out}


def months(cache):
    """file_id -> parsed record, for every cached single-month export."""
    return {k: v for k, v in cache.items() if isinstance(v, dict) and v.get('mo')}


def embedded_const(repo, name, array=False):
    """Read an embedded dashboard payload (const NAME) out of index.html."""
    import json

    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const %s = ' % name)
    if i < 0:
        raise SystemExit('ERR const %s not found in index.html' % name)
    end = '];' if array else '}'
    j = s.find(end, i)
    if j < 0:
        raise SystemExit('ERR const %s: no closing %s in index.html' % (name, end))
    return json.loads(s[i + len('const %s = ' % name):j + 1].replace('<\\/', '</'))


def edmap(repo):
    """EPI-MIS district name -> (dashboard district(s), division), from const EPIM."""
    m = {}
    for r in embedded_const(repo, 'EPIM', array=True):
        m[r['ed']] = (r['ds'], r['dv'])
    return m
