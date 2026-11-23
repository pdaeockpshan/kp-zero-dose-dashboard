# -*- coding: utf-8 -*-
"""Fit both A4 sheets back inside one page after the Nov-26 additions.

Widens the text column (13mm -> 11mm side margins), trims vertical rhythm,
and fixes two December timing details in the district brief.
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

PATH = 'index.html'
raw = open(PATH, encoding='utf-8', newline='').read()
assert '\r\n' in raw, 'expected CRLF'
s = raw.replace('\r\n', '\n')
assert '\r' not in s, 'lone CR in source'
orig_len = len(s)


def rep(old, new, label, n=1):
    global s
    got = s.count(old)
    assert got == n, f'{label}: expected {n}, found {got}'
    s = s.replace(old, new, n)


# ---------------------------------------------------------------- shared sheet chrome
rep('.rb-head{background:#0a1620;color:#e8eef2;padding:6.4mm 13mm 5.2mm;',
    '.rb-head{background:#0a1620;color:#e8eef2;padding:6.4mm 11mm 5.2mm;',
    'head base')
rep('.rb-head h1{font:600 17.6pt/1.12 "Segoe UI",Arial,sans-serif;margin:3.2mm 0 2.2mm}',
    '.rb-head h1{font:600 16.6pt/1.1 "Segoe UI",Arial,sans-serif;margin:2.4mm 0 1.8mm}',
    'head h1')
rep('.rb-head p{font:8.3pt/1.36 "Segoe UI",Arial,sans-serif;color:#9fb3bf;margin:0;max-width:118mm}',
    '.rb-head p{font:8.1pt/1.32 "Segoe UI",Arial,sans-serif;color:#9fb3bf;margin:0;max-width:126mm}',
    'head p')
rep('.rb-head .rbr span{display:block;font:8pt/1.4 "Segoe UI",Arial,sans-serif;color:#9fb3bf;margin-top:2mm}',
    '.rb-head .rbr span{display:block;font:8pt/1.34 "Segoe UI",Arial,sans-serif;color:#9fb3bf;margin-top:1.4mm}',
    'head rbr span')
rep('.rb-kpi{flex:1 1 0;border:.35mm solid #d7e0e6;border-top:1mm solid #2f7d6d;border-radius:1mm;padding:2.1mm 2.4mm 1.9mm;background:#fbfcfd}',
    '.rb-kpi{flex:1 1 0;border:.35mm solid #d7e0e6;border-top:1mm solid #2f7d6d;border-radius:1mm;padding:1.5mm 2.2mm 1.3mm;background:#fbfcfd}',
    'kpi pad')
rep('.rb-kpi .v{font:700 14pt/1 "Segoe UI",Arial,sans-serif;color:#12212c}',
    '.rb-kpi .v{font:700 13.4pt/1 "Segoe UI",Arial,sans-serif;color:#12212c}',
    'kpi value')
rep('.rb-kpi .l{font:7.2pt/1.28 "Segoe UI",Arial,sans-serif;color:#5b6f7c;margin-top:1.6mm}',
    '.rb-kpi .l{font:7pt/1.22 "Segoe UI",Arial,sans-serif;color:#5b6f7c;margin-top:1.2mm}',
    'kpi label')
rep('.rb-round .rf{font:7.2pt/1.3 "Segoe UI",Arial,sans-serif;color:#6b7f8b;margin-top:1.2mm}',
    '.rb-round .rf{font:7.2pt/1.28 "Segoe UI",Arial,sans-serif;color:#6b7f8b;margin-top:1mm}',
    'round foot')
rep('.rb-tbl td{border-bottom:.25mm solid #e3e9ed;padding:1.15mm 2mm 1.15mm 0;vertical-align:top}',
    '.rb-tbl td{border-bottom:.25mm solid #e3e9ed;padding:.9mm 2mm .9mm 0;vertical-align:top}',
    'tbl td pad')
rep('.rb-find .t{font:8.3pt/1.38 "Segoe UI",Arial,sans-serif;margin:0;color:#243642}',
    '.rb-find .t{font:8.1pt/1.32 "Segoe UI",Arial,sans-serif;margin:0;color:#243642}',
    'find text')
rep('.rb-find{display:flex;gap:4mm;align-items:flex-start;margin-bottom:2.2mm}',
    '.rb-find{display:flex;gap:4mm;align-items:flex-start;margin-bottom:1.6mm}',
    'find margin')
rep('.rb-blk{font:7.8pt/1.36 "Segoe UI",Arial,sans-serif;color:#334750}',
    '.rb-blk{font:7.6pt/1.3 "Segoe UI",Arial,sans-serif;color:#334750}',
    'blk font')
rep('.rb-blk h4{font:700 8.2pt "Segoe UI",Arial,sans-serif;margin:0 0 1.4mm;color:#12212c}',
    '.rb-blk h4{font:700 8.2pt "Segoe UI",Arial,sans-serif;margin:0 0 1mm;color:#12212c}',
    'blk h4')
rep('.rb-note{margin:2.2mm 0 0;font:7.6pt/1.32 "Segoe UI",Arial,sans-serif;color:#5b6f7c}',
    '.rb-note{margin:1.6mm 0 0;font:7.4pt/1.28 "Segoe UI",Arial,sans-serif;color:#5b6f7c}',
    'note')
rep('.rb-cav{margin:3.2mm 13mm 0;background:#fff6e5;border-left:1mm solid #e8a33d;color:#7a5318;font:7.7pt/1.34 "Segoe UI",Arial,sans-serif;padding:2.4mm 3mm}',
    '.rb-cav{margin:3.2mm 11mm 0;background:#fff6e5;border-left:1mm solid #e8a33d;color:#7a5318;font:7.5pt/1.3 "Segoe UI",Arial,sans-serif;padding:1.9mm 2.8mm}',
    'cav base')
rep('.rb-src{margin:1.6mm 13mm 0;font:6.9pt/1.38 "Segoe UI",Arial,sans-serif;color:#6b7f8b}',
    '.rb-src{margin:1.4mm 11mm 0;font:6.7pt/1.32 "Segoe UI",Arial,sans-serif;color:#6b7f8b}',
    'src base')
rep('.rb-foot{position:absolute;left:13mm;right:13mm;bottom:5mm;',
    '.rb-foot{position:absolute;left:11mm;right:11mm;bottom:4mm;',
    'foot')

# ---------------------------------------------------------------- province sheet overrides
rep('#p-rbrief .rb-head{padding:4.8mm 13mm 3.6mm}',
    '#p-rbrief .rb-head{padding:4mm 11mm 2.8mm}',
    'rb head')
rep('#p-rbrief .rb-kpis{padding-top:2.6mm}',
    '#p-rbrief .rb-kpis{padding-top:2mm}',
    'rb kpis')
rep('#p-rbrief .rb-sec{padding-top:2.8mm}',
    '#p-rbrief .rb-sec{padding-top:2.1mm}',
    'rb sec')
rep('#p-rbrief .rb-h{padding-bottom:1mm;margin-bottom:1.6mm}',
    '#p-rbrief .rb-h{padding-bottom:.8mm;margin-bottom:1.2mm}',
    'rb h')
rep('#p-rbrief .rb-note{margin-top:1.5mm}',
    '#p-rbrief .rb-note{margin-top:1.1mm}',
    'rb note')
rep('#p-rbrief .rb-cav{margin-top:2mm;padding:1.8mm 3mm}',
    '#p-rbrief .rb-cav{margin-top:1.2mm;padding:1.5mm 2.8mm}',
    'rb cav')
rep('#p-rbrief .rb-src{margin-top:1.1mm}',
    '#p-rbrief .rb-src{margin-top:.7mm}',
    'rb src')

# ---------------------------------------------------------------- district sheet overrides
rep('#p-pdis .rb-head{padding:5mm 13mm 3mm}',
    '#p-pdis .rb-head{padding:4.2mm 11mm 2.6mm}',
    'pd head')
rep('#p-pdis .rb-kpi{padding:1.4mm 2.2mm 1.3mm}',
    '#p-pdis .rb-kpi{padding:1.2mm 2mm 1.1mm}',
    'pd kpi')
rep('#p-pdis .rb-sec{padding:1.9mm 13mm 0}',
    '#p-pdis .rb-sec{padding:1.5mm 11mm 0}',
    'pd sec')
rep('#p-pdis .rb-kpis{padding-top:2.2mm}',
    '#p-pdis .rb-kpis{padding-top:1.8mm}',
    'pd kpis')
rep('#p-pdis .rb-h{margin-bottom:1.5mm;padding-bottom:.9mm}',
    '#p-pdis .rb-h{margin-bottom:1.1mm;padding-bottom:.7mm}',
    'pd h')
rep('#p-pdis .rb-cav{font-size:7pt;line-height:1.26;margin-top:.9mm;padding:1.3mm 3mm}',
    '#p-pdis .rb-cav{font-size:7pt;line-height:1.26;margin-top:.6mm;padding:1.1mm 2.6mm}',
    'pd cav')
rep('#p-pdis .rb-src{font-size:6.4pt;line-height:1.3;margin-top:.9mm}',
    '#p-pdis .rb-src{font-size:6.4pt;line-height:1.28;margin-top:.6mm}',
    'pd src')
rep('.pd-reg{border-left:1mm solid #e8a33d;background:#fff8ec;padding:1.9mm 3mm;margin-top:2.4mm;border-radius:.6mm}',
    '.pd-reg{border-left:1mm solid #e8a33d;background:#fff8ec;padding:1.4mm 2.6mm;margin-top:1.6mm;border-radius:.6mm}',
    'pd reg')
rep('#p-pdis .pd-reg{margin-top:1.8mm}',
    '#p-pdis .pd-reg{margin-top:1.2mm}',
    'pd reg override')
rep('.pd-note{font:7.1pt/1.3 "Segoe UI",Arial,sans-serif;color:#5b6f7c;margin:0}',
    '.pd-note{font:6.9pt/1.26 "Segoe UI",Arial,sans-serif;color:#5b6f7c;margin:0}',
    'pd note')

# ---------------------------------------------------------------- district sheet content
rep('5 · Decisions before the round closes', '5 · Decisions before NID Dec-26', 'pd sec5 head')
rep("w:'14 & 16 Dec'", "w:'13 & 15 Dec'", 'pd day2/4')
rep("'Re-draw the September lots that did not pass'",
    "'Carry the September lot misses into December supervision'", 'pd lq title')
rep("'. Re-sample rather than accept.'", "'. Those UCs go first in December.'", 'pd lq tail')
rep("a.push({t:'Re-check the intermediate LQAS lots in the watch UCs',\n      b:'Re-sample the lots that came back intermediate rather than accept them.',o:'WHO Area Coordinator',w:'14 Dec',m:'All re-drawn lots pass'});",
    "a.push({t:'Draw fresh lots in the UCs whose September lots came back intermediate',\n      b:'The December round should re-test those UCs rather than inherit the September reading.',o:'WHO Area Coordinator',w:'16 Dec',m:'Lots drawn in those UCs'});",
    'pd lq interim')
rep("o:'WHO Area Coordinator',w:'14 Dec',m:'All re-drawn lots pass'}",
    "o:'WHO Area Coordinator',w:'Before 12 Dec',m:'Those UCs supervised on day 1'}", 'pd lq date')
rep("b:'No September lot returned for this district, so the round has no independent coverage check.'",
    "b:'No September LQAS lot returned for this district, so September has no independent coverage check.'", 'pd lq none')
rep("Sept-26 covered figures stay the round's own self-report throughout.",
    "Sept-26 covered figures stay the round's own self-report; the SNID Nov-26 close-out is read on its own UC table until a covered figure arrives.",
    'pd hint')

# ---------------------------------------------------------------- checks
for gone in ['13mm 13mm', '.rb-head{padding:6.4mm 13mm', 'padding:2.1mm 2.4mm 1.9mm',
             'w:14 & 16 Dec', 'Re-draw the September lots']:
    assert gone not in s, f'leftover: {gone}'
for need in ['padding:4mm 11mm 2.8mm', 'padding:4.2mm 11mm 2.6mm', '5 · Decisions before NID Dec-26',
             "13 & 15 Dec", 'Carry the September lot misses']:
    assert need in s, f'missing: {need}'

out = s.replace('\n', '\r\n')
assert '\n' not in out.replace('\r\n', ''), 'lone LF in output'
assert out.count('\r\n') == s.count('\n')
open(PATH, 'w', encoding='utf-8', newline='').write(out)
print('patched', PATH, orig_len, '->', len(out))
