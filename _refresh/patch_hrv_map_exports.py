# -*- coding: utf-8 -*-
"""Give the HRA "HRA risk by district" map the same three downloads as the EPI and deployment maps.

The owner asked, 28-Oct-2026: 'i need export option for map in "HRA risk by district", all three
options PPTX, JPEG, PNG'. The card only offered the district roll-up CSV.

The exports are the live <svg> re-serialised with its own font stack (the page stylesheet never
travels with a data URI), rasterised at 2x, and laid out with the card's own legend and caption, so
the file explains its colours without the browser open. The PPTX slide carries the map and the ten
worst districts under the measure on screen, and the measure switch (#hrvMK) is read at draw time,
so the file always matches the selected measure and the division / district filter.

Applied to index.html on top of patch_hrat_scope.py, patch_hrat_round2.py and patch_hrdv_ui.py.
Un-apply THIS module before any of those three. `--unpatch` restores the previous file byte for byte.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

MASTER = 'index.html'

JS = """// HRA AT A GLANCE (4b/5): the district map as a file. Same geometry as the card: the live <svg> is
// re-serialised with its own font stack before rasterising, because the page stylesheet never travels
// with a data URI. Legend and caption come from the same values the card shows, and the measure on
// screen (#hrvMK) is what the file names, so the two cannot disagree.
let _HRVMAP=null,_HRVMW=0;
function hrvMapShot(){
 const svg=el('hrvMap')&&el('hrvMap').querySelector('svg');
 if(!svg)return Promise.resolve(null);
 const vb=(svg.getAttribute('viewBox')||'').split(/[\\s,]+/).map(Number),c=svg.cloneNode(true);
 c.removeAttribute('style');c.setAttribute('xmlns','http://www.w3.org/2000/svg');
 c.setAttribute('width',String(vb[2]));c.setAttribute('height',String(vb[3]));
 c.setAttribute('font-family','"Segoe UI",Arial,sans-serif');
 const img=new Image();
 return new Promise(function(res,rej){
  img.onload=function(){res({img:img,w:vb[2],h:vb[3]});};
  img.onerror=function(){rej(new Error('map svg would not raster'));};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(c));});
}
function hrvMapWrap(t,w){
 const m=document.createElement('canvas').getContext('2d');
 m.font='12px "Segoe UI",Arial,sans-serif';const out=[];let cur='';
 String(t).split(/\\s+/).forEach(function(v){const s=cur?cur+' '+v:v;
  if(m.measureText(s).width>w&&cur){out.push(cur);cur=v;}else cur=s;});
 if(cur)out.push(cur);return out;
}
async function hrvMapImgURL(kind,plain){
 const A=_HRVMAP;if(!A)return null;
 const sh=await hrvMapShot();if(!sh)return null;
 const S=2,W=660,TB=plain?0:56,LH=26,all=hrvMapWrap(A.C,W-32),ln=all.slice(0,4);
 if(all.length>4)ln[3]=ln[3].replace(/\\s*\\S*$/,'')+'\\u2026';
 const CH=ln.length?ln.length*15+12:0, mh=Math.round((W-24)*sh.h/sh.w), H=TB+mh+LH+CH, ly=TB+mh+16;
 const cv=document.createElement('canvas'); cv.width=W*S; cv.height=H*S;
 const x=cv.getContext('2d'); x.scale(S,S); x.fillStyle='#ffffff'; x.fillRect(0,0,W,H);
 if(!plain){x.fillStyle='#0f172a';x.font='bold 21px "Segoe UI",Arial,sans-serif';x.fillText(A.T,16,28);
  x.fillStyle='#475569';x.font='13px "Segoe UI",Arial,sans-serif';x.fillText(A.S,16,47);}
 x.drawImage(sh.img,(W-mh*sh.w/sh.h)/2,TB+2,mh*sh.w/sh.h,mh);
 let lx=16; x.font='12.5px "Segoe UI",Arial,sans-serif';
 A.L.forEach(function(b){x.fillStyle=b[0];x.fillRect(lx,ly-9,11,11);
  x.fillStyle='#374151';x.fillText(b[1],lx+15,ly);lx+=15+x.measureText(b[1]).width+16;});
 if(ln.length){x.fillStyle='#64748b';x.font='12px "Segoe UI",Arial,sans-serif';
  ln.forEach(function(t,i){x.fillText(t,16,ly+24+i*15);});}
 return {url:kind==='jpeg'?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png'),w:W,h:H};
}
function hrvMapFile(ext){return (_HRVMAP?_HRVMAP.base:'HRA_district_map')+ext;}
function hrvMapDl(url,name){
 const a=document.createElement('a');a.href=url;a.download=name;a.rel='noopener';
 document.body.appendChild(a);a.click();a.remove();
}
function hrvMapWire(){
 if(_HRVMW)return;_HRVMW=1;
 [['btnHRVMjpg','jpeg','.jpg','JPG'],['btnHRVMpng','png','.png','PNG']].forEach(function(p){
  const b=el(p[0]);if(!b)return;
  b.onclick=async function(){
   if(!_HRVMAP){toast('The map is not on screen to download');return;}
   b.disabled=true;
   try{const o=await hrvMapImgURL(p[1]);
    if(!o)toast('The map is not on screen to download');
    else{hrvMapDl(o.url,hrvMapFile(p[2]));toast(p[3]+' downloaded');}}
   catch(e){console.error(e);toast('Could not create the '+p[3]);}
   b.disabled=!_HRVMAP;};});
 const b=el('btnHRVMpptx');if(!b)return;
 b.onclick=async function(){
  const A=_HRVMAP;if(!A){toast('The map is not on screen to download');return;}
  b.disabled=true;
  try{
   await loadPptx();
   const o=await hrvMapImgURL('png',true);
   if(!o){toast('The map is not on screen to download');b.disabled=!_HRVMAP;return;}
   const P=window.PptxGenJS,pptx=new P(),F='Segoe UI',lst=A.rows.slice(0,10);
   pptx.layout='LAYOUT_WIDE';pptx.title=A.T;pptx.subject=A.S;
   const s=pptx.addSlide();s.background={color:'FFFFFF'};
   s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:0.14,fill:{color:'86198F'},line:{color:'86198F'}});
   s.addText(A.T,{x:0.5,y:0.24,w:12.3,h:0.55,fontFace:F,fontSize:24,bold:true,color:'86198F'});
   s.addText(A.S,{x:0.5,y:0.84,w:12.3,h:0.35,fontFace:F,fontSize:12,color:'6B7280'});
   let ih=5.5,iw=ih*o.w/o.h; if(iw>5.1){iw=5.1;ih=iw*o.h/o.w;}
   s.addImage({data:o.url,x:0.45,y:1.28,w:iw,h:ih});
   const rx=0.45+iw+0.34, rw=12.43-iw-0.34,
    hc=function(t,j){return {text:t,options:{bold:true,color:'FFFFFF',fill:{color:'86198F'},fontSize:10,
     align:j?'right':'left',valign:'middle'}};},
    rows=[[hc('District',0),hc(A.mk==='mean'?'Score':'High-Risk share',1)]].concat(lst.map(function(g){
     const v=A.mk==='mean'?g.p:g.hi;
     return [{text:DNAME(g.c)+' \\u00b7 '+g.dv,options:{fontSize:9.5,valign:'middle'}},
      {text:(v==null?'-':v.toFixed(1)+'%'),options:{fontSize:10,bold:true,align:'right',valign:'middle'}}];}));
   s.addTable(rows,{x:rx,y:1.28,w:rw,colW:[rw*0.66,rw*0.34],fontFace:F,
    rowH:[0.32].concat(rows.slice(1).map(function(){return 0.26;})),
    border:{type:'solid',pt:0.5,color:'E5E7EB'},autoPage:false,margin:0.04});
   const ty=1.42+0.32+lst.length*0.26;
   s.addText(A.C,{x:rx,y:ty,w:rw,h:Math.max(0.5,6.9-ty),fontFace:F,fontSize:9,color:'374151',valign:'top'});
   s.addShape(pptx.ShapeType.line,{x:0.5,y:7.0,w:12.33,h:0,line:{color:'E5E7EB',width:0.75}});
   s.addText('KP Polio and Synergy dashboard \\u00b7 HRA \\u00b7 '
    +new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}),
    {x:0.5,y:7.05,w:12.3,h:0.3,fontFace:F,fontSize:9,color:'6B7280'});
   await saveDeck(pptx,hrvMapFile('.pptx'));toast('Slide downloaded');
  }catch(e){console.error(e);toast('Could not create the slide (needs internet for the PPTX library)');}
  b.disabled=!_HRVMAP;};
}
hrvMapWire();
"""

BTN = ('<button class="btn" id="btnHRVMpptx" title="One PowerPoint slide with this map and the ten '
       'worst districts on the measure shown">Slide (PPTX)</button>'
       '<button class="btn" id="btnHRVMjpg">JPG</button>'
       '<button class="btn" id="btnHRVMpng">PNG</button>')

EDITS = [
    ('buttons',
     '<button class="btn" id="btnHRVcsv" title="Division, district, council counts by band, '
     'High-Risk share, marks earned and the marks charged, one row per district">'
     'District roll-up (CSV)</button>',
     BTN + '<button class="btn" id="btnHRVcsv" title="Division, district, council counts by band, '
     'High-Risk share, marks earned and the marks charged, one row per district">'
     'District roll-up (CSV)</button>'),

    ('helpers',
     '// HRA AT A GLANCE (5/5): the district roll-up download behind the map card.',
     JS.replace('\n', '\r\n') + '// HRA AT A GLANCE (5/5): the district roll-up download behind the '
     'map card.'),

    ('no-geometry',
     "  box.innerHTML='<div class=\"empty\">District geometry not embedded in this file.</div>';\r\n"
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';return;}",
     "  box.innerHTML='<div class=\"empty\">District geometry not embedded in this file.</div>';\r\n"
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';\r\n"
     "  _HRVMAP=null;[el('btnHRVMjpg'),el('btnHRVMpng'),el('btnHRVMpptx')].forEach(function(b){if(b)b.disabled=true;});\r\n"
     "  return;}"),

    ('no-data',
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';",
     "  el('hrvMNote').textContent='';el('chrvMap').textContent='';el('hrvMap').innerHTML='';\r\n"
     "  _HRVMAP=null;[el('btnHRVMjpg'),el('btnHRVMpng'),el('btnHRVMpptx')].forEach(function(b){if(b)b.disabled=true;});"),

    ('map-state',
     "  +'shapefile and every label sits inside its own district.';}",
     "  +'shapefile and every label sits inside its own district.';\r\n"
     " const PM=X.per||{};\r\n"
     " _HRVMAP={mk:mk,\r\n"
     "  L:lg.concat([['#f1f5f9',X.scope?'not in the selected division / district'\r\n"
     "   :(X.pub?'no sheet':'no row this period')]]),\r\n"
     "  C:(el('chrvMap').textContent||''),\r\n"
     "  T:'KP district map \\u00b7 HRA '+(mk==='mean'?'district score':'High-Risk council share'),\r\n"
     "  S:(PM.lbl||'published reading')+(PM.pub?' \\u00b7 '+PM.date:'')\r\n"
     "   +' \\u00b7 '+(X.sdd?X.sdd:X.sdv?X.sdv+' division':'KP, all '+X.nd+' districts with a reading'),\r\n"
     "  base:('HRA_district_map_'+(mk==='mean'?'score':'highrisk')+'_'+(X.sdd||X.sdv||'KP')+'_'\r\n"
     "   +(X.pub?HRA.asof:(PM.slug||'compiled'))).replace(/[^A-Za-z0-9]+/g,'_')+'_'\r\n"
     "   +new Date().toISOString().slice(0,10),\r\n"
     "  rows:X.ann.filter(function(o){return o.n&&(mk==='mean'?o.p!=null:o.hi!=null);})\r\n"
     "   .sort(function(a,b){return mk==='mean'?(a.p-b.p):(b.hi-a.hi);}).slice(0,10)};\r\n"
     " [el('btnHRVMjpg'),el('btnHRVMpng'),el('btnHRVMpptx')].forEach(function(b){if(b)b.disabled=false;});}"),
]


def apply(t, edits):
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            raise SystemExit('anchor %r found %d times - the master no longer matches what this '
                             'patch was written against' % (name, n))
        t = t.replace(old, new)
    return t


def unapply(t, edits):
    for name, old, new in reversed(edits):
        n = t.count(new)
        if n != 1:
            raise SystemExit('reverse anchor %r found %d times - not undoing something this patch '
                             'did not write' % (name, n))
        t = t.replace(new, old)
    return t


def check(t):
    for once in ('id="btnHRVMjpg"', 'id="btnHRVMpng"', 'id="btnHRVMpptx"',
                 'function hrvMapShot()', 'function hrvMapImgURL(kind,plain)',
                 'function hrvMapWire()', 'hrvMapWire();', '_HRVMAP={mk:mk,'):
        if t.count(once) != 1:
            raise SystemExit('ERR the HRA map export patch is missing %r (%d copies)'
                             % (once, t.count(once)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    ap.add_argument('--check', action='store_true', help='apply in memory, report, write nothing')
    a = ap.parse_args()
    cfg, vs = dashpatch.load_variants()
    v = [x for x in vs if x.rel == MASTER]
    if len(v) != 1:
        raise SystemExit('expected exactly one %s in sources.json variants' % MASTER)
    v = v[0]
    built = 'id="btnHRVMjpg"' in v.text
    if a.unpatch:
        v.require(built, 'nothing to undo - the HRA map export patch is not applied')
        v.text = unapply(v.text, EDITS)
    else:
        v.require(not built, 'already applied (btnHRVMjpg present)')
        v.text = apply(v.text, EDITS)
        check(v.text)
    if not v.changed:
        print('NO CHANGE')
        return 0
    dashpatch.assert_crlf(v)
    print('%s %-42s %+8d chars  HRA map exports %s' % ('UNPATCH' if a.unpatch else 'PATCH', v.rel,
                                                      v.delta(),
                                                      'removed' if a.unpatch else 'added'))
    if a.check:
        print('CHECK ONLY - nothing written')
        return 0
    dashpatch.write_variants([v])
    print('WROTE %s (%s bytes)' % (v.path, format(os.path.getsize(v.path), ',')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
