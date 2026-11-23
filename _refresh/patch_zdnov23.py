# -*- coding: utf-8 -*-
"""Ingest the SNID Nov-2026 IDIMS comparison report (23-Nov-2026, UC grain).

Rebuilds the DNOV payload (the Nov digitization view that sits beside the Sept DATA view),
flips the home digitization gate, and re-labels every prose surface that still says the
Nov digitization return is awaited. Everything asserts before the single write.
"""
import json
import sys

import pandas as pd

sys.path.insert(0, r'C:\Users\HD\Documents\kp-zero-dose-dashboard\_refresh')
import dashpatch

P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
SRC = r'C:\Users\HD\Downloads\Comparison_Report_2026-11-23 (1).xlsx'

t = open(P, encoding='utf-8', newline='').read()
assert t.count('\n') == t.count('\r\n'), 'CRLF damaged before patch'
assert '"k":["c","rep","ll"]' in t, 'expected the old 3-key DNOV payload'


def j(*ls):
    return '\r\n'.join(ls)


def rep(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, ('count %d != %d for %r' % (c, n, old[:110]))
    t = t.replace(old, new)


# ---------------- 1. rebuild DNOV ----------------
df = pd.read_excel(SRC, header=2)
df = df[pd.to_numeric(df['Sr No'], errors='coerce').notna()].copy()
assert len(df) == 421, len(df)
assert df['Campaign'].unique().tolist() == ['SNID Nov 2026'], df['Campaign'].unique()
df['code'] = df['UC Code'].map(lambda v: str(int(float(v))))

rows = []
for _, r in df.iterrows():
    def iv(v):
        if pd.isna(v):
            return 0
        return int(round(float(v)))
    rows.append([r['code'], iv(r['ZD Reported']), iv(r['ZD Linelist']),
                 iv(r['ZD Coverage']), iv(r['Still ZD Reported']), iv(r['Duplicate Count'])])

# prove against the report's own Grand Total row before trusting the row build
tot = df[['ZD Reported', 'ZD Linelist', 'ZD Coverage', 'Still ZD Reported', 'Duplicate Count']].sum()
assert [int(round(x)) for x in tot.tolist()] == [26478, 22529, 7168, 1376, 3], tot.tolist()
got = [sum(x[i] for x in rows) for i in (1, 2, 3, 4, 5)]
assert got == [26478, 22529, 7168, 1376, 3], got
assert len(set(x[0] for x in rows)) == 421, 'duplicate UC codes'

DATA = json.loads(dashpatch.get_payload(t, 'DATA').replace('<\\/', '</'))
zc = set(r['c'] for r in DATA)
assert set(x[0] for x in rows) == zc, 'Nov UC set differs from the Sept digitization UC set'
# identity is taken from DATA; prove the report agrees on district + tehsil
D = {r['c']: r for r in DATA}
up = lambda s: str(s).strip().upper()
for _, r in df.iterrows():
    g = D[r['code']]
    assert up(g['d']) == up(r['District']) and up(g['t']) == up(r['Tehsil']), (
        r['code'], g['d'], g['t'], r['District'], r['Tehsil'])

DNOV = {
    'camp': 'SNID Nov 2026',
    'asof': '23-Nov-2026',
    'src': 'IDIMS comparison report, UC level (Comparison_Report_2026-11-23 (1).xlsx)',
    'k': ['c', 'rep', 'll', 'cov', 'sr', 'dup'],
    'r': rows,
}
payload = json.dumps(DNOV, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
assert '\n' not in payload and '\r' not in payload
i, e = dashpatch.payload_span(t, 'DNOV')
old_len = e - i
t = t[:i] + payload + t[e:]
print('DNOV %d -> %d chars, %d rows' % (old_len, len(payload), len(rows)))

# ---------------- 2. gate ----------------
rep('const HZNOVRET={dig:false,val:false};', 'const HZNOVRET={dig:true,val:false};')

# ---------------- 3. masthead ----------------
rep(
    '<b>Digitization</b>: SNID Sept 2026 linelist vs IDIMS, report of 08-Nov-2026 (421 UCs, 9 districts), compared with SNID May 2026 (22-Jun-2026) · ',
    '<b>Digitization</b>: SNID Nov 2026 return of 23-Nov-2026 (421 UCs, 9 districts, 85.1% entered, 7,168 covered) · SNID Sept 2026 linelist vs IDIMS, report of 08-Nov-2026 (97.5% entered), compared with SNID May 2026 (22-Jun-2026) · ')

# ---------------- 4. section-2 counter ----------------
rep(
    '<span class="cnt">SNID Sept 2026 (last digitized round) · linelist entered ÷ IDIMS reported · 9 districts · SNID Nov-26 digitization return awaited</span>',
    '<span class="cnt">SNID Nov 2026 return in (23-Nov-2026) · 85.1% entered, 7,168 covered · 9 districts · SNID Sept 2026 last complete (97.5% entered)</span>')

# ---------------- 5. overview caption ----------------
rep(
    'Coverage % is SNID Sept-26, the latest campaign with a covered figure; the Nov column is the SNID Nov-26 UC-wise recorded return, whose covered figure is awaited. Digitization covers only the 9 districts in the IDIMS comparison report ("–" elsewhere).',
    'Coverage % is SNID Sept-26, the latest campaign with a province-wide covered figure; the Nov column is the SNID Nov-26 UC-wise recorded return, whose province-wide covered figure is awaited (the 9-district IDIMS return carries 7,168 covered). Digitization covers only the 9 districts in the IDIMS comparison report ("–" elsewhere); the Nov return is in for those 9.')

# ---------------- 6. register bullet ----------------
rep(
    "its covered figure and digitization are post-campaign returns that are still awaited, while its validation return has not started.",
    "its province-wide covered figure is a post-campaign return still awaited, its digitization return of 23-Nov-2026 is in for the 9 comparison-report districts, and its validation return has not started.")

# ---------------- 7. zero-dose hub heading ----------------
rep(
    'SNID Nov-26 recorded zero dose is in; its coverage and IDIMS digitization are the post-campaign returns awaited; LQAS is in and validation has not started; the IDIMS card stays blank until that return is compiled rather than showing an earlier round.',
    'SNID Nov-26 recorded zero dose is in; its digitization return of 23-Nov-2026 is in for the 9 comparison-report districts, its province-wide covered figure is a post-campaign return awaited, LQAS is in and validation has not started.')

# ---------------- 8. double-risk caption ----------------
rep(
    'Nov validation is coming in; its covered figure and digitization are post-campaign returns and are still awaited.',
    'Its province-wide covered figure is a post-campaign return still awaited and its validation has not started; its digitization return of 23-Nov-2026 is in for the 9 comparison-report districts.')

# ---------------- 9. dnovCard chrome ----------------
rep(
    '<div class="tblhdr"><h3 style="margin:0">SNID Nov-26 linelist entry so far <span style="font-weight:400;color:#64748b">(in progress)</span></h3><span class="cnt" id="dnovCnt"></span></div>',
    '<div class="tblhdr"><h3 style="margin:0">SNID Nov-26 digitization return <span style="font-weight:400;color:#64748b">(report of 23-Nov-2026)</span></h3><span class="cnt" id="dnovCnt"></span></div>')
rep('<div class="card"><div class="kl">Entered so far</div><div class="kv" id="dn1">–</div><div class="ks" id="dn1s"></div></div>',
    '<div class="card"><div class="kl">Linelist entered</div><div class="kv" id="dn1">–</div><div class="ks" id="dn1s"></div></div>')
rep('<div class="card"><div class="kl">UCs with 0 entries</div><div class="kv" id="dn4">–</div><div class="ks" id="dn4s"></div></div>',
    '<div class="card"><div class="kl">Covered in the IDIMS return</div><div class="kv" id="dn4">–</div><div class="ks" id="dn4s"></div></div>')
rep(
    '<div class="cap">Entry for SNID Nov-26 continues after the campaign, so low figures now are expected. The cards and charts below this panel stay on SNID Sept-26 until Nov entry is complete.</div>',
    '<div class="cap">The comparison report of 23-Nov-2026 covers the 9 districts that digitize through IDIMS. Covered and still zero-dose are that report\'s own columns, not a province-wide covered figure. The cards and charts below this panel stay on SNID Sept-26, the last round with a complete digitization return.</div>')

# ---------------- 10. renderDNov ----------------
old = j(
    '// ---------- SNID Nov-26 digitization progress (separate from the Sept view) ----------',
    'function renderDNov(){',
    " if(typeof DNOV==='undefined'||!DNOV||!el('dnovCard'))return;",
    ' const G={};DATA.forEach(r=>G[r.c]=r);',
    ' const qq=q.value.trim().toLowerCase();',
    ' const R=DNOV.r.map(x=>{const g=G[x[0]]||{};return {c:x[0],rep:x[1],ll:x[2],dv:g.dv,d:g.d,t:g.t,u:g.u};}).filter(r=>r.d&&',
    "  !(!dvOK(r.dv))&&dOK(r.d)&&!(fTeh.value&&r.t!==fTeh.value)&&!(!ucOK(r.c))&&",
    "  !(qq&&!(r.u+' '+r.t+' '+r.c+' '+r.d).toLowerCase().includes(qq)));",
    ' const rep=R.reduce((a,r)=>a+r.rep,0),ll=R.reduce((a,r)=>a+r.ll,0),gap=R.reduce((a,r)=>a+Math.max(0,r.rep-r.ll),0);',
    ' const zero=R.filter(r=>r.rep>0&&r.ll===0),p=rep?ll/rep*100:null;',
    ' const colP=v=>v>=95?C.high:v>=80?C.mod:v>=50?C.low:C.crit;',
    " el('dnovHint').textContent=DNOV.camp+' \\u00b7 '+DNOV.src+' \\u00b7 read '+DNOV.asof+'. Shown next to the SNID Sept-26 view, not instead of it.';",
    " el('dnovCnt').textContent=R.length+' UCs in view';",
    " el('dn1').textContent=p==null?'\\u2013':p.toFixed(1)+'%'; el('dn1').style.color=p==null?C.text:colP(p); el('dn1s').textContent='target 95% once entry closes';",
    " el('dn2').textContent=fmt(ll); el('dn2s').textContent='of '+fmt(rep)+' reported';",
    " el('dn3').textContent=fmt(gap);",
    " el('dn4').textContent=zero.length; el('dn4s').textContent=fmt(zero.reduce((a,r)=>a+r.rep,0))+' reported ZDs with no linelist yet';",
    " const byTeh=!!(fDist.value&&!DSEL),key=byTeh?'t':'d',lvl=byTeh?'tehsil':'district';",
    " const g={};R.forEach(r=>{const k=r[key];const o=g[k]=g[k]||{k,rep:0,ll:0,gap:0,z:0,n:0};o.rep+=r.rep;o.ll+=r.ll;o.gap+=Math.max(0,r.rep-r.ll);o.n++;if(r.rep>0&&r.ll===0)o.z++;});",
    " const gl=Object.values(g).map(o=>Object.assign(o,{p:o.rep?o.ll/o.rep*100:null}));",
    ' const g1=gl.filter(x=>x.p!=null).sort((a,b)=>b.p-a.p);',
    " Highcharts.chart('cNov',{chart:{type:'bar'},title:{text:'SNID Nov-26: % entered by '+lvl},subtitle:{text:'Dashed line = 95% target'},",
    "  xAxis:{categories:g1.map(x=>x.k)},yAxis:{title:{text:'Linelist \\u00f7 Reported (%)'},min:0,max:Math.max(100,...g1.map(x=>x.p)),plotLines:[{value:95,color:C.high,dashStyle:'Dash',width:2,zIndex:5}]},",
    "  legend:{enabled:false},tooltip:{useHTML:true,formatter(){const x=g1[this.point.index];return '<b>'+esc(x.k)+'</b><br>Entered '+fmt(x.ll)+' of '+fmt(x.rep)+' ('+x.p.toFixed(1)+'%)<br>'+x.z+' of '+x.n+' UCs with no entries';}},",
    "  plotOptions:{bar:{borderRadius:3,dataLabels:{enabled:true,format:'{y:.1f}%',style:{color:C.sec,textOutline:'none',fontWeight:'400'}}}},",
    "  series:[{name:'% entered',data:g1.map(x=>({y:+x.p.toFixed(1),color:colP(x.p)}))}]});",
    " el('capNov').textContent=g1.length>1?g1[g1.length-1].k+' is lowest at '+g1[g1.length-1].p.toFixed(1)+'%; '+g1[0].k+' leads at '+g1[0].p.toFixed(1)+'%.':'';",
    " el('tNovH').textContent='By '+lvl;",
    " drawTable('tNov',[{k:'k',l:lvl==='tehsil'?'Tehsil':'District'},{k:'rep',l:'ZD reported',n:1,f:r=>fmt(r.rep)},{k:'ll',l:'Entered',n:1,f:r=>fmt(r.ll)},",
    "  {k:'p',l:'% entered',n:1,f:r=>r.p==null?'\\u2013':'<b style=\"color:'+colP(r.p)+'\">'+r.p.toFixed(1)+'%</b>'},{k:'gap',l:'Not entered',n:1,f:r=>fmt(r.gap)},{k:'z',l:'UCs with 0 entries',n:1,f:r=>r.z+' / '+r.n}],gl,'p',1);",
    '}')

new = j(
    '// ---------- SNID Nov-26 digitization return (separate from the Sept view) ----------',
    'function renderDNov(){',
    " if(typeof DNOV==='undefined'||!DNOV||!el('dnovCard'))return;",
    ' const G={};DATA.forEach(r=>G[r.c]=r);',
    ' const qq=q.value.trim().toLowerCase();',
    ' const R=DNOV.r.map(x=>{const g=G[x[0]]||{};return {c:x[0],rep:x[1]||0,ll:x[2]||0,cov:x[3]||0,sr:x[4]||0,dv:g.dv,d:g.d,t:g.t,u:g.u};}).filter(r=>r.d&&',
    "  !(!dvOK(r.dv))&&dOK(r.d)&&!(fTeh.value&&r.t!==fTeh.value)&&!(!ucOK(r.c))&&",
    "  !(qq&&!(r.u+' '+r.t+' '+r.c+' '+r.d).toLowerCase().includes(qq)));",
    ' const rep=R.reduce((a,r)=>a+r.rep,0),ll=R.reduce((a,r)=>a+r.ll,0),gap=R.reduce((a,r)=>a+Math.max(0,r.rep-r.ll),0);',
    ' const cov=R.reduce((a,r)=>a+r.cov,0),zero=R.filter(r=>r.rep>0&&r.ll===0),p=rep?ll/rep*100:null,cp=ll?cov/ll*100:null;',
    ' const colP=v=>v>=95?C.high:v>=80?C.mod:v>=50?C.low:C.crit;',
    " el('dnovHint').textContent=DNOV.camp+' \\u00b7 '+DNOV.src+' \\u00b7 read '+DNOV.asof+'. Shown next to the SNID Sept-26 view, not instead of it; covered and still zero-dose are that report\\u2019s own columns.';",
    " el('dnovCnt').textContent=R.length+' UCs in view';",
    " el('dn1').textContent=p==null?'\\u2013':p.toFixed(1)+'%'; el('dn1').style.color=p==null?C.text:colP(p); el('dn1s').textContent='target 95% once entry closes';",
    " el('dn2').textContent=fmt(ll); el('dn2s').textContent='of '+fmt(rep)+' reported';",
    " el('dn3').textContent=fmt(gap);",
    " el('dn4').textContent=fmt(cov); el('dn4s').textContent=cp==null?'no covered column':'of '+fmt(ll)+' entered ('+cp.toFixed(1)+'%)';",
    " const byTeh=!!(fDist.value&&!DSEL),key=byTeh?'t':'d',lvl=byTeh?'tehsil':'district';",
    " const g={};R.forEach(r=>{const k=r[key];const o=g[k]=g[k]||{k,rep:0,ll:0,gap:0,z:0,n:0,cov:0,sr:0};o.rep+=r.rep;o.ll+=r.ll;o.gap+=Math.max(0,r.rep-r.ll);o.n++;o.cov+=r.cov;o.sr+=r.sr;if(r.rep>0&&r.ll===0)o.z++;});",
    " const gl=Object.values(g).map(o=>Object.assign(o,{p:o.rep?o.ll/o.rep*100:null}));",
    ' const g1=gl.filter(x=>x.p!=null).sort((a,b)=>b.p-a.p);',
    " Highcharts.chart('cNov',{chart:{type:'bar'},title:{text:'SNID Nov-26: % entered by '+lvl},subtitle:{text:'Dashed line = 95% target'},",
    "  xAxis:{categories:g1.map(x=>x.k)},yAxis:{title:{text:'Linelist \\u00f7 Reported (%)'},min:0,max:Math.max(100,...g1.map(x=>x.p)),plotLines:[{value:95,color:C.high,dashStyle:'Dash',width:2,zIndex:5}]},",
    "  legend:{enabled:false},tooltip:{useHTML:true,formatter(){const x=g1[this.point.index];return '<b>'+esc(x.k)+'</b><br>Entered '+fmt(x.ll)+' of '+fmt(x.rep)+' ('+x.p.toFixed(1)+'%)<br>'+x.z+' of '+x.n+' UCs with no entries';}},",
    "  plotOptions:{bar:{borderRadius:3,dataLabels:{enabled:true,format:'{y:.1f}%',style:{color:C.sec,textOutline:'none',fontWeight:'400'}}}},",
    "  series:[{name:'% entered',data:g1.map(x=>({y:+x.p.toFixed(1),color:colP(x.p)}))}]});",
    " el('capNov').textContent=(g1.length>1?g1[g1.length-1].k+' is lowest at '+g1[g1.length-1].p.toFixed(1)+'%; '+g1[0].k+' leads at '+g1[0].p.toFixed(1)+'%. ':'')+(zero.length?zero.length+' UCs have no entries yet.':'');",
    " el('tNovH').textContent='By '+lvl;",
    " drawTable('tNov',[{k:'k',l:lvl==='tehsil'?'Tehsil':'District'},{k:'rep',l:'ZD reported',n:1,f:r=>fmt(r.rep)},{k:'ll',l:'Entered',n:1,f:r=>fmt(r.ll)},",
    "  {k:'p',l:'% entered',n:1,f:r=>r.p==null?'\\u2013':'<b style=\"color:'+colP(r.p)+'\">'+r.p.toFixed(1)+'%</b>'},{k:'cov',l:'Covered',n:1,f:r=>fmt(r.cov)},{k:'sr',l:'Still ZD',n:1,f:r=>fmt(r.sr)}],gl,'p',1);",
    '}')
rep(old, new)

# ---------------- 11. home digitization card ----------------
old = j(
    ' }else{',
    "  el('hA2').style.display='';",
    ' const drep=S_(DATA,r=>r.rep), dll=S_(DATA,r=>r.ll), dp=drep?dll/drep*100:null;',
    ' const dDl=Object.values(DATA.reduce((a,r)=>{(a[r.d]=a[r.d]||{r:0,l:0});a[r.d].r+=r.rep;a[r.d].l+=r.ll;return a;},{}));',
    ' const dD=dDl.filter(x=>x.r&&x.l/x.r*100<90).length, dU=DATA.filter(r=>r.rep>0&&r.ll/r.rep*100<80).length, d0=DATA.filter(r=>r.rep>0&&r.ll===0).length;',
    " el('hR2').innerHTML=hRing(dp,'dig',104);",
    " el('hF2').innerHTML=`<div class=\"hf\"><b>${fmt(dll)}</b>linelisted children entered, of ${fmt(drep)} reported in IDIMS</div><div class=\"hf\"><b>${fmt(S_(DATA,gapOf))}</b>children still to be entered · ${DATA.length} UCs, 9 districts</div>`;",
    " hAlarm('hA2','Under-performing',[[dD,'districts',`${dD} districts below 90% digitized`,'overview'],[dU,'UCs',`${dU} UCs below 80% digitized, including ${d0} with no entries at all`,'followup']]);",
    ' }')
new = j(
    ' }else{',
    "  el('hA2').style.display='';",
    " const useN=HZNOVRET.dig, RS=useN?novDigRows():DATA;",
    ' const drep=S_(RS,r=>r.rep), dll=S_(RS,r=>r.ll), dp=drep?dll/drep*100:null;',
    ' const dDl=Object.values(RS.reduce((a,r)=>{(a[r.d]=a[r.d]||{r:0,l:0});a[r.d].r+=r.rep;a[r.d].l+=r.ll;return a;},{}));',
    ' const dD=dDl.filter(x=>x.r&&x.l/x.r*100<90).length, dU=RS.filter(r=>r.rep>0&&r.ll/r.rep*100<80).length, d0=RS.filter(r=>r.rep>0&&r.ll===0).length;',
    " el('hR2').innerHTML=hRing(dp,'dig',104);",
    " el('hF2').innerHTML=useN",
    "  ?`<div class=\"hf\"><b>${fmt(dll)}</b>linelisted children entered, of ${fmt(drep)} reported in IDIMS · ${esc(novLabel())} return of ${esc(DNOV.asof)}</div><div class=\"hf\"><b>${fmt(Math.max(0,drep-dll))}</b>children still to be entered · ${RS.length} UCs, 9 districts</div>`",
    "  :`<div class=\"hf\"><b>${fmt(dll)}</b>linelisted children entered, of ${fmt(drep)} reported in IDIMS</div><div class=\"hf\"><b>${fmt(S_(DATA,gapOf))}</b>children still to be entered · ${DATA.length} UCs, 9 districts</div>`;",
    " hAlarm('hA2','Under-performing',[[dD,'districts',`${dD} districts below 90% digitized`,'overview'],[dU,'UCs',`${dU} UCs below 80% digitized, including ${d0} with no entries at all`,'followup']]);",
    ' }')
rep(old, new)

# ---------------- 12. hzd strip metric + note ----------------
rep(
    " const dig=(k==='N'&&!HZNOVRET.dig)?['Digitized in IDIMS','–','post-campaign digitization return awaited','#6d28d9']:['Digitized in IDIMS',D.length?pc(dr?dl/dr*100:null):'–',D.length?`${fmt(dl)} of ${fmt(dr)} entered · ${fmt(Math.max(0,dr-dl))} not entered`:'no IDIMS data for this area (9 districts only)','#6d28d9'];",
    " const ND=(k==='N'&&HZNOVRET.dig)?novDigAgg(novDigRows().filter(matchG)):null;\r\n const dig=(k==='N'&&!HZNOVRET.dig)?['Digitized in IDIMS','–','post-campaign digitization return awaited','#6d28d9']:ND?['Digitized in IDIMS',ND.rep?pc(ND.p):'–',ND.rep?`${fmt(ND.ll)} of ${fmt(ND.rep)} entered · ${fmt(Math.max(0,ND.rep-ND.ll))} not entered`:'no IDIMS data in this area','#6d28d9']:['Digitized in IDIMS',D.length?pc(dr?dl/dr*100:null):'–',D.length?`${fmt(dl)} of ${fmt(dr)} entered · ${fmt(Math.max(0,dr-dl))} not entered`:'no IDIMS data for this area (9 districts only)','#6d28d9'];")
rep(
    "'SNID Nov-26 recorded zero dose is the round’s own UC-wise return. Its covered figure and IDIMS digitization are the post-campaign returns awaited, with LQAS in and validation still to start; SNID Sept-26 remains the last measured coverage.'",
    "'SNID Nov-26 recorded zero dose is the round’s own UC-wise return. Its IDIMS digitization return of 23-Nov-2026 is in for the 9 comparison-report districts; its province-wide covered figure is a post-campaign return awaited, with LQAS in and validation not started; SNID Sept-26 remains the last measured coverage.'")

# ---------------- 13. Nov digitization helpers ----------------
rep(
    'function novSum(){return novAgg(novRows().filter(matchG));}',
    j(
        'function novSum(){return novAgg(novRows().filter(matchG));}',
        "function novDigRows(){if(novDigRows._c)return novDigRows._c;const G={};DATA.forEach(r=>G[r.c]=r);",
        " const out=((typeof DNOV!=='undefined'&&DNOV)?DNOV.r:[]).map(x=>{const g=G[x[0]]||{};return {c:x[0],dv:g.dv,d:g.d,t:g.t,u:g.u,rep:x[1]||0,ll:x[2]||0,cov:x[3]||0,sr:x[4]||0,dup:x[5]||0};}).filter(r=>r.d);",
        ' novDigRows._c=out;return out;}',
        'function novDigAgg(rows){const w=rows||novDigRows();let rep=0,ll=0,cov=0,sr=0;const DS=new Set();',
        ' w.forEach(r=>{rep+=r.rep||0;ll+=r.ll||0;cov+=r.cov||0;sr+=r.sr||0;DS.add(r.d);});',
        ' return {n:w.length,rep,ll,cov,sr,dists:DS.size,p:rep?ll/rep*100:null,cl:ll?cov/ll*100:null};}'))

# ---------------- 14. cross-tab note ----------------
rep(
    "(g==='zi'?'SNID Nov-26 carries its own recorded zero-dose return only: the covered figure and digitization are the post-campaign returns still awaited, and validation is coming in. ':'')+(g==='hz'?'SNID Nov-26 carries recorded zero dose and LQAS: its covered figure arrives with the post-campaign return; its validation is in. ':'')",
    "(g==='zi'?'SNID Nov-26 carries its own recorded zero-dose return only: the province-wide covered figure is a post-campaign return still awaited, the digitization return of 23-Nov-2026 is in for the 9 comparison-report districts, and validation has not started. ':'')+(g==='hz'?'SNID Nov-26 carries recorded zero dose, LQAS and a 9-district digitization return: its province-wide covered figure arrives with the post-campaign return; its validation has not started. ':'')")

# ---------------- 15. register caption + method notes ----------------
rep(
    'Digitized is the Sept-26 linelist-vs-IDIMS exercise and exists only for the nine districts it covered, so every other round shows a dash.',
    'Digitized is the Sept-26 linelist-vs-IDIMS exercise and exists only for the nine districts it covered, so every other round shows a dash; the SNID Nov-26 return of 23-Nov-2026 covers the same nine districts and is shown on the Digitization tab.')
rep(
    "'Sept-26 linelist-vs-IDIMS exercise, report of 08-Nov-2026: nine districts, 421 UCs, 30,963 linelist entries against 31,762 IDIMS-reported children. Other rounds carry no digitization figure.'",
    "'Sept-26 linelist-vs-IDIMS exercise, report of 08-Nov-2026: nine districts, 421 UCs, 30,963 linelist entries against 31,762 IDIMS-reported children. SNID Nov-26 has a 23-Nov-2026 return for the same nine districts, shown on the Digitization tab; other rounds carry no digitization figure.'")
rep(
    "'Children written into the zero-dose linelist against the IDIMS figure. Only the Sept-26 exercise has it: nine districts, 421 UCs. Digitized % is entries \\u00f7 IDIMS reported on that same scope.'",
    "'Children written into the zero-dose linelist against the IDIMS figure. The Sept-26 exercise and the Nov-26 return each cover the same nine districts, 421 UCs. Digitized % is entries \\u00f7 IDIMS reported on that same scope.'")
rep(
    "'Sept-26 linelist-vs-IDIMS exercise, nine districts and 421 UCs, report of 08-Nov-2026: 30,963 linelist entries against 31,762 IDIMS-reported children. Other rounds carry no digitization figure.'",
    "'Sept-26 linelist-vs-IDIMS exercise, nine districts and 421 UCs, report of 08-Nov-2026: 30,963 linelist entries against 31,762 IDIMS-reported children. SNID Nov-26 has a 23-Nov-2026 return for the same nine districts, shown on the Digitization tab; other rounds carry no digitization figure.'")

# ---------------- 16. c3 deck zero-dose slide ----------------
rep(
    j(
        ' // 17 — zero dose',
        " {const s=base('Zero dose — 43,484 recorded, none yet covered','Children with no OPV dose recorded in the November round');",
        "  kpis(s,[{l:'Recorded ZD',v:n0(T.zd),s:p1(T.tgt?T.zd/T.tgt*100:null)+' of the HH target',c:RED},",
        "   {l:'ZD covered',v:'0',s:'covered column not compiled for Nov',c:GRY},"),
    j(
        ' // 17 — zero dose',
        ' {const DG=novDigAgg();',
        "  const s=base('Zero dose — '+n0(T.zd)+' recorded; '+n0(DG.cov)+' covered in IDIMS','Children with no OPV dose recorded in the November round');",
        "  kpis(s,[{l:'Recorded ZD',v:n0(T.zd),s:p1(T.tgt?T.zd/T.tgt*100:null)+' of the HH target',c:RED},",
        "   {l:'ZD covered',v:n0(DG.cov),s:DG.dists+' IDIMS districts · '+p1(DG.cl)+' of entered',c:AMB},"))
rep(
    "'The covered-zero-dose column has not been compiled for this round, so no recovery rate can be quoted yet. Sept-26 validation confirmed '+p1(VL.pct)+' of checked children as vaccinated; SNID Nov-26 validation has not started.',",
    "'The province-wide covered-zero-dose column has not been compiled; the IDIMS comparison return of 23-Nov-2026 covers '+DG.dists+' districts, where '+n0(DG.cov)+' of '+n0(DG.ll)+' entered children were covered ('+p1(DG.cl)+'). Sept-26 validation confirmed '+p1(VL.pct)+' of checked children as vaccinated; SNID Nov-26 validation has not started.',")
rep(
    "'5. Close the zero-dose loop: 43,484 recorded and no covered figure compiled; SNID Nov-26 validation has not started.',",
    "'5. Close the zero-dose loop: '+n0(T.zd)+' recorded; the 9-district IDIMS return shows '+n0(DG.cov)+' covered, and SNID Nov-26 validation has not started.',")
rep(
    "   ['Zero-dose validation','SNID Sep 2026 validation export','18-Nov-2026','UC'],",
    j(
        "   ['Zero-dose digitization','IDIMS comparison report, UC level (23-Nov-2026)','23-Nov-2026','UC → 9 districts'],",
        "   ['Zero-dose validation','SNID Sep 2026 validation export','18-Nov-2026','UC'],"))

# ---------------- 17. leftovers ----------------
rep("const HZNOVRET={dig:true,val:false}; // SNID Nov-26 post-campaign returns: flip a key to true in the round its return lands in DATA / VAL",
    "const HZNOVRET={dig:true,val:false}; // SNID Nov-26 post-campaign returns: dig is on since the 23-Nov-2026 IDIMS return")

for bad in ('"k":["c","rep","ll"]',
            'SNID Nov-26 digitization return awaited',
            'The covered-zero-dose column has not been compiled',
            "its validation is in. ",
            'Entry for SNID Nov-26 continues after the campaign'):
    assert bad not in t, ('leftover: %r' % bad)

assert t.count('\n') == t.count('\r\n'), 'CRLF damaged after patch'
open(P, 'w', encoding='utf-8', newline='').write(t)
print('patched %d chars' % len(t))
