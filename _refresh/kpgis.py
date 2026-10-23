"""Minimal geometry readers for the KP district map build (no third-party GIS libs).

The shapefile set on disk has no .prj/.dbf pair for the district file, so the payload is
built from raw bytes: .shp holds the rings, .dbf holds the UC attribute table, and the
districts are named from the dashboard's own UC rows (see extract_kpgeo.py). Only the
shape types the KP files actually use are implemented, and anything else aborts rather
than being approximated.
"""
import struct

POLY = {5: 'polygon', 15: 'polygonz', 25: 'polygonm', 20: 'polygonzm',
        3: 'arcline', 11: 'arclinez', 13: 'polylinezm', 17: 'polylinem'}


def read_shp(path):
    """-> [(rings...)] per record; a ring is [(lon, lat), ...]. Polygon/polyline only."""
    b = open(path, 'rb').read()
    if struct.unpack('>i', b[0:4])[0] != 9994:
        raise SystemExit('ERR geo %s is not a shapefile' % path)
    off, out = 100, []
    while off + 8 <= len(b):
        _, clen = struct.unpack('>2i', b[off:off + 8])
        off += 8
        if clen <= 0 or off + clen * 2 > len(b):
            break                                   # truncated tail: stop, never pad
        body = b[off:off + clen * 2]
        st = struct.unpack('<i', body[:4])[0]
        if st == 0:                                 # deleted record placeholder
            off += clen * 2
            continue
        kind = POLY.get(st)
        if kind is None:
            raise SystemExit('ERR geo %s: unsupported shape type %d' % (path, st))
        nparts, npts = struct.unpack('<2i', body[36:44])
        parts = list(struct.unpack('<%di' % nparts, body[44:44 + 4 * nparts]))
        ends = parts[1:] + [npts]
        flat = struct.unpack('<%dd' % (2 * npts), body[44 + 4 * nparts:44 + 4 * nparts + 16 * npts])
        pts = list(zip(flat[0::2], flat[1::2]))
        out.append([pts[s:e] for s, e in zip(parts, ends)])
        off += clen * 2
    return out


def read_dbf(path, encoding='cp1252'):
    """-> [dict] of the dBase III attribute table (deleted records skipped)."""
    b = open(path, 'rb').read()
    nrec, hlen, rlen = struct.unpack('<IHH', b[4:12])
    fields, off = [], 32
    while b[off] != 0x0D:
        fields.append((b[off:off + 11].split(b'\x00')[0].decode('ascii'), b[off + 16]))
        off += 32
    rows = []
    for i in range(nrec):
        p = hlen + i * rlen
        if b[p] == 0x2A:
            continue
        c, vals = p + 1, []
        for name, ln in fields:
            raw = b[c:c + ln].decode(encoding, 'replace').strip('\x00').strip()
            vals.append(raw or None)
            c += ln
        rows.append(dict(zip([f[0] for f in fields], vals)))
    return rows


def ring_area(ring):
    s = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def centroid(ring):
    a = ring_area(ring)
    if abs(a) < 1e-12:
        return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
    n = len(ring)
    cx = cy = 0.0
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        f = x1 * y2 - x2 * y1
        cx += (x1 + x2) * f
        cy += (y1 + y2) * f
    return (cx / (6 * a), cy / (6 * a))


def bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def inside(pt, ring):
    """Ray casting on a closed ring."""
    x, y = pt
    hit = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _d2seg(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (px - (ax + t * dx)) ** 2 + (py - (ay + t * dy)) ** 2


def simplify(ring, tol):
    """Douglas-Peucker (iterative) on one ring; keeps first and last point."""
    keep = [False] * len(ring)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    t2 = tol * tol
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = ring[i], ring[j]
        worst, idx = -1.0, i
        for k in range(i + 1, j):
            d = _d2seg(ring[k], a, b)
            if d > worst:
                worst, idx = d, k
        if worst > t2:
            keep[idx] = True
            stack.append((i, idx))
            stack.append((idx, j))
    return [p for p, k in zip(ring, keep) if k]


def max_deviation(orig, simp):
    """Greatest distance from any original vertex to the simplified ring (degrees)."""
    worst = 0.0
    for p in orig:
        best = min(_d2seg(p, simp[i], simp[(i + 1) % len(simp)]) for i in range(len(simp)))
        if best > worst:
            worst = best
    return worst ** 0.5
