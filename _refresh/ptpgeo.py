"""District / division / UC lookups for the PTP payload, read back out of index.html.

IDIMS spells districts its own way (DIKHAN, LAKKIMRWT, WAZIR-S Lower) and splits them
differently than the EPI tables, so every alias here is derived from payloads already
published in the dashboard rather than hand-typed.
"""
import json

import dashpatch


def district_aliases(epim):
    """raw IDIMS spelling -> [display district, division], only where it resolves to exactly one.

    KURRAM maps to two EPI districts (Kurram Lower and Central / Kurram Upper), so it is left
    out here and stays its own district unit rather than being guessed into a split.
    """
    disp_div = {}
    raw = {}
    for r in epim:
        disp_div[r['ed']] = r.get('dv', '')
        for d in r.get('ds', []):
            raw.setdefault(d, set()).add(r['ed'])
    return {d: [e, disp_div.get(e, '')] for d, s in raw.items() if len(s) == 1 for e in s}


def uc_district(snd):
    """8-digit UC code -> campaign-scope district name."""
    dn = {i: r[0] for i, r in enumerate(snd['d'])}
    return {str(r[3]): dn[r[0]] for r in snd['u']}
