function mdpNumV(v){
 if(typeof v==='number')return isFinite(v)?v:0;
 const s=String(v==null?'':v).replace(/[^0-9.\-]/g,'');const n=parseFloat(s);
 return isFinite(n)?n:0;
}
function mdpTimeV(v){
 if(v instanceof Date)return mdpPad(v.getHours())+':'+mdpPad(v.getMinutes());
 if(typeof v==='number'&&v>=0&&v<1){const m=Math.round(v*1440);return mdpPad(Math.floor(m/60)%24)+':'+mdpPad(m%60);}
 const s=String(v==null?'':v).trim();
 const m=/^(\d{1,2})[:.](\d{2})(?::\d{2})?\s*(AM|PM)?$/i.exec(s);
 if(!m)return '';
 let h=+m[1];const mi=+m[2],ap=(m[3]||'').toUpperCase();
 if(ap==='PM'&&h<12)h+=12;if(ap==='AM'&&h===12)h=0;
 if(h>23||mi>59)return '';
 return mdpPad(h)+':'+mdpPad(mi);
}
function mdpRsnCode(v){
 const u=String(v==null?'':v).toUpperCase();
 const m=/^\s*(SEC|NET|BOY|TRA|OTH)/.exec(u);if(m)return m[1];
 if(/SECURITY/.test(u))return 'SEC';
 if(/NETWORK|CONNECTIV|SIGNAL/.test(u))return 'NET';
 if(/BOYCOTT|REFUS/.test(u))return 'BOY';
 if(/TRANSPORT|ROAD|WEATHER|FLOOD/.test(u))return 'TRA';
 return u.trim()?'OTH':'';
}
