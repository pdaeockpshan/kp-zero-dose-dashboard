"""Add a district-grain detail view to the MPQA round-history card.

The owner re-read the EOC Micro Plan Scoring exports for NID APR 2026 and NID FEB 2026 on
16-Nov-2026; both matched the embedded MPQAH rounds UC by UC, so no figure moves. What the
section lacked was any way to read a closed round below the province total, so the history
card gets a round picker and a district table drawn from MPQAH.d, with its own total row.

One shot: aborts if the anchors are missing or already patched.
"""
import sys

P = 'index.html'

OLD_MARK = ('<div class="scroll"><table id="tMPQH"></table></div>'
            '<div class="cap" id="capMPQH"></div></div>')
NEW_MARK = ('<div class="scroll"><table id="tMPQH"></table></div>'
            '<div class="cap" id="capMPQH"></div>'
            '<div class="cqbar" style="margin:16px 0 10px"><b>Round detail</b>'
            '<select id="fMPQHD" aria-label="MPQA round detail"></select>'
            '<span class="cnt" id="cntMPQHD"></span><span style="flex:1"></span>'
            '<button class="btn" id="btnMPQHDcsv">Download round (CSV)</button></div>'
            '<div class="scroll" style="max-height:560px"><table id="tMPQHD"></table></div>'
            '<div class="cap" id="capMPQHD"></div></div>')

OLD_TAIL = "x.pp==null?'':rnd(x.pp,1)]));\r\n}"
NEW_TAIL = "x.pp==null?'':rnd(x.pp,1)]));\r\n renderMPQHD(Y,H);\r\n}"

OLD_HINT = ('The 2026 rounds sit side by side in the round-history table below; '
            'SNID Sept 2026 and SNID May 2026 were re-read on 16-Nov-2026 and matched it exactly.')
NEW_HINT = ('The 2026 rounds sit side by side in the round-history table below, and any one of '
            'them opens at district grain; all four closed 2026 rounds \\u2014 SNID Sept 2026, '
            'SNID May 2026, NID APR 2026 and NID FEB 2026 \\u2014 were re-read from the EOC Micro '
            'Plan Scoring export on 16-Nov-2026 and matched it exactly.')

OLD_CAP = ('SNID Sept 2026 and SNID May 2026 were re-read from the EOC Micro Plan Scoring export '
           'on 16-Nov-2026: all 260 and all 178 reported UCs matched this history exactly, so no '
           'figure moved.')
NEW_CAP = ('Pick a round under the table to read its districts. The four closed 2026 rounds were '
           're-read from the EOC Micro Plan Scoring export on 16-Nov-2026: SNID Sept 2026 (260 of '
           '277 assigned UCs reported), SNID May 2026 (178 of 214), NID APR 2026 (476 of 505) and '
           'NID FEB 2026 (466 of 493) matched this history UC by UC, so no figure moved.')

JS = r'''
// ---------- MPQA round detail: one closed round at district grain ----------
// A retired round keeps only its assigned sample's filed scores, so this table reports the
// sample and says so; it is never a district-wide micro-plan quality or coverage figure.
let MPQHDI=-1, MPQHDKEY='';
function renderMPQHD(Y,H){
 const sel=el('fMPQHD'), tb=el('tMPQHD'); if(!sel||!tb||!Y||!Y.length)return;
 const key=Y.map(q=>q.q).join('|');
 if(MPQHDKEY!==key){
  MPQHDKEY=key; MPQHDI=Y.length>1?1:0;
  sel.innerHTML=Y.map((q,i)=>'<option value="'+i+'">'+esc(q.c)+'</option>').join('');
 }
 if(MPQHDI<0||MPQHDI>=Y.length)MPQHDI=0;
 if(sel.value!==String(MPQHDI))sel.value=String(MPQHDI);
 sel.onchange=()=>{MPQHDI=+sel.value||0;renderMPQHD(Y,H);};
 const q=Y[MPQHDI], D=q.d||{}, nd=(q.n||[])[0];
 const rows=Object.keys(D).map(dn=>{const v=D[dn],pl=v[0],sc=v[1];
  return {d:dn,pl:pl,sc:sc,un:pl-sc,sp:pl?sc/pl*100:null,ps:v[2],ni:v[3],si:v[4],pp:sc?v[2]/sc*100:null};})
  .sort((a,z)=>(z.si-a.si)||(z.un-a.un)||((a.sp==null?101:a.sp)-(z.sp==null?101:z.sp)));
 const pcH=(v,g,w)=>v==null||isNaN(v)?'\u2013':'<span class="rg '+(v>=g?'g':v>=w?'a':'r')+'">'+rnd(v,1)+'%</span>';
 const T=rows.reduce((a,r)=>{['pl','sc','un','ps','ni','si'].forEach(k=>{a[k]+=r[k];});return a;},{pl:0,sc:0,un:0,ps:0,ni:0,si:0});
 drawTable('tMPQHD',[
  {k:'d',l:'District',f:r=>'<b>'+esc(r.d)+'</b>'},
  {k:'pl',l:'Assigned',n:1,tt:'UCs the Federal office put in this round\u2019s targeted sample for the district \u2014 low-performing or flagged UCs, never every UC',f:r=>fmt(r.pl)},
  {k:'sc',l:'Reported',n:1,tt:'Assigned UCs whose micro-plan review was filed; a partial review counts as reported',f:r=>fmt(r.sc)},
  {k:'sp',l:'Reported % of assigned',n:1,tt:'Share of the district\u2019s assigned sample that filed a review',f:r=>pcH(r.sp,100,70)},
  {k:'un',l:'Still to report',n:1,tt:'Assigned UCs with no review filed; in a closed round these are reviews that never arrived',f:r=>r.un?'<span class="rg '+(r.sp<60?'r':'a')+'">'+fmt(r.un)+'</span>':'<span class="rg g">0</span>'},
  {k:'ps',l:'Pass 90+',n:1,tt:'Reported UCs scoring 90 or more on the over-all micro-plan score',f:r=>fmt(r.ps)},
  {k:'pp',l:'Pass % of reported',n:1,tt:'Pass share of the reported UCs only \u2014 not of the district',f:r=>pcH(r.pp,90,70)},
  {k:'ni',l:'Needs improvement 70-89',n:1,f:r=>fmt(r.ni)},
  {k:'si',l:'Serious issues under 70',n:1,f:r=>r.si?'<span class="rg r">'+fmt(r.si)+'</span>':'<span class="rg g">0</span>'}],
  rows,'d',1,'No district rows for this round',
  {cell:{d:esc('Total \u2014 all '+rows.length+' districts carrying an assignment (this round)'),
   pl:fmt(T.pl),sc:fmt(T.sc),sp:T.pl?pcH(T.sc/T.pl*100,100,70):'\u2013',un:fmt(T.un),
   ps:fmt(T.ps),pp:T.sc?pcH(T.ps/T.sc*100,90,70):'\u2013',ni:fmt(T.ni),si:fmt(T.si)}});
 el('cntMPQHD').textContent=q.c+' \u00b7 '+q.q+' \u00b7 '+rows.length+' of '+fmt(nd)+' districts';
 el('capMPQHD').textContent='Assigned UCs are the Federal office\u2019s targeted sample for '+q.c+', not coverage; Reported counts filed reviews (partials included), and Pass / needs improvement / serious are shares of those reported UCs only. The round was read from the '+(q.f==='new'?'current':'retired')+' EOC Micro Plan Scoring format, harvested '+(q.a||H.gen)+'.';
 el('btnMPQHDcsv').onclick=()=>cqCSV('MPQA_'+q.q.replace(/[^A-Za-z0-9]+/g,'_')+'_by_district',
  ['District','Assigned','Reported','Reported % of assigned','Still to report','Pass 90+','Pass % of reported','Needs improvement 70-89','Serious issues under 70'],
  rows.map(r=>[r.d,r.pl,r.sc,r.sp==null?'':rnd(r.sp,1),r.un,r.ps,r.pp==null?'':rnd(r.pp,1),r.ni,r.si]));
}
'''

JS = JS.replace('\n', '\r\n')

t = open(P, 'r', encoding='utf-8', newline='').read()
assert t.count('\r\n') == t.count('\n'), 'CRLF damaged before patch'
for name, anchor in (('markup', OLD_MARK), ('tail', OLD_TAIL), ('hint', OLD_HINT), ('caption', OLD_CAP)):
    assert t.count(anchor) == 1, 'anchor %s: %d hits' % (name, t.count(anchor))
assert t.count('renderMPQHD') == 0, 'already patched'
assert t.count('function renderMPQ(){') == 1

t = t.replace(OLD_MARK, NEW_MARK)
t = t.replace(OLD_TAIL, NEW_TAIL)
t = t.replace(OLD_HINT, NEW_HINT)
t = t.replace(OLD_CAP, NEW_CAP)
t = t.replace('function renderMPQ(){', JS + 'function renderMPQ(){', 1)

assert t.count('\r\n') == t.count('\n'), 'CRLF damaged after patch'
assert t.count('id="fMPQHD"') == 1 and t.count('id="tMPQHD"') == 1
open(P, 'w', encoding='utf-8', newline='').write(t)
print('patched', P, len(t), 'bytes')
