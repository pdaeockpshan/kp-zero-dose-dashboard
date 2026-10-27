// HRA AT A GLANCE (2/3): division band mix, the ranked council curve and the indicator chart.
function hrvBand(X){
 const rows=Object.keys(X.div).map(function(k){
  const o=X.div[k];return {k:k,n:o.n,b:o.b,hi:o.b[2]/o.n*100};})
  .sort(function(a,b){return a.hi-b.hi;});
 HC('hrv1',{
  chart:{type:'bar',height:Math.max(240,rows.length*34+90),backgroundColor:'transparent',
   spacing:[8,10,6,6]},
  title:{text:null},
  xAxis:{categories:rows.map(function(r){return r.k;}),labels:{style:{fontSize:'11px'}}},
  yAxis:{min:0,max:100,title:{text:null},labels:{format:'{value}%'}},
  tooltip:{shared:true,
   pointFormat:'<b>{series.name}</b>: {point.y} councils ({point.percentage:.1f}%)'},
  plotOptions:{bar:{stacking:'percent',borderWidth:0,groupPadding:.08,
   dataLabels:{enabled:true,
    formatter:function(){return this.percentage>=9?fmt(this.point.y):'';},
    style:{fontSize:'10px',color:'#fff',textOutline:'none',fontWeight:'600'}}}},
  legend:{enabled:true},
  series:[0,1,2].map(function(i){return {name:HRVB[i].l,color:HRVB[i].c,
   data:rows.map(function(r){return r.b[i];})};})});
 const desc=rows.slice().sort(function(a,b){return b.hi-a.hi;});
 const top3=desc.slice(0,3).map(function(r){return r.k+' '+r.hi.toFixed(1)+'%';}).join(', ');
 const zeros=rows.filter(function(r){return r.b[2]===0;}).map(function(r){return r.k;});
 const top2n=(desc[0]?desc[0].b[2]:0)+(desc[1]?desc[1].b[2]:0);
 el('chrv1').innerHTML='Each bar is a division&rsquo;s councils split by the band their own score '
  +'falls in. <b>High-Risk share: '+top3+'.</b> '
  +(zeros.length?'No council is High Risk in '+zeros.join(' or ')+'. ':'')
  +'The two divisions with the largest shares hold '+fmt(top2n)+' of the '+fmt(X.bt[2])
  +' High-Risk councils.';}

function hrvCurve(X){
 const S=X.sorted;
 HC('hrv2',{
  chart:{type:'area',height:300,backgroundColor:'transparent',animation:false,spacing:[8,14,8,8]},
  title:{text:null},
  xAxis:{min:0,max:S.length,title:{text:'Councils, ranked by score',style:{fontSize:'11px'}},
   tickPositions:[1,250,500,750,1000,1250,S.length],
   labels:{formatter:function(){return fmt(this.value);}}},
  yAxis:{min:40,max:100,title:{text:'Score on the card (%)',style:{fontSize:'11px'}},
   plotBands:[{from:0,to:X.lo,color:'rgba(220,38,38,.08)'},
    {from:X.lo,to:X.hi,color:'rgba(217,119,6,.08)'},
    {from:X.hi,to:100,color:'rgba(22,163,74,.08)'}],
   plotLines:[{value:X.lo,color:'#dc2626',dashStyle:'Dash',width:1.2,
     label:{text:'High Risk below '+X.lo+'%',align:'left',x:6,
      style:{color:'#b91c1c',fontSize:'10px'}}},
    {value:X.hi,color:'#16a34a',dashStyle:'Dash',width:1.2,
     label:{text:'Low Risk from '+X.hi+'%',align:'left',x:6,
      style:{color:'#15803d',fontSize:'10px'}}}]},
  tooltip:{formatter:function(){
   const r=S[this.x-1];
   if(!r)return false;
   return '<b>Rank '+fmt(this.x)+'</b><br>'+esc(DNAME(HRA.d[r.d]))+' &middot; '+esc(r.u)
    +'<br>Score '+r.p.toFixed(1)+'% &middot; '+esc(HRVB[r.b].l);}},
  legend:{enabled:false},
  plotOptions:{area:{marker:{enabled:false},lineWidth:1.2,fillColor:'rgba(2,132,199,.18)'}},
  series:[{name:'Score',color:'#0284c7',turboThreshold:0,
   data:S.map(function(r,i){return [i+1,r.p];})}]});
 el('chrv2').innerHTML='Every council is a point, ranked by its own score, so the width of each shaded '
  +'stretch is how many councils fall in it. Half score above '+X.med.toFixed(1)+'% and a quarter above '
  +X.q3.toFixed(1)+'%. Green is the Low Risk range ('+X.hi+'% and above: '+fmt(X.bt[0])
  +' councils), amber Medium ('+X.lo+'% to '+X.hi+'%: '+fmt(X.bt[1])+') and red below '+X.lo+'% ('
  +fmt(X.bt[2])+' councils). Nothing is binned, so a council just under or over a cut-off is not hidden '
  +'by a wider bucket.';}

function hrvInd(X){
 const rows=X.ind.slice().sort(function(a,b){return b.ach-a.ach;});
 HC('hrv3',{
  chart:{type:'bar',height:Math.max(420,rows.length*22+70),backgroundColor:'transparent',
   spacing:[8,20,8,8]},
  title:{text:null},
  xAxis:{categories:rows.map(function(o){return HRV_SN[o.i]||o.nm.slice(0,26);}),
   labels:{style:{fontSize:'10.5px',color:C.sec}}},
  yAxis:{min:0,max:100,title:{text:null},labels:{format:'{value}%'},
   plotBands:[{from:0,to:60,color:'rgba(220,38,38,.05)'},
    {from:60,to:79,color:'rgba(217,119,6,.06)'},
    {from:79,to:100,color:'rgba(22,163,74,.05)'}]},
  tooltip:{useHTML:true,formatter:function(){
   const o=this.point.o;
   const rule=String(o.rule||'');
   return '<b>'+esc(o.nm)+'</b><br>'+esc(o.blk)
    +'<br>Marks earned '+o.ach.toFixed(1)+'% ('+fmt(o.got)+' of '+fmt(3*o.ap)+')'
    +'<br>Charged on '+fmt(o.ap)+' councils'
    +(o.z?'<br>'+fmt(o.z)+' councils score 0 ('+o.zs.toFixed(1)+'% of those charged)':'')
    +'<br><i>'+esc(rule.length>150?rule.slice(0,150)+'...':rule)+'</i>';}},
  plotOptions:{bar:{borderWidth:0,borderRadius:2,groupPadding:.05,pointPadding:.06,
   dataLabels:{enabled:true,inside:false,align:'right',x:2,
    formatter:function(){return this.point.o.ach.toFixed(1)+'%';},
    style:{fontSize:'9.5px',color:C.sec,textOutline:'none',fontWeight:'400'}}}},
  legend:{enabled:false},
  series:[{name:'Marks earned',colorByPoint:true,
   data:rows.map(function(o){return {y:o.ach,color:HRVBK[o.b].c,o:o};})}]});
 CKEY('hrv3',HRVBK.map(function(b){return [b.c,b.l];}));
 const worst=rows.slice(-3).reverse();
 const bl=X.blocks.slice().sort(function(a,b){return a.p-b.p;});
 const thin=X.ind.filter(function(o){return o.ap<900;})
  .sort(function(a,b){return a.ap-b.ap;}).slice(0,3)
  .map(function(o){return HRV_SN[o.i]+' '+fmt(o.ap);}).join(', ');
 el('chrv3').innerHTML='The three weakest indicators are <b>'
  +worst.map(function(o){return HRV_SN[o.i]+' '+o.ach.toFixed(1)+'%';}).join(', ')
  +'</b>, each measured as marks earned over the marks the card charges. '
  +esc(bl[0].l)+' is the weakest block at '+bl[0].p.toFixed(1)+'%, against '
  +bl.slice(1).map(function(b){return b.l+' '+b.p.toFixed(1)+'%';}).join(', ')+'. '
  +(thin?'Three indicators are charged on far fewer councils ('+esc(thin)
    +'), so their percentages rest on a thinner base than the rest. ':'');}
