"""Insert the AFP case & lab database (AFPD) card into all 4 dashboard variants.

Adds, in each variant:
  1. `const AFPD = {};` placeholder before `const SURVW = ` (refresh.py run
     swaps in the real payload afterwards).
  2. A card after the WPV1 chart card on the surveillance tab: KPI strip,
     two charts (monthly 2026 cases; lab specimens vs results) and the
     36-district table, plus a CSV download button.
  3. The `renderSurDB()` renderer before `function renderSurv(){`, called
     right after `renderSurvW();` at the end of `renderSur()`.

All inserted text uses CRLF so the files' line endings stay uniform.
Every anchor is asserted to occur exactly once per variant before editing;
nothing is written unless all four variants patch cleanly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HTML = (
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">AFP case &amp; lab database \u2014 EOC master files</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntAFPD"></span>'
 '<button class="btn" id="btnAFPD">Download (CSV)</button></div></div>\r\n'
 '<div class="kpis" id="kAFPD"></div>\r\n'
 '</div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="afpdM" class="ch" style="height:330px"></div><div class="cap" id="capafpdM"></div></div>\r\n'
 '<div class="card"><div id="afpdL" class="ch" style="height:330px"></div><div class="cap" id="capafpdL"></div></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="scroll"><table id="tAFPDb"></table></div>\r\n'
 '<div class="cap" id="capAFPD"></div>\r\n'
 '</div>\r\n'
)

JS = r"""
function renderSurDB(){
 if(typeof AFPD==='undefined'||!AFPD||!AFPD.d||!AFPD.y||!AFPD.k)return;
 const dnm=k=>(typeof DNAME==='function'?DNAME(k):k);
 const K=AFPD.k,ix=k=>K.indexOf(k);
 const y26=AFPD.y['2026']||[],y25=AFPD.y['2025']||[];
 const g=(y,k)=>{const i=ix(k);return i<0||y.length<=i?null:y[i];};
 const pct=(a,b)=>(a==null||b==null||!b)?null:a/b*100;
 const p1=v=>v==null?'\u2013':(Math.round(v*10)/10).toFixed(1);
 const MN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 const band=(v,hi,lo)=>v==null?C.none:v>=hi?C.high:v>=lo?C.mod:C.crit;
 el('cntAFPD').textContent='KP \u00b7 cases entered to '+(AFPD.asof||'')+' \u00b7 lab results to '+(AFPD.lres||'');
 const kpi=(l,v,s,col)=>'<div class="card"><div class="kl">'+l+'</div><div class="kv"'+(col?' style="color:'+col+'"':'')+'>'+v+'</div><div class="ks">'+s+'</div></div>';
 const sa26=pct(g(y26,'ad'),g(y26,'n')),n726=pct(g(y26,'n7'),g(y26,'n')),i4826=pct(g(y26,'i48'),g(y26,'n'));
 el('kAFPD').innerHTML=[
  kpi('AFP cases 2026',fmt(g(y26,'n')),'onset to '+esc(AFPD.onset||'')+' \u00b7 '+fmt(g(y25,'n'))+' in 2025'),
  kpi('Stool adequacy',p1(sa26)+'%','target \u2265 90% \u00b7 '+p1(pct(g(y25,'ad'),g(y25,'n')))+'% in 2025',band(sa26,90,80)),
  kpi('Notified < 7 days',p1(n726)+'%','onset to notification \u00b7 '+p1(pct(g(y25,'n7'),g(y25,'n')))+'% in 2025',band(n726,80,60)),
  kpi('Investigated < 48 h',p1(i4826)+'%','notification to investigation \u00b7 '+p1(pct(g(y25,'i48'),g(y25,'n')))+'% in 2025',band(i4826,80,60)),
  kpi('Zero-dose AFP',fmt(g(y26,'zd')),'no OPV dose \u00b7 '+fmt(g(y25,'zd'))+' in 2025','#b91c1c'),
  kpi('WPV1 2026',fmt(g(y26,'c1')),'confirmed \u00b7 '+fmt(g(y25,'c1'))+' in 2025','#b91c1c')
 ].join('');
 const M=AFPD.mon26||[];
 const mEnd=M.reduce((a,v,i)=>v>0?i+1:a,0)||12;
 const cats=MN.slice(0,mEnd);
 HC('afpdM',{chart:{type:'column'},title:{text:'AFP cases by month \u2014 2026'},subtitle:{text:'KP \u00b7 EOC AFP case database (AFP.DBF)'},xAxis:{categories:cats},yAxis:{title:{text:'AFP cases'},allowDecimals:false},legend:{enabled:false},
  plotOptions:{column:{borderRadius:2,dataLabels:{...dl,format:'{y}'}}},tooltip:{pointFormatter:function(){return '<b>'+fmt(this.y)+'</b> AFP cases in '+cats[this.index]+' 2026'+(this.index===mEnd-1&&mEnd<12?' (month to date)':'');}},
  series:[{name:'AFP cases',data:M.slice(0,mEnd).map((v,i)=>({y:v,color:i===mEnd-1&&mEnd<12?'#f59e0b':'#1F497D'}))}]});
 const SV=(typeof SURVW!=='undefined'&&SURVW.mon&&SURVW.mon.d&&SURVW.mon.d.KP)||[];
 const wk=SV.length?SV[SV.length-1]:null;
 const octD=(wk&&wk[9]!=null&&M[9]!=null)?M[9]-wk[9]:null;
 el('capafpdM').textContent='2026 detection by month of onset, from the case database (onset up to '+esc(AFPD.onset||'')+').'+(octD!=null&&octD>0?' October already '+fmt(M[9])+' cases vs '+fmt(wk[9])+' in the '+(SURVW.asof||'')+' weekly log \u2014 the master database is a week fresher.':'')+' Amber = month to date.';
 const L=AFPD.lab||{},LM=L.sm||[],LR=L.rm||[];
 const lEnd=LM.reduce((a,v,i)=>v>0?i+1:a,0)||12;
 const lc=MN.slice(0,lEnd);
 HC('afpdL',{chart:{type:'column'},title:{text:'Lab specimens vs results \u2014 2026'},subtitle:{text:'KP \u00b7 EOC polio lab database (AFPLAB.DBF)'},xAxis:{categories:lc},yAxis:{title:{text:'Specimens'},allowDecimals:false},legend:{verticalAlign:'top'},tooltip:{shared:true},
  plotOptions:{column:{borderRadius:2,dataLabels:{...dl,format:'{y}'}}},
  series:[{name:'Specimens collected',color:'#1F497D',data:LM.slice(0,lEnd)},{name:'Results reported',color:'#15803d',data:LR.slice(0,lEnd)}]});
 el('capafpdL').textContent=fmt(L.sp||0)+' specimens collected in 2026 (to '+esc(AFPD.lcoll||'')+'), '+fmt(L.rs||0)+' results reported (to '+esc(AFPD.lres||'')+'). Turnaround: median '+(L.tt==null?'\u2013':L.tt+' days')+', '+p1(L.t14)+'% within 14 days. '+fmt(L.pv1||0)+' poliovirus type 1 and '+fmt(L.npev||0)+' NPEV isolations so far.';
 const rows=Object.keys(AFPD.d).map(k=>{const a=AFPD.d[k];return{d:k,dn:dnm(k),n:a[0],ad:a[1],n7:a[2],i48:a[3],zd:a[4],sa:pct(a[1],a[0]),n7p:pct(a[2],a[0]),i48p:pct(a[3],a[0])};});
 rows.sort((x,y)=>y.n-x.n);
 const cell=(v,hi,lo)=>{if(v==null)return'\u2013';return '<span style="color:'+(v>=hi?'#047857':v>=lo?'#92400E':'#991B1B')+';font-weight:600">'+p1(v)+'</span>';};
 drawTable('tAFPDb',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'n',l:'AFP cases',n:1,tt:'2026 AFP cases (onset to '+esc(AFPD.onset||'')+')'},
  {k:'sa',l:'Stool adequacy',n:1,f:x=>cell(x.sa,90,80),tt:'Two adequate stools per case \u00b7 target \u2265 90%'},
  {k:'n7p',l:'Notified < 7d',n:1,f:x=>cell(x.n7p,80,60),tt:'Onset to notification \u00b7 target \u2265 80%'},
  {k:'i48p',l:'Inv. < 48 h',n:1,f:x=>cell(x.i48p,80,60),tt:'Notification to investigation (WHO) \u00b7 target \u2265 80%'},
  {k:'zd',l:'Zero-dose',n:1,f:x=>x.zd?'<b style="color:#b91c1c">'+x.zd+'</b>':'0',tt:'AFP cases with no OPV dose'}],
  rows,'n',-1);
 el('capAFPD').textContent='District detail, 2026 year-to-date, sorted by case count. Colour bands: green \u2265 target, amber near, red below (adequacy 90/80%, timeliness 80/60%). Investigation within 48 h is measured from notification. Aggregates only \u2014 no names, addresses or case identifiers. Source: EOC master databases AFP.DBF + AFPLAB.DBF (exported 21-Oct-2026).';
 el('btnAFPD').onclick=()=>csvDownload('AFP_case_lab_database_'+_slug()+'.csv',['District','AFP cases 2026','Stool adequate','Stool adequacy %','Notified <7d','Notified <7d %','Investigated <48h','Investigated <48h %','Zero-dose AFP'],rows.map(x=>[x.dn,x.n,x.ad,p1(x.sa),x.n7,p1(x.n7p),x.i48,p1(x.i48p),x.zd]));
}
""".replace('\n', '\r\n')

A_CONST = 'const SURVW = '
A_CARD = '<div class="cap" id="capwpvM"></div>\r\n</div>'
A_FUNC = 'function renderSurv(){'
A_CALL = ' renderSurvW();\r\n}'


def patch(v):
    t = v.text
    for a in (A_CONST, A_CARD, A_FUNC, A_CALL):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1): %r' % (t.count(a), a[:48]))
    t = t.replace(A_CONST, 'const AFPD = {};\r\n' + A_CONST)
    t = t.replace(A_CARD, A_CARD + '\r\n' + HTML)
    t = t.replace(A_FUNC, JS + '\r\n' + A_FUNC)
    t = t.replace(A_CALL, ' renderSurvW();\r\n renderSurDB();\r\n}')
    v.text = t
    v.changes.append('AFPD card + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for needle in ('const AFPD = {};', 'id="kAFPD"', 'id="afpdM"', 'id="afpdL"',
                   'id="tAFPDb"', 'function renderSurDB(){', 'renderSurDB();'):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))


def main():
    cfg, vs = dashpatch.load_variants()
    for v in vs:
        if 'const AFPD = ' in v.text:
            raise SystemExit('%s already has an AFPD const - not patching twice' % v.rel)
        patch(v)
    dashpatch.check_identical(cfg, vs)
    dashpatch.write_variants(vs)
    for v in vs:
        print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK afpd-ui %d variants' % len(vs))


if __name__ == '__main__':
    main()
