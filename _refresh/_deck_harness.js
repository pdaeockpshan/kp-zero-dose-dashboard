// Offline harness for the Last-3-campaigns deck block. Renders against the real payloads.
const fs = require('fs'), path = require('path'), vm = require('vm');
const D = path.join(__dirname);

const slides = [], problems = [];
function cnt(label, v) { return { label: String(label), v }; }

class Shape {
  constructor(o) { Object.assign(this, o); }
}
class Table { constructor(rows, o) { this.rows = rows; this.o = o; }
  get nrows() { return this.rows.length; } get ncols() { return this.rows[0].length; } }
class Chart { constructor(type, data, o) { this.type = type; this.data = data; this.o = o; } }
class Slide {
  constructor(n) { this.n = n; this.items = []; this.bg = null; this.charts = []; this.tables = []; this.texts = []; }
  set background(v) { this.bg = v.color; }
  addShape(t, o) { this.items.push(['shape', o]); }
  addText(t, o) { this.items.push(['text', o]);
    const flat = Array.isArray(t) ? t.map(x => x.text).join(' ') : String(t);
    this.texts.push({ t: flat, o }); }
  addTable(rows, o) { this.items.push(['table', o]); const tb = new Table(rows, o); this.tables.push(tb); }
  addChart(type, data, o) { this.items.push(['chart', o]); this.charts.push(new Chart(type, data, o)); }
}
class FakePPTX {
  constructor() { this.ShapeType = { rect: 'rect', line: 'line' }; this.ChartType = { bar: 'bar' }; }
  addSlide() { const s = new Slide(slides.length + 1); slides.push(s); return s; }
  write() { return Promise.resolve(new ArrayBuffer(8)); }
}

const ctx = {
  console,
  fmt: n => Number(n).toLocaleString('en-US'),
  el: () => ({ disabled: false, onclick: null }),
  c3Pick: () => { },
  loadPptx: async () => { },
  saveDeck: async (pptx, fn) => { ctx.__saved = fn; },
  toast: m => { ctx.__toast = m; },
  window: {},
  PptxGenJS: FakePPTX,
  setTimeout, Date, Math, Object, Array, JSON, String, Number, Promise, Set, Error
};
ctx.window = ctx;
vm.createContext(ctx);

// payloads + EPI helpers from the real dashboard source
vm.runInContext(fs.readFileSync(path.join(D, '_deck_test_data.js'), 'utf8'), ctx, { filename: 'data' });
vm.runInContext(`
const EAG=(EMETA.ag||[]).map(a=>({k:a[0],l:a[1],t:a[2],core:a[3]})), EAGK=Object.fromEntries(EAG.map(a=>[a.k,a]));
const eTg=(o,a)=>a.t==='n'?o.n:o.s;
const eP=(o,k)=>{const a=EAGK[k]; if(!a||o[k]==null)return null; const tg=eTg(o,a); return tg?o[k]/tg*100:null;};
function aggE(rows){const o={u:rows.length,n:0,s:0,zr:0,zu:0};EAG.forEach(a=>o[a.k]=null);
 rows.forEach(r=>{o.n+=r.n||0;o.s+=r.s||0;EAG.forEach(a=>{if(r[a.k]!=null)o[a.k]=(o[a.k]||0)+r[a.k];});if(r.zr!=null){o.zr+=r.zr;o.zu++;}});
 EAG.forEach(a=>o['p_'+a.k]=eP(o,a.k));
 o.d13=(o.p1&&o.p3!=null)?(o.p1-o.p3)/o.p1*100:null; o.dmr=(o.mr1&&o.mr2!=null)?(o.mr1-o.mr2)/o.mr1*100:null; return o;}
`, ctx, { filename: 'epi' });

// synthetic three-round selection: Nov from the real NOVUC rows, Sept/May scaled beside it
vm.runInContext(`
function c3View(){
 const K=NOVUC.k||[],rows=NOVUC.r||[],ti=K.indexOf('tg'),vi=K.indexOf('vac');
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
`, ctx, { filename: 'view' });

vm.runInContext(fs.readFileSync(path.join(D, '_deck_test_block.js'), 'utf8'), ctx, { filename: 'block' });

let deck;
try { deck = vm.runInContext('renderC3Deck(PptxGenJS)', ctx); }
catch (e) { console.log('RENDER_FAIL', e && e.stack); process.exit(1); }

console.log('slides', slides.length);
slides.forEach(s => {
  const t = s.texts.find(x => x.o && x.o.fontSize === 24);
  const tag = s.n === 1 ? '[cover]' : (t ? t.t : '(no title)');
  console.log(String(s.n).padStart(2), tag, '| texts', s.texts.length, 'tables', s.tables.length, 'charts', s.charts.length);
});

// geometry: every table must end above the footer rule at y=6.98
slides.forEach(s => s.tables.forEach((tb, i) => {
  const o = tb.o, rh = (o.rowH || [0.3]);
  const h = Array.isArray(rh) ? rh.reduce((a, b) => a + b, 0) : o.rowH * tb.nrows;
  const bottom = (o.y || 0) + h;
  if (bottom > 6.95) problems.push('S' + s.n + ' table' + i + ' bottom ' + bottom.toFixed(2));
  if (tb.ncols !== (tb.rows[0] || []).length) problems.push('S' + s.n + ' ragged table');
  tb.rows.forEach((r, ri) => { if (r.length !== tb.ncols) problems.push('S' + s.n + ' table' + i + ' row' + ri + ' cols ' + r.length + '/' + tb.ncols); });
}));
// geometry: any text box placed past the right edge or below the footer
slides.forEach(s => s.texts.forEach(t => {
  const o = t.o || {};
  if ((o.x || 0) + (o.w || 0) > 13.45) problems.push('S' + s.n + ' text overflows right: ' + t.t.slice(0, 30));
  if ((o.y || 0) + (o.h || 0) > 7.42) problems.push('S' + s.n + ' text below footer: ' + t.t.slice(0, 30));
  if (o.fontSize && o.h && !o.valign && o.h * 72 < o.fontSize * 1.05) problems.push('S' + s.n + ' textbox too short for ' + o.fontSize + 'pt: ' + t.t.slice(0, 30));
}));
// extract the KPI values the deck prints
const grab = (n, label) => {
  const s = slides[n - 1]; if (!s) return null;
  const i = s.texts.findIndex(t => t.t === label);
  return i >= 0 ? s.texts[i + 1].t : null;
};
const KPI = {
  'S1 HH coverage': grab(1, 'HH COVERAGE'), 'S1 overall': grab(1, 'OVERALL COVERAGE'),
  'S1 recorded missed': grab(1, 'RECORDED MISSED'), 'S1 ICM recall': grab(1, 'ICM RECALL'),
  'S3 latest': grab(3, 'LATEST COVERAGE'), 'S3 novHH': grab(3, 'NOV HH COVERAGE'), 'S3 novOvr': grab(3, 'NOV OVERALL'),
  'S5 recorded': grab(5, 'RECORDED MISSED'), 'S6 covered': grab(6, 'TOTAL COVERED'), 'S7 still': grab(7, 'TOTAL STILL MISSED'),
  'S8 team checks': grab(8, 'TEAM CHECKS'), 'S9 fixed sites': grab(9, 'FIXED SITES CHECKED'),
  'S11 recall': grab(11, 'RECALL %'), 'S12 lqas': grab(12, 'PASS %'), 'S13 ms': grab(13, 'MS %'),
  'S14 fm': grab(14, 'FM %'), 'S15 wpv1': grab(15, 'WPV1'), 'S15 afp': grab(15, 'AFP CASES 2026'),
  'S16 fi': grab(16, 'FULLY IMMUNIZED'), 'S16 mr2': grab(16, 'MR-2'), 'S17 zd': grab(17, 'RECORDED ZD'),
  'S18 flagged': grab(18, 'UCS FLAGGED'), 'S18 icm': grab(18, 'ICM'), 'S18 answered': grab(18, 'ICM ANSWERED')
};
Object.entries(KPI).forEach(([k, v]) => console.log('KPI', k.padEnd(20), v));
const dbg = vm.runInContext('(function(){const V=c3View();return {sel:V.sel.map(s=>s.l), n:V.rows.length, x0:V.rows[0]&&V.rows[0].x, d:V.rows[0]&&V.rows[0].d};})()', ctx);
console.log('VIEW', JSON.stringify(dbg).slice(0, 500));
console.log('COVER', slides[0].texts.map(t=>t.t).join(' | '));
console.log('S3 TABLE', JSON.stringify(slides[2].tables[0].rows.map(r=>r.map(c=>c.text))));
console.log('saved', ctx.__saved, '| toast', ctx.__toast);
console.log('problems', problems.length);
problems.slice(0, 40).forEach(p => console.log('  !', p));
