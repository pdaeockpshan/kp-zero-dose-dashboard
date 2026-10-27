/* hrat_eval.js - evaluates the HRA card's own Excel formulas.

The formulas are the ones read out of the divisions' workbook by _refresh/build_hrat.py and kept
verbatim in const HRAT, with the row they were read on replaced by {r}. The dashboard inlines this
file, so the grid on screen computes the 27 scores, the four block subtotals and percentages, the
maximum, the rank and the Risk label from the same text the downloaded sheet carries: the page cannot
report a row differently from the file it hands back, and the file recomputes the same numbers in
Excel.

It implements the part of Excel this card uses - IF (lazy, as Excel is), AND, OR, NOT, SUM, COUNT,
COUNTA, ISBLANK, IFERROR, RANK.EQ, percent literals (5% is 0.05) and Excel's comparison rules, which
are not JavaScript's: a blank answers a number as 0 and an empty text as "", a number never equals a
text, and any text ranks above any number - so the division that typed "0%" into a percent column
instead of formatting a zero scores the way Excel scores it, not the way a naive parser would.
*/
function hratMake(spec, rows) {
  var r0 = spec.r0 || 3;
  var fx = {};
  spec.c.forEach(function (c) { if (c.x) fx[c.L] = c.x; });

  var FNS = /^(RANK\.EQ|IFERROR|COUNTA|COUNT|ISBLANK|SUM|AND|OR|NOT|IF|RANK)/i;
  var REF = /^\$?([A-Za-z]{1,3})\$?(\{r\}|\d+)/;
  var NUM = /^\d+(\.\d+)?%?/;

  /* ---- tokenizer ---- */
  function tokens(src) {
    var out = [], i = 0;
    while (i < src.length) {
      var ch = src.charAt(i);
      if (ch === ' ' || ch === '\n' || ch === '\t') { i++; continue; }
      if (ch === '"') {
        var j = src.indexOf('"', i + 1);
        if (j < 0) throw new Error('hrat: unterminated text in ' + src);
        out.push({t: 'str', v: src.slice(i + 1, j)});
        i = j + 1;
        continue;
      }
      var f = FNS.exec(src.slice(i));
      if (f && src.charAt(i + f[0].length) === '(' &&
          !/[A-Za-z0-9_.$]/.test(src.charAt(i - 1))) {
        out.push({t: 'fn', v: f[0].toUpperCase()});
        i += f[0].length;
        continue;
      }
      var m = REF.exec(src.slice(i));
      if (m && src.charAt(i + m[0].length) !== '(') {
        out.push({t: 'ref', c: m[1].toUpperCase(), r: m[2] === '{r}' ? null : +m[2]});
        i += m[0].length;
        continue;
      }
      var n = NUM.exec(src.slice(i));
      if (n) {
        var pct = /%$/.test(n[0]);
        out.push({t: 'num', v: parseFloat(pct ? n[0].slice(0, -1) : n[0]) / (pct ? 100 : 1)});
        i += n[0].length;
        continue;
      }
      var w = /^\w+/.exec(src.slice(i));
      if (w && /^(TRUE|FALSE)$/.test(w[0])) {
        out.push({t: 'num', v: /^TRUE$/i.test(w[0]) ? 1 : 0});
        i += w[0].length;
        continue;
      }
      var op = /^(<=|>=|<>|[-+*/^&=(),:]|[<>])/.exec(src.slice(i));
      if (op) { out.push({t: 'op', v: op[1]}); i += op[1].length; continue; }
      throw new Error('hrat: cannot read ' + JSON.stringify(src.slice(i, i + 28)));
    }
    out.push({t: 'end'});
    return out;
  }

  /* ---- parser: comparison, then +-, then *, then ^, then an atom (Excel's order) ---- */
  function parse(tk) {
    var p = 0;
    function is(v) { return tk[p].t === 'op' && tk[p].v === v; }
    function eat(v) { if (!is(v)) throw new Error('hrat: expected ' + v + ' at token ' + p); p++; }
    function atom() {
      var x = tk[p];
      if (x.t === 'num') { p++; return {k: 'num', v: x.v}; }
      if (x.t === 'str') { p++; return {k: 'str', v: x.v}; }
      if (x.t === 'ref') {
        p++;
        if (is(':')) {
          p++;
          var y = tk[p];
          if (y.t !== 'ref') throw new Error('hrat: a range must end on a cell');
          p++;
          if (y.r === null || x.r === null) throw new Error('hrat: a relative range end is not read');
          return {k: 'range', c: x.c, r1: x.r, c2: y.c, r2: y.r};
        }
        return {k: 'ref', c: x.c, r: x.r};
      }
      if (x.t === 'fn') {
        p++;
        var a = [];
        eat('(');
        if (!is(')')) {
          for (;;) {
            a.push(expr());
            if (is(',')) { p++; continue; }
            break;
          }
        }
        eat(')');
        return {k: 'call', f: x.v, a: a};
      }
      if (is('(')) { p++; var e = expr(); eat(')'); return e; }
      if (is('-') || is('+')) { p++; return {k: 'neg', e: atom()}; }
      throw new Error('hrat: unexpected token ' + JSON.stringify(x) + ' at ' + p);
    }
    function pow() { var l = atom(); if (is('^')) { p++; return {k: 'bin', o: '^', l: l, r: pow()}; }
      return l; }
    function mul() { var l = pow(); while (is('*') || is('/')) { var v = tk[p].v; p++;
      l = {k: 'bin', o: v, l: l, r: pow()}; } return l; }
    function add() { var l = mul(); while (is('+') || is('-')) { var v = tk[p].v; p++;
      l = {k: 'bin', o: v, l: l, r: mul()}; } return l; }
    function cat() { var l = add(); while (is('&')) { p++; l = {k: 'bin', o: '&', l: l, r: add()}; }
      return l; }
    function expr() { var l = cat();
      while (is('=') || is('<>') || is('<') || is('>') || is('<=') || is('>=')) {
        var v = tk[p].v; p++; l = {k: 'cmp', o: v, l: l, r: cat()}; }
      return l; }
    var root = expr();
    if (tk[p].t !== 'end') throw new Error('hrat: ' + JSON.stringify(tk[p]) + ' left over');
    return root;
  }

  var parsed = {};
  function ast(L) {
    if (!parsed[L]) parsed[L] = parse(tokens(fx[L]));
    return parsed[L];
  }

  /* ---- Excel's value rules ---- */
  function E(code) { return {e: code}; }
  function isErr(v) { return !!v && typeof v === 'object' && typeof v.e === 'string'; }
  function isBlank(v) { return v === null || v === undefined; }
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function isTxt(v) { return typeof v === 'string'; }

  // a blank answers a number as 0 and a text as ""; text and number are different types and never
  // compare equal, which is where the ordering branch below sends them.
  function pair(a, b) {
    if (isBlank(a)) a = isNum(b) ? 0 : '';
    if (isBlank(b)) b = isNum(a) ? 0 : '';
    if (isNum(a) && isNum(b)) return [a, b];
    if (isTxt(a) && isTxt(b)) return [a.toLowerCase(), b.toLowerCase()];
    return null;                                   // mixed types: only ordering applies
  }
  function equal(a, b) {
    var p = pair(a, b);
    if (p) return p[0] === p[1];
    return false;
  }
  function order(a, b) {                          // -1 / 0 / 1; any text outranks any number
    var p = pair(a, b);
    if (p) return p[0] < p[1] ? -1 : (p[0] > p[1] ? 1 : 0);
    if (isNum(a)) return -1;
    if (isNum(b)) return 1;
    return 0;
  }
  function asNum(v) {                             // arithmetic: blank is 0, text is #VALUE!
    if (isBlank(v)) return 0;
    if (isNum(v)) return v;
    if (v === '') return 0;
    return E('#VALUE!');
  }
  function truth(v) {
    if (isBlank(v) || v === '') return false;
    if (isNum(v)) return v !== 0;
    return /^true$/i.test(v);
  }

  var memo = {};
  function value(L, row) {
    var r = row - r0;
    // a row that is not on the sheet has no formula in it either: RANK ranges commonly run past the
    // last compiled row, and Excel ignores those cells rather than evaluating a card over blanks
    if (!(r >= 0 && r < rows.length)) return null;
    var key = L + '|' + row;
    if (key in memo) return memo[key];
    memo[key] = null;
    var v;
    if (fx[L]) v = run(ast(L), row);
    else v = (rows[r][L] !== undefined) ? rows[r][L] : null;
    memo[key] = v;
    return v;
  }

  function run(node, row) {
    switch (node.k) {
      case 'num': return node.v;
      case 'str': return node.v;
      case 'ref': return value(node.c, node.r === null ? row : node.r);
      case 'range': {
        if (node.c !== node.c2) throw new Error('hrat: range ' + node.c + ':' + node.c2 +
                                                ' spans two columns');
        var out = [];
        for (var i = node.r1; i <= node.r2; i++) out.push(value(node.c, i));
        return out;
      }
      case 'neg': {
        var x = run(node.e, row);
        if (isErr(x)) return x;
        var xn = asNum(x);
        return isErr(xn) ? xn : -xn;
      }
      case 'cmp': {
        var a = run(node.l, row), b = run(node.r, row);
        if (isErr(a)) return a;
        if (isErr(b)) return b;
        if (node.o === '=') return equal(a, b) ? 1 : 0;
        if (node.o === '<>') return equal(a, b) ? 0 : 1;
        var c = order(a, b);
        var ok = node.o === '<' ? c < 0 : node.o === '>' ? c > 0 :
                 node.o === '<=' ? c <= 0 : c >= 0;
        return ok ? 1 : 0;
      }
      case 'bin': {
        var l = run(node.l, row), rr = run(node.r, row);
        if (isErr(l)) return l;
        if (isErr(rr)) return rr;
        if (node.o === '&') return text(l) + text(rr);
        var ln = asNum(l), rn = asNum(rr);
        if (isErr(ln)) return ln;
        if (isErr(rn)) return rn;
        if (node.o === '+') return ln + rn;
        if (node.o === '-') return ln - rn;
        if (node.o === '*') return ln * rn;
        if (node.o === '/') return rn === 0 ? E('#DIV/0!') : ln / rn;
        return Math.pow(ln, rn);
      }
      case 'call': return call(node.f, node.a, row);
      default: throw new Error('hrat: node ' + node.k);
    }
  }

  function text(v) {
    if (isBlank(v)) return '';
    if (isNum(v)) return String(v);
    if (isErr(v)) return v.e;
    return v;
  }

  function callAll(list, row) {
    var out = [];
    for (var i = 0; i < list.length; i++) {
      var v = run(list[i], row);
      if (isErr(v)) return E(v.e);
      out.push(v);
    }
    return out;
  }
  function spread(a) {
    var out = [];
    a.forEach(function (v) {
      if (Object.prototype.toString.call(v) === '[object Array]') out = out.concat(v);
      else out.push(v);
    });
    return out;
  }

  function call(f, list, row) {
    if (f === 'IF') {
      var c = run(list[0], row);
      if (isErr(c)) return c;
      return run(truth(c) ? list[1] : (list.length > 2 ? list[2] : {k: 'num', v: 0}), row);
    }
    if (f === 'IFERROR') {
      var v0 = run(list[0], row);
      return isErr(v0) ? run(list[1], row) : v0;
    }
    var a = callAll(list, row);
    if (isErr(a)) return a;
    var vs = spread(a);
    switch (f) {
      case 'AND': return vs.every(truth) ? 1 : 0;
      case 'OR': return vs.some(truth) ? 1 : 0;
      case 'NOT': return truth(vs[0]) ? 0 : 1;
      case 'SUM': return vs.reduce(function (s, x) { return isNum(x) ? s + x : s; }, 0);
      case 'COUNT': return vs.filter(isNum).length;
      case 'COUNTA': return vs.filter(function (x) { return !isBlank(x); }).length;
      case 'ISBLANK': return isBlank(vs[0]) ? 1 : 0;
      // a[1] is the evaluated range (spread() would flatten it into vs), a[2] the order argument
      case 'RANK': case 'RANK.EQ': return rankIn(a[0], a[1] || [], a[2]);
      default: throw new Error('hrat: function ' + f + ' is not on this card');
    }
  }

  // 1 + how many cells rank better. order 0 (what this card uses) ranks the largest first; a
  // non-zero order ranks the smallest first. A value that is not in the range is #N/A, which is
  // exactly what the sheet prints below its own fixed range.
  function rankIn(target, list, orderArg) {
    var cells = Object.prototype.toString.call(list) === '[object Array]' ? list : [list];
    if (!isNum(target)) return E('#N/A');
    var asc = isNum(orderArg) && orderArg !== 0;
    var better = 0, tie = 0;
    cells.forEach(function (x) {
      if (!isNum(x)) return;
      if (asc ? x < target : x > target) better++;
      if (x === target) tie++;
    });
    return tie ? better + 1 : E('#N/A');
  }

  /* ---- one row, all 39 computed columns ---- */
  function compute(index) {
    memo = {};
    var v = {}, blanks = 0;
    spec.i.forEach(function (x) {
      v[x.sc] = run(ast(x.sc), r0 + index);
      if (!isErr(v[x.sc]) && x.f.indexOf('ISBLANK') < 0 && isBlank(rows[index][x.raw[0]])) blanks++;
    });
    spec.B.forEach(function (b) {
      if (!b.sub) return;
      v[b.sub] = run(ast(b.sub), r0 + index);
      v[b.pct] = run(ast(b.pct), r0 + index);
    });
    var t = spec.tail;
    v[t.max] = run(ast(t.max), r0 + index);
    v[t.ovr] = run(ast(t.ovr), r0 + index);
    // the sheet's own anchored rank, so the map holds all 39 computed columns; the grid replaces it
    // with hratRank over the rows actually loaded, which is the one named deviation from the file.
    v[t.rank] = run(ast(t.rank), r0 + index);
    v[t.risk] = run(ast(t.risk), r0 + index);
    return {row: r0 + index, v: v, blanks: blanks};
  }

  return {spec: spec, rows: rows, compute: compute,
          all: function () { return rows.map(function (_, i) { return compute(i); }); },
          raw: function (L, index) { return rows[index] ? rows[index][L] : null; }};
}

/* The card's own rank is anchored to a fixed block of rows, which the payload names as a deviation.
 * Over the rows actually loaded this is the arithmetic: 1 + how many scored better (order 0, the
 * direction the sheet uses, so the highest percentage is rank 1).
 */
function hratRank(vals, asc) {
  return vals.map(function (v) {
    if (typeof v !== 'number' || !isFinite(v)) return null;
    var better = 0, tie = 0;
    vals.forEach(function (x) {
      if (typeof x !== 'number' || !isFinite(x)) return;
      if (asc ? x < v : x > v) better++;
      if (x === v) tie++;
    });
    return tie ? better + 1 : null;
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {hratMake: hratMake, hratRank: hratRank};
}
