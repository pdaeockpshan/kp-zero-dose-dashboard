import sys
P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
s = open(P, encoding='utf-8', newline='').read()
old = " el('cntADV').textContent=fmt(R.length)+' UCs';"
new = (" el('cntADV').textContent=fmt(R.length)+' UCs';\r\n"
       r" el('adNote').textContent=ADV.c.length+' campaigns \u00b7 '+ADV.c[0].y+'\u2013'+ADV.c[ADV.c.length-1].y+' \u00b7 export '+ADV.asof;")
if s.count(old) != 1:
    sys.exit('anchor count %d' % s.count(old))
s = s.replace(old, new)
open(P, 'w', encoding='utf-8', newline='').write(s)
print('adNote restored')
