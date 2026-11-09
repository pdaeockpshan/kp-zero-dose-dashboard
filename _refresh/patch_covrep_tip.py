# -*- coding: utf-8 -*-
"""Say, on the register itself, that recorded and the covered share cover different rounds.

Adding a recorded-only round leaves every district's covered % where it was while the
recorded column grows, so the two cells no longer divide. The caption and both Covered %
headers now name that, instead of leaving a reader to work it out.

Run after patch_covrep_scope.py:  python _refresh/patch_covrep_tip.py [--dry-run]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

EDITS = [
    ("{k:'cp',l:'Covered %',n:1,sv:function(r){return r.covRep?r.cov/r.covRep:null;}",
     "{k:'cp',l:'Covered %',n:1,tt:'covered \\u00f7 recorded, over the rounds that report a "
     "covered figure; a recorded-only round such as SNID Nov 2026 sits in the recorded column "
     "but not in this share',sv:function(r){return r.covRep?r.cov/r.covRep:null;}",
     2, 'covered % header'),
    ("so a round still awaiting it never enters the denominator as uncovered.",
     "so a round still awaiting it never enters the denominator as uncovered, though the "
     "recorded totals do include it.",
     1, 'register caption'),
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
