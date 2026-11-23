# -*- coding: utf-8 -*-
"""District monitor brief (A4 + 7 slides): add the SNID Nov-26 close-out per district
and re-anchor the actions to NID Dec-26 (starts 12 December 2026).
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

PATH = 'index.html'
raw = open(PATH, encoding='utf-8', newline='').read()
assert '\r\n' in raw, 'expected CRLF'
s = raw.replace('\r\n', '\n')
assert '\r' not in s, 'lone CR in source'
orig_len = len(s)


def rep(old, new, label, n=1):
    global s
    got = s.count(old)
    assert got == n, f'{label}: expected {n}, found {got}'
    s = s.replace(old, new, n)


# ---------------------------------------------------------------- pdNov()
rep("""/* ---------- the district fact object ---------- */""",
    """/* ---------- SNID Nov-26 close-out, per district (cached) ---------- */
var _PD_NOV=null;
function pdNov(){
  if(_PD_NOV) return _PD_NOV;
  var out={};
  function slot(k){return out[k]=out[k]||{tg:0,vac:0,sna:0,srf:0,slo:0,n:0,rep:0,ucs:0};}
  try{
    if(typeof NOVUC!=='undefined'&&NOVUC&&NOVUC.k&&NOVUC.r){
      var nb={}; NOVUC.k.forEach(function(k,i){nb[k]=i;});
      NOVUC.r.forEach(function(t){var g=slot(normU(t[nb.d]));g.tg+=t[nb.tg]||0;g.vac+=t[nb.vac]||0;g.sna+=t[nb.sna]||0;g.srf+=t[nb.srf]||0;g.slo+=t[nb.slo]||0;g.n++;});
    }
    if(typeof novRows==='function'){
      novRows().forEach(function(r){var g=slot(normU(r.d));g.rep+=r.rN||0;g.ucs++;});
    }
  }catch(e){}
  Object.keys(out).forEach(function(k){var g=out[k];g.pct=pct_(g.vac,g.tg);g.st=g.sna+g.srf+g.slo;g.stp=pct_(g.st,g.tg);});
  _PD_NOV=out; return out;
}

/* ---------- the district fact object ---------- */""",
    'pdNov')

# ---------------------------------------------------------------- pdFacts
rep("""  var rows=ZD.filter(function(r){return r.d===dist;});
  if(!rows.length) return null;
  var div=rows[0].dv||'', P_=pdProv();""",
    """  var rows=ZD.filter(function(r){return r.d===dist;});
  if(!rows.length) return null;
  var div=rows[0].dv||'', P_=pdProv();
  var nov=pdNov()[normU(dist)]||null;""",
    'pdFacts nov')

rep("""  var D={dist:dist,div:div,stamp:stamp_(),sepLbl:sepLbl,camp:sepLbl,li:li,""",
    """  var nvr=VAL.filter(function(r){return r.d===dist&&/nov/i.test(String(r.cp||''));});
  var nval={n:sum_(nvr,function(r){return r.n;}),vy:sum_(nvr,function(r){return r.vy;}),f:sum_(nvr,function(r){return r.f;}),
    u:(function(){var s={};nvr.forEach(function(r){s[r.c]=1;});return Object.keys(s).length;})()};
  nval.p=pct_(nval.vy,nval.n);

  var D={dist:dist,div:div,stamp:stamp_(),sepLbl:sepLbl,camp:sepLbl,li:li,nov:nov,nval:nval,""",
    'pdFacts nval')

# ---------------------------------------------------------------- caveat
rep("""var CAV='Caveat: Sept-26 covered figures are the round\\'s own self-reported coverage export, not confirmed by a later round.';""",
    """var CAV='Caveat: SNID Nov-26 has no covered figure yet — its coverage is read on the UC target, with LQAS, still-missed and validation returns. Sept-26 coverage is the round\\'s own self-reported export, not confirmed.';""",
    'CAV')

# ---------------------------------------------------------------- standing
rep("""function standing(D){
  if(D.frozenAll&&D.both>=5)
    return 'Every number below is '+D.nm+'’s own. The district enters November with '+N(D.rep)+' zero-dose children reported in September — '+yearPhrase(D)+' — and a covered column that has not moved since May.';
  if(!D.both)
    return 'Every number below is '+D.nm+'’s own. The district carries no May-26 covered figure, so September stands alone: '+N(D.rep)+' children reported and '+N(D.cov)+' covered in the round\\'s own export.';
  return 'Every number below is '+D.nm+'’s own. September coverage is '+P1(D.pct)+', against '+P1(D.M.pct)+' in May on the '+D.both+' UCs that carry a figure in both rounds.';
}""",
    """function standing(D){
  var nvS=D.nov?(' SNID Nov-26 has closed: '+N(D.nov.rep)+' children recorded and '+P1(D.nov.pct)+' of the UC target vaccinated, '+N(D.nov.st)+' still missed.'):' No SNID Nov-26 UC record is loaded for this district.';
  if(D.frozenAll&&D.both>=5)
    return 'Every number below is '+D.nm+'’s own. The district went into the November round with '+N(D.rep)+' zero-dose children reported in September — '+yearPhrase(D)+' — and a covered column that has not moved since May.'+nvS;
  if(!D.both)
    return 'Every number below is '+D.nm+'’s own. The district carries no May-26 covered figure, so September stands alone: '+N(D.rep)+' children reported and '+N(D.cov)+' covered in the round\\'s own export.'+nvS;
  return 'Every number below is '+D.nm+'’s own. September coverage was '+P1(D.pct)+', against '+P1(D.M.pct)+' in May on the '+D.both+' UCs that carry a figure in both rounds.'+nvS;
}""",
    'standing')

rep("'The November round is the first chance to establish a covered figure that a later round can confirm.'",
    "'The December round is the first chance to establish a covered figure that a later round can confirm.'",
    'register December')

# ---------------------------------------------------------------- novNote
rep("""function inRound(D){ return D.ucs-D.noCamp.length; }""",
    """function inRound(D){ return D.ucs-D.noCamp.length; }
function novNote(D){
  var nv=D.nov;
  if(!nv) return 'No SNID Nov-26 UC record is loaded for this district, so the November close-out cannot be read here.';
  return 'SNID Nov-26 close-out: '+N(nv.rep)+' zero-dose children recorded across '+N(nv.n)+' UCs; '+N(nv.vac)+' vaccinated against a '+N(nv.tg)+' UC target ('+P1(nv.pct)+'), leaving '+N(nv.st)+' still missed — '+N(nv.srf)+' refused, '+N(nv.sna)+' not available, '+N(nv.slo)+' left over. The covered figure is awaited.';
}""",
    'novNote')

# ---------------------------------------------------------------- kpiData
rep("""function kpiData(D){
  var pv=D.prov, k=[];
  k.push({v:N(inRound(D))+' of '+N(D.ucs),l:'union councils delivered the September round',c:D.noCamp.length?'warn':''});
  k.push({v:N(D.rep),l:'children found with no vaccine — '+yearPhrase(D),c:''});
  if(D.frozenAll&&D.both) k.push({v:D.frozen+' of '+D.both,l:'UCs carrying May’s covered figure into September',c:'bad'});
  else if(D.pct!=null) k.push({v:P1(D.pct),l:'covered as recorded — '+N(D.cov)+' of '+N(D.recRep),c:D.pct>=70?'':(D.pct>110?'bad':'warn')});
  else k.push({v:'–',l:'no covered figure reported for this district',c:'warn'});
  if(D.icm&&D.icm.recall!=null) k.push({v:P1(D.icm.recall),l:'ICM recall — '+N(D.icm.rc)+' children checked, province '+P1(pv.recall),c:D.icm.recall>=pv.recall?'':'warn'});
  else k.push({v:'–',l:'no September ICM return for this district',c:'warn'});
  if(D.lq.n) k.push({v:P1(D.lq.pass),l:'LQAS lots passed — '+D.lq.P+' of '+D.lq.n+' drawn, '+D.lq.F+' failed',c:D.lq.pass>=80?'':'warn'});
  else k.push({v:'–',l:'no LQAS lot returned for this district',c:'warn'});
  return k;
}""",
    """function kpiData(D){
  var pv=D.prov, k=[], nv=D.nov;
  k.push(nv?{v:N(nv.rep),l:'zero-dose children recorded in SNID Nov-26 across '+N(nv.n)+' UCs',c:''}
            :{v:'–',l:'no SNID Nov-26 UC record for this district',c:'warn'});
  k.push(nv&&nv.pct!=null?{v:P1(nv.pct),l:N(nv.vac)+' vaccinated of the '+N(nv.tg)+' UC target — '+N(nv.st)+' still missed after catch-up',c:nv.pct>=90?'':(nv.pct<80?'bad':'warn')}
            :{v:'–',l:'no UC target reported for SNID Nov-26',c:'warn'});
  k.push({v:N(inRound(D))+' of '+N(D.ucs),l:'union councils delivered the September round',c:D.noCamp.length?'warn':''});
  if(D.frozenAll&&D.both) k.push({v:D.frozen+' of '+D.both,l:'UCs carrying May’s covered figure into September',c:'bad'});
  else if(D.pct!=null) k.push({v:P1(D.pct),l:'Sept-26 covered as recorded — '+N(D.cov)+' of '+N(D.recRep),c:D.pct>=70?'':(D.pct>110?'bad':'warn')});
  else k.push({v:'–',l:'no September covered figure for this district',c:'warn'});
  if(D.icm&&D.icm.recall!=null) k.push({v:P1(D.icm.recall),l:'Sept-26 ICM recall — '+N(D.icm.rc)+' children checked, province '+P1(pv.recall),c:D.icm.recall>=pv.recall?'':'warn'});
  else k.push({v:'–',l:'no September ICM return for this district',c:'warn'});
  if(D.lq.n) k.push({v:P1(D.lq.pass),l:'Sept-26 LQAS lots passed — '+D.lq.P+' of '+D.lq.n+' drawn, '+D.lq.F+' failed',c:D.lq.pass>=80?'':'warn'});
  else k.push({v:'–',l:'no September LQAS lot returned for this district',c:'warn'});
  return k;
}""",
    'kpiData')

# ---------------------------------------------------------------- roundsHtml
rep("""function roundsHtml(D){
  var rows=[['Apr-26',D.A],['May-26',D.M],['Sept-26',D.S]];
  return rows.map(function(r,i){
    var v=r[1], p=v.pct, has=v.cov!=null&&v.rep!=null&&(v.rep>0||v.cov>0);
    var col=p==null?'#b8442f':(p>=70?'#2f7d6d':p>=55?'#d9822b':'#b8442f');
    return '<div class="rb-round"><div class="rh"><span>'+r[0]+'</span><b>'+P1(p)+'</b></div>'+
      '<div class="rb-track"><i style="width:'+Math.max(2,Math.min(100,p||0))+'%;background:'+col+'"></i></div>'+
      '<div class="rf">'+(has?N(v.cov)+' covered of '+N(v.rep)+' reported':'no covered figure for this round')+'</div></div>';
  }).join('');
}""",
    """function roundsHtml(D){
  var rows=[['Apr-26',D.A,null],['May-26',D.M,null],['Sept-26',D.S,null]];
  if(D.nov) rows.push(['Nov-26',{rep:D.nov.rep,cov:D.nov.vac,pct:D.nov.pct},D.nov]);
  return rows.map(function(r,i){
    var v=r[1], nv=r[2], p=v.pct, has=v.cov!=null&&v.rep!=null&&(v.rep>0||v.cov>0);
    var col=p==null?'#b8442f':(p>=70?'#2f7d6d':p>=55?'#d9822b':'#b8442f');
    return '<div class="rb-round"><div class="rh"><span>'+r[0]+'</span><b>'+P1(p)+'</b></div>'+
      '<div class="rb-track"><i style="width:'+Math.max(2,Math.min(100,p||0))+'%;background:'+col+'"></i></div>'+
      '<div class="rf">'+(nv?(N(nv.vac)+' vaccinated of '+N(nv.tg)+' UC target'):(has?N(v.cov)+' covered of '+N(v.rep)+' reported':'no covered figure for this round'))+'</div></div>';
  }).join('');
}""",
    'roundsHtml')

# ---------------------------------------------------------------- valText
rep("""function valText(D){
  var v=D.val;
  if(!v.n) return 'No zero-dose validation records have been entered for this district.';
  return N(v.n)+' children shown as covered were validated across the 2026 campaigns: '+N(v.vy)+' confirmed vaccinated'+(v.vn?(', '+N(v.vn)+' not confirmed'):'')+', across '+v.u+' UCs.';
}""",
    """function valText(D){
  var v=D.val, nv=D.nval||{n:0};
  if(!v.n&&!nv.n) return 'No zero-dose validation records have been entered for this district.';
  var out=v.n?(N(v.n)+' children shown as covered were validated across the 2026 campaigns: '+N(v.vy)+' confirmed vaccinated'+(v.vn?(', '+N(v.vn)+' not confirmed'):'')+', across '+v.u+' UCs.'):'';
  return out+(nv.n?(' SNID Nov-26 so far: '+N(nv.n)+' children on '+N(nv.f)+' forms, '+P1(nv.p)+' confirmed.'):' No SNID Nov-26 validation record yet.');
}""",
    'valText')

# ---------------------------------------------------------------- sheet section 1
rep("""  '<div class="rb-sec"><div class="rb-h">1 · Campaign performance, SNID Sept-26</div><div class="rb-rounds">'+roundsHtml(D)+'</div>'+
  '<div class="pd-note" style="margin-top:1.5mm">'+H(campNote(D))+'</div>'+""",
    """  '<div class="rb-sec"><div class="rb-h">1 · Campaign performance, SNID Sept-26 and Nov-26</div><div class="rb-rounds">'+roundsHtml(D)+'</div>'+
  '<div class="pd-note" style="margin-top:1.2mm">'+H(novNote(D))+'</div>'+
  '<div class="pd-note" style="margin-top:.8mm">'+H(campNote(D))+'</div>'+""",
    'sheet section 1')

# ---------------------------------------------------------------- sheet footer
rep("""'<div class="rb-foot"><span>District monitor brief · '+H(D.nm)+' · SNID Nov-26 starts 2 Nov 2026</span><span>page 1 of 1 · regenerated from the dashboard</span></div>';""",
    """'<div class="rb-foot"><span>District monitor brief · '+H(D.nm)+' · NID Dec-26 starts 12 Dec 2026</span><span>page 1 of 1 · regenerated from the dashboard</span></div>';""",
    'sheet footer')

# ---------------------------------------------------------------- sources
rep("""ICM, LQAS, MPQA, HRA, NEAP, routine EPI and AFP are the dashboard\\'s own roll-up of the 2026 exports; validation counts every 2026 campaign.""",
    """ICM, LQAS, MPQA, HRA, NEAP, routine EPI and AFP are the dashboard\\'s own roll-up of the 2026 exports; the SNID Nov-26 close-out is the UC-wise table\\'s own record and target; validation counts every 2026 campaign.""",
    'sources')

# ---------------------------------------------------------------- actions
rep("w:'3 & 5 Nov'", "w:'14 & 16 Dec'", 'a: 3 & 5 Nov')
rep("w:'2 Nov'", "w:'10 Dec'", 'a: 2 Nov', 4)
rep("w:'Before 2 Nov'", "w:'Before 12 Dec'", 'a: Before 2 Nov', 3)
rep("w:'7 Nov'", "w:'17 Dec'", 'a: 7 Nov')
rep("w:'By 20 Nov'", "w:'By 20 Dec'", 'a: By 20 Nov', 2)
rep("w:'4 Nov'", "w:'14 Dec'", 'a: 4 Nov', 4)
rep("w:'6 Nov'", "w:'16 Dec'", 'a: 6 Nov', 2)
rep("Every UC reads out its own November covered count. The district stops accepting a carried-forward figure.",
    "Every UC reads out its own December covered count. The district stops accepting a carried-forward figure.",
    'a: November covered count')
rep("'Fix the covered count before the November round starts'", "'Fix the covered count before the December round starts'", 'a: November round starts')
rep("'Make government-accountable staffing a condition of the November micro-plan'",
    "'Make government-accountable staffing a condition of the December micro-plan'", 'a: November micro-plan gov')
rep("'Protect the female share of the team in the November micro-plan'",
    "'Protect the female share of the team in the December micro-plan'", 'a: November micro-plan fem')
rep("sets the November result.", "sets the December result.", 'a: November result')
rep("'Hold Penta-3 and MR-2 above the provincial line through November'",
    "'Hold Penta-3 and MR-2 above the provincial line through December'", 'a: through November')
rep("'Run the September recall check in the watch UCs'", "'Run the recall check in the watch UCs'", 'a: September recall check')
rep("b:'The district is outside the November MPQA sample, so the quality of its micro-plan cannot be benchmarked.'",
    "b:'The district is outside the current MPQA sample, so the quality of its micro-plan cannot be benchmarked.'",
    'a: MPQA sample prose')

# ---------------------------------------------------------------- deck
rep("p.title=D.nm+' — district monitor brief, SNID Nov-26';", "p.title=D.nm+' — district monitor brief, NID Dec-26';", 'deck title')
rep("s.addText(D.nm+' before SNID Nov-26',", "s.addText(D.nm+' before NID Dec-26',", 'cover title')
rep("""  chips.push([N(D.rep),'children found with no vaccine, Sept-26']);
  chips.push([inRound(D)+' / '+D.ucs,'union councils delivered the round']);
  if(D.icm&&D.icm.recall!=null) chips.push([P1(D.icm.recall),'ICM recall — province '+P1(D.prov.recall)]);""",
    """  chips.push([N(D.nov?D.nov.rep:null),'zero-dose children recorded in SNID Nov-26']);
  chips.push([D.nov?P1(D.nov.pct):'–','of the '+N(D.nov?D.nov.tg:null)+' UC target vaccinated — '+N(D.nov?D.nov.st:null)+' still missed']);
  if(D.icm&&D.icm.recall!=null) chips.push([P1(D.icm.recall),'Sept-26 ICM recall — province '+P1(D.prov.recall)]);""",
    'cover chips')

rep("""s=base('Campaign performance · SNID Sept-26',D.nm+'’s September round, in its own numbers',
    inRound(D)+' of '+D.ucs+' UCs delivered the round'+(D.noCamp.length?(' and '+D.noCamp.length+' did not'):'')+'; '+N(D.rep)+' children were found with no vaccine.',true);""",
    """s=base('Campaign performance · Sept and Nov 2026',D.nm+'’s campaign year, in its own numbers',
    inRound(D)+' of '+D.ucs+' UCs delivered the September round'+(D.noCamp.length?(' and '+D.noCamp.length+' did not'):'')+'; '+N(D.rep)+' children were found with no vaccine then, and '+N(D.nov?D.nov.rep:null)+' were recorded in SNID Nov-26.',true);""",
    'slide2 head')

rep("""  [['Apr-26',D.A],['May-26',D.M],['Sept-26',D.S]].forEach(function(r,i){ var v=r[1], x=M+i*4.06, has=v.cov!=null&&v.rep!=null&&(v.rep>0||v.cov>0);
    card(s,x,yy2,3.86,0.92);
    s.addText(r[0],{x:x+0.22,y:yy2+0.08,w:1.6,h:0.22,fontSize:8,bold:true,color:C.pri,fontFace:FF});
    s.addText(P1(v.pct),{x:x+0.22,y:yy2+0.30,w:1.6,h:0.34,fontSize:16,bold:true,color:i===2&&D.frozenAll&&D.both?C.red:C.ink,fontFace:FF,fit:'shrink'});
    s.addText(has?N(v.cov)+' covered of '+N(v.rep)+' reported':'no covered figure for this round',{x:x+1.90,y:yy2+0.32,w:1.80,h:0.44,fontSize:7.8,color:C.mut,fontFace:FF,lineSpacingMultiple:1.1,fit:'shrink'});
  });""",
    """  var cyRows=[['Apr-26',D.A,null],['May-26',D.M,null],['Sept-26',D.S,null]];
  if(D.nov) cyRows.push(['Nov-26',{rep:D.nov.rep,cov:D.nov.vac,pct:D.nov.pct},D.nov]);
  var cwid=(CW-3*0.14)/4;
  cyRows.forEach(function(r,i){ var v=r[1], nv=r[2], x=M+i*(cwid+0.14), has=v.cov!=null&&v.rep!=null&&(v.rep>0||v.cov>0);
    card(s,x,yy2,cwid,0.92);
    s.addText(r[0],{x:x+0.18,y:yy2+0.08,w:1.2,h:0.22,fontSize:8,bold:true,color:C.pri,fontFace:FF});
    s.addText(P1(v.pct),{x:x+0.18,y:yy2+0.29,w:1.35,h:0.34,fontSize:15,bold:true,color:(!nv&&i===2&&D.frozenAll&&D.both)?C.red:C.ink,fontFace:FF,fit:'shrink'});
    s.addText(nv?(N(nv.vac)+' vaccinated of '+N(nv.tg)+' target'):(has?N(v.cov)+' covered of '+N(v.rep)+' reported':'no covered figure for this round'),{x:x+1.55,y:yy2+0.31,w:cwid-1.63,h:0.46,fontSize:7.2,color:C.mut,fontFace:FF,lineSpacingMultiple:1.1,fit:'shrink'});
  });""",
    'slide2 year cards')

rep("s.addText('READINESS FOR NOVEMBER',", "s.addText('READINESS FOR DECEMBER',", 'slide3 readiness')
rep("s=base('Routine EPI · Jan–Sep 2026','Routine coverage carries the November round',null,false);",
    "s=base('Routine EPI · Jan–Sep 2026','Routine coverage carries the December round',null,false);",
    'slide5 subtitle')
rep("D.frozenAll&&D.both?'The first act is a register review: the district needs its own November covered count, not a carried-forward one.'",
    "D.frozenAll&&D.both?'The first act is a register review: the district needs its own December covered count, not a carried-forward one.'",
    'slide7 subtitle')
rep("'_SNID_Nov26_Brief_'", "'_NID_Dec26_Brief_'", 'deck filename')

# ---------------------------------------------------------------- checks
for gone in ["'3 & 5 Nov'", "w:'2 Nov'", "w:'Before 2 Nov'", "w:'7 Nov'", "w:'By 20 Nov'", "w:'4 Nov'", "w:'6 Nov'",
             'SNID Nov-26 starts 2 Nov 2026', 'READINESS FOR NOVEMBER', '_SNID_Nov26_Brief_',
             'before SNID Nov-26', 'carries the November round']:
    assert gone not in s, f'leftover: {gone}'
for need in ['function pdNov', 'novNote', 'D.nov', 'NID Dec-26 starts 12 Dec 2026', 'READINESS FOR DECEMBER']:
    assert need in s, f'missing: {need}'

out = s.replace('\n', '\r\n')
assert '\n' not in out.replace('\r\n', ''), 'lone LF in output'
assert out.count('\r\n') == s.count('\n')
open(PATH, 'w', encoding='utf-8', newline='').write(out)
print('patched', PATH, orig_len, '->', len(out))
