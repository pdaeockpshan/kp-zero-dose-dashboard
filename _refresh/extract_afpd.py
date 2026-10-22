"""Extract the AFP case + lab database payload (const AFPD) from the EOC master DBF exports.

Usage: python _refresh/extract_afpd.py [--afp PATH] [--lab PATH] [--source PATH] [--out PATH]
Prints: SRC lines + one status line `OK afpd <json chars> <summary>` | ERR afpd <reason>

Sources (both in Downloads, exported from the EOC portal's AFP case database
and polio lab database):
  * `AFP.DBF`    - AFP case master: one row per AFP case, KP only, 2022-2026.
  * `AFPLAB.DBF` - Polio lab database: one row per stool specimen (cases,
                   contacts and hotcases), 2022-2026.

Both are dBase III files: 32-byte header, 32-byte field descriptors, then
fixed-width space-padded ASCII records (the portal writes non-standard field
type codes, but every value is a string; dates are YYYYMMDD).

PII: the case DB carries names and addresses. The DBF reader decodes every
field in memory; aggregation uses dates, geography, dose history and result
codes. Only provincial and district/year/month aggregates are emitted, never
patient, UC or EPID identifiers - the dashboard is a public GitHub Pages site.

Result codes (asserted against the case DB's merged copy of the same results):
1 = positive, 2 = negative, 7 = pending / not done. CLASS: 1 = WPV1,
2 = VDPV, 3 = discarded, blank = pending expert classification.
Timeliness follows the portal's own flags (verified against the line list):
notified <7 days = DNOT-DONSET in 0-7 days; investigated <48 h =
DOI-DNOT in 0-2 days (48 h from notification, the WHO definition - the
DBF carries dates only, so the day boundary is approximate). The lab's
"result reported" date is DVIREP (the virus report; DIRES is only filled
for a small subset of typed specimens).

Payload: {"src":..,"asof":..,"onset":..,"lsrc":..,"lcoll":..,"lres":..,
          "yrs":[2022..2026],"k":CK,"y":{year:[CK values]},
          "mon26":[12 monthly case counts],
          "d":{district:[n,ad,n7,i48,zd]},
          "dy":{district:[[CK values] for each year in yrs]},
          "dm":{district:[[12 monthly case counts] for each year in yrs]},
          "zm":{district:[[12 discarded],[12 pending],[12 confirmed]]},
          "lab":{"sm":[12],"rm":[12],"sp":..,"rs":..,"pv1":..,"npev":..,
                 "tt":..,"t14":..}}
CK: n,ad,n7,i48,zd,du,c1,cw,cp,c3,d1,d2,d3,zp,zc,zw,zi. The added dose
groups are 1, 2 and 3+; zp/zc/zw are zero-dose pending/discarded/confirmed
(CLASS 1 or 2), and zi requires zero doses and ADEQ == INADEQ. zi overlaps
those classification groups. zm is zero-dose only, 2026 only; months are Jan-Dec.
Legacy 2022 WAZIR-S is retained separately as WAZIR-S (undivided) in dy/dm.
Lab turnaround includes valid report >= collection pairs collected in 2026.
"""
import argparse
import datetime
import json
import os
import statistics
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'afpd'
YRS = [2022, 2023, 2024, 2025, 2026]
CK = ['n', 'ad', 'n7', 'i48', 'zd', 'du', 'c1', 'cw', 'cp', 'c3',
      'd1', 'd2', 'd3', 'zp', 'zc', 'zw', 'zi']
DK = ['n', 'ad', 'n7', 'i48', 'zd']
ZK = ['zc', 'zp', 'zw']
RENAME = {'WAZIR-S LOWER': 'WAZIR-S Lower', 'WAZIR-S UPPER': 'WAZIR-S Upper'}
UNDIVIDED = 'WAZIR-S (undivided)'


def dbf_records(path, need=('PROVINCE', 'YRONSET', 'DISTRICT', 'DONSET')):
    """Yield one dict per dBase III record (fixed-width ASCII fields)."""
    with open(path, 'rb') as fh:
        hdr = fh.read(32)
        if len(hdr) < 32 or hdr[0] != 3:
            raise SystemExit('ERR afpd %s is not a dBase III file' % os.path.basename(path))
        nrec = struct.unpack('<I', hdr[4:8])[0]
        hlen = struct.unpack('<H', hdr[8:10])[0]
        rlen = struct.unpack('<H', hdr[10:12])[0]
        fields = []
        fh.seek(32)
        while True:
            fd = fh.read(32)
            if not fd or fd[0] == 0x0D:
                break
            name = fd[:11].split(b'\x00')[0].decode('ascii', 'replace').strip()
            fields.append((name, fd[16]))
        want = {n: l for n, l in fields}
        for col in need:
            if col not in want:
                raise SystemExit('ERR afpd %s misses column %s' % (os.path.basename(path), col))
        fh.seek(hlen)
        for _ in range(nrec):
            rec = fh.read(rlen)
            if len(rec) < rlen:
                break
            if rec[0] == 0x2A:      # deleted record
                continue
            d = {}
            off = 1
            for name, l in fields:
                d[name] = rec[off:off + l].decode('ascii', 'replace').strip()
                off += l
            yield d


def pdate(s):
    s = (s or '').strip()
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return datetime.date(int(s[:4]), int(s[4:6]), int(s[6:]))
    except ValueError:
        return None


def num(s):
    t = ('' if s is None else str(s)).strip()
    if not t:
        return None
    try:
        return int(float(t))
    except ValueError:
        return None


def nk(s):
    return ''.join(ch for ch in str(s or '').upper() if ch.isalnum())


def surv_scope(repo):
    """Exact `const SURV` district keys, read from index.html so naming stays put."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SURV = ')
    if i < 0:
        raise SystemExit('ERR afpd const SURV not found in index.html')
    j = s.find('\n', i)
    dists = list(json.loads(s[i + len('const SURV = '):j].rstrip().rstrip(';')).keys())
    rev = {nk(d): d for d in dists}
    rev.update({nk(alias): target for alias, target in RENAME.items() if target in dists})
    rev.update({alias: target for alias, target in
                {'WAZIRSL': 'WAZIR-S Lower', 'WAZIRSU': 'WAZIR-S Upper'}.items()
                if target in dists})
    return dists, (lambda s: rev.get(nk(s)))


def pick(entry, which, override=None):
    """Newest file under the entry matching one exact filename, or the override."""
    pat = 'AFP.DBF' if which == 'afp' else 'AFPLAB.DBF'
    if override:
        return override
    best = None
    for rec in srcutil.discover(entry):
        if rec['name'] == pat:
            if best is None or rec['mtime'] > best['mtime']:
                best = rec
    if best is None:
        raise SystemExit('ERR afpd no %s under %s' % (pat, entry.get('roots')))
    return best['path']


def case_metrics(r, onset):
    """Compute each case's increments once for all aggregate views."""
    a = dict.fromkeys(CK, 0)
    a['n'] = 1
    notif, inves = pdate(r['DNOT']), pdate(r['DOI'])
    a['n7'] = int(bool(onset and notif and 0 <= (notif - onset).days <= 7))
    a['i48'] = int(bool(onset and notif and inves and 0 <= (inves - notif).days <= 2))
    a['ad'] = int(r['ADEQ'] == 'ADEQ')
    do = num(r['DOSES'])
    if do is None:
        a['du'] = 1
    elif do == 0:
        a['zd'] = 1
    elif do == 1:
        a['d1'] = 1
    elif do == 2:
        a['d2'] = 1
    elif do >= 3:
        a['d3'] = 1
    else:
        raise SystemExit('ERR afpd negative dose count')
    cls = r['CLASS']
    ck = 'c3' if cls == '3' else 'cw' if cls in ('1', '2') else 'cp'
    a[ck] = 1
    a['c1'] = int(cls == '1')
    if a['zd']:
        a[{'c3': 'zc', 'cw': 'zw', 'cp': 'zp'}[ck]] = 1
        a['zi'] = int(r['ADEQ'] == 'INADEQ')
    return a


def validate_case_metrics(a, scope):
    for keys, total in ((('zd', 'd1', 'd2', 'd3', 'du'), 'n'),
                        (('cp', 'c3', 'cw'), 'n'), (('zp', 'zc', 'zw'), 'zd')):
        if sum(a[k] for k in keys) != a[total]:
            raise SystemExit('ERR afpd %s %s buckets != %s' % (scope, '/'.join(keys), total))
    if any(not 0 <= a[k] <= a['n'] for k in CK):
        raise SystemExit('ERR afpd %s metric outside case count' % scope)
    if (a['c1'] > a['cw'] or a['zp'] > a['cp'] or a['zc'] > a['c3']
            or a['zw'] > a['cw'] or a['zi'] > a['zd'] or a['zi'] > a['n'] - a['ad']):
        raise SystemExit('ERR afpd %s inconsistent subset counts' % scope)


def build_case(path, repo):
    dists, dkey = surv_scope(repo)
    y = {yr: dict.fromkeys(CK, 0) for yr in YRS}
    mon = {yr: [0] * 12 for yr in YRS}
    history_dists = dists + [UNDIVIDED]
    dy = {k: {yr: dict.fromkeys(CK, 0) for yr in YRS} for k in history_dists}
    dm = {k: {yr: [0] * 12 for yr in YRS} for k in history_dists}
    zm = {k: [[0] * 12 for _ in ZK] for k in dists}
    maxon = maxen = None
    skip = unknown = 0
    for r in dbf_records(path):
        if r['PROVINCE'] != 'KP':
            skip += 1
            continue
        try:
            yr = int(r['YRONSET'])
        except ValueError:
            skip += 1
            continue
        if yr not in YRS:
            skip += 1
            continue
        k = UNDIVIDED if yr == 2022 and nk(r['DISTRICT']) == 'WAZIRS' else dkey(r['DISTRICT'])
        if k is None:
            unknown += 1
            continue
        onset = pdate(r['DONSET'])
        if onset is None or onset.year != yr:
            raise SystemExit('ERR afpd invalid or mismatched onset date in %d' % yr)
        if maxon is None or onset > maxon:
            maxon = onset
        en = pdate(r['DENTER'])
        if en and (maxen is None or en > maxen):
            maxen = en
        inc = case_metrics(r, onset)
        for a in (y[yr], dy[k][yr]):
            for key in CK:
                a[key] += inc[key]
        mi = onset.month - 1
        mon[yr][mi] += inc['n']
        dm[k][yr][mi] += inc['n']
        if yr == 2026:
            for zi, key in enumerate(ZK):
                zm[k][zi][mi] += inc[key]
    if unknown:
        raise SystemExit('ERR afpd %d rows with a district outside the SURV scope' % unknown)
    if maxon is None or maxen is None:
        raise SystemExit('ERR afpd no KP rows with onset/entry dates')
    d = {k: {key: dy[k][2026][key] for key in DK} for k in dists}
    wpv = {k: dy[k][2026]['c1'] for k in dists if dy[k][2026]['c1']}
    empty = [k for k in dists if d[k]['n'] == 0]
    if empty:
        raise SystemExit('ERR afpd no 2026 cases for %s' % empty)
    for yr in YRS:
        if y[yr]['n'] < 1000:
            raise SystemExit('ERR afpd only %d cases in %d' % (y[yr]['n'], yr))
        validate_case_metrics(y[yr], str(yr))
        if sum(mon[yr]) != y[yr]['n']:
            raise SystemExit('ERR afpd %d monthly total != year cases' % yr)
        for key in CK:
            if sum(dy[k][yr][key] for k in history_dists) != y[yr][key]:
                raise SystemExit('ERR afpd %d district %s total != year total' % (yr, key))
        for mi in range(12):
            if sum(dm[k][yr][mi] for k in history_dists) != mon[yr][mi]:
                raise SystemExit('ERR afpd %d month %d district total != year total' % (yr, mi + 1))
        for k in history_dists:
            validate_case_metrics(dy[k][yr], '%s %d' % (k, yr))
            if sum(dm[k][yr]) != dy[k][yr]['n']:
                raise SystemExit('ERR afpd %s %d monthly total != cases' % (k, yr))
    for zi, key in enumerate(ZK):
        if sum(sum(zm[k][zi]) for k in dists) != y[2026][key]:
            raise SystemExit('ERR afpd 2026 monthly %s total != year total' % key)
        for k in dists:
            if sum(zm[k][zi]) != dy[k][2026][key]:
                raise SystemExit('ERR afpd %s 2026 monthly %s total != cases' % (k, key))
    for k in dists:
        for mi in range(12):
            if sum(zm[k][zi][mi] for zi in range(len(ZK))) > dm[k][2026][mi]:
                raise SystemExit('ERR afpd %s 2026 month %d zero-dose total > cases' % (k, mi + 1))
    return y, mon[2026], d, dy, dm, zm, wpv, maxon, maxen, skip


def build_lab(path):
    sm = [0] * 12
    rm = [0] * 12
    sp = rs = pv1 = npev = 0
    tt = []
    maxc = maxr = None
    for r in dbf_records(path, ('PROVINCE', 'DISTRICT', 'DSTCOLL1', 'DVIREP1')):
        if r['PROVINCE'] != 'KP':
            continue
        c1 = pdate(r['DSTCOLL1'])
        c2 = pdate(r['DSTCOLL2'])
        r1 = pdate(r['DVIREP1'])
        r2 = pdate(r['DVIREP2'])
        for c in (c1, c2):
            if c and c.year == 2026:
                sm[c.month - 1] += 1
                sp += 1
                if maxc is None or c > maxc:
                    maxc = c
        for rr in (r1, r2):
            if rr and rr.year == 2026:
                rm[rr.month - 1] += 1
                rs += 1
                if maxr is None or rr > maxr:
                    maxr = rr
        if (r['ITDP11'] == '1' or r['ITDP12'] == '1') and (c1 and c1.year == 2026 or c2 and c2.year == 2026):
            pv1 += 1
        if (r['ENTERO1'] == '1' or r['ENTERO2'] == '1') and (c1 and c1.year == 2026 or c2 and c2.year == 2026):
            npev += 1
        for c, rr in ((c1, r1), (c2, r2)):
            if c and c.year == 2026 and rr and rr >= c:
                tt.append((rr - c).days)
    if maxc is None or maxr is None:
        raise SystemExit('ERR afpd no 2026 lab specimens with collection/report dates')
    med = statistics.median(tt) if tt else None
    t14 = round(100.0 * sum(1 for x in tt if x <= 14) / len(tt), 1) if tt else None
    if sp < 5000:
        raise SystemExit('ERR afpd only %d specimens collected in 2026' % sp)
    if rs < sp * 0.5:
        raise SystemExit('ERR afpd only %d of %d specimens have a reported result' % (rs, sp))
    return {'sm': sm, 'rm': rm, 'sp': sp, 'rs': rs, 'pv1': pv1, 'npev': npev,
            'tt': med, 't14': t14}, maxc, maxr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--afp')
    ap.add_argument('--lab')
    ap.add_argument('--source', help='accepted for refresh.py run; routed by filename')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    afp = a.afp or (a.source if a.source and os.path.basename(a.source).upper() == 'AFP.DBF' else None)
    lab = a.lab or (a.source if a.source and os.path.basename(a.source).upper() == 'AFPLAB.DBF' else None)
    afp = pick(entry, 'afp', afp)
    lab = pick(entry, 'lab', lab)
    if not os.path.exists(afp) or not os.path.exists(lab):
        raise SystemExit('ERR afpd source missing')
    print('SRC afpd case %s' % afp)
    print('SRC afpd lab %s' % lab)

    y, mon, d, dy, dm, zm, wpv, maxon, maxen, skip = build_case(afp, cfg['repo'])
    labd, maxc, maxr = build_lab(lab)

    afpd = {'src': os.path.basename(afp), 'asof': maxen.strftime('%d-%b-%Y'),
            'onset': maxon.isoformat(),
            'lsrc': os.path.basename(lab), 'lcoll': maxc.isoformat(), 'lres': maxr.isoformat(),
            'yrs': YRS, 'k': CK,
            'y': {str(yr): [y[yr][k] for k in CK] for yr in YRS},
            'mon26': mon, 'd': {k: [d[k][x] for x in DK] for k in d},
            'dy': {k: [[dy[k][yr][x] for x in CK] for yr in YRS] for k in dy},
            'dm': {k: [dm[k][yr] for yr in YRS] for k in dm},
            'zm': zm, 'lab': labd}
    js = srcutil.dumps(afpd)
    dest = a.out or os.path.join(srcutil.OUT, 'afpd.json')
    srcutil.write_text(dest, js)
    y26 = y[2026]
    pc = lambda a_, b_: round(100.0 * a_ / b_, 1) if b_ else 0.0
    summary = ('%d KP AFP cases %d-%d, %d in 2026 (onset to %s, entered to %s): adequacy %s%%, '
               'notified <7d %s%%, investigated <48h %s%%, %d zero-dose, %d WPV1, %d pending; '
               'lab 2026: %d specimens, %d results (to %s), %d PV1 / %d NPEV isolations, '
               'median turnaround %sd (%s%% within 14d)'
               % (y[2022]['n'] + y[2023]['n'] + y[2024]['n'] + y[2025]['n'] + y[2026]['n'],
                  YRS[0], YRS[-1], y26['n'], maxon, maxen,
                  pc(y26['ad'], y26['n']), pc(y26['n7'], y26['n']), pc(y26['i48'], y26['n']),
                  y26['zd'], y26['c1'], y26['cp'],
                  labd['sp'], labd['rs'], maxr, labd['pv1'], labd['npev'],
                  labd['tt'], labd['t14']))
    print('OK afpd %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
