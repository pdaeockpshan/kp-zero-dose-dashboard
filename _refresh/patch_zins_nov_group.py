"""Give the Insights & Notes tab its own campaign picker group that includes SNID Nov-26.

The tab's narrative, district notes and double-risk table already carry the Nov
return, but the picker and the side-by-side panel were built from campDefs('z'),
which lists only the three coverage rounds. Nov has no covered figure, so it is
added as recorded-only (same treatment as the Campaign history group), and the
coverage tabs (zov/zcmp/zperf) keep their three-campaign picker.
"""
import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"

with io.open(P, encoding="utf-8", newline="") as f:
    t = f.read()

assert t.count("\r\n") == t.count("\n")
orig = len(t)
L = t.split("\r\n")


def find_one(pred, label):
    idx = [i for i, l in enumerate(L) if pred(l)]
    assert len(idx) == 1, (label, idx)
    return idx[0]


# 1. picker state carries a separate key for the Insights tab
i = find_one(lambda l: "SYNCP={z:null,d:null,v:null,a:null,hz:null}" in l, "SYNCP init")
L[i] = L[i].replace("SYNCP={z:null,d:null,v:null,a:null,hz:null}",
                    "SYNCP={z:null,zi:null,d:null,v:null,a:null,hz:null}", 1)
assert "zi:null" in L[i]

# 2. zins maps to the new group
i = find_one(lambda l: l.startswith("const GRP=") and "zins:'z'" in l, "GRP")
L[i] = L[i].replace("zperf:'z',zins:'z',", "zperf:'z',zins:'zi',", 1)
assert "zins:'zi'" in L[i]

# 3. campDefs: Nov entry for the Insights group
i = find_one(lambda l: l.startswith(" if(g==='z')return CPS.map(") and l.rstrip().endswith("[k]}));"), "campDefs z")
zi = (" if(g==='zi')return CPS.map(k=>({k,l:CAMP[k],tok:{A:/\\bApr(il)?\\b/i,M:/\\bMay\\b/i,S:/\\bSept?(ember)?\\b/i}[k]}))"
      ".concat([{k:'N',l:novLabel(),tok:/\\bNov(ember)?\\b/i}]);")
L.insert(i + 1, zi)

# 4. NOTE copy for the Insights picker
i = find_one(lambda l: l.startswith("const NOTE=") and "z:'Selected campaigns show side by side" in l, "NOTE")
assert L[i].endswith("this page\\u2019s tables and charts.',")
L[i] = L[i] + ("zi:'This picker and the side-by-side table include SNID Nov-26 on the round\\u2019s own recorded "
               "zero dose; its covered figure and validation are the post-campaign returns still awaited. "
               "Deselect a campaign to hide its columns in the tables on this page.',")
assert "zi:'This picker" in L[i]

# 5. sbsData branch: ZD rows for the coverage rounds, the Nov return for N
i = find_one(lambda l: l.startswith(" if(g==='z'){ZD.filter(r=>matchZ(r))"), "sbsData z")
zi = [
    " if(g==='zi'){ZD.filter(r=>matchZ(r)).forEach(r=>D.forEach(x=>{if(x.k!=='N')add(ak(r),x.k,r['r'+x.k],r['c'+x.k]);}));",
    "  novRows().filter(matchG).forEach(r=>D.forEach(x=>{if(x.k==='N')add(ak(r),'N',r.rN,r.cN);}));",
    "  return {ll,D,acc,m:['Reported','Covered','% covered']};}",
]
L[i + 1:i + 1] = zi

# 6. side-by-side note: say what Nov carries, and what a dash means for it
i = find_one(lambda l: l.startswith(" box.querySelector('.synsbsn').textContent="), "sbs note")
L[i] = L[i].replace(
    "textContent=(g==='hz'?'SNID Nov-26 carries recorded zero dose and LQAS:",
    "textContent=(g==='zi'?'SNID Nov-26 carries its own recorded zero-dose return only: the covered figure, digitization and validation are the post-campaign returns still awaited. ':'')"
    "+(g==='hz'?'SNID Nov-26 carries recorded zero dose and LQAS:", 1)
L[i] = L[i].replace(
    "+(g==='hz'?'A dash in the covered column means the return is awaited, not that no child was covered.'",
    "+((g==='hz'||g==='zi')?'A dash in the covered column means the return is awaited, not that no child was covered.'", 1)
assert "g==='zi'?'SNID Nov-26 carries its own" in L[i]
assert "(g==='hz'||g==='zi')?'A dash" in L[i]

t = "\r\n".join(L)
assert t.count("\r\n") == t.count("\n")
with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(t)

print("ok %d -> %d" % (orig, len(t)))
sys.exit(0)
