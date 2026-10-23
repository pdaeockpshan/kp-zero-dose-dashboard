"""Name and simplify the KP district polygons for the dashboard map (KPGEO).

The district shapefile on disk ships geometry only - no .dbf, so the 37 polygons are
unnamed. They are labelled through the UC layer (PK_Admin4-KP_UCs), whose own attribute
table carries the polio UC code that joins to EPI[].c: each district polygon is given the
dashboard's majority district among the UCs that fall inside it. Nothing is guessed - a
polygon needs at least MIN_UCS dashboard-resolved UCs and MIN_AGREE agreement, and the
build aborts unless every one of the dashboard's 37 districts is claimed exactly once.

Geometry: 37 single-ring polygons, 24 720 vertices, WGS84 lon/lat. Rings are simplified
with Douglas-Peucker and asserted against max_deviation + area drift before the payload
is emitted, so a collapsed or over-smoothed district fails the build instead of shipping
a wrong map.

Usage:  python _refresh/extract_kpgeo.py            # report only, writes nothing
        python _refresh/extract_kpgeo.py --emit     # write _refresh/out/KPGEO.json
"""
import argparse
import collections
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import kpgis as G
import srcutil

DISTRICT_SHP = r'D:\AMAZON DATA\District Wise KP Shape File.shp'
UC_DIR = r'D:\extra tasks\KP UC Shapefile\KP UC Shapefile'
UC_SHP = os.path.join(UC_DIR, 'PK_Admin4-KP_UCs_23OCt21.shp')
UC_DBF = os.path.join(UC_DIR, 'PK_Admin4-KP_UCs_23OCt21.dbf')

MIN_UCS = 5           # dashboard-resolved UCs needed before a polygon can be named
MIN_AGREE = 0.75      # share of those UCs that must agree on the district
TOL = 0.0025          # Douglas-Peucker tolerance in degrees (~270 m at KP latitude)
MAX_DEV = 0.004       # no original vertex may sit further than this from the result
MAX_AREA_DRIFT = 0.02
VB_H = 1000.0         # viewBox height in px


def norm_code(c):
    """Polio UC codes arrive as padded strings in the dbf ('33405007.000000')."""
    return str(c or '').strip().upper().split('.')[0]


def dashboard_districts(text):
    """-> ({uc code: district}, {uc name(lc): district}, {district: division}, [districts]) from EPI."""
    epi = json.loads(dashpatch.get_payload(text, 'EPI'))
    by_code, by_name, division = {}, {}, {}
    for r in epi:
        if r.get('c'):
            by_code[norm_code(r['c'])] = r['d']
        if r.get('u'):
            by_name.setdefault(r['u'].strip().lower(), r['d'])
        if r.get('dv'):
            division.setdefault(r['d'], r['dv'])
    return by_code, by_name, division, sorted(set(r['d'] for r in epi if r.get('d')))


def rep_point(rings):
    """A point inside the biggest ring: its area centroid when that lands inside, else a vertex."""
    big = max(rings, key=lambda r: abs(G.ring_area(r)))
    c = G.centroid(big)
    if G.inside(c, big):
        return c
    for p in big:
        if G.inside(p, big):
            return p
    return big[0]


def project(bb):
    """-> (fn, vb_w) mapping lon/lat to an aspect-correct integer viewBox."""
    lon0, lat0, lon1, lat1 = bb
    mid = math.radians((lat0 + lat1) / 2.0)
    k = math.cos(mid)                                    # lon degrees are shorter
    sc = VB_H / (lat1 - lat0)
    w = (lon1 - lon0) * k * sc
    return (lambda lon, lat: (round((lon - lon0) * k * sc, 1), round((lat1 - lat) * sc, 1))), round(w, 1)


def label(polys, ucs):
    """-> (per-polygon vote records, UCs inside >1 polygon, UCs inside none)."""
    out = []
    owner = [[] for _ in ucs]
    for i, rings in enumerate(polys):
        ring = rings[0]
        hits = [(j, d) for j, (pt, d) in enumerate(ucs) if G.inside(pt, ring)]
        for j, _ in hits:
            owner[j].append(i)
        resolved = [d for _, d in hits if d]
        out.append({'i': i, 'ucs': len(hits), 'resolved': len(resolved),
                    'vote': collections.Counter(resolved)})
    return out, sum(1 for o in owner if len(o) > 1), sum(1 for o in owner if not o)


def anchor(simp, orig):
    """Label point: the simplified vertex deepest inside the original ring."""
    best, bxy = -1.0, simp[0]
    for p in simp:
        d = min(G._d2seg(p, orig[i], orig[(i + 1) % len(orig)]) for i in range(len(orig)))
        if d > best:
            best, bxy = d, p
    return bxy


def ring_path(ring, fn):
    """M + implicit lineto + Z on integer viewBox coords; consecutive duplicates dropped."""
    pts = []
    for lon, lat in ring[:-1] if ring[0] == ring[-1] else ring:
        xy = tuple(round(v) for v in fn(lon, lat))
        if not pts or pts[-1] != xy:
            pts.append(xy)
    return 'M' + ' '.join('%d %d' % p for p in pts) + 'Z', len(pts)


def emit(polys, by_idx, named, division, cfg):
    bb = [min(G.bbox(r[0])[0] for r in polys), min(G.bbox(r[0])[1] for r in polys),
          max(G.bbox(r[0])[2] for r in polys), max(G.bbox(r[0])[3] for r in polys)]
    fn, vb_w = project(bb)
    rows, total_pts, warn = [], 0, []
    for code, idx in sorted((v, ids[0]) for v, ids in named.items()):
        ring = polys[idx][0]
        simp = G.simplify(ring, TOL)
        if len(simp) < 4:
            raise SystemExit('ERR %s simplified to %d points' % (code, len(simp)))
        dev = G.max_deviation(ring, simp)
        a0, a1 = abs(G.ring_area(ring)), abs(G.ring_area(simp))
        if dev > MAX_DEV:
            raise SystemExit('ERR %s deviates %.4f deg from the source ring' % (code, dev))
        if abs(a1 - a0) / a0 > MAX_AREA_DRIFT:
            raise SystemExit('ERR %s area drift %.1f%% after simplifying' % (code, 100 * (a1 - a0) / a0))
        mid = math.radians(G.centroid(ring)[1])
        km2 = a0 * (111.320 * math.cos(mid)) * 111.320
        if km2 < 100:
            warn.append('%s only %.0f km2' % (code, km2))
        ax, ay = fn(*anchor(simp, ring))
        p, npts = ring_path(simp, fn)
        total_pts += npts
        rows.append({'c': code, 'v': division.get(code, ''), 'a': round(km2),
                     'uc': by_idx[idx], 'x': ax, 'y': ay, 'p': p})
    payload = {'bb': [round(x, 4) for x in bb], 'vb': [vb_w, int(VB_H)],
               'src': os.path.basename(DISTRICT_SHP), 'labels': 'EPI UC join',
               'ucsrc': os.path.basename(UC_SHP), 'uc_asof': '23-Oct-2021',
               'polys': len(rows), 'pts': total_pts, 'd': rows}
    js = srcutil.dumps(payload)
    print('KPGEO: %d districts, %d vertices, %d KB, total %.0f km2'
          % (len(rows), total_pts, len(js.encode('utf-8')) // 1024, sum(r['a'] for r in rows)))
    if warn:
        print('WARN', '; '.join(warn))
    dest = os.path.join(srcutil.OUT, 'kpgeo.json')
    srcutil.write_text(dest, js)
    print('wrote', dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--emit', action='store_true')
    a = ap.parse_args()

    cfg = srcutil.load_sources()
    text = srcutil.read_text(os.path.join(srcutil.repo_root(cfg), 'index.html'))
    by_code, by_name, division, districts = dashboard_districts(text)
    print('dashboard: %d districts, %d UC codes, %d UC names' % (len(districts), len(by_code), len(by_name)))

    polys = G.read_shp(DISTRICT_SHP)
    uc_polys = G.read_shp(UC_SHP)
    rows = G.read_dbf(UC_DBF)
    print('shapes: %d district polygons, %d UC polygons, %d UC attribute rows' % (len(polys), len(uc_polys), len(rows)))
    if len(uc_polys) != len(rows):
        raise SystemExit('ERR UC .shp/.dbf out of step (%d vs %d) - do not label blind' % (len(uc_polys), len(rows)))
    if any(len(r) != 1 for r in polys):
        raise SystemExit('ERR district file has multi-ring polygons - the vote below only reads ring 0')

    ucs = []
    for geo, row in zip(uc_polys, rows):
        code = norm_code(row.get('Ucode'))
        d = by_code.get(code) or by_name.get((row.get('UC') or '').strip().lower())
        ucs.append((rep_point(geo), d))
    print('UC join: %d/%d carry a dashboard district' % (sum(1 for _, d in ucs if d), len(ucs)))

    votes, multi, outside = label(polys, ucs)
    print('containment: %d UCs inside more than one district polygon, %d inside none' % (multi, outside))
    named = {}
    for v in sorted(votes, key=lambda x: -x['resolved']):
        top = v['vote'].most_common()
        share = top[0][1] / v['resolved'] if top and v['resolved'] else 0.0
        name = top[0][0] if top and v['resolved'] >= MIN_UCS and share >= MIN_AGREE else None
        if name:
            named.setdefault(name, []).append(v['i'])
        print('poly %-2d ucs=%-4d res=%-4d %-14s %s  bbox %s' % (
            v['i'], v['ucs'], v['resolved'], name or 'UNRESOLVED',
            ' '.join('%s:%d' % (k, n) for k, n in top[:3]) or '-',
            ' '.join('%.3f' % x for x in G.bbox(polys[v['i']][0]))))

    unres = [v['i'] for v in votes if v['i'] not in {i for ids in named.values() for i in ids}]
    dupes = {d: i for d, i in named.items() if len(i) > 1}
    missing = [d for d in districts if d not in named]
    print('claimed %d/%d districts | unresolved polygons: %s | duplicated: %s | missing: %s'
          % (len(named), len(districts), unres, dupes, missing))
    if missing or dupes or len(named) != len(districts):
        raise SystemExit('ERR not a 1:1 mapping - refusing to emit')

    if not a.emit:
        print('REPORT ONLY (pass --emit to write the payload)')
        return
    emit(polys, {v['i']: v['resolved'] for v in votes}, named, division, cfg)


if __name__ == '__main__':
    main()
