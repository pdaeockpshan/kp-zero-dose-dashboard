# -*- coding: utf-8 -*-
"""Extract the separate fIPV scope for Peshawar and Khyber (const FIPV).

Sources
  fIPV Peshawar and Khyber UCs.xlsx   UC detail: HH <5, fIPV 4m-10y, school targets
  fIPV Peshawar & Khyber Scope.pptx   scope summary: new vs existing fIPV UCs + totals

The workbook has no new/existing flag. The slide does, and its four "Total UCs"
blocks are the authority: Peshawar 5 new + 43 existing, Khyber 21 new + 9 existing
(26 new / 52 existing in total). Some slide spellings differ from the workbook
(SUR QAMAR/TD BAZAR/KHUGAKHEL/SHEIKHAMALKHEL/SULTANKHEL); ALIAS below maps them.
All 78 UCs are asserted to match exactly one workbook row.

fIPV targets in the workbook are fractional (94% of the under-10 OPV estimate).
They are allocated to whole children by largest remainder within each district so
that district and provincial totals match the workbook exactly.

Payload layout
  n/st/age/src/sc   title, planned start, age band, source filenames
  tot               {uc,new,exist,hh,fipv,sch}
  d                 [district, UCs, new, existing, HH target, fIPV target, school target]
  b                 [district index, border, UCs, HH target, fIPV target, school target]
  u                 [district index, border, isNew, UC, HH target, fIPV target, school target]
"""
import argparse
import html
import math
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'fipv'
DISTRICTS = ['Peshawar', 'Khyber']
BORDERS = ['Peshawar', 'Khyber', 'Afghanistan', 'Other UCs']
STRUCT = {'Peshawar', 'Khyber', 'Afghanistan', 'AFG-NANGARHAR', 'Districts', 'UCs',
          'Borders', 'Bordering with', 'Bordering With', 'New UCs Added', 'Existing Scope'}

# slide spellings that differ from the workbook
ALIAS = {
    'SUR QAMAR': 'SUR KAMAR',
    'TD BAZAR': 'TIDI BAZAR',
    'KHUGAKHEL': 'KHUGA KHEL',
    'SHEIKHAMALKHEL': 'SHEIKHMAL KHEL',
    'SULTANKHEL A': 'SULTAN KHEL A',
    'SULTANKHEL B': 'SULTAN KHEL B',
}


def norm(s):
    s = ALIAS.get(str(s).strip().upper(), str(s).strip().upper())
    return re.sub(r'[^A-Z0-9]', '', s)


def num(v):
    if v is None or str(v).strip() == '':
        raise SystemExit('ERR fipv empty numeric cell in %r' % (v,))
    return float(v)


def ppt_texts(path):
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n))
        out = []
        for n in names:
            x = z.read(n).decode('utf-8', 'replace')
            for para in re.findall(r'<a:p>(.*?)</a:p>', x, re.S):
                ts = re.findall(r'<a:t>(.*?)</a:t>', para, re.S)
                if ts:
                    t = html.unescape(''.join(ts)).strip()
                    if t:
                        out.append(t)
    if not out:
        raise SystemExit('ERR fipv no text found in %s' % path)
    return out


def read_ppt(path):
    texts = ppt_texts(path)
    try:
        start = texts.index('New UCs Added')
        end = texts.index('Existing Scope')
    except ValueError:
        raise SystemExit('ERR fipv scope slide markers missing (New UCs Added / Existing Scope)')
    region = texts[start:end]
    blocks, i = [], 0
    while i < len(region):
        m = re.fullmatch(r'Total UCs:\s*(\d+)', region[i])
        if not m:
            i += 1
            continue
        n = int(m.group(1))
        dist = region[i - 1] if i else ''
        names, j = [], i + 1
        while j < len(region) and not re.fullmatch(r'Total UCs:\s*\d+', region[j]):
            t = region[j]
            if t not in STRUCT and not t.startswith('Total UCs'):
                names.append(t)
            j += 1
        if len(names) != n:
            raise SystemExit('ERR fipv slide block %s says %d UCs but lists %d: %r'
                             % (dist, n, len(names), names))
        blocks.append((dist, n, names))
        i = j
    want = [('Peshawar', 5), ('Khyber', 21), ('Peshawar', 43), ('Khyber', 9)]
    if [(b[0], b[1]) for b in blocks] != want:
        raise SystemExit('ERR fipv slide blocks %r != %r' % ([(b[0], b[1]) for b in blocks], want))
    try:
        i = next(k for k, t in enumerate(texts) if t.lower() == 'under 5 target')
        j = next(k for k in range(i, len(texts)) if texts[k].strip().lower() == 'total')
    except StopIteration:
        raise SystemExit('ERR fipv scope slide total row not found')
    nums = []
    for t in texts[j + 1:]:
        s = t.replace(',', '').strip()
        if re.fullmatch(r'\d+', s):
            nums.append(int(s))
        if len(nums) == 4:
            break
    if nums != [78, 534888, 1184376, 245869]:
        raise SystemExit('ERR fipv slide totals %r != [78, 534888, 1184376, 245869]' % nums)
    return blocks, nums


def read_book(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb['Sheet1'] if 'Sheet1' in wb.sheetnames else wb[wb.sheetnames[0]]
    hdr = [str(ws.cell(1, c).value or '').strip() for c in range(1, 7)]
    if hdr[:2] != ['Districts', 'UCs'] or 'HH Target' not in hdr[2] or 'f-IPV' not in hdr[3]:
        raise SystemExit('ERR fipv unexpected workbook header %r' % hdr)
    fill = {}
    for rng in ws.merged_cells.ranges:
        v = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                fill[(r, c)] = v

    def cv(r, c):
        return fill.get((r, c), ws.cell(r, c).value)

    rows, total = [], None
    for r in range(2, ws.max_row + 1):
        a, u = cv(r, 1), cv(r, 2)
        if a and 'total' in str(a).strip().lower():
            total = [num(ws.cell(r, 3).value), num(ws.cell(r, 4).value), num(ws.cell(r, 5).value)]
            break
        if not a or not u:
            continue
        dist = str(a).strip()
        if dist not in DISTRICTS:
            raise SystemExit('ERR fipv unknown district %r in %s' % (dist, path))
        uc = str(u).strip()
        border = str(cv(r, 6) or 'Other UCs').strip()
        if border not in BORDERS:
            raise SystemExit('ERR fipv unknown border %r for %s / %s' % (border, dist, uc))
        rows.append({'d': dist, 'u': uc, 'b': border,
                     'hh': num(ws.cell(r, 3).value),
                     'fipv': num(ws.cell(r, 4).value),
                     'sch': num(ws.cell(r, 5).value)})
    wb.close()
    if total is None:
        raise SystemExit('ERR fipv total row not found in %s' % path)
    if len(rows) != 78:
        raise SystemExit('ERR fipv %d UC rows, expected 78' % len(rows))
    for d in DISTRICTS:
        if sum(1 for x in rows if x['d'] == d) != (48 if d == 'Peshawar' else 30):
            raise SystemExit('ERR fipv unexpected UC count for %s' % d)
    dup = sorted({(x['d'], x['u']) for x in rows if sum(1 for y in rows if (y['d'], y['u']) == (x['d'], x['u'])) > 1})
    if dup:
        raise SystemExit('ERR fipv duplicate UC rows %r' % dup)
    got = [sum(x['hh'] for x in rows), sum(x['fipv'] for x in rows), sum(x['sch'] for x in rows)]
    if [round(got[0]), round(got[1]), round(got[2])] != [round(total[0]), round(total[1]), round(total[2])]:
        raise SystemExit('ERR fipv workbook totals %r != total row %r' % (got, total))
    return rows, total


def allocate(vals, total):
    base = [int(math.floor(v + 1e-9)) for v in vals]
    need = int(total - sum(base))
    if not (0 <= need < len(vals)):
        raise SystemExit('ERR fipv rounding allocation needs %d seats for %d rows' % (need, len(vals)))
    order = sorted(range(len(vals)), key=lambda i: (-(vals[i] - base[i]), i))
    for i in order[:need]:
        base[i] += 1
    if sum(base) != total:
        raise SystemExit('ERR fipv rounding allocation %d != %d' % (sum(base), total))
    return base


def build(src_path, ppt_path, cfg):
    k = cfg['auto'][DS]['config']
    blocks, ppt_tot = read_ppt(ppt_path)
    rows, total = read_book(src_path)
    if ppt_tot[0] != len(rows) or round(total[0]) != ppt_tot[1] \
            or round(total[1]) != ppt_tot[2] or round(total[2]) != ppt_tot[3]:
        raise SystemExit('ERR fipv slide totals %r do not match workbook %r' % (ppt_tot, total))

    lookup = {(x['d'].upper(), norm(x['u'])): x for x in rows}
    if len(lookup) != len(rows):
        raise SystemExit('ERR fipv UC names collide after normalisation')
    new, exist = set(), set()
    for idx, (dist, n, names) in enumerate(blocks):
        status = 'new' if idx < 2 else 'exist'
        for nm in names:
            hit = lookup.get((dist.upper(), norm(nm)))
            if hit is None:
                raise SystemExit('ERR fipv slide UC %r not found in workbook district %s' % (nm, dist))
            key = (hit['d'], hit['u'])
            if key in new or key in exist:
                raise SystemExit('ERR fipv slide UC %r listed twice' % (nm,))
            (new if status == 'new' else exist).add(key)
    if len(new) != 26 or len(exist) != 52 or len(new | exist) != 78:
        raise SystemExit('ERR fipv new/existing split %d/%d does not cover 78 UCs'
                         % (len(new), len(exist)))
    for x in rows:
        x['new'] = 1 if (x['d'], x['u']) in new else 0

    d_order = sorted(DISTRICTS, key=lambda d: -sum(x['fipv'] for x in rows if x['d'] == d))
    dmap = {d: i for i, d in enumerate(d_order)}
    d = []
    for dist in d_order:
        R = [x for x in rows if x['d'] == dist]
        # allocate inside each border group so both group and district totals match
        for border in BORDERS:
            G = [x for x in R if x['b'] == border]
            if not G:
                continue
            target = int(round(sum(x['fipv'] for x in G)))
            for x, a in zip(G, allocate([x['fipv'] for x in G], target)):
                x['tg'] = a
        target = int(round(sum(x['fipv'] for x in R)))
        if sum(x['tg'] for x in R) != target:
            raise SystemExit('ERR fipv border allocation does not sum to district %s' % dist)
        d.append([dist.upper(), len(R), sum(x['new'] for x in R), len(R) - sum(x['new'] for x in R),
                  int(round(sum(x['hh'] for x in R))), target, int(round(sum(x['sch'] for x in R)))])
    if sum(x[5] for x in d) != round(total[1]):
        raise SystemExit('ERR fipv district fIPV totals %d != %d'
                         % (sum(x[5] for x in d), round(total[1])))

    b = []
    for dist in d_order:
        di = dmap[dist]
        for border in BORDERS:
            R = [x for x in rows if x['d'] == dist and x['b'] == border]
            if not R:
                continue
            b.append([di, border, len(R), int(round(sum(x['hh'] for x in R))),
                      sum(x['tg'] for x in R), int(round(sum(x['sch'] for x in R)))])

    u = []
    for dist in d_order:
        for x in sorted([x for x in rows if x['d'] == dist], key=lambda x: x['u']):
            u.append([dmap[dist], x['b'], x['new'], x['u'],
                      int(round(x['hh'])), x['tg'], int(round(x['sch']))])
    for i in range(len(d)):
        ur = [x for x in u if x[0] == i]
        if [sum(x[4] for x in ur), sum(x[5] for x in ur), sum(x[6] for x in ur)] != d[i][4:7]:
            raise SystemExit('ERR fipv UC rows do not sum to district %s' % d[i][0])

    p = {
        'n': k['name'], 'st': k['start'], 'age': k['age'],
        'src': os.path.basename(src_path), 'sc': os.path.basename(ppt_path),
        'tot': {'uc': len(rows), 'new': len(new), 'exist': len(exist),
                'hh': int(round(total[0])), 'fipv': int(round(total[1])),
                'sch': int(round(total[2]))},
        'd': d, 'b': b, 'u': u,
    }
    if len(new) + len(exist) != p['tot']['uc'] or sum(x[2] for x in d) != p['tot']['new']:
        raise SystemExit('ERR fipv new/existing counts inconsistent')
    summary = ('%d UCs (%s), fIPV target %s, HH %s, school %s, %d new / %d existing'
               % (p['tot']['uc'], ', '.join('%s %d' % (x[0].title(), x[1]) for x in d),
                  format(p['tot']['fipv'], ','), format(p['tot']['hh'], ','),
                  format(p['tot']['sch'], ','), p['tot']['new'], p['tot']['exist']))
    return p, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--ppt')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR fipv no fIPV scope workbook found under %s' % cfg['auto'][DS]['roots'])
    if a.ppt:
        ppt = srcutil.stat_rec(a.ppt)
    else:
        cf = cfg['auto'][DS]['config']
        ppt = srcutil.newest({'roots': cfg['auto'][DS]['roots'],
                              'patterns': [cf['scope_glob']], 'exclude': ['~$*']})
    if not ppt or not os.path.exists(ppt['path']):
        raise SystemExit('ERR fipv no fIPV scope slide found under %s' % cfg['auto'][DS]['roots'])
    payload, summary = build(rec['path'], ppt['path'], cfg)
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'fipv.json')
    srcutil.write_text(dest, js)
    print('SRC fipv %s' % rec['path'])
    print('SRC fipv slide %s' % ppt['path'])
    print('OK fipv %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
