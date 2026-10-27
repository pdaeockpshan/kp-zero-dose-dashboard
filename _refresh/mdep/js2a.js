function mdpRsnTop(R){
 const c={};R.forEach(o=>{if(o.rep&&o.rsn)c[o.rsn]=(c[o.rsn]||0)+1;});
 const e=Object.entries(c).sort((a,b)=>b[1]-a[1])[0];
 return e?('Main reason: '+esc(MDP_RSN[e[0]]||e[0])+' · '+e[1]+' district'+(e[1]===1?'':'s')):'No reason recorded';
}
function mdpKpis(R,T){
 const p=T.pct;
 el('mdpK1').textContent=p==null?'–':p.toFixed(1)+'%';
 el('mdpK1').style.color=p==null?C.mut:MDP_COL[mdpStat(p)];
 el('mdpK1s').textContent='mobile + fixed + transit + roaming · deployed ÷ planned';
 el('mdpK2').textContent=fmt(T.fd);
 el('mdpK2s').textContent='of '+fmt(T.fp)+' planned by the reporting districts';
 el('mdpK3').textContent=fmt(T.ucr);
 el('mdpK3s').textContent='of '+fmt(T.ucp)+' UCs in this scope';
 el('mdpK4').textContent=T.rep+' / '+R.length;
 el('mdpK4s').textContent=T.late+' after 12:00 · '+T.no+' with no report';
 el('mdpK5').textContent=fmt(T.aw);
 el('mdpK5s').textContent='teams planned but not yet deployed';
 el('mdpK6').textContent=fmt(T.inc);
 el('mdpK6s').textContent=mdpRsnTop(R);
}
function mdpCharts(R,T){
 const sub=mdpDayLbl()+' · '+mdpLbl(R);
 const G={};
 R.forEach(o=>{if(!o.rep)return;const g=G[o.dv]||(G[o.dv]={dv:o.dv,fp:0,fd:0,aw:0,n:0});
  g.fp+=o.fp;g.fd+=o.fd;g.aw+=o.awTot;g.n++;});
 const gs=Object.keys(G).sort().map(k=>G[k]).filter(g=>g.fp>0).map(g=>({...g,pct:g.fd/g.fp*100})).sort((a,b)=>a.pct-b.pct);
 HC('mdp1',{chart:{type:'bar'},title:{text:'Deployment % by division'},subtitle:{text:sub+' · field teams'},
  xAxis:{categories:gs.map(g=>g.dv)},yAxis:{title:{text:'% deployed'},max:Math.max(105,...gs.map(g=>g.pct)),plotLines:[{value:95,color:C.high,dashStyle:'Dash',width:2,zIndex:4,label:{text:'95%',style:{color:C.high}}}]},
  legend:{enabled:false},
  tooltip:{pointFormatter:function(){const g=gs[this.index];return '<b>'+esc(g.dv)+'</b><br>'+esc(g.fd.toLocaleString())+' of '+esc(g.fp.toLocaleString())+' teams ('+g.pct.toFixed(1)+'%)<br>'+g.n+' districts in the division total';}},
  plotOptions:{bar:{borderRadius:3,dataLabels:{enabled:true,format:'{y:.1f}%',style:{color:C.sec,textOutline:'none',fontWeight:'400'}}}},
  series:[{name:'Deployment %',data:gs.map(g=>({y:Math.round(g.pct*10)/10,color:MDP_COL[mdpStat(g.pct)]}))}]});
 el('capmdp1').textContent=gs.length?('Weighted across reporting districts of each division · '+mdpDayLbl().toLowerCase()):'No division has a report yet.';
 const P=MDP_TYPES.map(()=>0),D=MDP_TYPES.map(()=>0);
 R.forEach(o=>{if(!o.rep)return;for(let i=0;i<9;i++){P[i]+=o.p[i]||0;D[i]+=o.d[i]||0;}});
 HC('mdp2',{chart:{type:'column'},title:{text:'Planned vs deployed by team type'},subtitle:{text:sub},
  xAxis:{categories:MDP_TYPES.map(t=>t[1]),labels:{rotation:-35,style:{fontSize:'9px'}}},
  yAxis:{title:{text:'Teams'}},legend:{enabled:true},
  tooltip:{shared:true},
  plotOptions:{column:{borderRadius:2,dataLabels:{enabled:true,style:{fontSize:'9px',color:C.sec,textOutline:'none'}}}},
  series:[{name:'Planned',color:'#94a3b8',data:P},{name:'Deployed',color:'#0d9488',data:D}]});
 el('capmdp2').textContent='Team-days summed over the reporting districts for '+mdpDayLbl().toLowerCase()+'. Awaited = planned − deployed.';
}
