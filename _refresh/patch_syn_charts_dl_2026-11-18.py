"""Zero-dose recorded/covered: chart layout fixes + campaign-wise downloads.

1. .grid2 children get min-width:0. The side-by-side panel's campaign table was
   9,564px of min-content, so the chart column collapsed to 52px and the grid
   ran off the card. The table now scrolls inside its own column.
2. #ad1 gets vertical campaign labels and a taller plot (43 campaigns).
3. The side-by-side chart becomes a horizontal bar chart, capped to the 18
   largest areas and the 8 most recent campaigns with a figure, with the key
   outside the SVG (it was eating the whole 340px plot).
4. ADV Excel/CSV exports carry one row per UC and per district PER CAMPAIGN
   instead of the compiled summary.
5. The side-by-side panel gets a campaign-wise CSV/Excel download.
"""
import sys

P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
s = open(P, encoding='utf-8', newline='').read()

EDITS = []

# ---------- 1. grid columns cannot be squeezed/overrun by a wide table ----------
EDITS.append((
    '.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}\r\n.ch{height:340px}',
    '.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;margin-bottom:16px}\r\n'
    '.grid2>*{min-width:0}\r\n.ch{height:340px}',
    1))

EDITS.append((
    '.synsbs{margin-bottom:12px}',
    '.synsbs{margin-bottom:12px}\r\n.synsbs .grid2{grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr)}',
    1))

# ---------- 2. button titles / hint now describe campaign-wise exports ----------
EDITS.append((
    'title="Compiled UC results and district summary as a formatted Excel workbook - two sheets, frozen header and filters"',
    'title="Campaign-wise UC results and district summary as a formatted Excel workbook - one row per UC and per district per selected campaign, two sheets, frozen header"',
    1))
EDITS.append((
    'title="Compiled UC zero-dose results as CSV at the current campaign and geography scope"',
    'title="Campaign-wise UC zero-dose rows as CSV - one row per UC per selected campaign at the current geography scope"',
    1))
EDITS.append((
    'Excel exports the compiled UC table and district summary as one formatted workbook; CSV exports the same tables at the current campaign and geography scope.',
    'Excel and CSV export campaign-wise rows - one row per UC and per district for every selected campaign, at the current geography scope - so a multi-campaign selection no longer collapses into one compiled row.',
    1))

# ---------- 3. ad1: 43 campaigns need vertical labels and a taller plot ----------
EDITS.append((
    " el('ad1').style.height='380px';\r\n"
    " HC('ad1',{chart:{type:'column',zoomType:'x'},",
    " el('ad1').style.height='520px';\r\n"
    " HC('ad1',{chart:{type:'column',zoomType:'x',height:520},",
    1))
EDITS.append((
    "xAxis:{categories:T.map(x=>x.n),labels:{rotation:-45,style:{fontSize:'9px'}}},",
    "xAxis:{categories:T.map(x=>x.n),labels:{rotation:-90,align:'right',y:-4,style:{fontSize:'9px'}}},",
    1))

# ---------- 4. ADV downloads: one row per UC / district per campaign ----------
OLD_EXPORTS = """ const slug=s=>String(s||'').replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'').toLowerCase();
 const gseg=[fDiv.value,fDist.value,fTeh.value].filter(Boolean).map(slug).join('-');
 const scope=(multi?'compiled-'+sel.length+'-campaigns':slug(cp.n))+(gseg?'-'+gseg:'');
 const UH=['District','Tehsil','UC','UC criteria'].concat(multi?['Campaigns']:[]).concat(['ZD reported','Covered in round','Covered %','Not covered']);
 const DH=['District','Division','Category','Campaigns in selection','ZD reported','Covered in round','Covered %','Not covered'];
 const Urows=()=>R.map(x=>[x.d,x.t,x.u,critLab(x.d,x.u)].concat(multi?[x.n>1?x.n:'']:[]).concat([x.rep,x.cov==null?'':x.cov,x.cov==null?'':(x.rc?Math.round(x.cov/x.rc*1000)/10:''),x.nc==null?'':x.nc]));
 const Drows=()=>Gs.map(x=>[x.d,x.dv,critLab(x.d),multi?x.n:'',x.rep,x.rc?x.cov:'',x.rc?Math.round(x.cov/x.rc*1000)/10:'',x.rc?Math.max(0,x.rc-x.cov):'']);
 el('adXL').onclick=()=>{const u=Urows(),d=Drows();
  xlWrite('advance-'+scope+'.xlsx',[{sheet:'UC zero-dose results',H:UH,rows:u},{sheet:'District summary',H:DH,rows:d}],false)
   .then(()=>toast('Excel downloaded: 2 sheets, '+u.length+' UCs and '+d.length+' districts'))
   .catch(()=>{csvRaw('advance-'+scope+'.csv',UH,u);csvRaw('advance-districts-'+scope+'.csv',DH,d);
    toast('Excel library did not load, so both tables went out as CSV');});};
 el('adCSVc').onclick=()=>csvDownload('advance-'+scope+'.csv',UH,Urows());
 el('adCSV').onclick=()=>csvDownload('advance-'+scope+'.csv',UH,Urows());
 el('adDCSV').onclick=()=>csvDownload('advance-districts-'+scope+'.csv',DH,Drows());"""

NEW_EXPORTS = """ const slug=s=>String(s||'').replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'').toLowerCase();
 const gseg=[fDiv.value,fDist.value,fTeh.value].filter(Boolean).map(slug).join('-');
 const scope=(multi?'by-campaign-'+sel.length+'-campaigns':slug(cp.n))+(gseg?'-'+gseg:'');
 // campaign-wise rows: every selected campaign keeps its own line, never folded into a compiled row
 const cvis=r=>adVis(r)&&(!qq||(r.u+' '+r.t+' '+r.d).toLowerCase().indexOf(qq)>=0);
 const cwPct=(cov,den)=>cov==null?'':(den?Math.round(cov/den*1000)/10:'');
 const cwUc=()=>{const out=[];
  sel.forEach(ci=>{const c=ADV.c[ci];adRows(ci).filter(cvis).forEach(r=>out.push({c:c.n,y:c.y,m:c.m,d:r.d,dv:r.dv,t:r.t,u:r.u,rep:r.rep,cov:r.cov}));});
  return out;};
 const cwD=()=>{const out=[];
  sel.forEach(ci=>{const c=ADV.c[ci],G={};
   adRows(ci).filter(cvis).forEach(r=>{if(!r.rep&&r.cov==null)return;
    const g=G[r.d]||(G[r.d]={dv:r.dv,rep:0,cov:0,rc:0,cn:0});g.rep+=r.rep;if(r.cov!=null){g.cov+=r.cov;g.rc+=r.rep;g.cn=1;}});
   Object.keys(G).sort().forEach(k=>{const g=G[k];out.push({c:c.n,y:c.y,m:c.m,d:k,dv:g.dv,rep:g.rep,cov:g.cn?g.cov:null,rc:g.rc});});});
  return out;};
 const UH=['Campaign','Campaign year','Campaign month','District','Tehsil','UC','UC criteria','ZD reported','Covered in round','Covered %','Not covered'];
 const DH=['Campaign','Campaign year','Campaign month','District','Division','Category','ZD reported','Covered in round','Covered %','Not covered'];
 const Urows=()=>cwUc().map(x=>[x.c,x.y,x.m,x.d,x.t,x.u,critLab(x.d,x.u),x.rep,x.cov==null?'':x.cov,cwPct(x.cov,x.rep),x.cov==null?'':Math.max(0,x.rep-x.cov)]);
 const Drows=()=>cwD().map(x=>[x.c,x.y,x.m,x.d,x.dv,critLab(x.d,''),x.rep,x.cov==null?'':x.cov,cwPct(x.cov,x.rc),x.cov==null?'':Math.max(0,x.rc-x.cov)]);
 el('adXL').onclick=()=>{const u=Urows(),d=Drows();
  xlWrite('advance-'+scope+'.xlsx',[{sheet:'UC zero-dose results',H:UH,rows:u},{sheet:'District summary',H:DH,rows:d}],false)
   .then(()=>toast('Excel downloaded: '+fmt(u.length)+' campaign-wise UC rows and '+fmt(d.length)+' district rows'))
   .catch(()=>{csvRaw('advance-'+scope+'.csv',UH,u);csvRaw('advance-districts-'+scope+'.csv',DH,d);
    toast('Excel library did not load, so both tables went out as CSV');});};
 el('adCSVc').onclick=()=>csvDownload('advance-'+scope+'.csv',UH,Urows());
 el('adCSV').onclick=()=>csvDownload('advance-'+scope+'-uc.csv',UH,Urows());
 el('adDCSV').onclick=()=>csvDownload('advance-districts-'+scope+'.csv',DH,Drows());"""
EDITS.append((OLD_EXPORTS, NEW_EXPORTS, 1))


# the stray second adCSV handler (wrong denominator) goes with the rewrite
EDITS.append((
    """ el('adCSV').onclick=()=>csvDownload('advance-'+(multi?'compiled-'+sel.length+'-campaigns':cp.n.replace(/[^A-Za-z0-9]+/g,'-').toLowerCase())+'.csv',['District','Tehsil','UC','UC criteria'].concat(multi?['Campaigns']:[]).concat(['ZD reported','Covered in round','Covered %','Not covered']),R.map(x=>[x.d,x.t,x.u,critLab(x.d,x.u)].concat(multi?[x.n>1?x.n:'']:[]).concat([x.rep,x.cov==null?'':x.cov,x.cov==null?'':(x.rep?Math.round(x.cov/x.rep*1000)/10:''),x.nc==null?'':x.nc])));\r\n""",
    '',
    1))

# captions: say what the downloads now carry
EDITS.append((
    'Covered % and Not covered count only the UCs that carry a covered figure, so they do not add up against ZD reported.',
    'Covered % and Not covered count only the UCs that carry a covered figure, so they do not add up against ZD reported. The Excel and CSV downloads carry one row per district per selected campaign, not this compiled row.',
    1))
EDITS.append((
    "Campaigns before 2022 are on the Campaign history tab.';",
    "Campaigns before 2022 are on the Campaign history tab. Every download is campaign-wise: one row per UC (Excel and CSV) and per district (Excel) for each selected campaign.';",
    1))

# ---------- 5. side-by-side chart + campaign-wise download ----------
EDITS.append((
    "function sbsRender(pane,g){",
    "const SBSCOL=['#0e7490','#7c3aed','#ea580c','#15803d','#be123c','#2563eb','#b45309','#0f766e'];\r\n"
    "function sbsExport(box,k){\r\n"
    " const st=box&&box._sbs; if(!st){toast('Table not ready');return;}\r\n"
    " const S=st.S,rows=[];\r\n"
    " st.areas.forEach(a=>S.D.forEach(x=>{const c=S.acc[a][x.k];if(!c)return;const p=st.pc(c);rows.push([S.ll,a,x.l,c.rep,c.uk?'':c.num,p==null?'':+p.toFixed(1)]);}));\r\n"
    " S.D.forEach(x=>{const t=st.tot[x.k],p=st.pc(t);rows.push([S.ll,'Total \\u2014 every area listed',x.l,t.rep,t.uk?'':t.num,p==null?'':+p.toFixed(1)]);});\r\n"
    " const H=['Level','Area','Campaign',S.m[0],S.m[1],S.m[2]];\r\n"
    " const fn='KP_'+slug(pageTitle())+'_campaigns_by_'+slug(S.ll)+'_'+stamp();\r\n"
    " if(k==='csv'){const q_=v=>'\"'+String(v==null?'':v).replace(/\"/g,'\"\"')+'\"';\r\n"
    "  const L=[H.map(q_).join(',')];rows.forEach(r=>L.push(r.map(q_).join(',')));\r\n"
    "  dlBlob(new Blob(['\\ufeff'+L.join('\\r\\n')],{type:'text/csv;charset=utf-8'}),fn+'.csv');\r\n"
    "  toast('CSV downloaded ('+fmt(rows.length)+' campaign-wise rows)');return;}\r\n"
    " xlWrite(fn+'.xlsx',[{sheet:'By campaign',H,rows},{sheet:'Filters',H:['Item','Value'],rows:synMeta('Selected campaigns side by side')}],false)\r\n"
    "  .then(()=>toast('Excel downloaded ('+fmt(rows.length)+' campaign-wise rows)'))\r\n"
    "  .catch(()=>{toast('Excel library did not load, so the table went out as CSV');sbsExport(box,'csv');});\r\n"
    "}\r\n"
    "function sbsRender(pane,g){",
    1))

EDITS.append((
    "<div class=\"tblhdr\"><h3 style=\"margin:0\" class=\"synsbsh\"></h3><span class=\"cnt synsbsc\"></span></div>",
    "<div class=\"tblhdr\"><h3 style=\"margin:0\" class=\"synsbsh\"></h3><span style=\"display:flex;gap:12px;align-items:center;flex-wrap:wrap\"><span class=\"cnt synsbsc\"></span><span class=\"syndl synsbsdl\" style=\"margin:0\"><span>Download table:</span><button type=\"button\" data-k=\"csv\">CSV</button><button type=\"button\" data-k=\"xlsx\">Excel</button></span></span></div>",
    1))

EDITS.append((
    "  if(g==='hz')pane.appendChild(box); else pane.querySelector(':scope > .syncp').insertAdjacentElement('afterend',box);}",
    "  if(g==='hz')pane.appendChild(box); else pane.querySelector(':scope > .syncp').insertAdjacentElement('afterend',box);\r\n"
    "  box.querySelector('.synsbsdl').onclick=e=>{const b=e.target.closest('button');if(b)sbsExport(box,b.dataset.k);};}",
    1))

# remember the rendered matrix for the export
EDITS.append((
    " S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0,uk:false,ukN:0};areas.forEach(a=>{const c=S.acc[a][x.k];if(c){t.rep+=c.rep;t.num+=c.num;if(c.uk){t.uk=true;t.ukN++;}}});});",
    " S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0,uk:false,ukN:0};areas.forEach(a=>{const c=S.acc[a][x.k];if(c){t.rep+=c.rep;t.num+=c.num;if(c.uk){t.uk=true;t.ukN++;}}});});\r\n"
    " box._sbs={S,areas,tot,pc};",
    1))

OLD_CHART = """ const rep=a=>S.D.reduce((s,x)=>s+((S.acc[a][x.k]||{}).rep||0),0);
 const ca=areas.length>40?areas.slice().sort((a,b)=>rep(b)-rep(a)).slice(0,40):areas;
 Highcharts.chart(box.querySelector('#sbsCh_'+TAB),{chart:{type:'column'},title:{text:(recOnly?'Recorded zero dose by ':'Covered share by ')+S.ll.toLowerCase()+' and campaign'},
  subtitle:{text:'One bar per selected campaign'+(areas.length>40?' \\u00b7 40 largest of '+fmt(areas.length)+' shown':'')+(seriesD.length<S.D.length?' \\u00b7 coverage not yet reported for '+S.D.filter(x=>seriesD.indexOf(x)<0).map(x=>x.l).join(', '):'')},
  xAxis:{categories:ca,labels:{rotation:ca.length>8?-45:0}},yAxis:{title:{text:recOnly?'Recorded children':S.m[2]+' (%)'},min:0},
  tooltip:{shared:true,valueDecimals:1,valueSuffix:recOnly?'':'%'},plotOptions:{column:{borderRadius:2}},
  series:seriesD.map(x=>({name:x.l,data:ca.map(a=>{const c=S.acc[a][x.k];if(!c)return null;const v=recOnly?c.rep:pc(c);return v==null?null:+v.toFixed(recOnly?0:1);})}))});"""

NEW_CHART = """ const rep=a=>S.D.reduce((s,x)=>s+((S.acc[a][x.k]||{}).rep||0),0);
 // the panel has to stay readable with all 43 rounds selected: cap the chart (not the table) and
 // keep the colour key outside the SVG, where it cannot eat the plot
 const caMax=areas.slice().sort((a,b)=>rep(b)-rep(a)).slice(0,18).reverse();
 const sMax=seriesD.slice(0,8), h3=Math.max(360,caMax.length*22+150);
 el('sbsCh_'+TAB).style.height=h3+'px';
 HC('sbsCh_'+TAB,{chart:{type:'bar',height:h3},title:{text:(recOnly?'Recorded zero dose by ':'Covered share by ')+S.ll.toLowerCase()+' and campaign'},
  subtitle:{text:'One bar per selected campaign'+(areas.length>caMax.length?' \\u00b7 '+caMax.length+' largest of '+fmt(areas.length)+' '+S.ll.toLowerCase()+(areas.length===1?'':'s')+' shown, full list in the table':'')+(seriesD.length>sMax.length?' \\u00b7 '+sMax.length+' most recent of '+seriesD.length+' campaigns with a figure':'')+(seriesD.length<S.D.length?' \\u00b7 no figure yet for '+S.D.filter(x=>seriesD.indexOf(x)<0).map(x=>x.l).join(', '):'')},
  xAxis:{title:{text:recOnly?'Recorded children':S.m[2]+' (%)'},min:0},yAxis:{categories:caMax,labels:{style:{fontSize:'10px'}}},
  tooltip:{shared:true,valueDecimals:1,valueSuffix:recOnly?'':'%'},plotOptions:{bar:{borderRadius:2}},legend:{enabled:false},
  series:sMax.map((x,i)=>({name:x.l,color:SBSCOL[i%SBSCOL.length],data:caMax.map(a=>{const c=S.acc[a][x.k];if(!c)return null;const v=recOnly?c.rep:pc(c);return v==null?null:+v.toFixed(recOnly?0:1);})}))});
 CKEY('sbsCh_'+TAB,sMax.map((x,i)=>[SBSCOL[i%SBSCOL.length],x.l]));"""
EDITS.append((OLD_CHART, NEW_CHART, 1))


# the auto matrix download is replaced by the campaign-wise export in the panel header
EDITS.append((
    "function addTblDl(tb){\r\n if(tb.closest('.synms'))return;",
    "function addTblDl(tb){\r\n if(tb.closest('.synms,.synsbs'))return;",
    1))

CRLF=chr(13)+chr(10); LF=chr(10)
for old, new, n in EDITS:
    if CRLF not in old and LF in old:
        old=old.replace(LF,CRLF); new=new.replace(LF,CRLF)
    got = s.count(old)
    if got != n:
        sys.exit('expected %d of %r, found %d' % (n, old[:90], got))
    s = s.replace(old, new)

assert CRLF in s
open(P, 'w', encoding='utf-8', newline='').write(s)
print('patched %d fragments' % len(EDITS))
