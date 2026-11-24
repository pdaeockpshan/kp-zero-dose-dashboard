"""Patch the master index.html for the NID Dec-26 NEAP grid (const NEPD).

The closed SNID Nov-26 return (const NEAP) keeps every existing consumer; this round
adds the live Dec-26 grid as its own card above it, retitles the Nov block as a
closed-round record, and makes the district brief read the Dec grid while labelling
the Nov staffing as the last filed return.

Run once against index.html, then push_master.py syncs the other variants.
"""
import io
import sys

PATH = 'index.html'

MARKUP = """<div class="card" id="cardNEPD" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">NID Dec-26 readiness &mdash; live NEAP grid</h3><span class="cnt" id="cntNEPD"></span><span style="flex:1"></span><button class="btn" id="btnNEPDnid" title="Open the NID Dec-26 resource micro-plan">NID Dec-26 plan</button><button class="btn" id="btnNEPDcsv" title="District-wise NID Dec-26 readiness grid as downloaded from the EOC pre-campaign page">Download (CSV)</button></div><div class="hint" id="nepdHint"></div><div class="kpis"><div class="card"><div class="kl">DPEC held on time</div><div class="kv" id="nepd1">&ndash;</div><div class="ks" id="nepd1s"></div></div><div class="card"><div class="kl">DC attended DPEC</div><div class="kv" id="nepd2">&ndash;</div><div class="ks" id="nepd2s"></div></div><div class="card"><div class="kl">DHO attended DPEC</div><div class="kv" id="nepd3">&ndash;</div><div class="ks" id="nepd3s"></div></div><div class="card"><div class="kl">UCs with a DPEC filed</div><div class="kv" id="nepd4">&ndash;</div><div class="ks" id="nepd4s"></div></div><div class="card"><div class="kl">AIC training started</div><div class="kv" id="nepd5">&ndash;</div><div class="ks" id="nepd5s"></div></div><div class="card"><div class="kl">To campaign start</div><div class="kv" id="nepd6">&ndash;</div><div class="ks" id="nepd6s"></div></div></div><div class="scroll"><table id="tNEPD"></table></div><div class="cap" id="capNEPD"></div></div><div class="card" id="cardNEPDU" style="margin-bottom:16px"><div class="cqbar" style="margin:0 0 10px"><b>UC grid</b><select id="fNEPDUM" aria-label="UC rows to show"><option value="filed">UCs with a filed return</option><option value="all">Every UC in the export</option></select><b>District</b><select id="fNEPDU" aria-label="District"></select><span class="cnt" id="cntNEPDU"></span><span style="flex:1"></span><button class="btn" id="btnNEPDUcsv" title="UC-wise NID Dec-26 grid as shown">Download (CSV)</button></div><div class="scroll" style="max-height:560px"><table id="tNEPDU"></table></div><div class="cap" id="capNEPDU"></div></div>"""

FUNC = r"""// ---------- NID Dec-26 readiness: the live NEAP grid ----------
let NEPDUD=-1, NEPDUM='filed';
const nepDAd=s=>(s||'').replace(/^(\d{4})-(\d{2})-(\d{2})$/,(m,y,mo,d)=>d+'-'+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+mo-1]+'-'+y);
function renderNEPD(){
 const D=(typeof NEPD!=='undefined'&&NEPD)||null;
 if(!el('cardNEPD'))return;
 if(!D||!D.n){
  ['nepd1','nepd2','nepd3','nepd4','nepd5','nepd6'].forEach(id=>{if(el(id))el(id).innerHTML='\u2013';if(el(id+'s'))el(id+'s').textContent='';});
  el('cntNEPD').textContent='no NID Dec-26 return loaded'; el('nepdHint').textContent=''; el('tNEPD').innerHTML=''; el('capNEPD').textContent='';
  return;
 }
 const KN=(D.k||[]).map(x=>x[0]), KL=(D.k||[]).map(x=>x[1]);
 const extra=D.extra||[], isEx=dn=>extra.indexOf(dn)>=0;
 const R=Object.keys(D.d).map(dn=>{const v=D.d[dn],o={d:dn,dv:D2DV[dn]||''};KN.forEach((k,i)=>o[k]=v[i]==null||v[i]<0?null:v[i]);return o;});
 const REG=R.filter(r=>!isEx(r.d)), n=REG.length;
 const at=k=>REG.filter(r=>r[k]!=null&&r[k]>=100).length, any=k=>REG.filter(r=>r[k]!=null&&r[k]>0).length;
 const U=(D.u&&D.u.r)||[], UT=(D.u&&D.u.t)||[];
 const FILED=U.filter(a=>a.slice(3).some(v=>v>0));
 const uDpec=FILED.filter(a=>a[3]>=100).length;
 const nFiledD=new Set(FILED.map(a=>a[0])).size;
 const asof=nepDAd(D.asof), startTxt=D.start?nepDAd(D.start):'';
 const dTo=D.start?Math.ceil((new Date(D.start+'T00:00:00')-new Date())/864e5):null;
 const whoD=REG.filter(r=>r.dpec!=null&&r.dpec>=100).map(r=>r.d);
 el('nepdHint').innerHTML='Live status of the <b>NID Dec-26</b> round, as districts file the EOC pre-campaign NEAP grid (<b>'+esc(D.src)+'</b> district-wise, <b>'+esc(D.srcu||'')+'</b> UC-wise, downloaded <b>'+esc(asof)+'</b>'+(startTxt?', campaign starting <b>'+esc(startTxt)+'</b>'+(dTo!=null?(dTo>0?' ('+dTo+' days)':dTo===0?' (today)':' ('+(-dTo)+' days ago)'):''):'')+'): DPEC meetings and attendance, AIC and team training, microplan validation and team composition, district by district. Zeros are the portal zeros \u2014 a district that has not filed yet reads 0, not blank \u2014 and a dash means the cell was blank in the export. Only <b>'+at('dpec')+' of '+n+'</b> districts and <b>'+fmt(uDpec)+' of '+fmt(U.length)+'</b> UCs have filed a DPEC so far.';
 el('nepd1').innerHTML='<b>'+at('dpec')+'</b> / '+n;
 el('nepd1s').textContent='districts held their DPEC'+(whoD.length?' \u00b7 '+whoD.join(', '):' \u00b7 none yet');
 el('nepd2').innerHTML='<b>'+at('dc')+'</b> / '+n; el('nepd2s').textContent='districts had the DC at the DPEC';
 el('nepd3').innerHTML='<b>'+at('dho')+'</b> / '+n; el('nepd3s').textContent='districts had the DHO at the DPEC';
 el('nepd4').innerHTML='<b>'+fmt(uDpec)+'</b> / '+fmt(U.length);
 el('nepd4s').textContent='UCs with a DPEC filed \u00b7 '+fmt(FILED.length)+' UCs filed anything, in '+nFiledD+' district'+(nFiledD===1?'':'s');
 el('nepd5').innerHTML='<b>'+any('aic')+'</b> / '+n;
 el('nepd5s').textContent='districts started AIC training \u00b7 '+any('trn')+' started team training';
 el('nepd6').innerHTML=dTo==null?'\u2013':('<b>'+Math.abs(dTo)+'</b> '+(Math.abs(dTo)===1?'day':'days'));
 el('nepd6s').textContent=dTo==null?'no start date in the export':(dTo>0?('to '+startTxt+' \u00b7 NID Dec-26'):dTo===0?'campaign starts today':('since the '+startTxt+' start'));
 const BM={dpec:[100,100],dc:[100,100],dho:[100,100],ucmo:[100,100],ucsec:[100,100],aic:[100,100],trn:[100,100],mpv:[100,100],adult:[95,85],loc:[75,50],gov:[75,50],fem:[75,50]};
 const cell=(x,k)=>x[k]==null?'<span class="cnt">\u2013</span>':k==='inacc'?(x[k]<=0?'<span class="rg g">0</span>':'<span class="rg a">'+rnd(x[k],0)+'</span>'):rgN(x[k],(BM[k]||[100,0])[0],(BM[k]||[100,0])[1],x[k]%1?1:0);
 const cols=[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'+(isEx(x.d)?' <span class="cnt">portal sub-unit</span>':'')},{k:'dv',l:'Division'}];
 KN.forEach(k=>cols.push({k:k,l:(D.k.find(x=>x[0]===k)||[k,k])[1],n:1,f:x=>cell(x,k)}));
 const tot={cell:{d:esc('Total \u2014 '+n+' districts'),dv:''}};
 KN.forEach(k=>{tot.cell[k]=k==='inacc'?fmt(REG.reduce((a,r)=>a+(r[k]||0),0)):(REG.filter(r=>r[k]!=null&&r[k]>=(BM[k]||[100])[0]).length+' / '+n);});
 drawTable('tNEPD',cols,R,'d',1,null,tot);
 el('cntNEPD').textContent=R.length+' portal rows \u00b7 '+n+' districts \u00b7 '+fmt(U.length)+' UCs \u00b7 as of '+asof;
 el('capNEPD').textContent='NID Dec-26 grid from the EOC pre-campaign page ('+D.src+' district-wise, '+(D.srcu||'')+' UC-wise, downloaded '+asof+'). The bold bottom line counts districts meeting each column and its own target \u2014 the number before the slash is districts out of '+n+', never a percentage \u2014 and Inaccessible areas is the only column added up. The file still carries zeros for districts that have not filed, so no readiness mean is shown until the grid moves; zeros are filed zeros, not missing cells. BAR SWAT is the portal reporting sub-unit for Swat: it is shown as its own row but kept out of the '+n+'-district counts because the SOPS register carries SWAT separately.';
 const dns=Object.keys(D.d).sort();
 const selD=el('fNEPDU');
 if(selD){
  if(selD.dataset.built!=='1'){ selD.innerHTML='<option value="-1">All districts</option>'+dns.map((d,i)=>'<option value="'+i+'">'+esc(d)+'</option>').join(''); selD.dataset.built='1'; selD.onchange=()=>{NEPDUD=+selD.value; renderNEPD();}; }
  if(NEPDUD>=dns.length)NEPDUD=-1; selD.value=NEPDUD;
 }
 el('tNEPD').onclick=e=>{const tr=e.target.closest&&e.target.closest('tr'); if(!tr||!tr.cells||!tr.cells[0]||!tr.parentElement||tr.parentElement.tagName!=='TBODY')return; const i=dns.indexOf(tr.cells[0].textContent.trim()); if(i>=0){NEPDUD=i; renderNEPD();}};
 const selM=el('fNEPDUM');
 if(selM){ if(selM.dataset.built!=='1'){selM.dataset.built='1';selM.onchange=()=>{NEPDUM=selM.value; renderNEPD();};} selM.options[0].text='UCs with a filed return ('+FILED.length+')'; selM.value=NEPDUM; }
 const UR=U.map(a=>{const o={d:a[0],t:UT[a[1]]||'',u:a[2]};KN.forEach((k,i)=>o[k]=a[3+i]==null||a[3+i]<0?null:a[3+i]);o._f=a.slice(3).some(v=>v>0);return o;});
 let F=UR.filter(r=>NEPDUM==='all'||r._f);
 if(NEPDUD>=0)F=F.filter(r=>r.d===dns[NEPDUD]);
 const colsU=[];
 if(NEPDUD<0)colsU.push({k:'d',l:'District',f:x=>esc(x.d)});
 colsU.push({k:'t',l:'Tehsil'},{k:'u',l:'UC',f:x=>'<b>'+esc(x.u)+'</b>'});
 KN.forEach(k=>colsU.push({k:k,l:(D.k.find(x=>x[0]===k)||[k,k])[1],n:1,f:x=>cell(x,k)}));
 const uTot={cell:{d:'',t:'',u:esc('Total \u2014 '+F.length+' UCs')}};
 KN.forEach(k=>{uTot.cell[k]=k==='inacc'?fmt(F.reduce((a,x)=>a+(x[k]||0),0)):(F.filter(x=>x[k]!=null&&x[k]>=(BM[k]||[100])[0]).length+' / '+F.length);});
 drawTable('tNEPDU',colsU,F,'u',1,'No UC in this view has filed a return yet.',F.length?uTot:null);
 el('cntNEPDU').textContent=F.length+' UCs'+(NEPDUD>=0?' \u00b7 '+dns[NEPDUD]:'')+' \u00b7 '+(NEPDUM==='all'?'every UC in the export':fmt(FILED.length)+' filed of '+fmt(U.length));
 el('capNEPDU').textContent='UC-wise NID Dec-26 grid from '+(D.srcu||'')+' (as of '+nepDAd((D.u&&D.u.asof)||D.asof)+'): '+fmt(U.length)+' UCs, '+fmt(FILED.length)+' with any filed value, in '+nFiledD+' districts. The filed view lists only the UCs a district has started on; the all-UC view is the whole portal sheet, where an unfiled UC reads 0. Total row follows the columns above \u2014 UCs meeting each target, Inaccessible areas summed. UC names are as reported to the NEAP portal.';
 el('btnNEPDcsv').onclick=()=>cqCSV('NEAP_Dec-26_district_grid',['District','Division','Category'].concat(KL),R.map(r=>[r.d,r.dv,critLab(r.d)].concat(KN.map(k=>r[k]==null?'':r[k]))));
 el('btnNEPDUcsv').onclick=()=>cqCSV('NEAP_Dec-26_UC_grid',['District','Tehsil','UC','UC criteria'].concat(KL),F.map(x=>[x.d,x.t,x.u,critLab(x.d,x.u)].concat(KN.map(k=>x[k]==null?'':x[k]))));
 el('btnNEPDnid').onclick=()=>setTab('nid');
}
"""

REPL = []


def add(old, new, n=1):
    REPL.append((old, new, n))


# --- hub intro + Nov sources note -------------------------------------------------
add('Pick a campaign from the dropdown: the live NEAP status of the upcoming SNID Nov-26 round, or the preparatory indicators of an earlier round \u2014 one campaign is shown at a time.',
    'The top block is the live NID Dec-26 readiness grid as districts file it; below it sits the closed SNID Nov-26 round and its final NEAP return. Pick a campaign from the dropdown to read an earlier round \u2014 one campaign is shown at a time.')

add('Already signed in to the EOC portal? Open the <a href="https://www.eoc.gov.pk/analysis/precampaign/NOV-26-1/2" target="_blank" rel="noopener">district-wise</a> or <a href="https://www.eoc.gov.pk/analysis/precampaign/NOV-26-1/3" target="_blank" rel="noopener">UC-wise</a> page and click <b>Export to Excel</b> (file <code>NEAP.xls</code>); the scheduled NEAP refresh picks the newest <code>NEAP*.xls</code> in Downloads and republishes this block automatically.',
    'SNID Nov-26 has closed; these EOC pages stay open for the closed round \u2014 open the <a href="https://www.eoc.gov.pk/analysis/precampaign/NOV-26-1/2" target="_blank" rel="noopener">district-wise</a> or <a href="https://www.eoc.gov.pk/analysis/precampaign/NOV-26-1/3" target="_blank" rel="noopener">UC-wise</a> page and click <b>Export to Excel</b> (file <code>NEAP.xls</code>) if the final return has to be re-downloaded. The scheduled NEAP refresh now reads the NID Dec-26 grid above: it picks the newest <code>NEAP*.xls</code> in Downloads and republishes that block automatically.')

# --- Nov block headings -----------------------------------------------------------
add('<h3 style="margin:0">Core-team briefing \u2014 pre-campaign progress &amp; push list</h3>',
    '<h3 style="margin:0">Core-team briefing \u2014 SNID Nov-26 pre-campaign progress &amp; push list (closed round)</h3>')
add('<button class="btn pri" id="btnSITREP">\u25b6 Daily SITREP (pptx)</button>',
    '<button class="btn pri" id="btnSITREP" title="The SNID Nov-26 pre-campaign SITREP deck, built from the closed round final NEAP return">\u25b6 SITREP \u2014 SNID Nov-26 final (pptx)</button>')
add('<h3 style="margin:0">Activity timeline \u2014 countdown calendar vs NEAP status</h3>',
    '<h3 style="margin:0">Activity timeline \u2014 SNID Nov-26 countdown calendar vs the final NEAP return</h3>')
add('<h3 style="margin:0">SNID Nov-26 pre-campaign activities by district \u2014 NEAP live status</h3>',
    '<h3 style="margin:0">SNID Nov-26 pre-campaign activities by district \u2014 final NEAP return (round closed)</h3>')

# --- renderNEP hint and fIPV tense ----------------------------------------------
add("el('nepHint').innerHTML='Live status of the upcoming round, reported to the EOC NEAP dashboard (<b>'+esc(N.src)+'</b>, as of '+esc(ad)+'): DPEC meetings and attendance, AIC and team training, microplan validation and mobile-team composition, district by district. Green = at target, amber = under way, red = not yet reported; Inaccessible areas are better at zero.';",
    "el('nepHint').innerHTML='Final NEAP return for the SNID Nov-26 round, which has closed (<b>'+esc(N.src)+'</b>, as of '+esc(ad)+'): the round record of DPEC meetings and attendance, AIC and team training, microplan validation and mobile-team composition, district by district. Green = reached the target, amber = under way when the portal was read, red = never reported; Inaccessible areas are better at zero. This is the closed-round record, not live status \u2014 the NID Dec-26 grid above is the live one.';")

add("fIPV first \u2014 Peshawar &amp; Khyber are in fIPV preparation; launch 26-Oct-2026",
    "fIPV first \u2014 Peshawar &amp; Khyber went to fIPV on 26-Oct-2026")
add('fIPV starts in Peshawar and Khyber on <b>26-Oct-2026</b>',
    'fIPV started in Peshawar and Khyber on <b>26-Oct-2026</b>')
add('Both districts are busy with fIPV preparation, so their <b>SNID Nov-26 pre-campaign activities \u2014 DPEC, AIC/team training and microplan validation \u2014 will start late</b>. Read their NEAP status against this, not as stalled; the rest of KP continues on the normal countdown.',
    'Both districts were busy with fIPV preparation, so their <b>SNID Nov-26 pre-campaign activities \u2014 DPEC, AIC/team training and microplan validation \u2014 started late</b>. Read the final NEAP return against this, not as stalled; the rest of KP ran on the normal countdown.')
add('so its SNID activities start late by design.',
    'so its SNID activities started late by design.')
add('<b>Peshawar and Khyber are busy with fIPV preparation until the launch</b>, so their SNID Nov-26 pre-campaign activities \u2014 DPEC, AIC/team training and microplan validation \u2014 will start <b>late</b>; their NEAP status should be read against this, not as stalled.',
    '<b>Peshawar and Khyber were busy with fIPV preparation until the launch</b>, so their SNID Nov-26 pre-campaign activities \u2014 DPEC, AIC/team training and microplan validation \u2014 started <b>late</b>; their final NEAP return should be read against this, not as stalled.')
add('Schedule the SNID DPEC and training push for these two districts after the fIPV teams are deployed; the rest of the province continues on the normal countdown.',
    'The fIPV launch has passed; this closed-round NEAP return is the record of how their pre-campaign activities ran.')
add('\\u2014 at 0% on every indicator; needs DC-level intervention to hold DPECs before month-end.',
    '\\u2014 at 0% on every indicator; no DPEC was held in the round.')
add("so their SNID pre-campaign activities start late.'", "so their SNID pre-campaign activities started late.'")
add("'their':'its')+' SNID pre-campaign activities start late.'", "'their':'its')+' SNID pre-campaign activities started late.'")
add('Districts needing push \\u2014 Tier 1: nothing moving (no DPEC held)',
    'Tier 1 \\u2014 no DPEC in the final return')
add('Tier 2: DPEC held, AIC training not started', 'Tier 2 \u2014 DPEC held, AIC training never started')
add('Tier 3: started but behind (<90% AICs trained)', 'Tier 3 \u2014 started but under 90% AICs trained')
add("secs.push(['Ask to the core team',[", "secs.push(['What the final return leaves for NID Dec-26',[")
add("'DC-level push in '+T1o.map(r=>DNb(r.d)).join(', ')+' to hold DPECs.'",
    "'DC-level push in '+T1o.map(r=>DNb(r.d)).join(', ')+' to hold the first NID Dec-26 DPEC.'")
add("'AIC training to start in '+T2.map(r=>DNb(r.d)).join(', ')+' within 48 hours.'",
    "'AIC training to start in '+T2.map(r=>DNb(r.d)).join(', ')+' before 12-Dec.'")
add("' Peshawar and Khyber start SNID pre-campaign activities after the 26-Oct fIPV launch.'",
    "' Peshawar and Khyber started SNID pre-campaign activities after the 26-Oct fIPV launch.'")
add("dTo!=null&&dTo<=0?' \\u00b7 campaign under way'", "dTo!=null&&dTo<=0?' \\u00b7 round closed'")

# --- picker label + note ----------------------------------------------------------
add("esc((NEAP&&NEAP.camp)||'SNID Nov-26')+' \u00b7 pre-campaign activities (live)</option>'",
    "esc((NEAP&&NEAP.camp)||'SNID Nov-26')+' \u00b7 pre-campaign activities (round closed)</option>'")
add("if(isN){ el('fCPCnote').textContent=(NEAP&&NEAP.camp?NEAP.camp+' \u00b7 ':'')+'NEAP live status reported to the EOC'+(NEAP&&NEAP.asof?' \u00b7 as of '+NEAP.asof:''); renderNEP(); renderMPQ(); return; }",
    "if(isN){ el('fCPCnote').textContent='NID Dec-26 NEAP grid'+(NEPD&&NEPD.asof?' \u00b7 as of '+NEPD.asof:'')+' \u00b7 SNID Nov-26 final return'+(NEAP&&NEAP.asof?' \u00b7 as of '+NEAP.asof:''); renderNEPD(); renderNEP(); renderMPQ(); return; }")

# --- cross-cutting labels that still say "live"/"under way" ----------------------
add("['rdy','Nov-26 readiness']", "['rdy','Nov-26 readiness (last filed)']")
add("'Nov-26 NEAP readiness under 95%, micro-plan reviews still owed, or a micro-plan already scored under 70'",
    "'NEAP readiness in the last filed return (SNID Nov-26) under 95%, micro-plan reviews still owed, or a micro-plan already scored under 70'")
add("'<b>Nov-26 readiness</b>: '", "'<b>Nov-26 readiness (last filed)</b>: '")
add(' For the round under way, readiness is the NEAP pre-campaign reading from the Pre-campaign tab.',
    ' For the latest round, readiness is the NEAP pre-campaign reading in the last filed return, on the Pre-campaign tab.')
add('the same measure as \\u201cmicroplans validated\\u201d in the NEAP table above',
    'the same measure as \\u201cmicroplans validated\\u201d in the NEAP tables above')

# --- SITREP countdown wording for a closed round ---------------------------------
add("   :('Campaign under way \\u00b7 day '+(1-dTo)+' since '+nactDm(campSt)))));",
    "   :(dTo>=-6?('Campaign under way \\u00b7 day '+(1-dTo)+' since '+nactDm(campSt))\n    :('Campaign closed \\u00b7 '+(-dTo)+' days since '+nactDm(campSt))))));")

# --- district brief ---------------------------------------------------------------
add('pdInit({ZD:ZD,EPI:EPI,VAL:VAL,MPQA:MPQA,NEAP:NEAP,HRA:HRA,LQR:LQR,LQM:LQM,CQ:CQ,AFP:AFP});',
    'pdInit({ZD:ZD,EPI:EPI,VAL:VAL,MPQA:MPQA,NEAP:NEAP,NEPD:NEPD,HRA:HRA,LQR:LQR,LQM:LQM,CQ:CQ,AFP:AFP});')
add("  var nep=(NEAP.d&&NEAP.d[dist])||null;\n  var NEPK=((NEAP.k||[]).map(function(x){return x[0];}));\n  var neap=null;\n  if(nep){ neap={}; NEPK.forEach(function(k,i){neap[k]=nep[i]==null||nep[i]<0?null:nep[i];}); neap.camp=NEAP.camp||'Nov-26'; neap.asof=NEAP.asof||''; }\n",
    "  var nep=(NEAP.d&&NEAP.d[dist])||null;\n  var NEPK=((NEAP.k||[]).map(function(x){return x[0];}));\n  var neap=null;\n  if(nep){ neap={}; NEPK.forEach(function(k,i){neap[k]=nep[i]==null||nep[i]<0?null:nep[i];}); neap.camp=NEAP.camp||'Nov-26'; neap.asof=NEAP.asof||''; }\n  var ndv=(SRC.NEPD&&SRC.NEPD.d&&SRC.NEPD.d[dist])||null, nepd=null;\n  if(ndv){ var NDK=((SRC.NEPD.k||[]).map(function(x){return x[0];})); nepd={}; NDK.forEach(function(k,i){nepd[k]=ndv[i]==null||ndv[i]<0?null:ndv[i];});\n    var ndU=((SRC.NEPD.u||{}).r||[]).filter(function(a){return a[0]===dist;});\n    nepd.uAll=ndU.length; nepd.uFiled=ndU.filter(function(a){return a.slice(3).some(function(v){return v>0;});}).length;\n    nepd.camp=SRC.NEPD.camp||'NID Dec-26'; nepd.asof=SRC.NEPD.asof||''; nepd.start=SRC.NEPD.start||''; }\n")
add('icm:icm,lq:lq,mpqa:mpqa,neap:neap,hra:hra,',
    'icm:icm,lq:lq,mpqa:mpqa,neap:neap,nepd:nepd,hra:hra,')
add("  s.push(D.neap?('NEAP government-accountable staff '+P1(D.neap.gov)+' vs '+P1(p.gov)+' province, women '+P1(D.neap.fem)+' vs '+P1(p.fem)):'no NEAP pre-campaign return');",
    "  s.push(D.nepd?('NID Dec-26 NEAP '+(D.nepd.dpec>=100?'DPEC filed':'DPEC not yet filed')+(D.nepd.uAll?' ('+D.nepd.uFiled+' of '+D.nepd.uAll+' UCs)':'')):'no NID Dec-26 NEAP return loaded');\n  s.push(D.neap?('last filed return (SNID Nov-26): government-accountable '+P1(D.neap.gov)+' vs '+P1(p.gov)+' province, women '+P1(D.neap.fem)+' vs '+P1(p.fem)):'no closed SNID Nov-26 NEAP return');")

add("""  if(D.neap&&D.neap.gov!=null&&pv.gov!=null&&D.neap.gov<pv.gov){
    a.push({t:'Make government-accountable staffing a condition of the December micro-plan',
      b:P1(D.neap.gov)+' of team members are government-accountable against '+P1(pv.gov)+' province-wide. That is the number to raise.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'Share above '+Math.round(D.neap.gov+5)+'% and rising'});
  }else if(D.neap&&D.neap.fem!=null){
    a.push({t:'Protect the female share of the team in the December micro-plan',
      b:P1(D.neap.fem)+' of team members are women'+(pv.fem!=null?(' against '+P1(pv.fem)+' province-wide'):'')+'. Hold it through deployment.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'Share at or above '+Math.round(D.neap.fem)+'%'});
  }else{
    a.push({t:'Submit the missing NEAP return for this district',
      b:'No NEAP pre-campaign return is loaded for '+D.nm+', so the micro-plan cannot be benchmarked against the province.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'NEAP return submitted and scored'});
  }""",
    """  if(!D.nepd||!(D.nepd.dpec>=100)){
    a.push({t:'Hold the DPEC and file the NID Dec-26 NEAP readiness return',
      b:'No DPEC is on the Dec-26 grid for '+D.nm+' yet'+(D.nepd&&D.nepd.uAll?('; '+D.nepd.uFiled+' of '+D.nepd.uAll+' UCs have filed'):'')+'. The grid is the EOC record that the round is being prepared.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'DPEC held and the NEAP grid filed'});
  }else if(!(D.nepd.aic>0)){
    a.push({t:'Start AIC and team training for the December round',
      b:'The DPEC is filed on the Dec-26 grid but no AIC training is reported yet; teams cannot be trained before the AICs.',
      o:'District EPI focal person',w:'Before 12 Dec',m:'AIC training under way in every tehsil'});
  }else if(D.neap&&D.neap.gov!=null&&pv.gov!=null&&D.neap.gov<pv.gov){
    a.push({t:'Hold government-accountable staffing above the provincial line',
      b:'In the last filed return (SNID Nov-26), '+P1(D.neap.gov)+' of team members were government-accountable against '+P1(pv.gov)+' province-wide. That is the benchmark to hold through December.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'Share above '+Math.round(D.neap.gov+5)+'% and rising'});
  }else if(D.neap&&D.neap.fem!=null){
    a.push({t:'Protect the female share of the team in the December micro-plan',
      b:'In the last filed return (SNID Nov-26), '+P1(D.neap.fem)+' of team members were women'+(pv.fem!=null?(' against '+P1(pv.fem)+' province-wide'):'')+'. Hold it through deployment.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'Share at or above '+Math.round(D.neap.fem)+'%'});
  }else{
    a.push({t:'Submit the missing NEAP return for this district',
      b:'No NEAP pre-campaign return is loaded for '+D.nm+', so staffing cannot be benchmarked against the province.',
      o:'Deputy Commissioner',w:'Before 12 Dec',m:'NEAP return submitted and scored'});
  }""")

add("  ready.push(D.neap?['Government-accountable staff',P1(D.neap.gov)+' vs '+P1(D.prov.gov)+' province']:['NEAP return','not loaded for this district']);\n  ready.push(D.neap?['Women on the team',P1(D.neap.fem)+' vs '+P1(D.prov.fem)+' province']:['MPQA sample',D.mpqa?(D.mpqa.plan-D.mpqa.scored)+' of '+D.mpqa.plan+' plans still unscored':'not assigned']);",
    "  ready.push(D.nepd?['NID Dec-26 NEAP',(D.nepd.dpec>=100?'DPEC filed':'DPEC not yet filed')+(D.nepd.uAll?' \u00b7 '+D.nepd.uFiled+' of '+D.nepd.uAll+' UCs':'')]:['NID Dec-26 NEAP','not loaded for this district']);\n  ready.push(D.neap?['Staffing \u2014 last filed (Nov-26)',P1(D.neap.gov)+' govt-accountable \u00b7 '+P1(D.neap.fem)+' women']:['MPQA sample',D.mpqa?(D.mpqa.plan-D.mpqa.scored)+' of '+D.mpqa.plan+' plans still unscored':'not assigned']);")


def main():
    with io.open(PATH, encoding='utf-8', newline='') as fh:
        s = fh.read()
    crlf = s.count('\r\n')
    if crlf == 0 or s.count('\n') != crlf:
        sys.exit('ABORT: index.html is not pure CRLF')
    if 'id="cardNEPD"' in s:
        sys.exit('ABORT: NEPD UI patch is already applied')

    # normalise the scripted multi-line anchors to CRLF for matching
    global REPL
    REPL = [(o.replace('\n', '\r\n'), n.replace('\n', '\r\n') if '\n' in n and not n.endswith('\n') else n, c)
            for o, n, c in REPL]
    # new text may need normalising too, but never add a bare LF
    for old, new, cnt in REPL:
        pass

    anchor = '<div id="cpreNew">\r\n'
    if s.count(anchor) != 1:
        sys.exit('ABORT: cpreNew anchor found %d times' % s.count(anchor))
    s = s.replace(anchor, anchor + MARKUP.replace('\n', '\r\n') + '\r\n', 1)

    anchor2 = '// ---------- Pre-campaign ----------\r\n'
    if s.count(anchor2) != 1:
        sys.exit('ABORT: pre-campaign function anchor found %d times' % s.count(anchor2))
    s = s.replace(anchor2, FUNC.replace('\n', '\r\n') + '\r\n' + anchor2, 1)

    for old, new, cnt in REPL:
        # anchors containing newlines were normalised above; single-line ones pass through
        o = old.replace('\r\n', '\n')
        nw = new.replace('\r\n', '\n')
        # match against the CRLF file: build both forms
        oc = o.replace('\n', '\r\n')
        nc = nw.replace('\n', '\r\n')
        got = s.count(oc)
        if got != cnt:
            sys.exit('ABORT: anchor %r found %d times, expected %d' % (o[:80], got, cnt))
        s = s.replace(oc, nc)

    if s.count('\n') != s.count('\r\n'):
        sys.exit('ABORT: patch introduced a bare LF (%d LF, %d CRLF)' % (s.count('\n'), s.count('\r\n')))

    with io.open(PATH, 'w', encoding='utf-8', newline='') as fh:
        fh.write(s)
    print('OK nepd UI patch applied, %s chars, %d CRLF, 0 bare LF' % (format(len(s), ','), s.count('\r\n')))


if __name__ == '__main__':
    main()
