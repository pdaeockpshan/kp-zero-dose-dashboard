"""Add the SNID Nov 2026 market-survey and PCM rounds to the campaign data pack.

`PKX.ms` and `PKX.pcm` carry the two portal exports the compiled INDIC series does not hold:
MS.xlsx (market survey) and PCM - SNID Nov 2026.xlsx (post-campaign monitoring), both read
16-Nov-2026.  The pack renders entirely from these entries, so the district view, the UC detail,
the scoped Total line and the CSV download all work without further code.

Columns are INDIC.S.ms.k / INDIC.S.pcm.k exactly.  Where the export has no matching column the
cell is -1 and prints the dashboard's "not reported" dash; the entry note names every such column,
so a dash can never be mistaken for a zero.

The PCM rows are proved against the `const PCM` payload the Monitoring analysis tab reads: the
same workbook must produce the same checked / FM / missed totals district for district before
anything is written.  That payload is then swapped in from the same extractor output, so the tab
and the pack cannot drift apart.

Usage: python _refresh/patch_ms_pcm_pack.py [--write]
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PATH = 'index.html'
MS_PATH = os.path.join(os.environ.get('USERPROFILE') or '', 'Downloads', 'MS.xlsx')
PCM_PATH = os.path.join(os.environ.get('USERPROFILE') or '', 'Downloads', 'PCM - SNID Nov 2026.xlsx')
READ = '16-Nov-2026'

MS_COLS = ['# of MS', 'MS Check', 'Sum of MS_Verified', 'MS %', 'MS Missed',
           'MS NT House Missed', 'MS NT ChildMissed', 'MS NA', 'MS REF',
           'MS Child Asleep', 'MS VBNFM']
PCM_COLS = ['# of PCM MS', 'PCM_MS_Checked', 'PCM_MS_FM', 'PCM_MS%', 'PCM_NA', 'PCM_REF',
            'PCM_NT', 'PCM_TVBCM', 'SPOT_NA', 'SPOT_REF', 'SPOT_TVBCM', 'SPOT_TMH']


def load_const(t, name):
    key = 'const %s = ' % name
    start = t.find(key)
    if start < 0:
        raise SystemExit('ERR cannot find const %s' % name)
    start += len(key)
    return json.loads(t[start:t.index(';\r\n', start)])


def swap_const(t, name, obj):
    start = t.index('const %s = ' % name)
    end = t.index(';\r\n', start) + 1
    body = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    if ';\r\n' in body:
        raise SystemExit('ERR payload for %s would break the line anchor' % name)
    return t[:start] + 'const %s = %s;' % (name, body) + t[end:]


def nk(x):
    return re.sub(r'[^A-Z0-9]', '', str(x).upper())


def resolver(indic):
    byname, bydc, bycode = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for i, u in enumerate(indic['ucs']):
        byname[(u[1], nk(u[0]))].append(i)
        bydc[(u[1], str(u[3]))].append(i)
        bycode[str(u[3])].append(i)

    def locate(d, u, code=''):
        cand = byname.get((d, nk(u))) or []
        if len(cand) == 1:
            return cand[0], 'name'
        if code:
            same = [i for i in (bycode.get(str(code)) or []) if indic['ucs'][i][1] == d]
            if len(same) == 1:
                return same[0], 'code'
        if cand:
            return cand[0], 'name-dup'
        if code:
            anyc = bycode.get(str(code)) or []
            if len(anyc) == 1:
                return anyc[0], 'code'
        raise SystemExit('ERR UC %s/%s (%s) does not resolve to one register row' % (d, u, code))
    return locate


def dindex(indic, name):
    hit = [i for i, x in enumerate(indic['dn']) if nk(x) == nk(name)]
    if len(hit) != 1:
        raise SystemExit('ERR district %r is not one entry of INDIC.dn' % name)
    return hit[0]


def pct(p, n, dp=1):
    return round(100.0 * p / n, dp) if n else 0.0


def rollup(rows, ncols, pj, num, den):
    """District rows: counts summed, the % column recomputed from its own counts.

    A column the export does not report (-1 in every UC row) stays -1 at district level,
    so a dash never turns into a zero on the way up.
    """
    g = collections.defaultdict(lambda: [0] * ncols)
    seen = collections.defaultdict(lambda: [0] * ncols)
    for di, vals in rows:
        a, s = g[di], seen[di]
        for j in range(ncols):
            if j == pj or vals[j] == -1:
                continue
            a[j] += vals[j]
            s[j] += 1
    for di, a in g.items():
        for j in range(ncols):
            if j != pj and not seen[di][j]:
                a[j] = -1
        a[pj] = pct(a[num], a[den])
    return dict((str(di), a) for di, a in g.items())


def read_ms(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = [list(r) for r in wb['Sheet0'].iter_rows(values_only=True)]
    wb.close()
    out = []
    for r in rows[2:]:
        if not r[0] or not r[2] or not str(r[2]).strip():
            continue  # the trailing 'Total' row
        n = lambda i: int(r[i]) if isinstance(r[i], (int, float)) else 0
        out.append({'d': str(r[2]).strip(), 't': str(r[3]).strip(), 'u': str(r[4]).strip(),
                    'c': str(r[5]).strip() if r[5] is not None else '', 'camp': str(r[0]).strip(),
                    'n': n(6), 'chk': n(7), 'ver': n(8), 'ms': n(10),
                    'nt': n(11), 'ntc': n(12), 'na': n(13), 'rf': n(14), 'ot': n(15)})
    return out


def main():
    write = '--write' in sys.argv
    t = open(PATH, encoding='utf-8', newline='').read()
    indic = load_const(t, 'INDIC')
    pkx = load_const(t, 'PKX')
    locate = resolver(indic)

    import extract_pcm
    camp_pcm = extract_pcm.read_campaign_pcm(PCM_PATH)
    camp = camp_pcm[0]['camp']
    if {str(x['camp']).strip() for x in camp_pcm} != {camp}:
        raise SystemExit('ERR the PCM workbook mixes campaigns')

    # ---------------- market survey ----------------
    ms = read_ms(MS_PATH)
    ms_uu, ms_rows, seen = [], [], set()
    for x in ms:
        di = dindex(indic, x['d'])
        ix, how = locate(di, x['u'], x['c'])
        if ix in seen:
            raise SystemExit('ERR two market-survey rows land on one UC: %s %s' % (x['d'], x['u']))
        seen.add(ix)
        vals = [x['n'], x['chk'], x['ver'], pct(x['ver'], x['chk']),
                x['ms'], x['nt'], x['ntc'], x['na'], x['rf'], -1, -1]
        ms_rows.append((di, vals))
        ms_uu.append([ix, vals])
    ms_uu.sort(key=lambda r: r[0])
    ms_dd = rollup(ms_rows, len(indic['S']['ms']['k']), 3, 2, 1)
    ms_tot = lambda k: sum(x[k] for x in ms)
    if (len(ms), len(ms_dd), ms_tot('n'), ms_tot('chk'), ms_tot('ver'), ms_tot('ms')) != (85, 25, 103, 6739, 6205, 534):
        raise SystemExit('ERR market-survey grain or totals moved from the profiled workbook')
    if sum(ms_tot(k) for k in ('nt', 'ntc', 'na', 'rf', 'ot')) != ms_tot('ms'):
        raise SystemExit('ERR the market-survey reason buckets no longer add to the missed total')

    # ---------------- PCM ----------------
    pc_uu, pc_rows, seen = [], [], set()
    for x in camp_pcm:
        di = dindex(indic, x['d'])
        ix, how = locate(di, x['u'])
        if ix in seen:
            raise SystemExit('ERR two PCM rows land on one UC: %s %s' % (x['d'], x['u']))
        seen.add(ix)
        vals = [-1, x['chk'], x['fm'], pct(x['fm'], x['chk']),
                x['na'], x['rf'], x['nt'], x['tv'], -1, -1, -1, -1]
        pc_rows.append((di, vals))
        pc_uu.append([ix, vals])
    pc_uu.sort(key=lambda r: r[0])
    pc_dd = rollup(pc_rows, len(indic['S']['pcm']['k']), 3, 2, 1)

    # prove the pack against the const PCM payload the Monitoring analysis tab reads
    pay = json.load(open(os.path.join(HERE, 'out', 'pcm.json'), encoding='utf-8'))
    di = [i for i, d in enumerate(pay['ds']) if d['s'] == 1 and d['q'] == 'Nov 26']
    if len(di) != 1:
        raise SystemExit('ERR out/pcm.json carries %d Nov-26 PCM datasets' % len(di))
    rows = [r for r in pay['r'] if r[0] == di[0]]
    psum = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        k = [i for i, x in enumerate(indic['dn']) if nk(x) == nk(r[1])][0]
        psum[k][0] += r[7] or 0
        psum[k][1] += r[8] or 0
        psum[k][2] += r[9] or 0
    for k, v in psum.items():
        mine = pc_dd[str(k)]
        if [v[0], v[1], v[2]] != [mine[1], mine[2], mine[4] + mine[5] + mine[6] + mine[7]]:
            raise SystemExit('ERR district %s disagrees with const PCM: %s vs %s'
                             % (indic['dn'][k], v, mine))
    pc_tot = lambda k: sum(x[k] for x in camp_pcm)
    if (len(pc_uu), len(pc_dd), pc_tot('chk'), pc_tot('fm'), pc_tot('ms')) != (82, 8, 4921, 4728, 193):
        raise SystemExit('ERR PCM grain or totals moved from the profiled workbook')

    # ---------------- the entries ----------------
    ms_note = ('added from the EOC portal market-survey export, UC wise, read %s (MS.xlsx, '
               '%s); one row per UC carrying that UC\'s survey count; district rows sum the UC '
               'rows and their percentages are recomputed from those counts; the export\'s four '
               'named reasons leave its "Other" bucket (%s children) inside the missed total; it '
               'has no child-asleep column and its two extra "other reason" columns (mark washed '
               'away, mark not applied - both 0 this round) are outside the compiled series, so '
               'asleep and VBNFM print "-".'
               % (READ, camp, sum(x['ot'] for x in ms)))
    pc_note = ('added from the post-campaign monitoring workbook read %s (PCM - SNID Nov 2026.xlsx, '
               'sheet PCM), reconciled with the Monitoring analysis tab row for row; one row per '
               'monitored UC; district rows sum the UC rows and their percentages are recomputed '
               'from those counts; the export carries no survey count and no spot-check columns, so '
               'those print "-"; "Team did not visit" is the house-level bucket and "Team missed '
               'child" the child-level one.' % READ)
    pcm = [x for x in pkx.get('pcm', []) if nk(x['camp']['l']) != nk(camp)]
    mse = [x for x in pkx.get('ms', []) if nk(x['camp']['l']) != nk(camp)]
    pkx['ms'] = [{'camp': {'l': camp, 'y': camp[-4:], 'ip': 1}, 'dd': ms_dd, 'uu': ms_uu, 'ud': 1,
                  'note': ms_note}] + mse
    pkx['pcm'] = [{'camp': {'l': camp, 'y': camp[-4:], 'ip': 1}, 'dd': pc_dd, 'uu': pc_uu, 'ud': 1,
                   'note': pc_note}] + pcm

    t = swap_const(t, 'PKX', pkx)
    if load_const(t, 'PKX') != pkx:
        raise SystemExit('ERR const PKX round trip failed')
    old_pcm = load_const(t, 'PCM')
    if old_pcm != pay:
        t = swap_const(t, 'PCM', pay)
        if load_const(t, 'PCM') != pay:
            raise SystemExit('ERR const PCM round trip failed')
    if t.count('\r\n') != t.count('\n'):
        raise SystemExit('ERR line endings')

    print('ms : %d UC rows, %d districts, %d surveys, %d checked, %d verified, %d missed'
          % (len(ms_uu), len(ms_dd), ms_tot('n'), ms_tot('chk'), ms_tot('ver'), ms_tot('ms')))
    print('pcm: %d UC rows, %d districts, %d checked, %d FM, %d missed - equals const PCM district for district'
          % (len(pc_uu), len(pc_dd), pc_tot('chk'), pc_tot('fm'), pc_tot('ms')))
    print('PKX bytes %d -> %d' % (len(open(PATH, encoding='utf-8', newline='').read()), len(t)))
    if not write:
        print('DRY RUN - nothing written')
        return
    open(PATH, 'w', encoding='utf-8', newline='').write(t)
    print('WROTE', PATH)


if __name__ == '__main__':
    main()
