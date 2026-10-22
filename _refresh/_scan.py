# -*- coding: utf-8 -*-
"""Scratch: print short (non-payload) lines from index.html that mention a term."""
import io
import re
import sys

term = sys.argv[1]
path = sys.argv[2] if len(sys.argv) > 2 else 'index.html'
rx = re.compile(term, re.I)
with io.open(path, encoding='utf-8') as f:
    for n, line in enumerate(f, 1):
        if len(line) > 4000:
            continue
        if rx.search(line):
            print('%6d %s' % (n, line.rstrip()[:300]))
