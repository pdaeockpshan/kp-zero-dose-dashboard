// Render the Last-3-campaigns deck with the real PptxGenJS bundle, offline.
const fs = require('fs'), path = require('path'), vm = require('vm');
const D = __dirname;

const sandbox = {
  console,
  fmt: n => Number(n).toLocaleString('en-US'),
  el: () => ({ disabled: false, onclick: null }),
  c3Pick: () => { },
  loadPptx: async () => { },
  saveDeck: async () => { },
  toast: () => { },
  setTimeout, setInterval, clearTimeout, Date, Math, JSON, Object, Array, String, Number, Boolean,
  Promise, Set, Map, Error, TypeError, RegExp, parseInt, parseFloat, isNaN, Buffer,
  document: { createElement: () => ({ style: {} }), head: { appendChild: () => { } }, body: {} },
  navigator: { userAgent: 'node' },
  Blob: function Blob(parts, o) { this.parts = parts; this.type = o && o.type; this.size = 0; }
};
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.global = sandbox;
vm.createContext(sandbox);

vm.runInContext(fs.readFileSync(path.join(D, 'pptxgen.bundle.js'), 'utf8'), sandbox, { filename: 'pptxgen' });
if (typeof sandbox.PptxGenJS !== 'function') { console.log('NO_PPTXGENJS', typeof sandbox.PptxGenJS, Object.keys(sandbox).slice(-5)); process.exit(1); }

vm.runInContext(fs.readFileSync(path.join(D, '_deck_test_data.js'), 'utf8'), sandbox, { filename: 'data' });
vm.runInContext(`
const EAG=(EMETA.ag||[]).map(a=>({k:a[0],l:a[1],t:a[2],core:a[3]})), EAGK=Object.fromEntries(EAG.map(a=>[a.k,a]));
const eTg=(o,a)=>a.t==='n'?o.n:o.s;
const eP=(o,k)=>{const a=EAGK[k]; if(!a||o[k]==null)return null; const tg=eTg(o,a); return tg?o[k]/tg*100:null;};
function aggE(rows){const o={u:rows.length,n:0,s:0,zr:0,zu:0};EAG.forEach(a=>o[a.k]=null);
 rows.forEach(r=>{o.n+=r.n||0;o.s+=r.s||0;EAG.forEach(a=>{if(r[a.k]!=null)o[a.k]=(o[a.k]||0)+r[a.k];});if(r.zr!=null){o.zr+=r.zr;o.zu++;}});
 EAG.forEach(a=>o['p_'+a.k]=eP(o,a.k));
 o.d13=(o.p1&&o.p3!=null)?(o.p1-o.p3)/o.p1*100:null; o.dmr=(o.mr1&&o.mr2!=null)?(o.mr1-o.mr2)/o.mr1*100:null; return o;}
function c3View(){
 const K=NOVUC.k||[],rows=NOVUC.r||[];
 const R={};
 rows.forEach(a=>{const o={};K.forEach((k,j)=>o[k]=a[j]); if(!o.d||!o.u)return;
  R[o.d+'|'+o.u]={d:o.d,dv:o.dv||'',x:[null,null,{tg:o.tg||0,vc:o.vac||0,st:0,rf:0,lo:0,na:0}]};});
 Object.values(R).forEach(r=>{const n=r.x[2].tg;
  r.x[0]={tg:Math.round(n*0.99),vc:Math.round(n*0.95),st:0,rf:0,lo:0,na:0};
  r.x[1]={tg:Math.round(n*1.02),vc:Math.round(n*0.985),st:0,rf:0,lo:0,na:0};});
 const sel=[{id:'M26',l:'SNID May-26',sh:'SNID May-26',y:2026,m:5,t:'SNID',src:'mis'},
  {id:'S26',l:'SNID Sept-26',sh:'SNID Sept-26',y:2026,m:9,t:'SNID',src:'mis'},
  {id:'N26',l:'SNID Nov-26',sh:'SNID Nov-26',y:2026,m:11,t:'SNID',src:'nov'}];
 return {sel,rows:Object.values(R)};
}
`, sandbox, { filename: 'view' });
vm.runInContext(fs.readFileSync(path.join(D, '_deck_test_block.js'), 'utf8'), sandbox, { filename: 'block' });

const t0 = Date.now();
sandbox.__out = null;
vm.runInContext(`
(async()=>{
 const pptx=renderC3Deck(PptxGenJS);
 const ab=await pptx.write({outputType:'nodebuffer'});
 __out={ok:true,bytes:ab.length,buf:ab};
})().then(()=>{__done=1;},e=>{__out={ok:false,err:String(e&&e.stack||e)};__done=1;});
`, sandbox, { filename: 'run' });

const wait = setInterval(() => {
  if (!sandbox.__done) { if (Date.now() - t0 > 120000) { console.log('TIMEOUT after 120s'); process.exit(1); } return; }
  clearInterval(wait);
  const o = sandbox.__out;
  if (!o || !o.ok) { console.log('WRITE_FAIL', o && o.err); process.exit(1); }
  const out = path.join(D, '_deck_render_out.pptx');
  fs.writeFileSync(out, o.buf);
  console.log('WRITE_OK bytes', o.bytes, 'in', ((Date.now() - t0) / 1000).toFixed(1) + 's', '->', out);
}, 200);
