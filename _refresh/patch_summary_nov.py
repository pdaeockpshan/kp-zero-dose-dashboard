# -*- coding: utf-8 -*-
"""Summary tab: lead the campaign comparisons with SNID Nov-26.

Edits the master only (index.html, CRLF). Every anchor is asserted exactly once
before anything is written; the file is written once, at the end, from memory.
Markup and the CSV handler are edited globally; the renderSummary body is sliced
out first so marker searches cannot match the same comment in another renderer.
"""
import sys

sys.stdout.reconfigure(encoding='utf-8')

PATH = 'index.html'
s = open(PATH, encoding='utf-8', newline='').read()
orig_len = len(s)
assert '\r\n' in s and '\n\n' not in s.replace('\r\n', ''), 'expected a CRLF-only file'


def crlf(t):
    t = t.replace('\r\n', '\n').replace('\n', '\r\n')
    assert '\r' not in t.replace('\r\n', ''), 'lone CR in replacement'
    return t


def rep(st, old, new, label):
    n = st.count(old)
    assert n == 1, f'{label}: anchor found {n} times'
    return st.replace(old, crlf(new), 1)


def rep_line(st, prefix, newline_text, label):
    starts = []
    i = 0
    while True:
        j = st.find(prefix, i)
        if j < 0:
            break
        starts.append(j)
        i = j + 1
    assert len(starts) == 1, f'{label}: line prefix found {len(starts)} times'
    a = starts[0]
    b = st.find('\r\n', a)
    assert b > a, label
    return st[:a] + crlf(newline_text) + st[b:]


def rep_seg(st, a_marker, b_marker, newtext, label):
    assert st.count(a_marker) == 1, f'{label}: start marker count {st.count(a_marker)}'
    ia = st.find(a_marker)
    ib = st.find(b_marker, ia + len(a_marker))
    assert ib > ia, label
    return st[:ia] + crlf(newtext) + st[ib:]


def ins_before(st, anchor, text, label):
    assert st.count(anchor) == 1, f'{label}: anchor count {st.count(anchor)}'
    i = st.find(anchor)
    return st[:i] + crlf(text) + st[i:]


# ---------------------------------------------------------------- markup
s = rep(s, '<span class="cnt">NID Apr-26 · SNID May-26 · SNID Sept-26 · coverage % = covered ÷ reported</span>',
        '<span class="cnt">NID Apr-26 · SNID May-26 · SNID Sept-26 · SNID Nov-26 recorded · coverage % = covered ÷ reported</span>',
        's1 header')

s = rep(s, '<div class="card"><div class="kl">ZD covered · latest campaign</div>',
        '<div class="card"><div class="kl">ZD covered · Sept-26 (last measured)</div>',
        's1b label')

s = rep(s, '<div class="card"><div class="kl">Children not covered · latest</div>',
        '<div class="card"><div class="kl">Children not covered · Sept-26</div>',
        's1d label')

s = rep(s, '<div class="card"><div class="kl">Coverage % · like-for-like UCs</div><div class="kv" id="s1c"',
        '<div class="card"><div class="kl">Coverage % · like-for-like (to Sept-26)</div><div class="kv" id="s1c"',
        's1c label')

s = rep(s, '<span class="cnt">SNID Sept 2026 · linelist entered ÷ IDIMS reported · 9 districts</span>',
        '<span class="cnt">SNID Sept 2026 (last digitized round) · linelist entered ÷ IDIMS reported · 9 districts · SNID Nov-26 digitization return awaited</span>',
        's2 header')

s = rep(s, '<span class="cnt">SNID Sept-26 · SNID May-26 · NID Apr-26 · latest campaign per UC</span>',
        '<span class="cnt">SNID Nov-26 close-out · SNID Sept-26 for the trend · UC-target basis</span>',
        's5 header')

s = rep(s, '<div class="card"><div class="kl">Campaign coverage</div><div class="kv" id="s5a">',
        '<div class="card"><div class="kl">Campaign coverage · SNID Nov-26</div><div class="kv" id="s5a">',
        's5a label')

s = rep(s, '<div class="card"><div class="kl">Coverage trend</div>',
        '<div class="card"><div class="kl">Coverage trend · Sept → Nov</div>',
        's5b label')

s = rep(s, '<div class="cap">Click a district to filter all tabs to it. Coverage uses the latest campaign with coverage (May, or April where May did not run). Digitization covers only the 9 districts in the IDIMS comparison report ("–" elsewhere). Validation includes all validation campaigns.</div>',
        '<div class="cap">Click a district to filter all tabs to it. Coverage % is SNID Sept-26, the latest campaign with a covered figure; the Nov column is the SNID Nov-26 UC-wise recorded return, whose covered figure is awaited. Digitization covers only the 9 districts in the IDIMS comparison report ("–" elsewhere). Validation includes all validation campaigns.</div>',
        'table caption')

# ---------------------------------------------------------------- renderSummary slice
A = 'function renderSummary(){'
B = 'let SUMROWS=[];'
ia = s.find(A)
assert ia > 0 and s.count(A) == 1
ib = s.find(B, ia)
assert ib > ia and s.count(B) == 1
head, sl, tail = s[:ia], s[ia:ib], s[ib:]

# ---- section 1
S1 = ''' // 1. reported & covered
 const nv1=(typeof novSum==='function')?novSum():{n:0,rep:0,dists:0};
 el('s1a').innerHTML=`${fmt(z.rA)}<small> → </small>${fmt(z.rM)}`+(ZSAME?'':`<small> → </small>${fmt(z.rS)}`)+(nv1.rep?`<small> → </small><span style="color:#0f766e">${fmt(nv1.rep)}</span>`:'');
 el('s1as').textContent=`Apr ${z.nA} · May ${z.nM}`+(ZSAME?'':` · Sept ${z.nS} UCs`)+(nv1.rep?` · Nov ${fmt(nv1.n)} UCs recorded`:'');
 el('s1b').textContent=fmt(z['c'+LCP]); el('s1bs').textContent=`of ${fmt(z['rc'+LCP])} reported in ${CAMP[LCP]} UCs with coverage data · Sept-26 is the last measured round, its own covered export not yet confirmed by a later round · SNID Nov-26 covered figure awaited`;
 el('s1c').innerHTML=SCOV?`${pc(z.lf3A)}<small> → </small>${pc(z.lf3S)}`:`${pc(z.lfA)}<small> → </small>${pc(z.lfM)}`; el('s1c').style.color=colCov(SCOV?z.lf3S:z.lfM);
 const dd=SCOV?((z.lf3A!=null&&z.lf3S!=null)?z.lf3S-z.lf3A:null):((z.lfA!=null&&z.lfM!=null)?z.lfM-z.lfA:null);
 el('s1cs').innerHTML=dd==null?'No UCs with coverage in all campaigns':`<span class="${dd>=0?'up':'dn'}">${dd>=0?'▲ +':'▼ '}${dd.toFixed(1)} pts</span> · ${SCOV?z.nL3:z.nL} UCs like-for-like · Nov-26 coverage awaited`;
 el('s1d').textContent=fmt(gapNet(z,LCP)); el('s1ds').textContent=`reported − covered in ${fmt(z['nc'+LCP])} ${CAMP[LCP]} UCs with coverage · ${fmt(z['cr'+LCP])} below 50% · Nov-26 coverage awaited`;
 el('s1e').textContent=zR.filter(r=>r.tr==='Persistent low').length;
'''
sl = rep_seg(sl, ' // 1. reported & covered', ' // 2. digitization', S1, 'section 1')

# ---- section 4 header
sl = rep_line(sl, ' const eR=EPI.filter(matchE), e4=aggE(eR);',
              ''' const eR=EPI.filter(matchE), e4=aggE(eR);
 if(el('s4h'))el('s4h').textContent=(EPER?EPER+' · ':'')+'KP EPI-MIS · doses ÷ target';''',
              'section 4 header')

# ---- section 5
S5 = ''' // 5. campaigns — coverage & missed children (SNID Nov-26 close-out; Sept-26 for the trend)
 const cps5=(MISM.camps||[]), CP5=cps5.map(l=>({l,n:0,tg:0,vc:0,rec:0,st:0,srf:0,sna:0}));
 misHyd().forEach(r=>{ if(!r.d||!matchG(r))return; const c=CP5[r.ci]; if(!c)return; c.n++; c.tg+=r.tg||0; c.vc+=r.vc||0; c.rec+=(r.rna||0)+(r.rrf||0); c.st+=misSt(r); c.srf+=r.srf||0; c.sna+=r.sna||0;});
 const cN5=CP5[0]||{l:cps5[0]||''};
 const cov5=c=>c.tg?c.vc/c.tg*100:null;
 const NB={}; ((typeof NOVUC!=='undefined'&&NOVUC&&NOVUC.k)||[]).forEach((k,i)=>NB[k]=i);
 const NU=((typeof NOVUC!=='undefined'&&NOVUC&&NOVUC.r)||[]).map(t=>({dv:t[NB.dv],d:t[NB.d],t:t[NB.t],u:t[NB.u],c:t[NB.c],tg:t[NB.tg]||0,vac:t[NB.vac]||0,sna:t[NB.sna]||0,srf:t[NB.srf]||0,slo:t[NB.slo]||0})).filter(matchG);
 const nTg=S_(NU,r=>r.tg), nVac=S_(NU,r=>r.vac), nSna=S_(NU,r=>r.sna), nSrf=S_(NU,r=>r.srf), nSlo=S_(NU,r=>r.slo), nSt=nSna+nSrf+nSlo;
 const nCov=nTg?nVac/nTg*100:null, nStp=nTg?nSt/nTg*100:null;
 const nU5=NU.filter(r=>r.tg&&(r.sna+r.srf+r.slo)/r.tg*100>=5).length, nU3=NU.filter(r=>r.tg&&(r.sna+r.srf+r.slo)/r.tg*100>=3).length;
 const nHh=(typeof NOVF!=='undefined'&&NOVF&&NOVF.tot)?NOVF.tot[0]:null;
 const nRec=(!fTeh.value&&!fUC.value&&!(typeof UCSEL!=='undefined'&&UCSEL&&UCSEL.size))?(()=>{const KF={}; ((typeof NOVF!=='undefined'&&NOVF&&NOVF.k)||[]).forEach((k,i)=>KF[k]=i); let rec=0,sna=0,srf=0,n=0;
  ((typeof NOVF!=='undefined'&&NOVF&&NOVF.u)||[]).forEach(t=>{if(!dvOK(t[KF.div])||!dOK(t[KF.d]))return; rec+=t[KF.rec]||0; sna+=t[KF.sna]||0; srf+=t[KF.srf]||0; n++;});
  return n&&rec?{rec,recov:Math.max(0,rec-sna-srf)/rec*100}:null;})():null;
 if(nTg){
  const s5=cov5(cN5), d59=s5!=null?nCov-s5:null;
  el('s5a').textContent=pc(nCov); el('s5a').style.color=colCov(nCov);
  el('s5as').textContent=`${fmt(nVac)} vaccinated of the ${fmt(nTg)} UC target · ${fmt(NU.length)} UCs · ${novLabel()} UC-wise table`;
  el('s5b').innerHTML=s5==null?'–':`${pc(s5)} → ${pc(nCov)}`; el('s5b').style.color=colCov(nCov);
  el('s5bs').innerHTML=d59==null?'UC sets differ between rounds':`<span class="${d59>=0?'up':'dn'}">${d59>=0?'▲ +':'▼ '}${d59.toFixed(1)} pts</span> · ${cN5.l} → ${novLabel()} · same UC-target basis, ${fmt(cN5.n)} vs ${fmt(NU.length)} UCs`;
  el('s5c').textContent=fmt(nSt); el('s5c').style.color=nStp>=3?C.crit:nStp>0?C.mod:'';
  el('s5cs').textContent=`${pc(nStp)} of the UC target${nHh?' · '+pc(nSt/nHh*100)+' of the '+fmt(nHh)+' household target':''} · ${fmt(nSrf)} refused · ${fmt(nSna)} not available · ${fmt(nSlo)} left over`;
  el('s5d').textContent=nRec?pc(nRec.recov):'–';
  el('s5ds').textContent=nRec?`of ${fmt(nRec.rec)} children recorded missed · ${novLabel()} close-out`:'close-out is district grain; clear the tehsil/UC filter to see it';
  el('s5e').textContent=fmt(nU5); el('s5es').textContent=`${fmt(nU3)} at 3%+ · UC-target basis · ${novLabel()} only`;
 }else{['s5a','s5b','s5c','s5d','s5e'].forEach(i=>{el(i).textContent='–';el(i).style.color='';});el('s5as').textContent='No SNID Nov-26 UC in this selection';['s5bs','s5cs','s5ds','s5es'].forEach(i=>el(i).textContent='');}
'''
sl = rep_seg(sl, ' // 5. campaigns', ' // 6. AFP surveillance', S5, 'section 5')

# ---- chart 1
CH1 = ''' // chart 1: reported, covered, validated by campaign (SNID Nov-26 recorded; covered return awaited)
 const vby=cp=>{const l=VCAMP.filter(x=>x.z===cp).map(x=>x.l);return l.length?S_(vR.filter(r=>l.includes(r.cp)),r=>r.n):null;};
 const vNovR=vR.filter(r=>/nov/i.test(String(r.cp||''))), vNovN=vNovR.length?S_(vNovR,r=>r.n):null, vNovF=vNovR.length?S_(vNovR,r=>r.f):null;
 const cats1=nv1.rep?CATS.concat('SNID Nov-26'):CATS;
 HC('cs1',{chart:{type:'column'},title:{text:'Zero-dose children reported, covered and validated'},subtitle:{text:'By campaign · validation is a sample check of covered children · Nov-26 covered figure awaited'},
  xAxis:{categories:cats1},yAxis:{title:{text:'Zero-dose children (count)'}},tooltip:{shared:true},
  plotOptions:{column:{borderRadius:3,groupPadding:.1,dataLabels:{...dl,format:'{y:,.0f}'}}},
  series:[{name:'ZD reported',color:'#0f766e',data:CPS.map(cp=>z['r'+cp]).concat(nv1.rep?[nv1.rep]:[])},
   {name:'ZD covered',color:'#5eead4',data:CPS.map(cp=>z['nc'+cp]?z['c'+cp]:null).concat(nv1.rep?[null]:[])},
   {name:'Children validated',color:'#15803d',data:CPS.map(cp=>vby(cp)).concat(nv1.rep?[vNovN]:[])}]});
 const vA=vby('A'), vM=vby('M'), vS=vby('S');
 el('caps1').textContent=(nv1.rep?`SNID Nov-26 recorded ${fmt(nv1.rep)} zero-dose children in ${fmt(nv1.n)} UCs; its covered figure is the post-campaign return awaited${vNovN?' and '+fmt(vNovN)+' Nov-26 children on '+fmt(vNovF)+' forms have been validated':''}. `:'')+`${SCOV?'':'Sept coverage is not reported yet. '}Validators re-checked ${vA==null?'–':fmt(vA)} children in April, ${vM==null?'–':fmt(vM)} in May${vS!=null?` and ${fmt(vS)} in Sept`:''}. `+(VCAMP.filter(x=>!x.z).length?`Other validation campaigns (${VCAMP.filter(x=>!x.z).map(x=>x.l).join(', ')}) have no matching reported/covered campaign.`:'');
'''
sl = rep_seg(sl, ' // chart 1:', ' // chart 2:', CH1, 'chart 1')

# ---- rowsS: Nov recorded per key
old_rows = 'return {k,dv:(zR.find(r=>r[L.key]===k)||vR.find(r=>r[L.key]===k)||d2[0]||{}).dv,zrs:'
assert sl.count(old_rows) == 1, f'rowsS anchor {sl.count(old_rows)}'
sl = sl.replace(old_rows, crlf("return {k,znv:(()=>{const w=novRows().filter(r=>r[L.key]===k&&matchG(r));return w.length?S_(w,r=>r.rN):null;})(),dv:(zR.find(r=>r[L.key]===k)||vR.find(r=>r[L.key]===k)||d2[0]||{}).dv,zrs:"), 1)

# ---- table
TBL = ''' // table
 el('sTblT').textContent=`All indicators by ${L.lvl}`; el('cntS').textContent=rowsS.length+' '+L.pl;
 const nn=(k,l,f)=>({k,l,n:1,f});
 drawTable('tSum',[{k:'k',l:L.Lvl,f:x=>L.key==='d'?`<button class="lnk" data-sd="${esc(x.k)}"><b>${esc(x.k)}</b></button>`:`<b>${esc(x.k)}</b>`},
  nn('zrs','ZD reported · Sept',x=>fN(x.zrs)),nn('znv','ZD recorded · Nov',x=>x.znv==null?'':fN(x.znv)),nn('zp','Coverage %',x=>pcol(x.zp)+(x.zcp?` <span class="cnt">${esc(x.zcp.split(' ')[1]||x.zcp)}</span>`:'')),nn('zg','Not covered',x=>fN(x.zg)),
  nn('zdp','Cov. change Apr→May',x=>x.zdp==null?'–':`<span class="${x.zdp>=0?'up':'dn'}">${sgn(x.zdp)}</span>`),nn('zdq','Cov. change May→Sept',x=>x.zdq==null?'–':`<span class="${x.zdq>=0?'up':'dn'}">${sgn(x.zdq)}</span>`),nn('zpl','Persistent low UCs',x=>x.zpl||''),
  nn('dp','Digitized %',x=>x.dp==null?'–':`<span style="color:${x.dp>=95?C.high:x.dp>=80?C.mod:C.crit};font-weight:600">${pc(x.dp)}</span>`),nn('dgap','Not entered',x=>fN(x.dgap)),nn('dfu','Follow-up UCs',x=>x.dfu==null?'–':x.dfu),
  nn('vn','Validated',x=>fN(x.vn)),nn('vp','% vaccinated',x=>pV(x.vp)),nn('vno','Not vaccinated',x=>x.vno==null?'–':x.vno?`<b class="dn">${x.vno}</b>`:'0'),nn('vfl','Records to check',x=>fN(x.vfl)),nn('cst','Still missed % (camp.)',x=>x.cst==null?'–':`<span style="color:${x.cst>=3?'#b91c1c':'inherit'};font-weight:${x.cst>=3?700:400}">${pc(x.cst)}</span>`),nn('csf','Refusing (camp.)',x=>x.csf?`<b>${fmt(x.csf)}</b>`:'0'),nn('ep3','Penta-3 %',x=>pE(x.ep3)),nn('emr2','MR-2 %',x=>pE(x.emr2))],rowsS,'zp',1);
 el('tSum').querySelectorAll('[data-sd]').forEach(b=>b.onclick=()=>{fDist.value=b.dataset.sd;fTeh.value='';cascade();render();});
 SUMROWS=rowsS;
'''
sl = rep_seg(sl, ' // table\r\n', ' // insights', TBL, 'table')

# ---- insights: Nov bullet before the digitization bullet
sl = ins_before(sl, ' if(dR.length){\r\n  const gd={}',
                ''' if(nv1.rep)I.push(`<b>SNID Nov-26, the concluded round, recorded ${fmt(nv1.rep)} zero-dose children</b> in ${fmt(nv1.n)} UCs across ${fmt(nv1.dists)} districts; its covered figure is the post-campaign return awaited, while its LQAS, still-missed and validation returns are in.`);
''',
                'nov insight')

# ---- insights: campaigns bullet, Nov-first
sl = rep_line(sl, ' if(cN5.tg)I.push(',
              ''' if(nTg)I.push(`<b>Campaigns:</b> ${esc(novLabel())} vaccinated ${fmt(nVac)} children against a ${fmt(nTg)} UC target (${pc(nCov)}); ${fmt(nSt)} children (${pc(nStp)} of the UC target) were still missed after catch-up — ${fmt(nSrf)} refusals, ${fmt(nSna)} not available, ${fmt(nSlo)} left over from earlier rounds.${nRec?` ${fmt(nRec.rec)} were recorded missed, so ${pc(nRec.recov)} were recovered on catch-up.`:''} ${esc(cN5.l)} stood at ${pc(cov5(cN5))} on the same UC-target basis.`);
 else if(cN5.tg)I.push(`<b>Campaigns:</b> ${esc(cN5.l)} covered ${pc(cov5(cN5))} of the under-5 target; no SNID Nov-26 UC is in this selection, so the Nov close-out cannot be shown here.`);''',
              'campaign insight')

# sanity: no orphan references to the removed Sept-only aggregates
for tok in ('MS5', 'rcv5', 'dd5', 'cO5'):
    assert tok not in sl, f'{tok} still referenced in renderSummary'

s = head + sl + tail

# ---------------------------------------------------------------- CSV (top level, after the function)
s = rep_line(s, " [L.Lvl,'ZD reported Sept'",
             " [L.Lvl,'ZD reported Sept','ZD recorded Nov','Coverage % (latest)','Coverage campaign','Not covered','Coverage change Apr→May pts','Coverage change May→Sept pts','Persistent low UCs','Digitized %','Not entered','Follow-up UCs','Children validated','% vaccinated','Not vaccinated','Records to check','Penta-3 %','MR-2 %','Fully immunized %','Still missed % (campaigns)','Refusing (campaigns)'],",
             'csv header')

s = rep_line(s, ' SUMROWS.map(x=>[x.k,x.zrs,',
             r''' SUMROWS.map(x=>[x.k,x.zrs,x.znv==null?'':x.znv,x.zp==null?'':x.zp.toFixed(1),x.zcp,x.zg,x.zdp==null?'':x.zdp.toFixed(1),x.zdq==null?'':x.zdq.toFixed(1),x.zpl,x.dp==null?'':x.dp.toFixed(1),x.dgap,x.dfu,x.vn,x.vp==null?'':x.vp.toFixed(1),x.vno,x.vfl,x.ep3==null?'':x.ep3.toFixed(1),x.emr2==null?'':x.emr2.toFixed(1),x.efi==null?'':x.efi.toFixed(1),x.cst==null?'':x.cst.toFixed(1),x.csf||0]));};''',
             'csv rows')

# ---------------------------------------------------------------- write
assert s.count('\r\n') > 1000
assert s.count('\n') == s.count('\r\n'), 'unexpected newline mix'
open(PATH, 'w', encoding='utf-8', newline='').write(s)
print('patched', PATH, orig_len, '->', len(s))
