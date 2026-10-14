"""Extract intra-campaign monitoring QUALITY indicators from the UC-level exports.

Usage: python _refresh/extract_icmq.py [--source PATH] [--out PATH]
Prints one status line: OK icmq <json chars> <summary> | ERR icmq <reason>

Sources (EOC dashboard > Intra-campaign monitoring > export):
  INTRA CAMPAIGN TEAM MONITORED*.csv   -> tm  (# Teams Monitored + 27 quality %)
  INTRA CAMPAIGN AIC(S) VISITED*.csv   -> aic (# Supervisors Monitored + 18 quality %)

Each file is UC-level: Campaign / Province / District / Tehsil / UC name + one
percentage column per indicator.  Rows are aggregated to district x campaign as
a count-weighted mean (weight = teams monitored, supervisors monitored, or UC
rows when the export carries no count column) and rounded to whole percent.

Some rounds ship a column that is present but never filled in: Tableau emits 0
for every UC, which would read as a genuine province-wide 0%.  An indicator is
therefore treated as not asked in a round when fewer than 5% of that round's
valid values are non-zero (over at least 20 valid values); its key is reported
back in the payload under 'zc' so the dashboard can say so.

Payload shape:
  {"src":..,"asof":..,"tmK":[[key,label],..],"aicK":[[..]],
   "camps":{label:{"tm":{district:[ucs,teams,v..]},"aic":{district:[ucs,sups,v..]},
                    "wt":{"tm":"teams","aic":"sup"},"zc":{"tm":["loc",..]}}}}
Values are whole percentages; -1 means the export did not carry that indicator.
District names are normalised to the dashboard spelling (WAZIR-S Lower ...).
'--source' is accepted for refresh.py CLI compat; the extractor always scans
every matching file so the full campaign history stays current.
"""
import argparse
import collections
import csv
import datetime
import io
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'icmq'

DIST_RENAME = {
    'WAZIR-S LOWER': 'WAZIR-S Lower',
    'WAZIR-S UPPER': 'WAZIR-S Upper',
}

# key, source column candidates (any spelling), display label
TM_COLS = [
    ('loc', ['% Local'], 'Local recruits'),
    ('fem', ['% Female'], 'Female team members'),
    ('adu', ['% Adult'], 'Adult team members'),
    ('gov', ['% Govt Account'], 'On govt account'),
    ('idm', ['% Name Matches ID'], 'Name matches ID'),
    ('vmk', ['% Use of Valid Marker'], 'Use of valid marker'),
    ('mkq', ['% Quilty of Markers', '% Quality of Markers'], 'Marker quality'),
    ('trn', ['% Training'], 'Team trained'),
    ('cc1', ['% Cold Chain- approved Vaccine carrier'], 'Cold chain: approved carrier'),
    ('cc2', ['% Cold Chain- lid and seal properly'], 'Cold chain: lid and seal'),
    ('cc3', ['% Cold Chain- no water inside carrier'], 'Cold chain: no water inside'),
    ('cc4', ['% Cold Chain- vaccine carrier lined with ice'], 'Cold chain: lined with ice'),
    ('dry', ['% Dry'], 'Vaccine carrier dry'),
    ('vvm', ['% Valid VVM'], 'Valid VVM'),
    ('lab', ['% Intact Label'], 'Intact vial label'),
    ('rec', ['% Vial Properly Recapped'], 'Vial properly recapped'),
    ('mat', ['% Vacc. Children matched with doses'], 'Children matched with doses'),
    ('tal', ['% TallySheet', '% Tally Sheet filling', '% Tally Sheet'], 'Tally sheet filled'),
    ('vita', ['% Team administered Vitamin-A'], 'Team gave vitamin A'),
    ('rmc', ['% Record of Missed Children'], 'Record of missed children'),
    ('rtm', ['% Location in Route Map'], 'Location in route map'),
    ('wkl', ['% Proper Workload'], 'Proper workload'),
    ('ask', ['% Asking Newborn,NA,SC'], 'Asked about newborn / NA / SC'),
    ('afp', ['% Asking for AFP&RI'], 'Asked about AFP & RI'),
    ('fmo', ['% Marker Used for FM Only'], 'Marker used for FM only'),
    ('fmf', ['% Marking FM fully'], 'FM fully marked'),
    ('wst', ['% Minimizing Vaccine Wastage'], 'Vaccine wastage minimised'),
]
TM_COUNT = ['# Teams Monitored', '# Teams monitored']

AIC_COLS = [
    ('trt', ['% Supervisor Trained Team'], 'Supervisor trained the team'),
    ('cri', ['% Supervisor Carry Items'], 'Supervisor carried necessary items'),
    ('vac', ['% Vaccine Carrier'], 'Carried vaccine carrier'),
    ('opv', ['% OPV vials'], 'Carried OPV vials'),
    ('fmk', ['% Finger markers'], 'Carried finger markers'),
    ('ccm', ['% Cold Chain maintained'], 'Cold chain maintained'),
    ('mpu', ['% Microplan Updated'], 'Microplan updated'),
    ('vit', ['% Supervisor carrying Vitamin-A'], 'Carried vitamin A'),
    ('nid', ['% Name and ID match'], 'Name and ID match'),
    ('chk', ['% Checklist Completed'], 'Checklist completed'),
    ('vm3', ['% Signed VM03'], 'Signed VM03'),
    ('pov', ['% Supervisor clear on opem/partial vial use',
             '% Supervisor clear on open/partial vial use'], 'Clear on open / partial vial use'),
    ('sup', ['% Supervisor supported teams'], 'Supervisor supported teams'),
    ('ipc', ['% Quality of the IPC Skills of the supervisor with the teams'], 'Quality of IPC skills'),
    ('cv1', ['% Covid Temp Check'], 'Covid: temperature check'),
    ('cv2', ['% Covid wear mask'], 'Covid: mask worn'),
    ('cv3', ['% Covid used santzer', '% Covid used sanitizer'], 'Covid: sanitiser used'),
    ('cv4', ['% Covid social distance'], 'Covid: social distance'),
]
AIC_COUNT = ['# Supervisors Monitored', '# Supervisor Monitored']

# A column present in the export but left empty by the field reads as 0 for every
# UC; below these limits the indicator is reported as "not asked" instead.
ZERO_MIN_ROWS = 20
ZERO_MAX_NONZERO = 0.05


def key(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def dist(s):
    d = re.sub(r'\s+', ' ', str(s or '').strip().upper())
    return DIST_RENAME.get(d, d)


def find_sources(entry):
    pats = entry.get('patterns') or []
    exc = entry.get('exclude') or ['~$*']
    out = []
    for root in entry.get('roots') or []:
        if not os.path.isdir(root):
            continue
        for fn in sorted(os.listdir(root)):
            p = os.path.join(root, fn)
            if not os.path.isfile(p):
                continue
            if any(fnmatch_x(fn, e) for e in exc):
                continue
            if not any(fnmatch_x(fn, p2) for p2 in pats):
                continue
            out.append(p)
    return out


def fnmatch_x(name, pat):
    import fnmatch
    return fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(name.lower(), pat.lower())


def read_rows(path):
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
    if not rows:
        raise SystemExit('ERR icmq empty file %s' % path)
    head = [c.strip() for c in rows[0]]
    body = rows[1:]
    # the AIC "2 campaigns" export carries a merged group header + a sub-header row
    if body and not body[0][0].strip() and any(c.strip() for c in body[0][1:]):
        sub = [c.strip() for c in body[0]]
        head = [(sub[i] or head[i]) if i < len(sub) else head[i] for i in range(len(head))]
        body = body[1:]
    return head, body


def num(v):
    s = str(v or '').strip().replace(',', '')
    if not s or s in ('-', 'NA', 'N/A', 'null', 'None'):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def pct(v):
    """A usable percentage, or None. The source Tableau calcs emit INF and ratios
    above 100% for some rows; those are excluded from the means and counted."""
    f = num(v)
    if f is None or f < 0 or f > 100:
        return None
    return f


def build_index(head, cols):
    """[(key, label, col_index or -1)] plus the count column index."""
    hk = {key(c): i for i, c in enumerate(head)}
    idx = []
    for k, alts, lab in cols:
        j = -1
        for alt in alts:
            if key(alt) in hk:
                j = hk[key(alt)]
                break
        idx.append((k, lab, j))
    cj = -1
    for c in (TM_COUNT if cols is TM_COLS else AIC_COUNT):
        if key(c) in hk:
            cj = hk[key(c)]
            break
    return idx, cj


def aggregate_file(path, kind):
    head, body = read_rows(path)
    idx, cj = build_index(head, TM_COLS if kind == 'tm' else AIC_COLS)
    ck = key('Campaign name')
    hk = {key(c): i for i, c in enumerate(head)}
    if ck not in hk or key('District name') not in hk:
        raise SystemExit('ERR icmq %s has no Campaign name / District name column' % os.path.basename(path))
    ci, di = hk[ck], hk[key('District name')]

    # (campaign, district) -> {'n':rows,'w':weight sum,'acc':{k:(wsum,nsum)}}
    agg = collections.defaultdict(lambda: {'n': 0, 'w': 0.0, 'acc': collections.defaultdict(lambda: [0.0, 0.0])})
    camp_rows = collections.Counter()
    camp_bad = collections.Counter()      # impossible cells (INF / >100%)
    camp_badrows = collections.Counter()  # UC rows carrying at least one
    # campaign -> key -> [valid values, non-zero values]
    camp_fill = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in body:
        if len(r) <= max(ci, di):
            continue
        camp = re.sub(r'\s+', ' ', r[ci].strip())
        if not camp or camp.lower() in ('total', 'grand total'):
            continue
        d = dist(r[di])
        if not d:
            continue
        w = num(r[cj]) if cj >= 0 and cj < len(r) else None
        if w is None or w <= 0:
            w = 1.0
        g = agg[(camp, d)]
        g['n'] += 1
        g['w'] += w
        camp_rows[camp] += 1
        bad = 0
        fill = camp_fill[camp]
        for k, _lab, j in idx:
            if j < 0 or j >= len(r):
                continue
            raw = str(r[j] or '').strip()
            if not raw or raw.upper() in ('-', 'NA', 'N/A', 'NULL', 'NONE', 'NAN'):
                continue
            v = pct(raw)
            if v is None:
                bad += 1
                continue
            f = fill[k]
            f[0] += 1
            if v > 0:
                f[1] += 1
            a = g['acc'][k]
            a[0] += v * w
            a[1] += w
        if bad:
            camp_bad[camp] += bad
            camp_badrows[camp] += 1
    blank = {c: sorted(k for k, f in d.items()
                       if f[0] >= ZERO_MIN_ROWS and f[1] < f[0] * ZERO_MAX_NONZERO)
             for c, d in camp_fill.items()}
    return {'agg': agg, 'rows': camp_rows, 'bad': camp_bad, 'badrows': camp_badrows,
            'blank': blank, 'ncols': len(idx), 'has_w': cj >= 0}


def order_camps(names):
    """Newest campaign first, using the month/year in the label when present."""
    mon = {m: i + 1 for i, m in enumerate(
        ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'])}

    def sk(n):
        m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*[^0-9]{0,12}'
                      r'(?:20)?(\d{2})\b', str(n).lower())
        if not m:
            return (0, 0, str(n))
        y = int(m.group(2))
        y += 2000 if y <= 40 else 1900
        return (y, mon.get(m.group(1), 0), str(n))
    return sorted(names, key=lambda n: (-sk(n)[0], -sk(n)[1], sk(n)[2]))


def aggregate():
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    files = find_sources(entry)
    if not files:
        raise SystemExit('ERR icmq no intra-campaign monitoring CSVs found under %s' % entry['roots'])

    asof = max(os.path.getmtime(p) for p in files)
    best = {'tm': {}, 'aic': {}}          # kind -> camp -> {'n','rows','has_w','bad','badrows','file'}
    for path in files:
        low = os.path.basename(path).lower()
        kind = 'tm' if 'team monitored' in low else ('aic' if 'aic' in low else None)
        if kind is None:
            raise SystemExit('ERR icmq cannot tell team/AIC from %s' % os.path.basename(path))
        res = aggregate_file(path, kind)
        cols = TM_COLS if kind == 'tm' else AIC_COLS
        by_camp = collections.defaultdict(dict)
        for (camp, d), g in res['agg'].items():
            dead = res['blank'].get(camp) or []
            vals = []
            for c in cols:
                a = g['acc'].get(c[0])
                if c[0] in dead or not a or not a[1]:
                    vals.append(-1)
                else:
                    vals.append(int(round(a[0] / a[1])))
            by_camp[camp][d] = [g['n'], int(round(g['w'])) if res['has_w'] else -1] + vals
        for camp, rows in by_camp.items():
            n = res['rows'][camp]
            prev = best[kind].get(camp)
            if prev and prev['n'] >= n:
                continue
            best[kind][camp] = {'n': n, 'rows': rows, 'has_w': res['has_w'],
                                'bad': res['bad'][camp], 'badrows': res['badrows'][camp],
                                'blank': res['blank'].get(camp) or [],
                                'file': os.path.basename(path)}

    camps = {}
    for kind in ('tm', 'aic'):
        for camp, blk in best[kind].items():
            c = camps.setdefault(camp, {'wt': {}, 'n': {}, 'dq': {}})
            c[kind] = dict(sorted(blk['rows'].items()))
            c['n'][kind] = blk['n']
            c['wt'][kind] = ('teams' if kind == 'tm' else 'sup') if blk['has_w'] else 'uc'
            if blk['bad']:
                c['dq'][kind] = [blk['bad'], blk['badrows']]
            if blk['blank']:
                c.setdefault('zc', {})[kind] = blk['blank']
    for c in camps.values():
        if not c['dq']:
            c.pop('dq', None)

    payload = {
        'src': 'Intra-campaign monitoring exports (team monitored + AIC visited), UC level',
        'asof': datetime.date.fromtimestamp(asof).isoformat(),
        'tmK': [[x[0], x[2]] for x in TM_COLS],
        'aicK': [[x[0], x[2]] for x in AIC_COLS],
        'camps': {c: camps[c] for c in order_camps(camps)},
    }
    js = srcutil.dumps(payload)

    n_tm = sum(v.get('n', {}).get('tm', 0) for v in camps.values())
    n_aic = sum(v.get('n', {}).get('aic', 0) for v in camps.values())
    bad = sum(x[0] for v in camps.values() for x in (v.get('dq') or {}).values())
    zc = sum(len(x) for v in camps.values() for x in (v.get('zc') or {}).values())
    summary = ('%d campaigns (%d with team monitoring, %d with AIC), %s team UC rows, '
               '%s AIC UC rows, %d tm + %d aic indicators, %s impossible cells excluded, '
               '%d empty columns reported as not asked'
               % (len(camps), sum(1 for v in camps.values() if 'tm' in v),
                  sum(1 for v in camps.values() if 'aic' in v),
                  format(n_tm, ','), format(n_aic, ','), len(TM_COLS), len(AIC_COLS),
                  format(bad, ','), zc))
    return js, summary, files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    js, summary, files = aggregate()
    dest = a.out or os.path.join(srcutil.OUT, 'icmq.json')
    srcutil.write_text(dest, js)
    print('SRC icmq %s (%d files)' % (files[-1], len(files)))
    print('OK icmq %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
