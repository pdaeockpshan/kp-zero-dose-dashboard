"""One-shot: fill the plate's ICM Total Missed column from the ICM HH-cluster read.

The compiled Sept sheet carries only ICM Team No Visit / ICM TVBCM on its district tab and,
on its UC tab, an "ICM Total Missed" column that repeats Team No Visit in all 1 402 rows - so
the plate has never had a real district-grain ICM total (it printed -1 and dropped the column).

The ICM payload behind the Campaign-overview ICM card (`PKX.icm`, entry SNID Sept 2026) is the
round's household-cluster read: every district's total equals its own reason columns summed
(NT + TVBCM + NA + REF + Sleep + Others), 22 396 across 37 districts. That total is copied to
the plate's district grain; the UC grain is set to -1 (not reported) rather than republishing
the duplicated column, so the plate drops it at UC grain and the caption says why.
"""
import io
import json
import re

P = 'index.html'
t = io.open(P, encoding='utf-8', newline='').read()
assert t.count('\r\n') == t.count('\n'), 'CRLF already damaged'


def payload(name):
    m = re.search(r'const ' + name + r' = ', t)
    i = m.end()
    j = t.index(';\r\n', i)
    return json.loads(t[i:j])


def swap(name, obj):
    global t
    m = re.search(r'const ' + name + r' = ', t)
    i = m.end()
    j = t.index(';\r\n', i)
    old = t[i:j]
    assert old == json.dumps(json.loads(old), separators=(',', ':'), ensure_ascii=False), name + ' round-trip'
    t = t[:i] + json.dumps(obj, separators=(',', ':'), ensure_ascii=False) + t[j:]


CIN = payload('CIN')
PKX = payload('PKX')
BEFORE = json.loads(json.dumps(CIN))

assert [c[0] for c in CIN['k']][7:11] == ['ICM Recall %', 'ICM Total Missed', 'ICM Team No Visit', 'ICM TVBCM']
assert CIN['camp']['l'] == 'SNID Sept 2026'

sept = [e for e in PKX['icm'] if e['camp']['l'] == 'SNID Sept 2026']
assert len(sept) == 1, 'PKX has no single SNID Sept 2026 ICM entry'
sept = sept[0]

assert set(sept['dd']) == set(CIN['dd']), 'district keys differ between PKX and CIN'
for k, v in sept['dd'].items():
    s = sum(v[i] for i in range(5, 11) if v[i] > -1)
    assert s == v[4], ('reason identity broken', k, v[4], s)
    assert len(CIN['dd'][k]) == 18, (k, len(CIN['dd'][k]))

# The UC tab's "ICM Total Missed" is the NT column repeated; prove that before clearing it.
dup = [p for p in CIN['uu'] if p[1][8] != p[1][9]]
assert not dup, ('UC total is not a clean duplicate of NT', dup[:3])

total = 0
for k, v in sept['dd'].items():
    CIN['dd'][k][8] = v[4]
    total += v[4]
assert total == 22396, total
for pr in CIN['uu']:
    pr[1][8] = -1

swap('CIN', CIN)
assert t.count('\r\n') == t.count('\n'), 'CRLF damaged'
io.open(P, 'w', encoding='utf-8', newline='').write(t)

# Re-read and prove the swap touched index 8 only.
t2 = io.open(P, encoding='utf-8', newline='').read()
C2 = payload('CIN')
for k, v in C2['dd'].items():
    old = BEFORE['dd'][k]
    assert v[:8] == old[:8] and v[9:] == old[9:], ('district row shifted', k)
assert sum(v[8] for v in C2['dd'].values()) == 22396
assert all(pr[1][8] == -1 for pr in C2['uu'])
for i, pr in enumerate(C2['uu']):
    old = BEFORE['uu'][i][1]
    assert pr[1][:8] == old[:8] and pr[1][9:] == old[9:], ('UC row shifted', i)
print('ok: 37 districts carry the ICM total, 22,396 summed; 1,402 UC rows now read not reported')
