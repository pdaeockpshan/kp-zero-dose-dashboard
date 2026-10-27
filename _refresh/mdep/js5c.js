async function mdpExportTpl(){
 try{
  const X=await xlLib(),wb=new X.Workbook(),ws=wb.addWorksheet('Morning report');
  const d=Math.min(MDP_MAXD,Math.max(1,+mdpVal('mdpTplDay')||1));
  const sc=mdpBase().filter(o=>d<=mdpBaseD(o.n)||!!mdpGet(d,o.n))
   .sort((a,b)=>String(a.dv).localeCompare(String(b.dv))||String(a.n).localeCompare(String(b.n)));
  if(!sc.length){
   toast('No district is in the '+mdpCampLbl()+' register for day '+d
    +(d>7?' — an extended catch-up day needs the district to ask for it first':''));
   return false;
  }
  const ph=d<=3?'active campaign day · every district'
   :d<=5?'day '+d+' · every district (Peshawar and Khyber are still active)'
   :d<=7?'catch-up day · Peshawar and Khyber':'extended catch-up · only the districts that asked for it';
  mdpHead39(ws,mdpCampLbl()+' — morning team deployment return, day '+d,
   'Day '+d+' · '+ph+(mdpDayDate(d)?' · '+mdpDayDate(d):'')
    +(mdpStart()?' · campaign start '+mdpStart():' · campaign start date not recorded'),
   'One row per district. Fill time of update, UCs reported, deployed teams, incidents and the reason; planned teams are pre-filled from the last saved report where one exists. Awaited and the deployment % are formulas — leave them alone.');
  sc.forEach(o=>{
   const sv=mdpGet(d,o.n),lp=(sv&&sv.p)||mdpLastPlan(o.n)||[];
   const v=[o.dv,DNAME(o.n),mdpStart(),d,null,'',sv?sv.ucp:o.uc,sv?sv.ucr:null];
   for(let i=0;i<9;i++){v.push(lp[i]||0);v.push(sv?(sv.d[i]||0):null);}
   v.push(0,'');
   for(let i=0;i<11;i++)v.push(null);
   const r=ws.addRow(v),R=r.number;
   const f=(c,x)=>{r.getCell(c).value={formula:x};};
   f(29,'MAX(0,G'+R+'-H'+R+')');
   f(30,'MAX(0,I'+R+'-J'+R+')');
   f(31,'MAX(0,K'+R+'-L'+R+')');
   f(32,'MAX(0,M'+R+'-N'+R+')');
   f(33,'MAX(0,O'+R+'-P'+R+')');
   f(34,'MAX(0,Q'+R+'-R'+R+')');
   f(35,'MAX(0,S'+R+'-T'+R+')');
   f(36,'MAX(0,U'+R+'-V'+R+')');
   f(38,'MAX(0,Y'+R+'-Z'+R+')');
   f(39,'IFERROR((J'+R+'+N'+R+'+P'+R+'+R'+R+')/(I'+R+'+K'+R+'+M'+R+'+O'+R+'),"")');
  });
  for(let i=5;i<=ws.rowCount;i++){
   const rr=ws.getRow(i);
   rr.getCell(5).numFmt='h:mm AM/PM';
   for(let j=7;j<=26;j++)rr.getCell(j).numFmt='#,##0';
   for(let j=29;j<=38;j++)rr.getCell(j).numFmt='#,##0';
   rr.getCell(39).numFmt='0.0%';
  }
  ws.autoFilter={from:{row:4,column:1},to:{row:Math.max(4,ws.rowCount),column:39}};
  const d2=wb.addWorksheet('How to fill');
  d2.getColumn(1).width=118;
  mdpReadMe().forEach((t,i)=>{const r=d2.addRow([t]);
   r.alignment={wrapText:true,vertical:'top'};
   r.font=i===0?{bold:true,size:12,color:{argb:'FF115E59'}}:{size:10};});
  return await mdpGot(wb,mdpCampLbl().replace(/\s+/g,'_')+'_morning_return_day'+d+'.xlsx');
 }catch(e){console.error('mdp template',e);toast('The template could not be built: '+((e&&e.message)||'unknown error'));}
}
