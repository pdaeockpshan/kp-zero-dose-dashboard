# -*- coding: utf-8 -*-
"""Zero Dose overview: blank the IDIMS and validation cards while SNID Nov-26 returns are awaited.

The "Digitized in IDIMS" card carries the Sept-26 linelist-vs-IDIMS exercise (DATA) and the
"Validated as vaccinated" card aggregates every validation round in VAL, so on the SNID Nov-26
view both showed earlier-round figures as if they belonged to the current campaign. The owner
wants them blank and labelled awaited until the Nov returns are compiled.

This patch:

  * adds HZNOVRET {dig, val} - the switch that says whether each SNID Nov-26 post-campaign
    return is compiled yet. Flip a key to true in the same round its return lands in DATA/VAL;
  * gates the hR2/hF2/hA2 and hR3/hF3/hA3 fills in renderHome: awaited ring, awaited facts,
    alarm hidden while the return is pending, restored for every other campaign;
  * gates the two KPI items in hzdStrip the same way;
  * scopes the populated Nov view to the Nov validation round (VAL cp 'SNID November 2026')
    so the card never re-absorbs the earlier campaigns once it fills;
  * updates the pane intro, the Nov strip note and the triangulation caption to say which
    figures are the post-campaign returns awaited.

Run:  python _refresh/patch_hzd_await_cards.py [--dry-run]
"""
import sys

import dashpatch


def crlf(t):
    return t.replace('\r\n', '\n').replace('\n', '\r\n')


OLD_A = crlf(r"""const hBub=(n,lab,tip,go)=>`<button class="hb ${n?'':'ok'}" data-hgo="${go}" title="${esc(tip)}"><i>${fmt(n)}</i>${lab?`<span>${lab}</span>`:''}</button>`;
function hAlarm(id,ttl,items){""")

NEW_A = crlf(r"""const hBub=(n,lab,tip,go)=>`<button class="hb ${n?'':'ok'}" data-hgo="${go}" title="${esc(tip)}"><i>${fmt(n)}</i>${lab?`<span>${lab}</span>`:''}</button>`;
const HZNOVRET={dig:false,val:false}; // SNID Nov-26 post-campaign returns: flip a key to true in the round its return lands in DATA / VAL
const HZNOVCP='SNID November 2026';
function hzdK(){const S=SYNCP&&SYNCP.hz?SYNCP.hz:null;return !S?'N':(['N','S','M','A'].find(x=>S.has(x))||'N');}
function hzdAwait(what){return hzdK()==='N'&&!HZNOVRET[what];}
function hAlarm(id,ttl,items){""")

OLD_DIG = crlf(r""" // 2. digitization
 const drep=S_(DATA,r=>r.rep), dll=S_(DATA,r=>r.ll), dp=drep?dll/drep*100:null;
 const dDl=Object.values(DATA.reduce((a,r)=>{(a[r.d]=a[r.d]||{r:0,l:0});a[r.d].r+=r.rep;a[r.d].l+=r.ll;return a;},{}));
 const dD=dDl.filter(x=>x.r&&x.l/x.r*100<90).length, dU=DATA.filter(r=>r.rep>0&&r.ll/r.rep*100<80).length, d0=DATA.filter(r=>r.rep>0&&r.ll===0).length;
 el('hR2').innerHTML=hRing(dp,'dig',104);
 el('hF2').innerHTML=`<div class="hf"><b>${fmt(dll)}</b>linelisted children entered, of ${fmt(drep)} reported in IDIMS</div><div class="hf"><b>${fmt(S_(DATA,gapOf))}</b>children still to be entered · ${DATA.length} UCs, 9 districts</div>`;
 hAlarm('hA2','Under-performing',[[dD,'districts',`${dD} districts below 90% digitized`,'overview'],[dU,'UCs',`${dU} UCs below 80% digitized, including ${d0} with no entries at all`,'followup']]);""")

NEW_DIG = crlf(r""" // 2. digitization
 if(hzdAwait('dig')){
  el('hR2').innerHTML=hRing(null,'dig',104);
  el('hF2').innerHTML=`<div class="hf"><b>–</b>IDIMS entry return awaited for ${esc(novLabel())}</div><div class="hf">No earlier round is shown; the card fills when the Nov digitization return is compiled</div>`;
  el('hA2').style.display='none';
 }else{
  el('hA2').style.display='';
 const drep=S_(DATA,r=>r.rep), dll=S_(DATA,r=>r.ll), dp=drep?dll/drep*100:null;
 const dDl=Object.values(DATA.reduce((a,r)=>{(a[r.d]=a[r.d]||{r:0,l:0});a[r.d].r+=r.rep;a[r.d].l+=r.ll;return a;},{}));
 const dD=dDl.filter(x=>x.r&&x.l/x.r*100<90).length, dU=DATA.filter(r=>r.rep>0&&r.ll/r.rep*100<80).length, d0=DATA.filter(r=>r.rep>0&&r.ll===0).length;
 el('hR2').innerHTML=hRing(dp,'dig',104);
 el('hF2').innerHTML=`<div class="hf"><b>${fmt(dll)}</b>linelisted children entered, of ${fmt(drep)} reported in IDIMS</div><div class="hf"><b>${fmt(S_(DATA,gapOf))}</b>children still to be entered · ${DATA.length} UCs, 9 districts</div>`;
 hAlarm('hA2','Under-performing',[[dD,'districts',`${dD} districts below 90% digitized`,'overview'],[dU,'UCs',`${dU} UCs below 80% digitized, including ${d0} with no entries at all`,'followup']]);
 }""")

OLD_VAL = crlf(r""" // 3. validation
 const v=aggV(VAL), vD=groupV(VAL,'d').filter(x=>x.n&&x.p<95).length, vU=groupV(VAL,'c').filter(x=>x.n&&x.p<90).length;
 el('hR3').innerHTML=hRing(v.p,'vac',104);
 el('hF3').innerHTML=`<div class="hf"><b>${fmt(v.n)}</b>children re-checked by validators · ${fmt(v.f)} forms, ${v.u} UCs</div><div class="hf"><b>${fmt(v.vn)}</b>children found not vaccinated</div>`;
 hAlarm('hA3','Under-performing',[[vD,'districts',`${vD} districts where less than 95% of validated children were vaccinated`,'vsum'],[vU,'UCs',`${vU} UCs where less than 90% of validated children were vaccinated`,'vfu']]);""")

NEW_VAL = crlf(r""" // 3. validation
 if(hzdAwait('val')){
  el('hR3').innerHTML=hRing(null,'vac',104);
  el('hF3').innerHTML=`<div class="hf"><b>–</b>validation return awaited for ${esc(novLabel())}</div><div class="hf">No earlier round is shown; the card fills when the Nov validation return is compiled</div>`;
  el('hA3').style.display='none';
 }else{
  el('hA3').style.display='';
 const V0=hzdK()==='N'?VAL.filter(r=>r.cp===HZNOVCP):VAL;
 const v=aggV(V0), vD=groupV(V0,'d').filter(x=>x.n&&x.p<95).length, vU=groupV(V0,'c').filter(x=>x.n&&x.p<90).length;
 el('hR3').innerHTML=hRing(v.p,'vac',104);
 el('hF3').innerHTML=`<div class="hf"><b>${fmt(v.n)}</b>children re-checked by validators · ${fmt(v.f)} forms, ${v.u} UCs</div><div class="hf"><b>${fmt(v.vn)}</b>children found not vaccinated</div>`;
 hAlarm('hA3','Under-performing',[[vD,'districts',`${vD} districts where less than 95% of validated children were vaccinated`,'vsum'],[vU,'UCs',`${vU} UCs where less than 90% of validated children were vaccinated`,'vfu']]);
 }""")

OLD_STRIP = crlf(r"""function hzdStrip(){const inZ=ZD.filter(matchG), z=agg(inZ), D=DATA.filter(matchG), dr=S_(D,r=>r.rep), dl=S_(D,r=>r.ll), v=aggV(VAL.filter(matchG)), k=hzCampaign();""")

NEW_STRIP = crlf(r"""function hzdStrip(){const inZ=ZD.filter(matchG), z=agg(inZ), D=DATA.filter(matchG), dr=S_(D,r=>r.rep), dl=S_(D,r=>r.ll), k=hzCampaign(), V0=k==='N'?VAL.filter(r=>r.cp===HZNOVCP):VAL, v=aggV(V0.filter(matchG));""")

OLD_DIGITEM = crlf(r""" const dig=['Digitized in IDIMS',D.length?pc(dr?dl/dr*100:null):'–',D.length?`${fmt(dl)} of ${fmt(dr)} entered · ${fmt(Math.max(0,dr-dl))} not entered`:'no IDIMS data for this area (9 districts only)','#6d28d9'];""")

NEW_DIGITEM = crlf(r""" const dig=(k==='N'&&!HZNOVRET.dig)?['Digitized in IDIMS','–','post-campaign digitization return awaited','#6d28d9']:['Digitized in IDIMS',D.length?pc(dr?dl/dr*100:null):'–',D.length?`${fmt(dl)} of ${fmt(dr)} entered · ${fmt(Math.max(0,dr-dl))} not entered`:'no IDIMS data for this area (9 districts only)','#6d28d9'];""")

OLD_VALITEM = crlf(r""" const val=['Validated vaccinated',v.n?pc(v.p):'–',v.n?`${fmt(v.vy)} of ${fmt(v.n)} children checked · ${fmt(v.vn)} not vaccinated`:'no validation records','#15803d'];""")

NEW_VALITEM = crlf(r""" const val=(k==='N'&&!HZNOVRET.val)?['Validated vaccinated','–','post-campaign validation return awaited','#15803d']:['Validated vaccinated',v.n?pc(v.p):'–',v.n?`${fmt(v.vy)} of ${fmt(v.n)} children checked · ${fmt(v.vn)} not vaccinated`:'no validation records','#15803d'];""")

OLD_NOTE = ('Its covered figure, LQAS and validation are the post-campaign returns awaited; '
            'SNID Sept-26 remains the last measured coverage.')
NEW_NOTE = ('Its covered figure, LQAS, IDIMS digitization and validation are the post-campaign '
            'returns awaited; SNID Sept-26 remains the last measured coverage.')

OLD_INTRO = ('SNID Nov-26 recorded zero dose is in; its coverage, LQAS and validation are the '
             'post-campaign returns awaited.')
NEW_INTRO = ('SNID Nov-26 recorded zero dose is in; its coverage, LQAS, IDIMS digitization and '
             'validation are the post-campaign returns awaited; the IDIMS and validation cards stay '
             'blank until those returns are compiled rather than showing an earlier round.')

OLD_CAP = ('Reported coverage, IDIMS entry and validation compared district by district. '
           'A flag shows where they do not match.')
NEW_CAP = ('Reported coverage, IDIMS entry and validation compared district by district. '
           'A flag shows where they do not match. IDIMS entry and validation are not '
           'campaign-scoped; they show the last compiled round.')

PAIRS = [
    (OLD_A, NEW_A, 'helpers'),
    (OLD_DIG, NEW_DIG, 'digitization block'),
    (OLD_VAL, NEW_VAL, 'validation block'),
    (OLD_STRIP, NEW_STRIP, 'strip header'),
    (OLD_DIGITEM, NEW_DIGITEM, 'dig item'),
    (OLD_VALITEM, NEW_VALITEM, 'val item'),
    (OLD_NOTE, NEW_NOTE, 'nov note'),
    (OLD_INTRO, NEW_INTRO, 'pane intro'),
    (OLD_CAP, NEW_CAP, 'tri caption'),
]


def main(argv):
    dry = '--dry-run' in argv
    cfg, vs = dashpatch.load_variants()
    stamp = dashpatch.pkt_stamp()
    for v in vs:
        for old, new, label in PAIRS:
            n = v.text.count(old)
            v.require(n == 1, '%s: expected 1 hit, found %d' % (label, n))
            v.text = v.text.replace(old, new)
        dashpatch.set_stamp(v, stamp)
        for token in ("const HZNOVRET={dig:false,val:false}",
                      "if(hzdAwait('dig'))", "if(hzdAwait('val'))",
                      "HZNOVRET.dig)?['Digitized in IDIMS','–'",
                      "HZNOVRET.val)?['Validated vaccinated','–'",
                      "V0=k==='N'?VAL.filter(r=>r.cp===HZNOVCP):VAL",
                      "the IDIMS and validation cards stay blank"):
            v.require(token in v.text, 'missing %s' % token)
        v.require(v.text.count('function hzdAwait(') == 1, 'hzdAwait duplicated')
        v.require(v.text.count('function hzdK(') == 1, 'hzdK duplicated')
        print('%s: %+d chars' % (v.rel, v.delta()))
    dashpatch.commit_variants(vs)
    dashpatch.check_identical(cfg, vs)
    print('stamp -> %s' % stamp)
    if dry:
        print('DRY RUN - nothing written')
        return 0
    dashpatch.write_variants(vs)
    dashpatch.append_version(cfg, 'Zero Dose overview: the IDIMS digitization and validation cards stay blank and '
                                  'awaited on the SNID Nov-26 view instead of carrying Sept-26 figures; they fill, '
                                  'Nov-scoped, when the Nov returns are compiled.', dry=False)
    print('PATCHED %d variants + version files' % len(vs))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
