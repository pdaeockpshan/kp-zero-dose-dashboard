"""Extract the UC-level AFP case register (const AFPUC) from the KP line list.

The four-sheet line list (2023 / 2024 / 2025 / 2026) is the only source that carries
UC, onset, age, sex, stool adequacy, notification / investigation dates, doses and
class per case. The published payload keeps no names, addresses, EPIDs or lab numbers:
one compact row per AFP case, keyed to a UC code.

Usage: python _refresh/extract_afpuc.py [--source PATH] [--out PATH]
Prints one status line: OK afpuc <json chars> <summary> | ERR afpuc <reason>
"""
import argparse
import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'afpuc'
SHEETS = ['2023 Line List', '2024 Line List', '2025 Line List', '2026 Line List']
NEED = ['DISTRICT', 'TEHSIL', 'UC', 'UCODE', 'DONSET', 'DNOT', 'DOI', 'AGE', 'SEX',
        'ADEQ', 'CLASS', 'DOSES', 'VDOSES', 'STCOND1', 'STCOND2',
        'Samples_Collected', 'DIAG', 'ERC']
# 2023 sheet (86 cols) predates the derived scheduling columns
OPT = ['Samples_Collected', 'DIAG', 'ERC']


def d(v):
    if v is None:
        return None
    try:
        if v != v:  # NaN / NaT
            return None
    except Exception:
        pass
    try:
        x = v.date() if hasattr(v, 'date') else v
    except Exception:
        return None
    try:
        if x != x:
            return None
    except Exception:
        pass
    return x if isinstance(x, datetime.date) else None


def n(v, blank=-1):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return blank
    if f != f:  # NaN
        return blank
    return int(round(f))


def s(v):
    if v is None:
        return ''
    t = str(v).strip()
    return '' if t.lower() == 'nan' else t


def lvl(v, hi):
    """1 when 0 < v <= hi, 0 when v > hi, -1 when unknown."""
    return -1 if v is None else (1 if v <= hi else 0)


def build(path):
    import pandas as pd
    xl = pd.ExcelFile(path)
    missing = [s_ for s_ in SHEETS if s_ not in xl.sheet_names]
    if missing:
        raise SystemExit('ERR afpuc %s is missing sheet(s) %s - not the four-year line list'
                         % (os.path.basename(path), missing))
    ucs, uidx, rows, last = [], {}, [], None
    npx, npidx = [], {}
    for sh in SHEETS:
        df = pd.read_excel(path, sheet_name=sh)
        miss = [c for c in NEED if c not in df.columns and c not in OPT]
        if miss:
            raise SystemExit('ERR afpuc sheet %r is missing columns %s' % (sh, miss))
        has_smp = 'Samples_Collected' in df.columns
        for _, r in df.iterrows():
            on = d(r['DONSET'])
            if not on:
                continue
            code = s(r['UCODE'])
            cls = n(r['CLASS'], 0)
            if not code or code.lower() == 'nan':
                # registered in the district but no UC recorded: keep the count, not a fake UC
                key = (s(r['DISTRICT']).upper(), on.year)
                if key not in npidx:
                    npidx[key] = len(npx)
                    npx.append([key[0], key[1], 0, 0])
                npx[npidx[key]][2] += 1
                if cls not in (1, 2, 3):
                    npx[npidx[key]][3] += 1
                if last is None or on > last:
                    last = on
                continue
            try:
                code = str(int(float(code)))
            except ValueError:
                code = code.split('.')[0]
            k = code
            if k not in uidx:
                uidx[k] = len(ucs)
                ucs.append([code, s(r['UC']).upper(), s(r['TEHSIL']).upper(), s(r['DISTRICT']).upper()])
            dnot, doi = d(r['DNOT']), d(r['DOI'])
            sx = s(r['SEX']).upper()
            adq = s(r['ADEQ']).upper()
            st = 1 if n(r['STCOND1'], 0) and n(r['STCOND2'], 0) else 0
            smp = n(r['Samples_Collected'], st + st) if has_smp else st + st
            vd = n(r['VDOSES'], -1)
            dz = max(n(r['DOSES'], 0), 0)
            rows.append([
                on.year, on.month, uidx[k], n(r['AGE'], 0),
                1 if sx.startswith('M') else 0,
                1 if adq.startswith('A') else 0,
                cls if cls in (1, 2, 3) else 0,
                dz,
                vd if 0 <= vd < 90 else dz,
                lvl((dnot - on).days if dnot else None, 7),
                lvl((doi - on).days if doi else None, 2),
                smp,
                1 if s(r['DIAG']) else 0,
                1 if d(r['ERC']) else 0,
            ])
            if last is None or on > last:
                last = on
    if not rows:
        raise SystemExit('ERR afpuc no KP AFP rows with a UC code and an onset date')
    out = {'src': os.path.basename(path), 'asof': last.isoformat(), 'n': len(rows),
           'ucs': ucs, 'r': rows, 'np': npx}
    return out, '%d cases (%d UCs, %d district-only), onset %s-%s' % (
        len(rows), len(ucs), sum(x[2] for x in npx), rows[0][0], last.isoformat())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    path = a.source
    if not path:
        path = srcutil.newest(cfg['auto'][DS])['path']
    print('SRC afpuc %s' % path)
    out, summary = build(path)
    data = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, DS + '.json')
    srcutil.write_text(dest, data)
    print('OUT %s' % dest)
    print('OK afpuc %d %s' % (len(data), summary))


if __name__ == '__main__':
    main()
