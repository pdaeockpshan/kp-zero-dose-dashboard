function mdpLogPaint(lines){
 const box=el('mdpLog');if(!box||!lines.length)return;
 box.textContent=lines.map(x=>'· '+x).join('\n')+(box.textContent?'\n'+box.textContent:'');
}
async function mdpImportFiles(fl){
 const log=[];let ok=0,bad=0,older=0,out=0;
 for(const f of fl){
  try{
   const res=mdpFromGrid(await mdpGrid(f),f.name);
   ok+=res.ok||0;bad+=res.bad||0;older+=res.older||0;out+=res.out||0;
   log.push(f.name+' — '+(res.msg?res.msg:((res.ok||0)+' merged'+(res.bad?' · '+res.bad+' unknown district':'')+(res.out?' · '+res.out+' outside days 1-'+MDP_MAXD:'')+(res.older?' · '+res.older+' older than the saved copy':''))));
  }catch(e){log.push(f.name+' — could not read ('+((e&&e.message)||'unknown')+')');}
 }
 if(ok){mdpSave();renderMDEP();renderMDPBar();}
 mdpLogPaint(log);
 toast(ok?('Imported '+ok+' district-day report'+(ok===1?'':'s')+' into '+mdpCampLbl()):'No report was imported');
}
function mdpCsv(){
 const R=mdpRows();
 csvRaw(mdpCampLbl().replace(/\s+/g,'_')+'_morning_deployment_'+(MDD?('day'+MDD):'all')+'.csv',
  ['Campaign','District','Division','Category','Campaign days','Reports saved','Last report','UCs reported','UCs planned','UCs awaited','Teams deployed','Teams planned','Field deployment %','Teams awaited','Security incidents','Reason','Status'],
  R.map(o=>[mdpCampLbl(),DNAME(o.n),o.dv,o.cat,o.dy,o.reps,o.rep?('D'+o.last+' '+o.at):'',o.ucr,o.ucp,o.ucAw,o.fd,o.fp,o.pct==null?'':o.pct.toFixed(1),o.awTot,o.inc,o.rsn?(MDP_RSN[o.rsn]||o.rsn):'',MDP_ST[o.st][1]]));
}
