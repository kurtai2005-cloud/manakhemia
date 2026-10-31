/* 合併版 E2E：HD-2D 場景＋隱藏開發模式。node tests/e2e-hd2d.js（要 playwright-core＋系統 Chrome，glimmer-live 開 http server，例 python3 -m http.server 8138）
   HD-2D：時段→H 映射、雨→H3rain、~2 秒 crossfade、H4 引擎月／燈籠關、tint 次數唔加、低端 rim 關、粒子跟 grade、?hd2d=0 fallback、?scene=。
   開發模式：手勢開關（標題／左上角 1.5 秒 5 下）、?dev=1、每個掣都叫 __qa.dev API、滑桿、事件無視冷卻、進化（含螢絨）、跳 1 日、重設存檔二次確認＋清存檔。
   截圖：glimmer-combo/screens/（OUT 可改）hd2d-H1/H2/H3/H3rain/H4、devpanel-open 等。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const HD = require('../src/hd2d.js'), DP = require('../src/devpanel.js');
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', '..', 'screens') + '/';
require('fs').mkdirSync(OUT, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

console.log('# 純邏輯（Node）');
{
  const m = [[6, 'H1'], [9.9, 'H1'], [10, 'H3'], [15.9, 'H3'], [16, 'H2'], [18.9, 'H2'], [19, 'H4'], [23.5, 'H4'], [0, 'H4'], [5.9, 'H4']];
  ok(m.every(([h, v]) => HD.variantFor(h) === v), '時段映射 06–10 H1／10–16 H3／16–19 H2／19–06 H4', JSON.stringify(m.map(([h]) => HD.variantFor(h))));
  ok(HD.variantFor(12, 'rain') === 'H3rain' && HD.variantFor(8, 'rain') === 'H1' && HD.variantFor(21, 'rain') === 'H4', '落雨：只有日間 10–16 變 H3rain');
  const st = HD.createState(); HD.update(st, 0, { hour: 12 }); HD.update(st, 0.016, { hour: 20 });
  const a = st.mix; HD.update(st, 1.0, { hour: 20 }); const b = st.mix; HD.update(st, 1.1, { hour: 20 });
  ok(st.cur === 'H4' && a < 0.05 && b > 0.45 && b < 0.6 && st.mix === 1 && st.prev === null, 'crossfade ≈2 秒（0→0.5→1）', JSON.stringify([a, b, st.mix]));
  ok(HD.rimW(1, 0, [1, 0], 1) === 1 && HD.rimW(1, 0, [1, 0], -1) === 0 && HD.rimW(-1, 0, [1, 0], -1) === 1, 'rim w = max(0,n·dir)，scaleX −1 時 nx 取反');
  const o = HD.engineOverlays('H4'); ok(!o.moon && !o.lantern && HD.engineOverlays(null).moon, 'H4：引擎月／燈籠關（fallback 時開）');
  let t = []; let fired = false; for (let i = 0; i < 5; i++) { const r = DP.tapGesture(t, i * 300); t = r.taps; fired = r.fire; }
  let t2 = [], f2 = false; for (let i = 0; i < 5; i++) { const r = DP.tapGesture(t2, i * 400); t2 = r.taps; f2 = f2 || r.fire; }
  ok(fired && !f2, '手勢：1.2 秒內 5 下觸發；1.6 秒 5 下唔觸發');
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(150); await page.screenshot({ path: OUT + n + '.png' }); console.log('  📷 ' + n); };
  const fresh = async (qs, form) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + qs);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad && __glimmer.hdReady).catch(() => { });
    await E(() => Promise.all([__glimmer.liveLoad, __glimmer.hdReady])); await page.waitForTimeout(300);
    await E((form) => { const s = __glimmer.state; if (form === 'sprout') { s.stage = 'sprout'; s.form = null; s.growthSec = 100; } else { s.stage = 'adult'; s.form = form; s.growthSec = 3600; } Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); s.poops = 0; }, form || 'soft');
    await page.waitForTimeout(300);
  };
  const closeModals = () => E(() => { for (let i = 0; i < 8; i++) { const m = document.getElementById('modal'); if (m.style.display !== 'flex') break; const b = document.querySelector('#mbox [data-testid=modal-btn-0]'); if (!b) break; b.click(); } });
  const setHour = async (h, w) => { await E(([h, w]) => { __glimmer.hourOverride = h; __qa.hd2d.weather(w || null); }, [h, w]); await page.waitForTimeout(120); await E(() => __qa.hd2d.skipFade()); await page.waitForTimeout(200); };

  console.log('# HD-2D：時段／雨／crossfade');
  await fresh('q=high&hour=8&seed=7&ev=0', 'soft');
  let c = await E(() => __qa.hd2d.current());
  ok(c.ready && c.enabled && !c.error && c.variant === 'H1', 'HD-2D 載入，08:00 → H1', JSON.stringify(c));
  for (const [h, v, w, n] of [[8, 'H1', null, 'H1'], [17, 'H2', null, 'H2'], [13, 'H3', null, 'H3'], [13, 'H3rain', 'rain', 'H3rain'], [22, 'H4', null, 'H4']]) {
    await setHour(h, w); c = await E(() => __qa.hd2d.current());
    ok(c.variant === v && !c.fading, `${h}:00${w ? ' 落雨' : ''} → ${v}`, JSON.stringify(c));
    await page.waitForTimeout(500); await shot('hd2d-' + n);
  }
  await setHour(13, 'rain');
  let rn = await E(async () => { await new Promise(r => setTimeout(r, 900)); const H = __glimmer.hd; return { rips: H.rips.length, rainPat: H.rainPat ? H.rainPat.length : 0, g: H.grade('H3rain').particles, alpha: H.CFG ? null : null }; });
  ok(rn.rainPat === 4 && rn.rips > 0, '雨：rain_tile 4 幀＋地面 ripple', JSON.stringify(rn));
  ok(HD.CFG.rainLightAdd === 0.3, '雨：light_add alpha 0.3');
  rn = await E(() => { const v = __glimmer.view; return { sun: __glimmer.light.beh ? __glimmer.light.beh.sunbathe : null, w: __glimmer.light.hd2d && __glimmer.light.hd2d.weather }; });
  ok(rn.w === 'rain' && rn.sun === 0, 'weather hook（lighting.addModifier）：雨 → light.hd2d.weather＝rain、唔曬太陽', JSON.stringify(rn));
  // crossfade
  await setHour(13, null);
  const f0 = await E(() => __qa.hd2d.stat().fades);
  await E(() => { __glimmer.hourOverride = 21; });
  await page.waitForTimeout(60); const ca = await E(() => __qa.hd2d.current());
  await page.waitForTimeout(950); const cb = await E(() => __qa.hd2d.current());
  await page.screenshot({ path: OUT + 'hd2d-crossfade.png' });
  await page.waitForTimeout(1400); const cc = await E(() => __qa.hd2d.current()); const f1 = await E(() => __qa.hd2d.stat().fades);
  ok(ca.fading && ca.prev === 'H3' && ca.variant === 'H4' && ca.mix < 0.2, 'crossfade 開始：H3 → H4', JSON.stringify(ca));
  ok(cb.fading && cb.mix > 0.3 && cb.mix < 0.8, 'crossfade ~1 秒時約一半', JSON.stringify(cb));
  ok(!cc.fading && cc.mix === 1 && cc.prev === null && f1 > f0, 'crossfade ~2 秒完成', JSON.stringify(cc));

  console.log('# H4：引擎月 (150,76)／燈籠關、tint 次數');
  await setHour(22);
  let ov = await E(async () => { const r = __glimmer.renderer; const a = Object.assign({}, r.ovStat); await new Promise(z => setTimeout(z, 600)); return { hdOn: r.hdOn, moon: r.ovStat.moonStars - a.moonStars, lan: r.ovStat.lanterns - a.lanterns, ov: __qa.hd2d.current().overlays }; });
  ok(ov.hdOn && ov.moon === 0 && ov.lan === 0 && !ov.ov.moon && !ov.ov.lantern, 'H4：引擎月＋星／燈籠串一幀都冇畫', JSON.stringify(ov));
  for (const form of ['sprout', 'soft', 'bright', 'lumi']) {
    await E((f) => { const s = __glimmer.state; if (f === 'sprout') { s.stage = 'sprout'; s.form = null; } else { s.stage = 'adult'; s.form = f; } __qa.pet.faceStatReset(); }, form);
    const t = await E(async () => { const h0 = __qa.hd2d.stat(); __qa.pet.faceStatReset(); await new Promise(z => setTimeout(z, 700)); const h1 = __qa.hd2d.stat(), f = __qa.pet.face(); return { draws: f.stat.draws, tints: f.stat.tints, hd: h1.tints - h0.tints, rim: h1.rimMask - h0.rimMask, fb: h1.rimFallback - h0.rimFallback, live: f.live }; });
    ok(t.draws > 10 && t.tints === t.draws && t.live && t.rim > 0 && t.fb === 0, `${form}：每次畫寵物只 tint 1 次（HD tint 取代 daylight tint）＋生命感 rim mask`, JSON.stringify(t));
  }
  await shot('hd2d-H4-lumi');
  const low = await E(async () => { __glimmer.setQuality('low'); const h0 = __qa.hd2d.stat(); await new Promise(z => setTimeout(z, 600)); const h1 = __qa.hd2d.stat(); __glimmer.setQuality('high'); return { tints: h1.tints - h0.tints, rim: h1.rimMask - h0.rimMask + h1.rimFallback - h0.rimFallback }; });
  ok(low.tints > 5 && low.rim === 0, '低端（q=low）：rim 關、tint 照做', JSON.stringify(low));
  const parts = {};
  for (const [h, w, v] of [[8, null, 'H1'], [17, null, 'H2'], [13, null, 'H3'], [22, null, 'H4']]) { await setHour(h, w); await page.waitForTimeout(400); parts[v] = await E(() => { const H = __glimmer.hd; return [...new Set(H.ps.map(p => p.type))].join(','); }); }
  ok(parts.H1 === 'mote' && parts.H2 === 'gold' && parts.H3 === 'petal' && parts.H4 === 'firefly', '粒子跟 grade.json：H1 mote／H2 gold／H3 petal／H4 firefly', JSON.stringify(parts));
  // 團絨尺寸唔變（同 ?hd2d=0 比較 petDraw 盒）
  const pd1 = await E(() => { const p = __glimmer.renderer.petDraw; return p ? { w: p.w, h: p.h } : null; });

  console.log('# ?hd2d=0 fallback／?scene=');
  await fresh('q=high&hour=22&seed=7&ev=0&hd2d=0', 'soft');
  ov = await E(async () => { const r = __glimmer.renderer; const a = Object.assign({}, r.ovStat); __qa.pet.faceStatReset(); await new Promise(z => setTimeout(z, 600)); const f = __qa.pet.face(); return { hdOn: r.hdOn, moon: r.ovStat.moonStars - a.moonStars, en: __qa.hd2d.current().enabled, draws: f.stat.draws, tints: f.stat.tints }; });
  ok(!ov.hdOn && !ov.en && ov.moon > 0 && ov.tints === ov.draws, '?hd2d=0：舊程序化背景（引擎月／燈籠照畫）、daylight tint 每次 1 次', JSON.stringify(ov));
  const pd0 = await E(() => { const p = __glimmer.renderer.petDraw; return p ? { w: p.w, h: p.h } : null; });
  ok(JSON.stringify(pd0) === JSON.stringify(pd1), '團絨尺寸 HD-2D 同舊背景一樣', JSON.stringify([pd0, pd1]));
  await shot('hd2d-off-fallback-H4');
  await fresh('q=high&hour=8&seed=7&ev=0&scene=H4', 'soft');
  c = await E(() => __qa.hd2d.current());
  ok(c.mode === 'H4' && c.variant === 'H4', '?scene=H4 強制款', JSON.stringify(c));

  console.log('# 開發模式：手勢');
  await fresh('q=high&hour=13&seed=7&ev=0', 'soft');
  ok(await E(() => !!__qa.dev && !__qa.dev.isOpen() && !document.querySelector('#devp').classList.contains('open')), '預設收埋（無 ?dev=1）');
  for (let i = 0; i < 4; i++) await page.mouse.click(60, 22);
  ok(await E(() => !__qa.dev.isOpen()), '標題點 4 下：唔開');
  await page.waitForTimeout(1700);
  for (let i = 0; i < 5; i++) { await page.mouse.click(60, 22); await page.waitForTimeout(40); }
  ok(await E(() => __qa.dev.isOpen()), '標題 1.5 秒內點 5 下：打開');
  for (let i = 0; i < 5; i++) { await page.mouse.click(8, 8); await page.waitForTimeout(40); }
  ok(await E(() => !__qa.dev.isOpen()), '左上角 5 下：收埋');
  for (let i = 0; i < 5; i++) { await page.mouse.click(60, 22); await page.waitForTimeout(400); }
  ok(await E(() => !__qa.dev.isOpen()), '慢點（2 秒內 5 下）：唔開');
  await fresh('q=high&hour=13&seed=7&ev=0&dev=1', 'soft');
  ok(await E(() => __qa.dev.isOpen()), '?dev=1 預設打開');
  const geo = await E(() => { const r = document.querySelector('#devp').getBoundingClientRect(), cv = document.getElementById('gl').getBoundingClientRect(), pd = __glimmer.renderer.petDraw, k = cv.height / 422;
    return { top: r.top, h: r.height, petBottom: cv.top + 292 * k, petTop: pd ? cv.top + (292 - (pd.h || 50)) * k : null }; });
  ok(geo.top >= geo.petBottom - 8 && geo.h < 300, '抽屜喺底、唔遮團絨（頂 ≥ 寵物腳底）', JSON.stringify(geo));
  await shot('devpanel-open');
  await page.click('[data-testid=dev-fold]');
  // P2 DEV 掣 ≥48dp 之後標題列本身高咗（≈掣高＋padding），所以對標題列高度而唔係定死 40px
  const fd = await E(() => ({ h: document.querySelector('#devp').getBoundingClientRect().height, dh: document.querySelector('#devp .dh').getBoundingClientRect().height }));
  ok(fd.h <= fd.dh + 4 && fd.h < geo.h * 0.6, '可摺：摺起後只剩標題列', JSON.stringify(fd)); await shot('devpanel-folded');
  await page.click('[data-testid=dev-fold]');

  console.log('# 開發模式：每個掣都叫 API');
  const btns = await E(() => [...document.querySelectorAll('#devp button[data-a]')].map(b => b.dataset.a).filter(a => ['close', 'reset', 'fold'].indexOf(a) < 0));
  let bad = [];
  for (const a of btns) {
    const sel = `#devp button[data-a="${a}"]`;
    await closeModals(); await E(() => { __glimmer.ev = null; __glimmer.state.evs.pending = []; });
    const n0 = await E(() => __qa.dev.calls.length);
    try { await page.locator(sel).scrollIntoViewIfNeeded({ timeout: 2500 }); await page.click(sel, { force: true, timeout: 2500 }); }
    catch (e) { const why = await E((q) => { const el = document.querySelector(q), d = document.querySelector('#devp'); return { open: __qa.dev.isOpen(), folded: d && d.classList.contains('fold'), disp: el && getComputedStyle(el).display, pdisp: el && el.parentElement && getComputedStyle(el.parentElement).display }; }, sel); bad.push(a + '→不可見' + JSON.stringify(why)); await E(() => __qa.dev.open && __qa.dev.open()); continue; }
    await page.waitForTimeout(60);
    const last = await E(() => __qa.dev.calls[__qa.dev.calls.length - 1]); const n1 = await E(() => __qa.dev.calls.length);
    const [fn, arg] = a.split(':'); const err = await E(() => __qa.dev.calls.filter(c => c.name === 'error').map(c => c.arg));
    if (n1 <= n0 || last.name !== fn || (arg != null && String(Array.isArray(last.arg) ? last.arg[0] : last.arg) !== arg) || err.length) bad.push(a + '→' + JSON.stringify(last) + JSON.stringify(err));
    await page.waitForTimeout(80); await closeModals();
  }
  ok(btns.length >= 30 && bad.length === 0, `全部 ${btns.length} 個掣都經 __qa.dev API`, bad.join(' | '));
  // 效果
  let r = await E(() => { __qa.dev.speed(60); return { ts: __glimmer.timeScale, run: __glimmer.clockRun, fake: __glimmer.clock.fake }; });
  const h0 = await E(() => __glimmer.hour()); await page.waitForTimeout(1500); const h1 = await E(() => __glimmer.hour());
  ok(r.ts === 60 && r.run && h1 - h0 > 0.015, '時間 ×60：假時鐘快進（1.5 秒 ≈ 1.5 分鐘）', JSON.stringify([r, h0, h1]));
  await E(() => __qa.dev.speed(1)); ok(await E(() => __glimmer.timeScale === 1 && !__glimmer.clockRun && !__glimmer.clock.fake), '時間 ×1：返實時鐘');
  r = await E(() => { const s = __glimmer.state, g0 = s.growthSec, n0 = s.needs.hunger; const o = __qa.dev.skipDay(); return { o, grew: s.growthSec - g0, hunger: s.needs.hunger, n0, modal: document.getElementById('modal').style.display === 'flex' }; });
  ok(r.o.show && r.hunger < r.n0 && r.modal, '跳 1 日：行離線結算（需求跌、補抽／日記、出總結）', JSON.stringify(r));
  await closeModals();
  r = await E(() => { __qa.dev.setForm('lumi'); return { f: __glimmer.state.form, st: __glimmer.state.stage, chip: document.getElementById('substage').textContent }; }); await page.waitForTimeout(400);
  r.chip = await E(() => document.getElementById('substage').textContent);
  ok(r.f === 'lumi' && r.st === 'adult' && /螢絨/.test(r.chip), '直接設定隱藏形態「螢絨」', JSON.stringify(r));
  await E(() => { __qa.dev.playEvolve('bright'); }); await page.waitForTimeout(500);
  r = await E(() => ({ f: __glimmer.state.form, m: document.getElementById('mbox').textContent }));
  ok(r.f === 'bright' && /燦光/.test(r.m), '播進化場面（evolve 彈窗）', JSON.stringify(r)); await shot('devpanel-evolve');
  await closeModals();
  await E(() => { const i = document.querySelector('[data-testid=dev-need-hunger]'); i.value = 12; i.dispatchEvent(new Event('input', { bubbles: true })); const q = document.querySelector('[data-testid=dev-cq]'); q.value = 88; q.dispatchEvent(new Event('input', { bubbles: true })); });
  r = await E(() => ({ h: Math.round(__glimmer.state.needs.hunger), cq: Math.round(__glimmer.state.cq) }));
  ok(r.h <= 13 && r.cq === 88, '需求／CQ 滑桿', JSON.stringify(r));
  r = await E(() => __qa.dev.personality('bold')); ok(r.sticky === 0.1 && r.timid === 0, '性格切換（大膽獨立）', JSON.stringify(r));
  const evr = await E(() => { const out = {}; for (const id of __qa.dev.events()) { const E0 = __glimmer.state.evs; E0.cd[id] = E0.clock + 99 * 3600; const x = __qa.dev.trigger(id); out[id] = x.id === id && E0.log[E0.log.length - 1].id === id; } return out; });
  ok(Object.keys(evr).length === 9 && Object.values(evr).every(Boolean) && evr.grumpy && evr.flash && evr.firefly_walk, '觸發全 EVENTS 表（含鬧脾氣／閃光日／螢火散步），無視冷卻', JSON.stringify(evr));
  r = await E(() => { __qa.dev.scene('H3rain'); return { c: __qa.hd2d.current().mode, w: __glimmer.weather }; });
  ok(r.c === 'H3rain' && r.w === 'rain', '時段／天氣：H3 雨', JSON.stringify(r));
  await E(() => __qa.dev.scene('auto')); ok(await E(() => __qa.hd2d.current().mode === 'auto' && !__glimmer.weather), '時段：Auto');

  console.log('# 開發模式：重設存檔（二次確認）');
  await E(() => { __glimmer.state.grains = 4242; __glimmer.save(); });
  await page.click('[data-testid=dev-reset]');
  r = await E(() => ({ armed: __qa.dev.state().resetArmed, label: document.querySelector('[data-testid=dev-reset]').textContent, saved: !!localStorage.getItem(__glimmer && 'glimmer_save_v1') }));
  ok(r.armed && /確認/.test(r.label) && r.saved, '第一下：只係「再撳一次確認」，存檔仲喺度', JSON.stringify(r));
  await page.waitForTimeout(3300);
  ok(await E(() => !__qa.dev.state().resetArmed), '3 秒唔撳：自動取消');
  await page.click('[data-testid=dev-reset]');
  await Promise.all([page.waitForNavigation(), page.click('[data-testid=dev-reset]')]);
  await page.waitForFunction(() => window.__glimmer && __glimmer.state).catch(() => { });
  r = await E(() => { const raw = JSON.parse(localStorage.getItem('glimmer_save_v1') || 'null'); return { grains: __glimmer.state.grains, stage: __glimmer.state.stage, raw: raw ? raw.grains : null, dev: __qa.dev.isOpen() }; });
  ok(r.grains === 0 && r.stage === 'egg' && r.raw !== 4242, '第二下：清存檔＋重新開始（光卵、光粒 0）', JSON.stringify(r));

  ok(errs.length === 0, 'console 無錯誤／警告', errs.join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
