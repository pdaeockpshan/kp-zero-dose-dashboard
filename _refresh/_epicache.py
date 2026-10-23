"""Shared per-file parse cache for the EPI-MIS Consolidated monthly exports.

The monthly facility-wise exports are ~7.4 MB HTML-table files that take pandas
tens of seconds each to parse, and several extractors need the same parse, so the
per-district aggregates are cached under _refresh/cache/ keyed by srcutil.file_id
(path + mtime + size). Extractors run sequentially inside refresh.py run, so a
plain dict pickled to disk is safe. Cached month records carry the antigen-set
version they were parsed with; entries from an older panel are dropped so the
files are re-read and gain the new doses.
"""
import os
import pickle

import epi_ag
import srcutil

CACHE = os.path.join(srcutil.HERE, 'cache')
EPI_CACHE = os.path.join(CACHE, 'epi25mon.pkl')
AGVER = ','.join(epi_ag.KEYS)


def load():
    try:
        with open(EPI_CACHE, 'rb') as f:
            cache = pickle.load(f)
    except (OSError, EOFError, ValueError):
        return {}
    # skip markers (False / 'ERR: ...') stay; parsed months must match the current panel
    return {k: v for k, v in cache.items()
            if not isinstance(v, dict) or v.get('agv') == AGVER}


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

    AG = epi_ag.AG  # (key, source column, label, target, core)
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
    need = ['District', 'Target Newborns', 'Target Surviving Infants'] + [a[1] for a in AG if a[4]]
    miss = [c for c in need if c not in t.columns]
    if miss:
        raise RuntimeError('monthly export %s is missing columns %s' % (rec['name'], miss))
    agc = [(a[0], a[1]) for a in AG if a[1] in t.columns]
    # UC-wise exports carry Uncode (numeric per-UC rows, totals lack it); the
    # district-level 2024 exports instead carry Distcode.
    if 'Uncode' in t.columns:
        t = t[pd.to_numeric(t['Uncode'], errors='coerce').notna()].copy()
    elif 'Distcode' in t.columns:
        t = t[pd.to_numeric(t['Distcode'], errors='coerce').notna()].copy()
    num = ['Target Newborns', 'Target Surviving Infants'] + [c for _, c in agc]
    for c in num:
        t[c] = pd.to_numeric(t[c], errors='coerce').fillna(0)
    t['District'] = t['District'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    out = {}
    junk = {'', '0', '0.0', 'nan', 'none', 'null', 'total'}
    for ed, g in t.groupby('District'):
        if ed.strip().lower() in junk:
            continue
        out[ed] = {'n': int(g['Target Newborns'].sum()), 's': int(g['Target Surviving Infants'].sum()),
                   **{k: int(g[c].sum()) for k, c in agc}}
    return {'mo': mo, 'ed': out, 'agv': AGVER}


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
