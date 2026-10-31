/* 《微光小圃》 e2e-sys12 — systems12 第 1 批：系統 7 天氣／季節（自動天氣寫入 G.weather、DEV／?weather= 覆蓋、H3 陰／霧／雨、季節層、撐葉／打冷震、tell）。
   截圖 → SHOTS sys12-*.png。直向 390×844。數值讀 config（D.PARAMS.systems12）。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8238/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
const ONLY = (process.env.ONLY || '').split(',').filter(Boolean), want = (k) => !ONLY.length || ONLY.includes(k);
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info).slice(0, 600) : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.evoLoad && __glimmer.hdReady).catch(() => { }); await E(() => Promise.all([__glimmer.liveLoad, __glimmer.evoLoad, __glimmer.hdReady])); await page.waitForTimeout(300); };
  const shot = async (n, crop) => {
    await page.waitForTimeout(150); let clip;
    if (crop) clip = await E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, b = window.Glimmer.ui.petHitBox(); const w = 150, h = 170;
      return { x: Math.max(0, r.left + (b.x + b.w / 2) * k - w / 2), y: Math.max(0, r.top + (b.y + b.h / 2) * k - h / 2 - 20), width: w, height: h }; });
    await page.screenshot({ path: SHOTS + 'sys12-' + n + '.png', clip }); console.log('  📷 sys12-' + n);
  };
  const closeModals = async () => { for (let i = 0; i < 6; i++) { const v = await E(() => getComputedStyle(document.getElementById('modal')).display !== 'none'); if (!v) break; await E(() => { const b = document.querySelectorAll('#mbox .btn'); (b[b.length > 1 ? 1 : 0] || b[0]).click(); }); await page.waitForTimeout(150); } };
  const dev = async (tid) => { await E(() => { const p = document.getElementById('devp'); if (p && p.classList.contains('fold')) p.classList.remove('fold'); }); await page.click('[data-testid="' + tid + '"]'); };
  const go = async (q) => { await page.goto(BASE + q); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + q); await ready(); await E(() => { window.__noSaveOnHide = true; }); };
  const juv = () => E(() => { const s = __glimmer.state; s.stage = 'juvenile'; s.form = null; s.sleeping = false; s.growthSec = 10; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); s.poops = 0; __qa.pet.force('stay'); __glimmer.beh.x = 0; });

  if (want('wx')) {
    console.log('# ① 系統 7：自動天氣 → G.weather（DEV／?weather= 覆蓋）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1&wxauto=1');
    const C = await E(() => Glimmer.data.PARAMS.systems12);
    // 假時鐘：搵一個落緊雨嘅時刻（用遊戲 seed）
    const r = await E(() => { const G = __glimmer, X = Glimmer.sys12, seed = G.state.seed >>> 0, t0 = new Date(2026, 10, 2, 0, 0).getTime();
      let rainT = null, clearT = null; for (let m = 0; m < 14 * 24 * 60 && (rainT == null || clearT == null); m += 10) { const t = t0 + m * 60000, h = new Date(t).getHours(); const w = X.weatherAt(t, seed); if (w === 'rain' && rainT == null && h >= 10 && h < 16) rainT = t; if (w === 'clear' && clearT == null && h >= 10 && h < 16) clearT = t; }
      return { rainT, clearT, seed, sim: X.simulate(seed, t0, 14) }; });
    ok(r.rainT && r.clearT && Object.values(r.sim.weeks).every(n => n >= C.weather.rainPerWeek[0] && n <= C.weather.rainPerWeek[1]), '遊戲 seed 14 日：每週 1–3 場雨', r.sim.weeks);
    await E((t) => { const G = __glimmer; G.clock.fake = true; G.clock.t = t; G.hourOverride = null; __qa.sys12.weather(); }, r.rainT); await page.waitForTimeout(2600);
    let w = await E(() => __qa.sys12.wx());
    ok(w.auto && !w.manual && w.autoWeather === 'rain' && w.weatherNow === 'rain' && w.scene === 'H3rain', '自動：落雨時段 → G.weather＝rain、H3rain', w);
    await juv(); await page.waitForTimeout(1500); w = await E(() => __qa.sys12.wx());
    ok(w.umbrella && w.shown === 'leaf_umbrella', '落雨 → 團絨 idle 撐葉（leaf_umbrella）', w);
    await shot('wx-rain-auto'); await shot('wx-umbrella', true);
    await E((t) => { __glimmer.clock.t = t; }, r.clearT); await page.waitForTimeout(2600);
    w = await E(() => __qa.sys12.wx()); ok(w.weatherNow === 'clear' && w.scene === 'H3' && !w.umbrella, '自動：轉晴 → clear、H3、收葉', w);
    await dev('dev-weather-rain'); await page.waitForTimeout(2600); w = await E(() => __qa.sys12.wx());
    ok(w.manual && w.weatherNow === 'rain' && w.autoWeather === 'clear', 'DEV 雨 → 覆蓋自動（自動仍係 clear）', w);
    await dev('dev-weather-auto'); await page.waitForTimeout(1300); w = await E(() => __qa.sys12.wx());
    ok(!w.manual && w.weatherNow === 'clear', 'DEV 自動 → 跟返自動', w);
    for (const k of ['overcast', 'fog']) {
      await dev('dev-weather-' + k); await page.waitForTimeout(2600); w = await E(() => __qa.sys12.wx());
      ok(w.weatherNow === k && w.scene === 'H3' + k, `DEV ${k} → H3${k} 場景`, w); await shot('wx-' + k);
    }
    { const sh = await E(() => { __qa.sys12.play('shiver'); return new Promise(res => setTimeout(() => res(__qa.sys12.wx()), 300)); }); ok(sh.one === 'shiver' && sh.shown === 'shiver', '打冷震 clip 可播（霧天）', sh); await shot('wx-shiver', true); }
    const sp = await E(() => ({ fog: Glimmer.sys12.shiverMul('fog', 'autumn'), clear: Glimmer.sys12.shiverMul('clear', 'autumn') })); ok(sp.fog > sp.clear, '霧天打冷震機率加大', sp);
    // ?weather= 覆蓋
    await go('?q=high&hour=13&seed=21&ev=0&dev=1&wxauto=1&weather=overcast'); w = await E(() => __qa.sys12.wx());
    ok(w.manual && w.weatherNow === 'overcast', '?weather=overcast → 覆蓋自動', w);
    // 雨暗 18%
    const dim = await E(() => __glimmer.hd && Glimmer.hd2d.CFG.rainDim); ok(Math.abs(dim - C.weather.rainDim) < 1e-9, `H3 雨再暗 ${C.weather.rainDim * 100}%（config）`, dim);
    console.log('# ② 季節（香港月份）＋ DEV 強制');
    await go('?q=high&hour=8&seed=21&ev=0&dev=1&season=auto');
    for (const m of ['spring', 'summer', 'autumn', 'winter']) {
      await dev('dev-season-' + m); await page.waitForTimeout(400); await E(() => __glimmer.hd.loadSeason(__glimmer.wx.season)); await page.waitForTimeout(3600);
      w = await E(() => __qa.sys12.wx()); ok(w.season === m && w.scene === 'H1@' + m, `DEV 季節 ${m} → H1@${m}`, w); await shot('season-' + m);
    }
    await dev('dev-season-none'); await page.waitForTimeout(3500); w = await E(() => __qa.sys12.wx()); ok(!w.season && w.scene === 'H1', '季節 none → 基本款', w);
    await dev('dev-season-auto'); await E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, new Date(2026, 0, 10, 9).getTime()); await page.waitForTimeout(1300);
    w = await E(() => __qa.sys12.wx()); ok(w.season === 'winter', '自動：1 月 → 冬', w);
    // tell clip（遊美 G）
    console.log('# ③ §7 G tell clip（絨跳預告）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-juvenile'); await closeModals(); await juv(); await page.waitForTimeout(400);
    await E(() => { __glimmer.foreLog = []; __glimmer.state.ev.push({ type: 'foreshadow', form: 'tide', act: Glimmer.data.PARAMS.evo6.route.foreshadow.tide }); }); await page.waitForTimeout(250);
    w = await E(() => ({ log: __glimmer.foreLog, wx: __qa.sys12.wx() })); ok(w.log.length === 1 && w.log[0].tell === 'tell_tide' && w.wx.shown === 'tell_tide', '預告 tide → 播 tell_tide（行為照舊）', w); await shot('tell-tide', true);
  }
  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
