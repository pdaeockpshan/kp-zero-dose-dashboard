"""Refresh NOCD SNID Nov 2026 from the 11-Nov-2026 NEOC monitoring exports.

Team / fixed / supervisor / transit district tables plus the province indicator strips read from
each export's own Total row. Nothing else in NOCD moves; other campaigns keep their values.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

DL = r'C:\Users\HD\Downloads'
ASOF = '2026-11-11'

TI = ['Female', 'Adult', 'Name matches ID', 'Marker quality', 'Training',
      'CC approved carrier', 'CC lid & seal', 'CC no water', 'Dry', 'Valid VVM',
      'Intact label', 'Vial properly recapped', 'Doses matched to children',
      'Tally sheet', 'Vitamin-A', 'Missed-children record', 'Route map location',
      'Proper workload', 'Asks newborn/NA/SC', 'Asks AFP & RI', 'Marker for FM only',
      'FM fully marked', 'Minimising wastage']
FI = ['Functional', 'Local', 'Adult', 'Trained', 'Govt accountable', 'Dry', 'Valid VVM',
      'Intact label', 'Vial recapped', 'Detail address', 'Doses matched to children',
      'Fixed site in EPI centre', 'Vitamin-A', 'Stock register updated',
      'Stock leftover', 'RI given']
SI = ['Checklist completed', 'Supervisor supported teams', 'IPC quality']
SX = ['Located as per MP', 'Accessible', 'Visible', 'Posters/banners', 'Team ID badges',
      'Adult', 'CC approved carrier', 'CC lid & seal', 'CC no water', 'CC lined with ice',
      'Each team vaccine carrier', 'Each team marker', 'Each team tally sheet', 'Dry',
      'Valid VVM', 'Intact label', 'Vial recapped', 'Doses matched to children',
      'Dose matches children', 'Security present', 'Security helping']


def rows(name):
    with open(os.path.join(DL, name), encoding='utf-8-sig', newline='') as fh:
        return list(csv.reader(fh))


def num(v):
    try:
        f = float(str(v).replace(',', ''))
    except ValueError:
        return 0
    return int(f) if abs(f - round(f)) < 1e-9 else round(f, 2)


def main(write=False):
    team = rows('icm_2026-11-11_team.csv')
    fixed = rows('icm_fixed_2026-11-11.csv')
    sup = rows('icm_supervisor_2026-11-11.csv')
    tran = rows('icm_transit_2026-11-11.csv')

    tv, tvn = {}, 0
    for r in team[1:]:
        if r[0] == 'Total':
            tvn = num(r[3]); continue
        tv[r[2]] = num(r[3])
    fx, fxn = {}, 0
    for r in fixed[1:]:
        if r[0] == 'Total':
            fxn = num(r[3]); continue
        fx[r[2]] = num(r[3])
    sp = {}
    sup_tot = None
    for r in sup[2:]:
        if r[0] == 'Total':
            sup_tot = r; continue
        sp[r[2]] = {'chk': num(r[10]), 'sup': num(r[11])}
    tr, trn = {}, 0
    for r in tran[1:]:
        if r[0] == 'Total':
            trn = num(r[3]); continue
        tr[r[2]] = num(r[3])

    assert tvn == sum(tv.values()), ('team total', tvn, sum(tv.values()))
    assert fxn == sum(fx.values()), ('fixed total', fxn, sum(fx.values()))
    assert trn == sum(tr.values()), ('transit total', trn, sum(tr.values()))
    assert len(tv) == 27 and len(fx) == 27 and len(sp) == 27 and len(tr) == 26, (len(tv), len(fx), len(sp), len(tr))

    ttot = [r for r in team if r[0] == 'Total'][0]
    ftot = [r for r in fixed if r[0] == 'Total'][0]
    tttot = [r for r in tran if r[0] == 'Total'][0]
    ti = [[TI[i], num(ttot[4 + i])] for i in range(len(TI))]
    fi = [[FI[i], num(ftot[4 + i])] for i in range(len(FI))]
    si = [[SI[0], num(sup_tot[10])], [SI[1], num(sup_tot[11])], [SI[2], num(sup_tot[12])]]
    # supervisor carrier items sit in columns 3..9 of the Total row
    sc = [['Carrying vaccine carrier', num(sup_tot[3])],
          ['Carrying OPV vials', num(sup_tot[4])],
          ['Carrying finger markers', num(sup_tot[5])],
          ['Cold chain maintained', num(sup_tot[6])],
          ['Microplan updated', num(sup_tot[7])],
          ['Carrying Vitamin-A', num(sup_tot[8])],
          ['Name and ID match', num(sup_tot[9])]]
    tx = [[SX[i], num(tttot[4 + i])] for i in range(len(SX))]

    cfg, vs = dashpatch.load_variants()
    v = vs[0]
    o = json.loads(dashpatch.get_payload(v.text, 'NOCD').replace('<\\/', '</'))
    o['asof'] = ASOF
    c = o['camps']['SNID Nov 2026']
    old = (sum(c['tv'].values()), sum(c['fx'].values()), sum(c['tr'].values()))
    c['tv'], c['fx'], c['tr'], c['sp'] = tv, fx, tr, sp
    c['ti'], c['fi'], c['si'], c['sc'], c['tx'] = ti, fi, si, sc, tx
    c['n'] = {'tv': tvn, 'fx': fxn, 'tr': trn}
    print('old tv/fx/tr', old, '->', (tvn, fxn, trn))
    print('team indicators red (<90):', [x for x in ti if x[1] < 90])
    print('fixed red (<90):', [x for x in fi if x[1] < 90])
    print('supervisor:', sc, si)
    print('transit red (<90):', [x for x in tx if x[1] < 90])
    payload = srcutil.dumps(o)
    if write:
        changed = dashpatch.swap_payload(v, 'NOCD', payload)
        dashpatch.assert_crlf(v)
        if changed:
            srcutil.write_text(v.path, v.text)
        print('WROTE' if changed else 'UNCHANGED', v.changes)
    else:
        print('dry run; payload chars', len(payload))


if __name__ == '__main__':
    main('--write' in sys.argv)
