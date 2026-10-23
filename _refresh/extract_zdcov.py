# -*- coding: utf-8 -*-
"""Build out/zd.json: the SNID Sept-26 zero-dose "covered" figures per UC.

Two sources, one payload. The default is the campaign's UC-wise **summary coverage** report
(summary_<campaign>_*.xls / cov_<campaign>.xls): the join is proved first, every report row
must already be tracked with the same reported zero-dose count and the same household target.
`--uc-covered PATH` reads the portal's one-column UC-wise zero-dose covered export
(ucneapreport*.xls), which carries no reported column to prove against, so it joins by UC code,
re-checks its own Total row and reports how many UCs land above their recorded count.
A report cell left blank stays null ("not reported") while an explicit 0 stays 0 ("none covered")
- the campaign tab renders that difference.

Usage: python _refresh/extract_zdcov.py [--out PATH] [--verbose] [--uc-covered PATH]
"""
import argparse
import io
import json
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import covsept
import dashpatch
import extract_mis as em
import srcutil

DS = 'zdcov'
DASH = '–'  # the en dash the campaign tab's band labels use


def band(p, rep, cov):
    """Coverage band, in the campaign tab's own words and decision order."""
    if rep is None:
        return 'Not in campaign'
    if cov is None:
        return 'Coverage not reported'
    if rep == 0:
        return 'No ZDs reported'
    if p > 110:
        return 'Verify (>110%)'
    if p >= 90:
        return 'Good (90%s110%%)' % DASH
    if p >= 80:
        return 'Moderate (80%s90%%)' % DASH
    if p >= 50:
        return 'Low (50%s80%%)' % DASH
    return 'Critical (<50%)'


def rows_tracked(cfg):
    s = srcutil.read_text(os.path.join(cfg['repo'], 'index.html'))
    return json.loads(dashpatch.get_payload(s, 'ZD').replace('<\\/', '</'))


def report(cfg):
    slots = em.entry(cfg, DS).get('slots') or {}
    camp = [c for c, cp in slots.items() if cp == 'S']
    if len(camp) != 1:
        raise SystemExit('ERR zd %s.slots must name exactly one Sept campaign, got %s' % (DS, camp))
    hit = [x for x in em.candidates(cfg, em.DS) if em.campaign_key(x['camp']) == em.campaign_key(camp[0])]
    if not hit:
        raise SystemExit('ERR zd no coverage report found for %s' % camp[0])
    book, rec, notes = em.read_newest(hit[0])
    if book is None:
        raise SystemExit('ERR zd %s unreadable (%s)' % (camp[0], '; '.join(notes)))
    for n in notes:
        srcutil.say('WARN zd skipped %s' % n)
    return camp[0], book, rec


def sept_cols(r, cc):
    """The tracked UC row with this campaign's cS/pS/bS placed after hS, as const ZD stores them."""
    raw = None if (cc is None or not r['rS']) else 100.0 * cc / r['rS']
    keys = list(r.keys())
    at = keys.index('hS') + 1
    row = dict(r)
    for k, v in (('cS', cc), ('pS', None if raw is None else round(raw, 1)),
                 ('bS', band(raw, r['rS'], cc))):
        keys.insert(at, k)
        at += 1
        row[k] = v
    return {k: row[k] for k in keys}


def stats_of(tracked, out):
    words = set([t['bA'] for t in tracked] + [t['bM'] for t in tracked])
    off = sorted(set([o['bS'] for o in out]) - words)
    if off:
        raise SystemExit('ERR zd band label(s) April/May never use: %s' % off)
    cov = sum(o['cS'] for o in out if o['cS'] is not None)
    rep = sum(o['rS'] for o in out if o['rS'] is not None)
    return dict(ucs=len(out), covered=cov, reported=rep,
                with_fig=sum(1 for o in out if o['cS'] is not None),
                explicit0=sum(1 for o in out if o['cS'] == 0),
                not_rep=sum(1 for o in out if o['cS'] is None and o['rS'] is not None),
                over=sum(1 for o in out if o['cS'] is not None and o['rS'] and o['cS'] > o['rS']),
                absent=sum(1 for o in out if o['rS'] is None))


def uc_covered_rows(path):
    """The one-column UC-wise zero-dose covered export -> ([(code, covered|None)], Total|None, file).

Rows are Province / District / Tehsil / UC / UCCode / ZERO DOSE COVERED with a Total row;
the portal saves it as an HTML table named .xls, the real table in the sibling _files sidecar.
UC names are read for nothing but the abort message - the join is on UC code.
"""
    for p in (path, covsept.shell_table_path(path)):
        if not p or not os.path.exists(p):
            continue
        try:
            tbl = max(pd.read_html(io.BytesIO(open(p, 'rb').read())), key=len)
        except Exception:
            continue
        hdr = [covsept.lab(x).lower() for x in tbl.iloc[0]]
        codes = [i for i, h in enumerate(hdr) if h.replace(' ', '') in ('uccode', 'uccode')]
        covs = [i for i, h in enumerate(hdr) if 'zero dose' in h and 'covered' in h]
        if len(codes) != 1 or len(covs) != 1:
            raise SystemExit('ERR zd %s is not a UC-wise zero-dose covered table (header: %s)'
                             % (os.path.basename(path), ' | '.join(hdr)[:300]))
        rows, total = [], None
        for _, x in tbl.iloc[1:].iterrows():
            code = covsept._code(x[codes[0]])
            v = covsept._num(x[covs[0]])
            if re.fullmatch(r'\d+', code):
                rows.append((code, None if v is None else int(v)))
            elif covsept.lab(x[0]).lower() == 'total':
                total = None if v is None else int(v)
        if not rows:
            raise SystemExit('ERR zd no UC rows in %s' % p)
        return rows, total, p
    raise SystemExit('ERR zd cannot read %s' % path)


def build_uc(cfg, path, verbose=False):
    """The Sept covered column straight from the UC-wise zero-dose covered export."""
    tracked = rows_tracked(cfg)
    seen = {}
    for r in tracked:
        if r['c'] in seen:
            raise SystemExit('ERR zd duplicate UC code %s' % r['c'])
        seen[r['c']] = r
    rows, total, used = uc_covered_rows(path)
    index = {}
    for code, cov in rows:
        if code in index:
            raise SystemExit('ERR zd duplicate UC code %s in the export' % code)
        index[code] = cov
        if code not in seen:
            raise SystemExit('ERR zd export row %s is not a tracked UC' % code)
    got = sum(v for _, v in rows if v is not None)
    if total is not None and got != total:
        raise SystemExit('ERR zd rows sum %s but the export Total row says %s' % (got, total))
    out = [sept_cols(r, index.get(r['c'])) for r in tracked]
    stats = stats_of(tracked, out)
    if verbose:
        srcutil.say('ROW zd %s' % json.dumps(out[0], ensure_ascii=False))
    return 'UC-wise zero-dose covered', None, {'path': used}, out, stats


def build(cfg, verbose=False):
    tracked = rows_tracked(cfg)
    camp, book, rec = report(cfg)
    bad = covsept.check_totals(book['uc'], book['tot'], ['tgt', 'zrep', 'zcov'])
    if bad:
        raise SystemExit('ERR zd totals row disagrees (%s)' % '; '.join(bad))
    seen = {}
    for r in tracked:
        if r['c'] in seen:
            raise SystemExit('ERR zd duplicate UC code %s' % r['c'])
        seen[r['c']] = r
    index = {}
    for x in book['uc']:
        if x['code'] in index:
            raise SystemExit('ERR zd duplicate UC code %s in the report' % x['code'])
        index[x['code']] = x
        r = seen.get(x['code'])
        rep = None if x['zrep'] is None else int(x['zrep'])
        tgt = None if x['tgt'] is None else int(x['tgt'])
        if r is None:
            raise SystemExit('ERR zd report row %s (%s / %s) is not tracked' % (x['code'], x['teh'], x['uc']))
        if (r['rS'], r['hS']) != (rep, tgt):
            raise SystemExit('ERR zd %s disagrees with the report: reported %s/%s target %s/%s'
                             % (x['code'], r['rS'], rep, r['hS'], tgt))
    out = []
    for r in tracked:
        x = index.get(r['c'])
        out.append(sept_cols(r, None if x is None or x['zcov'] is None else int(x['zcov'])))
    rep = sum(o['rS'] for o in out if o['rS'] is not None)
    if rep != covsept.totals(book['uc'], 'zrep'):
        raise SystemExit('ERR zd reported sum %s vs report %s' % (rep, covsept.totals(book['uc'], 'zrep')))
    stats = stats_of(tracked, out)
    if verbose:
        srcutil.say('ROW zd %s' % json.dumps(out[0], ensure_ascii=False))
    return camp, book, rec, out, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--uc-covered', help='one-column UC-wise zero-dose covered export (ucneapreport*.xls)')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if a.uc_covered:
        camp, book, rec, out, stats = build_uc(cfg, a.uc_covered, a.verbose)
    else:
        camp, book, rec, out, stats = build(cfg, a.verbose)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'zd.json')
    srcutil.write_text(dest, js)
    srcutil.say('SRC zd %s  (%s export from %s)' % (dest, camp, rec['path']))
    srcutil.say('OK zd %d %s' % (len(js), ' '.join('%s=%s' % (k, format(v, ',')) for k, v in stats.items())))


if __name__ == '__main__':
    main()
