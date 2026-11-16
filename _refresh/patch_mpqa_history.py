"""One-shot: add the 2026 MPQA round-history card to the pre-campaign readiness block.

The MPQA card itself is wired to the live round only (const MPQA = SNID Nov-26), so the
rounds already carried in MPQAH - SNID Sept 2026, SNID May 2026, NID Apr/Feb 2026 - were
visible only as per-campaign columns on the Campaign indicators plate.  This card prints
them side by side, with no cross-round total because each round is a different targeted
sample.

The 16-Nov-2026 Micro Plan Scoring exports for SNID Sept and SNID May were compared
UC by UC against MPQAH before this patch: 260 and 178 reported UCs, 0 differences, so the
caption says the re-read matched instead of pretending a figure moved.
"""
P = 'index.html'
t = open(P, encoding='utf-8', newline='').read()


def one(old, new):
    global t
    assert t.count(old) == 1, (t.count(old), old[:80])
    t = t.replace(old, new)


CARD = ('<div class="card" id="cardMPQH" style="margin-bottom:16px;display:none"><div class="tblhdr">'
        '<h3 style="margin:0">MPQA across the 2026 rounds &mdash; each campaign&rsquo;s assigned sample</h3>'
        '<span class="cnt" id="cntMPQH"></span><span style="flex:1"></span>'
        '<button class="btn" id="btnMPQHcsv">Download (CSV)</button></div>'
        '<div class="scroll"><table id="tMPQH"></table></div><div class="cap" id="capMPQH"></div></div>')

# 1. markup: after the UC MPQA card, still inside the live pre-campaign block
anchor = ('<div class="cap" id="capMPQU"></div></div>\r\n</div>\r\n<div id="cpreOld">')
one(anchor, '<div class="cap" id="capMPQU"></div></div>\r\n' + CARD + '\r\n</div>\r\n<div id="cpreOld">')

# 2. renderer, immediately before the live-round renderer
JS = r"""// ---------- MPQA round history: the 2026 campaigns side by side ----------
// Each round is its own targeted sample, so the rows are not coverage and must never be
// added into one provincial total; only the passes are shares of that round's reported UCs.
function renderMPQH(){
 const H=(typeof MPQAH!=='undefined'&&MPQAH&&MPQAH.r)?MPQAH:null, card=el('cardMPQH'); if(!card)return;
 const Y=H?H.r.filter(q=>/2026$/.test(q.c||'')):[];
 if(!Y.length){card.style.display='none';return;}
 card.style.display='';
 const pctU=(v,g,w)=>v==null||isNaN(v)?'\u2013':'<span class="rg '+(v>=g?'g':v>=w?'a':'r')+'">'+rnd(v,1)+'%</span>';
 const cntH=(v,bad)=>v?'<span class="rg '+(bad?'r':'a')+'">'+fmt(v)+'</span>':'<span class="rg g">0</span>';
 const rows=Y.map((q,i)=>{const A=q.t||[],pl=A[0],sc=A[1],ps=A[2],ni=A[3],si=A[4];
  return {c:q.c,q:q.q,o:i+1,nd:(q.n||[])[0],pl:pl,sc:sc,sp:pl?sc/pl*100:null,ps:ps,ni:ni,si:si,pp:sc?ps/sc*100:null};});
 drawTable('tMPQH',[{k:'c',l:'Campaign',sv:x=>x.o,f:x=>'<b>'+esc(x.c)+'</b>'},
  {k:'q',l:'Portal round'},
  {k:'nd',l:'Districts',n:1,f:x=>fmt(x.nd)},
  {k:'pl',l:'UCs assigned',n:1,tt:'The targeted sample the Federal office assigned for that round \u2014 low-performing or flagged UCs, never every UC',f:x=>fmt(x.pl)},
  {k:'sc',l:'Reported',n:1,f:x=>fmt(x.sc)},
  {k:'sp',l:'Reported % of assigned',n:1,f:x=>pctU(x.sp,100,70)},
  {k:'ps',l:'Pass 90+',n:1,f:x=>cntH(x.ps,false)},
  {k:'ni',l:'Needs improvement 70-89',n:1,f:x=>cntH(x.ni,false)},
  {k:'si',l:'Serious issues under 70',n:1,f:x=>cntH(x.si,true)},
  {k:'pp',l:'Pass % of reported',n:1,f:x=>pctU(x.pp,90,70)}],rows,'c',1);
 el('cntMPQH').textContent=rows.length+' rounds \u00b7 history read '+esc(H.gen);
 el('capMPQH').textContent='Counts are UCs, not children, and each row is that round\u2019s assigned sample \u2014 a targeted list, not every UC \u2014 so the rows are not coverage and are not added into one total. The card above carries the live round\u2019s district and UC detail; the Campaign indicators plate carries each campaign\u2019s own MPQA columns at district and UC grain. SNID Sept 2026 and SNID May 2026 were re-read from the EOC Micro Plan Scoring export on 16-Nov-2026: all 260 and all 178 reported UCs matched this history exactly, so no figure moved.';
 el('btnMPQHcsv').onclick=()=>cqCSV('MPQA_2026_rounds',['Campaign','Portal round','Districts','UCs assigned','Reported','Reported % of assigned','Pass 90+','Needs improvement 70-89','Serious issues under 70','Pass % of reported'],rows.map(x=>[x.c,x.q,x.nd,x.pl,x.sc,x.sp==null?'':rnd(x.sp,1),x.ps,x.ni,x.si,x.pp==null?'':rnd(x.pp,1)]));
}
function renderMPQ(){"""
JS = JS.replace('\n', '\r\n')
one('function renderMPQ(){', JS)

# 3. call it even when the live round payload is absent
one('function renderMPQ(){\r\n const M=MPQA;', 'function renderMPQ(){\r\n renderMPQH();\r\n const M=MPQA;')

# 4. the hint says where the previous rounds live
one('they are <b>not</b> a province-wide micro-plan quality rate either.\';',
    'they are <b>not</b> a province-wide micro-plan quality rate either. The 2026 rounds sit side by side in the round-history table below; SNID Sept 2026 and SNID May 2026 were re-read on 16-Nov-2026 and matched it exactly.\';')

assert t.count('\r\n') == t.count('\n'), 'CRLF damaged'
open(P, 'w', encoding='utf-8', newline='').write(t)
print('ok: card, renderer, call and hint wired; %d CRLF lines' % t.count('\r\n'))
