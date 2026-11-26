"""Build a Node harness that renders the WPV profile for every UC in the EPI register.

Catches free-identifier and shape errors that only appear when a council is actually
selected (the browser test found `n2u` this way). Scratch: writes only under _refresh/out.

Usage: python _refresh/wpvprof_harness.py [--only CODE]
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import srcutil
import dashpatch

NAMES = ['EPI', 'CHD', 'LQR', 'LQM', 'PCM', 'ZD', 'WPV', 'WPVH', 'EPIUC', 'AFPUC', 'EMETA', 'EPIYTD', 'KPGEO']
AGG_JS = """
const EAG=(EMETA.ag||[]).map(a=>({k:a[0],l:a[1],t:a[2],core:a[3]})), EAGK=Object.fromEntries(EAG.map(a=>[a.k,a]));
const eTg=(o,a)=>a.t==='n'?o.n:o.s;
const eP=(o,k)=>{const a=EAGK[k]; if(!a||o[k]==null)return null; const tg=eTg(o,a); return tg?o[k]/tg*100:null;};
function aggE(rows){const o={u:rows.length,n:0,s:0,zr:0,zu:0};EAG.forEach(a=>o[a.k]=null);
 rows.forEach(r=>{o.n+=r.n||0;o.s+=r.s||0;EAG.forEach(a=>{if(r[a.k]!=null)o[a.k]=(o[a.k]||0)+r[a.k];});if(r.zr!=null){o.zr+=r.zr;o.zu++;}});
 EAG.forEach(a=>o['p_'+a.k]=eP(o,a.k));
 o.d13=(o.p1&&o.p3!=null)?(o.p1-o.p3)/o.p1*100:null; o.dmr=(o.mr1&&o.mr2!=null)?(o.mr1-o.mr2)/o.mr1*100:null; return o;}
"""
STUB = """
const EL={};
const node=()=>({value:'',innerHTML:'',textContent:'',disabled:false,options:[],querySelector:()=>null,style:{}});
const el=id=>{if(!EL[id]){EL[id]=node();}return EL[id];};
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>String(Math.round(n*100)/100);
const SVGI=()=>'';
const ICO={download:'d',swap:'s',flag:'f',alert:'a',chart:'c',users:'u',list:'l',clock:'k',target:'t',table:'b'};
const csvDownload=()=>{};
const document={getElementById:el};
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only')
    a = ap.parse_args()
    s = srcutil.read_text(os.path.join(ROOT, 'index.html'))
    parts = [STUB]
    for n in NAMES:
        parts.append('const %s = %s;\n' % (n, dashpatch.get_payload(s, n)))
    parts.append(AGG_JS)
    js = srcutil.read_text(os.path.join(HERE, 'wpvprof.js'))
    js = js.replace('/* WPVPROF:JS:START */\r\n', '').replace('\r\n/* WPVPROF:JS:END */', '')
    js = js.replace('\r\nWPVC.init();', '').replace('WPVC.init();\r\n', '')
    js = js.replace('esc(e&&e.message?e.message:e)', 'String(e&&e.stack?e.stack:e)')
    parts.append(js)
    only = json.dumps(a.only) if a.only else 'null'
    parts.append("""
const only=__ONLY__;
const out={n:0,ok:0,fail:[],thin:[],warn:[]};
const seen={};
EPI.forEach(function(e){
  const c=String(e.c||''); if(!c||seen[c])return; seen[c]=1;
  if(only&&c!==only)return;
  out.n++;
  el('wpvDiv').value=e.dv||''; el('wpvDist').value=e.d||''; el('wpvTeh').value=e.t||''; el('wpvUc').value=c;
  let err=null;
  try{ WPVC.draw(); }catch(x){ err=(x&&x.stack)?x.stack.split('\\n').slice(0,2).join(' | '):String(x); }
  const h=el('wpvBody').innerHTML||'';
  if(err){ out.fail.push(c+' '+e.d+'/'+e.u+': '+err); return; }
  if(h.length<400){ out.thin.push(c+' '+e.d+'/'+e.u+' ('+h.length+' chars)'); return; }
  if(/could not be rendered|is not defined|undefined%|NaN/.test(h)){ out.warn.push(c+' '+e.d+'/'+e.u+': '+(h.match(/.{0,60}(could not be rendered|is not defined|undefined%|NaN).{0,40}/)||[''])[0]); return; }
  out.ok++;
});
out.failN=out.fail.length; out.thinN=out.thin.length; out.warnN=out.warn.length;
out.fail=out.fail.slice(0,12); out.thin=out.thin.slice(0,12); out.warn=out.warn.slice(0,12);
console.log(JSON.stringify(out,null,1));
if(only){ console.log('---BODY---'); console.log((el('wpvBody').innerHTML||'').replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').slice(0,1400)); }
if(only){ try{ require('fs').writeFileSync(__dirname+'/_wpv_body.txt', (el('wpvBody').innerHTML||'').replace(/<(script|style)[^>]*>[\\s\\S]*?<\\/\\1>/g,' ').replace(/<\\/(tr|div|h4|h5|li|p|table)>/g,'\\n').replace(/<[^>]+>/g,' ').replace(/[ \\t]+/g,' ')); }catch(e){} }
""".replace('__ONLY__', only))
    dest = os.path.join(srcutil.OUT, '_wpv_harness.js')
    srcutil.write_text(dest, ''.join(parts))
    print('OK harness %s %d chars' % (dest, len(''.join(parts))))


if __name__ == '__main__':
    main()
