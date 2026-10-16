"""Extract EPI-MIS supervisory checklist visits (const ESUP) from the
Supervisory_Checklist_Report exports.

Every Supervisory_Checklist_Report*.xls under the configured roots is loaded; each
export covers its own date range and one visit type - the 2026 round arrives as two
files (fixed-site and outreach) - so the newest file wins per
(month, district, site type). Rows are visit-level checklists (~130 yes/no items);
this extractor keeps only the visit count and a curated set of quality indicators
(yes / answered per item), aggregated to month x district x site type, and caches
the aggregates per file id in _refresh/cache/esumon.pkl so the 300-370 MB exports
are streamed only once. Monitor names / CNICs / designations and vaccinator names
are never read into the payload (public site).

Usage: python _refresh/extract_esup.py [--out PATH]
Prints: SRC esup <newest file> | OK esup <json chars> <summary> | ERR esup <reason>
"""
import argparse
import os
import pickle
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import srcutil

DS = 'esup'
CACHE = os.path.join(srcutil.HERE, 'cache', 'esumon.pkl')
# indicator key -> header-label prefix (columns located by label, not position)
IND = [('open', 'Is the fixed site open at time of monitoring'),
       ('sign', 'Is EPI sign board'),
       ('chart', 'Are immunization monitoring charts displ'),
       ('upd', 'Are immunization monitoring charts updat'),
       ('plan', 'Is microplan available'),
       ('zd', 'Is the list of zero-dose children used'),
       ('sk', 'Is skilled person'),
       ('disp', 'Is vaccinator disposing the used syringe'),
       ('aefi', 'Does the vaccinator know about AEFIs'),
       ('tally', 'Is the vaccinator using a tally sheet'),
       ('card', 'Is EPI card being issued'),
       ('qr', 'Is the vaccinator using QR codes'),
       ('so', 'Is there any stockout observed'),
       ('mob', 'Was social mobilization conducted prior'),
       ('sbox', 'Are safety boxes available'),
       ('ret', 'Are syringes from outreach areas brought')]
SITE_COL, DT_COL = 'type of vacc', 'date & time of visit'
DATE_RE = re.compile(r'^(20\d\d-\d\d)-\d\d')
JUNK_D = ('', '0', '0.0', 'nan', 'none', 'null', 'total')


def load_cache():
    try:
        with open(CACHE, 'rb') as f:
            return pickle.load(f)
    except (OSError, EOFError, ValueError):
        return {}


def store_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(cache, f)
    os.replace(tmp, CACHE)


def stream_rows(path):
    buf = ''
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(4194304)
            if not chunk:
                break
            buf += chunk.decode('utf-8', 'replace')
            parts = buf.split('</tr>')
            buf = parts.pop()
            for pr in parts:
                if '<tr' in pr:
                    yield pr[pr.index('<tr'):]
    if '<tr' in buf:
        yield buf[buf.index('<tr'):]


def cellmap(hdr_cells):
    """header label list -> {key: column index}. Only site/date are required; older
    export shapes lack some questions (e.g. the outreach mobilization item), those
    indicators are simply absent from that file's contribution."""
    norm = [re.sub(r'\s+', ' ', c).strip().lower() for c in hdr_cells]
    ix = {}
    for key, pref in [(SITE_COL, SITE_COL), (DT_COL, DT_COL)] + IND:
        pref = pref.lower()
        for i, c in enumerate(norm):
            if c.startswith(pref):
                ix[key] = i
                break
    miss = [k for k in (SITE_COL, DT_COL) if k not in ix]
    if miss:
        raise SystemExit('ERR %s site/date columns not found: %s' % (DS, miss))
    return ix


def period(rec):
    with open(rec['path'], 'rb') as f:
        head = f.read(20000).decode('utf-8', 'replace')
    m = re.search(r'From\s*:\s*(20\d\d-\d\d-\d\d).{0,200}?To\s*:\s*(20\d\d-\d\d-\d\d)', head, re.S)
    return (m.group(1), m.group(2)) if m else None


def parse_file(rec, edn_ok):
    """One export -> {(mo, district, site): [visits, {ind: [yes, answered]}]}."""
    ix = None
    rows = {}
    n, junk = 0, 0
    for pr in stream_rows(rec['path']):
        cells = [re.sub(r'<[^>]+>', '', c) for c in
                 re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', pr, re.S)]
        if ix is None:
            if len(cells) < 100:
                continue
            ix = cellmap(cells)
            continue
        if len(cells) <= max(ix.values()):
            continue
        if not re.match(r'^\d+$', (cells[0] or '').strip()):
            continue
        d = re.sub(r'\s+', ' ', cells[1]).strip()
        dm = DATE_RE.match((cells[ix[DT_COL]] or '').strip())
        dn = d.lower()
        if not dm or dn in JUNK_D:
            junk += 1
            continue
        if dn not in edn_ok:
            raise SystemExit('ERR %s district %r not in the dashboard EPI mapping (%s)'
                             % (DS, d, rec['name']))
        site = (cells[ix[SITE_COL]] or '').strip().lower()
        if site not in ('fixed', 'outreach'):
            junk += 1
            continue
        mo = dm.group(1)
        r = rows.setdefault((mo, dn, site), [0, {}])
        r[0] += 1
        for key, col in ix.items():
            if key in (SITE_COL, DT_COL):
                continue
            v = (cells[col] or '').strip().lower()
            if v in ('yes', 'no'):
                o = r[1].setdefault(key, [0, 0])
                o[0] += v == 'yes'
                o[1] += 1
        n += 1
    print('# esup %s: %d visits, %d month-district-site keys, %d junk rows skipped%s'
          % (rec['name'], n, len(rows), junk,
             '' if len(ix) >= len(IND) + 2 else ' (no column for: %s)'
             % ', '.join(k for k, _ in IND if k not in ix)))
    return rows


def build(cfg):
    e = cfg['auto'][DS]
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no Supervisory_Checklist files under %s' % (DS, e['roots']))
    edm = _epicache.edmap(cfg['repo'])
    edn_ok = {k.lower() for k in edm}
    cache = load_cache()
    by = {}
    used = []
    for rec in files:  # newest mtime first: first writer wins per (mo, district, site)
        fid = srcutil.file_id(rec)
        if fid not in cache:
            cache[fid] = parse_file(rec, edn_ok)
            store_cache(cache)
        rows = cache[fid]
        used.append(rec['name'])
        for key, v in rows.items():
            by.setdefault(key, v)
    store_cache(cache)
    if not by:
        raise SystemExit('ERR %s no rows parsed' % DS)

    agg = {}
    for (mo, dn, site), (nv, inds) in by.items():
        r = agg.setdefault((mo, dn), {'ed': next(k for k in edm if k.lower() == dn),
                                      'f': 0, 'o': 0, 'i': {}})
        if site == 'fixed':
            r['f'] += nv
        else:
            r['o'] += nv
        for key, (y, n) in inds.items():
            o = r['i'].setdefault(key, [0, 0])
            o[0] += y
            o[1] += n
    out_rows = []
    for (mo, dn) in sorted(agg):
        r = agg[(mo, dn)]
        ds, dv = edm[r['ed']]
        out_rows.append({'mo': mo, 'ed': r['ed'], 'ds': ds, 'dv': dv,
                         'f': r['f'], 'o': r['o'],
                         'i': {k: v for k, v in sorted(r['i'].items())}})
    nf = sum(r['f'] for r in out_rows)
    no = sum(r['o'] for r in out_rows)
    asof = None
    for rec in files:
        pr = period(rec)
        if pr:
            asof = max(asof or pr[1], pr[1])
    if not asof:  # these exports carry no From/To header - use the newest file's date
        import datetime
        asof = datetime.date.fromtimestamp(files[0]['mtime']).isoformat()
    summary = ('%d fixed + %d outreach visits, %d districts, %s..%s (%d files: %s)'
               % (nf, no, len({r['ed'] for r in out_rows}),
                  out_rows[0]['mo'], out_rows[-1]['mo'], len(used), used[0]))
    out = {'src': 'EPI-MIS supervisory checklists (%d files: %s)' % (len(used), ', '.join(used)),
           'asof': asof, 'ind': [k for k, _ in IND],
           'indlab': {'open': 'Fixed site open at time of visit', 'sign': 'EPI sign board displayed',
                      'chart': 'Monitoring charts displayed', 'upd': 'Monitoring charts updated',
                      'plan': 'Microplan available with vaccinator', 'zd': 'Zero-dose list used by vaccinator',
                      'sk': 'Skilled vaccinator present', 'disp': 'Syringes disposed safely',
                      'aefi': 'Vaccinator knows AEFI response', 'tally': 'Tally sheet in use',
                      'card': 'EPI card issued to every child', 'qr': 'QR codes in use',
                      'so': 'Vaccine stockout observed (bad)', 'mob': 'Social mobilization done before session',
                      'sbox': 'Safety boxes available and used', 'ret': 'Syringes returned from outreach'},
           'rows': out_rows}
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # interface parity: every match is loaded
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    out, summary = build(cfg)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'esup.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s' % (DS, len(js), summary))


if __name__ == '__main__':
    main()
