// HRA AT A GLANCE (4/5): the district map, shaded by High-Risk share or by marks earned.
function hrvMap(X){
 const box=el('hrvMap');if(!box)return;
 if(typeof KPGEO==='undefined'||!KPGEO.d||!KPGEO.d.length){
  box.innerHTML='<div class="empty">District geometry not embedded in this file.</div>';
  el('hrvMNote').textContent='';el('chrvMap').textContent='';return;}
 const SM=el('hrvMK'),mk=SM&&SM.value==='mean'?'mean':'hi';
 const by={};X.ann.forEach(function(o){by[o.c]=o;});
 const sw=by['SWAT']||null;
 const src=function(c){return by[c]||(c==='BAR SWAT'?sw:null);};
 const val=function(c){const o=src(c);return (!o||!o.n)?null:(mk==='mean'?o.p:o.hi);};
 const cls=function(v){if(v==null)return '#f1f5f9';
  if(mk==='mean')return v>=85?'#dcfce7':v>=75?'#fde68a':v>=70?'#fb923c':'#b91c1c';
  return v<=0?'#dcfce7':v<=5?'#fde68a':v<=15?'#fb923c':'#b91c1c';};
 const tip=function(c){
  const o=by[c],o2=src(c);
  if(!o2||!o2.n)return DNAME(c)+'\nno HRA sheet';
  return DNAME(c)+'\n'+o2.dv+' division\n'+fmt(o2.n)+' councils: '+fmt(o2.b[0])+' Low / '
   +fmt(o2.b[1])+' Medium / '+fmt(o2.b[2])+' High'
   +'\nHigh-Risk share '+(o2.hi==null?'-':o2.hi.toFixed(1)+'%')
   +'\nMarks earned '+(o2.p==null?'-':o2.p.toFixed(1)+'%')
   +(o?'':'\nDrawn with the Swat reading: Bar Swat has no HRA sheet of its own');};
 const FU=KPGEO.vb[0]/540,LAB=hrvLab();
 let svg='<svg viewBox="0 0 '+KPGEO.vb[0]+' '+KPGEO.vb[1]+'" style="width:100%;display:block;'
  +'aspect-ratio:'+KPGEO.vb[0]+'/'+KPGEO.vb[1]+'" role="img" aria-label="HRA risk by district, Khyber Pakhtunkhwa">';
 svg+=KPGEO.d.map(function(p){
  const v=val(p.c);
  return '<path d="'+p.p+'" fill="'+(v==null?'#f1f5f9':cls(v))+'" stroke="#fff" stroke-width="1.1">'
   +'<title>'+esc(tip(p.c))+'</title></path>';}).join('');
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
 const lg=mk==='mean'
  ?[['#dcfce7','85% and above'],['#fde68a','75-85%'],['#fb923c','70-75%'],['#b91c1c','below 70%']]
  :[['#dcfce7','no High-Risk council'],['#fde68a','up to 5%'],['#fb923c','5-15%'],['#b91c1c','over 15%']];
 const list=X.ann.filter(function(o){return o.n&&(mk==='mean'?o.p!=null:o.hi!=null);})
  .sort(function(a,b){return mk==='mean'?(a.p-b.p):(b.hi-a.hi);}).slice(0,6);
 const word=mk==='mean'?'Lowest scores':'Highest High-Risk shares';
 const line=list.map(function(o){
  return DNAME(o.c)+' '+(mk==='mean'?o.p.toFixed(1):o.hi.toFixed(1))+'%';}).join(', ');
 el('hrvMNote').innerHTML='<span style="display:inline-flex;gap:12px;flex-wrap:wrap;margin-right:8px">'
  +lg.map(function(b){return '<span style="display:inline-flex;align-items:center;gap:4px">'
   +'<i style="width:10px;height:10px;border-radius:2px;background:'+b[0]+'"></i>'+b[1]+'</span>';}).join('')
  +'<span style="display:inline-flex;align-items:center;gap:4px"><i style="width:10px;height:10px;'
  +'border-radius:2px;background:#f1f5f9"></i>no sheet</span></span>'
  +'<div style="margin-top:4px"><b>'+word+':</b> '+line+'.</div>';
 const green=X.ann.filter(function(o){return o.n&&o.hi===0;}).length;
 const ex=X.ann.filter(function(o){return o.n&&o.hi===0&&o.p<76;})
  .sort(function(a,b){return a.p-b.p;})[0];
 el('chrvMap').innerHTML='Shading follows the measure picked above; the shares count councils, not '
  +'children. '+green+' of the '+X.nd+' districts have no High-Risk council, but that is not the same as '
  +'a clean district'+(ex?' &mdash; '+DNAME(ex.c)+' has none and still earns only '+ex.p.toFixed(1)
   +'% of its marks':'')+', which is why the measure can be switched. Bar Swat is drawn with the Swat '
  +'reading because it has no HRA sheet of its own; boundaries are the dashboard&rsquo;s KP district '
  +'shapefile and every label sits inside its own district.';}
