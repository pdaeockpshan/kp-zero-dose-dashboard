# -*- coding: utf-8 -*-
"""Take the covered-share denominator at the round/scope grain, not the UC grain.

SNID Nov 2026 is recorded-only: its export's covered column is the next round's figure,
so the round must not enter a coverage denominator as "not covered". The first cut added
each reporting UC's recorded children to covRep, which also re-based NID Apr 26 (489 of its
928 UCs carry no covered figure) and SNID May 2026 (7 UCs), moving the province share from
66.1% to 66.7% - a change nobody asked for. Deciding per round and scope instead keeps every
published percentage where it was and only leaves out the rounds that report no covered
figure at all.

Run after patch_adv_nov26.py:  python _refresh/patch_covrep_scope.py [--dry-run]
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

EDITS = [
    ("if(r.uc)r.uc.forEach(function(x){if(!K.has(x.k))return;o.rep+=x.rep;o.repUc++;"
     "if(x.cov!=null){o.cov+=x.cov;o.covUc++;o.covRep+=x.rep;}});",
     "if(r.uc)r.uc.forEach(function(x){if(!K.has(x.k))return;o.rep+=x.rep;o.repUc++;"
     "if(x.cov!=null){o.cov+=x.cov;o.covUc++;}});if(o.covUc)o.covRep=o.rep;",
     1, 'agg'),
    ("(rr.uc||[]).forEach(function(x){if(!K.has(x.k))return;var o=row(UC[x.k].d);"
     "o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;o.covRep+=x.rep;}});",
     "(rr.uc||[]).forEach(function(x){if(!K.has(x.k))return;var o=row(UC[x.k].d);"
     "o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;}});"
     "Object.keys(m).forEach(function(k){var o=m[k];o.covRep=o.covUc?o.rep:0;});",
     1, 'campDistricts'),
    ("g.n++;g.rep+=x.rep||0;g.cov+=x.cov||0;if(x.cov!=null)g.covRep+=x.rep||0;",
     "g.n++;g.rep+=x.rep||0;g.cov+=x.cov||0;if(x.cov!=null)g.covUc=(g.covUc||0)+1;",
     1, 'tehsil accum'),
    ("   var tl=Object.keys(tm).map(function(k){return tm[k];})",
     "   Object.keys(tm).forEach(function(k){var g=tm[k];g.covRep=g.covUc?g.rep:0;});\r\n"
     "   var tl=Object.keys(tm).map(function(k){return tm[k];})",
     1, 'tehsil set'),
]


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    for v in vs:
        s = v.text
        for old, new, n, why in EDITS:
            hit = s.count(old)
            if hit != n:
                raise AssertionError('%s: %s anchor hit %d, expected %d' % (v.rel, why, hit, n))
            s = s.replace(old, new)
        if 'o.covRep+=x.rep' in s:
            raise AssertionError('%s: UC-grain covRep left behind' % v.rel)
        v.text = s
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    for v in vs:
        print('%-42s %+8d chars' % (v.rel, v.delta()))
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    print('PATCHED %d variants' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
