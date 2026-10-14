"""Extract the NEOC intra-campaign monitoring payload (const NOCD).

Reads every icm_*.csv export under the roots (NEOC intra-campaign monitoring
modules: team visits, fixed sites, transit sites, supervisor checklists), groups
them by module (filename) and campaign (Campaign name column), and aggregates
per district. District names are mapped onto the dashboard's CHD.ds spellings.

Output shape:
 {src, asof, camps: {<campaign label>: {
    tv: {<district>: visits},       # team-monitoring visits (sum of '# Teams Monitored')
    uc: {<district>: ucs},          # UC rows covered by team monitoring
    fx: {<district>: sites},        # fixed sites monitored (sum of '# Fixed Sites Monitored')
    sp: {<district>: [chk%, sup%]}, # supervisor checklist % / supported-teams %
    tr: {<district>: visits}}}}     # transit site visits ('# Sites Visited')
Only modules present for a campaign appear.

Usage: python _refresh/extract_noc.py [--source PATH] [--out PATH]
Prints one status line: OK noc <json chars> <summary> | ERR noc <reason>
"""
import argparse
import collections
import csv
import datetime
import fnmatch
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'noc'
MODULES = (('supervisor', 'sp'), ('fixed', 'fx'), ('transit', 'tr'))
COUNT_COL = {'tv': '# Teams Monitored', 'fx': '# Fixed Sites Monitored', 'tr': '# Sites Visited'}
SP_COLS = ('% Checklist Completed', '% Supervisor supported teams')


def chd_const(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const CHD = ')
    if i < 0:
        raise SystemExit('ERR noc const CHD not found in index.html')
    j = s.find('\n', i)
    return json.loads(s[i + len('const CHD = '):j].rstrip().rstrip(';').replace('<\\/', '</'))


def num(v):
    if v is None or str(v).strip() == '':
        return 0.0
    try:
        return float(str(v).replace(',', '').replace('%', ''))
    except ValueError:
        return 0.0


def pct(v):
    f = num(v)
    return round(f, 1)


def module_of(path):
    b = os.path.basename(path).lower()
    for needle, mod in MODULES:
        if needle in b:
            return mod
    return 'tv'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', action='append')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    ds = cfg['auto'][DS]
    if a.source:
        files = list(a.source)
    else:
        files = []
        for root in ds['roots']:
            for pat in ds['patterns']:
                files.extend(glob.glob(os.path.join(root, pat)))
        files = [f for f in files if not any(fnmatch.fnmatch(os.path.basename(f), e) for e in ds.get('exclude', []))]
        files = sorted(set(files), key=lambda p: os.path.getmtime(p), reverse=True)
    files = [f for f in files if os.path.exists(f)]
    if not files:
        raise SystemExit('ERR noc no icm_*.csv exports found under %s' % ds['roots'])

    ref = chd_const(cfg['repo'])
    lower = {d.upper(): d for d in ref['ds']}

    camps = collections.defaultdict(lambda: collections.defaultdict(dict))
    sp_cand = collections.defaultdict(list)  # camp -> [(mtime, is_rollup, {dist: [chk,sup]})]
    used = []
    for path in files:
        mod = module_of(path)
        with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
            rows = list(csv.DictReader(fh))
        if not rows or 'District name' not in rows[0] or 'Campaign name' not in rows[0]:
            print('# noc skip %s (no District/Campaign columns)' % os.path.basename(path))
            continue
        used.append(path)
        seen_camps = collections.Counter()
        n = 0
        for r in rows:
            camp = str(r.get('Campaign name') or '').strip()
            dist = str(r.get('District name') or '').strip()
            if not camp or camp.lower() == 'total' or not dist or dist == '-':
                continue
            key = lower.get(dist.upper())
            if key is None:
                raise SystemExit('ERR noc district %r in %s does not match CHD.ds - layout/naming changed' % (dist, os.path.basename(path)))
            seen_camps[camp] += 1
            if mod == 'sp':
                vals = [pct(r.get(c)) for c in SP_COLS]
                if any(vals):
                    slot = dict(zip(('chk', 'sup'), vals))
                    is_rollup = not str(r.get('UC name') or '').strip()
                    for cand in sp_cand[camp]:
                        if cand[0] == path:
                            cand[1][key] = slot
                            cand[2] = cand[2] and is_rollup
                            break
                    else:
                        sp_cand[camp].append([path, {key: slot}, is_rollup, os.path.getmtime(path)])
                    n += 1
            else:
                v = num(r.get(COUNT_COL[mod]))
                if v:
                    slot = camps[camp][mod]
                    slot[key] = slot.get(key, 0) + (int(v) if abs(v - round(v)) < 1e-9 else v)
                    n += 1
        for camp, cnt in seen_camps.items():
            print('# noc %s -> %s %s (%d rows)' % (os.path.basename(path), camp, mod, cnt))
    if not used:
        raise SystemExit('ERR noc no readable icm_*.csv exports')
    for camp, cands in sp_cand.items():
        rollups = [c for c in cands if c[2]]
        if rollups:
            best = max(rollups, key=lambda c: c[3])
            print('# noc sp %s: using district rollup %s (%d districts)' % (camp, os.path.basename(best[0]), len(best[1])))
            camps[camp]['sp'] = best[1]
        else:
            merged = collections.defaultdict(lambda: [[], []])
            for c in cands:
                for k, v in c[1].items():
                    merged[k][0].append(v['chk'])
                    merged[k][1].append(v['sup'])
            camps[camp]['sp'] = {k: [round(sum(v[0]) / len(v[0]), 1), round(sum(v[1]) / len(v[1]), 1)]
                                 for k, v in merged.items()}
            print('# noc sp %s: no rollup - averaged %d UC-level file(s)' % (camp, len(cands)))
    if 'SNID Sept 2026' not in camps or 'tv' not in camps['SNID Sept 2026']:
        raise SystemExit('ERR noc no team-visit data for SNID Sept 2026 - check exports')
    if len(camps['SNID Sept 2026']['tv']) < 30:
        raise SystemExit('ERR noc team visits cover only %d districts - expected near-full province'
                         % len(camps['SNID Sept 2026']['tv']))

    asof = max(os.path.getmtime(f) for f in used)
    out = {'src': 'NEOC intra-campaign monitoring CSV exports: team visits, fixed sites, '
                  'supervisor checklists, transit sites',
           'asof': datetime.date.fromtimestamp(asof).isoformat(),
           'camps': {c: {m: dict(v) for m, v in sorted(mods.items())} for c, mods in sorted(camps.items())}}
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'noc.json')
    srcutil.write_text(dest, js)
    for f in used:
        print('SRC noc %s' % f)
    print('OK noc %d %s' % (len(js), '; '.join('%s: %s' % (c, ', '.join('%s(%d)' % (m, len(v)) for m, v in sorted(mods.items())))
                                              for c, mods in sorted(out['camps'].items()))))


if __name__ == '__main__':
    main()
