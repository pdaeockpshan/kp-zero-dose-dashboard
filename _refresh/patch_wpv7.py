"""Add the 7th confirmed WPV1 case of 2026 (KP/34/26/159) to the dashboard payloads.

Source: `afp_cases_sampling (5).xls`, the EOC "LINE LIST of WPVs" export downloaded
08-Nov-2026 (portal surveillance data updated 06-Nov-2026). Seven KP rows, one of them new:
Mastak UC, Bara tehsil, Khyber, onset 16-Oct-2026, male, 7 months. The 28-Oct line list
already carries the AFP record (KHYBER, onset 2026-10-16) as pending, so in the AFP master
this is a pending -> WPV1 move, not a new case.

Edits, all idempotent-guarded on the pre-state:
  * WPV / WPVH        insert the case (UC code 33401112, centroid [155.9, 303.4])
  * KSOC 2026         cases 6->7, male 2->3, <2yr 4->5, Pashto 6->7 (districts stay 3)
  * AMETA             wlast 16-Oct-26, wasof 2026-11-06 (the 08-Oct ZD-list asof is untouched)
  * AFPD 2026         c1 6->7, cw 6->7, cp 309->308, KP and KHYBER, plus the KHYBER
                      month cells (Sep c1/cw 1->2 - the line already held both Sep cases
                      but the monthly cut carried one; Oct +1 for the new onset)
No dose history is in the export (the OPV-dose columns are blank for every row), so the
zero-dose flags stay as they were: zw 1, the new case zd=false.

Run from the repo root: python _refresh/patch_wpv7.py
"""
import json
import os
import sys

P = 'index.html'
s = open(P, encoding='utf-8', newline='').read()
before = len(s)


def sub(text, old, new, count=1):
    n = text.count(old)
    assert n == count, 'expected %d got %d for %r' % (count, n, old[:70])
    return text.replace(old, new, count)


NEW = ('{"dv": "PESHAWAR", "d": "KHYBER", "t": "BARA", "u": "MASTAK", "c": "33401112", '
       '"mo": "2026-10", "on": "2026-10", "m": "exact", "pt": [155.9, 303.4], "ag": 7, '
       '"sx": "M", "ty": "WPV1", "zd": false}, ')

assert 'MASTAK", "c": "33401112", "mo": "2026-10"' not in s, 'case already present'
s = sub(s, 'const WPV = [', 'const WPV = [' + NEW)
s = sub(s, 'const WPVH = [', 'const WPVH = [{"dv": "PESHAWAR", "d": "KHYBER", "t": "BARA", '
        '"u": "MASTAK", "c": "33401112", "on": "2026-10"}, ')

s = sub(s, '{y:2026,dist:3,cases:6,m:2,f:4,lt2:4,zrd:0,ref:0,pas:6}',
        '{y:2026,dist:3,cases:7,m:3,f:4,lt2:5,zrd:0,ref:0,pas:7}')

s = sub(s, '"last": "16-Sep-26", ',
        '"last": "16-Sep-26", "wlast": "16-Oct-26", "wasof": "2026-11-06", ')

s = sub(s, "${esc(AMETA.last||_moL(WPV.map(r=>r.mo).sort().pop()))}</b>",
        "${esc(AMETA.wlast||AMETA.last||_moL(WPV.map(r=>r.mo).sort().pop()))}</b>")
s = sub(s, "${AMETA.asof?' as of '+esc(AMETA.asof):''}",
        "${(AMETA.wasof||AMETA.asof)?' as of '+esc(AMETA.wasof||AMETA.asof):''}")
s = sub(s, "esc(AMETA.last||AMETA.wlast||", "esc(AMETA.wlast||AMETA.last||")
s = sub(s, "' cases \u00b7 portal line list '+AMETA.asof", "' cases \u00b7 portal line list '+(AMETA.wasof||AMETA.asof)")

s = sub(s, 'AFP surveillance: master case database to 03-Nov-2026, line list to 28-Oct-2026, weekly log and sewage to 21-Oct-2026',
        'AFP surveillance: master case database to 03-Nov-2026, line list to 28-Oct-2026, WPV line list to 06-Nov-2026, weekly log and sewage to 21-Oct-2026')

# --- AFPD aggregates (decode/re-encode is byte-exact for this payload) ---
key = 'const AFPD = '
i = s.index(key)
st = i + len(key)
afpd, end = json.JSONDecoder().raw_decode(s, st)
assert json.dumps(afpd, ensure_ascii=False) == s[st:end], 'AFPD re-encode is not byte-exact'

k = afpd['k']
I = {name: j for j, name in enumerate(k)}
y26 = afpd['y']['2026']
assert afpd['y']['2026'][I['c1']] == 6 and afpd['y']['2026'][I['cp']] == 309, 'unexpected KP totals'
kh = afpd['dy']['KHYBER'][4]
assert kh[I['c1']] == 2 and kh[I['cp']] == 19, 'unexpected KHYBER totals'

y26[I['c1']] = 7
y26[I['cw']] = 7
y26[I['cp']] = 308
kh[I['c1']] = 3
kh[I['cw']] = 3
kh[I['cp']] = 18

mm = afpd['mm']['KHYBER'][4]
assert mm[I['c1']][8] == 1 and mm[I['c1']][9] == 0, 'unexpected KHYBER monthly c1'
mm[I['c1']][8] = 2          # both September onsets (13 and 16 Sep) in the monthly cut
mm[I['c1']][9] = 1          # 16-Oct onset
mm[I['cw']][8] = 2
mm[I['cw']][9] = 1

assert sum(v[4][I['c1']] for v in afpd['dy'].values()) == 7
assert sum(v[4][I['cp']] for v in afpd['dy'].values()) == 308
s = s[:st] + json.dumps(afpd, ensure_ascii=False) + s[end:]

tmp = P + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
os.replace(tmp, P)
print('patched %s: %d -> %d bytes (+%d)' % (P, before, len(s), len(s) - before))
