# -*- coding: utf-8 -*-
"""Reader for the EOC portal "Summary" UC-wise coverage export (one campaign per file).

Two physical forms exist:
  * the saved-portal form  - one self-contained HTML table (``cov_<campaign>.xls``, whose
    stacked header rows pandas reads as a MultiIndex);
  * the direct export form - a small ``.xls`` shell whose table lives in the sibling
    ``<name>_files/sheet001.htm``, with the header rows carried as data.

Both are read into one shape: UC-level rows keyed by the canonical names below, plus the
workbook totals row. Column labels are matched, never assumed by position, so a re-ordered
export fails loudly instead of silently shifting figures.

No personal data - this report is UC-level aggregates only.
"""
import io
import os
import re

import pandas as pd

# canonical key -> exact joined label (admin columns)
EXACT = {'prov': 'Province', 'div': 'Division', 'dist': 'District', 'teh': 'Tehsil',
         'uc': 'UC', 'code': 'UC Code'}
# canonical key -> (must-all-appear, must-none-appear) keywords on the lower-cased label.
# The portal leaves the "NA" sub-column unnamed in the direct export, so those keys match
# on the group label and exclude the sibling sub-columns.
WANT = {
    'tgt': (('household target',), ()),
    'vacc': (('household children vaccinated', '| total'), ()),
    'cct': (('household children vaccinated', '%'), ()),
    'rna': (('recorded missed',), ('ref', 'total')),
    'rrf': (('recorded missed', 'ref'), ('total covered',)),
    'rtot': (('recorded missed', 'total'), ()),
    'cam_na': (('covered during campaign',), ('ref', 'total', '%')),
    'cam_rf': (('covered during campaign', 'ref'), ('total covered',)),
    'cam_t': (('covered during campaign', 'total covered', 'total'), ('%')),
    'cam_p': (('covered during campaign', 'total covered', '%'), ()),
    'cu_na': (('covered during catchup',), ('ref', 'total', '%')),
    'cu_rf': (('covered during catchup', 'ref'), ('total covered',)),
    'cu_t': (('covered during catchup', 'total covered', 'total'), ('%')),
    'cu_p': (('covered during catchup', 'total covered', '%'), ()),
    'ex_na': (('covered extended catchup',), ('ref', 'total', '%')),
    'ex_rf': (('covered extended catchup', 'ref'), ('total covered',)),
    'ex_t': (('covered extended catchup', 'total covered', 'total'), ('%')),
    'ex_p': (('covered extended catchup', 'total covered', '%'), ()),
    'sna': (('still missed', 'still na'), ()),
    'srf': (('still missed', 'still ref'), ()),
    'slo': (('still missed', 'left over'), ()),
    'stot': (('still missed', '| total'), ('%',)),
    'spct': (('still missed', '| total', '%'), ()),
    'zrep': (('zero routine', 'reported'), ()),
    'zcov': (('zero dose', 'covered'), ()),
    'afp': (('afp',), ()),
    'vials': (('received vials',), ()),
    'sealed': (('remaining sealed',), ()),
}
PCT = {'cct', 'cam_p', 'cu_p', 'ex_p', 'spct'}
REQUIRED = ['prov', 'div', 'dist', 'teh', 'uc', 'code', 'tgt', 'vacc',
            'rna', 'rrf', 'rtot', 'sna', 'srf', 'slo', 'stot', 'zrep', 'zcov', 'afp']
KP_PROVINCES = ('KP', 'KPTD', 'KHYBER PAKHTUNKHWA')


def lab(s):
    return re.sub(r'\s+', ' ', str(s if s is not None else '')).strip()


def shell_table_path(path):
    """The companion table file written next to a small .xls shell, if present."""
    h = os.path.join(os.path.splitext(path)[0] + '_files', 'sheet001.htm')
    return h if os.path.exists(h) else None


def _code(v):
    s = lab(v)
    return s[:-2] if s.endswith('.0') else s


def _num(v):
    """Count: None when the cell is blank (not reported), a number otherwise."""
    s = lab(v).replace(',', '').replace('%', '')
    if s in ('', '-', 'nan', 'none', 'na'):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(round(f)) if abs(f - round(f)) < 1e-9 else f


def _pct(v):
    s = lab(v).replace(',', '').replace('%', '')
    if s in ('', '-', 'nan', 'none'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _labels(t):
    """Joined column labels such as 'Still Missed (based on HH Target) | Still NA | n',
    built from the MultiIndex header or from header rows carried as data."""
    if isinstance(t.columns, pd.MultiIndex):
        return [' | '.join(dict.fromkeys(x for x in (lab(c) for c in col)
                                         if x and x.lower() != 'nan')) for col in t.columns]
    kcol = next((i for i in range(len(t.columns))
                 if any(lab(t.iloc[r, i]).lower() == 'uc code' for r in range(min(8, len(t))))), None)
    if kcol is None:
        raise SystemExit('ERR cov no UC Code header found')
    n = 0
    while n < min(8, len(t)) and lab(t.iloc[n, kcol]).lower() == 'uc code':
        n += 1
    out = []
    for i in range(len(t.columns)):
        seen = []
        for r in range(n):
            v = lab(t.iloc[r, i])
            if v and v.lower() != 'nan' and v not in seen:
                seen.append(v)
        out.append(' | '.join(seen))
    return out


def columns(labels):
    """canonical key -> column index; aborts on a missing required column or a double match."""
    idx = {}
    for key, want in EXACT.items():
        hits = [i for i, c in enumerate(labels) if c.lower() == want.lower()]
        if not hits:
            raise SystemExit('ERR cov column %r not found (labels: %s)' % (key, ' | '.join(labels)[:600]))
        idx[key] = hits[0]
    for key, spec in WANT.items():
        inc, exc = spec
        hits = [i for i, c in enumerate(labels)
                if c and all(k in c.lower() for k in inc)
                and not any(k in c.lower() for k in exc)]
        if not hits:
            if key in REQUIRED:
                raise SystemExit('ERR cov column %r not found in this export (labels: %s)'
                                 % (key, ' | '.join(labels)[:600]))
            continue
        best = min(len(labels[h]) for h in hits)
        cand = [h for h in hits if len(labels[h]) == best]
        if len(cand) > 1:
            raise SystemExit('ERR cov column %r ambiguous: %s'
                             % (key, [labels[h] for h in cand]))
        idx[key] = cand[0]
    return idx


def read(path):
    """{'file','uc':[row],'tot':row|None,'cols':{key:label},'labels':[...]}"""
    tbl, used, err = None, None, None
    for p in (path, shell_table_path(path)):
        if not p or not os.path.exists(p):
            err = 'file not found: %s' % p
            continue
        # the portal saves this report three ways: an HTML table named .xls (with the real table
        # either inline or in the _files/sheet001.htm sidecar), and since 23-Oct-2026 a genuine
        # .xlsx. Header rows come through as data in every form, so _labels() finds them.
        try:
            tables = pd.read_html(io.BytesIO(open(p, 'rb').read()))
        except Exception as ex:
            if not re.search(r'\.xlsx?$', p, re.I):
                err = 'cannot read %s: %s' % (os.path.basename(p), str(ex)[:120])
                continue
            try:
                tables = [pd.read_excel(p, header=None)]
            except Exception as ex2:
                err = 'cannot read %s: %s' % (os.path.basename(p), str(ex2)[:120])
                continue
        if tables:
            tbl, used = max(tables, key=len), p
            break
    if tbl is None:
        raise SystemExit('ERR cov %s (%s)' % (err, path))
    labels = _labels(tbl)
    idx = columns(labels)
    tbl = tbl.copy()
    tbl.columns = range(len(tbl.columns))   # address columns by position from here on
    rows = [r for _, r in tbl.iterrows() if re.fullmatch(r'\d+', _code(r[idx['code']]))]
    if not rows:
        raise SystemExit('ERR cov no UC rows in %s' % used)
    pv = [lab(r[idx['prov']]).upper() for r in rows]
    if any(x in KP_PROVINCES for x in pv):
        rows = [r for r, x in zip(rows, pv) if x in KP_PROVINCES]

    def row(r):
        d = {}
        for k, i in idx.items():
            d[k] = _pct(r[i]) if k in PCT else _num(r[i])
        d['code'] = _code(r[idx['code']])
        for k in EXACT:
            d[k] = lab(r[idx[k]])
        return d

    uc = [row(r) for r in rows]
    tot = None
    for _, r in tbl.iterrows():
        if lab(r[idx['dist']]) in ('', '-') and _num(r[idx['tgt']]):
            tot = row(r)
            break
    return {'file': used, 'uc': uc, 'tot': tot, 'shell': shell_table_path(path) is not None,
            'cols': {k: labels[i] for k, i in idx.items()}, 'labels': labels,
            'n_raw': int(len(tbl))}


def totals(rows, key):
    return sum(r[key] or 0 for r in rows)


def check_totals(rows, tot, keys):
    """Compare the summed UC rows against the workbook's own totals row; returns notes."""
    notes = []
    if not tot:
        return ['workbook totals row not found']
    for k in keys:
        want, got = tot.get(k), totals(rows, k)
        if want is None:
            notes.append('%s: workbook total blank' % k)
        elif abs((want or 0) - got) > max(0.5, abs(want) * 0.002):
            notes.append('%s: UC rows %s vs workbook total %s' % (k, format(got, ','), format(want, ',')))
    return notes
