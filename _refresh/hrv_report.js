// HRA AT A GLANCE (6/6): findings and recommendations from the sheet compiled above.
// The owner asked, 27-Oct-2026: "it would be good if we can generate a small report based on
// compiled hra for findings and recommendations." Every figure is read from hrtRows and the card's
// own evaluation V - nothing comes from the dashboard payload, and no cause is invented for a score.
// The report follows the division/district filter above and prints that scope in its first line.
//
// Two traps the card itself sets, both handled by leaving rows out and saying so:
//   * a row with no answers still gets a percentage from the formulas' own defaults;
//   * a row answered only in the two blocks the card charges per answered cell can score ABOVE 100%,
//     because blank cells in those blocks still earn their default points while adding nothing to the
//     maximum. Neither is a reading of the UC, so both are counted separately, never averaged in.
const HRVRB=['','Terrain & security','Epidemiology & surveillance','SIA operations','EPI / PEI synergy'];
function hrvRepData(V){
 const idx=hrtView(),rows=idx.map(function(i){return hrtRows[i];}),
  vv=idx.map(function(i){return V[i];}),n=idx.length;
 const dv=el('hrtDiv')&&el('hrtDiv').value,dd=el('hrtDist')&&el('hrtDist').value,P=HRT_P();
 const out={n:n,dv:dv,dd:dd,slug:hrtSlug(),per:(P[2]||'Campaign')+' '+P[0]+'-'+P[1],
  band:[0,0,0],comp:[],over:0,other:0,districts:{},blocks:{},inds:[],textCols:{},offCols:{},
  dupe:0,nocode:0,blanks:0,full:0,marked:0,none:0,mean:null,_seen:{}};
 // indicator first: block achievement is taken from the answers themselves, not from the card's
 // block sums, which include the default points a blank earns.
 HRAT.i.forEach(function(ind){
  const cell=(ind.raw||[])[0],col=cell?(HRT_L[cell]||{L:cell}):null;
  let got=0,k=0,blank=0;
  rows.forEach(function(r,i){
   const sc=vv[i].v[ind.sc];
   if(col&&r0(r,col)){k++;if(typeof sc==='number'&&isFinite(sc))got+=sc;}else blank++;
  });
  out.inds.push({name:ind.name,blk:ind.blk,k:k,blank:blank,got:got,ach:k?got/(3*k)*100:null});
 });
 const bk={};
 out.inds.forEach(function(o){const B=bk[o.blk]=bk[o.blk]||{got:0,k:0};B.got+=o.got;B.k+=o.k;});
 [1,2,3,4].forEach(function(b){const B=bk[b];
  if(B&&B.k)out.blocks[b]={name:HRVRB[b],got:B.got,k:B.k,ach:B.got/(3*B.k)*100};});
 rows.forEach(function(r,i){
  const o=vv[i],ob=o.v;
  const any=HRTRAW.some(function(c){return r0(r,c);}),all=HRTRAW.every(function(c){return r0(r,c);});
  if(all)out.full++;
  out.blanks+=(o.blanks||0);
  const code=r.D?String(r.D).trim():'';
  if(!code)out.nocode++;else{if(out._seen[code])out.dupe++;else out._seen[code]=1;}
  HRTIN.forEach(function(c){
   const val=r[c.L];if(val==null)return;
   if((c.k==='pct'||c.k==='rate'||c.k==='cnt')&&typeof val==='string')
    out.textCols[c.h]=(out.textCols[c.h]||0)+1;
   const opts=(c.o||[]).filter(Boolean);
   if(opts.length&&!opts.some(function(x){return HRTN(x)===HRTN(String(val));}))
    out.offCols[c.h]=(out.offCols[c.h]||0)+1;
  });
  if(!any){out.none++;return;}
  out.marked++;
  const p=(typeof ob[HRTL.ovr]==='number'&&isFinite(ob[HRTL.ovr]))?ob[HRTL.ovr]:null;
  if(p==null){out.other++;return;}
  if(p>1){out.over++;return;}
  const b=hrtBand(p);
  out.band[b]++;out.comp.push({r:r,p:p,b:b});
  const d=String(r.B||'').trim()||'(no district)';
  const D=out.districts[d]=out.districts[d]||{n:0,sum:0,hi:0,lo:0};
  D.n++;D.sum+=p;if(b===2)D.hi++;if(b===0)D.lo++;
 });
 if(out.comp.length)out.mean=out.comp.reduce(function(s,x){return s+x.p;},0)/out.comp.length*100;
 return out;}

let _HRVRT='';
function hrvRepSave(){
 if(!_HRVRT){toast('There is nothing to download yet');return;}
 const b=new Blob([_HRVRT],{type:'text/plain;charset=utf-8'}),u=URL.createObjectURL(b),
  a=document.createElement('a');
 a.href=u;a.download='HRA_findings_'+hrtSlug()+'.txt';
 document.body.appendChild(a);a.click();a.remove();
 setTimeout(function(){URL.revokeObjectURL(u);},1500);
 toast('Report downloaded');}
function hrvRep(V){
 const box=el('hrvRep');if(!box)return;
 const D=hrvRepData(V||hrtVals()),B=D.band,tot=D.comp.length;
 const scope=(D.dv||D.dd?[(D.dv||'All divisions'),(D.dd||'All districts')].join(' / ')
  :'All divisions and districts')+' \u00b7 '+D.per
  +(D.n?' \u00b7 '+fmt(D.n)+' of '+fmt(hrtRows.length)+' councils':'');
 const sub=el('hrvRepSub');if(sub)sub.textContent=scope;
 const btn=el('btnHRVrep');
 if(btn){btn.disabled=!D.n;if(!btn.onclick)btn.onclick=hrvRepSave;}
 if(!D.n){box.innerHTML='<div class="hint" style="margin:0">This period is empty in this browser, so '
  +'there is nothing to read yet. Import a card or seed the sheet above.</div>';_HRVRT='';return;}
 const bl=[1,2,3,4].map(function(b){return D.blocks[b];}).filter(Boolean)
  .sort(function(a,b){return a.ach-b.ach;});
 const dl=Object.keys(D.districts).map(function(k){const o=D.districts[k];
  return {d:k,n:o.n,hi:o.hi,lo:o.lo,p:o.n?o.sum/o.n*100:null};});
 const hiD=dl.filter(function(o){return o.hi>0;}).sort(function(a,b){return b.hi-a.hi||a.p-b.p;});
 const loD=dl.filter(function(o){return o.p!=null;}).sort(function(a,b){return a.p-b.p;});
 const low=D.comp.slice().sort(function(a,b){return a.p-b.p;}).slice(0,5);
 const lowTxt=low.map(function(x){return String(x.r.C||'UC')+' ('+String(x.r.B||'?')+') '+pc(x.p*100);})
  .join('; ');
 const ind=D.inds.filter(function(o){return o.k&&o.ach!=null;})
  .sort(function(a,b){return a.ach-b.ach;});
 const dq=[],tc=Object.keys(D.textCols),oc=Object.keys(D.offCols);
 const tcn=tc.reduce(function(s,k){return s+D.textCols[k];},0),
  ocn=oc.reduce(function(s,k){return s+D.offCols[k];},0);
 if(tcn)dq.push(fmt(tcn)+' cell(s) in a number or percent column hold text');
 if(ocn)dq.push(fmt(ocn)+' cell(s) hold a value their dropdown does not list');
 if(D.dupe)dq.push(fmt(D.dupe)+' row(s) repeat a UC code');
 if(D.nocode)dq.push(fmt(D.nocode)+' row(s) carry no UC code');
 const wBlk=bl.length?bl[0]:null,sBlk=bl.length?bl[bl.length-1]:null;
 const ex=D.over+D.other;
 const F=[];
 F.push({h:'Coverage and completeness.',t:fmt(D.n)+' councils in scope: '+fmt(D.full)
  +' answer all '+HRAT.nsc+' indicators, '+fmt(D.marked)+' answer at least one'
  +(D.none?', and '+fmt(D.none)+' answer none at all':'')
  +'. '+fmt(D.blanks)+' indicator cells are still blank.'});
 if(tot)F.push({h:'Risk mix.',t:B[0]+' Low, '+B[1]+' Medium and '+B[2]+' High Risk ('
  +pc(B[2]/tot*100)+' High) among the '+fmt(tot)+' councils the card can compare'
  +(ex?' (the KPI row above counts every marked row, including the '+fmt(ex)
   +' left out below)':'')+'. Mean overall score '+pc(D.mean)+'. The card\u2019s axis runs the other way: '+HRAT.band.hi
  +'% or more is Low Risk, under '+HRAT.band.lo+'% is High.'});
 else F.push({h:'Risk mix.',t:'No council on this sheet can be compared on the card\u2019s axis yet '
  +'- see the next point.'});
 if(ex)F.push({h:'Rows the card cannot compare.',t:fmt(D.over)+' marked row(s) score above 100% of '
  +'the marks the card charges them'+(D.other?', and '+fmt(D.other)+' more carry no numeric score':'')
  +'. The card charges the SIA and EPI-indicator blocks only for the cells that are answered, while a '
  +'blank cell in those blocks can still earn its formula\u2019s default points, so a sparsely '
  +'answered row adds points without adding to the maximum. Those rows are left out of the risk '
  +'mix and the district scores; the indicator and block figures do count the cells they answered. '
  +'Complete them and re-import or edit them in place.'});
 if(wBlk)F.push({h:'Where the marks go.',t:'Answered indicators earn from '+pc(wBlk.ach)+' ('
  +wBlk.name+') to '+pc(sBlk.ach)+' ('+sBlk.name+'), counted over the councils that answered each '
  +'indicator.'});
 if(dl.length)F.push({h:'Districts.',t:(hiD.length?fmt(hiD.length)+' of '+fmt(dl.length)
  +' districts in scope hold a High-Risk council; the heaviest are '
  +hiD.slice(0,3).map(function(o){return o.d+' ('+o.hi+')';}).join(', ')+'.'
  :'No comparable council in scope falls under '+HRAT.band.lo
   +'%, so no district carries a High-Risk council.')
  +(loD.length?' Lowest mean council scores: '
   +loD.slice(0,3).map(function(o){return o.d+' '+pc(o.p);}).join(', ')+'.':'')});
 if(low.length)F.push({h:'Lowest councils.',t:lowTxt+'.'});
 if(ind.length)F.push({h:'Indicators taking the most off.',t:ind.slice(0,3).map(function(o){
  return o.name+' '+pc(o.ach)+' (answered by '+fmt(o.k)+' of '+fmt(D.n)+')';}).join('; ')+'.'});
 if(dq.length)F.push({h:'Cells to correct.',t:dq.join('; ')+'. The sheet keeps them as they came '
  +'in; the download writes them back unchanged.'});
 const R=[];
 if(B[2])R.push('Clear the '+fmt(B[2])+' High-Risk council(s) first'
  +(hiD.length?', starting with '+hiD.slice(0,3).map(function(o){return o.d+' ('+o.hi+')';}).join(', '):'')
  +'. Read their weakest block'+(wBlk?' - '+wBlk.name+' at '+pc(wBlk.ach):'')+' - with the district '
  +'team and record the correction on the next compilation.');
 else R.push('No comparable council is in the High band: keep the current controls and re-check the '
  +'five lowest councils before the next round, since they sit closest to the '+HRAT.band.lo+'% line.');
 if(ex)R.push('Complete the '+fmt(ex)+' row(s) the card cannot compare - answers in the SIA and '
  +'EPI-indicator blocks are what is missing - before the band on this sheet is read to anyone. The '
  +'card grades those rows on default points, not on what the UC answered.');
 if(D.full<D.n||D.blanks)R.push('Close the sheet before sign-off: '+fmt(D.n-D.full)+' council(s) are '
  +'missing at least one indicator and '+fmt(D.blanks)+' cell(s) are blank. In the always-charged '
  +'blocks a blank earns nothing while still counting in the maximum; in the other two it drops out '
  +'of the maximum and can earn default points, which is the trap above.');
 if(ind.length)R.push('Take the two weakest indicators back to their source registers: '+ind[0].name
  +(ind[1]?' and '+ind[1].name:'')+'. They are the largest single deductions on this sheet.');
 if(dq.length)R.push('Correct the flagged cells and rows above, then re-import or edit them in '
  +'place; the score will move once they are right.');
 box.innerHTML='<ul class="hrul">'+F.map(function(x){
   return '<li><b>'+esc(x.h)+'</b> '+esc(x.t)+'</li>';}).join('')+'</ul>'
  +'<h4 style="margin:14px 0 6px;font-size:13.5px">Recommendations</h4><ul class="hrul">'
  +R.map(function(x){return '<li>'+esc(x)+'</li>';}).join('')+'</ul>';
 const head='HRA UC-LEVEL FINDINGS - '+D.per+'\nScope: '+scope+'\nGenerated '
  +new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})
  +' from the sheet held in this browser.\n';
 _HRVRT=head+'\nFINDINGS\n'+F.map(function(x,i){return (i+1)+'. '+x.h+' '+x.t;}).join('\n')
  +'\n\nRECOMMENDATIONS\n'+R.map(function(x,i){return (i+1)+'. '+x;}).join('\n')
  +'\n\nNote: this report reads only the cells on this sheet. It does not verify them against the UC '
  +'register, and it is not the combined UC risk score used on the Cross-cutting pages.\n';}
