"""Extract the upcoming-campaign scope payload (const SND) from the Final Scope workbook.

Usage: python _refresh/extract_snd.py [--source PATH] [--out PATH] [--allow-unknown-districts]
Prints one status line: OK snd <json chars> <summary> | ERR snd <reason>
"""
import argparse
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'snd'


def zd_divisions(repo):
    """district -> division, taken from the dashboard's own ZD payload so filters line up."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR snd const ZD not found in index.html')
    j = s.find('\n', i)
    zd = json.loads(s[i + len('const ZD = '):j].rstrip().rstrip(';'))
    div = {}
    for r in zd:
        div[r['d']] = r['dv']
    return div


UC_COLS = {'dist': 'District', 'teh': 'Tehsil', 'uc': 'UC', 'code': 'Ucode', 'tg': 'Target'}


def uc_header(rows):
    """UC Wise carries its header on the first row whose first cell is 'Province'."""
    for r in rows[:10]:
        cells = [('' if c is None else str(c).strip()) for c in r]
        if cells and cells[0].lower() == 'province':
            idx = {}
            for k, name in UC_COLS.items():
                if name not in cells:
                    raise SystemExit('ERR snd UC Wise header has no %r column (%s)' % (name, cells))
                idx[k] = cells.index(name)
            return idx
    raise SystemExit('ERR snd UC Wise header row not found')


def build(src_path, cfg, repo, allow_unknown=False):
    import openpyxl
    ds = cfg['auto'][DS]
    k = ds['config']
    rename = k.get('rename') or {}
    d5 = k.get('days_5_districts') or []
    n5, n3 = k.get('days_5', 5), k.get('days_3', 3)

    wb = openpyxl.load_workbook(src_path, read_only=True, data_only=True)
    sheets = ds.get('sheets') or ['District', 'UC Wise']
    for sh in sheets:
        if sh not in wb.sheetnames:
            raise SystemExit('ERR snd sheet %r missing (has %s)' % (sh, wb.sheetnames))
    drows = [r[:5] for r in wb[sheets[0]].iter_rows(values_only=True) if r and r[0] == 'KP']
    uall = [r for r in wb[sheets[1]].iter_rows(values_only=True) if r]
    wb.close()
    uix = uc_header(uall)
    urows = [r for r in uall if r and r[0] == 'KP']
    if len(drows) < 5 or not urows:
        raise SystemExit('ERR snd only %d district rows / %d UC rows' % (len(drows), len(urows)))

    div = zd_divisions(repo)
    d = []
    for r in drows:
        name = rename.get(str(r[1]).strip(), str(r[1]).strip())
        d.append([name, div.get(name, ''), str(r[2]).strip(), int(r[3]), int(r[4])])
    unknown = [x[0] for x in d if not x[1]]
    if unknown and not allow_unknown:
        raise SystemExit('ERR snd districts not in dashboard ZD data (no division): %s '
                         '(add them to config.rename or pass --allow-unknown-districts)' % unknown)
    d.sort(key=lambda r: -r[4])
    di = {r[0]: i for i, r in enumerate(d)}
    dvs = sorted({r[1] for r in d if r[1]})

    teh, ti, u = [], {}, []
    for r in urows:
        dist = str(r[uix['dist']]).strip()
        dist = rename.get(dist, dist)
        t = str(r[uix['teh']]).strip()
        if t not in ti:
            ti[t] = len(teh)
            teh.append(t)
        u.append([dist, ti[t], str(r[uix['uc']]).strip(), str(r[uix['code']]), int(r[uix['tg']])])
    missing = sorted({r[0] for r in u if r[0] not in di})
    if missing and not allow_unknown:
        raise SystemExit('ERR snd UC rows for districts absent from the District sheet: %s' % missing)
    u = [r for r in u if r[0] in di]
    u = [[di[r[0]], r[1], r[2], r[3], r[4]] for r in u]
    u.sort(key=lambda r: (r[0], -r[4]))

    snd = {'n': k['name'], 'st': k['start'], 'src': os.path.basename(src_path),
           'dv': dvs, 'd': d, 't': teh, 'u': u, 'd5': d5, 'n5': n5, 'n3': n3}
    day1 = sum(r[4] / (n5 if r[0] in d5 else n3) for r in d)
    summary = '%d districts, %d tehsils, %d UCs, target %s, day-1 %s' % (
        len(d), len(teh), len(u), format(sum(r[4] for r in d), ','), format(int(round(day1)), ','))
    return snd, summary, unknown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    ap.add_argument('--allow-unknown-districts', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR snd no scope workbook found under %s' % cfg['auto'][DS]['roots'])
    snd, summary, unknown = build(rec['path'], cfg, cfg['repo'], a.allow_unknown_districts)
    js = srcutil.dumps(snd)
    dest = a.out or os.path.join(srcutil.OUT, 'snd.json')
    srcutil.write_text(dest, js)
    if unknown:
        print('WARN snd districts without a division:', unknown)
    print('SRC snd %s' % rec['path'])
    print('OK snd %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
