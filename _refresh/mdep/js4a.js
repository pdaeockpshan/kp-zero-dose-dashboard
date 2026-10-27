function mdpCell(v){
 if(v==null)return '';
 if(v instanceof Date)return v;
 if(typeof v==='object'){
  if(v.result!=null)return v.result;
  if(v.text!=null)return v.text;
  if(Array.isArray(v.richText))return v.richText.map(t=>t.text||'').join('');
  return '';
 }
 return v;
}
function mdpHeadIdx(H){
 const N=H.map(mdpNorm),ix={};
 N.forEach((k,j)=>{
  if(/^DIVISION/.test(k))ix.div=j;
  if(/^DISTRICT/.test(k)||k==='DIST')ix.dist=j;
  if(/CAMPAIGNDAY/.test(k)||k==='DAY')ix.day=j;
  if(/^TIMEOF/.test(k))ix.at=j;
  if(/UC.*PLANNED/.test(k))ix.ucp=j;
  if(/UC.*REPORTED/.test(k))ix.ucr=j;
  if(/SECURITYINCIDENT/.test(k)||/^INCIDENTS?$/.test(k))ix.inc=j;
  if(/^REMARK/.test(k)||/^REASON/.test(k))ix.rsn=j;
  if(/TTM/.test(k)&&/AWAIT/.test(k))ix.ttm=j;
 });
 const TOK={mobile:'MOBILE',inf:'INFLUENC',fixed:'FIXED',transit:'TRANSIT',roam:'ROAM',aic:'AIC',upec:'UPEC',dcf:'DCF',sec:'SECURITY'};
 MDP_TYPES.forEach((t,i)=>{
  const tok=TOK[t[0]];
  N.forEach((k,j)=>{
   if(k.indexOf(tok)<0)return;
   if(/DEPLOY|REPORTED|ACTUAL/.test(k)){if(ix['d'+i]==null)ix['d'+i]=j;return;}
   if(/PLANN|TARGET|REQUIRED|SANCTION/.test(k)){if(ix['p'+i]==null)ix['p'+i]=j;}
  });
 });
 return ix;
}
function mdpFromGrid(grid,file){
 let hi=-1,ix=null;
 for(let i=0;i<Math.min(12,grid.length);i++){
  const t=mdpHeadIdx((grid[i]||[]).map(mdpCell));
  if(t.dist!=null&&t.day!=null){hi=i;ix=t;break;}
 }
 if(hi<0)return {ok:0,bad:0,msg:'no header row with District and Campaign day in the first 12 rows'};
 let ok=0,bad=0,older=0,out=0;
 for(let i=hi+1;i<grid.length;i++){
  const row=grid[i]||[],ds=mdpCell(row[ix.dist]);
  const dstr=String(ds==null?'':ds).trim();
  if(!dstr||/^total|^grand/i.test(dstr))continue;
  const n=mdpDist(ds);
  if(!n){bad++;continue;}
  let day=Math.round(mdpNumV(row[ix.day]));
  if(!day)day=MDD||1;
  if(day<1||day>MDP_MAXD){out++;continue;}
  const at=ix.at!=null?mdpTimeV(row[ix.at]):'';
  const r={n:n,day:day,at:at||'',ucp:ix.ucp!=null?Math.round(mdpNumV(row[ix.ucp])):0,
   ucr:ix.ucr!=null?Math.round(mdpNumV(row[ix.ucr])):0,
   p:MDP_TYPES.map((t,k)=>ix['p'+k]!=null?Math.round(mdpNumV(row[ix['p'+k]])):0),
   d:MDP_TYPES.map((t,k)=>ix['d'+k]!=null?Math.round(mdpNumV(row[ix['d'+k]])):0),
   ttm:ix.ttm!=null?Math.round(mdpNumV(row[ix.ttm])):0,
   inc:ix.inc!=null?Math.round(mdpNumV(row[ix.inc])):0,
   rsn:ix.rsn!=null?mdpRsnCode(mdpCell(row[ix.rsn])):'',ts:new Date().toISOString()};
  if(!r.ucp){const sc=mdpScope().find(o=>o.n===n);r.ucp=sc?sc.uc:0;}
  const old=MDR[mdpKey(day,n)];
  if(old&&old.at&&r.at&&mdpMin(old.at)>mdpMin(r.at)){older++;continue;}
  MDR[mdpKey(day,n)]=r;ok++;
 }
 return {ok:ok,bad:bad,older:older,out:out};
}
async function mdpGrid(f){
 if(/\.csv$/i.test(f.name))return hrtCsv(await f.text());
 const X=await xlLib(),wb=new X.Workbook();await wb.xlsx.load(await f.arrayBuffer());
 const ws=wb.worksheets[0],g=[];
 ws.eachRow({includeEmpty:false},row=>{const a=[];row.eachCell({includeEmpty:true},c=>{a[c.col-1]=c.value;});g.push(a);});
 return g;
}
