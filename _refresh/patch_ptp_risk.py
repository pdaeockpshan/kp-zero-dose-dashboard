"""Fold the transit-point evidence into the combined UC risk score (master only).

Design rules this build keeps:
  * three new signals, and each one is only scored where its own evidence exists: the panel lapse
    (2 pts) for UCs whose posts IDIMS actually lists on the PTP panel, the report yield (1 pt) for
    UCs with 20+ reports, the survey finding rate (1 pt) only for districts with 100+ spot surveys -
    three surveys cannot set a ceiling for every UC in a district;
  * the house convention is kept: a signal with data present counts towards what the UC could score
    even when it scores zero, so a working transit channel lowers the percentage and a UC with no
    transit posts is neither punished nor diluted;
  * the lapse denominator runs from the UC's own first report to the export's newest month and drops
    the panel's three province-wide hole months, because a post that joined in 2025 is not lapsed
    for 2016;
  * yield is zero-dose children found per 100 reports, with a plausibility cap of 500: the export
    holds values no catchment can produce (up to 7,138 per 100), and those UCs are left unscored on
    that signal rather than ranked at the top of it;
  * no PTP coverage percentage enters the score or the copy - the meaning of the panel's own Coverage
    column is still unconfirmed with IDIMS;
  * the survey signal is never shown as a percentage: the export's `schk` counts spot-survey
    checklists and `ptp_missed_5` counts children, so their ratio is unvaccinated under-5s found per
    100 surveys and can exceed 100 (DIKHAN logs 526 children over 511 surveys, which is one child per
    survey, not an impossible 103%);
  * the district join uses PTP.dr (the raw IDIMS spelling), which is the spelling the zero-dose and
    EPI payloads use; CHITRAL and the two unsplit WAZIR-S units cannot be matched to one dashboard
    district, so they set no ceiling anywhere.
Bands (under 10% / under 25% of months, 75+ zero-dose per 100 reports, 20+ unvaccinated per 100
surveys) are the measured distribution's own quartiles, not invented cut-offs - see
_focus/ptp_pick2.py in the session directory for the search that picked them.
Only the master is touched; syncing the other three variants is a publishing action - and they do not
carry the PTPM payload yet, so the score would silently lose the survey signal there.
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = lambda x: x.replace('\n', '\r\n')

REL = 'index.html'
DASH = '\u2013'

A_SECTION = '// ================= (6) COMBINED UC RISK SCORE =================\r\n'
JS_START = '// ---------- transit-point inputs to the risk score'
JS_LAST = (" if (P.ptm)why.push(fmt(Math.round(h.rate)) + ' unvaccinated under-5s found per 100 "
           "spot surveys in the district');}\n"
           '}\n')  # the block's own tail, in source form, before the CRLF conversion

RW_OLD = "['wpv','Confirmed polio case in the UC',5]];"
RW_NEW = ("['wpv','Confirmed polio case in the UC',5],\r\n"
          " ['ptl','Transit-point posts filed in under a tenth of the months (2) / a quarter (1)',2],\r\n"
          " ['pty','Transit reports finding many zero-dose children (75+ per 100 reports)',1],\r\n"
          " ['ptm','HRMP spot surveys finding many unvaccinated under-5s (20+ per 100 surveys)',1]];")
RWS_OLD = "wpv:'Polio case'};"
RWS_NEW = "wpv:'Polio case',ptl:'PTP lapse',pty:'PTP yield',ptm:'PTP surveys'};"
DECL_OLD = '_RK=ZD.map(z=>{const c=z.c, P={}, why=[];'
DECL_NEW = '_RK=ZD.map(z=>{const c=z.c, P={}, why=[];let PTPV={};'
MAX_OLD = '  const max=RW.reduce('
MAX_NEW = ('  {const X = ptpRiskSignals(), PU = X.u[c], PH = X.d[z.d];\r\n'
           '   ptpRiskPut(P, why, X, PU, PH);\r\n'
           '   PTPV = {f: PU && PU.due ? PU.filed : null, r: PU ? PU.rows : null,\r\n'
           '    z: PU && PU.rows >= 20 && PU.zpr != null && PU.zpr <= X.cap ? PU.zpr : null,\r\n'
           '    s: PH && PH.srv >= X.min ? PH.rate : null, n: PH ? PH.srv : null};}\r\n'
           + MAX_OLD)
RET_OLD = 'lq:LQU[c]||null,why};});'
RET_NEW = 'lq:LQU[c]||null,ptp:PTPV,why};});'
WP_OLD = '{k:\'wpv\',l:\'Polio\',n:1,f:x=>x.wpv?\'<b class="dn">\'+x.wpv+\'</b>\':\'\'}'
WP_NEW = WP_OLD + (
    ",{k:'ptp',l:'PTP months filed',n:1,sv:x=>x.ptp.f,f:x=>x.ptp.f==null?'" + DASH + "':rgN(x.ptp.f,50,25)+'%'}"
    ",{k:'ptpz',l:'PTP ZD per 100 reports',n:1,sv:x=>x.ptp.z,f:x=>x.ptp.z==null?'" + DASH + "':fmt(Math.round(x.ptp.z))}"
    ",{k:'ptpm',l:'Unvacc. per 100 surveys',n:1,sv:x=>x.ptp.s,f:x=>x.ptp.s==null?'" + DASH + "':fmt(Math.round(x.ptp.s)),"
    "tt:'The HRMP spot-survey exports: ptp_missed_5 children found unvaccinated per 100 spot-survey checklists in the district, "
    "counted only where 100 or more surveys stand behind it. A count per 100 surveys, not a percentage - the two columns are "
    "checklists and children, so one child per survey reads 100.'}")
CSVH_OLD = "'ZD AFP cases','Polio cases','Why it scores'"
CSVH_NEW = ("'ZD AFP cases','Polio cases','PTP months filed %','PTP reports',"
            "'PTP zero-dose per 100 reports','PTP spot surveys','PTP unvaccinated under-5s per 100 spot surveys',"
            "'Why it scores'")
CSVR_OLD = "x.afp,x.wpv,x.why.join('; ')"
CSVR_NEW = "x.afp,x.wpv,r1(x.ptp.f),x.ptp.r,r1(x.ptp.z),x.ptp.n,r1(x.ptp.s),x.why.join('; ')"
CNT_OLD = 'UCs scored on up to 8 indicators'
CNT_NEW = 'UCs scored on up to ${RW.length} indicators'
HINT_OLD = 'Follows the Division / District / Tehsil filters.`+'
HINT_NEW = ('Follows the Division / District / Tehsil filters.`+\r\n'
            '  `<b>Transit-point inputs:</b> the share of months the panel posts filed for this UC '
            '(2 points under a tenth, 1 under a quarter, counted only where IDIMS lists posts), the '
            'zero-dose children those reports found per 100 reports (1 point at 75+, only for UCs with '
            '20 or more reports and a rate under 500, above which the export is not believable), and '
            'the unvaccinated under-5s the HRMP spot surveys find per 100 checklists in the district '
            '(1 point at 20+, only where 100 or more surveys stand behind it - that ratio is children '
            'per 100 surveys, not a percentage, and a district can honestly pass 100). No PTP coverage '
            'percentage is '
            'used anywhere - what that column counts is still unconfirmed with IDIMS.`+')
CAP_OLD = ('Surveillance covers every UC, so the zero-dose AFP (3) and polio case (5) points always '
           'count as possible. LQAS (4) counts only for UCs assessed in the last rounds, so a passed '
           'lot is evidence that lowers the score.')
CAP_NEW = (CAP_OLD + ' The three transit-point inputs work the same way: the panel lapse (2) counts '
           'only for UCs whose posts IDIMS lists on the panel, the report yield (1) only where a UC '
           'has 20 or more reports, and the survey finding (1) only in districts with 100 or more '
           'spot surveys - so a UC with a working transit channel is credited for it, and one with no '
           'transit posts is neither punished nor diluted. The yield and survey inputs are children '
           'per 100 reports or checklists, not percentages.')

EDITS = [(RW_OLD, RW_NEW), (RWS_OLD, RWS_NEW), (DECL_OLD, DECL_NEW), (MAX_OLD, MAX_NEW),
         (RET_OLD, RET_NEW), (WP_OLD, WP_NEW), (CSVH_OLD, CSVH_NEW), (CSVR_OLD, CSVR_NEW),
         (CNT_OLD, CNT_NEW), (HINT_OLD, HINT_NEW), (CAP_OLD, CAP_NEW)]

JS = '''
''' + JS_START + '''
// Two of the three signals come from the daily permanent-transit-point panel (PTP) and one from the
// HRMP field-check forms (PTPM). Both are keyed to the raw IDIMS district spelling (PTP.dr), which is
// the spelling the zero-dose and EPI payloads use, so an unsplit unit such as CHITRAL joins nothing
// and sets no ceiling. Nothing here reads the panel's own Coverage column.
var _PTX = null;
function ptpRiskSignals(){
 if(typeof PTP === 'undefined' || typeof PTPM === 'undefined')return {v: null, u: {}, d: {}, cap: 500, min: 100};
 if(_PTX && _PTX.v === PTP)return _PTX;
 const Q = {}, UK = {}, MK = {};
 (PTP.q || []).forEach((k, i) => { Q[k] = i; });
 (PTP.uk || []).forEach((k, i) => { UK[k] = i; });
 (PTPM.mk || []).forEach((k, i) => { MK[k] = i; });
 const hole = {};
 (PTP.gap || []).forEach(g => { hole[g] = 1; });
 // month slots the panel could have been filed in, the payload's own slot numbering, minus the
 // months the export is blank province-wide
 const slots = [];
 PTP.yr.forEach((y, yi) => { for (let m = 1; m <= 12; m++)if (!hole[y + '-' + (m < 10 ? '0' + m : '' + m)])slots.push(yi * 12 + m - 1); });
 const dueFrom = {};
 for (let i = slots.length - 1; i >= 0; i--)dueFrom[slots[i]] = (dueFrom[slots[i + 1]] || 0) + 1;
 const U = {};
 PTP.u.forEach(r => {
  const mc = r[UK.mc] || [], yc = r[UK.yc] || [], filed = {};
  let first = null;
  mc.forEach(c => { filed[c[0]] = 1; if (first === null || c[0] < first)first = c[0]; });
  const nf = Object.keys(filed).length, rows = yc.reduce((s, c) => s + ((c[1] || [])[Q.rows] || 0), 0);
  const due = first === null ? 0 : (dueFrom[first] || 0);
  U[r[UK.code]] = {posts: r[UK.posts], months: nf, due: due, first: first,
   filed: due ? nf / due * 100 : null, rows: rows, zpr: rows ? r[UK.zd] / rows * 100 : null};
 });
 // the field-check exports count two different things: schk is a spot-survey checklist and smiss is
 // the children found unvaccinated inside those checklists, so the ratio is children per 100 surveys
 // and a district that logs about one per survey reads just over 100 - never a coverage percentage
 const agg = {};
 PTPM.d.forEach(row => { let a = 0, b = 0;
  (row[1] || []).forEach(c => { a += c[1][MK.schk] || 0; b += c[1][MK.smiss] || 0; });
  agg[row[0]] = [a, b]; });
 const D = {};
 PTPM.ev.forEach(e => { const raw = (PTP.dr || [])[e[0]];
  if (raw == null)return;
  const ab = agg[e[0]] || [0, 0];
  D[raw] = {srv: ab[0], miss: ab[1], rate: ab[0] ? ab[1] / ab[0] * 100 : null}; });
 return _PTX = {v: PTP, u: U, d: D, cap: 500, min: 100};
}
function ptpRiskPut(P, why, X, u, h){
 if(u && u.due){const f = u.filed;
  P.ptl = f < 10 ? 2 : f < 25 ? 1 : 0;
  if (P.ptl)why.push('PTP posts filed in only ' + pc(f) + ' of the months since '
   + PTP.yr[Math.floor(u.first / 12)] + '-' + _MON[u.first % 12]);}
 if(u && u.rows >= 20 && u.zpr != null && u.zpr <= X.cap){P.pty = u.zpr >= 75 ? 1 : 0;
  if (P.pty)why.push(fmt(Math.round(u.zpr)) + ' zero-dose per 100 PTP reports');}
 if(h && h.srv >= X.min && h.rate != null){P.ptm = h.rate >= 20 ? 1 : 0;
''' + JS_LAST


def patch(v, dry):
    s = v.text
    for probe in ('ptpRiskSignals', "'ptl','Transit-point posts", 'ptp:PTPV'):
        v.require(s.count(probe) == 0, 'already present (%s)' % probe)
    v.require(s.count(A_SECTION) == 1 and s.count(JS_START) == 0, 'the section anchor is not usable')
    for old, new in EDITS:
        v.require(s.count(old) == 1, 'anchor found %d times: %r' % (s.count(old), old[:70]))
    js = CRLF(JS.lstrip('\n'))
    v.require(js.startswith(JS_START) and js.endswith(CRLF(JS_LAST)), 'the js block lost its shape')
    v.require('\r\r' not in js, 'the js block carries a doubled CR')
    s = s.replace(A_SECTION, js + A_SECTION, 1)
    for old, new in EDITS:
        s = s.replace(old, new, 1)
    for probe, n in (('function ptpRiskSignals', 1), ('function ptpRiskPut', 1),
                     ('ptpRiskPut(P, why, X, PU, PH)', 1), ('ptp:PTPV', 1),
                     ("'PTP months filed'", 1), ("'PTP spot surveys'", 1),
                     ('r1(x.ptp.f)', 1), ('r1(x.ptp.s)', 1), ('RW.length', 1),
                     ("ptl:'PTP lapse'", 1)):
        v.require(s.count(probe) == n, '%r occurs %d times after the patch' % (probe, s.count(probe)))
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    print('   js +%d chars, %d copy/table edits, net %+d chars'
          % (len(js), len(EDITS), sum(len(n) - len(o) for o, n in EDITS)))
    if not dry:
        dashpatch.write_variants([v])


def unpatch(v, dry):
    """Strip an applied fold, so the weights can be revised and re-applied."""
    s = v.text
    a, b = s.find(JS_START), s.find(A_SECTION)
    v.require(a > 0 and b > a, 'not applied: the js block is not delimited')
    s = s[:a] + s[b:]
    for old, new in EDITS:
        v.require(s.count(new) == 1, 'reversal did not match: %r' % new[:70])
        s = s.replace(new, old, 1)
    for probe in ('ptpRiskSignals', 'ptpRiskPut', "'ptl','Transit-point", 'x.ptp.', 'PTPV',
                  "'PTP months filed'", 'RW.length'):
        v.require(probe not in s, '%s survived the removal' % probe)
    v.text = s
    dashpatch.assert_crlf(v)
    print('   removed the transit-point fold')
    if not dry:
        dashpatch.write_variants([v])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true',
                    help='remove a previously applied fold so the weights can be revised')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    print('variants: ' + ', '.join('%s %s' % (v.rel, v.md5()[:8]) for v in vs))
    sel = [x for x in vs if x.rel == REL]
    if len(sel) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % REL)
    v = sel[0]
    if 'const PTPM = ' not in v.text:
        raise SystemExit('the HRMP field-check payload is not in %s yet' % v.rel)
    print('%s master only (%s)' % ('un-patching' if a.unpatch else 'patching', v.rel))
    (unpatch if a.unpatch else patch)(v, a.dry_run)
    print('   %s: %.1f KB -> %.1f KB (%+.1f KB)'
          % (v.rel, len(v.orig) / 1024.0, len(v.text) / 1024.0, v.delta() / 1024.0))
    print('   md5 %s' % v.md5())
    if a.dry_run:
        print('DRY RUN: nothing written.')
    else:
        print('master only: the other three variants follow only on the owner\'s word, and they have '
              'no PTPM payload yet.')


if __name__ == '__main__':
    main()
