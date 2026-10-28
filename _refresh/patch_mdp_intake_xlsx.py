"""District intake sheet download on the Morning deployment tab.

The shared district sheet is the offline-friendly alternative to the Google Form, but the
owner has to get the 139-row workbook into Google Sheets once. This adds the workbook to the
page itself: same content as _refresh/mdp_sheet_intake.py (Live tab, hidden Lists, Read me,
5 days per district, 7 for Peshawar and Khyber, list and whole-number validation), built in
the browser with ExcelJS so the owner can download it and import it into the sheet.

Master only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

BTN_OLD = ' <button class="btn" id="btnMDPtpl">Download template (xlsx)</button>\n'
BTN_NEW = (' <button class="btn" id="btnMDPtpl">Download template (xlsx)</button>\n'
           ' <button class="btn" id="btnMDPintake" title="The shared district sheet as a workbook: '
           'one pre-made row per district per campaign day">District intake sheet (xlsx)</button>\n')

CAP_OLD = ('Awaited and the deployment % are written as formulas in the template and recomputed on import.')
CAP_NEW = ('Awaited and the deployment % are written as formulas in the template and recomputed on import. '
           'The <b>district intake sheet</b> is the workbook behind the shared district sheet: it already '
           'carries one row per district per campaign day, so a district only types its time of update and '
           'its counts, and can file there offline in the Sheets app.')

JS_ANCHOR = 'function mdpReadMe(){\n'

JS_NEW = '''// The shared district sheet as a workbook: one row per district per campaign day, so a district only
// types its time of update and its counts. The header names are the ones mdpFeedParse accepts, so the
// page reads the tab through the same gviz CSV path as the form responses. Extended catch-up days
// (8-12) are added by the reporting desk, not pre-made here.
const mdpIntakeHead=()=>['Timestamp','Division','District','Campaign day','UCs planned','UCs reported']
 .concat(...MDP_TYPES.map(t=>[t[1]+' planned',t[1]+' deployed']))
 .concat(['Security incidents','Why is deployment late (SEC / NET / BOY / TRA / OTH)']);
const MDP_IN_PORT='FF5B21B6',MDP_IN_ID='FFEEF0F6',MDP_IN_TINT='FFFFF7CC';
async function mdpExportIntake(){
 try{
  const X=await xlLib(),wb=new X.Workbook(),H=mdpIntakeHead(),L=H.length;
  const ds=mdpScope().slice().sort((a,b)=>String(a.dv).localeCompare(String(b.dv))||String(a.n).localeCompare(String(b.n)));
  const ws=wb.addWorksheet('Live',{views:[{state:'frozen',ySplit:1}]});
  const lists=wb.addWorksheet('Lists'),rme=wb.addWorksheet('Read me');
  H.forEach((h,j)=>{const c=ws.getRow(1).getCell(j+1);c.value=h;
   c.font={bold:true,size:10,color:{argb:'FFFFFFFF'}};
   c.fill={type:'pattern',pattern:'solid',fgColor:{argb:MDP_IN_PORT}};
   c.alignment={vertical:'middle',horizontal:'center',wrapText:true};});
  ws.getRow(1).height=42;
  const note={1:'Time of this update, 24-hour HH:MM (08:15). A row with no time and no count is ignored.',
   2:'Pre-filled. Do not change.',3:'Pre-filled. Do not change.',4:'Pre-filled campaign day. Do not change.'};
  note[L]='SEC / NET / BOY / TRA / OTH, comma-separated when more than one applies.';
  Object.keys(note).forEach(j=>{ws.getRow(1).getCell(+j).note=note[j];});
  // the two list ranges are sheet references, not inline text: 37 districts overflow the 255-character
  // limit a literal list formula carries
  lists.getCell(1,1).value='Division';
  uniq(ds.map(o=>o.dv)).sort().forEach((v,i)=>{lists.getCell(i+2,1).value=v;});
  lists.getCell(1,2).value='District';
  ds.map(o=>o.n).sort().forEach((v,i)=>{lists.getCell(i+2,2).value=v;});
  lists.getCell(1,4).value='Campaign day';
  for(let d=1;d<=MDP_MAXD;d++)lists.getCell(d+1,4).value=d;
  lists.state='hidden';
  const ndv=uniq(ds.map(o=>o.dv)).length;
  const DV_DIV={type:'list',allowBlank:true,formulae:['Lists!$A$2:$A$'+(ndv+1)],
   showErrorMessage:true,errorStyle:'stop',errorTitle:'Division',error:'Pick a value from the list.',
   showInputMessage:true,promptTitle:'Division',prompt:'Pre-filled. Do not change.'};
  const DV_DIS={type:'list',allowBlank:true,formulae:['Lists!$B$2:$B$'+(ds.length+1)],
   showErrorMessage:true,errorStyle:'stop',errorTitle:'District',error:'Pick a value from the list.',
   showInputMessage:true,promptTitle:'District',prompt:'Pre-filled. Do not change.'};
  const DV_DAY={type:'list',allowBlank:true,formulae:['Lists!$D$2:$D$'+(MDP_MAXD+1)],
   showErrorMessage:true,errorStyle:'stop',errorTitle:'Campaign day',error:'Pick a value from the list.',
   showInputMessage:true,promptTitle:'Campaign day',prompt:'Pre-filled. Do not change.'};
  const DV_NUM={type:'whole',operator:'between',allowBlank:true,formulae:[0,100000],
   showErrorMessage:true,errorStyle:'stop',errorTitle:'Count',error:'Enter a whole number, 0 or more.',
   showInputMessage:true,promptTitle:'Count',prompt:'Teams planned / deployed, UCs, incidents. Planned may stay blank.'};
  const DV_RSN={type:'list',allowBlank:true,formulae:['"SEC,NET,BOY,TRA,OTH"'],
   showErrorMessage:true,errorStyle:'warning',errorTitle:'Reason',error:'Codes are SEC, NET, BOY, TRA, OTH.',
   showInputMessage:true,promptTitle:'Reason',prompt:'SEC security · NET network · BOY boycott · TRA transport · OTH other'};
  let r=1;
  ds.forEach(o=>{
   const days=mdpBaseD(o.n);
   for(let d=1;d<=days;d++){
    r++;const row=ws.getRow(r);
    row.getCell(1).value='';
    row.getCell(2).value=o.dv;
    row.getCell(3).value=o.n;
    row.getCell(4).value=d;
    for(let j=1;j<=4;j++){const c=row.getCell(j);
     c.font={size:10};c.alignment={vertical:'center'};
     c.fill={type:'pattern',pattern:'solid',fgColor:{argb:j===1?MDP_IN_TINT:MDP_IN_ID}};}
    row.getCell(1).numFmt='@';
    row.getCell(2).dataValidation=DV_DIV;
    row.getCell(3).dataValidation=DV_DIS;
    row.getCell(4).dataValidation=DV_DAY;
    for(let j=5;j<L;j++)row.getCell(j).dataValidation=DV_NUM;
    row.getCell(L).dataValidation=DV_RSN;
   }});
  const last=r;
  ws.autoFilter={from:{row:1,column:1},to:{row:last,column:L}};
  [11,13,15,9,8,8].forEach((w,j)=>{ws.getColumn(j+1).width=w;});
  for(let j=7;j<=L;j++)ws.getColumn(j).width=12;
  rme.getColumn(1).width=116;
  const rl=[
   ['Morning team deployment — district intake sheet','t'],
   [mdpCampLbl()+' · '+ds.length+' districts · '+(last-1)+' rows, one per district per campaign day','i'],
   ['',''],
   ['How to file','h'],
   ['1. Find your district in the District column of the Live tab, then the row for the campaign day.',''],
   ['2. Type the time of this update in the Timestamp column as 24-hour HH:MM (for example 08:15).',''],
   ['3. Type UCs planned, UCs reported, and the planned / deployed number for each team type.',''],
   ['4. Add security incidents if any, and the reason code if teams are short.',''],
   ['5. That is all — do not add rows, columns, tabs or notes. The page reads this tab by itself.',''],
   ['',''],
   ['Rules','h'],
   ['- Counts only. Never type a name, a phone number or a remark: this sheet is public because the dashboard is public.',''],
   ['- Planned may stay blank; the plan on file is used then. A typed 0 is kept as 0.',''],
   ['- Reason codes: SEC security, NET network, BOY boycott / access refusal, TRA transport, OTH other.',''],
   ['- Filing again: just edit your row and update the time. For the same district and day the later time wins.',''],
   ['- The same numbers can also be sent through the online form; whichever arrives later wins.',''],
   ['',''],
   ['Offline','h'],
   ['The Sheets app keeps edits made without a connection and syncs them when the phone is back online, and a half-filled row never reaches the dashboard — a row counts only once it carries a time or a number.',''],
   ['',''],
   ['Day blocks','h'],
   ['- Days 1-5: every district. Days 6-7: PESHAWAR and KHYBER only (their catch-up days).',''],
   ['- A catch-up day beyond that (8-'+MDP_MAXD+') is added by the reporting desk on request, not by districts.',''],
   ['',''],
   ['Reading','h'],
   ['The dashboard reads this tab as CSV every time the Morning deployment tab opens (at most every two minutes while it stays open). Nothing here is written by the dashboard.',''],
   ['',''],
   ['Share and protection (owner, once)','h'],
   ['1. File > Share > General access: "Anyone with the link" — Viewer is enough for the dashboard to read it; Editor is what districts need to type.',''],
   ['2. Select the header row and the Division / District / Campaign day columns, then Data > Protect ranges, so a district cannot rename its row or shift a column.',''],
   ['3. Keep the tab named Live — the dashboard asks for that name.','']
  ];
  rl.forEach((p,i)=>{const c=rme.getRow(i+1).getCell(1);c.value=p[0];
   c.alignment={vertical:'top',wrapText:true};
   c.font=p[1]==='t'?{bold:true,size:14}:p[1]==='i'?{size:10,italic:true,color:{argb:'FF555555'}}
    :p[1]==='h'?{bold:true,size:11,color:{argb:MDP_IN_PORT}}:{size:10};});
  return await mdpGot(wb,mdpCampLbl().replace(/\\s+/g,'_')+'_district_intake_sheet.xlsx');
 }catch(e){console.error('mdp intake sheet',e);toast('The intake sheet could not be built: '+((e&&e.message)||'unknown error'));}
}

'''

WIRE_OLD = " on('btnMDPtpl','onclick',()=>mdpExportTpl());\n"
WIRE_NEW = (" on('btnMDPtpl','onclick',()=>mdpExportTpl());\n"
            " on('btnMDPintake','onclick',()=>mdpExportIntake());\n")

# the division list is shorter than the district list, so it needs its own count: pointing it at
# A2:A(districts+1) dragged blank rows into the dropdown
DIV_OLD = ("  const DV_DIV={type:'list',allowBlank:true,formulae:['Lists!$A$2:$A$'+(ds.length+1)],\n")
DIV_NEW = ("  const ndv=uniq(ds.map(o=>o.dv)).length;\n"
           "  const DV_DIV={type:'list',allowBlank:true,formulae:['Lists!$A$2:$A$'+(ndv+1)],\n")


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edited = 0
    if "id=\"btnMDPintake\"" in v.text:
        old, new = crlf(DIV_OLD), crlf(DIV_NEW)
        if new in v.text:
            print('nothing to do')
            return
        if v.text.count(old) != 1:
            raise SystemExit('ABORT: division list anchor')
        v.text = v.text.replace(old, new, 1)
        v.changes.append('Morning intake: division list length')
        dashpatch.assert_crlf(v)
        dashpatch.write_variants([v])
        print('PATCHED index.html %+d chars, 1 edit' % (v.delta(),))
        return
    fixes = [
        (BTN_OLD, BTN_NEW, 'intake button'),
        (WIRE_OLD, WIRE_NEW, 'intake wiring'),
        (CAP_OLD, CAP_NEW, 'caption'),
    ]
    old, new, lbl = fixes[0]
    if v.text.count(crlf(old)) != 1:
        raise SystemExit('ABORT: intake button anchor')
    v.text = v.text.replace(crlf(old), crlf(new), 1)
    edited += 1
    v.changes.append('Morning intake: %s' % lbl)
    anchor = crlf(JS_ANCHOR)
    if v.text.count(anchor) != 1:
        raise SystemExit('ABORT: intake JS anchor')
    v.text = v.text.replace(anchor, crlf(JS_NEW) + anchor, 1)
    edited += 1
    v.changes.append('Morning intake: intake workbook export')
    for old, new, label in fixes[1:]:
        if v.text.count(crlf(old)) != 1:
            raise SystemExit('ABORT: %d matches for %s' % (v.text.count(crlf(old)), label))
        v.text = v.text.replace(crlf(old), crlf(new), 1)
        edited += 1
        v.changes.append('Morning intake: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), edited))


if __name__ == '__main__':
    main()
