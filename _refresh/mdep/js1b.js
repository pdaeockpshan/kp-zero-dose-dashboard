function mdpCalc(r){
 const p=r.p||[],d=r.d||[];
 const aw=MDP_TYPES.map((t,i)=>Math.max(0,(p[i]||0)-(d[i]||0)));
 const fp=MDP_FIELD.reduce((a,i)=>a+(p[i]||0),0),fd=MDP_FIELD.reduce((a,i)=>a+(d[i]||0),0);
 const ucAw=Math.max(0,(r.ucp||0)-(r.ucr||0));
 const pct=fp?fd/fp*100:null;
 return {aw,awTot:aw.reduce((a,b)=>a+b,0),fp,fd,pct,ucAw};
}
const mdpStat=p=>p==null?'no':(p>=95?'good':p>=85?'watch':p>=70?'low':'crit');
let _MDSV=null,_MDSK='',_MDDV=null;
function mdpDv(n){
 if(!_MDDV){const m={};if(typeof KPGEO!=='undefined')(KPGEO.d||[]).forEach(p=>{m[p.c]=p.v;});_MDDV=m;}
 return _MDDV[n]||(typeof D2DV!=='undefined'&&D2DV[n])||'Other';
}
// The register the tab measures against. Nov-26 uses the live campaign scope; a past campaign uses
// the districts its own record carries, plus any district a stored report names. It is never swapped
// for another campaign's scope, so a coverage total is always read against the register it names.
function mdpScope(){
 if(_MDSK!==MDC||!_MDSV){
  let v=[];
  if(MDC==='NOV-26')v=SNDALL.map(o=>({n:o.n,dv:o.dv,cat:o.cat,uc:o.uc}));
  else{
   const P=(typeof CQ!=='undefined'&&CQ&&CQ.pre&&CQ.pre[MDC])||{},seen={};
   const add=n=>{if(!n||seen[n])return;seen[n]=1;v.push({n:n,dv:mdpDv(n),cat:'',uc:0});};
   Object.keys(P).forEach(k=>add(mdpDist(k)));
   Object.keys(MDR).forEach(k=>{const r=MDR[k];if(r&&r.n)add(r.n);});
  }
  _MDSK=MDC;_MDSV=v;
 }
 return _MDSV.map(o=>Object.assign({},o,{dy:mdpLastDay(o.n)}));
}
function mdpLastDay(n){
 let m=mdpBaseD(n);
 for(let d=MDP_MAXD;d>mdpBaseD(n);d--){if(mdpGet(d,n)){m=d;break;}}
 return m;
}
function mdpBase(){const dv=mdpVal('mdpDiv'),dd=mdpVal('mdpDist');
 return mdpScope().filter(o=>(!dv||o.dv===dv)&&(!dd||o.n===dd));}
// A day picked in the form (an extended catch-up nobody has reported yet) must survive the day bar,
// otherwise the form snaps back to the last day anyone reported.
function mdpMaxD(){let m=MDD>0?MDD:0;mdpBase().forEach(o=>{if(o.dy>m)m=o.dy;});return m||7;}
function mdpLbl(R){const dv=mdpVal('mdpDiv'),dd=mdpVal('mdpDist');
 if(dd)return 'district '+esc(DNAME(dd));
 if(dv)return 'division '+esc(dv)+' ('+R.length+' districts)';
 return 'KP — all '+R.length+' districts in this campaign\u2019s register';}
function mdpDayLbl(){if(!MDD)return 'All reported days';
 const dd=mdpVal('mdpDist');
 return 'Day '+MDD+(dd?' · '+mdpPhase(dd,MDD):'');}
function mdpTodayDay(n){
 const st=mdpStart();if(!st)return 1;
 const p=String(st).split('-'),s=Date.UTC(+p[0],(+p[1]||1)-1,+p[2]||1),t=new Date(),
  n0=Date.UTC(t.getFullYear(),t.getMonth(),t.getDate());
 const d=Math.floor((n0-s)/864e5)+1,m=n?mdpLastDay(n):7;
 return d<1?1:d>m?m:d;}
function mdpLastPlan(n){for(let d=mdpLastDay(n);d>=1;d--){const r=mdpGet(d,n);if(r)return r.p.slice();}return null;}
function mdpRows(base){
 const R=[];
 for(const o of (base||mdpBase())){
  const dy=o.dy;
  if(MDD&&MDD>dy)continue;
  const days=MDD?[MDD]:[...Array(dy)].map((_,i)=>i+1),got=[];
  days.forEach(d=>{const r=mdpGet(d,o.n);if(r)got.push(r);});
  const p=MDP_TYPES.map(()=>0),dd=MDP_TYPES.map(()=>0);
  // teams add up over the days reported; UCs belong to a day, so the latest report carries them
  let ucp=o.uc||0,ucRep=0,ucr=0,inc=0,ttm=0,at='',last=0;
  got.forEach(r=>{for(let i=0;i<9;i++){p[i]+=r.p[i]||0;dd[i]+=r.d[i]||0;}
   inc+=r.inc||0;ttm+=r.ttm||0;
   if((r.ucp||0)>ucRep)ucRep=r.ucp||0;
   if(r.day>=last){last=r.day;at=r.at||'';ucr=r.ucr||0;}});
  if(!ucp)ucp=ucRep;
  const row={n:o.n,dv:o.dv,cat:o.cat,uc:o.uc,dy:dy,reps:got.length,last:last,at:at,
   ucp:ucp,ucr:ucr,p:p,d:dd,inc:inc,ttm:ttm,rsn:got.length?(got[got.length-1].rsn||''):'',rep:got.length>0};
  Object.assign(row,mdpCalc(row));
  row.st=row.rep?mdpStat(row.pct):'no';
  R.push(row);
 }
 return R;
}
function mdpTot(R){
 const t={n:R.length,rep:0,ucp:0,ucr:0,fp:0,fd:0,aw:0,inc:0,late:0,no:0,good:0,watch:0,low:0,crit:0};
 for(const o of R){
  if(o.rep){t.rep++;t.fp+=o.fp;t.fd+=o.fd;t.aw+=o.awTot;t.inc+=o.inc;t.late+=mdpLate(o)?1:0;}
  t.ucp+=o.ucp;t.ucr+=o.ucr;
  if(o.st==='no')t.no++;else t[o.st]++;
 }
 t.pct=t.fp?t.fd/t.fp*100:null;
 return t;
}
