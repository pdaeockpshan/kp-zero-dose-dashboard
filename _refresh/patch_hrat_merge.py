# -*- coding: utf-8 -*-
"""Let one HRA period hold every division's sheet, report uploader mistakes, and ignore duplicates.

The owner asked, 27-Oct-2026: "for every division separate sheet will be uploaded to dashboard ... i am
trying to upload two HRA sheets one for mardan and one for malakand 2 but i can only see for Mardan
division in table." and then, asked what the upload should do: "i want that when every division uploads
its HRA file it lands where it is required in dashboard and auto compiles. Also if any data has errors
or mistakes it prompts or give error message to uploader, also if someone uploads duplicates data for
same campaign it should be treated as one and ignored the duplicate." They approved the `Clear all
periods` control, this change, and the sync/publish of the round ("Go ahead", 27-Oct-2026).

It was not enabled. `hrtFromSheet()` and the CSV path both ended in `hrtRows = out`, so a second file
for the same campaign / year / month replaced the first one's rows; only the last upload survived. The
period key (`kp.hrat.<campaign>_<YYYY>-<MM>`) never distinguished divisions, and nothing on screen said
so.

What this module changes:

  * Merge by district. The districts named in the file are replaced by the file's rows - that is how a
    corrected division sheet lands over the division it corrects - and every other district on the
    period's sheet is left alone. A row is also replaced when its UC code matches, because a file whose
    District column is blank still names the councils it carries. A full-province file still replaces
    the period, because its district set is every district.
  * Duplicates are ignored, not counted twice. A UC code repeated inside one file keeps its first row
    and drops the rest, with the row numbers in the message; a file uploaded again over the same
    districts leaves the period's row count unchanged.
  * The uploader is told what happened. A coloured callout above the grid reports the file, the rows
    read, how many councils and divisions the period now holds, which districts this file replaced, and
    every row or cell that needs correcting, with Excel row numbers. A file that cannot be read, has no
    header row of this card, or holds no council row writes nothing and says so in red.
  * The division and district filters reset to "All" after an upload, so the uploader sees the whole
    compiled sheet rather than the division picked before.
  * Row order is the file's own order, appended after the divisions already held; nothing is sorted.
  * `hrtCsv()` handed out the row array it then emptied (`out.push(row);row.length=0`), so every CSV
    line arrived blank and every CSV upload was refused as "no header row". The row is copied on push.
    Un-applying this module restores that defect: fold this edit into `patch_hrat_ui.py` if the card is
    ever rebuilt and this module is retired.

The grid, the KPIs, the CSV/XLSX download and the PPTX findings report all read `hrtRows`, so once the
rows accumulate, the screen, the compiled workbook and the report carry every division.

Also added: a `Clear all periods` button beside `Clear this period`, because the stored sheets live in
the uploader's browser, not in this repo. It names the period keys it will remove and confirms first;
files already downloaded are untouched.

Applied to the index.html master after `patch_hrat_ui.py` and `patch_hrdv_ui.py`; the other three
variants follow through `push_master.py` on the owner's word (given 27-Oct-2026). Un-apply this module
FIRST when unwinding. `--unpatch` restores the previous file byte for byte. If the HRA card is ever
rebuilt from a pre-HRA master, fold these edits into `patch_hrat_ui.py` first.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

BTN = ('<button class="btn" id="btnHRTCLEAR" title="Empty this period in this browser - a file you '
       'already downloaded is untouched">Clear this period</button>')

CALL = ('<div id="hratImp" style="display:none;margin:0 0 10px;padding:9px 12px;border-radius:6px;'
        'font-size:12.5px;line-height:1.55"></div>\r\n'
        '<div class="card" id="hratRule"></div>')

HELP = """function hrtCodeK(v){return String(v==null?'':v).replace(/\\s+/g,' ').trim().toUpperCase();}
// A period's sheet accumulates the divisions. An upload replaces the districts its file covers and
// leaves every other district alone, so Mardan followed by Malakand-II leaves both on one sheet, and a
// corrected division file lands over that division only. A UC code repeated inside the file keeps its
// first row; a code the sheet already holds is replaced, never added twice.
function hrtMerge(out){
 const nd={},nc={},dn=[],uniq=[];
 let dup=0;
 out.forEach(o=>{const d=hrtCodeK(o.B);
  if(d&&!nd[d]){nd[d]=1;const t=String(o.B==null?'':o.B).replace(/\\s+/g,' ').trim();if(t)dn.push(t);}
  const k=hrtCodeK(o.D);
  if(k){if(nc[k]){dup++;return;}nc[k]=1;}
  uniq.push(o);});
 const was=hrtRows.length;
 const kept=hrtRows.filter(r=>{const d=hrtCodeK(r.B);if(d&&nd[d])return false;
  const k=hrtCodeK(r.D);return !(k&&nc[k]);});
 hrtRows=kept.concat(uniq);
 return {dropped:was-kept.length,dup:dup,districts:dn};}
function hrtDivs(){const o=[];
 hrtRows.forEach(r=>{const k=String(r.A==null?'':r.A).trim();if(k&&o.indexOf(k)<0)o.push(k);});
 return o;}
function hrtNote(){
 const dv=hrtDivs();
 el('hratNote').innerHTML=esc(HRT_P().join(' \\u00b7 '))+' \\u00b7 '+fmt(hrtRows.length)+' councils'
  +(dv.length>1?' across '+dv.length+' divisions':'')+' \\u00b7 '
  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';}
function hrtMergeNote(mg){
 const dv=hrtDivs();
 return 'The period now holds '+fmt(hrtRows.length)+' councils from '+dv.length+' division'
  +(dv.length===1?'':'s')+(dv.length?' ('+dv.join(', ')+')':'')+'.'
  +(mg.dropped?' It replaced '+fmt(mg.dropped)+' row(s) already held for '
    +(mg.districts.length>3?mg.districts.length+' districts':mg.districts.join(', '))+'.':'')
  +(mg.dup?' '+fmt(mg.dup)+' duplicate row(s) in the file were ignored.':'');}
function hrtImpBox(kind,html){
 const b=el('hratImp');if(!b)return;
 if(!html){b.style.display='none';b.innerHTML='';return;}
 const c=kind==='err'?['#b91c1c','#fef2f2']:kind==='warn'?['#b45309','#fffbeb']:['#15803d','#f0fdf4'];
 b.style.display='block';b.style.borderLeft='4px solid '+c[0];b.style.background=c[1];
 b.innerHTML=html;}
function hrtCheckRows(rows){
 let tx=0,of=0;const tc=[],oc=[];
 rows.forEach(r=>{HRTIN.forEach(c=>{const v=r[c.L];if(v===null||v===undefined)return;
  const o=(c.o||[]).filter(Boolean);
  if(!o.length&&(c.k==='pct'||c.k==='rate'||c.k==='cnt')&&typeof v==='string'){
   tx++;if(tc.indexOf(c.L)<0)tc.push(c.L);}
  if(o.length&&!o.some(x=>HRTN(x)===HRTN(String(v)))){
   of++;if(oc.indexOf(c.L)<0)oc.push(c.L);}});});
 const iss=[];
 if(tx)iss.push(fmt(tx)+' cell(s) in a number or percent column hold text ('
  +tc.slice(0,6).join(', ')+(tc.length>6?' \\u2026':'')+')');
 if(of)iss.push(fmt(of)+' cell(s) hold a value their dropdown does not list ('
  +oc.slice(0,6).join(', ')+(oc.length>6?' \\u2026':'')+')');
 return iss;}
"""

EDITS = [
    ('clearall-button', BTN,
     BTN + '<button class="btn" id="btnHRTCLEARALL" title="Remove every HRA sheet this browser has '
     'saved, for all periods - files you already downloaded are untouched">Clear all periods</button>'),

    ('callout', '<div class="card" id="hratRule"></div>', CALL),

    ('helpers', 'function hrtLogAdd(m){hrtLog.unshift(m);hrtLog=hrtLog.slice(0,10);',
     HELP.replace('\n', '\r\n') + 'function hrtLogAdd(m){hrtLog.unshift(m);hrtLog=hrtLog.slice(0,10);'),

    # hrtCsv() pushed the live row array and then emptied it, so every line of a CSV arrived blank and
    # every CSV upload was refused as "no header row". Copy the row on the way out.
    ('csv-parser', "if(ch==='\\n'){row.push(s);out.push(row);row.length=0;s='';continue;}",
     "if(ch==='\\n'){row.push(s);out.push(row.slice());row.length=0;s='';continue;}"),

    ('header-block', "  hrtLogAdd(fname+': no header row of this card was found (best match '+best+' "
     "of '+HRAT.n\r\n   +' columns over the first 8 rows), so nothing was imported.');\r\n  "
     "hrtRefresh();return;}",
     "  hrtLogAdd(fname+': no header row of this card was found (best match '+best+' of '+HRAT.n\r\n"
     "   +' columns over the first 8 rows), so nothing was imported.');\r\n  hrtRefresh();\r\n  "
     "hrtImpBox('err','<b>Nothing imported</b> '+esc(fname)+' \\u2014 no header row of this card was "
     "found (best match '+best+' of '+HRAT.n+' columns over the first 8 rows). Download the blank "
     "template and fill it, or check that the row holding Division / District / UC Name / UC Code is "
     "intact.');\r\n  return;}"),

    ('row-loop', " const M=hrtSheetMap(ws,hdr),out=[],pairs=[],odd={},txt={},conv={},seen={};\r\n"
     " let skipped=0,dupe=0;",
     " const M=hrtSheetMap(ws,hdr),out=[],pairs=[],odd={},txt={},conv={},seen={},skipR=[],dupeR=[];\r\n"
     " let skipped=0,dupe=0;"),

    ('row-skip', "  if(!any||(!o.D&&!o.C)){skipped++;continue;}\r\n"
     "  if(o.D){const k=String(o.D);if(seen[k])dupe++;else seen[k]=1;}\r\n"
     "  out.push(o);pairs.push({r:r,o:o});}",
     "  if(!any||(!o.D&&!o.C)){skipped++;if(skipR.length<8)skipR.push(r);continue;}\r\n"
     "  const ck=hrtCodeK(o.D);\r\n"
     "  if(ck){if(seen[ck]){dupe++;if(dupeR.length<8)dupeR.push(r);continue;}seen[ck]=1;}\r\n"
     "  out.push(o);pairs.push({r:r,o:o});}\r\n"
     " if(!out.length){\r\n"
     "  hrtLogAdd(fname+': the card was found but it holds no council row (every row was blank or "
     "carried neither a UC code nor a UC name), so nothing was imported.');\r\n"
     "  hrtRefresh();\r\n"
     "  hrtImpBox('err','<b>Nothing imported</b> '+esc(fname)+' \\u2014 no row under the header carries "
     "a UC code or a UC name.');\r\n"
     "  return;}"),

    ('merge', ' hrtRows=out;\r\n const V=hrtVals(),bad=[];',
     ' const mg=hrtMerge(out);\r\n'
     ' const V=hrtVals(),bad=[],pos=new Map(hrtRows.map((r,i)=>[r,i]));'),

    ('pairs', ' pairs.forEach((p,i)=>{\r\n  const row=ws.getRow(p.r);',
     ' pairs.forEach(p=>{\r\n  const i=pos.get(p.o);if(i===undefined)return;\r\n'
     '  const row=ws.getRow(p.r);'),

    ('row-messages', " if(skipped)bad.push(fmt(skipped)+' row(s) carried neither a UC code nor a UC "
     "name and were skipped');\r\n"
     " if(dupe)bad.push(fmt(dupe)+' row(s) repeat a UC code already on the sheet');",
     " if(skipped)bad.push(fmt(skipped)+' row(s) carried neither a UC code nor a UC name and were "
     "ignored'+(skipR.length?' (rows '+skipR.join(', ')+(skipped>skipR.length?' \\u2026':'')+')':''));\r\n"
     " if(dupe)bad.push(fmt(dupe)+' row(s) repeated a UC code already in this file and were ignored'"
     "+(dupeR.length?' (rows '+dupeR.join(', ')+(dupe>dupeR.length?' \\u2026':'')+')':''));"),

    ('import-log', " hrtLogAdd('Imported '+fmt(out.length)+' councils from '+fname+'. '+bad.join(' "
     "\\u00b7 '));\r\n hrtPage=0;hrtStore();hrtScope();hrtPaint(V);}",
     " hrtLogAdd('Imported '+fmt(out.length)+' councils from '+fname+'. '+hrtMergeNote(mg)+' '\r\n"
     "  +bad.join(' \\u00b7 '));\r\n"
     " const iss=[];\r\n"
     " if(skipped)iss.push(fmt(skipped)+' row(s) ignored with no UC code or UC name');\r\n"
     " if(dupe)iss.push(fmt(dupe)+' duplicate row(s) ignored');\r\n"
     " if(tn)iss.push(fmt(tn)+' cell(s) hold text in a number or percent column');\r\n"
     " if(on)iss.push(fmt(on)+' cell(s) hold a value their dropdown does not list');\r\n"
     " if(cn)iss.push(fmt(cn)+' cell(s) in percent columns are stored as whole numbers ('\r\n"
     "  +Object.keys(conv).join(', ')+') and were read as percents');\r\n"
     " if(diff.length)iss.push('the file\\u2019s computed columns disagree with this card\\u2019s formulas');\r\n"
     " hrtImpBox(iss.length?'warn':'ok','<b>'+(iss.length?'Imported with issues':'Imported')+'</b> '\r\n"
     "  +esc(fname)+' \\u00b7 '+fmt(out.length)+' councils read. '+esc(hrtMergeNote(mg))\r\n"
     "  +(iss.length?'<br><b>Check before this sheet is read to anyone:</b> '+esc(iss.join('; '))\r\n"
     "   +'. Full detail is in the import log below.':''));\r\n"
     " el('hrtDiv').value='';el('hrtDist').value='';\r\n"
     " hrtPage=0;hrtStore();hrtScope();hrtPaint(V);hrtNote();}"),

    ('csv-take', " const take=rows=>{if(!rows){hrtLogAdd(file.name+': no header row of this card was "
     "found in the CSV, so '\r\n   +'nothing was imported.');hrtRefresh();return;}\r\n"
     "  hrtRows=rows;hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());\r\n"
     "  toast('Imported '+fmt(rows.length)+' councils');};",
     " const take=rows=>{if(!rows){hrtLogAdd(file.name+': no header row of this card was found in the "
     "CSV, so '\r\n   +'nothing was imported.');hrtRefresh();\r\n"
     "   hrtImpBox('err','<b>Nothing imported</b> '+esc(file.name)+' \\u2014 no header row of this card "
     "was found in the CSV. In Excel use Save as \\u2192 Excel Workbook, or check the header row.');\r\n"
     "   return;}\r\n"
     "  const iss=hrtCheckRows(rows),mg=hrtMerge(rows);\r\n"
     "  hrtLogAdd('Imported '+fmt(rows.length)+' councils from '+file.name+'. '+hrtMergeNote(mg)+' '\r\n"
     "   +(iss.length?iss.join(' \\u00b7 '):''));\r\n"
     "  hrtImpBox(iss.length?'warn':'ok','<b>'+(iss.length?'Imported with issues':'Imported')+'</b> '\r\n"
     "   +esc(file.name)+' \\u00b7 '+fmt(rows.length)+' councils read. '+esc(hrtMergeNote(mg))\r\n"
     "   +(iss.length?'<br><b>Check before this sheet is read to anyone:</b> '+esc(iss.join('; '))\r\n"
     "    +'. Full detail is in the import log below.':''));\r\n"
     "  el('hrtDiv').value='';el('hrtDist').value='';\r\n"
     "  hrtPage=0;hrtStore();hrtScope();hrtPaint(hrtVals());hrtNote();\r\n"
     "  toast('Imported '+fmt(rows.length)+' councils \\u2014 the period now holds '\r\n"
     "   +fmt(hrtRows.length));};"),

    ('clearall-wire', "   hrtRows=[];try{localStorage.removeItem(HRTKEY(hrtSlug()));}catch(e){}\r\n"
     "   hrtRefresh();toast('This period is empty now');};\r\n",
     "   hrtRows=[];try{localStorage.removeItem(HRTKEY(hrtSlug()));}catch(e){}\r\n"
     "   hrtRefresh();toast('This period is empty now');};\r\n"
     "  el('btnHRTCLEARALL').onclick=()=>{\r\n"
     "   const ks=[];try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);\r\n"
     "    if(k&&k.indexOf(HRTKEY(''))===0)ks.push(k);}}catch(e){}\r\n"
     "   if(!ks.length){toast('This browser holds no saved HRA sheet');return;}\r\n"
     "   if(!window.confirm('Remove the HRA sheets this browser saved for '+ks.length+' period'\r\n"
     "    +(ks.length===1?'':'s')+' ('+ks.map(k=>k.slice(HRTKEY('').length)).join(', ')\r\n"
     "    +')? A file you already downloaded is untouched.'))return;\r\n"
     "   ks.forEach(k=>{try{localStorage.removeItem(k);}catch(e){}});\r\n"
     "   hrtRefresh();toast('Removed every saved HRA sheet from this browser');};\r\n"),

    ('refresh-clear', "function hrtRefresh(){\r\n hrtWire();",
     "function hrtRefresh(){\r\n hrtWire();\r\n hrtImpBox('');"),

    ('hint', "  +'under the year, month and campaign above, and travels as the file you download. The "
     "card\\u2019s '\r\n  +'Remarks column is not on this grid and not in the dashboard payload.';",
     "  +'under the year, month and campaign above, and travels as the file you download. One division "
     "at a '\r\n"
     "  +'time: an upload replaces the districts its file covers and leaves every other district on the '\r\n"
     "  +'sheet alone, so one period compiles every division and the download carries them all. Duplicate '\r\n"
     "  +'rows are ignored, and anything that needs correcting is reported above the grid. The card\\u2019s '\r\n"
     "  +'Remarks column is not on this grid and not in the dashboard payload.';"),

    ('note-call', " el('hratNote').innerHTML=esc(HRT_P().join(' \\u00b7 '))+' \\u00b7 '+fmt(hrtRows.length)+' "
     "councils \\u00b7 '\r\n  +'file name <b>'+esc(hrtTitle())+'.xlsx</b>';}",
     " hrtNote();}"),
]


COUNT = {'note-call': 2}  # renderHRT() and hrtRefresh() write the same note line


def apply(t, edits):
    for name, old, new in edits:
        want = COUNT.get(name, 1)
        n = t.count(old)
        if n != want:
            raise SystemExit('anchor %r found %d times (expected %d) - the master no longer matches '
                             'what this patch was written against' % (name, n, want))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        want = COUNT.get(name, 1)
        n = t.count(new)
        if n != want:
            raise SystemExit('reverse anchor %r found %d times (expected %d) - not undoing something '
                             'this patch did not write' % (name, n, want))
        t = t.replace(new, old)
    return t


def check(t):
    for once in ('function hrtMerge(out)', 'function hrtDivs()', 'function hrtNote()',
                 'function hrtMergeNote(mg)', 'function hrtImpBox(kind,html)',
                 'function hrtCheckRows(rows)', 'const mg=hrtMerge(out)', 'mg=hrtMerge(rows)',
                 'id="btnHRTCLEARALL"', 'id="hratImp"', "el('btnHRTCLEARALL').onclick"):
        if t.count(once) != 1:
            raise SystemExit('ERR the merge patch is missing %r (%d copies)' % (once, t.count(once)))
    if t.count('\r\n hrtNote();}') != 2:
        raise SystemExit('ERR renderHRT/hrtRefresh do not call hrtNote() (%d)'
                         % t.count('\r\n hrtNote();}'))
    if t.count('out.push(row.slice())') != 1 or 'out.push(row);row.length=0' in t:
        raise SystemExit('ERR hrtCsv() still hands out the row it then empties')
    if t.count(' hrtRows=out;\r\n') or t.count('  hrtRows=rows;hrtPage=0;'):
        raise SystemExit('ERR an import path still replaces the whole period')
    i = t.index('function hrtFromSheet(')
    j = t.index('function hrtImport(', i)
    if 'hrtMerge(out)' not in t[i:j] or 'hrtImpBox(' not in t[i:j]:
        raise SystemExit('ERR hrtFromSheet() does not merge and report the imported rows')
    k = t.index('function hrtImport(', i)
    if 'hrtMerge(rows)' not in t[k:k + 3000] or 'hrtCheckRows(rows)' not in t[k:k + 3000]:
        raise SystemExit('ERR the CSV import does not merge and check the imported rows')


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
    built = 'function hrtMerge(out)' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the merge patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (function hrtMerge present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA merge %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                v.delta(), 'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
