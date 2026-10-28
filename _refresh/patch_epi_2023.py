"""Add 2023 to the EPI coverage views (master only).

The 2023 monthly exports are UC-wise single-month files, so 2023 joins the year table
and the custom download as a full year, and the UC numbers table gains its months.
Run after the payloads (EMETA, EPIM, EPIUC) are in place.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

FIXES = [
    ('<span class="cnt">2024 · 2025 · 2026 year to date</span>',
     '<span class="cnt">2023 · 2024 · 2025 · 2026 year to date</span>'),

    ('District rows cover 2024–2026; UC rows cover <b>Jan–Dec 2025</b> and the <b>2026 year to date</b>, '
     'because the 2024 exports are district-level and the 2026 report exists only as year to date.',
     'District rows cover 2023–2026; UC rows cover <b>Jan–Dec 2023</b>, <b>Jan–Dec 2025</b> and the '
     '<b>2026 year to date</b> — 2024 is district-level only and 2026 has no single-month UC export, '
     'so UC rows are skipped for those periods.'),

    ('In the month view the extra doses exist only for the 2024 and 2025 monthly exports — 2025 is UC-level, '
     '2024 district-level — and the year table below adds each year up.',
     'In the month view the extra doses exist only for the 2023, 2024 and 2025 monthly exports — 2024 is '
     'district-level, 2023 and 2025 UC-level — and the year table below adds each year up.'),

    ('the doses table below has UC numbers for 2025 months.',
     'the doses table below has UC numbers for the 2023 and 2025 months.'),

    ("'No UC-level detail exists for '+esc(emLab(EM))+' — the 2024 exports are district-level and the 2026 "
     "report is year to date only. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> "
     "to Year to date.'",
     "'No UC-level detail exists for '+esc(emLab(EM))+' — UC rows exist for the 2023 and 2025 monthly "
     "exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no single-month "
     "UC export. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> to Year to date.'"),

    ("'<tr><td class=\"empty\">No UC-level numbers for '+esc(emLab(EM))+' — the 2024 exports are district-level "
     "and the 2026 report is year to date only. Switch to <b>District</b>, pick a 2025 month, or set "
     "<b>EPI month</b> to Year to date.</td></tr>'",
     "'<tr><td class=\"empty\">No UC-level numbers for '+esc(emLab(EM))+' — UC rows exist for the 2023 and "
     "2025 monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no "
     "single-month UC export. Switch to <b>District</b>, pick a 2023 or 2025 month, or set <b>EPI month</b> "
     "to Year to date.</td></tr>'"),

    ("'UC doses exist for Jan–Dec 2025 (UC-wise monthly exports) and for the 2026 year to date.'",
     "'UC doses exist for Jan–Dec 2023 and Jan–Dec 2025 (UC-wise monthly exports) and for the 2026 year to date.'"),

    ("(EM.slice(0,4)==='2025'?'the UC-wise single-month exports added up to district':'the 2026 monthly archive')",
     "(EM.slice(0,4)==='2026'?'the 2026 monthly archive':'the UC-wise single-month exports added up to district')"),

    ("function renderEY(){\n const a24=aggE(",
     "function renderEY(){\n const a23=aggE(EPIM.filter(r=>r.mo.slice(0,4)==='2023'&&matchEM(r)));\n const a24=aggE("),

    ("EYD=EAG.map((a,i)=>{const y24=a24['p_'+a.k],y25=a25['p_'+a.k],y26=a26['p_'+a.k];",
     "EYD=EAG.map((a,i)=>{const y23=a23['p_'+a.k],y24=a24['p_'+a.k],y25=a25['p_'+a.k],y26=a26['p_'+a.k];"),

    ("  return {o:i+1,k:a.k,l:a.l,y24,y25,y26,d24:a24[a.k],d25:a25[a.k],d26:a26[a.k],dl:(y25!=null&&y26!=null)?y26-y25:null};});",
     "  return {o:i+1,k:a.k,l:a.l,y23,y24,y25,y26,d23:a23[a.k],d24:a24[a.k],d25:a25[a.k],d26:a26[a.k],dl:(y25!=null&&y26!=null)?y26-y25:null};});"),

    ("  {k:'y24',l:'2024',n:1,sv:r=>r.y24==null?-1:r.y24,f:r=>cell(r.y24,r.d24)},",
     "  {k:'y23',l:'2023',n:1,sv:r=>r.y23==null?-1:r.y23,f:r=>cell(r.y23,r.d23)},\n"
     "  {k:'y24',l:'2024',n:1,sv:r=>r.y24==null?-1:r.y24,f:r=>cell(r.y24,r.d24)},"),

    ("el('capeY').textContent='Coverage % = doses ÷ target for each year’s months. 2024 and 2025 are the "
     "monthly EPI-MIS exports added up (2024 published district by district, 2025 UC by UC); 2026 is the "
     "Jan – Sep year to date from the UC-wise export. Doses sit under each percentage.'+"
     "((fTeh.value||q.value.trim())?' The tehsil/UC filters do not apply to 2024–2025: those exports are district-level.':'')",
     "el('capeY').textContent='Coverage % = doses ÷ target for each year’s months. 2023 and 2025 are the "
     "UC-wise monthly exports added up; 2024 is the district-level monthly exports added up; 2026 is the "
     "Jan – Sep year to date from the UC-wise export. Doses sit under each percentage.'+"
     "((fTeh.value||q.value.trim())?' The tehsil/UC filters narrow only the 2026 column: the 2023–2025 "
     "columns add up district rows.':'')"),

    ("const H=['#','Antigen','2024 coverage %','2024 doses','2025 coverage %','2025 doses',"
     "'2026 YTD coverage %','2026 YTD doses','Change 2025 to 2026 (pts)'];",
     "const H=['#','Antigen','2023 coverage %','2023 doses','2024 coverage %','2024 doses',"
     "'2025 coverage %','2025 doses','2026 YTD coverage %','2026 YTD doses','Change 2025 to 2026 (pts)'];"),

    ("const data=EYD.map(r=>[r.o,r.l,r.y24==null?'':+r.y24.toFixed(1),r.d24==null?'':r.d24,"
     "r.y25==null?'':+r.y25.toFixed(1),r.d25==null?'':r.d25,",
     "const data=EYD.map(r=>[r.o,r.l,r.y23==null?'':+r.y23.toFixed(1),r.d23==null?'':r.d23,"
     "r.y24==null?'':+r.y24.toFixed(1),r.d24==null?'':r.d24,r.y25==null?'':+r.y25.toFixed(1),r.d25==null?'':r.d25,"),

    ('const exYears=[2024,2025,2026];', 'const exYears=[2023,2024,2025,2026];'),

    ("add('Sources','2024: district-level single-month EPI-MIS exports · 2025: UC-wise single-month exports · "
     "2026: UC-wise year-to-date export (Jan – Sep).');",
     "add('Sources','2023 and 2025: UC-wise single-month EPI-MIS exports · 2024: district-level single-month "
     "exports · 2026: UC-wise year-to-date export (Jan – Sep).');"),

    ("if(skip.length)add('Not available at UC grain',skip.join(' · ')+'. The 2024 exports are district-level "
     "and the 2026 report is year to date only.');",
     "if(skip.length)add('Not available at UC grain',skip.join(' · ')+'. UC rows exist for the 2023 and 2025 "
     "monthly exports and the 2026 year to date; the 2024 exports are district-level and 2026 has no "
     "single-month UC export.');"),

    # the district-grain export row carried only two blanks (tehsil, UC) where the header has
    # three (tehsil, UC, EPI-MIS code), so every value from the targets on sat one column left
    ("'District · EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.k,'','',r.n,r.s,",
     "'District · EPI-MIS '+(p.mo?'single-month':'year to date'),r.dv,r.k,'','','',r.n,r.s,"),
]


FIXALL = [
    # the same sentence heads both branches of the month-view note
    ('UC doses exist for Jan–Dec 2025 and the 2026 year to date',
     'UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and the 2026 year to date'),
]


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    # the two renderEY insertions carry a newline; every newline in the file is CRLF
    for old, new in FIXES:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
        if new in v.text:
            print('  skip (already applied): %s' % new[:60].replace('\r\n', ' / '))
            continue
        n = v.text.count(old)
        if n != 1:
            raise SystemExit('ABORT: %d matches for %r' % (n, old[:70]))
        v.text = v.text.replace(old, new, 1)
        v.changes.append('2023: %s' % new[:60].replace('\r\n', ' / '))
    for old, new in FIXALL:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
        if new in v.text:
            print('  skip (already applied): %s' % new[:60].replace('\r\n', ' / '))
            continue
        n = v.text.count(old)
        if not n:
            raise SystemExit('ABORT: no matches for %r' % old[:70])
        v.text = v.text.replace(old, new)
        v.changes.append('%dx 2023: %s' % (n, new[:56].replace('\r\n', ' / ')))
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), len(v.changes)))
    for c in v.changes:
        print('  %s' % c)


if __name__ == '__main__':
    main()
