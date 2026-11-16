"""Label the closure headline with the round it is evaluated at.

closeAll() builds its per-UC status from MISM.camps, whose latest entry is
SNID Sept-26; SNID Nov-26 has no MISM history and no zero-dose covered return,
so 12.3% is a Sept reading. Say so instead of letting a post-Nov reader take it
as the closed round's result.
"""
import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"

with io.open(P, encoding="utf-8", newline="") as f:
    t = f.read()

assert t.count("\r\n") == t.count("\n")
orig = len(t)

A = "of evaluable UCs have closed the gap (${fmt(C.cl)} of ${fmt(S.wd)}) \u00b7 ${fmt(C.nd)} with incomplete evidence \u00b7 ${fmt(C.ro)} reopened</span>"
B = ("of evaluable UCs had closed the gap by ${esc((MISM.camps||[])[0]||'the last validated round')} "
     "(${fmt(C.cl)} of ${fmt(S.wd)}) \u00b7 ${fmt(C.nd)} with incomplete evidence \u00b7 ${fmt(C.ro)} reopened "
     "\u00b7 SNID Nov-26 is not yet in this check; its zero-dose covered return is awaited</span>")
assert t.count(A) == 1, t.count(A)
t = t.replace(A, B, 1)

assert t.count("\r\n") == t.count("\n")
with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(t)

print("ok %d -> %d" % (orig, len(t)))
sys.exit(0)
