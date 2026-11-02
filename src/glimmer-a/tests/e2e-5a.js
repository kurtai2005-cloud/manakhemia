/* 《微光小圃》 e2e-5a — 第 5 批 5a 家族長線（docs-gdd/series2-4a4b-spec.md §5a＋定案）：家族等級／經驗（追溯）、新蛋二揀一（灰卡原因、遲啲先、rail「新蛋」）、
   揀團絨蛋（主養搬入屋＋新一代）、揀細佬蛋（成年細佬搬入屋）、房 2–4（未開＝「家族 LvN 開」、圓點、n/4 隻）、住客（行／瞓）、打招呼（interact 面對面）、
   寵物卡（做主養／搬房）、家具一件一間＋「擺設」手信、升級彈窗、族譜（Lv10 金色）、🛠「5a」、存檔、?l5=0。截圖 → SHOTS（5a-*.png）。
   node tests/e2e-5a.js（BASE 預設 http://localhost:8240/index.html） */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const T0 = new Date(2026, 10, 2, 13, 0).getTime(), DAY = 86400e3;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '5a-' + n + '.png' });
  const L = () => E(() => __qa.l5.st());
  const h = () => E(() => __qa.house.st());
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').isVisible().catch(() => false);
  const click = (tid) => page.locator('[data-testid=' + tid + ']').click();
  const prep = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const hookToast = () => E(() => { window.__toasts = []; const U = Glimmer.ui, t = U.toast; if (U._h5) return; U._h5 = 1; U.toast = function (m) { window.__toasts.push(String(m)); return t.apply(this, arguments); }; });
  const toasts = () => E(() => window.__toasts.slice());
  const load = async (qs, clear) => {
    if (clear !== false) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad); await setT(T0); if (clear !== false) await prep(); await hookToast(); await W(400);
  };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(150); } };
  const openDev = async () => { await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await click('dev-btn'); await W(400); };
  const dev = async (k) => { await openDev(); await click('dev-l5-' + k); await W(600); };
  const devRun = (k) => E((k) => __qa.l5.dev().items.find(i => i.k === k).run(), k);   // 屋入面（dev 掣俾屋蓋住）直接行
  const toKid = async () => { await E(() => { const G = __glimmer, SR = Glimmer.series2, s = G.state, now = G.now(); s.stage = 'elder'; SR.noteElder(s, now - 6 * 86400e3); const o = SR.st(s); o.dueDay = SR.dayNum(now) - 6; SR.deliver(s, now - 5 * 86400e3);
    o.dreams = [{ day: 1, line: 'A', at: 0, live: true }, { day: 2, line: 'A', at: 0, live: true }, { day: 3, line: 'E', at: 0, live: true }]; SR.hatch(s, now - 1 * 86400e3); o.relQ.length = 0; s.stage = 'adult'; G.save(); }); await W(400); };

  console.log('# 載入');
  await load('q=high&hour=13&seed=21&ev=0');
  let l = await L(); ok(await E(() => !!(window.__glimmer.l5 && Glimmer.long5a && __glimmer.house5)), 'long5a＋long5aui 裝咗');
  ok(await E(() => /^5[ab]/.test(Glimmer.data.PARAMS.series2.version)), '版本 5a');
  ok(l.lv === 1 && l.xp === 0 && l.res.length === 0 && !l.offer, '新存檔：家族 Lv1・0 XP・冇住客', { lv: l.lv, xp: l.xp });
  ok(l.quiet === true, '?ev=0 → 唔自動彈窗');

  console.log('# 🛠 開發者「5a」');
  await openDev();
  ok((await page.locator('[data-testid=dev-version]').innerText()).match(/版本 5(a\.1|b)/), '開發者模式「版本 5a.1」');
  ok((await page.locator('[data-testid=dev-sec-l5]').innerText()).includes('5a'), '分組「5a（家族長線）」');
  const KEYS = ['prep', 'offer', 'offerKidOff', 'offerFull', 'pickTr', 'pickKid', 'xp', 'lv5', 'lv10', 'lvup', 'room2', 'room3', 'room4', 'resTr', 'resKid', 'fill', 'card', 'greet', 'tree', 'treeGold', 'sv', 'reset', 'kidMain', 'trMain'];
  { let n = 0; for (const k of KEYS) if (await page.locator('[data-testid=dev-l5-' + k + ']').count()) n++; ok(n === KEYS.length, KEYS.length + ' 個掣齊', n); }
  ok(/Lv1・0 XP・住客 0/.test(await page.locator('[data-testid=dev-status-l5]').innerText()), 'status：Lv・XP・住客・房 n/4');
  await page.locator('[data-testid=dev-sec-l5]').scrollIntoViewIfNeeded(); await shot('01-dev-section'); await closeModals();

  console.log('# 經驗（追溯）＋成年 → 翌日新蛋');
  await toKid(); await dev('prep'); await E(() => __qa.l5.tick()); l = await L();
  const fam = await E(() => __qa.l5.fam());
  ok(fam.init > 0 && Object.keys(fam.adults).length === 1 && fam.seen['raise:' + Object.keys(fam.adults)[0]], 'scan：init＋成年記錄', Object.keys(fam.adults));
  ok(l.xp >= 50 + 10 + 5 && l.lv >= 1, '追溯：細佬成年 +50・新形態 +10・葉仔床 +5', { xp: l.xp, lv: l.lv });
  ok(l.lvQ.length >= 1 && !l.ov, '升級排隊（?ev=0 唔自動彈）', { q: l.lvQ, ov: l.ov });
  ok(!!l.offer && !l.ready, '細佬成年 → 排咗新蛋（翌日）', l.offer);
  await setT(T0 + DAY); await E(() => __qa.l5.tick()); await W(300); l = await L();
  ok(l.ready && l.egg, '翌日：新蛋到（rail「新蛋」掣）', { ready: l.ready, egg: l.egg });
  ok(await vis('l5-rail-egg'), 'rail「新蛋」掣見到');
  await shot('02-rail-egg');

  console.log('# 新蛋二揀一');
  await click('l5-rail-egg'); await W(400); l = await L();
  ok(l.ov === 'offer' && await vis('l5-offer'), '撳「新蛋」→ 二揀一');
  ok((await page.locator('[data-testid=l5-offer-title]').innerText()).includes('新蛋嚟咗'), '標題「新蛋嚟咗！」');
  ok((await page.locator('[data-testid=l5-pick-tr]').getAttribute('data-ok')) === '0' && (await page.locator('[data-testid=l5-pick-tr]').getAttribute('data-reason')) === 'mainYoung', '團絨蛋灰：主養未到靜光');
  ok((await page.locator('[data-testid=l5-pick-kid]').getAttribute('data-ok')) === '1', '細佬蛋可以揀（成年細佬搬入屋）');
  await shot('03-offer');
  await click('l5-pick-tr'); await W(200); ok((await toasts()).pop().includes('主養未成年'), '撳灰卡 → toast 原因');
  await click('l5-later'); await W(300); l = await L();
  ok(!l.ov && l.ready && l.offer.snz > 0, '「遲啲先」→ 收起；蛋仲喺度（rail 掣留低）');
  await click('l5-rail-egg'); await W(300);
  const kidOld = await E(() => ({ id: Glimmer.series2.st(__glimmer.state).fid, line: Glimmer.series2.st(__glimmer.state).line }));
  await click('l5-pick-kid'); await W(500); l = await L();
  const p2 = await E(() => ({ phase: __glimmer.state.pet2.phase, fid: __glimmer.state.pet2.fid, bro: __glimmer.state.pet2.bro }));
  ok(p2.phase === 'egg' && p2.fid !== kidOld.id && !l.offer && !l.ov, '揀細佬蛋 → 新細佬蛋（offer 清）', p2);
  ok(l.res.some(r => r.id === kidOld.id && r.kind === 'kid' && r.room === 'room1'), '成年細佬搬入屋（房 1）', l.res);
  ok((await toasts()).some(t => t.includes('新細佬蛋')), 'toast「新細佬蛋嚟咗！」');
  ok(!(await vis('l5-rail-egg')), '揀完 → rail「新蛋」掣收');

  console.log('# 細佬蛋灰＋揀團絨蛋（新一代）');
  await dev('offerKidOff'); l = await L();
  ok(l.ov === 'offer' && (await page.locator('[data-testid=l5-pick-kid]').getAttribute('data-reason')) === 'raising', '細佬養緊 → 細佬蛋灰（細佬養緊）');
  ok((await page.locator('[data-testid=l5-pick-tr]').getAttribute('data-ok')) === '1', '團絨到靜光 → 團絨蛋可以揀');
  await shot('04-offer-kid-off');
  const gen0 = await E(() => __glimmer.state.gen || 1);
  await click('l5-pick-tr'); await W(600); l = await L();
  const g1 = await E(() => ({ gen: __glimmer.state.gen, stage: __glimmer.state.stage }));
  ok(g1.gen === gen0 + 1 && g1.stage === 'egg', '揀團絨蛋 → 第 ' + (gen0 + 1) + ' 代團絨蛋（主養）', g1);
  ok(l.res.some(r => r.id === 'tr' + gen0 && r.kind === 'tr'), '靜光團絨搬入屋', l.res.map(r => r.id));
  ok(await E(() => Glimmer.long5a.count(__glimmer.state, 'room1')) === 3, '房 1：主養＋2 住客＝3/4');

  console.log('# 屋仔 HUD／房');
  await E(() => __qa.house.open()); await W(900); let s = await h();
  ok(s.open && s.room === 'room1' && s.res.length === 2, '入屋：房 1 有 2 隻住客', s.res.length);
  ok((await page.locator('[data-testid=house-cap]').innerText()).includes('3/4'), 'HUD「3/4 隻」');
  { const D = {}; for (const k of ['room1', 'room2', 'room3', 'room4']) D[k] = await page.locator('[data-testid=house-dot-' + k + ']').getAttribute('data-state');
    ok(D.room1 === 'cur' && D.room2 === (l.lv >= 2 ? 'open' : 'locked') && D.room3 === 'locked' && D.room4 === 'locked', '圓點：而家間＝金、已開＝白、未開＝鎖', D); }
  if (l.lv < 2) { ok((await page.locator('[data-testid=house-room-r]').getAttribute('data-locked')) === '1', '右箭咀：房 2 上鎖'); await click('house-room-r'); await W(300); ok((await toasts()).pop().includes('家族 Lv2 開'), '撳上鎖箭咀 → 「家族 Lv2 開」'); }
  ok((await page.locator('[data-testid=house-fam]').innerText()).includes('Lv' + l.lv), 'HUD 家族等級 chip');
  await shot('05-room1-residents');
  await devRun('xp'); await devRun('xp'); await W(400); l = await L();
  ok(l.lv >= 2 && l.rooms.room2.open && l.rooms.room2.gift, 'Lv2 → 房 2 開＋送手信', l.rooms.room2);
  ok(l.rooms.room2.deco === l.rooms.room2.gift, '手信自動擺喺新房（擺設位）');
  await click('house-room-r'); await W(1200); s = await h();
  ok(s.room === 'room2', '右箭咀 → 森林閣樓', s.room);
  ok((await page.locator('[data-testid=house-title]').innerText().catch(() => '')).includes('森林閣樓') || await E(() => document.querySelector('#s2houseV').innerText.includes('森林閣樓')), '房名「森林閣樓」');
  await shot('06-room2');

  console.log('# 住客＋打招呼');
  let r1 = await E(() => __qa.l5.addRes('tr', 'room2')); let r2 = await E(() => __qa.l5.addRes('kid', 'room2')); await W(1500); s = await h();
  ok(r1 && r2 && s.res.length === 2 && s.res.every(a => a.fk), '房 2 加 2 隻住客（團絨＋細佬）', s.res);
  ok((await page.locator('[data-testid=house-room-r]').getAttribute('data-locked')) === '1', '右箭咀：房 3 上鎖（Lv5）');
  await click('house-room-r'); await W(300); ok((await toasts()).pop().includes('家族 Lv5 開'), '撳上鎖箭咀 → 「家族 Lv5 開」'); s = await h(); ok(s.room === 'room2', '上鎖唔會轉房');
  const g = await E((a) => __glimmer.house5.greet(a[0], a[1]), [r1.id, r2.id]); await W(300); const gs = await E(() => __glimmer.house5.greetSt());
  ok(g.ok && gs && gs.gap >= 22, '打招呼開始（gap≥22）', { g, gs });
  let acts, A1, A2; for (let i = 0; i < 50; i++) { acts = await E(() => __glimmer.house5.actors()); A1 = acts.find(a => a.id === r1.id); A2 = acts.find(a => a.id === r2.id); if (A1.clip === 'interact' && A2.clip === 'interact') break; await W(80); }
  ok(A1.clip === 'interact' && A2.clip === 'interact', '兩隻播 interact', [A1.clip, A2.clip]);
  ok(A1.dir === -A2.dir && Math.sign(A2.x - A1.x) === A1.dir, '面對面', { a: [A1.x, A1.dir], b: [A2.x, A2.dir] });
  await shot('07-greet');
  await W(1500); acts = await E(() => __glimmer.house5.actors()); ok(acts.filter(a => a.who === 'res').every(a => a.clip !== 'interact'), '1 秒後打完 → 返去閒住');

  console.log('# 寵物卡');
  const css = await E((id) => __glimmer.house5.css(id), r1.id); await E((id) => { const p = __glimmer.house5.actors().find(a => a.id === id); }, r1.id);
  await E(() => __qa.house.freeze && __qa.house.freeze()); const css2 = await E((id) => __glimmer.house5.css(id), r1.id);
  await page.mouse.click(css2.x, css2.y); await W(500); l = await L();
  ok(l.ov === 'card' && l.ovData.id === r1.id, '撳住客 → 寵物卡', { ov: l.ov, d: l.ovData });
  ok((await page.locator('[data-testid=l5-card-name]').innerText()).length > 0 && (await page.locator('[data-testid=l5-card-info]').innerText()).includes('森林閣樓'), '卡：名＋「住喺森林閣樓」');
  ok((await page.locator('[data-testid=l5-card-main]').getAttribute('data-dis')) === '1', '主養（蛋）未到靜光 → 做主養灰');
  await shot('08-pet-card');
  await click('l5-card-move'); await W(300); ok(await vis('l5-move'), '搬房 chooser');
  ok((await page.locator('[data-testid=l5-move-room2]').getAttribute('data-dis')) === '1' && (await page.locator('[data-testid=l5-move-room3]').getAttribute('data-dis')) === '1', '而家間／未開房灰');
  await shot('09-move');
  await click('l5-move-room1'); await W(400); l = await L();
  ok(l.res.find(r => r.id === r1.id).room === 'room1', '搬去屋仔（房 1）');
  s = await h(); ok(s.res.length === 1, '房 2 剩 1 隻（即時更新）', s.res.length);
  // 做主養（團絨住客 ↔ 主養）
  await E(() => __qa.l5.elder()); await E((id) => __qa.l5.card(id), r1.id); await W(300);
  ok((await page.locator('[data-testid=l5-card-main]').getAttribute('data-dis')) !== '1', '主養到靜光 → 做主養可以撳');
  const mainOld = await E(() => 'tr' + (__glimmer.state.gen || 1));
  await click('l5-card-main'); await W(500); l = await L();
  ok(!l.res.some(r => r.id === r1.id) && l.res.some(r => r.id === mainOld), '做主養：住客出花園，舊主養入屋', l.res.map(r => r.id));
  ok((await toasts()).some(t => t.includes('做咗主養')), 'toast「…做咗主養！」');
  await E((id) => __qa.l5.card(id), mainOld); await W(300); await E(() => __qa.l5.close());

  console.log('# 家具一件一間＋擺設');
  await E(() => __qa.house.decorate(true)); await W(500);
  ok(await page.locator('[data-testid=house-tab-deco]').count() === 1, '第 7 個 tab「擺設」');
  await E(() => __qa.house.tab('deco')); await W(300);
  ok(await page.locator('[data-testid=house-svrow] .card').count() === 11, '擺設：收起＋10 件手信卡');
  await shot('10-deco-tab');
  await E(() => __qa.house.tab('bed')); await W(200);
  const pl = await E(() => __qa.house.place('bed', 'bed_leaf')); await W(300);
  const where = await E(() => Glimmer.long5a.whereIs(__glimmer.state, 'bed_leaf'));
  ok(pl.ok && where === 'room2' && pl.from === 'room1', '葉仔床由房 1 搬嚟房 2（一件一間）', { pl, where });
  ok(await E(() => Glimmer.long5a.cardState(__glimmer.state, 'room1', 'bed_leaf')) === 'elsewhere', '房 1 卡：喺森林閣樓');
  await E(() => __qa.house.decorate(false)); await W(400);

  console.log('# 升級彈窗／Lv5／Lv10');
  await devRun('lvup'); await W(500); ok(await vis('l5-lvup') && (await page.locator('[data-testid=l5-lvup-title]').innerText()).includes('家族升級'), '升級彈窗「家族升級！」');
  ok((await page.locator('[data-testid=l5-lvup-unlock]').innerText()).length > 0, '解鎖卡');
  await shot('11-levelup'); await click('l5-lvup-ok'); await W(300); ok(!(await L()).ov, '「好嘢！」收');
  await devRun('room3'); await W(1400); s = await h(); l = await L();
  ok(l.lv >= 5 && l.rooms.room3.open && s.room === 'room3', 'Lv5 → 入星夜書房', { lv: l.lv, room: s.room });
  await shot('12-room3');
  await devRun('room4'); await W(1400); s = await h(); ok(s.room === 'room4', 'Lv8 → 入海風小屋', s.room); await shot('13-room4');
  ok((await page.locator('[data-testid=house-room-r]').count()) === 0 || !(await vis('house-room-r')), '最後一間 → 冇右箭咀');
  await devRun('fill'); await W(800); ok((await page.locator('[data-testid=house-cap]').innerText()).includes('4/4'), '住滿：「4/4 隻」');
  await shot('14-room4-full');
  await E(() => __qa.house.close()); await W(400);

  console.log('# 族譜');
  await dev('tree'); l = await L(); ok(l.ov === 'tree' && await vis('l5-tree'), '族譜');
  const nodes = await page.locator('#l5ov .node').count(); ok(nodes >= 5, '族譜 node ≥5', nodes);
  ok(await page.locator('#l5ov [data-link]').count() > 0, '金線連住代');
  ok(await page.locator('#l5ov .node[data-state=main]').count() >= 1, '主養有金冠');
  await shot('15-tree');
  await E(() => __qa.l5.close()); await dev('treeGold'); l = await L();
  ok(l.lv === 10 && await vis('l5-tree-goldframe') && (await page.locator('[data-testid=l5-tree-title]').innerText()).includes('微光大家族'), 'Lv10 金色族譜＋稱號「微光大家族」');
  await shot('16-tree-gold');
  await page.locator('#l5ov .node[data-state=house]').first().click(); await W(300); ok((await L()).ov === 'card', '族譜撳 node → 寵物卡'); await E(() => __qa.l5.close());

  console.log('# 屋企爆滿');
  await dev('offerFull'); ok((await page.locator('[data-testid=l5-pick-tr]').getAttribute('data-reason')) === 'full' && (await page.locator('[data-testid=l5-pick-tr-why]').innerText()).includes('住滿'), '全部住滿 → 團絨蛋灰（屋企住滿）');
  await shot('17-offer-full'); await click('l5-later'); await W(200);

  console.log('# 5a.1 細佬做主養（遊策裁定）');
  await load('q=high&hour=13&seed=21&ev=0'); await toKid();
  await dev('kidMain'); await closeModals(); await W(900); l = await L();
  const km = await E(() => { const s = __glimmer.state; return { km: s.fam && s.fam.km, main: s.fam && s.fam.main, p2: Glimmer.series2.st(s).phase, res: s.fam.res.map(r => r.id + ':' + r.kind + ':' + r.room), stage: s.stage, form: s.form, ov: __glimmer.evo.overlayInfo(), pd: __glimmer.renderer.petDraw }; });
  ok(km.km && km.main === 'kid:' + km.km.id, '①🛠「細佬做主養」→ 細佬做主養', km.main);
  ok(km.p2 === 'none', '①pet2 空出嚟（等新蛋）', km.p2);
  ok(km.res.some(x => /^tr\d+:tr:room1$/.test(x)), '①原主養團絨搬入房 1', km.res);
  ok(km.pd && km.pd.km === km.km.id, '①花園主位畫細佬（petDraw＝細佬）', km.pd);
  ok(await E(() => (__qa.s2.st().render.crown | 0) > 0 && (__qa.s2.st().render.km | 0) > 0), '①細佬（主位）＋頭頂皇冠有畫', await E(() => __qa.s2.st().render));
  ok(km.stage === 'elder' && km.ov.form !== 'egg' && /團絨|soft|radiant|sprout/.test(km.ov.form + '') , '③浮動照顯示團絨（' + km.ov.form + '）', km.ov);
  await shot('18-kidmain-garden');
  const care = await E(() => { const G = __glimmer, s = G.state, SIM = Glimmer.sim, SYS = Glimmer.sys12; const r0 = JSON.stringify({ evo: s.evo, evs: s.evs, form: s.form }), g0 = s.growthSec; s.needs.hunger = 40; s.sleeping = false;
    const f = SIM.feed(s, Glimmer.data.FOODS[0].id); for (let i = 0; i < 120; i++) SIM.step(s, 60, {}); return { fed: f.ok, h: s.needs.hunger, grow: s.growthSec - g0, route: JSON.stringify({ evo: s.evo, evs: s.evs, form: s.form }) === r0, mg: SYS.grant(s, 5, 'mg', G.now()), q: SYS.grant(s, 5, 'quest', G.now()), fade: SIM.fade(s, G.now()).ok }; });
  ok(care.fed && care.grow === 0 && care.route, '②照顧循環（餵食／肚餓）照行；唔長大、§7 路線唔郁', care);
  ok(care.mg === 0 && care.q === 0 && care.fade === false, '②冇碎（小遊戲／委託）、唔化光', care);
  await E(() => __glimmer.house5.open()); await W(1600);
  const ha = await E(() => __qa.house.st().res.map(a => a.id + ':' + a.kind)); ok(ha.includes(km.km.id + ':kid') && ha.some(x => /^tr\d+:tr$/.test(x)), '屋企房 1：細佬主養＋團絨住客', ha);
  await shot('19-kidmain-house');
  await E((id) => __glimmer.l5.card(id), km.km.id); await W(400);
  ok(await vis('l5-card-crown') && (await page.locator('[data-testid=l5-card-main]').innerText()).includes('主養緊') && (await page.locator('[data-testid=l5-card-info]').innerText()).includes('主養'), '細佬寵物卡：皇冠＋主養緊');
  await E(() => __qa.l5.close()); await E(() => __glimmer.house5.close()); await W(400);
  const back = await devRun('trMain'); await W(300); const k2 = await E(() => ({ km: __glimmer.state.fam.km, res: __glimmer.state.fam.res.map(r => r.id + ':' + r.kind) }));
  ok(back.ok && !k2.km && k2.res.includes(km.km.id + ':kid'), '🛠「揀返團絨做主養」→ 細佬返屋', { back, k2 });

  console.log('# 存檔');
  const before = await E(() => JSON.stringify({ lv: __qa.l5.fam().lv, res: __qa.l5.fam().res.map(r => r.id + ':' + r.room), deco: __qa.l5.fam().rooms }));
  await E(() => __glimmer.save()); await load('q=high&hour=13&seed=21&ev=0', false);
  const after = await E(() => JSON.stringify({ lv: __qa.l5.fam().lv, res: __qa.l5.fam().res.map(r => r.id + ':' + r.room), deco: __qa.l5.fam().rooms }));
  ok(before === after, 's.fam 存檔＋載返一樣', before === after ? '' : [before.slice(0, 400), after.slice(0, 400)]);

  console.log('# 自動彈窗（冇 ?ev=0）');
  await load('q=high&hour=13&seed=21'); await toKid(); await E(() => __qa.l5.tick()); await E(() => __qa.l5.xp(200)); await W(1600); l = await L();
  ok(l.ov === 'lvup' && !l.quiet, '升級 → 自動彈「家族升級！」', l.ov);

  console.log('# ?l5=0');
  await load('q=high&hour=13&seed=21&ev=0&l5=0'); ok(await E(() => !__glimmer.l5 && !(window.__qa && __qa.l5)), '?l5=0 → 5a 介面全停');
  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log('\n' + pass + ' pass, ' + fail + ' fail');
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
