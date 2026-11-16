import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"
t = io.open(P, encoding="utf-8", newline="").read()
assert t.count("\r\n") == t.count("\n")

a = r"const t=tot[x.k],pv=pc(t),miss=areas.length-t.ukN;return x.l+': '"
assert t.count(a) == 1, t.count(a)
t = t.replace(a, r"const t=tot[x.k],pv=pc(t);return x.l+': '", 1)

a2 = r"' \u00b7 no figure in '+miss+' of '"
assert t.count(a2) == 1, t.count(a2)
t = t.replace(a2, r"' \u00b7 no figure in '+t.ukN+' of '", 1)

assert t.count("\r\n") == t.count("\n")
io.open(P, "w", encoding="utf-8", newline="").write(t)
print("ok", len(t))
sys.exit(0)
