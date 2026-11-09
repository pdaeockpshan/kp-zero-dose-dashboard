# -*- coding: utf-8 -*-
"""Add SNID Nov 2026 to the PEI SYNERGY zero-dose register without inventing a covered figure.

The round is recorded-only: the advance-report route supplies 42,653 zero-dose children
reported per UC, and that same export's "covered by next round" column is 0 because no round
has followed. So every coverage percentage in the register has to divide by the recorded
children of the rounds that actually report covered - otherwise each Nov child would silently
count as not covered and the province share would drop for no reason.

`crp()` carries that denominator through every aggregate: agg -> shownRows/distRows/dRows ->
totals/dYears/campTotals/campDivRows. Rounds that report covered everywhere keep covRep == rep,
so their published percentages do not move.

Prose is rewritten where it named the last round or a fixed round count.

Run after the ADV payload is rebuilt:  python _refresh/patch_adv_nov26.py [--dry-run]
"""
import re
import sys

import dashpatch
import srcutil


def edits():
    E = []

    def add(old, new, n=1, why=''):
        E.append((old, new, n, why))

    # ---- 1. null-safe pct + the covered-round denominator helper -------------------
    add("function pct(a,b){return b?a/b*100:null;}",
        "function pct(a,b){return (a==null||isNaN(a)||!b)?null:a/b*100;} "
        "function crp(o){return o&&o.covRep!=null?o.covRep:o.rep;}",
        1, 'pct/crp')

    # ---- 2. the validation register's Nov round is the advance-report round ---------
    add("var VALMAP={'NIDAPR2026':'NID Apr 26','NIDFEB2026':'NID Feb 26',"
        "'SNIDMAY2026':'SNID May 2026','SNIDSEP2026':'SNID Sept 2026'};",
        "var VALMAP={'NIDAPR2026':'NID Apr 26','NIDFEB2026':'NID Feb 26',"
        "'SNIDMAY2026':'SNID May 2026','SNIDSEP2026':'SNID Sept 2026','SNIDNOVEMBER2026':'SNID Nov 2026'};",
        1, 'VALMAP alias')

    # ---- 3. agg(): recorded children of the UC rows that reported covered -----------
    add(" var o={rep:0,cov:0,covUc:0,repUc:0,dig:null,digRep:null,dUc:0,val:null,conf:null,vUc:0};",
        " var o={rep:0,cov:0,covUc:0,covRep:0,repUc:0,dig:null,digRep:null,dUc:0,val:null,conf:null,vUc:0};",
        1, 'agg init')
    add("if(r.uc)r.uc.forEach(function(x){if(!K.has(x.k))return;o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;}});",
        "if(r.uc)r.uc.forEach(function(x){if(!K.has(x.k))return;o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;o.covRep+=x.rep;}});",
        1, 'agg coveredRep')

    # ---- 4. row plumbing -----------------------------------------------------------
    add("adv:r.adv,ord:r.ord,rep:a.rep,cov:a.cov,covUc:a.covUc,repUc:a.repUc,",
        "adv:r.adv,ord:r.ord,rep:a.rep,cov:a.cov,covUc:a.covUc,covRep:a.covRep,repUc:a.repUc,",
        1, 'shownRows')
    add("return{n:r.n,y:r.y,adv:r.adv,rep:a.rep,cov:a.cov,covUc:a.covUc,repUc:a.repUc,",
        "return{n:r.n,y:r.y,adv:r.adv,rep:a.rep,cov:a.cov,covUc:a.covUc,covRep:a.covRep,repUc:a.repUc,",
        1, 'dRows')

    # ---- 5. KPI row ---------------------------------------------------------------
    add(" var rep=0,cov=0,covUc=0,dig=0,digRep=0,val=0,conf=0;",
        " var rep=0,cov=0,covUc=0,covRep=0,dig=0,digRep=0,val=0,conf=0;",
        1, 'draw accum')
    add("rows.forEach(function(r){rep+=r.rep;cov+=r.cov;covUc+=r.covUc;",
        "rows.forEach(function(r){rep+=r.rep;cov+=r.cov;covUc+=r.covUc;covRep+=r.covRep||0;",
        1, 'draw coveredRep')
    add("\r\n".join([
        " $('zrK2').textContent=fN(cov);",
        " $('zrK2s').textContent=covUc?'covered in the same round':'covered-in-round not reported';",
        " $('zrK3').textContent=fP(pct(cov,rep));",
        " $('zrK3s').textContent='covered \\u00f7 recorded';"]),
        "\r\n".join([
        " $('zrK2').textContent=covUc?fN(cov):'\\u2013';",
        " $('zrK2s').textContent=covUc?(covRep<rep?'covered in the same round, over the rounds that report it':'covered in the same round'):'covered-in-round not reported';",
        " $('zrK3').textContent=covUc?fP(pct(cov,covRep)):'\\u2013';",
        " $('zrK3s').textContent=covUc?'covered \\u00f7 recorded, rounds with a covered figure':'covered \\u00f7 recorded';"]),
        1, 'KPI 2-3')

    # ---- 6. covered % columns (register + district table) ---------------------------
    add("sv:function(r){return r.rep?r.cov/r.rep:null;},f:function(r){return r.covUc&&r.rep?rgN(r.cov/r.rep*100,90,80)+'%':",
        "sv:function(r){return r.covRep?r.cov/r.covRep:null;},f:function(r){return r.covUc&&r.covRep?rgN(r.cov/r.covRep*100,90,80)+'%':",
        2, 'covered % columns')

    # ---- 7. caption ----------------------------------------------------------------
    add(" $('zrCap').textContent='Recorded and covered come from the IDIMS advance reports "
        "(2022 to SNID Sept 2026), covered meaning vaccinated during that same round. "
        "Digitized is the Sept-26 linelist-vs-IDIMS exercise and exists only for the nine districts "
        "it covered, so every other round shows a dash. Validated is the zero-dose validation register, "
        "which carries four of the advance-report rounds plus four special activities that have no advance "
        "report. The four columns have different denominators; a dash means the source does not cover the "
        "round, not a zero.';",
        " $('zrCap').textContent='Recorded comes from the IDIMS advance reports (2022 to SNID Sept 2026) "
        "plus, for SNID Nov 2026, that round\\u2019s own UC-wise summary coverage export of 06-Nov-2026 \\u2014 "
        "42,653 children reported. Covered means vaccinated during that same round; it is a dash for SNID "
        "Nov 2026 because the export\\u2019s covered column is the next-round figure and no round has followed, "
        "and the covered share is taken over the rounds that do report covered, so a round still awaiting it "
        "never enters the denominator as uncovered. Digitized is the Sept-26 linelist-vs-IDIMS exercise and "
        "exists only for the nine districts it covered, so every other round shows a dash. Validated is the "
        "zero-dose validation register, which carries four of the advance-report rounds plus four special "
        "activities that have no advance report. The four columns have different denominators; a dash means "
        "the source does not cover the round, not a zero.';",
        1, 'zrCap')

    # ---- 8. map colouring ----------------------------------------------------------
    add("if(!o||!o.rep||!o.covUc)return {f:'#cbd5e1',c:'#475569',p:null};",
        "if(!o||!o.covRep||!o.covUc)return {f:'#cbd5e1',c:'#475569',p:null};",
        1, 'covBin guard')
    add(" var p=o.cov/o.rep*100;", " var p=o.cov/o.covRep*100;", 1, 'covBin share')

    # ---- 9. district rows + year/total aggregates ----------------------------------
    add("o={d:d,dv:DIST[d],rep:0,cov:0,covUc:0,repUc:0,",
        "o={d:d,dv:DIST[d],rep:0,cov:0,covUc:0,covRep:0,repUc:0,",
        1, 'distRows init')
    add("   o.rep+=a.rep;o.cov+=a.cov;o.covUc+=a.covUc;o.repUc+=a.repUc;",
        "   o.rep+=a.rep;o.cov+=a.cov;o.covUc+=a.covUc;o.covRep+=a.covRep;o.repUc+=a.repUc;",
        1, 'distRows accum')
    add("{y:r.y,n:0,rep:0,cov:0,covUc:0,dig:0,digRep:0,dUc:0,val:0,conf:0,vUc:0}",
        "{y:r.y,n:0,rep:0,cov:0,covUc:0,covRep:0,dig:0,digRep:0,dUc:0,val:0,conf:0,vUc:0}",
        1, 'dYears init')
    add("if(r.adv>=0){g.n++;g.rep+=r.rep;g.cov+=r.cov;g.covUc+=r.covUc;}",
        "if(r.adv>=0){g.n++;g.rep+=r.rep;g.cov+=r.cov;g.covUc+=r.covUc;g.covRep+=r.covRep;}",
        1, 'dYears accum')
    add(" var t={rep:0,cov:0,covUc:0,repUc:0,dig:0,digRep:0,dUc:0,val:0,conf:0,vUc:0,n:0};",
        " var t={rep:0,cov:0,covUc:0,covRep:0,repUc:0,dig:0,digRep:0,dUc:0,val:0,conf:0,vUc:0,n:0};",
        1, 'totals init')
    add("rows.forEach(function(r){t.n++;t.rep+=r.rep;t.cov+=r.cov;t.covUc+=r.covUc;t.repUc+=r.repUc||0;",
        "rows.forEach(function(r){t.n++;t.rep+=r.rep;t.cov+=r.cov;t.covUc+=r.covUc;t.covRep+=r.covRep||0;t.repUc+=r.repUc||0;",
        1, 'totals accum')

    # ---- 10. downloads / read me ---------------------------------------------------
    add("r.covUc?r.cov:'',r.covUc&&r.rep?Math.round(r.cov/r.rep*1000)/10:'',",
        "r.covUc?r.cov:'',r.covUc&&r.covRep?Math.round(r.cov/r.covRep*1000)/10:'',",
        1, 'xlsx covered %')
    add("r.adv<0?'Validation register only (no advance report)':(r.dig?'Advance report + Sept-26 digitization':'IDIMS advance report')];",
        "r.adv<0?'Validation register only (no advance report)':"
        "((ADV.sm&&ADV.sm[r.n])?'UC-wise summary coverage export':"
        "(r.dig?'Advance report + Sept-26 digitization':'IDIMS advance report'))];",
        1, 'xlsx source')
    add(" ['Recorded / covered','IDIMS advance reports 2022 to SNID Sept 2026 (export '+ADV.asof+'). Covered means vaccinated during the same round.'],",
        " ['Recorded / covered','IDIMS advance reports 2022 to SNID Sept 2026 (export '+ADV.asof+'), plus SNID Nov 2026 from its own UC-wise summary coverage export of 06-Nov-2026. Covered means vaccinated during the same round; it is a dash for SNID Nov 2026 until a round follows, and the covered share uses only the rounds that report covered.'],",
        1, 'readme')

    # ---- 11. all-rounds deck prose -------------------------------------------------
    add("and validated as vaccinated \\u2014 2022 to SNID Sept 2026. Scope: ",
        "and validated as vaccinated \\u2014 2022 to '+ROWS[ROWS.length-1].n+'. Scope: ",
        1, 'cover slide range')
    add(" ['Recorded','Zero-dose children reported per UC in the IDIMS advance report for that round. All 42 rounds from SNID Jan-22 to SNID Sept-26 carry it.'],",
        " ['Recorded','Zero-dose children reported per UC in the IDIMS advance report for that round, except SNID Nov 2026, whose count comes from that round\\u2019s own UC-wise summary coverage export. All '+ROWS.filter(function(r){return r.adv>=0;}).length+' rounds from SNID Jan-22 to SNID Nov 2026 carry a recorded figure, and SNID Nov 2026 does not yet carry a covered one.'],",
        1, 'how to read recorded')
    add(" ['Recorded and covered','IDIMS advance reports. The 2026 rounds take their covered figures from the dashboard\\u2019s own zero-dose dataset because the advance exports leave those columns blank; SNID Sept-26 covered is that round\\u2019s own UC-wise export (39,176 of 62,128, self-reported, not reconciled by a later round).'],",
        " ['Recorded and covered','IDIMS advance reports. The 2026 rounds take their covered figures from the dashboard\\u2019s own zero-dose dataset because the advance exports leave those columns blank; SNID Sept-26 covered is that round\\u2019s own UC-wise export (39,176 of 62,128, self-reported, not reconciled by a later round). SNID Nov 2026 has no advance report yet: its recorded count is that round\\u2019s own UC-wise summary coverage export of 06-Nov-2026, and covered stays a dash until a round follows, so its children are not counted as uncovered in any share.'],",
        1, 'deck notes')

    # ---- 12. scope-slide sentences -------------------------------------------------
    add("if(t.rep)lines.push(fN(t.rep)+' zero-dose children recorded across '+nAdv+' advance-report rounds, '+pcol(pct(t.cov,t.rep))+' covered in the same round.');",
        "if(t.rep)lines.push(fN(t.rep)+' zero-dose children recorded across '+nAdv+' advance-report rounds, '"
        "+(t.covUc?pcol(pct(t.cov,crp(t)))+' covered in the same round, over the rounds that report covered.':"
        "'but no covered figure yet for the newest round in this total.'));",
        1, 'scope line')
    add("if(y26&&y26.rep)lines.push('2026 so far: '+fN(y26.rep)+' recorded, '+pcol(pct(y26.cov,y26.rep))+' covered.');",
        "if(y26&&y26.rep)lines.push('2026 so far: '+fN(y26.rep)+' recorded, '"
        "+(y26.covUc?pcol(pct(y26.cov,crp(y26)))+' covered.':'covered not yet reported for SNID Nov 2026.'));",
        1, '2026 line')

    # ---- 13. per-campaign deck -----------------------------------------------------
    add("function row(d){return m[d]||(m[d]={d:d,dv:DIST[d],rep:0,cov:0,covUc:0,repUc:0,ll:0,llRep:0,dUc:0,val:0,conf:0,vUc:0});}",
        "function row(d){return m[d]||(m[d]={d:d,dv:DIST[d],rep:0,cov:0,covUc:0,covRep:0,repUc:0,ll:0,llRep:0,dUc:0,val:0,conf:0,vUc:0});}",
        1, 'campDistricts init')
    add("var o=row(UC[x.k].d);o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;}});",
        "var o=row(UC[x.k].d);o.rep+=x.rep;o.repUc++;if(x.cov!=null){o.cov+=x.cov;o.covUc++;o.covRep+=x.rep;}});",
        1, 'campDistricts coveredRep')
    add(" var t={nd:0,uc:0,rep:0,cov:0,covUc:0,ll:0,llRep:0,dUc:0,val:0,conf:0,vUc:0};",
        " var t={nd:0,uc:0,rep:0,cov:0,covUc:0,covRep:0,ll:0,llRep:0,dUc:0,val:0,conf:0,vUc:0};",
        1, 'campTotals init')
    add("  t.nd++;t.uc+=o.repUc||0;t.rep+=o.rep||0;t.cov+=o.cov||0;t.covUc+=o.covUc||0;",
        "  t.nd++;t.uc+=o.repUc||0;t.rep+=o.rep||0;t.cov+=o.cov||0;t.covUc+=o.covUc||0;t.covRep+=o.covRep||0;",
        1, 'campTotals accum')
    add("(m[o.dv]={dv:o.dv,nd:0,uc:0,rep:0,cov:0,covUc:0,ll:0,",
        "(m[o.dv]={dv:o.dv,nd:0,uc:0,rep:0,cov:0,covUc:0,covRep:0,ll:0,",
        1, 'campDivRows init')
    add("  g.nd++;g.uc+=o.repUc||0;g.rep+=o.rep||0;g.cov+=o.cov||0;g.covUc+=o.covUc||0;",
        "  g.nd++;g.uc+=o.repUc||0;g.rep+=o.rep||0;g.cov+=o.cov||0;g.covUc+=o.covUc||0;g.covRep+=o.covRep||0;",
        1, 'campDivRows accum')
    add("covRows[r.n]||(covRows[r.n]={n:r.n,y:r.y,adv:r.adv,rep:0,cov:0,covUc:0,repUc:0,",
        "covRows[r.n]||(covRows[r.n]={n:r.n,y:r.y,adv:r.adv,rep:0,cov:0,covUc:0,covRep:0,repUc:0,",
        1, 'covRows init')
    add("  o.rep+=r.rep;o.cov+=r.cov;o.covUc+=r.covUc;o.repUc+=r.repUc;",
        "  o.rep+=r.rep;o.cov+=r.cov;o.covUc+=r.covUc;o.covRep+=r.covRep;o.repUc+=r.repUc;",
        1, 'covRows accum')

    add("  [rr.adv>=0&&pt.rep?pcol(pct(pt.cov,pt.rep)):'\\u2013','covered in the same round'],",
        "  [rr.adv>=0&&pt.covUc?pcol(pct(pt.cov,pt.covRep)):'\\u2013',"
        "rr.adv>=0?(pt.covUc?'covered in the same round':'covered not yet reported'):'covered in the same round'],",
        1, 'camp cover kpi')
    add(" var scopeLine=rr.adv>=0?('Scope '+scopeTxt+'  \\u00b7  '+fN(ucRep)+' UCs reported this round  \\u00b7  '+fN(pt.cov)+' covered  \\u00b7  '+fN(pt.conf)+' confirmed vaccinated')",
        " var scopeLine=rr.adv>=0?('Scope '+scopeTxt+'  \\u00b7  '+fN(ucRep)+' UCs reported this round  \\u00b7  '"
        "+(pt.covUc?fN(pt.cov)+' covered  \\u00b7  ':(ADV.sm&&ADV.sm[camp]?'covered not yet reported  \\u00b7  ':fN(pt.cov)+' covered  \\u00b7  '))"
        "+fN(pt.conf)+' confirmed vaccinated')",
        1, 'camp scope line')
    add("  ['Covered',rr.adv>=0?'Children vaccinated during the same round in the same report. Covered % is covered \\u00f7 recorded on the '+ucN(bothU)+' in scope that reported both.':'No same-round coverage figure exists for this activity, so the covered column is a dash.'],",
        "  ['Covered',rr.adv>=0?(bothU?'Children vaccinated during the same round in the same report. Covered % is covered \\u00f7 recorded on the '+ucN(bothU)+' in scope that reported both.':'This round\\u2019s export carries recorded children but no covered figure yet, so the covered column is a dash and those children are not counted as uncovered in any share.'):'No same-round coverage figure exists for this activity, so the covered column is a dash.'],",
        1, 'camp how-to-read covered')
    add("  var line=valOnly?('Total: '+fN(pt.val)+' register entries \\u00b7 '+fN(pt.conf)+' confirmed vaccinated'):('Total: '+fN(pt.rep)+' recorded \\u00b7 '+fN(pt.cov)+' covered ('+pcol(pct(pt.cov,pt.rep))+')');",
        "  var line=valOnly?('Total: '+fN(pt.val)+' register entries \\u00b7 '+fN(pt.conf)+' confirmed vaccinated')"
        ":('Total: '+fN(pt.rep)+' recorded \\u00b7 '+(pt.covUc?fN(pt.cov)+' covered ('+pcol(pct(pt.cov,pt.covRep))+')':'covered not yet reported'));",
        1, 'camp division total')
    add("   us.forEach(function(x){var k=x.t||'\\u2014',g=tm[k]||(tm[k]={t:k,n:0,rep:0,cov:0,ll:0,dUc:0,val:0,conf:0});",
        "   us.forEach(function(x){var k=x.t||'\\u2014',g=tm[k]||(tm[k]={t:k,n:0,rep:0,cov:0,covRep:0,ll:0,dUc:0,val:0,conf:0});",
        1, 'tehsil init')
    add("    g.n++;g.rep+=x.rep||0;g.cov+=x.cov||0;if(x.ll!=null){g.ll+=x.ll;g.dUc++;}g.val+=x.val||0;g.conf+=x.conf||0;});",
        "    g.n++;g.rep+=x.rep||0;g.cov+=x.cov||0;if(x.cov!=null)g.covRep+=x.rep||0;if(x.ll!=null){g.ll+=x.ll;g.dUc++;}g.val+=x.val||0;g.conf+=x.conf||0;});",
        1, 'tehsil accum')
    add("if(t.rep)lines.push(fN(t.rep)+' zero-dose children recorded and '+fN(t.cov)+' covered ('+pcol(pct(t.cov,t.rep))+') in '+camp+'.');",
        "if(t.rep)lines.push(fN(t.rep)+' zero-dose children recorded and '"
        "+(t.covUc?fN(t.cov)+' covered ('+pcol(pct(t.cov,crp(t)))+')':'no covered figure yet')+' in '+camp+'.');",
        1, 'camp scope-slide line')
    add("  ['Recorded and covered',rr.adv>=0?'IDIMS advance report for this round.'+(rr.y>=2026?' The 2026 covered figures come from the dashboard\\u2019s own zero-dose dataset because those advance exports leave the covered columns blank.':'')",
        "  ['Recorded and covered',rr.adv>=0?((ADV.sm&&ADV.sm[camp])?'UC-wise summary coverage export for this round ('+ADV.sm[camp].d+'): the recorded count only, because that export\\u2019s covered column is the next-round figure and no round has followed.':'IDIMS advance report for this round.'+(rr.y>=2026?' The 2026 covered figures come from the dashboard\\u2019s own zero-dose dataset because those advance exports leave the covered columns blank.':''))",
        1, 'camp notes')
    add(" if(rr.adv>=0)src.push('Recorded and covered: IDIMS advance report for '+camp+(ADV.asof?' (export '+ADV.asof+')':'')+'.');",
        " if(rr.adv>=0&&ADV.sm&&ADV.sm[camp])src.push('Recorded only: the UC-wise summary coverage export for '+camp+' of '+ADV.sm[camp].d+'; its covered column is a dash until a round follows.');\r\n"
        " else if(rr.adv>=0)src.push('Recorded and covered: IDIMS advance report for '+camp+(ADV.asof?' (export '+ADV.asof+')':'')+'.');",
        1, 'camp source')

    # ---- 14. map/bars deck ---------------------------------------------------------
    add(" kpi(s,6.80,1.72,2.90,t.rep?pcol(pct(t.cov,t.rep)):'\\u2013','covered \\u00f7 recorded',C.pri);",
        " kpi(s,6.80,1.72,2.90,t.covUc?pcol(pct(t.cov,t.covRep)):'\\u2013','covered \\u00f7 recorded, rounds that report covered',C.pri);",
        1, 'map deck kpi')
    add("  var r={repUc:0,rep:0,cov:0,covUc:0};REST.forEach(function(o){r.repUc+=o.repUc;r.rep+=o.rep;r.cov+=o.cov;r.covUc+=o.covUc;});",
        "  var r={repUc:0,rep:0,cov:0,covUc:0,covRep:0};REST.forEach(function(o){r.repUc+=o.repUc;r.rep+=o.rep;r.cov+=o.cov;r.covUc+=o.covUc;r.covRep+=o.covRep;});",
        1, 'map deck rest')
    add("o.covUc&&o.rep?pcol(pct(o.cov,o.rep)):'\\u2013'",
        "o.covUc&&o.covRep?pcol(pct(o.cov,o.covRep)):'\\u2013'",
        1, 'map deck top rows')
    add("r.covUc&&r.rep?pcol(pct(r.cov,r.rep)):'\\u2013'",
        "r.covUc&&r.covRep?pcol(pct(r.cov,r.covRep)):'\\u2013'",
        1, 'map deck rest row')
    add("t.covUc&&t.rep?pcol(pct(t.cov,t.rep)):'\\u2013'",
        "t.covUc&&t.covRep?pcol(pct(t.cov,t.covRep)):'\\u2013'",
        1, 'map deck total row')

    # ---- 15. ADV page prose --------------------------------------------------------
    add("Every campaign from 2022 to SNID Sept 2026:",
        "Every campaign from 2022 to SNID Nov 2026:",
        1, 'adHint range')
    add("self-reported for the round, not yet reconciled.</div>",
        "self-reported for the round, not yet reconciled. SNID Nov 2026 has no advance report yet: "
        "its recorded figure comes from that round\\u2019s own UC-wise summary coverage export of 06-Nov-2026, "
        "and its covered column stays a dash until a round follows.</div>",
        1, 'adHint nov')
    add("(39,176 covered against 62,128 recorded). '+(multi?",
        "(39,176 covered against 62,128 recorded). SNID Nov 2026 is recorded-only: its count comes from "
        "that round\\u2019s own UC-wise summary coverage export of 06-Nov-2026 and it carries no covered figure yet. '+(multi?",
        1, 'capad3 nov')

    return E


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    E = edits()
    report = []
    for v in vs:
        s = v.text
        for old, new, n, why in E:
            got = s.count(old)
            v.require(got == n, '%s: expected %d hit(s) of %r, found %d' % (why, n, old[:70], got))
            s = s.replace(old, new)
        # every remaining X.cov ÷ X.rep is an aggregate: divide by the covered-round denominator
        s, k = re.subn(r'pct\(([A-Za-z0-9_$.]+)\.cov,\s*\1\.rep\)', r'pct(\1.cov,crp(\1))', s)
        v.require(k >= 10, 'coverage-denominator rewrite only hit %d sites' % k)
        v.require('crp(' in s and s.count('covRep') >= 55, 'covRep plumbing missing (count %d)' % s.count('covRep'))
        v.text = s
        v.changes.append('%d prose/plumbing edits, %d denominator rewrites' % (len(E), k))
        report.append('%s: %+d chars' % (v.rel, v.delta()))
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    print('\n'.join(report))
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    print('PATCHED %d variants' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
