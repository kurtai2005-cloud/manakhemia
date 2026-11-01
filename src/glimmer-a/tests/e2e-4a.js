/* 《微光小圃》 e2e-4a — 第 4 批 4a 細佬（docs-gdd/series2-4a4b-spec.md v1.1 §4a）：靜光 → 翌日蝸牛郵差送蛋、蛋 3 晚孵夢泡泡、孵化第一眼（2s／撳跳）、
   跟班升級場面、跟住行、道具托盤 → 拖畀團絨 → 示範錯（3a gest）→ 照抄、喊 → 拖團絨哄、一齊食／一齊瞓（朋友有被）、親密上限、朋友／家人場面、
   雙人彈彈葉（唔出碎）、S3 揭曉、S4–S6 形態、圖鑑、存檔、?s2=0、團絨路線分／碎唔受影響。截圖 → SHOTS。
   node tests/e2e-4a.js（BASE 預設 http://localhost:8240/index.html） */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const T0 = new Date(2026, 10, 2, 13, 0).getTime(), DAY = 86400e3, H = 3600e3;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n, clip) => page.screenshot(Object.assign({ path: SHOTS + '4a-' + n + '.png' }, clip ? { clip } : {}));
  const ZOOM = { x: 60, y: 420, width: 270, height: 200 };
  const q = () => E(() => __qa.s2.st());
  const until = async (fn, ms) => { const t0 = Date.now(); let s; while (Date.now() - t0 < (ms || 8000)) { s = await q(); if (fn(s)) return s; await W(100); } return q(); };
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const prep = (o) => E((o) => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = o.stage || 'elder'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 80, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; }, o || {});
  const load = async (qs, o) => {
    await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    if (o !== false) { await E(() => __glimmer.s2Load); await setT(T0); await prep(o); } await W(400);
  };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); } };
  const toKid = async (stageDay) => {   // 直接整一隻已孵化細佬（hatchDay = 今日 − stageDay）
    await E((d) => { const G = __glimmer, SR = Glimmer.series2, s = G.state, now = G.now(); SR.noteElder(s, now - 6 * 86400e3); const o = SR.st(s); o.dueDay = SR.dayNum(now) - 6; SR.deliver(s, now - 5 * 86400e3);
      o.dreams = [{ day: 1, line: 'A', at: 0, live: true }, { day: 2, line: 'A', at: 0, live: true }, { day: 3, line: 'E', at: 0, live: true }]; SR.hatch(s, now - d * 86400e3); o.relQ.length = 0; G.save(); }, stageDay || 0);
    await W(300);
  };
  const evoSnap = () => E(() => JSON.stringify({ evo: Object.assign({}, __glimmer.state.evo, { cl: null }),   // evo.cl＝時間累計（唔關事）
    w: Glimmer.sys12 && Glimmer.sys12.st ? Glimmer.sys12.st(__glimmer.state).wallet : null, g: Glimmer.sys12b.st(__glimmer.state).games.total }));

  console.log('# 載入／預設（webdriver 下唔自動送蛋／喊）');
  await load('q=high&hour=13&seed=21&ev=0', { stage: 'adult' });
  let s = await q(); ok(s.ready && !s.errors.length, '4a 圖全部載入', s.errors);
  ok(!s.auto.deliver && !s.auto.cry, 'webdriver 下 AUTO 閂', s.auto);
  ok(s.save.phase === 'none' && s.form === null, '未到靜光 → 冇細佬', { p: s.save.phase, f: s.form });
  { const h = await E(() => __qa.s2.dex()); ok(h && h.includes('未遇見') && h.includes('dex-s2-lock-kid') && (h.match(/dex-s2-lock-dream-/g) || []).length === 3 && (h.match(/dex-s2-lock-lesson-/g) || []).length === 6, '4a.1：未有蛋圖鑑都有新寵物系列（未遇見剪影）', h && h.slice(0, 120)); }
  await E(() => Glimmer.ui.openDex()); await W(400); await page.locator('[data-testid=dex-s2]').scrollIntoViewIfNeeded(); ok(await page.locator('[data-testid=dex-s2] [data-locked="1"]').count() >= 10, '圖鑑 DOM 有鎖住格'); ok(await E(() => { const r = document.getElementById('mbox').getBoundingClientRect(), md = document.getElementById('modal'); if (r.top >= 0 && r.bottom <= innerHeight) return true; return !!(window.__qa.uiv2 && __qa.uiv2.st().on) && r.top >= 0 && getComputedStyle(md).overflowY === 'auto' && md.scrollHeight > md.clientHeight; }), '未有蛋圖鑑（連新系列）成個塞得落一版（5a.1 v2 大字：唔縮字，改做可以碌）'); await shot('00-dex-locked'); await closeModals();
  ok(await E(() => Glimmer.data.PARAMS.series2.enabled === true), 'PARAMS.series2 開');

  console.log('# 攞蛋：靜光 → 翌日蝸牛郵差送');
  await prep({ stage: 'elder' }); await W(300); s = await q();
  ok(s.save.phase === 'due' && s.save.dueDay > 0, '團絨到靜光 → due（翌日）', s.save.phase);
  ok(await E(() => !Glimmer.series2.canDeliver(__glimmer.state, __glimmer.now())), '同日唔送');
  await setT(T0 + DAY); await W(200);
  const r0 = await E(() => __qa.b3b.spawn('snail_postman', 'right', true)); ok(r0 && r0.ok, '蝸牛郵差出場（b3b 訪客）', r0);
  s = await until(x => x.save.phase === 'egg', 40000); ok(s.save.phase === 'egg' && s.save.gotAt > 0, '郵差到 → 收到細佬蛋', s.save.phase);
  const b3 = await E(() => __qa.b3b.st()); ok(!(b3.visitor && b3.visitor.letter), '今次唔派信（送蛋代替）', b3.visitor);
  await W(800); s = await q(); ok(s.render.egg > 0, '蛋有畫', s.render); await shot('01-egg', ZOOM);
  ok(await E(() => { const r = Glimmer.series2.deliver(__glimmer.state, __glimmer.now()); return !r.ok; }), '最多 1 隻（再送 → 拒）');
  await E(() => { if (__qa.b3b.leave) __qa.b3b.leave(); }); await closeModals();

  console.log('# 蛋 3 晚：團絨瞓 → 攬蛋＋夢泡泡（當日最多照顧）');
  await E(() => { const SR = Glimmer.series2, s = __glimmer.state, n = __glimmer.now(); for (let i = 0; i < 3; i++) SR.careNote(s, 'water', n); SR.careNote(s, 'feed', n); });
  await setT(T0 + DAY + 9 * H); await E(() => { __glimmer.state.sleeping = true; }); await W(1500);
  s = await q(); ok(s.dream === 'A' && s.render.dream > 0, '夜晚瞓 → 夢泡泡＝淋花（A）', { d: s.dream, r: s.render.dream });
  ok(s.save.dreams.length === 1 && s.save.dreams[0].line === 'A', '第 1 晚夢記低 A', s.save.dreams);
  ok(Math.abs(s.egg.x - (await E(() => __glimmer.beh.x)) - 18) < 4, '蛋滑去團絨隔籬（攬蛋）', s.egg); await shot('02-egg-dream', ZOOM);
  ok(await E(() => __glimmer.s2Dex() !== null), '有蛋 → 圖鑑有「團絨教錯咗乜」');
  for (let n = 2; n <= 3; n++) { await E((n) => { const SR = Glimmer.series2, s = __glimmer.state; __glimmer.state.sleeping = false; __glimmer.clock.t += 15 * 3600e3; SR.careNote(s, n === 3 ? 'feed' : 'water', __glimmer.now()); SR.careNote(s, n === 3 ? 'feed' : 'water', __glimmer.now()); __glimmer.clock.t += 9 * 3600e3; __glimmer.state.sleeping = true; }, n); await W(700); }
  s = await q(); ok(s.save.dreams.length === 3 && s.save.dreams[2].line === 'E', '3 晚夢（A A E）', s.save.dreams.map(d => d.line));

  console.log('# 孵化第一眼（2s；撳跳）');
  await E(() => { __glimmer.clock.t += 15 * 3600e3; __glimmer.state.sleeping = false; }); s = await until(x => x.scene && x.scene.kind === 'hatch', 4000);
  ok(s.scene && s.scene.kind === 'hatch', '孵化場面自動開始（第 3 晚之後醒）', s.scene);
  await until(x => x.scene && x.scene.last && x.scene.last.t >= 520, 2000); await shot('03-hatch-crack'); s = await q(); ok(s.scene && s.scene.last && s.scene.last.egg && s.scene.last.rays, '殼裂＋光芒', s.scene && s.scene.last);
  ok(await E(() => document.body.classList.contains('s2-scene')), 'HUD 收埋（body.s2-scene）');
  await page.mouse.click(195, 400); await W(150); s = await q(); ok(s.scene && s.scene.skip && s.scene.t >= 2000, '撳 → 跳去最後一格', s.scene);
  await shot('04-hatch-glance');
  s = await until(x => x.save.phase === 'kid', 3000); ok(s.save.phase === 'kid' && s.stage === 'S1' && s.form === 'S1', '孵化 → 細佬 S1 蛋殼仔', { p: s.save.phase, st: s.stage });
  s = await until(x => x.scene && x.scene.kind === 'level', 3000); ok(s.scene && s.scene.rel === 'follow', '跟班升級小場面', s.scene);
  await W(700); await shot('05-lv-follow', ZOOM);
  s = await until(x => !x.scene, 6000); ok(!s.scene && s.save.rel === 'follow' && !s.puppet, '場面完 → 放返團絨', { sc: s.scene, pp: s.puppet });

  console.log('# 跟住團絨行');
  await E(() => { __glimmer.beh.x = -40; }); let fw = null;
  for (let i = 0; i < 40 && !fw; i++) { await W(150); const k = await E(() => [__qa.s2.st().kid.x, __glimmer.beh.x]); if (Math.abs(k[0] - k[1]) >= 18 && Math.abs(k[0] - k[1]) <= 50 && Math.abs(k[1] + 40) < 30) fw = k; }
  ok(!!fw, '細佬跟喺團絨後面（有距離）', fw || await E(() => [__qa.s2.st().kid.x, __glimmer.beh.x])); await shot('06-follow', ZOOM);

  console.log('# 教錯課：撳細佬 → 托盤 → 拖道具畀團絨');
  const ev0 = await evoSnap();
  let kc = await E(() => __qa.s2.kidCss()); await page.mouse.click(kc.x, kc.y); await W(300); s = await q();
  ok(s.tray, '撳細佬 → 道具托盤（S1 有堂）', { tray: s.tray, kc }); await shot('07-tray');
  ok(await page.locator('[data-testid^=s2-prop-]').count() === 8, '托盤 8 樣道具');
  const ch = await page.locator('[data-testid=s2-prop-A]').boundingBox(), pc = await E(() => __qa.s2.petCss());
  await page.mouse.move(ch.x + ch.width / 2, ch.y + ch.height / 2); await page.mouse.down(); await page.mouse.move(pc.x, pc.y - 20, { steps: 8 });
  ok(await page.locator('[data-testid=s2-drag-ghost]').count() === 1, '拖緊有影'); await page.mouse.move(pc.x, pc.y, { steps: 3 }); await page.mouse.up(); await W(200);
  s = await q(); ok(s.scene && s.scene.kind === 'lesson' && !s.tray, '放落團絨 → 上堂（托盤收）', s.scene);
  ok(s.scene && s.scene.rxOk, '團絨（靜光）用 3a 反應 clip 示範', s.scene);
  await W(1300); s = await q(); ok(s.gest && s.gest.clip === 's2_demo_A' && s.puppet, '示範：b.gest＝s2_demo_A＋puppet', { g: s.gest, p: s.puppet }); await shot('08-demo-A', ZOOM);
  await W(2200); s = await q(); ok(s.scene && s.scene.copy && s.scene.copy.fx.includes('prop_can') && s.render.copy > 0, '照抄：細佬攞水壺（evalClip＋face）', s.scene && s.scene.copy); await shot('09-copy-A', ZOOM);
  s = await until(x => !x.scene, 4000); ok(s.save.lessons.length === 1 && s.save.lessons[0].line === 'A' && s.save.day.n === 2, '堂 1 記低 A；親密 +2', { l: s.save.lessons, n: s.save.day.n });
  ok(!s.puppet && !s.gest, '上完堂放返團絨');
  let r = await E(() => __qa.s2.lesson('E')); ok(r.ok, '同日第 2 堂 OK', r); await until(x => !x.scene, 7000);
  r = await E(() => __qa.s2.lesson('B')); ok(!r.ok && r.reason === 'today', '每日最多 2 堂', r);
  ok(await evoSnap() === ev0, '上堂唔影響團絨路線分／碎／小遊戲計數');

  console.log('# 喊 → 拖團絨過去哄');
  await E(() => __qa.s2.cry()); await W(500); s = await q(); ok(s.kid.cry && s.kid.clip === 'cry', '細佬喊（cry strip）', s.kid); await shot('10-cry', ZOOM);
  const n0 = s.save.day.n, pc2 = await E(() => __qa.s2.petCss()), kc2 = await E(() => __qa.s2.kidCss());
  await page.mouse.move(pc2.x, pc2.y); await page.mouse.down(); await W(100); s = await q(); ok(s.drag && s.puppet, '撳住團絨 → 拖', { d: s.drag });
  await page.mouse.move(kc2.x + (kc2.x > pc2.x ? -30 : 30), kc2.y, { steps: 10 }); await W(1500); await page.mouse.up(); await W(200);
  s = await q(); ok(s.scene && s.scene.kind === 'comfort', '放喺細佬隔籬 → 哄喊 clip', { sc: s.scene, kid: s.kid, log: s.log.slice(-3) });
  await W(1000); await shot('11-comfort', ZOOM);
  s = await until(x => !x.scene, 5000); ok(!s.kid.cry && s.save.day.n === n0 + 2 && s.save.day.comforts === 1, '哄完：唔喊；親密 +2', { n: s.save.day.n, n0 });

  console.log('# 一齊食／上限');
  await E(() => __glimmer.sysFed('berry')); await W(300); s = await q(); ok(s.kid.mode === 'eat' && s.kid.clip === 'eat' && s.save.day.eat === 1, '團絨食 → 細佬一齊食（+1）', s.kid); await shot('12-eat', ZOOM);
  await W(1500); await E(() => { const o = Glimmer.series2.st(__glimmer.state); o.day.n = 9; }); await E(() => __qa.s2.cry()); await E(() => __qa.s2.comfort()); await until(x => !x.scene, 5000);
  s = await q(); ok(s.save.day.n === 10, '親密每日上限 10', s.save.day.n);

  console.log('# 一齊瞓（朋友有被）');
  await E(() => { const o = Glimmer.series2.st(__glimmer.state); o.rel = 'friend'; o.intim = 40; o.relQ.length = 0; o.sleepNight = null; __glimmer.clock.t = new Date(__glimmer.now()).setHours(22, 0, 0, 0); __glimmer.state.sleeping = true; });
  s = await until(x => x.kid.clip === 'sleep', 6000); ok(s.kid.clip === 'sleep', '團絨瞓 → 細佬行埋去瞓', s.kid);
  await W(500); s = await q(); ok(s.render.blanket > 0 && s.save.sleepNight != null, '朋友 → 有被；一齊瞓記低', { b: s.render.blanket, sn: s.save.sleepNight }); await shot('13-sleep-together', ZOOM);
  await E(() => { __glimmer.state.sleeping = false; __glimmer.clock.t += 10 * 3600e3; }); await W(400);

  console.log('# 朋友升級場面＋雙人彈彈葉');
  await E(() => { const o = Glimmer.series2.st(__glimmer.state); o.rel = 'follow'; o.intim = 29; }); await E(() => __qa.s2.cry()); await E(() => __qa.s2.comfort()); await until(x => !x.scene || x.scene.kind === 'level', 6000);
  s = await until(x => x.scene && x.scene.kind === 'level', 4000); ok(s.scene && s.scene.rel === 'friend' && s.save.rel === 'friend', '親密 ≥30 → 朋友場面', { sc: s.scene, rel: s.save.rel });
  await W(1100); await shot('14-lv-friend', ZOOM); await until(x => !x.scene, 6000); await closeModals();
  const ev1 = await evoSnap();
  await E(() => __qa.s2.card()); await W(300); ok(await page.locator('[data-testid=s2-card]').count() === 1, '細佬卡'); ok(await page.locator('#mbox .btn', { hasText: '二人彈彈葉' }).count() === 1, '朋友 → 有雙人彈彈葉');
  await shot('15-card'); await page.locator('#mbox .btn', { hasText: '二人彈彈葉' }).click(); await W(400);
  ok(await E(() => !!__glimmer.mg2Busy), '雙人彈彈葉開始'); await E(() => __qa.mg2.skipReady()); await E(() => __qa.mg2.step(0.6)); await shot('16-duo-play');
  await E(() => { const g = __qa.mg2.game(); g.score = 12; g.t = g.dur - 0.02; }); await E(() => __qa.mg2.step(0.2)); await W(300); await shot('17-duo-result');
  const lm = await E(() => __qa.mg2.last()); ok(lm && lm.duo && !lm.rewarded && lm.shards === 0, '雙人：唔出碎', lm);
  await E(() => __qa.mg2.close()); await W(200); s = await q(); ok(s.save.day.duo === 1, '雙人計今日 1 次', s.save.day);
  ok(await evoSnap() === ev1, '雙人唔食小遊戲額、唔加碎、唔加路線分');

  console.log('# 長大：S2 → S3 揭曉 → S4 → S5 → S6 家人');
  await closeModals(); const st0 = await E(() => Glimmer.series2.st(__glimmer.state).hatchDay);
  const grow = async (days) => { await E((d) => { const o = Glimmer.series2.st(__glimmer.state); o.hatchDay -= d; }, days); await W(500); return q(); };
  s = await grow(1); ok(s.stage === 'S2' && s.form === 'S2', 'S2 BB', s.stage);
  s = await grow(2); await W(300); s = await q(); ok(s.stage === 'S3' && s.save.line && s.save.settle, 'S3 → 揭曉系', { st: s.stage, l: s.save.line, se: s.save.settle });
  ok(s.form === s.save.line + '1', 'S3 形態＝' + (s.save.line || '?') + '1', s.form); await W(800); await shot('18-S3', ZOOM);
  s = await grow(3); ok(s.stage === 'S4' && s.form === 'S4' + s.save.line, 'S4 形態', s.form); await W(800); await shot('19-S4', ZOOM);
  s = await grow(3); ok(s.stage === 'S5' && s.form === s.save.line + '2', 'S5 形態', s.form);
  s = await grow(3); ok(s.stage === 'S6' && s.form === s.save.line + '3', 'S6 成年形態', s.form); await W(800); s = await q(); ok(s.render.kid > 0, 'S6 有畫（strip lazy 載）', s.errors);
  await E(() => { const o = Glimmer.series2.st(__glimmer.state); o.intim = 79; }); await E(() => __qa.s2.cry()); await E(() => __qa.s2.comfort());
  s = await until(x => x.scene && x.scene.kind === 'level', 8000); ok(s.scene && s.scene.rel === 'family', '親密 ≥80＋成年 → 家人場面', s.scene); await W(1100); await shot('20-lv-family', ZOOM);
  await until(x => !x.scene, 6000); await closeModals(); await E(() => __qa.s2.card()); await W(300);
  ok(await page.locator('[data-testid=s2-house]').count() === 1 && (await page.locator('[data-testid=s2-house]').innerText()).includes('入屋仔') && (await page.locator('[data-testid=s2-house]').getAttribute('data-open')) === '1', '家人 → 屋仔入口（4b）'); await shot('21-card-family'); await closeModals();

  console.log('# 圖鑑');
  await E(() => Glimmer.ui.openDex()); await W(400);
  ok(await page.locator('[data-testid=dex-s2]').count() === 1, '圖鑑「團絨教錯咗乜」');
  ok(await page.locator('[data-testid^=dex-s2-dream-]').count() === 3 && await page.locator('[data-testid^=dex-s2-lesson-]').count() === 2, '3 個夢＋2 堂');
  ok(await page.locator('[data-testid=dex-s2-settle]').count() === 1, '結算方法有寫');
  ok(await page.locator('[data-testid^=dex-s2-lock-lesson-]').count() === 4, '未上嘅 4 堂＝未遇見');
  await page.locator('[data-testid=dex-s2]').scrollIntoViewIfNeeded(); await shot('22-dex'); await closeModals();

  console.log('# 存檔／重開');
  await E(() => __glimmer.save()); const sv = await E(() => JSON.parse(localStorage.getItem(Glimmer.data.PARAMS.saveKey)).pet2);
  ok(sv && sv.phase === 'kid' && sv.rel === 'family', '存檔有 pet2', sv && sv.phase);
  await page.reload(); await page.waitForFunction(() => window.__glimmer && __glimmer.s2Load); await E(() => __glimmer.s2Load); await W(600);
  s = await q(); ok(s.save.phase === 'kid' && s.save.rel === 'family' && s.save.lessons.length === 2, '重開仲喺度', { p: s.save.phase });
  ok(await E(() => __glimmer.state.stage === 'elder'), '團絨唔變');

  console.log('# ?s2=0 全停');
  await page.goto(BASE + '?q=high&hour=13&ev=0&s2=0'); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await W(600);
  ok(await E(() => !__glimmer.s2Tick && !(window.__qa && window.__qa.s2)), '?s2=0 → 冇 s2Tick／__qa.s2');

  console.log('# 4a.1 設定「試玩：新寵物系列」');
  await load('q=high&hour=13&seed=21&ev=0', { stage: 'adult' }); await E(() => Glimmer.sys12b.badgeCheck(__glimmer.state, __glimmer.now()));   // prep 改 stage 觸發嘅成就先結算（唔關試玩按鈕事）
  const ev2 = await evoSnap(), stg = await E(() => [__glimmer.state.stage, __glimmer.state.form]);
  const openSet = async () => { await closeModals(); await page.locator('#gear').click({ force: true }).catch(() => E(() => document.getElementById('gear').click())); await W(400); };
  const openDev = async () => { await closeModals(); await page.locator('[data-testid=dev-btn]').click(); await W(400); };
  console.log('# 4a.3：試玩掣搬去「🛠 開發者模式」（設定冇試玩區）');
  ok(await page.locator('[data-testid=dev-btn]').isVisible(), '主畫面有「🛠 開發者」掣');
  ok(await E(() => { const b = document.querySelector('[data-testid=dev-btn]').getBoundingClientRect(), hit = (el) => { if (!el) return false; const r = el.getBoundingClientRect(); return r.width && !(b.right <= r.left || b.left >= r.right || b.bottom <= r.top || b.top >= r.bottom); };
    return ![...document.querySelectorAll('#hdRail .ibtn, #hdDock, .abtn, .need, #chip')].some(hit); }), '「🛠 開發者」掣唔遮 HUD／rail／dock');
  await shot('30-main-devbtn');
  await openSet(); ok(await page.locator('[data-testid=s2-test]').count() === 0 && await page.locator('#mbox [data-testid^=dev-s2-]').count() === 0 && !(await page.locator('#mbox').innerText()).includes('試玩'), '設定冇試玩區');
  ok((await page.locator('[data-testid=s2-version]').innerText()).includes('版本 5a'), '設定只留「版本 5a」');
  await shot('31-settings-no-test');
  await openDev(); ok(await E(() => document.getElementById('mbox').dataset.kind === 'devmode'), '撳「🛠 開發者」→ 開發者模式彈窗');
  ok((await page.locator('[data-testid=dev-version]').innerText()).includes('版本 5a'), '開發者模式頂顯示版本');
  ok((await page.locator('[data-testid=dev-sec-s2]').innerText()).includes('新寵物系列 4a'), '分組：新寵物系列 4a');
  for (const k of ['deliver', 'hatch', 'level', 'cry', 'evolve', 'duo', 'card']) ok(await page.locator('[data-testid=dev-s2-' + k + ']').isVisible(), '按鈕 ' + k + ' 睇得到');
  ok(await E(() => __qa.devmode.sections().some(x => x.id === 'uiv2')), '4b.1：有「UI v2」組');
  ok(JSON.stringify(await E(() => __qa.devmode.sections().filter(x => x.id !== 'uiv2' && x.id !== 'l5'))) === JSON.stringify([{ id: 's2', title: '新寵物系列 4a（細佬）', items: ['deliver', 'hatch', 'level', 'cry', 'evolve', 'duo', 'card'] }, { id: 'house', title: '家 4b（屋仔）', items: ['prep', 'entry', 'locked', 'open', 'deco', 'shards', 'rewards', 'setA', 'setB', 'sit', 'prank', 'sleep', 'night', 'touch', 'auto', 'close'] }]), 'register 結構（4a＋4b 兩組）');
  await shot('32-dev-panel'); await shot('23-settings-test');
  await page.locator('[data-testid=dev-s2-deliver]').click(); await W(400); s = await q();
  ok(s.save.phase === 'egg' && !(await E(() => Glimmer.ui.isModalOpen())), '「即刻送蛋」（團絨未靜光都送）→ 蛋；彈窗收埋', s.save.phase);
  await openDev(); await page.locator('[data-testid=dev-s2-deliver]').click(); await W(300); s = await q(); ok(s.save.phase === 'egg', '再送 → 最多 1 隻');
  await openDev(); await page.locator('[data-testid=dev-s2-hatch]').click(); s = await until(x => x.scene && x.scene.kind === 'hatch', 3000); ok(s.scene && s.scene.kind === 'hatch', '「即刻孵化」→ 孵化場面', s.scene);
  s = await until(x => x.save.phase === 'kid', 5000); ok(s.save.phase === 'kid' && s.save.dreams.length === 3, '孵化完 → 細佬（夢補夠 3 格）', s.save.dreams.length);
  await until(x => !x.scene && !x.save.relQ.length, 8000); await W(300);
  await openDev(); await page.locator('[data-testid=dev-s2-level]').click(); s = await until(x => x.scene && x.scene.kind === 'level', 3000); ok(s.save.rel === 'friend' && s.scene && s.scene.rel === 'friend', '「升一級關係」跟班 → 朋友（場面）', { rel: s.save.rel, sc: s.scene });
  await until(x => !x.scene, 8000); await openDev(); await page.locator('[data-testid=dev-s2-level]').click(); s = await until(x => x.scene && x.scene.kind === 'level', 3000); ok(s.save.rel === 'family', '再撳 → 家人', s.save.rel);
  await until(x => !x.scene, 8000); await closeModals(); await E(() => __qa.s2.card()); await W(300); ok((await page.locator('[data-testid=s2-house]').innerText()).includes('入屋仔'), '家人卡：屋仔入口（4b）'); await closeModals();
  await openDev(); await page.locator('[data-testid=dev-s2-cry]').click(); await W(500); s = await q(); ok(s.kid.cry && s.kid.clip === 'cry', '「觸發喊」→ 細佬喊', s.kid);
  { const d = await E(() => Math.abs(__qa.s2.st().kid.x - __glimmer.beh.x)); ok(d >= 20, '喊嗰陣細佬企喺團絨隔籬（睇得到）', d); }
  await W(600); await shot('24-kid-on-screen'); await shot('24-kid-zoom', ZOOM);
  ok(await evoSnap() === ev2 && JSON.stringify(await E(() => [__glimmer.state.stage, __glimmer.state.form])) === JSON.stringify(stg), '試玩按鈕唔改團絨成長／碎／路線', [ev2, await evoSnap()]);

  console.log('# 4a.2 設定：細佬進化／開二人彈／開細佬卡（自動準備）＋右側「細佬」掣');
  await load('q=high&hour=13&seed=21&ev=0', { stage: 'adult' }); await E(() => Glimmer.sys12b.badgeCheck(__glimmer.state, __glimmer.now())); const ev3 = await evoSnap();
  ok(!(await page.locator('[data-testid=s2-rail-kid]').isVisible().catch(() => false)), '未有細佬 → 冇「細佬」掣');
  await openDev(); await shot('25-settings-4a2'); await page.locator('[data-testid=dev-s2-card]').click(); await W(500); s = await q();
  ok(s.save.phase === 'kid' && await E(() => document.getElementById('mbox').dataset.kind === 's2Card'), '「開細佬卡」（未有蛋）→ 自動孵化＋開卡', s.save.phase);
  ok(await page.locator('[data-testid=s2-duo-hint]').count() === 1 && (await page.locator('[data-testid=s2-duo-hint]').innerText()).includes('做咗朋友先開'), '跟班卡：寫明二人彈點開');
  await shot('26-kid-card'); await closeModals(); await W(300);
  ok(await page.locator('[data-testid=s2-rail-kid]').isVisible(), '孵化後右側「細佬」掣睇得到');
  await page.locator('[data-testid=s2-rail-kid]').click(); await W(400); ok(await E(() => document.getElementById('mbox').dataset.kind === 's2Card'), '撳「細佬」掣 → 細佬卡'); await closeModals();
  for (const [from, to] of [['S1', 'S2'], ['S2', 'S3'], ['S3', 'S4']]) { await openDev(); await page.locator('[data-testid=dev-s2-evolve]').click(); s = await until(x => x.stage === to, 3000); ok(s.stage === to && !!s.form, '「細佬進化」' + from + ' → ' + to, [s.stage, s.form]); }
  s = await q(); ok(!!s.save.line, 'S3 揭曉系別', s.save.line);
  await W(400); await shot('27-kid-evolved'); await shot('27-kid-evolved-zoom', ZOOM);
  await openDev(); await page.locator('[data-testid=dev-s2-duo]').click(); await W(700); ok(await E(() => !!__glimmer.mg2Busy), '「開二人彈」→ 即刻開雙人彈彈葉');
  s = await q(); ok(s.save.rel === 'friend', '自動做朋友', s.save.rel); await E(() => __qa.mg2.skipReady()); await E(() => __qa.mg2.step(0.6)); await shot('28-duo-bounce');
  await E(() => { const g = __qa.mg2.game(); g.score = 8; g.t = g.dur - 0.02; }); await E(() => __qa.mg2.step(0.2)); await W(300); await E(() => __qa.mg2.close()); await until(x => !x.scene, 8000); await W(300); await closeModals();
  await page.locator('[data-testid=s2-rail-kid]').click(); await W(400); ok(await page.locator('#mbox .btn', { hasText: '二人彈彈葉' }).count() === 1, '朋友卡有「二人彈彈葉」掣'); await shot('29-kid-card-friend'); await closeModals();
  ok(await evoSnap() === ev3, '4a.2 試玩掣唔改團絨成長／碎／路線', [ev3, await evoSnap()]);

  console.log('# 4a.3 開發者掣收埋／出返');
  await openDev(); await page.locator('[data-testid=dev-toggle-btn]').click(); await W(200); await closeModals(); ok(!(await page.locator('[data-testid=dev-btn]').isVisible()), '彈窗入面「收埋」→ 主畫面冇咗掣');
  await openSet(); for (let i = 0; i < 5; i++) await page.locator('[data-testid=s2-version]').click(); await closeModals(); ok(await page.locator('[data-testid=dev-btn]').isVisible(), '設定撳「版本」5 下 → 掣出返');

  console.log('# ?s2x=1 → AUTO 開');
  await load('q=high&hour=13&seed=21&ev=0&s2x=1', { stage: 'adult' }); s = await q(); ok(s.auto.deliver && s.auto.cry, '?s2x=1 開 AUTO', s.auto);

  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log('\n4a e2e：' + pass + ' pass, ' + fail + ' fail');
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
