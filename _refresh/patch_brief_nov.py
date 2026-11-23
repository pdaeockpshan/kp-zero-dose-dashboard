# -*- coding: utf-8 -*-
"""Programme brief (A4 sheet + 15-slide deck): lead with SNID Nov-26 close-out,
re-anchor the decision horizon to NID Dec-26 (starts 12 December 2026).

Works on an LF-normalised copy in memory; writes the CRLF file once, at the end.
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

PATH = 'index.html'
raw = open(PATH, encoding='utf-8', newline='').read()
assert '\r\n' in raw, 'expected CRLF'
s = raw.replace('\r\n', '\n')
assert '\r' not in s, 'lone CR in source'

orig_len = len(s)


def rep(old, new, label):
    global s
    n = s.count(old)
    assert n == 1, f'{label}: anchor found {n} times'
    s = s.replace(old, new, 1)


def repn(old, new, n, label):
    global s
    got = s.count(old)
    assert got == n, f'{label}: expected {n}, found {got}'
    s = s.replace(old, new)


# ---------------------------------------------------------------- caveat
rep('var CAV="Caveat: Sept-26 covered figures are the round\'s own self-reported coverage export, not yet confirmed by a later round.";',
    'var CAV="Caveat: SNID Nov-26 has no covered figure yet — it is read on its UC target, LQAS, still-missed and validation returns. Sept-26 coverage is the round\'s own self-reported export, not yet confirmed.";',
    'CAV')

# ---------------------------------------------------------------- rbData Nov fields
rep("""  var teamPct=cq.l_tt?((cq.l_dn||0)+(cq.l_tm||0))/cq.l_tt*100:null;
  return {
    stamp:stamp(),""",
    """  var teamPct=cq.l_tt?((cq.l_dn||0)+(cq.l_tm||0))/cq.l_tt*100:null;
  var NSU=[];
  if(typeof NOVUC!=='undefined'&&NOVUC&&NOVUC.k&&NOVUC.r){
    var nb={}; NOVUC.k.forEach(function(k,i){nb[k]=i;});
    NOVUC.r.forEach(function(t){ NSU.push({dv:t[nb.dv],tg:t[nb.tg]||0,vac:t[nb.vac]||0,sna:t[nb.sna]||0,srf:t[nb.srf]||0,slo:t[nb.slo]||0}); });
  }
  var nsum=function(k){return NSU.reduce(function(a,r){return a+(r[k]||0);},0);};
  var nTg=nsum('tg'), nVac=nsum('vac'), nSna=nsum('sna'), nSrf=nsum('srf'), nSlo=nsum('slo'), nSt=nSna+nSrf+nSlo;
  var nDivD={};
  NSU.forEach(function(r){var k=r.dv||'\\u2013';var d=nDivD[k]=nDivD[k]||{tg:0,vac:0,n:0};d.tg+=r.tg;d.vac+=r.vac;d.n++;});
  var NDIV=Object.keys(nDivD).map(function(k){var d=nDivD[k];return {k:k,p:d.tg?d.vac/d.tg*100:null,n:d.n};}).sort(function(a,b){return (b.p||0)-(a.p||0);});
  var NREP=0,NUC=0;
  if(typeof novRows==='function'){var nrs=novRows();NUC=nrs.length;NREP=nrs.reduce(function(a,r){return a+(r.rN||0);},0);}
  var NHH=null,NREC=null;
  if(typeof NOVF!=='undefined'&&NOVF&&NOVF.k&&NOVF.tot){var nfi=function(k){var i=NOVF.k.indexOf(k);return i>=3&&NOVF.tot[i-3]!=null?+NOVF.tot[i-3]:null;};NHH=nfi('tgt');NREC=nfi('rec');}
  var NV=0,NVF=0,NVY=0;
  VAL.forEach(function(r){if(!/nov/i.test(String(r.cp||'')))return;NV+=(r.n||0);NVF++;NVY+=(r.vy||0);});
  return {
    stamp:stamp(),
    nRep:NREP, nUc:NUC, nTg:nTg, nVac:nVac, nCov:nTg?nVac/nTg*100:null, nSt:nSt, nSrf:nSrf, nSna:nSna, nSlo:nSlo,
    nStp:nTg?nSt/nTg*100:null, nHh:NHH, nHhPct:(NHH&&nSt)?nSt/NHH*100:null, nDiv:NDIV,
    nRec:NREC, nRecP:(NREC&&NREC>0)?Math.max(0,NREC-nSna-nSrf)/NREC*100:null,
    nVal:NV, nValF:NVF, nValY:NVY, nValP:NV?NVY/NV*100:null,""",
    'rbData nov block')

# ---------------------------------------------------------------- deliveryNote
rep("""function deliveryNote(D){
  return 'Delivery: '+n0(D.rep)+' zero-dose children reported in the round; ICM recall '+p1(D.icmR)+' on '+n0(D.icmRC)+' children checked, '+p1(D.away)+' of the '+n0(D.mi)+' missed were away from home and '+p1(D.ref)+' refused; LQAS '+n0(D.lP)+' of '+n0(D.lots)+' lots passed with '+p1(D.teamPct)+' of failures team-related; MPQA '+n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed as at '+h(D.mpqAs)+'.';
}""",
    """function deliveryNote(D){
  return 'Delivery: SNID Nov-26 recorded '+n0(D.nRep)+' zero-dose children in '+n0(D.nUc)+' UCs and vaccinated '+n0(D.nVac)+' against a '+n0(D.nTg)+' UC target ('+p1(D.nCov)+'), leaving '+n0(D.nSt)+' still missed after catch-up ('+p1(D.nStp)+' of the target); ICM recall '+p1(D.icmR)+' on '+n0(D.icmRC)+' children checked, '+p1(D.away)+' of the '+n0(D.mi)+' missed were away from home and '+p1(D.ref)+' refused; LQAS '+n0(D.lP)+' of '+n0(D.lots)+' lots passed with '+p1(D.teamPct)+' of failures team-related; MPQA '+n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed as at '+h(D.mpqAs)+'.';
}""",
    'deliveryNote')

# ---------------------------------------------------------------- kpi strip
rep("""  var kp=[
    {v:p1(D.covPct),l:n0(D.cov)+' of '+n0(D.rep)+' reported zero-dose children covered in Sept-26',c:''},
    {v:n0(D.rep),l:'zero-dose children reported in the September round',c:''},
    {v:p1(D.icmR),l:'ICM recall — '+n0(D.icmRV)+' of '+n0(D.icmRC)+' children checked',c:''},
    {v:p1(D.lots?D.lP/D.lots*100:null),l:n0(D.lP)+' of '+n0(D.lots)+' LQAS lots passed, '+n0(D.lF)+' failed',c:''},
    {v:p1(D.mpqPass),l:n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed, MPQA as at '+h(D.mpqAs),c:''}
  ]""",
    """  var kp=[
    {v:n0(D.nRep),l:'zero-dose children recorded in SNID Nov-26 across '+n0(D.nUc)+' UCs',c:''},
    {v:p1(D.nCov),l:n0(D.nVac)+' vaccinated of the '+n0(D.nTg)+' UC target — '+n0(D.nSt)+' still missed after catch-up',c:''},
    {v:p1(D.nStp),l:'still missed on the UC target ('+p1(D.nHhPct)+' of the household target); '+n0(D.nSrf)+' refused, '+n0(D.nSna)+' not available',c:'bad'},
    {v:p1(D.icmR),l:'ICM recall, SNID Nov-26 — '+n0(D.icmRV)+' of '+n0(D.icmRC)+' children checked',c:''},
    {v:p1(D.lots?D.lP/D.lots*100:null),l:'SNID Nov-26 LQAS — '+n0(D.lP)+' of '+n0(D.lots)+' lots passed, '+n0(D.lF)+' failed',c:''},
    {v:p1(D.mpqPass),l:'SNID Nov-26 MPQA — '+n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed (as at '+h(D.mpqAs)+')',c:''}
  ]""",
    'kpi strip')

# ---------------------------------------------------------------- rounds
rep("""<div class="rf">'+n0(D.cov)+' covered of '+n0(D.rep)+' reported</div></div>';""",
    """<div class="rf">'+n0(D.cov)+' covered of '+n0(D.rep)+' reported · last measured</div></div>'+
    '<div class="rb-round"><div class="rh"><span>Nov-26</span><b>'+p1(D.nCov)+'</b></div><div class="rb-track"><i style="width:'+Math.max(2,Math.min(100,D.nCov||0))+'%;background:'+((D.nCov||0)>=70?'#2f7d6d':(D.nCov||0)>=55?'#d9822b':'#b8442f')+'"></i></div><div class="rf">'+n0(D.nVac)+' vaccinated of '+n0(D.nTg)+' UC target · '+n0(D.nRep)+' recorded</div></div>';""",
    'rounds')

# ---------------------------------------------------------------- decisions table
rep("""  var dec=[
    ['Route the Nov-26 supervision wave to the '+n0(D.h50)+' UCs holding half the missed children','EOC-KP with division coordinators','5 Nov','Coverage in those UCs at or above 70%'],
    ['Re-verify ZD coverage in the '+n0(D.blocker)+' UCs that cannot close','District closure focal points','10 Nov','Closed UCs above 20% (from '+p1(D.clPct)+')'],
    ['Clear the '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage and '+n0(D.ovn)+' over-covered UCs before totals are read','M&amp;E and IDIMS cell','6 Nov','No UC outside the 50–110% band'],
    ['Move revisit windows to evenings and weekends in mobility districts','District health offices','From 2 Nov','Away-from-home share below 60%'],
    ['Put a female member on every monitoring team','District RHOs','Before deployment','Monitoring teams with a female member at or above 90%'],
    ['Clear the validation backlog on covered zero-dose children','Validation cell','20 Nov','60% validated (now '+p1(D.reg)+')']
  ]""",
    """  var dec=[
    ['Route the Dec-26 supervision wave to the '+n0(D.h50)+' UCs holding half the missed children','EOC-KP with division coordinators','5 Dec','Coverage in those UCs at or above 70%'],
    ['Re-verify ZD coverage in the '+n0(D.blocker)+' UCs that cannot close','District closure focal points','10 Dec','Closed UCs above 20% (from '+p1(D.clPct)+')'],
    ['Clear the '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage and '+n0(D.ovn)+' over-covered UCs before totals are read','M&amp;E and IDIMS cell','6 Dec','No UC outside the 50–110% band'],
    ['Move revisit windows to evenings and weekends in mobility districts','District health offices','From 12 Dec','Away-from-home share below 60%'],
    ['Put a female member on every monitoring team','District RHOs','Before deployment','Monitoring teams with a female member at or above 90%'],
    ['Clear the validation backlog on covered zero-dose children','Validation cell','20 Dec','60% validated (now '+p1(D.reg)+')']
  ]""",
    'decisions table')

# ---------------------------------------------------------------- sheet head
repn('The 2026 campaign year, and what November has to fix',
     'The 2026 campaign year, and what December has to fix', 2, 'headline')
repn('SNID Nov-26, starting 2 November 2026', 'NID Dec-26, starting 12 December 2026', 2, 'horizon')
repn('next review after SNID Nov-26', 'next review after NID Dec-26', 2, 'footer')

rep("""<p>A decision brief for the core team and the EOC-KP coordinator, built only from 2026 data: the campaign year first, then zero dose, routine EPI and surveillance, then the decisions. Regenerated from the live dashboard, so every figure below is the dashboard\\'s own roll-up of the 2026 exports.</p>""",
    """<p>A decision brief for the core team and the EOC-KP coordinator, built only from 2026 data: the campaign year first, then zero dose, routine EPI and surveillance, then the decisions. SNID Nov-26 has concluded and NID Dec-26 starts on 12 December, so the decisions are timed to that round. Regenerated from the live dashboard, so every figure below is the dashboard\\'s own roll-up of the 2026 exports.</p>""",
    'sheet intro')

# ---------------------------------------------------------------- finding 1
rep("""  '<div class="rb-find"><div class="n">'+p1(D.covPct)+'</div><p class="t">of '+n0(D.rep)+' reported zero-dose children were covered in Sept-26. On the '+n0(D.nL3)+' UCs present in all three rounds, like-for-like coverage fell to '+p1(D.lf)+', '+(D.lfA!=null?Math.abs(D.lfA-D.lf).toFixed(1):'–')+' points below April.</p></div>'+""",
    """  '<div class="rb-find"><div class="n">'+p1(D.nCov)+'</div><p class="t">of the '+n0(D.nTg)+' UC target vaccinated in SNID Nov-26, with '+n0(D.nSt)+' children ('+p1(D.nStp)+') still missed after catch-up. Sept-26, the last measured round, covered '+p1(D.covPct)+' of '+n0(D.rep)+' reported; on the '+n0(D.nL3)+' UCs present in all three rounds, like-for-like stood at '+p1(D.lf)+', '+(D.lfA!=null?Math.abs(D.lfA-D.lf).toFixed(1):'–')+' points below April.</p></div>'+""",
    'finding 1')

# ---------------------------------------------------------------- zero-dose block
rep("""  '<div class="rb-blk"><h4>Zero dose: concentration and closure</h4><span class="big">'+n0(D.net)+'</span>not covered in Sept-26 at UC-level net ('+p1(D.netPct)+' of the report). <span class="big">'+n0(D.st)+'</span>children missed across 2026; '+n0(D.h50)+' UCs hold half. '+n0(D.crS)+' UCs were covered below 50%. Only '+n0(D.cl)+' of '+n0(D.wd)+' UCs closed in 2026; '+n0(D.op)+' stay open.</div>'+""",
    """  '<div class="rb-blk"><h4>Zero dose: Nov-26, then the year</h4><span class="big">'+n0(D.nSt)+'</span>still missed after SNID Nov-26 catch-up ('+p1(D.nStp)+' of the UC target, '+p1(D.nHhPct)+' of the household target) from '+n0(D.nRep)+' recorded. <span class="big">'+n0(D.net)+'</span>not covered in Sept-26 at UC-level net. '+n0(D.h50)+' UCs hold half the year\\'s missed children; only '+n0(D.cl)+' of '+n0(D.wd)+' UCs closed in 2026, '+n0(D.op)+' stay open.</div>'+""",
    'zero-dose block')

# ---------------------------------------------------------------- surveillance block
rep(""". '+n0(D.val)+' children validated ('+p1(D.valPct)+' confirmed, '+n0(D.notVac)+' not vaccinated).</div>'+""",
    """. '+n0(D.val)+' children validated ('+p1(D.valPct)+' confirmed, '+n0(D.notVac)+' not vaccinated), '+n0(D.nVal)+' of them in Nov-26.</div>'+""",
    'surveillance block')

# ---------------------------------------------------------------- section 4 header
rep('<div class="rb-h">4 · Decisions before 2 November</div>',
    '<div class="rb-h">4 · Decisions before 12 December</div>',
    'section 4 header')

# ---------------------------------------------------------------- sources
rep('ZD reported and covered (NID Apr-26, SNID May-26, SNID Sept-26)',
    'ZD recorded and covered (NID Apr-26, SNID May-26, SNID Sept-26, SNID Nov-26)',
    'sources campaigns')
rep('intra-campaign monitoring for Sept-26 and LQAS to Nov-26',
    'intra-campaign monitoring and LQAS for SNID Nov-26',
    'sources monitoring')

# ---------------------------------------------------------------- cover slide
rep("s.addText('Data window Jan–Sep 2026  ·  Snapshot '+D.stamp,",
    "s.addText('Data window Jan–Nov 2026  ·  Snapshot '+D.stamp,",
    'cover window')
rep("""  kpi(s,0.67,4.45,3.7,1.75,p1(D.covPct),'of '+n0(D.rep)+' reported zero-dose children covered in the Sept-26 round');
  kpi(s,4.55,4.45,3.7,1.75,n0(D.net),'reported in Sept-26 and not covered (UC-level net)',C.red);""",
    """  kpi(s,0.67,4.45,3.7,1.75,p1(D.nCov),'of the '+n0(D.nTg)+' UC target vaccinated in SNID Nov-26');
  kpi(s,4.55,4.45,3.7,1.75,n0(D.nSt),'still missed after the Nov-26 catch-up — '+p1(D.nStp)+' of the UC target',C.red);""",
    'cover kpis')

# ---------------------------------------------------------------- slide 2
rep("s=base('For decision  ·  SNID Nov-26','Executive summary: three findings, three decisions',true);",
    "s=base('For decision  ·  NID Dec-26','Executive summary: three findings, three decisions',true);",
    'slide2 kicker')
rep("'DECISIONS BEFORE 2 NOVEMBER'", "'DECISIONS BEFORE 12 DECEMBER'", 'slide2 header')
rep("""  var F=[[p1(D.covPct),'of '+n0(D.rep)+' reported zero-dose children were covered in Sept-26. On the '+n0(D.nL3)+' UCs present in all three rounds, like-for-like coverage fell to '+p1(D.lf)+', '+(D.lfA!=null?Math.abs(D.lfA-D.lf).toFixed(1):'–')+' points below April.'],
        [p1(D.icmR),'ICM recall on '+n0(D.icmRC)+' children checked. '+p1(D.away)+' of the '+n0(D.mi)+' missed were away from home and '+p1(D.ref)+' refused, so the binding constraint is revisit timing inside the round.'],
        [n0(D.lP)+' of '+n0(D.lots),'LQAS lots passed, '+n0(D.lF)+' failed and '+p1(D.teamPct)+' of failures team-related; '+n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed as at '+h(D.mpqAs)+'.']];""",
    """  var F=[[p1(D.nCov),'of the '+n0(D.nTg)+' UC target vaccinated in SNID Nov-26; '+n0(D.nSt)+' children ('+p1(D.nStp)+') were still missed after catch-up. Sept-26, the last measured round, covered '+p1(D.covPct)+' of '+n0(D.rep)+' reported.'],
        [p1(D.icmR),'ICM recall on '+n0(D.icmRC)+' children checked in Nov-26. '+p1(D.away)+' of the '+n0(D.mi)+' missed were away from home and '+p1(D.ref)+' refused, so the binding constraint is revisit timing inside the round.'],
        [n0(D.lP)+' of '+n0(D.lots),'Nov-26 LQAS lots passed, '+n0(D.lF)+' failed and '+p1(D.teamPct)+' of failures team-related; '+n0(D.mpq[2])+' of '+n0(D.mpq[1])+' micro-plans passed as at '+h(D.mpqAs)+'.']];""",
    'slide2 findings')
rep("""  var Q=[[n0(D.h50)+' UCs','hold half of the '+n0(D.st)+' missed children. Send the Nov-26 supervisor wave to these UCs by name, not by district.'],
         [n0(D.blocker)+' UCs','need ZD coverage re-verified so closure can move; without it the tracker cannot show whether Nov-26 worked.'],
         ['4 gates','stand between Nov-26 and a readable total: '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage, '+n0(D.ovn)+' over-covered, and only '+p1(D.reg)+' of the validation register cleared.']];""",
    """  var Q=[[n0(D.h50)+' UCs','hold half of the '+n0(D.st)+' missed children. Send the Dec-26 supervisor wave to these UCs by name, not by district.'],
         [n0(D.blocker)+' UCs','need ZD coverage re-verified so closure can move; without it the tracker cannot show whether Nov-26 moved anything.'],
         ['4 gates','stand between Dec-26 and a readable total: '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage, '+n0(D.ovn)+' over-covered, and only '+p1(D.reg)+' of the validation register cleared.']];""",
    'slide2 decisions')

# ---------------------------------------------------------------- slide 3
rep("s=base('2026 record  ·  Jan–Sep','The 2026 record on one screen',true);",
    "s=base('2026 record  ·  Jan–Nov','The 2026 record on one screen',true);",
    'slide3 kicker')
rep("""  kpi(s,0.67,1.55,2.9,1.6,n0(D.rep),'zero-dose children reported in the Sept-26 round');
  kpi(s,3.72,1.55,2.9,1.6,p1(D.covPct),'covered in Sept-26 — '+n0(D.cov)+' children');
  kpi(s,6.77,1.55,2.9,1.6,n0(D.net)+' / '+n0(D.st),'Sept net uncovered · 2026 children missed');""",
    """  kpi(s,0.67,1.55,2.9,1.6,n0(D.nRep),'zero-dose children recorded in SNID Nov-26');
  kpi(s,3.72,1.55,2.9,1.6,p1(D.nCov),'of the UC target vaccinated — '+n0(D.nVac)+' of '+n0(D.nTg));
  kpi(s,6.77,1.55,2.9,1.6,n0(D.nSt),'still missed after the Nov-26 catch-up; '+p1(D.nStp)+' of the UC target',C.red);""",
    'slide3 kpis')
rep("""  var cols=[['WHAT IMPROVED','Catch-up sessions recovered 88.8% of missed doses. Admin campaign coverage reached '+p1(D.avac)+' in September ('+n0(D.avacV)+' of '+n0(D.avacT)+') and finger-marking '+p1(D.fm)+'.'],
            ['WHAT DID NOT','Like-for-like coverage fell to '+p1(D.lf)+' in September. Drop-out runs at '+p1(D.d13)+' Penta1→Penta3 and '+p1(D.dmr)+' MR1→MR2. '+n0(D.crS)+' UCs were covered below 50% in the Sept round.'],
            ['WHAT STAYS UNRESOLVED',''+n0(D.cases)+' confirmed polio cases. '+n0(D.blindD)+' blind-spot districts. Only '+p1(D.reg)+' of the zero-dose validation register is cleared. '+n0(D.pend)+' AFP cases still pending classification.']];""",
    """  var cols=[['WHAT IMPROVED','Admin campaign coverage reached '+p1(D.avac)+' in SNID Nov-26 ('+n0(D.avacV)+' of '+n0(D.avacT)+' household target) and finger-marking '+p1(D.fm)+'. Catch-up recovered '+p1(D.nRecP)+' of the '+n0(D.nRec)+' children recorded missed.'],
            ['WHAT DID NOT','Sept-26, the last measured round, covered '+p1(D.covPct)+' of '+n0(D.rep)+' reported. Drop-out runs at '+p1(D.d13)+' Penta1→Penta3 and '+p1(D.dmr)+' MR1→MR2. '+n0(D.crS)+' UCs were covered below 50% in the Sept round.'],
            ['WHAT STAYS UNRESOLVED',''+n0(D.cases)+' confirmed polio cases. '+n0(D.blindD)+' blind-spot districts. Only '+p1(D.reg)+' of the zero-dose validation register is cleared, and '+n0(D.nVal)+' Nov-26 children have been validated so far. '+n0(D.pend)+' AFP cases still pending classification.']];""",
    'slide3 cols')

# ---------------------------------------------------------------- slide 4
rep("s=base('Campaigns  ·  Apr / May / Sept 2026','Biggest report, smallest coverage share',true);",
    "s=base('Campaigns  ·  Apr / May / Sept / Nov 2026','Biggest report, smallest coverage share',true);",
    'slide4 kicker')
rep("""  var maxR=Math.max(D.rA,D.rM,D.rep)||1;
  [['Apr-26',D.rA,D.cA,D.pA,D.rcA],['May-26',D.rM,D.cM,D.pM,D.rcM],['Sept-26',D.rep,D.cov,D.covPct,D.rep]].forEach(function(c,i){
    var y=1.7+i*1.55;
    s.addText(c[0],{x:0.67,y:y,w:1.1,h:0.3,fontSize:11,bold:true,color:C.ink,fontFace:FF});
    s.addShape(p.ShapeType.roundRect,{x:1.8,y:y+0.02,w:c[1]/maxR*6.2,h:0.26,rectRadius:0.03,fill:{color:C.line},line:{width:0}});
    s.addShape(p.ShapeType.roundRect,{x:1.8,y:y+0.34,w:c[2]/maxR*6.2,h:0.26,rectRadius:0.03,fill:{color:i===2?C.pri:C.dim},line:{width:0}});
    s.addText(n0(c[1])+' reported',{x:8.15,y:y-0.02,w:1.9,h:0.3,fontSize:9.5,color:C.mut,fontFace:FF});
    s.addText(n0(c[2])+' covered',{x:8.15,y:y+0.3,w:1.9,h:0.3,fontSize:9.5,color:C.mut,fontFace:FF});
    s.addText(p1(c[3]),{x:10.3,y:y+0.05,w:1.5,h:0.5,fontSize:20,bold:true,color:c[3]>=70?C.pri:c[3]>=55?C.sec:C.red,fontFace:FF});
    s.addText(c[4]&&c[4]!==c[1]?'of '+n0(c[4])+' with coverage data':'all '+n0(c[4])+' reported',{x:8.15,y:y+0.62,w:2.1,h:0.24,fontSize:7.5,color:C.dim,fontFace:FF});
  });
  s.addText('WHAT CHANGED',{x:0.67,y:6.05,w:4,h:0.25,fontSize:8.5,bold:true,color:C.sec,charSpacing:1,fontFace:FF});
  s.addText(n0(D.rep)+' reported in Sept, the year\\'s highest  ·  '+p1(D.covPct)+' covered  ·  like-for-like '+p1(D.lfA)+' Apr → '+p1(D.lfM)+' May → '+p1(D.lf)+' Sept on '+n0(D.nL3)+' UCs',{x:0.67,y:6.32,w:11.9,h:0.35,fontSize:9.5,color:C.mut,fontFace:FF});""",
    """  var maxR=Math.max(D.rA,D.rM,D.rep,D.nRep)||1;
  [['Apr-26',D.rA,D.cA,D.pA,'of '+n0(D.rcA)+' with coverage data',false],
   ['May-26',D.rM,D.cM,D.pM,'of '+n0(D.rcM)+' with coverage data',false],
   ['Sept-26',D.rep,D.cov,D.covPct,'all '+n0(D.rep)+' reported',false],
   ['Nov-26',D.nRep,null,D.nCov,'of the '+n0(D.nTg)+' UC target vaccinated',true]].forEach(function(c,i){
    var y=1.5+i*1.15;
    s.addText(c[0],{x:0.67,y:y,w:1.1,h:0.3,fontSize:11,bold:true,color:C.ink,fontFace:FF});
    s.addShape(p.ShapeType.roundRect,{x:1.8,y:y+0.02,w:c[1]/maxR*6.2,h:0.24,rectRadius:0.03,fill:{color:C.line},line:{width:0}});
    if(c[2]!=null)s.addShape(p.ShapeType.roundRect,{x:1.8,y:y+0.30,w:c[2]/maxR*6.2,h:0.24,rectRadius:0.03,fill:{color:c[5]?C.pri:C.dim},line:{width:0}});
    s.addText(n0(c[1])+(c[5]?' recorded':' reported'),{x:8.15,y:y-0.02,w:2.0,h:0.3,fontSize:9.5,color:C.mut,fontFace:FF});
    s.addText(c[2]!=null?n0(c[2])+' covered':'covered figure awaited',{x:8.15,y:y+0.28,w:2.2,h:0.3,fontSize:9.5,color:c[2]!=null?C.mut:C.sec,fontFace:FF});
    s.addText(p1(c[3]),{x:10.3,y:y+0.02,w:1.5,h:0.5,fontSize:20,bold:true,color:c[3]>=70?C.pri:c[3]>=55?C.sec:C.red,fontFace:FF});
    s.addText(c[4],{x:8.15,y:y+0.60,w:2.1,h:0.24,fontSize:7.5,color:C.dim,fontFace:FF});
  });
  s.addText('WHAT CHANGED',{x:0.67,y:6.0,w:4,h:0.25,fontSize:8.5,bold:true,color:C.sec,charSpacing:1,fontFace:FF});
  s.addText(n0(D.nRep)+' recorded in SNID Nov-26, '+p1(D.nCov)+' of the UC target vaccinated and '+p1(D.nStp)+' still missed  ·  Sept covered '+p1(D.covPct)+' of '+n0(D.rep)+'  ·  like-for-like '+p1(D.lfA)+' Apr → '+p1(D.lfM)+' May → '+p1(D.lf)+' Sept on '+n0(D.nL3)+' UCs',{x:0.67,y:6.27,w:11.9,h:0.45,fontSize:9.5,color:C.mut,fontFace:FF});""",
    'slide4 rows')

# ---------------------------------------------------------------- slide 5
rep("s=base('Sept-26 coverage by division','Two programmes inside one province',true);",
    "s=base('Coverage by division  ·  Sept and Nov 2026','Two programmes inside one province',true);",
    'slide5 kicker')
rep("""  D.div.forEach(function(d,i){
    var y=1.62+i*0.68, col=d.p>=70?C.pri:d.p>=55?C.sec:C.red;
    s.addText(d.k,{x:0.67,y:y,w:2.2,h:0.3,fontSize:10.5,bold:true,color:C.ink,fontFace:FF});
    s.addShape(p.ShapeType.roundRect,{x:2.95,y:y+0.04,w:6.2,h:0.22,rectRadius:0.03,fill:{color:C.line},line:{width:0}});
    s.addShape(p.ShapeType.roundRect,{x:2.95,y:y+0.04,w:Math.max(0.04,Math.min(1,d.p/100)*6.2),h:0.22,rectRadius:0.03,fill:{color:col},line:{width:0}});
    s.addText(p1(d.p),{x:9.35,y:y-0.03,w:1.1,h:0.32,fontSize:12,bold:true,color:col,fontFace:FF});
    s.addText(n0(d.n)+' UCs',{x:10.55,y:y,w:1.2,h:0.3,fontSize:8.5,color:C.dim,fontFace:FF});
  });
  s.addText('WHAT THE SPLIT COSTS',{x:0.67,y:6.05,w:5,h:0.25,fontSize:8.5,bold:true,color:C.sec,charSpacing:1,fontFace:FF});
  s.addText(n0(D.net)+' not covered in Sept-26 ('+p1(D.netPct)+' of the '+n0(D.rep)+' reported)  ·  '+n0(D.crS)+' UCs covered below 50%  ·  '+D.hiDiv+' of '+D.div.length+' divisions at 89% or above',{x:0.67,y:6.32,w:11.9,h:0.35,fontSize:9.5,color:C.mut,fontFace:FF});""",
    """  D.div.forEach(function(d,i){
    var nd=(D.nDiv||[]).filter(function(x){return x.k===d.k;})[0], np=nd?nd.p:null, pUse=np!=null?np:d.p;
    var y=1.62+i*0.68, col=pUse>=70?C.pri:pUse>=55?C.sec:C.red;
    s.addText(d.k,{x:0.67,y:y,w:2.2,h:0.3,fontSize:10.5,bold:true,color:C.ink,fontFace:FF});
    s.addShape(p.ShapeType.roundRect,{x:2.95,y:y+0.04,w:6.2,h:0.22,rectRadius:0.03,fill:{color:C.line},line:{width:0}});
    s.addShape(p.ShapeType.roundRect,{x:2.95,y:y+0.04,w:Math.max(0.04,Math.min(1,(pUse||0)/100)*6.2),h:0.22,rectRadius:0.03,fill:{color:col},line:{width:0}});
    s.addText(p1(pUse),{x:9.35,y:y-0.03,w:1.1,h:0.32,fontSize:12,bold:true,color:col,fontFace:FF});
    s.addText(n0(d.n)+' UCs · Sept '+p1(d.p),{x:10.55,y:y,w:2.2,h:0.3,fontSize:8.5,color:C.dim,fontFace:FF});
  });
  s.addText('WHAT THE SPLIT COSTS',{x:0.67,y:6.05,w:5,h:0.25,fontSize:8.5,bold:true,color:C.sec,charSpacing:1,fontFace:FF});
  s.addText(n0(D.nSt)+' still missed after SNID Nov-26 ('+p1(D.nStp)+' of the UC target)  ·  '+n0(D.nRep)+' zero-dose children recorded  ·  '+n0(D.crS)+' UCs covered below 50% in Sept  ·  '+D.hiDiv+' of '+D.div.length+' divisions at 89% or above in Sept',{x:0.67,y:6.32,w:11.9,h:0.45,fontSize:9.5,color:C.mut,fontFace:FF});""",
    'slide5 divisions')

# ---------------------------------------------------------------- slide 6
rep("s=base('Monitoring  ·  Sept-26','Two instruments agree on coverage, not on cause',false);",
    "s=base('Monitoring  ·  SNID Nov-26','Two instruments agree on coverage, not on cause',false);",
    'slide6 kicker')

# ---------------------------------------------------------------- slide 8
rep("'Nov-26 readiness: '+p1(D.mpqPass)+' pass, '+n0(D.mpq[4])+' serious'",
    "'Dec-26 readiness: '+p1(D.mpqPass)+' pass, '+n0(D.mpq[4])+' serious'",
    'slide8 title')

# ---------------------------------------------------------------- slide 9
rep("'priority-1 UCs across the province. These should take the first supervisor visits of SNID Nov-26.'",
    "'priority-1 UCs across the province. These should take the first supervisor visits of NID Dec-26.'",
    'slide9 dec')

# ---------------------------------------------------------------- slide 10
rep("so a weak September round stalls the tracker into November.",
    "so a weak round stalls the tracker into December.",
    'slide10 dec')

# ---------------------------------------------------------------- slide 11
rep("s=base('Data quality  ·  before the round','Four gates stand between Nov-26 and a trusted total',true);",
    "s=base('Data quality  ·  before the December round','Four gates stand between Dec-26 and a trusted total',true);",
    'slide11 kicker')

# ---------------------------------------------------------------- slide 14
rep("""  [['Route Nov-26 supervision to the '+n0(D.h50)+' UCs holding half the missed children','EOC-KP with division coordinators','5 Nov','Coverage in those UCs at or above 70%'],
   ['Re-verify ZD coverage in the '+n0(D.blocker)+' UCs that cannot close','District closure focal points','10 Nov','Closed UCs above 20% (from '+p1(D.clPct)+')'],
   ['Clear the '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage and '+n0(D.ovn)+' over-covered UCs before totals are read','M&E and IDIMS cell','6 Nov','No UC outside the 50–110% band'],
   ['Move revisit windows to evenings and weekends in mobility districts','District health offices','From 2 Nov','Away-from-home share below 60%'],
   ['Put a female member on every monitoring team','District RHOs','Before deployment','MT with female member at or above 90%'],
   ['Clear the validation backlog on covered ZD children','Validation cell','20 Nov','60% validated (now '+p1(D.reg)+')']].forEach(function(r){""",
    """  [['Route Dec-26 supervision to the '+n0(D.h50)+' UCs holding half the missed children','EOC-KP with division coordinators','5 Dec','Coverage in those UCs at or above 70%'],
   ['Re-verify ZD coverage in the '+n0(D.blocker)+' UCs that cannot close','District closure focal points','10 Dec','Closed UCs above 20% (from '+p1(D.clPct)+')'],
   ['Clear the '+n0(D.old)+' stale, '+n0(D.z0n)+' zero-coverage and '+n0(D.ovn)+' over-covered UCs before totals are read','M&E and IDIMS cell','6 Dec','No UC outside the 50–110% band'],
   ['Move revisit windows to evenings and weekends in mobility districts','District health offices','From 12 Dec','Away-from-home share below 60%'],
   ['Put a female member on every monitoring team','District RHOs','Before deployment','MT with female member at or above 90%'],
   ['Clear the validation backlog on covered ZD children','Validation cell','20 Dec','60% validated (now '+p1(D.reg)+')']].forEach(function(r){""",
    'slide14 rows')

# ---------------------------------------------------------------- slide 15
rep("""  [['SCOPE','2026 only. January–September for routine EPI and surveillance, the three 2026 campaigns, and MPQA read at '+h(D.mpqAs)+'. No earlier year enters any figure.'],""",
    """  [['SCOPE','2026 only. January–September for routine EPI, the four 2026 campaigns through SNID Nov-26, surveillance, and MPQA read at '+h(D.mpqAs)+'. No earlier year enters any figure.'],""",
    'slide15 scope')
rep("""   ['CAVEAT','Sept-26 covered figures — '+n0(D.cov)+' / '+p1(D.covPct)+', '+n0(D.rollup)+', '+n0(D.net)+' — are the round\\'s own self-reported coverage export. They are not yet confirmed by a later round.'],""",
    """   ['CAVEAT','SNID Nov-26 has no covered figure yet: it is read on the '+n0(D.nTg)+' UC target, its LQAS, still-missed and validation returns. Sept-26 covered figures — '+n0(D.cov)+' / '+p1(D.covPct)+', '+n0(D.rollup)+', '+n0(D.net)+' — are the round\\'s own self-reported export.'],""",
    'slide15 caveat')
rep("""   ['DEFINITIONS','Not covered = reported − covered, per UC. '+n0(D.st)+' missed = 2026 gap analytics against administered doses. Like-for-like = the '+n0(D.nL3)+' UCs that reported in all three rounds.']]""",
    """   ['DEFINITIONS','Not covered = reported − covered, per UC. Still missed = not available + refused + left over, from the Nov-26 close-out. '+n0(D.st)+' missed = 2026 gap analytics against administered doses. Like-for-like = the '+n0(D.nL3)+' UCs that reported in all three rounds.']]""",
    'slide15 definitions')

# ---------------------------------------------------------------- checks
for gone in ['what November has to fix', 'SNID Nov-26, starting 2 November 2026',
             "'5 Nov'", "'10 Nov'", "'20 Nov'", "'From 2 Nov'", 'Route the Nov-26 supervision',
             'Route Nov-26 supervision', "'DECISIONS BEFORE 2 NOVEMBER'"]:
    assert gone not in s, f'leftover: {gone}'
for need in ['nStp', 'nDiv', 'NID Dec-26, starting 12 December 2026', 'still missed after SNID Nov-26']:
    assert need in s, f'missing: {need}'

out = s.replace('\n', '\r\n')
assert '\n' not in out.replace('\r\n', ''), 'lone LF in output'
assert out.count('\r\n') == s.count('\n')
open(PATH, 'w', encoding='utf-8', newline='').write(out)
print('patched', PATH, orig_len, '->', len(out))
