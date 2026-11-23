# -*- coding: utf-8 -*-
"""Relabel the 18-Nov validation block from SNID Nov-26 to SNID Sept-26.

Owner direction (2026-11-23): the 2,580 children the 18-Nov combined export
files under activity 342 are SNID Sept-26 validation, not Nov-26; SNID Nov-26
validation has not started. The 342 batch therefore merges into the SNID Sep
2026 rows (33 UCs carry both batches; their counts sum) and every Synergy
surface that presented it as a Nov return is corrected.
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\HD\Documents\kp-zero-dose-dashboard\_refresh')
import dashpatch as dp  # noqa: E402

PATH = 'index.html'
INTERNAL = 'Zero_Dose_Digitization_Dashboard.html'
NOV = 'SNID November 2026'
SEP = 'SNID Sep 2026'


def ser(o):
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')


def swap(text, name, obj):
    i, e = dp.payload_span(text, name)
    return text[:i] + ser(obj) + text[e:]


def relabel_cp(rows):
    n = 0
    for r in rows:
        if r.get('cp') == NOV:
            r['cp'] = SEP
            n += 1
    return n


def merge_val(rows):
    """Merge rows that share a UC code and campaign after the relabel."""
    out, idx = [], {}
    for r in rows:
        k = (r['c'], r['cp'])
        if k not in idx:
            idx[k] = r
            out.append(r)
            continue
        g = idx[k]
        for f, v in r.items():
            if f in ('c', 'cp'):
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                g[f] = (g.get(f) or 0) + v
    return out


def main():
    raw = open(PATH, encoding='utf-8', newline='').read()
    assert '\r\n' in raw and raw.count('\n') == raw.count('\r\n'), 'master not clean CRLF'
    s = raw.replace('\r\n', '\n')

    # ---------------- payloads ----------------
    VAL = json.loads(dp.get_payload(s, 'VAL'))
    VCH = json.loads(dp.get_payload(s, 'VCH'))
    VCAMP = json.loads(dp.get_payload(s, 'VCAMP'))

    n_val = relabel_cp(VAL)
    assert n_val == 284, 'VAL Nov rows: %d' % n_val
    VAL = merge_val(VAL)
    assert len(VAL) == 1785 - 33, 'VAL rows after merge: %d' % len(VAL)

    n_vch = relabel_cp(VCH)
    assert n_vch == 596, 'VCH Nov rows: %d' % n_vch
    sep = [r for r in VAL if r['cp'] == SEP]
    assert len(sep) == 324, 'Sept UCs after merge: %d' % len(sep)
    assert sum(r['n'] for r in sep) == 3291
    assert sum(r['f'] for r in sep) == 516
    assert sum(r['vy'] for r in sep) == 3118
    assert len({r['d'] for r in sep}) == 26

    old_sep = [c for c in VCAMP if c['l'] == SEP]
    assert len(old_sep) == 1 and old_sep[0]['n'] == 711, 'Sept VCAMP entry moved'
    old_sep[0].update({'z': 'S', 'n': 3291, 'u': 324, 'fr': '11-Sep', 'to': '18-Nov-2026'})
    VCAMP = [c for c in VCAMP if c['l'] != NOV]
    assert len(VCAMP) == 7, 'VCAMP entries after merge: %d' % len(VCAMP)

    s = swap(s, 'VAL', VAL)
    s = swap(s, 'VCH', VCH)
    s = swap(s, 'VCAMP', VCAMP)

    # ---------------- prose ----------------
    def rep(old, new, label, n=1):
        nonlocal s
        got = s.count(old)
        assert got == n, '%s: expected %d, found %d' % (label, n, got)
        s = s.replace(old, new, n)

    rep('8 campaigns (NID FEB 2026 to SNID November 2026)',
        '7 campaigns (NID FEB 2026 to SNID Sep 2026)', 'campaign count', 2)

    rep(', and its validation return is coming in (2,580 children on 336 forms through 18-Nov-2026) \u00b7 click a question',
        ', and its validation return has not started \u00b7 click a question', 'home questions head')

    rep('while its validation return is coming in (2,580 children on 336 forms through 18-Nov-2026). Nov is therefore',
        'while its validation return has not started. Nov is therefore', 'home questions detail')

    rep('8 campaigns (NID FEB 2026, NID APR 2026, SNID May 2026, KP-Special-1-Jul 2026, KP Special Aug 2026, KP Special Aug-Sep 2026-3, SNID Sep 2026, SNID November 2026) \u00b7 entries 20-Jan-2026 to 18-Nov-2026. The 18-Nov-2026 combined export adds 93 SNID Nov-26 validation forms (603 children); the SNID Sep-26 rows are unchanged at 711 children on 180 forms.',
        '7 campaigns (NID FEB 2026, NID APR 2026, SNID May 2026, KP-Special-1-Jul 2026, KP Special Aug 2026, KP Special Aug-Sep 2026-3, SNID Sep 2026) \u00b7 entries 20-Jan-2026 to 18-Nov-2026. The 18-Nov-2026 combined export completes the SNID Sep-26 exercise \u2014 3,291 children on 516 forms in two activity batches; SNID Nov-26 validation has not started.',
        'validation hint')

    rep('LQAS and validation are in (2,580 children re-checked on 336 forms so far); the IDIMS card stays blank',
        'LQAS is in and validation has not started; the IDIMS card stays blank', 'zero dose hub heading')

    rep('the Nov validation return separates the two.',
        'the validation return separates the two.', 'compare note')

    rep(" const vNovR=vR.filter(r=>/nov/i.test(String(r.cp||''))), vNovN=vNovR.length?S_(vNovR,r=>r.n):null, vNovF=vNovR.length?S_(vNovR,r=>r.f):null;",
        ' const vNovN=null, vNovF=null; // SNID Nov-26 validation has not started',
        'caps chart Nov series')

    rep("; its covered figure is the post-campaign return awaited${vNovN?' and '+fmt(vNovN)+' Nov-26 children on '+fmt(vNovF)+' forms have been validated':''}. ",
        '; its covered figure is the post-campaign return awaited and its validation has not started. ',
        'caps caption')

    rep('its covered figure is the post-campaign return awaited, while its LQAS, still-missed and validation returns are in.',
        'its covered figure is the post-campaign return awaited, while its LQAS and still-missed returns are in and validation has not started.',
        'insight line')

    rep('const HZNOVRET={dig:false,val:true};', 'const HZNOVRET={dig:false,val:false};', 'HZNOVRET')
    rep("const HZNOVCP='SNID November 2026';", "const HZNOVCP='SNID Nov 2026';", 'HZNOVCP')

    rep("const R=V.filter(r=>/SNID November 2026/i.test(r.cp||'')),",
        "const R=V.filter(r=>/^SNID Sep 2026$/i.test(r.cp||'')),", 'c3 validation filter')

    rep("s:n0(VL.nuc)+' UCs, Nov 2026 validation'", "s:n0(VL.nuc)+' UCs, Sept 2026 validation'", 'c3 KPI sub')

    rep("'The covered-zero-dose column has not been compiled for this round, so no recovery rate can be quoted yet. Validation so far confirms 97.5% of checked children as vaccinated.',",
        "'The covered-zero-dose column has not been compiled for this round, so no recovery rate can be quoted yet. Sept-26 validation confirmed '+p1(VL.pct)+' of checked children as vaccinated; SNID Nov-26 validation has not started.',",
        'c3 bullet validation')

    rep("'5. Close the zero-dose loop: 43,484 recorded, no covered figure compiled, validation confirming 95.9% of the 2,580 children checked so far.',",
        "'5. Close the zero-dose loop: 43,484 recorded and no covered figure compiled; SNID Nov-26 validation has not started.',",
        'c3 action 5')

    rep("['Zero-dose validation','SNID November 2026 validation export','18-Nov-2026','UC'],",
        "['Zero-dose validation','SNID Sep 2026 validation export','18-Nov-2026','UC'],", 'c3 sources')

    rep('with LQAS and validation already in; SNID Sept-26 remains the last measured coverage.',
        'with LQAS in and validation still to start; SNID Sept-26 remains the last measured coverage.', 'hzd strip note')

    rep('it is read on its UC target, LQAS, still-missed and validation returns. Sept-26 coverage',
        'it is read on its UC target, LQAS and still-missed returns; validation has not started. Sept-26 coverage',
        'province brief caveat')

    rep("' not vaccinated), '+n0(D.nVal)+' of them in Nov-26.</div>'+",
        "' not vaccinated).</div>'+", 'province brief validate block')

    rep(", and '+n0(D.nVal)+' Nov-26 children have been validated so far.", '', 'province deck unresolved')

    rep('its LQAS, still-missed and validation returns. Sept-26 covered figures',
        'its LQAS and still-missed returns; validation has not started. Sept-26 covered figures',
        'province deck caveat')

    rep('with LQAS, still-missed and validation returns. Sept-26 coverage',
        'with LQAS and still-missed returns; validation has not started. Sept-26 coverage',
        'district brief caveat')

    rep('its covered figure is the post-campaign return still awaited; its validation return is coming in.',
        'its covered figure is the post-campaign return still awaited; its validation has not started.',
        'campaign picker note')

    rep("""  var nvr=VAL.filter(function(r){return r.d===dist&&/nov/i.test(String(r.cp||''));});
  var nval={n:sum_(nvr,function(r){return r.n;}),vy:sum_(nvr,function(r){return r.vy;}),f:sum_(nvr,function(r){return r.f;}),
    u:(function(){var s={};nvr.forEach(function(r){s[r.c]=1;});return Object.keys(s).length;})()};
  nval.p=pct_(nval.vy,nval.n);

  var D={dist:dist,div:div,stamp:stamp_(),sepLbl:sepLbl,camp:sepLbl,li:li,nov:nov,nval:nval,""",
        """  var D={dist:dist,div:div,stamp:stamp_(),sepLbl:sepLbl,camp:sepLbl,li:li,nov:nov,""",
        'pdFacts nval removal')

    rep("""function valText(D){
  var v=D.val, nv=D.nval||{n:0};
  if(!v.n&&!nv.n) return 'No zero-dose validation records have been entered for this district.';
  var out=v.n?(N(v.n)+' children shown as covered were validated across the 2026 campaigns: '+N(v.vy)+' confirmed vaccinated'+(v.vn?(', '+N(v.vn)+' not confirmed'):'')+', across '+v.u+' UCs.'):'';
  return out+(nv.n?(' SNID Nov-26 so far: '+N(nv.n)+' children on '+N(nv.f)+' forms, '+P1(nv.p)+' confirmed.'):' No SNID Nov-26 validation record yet.');
}""",
        """function valText(D){
  var v=D.val;
  if(!v.n) return 'No zero-dose validation records have been entered for this district.';
  return N(v.n)+' children shown as covered were validated across the 2026 campaigns: '+N(v.vy)+' confirmed vaccinated'+(v.vn?(', '+N(v.vn)+' not confirmed'):'')+', across '+v.u+' UCs. SNID Nov-26 validation has not started.';
}""",
        'valText')

    # ---------------- checks ----------------
    for gone in ['"cp": "SNID November 2026"', '"l": "SNID November 2026"', '2,580 children',
                 '95.9%', 'Nov-26 so far', 'D.nVal', 'nov:nov,nval']:
        assert gone not in s, 'leftover: %r' % gone
    for need in ['SNID Nov-26 validation has not started', '7 campaigns (NID FEB 2026 to SNID Sep 2026)',
                 'const HZNOVRET={dig:false,val:false}', "const HZNOVCP='SNID Nov 2026'"]:
        assert need in s, 'missing: %r' % need

    out = s.replace('\n', '\r\n')
    assert out.count('\r\n') == s.count('\n')

    # ---------------- internal VCH labels ----------------
    iraw = open(INTERNAL, encoding='utf-8', newline='').read()
    assert iraw.count('\n') == iraw.count('\r\n'), 'internal not clean CRLF'
    isrc = iraw.replace('\r\n', '\n')
    IVCH = json.loads(dp.get_payload(isrc, 'VCH'))
    n_iv = relabel_cp(IVCH)
    assert n_iv == 596, 'internal VCH Nov rows: %d' % n_iv
    isrc2 = swap(isrc, 'VCH', IVCH)
    iout = isrc2.replace('\n', '\r\n')
    assert iout.count('\r\n') == isrc2.count('\n')

    open(PATH, 'w', encoding='utf-8', newline='').write(out)
    open(INTERNAL, 'w', encoding='utf-8', newline='').write(iout)
    print('patched', PATH, len(raw), '->', len(out))
    print('patched', INTERNAL, len(iraw), '->', len(iout))


if __name__ == '__main__':
    main()
