function mdpCampN(c){return c===MDC?Object.keys(MDR).length:Object.keys(mdpCampRows(c)).length;}
function mdpFillCamp(){
 const s=el('mdpCamp');if(!s)return;
 s.innerHTML=MDP_CAMPS.map(c=>{const n=mdpCampN(c.k);
  return '<option value="'+esc(c.k)+'">'+esc(c.l)+(c.cur?' · current':'')+' · '
   +(n?fmt(n)+' report'+(n===1?'':'s'):'no reports yet')+'</option>';}).join('');
 s.value=MDC;
}
function mdpCampGo(c){
 if(!c||c===MDC)return;
 mdpSave();
 mdpLoadCamp(c);
 MDD=0;
 mdpFillScope();renderMDPBar();renderMDEP();
 toast('Viewing '+mdpCampLbl(c));
}
function renderMDPBar(){
 if(!el('mdpSheet'))return;
 mdpFillCamp();mdpFillScope();mdpDaysPaint();mdpOwnUI();
 const R=mdpRows(),N=R.length+(R.length===1?' district':' districts');
 el('mdpCnt').textContent=N;
 el('shown').innerHTML='Morning deployment · '+esc(mdpCampLbl())+' · <b>'+esc(mdpDayLbl())
  +'</b> · '+esc(mdpPlain(R))+' · reports stay in this browser';
 el('mdpHint').innerHTML='<b>'+N+'</b> in the '+esc(mdpCampLbl())+' register for '
  +esc(mdpDayLbl().toLowerCase())+'. Every district reports <b>3 active + 2 catch-up = 5</b> days; '
  +'Peshawar and Khyber <b>5 + 2 = 7</b>. Days after that are extended catch-up asked for by a district, '
  +'so the day list stays open to day '+MDP_MAXD+'. '
  +(MDC!=='NOV-26'?'This is a past campaign: its register is the district list that campaign\u2019s own '
   +'record carries, and only reports stored in this browser are shown. ':'')
  +'Type a report below or import the 39-column district sheet. Nothing leaves this browser unless you '
  +'download the workbook.';
 const b=el('bMD');if(b)b.textContent=MDD?('Day '+MDD):'All days';
}
function renderMDEP(){
 if(!el('mdpSheet'))return;
 try{
  mdpDaysPaint();
  const R=mdpRows(),T=mdpTot(R);
  mdpKpis(R,T);mdpCharts(R,T);mdpCharts2(R,T);mdpHeat(R);mdpTable(R);mdpMap(R);mdpSheetDraw(R,T);
  mdpDaysPaint();mdpOwnUI();mdpFormSync();
  const td=el('mdpTplDay');if(td&&MDD)td.value=String(MDD);
 }catch(e){console.error('mdep render',e);}
}
function mdpBind(){
 if(window._mdpBound)return;window._mdpBound=1;
 mdpBindTeams();
 const on=(id,ev,fn)=>{const x=el(id);if(x)x[ev]=fn;};
 on('mdpCamp','onchange',()=>mdpCampGo(el('mdpCamp').value));
 on('mdpDiv','onchange',()=>{mdpFillScope();renderMDEP();renderMDPBar();});
 on('mdpDist','onchange',()=>{renderMDEP();renderMDPBar();});
 on('btnMDPprint','onclick',()=>window.print());
 on('btnMDPcsv','onclick',mdpCsv);
 on('btnMDPx','onclick',()=>mdpExportBoard());
 on('btnMDPSave','onclick',mdpSaveForm);
 on('btnMDPreset','onclick',mdpFormSync);
 on('btnMDPown','onclick',()=>mdpOwnAsk(null));
 on('btnMDPdel','onclick',mdpDelOne);
 on('btnMDPclear','onclick',mdpClearScope);
 on('btnMDPtpl','onclick',()=>mdpExportTpl());
 on('mdpFDist','onchange',mdpFormSync);
 on('mdpFDay','onchange',()=>{MDD=+el('mdpFDay').value||1;renderMDEP();renderMDPBar();});
 const fm=el('mdpForm');
 if(fm)fm.querySelectorAll('input,select').forEach(x=>{
  if(x.id!=='mdpFDist'&&x.id!=='mdpFDay')x.addEventListener('input',mdpFormCalc);});
 const fl=el('mdpFile');
 if(fl)fl.onchange=e=>{const fs=[...e.target.files];e.target.value='';if(fs.length)mdpImportFiles(fs);};
 const td=el('mdpTplDay');
 if(td&&!td.options.length){
  td.innerHTML=[...Array(MDP_MAXD)].map((_,i)=>{const d=i+1;
   return '<option value="'+d+'">Day '+d+(d<=5?'':' · '+(d<=7?'Peshawar and Khyber':'extended'))+'</option>';}).join('');
  td.value=String(MDD||1);}
 mdpFillCamp();mdpFillScope();mdpFormSync();mdpOwnUI();
}
mdpBind();
