"""One-shot: add the LQAS Total Missed column to the campaign indicators plate.

The compiled sheet and the live Nov sheet carry only LQAS_NT and LQAS_TVBMC, so the
total is taken from the E-LQAS UC-wise lot export (LQR), whose `tt` Grand Total is
proved equal to the sum of the seven missed-child reasons.  Values land at index 15,
immediately before LQAS_NT, at both grains; a district or UC the sample did not reach
is -1 (not reported), never 0.  CINN shares CIN's column list.

Also drops the "(in progress)" suffix from the SNID Nov 2026 campaign label in CINN
and in the two PKX admin/icm camp objects: the round has concluded.
"""
import json, re
from collections import defaultdict

P = 'index.html'
t = open(P, encoding='utf-8', newline='').read()


def payload(name, text):
    m = re.search(r'const ' + name + r' = ', text)
    i = m.end()
    j = text.index(';\r\n', i)
    return text[i:j], json.loads(text[i:j])


def swap(name, obj, text):
    m = re.search(r'const ' + name + r' = ', text)
    i = m.end()
    j = text.index(';\r\n', i)
    assert text[i:j] == json.dumps(json.loads(text[i:j]), separators=(',', ':'), ensure_ascii=False), name + ' round-trip'
    out = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    return text[:i] + out + text[j:]


_, CIN = payload('CIN', t)
_, CINN = payload('CINN', t)
_, INDIC = payload('INDIC', t)
_, INDA = payload('INDA', t)
_, LQR = payload('LQR', t)
_, PKX = payload('PKX', t)

BEFORE = {'CIN': json.loads(json.dumps(CIN)), 'CINN': json.loads(json.dumps(CINN))}

DN = INDIC['dn'] + INDA['dn']
UCS = INDIC['ucs'] + INDA['ucs']


def resolve(D, ci):
    """LQR lot row -> CIN UC-row index: exact code first, then district+UC name."""
    bycode = defaultdict(list)
    byname = defaultdict(list)
    for pr in D['uu']:
        u = UCS[pr[0]]
        bycode[u[3]].append(pr[0])
        byname[(DN[u[1]], u[0].strip().upper())].append(pr[0])
    out = {}
    for x in LQR:
        if x['ci'] != ci:
            continue
        cand = bycode.get(x['c'], [])
        if len(cand) != 1:
            cand = byname.get((x['d'], x['u'].strip().upper()), [])
        if len(cand) != 1:
            raise SystemExit('unresolved lot %r' % (x,))
        out[cand[0]] = x['tt']
    return out


def build(D, ci, expect_total):
    ucval = resolve(D, ci)
    dsum = defaultdict(int)
    dseen = set()
    for pr in D['uu']:
        if pr[0] in ucval:
            di = UCS[pr[0]][1]
            dsum[di] += ucval[pr[0]]
            dseen.add(di)
    assert sum(ucval.values()) == expect_total, (sum(ucval.values()), expect_total)
    distval = {int(di): (dsum[int(di)] if int(di) in dseen else -1) for di in D['dd']}
    assert sum(v for v in distval.values() if v > -1) == expect_total
    return ucval, distval


def apply(D, ci, expect_total, has_k):
    ucval, distval = build(D, ci, expect_total)
    if has_k:
        K = D['k']
        assert len(K) == 17 and K[15][0] == 'LQAS_NT', [c[0] for c in K[13:]]
        K.insert(15, ['LQAS Total Missed', 'n'])
    for di, v in D['dd'].items():
        assert len(v) == 17, (di, len(v))
        v.insert(15, distval[int(di)])
    for pr in D['uu']:
        assert len(pr[1]) == 17, (pr[0], len(pr[1]))
        pr[1].insert(15, ucval.get(pr[0], -1))
    print('%s: %d lots, total %d, %d districts with lots'
          % (D['camp']['l'], len(ucval), sum(ucval.values()),
             sum(1 for v in distval.values() if v > -1)))


apply(CIN, 1, 210, True)      # SNID Sept 2026 == LQR ci 1
apply(CINN, 0, 157, False)    # SNID Nov 2026  == LQR ci 0

assert CINN['camp']['l'] == 'SNID Nov 2026 (in progress)'
CINN['camp']['l'] = 'SNID Nov 2026'


def relabel(o):
    if isinstance(o, dict):
        return {k: ('SNID Nov 2026' if v == 'SNID Nov 2026 (in progress)' else relabel(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [relabel(v) for v in o]
    return o


PKX = relabel(PKX)
assert PKX['admin'][0]['camp']['l'] == 'SNID Nov 2026'
assert PKX['icm'][0]['camp']['l'] == 'SNID Nov 2026'

t = swap('CIN', CIN, t)
t = swap('CINN', CINN, t)
t = swap('PKX', PKX, t)
assert t.count('\r\n') == t.count('\n'), 'CRLF damaged'
open(P, 'w', encoding='utf-8', newline='').write(t)

# re-read, then prove the insert shifted nothing and both grains total the export
t2 = open(P, encoding='utf-8', newline='').read()
_, C2 = payload('CIN', t2)
_, N2 = payload('CINN', t2)
assert [c[0] for c in C2['k']][13:18] == [
    'Fail', 'LQAS Pass %', 'LQAS Total Missed', 'LQAS_NT', 'LQAS_TVBMC']
for name, D, exp in (('CIN', C2, 210), ('CINN', N2, 157)):
    B = BEFORE[name]
    for di, v in D['dd'].items():
        old = B['dd'][di]
        assert v[:15] == old[:15] and v[16:] == old[15:], (name, di)
    for i, pr in enumerate(D['uu']):
        old = B['uu'][i][1]
        assert pr[1][:15] == old[:15] and pr[1][16:] == old[15:], (name, i)
    assert all(len(v) == 18 for v in D['dd'].values())
    assert all(len(pr[1]) == 18 for pr in D['uu'])
    assert sum(v[15] for v in D['dd'].values() if v[15] > -1) == exp
    assert sum(pr[1][15] for pr in D['uu'] if pr[1][15] > -1) == exp
print('ok: district and UC grain both total 210 (Sept) and 157 (Nov), old columns intact')
