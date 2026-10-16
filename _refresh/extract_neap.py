"""Extract the upcoming campaign's pre-campaign readiness status (const NEAP).

Usage: python _refresh/extract_neap.py [--source PATH] [--out PATH]
Prints one status line: OK neap <json chars> <summary> | ERR neap <reason>

Source: EOC dashboard > Campaign > Pre Campaign > NEAP readiness (district-wise),
saved from the portal as `NEAP*.xls` (an HTML table) or `NEAP*.csv` in Downloads.
The portal re-saves under the same name with a " (n)" counter, so every save of a
round is a separate file; the newest one wins.

14 readiness columns per district, in portal order:
  DPEC held in time, DC, DHO, must-members attended %, UCMO present, UC secretary
  present, AICs trained %, teams trained %, microplans field-validated %, members
  18+, local member %, govt-accountable %, female member %, inaccessible areas.

Blank cells are reported as -1 (not reported); 0 means the portal reported zero.
District names are normalised to the dashboard spelling (WAZIR-S Lower / Upper)
and checked against the SND scope, so a scope change aborts instead of silently
dropping a district.

Payload: {"src":..,"asof":..,"camp":..,"n":..,"k":[[key,label],..],
          "d":{district:[14 values]},"tot":[14 means]}
"""
import argparse
import datetime
import html
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'neap'

K = [
    ('dpec', 'DPEC held on time'),
    ('dc', 'DC attended DPEC'),
    ('dho', 'DHO attended DPEC'),
    ('must', 'Must-members attended %'),
    ('ucmo', 'UCMO present'),
    ('ucsec', 'UC secretary present'),
    ('aic', 'AICs trained %'),
    ('trn', 'Teams trained %'),
    ('mpv', 'Microplans validated %'),
    ('adult', 'Members 18+ %'),
    ('loc', 'Local member %'),
    ('gov', 'Govt accountable %'),
    ('fem', 'Female member %'),
    ('inacc', 'Inaccessible areas'),
]
HEAD0 = 'dpecheldintime'
# source spellings, used only as anchors — the 14 indicator columns are read positionally
SRC_HEAD = ['province', 'district', 'dpecheldintime', 'dc', 'dho', 'mustmemberatteneded',
            'ucmopresent', 'ucsecretarypresent', 'trainedaics', 'teamtrained',
            'mpfieldvalidatedbyucstaff', 'allmtmembers18years', 'mtwithlocalteammembers',
            'mtwithgovaccountable', 'mtwithfemalemembers', 'inaccessiblearea']

RENAME = {
    'WAZIR-S LOWER': 'WAZIR-S Lower',
    'WAZIR-S UPPER': 'WAZIR-S Upper',
}


def snd_scope(repo):
    """(name -> target, campaign label) from the dashboard's own SND payload."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SND = ')
    if i < 0:
        raise SystemExit('ERR neap const SND not found in index.html')
    j = s.find('\n', i)
    snd = json.loads(s[i + len('const SND = '):j].rstrip().rstrip(';'))
    return {r[0] for r in snd['d']}, snd.get('n', '')


def cells_html(path):
    s = srcutil.read_text(path)
    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', s, re.S)
    out = []
    for tr in trs:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, re.S)
        out.append([html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in cells])
    return out


def cells_csv(path):
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        return [[c.strip() for c in r] for r in __import__('csv').reader(fh)]


def norm_head(h):
    return [re.sub(r'[^a-z0-9]', '', html.unescape(c).lower()) for c in h]


def parse(path):
    """-> (header, body rows) or None when the file is a different NEAP export."""
    raw = srcutil.read_text(path)
    rows = cells_html(path) if '<tr' in raw[:4000].lower() else cells_csv(path)
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return None
    hi = None
    for i, r in enumerate(rows[:12]):
        if norm_head(r)[:4] == ['province', 'district', 'dpecheldintime', 'dc']:
            hi = i
            break
    if hi is None:
        return None
    hdr = norm_head(rows[hi])
    if hdr[2] != re.sub(r'[^a-z0-9]', '', HEAD0):
        return None
    return rows[hi], rows[hi + 1:]


def parse_uc(path):
    """-> (header, body rows) of the UC-wise NEAP export, or None for other shapes.

    The UC-wise export carries the same 14 indicator columns in the same order
    after four geo columns (Province, District, Tehsil, UC)."""
    raw = srcutil.read_text(path)
    rows = cells_html(path) if '<tr' in raw[:4000].lower() else cells_csv(path)
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return None
    hi = None
    for i, r in enumerate(rows[:12]):
        if norm_head(r)[:5] == ['province', 'district', 'tehsil', 'uc', 'dpecheldintime']:
            hi = i
            break
    if hi is None:
        return None
    return norm_head(rows[hi]), rows[hi + 1:]


def num(v):
    t = ('' if v is None else str(v)).replace(',', '').strip()
    if t == '' or t.upper() in ('-', 'NA', 'N/A', 'NULL', 'NONE'):
        return -1
    try:
        return float(t)
    except ValueError:
        raise SystemExit('ERR neap %r is not a number' % v)


def build(path, repo):
    got = parse(path)
    if not got:
        raise SystemExit('ERR neap %s is not a NEAP readiness export' % os.path.basename(path))
    hdr, body = got
    hdr = norm_head(hdr)
    if len(hdr) < len(SRC_HEAD):
        raise SystemExit('ERR neap %s header has %d columns, want >= %d'
                         % (os.path.basename(path), len(hdr), len(SRC_HEAD)))
    for j in (2, 3, 2 + len(K) - 1):
        if hdr[j] != SRC_HEAD[j]:
            raise SystemExit('ERR neap %s column %d is %r, want %r'
                             % (os.path.basename(path), j, hdr[j], SRC_HEAD[j]))
    idx = list(range(2, 2 + len(K)))

    d = {}
    for r in body:
        if len(r) < 2:
            continue
        if len(r) < 2 + len(K):
            r = list(r) + [''] * (2 + len(K) - len(r))
        name = RENAME.get(r[1].strip().upper(), r[1].strip())
        if not name or name.upper() in ('TOTAL', 'GRAND TOTAL', 'KP'):
            continue
        if name in d:
            raise SystemExit('ERR neap duplicate district row %r' % name)
        d[name] = [num(r[j]) for j in idx]
    if not d:
        raise SystemExit('ERR neap no district rows found')

    scope, camp = snd_scope(repo)
    unknown = sorted(set(d) - scope)
    missing = sorted(scope - set(d))
    if unknown or missing:
        raise SystemExit('ERR neap district names do not match the %s scope: unknown=%s missing=%s'
                         % (camp or 'SND', unknown, missing))

    tot = []
    for k in range(len(K)):
        vals = [v[k] for v in d.values() if v[k] >= 0]
        tot.append(round(sum(vals) / len(vals), 1) if vals else -1)

    mtime = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    neap = {'src': os.path.basename(path), 'asof': mtime.date().isoformat(), 'camp': camp,
            'n': len(d), 'k': [[a, b] for a, b in K], 'd': d, 'tot': tot}
    started = sum(1 for v in d.values() if v[0] == 100)
    aic = [v[6] for v in d.values() if v[6] > 0]
    summary = ('%s, %d districts, DPEC held on time %d, AIC training reported by %d districts (best %s%%), '
               'teams with a female member reported by %d' % (
                   camp or 'SND', len(d), started, len(aic), (max(aic) if aic else '–'),
                   sum(1 for v in d.values() if v[12] > 0)))
    return neap, summary


def build_uc(path, repo):
    """-> (u payload, summary) from the newest UC-wise export, or (None, reason)."""
    got = parse_uc(path)
    if not got:
        return None, 'not a UC-wise NEAP export'
    hdr, body = got
    want = 4 + len(K)
    if len(hdr) < want:
        raise SystemExit('ERR neap UC export %s has %d columns, want >= %d'
                         % (os.path.basename(path), len(hdr), want))
    for j in range(len(K)):
        if hdr[4 + j] != SRC_HEAD[2 + j]:
            raise SystemExit('ERR neap UC export %s column %d is %r, want %r'
                             % (os.path.basename(path), 4 + j, hdr[4 + j], SRC_HEAD[2 + j]))
    scope, camp = snd_scope(repo)
    t, tr = [], {}
    r = []
    for row in body:
        if len(row) < want:
            row = list(row) + [''] * (want - len(row))
        dn = RENAME.get(row[1].strip().upper(), row[1].strip())
        if not dn or dn.upper() in ('TOTAL', 'GRAND TOTAL', 'KP'):
            continue
        if dn not in scope:
            raise SystemExit('ERR neap UC export district %r not in the %s scope'
                             % (dn, camp or 'SND'))
        tn = re.sub(r'\s+', ' ', row[2]).strip()
        ti = tr.get(tn)
        if ti is None:
            ti = tr[tn] = len(t)
            t.append(tn)
        r.append([dn, ti, re.sub(r'\s+', ' ', row[3]).strip()] + [num(row[4 + j]) for j in range(len(K))])
    if not r:
        return None, 'UC-wise export has no district rows'
    mtime = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    u = {'src': os.path.basename(path), 'asof': mtime.date().isoformat(),
         't': t, 'r': r}
    aic = sum(1 for x in r if x[3 + 6] > 0)
    summary = ('%s, %d UCs, %d tehsils, DPEC held on time %d, AIC training under way %d'
               % (camp or 'SND', len(r), len(t), sum(1 for x in r if x[3] >= 100), aic))
    return u, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    cands = srcutil.discover(cfg['auto'][DS])
    if a.source:
        s_abs = os.path.normcase(os.path.abspath(a.source))
        cands = [srcutil.stat_rec(a.source)] + [
            c for c in cands if os.path.normcase(os.path.abspath(c['path'])) != s_abs]
    if not cands:
        raise SystemExit('ERR neap no NEAP files found under %s' % cfg['auto'][DS]['roots'])
    for rec in cands:
        p = rec['path']
        if not os.path.exists(p):
            continue
        try:
            neap, summary = build(p, cfg['repo'])
        except SystemExit as e:
            if str(e).startswith('ERR neap %s is not' % os.path.basename(p)):
                # the newest save is often the UC-wise shape; the district
                # payload comes from the newest district-wise file instead
                if a.source and os.path.normcase(os.path.abspath(p)) == os.path.normcase(os.path.abspath(a.source)):
                    print('WARN neap %s is not the district-wise shape - trying the other candidates'
                          % os.path.basename(p))
                continue
            raise
        ucands = cands
        for rec2 in ucands:
            p2 = rec2['path']
            if not os.path.exists(p2):
                continue
            u, usum = build_uc(p2, cfg['repo'])
            if u:
                neap['u'] = u
                summary += '; UC-wise: ' + usum + ' (' + u['src'] + ')'
                break
        js = srcutil.dumps(neap)
        dest = a.out or os.path.join(srcutil.OUT, 'neap.json')
        srcutil.write_text(dest, js)
        print('SRC neap %s' % p)
        print('OK neap %d %s' % (len(js), summary))
        return
    raise SystemExit('ERR neap no NEAP readiness export among %d candidate files' % len(cands))


if __name__ == '__main__':
    main()
