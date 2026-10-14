"""Extract per-district monitor operations from the LS 2026 Tableau workbooks.

Usage: python _refresh/extract_mon.py [--source PATH] [--out PATH]
Prints one status line: OK mon <json chars> <summary> | ERR mon <reason>

Scans every campaign folder under roots for Team Monitoring.twbx + AIC
Monitoring.twbx, unzips each to its .hyper extract and aggregates per
dashboard campaign label:
  tm  district -> [visit forms, distinct teams (uc x Team #), distinct UCs,
                   distinct monitor accounts (Surveyor Email count only)]
  aic district -> [AIC checklists filed, distinct UCs]

Keyed by the dashboard's cq campaign labels. Unknown ActivityNames are
reported, not embedded. --source is accepted for refresh.py CLI compat;
the extractor always does a full scan so all campaigns stay current.
"""
import argparse
import io
import json
import os
import sys
import tempfile
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'mon'

CAMP_MAP = {
    'NID FEB 2026': 'NID Feb 26',
    'NID APR 2026': 'NID Apr 26',
    'SNID May 2026': 'SNID May 2026',
    'SNID Sep 2026': 'SNID Sept 2026',
    'KP Special Aug 2026': 'KP Special Aug 2026',
    'KP Special Aug-Sep 2026-3': 'KP Special Aug-Sep 2026',
}

DS_META = {
    'NID Feb 26': 'February 2026 NID',
    'NID Apr 26': 'April 2026 NID',
    'SNID May 2026': 'May 2026 SNID',
    'SNID Sept 2026': 'September 2026 SNID',
    'KP Special Aug 2026': 'KP special Aug 2026',
    'KP Special Aug-Sep 2026': 'KP special Aug-Sep 2026',
}


def find_twbx(roots):
    found = []
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                lf = f.lower()
                if lf.endswith('.twbx') and ('team monitoring' in lf or 'aic monitoring' in lf):
                    found.append(os.path.join(dirpath, f))
    return sorted(found)


def hyper_rows(hyper_path, want_email, want_team):
    from tableauhyperapi import HyperProcess, Connection, Telemetry
    rows = []
    cols = ['"district_name"', '"ActivityName"', '"uc_name"']
    if want_email:
        cols.append('"Surveyor Email"')
    if want_team:
        cols.extend(['"Team #"', '"Day of Work"'])
    sql = 'SELECT %s FROM "Extract"."Extract"' % (', '.join(cols), )
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, hyper_path) as c:
            for r in c.execute_query(sql):
                rows.append(list(r))
    return rows


def read_twbx(path, kind, tmpdir):
    """kind: 'team' | 'aic'. Returns (ActivityName -> rows) mapping."""
    with zipfile.ZipFile(path) as z:
        hypers = [n for n in z.namelist() if n.lower().endswith('.hyper')]
        if not hypers:
            raise SystemExit('ERR mon no .hyper inside %s' % path)
        hyper_path = os.path.join(tmpdir, '%s_%d.hyper' % (kind, abs(hash(path)) % 10**8))
        with open(hyper_path, 'wb') as f:
            f.write(z.read(hypers[0]))
    try:
        rows = hyper_rows(hyper_path, kind == 'team', kind == 'team')
    finally:
        try:
            os.remove(hyper_path)
        except OSError:
            pass
    by_camp = {}
    for r in rows:
        act = (str(r[1]).strip() if r[1] is not None else '')
        by_camp.setdefault(act, []).append(r)
    return by_camp


def aggregate():
    cfg = srcutil.load_sources()
    e = cfg['auto'][DS]
    roots = e['roots']
    files = find_twbx(roots)
    if not files:
        raise SystemExit('ERR mon no Team/AIC Monitoring.twbx found under %s' % roots)

    camps = {}
    skipped, asof = [], None
    with tempfile.TemporaryDirectory() as tmpdir:
        for path in files:
            kind = 'team' if 'team monitoring' in os.path.basename(path).lower() else 'aic'
            mtime = os.path.getmtime(path)
            asof = max(asof or 0, mtime)
            by_camp = read_twbx(path, kind, tmpdir)
            for act, rows in by_camp.items():
                lab = CAMP_MAP.get(act)
                if not lab:
                    if act and act not in skipped:
                        skipped.append(act)
                    continue
                if lab not in camps:
                    camps[lab] = {}
                if kind in camps[lab]:
                    continue  # stale duplicate folder (Jul folder is a May byte-copy)
                g = {}
                for r in rows:
                    d = (str(r[0]).strip() if r[0] is not None else '')
                    if not d:
                        continue
                    g.setdefault(d, []).append(r)
                if kind == 'team':
                    out = {}
                    for d, rs in g.items():
                        ucs = {str(r[2]).strip() for r in rs if r[2] is not None}
                        teams = {(str(r[2]).strip(), str(r[4]).strip()) for r in rs
                                 if r[2] is not None and r[4] is not None}
                        mons = {str(r[3]).strip().lower() for r in rs if r[3] is not None}
                        days = {str(r[5]).strip() for r in rs if r[5] is not None}
                        out[d] = [len(rs), len(teams), len(ucs), len(mons), len(days)]
                    camps[lab]['tm'] = out
                else:
                    out = {}
                    for d, rs in g.items():
                        ucs = {str(r[2]).strip() for r in rs if r[2] is not None}
                        out[d] = [len(rs), len(ucs)]
                    camps[lab]['aic'] = out

    for lab in camps:
        camps[lab]['tm'] = dict(sorted(camps[lab].get('tm', {}).items()))
        camps[lab]['aic'] = dict(sorted(camps[lab].get('aic', {}).items()))

    import datetime
    mon = {'src': 'Monitor Tableau exports (team monitoring + AIC monitoring), LS 2026',
           'asof': datetime.date.fromtimestamp(asof).isoformat(), 'camps': camps}
    js = srcutil.dumps(mon)

    n_rows = sum(len(c.get('tm', {})) for c in camps.values())
    tot_t = sum(v[0] for c in camps.values() for v in c.get('tm', {}).values())
    tot_a = sum(v[0] for c in camps.values() for v in c.get('aic', {}).values())
    summary = '%d campaigns (%s), %d district rows, %s team visits, %s AIC checklists' % (
        len(camps), ', '.join(sorted(camps)), n_rows, format(tot_t, ','), format(tot_a, ','))
    if skipped:
        summary += '; unmapped ActivityName: %s' % ', '.join(sorted(skipped))
    return js, summary, files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    js, summary, files = aggregate()
    dest = a.out or os.path.join(srcutil.OUT, 'mon.json')
    srcutil.write_text(dest, js)
    print('SRC mon %s (%d files)' % (files[-1], len(files)))
    print('OK mon %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
