/* 《微光小圃》 e2e-v3 — #83 新派 HD-2D V3 接入（遊美 art/workscenes-v3）：
   A 花園 V3 H1–H4＋四季 16 款；B petGlow（瞓 0／醒淡入 1→1.15→1／眼瞓 .6／夢 0；團絨＋細佬）；C 散步 walk_bg 日／黃昏／夜跟鐘；
   D 屋仔 V3（寵物光 1／床 0，燈／窗光唔熄）；E 360／390／412 × 13 頁 UI 重疊 ＝ 0、V3 字型、最細 18@3x；F 🛠 V3 試玩掣（開發者模式、≥48）、?v3=0 返 6b.3、v1 凍結。
   截圖 → SHOTS（v3-*.png）。node tests/e2e-v3.js */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const { audit } = require('./readaudit');
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const QS = 'q=high&seed=21&ev=0&hour=13';

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const errs = [];
  async function boot(vp, qs, dpr) {
    const ctx = await browser.newContext({ viewport: { width: vp[0], height: vp[1] }, deviceScaleFactor: dpr || 1 }); const page = await ctx.newPage();
    page.on('pageerror', e => errs.push('pageerror: ' + e.message)); page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.text()); });
    const q = qs == null ? QS : qs;
    await page.goto(BASE + '?' + q); await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + q);
    await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await page.evaluate(() => __glimmer.liveLoad); await page.evaluate(() => __glimmer.houseLoad).catch(() => { }); await page.evaluate(() => __glimmer.s2Load).catch(() => { });
    return { ctx, page, E: (f, a) => page.evaluate(f, a), W: (ms) => page.waitForTimeout(ms) };
  }
  const adult = (E) => E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 80, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const family = (E) => E(() => { const it = __qa.l5b.dev().items; it.find(i => i.k === 'prep').run(); it.find(i => i.k === 'hats').run(); __qa.house.close(); });


  const closeAll = (E) => E(() => { try { __qa.work62.close(); } catch (e) { } try { __qa.l5b.close(); } catch (e) { } try { __qa.house.close(); } catch (e) { } const t = document.getElementById('u62tip'); if (t) t.remove(); const c = document.querySelector('[data-testid=l6b-close]'); if (c) c.click(); const b = document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]'); if (b) b.click(); });

  const GARDEN = ['H1', 'H2', 'H3', 'H4'], SEAS = ['spring', 'summer', 'autumn', 'winter'];
  const g3 = (E) => E(() => __qa.hd2d.v3());

  // ───────── A. 花園 V3：各時段＋四季 ─────────
  console.log('A. 花園 V3（H1–H4、四季 16 款）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(1500);
    ok(await E(() => __qa.v3.on() && document.getElementById('ui').classList.contains('v3')), 'V3 預設開（#ui.v3）');
    for (const h of GARDEN) { await E((h) => { __qa.hd2d.set(h); __qa.hd2d.skipFade(); }, h); await W(1500);
      const a = await g3(E), b = await g3(E); await W(400); const c = await g3(E);
      ok(c.draws > a.draws && !c.missing.length && c.loaded.includes(h), '時段 ' + h + '：V3 有畫、冇缺圖', { d: [a.draws, c.draws], miss: c.missing, loaded: c.loaded });
      ok(c.lastGlow > 0.95, h + '：醒 petGlow ≈1', c.lastGlow);
      await page.screenshot({ path: SHOTS + 'v3-garden-' + h + '.png' }); }
    for (const s of SEAS) { await E((s) => { __qa.hd2d.season(s); __qa.hd2d.set('H2'); __qa.hd2d.skipFade(); }, s); await W(1800);
      const v = await g3(E), sn = await E(() => __qa.hd2d.season());
      ok(sn === s && !v.missing.length && v.loaded.some(k => k.includes(s)), '季節 ' + s + '：載入 V3 季節層', { sn, loaded: v.loaded, miss: v.missing });
      await page.screenshot({ path: SHOTS + 'v3-garden-' + s + '.png' }); }
    { const miss = []; for (const s of SEAS) for (const h of GARDEN) { await E(([s, h]) => { __qa.hd2d.season(s); __qa.hd2d.set(h); __qa.hd2d.skipFade(); }, [s, h]); let v; for (let i = 0; i < 20; i++) { await W(250); v = await g3(E); if (v.loaded.some(k => k.includes(s) && k.includes(h))) break; } if (v.missing.length || !v.loaded.some(k => k.includes(s) && k.includes(h))) miss.push(s + h); }
      ok(!miss.length, '四季 × H1–H4 ＝ 16 款全部載到', miss); }
    await E(() => { __qa.hd2d.season('auto'); __qa.hd2d.set('auto'); });
    await ctx.close(); }

  // ───────── B. petGlow：瞓／醒／眼瞓（團絨＋細佬） ─────────
  console.log('B. petGlow（瞓 0／醒 1→1.15→1／眼瞓 .6；團絨＋細佬）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await family(E); await W(1500);
    ok(await E(() => __qa.v3.glow()) >= 0.95, '醒：團絨光 1');
    await E(() => { const s = __glimmer.state; s.needs.energy = 40; s.sleeping = true; }); await W(300);
    const mid = await E(() => __qa.v3.glow()); await W(900);
    const z = await E(() => ({ g: __qa.v3.glow(), st: __qa.v3.state(), last: __qa.hd2d.v3().lastGlow }));
    ok(z.g === 0 && z.st === 'sleep' && z.last < 0.01, '瞓覺：600ms 淡到 0（花園 render 都 0）', { mid, z });
    await page.screenshot({ path: SHOTS + 'v3-garden-sleep.png' });
    await E(() => { const s = __glimmer.state; s.sleeping = false; s.needs.energy = 100; }); await W(200);
    const ws = []; for (let i = 0; i < 8; i++) { ws.push(await E(() => __qa.v3.glow())); await W(60); }
    await W(600); const w1 = await E(() => __qa.v3.glow());
    ok(Math.max(...ws) > 1.02 || ws.some(v => v > 0 && v < 1), '醒：淡入（' + ws.map(v => v.toFixed(2)).join(' ') + '）', ws);
    ok(Math.abs(w1 - 1) < 0.01, '醒之後返 1', w1);
    await E(() => __qa.v3.force('drowsy')); await W(600); ok(Math.abs(await E(() => __qa.v3.glow()) - 0.6) < 0.01, '眼瞓 60%');
    await E(() => __qa.v3.force('dreaming')); await W(800); ok(await E(() => __qa.v3.glow()) === 0, '夢遊 0');
    await E(() => { __qa.v3.force(null); }); await W(800);
    ok(await E(() => __qa.v3.kidGlow()) >= 0.95, '細佬醒：光 1');
    await E(() => __qa.v3.forceKid('sleep')); await W(900); ok(await E(() => __qa.v3.kidGlow()) === 0, '細佬瞓：光 0');
    await E(() => __qa.v3.forceKid(null)); await W(700); ok(await E(() => __qa.v3.kidGlow()) >= 0.95, '細佬醒返');
    await ctx.close(); }

  // ───────── C. 散步 walk_bg V3：日／黃昏／夜 ─────────
  console.log('C. 散步 walk_bg V3（跟時間）');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(1500);
    for (const [h, v] of [[13, 'day'], [18, 'dusk'], [22, 'night']]) {
      await closeAll(E); await E((h) => { __glimmer.hourOverride = h; }, h); await W(300);
      await E(() => document.querySelector('#l6bbtn').click()); await W(2200);
      const s = await E(() => __qa.l6b.v3());
      ok(s && s.on && s.variant === v && s.draws > 0 && !s.missing.length, h + ':00 → walk_bg ' + v, s);
      await page.screenshot({ path: SHOTS + 'v3-walk-' + v + '.png' }); }
    await ctx.close(); }

  // ───────── D. 屋仔 V3：寵物光 1／.6／床 0、燈＋窗光唔熄 ─────────
  console.log('D. 屋仔 V3');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await family(E); await W(1200);
    const dev = (k) => E((k) => { __qa.devmode.open(); const b = document.querySelector('[data-testid=dev-house-' + k + ']'); if (b) b.click(); return !!b; }, k);
    await E(() => __qa.house.open()); await W(1500); await dev('setA'); await dev('sit'); await W(1500);
    let s = await E(() => __qa.house.v3());
    ok(s.on && s.draws > 0 && !s.missing.length, '屋仔 V3 有畫、冇缺圖', s);
    ok(s.glow.tr >= 0.95 && s.glow.kid >= 0.95 && s.glow.trS === 'awake', '醒：寵物光 1', s.glow);
    ok(s.lamp > 0 && s.win && s.win !== 'none', '燈光池＋窗光（' + s.win + '）', [s.lamp, s.win]);
    await page.screenshot({ path: SHOTS + 'v3-house-day.png' });
    await dev('sleep'); await W(2200); s = await E(() => __qa.house.v3()); const l0 = s.lamp; await W(500); const s2 = await E(() => __qa.house.v3());
    ok(s2.glow.tr === 0 && s2.glow.kid === 0 && s2.glow.trS === 'sleep', '床：寵物光 0', s2.glow);
    ok(s2.lamp > l0 && s2.win && s2.winAtten >= 0, '瞓覺時燈／窗光照開', [l0, s2.lamp, s2.win]);
    await page.screenshot({ path: SHOTS + 'v3-house-night.png' });
    await dev('auto'); await ctx.close(); }

  // ───────── E. 重疊 360／390／412 × 每頁 ─────────
  console.log('E. UI 重疊（V3：360×640、390×844、412×915）');
  for (const vp of [[360, 640], [390, 844], [412, 915]]) {
    const { ctx, page, E, W } = await boot(vp); await adult(E); await family(E); await W(1500);
    const tag = vp.join('x'); let tot = 0; const bad = [];
    for (const pg of ['main', 'work', 'house', 'plan', 'walk', 'diary', 'dex', 'settings', 'kid', 'tip', 'voice', 'dev', 'hidden']) {
      await closeAll(E); await E(() => { __glimmer.nq && __glimmer.nq.clear && __glimmer.nq.clear(); __qa.ui63.setHidden(false); }); await W(400);
      await E((pg) => { const c = (s) => { const e = document.querySelector(s); if (e) e.click(); };
        if (pg === 'work') __qa.work62.open(); else if (pg === 'house') c('#s2house'); else if (pg === 'plan') __qa.l5b.plan(); else if (pg === 'walk') c('#l6bbtn'); else if (pg === 'diary') c('#diary'); else if (pg === 'dex') c('#dex');
        else if (pg === 'settings') c('#gear'); else if (pg === 'kid') c('#s2kid'); else if (pg === 'tip') { __qa.ui62.dev().items.find(i => i.k === 'tipdemo').run(); } else if (pg === 'voice') __glimmer.say({ line: '今日天氣好好，我哋出去行下好唔好？', src: 'voice', urgent: true });
        else if (pg === 'dev') { __qa.devmode.open(); } else if (pg === 'hidden') { __qa.ui63.setHidden(true); __glimmer.say({ line: '收埋咗都會講嘢', src: 'voice', urgent: true }); } }, pg);
      await W(pg === 'house' || pg === 'walk' ? 1800 : 900);
      const o = await E(() => __qa.ui62.overlap()); tot += o.hits.length; if (o.hits.length) bad.push([pg, o.hits.slice(0, 4)]);
      await page.screenshot({ path: SHOTS + 'v3-ov-' + tag + '-' + pg + '.png' });
      if (pg === 'settings') await E(() => { const tab = document.querySelector('[data-testid=hd-tab-home]'); if (tab) tab.click(); });
      if (pg === 'dev') await E(() => { const b = document.querySelector('[data-testid=dev-close]') || document.querySelector('[data-testid=modal-close]'); if (b) b.click(); });
    }
    await closeAll(E); await E(() => __qa.ui63.setHidden(false)); await W(500);
    ok(tot === 0, tag + '：13 頁（含開發者／收埋）可見 UI 框兩兩冇重疊', bad);
    // 字：V3 字型、最細 12 CSS（＝18@3x @390）
    const f = await E(() => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth; const els = [...ui.querySelectorAll('*')].filter(e => e.offsetWidth && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && getComputedStyle(e).visibility !== 'hidden' && getComputedStyle(e).opacity !== '0');
      return { min: Math.min(...els.filter(e => e.getBoundingClientRect().width > 0 && parseFloat(getComputedStyle(e).fontSize) > 0).map(e => { const r = e.getBoundingClientRect(); return parseFloat(getComputedStyle(e).fontSize) * (r.width / (e.offsetWidth || 1)) / k; })), fam: [...new Set(els.map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/"/g, '')))] }; });
    ok(f.fam.every(x => /GlimmerV3/.test(x)), tag + '：全部 UI 字用 V3 Noto CJK TC', f.fam);
    ok(f.min >= 11.95, tag + '：最細字 ≥12 CSS（18@3x）', f.min);
    await ctx.close();
  }

  // ───────── F. 🛠 開發者模式、?v3=0、v1 ─────────
  console.log('F. 🛠 V3 試玩掣、?v3=0、v1');
  { const { ctx, page, E, W } = await boot([390, 844]); await adult(E); await W(1200);
    await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(500);
    ok(await page.locator('[data-testid=dev-sec-v3]').count() === 1, '分組「HD-2D V3」喺開發者模式');
    ok(!(await E(() => [...document.querySelectorAll('[data-testid^=s2-set],[data-testid^=toggle-]')].some(e => /V3|寵物光/.test(e.textContent)))), '試玩掣唔喺設定');
    const hs = await E(() => [...document.querySelectorAll('[data-testid^=dev-v3-]')].map(e => e.getBoundingClientRect().height));
    ok(hs.length >= 9 && hs.every(h => h >= 47.5), 'V3 試玩掣 ≥48（' + hs.length + '）', hs);
    await page.locator('[data-testid=dev-v3-glow_sleep]').scrollIntoViewIfNeeded(); await page.locator('[data-testid=dev-v3-glow_sleep]').click(); await W(900);
    ok(await E(() => __qa.v3.glow()) === 0, '🛠「寵物光：瞓」有效');
    await E(() => document.querySelector('[data-testid=dev-v3-glow_auto]').click()); await W(800);
    ok(await E(() => __qa.v3.glow()) >= 0.95, '🛠「自動」返醒');
    await E(() => document.querySelector('[data-testid=dev-v3-season]').click()); await W(300); ok(await E(() => __qa.hd2d.season()) === 'spring', '🛠 季節輪轉 → 春');
    await ctx.close(); }
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&v3=0'); await adult(E); await family(E); await W(1500);
    const v = await E(() => ({ on: __qa.v3.on(), cls: document.getElementById('ui').classList.contains('v3'), u63: document.getElementById('ui').classList.contains('u63'), font: getComputedStyle(document.querySelector('#bar .abtn .hdl') || document.body).fontFamily, g: __qa.hd2d.v3() }));
    ok(!v.on && !v.cls && v.u63 && !/GlimmerV3/.test(v.font), '?v3=0：返 6b.3 樣（冇 V3 class／字型）', v);
    await E(() => __qa.house.open()); await W(1500); const h = await E(() => __qa.house.v3());
    ok(!h || !h.on, '?v3=0：屋仔用返舊畫法', h); await page.screenshot({ path: SHOTS + 'v3off-house.png' });
    await ctx.close(); }
  { const { ctx, page, E, W } = await boot([390, 844], QS + '&ui=1'); await adult(E); await W(1000);
    const v = await E(() => ({ v3: document.getElementById('ui').classList.contains('v3'), on: __qa.v3.on(), v2: document.getElementById('ui').classList.contains('v2') }));
    ok(!v.v3 && !v.on && !v.v2, 'v1 舊 UI 凍結（冇 V3）', v);
    await ctx.close(); }

  ok(errs.length === 0, '冇 console error／pageerror', errs.slice(0, 5));
  await browser.close();
  console.log(`\nv3 e2e：${pass} pass / ${fail} fail`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
