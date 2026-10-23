"""Insert the surveillance-operations block (SOPS) into the index.html master.

Adds, in the master:
  1. `const SOPS = {};` placeholder before `const SURVW = ` (refresh.py run
     swaps in the real payload afterwards).
  2. A block after the AFPD cards on the surveillance tab: KPI strip, four
     charts (district active visits, weekly active visits, zero-report
     timeliness by month, pendency by snapshot) and the district table with a
     CSV download.
  3. The `renderSOPS()` renderer before `function renderSurv(){`, called at the
     end of `renderSur()` after `renderSurDB();`.

Only the master is written. preview.html, public/index.html and the internal
build carry the same UI through `_refresh/push_master.py`, which is the
owner-approved route for propagating a hand-edited master and is run together
with publishing, not before it.

Every figure keeps its own denominator: the IDIMS zero-report export and the
weekly surveillance log measure timeliness differently, so both are named in
their own captions and never blended.

All inserted text uses CRLF so the file's line endings stay uniform.
Every anchor is asserted to occur exactly once before editing; nothing is
written unless the patch applies cleanly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

HTML = (
 '<div class="card">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Surveillance operations \u2014 active visits, zero reporting, pendency</h3>'
 '<div style="display:flex;gap:10px;align-items:center"><span class="cnt" id="cntSO"></span>'
 '<button class="btn" id="btnSO">Download (CSV)</button></div></div>\r\n'
 '<div class="kpis" id="kSO"></div>\r\n'
 '</div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="so1" class="ch" style="height:340px"></div><div class="cap" id="capso1"></div></div>\r\n'
 '<div class="card"><div id="so2" class="ch" style="height:340px"></div><div class="cap" id="capso2"></div></div>\r\n'
 '</div>\r\n'
 '<div class="grid2">\r\n'
 '<div class="card"><div id="so3" class="ch" style="height:320px"></div><div class="cap" id="capso3"></div></div>\r\n'
 '<div class="card"><div id="so4" class="ch" style="height:320px"></div><div class="cap" id="capso4"></div></div>\r\n'
 '</div>\r\n'
 '<div class="card">\r\n'
 '<div class="scroll"><table id="tSOb"></table></div>\r\n'
 '<div class="cap" id="capSO"></div>\r\n'
 '</div>\r\n'
)

JS = r"""
function renderSOPS(){
 if(typeof SOPS==='undefined'||!SOPS||!SOPS.av||!SOPS.zr||!SOPS.pn||!SOPS.last||!SOPS.vp)return;
 const dnm=k=>(typeof DNAME==='function'?DNAME(k):k);
 const MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 const p1=v=>v==null?'\u2013':(Math.round(v*10)/10).toFixed(1);
 const rt=(a,b)=>(a==null||!b)?null:100.0*a/b;
 const band=(v,hi,lo)=>v==null?C.none:v>=hi?C.high:v>=lo?C.mod:C.crit;
 const cc=(v,hi,lo)=>v==null?'\u2013':'<span style="color:'+(v>=hi?'#047857':v>=lo?'#92400E':'#991B1B')+';font-weight:600">'+p1(v)+'</span>';
 const s2=a=>{const s=[0,0];a.forEach(p=>{if(p){s[0]+=(+p[0]||0);s[1]+=(+p[1]||0);}});return s;};
 const s3=a=>{const s=[0,0,0];a.forEach(p=>{if(p)for(let i=0;i<3;i++)s[i]+=(+p[i]||0);});return s;};
 const ds=Object.keys(SOPS.av.tp).filter(k=>(!fDiv.value||D2DV[k]===fDiv.value)&&dOK(k));
 const whole=!fDiv.value&&!fDist.value&&!DSEL;
 const scName=DSEL?'selected districts':fDist.value?DNAME(fDist.value):fDiv.value?fDiv.value:'KP (whole province)';
 const NKW=SOPS.av.w.length||41;
 const AV=s2(ds.map(k=>SOPS.av.tp[k].al)),VW=s2(ds.map(k=>SOPS.av.tp[k].we)),
       VN=s2(ds.map(k=>SOPS.av.tp[k].fn)),VM=s2(ds.map(k=>SOPS.av.tp[k].mn));
 const ZR=s3(ds.map(k=>SOPS.zr.tot[k])),SITE=ds.reduce((a,k)=>a+(SOPS.zr.sites[k]||0),0);
 const ST=s2(ds.map(k=>SOPS.last.stool.d[k])),CD=s2(ds.map(k=>SOPS.last.case.d[k])),
       GL=s2(ds.map(k=>SOPS.last.geo.d[k]));
 const VP=s3(ds.map(k=>SOPS.vp.tot[k]));
 const avp=rt(AV[1],AV[0]),zrp=rt(ZR[2],ZR[0]),zrr=rt(ZR[1],ZR[0]),
       stp=rt(ST[1],ST[0]),cdp=rt(CD[1],CD[0]),glp=rt(GL[1],GL[0]);
 el('cntSO').textContent=ds.length+' districts \u00b7 visits and zero reports 2026 weeks 1\u2013'+NKW+
  ' \u00b7 pendency as at '+(SOPS.asof||'')+(whole?'':' \u00b7 scoped to '+scName);
 const kpi=(l,v,s,col)=>'<div class="card"><div class="kl">'+l+'</div><div class="kv"'+(col?' style="color:'+col+'"':'')+'>'+v+'</div><div class="ks">'+s+'</div></div>';
 el('kSO').innerHTML=[
  kpi('Active visits done',p1(avp)+'%',fmt(AV[1])+' of '+fmt(AV[0])+' expected \u00b7 target \u2265 90%',band(avp,90,80)),
  kpi('Zero reports in time',p1(zrp)+'%',fmt(ZR[2])+' of '+fmt(ZR[0])+' site-weeks on time \u00b7 IDIMS',band(zrp,90,80)),
  kpi('Stool received',p1(stp)+'%',fmt(ST[1])+' of '+fmt(ST[0])+' AFP line-list cases \u00b7 to '+(SOPS.last.stool.at||''),band(stp,90,80)),
  kpi('Case documentation',p1(cdp)+'%',fmt(CD[1])+' of '+fmt(CD[0])+' AFP cases with records received','#b91c1c'),
  kpi('Case geolocation',p1(glp)+'%',fmt(GL[1])+' of '+fmt(GL[0])+' AFP cases located',band(glp,90,80)),
  kpi('VPD cases reported',fmt(VP[0]),'AFP reports \u00b7 '+fmt(VP[1])+' measles-rubella + '+fmt(VP[2])+' NNT in weeks 1\u2013'+NKW)
 ].join('');
 // so1 - district completion of expected active visits
 const r1=ds.map(k=>{const a=SOPS.av.tp[k];return{k, dn:dnm(k), e:a.al[0], d:a.al[1], v:rt(a.al[1],a.al[0])};});
 r1.sort((a,b)=>(a.v==null)-(b.v==null)||a.v-b.v);
 HC('so1',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Active visits completed by district \u00b7 '+scName+' \u00b7 2026 weeks 1\u2013'+NKW,style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:r1.map(x=>x.dn),labels:{rotation:-38,align:'right',style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'% of expected visits done'},min:0,max:100,
   plotLines:[{value:90,color:C.mut,dashStyle:'Dash',width:2,zIndex:5,label:{text:'90%',style:{color:C.mut,fontSize:'10px'}}}]},
  legend:{enabled:false},tooltip:{useHTML:true,formatter:function(){const x=r1[this.point.index];
   return '<b>'+esc(x.dn)+'</b><br>Completed <b>'+p1(x.v)+'%</b> of expected visits<br>'+fmt(x.d)+' done of '+fmt(x.e)+' expected';}},
  plotOptions:{column:{borderRadius:2,pointPadding:0.12}},
  series:[{name:'Active visits done %',data:r1.map(x=>({y:x.v==null?null:+x.v.toFixed(1),color:band(x.v,90,80)}))}]});
 CKEY('so1',[[C.high,'\u2265 90% of expected visits done'],[C.mod,'80\u201390%'],[C.crit,'under 80%'],[C.mut,'dashed line = 90% target','line']]);
 const ok1=r1.filter(x=>x.v!=null);
 el('capso1').textContent=fmt(AV[1])+' of '+fmt(AV[0])+' expected active visits completed in '+ds.length+
  ' districts = '+p1(avp)+'% (weekly, fortnightly and monthly visit frequencies combined). '+
  (ok1.length?ok1[0].dn+' trails at '+p1(ok1[0].v)+'% and '+ok1[ok1.length-1].dn+' leads at '+p1(ok1[ok1.length-1].v)+'%. ':'')+
  (whole?'The '+SURVW.asof+' weekly surveillance log reports '+p1(SVLOG('as'))+'% for the same activity on its own denominator \u2014 close, but not the same count. ':'')+
  'District selection narrows this chart; the year / month filter does not, because this export publishes 2026 weeks only.';
 // so2 - weekly active-visit series, province level only
 const WE=SOPS.av.wk.map(p=>p[0]),WD=SOPS.av.wk.map(p=>p[1]);
 HC('so2',{chart:{type:'column'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Weekly-frequency sites: visits expected vs done \u00b7 whole province',style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:SOPS.av.w.map(w=>'W'+w),labels:{rotation:-38,style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'Visits'},allowDecimals:false},
  legend:{enabled:false},tooltip:{shared:true},
  plotOptions:{column:{borderRadius:1,dataLabels:{enabled:false}}},
  series:[{name:'Expected',color:'#94a3b8',data:WE},{name:'Done',color:'#1F497D',data:WD}]});
 CKEY('so2',[['#94a3b8','Visits expected in the week'],['#1F497D','Visits actually done']]);
 el('capso2').textContent='One bar pair per reporting week, whole province \u2014 the active-visit workbook publishes the weekly and fortnightly series only at province level, so this chart does not follow the district filter. '+
  fmt(VW[1])+' of '+fmt(VW[0])+' weekly-site visits done = '+p1(rt(VW[1],VW[0]))+'%, '+
  fmt(VN[1])+' of '+fmt(VN[0])+' fortnightly = '+p1(rt(VN[1],VN[0]))+'% over '+SOPS.av.fwk.length+' fortnights, '+
  fmt(VM[1])+' of '+fmt(VM[0])+' monthly-site = '+p1(rt(VM[1],VM[0]))+'% (monthly sites are the only frequency with district and month detail \u2014 see the table). '+
  'The three streams are different facility groups, so only the combined total in the district chart and KPI strip is a province figure.';
 // so3 - zero-report completeness and timeliness by month
 const zt=[0,1,2].map(j=>{const s=new Array(12).fill(0);ds.forEach(k=>SOPS.zr.mon[k].forEach((p,i)=>{s[i]+=(p[j]||0);}));return s;});
 let eM=11;
 while(eM>0&&!zt[0][eM])eM--;
 const mPct=(j)=>zt[0].slice(0,eM+1).map((v,i)=>v?+(100*zt[j][i]/v).toFixed(1):null);
 const rec=mPct(1),tim=mPct(2),zv=rec.concat(tim).filter(v=>v!=null);
 const zlo=zv.length?Math.min.apply(null,zv):0,zhi=zv.length?Math.max.apply(null,zv):100;
 HC('so3',{chart:{type:'line'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'Zero-report completeness and timeliness by month \u00b7 '+scName,style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:MO.slice(0,eM+1)},
  yAxis:{title:{text:'% of expected reports'},min:Math.min(88,Math.floor(zlo/5)*5),max:Math.ceil(zhi/5)*5,
   plotLines:[{value:90,color:C.mut,dashStyle:'Dash',width:2,zIndex:5,label:{text:'90%',style:{color:C.mut,fontSize:'10px'}}}]},
  legend:{enabled:false},tooltip:{shared:true},
  plotOptions:{line:{marker:{enabled:true,symbolSize:7},dataLabels:{...dl,format:'{y:.1f}%'}}},
  series:[{name:'Received',color:'#15803d',data:rec},{name:'In time',color:'#1F497D',data:tim}]});
 CKEY('so3',[['#15803d','Reports received, % of expected'],['#1F497D','Received within the deadline, % of expected'],[C.mut,'dashed line = 90% target','line']]);
 el('capso3').textContent=fmt(SITE)+' surveillance sites expected to report every week across '+ds.length+' districts. '+
  fmt(ZR[1])+' of '+fmt(ZR[0])+' weekly reports arrived = '+p1(zrr)+'%, of which '+fmt(ZR[2])+' ('+p1(zrp)+'%) arrived on time. '+
  (whole?'IDIMS counts site-weeks; the '+SURVW.asof+' weekly surveillance log scores timeliness as '+p1(SVLOG('zr'))+'% on a different denominator, so the two are shown side by side and never blended. ':'')+
  'Oct is partial (weeks to '+SOPS.asof+'). Received can exceed expected where a site reports more than once in a week.';
 // so4 - pendency rate per tracker snapshot (province level)
 const mk=st=>{const o={},s=SOPS.pn[st];(s.at||[]).forEach((a,i)=>{const c=s.d[i]||[0,0];o[a]=[c[0],c[1]];});return o;};
 const PA={stool:mk('stool'),case:mk('case'),geo:mk('geo')};
 const cmn=(SOPS.pn.stool.at||[]).filter(a=>PA.case[a]&&PA.geo[a]).slice().sort();
 const mlab=a=>a?MO[+a.slice(5,7)-1]+'\u2019'+a.slice(2,4):'';
 const pr=(st,a)=>{const p=PA[st][a];return (p&&p[0])?+(100*p[1]/p[0]).toFixed(1):null;};
 HC('so4',{chart:{type:'line'},title:{text:null},style:{fontSize:'12px'},
  subtitle:{text:'AFP pendency: monthly tracker snapshots, whole province',style:{color:'#475569',fontSize:'12.5px'}},
  xAxis:{categories:cmn.map(mlab),labels:{rotation:-38,style:{color:'#1f2937',fontSize:'9.5px'}}},
  yAxis:{title:{text:'% of the AFP line list cleared'},min:0,max:100},
  legend:{enabled:false},tooltip:{shared:true},
  plotOptions:{line:{marker:{enabled:true,symbolSize:5}}},
  series:[{name:'Stool received',color:'#1F497D',data:cmn.map(a=>pr('stool',a))},
          {name:'Case documentation',color:'#b91c1c',data:cmn.map(a=>pr('case',a))},
          {name:'Geolocation',color:'#15803d',data:cmn.map(a=>pr('geo',a))}]});
 CKEY('so4',[['#1F497D','Stool specimen received'],['#b91c1c','Case documentation received'],['#15803d','Case geolocation recorded']]);
 const ye=st=>Object.keys(SOPS.pn[st].yend||{}).sort().map(y=>{const v=SOPS.pn[st].yend[y];return y+' '+p1(rt(v[1][1],v[1][0]))+'%';}).join(', ');
 el('capso4').textContent='One point per tracker snapshot, whole province \u2014 the pendency workbook holds district detail only for the latest snapshot ('+SOPS.asof+'), so this chart is not district-filtered. '+
  'Year-end stool collection: '+ye('stool')+'. Case documentation at each year-end: '+ye('case')+'. Geolocation: '+ye('geo')+'. '+
  'Snapshots before '+mlab(SOPS.pn.stool.at[0])+' are left out: in the older blocks the tracker carries the previous year\u2019s tally or a gap count where a rate should be, so those months cannot be read as coverage.';
 // district table
 const rows=ds.map(k=>{const tp=SOPS.av.tp[k],z=SOPS.zr.tot[k]||[0,0,0],
   st=SOPS.last.stool.d[k]||[0,0],cd=SOPS.last.case.d[k]||[0,0],gl=SOPS.last.geo.d[k]||[0,0],vp=SOPS.vp.tot[k]||[0,0,0];
  return{k, dn:dnm(k), e:tp.al[0], d:tp.al[1], avp:rt(tp.al[1],tp.al[0]), mp:rt(tp.mn[1],tp.mn[0]),
   sit:SOPS.zr.sites[k]||0, zrp:rt(z[2],z[0]),
   stc:st[0], stp:rt(st[1],st[0]), cdp:rt(cd[1],cd[0]), glp:rt(gl[1],gl[0]),
   vaf:vp[0], vme:vp[1], vn:vp[2]};});
 drawTable('tSOb',[
  {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
  {k:'avp',l:'Active visits done %',n:1,f:x=>cc(x.avp,90,80),tt:'Completed / expected active visits, all frequencies, 2026 weeks 1\u2013'+NKW+' \u00b7 target \u2265 90%'},
  {k:'d',l:'Visits done',n:1,tt:'Completed active visits'},
  {k:'e',l:'Visits expected',n:1,tt:'Expected active visits'},
  {k:'sit',l:'Reporting sites',n:1,tt:'Sites that must send a weekly zero-report'},
  {k:'zrp',l:'Zero reports in time %',n:1,f:x=>cc(x.zrp,90,80),tt:'IDIMS: reports received within the deadline / expected site-weeks'},
  {k:'stc',l:'AFP cases (line list)',n:1,tt:'2026 AFP line-list cases in the pendency tracker, to '+SOPS.asof},
  {k:'stp',l:'Stool received %',n:1,f:x=>cc(x.stp,90,80),tt:'AFP cases with a stool specimen received, to '+SOPS.asof},
  {k:'cdp',l:'Case docs %',n:1,f:x=>cc(x.cdp,90,80),tt:'AFP cases with the case documentation received, to '+SOPS.asof},
  {k:'glp',l:'Geolocation %',n:1,f:x=>cc(x.glp,90,80),tt:'AFP cases with the location recorded, to '+SOPS.asof},
  {k:'vaf',l:'VPD AFP reports',n:1,tt:'AFP cases reported through weekly VPD reporting, weeks 1\u2013'+NKW+' \u00b7 a different denominator from the line list'},
  {k:'vme',l:'MR reports',n:1,tt:'Measles-rubella cases reported weekly, weeks 1\u2013'+NKW},
  {k:'vn',l:'NNT reports',n:1,tt:'Non-tetanus neonatal tetanus reports, weeks 1\u2013'+NKW}],
  rows,'avp',1);
 el('capSO').textContent='Sorted by the active-visit completion rate, weakest first. Every column keeps its own source and denominator: the active-visit workbook, the IDIMS zero-report export, the pendency tracker (latest snapshot '+SOPS.asof+') and the VPD weekly case counts (weeks 1\u2013'+NKW+') are four different exports and are never added together \u2014 VPD AFP reports and line-list AFP cases do not have to match. Colour bands: green \u2265 90%, amber 80\u201390%, red under 80%. Aggregates only \u2014 no names, addresses or case identifiers. Sources: '+esc(SOPS.src.av)+', '+esc(SOPS.src.zr)+', '+esc(SOPS.src.pn)+', '+esc(SOPS.src.vp)+'.';
 el('btnSO').onclick=()=>csvDownload('surveillance_operations_'+_slug()+'.csv',
  ['District','Active visits expected','Active visits done','Active visits done %','Monthly-site visits %','Reporting sites','Zero reports in time %','AFP line-list cases','Stool received %','Case documentation %','Geolocation %','VPD AFP reports','VPD measles-rubella reports','VPD NNT reports'],
  rows.map(x=>[x.dn,x.e,x.d,x.avp==null?'':p1(x.avp),x.mp==null?'':p1(x.mp),x.sit,x.zrp==null?'':p1(x.zrp),x.stc,p1(x.stp),p1(x.cdp),p1(x.glp),x.vaf,x.vme,x.vn]));
}
function SVLOG(key){
 if(typeof SURVW==='undefined'||!SURVW.sm||!SURVW.sm.k)return null;
 const i=SURVW.sm.k.indexOf(key);
 return i<0?null:SURVW.sm.kp[i];
}
""".replace('\n', '\r\n')

MASTER = 'index.html'
A_CONST = 'const SURVW = '
A_CARD = '<div class="cap" id="capAFPD"></div>\r\n</div>\r\n'
A_FUNC = 'function renderSurv(){'
A_CALL = ' renderSurvW();renderSurDB();\r\n}'


def patch(v):
    t = v.text
    for a in (A_CONST, A_CARD, A_FUNC, A_CALL):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1): %r' % (t.count(a), a[:48]))
    t = t.replace(A_CONST, 'const SOPS = {};\r\n' + A_CONST)
    t = t.replace(A_CARD, A_CARD + '\r\n' + HTML)
    t = t.replace(A_FUNC, JS + '\r\n' + A_FUNC)
    t = t.replace(A_CALL, ' renderSurvW();renderSurDB();\r\n renderSOPS();\r\n}')
    v.text = t
    v.changes.append('SOPS block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for needle in ('const SOPS = {};', 'id="kSO"', 'id="so1"', 'id="so2"', 'id="so3"', 'id="so4"',
                   'id="tSOb"', 'function renderSOPS(){', 'function SVLOG(', 'renderSOPS();'):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    v.require(t.count("CKEY('so") == 4, 'expected 4 chart colour keys, found %d' % t.count("CKEY('so"))


def main():
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'const SOPS = ' in v.text:
        raise SystemExit('%s already has a SOPS const - not patching twice' % v.rel)
    patch(v)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK sops-ui master only - preview / public / internal builds pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
