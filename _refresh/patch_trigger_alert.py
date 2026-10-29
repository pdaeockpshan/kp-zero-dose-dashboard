# -*- coding: utf-8 -*-
"""Adds the home-screen trigger alert: an animated docked card for MPQA trigger pendency.

Four atomic edits to the index.html master:
  1. alert CSS          - after the reminder styles
  2. `#alertCard`       - above the reminder bar
  3. alert JS           - rows, count-up, chip ping, show / hide
  4. the 1.7s auto-open - now opens the card, and the intensity modal becomes click-only

The card takes over from the MPQA intensity modal as the automatic alert: it docks top-right
without covering the page, shows once per browser session, pings the MPQA chip, and hands off
to the intensity popover. The modal's session flag and its auto-opener go with it, so there is
one alert on the home screen, not two.

ICM is left out until the Nov-26 round carries its own ICM triggers: the ICM table on the home
strip is still the SNID Sept-26 round, and announcing those pending UCs as today's alert would
read as current. It is one line in ALERTC to bring it back.

Master only: preview / public / internal pick the block up through push_master.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

A_CSS = '@media print{.rembar{display:none!important}}'
A_HTML = '<div class="rembar" id="remBar">'
A_FUNC = 'function renderNEP(){'
A_TIMER = '  setTimeout(mqWarnAuto,1700);'
A_CONST = "const MQWK='kpTrigWarn.v1';"
A_SET = " try{sessionStorage.setItem(MQWK,'1');}catch(e){}"
A_SEEN = "function mqWarnSeen(){try{return sessionStorage.getItem(MQWK)==='1';}catch(e){return false;}}"
A_AUTO = """function mqWarnAuto(){
 if(mqWarnSeen()||!mqWarnOnHome())return;
 const sp=el('snPop');
 if(sp&&sp.classList.contains('on')){
  document.addEventListener('snpop:closed',()=>{if(!mqWarnSeen()&&mqWarnOnHome())mqWarnOpen();},{once:true});
  return;
 }
 mqWarnOpen();
}"""

CSS = """.alertcard{position:fixed;top:16px;right:16px;z-index:60;width:336px;max-width:calc(100vw - 32px);background:#fff;border:1px solid var(--color-border);border-radius:14px;box-shadow:0 18px 44px rgba(15,23,42,.22);padding:12px 13px;opacity:0;transform:translateX(18px) scale(.985);transition:opacity .28s ease,transform .28s cubic-bezier(.2,.9,.3,1);pointer-events:none}
.alertcard.show{opacity:1;transform:none;pointer-events:auto}
.acHead{display:flex;align-items:center;gap:8px;margin:0 0 9px;font:700 12px var(--font-sans);letter-spacing:.01em;color:var(--color-text)}
.acDot{width:8px;height:8px;border-radius:50%;background:#be123c;animation:acDot 2.4s ease-out infinite}
.acX{all:unset;margin-left:auto;cursor:pointer;font:16px/1 var(--font-sans);color:var(--color-text-3);padding:1px 6px;border-radius:6px}
.acX:hover,.acX:focus-visible{background:var(--color-bg-secondary);color:var(--color-text)}
.acRow{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:11px;width:100%;cursor:pointer;padding:9px 10px;border-radius:10px;border:1px solid var(--color-border-light);border-left:4px solid var(--ac);margin:0 0 7px}
.acRow:hover,.acRow:focus-visible{background:var(--color-bg-secondary)}
.acRow:last-of-type{margin-bottom:9px}
.acNum{flex:0 0 auto;min-width:50px;font:800 25px/1 var(--font-mono);color:var(--ac);font-variant-numeric:tabular-nums}
.acTx{flex:1 1 auto;min-width:0;display:block}
.acTx b{display:block;font:700 12.5px/1.3 var(--font-sans);color:var(--color-text)}
.acTx i{display:block;font:11.5px/1.35 var(--font-sans);font-style:normal;color:var(--color-text-muted)}
.acTx u{display:block;font:10.5px/1.35 var(--font-sans);text-decoration:none;color:var(--color-text-3)}
.acGo{flex:0 0 auto;font:600 11px var(--font-sans);color:var(--ac)}
.acFoot{font:10.5px/1.4 var(--font-sans);color:var(--color-text-3)}
.acFoot b{color:var(--color-text);font-weight:600}
@keyframes acDot{0%{box-shadow:0 0 0 0 rgba(190,18,60,.45)}70%{box-shadow:0 0 0 8px rgba(190,18,60,0)}100%{box-shadow:0 0 0 0 rgba(190,18,60,0)}}
@keyframes acPop{from{transform:scale(.9);opacity:.5}to{transform:none;opacity:1}}
.alertcard.show .acRow{animation:acPop .34s cubic-bezier(.2,.9,.3,1) both}
.alertcard.show .acRow:nth-of-type(2){animation-delay:.09s}
@keyframes kpPing{0%{box-shadow:0 0 0 0 var(--pulse,rgba(190,18,60,.45))}70%{box-shadow:0 0 0 11px rgba(0,0,0,0)}100%{box-shadow:0 0 0 0 rgba(0,0,0,0)}}
.trigbtn.ping{animation:kpPing 1.8s ease-out 3}
@media(max-width:640px){.alertcard{left:10px;right:10px;top:auto;bottom:10px;width:auto;transform:translateY(14px)}}
@media(prefers-reduced-motion:reduce){.alertcard,.alertcard.show .acRow,.trigbtn.ping,.acDot{transition:none!important;animation:none!important}}"""

CARD = """<div class="alertcard" id="alertCard" role="status" aria-live="polite" aria-label="Control-room trigger alert">
 <div class="acHead"><span class="acDot"></span><span>Trigger alert</span><button class="acX" id="alertX" type="button" title="Dismiss" aria-label="Dismiss">&times;</button></div>
 <div id="alertBody"></div>
 <div class="acFoot" id="alertAsof"></div>
</div>
"""

JS = """// ---------- Home trigger alert: a docked card announcing pending trigger feedback ----------
// The card is the automatic home-screen alert; the intensity table and the per-trigger district
// tables stay one click away. It shows once per browser session, never covers the page, and
// counts up unless the reader has asked for reduced motion.
const ALERTK='kpTrigAlert.v1';
// ICM is deliberately absent: its trigger table still belongs to the SNID Sept-26 round. Add
// icm:['#b45309','rgba(180,83,9,.45)'] once the Nov-26 round carries ICM trigger feedback.
const ALERTC={mpqa:['#be123c','rgba(190,18,60,.45)']};
function alertRows(){
 const out=[];
 (TRIG.t||[]).forEach(t=>{
  if(!ALERTC[t.id])return;
  const pend=t.tot[2]-t.tot[3];if(pend<=0)return;
  const nD=Object.keys(t.d).filter(d=>(t.d[d][2]-t.d[d][3])>0).length;
  out.push({id:t.id,l:t.l,camp:t.camp,pend:pend,nD:nD,flagged:t.tot[2]});
 });
 return out;
}
function alertSeen(){try{return sessionStorage.getItem(ALERTK)==='1';}catch(e){return false;}}
function alertHide(){const c=el('alertCard');if(c)c.classList.remove('show');}
function acCount(n,to){
 const rm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(rm||!to){n.textContent=fmt(to);return;}
 const t0=(window.performance||Date).now(),D=820;
 (function step(t){const k=Math.min(1,(t-t0)/D),e=1-Math.pow(1-k,3);
  n.textContent=fmt(Math.round(to*e));if(k<1)requestAnimationFrame(step);})(t0);
}
function alertPing(){
 document.querySelectorAll('[data-trig]').forEach(b=>{
  const col=ALERTC[b.dataset.trig];if(!col)return;
  b.style.setProperty('--pulse',col[1]);
  b.classList.add('ping');
  setTimeout(()=>b.classList.remove('ping'),5600);
 });
}
function alertShow(){
 const c=el('alertCard');if(!c)return;
 const rows=alertRows();
 if(!rows.length){c.style.display='none';return;}
 el('alertBody').innerHTML=rows.map(r=>{
  const col=ALERTC[r.id];
  return '<button class="acRow" type="button" data-ac="'+r.id+'" style="--ac:'+col[0]+'">'+
   '<span class="acNum" data-to="'+r.pend+'">0</span>'+
   '<span class="acTx"><b>'+esc(r.l.replace(' trigger',''))+'</b>'+
   '<i>UCs pending feedback &middot; '+fmt(r.nD)+' '+(r.nD===1?'district':'districts')+'</i>'+
   '<u>'+esc(r.camp)+' &middot; '+fmt(r.flagged)+' flagged</u></span>'+
   '<span class="acGo">Open</span></button>';
 }).join('');
 el('alertAsof').innerHTML='Portal read <b>'+pendDay(TRIG.asof)+'</b> &middot; counts are union councils';
 c.querySelectorAll('[data-ac]').forEach(b=>{
  b.onclick=()=>{alertHide();if(b.dataset.ac==='mpqa')mqWarnOpen();else pendOpen(b.dataset.ac);};
 });
 c.classList.add('show');
 c.querySelectorAll('[data-to]').forEach(n=>acCount(n,+n.dataset.to));
 alertPing();
 c.onmouseenter=()=>clearTimeout(c._t);
 c._t=setTimeout(alertHide,13000);
 try{sessionStorage.setItem(ALERTK,'1');}catch(e){}
}
function alertAuto(){
 if(alertSeen()||!mqWarnOnHome())return;
 const sp=el('snPop');
 if(sp&&sp.classList.contains('on')){
  document.addEventListener('snpop:closed',()=>{if(!alertSeen()&&mqWarnOnHome())alertShow();},{once:true});
  return;
 }
 alertShow();
}
{
 const c=el('alertCard'),x=el('alertX');
 if(c&&x){
  x.onclick=()=>alertHide();
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape')alertHide();});
 }
}
"""


def _x(text):
    return text.replace('\n', '\r\n')


def patch(v):
    t = v.text
    for anchor, label in ((A_CSS, 'print rembar rule'), (A_HTML, 'remBar'), (A_FUNC, 'renderNEP'),
                          (A_TIMER, 'mqWarn auto-open'), (A_CONST, 'MQWK const'),
                          (A_SET, 'MQWK set'), (A_SEEN, 'mqWarnSeen'), (_x(A_AUTO), 'mqWarnAuto')):
        v.require(t.count(anchor) == 1, '%s anchor occurs %d times' % (label, t.count(anchor)))

    t = t.replace(A_CSS, A_CSS + '\r\n' + _x(CSS))
    t = t.replace(A_HTML, _x(CARD) + A_HTML)
    t = t.replace(A_FUNC, _x(JS) + '\r\n' + A_FUNC)
    t = t.replace(A_TIMER, '  setTimeout(alertAuto,2200);')

    # the modal is click-only now, so its session flag and auto-opener go
    t = t.replace(_x(A_CONST + '\n'), '')
    t = t.replace(_x(A_SET + '\n'), '')
    t = t.replace(_x(A_SEEN + '\n'), '')
    t = t.replace(_x(A_AUTO + '\n'), '')

    v.text = t
    for needle in ('id="alertCard"', 'id="alertBody"', 'id="alertX"', 'function alertShow(){',
                   'function alertAuto(){', 'kpTrigAlert.v1', 'setTimeout(alertAuto,2200);'):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    v.require(t.count('alertAuto') == 2, 'alertAuto occurs %d times' % t.count('alertAuto'))
    v.require(t.count('MQWK') == 0, 'MQWK still occurs %d times' % t.count('MQWK'))
    v.require(t.count('mqWarnAuto') == 0, 'mqWarnAuto still occurs %d times' % t.count('mqWarnAuto'))
    v.require(t.count('function mqWarnOnHome()') == 1, 'mqWarnOnHome lost')
    dashpatch.assert_crlf(v)
    v.changes.append('Home trigger alert card: MPQA + ICM, count-up and chip ping (%+d chars)'
                     % v.delta())


def main():
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'id="alertCard"' in v.text or 'kpTrigAlert.v1' in v.text:
        raise SystemExit('%s already has the trigger alert - not patching twice' % v.rel)
    patch(v)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK trigger alert master only - preview / public / internal pick it up through '
          'push_master.py')


if __name__ == '__main__':
    main()
