# -*- coding: utf-8 -*-
"""Put the Nov-26 focus shortlist into the standalone transit-point presentation (master only).

What it does
  * passes the two shortlists the "Where to focus" card already computes (PTPX.RF district units, PTPX.UF
    union councils) through ptpDeckData(), so the deck is built from exactly the figures on the page;
  * inserts one slide before "Recommended actions": five KPIs, the district units the channels flag most,
    and the action line for each of the top three, with the Nov-26 readiness gates that are still open.

Rules this build keeps
  * no PTP coverage percentage anywhere; the panel counts reports, not distinct children;
  * the HRMP spot-survey column stays "unvaccinated under-5s per 100 checklists", never a percentage;
  * channel flags are judged on the whole window, so the slide says so rather than letting a month
    selection silently change who is on the list;
  * only the top six shortlisted units are listed on the slide - the card holds all of them and the CSV.
Only the master is touched; the other three variants carry no PTPM payload and syncing them is a
publishing action that needs the owner's word.
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

CRLF = lambda x: x.replace('\n', '\r\n')
REL = 'index.html'

DATA_OLD = 'UR:X.UR.slice(),scope:pptScope(),'
DATA_NEW = 'UR:X.UR.slice(),RF:X.RF||[],UF:X.UF||[],scope:pptScope(),'

ACT_OLD = ' // 14 Actions\r\n'
FOCUS = """ // 14 Focus for the next campaign
 {const FR=X.RF||[],FU=X.UF||[];
  const f1=FR.filter(x=>x.n>=1),f2=FR.filter(x=>x.n>=2),f3=FR.filter(x=>x.n>=3),
   u2=FU.filter(x=>x.n>=2),u3=FU.filter(x=>x.n>=3),
   sil=FR.filter(x=>x.quiet||x.lapsed||x.thin),
   gapAll=FR.reduce((s,x)=>s+x.gap,0),gapF=f2.reduce((s,x)=>s+x.gap,0),gapU=u2.reduce((s,x)=>s+x.gap,0);
  const SH=f2.length?f2:f1, sw=SH.slice(0,6);
  const s=base('Where to focus for SNID Nov-26',CYN,
   (f2.length?f2.length+' of '+FR.length+' district units in scope are flagged by two or more independent channels, '+f3.length+' of them by three or more. ':'On this selection no district unit carries two channel flags; '+f1.length+' carries one. ')+
   'Each channel is a different source, so a unit only appears where they agree on a gap. A channel is judged on the whole '+X.win+' window, not on the period above.');
  kpis(s,[{l:'Districts flagged 2+',v:String(f2.length)+' / '+FR.length,s:f3.length+' at three or more, '+f1.length+' at one',vc:CYN},
   {l:'Units with a weak channel',v:String(sil.length),s:'never filed, gone quiet, or under a quarter of months',vc:AMB},
   {l:'Children with no covered figure',v:n0(gapAll),s:'reported on transit councils in '+X.camp,vc:RED},
   {l:'Shortlist share of that gap',v:gapAll?p1(gapF/gapAll*100):'\\u2013',s:n0(gapF)+' of '+n0(gapAll),vc:ORA},
   {l:'Councils flagged 2+',v:n0(u2.length),s:n0(u3.length)+' at three or more, from '+n0(FU.length)+' councils',vc:PUR}],CYN,1.32);
  s.addText('The district units the channels flag most',{x:0.5,y:2.74,w:8.0,h:0.3,fontFace:F,fontSize:12,bold:true,color:TXT});
  table(s,['District','Division','Chan. of 5','No covered figure','Covered %','OPV-3 %','Channel months %','VH+high UCs','Unvacc. per 100 surveys'],
   sw.map(x=>[cut(x.dn,22),cut(x.dv,13),x.n+' of 5',x.gap?n0(x.gap):'\\u2013',p1(x.zp),p1(x.ep),p1(x.monp),
    x.hv==null?'\\u2013':n0(x.hv),x.srv==null?'\\u2013':(x.srv<FOC.min?n0(Math.round(x.srate))+' of '+n0(x.srv):n0(Math.round(x.srate)))]),
   {x:0.5,y:3.02,w:12.33,colW:[2.4,1.25,0.9,1.6,1.05,1.05,1.25,1.25,1.58],col:CYN});
  const RM=SH.filter(x=>x.rdy&&x.rdy.length), NOJ=FR.filter(x=>x.hv==null).map(x=>x.raw);
  const B=sw.slice(0,3).map(x=>x.dn+' ('+x.n+' of 5 channels): '+cut((x.act.slice(0,2).join('; ')||'no action beyond the shortlist itself')+'.',165));
  if(RM.length)B.push('Nov-26 readiness still open: '+RM.slice(0,3).map(x=>x.dn+' - '+x.rdy[0]).join(', ')+(RM.length>3?' and '+(RM.length-3)+' more':'')+'.');
  bullets(s,B,{x:0.5,y:5.25,w:12.33,h:1.2,fs:10});
  note(s,'Covered figures are '+X.camp+'\\u2019s own export, not yet confirmed by a later round; OPV-3 is the cumulative routine window. A dash means the source has no row for that unit: '+(NOJ.length?'the '+NOJ.length+' units that IDIMS lists under a name the campaign data does not use ('+cut(NOJ.join(', '),60)+') carry no campaign, EPI or risk cell, only their own channel and findings. ':'')+n0(gapU)+' children sit behind the '+n0(u2.length)+' union councils flagged by two or more checks. Full shortlists and CSV downloads: the dashboard tab.',
   {x:0.5,y:6.48,w:12.33,h:0.48,fs:10,i:true});}

"""

EDITS = [(DATA_OLD, DATA_NEW), (ACT_OLD, CRLF(FOCUS) + ' // 15 Actions\r\n')]


def patch(v, dry):
    s = v.text
    v.require('function renderPTPDeck' in s, 'the transit point deck is not in this build')
    v.require('function focDist' in s and 'RF:RF,UF:UF' in s,
              'the Nov-26 focus card has to be patched in first')
    v.require("Where to focus for SNID Nov-26',CYN" not in s, 'the focus slide is already in the deck')
    for old, new in EDITS:
        v.require(s.count(old) == 1, 'anchor found %d times: %r' % (s.count(old), old[:70]))
    for old, new in EDITS:
        s = s.replace(old, new, 1)
    for probe, n in (("RF:X.RF||[],UF:X.UF||[]", 1), ("Where to focus for SNID Nov-26',CYN", 1),
                     ('// 15 Actions', 1), ('// 14 Actions', 0),
                     ("x.srv<FOC.min?n0(Math.round(x.srate))", 1), ('Chan. of 5', 1)):
        v.require(s.count(probe) == n, '%r occurs %d times after the patch (want %d)' % (probe, s.count(probe), n))
    v.require(s.count(' return pptx;') == 8, 'the deck lost its return shape')
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    print('   %d anchors, net %+d chars' % (len(EDITS), sum(len(n) - len(o) for o, n in EDITS)))
    if not dry:
        dashpatch.write_variants([v])


def unpatch(v, dry):
    """Remove the slide by its markers, so wording edits to FOCUS stay reversible."""
    s = v.text
    a = s.find(' // 14 Focus for the next campaign')
    b = s.find(' // 15 Actions\r\n')
    v.require(a > 0 and b > a, 'not applied: the focus slide is not delimited by its markers')
    s = s[:a] + s[b:]
    v.require(s.count(' // 15 Actions\r\n') == 1, 'the actions comment is not where the patch left it')
    s = s.replace(' // 15 Actions\r\n', ACT_OLD, 1)
    v.require(s.count(DATA_NEW) == 1, 'the deck data does not carry the shortlists')
    s = s.replace(DATA_NEW, DATA_OLD, 1)
    for probe in ('FOCUS for the next campaign', "Where to focus for SNID Nov-26',CYN",
                  '15 Actions', 'RF:X.RF||[]'):
        v.require(probe not in s, '%s survived the removal' % probe)
    v.require(s.count(' return pptx;') == 8, 'the deck lost its return shape')
    v.text = s
    dashpatch.assert_crlf(v)
    print('   removed the Nov-26 focus slide')
    if not dry:
        dashpatch.write_variants([v])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true',
                    help='remove a previously applied focus slide')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    print('variants: ' + ', '.join('%s %s' % (v.rel, v.md5()[:8]) for v in vs))
    sel = [x for x in vs if x.rel == REL]
    if len(sel) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % REL)
    v = sel[0]
    if 'const PTP = ' not in v.text:
        raise SystemExit('%s has no PTP payload' % v.rel)
    print('%s master only (%s)' % ('un-patching' if a.unpatch else 'patching', v.rel))
    (unpatch if a.unpatch else patch)(v, a.dry_run)
    print('   %s: %.1f KB -> %.1f KB (%+.1f KB)'
          % (v.rel, len(v.orig) / 1024.0, len(v.text) / 1024.0, v.delta() / 1024.0))
    print('   md5 %s' % v.md5())
    if a.dry_run:
        print('DRY RUN: nothing written.')
    else:
        print('master only: the other three variants follow only on the owner\'s word.')


if __name__ == '__main__':
    main()
