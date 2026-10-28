"""Tidy the intake workbook's validations and column widths.

Assigning the same validation object cell by cell made ExcelJS write two overlapping sqref
entries per rule (B2:B140 plus B10:B140), which shows up as duplicate rules in Excel and can
be flattened oddly by Google Sheets on import. One range per rule avoids it. The Campaign day
column also lost its width because 9 is ExcelJS's default column width and is not written back.

Run after patch_mdp_intake_xlsx.py. Master only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CELL_OLD = '''    row.getCell(2).dataValidation=DV_DIV;
    row.getCell(3).dataValidation=DV_DIS;
    row.getCell(4).dataValidation=DV_DAY;
    for(let j=5;j<L;j++)row.getCell(j).dataValidation=DV_NUM;
    row.getCell(L).dataValidation=DV_RSN;
   }});
  const last=r;
'''

CELL_NEW = '''   }});
  const last=r;
  // one range per rule: assigning the same validation cell by cell wrote overlapping sqref entries
  const dvTo=(c,r1,r2,dv)=>ws.dataValidations.add(ws.getCell(r1,c).address+':'+ws.getCell(r2,c).address,dv);
  dvTo(2,2,last,DV_DIV);
  dvTo(3,2,last,DV_DIS);
  dvTo(4,2,last,DV_DAY);
  ws.dataValidations.add(ws.getCell(2,5).address+':'+ws.getCell(last,L-1).address,DV_NUM);
  dvTo(L,2,last,DV_RSN);
'''

WIDTH_OLD = ' [11,13,15,9,8,8].forEach((w,j)=>{ws.getColumn(j+1).width=w;});\n'
WIDTH_NEW = ' [11,13,15,9.5,8,8].forEach((w,j)=>{ws.getColumn(j+1).width=w;});\n'


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edited = 0
    for old, new, label in [
        (CELL_OLD, CELL_NEW, 'one validation range per rule'),
        (WIDTH_OLD, WIDTH_NEW, 'campaign day width'),
    ]:
        old, new = crlf(old), crlf(new)
        if new in v.text:
            print('  skip (already applied): %s' % label)
            continue
        n = v.text.count(old)
        if n != 1:
            raise SystemExit('ABORT: %d matches for %s' % (n, label))
        v.text = v.text.replace(old, new, 1)
        edited += 1
        v.changes.append('Morning intake: %s' % label)
    if not edited:
        print('nothing to do')
        return
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, %d edits' % (v.delta(), edited))


if __name__ == '__main__':
    main()
