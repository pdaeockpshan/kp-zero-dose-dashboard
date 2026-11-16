"""Label the 'half of the missed children' figure with the round it is summed at.

Q1's hero now states Nov's own still-missed return (162,874, household target),
while S.h50 and S.st come from the Sept register. Naming the round on the h50
row stops the reader attaching it to the Nov figure.
"""
import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"

with io.open(P, encoding="utf-8", newline="") as f:
    t = f.read()

assert t.count("\r\n") == t.count("\n")
orig = len(t)

A = "${S.h50||'\u2013'} UCs hold half of the missed children</div>"
B = "${S.h50||'\u2013'} UCs hold half of the ${esc(mc)} missed children</div>"
assert t.count(A) == 1, t.count(A)
t = t.replace(A, B, 1)

assert t.count("\r\n") == t.count("\n")
with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(t)

print("ok %d -> %d" % (orig, len(t)))
sys.exit(0)
