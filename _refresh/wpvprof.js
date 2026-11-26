/* WPVPROF:JS:START */
const WPVC=(function(){
 const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 const NS=s=>String(s||'').toUpperCase().replace(/[^A-Z0-9]+/g,'');
 const F=n=>n==null?'–':fmt(n);
 const PC=v=>v==null?'–':v.toFixed(1)+'%';
 const SG=v=>v==null?'–':(v>0?'+':'')+v.toFixed(1)+'%';
 const avg=(a,f)=>{const g=f||(x=>x);const v=a.map(g).filter(x=>x!=null&&isFinite(x));return v.length?v.reduce((s,x)=>s+x,0)/v.length:null;};
 const MX=a=>a.length?Math.max.apply(null,a):null;
 const MN=a=>a.length?Math.min.apply(null,a):null;
 const A=a=>a&&a.length?a.join(', '):'–';
 const covT=p=>p==null?'':p>110?'t-over':p>=90?'t-high':p>=80?'t-low':'t-crit';
 const recT=p=>p==null?'':p>=90?'t-high':p>=80?'t-low':'t-crit';
 const pcmT=p=>p==null?'':p>=95?'t-high':p>=90?'t-low':'t-crit';
 const misT=p=>p==null?'':p<=2?'t-high':p<=5?'t-low':'t-crit';
 const missT=p=>p==null?'':p<=10?'t-high':p<=15?'t-low':'t-crit';
 const swpT=p=>p==null?'':p>=60?'t-high':p>=40?'t-low':'t-crit';
 const lqT=r=>r==='P'?'t-high':r==='I'?'t-low':r==='F'?'t-crit':'';
 const AF=(typeof AFPUC!=='undefined'&&AFPUC)?AFPUC:null;

 let G=null, cur=null;

 // ---------- geography (current EPI register, division -> district -> tehsil -> UC) ----------
 const DORD=['PESHAWAR','MARDAN','HAZARA','MALAKAND','KOHAT','BANNU','DIKHAN'];
 function geo(){
  if(G)return G;
  const dv=[],D={},T={},U={};
  EPI.forEach(e=>{
   const v=e.dv||'—', d=e.d||'—', t=e.t||'—';
   if(dv.indexOf(v)<0)dv.push(v);
   const dk=v+'|'+d; (D[v]=D[v]||[]); if(D[v].indexOf(d)<0)D[v].push(d);
   (T[dk]=T[dk]||[]); if(T[dk].indexOf(t)<0)T[dk].push(t);
   const tk=dk+'|'+t; (U[tk]=U[tk]||[]); const c=String(e.c||'');
   if(c&&!U[tk].some(x=>x.c===c))U[tk].push({c,u:e.u||''});
  });
  const oi=x=>{const i=DORD.indexOf(x);return i<0?99+i:i;};
  dv.sort((a,b)=>oi(a)-oi(b)||String(a).localeCompare(b));
  Object.keys(D).forEach(k=>D[k].sort());
  Object.keys(T).forEach(k=>T[k].sort());
  Object.keys(U).forEach(k=>U[k].sort((a,b)=>String(a.u).localeCompare(b.u)));
  return G={dv,D,T,U};
 }
 function setOpts(id,arr,ph,cur){
  const s=el(id); if(!s)return;
  s.innerHTML='<option value="">'+esc(ph)+'</option>'+arr.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
  s.value=(cur&&arr.indexOf(cur)>=0)?cur:''; s.disabled=!arr.length;
 }
 function setUCs(id,arr,ph,cur){
  const s=el(id); if(!s)return;
  s.innerHTML='<option value="">'+esc(ph)+'</option>'+arr.map(x=>'<option value="'+esc(x.c)+'" title="UC code '+esc(x.c)+'">'+esc(x.u)+'</option>').join('');
  s.value=(cur&&arr.some(x=>x.c===cur))?cur:''; s.disabled=!arr.length;
 }
 function init(){
  const g=geo();
  setOpts('wpvDiv',g.dv,'— select division —','');
  setOpts('wpvDist',[],'Select a division','');
  setOpts('wpvTeh',[],'Select a district','');
  setUCs('wpvUc',[],'Select a tehsil','');
  if(el('wpvDiv'))el('wpvDiv').onchange=()=>cascade(1);
  if(el('wpvDist'))el('wpvDist').onchange=()=>cascade(2);
  if(el('wpvTeh'))el('wpvTeh').onchange=()=>cascade(3);
  if(el('wpvUc'))el('wpvUc').onchange=()=>cascade(4);
  if(el('wpvReset'))el('wpvReset').onclick=()=>{init();draw();};
  if(el('wpvCsv'))el('wpvCsv').onclick=()=>{if(cur)csv(cur);};
  [['wpvCsv','download'],['wpvReset','swap']].forEach(pair=>{
   const b=el(pair[0]); if(!b)return; const i=b.querySelector('[data-ic]');
   if(i&&!i.innerHTML&&typeof SVGI!=='undefined'&&typeof ICO!=='undefined')i.innerHTML=SVGI(ICO[pair[1]]||ICO.download);
  });
  draw();
 }
 function cascade(level){
  const g=geo(),dv=el('wpvDiv').value,d=el('wpvDist').value;
  if(level<=1)setOpts('wpvDist',dv?(g.D[dv]||[]):[],dv?'— select district —':'Select a division','');
  if(level<=2){const v2=el('wpvDiv').value,d2=el('wpvDist').value;setOpts('wpvTeh',d2?(g.T[v2+'|'+d2]||[]):[],d2?'— select tehsil —':'Select a district','');}
  if(level<=3){const v3=el('wpvDiv').value,d3=el('wpvDist').value,t3=el('wpvTeh').value;setUCs('wpvUc',t3?(g.U[v3+'|'+d3+'|'+t3]||[]):[],t3?'— select UC —':'Select a tehsil','');}
  draw();
 }

 // ---------- joins ----------
 function chIdx(d,u){
  const uu=NS(u); let hit=-1;
  for(let i=0;i<CHD.u.length;i++){const x=CHD.u[i];if(CHD.ds[x[1]]!==d)continue;if(NS(x[0])===uu){hit=i;break;}}
  if(hit>=0)return hit;
  for(let i=0;i<CHD.u.length;i++){const x=CHD.u[i];if(CHD.ds[x[1]]!==d)continue;const n=NS(x[0]);if(n.length>=8&&(uu.indexOf(n)===0||n.indexOf(uu)===0)){hit=i;break;}}
  return hit;
 }
 const lab=c=>MON[(c.m||1)-1]+'-'+String(c.y||'').slice(2);
 function met(r){
  const g=v=>v===''||v==null?null:v/10;
  const t=r[1],cov=r[2],recN=r[7]||0,recR=r[8]||0,rec=recN+recR,sdc=r[9]||0,sm=r[5]||0,sna=r[3]||0,srf=r[4]||0;
  return {t,cov,recN,recR,rec,sdc,sm,sna,srf,zd:r[6]||0,clu:r[10]||0,
   covp:t?cov/t*100:null, recp:t?rec/t*100:null, sdcp:rec?sdc/rec*100:null, stp:t?sm/t*100:null,
   rcp:g(r[11]),snp:g(r[12]),msp:g(r[13]),lqp:g(r[14]),pcmp:g(r[15])};
 }

 // ---------- build ----------
 function build(dv,d,t,uc){
  const code=uc.c,u=uc.u;
  const ci=chIdx(d,u);
  const all=[];
  if(ci>=0)CHD.c.forEach((c,k)=>{const r=c.r.find(x=>x[0]===ci);if(r)all.push({k,c,r});});
  all.forEach((w,i)=>{
   w.m=met(w.r);
   const p=i>0?all[i-1]:null;
   w.prevT=p?p.r[1]:null;
   w.dtv=(w.prevT&&w.prevT>0)?((w.r[1]-w.prevT)/w.prevT*100):null;
   w.lab=lab(w.c);
  });
  const win=all.slice(-6);

  const lq=LQR.filter(x=>x.c===code).map(x=>({camp:(LQM&&LQM.camps&&LQM.camps[x.ci])||('Round '+(x.ci+1)),r:x.r,ci:x.ci,q:x}))
   .sort((a,b)=>a.ci-b.ci);

  const pm=[];
  PCM.r.forEach(a=>{
   if(String(a[4])!==String(code))return;
   const ds=PCM.ds[a[0]]||{};
   const o={di:a[0],lab:ds.n||('Round '+a[0]),q:ds.q||'',s:ds.s,type:(typeof PMSRC!=='undefined'?PMSRC[ds.s]:'')||'',
    cl:a[5]||0,hh:a[6]||0,chk:a[7]||0,fm:a[8]||0,ms:a[9]||0,nt:a[10]||0,tv:a[11]||0,na:a[12]||0,
    rf:a[13]||0,sl:a[14]||0,ot:a[15]||0,zd:a[16]||0,fk:a[17]||0,rc:a[25]||0,rv:a[26]||0};
   o.fmp=o.chk?o.fm/o.chk*100:null; o.msp=o.chk?o.ms/o.chk*100:null; o.rcp=o.rc?o.rv/o.rc*100:null;
   pm.push(o);
  });

  let afu=-1,recs=[];
  if(AF){afu=AF.ucs.findIndex(x=>String(x[0])===String(code)); if(afu>=0)recs=AF.r.filter(x=>x[2]===afu);}
  const yrs=[...new Set(recs.map(x=>x[0]))].sort();
  const afY=yrs.map(y=>{
   const g=recs.filter(x=>x[0]===y),n=g.length;
   const c1=g.filter(x=>x[6]===1).length,c2=g.filter(x=>x[6]===2).length,c3=g.filter(x=>x[6]===3).length,c0=g.filter(x=>x[6]===0).length;
   const adq=g.filter(x=>x[5]===1).length,n7=g.filter(x=>x[9]===1).length,n7u=g.filter(x=>x[9]>=0).length;
   const i2=g.filter(x=>x[10]===1).length,i2u=g.filter(x=>x[10]>=0).length,s2=g.filter(x=>x[11]>=2).length;
   return {y,n,c1,c2,c3,c0,adqp:n?adq/n*100:null,n7p:n7u?n7/n7u*100:null,i2p:i2u?i2/i2u*100:null,s2p:n?s2/n*100:null};
  });
  const mon26=[]; const y26=recs.filter(x=>x[0]===2026);
  for(let m=1;m<=12;m++){const g=y26.filter(x=>x[1]===m);if(g.length)mon26.push({m,n:g.length,p:g.filter(x=>x[6]===0).length});}
  const npx=(AF&&AF.np)?AF.np.filter(x=>String(x[0]).toUpperCase()===String(d).toUpperCase()):[];
  const np26=npx.filter(x=>x[1]===2026);

  const wpvU=(typeof WPV!=='undefined'?WPV:[]).filter(w=>String(w.c)===String(code));
  const wpvH=(typeof WPVH!=='undefined'?WPVH:[]).filter(w=>String(w.c)===String(code));
  const wpvD=(typeof WPV!=='undefined'?WPV:[]).filter(w=>w.d===d);
  const wpvD26=wpvD.filter(w=>String(w.on).slice(0,4)==='2026');
  const wpvKP26=(typeof WPV!=='undefined'?WPV:[]).filter(w=>String(w.on).slice(0,4)==='2026');

  const z=ZD.find(x=>String(x.c)===String(code))||ZD.find(x=>NS(x.u)===NS(u)&&x.d===d)||null;
  const ei=EPI.findIndex(x=>String(x.c)===String(code));
  const e=ei>=0?EPI[ei]:null;
  const dAgg=aggE(EPI.filter(x=>x.d===d)), kpAgg=aggE(EPI);
  const hasUC=typeof EPIUC!=='undefined'&&EPIUC&&EPIUC.rows&&EPIUC.rows.length===EPI.length;

  const P={dv,d,t,u,code,ci,all,win,lq,pm,afu,recs,yrs,afY,mon26,npx,np26,wpvU,wpvH,wpvD26,wpvKP26,z,ei,e,dAgg,kpAgg,hasUC};
  P.rl=recos(P);
  return P;
 }

 // ---------- recommendations ----------
 function recos(O){
  const R=[]; const w=O.win;
  if(!w.length)
   R.push(['crit','No campaign record for this UC','The campaign template carries no target or coverage row for this council, so the six-round triangulation cannot be built.','Confirm the UC name and code against the micro-plan before briefing.']);
  else{
   const latest=w[w.length-1];
   const cov=w.map(x=>x.m.covp).filter(v=>v!=null);
   const recp=w.map(x=>x.m.recp).filter(v=>v!=null);
   const sdc=w.map(x=>x.m.sdcp).filter(v=>v!=null);
   const rc=w.map(x=>x.m.rcp).filter(v=>v!=null);
   const over=cov.filter(v=>v>110).length;
   if(cov.length&&over>=Math.max(2,Math.ceil(cov.length/2)))
    R.push(['warn','Administrative target sits below the vaccinated count',
     'Coverage passed 110% in '+over+' of '+cov.length+' rounds (latest '+PC(latest.m.covp)+', range '+PC(MN(cov))+'–'+PC(MX(cov))+'). That is a target or denominator problem, not extra reach.',
     'Reconcile the UC target with the micro-plan and the household count before the next round; a low denominator hides unvaccinated children.']);
   if(recp.length&&avg(recp)>=12)
    R.push(['crit','Roughly one in eight target children is recorded missed every round',
     'Recorded missed averaged '+PC(avg(recp))+' of target across '+recp.length+' rounds (latest '+PC(latest.m.recp)+', '+F(latest.m.rec)+' children).',
     'Audit the missed-children register UC by UC: who was listed, who was found, and why the same children stay listed.']);
   if(sdc.length&&avg(sdc)<50)
    R.push(['warn','Same-day sweep recovers under half of the recorded missed list',
     'Same-day coverage averaged '+PC(avg(sdc))+' of recorded missed children (latest '+F(latest.m.sdc)+' of '+F(latest.m.rec)+').',
     'Re-brief the sweep team on the 48-hour rule and hold a same-day review of the missed list at the UC control room.']);
   if(rc.length&&(avg(rc)<90||(latest.m.rcp!=null&&latest.m.rcp<90)))
    R.push(['crit','Intra-campaign recall verification is below the 90% line',
     'ICM recall averaged '+PC(avg(rc))+' (latest '+PC(latest.m.rcp)+'; children seen '+PC(latest.m.snp)+' in '+F(latest.m.clu)+' clusters).',
     'Re-train supervisors on the recall check and require cluster-level recall above 90% before a UC closes.']);
   const lqLast=O.lq.length?O.lq[0]:null;
   const lqp=w.map(x=>x.m.lqp).filter(v=>v!=null);
   if((lqLast&&lqLast.r==='F')||(lqp.length&&lqp[lqp.length-1]<80))
    R.push(['crit','Lot quality assessment failed the latest round',
     (lqLast?('Lot result '+lqLast.r+' in '+lqLast.camp+' with '+F(lqLast.q.tt)+' children missed ('+F(lqLast.q.tm)+' team-missed, '+F(lqLast.q.dn)+' not visited, '+F(lqLast.q.rf)+' refusal).'):('LQAS '+PC(lqp[lqp.length-1])+' in the latest round.')),
     'Treat the lot as failed: repeat the sweep in the same houses and re-assess a fresh lot before declaring the UC covered.']);
   if(w.map(x=>x.m.msp).every(v=>v==null))
    R.push(['warn','Market survey return is blank for this UC',
     'None of the last '+w.length+' campaign rows carries a market survey percentage.',
     'Confirm whether a market survey was conducted; if not, add the UC to the next round\'s market-survey sample.']);
   const lqs=w.map(x=>x.m.lqp);
   if(lqs.every(v=>v==null))
    R.push(['note','LQAS did not assess this UC in the six rounds',
     'No lot result is attached to any of the last '+w.length+' campaign rows for this council.',
     'Include the UC in the next round\'s lot sampling; without it there is no independent quality read.']);
  }
  if(!O.pm.some(x=>x.s>=1))
   R.push(['warn','No post-campaign household check covers this UC',
    'The payload holds '+O.pm.length+' in-campaign ICM round(s) for this UC and no post-campaign PCM or PCHS round.',
    'Add the UC to the post-campaign monitoring sample so the ICM finding can be verified independently.']);
  if(O.z){
   const zc=[O.z.pA,O.z.pM,O.z.pS].filter(v=>v!=null);
   const lastZ=O.z.pS!=null?O.z.pS:O.z.pM;
   const zlbl=O.z.pS!=null?'Sept 2026':(O.z.pM!=null?'May 2026':'Apr 2026');
   const prevZ=O.z.pS!=null?O.z.pM:(O.z.pM!=null?O.z.pA:null);
   const zDrop=(prevZ!=null&&lastZ!=null)?lastZ-prevZ:null;
   const zSeq=[['April',O.z.pA],['May',O.z.pM],['Sept',O.z.pS]].filter(x=>x[1]!=null).map(x=>x[0]+' '+PC(x[1])).join(' → ');
   if(lastZ!=null&&lastZ<50)
    R.push(['crit','Zero-dose register coverage is '+PC(lastZ)+' in '+zlbl,
     'The register reported '+F(O.z.rS!=null?O.z.rS:O.z.rM)+' zero-dose children and covered '+F(O.z.cS!=null?O.z.cS:O.z.cM)+' in '+zlbl+'. Register path: '+zSeq+' (best of the three rounds '+PC(MX(zc))+').',
     'Trace every child on the register to a vaccination record and close the register at UC level before the next round.']);
   else if(zDrop!=null&&zDrop<=-15)
    R.push(['warn','Zero-dose register coverage fell '+Math.abs(zDrop).toFixed(1)+' points to '+PC(lastZ)+' in '+zlbl,
     'Register path: '+zSeq+'. The register still carries '+F(O.z.rS!=null?O.z.rS:O.z.rM)+' zero-dose children in '+zlbl+'.',
     'Re-check the register entries behind the fall before the next round; a drop this size usually means coverage or recording stopped, not that fewer children are zero-dose.']);
  }
  if(O.e){
   const p3=eP(O.e,'p3'),mr1=eP(O.e,'mr1');
   if(p3!=null&&p3<80)
    R.push(['crit','Routine Penta-3 coverage is '+PC(p3)+' in this UC',
     'The routine register holds '+F(O.e.p3)+' third doses against '+F(O.e.n)+' target children; the district sits at '+PC(O.dAgg.p_p3)+' and KP at '+PC(O.kpAgg.p_p3)+'.',
     'Fix the routine immunisation session plan for this UC, not only the campaign: the same children are being missed between rounds.']);
   const d13=(O.e.p1&&O.e.p3!=null)?(O.e.p1-O.e.p3)/O.e.p1*100:null;
   if(d13!=null&&d13>10)
    R.push(['warn','Penta-1 to Penta-3 dropout is '+PC(d13),
     F(O.e.p1)+' first doses against '+F(O.e.p3)+' third doses in this UC.',
     'Track the children who started and stopped; the follow-up register should carry them into the next session.']);
   const dmr=(O.e.mr1&&O.e.mr2!=null)?(O.e.mr1-O.e.mr2)/O.e.mr1*100:null;
   if(dmr!=null&&dmr>20)
    R.push(['warn','Measles second-dose dropout is '+PC(dmr),
     F(O.e.mr1)+' MR-1 against '+F(O.e.mr2)+' MR-2 doses in this UC.',
     'Schedule a measles catch-up for the UC and check MR-2 stock before the next outreach session.']);
   if(mr1!=null&&mr1<80)
    R.push(['warn','Routine MR-1 coverage is '+PC(mr1)+' in this UC',
     F(O.e.mr1)+' first measles doses against the register target; district '+PC(O.dAgg.p_mr1)+', KP '+PC(O.kpAgg.p_mr1)+'.',
     'Pair the measles catch-up with the next campaign round and confirm session attendance.']);
   if(O.e.zp!=null&&O.e.zp<80)
    R.push(['warn','Zero-dose coverage in the routine register is '+PC(O.e.zp),
     F(O.e.zr)+' children carry no antigen in this UC.',
     'Use the routine register, not only the campaign, to identify and follow these children.']);
  }
  const pend=O.afY.filter(x=>x.c0>0);
  if(pend.length)
   R.push(['crit','AFP cases at this UC are still awaiting classification',
    pend.map(x=>x.c0+' of '+x.n+' in '+x.y).join('; ')+'. The line list carries no final class for these records.',
    'Track the laboratory and ERC outcome to closure; re-read this profile once the class is final.']);
  if(O.wpvU.length||O.wpvD26.length)
   R.push(['crit','Confirmed WPV1 is on record for this area',
    (O.wpvU.length?O.wpvU.length+' WPV1 case(s) at this UC in the WPV register. ':'')+(O.wpvD26.length?O.wpvD26.length+' WPV1 case(s) in this district during 2026.':''),
    'Run the full case response: case investigation, house-to-house mop-up, and a surveillance sensitivity review around the UC.']);
  if(!R.length)R.push(['ok','No threshold breach in the rows on this card','Every indicator sits inside its benchmark for this UC.','Keep the UC in the routine review and re-read after the next round.']);
  return R;
 }

 // ---------- paint ----------
 const tagc=(v,t)=>'<span class="tag '+(t||'')+'">'+v+'</span>';
 const section=(n,title,extra)=>'<div class="tblhdr" style="margin:16px 0 6px"><h3 style="margin:0">'+n+' · '+esc(title)+'</h3><span class="cnt">'+esc(extra||'')+'</span></div>';
 const table=(head,rows)=>'<div class="scroll" style="max-height:none"><table class="gg"><thead><tr>'+head+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';

 function paint(O){
  const w=O.win, latest=w[w.length-1]||null;
  let h='<div class="pills" style="margin:4px 0 8px">'+
   tagc(esc(O.dv)+' › '+esc(O.d)+' › '+esc(O.t)+' › <b>'+esc(O.u)+'</b> · UC '+esc(O.code),'')+
   (latest?tagc('Coverage '+PC(latest.m.covp),covT(latest.m.covp)):'')+
   (latest&&latest.m.rcp!=null?tagc('ICM recall '+PC(latest.m.rcp),recT(latest.m.rcp)):'')+
   (O.lq.length?tagc('LQAS '+O.lq[0].r,lqT(O.lq[0].r)):'')+
   (O.z?tagc('ZD covered '+(O.z.pS!=null?O.z.pS:O.z.pM)+'%',(O.z.pS!=null?O.z.pS:O.z.pM)<50?'t-crit':'t-low'):'')+
   '</div>';

  // 1
  h+=section('1','Campaign triangulation — last six rounds with a row for this UC',
   w.length?('Showing '+w.length+' of '+O.all.length+' rounds on record; oldest to newest'):'No campaign row');
  if(w.length){
   const hd='<th class="gl">Indicator</th>'+w.map(x=>'<th class="n" title="'+esc(x.c.n+' · '+x.c.t)+'">'+esc(x.lab)+'</th>').join('')+'<th class="n">6-round avg</th>';
   const mean=k=>avg(w.map(x=>x.m[k]));
   const row=(t,fn,tone,mtxt,mtone)=>'<tr><td class="gl">'+t+'</td>'+
    w.map((x,i)=>'<td class="n '+(tone?tone(x.m,i):'')+'">'+fn(x.m,i,x)+'</td>').join('')+
    '<td class="n '+(mtone||'')+'">'+(mtxt==null?'–':mtxt)+'</td></tr>';
   const rows=[
    row('Administrative target',m=>F(m.t),null,F(mean('t'))),
    row('Target change vs previous round',(m,i,x)=>SG(x.dtv),null,'–'),
    row('Vaccinated',m=>F(m.cov),null,F(mean('cov'))),
    row('Coverage %',m=>PC(m.covp),m=>covT(m.covp),PC(mean('covp')),covT(mean('covp'))),
    row('Recorded missed',m=>F(m.rec),null,F(mean('rec'))),
    row('Recorded missed % of target',m=>PC(m.recp),m=>missT(m.recp),PC(mean('recp')),missT(mean('recp'))),
    row('Recorded missed — NA / refusal',m=>F(m.recN)+' / '+F(m.recR),null,'–'),
    row('Same-day covered from the missed list',m=>F(m.sdc),null,F(mean('sdc'))),
    row('Same-day covered % of recorded missed',m=>PC(m.sdcp),m=>swpT(m.sdcp),PC(mean('sdcp')),swpT(mean('sdcp'))),
    row('Still missed',m=>F(m.sm),null,F(mean('sm'))),
    row('Still missed % of target',m=>PC(m.stp),m=>misT(m.stp),PC(mean('stp')),misT(mean('stp'))),
    row('Still missed — NA / refusal',m=>F(m.sna)+' / '+F(m.srf),null,'–'),
    row('Zero-dose children recorded',m=>F(m.zd),null,F(mean('zd'))),
    row('ICM clusters',m=>m.clu?F(m.clu):'–',null,'–'),
    row('ICM recall %',m=>PC(m.rcp),m=>recT(m.rcp),PC(mean('rcp')),recT(mean('rcp'))),
    row('ICM children seen %',m=>PC(m.snp),m=>recT(m.snp),PC(mean('snp')),recT(mean('snp'))),
    row('Market survey %',m=>PC(m.msp),null,PC(mean('msp'))),
    row('LQAS %',m=>m.lqp==null?'–':PC(m.lqp),m=>m.lqp==null?'':m.lqp>=90?'t-high':m.lqp>=80?'t-low':'t-crit','–'),
    row('PCM field-monitoring %',m=>PC(m.pcmp),m=>pcmT(m.pcmp),PC(mean('pcmp')),pcmT(mean('pcmp'))),
    row('Operational flags',(m,i,x)=>flagTxt(x),null,'–')
   ];
   h+=table(hd,rows);
   const cov=w.map(x=>x.m.covp).filter(v=>v!=null);
   const rcp=w.map(x=>x.m.rcp).filter(v=>v!=null);
   const dt=w.map(x=>x.dtv).filter(v=>v!=null);
   const dtA=dt.map(Math.abs);
   h+='<div class="cap"><b>'+w.length+'-round read.</b> '+
    (cov.length?('Coverage ran '+PC(MN(cov))+'–'+PC(MX(cov))+' (mean '+PC(avg(cov))+'); '):'')+
    'recorded missed averaged '+PC(avg(w.map(x=>x.m.recp)))+
    ' of target and same-day coverage recovered '+PC(avg(w.map(x=>x.m.sdcp)))+' of that list; still missed averaged '+PC(avg(w.map(x=>x.m.stp)))+
    ' of target.'+(dtA.length?(' The target moved '+PC(avg(dtA))+' per round on average, '+PC(MX(dtA))+' at most.'):'')+
    (rcp.length?(' ICM recall averaged '+PC(avg(rcp))+' and children seen '+PC(avg(w.map(x=>x.m.snp)))+'.'):'')+
    (w.every(x=>x.m.msp==null)?' Market survey is blank in every round.':'')+
    ' Same-day % is covered ÷ recorded missed; still-missed % is still-missed children ÷ target; coverage above 100% means more children were vaccinated than the recorded target.</div>';
  } else h+='<div class="cap">No campaign row for this council in the campaign template.</div>';

  // 2
  h+=section('2','LQAS lots, in-campaign and post-campaign checks','P pass >90%, I intermediate 80–90%, F fail <80%');
  if(O.lq.length){
   const hd='<th class="gl">Round</th><th class="n">Lot result</th><th class="n">Total missed</th><th class="gl">Missed by reason</th>';
   const rows=O.lq.map(x=>{
    const why=[['tm','team missed'],['dn','not visited'],['aw','away'],['rf','refusal'],['nb','newborn'],['mg','migrant'],['ot','other']]
     .filter(p=>x.q[p[0]]).map(p=>F(x.q[p[0]])+' '+p[1]).join(', ');
    return '<tr><td class="gl">'+esc(x.camp)+'</td><td class="n '+lqT(x.r)+'">'+esc(x.r)+'</td><td class="n">'+F(x.q.tt)+'</td><td class="gl">'+esc(why||'–')+'</td></tr>';
   });
   h+=table(hd,rows);
  } else h+='<div class="cap">No LQAS lot for this UC in the payload (the portal compiles one lot per assessed UC).</div>';
  if(O.pm.length){
   const hd='<th class="gl">Monitoring round</th><th class="n">Type</th><th class="n">Clusters</th><th class="n">HH</th><th class="n">Checked</th><th class="n">FM %</th><th class="n">Missed %</th><th class="n">Recall %</th><th class="n">ZD found</th><th class="gl">Missed by reason</th>';
   const rows=O.pm.map(x=>{
    const why=[['nt','no team visit'],['tv','team missed child'],['na','away'],['rf','refusal'],['sl','asleep'],['ot','other']]
     .filter(p=>x[p[0]]).map(p=>F(x[p[0]])+' '+p[1]).join(', ');
    return '<tr><td class="gl">'+esc(x.lab)+'</td><td class="gl">'+esc(x.type)+'</td><td class="n">'+F(x.cl)+'</td><td class="n">'+F(x.hh)+'</td><td class="n">'+F(x.chk)+
     '</td><td class="n '+pcmT(x.fmp)+'">'+PC(x.fmp)+'</td><td class="n">'+PC(x.msp)+'</td><td class="n '+recT(x.rcp)+'">'+PC(x.rcp)+'</td><td class="n">'+F(x.zd)+'</td><td class="gl">'+esc(why||'–')+'</td></tr>';
   });
   h+=table(hd,rows);
   h+='<div class="cap">FM % = finger-marked children among those checked (target 95%+); recall % = children verified vaccinated among recall checks (target 90%+); ZD found = zero-dose children identified during the round.</div>';
  } else h+='<div class="cap">No ICM, PCM or PCHS round in the payload covers this UC.</div>';

  // 3
  h+=section('3','Surveillance — AFP register at this UC',AF?('Line list '+AF.src+', latest onset '+AF.asof+', '+fmt(AF.n)+' KP cases'):'AFP line list not loaded');
  if(O.afY.length){
   const hd='<th class="n">Year</th><th class="n">AFP cases</th><th class="n">WPV1</th><th class="n">VDPV</th><th class="n">Discarded</th><th class="n">Pending</th><th class="n">Stool adequate</th><th class="n">Notified ≤7d</th><th class="n">Investigated ≤2d</th>';
   const rows=O.afY.map(x=>'<tr><td class="n">'+x.y+'</td><td class="n">'+F(x.n)+'</td><td class="n '+(x.c1?'t-crit':'')+'">'+F(x.c1)+'</td><td class="n '+(x.c2?'t-low':'')+'">'+F(x.c2)+'</td><td class="n">'+F(x.c3)+'</td><td class="n '+(x.c0?'t-crit':'')+'">'+F(x.c0)+'</td><td class="n">'+PC(x.adqp)+'</td><td class="n">'+PC(x.n7p)+'</td><td class="n">'+PC(x.i2p)+'</td></tr>');
   h+=table(hd,rows);
   h+='<div class="cap">One row per AFP case in the four-year line list, reduced to count fields — no name, address, EPID or lab number is published. Pending = the sheet carries no final class. Timeliness is measured from the onset date over the cases that carry both dates.</div>';
  } else h+='<div class="cap">The line list carries no AFP case with this UC code.</div>';
  if(O.mon26.length)
   h+='<div class="cap"><b>2026 onset by month:</b> '+O.mon26.map(x=>MON[x.m-1]+' '+F(x.n)+(x.p?' ('+F(x.p)+' pending)':'')).join(' · ')+'.</div>';
  const wpvLast=O.wpvKP26.map(w=>String(w.on||'')).filter(Boolean).sort().pop();
  const wpvLastTxt=(wpvLast&&wpvLast.length>=7)?(MON[(+wpvLast.slice(5,7))-1]+' '+wpvLast.slice(0,4)):null;
  h+='<div class="cap"><b>This UC:</b> '+(O.wpvU.length?O.wpvU.length+' WPV1 case(s) in the WPV register; ':'no WPV1 case in the WPV register; ')+
   (O.wpvH.length?('historical WPV onset(s) '+A(O.wpvH.map(x=>x.on))):'no historical WPV onset')+
   '. <b>District '+esc(O.d)+':</b> '+F(O.wpvD26.length)+' WPV1 case(s) in 2026'+
   (O.np26.length?('; '+F(O.np26.reduce((s,x)=>s+x[2],0))+' AFP case(s) registered without a UC, '+F(O.np26.reduce((s,x)=>s+x[3],0))+' pending'):'')+
   '. <b>Province:</b> '+F(O.wpvKP26.length)+' WPV1 case(s) in 2026 across KP'+
   (wpvLastTxt?' (register covers onsets up to '+wpvLastTxt+'; a case confirmed after that shows here only once the register is refreshed)':'')+'.</div>';
  const pend26=(O.afY.find(x=>x.y===2026)||{}).c0||0;
  h+='<div class="cap" style="background:var(--color-warning-bg);color:var(--color-warning-text);padding:8px 12px;border-radius:6px"><b>Classification caveat.</b> '+
   (pend26>0?('The 2026 sheet carries '+F(pend26)+' record(s) at this UC with no final class, so they are waiting on the laboratory and ERC rather than confirmed or discarded. '):'')+
   'A programme-confirmed WPV1 case is read against the EOC case file; the register above is the surveillance denominator around it.</div>';

  // 4
  h+=section('4','Zero-dose recording and coverage','Digitization register (ZD), 2026 campaigns');
  if(O.z){
   const zr=[['Apr 2026',O.z.rA,O.z.cA,O.z.pA,O.z.bA],['May 2026',O.z.rM,O.z.cM,O.z.pM,O.z.bM],['Sept 2026',O.z.rS,O.z.cS,O.z.pS,O.z.bS]];
   const hd='<th class="gl">Campaign</th><th class="n">ZD reported</th><th class="n">ZD covered</th><th class="n">Covered %</th><th class="gl">Band</th>';
   const rows=zr.map(z=>'<tr><td class="gl">'+z[0]+'</td><td class="n">'+F(z[1])+'</td><td class="n">'+F(z[2])+'</td><td class="n '+((z[3]!=null&&z[3]<50)?'t-crit':(z[3]!=null&&z[3]<80)?'t-low':'')+'">'+PC(z[3])+'</td><td class="gl">'+esc(z[4]||'–')+'</td></tr>');
   h+=table(hd,rows);
   h+='<div class="cap">Covered % = zero-dose children covered ÷ zero-dose children reported. The register\'s own April→May class is <b>'+esc(O.z.tr)+'</b> (it calls 80%+ in both of those rounds consistently good); September stands at <b>'+(O.z.pS!=null?PC(O.z.pS):'not reported')+'</b>. Bands follow the register: below 50% critical, 50–80% low, 80–90% moderate, 90–110% good, above 110% verify.</div>';
  } else h+='<div class="cap">The digitization register carries no row for this UC.</div>';
  const om=[];
  if(latest)om.push('the campaign template recorded '+F(latest.m.zd)+' zero-dose children in '+latest.lab);
  if(O.pm.length)om.push('the latest ICM round counted '+F(O.pm[0].zd)+' among the children checked');
  if(O.e&&O.e.zr!=null)om.push('the routine EPI register carries '+F(O.e.zr)+' with no antigen');
  if(om.length)h+='<div class="cap">Other records of zero dose in the same UC: '+om.join('; ')+'. The sources count different populations — compare direction, not totals.</div>';

  // 5
  const epiPer=(typeof EPIYTD!=='undefined'&&EPIYTD&&EPIYTD.per)?String(EPIYTD.per).replace(' - ',' – '):'year to date';
  h+=section('5','EPI — routine doses, coverage and dropouts','UC vs district vs KP · EPI-MIS '+epiPer);
  if(O.e){
   const keys=['bcg','opv0','opv1','opv3','p1','p3','pcv3','ipv2','rota2','mr1','mr2','tcv','fi'];
   const nm=k=>((typeof EAGK!=='undefined'&&EAGK[k]&&EAGK[k].l)?EAGK[k].l:k.toUpperCase());
   const hd='<th class="gl">Antigen</th><th class="n">UC doses</th><th class="n">UC coverage</th><th class="n">District</th><th class="n">KP</th><th class="n">UC vs KP</th>';
   const rows=keys.map(k=>{
    const pu=eP(O.e,k),pd=eP(O.dAgg,k),pk=eP(O.kpAgg,k);
    const gap=(pu!=null&&pk!=null)?pu-pk:null;
    return '<tr><td class="gl">'+esc(nm(k))+'</td><td class="n">'+F(O.e[k])+'</td><td class="n '+covT(pu)+'">'+PC(pu)+'</td><td class="n">'+PC(pd)+'</td><td class="n">'+PC(pk)+'</td><td class="n '+((gap!=null&&gap<-10)?'t-crit':(gap!=null&&gap<0)?'t-low':'')+'">'+(gap==null?'–':(gap>0?'+':'')+gap.toFixed(1)+' pts')+'</td></tr>';
   });
   rows.push('<tr><td class="gl">Zero-dose children (no antigen)</td><td class="n">'+F(O.e.zr)+'</td><td class="n '+((O.e.zp!=null&&O.e.zp<80)?'t-crit':'')+'">'+PC(O.e.zp)+'</td><td class="n">–</td><td class="n">–</td><td class="n">–</td></tr>');
   const d13=(O.e.p1&&O.e.p3!=null)?(O.e.p1-O.e.p3)/O.e.p1*100:null;
   const dmr=(O.e.mr1&&O.e.mr2!=null)?(O.e.mr1-O.e.mr2)/O.e.mr1*100:null;
   rows.push('<tr class="tot"><td class="gl">Penta-1 → Penta-3 dropout</td><td class="n">'+(d13==null?'–':F(O.e.p1-O.e.p3))+'</td><td class="n '+(d13!=null&&d13>10?'t-crit':'t-high')+'">'+PC(d13)+'</td><td class="n">'+PC(O.dAgg.d13)+'</td><td class="n">'+PC(O.kpAgg.d13)+'</td><td class="n">–</td></tr>');
   rows.push('<tr class="tot"><td class="gl">MR-1 → MR-2 dropout</td><td class="n">'+(dmr==null?'–':F(O.e.mr1-O.e.mr2))+'</td><td class="n '+(dmr!=null&&dmr>20?'t-crit':'t-high')+'">'+PC(dmr)+'</td><td class="n">'+PC(O.dAgg.dmr)+'</td><td class="n">'+PC(O.kpAgg.dmr)+'</td><td class="n">–</td></tr>');
   h+=table(hd,rows);
   const epiPerTxt=epiPer==='year to date'?'EPI-MIS year-to-date register':('EPI-MIS '+epiPer+' register');
   h+='<div class="cap">Doses and coverage come from the '+esc(epiPerTxt)+', so an October dose is not in this table. Coverage is doses ÷ the antigen target, coloured like the EPI tab (above 110% check the target, 90%+ good, 80–90% watch, below that low). Dropout is (first − last) ÷ first, shown as the children lost. District and KP are recomputed from the same register, not copied from a report. Zero-dose coverage is the register\'s own ZD indicator, not zr ÷ target.</div>';
   if(O.hasUC){
    const mo=EPIUC.mo, rowv=EPIUC.rows[O.ei], kk=EPIUC.k, mi3=kk.indexOf('p3'), mi1=kk.indexOf('mr1');
    const mons=[];
    for(let i=mo.length-1;i>=0&&mons.length<6;i--){
     if(!/^2026-/.test(mo[i].mo))continue;
     const vals=kk.map((k,j)=>rowv[j][i]||0);
     if((vals[mi3]||0)+(vals[mi1]||0)<=0)continue;
     mons.unshift({l:mo[i].l,row:vals});
    }
    if(mons.length){
     const sub=['p3','mr1','mr2','fi'];
     const hd2='<th class="gl">Month (UC-wise export)</th><th class="n">Target</th>'+sub.map(k=>'<th class="n">'+esc(nm(k))+'</th>').join('');
     const rows2=mons.map(x=>'<tr><td class="gl">'+esc(x.l)+'</td><td class="n">'+F(x.row[kk.indexOf('n')])+'</td>'+sub.map(k=>'<td class="n">'+F(x.row[kk.indexOf(k)])+'</td>').join('')+'</tr>');
     h+='<div class="cap" style="margin-top:10px"><b>Last '+mons.length+' reported 2026 months for this UC</b> — EPIUC archive, '+esc(EPIUC.per)+'.</div>'+table(hd2,rows2);
    }
   }
  } else h+='<div class="cap">No routine EPI register row for this UC.</div>';

  // 6
  h+=section('6','Recommendations from the indicators above',O.rl.length+' trigger(s)');
  h+='<div>'+O.rl.map(r=>{
   const col=r[0]==='crit'?'#dc2626':r[0]==='warn'?'#d97706':r[0]==='note'?'#0891b2':'#16a34a';
   return '<div style="border-left:3px solid '+col+';background:var(--color-bg-secondary);padding:8px 12px;margin:0 0 8px;border-radius:0 6px 6px 0">'+
    '<b style="color:'+col+'">'+esc(r[1])+'</b><div style="font-size:12.5px;color:var(--color-text-secondary);margin:3px 0">'+esc(r[2])+'</div>'+
    '<div style="font-size:12.5px"><b>Action:</b> '+esc(r[3])+'</div></div>';
  }).join('')+'</div>';
  h+='<div class="cap">Every trigger is computed from the rows on this card when the UC is selected. Thresholds are the dashboard\'s own: coverage 90/80, ICM recall and seen 90/80, PCM field monitoring 95/90, still missed 2/5% of target, LQAS 90/80, Penta dropout 10%, MR-2 dropout 20%.</div>';

  el('wpvBody').innerHTML=h;
  if(el('wpvCnt'))el('wpvCnt').textContent=O.d+' · '+O.u+' · '+O.code;
 }

 function flagTxt(x){
  const f=[]; const m=x.m;
  if(m.covp!=null&&m.covp>110)f.push('target<vacc');
  if(m.recp!=null&&m.recp>=14)f.push('missed '+m.recp.toFixed(0)+'%');
  if(m.sdcp!=null&&m.sdcp<40)f.push('sweep<40%');
  if(m.rcp!=null&&m.rcp<85)f.push('recall<85');
  if(m.lqp!=null&&m.lqp<80)f.push('LQAS fail');
  if(m.msp==null)f.push('no MS');
  return f.length?esc(f.join('; ')):'–';
 }

 // ---------- csv ----------
 function csv(O){
  const H=['Section','Indicator','Round / year','Value','Note'], rows=[];
  rows.push(['Profile','Division',O.dv,'','']);
  rows.push(['Profile','District',O.d,'','']);
  rows.push(['Profile','Tehsil',O.t,'','']);
  rows.push(['Profile','UC',O.u,'',O.code]);
  O.win.forEach(x=>{
   const m=x.m;
   [['Administrative target',m.t],['Target change % vs previous round',x.dtv],['Vaccinated',m.cov],['Coverage %',m.covp],
    ['Recorded missed',m.rec],['Recorded missed % of target',m.recp],['Recorded missed NA',m.recN],['Recorded missed refusal',m.recR],
    ['Same-day covered',m.sdc],['Same-day % of recorded missed',m.sdcp],['Still missed',m.sm],['Still missed % of target',m.stp],
    ['Still missed NA',m.sna],['Still missed refusal',m.srf],['Zero-dose recorded',m.zd],['ICM clusters',m.clu],['ICM recall %',m.rcp],
    ['ICM seen %',m.snp],['Market survey %',m.msp],['LQAS %',m.lqp],['PCM FM %',m.pcmp]]
    .forEach(p=>rows.push(['Campaign',p[0],x.lab,p[1]==null?'':p[1],'']));
  });
  O.lq.forEach(x=>rows.push(['LQAS','Lot result',x.camp,x.r,'total missed '+x.q.tt]));
  O.pm.forEach(x=>{
   [['Clusters',x.cl],['Households',x.hh],['Children checked',x.chk],['FM %',x.fmp],['Missed %',x.msp],['Recall %',x.rcp],['Zero-dose found',x.zd],['Fake FM',x.fk]]
    .forEach(p=>rows.push(['Monitoring',p[0],x.lab,p[1]==null?'':p[1],x.type]));
  });
  O.afY.forEach(x=>{
   [['AFP cases',x.n],['WPV1',x.c1],['VDPV',x.c2],['Discarded',x.c3],['Pending',x.c0],['Stool adequate %',x.adqp],['Notified <=7d %',x.n7p],['Investigated <=2d %',x.i2p]]
    .forEach(p=>rows.push(['Surveillance',p[0],x.y,p[1]==null?'':p[1],'']));
  });
  O.mon26.forEach(x=>rows.push(['Surveillance','Onset month 2026',MON[x.m-1]+' 2026',x.n,x.p+' pending']));
  if(O.z){
   [['Apr 2026',O.z.rA,O.z.cA],['May 2026',O.z.rM,O.z.cM],['Sept 2026',O.z.rS,O.z.cS]].forEach(p=>{
    rows.push(['Zero dose','ZD reported',p[0],p[1]==null?'':p[1],'']);
    rows.push(['Zero dose','ZD covered',p[0],p[2]==null?'':p[2],'']);
   });
  }
  if(O.e){
   ['bcg','opv0','opv1','opv3','p1','p3','pcv3','ipv2','rota2','mr1','mr2','tcv','fi'].forEach(k=>{
    rows.push(['EPI',k+' doses','UC',O.e[k],'']);
    rows.push(['EPI',k+' coverage %','UC',eP(O.e,k),'']);
   });
   rows.push(['EPI','zero-dose children','UC',O.e.zr,'']);
   rows.push(['EPI','zero-dose coverage %','UC',O.e.zp,'']);
  }
  O.rl.forEach(r=>rows.push(['Recommendation',r[0],r[1],'',r[2]+' Action: '+r[3]]));
  const safe=s=>String(s).replace(/[^A-Za-z0-9]+/g,'_');
  csvDownload('wpv1_case_profile_'+safe(O.d)+'_'+safe(O.u)+'_'+O.code+'.csv',H,rows.map(r=>r.map(c=>c==null?'':c)));
 }

 // ---------- draw ----------
 function draw(){
  const body=el('wpvBody'); if(!body)return;
  const ucS=el('wpvUc'); const code=ucS?ucS.value:'';
  if(!code){
   cur=null;
   body.innerHTML='<div class="cap">Select division, district, tehsil and UC to build the confirmed-case profile. Every table, the flags and the recommendations are recalculated for the selected council.</div>';
   if(el('wpvCnt'))el('wpvCnt').textContent='';
   if(el('wpvCsv'))el('wpvCsv').disabled=true;
   return;
  }
  const g=geo(),dv=el('wpvDiv').value,d=el('wpvDist').value,t=el('wpvTeh').value;
  const uc=(g.U[dv+'|'+d+'|'+t]||[]).filter(x=>x.c===code)[0];
  if(!uc){body.innerHTML='<div class="cap">That UC is no longer in the EPI register.</div>';return;}
  let P=null;
  try{P=build(dv,d,t,uc);paint(P);cur=P;}
  catch(e){body.innerHTML='<div class="cap">Profile could not be rendered: '+esc(e&&e.message?e.message:e)+'</div>';cur=null;}
  if(el('wpvCsv'))el('wpvCsv').disabled=!cur;
 }

 return {init:init,draw:draw};
})();
WPVC.init();
/* WPVPROF:JS:END */
