# -*- coding: utf-8 -*-
"""Point the Summary tab's digitization block at the SNID Nov-26 return.

Sections: the five KPI cards (s2a..s2e) and sentence 2 of the "what the numbers say"
list. Sept stays visible as the last complete return. Every replacement asserts first.
"""
import sys

sys.path.insert(0, r'C:\Users\HD\Documents\kp-zero-dose-dashboard\_refresh')
P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'

t = open(P, encoding='utf-8', newline='').read()
assert t.count('\n') == t.count('\r\n')


def rep(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, ('count %d != %d for %r' % (c, n, old[:120]))
    t = t.replace(old, new)


# 1. derive the Nov layer once, beside the Sept aggregates
rep(
    ' const drep=S_(dR,r=>r.rep), dll=S_(dR,r=>r.ll), dgap=S_(dR,gapOf), dz0=dR.filter(r=>r.rep>0&&r.ll===0), dfu=dR.filter(r=>r.pr);\r\n'
    ' const dp=drep?dll/drep*100:null;\r\n',
    ' const drep=S_(dR,r=>r.rep), dll=S_(dR,r=>r.ll), dgap=S_(dR,gapOf), dz0=dR.filter(r=>r.rep>0&&r.ll===0), dfu=dR.filter(r=>r.pr);\r\n'
    ' const dp=drep?dll/drep*100:null;\r\n'
    " const nR=(typeof novDigRows==='function')?novDigRows().filter(matchG):[];\r\n"
    ' const nrep=S_(nR,r=>r.rep), nll=S_(nR,r=>r.ll), np=nrep?nll/nrep*100:null;\r\n'
    ' const nz0=nR.filter(r=>r.rep>0&&r.ll===0), nfu=nR.filter(r=>r.rep>0&&r.ll/r.rep*100<80);\r\n'
    " const nTop=(()=>{const g={};nR.forEach(r=>{g[r.d]=(g[r.d]||0)+gapOf(r);});return Object.entries(g).sort((a,b)=>b[1]-a[1])[0]||null;})();\r\n")

# 2. the five digits KPI cards
rep(
    " if(dR.length){\r\n"
    "  el('s2a').textContent=pc(dp); el('s2a').style.color=dp>=95?C.high:dp>=80?C.mod:C.crit;\r\n"
    "  el('s2as').textContent=`${dR.length} UCs · target 95%`;\r\n"
    "  el('s2b').innerHTML=`${fmt(dll)}<small> / </small>${fmt(drep)}`; el('s2bs').textContent='Linelist entered / IDIMS reported';\r\n"
    "  el('s2c').textContent=fmt(Math.max(0,drep-dll)); el('s2d').textContent=dz0.length; el('s2ds').textContent=fmt(S_(dz0,r=>r.rep))+' reported ZDs with no linelist';\r\n"
    "  el('s2e').textContent=dfu.length; el('s2es').textContent=`P1 ${dfu.filter(r=>r.pr==='P1').length} · P2 ${dfu.filter(r=>r.pr==='P2').length} · P3 ${dfu.filter(r=>r.pr==='P3').length} · P4 ${dfu.filter(r=>r.pr==='P4').length}`;\r\n",
    " if(nR.length||dR.length){\r\n"
    '  const useNov=nR.length>0, rep2=useNov?nrep:drep, ent2=useNov?nll:dll, p2=useNov?np:dp;\r\n'
    '  const ucs2=useNov?nR.length:dR.length, z02=useNov?nz0:dz0, fu2=useNov?nfu:dfu;\r\n'
    "  el('s2a').textContent=pc(p2); el('s2a').style.color=p2>=95?C.high:p2>=80?C.mod:C.crit;\r\n"
    "  el('s2as').textContent=`${ucs2} UCs · target 95%`+(useNov?' · Nov return of 23-Nov-2026':' · SNID Sept 2026');\r\n"
    "  el('s2b').innerHTML=`${fmt(ent2)}<small> / </small>${fmt(rep2)}`; el('s2bs').textContent=useNov?'Linelist entered / IDIMS reported · SNID Nov-26':'Linelist entered / IDIMS reported · SNID Sept-26';\r\n"
    "  el('s2c').textContent=fmt(useNov?S_(nR,gapOf):Math.max(0,drep-dll)); el('s2d').textContent=z02.length; el('s2ds').textContent=fmt(S_(z02,r=>r.rep))+' reported ZDs with no linelist';\r\n"
    "  el('s2e').textContent=fu2.length; el('s2es').textContent=useNov?(fu2.length-z02.length)+' partially entered · '+z02.length+' with none':`P1 ${dfu.filter(r=>r.pr==='P1').length} · P2 ${dfu.filter(r=>r.pr==='P2').length} · P3 ${dfu.filter(r=>r.pr==='P3').length} · P4 ${dfu.filter(r=>r.pr==='P4').length}`;\r\n")

# 3. sentence 2 of the narrative list
rep(
    " if(dR.length){\r\n"
    "  const gd={};dR.forEach(r=>{gd[r.d]=(gd[r.d]||0)+gapOf(r);});const top=Object.entries(gd).sort((a,b)=>b[1]-a[1])[0];\r\n"
    "  I.push(`<b>② Linelist digitization is ${pc(dp)}</b> for SNID Sept 2026 (${fmt(dll)} of ${fmt(drep)} reported). ${fmt(Math.max(0,drep-dll))} children are still to be entered and ${dz0.length} UCs have no entries`+(top&&top[1]&&!fDist.value?`; ${top[0]} has the largest backlog (${fmt(top[1])}).`:'.'));}\r\n",
    " if(nR.length){\r\n"
    "  I.push(`<b>② Linelist digitization is ${pc(np)}</b> for SNID Nov 2026 (${fmt(nll)} of ${fmt(nrep)} reported, the return of 23-Nov-2026). ${fmt(S_(nR,gapOf))} children are still to be entered and ${nz0.length} UCs have no entries`+(nTop&&nTop[1]&&!fDist.value?`; ${nTop[0]} has the largest backlog (${fmt(nTop[1])}).`:'')+(dR.length?` SNID Sept 2026, the last complete return, stands at ${pc(dp)}.`:''));}\r\n"
    " else if(dR.length){\r\n"
    "  const gd={};dR.forEach(r=>{gd[r.d]=(gd[r.d]||0)+gapOf(r);});const top=Object.entries(gd).sort((a,b)=>b[1]-a[1])[0];\r\n"
    "  I.push(`<b>② Linelist digitization is ${pc(dp)}</b> for SNID Sept 2026 (${fmt(dll)} of ${fmt(drep)} reported). ${fmt(Math.max(0,drep-dll))} children are still to be entered and ${dz0.length} UCs have no entries`+(top&&top[1]&&!fDist.value?`; ${top[0]} has the largest backlog (${fmt(top[1])}).`:'.'));}\r\n")

assert t.count('\n') == t.count('\r\n')
open(P, 'w', encoding='utf-8', newline='').write(t)
print('patched %d chars' % len(t))
