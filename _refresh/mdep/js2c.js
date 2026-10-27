function mdpHeat(R){
 const box=el('mdpHeat');if(!box)return;
 const cols=MDP_TYPES.map(t=>t[1]);
 let h='<table class="mdpheat"><thead><tr><th class="rh">District</th>'+cols.map(c=>'<th>'+esc(c)+'</th>').join('')+'<th>UCs</th><th>Field</th></tr></thead><tbody>';
 R.slice().sort((a,b)=>String(a.dv).localeCompare(String(b.dv))||String(a.n).localeCompare(String(b.n))).forEach(o=>{
  h+='<tr><td class="rh">'+esc(DNAME(o.n))+'</td>';
  for(let i=0;i<9;i++){
   const p=o.p[i]||0,d=o.d[i]||0;
   if(!o.rep||!p){h+='<td class="na" title="'+esc(cols[i])+': no plan or no report">·</td>';continue;}
   const pc=d/p*100;
   h+='<td style="background:'+MDP_COL[mdpStat(pc)]+'" title="'+esc(cols[i])+' · '+fmt(d)+' of '+fmt(p)+' ('+pc.toFixed(1)+'%)">'+Math.round(pc)+'</td>';
  }
  const up=o.ucp?o.ucr/o.ucp*100:null;
  h+='<td '+(up==null?'class="na"':'style="background:'+MDP_COL[mdpStat(up)]+'"')+' title="UCs reported: '+fmt(o.ucr)+' of '+fmt(o.ucp)+'">'+(up==null?'·':Math.round(up))+'</td>';
  h+='<td '+(o.pct==null?'class="na"':'style="background:'+MDP_COL[o.st]+'"')+' title="Field teams: '+fmt(o.fd)+' of '+fmt(o.fp)+'">'+(o.pct==null?'·':Math.round(o.pct))+'</td></tr>';
 });
 h+='</tbody></table>';
 box.innerHTML=h;
 el('mdpHcnt').textContent=R.length+' districts · '+cols.length+' team types';
 el('capmdpH').innerHTML='Deployed ÷ planned for each team type in '+esc(mdpDayLbl().toLowerCase())+'; <b>Field</b> is the four field-team types behind the headline %. Grey means no plan or no report.';
}
function mdpTable(R){
 drawTable('tMDP',[
  {k:'n',l:'District',f:o=>'<b>'+esc(DNAME(o.n))+'</b>'},
  {k:'dv',l:'Division',f:o=>esc(o.dv)},
  {k:'last',l:'Last report',n:1,f:o=>o.rep?('D'+o.last+(o.at?' · '+o.at+(mdpLate(o)?' ⚠':''):'')):'–',sv:o=>o.rep?o.last*10000+(mdpMin(o.at)||0):null},
  {k:'ucr',l:'UCs rep / planned',n:1,f:o=>fmt(o.ucr)+' / '+fmt(o.ucp),sv:o=>o.ucp?o.ucr/o.ucp:null},
  {k:'fd',l:'Teams deployed / planned',n:1,f:o=>o.rep?fmt(o.fd)+' / '+fmt(o.fp):'–',sv:o=>o.fp?o.fd/o.fp:null},
  {k:'pct',l:'Deployment %',n:1,f:o=>o.pct==null?'–':'<b style="color:'+MDP_COL[o.st]+'">'+o.pct.toFixed(1)+'%</b>',sv:o=>o.pct},
  {k:'aw',l:'Awaited',n:1,f:o=>o.rep?fmt(o.awTot):'–',sv:o=>o.rep?o.awTot:null},
  {k:'inc',l:'Incidents',n:1,f:o=>o.rep?fmt(o.inc):'–'},
  {k:'rsn',l:'Reason',f:o=>o.rsn?esc(MDP_RSN[o.rsn]||o.rsn):''},
  {k:'st',l:'Status',f:o=>'<span class="st '+MDP_ST[o.st][0]+'">'+MDP_ST[o.st][1]+'</span>'}
 ],R,'pct',1,'No district is in scope for this day in the current filter');
 el('mdpDayLbl').textContent=mdpDayLbl();
 el('mdpCnt2').textContent=R.length+' districts · '+mdpLbl(R);
 el('capMDP').innerHTML='Click a column to sort. A district with no report keeps its plan from the scope but shows <b>–</b> for deployment; reports timed after 12:00 carry ⚠.';
}
