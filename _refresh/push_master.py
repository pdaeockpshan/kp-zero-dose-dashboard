"""Push a hand-edited index.html out to the other three dashboard variants.

index.html is the master. preview.html and public/index.html are byte-identical copies of it.
The internal build (Zero_Dose_Digitization_Dashboard.html) is the same file except for four
regions: the un-sanitised VCH / AFP / WPV payloads and `const VSHOWN = true`.

So the internal build is regenerated from the new master plus the payloads of the current
internal file, but only after proving that the same regeneration still reproduces that internal
file from the previous master byte for byte. Nothing is written unless the proof passes, so a new
per-variant difference can never be flattened away by an overwrite.

Usage:
  python _refresh/push_master.py --dry-run    proof and diff report, writes nothing
  python _refresh/push_master.py              push, bump the PKT stamp, note in version.txt
  python _refresh/push_master.py --no-stamp   push, leave the stamp and version files alone
"""
import argparse
import datetime
import hashlib
import os
import re
import sys

import dashpatch
import srcutil

MASTER = 'index.html'
CLONES = ['preview.html', 'public/index.html']
INTERNAL = 'Zero_Dose_Digitization_Dashboard.html'
PER_VARIANT = ['VCH', 'AFP', 'WPV']
VSHOWN = re.compile(r'(const VSHOWN = )(true|false)(;)')


def swap_literal(text, name, payload):
    i, e = dashpatch.payload_span(text, name)
    return text[:i] + payload + text[e:]


def set_vshown(text, value):
    if len(VSHOWN.findall(text)) != 1:
        raise SystemExit('ABORT: VSHOWN literal not found exactly once')
    return VSHOWN.sub(lambda m: m.group(1) + value + m.group(3), text, count=1)


def own_payloads(text):
    return {name: dashpatch.get_payload(text, name) for name in PER_VARIANT}


def as_internal(master_text, own):
    t = set_vshown(master_text, 'true')
    for name in PER_VARIANT:
        t = swap_literal(t, name, own[name])
    return t


def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def check_crlf(rel, text):
    if '\r\n' not in text or text.count('\n') != text.count('\r\n'):
        raise SystemExit('ABORT: %s has mixed or LF-only line endings' % rel)


def first_diff(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))


def variant_paths(cfg):
    paths = {}
    for rel in [MASTER] + CLONES + [INTERNAL]:
        p = os.path.join(cfg['repo'], rel.replace('/', os.sep))
        if not os.path.exists(p):
            raise SystemExit('missing variant: %s' % p)
        paths[rel] = p
    return paths


def load_checked(cfg):
    paths = variant_paths(cfg)
    master = srcutil.read_text(paths[MASTER])
    prev = srcutil.read_text(paths[CLONES[0]])
    internal = srcutil.read_text(paths[INTERNAL])
    for rel in CLONES[1:]:
        if md5(srcutil.read_text(paths[rel])) != md5(prev):
            raise SystemExit('ABORT: %s already diverges from %s, refusing to overwrite it'
                             % (rel, CLONES[0]))
    for rel, text in ((MASTER, master), (CLONES[0], prev), (INTERNAL, internal)):
        check_crlf(rel, text)
    if VSHOWN.search(master).group(2) != 'false':
        raise SystemExit('ABORT: %s carries VSHOWN = true, it is not the public master' % MASTER)
    own = own_payloads(internal)
    rebuilt = as_internal(prev, own)
    if rebuilt != internal:
        raise SystemExit('ABORT: regeneration cannot reproduce %s (first difference at char %s). '
                         'The variants differ in more than %s plus VSHOWN, so this tool must be '
                         'extended before it may overwrite anything.'
                         % (INTERNAL, format(first_diff(internal, rebuilt), ','),
                            ' / '.join(PER_VARIANT)))
    print('proof: %s regenerates exactly from the previous master plus its own %s payloads'
          % (INTERNAL, ' / '.join(PER_VARIANT)))
    return paths, master, prev, internal, own


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-stamp', action='store_true')
    ap.add_argument('--note', help='version.txt line, derived from the master diff when omitted')
    a = ap.parse_args()

    cfg = srcutil.load_sources()
    paths, master, prev, internal, own = load_checked(cfg)
    stamps = {rel: dashpatch.get_stamp(dashpatch.Variant(paths[rel], rel)) for rel in paths}
    if len(set(stamps.values())) != 1:
        raise SystemExit('ABORT: stamps disagree across variants: %s' % stamps)
    old = stamps[MASTER]
    new = old if a.no_stamp else dashpatch.pkt_stamp(datetime.datetime.now(dashpatch.PKT))
    if old not in master:
        raise SystemExit('ABORT: master no longer carries stamp %s' % old)

    plan = [(MASTER, master), (CLONES[0], master), (CLONES[1], master),
            (INTERNAL, as_internal(master, own))]
    if not a.no_stamp:
        plan = [(rel, text.replace(old, new)) for rel, text in plan]
    for rel, text in plan:
        check_crlf(rel, text)
    pub = [md5(text) for rel, text in plan if rel in cfg['identical_group']]
    if len(set(pub)) != 1:
        raise SystemExit('ABORT: the public build would diverge from index.html')

    delta = len(master) - len(prev)
    print('master: %s -> %s chars (%+d against the previous copy)'
          % (format(len(prev), ','), format(len(master), ','), delta))
    for rel, text in plan:
        print('  %-42s %s chars  %+d against current'
              % (rel, format(len(text), ','), len(text) - len(srcutil.read_text(paths[rel]))))
    note = a.note or ('Pushed the hand-edited index.html master to preview / public / internal builds '
                      + '(%+d chars)' % delta)
    if not a.no_stamp:
        note += '. Timestamp refresh %s PKT' % new
    print('stamp: %s -> %s' % (old, new))
    print('version note: %s' % note[:170])
    if a.dry_run:
        print('DRY RUN - nothing written')
        return 0

    for rel, text in plan:
        srcutil.write_text(paths[rel], text)
        print('WROTE %s (%s bytes)' % (rel, format(os.path.getsize(paths[rel]), ',')))
    after = {rel: md5(srcutil.read_text(paths[rel])) for rel in paths}
    if len(set(after[rel] for rel in cfg['identical_group'])) != 1:
        raise SystemExit('ABORT after write: identical group diverged: %s' % after)
    if not a.no_stamp:
        dashpatch.append_version(cfg, note)
    st = srcutil.load_state()
    st['last_push'] = {'at': datetime.datetime.now(dashpatch.PKT).isoformat(timespec='seconds'),
                       'stamp': new, 'master_md5': after[MASTER], 'internal_md5': after[INTERNAL],
                       'chars': len(master), 'note': note}
    srcutil.save_state(st)
    print('md5: %s' % after)
    print('PUSHED all 4 variants (working copy only, nothing committed or pushed to git)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

