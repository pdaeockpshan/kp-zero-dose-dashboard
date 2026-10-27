# -*- coding: utf-8 -*-
"""SNID Nov-26: the morning team deployment tab.

The owner asked, 27-Oct-2026: "for every campaign we collect morning team deployment reports from
districts in scope ... Morning reports from field comes in intervals like it starts from 8 Am and may
go to 2 pm till completion due to different reasons like network issues, security incidents,
boycotts etc." and "it should be for campaign days as per scope". Then: "Normally campaign days are
3 + 2 ... for peshawar and khyber its 5 active days and 2 catchup days and than there can be extended
catchup request by districts so we would be needing all those days and there should be option for
selection of campaigns if anyone wants to see and download previous campaign deployment data along
with names of the campaign."

One tab: a day-scoped board (3 active + 2 catch-up days, 5 + 2 for Peshawar & Khyber, and any
extended catch-up a district asks for up to day 12), an online capture form, import of the district
39-column sheet merged by district + campaign day with the later time of update winning, a template
and a workbook export, an A4 one-pager, a campaign selector that reads and downloads earlier
campaigns, and an owner-key-gated scoped delete. Column F and
the free-text remarks are never read or written - they carry AIC / UCMO names and this is a public
page. Reports live in this browser only.

The additions are kept as small files under _refresh/mdep/ so each piece is reviewable; this driver
concatenates them. Applied to index.html only; the other three variants are synced later through
push_master.py. `--unpatch` restores the previous file byte for byte.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mdep')


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def read(name):
    with open(os.path.join(ASSETS, name), encoding='utf-8') as f:
        return crlf(f.read()).rstrip('\r\n')


JOIN = '\r\n\r\n'
CSS = JOIN.join(read(n) for n in ('style1.css', 'style2.css', 'style3.css'))
PANE = JOIN.join(read(n) for n in ('pane1.html', 'pane2.html', 'pane3.html', 'pane4.html'))
JS = [read(n) for n in ('js1a.js', 'js1b.js', 'js1c.js', 'js1e.js', 'js2a.js', 'js2b.js', 'js2c.js',
                        'js2d.js', 'js2e.js', 'js2f.js', 'js3a.js', 'js3b.js', 'js4a.js', 'js4b.js',
                        'js5a.js', 'js5b.js', 'js5c.js', 'js5d.js', 'js5e.js')]
HELPERS = JOIN.join(JS) + '\r\n'

NAV = ('<button class="tab" data-tab="mdep"><span class="tl">Morning deployment</span>'
       '<span class="badge" id="bMD">Day 1</span></button>')

EDITS = [
    ('css', '.tab[data-tab="er"],#p-er{--tc:#be123c}', CSS),
    ('nav', '<button class="tab" data-tab="er"><span class="tl">Evening review</span>'
            '<span class="badge" id="bER">Day 1</span></button>',
     NAV + '\r\n   <button class="tab" data-tab="er"><span class="tl">Evening review</span>'
           '<span class="badge" id="bER">Day 1</span></button>'),
    ('pane', '<!-- ================= HUB: Campaigns ================= -->',
     PANE + '\r\n' + '<!-- ================= HUB: Campaigns ================= -->'),
    ('hub-chip',
     '<button data-hl="hrat">HRA compilation</button><button data-hl="cpre">Pre-campaign</button>'
     '<button data-hl="cicm">Intra-campaign ops</button>',
     '<button data-hl="hrat">HRA compilation</button><button data-hl="cpre">Pre-campaign</button>'
     '<button data-hl="cicm">Intra-campaign ops</button><button data-hl="mdep">Morning deployment</button>'),
    ('tabs', "'sn','fipv','er','act'", "'sn','fipv','mdep','er','act'"),
    ('dispatch', 'sn:renderSN,fipv:renderFIPV,er:renderER,act:renderAct',
     'sn:renderSN,fipv:renderFIPV,mdep:renderMDEP,er:renderER,act:renderAct'),
    ('bar', 'function renderBar(){',
     "function renderBar(){\r\n if(TAB==='mdep'){renderMDPBar();return;}"),
    ('table-signature', 'function drawTable(id,cols,rows,defK,defD){',
     'function drawTable(id,cols,rows,defK,defD,empty){'),
    ('table-resort', 'drawTable(id,cols,rows,defK,defD);};});',
     'drawTable(id,cols,rows,defK,defD,empty);};});'),
    ('table-empty', '<td colspan="${cols.length}" class="empty">No UCs match the current filters</td>',
     '<td colspan="${cols.length}" class="empty">${empty||\'No UCs match the current filters\'}</td>'),
    ('helpers', '{const _rdN=render; render=function(){_rdN(); try{ntPass();}catch(e){}};}',
     HELPERS + '{const _rdN=render; render=function(){_rdN(); try{ntPass();}catch(e){}};}'),
]


def apply(t, edits):
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times - the master no longer matches what this '
                             'patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times - not undoing something this patch '
                             'did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    for once in ('id="p-mdep"', '<button class="tab" data-tab="mdep">', 'id="bMD"', 'data-hl="mdep"',
                 "'sn','fipv','mdep','er','act'", 'mdep:renderMDEP',
                 "if(TAB==='mdep'){renderMDPBar();return;}",
                 'function drawTable(id,cols,rows,defK,defD,empty){',
                 "${empty||'No UCs match the current filters'}",
                 'const MDP_OLDKEY=', 'function renderMDEP()', 'function renderMDPBar()',
                 'function mdpExportBoard()', 'function mdpExportTpl()', 'function mdpReadMe()',
                 'function mdpImportFiles(', 'function mdpBind(){', 'mdpBind();',
                 'function mdpOwnAsk(', 'function mdpClearScope()',
                 'const MDP_CAMPS=', 'const MDP_MAXD=12', 'function mdpFillCamp()',
                 'function mdpCampGo(', 'function mdpLastDay(', 'const mdpDayTag='):
        if t.count(once) != 1:
            raise SystemExit('ERR the mdep patch is missing %r (%d copies)' % (once, t.count(once)))
    if 'MDP_TYPES.map' not in t or 'mdpStoredRows' not in t:
        raise SystemExit('ERR the mdep helpers are incomplete')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='apply in memory, report, write nothing')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'id="p-mdep"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the mdep patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (p-mdep present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  morning deployment %s' % (
        'UNPATCH' if a.unpatch else 'PATCH', v.rel, v.delta(),
        'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
