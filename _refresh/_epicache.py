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
# ':uc1' says the cached record also carries the per-Union-Council rows, which the UC monthly
# payload needs; records written before that are re-read once.
AGVER = ','.join(epi_ag.KEYS) + ':uc1'


def load():
    try:
        with open(EPI_CACHE, 'rb') as f:
            cache = pickle.load(f)
    except (OSError, EOFError, ValueError):
        return {}
    # parsed months must match the current panel; an ERR marker is retried, never trusted -
    # the file id carries mtime and size, so a changed file is re-read anyway and a fixed
    # parser must not stay blocked by a parse that failed under the old one.
    return {k: v for k, v in cache.items()
            if not (isinstance(v, dict) and v.get('agv') != AGVER)
            and not (isinstance(v, str) and v.startswith('ERR:'))}


def store(cache):
    os.makedirs(CACHE, exist_ok=True)
    tmp = EPI_CACHE + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(cache, f)
    os.replace(tmp, EPI_CACHE)


def read_consolidated(rec):
    """One monthly export -> {'mo': 'YYYY-MM', 'ed': {epi_district: {n,s,+antigens}},
    'uc': {Uncode: {d,t,u,n,s,+antigens}}}.

    'uc' is empty for the 2024 district-level exports (they carry Distcode, not Uncode).
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
    # the total footer only looks like a data row after the colspan flattening shifts numbers
    # left into the empty cells; the serial number is the one column that cannot be shifted
    # into, so it is what separates the rows from the footer.
    t['S No.'] = pd.to_numeric(t['S No.'], errors='coerce')
    t = t[t['S No.'].notna()].copy()
    # UC-wise exports carry Uncode (numeric per-UC rows, totals lack it); the
    # district-level 2024 exports instead carry Distcode.
    uc = {}
    if 'Uncode' in t.columns:
        t['Uncode'] = t['Uncode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        t = t[t['Uncode'].str.match(r'^\d+$')].copy()
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
    if 'Uncode' in t.columns:
        junkrows = []
        for _, x in t.iterrows():
            ed = str(x['District']).strip()
            if ed.lower() in junk:
                # a handful of Chitral Upper councils come through with district '0'; they are
                # all-zero rows, so they carry no dose and must not create a fake district - but
                # a non-zero one would be silently lost, so it aborts the extract instead.
                nz = [c for c in num if float(x[c]) > 0]
                if nz:
                    raise RuntimeError('%s: UC %s has district "%s" but reports %s'
                                       % (rec['name'], x['Uncode'], ed, ', '.join(nz)))
                junkrows.append(x['Uncode'])
                continue
            uc[x['Uncode']] = {
                'd': ed, 't': str(x['Tehsil']).strip(), 'u': str(x['Union Council']).strip(),
                'n': int(x['Target Newborns']), 's': int(x['Target Surviving Infants']),
                **{k: int(x[c]) for k, c in agc}}
        if junkrows:
            print('  note: %s dropped %d all-zero rows with no district (%s)'
                  % (rec['name'], len(junkrows), ', '.join(sorted(set(junkrows)))))
    return {'mo': mo, 'ed': out, 'uc': uc, 'agv': AGVER}


def months(cache):
    """file_id -> parsed record, for every cached single-month export."""
    return {k: v for k, v in cache.items() if isinstance(v, dict) and v.get('mo')}


def embedded_const(repo, name, array=False):
    """Read an embedded dashboard payload (const NAME) out of index.html.

    The payload is decoded rather than cut at the first '}' - EMETA holds nested objects,
    so a scan for a closing brace stops inside its first month entry.
    """
    import json

    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const %s = ' % name)
    if i < 0:
        raise SystemExit('ERR const %s not found in index.html' % name)
    i += len('const %s = ' % name)
    try:
        obj, _ = json.JSONDecoder().raw_decode(s[i:].replace('<\\/', '</'))
    except ValueError as ex:
        raise SystemExit('ERR const %s cannot be read from index.html: %s' % (name, ex))
    if array and not isinstance(obj, list) or not array and not isinstance(obj, dict):
        raise SystemExit('ERR const %s is not a%s' % (name, 'n array' if array else 'n object'))
    return obj


def edmap(repo):
    """EPI-MIS district name -> (dashboard district(s), division), from const EPIM."""
    m = {}
    for r in embedded_const(repo, 'EPIM', array=True):
        m[r['ed']] = (r['ds'], r['dv'])
    return m
