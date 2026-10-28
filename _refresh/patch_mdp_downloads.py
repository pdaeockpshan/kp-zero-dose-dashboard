"""Share buttons for every morning-deployment chart and roll-up, plus a district summary card.

The owner asked (28-Oct-2026) for a JPEG / PNG / Excel download on the Divisional roll-up, a
PPTX / JPEG / PNG / Excel-table download on each of the four charts, and a small district-wise
summary table. The map already had its own exports, so the new code follows the same two routes
it uses: clone the drawn SVG and rasterise it through a canvas for images, and hand a header +
rows pair to `csvDownload` for the workbook. Nothing is recomputed differently from the screen:
the chart exports read the live Highcharts instance in `CH[id]`, and the two table exports run
the same `mdpRows` / `mdpDivAgg` the tables are drawn from.

Run: python _refresh/patch_mdp_downloads.py   (master only, idempotent)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CSS_OLD = '#mdpMap svg{display:block;max-width:100%;height:auto}'
CSS_NEW = (CSS_OLD + '\n'
           '.mdpdl,.chdl{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;margin:0 0 4px}\n'
           '.mdpdl .btn,.chdl .btn{padding:2px 8px;font-size:11px;line-height:1.35}')

DIV_OLD = ' <div><h3>Division roll-up</h3><table class="shtbl" id="tMDPDiv"></table></div>'
DIV_NEW = (' <div><h3>Division roll-up</h3>\n'
           ' <div class="mdpdl noprint"><button class="btn" data-mdptbl="div" data-k="jpg" '
           'title="The division roll-up as a JPG image to share">JPG</button>'
           '<button class="btn" data-mdptbl="div" data-k="png">PNG</button>'
           '<button class="btn" data-mdptbl="div" data-k="xlsx" '
           'title="The division roll-up as an Excel table">Excel</button></div>\n'
           ' <table class="shtbl" id="tMDPDiv"></table></div>')

GRID_OLD = '''<div class="grid2 noprint">
 <div class="card"><div id="mdp1" class="ch"></div><div class="cap" id="capmdp1"></div></div>
 <div class="card"><div id="mdp2" class="ch"></div><div class="cap" id="capmdp2"></div></div>
 <div class="card"><div id="mdp3" class="ch"></div><div class="cap" id="capmdp3"></div></div>
 <div class="card"><div id="mdp4" class="ch"></div><div class="cap" id="capmdp4"></div></div>
</div>'''

def card(i):
    b = ('<div class="chdl noprint">'
         '<button class="btn" data-mdpch="mdp{i}" data-k="pptx" title="A PowerPoint slide with this chart">PPTX</button>'
         '<button class="btn" data-mdpch="mdp{i}" data-k="jpg">JPG</button>'
         '<button class="btn" data-mdpch="mdp{i}" data-k="png">PNG</button>'
         '<button class="btn" data-mdpch="mdp{i}" data-k="xlsx" '
         'title="The numbers behind this chart as an Excel table">Excel table</button></div>').format(i=i)
    return (' <div class="card">' + b + '<div id="mdp{i}" class="ch"></div>'
            '<div class="cap" id="capmdp{i}"></div></div>').format(i=i)

SUMMARY_CARD = '''<div class="card noprint">
<div class="tblhdr"><h3 style="margin:0">District summary &mdash; deployment at a glance</h3><span class="cnt" id="mdpSmCnt"></span><span style="flex:1"></span><button class="btn" data-mdptbl="small" data-k="jpg" title="The district summary as a JPG image to share">JPG</button><button class="btn" data-mdptbl="small" data-k="png">PNG</button><button class="btn" data-mdptbl="small" data-k="xlsx" title="The district summary as an Excel table">Excel table</button></div>
<div class="scroll" style="max-height:420px"><table id="tMDPSmall"></table></div>
<div class="cap" id="capMDPSmall"></div>
</div>

'''

GRID_NEW = SUMMARY_CARD + '''<div class="grid2 noprint">
''' + '\n'.join(card(i) for i in (1, 2, 3, 4)) + '\n</div>'

HEAT_OLD = ('<div class="tblhdr"><h3 style="margin:0">Deployment by team type and district</h3>'
            '<span class="cnt" id="mdpHcnt"></span></div>')
HEAT_NEW = ('<div class="tblhdr"><h3 style="margin:0">Deployment by team type and district</h3>'
            '<span class="cnt" id="mdpHcnt"></span><span style="flex:1"></span>'
            '<button class="btn" id="btnMDPHxls" title="The matrix as an Excel table">Excel table</button></div>')

AGG_OLD = ''' const G={};
 R.forEach(o=>{const g=G[o.dv]||(G[o.dv]={dv:o.dv,n:0,rep:0,fp:0,fd:0,aw:0,ucp:0,ucr:0,inc:0});
  g.n++;g.ucp+=o.ucp;g.ucr+=o.ucr;
  if(o.rep){g.rep++;g.fp+=o.fp;g.fd+=o.fd;g.aw+=o.awTot;g.inc+=o.inc;}});
 const gs=Object.keys(G).sort().map(x=>G[x]);'''

AGG_NEW = ' const gs=mdpDivAgg(R);'

RENDER_OLD = '  mdpKpis(R,T);mdpCharts(R,T);mdpCharts2(R,T);mdpHeat(R);mdpTable(R);mdpMap(R);mdpSheetDraw(R,T);'
RENDER_NEW = '  mdpKpis(R,T);mdpSmall(R,T);mdpCharts(R,T);mdpCharts2(R,T);mdpHeat(R);mdpTable(R);mdpMap(R);mdpSheetDraw(R,T);'

JS_ANCHOR = '\nmdpMapWire();'

JS_NEW = r'''

// ---------- share: table images, chart images, slides and sheets ----------
// Every route here reads what is already on screen: the chart exports take the live Highcharts
// instance in CH[id], and the table exports run the same mdpRows / mdpDivAgg the tables print.
let _MDPDLW=0;
const MDP_CHX={mdp1:'Division',mdp2:'Team type',mdp3:'Campaign day',mdp4:'District'};
const mdpSlug=s=>String(s||'morning deployment').toLowerCase().replace(/[^a-z0-9]+/g,'_')
 .replace(/^_+|_+$/g,'').slice(0,64)||'morning_deployment';
function mdpShareFile(key,ext){
 return 'MDP_'+mdpSlug(key)+'_'+mdpCampLbl().replace(/[^A-Za-z0-9]+/g,'_')+'_'
  +(MDD?'day'+MDD:'all_days')+'_'+new Date().toISOString().slice(0,10)+ext;
}
function mdpShareSave(url,name){
 const a=document.createElement('a');a.href=url;a.download=name;a.rel='noopener';
 document.body.appendChild(a);a.click();a.remove();
}
function mdpLiveWhen(){
 const t=MDLIVE&&MDLIVE.at?new Date(MDLIVE.at):null;
 return t?('sheet read '+mdpPad(t.getHours())+':'+mdpPad(t.getMinutes())):'sheet not read yet';
}
function mdpDivAgg(R){
 const G={};
 R.forEach(o=>{const g=G[o.dv]||(G[o.dv]={dv:o.dv,n:0,rep:0,fp:0,fd:0,aw:0,ucp:0,ucr:0,inc:0});
  g.n++;g.ucp+=o.ucp;g.ucr+=o.ucr;
  if(o.rep){g.rep++;g.fp+=o.fp;g.fd+=o.fd;g.aw+=o.awTot;g.inc+=o.inc;}});
 return Object.keys(G).sort().map(x=>G[x]);
}
function mdpWrapText(x,t,w){
 const out=[];let cur='';
 String(t==null?'':t).split(/\s+/).forEach(v=>{const s=cur?cur+' '+v:v;
  if(x.measureText(s).width>w&&cur){out.push(cur);cur=v;}else cur=s;});
 if(cur)out.push(cur);return out;
}
function mdpTblCanvas(o,kind){
 const S=2,PAD=18,HH=32,RH=25,FS=12.5;
 const m=document.createElement('canvas').getContext('2d');
 m.font=FS+'px "Segoe UI",Arial,sans-serif';
 const all=(o.rows||[]).concat(o.foot?[o.foot]:[]);
 const cw=o.H.map((h,i)=>{let w=m.measureText(String(h)).width;
  all.forEach(r=>{w=Math.max(w,m.measureText(String(r[i]==null?'':r[i])).width);});
  return Math.ceil(w)+26;});
 let TW=cw.reduce((a,b)=>a+b,0);
 if(TW<560)cw[0]+=560-TW;else if(TW>1320)cw=cw.map(v=>Math.round(v*1320/TW));
 TW=cw.reduce((a,b)=>a+b,0);
 const W=TW+PAD*2,tw=W-PAD*2;
 m.font='bold 18px "Segoe UI",Arial,sans-serif';
 const tL=mdpWrapText(m,o.T||'',tw);
 m.font='12.5px "Segoe UI",Arial,sans-serif';
 const sL=o.S?mdpWrapText(m,o.S,tw):[];
 m.font='11.5px "Segoe UI",Arial,sans-serif';
 const cL=o.C?mdpWrapText(m,o.C,tw):[];
 const rows=o.rows||[];
 let top=26+(tL.length-1)*24+22;
 if(sL.length)top+=(sL.length-1)*17+12;
 const tableH=HH+rows.length*RH+(o.foot?RH+2:0);
 const H=top+tableH+18+Math.max(0,cL.length-1)*16+14;
 const cv=document.createElement('canvas');cv.width=Math.ceil(W*S);cv.height=Math.ceil(H*S);
 const x=cv.getContext('2d');x.scale(S,S);
 x.fillStyle='#ffffff';x.fillRect(0,0,W,H);
 x.textBaseline='alphabetic';
 x.fillStyle='#0f172a';x.font='bold 18px "Segoe UI",Arial,sans-serif';
 tL.forEach((l,i)=>x.fillText(l,PAD,26+i*24));
 if(sL.length){x.fillStyle='#475569';x.font='12.5px "Segoe UI",Arial,sans-serif';
  const y0=26+(tL.length-1)*24+18;sL.forEach((l,i)=>x.fillText(l,PAD,y0+i*17));}
 x.fillStyle='#0d9488';x.fillRect(PAD,top,TW,HH);
 x.fillStyle='#ffffff';x.font='bold 12.5px "Segoe UI",Arial,sans-serif';
 let cx=PAD;
 o.H.forEach((h,i)=>{x.textAlign=i?'right':'left';x.fillText(String(h),i?cx+cw[i]-10:cx+10,top+21);cx+=cw[i];});
 x.textAlign='left';
 let ry=top+HH;
 rows.forEach((r,ri)=>{
  if(ri%2){x.fillStyle='#f8fafc';x.fillRect(PAD,ry,TW,RH);}
  x.fillStyle='#1f2937';x.font=FS+'px "Segoe UI",Arial,sans-serif';
  let kx=PAD;
  r.forEach((v,ci)=>{x.textAlign=ci?'right':'left';
   x.fillText(String(v==null?'':v),ci?kx+cw[ci]-10:kx+10,ry+RH-8);kx+=cw[ci];});
  x.textAlign='left';
  x.strokeStyle='#e5e7eb';x.lineWidth=1;x.beginPath();x.moveTo(PAD,ry+RH+0.5);
  x.lineTo(PAD+TW,ry+RH+0.5);x.stroke();
  ry+=RH;
 });
 if(o.foot){
  x.fillStyle='#ecfdf5';x.fillRect(PAD,ry,TW,RH+2);
  x.strokeStyle='#0d9488';x.lineWidth=1.5;x.beginPath();x.moveTo(PAD,ry+0.5);x.lineTo(PAD+TW,ry+0.5);x.stroke();
  x.fillStyle='#0f172a';x.font='bold 12.5px "Segoe UI",Arial,sans-serif';
  let fx=PAD;
  o.foot.forEach((v,ci)=>{x.textAlign=ci?'right':'left';
   x.fillText(String(v==null?'':v),ci?fx+cw[ci]-10:fx+10,ry+RH-8);fx+=cw[ci];});
  x.textAlign='left';ry+=RH+2;
 }
 if(cL.length){x.fillStyle='#64748b';x.font='11.5px "Segoe UI",Arial,sans-serif';
  const y0=ry+18;cL.forEach((l,i)=>x.fillText(l,PAD,y0+i*16));}
 return {url:kind==='jpeg'?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png'),
  ext:kind==='jpeg'?'.jpg':'.png',w:W,h:H};
}
function mdpDivSpec(){
 const R=mdpRows(),T=mdpTot(R),gs=mdpDivAgg(R);
 return {key:'division_roll_up',
  T:'Division roll-up \u2014 morning field-team deployment',
  S:mdpCampLbl()+' \u00b7 '+mdpDayLbl()+' \u00b7 '+mdpLbl(R),
  H:['Division','Districts','Reporting','Teams deployed / planned','Dep %','UCs / planned','Awaited','Inc.'],
  rows:gs.map(g=>[g.dv,String(g.n),String(g.rep),nfmt(g.fd)+' / '+nfmt(g.fp),
   g.fp?pfmt(g.fd/g.fp*100):'\u2013',nfmt(g.ucr)+' / '+nfmt(g.ucp),nfmt(g.aw),nfmt(g.inc)]),
  foot:['Campaign total',String(T.n),String(T.rep),nfmt(T.fd)+' / '+nfmt(T.fp),pfmt(T.pct),
   nfmt(T.ucr)+' / '+nfmt(T.ucp),nfmt(T.aw),nfmt(T.inc)],
  C:'Weighted across the reporting districts of each division. Field teams are mobile, fixed, transit '
   +'and roaming, so Dep % is those four deployed \u00f7 planned. Awaited = planned \u2212 deployed. '
   +'Snapshot: '+mdpLiveWhen()+'.'};
}
function mdpSmallSpec(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R);
 return {key:'district_summary',
  T:'District summary \u2014 morning field-team deployment',
  S:mdpCampLbl()+' \u00b7 '+mdpDayLbl()+' \u00b7 '+mdpLbl(R),
  H:['District','Division','Days','Teams deployed / planned','Dep %','UCs rep. / planned','Status'],
  rows:R.map(o=>[DNAME(o.n),o.dv,String(o.reps||0),o.rep?(nfmt(o.fd)+' / '+nfmt(o.fp)):'\u2013',
   o.pct==null?'\u2013':pfmt(o.pct),nfmt(o.ucr)+' / '+nfmt(o.ucp),MDP_ST[o.st][1]]),
  foot:['Campaign total',String(T.n)+' districts',String(T.rep)+' reported',nfmt(T.fd)+' / '+nfmt(T.fp),
   pfmt(T.pct),nfmt(T.ucr)+' / '+nfmt(T.ucp),T.good+' on plan'],
  C:'Lowest deployment first. Days counts the campaign days that district has reported in this '
   +'selection. A district with no report keeps its plan but shows no %. Snapshot: '+mdpLiveWhen()+'.'};
}
function mdpDivXlsx(){
 const R=mdpRows(),T=mdpTot(R),gs=mdpDivAgg(R);
 const H=['Division','Districts','Reporting','Teams planned','Teams deployed','Teams awaited',
  'Deployment %','UCs planned','UCs reported','Security incidents'];
 const rows=gs.map(g=>[g.dv,g.n,g.rep,g.fp,g.fd,g.aw,
  g.fp?Math.round(g.fd/g.fp*1000)/10:'',g.ucp,g.ucr,g.inc]);
 rows.push(['Campaign total',T.n,T.rep,T.fp,T.fd,T.aw,T.pct==null?'':Math.round(T.pct*1000)/10,T.ucp,T.ucr,T.inc]);
 csvDownload(mdpShareFile('division_roll_up','.xlsx'),H,rows);
}
function mdpSmallXlsx(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R);
 const H=['District','Division','Days reported','Teams planned','Teams deployed','Teams awaited',
  'Deployment %','UCs planned','UCs reported','Status','Last campaign day','Last update'];
 const rows=R.map(o=>[DNAME(o.n),o.dv,o.reps||0,o.fp,o.fd,o.rep?o.awTot:'',
  o.pct==null?'':Math.round(o.pct*1000)/10,o.ucp,o.ucr,MDP_ST[o.st][1],o.rep?o.last:'',o.rep?(o.at||''):'']);
 rows.push(['Campaign total',T.n+' districts',T.rep,T.fp,T.fd,T.aw,
  T.pct==null?'':Math.round(T.pct*1000)/10,T.ucp,T.ucr,T.good+' on plan','','']);
 csvDownload(mdpShareFile('district_summary','.xlsx'),H,rows);
}
function mdpHeatXlsx(){
 const R=mdpRows().slice().sort((a,b)=>String(a.dv).localeCompare(String(b.dv))||String(a.n).localeCompare(String(b.n)));
 const H=['District','Division'].concat(MDP_TYPES.map(t=>t[1]+' %')).concat(['UCs %','Field %','Teams planned','Teams deployed','Status']);
 const rows=R.map(o=>{
  const pcs=MDP_TYPES.map((t,i)=>{const p=o.p[i]||0;return o.rep&&p?Math.round((o.d[i]||0)/p*1000)/10:'';});
  return [DNAME(o.n),o.dv].concat(pcs).concat([o.ucp?Math.round(o.ucr/o.ucp*1000)/10:'',
   o.pct==null?'':Math.round(o.pct*1000)/10,o.fp,o.fd,MDP_ST[o.st][1]]);
 });
 csvDownload(mdpShareFile('deployment_by_team_type','.xlsx'),H,rows);
}
function mdpSmall(R,T){
 drawTable('tMDPSmall',[
  {k:'n',l:'District',f:o=>'<b>'+esc(DNAME(o.n))+'</b>'},
  {k:'dv',l:'Division',f:o=>esc(o.dv)},
  {k:'reps',l:'Days',n:1,f:o=>String(o.reps||0),sv:o=>o.reps||0},
  {k:'fd',l:'Teams deployed / planned',n:1,f:o=>o.rep?(fmt(o.fd)+' / '+fmt(o.fp)):'\u2013',sv:o=>o.fp?o.fd/o.fp:null},
  {k:'pct',l:'Deployment %',n:1,f:o=>o.pct==null?'\u2013':'<b style="color:'+MDP_COL[o.st]+'">'+o.pct.toFixed(1)+'%</b>',sv:o=>o.pct},
  {k:'ucr',l:'UCs rep. / planned',n:1,f:o=>fmt(o.ucr)+' / '+fmt(o.ucp),sv:o=>o.ucp?o.ucr/o.ucp:null},
  {k:'st',l:'Status',f:o=>'<span class="st '+MDP_ST[o.st][0]+'">'+MDP_ST[o.st][1]+'</span>'}
 ],R,'pct',1,'No district is in scope for this day in the current filter');
 const c=el('mdpSmCnt');
 if(c)c.textContent=T.rep+' of '+R.length+' districts reported \u00b7 '
  +(T.pct==null?'no field teams planned yet':T.pct.toFixed(1)+'% deployed');
 const cap=el('capMDPSmall');
 if(cap)cap.innerHTML='One row per district with the numbers a morning call needs; the full board with '
  +'awaited teams, incidents and reasons is below. <b>Days</b> counts the campaign days that district '
  +'has reported'+(MDD?' (one, for a single day)':'')+'.';
}
function mdpCh(id){
 const c=(typeof CH!=='undefined')?CH[id]:null;
 return c&&c.series&&c.series.length&&c.renderTo?c:null;
}
function mdpChTitle(id){const c=mdpCh(id);return String((c&&c.title&&c.title.textStr)||'Morning deployment');}
function mdpChSub(id){const c=mdpCh(id);return String((c&&c.subtitle&&c.subtitle.textStr)||'');}
function mdpChCap(id){const e=el('cap'+id);return e?(e.textContent||''):'';}
function mdpChVal(s,i){
 const p=s.points&&s.points[i];
 let v=p?p.y:(s.yData?s.yData[i]:(s.data?s.data[i]:null));
 if(v&&typeof v==='object')v=v.y;
 return (typeof v==='number'&&isFinite(v))?Math.round(v*100)/100:'';
}
async function mdpChReady(c){
 if(c.chartWidth>120)return;
 try{c.reflow();}catch(e){}
 await new Promise(r=>setTimeout(r,90));
}
async function mdpChImg(id,kind){
 const c=mdpCh(id);if(!c)return null;
 await mdpChReady(c);
 const svg=c.renderTo.querySelector('svg');if(!svg)return null;
 const cl=svg.cloneNode(true);
 cl.setAttribute('xmlns','http://www.w3.org/2000/svg');
 cl.setAttribute('font-family','"Segoe UI",Arial,sans-serif');
 const W=Math.max(560,Math.round(c.chartWidth||900)),CH0=Math.max(240,Math.round(c.chartHeight||400));
 const S=2,TB=76;
 const m=document.createElement('canvas').getContext('2d');
 m.font='11.5px "Segoe UI",Arial,sans-serif';
 const cap=mdpChCap(id),cL=cap?mdpWrapText(m,cap,W-28).slice(0,4):[];
 const CB=cL.length?cL.length*16+8:0;
 const H=TB+CH0+CB+10;
 const img=new Image();
 await new Promise((res,rej)=>{img.onload=res;img.onerror=()=>rej(new Error('chart svg would not raster'));
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(cl));});
 const cv=document.createElement('canvas');cv.width=W*S;cv.height=H*S;
 const x=cv.getContext('2d');x.scale(S,S);
 x.fillStyle='#ffffff';x.fillRect(0,0,W,H);
 x.fillStyle='#0f172a';x.font='bold 19px "Segoe UI",Arial,sans-serif';
 x.fillText(mdpChTitle(id),14,26);
 x.fillStyle='#475569';x.font='12.5px "Segoe UI",Arial,sans-serif';
 x.fillText(mdpChSub(id)+' \u00b7 '+mdpLiveWhen(),14,47);
 x.drawImage(img,0,TB,W,CH0);
 if(cL.length){x.fillStyle='#64748b';x.font='11.5px "Segoe UI",Arial,sans-serif';
  cL.forEach((l,i)=>x.fillText(l,14,TB+CH0+22+i*16));}
 return kind==='jpeg'?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png');
}
function mdpChTable(id){
 const c=mdpCh(id);if(!c)return null;
 const cats=(c.xAxis&&c.xAxis[0]&&c.xAxis[0].categories?c.xAxis[0].categories:[]).map(v=>String(v));
 const H=[MDP_CHX[id]||'Item'].concat(c.series.map(s=>String(s.name||'Value')));
 const rows=cats.map((k,i)=>[k].concat(c.series.map(s=>mdpChVal(s,i))));
 return {H:H,rows:rows};
}
async function mdpChPptx(id){
 const c=mdpCh(id);if(!c)return;
 await loadPptx();
 const url=await mdpChImg(id,'png');
 if(!url)return;
 const P=window.PptxGenJS,pptx=new P();
 pptx.layout='LAYOUT_WIDE';pptx.title=mdpChTitle(id);
 const s=pptx.addSlide();s.background={color:'FFFFFF'};
 s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.14,fill:{color:'0D9488'},line:{color:'0D9488'}});
 s.addText(mdpChTitle(id),{x:0.5,y:0.24,w:12.3,h:0.55,fontFace:'Segoe UI',fontSize:24,bold:true,color:'0F172A'});
 s.addText(mdpChSub(id)+' \u00b7 '+mdpLiveWhen(),{x:0.5,y:0.84,w:12.3,h:0.35,fontFace:'Segoe UI',fontSize:12,color:'6B7280'});
 const W=Math.max(560,Math.round(c.chartWidth||900)),H=Math.max(240,Math.round(c.chartHeight||400))+76;
 let iw=12.43,ih=iw*H/W;
 if(ih>5.3){ih=5.3;iw=ih*W/H;}
 s.addImage({data:url,x:0.45,y:1.3,w:iw,h:ih});
 const cap=mdpChCap(id);
 s.addText(cap,{x:0.5,y:1.35+ih+0.1,w:12.3,h:Math.max(0.4,6.9-(1.35+ih+0.1)),
  fontFace:'Segoe UI',fontSize:10.5,color:'374151',valign:'top'});
 s.addShape(pptx.ShapeType.line,{x:0.5,y:7.02,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
 s.addText(mdpCampLbl()+' \u00b7 '+mdpDayLbl()+' \u00b7 EOC KP Polio Eradication Programme',
  {x:0.5,y:7.06,w:10.5,h:0.3,fontFace:'Segoe UI',fontSize:9,color:'6B7280'});
 await saveDeck(pptx,mdpShareFile(mdpChTitle(id),'.pptx'));
}
function mdpDlWire(){
 if(_MDPDLW)return;_MDPDLW=1;
 const SPEC={div:mdpDivSpec,small:mdpSmallSpec};
 document.querySelectorAll('[data-mdptbl]').forEach(b=>{
  b.onclick=()=>{
   const name=b.dataset.mdptbl,kind=b.dataset.k;
   if(kind==='xlsx'){if(name==='div')mdpDivXlsx();else mdpSmallXlsx();return;}
   b.disabled=true;
   try{const o=SPEC[name](),cv=mdpTblCanvas(o,kind==='jpg'?'jpeg':'png');
    mdpShareSave(cv.url,mdpShareFile(o.key,cv.ext));
    toast(kind==='jpg'?'JPG downloaded':'PNG downloaded');}
   catch(e){console.error('mdp table image',e);toast('Could not create the image');}
   b.disabled=false;
  };
 });
 document.querySelectorAll('[data-mdpch]').forEach(b=>{
  b.onclick=async()=>{
   const id=b.dataset.mdpch,k=b.dataset.k;
   if(!mdpCh(id)){toast('That chart is not on screen to download');return;}
   b.disabled=true;
   try{
    if(k==='xlsx'){
     const d=mdpChTable(id);
     if(!d)toast('Nothing to download yet');
     else csvDownload(mdpShareFile(mdpChTitle(id),'.xlsx'),d.H,d.rows);
    }else if(k==='pptx')await mdpChPptx(id);
    else{
     const u=await mdpChImg(id,k);
     if(!u)toast('Nothing to download yet');
     else{mdpShareSave(u,mdpShareFile(mdpChTitle(id),k==='jpg'?'.jpg':'.png'));
      toast(k==='jpg'?'JPG downloaded':'PNG downloaded');}
    }
   }catch(e){console.error('mdp chart download',e);
    toast('Could not create the '+(k==='xlsx'?'table':k.toUpperCase()));}
   b.disabled=false;
  };
 });
 const h=el('btnMDPHxls');if(h)h.onclick=()=>mdpHeatXlsx();
}
mdpDlWire();
'''


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    if 'id="tMDPSmall"' in v.text:
        print('nothing to do')
        return
    edits = [
        (CSS_OLD, CSS_NEW, 'share button styles'),
        (DIV_OLD, DIV_NEW, 'division roll-up buttons'),
        (GRID_OLD, GRID_NEW, 'chart buttons + district summary card'),
        (HEAT_OLD, HEAT_NEW, 'heatmap excel button'),
        (AGG_OLD, AGG_NEW, 'shared division aggregation'),
        (RENDER_OLD, RENDER_NEW, 'render the summary'),
    ]
    for old, new, label in edits:
        o, n = crlf(old), crlf(new)
        c = v.text.count(o)
        if c != 1:
            raise SystemExit('ABORT: %d matches for %s' % (c, label))
        v.text = v.text.replace(o, n, 1)
        v.changes.append('Morning deployment share: %s' % label)
    anchor = crlf(JS_ANCHOR)
    if v.text.count(anchor) != 1:
        raise SystemExit('ABORT: %d matches for the mdpMapWire anchor' % v.text.count(anchor))
    v.text = v.text.replace(anchor, anchor + crlf(JS_NEW), 1)
    v.changes.append('Morning deployment share: export helpers and wiring')
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars' % v.delta())


if __name__ == '__main__':
    main()
