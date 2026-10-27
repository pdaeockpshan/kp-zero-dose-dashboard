# -*- coding: utf-8 -*-
"""HRA: an owner-only delete mode with its own division and district selectors.

The owner asked, 27-Oct-2026: "There should be division/district selection mode in owner mode for
deletion".

Until this module the only scoped delete reused #hrtDiv / #hrtDist - the two selects that also narrow
the grid, the KPIs and the at-a-glance charts. Reading the card and choosing what to remove competed
for the same two controls, and the delete button sat in the grid header with no statement of what it
would remove. This module separates the two:

  * A delete card appears only while Owner mode is unlocked. It carries its own Division and District
    selects, filled from the period's own rows (so a division or district can only be picked if the
    sheet holds it), with the district list following the division.
  * The card states the period and row count it acts on, updates the selected row count as the pair
    changes, and says that every other district and any downloaded file stay untouched.
  * "Delete the selected rows" removes exactly the rows the pair names from this period in this
    browser, then refreshes the card, the coverage panel, the charts and the log the same way the
    existing scoped delete does.
  * The old "Delete the rows in the filter" button is hidden: a delete that silently follows the
    reading filters is exactly the ambiguity the owner asked to remove. Its handler stays in the file
    so this module can be un-applied byte for byte.

Delete stays a per-browser action - the compiled sheet lives in the visitor's localStorage - so the
card is a clean choice of scope, not access to anyone else's copy.

Applied to index.html after patch_hrat_round2.py; un-apply this module FIRST. `--unpatch` restores the
previous file byte for byte.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


PANEL = crlf(r"""
<div class="card" id="hratDel" style="display:none;margin:0 0 14px;padding:10px 12px;border-left:4px solid #b91c1c">
<div class="tblhdr" style="margin-bottom:6px"><h3 style="margin:0">Delete compiled rows &middot; owner only</h3><span class="cnt" id="hrtDelPer"></span><span style="flex:1"></span><span class="cnt" id="hrtDelCnt"></span></div>
<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><select class="hrc" id="hrtDelDiv" aria-label="Division to delete"></select><select class="hrc" id="hrtDelDist" aria-label="District to delete"></select><button class="btn" id="btnHRTDEL2" disabled title="Remove the councils of the division or district picked here from this period. The rest of the period and any file you already downloaded are untouched">Delete the selected rows</button></div>
<div class="cap" id="hrtDelNote" style="margin-top:6px"></div>
</div>
""")

HELPERS = crlf(r"""// ---------- owner delete mode: its own division / district pair ----------
// The owner asked, 27-Oct-2026: "There should be division/district selection mode in owner mode for
// deletion". The reading filters used to double as the delete scope; this panel keeps a separate pair
// so choosing where to read never decides what to remove. It is shown only while the owner key is
// unlocked, and it only ever offers divisions and districts the period actually holds.
function hrtPerLbl(){
 const C=el('fHRC'),Y=el('fHRY'),M=el('fHRM'),
  t=C&&C.options[C.selectedIndex]?C.options[C.selectedIndex].text:'',
  m=M&&M.value?HRTMO[+M.value-1]:'',
  l=String(t).toLowerCase();
 if(t&&m&&l.indexOf(m.toLowerCase())>=0&&l.indexOf(Y.value)>=0)return t;
 return (t?t+' \u00b7 ':'')+(m?m+' ':'')+(Y?Y.value:'');}
function hrtDelPick(){
 const dv=el('hrtDelDiv').value,dd=el('hrtDelDist').value,out=[];
 hrtRows.forEach(function(r,i){
  const a=String(r.A==null?'':r.A).trim(),b=String(r.B==null?'':r.B).trim();
  if(dv&&a!==dv)return;
  if(dd&&b!==dd)return;
  out.push(i);});
 return {dv:dv,dd:dd,idx:out,n:out.length,label:dd?dd:(dv?dv+' division':'')};}
function hrtDelFill(){
 const dv=el('hrtDelDiv'),dd=el('hrtDelDist');if(!dv||!dd)return;
 const k0=dv.value,k1=dd.value,D={},B={};
 hrtRows.forEach(function(r){const a=String(r.A==null?'':r.A).trim();if(a)D[a]=1;});
 dv.innerHTML='<option value="">All divisions</option>'+Object.keys(D).sort()
  .map(function(x){return '<option value="'+esc(x)+'">'+esc(x)+'</option>';}).join('');
 dv.value=D[k0]?k0:'';
 const ds=dv.value;
 hrtRows.forEach(function(r){const b=String(r.B==null?'':r.B).trim();
  if(b&&(!ds||String(r.A==null?'':r.A).trim()===ds))B[b]=1;});
 dd.innerHTML='<option value="">All districts'+(ds?' in '+esc(ds):'')+'</option>'+Object.keys(B).sort()
  .map(function(x){return '<option value="'+esc(x)+'">'+esc(x)+'</option>';}).join('');
 dd.value=B[k1]?k1:'';
 hrtDelCount();}
function hrtDelCount(){
 const dv=el('hrtDelDiv'),dd=el('hrtDelDist'),b=el('btnHRTDEL2'),n=el('hrtDelNote');
 if(!dv||!dd||!b)return;
 const S=hrtDelPick(),on=!!_hraOwn;
 b.disabled=!(on&&S.n&&(S.dv||S.dd));
 const per=el('hrtDelPer');if(per)per.textContent=hrtPerLbl()+' \u00b7 '+fmt(hrtRows.length)+' rows';
 const cnt=el('hrtDelCnt');
 if(cnt)cnt.textContent=(S.dv||S.dd)?(fmt(S.n)+' of '+fmt(hrtRows.length)+' rows'):'Pick a division or district';
 if(n)n.textContent=!on?'Unlock Owner mode to delete.'
  :!hrtRows.length?'This period holds no rows in this browser.'
  :(S.dv||S.dd)?('This removes '+fmt(S.n)+' row'+(S.n===1?'':'s')+' for '+S.label+' from '
    +hrtPerLbl()+', and keeps every other district. A file you already downloaded is untouched.')
  :'Pick a division, or a division and a district. Only the sheet in this browser is changed.';}
function hrtDelSel(){
 if(!_hraOwn){toast('Owner only - unlock with the Owner mode button');return;}
 const S=hrtDelPick();
 if(!S.dv&&!S.dd){toast('Pick a division or a district to delete');return;}
 if(!S.n){toast('Nothing on this sheet matches that selection');return;}
 if(!window.confirm('Remove '+fmt(S.n)+' council row(s) for '+S.label+' from '+hrtPerLbl()
  +'? Every other district on the sheet stays, and a file you already downloaded is untouched.'))return;
 const drop={};S.idx.forEach(function(i){drop[i]=1;});
 hrtRows=hrtRows.filter(function(r,i){return !drop[i];});
 hrtPage=0;hrtStore();hrtScope();
 hrtPaint(hrtVals());hrtNote();_HRVD=null;hrvRender();
 hrtLogAdd('Deleted '+fmt(S.n)+' council row(s) for '+S.label+'. The period now holds '
  +fmt(hrtRows.length)+'.');
 hrtImpBox('ok','<b>Deleted</b> '+fmt(S.n)+' council row(s) for '+esc(S.label)+'. The period now '
  +'holds '+fmt(hrtRows.length)+'.');
 toast('Removed '+fmt(S.n)+' council'+(S.n===1?'':'s'));}
function hrtMk(){if(!_HRTC||_HRTC.rows!==hrtRows)_HRTC={rows:hrtRows,mk:hratMake(HRAT,hrtRows)};
 return _HRTC.mk;}
""")

EDITS = [
    ('del-panel',
     '<div id="hratImp"',
     PANEL.lstrip('\r\n') + '<div id="hratImp"'),

    ('hide-old-del',
     'id="btnHRTDEL" disabled title=',
     'id="btnHRTDEL" disabled style="display:none" title='),

    ('del-helpers',
     crlf(r"""function hrtMk(){if(!_HRTC||_HRTC.rows!==hrtRows)_HRTC={rows:hrtRows,mk:hratMake(HRAT,hrtRows)};
 return _HRTC.mk;}
"""),
     HELPERS),

    ('owner-ui',
     crlf(r"""  x.title=on?x.dataset.bt:'Owner only - unlock with the Owner mode button';});}
"""),
     crlf(r"""  x.title=on?x.dataset.bt:'Owner only - unlock with the Owner mode button';});
 const p=el('hratDel');if(p)p.style.display=on?'block':'none';
 if(typeof hrtDelFill==='function')hrtDelFill();}
""")),

    ('scope-refresh',
     crlf(r""" const bd=el('btnHRTDEL');if(bd)bd.disabled=!(_hraOwn&&(dv.value||dd.value));}
"""),
     crlf(r""" const bd=el('btnHRTDEL');if(bd)bd.disabled=!(_hraOwn&&(dv.value||dd.value));
 if(typeof hrtDelFill==='function')hrtDelFill();}
""")),

    ('del-wire',
     crlf(r"""  el('hrvPer').onchange=()=>hrvRender();}
 hraOwnUI();}
"""),
     crlf(r"""  el('hrvPer').onchange=()=>hrvRender();
  if(el('hrtDelDiv'))el('hrtDelDiv').onchange=function(){
   if(el('hrtDelDist'))el('hrtDelDist').value='';hrtDelFill();};
  if(el('hrtDelDist'))el('hrtDelDist').onchange=hrtDelCount;
  if(el('btnHRTDEL2'))el('btnHRTDEL2').onclick=hrtDelSel;}
 hraOwnUI();}
""")),
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
    for once in ('id="hratDel"', 'id="hrtDelDiv"', 'id="hrtDelDist"', 'id="btnHRTDEL2"',
                 'function hrtDelFill()', 'function hrtDelPick()', 'function hrtDelSel()',
                 'function hrtPerLbl()',
                 'id="btnHRTDEL" disabled style="display:none"',
                 "if(el('btnHRTDEL2'))el('btnHRTDEL2').onclick=hrtDelSel;",
                 "const p=el('hratDel');if(p)p.style.display=on?'block':'none';"):
        if t.count(once) != 1:
            raise SystemExit('ERR the delete-mode patch is missing %r (%d copies)' % (once, t.count(once)))


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
    built = 'id="hratDel"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the delete-mode patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (hratDel present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA delete mode %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                       v.delta(), 'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
