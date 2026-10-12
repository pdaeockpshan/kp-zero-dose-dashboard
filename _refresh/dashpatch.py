"""CRLF-safe surgical patching of the four dashboard variants.

Every mutation happens in memory first; nothing is written until all asserts pass.
"""
import datetime
import hashlib
import io
import json
import os
import re

import srcutil

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
STAMP_RE = r'(\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2})'
PKT = datetime.timezone(datetime.timedelta(hours=5), 'PKT')


def pkt_stamp(when=None):
    t = when or datetime.datetime.now(PKT)
    return '%02d-%s-%d %02d:%02d' % (t.day, MONTHS[t.month - 1], t.year, t.hour, t.minute)


class Variant(object):
    def __init__(self, path, rel):
        self.path = path
        self.rel = rel
        self.orig = srcutil.read_text(path)
        self.text = self.orig
        self.changes = []

    @property
    def changed(self):
        return self.text != self.orig

    def delta(self):
        return len(self.text) - len(self.orig)

    def md5(self):
        return hashlib.md5(self.text.encode('utf-8')).hexdigest()

    def require(self, cond, msg):
        if not cond:
            raise AssertionError('%s: %s' % (self.rel, msg))

    def count(self, needle):
        return self.text.count(needle)


def load_variants(cfg=None):
    cfg = cfg or srcutil.load_sources()
    root = cfg['repo']
    vs = []
    for rel in cfg['variants']:
        p = os.path.join(root, rel.replace('/', os.sep))
        if not os.path.exists(p):
            raise SystemExit('missing variant: %s' % p)
        vs.append(Variant(p, rel))
    return cfg, vs


def _scan_literal(s, i):
    """i points at '{' or '['; return index just past the matching closer."""
    open_ch = s[i]
    close_ch = '}' if open_ch == '{' else ']'
    depth = 0
    instr = False
    esc = False
    n = len(s)
    while i < n:
        c = s[i]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c in '{[':
                depth += 1
            elif c in '}]':
                depth -= 1
                if depth == 0:
                    return i + 1, close_ch
        i += 1
    raise ValueError('unterminated JSON literal for %s' % open_ch)


def payload_span(s, name):
    """(start, end) of the JSON literal in `const <name> = {...};`"""
    hits = [m for m in re.finditer(r'(?:const|var|let)\s+' + re.escape(name) + r'\s*=\s*', s)]
    if len(hits) != 1:
        raise AssertionError('const %s found %d times (expected 1)' % (name, len(hits)))
    m = hits[0]
    i = m.end()
    if s[i] not in '{[':
        raise AssertionError('const %s does not start with a JSON literal' % name)
    end, _ = _scan_literal(s, i)
    tail = s[end:end + 4]
    if not tail.startswith(';'):
        raise AssertionError('const %s literal is not terminated by ";" (got %r)' % (name, tail))
    return i, end


def get_payload(s, name):
    i, e = payload_span(s, name)
    return s[i:e]


def swap_payload(v, name, payload_json):
    """Replace the embedded JSON literal for `const name = ...;`. Returns True if it changed."""
    json.loads(payload_json.replace('<\\/', '</'))
    v.require('\n' not in payload_json and '\r' not in payload_json, 'payload contains newlines')
    i, e = payload_span(v.text, name)
    old = v.text[i:e]
    if old == payload_json:
        return False
    v.text = v.text[:i] + payload_json + v.text[e:]
    v.changes.append('%s %d -> %d chars' % (name, len(old), len(payload_json)))
    return True


def get_stamp(v):
    m1 = re.findall(r'Updated ' + STAMP_RE, v.text)
    m2 = re.findall(r'Last updated ' + STAMP_RE, v.text)
    v.require(len(m1) == 1, 'hero "Updated" stamp found %d times' % len(m1))
    v.require(len(m2) == 1, 'header "Last updated" stamp found %d times' % len(m2))
    v.require(m1[0] == m2[0], 'stamps disagree: %s vs %s' % (m1[0], m2[0]))
    return m1[0]


def set_stamp(v, new, old=None):
    old = old or get_stamp(v)
    v.require(v.text.count(old) == 2, 'stamp %s occurs %d times (expected 2)' % (old, v.text.count(old)))
    v.text = v.text.replace(old, new)
    v.changes.append('stamp %s -> %s' % (old, new))
    return old


def assert_crlf(v):
    v.require('\r\n' in v.text, 'no CRLF left in file')
    v.require(v.text.count('\n') == v.text.count('\r\n'), 'mixed line endings')


def append_version(cfg, line, dry=False):
    """Append one CRLF note line to every version file."""
    root = cfg['repo']
    touched = []
    for rel in cfg.get('version_files') or []:
        p = os.path.join(root, rel.replace('/', os.sep))
        if not os.path.exists(p):
            continue
        s = srcutil.read_text(p)
        if not s.endswith('\r\n'):
            s = s.rstrip('\r\n') + '\r\n'
        s += line.replace('\n', ' ').strip() + '\r\n'
        touched.append((p, s))
    if not dry:
        for p, s in touched:
            srcutil.write_text(p, s)
    return [p for p, _ in touched]


def commit_variants(vs):
    """Post-mutation consistency checks, then write everything."""
    for v in vs:
        assert_crlf(v)
    return True


def write_variants(vs):
    for v in vs:
        if v.changed:
            srcutil.write_text(v.path, v.text)


def check_identical(cfg, vs):
    group = cfg.get('identical_group') or []
    byrel = {v.rel: v for v in vs}
    sums = {r: byrel[r].md5() for r in group if r in byrel}
    if len(set(sums.values())) > 1:
        raise AssertionError('public build diverged from index/preview: %s' % sums)
    return sums
