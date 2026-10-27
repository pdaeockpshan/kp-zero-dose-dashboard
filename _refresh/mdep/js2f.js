function mdpSheetDraw(R,T){
 const dd=mdpVal('mdpDist');
 const dl=MDD?(mdpDayTag(MDD)+(dd?' · '+mdpPhase(dd,MDD):'')):'All reported days';
 el('mdpTitle').textContent=mdpCampLbl()+' — Morning Team Deployment';
 el('mdpSub').innerHTML='<b>'+esc(dl)+'</b> · '+mdpLbl(R);
 el('mdpStamp').innerHTML='Reports received: '+T.rep+' of '+R.length+' districts<br>Generated '+nowLbl();
 el('mdpFtL').textContent='Prepared by: EOC KP · Polio Eradication Programme · scope source: '+mdpSrcLbl();
 el('mdpFtD').textContent=MDD?mdpDayTag(MDD):'All reported days';
 const k=(i,v,s)=>'<div class="shk1"><i>'+i+'</i><b>'+v+'</b><s>'+(s||'')+'</s></div>';
 el('mdpSheetKpis').innerHTML=
  k('Field deployment',T.pct==null?'–':T.pct.toFixed(1)+'%','mobile + fixed + transit + roaming')+
  k('Teams deployed',fmt(T.fd),'of '+fmt(T.fp)+' planned')+
  k('UCs reported',fmt(T.ucr),'of '+fmt(T.ucp)+' in the register')+
  k('Reports received',T.rep+' / '+R.length,T.late+' after 12:00 · '+T.no+' none')+
  k('Teams awaited',fmt(T.aw),'planned, not yet deployed')+
  k('Security incidents',fmt(T.inc),mdpDayLbl())+
  k('Districts on plan',String(T.good),T.watch+' watch · '+T.low+' short · '+T.crit+' critical')+
  k('Divisions',String(new Set(R.map(o=>o.dv)).size),mdpLbl(R));
 const G={};
 R.forEach(o=>{const g=G[o.dv]||(G[o.dv]={dv:o.dv,n:0,rep:0,fp:0,fd:0,aw:0,ucp:0,ucr:0,inc:0});
  g.n++;g.ucp+=o.ucp;g.ucr+=o.ucr;
  if(o.rep){g.rep++;g.fp+=o.fp;g.fd+=o.fd;g.aw+=o.awTot;g.inc+=o.inc;}});
 const gs=Object.keys(G).sort().map(x=>G[x]);
 el('tMDPDiv').innerHTML=erTbl(['Division','Dist','Rep','Teams','Dep %','UCs','Awaited','Inc.'],
  gs.map(g=>[esc(g.dv),String(g.n),String(g.rep),nfmt(g.fd)+' / '+nfmt(g.fp),(g.fp?pfmt(g.fd/g.fp*100):'–'),nfmt(g.ucr)+' / '+nfmt(g.ucp),nfmt(g.aw),nfmt(g.inc)]),
  ['Campaign total',String(T.n),String(T.rep),nfmt(T.fd)+' / '+nfmt(T.fp),pfmt(T.pct),nfmt(T.ucr)+' / '+nfmt(T.ucp),nfmt(T.aw),nfmt(T.inc)]);
 const rs=R.slice().sort((a,b)=>(a.pct==null?-1:a.pct)-(b.pct==null?-1:b.pct));
 el('tMDPSum').innerHTML=erTbl(['District','Div','Last','UCs','Teams','Dep %','Awaited','Inc.','Reason','Status'],
  rs.map(o=>[esc(DNAME(o.n)),esc(o.dv),o.rep?('D'+o.last+(o.at?' '+o.at:'')):'–',nfmt(o.ucr)+'/'+nfmt(o.ucp),o.rep?(nfmt(o.fd)+'/'+nfmt(o.fp)):'–',(o.pct==null?'–':pfmt(o.pct)),(o.rep?nfmt(o.awTot):'–'),(o.rep?nfmt(o.inc):'–'),esc(o.rsn?(MDP_RSN[o.rsn]||o.rsn):''),mdpStTag(o.st)]),
  ['Campaign total',String(T.n)+(T.n===1?' district':' districts'),mdpDayLbl(),nfmt(T.ucr)+'/'+nfmt(T.ucp),nfmt(T.fd)+'/'+nfmt(T.fp),pfmt(T.pct),nfmt(T.aw),nfmt(T.inc),'',T.good+' on plan']);
 el('mdpBn').innerHTML=mdpBn(R,T);
 el('mdpDayLbl2').textContent=mdpDayLbl();
}
