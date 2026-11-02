/* 《微光小圃》 e2e-touch — 第 3 批 3a（docs-gdd/batch3-fun-spec.md §①②）：真滑鼠手勢（戳／長按 3s 摸頭／搔癢→碌地笑／拉開彈返）＋devicemotion 搖機暈、
   心情每種每日第一次 +1（同浮動 fpet_daily_v1 共用 ≤5）、提示排隊（同一時間一個泡）、扮醒呆 6 款＋戳佢尷尬＋圖鑑呆呆時刻＋徽章、瞓覺揉眼翻身。截圖 → SHOTS touch-*.png */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8138/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const D = require('../src/data.js');
const LINES = require('../src/touch.js').LINES;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = async (n) => { await W(120); const h = await E(() => __qa.pet.hitBox()); await page.screenshot({ path: SHOTS + 'touch-' + n + '.png', clip: { x: 0, y: Math.max(0, h.css.y - 260), width: 390, height: 420 } }); console.log('  📷 touch-' + n); };
  const load = async (qs, pre) => {
    await page.goto(BASE + '?' + qs); await E((pre) => { window.__noSaveOnHide = true; localStorage.clear(); if (pre) for (const k in pre) localStorage.setItem(k, pre[k]); }, pre || null);
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await W(300);
    await E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; __qa.pet.force('stay'); __glimmer.beh.x = 0; });
    await W(400);
  };
  const center = async () => { const h = await E(() => __qa.pet.hitBox()); return { x: h.css.x + h.css.w / 2, y: h.css.y + h.css.h / 2 }; };
  const st = () => E(() => __qa.touch.st());
  const okGrant = (s, k) => s.grants.some(g => g.kind === k && g.ok);
  const seen = async (key, ms) => E(([key, ms]) => new Promise(res => { const t0 = performance.now(); (function f() { const g = __glimmer.beh.gest; if (g && g.key === key) return res(true); if (performance.now() - t0 > ms) return res(false); requestAnimationFrame(f); })(); }), [key, ms]);
  const voice = () => E(() => { const v = document.querySelector('[data-testid=s12-voice]'); return { text: v.textContent.trim(), op: +getComputedStyle(v).opacity, src: v.dataset.src || null }; });

  console.log('# ① 觸摸互動（真滑鼠）');
  await load('q=high&hour=13&seed=11&ev=0');
  await E(() => { window.__patN = 0; const X = Glimmer.sys12, f = X.notePat; X.notePat = function () { window.__patN++; return f.apply(this, arguments); }; });
  let c = await center(), m0 = await E(() => __glimmer.state.needs.mood);
  const pk = seen('g_poke', 600); await page.mouse.click(c.x, c.y); ok(await pk, '戳：squash 動作 g_poke');
  let s = await st(); ok(okGrant(s, 'poke') && s.mood.shared === 1, '戳：今日第一次 心情 +1（共用額 1）', s.grants);
  ok(await E(() => window.__patN) === 1, '短撳照舊計一次摸頭（v10.2）');
  await W(400); await page.mouse.click(c.x, c.y); await W(100); s = await st(); ok(s.grants.filter(g => g.kind === 'poke').slice(-1)[0].reason === 'repeat' && s.mood.shared === 1, '同日再戳唔再加');
  await W(700); c = await center(); await E(() => { window.__patN = 0; }); await page.mouse.move(c.x, c.y); await page.mouse.down();
  await W(900); s = await st(); ok(s.act && s.act.key === 'g_hold' && okGrant(s, 'hold'), '長按 ≥0.6s：瞇眼舒服 g_hold＋心情', s.act);
  let fh = await E(() => __glimmer.beh.face); for (let i = 0; i < 10 && fh.eyes !== 'happy'; i++) { await W(60); fh = await E(() => __glimmer.beh.face); } ok(fh.eyes === 'happy', '長按表情：合眼笑', fh);   /* #83：nuzzle clip 有幾格 squint（v3=0 一樣）→ 撳住期間 600ms 內見到合眼笑就算 */
  await shot('hold');
  await W(2400); ok(await E(() => window.__patN) === 1, '持續 3s ＝ 一次摸頭（未鬆手已計）');
  await page.mouse.up(); await W(200); ok(await E(() => window.__patN) === 1, '鬆手唔再重覆計摸頭');
  await W(600); c = await center(); await page.mouse.move(c.x, c.y); await page.mouse.down();
  for (let i = 0; i < 8; i++) { await page.mouse.move(c.x + (i % 2 ? -10 : 10), c.y); await W(90); }
  s = await st(); ok(okGrant(s, 'tickle') && s.act && /^g_(tickle|roll)$/.test(s.act.key), '1s 內來回擦 ≥4 次：搔癢笑', s.act);
  await shot('tickle');
  for (let i = 0; i < 40; i++) { await page.mouse.move(c.x + (i % 2 ? -10 : 10), c.y); await W(90); }
  s = await st(); ok(s.log.some(l => l.key === 'g_roll'), '再擦 3s：碌地笑 g_roll', s.log.map(l => l.key));
  let v = await voice(); ok(v.text === LINES.tickle && v.op > 0.5, '心聲「我…我一啲都唔怕癢㗎！」', v);
  await page.mouse.up(); await W(2800);
  c = await center(); await page.mouse.move(c.x, c.y); await page.mouse.down();
  for (let i = 1; i <= 8; i++) { await page.mouse.move(c.x + i * 9, c.y + 2); await W(30); }
  s = await st(); ok(s.act && s.act.key === 'g_pull', '拖住：拉長 g_pull', s.act); await shot('pull');
  const sp = seen('g_spring', 600); await page.mouse.up(); ok(await sp, '拖離 >40px 放手：彈簧彈返 g_spring'); s = await st(); ok(okGrant(s, 'pull'), '拉開：心情 +1');
  await W(1000);
  await E(() => { const ev = (g) => window.dispatchEvent(new DeviceMotionEvent('devicemotion', { accelerationIncludingGravity: { x: g * 9.81, y: 0, z: 0 } })); ev(3); setTimeout(() => ev(3.2), 300); });
  await W(450); s = await st(); ok(s.act && s.act.key === 'g_dizzy' && okGrant(s, 'shake'), 'devicemotion 1s 內兩次 >2.5g：暈 g_dizzy', s.act);
  const gz = await E(() => __glimmer.renderer.faceStat.last.gest); ok(gz && gz.rx && gz.clip === 'touch_shake_dizzy' && gz.faceOn && /dizzy/.test(gz.face || ''), '暈：遊美 clip touch_shake_dizzy（face patch dizzy）', gz);
  await shot('dizzy');
  s = await st(); ok(s.mood.shared === 5 && s.grants.filter(g => g.ok).length === 5, '5 種手勢各一次 → 共用額 5', s.mood);
  const lsN = await E(() => { const d = new Date(); return JSON.parse(localStorage.getItem('fpet_daily_v1'))[d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate()]; }); ok(lsN === 5, 'localStorage fpet_daily_v1（浮動團絨同一個 key）＝ 5', lsN);
  await W(300); await E(() => { __qa.touch.shake(3, 1000); __qa.touch.shake(3, 1000.4); __qa.touch.shake(3, 1010); __qa.touch.shake(3, 1010.4); __qa.touch.shake(3, 1020); __qa.touch.shake(3, 1020.4); }); await W(700);   // 遊美 touch_shake_pretend：line 事件喺 300ms
  v = await voice(); ok(v.text === LINES.brag || (await E(() => __glimmer.nq.log.some(l => l.line === '頭先係我故意轉嘅'))), '1 分鐘內搖 3 次 →「頭先係我故意轉嘅」', v);

  console.log('# 共用上限：浮動已用 4 → 手勢只得 1');
  const dk = (() => { const d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); })();
  await load('q=high&hour=13&seed=12&ev=0', { fpet_daily_v1: JSON.stringify({ [dk]: 4 }) });
  await E(() => { __qa.touch.gesture('poke'); __qa.touch.gesture('hold'); __qa.touch.reset(); }); s = await st();
  ok(okGrant(s, 'poke') && s.grants.find(g => g.kind === 'hold').reason === 'cap' && s.mood.shared === 5, '第 5 下之後 cap（同浮動 ≤5）', s.grants);
  // 同一個 evaluate 內前後比（唔會中間行 tick）；只比照顧／事件計數＋路線分（時間驅動欄唔比）
  const rp = await E(() => { const S = __glimmer.state, snap = () => JSON.stringify({ care: S.evo && S.evo.care, evIn: S.evo && S.evo.evIn, route: S.route || null, b5: S.evo && S.evo.b5 }); const a = snap(); __qa.touch.gesture('tickle'); __qa.touch.gesture('pull', { dx: 60 }); __qa.touch.gesture('poke'); return { a, b: snap() }; });
  ok(rp.a === rp.b, '手勢唔郁 evo 照顧／事件計數／路線分', rp.a === rp.b ? undefined : rp);

  console.log('# ⓪ 提示排隊');
  await E(() => { __qa.touch.reset(); Object.assign(__glimmer.state.needs, { hunger: 10 }); }); await W(400);
  ok(await E(() => getComputedStyle(document.getElementById('bubble')).display !== 'none'), '冇心聲時：狀態氣泡「好肚餓…」照出');
  await E(() => { __glimmer.say({ line: '第一句', sec: 1.5 }); __glimmer.say({ line: '第二句', sec: 1.5 }); }); await W(150);
  const q1 = await E(() => ({ v: document.querySelector('[data-testid=s12-voice-text]').textContent, op: +getComputedStyle(document.querySelector('[data-testid=s12-voice]')).opacity, bub: getComputedStyle(document.getElementById('bubble')).display, n: __glimmer.nq.size() }));
  ok(q1.v === '第一句' && q1.op > 0.5 && q1.bub === 'none' && q1.n === 2, '同一時間一個：第一句出、第二句排隊、狀態氣泡讓位', q1);
  await shot('queue');
  await W(1800); ok(await E(() => document.querySelector('[data-testid=s12-voice-text]').textContent) === '第二句', '第一句完 → 第二句');
  await W(1800); ok(await E(() => getComputedStyle(document.getElementById('bubble')).display !== 'none' && !__glimmer.nq.busy(performance.now())), '排完 → 狀態氣泡返嚟');
  await E(() => { Object.assign(__glimmer.state.needs, { hunger: 100 }); const r = __glimmer.sysVoice({ src: 'app', force: true }); window.__vr = r; }); await W(100);
  ok(await E(() => !window.__vr.ok || __glimmer.nq.log.some(l => l.line === window.__vr.line)), '親密度心聲（sysVoice）都經排隊', await E(() => window.__vr));

  console.log('# ② 扮醒呆反應包');
  const RXC = { glasses: 'dim_glasses_count', book: 'dim_book_sleep', wall: 'dim_wall_bump', mirror: 'dim_mirror', finger: 'dim_count_fingers', prof: 'dim_professor' };
  await load('q=high&hour=13&seed=13&ev=0');
  for (const k of ['glasses', 'book', 'wall', 'mirror', 'finger', 'prof']) {
    await E((k) => { __qa.touch.reset(); __glimmer.nq.clear(); __qa.touch.dumb(k); }, k); await W(2600);
    s = await st(); v = await voice();
    ok(s.act && s.act.key === 'd_' + k && LINES.dumb[k].includes(v.text) && v.src === 'dumb', k + '：動作 d_' + k + '＋自信錯誤心聲', { act: s.act, v });
    const gk = await E(() => __glimmer.renderer.faceStat.last.gest); ok(gk && gk.rx && gk.clip === RXC[k] && gk.faceOn !== undefined, k + '：用遊美 clip ' + RXC[k], gk);
    if (k === 'mirror') ok(gk.fx.includes('fx_mirror_back') && gk.fx.includes('fx_mirror_front') && (await E(() => __glimmer.renderer.faceStat.rxReflect || 0)) > 0, '鏡：前後層＋倒影有畫', { fx: gk.fx, n: await E(() => __glimmer.renderer.faceStat.rxReflect) });
    await shot('dumb-' + k);
  }
  ok(await E(() => __glimmer.beh.state === 'stay' && __glimmer.beh.hushUntil > __glimmer.beh.t), '扮緊嘢：團絨企定（唔行開）');
  c = await center(); await page.mouse.click(c.x, c.y); await W(250); s = await st(); v = await voice();
  ok(s.act && s.act.key === 'd_caught' && v.text === LINES.caught, '做緊時戳佢 → 尷尬臉＋「我係試緊你咋」', { act: s.act, v }); await shot('caught');
  await W(2500); s = await st(); ok(s.seen.length === 6, '圖鑑呆呆時刻 6 格齊', s.seen);
  await W(1300); const bd = await E(() => __qa.sys12b.badges().list.find(b => b.k === 'dumb_all')); ok(bd && bd.got && bd.reward === 5, '收齊 → 普通徽章「收齊呆呆時刻」5 碎', bd);
  await E(() => __glimmer.ui ? 0 : 0); await E(() => Glimmer.ui.openDex()); await W(300);
  const dx = await E(() => [...document.querySelectorAll('[data-testid^="dex-dumb-"]')].map(e => e.dataset.got)); ok(dx.length === 6 && dx.every(g => g === '1'), '圖鑑 modal 呆呆時刻 6 格', dx);
  await page.screenshot({ path: SHOTS + 'touch-dex.png' }); console.log('  📷 touch-dex');
  await E(() => document.querySelector('.modal .btn, [data-testid=modal-btn-0]') && document.querySelector('.modal .btn, [data-testid=modal-btn-0]').click()); await W(200);
  console.log('# 自動抽（idle 20s／60s／25%；每日 8）');
  await load('q=high&hour=13&seed=14&ev=0');
  const ar = await E(() => { const r0 = Math.random; Math.random = () => 0.1; __qa.touch.reset(); const r = __qa.touch.roll(); Math.random = r0; return r; });
  ok(ar && ar.k && ar.n === 1, 'idle 夠 → 抽中 25% → 開始一款', ar);
  const ar2 = await E(() => { __qa.touch.reset(); const r0 = Math.random; Math.random = () => 0.1; const r = __qa.touch.roll(); Math.random = r0; return r; }); ok(!ar2, '隔唔夠 3 分鐘唔再抽');
  ok(await E(() => __qa.touch.st().autoDumb === false), 'Playwright 預設唔自動抽（?dumb=1 先開；唔擾其他 e2e）');

  console.log('# 瞓覺中：揉眼翻身，唔加心情');
  await E(() => { __qa.touch.reset(); __glimmer.state.needs.energy = 10; __glimmer.state.sleeping = true; }); await W(200); ok(await E(() => __glimmer.state.sleeping), '（瞓緊）');
  await E(() => { __qa.touch.shake(3, 2000); __qa.touch.shake(3, 2000.4); }); s = await st();
  ok(s.act && s.act.key === 'g_rub' && !s.grants.some(g => g.ok), '瞓覺搖機 → g_rub，冇心情', s);
  await W(300); const gr = await E(() => __glimmer.renderer.faceStat.last.gest); ok(gr && gr.rx && gr.clip === 'touch_sleep_rub', '瞓覺：遊美 clip touch_sleep_rub', gr);
  console.log('# ?rx=0 → 程序化後備');
  await load('q=high&hour=13&seed=15&ev=0&rx=0'); await E(() => { __qa.touch.reset(); __qa.touch.gesture('tickle'); }); await W(300);
  const gf = await E(() => __glimmer.renderer.faceStat.last.gest); ok(gf && !gf.rx && gf.key === 'g_tickle', '?rx=0：冇遊美圖都照郁（程序化）', gf);
  await E(() => { __glimmer.state.sleeping = false; });
  ok(!errs.length, '冇 console error／pageerror', errs.slice(0, 5));
  await browser.close();
  console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
