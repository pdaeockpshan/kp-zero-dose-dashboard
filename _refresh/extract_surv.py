"""Extract the AFP surveillance payload (const SURVW) for the dashboard surveillance tab.

Usage: python _refresh/extract_surv.py [--source WEEKLY_XLSX] [--ll LINELIST_XLSX] [--out PATH]
Prints: SRC lines + one status line `OK surv <json chars> <summary>` | ERR surv <reason>

Sources (both in Downloads, newest of each is used):
  * `Surv. Weekly Updates Log*.xlsx` - provincial surveillance weekly log:
      - `Summary`  : year-to-date indicators per district (NP-AFP rate, stool adequacy,
                     notification <7d, investigation <48h, EV/SL isolation, True AFP, GBS,
                     weekly active-surveillance visits, zero-report timeliness) + Grand Total.
      - `Indicators ` (trailing space): the same indicators as yearly histories 2013-2026 per
                     district, plus roll-up rows for the 7 divisions and KP (Grand Total).
                     District rows sit above the Grand Total, division rows below it - the
                     BANNU/KOHAT/PESHAWAR/MARDAN/MALAKAND names collide, so the row order
                     decides which one a row is.
      - `PointinTimeCaseDetection..`: AFP cases per district per month, 2019-2026.
      - `District Wise Pendency`: weekly pendency snapshots; the newest block is extracted
                     (currently Investigation complete / FUP inadequate / ERC).
  * `LineList-2023-2024-2025-2026.xlsx` - AFP line list sheets `2023 Line List`..`2026 Line List`.
      Only aggregates are extracted (case counts, OPV dose buckets, stool adequacy,
      notification/investigation timeliness, classification). Names, addresses and other
      EPID-level detail stay out of the payload - the dashboard is a public GitHub Pages site.

All reads use explicit min_col=1 because this workbook misdeclares its dimensions (openpyxl
otherwise shifts every column by one). District names are normalised to the dashboard's own
`const SURV` keys, which this script reads from index.html so naming stays in one place.

Payload: {"asof":..,"src":..,"llsrc":..,"llasof":..,"lastepid":..,"yrs":[2023..2026],
          "sm":{"k":..,"lab":..,"d":{district:[10]},"kp":[10]},
          "ind":{"g":[..],"lab":[..],"r":{district|KP|division:{"y":{g:[years]},"v":{g:[vals]}}}},
          "mon":{"y":[2019..2026],"d":{district|KP:[[12 months] per year]}},
          "pen":{"at":..,"k":[..],"d":{district:[..]}},
          "ll":{"d":{district:{n,zd,d1,d2,d3,du,ad,n7,i48,c3,cp,cw: [4 yearly arrays]}}}}
"""
import argparse
import datetime
import fnmatch
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'surv'
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
DIVISIONS = ['BANNU', 'DIKHAN', 'KOHAT', 'PESHAWAR', 'MARDAN', 'MALAKAND', 'HAZARA']
SM_K = ['np', 'sa', 'n7', 'i48', 'ev', 'sl', 'ta', 'gbs', 'as', 'zr']
SM_LAB = ['NP-AFP rate', 'Stool adequacy %', 'Notified <7 days %', 'Investigated <48 h %',
          'EV isolation %', 'SL isolation %', 'True AFP rate', 'GBS rate',
          'Weekly AS visits %', 'Zero-report timeliness %']
IND_G = ['sa', 'n7', 'i48', 'np', 'ta', 'gbs', 'ev', 'sl', 'rw', 'evsl']
IND_MAP = {'STOOLADEQUACY': 'sa', 'NOTIFYWITHIN7DAYS': 'n7', 'INVESTIGATEDWITHIN48HRS': 'i48',
           'NPAFPRATE': 'np', 'TRUEAFPRATE': 'ta', 'GBSRATE': 'gbs', 'EVISOLATION': 'ev',
           'SLISOLATION': 'sl', 'NONPOLIOAFPWITHRESIDUALWEAKNESS': 'rw', 'EVSL': 'evsl'}
SM_MAP = {'NPAFPRATE': 'np', 'STOOLADEQUACY': 'sa', 'NOTIFICATIONWITHIN7D': 'n7',
          'INVTWITHIN48HRS': 'i48', 'EVRATE': 'ev', 'SLRATE': 'sl', 'TRUEAFP': 'ta',
          'GBS': 'gbs', 'WEEKLYASVISITS': 'as', 'ZEROREPORTTIMELINESS': 'zr'}
LL_KEYS = ['n', 'zd', 'd1', 'd2', 'd3', 'du', 'ad', 'n7', 'i48', 'c3', 'cp', 'cw']
LL_NEED = ['DISTRICT', 'PROVINCE', 'DOSES', 'ADEQ', 'CLASS', 'EPID', 'DONSET']


def nk(s):
    return re.sub(r'[^A-Z0-9]', '', str(s or '').upper())


def num(v):
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    try:
        t = str(v or '').strip().replace('%', '')
        return round(float(t), 4) if t else None
    except ValueError:
        return None


def rows_of(wb, sheet, pad=40):
    if sheet not in wb.sheetnames:
        raise SystemExit('ERR surv sheet %r missing (has %s)' % (sheet, wb.sheetnames))
    ws = wb[sheet]
    return list(ws.iter_rows(min_row=1, min_col=1, max_row=ws.max_row,
                             max_col=(ws.max_column or 1) + pad, values_only=True))


def make_dkey(repo):
    """district spelling -> exact `const SURV` key, read from index.html so naming stays put."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SURV = ')
    if i < 0:
        raise SystemExit('ERR surv const SURV not found in index.html')
    j = s.find('\n', i)
    dists = list(json.loads(s[i + len('const SURV = '):j].rstrip().rstrip(';')).keys())
    rev = {nk(d): d for d in dists}
    rev.update({'WAZIRSL': 'WAZIR-S Lower', 'WAZIRSU': 'WAZIR-S Upper',
                'LAKKIMARWAT': 'LAKKIMRWT', 'KOLAIPALACE': 'KOLAIPALAS'})
    return dists, (lambda s: rev.get(nk(s)))


def newest_like(entry, pat):
    """Newest file under the entry's roots matching one extra pattern (for the line list)."""
    best = None
    for root in entry.get('roots') or []:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for fn in filenames:
                if not fnmatch.fnmatch(fn, pat) or any(fnmatch.fnmatch(fn, e) for e in entry.get('exclude') or []):
                    continue
                p = os.path.join(dirpath, fn)
                m = os.stat(p).st_mtime
                if best is None or m > best[0]:
                    best = (m, p)
    return best[1] if best else None


# ------------------------------------------------------------- weekly log

def parse_summary(wb, dists, dkey):
    rows = rows_of(wb, 'Summary')
    cols = {}
    for j, c in enumerate(rows[1]):
        k = nk(c)
        if not k:
            continue
        for want, key in SM_MAP.items():
            if k.startswith(want) or want.startswith(k):
                cols[key] = j
    lack = [k for k in SM_K if k not in cols]
    if lack:
        raise SystemExit('ERR surv Summary header misses %s' % lack)
    sm, kp = {}, None
    for r in rows[2:]:
        if not nk(r[1]):
            continue
        vals = [num(r[cols[k]]) for k in SM_K]
        if nk(r[1]) == 'GRANDTOTAL':
            kp = vals
            break
        d = dkey(r[1])
        if d:
            sm[d] = vals
    if kp is None or len(sm) != len(dists):
        raise SystemExit('ERR surv Summary: %d districts read (want %d), Grand Total %s'
                         % (len(sm), len(dists), 'ok' if kp else 'missing'))
    return {'k': SM_K, 'lab': SM_LAB, 'd': sm, 'kp': kp}


def parse_indicators(wb, dists, dkey):
    rows = rows_of(wb, 'Indicators ')
    r1, r3 = rows[0], rows[2]
    spans = []
    for j in range(2, len(r1)):
        g = IND_MAP.get(nk(r1[j]))
        if g:
            spans.append([j, g])
    for a, b in zip(spans, spans[1:]):
        a.append(b[0] - 1)
    spans[-1].append(len(r3) - 1)
    got = [g for _, g, _ in spans]
    lack = [g for g in IND_G if g not in got]
    if lack:
        raise SystemExit('ERR surv Indicators groups missing %s (got %s)' % (lack, got))
    out, seen_gt = {}, False
    for r in rows[3:]:
        lab = nk(r[1])
        if not lab:
            continue
        if lab == 'GRANDTOTAL':
            seen_gt = True
            out['KP'] = ind_row(r, spans, r3)
            continue
        if not seen_gt:
            d = dkey(r[1])
            if d:
                out[d] = ind_row(r, spans, r3)
        elif lab == 'KP':
            continue  # division roll-up repeat of the Grand Total row
        elif lab in DIVISIONS:
            out['DIV:' + lab] = ind_row(r, spans, r3)  # DIV: prefix - 6 names collide with districts
    want = len(dists) + 1 + len(DIVISIONS)
    if len(out) != want:
        raise SystemExit('ERR surv Indicators: %d rows read (want %d: districts+KP+divisions)'
                         % (len(out), want))
    return out


def ind_row(r, spans, r3):
    y, v = {}, {}
    for start, g, end in spans:
        ys, vals = [], []
        for j in range(start, end + 1):
            yr = r3[j]
            if isinstance(yr, str) and not yr.strip().isdigit():
                continue
            try:
                yr = int(yr)
            except (TypeError, ValueError):
                continue
            if yr in ys:            # duplicated year column - rightmost wins
                vals[ys.index(yr)] = num(r[j])
                continue
            ys.append(yr)
            vals.append(num(r[j]))
        y[g], v[g] = ys, vals
    return {'y': y, 'v': v}


def parse_monthly(wb, dists, dkey):
    rows = rows_of(wb, 'PointinTimeCaseDetection..')
    r2, r3 = rows[1], rows[2]
    blocks, cur, years = [], None, []
    for j in range(2, len(r3)):
        m = nk(r3[j])
        if m == 'JAN':
            cur = {'m': [], 'c': []}
            blocks.append(cur)
        if cur and m in MONTHS:
            cur['m'].append(m)
            cur['c'].append(j)
    for t in r2[2:]:
        m = re.match(r'\s*(\d{4})', str(t or ''))
        if m:
            years.append(int(m.group(1)))
    if not blocks or len(blocks) != len(years):
        raise SystemExit('ERR surv monthly: %d year blocks vs %d year labels' % (len(blocks), len(years)))
    mon = {'y': years, 'd': {}}
    for r in rows[3:]:
        if not nk(r[1]):
            continue
        key = 'KP' if nk(r[1]) == 'GRANDTOTAL' else dkey(r[1])
        if key is None:
            continue
        mon['d'][key] = [[int(v) if v is not None else None for v in (r[j] for j in b['c'])] for b in blocks]
    lack = [d for d in dists if d not in mon['d']]
    if lack or 'KP' not in mon['d']:
        raise SystemExit('ERR surv monthly missing %s%s' % (lack[:5], '' if 'KP' in mon['d'] else ' +KP'))
    return mon


def parse_pendency(wb, dists, dkey):
    rows = rows_of(wb, 'District Wise Pendency')
    last = None
    for j, c in enumerate(rows[0]):
        if str(c or '').strip().lower().startswith('pendency at'):
            last = j
    if last is None:
        raise SystemExit('ERR surv pendency: no "Pendency at" column found')
    subs = [str(c or '').strip() for c in rows[2][last:] if str(c or '').strip()]
    at = (re.search(r'Pendency at (\d{2}-\w{3}-\d{4})', str(rows[0][last])) or [None, ''])[1]
    d = {}
    for r in rows[3:]:
        if not nk(r[0]) or nk(r[0]) == 'GRANDTOTAL':
            continue
        key = dkey(r[0])
        if key:
            d[key] = [num(r[last + i]) for i in range(len(subs))]
    lack = [x for x in dists if x not in d]
    if lack:
        raise SystemExit('ERR surv pendency missing %s' % lack)
    return {'at': at, 'k': subs, 'd': d}


# ------------------------------------------------------------- line list

def parse_linelist(path, dkey, dists, years):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    agg = {d: {k: [0] * len(years) for k in LL_KEYS} for d in dists}
    llasof, lastepid, skip = None, '', 0
    for yi, yr in enumerate(years):
        sheet = '%d Line List' % yr
        if sheet not in wb.sheetnames:
            raise SystemExit('ERR surv line list sheet %r missing (has %s)' % (sheet, wb.sheetnames))
        rows = rows_of(wb, sheet)
        h = {}
        for j, c in enumerate(rows[0]):
            k = nk(c)
            if k and k not in h:
                h[k] = j
        lack = [k for k in LL_NEED if k not in h]
        if lack:
            raise SystemExit('ERR surv %s header misses %s' % (sheet, lack))
        has_n7, has_i48 = 'NOTI7DAYS' in h, 'INVES48HRS' in h
        for r in rows[1:]:
            if nk(r[h['PROVINCE']]) != 'KP':
                skip += 1
                continue
            d = dkey(r[h['DISTRICT']])
            if not d:
                raise SystemExit('ERR surv %s: unknown district %r' % (sheet, r[h['DISTRICT']]))
            a = agg[d]
            a['n'][yi] += 1
            do = r[h['DOSES']]
            t = str(do).strip() if do is not None else ''
            try:
                doses = int(float(t)) if t else None
            except ValueError:
                doses = None
            if doses is None:
                a['du'][yi] += 1
            elif doses == 0:
                a['zd'][yi] += 1
            elif doses == 1:
                a['d1'][yi] += 1
            elif doses == 2:
                a['d2'][yi] += 1
            else:
                a['d3'][yi] += 1
            if nk(r[h['ADEQ']]) == 'ADEQ':
                a['ad'][yi] += 1
            onset = r[h['DONSET']]
            if has_n7:
                if str(r[h['NOTI7DAYS']]).strip() == '1':
                    a['n7'][yi] += 1
            elif isinstance(onset, datetime.datetime) and isinstance(r[h['DNOT']], datetime.datetime):
                if 0 <= (r[h['DNOT']] - onset).days <= 7:
                    a['n7'][yi] += 1
            if has_i48:
                if str(r[h['INVES48HRS']]).strip() == '1':
                    a['i48'][yi] += 1
            elif isinstance(onset, datetime.datetime) and isinstance(r[h['DOI']], datetime.datetime):
                if 0 <= (r[h['DOI']] - onset).days <= 2:
                    a['i48'][yi] += 1
            cls = str(r[h['CLASS']] or '').strip()
            if cls == '3':
                a['c3'][yi] += 1
            elif cls in ('1', '2'):
                a['cw'][yi] += 1
            else:
                a['cp'][yi] += 1
            if isinstance(onset, datetime.datetime) and (llasof is None or onset > llasof):
                llasof = onset
                lastepid = str(r[h['EPID']] or '')
    wb.close()
    empty = [d for d in dists if sum(agg[d]['n']) == 0]
    if empty:
        raise SystemExit('ERR surv line list has no cases for %s' % empty)
    return agg, llasof, lastepid, skip


# ------------------------------------------------------------- main

def build(weekly, ll, cfg, repo):
    import openpyxl
    dists, dkey = make_dkey(repo)
    wb = openpyxl.load_workbook(weekly, read_only=True, data_only=True)
    sm = parse_summary(wb, dists, dkey)
    ind = parse_indicators(wb, dists, dkey)
    mon = parse_monthly(wb, dists, dkey)
    pen = parse_pendency(wb, dists, dkey)
    wb.close()

    # cross-check: the Indicators sheet's newest year must agree with the Summary YTD figures
    for g in ('sa', 'n7', 'i48', 'np', 'ev', 'sl'):
        ys, vs = ind['KP']['y'][g], ind['KP']['v'][g]
        a, b = vs[ys.index(max(ys))], sm['kp'][SM_K.index(g)]
        if a is None or b is None or abs(a - b) > 1.0:
            raise SystemExit('ERR surv Indicators %s newest year %s vs Summary %s diverge (%s vs %s)'
                             % (g, max(ys), g, a, b))

    yrs = [2023, 2024, 2025, 2026]
    agg, llasof, lastepid, skip = parse_linelist(ll, dkey, dists, yrs)
    for d in dists:
        n = agg[d]['n']
        for yi in range(len(yrs)):
            if sum(agg[d][k][yi] for k in ('zd', 'd1', 'd2', 'd3', 'du')) != n[yi]:
                raise SystemExit('ERR surv %s %d dose buckets != cases' % (d, yrs[yi]))

    asof = (re.search(r'(\d{2}-\w{3}-\d{4})', os.path.basename(weekly)) or [None, ''])[1]
    survw = {'asof': asof, 'src': os.path.basename(weekly),
             'llsrc': os.path.basename(ll),
             'llasof': llasof.date().isoformat() if llasof else '',
             'lastepid': lastepid, 'yrs': yrs,
             'sm': sm,
             'ind': {'g': IND_G, 'lab': [SM_LAB[SM_K.index(g)] if g in SM_K else
                                        ('Residual weakness #' if g == 'rw' else 'EV + SL %') for g in IND_G], 'r': ind},
             'mon': mon, 'pen': pen, 'll': {'d': agg}}
    yi = max(range(len(mon['y'])), default=0)
    mon26 = [v for v in (mon['d']['KP'][yi] or []) if v is not None]
    mix = ', '.join('%d:%d' % (y, sum(agg[d]['n'][i] for d in dists)) for i, y in enumerate(yrs))
    if sum(mon26) < 1000:
        raise SystemExit('ERR surv monthly KP %d months look empty (%s)' % (mon['y'][yi], mon26))
    summary = ('%d districts, YTD %s (NP-AFP %.1f, SA %.1f%%, Notif7d %.1f%%), %d division rows, '
               'monthly %d-%d, pendency %s, line list cases %s, last EPID %s, %d non-KP rows skipped'
               % (len(dists), survw['asof'], sm['kp'][0], sm['kp'][1], sm['kp'][2],
                  sum(1 for k in ind if k in DIVISIONS), min(mon['y']), max(mon['y']),
                  pen['at'] or '?', mix, lastepid, skip))
    return survw, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', help='weekly updates log (default: newest match)')
    ap.add_argument('--ll', help='line list workbook (default: newest LineList-*)')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    weekly = a.source or (srcutil.newest(entry) or {}).get('path')
    if not weekly or not os.path.exists(weekly):
        raise SystemExit('ERR surv no weekly updates log found under %s' % entry['roots'])
    ll = a.ll or newest_like(entry, 'LineList-*.xlsx')
    if not ll or not os.path.exists(ll):
        raise SystemExit('ERR surv no LineList-*.xlsx found under %s' % entry['roots'])
    print('SRC surv weekly %s' % weekly)
    print('SRC surv linelist %s' % ll)
    survw, summary = build(weekly, ll, cfg, cfg['repo'])
    js = srcutil.dumps(survw)
    dest = a.out or os.path.join(srcutil.OUT, 'survw.json')
    srcutil.write_text(dest, js)
    print('OK surv %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
