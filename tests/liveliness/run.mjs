// QA harness 生命感 S1 — usage: node run.mjs /path/to/glimmer-live-s1.html
import { chromium } from 'playwright';
import fs from 'fs';
const FILE = process.argv[2] || '/workspace/glimmer-live/dist/glimmer-live-s1.html';
if (!fs.existsSync(FILE)) { console.error('MISSING', FILE); process.exit(2); }
const URL = 'file://' + FILE, R = { file: FILE, sizeMB: +(fs.statSync(FILE).size/1048576).toFixed(2) };
const b = await chromium.launch();
const mk = async (w, h) => { const c = await b.newContext({ viewport:{width:w,height:h}, deviceScaleFactor:3, isMobile:true, hasTouch:true });
  const p = await c.newPage(); const errs=[]; p.on('console',m=>m.type()==='error'&&errs.push(m.text())); p.on('pageerror',e=>errs.push(String(e)));
  const t0=Date.now(); await p.goto(URL,{waitUntil:'load'}); const load=Date.now()-t0; await p.waitForTimeout(1500); return {c,p,errs,load}; };
// 1 layout
R.layout=[];
for (const [w,h] of [[360,640],[390,844],[412,915],[844,390]]) {
  const {c,p,errs,load}=await mk(w,h);
  const info=await p.evaluate(()=>{const d=document.documentElement,vw=innerWidth,vh=innerHeight;
    const els=[...document.querySelectorAll('button,a,[role=button],[onclick],input,canvas')].map(e=>{const r=e.getBoundingClientRect();return{tag:e.tagName,id:e.id,cls:String(e.className).slice(0,40),x:r.x,y:r.y,w:r.width,h:r.height,vis:getComputedStyle(e).visibility!=='hidden'&&r.width>0}}).filter(e=>e.vis);
    const small=els.filter(e=>e.tag!=='CANVAS'&&(e.w<44||e.h<44)); const off=els.filter(e=>e.x<0||e.y<0||e.x+e.w>vw+1||e.y+e.h>vh+1);
    const ov=[];const bt=els.filter(e=>e.tag!=='CANVAS');for(let i=0;i<bt.length;i++)for(let j=i+1;j<bt.length;j++){const a=bt[i],q=bt[j];if(a.x<q.x+q.w&&q.x<a.x+a.w&&a.y<q.y+q.h&&q.y<a.y+a.h)ov.push([a.id||a.cls,q.id||q.cls]);}
    return{vw,vh,scrollW:d.scrollWidth,scrollH:d.scrollHeight,hScroll:d.scrollWidth>vw,vScroll:d.scrollHeight>vh,els,small,off,ov,
      rotateText:/轉|rotate|直向|portrait/i.test(document.body.innerText), qaKeys:window.__qa?Object.keys(window.__qa):null,
      globals:Object.keys(window).filter(k=>/qa|pet|game|gaze|glimmer|state/i.test(k))};});
  const shot=`shots/layout_${w}x${h}.png`; await p.screenshot({path:shot});
  R.layout.push({w,h,load,errs,shot,...info}); await c.close();
}
// 2 gaze (needs state exposure; probe common names)
const {c,p,errs,load}=await mk(390,844); R.loadMs=load;
const probe=()=>p.evaluate(()=>{const q=window.__qa||{};const s=(q.pet||q.state||q);try{return JSON.parse(JSON.stringify(s,(k,v)=>typeof v==='function'?undefined:v))}catch(e){return String(e)}});
R.qaSnapshot=await probe();
const cvs=await p.evaluate(()=>{const e=document.querySelector('canvas')||document.body;const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height}});
const cx=cvs.x+cvs.w/2, cy=cvs.y+cvs.h/2; R.gaze=[];
for (const [dx,dy] of [[-150,0],[150,0],[0,-250],[0,250],[0,0],[2,1],[-2,-1]]) {
  await p.mouse.move(cx+dx,cy+dy,{steps:5}); const t=[];for(let i=0;i<6;i++){await p.waitForTimeout(50);t.push(await probe());}
  R.gaze.push({dx,dy,samples:t}); await p.screenshot({path:`shots/gaze_${dx}_${dy}.png`});
}
// idle return: wait 12s sampling
R.idle=[];for(let i=0;i<12;i++){await p.waitForTimeout(1000);R.idle.push(await probe());}
// 3 tap behind: taps around above/sides of center
R.taps=[];for(let i=0;i<20;i++){const a=(i/20)*Math.PI*2,rr=120+ (i%3)*30;await p.touchscreen.tap(cx+Math.cos(a)*rr,cy+Math.sin(a)*rr);await p.waitForTimeout(1200);R.taps.push({i,x:cx+Math.cos(a)*rr,y:cy+Math.sin(a)*rr,s:await probe()});}
for(let i=0;i<10;i++){await p.touchscreen.tap(cx,cy-160);await p.waitForTimeout(300);} R.spamAfter=await probe(); await p.waitForTimeout(3000); R.spamSettle=await probe();
await p.touchscreen.tap(cx,cy); await p.waitForTimeout(800); R.tapPet=await probe(); await p.screenshot({path:'shots/tap_pet.png'});
// 6 perf 4x
const cdp=await c.newCDPSession(p); await cdp.send('Emulation.setCPUThrottlingRate',{rate:4}); await cdp.send('Performance.enable');
const perf=await p.evaluate((D)=>new Promise(res=>{const f=[];let lt=0,last=performance.now();try{new PerformanceObserver(l=>lt+=l.getEntries().length).observe({entryTypes:['longtask']})}catch(e){}
  const t0=last;(function loop(t){f.push(t-last);last=t;if(t-t0<D)requestAnimationFrame(loop);else{f.sort((a,b)=>a-b);res({frames:f.length,fps:f.length/30,p50:f[f.length>>1],p95:f[Math.floor(f.length*.95)],max:f[f.length-1],longtasks:lt,heapMB:performance.memory?performance.memory.usedJSHeapSize/1048576:null})}})(last)}),+(process.env.PERF_MS||30000));
R.perf4x=perf; R.consoleErrors=errs;
fs.writeFileSync('out/results.json',JSON.stringify(R,null,1)); console.log('done', JSON.stringify({size:R.sizeMB,load:R.loadMs,perf}));
await b.close();
