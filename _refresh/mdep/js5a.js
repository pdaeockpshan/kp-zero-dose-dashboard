const MDP_TEAL='FF0D9488';
function mdpCol(n){return n<=26?String.fromCharCode(64+n):'A'+String.fromCharCode(38+n);}
function mdpTimeNum(t){const m=mdpMin(t);return m==null?null:m/1440;}
function mdpHead39(ws,title,sub,note){
 ws.mergeCells(1,1,1,39);const t=ws.getCell(1,1);t.value=title;
 t.font={bold:true,size:14,color:{argb:'FF115E59'}};t.alignment={vertical:'middle'};ws.getRow(1).height=24;
 ws.mergeCells(2,1,2,39);const s=ws.getCell(2,1);s.value=sub;s.font={size:11,color:{argb:'FF334155'}};
 ws.mergeCells(3,1,3,39);const n=ws.getCell(3,1);n.value=note;n.font={size:9.5,italic:true,color:{argb:'FF64748B'}};
 const hr=ws.getRow(4);hr.values=MDP_H;hr.height=54;
 hr.alignment={vertical:'middle',horizontal:'left',wrapText:true};
 hr.font={bold:true,size:9,color:{argb:'FFFFFFFF'}};
 hr.eachCell(c=>{c.fill={type:'pattern',pattern:'solid',fgColor:{argb:MDP_TEAL}};c.border={bottom:{style:'thin',color:{argb:'FF0F766E'}}};});
 ws.views=[{state:'frozen',ySplit:4}];
 const W=[12,18,12,9,9,50,9,9];for(let i=0;i<18;i++)W.push(9);W.push(10,12);for(let i=0;i<10;i++)W.push(11);W.push(10);
 W.forEach((w,j)=>{ws.getColumn(j+1).width=w;});
}
function mdpRows39(ws,rows){
 rows.forEach(v=>{const rr=ws.addRow(v);
  rr.getCell(5).numFmt='h:mm AM/PM';
  for(let j=7;j<=26;j++)rr.getCell(j).numFmt='#,##0';
  for(let j=29;j<=38;j++)rr.getCell(j).numFmt='#,##0';
  rr.getCell(39).numFmt='0.0%';});
 ws.autoFilter={from:{row:4,column:1},to:{row:Math.max(4,ws.rowCount),column:39}};
}
function mdpStoredRows(){
 // every saved day for the scope, so the returned workbook is the full record, not one day's slice
 const out=[];
 mdpBase().forEach(o=>{const dy=o.dy;
  for(let d=1;d<=dy;d++){const r=mdpGet(d,o.n);if(r)out.push({r:r,o:o});}});
 return out.sort((a,b)=>String(a.o.dv).localeCompare(String(b.o.dv))||String(a.r.n).localeCompare(String(b.r.n))||a.r.day-b.r.day);
}
function mdpVals(r,o){
 const c=mdpCalc(r),aw=c.aw,v=[o.dv,DNAME(o.n),mdpStart(),r.day,mdpTimeNum(r.at),'',r.ucp||0,r.ucr||0];
 for(let i=0;i<9;i++){v.push(r.p[i]||0);v.push(r.d[i]||0);}
 v.push(r.inc||0,r.rsn?(r.rsn+' — '+(MDP_RSN[r.rsn]||'')):'');
 v.push(c.ucAw,aw[0],aw[1],aw[2],aw[3],aw[4],aw[5],aw[6],r.ttm||0,aw[8]);
 v.push(c.pct==null?'':Math.round(c.pct*10)/1000);
 return v;
}
function mdpGot(wb,file){
 return wb.xlsx.writeBuffer().then(buf=>{const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([buf],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  a.download=file;document.body.appendChild(a);a.click();a.remove();toast('Excel downloaded');return true;});
}
