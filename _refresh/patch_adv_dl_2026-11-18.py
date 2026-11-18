"""ADV page: coverage-share denominator, chart sizing/selection, Excel+CSV exports."""
import sys

P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
s = open(P, encoding='utf-8', newline='').read()
assert '\r\n' in s
t = s.replace('\r\n', '\n')
assert '\r' not in t

# ---------- HTML ----------
H_EDITS = [
    ('<div class="hmcpop" id="fADCp" hidden></div></div><span class="cnt" id="adNote"></span></div>',
     '<div class="hmcpop" id="fADCp" hidden></div></div>'
     '<span style="display:flex;gap:6px;align-items:center">'
     '<button type="button" class="btn" id="adXL" title="Compiled UC results and district summary as a formatted Excel workbook - two sheets, frozen header and filters">'
     '<span data-ic="download"></span>Excel</button>'
     '<button type="button" class="btn" id="adCSVc" title="Compiled UC zero-dose results as CSV at the current campaign and geography scope">'
     '<span data-ic="download"></span>CSV</button></span>'
     '<span class="cnt" id="adNote"></span></div>', 1),
    ('<button class="btn" id="adCSV">Download CSV</button>',
     '<button class="btn" id="adCSV"><span data-ic="download"></span>Download CSV</button>', 1),
    ('<button class="btn" id="adDCSV">Download CSV</button>',
     '<button class="btn" id="adDCSV"><span data-ic="download"></span>Download CSV</button>', 1),
    ('its covered column stays a dash until a round follows.</div>',
     'its covered column stays a dash until a round follows. Where a selected campaign or UC carries no '
     'covered figure, the covered share and the not-covered count are computed over the UCs that do carry '
     'one, and the captions say how many sit outside. Excel exports the compiled UC table and district '
     'summary as one formatted workbook; CSV exports the same tables at the current campaign and geography scope.</div>', 1),
    ('.tblhdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:12px;flex-wrap:wrap}',
     '.tblhdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;gap:12px;flex-wrap:wrap}\n'
     '.btn [data-ic]{display:inline-flex;margin-right:5px;vertical-align:-2px}.btn [data-ic] svg{width:14px;height:14px}', 1),
]
for old, new, n in H_EDITS:
    got = t.count(old)
    if got != n:
        sys.exit('HTML expected %d of %r, found %d' % (n, old[:80], got))
    t = t.replace(old, new)

# ---------- renderADV body ----------
L = t.split('\n')
f0 = next(i for i, l in enumerate(L) if i > 9000 and l.strip() == 'let R;'
          and L[i - 1].strip().startswith('const cp=ADV.c[sel[0]]'))
f1 = next(i for i, l in enumerate(L) if i > f0 and l.strip().startswith("el('capad3')"))
f2 = f1 + 1
assert L[f2].strip().startswith("el('adCSV').onclick"), L[f2]

BLOCK_A = r""" if(multi){const M={};
  sel.forEach(ci=>ADV.r[ci].forEach(a=>{const u=ADV.u[a[0]];const g=M[a[0]]||(M[a[0]]={dv:ADV.dv[u[0]],d:ADV.ds[u[0]],t:u[1],u:u[2],rep:0,cov:0,rc:0,nc:null,n:0,cn:0});
   g.rep+=a[1];g.n++;if(a[2]!=null){g.cov+=a[2];g.rc+=a[1];g.cn++;}}));
  R=Object.keys(M).map(k=>{const g=M[k];g.nc=g.cn?g.rc-g.cov:null;return g;});
 }else R=adRows(sel[0]).map(r=>({dv:r.dv,d:r.d,t:r.t,u:r.u,rep:r.rep,cov:r.cov,rc:r.cov==null?0:r.rep,nc:r.nc,n:1,cn:r.cov==null?0:1}));
 R=R.filter(r=>adVis(r)&&(!qq||(r.u+' '+r.t+' '+r.d).toLowerCase().indexOf(qq)>=0));
 const covMiss=sel.filter(ci=>!ADV.r[ci].some(x=>x[2]!=null)).length;
 const rep=sum_(R,r=>r.rep),cov=sum_(R,r=>r.cov),rc=sum_(R,r=>r.rc),covK=R.some(r=>r.cn>0);
 el('adk1').textContent=fmt(rep);el('adk1s').textContent=multi?(sel.length+' campaigns compiled'):cp.n;
 el('adk2').textContent=covK?fmt(cov):'\u2013';
 el('adk2s').textContent=covK?(covMiss?('covered in '+(sel.length-covMiss)+' of '+sel.length+' selected campaigns'):'covered during the round'):'covered in round not yet compiled';
 el('adk3').textContent=covK&&rc?pc(cov/rc*100):'\u2013';
 el('adk3s').textContent=covK?'covered \u00f7 reported in the UCs that carry coverage':'no covered figure in the selection';
 el('adk4').textContent=fmt(R.filter(r=>r.rep>0).length);el('adk4s').textContent='of '+fmt(R.length)+' UCs in the report';
 el('adk5').textContent=new Set(R.filter(r=>r.rep>0).map(r=>r.d)).size;el('adk5s').textContent='districts reporting zero-dose children';
 const T=ADV.c.map((c,i)=>{const rows=adRows(i).filter(adVis);const has=rows.some(r=>r.cov!=null);const rp=sum_(rows,r=>r.rep),cv=has?sum_(rows,r=>r.cov):null;return{i,n:c.n,rp,cv,sel:sel.indexOf(i)>=0};});
 el('ad1').style.height='380px';
 HC('ad1',{chart:{type:'column',zoomType:'x'},title:{text:'Zero-dose children reported & covered, '+ADV.c[0].y+' \u2013 '+ADV.c[ADV.c.length-1].y},subtitle:{text:'IDIMS advance reports \u00b7 click a campaign to open it \u00b7 selected campaigns in full colour'+(fDist.value||fDiv.value?' \u00b7 '+(fDist.value||fDiv.value+' division'):'')},
  xAxis:{categories:T.map(x=>x.n),labels:{rotation:-45,style:{fontSize:'9px'}}},
  yAxis:{title:{text:'Children'},allowDecimals:false,min:0},
  tooltip:{shared:true,headerFormatter:function(){const p=this.points&&this.points[0]&&this.points[0].point;return p&&p.full?p.full:(this.x||'');}},
  plotOptions:{series:{point:{events:{click:function(){if(this.ai!=null){ADS=this.ai;ADSM=null;renderADV();}}}}}},
  series:[
   {name:'Reported',color:'#a78bfa',data:T.map(x=>({y:x.rp,ai:x.i,full:x.n,color:x.sel?'#a78bfa':'rgba(167,139,250,.22)'}))},
   {name:'Covered in round',color:'#15803d',data:T.map(x=>({y:x.cv,ai:x.i,full:x.n,color:x.sel?'#15803d':'rgba(21,128,61,.22)'}))}]});
 el('capad1').textContent='Zero-dose children reported per UC and how many of them were vaccinated during the same round. CR, OBR and bordering-UC activities cover only part of the province, so their bars are lower; campaigns outside the current selection are held back in pale colour.';
 const D={};R.forEach(r=>{if(!r.rep&&!r.cov)return;const g=D[r.d]||(D[r.d]={rep:0,cov:0,rc:0});g.rep+=r.rep;g.cov+=r.cov;g.rc+=r.rc;});
 const Dal=Object.keys(D).map(k=>{const g=D[k];return{k,rep:g.rep,cov:g.cov,rc:g.rc,p:g.rc?g.cov/g.rc*100:null};});
 const Ds=covK?Dal.filter(x=>x.rc>0).sort((a,b)=>a.p-b.p):Dal.slice().sort((a,b)=>b.rep-a.rep);
 const dNoCov=covK?Dal.length-Ds.length:0;
 const h2=Math.min(1100,Math.max(340,Ds.length*20+110));
 el('ad2').style.height=h2+'px';
 if(covK){HC('ad2',{chart:{type:'bar',height:h2},title:{text:'Covered share by district \u2014 '+(multi?sel.length+' campaigns compiled':cp.n)},subtitle:{text:'Zero-dose children covered \u00f7 reported in the UCs that carry a covered figure \u00b7 click a district to filter the dashboard to it'},
  xAxis:{categories:Ds.map(x=>x.k),labels:{style:{fontSize:'10px'}}},yAxis:{title:{text:'Percent'},min:0,max:110},
  tooltip:{formatter:function(){return '<b>'+this.point.dn+'</b> '+pc(this.point.p)+' \u00b7 '+fmt(this.point.cv)+' covered of '+fmt(this.point.rp)+' reported'+(this.point.all!==this.point.rp?(' ('+fmt(this.point.all)+' reported across all selected rows)'):'');}},
  plotOptions:{bar:{borderRadius:2,point:{events:{click:function(){fDist.value=this.dn;cascade();render();}}}}},
  legend:{enabled:false},
  series:[{name:'Covered %',data:Ds.map(x=>({y:Math.round(x.p*10)/10,dn:x.k,cv:x.cov,rp:x.rc,all:x.rep,color:x.p>=90?'#15803d':x.p>=80?'#d97706':'#b91c1c'}))}]});
 CKEY('ad2',[['#15803d','90% of reported zero-dose children covered'],['#d97706','80-90%'],['#b91c1c','under 80%']]);
 el('capad2').textContent=Ds.length?('Lowest: '+esc(Ds[0].k)+' '+pc(Ds[0].p)+' \u00b7 highest: '+esc(Ds[Ds.length-1].k)+' '+pc(Ds[Ds.length-1].p)+(multi&&covMiss?(' \u00b7 covered-in-round compiled for '+(sel.length-covMiss)+' of '+sel.length+' selected campaigns'):'')+(dNoCov?(' \u00b7 '+dNoCov+' district'+(dNoCov>1?'s':'')+' carry no covered figure'):'')+'. Share = covered \u00f7 reported in the UCs that carry a covered figure. Green \u2265 90%, amber 80\u201390%, red < 80%.'):'No zero-dose children reported under the current filters.';}
 else{HC('ad2',{chart:{type:'bar',height:h2},title:{text:'Zero-dose children by district \u2014 '+(multi?sel.length+' campaigns compiled':cp.n)+' \u2014 covered not yet reported'},subtitle:{text:'Covered-in-round figures are not in every selected export \u00b7 click a district to filter the dashboard to it'},
  xAxis:{categories:Ds.map(x=>x.k),labels:{style:{fontSize:'10px'}}},yAxis:{title:{text:'Children'},allowDecimals:false,min:0},
  tooltip:{formatter:function(){return '<b>'+this.point.dn+'</b> '+fmt(this.point.rp)+' reported';}},
  plotOptions:{bar:{borderRadius:2,point:{events:{click:function(){fDist.value=this.dn;cascade();render();}}}}},
  legend:{enabled:false},
  series:[{name:'Reported',color:'#a78bfa',data:Ds.map(x=>({y:x.rep,dn:x.k,rp:x.rep}))}]});
 el('capad2').textContent=Ds.length?'Highest: '+esc(Ds[0].k)+' '+fmt(Ds[0].rep)+' \u00b7 lowest: '+esc(Ds[Ds.length-1].k)+' '+fmt(Ds[Ds.length-1].rep)+' reported. Reported only \u2014 the campaigns selected here carry no covered-in-round column, so the covered-share graph appears as soon as a selected campaign carries one.':'No zero-dose children reported under the current filters.';}
 const G={};R.forEach(r=>{const g=G[r.d]||(G[r.d]={dv:r.dv,d:r.d,rep:0,cov:0,rc:0,cn:0,n:0});g.rep+=r.rep;g.cov+=r.cov;g.rc+=r.rc;g.cn+=r.cn;g.n+=r.n;});
 const Gs=Object.values(G).sort((a,b)=>b.rep-a.rep);
 drawTable('tADD',[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},{k:'dv',l:'Division',f:x=>esc(x.dv)},{k:'n',l:'Campaigns',n:1,f:x=>x.n>1?x.n:'\u2013'},{k:'rep',l:'ZD reported',n:1,f:x=>fmt(x.rep)},{k:'cov',l:'Covered in round',n:1,f:x=>x.cn?fmt(x.cov):'\u2013'},{k:'p',l:'Covered %',n:1,f:x=>!x.rc?'\u2013':rgN(x.cov/x.rc*100,90,80)+'%'},{k:'nc',l:'Not covered',n:1,f:x=>x.rc?fmt(Math.max(0,x.rc-x.cov)):'\u2013'}],Gs,'rep',-1);
 el('cntADD').textContent=Gs.length+' districts';
 el('capadD').textContent='District summary compiled from the same campaign selection and Division / District / Tehsil filters as the UC table. Campaigns = how many of the selected campaigns reported zero-dose children in the district; covered-in-round sums only the selected campaigns whose export carries coverage. Covered % and Not covered count only the UCs that carry a covered figure, so they do not add up against ZD reported.';
 const cols=[{k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'},{k:'t',l:'Tehsil',f:x=>esc(x.t)},{k:'u',l:'UC',f:x=>esc(x.u)},critCol(x=>x.d,x=>x.u)];
 if(multi)cols.push({k:'n',l:'Campaigns',n:1,f:x=>x.n>1?x.n:'\u2013'});
 cols.push({k:'rep',l:'ZD reported',n:1,f:x=>fmt(x.rep)},{k:'cov',l:'Covered in round',n:1,f:x=>x.cov==null?'\u2013':fmt(x.cov)},{k:'p',l:'Covered %',n:1,f:x=>x.cov==null?'\u2013':(x.rc?rgN(x.cov/x.rc*100,90,80)+'%':'\u2013')},{k:'nc',l:'Not covered',n:1,f:x=>x.nc==null?'\u2013':fmt(x.nc)});
 drawTable('tADV',cols,R,'rep',-1);
 el('cntADV').textContent=fmt(R.length)+' UCs';
 el('adNote').textContent=ADV.c.length+' campaigns \u00b7 '+ADV.c[0].y+'\u2013'+ADV.c[ADV.c.length-1].y+' \u00b7 export '+ADV.asof;"""

BLOCK_B = r""" const slug=s=>String(s||'').replace(/[^A-Za-z0-9]+/g,'-').replace(/^-+|-+$/g,'').toLowerCase();
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
 el('adDCSV').onclick=()=>csvDownload('advance-districts-'+scope+'.csv',DH,Drows());
 ['adXL','adCSVc','adCSV','adDCSV'].forEach(id=>{const b=el(id);const i=b&&b.querySelector('[data-ic]');if(i&&!i.innerHTML)i.innerHTML=SVGI(ICO.download);});"""

L[f0 + 1:f1] = BLOCK_A.split('\n')
L[f2] = BLOCK_B
t = '\n'.join(L)
out = t.replace('\n', '\r\n')
assert '\r\r' not in out and '\n' not in out.replace('\r\n', '')
open(P, 'w', encoding='utf-8', newline='').write(out)
print('patched ADV page: %d lines in body, %d HTML fragments' % (len(BLOCK_A.split('\n')), len(H_EDITS)))
