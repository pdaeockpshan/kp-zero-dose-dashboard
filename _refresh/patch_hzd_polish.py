# -*- coding: utf-8 -*-
"""Polish the Zero Dose overview page filters: label the two pickers and fix plurals.

The page bar read "PESHAWARPESHAWAR" when the division and district shared a name, and the
Nov-26 strip said "1 districts" / "1 UCs" for single-area scopes. Both are copy fixes on the
block patch_hzd_nov_filters.py installs, so they are applied to all four variants after it.

Run:  python _refresh/patch_hzd_polish.py [--dry-run]
"""
import sys

import dashpatch


def edits():
    return [
        ("' UCs \u00b7 '+fmt(nv.dists)+' districts'",
         "' UC'+(nv.n===1?'':'s')+' \u00b7 '+fmt(nv.dists)+' district'+(nv.dists===1?'':'s')",
        1, 'nov strip plural'),
        (" bd.querySelector('span').textContent=DVSEL?DVSEL.size+' divisions':(fDiv.value||'All divisions');",
         " bd.querySelector('span').textContent=DVSEL?DVSEL.size+' division'+(DVSEL.size===1?'':'s')+' selected':(fDiv.value?'Division: '+fDiv.value:'Division: all');",
         1, 'division label'),
        (" bs.querySelector('span').textContent=DSEL?dsCnt()+' districts':(fDist.value||'All districts');",
         " bs.querySelector('span').textContent=DSEL?dsCnt()+' district'+(dsCnt()===1?'':'s')+' selected':(fDist.value?'District: '+fDist.value:'District: all');",
         1, 'district label'),
    ]


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    new_stamp = dashpatch.pkt_stamp()
    for v in vs:
        s = v.text
        for old, new, n, why in edits():
            got = s.count(old)
            v.require(got == n, '%s: expected %d hit(s), found %d' % (why, n, got))
            s = s.replace(old, new)
        v.text = s
        dashpatch.set_stamp(v, new_stamp)
    for v in vs:
        for token in ("'Division: '", "'District: '", "district'+(nv.dists===1?'':'s')"):
            v.require(token in v.text, 'missing %s' % token)
        print('%s: %+d chars' % (v.rel, v.delta()))
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    print('stamp -> %s' % new_stamp)
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, 'Zero Dose overview filters: label the division and district pickers '
                                  'and fix single-area plurals in the Nov-26 strip.', dry=False)
    print('PATCHED %d variants' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
