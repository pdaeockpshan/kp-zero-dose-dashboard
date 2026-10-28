"""Build the shared district intake sheet for the morning team-deployment reports.

The Google Form needs a live connection at the moment Submit is pressed, which is exactly the
case that fails in the field. This workbook is the sheet alternative: one pre-made row per
district per campaign day, so a district only types its time of update and its counts, and can
do that offline in the Sheets app. The header names are the ones mdpFeedParse already accepts,
so the dashboard reads this tab through the same gviz CSV path as the form responses.

Days follow the campaign model: 5 for every district, 7 for PESHAWAR and KHYBER; extended
catch-up days (8-12) are added by the reporting desk, not pre-made here.

Run: python _refresh/mdp_sheet_intake.py
"""
import json
import os
import sys

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, 'index.html')
OUT = os.path.join(ROOT, '_refresh', 'mdep', 'mdp_sheet_intake_SNID_Nov-26.xlsx')

CADRES = ['Mobile teams', 'Influencers', 'Fixed teams', 'Transit teams', 'Roaming teams',
          'AIC teams', 'UPEC chairmen', 'DCF teams', 'Security']
HEAD = (['Timestamp', 'Division', 'District', 'Campaign day', 'UCs planned', 'UCs reported']
        + [h for c in CADRES for h in (c + ' planned', c + ' deployed')]
        + ['Security incidents', 'Why is deployment late (SEC / NET / BOY / TRA / OTH)'])
REASON_HEAD = HEAD[-1]
LONG_DAYS = {'PESHAWAR', 'KHYBER'}
TAB = 'Live'

HDR_FILL = PatternFill('solid', fgColor='FF5B21B6')
ID_FILL = PatternFill('solid', fgColor='FFEEF0F6')
FILL_FILL = PatternFill('solid', fgColor='FFFFF7CC')
WHITE = Font(color='FFFFFFFF', bold=True, size=10)
SMALL = Font(size=10)


def scope():
    t = open(MASTER, encoding='utf-8', newline='').read()
    k = t.index('const SND = ')
    snd, _ = json.JSONDecoder().raw_decode(t[k + len('const SND = '):])
    return [(r[0], r[1]) for r in snd['d']]


def read_me(ws, camp, nrows, districts):
    ws.column_dimensions['A'].width = 116
    lines = [
        ('Morning team deployment - district intake sheet', 'title'),
        ('%s · %d districts · %d rows, one per district per campaign day' % (camp, len(districts), nrows), 'sub'),
        ('', ''),
        ('How to file', 'h'),
        ('1. Find your district in the District column of the Live tab, then the row for the campaign day.', ''),
        ('2. Type the time of this update in the Timestamp column as 24-hour HH:MM (for example 08:15).', ''),
        ('3. Type UCs planned, UCs reported, and the planned / deployed number for each team type.', ''),
        ('4. Add security incidents if any, and the reason code if teams are short.', ''),
        ('5. That is all - do not add rows, columns, tabs or notes. The page reads this tab by itself.', ''),
        ('', ''),
        ('Rules', 'h'),
        ('- Counts only. Never type a name, a phone number or a remark: this sheet is public because the '
         'dashboard is public.', ''),
        ('- Planned may stay blank; the plan on file is used then. A typed 0 is kept as 0.', ''),
        ('- Reason codes: SEC security, NET network, BOY boycott / access refusal, TRA transport, '
         'OTH other. Combine with commas if more than one applies.', ''),
        ('- Filing again: just edit your row and update the time. For the same district and day the later '
         'time wins, so there is no need to delete anything.', ''),
        ('- The same numbers can also be sent through the online form; whichever arrives later wins.', ''),
        ('', ''),
        ('Offline', 'h'),
        ('The Sheets app keeps edits made without a connection and syncs them when the phone is back '
         'online, and a half-filled row never reaches the dashboard - a row counts only once it carries a '
         'time or a number.', ''),
        ('', ''),
        ('Day blocks', 'h'),
        ('- Days 1-5: every district. Days 6-7: PESHAWAR and KHYBER only (their catch-up days).', ''),
        ('- A catch-up day beyond that (8-12) is added by the reporting desk on request, not by districts.', ''),
        ('', ''),
        ('Reading', 'h'),
        ('The dashboard reads this tab as CSV every time the Morning deployment tab opens (at most every '
         'two minutes while it stays open). Nothing here is written by the dashboard.', ''),
        ('', ''),
        ('Share and protection (owner, once)', 'h'),
        ('1. File > Share > General access: "Anyone with the link" - Viewer is enough for the dashboard to '
         'read it; Editor is what districts need to type.', ''),
        ('2. Select the header row and the Division / District / Campaign day columns, then Data > Protect '
         'ranges, so a district cannot rename its row or shift a column.', ''),
        ('3. Keep the tab named Live - the dashboard asks for that name.', ''),
    ]
    for i, (txt, kind) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=1, value=txt)
        c.alignment = Alignment(vertical='top', wrap_text=True)
        if kind == 'title':
            c.font = Font(bold=True, size=14)
        elif kind == 'sub':
            c.font = Font(size=10, italic=True, color='FF555555')
        elif kind == 'h':
            c.font = Font(bold=True, size=11, color='FF5B21B6')


def build():
    districts = sorted(scope(), key=lambda r: (r[1], r[0]))
    wb = Workbook()
    live = wb.active
    live.title = TAB
    lists = wb.create_sheet('Lists')
    rme = wb.create_sheet('Read me')

    for j, h in enumerate(HEAD, start=1):
        c = live.cell(row=1, column=j, value=h)
        c.fill = HDR_FILL
        c.font = WHITE
        c.alignment = Alignment(vertical='center', wrap_text=True, horizontal='center')

    notes = {
        1: 'Time of this update, 24-hour HH:MM (08:15). A row with no time and no count is ignored.',
        2: 'Pre-filled. Do not change.',
        3: 'Pre-filled. Do not change.',
        4: 'Pre-filled campaign day. Do not change.',
        len(HEAD): 'SEC / NET / BOY / TRA / OTH, comma-separated when more than one applies.',
    }
    for j, txt in notes.items():
        live.cell(row=1, column=j).comment = Comment(txt, 'Reporting desk', width=260, height=90)

    r = 2
    for n, dv in districts:
        days = 7 if n in LONG_DAYS else 5
        for d in range(1, days + 1):
            vals = ['', dv, n, d]
            for j, v in enumerate(vals, start=1):
                c = live.cell(row=r, column=j, value=v)
                c.font = SMALL
                c.fill = FILL_FILL if j == 1 else ID_FILL
                if j == 1:
                    c.number_format = '@'
                c.alignment = Alignment(vertical='center')
            r += 1
    last = r - 1

    live.freeze_panes = 'A2'
    live.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(HEAD)), last)
    widths = {1: 11, 2: 13, 3: 15, 4: 9, 5: 8, 6: 8}
    for j in range(1, len(HEAD) + 1):
        live.column_dimensions[get_column_letter(j)].width = widths.get(j, 12)
    live.row_dimensions[1].height = 42

    lists['A1'] = 'Division'
    for i, dv in enumerate(sorted({d for _, d in districts}), start=2):
        lists.cell(row=i, column=1, value=dv)
    lists['B1'] = 'District'
    for i, n in enumerate(sorted({n for n, _ in districts}), start=2):
        lists.cell(row=i, column=2, value=n)
    lists['D1'] = 'Campaign day'
    for i in range(1, 13):
        lists.cell(row=i + 1, column=4, value=i)
    lists['F1'] = 'Reason'
    for i, code in enumerate(['SEC', 'NET', 'BOY', 'TRA', 'OTH'], start=2):
        lists.cell(row=i, column=6, value=code)
    lists.sheet_state = 'hidden'

    def dv_list(col, first, lastrow, target, title, prompt, stop=True):
        d = DataValidation(type='list', formula1='Lists!$%s$%d:$%s$%d' % (col, first, col, lastrow),
                           allow_blank=True, showDropDown=False)
        d.error = 'Pick a value from the list.'
        d.errorTitle = title
        d.errorStyle = 'stop' if stop else 'warning'
        d.showErrorMessage = True
        d.prompt = prompt
        d.promptTitle = title
        d.showInputMessage = True
        live.add_data_validation(d)
        d.add(target)
        return d

    dv_list('A', 2, len(districts) + 1, 'B2:B%d' % last, 'Division', 'Pre-filled.')
    dv_list('B', 2, len(districts) + 1, 'C2:C%d' % last, 'District', 'Pre-filled.')
    dv_list('D', 2, 13, 'D2:D%d' % last, 'Campaign day', 'Pre-filled.')

    num = DataValidation(type='whole', operator='between', formula1='0', formula2='100000',
                         allow_blank=True, showErrorMessage=True, errorTitle='Count',
                         error='Enter a whole number, 0 or more.',
                         prompt='Teams planned / deployed, UCs, incidents. Planned may stay blank.',
                         promptTitle='Count', showInputMessage=True)
    live.add_data_validation(num)
    num.add('E2:F%d' % last)
    num.add('G2:Y%d' % last)

    rsn = DataValidation(type='list', formula1='"SEC,NET,BOY,TRA,OTH"', allow_blank=True,
                         showErrorMessage=True, errorStyle='warning',
                         errorTitle='Reason', error='Codes are SEC, NET, BOY, TRA, OTH.',
                         prompt='SEC security · NET network · BOY boycott · TRA transport · OTH other',
                         promptTitle='Reason', showInputMessage=True)
    live.add_data_validation(rsn)
    rsn.add('Z2:Z%d' % last)

    read_me(rme, 'SNID Nov-26', last - 1, districts)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print('WROTE %s' % OUT)
    print('  rows %d (%d districts, days 1-5 all, 6-7 PESHAWAR + KHYBER), columns %d'
          % (last - 1, len(districts), len(HEAD)))
    print('  header: %s' % ' | '.join(HEAD[:6] + ['...'] + HEAD[-2:]))


if __name__ == '__main__':
    build()
