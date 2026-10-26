"""Extract the Permanent Transit Points payload (const PTP) from the IDIMS PTP coverage export.

The export is a tab-separated text file with an .xls name: one row per post per reporting day,
2016 to the export date. It is aggregated here to district x year, district x reporting month and
UC level, because the row detail carries post names and locations that do not belong on a public
site.

Month cells (d[i][4]) carry the same column order as the year cells so the renderer can index both
with one key list; their 'months' slot is always 1 because the cell IS one month. The section offers
months only inside a chosen year, so no cross-year month figure is published: a post that reported in
March 2024 and again in March 2025 is one post in each of those two cells, never one post for a
"March" summed over the window. UC rows carry the same two cell lists in u[i][7] and u[i][8], in the
shorter uq column order, so the UC table can follow the period pick too.

Post identity: the key is Site_ID, falling back to ID. From the 23-Oct-2026 export onwards ID is a
per-report-row id (263,024 rows, 263,024 distinct IDs) and the post number moved to Site_ID (1,150
of them); the older exports have no Site_ID column and their ID is exactly that post number - the
20-Apr-2025 export's IDs 805 and 782 are the current export's Site_IDs 805 and 782, with the same
UC codes and post names, so the two spellings share one key without splitting any post.

District spelling: the same export also upper-cases two district units it used to write mixed case
('WAZIR-S LOWER', 'WAZIR-S UPPER' against alias 'WAZIR-S Lower'). Aliases are therefore matched
case-insensitively, but only where the lower-cased spelling resolves to one display district - 20,539
rows hang on those two spellings, and an exact-match lookup silently drops them.

no_of_refusals is summed, but it is non-zero only from reft onwards (2026 in the 24-Oct-2026 export;
the column exists and is blank-or-zero before that). reft is published so the UI can show a dash
rather than a false zero for the earlier years.

Held out of the payload deliberately:
  PostName, PostLocation, HealthFacility, Remarks
                               - they name fixed checkpoints, staff and free text; a public GitHub
                                 Pages site is not where they belong
  Coverage_under5, Coverage_above5
                               - the owner's workbook defines the same family without them, and the
                                 columns are filled for at most 7.1% of Coverage in any year
                                 (0.0% for 2016-2022), so they carry no measure
  VacRecvd, aav_cards          - populated 2021-2025 then blank/6 rows in 2026: a column the panel
                                 stopped filling, and a published zero would read as "no vaccine
                                 received"

Coverage, OPVUsed, OPVGiven and OPVReturned ARE published now, from covy (2022) onwards only. The
owner's own workbook (PTP-STP Coverage and Compliance.twbx, "Joint Database/3. HRMP") supplies the
definition: Wastage % = 1-(SUM([Coverage])/SUM([OPVUsed]) * 1), so Coverage counts children covered
and OPVUsed counts doses actually used, and OPVGiven = OPVUsed + OPVReturned (true in 261,710 of
that file's 261,923 rows). Nothing in this repo invents the ratio.

It is published from 2022 because it does not reconcile before it, and the failure is not an age-mix
artefact - the 0-5Years rows, which are 89-98% of every year, give the same answer as all rows:
wastage of -570.6% (2016), -360.7, -424.0, -169.8, -63.3, -18.8 (2021), then +2.7 (2022), +6.6,
+6.9, +7.2, +8.4 (2026). A Coverage above OPVUsed is arithmetically impossible under that
definition, so the earlier years are published but dashed, and cwaste carries the year table that
shows why. The cross-check that licenses the whole family: KP 2026 wastage is +7.40% on this export
(24-Oct pull) against +7.38% on the owner's workbook (06-Oct pull).

Do not divide anything by expd. Summed Coverage over summed ExpChildrenDay is 1.58 all-time and 0.63
in 2026, so the panel's "expected child-days" is not a population denominator however the column
reads. ExpChildrenDay is published as the panel's own exposure figure and never as a denominator.

The three class cuts (ty/dur/age) classify the reporting ROW as the row states it, which is why each
one closes on the province total. That is different from pd, which attributes a POST to its
most-often-seen type over ten years: a post that changed type is in one pd bucket and in two class
cells. PostDuration values are the operational strategies the section is asked about - Seasonal,
Permanent, Temporary, EID-RAMAZAN, the six TTP Ring strategy belts, VRC/Holding Centers.

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
# The last four are the Coverage/OPV family the owner's workbook defines; they are in every cell so
# the period filter works on them too, but covy says from which year the UI may print them.
SUMCOLS = [('zd', 'ZeroDose'),
           ('cbu_in', 'CB_InUpto10'), ('cbu_out', 'CB_OutUpto10'),
           ('cbo_in', 'CB_InAbove10'), ('cbo_out', 'CB_OutAbove10'),
           ('nbv', 'new_born_vaccination'), ('teams', 'NoOfTeams'), ('sup', 'NoOfSupervisors'),
           ('expd', 'ExpChildrenDay'), ('ref', 'no_of_refusals'),
           ('cov', 'Coverage'), ('used', 'OPVUsed'), ('given', 'OPVGiven'), ('ret', 'OPVReturned')]
K = ['rows', 'months', 'posts', 'ucs'] + [k for k, _ in SUMCOLS]
# UC cells keep their own short order, exactly as they are built below: [posts, months, rows, zd, cbu].
UQ = ['posts', 'months', 'rows', 'zd', 'cbu']
# First year the Coverage/OPV family reconciles - see the module docstring for the year table.
COVY = 2022
# Measures carried on a class cell. The class of the ROW, not of the post: see the docstring.
MK = ['rows', 'cov', 'used', 'zd']
# axis id, source column, payload key for its value list, payload key for its cells
CLASSES = [('ty', 'PostType', 'cty', 'td'),
           ('dur', 'PostDuration', 'cdur', 'dd'),
           ('age', 'AgeGroup', 'cag', 'ad')]
UNSTATED = 'Not stated'

# district (IDIMS spelling) -> corridor, exactly as the owner classifies it in
# PTP-STP Coverage and Compliance.twbx. Constant per district in that file - no district carries two.
# The Hazara divisions are blank there, which is a statement about the corridor programme, not a
# missing value, so they publish as "Not on a corridor". A spelling not in this map publishes as
# Not stated and is named on the refresh log, so a renamed district unit cannot quietly vanish.
CORRIDOR = {'BANNU': 'Central Corridor', 'DIKHAN': 'Central Corridor', 'KOHAT': 'Central Corridor',
            'KURRAM': 'Central Corridor', 'HANGU': 'Central Corridor', 'KARAK': 'Central Corridor',
            'ORAKZAI': 'Central Corridor', 'TANK': 'Central Corridor', 'LAKKIMRWT': 'Central Corridor',
            'WAZIR-N': 'Central Corridor', 'WAZIR-S': 'Central Corridor',
            'WAZIR-S LOWER': 'Central Corridor', 'WAZIR-S UPPER': 'Central Corridor',
            'BAJOUR': 'Northern Corridor', 'CHARSADA': 'Northern Corridor',
            'CHITRAL': 'Northern Corridor', 'CHITRALLOWER': 'Northern Corridor',
            'CHITRALUPPER': 'Northern Corridor', 'DIRLOWER': 'Northern Corridor',
            'DIRUPPER': 'Northern Corridor', 'KHYBER': 'Northern Corridor',
            'MALAKAND': 'Northern Corridor', 'MARDAN': 'Northern Corridor',
            'MOHMAND': 'Northern Corridor', 'NOWSHERA': 'Northern Corridor',
            'PESHAWAR': 'Northern Corridor', 'SWABI': 'Northern Corridor', 'SWAT': 'Northern Corridor',
            'ABOTABAD': '', 'BATAGRAM': '', 'BUNER': '', 'HARIPUR': '', 'KOHISTANLOWER': '',
            'KOHISTANUPPER': '', 'MANSEHRA': '', 'SHANGLA': '', 'TORGHAR': ''}
NOT_ON = 'Not on a corridor'
# IDIMS re-cases district spellings between exports and the dashboard's own split of South
# Waziristan is written mixed case, so the corridor lookup goes through an upper-cased index.
CORR_UP = {k.upper(): v for k, v in CORRIDOR.items()}

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
    aliases = dict(ptpgeo.district_aliases(epim))
    aliases.update(FALLBACK)
    # IDIMS re-cases district spellings between exports ('WAZIR-S Lower' then 'WAZIR-S LOWER'), and
    # an exact-match lookup drops those rows silently - 20,539 of them in the 24-Oct-2026 export.
    # Accept a spelling case-insensitively only where every case variant agrees on one district.
    seen = defaultdict(set)
    for k, v in aliases.items():
        seen[k.lower()].add(v[0])
    for k, v in list(aliases.items()):
        low = k.lower()
        if low != k and len(seen[low]) == 1:
            aliases.setdefault(low, v)
    return aliases, ptpgeo.uc_district(snd), set(ucpt)


def resolve(d, aliases):
    """[display name, division] for an IDIMS district spelling, or None if it is unknown."""
    return aliases.get(d) or aliases.get(d.lower())


def collect(path, aliases, cut):
    zeros = dict.fromkeys([k for k, _ in SUMCOLS], 0.0)
    uc0 = dict.fromkeys([k for k in UQ if k != 'posts'], 0.0)
    cells = defaultdict(lambda: dict(zeros))
    mcells = defaultdict(lambda: dict(zeros))
    posts_in = defaultdict(set)
    ucs_in = defaultdict(set)
    months_in = defaultdict(set)
    mposts_in = defaultdict(set)
    mucs_in = defaultdict(set)
    uc_y = defaultdict(lambda: dict(uc0, p=set(), mo=set()))
    uc_m = defaultdict(lambda: dict(uc0, p=set()))
    post = {}
    refyears = set()
    # one cell per (district, class value, year) for each class axis, in MK order
    cells_c = {out: defaultdict(lambda: [0.0] * len(MK)) for _, _, _, out in CLASSES}
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
            pid = (r.get('Site_ID') or '').strip() or (r.get('ID') or '').strip()
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
            for aid, col, vkey, ckey in CLASSES:
                cv = (r.get(col) or '').strip()
                if not cv or cv == 'NULL':
                    cv = UNSTATED
                cc = cells_c[ckey][(dn[0], cv, y)]
                cc[0] += 1
                cc[1] += vals['cov']
                cc[2] += vals['used']
                cc[3] += vals['zd']
            months_in[key].add(m)
            ucs_in[key].add(u)
            mposts_in[mkey].add(pid)
            mucs_in[mkey].add(u)
            cbu = vals['cbu_in'] + vals['cbu_out']
            uy = uc_y[(u, y)]
            uy['rows'] += 1
            uy['zd'] += vals['zd']
            uy['cbu'] += cbu
            uy['p'].add(pid)
            uy['mo'].add(m)
            um = uc_m[(u, y * 100 + m)]
            um['rows'] += 1
            um['zd'] += vals['zd']
            um['cbu'] += cbu
            um['p'].add(pid)
            if vals['ref'] > 0:
                refyears.add(y)

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
            p['cbu'] += cbu
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
            uc_y, uc_m, refyears, post, dropped, total, cells_c)


def build(path, repo):
    aliases, snd_uc, ucpt = load_lookups(repo)
    last_cut = last_stamp(path)
    (cells, mcells, posts_in, ucs_in, months_in, mposts_in, mucs_in,
     uc_y, uc_m, refyears, post, dropped, total, cells_c) = collect(path, aliases, last_cut)
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
    by_code_y = defaultdict(list)
    by_code_m = defaultdict(list)
    for (code, y) in uc_y:
        by_code_y[code].append(y)
    for (code, ym) in uc_m:
        by_code_m[code].append(ym)
    for code, ps in by_uc.items():
        dd = list({p['d'] for p in ps})[0]
        yc = [[yidx[y], [len(uc_y[(code, y)]['p']), len(uc_y[(code, y)]['mo']),
                         int(round(uc_y[(code, y)]['rows'])), int(round(uc_y[(code, y)]['zd'])),
                         int(round(uc_y[(code, y)]['cbu']))]] for y in sorted(by_code_y[code])]
        mc = [[yidx[ym // 100] * 12 + ym % 100 - 1,
               [len(uc_m[(code, ym)]['p']), 1, int(round(uc_m[(code, ym)]['rows'])),
                int(round(uc_m[(code, ym)]['zd'])), int(round(uc_m[(code, ym)]['cbu']))]]
              for ym in sorted(by_code_m[code])]
        u.append([code, didx[dd], len(ps),
                  len({m for p in ps for m in p['months']}),
                  int(round(sum(p['zd'] for p in ps))),
                  int(round(sum(p['cbu'] for p in ps))),
                  1 if code in ucpt else 0, yc, mc])
    # the UC cells must add back to the district cells as well: every kept row has one UC, one
    # year and one month, so the two totals closing on the same figure is what proves the joins.
    uy_rows = sum(c[1][2] for r in u for c in r[7])
    um_rows = sum(c[1][2] for r in u for c in r[8])
    if uy_rows != kept or um_rows != kept:
        raise SystemExit('ERR ptp UC cells do not add up to the kept rows: years %s months %s kept %s'
                         % (uy_rows, um_rows, kept))
    ubad = []
    for r in u:
        slots = defaultdict(list)
        for c in r[8]:
            slots[c[0] // 12].append(c)
        ycell = {c[0]: c[1] for c in r[7]}
        for yj, cs in slots.items():
            yv = ycell.get(yj)
            if yv is None or sum(c[1][2] for c in cs) != yv[2] or sum(c[1][3] for c in cs) != yv[3] \
                    or len(cs) != yv[1] or max(c[1][0] for c in cs) > yv[0] \
                    or len({c[0] for c in cs}) != len(cs):
                ubad.append('%s year %s' % (r[0], years[yj] if yj < len(years) else yj))
    if ubad:
        raise SystemExit('ERR ptp UC month cells do not reconcile: %s' % ubad[:8])
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

    # month slots inside the reporting window that carry no report anywhere in KP - the source's own
    # holes, published so the coverage grid can call them gaps instead of leaving them blank.
    filing = defaultdict(set)
    for (dd, ym) in mcells:
        filing[ym].add(dd)
    slots = [yy * 100 + mm for yy in years for mm in range(1, 13) if yy * 100 + mm <= last_cut]
    gap = ['%d-%02d' % (s // 100, s % 100) for s in slots if s not in filing]

    # ---- the Coverage/OPV family the owner's workbook defines ----
    # Wastage by year is published as the reason for the covy cut, not as a footnote to it.
    # Local names here must not reuse u or vals: u is the UC roster and vals() builds a cell.
    cov_year = {}
    for (dd, yy), c in cells.items():
        e = cov_year.setdefault(yy, [0.0, 0.0])
        e[0] += c['cov']
        e[1] += c['used']
    cwaste = {}
    for yy in sorted(cov_year):
        cy, cu = cov_year[yy]
        cwaste[str(yy)] = [int(round(cy)), int(round(cu)),
                           round(100.0 * (1.0 - cy / cu), 2) if cu else None]
    if not sum(x[0] + x[1] for x in cwaste.values()):
        raise SystemExit('ERR ptp Coverage and OPVUsed are both empty - the export changed shape '
                         'and the family cannot be published')
    if cwaste.get(str(COVY)) is None or not (cwaste[str(COVY)][2] or 0) > 0:
        raise SystemExit('ERR ptp wastage in %d is %s, so the Coverage/OPV family no longer '
                         'reconciles from the published first year - re-check the workbook '
                         'definition before publishing it' % (COVY, cwaste.get(str(COVY))))

    cls = {}
    for aid, col, vkey, ckey in CLASSES:
        names = sorted({k[1] for k in cells_c[ckey]})
        # every kept row carries one class value for each axis, so a class axis closing on the
        # province totals is what proves no row was bucketed twice or dropped
        s_r = sum(x[0] for x in cells_c[ckey].values())
        s_c = sum(x[1] for x in cells_c[ckey].values())
        if s_r != kept:
            raise SystemExit('ERR ptp %s (%s) class rows %s do not close on kept %s'
                             % (aid, col, s_r, kept))
        if abs(s_c - sum(c['cov'] for c in cells.values())) > 1e-6:
            raise SystemExit('ERR ptp %s (%s) class coverage %s against province coverage %s'
                             % (aid, col, s_c, sum(c['cov'] for c in cells.values())))
        ci = {v: i for i, v in enumerate(names)}
        cls[vkey] = names
        cls[ckey] = [[didx[dd], ci[cv], yidx[yy], [int(round(x[i])) for i in range(len(MK))]]
                     for (dd, cv, yy), x in sorted(cells_c[ckey].items(),
                                                   key=lambda r: (r[0][0], r[0][2], r[0][1]))]

    cor, unmapped = [], []
    for dd in dists:
        raw = raw_of[dd]
        hit = CORRIDOR.get(raw, CORRIDOR.get(dd))
        if hit is None:
            hit = CORR_UP.get(raw.upper(), CORR_UP.get(dd.upper()))
        if hit is None:
            cor.append(UNSTATED)
            unmapped.append(raw)
        else:
            cor.append(hit or NOT_ON)

    # the guard that catches a rebound u: a payload whose roster collapsed to a number would still
    # pass every reconciliation above, because those all ran before it.
    if not isinstance(u, list) or len(u) != n['ucs'] or any(len(r) != 9 for r in u):
        raise SystemExit('ERR ptp UC roster lost: %s against n.ucs %s'
                         % (str(type(u).__name__) if not isinstance(u, list) else len(u), n['ucs']))
    if len(cls['cty']) < 2 or len(cls['cdur']) < 2:
        raise SystemExit('ERR ptp class axes collapsed: %s types, %s durations'
                         % (len(cls['cty']), len(cls['cdur'])))

    pkt = dashpatch.pkt_stamp(datetime.datetime.fromtimestamp(os.path.getmtime(path), dashpatch.PKT))
    ptp = {'src': os.path.basename(path), 'asof': pkt.split(' ')[0], 'gen': dashpatch.pkt_stamp(),
           'prov': 'KP', 'win': '%d-%d' % (years[0], years[-1]),
           'k': K, 'q': UQ, 'uk': ['code', 'd', 'posts', 'months', 'zd', 'cbu', 'onmap', 'yc', 'mc'],
           'reft': min(refyears) if refyears else None,
           'yr': years, 'ds': dists, 'dr': [raw_of[x] for x in dists],
           'dv': [dv_of[x] for x in dists], 'ty': types, 'st': stats, 'rk': risks,
           'd': d, 'u': u, 'pd': pd, 'pdk': ['type', 'last status', 'last security risk'],
           'n': n, 'drop': dict(dropped), 'gap': gap, 'gden': len(slots), 'last': last_cut,
           # the Coverage/OPV family, its first publishable year and the year table that proves it
           'covy': COVY, 'cw': cwaste, 'mk': MK, 'cor': cor, 'corx': unmapped,
           'cdef': {'src': 'PTP-STP Coverage and Compliance.twbx (Joint Database/3. HRMP)',
                    'waste': '1-(SUM([Coverage])/SUM([OPVUsed]))',
                    'factor': '100/(100-(Wastage %*100))',
                    'bands': 'Wastage % <=0 Negative, 0-10 Acceptable Range, >10 High Wastage',
                    'identity': 'OPVGiven = OPVUsed + OPVReturned, true in 261,710 of 261,923 rows '
                                'of that file'},
           'cty': cls['cty'], 'td': cls['td'], 'cdur': cls['cdur'], 'dd': cls['dd'],
           'cag': cls['cag'], 'ad': cls['ad'],
           'hold': ['Coverage_under5', 'Coverage_above5', 'VacRecvd', 'aav_cards',
                    'PostName', 'PostLocation', 'HealthFacility', 'Remarks'],
           'note': 'aggregated to district x year, district x month and UC x year/month; post names, '
                   'locations, facilities and remarks excluded; summed columns count reports, not '
                   'distinct children; posts keyed on Site_ID (ID before the Oct-2026 export); '
                   'refusals only exist from reft onwards; UC cells follow q; gap lists month slots '
                   '(yyyymm) up to last that carry no report anywhere in KP; cov/used/given/ret are '
                   'the Coverage/OPV family the owner workbook defines (cdef) and are only '
                   'meaningful from covy - cw carries the per-year [cov, used, wastage %] that shows '
                   'why; td/dd/ad are district x class x year cells in mk order, classing the '
                   'reporting row not the post; cor is each district\'s corridor as the owner '
                   'classifies it, corx names any district the map does not cover'}
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
    print('GAP ptp %d of %d %s' % (len(ptp['gap']), ptp['gden'], ptp['gap']))
    print('REF ptp refusals only from %s, total %s' % (ptp['reft'], format(ptp['n'].get('ref', 0), ',')))
    print('COV ptp published from %s: cov %s used %s, wastage %.2f%%'
          % (ptp['covy'], format(ptp['n']['cov'], ','), format(ptp['n']['used'], ','),
             100.0 * (1.0 - ptp['n']['cov'] / ptp['n']['used'])))
    print('CWASTE ptp %s' % ' '.join('%s %s' % (y, 'n/a' if x[2] is None else '%+.2f%%' % x[2])
                                     for y, x in sorted(ptp['cw'].items())))
    print('CLS ptp %d type cells (%d types), %d duration cells (%d), %d age cells (%d)'
          % (len(ptp['td']), len(ptp['cty']), len(ptp['dd']), len(ptp['cdur']),
             len(ptp['ad']), len(ptp['cag'])))
    print('CORR ptp %s' % ', '.join('%s x%d' % (c, ptp['cor'].count(c))
                                    for c in sorted(set(ptp['cor']))))
    if ptp['corx']:
        print('WARN ptp corridor map does not cover: %s - they publish as %s'
              % (ptp['corx'], UNSTATED))


if __name__ == '__main__':
    main()
