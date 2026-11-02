"""Profile the three 10:43 coverage exports for SNID Nov 2026 (compact)."""
import io, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DL = Path(r'C:\Users\HD\Downloads')
FILES = [
    'coverage_SNID Nov 2026_2026-11-02_104311.xls',
    'coverage_SNID Nov 2026_2026-11-02_104319.xls',
    'coverage_SNID Nov 2026_2026-11-02_104330.xls',
]
for fn in FILES:
    p = DL / fn
    text = p.read_bytes().decode('utf-8', 'replace')
    df = max(pd.read_html(io.StringIO(text), header=0), key=len)
    print('=' * 100)
    print(fn, p.stat().st_size, df.shape)
    print('levels:', [c for c in ('Province', 'Division', 'District', 'Tehsil', 'UC') if c in df.columns])
    print('province vals:', df['Province'].dropna().unique()[:5].tolist())
    print('districts:', df['District'].nunique() if 'District' in df.columns else None,
          'ucs:', df['UC'].nunique() if 'UC' in df.columns else None)
    print('first cols:', list(df.columns)[:12])
    keep = [c for c in df.columns if c in ('Province', 'Division', 'District', 'Tehsil', 'UC',
            'Target Children in HH from MP (Planning)', 'Overall Target', 'Overall Children Vaccinated',
            'Overall Children Vaccinated (Campaign days)')]
    keep += [c for c in df.columns if str(c).startswith('Overall Children Vaccinated') and c not in keep][:2]
    print(df[keep].head(4).to_string(max_colwidth=30))
    print('tail:')
    print(df[keep].tail(2).to_string(max_colwidth=30))
