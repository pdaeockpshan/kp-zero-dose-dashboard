# -*- coding: utf-8 -*-
"""Make the Zero Dose side-by-side dash note say what a dash means there.

On the hz group the covered column is a dash for SNID Nov-26 because the post-campaign return
is awaited, not because the area lacks data. The generic tail sentence said the latter.

Run:  python _refresh/patch_hzd_sbs_note.py [--dry-run]
"""
import sys

import dashpatch

OLD = ("+'Each campaign keeps its own columns \\u2014 nothing is added across rounds. "
       "A dash means the area has no data for that round.';")
NEW = ("+'Each campaign keeps its own columns \\u2014 nothing is added across rounds. '"
       "+(g==='hz'?'A dash in the covered column means the return is awaited, not that no child was covered.'"
       ":'A dash means the area has no data for that round.');")


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    stamp = dashpatch.pkt_stamp()
    for v in vs:
        n = v.text.count(OLD)
        v.require(n == 1, 'expected 1 note hit, found %d' % n)
        v.text = v.text.replace(OLD, NEW)
        dashpatch.set_stamp(v, stamp)
        v.require("g==='hz'?'A dash in the covered column" in v.text, 'note tail missing')
        print('%s: %+d chars' % (v.rel, v.delta()))
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    print('stamp -> %s' % stamp)
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, 'Zero Dose side-by-side: a dash in the covered column means the '
                                  'post-campaign return is awaited, not missing data.', dry=False)
    print('PATCHED %d variants' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
