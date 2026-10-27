function mdpBindTeams(){
 const w=el('mdpTeams');if(!w||w._b)return;w._b=1;
 w.innerHTML='<div></div><div class="h">Planned</div><div class="h">Deployed</div><div class="h">Awaited</div>'+
  MDP_TYPES.map((t,i)=>'<div class="nm">'+esc(t[1])+'</div><input id="mdpP'+i+'" type="number" min="0" step="1" aria-label="'+esc(t[1])+' planned"><input id="mdpD'+i+'" type="number" min="0" step="1" aria-label="'+esc(t[1])+' deployed"><div class="aw" id="mdpA'+i+'">0</div>').join('');
}
function mdpFormSync(){
 const fd=el('mdpFDist'),ds=el('mdpFDay');if(!fd||!ds)return;
 if(!fd.value){const S=mdpScope();if(S[0])fd.value=S[0].n;}
 const n=fd.value,base=n?mdpBaseD(n):5;
 if(ds._n!==n){
  const prev=+ds.value||1;
  ds.innerHTML=[...Array(MDP_MAXD)].map((_,i)=>{const d=i+1;
   return '<option value="'+d+'">Day '+d+' · '+mdpPhase(n||'',d)+'</option>';}).join('');
  ds._n=n;
  ds.value=String(prev>=1&&prev<=MDP_MAXD?prev:1);
 }
 if(MDD>=1&&MDD<=MDP_MAXD)ds.value=String(MDD);
 const d=+ds.value||1,r=n?mdpGet(d,n):null,sc=n?(mdpScope().find(o=>o.n===n)||{}):{};
 const lp=r?r.p:mdpLastPlan(n);
 el('mdpAt').value=r?(r.at||''):mdpNow();
 el('mdpUCP').value=r?r.ucp:(sc.uc||0);
 el('mdpUCR').value=r?r.ucr:'';
 el('mdpInc').value=r?(r.inc||0):0;
 el('mdpTTM').value=r?(r.ttm||0):0;
 el('mdpRsn').value=r?(r.rsn||''):'';
 MDP_TYPES.forEach((t,i)=>{el('mdpP'+i).value=lp?(lp[i]||0):0;el('mdpD'+i).value=r?(r.d[i]||0):0;});
 el('mdpFormLbl').textContent=n?('Day '+d+' · '+DNAME(n)+(r?' · saved report':' · new report')):'No district';
 el('mdpFormCnt').textContent=n?(base+' days · '+mdpActD(n)+' active + 2 catch-up'+(d>base?' · extended catch-up':'')):'';
 mdpFormCalc();
}
function mdpFormCalc(){
 const g=id=>Math.max(0,Math.round(+el(id).value||0));
 const p=MDP_TYPES.map((t,i)=>g('mdpP'+i)),d=MDP_TYPES.map((t,i)=>g('mdpD'+i));
 const c=mdpCalc({p:p,d:d,ucp:g('mdpUCP'),ucr:g('mdpUCR')});
 MDP_TYPES.forEach((t,i)=>{const a=el('mdpA'+i);if(!a)return;a.textContent=c.aw[i];a.classList.toggle('hot',c.aw[i]>0);});
 const pct=c.pct,late=mdpLate({at:el('mdpAt').value});
 el('mdpCalc').innerHTML='<span>Field deployment <b style="color:'+(pct==null?C.mut:MDP_COL[mdpStat(pct)])+'">'+(pct==null?'–':pct.toFixed(1)+'%')+'</b></span>'+
  '<span>Awaited <b>'+fmt(c.awTot)+'</b> teams</span><span>UCs awaited <b>'+fmt(c.ucAw)+'</b></span>'+
  '<span class="mdpdm'+(late?' late':'')+'">'+(el('mdpAt').value?(late?'After 12:00 · late':'On time'):'time not set')+'</span>';
}
function mdpReadForm(){
 const fd=el('mdpFDist'),n=fd?fd.value:'',g=id=>Math.max(0,Math.round(+el(id).value||0));
 return {n:n,day:+el('mdpFDay').value||1,at:el('mdpAt').value||'',ucp:g('mdpUCP'),ucr:g('mdpUCR'),
  p:MDP_TYPES.map((t,i)=>g('mdpP'+i)),d:MDP_TYPES.map((t,i)=>g('mdpD'+i)),
  ttm:g('mdpTTM'),inc:g('mdpInc'),rsn:el('mdpRsn').value||'',ts:new Date().toISOString()};
}
function mdpSaveForm(){
 const r=mdpReadForm();
 if(!r.n){toast('Pick a district first');return;}
 if(r.day<1||r.day>MDP_MAXD){toast('Pick a campaign day');return;}
 if(!r.at)r.at=mdpNow();
 MDR[mdpKey(r.day,r.n)]=r;mdpSave();renderMDEP();renderMDPBar();
 toast('Saved '+DNAME(r.n)+' · day '+r.day+(r.day>mdpBaseD(r.n)?' · extended catch-up':'')+(mdpLate(r)?' · after 12:00':''));
}
