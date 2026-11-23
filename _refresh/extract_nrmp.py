"""Extract the NID Dec-2026 resource micro-plan (const NRMP) from the campaign RMP workbook.

`KP RMP Dec.xlsx` is the EOC's district-grain resource micro-plan for the December NID:
one row per district with tehsils, union councils, the administrative target and the
team/staff matrix (mobile, transit/school and fixed teams, AICs, UCMOs, drivers, the
SMT/CBV area columns, DCF/DDM/DEO support and logistics). Campaign dates, scope
districts and the plan's district spellings are validated here so the dashboard cannot
show a plan row the EPI mapping does not know.

Usage: python _refresh/extract_nrmp.py [--out PATH]
Prints: OK nrmp <json chars> <summary> | ERR nrmp <reason>
"""
import argparse
import datetime
import os
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

DS = 'nrmp'
# (payload key, header label, group) in workbook column order after District
K = [('teh', '# of Tehsils', 'geo'), ('uc', '# of UCs', 'geo'), ('tg', 'Target', 'geo'),
     ('mt', 'Mobile Teams', 'mt'), ('mtt', 'Transit/School Teams', 'mt'), ('mtf', 'Fixed Teams', 'mt'),
     ('aic', 'AICs', 'mt'), ('ucmo', 'UCMOs', 'mt'),
     ('dfa', 'Driver for Female AIC', 'mt'), ('dfu', 'Driver for Female UCMO', 'mt'),
     ('smt', 'SMT Teams', 'smt'), ('smt_t', 'SMT Transit Teams', 'smt'), ('smt_f', 'SMT Fixed Teams', 'smt'),
     ('smt_a', 'SMT AICs', 'smt'), ('smt_u', 'SMT UCMOs', 'smt'), ('smt_fa', 'SMT Female AICs', 'smt'),
     ('smt_fu', 'SMT Female UCMOs', 'smt'), ('cbm', 'CBV Members', 'smt'), ('cba', 'CBV AICs', 'smt'),
     ('dcf', 'District Campaign Facilitator', 'sup'), ('ddm', 'DDM Focal Persons', 'sup'),
     ('deo', 'Data Entry Operators', 'sup'), ('ddm_t', 'DDM Tehsil Validator', 'sup'),
     ('ice', 'Ice of Ice', 'log'), ('veh', 'Vehicle', 'log')]
LAB = {'teh': 'Tehsils', 'uc': 'Union councils', 'tg': 'Children targeted',
       'mt': 'Mobile teams', 'mtt': 'Transit / school teams', 'mtf': 'Fixed teams',
       'aic': 'AICs', 'ucmo': 'UCMOs', 'dfa': 'Drivers (female AIC)', 'dfu': 'Drivers (female UCMO)',
       'smt': 'SMT teams', 'smt_t': 'SMT transit teams', 'smt_f': 'SMT fixed teams',
       'smt_a': 'SMT AICs', 'smt_u': 'SMT UCMOs', 'smt_fa': 'SMT female AICs',
       'smt_fu': 'SMT female UCMOs', 'cbm': 'CBV members', 'cba': 'CBV AICs',
       'dcf': 'District campaign facilitators', 'ddm': 'DDM focal persons',
       'deo': 'Data entry operators', 'ddm_t': 'DDM tehsil validators', 'ice': 'Ice packs',
       'veh': 'Vehicles / boats'}
# the plan writes one Kurram row; the EPI mapping splits it into two, hence this label
SPECIAL = {'KURRAM': ('Kurram (Lower, Central & Upper)', 'KOHAT')}


def norm(v):
    s = unicodedata.normalize('NFKD', str(v or '')).upper()
    return ''.join(c for c in s if c.isalnum())


def epi_map(cfg):
    """EPI-MIS district spelling -> (display district, division)."""
    s = srcutil.read_text(os.path.join(cfg['repo'], 'index.html'))
    i = s.find('const EPIM = ')
    j = s.find('];', i)
    import json
    epim = json.loads(s[i + len('const EPIM = '):j + 1].replace('<\\/', '</'))
    out = {}
    for r in epim:
        for ds in r['ds']:
            out[norm(ds)] = (r['ed'], r['dv'])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    e = {'patterns': ['KP RMP*.xlsx'], 'roots': ['C:\\Users\\HD\\Downloads', 'D:\\AMAZON DATA'],
         'exclude': ['~$*']}
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no KP RMP*.xlsx under %s' % (DS, e['roots']))
    rec = files[0]
    import openpyxl
    ws = openpyxl.load_workbook(rec['path'], data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    if not rows or str(rows[1][0] or '').strip().lower() != 'district':
        raise SystemExit('ERR %s header row not found in %s' % (DS, rec['name']))
    hdr = [str(c or '').strip() for c in rows[1]]
    ix = {}
    for key, lab, _ in K:
        hit = [i for i, h in enumerate(hdr) if h.startswith(lab)]
        if not hit:
            raise SystemExit('ERR %s %s missing column %r' % (DS, rec['name'], lab))
        ix[key] = hit[0]
    edm = epi_map(cfg)
    out, unknown = [], []
    for r in rows[2:]:
        d0 = str(r[0] or '').strip()
        if not d0:
            continue
        n = norm(d0)
        if n in SPECIAL:
            dn, dv = SPECIAL[n]
        elif n in edm:
            dn, dv = edm[n]
        else:
            unknown.append(d0)
            continue
        o = {'d': dn, 'dv': dv, 'src': d0}
        for key, _, _ in K:
            v = r[ix[key]]
            if v is None or (isinstance(v, str) and not v.strip()):
                o[key] = 0
            elif isinstance(v, (int, float)):
                o[key] = int(v)
            else:
                raise SystemExit('ERR %s %s %s column %s holds %r' % (DS, rec['name'], d0, key, v))
        out.append(o)
    if unknown:
        raise SystemExit('ERR %s districts not in the EPI mapping: %s' % (DS, unknown))
    if len(out) != 37:
        raise SystemExit('ERR %s %d district rows (expected 37)' % (DS, len(out)))
    out.sort(key=lambda x: x['d'])
    tot = {k: sum(r[k] for r in out) for k, _, _ in K}
    payload = {'src': rec['name'],
               'asof': datetime.date.fromtimestamp(files[0]['mtime']).isoformat(),
               'cam': 'NID Dec-2026', 'start': '2026-12-12',
               'k': [[k, LAB[k], g] for k, _, g in K], 'rows': out}
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'nrmp.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %d districts, %d UCs, target %s, %d teams (%d mobile + %d transit + %d fixed), '
          '%d SMT, %d CBV, %d AICs (%s)'
          % (DS, len(js), len(out), tot['uc'], '{:,}'.format(tot['tg']),
             tot['mt'] + tot['mtt'] + tot['mtf'], tot['mt'], tot['mtt'], tot['mtf'],
             tot['smt'], tot['cbm'], tot['aic'], rec['name']))


if __name__ == '__main__':
    main()
