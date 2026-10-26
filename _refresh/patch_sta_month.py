# -*- coding: utf-8 -*-
"""Land the month grain on the search-team (const STA) grids so the period picker narrows them.

WHY (owner, 26-Oct-2026): "insert year/month filter option in PTPs all data tables". The PTP period
control already narrowed the KPI strip, the district grid, the UC listing and the reporting-coverage
grid. The four tables on the search-team card - the antigen ladder, the checklist items, the
activity-versus-checklist link and the EPI-register comparison - could not, because const STA only
ever published district x year cells there and their own tooltips said so. extract_sta.py now ships
`alM`, `itM`, `lnkM` and `triM` beside the year books, and this module reads them.

What is guaranteed where, and by whom:
  - A month cell is the same sum cut finer, never a second measure. The row void rule fires in the
    extractor before either book is written, and `checks()` in extract_sta.py aborts the build unless
    every month book adds back to its year book, so nothing here re-implements the void rule.
  - A withheld ladder antigen is withheld from both books, so a month view can never show a number the
    year view refuses.
  - The two distinct-team columns and "years filed" on the link table stay whole-span, because a
    district-scoped union cannot be taken over a slice of it. Their tooltips now name which columns
    follow the pick and which do not, which is the rule the owner set for every published total.
  - With a month picked, a "team-month" count on that table is the teams that filed in that month: the
    month is already in the key, so it is the same number read at a narrower grain.
  - The EPI comparison narrows both registers to the picked period together, so the two figures that
    sit beside each other are always the same months.

Edits all four variants with one identical sequence, like patch_mpqa_framing.py: every anchor is a run
of lines the refresh pipeline keeps byte-identical across them, so this needs no push_master sync of
its own. It does need the month-grain payload, and since the patched `staTab()` would throw on a
payload without `alM`, that is asserted before anything is written.

Usage:
  python _refresh/patch_sta_month.py --dry-run   anchor checks and per-variant diff, writes nothing
  python _refresh/patch_sta_month.py             patch all four variants
  python _refresh/patch_sta_month.py --unpatch   restore the year-only reading, text and all
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = '\r\n'


def L(*lines):
    return CRLF.join(lines)


# ---- staTab(): index the four month books, and put the two link books on one column layout ----
A_DECL = r' const y={},m={},e={},k={},t={},l={},i={};'
N_DECL = r' const y={},m={},e={},k={},t={},l={},i={},lm={},im={},km={},tm={};'

A_LINK = L(r' STA.lnk.forEach(r=>{k[r[0]]=r});',
           r' STA.tri.forEach(r=>{t[r[0]]=r});')
N_LINK = L(r' STA.lnk.forEach(r=>{k[r[0]]=r.slice(1)});',
           r' STA.tri.forEach(r=>{t[r[0]]=r.slice(1)});',
           ' // a month row puts its slot where a window row puts its first value, so both books are',
           ' // sliced to the same columns and the readers below never ask which grain they were given',
           r' STA.lnkM.forEach(r=>{(km[r[0]]=km[r[0]]||{})[r[1]]=r.slice(2)});',
           r' STA.triM.forEach(r=>{(tm[r[0]]=tm[r[0]]||{})[r[1]]=r.slice(2)});')

A_ITEM = L(r" STA.it.forEach(r=>{((i[r[0]]=i[r[0]]||{})[r[1]]=i[r[0]][r[1]]||{})[r[2]]=r;});",
           r' return _STA={v:STA,y:y,m:m,e:e,k:k,t:t,l:l,i:i};')
N_ITEM = L(r" STA.it.forEach(r=>{((i[r[0]]=i[r[0]]||{})[r[1]]=i[r[0]][r[1]]||{})[r[2]]=r;});",
           r' STA.alM.forEach(r=>{((lm[r[0]]=lm[r[0]]||{})[r[1]]=lm[r[0]][r[1]]||{})[r[2]]=r;});',
           r' STA.itM.forEach(r=>{((im[r[0]]=im[r[0]]||{})[r[1]]=im[r[0]][r[1]]||{})[r[2]]=r;});',
           r' return _STA={v:STA,y:y,m:m,e:e,k:k,t:t,l:l,i:i,lm:lm,im:im,km:km,tm:tm};')

# ---- renderPTP(): the grain the whole card is now cut at, plus the two tooltip strings ----
A_CL = r'  const CL=i=>mv?SS.m[i][yi*12+mv-1]:SS.y[i][yi];'
N_CL = L(A_CL,
         r"  const SL=yi*12+mv-1, GJ=mv?[SL]:YJ, GN=mv?'district x month':'district x year';",
         r'  const LK=i=>(mv?SS.lm[i]:SS.l[i])||{}, IK=i=>(mv?SS.im[i]:SS.i[i])||{};',
         r'  const KK=i=>mv?(SS.km[i]||{})[SL]:SS.k[i], TK=i=>mv?(SS.tm[i]||{})[SL]:SS.t[i];')

# The two tooltip strings are read eagerly where they are declared, so they go after SPW, not next
# to the accessors above: `const MK=...+SPW` landing at the CL line would hit SPW's temporal dead
# zone, throw before the card draws a single row, and leave every table on the card empty.
A_SPW = r'  const SPW=STA.spans.sact;'
N_SPW = L(A_SPW,
          r"  const MK=mv?('With a month picked this is the teams that filed in that month in this "
          r"district - the month is already in the key, so the count is of teams, and the pick "
          r"narrows it.'):('Over the whole span this card reads ('+SPW+'), not the pick.');",
          r"  const EPP=mv?('the picked month ('+_MON[mv-1]+'/'+yv+')'):('the '+fmt(STA.epi.months."
          r"length)+' months both registers cover ('+STA.epi.per+')');")

A_LR = L(r'   if(!vw)SCOPE.forEach(i=>{const yy=SS.l[i]||{};',
         r'    YJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.n+=r[3]; o.t+=r[4]; o.c+=r[5]; '
         r'o.v+=r[6]; o.d++}})});')
N_LR = L(r'   if(!vw)SCOPE.forEach(i=>{const yy=LK(i);',
         r'    GJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.n+=r[3]; o.t+=r[4]; o.c+=r[5]; '
         r'o.v+=r[6]; o.d++}})});')

A_IR = L(r'   SCOPE.forEach(i=>{const yy=SS.i[i]||{};',
         r'    YJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.y+=r[3]; o.nn+=r[4]; o.b+=r[5]; '
         r'o.d++}})});')
N_IR = L(r'   SCOPE.forEach(i=>{const yy=IK(i);',
         r'    GJ.forEach(j=>{const r=yy[j]&&yy[j][x]; if(r){o.y+=r[3]; o.nn+=r[4]; o.b+=r[5]; '
         r'o.d++}})});')

A_KR = L(r'  const KR=SCOPE.filter(i=>SS.k[i]).map(i=>{const r=SS.k[i], e=SS.e[i]||[];',
         r'   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], a:r[1], b:r[2], o:r[3],',
         r'    at:e[1], mt:e[3], rep:Object.keys(SS.y[i]||{}).length};});')
N_KR = L(r'  const KR=SCOPE.map(i=>({i:i, r:KK(i)})).filter(x=>x.r).map(x=>{const i=x.i, r=x.r, ',
         r'e=SS.e[i]||[];',
         r'   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], a:r[0], b:r[1], o:r[2],',
         r'    at:e[1], mt:e[3], rep:Object.keys(SS.y[i]||{}).length};});')

A_XR = L(r'  const XR=SCOPE.filter(i=>SS.t[i]).map(i=>{const r=SS.t[i];',
         r'   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], e3:r[1], eb:r[2], s3:r[3], sz:r[4], re:r[5],',
         r'    h3:P(r[3], r[1]), hz:P(r[4], r[1])};});')
N_XR = L(r'  const XR=SCOPE.map(i=>({i:i, r:TK(i)})).filter(x=>x.r).map(x=>{const i=x.i, r=x.r;',
         r'   return {i:i, dn:PTP.ds[i], dv:PTP.dv[i], e3:r[0], eb:r[1], s3:r[2], sz:r[3], re:r[4],',
         r'    h3:P(r[2], r[0]), hz:P(r[3], r[0])};});')

# ---- the two count columns whose heading was nailed to district x year ----
A_DC1 = L(r"   {k:'d', l:'District-years', n:1, f:x=>W(x, x.d),",
          r"    tt:'District x year cells in scope that hold at least one row recording this pair. "
          r"This table is '",
          r"     +'district x year by construction, so the month picker cannot narrow it; a month "
          r"view reads the '",
          r"     +'whole year and says so in its count line.'},")
N_DC1 = L(r"   {k:'d', l:mv?'District x month':'District-years', n:1, f:x=>W(x, x.d),",
          r"    tt:GN+' cells in scope that hold at least one row recording this pair, and the period "
          r"picker '",
          r"     +'cuts this table at that grain: with a month picked every figure on the row is "
          r"summed over that '",
          r"     +'one month of the picked year. A target written for a month the team did not work "
          r"is still '",
          r"     +'caught by the void rule, which ran before either grain was written.'},")

A_DC2 = L(r"   {k:'d', l:'District-years', n:1, f:x=>d0(x.d),",
          r"    tt:'District x year cells in scope with at least one checklist answering this item. "
          r"District x '",
          r"     +'year by construction, so the month picker cannot narrow this table.'},")
N_DC2 = L(r"   {k:'d', l:mv?'District x month':'District-years', n:1, f:x=>d0(x.d),",
          r"    tt:GN+' cells in scope with at least one checklist answering this item, at the grain "
          r"the period '",
          r"     +' picker is at: a month view counts district-months and answers nothing outside "
          r"that month.'},")

# ---- the link table: three columns now follow the pick, three stay whole-span ----
A_LNK1 = L(r"   {k:'a', l:STA.lk[0], n:1, tt:'Distinct district + team number + month combinations "
           r"the activity '",
           r"    +'form filed in this district, over '+SPW+'. A team-month is one team working one "
           r"month in one '",
           r"    +'district, so this is not a report count.'},",
           r"   {k:'b', l:STA.lk[1], n:1, tt:'The same combination counted from the checklist side, "
           r"over '",
           r"    +STA.spans.smon+'.'},",
           r"   {k:'o', l:STA.lk[2], n:1, tt:'On both sides. Published as a count and never as a "
           r"rate: a district '",
           r"    +'with 144 activity team-months and 118 matched is a different finding from one "
           r"with 1 checklist '",
           r"    +'team-month against no activity at all, and a single percentage would flatten "
           r"both.'},")
N_LNK1 = L(r"   {k:'a', l:STA.lk[0], n:1, tt:'Distinct district + team number + month combinations "
           r"the activity '",
           r"    +'form filed in this district, over '+SPW+'. A team-month is one team working one "
           r"month in one '",
           r"    +'district, so this is not a report count. '+MK},",
           r"   {k:'b', l:STA.lk[1], n:1, tt:'The same combination counted from the checklist side, "
           r"over '",
           r"    +STA.spans.smon+'. '+MK+' It is that side of the pair alone, never the two columns "
           r"added '",
           r"    +'together.'},",
           r"   {k:'o', l:STA.lk[2], n:1, tt:'On both sides. Published as a count and never as a "
           r"rate: a district '",
           r"    +'with 144 activity team-months and 118 matched is a different finding from one "
           r"with 1 checklist '",
           r"    +'team-month against no activity at all, and a single percentage would flatten "
           r"both. It '",
           r"    +'follows the pick too, so a month view counts the teams that filed both forms that "
           r"month.'},")

A_LNK2 = L(r"   {k:'at', l:'Activity teams', n:1, tt:'Team numbers used on activity reports in this "
           r"district.'},",
           r"   {k:'mt', l:'Checklist teams', n:1, tt:'Team numbers used on monitoring checklists in "
           r"this district.'},",
           r"   {k:'rep', l:'Years filed', n:1, tt:'Year slots in the panel window where this "
           r"district has at '",
           r"    +'least one kept search-team row of either form.'}],")
N_LNK2 = L(r"   {k:'at', l:'Activity teams', n:1, tt:'Team numbers used on activity reports in this "
           r"district, '",
           r"    +'over '+SPW+'. Not narrowed by the period pick: it is a union of team numbers "
           r"across the whole '",
           r"    +'span, and a union cannot be taken for a slice of it.'},",
           r"   {k:'mt', l:'Checklist teams', n:1, tt:'Team numbers used on monitoring checklists in "
           r"this district, '",
           r"    +'over '+STA.spans.smon+'. The same rule as the column beside it - whole span, "
           r"never the pick.'},",
           r"   {k:'rep', l:'Years filed', n:1, tt:'Year slots in the panel window where this "
           r"district has at '",
           r"    +'least one kept search-team row of either form. Whole window by construction, so "
           r"the pick does '",
           r"    +'not narrow it: that is why a district can hold a row here in a month of one year "
           r"and still '",
           r"    +'count the years it filed beside it.'}],")

# ---- the EPI comparison: both registers move to the picked period together ----
A_EPI = L(r"   {k:'e3', l:STA.tk[0], n:1, tt:'From the facility EPI register (const EPIM), summed "
           r"over the '",
           r"    +fmt(STA.epi.months.length)+' months both registers cover ('+STA.epi.per+'). Doses "
           r"administered '",
           r"    +'through fixed and mobile sites.'},",
           r"   {k:'eb', l:STA.tk[1], n:1, tt:'The same register, BCG, same months.'},",
           r"   {k:'s3', l:STA.tk[2], n:1, tt:'From the search-team activity form over the same "
           r"months - the '",
           r"    +'covered side of the OPV-3 pair, after the void rule.'},",
           r"   {k:'sz', l:STA.tk[3], n:1, tt:'The covered side of the zero-dose pair from the same "
           r"form and the '",
           r"    +'same months. This is a search team finding a child with no prior dose, not a "
           r"register of '",
           r"    +'children who never got one.'},")
N_EPI = L(r"   {k:'e3', l:STA.tk[0], n:1, tt:'From the facility EPI register (const EPIM), summed "
           r"over '+EPP+'. '",
           r"    +'Doses administered through fixed and mobile sites.'},",
           r"   {k:'eb', l:STA.tk[1], n:1, tt:'The same register, BCG, the same period as the column "
           r"beside it.'},",
           r"   {k:'s3', l:STA.tk[2], n:1, tt:'From the search-team activity form over the same "
           r"period - the '",
           r"    +'covered side of the OPV-3 pair, after the void rule. Both registers move with the "
           r"pick, so the '",
           r"    +'two figures that sit beside each other are always the same months.'},",
           r"   {k:'sz', l:STA.tk[3], n:1, tt:'The covered side of the zero-dose pair from the same "
           r"form and the '",
           r"    +'same period. This is a search team finding a child with no prior dose, not a "
           r"register of '",
           r"    +'children who never got one.'},")

# ---- the count lines, which may no longer deny the pick ----
A_CNT = L(r"  el('cntSTl').textContent=STA.ag.length+' antigen pairs \u00b7 '+Object.keys("
          r"STA.agvoid).length",
          r"   +' withheld \u00b7 district x year, '+(one?String(yv):('all '+YJ.length+' years in "
          r"scope'))",
          r"   +(mv?' \u00b7 the month cannot narrow this table':'');",
          r"  el('cntSTi').textContent=IR.length+' of '+STA.ik.length+' item columns answered "
          r"\u00b7 '",
          r"   +STA.inever.length+' no row ever answered \u00b7 district x year, '",
          r"   +(one?String(yv):('all '+YJ.length+' years in scope'))+(mv?' \u00b7 the month cannot "
          r"narrow it':'');",
          r"  el('cntSTk').textContent=KR.length+' district units \u00b7 whole window '+SPW",
          r"   +' \u00b7 the period picked does not narrow this table';",
          r"  el('cntSTe').textContent=XR.length+' district units in both registers \u00b7 '",
          r"   +fmt(STA.epi.months.length)+' months of '+STA.epi.per+' \u00b7 not narrowed by the "
          r"period picked';")
N_CNT = L(r"  el('cntSTl').textContent=STA.ag.length+' antigen pairs \u00b7 '+Object.keys("
          r"STA.agvoid).length",
          r"   +' withheld \u00b7 '+GN+' \u00b7 '+SLab;",
          r"  el('cntSTi').textContent=IR.length+' of '+STA.ik.length+' item columns answered "
          r"\u00b7 '",
          r"   +STA.inever.length+' no row ever answered \u00b7 '+GN+' \u00b7 '+SLab;",
          r"  el('cntSTk').textContent=KR.length+' district units \u00b7 '+GN+' \u00b7 '+SLab",
          r"   +' \u00b7 the last three columns stay whole-span';",
          r"  el('cntSTe').textContent=XR.length+' district units in both registers \u00b7 '",
          r"   +(mv?('one month ('+_MON[mv-1]+'/'+yv+')'):(fmt(STA.epi.months.length)+' months of '"
          r"+STA.epi.per))+' \u00b7 '+GN;")

# ---- the caption's closing claim about what the pick reaches ----
A_CAP = L(r"   'Read every figure here as a count of forms and of what those forms wrote down. The "
          r"district table '",
          r"    +'sorts by activity reports, largest first, and follows the Reporting period pick, "
          r"the Division '",
          r"    +'filter and the District filter; the ladder, the item table and the two comparison "
          r"tables are '",
          r"    +'whole-window or district x year and their count lines say which.'")
N_CAP = L(r"   'Read every figure here as a count of forms and of what those forms wrote down. Every "
          r"table on '",
          r"    +'this card follows the Reporting period pick, the Division filter and the District "
          r"filter, at '",
          r"    +'the grain the pick is cut - district x month with a month picked, district x year "
          r"with a '",
          r"    +'whole year - and the district table sorts by activity reports, largest first. The "
          r"three columns '",
          r"    +'that do not narrow are the two distinct-team counts and years-filed on the "
          r"activity-versus-'",
          r"    +'checklist table: they are unions over the whole span, and their tooltips say so.'")

# ---- the four downloads: the pick belongs in the file name and in the header ----
A_DL1 = L(r"  el('btnSTl').onclick=()=>csvDownload('hrmp_search_teams_antigen_ladder_'+(one?String("
          r"yv):STA.win)",
          r"    +'_'+_slug()+'.csv',",
          r"   ['Antigen','Published','District-years','Reports recording the pair','Children "
          r"targeted',",
          r"    'Children covered','Rows voided','Voided per 100 reports','Covered per 100 targeted',"
          r"'Period'],",
          r"   LR.map(x=>[x.lab,x.wd?('withheld: '+x.wd[0]):'yes',x.wd?'':x.d,x.wd?'':x.n,x.wd?'':"
          r"x.t,",
          r"    x.wd?'':x.c,x.wd?'':x.v,x.wd?'':q1(x.vh),x.wd?'':q1(x.sh),one?String(yv):SPW]));")
N_DL1 = L(r"  el('btnSTl').onclick=()=>csvDownload('hrmp_search_teams_antigen_ladder_'+(one?(mv?(yv+"
          r"'-'+mv):('y'+yv)):STA.win)",
          r"    +'_'+_slug()+'.csv',",
          r"   ['Antigen','Published',mv?'District x month':'District-years','Reports recording the "
          r"pair','Children targeted',",
          r"    'Children covered','Rows voided','Voided per 100 reports','Covered per 100 targeted',"
          r"'Period'],",
          r"   LR.map(x=>[x.lab,x.wd?('withheld: '+x.wd[0]):'yes',x.wd?'':x.d,x.wd?'':x.n,x.wd?'':"
          r"x.t,",
          r"    x.wd?'':x.c,x.wd?'':x.v,x.wd?'':q1(x.vh),x.wd?'':q1(x.sh),one?(mv?(_MON[mv-1]+'/'+yv)"
          r":String(yv)):SPW]));")

A_DL2 = L(r"  el('btnSTi').onclick=()=>csvDownload('hrmp_search_teams_checklist_items_'+(one?String("
          r"yv):STA.win)",
          r"    +'_'+_slug()+'.csv',",
          r"   ['Checklist item','District-years','Answered yes','Answered no','Left blank',",
          r"    'Yes per 100 answered','Never answered by any row','Period'],",
          r"   IR.map(x=>[x.lab,x.d,x.y,x.nn,x.b,q1(x.sh),'','' ]).concat(",
          r"    STA.inever.map(c=>[STA.ikl[STA.ik.indexOf(c)],'', '', '', '', '', 'yes', ''])));")
N_DL2 = L(r"  el('btnSTi').onclick=()=>csvDownload('hrmp_search_teams_checklist_items_'+(one?(mv?(yv+"
          r"'-'+mv):('y'+yv)):STA.win)",
          r"    +'_'+_slug()+'.csv',",
          r"   ['Checklist item',mv?'District x month':'District-years','Answered yes','Answered no',"
          r"'Left blank',",
          r"    'Yes per 100 answered','Never answered by any row','Period'],",
          r"   IR.map(x=>[x.lab,x.d,x.y,x.nn,x.b,q1(x.sh),'',one?(mv?(_MON[mv-1]+'/'+yv):String(yv))"
          r":SPW]).concat(",
          r"    STA.inever.map(c=>[STA.ikl[STA.ik.indexOf(c)],'', '', '', '', '', 'yes', ''])));")

A_DL3 = L(r"  el('btnSTk').onclick=()=>csvDownload('hrmp_search_teams_activity_vs_checklist_'+STA.win"
          r"+'_'+_slug()",
          r"    +'.csv',",
          r"   ['Division','District','Activity team-months','Checklist team-months','Team-months "
          r"with both',",
          r"    'Activity teams','Checklist teams','Years filed','Window'],",
          r"   KR.map(x=>[x.dv,x.dn,x.a,x.b,x.o,x.at,x.mt,x.rep,SPW]));")
N_DL3 = L(r"  el('btnSTk').onclick=()=>csvDownload('hrmp_search_teams_activity_vs_checklist_'+(one?"
          r"(mv?(yv+'-'+mv):('y'+yv)):STA.win)+'_'+_slug()",
          r"    +'.csv',",
          r"   ['Division','District','Activity team-months','Checklist team-months','Team-months "
          r"with both',",
          r"    'Activity teams (whole span)','Checklist teams (whole span)','Years filed (whole "
          r"window)','Period'],",
          r"   KR.map(x=>[x.dv,x.dn,x.a,x.b,x.o,x.at,x.mt,x.rep,one?(mv?(_MON[mv-1]+'/'+yv):String("
          r"yv)):SPW]));")

A_DL4 = L(r"  el('btnSTe').onclick=()=>csvDownload('hrmp_search_teams_vs_epi_register_'+STA.epi.per"
          r".replace('-','to')",
          r"    +'.csv',")
N_DL4 = L(r"  el('btnSTe').onclick=()=>csvDownload('hrmp_search_teams_vs_epi_register_'+(mv?(yv+'-'"
          r"+mv):(one?('y'+yv):STA.epi.per.replace('-','to')))+'_'+_slug()+'.csv',")

PAIRS = [(A_DECL, N_DECL), (A_LINK, N_LINK), (A_ITEM, N_ITEM), (A_CL, N_CL), (A_SPW, N_SPW),
         (A_LR, N_LR), (A_IR, N_IR), (A_KR, N_KR), (A_XR, N_XR),
         (A_DC1, N_DC1), (A_DC2, N_DC2), (A_LNK1, N_LNK1), (A_LNK2, N_LNK2),
         (A_EPI, N_EPI), (A_CNT, N_CNT), (A_CAP, N_CAP),
         (A_DL1, N_DL1), (A_DL2, N_DL2), (A_DL3, N_DL3), (A_DL4, N_DL4)]

NEW_MARKS = ('const SL=yi*12+mv-1', 'SS.lm[i]', 'SS.km[i]', 'SS.tm[i]', 'const MK=mv?', 'const EPP=mv?',
             r"csvDownload('hrmp_search_teams_activity_vs_checklist_'+(one?", "withheld \\u00b7 '+GN")
OLD_MARKS = ('the month cannot narrow this table', 'District x year cells in scope',
             'not narrowed by the period picked', 'whole-window or district x year',
             r"csvDownload('hrmp_search_teams_activity_vs_checklist_'+STA.win",
             r"   {k:'d', l:'District-years',")


def scan(tag, frag):
    """Read the new JS line by line and in pairs, for the two ways a raw-string line list lies.

    A JS single-quoted string cannot cross a line, so a fragment written one Python string per JS
    line can only be broken by a quote that was mistranscribed. Three shapes, none of which a
    bracket-balance check on a partial fragment can see (the closers of these blocks live outside
    the fragment on purpose), and all of which a per-line quote count catches:
      - an odd number of single quotes on one line: a closing quote went missing;
      - a line ending with a quote followed by a line opening one: the sentence was split in two and
        the first half silently dropped, which is what happened to the draft of the count line;
      - a line ending in `+` followed by a line starting with `+`: the reader gets `a + + 'b'` and
        renders NaN instead of text.
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


def edits(reverse):
    seq = list(PAIRS)
    return [(b, a) for a, b in reversed(seq)] if reverse else seq


def apply(v, seq):
    for old, new in seq:
        v.require(v.count(old) == 1,
                  'anchor occurs %d times (want 1): %r' % (v.count(old), old[:90]))
        v.text = v.text.replace(old, new, 1)


def check(v, applied):
    # the two mark lists mean opposite things in the two directions: applying puts the new marks in
    # and pushes every year-only claim out; reversing has to bring each of those claims back.
    if applied:
        for p in NEW_MARKS:
            v.require(v.count(p) >= 1, 'the applied build lost %r (%d)' % (p, v.count(p)))
        for p in OLD_MARKS:
            v.require(v.count(p) == 0, 'the year-only claim survived: %r' % p)
        # a month book the renderer cannot read is worse than no month book at all
        v.require(all(v.count('"%s"' % k) == 1 for k in ('alM', 'itM', 'lnkM', 'triM')),
                  'the embedded const STA carries no month arrays - run '
                  'python _refresh/refresh.py run --only sta first')
        v.require(v.count('function staTab(){') == 1 and v.count("drawTable('tSTl'") == 1
                  and v.count("drawTable('tSTe'") == 1, 'the search-team block came apart')
        for idm in ('cntSTl', 'cntSTi', 'cntSTk', 'cntSTe', 'capSTa'):
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
    if applied:
        for i, (_, new) in enumerate(seq, 1):
            scan('STA-MONTH edit %d' % i, new)
    for v in vs:
        if 'function staTab(){' not in v.text:
            raise SystemExit('%s: no search-team block - patch_sta_ui.py has to be applied first'
                             % v.rel)
        had = v.count(NEW_MARKS[0])
        if applied and had:
            raise SystemExit('%s: the month grain is already applied' % v.rel)
        if a.unpatch and not had:
            raise SystemExit('%s: the month grain is not applied, nothing to reverse' % v.rel)
        apply(v, seq)
        check(v, applied)
        v.changes.append('STA month grain %s (%+d chars)'
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
    print('OK sta-month - %s' % ('the search-team grids follow the period pick in all four variants'
                                 if applied else
                                 'the search-team grids read district x year again, as before'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
