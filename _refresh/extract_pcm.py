"""Extract the post-campaign monitoring payload (const PCM).

Three sources, one payload:
  * PCHS post-campaign household checks (NID Feb 2026 - KP Special Aug 2026)
    D:\\AMAZON DATA\\PCHS Data*.xlsx
  * post-campaign monitoring for the newest campaign
    D:\\AMAZON DATA\\POST CAMPAIGN MONITORING*.xlsx (currently SNID Sept-26)
  * per-UC intra-campaign monitoring (ICM) for the 2026 campaigns plus
    campaign-level ICM/PCM/LQAS aggregates and campaign coverage back to 2017,
    from the KP+TD UC spotting workbook DATA sheet (reuses cache/ch_rows.pkl,
    same cache as extract_chd)

Surveyor names / designations in the PCHS sheet are deliberately NOT extracted -
the public variant is served on GitHub Pages.

Usage: python _refresh/extract_pcm.py [--source PATH] [--out PATH] [--no-cache]
Prints one status line: OK pcm <json chars> <summary> | ERR pcm <reason>
"""
import argparse
import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'pcm'
MONNAME = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
           7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
MONTHS = [('jan', 1), ('feb', 2), ('mar', 3), ('apr', 4), ('may', 5), ('jun', 6),
          ('jul', 7), ('aug', 8), ('sept', 9), ('sep', 9), ('oct', 10), ('nov', 11), ('dec', 12)]
RENAME = {'LAKKIMARWAT': 'LAKKIMRWT', 'LAKKI MARWAT': 'LAKKIMRWT', 'LAKKIMARWAT ': 'LAKKIMRWT',
          'WAZIR-S UPPER': 'WAZIR-S Upper', 'WAZIR-S LOWER': 'WAZIR-S Lower',
          'WAZIR S UPPER': 'WAZIR-S Upper', 'WAZIR S LOWER': 'WAZIR-S Lower',
          'WAZIRISTAN-N': 'WAZIR-N', 'WAZIRISTAN-S LOWER': 'WAZIR-S Lower', 'WAZIRISTAN-S UPPER': 'WAZIR-S Upper',
          'N WAZIRISTAN': 'WAZIR-N', 'S WAZIRISTAN LOWER': 'WAZIR-S Lower', 'S WAZIRISTAN UPPER': 'WAZIR-S Upper'}
# unified per-UC row: di,d,t,u,c,cl,hh,chk,fm,ms,nt,tv,na,rf,sl,ot,zd,fk,vb,dm,vm,gu,gv,pa,ma,rc,rv,sc,sv
RLEN = 29


def num(x):
    if x is None:
        return 0
    if isinstance(x, (int, float)):
        return int(round(x))
    try:
        return int(round(float(str(x).replace(',', '').strip())))
    except ValueError:
        return 0


def clean(x):
    return re.sub(r'\s+', ' ', str(x).strip()) if x is not None else ''


def norm(x):
    return re.sub(r'[^A-Z0-9]', '', str(x).upper())


def lab_month(lab):
    l = str(lab).lower()
    for t, m in MONTHS:
        if t in l:
            return m
    return 0


def lab_year(lab, dflt=None):
    m = re.search(r'(?:20)?(\d{2})\b', str(lab))
    if m:
        v = int(m.group(1))
        return 2000 + v if v < 100 else v
    return dflt


def ctype(lab):
    u = str(lab).upper()
    if 'SNID' in u or 'SIA' in u:
        return 'SNID'
    if u.startswith('NID') or ' NID' in u:
        return 'NID'
    if 'OBR' in u:
        return 'OBR'
    if u.startswith('CR') or 'CR ' in u:
        return 'CR'
    return 'SIA'


def camp_label(raw, y, mo):
    """Display label used for the dataset dropdown and the CQK join."""
    r = clean(raw)
    if 'special' in r.lower() or 'kp sp' in r.lower():
        return r
    t = ctype(r)
    if mo:
        return '%s %s %d' % (t, MONNAME[mo], y)
    return r if r else '%s %d' % (t, y)


def rawtag(raw):
    """Short distinguishing tail for campaigns sharing a month (e.g. BANNU, NORTH, P1)."""
    t = re.sub(r'[^A-Z0-9]+', '', str(raw).upper())
    for mt in ('SEPT', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'):
        i = t.find(mt)
        if i >= 0:
            t = t[:i] + t[i + len(mt):]
            break
    t = re.sub(r'20\d\d', '', t)
    t = re.sub(r'\d{2}', '', t)
    t2 = re.sub(r'^(SNID|SIA|OBR|CRM|NID|CR|ER)', '', t)
    return t2 if t2 else t


def zd_codes(repo):
    """(district, normalised UC name) -> UC code, from the embedded ZD payload."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const ZD = ')
    if i < 0:
        raise SystemExit('ERR pcm const ZD not found in index.html')
    # parsed, not regexed: refresh.py rewrites this payload as compact JSON, and a pattern
    # that expects `"d": "..."` spacing silently returns no rows (and no UC codes).
    j = s.find('\n', i)
    zds = json.loads(s[i + len('const ZD = '):j].rstrip().rstrip(';').replace('<\\/', '</'))
    out, byn = {}, collections.defaultdict(list)
    for r in zds:
        d, u, c = r.get('d'), r.get('u'), r.get('c')
        if not (d and u and c):
            continue
        out[(d, norm(u))] = c
        byn[norm(u)].append(c)
    if not out:
        raise SystemExit('ERR pcm const ZD has no district/UC/code rows')
    uniq = {k: v[0] for k, v in byn.items() if len(v) == 1}
    return out, uniq


class UCMapper:
    def __init__(self, repo):
        self.zd, self.uniq = zd_codes(repo)
        self.missed = []

    def code(self, d, u):
        d2 = RENAME.get(d, d)
        c = self.zd.get((d2, norm(u)))
        if c:
            return c
        c = self.uniq.get(norm(u))
        if c:
            return c
        self.missed.append('%s/%s' % (d2, u))
        return ''


def read_xlsx_rows(path, want_first_sheet=True):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0] if want_first_sheet else wb[wb.sheetnames[0]]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def _hdrlist(r):
    return [clean(x).lower() for x in r]


def _find(hdr, subs, exact=False):
    for i, h in enumerate(hdr):
        if not h:
            continue
        if (h == subs) if exact else (subs in h):
            return i
    return None


def read_pchs(path):
    rows = read_xlsx_rows(path)
    hdr = _hdrlist(rows[0])
    ix = {'camp': _find(hdr, 'campa'), 'd': _find(hdr, 'district'), 't': _find(hdr, 'tehsil'),
          'u': _find(hdr, 'uc', exact=True), 'cl': _find(hdr, 'cluster'),
          'chk': _find(hdr, 'children in hh'), 'fm': _find(hdr, 'children fm'),
          'ms': _find(hdr, 'total missed'), 'nt': _find(hdr, 'nt', exact=True),
          'tv': _find(hdr, 'tvbmc'), 'na': _find(hdr, 'na', exact=True),
          'rf': _find(hdr, 'refusal'), 'zd': _find(hdr, 'zero dose'), 'fk': _find(hdr, 'fake')}
    missing = [k for k, v in ix.items() if v is None]
    if missing:
        raise SystemExit('ERR pcm PCHS sheet missing columns %s (has %s)' % (missing, hdr))
    out = []
    for r in rows[1:]:
        g = lambda k: clean(r[ix[k]]) if ix[k] < len(r) else ''
        n = lambda k: num(r[ix[k]]) if ix[k] < len(r) else 0
        camp, d, u = g('camp'), g('d'), g('u')
        if not camp or not d or not u:
            continue
        out.append({'camp': camp, 'd': d, 't': g('t'), 'u': u,
                    'cl': n('cl'), 'chk': n('chk'), 'fm': n('fm'), 'ms': n('ms'),
                    'nt': n('nt'), 'tv': n('tv'), 'na': n('na'), 'rf': n('rf'),
                    'zd': n('zd'), 'fk': n('fk')})
    return out


def read_pcm26(path):
    rows = read_xlsx_rows(path)
    hi = None
    for i, r in enumerate(rows[:6]):
        h = _hdrlist(r)
        hits = sum(1 for x in h if x and ('district' in x or x == 'uc' or 'camp' in x or 'tehsil' in x))
        if hits >= 3:
            hi = i
            break
    if hi is None:
        raise SystemExit('ERR pcm no header row found in %s' % os.path.basename(path))
    # two-row header: merged group cells on row hi, real names on row hi+1
    h0, h1 = _hdrlist(rows[hi]), (_hdrlist(rows[hi + 1]) if hi + 1 < len(rows) else [])
    hdr = [(h1[i] if i < len(h1) and h1[i] else h0[i]) for i in range(max(len(h0), len(h1)))]
    ix = {'camp': _find(hdr, 'camp'), 'd': _find(hdr, 'district'), 't': _find(hdr, 'tehsil'),
          'u': _find(hdr, 'uc', exact=True), 'chk': _find(hdr, 'check'),
          'fm': _find(hdr, 'fm'), 'ms': _find(hdr, 'not f'),
          'nt': _find(hdr, 'team did not'), 'tv': _find(hdr, 'team missed'),
          'na': _find(hdr, 'away'), 'rf': _find(hdr, 'refus')}
    missing = [k for k, v in ix.items() if v is None]
    if missing:
        raise SystemExit('ERR pcm PCM-26 sheet missing columns %s (has %s)' % (missing, hdr))
    out = []
    for r in rows[hi + 1:]:
        g = lambda k: clean(r[ix[k]]) if ix[k] < len(r) else ''
        n = lambda k: num(r[ix[k]]) if ix[k] < len(r) else 0
        camp, d, u = g('camp'), g('d'), g('u')
        if not camp or not d or not u:
            continue
        if not any(num(x) for x in r if isinstance(x, (int, float))):
            continue
        out.append({'camp': camp, 'd': d, 't': g('t'), 'u': u,
                    'chk': n('chk'), 'fm': n('fm'), 'ms': n('ms'),
                    'nt': n('nt'), 'tv': n('tv'), 'na': n('na'), 'rf': n('rf')})
    return out


ICM_H = {'cl': 'ICM_Clusters_Taken', 'hh': 'ICM_HH_Checked', 'rc': 'ICMrecall 0-59 Check',
         'rv': 'ICMrecall 0-59 Verified', 'ms': 'ICM TMissed', 'nt': 'ICM_TeamNoVisit',
         'tv': 'ICM_TVBCM', 'na': 'ICM_NA', 'rf': 'ICM_REFUSAL', 'sl': 'ICM_Asleep',
         'ot': 'ICM_Other', 'sc': 'ICMseen 0-59 Check', 'sv': 'ICMseen 0-59 verified',
         'vb': 'ICM_VBNFM', 'dm': 'ICM_DOORMARKING', 'zd': 'ICM_ZERODOSE Children',
         'pa': 'ICM_PoorAreas', 'ma': 'ICM_MissedAreas', 'vm': 'ICM_#VaccinatedbyMonitor',
         'gu': 'ICM_Guest in House', 'gv': 'ICM_GuestVaccinated', 'fk': 'NotVaccbutFM',
         'pcl': 'PCM_#ofCluster', 'pchk': 'PCM Total Check', 'pfm': 'PCM_FM', 'pms': 'PCM_NFM',
         'pna': 'PCM_NA', 'prf': 'PCM_REF', 'pborn': 'PCM_Born', 'pnt': 'PCM_NT',
         'ptv': 'PCM_TVBCM', 'psl': 'PCM_Asleep', 'pvb': 'PCM_no_FM VBNFM',
         'pmg': 'PCM_Migrant', 'pfk': 'PCM_FM_notVacc (Fake)', 'pvm': 'PCM_VAccbyMon'}
ICM_KEYS = ['cl', 'hh', 'rc', 'rv', 'ms', 'nt', 'tv', 'na', 'rf', 'sl', 'ot', 'sc', 'sv',
            'vb', 'dm', 'zd', 'pa', 'ma', 'vm', 'gu', 'gv', 'fk']
LQ_H = {'qp': 'LQASpassed', 'qi': 'LQASinterm', 'qf': 'LQASfailed', 'qtm': 'LQAS_TotalMissed',
        'qnt': 'LQAS_NT', 'qtv': 'LQAS_TVBMC', 'qna': 'LQAS_NA', 'qsl': 'LQAS_Asleep',
        'qmg': 'LQAS_Migrated', 'qbn': 'LQAS_Born', 'qrf': 'LQAS_REF', 'qvb': 'LQAS_VBNFM',
        'qfw': 'LQAS_FMwoSV', 'qin': 'LQAS_Inacessible', 'qot': 'LQAS_Others'}
LQ_KEYS = list(LQ_H)
CV_H = {'tg': 'AdmTarget', 'vc': 'AdmCovered', 'zd': 'Adm_ZeroDoze', 'na': 'Adm_Rec_NA',
        'sna': 'Adm_StillNA', 'rec': 'Adm_TotalRecorded', 'st': 'Adm_TotalStillMissed'}


def workbook_monitoring(hdr, rows, verbose=True):
    """Campaign-level ICM + PCM + LQAS + coverage aggregates (trend) and per-UC ICM rows for 2026."""
    missing = [v for v in list(ICM_H.values()) + list(LQ_H.values()) + list(CV_H.values())
               + ['Year', 'Campaign', 'District', 'Tehsil', 'UC_NAME']
               if v not in hdr]
    if missing:
        raise SystemExit('ERR pcm DATA sheet is missing columns %s - layout changed' % missing[:5])
    ix = {k: hdr.index(v) for k, v in ICM_H.items()}
    for k, v in LQ_H.items():
        ix[k] = hdr.index(v)
    icv = {k: hdr.index(v) for k, v in CV_H.items()}
    iy, icamp = hdr.index('Year'), hdr.index('Campaign')
    idist, iteh, iuc = hdr.index('District'), hdr.index('Tehsil'), hdr.index('UC_NAME')

    # case-variant campaign spellings (NIDApr19 / NIDAPR19) aggregate into one campaign
    spell = collections.Counter()
    for r in rows:
        camp = clean(r[icamp])
        if camp:
            spell[camp.upper()] += 1
    canon = {}
    for up, n in spell.items():
        canon[up] = up if n == 1 else None
    for r in rows:
        camp = clean(r[icamp])
        if camp and canon[camp.upper()] is None:
            canon[camp.upper()] = camp  # first-seen spelling wins

    agg = collections.defaultdict(lambda: {k: 0 for k in ICM_KEYS})
    pac = collections.defaultdict(lambda: {k: 0 for k in ['pcl', 'pchk', 'pfm', 'pms', 'pna', 'prf',
                                                          'pborn', 'pnt', 'ptv', 'psl', 'pvb', 'pmg', 'pfk', 'pvm']})
    lqg = collections.defaultdict(lambda: {k: 0 for k in LQ_KEYS})
    cvg = collections.defaultdict(lambda: [0] * 7)  # tg,vc,zd,rec,st,na,sna
    uc26 = collections.defaultdict(lambda: collections.defaultdict(lambda: {k: 0 for k in ICM_KEYS}))
    for r in rows:
        y = num(r[iy])
        camp = clean(r[icamp])
        if not camp:
            continue
        camp = canon[camp.upper()]
        k = (y, camp)
        a, p, q = agg[k], pac[k], lqg[k]
        any_icm = 0
        for f in ICM_KEYS:
            v = num(r[ix[f]])
            a[f] += v
            any_icm += v
        for f in p:
            p[f] += num(r[ix[f]])
        for f in q:
            q[f] += num(r[ix[f]])
        c = cvg[k]
        for j, f in enumerate(('tg', 'vc', 'zd', 'rec', 'st', 'na', 'sna')):
            c[j] += num(r[icv[f]])
        if y == 2026 and any_icm:
            d, t, u = clean(r[idist]), clean(r[iteh]), clean(r[iuc])
            if d and u:
                g = uc26[k][(d, u)]
                g['t'] = g.get('t') or t
                for f in ICM_KEYS:
                    g[f] += num(r[ix[f]])

    if verbose:
        for k in sorted(agg):
            a = agg[k]
            if sum(a.values()) <= 0:
                continue
            chk, fm, ms = a['sc'], a['sv'], a['ms']
            rs = a['nt'] + a['tv'] + a['na'] + a['rf'] + a['sl'] + a['ot']
            srcutil.say('#   ICM %-28s chk=%-7s fm=%-7s (%.1f%%) rchk=%-7s rfm=%-7s tmiss=%-6s reasons=%-6s zd=%-4s fk=%-3s dm=%-5s vm=%-5s'
                        % ('%s %s' % k, chk, fm, (fm / chk * 100 if chk else 0), a['rc'], a['rv'],
                           ms, rs, a['zd'], a['fk'], a['dm'], a['vm']))
        nlq = 0
        for k in sorted(lqg):
            q = lqg[k]
            lots = q['qp'] + q['qi'] + q['qf']
            if lots <= 0:
                continue
            nlq += 1
            if nlq <= 3 or k[0] >= 2026:
                rs = q['qnt'] + q['qtv'] + q['qna'] + q['qsl'] + q['qmg'] + q['qbn'] + q['qrf'] + q['qvb'] + q['qfw'] + q['qin'] + q['qot']
                srcutil.say('#   LQAS %-28s lots=%-5s P=%-5s I=%-4s F=%-5s (%.1f%% pass) tmiss=%-6s reasons=%-6s'
                            % ('%s %s' % k, lots, q['qp'], q['qi'], q['qf'], q['qp'] / lots * 100, q['qtm'], rs))
        ncv = sum(1 for k in cvg if cvg[k][0] > 0)
        zcov = [k for k in cvg if cvg[k][0] > 0 and cvg[k][1] <= 0]
        srcutil.say('#   LQAS campaigns=%d, coverage campaigns=%d (target>0, covered=0: %d)'
                    % (nlq, ncv, len(zcov)))
    return agg, pac, lqg, cvg, uc26


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', help='explicit PCHS or PCM source file')
    ap.add_argument('--out')
    ap.add_argument('--no-cache', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    ds = cfg['auto'][DS]

    pchs_pat = {'roots': ds['roots'], 'patterns': ['PCHS Data*.xlsx', 'PCHS*.xlsx']}
    pcm_pat = {'roots': ds['roots'], 'patterns': ['POST CAMPAIGN MONITORING*.xlsx', '*POST CAMPAIGN*.xlsx']}
    pchs_rec = pcm_rec = None
    if a.source:
        rec = srcutil.stat_rec(a.source)
        if fnmatch_pchs(a.source):
            pchs_rec = rec
        else:
            pcm_rec = rec
    if not pchs_rec:
        pchs_rec = srcutil.newest(pchs_pat)
    if not pcm_rec:
        pcm_rec = srcutil.newest(pcm_pat)
    if not pchs_rec:
        raise SystemExit('ERR pcm no PCHS file found under %s' % ds['roots'])
    if not pcm_rec:
        raise SystemExit('ERR pcm no POST CAMPAIGN MONITORING file found under %s' % ds['roots'])
    srcutil.say('# pcm: PCHS=%s / PCM=%s' % (pchs_rec['name'], pcm_rec['name']))

    pchs = read_pchs(pchs_rec['path'])
    pcm26 = read_pcm26(pcm_rec['path'])

    import extract_chd
    chde = cfg['auto']['chd']
    chd_rec = srcutil.newest(chde)
    if not chd_rec:
        raise SystemExit('ERR pcm spotting workbook not found under %s' % chde['roots'])
    cache_path = os.path.join(srcutil.HERE, chde.get('cache', 'cache/ch_rows.pkl').replace('/', os.sep))
    hdr, wrows, cached = extract_chd.read_rows(chd_rec, chde['sheet'], cache_path, use_cache=not a.no_cache)
    srcutil.say('# pcm: workbook %s (%d rows, cache=%s)' % (chd_rec['name'], len(wrows), 'hit' if cached else 'rebuilt'))
    agg, pac, lqg, cvg, uc26 = workbook_monitoring(hdr, wrows)

    umap = UCMapper(cfg['repo'])

    # ---- campaign x-axis keys (chronological, shared by all sources) ----
    keys = {}

    def key(y, mo, lab):
        k = (y, mo or 0, lab)
        if k not in keys:
            keys[k] = None
        return k

    def keylab(y, mo, raw):
        return MONNAME[mo] + ' ' + str(y)[2:] if mo else camp_label(raw, y, mo)

    def has_lq(k):
        q = lqg[k]
        return q['qp'] + q['qi'] + q['qf'] > 0

    def has_cv(k):
        return cvg[k][0] > 0

    allc = []
    for (y, camp) in sorted(set(agg) | set(lqg) | set(cvg)):
        ag, pc = agg[(y, camp)], pac[(y, camp)]
        if sum(ag.values()) <= 0 and pc['pchk'] + pc['pfm'] + pc['pms'] <= 0 \
                and not has_lq((y, camp)) and not has_cv((y, camp)):
            continue
        allc.append((y, camp))
    grp = collections.defaultdict(list)
    for y, camp in allc:
        grp[(y, lab_month(camp))].append(camp)

    def wklab(y, camp):
        mo = lab_month(camp)
        if len(grp[(y, mo)]) == 1:
            return keylab(y, mo, camp)
        base = camp_label(camp, y, mo)
        if sum(1 for c in grp[(y, mo)] if camp_label(c, y, mo) == base) > 1:
            base += ' \u00b7 ' + rawtag(camp)
        return base

    wk = {}
    for (y, camp) in allc:
        wk[(y, camp)] = key(y, lab_month(camp), wklab(y, camp))
    pk = {}
    for r in pchs:
        mo = lab_month(r['camp'])
        y = lab_year(r['camp'], 2026)
        pk[r['camp']] = key(y, mo, keylab(y, mo, r['camp']))
    mo26 = lab_month(pcm26[0]['camp'])
    ck = key(lab_year(pcm26[0]['camp'], 2026), mo26,
             keylab(lab_year(pcm26[0]['camp'], 2026), mo26, pcm26[0]['camp']))
    order = sorted(keys)
    xof = {k: i for i, k in enumerate(order)}
    tc = [k[2] for k in order]

    # ---- trend rows: [x, src, cl, chk, fm, ms, zd, fk, label] ----
    tr = []
    for (y, camp) in sorted(agg):
        x = xof.get(wk.get((y, camp)))
        if x is None:
            continue
        lab = camp_label(camp, y, lab_month(camp))
        ag, pc = agg[(y, camp)], pac[(y, camp)]
        if sum(ag.values()) > 0:
            tr.append([x, 0, ag['cl'], ag['sc'], ag['sv'], ag['ms'], ag['zd'], ag['fk'], lab,
                       ag['rc'], ag['rv']])
        if pc['pchk'] + pc['pfm'] + pc['pms'] > 0:
            tr.append([x, 1, pc['pcl'], pc['pchk'], pc['pfm'], pc['pms'], 0, pc['pfk'], lab, 0, 0])
    psum = collections.defaultdict(lambda: [0] * 7)  # cl,chk,fm,ms,zd,fk,n
    for r in pchs:
        s = psum[r['camp']]
        s[0] += r['cl']; s[1] += r['chk']; s[2] += r['fm']; s[3] += r['ms']; s[4] += r['zd']; s[5] += r['fk']; s[6] += 1
    for camp, s in psum.items():
        mo = lab_month(camp)
        y = lab_year(camp, 2026)
        tr.append([xof[pk[camp]], 2, s[0], s[1], s[2], s[3], s[4], s[5], camp_label(camp, y, mo), 0, 0])
    s26 = [0] * 6
    for r in pcm26:
        s26[0] += r['chk']; s26[1] += r['fm']; s26[2] += r['ms']
    c26lab = camp_label(pcm26[0]['camp'], lab_year(pcm26[0]['camp'], 2026), mo26)
    tr.append([xof[ck], 1, 0, s26[0], s26[1], s26[2], 0, 0, c26lab, 0, 0])
    tr.sort(key=lambda t: (t[0], t[1]))

    # ---- LQAS lots per campaign: [x, lots, P, I, F, tmiss, nt, tv, na, sl, mg, bn, rf, vb, fw, in, ot] ----
    lq = []
    for (y, camp) in sorted(lqg):
        if not has_lq((y, camp)):
            continue
        x = xof.get(wk.get((y, camp)))
        if x is None:
            continue
        q = lqg[(y, camp)]
        lq.append([x, q['qp'] + q['qi'] + q['qf'], q['qp'], q['qi'], q['qf'], q['qtm'],
                   q['qnt'], q['qtv'], q['qna'], q['qsl'], q['qmg'], q['qbn'],
                   q['qrf'], q['qvb'], q['qfw'], q['qin'], q['qot']])
    lq.sort()

    # ---- campaign coverage: [x, target, covered, zd-recorded, rec, still, na, still-na]
    # (keep every campaign with a target; covered may be 0 when not yet compiled) ----
    cv = []
    for (y, camp) in sorted(cvg):
        t, v, zd, rec, st, na, sna = cvg[(y, camp)]
        if t <= 0:
            continue
        x = xof.get(wk.get((y, camp)))
        if x is None:
            continue
        cv.append([x, t, v, zd, rec, st, na, sna])
    cv.sort()

    # ---- advance-report zero-dose chain per slot: [x, reported, covered|null] ----
    # covered=null when every advance-report triplet for the campaign leaves it blank
    ad = []
    adv_path = os.path.join(srcutil.OUT, 'adv.json')
    if os.path.exists(adv_path):
        with open(adv_path, encoding='utf-8') as f:
            advj = json.load(f)
        ak = collections.defaultdict(lambda: [0, 0, 0, 0])  # rep, cov, nulls, rows
        for ci, c in enumerate(advj['c']):
            if not c.get('m'):
                continue
            ar = ak[(ctype(c['n']), c['m'], c.get('y') or 0)]
            for t3 in advj['r'][ci]:
                ar[0] += t3[1] or 0
                ar[3] += 1
                if t3[2] is None:
                    ar[2] += 1
                else:
                    ar[1] += t3[2]
        slot_ad = collections.defaultdict(lambda: [0, 0, 0, 0])
        for (y, camp) in cvg:
            x = xof.get(wk.get((y, camp)))
            if x is None:
                continue
            d = (ctype(camp), lab_month(camp), y)
            if d in ak:
                sa, aa = slot_ad[x], ak[d]
                for j in range(4):
                    sa[j] += aa[j]
        for x in sorted(slot_ad):
            rep, cov, nul, n = slot_ad[x]
            if rep > 0:
                ad.append([x, rep, None if nul >= n else cov])
        srcutil.say('# pcm: advance-report join: %d slots, %d campaigns rep>0'
                    % (len(slot_ad), sum(1 for r in ad if r[2] is not None)))

    # ---- datasets (newest first) + UC rows ----
    ds_out, rows = [], []

    def add_ds(label, q, src, n, caps, rws):
        di = len(ds_out)
        ds_out.append({'n': label, 'q': q, 's': src, 'u': n,
                       'zd': caps.get('zd', 0), 'fk': caps.get('fk', 0), 'vb': caps.get('vb', 0),
                       'dm': caps.get('dm', 0), 'pa': caps.get('pa', 0)})
        for r in rws:
            rows.append([di] + r)

    # SNID Sept-26 PCM
    r26 = []
    for r in pcm26:
        d = RENAME.get(r['d'], r['d'])
        r26.append([d, r['t'], r['u'], umap.code(d, r['u']),
                    0, 0, r['chk'], r['fm'], r['ms'], r['nt'], r['tv'], r['na'], r['rf'],
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0][:RLEN])
    add_ds(c26lab + ' · post-campaign monitoring (PCM)', c26lab, 1, len(r26), {}, r26)

    # PCHS campaigns, newest campaign first
    by_camp = collections.defaultdict(list)
    for r in pchs:
        by_camp[r['camp']].append(r)
    def camp_sort(c):
        return (lab_year(c, 2026) or 0, lab_month(c) or 0)
    for camp in sorted(by_camp, key=camp_sort, reverse=True):
        mo, y = lab_month(camp), lab_year(camp, 2026)
        lab = camp_label(camp, y, mo)
        rp = []
        for r in by_camp[camp]:
            d = RENAME.get(r['d'], r['d'])
            rp.append([d, r['t'], r['u'], umap.code(d, r['u']),
                       r['cl'], 0, r['chk'], r['fm'], r['ms'], r['nt'], r['tv'], r['na'], r['rf'],
                       0, 0, r['zd'], r['fk'], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0][:RLEN])
        add_ds(lab + ' · PCHS household checks', lab, 2, len(rp), {'zd': 1, 'fk': 1}, rp)

    # ICM 2026, newest campaign first
    for (y, camp) in sorted(uc26, key=lambda k: (k[0], lab_month(k[1])), reverse=True):
        if y != 2026:
            continue
        mo = lab_month(camp)
        lab = camp_label(camp, y, mo)
        ri = []
        for (d, u), g in sorted(uc26[(y, camp)].items()):
            d2 = RENAME.get(d, d)
            ri.append([d2, g.get('t', ''), u, umap.code(d2, u),
                       g['cl'], g['hh'], g['sc'], g['sv'], g['ms'], g['nt'], g['tv'], g['na'], g['rf'],
                       g['sl'], g['ot'], g['zd'], g['fk'], g['vb'], g['dm'], g['vm'], g['gu'], g['gv'],
                       g['pa'], g['ma'], g['rc'], g['rv'], g['sc'], g['sv']][:RLEN])
        add_ds(lab + ' · intra-campaign monitoring (ICM)', lab, 0, len(ri),
               {'zd': 1, 'fk': 1, 'vb': 1, 'dm': 1, 'pa': 1}, ri)

    # order datasets newest-first overall
    ds_sorted = sorted(range(len(ds_out)), key=lambda j: (-(lab_year(ds_out[j]['q'], 0) or 0),
                                                          -lab_month(ds_out[j]['q']),
                                                          [1, 2, 0].index(ds_out[j]['s'])))
    newds = [ds_out[j] for j in ds_sorted]
    remap = {old: new for new, old in enumerate(ds_sorted)}
    for r in rows:
        r[0] = remap[r[0]]
    ds_out = newds

    out = {'tc': tc, 'tr': tr, 'lq': lq, 'cv': cv, 'ad': ad, 'ds': ds_out, 'r': rows}
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'pcm.json')
    srcutil.write_text(dest, js)

    # ---- sanity report ----
    srcutil.say('# pcm: UC-code join misses (%d): %s' % (len(umap.missed), ', '.join(umap.missed[:12]) or 'none'))
    for di, d in enumerate(ds_out):
        rr = [r for r in rows if r[0] == di]
        chk, fm, ms = sum(r[7] for r in rr), sum(r[8] for r in rr), sum(r[9] for r in rr)
        nt, tv, na, rf, sl, ot = (sum(r[10] for r in rr), sum(r[11] for r in rr), sum(r[12] for r in rr),
                                  sum(r[13] for r in rr), sum(r[14] for r in rr), sum(r[15] for r in rr))
        zd, fk = sum(r[16] for r in rr), sum(r[17] for r in rr)
        srcutil.say('#   %-52s %4d UCs chk=%-7s fm=%-7s (%5.1f%%) ms=%-5s (nt %s tv %s na %s rf %s sl %s ot %s gap %s) zd=%s fk=%s'
                    % (d['n'], d['u'], chk, fm, (fm / chk * 100 if chk else 0), ms, nt, tv, na, rf, sl, ot,
                       ms - nt - tv - na - rf - sl - ot, zd, fk))
    wn = [r for r in rows if r[0] == 0 and r[1] == 'WAZIR-N']
    if wn:
        srcutil.say('#   WAZIR-N Sept-26 PCM: %d UCs, chk=%s fm=%s ms=%s no-team=%s'
                    % (len(wn), sum(r[7] for r in wn), sum(r[8] for r in wn),
                       sum(r[9] for r in wn), sum(r[10] for r in wn)))
    summary = '%d trend pts (%d campaigns), %d LQAS campaigns, %d with coverage (%d with advance-report chain), %d datasets, %d UC rows' % (
        len(tr), len(tc), len(lq), len(cv), len(ad), len(ds_out), len(rows))
    print('SRC pcm %s | %s' % (pchs_rec['path'], pcm_rec['path']))
    print('OK pcm %d %s' % (len(js), summary))


def fnmatch_pchs(path):
    import fnmatch
    name = os.path.basename(path)
    return any(fnmatch.fnmatch(name, p) for p in ['PCHS Data*.xlsx', 'PCHS*.xlsx'])


if __name__ == '__main__':
    main()
