/* 《微光小圃》 e2e-s2b — 生命感 s2b：開發者面板「即刻觸發」＋「展示模式」＋遊美 s2 真 clip（smug_pose／act_cool／lookup_tip／getup／sniff_itch）＋fx 蟲仔。
   面板要喺正常開發模式（?dev=1／左上名牌 5 下）見到，唔使 ?debug=1。
   截圖 → SHOTS（預設 ../../screens/）s2b-*.png。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.SHOTS || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(180); await page.screenshot({ path: SHOTS + 's2b-' + n + '.png' }); console.log('  📷 s2b-' + n); };
  const load = async (qs, clear) => {
    if (clear) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await page.waitForTimeout(300);
    await E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'soft'; s.growthSec = 3600; Object.assign(s.needs, { hunger: 100, mood: 55, clean: 100, energy: 100 }); s.poops = 0; s.sleeping = false; });
    await page.waitForTimeout(200);
  };
  const st = () => E(() => __qa.pet.state());
  const prep = () => E(() => { __qa.pet.pause(true); __qa.pet.force('stay'); __qa.pet.step(0.4); __glimmer.beh.x = 0; __glimmer.beh.dir = 1; Object.assign(__glimmer.state.needs, { mood: 55, energy: 100, hunger: 100 }); });
  const LIVE = ['sniff', 'lookup', 'swat', 'scratch', 'sneeze', 'happy', 'drag', 'smug'];

  console.log('# 正常開發面板（冇 ?debug=1）見到生命感掣');
  await load('q=high&hour=13&seed=11&ev=0&dev=1', true);
  let vis = await E((L) => L.concat(['demo']).map(k => { const el = document.querySelector('[data-testid="dev-live-' + k + '"]'); return [k, !!el && el.offsetParent !== null]; }), LIVE);
  ok(vis.every(v => v[1]) && await E(() => { const g = document.getElementById('dbg'); return !g || g.offsetParent === null; }), '?dev=1：8 個即刻觸發掣＋展示模式掣可見（無 debug 面板）', JSON.stringify(vis));
  ok(await E(() => ['sniff_sneeze', 'lookup_tip', 'swat_miss', 'swat_hit'].every(n => { const el = document.querySelector('[data-testid="dev-chain-' + n + '"]'); return el && el.offsetParent !== null; })), '?dev=1：s2 強制鏈掣（嗅→噴嚏／望天→後倒／撲空→得意／拍中）可見');
  ok(await E(() => document.querySelector('[data-testid=dev-live-demo]').textContent === '展示模式 關' && !document.querySelector('[data-testid=dev-live-demo]').classList.contains('on') && !__glimmer.liveDemo), '展示模式預設關（面板顯示「關」）');
  await load('q=high&hour=13&seed=11&ev=0', true);
  ok(await E(() => !__qa.dev.isOpen()), '無 ?dev=1：面板預設收埋');
  for (let i = 0; i < 5; i++) { await page.mouse.click(60, 22); await page.waitForTimeout(40); }
  vis = await E((L) => __qa.dev.isOpen() && L.every(k => { const el = document.querySelector('[data-testid="dev-live-' + k + '"]'); return el && el.offsetParent !== null; }), LIVE);
  ok(vis, '左上名牌點 5 下：開面板，即刻觸發掣見到');

  console.log('# 即刻觸發：撳掣即出對應 clip（唔理冷卻／機率）');
  await load('q=high&hour=13&seed=11&ev=0&dev=1', true);
  const want = { sniff: ['sniff'], lookup: ['lookup'], swat: ['idle', 'swat'], scratch: ['scratch'], sneeze: ['sneeze'], smug: ['smug_pose'] };
  for (const k of Object.keys(want)) {
    await prep(); await E(() => { const b = __glimmer.beh; for (const m of ['scratch', 'sneeze', 'sniff', 'lookup', 'swat']) b.microAt[m] = b.t - 1; });   // 全部冷卻中
    await page.click('[data-testid="dev-live-' + k + '"]');
    const seen = await E(() => { const o = []; for (let i = 0; i < 40; i++) { const r = __qa.pet.step(1 / 30, 1 / 60); if (o[o.length - 1] !== r.show) o.push(r.show); if (r.state !== 'micro') break; } return o; });
    const last = await E(() => __qa.dev.calls[__qa.dev.calls.length - 1]);
    ok(want[k].every(c => seen.includes(c)) && last.name === 'live' && last.arg === k, k + ' 掣 → ' + seen.join('>'), JSON.stringify([seen, last]));
  }
  // 蟲仔 sprite＋真 smug（截圖）
  await prep(); await page.click('[data-testid=dev-live-swat]');
  let s = await E(() => { let r; for (let i = 0; i < 60; i++) { r = __qa.pet.step(1 / 60, 1 / 60); if (r.bug === 'buzz' && __glimmer.beh.t > 0) break; } __qa.pet.step(0.25, 1 / 60); return __qa.pet.state(); });
  await page.waitForTimeout(150); let f = await E(() => __qa.pet.face());
  ok(s.bug === 'buzz' && f.bugArt === true, '拍蟲掣：遊美 fx_bug 蟲仔喺頭邊飛', JSON.stringify([s.bug, f.bugArt])); await shot('bug');
  await prep(); await page.click('[data-testid=dev-live-smug]');
  s = await E(() => { let r; for (let i = 0; i < 60; i++) { r = __qa.pet.step(1 / 30, 1 / 60); if (r.showFrame === 3) break; } return r; }); await page.waitForTimeout(150); f = await E(() => __qa.pet.face());
  ok(s.show === 'smug_pose' && f.clip === 'smug_pose' && f.eyes === 'sleepy' && f.mouth === 'squint' && f.live, 'smug 掣：真 smug_pose（preset smug 臉）', JSON.stringify([s.show, f.clip, f.eyes, f.mouth])); await shot('smug');
  // 個性鏈照接：拍蟲 20 次，有撲空→得意
  const chain = await E(() => { let miss = 0, n = 0; for (let k = 0; k < 20; k++) { __qa.pet.force('stay'); __qa.pet.step(0.3); __qa.dev.live('swat'); const tags = new Set(); for (let i = 0; i < 200; i++) { const r = __qa.pet.step(1 / 30, 1 / 60); if (r.micro) tags.add(r.micro); if (r.state !== 'micro') break; } n++; if (tags.has('smug')) miss++; } return { miss, n }; });
  ok(chain.miss >= 8 && chain.miss < 20, '拍蟲掣：個性鏈照接（撲空→得意 ' + chain.miss + '/' + chain.n + '）');
  for (const [k, g] of [['happy', 'walk_happy'], ['drag', 'walk_drag']]) {
    await prep(); await page.click('[data-testid="dev-live-' + k + '"]');
    const r = await E(() => { let walkT = 0, shows = new Set(), gf = __qa.pet.gaitForce(); for (let i = 0; i < 60 * 8; i++) { const r = __qa.pet.step(1 / 60, 1 / 60); if (r.state === 'walk') { walkT += 1 / 60; shows.add(r.show); } else if (walkT > 0) break; } return { walkT, shows: [...shows], gf }; });
    ok(r.shows.join() === g && r.walkT >= 3.95 && r.walkT <= 6.05 && r.gf && r.gf.g === g, k + ' 掣：即刻用 ' + g + ' 行 ' + r.walkT.toFixed(2) + 's（4–6s）', JSON.stringify(r));
  }
  await prep(); await page.click('[data-testid=dev-live-happy]'); await E(() => __qa.pet.step(0.6, 1 / 60)); await page.waitForTimeout(120);
  ok((await st()).show === 'walk_happy', '開心步行緊（截圖）'); await shot('gait-happy');

  console.log('# 展示模式（×5 頻率、冷卻 ÷5、localStorage）');
  const base = await E(() => Glimmer.behavior.idleWeights(Object.assign({}, __glimmer.beh, { microAt: {}, lastIdle: null }), __glimmer.behCtx));
  await page.click('[data-testid=dev-live-demo]');
  let d = await E(() => ({ on: __glimmer.liveDemo, ls: localStorage.getItem('glimmer.liveDemo'), txt: document.querySelector('[data-testid=dev-live-demo]').textContent, cls: document.querySelector('[data-testid=dev-live-demo]').classList.contains('on'), st: document.querySelector('[data-testid=dev-live-demo-state]').textContent, w: Glimmer.behavior.idleWeights(Object.assign({}, __glimmer.beh, { microAt: {}, lastIdle: null }), __glimmer.behCtx) }));
  ok(d.on && d.ls === '1' && d.txt === '展示模式 開' && d.cls && /×5/.test(d.st), '撳展示模式 → 開（localStorage＋面板顯示「開」' + d.st + '）', JSON.stringify(d));
  ok(base.scratch > 0 && Math.abs(d.w.scratch - base.scratch * 5) < 1e-9, '展示模式：scratch 權重 ×5（' + base.scratch + ' → ' + d.w.scratch + '）');
  await E(() => __qa.pet.pause(false)); await shot('panel-demo');
  await page.reload(); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await page.waitForTimeout(400);
  d = await E(() => ({ on: __glimmer.liveDemo, beh: __glimmer.beh.demo, txt: document.querySelector('[data-testid=dev-live-demo]').textContent }));
  ok(d.on && d.beh && d.txt === '展示模式 開', '重載後展示模式仍開（localStorage）', JSON.stringify(d));
  const rate = (on) => E((on) => { __qa.pet.pause(true); __qa.dev.demo(on); __qa.pet.reseed(21); const s = __glimmer.state; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); __qa.pet.step(1800, 0.1); return __glimmer.beh.log.micro.length; }, on);
  const nOn = await rate(true), nOff = await rate(false);
  ok(nOn >= nOff * 3 && nOn > 0, '展示模式：30 分鐘小動作 ' + nOff + ' → ' + nOn + '（×' + (nOn / Math.max(1, nOff)).toFixed(1) + '）');
  await E(() => __qa.pet.pause(false));
  d = await E(() => (__glimmer.state.needs.mood = 55, { on: __glimmer.liveDemo, ls: localStorage.getItem('glimmer.liveDemo'), txt: document.querySelector('[data-testid=dev-live-demo]').textContent, beh: __glimmer.beh.demo, w: Glimmer.behavior.idleWeights(Object.assign({}, __glimmer.beh, { microAt: {}, lastIdle: null }), __glimmer.behCtx) }));
  ok(!d.on && d.ls === null && d.txt === '展示模式 關' && !d.beh && Math.abs(d.w.scratch - base.scratch) < 1e-9, '關展示模式：回復原狀（localStorage 清走、面板「關」）', JSON.stringify(d));
  await page.reload(); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await page.waitForTimeout(300);
  ok(await E(() => !__glimmer.liveDemo && !__glimmer.beh.demo), '重載後保持關');

  console.log('# ?debug=1 面板都有');
  await load('debug=1&q=high&hour=13&seed=11&ev=0', true);
  ok(await E(() => ['sniff', 'lookup', 'swat', 'scratch', 'sneeze', 'happy', 'drag', 'smug'].every(k => document.querySelector('[data-testid="dbg-now-' + k + '"]')) && !!document.querySelector('[data-testid=dbg-live-demo]')), 'debug 面板「即刻觸發」組（8 掣＋展示模式）');

  ok(errs.length === 0, 'console 無錯誤／警告', errs.slice(0, 5).join(' | '));
  await browser.close();
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
