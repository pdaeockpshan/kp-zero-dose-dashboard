"""The EPI-MIS antigen panel, in one place.

The Consolidated facility-wise exports (YTD UC-wise and the single-month archive) carry
62 columns; this module declares the 19 we publish, in schedule order, and which target
each dose is measured against. Three extractors read it: extract_epi_ytd (UC rows),
_epicache/extract_epim (district x month) and extract_emeta (const EMETA's `ag`, which
is what the dashboard's meter tiles render from).

A `True` flag in the table below marks a CORE column: it must be present in every
export, and a missing one aborts the extract because the layout has changed. Optional
doses are read when the export carries them and simply left out of that month when it
does not, so an older or slimmer export cannot delete a whole month of history.

Deliberately NOT here: HEP B (reported as zero in every UC), DTP (404 doses in 36 UCs,
a residue not a series), the TT / PLW maternal block (different programme - it would
dilute the UC focus logic) and the portal's own `%` columns (coverage is computed here,
against the target, so the definition stays ours).
"""

# (key, source column, display label, target, core)
AG = [
    ('bcg', 'BCG Total', 'BCG', 'n', True),
    ('opv0', 'OPV 0 Total', 'OPV-0', 'n', True),
    ('opv1', 'OPV I Total', 'OPV-1', 's', False),
    ('opv2', 'OPV II Total', 'OPV-2', 's', False),
    ('opv3', 'OPV III Total', 'OPV-3', 's', False),
    ('p1', 'Pentavalent I Total', 'Penta-1', 's', True),
    ('p2', 'Pentavalent II Total', 'Penta-2', 's', False),
    ('p3', 'Pentavalent III Total', 'Penta-3', 's', True),
    ('pcv1', 'PCV 10 I Total', 'PCV-1', 's', False),
    ('pcv2', 'PCV 10 II Total', 'PCV-2', 's', False),
    ('pcv3', 'PCV 10 III Total', 'PCV-3', 's', True),
    ('ipv1', 'IPV Total', 'IPV-1', 's', True),
    ('ipv2', 'IPV II Total', 'IPV-2', 's', True),
    ('rota1', 'Rota I Total', 'Rota-1', 's', False),
    ('rota2', 'Rota II Total', 'Rota-2', 's', True),
    ('mr1', 'MR I Total', 'MR-1', 's', True),
    ('mr2', 'MR II Total', 'MR-2', 's', True),
    ('tcv', 'TCV Total', 'TCV', 's', False),
    ('fi', 'Fully Immunized Total', 'Fully immunized', 's', True),
]
CORE = [a for a in AG if a[4]]
EXT = [a for a in AG if not a[4]]
KEYS = [a[0] for a in AG]
TARGET = {a[0]: a[3] for a in AG}


def emeta_ag():
    """const EMETA's `ag` list: [key, label, target, core] - what the tiles render from.

    The core flag tells the dashboard which doses every export is expected to carry
    (and so which columns belong in the district and UC tables by default); the extra
    doses are shown once you select them.
    """
    return [[a[0], a[2], a[3], 1 if a[4] else 0] for a in AG]
