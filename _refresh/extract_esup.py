"""Extract EPI-MIS supervisory checklist visits (const ESUP) from the
Supervisory_Checklist_Report exports.

Every Supervisory_Checklist_Report*.xls under the configured roots is loaded; each
export covers its own date range and one visit type - the 2026 round arrives as two
files (fixed-site and outreach) - so the newest file wins per
(month, district, site type). Rows are visit-level checklists (~130 yes/no items);
this extractor keeps only the visit count, a curated set of quality indicators
(yes / answered per item) and the monitor's organisation and designation labels,
aggregated to month x district x site type, and caches the aggregates per file id
in _refresh/cache/esumon2.pkl so the 300-370 MB exports are streamed only once.
Monitor names, CNICs and vaccinator names are never read into the payload (public site).

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
CACHE = os.path.join(srcutil.HERE, 'cache', 'esumon2.pkl')
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
AG_COL, DG_COL = 'agency name of monitor', 'designation of monitor'
DATE_RE = re.compile(r'^(20\d\d-\d\d)-\d\d')
JUNK_D = ('', '0', '0.0', 'nan', 'none', 'null', 'total')
# label variants seen in the exports -> one row per organisation / designation.
# Only the labels are kept; monitor names and CNICs are never read.
AGMAP = {'GOVT.': 'GOVT', 'GOVT (LHW)': 'GOVT', 'GOVT': 'GOVT',
         'WHO-POLIO': 'WHO-POLIO/PEI', 'WHO-PEI': 'WHO-POLIO/PEI',
         'NSTOP': 'NSTOP', 'NSTOP-POLIO': 'NSTOP', 'NSTOP-EPI': 'NSTOP',
         'UNICEF-POLIO': 'UNICEF', 'UNICEF-EPI': 'UNICEF', 'UNICEF-ISD': 'UNICEF',
         'RIZ CONSULTING / GATES FOUNDATION': 'RIZ CONSULTING / GATES FOUNDATION',
         'RIZ / GATE FOUNDATION': 'RIZ CONSULTING / GATES FOUNDATION'}
# the designation column is free text: ~200 spellings of "1st level supervisor", bare
# person names and a few column-shift artefacts. Canonicalise at build time (below) so
# the payload carries one row per role and no person names; the parse keeps the raw label.
AG_FIX = {'WHO': 'WHO-POLIO/PEI', 'PEI': 'WHO-POLIO/PEI', 'WHO-PEI': 'WHO-POLIO/PEI'}
AG_JUNK = {'6', 'AREA COORDINATOR'}
DG_RULES = [
    (r'^(FSV|F ?S ?V|FIELD SUPERVISOR VACCINATOR)', 'FSV (field supervisor vaccinator)'),
    (r'^(DSV|D ?S ?V|DISTRICT SUPERVISOR VACCINATOR)', 'DSV (district supervisor vaccinator)'),
    (r'^(TSV|T ?S ?V|T S V|TSV\.|TEHSIL SUPERVISOR VACCINATOR)', 'TSV (tehsil supervisor vaccinator)'),
    (r'^(ASV|ASSISTANT SUPERINTENDENT VACCINATION)', 'ASV (assistant superintendent vaccination)'),
    (r'^(UCCO|UCO|UCPO|UC ?POLIO|UNION COUN[CS]EL POLIO OFFICER|UNION COUNCIL POLIO OFFICER)',
     'UC polio officer'),
    (r'^(T/TH POLIO OFFICER|TOWN-TEHSIL POLIO OFFICER|TOWN/TEHSIL POLIO OFFICER|TPO|TEHSIL POLIO OFFICER'
     r'|TEHSI POLIO OFFICER|TOWN POLIO OFFICER|TALUKA POLIO OFFICER)', 'Tehsil/town polio officer'),
    (r'^(DPO|DISTRICT POLIO OFFICER)', 'District polio officer'),
    (r'^(UCMO|U C M O|UCMOO|UC ?MO|UMCO)', 'UCMO (UC medical officer)'),
    (r'^(EPI COORDINATOR|EPI CORDINATOR|DR EPI COORDINATOR|DISTRICT EPI COORDINATOR'
     r'|DISTRACT EPI COORDINATOR|COORDINATOR EPI)', 'EPI coordinator'),
    (r'^(M ?& ?E OFFICER|M AND E OFFICER|M&E OFFICER|AD M&E|PROVINCIAL M AND E OFFICER)', 'M&E officer'),
    (r'^(NSTOP|N-STOP|NSTOP OFFICER|N-STOP OFFICER|INTERNATIONAL STOP OFFICER|NSTOP OFFICER EPI|NSTOP EPI)',
     'NSTOP officer'),
    (r'^(DSO|DISTRICT SURVEILLANCE OFFICER|DISEASE[S]? SURVEILLANCE OFFICER'
     r'|DISTRICT SURVEILLANCE COORDINATOR|DISTRICT SURVEILLANCE OFFICER \(DSO\))',
     'District surveillance officer'),
    (r'^(ASSISTANT DIRECTOR|AD T|AD TRAINING|AD EPI|AD M&E|AD$|A\.D\. SURVEILLANCE|AD ?SURVEILLANCE)',
     'Assistant director'),
    (r'^(DEPUTY DIRECTOR|DEPUTY DISTRICT HEALTH OFFICER|DDHO|DHO|DISTRICT HEALTH OFFICER)', 'Deputy director / DHO'),
    (r'^(FIELD SUPERVISOR MEDICAL OFFICER|FSMO|MEDICAL OFFICER|MO|M\.O|M/O|WMO|WOMEN MEDICAL OFFICER)',
     'Medical officer'),
    (r'^(UCSP|UCCSO|UCSSO|UCSO|UCC0|ANION COUNCIL COMMUNICATINS SUPPORT OFFICER'
     r'|UNION COUNCIL COMMUNICATINS SUPPORT OFFICER|UNION COUNCIL COMMUNICATION SUPPORT OFFICER'
     r'|UNION COUNCIL COMMUNICATION OFFICER|COMMUNITY COMMUNICATION OFFICER \(CCO\))',
     'UC communication support officer'),
    (r'^(IO|I\.?O|I ?O WHO|IO WHO|IO KHYBER|IMMUNIZATION OFFICER|IMMUNIZATION OFFICERS'
     r'|IMMUNIZATION OFFICER WHO POLIO|IMMUNIZATION OFFICER UNICEF)', 'Immunization officer'),
    (r'^(DISTRICT EPI FOCAL PERSON|DIVISIONAL EPI FOCAL PERSON|PEI FOCAL PERSON|VPD FOCAL PERSON'
     r'|AEFI FOCAL PERSON|AIFI FOCAL PERSON|DISTRICT FOCAL PERSON|VPD SURVEILLANCE FOCAL PERSON)',
     'EPI / VPD focal person'),
    (r'^(THIRD-PARTY FIELD MONITOR|DISTRICT MONITOR|PROVINCIAL EPI MONITOR|PROVINCIAL MONITOR'
     r'|1ST LEVEL MONITOR|FIELD SURVEILLANCE OFFICER|FSO|DISTRICT HEALTH COMMUNICATIONS SUPPORT OFFICER'
     r'|DHCSO)', 'Field monitor / surveillance officer'),
    (r'^(DATA ANALYST|PROGRAM ANALYST|DATA MANAGER|DATA MANAGERS|DEO|PROVINCIAL PROGRAM DATA ASSISTANT'
     r'|COMPUTER OPERATOR|SOFTWARE DEVELOPER)', 'Data / program analyst'),
]
# "1st/2nd level supervisor" is written in ~150 ways; catch the wordings the rules miss
L1_RE = re.compile(r'\b(1 ?ST|1RST|IST|FIRST|FRIST|FIST|FAST|FIRS)\b.{0,20}'
                   r'\b(LEVEL|LEVAL|LIVEL|LAVEL|LEWAL|LIVAL|LEVEP|LAEVAL|LEVL|LEVE|LAWAL|LEGAL|LEVELS)\b')


def norm_label(v, table, missing):
    k = re.sub(r'\s+', ' ', (v or '')).strip().upper()
    if not k:
        return missing
    return table.get(k, k)


def canon_ag(lab):
    v = re.sub(r'\s+', ' ', (lab or '')).strip().upper()
    if not v or v in AG_JUNK or v == '(NOT STATED)':
        return '(not stated)'
    return AG_FIX.get(v, lab.strip())


def canon_dg(lab):
    v = re.sub(r'\s+', ' ', (lab or '')).strip().upper()
    if not v or v in ('(NOT STATED)', 'NO', 'OUT REACH'):
        return '(not stated)'
    if v == 'OTHER':
        return 'Other roles'
    for pat, out in DG_RULES:
        if re.match(pat, v):
            return out
    if v in ('FLS', '1ST LEVEL SUPERVISOR', 'FIRST LEVEL SUPERVISOR') or L1_RE.search(v):
        if v.startswith('2ND') or v.startswith('2 LEVEL') or v.startswith('SECOND'):
            return '2nd-level supervisor'
        return 'FSV (field supervisor vaccinator)' if v == 'FLS' else '1st-level supervisor (other wording)'
    if v.startswith('2ND') or v.startswith('2 LEVEL') or v.startswith('SECOND') or '2 LEVEL' in v:
        return '2nd-level supervisor'
    return 'Other roles'


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
    for key, pref in [(SITE_COL, SITE_COL), (DT_COL, DT_COL),
                      ('ag', AG_COL), ('dg', DG_COL)] + IND:
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
        r = rows.setdefault((mo, dn, site), [0, {}, {}, {}])
        r[0] += 1
        if 'ag' in ix:
            lab = norm_label(cells[ix['ag']], AGMAP, '(not stated)')
            r[2][lab] = r[2].get(lab, 0) + 1
        if 'dg' in ix:
            lab = norm_label(cells[ix['dg']], DGMAP, '(not stated)')
            r[3][lab] = r[3].get(lab, 0) + 1
        for key, col in ix.items():
            if key in (SITE_COL, DT_COL, 'ag', 'dg'):
                continue
            v = (cells[col] or '').strip().lower()
            if v in ('yes', 'no'):
                o = r[1].setdefault(key, [0, 0])
                o[0] += v == 'yes'
                o[1] += 1
        n += 1
    if ix is None:
        print('# esup %s: no HTML table header (xlsx or empty export), skipped' % rec['name'])
    else:
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
    for (mo, dn, site), (nv, inds, ags, dgs) in by.items():
        r = agg.setdefault((mo, dn), {'ed': next(k for k in edm if k.lower() == dn),
                                      'f': 0, 'o': 0, 'i': {}, 'ag': {}, 'dg': {}})
        if site == 'fixed':
            r['f'] += nv
        else:
            r['o'] += nv
        for key, (y, n) in inds.items():
            o = r['i'].setdefault(key, [0, 0])
            o[0] += y
            o[1] += n
        for lab, cnt in ags.items():
            o = r['ag'].setdefault(canon_ag(lab), [0, 0])
            o[0 if site == 'fixed' else 1] += cnt
        for lab, cnt in dgs.items():
            o = r['dg'].setdefault(canon_dg(lab), [0, 0])
            o[0 if site == 'fixed' else 1] += cnt
    out_rows = []
    for (mo, dn) in sorted(agg):
        r = agg[(mo, dn)]
        ds, dv = edm[r['ed']]
        row = {'mo': mo, 'ed': r['ed'], 'ds': ds, 'dv': dv,
               'f': r['f'], 'o': r['o'],
               'i': {k: v for k, v in sorted(r['i'].items())}}
        if r['ag']:
            row['ag'] = {k: v for k, v in sorted(r['ag'].items(), key=lambda x: -sum(x[1]))}
        if r['dg']:
            row['dg'] = {k: v for k, v in sorted(r['dg'].items(), key=lambda x: -sum(x[1]))}
        out_rows.append(row)
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
