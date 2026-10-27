// HRA AT A GLANCE (5/5): the district roll-up download behind the map card.
function hrvCSV(){
 const X=hrvData();
 if(!X.n){toast('The HRA payload is empty');return;}
 const H=['Division','District','Councils','Low Risk','Medium Risk','High Risk','High Risk %',
  'Marks earned %','Mean council score %','Marks earned','Marks charged','Sheets'];
 const rows=X.ann.slice().sort(function(a,b){
  return a.dv===b.dv?(DNAME(a.c)<DNAME(b.c)?-1:1):(a.dv<b.dv?-1:1);}).map(function(o){
  return [o.dv,DNAME(o.c),o.n,o.b[0],o.b[1],o.b[2],
   o.hi==null?'':Math.round(o.hi*10)/10,
   o.p==null?'':Math.round(o.p*10)/10,
   o.m==null?'':Math.round(o.m*10)/10,
   o.ach,o.pos,o.dates];});
 const meanAll=X.ann.reduce(function(s,o){return s+(o.m||0)*o.n;},0)/X.n;
 rows.push(['All','All '+X.nd+' districts',X.n,X.bt[0],X.bt[1],X.bt[2],
  Math.round(X.bt[2]/X.n*1000)/10,Math.round(X.achT/X.posT*1000)/10,Math.round(meanAll*10)/10,
  X.achT,X.posT,'']);
 csvDownload('HRA_district_rollup_'+HRA.asof+'.csv',H,rows);}
