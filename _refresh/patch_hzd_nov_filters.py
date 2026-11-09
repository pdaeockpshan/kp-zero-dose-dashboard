# -*- coding: utf-8 -*-
"""Zero Dose overview: show SNID Nov-26 recorded ZD, with campaign + division + district picks.

The overview strip used to hard-code the Sept-26 coverage round, so the round the owner has
just closed (SNID Nov 2026, 42,653 zero-dose children recorded across 996 UCs in 27 districts)
never appeared. This patch:

  * adds Nov-26 (ADV's last round, UC-wise) to the overview strip, the home card and the
    side-by-side panel, with covered left as a dash because the post-campaign return is pending;
  * gives the page its own campaign group ('hz') so picking Nov here cannot blank the zov /
    zcmp / zperf / zins tables that share the 'z' group;
  * adds a page filter row on p-hzd: division and district multi-selects that drive the same
    global geography state as the top bar, so the strip, cards, triangulation table and
    side-by-side panel all agree;
  * keeps Nov out of the coverage chart (no covered figure exists), and charts recorded counts
    instead when a selection has no covered data at all.

Run:  python _refresh/patch_hzd_nov_filters.py [--dry-run]
"""
import sys

import dashpatch


def crlf(t):
    return t.replace('\r\n', '\n').replace('\n', '\r\n')


NEW_STRIP = r"""// ---------- SNID Nov-26 recorded zero dose (ADV last round, UC-wise) ----------
function novCampIdx(){return (typeof ADV!=='undefined'&&ADV&&ADV.c&&ADV.c.length)?ADV.c.length-1:-1;}
function novLabel(){const i=novCampIdx();return i>=0?ADV.c[i].n:'SNID Nov 2026';}
function novRows(){if(novRows._c)return novRows._c;const i=novCampIdx();if(i<0)return [];const out=[],C={};
 const nk=s=>String(s==null?'':s).toUpperCase().replace(/[^A-Z0-9]/g,'');
 ZD.forEach(r=>{C[r.d+'|'+nk(r.u)]=r.c;});
 (ADV.r[i]||[]).forEach(t=>{const u=ADV.u[t[0]];if(!u)return;const d=ADV.ds[u[0]];
  out.push({d,dv:ADV.dv[u[0]],t:u[1],u:u[2],c:C[d+'|'+nk(u[2])],rN:t[1],cN:t[2]});});
 novRows._c=out;return out;}
function novAgg(rows){const w=rows||novRows();let rep=0,cov=0,sC=0,nC=0;const DS=new Set();
 w.forEach(r=>{rep+=r.rN||0;DS.add(r.d);if(r.cN!=null){cov+=r.cN;sC+=r.rN||0;nC++;}});
 return {n:w.length,rep,cov:nC?cov:null,rc:sC,covUc:!!nC,p:sC?cov/sC*100:null,dists:DS.size};}
function novSum(){return novAgg(novRows().filter(matchG));}
function hzCampaign(){const S=SYNCP.hz;if(!S)return 'N';return ['N','S','M','A'].find(k=>S.has(k))||'N';}
function hzdStrip(){const inZ=ZD.filter(matchG), z=agg(inZ), D=DATA.filter(matchG), dr=S_(D,r=>r.rep), dl=S_(D,r=>r.ll), v=aggV(VAL.filter(matchG)), k=hzCampaign();
 const dig=['Digitized in IDIMS',D.length?pc(dr?dl/dr*100:null):'–',D.length?`${fmt(dl)} of ${fmt(dr)} entered · ${fmt(Math.max(0,dr-dl))} not entered`:'no IDIMS data for this area (9 districts only)','#6d28d9'];
 const val=['Validated vaccinated',v.n?pc(v.p):'–',v.n?`${fmt(v.vy)} of ${fmt(v.n)} children checked · ${fmt(v.vn)} not vaccinated`:'no validation records','#15803d'];
 if(k==='N'){const nv=novSum();
  hubStrip('hzd',[['Zero dose reported',fmt(nv.rep),esc(novLabel())+' · '+fmt(nv.n)+' UCs · '+fmt(nv.dists)+' districts'],['ZD children covered','–','post-campaign coverage return awaited','#64748b'],['Not covered','–','follows the coverage return','#64748b'],dig,val],
   'SNID Nov-26 recorded zero dose is the round’s own UC-wise return. Its covered figure, LQAS and validation are the post-campaign returns awaited; SNID Sept-26 remains the last measured coverage.');
  return;}
 const rc=z['rc'+k]||0, cc=z['c'+k]||0;
 hubStrip('hzd',[['Zero dose reported',fmt(z['r'+k]||0),esc(CAMP[k])+' · '+fmt(z['n'+k]||0)+' UCs'],['ZD children covered',pc(z['p'+k]),`${fmt(cc)} of ${fmt(rc)} · ${esc(CAMP[k])}`,'#0f766e'],['Not covered',fmt(Math.max(0,rc-cc)),'zero-dose children still to reach','#b91c1c'],dig,val]);}"""

NEW_HF1 = r""" const nv=novAgg(novRows());
 el('hF1').innerHTML=`<div class="hf"><b>${fmt(nv.rep)}</b>zero-dose children recorded · ${esc(novLabel())} · ${fmt(nv.n)} UCs</div><div class="hf"><b>${fmt(zRep)}</b>reported · ${esc(CAMP[ZSAME?'M':'S'])} · <b>${fmt(z['c'+cK])}</b> covered in the same report (${pc(z['p'+cK])})</div>`;"""

NEW_HZBAR = r"""function hzBar(pane){
 let bar=pane.querySelector(':scope > .hzbar');
 if(!bar){bar=document.createElement('div');bar.className='hzbar';
  const X='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:5px"><circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/></svg>';
  bar.innerHTML='<span class="hzbl">Scope</span><button type="button" class="hmcbtn synmsb hzbd" style="min-width:150px"><span></span>'+CARET+'</button><button type="button" class="hmcbtn synmsb hzbs" style="min-width:150px"><span></span>'+CARET+'</button><button type="button" class="btn hzbr">'+X+'Reset page filters</button><span class="hzbn"></span>';
  const hd=pane.querySelector(':scope > .hubhd');if(hd)hd.insertAdjacentElement('beforebegin',bar);else pane.appendChild(bar);
  bar.querySelector('.hzbd').onclick=e=>{e.stopPropagation();
   const items=uniq(ZD.map(r=>r.dv)).map(v=>({v,l:v}));
   msOpen(e.currentTarget,{title:'Divisions',items,sel:DVSEL||(fDiv.value?new Set([fDiv.value]):null),onApply:(s,n)=>{
    DSEL=null;DSMV='';fDist.value='';fTeh.value='';UCSEL=null;fUC.value='';
    if(!s.length||s.length>=n){DVSEL=null;fDiv.value='';}else if(s.length===1){DVSEL=null;fDiv.value=s[0];}else{DVSEL=new Set(s);fDiv.value='';}
    cascade();render();}});};
  bar.querySelector('.hzbs').onclick=e=>{e.stopPropagation();
   const items=uniq(ZD.filter(r=>dvOK(r.dv)).map(r=>r.d)).sort((a,b)=>a.localeCompare(b)).map(d=>({v:d,l:d,g:D2DV[d]||''}));
   msOpen(e.currentTarget,{title:'Districts',items,sel:DSEL||(fDist.value?new Set([fDist.value]):null),onApply:(s,n)=>{
    if(!s.length||s.length>=n){DSEL=null;fDist.value='';}else if(s.length===1){DSEL=null;fDist.value=s[0];}else DSEL=new Set(s);
    DSMV=DSEL?dsKey(DSEL):'';fTeh.value='';UCSEL=null;fUC.value='';
    DSLOCK=true;try{cascade();}finally{DSLOCK=false;}
    render();}});};
  bar.querySelector('.hzbr').onclick=()=>{DVSEL=null;fDiv.value='';DSEL=null;DSMV='';fDist.value='';fTeh.value='';UCSEL=null;fUC.value='';SYNCP.hz=null;
   DSLOCK=true;try{cascade();}finally{DSLOCK=false;}render();};
 }
 const bd=bar.querySelector('.hzbd'),bs=bar.querySelector('.hzbs');
 bd.querySelector('span').textContent=DVSEL?DVSEL.size+' divisions':(fDiv.value||'All divisions');
 bd.title=DVSEL?'Selected: '+[...DVSEL].join(', '):'Filter by division \u2014 pick one or many';
 bs.querySelector('span').textContent=DSEL?dsCnt()+' districts':(fDist.value||'All districts');
 bs.title=DSEL?'Selected: '+[...DSEL].join(', '):'Filter by district \u2014 pick one or many';
 bar.querySelector('.hzbn').textContent=geoOn()?'The overview line and the tables follow these picks.':'Pick a division or district to narrow this page.';
}"""


def edits():
    E = []

    def add(old, new, n=1, why=''):
        E.append((old, new, n, why))

    add("var DVSEL=null,UCSEL=null,SYNCP={z:null,d:null,v:null,a:null};",
        "var DVSEL=null,UCSEL=null,SYNCP={z:null,d:null,v:null,a:null,hz:null};",
        1, 'SYNCP hz group')

    add("Zero-dose children reported in campaigns, covered against that same campaign's list, "
        "recorded in IDIMS and validated as vaccinated. The cards show all of KP; the cross-check "
        "table follows the division / district filter.",
        "Zero-dose children recorded in each campaign's own return, covered against that same "
        "campaign's list, entered in IDIMS and validated as vaccinated. SNID Nov-26 recorded zero "
        "dose is in; its coverage, LQAS and validation are the post-campaign returns awaited. The "
        "cards show all of KP; the cross-check table follows the division / district filter.",
        1, 'pane intro')

    add("const GRP={hzd:'z',zov:'z',zcmp:'z',zperf:'z',zins:'z',overview:'d',compare:'d',followup:'d',notes:'d',vsum:'v',vfu:'v',adv:'a'};",
        "const GRP={hzd:'hz',zov:'z',zcmp:'z',zperf:'z',zins:'z',overview:'d',compare:'d',followup:'d',notes:'d',vsum:'v',vfu:'v',adv:'a'};",
        1, 'hzd own campaign group')

    add(" if(g==='z')return CPS.map(k=>({k,l:CAMP[k],tok:{A:/\\bApr(il)?\\b/i,M:/\\bMay\\b/i,S:/\\bSept?(ember)?\\b/i}[k]}));",
        " if(g==='z')return CPS.map(k=>({k,l:CAMP[k],tok:{A:/\\bApr(il)?\\b/i,M:/\\bMay\\b/i,S:/\\bSept?(ember)?\\b/i}[k]}));\r\n"
        " if(g==='hz')return CPS.map(k=>({k,l:CAMP[k],tok:{A:/\\bApr(il)?\\b/i,M:/\\bMay\\b/i,S:/\\bSept?(ember)?\\b/i}[k]})).concat([{k:'N',l:novLabel(),tok:/\\bNov(ember)?\\b/i}]);",
        1, 'campaign defs hz')

    add(r"const NOTE={z:'Selected campaigns show side by side below; the other campaigns are hidden from this page\u2019s tables and charts.',",
        r"const NOTE={hz:'The overview line shows the most recent campaign you selected; the panel below compares every selected campaign, with SNID Nov-26 recorded only.',z:'Selected campaigns show side by side below; the other campaigns are hidden from this page\u2019s tables and charts.',",
        1, 'NOTE hz')

    add(" const add=(a,k,rep,num)=>{if(rep==null)return;const o=acc[a]=acc[a]||{},c=o[k]=o[k]||{rep:0,num:0};c.rep+=rep||0;c.num+=num||0;};",
        " const add=(a,k,rep,num)=>{if(rep==null)return;const o=acc[a]=acc[a]||{},c=o[k]=o[k]||{rep:0,num:0};c.rep+=rep||0;if(num==null)c.uk=true;else c.num+=num||0;};",
        1, 'unknown-coverage flag')

    add(" if(g==='z'){ZD.filter(r=>matchZ(r)).forEach(r=>D.forEach(x=>add(ak(r),x.k,r['r'+x.k],r['c'+x.k])));return {ll,D,acc,m:['Reported','Covered','% covered']};}",
        " if(g==='z'){ZD.filter(r=>matchZ(r)).forEach(r=>D.forEach(x=>add(ak(r),x.k,r['r'+x.k],r['c'+x.k])));return {ll,D,acc,m:['Reported','Covered','% covered']};}\r\n"
        " if(g==='hz'){ZD.filter(r=>matchG(r)).forEach(r=>D.forEach(x=>{if(x.k!=='N')add(ak(r),x.k,r['r'+x.k],r['c'+x.k]);}));\r\n"
        "  novRows().filter(matchG).forEach(r=>D.forEach(x=>{if(x.k==='N')add(ak(r),'N',r.rN,r.cN);}));\r\n"
        "  return {ll,D,acc,m:['Reported','Covered','% covered']};}",
        1, 'sbsData hz')

    add("  pane.querySelector(':scope > .syncp').insertAdjacentElement('afterend',box);}",
        "  if(g==='hz')pane.appendChild(box); else pane.querySelector(':scope > .syncp').insertAdjacentElement('afterend',box);}",
        1, 'sbs position hz')

    add(" const S=sbsData(g),areas=Object.keys(S.acc).sort((a,b)=>a.localeCompare(b)),pc=c=>c&&c.rep?c.num/c.rep*100:null,tot={};",
        " const S=sbsData(g),areas=Object.keys(S.acc).sort((a,b)=>a.localeCompare(b)),pc=c=>c&&!c.uk&&c.rep?c.num/c.rep*100:null,tot={};\r\n"
        " const covD=S.D.filter(x=>areas.some(a=>{const c=S.acc[a][x.k];return c&&!c.uk&&c.rep;})),recOnly=!covD.length,seriesD=recOnly?S.D:S.D.filter(x=>covD.indexOf(x)>=0);",
        1, 'covered-series guard')

    add(" S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0};areas.forEach(a=>{const c=S.acc[a][x.k];if(c){t.rep+=c.rep;t.num+=c.num;}});});",
        " S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0,uk:false};areas.forEach(a=>{const c=S.acc[a][x.k];if(c){t.rep+=c.rep;t.num+=c.num;if(c.uk)t.uk=true;}});});",
        1, 'totals unknown flag')

    add(r" box.querySelector('.synsbsn').textContent=(g==='a'&&(UCSEL||fUC.value)?'The 2022\u201326 advance reports carry no UC codes, so the UC filter is not applied here. ':'')+'Each campaign keeps its own columns \u2014 nothing is added across rounds. A dash means the area has no data for that round.';",
        r" box.querySelector('.synsbsn').textContent=(g==='hz'?'SNID Nov-26 carries recorded zero dose only: its covered figure, LQAS and validation arrive with the post-campaign returns. ':'')+(g==='a'&&(UCSEL||fUC.value)?'The 2022\u201326 advance reports carry no UC codes, so the UC filter is not applied here. ':'')+'Each campaign keeps its own columns \u2014 nothing is added across rounds. A dash means the area has no data for that round.';",
        1, 'sbs note hz')

    add(r''' const cell=c=>c?'<td class="n">'+fmt(c.rep)+'</td><td class="n">'+fmt(c.num)+'</td><td class="n">'+(pc(c)==null?'\u2013':'<b style="color:'+colP(pc(c))+'">'+pc(c).toFixed(1)+'%</b>')+'</td>':'<td class="n">\u2013</td><td class="n">\u2013</td><td class="n">\u2013</td>';''',
        r''' const cell=c=>{if(!c)return '<td class="n">\u2013</td><td class="n">\u2013</td><td class="n">\u2013</td>';const p=pc(c);return '<td class="n">'+fmt(c.rep)+'</td><td class="n">'+(c.uk?'\u2013':fmt(c.num))+'</td><td class="n">'+(p==null?'\u2013':'<b style="color:'+colP(p)+'">'+p.toFixed(1)+'%</b>')+'</td>';};''',
        1, 'cell unknown dash')

    add(crlf(r""" Highcharts.chart(box.querySelector('#sbsCh_'+TAB),{chart:{type:'column'},title:{text:S.m[2].charAt(0).toUpperCase()+S.m[2].slice(1)+' by '+S.ll.toLowerCase()+' and campaign'},
  subtitle:{text:'One bar per selected campaign'+(areas.length>40?' \u00b7 40 largest of '+fmt(areas.length)+' shown':'')},
  xAxis:{categories:ca,labels:{rotation:ca.length>8?-45:0}},yAxis:{title:{text:S.m[2]+' (%)'},min:0},
  tooltip:{shared:true,valueDecimals:1,valueSuffix:'%'},plotOptions:{column:{borderRadius:2}},
  series:S.D.map(x=>({name:x.l,data:ca.map(a=>{const v=pc(S.acc[a][x.k]);return v==null?null:+v.toFixed(1);})}))});"""),
        crlf(r""" Highcharts.chart(box.querySelector('#sbsCh_'+TAB),{chart:{type:'column'},title:{text:(recOnly?'Recorded zero dose by ':'Covered share by ')+S.ll.toLowerCase()+' and campaign'},
  subtitle:{text:'One bar per selected campaign'+(areas.length>40?' \u00b7 40 largest of '+fmt(areas.length)+' shown':'')+(seriesD.length<S.D.length?' \u00b7 coverage not yet reported for '+S.D.filter(x=>seriesD.indexOf(x)<0).map(x=>x.l).join(', '):'')},
  xAxis:{categories:ca,labels:{rotation:ca.length>8?-45:0}},yAxis:{title:{text:recOnly?'Recorded children':S.m[2]+' (%)'},min:0},
  tooltip:{shared:true,valueDecimals:1,valueSuffix:recOnly?'':'%'},plotOptions:{column:{borderRadius:2}},
  series:seriesD.map(x=>({name:x.l,data:ca.map(a=>{const c=S.acc[a][x.k];if(!c)return null;const v=recOnly?c.rep:pc(c);return v==null?null:+v.toFixed(recOnly?0:1);})}))});"""),
        1, 'chart recorded fallback')

    add(r" box.querySelector('.synsbscap').textContent=S.D.map(x=>x.l+': '+(pc(tot[x.k])==null?'no data':pc(tot[x.k]).toFixed(1)+'% ('+fmt(tot[x.k].num)+' of '+fmt(tot[x.k].rep)+')')).join(' \u00b7 ');",
        r" box.querySelector('.synsbscap').textContent=S.D.map(x=>x.l+': '+(tot[x.k].uk&&!tot[x.k].num?'recorded '+fmt(tot[x.k].rep)+' \u00b7 coverage awaited':pc(tot[x.k])==null?'no data':pc(tot[x.k]).toFixed(1)+'% ('+fmt(tot[x.k].num)+' of '+fmt(tot[x.k].rep)+')')).join(' \u00b7 ');",
        1, 'caption unknown')

    add("@media print{.syndl,.syncp,.synms{display:none!important}}",
        ".hzbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 10px;padding:8px 12px;border:1px solid var(--color-border);border-radius:12px;background:#f8fafc}\r\n"
        ".hzbar .hzbl{font:600 12px var(--font-sans);color:#0e7490}\r\n"
        ".hzbar .hzbn{font:12px var(--font-sans);color:var(--color-text-secondary);flex:1;min-width:180px}\r\n"
        ".hzbar .btn{display:inline-flex;align-items:center;padding:6px 12px;border-radius:10px}\r\n"
        "@media (max-width:700px){.hzbar .hmcbtn{width:100%;min-width:0!important;max-width:none!important}}\r\n"
        "@media print{.syndl,.syncp,.synms,.hzbar{display:none!important}}",
        1, 'hzbar css')

    add("// ---------- wiring ----------\r\nlet busy=false,tmr=null;",
        crlf(NEW_HZBAR) + "\r\n// ---------- wiring ----------\r\nlet busy=false,tmr=null;",
        1, 'hzbar function')

    add(" try{if(g){cpBar(pane,g);sbsRender(pane,g);}}catch(e){console.warn('syn panel',e);}",
        " try{if(g){cpBar(pane,g);if(TAB==='hzd')hzBar(pane);sbsRender(pane,g);}}catch(e){console.warn('syn panel',e);}",
        1, 'after wiring hzbar')

    return E


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    E = edits()
    report = []
    new_stamp = dashpatch.pkt_stamp()
    for v in vs:
        s = v.text
        for old, new, n, why in E:
            got = s.count(old)
            v.require(got == n, '%s: expected %d hit(s) of %r, found %d' % (why, n, old[:70], got))
            s = s.replace(old, new)

        # ---- overview strip: whole function replaced (it carries literal middots/dashes) ----
        a = s.index('function hzdStrip(){')
        b = s.index('function hepiStrip(){')
        old_block = s[a:b]
        v.require(old_block.count("hubStrip('hzd'") == 1, 'hzdStrip anchor moved')
        v.require(old_block.endswith(']);}\r\n'), 'hzdStrip end marker moved')
        s = s[:a] + crlf(NEW_STRIP) + '\r\n' + s[b:]

        # ---- home card: fact 1 becomes the Nov-26 recorded count ----
        lines = s.split('\r\n')
        hit = [i for i, l in enumerate(lines) if l.startswith(' el(\'hF1\').innerHTML=`<div class="hf"><b>${fmt(zRep)}</b>')]
        v.require(len(hit) == 1, 'hF1 line: expected 1 hit, found %d' % len(hit))
        lines[hit[0]:hit[0] + 1] = NEW_HF1.split('\n')
        s = '\r\n'.join(lines)

        # ---- stamp ----
        v.text = s
        dashpatch.set_stamp(v, new_stamp)

        # ---- guards ----
        for token in ('function novRows', 'function hzBar', "GRP={hzd:'hz'", "if(g==='hz')return CPS",
                      "bar.className='hzbar'", 'novLabel()', 'c.uk'):
            v.require(token in v.text, 'missing %s' % token)
        v.require(v.text.count('function hzdStrip(') == 1, 'hzdStrip duplicated')
        v.require(v.text.count('hubStrip(\'hzd\'') == 2, 'hzdStrip call count unexpected')
        v.require('SNID Nov-26 recorded zero dose is the round’s own' in v.text,
                  'Nov overview note missing')
        report.append('%s: %+d chars' % (v.rel, v.delta()))

    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    print('\n'.join(report))
    print('stamp -> %s' % new_stamp)
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, 'Zero Dose overview: SNID Nov-26 recorded zero dose (42,653 children, 996 UCs) '
                                  'with a campaign picker and division/district multi-select filters; Nov covered stays a dash '
                                  'until the post-campaign return.', dry=False)
    print('PATCHED %d variants + version files' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
