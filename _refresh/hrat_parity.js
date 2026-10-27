/* hrat_parity.js - proves _refresh/hrat_eval.js against the divisions' own HRA workbooks.

The fixture (python _refresh/dump_hrat_parity.py) carries, for every compiled row of two workbooks,
what staff typed in the 33 input columns, what the sheet's cell held for each of the 39 computed
columns, and the formula text the file itself reads. Two passes run the evaluator over the same inputs:

  own text  - each file's own 39 formulas. Every cell the file still carries as a formula must come
              back exactly: that is Excel's arithmetic reproduced, not a model of it. A disagreement
              here is a bug in the evaluator and fails the run.
  published - the text const HRAT ships. Its differences are the audit of fidelity: each miss is
              classified as sitting on a column the published spec restates, on a column that reads
              one, or on neither - and an unexplained miss fails the run. Both texts are printed.

A cell whose cached value survived a paste (its formula is gone) is a published number, not a claim
about the inputs, so it is counted apart. Where the pasted mark tells the two candidate rules apart
- the March sheet compares AI against a bare 10 while the column's own printed rule says >10% - both
rules are scored against the divisions' numbers and the counts are printed. The rank is checked twice:
against the sheet's ranks using the percentages the evaluator computes, and using the percentages the
sheet cached, which separates the arithmetic of RANK.EQ from a chain that has a paste inside it.

  ELECTRON_RUN_AS_NODE=1 Qoder.exe _refresh/hrat_parity.js
*/
'use strict';
const fs = require('fs');
const path = require('path');
const {hratMake, hratRank} = require('./hrat_eval.js');

const FIX = process.argv[2] || path.join(__dirname, 'out', 'hrat_parity.json');
const fix = JSON.parse(fs.readFileSync(FIX, 'utf8'));
const spec = fix.spec;
const tail = spec.tail;
const TOL = 1e-9;

function norm(v) {
  if (v === null || v === undefined || v === '') return {k: 'blank', s: '', n: null};
  if (typeof v === 'object' && typeof v.e === 'string') return {k: 'err', s: v.e, n: null};
  if (typeof v === 'number') {
    if (!isFinite(v)) return {k: 'err', s: '#NUM!', n: null};
    return {k: 'num', s: String(v), n: v};
  }
  return {k: 'txt', s: String(v).toLowerCase().trim(), n: null};
}
function same(a, b) {
  const x = norm(a), y = norm(b);
  if (x.k === 'num' && y.k === 'num') return Math.abs(x.n - y.n) <= TOL;
  if ((x.k === 'blank' || x.k === 'txt') && (y.k === 'blank' || y.k === 'txt')) return x.s === y.s;
  return x.k === y.k && x.s === y.s;
}
function show(v) {
  const n = norm(v);
  return n.k === 'err' ? n.s : (n.k === 'blank' ? '(blank)' : JSON.stringify(v));
}
function pad(s, w) { s = String(s); return s.length >= w ? s : s + ' '.repeat(w - s.length); }

const group = {};
spec.i.forEach(x => { group[x.sc] = 'score: ' + x.name.slice(0, 24); });
spec.B.forEach(b => { if (b.sub) { group[b.sub] = 'block subtotal'; group[b.pct] = 'block %'; } });
group[tail.max] = 'total maximum'; group[tail.ovr] = '% achieved';
group[tail.rank] = 'rank'; group[tail.risk] = 'risk label';

const pubText = {};
spec.c.forEach(c => { if (c.x) pubText[c.L] = c.x; });

/* Which computed columns each computed column reads, so a live cell whose inputs were themselves
 * pasted is not held to the same standard as one whose whole chain the sheet still computes. */
const wantSet = new Set(fix.want);
function depMap(s) {
  const by = {};
  s.c.forEach(c => { by[c.L] = c.x; });
  const m = {};
  fix.want.forEach(L => {
    const body = String(by[L] || '').replace(/"[^"]*"/g, '""');
    const out = [];
    const re = /\$?([A-Z]{1,3})\$?(?:\{r\}|\d+)/g;
    let x;
    while ((x = re.exec(body))) {
      const c = x[1];
      if (c !== L && wantSet.has(c) && out.indexOf(c) < 0) out.push(c);
    }
    m[L] = out;
  });
  return m;
}
function closure(m) {
  const done = {};
  function go(L) {
    if (done[L]) return done[L];
    const out = [];
    done[L] = [];                                  // filled before recursing: this chain has no cycles
    m[L].forEach(d => {
      if (out.indexOf(d) < 0) out.push(d);
      go(d).forEach(x => { if (out.indexOf(x) < 0) out.push(x); });
    });
    done[L] = out;
    return out;
  }
  const r = {};
  fix.want.forEach(L => { r[L] = go(L); });
  return r;
}

// a spec whose formula columns read the way this file does
function ownSpec(file) {
  const s = JSON.parse(JSON.stringify(spec));
  const by = {};
  s.c.forEach(c => { by[c.L] = c; });
  Object.keys(file.fx).forEach(L => { if (by[L]) by[L].x = file.fx[L]; });
  return s;
}

function pass(file, s, label) {
  const rows = file.rows.map(r => r.in);
  const mk = hratMake(s, rows);
  const dep = closure(depMap(s));
  const out = {label, mk, cells: 0, ok: 0, strictBad: 0, chainBad: 0, pastedBad: 0,
               pastedOk: 0, bad: []};
  file.rows.forEach((r, i) => {
    const v = mk.compute(i).v;
    fix.want.forEach(L => {
      const got = v[L], exp = r.exp[L];
      const isLive = r.fl.indexOf(L) >= 0;
      // a cell the sheet still computes is only a proof when the whole chain behind it is live too;
      // behind a pasted mark the sheet's own cached number is not the formula's answer
      const whole = isLive && dep[L].every(d => r.fl.indexOf(d) >= 0);
      out.cells++;
      if (same(got, exp)) {
        out.ok++;
        if (!isLive) out.pastedOk++;
        return;
      }
      if (whole) out.strictBad++; else if (isLive) out.chainBad++; else out.pastedBad++;
      out.bad.push({r: r.r, code: r.code, L, group: group[L], live: isLive, whole, exp, got,
                    text: (isLive ? (file.fx[L] || pubText[L]) : pubText[L]),
                    in: Object.keys(r.in).filter(k => r.in[k] !== null && r.in[k] !== undefined &&
                                                      r.in[k] !== '')
                      .map(k => k + '=' + JSON.stringify(r.in[k])).join(' ')});
    });
  });
  return out;
}

function tag(b) {
  return b.live ? (b.whole ? ' [sheet computes]' : ' [behind a paste]') : ' [pasted]';
}
function report(o) {
  const by = {};
  o.bad.forEach(b => {
    const k = b.L + ' ' + pad(b.group, 24) + tag(b);
    (by[k] = by[k] || {n: 0, e: b}).n++;
  });
  console.log('  ' + o.label);
  console.log('    reproduced ' + o.ok + ' of ' + o.cells + ' cells ('
              + (100 * o.ok / o.cells).toFixed(2) + '%)  |  strict misses ' + o.strictBad
              + '  |  misses behind a pasted dependency ' + o.chainBad
              + '  |  pasted cells wrong ' + o.pastedBad + '  |  pasted cells matched ' + o.pastedOk);
  Object.keys(by).sort((a, b) => by[b].n - by[a].n).slice(0, 12).forEach(k => {
    const b = by[k].e;
    console.log('      ' + pad(k, 46) + ' x' + pad(by[k].n, 6)
                + ' e.g. row ' + b.r + ' UC ' + b.code + ': exp=' + show(b.exp)
                + ' got=' + show(b.got));
  });
  o.bad.filter(b => b.whole).slice(0, 5).forEach(b => {
    console.log('        detail r' + b.r + ' ' + b.L + ' exp=' + show(b.exp) + ' got=' + show(b.got)
                + ' | formula ' + (b.text || '(none)'));
    console.log('               inputs ' + b.in.slice(0, 400));
  });
}

/* The sheet's own rank is anchored to a fixed block of rows; over that block hratRank - what the grid
 * uses - must return the numbers the sheet shows. The block comes from the file's own RANK text.
 *
 * Two readings, because the rank sits at the end of a long chain:
 *   computed - rank the percentages the evaluator produces and compare with the sheet's ranks. This
 *              only holds where the whole chain is live, so it is the province's 36 formula rows.
 *   cached   - rank the percentages the sheet itself cached and compare with the sheet's own ranks.
 *              That isolates the arithmetic of RANK.EQ (descending, ties sharing a rank) from the rows
 *              whose marks were pasted, and is what says whether a mismatch is the evaluator or the
 *              file's own stale intermediates.
 */
function rankWindow(file, mk) {
  const f = file.fx[tail.rank] || pubText[tail.rank] || '';
  const m = new RegExp('\\$?' + tail.ovr + '\\$(\\d+):\\$?' + tail.ovr + '\\$(\\d+)').exec(f);
  if (!m) return null;
  const lo = +m[1], hi = +m[2];
  const idx = [];
  file.rows.forEach((r, i) => {
    if (r.r >= lo && r.r <= hi && r.fl.indexOf(tail.rank) >= 0) idx.push(i);
  });
  if (!idx.length) return {lo, hi, n: 0, ok: 0, bad: []};
  const vals = idx.map(i => mk.compute(i).v[tail.ovr]);
  const rk = hratRank(vals, false);
  const bad = [];
  let ok = 0;
  idx.forEach((i, j) => {
    const exp = file.rows[i].exp[tail.rank];
    if (same(rk[j], exp)) ok++; else bad.push([file.rows[i].r, exp, rk[j]]);
  });
  const all = file.rows.filter(r => r.r >= lo && r.r <= hi);
  const cv = all.map(r => r.exp[tail.ovr]);
  const cr = hratRank(cv, false);
  const cached = {n: 0, ok: 0, bad: []};
  all.forEach((r, j) => {
    const exp = r.exp[tail.rank];
    if (typeof exp !== 'number') return;              // an error or blank rank proves nothing
    cached.n++;
    if (same(cr[j], exp)) cached.ok++; else cached.bad.push([r.r, exp, cr[j]]);
  });
  return {lo, hi, n: idx.length, ok, bad, cached};
}

/* The published pass may differ only where the published spec deliberately restates the sheet's own
 * text, or sits behind such a column. Anything else is a fidelity bug, so the run counts the misses
 * apart instead of trusting the wording of its own verdict. Spacing is not a rule: the builder's
 * cleaned text and the workbook's can differ by the space after a comma, so a column counts as
 * restated only when the two texts still differ with every space removed. */
const depPub = closure(depMap(spec));
const flat = s => String(s).replace(/\s+/g, '');
const restatedOf = file => fix.want.filter(L =>
  file.fx[L] !== undefined && flat(file.fx[L]) !== flat(pubText[L]));
const spacedOnly = file => fix.want.filter(L =>
  file.fx[L] !== undefined && file.fx[L] !== pubText[L] && flat(file.fx[L]) === flat(pubText[L]));
function explainMiss(b, restated) {
  if (restated.indexOf(b.L) >= 0) return 'restated';
  if (depPub[b.L].some(d => restated.indexOf(d) >= 0)) return 'behind a restatement';
  return 'UNEXPLAINED';
}

// the divisions' own pasted marks, scored against the two candidate thresholds
function threshold(s) {
  const m = /(\d+(?:\.\d+)?)(%?)\s*$/.exec(s);
  if (!m) return null;
  return parseFloat(m[1]) / (m[2] ? 100 : 1);
}
function ruleEvidence(file, dep, sc) {
  const w = spec.warn.filter(x => x.col === sc && x.raw === dep).pop();
  if (!w) return null;
  const hi = threshold(w.to), lo = threshold(w.from);
  const out = {both: 0, onlyHi: 0, onlyLo: 0, neither: 0, n: 0};
  file.rows.forEach(r => {
    if (r.fl.indexOf(sc) >= 0) return;                      // this row still computes it
    const x = r.in[dep], y = r.exp[sc];
    if (typeof x !== 'number' || typeof y !== 'number') return;
    out.n++;
    const a = y === (x >= hi ? 3 : 0), b = y === (x >= lo ? 3 : 0);
    if (a && b) out.both++; else if (a) out.onlyHi++; else if (b) out.onlyLo++; else out.neither++;
  });
  out.hi = hi;
  out.lo = lo;
  return out;
}

let hard = 0, soft = 0;
fix.files.forEach(file => {
  console.log('\n=== ' + file.name + ' [' + file.sheet + ']  ' + file.rows.length + ' rows, '
              + file.live + ' still carrying formulas, ' + Object.keys(file.fx).length
              + ' of 39 columns ever live');
  const own = ownSpec(file);
  const o1 = pass(file, own, 'own text - the formulas as this file reads them');
  report(o1);
  hard += o1.strictBad;
  const o2 = pass(file, spec, 'published - const HRAT as it ships');
  report(o2);
  soft += o2.strictBad;
  const un = {};
  o2.bad.filter(b => b.whole && flat(file.fx[b.L]) === flat(pubText[b.L]))
    .forEach(b => { un[b.L + ' ' + b.group] = (un[b.L + ' ' + b.group] || 0) + 1; });
  console.log('    published pass: misses on cells the sheet computes with the same text %j', un);
  const restated = restatedOf(file);
  const kinds = {restated: 0, 'behind a restatement': 0, UNEXPLAINED: 0};
  const unexplained = [];
  o2.bad.filter(b => b.whole).forEach(b => {
    const k = explainMiss(b, restated);
    kinds[k]++;
    if (k === 'UNEXPLAINED' && unexplained.indexOf(b.L) < 0) unexplained.push(b.L);
  });
  hard += kinds.UNEXPLAINED;
  console.log('    ' + o2.strictBad + ' published misses against ' + restated.length
              + ' restated column(s): ' + kinds.restated + ' on a restated column, '
              + kinds['behind a restatement'] + ' downstream of one, ' + kinds.UNEXPLAINED
              + ' unexplained' + (unexplained.length ? ' - ' + unexplained.join(', ') : ''));
  Object.keys(file.fx).filter(L => restated.indexOf(L) >= 0).forEach(L => {
    console.log('    ' + L + ' ' + group[L] + ' is restated:');
    console.log('        file      ' + file.fx[L]);
    console.log('        published ' + pubText[L]);
  });
  const so = spacedOnly(file);
  if (so.length) console.log('    ' + so.join(', ') + ' read' + (so.length > 1 ? '' : 's')
              + ' the same rule, only the spacing differs');
  const contig = file.rows.every((r, i) => r.r === spec.r0 + i);
  console.log('    sheet rows contiguous from row ' + spec.r0 + ': ' + contig);
  if (contig) {
    const rw = rankWindow(file, o1.mk);
    if (rw && rw.n) {
      console.log('    hratRank over the anchored block rows ' + rw.lo + '-' + rw.hi + ' on the '
                  + 'percentages the evaluator computes: ' + rw.ok + ' of ' + rw.n + ' match');
      rw.bad.slice(0, 5).forEach(x => {
        console.log('        r' + x[0] + ' exp=' + show(x[1]) + ' got=' + show(x[2]));
      });
      console.log('    the same ranks taken from the percentages the sheet itself cached: '
                  + rw.cached.ok + ' of ' + rw.cached.n + ' match');
      rw.cached.bad.slice(0, 5).forEach(x => {
        console.log('        r' + x[0] + ' exp=' + show(x[1]) + ' got=' + show(x[2]));
      });
      hard += rw.cached.n - rw.cached.ok;
    } else console.log('    hratRank: ' + (rw ? 'no live rank inside rows ' + rw.lo + '-' + rw.hi
                                              : 'no rank range readable'));
  }
  const ev = ruleEvidence(file, 'AI', 'AJ');
  if (ev && ev.n) {
    console.log('    ' + ev.n + ' pasted AJ marks against AI: ' + ev.both + ' agree with both '
                + 'thresholds, ' + ev.onlyHi + ' only with the printed rule (AI>=' + ev.hi
                + '), ' + ev.onlyLo + ' only with this sheet\'s formula (AI>=' + ev.lo + '), '
                + ev.neither + ' with neither');
  }
});

console.log('\n' + (hard === 0
  ? 'PASS  the evaluator reproduces every cell each workbook still computes itself, every rank '
      + 'hratRank returns over the sheet\'s own cached percentages is the number the sheet shows, '
      + 'and the published text\'s ' + soft + ' misses all sit on or behind a restated column'
  : 'FAIL  ' + hard + ' cells - the evaluator does not reproduce the workbook\'s own arithmetic, '
      + 'or the published spec changes a value no restated rule explains'));
process.exit(hard ? 1 : 0);
