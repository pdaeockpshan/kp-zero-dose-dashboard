"""Point the morning feed at the district sheet the owner has now imported.

The owner imported mdp_sheet_intake_SNID_Nov-26.xlsx into sheet 1th6sKX... and left it readable
"anyone with the link", so the tab can read the Live tab beside the form responses. Until this
id was set mdpFeedSrcs() returned the form only and the district-sheet caption stayed hidden.

Master only; publishing is a separate decision.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

SHEET_ID = '1th6sKXoGlceSpWt2Uv1VH54q46k5USLBxlH6urCFdPc'

OLD = " gridId:'',\n"
NEW = " gridId:'%s',\n" % SHEET_ID


def crlf(s):
    return s.replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    if crlf(NEW) in v.text:
        print('nothing to do')
        return
    if v.text.count(crlf(OLD)) != 1:
        raise SystemExit('ABORT: gridId anchor')
    v.text = v.text.replace(crlf(OLD), crlf(NEW), 1)
    v.changes.append('Morning feed: read the shared district sheet')
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars, 1 edit' % (v.delta(),))


if __name__ == '__main__':
    main()
