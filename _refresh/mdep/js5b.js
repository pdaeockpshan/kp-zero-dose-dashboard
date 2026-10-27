function mdpPlain(R){
 const dv=mdpVal('mdpDiv'),dd=mdpVal('mdpDist');
 if(dd)return 'district '+DNAME(dd);
 if(dv)return 'division '+dv+' ('+R.length+' districts)';
 return 'KP — all '+R.length+' districts in the '+mdpCampLbl()+' register';
}
function mdpShtTbl(ws,head,rows){
 const hr=ws.addRow(head);hr.height=30;
 hr.font={bold:true,size:9,color:{argb:'FFFFFFFF'}};
 hr.alignment={wrapText:true,vertical:'middle'};
 hr.eachCell(c=>{c.fill={type:'pattern',pattern:'solid',fgColor:{argb:MDP_TEAL}};});
 rows.forEach(r=>ws.addRow(r));
 ws.views=[{state:'frozen',ySplit:1}];
 head.forEach((h,i)=>{ws.getColumn(i+1).width=Math.max(11,Math.min(46,String(h).length+4));});
}
async function mdpExportBoard(){
 try{
  const X=await xlLib(),wb=new X.Workbook(),R=mdpRows(),T=mdpTot(R),S=mdpStoredRows();
  const day=MDD?mdpDayTag(MDD):'All reported days';
  const plain=mdpPlain(R);
  const ws=wb.addWorksheet('Morning report');
  mdpHead39(ws,mdpCampLbl()+' — morning team deployment',day+' · '+plain,
   'Every saved district-day report in the current filter — '+S.length+' row'+(S.length===1?'':'s')+'. Column F and the free-text remarks are not collected; REMARKS carries the reason code only.');
  mdpRows39(ws,S.map(x=>mdpVals(x.r,x.o)));
  const d1=wb.addWorksheet('District summary');
  mdpShtTbl(d1,['District','Division','Category','Campaign days','Reports saved','Last report','UCs reported','UCs planned','UCs awaited','Teams deployed','Teams planned','Deployment %','Teams awaited','Incidents','Reason','Status'],
   R.map(o=>[DNAME(o.n),o.dv,o.cat,o.dy,o.reps,o.rep?('D'+o.last+(o.at?' '+o.at:'')):'',o.ucr,o.ucp,o.ucAw,o.fd,o.fp,o.pct==null?'':Math.round(o.pct*10)/1000,o.rep?o.awTot:'',o.rep?o.inc:'',o.rsn?(MDP_RSN[o.rsn]||o.rsn):'',MDP_ST[o.st][1]]));
  d1.getColumn(12).numFmt='0.0%';
  const G={};
  R.forEach(o=>{const g=G[o.dv]||(G[o.dv]={dv:o.dv,n:0,rep:0,ucp:0,ucr:0,fp:0,fd:0,aw:0,inc:0});
   g.n++;g.ucp+=o.ucp;g.ucr+=o.ucr;
   if(o.rep){g.rep++;g.fp+=o.fp;g.fd+=o.fd;g.aw+=o.awTot;g.inc+=o.inc;}});
  const gs=Object.keys(G).sort().map(k=>G[k]);
  const d2=wb.addWorksheet('Division summary');
  mdpShtTbl(d2,['Division','Districts','Reported','Teams deployed','Teams planned','Deployment %','UCs reported','UCs planned','Teams awaited','Incidents'],
   gs.map(g=>[g.dv,g.n,g.rep,g.fd,g.fp,g.fp?Math.round(g.fd/g.fp*1000)/1000:'',g.ucr,g.ucp,g.aw,g.inc]));
  d2.addRow(['TOTAL — '+plain,T.n,T.rep,T.fd,T.fp,T.pct==null?'':Math.round(T.pct*10)/1000,T.ucr,T.ucp,T.aw,T.inc]).font={bold:true};
  d2.getColumn(6).numFmt='0.0%';
  const d3=wb.addWorksheet('Read me');
  d3.getColumn(1).width=118;
  mdpReadMe().forEach((t,i)=>{const r=d3.addRow([t]);
   r.alignment={wrapText:true,vertical:'top'};
   r.font=i===0?{bold:true,size:12,color:{argb:'FF115E59'}}:{size:10};});
  return await mdpGot(wb,mdpCampLbl().replace(/\s+/g,'_')+'_morning_deployment_'+(MDD?'day'+MDD:'all')+'.xlsx');
 }catch(e){console.error('mdp workbook',e);toast('The workbook could not be built: '+((e&&e.message)||'unknown error'));}
}
