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

PII: the case DB carries names and addresses. This extractor reads only dates,
geography, dose history and lab-result codes, and writes district-level
aggregates - the dashboard is a public GitHub Pages site.

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
          "yrs":[2022..2026],"k":[..],
          "y":{year:[n,ad,n7,i48,zd,du,c1,cw,cp,c3]},
          "mon26":[12],
          "d":{district:[n,ad,n7,i48,zd]},
          "lab":{"sm":[12],"rm":[12],"sp":..,"rs":..,"pv1":..,"npev":..,
                 "tt":..,"t14":..}}
"""
import argparse
import datetime
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'afpd'
YRS = [2022, 2023, 2024, 2025, 2026]
CK = ['n', 'ad', 'n7', 'i48', 'zd', 'du', 'c1', 'cw', 'cp', 'c3']
DK = ['n', 'ad', 'n7', 'i48', 'zd']
RENAME = {'WAZIR-S LOWER': 'WAZIR-S Lower', 'WAZIR-S UPPER': 'WAZIR-S Upper'}


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
    rev.update({'WAZIRSL': 'WAZIR-S Lower', 'WAZIRSU': 'WAZIR-S Upper'})
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


def build_case(path, repo):
    dists, dkey = surv_scope(repo)
    y = {yr: dict.fromkeys(CK, 0) for yr in YRS}
    mon = [0] * 12
    d = {k: dict.fromkeys(DK, 0) for k in dists}
    maxon = maxen = None
    skip = unknown = 0
    wpv = {}
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
        a = y[yr]
        a['n'] += 1
        onset = pdate(r['DONSET'])
        notif = pdate(r['DNOT'])
        inves = pdate(r['DOI'])
        if onset:
            if maxon is None or onset > maxon:
                maxon = onset
            if notif and 0 <= (notif - onset).days <= 7:
                a['n7'] += 1
            if inves and notif and 0 <= (inves - notif).days <= 2:
                a['i48'] += 1
        if r['ADEQ'] == 'ADEQ':
            a['ad'] += 1
        do = num(r['DOSES'])
        if do is None:
            a['du'] += 1
        elif do == 0:
            a['zd'] += 1
        cls = r['CLASS']
        if cls == '3':
            a['c3'] += 1
        elif cls in ('1', '2'):
            a['cw'] += 1
            if cls == '1':
                a['c1'] += 1
        else:
            a['cp'] += 1
        en = pdate(r['DENTER'])
        if en and (maxen is None or en > maxen):
            maxen = en
        if yr == 2026:
            if onset:
                mon[onset.month - 1] += 1
            k = dkey(r['DISTRICT'])
            if k is None:
                unknown += 1
                continue
            row = d[k]
            row['n'] += 1
            if r['ADEQ'] == 'ADEQ':
                row['ad'] += 1
            if onset and notif and 0 <= (notif - onset).days <= 7:
                row['n7'] += 1
            if onset and notif and inves and 0 <= (inves - notif).days <= 2:
                row['i48'] += 1
            if do == 0:
                row['zd'] += 1
            if cls == '1':
                wpv[k] = wpv.get(k, 0) + 1
    if maxon is None or maxen is None:
        raise SystemExit('ERR afpd no KP rows with onset/entry dates')
    empty = [k for k in dists if d[k]['n'] == 0]
    if empty:
        raise SystemExit('ERR afpd no 2026 cases for %s' % empty)
    if unknown:
        raise SystemExit('ERR afpd %d rows with a district outside the SURV scope' % unknown)
    if sum(mon) != sum(d[k]['n'] for k in dists) or sum(mon) != y[2026]['n']:
        raise SystemExit('ERR afpd 2026 monthly %d != district %d != year %d'
                         % (sum(mon), sum(d[k]['n'] for k in dists), y[2026]['n']))
    for yr in YRS:
        if y[yr]['n'] < 1000:
            raise SystemExit('ERR afpd only %d cases in %d' % (y[yr]['n'], yr))
    return y, mon, d, wpv, maxon, maxen, skip


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
            if c and rr and rr >= c:
                tt.append((rr - c).days)
    if maxc is None or maxr is None:
        raise SystemExit('ERR afpd no 2026 lab specimens with collection/report dates')
    tt.sort()
    med = tt[len(tt) // 2] if tt else None
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

    y, mon, d, wpv, maxon, maxen, skip = build_case(afp, cfg['repo'])
    labd, maxc, maxr = build_lab(lab)

    afpd = {'src': os.path.basename(afp), 'asof': maxen.strftime('%d-%b-%Y'),
            'onset': maxon.isoformat(),
            'lsrc': os.path.basename(lab), 'lcoll': maxc.isoformat(), 'lres': maxr.isoformat(),
            'yrs': YRS, 'k': CK,
            'y': {str(yr): [y[yr][k] for k in CK] for yr in YRS},
            'mon26': mon, 'd': {k: [d[k][x] for x in DK] for k in d},
            'lab': labd}
    js = srcutil.dumps(afpd)
    dest = a.out or os.path.join(srcutil.OUT, 'afpd.json')
    srcutil.write_text(dest, js)
    y26 = y[2026]
    pc = lambda a_, b_: round(100.0 * a_ / b_, 1) if b_ else 0.0
    summary = ('%d KP AFP cases %d-%d, %d in 2026 (onset to %s, entered to %s): adequacy %s%%, '
               'notified <7d %s%%, investigated <48h %s%%, %d zero-dose, %d WPV1, %d pending; '
               'lab 2026: %d specimens, %d results (to %s), %d PV1 / %d NPEV isolations, '
               'median turnaround %dd (%s%% within 14d)'
               % (y[2022]['n'] + y[2023]['n'] + y[2024]['n'] + y[2025]['n'] + y[2026]['n'],
                  YRS[0], YRS[-1], y26['n'], maxon, maxen,
                  pc(y26['ad'], y26['n']), pc(y26['n7'], y26['n']), pc(y26['i48'], y26['n']),
                  y26['zd'], y26['c1'], y26['cp'],
                  labd['sp'], labd['rs'], maxr, labd['pv1'], labd['npev'],
                  labd['tt'], labd['t14']))
    print('OK afpd %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
