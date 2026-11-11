/* 《微光小圃》 e2e-3d — #89 3D 花園 H1／H1.2／H1.3／H1.4／H1.5：場景載入、遮擋、觸摸、日夜光、畫質切換、?3d=0、可見區、網格、behavior.step 行速。
   截圖 → SHOTS；3d-h1-*.png、3d-h11-*.png、3d-h13-*.png、3d-h14-*.png、3d-h15-*.png。fps／p95 用 CDP 4× CPU。node tests/e2e-3d.js */
const path = require('path');
const fs = require('fs');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8510/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
const APKSHOTS = process.env.APKSHOTS || '/workspace/apk/';
fs.mkdirSync(SHOTS, { recursive: true });
fs.mkdirSync(APKSHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const QS3 = '3d=high&q=high&seed=21&ev=0&hour=13';

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME || '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', '--ignore-gpu-blocklist', '--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl']
  });
  const errs = [];
  async function boot(vp, qs, dpr) {
    const ctx = await browser.newContext({ viewport: { width: vp[0], height: vp[1] }, deviceScaleFactor: dpr || 1 });
    const page = await ctx.newPage();
    page.on('pageerror', e => errs.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.text()); });
    const q = qs == null ? QS3 : qs;
    await page.goto(BASE + '?' + q);
    await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); });
    await page.goto(BASE + '?' + q);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad);
    await page.evaluate(() => __glimmer.liveLoad);
    await page.evaluate(() => __glimmer.houseLoad).catch(() => { });
    await page.evaluate(() => __glimmer.s2Load).catch(() => { });
    return { ctx, page, E: (f, a) => page.evaluate(f, a), W: (ms) => page.waitForTimeout(ms) };
  }
  const adultR = (E) => E(() => {
    const s = __glimmer.state; s.stage = 'adult'; s.form = 'radiant'; s.sleeping = false;
    Object.assign(s.needs, { mood: 80, energy: 100, hunger: 100, clean: 100 }); s.poops = 0;
    if (__qa.pet && __qa.pet.force) __qa.pet.force('stay');
    if (__glimmer.beh) __glimmer.beh.x = 0;
  });
  const clearTips = (E) => E(() => {
    ['toast', 'u62tip', 'bubble', 's12voice'].forEach(function (id) {
      const e = document.getElementById(id); if (!e) return;
      e.style.display = 'none'; if (id === 'toast' || id === 'u62tip') e.textContent = '';
    });
    document.querySelectorAll('#l6dlay .bub, .bub.on').forEach(function (e) { e.remove(); });
  });
  const waitG3 = async (E, W, ms) => {
    const t0 = Date.now();
    while (Date.now() - t0 < (ms || 15000)) {
      const st = await E(() => ({ ready: !!(window.__qa && __qa.g3d && __qa.g3d.ready()), on: !!(window.__qa && __qa.g3d && __qa.g3d.on()), err: window.__qa && __qa.g3d && __qa.g3d.error && __qa.g3d.error(), meshes: window.__qa && __qa.g3d && __qa.g3d.meshes && __qa.g3d.meshes() }));
      if (st.ready || st.err) return st;
      await W(200);
    }
    return await E(() => ({ ready: !!(window.__qa && __qa.g3d && __qa.g3d.ready()), on: !!(window.__qa && __qa.g3d && __qa.g3d.on()), err: window.__qa && __qa.g3d && __qa.g3d.error && __qa.g3d.error(), meshes: window.__qa && __qa.g3d && __qa.g3d.meshes && __qa.g3d.meshes(), timeout: true }));
  };

  // ───────── A. 場景載入 ─────────
  console.log('A. 場景載入（17 mesh、WebGL ready）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E);
    const st = await waitG3(E, W, 20000); await W(800);
    ok(st.ready && !st.err, '3D 載入成功、冇 error', st);
    ok(st.meshes === 17, '17 件 mesh', st);
    ok(st.on && await E(() => __qa.g3d.on() && __qa.g3d.quality() === 'high'), '預設 ?3d=high → on／high', await E(() => ({ on: __qa.g3d.on(), q: __qa.g3d.quality() })));
    const draws = await E(() => __glimmer.g3d && __glimmer.g3d.stat && __glimmer.g3d.stat.draws);
    ok(draws > 0, '已經有畫至少一幀', draws);
    const pet = await E(() => __qa.g3d.pet());
    ok(pet && pet.frame && /front_idle|fallback/.test(pet.frame), 'radiant dir4 idle 幀', pet);
    await ctx.close(); }

  // ───────── B. 遮擋 ─────────
  console.log('B. 遮擋（寵物行到物件後被擋住）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(400);
    const front = await E(() => { __qa.g3d.forcePet({ x: 0, z: 0 }); return null; });
    await W(250);
    const a = await E(() => ({ occ: __qa.g3d.occluded(0, 0), pet: __qa.g3d.pet() }));
    ok(!a.occ, '前排 (0,0) 唔被遮', a);
    await E(() => __qa.g3d.forcePet({ x: -88, z: -80 })); await W(300);
    const b = await E(() => ({ occ: __qa.g3d.occluded(-88, -80), pet: __qa.g3d.pet() }));
    ok(b.occ, '樹後 (−88,−80) 被遮', b);
    await E(() => __qa.g3d.forcePet({ x: 82.5, z: -110 })); await W(300);
    const c = await E(() => ({ occ: __qa.g3d.occluded(82.5, -110), pet: __qa.g3d.pet() }));
    ok(c.occ, '小屋後 (82.5,−110) 被遮', c);
    await E(() => __qa.g3d.forcePet(null));
    await ctx.close(); }

  // ───────── C. 觸摸命中 ─────────
  console.log('C. 觸摸命中（3D 投影 AABB）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(500);
    await E(() => { if (__qa.pet && __qa.pet.force) __qa.pet.force('stay'); if (__glimmer.beh) __glimmer.beh.x = 0; __qa.g3d.forcePet({ x: 0, z: 0 }); });
    await W(400);
    const box = await E(() => { const pd = __qa.g3d.petDraw(), hit = __qa.pet.hitBox(); return { pd, hit, in: __qa.g3d.petHit(pd.x + pd.w / 2, pd.y + pd.h / 2), out: __qa.g3d.petHit(10, 10) }; });
    ok(box.pd && box.pd.w > 8 && box.pd.h > 8 && box.pd.g3d, 'petDraw 有 3D AABB', box.pd);
    ok(box.in && !box.out, '中心命中、邊位唔中', { in: box.in, out: box.out });
    ok(box.hit && box.hit.css && box.hit.css.w > 8, 'hitBox CSS 跟 3D petDraw', box.hit && box.hit.css);
    await E(() => { window.__patN = 0; const X = Glimmer.sys12, f = X.notePat; X.notePat = function () { window.__patN++; return f.apply(this, arguments); }; });
    const css = box.hit.css;
    await page.mouse.click(css.x + css.w / 2, css.y + css.h / 2);
    await W(500);
    const poked = await E(() => window.__patN > 0 || (__glimmer.beh && __glimmer.beh.gest && /poke|pat|touch/.test(__glimmer.beh.gest.key || '')) || (__glimmer.renderer && __glimmer.renderer.pet && __glimmer.renderer.pet.act));
    ok(!!poked || await E(() => window.__patN) >= 1, '撳 3D 寵物命中（摸／戳）', await E(() => ({ pat: window.__patN, gest: __glimmer.beh && __glimmer.beh.gest, act: __glimmer.renderer && __glimmer.renderer.pet && __glimmer.renderer.pet.act })));
    await E(() => __qa.g3d.forcePet(null));
    await ctx.close(); }

  // ───────── D. 日夜光 ─────────
  console.log('D. 日夜光（window_side／fill／sun）');
  { const { ctx, page, E, W } = await boot([390, 844], '3d=high&q=high&seed=21&ev=0&hour=13'); await adultR(E); await waitG3(E, W); await W(400);
    await E(() => { __glimmer.hourOverride = 13; }); await W(400);
    const day = await E(() => { const L = __qa.g3d.lit(), n = __qa.g3d.night(); return { n, sun: L && L.sun, fill: L && L.fill, ws: L && L.byId && L.byId.window_side, w: L && L.byId && L.byId.window, lamp: L && L.byId && L.byId.lamp }; });
    ok(day.n === 0, '13:00 nightMix＝0', day);
    ok(Math.abs(day.fill - 0.38) < 0.001, '日 fill＝0.38', day.fill);
    ok(day.ws === 0 && day.w === 0 && day.lamp === 0, '日 window_side／window／lamp＝0', day);
    ok(day.sun > 0.8, '日 sun 近 1', day.sun);
    await page.screenshot({ path: SHOTS + '3d-h1-day.png' });
    fs.copyFileSync(SHOTS + '3d-h1-day.png', APKSHOTS + '3d-h1-day.png');
    await E(() => { __glimmer.hourOverride = 22; }); await W(500);
    const night = await E(() => { const L = __qa.g3d.lit(), n = __qa.g3d.night(); return { n, sun: L && L.sun, fill: L && L.fill, ws: L && L.byId && L.byId.window_side, w: L && L.byId && L.byId.window, lamp: L && L.byId && L.byId.lamp }; });
    ok(night.n === 1, '22:00 nightMix＝1', night);
    ok(night.fill === 0, '夜 fill＝0（唔出影）', night.fill);
    ok(Math.abs(night.ws - 0.7) < 0.001, '夜 window_side＝0.7', night.ws);
    ok(Math.abs(night.w - 0.8) < 0.001, '夜 window＝0.8', night.w);
    ok(night.sun < 0.3, '夜 sun 低', night.sun);
    await page.screenshot({ path: SHOTS + '3d-h1-night.png' });
    fs.copyFileSync(SHOTS + '3d-h1-night.png', APKSHOTS + '3d-h1-night.png');
    await ctx.close(); }

  // ───────── E. 畫質切換 ─────────
  console.log('E. 畫質切換（high／mid／low）＋開發者模式');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(300);
    ok(await E(() => __qa.g3d.quality() === 'high' && __qa.g3d.on()), '開始 high');
    await E(() => __qa.g3d.setQuality('mid')); await W(400);
    ok(await E(() => __qa.g3d.quality() === 'mid' && __qa.g3d.on()), 'mid 仍然 3D on');
    await E(() => __qa.g3d.setQuality('low')); await W(400);
    const low = await E(() => ({ q: __qa.g3d.quality(), on: __qa.g3d.on(), hd: !!(__qa.hd2d && (__qa.hd2d.on ? __qa.hd2d.on() : true)) }));
    ok(low.q === 'low' && !low.on, 'low＝2D 後備（g3d.off）', low);
    await E(() => { __qa.g3d.setQuality('high'); if (!__qa.g3d.ready()) return __qa.g3d.reload(); }); await W(800);
    const back = await waitG3(E, W, 10000);
    ok(back.ready && await E(() => __qa.g3d.on() && __qa.g3d.quality() === 'high'), '切返 high 恢復 3D', back);
    await E(() => { if (__qa.devmode && __qa.devmode.setShown) __qa.devmode.setShown(true); }); await W(100);
    await page.locator('[data-testid=dev-btn]').click().catch(() => { });
    await W(400);
    ok(await page.locator('[data-testid=dev-sec-g3d]').count() === 1, '開發者模式有「3D 花園 H1」分組');
    const keys = await E(() => [...document.querySelectorAll('[data-testid^=dev-g3d-]')].map(e => e.dataset.testid));
    ok(keys.includes('dev-g3d-high') && keys.includes('dev-g3d-sway') && keys.includes('dev-g3d-follow') && keys.includes('dev-g3d-perf'), '畫質／擺鏡／跟拍／fps 面板掣', keys);
    await E(() => __qa.g3d.showPerf(true)); await W(200);
    ok(await E(() => { const el = document.querySelector('[data-testid=g3d-perf]'); return el && getComputedStyle(el).display !== 'none'; }), 'fps／耗電面板顯示');
    await ctx.close(); }

  // ───────── F. ?3d=0 返 2D ─────────
  console.log('F. ?3d=0 返 2D（跟舊 HD-2D）');
  { const { ctx, page, E, W } = await boot([390, 844], '3d=0&q=high&seed=21&ev=0&hour=13'); await adultR(E); await W(1200);
    const st = await E(() => ({
      on: !!(window.__qa && __qa.g3d && __qa.g3d.on()),
      q: window.__qa && __qa.g3d && __qa.g3d.quality && __qa.g3d.quality(),
      v3: !!(window.__qa && __qa.v3 && __qa.v3.on && __qa.v3.on()),
      hd: window.__qa && __qa.hd2d && (typeof __qa.hd2d.on === 'function' ? __qa.hd2d.on() : true)
    }));
    ok(!st.on && st.q === 'low', '?3d=0：3D 關、quality＝low', st);
    ok(st.v3, '?3d=0：V3／HD-2D 仍然開', st);
    await ctx.close(); }

  // ───────── G. 窄屏 ─────────
  console.log('G. 窄屏 360×640 截圖');
  { const { ctx, page, E, W } = await boot([360, 640], QS3, 1); await adultR(E); await waitG3(E, W); await W(800);
    await E(() => { __glimmer.hourOverride = 13; __qa.g3d.setSway(false); __qa.g3d.setFollow(true); }); await W(600);
    await page.screenshot({ path: SHOTS + '3d-h1-narrow.png' });
    fs.copyFileSync(SHOTS + '3d-h1-narrow.png', APKSHOTS + '3d-h1-narrow.png');
    ok(fs.existsSync(APKSHOTS + '3d-h1-narrow.png'), '窄屏截圖已寫');
    await ctx.close(); }

  // ───────── H. 4× CPU fps／rAF p95 ─────────
  console.log('H. 中端機 4× CPU 慢 fps／callback p95');
  let fpsReport = null;
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(400);
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await E(() => { __qa.g3d.showPerf(true); __glimmer.hourOverride = 13; });
    const p95of = (arr) => { const a = arr.slice().sort((x, y) => x - y); if (!a.length) return 0; const i = Math.min(a.length - 1, Math.max(0, Math.ceil(a.length * 0.95) - 1)); return +a[i].toFixed(2); };
    const measure = async (q) => {
      await E((q) => { if (q === 'low') { __qa.g3d.setQuality('low'); } else { __qa.g3d.setQuality(q); if (!__qa.g3d.ready()) return __qa.g3d.reload(); } }, q);
      if (q !== 'low') await waitG3(E, W, 8000);
      await W(400);
      await E(() => {
        window.__cbMs = [];
        if (!window.__cbWrap) {
          const orig = window.requestAnimationFrame.bind(window);
          window.__cbWrap = true;
          window.requestAnimationFrame = function (cb) {
            return orig(function (t) { const t0 = performance.now(); try { cb(t); } finally { if (window.__cbMs) window.__cbMs.push(performance.now() - t0); } });
          };
        }
        window.__cbMs = [];
      });
      await W(2800);
      const raw = await E(() => (window.__cbMs || []).slice(8));  // 丟開頭幾幀
      const samples = raw.filter(n => typeof n === 'number' && n >= 0 && n < 80);
      const sorted = samples.slice().sort((x, y) => x - y);
      const p50v = sorted.length ? +sorted[Math.floor(sorted.length * 0.5)].toFixed(2) : 0;
      const p95v = p95of(samples);
      const max = samples.length ? +Math.max(...samples).toFixed(2) : 0;
      const over = samples.filter(n => n > 4.5).length;
      const live = await E(() => ({ q: __qa.g3d.quality(), on: __qa.g3d.on(), fps: __qa.g3d.fps(), ms: __qa.g3d.lastMs(), soft: __qa.g3d.shadowSoft && __qa.g3d.shadowSoft(), sz: __qa.g3d.shadowSize && __qa.g3d.shadowSize() }));
      return { q: live.q, on: live.on, n: samples.length, p50: p50v, p95: p95v, max, over, fps: live.fps, ms: live.ms, soft: live.soft, sz: live.sz };
    };
    const high = await measure('high');
    const mid = await measure('mid');
    const low = await measure('low');
    await E(() => { __qa.g3d.setQuality('high'); if (!__qa.g3d.ready()) return __qa.g3d.reload(); });
    await waitG3(E, W, 8000);
    fpsReport = { throttle: '4x', high, mid, low };
    ok(high.on && mid.on && !low.on, '4× CPU：high／mid 仍然 3D，low＝2D', fpsReport);
    console.log('  fps 4× CPU p95: ' + JSON.stringify(fpsReport));
    const fpsPath = process.env.FPS4X || path.join('/tmp', 'g3d-fps-4x.json');
    fs.writeFileSync(fpsPath, JSON.stringify(fpsReport, null, 2));
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 }).catch(() => { });
    await ctx.close(); }

  // ───────── I. H1.1 寵物直立、XZ 方向、遮擋截圖 ─────────
  console.log('I. H1.1 寵物直立／四方向／行到物件後');
  const H11 = process.env.H11SHOTS || '/workspace/apk/';
  fs.mkdirSync(H11, { recursive: true });
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(400);
    await E(() => { __glimmer.hourOverride = 13; __qa.g3d.setSway(false); __qa.g3d.setFollow(true); if (__glimmer.beh) { __glimmer.beh.x = 0; __glimmer.beh.z = 0; } });
    ok(await E(() => __qa.g3d.petFlipY()) === true, 'pet 貼圖 flipY＝true（唔倒轉）');
    await E(() => __qa.g3d.forcePet({ x: 0, z: 20, facing: { dir: 'front', flip: false, clip: 'idle' }, moving: false })); await W(500);
    const up = await E(() => {
      const pd = __qa.g3d.petDraw();
      const k = __glimmer.renderer.k || 2;
      const ctx2 = __glimmer.renderer.ctx;
      const avg = (y0, y1) => {
        let n = 0, sat = 0, lum = 0;
        for (let y = y0; y < y1; y += 2) for (let x = pd.x + 6; x < pd.x + pd.w - 6; x += 2) {
          const d = ctx2.getImageData(Math.round(x * k), Math.round(y * k), 1, 1).data;
          const mx = Math.max(d[0], d[1], d[2]), mn = Math.min(d[0], d[1], d[2]);
          sat += mx - mn; lum += (d[0] + d[1] + d[2]) / 3; n++;
        }
        return n ? { sat: sat / n, lum: lum / n } : { sat: 0, lum: 0 };
      };
      const top = avg(pd.y + 2, pd.y + pd.h * 0.42);
      const bot = avg(pd.y + pd.h * 0.62, pd.y + pd.h - 2);
      return { pd, top, bot, flip: __qa.g3d.petFlipY() };
    });
    // 直立：上半（頭／身）飽和度或亮度結構同下半（腳）唔應該倒轉成「面喺腳位」——頭比較亮／較有色。
    ok(up.pd && up.pd.h > 16 && up.top.sat + up.top.lum > 0, '投影 AABB 可採樣', up);
    ok(up.top.sat >= up.bot.sat * 0.7, '上半身唔似倒轉（頭／身喺上）', up);
    await page.screenshot({ path: SHOTS + '3d-h11-day.png' });
    fs.copyFileSync(SHOTS + '3d-h11-day.png', H11 + '3d-h11-day.png');

    await E(() => __qa.g3d.forcePet({ x: 0, z: 55, facing: { dir: 'front', flip: false, clip: 'walk' }, dx: 0, dz: 8, moving: true })); await W(400);
    const fr = await E(() => __qa.g3d.pet());
    ok(fr.frame && /front_/.test(fr.frame), '向鏡頭行＝front 幀', fr);
    await page.screenshot({ path: SHOTS + '3d-h11-walk-front.png' });
    fs.copyFileSync(SHOTS + '3d-h11-walk-front.png', H11 + '3d-h11-walk-front.png');

    await E(() => __qa.g3d.forcePet({ x: 40, z: 20, facing: { dir: 'side', flip: false, clip: 'walk' }, dx: 8, dz: 0, moving: true })); await W(400);
    const sd = await E(() => __qa.g3d.pet());
    ok(sd.frame && /side_/.test(sd.frame) && !(sd.facing && sd.facing.flip), '向右行＝side', sd);
    await page.screenshot({ path: SHOTS + '3d-h11-walk-side.png' });
    fs.copyFileSync(SHOTS + '3d-h11-walk-side.png', H11 + '3d-h11-walk-side.png');

    await E(() => __qa.g3d.forcePet({ x: -40, z: 20, facing: { dir: 'side', flip: true, clip: 'walk' }, dx: -8, dz: 0, moving: true })); await W(400);
    const sl = await E(() => __qa.g3d.pet());
    ok(sl.frame && /side_/.test(sl.frame) && sl.facing && sl.facing.flip, '向左行＝side 鏡像', sl);
    await page.screenshot({ path: SHOTS + '3d-h11-walk-side-left.png' });
    fs.copyFileSync(SHOTS + '3d-h11-walk-side-left.png', H11 + '3d-h11-walk-side-left.png');

    await E(() => __qa.g3d.forcePet({ x: 0, z: -20, facing: { dir: 'back', flip: false, clip: 'walk' }, dx: 0, dz: -8, moving: true })); await W(400);
    const bk = await E(() => __qa.g3d.pet());
    ok(bk.frame && /back_/.test(bk.frame), '向屋行＝back 幀', bk);
    await page.screenshot({ path: SHOTS + '3d-h11-walk-back.png' });
    fs.copyFileSync(SHOTS + '3d-h11-walk-back.png', H11 + '3d-h11-walk-back.png');

    await E(() => __qa.g3d.forcePet({ x: 82.5, z: -110, facing: { dir: 'back', flip: false, clip: 'idle' }, moving: false })); await W(500);
    const oc = await E(() => ({ occ: __qa.g3d.occluded(82.5, -110), pet: __qa.g3d.pet() }));
    ok(oc.occ, '行到小屋後被遮擋', oc);
    await page.screenshot({ path: SHOTS + '3d-h11-occluded.png' });
    fs.copyFileSync(SHOTS + '3d-h11-occluded.png', H11 + '3d-h11-occluded.png');
    ok(fs.existsSync(H11 + '3d-h11-day.png') && fs.existsSync(H11 + '3d-h11-occluded.png') && fs.existsSync(H11 + '3d-h11-walk-front.png') && fs.existsSync(H11 + '3d-h11-walk-side.png') && fs.existsSync(H11 + '3d-h11-walk-back.png'), 'H1.1 截圖已寫');

    // 實際 XZ hook：從原點 step 去樹後唔入 footprint
    const pathOk = await E(() => {
      let x = 0, z = 0, pi = 0, hit = false, arr = false;
      const objs = __glimmer.g3d.objects, G = Glimmer.garden3d;
      const path = G.buildPath(objs, 0, 0, -88, -80, 10, G.RANGE3.x, G.RANGE3.z);
      for (let i = 0; i < 2000; i++) {
        const fol = G.followPath(objs, x, z, path, { x: -88, z: -80 }, 2, 10, G.RANGE3.x, G.RANGE3.z, pi);
        pi = fol.pi; x = fol.step.x; z = fol.step.z;
        if (G.blocked(objs, x, z, 10).length) { hit = true; break; }
        if (fol.step.arrived) { arr = true; break; }
      }
      return { arr, hit, x, z };
    });
    ok(pathOk.arr && !pathOk.hit, '執行期 A* 可由原點行到樹後', pathOk);
    await E(() => __qa.g3d.forcePet(null));
    await ctx.close(); }

  // ───────── J. H1.2 構圖／網格／行速／hook／花盆遮擋 ─────────
  console.log('J. H1.2 可見區、網格預設關、behavior.step 行 3D、花盆遮擋');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(400);
    await E(() => { __glimmer.hourOverride = 13; __qa.g3d.setSway(false); __qa.g3d.setFollow(true); if (__glimmer.beh) { __glimmer.beh.x = 0; __glimmer.beh.z = 0; } });
    const hooks = await E(() => ({
      onBeh: !!(Glimmer.data.PARAMS.beh && typeof Glimmer.data.PARAMS.beh.g3dWalk === 'function'),
      onParent: typeof Glimmer.data.PARAMS.g3dWalk === 'function',
      grid: __qa.g3d.gridOn(),
      look: __qa.g3d.look && __qa.g3d.look(),
      vis: __qa.g3d.vis && __qa.g3d.vis()
    }));
    ok(hooks.onBeh && !hooks.onParent, 'g3dWalk 等 hook 掛喺 PARAMS.beh', hooks);
    ok(hooks.grid === false, '地面網格預設關', hooks);
    ok(hooks.look && Math.abs(hooks.look[0]) < 2 && Math.abs(hooks.look[2] + 72) < 2, '跟拍建立鏡頭 look≈[0,30,-72]', hooks.look);
    const visLand = await E(() => {
      const ids = ['tree', 'fence', 'lamp', 'cottage'];
      const vis = __qa.g3d.vis();
      const g = __glimmer.g3d;
      const out = {};
      ids.forEach(id => {
        const m = g.meshObj && g.meshObj[id];
        if (!m) { out[id] = { missing: true }; return; }
        const p = g.project(m.position.x, (m.position.y || 0) + 8, m.position.z);
        out[id] = { x: p.x, y: p.y, in: p.x >= vis.x - 8 && p.x <= vis.x + vis.w + 8 && p.y >= vis.y - 12 && p.y <= vis.y + vis.h + 24 };
      });
      return out;
    });
    ok(visLand.tree && visLand.tree.in && visLand.fence && visLand.fence.in && visLand.lamp && visLand.lamp.in && visLand.cottage && visLand.cottage.in, '樹／籬笆／燈柱／屋都喺可見區', visLand);
    const gridToggle = await E(() => { const a = __qa.g3d.gridOn(); const b = __qa.g3d.setGrid(true); const c = __qa.g3d.gridOn(); __qa.g3d.setGrid(false); return { a: a, b: b, c: c, off: __qa.g3d.gridOn() }; });
    ok(gridToggle.a === false && gridToggle.c === true && gridToggle.off === false, '開發者模式可開關地面網格', gridToggle);

    const walked = await E(() => {
      const BEH = Glimmer.behavior, b = __glimmer.beh;
      b.x = 0; b.z = 0; b.tx = 20; b.tz = 36; b.speed = Glimmer.data.PARAMS.beh.walkSpeed; b.state = 'walk'; b.phase = '';
      const ctx = { s: __glimmer.state, pw: {}, sun: 1, override: null, event: null };
      const t0 = b.t;
      for (let i = 0; i < 90; i++) BEH.step(b, ctx);
      return { x: b.x, z: b.z, dt: b.t - t0, state: b.state };
    });
    ok(walked.z > 4, 'e2e 經 behavior.step 行 3D（z 改變）', walked);

    const pot = await E(() => {
      __qa.g3d.forcePet({ x: 49, z: 8, moving: false });
      const behind = __qa.g3d.occluded(49, 8);
      const front = (function () { __qa.g3d.forcePet({ x: 49, z: 50, moving: false }); return __qa.g3d.occluded(49, 50); }());
      __qa.g3d.forcePet(null);
      return { behind: behind, front: front };
    });
    await W(200);
    ok(pot.behind && !pot.front, '花盆後遮擋（y 取 8／16／24，唔再永遠 false）', pot);

    const lostFn = await E(() => typeof __qa.g3d.lost === 'function' && __qa.g3d.lost() === false);
    ok(lostFn, 'webglcontextlost 之後 on() 會關（hook 存在、初始未 lost）');

    const frameNo = await E(() => {
      const R = __glimmer.renderer; const a = R.frameNo;
      if (R.frame) R.frame(0.016, { state: __glimmer.state, beh: __glimmer.beh, hour: 13, quality: 'high', mode: 'garden', light: null });
      return { a: a, b: R.frameNo, blit: !!(R.petBlit && R.petBlit.fn === R.frameNo) };
    });
    ok(frameNo.b === frameNo.a + 1, 'render.frame 會 this.frameNo++（唔再吞入註解）', frameNo);

    await ctx.close(); }

  // ───────── K. H1.3 自主行、屎、細佬、2D 清單、影圖 ─────────
  console.log('K. H1.3／H1.4 自主行／屎優先／影子／雨／影圖');
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(500);
    const qset = await E(() => ({ mid: Glimmer.garden3d.QSET.mid, high: Glimmer.garden3d.QSET.high, midLive: (__qa.g3d.setQuality('mid'), { ev: __qa.g3d.shadowEvery(), sz: __qa.g3d.shadowSize(), soft: __qa.g3d.shadowSoft() }), highLive: (__qa.g3d.setQuality('high'), { ev: __qa.g3d.shadowEvery(), sz: __qa.g3d.shadowSize(), soft: __qa.g3d.shadowSoft() }) }));
    ok(qset.mid.shadow === 256 && qset.mid.shadowEvery === 2 && qset.high.shadow === 1024 && qset.high.shadowEvery === 3 && qset.high.softShadow === false, 'QSET mid 256／每 2 幀、high 1024／每 3 幀／關 soft', qset);
    ok(qset.midLive.sz === 256 && qset.midLive.ev === 2 && qset.highLive.sz === 1024 && qset.highLive.ev === 3 && qset.highLive.soft === false && qset.midLive.soft === false, '執行期 mid 影圖／shadowEvery／high 1024／PCF', qset);
    ok(qset.high.dpr === 1 && qset.mid.dpr === 1, 'QSET dpr 上限 high／mid 1', qset);
    await E(() => __qa.g3d.setQuality('high')); await W(400);
    const sz0 = await E(() => ({ n: __qa.g3d.setSizeN(), vs: __qa.g3d.viewSize() }));
    await W(800);
    const sz1 = await E(() => ({ n: __qa.g3d.setSizeN(), vs: __qa.g3d.viewSize() }));
    ok(sz1.vs && sz1.vs.w === 195 && sz1.vs.h === 422, 'high WebGL 尺寸受 dpr 1 上限（195×422 整數倍）', sz1);
    ok(sz1.n === sz0.n, '尺寸／dpr 冇變就唔再 setSize', { sz0, sz1 });
    await E(() => { __qa.g3d.setQuality('mid'); if (!__qa.g3d.ready()) return __qa.g3d.reload(); });
    await waitG3(E, W, 8000); await W(400);
    const midVs = await E(() => __qa.g3d.viewSize());
    ok(midVs && midVs.w === 195 && midVs.h === 422, 'mid WebGL 尺寸受 dpr 1 上限（195×422 整數倍）', midVs);
    await E(() => { __qa.g3d.setQuality('high'); if (!__qa.g3d.ready()) return __qa.g3d.reload(); });
    await waitG3(E, W, 8000); await W(200);

    const inv = await E(() => {
      const items = __qa.g3d.worldItems();
      const garden = items.filter(x => x.inGarden);
      const cv = document.createElement('canvas'); cv.width = 8; cv.height = 8;
      const src = { img: cv, sx: 0, sy: 0, sw: 8, sh: 8, px: 4, py: 8 };
      const list = garden.filter(x => x.id !== 'pet' && x.id !== 'pot' && x.id !== 'sunPatch' && x.id !== 'weather').map((x, i) => ({ id: 'inv-' + x.id, kind: x.id, x: (i - 5) * 8, z: 20, src: src, shadow: false, hit: false }));
      __qa.g3d.syncActors(list);
      const got = __qa.g3d.actors().map(a => a.kind);
      return { n: items.length, garden: garden.map(x => x.id), got: got, pet: !!__qa.g3d.pet(), meshes: __qa.g3d.meshes() };
    });
    const missing = inv.garden.filter(id => id !== 'pet' && id !== 'pot' && id !== 'sunPatch' && id !== 'weather' && inv.got.indexOf(id) < 0);
    ok(inv.n >= 20 && inv.pet && inv.meshes === 17 && missing.length === 0, '清單逐樣可入 3D actors（pet／pot／天氣另證）', { missing, garden: inv.garden, got: inv.got });

    const auto = await E(() => {
      const BEH = Glimmer.behavior, b = __glimmer.beh, FIX = 1 / 60;
      if (__qa.s2 && __qa.s2.test) __qa.s2.test('_kid');
      b.state = 'stay'; b.phase = ''; b.variant = null; b.sleeping = false; b.hushUntil = 0;
      b.lastWalkAt = (b.t || 0) - 10; b.stateT = 2; b.x = 0; b.z = 0; b.tx = 0; b.tz = 0;
      if (__qa.s2 && __qa.s2.kidX) { __qa.s2.kidX(12); __qa.s2.kidZ(8); }
      const p0 = { x: b.x, z: b.z || 0 };
      const k0 = (__qa.s2 && __qa.s2.st && __qa.s2.st().kid) || { x: 12, z: 8 };
      const ctx = { s: __glimmer.state, pw: {}, sun: 1, override: null, event: null };
      for (let i = 0; i < 30 * 60; i++) {
        BEH.step(b, ctx);
        if (__glimmer.s2Tick) __glimmer.s2Tick(FIX);
      }
      const k1 = (__qa.s2 && __qa.s2.st && __qa.s2.st().kid) || { x: 0, z: 0 };
      return { p0, p1: { x: b.x, z: b.z || 0, state: b.state }, k0, k1, kidPhase: __qa.s2 && __qa.s2.st && __qa.s2.st().save && __qa.s2.st().save.phase };
    });
    const pMove = Math.hypot(auto.p1.x - auto.p0.x, auto.p1.z - auto.p0.z);
    const kMove = Math.hypot((auto.k1.x || 0) - (auto.k0.x || 0), (auto.k1.z || 0) - (auto.k0.z || 0));
    ok(pMove > 8, '無 input 30 秒內寵物自主位移', { pMove, p0: auto.p0, p1: auto.p1 });
    ok(kMove > 8, '無 input 30 秒內細佬自主位移', { kMove, k0: auto.k0, k1: auto.k1, phase: auto.kidPhase });

    const poop = await E(() => {
      const s = __glimmer.state; s.poops = 2;
      const pw = __qa.g3d.poopWorld(0);
      if (__qa.s2 && __qa.s2.kidX && pw) { __qa.s2.kidX(pw.x); __qa.s2.kidZ(pw.z); }  // 細佬企喺屎上面，盒會包住
      const R = __glimmer.renderer;
      if (R.frame) R.frame(0.016, { state: s, beh: __glimmer.beh, hour: 13, quality: 'high', mode: 'garden', light: __glimmer.light, event: null });
      const acts = (__qa.g3d.actors() || []).filter(a => a.kind === 'poop');
      const box = acts[0] && __qa.g3d.actorBox(acts[0]);
      const hit = box && __qa.g3d.hitActor(box.x + box.w / 2, box.y + box.h * 0.6);
      const kinds = (__qa.g3d.actors() || []).map(a => a.kind);
      return { n: acts.length, hit: hit && hit.kind, box, before: s.poops, kinds, kid: !!(__qa.s2 && __qa.s2.st && __qa.s2.st().kid) };
    });
    ok(poop.n >= 1 && poop.hit === 'poop', '屎喺 3D 出現、hitActor 命中（細佬疊住都優先回屎）', poop);
    await E(() => { __glimmer.hourOverride = 13; });
    await clearTips(E); await W(200);
    await page.screenshot({ path: SHOTS + '3d-h14-poop-before.png' });
    fs.copyFileSync(SHOTS + '3d-h14-poop-before.png', APKSHOTS + '3d-h14-poop-before.png');
    // 逐舊清晒
    let left = poop.before;
    for (let n = 0; n < 4 && left > 0; n++) {
      const box = await E(() => {
        const R = __glimmer.renderer;
        if (R.frame) R.frame(0.016, { state: __glimmer.state, beh: __glimmer.beh, hour: 13, quality: 'high', mode: 'garden', light: __glimmer.light, event: null });
        const acts = (__qa.g3d.actors() || []).filter(a => a.kind === 'poop');
        const b = acts[0] && __qa.g3d.actorBox(acts[0]);
        if (!b) return null;
        const r = __glimmer.renderer.canvas.getBoundingClientRect();
        return { x: r.left + (b.x + b.w / 2) / 195 * r.width, y: r.top + (b.y + b.h * 0.6) / 422 * r.height, hit: (__qa.g3d.hitActor(b.x + b.w / 2, b.y + b.h * 0.6) || {}).kind };
      });
      if (!box) break;
      ok(box.hit === 'poop', '清屎第 ' + (n + 1) + ' 下 hitActor＝poop', box);
      await page.mouse.click(box.x, box.y);
      await W(350);
      left = await E(() => __glimmer.state.poops);
    }
    const after = await E(() => __glimmer.state.poops);
    ok(after === 0, '3D 撳屎清到 0', { before: poop.before, after });
    await clearTips(E); await W(150);
    await page.screenshot({ path: SHOTS + '3d-h14-poop-after.png' });
    fs.copyFileSync(SHOTS + '3d-h14-poop-after.png', APKSHOTS + '3d-h14-poop-after.png');

    // 6d 朋友影子：alphaTest 0.1、texture 半透明、3D 睇到
    const sh = await E(() => {
      const cv = document.createElement('canvas'); cv.width = 32; cv.height = 48;
      const g = cv.getContext('2d'); g.fillStyle = 'rgba(90,60,140,1)'; g.fillRect(8, 4, 16, 40);
      const src = { img: cv, sx: 0, sy: 0, sw: 32, sh: 48, px: 16, py: 48 };
      const list = [{ id: 'shadow-e2e', kind: 'shadow', x: 10, z: 36, src: src, alpha: 0.45, shadow: true, hit: true, w: 28, h: 40 }];
      __qa.g3d.syncActors(list);
      const R = __glimmer.renderer;
      if (R.frame) R.frame(0.016, { state: __glimmer.state, beh: __glimmer.beh, hour: 13, quality: 'high', mode: 'garden', light: __glimmer.light, event: null });
      const mat = __qa.g3d.actorMat('shadow-e2e');
      return mat;
    });
    ok(sh && sh.alphaTest <= 0.1 + 1e-6 && sh.transparent && sh.maxA > 0.2 && sh.maxA < 0.7, '6d 影子 material 半透明（alphaTest≤0.1、tex alpha≈0.45）', sh);
    await E(() => {
      if (__qa.l6d && __qa.l6d.dev) { const it = __qa.l6d.dev().items.find(i => i.k === 'visit'); if (it) it.run(); }
      if (__qa.l6d && __qa.l6d.layTick) __qa.l6d.layTick(true);
    });
    await clearTips(E); await W(700);
    const shLive = await E(() => {
      const acts = (__qa.g3d.actors() || []).filter(a => a.kind === 'shadow');
      const mats = acts.map(a => Object.assign({ id: a.id }, __qa.g3d.actorMat(a.id) || {}));
      return { n: acts.length, mats };
    });
    ok(shLive.n >= 1 && shLive.mats.every(m => m.transparent && m.alphaTest <= 0.1 + 1e-6), '花園朋友影子 3D 半透明畫到', shLive);
    await page.screenshot({ path: SHOTS + '3d-h14-friend-shadow.png' });
    fs.copyFileSync(SHOTS + '3d-h14-friend-shadow.png', APKSHOTS + '3d-h14-friend-shadow.png');

    // 雨
    const rain = await E(() => {
      if (__qa.g3d.setWeather) __qa.g3d.setWeather('rain');
      if (__qa.hd2d && __qa.hd2d.weather) __qa.hd2d.weather('rain');
      else { __glimmer.weather = 'rain'; if (__glimmer.wx) __glimmer.wx.manual = true; }
      const R = __glimmer.renderer;
      for (let i = 0; i < 12; i++) if (R.frame) R.frame(0.05, { state: __glimmer.state, beh: __glimmer.beh, hour: 13, quality: 'high', mode: 'garden', light: __glimmer.light, event: null });
      return __qa.g3d.rainInfo();
    });
    await W(500);
    await clearTips(E); await W(200);
    const rain2 = await E(() => __qa.g3d.rainInfo());
    ok(rain2 && rain2.visible && rain2.n >= 180 && rain2.size >= 4 && rain2.atten === false, '雨點可見、加大、螢幕像素', rain2);
    await page.screenshot({ path: SHOTS + '3d-h14-rain.png' });
    fs.copyFileSync(SHOTS + '3d-h14-rain.png', APKSHOTS + '3d-h14-rain.png');
    await E(() => { if (__qa.g3d.setWeather) __qa.g3d.setWeather(null); if (__qa.hd2d && __qa.hd2d.weather) __qa.hd2d.weather('clear'); else { __glimmer.weather = null; } });

    await E(() => { __glimmer.hourOverride = 13; __qa.g3d.forcePet({ x: 0, z: 20 }); if (__qa.s2 && __qa.s2.kidX) { __qa.s2.kidX(-20); __qa.s2.kidZ(16); } __glimmer.state.poops = 1; });
    await W(400);
    await page.screenshot({ path: SHOTS + '3d-h13-day.png' });
    fs.copyFileSync(SHOTS + '3d-h13-day.png', APKSHOTS + '3d-h13-day.png');
    await E(() => { __glimmer.hourOverride = 22; }); await W(500);
    await page.screenshot({ path: SHOTS + '3d-h13-night.png' });
    fs.copyFileSync(SHOTS + '3d-h13-night.png', APKSHOTS + '3d-h13-night.png');
    await E(() => { __glimmer.hourOverride = 13; __qa.g3d.forcePet({ x: 10, z: 30 }); }); await W(400);
    await page.screenshot({ path: SHOTS + '3d-h13-kid-poop.png' });
    fs.copyFileSync(SHOTS + '3d-h13-kid-poop.png', APKSHOTS + '3d-h13-kid-poop.png');
    await E(() => __qa.g3d.forcePet({ x: -88, z: -80 })); await W(400);
    const occ = await E(() => __qa.g3d.occluded(-88, -80));
    ok(occ, '寵物行到樹後被擋', occ);
    await page.screenshot({ path: SHOTS + '3d-h13-occluded.png' });
    fs.copyFileSync(SHOTS + '3d-h13-occluded.png', APKSHOTS + '3d-h13-occluded.png');
    ok(fs.existsSync(APKSHOTS + '3d-h13-day.png') && fs.existsSync(APKSHOTS + '3d-h13-night.png') && fs.existsSync(APKSHOTS + '3d-h13-kid-poop.png') && fs.existsSync(APKSHOTS + '3d-h13-occluded.png') && fs.existsSync(APKSHOTS + '3d-h14-poop-before.png') && fs.existsSync(APKSHOTS + '3d-h14-poop-after.png') && fs.existsSync(APKSHOTS + '3d-h14-friend-shadow.png') && fs.existsSync(APKSHOTS + '3d-h14-rain.png'), 'H1.3／H1.4 截圖已寫');
    await E(() => __qa.g3d.forcePet(null));
    await ctx.close(); }

  // ───────── L. H1.4 多 viewport 散步／朋友掣唔重疊 ─────────
  console.log('L. H1.4 360／390／412／768 散步掣同朋友掣唔重疊');
  for (const vp of [[360, 640], [390, 844], [412, 915], [768, 1024]]) {
    const { ctx, page, E, W } = await boot(vp); await adultR(E); await waitG3(E, W); await W(800);
    await E(() => { __glimmer.hourOverride = 13; if (__qa.l6d && __qa.l6d.railTick) __qa.l6d.railTick(); });
    await clearTips(E); await W(400);
    const o = await E(() => {
      const a = document.getElementById('l6dbtn'), b = document.getElementById('l6bbtn');
      if (__qa.l6d && __qa.l6d.railTick) __qa.l6d.railTick();
      const ov = (__qa.ui62 && __qa.ui62.overlap) ? __qa.ui62.overlap() : { n: 0, hits: [] };
      const hit = [];
      if (a && b) {
        const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        const inter = ra.left < rb.right && rb.left < ra.right && ra.top < rb.bottom && rb.top < ra.bottom;
        if (inter) hit.push({ ids: ['#l6dbtn', '#l6bbtn'], a: [ra.x, ra.y, ra.w || ra.width, ra.h || ra.height], b: [rb.x, rb.y, rb.width, rb.height] });
      }
      return { ids: { l6d: !!(a && a.style.display !== 'none'), l6b: !!(b && b.style.display !== 'none') }, hit, ovHits: (ov.hits || []).filter(h => /l6dbtn|l6bbtn/.test(JSON.stringify(h))) };
    });
    ok(o.ids.l6d && o.ids.l6b && o.hit.length === 0 && o.ovHits.length === 0, vp.join('×') + ' 散步掣同朋友掣冇重疊', o);
    if (vp[0] === 360 && vp[1] === 640) {
      await page.screenshot({ path: SHOTS + '3d-h14-360-btns.png' });
      fs.copyFileSync(SHOTS + '3d-h14-360-btns.png', APKSHOTS + '3d-h14-360-btns.png');
      ok(fs.existsSync(APKSHOTS + '3d-h14-360-btns.png'), '360×640 掣排版截圖已寫');
    }
    await ctx.close();
  }

  const fatal = errs.filter(e => !/open-meteo|ResizeObserver|favicon/.test(e));
  ok(fatal.length === 0, '冇 pageerror／console error', fatal.slice(0, 8));

  await browser.close();
  console.log('— ' + (fail ? '失敗' : '通過') + '／' + pass + (fail ? '  失敗 ' + fail : '') + '—');
  if (fpsReport) console.log('FPS4X ' + JSON.stringify(fpsReport));
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
