"""Map the 10:43 coverage export columns to the published CQ.adm fields."""
import io, json, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')


def raw(fn):
    text = (DL / fn).read_bytes().decode('utf-8', 'replace')
    return max(pd.read_html(io.StringIO(text), header=None), key=len)


def load_cq():
    s = open(ROOT / 'index.html', encoding='utf-8', newline='').read()
    i = s.find('const CQ = {'); j = s.find('{', i)
    d, k, instr, esc = 0, j, False, False
    while k < len(s):
        ch = s[k]
        if instr:
            if esc: esc = False
            elif ch == chr(92): esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == '{': d += 1
            elif ch == '}':
                d -= 1
                if d == 0: break
        k += 1
    return json.loads(s[j:k + 1])


cq = load_cq()
adm = cq['adm']['NOV-26-1']
dist = raw('coverage_SNID Nov 2026_2026-11-02_104319.xls')
print('district file shape', dist.shape)
print('header rows:')
for r in range(4):
    print(' ', r, [str(x) for x in dist.iloc[r].tolist()[:20]])
idx0 = dist.columns[0] if False else None
data = dist.reset_index(drop=True)
print('columns type:', type(dist.columns).__name__, 'first cols:', list(dist.columns)[:8])
data = dist[dist.iloc[:, 0].astype(str).str.strip() == 'KP']
print('KP rows', len(data), 'districts', data.iloc[:, 2].nunique())
print('districts:', sorted(data.iloc[:, 2].astype(str).unique()))
print('missing from published:', sorted(set(data.iloc[:, 2].astype(str)) - set(adm)))
print('published not in export:', sorted(set(adm) - set(data.iloc[:, 2].astype(str))))
row = data[data.iloc[:, 2].astype(str).str.upper() == 'DIKHAN'].iloc[0]
print('\nDIKHAN published:', adm['DIKHAN'])
for i, v in enumerate(row.tolist()):
    if str(v) not in ('nan', '0', '0.0', '-'):
        print(i, repr(v))
