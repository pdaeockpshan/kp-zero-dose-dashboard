# -*- coding: utf-8 -*-
"""Finalise NOVUC from the live UC-wise summary table (read 11-Nov-2026 16:01).

Only the admin columns move: overall target (unchanged), overall vaccinations, still missed
(NA / refusals / leftover). ICM columns keep the 04-Nov IDIMS read.

Usage: python _refresh/patch_novuc_final.py [--write]
"""
import argparse
import collections
import json
import sys

import pandas as pd

sys.path.insert(0, 'C:/Users/HD/Documents/kp-zero-dose-dashboard/_refresh')
import dashpatch
import srcutil

SRC = 'C:/Users/HD/Downloads/summary_SNID Nov 2026_uc_live.xls'
LIVE_READ = '11-Nov-2026 16:01'
EXP_TG = 4808167
EXP_VAC = 4696957
EXP_SNA = 72897
EXP_SRF = 21517
EXP_SLO = 68460


def num(v):
    try:
        return float(str(v).replace(',', ''))
    except ValueError:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()

    path = 'C:/Users/HD/Documents/kp-zero-dose-dashboard/index.html'
    s = srcutil.read_text(path)
    p = json.loads(dashpatch.get_payload(s, 'NOVUC').replace('<\\/', '</'))
    rows, K = p['r'], p['k']
    ix = {k: i for i, k in enumerate(K)}
    assert len(rows) == 996 and len(K) == 22

    df = pd.read_html(SRC, header=[0, 1, 2, 3])[0]
    df = df[df.iloc[:, 5].astype(str).str.strip().str.match(r'^\d{8}$')]
    live = {str(r.iloc[5]).strip(): r for _, r in df.iterrows()}
    assert len(live) == 996, len(live)

    codes = [str(r[ix['c']]).strip() for r in rows]
    assert len(set(codes)) == 996
    assert set(codes) == set(live), (len(set(codes) - set(live)), len(set(live) - set(codes)))

    drops = []
    for r in rows:
        L = live[str(r[ix['c']]).strip()]
        tg = int(num(L.iloc[16]))
        vac = int(num(L.iloc[17]))
        sna = int(num(L.iloc[119]))
        srf = int(num(L.iloc[124]))
        slo = int(num(L.iloc[127]))
        assert sna + srf + slo == int(num(L.iloc[126])), (r[ix['u']], sna, srf, slo)
        assert r[ix['tg']] == tg, (r[ix['u']], r[ix['tg']], tg)
        if vac < r[ix['vac']]:
            drops.append((r[ix['u']], r[ix['vac']], vac))
        r[ix['vac']], r[ix['sna']], r[ix['srf']], r[ix['slo']] = vac, sna, srf, slo

    assert len(drops) <= 15, drops
    sums = {k: int(sum(r[ix[k]] for r in rows)) for k in ('tg', 'vac', 'sna', 'srf', 'slo')}
    assert sums == {'tg': EXP_TG, 'vac': EXP_VAC, 'sna': EXP_SNA, 'srf': EXP_SRF,
                    'slo': EXP_SLO}, sums
    assert sums['sna'] + sums['srf'] + sums['slo'] == 162874

    p['asof'] = ('live portal UC-wise table read ' + LIVE_READ +
                 ' (campaign NOV-26-1); ICM columns from the 04-Nov-2026 20:14 IDIMS downloads')
    p['src'] = ('EOC portal Summary report, SNID Nov 2026, UC wise: household and overall targets, '
                'vaccinations, still missed (NA / refusals / leftover); live UC-Wise table read '
                + LIVE_READ + '; ICM columns from IDIMS forms 11, 24 and 10 downloaded 04-Nov-2026 20:14')

    by_d = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        d = by_d[r[ix['d']]]
        d[0] += r[ix['tg']]
        d[1] += r[ix['vac']]
        d[2] += r[ix['sna']] + r[ix['srf']] + r[ix['slo']]
    print('%-14s %9s %9s %6s %8s' % ('district', 'target', 'vacc', 'cov%', 'still'))
    for d in sorted(by_d):
        t, v, st = by_d[d]
        print('%-14s %9d %9d %6.2f %8d' % (d, t, v, 100.0 * v / t, st))
    print('SUM', sums, 'still total', 162874)
    print('decreases', len(drops), drops)

    if a.write:
        v = dashpatch.Variant(path, 'index.html')
        dashpatch.swap_payload(v, 'NOVUC', srcutil.dumps(p))
        dashpatch.assert_crlf(v)
        srcutil.write_text(path, v.text)
        print('WROTE', v.changes)
    else:
        print('DRY RUN ok')


if __name__ == '__main__':
    main()
