# -*- coding: utf-8 -*-
"""Build out/zd.json: the SNID Sept-26 zero-dose "covered" figures per UC.

The Sept coverage report is joined to the dashboard's tracked UCs by UC code, and the join is
proved first: every report row must already be tracked with the same reported zero-dose count
and the same household target. A report cell left blank stays null ("not reported") while an
explicit 0 stays 0 ("none covered") - the campaign tab renders that difference.

Usage: python _refresh/extract_zdcov.py [--out PATH] [--verbose]
"""
import argparse
import json
import os
import sys

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
        cc = None if x is None or x['zcov'] is None else int(x['zcov'])
        raw = None if (cc is None or not r['rS']) else 100.0 * cc / r['rS']
        keys = list(r.keys())
        at = keys.index('hS') + 1
        row = dict(r)
        for k, v in (('cS', cc), ('pS', None if raw is None else round(raw, 1)),
                     ('bS', band(raw, r['rS'], cc))):
            keys.insert(at, k)
            at += 1
            row[k] = v
        out.append({k: row[k] for k in keys})
    words = set([t['bA'] for t in tracked] + [t['bM'] for t in tracked])
    off = sorted(set([o['bS'] for o in out]) - words)
    if off:
        raise SystemExit('ERR zd band label(s) April/May never use: %s' % off)
    cov = sum(o['cS'] for o in out if o['cS'] is not None)
    rep = sum(o['rS'] for o in out if o['rS'] is not None)
    if rep != covsept.totals(book['uc'], 'zrep'):
        raise SystemExit('ERR zd reported sum %s vs report %s' % (rep, covsept.totals(book['uc'], 'zrep')))
    if verbose:
        srcutil.say('ROW zd %s' % json.dumps(out[0], ensure_ascii=False))
    stats = dict(ucs=len(out), covered=cov, reported=rep,
                 with_fig=sum(1 for o in out if o['cS'] is not None),
                 explicit0=sum(1 for o in out if o['cS'] == 0),
                 not_rep=sum(1 for o in out if o['cS'] is None and o['rS'] is not None),
                 absent=sum(1 for o in out if o['rS'] is None))
    return camp, book, rec, out, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    camp, book, rec, out, stats = build(cfg, a.verbose)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'zd.json')
    srcutil.write_text(dest, js)
    srcutil.say('SRC zd %s  (%s export from %s)' % (dest, camp, rec['path']))
    srcutil.say('OK zd %d %s' % (len(js), ' '.join('%s=%s' % (k, format(v, ',')) for k, v in stats.items())))


if __name__ == '__main__':
    main()
