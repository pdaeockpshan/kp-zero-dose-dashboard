"""Harvest VAL/VCH/VUC/VCAMP from the legacy pipeline's rebuilt internal page.

The pipeline emits only the internal build (names in VCH). The public VCH is
derived from it: drop nm/fn, blank cd/mo. The rule is asserted against the
non-Nov rows the live public build already carries before anything is written.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch as dp  # noqa: E402

LEGACY = r'C:\Users\HD\Downloads\ZD_Dashboard\Zero_Dose_Digitization_Dashboard.html'
PUBLIC_CONSTS = ('VAL', 'VUC', 'VCAMP')
NOV = 'SNID November 2026'


def ser(o):
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')


def publicize(rows):
    out = []
    for r in rows:
        q = {k: v for k, v in r.items() if k not in ('nm', 'fn')}
        q['cd'] = ''
        q['mo'] = ''
        out.append(q)
    return out


def main(write):
    src = open(LEGACY, encoding='utf-8', newline='').read()
    rebuilt = {n: json.loads(dp.get_payload(src, n)) for n in ('VAL', 'VCH', 'VUC', 'VCAMP')}
    vch_internal = rebuilt['VCH']
    vch_public = publicize(vch_internal)

    cfg, vs = dp.load_variants()
    live_internal = json.loads(dp.get_payload(
        open(os.path.join(cfg['repo'], 'Zero_Dose_Digitization_Dashboard.html'),
             encoding='utf-8', newline='').read(), 'VCH'))
    live_public_nov = [r for r in publicize(live_internal) if r['cp'] == NOV]
    print('internal live Nov rows %d (rebuild %d)' % (len(live_public_nov), len([r for r in vch_public if r['cp'] == NOV])))

    for v in vs:
        if v.rel.endswith('Zero_Dose_Digitization_Dashboard.html'):
            continue
        live = [r for r in json.loads(dp.get_payload(v.text, 'VCH')) if r['cp'] != NOV]
        der = [r for r in vch_public if r['cp'] != NOV]
        v.require(live == der, 'public VCH derivation differs on non-Nov rows')
    assert not any('nm' in r or 'fn' in r for r in vch_public), 'names left in public VCH'
    assert not any(r['cd'] or r['mo'] for r in vch_public), 'cd/mo left in public VCH'

    for v in vs:
        internal = v.rel.endswith('Zero_Dose_Digitization_Dashboard.html')
        for n in PUBLIC_CONSTS:
            dp.swap_payload(v, n, ser(rebuilt[n]))
        ch = vch_internal if internal else vch_public
        dp.swap_payload(v, 'VCH', ser(ch))
        print('%-46s VCH rows %5d' % (v.rel, len(ch)))
        dp.assert_crlf(v)

    if not write:
        print('dry run - nothing written')
        return
    dp.check_identical(cfg, vs)
    dp.write_variants(vs)
    print('written')


if __name__ == '__main__':
    main('--write' in sys.argv)
