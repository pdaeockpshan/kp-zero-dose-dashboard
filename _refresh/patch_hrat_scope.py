# -*- coding: utf-8 -*-
"""Scope the whole HRA tab to one division or district, and delete that scope.

The owner asked, 27-Oct-2026: "if i want to delete data there should be option for Division/district
and there should be filter option in dashboard table so if anyone wants to see a specific district
online can select that district or division."

Before this module the division / district selects above the compiled grid filtered the grid, the KPIs
and the findings report, and nothing else: the charts, the district map and the roll-up download were
built from `const HRA` (the published reading) and always covered all 1,418 councils. There was also no
way to remove one division or one district - only "Clear this period" and "Clear all periods".

What this module changes:

  * One scope. The same two selects now drive the compiled card AND the HRA-at-a-glance section: the
    band-by-division chart, the score curve, the indicator chart, the district map and its legend, the
    roll-up download and the new district table all narrow to the chosen division / district. The
    payload reading is filtered on its own district and division fields, the card on its rows. The
    two sides spell districts and divisions slightly differently ("Malakand-II" on the sheet,
    "Malakand" in the payload), so the match ignores case, spacing and punctuation and accepts a
    numbered suffix on either side, and a district is matched on both its payload key and its display
    name.
  * District list follows the division. Pick a division and the district select lists only that
    division's districts; clearing the division restores the full list.
  * A district table on screen. "HRA risk by district" gains a real table (division, district,
    councils, Low / Medium / High, High-Risk share, marks earned, mean score) with a total row, so a
    district can be read without downloading the CSV first.
  * Delete the scope. A "Delete the rows in the filter" button removes the councils the two selects
    name from this period, after a confirm that states the scope and the row count. The other
    districts on the sheet stay, the download is untouched, and the button is disabled while both
    selects read "All". This is the per-division / per-district counterpart to "Clear this period".

`ann` stays aligned with the payload district array `D` (and with `ix`) - the accumulation indexes it
by the district's payload position - so the scope filters the council rows, never the district array.

Applied to the index.html master after `patch_hrat_merge.py`. Un-apply this module FIRST. `--unpatch`
restores the previous file byte for byte.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

HELP = """function hrtDelScope(){
 const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';
 if(!dv&&!dd)return null;
 const idx=hrtView();
 return {dv:dv,dd:dd,n:idx.length,idx:idx,
  label:dd?dd:(dv+' division')};}
function hrtDel(){
 const S=hrtDelScope();
 if(!S){toast('Pick a division or a district in the filters first');return;}
 if(!S.n){toast('Nothing on this sheet matches that filter');return;}
 if(!window.confirm('Remove '+fmt(S.n)+' council row(s) for '+S.label+' from this period? Every '
  +'other district on the sheet stays, and a file you already downloaded is untouched.'))return;
 const drop={};S.idx.forEach(function(i){drop[i]=1;});
 hrtRows=hrtRows.filter(function(r,i){return !drop[i];});
 hrtPage=0;hrtStore();hrtScope();
 hrtPaint(hrtVals());hrtNote();hrvRender();
 hrtLogAdd('Deleted '+fmt(S.n)+' council row(s) for '+S.label+'. The period now holds '
  +fmt(hrtRows.length)+'.');
 hrtImpBox('ok','<b>Deleted</b> '+fmt(S.n)+' council row(s) for '+esc(S.label)+'. The period now '
  +'holds '+fmt(hrtRows.length)+' from '+hrtDivs().length+' division'
  +(hrtDivs().length===1?'':'s')+'.');
 toast('Removed '+fmt(S.n)+' council'+(S.n===1?'':'s'));}
"""

TABLE = """// The district roll-up the CSV already carried, on screen and under the same scope.
function hrvTable(X){
 const t=el('hrvTbl');if(!t)return;
 const rows=X.ann.filter(function(o){return o.n;}).sort(function(a,b){return (b.hi||0)-(a.hi||0);});
 const td=function(o){return '<tr><td>'+esc(o.dv)+'</td><td>'+esc(DNAME(o.c))+'</td><td>'+fmt(o.n)
  +'</td><td>'+fmt(o.b[0])+'</td><td>'+fmt(o.b[1])+'</td><td>'+fmt(o.b[2])+'</td><td>'
  +(o.hi==null?'-':o.hi.toFixed(1))+'</td><td>'+(o.p==null?'-':o.p.toFixed(1))+'</td><td>'
  +(o.m==null?'-':o.m.toFixed(1))+'</td></tr>';};
 t.innerHTML='<thead><tr><th>Division</th><th>District</th><th>Councils</th><th>Low Risk</th>'
  +'<th>Medium</th><th>High</th><th>High-Risk %</th><th>Marks earned %</th><th>Mean score %</th>'
  +'</tr></thead><tbody>'+(rows.length?rows.map(td).join('')
  :'<tr><td colspan="9" class="cnt">No HRA reading for the selected division and district.</td></tr>')
  +'</tbody>'+(rows.length?'<tfoot><tr class="tot"><td>All in scope</td><td>'+fmt(X.nd)
  +(X.nd===1?' district':' districts')+'</td><td>'+fmt(X.n)+'</td><td>'+fmt(X.bt[0])+'</td><td>'+fmt(X.bt[1])+'</td><td>'
  +fmt(X.bt[2])+'</td><td>'+(X.n?(X.bt[2]/X.n*100).toFixed(1):'-')+'</td><td>'
  +(X.posT?(X.achT/X.posT*100).toFixed(1):'-')+'</td><td>'
  +(X.n?((X.ann.reduce(function(s,o){return s+o.sum;},0))/X.n).toFixed(1):'-')+'</td></tr></tfoot>':'');}
"""

EDITS = [
    ('del-button',
     '<select class="hrc" id="hrtDiv" aria-label="Division shown"></select>'
     '<select class="hrc" id="hrtDist" aria-label="District shown"></select>'
     '<span style="flex:1"></span>',
     '<select class="hrc" id="hrtDiv" aria-label="Division shown"></select>'
     '<select class="hrc" id="hrtDist" aria-label="District shown"></select>'
     '<button class="btn" id="btnHRTDEL" disabled title="Remove the councils of the division or '
     'district picked in the two filters beside this button; the rest of the period and any file you '
     'already downloaded are untouched">Delete the rows in the filter</button><span style="flex:1"></span>'),

    ('rollup-table',
     '<div id="hrvMap" style="max-width:620px;margin:0 auto"></div>'
     '<div class="cap" id="chrvMap"></div></div>',
     '<div id="hrvMap" style="max-width:620px;margin:0 auto"></div>'
     '<div class="cap" id="chrvMap"></div>'
     '<div class="cap" style="margin:12px 0 6px"><b>District roll-up on screen</b> &mdash; the same '
     'rows the CSV carries, under the same division / district filter.</div>'
     '<div style="overflow:auto;max-height:440px">'
     '<table class="shtbl" id="hrvTbl"></table></div></div>'),

    ('ind-caption',
     '<span style="font-size:12px;color:var(--color-text-secondary)">Marks earned as a share of the '
     'marks the card charges, all 1,418 councils</span>',
     '<span id="hrv3cap" style="font-size:12px;color:var(--color-text-secondary)"></span>'),

    ('scope-fn',
     "function hrtScope(){\r\n"
     " const dv=el('hrtDiv'),dd=el('hrtDist'),k0=dv.value,k1=dd.value,D={},B={};\r\n"
     " hrtRows.forEach(r=>{if(r.A)D[r.A]=1;if(r.B)B[r.B]=1;});\r\n"
     " dv.innerHTML='<option value=\"\">All divisions</option>'+Object.keys(D).sort()\r\n"
     "  .map(x=>'<option value=\"'+esc(x)+'\">'+esc(x)+'</option>').join('');\r\n"
     " dd.innerHTML='<option value=\"\">All districts</option>'+Object.keys(B).sort()\r\n"
     "  .map(x=>'<option value=\"'+esc(x)+'\">'+esc(x)+'</option>').join('');\r\n"
     " dv.value=D[k0]?k0:'';dd.value=B[k1]?k1:'';}",
     "// One scope for the tab: the card and the at-a-glance section read the same two selects. The\r\n"
     "// district list follows the division, and Delete is only live while one of the two names a scope.\r\n"
     "function hrtScope(){\r\n"
     " const dv=el('hrtDiv'),dd=el('hrtDist'),k0=dv.value,k1=dd.value,D={},B={};\r\n"
     " hrtRows.forEach(r=>{if(r.A)D[r.A]=1;});\r\n"
     " dv.innerHTML='<option value=\"\">All divisions</option>'+Object.keys(D).sort()\r\n"
     "  .map(x=>'<option value=\"'+esc(x)+'\">'+esc(x)+'</option>').join('');\r\n"
     " dv.value=D[k0]?k0:'';\r\n"
     " const ds=dv.value;\r\n"
     " hrtRows.forEach(r=>{if(r.B&&(!ds||String(r.A||'')===ds))B[r.B]=1;});\r\n"
     " dd.innerHTML='<option value=\"\">All districts</option>'+Object.keys(B).sort()\r\n"
     "  .map(x=>'<option value=\"'+esc(x)+'\">'+esc(x)+'</option>').join('');\r\n"
     " dd.value=B[k1]?k1:'';\r\n"
     " const bd=el('btnHRTDEL');if(bd)bd.disabled=!(dv.value||dd.value);}"),

    ('del-fn', " b.innerHTML=html;}\r\nfunction hrtCheckRows(rows){",
     " b.innerHTML=html;}\r\n" + HELP.replace('\n', '\r\n') + "function hrtCheckRows(rows){"),

    ('select-handlers',
     "  el('hrtDiv').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());};\r\n"
     "  el('hrtDist').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());};",
     "  el('hrtDiv').onchange=()=>{hrtPage=0;hrtScope();hrtPaint(hrtVals());hrvRender();};\r\n"
     "  el('hrtDist').onchange=()=>{hrtPage=0;hrtPaint(hrtVals());hrvRender();};"),

    ('del-wire',
     "  el('btnHRThide').onclick=()=>{hrtHide=!hrtHide;\r\n"
     "   el('btnHRThide').textContent=hrtHide?'Show the computed columns':'Hide the computed columns';\r\n"
     "   hrtPaint(hrtVals());};",
     "  el('btnHRThide').onclick=()=>{hrtHide=!hrtHide;\r\n"
     "   el('btnHRThide').textContent=hrtHide?'Show the computed columns':'Hide the computed columns';\r\n"
     "   hrtPaint(hrtVals());};\r\n"
     "  el('btnHRTDEL').onclick=hrtDel;"),

    ('data-head',
     "function hrvData(){\r\n"
     " if(_HRVD)return _HRVD;\r\n"
     " const U=(typeof HRA!=='undefined'&&HRA.u)||[],D=(typeof HRA!=='undefined'&&HRA.d)||[];\r\n"
     " if(!U.length){_HRVD={n:0};return _HRVD;}",
     "function hrvScope(){const dv=el('hrtDiv')?el('hrtDiv').value:'',dd=el('hrtDist')?el('hrtDist').value:'';\r\n"
     " return {dv:dv,dd:dd,k:HRTN(dv)+'\\u0001'+HRTN(dd)};}\r\n"
     "function hrvData(){\r\n"
     " const SC=hrvScope();\r\n"
     " if(_HRVD&&_HRVD.k===SC.k)return _HRVD;\r\n"
     " const U0=(typeof HRA!=='undefined'&&HRA.u)||[],D=(typeof HRA!=='undefined'&&HRA.d)||[];\r\n"
     " if(!U0.length){_HRVD={n:0,k:SC.k};return _HRVD;}"),

    ('data-scope',
     " const ix={};D.forEach(function(c,i){ix[c]=i;});\r\n"
     " const ann=D.map(function(c){return {c:c,dv:dvOf(c),n:0,b:[0,0,0],oct:0,ach:0,pos:0,sum:0,vm:0};});\r\n"
     " const div={};",
     " const ix={};D.forEach(function(c,i){ix[c]=i;});\r\n"
     " const ann=D.map(function(c){return {c:c,dv:dvOf(c),n:0,b:[0,0,0],oct:0,ach:0,pos:0,sum:0,vm:0};});\r\n"
     " const hvS=function(a,b){a=HRTN(a);b=HRTN(b);\r\n"
     "  return a===b||a.indexOf(b+' ')===0||b.indexOf(a+' ')===0;};\r\n"
     " const inS=function(o){return (!SC.dv||hvS(o.dv,SC.dv))\r\n"
     "  &&(!SC.dd||hvS(o.c,SC.dd)||hvS(DNAME(o.c),SC.dd));};\r\n"
     " const U=(!SC.dv&&!SC.dd)?U0:U0.filter(function(r){const o=ann[ix[D[r[0]]]];\r\n"
     "  return !!o&&inS(o);});\r\n"
     " const div={};"),

    ('data-result',
     " _HRVD={n:U.length,nd:D.length,ann:ann,div:div,ind:ind,blocks:blocks,bt:bt,vint:vint,",
     " _HRVD={k:SC.k,scope:!!(SC.dv||SC.dd),sdv:SC.dv,sdd:SC.dd,\r\n"
     "  n:U.length,nd:ann.filter(function(o){return o.n;}).length,ann:ann,div:div,\r\n"
     "  ind:ind,blocks:blocks,bt:bt,vint:vint,"),

    ('hint-scope',
     " el('hrvHint').innerHTML='<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' districts and '+dvn\r\n"
     "  +' divisions carry an HRA reading dated '+esc(hrvD(HRA.asof))+'.</b> On the card&rsquo;s own axis '",
     " el('hrvHint').innerHTML=(X.scope?'<b>'+esc(X.sdv||'All divisions')+(X.sdd?' / '+esc(X.sdd):'')\r\n"
     "  +' selected:</b> ':'')+'<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' district'\r\n"
     "  +(X.nd===1?'':'s')+' and '+dvn+' division'+(dvn===1?'':'s')\r\n"
     "  +' carry'\r\n"
     "  +' an HRA reading dated '+esc(hrvD(HRA.asof))+'.</b> On the card&rsquo;s own axis '"),

    ('band-cap',
     "  +'The two divisions with the largest shares hold '+fmt(top2n)+' of the '+fmt(X.bt[2])\r\n"
     "  +' High-Risk councils.';}",
     "  +(rows.length<3?'The filter holds '+fmt(X.bt[2])+' High-Risk council'\r\n"
     "   +(X.bt[2]===1?'':'s')+' in '+rows.length+' division'+(rows.length===1?'':'s')+'.'\r\n"
     "   :'The two divisions with the largest shares hold '+fmt(top2n)+' of the '+fmt(X.bt[2])\r\n"
     "    +' High-Risk councils.');}"),

    ('curve-ticks',
     "  xAxis:{min:0,max:S.length,title:{text:'Councils, ranked by score',style:{fontSize:'11px'}},\r\n"
     "   tickPositions:[1,250,500,750,1000,1250,S.length],",
     "  xAxis:{min:0,max:S.length,title:{text:'Councils, ranked by score',style:{fontSize:'11px'}},\r\n"
     "   tickPositions:(S.length>=1000?[1,250,500,750,1000,1250,S.length]\r\n"
     "    :[1,Math.max(2,Math.round(S.length*.25)),Math.max(2,Math.round(S.length*.5)),\r\n"
     "      Math.max(2,Math.round(S.length*.75)),S.length]\r\n"
     "     .filter(function(v,i,a){return a.indexOf(v)===i;})),"),

    ('map-tip',
     "  if(!o2||!o2.n)return DNAME(c)+'\\nno HRA sheet';",
     "  if(!o2||!o2.n)return DNAME(c)+(X.scope?'\\noutside the selected division / district'\r\n"
     "   :'\\nno HRA sheet');"),

    ('map-lg',
     "  +'border-radius:2px;background:#f1f5f9\"></i>no sheet</span></span>'",
     "  +'border-radius:2px;background:#f1f5f9\"></i>'+(X.scope?'not in the selected division / '\r\n"
     "   +'district':'no sheet')+'</span></span>'"),

    ('ind-cap',
     " const worst=rows.slice(-3).reverse();",
     " el('hrv3cap').textContent='Marks earned as a share of the marks the card charges, '+fmt(X.n)\r\n"
     "  +' council'+(X.n===1?'':'s')+(X.scope?' in the selected division / district':'')+' in the '\r\n"
     "  +'published reading';\r\n"
     " const worst=rows.slice(-3).reverse();"),

    ('ind-thin',
     " const thin=X.ind.filter(function(o){return o.ap<900;})",
     " const thin=X.ind.filter(function(o){return o.ap<Math.max(12,Math.round(X.n*0.64));})"),

    ('table-fn', "function hrvCSV(){", TABLE.replace('\n', '\r\n') + "function hrvCSV(){"),

    ('render-table',
     " hrvMap(X);\r\n const K=el('hrvMK');",
     " hrvMap(X);\r\n hrvTable(X);\r\n const K=el('hrvMK');"),

    ('render-empty',
     " if(!X.n){h.innerHTML='The HRA payload is empty, so there is nothing to chart.';\r\n"
     "  el('chrv1').textContent='';el('chrv2').textContent='';el('chrv3').textContent='';\r\n"
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';\r\n"
     "  return;}",
     " if(!X.n){h.innerHTML=X.scope?'No council in the selected division or district carries an HRA '\r\n"
     "  +'reading in the published payload.':'The HRA payload is empty, so there is nothing to chart.';\r\n"
     "  el('chrv1').textContent='';el('chrv2').textContent='';el('chrv3').textContent='';\r\n"
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';\r\n"
     "  if(el('hrvTbl'))el('hrvTbl').innerHTML='';if(el('hrv3cap'))el('hrv3cap').textContent='';\r\n"
     "  return;}"),

    ('map-cap',
     "  +'children. '+green+' of the '+X.nd+' districts have no High-Risk council, but that is not the same as '",
     "  +'children. '+green+' of the '+X.nd+' district'+(X.nd===1?' has':'s have')\r\n"
     "  +' no High-Risk council, but that is not the same as '"),

    ('csv-rows',
     " const rows=X.ann.slice().sort(function(a,b){",
     " const rows=X.ann.filter(function(o){return o.n;}).slice().sort(function(a,b){"),

    ('csv-total',
     " rows.push(['All','All '+X.nd+' districts',X.n,",
     " rows.push(['All','All '+X.nd+' district'+(X.nd===1?'':'s'),X.n,"),

    ('csv-name',
     " csvDownload('HRA_district_rollup_'+HRA.asof+'.csv',H,rows);}",
     " csvDownload('HRA_district_rollup_'+(X.sdv?X.sdv+'_':'')+(X.sdd?X.sdd+'_':'')+HRA.asof\r\n"
     "  +'.csv',H,rows);}"),
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
    for once in ('id="btnHRTDEL"', "el('btnHRTDEL').onclick=hrtDel", 'function hrtDel()',
                 'function hrtDelScope()', 'function hrvScope()', 'function hrvTable(X)',
                 'id="hrvTbl"', 'hrvTable(X);', 'const inS=function(o)',
                 'const U=(!SC.dv&&!SC.dd)?U0:U0.filter',
                 'nd:ann.filter(function(o){return o.n;}).length',
                 'tickPositions:(S.length>=1000', 'table class="shtbl" id="hrvTbl"',
                 "hrvRender();\r\n hrtLogAdd('Deleted '"):
        if t.count(once) != 1:
            raise SystemExit('ERR the scope patch is missing %r (%d copies)' % (once, t.count(once)))
    for once in ('hvS(', "el('hrv3cap')", 'btnHRTDEL'):
        if once not in t:
            raise SystemExit('ERR the scope patch is missing %r' % once)
    for gone in ('const ann=all.filter', 'nd:D.length', 'if(_HRVD)return _HRVD;',
                 'all 1,418 councils', "return DNAME(c)+'\\nno HRA sheet';",
                 'out.push(row);row.length=0'):
        if gone in t:
            raise SystemExit('ERR %r still in the master' % gone)
    for stays in ('const o=ann[ix[D[r[0]]]];if(!o)return;', 'hrtRows.forEach(r=>{if(r.A)D[r.A]=1;})'):
        if t.count(stays) != 1:
            raise SystemExit('ERR %r should be here exactly once (%d)' % (stays, t.count(stays)))


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
    built = 'id="btnHRTDEL"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the scope patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (btnHRTDEL present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA scope %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                v.delta(), 'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
