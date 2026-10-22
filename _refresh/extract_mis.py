# -*- coding: utf-8 -*-
"""Missed children and refusals per UC per campaign (const MIS, MISM).

Sources are the EOC portal's UC-wise summary coverage reports - one file per campaign.
Two physical forms are accepted (see covsept.py): the saved `cov_<campaign>.xls` copies in
the repo's `_portal` folder, and the direct `summary_<campaign>_<date>_<time>.xls` export
with its sibling `_files/sheet001.htm`. When the same campaign exists in several places the
newest mtime wins, so a fresh portal export overrides the saved copy without touching it.

Rows are UCs the dashboard already tracks (matched by UC code against const ZD); a coverage
row for an untracked UC is reported and skipped rather than invented. Values are counts,
blank cells become 0 exactly as the campaign tab's arithmetic expects - the difference
between "not reported" and "zero" is carried by ZD, not here.

Payload `const MIS`: [{c, ci, tg, vc, rna, rrf, sna, srf, slo}] - ci indexes MISM.camps.
Payload `const MISM`: {camps: [labels newest-first], n: rows}.

Usage: python _refresh/extract_mis.py [--out PATH] [--mis-out PATH] [--verbose]
Prints: SRC mis <path> (one per campaign) | OK mis <chars> <summary> | ERR mis <reason>
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import covsept
import srcutil


DS = 'mism'
MON = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7,
       'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12}
WORDS = '|'.join(sorted(MON, key=lambda k: -len(k)))
FILE_RE = re.compile(r'(?i)^cov_(.+)\.xls$|^summary_(.+?)_(\d{4}-\d{2}-\d{2})_(\d{6})\.xls$')
VALUE_KEYS = (('tg', 'tgt'), ('vc', 'vacc'), ('rna', 'rna'), ('rrf', 'rrf'),
              ('sna', 'sna'), ('srf', 'srf'), ('slo', 'slo'))


def entry(cfg, ds=DS):
    """Config lives under manual (two payloads, so refresh.py run cannot drive it)."""
    return cfg['auto'].get(ds) or cfg['manual'][ds]


def campaign_of(path):
    m = FILE_RE.match(os.path.basename(path))
    if not m:
        return None
    # group(1) = cov_<campaign>.xls, group(2) = summary_<campaign>_<date>_<time>.xls
    return (m.group(1) or m.group(2)).strip()


def asof_key(name):
    """Sort by the export stamp in the filename, falling back to the file mtime."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{6})', name)
    return m.group(1) + m.group(2) if m else ''


def order(camp):
    """(year, month) sort key for a campaign name; unknown campaigns sort last."""
    s = str(camp).lower()
    m = re.search(r'(%s)[\s\-_]*(\d{2,4})' % WORDS, s)
    if not m:
        return (0, 0)
    y = int(m.group(2))
    return (y + 2000 if y < 100 else y, MON[m.group(1)])


def label(camp):
    """'SNID Sept 2026' -> 'SNID Sept-26', matching the campaign tab's existing labels."""
    c = re.sub(r'\s+', ' ', str(camp)).strip()
    m = re.search(r'(%s)[\s\-_]*(\d{2,4})' % WORDS, c, re.I)
    if not m:
        return c
    kind = c[:m.start(1)].strip(' -_').upper() or 'Campaign'
    abbr = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'][MON[m.group(1).lower()] - 1]
    return '%s %s-%s' % (kind, abbr, m.group(2)[-2:])


def zd_codes(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR mis const ZD not found in index.html')
    j = s.find('\n', i)
    return {r['c'] for r in json.loads(s[i + len('const ZD = '):j].rstrip().rstrip(';').replace('<\\/', '</'))}


def campaign_key(camp):
    """Group by the normalised campaign so 'SNID Sept 2026' and 'SNID Sept 2026 ' share a slot."""
    return re.sub(r'\s+', ' ', str(camp)).strip().lower()


def candidates(cfg, ds=DS):
    """Campaign -> every matching source file, newest export first (export stamp, then mtime)."""
    allow = {campaign_key(c) for c in entry(cfg, ds).get('campaigns') or []}
    pool = {}
    for scan in entry(cfg, ds)['scans']:
        for rec in srcutil.discover(scan):
            camp = campaign_of(rec['path'])
            if not camp or order(camp) == (0, 0):
                continue
            if allow and campaign_key(camp) not in allow:
                continue
            pool.setdefault(campaign_key(camp), {'camp': camp, 'files': []})['files'].append(rec)
    for slot in pool.values():
        slot['files'].sort(key=lambda r: (asof_key(r['name']), r['mtime']), reverse=True)
    return sorted(pool.values(), key=lambda x: order(x['camp']), reverse=True)


def read_newest(slot):
    """Newest readable export for a campaign - later same-round re-exports are partial dumps
    or a different report shape, so an unreadable candidate falls through with a note."""
    notes = []
    for i, rec in enumerate(slot['files']):
        try:
            book = covsept.read(rec['path'])
        except SystemExit as ex:
            notes.append('%s (%s)' % (os.path.basename(rec['path']), str(ex).replace('ERR cov ', '')[:80]))
            continue
        except Exception as ex:
            notes.append('%s (%s)' % (os.path.basename(rec['path']), str(ex)[:80]))
            continue
        if i:
            notes.append('used %s after %d unreadable newer export(s)' % (os.path.basename(rec['path']), i))
        return book, rec, notes
    return None, None, notes


def build(cfg, verbose=False):
    repo = cfg['repo']
    tracked = zd_codes(repo)
    want = entry(cfg).get('campaigns') or []
    picked = candidates(cfg)
    if not picked:
        raise SystemExit('ERR mis no coverage reports found under %s'
                         % [s.get('roots') for s in entry(cfg)['scans']])
    camps, mis, warn = [], [], []
    for slot in picked:
        camp = slot['camp']
        lab = label(camp)
        book, rec, notes = read_newest(slot)
        if book is None:
            raise SystemExit('ERR mis %s: no readable coverage report (%s)' % (lab, '; '.join(notes)))
        for n in notes:
            warn.append('%s: skipped %s' % (lab, n))
        rows = book['uc']
        k = len(camps)
        disagreements = covsept.check_totals(rows, book['tot'], [v for _, v in VALUE_KEYS])
        if disagreements:
            raise SystemExit('ERR mis %s: totals row disagrees (%s)' % (lab, '; '.join(disagreements)))
        unmatched = sorted({r['code'] for r in rows if r['code'] not in tracked})
        keep = [r for r in rows if r['code'] in tracked]
        if unmatched:
            warn.append('%s: %d UCs in the coverage report not tracked by this dashboard (skipped): %s'
                        % (lab, len(unmatched), ', '.join(unmatched[:6])))
        if len(keep) < 100:
            raise SystemExit('ERR mis %s: only %d tracked UCs' % (lab, len(keep)))
        seen = set()
        for r in keep:
            if r['code'] in seen:
                raise SystemExit('ERR mis %s: duplicate UC code %s' % (lab, r['code']))
            seen.add(r['code'])
            row = {'c': r['code'], 'ci': k}
            for out, src in VALUE_KEYS:
                v = r.get(src)
                row[out] = int(v) if isinstance(v, (int, float)) else 0
            mis.append(row)
        camps.append(lab)
        print('SRC mis %s  (%d UCs, %d tracked, %s vaccinated, %s still missed)'
              % (rec['path'], len(rows), len(keep),
                 format(sum(x['vc'] for x in mis if x['ci'] == k), ','),
                 format(sum(x['sna'] + x['srf'] + x['slo'] for x in mis if x['ci'] == k), ',')))
    missing = [c for c in want if campaign_key(c) not in {campaign_key(s['camp']) for s in picked}]
    if missing:
        raise SystemExit('ERR mis tracked campaign(s) with no coverage report: %s' % ', '.join(missing))
    if len(camps) != len(want) and want:
        raise SystemExit('ERR mis %d campaigns found, %d tracked (%s)' % (len(camps), len(want), camps))
    for w in warn:
        print('WARN mis %s' % w)
    return camps, mis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', help='write MISM json here')
    ap.add_argument('--mis-out', help='write MIS json here')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    camps, mis = build(cfg, a.verbose)
    mism = {'camps': camps, 'n': len(mis)}
    js_mis = srcutil.dumps(mis)
    js_mism = srcutil.dumps(mism)
    for dest, js in ((a.mis_out or os.path.join(srcutil.OUT, 'mis.json'), js_mis),
                     (a.out or os.path.join(srcutil.OUT, 'mism.json'), js_mism)):
        srcutil.write_text(dest, js)
    per = {}
    for r in mis:
        p = per.setdefault(r['ci'], [0, 0, 0])
        p[0] += 1
        p[1] += r['vc']
        p[2] += r['sna'] + r['srf'] + r['slo']
    summary = '%d rows, %s' % (len(mis), '; '.join('%s: %d UCs, %s vaccinated, %s still missed'
                                                   % (camps[k], per[k][0], format(per[k][1], ','),
                                                      format(per[k][2], ','))
                                                   for k in sorted(per)))
    print('OK mis %d+%d %s' % (len(js_mis), len(js_mism), summary))


if __name__ == '__main__':
    main()
