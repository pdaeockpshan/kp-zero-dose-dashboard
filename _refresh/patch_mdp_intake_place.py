"""Put the intake-sheet download next to the sheet links, not the per-day template.

The button was added under "Template for day N", which is the wrong neighbour: the intake sheet
is the shared district sheet, not a one-day return. It moves up to the row that already carries
the form and sheet links, so a reader looking for where districts file finds both together.

Run after patch_mdp_intake_xlsx.py. Master only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

SHEET_A = (' <a class="btn" id="mdpSheetA" href="https://docs.google.com/spreadsheets/d/'
           '12xvLgWLk60L5XM6fwtog5Jc0_3KwUrIT-fKMyN1wfNE/edit" target="_blank" rel="noopener">'
           'Response sheet</a>\n')

BTN = (' <button class="btn" id="btnMDPintake" title="The shared district sheet as a workbook: '
       'one pre-made row per district per campaign day">District intake sheet (xlsx)</button>\n')

TEMPLATE_ROW = (' <button class="btn" id="btnMDPtpl">Download template (xlsx)</button>\n'
                + BTN)


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    if crlf(TEMPLATE_ROW) not in v.text and crlf(SHEET_A + BTN) in v.text:
        print('nothing to do')
        return
    if v.text.count(crlf(TEMPLATE_ROW)) != 1:
        raise SystemExit('ABORT: template row anchor')
    v.text = v.text.replace(crlf(TEMPLATE_ROW),
                            crlf(' <button class="btn" id="btnMDPtpl">Download template (xlsx)</button>\n'), 1)
    if v.text.count(crlf(SHEET_A)) != 1:
        raise SystemExit('ABORT: sheet link anchor')
    v.text = v.text.replace(crlf(SHEET_A), crlf(SHEET_A + BTN), 1)
    v.changes.append('Morning intake: button beside the sheet links')
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, 1 edit' % (v.delta(),))


if __name__ == '__main__':
    main()
