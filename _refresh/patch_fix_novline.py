import hashlib, os, sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
t = open(P, 'r', encoding='utf-8', newline='').read()
assert t.count('\r\n') == t.count('\n'), 'file left LF mode'

lines = t.split('\r\n')
A = ' if(NRW.length){const DN={};'
idx = [i for i, s in enumerate(lines) if s.startswith(A)]
assert len(idx) == 1, 'anchor hits %r' % idx
i = idx[0]
assert lines[i + 1].startswith('  const dt=Object.values(DN)'), lines[i + 1][:60]
assert lines[i + 2].startswith('  const ks=mHH'), lines[i + 2][:60]
assert lines[i + 3].startswith('  I.push(`<b>SNID Nov-26 closed'), lines[i + 3][:60]
assert lines[i + 4].startswith(" else I.push('<b>SNID Nov-26 did not cover"), lines[i + 4][:60]

new = [
    ' if(NRW.length){const DN={}; NRW.forEach(x=>{const g=DN[x.d]=DN[x.d]||{k:x.d,rep:0};g.rep+=x.rN||0;});',
    '  const dt=Object.values(DN).sort((a,b)=>b.rep-a.rep), t3=dt.slice(0,3), sh3=nvRep?S_(t3,g=>g.rep)/nvRep*100:null;',
    '  const ks=mHH?mSep/mHH*1000:null, kn=mHH?mNov/mHH*1000:null, dch=mSep?mNov-mSep:null;',
    "  const nvTop=t3.length?' Largest caseloads: '+t3.map(g=>esc(g.k)+' ('+fmt(g.rep)+')').join(', ')+(sh3==null?'':' \u2014 '+sh3.toFixed(0)+'% of the round between them')+'.':'';",
    "  const nvCmp=nm.length?' On the '+fmt(nm.length)+' UCs that are in both Sept and Nov, reported ZDs went from '+fmt(mSep)+' to '+fmt(mNov)+' ('+sgn(dch,0)+', '+sgn(mSep?(mNov/mSep-1)*100:null,1)+'%), or '+(ks==null?'\u2013':ks.toFixed(1))+' \u2192 '+(kn==null?'\u2013':kn.toFixed(1))+' per 1,000 households; '+fmt(NVMUP)+' UCs rose and '+fmt(NVMDN)+' fell. A fall can mean fewer zero-dose children found or fewer recorded \u2014 the Nov validation return separates the two.':'';",
    "  I.push('<b>SNID Nov-26 closed with '+fmt(nvRep)+' zero-dose children reported across '+fmt(nvU)+' UCs in '+fmt(nvD)+' districts.</b> Its own zero-dose covered figure is a post-campaign return and is not in yet, so Nov coverage cannot be measured and Sept stays the last measured round.'+nvCmp+nvTop);}",
]
lines[i:i + 4] = new

out = '\r\n'.join(lines)
assert out.count('\r\n') == out.count('\n'), 'CRLF broken'
open(P, 'w', encoding='utf-8', newline='').write(out)
print('fixed line, chars', len(out))
print('md5', hashlib.md5(out.encode('utf-8')).hexdigest())
