# -*- coding: utf-8 -*-
"""Correct the MPQA sampling framing and add the UC-level assigned list.

WHY (owner, 25-Oct-2026): "MPQA is randomly planned for low performing ucs or any other
indicator but it is not mandatory for all ucs of district." Every label that read planned /
picked / review progress implied a district duty to assess its whole UC list, and the pass
shares implied a province-wide micro-plan quality rate. Both are wrong:

  * assigned / campaign UCs  -> a sampling share, never a coverage target,
  * pass / needs / serious   -> bands over the UCs already reported, of deliberately
                                problem-selected plans, so not a quality rate for the district,
  * reported / assigned      -> the one figure a district actually owes.

So planned -> assigned, scored -> reported, review progress -> reported % of assigned,
backlog -> reports still owed. The same round's UC-level export (const MPQA.u, from
extract_mpqa.py) is landed here as a district-pickable table of the assigned UCs with their
reported state and desk / field / over-all scores, on the NEAP UC-table conventions. The
export's per-checklist-item columns stay un-published: its header lists 20 questions over 17
score columns, so no item can be tied to a column.

CHAINED PATCH. The strings it replaces come from patch_mpqa_ui.py (the MPQA card and
renderMPQ) and patch_sitrep_ui.py (SITREP deck Section 4 text); this module does not re-run
them and they must not be re-run over it. Un-patch in reverse module order - this module
first. It edits all four variants, not the master only: every anchor is a single line that
the refresh pipeline keeps byte-identical across them, so no variant keeps the old framing.

Usage:
  python _refresh/patch_mpqa_framing.py --dry-run    anchor checks and diff report, writes nothing
  python _refresh/patch_mpqa_framing.py              patch all four variants
  python _refresh/patch_mpqa_framing.py --unpatch    reverse it
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = '\r\n'
Q = "'"

# ---- the UC-level card, inserted straight after the MPQA district card -------------------
ANCHOR_CARD = r'''<div class="cap" id="capMPQ"></div></div>'''
CARD = (r'<div class="card" id="cardMPQU" style="margin-bottom:16px;display:none">'
        r'<div class="cqbar" style="margin:0 0 10px"><b>District</b>'
        r'<select id="fMPQU" aria-label="District"></select><span class="cnt" id="cntMPQU"></span>'
        r'<span style="flex:1"></span><button class="btn" id="btnMPQUcsv">Download (CSV)</button></div>'
        r'<div class="scroll" style="max-height:560px"><table id="tMPQU"></table></div>'
        r'<div class="cap" id="capMPQU"></div></div>')

# ---- the UC-level renderer, appended inside renderMPQ (its last statement is the CSV) ----
ANCHOR_JS = r'''x.under==null?'':rnd(x.under)]));''' + CRLF + r'''}'''
UC_JS = r'''
 const MU=M.u, TR=M.thr||[90,70], dnU=Object.keys(M.d).sort();
 if(!MU||!MU.r){ el('cardMPQU').style.display='none'; }
 else{
  el('cardMPQU').style.display='';
  const selU=el('fMPQU');
  if(selU.dataset.built!=='1'){ selU.innerHTML='<option value="-1">All districts</option>'+dnU.map((d,i)=>'<option value="'+i+'">'+esc(d)+'</option>').join(''); selU.dataset.built='1'; selU.onchange=()=>{MPQUD=+selU.value; renderMPQ();}; }
  if(MPQUD>=dnU.length)MPQUD=-1;
  selU.value=MPQUD;
  el('tMPQ').onclick=e=>{const tr=e.target.closest&&e.target.closest('tr'); if(!tr||!tr.cells||!tr.cells[0]||!tr.parentElement||tr.parentElement.tagName!=='TBODY')return; const i=dnU.indexOf(tr.cells[0].textContent.trim()); if(i>=0){MPQUD=i; renderMPQ();}};
  const TH=MU.t||[];
  const SU=MU.r.map(a=>{const x={d:a[0],t:TH[a[1]]||'',u:a[2],c:a[3],st:a[4],dk:a[5],fv:a[6],ov:a[7]};
   x.bd=x.st===2?'Not reported':(x.ov==null?'No over-all score':(x.ov>=TR[0]?'Pass':x.ov>=TR[1]?'Needs improvement':'Serious issues'));
   x.stl=x.st===2?'not reported':(x.st===1?'partial':'reported'); return x;});
  const FU=MPQUD>=0?SU.filter(x=>x.d===dnU[MPQUD]):SU;
  const scU=v=>v==null?'<span class="cnt">–</span>':'<span class="rg '+(v>=TR[0]?'g':v>=TR[1]?'a':'r')+'">'+rnd(v,1)+'</span>';
  const stTag=x=>x.st===2?'<span class="rg r">Not reported</span>':(x.st===1?'<span class="rg a">Partial</span>':'<span class="rg g">Reported</span>');
  drawTable('tMPQU',(MPQUD<0?[{k:'d',l:'District',f:x=>esc(x.d)}]:[]).concat([
   {k:'t',l:'Tehsil'},{k:'u',l:'UC',f:x=>'<b>'+esc(x.u)+'</b>'},{k:'c',l:'UC code'},critCol(x=>x.d,x=>x.u),
   {k:'st',l:'MPQA state',sv:x=>x.st,f:stTag,tt:'Whether this UC’s review has been filed. The list is a targeted sample, so Not reported is an outstanding review, not a missing score.'},
   {k:'ov',l:'Over-all %',n:1,tt:'The banded MPQA score: '+TR[0]+'+ pass, '+TR[1]+'-'+(TR[0]-1)+' needs improvement, under '+TR[1]+' serious',f:x=>scU(x.ov)},
   {k:'dk',l:'Desk review %',n:1,f:x=>scU(x.dk)},{k:'fv',l:'Field validation %',n:1,f:x=>scU(x.fv)},
   {k:'bd',l:'Band',f:x=>esc(x.bd)}]),FU,'st',-1);
  const rpU=FU.filter(x=>x.st!==2).length, ovU=FU.filter(x=>x.ov!=null);
  el('cntMPQU').textContent=fmt(FU.length)+' assigned UCs'+(MPQUD>=0?' · '+dnU[MPQUD]:' province-wide')+' · '+fmt(rpU)+' reported · '+fmt(FU.length-rpU)+' still to report';
  el('capMPQU').textContent='These '+fmt(FU.length)+' rows are the UCs assigned for micro-plan assessment in this view — a targeted sample of low-performing and flagged UCs, not every UC of the district. Read from '+esc(MU.src)+' (as of '+esc(MU.asof)+'): MPQA state is whether the review has been filed, and desk / field / over-all % are the scores as reported to the portal. A filed row can still carry no over-all score, which the portal counts as a serious issue. Sorted with the outstanding reviews on top, because filing the assigned list is the obligation; click a district row above to narrow to it. The same export carries per-checklist-item scores, but its header lists 20 questions over 17 score columns, so those are not published.'+(ovU.length?' Mean over-all of the '+fmt(ovU.length)+' scored UCs here: '+rnd(ovU.reduce((a,x)=>a+x.ov,0)/ovU.length,1)+'%.':'');
  el('btnMPQUcsv').onclick=()=>cqCSV('MPQA_assigned_UCs_'+M.camp,['District','Tehsil','UC','UC code','UC criteria','MPQA state','Desk review %','Field validation %','Over-all %','Band'],
   FU.map(x=>[x.d,x.t,x.u,x.c,critLab(x.d,x.u),x.stl,x.dk==null?'':rnd(x.dk,1),x.fv==null?'':rnd(x.fv,1),x.ov==null?'':rnd(x.ov,1),x.bd]));
 }'''

GLOBAL = (r'let NEPUD=-1;', r'let NEPUD=-1;' + CRLF + r'let MPQUD=-1;')

# ---- (old, new) string pairs: every old entry is one applied line of the dashboard -------
PAIRS = [
    # hub blurb
    (r'''micro-plan quality assessment (MPQA) scores of the UCs picked for review''',
     r'''micro-plan quality assessment (MPQA) scores of the UCs assigned for review (a targeted sample)'''),
    # KPI card labels
    (r'''<div class="kl">UCs picked for MPQA</div>''',
     r'''<div class="kl">UCs assigned for MPQA</div>'''),
    (r'''<div class="kl">Reviews completed</div>''',
     r'''<div class="kl">Assigned UCs reported</div>'''),
    # the hint
    (r''' el('mpqHint').innerHTML='Micro-plan quality assessment (MPQA) \u2014 <b>not</b> the same measure as \u201cmicroplans validated\u201d in the NEAP table above. The countdown calendar puts <b>real-time MPQA of selected UCs</b> on 21-Oct-2026, <b>course correction for failed UCs</b> on 23\u201324-Oct and <b>re-MPQA if required</b> on 26-Oct: the UCs scored here are the ones <b>assigned by the Federal office</b> and assessed live by District/Tehsil Officers and IMs, reported on the EOC <i>Campaign \u203a Pre Campaign \u203a Micro Plan Scoring</i> export (<b>'+esc(M.src)+'</b>, generated '+esc(M.gen)+'). For '+esc(M.camp)+' that is <b>'+fmt(picked)+' UCs picked for review</b> out of <b>'+fmt(su)+' campaign UCs</b> across all '+M.n+' SND districts ('+pcx(picked,su)+' of the scope), and <b>'+fmt(scored)+'</b> of the picked UCs have been scored so far \u2014 '+pcx(scored,picked)+' review progress, '+fmt(pend)+' still waiting. Pass / needs-improvement / serious shares are <b>of the UCs already scored</b>, never of the campaign.';''',
     r''' el('mpqHint').innerHTML='Micro-plan quality assessment (MPQA) \u2014 <b>not</b> the same measure as \u201cmicroplans validated\u201d in the NEAP table above, and <b>not</b> a check on every UC. The countdown calendar puts <b>real-time MPQA of selected UCs</b> on 21-Oct-2026, <b>course correction for failed UCs</b> on 23\u201324-Oct and <b>re-MPQA if required</b> on 26-Oct. The UCs scored here are a <b>targeted sample</b>: picked at random among low-performing UCs or UCs flagged on another indicator, <b>assigned by the Federal office</b>, then assessed live by District/Tehsil Officers and IMs and reported on the EOC <i>Campaign \u203a Pre Campaign \u203a Micro Plan Scoring</i> export (<b>'+esc(M.src)+'</b>, generated '+esc(M.gen)+'). For '+esc(M.camp)+' that sample is <b>'+fmt(picked)+' assigned UCs</b> out of <b>'+fmt(su)+' campaign UCs</b> across all '+M.n+' SND districts ('+pcx(picked,su)+' of the scope) \u2014 a <b>sampling share, not a coverage target</b>, since no district is required to have every UC assessed. What <b>is</b> owed is the assigned list itself: <b>'+fmt(scored)+'</b> of '+fmt(picked)+' reported so far, '+pcx(scored,picked)+' filed, '+fmt(pend)+' still to report. Pass / needs-improvement / serious shares are <b>of the UCs already reported</b>, never of the campaign, and because the sample is deliberately problem-selected they are <b>not</b> a province-wide micro-plan quality rate either.';'''),
    # KPI subtitles
    (r''' el('mpq1s').textContent='of '+fmt(su)+' campaign UCs \u00b7 '+pcx(picked,su)+' picked for review \u00b7 '+M.n+' districts';''',
     r''' el('mpq1s').textContent='sampled from '+fmt(su)+' campaign UCs \u00b7 '+M.n+' districts \u00b7 a share of the scope, not a target';'''),
    (r''' el('mpq2s').textContent=fmt(scored)+' of '+fmt(picked)+' scored \u00b7 '+fmt(pend)+' still to review';''',
     r''' el('mpq2s').textContent=fmt(scored)+' of '+fmt(picked)+' assigned UCs reported \u00b7 '+fmt(pend)+' still to file \u2014 the one MPQA obligation';'''),
    (r''' el('mpq3s').textContent=fmt(pass)+' UCs at 90+ \u00b7 of the UCs scored';''',
     r''' el('mpq3s').textContent=fmt(pass)+' UCs at 90+ \u00b7 of the '+fmt(scored)+' reported UCs only';'''),
    (r'''of scored UCs \u00b7 70\u201389, course correction due 23\u201324-Oct';''',
     r'''of reported UCs \u00b7 70\u201389, course correction due 23\u201324-Oct';'''),
    (r'''pcx(ser,scored)+' of scored UCs \u00b7 under 70 in ''',
     r'''pcx(ser,scored)+' of reported UCs \u00b7 under 70 in '''),
    # the chart
    (r'''  title:{text:'UCs picked for micro-plan assessment \u00b7 '+M.camp},''',
     r'''  title:{text:'UCs assigned for micro-plan assessment \u00b7 '+M.camp},'''),
    (r'''  subtitle:{text:'Where the score landed, and the reviews each district still has to do \u2014 biggest backlog on top'},''',
     r'''  subtitle:{text:'A targeted sample, not every UC \u00b7 where the reported scores landed and which districts still owe reports \u2014 most outstanding on top'},'''),
    (r'''title:{text:'UCs picked for MPQA'}''', r'''title:{text:'UCs assigned for MPQA'}'''),
    (r'''{name:'Picked, not yet scored',''', r'''{name:'Assigned, not yet reported','''),
    (r'''['#cbd5e1','Picked but not yet scored']''', r'''['#cbd5e1','Assigned but not yet reported']'''),
    # chart caption
    (r'''(deep.length?'Biggest review backlog: '+deep.slice(0,3).map(r=>r.d+' ('+r.un+' of '+r.pl+' picked UCs still unscored)').join('; ')+'.':'Every picked UC has been scored.')''',
     r'''(deep.length?'Most reports still owed: '+deep.slice(0,3).map(r=>r.d+' ('+r.un+' of '+r.pl+' assigned UCs not yet reported)').join('; ')+'.':'Every assigned UC has been reported.')'''),
    # the district table
    (r'''  {k:'mp',l:'Campaign UCs',n:1,f:x=>x.mp==null?'\u2013':fmt(x.mp)},''',
     r'''  {k:'mp',l:'Campaign UCs',n:1,tt:'UCs in the campaign scope, shown for context only \u2014 MPQA does not have to cover them',f:x=>x.mp==null?'\u2013':fmt(x.mp)},'''),
    (r'''{k:'pl',l:'Picked for MPQA',n:1,f:x=>fmt(x.pl)}''',
     r'''{k:'pl',l:'UCs assigned',n:1,tt:'The targeted sample the Federal office picked for this district \u2014 low-performing or flagged UCs \u2014 not every UC of the district',f:x=>fmt(x.pl)}'''),
    (r'''{k:'sc',l:'Scored',n:1,f:x=>fmt(x.sc)}''', r'''{k:'sc',l:'Reported',n:1,f:x=>fmt(x.sc)}'''),
    (r'''{k:'sp',l:'Review progress',n:1,tt:'Share of this district\'s picked UCs already scored',f:x=>stU(x.sp)}''',
     r'''{k:'sp',l:'Reported % of assigned',n:1,tt:'Share of the assigned sample whose review has been filed \u2014 the one MPQA figure a district owes',f:x=>stU(x.sp)}'''),
    (r'''{k:'un',l:'Still to review',n:1,f:x=>x.un===0?''',
     r'''{k:'un',l:'Still to report',n:1,tt:'Assigned UCs whose MPQA has not been filed yet',f:x=>x.un===0?'''),
    (r'''{k:'pp',l:'Pass % of scored',n:1,f:x=>pU(x.pp)}''', r'''{k:'pp',l:'Pass % of reported',n:1,f:x=>pU(x.pp)}'''),
    (r'''{k:'under',l:'Under 90 % of scored',n:1,f:x=>x.under==null?''',
     r'''{k:'under',l:'Under 90 % of reported',n:1,f:x=>x.under==null?'''),
    (r''' el('cntMPQ').textContent=M.n+' districts \u00b7 '+fmt(scored)+' of '+fmt(picked)+' picked UCs scored \u00b7 '+esc(M.gen);''',
     r''' el('cntMPQ').textContent=M.n+' districts \u00b7 '+fmt(scored)+' of '+fmt(picked)+' assigned UCs reported \u00b7 '+esc(M.gen);'''),
    (r''' el('capMPQ').textContent='Counts, not rates. Picked for MPQA is the UC list the Federal office assigned to this district, Scored is what has been assessed, and the three band columns split only the scored UCs. Review progress = scored / picked, while Pass % and Under 90 % are of the scored UCs \u2014 so a district can pass everything it has looked at and still be the one behind on the review (grey bar above). Review progress green at 100%, amber from 70%; pass share green at 90+, amber from 70; under 90 % of scored is better near zero. Course correction for failed UCs is due 23\u201324-Oct-2026 and re-MPQA 26-Oct on the countdown calendar.';''',
     r''' el('capMPQ').textContent='Counts, not rates. UCs assigned is the targeted sample the Federal office picked for this district \u2014 low-performing UCs or UCs flagged on another indicator \u2014 not a duty to assess every UC, so the Campaign UCs column is context and the assigned share of them is not a coverage target. Reported is what the district has filed, and the three band columns split only those reported UCs. Reported % of assigned = filed / assigned and is the one figure owed, while Pass % and Under 90 % are of reported UCs and \u2014 the sample being problem-selected by design \u2014 are not a province-wide micro-plan quality rate. A district can pass everything it has looked at and still owe the most reports (grey bar above). Reported % of assigned green at 100%, amber from 70%; pass share green at 90+, amber from 70; under 90 % of reported is better near zero. Course correction for failed UCs is due 23\u201324-Oct-2026 and re-MPQA 26-Oct on the countdown calendar.';'''),
    (r'''['District','Division','Category','Campaign UCs','UCs picked for MPQA','UCs scored','Review progress %','Picked not yet scored','Pass 90+','Pass % of scored','Needs improvement 70-89','Serious issues under 70','Under 90 % of scored']''',
     r'''['District','Division','Category','Campaign UCs','UCs assigned for MPQA','UCs reported','Reported % of assigned','Assigned not yet reported','Pass 90+','Pass % of reported','Needs improvement 70-89','Serious issues under 70','Under 90 % of reported']'''),
    # SITREP deck, Section 4
    (r'''(X.mpGen||X.asof)+' \u00b7 '+X.scope+' \u00b7 counts of UCs, not rates'+(X.MP.un?' \u00b7 '+n0(X.MP.un)+' UCs still to report':'')''',
     r'''(X.mpGen||X.asof)+' \u00b7 '+X.scope+' \u00b7 assigned sample, counts not rates'+(X.MP.un?' \u00b7 '+n0(X.MP.un)+' assigned UCs still to report':'')'''),
    (r'''{l:'UCs planned for MPQA',v:n0(X.MP.pl),s:X.mr.length+' '+plu(X.mr.length,'district')+' in scope'}''',
     r'''{l:'UCs assigned for MPQA',v:n0(X.MP.pl),s:'targeted sample \u00b7 '+X.mr.length+' '+plu(X.mr.length,'district')+' in scope'}'''),
    (r'''{l:'MPQA reported',v:n0(X.MP.sc),s:p1(X.MP.sp)+' of planned'}''',
     r'''{l:'Assigned UCs reported',v:n0(X.MP.sc),s:p1(X.MP.sp)+' of the assigned list'}'''),
    (r'''{l:'MPQA pending',v:n0(X.MP.un),vc:X.MP.un?RED:GRN,s:'not yet reviewed'}''',
     r'''{l:'Still to report',v:n0(X.MP.un),vc:X.MP.un?RED:GRN,s:'the one MPQA obligation'}'''),
    (r'''{l:'Pass (90+)',v:n0(X.MP.ps),s:p1(X.MP.pp)+' of reported'}''',
     r'''{l:'Pass (90+)',v:n0(X.MP.ps),s:p1(X.MP.pp)+' of reported \u00b7 sample only'}'''),
    (r'''table(s,['District','UCs planned','UCs reported','Report %','Pass','Needs improvement','Serious issues','Under 90 % of reported'],''',
     r'''table(s,['District','UCs assigned','UCs reported','Reported %','Pass','Needs improvement','Serious issues','Under 90 % of reported'],'''),
    (r'''('Showing 12 of '+X.mr.length+' districts with picked UCs, most pending first.')''',
     r'''('Showing 12 of '+X.mr.length+' districts with assigned UCs, those owing the most reports first.')'''),
    (r'''note(s,'UCs planned is the list the Federal office assigned to the district, UCs reported is what it has assessed, and the three band columns ('+X.mpBand.join(', ')+') split only the UCs already reported \u2014 so a district can pass everything it has looked at and still be behind on the review.',''',
     r'''note(s,'UCs assigned is a targeted sample picked from low-performing or flagged UCs, not a duty to assess every UC, so the assigned share of the campaign is not a coverage target. UCs reported is what the district has filed, and the bands ('+X.mpBand.join(', ')+') split only those reported UCs \u2014 problem-selected plans, so not a micro-plan quality rate for the district. What is owed is the assigned list: a district can pass every review it has filed and still owe reports.','''),
    (r'''A.push('Clear the '+n0(X.MP.un)+' pending micro-plan review'+(X.MP.un>1?'s':'')+' \u2014 furthest behind: ''',
     r'''A.push('File the '+n0(X.MP.un)+' outstanding MPQA report'+(X.MP.un>1?'s':'')+' on the assigned sample \u2014 furthest behind: '''),
    (r"'Micro-plan quality: '+X.mpSrc+', generated '+X.mpGen+' \u2014 counts of UCs, and the bands ('+X.mpBand.join(', ')+') split only the UCs already reported.'",
     r"'Micro-plan quality: '+X.mpSrc+', generated '+X.mpGen+' \u2014 counts of the UCs assigned as a targeted sample; the bands ('+X.mpBand.join(', ')+') split only the UCs already reported.'"),
]

NEW_MARKS = ['id="cardMPQU"', 'id="tMPQU"', 'id="fMPQU"', 'id="cntMPQU"', 'id="capMPQU"',
             'id="btnMPQUcsv"', 'let MPQUD=-1;', "drawTable('tMPQU'", 'MPQA state',
             'Assigned, not yet reported', 'Reported % of assigned', 'UCs assigned for MPQA',
             'Assigned UCs reported', 'Most reports still owed']
OLD_MARKS = ['id="cardMPQU"', 'let MPQUD=-1;', "drawTable('tMPQU'", 'Assigned, not yet reported',
             'Reported % of assigned', 'Most reports still owed', 'Assigned UCs reported']


def crlf(s):
    return s.replace('\n', CRLF).strip('\r\n')


def edits(reverse=False):
    seq = [(ANCHOR_CARD, ANCHOR_CARD + CRLF + CARD),
           (ANCHOR_JS, ANCHOR_JS.split(CRLF)[0] + CRLF + crlf(UC_JS) + CRLF + '}'),
           GLOBAL] + PAIRS
    if reverse:
        return [(n, o) for o, n in reversed(seq)]
    return seq


def apply(v, pairs):
    for old, new in pairs:
        v.require(v.count(old) == 1,
                  'anchor occurs %d times (want 1): %r' % (v.count(old), old[:80]))
        v.text = v.text.replace(old, new, 1)


def check(v, applied):
    marks = NEW_MARKS if applied else OLD_MARKS
    for p in (marks if applied else marks):
        n = v.count(p)
        if applied:
            v.require(n >= 1, 'the applied build lost %r' % p)
        else:
            v.require(n == 0, 'reversal left %r behind (%d)' % (p, n))
    if applied:
        for p in ('Picked for MPQA', 'Review progress', 'UCs planned for MPQA'):
            v.require(v.count(p) == 0, 'the old framing survived: %r' % p)
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    v.require(v.count('function renderMPQ(){') == 1, 'renderMPQ must stay one function')
    v.require(v.count('function renderNEP(){') == 1, 'the NEAP renderer must stay')
    v.require(v.count('const MPQA = ') == 1, 'the MPQA payload const must stay')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true',
                    help='reverse the framing fix and drop the UC-level block')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    applied = not a.unpatch
    seq = edits(a.unpatch)
    for v in vs:
        if 'const MPQA = ' not in v.text:
            raise SystemExit('%s: no MPQA block here - patch_mpqa_ui.py has to be applied first' % v.rel)
        had = v.count('id="cardMPQU"')
        if applied and had:
            raise SystemExit('%s: the MPQA framing fix is already applied' % v.rel)
        if a.unpatch and not had:
            raise SystemExit('%s: the MPQA framing fix is not applied, nothing to reverse' % v.rel)
        apply(v, seq)
        check(v, applied)
        v.changes.append('MPQA %s (%+d chars)' % ('framing + UC block' if applied else 'framing reversed',
                                                  v.delta()))
        print('  %-42s %+8d chars  %s' % (v.rel, v.delta(), '; '.join(v.changes)))
    sums = dashpatch.check_identical(cfg, vs)
    print('identical group md5: %s' % sums)
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    for v in vs:
        print('WROTE %s' % v.rel)
    print('OK mpqa-framing - now: python _refresh/refresh.py run --only mpqa,neap --force')
    return 0


if __name__ == '__main__':
    sys.exit(main())
