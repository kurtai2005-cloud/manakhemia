/* 《微光小圃》 e2e-4b — 第 4 批 4b 屋仔（docs-gdd/series2-4a4b-spec.md v1.1 §4b）：家人先開（入口上鎖／解鎖＋紅點）、細佬卡真入口、
   屋仔畫面（日／夜分層＋光）、預設葉仔床、佈置（6 格分頁、卡狀態、碎唔夠、買、擺、收起、第一次擺心情 +1 共用上限）、委託／訪客獎、
   坐埋一齊（心心）、整蠱（「哇！」、每日 3 次）、21:00–03:00 同床瞓（zzz）、撳團絨＝3a 反應、撳細佬跳、🛠 開發者「家 4b」、存檔、?house=0、
   團絨進化路線分／碎／小遊戲唔受影響。截圖 → SHOTS（4b-*.png）。node tests/e2e-4b.js（BASE 預設 http://localhost:8240/index.html） */
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
  const shot = (n) => page.screenshot({ path: SHOTS + '4b-' + n + '.png' });
  const h = () => E(() => __qa.house.st());
  const until = async (fn, ms) => { const t0 = Date.now(); let s; while (Date.now() - t0 < (ms || 8000)) { s = await h(); if (fn(s)) return s; await W(100); } return h(); };
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const prep = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const load = async (qs, clear) => {
    if (clear !== false) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad); await setT(T0); if (clear !== false) await prep(); await W(400);
  };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); } };
  const toast = () => E(() => (window.__toasts && window.__toasts.length ? window.__toasts[window.__toasts.length - 1] : (document.getElementById('toast') || {}).textContent || ''));
  const near = (a, b) => Math.abs(a - b) < 0.2;
  const openDev = async () => { await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(400); };
  const dev = async (k) => { await openDev(); await page.locator('[data-testid=dev-house-' + k + ']').click(); await W(500); };
  const toKid = async () => { await E(() => { const G = __glimmer, SR = Glimmer.series2, s = G.state, now = G.now(); s.stage = 'elder'; SR.noteElder(s, now - 6 * 86400e3); const o = SR.st(s); o.dueDay = SR.dayNum(now) - 6; SR.deliver(s, now - 5 * 86400e3);
    o.dreams = [{ day: 1, line: 'A', at: 0, live: true }, { day: 2, line: 'A', at: 0, live: true }, { day: 3, line: 'E', at: 0, live: true }]; SR.hatch(s, now - 1 * 86400e3); o.relQ.length = 0; G.save(); }); await W(400); };
  const evoSnap = () => E(() => JSON.stringify({ evo: Object.assign({}, __glimmer.state.evo, { cl: null, login: null }),   // evo.login＝跨日登入（唔關屋仔事）
    g: Glimmer.sys12b.st(__glimmer.state).games.total, route: __glimmer.state.route || null }));
  const mood = () => E(() => __glimmer.state.needs.mood);

  console.log('# 載入');
  await load('q=high&hour=13&seed=21&ev=0');
  let s = await h(); ok(s.ready && !s.errors.length, '4b 屋仔圖全部載入', s.errors);
  ok(await E(() => Glimmer.data.PARAMS.house && Glimmer.data.PARAMS.house.enabled === true), 'PARAMS.house 開');
  ok(await E(() => /^4b/.test(Glimmer.data.PARAMS.series2.version)), '版本 4b（4b.1 UI v2）');
  ok(!s.open && (!s.rail || !s.rail.shown), '未有細佬 → 冇屋仔掣', s.rail);

  console.log('# 入口：上鎖（細佬未係家人）');
  await toKid(); const evo0 = await evoSnap(); await E(() => { window.__toasts = []; const U = Glimmer.ui, t = U.toast; U.toast = function (m) { window.__toasts.push(String(m)); return t.apply(this, arguments); }; }); await E(() => __qa.house.rail()); await W(300); s = await h();
  ok(s.rail && s.rail.shown && s.rail.locked === '1' && !s.rail.dot, '有細佬未家人 → 屋仔掣上鎖', s.rail);
  { const b = await page.locator('[data-testid=s2-rail-house]').boundingBox(); const X = await E(() => (window.__qa && __qa.uiv2 && __qa.uiv2.st().on) ? __qa.uiv2.st().rail.house : { x: 360, y: 336 }); ok(b && Math.abs(b.x + b.width / 2 - X.x) < 3 && Math.abs(b.y + b.height / 2 - X.y) < 3, '入口喺 rail（v1 360／336；v2 跟 layout rail）', b, X); }
  await page.locator('[data-testid=s2-rail-house]').click(); await W(300);
  ok((await toast()).includes('同細佬做咗家人就可以一齊住'), '撳上鎖掣 → 「同細佬做咗家人就可以一齊住」'); s = await h(); ok(!s.open, '上鎖入唔到');
  await shot('01-entry-locked');
  await E(() => __qa.s2.card()); await W(300);
  ok((await page.locator('[data-testid=s2-house]').getAttribute('data-open')) === '0' && (await page.locator('[data-testid=s2-house]').innerText()).includes('做咗家人先開'), '細佬卡：屋仔上鎖'); await closeModals();
  ok(await E(() => Glimmer.house.cardState(__glimmer.state, 'bed_cloud')) && !(await E(() => Glimmer.house.unlocked(__glimmer.state))), 'unlocked() = false');

  console.log('# 🛠 開發者「家 4b」');
  await openDev();
  ok((await page.locator('[data-testid=dev-version]').innerText()).includes('版本 4b'), '開發者模式顯示「版本 4b」');
  ok((await page.locator('[data-testid=dev-sec-house]').innerText()).includes('家 4b'), '分組「家 4b（屋仔）」');
  const KEYS = ['prep', 'entry', 'locked', 'open', 'deco', 'shards', 'rewards', 'setA', 'setB', 'sit', 'prank', 'sleep', 'night', 'touch', 'auto', 'close'];
  { let n = 0; for (const k of KEYS) if (await page.locator('[data-testid=dev-house-' + k + ']').count()) n++; ok(n === KEYS.length, '16 個掣齊', n); }
  ok((await page.locator('[data-testid=dev-status-house]').innerText()).includes('未開'), 'status：未開');
  await page.locator('[data-testid=dev-sec-house]').scrollIntoViewIfNeeded(); await shot('02-dev-section'); await closeModals();
  await dev('prep'); let s2 = await E(() => __qa.s2.st()); ok(s2.save.rel === 'family' && s2.stage === 'S6', '「準備」→ 細佬成年＋家人（自動）', { rel: s2.save.rel, st: s2.stage });
  await W(800); s = await h(); ok(s.rail.locked === '0' && s.rail.dot, '解鎖 → 屋仔掣開＋紅點', s.rail);
  ok(s.save.owned.length === 1 && s.save.slots.bed === 'bed_leaf', '預設送葉仔床（擺好）', s.save);
  await dev('entry'); await W(300); await shot('03-entry-open');
  await E(() => __qa.s2.card()); await W(300);
  ok((await page.locator('[data-testid=s2-house]').getAttribute('data-open')) === '1' && (await page.locator('[data-testid=s2-house]').innerText()).includes('入屋仔') && await page.locator('#mbox .btn', { hasText: '入屋仔' }).count() === 1, '細佬卡：屋仔真入口＋「🏠 入屋仔」掣（取代「即將開放」）');
  await shot('04-card-house');

  console.log('# 入屋仔');
  const m0 = await mood();
  await page.locator('#mbox .btn', { hasText: '入屋仔' }).click(); await W(1500); s = await h();
  ok(s.open && !(await E(() => Glimmer.ui.isModalOpen())), '撳卡「入屋仔」→ 屋仔（卡收埋）', s.log.slice(-3));
  ok(await page.locator('[data-testid=house-view]').isVisible() && (await page.locator('[data-testid=house-title]').innerText()) === '屋仔', '屋仔畫面＋標題');
  ok(s.stats.frames > 10 && s.stats.layers > 20 && s.stats.furn > 0 && s.stats.pets > 0, '畫緊（分層＋家具＋寵物）', s.stats);
  ok(s.pets.tr.last && s.pets.kid.last && s.pets.tr.last.w > 0 && s.pets.kid.last.w === 48, '兩隻都有畫（團絨 atlas＋細佬 48px）', s.pets);
  ok(s.stats.variant === 'day' && !s.night, '13:00 → 日間', s.stats.variant);
  ok(!s.rail.dot && s.save.seen, '入過 → 紅點消');
  ok(near(await mood(), m0 + 1), '第一次入屋（擺好床）心情 +1', { m0, m: await mood() });
  { const px = await E(() => { const c = document.querySelector('[data-testid=house-canvas]'), x = c.getContext('2d'), d = x.getImageData(0, 0, c.width, c.height).data; let n = 0, sum = 0; for (let i = 0; i < d.length; i += 4 * 97) { n++; sum += d[i] + d[i + 1] + d[i + 2]; } return sum / n; }); ok(px > 150, 'canvas 有內容（日間光）', px); }
  await shot('05-house-day');
  const ex = await E(() => __glimmer.state.pet2 && Object.keys(__glimmer.state.pet2));
  ok(ex && ex.includes('house'), '存喺 s.pet2.house', ex);

  console.log('# 佈置');
  await page.locator('[data-testid=house-decorate]').click(); await W(700); s = await h();
  ok(s.deco && s.offY < 0, '撳「佈置」→ 佈置模式（房上移）', s.offY);
  for (const k of ['bed', 'table', 'wall', 'rug', 'window', 'lamp']) ok(await page.locator('[data-testid=house-tab-' + k + ']').isVisible() && await page.locator('[data-testid=house-pin-' + k + ']').count() === 1, '分頁＋圖釘 ' + k);
  ok((await page.locator('[data-testid=house-tab-bed]').getAttribute('data-sel')) === '1' && (await page.locator('[data-testid=house-tabtitle]').innerText()).includes('床'), '預設揀「床」');
  ok((await page.locator('[data-testid=house-card-bed_leaf]').getAttribute('data-state')) === 'equipped' && (await page.locator('[data-testid=house-card-bed_cloud]').getAttribute('data-state')) === 'buy', '卡狀態：擺緊／可買');
  const w0 = await E(() => Glimmer.sys12.st(__glimmer.state).wallet.total);
  ok((await page.locator('[data-testid=house-chip]').innerText()).includes(String(w0)), '碎 chip = 錢包', w0);
  await shot('06-decorate');
  await E(() => { window.__toasts.length = 0; }); await page.locator('[data-testid=house-card-bed_cloud]').click(); await W(300);
  ok((await E(() => window.__toasts.join('|'))).includes('碎唔夠') && !(await E(() => Glimmer.ui.isModalOpen())), '碎唔夠 → 提示（唔彈買）', await toast());
  await page.locator('[data-testid=house-tab-wall]').click(); await W(300);
  ok((await page.locator('[data-testid=house-card-wall_frame]').getAttribute('data-state')) === 'locked', '團絨相框：上鎖（委託獎）');
  await page.locator('[data-testid=house-card-wall_frame]').click(); await W(300); ok((await toast()).includes('委託'), '撳上鎖 → 講點攞（仲差幾張委託）', await toast());
  await page.locator('[data-testid=house-tab-lamp]').click(); await W(300);
  ok((await page.locator('[data-testid=house-card-lamp_mushroom]').getAttribute('data-state')) === 'locked', '蘑菇燈：上鎖（訪客獎）');
  await shot('07-deco-locked');
  await closeModals(); await dev('shards'); s = await h(); ok(s.wallet === w0 + 200, '「加 200 碎」', s.wallet);
  ok(s.open && s.deco, '開發者掣唔會趕走屋仔／佈置');
  await page.locator('[data-testid=house-tab-bed]').click(); await W(300);
  await page.locator('[data-testid=house-card-bed_cloud]').click(); await W(400);
  ok(await page.locator('[data-testid=house-buy]').isVisible() && (await page.locator('[data-testid=house-buy]').innerText()).includes('40'), '買家具確認（40 碎）');
  await shot('08-buy');
  await page.locator('#mbox [data-testid=modal-btn-0]').click(); await W(900); s = await h();
  ok(s.wallet === w0 + 160 && s.save.owned.includes('bed_cloud') && s.save.slots.bed === 'bed_cloud', '買咗 → 扣 40 碎＋自動擺', { w: s.wallet, slots: s.save.slots });
  ok((await page.locator('[data-testid=house-card-bed_cloud]').getAttribute('data-state')) === 'equipped' && (await page.locator('[data-testid=house-card-bed_leaf]').getAttribute('data-state')) === 'owned', '卡狀態更新', null);
  await page.locator('[data-testid=house-card-bed_leaf]').click(); await W(400); s = await h(); ok(s.save.slots.bed === 'bed_leaf' && s.wallet === w0 + 160, '換返葉仔床（唔洗碎）', s.save.slots.bed);
  await page.locator('[data-testid=house-tab-table]').click(); await W(200);
  const m1 = await mood(); await page.locator('[data-testid=house-card-table_stump]').click(); await W(300); await page.locator('#mbox [data-testid=modal-btn-0]').click(); await W(900); s = await h();
  ok(s.save.slots.table === 'table_stump' && near(await mood(), m1 + 1), '第一次擺樹樁檯 → 心情 +1', { slot: s.save.slots.table, m1, m: await mood() });
  await page.locator('[data-testid=house-card-clear]').click(); await W(300); s = await h(); ok(s.save.slots.table === null, '收起 → 空格');
  await page.locator('[data-testid=house-card-table_stump]').click(); await W(300); ok(near(await mood(), m1 + 1), '再擺同一件唔再加心情');
  { // 共用每日上限（同 3a 觸摸 fpet_daily_v1）
    const r = await E(() => { const d = new Date(__glimmer.now()), today = d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); const o = JSON.parse(localStorage.getItem('fpet_daily_v1') || '{}'); return { o, today }; });
    ok(r.o[r.today] >= 2, '心情記入共用每日上限 fpet_daily_v1（同 3a 觸摸）', r);
    await E(() => { const k = 'fpet_daily_v1'; const o = JSON.parse(localStorage.getItem(k) || '{}'); for (const f in o) if (typeof o[f] === 'number' && f !== 'd') o[f] = 5; localStorage.setItem(k, JSON.stringify(o)); });
    await E(() => __qa.house.give(['rug_leaf'])); await page.locator('[data-testid=house-tab-rug]').click(); await W(200);
    const m2 = await mood(); await page.locator('[data-testid=house-card-rug_leaf]').click(); await W(400);
    ok(near(await mood(), m2), '共用上限滿咗 → 第一次擺唔再加心情', { m2, m: await mood() });
  }
  await page.locator('[data-testid=house-done]').click(); await W(700); s = await h(); ok(!s.deco && Math.abs(s.offY) < 1, '撳「完成」→ 返屋仔', s.offY);

  console.log('# 委託／訪客獎');
  await E(() => { const s = __glimmer.state; s.sys12 = s.sys12 || {}; s.sys12.quests = s.sys12.quests || {}; s.sys12.quests.paidN = (Glimmer.house.st(s).q0 | 0) + 3; }); await E(() => __qa.house.rail()); await W(300); s = await h();
  ok(s.save.owned.includes('wall_frame') && !s.save.owned.includes('win_star'), '家人後完成 3 張委託 → 團絨相框', s.save.owned);
  await E(() => { const s = __glimmer.state; s.sys12.quests.paidN = (Glimmer.house.st(s).q0 | 0) + 9; }); await E(() => __qa.house.rail()); await W(200); s = await h(); ok(s.save.owned.includes('win_star'), '9 張 → 星星窗');
  await E(() => { const s = __glimmer.state; s.b3b = s.b3b || {}; s.b3b.vis = s.b3b.vis || {}; s.b3b.vis.mushroom_granny = Object.assign(s.b3b.vis.mushroom_granny || {}, { max: true }); }); await E(() => __qa.house.rail()); await W(200); s = await h();
  ok(s.save.owned.includes('lamp_mushroom') && !s.save.owned.includes('lamp_firefly'), '蘑菇婆婆友誼滿 → 蘑菇燈', s.save.owned);
  ok(await E(() => { const v = __glimmer.state.b3b.vis.mushroom_granny; return !!v; }), '訪客原有資料保留');
  await dev('rewards'); s = await h(); ok(['wall_frame', 'win_star', 'lamp_mushroom', 'lamp_firefly'].every(i => s.save.owned.includes(i)), '開發者「攞獎」→ 4 件齊');

  console.log('# 組合／坐埋一齊');
  await dev('setA'); await W(600); s = await h(); ok(s.save.slots.lamp && s.save.slots.rug && s.save.slots.wall && s.save.slots.window, '森林組（A）擺好', s.save.slots); await shot('09-set-A');
  await dev('setB'); await W(600); s = await h(); ok(s.save.slots.bed === 'bed_cloud', '夢幻組（B）擺好', s.save.slots); await shot('10-set-B');
  await dev('sit'); s = await until(x => x.stats.hearts > 0, 6000); ok(s.mode === 'sit' && s.stats.hearts > 0, '坐埋一齊 → 心心', { m: s.mode, h: s.stats.hearts });
  { const d = Math.abs(s.pets.tr.x - s.pets.kid.x); ok(d > 20 && d < 50 && s.pets.tr.dir === 1 && s.pets.kid.dir === -1, '並排坐（面對面）', { d, a: s.pets.tr.dir, b: s.pets.kid.dir }); }
  await shot('11-sit');
  s = await until(x => x.mode === 'free', 9000); ok(s.mode === 'free', '6 秒後返自由行');

  console.log('# 整蠱');
  const pl0 = s.save.prankLeft; await dev('prank'); s = await until(x => x.stats.wah > 0, 8000);
  ok(s.stats.wah > 0, '整蠱 →「哇！」', s.stats); await W(150); await shot('12-prank');
  s = await until(x => x.mode === 'free', 8000); ok(s.mode === 'free' && s.save.prankLeft === pl0, '開發者整蠱唔計次數', s.save.prankLeft);
  { let n = 0; for (let i = 0; i < 3 && (await h()).save.prankLeft > 0; i++) { const r = await E(() => __qa.house.prank(false)); if (r === true) n++; await until(x => x.mode === 'free', 30000); }   // 自由行時亦可能自己整蠱（都計數）
    ok(n >= 1, '自然整蠱計次數', n); }
  s = await h(); ok(s.save.prankLeft === 0 && (await E(() => __qa.house.prank(false))) === false, '每日上限 3 次', s.save.prankLeft);
  await setT(T0 + DAY); await W(200); s = await h(); ok(s.save.prankLeft === 3, '第二日重置', s.save.prankLeft); await setT(T0);

  console.log('# 摸／撳');
  await E(() => __qa.house.freeze()); await W(300);
  { const p = await E(() => __qa.house.petCss('tr')); await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.mouse.up(); await W(150); s = await h();
    ok(s.log.some(l => l.k === 'trTouch'), '撳團絨 → 3a 觸摸', p); ok(s.gest && s.gest.key, '3a 反應動畫（G.beh.gest）', s.gest); await shot('13-touch'); }
  await W(1500);
  { const p = await E(() => __qa.house.petCss('kid')); await page.mouse.click(p.x, p.y); await W(100); s = await h(); ok(s.log.some(l => l.k === 'kidTap') && s.pets.kid && true, '撳細佬 → 跳＋心心'); }
  await dev('touch'); s = await h(); ok(s.gest && s.gest.key, '開發者「摸團絨」→ 反應', s.gest);

  console.log('# 夜晚／同床瞓');
  await dev('auto'); await setT(new Date(2026, 10, 2, 22, 0).getTime()); s = await until(x => x.mode === 'sleep', 6000);
  ok(s.night && s.sleepWanted && s.mode === 'sleep' && s.bed, '22:00 → 夜晚、兩隻同床瞓', { n: s.night, m: s.mode, b: s.bed });
  ok(s.pets.tr.mode === 'sleep' && s.pets.kid.mode === 'sleep', '兩隻都瞓緊');
  s = await until(x => x.stats.variant === 'night' && x.stats.zzz > 0, 6000); ok(s.stats.variant === 'night' && s.stats.zzz > 0, '夜間版＋zzz', s.stats);
  ok(s.stats.glow > 0, '燈光（emissive／glow）', s.stats.glow); await shot('14-sleep-night');
  await setT(new Date(2026, 10, 2, 3, 30).getTime() + DAY); s = await until(x => x.mode !== 'sleep', 5000); ok(s.mode !== 'sleep' && !s.sleepWanted, '03:00 後醒', s.mode);
  await setT(T0); await dev('night'); s = await until(x => x.stats.variant === 'night', 6000); ok(s.night && s.stats.variant === 'night', '開發者「日／夜」→ 夜晚（唔瞓）', s.mode); await shot('15-night-awake');
  await dev('sleep'); s = await h(); ok(s.mode === 'sleep', '開發者「同床瞓」');
  await dev('auto'); await W(300); s = await h(); ok(!s.night && s.mode !== 'sleep', '開發者「還原自動」', { n: s.night, m: s.mode });

  console.log('# 返花園／存檔');
  await page.locator('[data-testid=house-back]').click(); await W(400); s = await h(); ok(!s.open && !(await page.locator('[data-testid=house-view]').isVisible()), '撳返回 → 花園');
  await E(() => __qa.house.open()); await W(300); await page.keyboard.press('Escape'); await W(300); s = await h(); ok(!s.open, 'Esc → 花園');
  await dev('open'); s = await h(); ok(s.open, '開發者「入屋仔」'); await dev('deco'); s = await h(); ok(s.deco, '開發者「開佈置」'); await shot('16-dev-deco');
  await dev('close'); s = await h(); ok(!s.open, '開發者「返花園」');
  const saved = JSON.stringify((await h()).save.slots);
  await E(() => __glimmer.save()); await load('q=high&hour=13&seed=21&ev=0', false); s = await h();
  ok(JSON.stringify(s.save.slots) === saved && s.save.owned.length >= 8, '重載 → 屋仔存檔', s.save);
  ok(s.rail && s.rail.locked === '0', '重載後入口照開');

  console.log('# 團絨唔受影響');
  { const e1 = JSON.parse(await evoSnap()), e0 = JSON.parse(evo0); ok(JSON.stringify(e1.evo) === JSON.stringify(e0.evo) && JSON.stringify(e1.route) === JSON.stringify(e0.route), '團絨進化路線分唔變', { e0: e0.evo, e1: e1.evo }); ok(e1.g === e0.g, '小遊戲紀錄唔變'); }
  ok(await E(() => Glimmer.series2.LINES_OUT ? !JSON.stringify(Glimmer.series2.LINES_OUT).includes('即將開放') : true), '已冇「即將開放」字');

  console.log('# ?house=0');
  await load('q=high&hour=13&seed=21&ev=0&house=0'); await toKid(); await E(() => __qa.s2.test('family')); await W(800);
  ok(!(await page.locator('[data-testid=s2-rail-house]').count()) && !(await E(() => __qa.devmode.sections().some(x => x.id === 'house'))), '?house=0 → 冇屋仔');

  const bad = errs.filter(e => !/favicon|ERR_FILE_NOT_FOUND|net::/.test(e)); ok(!bad.length, '冇 console error', bad);
  console.log('\n' + pass + ' 過／' + fail + ' 唔過'); await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
