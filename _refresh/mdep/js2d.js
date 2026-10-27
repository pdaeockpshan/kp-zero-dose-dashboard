function mdpMap(R){
 const box=el('mdpMap');if(!box)return;
 const IN={};R.forEach(o=>{IN[o.n]=o;});
 const REG={};mdpScope().forEach(o=>{REG[o.n]=1;});
 const CW=34,CH=21,G=2,W=7,H=10;let b='';
 Object.keys(SNPOS).forEach(n=>{
  const c=SNPOS[n][0],r=SNPOS[n][1],ab=SNPOS[n][2],o=IN[n];
  const x=c*(CW+G)+G,y=r*(CH+G)+G;
  const inReg=!!REG[n];
  const f=o?(o.rep?MDP_COL[o.st]:MDP_COL.no):(inReg?'#e2e8f0':'#eef2f7');
  const tip=o?esc(DNAME(n))+(o.rep?(' — '+(o.pct==null?'no field teams planned':o.pct.toFixed(1)+'% deployed')+' · '+fmt(o.fd)+' of '+fmt(o.fp)+' teams · '+o.reps+' day(s) reported'):' — in the register, no report'):esc(n)+(inReg?' — in the register, no report':' — not in this campaign');
  b+='<g><title>'+tip+'</title><rect x="'+x+'" y="'+y+'" width="'+CW+'" height="'+CH+'" rx="3" fill="'+f+'" stroke="rgba(255,255,255,.9)"/><text x="'+(x+CW/2)+'" y="'+(y+CH/2+2.5)+'" text-anchor="middle" font-size="7" fill="'+(o?'#fff':'#94a3b8')+'">'+esc(ab)+'</text></g>';
 });
 box.innerHTML='<svg viewBox="0 0 '+(W*(CW+G)+G)+' '+(H*(CH+G)+G)+'" role="img" aria-label="Schematic map of Khyber Pakhtunkhwa coloured by morning team deployment" style="font-family:var(--font-mono)">'+b+'</svg>';
 el('mdpMapLeg').innerHTML=['good','watch','low','crit','no'].map(k=>'<span><i style="background:'+MDP_COL[k]+'"></i>'+MDP_ST[k][1]+'</span>').join('')+'<span><i style="background:#eef2f7;border:1px solid #cbd5e1"></i>Not in this campaign</span>';
 el('mdpMcnt').textContent=R.filter(o=>o.rep).length+' of '+R.length+' districts reporting';
}
