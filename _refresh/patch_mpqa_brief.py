# -*- coding: utf-8 -*-
"""Add the MPQA crux to the pre-campaign core-team brief (#cardNEPB / #nepB).

WHY (owner, 25-Oct-2026): "include MPQA crux in Pre-campaign brief so that districts can
know what is happening, a few lines would be enough with summary." The brief carried NEAP
readiness, the countdown calendar and the three push tiers, but nothing on micro-plan
quality - so a district could read its whole brief and not see that its assigned MPQA
reviews are unfiled, even though that is the one MPQA figure it owes.

The section keeps the framing that patch_mpqa_framing.py established for the rest of the
dashboard: the assigned list is a targeted sample of low-performing / flagged UCs, scoring
every UC is not a requirement, the assigned share of the campaign is context rather than a
coverage target, the three bands are shares of the UCs already reported of deliberately
problem-selected plans (so not a micro-plan quality rate), and reported / assigned is the
one obligation. It follows the brief's own division picker (#fNEPDV, NEPDV) like every
other section, and it also adds one line to "Ask to the core team" naming the outstanding
reviews and the district furthest behind.

CHAINED PATCH, master-independent: it only reads `const MPQA` at render time and reuses the
brief's own helpers (dvOf, DNb, ucN, pcT, fmt, pc, esc), so it is independent of
patch_mpqa_ui.py / patch_sitrep_ui.py / patch_mpqa_framing.py in the patch order - but it
is meaningless before patch_mpqa_ui.py has landed the MPQA block, and the module checks for
that. It edits all four variants so no variant ships a brief without the crux, bumps the PKT
stamp on every variant and appends the version.txt note (the same bookkeeping
push_master.py would do, without needing the owner's publishing word).

Usage:
  python _refresh/patch_mpqa_brief.py --dry-run    anchor checks + delta report, writes nothing
  python _refresh/patch_mpqa_brief.py              patch all four variants and bump the stamp
  python _refresh/patch_mpqa_brief.py --unpatch    remove the section again (--dry-run works too)
  python _refresh/patch_mpqa_brief.py --no-stamp   patch the text, leave the PKT stamp alone
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import dashpatch

MARK_A = r'// MPQA-BRIEF-START (patch_mpqa_brief.py)'
MARK_B = r'// MPQA-BRIEF-END'

# the brief builds its sections into `secs`; the crux goes in after the countdown-calendar
# section and before the push tiers, which is where the "what is happening" reading sits.
ANCHOR = r''' let t1line;'''

ASK_OLD = r'''with their NEAP updates.']]);'''
ASK_NEW = r'''with their NEAP updates.'].concat(mqAsk?[mqAsk]:[])]);'''

# every string literal stays on ONE physical line: a line ending with ' followed by a line
# starting with ' is a second statement, and a line starting with +' after a line ending with
# + is a unary plus - both pass node --check and only show up in the rendered text.
BLOCK = r'''
 // MPQA-BRIEF-START (patch_mpqa_brief.py)
 let mqAsk='';
 if(typeof MPQA!=='undefined'&&MPQA&&MPQA.d){
  const MQ=MPQA, mqD=Object.keys(MQ.d).filter(d=>!NEPDV||dvOf(d)===NEPDV).sort();
  const mqT=[0,0,0,0,0];
  mqD.forEach(d=>MQ.d[d].forEach((x,j)=>{mqT[j]+=x;}));
  const mqA=mqT[0], mqR=mqT[1], mqU=mqA-mqR, mqCam=mqD.reduce((s,d)=>s+ucN(d),0);
  const mqOwe=mqD.filter(d=>MQ.d[d][0]>MQ.d[d][1]).sort((a,b)=>(MQ.d[b][0]-MQ.d[b][1])-(MQ.d[a][0]-MQ.d[a][1]));
  const mqSer=mqD.filter(d=>MQ.d[d][4]>0).sort((a,b)=>MQ.d[b][4]-MQ.d[a][4]);
  const mqB=[];
  if(!mqD.length){
   mqB.push('No micro-plan quality assessment round covers '+dvL+' \u2014 the assigned sample sits with the other divisions.');
  }else{
   mqB.push('MPQA scores a <b>targeted sample</b>: '+fmt(mqA)+' union council'+(mqA===1?'':'s')+' across '+mqD.length+(mqD.length===1?' district':' districts')+' in this view, picked among low performers or flagged on another indicator. Scoring every UC of a district is <b>not</b> a requirement'+(mqCam?', so the '+pcT(mqA,mqCam)+' of the '+fmt(mqCam)+' campaign UC'+(mqCam===1?'':'s')+' here that '+((mqCam===1)?'is':'are')+' assigned is context, never a coverage target':'')+'.');
   mqB.push('Reported so far: <b>'+fmt(mqR)+' of '+fmt(mqA)+'</b> assigned UC'+(mqA===1?'':'s')+' ('+pc(mqA?mqR/mqA*100:null)+'), leaving <b>'+fmt(mqU)+'</b> review'+(mqU===1?'':'s')+' still to file \u2014 the one figure a district actually owes, and a short count here is a reporting slippage, not proof the micro-plan was never checked.');
   mqB.push('Of the '+fmt(mqR)+' reported UC'+(mqR===1?'':'s')+': '+fmt(mqT[2])+' pass (90+), '+fmt(mqT[3])+' needs improvement (70-89), '+fmt(mqT[4])+' serious issue'+(mqT[4]===1?'':'s')+' (under 70). These are deliberately problem-selected plans, so the bands are not a micro-plan quality rate for a district or for KP.');
   if(mqOwe.length)mqB.push('Furthest behind on filing: '+mqOwe.slice(0,4).map(d=>'<b>'+DNb(d)+'</b> ('+fmt(MQ.d[d][0]-MQ.d[d][1])+' of '+fmt(MQ.d[d][0])+' assigned)').join(', ')+(mqOwe.length>4?', and '+(mqOwe.length-4)+' more \u2014':' \u2014')+' a district can pass every plan it has looked at and still be behind on its own list.');
   if(mqSer.length)mqB.push('Already scored under 70: '+mqSer.slice(0,4).map(d=>'<b>'+DNb(d)+'</b> '+fmt(MQ.d[d][4])).join(', ')+(mqSer.length>4?', and more \u2014':' \u2014')+' each plan behind those scores needs reworking before the campaign, not another review.');
   mqB.push('Per-UC desk / field / over-all scores are in the MPQA card below (source <b>'+esc(MQ.src)+'</b>, '+esc(MQ.gen)+').');
   if(mqU>0)mqAsk=fmt(mqU)+' outstanding MPQA review'+(mqU>1?'s':'')+' on the assigned sample'+(mqOwe.length?', starting with '+DNb(mqOwe[0])+' ('+fmt(MQ.d[mqOwe[0]][0]-MQ.d[mqOwe[0]][1])+' still to file)':'')+(mqT[4]>0?' \u2014 file them as reporting, and rework the '+fmt(mqT[4])+' micro-plan'+(mqT[4]>1?'s':'')+' scored under 70.':'.');
  }
  secs.push(['Micro-plan quality assessment (MPQA)'+(NEPDV?' \u2014 '+dvL:' province-wide'),mqB]);
 }
 // MPQA-BRIEF-END
'''


def patch(v, dry):
    s = v.text
    v.require(s.count(MARK_A) == 0, 'the brief already carries the MPQA crux')
    v.require('const MPQA = ' in s, 'no MPQA payload in this variant - patch_mpqa_ui.py comes first')
    v.require(s.count(ANCHOR) == 1, 'anchor found %d times: %r' % (s.count(ANCHOR), ANCHOR))
    v.require(s.count(ASK_OLD) == 1, 'ask-line anchor found %d times' % s.count(ASK_OLD))
    blk = BLOCK.lstrip('\n').replace('\n', '\r\n')
    v.require(blk.startswith(' ' + MARK_A) and blk.rstrip('\r\n').endswith(MARK_B),
              'the block no longer sits between its own markers')
    s = s.replace(ANCHOR, blk + ANCHOR, 1)
    s = s.replace(ASK_OLD, ASK_NEW, 1)
    v.require(s.count('function renderNEP') == 1, 'renderNEP count changed')
    v.require(s.count('let mqAsk=') == 1, 'the ask-line variable insert failed')
    v.require(s.count('Micro-plan quality assessment (MPQA)') >= 2, 'the brief section title is missing')
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    v.changes.append('MPQA crux in the pre-campaign brief (%+d chars)' % v.delta())
    print('  %-42s %+8d chars' % (v.rel, v.delta()))


def unpatch(v, dry):
    s = v.text
    v.require(s.count(MARK_A) == 1, 'the MPQA crux is not applied as a marked block')
    v.require(s.count(MARK_B) == 1, 'the closing marker is missing')
    a, b = s.find(MARK_A), s.find(MARK_B)
    v.require(a > 0 and b > a, 'the markers are out of order')
    head = s.rfind('\r\n', 0, a) + 2
    tail = s.find('\r\n', b)
    v.require(head > 1 and tail > b, 'cannot bound the marked region')
    s = s[:head] + s[tail + 2:]
    v.require(s.count(ASK_NEW) == 1, 'the ask line is not where it was changed')
    s = s.replace(ASK_NEW, ASK_OLD, 1)
    v.require('mqAsk' not in s, 'a fragment of the MPQA crux survived the removal')
    v.require(s.count(ANCHOR) == 1, 'the brief anchor was damaged')
    v.text = s
    dashpatch.assert_crlf(v)
    v.require('\r\r\n' not in v.text, 'doubled CR introduced')
    v.changes.append('MPQA crux removed from the brief (%+d chars)' % v.delta())
    print('  %-42s %+8d chars' % (v.rel, v.delta()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--no-stamp', action='store_true', help='leave the PKT timestamps alone')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    old = dashpatch.get_stamp(vs[0])
    stamps = set(dashpatch.get_stamp(v) for v in vs)
    if len(stamps) != 1:
        raise SystemExit('ABORT: the variants disagree on the stamp: %s' % stamps)
    new = dashpatch.pkt_stamp(datetime.datetime.now(dashpatch.PKT))
    step = unpatch if a.unpatch else patch
    for v in vs:
        step(v, a.dry_run)
        if not a.no_stamp and not a.unpatch:
            dashpatch.set_stamp(v, new, old)
            v.changes.append('stamp %s -> %s' % (old, new))
    sums = dashpatch.check_identical(cfg, vs)
    print('identical group md5: %s' % sums)
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    for v in vs:
        print('WROTE %s' % v.rel)
    if not a.no_stamp and not a.unpatch:
        dashpatch.append_version(cfg, 'Pre-campaign brief: added the MPQA crux (assigned sample, %s '
                                      % 'reported / outstanding / bands) with the push lines, per division. '
                                      'Timestamp refresh %s PKT' % new)
        print('stamp: %s -> %s' % (old, new))
    print('OK mpqa-brief')
    return 0


if __name__ == '__main__':
    sys.exit(main())
