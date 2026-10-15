"""Self-contained animated widgets (HTML5 canvas) embedded in Streamlit.

Each function returns an HTML string; render with
    streamlit.components.v1.html(html, height=...)
No external libraries / CDN needed, so everything works offline.
"""
import json

HEAD = """<!doctype html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box}
html,body{margin:0;background:transparent;font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;color:#e8eef8;overflow:hidden}
.wrap{border:1px solid rgba(148,163,184,.18);border-radius:18px;background:linear-gradient(180deg,rgba(14,22,40,.92),rgba(8,13,24,.95));padding:10px 12px 12px}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px;font-size:12px;color:#9fb0c7}
.bar b{color:#e8eef8}
.sp{flex:1}
button,select{background:rgba(57,217,209,.10);color:#eafcfb;border:1px solid rgba(57,217,209,.30);border-radius:9px;padding:5px 11px;font-weight:600;font-size:12px;font-family:inherit;cursor:pointer}
button:hover{border-color:#39d9d1}
button.on{background:rgba(57,217,209,.32)}
input[type=range]{accent-color:#39d9d1;vertical-align:middle}
canvas{display:block;width:100%}
</style></head><body><div class="wrap">"""

TAIL = "</div></body></html>"

COMMON_JS = """
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const lerp=(a,b,t)=>a+(b-a)*t;
function setup(cv,h){const dpr=window.devicePixelRatio||1;const w=Math.max(520,Math.floor(cv.parentElement.clientWidth));
 cv.width=w*dpr;cv.height=h*dpr;cv.style.height=h+'px';const ctx=cv.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);return {ctx:ctx,w:w,h:h};}
function rr(ctx,x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function gauss(r){let u=0;while(u===0)u=r();const v=r();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v)}
function hash(x){const s=Math.sin(x*12.9898+78.233)*43758.5453;return (s-Math.floor(s))*2-1}
function mix(c1,c2,t){t=clamp(t,0,1);return 'rgb('+Math.round(lerp(c1[0],c2[0],t))+','+Math.round(lerp(c1[1],c2[1],t))+','+Math.round(lerp(c1[2],c2[2],t))+')'}
function txt(ctx,s,x,y,col,size,align,weight){ctx.fillStyle=col||'#9fb0c7';ctx.font=(weight||500)+' '+(size||11)+'px Inter,Arial,sans-serif';ctx.textAlign=align||'left';ctx.fillText(s,x,y);}
"""


def _build(body, js, params):
    return HEAD + body + "<script>" + COMMON_JS + js.replace("__PARAMS__", json.dumps(params)) + "</script>" + TAIL


# =============================================================================
# 02  DAMAGE BEING SENSED
# =============================================================================
SENSE_BODY = """
<div class="bar"><b>Live damage-sensing demo</b><span id="cls"></span><span class="sp"></span>
Speed <select id="spd"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select>
<button id="rep">&#8635; Replay</button></div>
<canvas id="c"></canvas>
"""

SENSE_JS = r"""
const P=__PARAMS__;
const SEV={"Healthy":0,"Matrix Crack":.45,"Delamination":.75,"Fibre Break":1};
const NAMES={"Healthy":"No damage","Matrix Crack":"Matrix crack","Delamination":"Delamination","Fibre Break":"Fibre break"};
const cv=document.getElementById('c');let S,plate,sensors,site,crack,ell,bg,pulses=[],sigma,thr;
const T=10,V=330,GROW0=1.5,GROWT=3.0;
let start=performance.now(),speed=1,detT=null,lvl=0,prevTT=0;
document.getElementById('cls').textContent='Class: '+P.cls+'  |  load '+P.load+'  |  shots '+P.shots;
document.getElementById('spd').onchange=e=>{speed=parseFloat(e.target.value)};
document.getElementById('rep').onclick=()=>{start=performance.now();detT=null;lvl=0;};
function pointAt(g){
  if(crack){const n=crack.length-1;const f=clamp(g,0,1)*n;const i=Math.min(n-1,Math.floor(f));const u=f-i;return {x:lerp(crack[i].x,crack[i+1].x,u),y:lerp(crack[i].y,crack[i+1].y,u)};}
  if(ell){const a=g*6.283*1.5;return {x:ell.x+Math.cos(a)*ell.rx*Math.min(1,.3+g),y:ell.y+Math.sin(a)*ell.ry*Math.min(1,.3+g)};}
  return {x:site.x,y:site.y};
}
function build(){
  S=setup(cv,480);const W=S.w;
  plate={x:16,y:46,w:Math.floor(W*.56),h:340};
  const px=plate.x,py=plate.y,pw=plate.w,ph=plate.h;
  sensors=[[.08,.14],[.92,.14],[.08,.86],[.92,.86]].map((q,i)=>({x:px+q[0]*pw,y:py+q[1]*ph,n:'S'+(i+1)}));
  site={x:px+.46*pw,y:py+.55*ph};
  const sev=SEV[P.cls];crack=null;ell=null;
  const r=mulberry(11);
  if(P.cls==='Matrix Crack'){const L=.17*pw,a=-.55;crack=[];for(let i=0;i<=8;i++){const u=i/8-.5;crack.push({x:site.x+Math.cos(a)*L*u+(r()-.5)*7,y:site.y+Math.sin(a)*L*u+(r()-.5)*7});}}
  if(P.cls==='Fibre Break'){const L=.62*ph;crack=[];for(let i=0;i<=14;i++){const u=i/14-.5;crack.push({x:site.x+u*.12*L+(r()-.5)*16,y:site.y+u*L});}}
  if(P.cls==='Delamination'){ell={x:site.x,y:site.y,rx:.21*pw,ry:.1*ph};}
  sigma=.04+.5/Math.sqrt(P.shots);thr=4*sigma;
  pulses=[];
  if(sev>0){for(let i=0;i<7;i++){const te=GROW0+i*.45;const o=pointAt(i/6);
    const p={te:te,ox:o.x,oy:o.y,ta:[],A:[]};
    sensors.forEach(s=>{const d=Math.hypot(s.x-o.x,s.y-o.y);p.ta.push(te+d/V);p.A.push(2.2*sev*Math.exp(-d/420));});
    pulses.push(p);}}
  bg=document.createElement('canvas');bg.width=pw;bg.height=ph;const b=bg.getContext('2d');
  const g=b.createLinearGradient(0,0,pw,ph);g.addColorStop(0,'#142036');g.addColorStop(1,'#0c1424');b.fillStyle=g;b.fillRect(0,0,pw,ph);
  b.lineWidth=2;for(let k=-ph;k<pw;k+=9){b.strokeStyle='rgba(130,150,185,.11)';b.beginPath();b.moveTo(k,0);b.lineTo(k+ph,ph);b.stroke();
    b.strokeStyle='rgba(130,150,185,.07)';b.beginPath();b.moveTo(k+ph,0);b.lineTo(k,ph);b.stroke();}
}
function sample(j,u){let v=0;for(const p of pulses){const ta=p.ta[j];if(u>ta){const d=u-ta;v+=p.A[j]*Math.exp(-d*5)*Math.sin(6.283*14*d);}}return v+sigma*1.7*hash(u*997+j*13.7);}
function env(j,t){let v=0;for(const p of pulses){const ta=p.ta[j];if(t>ta)v+=p.A[j]*Math.exp(-(t-ta)*5);}return v;}
function frame(now){
  const W=S.w,ctx=S.ctx;ctx.clearRect(0,0,W,S.h);
  let tt=((now-start)/1000*speed);tt=tt%T;
  if(tt<prevTT){detT=null;lvl=0;}prevTT=tt;
  const px=plate.x,py=plate.y,pw=plate.w,ph=plate.h;
  const sev=SEV[P.cls];
  // title row
  txt(ctx,'CFRP panel (top view)',px,py-14,'#9fb0c7',11,'left',700);
  // plate
  ctx.save();rr(ctx,px,py,pw,ph,14);ctx.clip();ctx.drawImage(bg,px,py);
  // load arrows + tint
  const lf=clamp(tt/GROW0,0,1)*(P.load/100);
  ctx.fillStyle='rgba(255,184,107,'+(.05+.18*lf*(sev>0?1:.3))+')';ctx.fillRect(px,py,pw,ph);
  // delamination region
  const g=clamp((tt-GROW0)/GROWT,0,1);
  if(ell){const k=Math.min(1,.15+.85*g);ctx.save();ctx.translate(ell.x,ell.y);ctx.scale(ell.rx*k,ell.ry*k);ctx.beginPath();ctx.arc(0,0,1,0,6.283);ctx.restore();
    ctx.fillStyle='rgba(255,120,90,'+(.22*g+.05)+')';ctx.fill();ctx.strokeStyle='rgba(255,140,100,.9)';ctx.setLineDash([6,4]);ctx.lineWidth=2;ctx.stroke();ctx.setLineDash([]);
    for(let i=-2;i<=2;i++){ctx.strokeStyle='rgba(255,170,130,'+(.4*g)+')';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(ell.x-ell.rx*k*.8,ell.y+i*6);ctx.lineTo(ell.x+ell.rx*k*.8,ell.y+i*6);ctx.stroke();}}
  // cracks
  if(crack&&g>0){const n=crack.length-1;const f=g*n;ctx.lineJoin='round';
    for(const pass of [[10,'rgba(255,80,80,.18)'],[2.6,'#ff5a5a']]){ctx.lineWidth=pass[0];ctx.strokeStyle=pass[1];ctx.beginPath();ctx.moveTo(crack[0].x,crack[0].y);
      for(let i=1;i<=n;i++){if(i<=f)ctx.lineTo(crack[i].x,crack[i].y);else{const u=f-(i-1);if(u>0){ctx.lineTo(lerp(crack[i-1].x,crack[i].x,u),lerp(crack[i-1].y,crack[i].y,u));}break;}}ctx.stroke();}
    const tip=pointAt(g);ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(tip.x,tip.y,3.5,0,6.283);ctx.fill();}
  // acoustic wavefronts
  for(const p of pulses){const r=(tt-p.te)*V;if(r>0&&r<pw*1.1){const a=clamp(1-r/(pw*.95),0,1)*.75;
    ctx.strokeStyle='rgba(57,217,209,'+a+')';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.ox,p.oy,r,0,6.283);ctx.stroke();}}
  // sensors
  let maxEnv=0;
  sensors.forEach((s,j)=>{const e=env(j,tt);maxEnv=Math.max(maxEnv,e);const on=e>thr;
    if(on){ctx.fillStyle='rgba(255,184,107,'+clamp(e/(thr*4),.15,.5)+')';ctx.beginPath();ctx.arc(s.x,s.y,26,0,6.283);ctx.fill();}
    ctx.fillStyle=on?'#ffb86b':'#5ee7a5';ctx.beginPath();ctx.arc(s.x,s.y,8,0,6.283);ctx.fill();
    ctx.strokeStyle='#0b1220';ctx.lineWidth=2;ctx.stroke();
    txt(ctx,s.n,s.x,s.y+(s.y<py+ph/2?24:-14),'#cfe0f5',10,'center',700);});
  ctx.restore();
  rr(ctx,px,py,pw,ph,14);ctx.strokeStyle='rgba(148,163,184,.3)';ctx.lineWidth=1.2;ctx.stroke();
  // detection
  const D=maxEnv/thr;
  if(detT===null&&D>1&&sev>0)detT=tt;
  lvl=Math.max(lvl,clamp(maxEnv/(thr*3),0,1));
  if(detT!==null){
    const q=clamp((tt-detT)/1.2,0,1),err=12+sigma*260;
    const lx=site.x+hash(7.1)*err*.3,ly=site.y+hash(3.3)*err*.3;
    ctx.strokeStyle='rgba(255,90,90,'+(.9)+')';ctx.lineWidth=1.6;ctx.beginPath();ctx.arc(lx,ly,err*(2-q)+4,0,6.283);ctx.stroke();
    ctx.beginPath();ctx.moveTo(lx-14,ly);ctx.lineTo(lx+14,ly);ctx.moveTo(lx,ly-14);ctx.lineTo(lx,ly+14);ctx.stroke();
    txt(ctx,'localised \u00b1'+Math.round(err/6)+' mm',lx+16,ly-12,'#ffb3b3',10.5,'left',700);}
  // load bar + meter (below plate)
  const by=py+ph+16;
  txt(ctx,'Applied load',px,by+10,'#9fb0c7',10.5,'left',600);
  ctx.fillStyle='rgba(148,163,184,.15)';rr(ctx,px+82,by,pw-82,12,6);ctx.fill();
  ctx.fillStyle='#ffb86b';rr(ctx,px+82,by,Math.max(8,(pw-82)*lf),12,6);ctx.fill();
  txt(ctx,'Damage sensed',px,by+36,'#9fb0c7',10.5,'left',600);
  ctx.fillStyle='rgba(148,163,184,.15)';rr(ctx,px+82,by+26,pw-82,12,6);ctx.fill();
  const mc=lvl>.33?mix([255,184,107],[255,80,80],(lvl-.33)/.6):mix([94,231,165],[255,184,107],lvl/.33);
  ctx.fillStyle=mc;rr(ctx,px+82,by+26,Math.max(8,(pw-82)*lvl),12,6);ctx.fill();
  // banner
  const bx=px+pw+24,bw=W-bx-16;
  let bt='\u25CF MONITORING \u2013 acoustic sensors listening',bc='94,231,165';
  if(sev===0&&tt>GROW0){bt='\u2713 STRUCTURE HEALTHY \u2013 no anomaly';}
  if(detT!==null){bt='\u26A0 DAMAGE SENSED \u2013 '+NAMES[P.cls]+'  (t = '+detT.toFixed(1)+' s)';bc='255,90,90';}
  else if(sev>0&&tt>GROW0+GROWT+2.2){bt='\u26A0 Below detection threshold \u2013 raise shots';bc='255,184,107';}
  ctx.fillStyle='rgba('+bc+',.12)';rr(ctx,bx,py-30,bw,26,9);ctx.fill();ctx.strokeStyle='rgba('+bc+',.5)';ctx.lineWidth=1;ctx.stroke();
  txt(ctx,bt,bx+10,py-13,'rgb('+bc+')',11.5,'left',700);
  // traces
  const th=(ph-6)/4,tw=bw-30,tx=bx+30;
  sensors.forEach((s,j)=>{
    const ty=py+j*th+3;ctx.fillStyle='rgba(10,16,28,.8)';rr(ctx,bx,ty,bw,th-6,8);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.14)';ctx.stroke();
    txt(ctx,s.n,bx+8,ty+(th-6)/2+4,'#cfe0f5',10.5,'left',700);
    const cy=ty+(th-6)/2,amp=(th-6)/2-4;const sc=amp/1.3;
    ctx.strokeStyle='rgba(255,184,107,.45)';ctx.setLineDash([4,3]);ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(tx,cy-thr*sc);ctx.lineTo(tx+tw,cy-thr*sc);ctx.moveTo(tx,cy+thr*sc);ctx.lineTo(tx+tw,cy+thr*sc);ctx.stroke();ctx.setLineDash([]);
    ctx.strokeStyle='#39d9d1';ctx.lineWidth=1.3;ctx.beginPath();
    const win=3;for(let x=0;x<=tw;x+=1.5){const u=tt-win+win*x/tw;if(u<0){ctx.moveTo(tx+x+1.5,cy);continue;}
      const v=clamp(sample(j,u),-1.3,1.3);ctx.lineTo(tx+x,cy-v*sc);}
    ctx.stroke();
  });
  txt(ctx,'dashed = detection threshold (4\u03c3 noise)',bx,py+ph+14,'#6f819b',10,'left',500);
  txt(ctx,'Noise \u03c3 = '+sigma.toFixed(3)+'  (more shots \u2192 less noise)',bx,py+ph+30,'#6f819b',10,'left',500);
  requestAnimationFrame(frame);
}
build();requestAnimationFrame(frame);
window.addEventListener('resize',()=>{build();});
"""


def sensing_html(cls="Matrix Crack", load=50, shots=512):
    return _build(SENSE_BODY, SENSE_JS, {"cls": cls, "load": int(load), "shots": int(shots)})


# =============================================================================
# 03  SIGNAL BEING DETECTED
# =============================================================================
SIGNAL_BODY = """
<div class="bar"><b>Live signal-detection demo</b><span id="info"></span><span class="sp"></span>
Speed <select id="spd"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select>
<button id="rep">&#8635; Restart</button></div>
<canvas id="c"></canvas>
"""

SIGNAL_JS = r"""
const P=__PARAMS__;
const cv=document.getElementById('c');let S;
const FS=512,N=256,CYC=10,ON=3.5,NB=66;
let speed=1,ts=0,buf=[],last=performance.now(),frameNo=0,total=0;
let mags=new Array(NB).fill(0),thr=1,floor=0,band=0,score=0,hist=[],baseBand=0,detS=null,hits=0,detFreq=null;
const cosT=[],sinT=[],win=[];
for(let n=0;n<N;n++)win.push(.5-.5*Math.cos(6.283*n/(N-1)));
for(let k=0;k<NB;k++){cosT.push([]);sinT.push([]);for(let n=0;n<N;n++){cosT[k].push(Math.cos(6.283*k*n/N));sinT[k].push(Math.sin(6.283*k*n/N));}}
document.getElementById('info').textContent='Base '+P.base+' Hz | damage '+P.dmg+' Hz | amp '+P.amp+' | noise '+P.noise;
document.getElementById('spd').onchange=e=>{speed=parseFloat(e.target.value)};
function gen(t){
  const ph=t%CYC;let d=0;
  if(ph>ON){const ramp=clamp((ph-ON)/.3,0,1);d=P.amp*ramp*Math.exp(-(ph-ON)/3)*Math.sin(6.283*P.dmg*t);}
  return 2.5*Math.sin(6.283*P.base*t)+1.1*Math.sin(6.283*(P.base+16)*t)+d+P.noise*gauss(Math.random);
}
function reset(){ts=0;buf=[];total=0;for(let i=0;i<N*2;i++){buf.push(gen(ts));ts+=1/FS;total++;}baseBand=0;hist=[];detS=null;hits=0;detFreq=null;}
document.getElementById('rep').onclick=reset;
function build(){S=setup(cv,480);}
function analyse(){
  const seg=buf.slice(buf.length-N);const df=FS/N;
  for(let k=0;k<NB;k++){let re=0,im=0;for(let n=0;n<N;n++){const v=seg[n]*win[n];re+=v*cosT[k][n];im-=v*sinT[k][n];}mags[k]=Math.sqrt(re*re+im*im)/Math.sqrt(N);}
  const kd=Math.round(P.dmg/df);let b=0;for(let k=Math.max(1,kd-2);k<=Math.min(NB-1,kd+2);k++)b=Math.max(b,mags[k]);
  const skip=[Math.round(P.base/df),Math.round((P.base+16)/df)];let s=0,c=0;
  for(let k=3;k<NB;k++){if(Math.abs(k-kd)<=4)continue;if(Math.abs(k-skip[0])<=4||Math.abs(k-skip[1])<=4)continue;s+=mags[k];c++;}
  floor=c?s/c:0;band=b;
  const ph=ts%CYC;
  if(ph<ON-.2)baseBand=Math.max(baseBand,b);
  thr=Math.max(.35,5*floor,1.5*baseBand);score=band/thr;
  hist.push(score);if(hist.length>260)hist.shift();
  if(ph>ON&&score>1){hits++;if(hits>=2&&detS===null){detS=total-1;detFreq=P.dmg;detAbs=ts;}}else if(score<=1)hits=0;
}
let detAbs=0,prevPh=0;
function frame(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;
  const ns=Math.round(FS*dt*speed);
  for(let i=0;i<ns;i++){buf.push(gen(ts));ts+=1/FS;total++;}
  if(buf.length>FS*2)buf.splice(0,buf.length-FS*2);
  const ph=ts%CYC;if(ph<prevPh){detS=null;hits=0;hist=hist.slice(-40);}prevPh=ph;
  frameNo++;if(frameNo%3===0)analyse();
  const ctx=S.ctx,W=S.w;ctx.clearRect(0,0,W,S.h);
  // waveform panel
  const wx=16,wy=34,ww=W-32,wh=150;
  txt(ctx,'Time-domain sensor waveform (last 1 s)',wx,wy-10,'#9fb0c7',11,'left',700);
  ctx.fillStyle='rgba(10,16,28,.8)';rr(ctx,wx,wy,ww,wh,10);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.16)';ctx.stroke();
  ctx.strokeStyle='rgba(148,163,184,.12)';ctx.beginPath();ctx.moveTo(wx,wy+wh/2);ctx.lineTo(wx+ww,wy+wh/2);ctx.stroke();
  const active=(ts%CYC)>ON&&(ts%CYC)<ON+4;
  const sc=(wh/2-8)/9;
  ctx.strokeStyle=detS!==null?'#ffb86b':'#39d9d1';ctx.lineWidth=1.3;ctx.beginPath();
  const L=buf.length;for(let x=0;x<=ww;x+=1){const i=Math.floor(x/ww*(L-1));const v=clamp(buf[i],-9,9);if(x===0)ctx.moveTo(wx+x,wy+wh/2-v*sc);else ctx.lineTo(wx+x,wy+wh/2-v*sc);}ctx.stroke();
  const di=detS===null?-1:detS-(total-L);
  if(detS!==null&&di>=0&&di<L){const x=wx+di/(L-1)*ww;ctx.strokeStyle='#ff5a5a';ctx.setLineDash([5,4]);ctx.lineWidth=1.6;ctx.beginPath();ctx.moveTo(x,wy);ctx.lineTo(x,wy+wh);ctx.stroke();ctx.setLineDash([]);
    txt(ctx,'detected',Math.min(x+6,wx+ww-52),wy+14,'#ff9d9d',10.5,'left',700);}
  // status banner
  const det=(score>1&&(ts%CYC)>ON);
  let bt='\u25CF LISTENING \u2013 no damage signature',bc='94,231,165';
  if(detS!==null||det){bt='\u26A0 DAMAGE SIGNAL DETECTED at '+P.dmg+' Hz  (score '+score.toFixed(1)+'\u00d7 threshold)';bc='255,90,90';}
  else if((ts%CYC)>ON+.3&&P.amp<.4){bt='\u26A0 Signal too weak to detect';bc='255,184,107';}
  ctx.fillStyle='rgba('+bc+',.12)';rr(ctx,W-16-410,wy-30,410,24,9);ctx.fill();ctx.strokeStyle='rgba('+bc+',.5)';ctx.stroke();
  txt(ctx,bt,W-16-400,wy-13,'rgb('+bc+')',11,'left',700);
  // spectrum panel
  const sx=16,sy=222,sw=Math.floor(W*.60)-16,sh=210;
  txt(ctx,'Live frequency spectrum (QFT / FFT of last 0.5 s)',sx,sy-12,'#9fb0c7',11,'left',700);
  ctx.fillStyle='rgba(10,16,28,.8)';rr(ctx,sx,sy,sw,sh,10);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.16)';ctx.stroke();
  const df=FS/N,fmax=(NB-1)*df;let ymax=Math.max(14,thr*1.4);for(let k=0;k<NB;k++)ymax=Math.max(ymax,mags[k]*1.1);
  const bw=(sw-20)/NB,kd=Math.round(P.dmg/df);
  for(let k=1;k<NB;k++){const h=mags[k]/ymax*(sh-34);const isD=Math.abs(k-kd)<=2;const isB=Math.abs(k-Math.round(P.base/df))<=1||Math.abs(k-Math.round((P.base+16)/df))<=1;
    ctx.fillStyle=isD?(score>1?'#ff5a5a':'#9b7cff'):(isB?'#39d9d1':'rgba(143,160,184,.55)');ctx.fillRect(sx+10+k*bw,sy+sh-22-h,Math.max(1.5,bw-1),h);}
  const ty=sy+sh-22-thr/ymax*(sh-34);
  ctx.strokeStyle='#ffb86b';ctx.setLineDash([6,4]);ctx.lineWidth=1.3;ctx.beginPath();ctx.moveTo(sx+10,ty);ctx.lineTo(sx+sw-10,ty);ctx.stroke();ctx.setLineDash([]);
  txt(ctx,'adaptive threshold',sx+sw-14,ty-5,'#ffb86b',10,'right',600);
  for(let f=0;f<=120;f+=20){txt(ctx,f+'',sx+10+(f/df)*bw,sy+sh-6,'#6f819b',10,'center',500);}
  txt(ctx,'Hz',sx+sw-14,sy+sh-6,'#6f819b',10,'right',600);
  txt(ctx,'healthy peaks',sx+14,sy+16,'#39d9d1',10.5,'left',600);
  txt(ctx,'damage band',sx+100,sy+16,score>1?'#ff5a5a':'#9b7cff',10.5,'left',600);
  // score timeline
  const cx=sx+sw+18,cw=W-cx-16;
  txt(ctx,'Detection score vs time',cx,sy-12,'#9fb0c7',11,'left',700);
  ctx.fillStyle='rgba(10,16,28,.8)';rr(ctx,cx,sy,cw,sh,10);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.16)';ctx.stroke();
  const smax=Math.max(3,...hist);const y1=sy+sh-24-(1/smax)*(sh-44);
  ctx.strokeStyle='#ffb86b';ctx.setLineDash([6,4]);ctx.beginPath();ctx.moveTo(cx+8,y1);ctx.lineTo(cx+cw-8,y1);ctx.stroke();ctx.setLineDash([]);
  txt(ctx,'score = 1',cx+cw-12,y1-5,'#ffb86b',10,'right',600);
  ctx.strokeStyle=score>1?'#ff5a5a':'#5ee7a5';ctx.lineWidth=1.8;ctx.beginPath();
  hist.forEach((v,i)=>{const x=cx+8+i/259*(cw-16),y=sy+sh-24-(v/smax)*(sh-44);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);});ctx.stroke();
  txt(ctx,'score '+score.toFixed(2),cx+12,sy+sh-8,'#cfe0f5',11,'left',700);
  txt(ctx,'floor '+floor.toFixed(2),cx+cw-12,sy+sh-8,'#6f819b',10.5,'right',500);
  const cyc=ts%CYC;
  txt(ctx,'cycle '+cyc.toFixed(1)+' s  |  damage event starts at '+ON.toFixed(1)+' s',16,S.h-6,'#6f819b',10.5,'left',500);
  requestAnimationFrame(frame);
}
build();reset();requestAnimationFrame(frame);
window.addEventListener('resize',build);
"""


def signal_html(base_freq=18, damage_freq=72, amp=1.8, noise=0.65):
    return _build(SIGNAL_BODY, SIGNAL_JS, {"base": base_freq, "dmg": damage_freq, "amp": amp, "noise": noise})


# =============================================================================
# 04  POLYMER / CFRP BREAKAGE
# =============================================================================
BREAK_BODY = """
<div class="bar"><b>Polymer network breakage</b><span class="sp"></span>
<span id="chips"></span>
Speed <select id="spd"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select>
<button id="rep">&#8635; Replay</button></div>
<canvas id="c"></canvas>
"""

BREAK_CORE = r"""
//CORE_START
const NC=20,NR=9;
const CFG={
 "Healthy":     {ex:.05,et:0,  shear:0,   fib:[9,9],  mat:[9,9],  note:'Elastic only \u2013 no bond breaks'},
 "Matrix Crack":{ex:.02,et:.085,shear:0,  fib:[9,9],  mat:[.085,.16],note:'Resin chains between fibre layers snap'},
 "Delamination":{ex:.01,et:.05,shear:.05, fib:[9,9],  mat:[.20,.30], iface:[.030,.06],note:'Interface between plies peels apart'},
 "Fibre Break": {ex:.075,et:0, shear:0,   fib:[.058,.085],mat:[.30,.40],note:'Carbon fibres rupture, ends recoil'}
};
function makeSim(cls,pw,ph,seed){
  const cfg=CFG[cls],rnd=mulberry(seed||5);
  const dx=(pw-120)/(NC-1),dy=(ph-50)/(NR-1);
  const nodes=[];for(let j=0;j<NR;j++)for(let i=0;i<NC;i++){const x=30+i*dx,y=25+j*dy;nodes.push({i:i,j:j,x0:x,y0:y,x:x,y:y});}
  const id=(i,j)=>j*NC+i;
  const sp=[];
  function add(a,b,type,k,thr){const A=nodes[a],B=nodes[b];sp.push({a:a,b:b,type:type,k:k,L0:Math.hypot(A.x0-B.x0,A.y0-B.y0),thr:thr,alive:true,st:0});}
  const mid=Math.floor(NR/2)-1; // interface between row mid and mid+1
  for(let j=0;j<NR;j++)for(let i=0;i<NC;i++){
    if(i<NC-1){let thr=lerp(cfg.fib[0],cfg.fib[1],rnd());
      if(cls==='Fibre Break'&&i>=8&&i<=10&&j>=1&&j<=NR-2)thr*=.62+.2*rnd();
      add(id(i,j),id(i+1,j),'fibre',1.0,thr);}
    if(j<NR-1){const isIf=(j===mid);let thr=lerp(cfg.mat[0],cfg.mat[1],rnd());
      if(isIf&&cfg.iface)thr=lerp(cfg.iface[0],cfg.iface[1],rnd());
      if(cls==='Matrix Crack'&&i>=8&&i<=11&&j>=2&&j<=5)thr*=.48;
      add(id(i,j),id(i,j+1),isIf&&cfg.iface?'iface':'matrix',.30,thr);
      if(i<NC-1){let t1=lerp(cfg.mat[0],cfg.mat[1],rnd())*2.2,t2=lerp(cfg.mat[0],cfg.mat[1],rnd())*2.2;
        if(isIf&&cfg.iface){t1=lerp(cfg.iface[0],cfg.iface[1],rnd())*2.2;t2=lerp(cfg.iface[0],cfg.iface[1],rnd())*2.2;}
        add(id(i,j),id(i+1,j+1),isIf&&cfg.iface?'iface':'matrix',.18,t1);
        add(id(i+1,j),id(i,j+1),isIf&&cfg.iface?'iface':'matrix',.18,t2);}}
  }
  return {cfg:cfg,nodes:nodes,sp:sp,dx:dx,dy:dy,mid:mid,pw:pw,ph:ph,lam:0,H:(NR-1)*dy,Lx:(NC-1)*dx,broken:{fibre:0,matrix:0,iface:0},events:[],stress:0};
}
function stepSim(s,lam,t){
  s.lam=lam;const cfg=s.cfg,nodes=s.nodes;
  // boundary targets
  for(const n of nodes){
    n.fx=false;n.fy=false;
    if(n.i===0){n.fx=true;n.x=n.x0;if(cfg.shear){n.fy=true;n.y=n.y0;}}
    if(n.i===NC-1){n.fx=true;const sh=cfg.shear?(n.j<=s.mid?1:-1)*lam*cfg.shear*s.Lx:0;n.x=n.x0+lam*cfg.ex*s.Lx+sh;}
    if(n.j===0&&cfg.et){n.fy=true;n.y=n.y0-lam*cfg.et*s.H*.5;}
    if(n.j===NR-1&&cfg.et){n.fy=true;n.y=n.y0+lam*cfg.et*s.H*.5;}
  }
  let newB=0;
  for(let it=0;it<45;it++){
    for(const e of s.sp){if(!e.alive)continue;const A=nodes[e.a],B=nodes[e.b];
      const dxx=B.x-A.x,dyy=B.y-A.y;const d=Math.hypot(dxx,dyy)||1e-6;const diff=(d-e.L0)/d;
      const wa=(A.fx&&A.fy)?0:1,wb=(B.fx&&B.fy)?0:1;const w=wa+wb;if(!w)continue;
      const c=Math.min(1,e.k*1.6);
      const ox=dxx*diff*c,oy=dyy*diff*c;
      if(wa){if(!A.fx)A.x+=ox*wa/w;if(!A.fy)A.y+=oy*wa/w;}
      if(wb){if(!B.fx)B.x-=ox*wb/w;if(!B.fy)B.y-=oy*wb/w;}
    }
  }
  // stress + break check
  let F=0;
  for(const e of s.sp){if(!e.alive)continue;const A=nodes[e.a],B=nodes[e.b];const d=Math.hypot(B.x-A.x,B.y-A.y);
    e.st=(d-e.L0)/e.L0;
    if(e.st>e.thr){e.alive=false;s.broken[e.type]++;newB++;s.events.push({x:(A.x+B.x)/2,y:(A.y+B.y)/2,t:t,type:e.type});}
    else if(B.i===NC-1&&A.i<NC-1){F+=e.k*Math.max(0,e.st)*(B.x-A.x)/d;}}
  s.stress=lerp(s.stress,F,.5);
  return newB;
}
//CORE_END
"""

BREAK_JS = BREAK_CORE + r"""
const P=__PARAMS__;
const cv=document.getElementById('c');let S,sim,cls=P.cls,speed=1,start=performance.now(),curve=[],aeCurve=[],pk=0,holdFrom=null,flashes=[];
const LT=9,HOLD=2.4;
const CL=["Healthy","Matrix Crack","Delamination","Fibre Break"];
const chips=document.getElementById('chips');
CL.forEach(c=>{const b=document.createElement('button');b.textContent=c;b.onclick=()=>{cls=c;reset();};b.dataset.c=c;chips.appendChild(b);});
function mark(){chips.querySelectorAll('button').forEach(b=>b.className=b.dataset.c===cls?'on':'');}
document.getElementById('spd').onchange=e=>{speed=parseFloat(e.target.value)};
document.getElementById('rep').onclick=()=>reset();
let pw,ph;
function build(){S=setup(cv,470);pw=Math.floor(S.w*.60);ph=330;reset();}
function reset(){sim=makeSim(cls,pw,ph,5);curve=[];aeCurve=[];pk=0;holdFrom=null;flashes=[];start=performance.now();mark();}
let simT=0,lastNow=performance.now();
function frame(now){
  const dtr=Math.min(.05,(now-lastNow)/1000);lastNow=now;
  const ctx=S.ctx,W=S.w;ctx.clearRect(0,0,W,S.h);
  const el=(now-start)/1000*speed;
  let lam=clamp(el/LT,0,1);
  if(lam<1||holdFrom===null){
    const nb=stepSim(sim,lam,el);
    const strain=lam*sim.cfg.ex*100+ (sim.cfg.shear?lam*sim.cfg.shear*100:0)+(sim.cfg.et?lam*sim.cfg.et*100*.25:0);
    curve.push([strain,sim.stress]);pk=Math.max(pk,sim.stress);
    aeCurve.push([strain,sim.broken.fibre+sim.broken.matrix+sim.broken.iface]);
    for(let k=0;k<nb;k++){}
    if(lam>=1)holdFrom=el;
  } else if(el-holdFrom>HOLD){reset();}
  // flashes from events
  while(flashes.length<sim.events.length){const e=sim.events[flashes.length];flashes.push({x:e.x,y:e.y,t:performance.now(),type:e.type});}
  const px=16,py=44;
  txt(ctx,'Polymer matrix + carbon-fibre lattice under load',px,py-14,'#9fb0c7',11,'left',700);
  ctx.fillStyle='rgba(10,16,28,.85)';rr(ctx,px,py,pw,ph,14);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.18)';ctx.stroke();
  ctx.save();rr(ctx,px,py,pw,ph,14);ctx.clip();ctx.translate(px,py);
  // load arrows
  const la=lam;ctx.fillStyle='rgba(255,184,107,'+(.25+.6*la)+')';
  for(let j=0;j<NR;j+=2){const n=sim.nodes[(j)*NC+NC-1];const ax=n.x+8;ctx.beginPath();ctx.moveTo(ax,n.y-5);ctx.lineTo(ax+14+18*la,n.y);ctx.lineTo(ax,n.y+5);ctx.closePath();ctx.fill();}
  // springs
  for(const e of sim.sp){
    const A=sim.nodes[e.a],B=sim.nodes[e.b];
    if(!e.alive)continue;
    const f=clamp(e.st/e.thr,0,1);
    if(e.type==='fibre'){ctx.strokeStyle=mix([46,230,214],[255,70,70],Math.pow(f,1.6));ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();}
    else if(e.k>.25){
      // vertical polymer chain drawn as zig-zag
      const dxx=B.x-A.x,dyy=B.y-A.y,d=Math.hypot(dxx,dyy),nx=-dyy/d,ny=dxx/d;const seg=6,amp=3.2*Math.max(.25,1-e.st*5);
      ctx.strokeStyle=e.type==='iface'?mix([190,150,255],[255,70,70],Math.pow(f,1.4)):mix([155,124,255],[255,80,80],Math.pow(f,1.4));ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(A.x,A.y);
      for(let q=1;q<seg;q++){const u=q/seg,o=(q%2?1:-1)*amp;ctx.lineTo(A.x+dxx*u+nx*o,A.y+dyy*u+ny*o);}ctx.lineTo(B.x,B.y);ctx.stroke();}
    else{ctx.strokeStyle='rgba(155,124,255,'+(.10+.5*f)+')';ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();}
  }
  for(const n of sim.nodes){ctx.fillStyle='#cfe0f5';ctx.beginPath();ctx.arc(n.x,n.y,2.2,0,6.283);ctx.fill();}
  // break flashes
  const nowp=performance.now();
  for(const f of flashes){const a=(nowp-f.t)/700;if(a<1){ctx.strokeStyle=f.type==='fibre'?'rgba(255,255,255,'+(1-a)+')':'rgba(255,90,90,'+(1-a)+')';ctx.lineWidth=2;ctx.beginPath();ctx.arc(f.x,f.y,4+a*(f.type==='fibre'?22:14),0,6.283);ctx.stroke();}}
  ctx.restore();
  // legend + status
  const ly=py+ph+16;
  ctx.fillStyle='#2ee6d6';ctx.fillRect(px,ly,16,3);txt(ctx,'carbon fibre',px+22,ly+5,'#9fb0c7',10.5);
  ctx.strokeStyle='#9b7cff';ctx.lineWidth=1.4;ctx.beginPath();ctx.moveTo(px+110,ly+1);ctx.lineTo(px+114,ly-3);ctx.lineTo(px+118,ly+5);ctx.lineTo(px+122,ly-3);ctx.lineTo(px+126,ly+1);ctx.stroke();txt(ctx,'polymer chain',px+132,ly+5,'#9fb0c7',10.5);
  txt(ctx,'red = about to break',px+225,ly+5,'#ff8a8a',10.5);
  txt(ctx,sim.cfg.note,px+pw,ly+5,'#cfe0f5',11,'right',600);
  const tot=sim.broken.fibre+sim.broken.matrix+sim.broken.iface;
  txt(ctx,'Broken bonds: '+tot+'   (fibre '+sim.broken.fibre+' | resin '+sim.broken.matrix+' | interface '+sim.broken.iface+')',px,ly+30,tot>0?'#ffb3b3':'#5ee7a5',12,'left',700);
  txt(ctx,'Load '+Math.round(lam*100)+'%',px+pw,ly+30,'#ffb86b',12,'right',700);
  // charts
  const cx=px+pw+22,cw=W-cx-16;
  function chart(y,h,title,data,col,ymaxMin,yl){
    txt(ctx,title,cx,y-8,'#9fb0c7',11,'left',700);
    ctx.fillStyle='rgba(10,16,28,.85)';rr(ctx,cx,y,cw,h,10);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.16)';ctx.stroke();
    const xm=Math.max(sim.cfg.ex*100+(sim.cfg.shear||0)*100+(sim.cfg.et||0)*25,1);
    let ym=ymaxMin;for(const d of data)ym=Math.max(ym,d[1]);
    ctx.strokeStyle='rgba(148,163,184,.10)';for(let g=1;g<4;g++){ctx.beginPath();ctx.moveTo(cx+8,y+h-20-g*(h-34)/4);ctx.lineTo(cx+cw-8,y+h-20-g*(h-34)/4);ctx.stroke();}
    ctx.strokeStyle=col;ctx.lineWidth=2;ctx.beginPath();
    data.forEach((d,i)=>{const X=cx+10+d[0]/xm*(cw-22),Y=y+h-20-d[1]/ym*(h-34);if(i===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);});ctx.stroke();
    if(data.length){const d=data[data.length-1];const X=cx+10+d[0]/xm*(cw-22),Y=y+h-20-d[1]/ym*(h-34);ctx.fillStyle=col;ctx.beginPath();ctx.arc(X,Y,4,0,6.283);ctx.fill();}
    txt(ctx,'strain (%) \u2192',cx+cw-10,y+h-6,'#6f819b',10,'right',500);txt(ctx,yl,cx+10,y+14,'#6f819b',10,'left',500);
  }
  chart(py,150,'Stress\u2013strain response',curve,'#39d9d1',.12,'stress (a.u.)');
  chart(py+190,140,'Acoustic-emission events (cumulative bond breaks)',aeCurve,'#ffb86b',4,'broken bonds');
  const first=aeCurve.findIndex(d=>d[1]>0);
  if(first>=0){txt(ctx,'first break \u2192 sensor would flag damage',cx,py+ph+16,'#ff9d9d',10.5,'left',600);}
  else txt(ctx,'no damage events',cx,py+ph+16,'#5ee7a5',10.5,'left',600);
  requestAnimationFrame(frame);
}
build();requestAnimationFrame(frame);
window.addEventListener('resize',build);
"""


def breakage_html(cls="Fibre Break"):
    return _build(BREAK_BODY, BREAK_JS, {"cls": cls})


# =============================================================================
# 06  THERMAL HEALING SIMULATOR
# =============================================================================
HEAL_BODY = """
<div class="bar"><b>Self-healing simulator</b>
<span>Temperature <input id="T" type="range" min="20" max="220" step="1" value="25" style="width:210px"> <b id="Tv">25 &deg;C</b></span>
<span class="sp"></span>
Speed <select id="spd"><option value="1">1x</option><option value="3" selected>3x</option><option value="10">10x</option></select>
<button id="ramp">&#9650; Auto-heat</button><button id="brk">&#10007; Break again</button><button id="pz">&#10074;&#10074; Pause</button></div>
<canvas id="c"></canvas>
"""

HEAL_JS = r"""
const P=__PARAMS__;
const R=8.314,TREF=393.15,KREF=.12,TDEG=190;
const heq=T=>1/(1+Math.exp(-(T-(P.onset+25))/10));
const kT=T=>KREF*Math.exp(P.ea*1000/R*(1/TREF-1/(T+273.15)));
const cv=document.getElementById('c');let S,pw,ph;
let T=P.temp,h=0,tmin=0,speed=3,paused=false,auto=false,last=performance.now(),hist=[],chains=[],links=[],face=[];
const sl=document.getElementById('T');sl.value=T;
function setT(v){T=clamp(v,20,220);sl.value=T;document.getElementById('Tv').textContent=Math.round(T)+' \u00b0C';}
sl.oninput=e=>{auto=false;document.getElementById('ramp').className='';setT(parseFloat(e.target.value));};
document.getElementById('spd').onchange=e=>{speed=parseFloat(e.target.value)};
document.getElementById('ramp').onclick=function(){auto=!auto;this.className=auto?'on':'';if(auto&&T>=200)setT(25);};
document.getElementById('brk').onclick=()=>{h=0;tmin=0;hist=[];};
document.getElementById('pz').onclick=function(){paused=!paused;this.className=paused?'on':'';this.innerHTML=paused?'&#9654; Resume':'&#10074;&#10074; Pause';};
setT(T);
function build(){
  S=setup(cv,470);pw=Math.floor(S.w*.58);ph=340;
  const r=mulberry(21);chains=[];
  for(let i=0;i<34;i++){const side=i%2?1:-1;chains.push({side:side,y:70+r()*(ph-140),len:40+r()*80,ph:r()*6.28,ph2:r()*6.28,w:.7+r()*.6});}
  links=[];const M=18;for(let i=0;i<M;i++)links.push({y:62+(i+.5)*(ph-124)/M+(r()-.5)*6,th:(i+r()*.6)/M,ph:r()*6.28});
  face=[];for(let y=0;y<=ph;y+=10)face.push((r()-.5)*9);
}
function frame(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;
  if(!paused){
    if(auto){setT(T+dt*14);if(T>=160)auto=false,document.getElementById('ramp').className='';}
    const dm=dt*speed;tmin+=dm;
    const k=kT(T),he=heq(T);
    if(he>h)h+=(he-h)*(1-Math.exp(-k*dm));
    if(T>TDEG)h=Math.max(0,h-.02*(T-TDEG)/10*dm);
    h=clamp(h,0,1);
    if(Math.floor(tmin*4)!==hist._lt){hist._lt=Math.floor(tmin*4);hist.push([tmin,h,T]);if(hist.length>400)hist.shift();}
  }
  const ctx=S.ctx,W=S.w;ctx.clearRect(0,0,W,S.h);
  const px=16,py=40;
  const heat=clamp((T-20)/200,0,1);
  txt(ctx,'Cross-section of damaged polymer matrix (between CFRP plies)',px,py-14,'#9fb0c7',11,'left',700);
  ctx.save();rr(ctx,px,py,pw,ph,14);ctx.clip();ctx.translate(px,py);
  // background + heat
  ctx.fillStyle='#0d1626';ctx.fillRect(0,0,pw,ph);
  const hg=ctx.createLinearGradient(0,ph,0,0);hg.addColorStop(0,'rgba(255,'+Math.round(140-90*heat)+',60,'+(.15+.55*heat)+')');hg.addColorStop(1,'rgba(255,120,60,0)');
  ctx.fillStyle=hg;ctx.fillRect(0,0,pw,ph);
  // plies
  for(const y0 of [0,ph-50]){ctx.fillStyle='#0a0f19';ctx.fillRect(0,y0,pw,50);ctx.fillStyle='rgba(80,95,120,.55)';
    for(let x=10;x<pw;x+=18){ctx.beginPath();ctx.arc(x,y0+25,6.5,0,6.283);ctx.fill();}}
  txt(ctx,'carbon-fibre ply',10,16,'#6f819b',10,'left',600);
  // crack gap
  const gmax=54,gap=gmax*Math.pow(1-h,1.15),cxm=pw/2;
  const wob=(T-20)/180;
  const t=now/1000;
  // matrix blocks (left/right)
  function block(side){
    ctx.beginPath();const x0=side<0?0:pw,xe=cxm+side*gap/2;
    ctx.moveTo(x0,50);ctx.lineTo(xe+face[0]*Math.max(.15,1-h*.9),50);
    face.forEach((f,i)=>{const y=50+i*10;if(y<=ph-50)ctx.lineTo(xe+f*(1-h*.92)*side*.9,y);});
    ctx.lineTo(x0,ph-50);ctx.closePath();
    const g=ctx.createLinearGradient(0,50,0,ph-50);g.addColorStop(0,'rgba(155,124,255,.18)');g.addColorStop(1,'rgba(155,124,255,.10)');ctx.fillStyle=g;ctx.fill();
    ctx.strokeStyle=h>.6?'rgba(94,231,165,.75)':'rgba(255,100,100,.8)';ctx.lineWidth=1.6;ctx.stroke();
  }
  block(-1);block(1);
  // polymer chains
  for(const c of chains){
    const xs=cxm+c.side*(gap/2+4),dir=-c.side;
    const amp=1+9*wob*c.w;
    ctx.strokeStyle='rgba(180,160,255,.55)';ctx.lineWidth=1.3;ctx.beginPath();
    const n=26;for(let q=0;q<=n;q++){const u=q/n;const x=xs+dir*(-1)*(-1)*0+c.side*u*c.len;const y=c.y+Math.sin(u*14+c.ph+t*(1.5+6*wob))*amp*(.4+.6*u)+Math.sin(u*5+c.ph2+t*(1+4*wob))*amp*.4;if(q===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
    ctx.stroke();
    // dangling end
    const yy=c.y+Math.sin(c.ph+t*(1.5+6*wob))*amp*.1;
    ctx.fillStyle=h>.5?'#5ee7a5':'#ff6b6b';ctx.beginPath();ctx.arc(xs,yy,2.6,0,6.283);ctx.fill();
  }
  // bridging links
  for(const l of links){
    const q=clamp((h-l.th)*7,0,1);if(q<=0)continue;
    const xL=cxm-gap/2-2,xR=cxm+gap/2+2;
    ctx.strokeStyle='rgba(94,231,165,'+(.25+.7*q)+')';ctx.lineWidth=1.6+q;ctx.beginPath();
    const n=16;for(let s=0;s<=n;s++){const u=s/n;const x=lerp(xL,xR,u);const y=l.y+Math.sin(u*18+l.ph+t*(3+8*wob))*(2+6*wob)*(1-Math.abs(u-.5)*1.2);if(s===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
    ctx.stroke();
    if(q>.99){ctx.fillStyle='rgba(94,231,165,.9)';ctx.beginPath();ctx.arc((xL+xR)/2,l.y,2.2,0,6.283);ctx.fill();}
  }
  // heater
  const hc=mix([60,70,90],[255,110,50],heat);ctx.fillStyle=hc;ctx.fillRect(0,ph-6,pw,6);
  ctx.restore();
  rr(ctx,px,py,pw,ph,14);ctx.strokeStyle='rgba(148,163,184,.25)';ctx.stroke();
  txt(ctx,'heater',px+pw-10,py+ph+12,'#ff9a6b',10,'right',600);
  // status
  let st='Below activation \u2013 chains frozen, no healing',sc='143,160,184';
  if(T>=P.onset-10&&T<P.onset+15){st='Chain mobility rising \u2013 very slow healing';sc='255,184,107';}
  if(T>=P.onset+15){st='Reversible bonds reforming across the crack';sc='94,231,165';}
  if(h>.97){st='\u2713 Fully healed \u2013 crack closed';sc='94,231,165';}
  if(T>TDEG){st='\u26A0 Above '+TDEG+' \u00b0C \u2013 thermal degradation of the polymer';sc='255,90,90';}
  ctx.fillStyle='rgba('+sc+',.12)';rr(ctx,px,py+ph+22,pw,26,9);ctx.fill();ctx.strokeStyle='rgba('+sc+',.5)';ctx.stroke();
  txt(ctx,st,px+12,py+ph+39,'rgb('+sc+')',11.5,'left',700);
  // right column
  const cx=px+pw+22,cw=W-cx-16;
  // gauges
  function gauge(y,label,val,col,sub){txt(ctx,label,cx,y,'#9fb0c7',11,'left',700);txt(ctx,sub,cx+cw,y,col,13,'right',800);
    ctx.fillStyle='rgba(148,163,184,.15)';rr(ctx,cx,y+7,cw,12,6);ctx.fill();ctx.fillStyle=col;rr(ctx,cx,y+7,Math.max(8,cw*val),12,6);ctx.fill();}
  gauge(py+4,'Crack healed',h,'#5ee7a5',(h*100).toFixed(0)+'%');
  const rec=.92*h;
  gauge(py+44,'Strength recovery (illustrative)',rec,'#39d9d1',(rec*100).toFixed(0)+'%');
  txt(ctx,'t = '+tmin.toFixed(1)+' min   |   T = '+T.toFixed(0)+' \u00b0C   |   rate k = '+kT(T).toFixed(3)+' /min',cx,py+86,'#cfe0f5',11,'left',600);
  // chart 1: healing vs time
  function panel(y,hh,title){txt(ctx,title,cx,y-8,'#9fb0c7',11,'left',700);ctx.fillStyle='rgba(10,16,28,.85)';rr(ctx,cx,y,cw,hh,10);ctx.fill();ctx.strokeStyle='rgba(148,163,184,.16)';ctx.stroke();}
  const y1=py+118,h1=108;panel(y1,h1,'Healing progress vs time');
  const tmax=Math.max(30,tmin*1.05);
  ctx.strokeStyle='rgba(255,154,107,.55)';ctx.lineWidth=1.3;ctx.beginPath();
  hist.forEach((d,i)=>{const X=cx+10+d[0]/tmax*(cw-20),Y=y1+h1-16-((d[2]-20)/200)*(h1-30);if(i===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);});ctx.stroke();
  ctx.strokeStyle='#5ee7a5';ctx.lineWidth=2.2;ctx.beginPath();
  hist.forEach((d,i)=>{const X=cx+10+d[0]/tmax*(cw-20),Y=y1+h1-16-d[1]*(h1-30);if(i===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);});ctx.stroke();
  txt(ctx,'green = healed fraction   orange = temperature',cx+8,y1+h1-4,'#6f819b',9.5,'left',500);
  // chart 2: capacity vs temperature
  const y2=y1+h1+34,h2=118;panel(y2,h2,'Healing capacity vs temperature');
  ctx.strokeStyle='#9b7cff';ctx.lineWidth=2;ctx.beginPath();
  for(let i=0;i<=100;i++){const TT=20+i*2;const X=cx+10+i/100*(cw-20),Y=y2+h2-20-heq(TT)*(h2-34);if(i===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);}ctx.stroke();
  // rate curve (log-ish normalized)
  ctx.strokeStyle='rgba(57,217,209,.8)';ctx.lineWidth=1.5;ctx.beginPath();
  const kmax=kT(220);for(let i=0;i<=100;i++){const TT=20+i*2;const X=cx+10+i/100*(cw-20),Y=y2+h2-20-Math.pow(kT(TT)/kmax,.35)*(h2-34);if(i===0)ctx.moveTo(X,Y);else ctx.lineTo(X,Y);}ctx.stroke();
  const mx=cx+10+(T-20)/200*(cw-20);
  ctx.strokeStyle='rgba(255,255,255,.55)';ctx.setLineDash([4,3]);ctx.beginPath();ctx.moveTo(mx,y2+6);ctx.lineTo(mx,y2+h2-20);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(mx,y2+h2-20-heq(T)*(h2-34),4.5,0,6.283);ctx.fill();
  const ox=cx+10+(P.onset-20)/200*(cw-20);ctx.strokeStyle='rgba(255,184,107,.5)';ctx.beginPath();ctx.moveTo(ox,y2+6);ctx.lineTo(ox,y2+h2-20);ctx.stroke();
  txt(ctx,'onset',ox+3,y2+16,'#ffb86b',9.5,'left',600);
  txt(ctx,'20',cx+10,y2+h2-6,'#6f819b',9.5,'left');txt(ctx,'220 \u00b0C',cx+cw-10,y2+h2-6,'#6f819b',9.5,'right');
  txt(ctx,'purple = capacity',cx+cw/2-40,y2+h2-6,'#9b7cff',9.5,'center',600);txt(ctx,'cyan = rate (scaled)',cx+cw/2+40,y2+h2-6,'#39d9d1',9.5,'center',600);
  requestAnimationFrame(frame);
}
build();requestAnimationFrame(frame);
window.addEventListener('resize',build);
"""


def healing_html(onset=60, ea_kj=80, temp=25):
    return _build(HEAL_BODY, HEAL_JS, {"onset": onset, "ea": ea_kj, "temp": temp})
