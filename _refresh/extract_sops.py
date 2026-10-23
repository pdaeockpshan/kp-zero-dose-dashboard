"""Extract the surveillance-operations payload (const SOPS) for the dashboard surveillance tab.

Usage: python _refresh/extract_sops.py [--av XLSX] [--zr XLSX] [--pn XLSX] [--vp XLSX] [--out PATH]
Prints: SRC lines + one status line `OK sops <json chars> <summary>` | ERR sops <reason>

Sources (newest of each under the configured roots, all manual EOC downloads):
  * `Active-visit (2026).xlsx`  - AFP active-surveillance visit tracker:
      - `Total (2)` : per district Exp/Done for weekly, fortnightly, monthly visits + overall.
      - `Monthly`   : per district Exp/Done/% for each calendar month.
      - `Weekly Analysis` : per district Exp/Done/% for each epidemiological week.
  * `Zero Reporting IDIMS -(2026).xlsx` - `ZeroReports_2026` is a tidy long table, one row per
      district per week: sites, expected reports, reports received, received in time.
  * `Pendency Status on -21-Oct-2026.xlsx` - three sheets (`Stool Specimen Validation`,
      `AFP Case Validation`, `GeoLocation`) of weekly snapshot blocks, three columns each:
      district, AFP cases so far that year, cases with that step completed, and the percent.
      Blocks run Feb-2022 to the newest snapshot. The other sheets in this workbook are
      per-record validation forms (officer names, designations, emails, EPIDs) and are
      deliberately not read.
  * `Zero_Report_Cases_ONLY.xlsx` - `Sumamy`: per district per week, AFP / measles / NNT case
      counts for 2026, with the three annual totals as the last columns.

Nothing here carries a name, address, CNIC, phone, email or EPID into the payload: district
and week/month labels and counts only. District spelling is normalised to the dashboard's own
`const SURV` keys. The active-visit and zero-report figures are cross-checked against the
official weekly log payload (SURVW `as` and `zr`) and the script aborts if either source
disagrees with the log for most districts.
"""
import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
from extract_surv import make_dkey, newest_like, rows_of  # shared spelling + sheet reader

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
NUM = (int, float)
Streams = ('stool', 'case', 'geo')
STREAM_SHEET = {'stool': 'Stool Specimen Validation', 'case': 'AFP Case Validation',
                'geo': 'GeoLocation'}


def num(v):
    return v if isinstance(v, NUM) and not isinstance(v, bool) else None


def pair(row, i):
    """Exp/Done from a 3-column block (Exp, Done, %), tolerating blanks."""
    e, d = num(row[i]) if i < len(row) else None, num(row[i + 1]) if i + 1 < len(row) else None
    return e, d


def wk2month(w, year=2026):
    """ISO week -> month, using the Thursday of that week (1 Jan 2026 is a Thursday)."""
    thu = dt.date(year, 1, 1) + dt.timedelta(days=7 * (int(w) - 1))
    return thu.month


def asof(iso):
    d = dt.date.fromisoformat(iso)
    return '%02d-%s-%d' % (d.day, MONTHS[d.month - 1], d.year)


def sheet_rows(wb, name, pad=6):
    return rows_of(wb, name, pad)


def district_rows(rows, hi, dkey):
    """[(surv_key, raw_row)] for every data row whose label column maps to a dashboard district."""
    out = []
    for r in rows[hi:]:
        if not r or not r[0]:
            continue
        k = dkey(str(r[0]).strip())
        if k:
            out.append((k, r))
    return out


# ------------------------------------------------------------------ active visits
def exp_blocks(rows, lab_row):
    """Columns where the sub-header says "Exp": each block is Exp / Done / % for one period.

    Row 1 of these sheets is empty, the period labels sit on row 2 and the Exp/Done/% sub-header
    on row 3, with district data from row 4 (0-based: 1, 2, 3).
    """
    sub = rows[2]
    starts = [i for i, v in enumerate(sub) if isinstance(v, str) and v.strip().lower() == 'exp']
    out = []
    for i in starts:
        lab = str(rows[lab_row][i]).strip() if i < len(rows[lab_row]) and rows[lab_row][i] else ''
        if not lab and i and rows[lab_row][i - 1]:
            lab = str(rows[lab_row][i - 1]).strip()
        out.append((i, lab))
    return out


def parse_av(path, dkey):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        # per district, per calendar month: Jan..Dec blocks (the "Total" block is the same as tp['mn'])
        rows = sheet_rows(wb, 'Monthly', 40)
        mb = exp_blocks(rows, 1)
        months = [(i, MONTHS.index(l)) for i, l in mb if l in MONTHS]
        tcol = [i for i, l in mb if l == 'Total']
        mon, mon_tot = {}, {}
        for k, r in district_rows(rows, 3, dkey):
            got = {mi: list(pair(r, i)) for i, mi in months}
            mon[k] = [got.get(mi, [None, None]) for mi in range(12)]
            if tcol:
                mon_tot[k] = pair(r, tcol[0])
        # KP weekly + fortnightly series (sum of districts), keyed by epidemiological week
        series = {}
        for sh, kind in (('Weekly Analysis', 'wk'), ('Fortnightly', 'fn')):
            rows = sheet_rows(wb, sh, 40)
            acc = {}
            for i, lab in exp_blocks(rows, 1):
                m = re.match(r'(?i)Wk#(\d+)(?:-(\d+))?$', lab)
                if not m:
                    continue
                w = int(m.group(1))
                for k, r in district_rows(rows, 3, dkey):
                    e, d = pair(r, i)
                    a = acc.setdefault(w, [0, 0])
                    a[0] += e or 0
                    a[1] += d or 0
            order = sorted(acc)
            while len(order) > 1 and not any(acc[order[-1]]):  # trailing rows carry no expected visits
                order.pop()
            series[kind] = (order, [acc[w] for w in order])
        # per district totals: weekly / fortnightly / monthly / overall
        rows = sheet_rows(wb, 'Total (2)', 45)
        blocks = exp_blocks(rows, 1)
        want = {'weekly': 'we', 'fortnightly': 'fn', 'monthly': 'mn', 'total': 'al'}
        at = {want[l.lower()]: i for i, l in blocks if l.lower() in want}
        if set(want.values()) - set(at):
            raise SystemExit('ERR sops Total (2): blocks not found: %s' % sorted(at.values()))
        tp = {k: {kk: pair(r, at[kk]) for kk in ('we', 'fn', 'mn', 'al')}
              for k, r in district_rows(rows, 3, dkey)}
        kp = {kk: [sum(v[kk][0] or 0 for v in tp.values()), sum(v[kk][1] or 0 for v in tp.values())]
              for kk in ('we', 'fn', 'mn', 'al')}
        return {'mon': mon, 'mon_tot': mon_tot, 'wk': series['wk'][1], 'wlabel': series['wk'][0],
                'fwk': series['fn'][1], 'fwlabel': series['fn'][0],
                'tp': tp, 'kp': kp}
    finally:
        wb.close()


# ------------------------------------------------------------------ zero reporting
def parse_zr(path, dkey):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = sheet_rows(wb, 'ZeroReports_2026', 4000)
        hdr = [str(v).strip() for v in rows[0] if v]
        want = ['Province', 'District', 'Week', 'Year', 'Total_Sites',
                'Total_Expected', 'Total_Received', 'Received_Intime']
        if hdr != want:
            raise SystemExit('ERR sops ZeroReports_2026 header changed: %s' % hdr)
        d, weeks, sites = {}, set(), {}
        for r in rows[1:]:
            if not r or not r[1]:
                continue
            k = dkey(str(r[1]).strip())
            w, yr = num(r[2]), num(r[3])
            if not k or w is None or yr != 2026:
                continue
            w = int(w)
            d.setdefault(k, {})[w] = [num(r[5]) or 0, num(r[6]) or 0, num(r[7]) or 0]
            sites[k] = max(sites.get(k, 0), num(r[4]) or 0)
            weeks.add(w)
        wl = sorted(weeks)
        dd = {k: [d[k].get(w, [0, 0, 0]) for w in wl] for k in d}
        kp = [[sum(d[k].get(w, [0, 0, 0])[j] for k in d) for j in (0, 1, 2)] for w in wl]
        tot = {k: [sum(x[j] for x in dd[k]) for j in (0, 1, 2)] for k in dd}
        mon = {}
        for k in dd:
            m = [[0, 0, 0] for _ in range(12)]
            for i, w in enumerate(wl):
                mi = min(11, max(0, wk2month(w) - 1))
                for j in (0, 1, 2):
                    m[mi][j] += dd[k][i][j]
            mon[k] = m
        return {'w': wl, 'd': dd, 'kp': kp, 'tot': tot, 'sites': sites, 'mon': mon}
    finally:
        wb.close()


# ------------------------------------------------------------------ pendency tracker
def snap_date(label):
    m = re.search(r'(\d{1,2})[\s-]*([A-Za-z]{3})[a-z]*[\s-]*(\d{4})', str(label))
    if not m:
        return None
    mo = MONTHS.index(m.group(2).capitalize()) + 1
    try:
        return dt.date(int(m.group(3)), mo, int(m.group(1)))
    except ValueError:
        return None


def den_title(rows, i):
    """Label of a block's denominator column - it was re-worded in 2026, so captions must follow it."""
    for r in rows[2:4]:
        j = i + 1
        if j < len(r) and isinstance(r[j], str) and r[j].strip():
            return r[j].strip()
    return ''


def block_titles(rows, i):
    """Header text a block carries in its first columns; newer snapshots shift it one row up."""
    out = []
    for r in rows[2:4]:
        for j in (i, i + 1, i + 2):
            if j < len(r) and isinstance(r[j], str) and r[j].strip():
                out.append(r[j].strip())
    return out


def parse_pn(path, dkey):
    """Snapshot blocks are 4 columns wide: District | AFP cases | cases completed | percent.

    Each block is a cumulative-within-year tally as at its status date, so one point per calendar
    month (the latest block in that month) is the trend the tracker supports. Blocks that cannot
    be read as a rate - see the filter below - are dropped and counted, never rescaled.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        out, latest = {}, {}
        for st, sh in STREAM_SHEET.items():
            rows = sheet_rows(wb, sh, 40)
            h1 = rows[0]
            starts = [i for i, v in enumerate(h1) if isinstance(v, str) and 'status' in v.lower()]
            if not starts:
                raise SystemExit('ERR sops %s: no snapshot blocks found' % sh)
            bad = [i for i in starts
                   if not any(t.lower() == 'district' for t in block_titles(rows, i))]
            if bad:
                raise SystemExit('ERR sops %s: %d blocks not laid out as district/cases/done '
                                 '(%s)' % (sh, len(bad), bad[:4]))
            best, per, over = {}, {}, [0]
            for i in starts:
                sd = snap_date(h1[i])
                if not sd:
                    continue
                key = (sd.year, sd.month)
                if key in best and best[key][0] > sd:
                    continue  # keep the right-most block for the month, incl. duplicate dates
                acc, tot = {}, [0, 0]
                pb = pk = 0
                for r in rows[5:]:
                    if i + 2 >= len(r) or not r[i]:
                        continue
                    k = dkey(str(r[i]).strip())
                    c, dn = num(r[i + 1]), num(r[i + 2])
                    if not k or c is None:
                        continue
                    if dn is not None and c is not None and dn > c:
                        over[0] += 1  # 2022 blocks back-count validations onto a smaller case tally
                    pv = num(r[i + 3]) if i + 3 < len(r) else None
                    if pv is not None and c:  # the sheet's own percent column proves the geometry
                        if abs(pv - (dn or 0) / c) > 0.005:
                            pb += 1
                        else:
                            pk += 1
                    acc[k] = [int(c), int(dn or 0)]
                    tot[0] += int(c)
                    tot[1] += int(dn or 0)
                if len(acc) < 20:
                    raise SystemExit('ERR sops %s: snapshot %s matched only %d districts'
                                     % (sh, h1[i], len(acc)))
                best[key] = (sd, acc, tot, den_title(rows, i))
                per[key] = (pb, pk)
            order = sorted(best)
            pok = sum(v[1] for v in per.values())
            prb = sum(v[0] for v in per.values())
            stale = [k for k, (pb, pk) in sorted(per.items()) if pb]
            if pok < 500 or prb > 0.05 * (pok + prb):
                raise SystemExit('ERR sops %s: block geometry unproven, percent column matched %d/%d '
                                 'cells' % (sh, pok, pok + prb))
            # A snapshot is only usable once its own year has reset. Two source faults make some
            # blocks unchartable, and they are dropped rather than silently re-scaled:
            #   - January (sometimes February) still carries the previous December's tally, so the
            #     rate is computed against a case base from the year before;
            #   - a rate above 100% later than February means that year's base is broken all year
            #     (2022 stool validations count ~146% of that year's cases), so the year goes.
            ymax = {}
            for k in order:
                if k[1] >= 3:  # the settled part of the year; Jan/Feb may still carry the old tally
                    ymax[k[0]] = max(ymax.get(k[0], 0), best[k][2][0])
            badyr = set(k[0] for k in order if k[1] >= 3
                        and best[k][2][0] and best[k][2][1] / best[k][2][0] > 1.02)
            keep, drop = [], {}
            for k in order:
                tot = best[k][2]
                prev = ymax.get(k[0] - 1, 0)
                if k[0] in badyr:
                    drop['%d back-counted' % k[0]] = drop.get('%d back-counted' % k[0], 0) + 1
                elif k[1] <= 2 and prev and tot[0] > 0.9 * prev:
                    drop['carries %d tally' % (k[0] - 1)] = drop.get('carries %d tally' % (k[0] - 1), 0) + 1
                else:
                    keep.append(k)
            if not keep or keep[-1] != order[-1]:
                raise SystemExit('ERR sops %s: newest snapshot %s was dropped, nothing to report'
                                 % (sh, order[-1]))
            yend = {}
            for k in keep:
                if k[1] >= 10 and (k[0] not in yend or k > yend[k[0]]):
                    yend[k[0]] = k
            print('CHK pn %-22s %2d districts x %d usable monthly snapshots (%d blocks dropped: %s), '
                  '%d/%d cells match their own %% column, %d cells count more done than cases, '
                  'stale %% cells in %s'
                  % (sh, len(best[keep[-1]][1]), len(keep), len(order) - len(keep),
                     ', '.join('%s x%d' % (kk, vv) for kk, vv in sorted(drop.items())) or 'none',
                     pok, pok + prb, over[0],
                     ', '.join('%04d-%02d' % k for k in stale) or 'none'))
            dens = []
            for k in keep:
                if best[k][3] and best[k][3] not in dens:
                    dens.append(best[k][3])
            out[st] = {'at': ['%04d-%02d' % k for k in keep],
                       'd': [list(best[k][2]) for k in keep],
                       'dates': [best[k][0].isoformat() for k in keep],
                       'dens': dens,
                       'yend': {'%d' % y: [best[yend[y]][0].isoformat(), list(best[yend[y]][2])]
                                for y in sorted(yend)}}
            latest[st] = {'at': best[keep[-1]][0].isoformat(), 'd': best[keep[-1]][1]}
        return out, latest
    finally:
        wb.close()


# ------------------------------------------------------------------ VPD weekly cases
def parse_vp(path, dkey):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = sheet_rows(wb, 'Sumamy', 45)
        wrow, lab = rows[3], rows[4]
        weeks, tots = [], {}
        for i, v in enumerate(wrow):
            if v is None or i == 0:
                continue
            h = str(v).strip()
            if h.lower().startswith('total '):
                tots[h.lower()] = i
                continue
            try:
                w = int(h)
            except ValueError:
                continue
            if str(lab[i]).strip().lower().startswith('afp'):
                weeks.append((i, w))
        if not weeks:
            raise SystemExit('ERR sops Sumamy: no AFP/Measles/NNT week blocks found')
        want = {'total afp cases': 0, 'total measles cases': 1, 'total nnt cases': 2}
        if set(want) - set(tots):
            raise SystemExit('ERR sops Sumamy: annual total columns missing %s'
                             % sorted(set(want) - set(tots)))
        d, totcols = {}, {}
        for k, r in district_rows(rows, 5, dkey):
            d[k] = [[int(num(r[i]) or 0), int(num(r[i + 1]) or 0), int(num(r[i + 2]) or 0)]
                    for i, _ in weeks]
            totcols[k] = [int(num(r[tots[h]]) or 0) for h in sorted(want, key=want.get)]
        wl = [w for _, w in weeks]
        kp = [[sum(d[k][i][j] for k in d) for j in (0, 1, 2)] for i in range(len(wl))] if d else []
        return {'w': wl, 'd': d, 'kp': kp, 'tot': totcols}
    finally:
        wb.close()


# ------------------------------------------------------------------ cross-checks
def survw_indicators(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SURVW = ')
    if i < 0:
        return {}
    payload = json.loads(s[i + len('const SURVW = '):s.find('\n', i)].rstrip().rstrip(';'))
    K = payload['sm']['k']
    return {'as': K.index('as'), 'zr': K.index('zr'),
            'd': payload['sm']['d'], 'kp': payload['sm'].get('kp'),
            'asof': payload.get('asof'), 'wmax': None}


def check(name, pairs, idx, tol, worst_ok=0.5):
    """Compare payload-derived % against the weekly log's own %, district by district."""
    bad = []
    for k, got in pairs:
        want = idx(k)
        if want is None:
            continue
        if abs(got - want) > tol:
            bad.append((k, round(got, 1), round(want, 1)))
    print('CHK %-16s %d districts compared, %d outside %g pp' % (name, len(pairs), len(bad), tol))
    if bad:
        print('    worst: ' + ', '.join('%s %.1f vs log %.1f' % b for b in
                                        sorted(bad, key=lambda x: -abs(x[1] - x[2]))[:6]))
    if len(bad) > worst_ok * len(pairs):
        raise SystemExit('ERR sops %s disagrees with the weekly log for most districts' % name)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--av')
    ap.add_argument('--zr')
    ap.add_argument('--pn')
    ap.add_argument('--vp')
    ap.add_argument('--source', help='accepted for refresh.py run; routed to a slot by filename')
    ap.add_argument('--out')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    repo = cfg['repo']
    entry = (cfg.get('auto') or {}).get('sops') or (cfg.get('manual') or {}).get('sops') or {}
    roots = entry.get('roots') or [r'C:\Users\HD\Downloads']
    dists, dkey = make_dkey(repo)

    def pick(arg, pat):
        if arg:
            return arg
        if a.source and fnmatch.fnmatch(os.path.basename(a.source), pat):
            return a.source
        e = dict(entry)
        e['roots'] = roots
        e['patterns'] = [pat]
        e['exclude'] = ['~$*']
        f = newest_like(e, pat)
        if not f:
            raise SystemExit('ERR sops no source matching %r' % pat)
        return f

    av, zr, pn, vp = (pick(a.av, 'Active-visit (20??).xlsx'), pick(a.zr, 'Zero Reporting IDIMS*.xlsx'),
                      pick(a.pn, 'Pendency Status on *.xlsx'), pick(a.vp, 'Zero_Report_Cases_ONLY.xlsx'))
    for p in (av, zr, pn, vp):
        print('SRC %s' % p)

    AV = parse_av(av, dkey)
    ZR = parse_zr(zr, dkey)
    PN, LAST = parse_pn(pn, dkey)
    VP = parse_vp(vp, dkey)

    # geography coverage: which district rows did each source actually carry
    seen = {'av': set(AV['tp']), 'zr': set(ZR['d']), 'vp': set(VP['d'])}
    for st in Streams:
        seen['pn' + st] = set(LAST[st]['d'])
    print('GEO ' + ' | '.join('%s %d' % (k, len(v)) for k, v in sorted(seen.items())))
    if len(seen['av']) < 20 or len(seen['zr']) < 20:
        raise SystemExit('ERR sops district mapping lost rows (av %d, zr %d)'
                         % (len(seen['av']), len(seen['zr'])))

    # ---- internal consistency: each sheet has to add up to its own totals
    bad = [k for k, v in AV['tp'].items()
           if any((v['we'][j] or 0) + (v['fn'][j] or 0) + (v['mn'][j] or 0) != (v['al'][j] or 0)
                  for j in (0, 1))]
    print('CHK av composition   %d districts, %d where weekly+fortnightly+monthly != total'
          % (len(AV['tp']), len(bad)))
    if bad:
        raise SystemExit('ERR sops Active-visit totals do not add up: %s' % bad[:6])
    bad = [k for k in AV['tp']
           if any(sum(x[j] or 0 for x in AV['mon'][k]) != (AV['mon_tot'].get(k, [0, 0])[j] or 0)
                  for j in (0, 1))]
    print('CHK av monthly       %d districts, %d whose Jan-Dec blocks miss the sheet Total'
          % (len(AV['mon']), len(bad)))
    if bad:
        raise SystemExit('ERR sops Active-visit monthly blocks do not add up: %s' % bad[:6])
    for kind, lab in (('wk', 'we'), ('fwk', 'fn')):
        se = sum(x[0] for x in AV[kind])
        st = sum(x[1] for x in AV[kind])
        ok = se == AV['kp'][lab][0] and st == AV['kp'][lab][1]
        print('CHK av %-14s %d periods, exp %s / done %s vs totals %s / %s -> %s'
              % (kind + ' vs totals', len(AV[kind]), se, st, AV['kp'][lab][0], AV['kp'][lab][1],
                 'ok' if ok else 'MISMATCH'))
        if not ok:
            raise SystemExit('ERR sops %s sheet does not sum to the district totals' % lab)
    # zero reports: received-in-time can never exceed reports received, nor the site-weeks due
    zbad = [k for k, rws in ZR['d'].items()
            if any(x[2] > x[1] or x[1] > ZR['sites'][k] * len(ZR['w']) or x[0] > ZR['sites'][k] * len(ZR['w'])
                   for x in rws)]
    print('CHK zr bounds        %d districts, %d outside 0 <= in-time <= received <= sites x weeks'
          % (len(ZR['d']), len(zbad)))
    if zbad:
        raise SystemExit('ERR sops ZeroReports_2026 values are not nested: %s' % zbad[:6])

    # ---- against the official weekly log. The log's own measures are close at province level
    # but use different denominators per district, so only the KP figure is used as a gate.
    SW = survw_indicators(repo)
    if SW:
        kp_as, kp_zr = (SW['kp'][SW['as']], SW['kp'][SW['zr']]) if SW.get('kp') else (None, None)
        ae, ad = AV['kp']['al']
        avp = [('KP', 100.0 * ad / ae)] if ae and kp_as is not None else []
        check('active visits vs log', avp, lambda k: kp_as, 6.0)
        ze = sum(x[0] for x in ZR['kp'])
        print('CMP zero reports     IDIMS %d/%d received = %.1f%% of expected, %.1f%% reported in '
              'time; weekly log %s "Zero-report timeliness %%" = %.1f%% (different denominators, '
              'both are shown separately)'
              % (sum(x[1] for x in ZR['kp']), ze,
                 100.0 * sum(x[1] for x in ZR['kp']) / ze if ze else 0.0,
                 100.0 * sum(x[2] for x in ZR['kp']) / ze if ze else 0.0,
                 SW.get('asof'), kp_zr if kp_zr is not None else 0.0))

    # VPD weekly sums back to the sheet's own annual totals
    bad = [k for k in VP['d']
           if any(sum(x[j] for x in VP['d'][k]) != VP['tot'].get(k, [-1, -1, -1])[j] for j in (0, 1, 2))]
    print('CHK vpd totals     %d districts, %d that do not sum back' % (len(VP['d']), len(bad)))
    if len(bad) > 2:
        raise SystemExit('ERR sops weekly case counts disagree with the workbook totals: %s'
                         % bad[:8])

    payload = {
        'asof': asof(LAST['stool']['at']),
        'src': {'av': os.path.basename(av), 'zr': os.path.basename(zr),
                'pn': os.path.basename(pn), 'vp': os.path.basename(vp)},
        'av': {'w': AV['wlabel'], 'wk': AV['wk'], 'fw': AV['fwlabel'], 'fwk': AV['fwk'],
               'mon': AV['mon'], 'mt': AV['mon_tot'], 'tp': AV['tp'], 'kp': AV['kp']},
        'zr': {'w': ZR['w'], 'd': ZR['d'], 'kp': ZR['kp'], 'tot': ZR['tot'], 'sites': ZR['sites'],
               'mon': ZR['mon']},
        'pn': PN,
        'last': {st: {'at': asof(LAST[st]['at']), 'd': LAST[st]['d']} for st in Streams},
        'vp': {'w': VP['w'], 'kp': VP['kp'], 'tot': VP['tot']},
    }
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'sops.json')
    if not a.dry:
        srcutil.write_text(dest, js)
    av_kp = AV['kp']['al']
    z_kp = [sum(x[j] for x in ZR['kp']) for j in (0, 1, 2)]
    l26 = {st: LAST[st]['d'] for st in Streams}
    pc = lambda a_, b_: round(100.0 * a_ / b_, 1) if b_ else 0.0
    for st in Streams:
        print('YEND %-6s %s' % (st, ', '.join(
            '%s %s%% (%s/%s)' % (y, pc(v[1][1], v[1][0]), '{:,}'.format(int(v[1][1])),
                                 '{:,}'.format(int(v[1][0])))
            for y, v in sorted(PN[st]['yend'].items()))))
    print('OK sops %d %d active visits %s/%s done (%s%%) across %d districts; '
          '%d zero-report rows over weeks %d-%d, %d/%s received (%s%%), %s%% in time; '
          'pendency to %s: stool %s%% (%s/%s), case validation %s%% (%s/%s), geolocation %s%%; '
          'VPD 2026 wk1-%d: %d AFP / %d measles / %d NNT in %d districts; snapshots %s'
          % (len(js), av_kp[1], '{:,}'.format(int(av_kp[1])), '{:,}'.format(int(av_kp[0])),
             pc(av_kp[1], av_kp[0]), len(AV['tp']),
             len(ZR['w']), ZR['w'][0], ZR['w'][-1], z_kp[1], '{:,}'.format(int(z_kp[0])),
             pc(z_kp[1], z_kp[0]), pc(z_kp[2], z_kp[0]),
             payload['asof'],
             pc(sum(v[1] for v in l26['stool'].values()), sum(v[0] for v in l26['stool'].values())),
             '{:,}'.format(int(sum(v[1] for v in l26['stool'].values()))),
             '{:,}'.format(int(sum(v[0] for v in l26['stool'].values()))),
             pc(sum(v[1] for v in l26['case'].values()), sum(v[0] for v in l26['case'].values())),
             sum(v[1] for v in l26['case'].values()), sum(v[0] for v in l26['case'].values()),
             pc(sum(v[1] for v in l26['geo'].values()), sum(v[0] for v in l26['geo'].values())),
             ZR['w'][-1], sum(x[0] for x in VP['kp']), sum(x[1] for x in VP['kp']),
             sum(x[2] for x in VP['kp']), len(VP['d']),
             ', '.join('%s %d' % (st, len(PN[st]['at'])) for st in Streams)))


if __name__ == '__main__':
    main()
