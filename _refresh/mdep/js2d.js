// The deployment map is the dashboard's own KP district geometry (KPGEO), not a schematic grid, so a
// district sits where it does on the front page. Fill is the share of the day's field teams deployed,
// on the same four bands the rest of the tab uses. _MDPMAP holds the last drawn state so the JPG / PNG /
// PPTX exports carry the exact colours, legend and caption that are on screen.
let _MDPMAP=null,_MDPMW=0;
function mdpMap(){
 const box=el('mdpMap');if(!box)return;
 const lg=el('mdpMapLeg'),cnt=el('mdpMcnt'),cap=el('mdpMapCap');
 const b1=el('btnMDPMjpg'),b2=el('btnMDPMpng'),b3=el('btnMDPMpptx');
 if(typeof KPGEO==='undefined'||!KPGEO.d||!KPGEO.d.length){
  box.innerHTML='<div class="empty">District geometry not embedded in this file.</div>';
  if(lg)lg.innerHTML='';if(cnt)cnt.textContent='';if(cap)cap.textContent='';
  [b1,b2,b3].forEach(b=>{if(b)b.disabled=true;});
  _MDPMAP=null;return;}
 const REG={},ALL=mdpScope();ALL.forEach(o=>{REG[o.n]=1;});
 const BASE={};mdpBase().forEach(o=>{BASE[o.n]=1;});
 const IN={},R=mdpRows();R.forEach(o=>{IN[o.n]=o;});
 const filterOn=!!(mdpVal('mdpDiv')||mdpVal('mdpDist'));
 const day=MDD?('day '+MDD):'the days reported so far',dl=MDD?('day '+MDD):'this campaign',
  nReg=Object.keys(REG).length;
 const tip=function(n){
  const o=IN[n];
  if(!REG[n])return DNAME(n)+'\n'+mdpDv(n)+' division\nnot in the '+mdpCampLbl()+' register';
  if(!BASE[n])return DNAME(n)+'\n'+mdpDv(n)+' division\noutside the selected division / district';
  if(!o||!o.rep)return DNAME(n)+'\n'+mdpDv(n)+' division\nno report for '+dl
   +(o&&o.uc?'\n'+fmt(o.uc)+' UCs planned':'');
  return DNAME(n)+'\n'+mdpDv(n)+' division\n'
   +(o.pct==null?'no field teams planned':o.pct.toFixed(1)+'% deployed \u00b7 '+MDP_ST[o.st][1])
   +'\n'+fmt(o.fd)+' of '+fmt(o.fp)+' field teams'
   +'\nUCs '+fmt(o.ucr)+' of '+fmt(o.ucp)+' reported'
   +'\n'+o.reps+' day'+(o.reps===1?'':'s')+' reported this campaign'
   +(o.at?'\nlast update '+o.at:'');
 };
 const fill=function(n){
  if(!REG[n])return '#f8fafc';
  if(!BASE[n])return '#eef2f7';
  const o=IN[n];
  return o&&o.rep&&o.pct!=null?MDP_COL[o.st]:MDP_COL.no;
 };
 const LAB=hrvLab();
 let svg='<svg viewBox="0 0 '+KPGEO.vb[0]+' '+KPGEO.vb[1]+'" role="img" aria-label="Khyber Pakhtunkhwa district map coloured by morning field-team deployment" style="width:100%;display:block;aspect-ratio:'+KPGEO.vb[0]+'/'+KPGEO.vb[1]+'">';
 svg+=KPGEO.d.map(function(p){
  return '<path d="'+p.p+'" fill="'+fill(p.c)+'" stroke="#fff" stroke-width="1.1">'
   +'<title>'+esc(tip(p.c))+'</title></path>';}).join('');
 const FU=KPGEO.vb[0]/540;
 svg+=LAB.filter(function(l){return l.ld;}).map(function(l){
  return '<g pointer-events="none"><line x1="'+l.cx.toFixed(1)+'" y1="'+l.cy.toFixed(1)+'" x2="'
   +l.x.toFixed(1)+'" y2="'+l.y.toFixed(1)+'" stroke="#334155" stroke-width="'+(0.8*FU).toFixed(2)
   +'" stroke-opacity=".6"/><circle cx="'+l.cx.toFixed(1)+'" cy="'+l.cy.toFixed(1)+'" r="'
   +(1.5*FU).toFixed(1)+'" fill="#334155"/></g>';}).join('');
 svg+=LAB.map(function(l){
  return '<text x="'+l.x.toFixed(1)+'" y="'+(l.y+l.fs*0.34).toFixed(1)+'" text-anchor="middle" font-size="'
   +l.fs.toFixed(1)+'" font-weight="600" fill="#0f172a" stroke="#fff" stroke-width="'+(l.fs*0.3).toFixed(1)
   +'" stroke-linejoin="round" paint-order="stroke" pointer-events="none">'+esc(l.n)+'</text>';}).join('');
 svg+='</svg>';
 box.innerHTML=svg;
 const LEG=[['good','On plan \u00b7 95% and above'],['watch','Watch \u00b7 85-95%'],
  ['low','Short \u00b7 70-85%'],['crit','Critical \u00b7 below 70%'],['no','No report for '+dl]];
 if(filterOn)LEG.push(['#eef2f7','Outside the selected division / district']);
 LEG.push(['#f8fafc','Not in the '+mdpCampLbl()+' register']);
 if(lg)lg.innerHTML=LEG.map(function(b){
  return '<span><i style="background:'+b[0]+';border:1px solid #dbe3ee"></i>'+b[1]+'</span>';}).join('');
 const rep=R.filter(function(o){return o.rep&&o.pct!=null;});
 if(cnt)cnt.textContent=rep.length+' of '+nReg+' districts reporting';
 const worst=rep.slice().sort(function(a,b){return a.pct-b.pct;});
 const best=worst.slice().reverse();
 const on=rep.filter(function(o){return o.st==='good';}).length;
 const noR=ALL.filter(function(o){return BASE[o.n]&&!(IN[o.n]&&IN[o.n].rep);}).length;
 let capTxt='Colour is the share of the day\u2019s field teams actually deployed: mobile, fixed, transit '
  +'and roaming teams, against the plan for '+day+'. '+rep.length+' of the '+nReg+' districts in the '
  +mdpCampLbl()+' register have a report; '+on+' '+(on===1?'is':'are')+' on plan at 95% and above'
  +(worst.length?' and the lowest '+(worst.length>1?worst.slice(0,3).map(function(o){return DNAME(o.n)+' '+o.pct.toFixed(0)+'%';}).join(', '):DNAME(worst[0].n)+' '+worst[0].pct.toFixed(0)+'%'):'')
  +'. '+(noR?'No report yet for '+noR+' district'+(noR===1?'':'s')+'. ':'')
  +'Hover a district for its team counts. Boundaries: '+KPGEO.src+' + '+KPGEO.ucsrc+' (UC layer '+KPGEO.uc_asof+').';
 if(cap)cap.textContent=capTxt;
 const T='KP district map \u00b7 morning field-team deployment';
 const S=mdpCampLbl()+' \u00b7 '+mdpDayLbl()+' \u00b7 '+rep.length+' of '+nReg+' districts reporting';
 _MDPMAP={T:T,S:S,rows:worst,C:capTxt,L:LEG};
 [b1,b2,b3].forEach(function(b){if(b)b.disabled=false;});
}
function mdpMapShot(){
 const svg=el('mdpMap')&&el('mdpMap').querySelector('svg');
 if(!svg)return Promise.resolve(null);
 const vb=(svg.getAttribute('viewBox')||'').split(/[\s,]+/).map(Number),c=svg.cloneNode(true);
 c.removeAttribute('style');c.setAttribute('xmlns','http://www.w3.org/2000/svg');
 c.setAttribute('width',String(vb[2]));c.setAttribute('height',String(vb[3]));
 c.setAttribute('font-family','"Segoe UI",Arial,sans-serif');
 const img=new Image();
 return new Promise(function(res,rej){
  img.onload=function(){res({img:img,w:vb[2],h:vb[3]});};
  img.onerror=function(){rej(new Error('map svg would not raster'));};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(c));});
}
function mdpMapWrap(t,w){
 const m=document.createElement('canvas').getContext('2d');
 m.font='12px "Segoe UI",Arial,sans-serif';const out=[];let cur='';
 String(t).split(/\s+/).forEach(function(v){const s=cur?cur+' '+v:v;
  if(m.measureText(s).width>w&&cur){out.push(cur);cur=v;}else cur=s;});
 if(cur)out.push(cur);return out;
}
async function mdpMapImgURL(kind,plain){
 const A=_MDPMAP;if(!A)return null;
 const sh=await mdpMapShot();if(!sh)return null;
 const S=2,W=660,TB=plain?0:56,LH=26,all=mdpMapWrap(A.C,W-32),ln=all.slice(0,4);
 if(all.length>4)ln[3]=ln[3].replace(/\s*\S*$/,'')+'\u2026';
 const CH=ln.length?ln.length*15+12:0, mh=Math.round((W-24)*sh.h/sh.w), H=TB+mh+LH+CH, ly=TB+mh+16;
 const cv=document.createElement('canvas'); cv.width=W*S; cv.height=H*S;
 const x=cv.getContext('2d'); x.scale(S,S); x.fillStyle='#ffffff'; x.fillRect(0,0,W,H);
 if(!plain){x.fillStyle='#0f172a';x.font='bold 21px "Segoe UI",Arial,sans-serif';x.fillText(A.T,16,28);
  x.fillStyle='#475569';x.font='13px "Segoe UI",Arial,sans-serif';x.fillText(A.S,16,47);}
 x.drawImage(sh.img,(W-mh*sh.w/sh.h)/2,TB+2,mh*sh.w/sh.h,mh);
 let lx=16; x.font='12.5px "Segoe UI",Arial,sans-serif';
 A.L.forEach(function(b){x.fillStyle=b[0];x.fillRect(lx,ly-9,11,11);
  x.fillStyle='#374151';x.fillText(b[1],lx+15,ly);lx+=15+x.measureText(b[1]).width+16;});
 if(ln.length){x.fillStyle='#64748b';x.font='12px "Segoe UI",Arial,sans-serif';
  ln.forEach(function(t,i){x.fillText(t,16,ly+24+i*15);});}
 return {url:kind==='jpeg'?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png'),w:W,h:H};
}
function mdpMapFile(ext){
 return 'MDP_district_map_'+mdpCampLbl().replace(/[^A-Za-z0-9]+/g,'_')+'_'
  +(MDD?'day'+MDD:'all_days')+'_'+new Date().toISOString().slice(0,10)+ext;
}
function mdpMapDl(url,name){
 const a=document.createElement('a');a.href=url;a.download=name;a.rel='noopener';
 document.body.appendChild(a);a.click();a.remove();
}
function mdpMapWire(){
 if(_MDPMW)return;_MDPMW=1;
 [['btnMDPMjpg','jpeg','.jpg','JPG'],['btnMDPMpng','png','.png','PNG']].forEach(function(p){
  const b=el(p[0]);if(!b)return;
  b.onclick=async function(){
   if(!_MDPMAP){toast('The map is not on screen to download');return;}
   b.disabled=true;
   try{const o=await mdpMapImgURL(p[1]);
    if(!o)toast('The map is not on screen to download');
    else{mdpMapDl(o.url,mdpMapFile(p[2]));toast(p[3]+' downloaded');}}
   catch(e){console.error(e);toast('Could not create the '+p[3]);}
   b.disabled=!_MDPMAP;};});
 const b=el('btnMDPMpptx');if(!b)return;
 b.onclick=async function(){
  const A=_MDPMAP;if(!A){toast('The map is not on screen to download');return;}
  b.disabled=true;
  try{
   await loadPptx();
   const o=await mdpMapImgURL('png',true);
   if(!o){toast('The map is not on screen to download');b.disabled=!_MDPMAP;return;}
   const P=window.PptxGenJS,pptx=new P(),F='Segoe UI';
   const lst=A.rows.slice(0,12);
   pptx.layout='LAYOUT_WIDE';pptx.title=A.T;pptx.subject=A.S;
   const s=pptx.addSlide();s.background={color:'FFFFFF'};
   s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.14,fill:{color:'0F766E'},line:{color:'0F766E'}});
   s.addText(A.T,{x:0.5,y:0.24,w:12.3,h:0.55,fontFace:F,fontSize:24,bold:true,color:'0F766E'});
   s.addText(A.S,{x:0.5,y:0.84,w:12.3,h:0.35,fontFace:F,fontSize:12,color:'6B7280'});
   let ih=5.5,iw=ih*o.w/o.h; if(iw>5.1){iw=5.1;ih=iw*o.h/o.w;}
   s.addImage({data:o.url,x:0.45,y:1.28,w:iw,h:ih});
   const rx=0.45+iw+0.34, rw=12.43-iw-0.34,
    hc=function(t,j){return {text:t,options:{bold:true,color:'FFFFFF',fill:{color:'0F766E'},fontSize:10,align:j?'right':'left',valign:'middle'}};},
    rows=[[hc('Lowest districts',0),hc('Deployment',1)]].concat(lst.map(function(g){
     const st=g.st,co=MDP_COL[st];
     return [{text:DNAME(g.n),options:{fontSize:10,valign:'middle'}},
      {text:(g.pct==null?'-':g.pct.toFixed(1)+'%')+' \u00b7 '+MDP_ST[st][1],
       options:{fontSize:10,bold:true,align:'right',valign:'middle',color:co.slice(1).toUpperCase()}}];}));
   s.addTable(rows,{x:rx,y:1.28,w:rw,colW:[rw*0.55,rw*0.45],fontFace:F,
    rowH:[0.32].concat(rows.slice(1).map(function(){return 0.26;})),
    border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false,margin:0.04});
   const ty=1.42+0.32+lst.length*0.26;
   s.addText(A.C,{x:rx,y:ty,w:rw,h:Math.max(0.5,6.9-ty),fontFace:F,fontSize:9.5,color:'374151',valign:'top'});
   s.addShape(pptx.ShapeType.line,{x:0.5,y:7.0,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
   s.addText('KP Polio and Synergy dashboard \u00b7 '+new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}),
    {x:0.5,y:7.05,w:12.3,h:0.3,fontFace:F,fontSize:9,color:'6B7280'});
   await saveDeck(pptx,mdpMapFile('.pptx'));toast('Slide downloaded');
  }catch(e){console.error(e);toast('Could not create the slide (needs internet for the PPTX library)');}
  b.disabled=!_MDPMAP;};
}
mdpMapWire();
