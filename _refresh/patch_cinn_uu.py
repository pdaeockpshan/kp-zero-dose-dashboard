# -*- coding: utf-8 -*-
"""Refresh the admin columns of CINN.uu (campaign-indicators UC plate, household basis).

Rows are keyed by absolute UC index into INDIC.ucs, whose 4th element is the portal UC code.
975 of 996 codes are on the live 11-Nov UC-wise table; the other 21 (Kurram) keep the 06-Nov read.

Usage: python _refresh/patch_cinn_uu.py [--write]
"""
import argparse
import json
import sys

import pandas as pd

sys.path.insert(0, 'C:/Users/HD/Documents/kp-zero-dose-dashboard/_refresh')
import dashpatch
import srcutil

SRC = 'C:/Users/HD/Downloads/summary_SNID Nov 2026_uc_live.xls'


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
    c = json.loads(dashpatch.get_payload(s, 'CINN').replace('<\\/', '</'))
    ind = json.loads(dashpatch.get_payload(s, 'INDIC').replace('<\\/', '</'))
    assert len(c['uu']) == 996
    assert all(len(v) == 17 for _, v in c['uu'])

    df = pd.read_html(SRC, header=[0, 1, 2, 3])[0]
    df = df[df.iloc[:, 5].astype(str).str.strip().str.match(r'^\d{8}$')]
    live = {str(r.iloc[5]).strip(): r for _, r in df.iterrows()}
    assert len(live) == 996

    upd, kept, drops = 0, [], 0
    for idx, vals in c['uu']:
        code = str(ind['ucs'][idx][3]).strip()
        if code not in live:
            kept.append(code)
            continue
        r = live[code]
        tg, vac = int(num(r.iloc[8])), int(num(r.iloc[15]))
        sna, srf, slo = int(num(r.iloc[119])), int(num(r.iloc[124])), int(num(r.iloc[127]))
        assert sna + srf + slo == int(num(r.iloc[126])), code
        assert vals[0] == tg, (code, vals[0], tg)
        if vac < vals[1]:
            drops += 1
        vals[0] = tg
        vals[1] = vac
        vals[2] = round(100.0 * vac / tg, 2) if tg else 0.0
        vals[3], vals[4], vals[5] = sna, srf, slo
        vals[6] = round(100.0 * (sna + srf + slo) / tg, 2) if tg else 0.0
        upd += 1
    assert upd == 975 and len(kept) == 21, (upd, kept)
    assert drops <= 15, drops

    c['src'] = ('EOC portal Summary report, SNID Nov 2026 - district grain read 11-Nov-2026 15:25 '
                '(live District-Wise table; the Export button returned province grain); UC rows for '
                '975 matched UCs read 11-Nov-2026 16:01 from the live UC-Wise table; 21 UCs absent '
                'from that table keep the 06-Nov-2026 20:47 row and still re-add to the district '
                'totals; ICM columns from the IDIMS form 11 '
                'cluster download 04-Nov-2026 20:14; LQAS not yet posted')
    print('updated', upd, 'kept', len(kept), kept[:6], 'decreases', drops)
    print('sum tg', sum(v[0] for _, v in c['uu']), 'sum vac', sum(v[1] for _, v in c['uu']))

    if a.write:
        v = dashpatch.Variant(path, 'index.html')
        dashpatch.swap_payload(v, 'CINN', srcutil.dumps(c))
        dashpatch.assert_crlf(v)
        srcutil.write_text(path, v.text)
        print('WROTE', v.changes)
    else:
        print('DRY RUN ok')


if __name__ == '__main__':
    main()
