# -*- coding: utf-8 -*-
"""Send the PTP tab's tables out as formatted Excel instead of CSV (owner, 26-Oct-2026).

WHY: "what if we can replace CSV with properly format excel sheet download option. CSV is little off
color and dont look appropriate". These are briefing attachments, and a CSV opens as a grey block of
text - no header that stands out, no frozen row, no filters, and every number left-aligned as a
string so the recipient has to convert it before sorting anything.

HOW, and why it touches no call site: the tab's fifteen download buttons all call the shared
csvDownload with a file name that belongs to this tab (ptp_..., hrmp_..., nov26_focus_...). Those
prefixes are the routing test, so one dispatcher at the helper is enough and the fifteen onclicks -
each of which builds its own columns and rows at click time, after the table has been sorted - stay
byte-identical. csvRaw is the old body, unchanged, and stays the sink for every other tab and for the
fallback.

ExcelJS is fetched on the first press rather than on page load (about a megabyte, and the charts
already come from the same CDN), and if it never answers the same columns and rows go out as CSV with
a toast that says which format arrived - a briefing must not fail because a CDN did.

The "Download the tab" button collects through the same buttons rather than re-describing them: it
sets XLQ, fires each tab button's own handler, and takes what they register. A second copy of fifteen
column lists would be a second source of truth, and the first to drift.

Usage:
  python _refresh/patch_ptp_excel.py --dry-run    anchor checks and per-variant diff
  python _refresh/patch_ptp_excel.py              patch all four variants
  python _refresh/patch_ptp_excel.py --unpatch    restore the CSV downloads, text and all
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
# the quote/continuation and bracket-net gates live with the sibling module that built them; reuse
# them rather than re-typing a weaker version of the same check.
from patch_ptp_class_month import CRLF, L, scan, net

PANE = '<section class="pane" id="p-ptp">'

# ---- the download layer: csvDownload becomes a dispatcher, Excel joins it ----
A_CSV = L(r"function csvDownload(name,H,rows){",
          r""" const q_=v=>'"'+String(v==null?'':v).replace(/"/g,'""')+'"';""",
          r""" const csv='\ufeff'+[H,...rows].map(x=>x.map(q_).join(',')).join('\r\n');""",
          r""" try{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download=name;document.body.appendChild(a);a.click();a.remove();toast('CSV downloaded ('+rows.length+' rows)');}""",
          r" catch(e){toast('Download blocked here. Open the dashboard file in a browser to download.');}",
          r"}")

N_CSV = r"""function csvRaw(name,H,rows){
 const q_=v=>'"'+String(v==null?'':v).replace(/"/g,'""')+'"';
 const csv='\ufeff'+[H,...rows].map(x=>x.map(q_).join(',')).join('\r\n');
 try{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download=name;document.body.appendChild(a);a.click();a.remove();toast('CSV downloaded ('+rows.length+' rows)');}
 catch(e){toast('Download blocked here. Open the dashboard file in a browser to download.');}
}
// ---------- formatted Excel for the PTP tab ----------
// The PTP file names are this tab's own tables, so the prefix test below is what routes them; every
// other tab keeps csvRaw. ExcelJS is about a megabyte, so it is asked for on the first press and not
// on page load, from the same CDN the charts already use. If it never answers, the same columns and
// rows go out as CSV and the toast says which one arrived: a briefing must not fail over a CDN.
const XLP=/^(ptp_|hrmp_|nov26_focus_)/;
const XLURL='https://cdn.jsdelivr.net/npm/exceljs@4.4.0/dist/exceljs.min.js';
const XLTAB={ptp_district_inventory:'District inventory',ptp_triangulation:'UC triangulation',
 ptp_union_councils:'Union councils',ptp_reporting_coverage:'Reporting coverage',
 ptp_field_checks:'HRMP field checks',ptp_coverage_grouped:'Class cuts',
 ptp_coverage_wastage:'Wastage ledger',ptp_coverage_by_year:'Year trend',
 hrmp_mobile_migrant_teams:'Mobile migrant teams',hrmp_search_teams_forms:'Forms filed',
 hrmp_search_teams_district:'Search teams by district',hrmp_search_teams_antigen_ladder:'Antigen ladder',
 hrmp_search_teams_checklist_items:'Checklist items',hrmp_search_teams_activity_vs_checklist:'Activity vs checklist',
 hrmp_search_teams_vs_epi_register:'Search teams vs EPI',nov26_focus_districts:'Focus districts',
 nov26_focus_union_councils:'Focus union councils'};
let XLb=null,XLp=null,XLQ=null,PTPC=null;
function csvDownload(name,H,rows){XLP.test(name)?xlsxDownload(name,H,rows):csvRaw(name,H,rows);}
function xlLib(){
 if(XLb) return Promise.resolve(XLb);
 if(!XLp) XLp=new Promise((res,rej)=>{const s=document.createElement('script');s.src=XLURL;
  s.onload=()=>{XLb=window.ExcelJS||null;if(XLb)res(XLb);else{XLp=null;rej(new Error('ExcelJS absent'));}};
  s.onerror=()=>{XLp=null;rej(new Error('ExcelJS blocked'));};document.head.appendChild(s);});
 return XLp;
}
const xlStem=n=>String(n).replace(/\.csv$/,'');
// the sheet tab says what the table is; the file name says what period it was read at, and the two
// carry the same prefix so the longest match wins (the search-team stems nest inside each other).
const xlTab=n=>{const s=xlStem(n),k=Object.keys(XLTAB).filter(x=>s.indexOf(x)===0)
 .sort((a,b)=>b.length-a.length)[0];return k?XLTAB[k]:s.replace(/_/g,' ').slice(0,31);};
const xlNum=(v,isPct)=>{if(typeof v==='number')return isFinite(v)?v:null;
 if(typeof v!=='string')return null;const t=v.trim();
 // a percent column reaches the download as screen text, so '72.8%' has to land as the number
 // 72.8 with the sign dropped; stripping inside xlNum keeps the numeric test and the written
 // value on one rule instead of two that can disagree.
 const s=isPct&&/%$/.test(t)?t.slice(0,-1).trim():t;
 if(!/^-?\d+(\.\d+)?$/.test(s))return null;
 // a code written with a leading zero is an identifier, not a quantity - the IDIMS district
 // code '09' would otherwise land as 9 and misreport which record the row belongs to.
 if(/^[-+]?0\d/.test(s))return null;
 return Number(s);};
function xlSheet(wb,sp){
 const H=sp.H;
 // a dash is how the tables print "no figure"; in Excel that cell must be empty, not the character
 const data=sp.rows.map(r=>H.map((_,j)=>{const v=r[j];
  if(v===null||v===undefined)return null;const t=(typeof v==='string')?v.trim():v;
  return (t===''||t==='\u2013')?null:t;}));
 const pct=H.map(h=>/%$/.test(String(h).trim()));
 const num=H.map((h,j)=>{let seen=false,ok=true;
  data.forEach(r=>{const v=r[j];if(v===null)return;seen=true;if(xlNum(v,pct[j])===null)ok=false;});
  return seen&&ok;});
 const dec=H.map((h,j)=>num[j]&&data.some(r=>r[j]!==null&&xlNum(r[j],pct[j])%1!==0));
 const ws=wb.addWorksheet(String(sp.sheet).slice(0,31),{views:[{state:'frozen',ySplit:1}]});
 ws.getRow(1).values=H;
 data.forEach(r=>{const row=ws.addRow();
  r.forEach((v,j)=>{const c=row.getCell(j+1);if(v===null)return;
   if(num[j]){c.value=xlNum(v,pct[j]);c.alignment={horizontal:'right'};
    c.numFmt=pct[j]?'0.0"%"':(dec[j]?'#,##0.0#':'#,##0');}
   else c.value=v;});});
 H.forEach((h,j)=>{let w=String(h).length+2;
  data.forEach(r=>{const v=r[j];if(v===null)return;const l=String(v).length+(num[j]?6:0);
   if(l+2>w)w=l+2;});
  ws.getColumn(j+1).width=Math.max(9,Math.min(46,w));});
 const hr=ws.getRow(1);
 hr.height=32;hr.font={bold:true,color:{argb:'FFFFFFFF'}};
 hr.alignment={vertical:'middle',horizontal:'left',wrapText:true};
 hr.eachCell(c=>{c.fill={type:'pattern',pattern:'solid',fgColor:{argb:'FF5B21B6'}};});
 // autoFilter only after the rows exist, or the filter range stops at the header
 ws.autoFilter={from:{row:1,column:1},to:{row:ws.rowCount,column:H.length}};
 return ws;
}
// the workbook mixes tables read at different grains, so it needs the sentence the page already makes
function xlMeta(wb){
 const L=PTPC||{},ws=wb.addWorksheet('Read me',{views:[{showGridLines:false}]});
 ws.getColumn(1).width=24;ws.getColumn(2).width=112;
 const add=(a,b)=>{const r=ws.addRow([a,String(b==null?'':b)]);
  r.getCell(1).font={bold:true};r.alignment={vertical:'top',wrapText:true};};
 add('Workbook','Every sheet here is a table from the PTP tab of the KP Polio and Synergy Dashboard, '+
  'at the period picked on that tab when the file was made.');
 if(L.per)add('Reporting period',L.per);
 if(L.slab)add('Period the figures carry',L.slab);
 if(L.slug)add('Division / District filter',L.slug);
 if(L.src)add('Source',L.src+(L.asof?(' (as at '+L.asof+')'):''));
 if(L.win)add('Panel window',L.win);
 if(L.covy!=null)add('Coverage published from',L.covy);
 add('What does not narrow','Posts listed, UCs with a PTP and the campaign and routine EPI columns '+
  'beside them are panel rosters over the whole window, not period figures; the distinct-team counts '+
  'and the years-filed column are unions over a span. The Period column on each sheet says which '+
  'reading a row carries.');
 add('Counts, not children','The panel files one row per post per day, so a child seen twice in a '+
  'week is counted twice. Findings columns are signal, not coverage.');
 if(L.hold)add('Columns held back',L.hold);
 add('Made',new Date().toLocaleString());
 return ws;
}
function xlWrite(file,sheets,meta){
 return xlLib().then(X=>{const wb=new X.Workbook();
  wb.creator='KP Polio and Synergy Dashboard';wb.created=new Date();wb.title=xlStem(file);
  // the Read-me sheet goes in first so the file opens on the period, the source and the columns
  // held back, not on a number that has no grain attached to it yet
  if(meta)xlMeta(wb);
  sheets.forEach(sp=>xlSheet(wb,sp));
  return wb.xlsx.writeBuffer();}).then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();return true;});
}
function xlsxDownload(name,H,rows){
 if(XLQ){XLQ.push({sheet:xlTab(name),H,rows});return;}
 xlWrite(xlStem(name)+'.xlsx',[{sheet:xlTab(name),H,rows}],false)
  .then(()=>toast('Excel downloaded ('+rows.length+' rows)'))
  .catch(()=>{csvRaw(name,H,rows);
   toast('Excel library did not load, so the same table went out as CSV');});
}
// one workbook for the whole tab, collected through the tab\'s own buttons so the column lists stay
// in one place. Each handler still builds its rows at click time, so the sheet matches the table as
// it is sorted on screen.
const XLTABS=['btnPTc','btnPTm','btnMTf','btnSTf','btnSTd','btnSTl','btnSTi','btnSTk','btnSTe',
 'btnPTcov','btnPTg','btnPTy','btnPTa','btnPTb','btnPTu','btnFOCd','btnFOCu'];
function xlsxWorkbook(){
 const keep=XLQ;XLQ=[];
 XLTABS.forEach(id=>{const b=el(id);if(b&&b.onclick){try{b.onclick();}catch(e){}}});
 const q=XLQ;XLQ=keep;
 if(!q.length){toast('Nothing on this tab was ready to collect');return;}
 const st=el('ptXStatus');if(st)st.textContent='Building '+q.length+' sheets...';
 xlWrite('ptp_tab_'+(PTPC?PTPC.slug:'all')+'_'+(PTPC?PTPC.fseg:'window')+'.xlsx',q,true)
  .then(()=>{if(st)st.textContent='';toast('Workbook downloaded ('+q.length+' tables plus the Read-me sheet)');})
  .catch(()=>{if(st)st.textContent='';q.forEach(sp=>csvRaw(sp.sheet+'.csv',sp.H,sp.rows));
   toast('Excel library did not load, so each sheet went out as its own CSV');});
}"""
N_CSV_L = CRLF.join(N_CSV.split('\n'))

# ---- the tab control bar: one more button, and a place to say what it is doing ----
# Anchored mid-line on the two elements the new button goes between: the bar is one long physical
# line and the presentation button in it carries a glyph, so neither belongs in an anchor.
A_BAR = (r'<span class="cnt" id="ptNote"></span>'
         r'<button class="btn" id="btnPTPDeck"')
N_BAR = (r'<span class="cnt" id="ptNote"></span>'
         r'<button class="btn" id="btnPTX" title="Every table on this tab as one Excel workbook, '
         'with a Read-me sheet naming the period, the source and what does not narrow">'
         'Download the tab (Excel)</button><span class="cnt" id="ptXStatus"></span>'
         r'<button class="btn" id="btnPTPDeck"')

# Anchored on the line that declares PLab, not on the tab hint above it: PLab is a const further down
# renderPTP, so reading it in the hint's tail is a temporal-dead-zone ReferenceError that aborts the
# render - the hint still prints and then every KPI, table and download handler below it is missing.
# ---- the context the Excel Read-me sheet prints, and the workbook button ----
A_CTX = L(r" const PLab=one?(mv?(_MON[mv-1]+' '+yv):String(yv)):(PTP.covy+' \u2013 '+LY+' (from '+PTP.covy+')');")
N_CTX = L(r" const PLab=one?(mv?(_MON[mv-1]+' '+yv):String(yv)):(PTP.covy+' \u2013 '+LY+' (from '+PTP.covy+')');",
          r" // what the Excel downloads print on their Read-me sheet: the period this render is at,",
          r" // the source behind it and the columns held back. PTPC is refreshed on every render, so a",
          r" // workbook can never describe a period the page is not showing.",
          r" PTPC={per:PLab,slab:SLab,win:PTP.win,covy:PTP.covy,src:PTP.src,asof:PTP.asof,",
          r"  slug:_slug(),fseg:(one?(mv?(yv+'-'+mv):('y'+yv)):PTP.win),hold:(PTP.hold||[]).join(', ')};",
          r" el('btnPTX').onclick=xlsxWorkbook;")

# ---- the district column the transit-point downloads carry ----
# The value behind it is the IDIMS spelling of the district (ABOTABAD beside Abbottabad), not a
# number - the extractor maps it from the export's own name list, and the UC criteria beside it
# is looked up through the same string. A header that promises a code sends the reader hunting
# for digits that the source never had.
A_RAW1 = L(r"  ['Division','District','IDIMS district code','Corridor','UC criteria','Posts in panel','Reporting district-months',")
N_RAW1 = L(r"  ['Division','District','IDIMS name as filed','Corridor','UC criteria','Posts in panel','Reporting district-months',")
A_RAW2 = L(r"  ['Division','District','IDIMS district code','UC criteria','PTPs in panel','Posts with a status','Reported functional',")
N_RAW2 = L(r"  ['Division','District','IDIMS name as filed','UC criteria','PTPs in panel','Posts with a status','Reported functional',")
A_RAW3 = L(r"  ['Division','District','IDIMS district code','UC criteria','UCs with a PTP','UCs on the UC map','UCs in campaign ZD data',")
N_RAW3 = L(r"  ['Division','District','IDIMS name as filed','UC criteria','UCs with a PTP','UCs on the UC map','UCs in campaign ZD data',")
A_RAW4 = L(r"  ['Division','District','IDIMS district code','UC criteria','Channels flagged (of 5)','In Nov-26 campaign scope',")
N_RAW4 = L(r"  ['Division','District','IDIMS name as filed','UC criteria','Channels flagged (of 5)','In Nov-26 campaign scope',")

PAIRS = [(A_CSV, N_CSV_L), (A_BAR, N_BAR), (A_CTX, N_CTX),
         (A_RAW1, N_RAW1), (A_RAW2, N_RAW2), (A_RAW3, N_RAW3), (A_RAW4, N_RAW4)]


NEW_MARKS = ('function csvRaw(name,H,rows){', 'function xlsxDownload(name,H,rows){',
             'function xlsxWorkbook(){', "const XLP=/^(ptp_|hrmp_|nov26_focus_)/",
             "id=\"btnPTX\"", 'el(\'btnPTX\').onclick=xlsxWorkbook;', 'PTPC={per:PLab,slab:SLab,', 'IDIMS name as filed')
OLD_MARKS = (L(r"function csvDownload(name,H,rows){",
               r""" const q_=v=>'"'+String(v==null?'':v).replace(/"/g,'""')+'"';"""),)

def pane_labels(v, applied):
    """Rename this tab's own buttons, and only this tab's, inside the p-ptp section."""
    i = v.text.index(PANE)
    j = v.text.index('</section>', i)
    # the scan starts after this pane's own opening tag, or the guard counts the pane it is inside
    v.require(v.text.count('<section class="pane"', i + len(PANE), j) == 0,
              'another pane opens inside p-ptp, so the section boundary is wrong (%s)' % v.rel)
    span = v.text[i:j]
    want = 'Download (Excel)' if applied else 'Download (CSV)'
    away = 'Download (CSV)' if applied else 'Download (Excel)'
    n, m = span.count(want), span.count(away)
    v.require(n == 0, '%d %s labels already in the PTP pane before relabelling (%s)'
              % (n, want, v.rel))
    v.require(m == 17, 'the PTP pane holds %d download buttons, not 17 (%s)' % (m, v.rel))
    v.text = v.text[:i] + span.replace(away, want) + v.text[j:]
    return m


def edits(reverse):
    seq = list(PAIRS)
    return [(b, a) for a, b in reversed(seq)] if reverse else seq


def apply(v, seq, applied):
    for old, new in seq:
        v.require(v.count(old) == 1, 'anchor occurs %d times (want 1): %r' % (v.count(old), old[:90]))
        v.text = v.text.replace(old, new, 1)
    n = pane_labels(v, applied)
    v.changes.append('%d PTP download buttons relabelled' % n)


def check(v, applied):
    if applied:
        for p in NEW_MARKS:
            v.require(v.count(p) >= 1, 'the applied build lost %r (%d)' % (p, v.count(p)))
        for p in OLD_MARKS:
            v.require(v.count(p) == 0, 'the old csvDownload body survived: %r' % p)
        # the router is the whole feature: if it no longer matches the tab's file names, every PTP
        # download silently reverts to CSV and nothing on the page says so.
        v.require(v.count("XLP.test(name)?xlsxDownload(name,H,rows):csvRaw(name,H,rows);") == 1,
                  'csvDownload no longer routes by file name')
        for stem in ('ptp_district_inventory', 'hrmp_search_teams_vs_epi_register',
                     'nov26_focus_union_councils'):
            v.require(v.count("csvDownload('%s_" % stem) >= 1,
                      'no PTP download uses the %s prefix, so the router would miss it' % stem)
        # every name the router can send to Excel must have a sheet tab, and every sheet tab must
        # still belong to a download that exists - otherwise a renamed file silently loses its label
        for k in XLTAB_KEYS:
            v.require(v.count("csvDownload('%s" % k) >= 1,
                      'XLTAB names %s but no download on the page still uses that stem' % k)
        v.require(v.count('ws.autoFilter=') == 1 and v.count("addWorksheet(String(sp.sheet)") == 1,
                  'the sheet writer came apart')
        for idm in ('btnPTX', 'ptXStatus'):
            v.require(v.count('id="%s"' % idm) == 1, '%s is not on the page exactly once' % idm)
        n_id = v.count("'IDIMS name as filed'")
        v.require(n_id == 4,
                  'the transit-point downloads print %d IDIMS name columns, not the 4 the '
                  'relabel pair list expects' % n_id)
    else:
        for p in NEW_MARKS:
            v.require(v.count(p) == 0, 'reversal left the Excel mark %r behind (%d)' % (p, v.count(p)))
        for p in OLD_MARKS:
            v.require(v.count(p) >= 1, 'reversal did not restore %r (%d)' % (p, v.count(p)))
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')


XLTAB_KEYS = ('ptp_district_inventory', 'ptp_triangulation', 'ptp_union_councils',
              'ptp_reporting_coverage', 'ptp_field_checks', 'ptp_coverage_grouped',
              'ptp_coverage_wastage', 'ptp_coverage_by_year', 'hrmp_mobile_migrant_teams',
              'hrmp_search_teams_forms', 'hrmp_search_teams_district',
              'hrmp_search_teams_antigen_ladder', 'hrmp_search_teams_checklist_items',
              'hrmp_search_teams_activity_vs_checklist', 'hrmp_search_teams_vs_epi_register',
              'nov26_focus_districts', 'nov26_focus_union_councils')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    applied = not a.unpatch
    for i, (old, new) in enumerate(PAIRS, 1):
        if net(old) != net(new):
            raise SystemExit('PTP-EXCEL edit %d moves the bracket net of the statement it sits '
                             'inside (%d -> %d): %r' % (i, net(old), net(new), new[:80]))
    if applied:
        scan('PTP-EXCEL edit 2 (bar)', N_BAR)
        scan('PTP-EXCEL edit 3 (context)', N_CTX)
        # the inserted block is whole functions, so it must net to zero on its own
        z = net(N_CSV_L)
        if z:
            raise SystemExit('the Excel helper block does not close itself (net %+d)' % z)
        # N_CSV is written with plain newlines and turned into CRLF on the way in, so the per-line
        # checks read the LF form
        for line, s in enumerate(N_CSV.split('\n'), 1):
            if s.lstrip().startswith('//'):
                continue
            if (s.count("'") - s.count("\\'")) % 2:
                raise SystemExit('PTP-EXCEL helper line %d has an unterminated quote: %r'
                                 % (line, s[:120]))
    for v in vs:
        v.require(PANE in v.text, '%s has no PTP pane' % v.rel)
        had = v.count('function csvRaw(')
        if applied and had:
            raise SystemExit('%s: the Excel download layer is already applied' % v.rel)
        if a.unpatch and not had:
            raise SystemExit('%s: no Excel download layer to reverse' % v.rel)
        apply(v, edits(a.unpatch), applied)
        check(v, applied)
        v.changes.append('PTP Excel downloads %s (%+d chars)'
                         % ('in' if applied else 'reversed', v.delta()))
        print('  %-42s %+8d chars  %s' % (v.rel, v.delta(), '; '.join(v.changes)))
    sums = dashpatch.check_identical(cfg, vs)
    print('identical group md5: %s' % sums)
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    for v in vs:
        print('WROTE %s' % v.rel)
    print('OK ptp-excel - %s' % ('every PTP-tab download now goes out as a formatted workbook, with '
                                 'CSV kept as the fallback' if applied else
                                 'the PTP tab downloads CSV again, text and all'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
