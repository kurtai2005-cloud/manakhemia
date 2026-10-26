/* E2E：node tests/e2e-playwright.js   需要 playwright-core + 系統 Chrome，並先喺 glimmer-proto 目錄開 http server：
     python3 -m http.server 8125
   環境變數：PW（playwright-core 路徑）、CHROME、BASE、OUT */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/tools/pw/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8125/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', 'screens') + '/';
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: false, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const W = 195, H = 422;
  const G = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(250); await page.screenshot({ path: OUT + n + '.png' }); console.log('  📷 ' + n); };
  const artToClient = async (ax, ay) => { const r = await G(() => { const b = document.getElementById('gl').getBoundingClientRect(); return { l: b.left, t: b.top, w: b.width, h: b.height }; }); return { x: r.l + ax / W * r.w, y: r.t + ay / H * r.h }; };
  const click = async (sel) => { await page.click(sel); await page.waitForTimeout(120); };
  const st = () => G(() => { const s = __glimmer.state; return JSON.parse(JSON.stringify({ stage: s.stage, form: s.form, needs: s.needs, sleeping: s.sleeping, poops: s.poops, cq: s.cq, growthSec: s.growthSec, grains: s.grains, wd: s.withdrawn, q: s.settings.quality })); });
  const closeModals = async () => { for (let i = 0; i < 4; i++) { if (await page.isVisible('#modal')) { await page.click('[data-testid=modal-btn-0]'); await page.waitForTimeout(150); } } };

  console.log('# 新遊戲');
  await page.goto(BASE + '?debug=1&q=high');
  await page.evaluate(() => localStorage.clear()); await page.reload(); await page.waitForTimeout(900);
  ok(await page.isVisible('#dbgT'), '?debug=1 顯示 debug 開關');
  let s = await st(); ok(s.stage === 'egg', '開局係光卵');
  await shot('01-egg-new');

  console.log('# 光卵輕點 → 孵化');
  const eggPos = await artToClient(97, 272);
  for (let i = 0; i < 4; i++) { await page.mouse.click(eggPos.x, eggPos.y); await page.waitForTimeout(120); }
  s = await st(); ok(s.growthSec >= 4 * 75 - 1 && s.stage === 'egg', '輕點增加光卵進度', s.growthSec);
  await shot('02-egg-glow-cracked');
  for (let i = 0; i < 4; i++) { await page.mouse.click(eggPos.x, eggPos.y); await page.waitForTimeout(120); }
  await page.waitForTimeout(300);
  s = await st(); ok(s.stage === 'sprout', '點 8 下孵化成芽崽');
  ok(await page.isVisible('#modal'), '出現孵化彈窗'); await shot('03-hatch-modal');
  await closeModals(); await page.waitForTimeout(800); await shot('04-sprout-idle');

  console.log('# 餵食／玩耍／清潔');
  await G(() => { __glimmer.state.needs.hunger = 40; __glimmer.state.needs.mood = 40; __glimmer.state.needs.clean = 40; });
  await click('#btn-feed'); await shot('05-feed-menu');
  await click('[data-testid=food-meal]'); await page.waitForTimeout(450); await shot('06-eating');
  s = await st(); ok(s.needs.hunger > 75, '正餐 +40 → 飽腹', s.needs.hunger.toFixed(1));
  await page.waitForTimeout(900);
  await click('#btn-play'); await click('[data-testid=play-tease]'); await page.waitForTimeout(500); await shot('07-play-ball');
  s = await st(); ok(s.needs.mood >= 54, '逗玩 +15 心情', s.needs.mood.toFixed(1));
  await page.waitForTimeout(1300);
  await G(() => { __glimmer.state.poops = 3; });
  await page.waitForTimeout(400); await shot('08-poops');
  const p0 = await G(() => Glimmer.render.POOP_SLOTS[2]); const pc = await artToClient(p0[0] - 1.5 * 0, p0[1] - 4);
  await page.mouse.click(pc.x, pc.y); await page.waitForTimeout(200);
  s = await st(); ok(s.poops === 2, '輕點便便清走 1 個', s.poops);
  await click('#btn-clean'); await page.waitForTimeout(500); await shot('09-rinse');
  s = await st(); ok(s.needs.clean >= 89, '沖洗 +50 清潔', s.needs.clean.toFixed(1));
  await page.waitForTimeout(1200);

  console.log('# 不適／飢餓光色');
  await G(() => { __glimmer.state.needs.hunger = 22; });
  await page.waitForTimeout(900); await shot('10-hungry-dim');
  await G(() => { __glimmer.state.needs.hunger = 8; });
  await page.waitForTimeout(900); await shot('11-unwell');
  s = await st(); ok(await page.textContent('#substage').then(t => t.includes('不適')), '需求 <15 顯示「不適」');
  const g0 = s.growthSec; await page.waitForTimeout(1500); s = await st(); ok(Math.abs(s.growthSec - g0) < 0.5, '不適時成長停止');
  await G(() => { __glimmer.state.needs.hunger = 80; });

  console.log('# 睡眠／關燈（月光）');
  await G(() => { __glimmer.state.needs.energy = 35; });
  await click('#btn-sleep'); await page.waitForTimeout(2200); await shot('12-sleep-moon');
  s = await st(); ok(s.sleeping, '關燈入睡');
  await G(() => { __glimmer.fastForward(3600); }); s = await st(); ok(s.needs.energy > 35 + 12, '睡眠精力回升', s.needs.energy.toFixed(1));
  await G(() => { __glimmer.fastForward(3600 * 4); }); s = await st(); ok(!s.sleeping && s.needs.energy > 90, '精力滿自動醒', s.needs.energy.toFixed(1));
  await G(() => { for (const k of ['hunger', 'mood', 'clean', 'energy']) __glimmer.state.needs[k] = 85; });

  console.log('# 迷你遊戲：接星屑');
  await click('#btn-play'); await click('[data-testid=play-mg]');
  await page.waitForTimeout(2000); await shot('13-minigame-start');
  const t0 = Date.now(); let shotMid = false, grains0 = (await st()).grains;
  while (Date.now() - t0 < 58000) {
    const info = await G(() => { const m = Glimmer.ui.mgState(); if (!m) return null; let tgt = m.mg.basketX, best = 1e9; for (const it of m.mg.items) if (it.type !== 'stone' && Glimmer.data.PARAMS.mg.basketY - it.y > 0 && Glimmer.data.PARAMS.mg.basketY - it.y < best) { best = Glimmer.data.PARAMS.mg.basketY - it.y; tgt = it.x; } return { tgt, t: m.mg.t, score: m.mg.score, over: m.mg.over }; });
    if (!info) break;
    // 偶爾（約 15%）故意唔接，令分數更似真人
    const c = await artToClient(info.tgt, 300); await page.mouse.move(c.x, c.y);
    if (!shotMid && info.t > 20) { shotMid = true; await shot('14-minigame-play'); }
    await page.waitForTimeout(70);
  }
  await page.waitForTimeout(700);
  ok(await page.isVisible('#modal'), '接星屑完結出現結算'); await shot('15-minigame-result');
  const res = await G(() => Glimmer.ui && __glimmer.lastMG);
  ok(res && res.grains === Math.min(20, Math.floor(res.score / 10)) && res.ratio === 1, '光粒 = floor(分數/10)（cap 20），首次全額', JSON.stringify(res));
  s = await st(); ok(s.grains === grains0 + res.grains, '光粒已加入', s.grains);
  await closeModals();

  console.log('# 進化分支（燦光 CQ≥70）');
  await G(() => { const x = __glimmer.state; x.cq = 82; x.growthSec = Glimmer.data.PARAMS.stageSec.sprout - 3; });
  await page.waitForTimeout(5000);
  s = await st(); ok(s.stage === 'adult' && s.form === 'bright', 'CQ 82 → 守夜者「燦光」', s.stage + '/' + s.form);
  await shot('16-evolve-modal'); await closeModals(); await page.waitForTimeout(2500); await shot('17-adult-bright');

  console.log('# 後處理畫質（燦光成體）');
  for (const q of ['high', 'mid', 'low', 'off']) { await G((q) => __glimmer.setQuality(q), q); await page.waitForTimeout(500); await shot('18-fx-' + q); }
  await G(() => __glimmer.setQuality('high'));
  console.log('# 日夜燈色');
  for (const h of [5, 9, 14, 18, 22]) { await G((h) => { __glimmer.hourOverride = h; }, h); await page.waitForTimeout(450); await shot('19-time-' + String(h).padStart(2, '0')); }
  await G(() => { __glimmer.hourOverride = 23; __glimmer.state.needs.energy = 40; }); await page.waitForTimeout(600); await shot('20-night-suggest');
  ok(await page.evaluate(() => document.getElementById('btn-sleep').classList.contains('hint')), '23:00 後出現就寢建議');
  await G(() => { __glimmer.hourOverride = null; });

  console.log('# 其他分支（柔光／微塵）');
  for (const [cq, f, nm] of [[55, 'soft', '21-adult-soft'], [20, 'dust', '22-adult-dust']]) {
    await G((cq) => { const x = __glimmer.state; x.stage = 'sprout'; x.form = null; x.cq = cq; x.growthSec = Glimmer.data.PARAMS.stageSec.sprout - 3; for (const k of ['hunger', 'mood', 'clean', 'energy']) x.needs[k] = 80; }, cq);
    await page.waitForTimeout(5000); s = await st(); ok(s.form === f, `CQ ${cq} → ${f}`, s.form); await closeModals(); await page.waitForTimeout(1800); await shot(nm);
  }

  console.log('# 設定／畫質持久化');
  await click('[data-testid=gear]'); await shot('23-settings'); await click('[data-testid=q-mid]'); await click('[data-testid=modal-btn-0]');
  await G(() => { const x = __glimmer.state; x.stage = 'adult'; x.form = 'bright'; x.cq = 50; for (const k of ['hunger', 'mood', 'clean', 'energy']) x.needs[k] = 70; });

  console.log('# 存檔／重載／離線摘要（T=6h, 30h）');
  await page.goto(BASE + '?debug=1'); await page.waitForTimeout(800); // 唔帶 q 參數，驗證畫質由存檔還原
  for (const [hrs, nm] of [[6, '24-offline-6h'], [30, '25-offline-30h']]) {
    await G((hrs) => { const x = __glimmer.state; x.stage = 'sprout'; x.form = null; x.growthSec = 1000; x.sleeping = false; for (const k of ['hunger', 'mood', 'clean', 'energy']) x.needs[k] = hrs === 6 ? 100 : 40; x.poops = 0; __glimmer.save(); }, hrs);
    const before = await st();
    // 模擬離開：把 lastSeen 往前推，然後重載（頁面 pagehide 會覆寫 lastSeen，所以先清旗標）
    await G((hrs) => { window.__noSaveOnHide = true; const k = Glimmer.data.PARAMS.saveKey; const o = JSON.parse(localStorage.getItem(k)); o.lastSeen = Date.now() - hrs * 3600e3; localStorage.setItem(k, JSON.stringify(o)); }, hrs);
    await page.reload(); await page.waitForTimeout(1100);
    const after = await st();
    const E = hrs === 6 ? 6 : 12;
    ok(await page.isVisible('#modal') && await page.textContent('#mbox h2').then(t => t.includes('你不在時')), `T=${hrs}h 重載出現回歸摘要`);
    const nLines = await page.$$eval('#mbox p', ps => ps.length); ok(nLines <= 3 && nLines >= 1, '摘要 ≤3 句（' + nLines + '）');
    ok(Math.abs(after.growthSec - (1000 + E * 3600 * 0.5)) < 120, `離線成長 = E(${E}h)×50%`, after.growthSec.toFixed(0));
    ok(['hunger', 'mood', 'clean', 'energy'].every(k => after.needs[k] >= 19.9), '離線需求保底 ≥20', JSON.stringify(after.needs));
    ok(after.q === 'mid', '畫質設定經重載保留 (mid)', after.q);
    ok(after.grains > before.grains, '回歸禮物光粒 +' + (after.grains - before.grains));
    await shot(nm); await closeModals();
  }

  console.log('# 桌面視窗縮放');
  await page.setViewportSize({ width: 1280, height: 800 }); await page.waitForTimeout(600); await shot('26-desktop-1280x800');
  const li = await G(() => __glimmer.layoutInfo); ok(li.cssW > 300 && li.cssH <= 800, '縮放至適合視窗', JSON.stringify(li));
  await page.setViewportSize({ width: 360, height: 740 }); await page.waitForTimeout(600); await shot('27-small-360x740');
  await page.setViewportSize({ width: 390, height: 844 }); await page.waitForTimeout(400);

  console.log('# 後處理幀時間（headless 軟件渲染，非真機；每檔 120 幀 renderer.frame 耗時）');
  await G(() => { __glimmer.state.stage = 'adult'; __glimmer.state.form = 'bright'; __glimmer.hourOverride = 21; });
  const bench = [];
  for (const q of ['off', 'low', 'mid', 'high']) { const r = await G((q) => __glimmer.bench(q, 120), q); bench.push(r); console.log('  ' + JSON.stringify(r)); }
  ok(bench.every(b => b.avgMs < 60), '各畫質平均幀時間 < 60ms（headless）');

  console.log('# 無 debug 時唔顯示面板');
  await page.goto(BASE); await page.waitForTimeout(700); ok(!(await page.isVisible('#dbgT')), '無 ?debug=1 → 冇 debug 控制'); 

  ok(errs.length === 0, 'console 無 error/warning', errs.join(' | '));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
