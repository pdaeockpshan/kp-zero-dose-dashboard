"""Insert the HRMP PTP field-monitoring block (const PTPM) into the index.html master.

Adds, in the master only:
  1. `const PTPM = {...}` right after `const PTP = {...};`, filled from _refresh/out/ptpm.json so
     the block is live the moment the master is patched; later refreshes go through
     `refresh.py run --only ptpm`.
  2. A field-check card directly under the reporting-coverage grid, with its own table (tPTm),
     caption and CSV download.
  3. `ptpmTab()` next to the other PTP cache helpers, and the render block inside `renderPTP()`,
     before the district inventory table.

What this block is: the three IDIMS HRMP forms filed at the same transit points - a monitoring
checklist, a spot survey and a logistics check - joined to the PTP roster on ptp_loc = Site_ID and
keyed on the district index and month slots const PTP already uses, so the existing Reporting period
picker (year, then month) scopes it like every other table on the tab.

Design rules the patch depends on, all established by recon in _refresh/extract_ptpm.py:
  - The exports stop in Apr-2025 while the reporting panel runs to Oct-2026. A period outside a
    form's own span renders a dash with the span in its tooltip, never a zero.
  - "Posts ever checked" is a whole-window union stored per district (ev[7]) plus a province-level
    union (n.reached_any), because 8 posts are filed under two districts. It is blank in a period
    view rather than guessed from the three post columns beside it.
  - Only counts of forms, visits and posts are published. The answer-code columns, the copy-through
    team attributes, total_team / transit_teams, the two spot-survey child tallies, the 15 logistics
    item families and every name, CNIC, phone and coordinate stay in PTPM.hold and are named in the
    caption as held out.
  - The four under-5 spot columns are published under the export's own column names because the
    questionnaire wording does not travel with the export.
  - Nothing here is an immunization coverage figure, and the PTP panel's Coverage / OPV columns are
    still held out (#156), so no coverage percentage appears anywhere on the tab.

All inserted text is written with CRLF so the file's line endings stay uniform.
Every anchor is asserted to occur exactly once before editing; nothing is written unless the patch
applies cleanly.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

MASTER = 'index.html'
PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'ptpm.json')

A_CONST = 'const SURVW = {'
A_CARD = '<div class="cap" id="capPTc"></div>\r\n</div>\r\n'
A_CACHE = 'function ptBadge(){'
A_RENDER = ' // district inventory table\r\n'
A_HINT = 'reporting-coverage grid and the union-council listing.'
HINT_NEW = ('reporting-coverage grid, the HRMP field-check table and the union-council listing. '
            'The field-check table follows the same pick, but those three forms stopped in '
            'Apr-2025, so a later period is a dash there rather than nothing filed.')

CARD = (
 '<div class="card" id="cPTm" style="display:none">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Field checks at the same posts: HRMP monitoring, spot '
 'surveys and logistics</h3><div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntPTm"></span><button class="btn" id="btnPTm">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tPTm"></table></div>\r\n'
 '<div class="cap" id="capPTm"></div>\r\n'
 '</div>\r\n'
)

CACHE = r"""var _PTMM=null;
function ptpmTab(){
 if(_PTMM&&_PTMM.v===PTPM)return _PTMM;
 const y={},m={},e={};
 PTPM.d.forEach(r=>{const a={},b={};
  (r[1]||[]).forEach(c=>{a[c[0]]=c[1];}); (r[2]||[]).forEach(c=>{b[c[0]]=c[1];});
  y[r[0]]=a; m[r[0]]=b;});
 PTPM.ev.forEach(r=>{e[r[0]]=r;});
 return _PTMM={v:PTPM,y:y,m:m,e:e};
}
"""

RENDER = r""" // HRMP field checks at these same posts: monitoring checklists, spot surveys, logistics
 const PMC=el('cPTm');
 if(PMC){
  if(typeof PTPM==='undefined'||!PTPM||!PTPM.d||!PTPM.d.length||!PTPM.mk||PTPM.yr.length!==nY){
   PMC.style.display='none';
  }else{
  PMC.style.display='';
  const PT=ptpmTab(), MK={}, KS={mon:['mchk','mpst','moff','mtm','mtp'],
   spot:['schk','spst','soff','ssick','sref','smiss','sload'], log:['lchk','lpst','loff']}, SOF={}, SP={};
  const SRCW={mon:'monitoring', spot:'the spot survey', log:'the logistics check'};
  PTPM.mk.forEach((k,i)=>{MK[k]=i});
  Object.keys(KS).forEach(s=>{KS[s].forEach(k=>{SOF[k]=s;});
   // a form stopped being filed long before the daily panel did, so out-of-span periods are dashes
   SP[s]=!one||(mv?(PTPM.first[s]<=yv*100+mv&&yv*100+mv<=PTPM.last[s])
    :(PTPM.first[s]<=yv*100+12&&PTPM.last[s]>=yv*100+1));});
  const EVI={mpst:1, spst:2, lpst:3, moff:4, soff:5, loff:6};
  const CL=i=>mv?PT.m[i][yi*12+mv-1]:PT.y[i][yi];
  const V=(i,k)=>{const a=MK[k];
   if(!SP[SOF[k]])return null;
   if(!one){if(EVI[k]!=null){const e=PT.e[i]; return e?(e[EVI[k]]||0):0;}
    let t=0; const yb=PT.y[i]||{}; Object.keys(yb).forEach(j=>{t+=(yb[j][a]||0);}); return t;}
   const c=CL(i); return c?(c[a]||0):0;};
  const MR=DI.filter(i=>PT.y[i]).map(i=>{const e=PT.e[i]||[], den=PTP.d[i][2];
   return{i:i, dn:PTP.ds[i], dv:PTP.dv[i], posts:den, any:one?null:(e[7]||0),
    rcp:one?null:(den?100*(e[7]||0)/den:null),
    mchk:V(i,'mchk'), mpst:V(i,'mpst'), mtm:V(i,'mtm'), mtp:V(i,'mtp'),
    schk:V(i,'schk'), spst:V(i,'spst'), ssick:V(i,'ssick'), sref:V(i,'sref'),
    smiss:V(i,'smiss'), sload:V(i,'sload'), lchk:V(i,'lchk'), lpst:V(i,'lpst')};});
  const d0=v=>v==null?'\u2013':fmt(v);
  const DQ=s=>PTPM.n[s].dq||{}, DRS=s=>{const d=PTPM.n[s].drop||{};
   return Object.keys(d).map(k=>fmt(d[k])+' '+k).join(', ')||'nothing'};
  const FMT=s=>SRCW[s]+' '+PTPM.spans[s];
  // the three forms cover their own window, not the panel's, so label their sums with theirs
  const FSP=(function(){let a=null,b=null;['mon','spot','log'].forEach(s=>{const p=(PTPM.spans[s]||'').split('..');
   if(p[0]&&(!a||p[0]<a))a=p[0]; if(p[1]&&(!b||p[1]>b))b=p[1];}); return a+'..'+b;})();
  const SW=one?SLab:FSP;
  drawTable('tPTm',[
   {k:'dn',l:'District',f:x=>'<b>'+esc(x.dn)+'</b>'},
   {k:'dv',l:'Division'},
   {k:'posts',l:'PTPs',n:1,f:x=>fmt(x.posts),
    tt:'Permanent Transit Points listed for this district across '+PTP.win+' - the same roster the reporting tables use'},
   {k:'any',l:'Posts ever checked',n:1,f:x=>d0(x.any),
    tt:'Distinct panel posts reached by at least one of the three forms over '+FSP+'. It is a union, not the sum of the three post columns beside it, and it is blank in a period view because a post checked in two different months is still one post'},
   {k:'rcp',l:'Reached %',n:1,f:x=>x.rcp==null?'\u2013':cc(x.rcp,50,25),
    tt:'Posts ever checked / posts on the panel. Green is 50% or more of a district\'s posts, amber 25-50%, red under 25%'},
   {k:'mchk',l:'Checklists',n:1,f:x=>d0(x.mchk),
    tt:'Monitoring checklists logged in '+SW+' - '+FMT('mon')+', so any period after Apr-2025 is a dash, not a zero'},
   {k:'mpst',l:'Posts monitored',n:1,f:x=>d0(x.mpst),
    tt:'Distinct panel posts with a monitoring checklist in '+SW},
   {k:'mtm',l:'Teams monitored',n:1,f:x=>d0(x.mtm),
    tt:'teams_monitored summed over checklists in '+SW+' - team visits, not distinct teams. The source writes a fraction in '+fmt(DQ('mon')['teams_monitored is not a whole number']||0)+' of its rows and those are rounded to a whole team here'},
   {k:'mtp',l:'Teams present',n:1,f:x=>d0(x.mtp),
    tt:'present_teams summed over checklists in '+SW+', same rounding as the column beside it'},
   {k:'schk',l:'Spot surveys',n:1,f:x=>d0(x.schk),
    tt:'Spot-survey rows logged in '+SW+' - '+FMT('spot')},
   {k:'spst',l:'Posts surveyed',n:1,f:x=>d0(x.spst),
    tt:'Distinct panel posts with a spot survey in '+SW},
   {k:'ssick',l:'sick_5',n:1,f:x=>d0(x.ssick),
    tt:'The export\'s own column sick_5, summed over spot surveys in '+SW+'. The questionnaire wording does not travel with the file, so these four under-5 columns are published under the names the source gives them'},
   {k:'sref',l:'refused_5',n:1,f:x=>d0(x.sref),
    tt:'The export\'s own column refused_5, summed over spot surveys in '+SW},
   {k:'smiss',l:'ptp_missed_5',n:1,f:x=>d0(x.smiss),
    tt:'The export\'s own column ptp_missed_5, summed over spot surveys in '+SW},
   {k:'sload',l:'over_loading_5',n:1,f:x=>d0(x.sload),
    tt:'The export\'s own column over_loading_5, summed over spot surveys in '+SW},
   {k:'lchk',l:'Logistics checks',n:1,f:x=>d0(x.lchk),
    tt:'Logistics check-list rows logged in '+SW+' - '+FMT('log')+'. Its 15 item columns are held out, see the caption'},
   {k:'lpst',l:'Posts checked',n:1,f:x=>d0(x.lpst),
    tt:'Distinct panel posts with a logistics check in '+SLab}],
   MR, one?'schk':'rcp', one?-1:1);
  el('cntPTm').textContent=MR.length+' district units in the field exports \u00b7 '+SW
   +' \u00b7 the three forms were pulled '+PTPM.asof;
  const NOF=DI.filter(i=>!PT.y[i]).map(i=>PTP.ds[i]);
  const GH=['mon','spot','log'].filter(s=>(PTPM.gap[s]||[]).length);
  const gl=s=>(PTPM.gap[s]||[]).map(g=>_MON[(+g.slice(5,7))-1]+'/'+g.slice(0,4)).join(', ');
  const RANY=PTPM.n.reached_any||0, RPOS=PTPM.n.roster_posts||0;
  const USUM=MR.reduce((t,x)=>t+(x.any||0),0), SPOS=MR.reduce((t,x)=>t+x.posts,0);
  el('capPTm').textContent=[
   'These are the HRMP field visits to the same transit points the panel above reports from: three '
    +'IDIMS forms - a monitoring checklist, a spot survey and a logistics check - joined to the PTP '
    +'roster on ptp_loc = Site_ID, so the post columns count panel posts and not rows. Across '+FSP+
    ', '+fmt(PTPM.n.mon.posts)+' posts carry a monitor, '+fmt(PTPM.n.spot.posts)+' a survey and '
    +fmt(PTPM.n.log.posts)+' a logistics check.',
   'The forms stopped before the reporting panel did: '+FMT('mon')+', '+FMT('spot')+' and '+FMT('log')+
    ', while the daily reports run to '+LM+'. A period after a form stopped shows \u2013 with that '
    +'form\'s span in its tooltip, never a zero, so '
    +(one?('picking '+yv+' shows what was actually filed in the field then, and much of 2025 and all of '
      +PTP.yr[nY-1]+' is dashed.'):('the whole-window view is the only one where all three forms are '
      +'filled in.')),
   RPOS?(('Province-wide over '+FSP+', at least one field check reached '+fmt(RANY)+' of the '
    +fmt(RPOS)+' panel posts ('+p1(100*RANY/RPOS)+'%), leaving '+fmt(RPOS-RANY)+' that never had one. ')
    +(one?'Reached is blank in a period view on purpose: a post checked in two months is still one '
      +'post, and the union is only published for '+FSP+' and for the province.'
      :'The '+fmt(MR.length)+(MR.length===1?' row reads ':' rows read ')+fmt(USUM)+' posts of the '
      +fmt(SPOS)+' on their own rosters'+(whole?', because '+fmt(USUM-RANY)+' posts are filed under two '
      +'districts - which is why the province figure is the union and not that sum'
      :'; a post filed under two districts counts once in each, so that sum is not a province union')+'.'))
    :'No roster total in this payload.',
   NOF.length?(fmt(NOF.length)+' district unit'+(NOF.length>1?'s':'')+' in scope '
    +(NOF.length>1?'report daily at a PTP but appear in none of the three field exports'
     :'reports daily at a PTP but appears in none of the three field exports')+': '+esc(NOF.join(', '))
     +'. They get no row in this table, which is the finding rather than a hole in the table.')
     :'Every district unit in scope appears in at least one of the three field exports.',
   GH.length?('Inside their own spans the forms have holes: '+GH.map(s=>SRCW[s]+' has nothing filed '
    +'anywhere in KP in '+gl(s)).join('; ')+'.')
    :'Inside their own spans every month slot carries at least one form somewhere in KP.',
   'How the rows were kept: of '+fmt(PTPM.n.mon.read)+' monitoring rows read, '+DRS('mon')+' was '
    +'dropped, and the same for the survey ('+fmt(PTPM.n.spot.read)+' read, '+DRS('spot')+' dropped) and '
    +'the logistics form ('+fmt(PTPM.n.log.read)+' read, '+DRS('log')+' dropped). '
    +fmt(DQ('mon')['visit month and entry month differ']||0)+' monitoring rows were entered in a '
    +'different month from the visit, and the visit month is what is published here; the survey and '
    +'logistics forms carry no visit date, so their months are entry months. '
    +fmt(DQ('spot')['post recorded under a district the panel places elsewhere']||0)+' survey rows and '
    +fmt(DQ('log')['post recorded under a district the panel places elsewhere']||0)+' logistics rows name '
    +'a post the Oct-2026 panel places in another district ('+fmt(PTPM.n.spot.moved)+' survey posts and '
    +fmt(PTPM.n.log.moved)+' logistics posts sit under two districts), and each form also reached posts '
    +'that are not on the panel roster at all - '+fmt(PTPM.n.mon.off_posts)+' monitored, '
    +fmt(PTPM.n.spot.off_posts)+' surveyed, '+fmt(PTPM.n.log.off_posts)+' logistics-checked - counted in '
    +'the form columns and never in the post columns.',
   'What these exports also carry and this table does not publish: the yes/no answer fields, which the '
    +'source stores as 1/2/3 with no legend; the eight team-attribute columns, which repeat the same '
    +'values row for row; total_team and transit_teams, which reach 202 and 141 in single rows; the '
    +'under-5 and under-10 child tallies, which belong to two different questionnaires split by '
    +'site_type (19,986 survey rows against 233); the 15 logistics item families, whose abbreviations are '
    +'undefined and whose available exceeds total in 846 rows; and every person, CNIC, phone number and '
    +'coordinate. The four under-5 columns kept here are headed exactly as the export heads them, '
    +'because the wording behind them is not in the file.',
   'Read every figure here as a count of forms and visits. None of it is a coverage measure and none of '
    +'it can be turned into one: it records who walked up to a transit point and when, not how many '
    +'children were protected. Rows run by share of posts ever reached, weakest first, and the Division '
    +'and District filters scope every row.'
  ].join(' ');
  el('btnPTm').onclick=()=>csvDownload('ptp_field_checks_'+(one?(mv?(yv+'-'+mv):('y'+yv)):PTP.win)
    +'_'+_slug()+'.csv',
   ['Division','District','PTPs on the panel','Posts ever checked','Reached %','Monitoring checklists',
    'Posts monitored','Teams monitored','Teams present','Spot surveys','Posts surveyed',
    'sick_5','refused_5','ptp_missed_5','over_loading_5','Logistics checks','Posts logistics-checked'],
   MR.map(x=>[x.dv,x.dn,x.posts,x.any,x.rcp==null?'':p1(x.rcp),x.mchk,x.mpst,x.mtm,x.mtp,x.schk,x.spst,
    x.ssick,x.sref,x.smiss,x.sload,x.lchk,x.lpst]));
  }
 }
"""


def patch(v, js):
    t = v.text
    for nm, a in (('const', A_CONST), ('card', A_CARD), ('cache', A_CACHE),
                  ('render', A_RENDER), ('hint', A_HINT)):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1) [%s]: %r'
                  % (t.count(a), nm, a[:56]))
    v.require('const PTPM' not in t and 'id="cPTm"' not in t, 'PTPM block already patched in')
    t = t.replace(A_CONST, 'const PTPM = %s;\r\n' % js + A_CONST)
    t = t.replace(A_CARD, A_CARD + CARD)
    t = t.replace(A_CACHE, CACHE.replace('\n', '\r\n') + A_CACHE)
    t = t.replace(A_RENDER, RENDER.replace('\n', '\r\n') + A_RENDER)
    t = t.replace(A_HINT, HINT_NEW)
    v.text = t
    v.changes.append('PTPM field-check block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for once in ('const PTPM = {', 'function ptpmTab(){', 'ptp_field_checks_',
                 'id="cPTm"', "drawTable('tPTm'", "el('capPTm')", "el('cntPTm')"):
        v.require(t.count(once) == 1, '%s occurs %d times (want 1)' % (once, t.count(once)))
    for needle in ('id="tPTm"', 'id="capPTm"', 'id="btnPTm"', 'Posts ever checked', 'over_loading_5',
                   "PMC.style.display='none'", "one?'schk':'rcp'", 'SOF[k]=s', 'EVI={mpst:1',
                   'teams_monitored is not a whole number', 'ptp_loc = Site_ID'):
        v.require(t.count(needle) >= 1, '%s is missing' % needle)
    # the field table has to sit between the coverage grid and the district inventory
    v.require(t.index('id="capPTc"') < t.index('id="cPTm"') < t.index('id="tPTa"'),
              'the field-check card is not between the coverage grid and the district inventory')
    v.require(t.index('const PTPM = ') < t.index('const SURVW = '), 'PTPM const must precede SURVW')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_ptpm.py first' % PAYLOAD)
    obj = json.loads(srcutil.read_text(PAYLOAD))
    js = srcutil.dumps(obj)
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    patch(v, js)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('payload PTPM %d chars, %d districts with field data, %d held-out column groups'
          % (len(js), len(obj['ds']), len(obj['hold'])))
    print("OK ptpm-ui master only - preview / public / internal builds pick the block up through "
          'push_master.py, which needs the owner\'s word')


if __name__ == '__main__':
    main()
