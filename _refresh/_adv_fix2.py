import sys
P = r'C:\Users\HD\Documents\kp-zero-dose-dashboard\index.html'
s = open(P, encoding='utf-8', newline='').read()
E = [
    (' const h2=Math.min(1100,Math.max(340,Ds.length*20+110));',
     ' const h2=Math.min(1100,Math.max(340,Ds.length*20+110));const pmaxp=Ds.length?Math.max.apply(null,Ds.map(x=>x.p)):0;const dOver=Ds.filter(x=>x.p>100).length;', 1),
    ("yAxis:{title:{text:'Percent'},min:0,max:110},",
     "yAxis:{title:{text:'Percent'},min:0,max:Math.min(200,Math.max(110,Math.ceil(pmaxp/10)*10))},", 1),
    ("+(dNoCov?(' \\u00b7 '+dNoCov+' district'+(dNoCov>1?'s':'')+' carry no covered figure'):'')+'. Share = covered",
     "+(dNoCov?(' \\u00b7 '+dNoCov+' district'+(dNoCov>1?'s':'')+' carry no covered figure'):'')+(dOver?(' \\u00b7 '+dOver+' district'+(dOver>1?'s':'')+' above 100% because the covered return is not reconciled with the advance reported count'):'')+'. Share = covered", 1),
]
for o, n, c in E:
    g = s.count(o)
    if g != c:
        sys.exit('want %d got %d for %r' % (c, g, o[:60]))
    s = s.replace(o, n)
open(P, 'w', encoding='utf-8', newline='').write(s)
print('ok')
