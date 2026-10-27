function mdpFillScope(){
 const dv=el('mdpDiv'),dd=el('mdpDist'),fd=el('mdpFDist');if(!dv||!dd)return;
 const cur=dv.value,curD=dd.value,S=mdpScope();
 const dvs=[...new Set(S.map(o=>o.dv))].sort();
 dv.innerHTML='<option value="">All divisions</option>'+dvs.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');
 dv.value=dvs.indexOf(cur)>=0?cur:'';
 const list=mdpBase();
 dd.innerHTML='<option value="">All districts</option>'+list.map(o=>'<option value="'+esc(o.n)+'">'+esc(DNAME(o.n))+'</option>').join('');
 dd.value=list.some(o=>o.n===curD)?curD:'';
 if(fd){
  const keep=fd.value,g={};S.forEach(o=>{(g[o.dv]=g[o.dv]||[]).push(o.n);});
  fd.innerHTML=Object.keys(g).sort().map(k=>'<optgroup label="'+esc(k)+'">'
   +g[k].map(n=>'<option value="'+esc(n)+'">'+esc(DNAME(n))+'</option>').join('')+'</optgroup>').join('');
  fd.value=S.some(o=>o.n===keep)?keep:(S[0]?S[0].n:'');
 }
}
function mdpChipSub(d){
 const dd=mdpVal('mdpDist');if(dd)return mdpPhase(dd,d);
 if(d<=3)return 'active · all';
 if(d<=5)return 'catch-up · all';
 if(d<=7)return 'Peshawar &amp; Khyber';
 return 'extended';
}
function mdpDaysPaint(){
 const bar=el('mdpDays');if(!bar)return;
 const M=mdpMaxD();
 if(MDD>M)MDD=M;if(MDD<0)MDD=0;
 let h='<button type="button" data-d="0"'+(MDD===0?' class="on"':'')+'>All days<small>reported</small></button>';
 for(let d=1;d<=M;d++)h+='<button type="button" data-d="'+d+'"'+(MDD===d?' class="on"':'')
  +'>Day '+d+'<small>'+mdpChipSub(d)+'</small></button>';
 bar.innerHTML=h;
 bar.querySelectorAll('button').forEach(b=>b.onclick=()=>{MDD=+b.dataset.d;renderMDEP();renderMDPBar();});
}
function mdpNorm(s){return String(s==null?'':s).toUpperCase().replace(/[^A-Z0-9]/g,'');}
let _MDIX=null;
function mdpDix(){
 if(_MDIX)return _MDIX;const m={};
 const add=(k,v)=>{k=mdpNorm(k);if(k&&!m[k])m[k]=v;};
 SNDALL.forEach(o=>{add(o.n,o.n);add(DNAME(o.n),o.n);});
 if(typeof KPGEO!=='undefined')(KPGEO.d||[]).forEach(p=>{add(p.c,p.c);add(DNAME(p.c),p.c);});
 [['DIKHAN','DIKHAN'],['DOTIKHAN','DIKHAN'],['LAKKIMARWAT','LAKKIMRWT'],['LAKKIMARWAT','LAKKIMRWT'],
  ['KOHISTANUPPER','KOHISTANUPPER'],['KOHISTANLOWER','KOHISTANLOWER'],['KOLAIPALAS','KOLAIPALAS'],
  ['TORGHAR','TORGHAR'],['DIRLOWER','DIRLOWER'],['DIRUPPER','DIRUPPER'],
  ['CHITRALUPPER','CHITRALUPPER'],['CHITRALLOWER','CHITRALLOWER'],
  ['WAZIRISTANSOUTHUPPER','WAZIR-S Upper'],['WAZIRISTANSOUTHLOWER','WAZIR-S Lower'],
  ['WAZIRISTANNORTH','WAZIR-N'],['BARSWAT','BAR SWAT'],['SWAT','SWAT']].forEach(x=>add(x[0],x[1]));
 return _MDIX=m;
}
function mdpDist(s){
 const k=mdpNorm(s);if(!k)return null;const m=mdpDix();
 if(m[k])return m[k];
 const k2=k.replace(/^DISTRICT/,'');if(m[k2])return m[k2];
 const hit=Object.keys(m).filter(x=>x.length>=5&&(x.indexOf(k2)===0||k2.indexOf(x)===0));
 const u=[...new Set(hit.map(x=>m[x]))];
 return u.length===1?u[0]:null;
}
