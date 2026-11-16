import io, sys

P = 'index.html'
t = open(P, encoding='utf-8', newline='').read()

assert t.count('\r\n') == t.count('\n'), 'CRLF damaged before patch'
assert 'NVMUP' not in t, 'patch already applied'


def j(*ls):
    return '\r\n'.join(ls)


def rep(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, (c, n, old[:90])
    t = t.replace(old, new)


# ---------- static copy ----------
rep(
    '<div class="hint">These inferences are written from the data and update with the Division, District, Tehsil and search filters. Pick a district at the top to get its tehsil-level story.</div>',
    '<div class="hint">These inferences are written from the data and update with the Division, District, Tehsil and search filters. Pick a district at the top to get its tehsil-level story. SNID Nov-26 is in on its own reported zero-dose return; its covered figure is a post-campaign return and is still awaited.</div>'
)

rep(
    "<li><b>Like-for-like trend</b>: April vs May uses only UCs that reported coverage in both campaigns, so the smaller May SNID doesn't distort the result.</li>",
    j(
        "<li><b>Like-for-like trend</b>: April → May → Sept uses only UCs that reported coverage in all three campaigns, so the smaller May and Sept SNID rounds don't distort the result.</li>",
        "<li><b>SNID Nov-26</b> is the latest round. Its reported zero-dose count is the round's own UC-wise return; its covered figure, digitization and validation are post-campaign returns that are still awaited. Nov is therefore compared on reported ZDs only, and Sept remains the last measured coverage.</li>"
    )
)

rep(
    'Ordered by rating, with the places that need attention first. Each note gives the coverage trend, the gap, the Sept caseload and the focus UCs.',
    'Ordered by rating, with the places that need attention first. Each note gives the coverage trend, the gap, the Sept and Nov caseloads and the focus UCs.'
)

rep(
    '<div class="tblhdr"><h3 style="margin:0">SNID Sept double-risk UCs: last coverage &lt;80% and more ZDs reported now</h3>',
    '<div class="tblhdr"><h3 style="margin:0">Double-risk UCs: coverage below 80% before SNID Sept and a larger caseload then, with the Nov return alongside</h3>'
)

rep(
    '<div class="cap">"Last coverage" = SNID May, or NID April for UCs not in May. These UCs had a coverage problem last time and a larger zero-dose caseload in Sept. Sept coverage is now reported, so the Sept columns show whether each of them closed the gap; start with the UCs still below 80% in Sept.</div>',
    '<div class="cap" id="capZP">"Base coverage" = SNID May, or NID April for UCs not in May. These UCs had a coverage problem before the Sept round and a larger zero-dose caseload in it. The Sept columns show whether each of them closed the gap; the Nov columns carry the round\'s own UC-wise return.</div>'
)

# ---------- helper: base round for the double-risk cohort ----------
rep(
    'const priRows=()=>cur.filter(r=>{const l=ucLast(r);return l.p!=null&&l.p<80&&r.rS!=null&&r.rS>l.r;});',
    j(
        '// the double-risk base is the last measured round BEFORE Sept, so the cohort does not vanish once Sept coverage lands',
        'const pBase=o=>{if(o.pM!=null)return{p:o.pM,r:o.rM,cp:CAMP.M,k:\'M\'};if(o.pA!=null)return{p:o.pA,r:o.rA,cp:CAMP.A,k:\'A\'};return{p:null,r:null,cp:\'\',k:null};};',
        'const priRows=()=>cur.filter(r=>{const b=pBase(r);return b.p!=null&&b.p<80&&r.rS!=null&&b.r!=null&&r.rS>b.r;});'
    )
)

# ---------- Nov-26 plumbing + headline inference ----------
rep(
    " else I.push(SCOV?'No UC in this selection reported coverage in all three campaigns, so the three-way coverage trend cannot be measured here. Only reported ZDs can be tracked.':'No UC in this selection reported coverage in both April and May, so the coverage trend cannot be measured. Only reported ZDs can be tracked here.');",
    j(
        " else I.push(SCOV?'No UC in this selection reported coverage in all three campaigns, so the three-way coverage trend cannot be measured here. Only reported ZDs can be tracked.':'No UC in this selection reported coverage in both April and May, so the coverage trend cannot be measured. Only reported ZDs can be tracked here.');",
        ' // SNID Nov-26: the closed round\'s own UC-wise return. Covered is a post-campaign return, so Nov is read on reported ZDs only.',
        ' const NRW=novRows().filter(matchG), NVM={}, ZC={};',
        ' NRW.forEach(x=>{if(x.c)NVM[x.c]=x;}); cur.forEach(r=>{ZC[r.c]=r;});',
        ' const nkD=s=>String(s||\'\').toUpperCase().replace(/[^A-Z0-9]/g,\'\');',
        ' const nvRep=S_(NRW,x=>x.rN), nvU=NRW.length, nvD=new Set(NRW.map(x=>x.d)).size;',
        ' const nm=NRW.filter(x=>ZC[x.c]!=null), mSep=S_(nm,x=>ZC[x.c].rS), mNov=S_(nm,x=>x.rN), mHH=S_(nm,x=>ZC[x.c].hS);',
        ' const NVMUP=nm.filter(x=>ZC[x.c].rS!=null&&x.rN>ZC[x.c].rS).length, NVMDN=nm.filter(x=>ZC[x.c].rS!=null&&x.rN<ZC[x.c].rS).length;',
        ' if(NRW.length){const DN={}; NRW.forEach(x=>{const g=DN[x.d]=DN[x.d]||{k:x.d,rep:0};g.rep+=x.rN||0;});',
        '  const dt=Object.values(DN).sort((a,b)=>b.rep-a.rep), t3=dt.slice(0,3), sh3=nvRep?S_(t3,g=>g.rep)/nvRep*100:null;',
        '  const ks=mHH?mSep/mHH*1000:null, kn=mHH?mNov/mHH*1000:null, dch=mSep?mNov-mSep:null;',
        '  I.push(`<b>SNID Nov-26 closed with ${fmt(nvRep)} zero-dose children reported across ${fmt(nvU)} UCs in ${fmt(nvD)} districts.</b> Its own zero-dose covered figure is a post-campaign return and is not in yet, so Nov coverage cannot be measured and Sept stays the last measured round.`+(nm.length?` On the ${fmt(nm.length)} UCs that are in both Sept and Nov, reported ZDs went from ${fmt(mSep)} to ${fmt(mNov)} (${sgn(dch,0)}, ${sgn(mSep?(mNov/mSep-1)*100:null,1)}%), or ${ks==null?\'–\':ks.toFixed(1)} → ${kn==null?\'–\':kn.toFixed(1)} per 1,000 households; ${fmt(NVMUP)} UCs rose and ${fmt(NVMDN)} fell. A fall can mean fewer zero-dose children found or fewer recorded — the Nov validation return separates the two.`:\'\')+(t3.length?` Largest caseloads: ${t3.map(g=>`${esc(g.k)} (${fmt(g.rep)})`).join(\', \')}${sh3==null?\'\':` — ${sh3.toFixed(0)}% of the round between them`}.`:''));}',
        " else I.push('<b>SNID Nov-26 did not cover this selection.</b> The round ran in 27 districts, so these trends stop at SNID Sept; Nov coverage is a post-campaign return that is still awaited.');"
    )
)

# ---------- double-risk cohort: Nov follow-up sentence ----------
rep(
    "  I.push(`<b>${PR.length} UCs are at double risk.</b> Their last coverage before SNID Sept was below 80% and they reported more zero-dose children in Sept (${fmt(S_(PR,r=>r.rS))}).`+(SCOV?` ${still} of them are still under 80% in Sept and ${noC} gave no Sept coverage figure,`:'')+' they are listed below and should come first for coverage follow-up.');}",
    j(
        "  I.push(`<b>${PR.length} UCs are at double risk.</b> Their last coverage before SNID Sept was below 80% and they reported more zero-dose children in Sept (${fmt(S_(PR,r=>r.rS))}).`+(SCOV?` ${still} of them are still under 80% in Sept and ${noC} gave no Sept coverage figure,`:'')+' they are listed below and should come first for coverage follow-up.');}",
        ' if(PR.length&&NRW.length){const pn=PR.filter(r=>NVM[r.c]!=null), upn=pn.filter(r=>NVM[r.c].rN>r.rS).length;',
        "  if(upn)I.push(`<b>${upn} of those ${pn.length} double-risk UCs are inside the Nov scope and reported more ZDs again in Nov</b> (${fmt(S_(pn,r=>NVM[r.c].rN))} against ${fmt(S_(pn,r=>r.rS))} in Sept).`);}"
    )
)

# ---------- district notes ----------
rep(
    " el('zdnT').textContent=(L.key==='d'?'District':'Tehsil')+' notes'+(fDist.value?': '+fDist.value:'');",
    j(
        " el('zdnT').textContent=(L.key==='d'?'District':'Tehsil')+' notes'+(fDist.value?': '+fDist.value:'');",
        ' const NVD={}; NRW.forEach(x=>{const k=nkD(x.d);NVD[k]=(NVD[k]||0)+(x.rN||0);});'
    )
)

rep(
    "  <p>Sept reported: <b>${fmt(x.rS)}</b>${x.chS==null?'':` (${sgn(x.chS,0)}% vs April)`} · ${x.kS==null?'–':x.kS.toFixed(1)} per 1,000 HH</p>",
    j(
        "  <p>Sept reported: <b>${fmt(x.rS)}</b>${x.chS==null?'':` (${sgn(x.chS,0)}% vs April)`} · ${x.kS==null?'–':x.kS.toFixed(1)} per 1,000 HH</p>",
        "  ${NVD[nkD(x.k)]==null?'':`<p>Nov reported: <b>${fmt(NVD[nkD(x.k)])}</b>${x.rS==null?'':` (${sgn(NVD[nkD(x.k)]-x.rS,0)}% vs Sept)`} · Nov coverage awaited</p>`}"
    )
)

# ---------- priority table ----------
rep(
    j(
        "  {k:'lc',l:'Last coverage',sv:r=>ucLast(r).cp,f:r=>ucLast(r).cp||'–'},zn('lp','Last cov %',r=>pcol(ucLatest(r)),ucLatest),",
        "  zn('lr','Last reported',r=>fN(ucLast(r).r),r=>ucLast(r).r),zn('rS','Sept reported',r=>`<b>${fN(r.rS)}</b>`),",
        "  zn('inc','Rise',r=>sgn(r.rS-ucLast(r).r,0),r=>r.rS-ucLast(r).r),",
        "  zn('gc','Not covered ('+CAMP[LCP]+')',r=>r['c'+LCP]==null?'–':(gapZ(r,LCP)||''),r=>r['c'+LCP]==null?null:gapZ(r,LCP)),{k:'tr',l:'Trend Apr–May',f:r=>ztTag(r.tr)}],PR,'rS',-1);"
    ),
    j(
        "  {k:'lc',l:'Base coverage',sv:r=>pBase(r).cp,f:r=>pBase(r).cp||'–'},zn('lp','Base cov %',r=>pcol(pBase(r).p),r=>pBase(r).p),",
        "  zn('lr','Base reported',r=>fN(pBase(r).r),r=>pBase(r).r),zn('rS','Sept reported',r=>`<b>${fN(r.rS)}</b>`),",
        "  zn('inc','Rise vs base',r=>sgn(r.rS-pBase(r).r,0),r=>r.rS-pBase(r).r),",
        "  zn('gc','Not covered ('+CAMP[LCP]+')',r=>r['c'+LCP]==null?'–':(gapZ(r,LCP)||''),r=>r['c'+LCP]==null?null:gapZ(r,LCP)),",
        "  zn('rN','Nov reported',r=>NVM[r.c]==null?'–':'<b>'+fN(NVM[r.c].rN)+'</b>',r=>NVM[r.c]==null?null:NVM[r.c].rN),",
        "  zn('incN','Sept→Nov',r=>NVM[r.c]==null?'–':sgn(NVM[r.c].rN-r.rS,0),r=>NVM[r.c]==null?null:NVM[r.c].rN-r.rS),",
        "  {k:'tr',l:'Trend Apr–May',f:r=>ztTag(r.tr)}],PR,'rS',-1);"
    )
)

# ---------- count + caption ----------
rep(
    " el('cntZP').textContent=PR.length+' UCs';",
    j(
        " const np=PR.filter(r=>NVM[r.c]!=null).length;",
        " el('cntZP').textContent=PR.length+' UCs'+(np?' · '+np+' in the Nov scope':'');",
        " const nfT=(typeof NOVF!=='undefined'&&NOVF&&NOVF.tot&&NOVF.k)?NOVF.tot[NOVF.k.indexOf('zd')-3]:null;",
        " if(el('capZP'))el('capZP').innerHTML='\"Base coverage\" = SNID May, or NID April for UCs not in May: a coverage problem before the Sept round plus a larger zero-dose caseload in it. The Sept columns show whether each closed the gap on its own return; start with those still under 80% in Sept. <b>Nov reported</b> is the round’s own UC-wise return, read 06-Nov-2026'+(nfT!=null?', while the 11-Nov district close-out reads '+fmt(nfT)+' at district grain':'')+'. Nov covered, digitization and validation are post-campaign returns and are still awaited.';"
    )
)

# ---------- CSV ----------
rep(
    j(
        "el('btnZCSV').onclick=()=>csvDownload('ZD_Sept_Priority_UCs_'+(fDist.value||'All_districts').replace(/\\s+/g,'_')+'.csv',",
        " ['District','Tehsil','UC','UC Code','Last coverage campaign','Last coverage %','Last reported','Sept reported','Rise','Trend Apr-May'],",
        " priRows().sort((x,y)=>x.d.localeCompare(y.d)||y.rS-x.rS).map(r=>[r.d,r.t,r.u,r.c,r.pM!=null?CAMP.M:CAMP.A,r.pM!=null?r.pM:r.pA,r.pM!=null?r.rM:r.rA,r.rS,r.rS-(r.pM!=null?r.rM:r.rA),r.tr]));"
    ),
    j(
        "el('btnZCSV').onclick=()=>csvDownload('ZD_DoubleRisk_UCs_'+(fDist.value||'All_districts').replace(/\\s+/g,'_')+'.csv',",
        " ['District','Tehsil','UC','UC Code','Base coverage campaign','Base coverage %','Base reported','Sept reported','Rise vs base','Nov reported','Sept to Nov','Trend Apr-May'],",
        " priRows().sort((x,y)=>x.d.localeCompare(y.d)||y.rS-x.rS).map(r=>[r.d,r.t,r.u,r.c,pBase(r).cp,pBase(r).p,pBase(r).r,r.rS,r.rS-pBase(r).r,NVM[r.c]==null?'':NVM[r.c].rN,NVM[r.c]==null?'':NVM[r.c].rN-r.rS,r.tr]));"
    )
)

assert t.count('\r\n') == t.count('\n'), 'CRLF damaged after patch'
open(P, 'w', encoding='utf-8', newline='').write(t)
print('patched', P, len(t))
