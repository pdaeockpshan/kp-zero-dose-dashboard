"""Route the morning-deployment Excel buttons through ExcelJS and fix the summary's total row.

Two defects found while checking the share buttons in the browser on 28-Oct-2026:

1. `csvDownload` only builds a real workbook when the file name matches XLP. The new MDP_ names
   did not, so the three "Excel" buttons wrote CSV bytes inside a .xlsx file (the district
   summary arrived as 2,128 bytes and no ExcelJS request was ever made). Adding MDP_ to XLP puts
   them on the same typed workbook route as the PTP / HRMP downloads - numeric columns,
   `0.0"%"` on the percent columns, a dash left as an empty cell.
2. The district summary's total row put a district count in the Division column and the
   reporting-district count under "Days reported". A total has to be labelled with the level it
   was summed at, so the row now reads "All divisions" and the day column carries the district-day
   total it actually adds up.
3. Exported chart images repeated the heading: the canvas drew one and Highcharts drew another from
   inside the SVG. Both Highcharts nodes are removed and the band they occupied is cropped off. The
   PPTX embeds a header-less copy, since its slide already carries the title, subtitle and caption.

Run: python _refresh/patch_mdp_xlsx.py   (master only, idempotent)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch

XLP_OLD = 'const XLP=/^(ptp_|hrmp_|nov26_focus_|hrd_|HRA UC Level)/;'
XLP_NEW = 'const XLP=/^(ptp_|hrmp_|nov26_focus_|hrd_|HRA UC Level|MDP_)/;'

TAB_OLD = " hrd_districts:'High-risk districts',hrd_union_councils:'HRA councils'};"
TAB_NEW = (" hrd_districts:'High-risk districts',hrd_union_councils:'HRA councils',\n"
           " MDP_division_roll_up:'Division roll-up',MDP_district_summary:'District summary',\n"
           " MDP_deployment_by_division:'Deployment by division',"
           "MDP_planned_vs_deployed_by_team_type:'Planned vs deployed',\n"
           " MDP_deployment_pace:'Pace and reports',MDP_teams_awaited_by_district:'Awaited by district',\n"
           " MDP_deployment_by_team_type:'Heatmap by team type'};")

SPEC_OLD = '''function mdpSmallSpec(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R);'''
SPEC_NEW = '''function mdpSmallSpec(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R),
  sR=R.reduce((a,o)=>a+(o.reps||0),0);'''

FOOT_OLD = '''  foot:['Campaign total',String(T.n)+' districts',String(T.rep)+' reported',nfmt(T.fd)+' / '+nfmt(T.fp),
   pfmt(T.pct),nfmt(T.ucr)+' / '+nfmt(T.ucp),T.good+' on plan'],'''
FOOT_NEW = '''  foot:['Campaign total','All divisions',String(sR),nfmt(T.fd)+' / '+nfmt(T.fp),
   pfmt(T.pct),nfmt(T.ucr)+' / '+nfmt(T.ucp),T.good+' of '+T.n+' on plan'],'''

XS_OLD = '''function mdpSmallXlsx(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R);'''
XS_NEW = '''function mdpSmallXlsx(){
 const R=mdpRows().slice().sort((a,b)=>(a.pct==null?999:a.pct)-(b.pct==null?999:b.pct)),T=mdpTot(R),
  sR=R.reduce((a,o)=>a+(o.reps||0),0);'''

XSROW_OLD = ''' rows.push(['Campaign total',T.n+' districts',T.rep,T.fp,T.fd,T.aw,
  T.pct==null?'':Math.round(T.pct*1000)/10,T.ucp,T.ucr,T.good+' on plan','','']);'''
XSROW_NEW = ''' rows.push(['Campaign total','All divisions',sR,T.fp,T.fd,T.aw,
  T.pct==null?'':Math.round(T.pct*10)/10,T.ucp,T.ucr,T.good+' of '+T.n+' districts on plan','','']);'''


STEM_OLD = "const xlStem=n=>String(n).replace(/\\.csv$/,'');"
STEM_NEW = "const xlStem=n=>String(n).replace(/\\.(csv|xlsx)$/,'');"

# mdpRows / mdpTot already carry a percent (0-100); the *1000/10 round came from the ratio
# columns beside them, where the input is a fraction. Applied to pct it wrote 8800 for 88.0%.
# the trailing comma keeps the match off the older district CSV, which writes a 0-1 share
# through Math.round(o.pct*10)/1000
PCT_O_OLD = "Math.round(o.pct*1000)/10,"
PCT_O_NEW = "Math.round(o.pct*10)/10,"
PCT_T_OLD = "Math.round(T.pct*1000)/10,"
PCT_T_NEW = "Math.round(T.pct*10)/10,"

# a district that has not reported has no typed plan, so its zero is an absence, not a count
FALSE_ZERO_OLD = "const rows=R.map(o=>[DNAME(o.n),o.dv,o.reps||0,o.fp,o.fd,o.rep?o.awTot:'',"
FALSE_ZERO_NEW = "const rows=R.map(o=>[DNAME(o.n),o.dv,o.reps||0,o.rep?o.fp:'',o.rep?o.fd:'',o.rep?o.awTot:'',"

DIVZERO_OLD = ''' const rows=gs.map(g=>[g.dv,g.n,g.rep,g.fp,g.fd,g.aw,
  g.fp?Math.round(g.fd/g.fp*1000)/10:'',g.ucp,g.ucr,g.inc]);'''
DIVZERO_NEW = ''' const rows=gs.map(g=>[g.dv,g.n,g.rep,g.rep?g.fp:'',g.rep?g.fd:'',g.rep?g.aw:'',
  g.rep&&g.fp?Math.round(g.fd/g.fp*1000)/10:'',g.ucp,g.ucr,g.inc]);'''

HEATZERO_OLD = ''' return [DNAME(o.n),o.dv].concat(pcs).concat([o.ucp?Math.round(o.ucr/o.ucp*1000)/10:'',
   o.pct==null?'':Math.round(o.pct*10)/10,o.fp,o.fd,MDP_ST[o.st][1]]);'''
HEATZERO_NEW = ''' return [DNAME(o.n),o.dv].concat(pcs).concat([o.rep&&o.ucp?Math.round(o.ucr/o.ucp*1000)/10:'',
   o.pct==null?'':Math.round(o.pct*10)/10,o.rep?o.fp:'',o.rep?o.fd:'',MDP_ST[o.st][1]]);'''

# the button says jpg, so the rasteriser has to be told jpeg - it was handed 'jpg' and fell through
# to the PNG branch, which wrote PNG bytes into a 114 KB .jpg that matched its .png twin byte for byte
JPG_OLD = ''' return kind==='jpeg'?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png');
}
function mdpChTable(id){'''
JPG_NEW = ''' return (kind==='jpeg'||kind==='jpg')?cv.toDataURL('image/jpeg',0.92):cv.toDataURL('image/png');
}
function mdpChTable(id){'''

# Each Highcharts chart draws its own title and subtitle inside the SVG, so a chart image carried the
# heading twice: once from the canvas header, once from Highcharts. Strip both nodes from the clone and
# crop the band they sat in. A "bare" image - the one the PPTX embeds - also drops the canvas header and
# caption, because the slide sets those words itself; otherwise the slide would show them a third time.
SIG_OLD = 'async function mdpChImg(id,kind){'
SIG_NEW = 'async function mdpChImg(id,kind,bare){'

IMGWH_OLD = 'let _MDPDLW=0;'
IMGWH_NEW = 'let _MDPDLW=0,MDP_IMGWH=null;'

CROP_OLD = ''' const cl=svg.cloneNode(true);
 cl.setAttribute('xmlns','http://www.w3.org/2000/svg');'''
CROP_NEW = ''' let tBot=0;
 try{['.highcharts-title','.highcharts-subtitle'].forEach(q=>{const n=svg.querySelector(q);
  if(n){const b=n.getBBox();tBot=Math.max(tBot,b.y+b.height);}});}catch(e){}
 const cl=svg.cloneNode(true);
 cl.querySelectorAll('.highcharts-title,.highcharts-subtitle').forEach(n=>n.remove());
 cl.setAttribute('xmlns','http://www.w3.org/2000/svg');'''

GEO_OLD = ''' const W=Math.max(560,Math.round(c.chartWidth||900)),CH0=Math.max(240,Math.round(c.chartHeight||400));
 const S=2,TB=76;
 const m=document.createElement('canvas').getContext('2d');
 m.font='11.5px "Segoe UI",Arial,sans-serif';
 const cap=mdpChCap(id),cL=cap?mdpWrapText(m,cap,W-28).slice(0,4):[];
 const CB=cL.length?cL.length*16+8:0;
 const H=TB+CH0+CB+10;'''
GEO_NEW = ''' const W=Math.max(560,Math.round(c.chartWidth||900)),CH0=Math.max(240,Math.round(c.chartHeight||400));
 const vb=cl.viewBox&&cl.viewBox.baseVal;
 const srcW=Math.round(vb&&vb.width>40?vb.width:W),srcH=Math.round(vb&&vb.height>40?vb.height:CH0);
 const crop=Math.max(0,Math.min(Math.round(tBot)+4,srcH-160)),sh=Math.max(120,srcH-crop);
 const dh=Math.round(sh*W/srcW);
 const S=2,TB=bare?0:76;
 const m=document.createElement('canvas').getContext('2d');
 m.font='11.5px "Segoe UI",Arial,sans-serif';
 const cap=bare?'':mdpChCap(id),cL=cap?mdpWrapText(m,cap,W-28).slice(0,4):[];
 const CB=cL.length?cL.length*16+8:0;
 const H=TB+dh+CB+10;
 MDP_IMGWH={w:W,h:H};'''

DRAW_OLD = r''' x.fillStyle='#ffffff';x.fillRect(0,0,W,H);
 x.fillStyle='#0f172a';x.font='bold 19px "Segoe UI",Arial,sans-serif';
 x.fillText(mdpChTitle(id),14,26);
 x.fillStyle='#475569';x.font='12.5px "Segoe UI",Arial,sans-serif';
 x.fillText(mdpChSub(id)+' \u00b7 '+mdpLiveWhen(),14,47);
 x.drawImage(img,0,TB,W,CH0);
 if(cL.length){x.fillStyle='#64748b';x.font='11.5px "Segoe UI",Arial,sans-serif';
  cL.forEach((l,i)=>x.fillText(l,14,TB+CH0+22+i*16));}'''
DRAW_NEW = r''' x.fillStyle='#ffffff';x.fillRect(0,0,W,H);
 if(!bare){x.fillStyle='#0f172a';x.font='bold 19px "Segoe UI",Arial,sans-serif';
  x.fillText(mdpChTitle(id),14,26);
  x.fillStyle='#475569';x.font='12.5px "Segoe UI",Arial,sans-serif';
  x.fillText(mdpChSub(id)+' \u00b7 '+mdpLiveWhen(),14,47);}
 x.drawImage(img,0,crop,srcW,sh,0,TB,W,dh);
 if(cL.length){x.fillStyle='#64748b';x.font='11.5px "Segoe UI",Arial,sans-serif';
  cL.forEach((l,i)=>x.fillText(l,14,TB+dh+22+i*16));}'''

PPURL_OLD = " const url=await mdpChImg(id,'png');"
PPURL_NEW = " const url=await mdpChImg(id,'png',true);"

PPGEO_OLD = ' const W=Math.max(560,Math.round(c.chartWidth||900)),H=Math.max(240,Math.round(c.chartHeight||400))+76;'
PPGEO_NEW = ' const D=MDP_IMGWH||{w:Math.max(560,Math.round(c.chartWidth||900)),h:Math.max(240,Math.round(c.chartHeight||400))},W=D.w,H=D.h;'


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def main():
    cfg, vs = dashpatch.load_variants()
    v = next(x for x in vs if x.rel == 'index.html')
    edits = [
        (XLP_OLD, XLP_NEW, 'Excel routing for the MDP downloads', 1),
        (STEM_OLD, STEM_NEW, 'stop doubling the .xlsx extension', 1),
        (TAB_OLD, TAB_NEW, 'sheet tab names', 1),
        (SPEC_OLD, SPEC_NEW, 'summary image total row', 1),
        (FOOT_OLD, FOOT_NEW, 'summary image total row labels', 1),
        (XS_OLD, XS_NEW, 'summary sheet total row', 1),
        (XSROW_OLD, XSROW_NEW, 'summary sheet total row labels', 1),
        (PCT_O_OLD, PCT_O_NEW, 'district percent scaled once', 2),
        (PCT_T_OLD, PCT_T_NEW, 'total percent scaled once', 2),
        (FALSE_ZERO_OLD, FALSE_ZERO_NEW, 'blank instead of a false zero plan', 1),
        (DIVZERO_OLD, DIVZERO_NEW, 'division totals left blank with no report', 1),
        (HEATZERO_OLD, HEATZERO_NEW, 'heatmap sheet leaves unreported cells blank', 1),
        (JPG_OLD, JPG_NEW, 'chart JPG really is a JPEG', 1),
        (SIG_OLD, SIG_NEW, 'chart image can be drawn without the share header', 1),
        (IMGWH_OLD, IMGWH_NEW, 'remember the raster size for the slide', 1),
        (CROP_OLD, CROP_NEW, 'drop the Highcharts heading before rasterising', 1),
        (GEO_OLD, GEO_NEW, 'crop the heading band and size the canvas to it', 1),
        (DRAW_OLD, DRAW_NEW, 'draw the cropped chart and keep the caption under it', 1),
        (PPURL_OLD, PPURL_NEW, 'slide embeds the header-less chart image', 1),
        (PPGEO_OLD, PPGEO_NEW, 'slide image keeps the chart aspect', 1),
    ]
    todo = []
    for old, new, label, expect in edits:
        o, n = crlf(old), crlf(new)
        c = v.text.count(o)
        if c == 0 and v.text.count(n) == expect:
            continue
        if c != expect:
            raise SystemExit('ABORT: %d matches for %s, expected %d' % (c, label, expect))
        todo.append((o, n, label))
    if not todo:
        print('nothing to do')
        return
    for o, n, label in todo:
        v.text = v.text.replace(o, n)
        v.changes.append('Morning deployment share: %s' % label)
    dashpatch.assert_crlf(v)
    dashpatch.write_variants([v])
    print('PATCHED index.html %+d chars (%d edit(s))' % (v.delta(), len(todo)))


if __name__ == '__main__':
    main()
