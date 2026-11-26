"""Inject the WPV1 confirmed-case profile into the master (index.html).

Four marked blocks:
  /* WPVPROF:DATA:START */   const AFPUC = {...};            before `const CHD = `
  <!-- WPVPROF:START -->     the card + four cascading selects + #wpvBody
  /* WPVPROF:JS:START */     the WPVC module (from _refresh/wpvprof.js)
  /* WPVPROF:HOOK:START */   one line in render(): WPVC.draw() on the surv tab

Every block is delimited so the patch is reversible and re-running after a
module edit replaces it in place instead of stacking a second copy.

Usage:
  python _refresh/patch_wpvprof.py            apply to index.html
  python _refresh/patch_wpvprof.py --check    verify the blocks are present
  python _refresh/patch_wpvprof.py --unpatch  remove all four blocks
"""
import argparse
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import srcutil

MASTER = os.path.join(ROOT, 'index.html')
JS = os.path.join(HERE, 'wpvprof.js')
DATA = os.path.join(srcutil.OUT, 'afpuc.json')

PAYLOAD = ('const CHD = ',)
MARKUP = '<div class="card" style="margin-bottom:14px"><h3>What the surveillance data says</h3><ul class="ins" id="svIns"></ul></div>'
BEFORE_INIT = '\r\nkxInit();\r\n'
HOOK_AT = '[TAB]();'

DATA_M = ('/* WPVPROF:DATA:START */', '/* WPVPROF:DATA:END */')
HTML_M = ('<!-- WPVPROF:START -->', '<!-- WPVPROF:END -->')
JS_M = ('/* WPVPROF:JS:START */', '/* WPVPROF:JS:END */')
HOOK_M = ('/* WPVPROF:HOOK:START */', '/* WPVPROF:HOOK:END */')
HOOK = "if(TAB==='surv'&&typeof WPVC!=='undefined')WPVC.draw();"

CARD = """<div class="card" id="wpvCard" style="border-top:5px solid #b91c1c">
<div class="tblhdr"><h3 style="margin:0">WPV1 confirmed-case profile — campaigns, post-campaign activity, AFP, zero dose and routine EPI</h3><span class="cnt" id="wpvCnt"></span></div>
<div class="hint" style="margin:0 0 10px">Pick a division, district, tehsil and union council. The profile reads the last six campaigns (target movement, coverage, recorded missed, same-day cover, still missed with its NA and refusal split, ICM household clusters, market survey, LQAS, PCM and PCHS), the AFP register and its timeliness, zero-dose recording, and routine EPI with dropouts — then lists the recommendations its own thresholds trigger. Built for a confirmed WPV1 case file; it reads any council.</div>
<div class="pdtools" style="max-width:none;margin:0 0 12px">
 <div class="pdt">Case profile<span class="pdstat">UC level</span><small>one council at a time · every figure recalculated on selection</small></div>
 <div class="pdbtns">
  <div><label for="wpvDiv">Division</label><select id="wpvDiv" aria-label="Division"></select></div>
  <div><label for="wpvDist">District</label><select id="wpvDist" aria-label="District"></select></div>
  <div><label for="wpvTeh">Tehsil</label><select id="wpvTeh" aria-label="Tehsil"></select></div>
  <div><label for="wpvUc">Union council</label><select id="wpvUc" aria-label="Union council"></select></div>
  <button class="btn" id="wpvCsv" disabled><span data-ic></span> Download profile (CSV)</button>
  <button class="btn" id="wpvReset"><span data-ic></span> Reset</button>
 </div>
</div>
<div id="wpvBody"></div>
</div>"""


def fail(msg):
    raise SystemExit('ERR wpvprof ' + msg)


def count1(s, a, what):
    n = s.count(a)
    if n != 1:
        fail('%s occurs %d times, expected 1' % (what, n))
    return s.find(a)


def line_at(s, i):
    return i == 0 or s[i - 2:i] == '\r\n'


def remove(s, pair, what):
    a, b = pair
    if a not in s and b not in s:
        return s, 0
    if s.count(a) != 1 or s.count(b) != 1:
        fail('%s markers are damaged (%d start, %d end)' % (what, s.count(a), s.count(b)))
    i = s.find(a)
    j = s.find(b) + len(b)
    if not line_at(s, i):
        fail('%s start marker is not at the head of a line' % what)
    if s[j:j + 2] != '\r\n':
        fail('%s end marker is not followed by CRLF' % what)
    return s[:i] + s[j + 2:], 1


def add(s, at, pair, body, what):
    a, b = pair
    if a in s or b in s:
        fail('%s block still present after strip' % what)
    ins = a + '\r\n' + body + '\r\n' + b + '\r\n'
    return s[:at] + ins + s[at:]


def crlf(t, what):
    t = t.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    if t.count('\n') != t.count('\r\n'):
        fail('%s did not convert cleanly to CRLF' % what)
    return t


def load_data():
    if not os.path.exists(DATA):
        fail('%s missing - run _refresh/extract_afpuc.py first' % DATA)
    raw = srcutil.read_text(DATA)
    if '\n' in raw:
        fail('afpuc json carries a newline')
    d = json.loads(raw.replace('<\\/', '</'))
    for k in ('n', 'ucs', 'r', 'src', 'asof'):
        if k not in d:
            fail('afpuc json has no %r key' % k)
    if '"NAME"' in raw or '"EPID"' in raw or '"LABNO"' in raw:
        fail('afpuc json mentions a person-level column')
    return raw, d


def load_js():
    if not os.path.exists(JS):
        fail('%s missing' % JS)
    t = crlf(srcutil.read_text(JS), 'wpvprof.js')
    if not t.startswith('/* WPVPROF:JS:START */\r\n'):
        fail('wpvprof.js does not open with its marker')
    if not t.rstrip('\r\n').endswith('/* WPVPROF:JS:END */'):
        fail('wpvprof.js does not close with its marker')
    if 'AFPUC' not in t or 'function paint(' not in t:
        fail('wpvprof.js does not look like the profile module')
    return t.replace('/* WPVPROF:JS:START */\r\n', '').replace('\r\n/* WPVPROF:JS:END */', '').rstrip('\r\n')


def strip_all(s):
    n = 0
    for pair, what in ((HOOK_M, 'hook'), (JS_M, 'js'), (DATA_M, 'data'), (HTML_M, 'markup')):
        s, k = remove(s, pair, what)
        n += k
    return s, n


def check(s):
    rows = []
    for pair, what in ((DATA_M, 'data'), (HTML_M, 'markup'), (JS_M, 'js'), (HOOK_M, 'hook')):
        rows.append((what, s.count(pair[0]), s.count(pair[1])))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    s = srcutil.read_text(MASTER)
    if '\r\n' not in s or s.count('\n') != s.count('\r\n'):
        fail('index.html is not uniformly CRLF')
    orig = len(s)

    if a.check:
        bad = 0
        for what, x, y in check(s):
            ok = x == 1 and y == 1
            bad += 0 if ok else 1
            print('%-7s %s  start=%d end=%d' % (what, 'ok' if ok else 'MISSING', x, y))
        if 'const AFPUC = ' in s:
            i = s.find('const AFPUC = ')
            j = s.find('\r\n', i)
            print('payload  %d chars' % (j - i))
        print('size     %d chars' % len(s))
        if HOOK not in s:
            print('hook     MISSING')
            bad += 1
        raise SystemExit(0 if bad == 0 else 1)

    if a.unpatch:
        s2, n = strip_all(s)
        if not n:
            print('nothing to remove')
            raise SystemExit(0)
        if 'WPVPROF' in s2:
            fail('markers survived the strip')
        if s2.count(PAYLOAD[0]) != 1 or s2.count('\r\nkxInit();\r\n') != 1 or s2.count(HOOK_AT) != 1:
            fail('anchors did not return to one each after the strip')
        if not a.dry_run:
            srcutil.write_text(MASTER, s2)
        print('OK wpvprof unpatch %d blocks, %d -> %d chars' % (n, orig, len(s2)))
        raise SystemExit(0)

    raw, d = load_data()
    body = load_js()

    s, n = strip_all(s)
    if n:
        print('replaced %d existing block(s)' % n)
    if 'WPVC' in s or 'AFPUC' in s:
        fail('WPVC/AFPUC appear outside the marked blocks')

    data_body = 'const AFPUC = ' + raw + ';'
    i = count1(s, PAYLOAD[0], 'payload anchor')
    if not line_at(s, i):
        fail('payload anchor is not at the head of a line')
    s = add(s, i, DATA_M, data_body, 'data')

    i = count1(s, MARKUP, 'insights card')
    i += len(MARKUP) + 2          # step over the CRLF that follows it
    s = add(s, i, HTML_M, crlf(CARD, 'card'), 'markup')

    i = count1(s, BEFORE_INIT, 'kxInit anchor') + 2
    s = add(s, i, JS_M, body, 'js')

    i = count1(s, HOOK_AT, 'render hook anchor') + len(HOOK_AT) + 2
    s = add(s, i, HOOK_M, HOOK, 'hook')

    if not a.dry_run:
        srcutil.write_text(MASTER, s)
    for what, x, y in check(s):
        if x != 1 or y != 1:
            fail('%s block is not singular after apply' % what)
    if s.count('const AFPUC = ') != 1 or s.count('const WPVC=') != 1 or s.count(HOOK) != 1:
        fail('payload/module/hook count is wrong after apply')
    print('OK wpvprof %d -> %d chars (+%d)  payload %d  module %d  cases %d  ucs %d  asof %s'
          % (orig, len(s), len(s) - orig, len(raw), len(body), d['n'], len(d['ucs']), d['asof']))
    print('md5 %s' % hashlib.md5(s.encode('utf-8')).hexdigest())


if __name__ == '__main__':
    main()
