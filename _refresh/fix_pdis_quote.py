# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
p = 'index.html'
raw = open(p, encoding='utf-8', newline='').read()
bad = "the UC-wise table's own record and target"
good = "the UC-wise table" + chr(92) + "'s own record and target"
n = raw.count(bad)
assert n == 1, n
out = raw.replace(bad, good)
assert out.count(good) == 1
open(p, 'w', encoding='utf-8', newline='').write(out)
print('fixed', n, len(raw), '->', len(out))
