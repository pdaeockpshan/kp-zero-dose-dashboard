# -*- coding: utf-8 -*-
"""Adds the daily trigger reminder generator: one mail to EOC-KP, MNE officer in cc.

Four atomic edits to the index.html master:
  1. reminder CSS            - after the intensity-warning styles
  2. `#remBar` action row    - under the three trigger chips
  3. `#remPop` dialog        - before the MPQA intensity popup
  4. reminder JS             - pending rows, since-yesterday delta, body / .eml / CSV

The reminder is action-only: districts with pending MPQA feedback. ICM joins the list when
the Nov-26 round starts and the portal begins recording feedback against it; admin coverage
stays out until EOC confirms that trigger expects feedback.
Recipient addresses are NOT embedded in the page - they are entered once and kept
in this browser's localStorage, so nothing personal enters the repo or Pages.

Master only: preview / public / internal pick the block up through push_master.py,
which is a publish and needs the owner's go-ahead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

A_CSS = '.trigwarn .twgo{flex:0 0 auto;font:600 11.5px var(--font-sans);color:#be123c}'
A_ROW = '<div class="trigrow" id="trigRow"></div>'
A_POP = '<!-- ============ MPQA trigger intensity: home warning + district breakdown ============ -->'
A_FUNC = 'function renderTRIG(){'

CSS = """.rembar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:9px 0 0}
.rembtn{display:inline-flex;align-items:center;gap:8px;cursor:pointer;border:1px solid rgba(15,23,42,.16);background:#fff;border-radius:9px;padding:7px 12px;font:12px/1.2 var(--font-sans);color:var(--color-text)}
.rembtn:hover,.rembtn:focus-visible{border-color:#0f172a;outline:none}
.rembtn .rdot{width:8px;height:8px;border-radius:50%;background:#be123c;flex:0 0 auto}
.rembtn.clear .rdot{background:#15803d}
.rembtn b{font-weight:700}
.rembtn .rs{color:var(--color-text-3)}
.remst{font:11.5px var(--font-sans);color:var(--color-text-3)}
.remst b{color:var(--color-text);font-weight:700}
.remwho{margin:0 0 7px;font:11.5px/1.5 var(--font-sans);color:var(--color-text-3)}
.remwho b{color:var(--color-text);font-weight:600}
.rempre{white-space:pre-wrap;word-break:break-word;font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--color-text);background:var(--color-bg-alt,#f8fafc);border:1px solid var(--color-border-light);border-radius:8px;padding:11px 13px;margin:0}
.remsubj{margin:0 0 7px;font:12px/1.5 var(--font-sans);color:var(--color-text-3);word-break:break-word}
.remsubj b{color:var(--color-text);font-weight:600}
.remaddr{display:flex;align-items:flex-end;gap:8px;flex-wrap:wrap;margin:9px 0 0;padding-top:9px;border-top:1px solid var(--color-border-light)}
.remaddr label{display:flex;flex-direction:column;gap:3px;flex:1 1 230px;min-width:0;font:10.5px var(--font-sans);text-transform:uppercase;letter-spacing:.04em;color:var(--color-text-3)}
.remaddr input{width:100%;font:12px var(--font-sans);padding:6px 8px;border:1px solid var(--color-border);border-radius:7px;background:#fff;color:var(--color-text)}
.remaddr input:focus{outline:none;border-color:#0f172a}
.remaddr .btn{flex:0 0 auto}
@media print{.rembar{display:none!important}}"""

BAR = """<div class="rembar" id="remBar">
 <button class="rembtn" id="btnRemind" type="button" title="Compose today's trigger reminder for EOC-KP, with the MNE officer in cc"><span class="rdot"></span><b>Daily reminder</b><span class="rs">to EOC-KP · MNE officer cc</span></button>
 <span class="remst" id="remState">–</span>
</div>
"""

POP = """<!-- ============ Daily trigger reminder: EOC-KP to, MNE officer cc ============ -->
<div class="snpop" id="remPop" role="dialog" aria-modal="true" aria-labelledby="remTitle">
 <div class="snpopbox pndbox">
  <div class="snpophd">
   <div style="min-width:0"><h3 id="remTitle">Daily trigger reminder — EOC-KP</h3><div class="snpopsub" id="remSub"></div></div>
   <button class="snpopx" id="remX" type="button" title="Close" aria-label="Close">&times;</button>
  </div>
  <div class="remwho" id="remWho"></div>
  <div class="remsubj" id="remSubj"></div>
  <div class="scroll" style="max-height:40vh"><pre class="rempre" id="remBody"></pre></div>
  <div class="remaddr">
   <label>To<input id="remTo" type="email" autocomplete="off" spellcheck="false" placeholder="EOC-KP address"></label>
   <label>Cc<input id="remCc" type="email" autocomplete="off" spellcheck="false" placeholder="MNE officer address"></label>
   <button class="btn" id="remSave" type="button">Save recipients</button>
  </div>
  <div class="snpopft">
   <button class="btn" id="remCopy" type="button">Copy email</button>
   <button class="btn" id="remEml" type="button">Download .eml draft</button>
   <button class="btn" id="remCsv" type="button">Download CSV</button>
   <button class="btn" id="remX2" type="button">Close</button>
  </div>
 </div>
</div>"""

JS = """// ---------- daily trigger reminder: one mail to EOC-KP, MNE officer in cc ----------
// Action-only: districts that still owe MPQA trigger feedback. ICM is added when its Nov-26
// round starts; admin coverage stays out until EOC confirms it expects feedback. The addresses live
// in this browser only (localStorage); nothing personal is written into the page or the repo.
// The delta compares the pending count per district between the last two portal reads, so a
// newly flagged UC can raise it even when feedback is being entered - both directions are shown.
const REMAK='kpRemAddr.v1', REMSK='kpRemSnap.v1';
const REMTRIG=[['mpqa','MPQA trigger']];
function remAddr(){
 try{const o=JSON.parse(localStorage.getItem(REMAK)||'{}');return {to:String(o.to||'').trim(),cc:String(o.cc||'').trim()};}
 catch(e){return {to:'',cc:''};}
}
function remPend(){
 const out={t:[],pend:0,asof:TRIG.asof};
 REMTRIG.forEach(p=>{
  const T=(TRIG.t||[]).filter(x=>x.id===p[0])[0];if(!T)return;
  const rows=[];
  Object.keys(T.d).forEach(d=>{const v=T.d[d],n=v[2]-v[3];if(n>0)rows.push({d:d,p:n,t:v[2],f:v[3]});});
  rows.sort((a,b)=>b.p-a.p||(a.d<b.d?-1:1));
  out.t.push({id:p[0],l:p[1],camp:T.camp,tot:T.tot[2],fb:T.tot[3],pend:T.tot[2]-T.tot[3],n:rows.length,rows:rows});
  out.pend+=T.tot[2]-T.tot[3];
 });
 return out;
}
function remSnap(D){
 D=D||remPend();
 let S={};
 try{S=JSON.parse(localStorage.getItem(REMSK)||'{}')||{};}catch(e){S={};}
 const day={};
 D.t.forEach(x=>{const m={};x.rows.forEach(r=>{m[r.d]=r.p;});day[x.id]=m;});
 if(D.asof){S[D.asof]=day;
  const ks=Object.keys(S).sort();
  if(ks.length>10)ks.slice(0,ks.length-10).forEach(k=>{delete S[k];});
  try{localStorage.setItem(REMSK,JSON.stringify(S));}catch(e){}
 }
 return D;
}
function remDelta(D){
 let S={};
 try{S=JSON.parse(localStorage.getItem(REMSK)||'{}')||{};}catch(e){return null;}
 const prev=Object.keys(S).filter(k=>k<D.asof).sort().pop();
 if(!prev)return null;
 const o={date:prev,cleared:0,newly:0};
 D.t.forEach(x=>{
  const a=S[prev][x.id]||{},b={};
  x.rows.forEach(r=>{b[r.d]=r.p;});
  Object.keys(a).forEach(d=>{if(a[d]>(b[d]||0))o.cleared+=a[d]-(b[d]||0);});
  Object.keys(b).forEach(d=>{if(b[d]>(a[d]||0))o.newly+=b[d]-(a[d]||0);});
 });
 return o;
}
function remSubject(D){
 const ad=pendDay(D.asof);
 if(!D.pend)return 'KP trigger reminder - no feedback pending - read '+ad;
 return 'KP trigger reminder - '+D.t.map(x=>fmt(x.pend)+' '+x.id.toUpperCase()).join(' + ')+
  ' UCs pending feedback - read '+ad;
}
function remText(D,d){
 const ad=pendDay(D.asof),L=[];
 L.push('Dear EOC-KP,');
 L.push('');
 L.push('Trigger feedback is still pending for the union councils below, as read from the EOC control-room triggers on '+ad+'. Please have the concerned districts enter the feedback in the portal so the pendency closes. For onward sharing with the concerned districts.');
 L.push('');
 D.t.forEach(x=>{
  L.push(x.l+' - '+x.camp+' ('+fmt(x.pend)+' UCs pending in '+fmt(x.n)+' '+plural(x.n,'district')+')');
  x.rows.forEach(r=>L.push('- '+r.d+' - '+fmt(r.p)+' pending of '+fmt(r.t)+' flagged'));
  L.push('');
 });
 if(d)L.push('Change since the '+pendDay(d.date)+' portal read: '+fmt(d.cleared)+' UCs cleared, '+fmt(d.newly)+' newly pending (net '+((d.newly-d.cleared)>0?'+':'')+fmt(d.newly-d.cleared)+'). Feedback entered lowers the count; a newly flagged UC raises it.');
 L.push('KP totals: '+D.t.map(x=>x.l+' '+fmt(x.tot)+' flagged, '+fmt(x.fb)+' feedback, '+fmt(x.pend)+' pending').join('; ')+'.');
 L.push('This reminder covers the MPQA trigger only. ICM and admin-coverage reminders are held until the campaign round starts on 2 Nov 2026 and the portal begins recording feedback for them.');
 L.push('');
 L.push('Counts are union councils, not children. Portal read '+ad+', '+((TRIG.t||[]).filter(x=>x.id==='mpqa')[0]||{}).camp+' round.');
 L.push('');
 L.push('Cc: MNE officer, WHO - for information.');
 return L.join('\\n');
}
function plural(n,w){return n===1?w:w+'s';}
function remEmlText(A,subj,body){
 const h=['MIME-Version: 1.0','Content-Type: text/plain; charset=utf-8','Content-Transfer-Encoding: 8bit','X-Unsent: 1'];
 if(A.to)h.push('To: '+A.to);
 if(A.cc)h.push('Cc: '+A.cc);
 h.push('Subject: '+subj);
 return h.join('\\r\\n')+'\\r\\n\\r\\n'+body.replace(/\\r?\\n/g,'\\r\\n')+'\\r\\n';
}
function remSaveFile(name,text,type){
 try{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:type||'text/plain;charset=utf-8'}));a.download=name;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},700);return true;}
 catch(e){toast('Could not save the file here');return false;}
}
function remStamp(D){
 D=D||remPend();
 const s=el('remState'),b=el('btnRemind');if(!s||!b)return;
 if(!D.pend){s.innerHTML='<b>nothing pending</b> - no reminder today';b.classList.add('clear');return;}
 b.classList.remove('clear');
 const d=remDelta(D);
 s.innerHTML=D.t.map(x=>'<b>'+fmt(x.pend)+'</b> '+x.id.toUpperCase()+' pending in '+fmt(x.n)+' '+plural(x.n,'district')).join(' · ')+' · read '+pendDay(D.asof)+
  (d?' · <b>'+fmt(d.cleared)+'</b> cleared since '+pendDay(d.date):'');
}
function remWho(A){
 const w=el('remWho');if(!w)return;
 if(A.to||A.cc){
  w.innerHTML='To <b>'+esc(A.to||'(not set)')+'</b>'+(A.cc?' · Cc <b>'+esc(A.cc)+'</b>':' · Cc <b>not set</b>')+
   ' · saved in this browser only, not in the page or the repo';
 }else{
  w.innerHTML='No recipients on this browser yet. Enter the EOC-KP address and the MNE officer once, then Save - they stay in this browser and never enter the page or the repo.';
 }
}
function remOpen(){
 const p=el('remPop');if(!p)return;
 const D=remSnap(),d=remDelta(D),A=remAddr(),ad=pendDay(D.asof),zero=!D.pend;
 el('remSub').innerHTML=(zero?'<span class="st st-on">Clear</span> · no MPQA feedback pending':
  D.t.map(x=>'<b>'+fmt(x.pend)+'</b> '+esc(x.l.replace(' trigger',''))+' pending in <b>'+fmt(x.n)+'</b> '+plural(x.n,'district')).join(' · '))+
  ' · portal read '+ad+(zero?'':(d?' · since '+pendDay(d.date)+': <b>'+fmt(d.cleared)+'</b> cleared, <b>'+fmt(d.newly)+'</b> newly pending':
  ' · no earlier portal read on this browser, so the delta starts from the next refresh'));
 el('remBody').textContent=zero?('Nothing is pending against the MPQA trigger today, so no reminder is generated - the next mail goes out when a district owes feedback.\\n\\nCounts are union councils. Portal read '+ad+'.'):remText(D,d);
 el('remSubj').textContent=zero?'No reminder generated today':('Subject: '+remSubject(D));
 el('remTo').value=A.to;el('remCc').value=A.cc;
 remWho(A);
 ['remCopy','remEml','remCsv'].forEach(k=>{const b=el(k);if(b)b.disabled=zero;});
 p.classList.add('on');
}
function remClose(){const p=el('remPop');if(p)p.classList.remove('on');}
{
 const b=el('btnRemind');if(b)b.onclick=remOpen;
 const p=el('remPop');
 if(p){
  el('remX').onclick=remClose;el('remX2').onclick=remClose;
  p.onclick=ev=>{if(ev.target===p)remClose();};
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&p.classList.contains('on'))remClose();});
  el('remSave').onclick=()=>{
   const to=el('remTo').value.trim(),cc=el('remCc').value.trim();
   if(!/@/.test(to)||!/@/.test(cc)){toast('Enter both addresses - EOC-KP in To, the MNE officer in Cc');return;}
   try{localStorage.setItem(REMAK,JSON.stringify({to:to,cc:cc}));}catch(e){toast('This browser will not store the addresses');return;}
   remWho({to:to,cc:cc});toast('Recipients saved in this browser');
  };
  el('remCopy').onclick=()=>{
   const D=remPend();if(!D.pend){toast('Nothing pending - no reminder today');return;}
   const t='Subject: '+remSubject(D)+'\\n\\n'+remText(D,remDelta(D));
   if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(()=>toast('Subject and body copied'),()=>toast('Could not access the clipboard'));
   else toast('Copy not supported in this browser - use the .eml draft');
  };
  el('remEml').onclick=()=>{
   const D=remPend(),A=remAddr();if(!D.pend){toast('Nothing pending - no reminder today');return;}
   if(!A.to){toast('Enter the EOC-KP address in To, then Save');el('remTo').focus();return;}
   const subj=remSubject(D),body=remText(D,remDelta(D));
   if(remSaveFile('KP_trigger_reminder_'+D.asof+'.eml',remEmlText(A,subj,body),'message/rfc822'))toast('Draft downloaded - open it to send from Outlook');
  };
  el('remCsv').onclick=()=>{
   const D=remPend();if(!D.pend){toast('Nothing pending - no reminder today');return;}
   const H=['Trigger','Campaign','District','Flagged UCs','Feedback','Pending'];
   const rows=[];
   D.t.forEach(x=>{
    x.rows.forEach(r=>rows.push([x.l,x.camp,r.d,r.t,r.f,r.p]));
    rows.push([x.l,x.camp,'KP total',x.tot,x.fb,x.pend]);
   });
   csvDownload('Trigger_reminder_'+D.asof+'.csv',H,rows);
  };
  try{const D=remSnap();remStamp(D);}catch(e){}
 }
}
"""


def _x(text):
    return text.replace('\n', '\r\n')


def patch(v):
    t = v.text
    for anchor, label in ((A_CSS, 'trigwarn twgo'), (A_ROW, 'trigRow'), (A_POP, 'MPQA popup comment'),
                          (A_FUNC, 'renderTRIG')):
        v.require(t.count(anchor) == 1, '%s anchor occurs %d times' % (label, t.count(anchor)))
    t = t.replace(A_CSS, A_CSS + '\r\n' + _x(CSS))
    t = t.replace(A_ROW, A_ROW + '\r\n' + _x(BAR))
    t = t.replace(A_POP, _x(POP) + '\r\n\r\n' + A_POP)
    t = t.replace(A_FUNC, _x(JS) + '\r\n' + A_FUNC)
    v.text = t
    for needle in ('id="remBar"', 'id="btnRemind"', 'id="remPop"', 'id="remBody"', 'id="remSubj"', 'id="remTo"',
                   'function remPend(){', 'function remText(', 'function remEmlText(',
                   'function remSubject(', 'function remStamp('):
        v.require(t.count(needle) == 1, '%s occurs %d times' % (needle, t.count(needle)))
    dashpatch.assert_crlf(v)
    v.changes.append('Daily trigger reminder generator: EOC-KP to, MNE officer cc (%+d chars)'
                     % v.delta())


def main():
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    if 'id="remPop"' in v.text or 'kpRemAddr.v1' in v.text:
        raise SystemExit('%s already has the daily reminder - not patching twice' % v.rel)
    patch(v)
    dashpatch.write_variants([v])
    print('PATCHED %-42s %+8d chars' % (v.rel, v.delta()))
    print('OK daily reminder master only - preview / public / internal pick the block up '
          'through push_master.py when the owner approves publishing')


if __name__ == '__main__':
    main()
