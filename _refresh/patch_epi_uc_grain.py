# -*- coding: utf-8 -*-
"""EPI: one row per UC in the "Antigen coverage" table, next to the district rows.

The owner asked, 25-Nov-2026: "we have all the available data district and UC wise in dashboard. I
need you to add UC wise as well in Antigen coverage by district table. It is currently only district
wise but you can add UC wise as well with it and it would be more convenient. ... Coverage uc wise
is most important which is missing."

The table is rebuilt from the same monthly UC matrix the doses table already reads (const EPIUC), so
no payload changes. Three rules keep it honest:

  1. The grain follows the EPI month picker and the division / district / tehsil filters. Year to
     date is the Jan-Sep 2026 UC export; a month is that month's UC-wise export.
  2. A UC month is only shown when its UC rows add up to the district file for that month. The
     October 2026 UC export is a mid-month part-report (its Penta-1 rows sum to 52,469 against the
     district file's 98,985, i.e. 53%; September is 100%), so a UC coverage rate for it would read
     as a false drop. That month stays at district grain and the pill says why. The download card
     applies the same rule, so a part-report month cannot be exported at UC or Tehsil grain either.
  3. Every rate is the row's own doses over the row's own target - nothing is averaged up from the
     row above and no UC row inherits the district figure.

Applied to all four variants in one pass (the public trio must stay byte-identical). `--unpatch`
restores the previous text; `--check` prints what would change.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch


def nl(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


# ---------------------------------------------------------------- edits

HEADER = (r'''<div class="tblhdr"><h3 style="margin:0" id="eGT">Antigen coverage by district</h3><span class="cnt">Click a district to drill down to its tehsils</span></div>
''', r'''<div class="tblhdr"><h3 style="margin:0" id="eGT">Antigen coverage by district</h3><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span class="cnt" id="eGcnt"></span><div class="pills" id="eGpills"><button class="btn on" data-g="d">District</button><button class="btn" data-g="u">UC</button></div></div></div>
''')

CAPTION = (r'''<div class="cap">Coverage % = doses given ÷ target for Jan 2026''',
           r'''<div class="cap" id="eGTCap">Coverage % = doses given ÷ target for Jan 2026''')

INTRO = (r'''click one of those meters to add it there, and the CSV always holds all 19.''',
         r'''click one of those meters to add it there, and the CSV always holds all 19. The <b>Antigen coverage</b> table below switches between district rows and one row per UC for any period whose UC-wise export is complete; 2024, and October 2026 whose UC-wise export is only a part-report, stay at district grain.''')

DLNOTE = (r'''the Jan–Sep 2026 year-to-date total is always on offer as its own row.''',
          r'''the Jan–Sep 2026 year-to-date total is always on offer as its own row. October 2026 has no complete UC-wise export yet, so UC and Tehsil rows are switched off for it and it downloads at district grain only.''')

TOPBAR = (r'''${EM?' · month view (UC coverage table is YTD)':''}''',
          r'''${EM?' · month view':''}''')

STATE = (r'''let EN='d', EYD=[];''', r'''let EN='d', EG='d', EYD=[];''')

PART = (r'''const eucRow=(r,i,mi)=>{const o={...r};if(EUCOK&&mi>=0){const w=EUCM.rows[i];EUCM.k.forEach((k,j)=>{o[k]=w[j][mi];});}return o;};
''', r'''const eucRow=(r,i,mi)=>{const o={...r};if(EUCOK&&mi>=0){const w=EUCM.rows[i];EUCM.k.forEach((k,j)=>{o[k]=w[j][mi];});}return o;};
// A UC month can be a mid-month snapshot. Its UC rows then add up to well under the district file
// for the same month, so a per-UC coverage rate would read as a false drop. Such a month is kept
// at district grain and the reason is shown. Measured on Penta-1, the dose every UC reports.
const EUCPART=(()=>{const S={};if(!EUCOK||EUCI['p1']==null)return S;const pi=EUCI['p1'];
 const dt={};(EPIM||[]).forEach(r=>{dt[r.mo]=(dt[r.mo]||0)+(r.p1||0);});
 (EUCM.mo||[]).forEach((m,mi)=>{const d=dt[m.mo];if(!d)return;let u=0;
  EUCM.rows.forEach(w=>{const v=w[pi]&&w[pi][mi];if(v!=null)u+=v;});
  const q=u/d;if(q<0.9)S[m.mo]=Math.round(q*100);});
 return S;})();
const eucPart=mo=>EUCPART[mo]||0;
''')

UC_MONTH_OK = (r'''const exUCMonthOK=mo=>EUCOK&&eucMi(mo)>=0;''',
               r'''const exUCMonthOK=mo=>EUCOK&&eucMi(mo)>=0&&!eucPart(mo);''')

UC_MONTH_CMT = (r'''// EPI-MIS publishes UC rows month by month for 2023, 2025 and every 2026 month on file; 2024 was
// exported district-level only. A month with no UC export stays in the list but switched off, so
// choosing the UC grain never makes the month list disappear.
''', r'''// EPI-MIS publishes UC rows month by month for 2023, 2025 and every 2026 month on file; 2024 was
// exported district-level only. A month with no UC export stays in the list but switched off, so
// choosing the UC grain never makes the month list disappear. A part-report UC month is switched
// off the same way: its UC rows are a slice of the month, so its percentages are not coverage.
''')

MONTHBOX = (r''' box.innerHTML=av.map(p=>{const k=p.mo||'YTD';
  return '<label title="'+(p.off?'UC month-wise rows are not published for '+p.lab:'')+'" style="display:flex;align-items:center;gap:6px;cursor:'+(p.off?'not-allowed':'pointer')+(p.off?';opacity:.45;':'')+'"><input type="checkbox" value="'+esc(k)+'"'+(p.off?' disabled':'')+(EXPER.has(k)&&!p.off?' checked':'')+'>'+esc(p.mn)+'</label>';}).join('');
''', r''' box.innerHTML=av.map(p=>{const k=p.mo||'YTD',pt=!!eucPart(p.mo);
  return '<label title="'+(p.off?(pt?'No complete UC rows for '+p.lab+' — its UC-wise export is a mid-month part-report':'UC month-wise rows are not published for '+p.lab):'')+'" style="display:flex;align-items:center;gap:6px;cursor:'+(p.off?'not-allowed':'pointer')+(p.off?';opacity:.45;':'')+'"><input type="checkbox" value="'+esc(k)+'"'+(p.off?' disabled':'')+(EXPER.has(k)&&!p.off?' checked':'')+'>'+esc(p.mn)+(pt?' · part-report':'')+'</label>';}).join('');
''')

HINT = (r''' if(hint){hint.style.display=offN?'':'none';
  hint.textContent=offN?'UC rows are published month by month for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, so the '+EXY+' months above are switched off. Change Year to 2023, 2025 or 2026 for month-by-month UC rows, or tick "Jan–Sep 2026 (year to date)" for the 2026 UC total.':'';}
''', r''' if(hint){const pr=av.filter(p=>p.off&&eucPart(p.mo));
  hint.style.display=offN?'':'none';
  hint.textContent=!offN?'':pr.length?'No complete UC rows for '+pr.map(p=>p.lab).join(', ')+' — that UC-wise export is a mid-month part-report (about '+pr.map(p=>eucPart(p.mo)).join('%, ')+'% of the district total), so its UC rates would read as a false drop. District rows stay available for it; UC months run Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year-to-date total.':'UC rows are published month by month for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, so the '+EXY+' months above are switched off. Change Year to 2023, 2025 or 2026 for month-by-month UC rows, or tick "Jan–Sep 2026 (year to date)" for the 2026 UC total.';}
''')

EN_CAP = (r'''  cap.textContent='Doses given by each UC for '+(EM?emLab(EM):EPER)+', from the UC-wise '+(EM?'single-month':'year-to-date')+' export.';
''', r'''  const pr=eucPart(EM);
  cap.textContent='Doses given by each UC for '+(EM?emLab(EM):EPER)+', from the UC-wise '+(EM?'single-month':'year-to-date')+' export.'+(pr?' That export is a mid-month part-report (about '+pr+'% of the district total), so these are doses recorded so far, not a full month.':'');
''')

HANDLER = (r'''el('eNpills').querySelectorAll('button').forEach(b=>b.onclick=()=>{EN=b.dataset.g;renderEN();});
''', r'''el('eNpills').querySelectorAll('button').forEach(b=>b.onclick=()=>{EN=b.dataset.g;renderEN();});
if(el('eGpills'))el('eGpills').querySelectorAll('button').forEach(b=>b.onclick=()=>{
 if(b.disabled||EG===b.dataset.g)return;
 EG=b.dataset.g;delete SORT.tEG;renderEOv();});
''')

NOTE = (r'''document.querySelectorAll('.emnote').forEach(n=>n.textContent=EM?'Month view uses district-level EPI-MIS monthly data (division and district filters apply). UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year to date; the All UCs coverage table stays year-to-date.':'Monthly charts use district-level EPI-MIS data; UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year to date.');}''',
         r'''document.querySelectorAll('.emnote').forEach(n=>n.textContent=EM?'Month view uses district-level EPI-MIS monthly data (division and district filters apply). The Antigen coverage table switches to one row per UC when the UC-wise export for that month is complete; 2024 and the October part-report stay at district grain. The All UCs table stays year-to-date.':'Monthly charts use district-level EPI-MIS data; UC doses exist for Jan–Dec 2023, Jan–Dec 2025 and Jan–Sep 2026, plus the 2026 year to date.');}''')

ENOTE = (r'''Showing <b>'+esc(emLab(EM))+'</b> only — district-level EPI-MIS monthly data. The All UCs table and the Priority UCs page remain year-to-date; the doses table below has UC numbers for the 2023, 2025 and 2026 months.''',
         r'''Showing <b>'+esc(emLab(EM))+'</b> only — district-level EPI-MIS monthly data. The All UCs table and the Priority UCs page remain year-to-date; the doses table below has UC numbers for the 2023, 2025 and 2026 months, and the coverage table switches to UC rows when that month has a complete UC-wise export.''')

TABLE = (r''' var capEG=el('eGT').closest('.card').querySelector('.cap');
 if(capEG){ if(!capEG.dataset.ytd)capEG.dataset.ytd=capEG.innerHTML;
  capEG.innerHTML=EM?'Coverage % = doses given ÷ target for the selected month (district-level EPI-MIS monthly data). Over 100% usually means the monthly target is too low or children from other areas were vaccinated here. Dropout columns stay year-to-date.':capEG.dataset.ytd;}
 // tables
 el('eGT').textContent=`Antigen coverage by ${L.lvl}`;
 const nn=(k,l,f)=>({k,l,n:1,f});
 const agCols=EAG.filter(x=>x.core||x.k===a.k).map(x=>({k:'p_'+x.k,l:x.l,n:1,cls:'ec',f:r=>pE(r['p_'+x.k])}));
 drawTable('tEG',[{k:'k',l:L.Lvl,f:x=>L.key==='d'?dz(x.k):`<b>${esc(x.k)}</b>`},(EM?{k:'u',l:'UCs',n:1,f:()=>'<span style="color:var(--color-text-muted)">YTD</span>'}:nn('u','UCs')),nn('s','Target infants',x=>fmt(x.s)),...agCols,nn('d13','P1→P3 drop',x=>(x.d13==null?'–':rgNL(x.d13,5,10)+'%')),nn('dmr','MR1→2 drop',x=>(x.dmr==null?'–':rgNL(x.dmr,10,20)+'%'))],G,'p_'+a.k,1);
''', r''' // tables — district rows, or one row per UC when the UC-wise export covers the period
 const nn=(k,l,f)=>({k,l,n:1,f});
 const eMi=EM?eucMi(EM):-1, ePart=EM?eucPart(EM):0, eUp=EUCOK&&(!EM||(eMi>=0&&!ePart));
 // the reader's grain is remembered, but a period with no UC rows falls back to district without
 // discarding it, so returning to a complete month restores the UC table
 const eGr=(EG==='u'&&eUp)?'u':'d';
 const agCols=EAG.filter(x=>x.core||x.k===a.k).map(x=>({k:'p_'+x.k,l:x.l,n:1,cls:'ec',f:r=>pE(r['p_'+x.k]),sv:r=>r['p_'+x.k]==null?1e9:r['p_'+x.k]}));
 const eGcnt=el('eGcnt'), eGcap=el('eGTCap');
 el('eGT').textContent='Antigen coverage by '+(eGr==='u'?'UC':L.lvl);
 if(eGr==='u'){
  const U=(EM?EPI.map((r,i)=>eucRow(r,i,eMi)).filter(matchE):cur).map(r=>{const o2={...r};
   EAG.forEach(x=>o2['p_'+x.k]=eP(r,x.k));
   o2.d13=(r.p1&&r.p3!=null)?(r.p1-r.p3)/r.p1*100:null;
   o2.dmr=(r.mr1&&r.mr2!=null)?(r.mr1-r.mr2)/r.mr1*100:null;return o2;});
  if(eGcnt)eGcnt.textContent=fmt(U.length)+' UCs in view';
  if(eGcap)eGcap.textContent='Coverage % = doses given ÷ target for '+(EM?emLab(EM):EPER)+', one row per EPI-MIS union council ('+(EM?'UC-wise single-month export':'UC-wise year-to-date export')+'). Over 100% usually means the target is set too low or children from other areas were vaccinated here. Dropout = share of children who got the first dose but not the later one. Lowest coverage first.';
  drawTable('tEG',[{k:'d',l:'District',f:r=>dz(r.d)},{k:'t',l:'Tehsil'},{k:'en',l:'UC (EPI-MIS)'},nn('s','Target infants',r=>fmt(r.s)),...agCols,nn('d13','P1→P3 drop',r=>(r.d13==null?'–':rgNL(r.d13,5,10)+'%')),nn('dmr','MR1→2 drop',r=>(r.dmr==null?'–':rgNL(r.dmr,10,20)+'%'))],U,'p_'+a.k,1);
 }else{
  if(eGcnt)eGcnt.textContent=fmt(G.length)+' '+L.pl+' in view';
  if(eGcap)eGcap.textContent=EM?'Coverage % = doses given ÷ target for '+emLab(EM)+' (district-level EPI-MIS monthly data). Over 100% usually means the monthly target is too low or children from other areas were vaccinated here. Dropout columns stay year-to-date.':'Coverage % = doses given ÷ target for Jan 2026 – Sep 2026 (newborns for BCG and OPV-0, surviving infants for the rest). Over 100% usually means the target is set too low or children from other areas were vaccinated here. Dropout = share of children who got the first dose but not the later one.';
  drawTable('tEG',[{k:'k',l:L.Lvl,f:x=>L.key==='d'?dz(x.k):`<b>${esc(x.k)}</b>`},(EM?{k:'u',l:'UCs',n:1,f:()=>'<span style="color:var(--color-text-muted)">YTD</span>'}:nn('u','UCs')),nn('s','Target infants',x=>fmt(x.s)),...agCols,nn('d13','P1→P3 drop',x=>(x.d13==null?'–':rgNL(x.d13,5,10)+'%')),nn('dmr','MR1→2 drop',x=>(x.dmr==null?'–':rgNL(x.dmr,10,20)+'%'))],G,'p_'+a.k,1);
 }
 if(el('eGpills'))el('eGpills').querySelectorAll('button').forEach(b=>{const u=b.dataset.g==='u';
  b.classList.toggle('on',b.dataset.g===eGr);
  if(u){b.disabled=!eUp;b.textContent=ePart?'UC (part-report)':'UC';
   b.title=!EUCOK?'UC rows are not embedded in this build':!EM?'One row per union council':eMi<0?'No UC-wise export exists for '+emLab(EM)+' — 2024 was published district-level only':ePart?'The UC-wise export for '+emLab(EM)+' is a mid-month part-report (about '+ePart+'% of the district total), so UC coverage is not shown for it':'One row per union council';}});
''')

TICKEU = (r''' if(EM){const nu=eucMi(EM)>=0;el('tEU').innerHTML='<tr><td class="empty">'+(nu?'UC coverage here stays year-to-date — the <b>doses table</b> above has this month at UC level.':'No UC-level detail exists for '+esc(emLab(EM))+' — UC rows exist for the 2023, 2025 and 2026 monthly exports; the 2024 exports are district-level, so that year has no UC grain. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> to Year to date.')+'</td></tr>';el('cntEU').textContent=nu?'UC coverage: year to date':'UC detail unavailable for this month';el('btnEUCSV').disabled=true;el('btnEUCSV').title='Set EPI month to Year to date to download UC coverage';}
''', r''' if(EM){const mi=eucMi(EM),pr=eucPart(EM);
  el('tEU').innerHTML='<tr><td class="empty">'+(mi>=0&&!pr?'This table stays year to date — the <b>Antigen coverage</b> table above has '+esc(emLab(EM))+' at UC grain.':pr?'No UC coverage for '+esc(emLab(EM))+' — its UC-wise export is a mid-month part-report (about '+pr+'% of the district total), so the <b>Antigen coverage</b> table stays at district grain. The <b>doses table</b> has UC counts for the month; set <b>EPI month</b> to Year to date for UC coverage.':'No UC-level detail exists for '+esc(emLab(EM))+' — UC rows exist for the 2023, 2025 and 2026 monthly exports; the 2024 exports are district-level, so that year has no UC grain. Use the <b>doses table</b> for district numbers, or set <b>EPI month</b> to Year to date.')+'</td></tr>';
  el('cntEU').textContent=(mi>=0&&!pr)?'UC coverage: year to date':'UC detail unavailable for this month';
  el('btnEUCSV').disabled=true;el('btnEUCSV').title='Set EPI month to Year to date to download UC coverage';}
''')

EDITS = [
    ('header', HEADER),
    ('caption', CAPTION),
    ('intro', INTRO),
    ('download note', DLNOTE),
    ('top bar', TOPBAR),
    ('state', STATE),
    ('part-report map', PART),
    ('download uc months', UC_MONTH_OK),
    ('download uc comment', UC_MONTH_CMT),
    ('month box', MONTHBOX),
    ('download hint', HINT),
    ('doses caption', EN_CAP),
    ('grain handler', HANDLER),
    ('month note', NOTE),
    ('coverage note', ENOTE),
    ('coverage table', TABLE),
    ('all ucs note', TICKEU),
]


def apply(text, pairs, strict=True):
    for name, (old, new) in pairs:
        o, n = nl(old), nl(new)
        c = text.count(o)
        if c != 1:
            raise AssertionError('%s: anchor found %d times (want 1)' % (name, c))
        text = text.replace(o, n, 1)
    return text


def unapply(text, pairs):
    for name, (old, new) in reversed(pairs):
        o, n = nl(old), nl(new)
        c = text.count(n)
        if c != 1:
            raise AssertionError('%s: patched text found %d times (want 1)' % (name, c))
        text = text.replace(n, o, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    pairs = EDITS
    for v in vs:
        v.require('id="eGT"' in v.text, 'the EPI antigen table is not present in %s' % v.rel)
        v.text = unapply(v.text, pairs) if a.unpatch else apply(v.text, pairs)
    if all(not v.changed for v in vs):
        print('NO CHANGE')
        return 0
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    for v in vs:
        print('%s %-42s %+8d chars' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel, v.delta()))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants(vs)
    print('WROTE %d variants' % sum(1 for v in vs if v.changed))
    return 0


if __name__ == '__main__':
    sys.exit(main())
