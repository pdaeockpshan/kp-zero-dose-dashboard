"""Build the district intake workbook day by day, matching the workbook the desk now files.

The shared sheet moved from one Live tab to Day-1st .. Day-5th. The downloaded intake workbook is
the starting point for that sheet, so it has to carry the same tabs: otherwise a desk that imports
it rebuilds a Live tab the dashboard no longer reads.

Every district gets a row on every day tab, the day is pre-filled, and the tab names come from
MDP_FEED.gridTabs so the workbook and the reader cannot drift apart. The Blockers tab is unchanged.

Master only; publishing is a separate decision.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch


def crlf(s):
    return s.replace('\n', '\r\n')


EDITS = []


def edit(old, new, note):
    EDITS.append((crlf(old), crlf(new), note))


# 1. one worksheet per day tab instead of Live
edit(
    "  const ws=wb.addWorksheet('Live',{views:[{state:'frozen',ySplit:1}]});\n"
    "  const lists=wb.addWorksheet('Lists'),rme=wb.addWorksheet('Read me');\n"
    "  H.forEach((h,j)=>{const c=ws.getRow(1).getCell(j+1);c.value=h;\n"
    "   c.font={bold:true,size:10,color:{argb:'FFFFFFFF'}};\n"
    "   c.fill={type:'pattern',pattern:'solid',fgColor:{argb:MDP_IN_PORT}};\n"
    "   c.alignment={vertical:'middle',horizontal:'center',wrapText:true};});\n"
    "  ws.getRow(1).height=42;\n"
    "  const note={1:'Time of this update, 24-hour HH:MM (08:15). A row with no time and no count is ignored.',\n"
    "   2:'Pre-filled. Do not change.',3:'Pre-filled. Do not change.',4:'Pre-filled campaign day. Do not change.'};\n"
    "  note[L]='SEC / NET / BOY / STK / TRA / OTH, comma-separated when more than one applies.';\n"
    "  Object.keys(note).forEach(j=>{ws.getRow(1).getCell(+j).note=note[j];});\n",
    "  // One tab per campaign day, named exactly as the reader asks for them, so the workbook that is\n"
    "  // imported and the workbook that is read cannot drift apart.\n"
    "  const DAYS=MDP_FEED.gridTabs||[],dayWs=[];\n"
    "  DAYS.forEach(t=>{\n"
    "   const ws=wb.addWorksheet(t[0],{views:[{state:'frozen',ySplit:1}]});\n"
    "   H.forEach((h,j)=>{const c=ws.getRow(1).getCell(j+1);c.value=h;\n"
    "    c.font={bold:true,size:10,color:{argb:'FFFFFFFF'}};\n"
    "    c.fill={type:'pattern',pattern:'solid',fgColor:{argb:MDP_IN_PORT}};\n"
    "    c.alignment={vertical:'middle',horizontal:'center',wrapText:true};});\n"
    "   ws.getRow(1).height=42;\n"
    "   ws.getRow(1).getCell(4).note='Pre-filled campaign day. Do not change.';\n"
    "   [2,3].forEach(j=>{ws.getRow(1).getCell(j).note='Pre-filled. Do not change.';});\n"
    "   ws.getRow(1).getCell(1).note='Time of this update, 24-hour HH:MM (08:15). A row with no '+\n"
    "    'reported or deployed count is ignored; the time orders a district that files twice.';\n"
    "   ws.getRow(1).getCell(L).note='SEC / NET / BOY / STK / TRA / OTH, comma-separated when more than one applies.';\n"
    "   dayWs.push(ws);\n"
    "  });\n"
    "  const lists=wb.addWorksheet('Lists'),rme=wb.addWorksheet('Read me');\n",
    'intake: one worksheet per day tab')

# 2. rows: every district on every day tab
edit(
    "  let r=1;\n"
    "  ds.forEach(o=>{\n"
    "   const days=mdpBaseD(o.n);\n"
    "   for(let d=1;d<=days;d++){\n"
    "    r++;const row=ws.getRow(r);\n"
    "    row.getCell(1).value='';\n"
    "    row.getCell(2).value=o.dv;\n"
    "    row.getCell(3).value=o.n;\n"
    "    row.getCell(4).value=d;\n"
    "    for(let j=1;j<=4;j++){const c=row.getCell(j);\n"
    "     c.font={size:10};c.alignment={vertical:'center'};\n"
    "     c.fill={type:'pattern',pattern:'solid',fgColor:{argb:j===1?MDP_IN_TINT:MDP_IN_ID}};}\n"
    "    row.getCell(1).numFmt='@';\n"
    "   }});\n"
    "  const last=r;\n",
    "  dayWs.forEach((ws,k)=>{\n"
    "   const d=DAYS[k][1];\n"
    "   ds.forEach((o,i)=>{const row=ws.getRow(i+2);\n"
    "    row.getCell(1).value='';\n"
    "    row.getCell(2).value=o.dv;\n"
    "    row.getCell(3).value=o.n;\n"
    "    row.getCell(4).value=d;\n"
    "    for(let j=1;j<=4;j++){const c=row.getCell(j);\n"
    "     c.font={size:10};c.alignment={vertical:'center'};\n"
    "     c.fill={type:'pattern',pattern:'solid',fgColor:{argb:j===1?MDP_IN_TINT:MDP_IN_ID}};}\n"
    "    row.getCell(1).numFmt='@';\n"
    "   });\n"
    "  });\n"
    "  const last=ds.length+1;\n",
    'intake: one pre-made row per district per day tab')

# 3. validations on every day tab
edit(
    "  // one range per rule: assigning the same validation cell by cell wrote overlapping sqref entries\n"
    "  const dvTo=(c,r1,r2,dv)=>ws.dataValidations.add(ws.getCell(r1,c).address+':'+ws.getCell(r2,c).address,dv);\n"
    "  dvTo(2,2,last,DV_DIV);\n"
    "  dvTo(3,2,last,DV_DIS);\n"
    "  dvTo(4,2,last,DV_DAY);\n"
    "  ws.dataValidations.add(ws.getCell(2,5).address+':'+ws.getCell(last,L-1).address,DV_NUM);\n"
    "  dvTo(L,2,last,DV_RSN);\n",
    "  // one range per rule: assigning the same validation cell by cell wrote overlapping sqref entries\n"
    "  dayWs.forEach(ws=>{\n"
    "   const dvTo=(c,r1,r2,dv)=>ws.dataValidations.add(ws.getCell(r1,c).address+':'+ws.getCell(r2,c).address,dv);\n"
    "   dvTo(2,2,last,DV_DIV);\n"
    "   dvTo(3,2,last,DV_DIS);\n"
    "   dvTo(4,2,last,DV_DAY);\n"
    "   ws.dataValidations.add(ws.getCell(2,5).address+':'+ws.getCell(last,L-1).address,DV_NUM);\n"
    "   dvTo(L,2,last,DV_RSN);\n"
    "  });\n",
    'intake: validations on every day tab')

# 4. filters and widths on every day tab
edit(
    "  ws.autoFilter={from:{row:1,column:1},to:{row:last,column:L}};\n"
    "  [11,13,15,9.5,8,8].forEach((w,j)=>{ws.getColumn(j+1).width=w;});\n"
    "  for(let j=7;j<=L;j++)ws.getColumn(j).width=12;\n",
    "  dayWs.forEach(ws=>{\n"
    "   ws.autoFilter={from:{row:1,column:1},to:{row:last,column:L}};\n"
    "   [11,13,15,9.5,8,8].forEach((w,j)=>{ws.getColumn(j+1).width=w;});\n"
    "   for(let j=7;j<=L;j++)ws.getColumn(j).width=12;\n"
    "  });\n",
    'intake: filters and widths on every day tab')

# 5. read me: the tab is now the day
edit(
    "   [mdpCampLbl()+' · '+ds.length+' districts · '+(last-1)+' rows, one per district per campaign day','i'],\n",
    "   [mdpCampLbl()+' · '+ds.length+' districts · '+DAYS.length+' day tabs · one pre-made row per district per day','i'],\n",
    'read me: subtitle')

edit(
    "   ['1. Find your district in the District column of the Live tab, then the row for the campaign day.',''],\n",
    "   ['1. Open the tab for the campaign day ('+DAYS.map(t=>t[0]).join(', ')+') and find your district in the District column.',''],\n",
    'read me: open the day tab')

edit(
    "   ['5. That is all — do not add rows, columns, tabs or notes. The page reads this tab by itself.',''],\n",
    "   ['5. That is all — do not add rows, columns or tabs, and do not rename a day tab. The page reads the day tabs by itself.',''],\n",
    'read me: read by itself')

edit(
    "   ['The Sheets app keeps edits made without a connection and syncs them when the phone is back online, and a half-filled row never reaches the dashboard — a row counts only once it carries a time or a number.',''],\n",
    "   ['The Sheets app keeps edits made without a connection and syncs them when the phone is back online, and a half-filled row never reaches the dashboard — a row counts only once a reported or deployed count is typed on it.',''],\n",
    'read me: what counts as filed')

edit(
    "   ['The dashboard reads this tab as CSV every time the Morning deployment tab opens (at most every two minutes while it stays open). Nothing here is written by the dashboard.',''],\n",
    "   ['The dashboard reads each day tab as CSV every time the Morning deployment tab opens (at most every two minutes while it stays open). Nothing here is written by the dashboard.',''],\n",
    'read me: each day tab is read')

edit(
    "   ['3. Keep the tab named Live — the dashboard asks for that name.','']\n",
    "   ['3. Keep the day tabs named '+DAYS.map(t=>t[0]).join(', ')+' — the dashboard asks for those names.','']\n",
    'read me: keep the day tab names')

edit(
    "   ['- Days 1-5: every district. Days 6-7: PESHAWAR and KHYBER only (their catch-up days).',''],\n"
    "   ['- A catch-up day beyond that (8-'+MDP_MAXD+') is added by the reporting desk on request, not by districts.',''],\n",
    "   ['- One tab per day, days 1-5, every district. The sheet this workbook mirrors carries only those five tabs, so the catch-up days PESHAWAR and KHYBER run on days 6-7 are not filed here.',''],\n"
    "   ['- If those days have to be collected, the reporting desk adds a Day-6th and a Day-7th tab and the page is pointed at them; it does not read a tab nobody named.',''],\n",
    'read me: five tabs cover days 1-5 only')

edit(
    "  // The Live tab answers \"how many teams are out\"; this tab answers \"which UC is blocked, why and for\n",
    "  // The day tabs answer \"how many teams are out\"; this tab answers \"which UC is blocked, why and for\n",
    'intake: Blockers comment follows the day tabs')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    if "const DAYS=MDP_FEED.gridTabs||[]" in v.text:
        print('nothing to do')
        return
    for old, new, note in EDITS:
        v.require(v.text.count(old) == 1, 'anchor %r found %d times' % (note, v.text.count(old)))
        v.text = v.text.replace(old, new, 1)
        v.changes.append(note)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), len(EDITS)))


if __name__ == '__main__':
    main()
