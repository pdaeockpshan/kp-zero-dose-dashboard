# -*- coding: utf-8 -*-
"""Adds the MPQA trigger intensity warning: a home-screen banner and a district popover.

Four atomic edits to the index.html master:
  1. intensity CSS               - after the pendency tab styles
  2. `#trigWarn` banner          - above the three trigger chips
  3. `#mqWarnPop` dialog markup  - before the SNID launch popup
  4. grading + renderer JS       - mqIntensity / renderTrigWarn / mqWarnOpen, and an
                                  auto-open that waits for the SNID scope popup to close
It also makes snPopClose announce itself so the two popovers never stack.

Master only: preview / public / internal pick the block up through push_master.py,
which is a publish and needs the owner's go-ahead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

A_CSS = '.pndtab.on{background:#0f172a;color:#fff;border-color:#0f172a}'
A_ROW = '<div class="trigrow" id="trigRow"></div>'
A_POP = '<!-- ============ SNID launch popup: countdown + schematic scope map ============ -->'
A_FUNC = 'function renderNEP(){'
A_CALL = 'renderHomeAct(); renderTRIG();'
CALLNEW = 'renderHomeAct(); renderTRIG(); renderTrigWarn();'
A_SNCLOSE = ("function snPopClose(){const p=el('snPop');if(p)p.classList.remove('on');}")
SNCLOSENEW = ("function snPopClose(){const p=el('snPop');if(p)p.classList.remove('on');"
              "try{document.dispatchEvent(new Event('snpop:closed'));}catch(e){}}")

CSS = """.trigwarn{display:flex;align-items:center;gap:11px;cursor:pointer;margin:0 0 11px;padding:9px 13px;border-radius:10px;border:1px solid rgba(190,18,60,.28);border-left:5px solid #be123c;background:linear-gradient(90deg,rgba(190,18,60,.09),rgba(190,18,60,.02));font:12.5px/1.45 var(--font-sans);color:var(--color-text)}
.trigwarn:hover,.trigwarn:focus-visible{background:rgba(190,18,60,.13);outline:none}
.trigwarn .twg{flex:0 0 auto;font:700 10.5px var(--font-sans);letter-spacing:.04em;text-transform:uppercase;color:#fff;background:#be123c;border-radius:999px;padding:3px 9px}
.trigwarn .twt{flex:1 1 auto;min-width:0}
.trigwarn .twgo{flex:0 0 auto;font:600 11.5px var(--font-sans);color:#be123c}
.trigbtn .twpc{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:999px;font:700 10px var(--font-sans);color:#fff;vertical-align:1px}
.mqgauge{display:flex;height:24px;border-radius:7px;overflow:hidden;border:1px solid var(--color-border-light);margin:2px 0 7px}
.mqgauge i{display:block;height:100%;min-width:2px}
.mqbar{display:inline-block;width:52px;height:7px;border-radius:4px;background:var(--color-border-light);vertical-align:middle;overflow:hidden;margin-right:5px}
.mqbar i{display:block;height:100%;border-radius:4px}
.mqdots{display:inline-block;margin-left:5px;vertical-align:1px}
.mqdots span{display:inline-block;width:6px;height:6px;border-radius:50%;background:#b91c1c}
@media(max-width:900px){.trigwarn{flex-wrap:wrap}}
@media(max-width:900px){.hsec{flex-wrap:wrap;gap:2px 10px}.hsec h2{flex:1 1 100%}}"""

BANNER = '<div class="trigwarn" id="trigWarn" role="button" tabindex="0"></div>\n'

POP = """<!-- ============ MPQA trigger intensity: home warning + district breakdown ============ -->
<div class="snpop" id="mqWarnPop" role="dialog" aria-modal="true" aria-labelledby="mqWarnTitle">
 <div class="snpopbox pndbox">
  <div class="snpophd">
   <div style="min-width:0"><h3 id="mqWarnTitle">MPQA trigger — intensity by district</h3><div class="snpopsub" id="mqWarnSub"></div></div>
   <button class="snpopx" id="mqWarnX" type="button" title="Close" aria-label="Close">&times;</button>
  </div>
  <div id="mqWarnGauge"></div>
  <div class="scroll" style="max-height:42vh;margin-top:6px"><table id="mqWarnTbl"></table></div>
  <div class="cap" id="mqWarnCap"></div>
  <div class="snpopft">
   <button class="btn" id="mqWarnGo" type="button">MPQA pendency table</button>
   <button class="btn" id="mqWarnNep" type="button">Pre-campaign readiness</button>
   <button class="btn" id="mqWarnX2" type="button">Close</button>
  </div>
 </div>
</div>"""

JS = """// ---------- MPQA trigger intensity: how hard the trigger is hitting each district ----------
// Intensity is the share of a district's MPQA-assigned UCs that met either trigger flag. The
// bands are printed in the caption; a serious finding lifts a district to High on its own.
const MQWK='kpTrigWarn.v1';
const MQG=[['High','st-behind','#be123c'],['Moderate','st-watch','#d97706'],['Watch','st-no','#64748b'],['Clear','st-on','#15803d']];
function mqGrade(pc,ser){const i=(ser>0||pc>=15)?0:(pc>=5?1:(pc>0?2:3));return {l:MQG[i][0],cls:MQG[i][1],c:MQG[i][2]};}
function mqIntensity(){
 const T=(TRIG.t||[]).filter(x=>x.id==='mpqa')[0];if(!T)return null;
 const rows=Object.keys(T.d).map(d=>{
  const v=T.d[d],m=(MPQA.d&&MPQA.d[d])||[0,0,0,0,0],ass=m[0],pc=ass?v[2]*100/ass:0;
  return {d:d,ass:ass,t:v[2],a:v[0],b:v[1],ser:m[4],rep:m[1],fb:v[3],pend:v[2]-v[3],pc:pc,g:mqGrade(pc,m[4])};});
 rows.sort((x,y)=>y.t-x.t||y.pc-x.pc||(x.d<y.d?-1:1));
 const s=rows.reduce((o,r)=>({ass:o.ass+r.ass,t:o.t+r.t,ser:o.ser+r.ser,rep:o.rep+r.rep,fb:o.fb+r.fb,pend:o.pend+r.pend}),{ass:0,t:0,ser:0,rep:0,fb:0,pend:0});
 s.pc=s.ass?s.t*100/s.ass:0;
 return {rows:rows,sum:s,grade:mqGrade(s.pc,s.ser),camp:T.camp,asof:TRIG.asof,
  nD:rows.filter(r=>r.t>0).length,nSer:rows.filter(r=>r.ser>0).length,nPend:rows.filter(r=>r.pend>0).length,n:rows.length};
}
function renderTrigWarn(){
 const b=el('trigWarn');if(!b)return;
 const M=mqIntensity();if(!M){b.style.display='none';return;}
 const s=M.sum,g=M.grade;
 b.style.borderLeftColor=g.c;
 b.innerHTML='<span class="twg" style="background:'+g.c+'">MPQA '+esc(g.l)+'</span>'+
  '<span class="twt"><b>'+fmt(s.t)+' of '+fmt(s.ass)+'</b> assigned UCs met the MPQA trigger ('+s.pc.toFixed(1)+'%) · <b>'+fmt(s.ser)+'</b> serious in '+fmt(M.nSer)+' districts · <b>'+fmt(s.pend)+'</b> trigger feedbacks pending in '+fmt(M.nPend)+' districts</span>'+
  '<span class="twgo">Intensity by district &rarr;</span>';
 b.setAttribute('aria-label','MPQA trigger intensity '+g.l+' — '+fmt(s.t)+' of '+fmt(s.ass)+' assigned UCs flagged. Open the district breakdown.');
 b.onclick=mqWarnOpen;
 b.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();mqWarnOpen();}};
 const chip=document.querySelector('[data-trig="mpqa"]');
 if(chip){
  chip.style.setProperty('--tc',g.c);
  const sub=chip.querySelector('.ts2');
  if(sub&&!chip.querySelector('.twpc')){const e=document.createElement('span');e.className='twpc';e.style.background=g.c;e.textContent=g.l.toUpperCase()+' '+s.pc.toFixed(0)+'%';sub.appendChild(e);}
 }
}
function mqWarnOpen(){
 const p=el('mqWarnPop');if(!p)return;
 const M=mqIntensity();if(!M)return;
 const s=M.sum,g=M.grade,im=s.t-s.ser,cl=Math.max(0,s.ass-s.t),ad=pendDay(M.asof);
 el('mqWarnSub').innerHTML='<span class="st '+g.cls+'">'+esc(g.l)+'</span> · <b>'+fmt(s.t)+'</b> of <b>'+fmt(s.ass)+'</b> assigned UCs flagged ('+s.pc.toFixed(1)+'%) · <b>'+fmt(s.ser)+'</b> serious in '+fmt(M.nSer)+' districts · <b>'+fmt(s.pend)+'</b> trigger feedbacks pending in '+fmt(M.nPend)+' of '+fmt(M.n)+' districts · '+esc(M.camp)+', portal read '+ad;
 el('mqWarnGauge').innerHTML='<div class="mqgauge" role="img" aria-label="'+fmt(s.ser)+' serious, '+fmt(im)+' needs improvement, '+fmt(cl)+' clear UCs">'+
  '<i style="flex:'+s.ser+';background:#be123c"></i><i style="flex:'+im+';background:#f59e0b"></i><i style="flex:'+cl+';background:#d7dde7"></i></div>'+
  '<div class="snleg"><span><i style="background:#be123c"></i>Serious '+fmt(s.ser)+'</span><span><i style="background:#f59e0b"></i>Needs improvement '+fmt(im)+'</span><span><i style="background:#d7dde7"></i>Not flagged '+fmt(cl)+'</span><span>of '+fmt(s.ass)+' assigned UCs</span></div>';
 drawTable('mqWarnTbl',[
  {k:'d',l:'District',f:x=>'<b>'+esc(x.d)+'</b>'+(x.ser?'<span class="mqdots" title="'+fmt(x.ser)+' serious"><span></span></span>':'')},
  {k:'t',l:'Flagged',n:1,tt:'Union councils that met either MPQA trigger flag'},
  {k:'ass',l:'Assigned',n:1,tt:'UCs assigned for micro-plan assessment in this round'},
  {k:'pc',l:'Intensity',n:1,tt:'Flagged UCs as a share of the assigned UCs',f:x=>'<span class="mqbar"><i style="width:'+Math.min(100,x.pc).toFixed(1)+'%;background:'+x.g.c+'"></i></span>'+x.pc.toFixed(1)+'%'},
  {k:'ser',l:'Serious',n:1,tt:'UCs with a serious MPQA finding',f:x=>pendZero(x.ser,true)},
  {k:'fb',l:'Feedback',n:1,tt:'Trigger feedback entered in the portal for those UCs'},
  {k:'pend',l:'Pending',n:1,tt:'Flagged UCs with no trigger feedback yet',f:x=>pendZero(x.pend,true)}],
  M.rows,'t',-1);
 el('mqWarnCap').textContent='Intensity is flagged UCs as a share of the UCs assigned for micro-plan assessment: High at 15% or more (or any serious finding), Moderate 5-15%, Watch under 5%, Clear none. '+
  'A red dot marks a district carrying a serious MPQA finding. Assignment is the MPQA sample, not every UC, so a district with two or three assigned UCs moves a long way on one UC — read the count beside the share. '+
  'Report filing is a separate measure: '+fmt(s.rep)+' of '+fmt(s.ass)+' assigned UCs filed a report, '+fmt(s.ass-s.rep)+' did not. Counts are UCs, not children; '+M.camp+', portal read '+ad+'.';
 p.classList.add('on');
 try{sessionStorage.setItem(MQWK,'1');}catch(e){}
}
function mqWarnClose(){const p=el('mqWarnPop');if(p)p.classList.remove('on');}
function mqWarnSeen(){try{return sessionStorage.getItem(MQWK)==='1';}catch(e){return false;}}
function mqWarnOnHome(){const on=document.querySelector('.pane.on');return !!on&&on.id==='p-home';}
function mqWarnAuto(){
 if(mqWarnSeen()||!mqWarnOnHome())return;
 const sp=el('snPop');
 if(sp&&sp.classList.contains('on')){
  document.addEventListener('snpop:closed',()=>{if(!mqWarnSeen()&&mqWarnOnHome())mqWarnOpen();},{once:true});
  return;
 }
 mqWarnOpen();
}
{
 const p=el('mqWarnPop');
 if(p){
  el('mqWarnX').onclick=mqWarnClose;el('mqWarnX2').onclick=mqWarnClose;
  p.onclick=ev=>{if(ev.target===p)mqWarnClose();};
  el('mqWarnGo').onclick=()=>{mqWarnClose();pendOpen('mpqa');};
  el('mqWarnNep').onclick=()=>{mqWarnClose();pendOpen('neap');};
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&p.classList.contains('on'))mqWarnClose();});
  setTimeout(mqWarnAuto,1700);
 }
}
"""


def _x(text):
    return text.replace('\n', '\r\n')


def patch(v):
    t = v.text
    for anchor, label in ((A_CSS, 'pndtab.on'), (A_ROW, 'trigRow'), (A_POP, 'SNID popup comment'),
                          (A_FUNC, 'renderNEP'), (A_CALL, 'home call site'), (A_SNCLOSE, 'snPopClose')):
        v.require(t.count(anchor) == 1, '%s anchor occurs %d times' % (label, t.count(anchor)))
    t = t.replace(A_CSS, A_CSS + '\r\n' + _x(CSS))
    t = t.replace(A_ROW, _x(BANNER) + A_ROW)
    t = t.replace(A_POP, _x(POP) + '\r\n\r\n' + A_POP)
    t = t.replace(A_FUNC, _x(JS) + '\r\n' + A_FUNC)
    t = t.replace(A_CALL, CALLNEW)
    t = t.replace(A_SNCLOSE, SNCLOSENEW)
    v.text = t
    for needle in ('id="trigWarn"', 'class="trigwarn"', 'id="mqWarnPop"', 'id="mqWarnTbl"',
                   'id="mqWarnGauge"', 'function mqIntensity(){', 'function renderTrigWarn(){',
                   'function mqWarnOpen(){', CALLNEW):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    # dispatched in snPopClose, listened for in mqWarnAuto
    v.require(t.count('snpop:closed') == 2, 'snpop:closed occurs %d times' % t.count('snpop:closed'))
    dashpatch.assert_crlf(v)
    v.changes.append('MPQA trigger intensity warning: home banner + district popover (%+d chars)'
                     % v.delta())


def main():
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'id="mqWarnPop"' in v.text or 'kpTrigWarn.v1' in v.text:
        raise SystemExit('%s already has the intensity warning - not patching twice' % v.rel)
    patch(v)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK mpqa-warning master only - preview / public / internal pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
