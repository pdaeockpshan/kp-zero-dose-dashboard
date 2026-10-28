"""Read the morning-report returns from a shared district sheet as well as the Google Form.

The form posts only when the phone has a live connection, which is the failure the districts
report. The intake workbook built by mdp_sheet_intake.py gives every district-day its own
pre-filled row in a Google Sheet, so a district types counts offline and the row syncs later.
This module teaches the feed to read that tab too, merge it with the form responses on
district + day (later time of update wins) and say which channels were read.

MDP_FEED.gridId stays empty until the owner creates the sheet; with it empty the feed behaves
exactly as before, so this patch is inert until the id is filled in. Master only: push_master.py
derives the other three variants.
Idempotent: a block already carrying its new text is skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CMT_OLD = '''// ---------- Live feed: the district morning form ----------
// Districts submit the Google Form during the campaign; every response lands on the linked response
// sheet's first tab, which is shared view-only so this page can read it as CSV. The site is public, so
// the form asks for counts only - no name, no free text - and nothing here reads a person-identifying
// column. The sheet's own Timestamp is the "time of update", so a resubmission replaces the earlier
// row for the same district and day.'''

CMT_NEW = '''// ---------- Live feed: the district morning form and the shared district sheet ----------
// Districts file the Google Form, or type into their own row of the shared district sheet where the
// connection is poor. Both are read as CSV by this page and merged on district + day, later time of
// update wins. The site is public, so both carry counts only - no name, no free text - and nothing
// here reads a person-identifying column.'''

FEED_OLD = '''const MDP_FEED={
 camp:'NOV-26',
 id:'12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE',
 tab:'Form Responses 1',
 form:'https://docs.google.com/forms/d/1UnWmFlLedcMJyz8ttlHb669IYZZWoS_obPtMw-7jx-U/viewform',
 sheet:'https://docs.google.com/spreadsheets/d/12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE/edit',
 cache:'kpMDP.live.NOV-26'
};'''

FEED_NEW = '''// Two intake channels for this campaign: the Google Form (read from its response sheet) and the
// shared district sheet, whose rows are pre-filled one per district and campaign day. gridId stays
// empty until that workbook is created; empty means the form is the only reader.
const MDP_FEED={
 camp:'NOV-26',
 id:'12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE',
 tab:'Form Responses 1',
 gridId:'',
 gridTab:'Live',
 form:'https://docs.google.com/forms/d/1UnWmFlLedcMJyz8ttlHb669IYZZWoS_obPtMw-7jx-U/viewform',
 sheet:'https://docs.google.com/spreadsheets/d/12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE/edit',
 cache:'kpMDP.live.NOV-26'
};
const mdpFeedSrcs=()=>{
 const s=[{k:'form',id:MDP_FEED.id,tab:MDP_FEED.tab,l:'form'}];
 if(MDP_FEED.gridId)s.push({k:'grid',id:MDP_FEED.gridId,tab:MDP_FEED.gridTab,l:'sheet'});
 return s;};'''

STAMP_OLD = '''const mdpFeedStamp=ts=>{const p=Date.parse(String(ts||'').replace(/\\s+/g,' '));
 if(isFinite(p))return p;const m=mdpMin(mdpFeedTime(ts));return m==null?0:m;};'''

STAMP_NEW = STAMP_OLD + '''
// A form row carries a full date and time; a sheet row usually only HH:MM. Compare milliseconds
// only when both parse as dates, otherwise compare minutes of day - never mix the two scales.
const mdpFeedCmp=(a,b)=>{
 const A=Date.parse(String(a||'').replace(/\\s+/g,' ')),B=Date.parse(String(b||'').replace(/\\s+/g,' '));
 if(isFinite(A)&&isFinite(B))return A-B;
 const x=mdpMin(mdpFeedTime(a)),y=mdpMin(mdpFeedTime(b));
 return (x==null?-1:x)-(y==null?-1:y);};'''

LIVE_OLD = "let MDLIVE={raw:{},at:0,n:0,miss:0,sup:0,err:'',busy:0};"
LIVE_NEW = "let MDLIVE={raw:{},at:0,n:0,miss:0,sup:0,err:'',warn:'',src:'',busy:0};"

PARSE_OLD = '''function mdpFeedParse(t){
 const g=mdpFeedCsv(t);'''

PARSE_NEW = '''function mdpFeedParse(t,opt){
 const g=mdpFeedCsv(t);'''

COUNT_OLD = ''' const rows={};let miss=0,sup=0;
 if(!ix.n||!ix.day)return {rows:rows,n:0,miss:0,sup:0,badHdr:1};'''

COUNT_NEW = ''' const rows={};let miss=0,sup=0,blank=0;
 if(!ix.n||!ix.day)return {rows:rows,n:0,miss:0,sup:0,badHdr:1};
 const grid=!!(opt&&opt.grid);
 // The district sheet arrives with every district-day row pre-filled (division, district, day), so a
 // row counts only once the district has typed a time or a number; identity alone means "not filed"
 // and must not be reported as an unmatched row.
 const hasV=(a,r)=>{if(!a)return false;
  for(let q=0;q<a.length;q++){if(String(r[a[q]]==null?'':r[a[q]]).trim()!=='')return true;}return false;};'''

SKIP_OLD = '''  const jd=pick(ix.day,r),day=jd!=null?Math.round(mdpNumV(r[jd])):0;
  if(!(day>=1)||day>MDP_MAXD){miss++;continue;}'''

SKIP_NEW = '''  const jd=pick(ix.day,r),day=jd!=null?Math.round(mdpNumV(r[jd])):0;
  if(!(day>=1)||day>MDP_MAXD){miss++;continue;}
  if(grid&&!hasV(ix.ts,r)&&!hasV(ix.ucp,r)&&!hasV(ix.ucr,r)&&!hasV(ix.inc,r)
   &&!MDP_TYPES.some((x,k)=>hasV(ix['p'+k],r)||hasV(ix['d'+k],r))){blank++;continue;}'''

TIE_OLD = "  if(old){sup++;if(mdpFeedStamp(old.ts)>=mdpFeedStamp(ts))continue;}"
TIE_NEW = "  if(old){sup++;if(mdpFeedCmp(old.ts,ts)>=0)continue;}"

RET_OLD = " return {rows:rows,n:Object.keys(rows).length,miss:miss,sup:sup};"
RET_NEW = " return {rows:rows,n:Object.keys(rows).length,miss:miss,sup:sup,blank:blank};"

RESTORE_OLD = '''  if(d&&d.raw&&d.at){MDLIVE.raw=d.raw;MDLIVE.at=d.at;MDLIVE.n=d.n||0;MDLIVE.miss=d.miss||0;MDLIVE.sup=d.sup||0;}}catch(e){}'''
RESTORE_NEW = '''  if(d&&d.raw&&d.at){MDLIVE.raw=d.raw;MDLIVE.at=d.at;MDLIVE.n=d.n||0;MDLIVE.miss=d.miss||0;MDLIVE.sup=d.sup||0;
   MDLIVE.src=d.src||'';MDLIVE.warn=d.warn||'';}}catch(e){}'''

LOAD_NEW = '''const mdpFeedUrl=s=>'https://docs.google.com/spreadsheets/d/'+s.id+'/gviz/tq?tqx=out:csv&sheet='
 +encodeURIComponent(s.tab)+'&_='+Date.now();
// Both channels are read in turn and merged on district + day, so a district that files the form at
// 08:10 and edits its sheet row at 08:25 shows 08:25; a channel that fails does not hide the other.
async function mdpFeedLoad(){
 if(MDLIVE.busy||MDC!==MDP_FEED.camp)return;
 MDLIVE.busy=1;MDLIVE.lastTry=Date.now();mdpFeedChip();
 const srcs=mdpFeedSrcs(),all={},errs=[],ok=[];
 let miss=0,sup=0;
 for(const s of srcs){
  try{
   const r=await fetch(mdpFeedUrl(s),{cache:'no-store'});
   if(!r.ok)throw new Error('HTTP '+r.status);
   const t=await r.text();
   if(!/^\\s*"?Timestamp/i.test(t))throw new Error('not readable - share it "anyone with the link, viewer"');
   const o=mdpFeedParse(t,{grid:s.k==='grid'});
   if(o.badHdr)throw new Error('the District and Campaign day columns are missing');
   ok.push(s.l);miss+=o.miss;sup+=o.sup||0;
   Object.keys(o.rows).forEach(k=>{const nr=o.rows[k],old=all[k];
    if(!old){all[k]=nr;return;}
    if(mdpFeedCmp(old.ts,nr.ts)<0)all[k]=nr;
    sup++;});
  }catch(e){errs.push(s.l+' '+String((e&&e.message)||e));}
 }
 if(ok.length){
  MDLIVE.raw=all;MDLIVE.n=Object.keys(all).length;MDLIVE.miss=miss;MDLIVE.sup=sup;
  MDLIVE.at=Date.now();MDLIVE.err='';MDLIVE.src=ok.join(' + ');
  MDLIVE.warn=errs.length?'read failed for '+errs.join(' · '):'';
  try{localStorage.setItem(MDP_FEED.cache,JSON.stringify({at:MDLIVE.at,raw:all,n:MDLIVE.n,
   miss:miss,sup:sup,src:MDLIVE.src,warn:MDLIVE.warn}));}catch(e){}
 }else{
  MDLIVE.err=errs.join(' · ');
 }
 MDLIVE.busy=0;mdpFeedChip();
 try{renderMDEP();renderMDPBar();}catch(e){console.error('mdep feed render',e);}
}
'''

CHIP_NEW = '''function mdpFeedChip(){
 const b=el('mdpFeed');if(!b)return;
 const cls=c=>{b.className='btn mdpfeed '+c;};
 if(MDC!==MDP_FEED.camp){
  b.disabled=true;b.textContent='Sheet feed · no form for this campaign';cls('off');
  b.title='Only the current campaign has the online district form';return;}
 b.disabled=false;
 const two=mdpFeedSrcs().length>1;
 if(MDLIVE.busy){b.textContent='Sheet feed · reading…';cls('wait');b.title='Reading the district returns';return;}
 if(MDLIVE.err&&!MDLIVE.at){
  b.textContent='Sheet feed · read failed · retry';cls('bad');
  b.title='Could not read the returns: '+MDLIVE.err;return;}
 if(!MDLIVE.at){b.textContent='Sheet feed · not read yet';cls('wait');b.title='Click to read the district returns';return;}
 const t=new Date(MDLIVE.at),stale=Date.now()-MDLIVE.at>900000;
 b.textContent='Sheet feed · read '+mdpPad(t.getHours())+':'+mdpPad(t.getMinutes())+' · '
  +MDLIVE.n+' district-day'+(MDLIVE.n===1?'':'s')
  +(MDLIVE.sup?' · '+MDLIVE.sup+' duplicate row'+(MDLIVE.sup===1?'':'s')+' dropped':'')
  +(MDLIVE.miss?' · '+MDLIVE.miss+' unmatched':'')
  +(two&&MDLIVE.src?' · '+MDLIVE.src:'');
 cls(MDLIVE.warn?'stale':'ok'+(stale?' stale':''));
 b.title='District returns, one row per district and day (the later time of update wins)'
  +(two?' · sources: '+MDLIVE.src:' · source: Google Form responses')
  +(MDLIVE.warn?' · '+MDLIVE.warn:'')
  +(stale?' · last read more than 15 minutes ago, click to read again':' · click to read again');
}
'''

BIND_OLD = " ['mdpFormA','mdpSheetA'].forEach((id,i)=>{const a=el(id);if(a)a.href=i?MDP_FEED.sheet:MDP_FEED.form;});"

BIND_NEW = ''' ['mdpFormA','mdpSheetA'].forEach((id,i)=>{const a=el(id);if(a)a.href=i?(MDP_FEED.gridId?'https://docs.google.com/spreadsheets/d/'+MDP_FEED.gridId+'/edit':MDP_FEED.sheet):MDP_FEED.form;});
 const ga=el('mdpSheetA');
 if(ga)ga.textContent=MDP_FEED.gridId?'District sheet':'Response sheet';
 const gc=el('mdpGridCap');
 if(gc){gc.style.display=MDP_FEED.gridId?'':'none';
  if(MDP_FEED.gridId)gc.innerHTML='<b>District sheet:</b> every district-day row is already in the sheet, so a district only types its time of update and its counts. It can file there instead of the form, it works offline in the Sheets app, and whichever of the two arrives later wins.';}'''

CAP_OLD = '''<div class="mdpwa">Districts fill the <b>online morning form</b> during the campaign and the tab reads their answers from the response sheet by itself:'''
CAP_NEW = '''<div class="cap" id="mdpGridCap" style="display:none"></div>
<div class="mdpwa">Districts fill the <b>online morning form</b>, or update their own row in the shared district sheet, during the campaign, and the tab reads their answers by itself:'''

DEL_OLD = "'That report came from the online form - remove its row in the response sheet'"
DEL_NEW = "'That report came from the online form or the sheet - remove its row there'"

CLR_OLD = "'Reports submitted through the online form are not touched - remove those rows in the response sheet.'"
CLR_NEW = "'Reports submitted through the form or the sheet are not touched - remove those rows there.'"

NOTE_OLD = ('Districts fill the online morning form during the campaign; their answers land on the response '
            'sheet and the tab reads that sheet when it opens, keeping the latest submission for each '
            'district and day by the sheet Timestamp.')
NOTE_NEW = ('Districts fill the online morning form, or edit their own row in the shared district sheet where '
            'the connection is poor; both are read when the tab opens and the later time of update wins for '
            'each district and day.')

PRIV_OLD = 'The form and its response sheet are public because this page is public: they carry district counts only, plus a fixed reason list, and no free-text question exists.'
PRIV_NEW = 'The form, its response sheet and the district sheet are public because this page is public: they carry district counts only, plus a fixed reason list, and neither has a free-text column.'

STORE_OLD = 'Form answers live in the Google response sheet, which this page only reads.'
STORE_NEW = 'Form answers and sheet rows live in Google, which this page only reads.'

BAR_OLD = "'Districts submit the <b>online morning form</b>; its answers are read from the response sheet '"
BAR_NEW = "'Districts submit the <b>online morning form</b> or update their row in the shared district sheet; both are read '"

BAR2_OLD = "'latest submission per district and day. Typed or imported reports stay in this browser. '"
BAR2_NEW = "'the latest time of update per district and day. Typed or imported reports stay in this browser. '"

# Applied after the splices, because LOAD_NEW and CHIP_NEW already carry the corrected text: on a
# fresh run there is nothing to replace, on an incremental run the earlier version is upgraded.
MERGE_OLD = '''    if(!old){all[k]=nr;return;}
    if(mdpFeedCmp(old.ts,nr.ts)<0){all[k]=nr;sup++;}});'''
MERGE_NEW = '''    if(!old){all[k]=nr;return;}
    if(mdpFeedCmp(old.ts,nr.ts)<0)all[k]=nr;
    sup++;});'''

CHIPW_OLD = "  +(MDLIVE.sup?' · '+MDLIVE.sup+' resubmission'+(MDLIVE.sup===1?'':'s')+' replaced':'')"
CHIPW_NEW = "  +(MDLIVE.sup?' · '+MDLIVE.sup+' duplicate row'+(MDLIVE.sup===1?'':'s')+' dropped':'')"

BINDW_OLD = ''' const ga=el('mdpSheetA');
 if(ga&&MDP_FEED.gridId)ga.textContent='District sheet';
 const gc=el('mdpGridCap');
 if(gc&&MDP_FEED.gridId){gc.style.display='';'''
BINDW_NEW = ''' const ga=el('mdpSheetA');
 if(ga)ga.textContent=MDP_FEED.gridId?'District sheet':'Response sheet';
 const gc=el('mdpGridCap');
 if(gc){gc.style.display=MDP_FEED.gridId?'':'none';
  if(MDP_FEED.gridId)'''

# mdpFeedStamp only ever compared two timestamps on one scale; mdpFeedCmp replaced it.
STAMP_DEL = '''const mdpFeedStamp=ts=>{const p=Date.parse(String(ts||'').replace(/\\s+/g,' '));
 if(isFinite(p))return p;const m=mdpMin(mdpFeedTime(ts));return m==null?0:m;};
'''

POST_FIXES = [(MERGE_OLD, MERGE_NEW), (CHIPW_OLD, CHIPW_NEW), (BINDW_OLD, BINDW_NEW)]

# A block already carrying one of these has been moved past the FIXES stage by an earlier run.
SUPERSEDED = [BINDW_NEW]

FIXES = [
    (CMT_OLD, CMT_NEW),
    (FEED_OLD, FEED_NEW),
    (STAMP_OLD, STAMP_NEW),
    (LIVE_OLD, LIVE_NEW),
    (PARSE_OLD, PARSE_NEW),
    (COUNT_OLD, COUNT_NEW),
    (SKIP_OLD, SKIP_NEW),
    (TIE_OLD, TIE_NEW),
    (RET_OLD, RET_NEW),
    (RESTORE_OLD, RESTORE_NEW),
    (BIND_OLD, BIND_NEW),
    (CAP_OLD, CAP_NEW),
    (DEL_OLD, DEL_NEW),
    (CLR_OLD, CLR_NEW),
    (NOTE_OLD, NOTE_NEW),
    (PRIV_OLD, PRIV_NEW),
    (STORE_OLD, STORE_NEW),
    (BAR_OLD, BAR_NEW),
    (BAR2_OLD, BAR2_NEW),
]

# Whole functions are spliced between markers rather than matched line by line.
SPLICES = [
    ('function mdpFeedUrl(){', '// Read on opening the tab', LOAD_NEW, 'const mdpFeedUrl=s=>'),
    ('function mdpFeedChip(){', 'mdpFeedRestore();', CHIP_NEW, 'const two=mdpFeedSrcs().length>1;'),
]


def splice(text, start, end, new, marker):
    if marker in text:
        print('  skip (already applied): %s' % start)
        return text, 0
    if text.count(start) != 1 or text.count(end) != 1:
        raise SystemExit('ABORT: markers not unique for %r (%d / %d)'
                         % (start, text.count(start), text.count(end)))
    i = text.index(start)
    j = text.index(end, i)
    print('  spliced %s (%d chars -> %d)' % (start, j - i, len(new)))
    return text[:i] + new + text[j:], 1


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edited = 0
    for old, new in FIXES:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
        if new in v.text:
            print('  skip (already applied): %s' % old[:58].replace('\r\n', ' / '))
            continue
        n = v.text.count(old)
        if n == 0 and any(s.replace('\n', '\r\n') in v.text for s in SUPERSEDED):
            print('  skip (moved past by a later fix): %s' % old[:58].replace('\r\n', ' / '))
            continue
        if n != 1:
            raise SystemExit('ABORT: %d matches for %r' % (n, old[:80]))
        v.text = v.text.replace(old, new, 1)
        edited += 1
        v.changes.append('sheet feed: %s' % new[:56].replace('\r\n', ' / '))
    for start, end, new, marker in SPLICES:
        v.text, n = splice(v.text, start, end, new.replace('\n', '\r\n'), marker)
        edited += n
        if n:
            v.changes.append('sheet feed: %s ... (whole function)' % start)
    for old, new in POST_FIXES:
        old = old.replace('\n', '\r\n')
        new = new.replace('\n', '\r\n')
        if new in v.text:
            continue
        if v.text.count(old) != 1:
            continue
        v.text = v.text.replace(old, new, 1)
        edited += 1
        v.changes.append('sheet feed: %s' % new[:56].replace('\r\n', ' / '))
    gone = STAMP_DEL.replace('\n', '\r\n')
    if v.text.count(gone) == 1:
        v.text = v.text.replace(gone, '', 1)
        edited += 1
        v.changes.append('sheet feed: dropped the dead mdpFeedStamp helper')
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), edited))


if __name__ == '__main__':
    main()
