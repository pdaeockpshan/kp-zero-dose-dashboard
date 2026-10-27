# -*- coding: utf-8 -*-
"""Land the month grain on the PTP class cuts (tPTg / pt6) so the period picker narrows them.

WHY (owner, 26-Oct-2026): "insert year/month filter option in PTPs all data tables". The district grid,
the UC listing, the reporting-coverage grid, the wastage ledger and the four search-team tables already
follow the pick. Three blocks did not: the class cuts on the coverage card (post type, post strategy,
age band) read district x class x year only and their own captions said so in as many words, and the
year-trend table's caption made a whole-year cross-check that a month pick quietly invalidated.

extract_ptp.py now ships `tdM`, `ddM` and `adM` beside `td`, `dd` and `ad` - the same
[district, class, cell] rows with the slot (`yearIndex*12 + month - 1`) where the year book carries the
year index, and the same four measures. The build refuses a month book unless every month set adds back
to its year cell and every year cell has month cells behind it, so nothing here re-implements that
check: a month row is the same sum cut finer, never a second measure.

What is deliberately left whole-span:
  - the two distinct-team columns and years-filed on the search-team card (unions over a whole span;
    patch_sta_month.py labels them, this module points at them from the tab hint);
  - the post roster that rides in the UC download;
  - tPTy keeps one row per year, because it exists to show the covy cut across years. With a month
    picked each row is that month inside its own year - a year row, not a cross-year month sum, which
    the extractor docstring forbids. The row label, the count line, the caption and the download all
    say so, and the "+7.38% on the reporting file" sentence only prints when the month box is empty,
    because it is a whole-year claim about a whole-year figure.

Edits all four variants with one identical sequence, like patch_sta_month.py: every anchor is a run of
lines the refresh pipeline keeps byte-identical across them, so this needs no push_master sync of its
own. It does need the month-grain payload, and since `GC()` would read undefined without `tdM`, the
three keys are asserted before anything is written.

Usage:
  python _refresh/patch_ptp_class_month.py --dry-run    anchor checks and per-variant diff
  python _refresh/patch_ptp_class_month.py              patch all four variants
  python _refresh/patch_ptp_class_month.py --unpatch    restore the year-only reading, text and all
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = '\r\n'


def L(*lines):
    return CRLF.join(lines)


# ---- the class readers: one grain test, one book picker ----
A_CMT = L(r' // pt6 + tPTg - the class cuts. Cells are district x class x year, so the month cannot narrow them.')
N_CMT = L(r' // pt6 + tPTg - the class cuts. Each class axis now ships two books of the same cells:',
          r' // district x class x year and those cells cut at the slot the district month book uses, so this',
          r' // card reads the grain the period control is at instead of denying it. The extractor refuses a',
          r' // month book unless each set of month cells adds back to its year cell, so the two views are one',
          r' // dataset cut finer and never two measures that can disagree.')

A_CLS = L(r' const clsagg=(cells,ci)=>{const o={rows:0,cov:0,used:0,zd:0,any:0};',
          r'  cells.forEach(r=>{if(r[1]!==ci)return; if(DI.indexOf(r[0])<0)return;',
          r'   o.any+=r[3][0];',
          r'   if(YCLS.indexOf(r[2])<0)return; o.rows+=r[3][0]; o.cov+=r[3][1]; o.used+=r[3][2]; o.zd+=r[3][3];});',
          r'  o.w=wsp(o.cov,o.used); o.f=fac(o.w); return o;};')
N_CLS = L(r' // a month row puts its slot where a year row puts its year index, so one test picks the grain',
          r' // and clsagg never asks which book it was handed. CG closes over YCLS, which is declared below',
          r' // and read only when the table draws - a string evaluated here instead would hit that',
          r' // declaration while it is still in its temporal dead zone and leave the whole card empty.',
          r' const CG=mv?(s=>YCLS.indexOf((s/12)|0)>=0&&s%12===mv-1):(j=>YCLS.indexOf(j)>=0);',
          r" const GC=a=>mv?PTP[a[3]+'M']:PTP[a[3]];",
          r" const CGN=mv?'month':'year';",
          r' const clsagg=(cells,ci)=>{const o={rows:0,cov:0,used:0,zd:0,any:0};',
          r'  cells.forEach(r=>{if(r[1]!==ci)return; if(DI.indexOf(r[0])<0)return;',
          r'   o.any+=r[3][0];',
          r'   if(!CG(r[2]))return; o.rows+=r[3][0]; o.cov+=r[3][1]; o.used+=r[3][2]; o.zd+=r[3][3];});',
          r'  o.w=wsp(o.cov,o.used); o.f=fac(o.w); return o;};')

A_CELL = L(r'   const cells=PTP[a[3]], names=PTP[a[2]];',
           r"   names.forEach((nm,ci)=>{const o=clsagg(cells,ci); o.lab=nm; o.n=0; if(!o.any)return;")
N_CELL = L(r'   const cells=GC(a), names=PTP[a[2]];',
           r'   // `any` stays whole-window on purpose: it says the class exists at all. With a month picked',
           r'   // the row is dropped a line later unless that month itself holds a report for it.',
           r"   names.forEach((nm,ci)=>{const o=clsagg(cells,ci); o.lab=nm; o.n=0; if(!o.any)return;")

# ---- the column that named its own grain ----
A_TT = L(r"   {k:'rows',l:'Reports',n:1,f:x=>x.rows==null?DASH:fmt(x.rows),",
         r"    tt:'Daily post reports carrying a wastage-usable year'},")
N_TT = L(r"   {k:'rows',l:'Reports',n:1,f:x=>x.rows==null?DASH:fmt(x.rows),",
         r"    tt:'Daily post reports in the period picked, summed at district x class x '+CGN+' - the '",
         r"     +'usable years run from '+PTP.covy+', so a class that reported only before that is a dash.'},")

# ---- the two captions that denied the pick ----
# N_C6 closes the mv group on the ternary line rather than the last line, and that is not a style
# choice: a `+ '...sentence...'` written while `(mv?(A) : (B)` is still open becomes part of B, so it
# prints for a year and disappears for a month. The bracket count stays right either way, node --check
# passes, and only the rendered caption shows the sentence was eaten.
A_C6 = L(r"      :('These rows are district x year cells, so they read the '+YCLS.length+' usable years from '+PTP.covy",
         r"       +' onwards and the month selector cannot narrow them.'))")
N_C6 = L(r"      :('These rows are class cells read at the grain of the pick, so '",
         r"       +(mv?('the month selected ('+_MON[mv-1]+'/'+yv+') IS the row')",
         r"            :('each row reads the '+YCLS.length+(YCLS.length===1?' usable year':' usable years')",
         r"             +' from '+PTP.covy+' onwards'+(YCLS.length===1?', whole year':', whole years')))",
         r"       +'. A month is one reporting burst: a class can read thin or empty here and full in the '",
         r"       +'year view beside it.'))")

A_CG = L(r"   :('Post type, post strategy and age band classify the <b>reporting row as the panel wrote it</b>, which is '",
         r"     +'why these rows add back to the province totals. They are district x <b>year</b> cells, so the month '",
         r"     +'selector cannot narrow them: each row covers '+YCLS.length+' usable years ('+PTP.covy+' onwards)'",
         r"     +(one?', read at '+yv:'')+'. Post status in the inventory table above is different \u2014 that attributes a '",
         r"     +'<b>post</b> to its most often seen type over the whole window. The class cells carry reports, coverage, '",
         r"     +'doses used and zero-dose, so the two dose-supply columns the division and corridor rows show are not '",
         r"     +'cut this way.'))")
N_CG = L(r"   :('Post type, post strategy and age band classify the <b>reporting row as the panel wrote it</b>, which is '",
         r"     +'why these rows add back to the province totals. The same cells ship twice - once per year and once '",
         r"     +'per month, the month rows on the slot the district month cells use - so this table reads the grain '",
         r"     +'the period control is at: '+(mv?('the month selected ('+_MON[mv-1]+'/'+yv+') is the whole row, and '",
         r"     +'a month is one reporting burst, so a class can be thin here and full in the year view')",
         r"     :('each row covers '+YCLS.length+(YCLS.length===1?' usable year':' usable years')+' from '",
         r"     +PTP.covy+' onwards, whole '+(YCLS.length===1?'year':'years')+(one?', read at '+yv:'')))",
         r"     +'. Post status in the inventory table above is different \u2014 that attributes a '",
         r"     +'<b>post</b> to its most often seen type over the whole window. The class cells carry reports, '",
         r"     +'coverage, doses used and zero-dose, so the two dose-supply columns the division and corridor rows '",
         r"     +'show are not cut this way.'))")

# ---- the count line, which may no longer deny the pick ----
A_CNT = L(r"  el('cntPTg').textContent=fmt(G.length)+' groups \u00b7 '+(per?PLab:(YCLS.length+' usable years, whole-year figures'));")
N_CNT = L(r"  el('cntPTg').textContent=fmt(G.length)+' groups \u00b7 '+PLab+' \u00b7 '",
          r"   +(per?('summed from district x '+CGN+' cells by '+(GKEY==='div'?'division':'corridor'))",
          r"        :('district x class x '+CGN));")

# ---- the download: the pick belongs in the file name, and the grain belongs in the file ----
A_DL = L(r" el('btnPTg').onclick=()=>csvDownload('ptp_coverage_grouped_'+GKEY+'_'+_slug()+'.csv',",
         r"  ['Group','Reports','Children covered','Doses used','Doses given','Doses returned','Wastage %',",
         r"   'Band','Order factor','Zero-dose found','Found per 100 reports','Period'],",
         r"  grows().map(x=>[x.lab,x.rows,x.cov,x.used,x.giv||'',x.ret||'',x.w==null?'':p1(x.w),",
         r"   x.w==null?'':BN[BAND(x.w)][0],x.f==null?'':(Math.round(x.f*100)/100).toFixed(2),",
         r"   x.zd,x.rows?p1(100*x.zd/x.rows):'',(GKEY==='div'||GKEY==='cor')?PLab:PTP.covy+' onwards']));")
N_DL = L(r" el('btnPTg').onclick=()=>csvDownload('ptp_coverage_grouped_'+GKEY+'_'",
         r"  +(one?(mv?(yv+'-'+mv):('y'+yv)):PTP.win)+'_'+_slug()+'.csv',",
         r"  ['Group','Reports','Children covered','Doses used','Doses given','Doses returned','Wastage %',",
         r"   'Band','Order factor','Zero-dose found','Found per 100 reports','Grouped at','Period'],",
         r"  grows().map(x=>[x.lab,x.rows,x.cov,x.used,x.giv||'',x.ret||'',x.w==null?'':p1(x.w),",
         r"   x.w==null?'':BN[BAND(x.w)][0],x.f==null?'':(Math.round(x.f*100)/100).toFixed(2),",
         r"   x.zd,x.rows?p1(100*x.zd/x.rows):'',",
         r"   (GKEY==='div'?'division':(GKEY==='cor'?'corridor':'class'))+' x district x '+CGN,PLab]));")

# ---- tPTy: still one row per year, now honest about which slice of each year ----
A_YL = L(r"  {k:'y',l:'Year',f:x=>'<b>'+x.y+'</b>'},")
N_YL = L(r"  {k:'y',l:mv?'Month of each year':'Year',f:x=>'<b>'+x.y+(mv?(' '+_MON[mv-1]):'')+'</b>'},")

A_YC = L(r"""  {k:'ok',l:'Published',f:x=>x.ok?'<span class="tag t-high">Yes</span>':'<span class="cnt">No \u2014 covered exceeds doses used</span>'}],""",
         r"  YR,'y',1);",
         r" el('cntPTy').textContent=fmt(YR.filter(x=>x.ok).length)+' of '+fmt(YR.length)+' years published';")
N_YC = L(r"""  {k:'ok',l:'Published',f:x=>x.ok?'<span class="tag t-high">Yes</span>':'<span class="cnt">No \u2014 covered exceeds doses used</span>'}],""",
         r"  YR,'y',1);",
         r" el('cntPTy').textContent=fmt(YR.filter(x=>x.ok).length)+' of '+fmt(YR.length)+' years published'",
         r"   +(mv?(' \u00b7 each row is '+_MON[mv-1]+' inside its own year'):(' \u00b7 whole years'));")

A_YCAP = L(r"  +'The reporting file and this export agree on it independently: the file pulled in early October gives +7.38% '",
           r"  +'for KP 2026, this one gives '+p1(YR.length?wsp(YR[YR.length-1].cov,YR[YR.length-1].used):null)+'%. '")
N_YCAP = L(r"  +(mv?('Every row here is the month selected ('+_MON[mv-1]+') read inside its own year: that is one '",
           r"      +'month of each year laid side by side, never a month summed across years, and no row is a year '",
           r"      +'entire - so the cross-check below only holds with the month box empty.')",
           r"      :('The reporting file and this export agree on it independently: the file pulled in early October '",
           r"       +'gives +7.38% for KP 2026, this whole-year read gives '",
           r"       +p1(YR.length?wsp(YR[YR.length-1].cov,YR[YR.length-1].used):null)+'%. '))")

A_YDL = L(r" el('btnPTy').onclick=()=>csvDownload('ptp_coverage_by_year_'+_slug()+'.csv',",
          r"  ['Year','Reports','Children covered','Doses used','Wastage %','Published from '+PTP.covy],",
          r"  YR.map(x=>[x.y,x.rows,x.cov,x.used,x.w==null?'':p1(x.w),x.ok?'Yes':'No']));")
N_YDL = L(r" el('btnPTy').onclick=()=>csvDownload('ptp_coverage_by_year_'",
          r"  +(one?(mv?(yv+'-'+mv):('y'+yv)):PTP.win)+'_'+_slug()+'.csv',",
          r"  [mv?'Month of each year':'Year','Reports','Children covered','Doses used','Wastage %',",
          r"   'Published from '+PTP.covy],",
          r"  YR.map(x=>[x.y+(mv?(' '+_MON[mv-1]):''),x.rows,x.cov,x.used,x.w==null?'':p1(x.w),x.ok?'Yes':'No']));")

# ---- the triangulation chip: its UC total is a panel roster, so name the span it was summed at ----
# SLab is deliberately not added: PTP.win and SLab read the same way in the default state, and the
# chip then printed the window twice.
A_CHIP = L(r" el('cntPTb').textContent=R.length+' district units \u00b7 '+K('ucs')+' PTP UCs';")
N_CHIP = L(r" el('cntPTb').textContent=R.length+' district units \u00b7 '+K('ucs')+' PTP UCs'",
           r"  +' on the '+PTP.win+' roster';")

# ---- the tab hint count that disagreed with its own list ----
# patch_ptp_cov.py wrote this four-line sentence joined with LF instead of CRLF, so on disk it is one
# 317-character physical line (valid JS, but no later anchor can point at a piece of it). The repair
# puts the line breaks back and, in the same pass, stops the prose claiming four held-back columns
# while PTP.hold - printed right beside it - carries eight.
A_HOLD = L(r"  +' Post names, locations, facility names and remarks are excluded, and so are four columns that '  +'stopped being filled or never reconcile ('+PTP.hold.join(', ')+'). Coverage and OPV are now '  +'published from '+PTP.covy+' on, under the definition in the HRMP reporting file - see the '  +'coverage block below.'")
N_HOLD = L(r"  +' Post names, locations, facility names and remarks are excluded, and so are '+PTP.hold.length+' columns that '",
           r"  +'stopped being filled or never reconcile ('+PTP.hold.join(', ')+'). Coverage and OPV are now '",
           r"  +'published from '+PTP.covy+' on, under the definition in the HRMP reporting file - see the '",
           r"  +'coverage block below.'")

# ---- the tab hint: which tables follow the pick, and what cannot ----
A_HINT = L(r"  +'across years. Every table on this page follows that pick, including the month-by-month '",
           r"  +'reporting-coverage grid, the three HRMP blocks and the union-council listing. All three follow the same pick, but the mobile-team block stops where its Apr-2025 export stops - four of its six forms were not being filed after that - while the search-team block below it runs to Oct-2026, so a late period is a dash in one and a figure in the other.'")
N_HINT = L(r"  +'across years. Every table on this page follows that pick, including the month-by-month '",
           r"  +'reporting-coverage grid, the wastage ledger, the class cuts (post type, strategy, age band), '",
           r"  +'the year trend and the union-council listing. What does not narrow says so where it appears: '",
           r"  +'the two distinct-team counts and the years-filed column on the search-team card are unions '",
           r"  +'over a whole span, the post roster that rides in the union-council download is the whole '",
           r"  +'window, and the year trend keeps one row per year even with a month picked - each of those '",
           r"  +'rows is then that month inside its own year. The rosters never narrow by design: posts listed '",
           r"  +'and UCs with a PTP are panel listings over '+PTP.win+', and so are the campaign and routine EPI '",
           r"  +'columns matched beside them. The three HRMP blocks follow the same '",
           r"  +'pick, but the mobile-team block stops where its Apr-2025 export stops - four of its six forms '",
           r"  +'were not being filed after that - while the search-team block below it runs to Oct-2026, so '",
           r"  +'a late period is a dash in one and a figure in the other.'")

PAIRS = [(A_CMT, N_CMT), (A_CLS, N_CLS), (A_CELL, N_CELL), (A_TT, N_TT), (A_CHIP, N_CHIP),
         (A_C6, N_C6), (A_CG, N_CG), (A_CNT, N_CNT), (A_DL, N_DL),
         (A_YL, N_YL), (A_YC, N_YC), (A_YCAP, N_YCAP), (A_YDL, N_YDL),
         (A_HOLD, N_HOLD), (A_HINT, N_HINT)]

NEW_MARKS = ("const CG=mv?(s=>YCLS.indexOf", "const GC=a=>mv?PTP[a[3]+'M']", "const CGN=mv?'month':'year'",
             "summed at district x class x '+CGN", "'Grouped at'", "l:mv?'Month of each year':'Year'",
             "this whole-year read gives", "What does not narrow says so where",
             "on the '+PTP.win+' roster", r"and so are '+PTP.hold.length+' columns")
OLD_MARKS = ("the month cannot narrow them", "These rows are district x year cells",
             "They are district x <b>year</b> cells", "Daily post reports carrying a wastage-usable year",
             "' years published';", "reporting-coverage grid, the three HRMP blocks",
             "(GKEY==='div'||GKEY==='cor')?PLab:PTP.covy+' onwards'",
             "csvDownload('ptp_coverage_by_year_'+_slug()",
             "csvDownload('ptp_coverage_grouped_'+GKEY+'_'+_slug()",
             r"district units \u00b7 '+K('ucs')+' PTP UCs';", "and so are four columns that")


def scan(tag, frag):
    """Read the new JS line by line and in pairs, for the two ways a raw-string line list lies.

    A JS single-quoted string cannot cross a line, so a fragment written one Python string per JS
    line can only be broken by a quote that was mistranscribed. Three shapes, none of which a
    bracket-balance check on a partial fragment can see, and all of which a per-line quote count
    catches: an odd number of single quotes on one line (a closing quote went missing); a line
    ending with a quote followed by a line opening one (the sentence was split and the first half
    dropped); a line ending in `+` followed by a line starting with `+'` (the reader gets NaN).
    `node --check` on the extracted inline <script> is still the real syntax gate after this.
    """
    lines = frag.split(CRLF)
    for n, s in enumerate(lines, 1):
        if (s.count("'") - s.count("\\'")) % 2:
            raise SystemExit('%s: line %d has an unterminated quote: %r' % (tag, n, s[:120]))
    for a, b in zip(lines, lines[1:]):
        if a.rstrip().endswith("'") and b.lstrip().startswith("'"):
            raise SystemExit('%s: text dropped between line pairs %r / %r' % (tag, a[-60:], b[:60]))
        if a.rstrip().endswith('+') and b.lstrip().startswith("+'"):
            raise SystemExit('%s: NaN risk between lines %r / %r' % (tag, a[-60:], b[:60]))


def net(frag):
    """The bracket depth a fragment leaves behind, ignoring brackets inside single-quoted JS strings.

    Every anchor here is a run of lines inside one big `el('cap').textContent=(A ? (X) : (Y))`
    expression, so a replacement that closes one fewer bracket than it replaced does not break the
    line it broke - it orphans the *next* branch, and `node --check` reports the missing close at the
    ':' of a caption several lines below, nowhere near the edit. Comment lines are skipped, since
    their brackets are prose.
    """
    d = 0
    for line in frag.split(CRLF):
        s = line.strip()
        if s.startswith('//'):
            continue
        q = False
        i = 0
        while i < len(s):
            c = s[i]
            if q:
                if c == '\\':
                    i += 2
                    continue
                if c == "'":
                    q = False
            elif c == "'":
                q = True
            elif c == '(' or c == ')':
                d += 1 if c == '(' else -1
            i += 1
    return d


def edits(reverse):
    seq = list(PAIRS)
    return [(b, a) for a, b in reversed(seq)] if reverse else seq


def apply(v, seq):
    for old, new in seq:
        v.require(v.count(old) == 1,
                  'anchor occurs %d times (want 1): %r' % (v.count(old), old[:90]))
        v.text = v.text.replace(old, new, 1)


def check(v, applied):
    if applied:
        for p in NEW_MARKS:
            v.require(v.count(p) >= 1, 'the applied build lost %r (%d)' % (p, v.count(p)))
        for p in OLD_MARKS:
            v.require(v.count(p) == 0, 'the year-only claim survived: %r' % p)
        # a month book the renderer cannot read is worse than no month book at all
        v.require(all(v.count('"%s"' % k) == 1 for k in ('tdM', 'ddM', 'adM')),
                  'the embedded const PTP carries no class month arrays - run '
                  'python _refresh/refresh.py run --only ptp first')
        v.require(v.count('const clsagg=') == 1 and v.count("drawTable('tPTg'") == 1
                  and v.count("drawTable('tPTy'") == 1, 'the PTP coverage block came apart')
        for idm in ('cntPTg', 'capPTg', 'cappt6', 'cntPTy', 'capPTy'):
            v.require(v.count("el('%s')" % idm) >= 1, '%s lost its writer' % idm)
    else:
        for p in NEW_MARKS:
            v.require(v.count(p) == 0, 'reversal left the month-grain mark %r behind (%d)'
                      % (p, v.count(p)))
        for p in OLD_MARKS:
            v.require(v.count(p) >= 1, 'reversal did not restore %r (%d)' % (p, v.count(p)))
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    applied = not a.unpatch
    seq = edits(a.unpatch)
    for i, (old, new) in enumerate(PAIRS, 1):
        if net(old) != net(new):
            raise SystemExit('PTP-CLASS-MONTH edit %d moves the bracket net of the statement it sits '
                             'inside (%d -> %d), so the surrounding ternary stops closing: %r'
                             % (i, net(old), net(new), new[:80]))
    if applied:
        for i, (_, new) in enumerate(seq, 1):
            scan('PTP-CLASS-MONTH edit %d' % i, new)
    for v in vs:
        if 'const clsagg=' not in v.text:
            raise SystemExit('%s: no PTP class block - the coverage card has to be patched in first' % v.rel)
        had = v.count(NEW_MARKS[0])
        if applied and had:
            raise SystemExit('%s: the class month grain is already applied' % v.rel)
        if a.unpatch and not had:
            raise SystemExit('%s: the class month grain is not applied, nothing to reverse' % v.rel)
        apply(v, seq)
        check(v, applied)
        v.changes.append('PTP class month grain %s (%+d chars)'
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
    print('OK ptp-class-month - %s' % ('the class cuts and the year trend follow the period pick in '
                                       'all four variants' if applied else
                                       'the class cuts read district x year again, text and all'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
