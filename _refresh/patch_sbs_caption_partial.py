"""Stop the side-by-side caption from calling partly-covered campaigns "no data".

April and May aggregate covered figures for only some districts, so the total
percentage is rightly withheld; the caption then said "no data" even where
59,522 April and 32,750 May ZDs and their known covered counts exist. Show the
covered count and how many areas have no figure, and keep "no data" for a
campaign that genuinely has none.
"""
import io
import sys

P = r"C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html"

with io.open(P, encoding="utf-8", newline="") as f:
    t = f.read()

assert t.count("\r\n") == t.count("\n")
orig = len(t)
L = t.split("\r\n")

A = (" S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0,uk:false};areas.forEach(a=>{const c=S.acc[a][x.k];"
     "if(c){t.rep+=c.rep;t.num+=c.num;if(c.uk)t.uk=true;}});});")
B = (" S.D.forEach(x=>{const t=tot[x.k]={rep:0,num:0,uk:false,ukN:0};areas.forEach(a=>{const c=S.acc[a][x.k];"
     "if(c){t.rep+=c.rep;t.num+=c.num;if(c.uk){t.uk=true;t.ukN++;}}});});")
assert t.count(A) == 1, t.count(A)
t = t.replace(A, B, 1)

A2 = (" box.querySelector('.synsbscap').textContent=S.D.map(x=>x.l+': '+(tot[x.k].uk&&!tot[x.k].num?"
      "'recorded '+fmt(tot[x.k].rep)+' \\u00b7 coverage awaited':pc(tot[x.k])==null?'no data':"
      "pc(tot[x.k]).toFixed(1)+'% ('+fmt(tot[x.k].num)+' of '+fmt(tot[x.k].rep)+')')).join(' \\u00b7 ');")
B2 = (" box.querySelector('.synsbscap').textContent=S.D.map(x=>{const t=tot[x.k],pv=pc(t),"
      "miss=areas.length-t.ukN;return x.l+': '+(pv!=null?pv.toFixed(1)+'% ('+fmt(t.num)+' of '+fmt(t.rep)+')':"
      "t.uk&&!t.num?'recorded '+fmt(t.rep)+' \\u00b7 coverage awaited':"
      "t.uk?'coverage partly reported: '+fmt(t.num)+' covered of '+fmt(t.rep)+' \\u00b7 no figure in '+miss+' of '+"
      "areas.length+' '+S.ll.toLowerCase()+(areas.length===1?'':'s'):'no data');}).join(' \\u00b7 ');")
assert t.count(A2) == 1, t.count(A2)
t = t.replace(A2, B2, 1)

assert t.count("\r\n") == t.count("\n")
with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(t)

print("ok %d -> %d" % (orig, len(t)))
sys.exit(0)
