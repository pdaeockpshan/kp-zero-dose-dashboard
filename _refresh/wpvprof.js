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
  if(el('wpvXls'))el('wpvXls').onclick=()=>{if(cur)xls(cur);};
  if(el('wpvPptx'))el('wpvPptx').onclick=()=>{if(cur)deck(cur);};
  [['wpvCsv','download'],['wpvXls','table'],['wpvPptx','present'],['wpvReset','swap']].forEach(pair=>{
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
     (lqLast?('Lot result '+lqWord(lqLast.r)+' in '+lqLast.camp+' with '+F(lqLast.q.tt)+' '+(lqLast.q.tt===1?'child':'children')+' missed ('+F(lqLast.q.tm)+' team-missed, '+F(lqLast.q.dn)+' not visited, '+F(lqLast.q.rf)+' '+(lqLast.q.rf===1?'refusal':'refusals')+').'):('LQAS '+PC(lqp[lqp.length-1])+' in the latest round.')),
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
   (O.lq.length?tagc('LQAS '+lqWord(O.lq[0].r),lqT(O.lq[0].r)):'')+
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
  h+=section('2','LQAS lots, in-campaign and post-campaign checks','Pass >90%, Intermediate 80–90%, Fail <80%');
  if(O.lq.length){
   const hd='<th class="gl">Round</th><th class="n">Lot result</th><th class="n">Total missed</th><th class="gl">Missed by reason</th>';
   const rows=O.lq.map(x=>{
    const why=[['tm','team missed'],['dn','not visited'],['aw','away'],['rf','refusal'],['nb','newborn'],['mg','migrant'],['ot','other']]
     .filter(p=>x.q[p[0]]).map(p=>F(x.q[p[0]])+' '+p[1]).join(', ');
    return '<tr><td class="gl">'+esc(x.camp)+'</td><td class="n '+lqT(x.r)+'">'+esc(lqWord(x.r))+'</td><td class="n">'+F(x.q.tt)+'</td><td class="gl">'+esc(why||'–')+'</td></tr>';
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
  O.lq.forEach(x=>rows.push(['LQAS','Lot result',x.camp,lqWord(x.r),'total missed '+x.q.tt]));
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

 // ---------- workbook ----------
 const agn=k=>((typeof EAGK!=='undefined'&&EAGK[k]&&EAGK[k].l)?EAGK[k].l:k.toUpperCase());
 const sfx=s=>String(s).replace(/[^A-Za-z0-9]+/g,'_');
 const stem=O=>'wpv1_case_profile_'+sfx(O.d)+'_'+sfx(O.u)+'_'+O.code;
 const updTxt=()=>{const t=(el('hUpd')||{}).textContent||'';return String(t).replace(/^Updated\s*/,'').trim();};
 const epiPer=()=>(typeof EPIYTD!=='undefined'&&EPIYTD&&EPIYTD.per)?String(EPIYTD.per).replace(' - ',' – '):'year to date';

 function flagRaw(x){
  const f=[];const m=x.m;
  if(m.covp!=null&&m.covp>110)f.push('target<vacc');
  if(m.recp!=null&&m.recp>=14)f.push('missed '+m.recp.toFixed(0)+'%');
  if(m.sdcp!=null&&m.sdcp<40)f.push('sweep<40%');
  if(m.rcp!=null&&m.rcp<85)f.push('recall<85');
  if(m.lqp!=null&&m.lqp<80)f.push('LQAS fail');
  if(m.msp==null)f.push('no MS');
  return f.join('; ');
 }
 function xlProfile(O){
  const w=O.win,latest=w[w.length-1]||null;
  const cov=w.map(x=>x.m.covp).filter(v=>v!=null);
  const rc=w.map(x=>x.m.rcp).filter(v=>v!=null);
  const c0=(O.afY.find(x=>x.y===2026)||{}).c0||0;
  const r1=v=>v==null?null:+(+v).toFixed(1);
  const rows=[
   ['Division',O.dv],['District',O.d],['Tehsil',O.t],['Union council',O.u],['UC code',O.code],
   ['Campaign rounds on record',O.all.length],
   ['Rounds shown (most recent six with a row)',w.length],
   ['Latest campaign row',latest?latest.lab:'–'],
   ['Coverage, latest round %',latest?r1(latest.m.covp):null],
   ['Coverage, mean of the rounds shown %',r1(avg(cov))],
   ['ICM recall, latest round %',latest?r1(latest.m.rcp):null],
   ['ICM recall, mean of the rounds shown %',r1(avg(rc))],
   ['LQAS lot, latest',O.lq.length?(lqWord(O.lq[0].r)+' · '+O.lq[0].camp):'none'],
   ['Zero-dose covered %, Sept 2026',O.z?r1(O.z.pS):null],
   ['WPV1 cases at this UC (WPV register)',O.wpvU.length],
   ['WPV1 cases in this district, 2026',O.wpvD26.length],
   ['WPV1 cases across KP, 2026',O.wpvKP26.length],
   ['AFP cases at this UC awaiting classification, 2026',c0],
   ['AFP register',AF?(AF.src+' · onsets to '+AF.asof):'not loaded'],
   ['Campaign source','CHD — EOC campaign template, one row per UC per round'],
   ['Zero-dose source','ZD — digitization register, 2026 campaigns (Apr, May, Sept)'],
   ['Routine EPI period',epiPer()],
   ['Routine EPI archive',(typeof EPIUC!=='undefined'&&EPIUC)?String(EPIUC.per):''],
   ['Recommendations triggered',O.rl.length],
   ['Data stamp',updTxt()||'–'],
   ['Made',new Date().toLocaleString()]
  ];
  return {sheet:'Profile',H:['Field','Value'],rows:rows.map(r=>[r[0],r[1]==null?'':r[1]])};
 }
 function xlCamps(O){
  const w=O.win,H=['Indicator'].concat(w.map(x=>x.lab),['6-round avg']);
  const mean=k=>avg(w.map(x=>x.m[k]));
  const r=(name,fn,mk)=>[name].concat(w.map((x,i)=>fn(x.m,i,x)),[mk===undefined?null:mk]);
  const rows=[
   r('Administrative target',m=>m.t,mean('t')),
   r('Target change % vs previous round',(m,i,x)=>x.dtv,null),
   r('Vaccinated',m=>m.cov,mean('cov')),
   r('Coverage %',m=>m.covp,mean('covp')),
   r('Recorded missed',m=>m.rec,mean('rec')),
   r('Recorded missed % of target',m=>m.recp,mean('recp')),
   r('Recorded missed — NA',m=>m.recN,null),
   r('Recorded missed — refusal',m=>m.recR,null),
   r('Same-day covered',m=>m.sdc,mean('sdc')),
   r('Same-day covered % of recorded missed',m=>m.sdcp,mean('sdcp')),
   r('Still missed',m=>m.sm,mean('sm')),
   r('Still missed % of target',m=>m.stp,mean('stp')),
   r('Still missed — NA',m=>m.sna,null),
   r('Still missed — refusal',m=>m.srf,null),
   r('Zero-dose children recorded',m=>m.zd,mean('zd')),
   r('ICM clusters',m=>m.clu||null,null),
   r('ICM recall %',m=>m.rcp,mean('rcp')),
   r('ICM children seen %',m=>m.snp,mean('snp')),
   r('Market survey %',m=>m.msp,mean('msp')),
   r('LQAS %',m=>m.lqp,mean('lqp')),
   r('PCM field-monitoring %',m=>m.pcmp,mean('pcmp')),
   r('Operational flags',(m,i,x)=>flagRaw(x)||null,null)
  ];
  return {sheet:'Campaign rounds',H,rows};
 }
 function xlLq(O){
  const H=['Round','Lot result','Total missed','Team missed','Not visited','Away','Refusal','Newborn','Migrant','Other'];
  const rows=O.lq.map(x=>[x.camp,lqWord(x.r),x.q.tt,x.q.tm,x.q.dn,x.q.aw,x.q.rf,x.q.nb,x.q.mg,x.q.ot]);
  return {sheet:'LQAS lots',H,rows};
 }
 function xlMon(O){
  const H=['Monitoring round','Type','Clusters','Households','Children checked','FM %','Missed %','Recall %','Zero-dose found','No team visit','Team missed','Away','Refusal','Asleep','Other'];
  const rows=O.pm.map(x=>[x.lab,x.type,x.cl,x.hh,x.chk,x.fmp,x.msp,x.rcp,x.zd,x.nt,x.tv,x.na,x.rf,x.sl,x.ot]);
  return {sheet:'Post-campaign checks',H,rows};
 }
 function xlAf(O){
  const H=['Year','AFP cases','WPV1','VDPV','Discarded','Pending','Stool adequate %','Notified ≤7d %','Investigated ≤2d %'];
  const rows=O.afY.map(x=>[x.y,x.n,x.c1,x.c2,x.c3,x.c0,x.adqp,x.n7p,x.i2p]);
  O.mon26.forEach(x=>rows.push([MON[x.m-1]+' 2026 onset','','','','','',x.n,'','']));
  return {sheet:'Surveillance',H,rows};
 }
 function xlZd(O){
  const H=['Campaign','ZD reported','ZD covered','Covered %','Band'];
  if(!O.z)return {sheet:'Zero dose',H,rows:[]};
  return {sheet:'Zero dose',H,rows:[
   ['Apr 2026',O.z.rA,O.z.cA,O.z.pA,O.z.bA],
   ['May 2026',O.z.rM,O.z.cM,O.z.pM,O.z.bM],
   ['Sept 2026',O.z.rS,O.z.cS,O.z.pS,O.z.bS]]};
 }
 function xlEpi(O){
  const H=['Antigen','UC doses','UC coverage %','District coverage %','KP coverage %','UC vs KP (pts)'];
  if(!O.e)return {sheet:'Routine EPI',H,rows:[]};
  const keys=['bcg','opv0','opv1','opv3','p1','p3','pcv3','ipv2','rota2','mr1','mr2','tcv','fi'];
  const rows=keys.map(k=>{
   const pu=eP(O.e,k),pd=eP(O.dAgg,k),pk=eP(O.kpAgg,k);
   const gap=(pu!=null&&pk!=null)?+(pu-pk).toFixed(1):null;
   return [agn(k),O.e[k],pu,pd,pk,gap];
  });
  rows.push(['Zero-dose children (no antigen)',O.e.zr,O.e.zp,null,null,null]);
  const d13=(O.e.p1&&O.e.p3!=null)?+(((O.e.p1-O.e.p3)/O.e.p1)*100).toFixed(1):null;
  const dmr=(O.e.mr1&&O.e.mr2!=null)?+(((O.e.mr1-O.e.mr2)/O.e.mr1)*100).toFixed(1):null;
  rows.push(['Penta-1 → Penta-3 dropout %',null,d13,O.dAgg.d13,O.kpAgg.d13,null]);
  rows.push(['MR-1 → MR-2 dropout %',null,dmr,O.dAgg.dmr,O.kpAgg.dmr,null]);
  return {sheet:'Routine EPI',H,rows};
 }
 function xlRec(O){
  const H=['#','Severity','Finding','Evidence','Action'];
  const rows=O.rl.map((r,i)=>[i+1,r[0]==='crit'?'Critical':r[0]==='warn'?'Warning':r[0]==='note'?'Note':'Clear',r[1],r[2],r[3]]);
  return {sheet:'Recommendations',H,rows};
 }
 function xls(O){
  if(typeof xlWrite!=='function'){toast('The Excel library is not on this page, so the CSV carries the rows');csv(O);return;}
  const b=el('wpvXls');if(b)b.disabled=true;
  const sheets=[xlProfile(O),xlCamps(O),xlLq(O),xlMon(O),xlAf(O),xlZd(O),xlEpi(O),xlRec(O)];
  toast('Building the workbook…');
  xlWrite(stem(O)+'.xlsx',sheets,false)
   .then(()=>toast('Excel workbook downloaded · '+sheets.length+' sheets'))
   .catch(()=>{toast('Excel did not load, so the same rows went out as CSV');csv(O);})
   .then(()=>{if(b)b.disabled=!cur;});
 }

 // ---------- presentation ----------
 const DK={ink:'0F172A',ink2:'1E293B',red:'B91C1C',redL:'FCA5A5',slate:'475569',mut:'94A3B8',soft:'F1F5F9',line:'E2E8F0',teal:'0E7490',amb:'D97706',grn:'15803D'};
 const sevCol=s=>s==='crit'?DK.red:s==='warn'?DK.amb:s==='note'?DK.teal:DK.grn;
 const sevLbl=s=>s==='crit'?'CRITICAL':s==='warn'?'WARNING':s==='note'?'NOTE':'ON TRACK';
 function dHead(s,p,no,title,sub,total){
  s.background={color:'FFFFFF'};
  s.addShape(p.ShapeType.rect,{x:0,y:0,w:13.333,h:0.14,fill:{color:DK.red},line:{color:DK.red}});
  s.addText(String(no).padStart(2,'0'),{x:0.5,y:0.42,w:0.7,h:0.4,fontFace:'Segoe UI',fontSize:13,bold:true,color:DK.red});
  s.addText(title,{x:1.14,y:0.38,w:11.7,h:0.5,fontFace:'Segoe UI',fontSize:22,bold:true,color:DK.ink,fit:'shrink'});
  if(sub)s.addText(sub,{x:1.14,y:0.9,w:11.7,h:0.3,fontFace:'Segoe UI',fontSize:10.5,color:DK.slate});
  s.addShape(p.ShapeType.rect,{x:0.5,y:1.3,w:12.33,h:0.014,fill:{color:DK.line},line:{color:DK.line}});
  s.addText('KP Polio and Synergy Dashboard · WPV1 confirmed-case profile',{x:0.5,y:7.16,w:9.5,h:0.22,fontFace:'Segoe UI',fontSize:8,color:DK.mut});
  s.addText(no+' / '+total,{x:11.8,y:7.16,w:1.03,h:0.22,fontFace:'Segoe UI',fontSize:8,color:DK.mut,align:'right'});
 }
 function dTable(s,p,hh,rows,o){
  const tv=c=>((c&&typeof c==='object'&&c.text!=null)?c.text:c);
  const t2=v=>v==null?'':String(v).trim();
  const numpat=/^[+\-]?(?:(?:\d{1,3}(?:,\d{3})+)|\d+)(?:\.\d+)?%?$/;
  const skip=v=>v===''||v==='–';
  const right=hh.map((_,j)=>{
   let num=0,txt=0;
   rows.forEach(r=>{const v=t2(tv(r[j]));if(skip(v))return;if(numpat.test(v))num++;else txt++;});
   const yr=rows.every(r=>{const v=t2(tv(r[j]));return skip(v)||/^\d{4}$/.test(v);});
   return num>0&&!yr&&num/(num+txt)>=0.6;
  });
  const H=hh.map((h,j)=>({text:h,options:{bold:true,color:'FFFFFF',fill:{color:o.head||DK.red},fontSize:8.5,align:right[j]?'right':'left'}}));
  const body=rows.map((r,ri)=>r.map((c,j)=>{
   const obj=(c&&typeof c==='object'&&c.text!=null);
   const cell=obj?c:{text:(c==null?'–':String(c)),options:{}};
   cell.options=Object.assign({fontSize:o.fs||8.5,color:DK.ink,fill:{color:ri%2?'FFFFFF':DK.soft},align:right[j]?'right':'left'},cell.options);
   return cell;
  }));
  const colW=o.colW||hh.map(()=>o.w/hh.length);
  s.addTable([H].concat(body),{x:o.x||0.5,y:o.y,w:o.w||12.33,colW,rowH:o.rowH||0.26,border:{type:'solid',pt:0.5,color:DK.line},fontFace:'Segoe UI',valign:'middle',margin:0.045,autoPage:false});
 }
 function dKpi(s,p,x,y,w,h,label,val,tone){
  s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:0.06,fill:{color:DK.ink2},line:{color:DK.ink2}});
  s.addText(label,{x:x+0.12,y:y+0.1,w:w-0.24,h:0.26,fontFace:'Segoe UI',fontSize:8.5,color:DK.mut});
  s.addText(val==null?'–':val,{x:x+0.12,y:y+0.33,w:w-0.24,h:h-0.42,fontFace:'Segoe UI',fontSize:21,bold:true,color:tone||'FFFFFF',fit:'shrink'});
}
 function ucGeo(O){
  try{
   const g=(typeof KPGEO==='string')?JSON.parse(KPGEO):KPGEO, ds=(g&&g.d)||[], vb=(g&&g.vb)||[706.2,1000];
   const dn=NS(O.d);
   const sel=ds.find(x=>NS(x.c)===dn)||ds.find(x=>{const n=NS(x.c);return n.length>=5&&dn.length>=5&&(n===dn||n.indexOf(dn)===0||dn.indexOf(n)===0);});
   return sel?{ds,sel,vb}:null;
  }catch(e){return null;}
 }
 function mapSVG(O){
  const m=ucGeo(O); if(!m)return null;
  const ds=m.ds,sel=m.sel,vb=m.vb;
  const paths=ds.map(x=>'<path d="'+x.p+'" fill="'+(x===sel?'#B91C1C':'#22314A')+'" stroke="'+(x===sel?'#FCA5A5':'#3B4A63')+'" stroke-width="'+(x===sel?5:2.5)+'" stroke-linejoin="round"/>').join('');
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+vb[0]+'" height="'+vb[1]+'" viewBox="0 0 '+vb[0]+' '+vb[1]+'">'+paths+
   '<circle cx="'+sel.x+'" cy="'+sel.y+'" r="10" fill="#FFFFFF" stroke="#B91C1C" stroke-width="5"/></svg>';
 }
 function mapImage(O){
  return new Promise(res=>{
   const svg=mapSVG(O);
   if(!svg||typeof Image==='undefined'||typeof document==='undefined'||!document.createElement)return res(null);
   try{
    const img=new Image(), g=(typeof KPGEO==='string')?JSON.parse(KPGEO):KPGEO, vb=(g&&g.vb)||[706.2,1000];
    const W=780, H=Math.round(W*vb[1]/vb[0]);
    img.onload=()=>{try{
     const c=document.createElement('canvas'); c.width=W; c.height=H;
     const x=c.getContext('2d'); x.fillStyle='#14203A'; x.fillRect(0,0,W,H); x.drawImage(img,0,0,W,H);
     res(c.toDataURL('image/png'));
    }catch(e){res(null);}};
    img.onerror=()=>res(null);
    img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
   }catch(e){res(null);}
  });
 }
 function lqWord(r){return r==='F'?'Fail':(r==='P'?'Pass':(r==null?'–':String(r)));}
 function buildDeck(O,MAPIMG){
  const ppt=new window.PptxGenJS();
  ppt.layout='LAYOUT_WIDE';
  ppt.author='KP Polio and Synergy Dashboard';
  ppt.company='KP EOC · PEI Synergy';
  ppt.title='WPV1 confirmed-case profile · '+O.u+' · '+O.d;
  ppt.subject='Campaign triangulation, surveillance, zero dose, routine EPI and recommendations for UC '+O.code;
  const w=O.win,latest=w[w.length-1]||null;
  const cov=w.map(x=>x.m.covp).filter(v=>v!=null);
  const rc=w.map(x=>x.m.rcp).filter(v=>v!=null);
  const ms=w.map(x=>x.m.msp).filter(v=>v!=null);
  const lq=w.map(x=>x.m.lqp).filter(v=>v!=null);
  const dtA=w.map(x=>x.dtv).filter(v=>v!=null).map(Math.abs);
  const lqLast=O.lq.length?O.lq[0]:null;
  const zPct=O.z?(O.z.pS!=null?O.z.pS:O.z.pM):null;
  const zLbl=O.z?(O.z.pS!=null?'Sept 2026':(O.z.pM!=null?'May 2026':'Apr 2026')):null;
  const pend26=(O.afY.find(x=>x.y===2026)||{}).c0||0;
  const wpvLast=O.wpvKP26.map(x=>String(x.on||'')).filter(Boolean).sort().pop();
  const wpvLastTxt=(wpvLast&&wpvLast.length>=7)?(MON[(+wpvLast.slice(5,7))-1]+' '+wpvLast.slice(0,4)):null;
  const recSlides=Math.max(1,Math.ceil(O.rl.length/4));
  const total=7+recSlides+2;

  // 1 cover
  let s=ppt.addSlide();
  s.background={color:DK.ink};
  const geo=ucGeo(O);
  s.addShape(ppt.ShapeType.rect,{x:0,y:0,w:13.333,h:0.16,fill:{color:DK.red},line:{color:DK.red}});
  s.addShape(ppt.ShapeType.rect,{x:7.7,y:0,w:5.633,h:7.5,fill:{color:'14203A'},line:{color:'14203A'}});
  s.addShape(ppt.ShapeType.rect,{x:7.7,y:0,w:0.02,h:7.5,fill:{color:'2A3A57'},line:{color:'2A3A57'}});
  s.addText('SURVEILLANCE · CONFIRMED-CASE PROFILE',{x:0.7,y:0.6,w:6.6,h:0.3,fontFace:'Segoe UI',fontSize:10.5,bold:true,color:DK.mut,charSpacing:2});
  s.addText('WPV1 case profile',{x:0.7,y:0.94,w:6.7,h:0.8,fontFace:'Segoe UI',fontSize:38,bold:true,color:'FFFFFF',fit:'shrink'});
  s.addText(O.u,{x:0.7,y:1.74,w:6.6,h:0.7,fontFace:'Segoe UI',fontSize:29,bold:true,color:DK.redL,fit:'shrink'});
  s.addText(O.dv+'  ›  '+O.d+'  ›  '+O.t,{x:0.72,y:2.48,w:6.6,h:0.3,fontFace:'Segoe UI',fontSize:11.5,color:DK.mut,fit:'shrink'});
  s.addShape(ppt.ShapeType.roundRect,{x:0.7,y:2.86,w:2.05,h:0.38,rectRadius:0.19,fill:{color:'7F1D1D'},line:{color:'7F1D1D'}});
  s.addText('UC '+O.code,{x:0.7,y:2.86,w:2.05,h:0.38,fontFace:'Segoe UI',fontSize:11,bold:true,color:'FFFFFF',align:'center',valign:'middle'});
  dKpi(s,ppt,0.7,3.56,3.15,1.15,'Coverage · latest round',latest?PC(latest.m.covp):null,latest&&latest.m.covp!=null&&latest.m.covp<80?DK.redL:'FFFFFF');
  dKpi(s,ppt,4.05,3.56,3.15,1.15,'ICM recall · latest round',latest?PC(latest.m.rcp):null,latest&&latest.m.rcp!=null&&latest.m.rcp<90?DK.redL:'FFFFFF');
  dKpi(s,ppt,0.7,4.86,3.15,1.15,'Zero-dose covered · '+(zLbl||'register'),zPct!=null?PC(zPct):null,zPct!=null&&zPct<50?DK.redL:'FFFFFF');
  dKpi(s,ppt,4.05,4.86,3.15,1.15,'LQAS · latest lot',lqLast?lqWord(lqLast.r):(lq.length?PC(lq[lq.length-1]):null),lqLast&&lqLast.r==='F'?DK.redL:'FFFFFF');
  s.addText((O.wpvU.length?('Confirmed WPV1 on record at this UC. '):'No WPV1 case in the WPV register at this UC. ')+
   'Six rounds '+((w.length&&w[0].lab)||'')+' to '+((latest&&latest.lab)||'')+' · AFP line list to '+(AF?AF.asof:'–')+' · routine EPI '+epiPer()+'.',
   {x:0.7,y:6.24,w:6.65,h:0.75,fontFace:'Segoe UI',fontSize:11,color:'E2E8F0',fit:'shrink'});
  s.addText('Prepared for the core team · '+(updTxt()||new Date().toLocaleString()),{x:0.7,y:7.06,w:5.4,h:0.28,fontFace:'Segoe UI',fontSize:9,color:DK.mut});
  s.addText('KP Polio and Synergy Dashboard',{x:4.9,y:7.06,w:2.6,h:0.28,fontFace:'Segoe UI',fontSize:9,color:DK.mut,align:'right'});
  if(MAPIMG){
   const mh=5.32, mw=mh*706.2/1000;
   s.addText('KP · DISTRICT OF THE UC',{x:7.7,y:0.4,w:5.633,h:0.26,fontFace:'Segoe UI',fontSize:9,bold:true,color:DK.mut,charSpacing:1.5,align:'center'});
   s.addImage({data:MAPIMG,x:7.7+(5.633-mw)/2,y:0.72,w:mw,h:mh});
   s.addText(O.d,{x:7.9,y:6.14,w:5.25,h:0.3,fontFace:'Segoe UI',fontSize:14,bold:true,color:'FFFFFF',align:'center',fit:'shrink'});
   const l1=[],l2=[];
   if(latest&&latest.m.t!=null)l1.push('Target children '+F(latest.m.t)+' ('+latest.lab+')');
   if(geo&&geo.sel.a)l1.push('Area '+F(geo.sel.a)+' km²');
   const duc=(()=>{try{const q={};EPI.forEach(e=>{if(e.d===O.d&&e.c)q[e.c]=1;});return Object.keys(q).length;}catch(e){return 0;}})();
   if(duc)l2.push(duc+' UCs on the EPI register');
   if(geo&&geo.sel.v)l2.push(geo.sel.v+' division');
   s.addText(l1.join('  ·  '),{x:7.9,y:6.46,w:5.25,h:0.26,fontFace:'Segoe UI',fontSize:9,color:'C7D2E4',align:'center',fit:'shrink'});
   s.addText(l2.join('  ·  '),{x:7.9,y:6.72,w:5.25,h:0.26,fontFace:'Segoe UI',fontSize:9,color:'C7D2E4',align:'center',fit:'shrink'});
   s.addText('UC '+O.u+' · '+O.t+' highlighted in red',{x:7.9,y:7.04,w:5.25,h:0.24,fontFace:'Segoe UI',fontSize:8.5,bold:true,color:DK.redL,align:'center',fit:'shrink'});
  }else if(geo){
   s.addText(O.d,{x:8.1,y:3.3,w:4.9,h:0.4,fontFace:'Segoe UI',fontSize:16,bold:true,color:'FFFFFF'});
   s.addText('UC '+O.u+' · '+O.t,{x:8.1,y:3.72,w:4.9,h:0.3,fontFace:'Segoe UI',fontSize:10,color:DK.redL});
  }

  // 2 at a glance
  s=ppt.addSlide();
  dHead(s,ppt,2,'Six rounds at a glance','Six most recent rounds with a row for this UC · every figure recomputed on selection',total);
  const six=[
   ['Latest coverage',latest?PC(latest.m.covp):null],
   ['Mean coverage',PC(avg(cov))],
   ['Recorded missed · mean of target',PC(avg(w.map(x=>x.m.recp)))],
   ['Same-day recovery · mean',PC(avg(w.map(x=>x.m.sdcp)))],
   ['Still missed · mean of target',PC(avg(w.map(x=>x.m.stp)))],
   ['ICM recall · mean',PC(avg(rc))]
  ];
  six.forEach((k,i)=>{
   const x=0.5+(i%3)*4.13,y=1.65+Math.floor(i/3)*1.55;
   s.addShape(ppt.ShapeType.roundRect,{x,y,w:3.9,h:1.3,rectRadius:0.06,fill:{color:DK.soft},line:{color:DK.line}});
   s.addText(k[0],{x:x+0.16,y:y+0.14,w:3.58,h:0.3,fontFace:'Segoe UI',fontSize:10,color:DK.slate});
   s.addText(k[1]==null?'–':k[1],{x:x+0.16,y:y+0.46,w:3.58,h:0.68,fontFace:'Segoe UI',fontSize:27,bold:true,color:DK.ink,fit:'shrink'});
  });
  s.addShape(ppt.ShapeType.rect,{x:0.5,y:4.95,w:0.07,h:1.55,fill:{color:DK.red},line:{color:DK.red}});
  const reads=[];
  if(cov.length)reads.push('Coverage ran '+PC(MN(cov))+'–'+PC(MX(cov))+' (mean '+PC(avg(cov))+'); '+(cov.filter(v=>v>110).length?cov.filter(v=>v>110).length+' of '+cov.length+' rounds sit above 110%, so the target needs reconciling.':'no round crossed 110%.'));
  if(w.length)reads.push('Recorded missed averaged '+PC(avg(w.map(x=>x.m.recp)))+' of target and same-day coverage recovered '+PC(avg(w.map(x=>x.m.sdcp)))+' of that list; still missed averaged '+PC(avg(w.map(x=>x.m.stp)))+'.');
  if(rc.length)reads.push('ICM recall averaged '+PC(avg(rc))+(latest&&latest.m.clu?(' over '+F(latest.m.clu)+' clusters in the latest round ('+PC(latest.m.snp)+' of children seen)'):'')+'.');
  s.addText(reads.map((t,i)=>({text:(i+1)+'   '+t,options:{breakLine:true}})),{x:0.75,y:5.02,w:11.9,h:1.4,fontFace:'Segoe UI',fontSize:11.5,color:DK.ink,lineSpacingMultiple:1.15});

  // 3 campaign table
  s=ppt.addSlide();
  dHead(s,ppt,3,'Campaign triangulation','Last six rounds with a row for this UC · target movement, coverage, missed children, ICM, market survey, LQAS and PCM',total);
  const hd=['Indicator'].concat(w.map(x=>x.lab),['6-round avg']);
  const mean=k=>avg(w.map(x=>x.m[k]));
  const bad=(v,fn)=>fn(v)?DK.red:DK.ink;
  const rrow=(name,fn,mk,tone)=>{
   const out=[name];
   w.forEach((x,i)=>{const v=fn(x.m,i,x);out.push(tone?v==null?'–':{text:String(v),options:{color:bad(v,tone),bold:true}}:v);});
   out.push(mk==null?'–':mk);
   return out;
  };
  const rows3=[
   rrow('Target',m=>m.t,mean('t')),
   rrow('Target change %',(m,i,x)=>SG(x.dtv),null),
   rrow('Coverage %',m=>PC(m.covp),PC(mean('covp')),v=>{const n=parseFloat(v);return n>110||n<80;}),
   rrow('Recorded missed %',m=>PC(m.recp),PC(mean('recp')),v=>parseFloat(v)>=14),
   rrow('Same-day % of missed',m=>PC(m.sdcp),PC(mean('sdcp')),v=>parseFloat(v)<40),
   rrow('Still missed %',m=>PC(m.stp),PC(mean('stp')),v=>parseFloat(v)>=5),
   rrow('Still missed NA / refusal',m=>F(m.sna)+' / '+F(m.srf),null),
   rrow('ICM recall %',m=>PC(m.rcp),PC(mean('rcp')),v=>parseFloat(v)<90),
   rrow('Market survey %',m=>PC(m.msp),PC(mean('msp'))),
   rrow('LQAS %',m=>m.lqp==null?'–':PC(m.lqp),'–',v=>v!=='–'&&parseFloat(v)<80),
   rrow('PCM field-monitoring %',m=>PC(m.pcmp),PC(mean('pcmp')),v=>v!=='–'&&parseFloat(v)<90)
  ];
  dTable(s,ppt,hd,rows3,{x:0.45,y:1.5,w:12.43,colW:[2.73].concat(w.map(()=>1.35),[1.6]),rowH:0.31,fs:8.5});
  if(dtA.length)s.addText('The target moved '+PC(avg(dtA))+' per round on average, '+PC(MX(dtA))+' at most. Red cells are outside the dashboard benchmark:',{x:0.5,y:6.28,w:12.3,h:0.28,fontFace:'Segoe UI',fontSize:9,color:DK.slate});
  s.addText('coverage 90%+, recorded missed under 14% of target, same-day recovery 40%+, still missed under 5%, ICM recall 90%+, LQAS and PCM 80/90%+.',{x:0.5,y:6.52,w:12.3,h:0.28,fontFace:'Segoe UI',fontSize:9,color:DK.mut});

  // 4 read
  s=ppt.addSlide();
  dHead(s,ppt,4,'What the rounds say','Read straight from the table: the movement, the recovery and the gap that remains',total);
  const pts=[];
  if(cov.length)pts.push(['Coverage '+PC(MN(cov))+'–'+PC(MX(cov)),'Mean '+PC(avg(cov))+' across '+cov.length+' rounds. '+(cov.filter(v=>v>110).length?'Above 110% in '+cov.filter(v=>v>110).length+' round(s) — the denominator, not the reach, is the question.':'Every round stayed inside the band.')]);
  if(w.length)pts.push(['Roughly '+PC(avg(w.map(x=>x.m.recp)))+' of the target is recorded missed','Mean of the six rounds; the latest round listed '+F((latest||{}).m&&latest.m.rec)+' children.']);
  if(w.length)pts.push(['Same-day sweep recovers '+PC(avg(w.map(x=>x.m.sdcp)))+' of the missed list','Still missed then averages '+PC(avg(w.map(x=>x.m.stp)))+' of target'+(latest?(' — '+F(latest.m.sna)+' not available and '+F(latest.m.srf)+' refusals in the latest round'):'')+'.']);
  if(rc.length)pts.push(['ICM recall '+PC(avg(rc))+' on average','Latest round checked '+F((latest||{}).m&&latest.m.clu)+' clusters and saw '+PC(latest&&latest.m.snp)+' of the children listed.']);
  if(O.lq.length)pts.push(['LQAS '+(lqLast?('lot result '+lqWord(lqLast.r)+' in '+lqLast.camp):'recorded')+' with '+F(lqLast?lqLast.q.tt:null)+' '+(lqLast&&lqLast.q.tt===1?'child':'children')+' missed','Of these, '+F(lqLast?lqLast.q.tm:null)+' team-missed, '+F(lqLast?lqLast.q.dn:null)+' not visited and '+F(lqLast?lqLast.q.rf:null)+' '+(lqLast&&lqLast.q.rf===1?'refusal':'refusals')+'.']);
  if(!ms.length)pts.push(['Market survey is blank for every round','No market survey percentage is attached to this UC, so social-data triangulation is missing.']);
  if(O.pm.length)pts.push(['Post-campaign checks: '+O.pm.length+' round(s)','Latest is '+O.pm[0].lab+' ('+O.pm[0].type+') with '+PC(O.pm[0].fmp)+' finger-marking and '+PC(O.pm[0].rcp)+' recall.']);
  pts.slice(0,6).forEach((t,i)=>{
   const y=1.55+i*0.9;
   s.addShape(ppt.ShapeType.rect,{x:0.5,y:y+0.06,w:0.06,h:0.62,fill:{color:DK.red},line:{color:DK.red}});
   s.addText(t[0],{x:0.72,y:y,w:11.9,h:0.34,fontFace:'Segoe UI',fontSize:13,bold:true,color:DK.ink,fit:'shrink'});
   s.addText(t[1],{x:0.72,y:y+0.33,w:11.9,h:0.4,fontFace:'Segoe UI',fontSize:10,color:DK.slate,fit:'shrink'});
  });

  // 5 surveillance
  s=ppt.addSlide();
  dHead(s,ppt,5,'Surveillance','AFP line list at this UC · WPV1 position against the district and the province',total);
  if(O.afY.length){
   dTable(s,ppt,['Year','AFP cases','WPV1','VDPV','Discarded','Pending','Stool adequate %','Notified ≤7d %','Investigated ≤2d %'],
    O.afY.map(x=>[x.y,x.n,{text:F(x.c1),options:{color:x.c1?DK.red:DK.ink,bold:!!x.c1}},x.c2?{text:F(x.c2),options:{color:DK.amb}}:x.c3,F(x.c3),{text:F(x.c0),options:{color:x.c0?DK.red:DK.ink}},PC(x.adqp),PC(x.n7p),PC(x.i2p)]),
    {x:0.5,y:1.55,w:7.55,colW:[0.7,0.85,0.65,0.65,0.85,0.75,1.05,1.05,1.0],rowH:0.3,fs:8.5});
  }else s.addText('The line list carries no AFP case with this UC code.',{x:0.5,y:1.55,w:7.5,h:0.4,fontFace:'Segoe UI',fontSize:11,color:DK.slate});
  const boxes=[
   ['This UC',O.wpvU.length?O.wpvU.length+' WPV1 case(s) in the WPV register'+(O.wpvH.length?(' · onsets '+A(O.wpvH.map(x=>x.on))):''):'No WPV1 case in the WPV register'+(O.wpvH.length?(' · historical onset(s) '+A(O.wpvH.map(x=>x.on))):'')],
   ['District '+O.d,O.wpvD26.length+' WPV1 case(s) in 2026'+(O.np26.length?(' · '+F(O.np26.reduce((a,x)=>a+x[2],0))+' AFP case(s) without a UC, '+F(O.np26.reduce((a,x)=>a+x[3],0))+' pending'):'')],
   ['Province',O.wpvKP26.length+' WPV1 case(s) in 2026 across KP'+(wpvLastTxt?(' · register covers onsets to '+wpvLastTxt):'')],
   ['Classification',pend26?F(pend26)+' record(s) at this UC have no final class — waiting on laboratory and ERC':'No record at this UC is awaiting a final class']
  ];
  boxes.forEach((bx,i)=>{
   const y=1.52+i*1.22;
   s.addShape(ppt.ShapeType.roundRect,{x:8.25,y,w:4.6,h:1.05,rectRadius:0.06,fill:{color:DK.soft},line:{color:DK.line}});
   s.addText(bx[0],{x:8.4,y:y+0.08,w:4.3,h:0.25,fontFace:'Segoe UI',fontSize:9,bold:true,color:DK.red});
   s.addText(bx[1],{x:8.4,y:y+0.32,w:4.3,h:0.66,fontFace:'Segoe UI',fontSize:9.5,color:DK.ink,fit:'shrink'});
  });
  s.addText('An AFP record depends on the line list checked; a broadcast-confirmed case depends on the EOC case file. The register only carries onsets up to its own export date.',{x:0.5,y:6.32,w:7.55,h:0.5,fontFace:'Segoe UI',fontSize:8.5,color:DK.mut});

  // 6 zero dose
  s=ppt.addSlide();
  dHead(s,ppt,6,'Zero dose','Digitization register · zero-dose children reported and covered by campaign',total);
  if(O.z){
   dTable(s,ppt,['Campaign','ZD reported','ZD covered','Covered %','Band'],
    [['Apr 2026',O.z.rA,O.z.cA,{text:PC(O.z.pA),options:{color:O.z.pA!=null&&O.z.pA<50?DK.red:DK.ink,bold:true}},O.z.bA||'–'],
     ['May 2026',O.z.rM,O.z.cM,{text:PC(O.z.pM),options:{color:O.z.pM!=null&&O.z.pM<50?DK.red:DK.ink,bold:true}},O.z.bM||'–'],
     ['Sept 2026',O.z.rS,O.z.cS,{text:PC(O.z.pS),options:{color:O.z.pS!=null&&O.z.pS<50?DK.red:DK.ink,bold:true}},O.z.bS||'–']],
    {x:0.5,y:1.55,w:7.5,colW:[1.7,1.5,1.5,1.4,1.4],rowH:0.34,fs:10});
   const zseq=[['April',O.z.pA],['May',O.z.pM],['Sept',O.z.pS]].filter(x=>x[1]!=null).map(x=>x[0]+' '+PC(x[1])).join('  →  ');
   s.addShape(ppt.ShapeType.roundRect,{x:0.5,y:3.45,w:7.5,h:0.95,rectRadius:0.06,fill:{color:DK.ink},line:{color:DK.ink}});
   s.addText('Register path   '+zseq,{x:0.7,y:3.6,w:7.1,h:0.3,fontFace:'Segoe UI',fontSize:9,color:DK.mut});
   s.addText(zPct!=null?('Latest coverage '+PC(zPct)+' in '+zLbl):'No coverage figure in the register',{x:0.7,y:3.88,w:7.1,h:0.4,fontFace:'Segoe UI',fontSize:16,bold:true,color:'FFFFFF',fit:'shrink'});
   s.addText('Covered % = zero-dose children covered ÷ reported. Bands follow the register: below 50% critical, 50–80% low, 80–90% moderate, 90–110% good, above 110% verify.',{x:8.25,y:1.55,w:4.6,h:1.6,fontFace:'Segoe UI',fontSize:9.5,color:DK.slate});
   const om=[];
   if(latest)om.push('campaign template: '+F(latest.m.zd)+' in '+latest.lab);
   if(O.pm.length)om.push('latest ICM round: '+F(O.pm[0].zd)+' among children checked');
   if(O.e&&O.e.zr!=null)om.push('routine EPI register: '+F(O.e.zr)+' with no antigen');
   if(om.length)s.addText('Other records of zero dose in this UC — '+om.join('; ')+'. The sources count different populations, so compare direction, not totals.',{x:8.25,y:3.35,w:4.6,h:1.6,fontFace:'Segoe UI',fontSize:9.5,color:DK.slate});
  }else{
   s.addText('The digitization register carries no row for this UC.',{x:0.5,y:1.55,w:12,h:0.4,fontFace:'Segoe UI',fontSize:12,color:DK.slate});
  }

  // 7 routine EPI
  s=ppt.addSlide();
  dHead(s,ppt,7,'Routine EPI','Doses and coverage against the district and KP · '+epiPer(),total);
  if(O.e){
   const keys=['bcg','opv3','p3','mr1','mr2','rota2','fi'];
   const rows7=keys.map(k=>[agn(k),O.e[k],PC(eP(O.e,k)),PC(eP(O.dAgg,k)),PC(eP(O.kpAgg,k))]);
   const d13=(O.e.p1&&O.e.p3!=null)?(((O.e.p1-O.e.p3)/O.e.p1)*100):null;
   const dmr=(O.e.mr1&&O.e.mr2!=null)?(((O.e.mr1-O.e.mr2)/O.e.mr1)*100):null;
   rows7.push([{text:'Zero-dose children (no antigen)',options:{bold:true}},O.e.zr,{text:PC(O.e.zp),options:{color:O.e.zp!=null&&O.e.zp<80?DK.red:DK.ink,bold:true}},'–','–']);
   rows7.push([{text:'Penta-1 → Penta-3 dropout %',options:{bold:true}},(d13==null?'–':F(O.e.p1-O.e.p3)),{text:PC(d13),options:{color:d13!=null&&d13>10?DK.red:DK.grn,bold:true}},PC(O.dAgg.d13),PC(O.kpAgg.d13)]);
   rows7.push([{text:'MR-1 → MR-2 dropout %',options:{bold:true}},(dmr==null?'–':F(O.e.mr1-O.e.mr2)),{text:PC(dmr),options:{color:dmr!=null&&dmr>20?DK.red:DK.grn,bold:true}},PC(O.dAgg.dmr),PC(O.kpAgg.dmr)]);
   dTable(s,ppt,['Antigen','UC doses','UC coverage','District coverage','KP coverage'],rows7,{x:0.5,y:1.55,w:12.33,colW:[3.6,2.2,2.2,2.2,2.13],rowH:0.34,fs:10});
   s.addText('Coverage is doses ÷ the antigen target. Dropout is (first − last) ÷ first, shown as the children lost. District and KP are recomputed from the same register. An October dose is not in this table.',{x:0.5,y:6.2,w:12.3,h:0.5,fontFace:'Segoe UI',fontSize:9,color:DK.mut});
  }else s.addText('No routine EPI register row for this UC.',{x:0.5,y:1.55,w:12,h:0.4,fontFace:'Segoe UI',fontSize:12,color:DK.slate});

  // 8+ recommendations
  O.rl.forEach((r,i)=>{
   if(i%4)return;
   const group=O.rl.slice(i,i+4);
   s=ppt.addSlide();
   dHead(s,ppt,8+Math.floor(i/4),'Recommendations '+(Math.floor(i/4)+1)+' of '+recSlides,'Threshold-driven: each finding is computed from the rows on the previous slides',total);
   group.forEach((g,j)=>{
    const y=1.5+j*1.28,h=1.16,col=sevCol(g[0]);
    s.addShape(ppt.ShapeType.roundRect,{x:0.5,y,w:12.33,h,rectRadius:0.05,fill:{color:DK.soft},line:{color:DK.line}});
    s.addShape(ppt.ShapeType.rect,{x:0.5,y,w:0.07,h,fill:{color:col},line:{color:col}});
    s.addText(sevLbl(g[0]),{x:0.72,y:y+0.1,w:1.35,h:0.24,fontFace:'Segoe UI',fontSize:8,bold:true,color:col});
    s.addText(g[1],{x:1.9,y:y+0.08,w:10.7,h:0.3,fontFace:'Segoe UI',fontSize:12,bold:true,color:DK.ink,fit:'shrink'});
    s.addText(g[2],{x:0.72,y:y+0.4,w:11.9,h:0.36,fontFace:'Segoe UI',fontSize:8.8,color:DK.slate,fit:'shrink'});
    s.addText('Action: '+g[3],{x:0.72,y:y+0.77,w:11.9,h:0.3,fontFace:'Segoe UI',fontSize:9,color:DK.ink,fit:'shrink'});
   });
  });

  // thank you
  s=ppt.addSlide();
  s.background={color:DK.ink};
  s.addShape(ppt.ShapeType.rect,{x:0,y:0,w:13.333,h:0.16,fill:{color:DK.red},line:{color:DK.red}});
  s.addText('WPV1 CASE PROFILE · KP EOC',{x:0.9,y:2.2,w:11.5,h:0.3,fontFace:'Segoe UI',fontSize:11,bold:true,color:DK.mut,charSpacing:3});
  s.addText('Thank you',{x:0.9,y:2.52,w:11.5,h:1.05,fontFace:'Segoe UI',fontSize:46,bold:true,color:'FFFFFF'});
  s.addShape(ppt.ShapeType.rect,{x:0.92,y:3.7,w:1.6,h:0.06,fill:{color:DK.red},line:{color:DK.red}});
  s.addText(O.u+' · UC '+O.code,{x:0.9,y:3.95,w:11.5,h:0.42,fontFace:'Segoe UI',fontSize:17,bold:true,color:DK.redL,fit:'shrink'});
  s.addText(O.dv+'  ›  '+O.d+'  ›  '+O.t,{x:0.92,y:4.42,w:11.5,h:0.32,fontFace:'Segoe UI',fontSize:12,color:'C7D2E4'});
  s.addText('Every figure in this deck is recomputed from the dashboard when the UC is selected, so the same selection here and in the next round gives a comparable picture.',
   {x:0.9,y:5.0,w:9.6,h:0.7,fontFace:'Segoe UI',fontSize:11,color:DK.mut});
  s.addText('KP Polio and Synergy Dashboard · WPV1 confirmed-case profile',{x:0.9,y:7.16,w:9.5,h:0.22,fontFace:'Segoe UI',fontSize:8,color:DK.mut});
  s.addText((total-1)+' / '+total,{x:11.3,y:7.16,w:1.53,h:0.22,fontFace:'Segoe UI',fontSize:8,color:DK.mut,align:'right'});

  // closing
  s=ppt.addSlide();
  dHead(s,ppt,total,'Sources and method','Every figure on these slides is recomputed from the dashboard payloads when the UC is selected',total);
  const src=[
   ['Campaign triangulation','CHD — EOC campaign template, one row per UC per round; the six most recent rounds with a row are shown.'],
   ['Post-campaign activity','LQR / LQM — LQAS lots; PCM — ICM, PCM and PCHS rounds for the UC.'],
   ['Surveillance','AFPUC — four-sheet AFP line list, '+(AF?(fmt(AF.n)+' KP cases, onsets to '+AF.asof):'not loaded')+'; WPV / WPVH — EOC WPV register.'],
   ['Zero dose','ZD — digitization register, 2026 campaigns.'],
   ['Routine EPI','EPI / EPIYTD — EPI-MIS '+epiPer()+'; EPIUC archive '+(typeof EPIUC!=='undefined'&&EPIUC?String(EPIUC.per):'')+'.'],
   ['Method','Coverage 90/80; ICM recall and seen 90/80; PCM field monitoring 95/90; still missed 2/5% of target; LQAS 90/80; Penta dropout 10%; MR-2 dropout 20%.'],
   ['Caveat','An AFP record and a programme-confirmed case are read from different sources; the register is the surveillance denominator around the case.'],
   ['Privacy','No name, address, EPID or laboratory number is carried in the payload or this deck.']
  ];
  src.forEach((r,i)=>{
   const col=i%2,x=0.5+col*6.25,y=1.5+Math.floor(i/2)*1.3;
   s.addText(r[0],{x,y,w:5.9,h:0.28,fontFace:'Segoe UI',fontSize:10.5,bold:true,color:DK.red});
   s.addText(r[1],{x,y:y+0.28,w:5.9,h:0.9,fontFace:'Segoe UI',fontSize:9,color:DK.slate,fit:'shrink'});
  });
  return ppt;
 }
 function deck(O){
  const b=el('wpvPptx');if(b)b.disabled=true;
  if(typeof loadPptx!=='function'||typeof saveDeck!=='function'){toast('The presentation helpers are not on this page');if(b)b.disabled=!cur;return;}
  toast('Building the presentation…');
  Promise.all([mapImage(O).catch(()=>null),loadPptx()])
   .then(([img])=>saveDeck(buildDeck(O,img),stem(O).replace(/^wpv1_case_profile_/,'WPV1_case_profile_')+'.pptx'))
   .then(()=>toast('Presentation downloaded · '+(7+Math.max(1,Math.ceil(O.rl.length/4))+2)+' slides'))
   .catch(e=>{console.warn(e);toast('Presentation failed: '+((e&&e.message)||e));})
   .then(()=>{if(b)b.disabled=!cur;});
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
   if(el('wpvXls'))el('wpvXls').disabled=true;
   if(el('wpvPptx'))el('wpvPptx').disabled=true;
   return;
  }
  const g=geo(),dv=el('wpvDiv').value,d=el('wpvDist').value,t=el('wpvTeh').value;
  const uc=(g.U[dv+'|'+d+'|'+t]||[]).filter(x=>x.c===code)[0];
  if(!uc){body.innerHTML='<div class="cap">That UC is no longer in the EPI register.</div>';return;}
  let P=null;
  try{P=build(dv,d,t,uc);paint(P);cur=P;}
  catch(e){body.innerHTML='<div class="cap">Profile could not be rendered: '+esc(e&&e.message?e.message:e)+'</div>';cur=null;}
  if(el('wpvCsv'))el('wpvCsv').disabled=!cur;
  if(el('wpvXls'))el('wpvXls').disabled=!cur;
  if(el('wpvPptx'))el('wpvPptx').disabled=!cur;
 }

 return {init:init,draw:draw};
})();
WPVC.init();
/* WPVPROF:JS:END */
