// HRA AT A GLANCE (1/3): payload roll-ups, hint and the render hook.
// Read by patch_hrdv_ui.py and inserted into the master ahead of hrtWire(). Nothing here writes to
// the compiled card: the figures come from const HRA, the dashboard payload.
const HRVB=[{c:'#16a34a',l:'Low Risk'},{c:'#d97706',l:'Medium Risk'},{c:'#dc2626',l:'High Risk'}];
const HRVBK=[{c:'#0284c7',l:'Terrain & security'},{c:'#7c3aed',l:'Epidemiology & surveillance'},
 {c:'#ea580c',l:'SIA operations'},{c:'#0d9488',l:'EPI / PEI synergy'}];
const HRV_DV={HAZARA:'Hazara',MALAKAND:'Malakand',BANNU:'Bannu',PESHAWAR:'Peshawar',DIKHAN:'DI Khan',
 KOHAT:'Kohat',MARDAN:'Mardan'};
const HRV_ABBR={KOLAIPALAS:'Palas',CHITRALUPPER:'Chitral U',CHITRALLOWER:'Chitral L',DIRUPPER:'Dir U',
 DIRLOWER:'Dir L',KOHISTANUPPER:'Kohistan U',KOHISTANLOWER:'Kohistan L','WAZIR-S Upper':'S Wazir U',
 'WAZIR-S Lower':'S Wazir L','WAZIR-N':'N Wazir'};
const HRV_SN=['G1/G2/G3 categorisation','Access status','Security-compromised areas',
 'Borders Afghanistan','Confirmed polio cases','cVDPV cases','Polio-compatible cases',
 'Orphan virus detected','Zero-dose NPAFP case','NPAFP with 7+ OPV doses','cVDPV/WPV in environment',
 'Annualised NPAFP rate','Stool adequacy','NPEV isolation rate','Silent UCs (36 months)','MPQA passed',
 'FFM in last 3 SIAs','Operational issues in missed','Still-missed % of target','LQAS lots passed',
 'Still missed among missed','UCs with >5% HRMP','EPI UC category','Penta-3 / OPV3 coverage','IPV in EPI',
 '90%+ OPV3 coverage','Sentinel events'];
let _HRVD=null,_HRVLAB=null,_HRVR=false;
const HRV_MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function hrvD(s){const p=String(s).split('-');
 return p.length===3?(+p[2])+' '+HRV_MO[+p[1]-1]+' '+p[0]:String(s);}

function hrvBlk(n){const s=String(n).toLowerCase();
 return /^geograph/.test(s)?0:/^epidem/.test(s)?1:/^sia/.test(s)?2:3;}
function hrvDates(mask){const out=[];(HRA.v||[]).forEach(function(d,i){if(mask&(1<<i))out.push(d);});
 return out;}

function hrvData(){
 if(_HRVD)return _HRVD;
 const U=(typeof HRA!=='undefined'&&HRA.u)||[],D=(typeof HRA!=='undefined'&&HRA.d)||[];
 if(!U.length){_HRVD={n:0};return _HRVD;}
 const HI=HRA.thr[0],LO=HRA.thr[1];
 const kg={};(typeof KPGEO!=='undefined'?KPGEO.d:[]).forEach(function(p){kg[p.c]=p.v;});
 const dvOf=function(c){
  const k=kg[c]||(typeof D2DV!=='undefined'?(D2DV[c]||null):null)||'Other';
  return HRV_DV[k]||k;};
 const ix={};D.forEach(function(c,i){ix[c]=i;});
 const ann=D.map(function(c){return {c:c,dv:dvOf(c),n:0,b:[0,0,0],oct:0,ach:0,pos:0,sum:0,vm:0};});
 const div={};
 U.forEach(function(r){
  const o=ann[ix[D[r[0]]]];if(!o)return;
  const b=r[6];
  o.n++;o.b[b]++;o.ach+=r[3];o.pos+=r[4];o.sum+=r[5];o.vm|=(1<<r[7]);
  if(r[7]===0)o.oct++;
  const k=o.dv;
  if(!div[k])div[k]={n:0,b:[0,0,0]};
  div[k].n++;div[k].b[b]++;});
 ann.forEach(function(o){
  o.hi=o.n?o.b[2]/o.n*100:null;
  o.p=o.pos?o.ach/o.pos*100:null;
  o.m=o.n?o.sum/o.n:null;
  o.dates=hrvDates(o.vm).join(' & ');});
 const ind=HRA.k.map(function(k,i){
  let ap=0,got=0,z=0;
  U.forEach(function(r){const s=r[8][i];
   if(s==null||s<0)return;
   ap++;got+=s;if(s===0)z++;});
  return {i:i,nm:k[1],blk:k[0],rule:k[2],ap:ap,got:got,z:z,b:hrvBlk(k[0]),
   ach:ap?got/(3*ap)*100:null,zs:ap?z/ap*100:null};});
 const blocks=HRVBK.map(function(x,i){return {c:x.c,l:x.l,got:0,pos:0,p:null};});
 ind.forEach(function(o){blocks[o.b].got+=o.got;blocks[o.b].pos+=3*o.ap;});
 blocks.forEach(function(o){o.p=o.pos?o.got/o.pos*100:null;});
 const scores=U.map(function(r){return r[5];}).filter(function(v){return v!=null;})
  .sort(function(a,b){return a-b;});
 const q=function(f){return scores.length?scores[Math.min(scores.length-1,Math.floor(f*scores.length))]:null;};
 const bt=[0,0,0],vint=[0,0];let achT=0,posT=0;
 U.forEach(function(r){bt[r[6]]++;vint[r[7]]=(vint[r[7]]||0)+1;achT+=r[3];posT+=r[4];});
 _HRVD={n:U.length,nd:D.length,ann:ann,div:div,ind:ind,blocks:blocks,bt:bt,vint:vint,
  hi:HI,lo:LO,achT:achT,posT:posT,
  min:scores.length?scores[0]:null,max:scores.length?scores[scores.length-1]:null,
  med:q(.5),q1:q(.25),q3:q(.75),
  mixed:ann.filter(function(o){return o.n&&(o.vm&1)&&o.vm!==1;}).map(function(o){
   return {c:o.c,old:o.n-o.oct,n:o.n};}),
  sorted:U.map(function(r){return {p:r[5],d:r[0],u:r[1],b:r[6]};})
   .sort(function(a,b){return b.p-a.p;})};
 return _HRVD;}

function hrvRender(){
 const h=el('hrvHint');
 if(!h)return;
 const X=hrvData();
 if(!X.n){h.innerHTML='The HRA payload is empty, so there is nothing to chart.';
  el('chrv1').textContent='';el('chrv2').textContent='';el('chrv3').textContent='';
  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';
  return;}
 hrvHint(X);
 hrvBand(X);
 hrvCurve(X);
 hrvInd(X);
 hrvMap(X);
 const K=el('hrvMK');
 if(K)K.onchange=function(){hrvMap(hrvData());};
 const B=el('btnHRVcsv');
 if(B)B.onclick=hrvCSV;
 _HRVR=true;}

function hrvHint(X){
 const dvn=Object.keys(X.div).length;
 const mix=X.mixed.map(function(o){
  return DNAME(o.c)+': '+o.old+' of '+o.n+' still on the March sheet';}).join('; ');
 el('hrvHint').innerHTML='<b>'+fmt(X.n)+' councils in '+fmt(X.nd)+' districts and '+dvn
  +' divisions carry an HRA reading dated '+esc(hrvD(HRA.asof))+'.</b> On the card&rsquo;s own axis '
  +fmt(X.bt[0])+' are Low Risk, '+fmt(X.bt[1])+' Medium and '+fmt(X.bt[2])+' High ('
  +(X.bt[2]/X.n*100).toFixed(1)+'%). A high percentage here is a safe council &mdash; this is not the '
  +'combined UC risk score used on the Cross-cutting pages, and the two are never blended. '
  +fmt(X.vint[0])+' councils carry the 26 Oct Mardan-division sheets and '+fmt(X.vint[1])
  +' still carry the 26-Mar sheet'+(mix?' ('+esc(mix)+')':'')+'. The '+HRA.nx.length
  +' criteria the card leaves unscored are not in these figures, and neither is anything typed into the '
  +'card above: that sheet belongs to its own year, month and campaign.';}
