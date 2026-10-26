"""Insert the HRMP mobile and migrant team block (const MTM) into the index.html master.

Adds, in the master only:
  1. `const MTM = {...}` right after `const PTPM = {...};`, filled from _refresh/out/mtm.json so the
     block is live the moment the master is patched; later refreshes go through `refresh.py run
     --only mtm`.
  2. One card under the field-check card with two tables: tMTf (the six forms) and tMTd (the same
     forms by district), its caption and a CSV download.
  3. `mtmTab()` next to the other PTP cache helpers, and the render block inside `renderPTP()`,
     after the field-check block and before the district inventory table.

Design rules the patch depends on, all established by recon in _refresh/extract_mtm.py:
  - The six forms stop in Apr-2025 while the reporting panel runs to Oct-2026, and each one starts and
    stops in its own month. A column is dashed when none of the forms that write it is live in the
    picked period, never shown as a zero.
  - Teams and union councils are district-scoped unions (the nomad form holds 23 distinct team numbers
    province-wide against 63 once scoped to their district), so they are published only for the whole
    window and the province figure is labelled as a sum of district counts. A period view leaves them
    blank rather than pretending a team seen in two months is two teams.
  - Rows are counted per form in six separate columns so a period view can say which form filed them;
    "Forms filed" is the sum of those six and is a count of forms, not of children.
  - Nothing here is a coverage figure. The target_* / coverage_* family is held out while the same
    family on the PTP panel is still unconfirmed (#156), so no coverage percentage appears.
  - origin_country is decoded from the export's own caption columns, which is why the mapping form is
    published as two origin columns and none of its population fields.

All inserted text is written with CRLF so the file's line endings stay uniform.
Every anchor is asserted to occur exactly once before editing; nothing is written unless the patch
applies cleanly.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

MASTER = 'index.html'
PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'mtm.json')

A_CONST = 'const SURVW = {'
A_CARD = '<div class="cap" id="capPTm"></div>\r\n</div>\r\n'
A_CACHE = 'function ptBadge(){'
A_RENDER = ' // district inventory table\r\n'
A_HINT = ('reporting-coverage grid, the HRMP field-check table and the union-council listing. The '
          'field-check table follows the same pick, but those three forms stopped in Apr-2025, so a '
          'later period is a dash there rather than nothing filed.')
HINT_NEW = ('reporting-coverage grid, the two HRMP blocks and the union-council listing. The two HRMP '
            'blocks follow the same pick, but none of those nine forms was still being filed after '
            'Apr-2025, so a later period is a dash there rather than nothing filed.')

CARD = (
 '<div class="card" id="cMTf" style="display:none">\r\n'
 '<div class="tblhdr"><h3 style="margin:0">Mobile and migrant teams: the six HRMP forms filed in the '
 'same Apr-2025 pull</h3><div style="display:flex;gap:10px;align-items:center">'
 '<span class="cnt" id="cntMTf"></span><button class="btn" id="btnMTf">Download (CSV)</button></div></div>\r\n'
 '<div class="scroll"><table id="tMTf"></table></div>\r\n'
 '<div class="tblhdr"><h3 style="margin:0">The same six forms district by district</h3></div>\r\n'
 '<div class="scroll"><table id="tMTd"></table></div>\r\n'
 '<div class="cap" id="capMTf"></div>\r\n'
 '</div>\r\n'
)

CACHE = r"""var _MTM=null;
function mtmTab(){
 if(_MTM&&_MTM.v===MTM)return _MTM;
 const y={},m={},e={};
 MTM.d.forEach(r=>{const a={},b={};
  (r[1]||[]).forEach(c=>{a[c[0]]=c[1];}); (r[2]||[]).forEach(c=>{b[c[0]]=c[1];});
  y[r[0]]=a; m[r[0]]=b;});
 MTM.ev.forEach(r=>{e[r[0]]=r;});
 return _MTM={v:MTM,y:y,m:m,e:e};
}
"""

RENDER = r""" // HRMP mobile and migrant teams: the six forms pulled alongside the transit-point checks
 const MTC=el('cMTf');
 if(MTC){
  if(typeof MTM==='undefined'||!MTM||!MTM.d||!MTM.d.length||!MTM.mk||!MTM.forms||MTM.yr.length!==nY){
   MTC.style.display='none';
  }else{
  MTC.style.display='';
  const MT=mtmTab(), MM={}, OWN={}, SP={}, FL={};
  MTM.mk.forEach((k,i)=>{MM[k]=i});
  MTM.forms.forEach(f=>{FL[f.id]=f; f.cols.forEach(k=>{(OWN[k]=OWN[k]||[]).push(f.id);});
   SP[f.id]=!one||(mv?(MTM.first[f.id]<=yv*100+mv&&yv*100+mv<=MTM.last[f.id])
    :(MTM.first[f.id]<=yv*100+12&&MTM.last[f.id]>=yv*100+1));});
  const LBL={mapR:'Mapping records', pkf:'Pakistan-origin', afg:'Afghan-origin',
   nomadR:'Nomad team reports', mna:'Missed: not available', mrf:'Missed: refusal',
   z2:'Under-two zero-dose', epc:'EPI cards issued', nomonR:'Nomad checklists',
   sactR:'Search team reports', sp:'Sessions planned', sc:'Sessions conducted',
   smonR:'Search checklists', bikerR:'Biker reports', bn:'Not available recorded',
   bs:'Still not available', rn:'Refusals recorded', rs:'Still refusing',
   afp:'AFP cases', aef:'AEFI events'};
  const X={pkf:'origin_country is a code here, and the export names it in its own caption columns, so ' +
   '1 is published as a Pakistan-origin household and 2 as Afghan-origin. The export proves that ' +
   'reading itself: it fills the Pakistan district field in 83,206 of 83,207 code-1 rows and in none ' +
   'of the 31,694 code-2 rows.',
   afg:'Mapping rows whose household is recorded as Afghan-origin. No family or child total comes from ' +
   'this form: 906 rows claim more than 100 children and one claims 7,640, a tail holding a fifth of ' +
   'the province sum, so the rows are counted and the population columns are held out.',
   mapR:'One row is one mapping record for a household on the move, not one household: the same family ' +
   'recorded again in a later month counts again here.',
   z2:'The export\'s own ri_zero_under_2: children under two the team recorded as having no prior dose ' +
   'at that visit. A tally the team wrote down, not a coverage estimate.',
   mna:'missed_na on the nomad form - children recorded as missed because they were not available. The ' +
   'biker columns further right are that form\'s own version of the same question, so the two are not ' +
   'added together.',
   mrf:'missed_refusal on the nomad form.',
   nomadR:'One row is one nomad-team activity report.',
   nomonR:'One row is one monitoring checklist filed on a nomad team. Its item block (items_checked, ' +
   'data_Recording, vaccination) is blank in every row of the export, so nothing beyond the count of ' +
   'checklists is publishable from it.',
   sactR:'One row is one search-team activity report.',
   smonR:'One row is one monitoring checklist filed on a search team; its search_team, vaccination and ' +
   'cold_chain item columns are blank in every row.',
   bikerR:'One row is one special biker team report.',
   sp:'session_plan on the search-team form. In 49 of its rows the form records more sessions ' +
   'conducted than planned.',
   sc:'Summed over the rows that survived the source\'s own archive flag and its repeated unique_ids. ' +
   'One row writes -2 in this column: a negative cannot be part of a published total, so that cell is ' +
   'voided and this column is the sum of the usable values, not the raw column total.',
   bn:'na_recorded on the biker form. The 13 rows where still_na exceeds it are why these two columns ' +
   'are published as recorded and still-open tallies instead of as a rate.',
   rn:'refusal_recorded on the biker form - one of its rows carries 710 of them.',
   rs:'still_refusal on the biker form: refusals the team recorded as still open at that visit.',
   afp:'afp on the nomad form and afp_count on the search and biker forms, published under the names ' +
   'the source gives them. AFP surveillance has its own section on this dashboard built from the ' +
   'case-based line list; this is only what these team forms wrote down.',
   aef:'aefi and aefi_count, with the same caveat as the column beside it.'};
  const CL=i=>mv?MT.m[i][yi*12+mv-1]:MT.y[i][yi];
  const LV=k=>(OWN[k]||[]).some(s=>SP[s]);
  const V=(i,k)=>{if(!LV(k))return null; const a=MM[k];
   if(!one){let t=0; const yb=MT.y[i]||{}; Object.keys(yb).forEach(j=>{t+=(yb[j][a]||0);}); return t;}
   const c=CL(i); return c?(c[a]||0):0;};
  const d0=v=>v==null?'\u2013':fmt(v);
  const EIX=(id,suf)=>{const p=MTM.ek.indexOf(id+suf); return p<0?null:p;};
  // a column is written by one or more forms, so its tooltip says which and over what months each ran
  const TT=k=>LBL[k]+' \u00b7 '+(OWN[k]||[]).map(s=>FL[s].label+', filed '+MTM.spans[s]).join('; ')+
   '. Summed over rows recorded '+(one?SLab:('in '+MTM.win))+'. '+(X[k]||'')+
   ' A dash means none of those forms was being filed in the period picked.';
  const RC=MTM.forms.map(f=>f.id+'R');
  const SCOPE=DI.filter(i=>MT.y[i]);
  const UN=(i,p)=>{if(one||p==null)return null; const e=MT.e[i]; return e?(e[1+p]||0):null;};
  const SUMU=p=>{if(p==null||one)return null; let t=0;
   SCOPE.forEach(i=>{const v=UN(i,p); if(v)t+=v;}); return t;};
  const FR=MTM.forms.map(f=>{const rk=f.id+'R'; let rec=0, dd=0;
   SCOPE.forEach(i=>{const v=V(i,rk); if(v){rec+=v; dd++;}});
   return {id:f.id, label:f.label, row:f.row, span:f.span, whole:fmt(f.rows),
    rec:SP[f.id]?rec:null, dist:SP[f.id]?dd:null,
    teams:SUMU(EIX(f.id,'Tm')), ucs:SUMU(EIX(f.id,'Uc')),
    cols:f.cols.filter(c=>c!==rk).map(c=>LBL[c]).join(', ')||'nothing but the row count'};});
  const DR=SCOPE.map(i=>{const o={i:i, dn:PTP.ds[i], dv:PTP.dv[i]};
   MTM.mk.forEach(k=>{o[k]=V(i,k)});
   let t=0, any=false; RC.forEach(k=>{const v=o[k]; if(v!=null){any=true; t+=v;}});
   o.all=any?t:null;
   let tm=null; MTM.forms.forEach(f=>{const v=UN(i,EIX(f.id,'Tm')); if(v!=null)tm=(tm||0)+v;});
   o.tm=tm; return o;});
  drawTable('tMTf',[
   {k:'label', l:'Form', f:x=>'<b>'+esc(x.label)+'</b>'},
   {k:'row', l:'One row is', tt:'How the export is keyed. Every number in the table below counts rows ' +
    'of these forms, so a busy district can file many rows about the same team or the same household, ' +
    'and no column here is a count of distinct children.'},
   {k:'rec', l:'Rows filed', n:1, f:x=>d0(x.rec),
    tt:'Rows kept for this form '+(one?SLab:('in '+MTM.win))+', after the source\'s own archive flag '
     +'and its repeated unique_ids are dropped - read it as a filing volume, not a count of children.'},
   {k:'dist', l:'Districts filing', n:1, f:x=>d0(x.dist),
    tt:'District units in scope with at least one row of this form in the period picked. The six forms '
     +'do not reach the same districts, so a dash in one column against figures in another means that '
     +'form was not being filed there.'},
   {k:'span', l:'Filed between', tt:'The months this form was actually being written into IDIMS. All ' +
    'six were pulled on '+MTM.asof+' and nothing after that is in the files.'},
   {k:'teams', l:'Teams (within district)', n:1, f:x=>d0(x.teams),
    tt:'Distinct team numbers inside their own district, summed over the districts in scope. The '
     +'numbers repeat across districts - the nomad form holds '+fmt(MTM.n.nomad.teams_any)+' distinct '
     +'numbers province-wide against '+fmt(MTM.n.nomad.teams)+' district-scoped, the biker form '+
     fmt(MTM.n.biker.teams_any)+' against '+fmt(MTM.n.biker.teams)+' - because the export carries no '
     +'province-wide team id, so this is a sum of district counts, not a headcount of teams. Blank in '
     +'a period view: a team that worked in two months is one team.'},
   {k:'ucs', l:'Union councils', n:1, f:x=>d0(x.ucs),
    tt:'Distinct uc_name values inside their own district, summed over the districts in scope. Blank '
     +'in a period view for the same reason as the column beside it.'},
   {k:'cols', l:'Columns it carries',
    tt:'Which of the district table\'s columns this form writes. A column with one form behind it is '
     +'that form\'s total; AFP and AEFI are written by three of the six.'}],
   FR, 'rec', -1);
  drawTable('tMTd',[
   {k:'dn', l:'District', f:x=>'<b>'+esc(x.dn)+'</b>'},
   {k:'dv', l:'Division'},
   {k:'all', l:'Forms filed', n:1, f:x=>d0(x.all),
    tt:'The six per-form row columns added together - a count of forms filed in this district, never '
     +'of children reached. Of the '+PTP.ds.length+' district units that report at a transit point, '+
     SCOPE.length+' appear in at least one of the six mobile-team exports.'},
   {k:'tm', l:'Teams (district)', n:1, f:x=>d0(x.tm),
    tt:'Team numbers recorded inside this district, added across the forms that record them - a number '
     +'used by both a nomad and a search team counts twice, and the same number in two districts '
     +'counts once in each. Blank in a period view, because the union is only published over '+MTM.win},
   {k:'mapR', l:'Mapping records', n:1, f:x=>d0(x.mapR), tt:TT('mapR')},
   {k:'pkf', l:'Pakistan-origin', n:1, f:x=>d0(x.pkf), tt:TT('pkf')},
   {k:'afg', l:'Afghan-origin', n:1, f:x=>d0(x.afg), tt:TT('afg')},
   {k:'nomadR', l:'Nomad reports', n:1, f:x=>d0(x.nomadR), tt:TT('nomadR')},
   {k:'mna', l:'Missed: not available', n:1, f:x=>d0(x.mna), tt:TT('mna')},
   {k:'mrf', l:'Missed: refusal', n:1, f:x=>d0(x.mrf), tt:TT('mrf')},
   {k:'z2', l:'Under-2 zero-dose', n:1, f:x=>d0(x.z2), tt:TT('z2')},
   {k:'epc', l:'EPI cards issued', n:1, f:x=>d0(x.epc), tt:'epi_card_issued on the nomad form, summed ' +
    'over its rows - a count of cards a team wrote down, not of children holding one. Filed '
    +(one?(SP.nomad?SLab:('not being filed in '+SLab)):(MTM.spans.nomad+'.'))},
   {k:'nomonR', l:'Nomad checklists', n:1, f:x=>d0(x.nomonR), tt:TT('nomonR')},
   {k:'sactR', l:'Search reports', n:1, f:x=>d0(x.sactR), tt:TT('sactR')},
   {k:'sp', l:'Sessions planned', n:1, f:x=>d0(x.sp), tt:TT('sp')},
   {k:'sc', l:'Sessions conducted', n:1, f:x=>d0(x.sc), tt:TT('sc')},
   {k:'smonR', l:'Search checklists', n:1, f:x=>d0(x.smonR), tt:TT('smonR')},
   {k:'bikerR', l:'Biker reports', n:1, f:x=>d0(x.bikerR), tt:TT('bikerR')},
   {k:'bn', l:'NA recorded', n:1, f:x=>d0(x.bn), tt:TT('bn')},
   {k:'bs', l:'Still NA', n:1, f:x=>d0(x.bs), tt:'still_na on the biker form - children still not ' +
    'available when the team came back. 5,982 of its rows reconcile against the column beside it and ' +
    '13 exceed it.'},
   {k:'rn', l:'Refusals recorded', n:1, f:x=>d0(x.rn), tt:TT('rn')},
   {k:'rs', l:'Still refusing', n:1, f:x=>d0(x.rs), tt:TT('rs')},
   {k:'afp', l:'AFP cases', n:1, f:x=>d0(x.afp), tt:TT('afp')},
   {k:'aef', l:'AEFI events', n:1, f:x=>d0(x.aef), tt:TT('aef')}],
   DR, 'all', -1);
  const SW2=one?SLab:MTM.win;
  el('cntMTf').textContent=DR.length+' district units in the six mobile-team exports \u00b7 '+SW2
   +' \u00b7 all six were pulled '+MTM.asof;
  const DRS=f=>{const d=MTM.n[f].drop||{};
   return Object.keys(d).map(k=>fmt(d[k])+' '+k).join(', ')||'nothing'};
  const DQ=(f,k)=>fmt((MTM.n[f].dq||{})[k]||0);
  const GL=f=>(MTM.gap[f]||[]).map(g=>_MON[(+g.slice(5,7))-1]+'/'+g.slice(0,4)).join(', ');
  const GAPS=MTM.forms.filter(f=>(MTM.gap[f.id]||[]).length);
  const NEG=(function(){let n=0, w='';
   MTM.forms.forEach(f=>{const d=MTM.n[f.id].dq||{};
    Object.keys(d).forEach(k=>{if(/is negative$/.test(k)){n+=d[k]; w=f.label+' '+k;}});});
   return {n:n, w:w};})();
  el('capMTf').textContent=[
   'These are the six HRMP forms about mobile and migrant teams that were pulled from IDIMS on '+
    MTM.asof+', the same day as the three transit-point field checks above and never re-pulled since: '
    +'a mapping form for households on the move, activity reports from nomad teams, search teams and '
    +'the special biker teams, and one monitoring checklist each for the nomad and search teams. They '
    +'sit on the same district index and the same month slots as the transit-point tables, so the '
    +'Reporting period control scopes all four grids together.',
   'All six stopped being filed long before the daily reports did: '+MTM.forms.map(f=>f.label+' '
    +MTM.spans[f.id]).join(', ')+', while the daily panel runs to '+LM+'. A period after a form '
    +'stopped shows \u2013 with that form\'s span in its tooltip, never a zero'+(one?', and the period '
    +'picked here is '+SLab+'.':', so the whole-window view is the only one in which every column is ' +
    'filled in.'),
   'How far each form went: '+MTM.forms.map(f=>f.label+' in '+fmt(f.districts)+' districts and '+
    fmt(f.ucs)+' union councils'+(f.teams?(' on '+fmt(f.teams)+' team numbers scoped to their own ' +
    'district'):', recording no team number')).join('; ')+'. The team and union-council columns are '
    +'sums of district-scoped unions, not province-wide headcounts: the nomad form holds '+
    fmt(MTM.n.nomad.teams_any)+' distinct team numbers across KP against '+fmt(MTM.n.nomad.teams)+
    ' once scoped to their district, and the biker form '+fmt(MTM.n.biker.teams_any)+' against '+
    fmt(MTM.n.biker.teams)+', because the export carries no province-wide team id. Both go blank in a '
    +'period view, because a team that worked in two months is still one team.',
   'Every month here is the month the entry was made. Three of the six forms also carry a separate '
    +'activity date, and it disagrees with the entry month often enough that one uniform rule was the '
    +'only honest one: '+DQ('sact','activity month and entry month differ')+' search-team rows, '+
    DQ('smon','activity month and entry month differ')+' search checklists and '+
    DQ('biker','activity month and entry month differ')+' biker rows were entered in a different month '
    +'from the visit, and '+DQ('sact','activity date after the export was taken')+' search row is '
    +'dated after the export itself was taken. Rows are never re-dated.',
   'How the rows were kept: '+MTM.forms.map(f=>'of '+fmt(MTM.n[f.id].read)+' '+f.label+' rows read, '
    +DRS(f.id)+' was dropped and '+fmt(MTM.n[f.id].kept)+' kept').join('; ')+'. Archived rows are the '
    +'source\'s own is_archive flag, not a judgement made here. The mapping form also carries two rows '
    +'under a district spelling that is not on the KP district index (KOLAIPALAS); they are dropped '
    +'under that named reason rather than guessed onto a district.',
   'Where the forms disagree with themselves, published as found: '+
    DQ('biker','team_no and team_n0 disagree')+' of '+fmt(MTM.n.biker.kept)+' biker rows write '
    +'different values in team_no and team_n0, the two spellings of the same field; '+
    DQ('biker','still-not-available exceeds recorded not-available')+' record more children still not '
    +'available than were recorded not available and '+
    DQ('biker','still-refusal exceeds recorded refusal')+' do the same for refusals; '+
    DQ('sact','sessions conducted exceed sessions planned')+' search rows conduct more sessions than '
    +'they planned. The mapping form reaches '+fmt(MTM.n.map.districts)+' district units but the '
    +'search-team form only '+fmt(MTM.n.sact.districts)+', so a dash in one column beside figures in '
    +'another means that form was not being filed there, not that no mobile team worked there.',
   NEG.n?('A published count cannot go negative, and one cell did: '+esc(NEG.w)+', a search-team row '
    +'at Peshawar writing session_conducted = -2. The visit happened, so the row and its other columns '
    +'stand and that single cell is voided, which makes Sessions conducted the sum of the usable '
    +'values rather than the raw column total.')
    :'No published count column carries a negative value in this pull.',
   GAPS.length?('Inside their own spans these forms have holes: '+GAPS.map(f=>f.label+' has nothing '
    +'filed anywhere in KP in '+GL(f.id)).join('; ')+'.')
    :'Inside their own spans every month slot of all six forms carries at least one row somewhere in KP.',
   'What these exports also carry and this table does not publish: the target_* and coverage_* columns, '
    +'the same field family the transit-point panel still holds out pending the IDIMS report '
    +'definition \u2014 in these files they are child counts rather than percentages, but coverage '
    +'exceeds target in 4,245 of 103,143 search-team rows and one target_ipv_1 is -3, so nothing built '
    +'on them is published while that question is open. Also held out: the bare dose columns, empty in '
    +'every live search-team row and sitting on the nomad form beside three mutually inconsistent OPV '
    +'tallies (vacc_opv 203,129 against opv_does1+2+3 192,307 against target_opv 245,337); the mapping '
    +'form\'s no_of_families and no_of_child, whose median is 3 but where 906 rows claim more than 100 '
    +'children and one claims 7,640, a tail holding a fifth of the province sum; every integer answer '
    +'code with no caption (mmp_types 1-10, hrmp_type 1-12, riadmin, team_planned 0/1/8, and the '
    +'checklist item block, whose item columns are blank in every row of both monitoring checklists); '
    +'duration, which reaches 100,000,000; mob_pop_card_issued, 3,134 in a single session; and every '
    +'surveyor, monitor, focal person, AIC and team member name, email, designation, CNIC-derived '
    +'field, settlement and area name, free-text remark and per-row coordinate, because this is a '
    +'public site.',
   'Read every figure here as a count of forms, and of what those forms wrote down. None of it is a '
    +'coverage measure and none of it can be turned into one, so no percentage appears in this block - '
    +'the same standing rule as the field-check table above. District rows sort by forms filed, largest '
    +'first, and the Division and District filters scope every row of both tables.'
  ].join(' ');
  const CK=['all','tm','mapR','pkf','afg','nomadR','mna','mrf','z2','epc','nomonR','sactR','sp','sc',
   'smonR','bikerR','bn','bs','rn','rs','afp','aef'];
  const CH=['Forms filed','Teams (within district)','Mapping records','Pakistan-origin',
   'Afghan-origin','Nomad team reports','Missed: not available','Missed: refusal',
   'Under-two zero-dose recorded','EPI cards issued','Nomad team checklists','Search team reports',
   'Sessions planned','Sessions conducted','Search team checklists','Biker team reports',
   'Not available recorded','Still not available','Refusals recorded','Still refusing',
   'AFP cases','AEFI events'];
  el('btnMTf').onclick=()=>csvDownload('hrmp_mobile_migrant_teams_'+(one?(mv?(yv+'-'+mv):('y'+yv))
    :MTM.win)+'_'+_slug()+'.csv', ['Division','District'].concat(CH),
   DR.map(x=>[x.dv,x.dn].concat(CK.map(k=>x[k]==null?'':x[k]))));
  }
 }
"""


def strip_js(block):
    """Blank out string literals and comments, so bracket counting sees only real code."""
    out, i, n = [], 0, len(block)
    while i < n:
        c = block[i]
        if c in "'\"":
            j = i + 1
            while j < n and block[j] != c:
                j += 2 if block[j] == chr(92) else 1
            out.append("''")
            i = j + 1
            continue
        if c == '/' and i + 1 < n and block[i + 1] == '/':
            while i < n and block[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and block[i + 1] == '*':
            k = block.find('*/', i)
            i = n if k < 0 else k + 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def check_js(v, name, block):
    """Two failure modes this patch has already produced once: a bracket left open, and two string
    literals side by side with no + between them (valid Python, a syntax error in JS)."""
    pairs, stack = {'(': ')', '[': ']', '{': '}'}, []
    for ch in strip_js(block):
        if ch in pairs:
            stack.append(ch)
        elif ch in pairs.values():
            v.require(bool(stack) and pairs[stack[-1]] == ch,
                      '%s: a %r closes nothing (depth %d)' % (name, ch, len(stack)))
            stack.pop()
    v.require(not stack, '%s: %d bracket(s) left open: %s' % (name, len(stack), ''.join(stack)))
    lines = block.split('\n')
    for k in range(len(lines) - 1):
        a, b = lines[k].rstrip(), lines[k + 1].lstrip()
        v.require(not (a.endswith("'") and not a.endswith(chr(92) + "'") and b.startswith("'")),
                  '%s: line %d ends a string and line %d starts another with no + between them'
                  % (name, k + 1, k + 2))


def patch(v, js, obj):
    check_js(v, 'CACHE', CACHE)
    check_js(v, 'RENDER', RENDER)
    t = v.text
    for nm, a in (('const', A_CONST), ('card', A_CARD), ('cache', A_CACHE),
                  ('render', A_RENDER), ('hint', A_HINT)):
        v.require(t.count(a) == 1, 'anchor occurs %d times (want 1) [%s]: %r'
                  % (t.count(a), nm, a[:56]))
    v.require('const MTM' not in t and 'id="cMTf"' not in t, 'MTM block already patched in')
    # the download has to match the grid column for column, or the CSV reorders the data against its
    # own header with nothing on screen saying so
    names = [x.strip().strip("'") for x in
             re.search(r"const CK=\[(.*?)\];", RENDER, re.S).group(1).split(',')]
    v.require(sorted(names) == sorted(['all', 'tm'] + obj['mk']),
              'the CSV key list and MTM.mk are not the same columns: %s vs %s'
              % (names, obj['mk']))
    heads = [x.strip() for x in
             re.search(r"const CH=\[(.*?)\];", RENDER, re.S).group(1).split(',')]
    v.require(len(heads) == len(names), 'the CSV has %d keys but %d headers'
              % (len(names), len(heads)))
    # every measure has to reach the grid, otherwise a column exists in the payload and not on screen
    for k in obj['mk']:
        v.require(re.search(r"\{k:'%s'," % k, RENDER) is not None, 'column %s is not drawn' % k)
    t = t.replace(A_CONST, 'const MTM = %s;\r\n' % js + A_CONST)
    t = t.replace(A_CARD, A_CARD + CARD)
    t = t.replace(A_CACHE, CACHE.replace('\n', '\r\n') + A_CACHE)
    t = t.replace(A_RENDER, RENDER.replace('\n', '\r\n') + A_RENDER)
    t = t.replace(A_HINT, HINT_NEW)
    v.text = t
    v.changes.append('MTM mobile-team block + renderer (%+d chars)' % v.delta())
    dashpatch.assert_crlf(v)
    for once in ('const MTM = {', 'function mtmTab(){', 'hrmp_mobile_migrant_teams_',
                 'id="cMTf"', "drawTable('tMTf'", "drawTable('tMTd'", "el('capMTf')",
                 "el('cntMTf')", "el('btnMTf')"):
        v.require(t.count(once) == 1, '%s occurs %d times (want 1)' % (once, t.count(once)))
    for needle in ('id="tMTf"', 'id="tMTd"', 'id="capMTf"', 'Forms filed', 'Still not available',
                   'KOLAIPALAS', "MTC.style.display='none'", "DR, 'all', -1", "FR, 'rec', -1",
                   'target_opv 245,337', 'session_conducted = -2'):
        v.require(t.count(needle) >= 1, '%s is missing' % needle)
    # both HRMP blocks have to sit between the coverage grid and the district inventory
    v.require(t.index('id="capPTm"') < t.index('id="cMTf"') < t.index('id="tPTa"'),
              'the mobile-team card is not between the field-check card and the district inventory')
    v.require(t.index('const PTPM = ') < t.index('const MTM = ') < t.index('const SURVW = '),
              'MTM const must sit between PTPM and SURVW')
    v.require(t.index("drawTable('tPTm'") < t.index("drawTable('tMTf'"),
              'the mobile-team render must follow the field-check render')
    v.require(t.index('function mtmTab(){') < t.index('function ptBadge(){'),
              'mtmTab must sit with the other PTP cache helpers')


def main():
    if not os.path.exists(PAYLOAD):
        raise SystemExit('missing %s - run _refresh/extract_mtm.py first' % PAYLOAD)
    obj = json.loads(srcutil.read_text(PAYLOAD))
    js = srcutil.dumps(obj)
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    patch(v, js, obj)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('payload MTM %d chars, %d forms, %d districts with mobile-team data, %d measures, %d '
          'held-out groups' % (len(js), len(obj['forms']), len(obj['ds']), len(obj['mk']),
                               len(obj['hold'])))
    print('OK mtm-ui master only - the other three variants are synced by push_master.py, which '
          "needs the owner's word")


if __name__ == '__main__':
    main()
