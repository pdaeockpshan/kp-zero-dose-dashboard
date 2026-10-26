"""Retire the "cannot land yet" blocker text now that the 26-Oct-2026 sync has landed.

push_master.py put the MTM / STA / PTP-coverage blocks into all four variants at
26-Oct-2026 14:43, so the registry sentences that describe them as master-only are now
history, not a live blocker. The rule they teach stays - it is restated in the past tense
so a future structural edit to the master still reads as the thing that re-opens the abort.

Design rules, same as every other patch module here:
  - text surgery with exact occurrence counts, asserted before anything is written;
  - --unpatch restores the previous bytes exactly;
  - neither sources.json nor SOURCES.md is ever reformatted (mixed indentation, LF).
"""

import io
import sys

REPO = r'C:\Users\HD\Documents\kp-zero-dose-dashboard'

SYNC = '26-Oct-2026 14:43'

SWAP = [
    ('_refresh/sources.json', 1,
     "it does not mean `run` can land the payload: `swap_payload` needs `const STA` in every "
     "variant and it is in the master alone until `push_master.py` carries the block to the "
     "other three - that sync counts as publishing and needs the owner's word, and until it "
     "lands `run` aborts at `check_identical` for every dataset because the master already "
     "differs from preview and `public`.",
     "it does not mean `run` can land the payload on its own: `swap_payload` needs `const STA` "
     "in every variant, which has held since `push_master.py` carried the block to the other "
     "three at " + SYNC + " - that sync counts as publishing and needs the owner's word, and "
     "while any structural edit leaves the master differing from preview and `public`, `run` "
     "aborts at `check_identical` for every dataset again."),
]

for const in ('MTM', 'STA'):
    SWAP.append(('_refresh/SOURCES.md', 1,
                 "`run` cannot land this payload yet because `swap_payload` needs `const " + const
                 + "` in every variant and it exists in the master alone until `push_master.py` "
                 "carries the block to the other three (that sync counts as publishing and needs "
                 "the owner's word).",
                 "`swap_payload` needs `const " + const + "` in every variant, which has held "
                 "since `push_master.py` carried the block to the other three at " + SYNC
                 + " (that sync counts as publishing and needs the owner's word)."))

DIVERGED_OLD = ('`index.html`, `preview.html` and `public/index.html` diverged as of 26-Oct-2026 '
                'because the `MTM` (`capMTf`), `STA` (`capSTa`) and PTP coverage/wastage '
                '(`cntPTcov`) blocks are master-only,')
DIVERGED_NEW = ('`index.html`, `preview.html` and `public/index.html` were diverged until ' + SYNC
                + ' because those `MTM` (`capMTf`), `STA` (`capSTa`) and PTP coverage/wastage '
                + '(`cntPTcov`) blocks were master-only, and a new structural edit to the master '
                'reopens the same abort until it is synced,')
SWAP.append(('_refresh/SOURCES.md', 2, DIVERGED_OLD, DIVERGED_NEW))


def read(rel):
    with io.open(REPO + '\\' + rel.replace('/', '\\'), encoding='utf-8', newline='') as f:
        return f.read()


def write(rel, text):
    with io.open(REPO + '\\' + rel.replace('/', '\\'), 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def main(argv):
    unpatch = '--unpatch' in argv
    texts = {rel: read(rel) for rel, _, _, _ in SWAP}
    plan = []
    for rel, n, a, b in SWAP:
        src, dst = (b, a) if unpatch else (a, b)
        cur = texts[rel].count(src)
        want = n - texts[rel].count(dst)
        assert cur == want, ('%s: expected %d occurrences of %r, found %d' % (rel, want, src[:60], cur))
        plan.append((rel, src, dst))
    for rel, src, dst in plan:
        texts[rel] = texts[rel].replace(src, dst)
    wrote = 0
    for rel in list(texts):
        orig = read(rel)
        if texts[rel] == orig:
            continue
        write(rel, texts[rel])
        wrote += 1
        print('%s %s %+d chars' % ('UNPATCHED' if unpatch else 'PATCHED', rel,
                                   len(texts[rel]) - len(orig)))
    if not wrote:
        print('NO_CHANGE')
    print('OK sync-note - registry text only, the four HTML variants are untouched')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
