/* 《微光小圃》 e2e-3d — #89 3D 花園 H1 試點：場景載入、遮擋、觸摸、日夜光、畫質切換、?3d=0。
   截圖 → SHOTS；3d-h1-*.png 同 3d-h11-*.png（H11SHOTS／APK 目錄）。fps 用 CDP 4× CPU。node tests/e2e-3d.js */
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

  // ───────── H. 4× CPU fps ─────────
  console.log('H. 中端機 4× CPU 慢 fps');
  let fpsReport = null;
  { const { ctx, page, E, W } = await boot([390, 844]); await adultR(E); await waitG3(E, W); await W(400);
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await E(() => { __qa.g3d.showPerf(true); __glimmer.hourOverride = 13; });
    await W(2500);
    const mid = await E(() => ({ q: __qa.g3d.quality(), on: __qa.g3d.on(), fps: __qa.g3d.fps(), ms: __qa.g3d.lastMs() }));
    await W(2500);
    const mid2 = await E(() => ({ q: __qa.g3d.quality(), on: __qa.g3d.on(), fps: __qa.g3d.fps(), ms: __qa.g3d.lastMs(), draws: __glimmer.g3d && __glimmer.g3d.stat && __glimmer.g3d.stat.draws }));
    fpsReport = { throttle: '4x', first: mid, second: mid2 };
    ok(mid2.on, '4× CPU 之下 3D 仍然開（未自動跌去 2D，窗口 2×120 幀）', mid2);
    console.log('  fps 4× CPU: ' + JSON.stringify(fpsReport));
    fs.writeFileSync('/home/box/keep/3d-h1/fps-4x.json', JSON.stringify(fpsReport, null, 2));
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

  const fatal = errs.filter(e => !/open-meteo|ResizeObserver|favicon/.test(e));
  ok(fatal.length === 0, '冇 pageerror／console error', fatal.slice(0, 8));

  await browser.close();
  console.log('— ' + (fail ? '失敗' : '通過') + '／' + pass + (fail ? '  失敗 ' + fail : '') + '—');
  if (fpsReport) console.log('FPS4X ' + JSON.stringify(fpsReport));
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
