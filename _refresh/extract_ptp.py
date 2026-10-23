"""Extract the Permanent Transit Points payload (const PTP) from the IDIMS PTP coverage export.

The export is a tab-separated text file with an .xls name: one row per post per reporting day,
2016 to the export date. It is aggregated here to district x year, district x reporting month and
UC level, because the row detail carries post names and locations that do not belong on a public
site.

Month cells (d[i][4]) carry the same column order as the year cells so the renderer can index both
with one key list; their 'months' slot is always 1 because the cell IS one month. The section offers
months only inside a chosen year, so no cross-year month figure is published: a post that reported in
March 2024 and again in March 2025 is one post in each of those two cells, never one post for a
"March" summed over the window.

Held out of the payload deliberately:
  PostName, PostLocation       - they name fixed checkpoints; a public GitHub Pages site is not
                                 where they belong
  Coverage, Coverage_under5, Coverage_above5,
  OPVGiven, OPVUsed, OPVReturned, VacRecvd, aav_cards
                               - their units do not reconcile (see SOURCES.md), so nothing built
                                 on them is published until the report definition is confirmed

Every summed column adds one row per post per reporting day, so ZeroDose and the cross-border
columns are counts of reports, not of distinct children - a child found at a post twice in a week
is in the tally twice.

The export's own last TimeStamp bounds the reporting period: rows carrying a year/month after it
(2025/12 in the 20-Apr-2025 export, one MALAKAND row whose VaccinationDate is 24-Dec-2024) are a
source typo, and the month picker would otherwise offer a month that had not happened yet. They are
dropped and counted, never re-dated to the date the row actually carries. Rows with a valid year but
no month (Mth=0) are counted under their own reason instead of the tab-shifted one.

Post attributes: PostType is the value most often seen across the window; PostStatus and
SecurityRisk are taken from the post's most recent report, because "is it working now" is what the
section is asked to show and the window spans ten years.

Usage: python _refresh/extract_ptp.py [--source PATH] [--out PATH]
Prints one status line: OK ptp <json chars> <summary>
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import ptpgeo
import srcutil

DS = 'ptp'
UC_RE = re.compile(r'\d{8}$')

# Summed here from these source columns; 'rows'/'months'/'posts'/'ucs' are counted, not summed.
SUMCOLS = [('zd', 'ZeroDose'),
           ('cbu_in', 'CB_InUpto10'), ('cbu_out', 'CB_OutUpto10'),
           ('cbo_in', 'CB_InAbove10'), ('cbo_out', 'CB_OutAbove10'),
           ('nbv', 'new_born_vaccination'), ('teams', 'NoOfTeams'), ('sup', 'NoOfSupervisors'),
           ('expd', 'ExpChildrenDay')]
K = ['rows', 'months', 'posts', 'ucs'] + [k for k, _ in SUMCOLS]

# IDIMS keeps three district units broader than the dashboard's EPI split, so EPIM has no 1:1
# alias for them. Display name and division are the EPI family each one belongs to.
FALLBACK = {'KURRAM': ('Kurram', 'KOHAT'),
           'CHITRAL': ('Chitral (unsplit)', 'MALAKAND'),
           'WAZIR-S': ('South Waziristan (unsplit)', 'DIKHAN')}


def num(x):
    x = (x or '').strip().replace(',', '')
    try:
        return float(x)
    except ValueError:
        return None


def counter_mode(c):
    return c.most_common(1)[0][0] if c else None


def last_stamp(path):
    """The export's newest TimeStamp as yyyymm - no row can describe a period after it."""
    best = ''
    with open(path, 'r', encoding='utf-8', errors='replace', newline='') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            ts = (r.get('TimeStamp') or '').strip()
            if ts > best:
                best = ts
    if len(best) < 7 or not best[:4].isdigit() or not best[5:7].isdigit():
        raise SystemExit('ERR ptp no readable TimeStamp in %s - the reporting period cannot be '
                         'bounded' % path)
    return int(best[:4]) * 100 + int(best[5:7])


def load_lookups(repo):
    html = srcutil.read_text(os.path.join(repo, 'index.html'))
    epim = json.loads(dashpatch.get_payload(html, 'EPIM'))
    snd = json.loads(dashpatch.get_payload(html, 'SND'))
    ucpt = json.loads(dashpatch.get_payload(html, 'UCPT'))
    return ptpgeo.district_aliases(epim), ptpgeo.uc_district(snd), set(ucpt)


def resolve(d, aliases):
    """[display name, division] for an IDIMS district spelling, or None if it is unknown."""
    return aliases.get(d) or FALLBACK.get(d)


def collect(path, aliases, cut):
    zeros = dict.fromkeys([k for k, _ in SUMCOLS], 0.0)
    cells = defaultdict(lambda: dict(zeros))
    mcells = defaultdict(lambda: dict(zeros))
    posts_in = defaultdict(set)
    ucs_in = defaultdict(set)
    months_in = defaultdict(set)
    mposts_in = defaultdict(set)
    mucs_in = defaultdict(set)
    post = {}
    dropped = Counter()
    total = 0

    with open(path, 'r', encoding='utf-8', errors='replace', newline='') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            total += 1
            if (r.get('Province') or '').strip() != 'KP':
                dropped['not KP'] += 1
                continue
            u = (r.get('Ucode') or '').strip()
            d = (r.get('District') or '').strip()
            pid = (r.get('ID') or '').strip()
            dn = resolve(d, aliases)
            if not UC_RE.match(u) or not dn:
                dropped['no UC code, or district not in dashboard aliases'] += 1
                continue
            y, m = num(r.get('Yr')), num(r.get('Mth'))
            if y is None or m is None or not (2000 <= y <= 2100) or m < 0 or m > 12 \
                    or y != int(y) or m != int(m):
                dropped['unreadable year/month (tab-shifted rows)'] += 1
                continue
            y, m = int(y), int(m)
            if m == 0:
                dropped['no month given in the source (Mth=0)'] += 1
                continue
            if y * 100 + m > cut:
                dropped['year/month after the export timestamp (source typo)'] += 1
                continue

            key = (dn[0], y)
            mkey = (dn[0], y * 100 + m)
            vals = {k: (num(r.get(c)) or 0.0) for k, c in SUMCOLS}
            cells[key]['rows'] = cells[key].get('rows', 0) + 1
            mcells[mkey]['rows'] = mcells[mkey].get('rows', 0) + 1
            for k, v in vals.items():
                cells[key][k] += v
                mcells[mkey][k] += v
            months_in[key].add(m)
            ucs_in[key].add(u)
            mposts_in[mkey].add(pid)
            mucs_in[mkey].add(u)

            p = post.get(pid)
            if p is None:
                p = post[pid] = {'d': dn[0], 'dv': dn[1], 'ds': set(), 'types': Counter(),
                                 'stats': Counter(), 'risks': Counter(), 'uc': set(),
                                 'months': set(), 'last': 0, 'lstat': None, 'lrisk': None,
                                 'zd': 0.0, 'cbu': 0.0, 'rows': 0}
            p['ds'].add(dn[0])
            ym = y * 100 + m
            p['rows'] += 1
            p['months'].add(ym)
            p['uc'].add(u)
            p['zd'] += vals['zd']
            p['cbu'] += vals['cbu_in'] + vals['cbu_out']
            posts_in[key].add(pid)
            if ym >= p['last']:
                p['last'] = ym
                st = (r.get('PostStatus') or '').strip()
                rk = (r.get('SecurityRisk') or '').strip()
                if st and st != 'NULL':
                    p['lstat'] = st
                if rk and rk != 'NULL':
                    p['lrisk'] = rk
            for fld, col in (('types', 'PostType'), ('stats', 'PostStatus'), ('risks', 'SecurityRisk')):
                v = (r.get(col) or '').strip()
                if v and v != 'NULL':
                    p[fld][v] += 1

    # a post listed under two district spellings would be shown in the first one only, so the
    # whole district column would be wrong - stop instead of guessing.
    moved = sorted(pid for pid, p in post.items() if len(p['ds']) > 1)
    if moved:
        raise SystemExit('ERR ptp post IDs reported under more than one district: %s' % moved[:12])
    for p in post.values():
        del p['ds']
        p['type'] = counter_mode(p['types'])
        p['stat'] = p['lstat'] or counter_mode(p['stats'])
        p['risk'] = p['lrisk'] or counter_mode(p['risks'])
    return (cells, mcells, posts_in, ucs_in, months_in, mposts_in, mucs_in,
            post, dropped, total)


def build(path, repo):
    aliases, snd_uc, ucpt = load_lookups(repo)
    (cells, mcells, posts_in, ucs_in, months_in, mposts_in, mucs_in,
     post, dropped, total) = collect(path, aliases, last_stamp(path))
    if not cells or not post:
        raise SystemExit('ERR ptp nothing parsed from %s - header or units changed' % path)

    years = sorted({y for (_, y) in cells})
    dists = sorted({d for (d, _) in cells})
    yidx = {y: i for i, y in enumerate(years)}
    didx = {d: i for i, d in enumerate(dists)}
    raw_of = {}
    for d in dists:
        hit = [k for k, v in list(aliases.items()) + list(FALLBACK.items()) if v[0] == d]
        raw_of[d] = hit[0] if hit else d
    dv_of = {}
    for d in dists:
        dv_of[d] = next(p['dv'] for p in post.values() if p['d'] == d)

    def vals(c):
        return [c['rows'], c['months'], c['posts'], c['ucs']] + \
               [int(round(c[k])) for k, _ in SUMCOLS]

    for key, c in cells.items():
        c['months'] = len(months_in.get(key, ()))
        c['posts'] = len(posts_in.get(key, ()))
        c['ucs'] = len(ucs_in.get(key, ()))
    for mkey, c in mcells.items():
        c['months'] = 1
        c['posts'] = len(mposts_in[mkey])
        c['ucs'] = len(mucs_in[mkey])

    # the month cells must add back to the year cells, or the period filter on the page would be a
    # different dataset than the window view.
    bad = []
    per_year = defaultdict(int)
    for mkey in mcells:
        per_year[(mkey[0], mkey[1] // 100)] += 1
    for (dd, yy), c in cells.items():
        slots = [(dd, yy * 100 + m) for m in sorted(months_in[(dd, yy)])]
        miss = [s for s in slots if s not in mcells]
        if miss or per_year[(dd, yy)] != len(slots):
            bad.append('%s %d: %d year months against %d month cells, missing %s'
                       % (dd, yy, len(slots), per_year[(dd, yy)], miss))
            continue
        for k in ['rows'] + [x for x, _ in SUMCOLS]:
            got = sum(mcells[s][k] for s in slots)
            if abs(got - c[k]) > 1e-6:
                bad.append('%s %d: %s year %s against months %s' % (dd, yy, k, c[k], got))
        top = max((mcells[s]['posts'] for s in slots), default=0)
        tou = max((mcells[s]['ucs'] for s in slots), default=0)
        if top > c['posts'] or tou > c['ucs']:
            bad.append('%s %d: month posts/UCs %d/%d above the year %d/%d'
                       % (dd, yy, top, tou, c['posts'], c['ucs']))
    if bad:
        raise SystemExit('ERR ptp month cells do not reconcile: %s' % bad[:8])

    d = []
    for dd in dists:
        yc = [[yidx[yy], vals(cells[(dd, yy)])] for yy in years if (dd, yy) in cells]
        mc = [[yidx[mkey[1] // 100] * 12 + mkey[1] % 100 - 1, vals(mcells[mkey])]
              for mkey in sorted(k for k in mcells if k[0] == dd)]
        ps = [p for p in post.values() if p['d'] == dd]
        d.append([didx[dd], len({u for p in ps for u in p['uc']}), len(ps), yc, mc])

    # province totals: month cells summed against year cells against the kept rows
    kept = total - sum(dropped.values())
    for k in ['rows'] + [x for x, _ in SUMCOLS]:
        s_y = sum(c.get(k, 0) for c in cells.values())
        s_m = sum(c.get(k, 0) for c in mcells.values())
        if abs(s_y - s_m) > 1e-6:
            raise SystemExit('ERR ptp province total mismatch for %s: years %s months %s'
                             % (k, s_y, s_m))
    if sum(c['rows'] for c in mcells.values()) != kept:
        raise SystemExit('ERR ptp month cells do not add up to the kept rows')
    if sum(c['rows'] for c in cells.values()) != kept:
        raise SystemExit('ERR ptp year cells do not add up to the kept rows')

    by_uc = defaultdict(list)
    for p in post.values():
        for uc in p['uc']:
            by_uc[uc].append(p)
    # one UC code must sit in one district; if IDIMS ever disagrees, this payload would silently
    # attribute the whole UC to the first name, so it stops here instead.
    split = sorted(c for c, ps in by_uc.items() if len({p['d'] for p in ps}) > 1)
    if split:
        raise SystemExit('ERR ptp UC codes reported under more than one district: %s' % split[:12])
    u = []
    for code, ps in by_uc.items():
        u.append([code, didx[list({p['d'] for p in ps})[0]], len(ps),
                  len({m for p in ps for m in p['months']}),
                  int(round(sum(p['zd'] for p in ps))),
                  int(round(sum(p['cbu'] for p in ps))),
                  1 if code in ucpt else 0])
    u.sort(key=lambda r: (-r[4], -r[5]))

    all_uc = set(by_uc)  # by_uc is the local UC index; the loop var above is a post
    n = {'posts': len(post), 'ucs': len(all_uc), 'dists': len(dists), 'years': len(years),
         'read': total, 'kept': total - sum(dropped.values()),
         'uc_scope': len(all_uc & set(snd_uc)), 'uc_map': len(all_uc & ucpt)}
    for k, _ in SUMCOLS:
        n[k] = int(round(sum(c.get(k, 0.0) for c in cells.values())))
    types = sorted({p['type'] for p in post.values() if p['type']})
    stats = sorted({p['stat'] for p in post.values() if p['stat']})
    risks = sorted({p['risk'] for p in post.values() if p['risk']})
    # pd[i] = [posts by type, by last-reported status, by last-reported security risk]
    # for district i, each aligned to ty / st / rk.
    pd = []
    for dd in dists:
        ps = [p for p in post.values() if p['d'] == dd]
        ct, cs, cr = (Counter(p['type'] for p in ps if p['type']),
                      Counter(p['stat'] for p in ps if p['stat']),
                      Counter(p['risk'] for p in ps if p['risk']))
        pd.append([[ct.get(x, 0) for x in types], [cs.get(x, 0) for x in stats],
                   [cr.get(x, 0) for x in risks]])

    pkt = dashpatch.pkt_stamp(datetime.datetime.fromtimestamp(os.path.getmtime(path), dashpatch.PKT))
    ptp = {'src': os.path.basename(path), 'asof': pkt.split(' ')[0], 'gen': dashpatch.pkt_stamp(),
           'prov': 'KP', 'win': '%d-%d' % (years[0], years[-1]),
           'k': K, 'uk': ['code', 'd', 'posts', 'months', 'zd', 'cbu', 'onmap'],
           'yr': years, 'ds': dists, 'dr': [raw_of[x] for x in dists],
           'dv': [dv_of[x] for x in dists], 'ty': types, 'st': stats, 'rk': risks,
           'd': d, 'u': u, 'pd': pd, 'pdk': ['type', 'last status', 'last security risk'],
           'n': n, 'drop': dict(dropped),
           'hold': ['Coverage', 'Coverage_under5', 'Coverage_above5', 'OPVGiven', 'OPVUsed',
                    'OPVReturned', 'VacRecvd', 'aav_cards', 'PostName', 'PostLocation'],
           'note': 'aggregated to district x year and UC; post names and locations excluded; '
                   'summed columns count reports, not distinct children'}
    summary = ('%s rows read, %d kept, %d posts, %d UCs, %d districts, %d-%d, ZD found %s'
               % (format(total, ','), n['kept'], n['posts'], n['ucs'], len(dists),
                  years[0], years[-1], format(n['zd'], ',')))
    return ptp, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR ptp no PTP coverage export under %s' % cfg['auto'][DS]['roots'])
    ptp, summary = build(rec['path'], cfg['repo'])
    js = srcutil.dumps(ptp)
    srcutil.write_text(a.out or os.path.join(srcutil.OUT, 'ptp.json'), js)
    print('SRC ptp %s' % rec['path'])
    print('OK ptp %d %s' % (len(js), summary))
    if ptp['drop']:
        print('DROP ptp %s' % ptp['drop'])


if __name__ == '__main__':
    main()
