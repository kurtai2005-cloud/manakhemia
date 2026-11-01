/* 《微光小圃》 e2e-sys12b — systems12 第 2 批：5 小遊戲（接光點／捉迷藏）→ 2 小圃種花 → 4 散步收集＋收藏櫃 → 11 成就徽章。
   截圖 → SHOTS sys12b-*.png。直向 390×844。數值讀 config（D.PARAMS.systems12b）。 */
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

const Glimmer_lines_ok = (txt, L) => L.some(l => txt.includes(l));
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
    await page.screenshot({ path: SHOTS + 'sys12b-' + n + '.png', clip }); console.log('  📷 sys12b-' + n);
  };
  const closeModals = async () => { for (let i = 0; i < 6; i++) { const v = await E(() => getComputedStyle(document.getElementById('modal')).display !== 'none'); if (!v) break; await E(() => { const b = document.querySelectorAll('#mbox .btn'); (b[b.length > 1 ? 1 : 0] || b[0]).click(); }); await page.waitForTimeout(150); } };
  const jc = (tid) => E((tid) => document.querySelector('[data-testid="' + tid + '"]').click(), tid);
  const dev = async (tid) => { await E(() => { const p = document.getElementById('devp'); if (p && p.classList.contains('fold')) p.classList.remove('fold'); }); await page.click('[data-testid="' + tid + '"]'); };
  const go = async (q) => { await page.goto(BASE + q); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + q); await ready(); await E(() => { window.__noSaveOnHide = true; }); };
  const juv = () => E(() => { const s = __glimmer.state; s.stage = 'juvenile'; s.form = null; s.sleeping = false; s.growthSec = 10; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); s.poops = 0; __qa.pet.force('stay'); __glimmer.beh.x = 0; });

  const dev0 = dev; const devF = async (tid) => { await E(() => { const p = document.getElementById('devp'); if (p) p.classList.add('open'); }); await dev0(tid); await E(() => { const p = document.getElementById('devp'); if (p) { p.classList.add('fold'); p.classList.remove('open'); } }); };
  await go('?q=high&hour=13&seed=21&ev=0&dev=1');
  await juv(); await closeModals();
  const C = await E(() => Glimmer.data.PARAMS.systems12b);
  if (want('games')) {
    console.log('# ① 系統 5 小遊戲');
    const tabs = await E(() => __glimmer.s12.tabs.map(t => t[0]).join());
    ok(tabs === 'quest,diary,bond,surp,games,garden,cab,badge', '面板加 4 個 tab（第 1 批 4 個保留）', tabs);
    await closeModals(); await E(() => { const p = document.getElementById('devp'); if (p) { p.classList.add('fold'); p.classList.remove('open'); } }); await jc('play'); await page.waitForTimeout(200);
    const items = await E(() => ['play-mg', 'play-catch', 'play-hide'].map(t => !!document.querySelector('[data-testid="' + t + '"]')));
    ok(items.every(Boolean), '玩 menu：接星屑（舊）＋接光點＋捉迷藏', items); await shot('play-menu');
    await E(() => { const b = document.querySelector('[data-testid="play-catch"]'); b && b.click(); }); await page.waitForTimeout(300);
    const m = await E(() => { const x = Glimmer.ui.mgState(); return x && { kind: x.kind, dur: x.mg.M.durationSec, mode: __glimmer.mode }; });
    ok(m && m.kind === 'catch' && m.dur === C.games.catch.durationSec && m.mode === 'minigame', '接光點開始：30 秒', m);
    const w0 = await E(() => Glimmer.sys12.wallet(__glimmer.state, __glimmer.now()).o), mood0 = await E(() => __glimmer.state.needs.mood), mg0 = await E(() => __glimmer.state.stats.mgPlays);
    await E(() => { const x = Glimmer.ui.mgState(); x.ready = 0; x.mg.score = 80; x.mg.t = x.mg.M.durationSec - 0.05; }); await page.waitForTimeout(900);
    const r = await E(() => __glimmer.lastMG);
    ok(r && r.kind === 'catch' && r.stars === 3 && r.shards === 3, '完場 3 星 → 3 星星碎', r);
    const w1 = await E(() => Glimmer.sys12.wallet(__glimmer.state, __glimmer.now()).o), mood1 = await E(() => __glimmer.state.needs.mood), mg1 = await E(() => __glimmer.state.stats.mgPlays);
    ok(w1 - w0 === 3 && mg1 === mg0 + 1, '星星碎經 wallet；計一局 mg', { w0, w1, mg0, mg1 });
    ok(Math.abs(mood1 - mood0) < 2, '冇加心情（只有自然衰減）', { mood0, mood1 });
    await shot('catch-result'); await closeModals();
    await devF('dev-s12-hide'); await page.waitForTimeout(200);
    let hs = await E(() => __qa.sys12b.hideState()); ok(hs && hs.spots.length >= 3 && hs.spots.length <= 5, '捉迷藏：3–5 個匿位', hs);
    const geo = await E(() => { const b = document.querySelector('[data-testid="s12b-spot-0"]').getBoundingClientRect(); return { y: b.top, h: b.height, H: innerHeight }; });
    ok(geo.y > geo.H * 0.45 && geo.h >= 44, '直向單手：匿位掣喺下半、≥44px', geo); await shot('hide');
    for (let k = 0; k < 3; k++) { hs = await E(() => __qa.sys12b.hideState()); if (!hs) break; await page.click('[data-testid="s12b-spot-' + hs.at + '"]'); await page.waitForTimeout(120); }
    await page.waitForTimeout(800); const rh = await E(() => __qa.sys12b.lastHide());
    ok(rh && rh.kind === 'hide' && rh.value === 3 && rh.stars === 3, '3 輪全中 → 3 星', rh); await shot('hide-result'); await closeModals();
    await E(() => __qa.sys12b.hideStart(5)); const t0 = await E(() => __qa.sys12b.hideState().left);
    ok(t0 <= 45, '捉迷藏限時 ≤45 秒', t0);
    await page.click('[data-testid="s12b-hide-quit"]'); ok(await E(() => __qa.sys12b.hideState() === null && getComputedStyle(document.getElementById('s12hide')).display === 'none'), '唔玩 → 退出、唔計');
    await E(() => { for (let i = 0; i < 5; i++) Glimmer.sys12b.gameFinish(__glimmer.state, 'hide', 0, __glimmer.now()); });
    const g = await E(() => __qa.sys12b.games()); ok(g.left === 0, '每日頭 5 局有獎（已用完）', g);
    await E(() => __qa.sys12.open('games')); await page.waitForTimeout(200); const gt = await E(() => document.querySelector('[data-testid="s12b-games-left"]').textContent);
    ok(/5\/5/.test(gt), '小遊戲 tab 顯示今日局數', gt); await shot('tab-games'); await E(() => __glimmer.s12close());
    await devF('dev-s12-games-reset'); ok((await E(() => __qa.sys12b.games())).left === 5, 'DEV 今日局數清零');
  }
  if (want('garden')) {
    console.log('# ② 系統 2 小圃種花');
    await E(() => { const w = Glimmer.sys12.st(__glimmer.state).wallet; w.total = 20; });
    await devF('dev-s12-garden-open'); await page.waitForTimeout(200);
    ok(await E(() => document.querySelectorAll('[data-testid^="s12b-pot-"]').length === 3), '3 格花盆');
    await page.click('[data-testid="s12b-plant-0-bluebell"]'); await page.waitForTimeout(150);
    let gd = await E(() => __qa.sys12b.garden()); ok(gd.pots[0].k === 'bluebell' && (await E(() => Glimmer.sys12.wallet(__glimmer.state, __glimmer.now()).total)) === 20 - C.garden.seedPrice, '撳種藍鈴：扣 ' + C.garden.seedPrice + ' 星星碎', gd.pots[0]);
    await page.click('[data-testid="s12b-water-0"]'); await page.waitForTimeout(150); gd = await E(() => __qa.sys12b.garden());
    ok(gd.pots[0].wateredToday && gd.pots[0].stage === 1, '淋水 → 芽', gd.pots[0]); await shot('garden-sprout');
    await E(() => __glimmer.s12dev.gardenDay()); await E(() => __glimmer.s12dev.gardenWater()); const b5a = await E(() => JSON.stringify((__glimmer.state.evo.b5sys || {})[__glimmer.state.stage] || {}));
    await E(() => __glimmer.s12dev.gardenDay()); await page.waitForTimeout(1300); gd = await E(() => __qa.sys12b.garden());
    const b5b = await E(() => ((__glimmer.state.evo.b5sys || {})[__glimmer.state.stage] || {}).moon || 0);
    ok(gd.pots[0].bloomed && b5b >= C.garden.bloomPts, '淋 2 日 → 開花，月眠 +' + C.garden.bloomPts, { p: gd.pots[0], b5a, b5b });
    await E(() => __qa.sys12.open('garden')); await page.waitForTimeout(200); await shot('garden-bloom');
    await page.click('[data-testid="s12b-harvest-0"]'); gd = await E(() => __qa.sys12b.garden()); ok(gd.pots[0].empty && gd.vase.bluebell === 1, '剪落花瓶');
    await E(() => __glimmer.s12dev.gardenPlant()); await E(() => { __glimmer.s12dev.gardenDay(); __glimmer.s12dev.gardenDay(); }); gd = await E(() => __qa.sys12b.garden());
    const wil = gd.pots.find(p => !p.empty); ok(wil && wil.wilted && (await E(() => __glimmer.state.stage)) === 'juvenile', '冇淋水 → 枯，團絨冇事', wil);
    await E(() => __qa.sys12.open('garden')); await page.waitForTimeout(200); await shot('garden-wilted'); await E(() => __glimmer.s12close());
  }
  if (want('walk')) {
    console.log('# ③ 系統 4 散步收集＋收藏櫃');
    await E(() => __glimmer.s12dev.pickReset());
    const r1 = await E(() => __glimmer.s12dev.pick()); ok(r1 && r1.k, 'DEV 執一件', r1);
    for (let i = 0; i < 6; i++) await E(() => __glimmer.s12dev.pick());
    const cb = await E(() => __qa.sys12b.cabinet()); ok(cb.today === 5, '每日最多 5 件', cb.today);
    await E(() => __glimmer.s12dev.pickReset());
    const walked = await E(() => new Promise(res => { const W = Glimmer.sys12b.st(__glimmer.state).walk, n0 = W.total; const orig = Math.random; let calls = 0; Math.random = () => 0.05; __qa.pet.force('walk'); setTimeout(() => { Math.random = orig; res({ n0, n1: Glimmer.sys12b.st(__glimmer.state).walk.total }); }, 700); }));
    ok(walked.n1 > walked.n0, '團絨開始行 → 擲 10%（hook 喺 behavior walk）', walked);
    await devF('dev-s12-cab-open'); await page.waitForTimeout(400);
    const cells = await E(() => ({ n: document.querySelectorAll('[data-testid^="s12b-slot-"]').length, locked: document.querySelectorAll('[data-testid^="s12b-slot-"][data-locked]').length, imgs: [...document.querySelectorAll('#s12body img')].filter(i => i.complete && i.naturalWidth === 32).length }));
    ok(cells.n === 30 && cells.locked === 18 && cells.imgs === 12, '收藏櫃 30 格（12 件有圖剪影／已收集；18 格鎖）', cells); await shot('cabinet');
    await E(() => __glimmer.s12close());
  }
  if (want('badge')) {
    console.log('# ④ 系統 11 成就徽章');
    await E(() => __glimmer.s12dev.badgeReset());
    await E(() => { const s = __glimmer.state; s.dex = ['moon']; }); await page.waitForTimeout(1300);
    let b = await E(() => __qa.sys12b.badges()); ok(b.list.find(x => x.k === 'route_moon').got, '圖鑑月眠 → 月眠徽章（通知）', b.have);
    const gainTxt = await E(() => document.getElementById('s12gain') ? document.getElementById('s12gain').textContent : ''); ok(/徽章/.test(gainTxt), '通知文字', gainTxt);
    const h0 = b.have; await page.waitForTimeout(1200); b = await E(() => __qa.sys12b.badges()); ok(b.have === h0, '唔重覆給');
    await devF('dev-s12-badge-open'); await page.waitForTimeout(200); ok(await E(() => document.querySelectorAll('[data-testid^="s12b-badge-"][data-got]').length === 11), '徽章 tab：11 個（其餘 19 未開放）'); await shot('badges');
    await E(() => __glimmer.s12close());
  }
  if (want('keep')) {
    console.log('# ⑤ 舊功能保留');
    ok(await E(() => typeof __glimmer.evo.overlayOpenGame === 'function' && typeof Glimmer.ui.startMG === 'function'), '浮動撳兩下開 game（接星屑）保留');
    await E(() => Glimmer.ui.startMG()); const m0 = await E(() => { const x = Glimmer.ui.mgState(); return x && { kind: x.kind || null, dur: x.mg.M.durationSec }; });
    ok(m0 && m0.kind === null && m0.dur === 45, '接星屑（舊）照舊 45 秒', m0); await E(() => Glimmer.ui.endMG(true));
    const sv = await E(() => { __glimmer.save(); const raw = localStorage.getItem(Object.keys(localStorage).find(k => /glimmer/i.test(k))); return raw && raw.includes('sys12b'); }); ok(sv, '存檔有 sys12b');
  }
  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
