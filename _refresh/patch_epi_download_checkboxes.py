"""Month picker in the EPI download card: checkboxes instead of a Ctrl-click list.

The owner asked for a tick box in front of every month of the antigen-wise download, so a
reader does not have to know that Ctrl/⌘-click adds a month to a multi-select. The list is
built from the same grain-aware `exAvail()`; ticking or unticking only refreshes the count and
the two download buttons, so the list never collapses under the pointer.

Run after patch_epi_download_simple.py. Master only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

HTML_OLD = '''<div style="margin:6px 0 2px"><span class="cnt" style="display:block;margin-bottom:3px">Months — Ctrl/⌘-click for more than one</span>
<select id="exMonth" multiple aria-label="Download months" style="font:13px var(--font-sans);padding:4px 6px;border:1px solid var(--color-border);border-radius:8px;background:#fff;width:100%;max-width:440px;vertical-align:top"></select></div>'''

HTML_NEW = '''<div style="margin:6px 0 2px"><span class="cnt" style="display:block;margin-bottom:4px">Months — tick one or more</span>
<div id="exMonthBox" role="group" aria-label="Download months" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:3px 14px;max-width:640px;font:13px var(--font-sans)"></div></div>'''

NOTE_OLD = 'Pick a <b>year</b>, one or more <b>months</b> (Ctrl/⌘-click for several, or <b>All months</b>), narrow by'
NOTE_NEW = 'Pick a <b>year</b>, tick one or more <b>months</b> (or <b>All months</b>), narrow by'

JS_OLD = ''' const av=exAvail();
 const ms=el('exMonth');
 ms.innerHTML=av.map(p=>{const k=p.mo||'YTD';return '<option value="'+esc(k)+'"'+(EXPER.has(k)?' selected':'')+'>'+esc(p.mn)+'</option>';}).join('');
 ms.size=Math.min(Math.max(av.length,3),9);
 const n=exPeriods().length;
 ['btnEXxls','btnEXcsv'].forEach(id=>{const b=el(id);if(b){b.disabled=!n;b.title=n?'':'Pick at least one month first';}});
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' · '+EXG_L[EXG]+' rows'+(EXDIV?' · '+exDvL(EXDIV):'')+(EXDIST?' · '+EXDIST:''):'Pick at least one month';
}'''

JS_NEW = ''' const av=exAvail(),box=el('exMonthBox');
 box.innerHTML=av.map(p=>{const k=p.mo||'YTD';
  return '<label style="display:flex;align-items:center;gap:6px;cursor:pointer"><input type="checkbox" value="'+esc(k)+'"'+(EXPER.has(k)?' checked':'')+'>'+esc(p.mn)+'</label>';}).join('');
 // Ticking a month only updates the count and the buttons: rebuilding the list here would move
 // the box under the pointer while the reader is still ticking months.
 box.querySelectorAll('input').forEach(c=>c.onchange=()=>{EXPER.clear();box.querySelectorAll('input:checked').forEach(x=>EXPER.add(x.value));exCount();});
 exCount();
}
const exCount=()=>{
 const n=exPeriods().length;
 ['btnEXxls','btnEXcsv'].forEach(id=>{const b=el(id);if(b){b.disabled=!n;b.title=n?'':'Pick at least one month first';}});
 el('cntEX').textContent=n?n+' period'+(n===1?'':'s')+' · '+EXG_L[EXG]+' rows'+(EXDIV?' · '+exDvL(EXDIV):'')+(EXDIST?' · '+EXDIST:''):'Pick at least one month';
};'''

WIRE_OLD = "el('exMonth').onchange=()=>{EXPER.clear();[...el('exMonth').selectedOptions].forEach(o=>EXPER.add(o.value));renderEX();};\n"

FIXES = [
    (HTML_OLD, HTML_NEW, 'months box'),
    (NOTE_OLD, NOTE_NEW, 'note copy'),
    (JS_OLD, JS_NEW, 'checkbox build'),
    (WIRE_OLD, '', 'old select wiring'),
]


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edited = 0
    for old, new, label in FIXES:
        old, new = crlf(old), crlf(new)
        if (new and new in v.text) or (not new and old not in v.text):
            print('  skip (already applied): %s' % label)
            continue
        n = v.text.count(old)
        if n != 1:
            raise SystemExit('ABORT: %d matches for %s' % (n, label))
        v.text = v.text.replace(old, new, 1)
        edited += 1
        v.changes.append('EPI download months: %s' % label)
    if not edited:
        print('nothing to do')
        return
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), edited))


if __name__ == '__main__':
    main()
