"""Home: the three questions now lead with the concluded SNID Nov-26 round.

The campaign has closed. What the leadership cards still show is the Sept-26
coverage read, because Nov-26's covered column only fills when the next round
reports; LQAS lots and the validation register also return after the round. So
the cards name the Nov-26 recorded count, keep the measured Sept-26 gap as the
last closed reading, and say which post-campaign returns are still awaited.
"""
import sys
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
import dashpatch


def edits():
    E = []

    def add(old, new, n, why):
        E.append((old, new, n, why))

    add('<span>All of KP \u00b7 click a question to show or hide its details'
        '<button class="hqall" id="hQall" type="button">Show all details</button></span>',
        '<span>All of KP \u00b7 SNID Nov-26 has concluded \u2014 its coverage, LQAS and validation are the '
        'post-campaign returns still awaited \u00b7 click a question to show or hide its details'
        '<button class="hqall" id="hQall" type="button">Show all details</button></span>',
        1, 'section subtitle')

    add(" const S=gapStats(()=>true,()=>true), mc=(MISM.camps||[])[0]||'', "
        "cK=SCOV?'S':ZD.some(r=>r.cM!=null)?'M':'A';\r\n",
        " const S=gapStats(()=>true,()=>true), mc=(MISM.camps||[])[0]||'', "
        "cK=SCOV?'S':ZD.some(r=>r.cM!=null)?'M':'A';\r\n"
        " const NVr=(typeof ADV!=='undefined'&&ADV&&ADV.r&&ADV.r.length)?ADV.r[ADV.r.length-1]:null,"
        "NVn=NVr?NVr.length:0,NVrep=NVr?NVr.reduce((a,x)=>a+(x[1]||0),0):0,"
        "NVopen=!!NVr&&!NVr.some(x=>x[2]!=null),"
        "NVlbl=(typeof ADV!=='undefined'&&ADV&&ADV.c&&ADV.c.length)?ADV.c[ADV.c.length-1].n:'SNID Nov 2026';\r\n",
        1, 'q1 nov handle')

    add(" el('hQ1b').innerHTML=`<b>${fmt(S.st)}</b><span>children still missed after ${esc(mc)} "
        "(${pc(S.stp)} of target)</span>`;\r\n",
        " el('hQ1b').innerHTML=(NVopen&&NVrep)?`<b>${fmt(NVrep)}</b><span>zero-dose children recorded in "
        "${esc(NVlbl)} (${fmt(NVn)} UCs) \u2014 the round has concluded; coverage, LQAS and validation are "
        "post-campaign reads still returning, so the last measured still-missed is ${fmt(S.st)} after "
        "${esc(mc)} (${pc(S.stp)} of target)</span>`:`<b>${fmt(S.st)}</b><span>children still missed after "
        "${esc(mc)} (${pc(S.stp)} of target)</span>`;\r\n",
        1, 'q1 headline')

    add('`<div><b>${fmt(S.zun)}</b> zero-dose children not yet covered \u00b7 ',
        '`<div><b>${fmt(S.zun)}</b> zero-dose children not yet covered in ${esc(CAMP[cK])} \u00b7 ',
        1, 'q1 zun label')

    add('ZD follow-up: ${esc(CAMP[cK])}.',
        '${esc(NVlbl)} concluded with ${fmt(NVrep)} zero-dose children recorded and no covered figure yet; '
        'its coverage, LQAS and validation are the post-campaign returns awaited.',
        1, 'q1 follow-up')

    add(":'<b>\u2013</b><span>no LQAS data</span>';",
        ":iteam!=null?`<b>${Math.round(iteam)}%</b><span>of children the monitors found missed in the "
        "${esc(NVlbl)} ICM returns so far were missed by teams (not visited or missed in the house) \u00b7 "
        "LQAS is a post-campaign read still awaited</span>`:"
        "'<b>\u2013</b><span>no monitoring or LQAS data yet</span>';",
        1, 'q2 headline')

    add(" el('hQ2f').innerHTML=`<div><b>LQAS</b> (${fmt(lt)} children${lt<500?', small sample':''})</div>"
        "${bar(lq,lt)}<div><b>Monitors during the campaign (ICM)</b> (${fmt(mi)} children)</div>${bar(icm,mi)}`+\r\n",
        " el('hQ2f').innerHTML=(lt?`<div><b>LQAS</b> (${fmt(lt)} children${lt<500?', small sample':''})</div>"
        "${bar(lq,lt)}`:`<div><b>LQAS</b> \u00b7 not yet reported for ${esc(XD.C?XD.C.l:'')} \u2014 lots are "
        "scored after the round</div>`)+`<div><b>Monitors during the campaign (ICM)</b> (${fmt(mi)} children)"
        "</div>${bar(icm,mi)}`+\r\n",
        1, 'q2 detail')

    add("  `<span>Polio cases 2026</span>",
        "  `<span>${esc(NVlbl)}</span><span><b>${fmt(NVrep)}</b> recorded \u00b7 covered, LQAS and validation "
        "awaited</span>`+\r\n  `<span>Polio cases 2026</span>",
        1, 'q3 nov row')

    return E


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    E = edits()
    for v in vs:
        s = v.text
        for old, new, n, why in E:
            got = s.count(old)
            v.require(got == n, '%s: expected %d hit(s) of %r, found %d' % (why, n, old[:70], got))
            s = s.replace(old, new)
        v.require('NVopen' in s and s.count('NVrep') >= 4, 'nov handle missing')
        v.text = s
        v.changes.append('%d three-question edits' % len(E))
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    old_stamp = dashpatch.get_stamp(vs[0])
    new_stamp = old_stamp if dry else dashpatch.pkt_stamp()
    if new_stamp != old_stamp:
        for v in vs:
            dashpatch.set_stamp(v, new_stamp, old_stamp)
    for v in vs:
        print('%-42s %+8d chars' % (v.rel, v.delta()))
    print('stamp: %s -> %s' % (old_stamp, new_stamp))
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, 'Home three questions read SNID Nov-26 as concluded: Nov recorded count '
                            'leads, Sept-26 stays the last measured gap, coverage/LQAS/validation named as '
                            'the post-campaign returns awaited. Timestamp refresh %s PKT.' % new_stamp)
    print('PATCHED %d variants' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
