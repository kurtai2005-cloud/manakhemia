/* 遊測 s1 修正＋PR#17 QA3＋H3 雨聲 E2E（合併版）。node tests/e2e-s1.js（playwright-core＋系統 Chrome；http server 開 glimmer-live）
   P1-1 ⚙️／📖 熱區 ≥44 CSS px（390／360／320 闊）；P1-2 橫向「請轉直向」；P1-4 靜態層 cache（命中率＋同逐層合成像素一致）；
   P1-5 按短邊 fit＋背景延伸（多種視窗、四角唔係黑邊）；P2 拖動眼神跟手指／短 tap 先回頭／長按唔觸發／寵物熱區 ≥44px 貼身／開心閉眼頭部微轉；
   QA3 日記「2 日後作廢」；H3 雨聲 short→loop（BufferSource.loop）＋停雨淡出＋開發模式切雨觸發。截圖去 glimmer-combo/screens/。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', '..', 'screens') + '/';
require('fs').mkdirSync(OUT, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const errs = [];
  const open = async (vp, qs, opt) => {
    const ctx = await browser.newContext(Object.assign({ viewport: vp, deviceScaleFactor: 1 }, opt || {}));
    const page = await ctx.newPage();
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    await page.goto(BASE + '?' + qs); await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + qs);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad && __glimmer.hdReady).catch(() => { });
    await page.evaluate(() => Promise.all([__glimmer.liveLoad, __glimmer.hdReady])); await page.waitForTimeout(300);
    return { ctx, page, E: (fn, a) => page.evaluate(fn, a), shot: async (n) => { await page.waitForTimeout(150); await page.screenshot({ path: OUT + n + '.png' }); console.log('  📷 ' + n); } };
  };
  const adult = (E, form) => E((form) => { const s = __glimmer.state; if (form === 'sprout') { s.stage = 'sprout'; s.form = null; s.growthSec = 100; } else { s.stage = 'adult'; s.form = form; s.growthSec = 3600; } Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); s.poops = 0; }, form || 'soft');
  const closeModals = (E) => E(() => { for (let i = 0; i < 8; i++) { const m = document.getElementById('modal'); if (!m || m.style.display !== 'flex') break; const b = document.querySelector('#mbox [data-testid=modal-btn-0]'); if (!b) break; b.click(); } });

  console.log('# P1-1 ⚙️／📖 熱區 ≥44 CSS px');
  for (const vp of [{ width: 390, height: 844 }, { width: 360, height: 780 }, { width: 360, height: 640 }, { width: 320, height: 568 }]) {
    const { ctx, E } = await open(vp, 'seed=3&ev=0');
    const r = await E(() => ['gear', 'diary'].map(id => { const b = document.getElementById(id).getBoundingClientRect(); return { id, w: +b.width.toFixed(1), h: +b.height.toFixed(1) }; }));
    ok(r.every(x => x.w >= 44 && x.h >= 44), `${vp.width}×${vp.height}：⚙️ ${r[0].w}×${r[0].h}、📖 ${r[1].w}×${r[1].h} CSS px（≥44）`, JSON.stringify(r));
    if (vp.width === 360 && vp.height === 780) {   // 實點：熱區邊緣（距中心 21px）點落都打開
      const hit = await E(() => { const b = document.getElementById('gear').getBoundingClientRect(), cx = b.left + b.width / 2, cy = b.top + b.height / 2; return [[cx - 21, cy], [cx + 21, cy], [cx, cy - 21], [cx, cy + 21]].map(([x, y]) => { const el = document.elementFromPoint(x, y); return !!(el && el.closest('#gear')); }); });
      ok(hit.every(Boolean), '360 闊：⚙️ 中心 ±21px 四邊都命中', JSON.stringify(hit));
    }
    await ctx.close();
  }

  console.log('# P1-2 橫向提示「請轉直向」');
  {
    let o = await open({ width: 844, height: 390 }, 'seed=3&ev=0', { hasTouch: true, isMobile: true });
    let r = await o.E(() => { const el = document.getElementById('rotate'), cs = getComputedStyle(el); return { disp: cs.display, txt: el.innerText, z: +cs.zIndex, cover: el.getBoundingClientRect().width >= innerWidth - 1 }; });
    ok(r.disp === 'flex' && /請轉直向/.test(r.txt) && r.cover && r.z >= 100, '手機橫向（844×390 touch）：顯示「請轉直向」全屏', JSON.stringify(r));
    await o.shot('s1-landscape-rotate'); await o.ctx.close();
    o = await open({ width: 390, height: 844 }, 'seed=3&ev=0', { hasTouch: true, isMobile: true });
    r = await o.E(() => getComputedStyle(document.getElementById('rotate')).display); ok(r === 'none', '手機直向：唔顯示', r); await o.ctx.close();
    o = await open({ width: 1280, height: 720 }, 'seed=3&ev=0&orient=landscape');
    r = await o.E(() => getComputedStyle(document.getElementById('rotate')).display); ok(r === 'flex', '?orient=landscape 強制顯示（桌面測試用）', r); await o.ctx.close();
    o = await open({ width: 1280, height: 720 }, 'seed=3&ev=0');
    r = await o.E(() => getComputedStyle(document.getElementById('rotate')).display); ok(r === 'none', '桌面滑鼠橫向視窗：唔擋（方便電腦試玩）', r); await o.ctx.close();
  }

  console.log('# P1-5 按短邊 fit＋背景延伸（唔留黑邊）');
  for (const vp of [{ width: 390, height: 844 }, { width: 360, height: 800 }, { width: 412, height: 915 }, { width: 768, height: 1024 }, { width: 1280, height: 720 }]) {
    const o = await open(vp, 'seed=3&ev=0&hour=13'); await adult(o.E); await o.page.waitForTimeout(500);
    const li = await o.E(() => __glimmer.layoutInfo);
    const fitW = Math.min(vp.width / 195, vp.height / 422) * 195;
    const buf = await o.page.screenshot(); const png = require(path.join(__dirname, 'png-lite.js')).decode(buf);
    const px = (x, y) => { const i = (y * png.width + x) * 4; return [png.data[i], png.data[i + 1], png.data[i + 2]]; };
    const pts = [[2, 2], [png.width - 3, 2], [2, png.height - 3], [png.width - 3, png.height - 3], [2, png.height >> 1], [png.width - 3, png.height >> 1]];
    const dark = pts.map(([x, y]) => px(x, y)).filter(c => c[0] + c[1] + c[2] < 24).length;
    const bars = (li.barsX > 1 || li.barsY > 1);
    ok(Math.abs(li.cssW - fitW) < 1 && (li.cssW >= vp.width - 1 || li.cssH >= vp.height - 1), `${vp.width}×${vp.height}：按短邊 fit（${li.fit}，${Math.round(li.cssW)}×${Math.round(li.cssH)}）`, JSON.stringify(li));
    ok(!bars || (dark === 0 && (await o.E(() => __glimmer.bgfillN || 0)) > 0), `${vp.width}×${vp.height}：畫面外由模糊延伸背景填滿（四角／兩側 ${pts.length} 點冇黑邊）`, JSON.stringify(pts.map(([x, y]) => px(x, y))));
    if (vp.width === 1280 || vp.width === 768) await o.shot('s1-fit-' + vp.width + 'x' + vp.height);
    await o.ctx.close();
  }

  // 主測試頁（390×844）
  const o = await open({ width: 390, height: 844 }, 'seed=7&ev=0&hour=13&q=high');
  const { page, E, shot } = o;
  await adult(E, 'soft'); await page.waitForTimeout(400); await closeModals(E);

  console.log('# P1-4 靜態層 cache（時段／雨先重建）');
  {
    await E(() => { __qa.hd2d.set('H3'); __qa.hd2d.skipFade(); }); await page.waitForTimeout(600);
    const a = await E(() => __qa.hd2d.cache()); await page.waitForTimeout(1500); const b = await E(() => __qa.hd2d.cache());
    const builds = b.builds - a.builds, hits = b.hits - a.hits;
    ok(a.on && hits > 40 && builds <= hits * 0.25, `靜止 1.5 秒：cache 命中 ${hits} 次、重建 ${builds} 次（只喺整數視差位移變時）`, JSON.stringify([a, b]));
    await E(() => { __qa.hd2d.set('H3rain'); }); await page.waitForTimeout(300);
    const c = await E(() => __qa.hd2d.cache()); ok(c.variants.indexOf('H3rain') >= 0 && c.variants.indexOf('H3') >= 0, '轉雨（H3→H3rain crossfade）：另起一套 cache；H3 保留', JSON.stringify(c.variants));
    // 像素一致：凍結視差＋粒子 → cache on／off 同一幀比較
    const diff = await E(async () => {
      const r = __glimmer.renderer, hd = __glimmer.hd; __qa.hd2d.set('H2'); __qa.hd2d.skipFade(); __qa.pet.pause(true);
      const freeze = () => { r.parT.active = true; r.parT.last = 1e9; r.parT.x = 0.3; r.parT.y = -0.2; r.par.x = 0.3; r.par.y = -0.2; hd.ps.length = 0; hd.part = null; };
      const grab = async () => { freeze(); await new Promise(res => setTimeout(res, 120)); freeze(); await new Promise(res => requestAnimationFrame(() => requestAnimationFrame(res))); const cc = document.createElement('canvas'); cc.width = 195; cc.height = 422; const cx = cc.getContext('2d', { willReadFrequently: true }); cx.drawImage(hd.buf, 0, 0); return cx.getImageData(0, 0, 195, 422).data; };
      const keepPart = hd.part; hd.cacheOn = true; const A = await grab(); hd.cacheOn = false; const B = await grab(); hd.cacheOn = true; hd.part = keepPart; __qa.pet.pause(false);
      let mx = 0, n = 0; for (let i = 0; i < A.length; i += 4) { const d = Math.max(Math.abs(A[i] - B[i]), Math.abs(A[i + 1] - B[i + 1]), Math.abs(A[i + 2] - B[i + 2])); if (d > mx) mx = d; if (d > 2) n++; }
      return { mx, n, tot: A.length / 4 };
    });
    ok(diff.n / diff.tot < 0.02 && diff.mx <= 12, `cache 合成 vs 逐層合成：最大差 ${diff.mx}／差 >2 嘅像素 ${(100 * diff.n / diff.tot).toFixed(2)}%`, JSON.stringify(diff));
    await E(() => { __qa.hd2d.set('auto'); __qa.hd2d.skipFade(); });
  }

  console.log('# P2 寵物熱區 ≥44px 但貼身');
  await E(() => { __qa.pet.pause(true); __qa.pet.force('idle'); __qa.pet.step(1); __qa.pet.setGaze(null); }); await page.waitForTimeout(300);
  let hb = await E(() => __qa.pet.hitBox());
  ok(hb.css.w >= 44 && hb.css.h >= 44, `soft：熱區 ${Math.round(hb.css.w)}×${Math.round(hb.css.h)} CSS px（≥44）`, JSON.stringify(hb.css));
  ok(hb.body && hb.css.w <= Math.max(44, hb.bodyCss.w + 14) && hb.css.h <= Math.max(44, hb.bodyCss.h + 14), `熱區唔大過身體太多（身體 ${Math.round(hb.bodyCss.w)}×${Math.round(hb.bodyCss.h)}，每邊 ≤7 CSS px；舊版 176×188）`, JSON.stringify([hb.css, hb.bodyCss]));
  await adult(E, 'sprout'); await page.waitForTimeout(400);
  const hs = await E(() => __qa.pet.hitBox());
  ok(hs.css.w >= 44 && hs.css.h >= 44 && hs.body && hs.css.w <= Math.max(44, hs.bodyCss.w + 14) + 1, `sprout（細隻）：撐到 ${Math.round(hs.css.w)}×${Math.round(hs.css.h)}（身體 ${Math.round(hs.bodyCss.w)}×${Math.round(hs.bodyCss.h)}）`, JSON.stringify([hs.css, hs.bodyCss]));
  {
    const o2 = await open({ width: 360, height: 780 }, 'seed=7&ev=0&hour=13'); await adult(o2.E, 'sprout'); await o2.page.waitForTimeout(500);
    const h3 = await o2.E(() => __qa.pet.hitBox()); ok(h3.css.w >= 44 && h3.css.h >= 44, `360 闊 sprout：熱區 ${h3.css.w.toFixed(1)}×${h3.css.h.toFixed(1)} CSS px（≥44）`, JSON.stringify(h3.css)); await o2.ctx.close();
  }
  await adult(E, 'soft'); await page.waitForTimeout(400);
  // 熱區外（身體右邊 12 CSS px 外）點：唔算點寵物
  {
    hb = await E(() => __qa.pet.hitBox());
    const n0 = await E(() => (__glimmer.beh.journal || []).filter(j => j.ev === 'tap' && j.name === 'pet').length);
    await page.mouse.click(hb.css.x + hb.css.w + 12, hb.css.y + hb.css.h / 2); await E(() => __qa.pet.step(0.2));
    const n1 = await E(() => (__glimmer.beh.journal || []).filter(j => j.ev === 'tap' && j.name === 'pet').length);
    await page.mouse.click(hb.css.x + hb.css.w / 2, hb.css.y + hb.css.h / 2); await E(() => __qa.pet.step(0.2));
    const n2 = await E(() => (__glimmer.beh.journal || []).filter(j => j.ev === 'tap' && j.name === 'pet').length);
    ok(n1 === n0 && n2 === n0 + 1, '熱區外 12px 點唔算寵物；熱區中心點＝1 次', JSON.stringify([n0, n1, n2]));
  }

  console.log('# P2 回頭（D2）只限短 tap <300ms；長按唔觸發');
  const behind = async (holdMs) => {
    await E(() => { const b = __glimmer.beh; __qa.pet.force('idle'); __qa.pet.step(2); b.dir = 1; b.turn = null; b.lastTouch = b.t; b.petTaps.length = 0; }); await page.waitForTimeout(150);
    const h = await E(() => __qa.pet.hitBox()); const x = h.css.x + 4, y = h.css.y + h.css.h / 2;   // 寵物向右，點佢左邊（背後）
    const t0 = await E(() => ({ turn: __glimmer.beh.log.enters.turn || 0, hold: __glimmer.beh.log.enters.hold || 0, nz: __glimmer.beh.log.enters.nuzzleStart || 0 }));
    await page.mouse.move(x, y); await page.mouse.down(); await page.waitForTimeout(holdMs); await page.mouse.up(); await E(() => __qa.pet.step(0.3));
    const t1 = await E(() => ({ turn: __glimmer.beh.log.enters.turn || 0, hold: __glimmer.beh.log.enters.hold || 0, nz: __glimmer.beh.log.enters.nuzzleStart || 0, dir: __glimmer.beh.dir, press: __glimmer.lastPetPress }));
    return { turn: t1.turn - t0.turn, hold: t1.hold - t0.hold, nz: t1.nz - t0.nz, dir: t1.dir, press: t1.press };
  };
  let r = await behind(60); ok(r.turn === 1 && r.dir === -1 && r.press.short, `短 tap（${r.press.ms}ms）背後：回頭 1 次`, JSON.stringify(r));
  // s3（10-31）刻意改：長按 ≥0.4s 而家會開始 D3 磨蹭（nuzzle 轉向手指）→ 背後長按會面向手指；但仍然唔算 D2 回頭（turn 0）
  r = await behind(650); ok(r.turn === 0 && r.hold === 1 && !r.press.short && r.press.nuzzle && (r.nz === 1 ? r.dir === -1 : r.dir === 1), `長按（${r.press.ms}ms）背後：唔 D2 回頭（記 hold）；s3 磨蹭轉向手指（nuzzle ${r.nz}）`, JSON.stringify(r));
  r = await behind(250); ok(r.turn === 1 && r.press.ms < 300, `250ms 仍算短 tap：回頭`, JSON.stringify(r));

  console.log('# P2 拖動手指 → 眼神跟手指');
  {
    await E(() => { __qa.pet.force('idle'); __qa.pet.step(2); __glimmer.beh.dir = 1; __qa.pet.setGaze(null); });
    const h = await E(() => __qa.pet.hitBox()), cy = h.css.y + h.css.h / 2;
    await page.mouse.move(100, 640); await page.mouse.down();
    await page.mouse.move(20, cy, { steps: 6 }); await E(() => __qa.pet.step(0.3)); const gL = await E(() => __qa.pet.gaze());
    await page.mouse.move(370, cy, { steps: 8 }); await E(() => __qa.pet.step(0.3)); const gR = await E(() => __qa.pet.gaze());
    await page.mouse.move(195, 60, { steps: 6 }); await E(() => __qa.pet.step(0.3)); const gU = await E(() => __qa.pet.gaze());
    await page.mouse.up(); await E(() => __qa.pet.step(1.0)); const gA = await E(() => __qa.pet.gaze());
    ok(gL.src === 'finger' && gL.tx < -0.5 && (gL.q === 'L' || gL.q === 'CL'), '拖去左：src finger、望左（' + gL.q + '）', JSON.stringify(gL));
    ok(gR.src === 'finger' && gR.tx > 0.5 && (gR.q === 'R' || gR.q === 'CR'), '拖去右：望右（' + gR.q + '）', JSON.stringify(gR));
    ok(gU.src === 'finger' && gU.ty < -0.5, '拖去上：望上', JSON.stringify(gU));
    ok(gA.src !== 'finger', '放手後回復自動（' + gA.src + '）', JSON.stringify(gA));
    await shot('s1-gaze-drag');
  }

  console.log('# P2 開心閉眼 → 頭部微轉');
  {
    const res = await E(async () => {
      const b = __glimmer.beh, r = __glimmer.renderer; __qa.pet.force('idle'); __qa.pet.step(1); b.faceForce = { eyes: 'happy', mouth: 'smile' };
      const out = {};
      for (const q of ['L', 'R', 'C']) { __qa.pet.setGaze(q); __qa.pet.step(0.3); const h0 = r.faceStat.headTurn || 0; await new Promise(res => setTimeout(res, 200)); const l = r.faceStat.last || {}; out[q] = { head: l.headTurn || null, n: (r.faceStat.headTurn || 0) - h0, eyes: l.eyes, gaze: b.face.gaze, fh: b.face.head }; }
      b.faceForce = null; __qa.pet.setGaze(null); return out;
    });
    ok(res.L.n > 0 && res.R.n > 0 && res.L.head && res.R.head && res.L.head !== res.R.head && res.L.gaze === 'C', '開心閉眼（eyes_happy 只得 C）：望左／右 → 五官整組微移 1px（頭部微轉）', JSON.stringify(res));
    ok(res.C.n === 0 && !res.C.head, '望正中：唔轉', JSON.stringify(res.C));
  }
  await E(() => __qa.pet.pause(false));

  console.log('# QA3 日記提示文案');
  {
    const t = await E(() => { const s = __glimmer.state, now = __glimmer.now(); s.evs.diary = [{ id: 'gift', ts: now - 12.5 * 86400e3, grains: 3, mood: 0 }]; return Glimmer.events.diaryWarn(s, now); });
    await E(() => document.getElementById('diary').click()); await page.waitForTimeout(300);
    const txt = await E(() => { const w = document.querySelector('[data-testid=diary-warn]'); return w ? w.textContent : null; });
    ok(t === 1 && txt && /2 日後作廢/.test(txt) && !/就快過期/.test(txt), '日記提示：「' + txt + '」', txt);
    await shot('s1-diary-warn'); await closeModals(E);
    const src = await E(() => fetch('src/main.js').then(r => r.text())); ok(/2 日後作廢/.test(src) && !/就快過期/.test(src), '開 app toast 文案同步改「2 日後作廢」');
  }

  console.log('# H3 雨層細雨環境聲（short → loop，WebAudio）');
  {
    await page.mouse.click(30, 400);   // 解鎖 AudioContext（用戶手勢）
    await E(() => Glimmer.audio.Engine.ready); await page.waitForTimeout(300);
    const st0 = await E(() => Glimmer.audio.Engine.status()); ok(st0.ctx === 'running', 'AudioContext running', JSON.stringify(st0));
    await E(() => { __qa.dev.open(); }); await page.click('[data-testid=dev-scene-H3rain]', { force: true });   // 開發模式切雨
    await page.waitForFunction(() => { const r = Glimmer.audio.Engine.rainStatus(); return r.on && r.loop; }, null, { timeout: 8000 }).catch(() => { });
    const a = await E(() => Glimmer.audio.Engine.rainStatus());
    const h = a.hist[a.hist.length - 1] || {};
    ok(a.on && h.name === 'amb:rain:start', '開發模式切 H3 雨：雨聲開始', JSON.stringify(a));
    ok(a.short && a.short.node === 'AudioBufferSourceNode' && a.short.loop === false && Math.abs(a.short.bufDur - 6) < 0.01, 'short（6s）用 BufferSource 播一次', JSON.stringify(a.short));
    ok(a.loop && a.loop.node === 'AudioBufferSourceNode' && a.loop.loop === true && a.loop.loopStart === 0 && Math.abs(a.loop.loopEnd - a.loop.bufDur) < 1e-3 && Math.abs(a.loop.bufDur - 24.706) < 0.01, 'loop（24.706s）＝AudioBufferSourceNode.loop＝true、loopStart 0、loopEnd＝buffer 長（sample-accurate）', JSON.stringify(a.loop));
    ok(Math.abs(a.loop.t0 - a.short.t0 - 1.5) < 0.01 && h.xfadeSec >= 1 && h.xfadeSec <= 2, `short 開始後 ${(a.loop.t0 - a.short.t0).toFixed(2)}s crossfade（${h.xfadeSec}s）入 loop`, JSON.stringify(h));
    ok(a.audioEls === 0, '冇 <audio> 元素', a.audioEls);
    await page.waitForTimeout(800); const g1 = await E(() => Glimmer.audio.Engine.rainStatus());
    await page.waitForTimeout(2600); const g2 = await E(() => Glimmer.audio.Engine.rainStatus());
    ok(g2.loop.gain > 0.9 && g2.short.gain < 0.05 && g1.loop.gain < 0.05, `crossfade：0.8s loop ${g1.loop.gain} → 3.4s loop ${g2.loop.gain}／short ${g2.short.gain}`, JSON.stringify([g1.loop, g2.loop, g2.short]));
    await shot('s1-rain-audio-devpanel');
    await page.click('[data-testid=dev-scene-H3]', { force: true }); await page.waitForTimeout(400);   // 停雨
    const b = await E(() => Glimmer.audio.Engine.rainStatus()); const hs = b.hist[b.hist.length - 1] || {};
    ok(!b.on && hs.name === 'amb:rain:stop' && hs.fadeOutSec >= 1.5 && hs.fadeOutSec <= 2, `停雨：loop 淡出 ${hs.fadeOutSec}s`, JSON.stringify(b));
    ok(b.fading && b.fading.loopGain > 0.2 && b.fading.loopGain < 1, `淡出中（0.4s 後 gain ${b.fading && b.fading.loopGain}）`, JSON.stringify(b.fading));
    await page.waitForTimeout(1800); const c = await E(() => Glimmer.audio.Engine.rainStatus());
    ok(!c.fading, '淡出完成，節點已釋放', JSON.stringify(c.fading));
    // 自動：13:00 落雨（天氣 hook）一樣觸發
    await E(() => { __qa.dev.scene('auto'); __glimmer.hourOverride = 13; __qa.hd2d.weather('rain'); }); await page.waitForFunction(() => Glimmer.audio.Engine.rainStatus().on, null, { timeout: 6000 }).catch(() => { });
    ok(await E(() => Glimmer.audio.Engine.rainStatus().on), 'Auto＋13:00 落雨（H3rain）：雨聲自動開');
    await E(() => { __qa.hd2d.weather(null); }); await page.waitForTimeout(3200);
    ok(!(await E(() => Glimmer.audio.Engine.rainStatus().on)), '雨停（轉返 H3）：雨聲停');
  }

  ok(errs.length === 0, 'console 無錯誤／警告', errs.slice(0, 5).join(' | '));
  await browser.close();
  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
