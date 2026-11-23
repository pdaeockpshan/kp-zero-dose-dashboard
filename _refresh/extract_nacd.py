"""NID countdown calendar -> const NACD (planned activity windows, no NEAP join yet).

Same PEOC "Countdown of NIDs" grid as NACT, but the December sheet is laid out
differently: row 1 carries month group headers as merged ranges (November
cols C..N, December O..AS), row 2 the day numbers, row 3 the weekday and rows
4..31 the 28 numbered activities. Windows are cell fills, and most of them are
drawn as merged ranges (a week-long campaign bar, a three-day communication
block), so the parser reads each merged range as one bar instead of colouring
only its anchor cell.

A merged range that spans several rows (AM4:AM31, the Christmas holiday) is a
column-wide calendar note, not an activity bar: it is kept in `notes` with its
own date and never painted on an activity row.

  FF00B0F0  scheduled window                  ('s')
  theme 7   main / review window              ('m')
  FFFF0000  post-campaign review              ('r')
  theme 5   LQAS/PCM or catch-up              ('u', 'q' on activity 22)
  theme 9   campaign week or catch-up day     ('c', 'u' when the text says Catch)

Usage: python _refresh/extract_nacd.py [--out PATH]
Prints: OK nacd <json chars> <summary> | ERR nacd <reason>
"""
import argparse
import datetime
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'nacd'
PKT = datetime.timezone(datetime.timedelta(hours=5), 'PKT')
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

TITLES = [
    'Previous SIA action points review',
    'PEOC / divisional staff orientation',
    'District master-trainers training (PEOC)',
    'Post-campaign review + DPEC meeting',
    'Zero-dose list collection + micro plan update',
    'AIC & UCMO training (micro plan updating)',
    'MP desk review + field validation (UC staff)',
    'UPEC meeting + summary micro plan to DEOC',
    'IDIMS data entry + target review',
    'Communication & social mobilization',
    'Real-time MPQA of selected UCs',
    'Course correction for failed UCs',
    'Re-MPQA if required',
    'FLW training (stall methodology)',
    'Training of defaulters',
    'Vaccine & logistics distribution',
    'District readiness meeting (DC chairs)',
    'Fixing pre-campaign issues',
    'Campaign implementation',
    'Market survey',
    'Zero-dose list to vaccinator',
    'Post-campaign evaluation (LQAS + PCM)',
    'LQAS/PCM investigation + UC improvement plan',
    'Retrieval of markers / vaccine / carriers / ID cards',
    'Post-campaign review at UC level',
    'Post-campaign review at district level',
    'Post-campaign review at provincial level',
    'Post-campaign review at national level',
]


def kind_of(fill, text=''):
    """kind letter for a bar fill, or None for the grid base."""
    if fill is None or fill.patternType is None:
        return None
    sc = fill.start_color
    if getattr(sc, 'type', None) == 'rgb':
        rgb = getattr(sc, 'rgb', None)
        if rgb == 'FFFFC000':
            return None                     # Sunday / holiday column
        if rgb == 'FF00B0F0':
            return 's'
        if rgb == 'FFFF0000':
            return 'r'
        if rgb == 'FF92D050':
            return 'c' if text else None    # solid green = campaign
        return None
    if getattr(sc, 'type', None) == 'theme':
        th = getattr(sc, 'theme', None)
        if th == 9:
            return 'u' if str(text).strip().lower().startswith('catch') else 'c'
        return {7: 'm', 5: 'u'}.get(th)
    return None


def month_groups(ws, year, camp_month):
    """col -> ISO date from the row-1 month groups and row-2 day numbers."""
    groups = []
    for mr in ws.merged_cells.ranges:
        if mr.min_row != 1 or mr.max_row != 1 or mr.min_col < 3:
            continue
        label = str(ws.cell(1, mr.min_col).value or '').strip()
        mo = None
        for i, x in enumerate(MONTHS):
            if label.lower().startswith(x.lower()):
                mo = i + 1
        if mo is None:
            raise RuntimeError('row-1 group %r at %s is not a month' % (label, mr.coord))
        yy = year - 1 if mo > camp_month else year
        groups.append((mr.min_col, mr.max_col, mo, yy))
    groups.sort()
    if not groups:
        raise RuntimeError('no month groups in row 1')
    dates = {}
    for c0, c1, mo, yy in groups:
        for col in range(c0, c1 + 1):
            v = ws.cell(2, col).value
            if v is None or not str(v).strip().isdigit():
                raise RuntimeError('no day number in row 2 col %d (%r)' % (col, v))
            dates[col] = '%04d-%02d-%02d' % (yy, mo, int(v))
    lo, hi = groups[0][0], groups[-1][1]
    want = set(range(lo, hi + 1))
    if set(dates) != want:
        raise RuntimeError('month groups leave a gap in columns %d..%d' % (lo, hi))
    return dates, groups


def nkey(t):
    return re.sub(r'[^a-z0-9]+', '', str(t).lower())


def read_calendar(path):
    import openpyxl
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    hdr = str(ws.cell(row=1, column=2).value or '')
    m = re.search(r'\(([^)]+)\)\s*(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', hdr)
    if not m:
        raise RuntimeError('cannot read campaign dates from B1 header %r' % hdr[:80])
    vac, d0, d1, mon, year = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5))
    mo = None
    for i, x in enumerate(MONTHS):
        if mon.lower().startswith(x.lower()):
            mo = i + 1
    if mo is None:
        raise RuntimeError('unknown month %r in B1 header' % mon)
    st = '%04d-%02d-%02d' % (year, mo, d0)
    en = '%04d-%02d-%02d' % (year, mo, d1)

    dates, groups = month_groups(ws, year, mo)
    maxc = groups[-1][1]

    inmerge = {}
    for mr in ws.merged_cells.ranges:
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                inmerge[(r, c)] = mr

    sundays, notes = set(), []
    merged_bars = {}     # row -> [(c0, c1, kind, text)]
    for mr in ws.merged_cells.ranges:
        if mr.min_row < 4 or mr.max_col < 3 or mr.max_row > 31:
            continue
        cell = ws.cell(mr.min_row, mr.min_col)
        text = re.sub(r'\s+', ' ', str(cell.value or '')).strip()
        f = cell.fill
        if mr.min_row != mr.max_row:
            # a column-wide annotation, not an activity bar
            if text:
                d = dates.get(mr.min_col)
                notes.append({'d': d, 't': text})
            continue
        k = kind_of(f, text)
        if k:
            merged_bars.setdefault(mr.min_row, []).append([mr.min_col, mr.max_col, k, text])

    acts = []
    for r in range(4, 32):
        n = ws.cell(row=r, column=1).value
        name = ws.cell(row=r, column=2).value
        if n is None or name is None:
            continue
        if int(n) != len(acts) + 1:
            raise RuntimeError('activity numbering broken at row %d (%r)' % (r, n))
        pieces = []      # [c0, c1, kind]
        for col in range(3, maxc + 1):
            if (r, col) in inmerge:
                continue
            c = ws.cell(row=r, column=col)
            f = c.fill
            k = kind_of(f, c.value)
            if not k:
                if f is not None and f.patternType is not None:
                    sc = f.start_color
                    if getattr(sc, 'type', None) == 'rgb' and getattr(sc, 'rgb', None) == 'FFFFC000':
                        sundays.add(dates[col])
                continue
            if pieces and col == pieces[-1][1] + 1 and k == pieces[-1][2]:
                pieces[-1][1] = col
            else:
                pieces.append([col, col, k])
        for c0, c1, k, _ in merged_bars.get(r, []):
            pieces.append([c0, c1, k])
        if not pieces:
            raise RuntimeError('activity %d (row %d) has no bar cells' % (n, r))
        pieces.sort()
        bars = []
        for c0, c1, k in pieces:
            if n == 22 and k == 'u':
                k = 'q'                        # LQAS/PCM day on the post-evaluation row
            s, e = dates[c0], dates[c1]
            if k == 'c':
                e = max(e, en)                 # the campaign bar runs to the last day
            if bars and bars[-1][2] == k and dates[c0] <= bars[-1][1]:
                bars[-1][1] = max(bars[-1][1], e)
            else:
                bars.append([s, e, k])
        act = {'n': int(n), 't': TITLES[int(n) - 1],
               'd': re.sub(r'\s+', ' ', str(name)).strip(),
               's': bars[0][0], 'e': bars[-1][1], 'b': bars}
        notes_r = [t for c0, c1, k, t in merged_bars.get(r, []) if t]
        keep = []
        for t in notes_r:
            kk = nkey(t)
            if any(kk.startswith(nkey(x)) or nkey(x).startswith(kk) or kk[:40] == nkey(x)[:40]
                   for x in keep):
                continue
            keep.append(t)
        if keep:
            act['x'] = ' '.join(keep)
        acts.append(act)

    # plain (unmerged) text cells inside the grid become activity notes
    for r in range(4, 32):
        for col in range(3, maxc + 1):
            c = ws.cell(row=r, column=col)
            if c.value is None or not str(c.value).strip():
                continue
            if (r, col) in inmerge:
                continue
            a = acts[r - 4]
            txt = re.sub(r'\s+', ' ', str(c.value)).strip()
            if a.get('x') and (nkey(txt) == nkey(a['x']) or nkey(txt) in nkey(a['x'])):
                continue
            a['x'] = (a.get('x') + ' ' + txt).strip() if a.get('x') else txt

    d = datetime.date.fromisoformat(min(dates.values()))
    last = datetime.date.fromisoformat(max(dates.values()))
    d += datetime.timedelta(days=(6 - d.weekday()) % 7)
    exp_sun = []
    while d <= last:
        exp_sun.append(d.isoformat())
        d += datetime.timedelta(days=7)
    if sundays != set(exp_sun):
        raise RuntimeError('Sunday columns %s do not match %s - day numbering shifted?'
                           % (sorted(sundays), sorted(exp_sun)))
    if len(acts) != 28:
        raise RuntimeError('expected 28 activities, found %d' % len(acts))
    return vac, st, en, acts, notes


def build(cfg):
    e = cfg['auto'][DS]
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no activity calendar under %s' % (DS, e['roots']))
    rec = files[0]
    vac, st, en, acts, notes = read_calendar(rec['path'])
    conf = e.get('config') or {}
    camp = conf.get('campaign') or ('NID ' + MONTHS[int(st[5:7]) - 1] + '-' + st[2:4])
    if conf.get('start') and conf['start'] != st:
        raise SystemExit('ERR %s calendar says the campaign starts %s but the active scope starts %s - '
                         'drop the right calendar or update auto.nacd.config' % (DS, st, conf['start']))
    asof = datetime.datetime.fromtimestamp(rec['mtime'], PKT).strftime('%Y-%m-%d')
    out = {'camp': camp, 'vac': vac, 'st': st, 'en': en,
           'from': min(a['s'] for a in acts), 'to': max(a['e'] for a in acts),
           'asof': asof, 'src': rec['name'], 'notes': notes, 'a': acts}
    nb = sum(len(a['b']) for a in acts)
    return out, '%d activities, %d bars, %s..%s, campaign %s %s..%s, %d notes' % (
        len(acts), nb, out['from'], out['to'], camp, st, en, len(notes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if a.source:
        cfg['auto'][DS] = dict(cfg['auto'][DS], roots=[os.path.dirname(os.path.abspath(a.source))],
                               patterns=[os.path.basename(a.source)], exclude=[])
    out, summary = build(cfg)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, DS + '.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s' % (DS, len(js), summary))


if __name__ == '__main__':
    main()
