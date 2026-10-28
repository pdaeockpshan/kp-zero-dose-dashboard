"""UC x month dose counts for the EPI section (const EPIUC).

EPIM carries the district x month panel; the UC-wise monthly exports behind it also carry
every union council, and the numbers tables need that grain so a downloaded month can be
read at UC level instead of only as a district total. Only the UC-wise monthly exports can
supply it: the 2024 files are district summaries (no Uncode) and 2026 has no monthly export
on disk at all, so this payload covers exactly the months that have a UC row in the cache.

Rows are anchored to the embedded EPI payload by Uncode, name and district - the same rule
extract_epi_ytd uses - so a UC cannot enter or change identity through this file. Every
month's UC rows are then re-added per district and compared with EPIM's district figure for
that month; a mismatch aborts the extract rather than publishing two numbers for one cell.

Usage: python _refresh/extract_epi_ucm.py [--out PATH]
Prints: OK epiuc <json chars> <summary> | ERR epiuc <reason>
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import epi_ag
import srcutil

DS = 'epiuc'


def build(cfg):
    e = cfg['auto']['epim']  # same exports, same cache as the district-month payload
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no Consolidated files under %s' % (DS, e['roots']))
    cache = _epicache.load()
    by_mo = {}
    newest = None
    for rec in files:
        fid = srcutil.file_id(rec)
        rec_o = cache.get(fid)
        if rec_o is None:
            print('# epiuc parsing %s ...' % rec['name'])
            try:
                rec_o = _epicache.read_consolidated(rec)
            except Exception as ex:
                cache[fid] = 'ERR: %s' % str(ex).split(chr(10))[0][:120]
                print('WARN epiuc skipped %s (cannot parse: %s)' % (rec['name'], ex))
                continue
            cache[fid] = rec_o if rec_o is not None else False
        if not isinstance(rec_o, dict) or not rec_o.get('uc'):
            continue
        if rec_o['mo'] in by_mo:
            # the same month can sit in both D:\AMAZON DATA and Downloads; discovery is
            # newest-first, so the copy already held is the newer download.
            print('  note: %s also carries %s - keeping %s'
                  % (rec['name'], rec_o['mo'], by_mo[rec_o['mo']][1]))
            continue
        by_mo[rec_o['mo']] = (rec_o['uc'], rec['name'], rec)
        if newest is None or rec['mtime'] > newest['mtime']:
            newest = rec
    _epicache.store(cache)
    by_mo = {mo: v[0] for mo, v in by_mo.items()}
    if not by_mo:
        raise SystemExit('ERR %s no UC-wise monthly export found' % DS)

    emeta = _epicache.embedded_const(cfg['repo'], 'EMETA')
    months = sorted(m for m in by_mo if m in {x['mo'] for x in emeta['months']})
    dropped = sorted(set(by_mo) - set(months))
    if dropped:
        print('  note: UC-wise exports outside the published month index are not used: %s'
              % ', '.join(dropped))
    part = [x['mo'] for x in emeta['months'] if x.get('pt')]
    part = [m for m in months if m in part]
    if part:
        print('  note: %s is a part-report (the YTD export carries the full month at district '
              'level), so it is not published at UC grain: %s' % (part[0], ', '.join(part)))
        months = [m for m in months if m not in part]
    if not months:
        raise SystemExit('ERR %s no usable UC-wise month left' % DS)

    base = _epicache.embedded_const(cfg['repo'], 'EPI', array=True)
    epim = {(r['mo'], r['ed']): r for r in
            _epicache.embedded_const(cfg['repo'], 'EPIM', array=True)}

    first = by_mo[months[0]]
    codes = set(first)
    for mo in months:
        if set(by_mo[mo]) != codes:
            miss = sorted(codes - set(by_mo[mo]))[:5]
            extra = sorted(set(by_mo[mo]) - codes)[:5]
            raise SystemExit('ERR %s %s lists %d UCs, %s lists %d (missing %s, new %s) - '
                             'a UC appearing mid-year needs checking before it is published'
                             % (DS, months[0], len(codes), mo, len(by_mo[mo]), miss, extra))
    bad = [r['ec'] for r in base if r['ec'] not in codes]
    if bad:
        raise SystemExit('ERR %s %d UC(s) in the dashboard are not in the monthly exports '
                         '(first: %s)' % (DS, len(bad), ', '.join(bad[:5])))
    diff = []
    for r in base:
        u = first[r['ec']]
        if u['u'].upper() != str(r['en']).upper() or u['d'] != r['ed']:
            diff.append('%s %s/%s vs %s/%s' % (r['ec'], u['d'], u['u'], r['ed'], r['en']))
    if diff:
        raise SystemExit('ERR %s UC identity changed (%s)' % (DS, '; '.join(diff[:5])))

    sample = next(iter(first.values()))
    ext = [a[0] for a in epi_ag.AG if a[0] in sample]
    keys = ['n', 's'] + [a[0] for a in epi_ag.AG if a[0] in sample]
    if len(keys) < 3:
        raise SystemExit('ERR %s the UC rows carry no antigen doses (fields: %s)'
                         % (DS, ', '.join(sorted(sample))))    # re-add each month's UC rows per district and hold them against EPIM
    for mo in months:
        per = {}
        for code, u in by_mo[mo].items():
            d = per.setdefault(u['d'], {k: 0 for k in keys})
            for k in keys:
                d[k] += u[k]
        for ed, v in per.items():
            ref = epim.get((mo, ed))
            if ref is None:
                raise SystemExit('ERR %s EPIM has no %s row for %s' % (DS, mo, ed))
            for k in keys:
                if ref.get(k) != v[k]:
                    raise SystemExit('ERR %s %s / %s: UC rows add to %d, EPIM says %s'
                                     % (DS, mo, ed, v[k], ref.get(k)))

    rows = []
    zero = 0
    for r in base:
        u = first[r['ec']]
        for k in keys:
            if not any(by_mo[mo][r['ec']][k] for mo in months):
                zero += 1
        rows.append([[by_mo[mo][r['ec']][k] for mo in months] for k in keys])

    def mlab(mo):
        return (next((m['l'] for m in emeta['months'] if m['mo'] == mo), mo))

    payload = {
        'per': '%s - %s' % (mlab(months[0]), mlab(months[-1])) if len(months) > 1 else mlab(months[0]),
        'from': months[0], 'to': months[-1],
        'mo': [{'mo': mo, 'l': mlab(mo)} for mo in months],
        'k': keys,
        'ucs': len(base),
        'src': 'EPI-MIS UC-wise monthly exports %s to %s (%d files)' % (months[0], months[-1], len(months)),
        'got': srcutil.mtime_str(newest),
        'rows': rows,
    }
    summary = ('%d months x %d UCs x %d fields, extras %s, %d all-zero UC-dose series; '
               'every district-month re-adds to EPIM'
               % (len(months), len(base), len(keys), ','.join(ext) or 'none', zero))
    return payload, payload['per'], summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # interface parity: every cached match is read
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    payload, per, summary = build(cfg)
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'epi_ucm.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s | %s' % (DS, len(js), per, summary))


if __name__ == '__main__':
    main()
