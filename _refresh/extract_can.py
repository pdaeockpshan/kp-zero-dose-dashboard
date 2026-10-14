"""Extract the district-level campaign-analysis payload (const CAN) from the KP+TD spotting workbook.

Same DATA sheet and cache as extract_chd.py, aggregated per campaign x district. Row layout
(33 fields, all sums of the UC rows):
 [di, tgt, cov, stillNA, stillRef, stillTot, zd, recNA, recRef, sdc,
  icmClu, icmChk, icmVer, icmMiss, icmNA, icmRef, icmTNV, icmTVBCM,
  msN, msChk, msVer, msMiss, msNTH, msNTC, msNA, msRef, msSlp,
  lqP, lqI, lqF, pcmClu, pcmChk, pcmFM]
Campaign order and district indexes are asserted against the dashboard's CHD payload, so
CAN.d[i] aligns with CHD.c[i] and di indexes CAN.ds == CHD.ds.

Usage: python _refresh/extract_can.py [--source PATH] [--out PATH] [--no-cache]
Prints one status line: OK can <json chars> <summary> | ERR can <reason>
"""
import argparse
import collections
import datetime
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
import extract_chd as chd

DS = 'can'
FIELDS = ['tgt', 'cov', 'sna', 'srf', 'stot', 'zd',
          'rec_na', 'rec_ref', 'sdc',
          'icm_clu', 'icm_chk', 'icm_ver', 'icm_miss', 'icm_na', 'icm_ref', 'icm_tnv', 'icm_tvbcm',
          'ms_n', 'ms_chk', 'ms_ver', 'ms_miss', 'ms_nth', 'ms_ntc', 'ms_na', 'ms_ref', 'ms_slp',
          'lq_p', 'lq_i', 'lq_f', 'pcm_clu', 'pcm_chk', 'pcm_fm']
ICOLS = {'cov': 'AdmCovered', 'sna': 'Adm_StillNA', 'srf': 'Adm_StillREF',
         'stot': 'Adm_TotalStillMissed', 'zd': 'Adm_ZeroDoze',
         'rec_na': 'Adm_Rec_NA', 'rec_ref': 'Adm_Rec_Ref', 'sdc': 'Adm_SDC',
         'icm_clu': 'ICM_Clusters_Taken', 'icm_chk': 'ICMrecall 0-59 Check',
         'icm_ver': 'ICMrecall 0-59 Verified', 'icm_miss': 'ICM TMissed',
         'icm_na': 'ICM_NA', 'icm_ref': 'ICM_REFUSAL', 'icm_tnv': 'ICM_TeamNoVisit',
         'icm_tvbcm': 'ICM_TVBCM', 'ms_n': '# of MS', 'ms_chk': 'MS_Checked',
         'ms_ver': 'MS_Verified', 'ms_miss': 'MS_Missed', 'ms_nth': 'MS_NTHouse Missed',
         'ms_ntc': 'MS_NTChildMissed', 'ms_na': 'MS_NA', 'ms_ref': 'MS_REF',
         'ms_slp': 'MS_Child Asleep', 'lq_p': 'LQASpassed', 'lq_i': 'LQASinterm',
         'lq_f': 'LQASfailed', 'pcm_clu': 'PCM_#ofCluster', 'pcm_chk': 'PCM Total Check',
         'pcm_fm': 'PCM_FM'}


def chd_const(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const CHD = ')
    if i < 0:
        raise SystemExit('ERR can const CHD not found in index.html')
    j = s.find('\n', i)
    import json
    return json.loads(s[i + len('const CHD = '):j].rstrip().rstrip(';').replace('<\\/', '</'))


def build(hdr, rows, repo, rec):
    ix = {}
    for k, v in ICOLS.items():
        if v not in hdr:
            raise SystemExit('ERR can DATA sheet is missing column %r - layout changed, update ICOLS' % v)
        ix[k] = hdr.index(v)
    mp_ix = hdr.index('Adm_MPTarget')
    adm_ix = hdr.index('AdmTarget')
    dist_ix = hdr.index(chd.COLS['dist'])
    camp_ix = hdr.index(chd.COLS['camp'])
    year_ix = hdr.index(chd.COLS['year'])
    prov_ix = hdr.index(chd.COLS['prov'])
    mon_ix = hdr.index(chd.COLS['month'])

    ref = chd_const(repo)
    order, div = chd.district_order(repo)
    di = {d: i for i, d in enumerate(order)}

    G = collections.defaultdict(lambda: [0] * len(FIELDS))
    mos = collections.defaultdict(list)
    for r in rows:
        if r[prov_ix] not in ('KP', 'KPTD'):
            continue
        d = str(r[dist_ix]).strip()
        if d not in div:
            continue
        y = int(r[year_ix])
        lab = str(r[camp_ix]).strip()
        g = G[(y, lab, d)]
        tmp = chd.num(r[mp_ix])
        g[0] += tmp if tmp > 0 else max(chd.num(r[adm_ix]), 0)
        for fi in range(1, len(FIELDS)):
            g[fi] += chd.num(r[ix[FIELDS[fi]]])
        if r[mon_ix]:
            mos[(y, lab)].append(chd.MONIDX.get(str(r[mon_ix]).strip()[:3].title(), 0))

    C = collections.defaultdict(dict)
    for (y, lab, d), g in G.items():
        if any(g):
            C[(y, lab)][d] = list(g)

    cams = []
    for (y, lab), drows in C.items():
        mo = chd.lab_month(lab)
        if mo is None:
            cc = [m for m in mos.get((y, lab), []) if m]
            mo = collections.Counter(cc).most_common(1)[0][0] if cc else 0
        cams.append({'y': y, 'mo': mo, 'n': lab, 'd': drows})
    cams.sort(key=lambda x: (x['y'], x['mo'], x['n']))

    if len(cams) != len(ref['c']):
        raise SystemExit('ERR can extracted %d campaigns but dashboard CHD has %d - workbook changed?'
                         % (len(cams), len(ref['c'])))
    for a, b in zip(cams, ref['c']):
        if a['n'] != b['n'] or a['y'] != b['y']:
            raise SystemExit('ERR can campaign order mismatch: workbook %r vs dashboard %r'
                             % ((a['y'], a['n']), (b['y'], b['n'])))

    d = []
    for c in cams:
        rows_c = sorted([[di[dn]] + g for dn, g in c['d'].items()], key=lambda x: x[0])
        d.append(rows_c)

    def camp_has(fi):
        return sum(1 for rc in d if any(r[fi + 1] for r in rc))
    asof = datetime.date.fromtimestamp(rec['mtime']).isoformat()
    out = {'src': 'KP+TD UC spotting workbook DATA sheet, campaign x district aggregate',
           'asof': asof, 'ds': order, 'n': [c['n'] for c in cams], 'd': d}
    summary = '%d campaigns %s-%s, %d districts, %d rows, %d campaigns with ICM, %d MS, %d LQAS, %d PCM' % (
        len(cams), '%s%s' % (chd.MONNAME.get(cams[0]['mo'], ''), cams[0]['y']),
        '%s%s' % (chd.MONNAME.get(cams[-1]['mo'], ''), cams[-1]['y']),
        len(order), sum(len(x) for x in d),
        camp_has(10), camp_has(18), camp_has(26), camp_has(30))
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    ap.add_argument('--no-cache', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    ds = cfg['auto'][DS]
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(ds)
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR can no spotting workbook found under %s' % ds['roots'])
    cache_path = os.path.join(srcutil.HERE, ds.get('cache', 'cache/ch_rows.pkl').replace('/', os.sep))
    hdr, rows, cached = chd.read_rows(rec, ds['sheet'], cache_path, use_cache=not a.no_cache)
    srcutil.say('# can: %s (%d rows, cache=%s)' % (rec['name'], len(rows), 'hit' if cached else 'rebuilt'))
    out, summary = build(hdr, rows, cfg['repo'], rec)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'can.json')
    srcutil.write_text(dest, js)
    print('SRC can %s' % rec['path'])
    print('OK can %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
