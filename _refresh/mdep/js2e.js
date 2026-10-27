const mdpStTag=s=>'<span class="st '+MDP_ST[s][0]+'">'+MDP_ST[s][1]+'</span>';
function mdpBn(R,T){
 const sec=(t,items)=>items.length?'<div class="bnsec"><b>'+t+'</b><ul>'+items.map(x=>'<li>'+x+'</li>').join('')+'</ul></div>':'';
 const no=R.filter(o=>!o.rep),out=[];
 out.push(sec('No report for '+mdpDayLbl().toLowerCase()+' — '+no.length+' district'+(no.length===1?'':'s'),
  no.slice(0,8).map(o=>'<b>'+esc(DNAME(o.n))+'</b> · '+fmt(o.uc)+' UCs planned')));
 const cr=R.filter(o=>o.rep&&(o.st==='crit'||o.st==='low')).sort((a,b)=>(a.pct||0)-(b.pct||0));
 out.push(sec('Under 85% of the field plan — '+cr.length+' district'+(cr.length===1?'':'s'),
  cr.slice(0,8).map(o=>'<b>'+esc(DNAME(o.n))+'</b> · '+o.pct.toFixed(0)+'% · '+fmt(o.awTot)+' teams awaited'+(o.rsn?' · '+esc(MDP_RSN[o.rsn]||o.rsn):''))));
 const inc=R.filter(o=>o.rep&&o.inc>0).sort((a,b)=>b.inc-a.inc);
 out.push(sec('Security incidents — '+fmt(T.inc)+' in view',inc.slice(0,6).map(o=>'<b>'+esc(DNAME(o.n))+'</b> · '+fmt(o.inc))));
 const late=R.filter(o=>mdpLate(o)).sort((a,b)=>(mdpMin(b.at)||0)-(mdpMin(a.at)||0));
 out.push(sec('Reports after 12:00 — '+late.length,late.slice(0,6).map(o=>'<b>'+esc(DNAME(o.n))+'</b> · '+esc(o.at))));
 const uca=R.filter(o=>o.rep&&o.ucAw>0).sort((a,b)=>b.ucAw-a.ucAw);
 out.push(sec('UCs awaited — '+fmt(T.ucp-T.ucr)+' in the register',uca.slice(0,6).map(o=>'<b>'+esc(DNAME(o.n))+'</b> · '+fmt(o.ucr)+' of '+fmt(o.ucp)+' reported ('+fmt(o.ucAw)+' awaited)')));
 const j=out.join('');
 return j||'<div class="bnnone">No reports yet — enter a district report below, or import the district sheets, and this block fills itself.</div>';
}
