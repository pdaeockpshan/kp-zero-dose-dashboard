# -*- coding: utf-8 -*-
"""HRA visuals: the division band mix, the ranked council curve, the 27-indicator weakness chart and
the labelled district map, at the foot of the `hrat` pane.

The owner asked, 27-Oct-2026: "And a good visual dashboard for hra", then "it would be good if we can
generate a small report based on compiled hra for findings and recommendations", then "The report
should be in PPTX." The report card's button now builds a seven-slide deck from the same findings and
recommendations; the text report stays as the offline fallback.

The block sits BELOW the compilation card on purpose: the card is what divisional staff open the tab
for (its pickers, upload and download), and these charts read `const HRA`, the dashboard payload, not
the sheet compiled above. The heading says so, and so does the hint. The findings report at the foot
is the one part that reads the compiled sheet, and its scope line names the filter it read.

Rules kept:
  * The card's own axis, never the combined UC risk score: 79%+ is Low Risk, under 60% is High.
  * Per-sheet vintage: 132 councils on the 26-Oct Mardan-division sheets, 1,286 on 26-Mar, three
    Mardan councils on March; the hint states the split.
  * No invented data: every figure is a roll-up of HRA.u, and the district roll-up CSV writes the same
    numbers the map is shaded with.
  * The report never averages a row the card cannot grade: rows with no answers, and rows that score
    above 100% because the card charges two blocks per answered cell while blanks in them still earn
    their formula defaults, are counted out loud and left out of every percentage.

Applied to the index.html master only; the other variants follow through push_master.py on the
owner's word. `--unpatch` restores the previous file byte for byte. Because the hook sits inside
renderHRT(), this module must be un-applied BEFORE `patch_hrat_ui.py --unpatch`.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'
HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = ['hrv_data.js', 'hrv_charts.js', 'hrv_geo.js', 'hrv_district.js', 'hrv_csv.js',
         'hrv_report.js', 'hrv_report_pptx.js']

NEW_IDS = ['hrvHint', 'hrv1', 'chrv1', 'hrv2', 'chrv2', 'hrv3', 'chrv3', 'hrvMNote', 'hrvMap',
           'hrvMK', 'btnHRVcsv', 'chrvMap', 'hrvRepSub', 'hrvRep', 'hrvRepFoot', 'btnHRVrep']

A_PANE = ('<div class="card"><div class="tblhdr"><h3 style="margin:0">What the last import read</h3>'
          '</div><div class="cap" id="hrtLog"></div></div>\r\n</section>')
A_HOOK = ' hrtRule();hrtPaint(V);\r\n'
A_PAINT = 'function hrtPaint(V){hrtAll=V;hrtTable(V);hrtKpi(V);hrtBadge();}\r\n'
A_PAINT_NEW = 'function hrtPaint(V){hrtAll=V;hrtTable(V);hrtKpi(V);hrtBadge();hrvRep(V);}\r\n'
A_JS = 'function hrtWire(){\r\n'

MARKUP = """<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:26px 0 10px;border-top:1px solid var(--color-border);padding-top:16px">
<h2 style="margin:0;font-size:17px;font-weight:600">HRA at a glance</h2>
<span style="font-size:12px;color:var(--color-text-secondary)">The province&rsquo;s HRA sheets as they stand &mdash; read from the dashboard payload, not from the sheet compiled above</span>
</div>
<div class="hint" id="hrvHint"></div>
<div class="grid2">
<div class="card"><div class="tblhdr"><h3 style="margin:0">Risk band by division</h3></div><div id="hrv1"></div><div class="cap" id="chrv1"></div></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">Council scores against the card&rsquo;s thresholds</h3></div><div id="hrv2"></div><div class="cap" id="chrv2"></div></div>
</div>
<div class="card" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Where the card takes its points off</h3><span style="font-size:12px;color:var(--color-text-secondary)">Marks earned as a share of the marks the card charges, all 1,418 councils</span></div><div id="hrv3"></div><div class="cap" id="chrv3"></div></div>
<div class="card"><div class="tblhdr"><h3 style="margin:0">HRA risk by district</h3><select class="hrc" id="hrvMK" aria-label="District measure"><option value="hi">High-Risk council share</option><option value="mean">District score</option></select><span style="flex:1"></span><button class="btn" id="btnHRVcsv" title="Division, district, council counts by band, High-Risk share, marks earned and the marks charged, one row per district">District roll-up (CSV)</button></div><div id="hrvMNote" class="cap" style="margin:0 0 8px"></div><div id="hrvMap" style="max-width:620px;margin:0 auto"></div><div class="cap" id="chrvMap"></div></div>
<div class="card" style="margin-top:16px"><div class="tblhdr"><h3 style="margin:0">Findings and recommendations</h3><button class="btn" id="btnHRVrep" title="A short PowerPoint deck built from the sheet compiled above and the division / district filter on it">Download the report (.pptx)</button></div><div class="cap" id="hrvRepSub" style="margin:0 0 8px"></div><div id="hrvRep"></div><div class="cap" id="hrvRepFoot">Read from the cells on this sheet only, and from the filter above it. A high percentage is a safe council &mdash; the card&rsquo;s own axis, not the combined UC risk score.</div></div>
"""


def source():
    out = []
    for p in PARTS:
        with open(os.path.join(HERE, p), encoding='utf-8') as f:
            out.append(f.read().replace('\r\n', '\n').rstrip('\n'))
    return '\n'.join(out) + '\n'


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def build_edits(js):
    pane = A_PANE[:-len('</section>')] + crlf(MARKUP) + '</section>'
    return [
        ('pane', A_PANE, pane),
        ('hook', A_HOOK, A_HOOK + ' hrvRender();\r\n'),
        ('paint', A_PAINT, A_PAINT_NEW),
        ('js', A_JS, crlf(js) + '\r\n' + A_JS),
    ]


def apply(t, edits):
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times (expected 1)' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times (expected 1) - not undoing something '
                             'this patch did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('ERR duplicate element ids after the HRA visuals: %s' % ', '.join(dup[:12]))
    miss = [i for i in NEW_IDS if t.count('id="%s"' % i) != 1]
    if miss:
        raise SystemExit('ERR the HRA visuals are missing an anchor id: %s' % ', '.join(miss))
    for once in ('function hrvRender()', 'function hrvData()', 'function hrvBand(', 'function hrvCurve(',
                 'function hrvInd(', 'function hrvMap(', 'function hrvLab()', 'function hrvCSV()',
                 'function hrvRep(', 'function hrvRepData(', 'function hrvRepSave(',
                 'function hrvRepPptx(', 'function hrvRepDeck(',
                 'function renderHRT()', 'function hrtWire()', 'function hrtExport('):
        if t.count(once) != 1:
            raise SystemExit('ERR the HRA visuals lost %r (%d copies)' % (once, t.count(once)))
    if t.count(' hrvRender();\r\n') != 1:
        raise SystemExit('ERR renderHRT() does not call hrvRender() exactly once')
    if t.count('hrtBadge();hrvRep(V);}') != 1:
        raise SystemExit('ERR hrtPaint() does not refresh the report exactly once')
    i = t.find('function renderHRT()')
    if i < 0 or t.find('hrvRender();', i, i + 4000) < 0:
        raise SystemExit('ERR hrvRender() is not hooked inside renderHRT()')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='apply in memory, report, write nothing')
    a = ap.parse_args()
    edits = build_edits(source())
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'id="hrvHint"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the HRA visuals are not applied')
        v.text = unapply(v.text, edits)
    else:
        v.require(not built, 'already applied (id="hrvHint" present)')
        v.text = apply(v.text, edits)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA visuals %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                 v.delta(), 'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
