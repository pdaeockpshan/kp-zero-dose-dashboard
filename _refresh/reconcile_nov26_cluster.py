"""Reconcile the UC-level Nov-26 cluster export with the published CQ.icm payload."""
import io, json, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')


def read_table(p, header=0):
    text = p.read_bytes().decode('utf-8', 'replace')
    tables = pd.read_html(io.StringIO(text), header=header)
    return max(tables, key=len)


def load_cq():
    s = open(ROOT / 'index.html', encoding='utf-8', newline='').read()
    i = s.find('const CQ = {')
    j = s.find('{', i)
    depth, k, instr, esc = 0, j, False, False
    while k < len(s):
        ch = s[k]
        if instr:
            if esc:
                esc = False
            elif ch == chr(92):
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
        k += 1
    return json.loads(s[j:k + 1])


def num(s):
    try:
        v = float(str(s).replace(',', ''))
        return int(v) if v == int(v) else v
    except Exception:
        return 0


def main():
    cq = load_cq()
    icm = cq['icm']['NOV-26-1']
    df = read_table(DL / 'icm_2026-11-02_10-33-10.xls')
    df = df[df['Campaign Name'] == 'SNID Nov 2026']
    df = df[df['District'].astype(str) != 'Total']
    print('rows', len(df), 'districts', sorted(df['District'].unique()))
    cols = list(df.columns)
    print(cols)
    ren = {
        cols[7]: 'cl', cols[8]: 'hh', cols[9]: 'door', cols[10]: 'nr', cols[11]: 'dw',
        cols[12]: 'rc', cols[13]: 'rcm', cols[14]: 'rcpct',
        cols[15]: 'mi', cols[16]: 'tdn', cols[17]: 'tm', cols[18]: 'na', cols[19]: 'rf',
        cols[20]: 'gr', cols[21]: 'gv', cols[22]: 'gvpct',
        cols[23]: 'seen', cols[24]: 'fm', cols[25]: 'fmpct', cols[26]: 'nvfm',
        cols[27]: 'epi05', cols[28]: 'lk', cols[29]: 'lk1', cols[30]: 'lk2',
        cols[31]: 'pca', cols[32]: 'ma',
    }
    d = df.rename(columns=ren)
    for c in list(ren.values()):
        d[c] = d[c].map(num)
    g = d.groupby('District', sort=True)[list(ren.values())].sum()
    print('tehsil/UC rows:', d['UC'].nunique())
    print()
    keys = ['cl', 'hh', 'door', 'nr', 'dw', 'rc', 'mi', 'tdn', 'tm', 'na', 'rf', 'gr', 'gv', 'seen', 'fm', 'nvfm', 'pca', 'ma']
    mism = []
    for dist in sorted(icm):
        if dist not in g.index:
            mism.append((dist, 'MISSING IN EXPORT'))
            continue
        row = g.loc[dist]
        pub = icm[dist]
        diffs = {k: (int(row[k]), pub.get(k)) for k in keys if int(row[k]) != pub.get(k)}
        if diffs:
            mism.append((dist, diffs))
    print('districts in published but not export:', sorted(set(icm) - set(g.index)))
    print('districts in export but not published:', sorted(set(g.index) - set(icm)))
    print('mismatched districts:', len(mism))
    for m in mism[:10]:
        print(m)
    if not mism:
        print('ALL 18 COUNTS MATCH PUBLISHED CQ.icm NOV-26-1 EXACTLY')


if __name__ == '__main__':
    main()
