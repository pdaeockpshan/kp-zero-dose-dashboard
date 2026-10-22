"""Task117: publish the fresh EPI-MIS year-to-date coverage and the district dropout report
into the four local dashboard variants.

  python _refresh/patch_epi_ytd.py --dry-run
  python _refresh/patch_epi_ytd.py

This writes only the working copy - it never commits, pushes or deploys.

Reads the JSON produced by extract_epi_ytd.py / extract_epi_drop.py, replaces const EPI,
adds const EPIYTD (dated year-to-date metadata) and const EPIDROP (the published district
dropout rates), and rewrites the labels that borrowed the monthly archive window
(EMETA.per = Jan 2024 - Sep 2026) as if it were the year-to-date period.

EPIM/EMETA are deliberately untouched: a year-to-date file says nothing about individual
months, so the month-by-month archive stays as it was harvested.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HERE = srcutil.HERE
OUT_EPI = os.path.join(HERE, 'out', 'epi_ytd.json')
OUT_META = os.path.join(HERE, 'out', 'epi_ytd.meta.json')
OUT_DROP = os.path.join(HERE, 'out', 'epi_drop.json')


def crlf(*lines):
    return '\r\n'.join(lines)


# ---------------------------------------------------------------- text edits
def edits():
    """(name, old, new) - each old must occur exactly once per variant."""
    E = []

    # 1. source hint on the antigen coverage page
    E.append(('hint',
      '<div class="hint">Data: <b>KP EPI-MIS</b> · Vaccination Coverage report · <b>Jan 2026 – Sep 2026</b> (year to date) · 1,459 UCs in 37 districts. Coverage % = doses given ÷ target for the period (newborns for BCG and OPV-0, surviving infants for the rest). <b>Sep 2026 is still being reported</b> (about 65% of a normal month so far), so the year-to-date figures will rise a little as September completes. <span id="eNote"></span></div>',
      '<div class="hint">Data: <b>KP EPI-MIS</b> · UC-wise Vaccination Coverage report · <b>Jan 2026 – Sep 2026</b> (year to date, export saved <span id="eSrc"></span>) · 1,459 UCs in 37 districts, <b>1,167 matched to the polio UC list</b>. Coverage % = doses given ÷ target for the period (newborns for BCG and OPV-0, surviving infants for the rest). The month-by-month charts use the separate single-month archive, where the <b>Sep 2026 bar is an older part-report</b> — the year-to-date file above already carries a full month for September. <span id="eNote"></span></div>'))

    # 2. dropout report card, after the district coverage table
    capEG = '<div class="cap">Coverage % = doses given ÷ target for Jan 2026 – Sep 2026 (newborns for BCG and OPV-0, surviving infants for the rest). Over 100% usually means the target is set too low or children from other areas were vaccinated here. Dropout = share of children who got the first dose but not the later one.</div>'
    E.append(('drop-card', crlf(capEG, '</div>'), crlf(capEG, '</div>',
      '<div class="card" style="margin-bottom:16px">',
      '<div class="tblhdr"><h3 style="margin:0">Dropout report by district (as published)</h3><div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntED"></span><button class="btn" id="btnEDCSV">Download (CSV)</button></div></div>',
      '<div class="scroll" style="max-height:460px"><table id="tED"></table></div>',
      '<div class="cap" id="capED"></div>',
      '</div>')))

    # 3. year-to-date period label, no longer borrowed from the monthly archive
    E += [
      ('lbl-summary', "<b>Routine EPI (${esc(EMETA.per||'')}):</b>", "<b>Routine EPI (${esc(EPER)}):</b>"),
      ('lbl-xz4', "el('xz4').textContent=ne.length?(fmt(ne.length)+' UCs · '+(EMETA.per||'')):'no EPI data';",
                  "el('xz4').textContent=ne.length?(fmt(ne.length)+' UCs · '+EPER):'no EPI data';"),
      ('lbl-ppt', "const eD={per:EMETA.per||'',s:e.s,n:e.n,", "const eD={per:EPER,s:e.s,n:e.n,"),
      ('lbl-brf', "e:{per:EMETA.per||'',s:e.s,u:e.u,", "e:{per:EPER,s:e.s,u:e.u,"),
      ('lbl-e1s', "${EM?esc(emLab(EM)):(EMETA.per||'')}", "${EM?esc(emLab(EM)):EPER}"),
      ('lbl-ce1', "${EM?emLab(EM):(EMETA.per||'')}", "${EM?emLab(EM):EPER}"),
      ('lbl-hmap', "${a.t==='n'?'newborns':'surviving infants'} · ${EMETA.per||''}`",
                   "${a.t==='n'?'newborns':'surviving infants'} · ${EPER}`"),
      ('lbl-hE0', "`KP EPI-MIS · ${EMETA.per||''} · ${fmt(EPI.length)} UCs`",
                   "`KP EPI-MIS · ${EPER} · ${fmt(EPI.length)} UCs`"),
      ('lbl-crcm', "infants on the EPI target without Penta-3 (${EMETA.per||'Jan–Sep'})",
                   "infants on the EPI target without Penta-3 (${EPER})"),
      ('lbl-work', "for 90% Penta-3 (${esc(EMETA.per||'Jan–Sep')})", "for 90% Penta-3 (${esc(EPER)})"),
      ('lbl-cx6', "To 90% Penta-3 and MR-2 · ${EMETA.per||'Jan–Sep'}", "To 90% Penta-3 and MR-2 · ${EPER}"),
      ('lbl-hhE', "'Penta-3 · '+esc(EMETA.per||'')", "'Penta-3 · '+esc(EPER)"),
      ('lbl-hepi', "esc(EMETA.per||'')+' · '+fmt(R.length)+' UCs'", "esc(EPER)+' · '+fmt(R.length)+' UCs'"),
    ]

    # 4. the month picker: the blank option really is the year-to-date UC file
    E.append(('emsel',
      crlf("function emSel(){document.querySelectorAll('.emsel').forEach(s=>{ if(!s.options.length){s.innerHTML='<option value=\"\">All months ('+esc(EMETA.per||'YTD')+')</option>'+(EMETA.months||[]).map(m=>'<option value=\"'+m.mo+'\">'+esc(m.l)+(m.pt?' · partial':'')+'</option>').join(''); s.onchange=()=>{EM=s.value;document.querySelectorAll('.emsel').forEach(x=>{x.value=EM;});render();};} s.value=EM;});"),
      crlf("function emSel(){document.querySelectorAll('.emsel').forEach(s=>{ if(!s.options.length){s.innerHTML='<option value=\"\">Year to date ('+esc(EPER)+')</option>'+(EMETA.months||[]).map(m=>'<option value=\"'+m.mo+'\">'+esc(m.l)+(m.pt?' · part-report':'')+'</option>').join(''); s.onchange=()=>{EM=s.value;document.querySelectorAll('.emsel').forEach(x=>{x.value=EM;});render();};} s.value=EM;});")))
    E.append(('emsel-uc',
      "if(EM){el('tEU').innerHTML='<tr><td class=\"empty\">UC-level detail is year-to-date — set <b>EPI month</b> to “All months” to view it.</td></tr>';el('cntEU').textContent='UC detail: set EPI month to All months';el('btnEUCSV').disabled=true;el('btnEUCSV').title='Set EPI month to All months to download UC-level data';}",
      "if(EM){el('tEU').innerHTML='<tr><td class=\"empty\">UC-level detail is year-to-date — set <b>EPI month</b> to “Year to date” to view it.</td></tr>';el('cntEU').textContent='UC detail: set EPI month to Year to date';el('btnEUCSV').disabled=true;el('btnEUCSV').title='Set EPI month to Year to date to download UC-level data';}"))

    # 5. monthly archive wording: September is complete in the year-to-date file now
    E += [
      ('ce3-sub', "it'+(EMETA.partial?` · ${EMETA.partial} partial`:'')",
                  "it'+(EMETA.partial?` · ${EMETA.partial} archived as a part-report`:'')"),
      ('cape3',
       "(EMETA.partial?`${EMETA.partial} is still being reported (about ${EMETA.partial_pct}% of a normal month so far), so its low figure is not a real drop.`:'')",
       "(EMETA.partial?`${EMETA.partial} in this archive is only a part-report (about ${EMETA.partial_pct}% of a normal month when the single-month exports were taken), so its low bar is not a real drop - the year-to-date figures above already include a full ${EMETA.partial}.`:'')"),
      ('cape8', "(EMETA.partial?' '+EMETA.partial+' is still partial.':'')",
                 "(EMETA.partial?' '+EMETA.partial+' is an archived part-report.':'')"),
    ]

    # 6. dropout KPI subtitles: dose difference, not a list of named children
    E += [
      ('e2s', "o.p1?`${fmt(Math.max(o.p1-o.p3,0))} children got Penta-1 but not Penta-3`:''",
              "o.p1?`${fmt(Math.max(o.p1-o.p3,0))} Penta-1 doses with no Penta-3 recorded`:''"),
      ('e3s', "o.mr1?`${fmt(Math.max(o.mr1-o.mr2,0))} children got MR-1 but not MR-2`:''",
              "o.mr1?`${fmt(Math.max(o.mr1-o.mr2,0))} MR-1 doses with no MR-2 recorded`:''"),
    ]

    # 7. three questions: the routine snapshot keeps its date, loses the stale caveat
    E += [
      ('gp-period', "const GP_EPI_PERIOD='Jan–Sep 2026 YTD; September partial';",
                    "const GP_EPI_PERIOD=EPER+' YTD';"),
      ('gp-cap', "EPI-MIS (${GP_EPI_PERIOD}; UCs matched to polio UC codes)",
                 "EPI-MIS ${esc(EPIYTD.got||'')}; UCs matched to polio UC codes"),
    ]

    # 8. render the dropout table with the coverage page
    E.append(('renderED-call', crlf('function renderEOv(){', ' emSel();'),
              crlf('function renderEOv(){', ' emSel();', ' renderED();')))
    js = crlf(
      "// ---------- EPI-MIS dropout report (district level, published as reported) ----------",
      "const EDSPL={p1m1:['Male','Female'],p1p3:['Male','Female'],mr12:['Male','Female'],tt12:['Pregnant women','CBA teams'],ipv:['Male','Female']};",
      "const edOK=r=>(!fDiv.value||r.dv===fDiv.value)&&((r.ds||[]).some(d=>dOK(d)));",
      "const edRows=()=>(EPIDROP.rows||[]).filter(edOK);",
      "const edCov=()=>Object.fromEntries(groupE(EPI,'ed').map(x=>[x.k,x]));",
      "const edN=v=>v==null||isNaN(v)?'–':rgNL(v,5,10,0)+'%';",
      "function renderED(){",
      " el('eSrc').textContent=EPIYTD.got||'';",
      " const G=EPIDROP.g||[], rows=edRows(), cov=edCov();",
      " el('cntED').textContent=`${fmt(rows.length)} districts`;",
      " drawTable('tED',[{k:'ed',l:'District (EPI-MIS)',sv:r=>r.ed.toLowerCase(),f:r=>`<b>${esc(r.ed)}</b>`},{k:'dv',l:'Division'},",
      "  ...G.map(([k,l])=>({k,l,n:1,sv:r=>r[k][2],f:r=>`<span title=\"${esc(l)} · ${EDSPL[k][0]} ${r[k][0]}%, ${EDSPL[k][1]} ${r[k][1]}% (as reported)\">${edN(r[k][2])}</span>`})),",
      "  {k:'cd13',l:'Penta-1→Penta-3 from UC doses',n:1,sv:r=>{const c=(cov[r.ed]||{}).d13;return c==null?999:c;},f:r=>{const c=(cov[r.ed]||{}).d13;return c==null?'–':rgNL(c,5,10)+'%';}}],rows,'ed',1);",
      " const kp=EPIDROP.kp||{}, ce=aggE(EPI);",
      " el('capED').innerHTML=`${esc(EPIDROP.m.per||'')} · published KP total: `+G.map(([k,l])=>`${esc(l)} <b>${kp[k]!=null?kp[k][2]+'%':'–'}</b>`).join(' · ')+'. `+",
      "  `These are the programme's own district rates from the EPI-MIS dropout report (saved ${esc(EPIDROP.m.got||'')}) and they are not the same arithmetic as the rest of this page: they are calculated on sex-split dose cohorts and carry no denominators, so they cannot be re-added for a division - for all KP use the published total above. The last column is this dashboard's own Penta-1→Penta-3 dropout from the UC-level doses (${esc(EPER)}), which follows the filters and reads <b>${pc(ce.d13)}</b> for the current selection. A negative rate is real: more later doses than first doses, usually catch-up of older children. TT-1→TT-2 is maternal and does not affect the zero-dose work.`;",
      "}",
      "const EDH=()=>['District (EPI-MIS)','EPI-MIS district code','Division',...EPIDROP.g.flatMap(([k,l])=>[l+' '+EDSPL[k][0]+' %',l+' '+EDSPL[k][1]+' %',l+' total %']),'Penta-1→Penta-3 from UC doses %'];",
      "const edRow=r=>{const c=edCov()[r.ed]||{};return [r.ed,r.code,r.dv,...EPIDROP.g.flatMap(([k])=>r[k]),c.d13==null?'':c.d13.toFixed(1)];};",
      "el('btnEDCSV').onclick=()=>csvDownload('EPI_Dropout_Report_by_District_'+_slug()+'.csv',EDH(),edRows().map(edRow));",
      "")
    E.append(('renderED-js', "const EUH=()=>[", js + "const EUH=()=>["))
    return E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    rows_js = srcutil.read_text(OUT_EPI).strip()
    meta = json.loads(srcutil.read_text(OUT_META).strip())
    drop = json.loads(srcutil.read_text(OUT_DROP).strip())
    rows = json.loads(rows_js)
    meta_js, drop_js = srcutil.dumps(meta), srcutil.dumps(drop)
    E = edits()

    cfg, vs = dashpatch.load_variants()
    for v in vs:
        v.require('const EPIYTD' not in v.text and 'const EPIDROP' not in v.text,
                  'EPIYTD/EPIDROP already present - this patch is one-shot')
        for name, old, new in E:
            n = v.count(old)
            v.require(n == 1, 'anchor "%s" found %d times (expected 1)' % (name, n))
        for name, old, new in E:
            v.text = v.text.replace(old, new)
        i = v.text.index('const EMETA ')
        j = v.text.index(';\r\n', i) + 1
        v.text = (v.text[:j] + '\r\nconst EPIYTD = ' + meta_js + ';\r\nconst EPIDROP = ' + drop_js +
                  ";\r\nconst EPER=(EPIYTD.per||EMETA.per||'').replace(' - ',' – ');" + v.text[j:])
        v.changes.append('EPIYTD/EPIDROP/EPER added')
        dashpatch.swap_payload(v, 'EPI', rows_js)

    old_stamp = dashpatch.get_stamp(vs[0])
    new_stamp = dashpatch.pkt_stamp()
    for v in vs:
        dashpatch.set_stamp(v, new_stamp, old_stamp)
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)

    t = lambda k: format(sum(r[k] for r in rows), ',')
    p1, p3, m1, m2 = (sum(r[k] for r in rows) for k in ('p1', 'p3', 'mr1', 'mr2'))
    d13, dmr = (p1 - p3) / p1 * 100, (m1 - m2) / m1 * 100
    kp = drop['kp']
    note = ('EPI routine coverage replaced from the UC-wise EPI-MIS export %s (saved %s): %s UCs in %s '
            'districts, %s year to date; all %s reviewed polio UC matches kept as they are (the new extractor '
            'aborts on any new, renamed or moved UC, and %d zero-valued rows without a district are excluded). '
            'Penta-1 %s, Penta-3 %s, MR-1 %s, MR-2 %s, so the coverage-derived Penta-1->Penta-3 dropout is '
            '%.1f%% and MR-1->MR-2 %.1f%%. September is no longer called partial in the year-to-date figures '
            '(its residual is about a full month); the month-by-month archive keeps its older September '
            'part-report bar and is relabelled, and every year-to-date label now uses the new dated EPIYTD '
            'source payload instead of borrowing the EMETA monthly window (summary, exports, both briefing '
            'generators, home, hubs, critical analysis, three questions). Added the published district dropout '
            'report (EPIDROP from %s: %d districts plus the KP total, five dose pairs, male/female/total, CSV) '
            'as its own table beside the dashboard-calculated dropout, with the disagreement stated rather '
            'than smoothed away (KP Penta-1->Penta-3: report %d%%, UC doses %.1f%%; MR-1->MR-2: %d%% vs %.1f%%) '
            'and a rule that published rates are never averaged across districts. Timestamp refresh %s PKT.'
            % (meta['src'], meta['got'], format(meta['ucs'], ','), meta['dists'], meta['per'],
               meta['matched'], meta['excluded'], t('p1'), t('p3'), t('mr1'), t('mr2'), d13, dmr,
               drop['m']['src'], drop['m']['dists'], kp['p1p3'][2], d13, kp['mr12'][2], dmr, new_stamp))
    for v in vs:
        print('  %-42s %+9d chars  %s' % (v.rel, v.delta(), '; '.join(v.changes)))
    print('stamp: %s -> %s' % (old_stamp, new_stamp))
    print('note : %s' % note)
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0
    srcutil.write_text(os.path.join(HERE, 'out', 'epi_note.txt'), note.replace('\n', ' ').strip() + '\r\n')
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, note)
    print('written (no commit, no push)')
    return 0


if __name__ == '__main__':
    main()
