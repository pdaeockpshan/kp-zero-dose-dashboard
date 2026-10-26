"""Put the long notes of every section behind a popover.

The owner asked, 26-Oct-2026: "the notes in every section should be popover as some notes are too
large which creates confusion for readers and messy environment." The site carries its method,
provenance and caveat text in `.hint`, `.note` and `.cap` blocks, and the longest of them run to
400-700 characters - several stacked on one screen read as a wall of text and push the tables and
charts below the fold.

This pass does not move or rewrite any note. Each render, the active pane is scanned and every note
longer than its threshold is clamped to two lines with a "Full note" pill under it; the pill opens
one shared popover that carries a copy of the note's own HTML. The note element is never replaced,
because renders write into nested spans inside these blocks (`vmNote`, `xScope`, `pScope`, the
campaign labels) and a rewrite would delete the ids those renders still address; the popover copy
has its `id` attributes stripped for the same reason - an open copy must not hold a second live id
of the note it duplicates. Short notes stay exactly as
they were, and a note that becomes short again after a filter change loses its clamp and
its pill - the pass is re-evaluated per render, so it follows the filters.

Thresholds are per class (220 characters for chart captions, 170 for hints/notes): below them a
block fits its two lines and clamping it would only hide a sentence behind a click.

Applied to the index.html master only; the other three variants get it through
`_refresh/push_master.py`, which is the owner-approved route for propagating a hand-edited master.
`--unpatch` restores the previous file byte for byte. Every anchor is asserted to occur exactly
once, all inserted text uses CRLF, and ids stay unique.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

CSS_ANCHOR = ('.hint{background:var(--color-info-bg);color:var(--color-info-text);'
              'border-radius:var(--radius-sm);padding:8px 12px;font-size:12.5px;margin-bottom:14px}')

CSS_LINES = [
    '',
    '/* Long notes read as a wall of text: clamped to two lines, full text in a popover. Only the',
    '   prefixed line-clamp is used - with the standard property alongside it Chromium leaves a',
    '   clipped third line peeking under the ellipsis. The bottom padding goes with it: a',
    '   -webkit-box paints the hidden third line into that padding, so the tinted note box ends at',
    '   its last visible line. */',
    '.ntclip{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;'
    'overflow:hidden;text-overflow:ellipsis;padding-bottom:0}',
    '.ntbtn{all:unset;cursor:pointer;font-size:11.5px;font-weight:700;padding:3px 11px;'
    'border-radius:14px;margin-top:5px;background:#fff;color:var(--tc,#0f766e);'
    'border:1px solid color-mix(in srgb,var(--tc,#0f766e) 40%,#e5e7eb)}',
    '.ntbtn:hover,.ntbtn:focus-visible,.ntbtn.on{background:var(--tc,#0f766e);color:#fff}',
    '.ntpop{position:fixed;z-index:78;display:none;max-height:min(62vh,460px);overflow:auto;'
    'background:#fff;border:1px solid var(--color-border);border-radius:12px;'
    'box-shadow:0 14px 36px rgba(15,23,42,.18);padding:12px 14px;'
    'font-size:12.5px;line-height:1.55;color:var(--color-text)}',
    '.ntpop.on{display:block}',
    '.ntpop b{color:var(--color-text)}',
]

JS_ANCHOR = "kxInit();\r\nsetTab((location.hash||'').replace('#','')||'home');"

JS_LINES = [
    '',
    '// ---------- long notes behind a popover ----------',
    '// Renders fill these blocks with method and provenance prose, some 700 characters long. The',
    '// note itself is left in the DOM untouched - renders also write into spans nested inside it -',
    '// and only its presentation changes: two lines on the page, the whole block on request.',
    'var NTMIN={cap:220,hint:170};',
    'function ntClose(){const p=document.getElementById("ntpop"),b=document.querySelector(".ntbtn.on");',
    ' if(p&&p.classList.contains("on"))p.classList.remove("on");',
    ' if(b){b.classList.remove("on");b.setAttribute("aria-expanded","false");}}',
    'function ntOpen(btn,src){',
    ' let p=el("ntpop"); if(!p){p=document.createElement("div");p.id="ntpop";p.className="ntpop";',
    '  p.setAttribute("role","dialog");p.setAttribute("aria-label","Full note");',
    '  document.body.appendChild(p);}',
    ' p.innerHTML=src.innerHTML;',
    ' p.querySelectorAll("[id]").forEach(x=>x.removeAttribute("id"));',
    ' const w=Math.min(560,window.innerWidth-20), r=btn.getBoundingClientRect();',
    ' p.classList.add("on"); p.style.width=w+"px";',
    ' p.style.left=Math.max(10,Math.min(r.left,window.innerWidth-w-10))+"px";',
    ' let top=r.bottom+6; if(top+p.offsetHeight>window.innerHeight-8)top=Math.max(8,r.top-p.offsetHeight-6);',
    ' p.style.top=top+"px";',
    ' btn.classList.add("on"); btn.setAttribute("aria-expanded","true");',
    '}',
    'function ntPass(){',
    ' ntClose();',
    ' const P=document.querySelector(".pane.on"); if(!P)return;',
    ' P.querySelectorAll(".hint,.note,.cap").forEach(x=>{',
    '  const min=NTMIN[x.classList.contains("cap")?"cap":"hint"], len=(x.textContent||"").trim().length;',
    '  const nx=x.nextElementSibling, has=nx&&nx.classList&&nx.classList.contains("ntbtn");',
    '  if(len<=min){x.classList.remove("ntclip"); x.style.maxHeight=""; if(has)nx.remove(); return;}',
    '  x.classList.add("ntclip");',
    '  // The clamp box must end at the last visible line: padding-top plus two line-heights. Any',
    '  // taller box paints the hidden third line into the note padding.',
    '  const cs=getComputedStyle(x), lh=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.45;',
    '  x.style.maxHeight=(2*lh+parseFloat(cs.paddingTop))+"px";',
    '  if(has)return;',
    '  const b=document.createElement("button"); b.type="button"; b.className="ntbtn";',
    '  b.textContent="Full note"; b.setAttribute("aria-expanded","false");',
    '  b.onclick=()=>{if(b.classList.contains("on"))ntClose(); else ntOpen(b,x);};',
    '  x.after(b);',
    ' });',
    '}',
    '{const _rdN=render; render=function(){_rdN(); try{ntPass();}catch(e){}};}',
    'document.addEventListener("click",ev=>{const t=ev.target;',
    ' if(t&&t.closest&&(t.closest(".ntbtn")||t.closest(".ntpop")))return; ntClose();},true);',
    'document.addEventListener("keydown",ev=>{if(ev.key==="Escape")ntClose();});',
    'window.addEventListener("resize",ntClose);',
    'window.addEventListener("scroll",()=>{const p=document.getElementById("ntpop");',
    ' if(p&&p.classList.contains("on"))ntClose();},true);',
]

EDITS = [
    ('css', CSS_ANCHOR, CSS_ANCHOR + '\r\n' + '\r\n'.join(CSS_LINES)),
    ('js', JS_ANCHOR, '\r\n'.join(JS_LINES) + '\r\n' + JS_ANCHOR),
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


def check(t):
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('ERR duplicate element ids after the popover pass: %s' % ', '.join(dup[:12]))


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
    done = 'function ntPass(){' in v.text
    if a.unpatch:
        v.require(done, 'nothing to undo - the popover pass is not applied')
        v.text = unapply(v.text)
    else:
        v.require(not done, 'already applied (ntPass present)')
        v.text = apply(v.text)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  notes -> clamped + popover' %
          ('UNPATCH' if a.unpatch else 'PATCH', v.rel, v.delta()))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    print('OK note-popovers master only - the other three variants are synced by push_master.py, '
          "which needs the owner's word")
    return 0


if __name__ == '__main__':
    sys.exit(main())
