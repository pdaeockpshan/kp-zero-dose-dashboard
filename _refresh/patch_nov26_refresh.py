"""Refresh SNID Nov 2026 day-1 campaign payloads from the 02-Nov-2026 Downloads exports.

Replaces four embedded blocks in the master only:

- CQ.adm / CQ.icm / CQ.meta for NOV-26-1 — the 10:43 coverage summary, the 10:33
  ICM cluster export (counts, UCs reported, operational-issue %) and the new read
  time. The 10 supervisor checklist percentages are kept: the UC-level supervisor
  export cannot reproduce the portal's district figures.
- NOCD.camps['SNID Nov 2026'] — adds team visits and transit visits; the portal's
  27-district supervisor checklist block stays. No fixed-site block: the only
  fixed-site export downloaded is labelled SNID May 2026.
- ICMQ.camps['SNID Nov 2026'] — team-monitored (weighted by teams) and AIC-visited
  (unweighted UC mean) tables, with vitamin-A's AIC column flagged not asked.

Every other campaign is asserted byte-identical after the swap.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'nov26_refresh_2026-11-02.json')
CAMP = 'NOV-26-1'
LABEL = 'SNID Nov 2026'
ASOF = '2026-11-02'
DATE = '02-Nov-2026'

META_SRC = {
    'admin': 'EOC portal /whoapi/summaryreportedcoverage?compaignid=NOV-26-1 (Campaign Coverage, district wise), export 02-Nov-2026 10:43',
    'icm': 'EOC portal /icm/who_api_ICM - Intra Campaign Monitoring (Cluster), district wise, export 02-Nov-2026 10:33',
    'sv': 'EOC portal /icm/supervisormonitoring - ICM Supervisor Monitoring, district wise',
    'op': 'Computed from the ICM cluster export: (team did not visit + team missed the child) / missed children',
    'nm': 'EOC portal ICM team-monitoring (UC wise, 10:35), supervisor (10:37) and transit (10:37) exports',
}

CAP_OLD = 'ICM \u203a Intra Campaign Monitoring (Cluster) and the operational-issue report, district wise'
CAP_NEW = ('ICM \u203a Intra Campaign Monitoring (Cluster), district wise \u2014 the operational-issue % is '
           '(team did not visit + team missed the child) over missed children')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    raw = json.load(open(DATA, encoding='utf-8'))

    adm = {d: dict(zip(raw['admKeys'], vals)) for d, vals in raw['adm'].items()}
    icm = {}
    for d, vals in raw['icm'].items():
        row = dict(zip(raw['icmKeys'], vals))
        row['op'] = raw['op'][d]
        row['sv'] = raw['sv'][d]
        icm[d] = row
    if not (len(adm) == len(icm) == 27):
        raise SystemExit('district counts: adm %d icm %d' % (len(adm), len(icm)))

    # --- CQ ------------------------------------------------------------
    cq = json.loads(dashpatch.get_payload(v.text, 'CQ'))
    old_icm = cq['icm'][CAMP]
    for d, row in old_icm.items():
        if row.get('op') is not None:
            calc = round((row['tdn'] + row['tm']) * 100 / row['mi'], 2) if row['mi'] else None
            if calc is None or abs(calc - row['op']) > 0.005:
                raise SystemExit('%s: op formula no longer reproduces the portal value (%s vs %s)'
                                 % (d, calc, row['op']))
    others = {k: json.dumps(val, sort_keys=True) for k, val in cq['icm'].items() if k != CAMP}
    othadm = {k: json.dumps(val, sort_keys=True) for k, val in cq['adm'].items() if k != CAMP}
    othmeta = {k: json.dumps(val, sort_keys=True) for k, val in cq['meta'].items() if k != CAMP}

    cq['adm'][CAMP] = adm
    cq['icm'][CAMP] = icm
    m = cq['meta'][CAMP]
    m['day'] = 1
    m['asof'] = DATE
    m['read'] = ASOF
    m['src'] = dict(META_SRC)

    cq_json = srcutil.dumps(cq)
    re_cq = json.loads(cq_json.replace('<\\/', '</'))
    assert {k: json.dumps(val, sort_keys=True) for k, val in re_cq['icm'].items() if k != CAMP} == others
    assert {k: json.dumps(val, sort_keys=True) for k, val in re_cq['adm'].items() if k != CAMP} == othadm
    assert {k: json.dumps(val, sort_keys=True) for k, val in re_cq['meta'].items() if k != CAMP} == othmeta
    assert re_cq['camps'] == cq['camps'] and re_cq['pre'] == cq['pre']
    assert len(re_cq['icm'][CAMP]) == 27 and len(re_cq['adm'][CAMP]) == 27
    dashpatch.swap_payload(v, 'CQ', cq_json)

    # --- NOCD ----------------------------------------------------------
    nocd = json.loads(dashpatch.get_payload(v.text, 'NOCD'))
    n_old = {k: json.dumps(val, sort_keys=True) for k, val in nocd['camps'].items() if k != LABEL}
    sp = (nocd['camps'].get(LABEL) or {}).get('sp') or {}
    if len(sp) != 27:
        raise SystemExit('published supervisor checklist block has %d districts' % len(sp))
    nocd['camps'][LABEL] = {'tv': raw['tv'], 'sp': sp, 'tr': raw['tr']}
    nocd['asof'] = ASOF
    nocd_json = srcutil.dumps(nocd)
    re_n = json.loads(nocd_json.replace('<\\/', '</'))
    assert {k: json.dumps(val, sort_keys=True) for k, val in re_n['camps'].items() if k != LABEL} == n_old
    assert len(re_n['camps'][LABEL]['tv']) == 27 and len(re_n['camps'][LABEL]['tr']) == 24
    dashpatch.swap_payload(v, 'NOCD', nocd_json)

    # --- ICMQ ----------------------------------------------------------
    icmq = json.loads(dashpatch.get_payload(v.text, 'ICMQ'))
    q_old = {k: json.dumps(val, sort_keys=True) for k, val in icmq['camps'].items() if k != LABEL}
    camps = {LABEL: raw['icmq']}
    camps.update({k: val for k, val in icmq['camps'].items() if k != LABEL})
    icmq['camps'] = camps
    icmq['asof'] = ASOF
    icmq_json = srcutil.dumps(icmq)
    re_q = json.loads(icmq_json.replace('<\\/', '</'))
    assert {k: json.dumps(val, sort_keys=True) for k, val in re_q['camps'].items() if k != LABEL} == q_old
    assert list(re_q['camps'])[0] == LABEL
    assert len(re_q['camps'][LABEL]['tm']) == 27 and len(re_q['camps'][LABEL]['aic']) == 27
    assert len(re_q['tmK']) == 27 and len(re_q['aicK']) == 18
    dashpatch.swap_payload(v, 'ICMQ', icmq_json)

    # --- caption: the operational-issue % is derived from the cluster counts
    if v.text.count(CAP_OLD) != 1:
        raise SystemExit('operational-issue caption anchor found %d times' % v.text.count(CAP_OLD))
    v.text = v.text.replace(CAP_OLD, CAP_NEW, 1)
    v.changes.append('capCIO: operational-issue derivation')

    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, 3 payloads + 1 caption' % v.delta())
    print('  adm %d districts (missed %s), icm %d (%d/%d UCs), tv %d districts, tr %d, '
          'icmq tm %d rows / aic %d rows'
          % (len(adm), format(sum(a['missed'] for a in adm.values()), ','), len(icm),
             sum(r['ruc'] for r in icm.values()), sum(r['tuc'] for r in icm.values()),
             len(raw['tv']), len(raw['tr']), raw['icmq']['n']['tm'], raw['icmq']['n']['aic']))


if __name__ == '__main__':
    main()
