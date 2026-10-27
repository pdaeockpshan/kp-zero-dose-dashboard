// HRA AT A GLANCE (3/4): district ring geometry and the bounded label placer.
// The same algorithm the EPI district map uses: each label stays inside its own ring, the largest
// districts claim their space first, two shrink steps, and a leader line when a label has to move.
function hrvRing(p){const n=(p.p.match(/-?[\d.]+/g)||[]).map(Number),r=[];
 let a=1e9,b=1e9,c=-1e9,d=-1e9;
 for(let k=0;k+1<n.length;k+=2){r.push([n[k],n[k+1]]);
  if(n[k]<a)a=n[k];if(n[k]>c)c=n[k];if(n[k+1]<b)b=n[k+1];if(n[k+1]>d)d=n[k+1];}
 r.bb=[a,b,c,d];return r;}
function hrvIn(x,y,r){let q=false;
 for(let i=0,j=r.length-1;i<r.length;j=i++){const a=r[j],b=r[i];
  if((a[1]>y)!==(b[1]>y))q=x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]?!q:q;}
 return q;}
function hrvBox(x,y,w,h,r){const a=w/2,b=h/2;
 return hrvIn(x,y,r)&&hrvIn(x-a,y-b,r)&&hrvIn(x+a,y-b,r)&&hrvIn(x-a,y+b,r)&&hrvIn(x+a,y+b,r);}
function hrvLab(){
 if(_HRVLAB)return _HRVLAB;
 const FU=KPGEO.vb[0]/540,FS=10.4*FU,CHW=0.62,LAD=[1,0.84,0.68];
 const R=KPGEO.d.map(hrvRing),placed=[],out=[];
 const clear=function(x,y,w,h){
  return !placed.some(function(b){return Math.abs(b[0]-x)<(b[2]+w)/2&&Math.abs(b[1]-y)<(b[3]+h)/2;});};
 const inb=function(x,y,w,h){
  return x-w/2>=-2*FU&&x+w/2<=KPGEO.vb[0]+2*FU&&y-h/2>=0&&y+h/2<=KPGEO.vb[1];};
 const find=function(p,r,w,h,full){const bb=r.bb;
  const ok=full?function(x,y){
    return x-w/2>=bb[0]&&x+w/2<=bb[2]&&y-h/2>=bb[1]&&y+h/2<=bb[3]&&hrvBox(x,y,w,h,r)&&clear(x,y,w,h);}
   :function(x,y){
    return x>=bb[0]&&x<=bb[2]&&y>=bb[1]&&y<=bb[3]&&hrvIn(x,y,r)&&clear(x,y,w,h);};
  if(inb(p.x,p.y,w,h)&&ok(p.x,p.y))return [p.x,p.y];
  for(let d=3*FU;d<=120*FU;d+=2*FU)for(let a=0;a<24;a++){
   const t=a*0.2618+d*0.02,x=p.x+Math.cos(t)*d,y=p.y+Math.sin(t)*d*0.82;
   if(inb(x,y,w,h)&&ok(x,y))return [x,y];}
  return null;};
 KPGEO.d.map(function(p,i){return {p:p,r:R[i]};})
  .filter(function(o){return o.p.x!=null&&o.p.y!=null;})
  .sort(function(m,n){return n.p.a-m.p.a;}).forEach(function(o){
   const p=o.p,r=o.r,nm=HRV_ABBR[p.c]||DNAME(p.c);
   const sz=function(k){const s=FS*LAD[k];return {s:s,w:nm.length*s*CHW+s*0.5,h:s*1.2};};
   let hit=null,g=sz(0),k;
   for(k=0;k<LAD.length&&!hit;k++){g=sz(k);hit=find(p,r,g.w,g.h,true);}
   for(k=0;k<LAD.length&&!hit;k++){g=sz(k);hit=find(p,r,g.w,g.h,false);}
   if(!hit){g=sz(1);hit=[p.x,p.y];}
   placed.push([hit[0],hit[1],g.w,g.h]);
   out.push({n:nm,x:hit[0],y:hit[1],fs:g.s,cx:p.x,cy:p.y,ld:Math.hypot(hit[0]-p.x,hit[1]-p.y)>55*FU});});
 _HRVLAB=out;return out;}
