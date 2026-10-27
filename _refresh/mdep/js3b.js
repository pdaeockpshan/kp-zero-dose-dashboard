function mdpOwnUI(){
 const on=!!_hraOwn,b=el('btnMDPown');
 if(b){b.textContent=on?'Owner mode: on':'Owner mode';b.classList.toggle('on',on);}
 ['btnMDPdel','btnMDPclear'].forEach(id=>{const x=el(id);if(!x)return;
  if(!x.dataset.bt)x.dataset.bt=x.title||'';
  x.disabled=!on;x.title=on?x.dataset.bt:'Owner only - unlock with the Owner mode button';});
 const l=el('mdpOwnLbl');if(l)l.textContent=on?'Owner mode is on for this visit':'Delete controls need the owner key';
}
function mdpOwnAsk(fn){if(_hraOwn){if(fn)fn();return;}hraOwnAsk(function(){mdpOwnUI();if(fn)fn();});}
function mdpDelOne(){mdpOwnAsk(function(){
 const n=el('mdpFDist').value,d=+el('mdpFDay').value||1;
 if(!mdpGet(d,n)){toast('No saved report for that district-day');return;}
 if(!window.confirm('Delete the saved morning report for '+(DNAME(n)||n)+', day '+d+'?\n\nA file you already downloaded is untouched.'))return;
 delete MDR[mdpKey(d,n)];mdpSave();renderMDEP();renderMDPBar();toast('Deleted day '+d);
});}
function mdpClearScope(){mdpOwnAsk(function(){
 const dv=mdpVal('mdpDiv'),dd=mdpVal('mdpDist'),scope=dd?(DNAME(dd)||dd):(dv?('division '+dv):'KP');
 const set={};mdpBase().forEach(o=>{set[o.n]=1;});
 const keys=[];
 Object.keys(MDR).forEach(k=>{const r=MDR[k];
  if(r&&set[r.n]&&(!MDD||r.day===MDD))keys.push(k);});
 if(!keys.length){toast('No saved reports in this scope');return;}
 if(!window.confirm('Delete '+keys.length+' saved morning report'+(keys.length===1?'':'s')+' for '
  +(MDD?('day '+MDD):'all days')+' in '+scope+'?\n\nFiles you already downloaded are untouched.'))return;
 keys.forEach(k=>{delete MDR[k];});mdpSave();renderMDEP();renderMDPBar();toast('Deleted '+keys.length+' report'+(keys.length===1?'':'s'));
});}
