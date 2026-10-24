# -*- coding: utf-8 -*-
"""Patch the micro-plan quality assessment (MPQA) block into the index.html master.

Lands four things in one atomic edit:
  1. `const MPQA = {...};`   - payload from _refresh/out/mpqa.json
  2. the card HTML          - inside #cpreNew, straight after the NEAP UC table
  3. `function renderMPQ()` - hint, five KPIs, stacked bar, district table, CSV
  4. the call site          - beside renderNEP() when the live campaign is shown

Master only: preview / public / internal build up through push_master.py, which is
a publish and needs the owner's go-ahead.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HERE = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = os.path.join(HERE, 'out', 'mpqa.json')
MASTER = 'index.html'

A_CONST = 'const NACT = '
A_HTML = '<div class="cap" id="capNEPU"></div></div>'
A_FUNC = 'function renderNEP(){'
A_CALL = 'renderNEP(); return; }'
CALLNEW = 'renderNEP(); renderMPQ(); return; }'

HTML = """<div class="hint" id="mpqHint"></div>
<div class="kpis">
<div class="card"><div class="kl">UCs picked for MPQA</div><div class="kv" id="mpq1">\u2013</div><div class="ks" id="mpq1s"></div></div>
<div class="card"><div class="kl">Reviews completed</div><div class="kv" id="mpq2">\u2013</div><div class="ks" id="mpq2s"></div></div>
<div class="card"><div class="kl">Pass \u00b7 score 90+</div><div class="kv" id="mpq3">\u2013</div><div class="ks" id="mpq3s"></div></div>
<div class="card"><div class="kl">Needs improvement \u00b7 70-89</div><div class="kv" id="mpq4">\u2013</div><div class="ks" id="mpq4s"></div></div>
<div class="card"><div class="kl">Serious issues \u00b7 under 70</div><div class="kv" id="mpq5">\u2013</div><div class="ks" id="mpq5s"></div></div>
</div>
<div class="card" style="margin-bottom:16px"><div class="tblhdr"><h3 style="margin:0">Micro-plan quality assessment (MPQA) by district \u2014 <span id="mpqCamp"></span></h3><span class="cnt" id="cntMPQ"></span><span style="flex:1"></span><button class="btn" id="btnMPQcsv">Download (CSV)</button></div><div id="cmpq1" class="ch"></div><div class="cap" id="capMPQ1"></div><div class="scroll"><table id="tMPQ"></table></div><div class="cap" id="capMPQ"></div></div>"""

JS = """// ---------- MPQA: micro-plan quality assessment of the UCs picked for review ----------
function renderMPQ(){
 const M=MPQA; if(!M||!M.d)return;
 const T=M.tot, picked=T[0], scored=T[1], pass=T[2], need=T[3], ser=T[4], pend=picked-scored;
 const su=(SND&&SND.d)?SND.d.reduce((a,r)=>a+(r[3]||0),0):0;
 const rows=Object.keys(M.d).sort().map(dn=>{const v=M.d[dn],o={d:dn,pl:v[0],sc:v[1],ps:v[2],ni:v[3],si:v[4]};
  o.un=o.pl-o.sc; o.sp=o.pl?o.sc/o.pl*100:null; o.pp=o.sc?o.ps/o.sc*100:null;
  o.under=o.sc?(o.ni+o.si)/o.sc*100:null; o.dv=D2DV[dn]||'';
  const s=(SND&&SND.d)?SND.d.find(x=>x[0]===dn):null; o.mp=s?s[3]:null; return o;});
 const bad=rows.filter(r=>r.si>0), deep=rows.filter(r=>r.un>0).sort((a,b)=>(b.un-a.un)||(a.sp-b.sp));
 const pcx=(a,b)=>b?pc(a/b*100):'\\u2013';
 el('mpqCamp').textContent=M.camp;
 el('mpqHint').innerHTML='Micro-plan quality assessment (MPQA) \\u2014 <b>not</b> the same measure as \\u201cmicroplans validated\\u201d in the NEAP table above. The countdown calendar puts <b>real-time MPQA of selected UCs</b> on 21-Oct-2026, <b>course correction for failed UCs</b> on 23\\u201324-Oct and <b>re-MPQA if required</b> on 26-Oct: the UCs scored here are the ones <b>assigned by the Federal office</b> and assessed live by District/Tehsil Officers and IMs, reported on the EOC <i>Campaign \\u203a Pre Campaign \\u203a Micro Plan Scoring</i> export (<b>'+esc(M.src)+'</b>, generated '+esc(M.gen)+'). For '+esc(M.camp)+' that is <b>'+fmt(picked)+' UCs picked for review</b> out of <b>'+fmt(su)+' campaign UCs</b> across all '+M.n+' SND districts ('+pcx(picked,su)+' of the scope), and <b>'+fmt(scored)+'</b> of the picked UCs have been scored so far \\u2014 '+pcx(scored,picked)+' review progress, '+fmt(pend)+' still waiting. Pass / needs-improvement / serious shares are <b>of the UCs already scored</b>, never of the campaign.';
 el('mpq1').innerHTML=fmt(picked);
 el('mpq1s').textContent='of '+fmt(su)+' campaign UCs \\u00b7 '+pcx(picked,su)+' picked for review \\u00b7 '+M.n+' districts';
 el('mpq2').innerHTML=rgN(scored/picked*100,100,70,1);
 el('mpq2s').textContent=fmt(scored)+' of '+fmt(picked)+' scored \\u00b7 '+fmt(pend)+' still to review';
 el('mpq3').innerHTML=rgN(pass/scored*100,90,70,1);
 el('mpq3s').textContent=fmt(pass)+' UCs at 90+ \\u00b7 of the UCs scored';
 el('mpq4').innerHTML='<span class="rg '+(need/scored*100>15?'r':'a')+'">'+fmt(need)+'</span>';
 el('mpq4s').textContent=pcx(need,scored)+' of scored UCs \\u00b7 70\\u201389, course correction due 23\\u201324-Oct';
 el('mpq5').innerHTML='<span class="rg '+(ser?'r':'g')+'">'+fmt(ser)+'</span>';
 el('mpq5s').textContent=ser?(pcx(ser,scored)+' of scored UCs \\u00b7 under 70 in '+bad.map(r=>r.d).join(', ')):'no UC scored under 70';
 const G=rows.slice().sort((a,b)=>(b.un-a.un)||(a.sp-b.sp));
 el('cmpq1').style.height=Math.max(420,G.length*24+140)+'px';
 HC('cmpq1',{chart:{type:'bar',stacking:'normal'},
  title:{text:'UCs picked for micro-plan assessment \\u00b7 '+M.camp},
  subtitle:{text:'Where the score landed, and the reviews each district still has to do \\u2014 biggest backlog on top'},
  xAxis:{categories:G.map(r=>r.d)},
  yAxis:{min:0,max:Math.max.apply(null,G.map(r=>r.pl)),title:{text:'UCs picked for MPQA'},allowDecimals:false},
  tooltip:{shared:true},
  plotOptions:{bar:{stacking:'normal',borderWidth:0,borderRadius:2,
   dataLabels:{...dl,formatter:function(){return this.y?this.y:'';}}}},
  legend:{enabled:false},
  series:[{name:'Pass (90+)',color:'#16a34a',data:G.map(r=>r.ps||null)},
   {name:'Needs improvement (70-89)',color:'#f59e0b',data:G.map(r=>r.ni||null)},
   {name:'Serious issues (under 70)',color:'#dc2626',data:G.map(r=>r.si||null)},
   {name:'Picked, not yet scored',color:'#cbd5e1',data:G.map(r=>r.un||null)}]});
 CKEY('cmpq1',[['#16a34a','Pass \\u00b7 90+'],['#f59e0b','Needs improvement \\u00b7 70-89'],['#dc2626','Serious issues \\u00b7 under 70'],['#cbd5e1','Picked but not yet scored']]);
 el('capMPQ1').textContent=(deep.length?'Biggest review backlog: '+deep.slice(0,3).map(r=>r.d+' ('+r.un+' of '+r.pl+' picked UCs still unscored)').join('; ')+'.':'Every picked UC has been scored.')+(bad.length?' UCs scored under 70: '+bad.map(r=>r.d+' ('+r.si+')').join(', ')+'.':'');
 const stU=v=>v==null?'<span class="cnt">\\u2013</span>':rgN(v,100,70,1);
 const pU=v=>v==null?'<span class="cnt">\\u2013</span>':rgN(v,90,70,1);
 const cnt=(v,bad2)=>v?'<span class="rg '+(bad2?'r':'a')+'">'+fmt(v)+'</span>':'<span class="rg g">0</span>';
 drawTable('tMPQ',[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},
  {k:'dv',l:'Division',f:x=>esc(x.dv||'\\u2013')},critDCol(x=>x.d),
  {k:'mp',l:'Campaign UCs',n:1,f:x=>x.mp==null?'\\u2013':fmt(x.mp)},
  {k:'pl',l:'Picked for MPQA',n:1,f:x=>fmt(x.pl)},
  {k:'sc',l:'Scored',n:1,f:x=>fmt(x.sc)},
  {k:'sp',l:'Review progress',n:1,tt:'Share of this district\\'s picked UCs already scored',f:x=>stU(x.sp)},
  {k:'un',l:'Still to review',n:1,f:x=>x.un===0?'<span class="rg g">0</span>':'<span class="rg '+(x.sp<60?'r':'a')+'">'+fmt(x.un)+'</span>'},
  {k:'ps',l:'Pass',n:1,f:x=>cnt(x.ps,false)},
  {k:'pp',l:'Pass % of scored',n:1,f:x=>pU(x.pp)},
  {k:'ni',l:'Needs improvement',n:1,f:x=>cnt(x.ni,false)},
  {k:'si',l:'Serious issues',n:1,f:x=>cnt(x.si,true)},
  {k:'under',l:'Under 90 % of scored',n:1,f:x=>x.under==null?'\\u2013':'<span class="rg '+(x.under<=5?'g':x.under<=15?'a':'r')+'">'+rnd(x.under)+'</span>'}],rows,'un',-1);
 el('cntMPQ').textContent=M.n+' districts \\u00b7 '+fmt(scored)+' of '+fmt(picked)+' picked UCs scored \\u00b7 '+esc(M.gen);
 el('capMPQ').textContent='Counts, not rates. Picked for MPQA is the UC list the Federal office assigned to this district, Scored is what has been assessed, and the three band columns split only the scored UCs. Review progress = scored / picked, while Pass % and Under 90 % are of the scored UCs \\u2014 so a district can pass everything it has looked at and still be the one behind on the review (grey bar above). Review progress green at 100%, amber from 70%; pass share green at 90+, amber from 70; under 90 % of scored is better near zero. Course correction for failed UCs is due 23\\u201324-Oct-2026 and re-MPQA 26-Oct on the countdown calendar.';
 el('btnMPQcsv').onclick=()=>cqCSV('MPQA_'+M.camp,['District','Division','Category','Campaign UCs','UCs picked for MPQA','UCs scored','Review progress %','Picked not yet scored','Pass 90+','Pass % of scored','Needs improvement 70-89','Serious issues under 70','Under 90 % of scored'],
  rows.map(x=>[x.d,x.dv,critLab(x.d),x.mp==null?'':x.mp,x.pl,x.sc,x.sp==null?'':rnd(x.sp),x.un,x.ps,x.pp==null?'':rnd(x.pp),x.ni,x.si,x.under==null?'':rnd(x.under)]));
}
"""

_HTML = HTML.replace('\n', '\r\n')
_JS = JS.replace('\n', '\r\n')


def patch(v, js):
    t = v.text
    for a in (A_CONST, A_HTML, A_FUNC, A_CALL):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1): %r' % (t.count(a), a[:48]))
    t = t.replace(A_CONST, 'const MPQA = %s;\r\n' % js + A_CONST)
    t = t.replace(A_HTML, A_HTML + '\r\n' + _HTML)
    t = t.replace(A_FUNC, _JS + '\r\n' + A_FUNC)
    t = t.replace(A_CALL, CALLNEW)
    v.text = t
    v.changes.append('MPQA block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for needle in ('const MPQA = {', 'id="mpqHint"', 'id="mpq1"', 'id="mpq5s"', 'id="cmpq1"',
                   'id="capMPQ1"', 'id="tMPQ"', 'id="cntMPQ"', 'id="btnMPQcsv"', 'id="capMPQ"',
                   'function renderMPQ(){', CALLNEW):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    v.require(t.count("CKEY('cmpq1'") == 1, 'the MPQA chart lost its colour key')
    v.require(t.count('renderNEP();') == 4, 'expected renderNEP() to keep its 4 call sites')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_mpqa.py first' % PAYLOAD)
    js = srcutil.read_text(PAYLOAD).strip()
    json.loads(js)                       # the payload must be valid JSON before it is embedded
    if '\n' in js or '\r' in js:
        raise SystemExit('mpqa.json must be a single line for the <script> embed')
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'const MPQA = ' in v.text:
        raise SystemExit('%s already has an MPQA const - not patching twice' % v.rel)
    patch(v, js)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK mpqa-ui master only - preview / public / internal pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
