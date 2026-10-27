// ---------- Morning team deployment: campaigns, storage and the day model ----------
// The owner asked, 27-Oct-2026: "for every campaign we collect morning team deployment reports from
// districts in scope ... Morning reports from field comes in intervals like it starts from 8 Am and
// may go to 2 pm till completion due to different reasons like network issues, security incidents,
// boycotts etc." Then: "Normally campaign days are 3 + 2 (3 days of active campaign and 2 days for
// catchup activities and for peshawar and khyber its 5 active days and 2 catchup days and than there
// can be extended catchup request by districts so we would be needing all those days and there should
// be option for selection of campaigns ... along with names of the campaign."
// One row per district per campaign day, typed in here or imported from the 39-column sheet the
// districts already fill. Column F and the free-text remarks are never read or written because they
// carry AIC / UCMO names. Reports stay in this browser, one storage key per campaign.
const MDP_OLDKEY='kpMDP.SNIDNOV26.v1';
const mdpStoreKey=c=>'kpMDP.'+c+'.v2';
const MDP_MAXD=12;                          // open past 7: extended catch-up is asked for per district
const mdpActD=n=>/^(PESHAWAR|KHYBER)$/.test(n)?5:3;
const mdpBaseD=n=>mdpActD(n)+2;             // 3+2 for most districts, 5+2 for Peshawar & Khyber
const mdpPhase=(n,d)=>d<=mdpActD(n)?'active':d<=mdpBaseD(n)?'catch-up':'extended catch-up';
const MDP_CAMPS=[{k:'NOV-26',l:SND.n,st:SND.st,src:SND.src,cur:1}]
 .concat(((typeof CQ!=='undefined'&&CQ&&CQ.camps)||[]).filter(c=>c.l!==SND.n)
  .map(c=>({k:c.v,l:c.l,st:'',src:'the districts that campaign\u2019s own record carries'})));
let MDC='NOV-26',MDR={},MDD=0;
const mdpCampLbl=k=>{k=k||MDC;const c=MDP_CAMPS.find(x=>x.k===k);return c?c.l:String(k);};
const mdpStart=()=>{const c=MDP_CAMPS.find(x=>x.k===MDC);return (c&&c.st)||'';};
const mdpSrcLbl=()=>{const c=MDP_CAMPS.find(x=>x.k===MDC);return (c&&c.src)||'campaign register';};
function mdpCampRows(c){
 try{const d=JSON.parse(localStorage.getItem(mdpStoreKey(c))||'null');
  return d&&d.r&&typeof d.r==='object'?d.r:{};}catch(e){return {};}}
function mdpSave(){
 try{localStorage.setItem(mdpStoreKey(MDC),JSON.stringify({c:MDC,l:mdpCampLbl(MDC),r:MDR}));}
 catch(e){toast('Browser storage is full - download the workbook before clearing it');}}
function mdpLoadCamp(c){
 MDC=c;MDR=mdpCampRows(c);let mig=0;
 if(c==='NOV-26'&&!Object.keys(MDR).length){
  try{const o=JSON.parse(localStorage.getItem(MDP_OLDKEY)||'null');
   if(o&&o.c===SND.n&&o.r&&typeof o.r==='object'){MDR=o.r;mig=1;}}catch(e){}
 }
 for(const k of Object.keys(MDR)){const r=MDR[k];
  if(!r||!Array.isArray(r.p)||r.p.length!==9||!Array.isArray(r.d)||r.d.length!==9
   ||!(r.day>=1)||!(r.day<=MDP_MAXD)||typeof r.n!=='string')delete MDR[k];}
 if(mig){mdpSave();try{localStorage.removeItem(MDP_OLDKEY);}catch(e){}}
 return MDR;
}
const MDP_TYPES=[
 ['mobile','Mobile teams','# Mobile teams'],
 ['inf','Influencers','# of Influencers'],
 ['fixed','Fixed teams','# Fixed teams'],
 ['transit','Transit teams','# Transit teams'],
 ['roam','Roaming teams','# Roaming teams'],
 ['aic','AIC teams','# AICs'],
 ['upec','UPEC chairmen','# UPEC chairmen'],
 ['dcf','DCF teams','# DCF'],
 ['sec','Security','# Security']
];
const MDP_FIELD=[0,2,3,4];
const MDP_H=['DIVISION','District','Campaign start date','Campaign day','Time of update',
 'Time of last team deployed with details, UC, Team #, AIC name etc(This information needs to be entered for those districts where deployment is late )',
 "# of UC's Planned","# of UC's reported"]
 .concat(...MDP_TYPES.map(t=>[t[2]+' planned',t[2]+' deployed']))
 .concat(['# of Security incidents','REMARKS',"# of UC's Awaited"],
  MDP_TYPES.slice(0,7).map(t=>t[1]+' awaited'),['# TTM awaited','# Security awaited','Team Deployment %']);
const MDP_RSN={SEC:'Security incident',NET:'Network / connectivity',BOY:'Boycott / access refusal',TRA:'Transport / access',OTH:'Other'};
const MDP_ST={good:['st-on','On plan'],watch:['st-watch','Watch'],low:['st-behind','Short'],crit:['st-behind','Critical'],no:['st-no','No report']};
const MDP_COL={good:'#15803d',watch:'#d97706',low:'#ea580c',crit:'#b91c1c',no:'#94a3b8'};
const mdpKey=(d,n)=>n+'|'+d;
const mdpGet=(d,n)=>MDR[mdpKey(d,n)]||null;
const mdpVal=id=>{const x=el(id);return x?x.value:'';};
const mdpPad=n=>(n<10?'0':'')+n;
const mdpNow=()=>{const d=new Date();return mdpPad(d.getHours())+':'+mdpPad(d.getMinutes());};
const mdpMin=t=>{const m=/^(\d{1,2}):(\d{2})/.exec(String(t||''));return m?(+m[1])*60+(+m[2]):null;};
const mdpLate=r=>!!(r&&r.at&&mdpMin(r.at)>720);
const mdpDayDate=d=>{const st=mdpStart();if(!st)return '';
 const p=String(st).split('-'),t=new Date(Date.UTC(+p[0],(+p[1]||1)-1,+p[2]||1));
 t.setUTCDate(t.getUTCDate()+(d-1));const z=n=>(n<10?'0':'')+n;
 const iso=t.getUTCFullYear()+'-'+z(t.getUTCMonth()+1)+'-'+z(t.getUTCDate());
 try{return erDateLbl(iso);}catch(e){return iso;}};
const mdpDayTag=d=>'Day '+d+(mdpDayDate(d)?' · '+mdpDayDate(d):'');
mdpLoadCamp('NOV-26');
