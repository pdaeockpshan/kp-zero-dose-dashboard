function mdpTrendD(){
 const cats=[],pct=[],rep=[],sc=[],M=mdpMaxD();
 for(let d=1;d<=M;d++){
  const base=mdpBase().filter(o=>o.dy>=d);
  let fp=0,fd=0,n=0;
  base.forEach(o=>{const r=mdpGet(d,o.n);if(r){const c=mdpCalc(r);fp+=c.fp;fd+=c.fd;n++;}});
  cats.push('Day '+d);pct.push(fp?Math.round(fd/fp*1000)/10:null);rep.push(n);sc.push(base.length);
 }
 return {cats,pct,rep,sc};
}
function mdpCharts2(R,T){
 const tr=mdpTrendD();
 HC('mdp3',{chart:{zoomType:'x'},title:{text:'Deployment pace and reports received by campaign day'},subtitle:{text:mdpLbl(R)+' · reports are stored day by day'},
  xAxis:{categories:tr.cats},
  yAxis:[{title:{text:'Districts reporting'},min:0},{title:{text:'% deployed'},opposite:true,min:0,max:105,plotLines:[{value:95,color:C.high,dashStyle:'Dash',width:1.5,zIndex:3,label:{text:'95%',style:{color:C.high,fontSize:'9px'}}}]}],
  tooltip:{shared:true},
  plotOptions:{column:{borderRadius:3,color:'#99f6e4',borderColor:'#0d9488',borderWidth:1,dataLabels:{enabled:true,style:{fontSize:'9px',color:C.sec,textOutline:'none'}}}},
  series:[{type:'column',name:'Districts reporting',data:tr.rep,yAxis:0},
   {type:'spline',name:'Deployment %',data:tr.pct,yAxis:1,color:'#0d9488',marker:{radius:3},connectNulls:false}]});
 el('capmdp3').innerHTML='Days 1-3 are the active round for every district and days 4-5 its catch-up; '
  +'Peshawar and Khyber run 5 active days and catch up on days 6-7. A day after that is extended '
  +'catch-up asked for by the district, so only the districts that asked appear. A day with no report shows a gap in the line.';
 const A=R.filter(o=>o.rep&&o.awTot>0).sort((a,b)=>b.awTot-a.awTot).slice(0,12);
 HC('mdp4',{chart:{type:'bar',height:Math.max(320,A.length*26+110)},title:{text:'Teams awaited by district'},subtitle:{text:mdpDayLbl()+' · planned − deployed'},
  xAxis:{categories:A.map(o=>DNAME(o.n)),labels:{style:{fontSize:'10px'}}},
  yAxis:{title:{text:'Teams awaited'}},legend:{enabled:false},
  tooltip:{pointFormatter:function(){const o=A[this.index];return '<b>'+esc(DNAME(o.n))+'</b><br>'+o.awTot+' teams awaited<br>'+esc(o.fd.toLocaleString())+' of '+esc(o.fp.toLocaleString())+' deployed ('+(o.pct==null?'–':o.pct.toFixed(1)+'%')+')<br>'+(o.rsn?(esc(MDP_RSN[o.rsn]||o.rsn)):'no reason recorded');}},
  plotOptions:{bar:{borderRadius:2,dataLabels:{enabled:true,style:{color:C.sec,textOutline:'none',fontWeight:'400'}}}},
  series:[{name:'Awaited',data:A.map(o=>({y:o.awTot,color:MDP_COL[o.st]}))}]});
 el('capmdp4').textContent=A.length?'Largest shortfalls first. Districts with no report are not shown here — they are listed on the one-pager and the board.':'No awaited teams in the reports received so far.';
}
