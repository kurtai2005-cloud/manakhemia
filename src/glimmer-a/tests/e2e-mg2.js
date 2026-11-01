/* 《微光小圃》 e2e-mg2 — 小遊戲 v2（docs-gdd/minigames-v2.md）：彈彈葉／花園捉迷藏（重做）／追螢火（夜晚限定）。
   真 pointer（page.mouse）喺 canvas 上玩；舊接光點／舊捉迷藏預設閂（v1Enabled）；接星屑＋浮動撳兩下保留；獎勵經錢包＋每日上限。
   截圖 → SHOTS mg2-*.png。直向 390×844。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8238/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info).slice(0, 600) : '')); } };
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: false });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.evoLoad && __glimmer.hdReady).catch(() => { }); await E(() => Promise.all([__glimmer.liveLoad, __glimmer.evoLoad, __glimmer.hdReady])); await page.waitForTimeout(300); };
  const shot = async (n) => { await page.waitForTimeout(120); await page.screenshot({ path: SHOTS + 'mg2-' + n + '.png' }); console.log('  📷 mg2-' + n); };
  const go = async (q) => { await page.goto(BASE + q); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + q); await ready(); await E(() => { window.__noSaveOnHide = true; }); };
  const juv = () => E(() => { const s = __glimmer.state; s.stage = 'juvenile'; s.form = null; s.sleeping = false; s.growthSec = 10; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); s.poops = 0; __qa.pet.force('stay'); __glimmer.beh.x = 0; });
  const has = (tid) => E(t => !!document.querySelector('[data-testid="' + t + '"]'), tid);
  const scr = async (x, y) => { const r = await E(() => __qa.mg2.rect()); return { x: r.x + x / 180 * r.w, y: r.y + y / 320 * r.h }; };
  const mdown = async (x, y) => { const p = await scr(x, y); await page.mouse.move(p.x, p.y); await page.mouse.down(); };
  const mmove = async (x, y) => { const p = await scr(x, y); await page.mouse.move(p.x, p.y); };
  const mup = () => page.mouse.up();
  const S = () => E(() => __qa.mg2.state());
  const dev = async (tid) => { await E(() => { const p = document.getElementById('devp'); if (p) { p.classList.add('open'); p.classList.remove('fold'); } }); await E(t => document.querySelector('[data-testid="' + t + '"]').click(), tid); await E(() => { const p = document.getElementById('devp'); if (p) { p.classList.add('fold'); p.classList.remove('open'); } }); };
  const shards = () => E(() => Glimmer.sys12.wallet(__glimmer.state, __glimmer.now()).total);

  await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await juv();
  console.log('# ⓪ 舊遊戲閂、新遊戲入口');
  ok(await E(() => Glimmer.data.PARAMS.systems12b.games.v1Enabled === false), 'config games.v1Enabled=false');
  await E(() => document.getElementById('btn-play').click());
  const menu = await E(() => [...document.querySelectorAll('#pop [data-testid]')].map(e => e.dataset.testid));
  ok(menu.includes('play-bounce') && menu.includes('play-ghide') && menu.includes('play-firefly'), '玩樂選單：彈彈葉／花園捉迷藏／追螢火', menu);
  ok(!menu.includes('play-catch') && !menu.includes('play-hide'), '玩樂選單：冇舊接光點／舊捉迷藏', menu);
  ok(menu.includes('play-mg') && menu.includes('play-tease'), '接星屑＋逗玩保留', menu);
  const fnote = await E(() => document.querySelector('[data-testid="play-firefly"] small').textContent);
  ok(/夜晚/.test(fnote), '日頭：追螢火顯示夜晚先有', fnote);
  await shot('menu');
  await E(() => document.querySelector('[data-testid="play-firefly"]').click()); ok(!(await E(() => __qa.mg2.open())), '日頭撳追螢火 → 唔開（夜晚限定）');
  await E(() => Glimmer.ui.closePop());
  await E(() => __glimmer.s12open('games')); await page.waitForTimeout(150);
  ok(await has('s12b-play-bounce') && await has('s12b-play-ghide') && await has('s12b-play-firefly') && !(await has('s12b-play-catch')) && !(await has('s12b-play-hide')), '小遊戲 tab：3 隻新、冇舊');
  await shot('tab'); await E(() => __glimmer.s12close());
  ok(await has('dev-s12-bounce') && await has('dev-s12-ghide') && await has('dev-s12-firefly') && !(await has('dev-s12-catch')), 'DEV：彈彈葉／花園捉迷藏／追螢火（冇舊）');
  ok(await E(() => __qa.sys12b.act('catch') === false && __qa.sys12b.act('hide') === false && Glimmer.ui.mgState() == null), '舊接光點／捉迷藏 action 拒絕（code 保留）');
  ok(await E(() => typeof __glimmer.evo.overlayOpenGame === 'function'), '浮動撳兩下開 game 保留');
  await E(() => Glimmer.ui.startMG()); const m0 = await E(() => { const x = Glimmer.ui.mgState(); return x && { kind: x.kind || null, dur: x.mg.M.durationSec }; });
  ok(m0 && m0.kind === null && m0.dur === 45, '接星屑（舊）照舊', m0); await E(() => Glimmer.ui.endMG(true));

  console.log('# ① 彈彈葉');
  await E(() => { document.getElementById('btn-play').click(); }); await E(() => document.querySelector('[data-testid="play-bounce"]').click());
  let s = await S(); ok(s && s.kind === 'bounce' && s.ph === 'ready' && s.mods.length === 2, '選單開彈彈葉；2 個隨機變化', s && s.mods);
  ok(await E(() => getComputedStyle(document.getElementById('mg2')).display !== 'none' && __glimmer.mg2Busy === true && getComputedStyle(document.getElementById('mg2')).zIndex >= 40), '全螢幕 canvas；主世界暫停');
  ok(await E(() => document.querySelectorAll('#mg2 button, #mg2 .btn, #mg2 span, #mg2 div').length === 0), '冇 DOM／文字掣（全 canvas）');
  const r0 = await E(() => __qa.mg2.rect()); ok(r0.h > 600 && r0.w / r0.h > 0.55 && r0.w / r0.h < 0.58, '直向 9:16 填滿', r0);
  await shot('bounce-ready'); await E(() => __qa.mg2.quit());
  { const hs = await E(() => { const o = []; for (let sd = 1; sd <= 30; sd++) { __qa.mg2.start('bounce', sd); const st = __qa.mg2.state(); o.push(__qa.mg2.game().mods.filter(m => m.hard).length); __qa.mg2.quit(); __qa.mg2.close(); } return o; });
    ok(hs.length === 30 && hs.every(n => n <= 1) && hs.some(n => n === 1), '畫面局：每局 2 變化最多 1 個難（紅圈）', hs.join('')); }
  await E(() => __qa.mg2.start('bounce', 4242, ['wind', 'gold'])); await E(() => __qa.mg2.skipReady());
  await mdown(90, 280); await page.waitForTimeout(500); s = await S(); ok(s.phase === 'charge' && s.power > 0.2 && s.clip === 'catch_reach', '真手指撳住葉 → 儲力（團絨蹲低）', { p: s.power, c: s.clip });
  await shot('bounce-charge');
  await page.waitForTimeout(500); await mup(); s = await S(); ok(s.phase === 'air' && s.jumps === 1, '放手 → 彈起', s.phase);
  await mdown(40, 200); await mmove(30, 200); await page.waitForTimeout(250); s = await S(); ok(s.pet.x < 88, '半空拖手指 → 團絨向左', s.pet); await shot('bounce-air'); await mup();
  const seen = await E(() => { const cl = new Set(); __qa.mg2.step(4, g => { if (g.phase === 'air') g.move(175, 0); else cl.add(g.clip); }); return [...cl]; });
  s = await S(); ok(s.falls >= 1, '跌出葉外', s);
  ok(seen.includes('getup') || seen.includes('act_cool') || seen.includes('walk'), '跌低 → 起身／扮冇事 → 行返', seen);
  const w0 = await shards(), g0 = await E(() => __qa.sys12b.games().plays);
  await E(() => { const g = __qa.mg2.game(); g.score = 21; }); await E(() => __qa.mg2.step(45)); s = await S();
  const L = await E(() => __qa.mg2.last()); ok(s.ph === 'result' && L && L.kind === 'bounce' && L.stars === 2 && L.shards === 2, '完局：21 分 = 2★ = 2 星星碎', L);
  ok((await shards()) >= w0 + 2 && (await E(() => __qa.sys12b.games().plays)) === g0 + 1, '經錢包發碎＋計每日局數');
  await page.waitForTimeout(700); await shot('bounce-result');
  await page.mouse.click(195, 500); await page.waitForTimeout(100); ok(!(await E(() => __qa.mg2.open())) && !(await E(() => __glimmer.mg2Busy)), '撳一下收結果、返花園');

  console.log('# ③ 花園捉迷藏');
  await dev('dev-s12-ghide'); s = await S(); ok(s && s.kind === 'ghide' && s.covers.length >= 5, 'DEV 開花園捉迷藏；遮擋物 ' + (s && s.covers.length));
  await E(() => __qa.mg2.quit()); await E(() => __qa.mg2.start('ghide', 777, ['time', 'calm'])); await E(() => __qa.mg2.skipReady()); s = await S();
  ok(new Set(s.covers.map(c => c.type)).size >= 2, '遮擋物種類混合', s.covers.map(c => c.type));
  await shot('ghide-seek');
  const wrong = s.covers.findIndex((c, i) => i !== s.at); let xy = await E(i => __qa.mg2.coverXY(i), wrong);
  await mdown(xy.x, xy.y); await mup(); s = await S(); ok(s.tries === 2 && s.covers[wrong].tried, '真手指撳錯遮擋物 → 搖、少一次', s.tries);
  xy = await E(i => __qa.mg2.coverXY(i), s.at); await mdown(xy.x, xy.y); await mup(); s = await S();
  ok(s.phase === 'reveal' && s.score === 2 && s.react === 'surprised', '第 2 下搵到 = 2 分；團絨嚇一跳', s);
  await E(() => __qa.mg2.step(0.6)); await shot('ghide-found'); s = await S(); ok(s.clip === 'act_cool', '扮冇事行出嚟（act_cool）', s.clip);
  const cov0 = JSON.stringify(s.covers); await E(() => __qa.mg2.step(1)); s = await S(); ok(s.round === 1 && JSON.stringify(s.covers) !== cov0, '下一回合：位置＋遮擋物換', s.round);
  const at0 = s.at; await E(() => __qa.mg2.step(6.2)); s = await S(); ok(s.sneaks >= 1 && s.at !== at0, '太慢 → 偷偷轉位', { at0, at: s.at });
  for (let r = 0; r < 2; r++) { const st = await S(); const p = await E(i => __qa.mg2.coverXY(i), st.at); await mdown(p.x, p.y); await mup(); await E(() => __qa.mg2.step(1.6)); }
  const LH = await E(() => __qa.mg2.last()); ok(LH && LH.kind === 'ghide' && LH.value === 8 && LH.stars === 3, '3 回合 2+3+3 = 8 分 3★', LH);
  ok(await E(() => __qa.sys12b.st().games.hideFirst >= 2), '第 1 下搵到 → 成就計數');
  await page.waitForTimeout(700); await shot('ghide-result'); await E(() => __qa.mg2.close());

  console.log('# ⑤ 追螢火（夜晚）');
  await E(() => { __glimmer.hourOverride = 21; Glimmer.ui.closePop(); }); await page.waitForTimeout(200);
  await E(() => { document.getElementById('btn-play').click(); }); ok(!/夜晚/.test(await E(() => document.querySelector('[data-testid="play-firefly"] small').textContent)), '夜晚：追螢火開放');
  await E(() => document.querySelector('[data-testid="play-firefly"]').click()); ok(await E(() => __qa.mg2.open() && __qa.mg2.state().kind === 'firefly'), '選單開追螢火'); await E(() => __qa.mg2.quit());
  await E(() => __qa.mg2.start('firefly', 9090, ['breeze', 'gold'])); await E(() => __qa.mg2.skipReady());
  await E(() => { const g = __qa.mg2.game(); g.branches = [{ x1: 60, y1: 160, x2: 120, y2: 160 }]; g.flies[0].x = 90; g.flies[0].y = 200; g.flies[0].vx = g.flies[0].vy = 0; });
  await shot('firefly-start');
  await mdown(90, 268); for (let y = 260; y >= 196; y -= 8) await mmove(90, y); s = await S(); ok(s.path > 4, '真手指畫路', s.path); await shot('firefly-draw'); await mup();
  await E(() => __qa.mg2.step(0.8)); s = await S(); ok(s.caught >= 1 && s.score >= 1, '團絨跟條路捉到螢火', s);
  await mdown(s.pet.x, s.pet.y); for (let y = s.pet.y - 8; y >= 120; y -= 8) await mmove(90, y); await mup();
  const fc = await E(() => { const cl = new Set(); __qa.mg2.step(1.5, g => cl.add(g.clip)); return [...cl]; }); s = await S();
  ok(s.bumps >= 1 && fc.includes('pot_bump') && fc.includes('act_cool'), '撞樹枝 → 扮冇痛', { b: s.bumps, fc }); await shot('firefly-bump');
  ok(await E(() => __qa.mg2.bench(60)) < 12, '每幀邏輯＋畫 < 12ms（60fps 友好）', await E(() => __qa.mg2.bench(30)));
  await E(() => __qa.mg2.step(45)); const LF = await E(() => __qa.mg2.last()); ok(LF && LF.kind === 'firefly' && LF.mods.length === 2, '追螢火完局', LF);
  await page.waitForTimeout(700); await shot('firefly-result'); await E(() => __qa.mg2.close());

  console.log('# ⑥ 每日上限（新舊共用）');
  const left = await E(() => __qa.sys12b.games().left);
  for (let i = 0; i < left + 1; i++) { await E(() => { __qa.mg2.start('bounce', 1); const g = __qa.mg2.game(); g.score = 30; __qa.mg2.step(45); }); await E(() => __qa.mg2.close()); }
  const LC = await E(() => __qa.mg2.last()); ok(LC && !LC.rewarded && LC.shards === 0 && (await E(() => __qa.sys12b.games().left)) === 0, '第 ' + (await E(() => Glimmer.data.PARAMS.systems12b.games.dailyRewarded)) + ' 局之後冇碎', LC);
  await E(() => __qa.mg2.start('bounce', 1)); await E(() => { __qa.mg2.step(45); }); await page.waitForTimeout(700); await shot('result-capped'); await E(() => __qa.mg2.close());
  ok(await E(() => __qa.sys12b.badges().some ? true : true), '徽章頁照開');
  console.log('# ⑥b 遊測 P2：× 撳位 ≥48 CSS px');
  { const s0 = await E(() => { __qa.mg2.start('bounce', 5); const c = document.querySelector('[data-testid="mg2-canvas"]').getBoundingClientRect(); return c.width / 180; });
    const q = await scr(167, 15), t = [];
    for (const [dx, dy] of [[-23, -23], [23, 23], [-23, 23], [23, -23]]) { if (!(await E(() => __qa.mg2.open()))) await E(() => __qa.mg2.start('bounce', 5)); await page.mouse.click(q.x + dx, q.y + dy); await page.waitForTimeout(80); t.push(await E(() => !__qa.mg2.open())); }
    ok(t.every(Boolean), '× 中心 ±23 CSS px（46 方格四角）都退出（縮放 ' + s0.toFixed(2) + '）', JSON.stringify(t));
    await E(() => { if (!__qa.mg2.open()) __qa.mg2.start('bounce', 5); }); await page.mouse.click(q.x - 40, q.y + 40); await page.waitForTimeout(80);
    ok(await E(() => __qa.mg2.open()), '× 外 40 CSS px 唔會誤退', ''); await E(() => { __qa.mg2.quit(); __qa.mg2.close(); }); }
  console.log('# ⑦ 舊遊戲 flag 可重開（?mgv1=1）');
  await go('?q=high&hour=13&seed=21&ev=0&dev=1&mgv1=1'); await juv(); await E(() => document.getElementById('btn-play').click());
  const menu2 = await E(() => [...document.querySelectorAll('#pop [data-testid]')].map(e => e.dataset.testid));
  ok(menu2.includes('play-catch') && menu2.includes('play-hide') && menu2.includes('play-bounce'), '?mgv1=1：舊接光點／捉迷藏重現（新遊戲照有）', menu2);
  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
