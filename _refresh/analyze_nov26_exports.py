"""Profile the 02-Nov-2026 ICM exports against the published NOV-26-1 payload."""
import io, json, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')

FILES = {
    'cluster': DL / 'icm_2026-11-02_10-33-10.xls',
    'team_new': DL / 'icm_2026-11-02_10-35-45.xls',
    'team_old': DL / 'icm_2026-11-02_10-35-24.xls',
    'fixed': DL / 'icm_fixed_2026-11-02_10-36-02.xls',
    'supervisor': DL / 'icm_supervisor_2026-11-02_10-37-14.xls',
    'transit': DL / 'icm_transit_2026-11-02_10-37-29.xls',
}


def read_html_xls(p, header=0):
    raw = p.read_bytes()
    text = raw.decode('utf-8', 'replace')
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


def main():
    cq = load_cq()
    adm = cq['adm']['NOV-26-1']
    icm = cq['icm']['NOV-26-1']

    for key, p in FILES.items():
        df = read_html_xls(p)
        camp_vals = sorted({str(v) for v in df.iloc[:, 0].dropna().unique()}) if df.shape[1] else []
        print('=' * 100)
        print(key, p.name, df.shape, 'campaigns:', camp_vals[:5])
        print('cols:', list(df.columns)[:40])
        if 'District' in df.columns:
            print('districts:', df['District'].nunique())
    print()
    print('published adm districts', len(adm), 'icm districts', len(icm))
    for d in ['DIKHAN', 'PESHAWAR', 'SWAT', 'MARDAN']:
        print(d, 'ADM', adm.get(d))
        print(d, 'ICM', json.dumps(icm.get(d))[:400])


if __name__ == '__main__':
    main()
