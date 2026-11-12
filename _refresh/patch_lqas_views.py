"""Join the SNID Nov 2026 lots into the two tables that hold a portal taxonomy.

  * `PKX.lqas`  - the E-LQAS card on Campaign overview and Post-campaign analysis
  * `CINN`      - the campaign indicators plate (district and UC grain)

Both carry the portal's fourteen-column reason taxonomy, which the dashboard's own
`LQR` does not: LQR keeps the seven reasons the UC-wise export prints (away,
newborn, migrant, refused, team did not visit, team missed child, others), and the
taxonomy splits them as NT = team did not visit, TVBMC = team missed the child,
NA = away, Migrated, Born, REF = refused.  `ot` (others) has no column in either
table and is therefore not carried - the caption says so.

The mapping is proved, not assumed: the same builder is run over the SNID Sept
2026 lots (ci=1) and must reproduce the September rows already embedded in
`PKX.lqas` exactly, district for district and UC for UC, before anything is written.

Usage: python _refresh/patch_lqas_views.py [--write]
"""
import io
import json
import re
import sys

PATH = 'index.html'

# PKX / CINN column layout after the lot counts
#   0 Pass 1 Intermediate 2 Fail 3 Pass % 4 NT 5 TVBMC 6 NA 7 Asleep
#   8 Migrated 9 Born 10 REF 11 VBNFM 12 FMwoSV 13 Inaccessible
PKX_COLS = 14
UC_SRC = 'lqas_2026-11-12_03-03-54.xls'
DIST_SRC = 'lqas_2026-11-12_03-04-02.xls'


def load_const(t, name):
    # each payload is one very long line, so the first ';\r\n' after the
    # declaration is its terminator
    key = 'const %s = ' % name
    start = t.find(key)
    if start < 0:
        raise SystemExit('ERR cannot find const %s' % name)
    start += len(key)
    end = t.index(';\r\n', start)
    return json.loads(t[start:end])


def swap_const(t, name, obj):
    start = t.index('const %s = ' % name)
    end = t.index(';\r\n', start) + 1   # end points at the CR, so keep the ';' ourselves
    body = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    if ';\r\n' in body:
        raise SystemExit('ERR payload for %s would break the line anchor' % name)
    return t[:start] + 'const %s = %s;' % (name, body) + t[end:]


def resolver(indic):
    # The register carries some UC codes twice (a UC listed again in a later census
    # pass). The published LQAS rows use the earlier entry, so first occurrence wins.
    bycode = {}
    byname = {}
    for i, u in enumerate(indic['ucs']):
        bycode.setdefault(str(u[3]), []).append(i)
        byname.setdefault((u[1], u[0].strip().upper()), []).append(i)

    def resolve(lot):
        d = dindex(indic, lot['d'])
        code = bycode.get(str(lot['c'])) or []
        same = [i for i in code if indic['ucs'][i][1] == d]
        if len(same) == 1:
            return same[0], 'code'
        if not code:
            cand = byname.get((d, lot['u'].strip().upper()), [])
            if len(cand) != 1:
                raise SystemExit('ERR UC %s/%s (%s) has no unique register match (%d)'
                                 % (lot['d'], lot['u'], lot['c'], len(cand)))
            return cand[0], 'name'
        return code[0], 'code'
    return resolve


def dindex(indic, name):
    try:
        return indic['dn'].index(name)
    except ValueError:
        raise SystemExit('ERR district %r is not in INDIC.dn' % name)


def aggregate(lots):
    dd = {}
    for x in lots:
        d = dindex(INDIC, x['d'])
        a = dd.setdefault(d, dict(P=0, I=0, F=0, n=0,
                                  dn=0, tm=0, aw=0, mg=0, nb=0, rf=0, ot=0, tt=0))
        a[x['r']] += 1
        a['n'] += 1
        for k in ('dn', 'tm', 'aw', 'mg', 'nb', 'rf', 'ot', 'tt'):
            a[k] += x[k]
    return dd


def pct(p, n, dp):
    return round(100.0 * p / n, dp) if n else 0.0


def pky_row(a, dp):
    return [a['P'], a['I'], a['F'], pct(a['P'], a['n'], dp),
            a['dn'], a['tm'], a['aw'], -1, a['mg'], a['nb'], a['rf'], -1, -1, -1]


def pkx_payload(lots, resolve, dp, camp, note):
    dd = aggregate(lots)
    out = {}
    for d in sorted(dd):
        out[str(d)] = pky_row(dd[d], dp)
    uu = []
    seen = set()
    unmatched = []
    for x in sorted(lots, key=lambda r: (dindex(INDIC, r['d']), r['c'], r['u'])):
        ix, how = resolve(x)
        if ix in seen:
            raise SystemExit('ERR two lots land on one UC: %s %s' % (x['d'], x['u']))
        seen.add(ix)
        if how == 'name':
            unmatched.append('%s/%s' % (x['d'], x['u']))
        one = dict(P=1 if x['r'] == 'P' else 0, I=1 if x['r'] == 'I' else 0,
                   F=1 if x['r'] == 'F' else 0, n=1,
                   dn=x['dn'], tm=x['tm'], aw=x['aw'], mg=x['mg'],
                   nb=x['nb'], rf=x['rf'], ot=x['ot'], tt=x['tt'])
        uu.append([ix, pky_row(one, 1)])
    uu.sort(key=lambda r: r[0])
    return {'camp': camp, 'dd': out, 'uu': uu, 'note': note}, unmatched


def cin_lqas(cinn, lots, resolve, dp):
    dd = aggregate(lots)
    filled = 0
    for k, vals in cinn['dd'].items():
        a = dd.get(int(k))
        if a:
            vals[11:17] = [a['P'], a['I'], a['F'], pct(a['P'], a['n'], dp), a['dn'], a['tm']]
            filled += 1
        else:
            vals[11:17] = [-1] * 6
    byix = {r[0]: r for r in cinn['uu']}
    added = 0
    for x in lots:
        ix, _ = resolve(x)
        row = byix.get(ix)
        vals = [1 if x['r'] == 'P' else 0, 1 if x['r'] == 'I' else 0,
                1 if x['r'] == 'F' else 0, 100.0 if x['r'] == 'P' else 0.0,
                x['dn'], x['tm']]
        if row:
            row[1][11:17] = vals
        else:
            byix[ix] = [ix, [-1] * 11 + vals]
            added += 1
    cinn['uu'] = [byix[k] for k in sorted(byix)]
    return filled, added


def main():
    write = '--write' in sys.argv
    t = io.open(PATH, encoding='utf-8', newline='').read()
    global INDIC
    INDIC = load_const(t, 'INDIC')
    LQR = load_const(t, 'LQR')
    LQM = load_const(t, 'LQM')
    CINN = load_const(t, 'CINN')
    PKX = load_const(t, 'PKX')

    resolve = resolver(INDIC)
    nov = [x for x in LQR if x['ci'] == 0]
    sept = [x for x in LQR if x['ci'] == 1]
    if len(nov) != 80 or len(sept) != 120:
        raise SystemExit('ERR expected 80 Nov and 120 Sept lots, got %d/%d' % (len(nov), len(sept)))

    # --- guard 1: the builder reproduces the September rows already published ---
    old = [x for x in PKX['lqas'] if 'Sept' in x['camp']['l']]
    if len(old) != 1:
        raise SystemExit('ERR expected one Sept PKX entry')
    rebuilt, _ = pkx_payload(sept, resolve, 1, old[0]['camp'], old[0].get('note', ''))
    if rebuilt['dd'] != old[0]['dd']:
        raise SystemExit('ERR Sept district rows differ from the published PKX')
    # the published rows follow the portal export order; compare them by UC index
    if dict(rebuilt['uu']) != dict(old[0]['uu']):
        raise SystemExit('ERR Sept UC rows differ from the published PKX')

    # --- the November entry ---
    note = ('added from the EOC portal Post Campaign LQAS, UC wise export read 12-Nov-2026 03:03 '
            '(%s), reconciled lot for lot with the district summary read 12-Nov-2026 03:04 (%s); '
            'one lot per UC; asleep, VBNFM, FM without SV and inaccessible are not in that table; '
            "the portal's seven reasons leave its \"others\" uncarried; 2 ABOTABAD UCs (LORA, PAWA) "
            'now carry portal codes the register does not hold and were matched on district and name'
            % (UC_SRC, DIST_SRC))
    nov_pk, named = pkx_payload(nov, resolve, 1, {'l': 'SNID Nov 2026', 'y': '2026', 'ip': 1}, note)

    if (sum(1 for x in nov if x['r'] == 'P'), sum(1 for x in nov if x['r'] == 'I'),
            sum(1 for x in nov if x['r'] == 'F')) != (67, 9, 4):
        raise SystemExit('ERR pass/inter/fail counts moved')
    if sum(x['tt'] for x in nov) != 157 or sum(x['tm'] for x in nov) != 90:
        raise SystemExit('ERR missed-child totals moved')
    if len(nov_pk['dd']) != 16 or len(nov_pk['uu']) != 80:
        raise SystemExit('ERR Nov grain is not 16 districts / 80 lots')
    if named != ['ABOTABAD/PAWA', 'ABOTABAD/LORA']:
        raise SystemExit('ERR unexpected name-matched UCs: %r' % (named,))

    PKX['lqas'] = [nov_pk] + PKX['lqas']

    # --- the plate ---
    filled, added = cin_lqas(CINN, nov, resolve, 2)
    CINN['src'] = ('EOC portal Summary report, SNID Nov 2026 - district grain read 11-Nov-2026 15:25 '
                   '(live District-Wise table; the Export button returned province grain); UC rows for '
                   '975 matched UCs read 11-Nov-2026 16:01 from the live UC-Wise table; 21 UCs absent '
                   'from that table keep the 06-Nov-2026 20:47 row and still re-add to the district '
                   'totals; ICM columns from the IDIMS form 11 cluster download 04-Nov-2026 20:14; '
                   'LQAS columns joined from the EOC post-campaign E-LQAS UC-wise export read '
                   '12-Nov-2026 03:03 (%s), reconciled lot for lot with that round\'s district summary, '
                   'so the plate and the E-LQAS card read the same lots; the 2 ABOTABAD UCs on new '
                   'portal codes are matched to the register on district and name' % UC_SRC)

    # --- prose ---
    old_sent = (" if(sel.indexOf(CINNI)>=0)cap+=' <b>SNID Nov 2026</b> carries no LQAS column in this compiled sheet, so those columns drop out rather than print a number; that round&rsquo;s '+fmt(LQR.filter(x=>x.ci===0).length)+' lots are on the post-campaign LQAS page.';\r\n")
    new_sent = (" if(sel.indexOf(CINNI)>=0)cap+=' <b>SNID Nov 2026</b> LQAS is joined from the EOC post-campaign E-LQAS UC-wise export (read 12-Nov-2026): '+fmt(LQR.filter(x=>x.ci===0).length)+' lots, one per UC, in '+fmt(Array.from(new Set(LQR.filter(x=>x.ci===0).map(x=>x.d))).length)+' districts \\u2014 a district the sample did not reach prints &ldquo;&ndash;&rdquo;, and the &ldquo;others&rdquo; reason has no column in this taxonomy.';\r\n")
    if old_sent not in t:
        raise SystemExit('ERR plate caption anchor missing')
    t = t.replace(old_sent, new_sent)

    old_hint = 'SNID Sept 2026</b> is read from the compiled sheet; the rounds before it are merged from the dashboard&rsquo;s own campaign data pack into the same 17 columns, so this plate and the data pack can never disagree.'
    new_hint = 'SNID Sept 2026</b> is read from the compiled sheet; the rounds before it are merged from the dashboard&rsquo;s own campaign data pack into the same 17 columns, so this plate and the data pack can never disagree. <b>SNID Nov 2026</b> is that round&rsquo;s own live portal read, with its LQAS columns joined from the post-campaign E-LQAS export.'
    if old_hint not in t:
        raise SystemExit('ERR plate hint anchor missing')
    t = t.replace(old_hint, new_hint)

    t = swap_const(t, 'PKX', PKX)
    t = swap_const(t, 'CINN', CINN)

    # --- round trip ---
    if load_const(t, 'PKX') != PKX or load_const(t, 'CINN') != CINN:
        raise SystemExit('ERR const round trip failed')
    crlf, lf = t.count('\r\n'), t.count('\n')
    if crlf != lf:
        raise SystemExit('ERR line endings: %d CRLF vs %d LF' % (crlf, lf))

    print('sept guard OK (20 districts / 120 UCs reproduced exactly)')
    print('nov: 80 lots, %d districts, %d/%d/%d, %d missed, %d team-missed'
          % (len(nov_pk['dd']), 67, 9, 4, 157, 90))
    print('plate: %d district rows filled, %d UC rows added, %d UC rows total'
          % (filled, added, len(CINN['uu'])))
    print('name-matched UCs:', ', '.join(named))
    print('bytes %d -> %d' % (len(io.open(PATH, encoding='utf-8', newline='').read()), len(t)))
    if not write:
        print('DRY RUN - nothing written')
        return
    io.open(PATH, 'w', encoding='utf-8', newline='').write(t)
    print('WROTE', PATH)


if __name__ == '__main__':
    main()
