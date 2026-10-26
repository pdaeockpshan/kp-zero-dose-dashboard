"""Merge the "Last 3 campaigns" (c3) and "Monitoring analysis" (pcm) panes into one tab.

The owner asked, 26-Oct-2026: "In campaign section last three campaigns comparison and field
monitoring should be combined and should be presented as one button." The two panes answer the
same question from two registers - the comparison says how much of the target was left over, the
monitoring says what monitors found on the ground in the same round - so they now sit behind one
nav button ("Comparison & monitoring") with a segmented switch that shows one half at a time.

Why a switch and not one long scroll: charts are hand-built into `.ch` containers whose height is
set at render time, so a half that is hidden while it renders would size itself against a
collapsed box. `renderC3` and `renderPCM` stay untouched and are called for the visible half only;
switching sets the display first, then renders, so each half is measured while it is on screen.
Nothing is recomputed twice and no card id is duplicated - `p-pcm` simply becomes `#c3B` inside
`#p-c3`, and the old `#pcm` route (hash, `data-hl`, `setTab('pcm')`) remaps to the merged pane with
sub B active instead of falling through to `home`.

Applied to the index.html master only; the other three variants get it through
`_refresh/push_master.py`, which is the owner-approved route for propagating a hand-edited master.
`--unpatch` restores the previous file byte for byte.

All inserted text uses CRLF. Every anchor is asserted to occur exactly once before anything is
written, and id uniqueness across the whole file is asserted after the merge.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

# (id, old, new) - applied in order, each old must occur exactly once.
EDITS = [
    # 1. The monitoring half keeps its own cyan accent now that it is inside the orange c3 pane.
    ('accent',
     '.tab[data-tab="pcm"],#p-pcm{--tc:#0891b2}',
     '#p-c3 .c3sub[data-sub="b"]{--tc:#0891b2}'),
    # 2. Segmented switch styling (scoped to .c3seg so .on cannot leak into tabs or panes).
    ('css',
     '.cqbar select{font:13px var(--font-sans);padding:5px 8px;border-radius:8px;'
     'border:1px solid var(--color-border);background:#fff}',
     '.cqbar select{font:13px var(--font-sans);padding:5px 8px;border-radius:8px;'
     'border:1px solid var(--color-border);background:#fff}\r\n'
     '.c3seg{display:flex;gap:4px;padding:3px;border-radius:22px;'
     'border:1px solid color-mix(in srgb,var(--tc) 35%,#e5e7eb);'
     'background:color-mix(in srgb,var(--tc) 7%,#fff)}\r\n'
     '.c3seg button{all:unset;cursor:pointer;font-size:12.5px;font-weight:700;'
     'padding:5px 13px;border-radius:18px;color:var(--tc);white-space:nowrap}\r\n'
     '.c3seg button:hover,.c3seg button:focus-visible{background:#fff}\r\n'
     '.c3seg button.on{background:var(--tc);color:#fff}'),
    # 3. One nav button instead of two, labelled for what the merged pane holds.
    ('nav',
     '   <button class="tab" data-tab="c3"><span class="tl">Last 3 campaigns</span>'
     '<span class="badge" id="bC3">–</span></button>\r\n'
     '   <button class="tab" data-tab="pcm"><span class="tl">Monitoring analysis</span>'
     '<span class="badge" id="bPCM">–</span></button>\r\n',
     '   <button class="tab" data-tab="c3"><span class="tl">Comparison &amp; monitoring</span>'
     '<span class="badge" id="bC3">–</span></button>\r\n'),
    # 4. Pane header + the wrapper that holds the comparison half.
    ('pane-head',
     '<div class="cqbar"><b>Last 3 campaigns</b>',
     '<div class="cqbar"><b>Campaign comparison &amp; monitoring</b><span class="c3seg">'
     '<button type="button" class="on" data-sub="a">Last 3 campaigns comparison</button>'
     '<button type="button" data-sub="b">Field monitoring analysis</button></span></div>\r\n'
     '<div class="c3sub" id="c3A" data-sub="a">\r\n'
     '<div class="cqbar"><b>Last 3 campaigns</b>'),
    # 5. Close the comparison half, open the monitoring half in its place.
    ('sub-b',
     '</section>\r\n\r\n<!-- CAMPAIGNS: POST-CAMPAIGN MONITORING (ICM / PCM / PCHS) -->\r\n'
     '<section class="pane" id="p-pcm">\r\n',
     '</div>\r\n\r\n<!-- CAMPAIGN MONITORING: second half of the merged c3 pane -->\r\n'
     '<div class="c3sub" id="c3B" data-sub="b" style="display:none">\r\n'),
    # 6. Close the monitoring half, then the merged pane.
    ('sub-end',
     '<div class="cap" id="pcmc5"></div>\r\n</div>\r\n</section>\r\n',
     '<div class="cap" id="pcmc5"></div>\r\n</div>\r\n</div>\r\n</section>\r\n'),
    # 7. The in-pane chip now switches half instead of jumping to a tab that no longer exists.
    #    The identical chip on the Post-campaign hub keeps data-hl="pcm" - setTab remaps it.
    ('chip',
     '<button data-hl="cpost">Post-campaign analysis — ICM &amp; ops vs outcome</button>'
     '<button data-hl="pcm">Monitoring analysis (ICM · LQAS · PCM/PCHS)</button>',
     '<button data-hl="cpost">Post-campaign analysis — ICM &amp; ops vs outcome</button>'
     '<button data-sub="b">Monitoring analysis (ICM · LQAS · PCM/PCHS)</button>'),
    # 7b. Two labels outside the pane name the merged tab; both routes still resolve.
    ('hl-c3',
     '<button data-hl="c3">Last 3 campaigns</button>',
     '<button data-hl="c3">Comparison &amp; monitoring</button>'),
    ('hero',
     '<button class="hgo2" data-hl="c3" title="Combined analysis of the last three campaigns — '
     'campaign coverage, missed children and zero-dose children recorded and covered, with the UCs '
     'that need focus"><span class="hi" data-ic="chart"></span>Last 3 campaigns comparison</button>',
     '<button class="hgo2" data-hl="c3" title="Campaign comparison and monitoring in one place — '
     'coverage, missed children and zero-dose children across the last three rounds, and what ICM, '
     'PCM and PCHS monitors found in the same rounds"><span class="hi" data-ic="chart">'
     '</span>Comparison &amp; monitoring</button>'),
    # 8. Tab allowlist: 'pcm' is no longer a tab.
    ('tabs',
     "'hcamp','c3','pcm','cpre'",
     "'hcamp','c3','cpre'"),
    # 9. setTab remaps the old route before the allowlist check, so a stale #pcm link still lands
    #    on the merged pane rather than falling through to home, and syncs the halves so the pane
    #    shows the half it is about to render.
    ('settab',
     'function setTab(t){\r\n if(!TABS.includes(t))t=\'home\';',
     'function setTab(t){\r\n if(t===\'pcm\'){C3SUB=\'b\';t=\'c3\';}\r\n'
     ' if(!TABS.includes(t))t=\'home\';'),
    ('sub-show',
     " try{history.replaceState(null,'','#'+t);}catch(e){}\r\n render();",
     " try{history.replaceState(null,'','#'+t);}catch(e){}\r\n"
     ' if(t===\'c3\')c3Show(C3SUB);\r\n render();'),
    # 10. One entry in the render dispatch, pointed at the visible half.
    ('dispatch',
     'c3:renderC3,pcm:renderPCM,',
     'c3:renderC3Half,'),
    # 11. The half state, the visibility sync, the switch and its wiring, ahead of setTab.
    #     c3Show is separate from c3Sub because setTab must open the target half *before* the
    #     render dispatch fills it - a half that renders while hidden sizes its charts against a
    #     collapsed box.
    ('js',
     'function setTab(t){',
     'var C3SUB=\'a\';\r\n'
     'function renderC3Half(){(C3SUB===\'b\'?renderPCM:renderC3)();}\r\n'
     'function c3Show(s){\r\n'
     ' const A=el(\'c3A\'), B=el(\'c3B\');\r\n'
     ' if(A)A.style.display=s===\'a\'?\'\':\'none\';\r\n'
     ' if(B)B.style.display=s===\'b\'?\'\':\'none\';\r\n'
     " document.querySelectorAll('#p-c3 .c3seg button[data-sub]').forEach(x=>"
     "x.classList.toggle('on',x.dataset.sub===s));\r\n"
     '}\r\n'
     'function c3Sub(s){\r\n'
     ' C3SUB=s===\'b\'?\'b\':\'a\';\r\n'
     ' c3Show(C3SUB);\r\n'
     ' if(C3SUB===\'b\')renderPCM();else renderC3();\r\n'
     '}\r\n'
     'document.querySelectorAll(\'#p-c3 button[data-sub]\').forEach(x=>x.onclick='
     '()=>c3Sub(x.dataset.sub));\r\n'
     'function setTab(t){'),
]


def apply(t):
    for name, old, new in EDITS:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times (expected 1) - the master no longer '
                             'matches what this patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t):
    for name, old, new in reversed(EDITS):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times (expected 1) - not undoing '
                             'something this patch did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check_ids(t):
    """Every id in the file exactly once: a merged pane must not double up a card id."""
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('ERR duplicate element ids after merge: %s' % ', '.join(dup[:12]))
    need = ['c3A', 'c3B', 'c3Hint', 'pcmHint', 'fPCM', 'tC3', 'tPCM', 'btnPCMPPT']
    miss = [i for i in need if ids.count(i) != 1]
    if miss:
        raise SystemExit('ERR merged pane lost an anchor id: %s' % ', '.join(miss))
    if 'bPCM' in ids:
        raise SystemExit('ERR the removed nav badge bPCM is still in the file')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='report only')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    merged = 'id="c3B"' in v.text
    if a.unpatch:
        v.require(merged, 'nothing to undo - the merge is not applied')
        v.text = unapply(v.text)
    else:
        v.require(not merged, 'already merged (id="c3B" present)')
        v.text = apply(v.text)
        check_ids(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  panes %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                             v.delta(), 'c3 -> c3 (sub a|b)' if not a.unpatch
                                             else 'c3 (sub a|b) -> c3 + pcm'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    print('OK c3pcm-merge master only - the other three variants are synced by push_master.py, '
          "which needs the owner's word")
    return 0


if __name__ == '__main__':
    sys.exit(main())
