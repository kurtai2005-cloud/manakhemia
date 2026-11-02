/* 《微光小圃》 e2e-6c — 第 6 批 6c「夢境探險」（遊策 breakthrough-6a6d-spec §6c）：
   團絨瞓緊＋21:00–03:00 先出「入夢」、每晚 1 次；3×5 夢地圖跟當日 6a 記錄（餵菇→蘑菇森林、淋水→水珠湖、玩得多→玩具房、夜晚→星空）；
   撳格陪團絨行、拾夢碎片、5 片 1 張夢圖鑑；時間到／拾晒／醒返 → 小結；每晚 ≤3 分鐘；唔郁錢包／親密度；placeholder（洋紅虛線）；
   字清晰度（FP12 24px、對比 ≥4.5）、熱區 ≥48、🛠「6c」、?l6c=0。截圖 360×780 DPR3 → SHOTS（6c-*.png）。node tests/e2e-6c.js */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const { audit } = require('./readaudit');
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const NR = (a, b) => typeof a === 'number' && Math.abs(a - b) < 0.3;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };


(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.type() + ': ' + m.text() + ' ' + ((m.location() || {}).url || '')); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '6c-' + n + '.png' });
  const Q = () => E(() => __qa.l6c.st());
  const QS = 'q=high&seed=21&ev=0&hour=22';
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load).catch(() => { }); await E(() => __glimmer.houseLoad).catch(() => { }); };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = document.querySelector('[data-testid=dev-close]') || [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(250); } };
  // 當日記錄：暖菇飯 meal 次、淋水 rinse 次、玩 play 次；瞓緊
  const prep = (r) => E((r) => { const s = __glimmer.state, M6 = Glimmer.long6a, t = __glimmer.now(); s.stage = 'adult'; s.form = 'moon'; s.poops = 0;
    Object.assign(s.needs, { mood: 70, energy: 20, hunger: 80, clean: 100 }); s.sleeping = true;
    for (let i = 0; i < r[0]; i++) M6.note(s, 'food', 'meal', 0, 0, 0, t); for (let i = 0; i < r[1]; i++) M6.note(s, 'care', 'rinse', 0, 0, 0, t); for (let i = 0; i < r[2]; i++) M6.note(s, 'care', 'play', 0, 0, 0, t); __glimmer.save && __glimmer.save(); }, r || [3, 1, 0]);
  const sleep = () => E(() => { const s = __glimmer.state; s.sleeping = true; s.needs.energy = 20; });
  const fresh = async (qs, r) => { await page.goto(BASE + '?' + (qs || QS)); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + (qs || QS)); await ready(); await prep(r); await W(1300); await closeModals(); await sleep(); await W(1200); };
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').first().isVisible().catch(() => false);
  const click = (tid) => page.locator('[data-testid=' + tid + ']').first().click();
  const readOk = async (name, sel) => { const a = await audit(page, sel); ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（FP12 24px、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); };
  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0;
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; }
        return { id: e.dataset.testid || e.id, n, lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1) && L.every(x => x.n === 8), label + ' 熱區 ≥48（' + L.length + ' 個）', L.filter(x => x.n < 8).slice(0, 3)); };
  const cnt = (g) => g.reduce((o, k) => (o[k] = (o[k] | 0) + 1, o), {});
  const tileCenterWalk = async (i) => { await click('l6c-tile-' + i); for (let k = 0; k < 40; k++) { const q = await Q(); if (q.pos === i && !q.path.length) return true; await W(150); } return false; };

  console.log('# 載入＋入夢條件');
  await fresh();
  ok(await E(() => !!(Glimmer.long6c && Glimmer.long6cui && window.__qa && __qa.l6c && __glimmer.l6c)), 'long6c＋long6cui 裝咗');
  ok(await E(() => Glimmer.data.PARAMS.series2.version === '6c'), '版本 6c');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l6c' && s.title.includes('6c'))), '🛠 開發者模式有「6c」分組');
  let q = await Q(); ok(q.can && q.rail && q.railMode === 'enter', '22:00＋瞓緊 → rail「入夢」', { can: q.can, why: q.why, rail: q.rail });
  ok(await E(() => document.querySelector('#l6cbtn i.l').textContent === '入夢'), '掣字「入夢」');
  await hitOk('rail「入夢」', '[data-testid=l6c-rail]');
  await shot('01-garden-rail');
  await E(() => { __glimmer.state.sleeping = false; __qa.l6c.railTick(); }); q = await Q(); ok(!q.can && q.why === 'awake' && !q.rail, '醒咗 → 冇「入夢」', { why: q.why, rail: q.rail });
  await E(() => { __glimmer.hourOverride = 14; __glimmer.state.sleeping = true; __qa.l6c.railTick(); }); q = await Q(); ok(q.why === 'hours' && !q.rail, '14:00 瞓緊 → 唔係夜晚，冇掣', q.why);
  await E(() => { __glimmer.hourOverride = 22; }); await sleep(); await E(() => __qa.l6c.railTick()); q = await Q(); ok(q.rail && q.can, '返 22:00 → 又有');

  console.log('# 入夢：地圖跟當日記錄');
  const w0 = await E(() => ({ w: __glimmer.state.sys12 && __glimmer.state.sys12.wallet.total, b: JSON.stringify(__glimmer.state.sys12 && __glimmer.state.sys12.bond), b5: JSON.stringify(__glimmer.state.b5 || null) }));
  await click('l6c-rail'); await W(300); q = await Q(); ok(q.on && q.tonight && !q.can && q.why === 'done', '撳「入夢」→ 入咗夢、今晚用咗', { on: q.on, why: q.why });
  const plan = await E(() => __qa.l6c.plan()); const c = cnt(plan.grid);
  ok(plan.grid.length === 15 && c.forest === 7 && c.lake === 4 && c.star === 4 && !c.toy, '暖菇飯 3、淋水 1、冇玩 → 森林 7／湖 4／星 4（冇玩具房）', c);
  ok(plan.facts && plan.facts.meal === 3 && plan.facts.rinse === 1, '地圖用嘅記錄＝當日 6a 記錄', plan.facts);
  ok(await E((g) => JSON.stringify(Glimmer.long6c.plan(__glimmer.state, __glimmer.now(), __glimmer.hour()).grid) === JSON.stringify(g), plan.grid), '畫面地圖＝邏輯重算（同一晚同記錄）');
  ok(await E(() => [...document.querySelectorAll('#l6cov .tile')].map(t => t.dataset.th).join()) === plan.grid.join(), '15 格主題同地圖一致');
  await W(1300); q = await Q(); ok(q.phase === 'play', '過場後可以行', q.phase);
  ok(await E(() => ['6c:tile_forest', '6c:tile_lake', '6c:tile_star', '6c:dream_walk', '6c:nightcap', '6c:frag', '6c:transition'].every(k => document.querySelector('#l6cov [data-ph="' + k + '"]'))), 'placeholder：tile×3、dream_walk、nightcap、frag、transition');
  ok(await E(() => getComputedStyle(document.querySelector('#l6cov [data-ph="6c:tile_forest"]')).outlineStyle === 'dashed'), 'placeholder 洋紅虛線');
  await readOk('夢境畫面', '#l6cov');
  await hitOk('15 格＋醒返', '#l6cov .tile,[data-testid=l6c-wake]', 16);
  await shot('02-dream-map');

  console.log('# 行路＋拾碎片');
  const f0 = plan.frags.filter(f => f.at === 0); ok(f0.length === 2 && (await E(() => document.querySelectorAll('#l6cov .frag[data-on="1"]').length)) === 2, '一開始有 2 片');
  ok(await tileCenterWalk(10), '撳格 → 團絨逐格行過去'); q = await Q(); ok(q.rev >= 6, '行過嘅格霧散開', q.rev);
  for (const f of f0) await tileCenterWalk(f.tile);
  q = await Q(); ok(q.got === 2 && q.frag[f0[0].th] >= 1, '行到碎片格 → 拾到（即刻入帳）', { got: q.got, frag: q.frag });
  ok((await E(() => __qa.l6c.toasts().join('|'))).includes('夢碎片'), '拾到有提示');
  const w1 = await E(() => ({ w: __glimmer.state.sys12 && __glimmer.state.sys12.wallet.total, b: JSON.stringify(__glimmer.state.sys12 && __glimmer.state.sys12.bond), b5: JSON.stringify(__glimmer.state.b5 || null) }));
  ok(w1.w === w0.w && w1.b5 === w0.b5, '唔出碎、唔加月眠分', { w0: w0.w, w1: w1.w });
  ok(await E(() => __glimmer.state.sleeping === true), '夢入面團絨照瞓');
  await E(() => __qa.l6c.skip(26)); await W(400); ok((await E(() => document.querySelectorAll('#l6cov .frag[data-on="1"]').length)) === 1, '25 秒 → 第 3 片浮出');

  console.log('# 時間到 → 小結（≤3 分鐘）');
  await E(() => __qa.l6c.skip(130)); await W(600); q = await Q(); ok(q.endWhy === 'time' && q.sec <= 180, '150 秒到 → 自動醒（' + Math.round(q.sec) + ' 秒）', { why: q.endWhy, sec: q.sec });
  await W(1400); ok(await vis('l6c-sum'), '出夢過場後 → 今晚小結');
  ok((await E(() => document.querySelector('[data-testid=l6c-sum-got]').textContent)).includes('2／6'), '小結：拾到 2／6');
  await readOk('今晚小結', '[data-testid=l6c-sum]'); await hitOk('小結掣', '[data-testid=l6c-sum-dexbtn],[data-testid=l6c-sum-ok]', 2);
  const lg = (await Q()).log.slice(-1)[0]; ok(lg && lg.sec <= 180 && lg.got === 2, '記錄：' + (lg && lg.sec) + ' 秒 ≤180', lg);
  await shot('03-summary');
  await click('l6c-sum-dexbtn'); await W(400); q = await Q(); ok(!q.on && q.dex, '「睇夢圖鑑」→ 夢圖鑑');
  ok(await E(() => document.querySelectorAll('#l6cdex [data-ph^="6c:card_"]').length === 20), '夢圖鑑 20 張 placeholder（6c:card_*）');
  await readOk('夢圖鑑', '#l6cdex'); await hitOk('夢圖鑑卡＋✕', '#l6cdex .card6,[data-testid=l6c-dex-close]', 21);
  await click('l6c-card-f1'); await W(150); ok((await E(() => document.querySelector('[data-testid=l6c-dex-detail]').textContent)).includes('未砌到'), '撳未有嘅卡 → 未砌到');
  await click('l6c-dex-close'); await W(300); q = await Q(); ok(!q.dex && q.rail && q.railMode === 'dex', '今晚用咗 → rail 變「夢簿」', { rail: q.rail, m: q.railMode });
  ok(!(await E(() => __qa.l6c.start('qa').ok)), '同一晚再入 → 唔得');

  console.log('# 拾晒 6 片 → 提早醒；砌夢圖鑑');
  await E(() => { const o = Glimmer.long6c.resetNight(__glimmer.state); o.frag.forest = 4; }); await sleep(); await E(() => __qa.l6c.start('qa')); await W(1400);
  const p2 = await E(() => __qa.l6c.plan()); await E(() => __qa.l6c.skip(101));
  for (const f of p2.frags) await E((i) => __qa.l6c.walkTo(i), f.tile);
  await W(500); q = await Q(); ok(q.endWhy === 'all' && q.got === 6, '6 片拾晒 → 自動醒（all）', { why: q.endWhy, got: q.got });
  await W(1500); ok((await E(() => document.querySelector('[data-testid=l6c-sum-got]').textContent)).includes('6／6'), '小結 6／6');
  q = await Q(); ok(q.cards >= 1 && q.byTh.forest >= 1 && (await E(() => !!Glimmer.long6c.st(__glimmer.state).cards.f1)), '森林碎片（4＋今晚）夠 5 片 → 第 1 張夢圖鑑「會唱歌嘅菇」', { cards: q.cards, frag: q.frag });
  ok(await vis('l6c-sum-card'), '小結列出新夢圖鑑');
  await click('l6c-sum-ok'); await W(300); ok(!(await Q()).on && !(await E(() => !!document.getElementById('l6cov'))), '「好」→ 返花園');

  console.log('# 醒返（提早）＋玩具房');
  await fresh(QS, [0, 0, 3]); const p3 = await E(() => (__qa.l6c.start('qa'), __qa.l6c.plan())); ok(cnt(p3.grid).toy >= 2 && !cnt(p3.grid).forest, '淨係玩 3 次 → 玩具房（冇森林）', cnt(p3.grid));
  ok(await E(() => !!document.querySelector('#l6cov [data-ph="6c:tile_toy"]')), 'placeholder：6c:tile_toy');
  await W(1400); await click('l6c-wake'); await W(1600); q = await Q(); ok(q.endWhy === 'wake' && (await vis('l6c-sum')), '撳「醒返」→ 小結');
  await click('l6c-sum-ok'); await W(300);

  console.log('# 蛋／細佬主養');
  await E(() => { __glimmer.state.stage = 'egg'; __qa.l6c.railTick(); }); q = await Q(); ok(q.why === 'egg' && !q.rail, '蛋 → 冇夢');
  await E(() => { const s = __glimmer.state; s.stage = 'adult'; s.fam = s.fam || {}; s.fam.km = true; Glimmer.long6c.resetNight(s); __qa.l6c.railTick(); }); q = await Q(); ok(q.why === 'km', '細佬主養 → 冇夢', [q.why, await E(() => [__glimmer.state.stage, JSON.stringify(__glimmer.state.fam && __glimmer.state.fam.km), __glimmer.state.sleeping])]);
  await E(() => { __glimmer.state.fam.km = false; });

  console.log('# 🛠 開發者模式「6c」');
  await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(400);
  ok(await page.locator('[data-testid=dev-sec-l6c]').isVisible(), '分組「6c（夢境探險）」喺開發者模式');
  await hitOk('6c 掣', '[data-testid^=dev-l6c-]', 12);
  await page.locator('[data-testid=dev-sec-l6c]').scrollIntoViewIfNeeded(); await readOk('開發者「6c」', '[data-testid=dev-sec-l6c]');
  await page.locator('[data-testid=dev-sec-l6c]').scrollIntoViewIfNeeded(); await W(200); await shot('05-dev');
  const dclick = async (k) => { if (!(await page.locator('[data-testid=dev-sec-l6c]').isVisible().catch(() => false))) { await closeModals(); await page.locator('[data-testid=dev-btn]').click(); await W(400); } await page.locator('[data-testid=dev-l6c-' + k + ']').scrollIntoViewIfNeeded(); await page.locator('[data-testid=dev-l6c-' + k + ']').click(); await W(150); };
  await dclick('reset'); q = await Q(); ok(q.cards === 0 && q.n.frags === 0, '「重設 6c」→ 清晒');
  await dclick('theme'); q = await Q(); ok(q.byTh.forest === 5 && q.furn.forest === 'sv_mushroom' && (await E(() => !!Glimmer.long5a.st(__glimmer.state).sv.sv_mushroom)), '「砌齊蘑菇森林」→ 5 張＋送「細蘑菇」擺設', { by: q.byTh, furn: q.furn });
  await dclick('all'); q = await Q(); ok(q.cards === 20, '「夢圖鑑全開」→ 20 張');
  await dclick('dex'); await W(300); ok((await Q()).dex, '「睇夢圖鑑」');
  ok(await E(() => document.querySelectorAll('#l6cdex .card6[data-have="1"]').length === 20), '20 張都有');
  await click('l6c-card-s3'); await W(150); ok((await E(() => document.querySelector('[data-testid=l6c-dex-detail]').textContent)).includes('月亮韆鞦'), '撳卡 → 卡名');
  await readOk('夢圖鑑（全開）', '#l6cdex'); await shot('04-dex-full'); await click('l6c-dex-close'); await W(200);
  await dclick('night'); await dclick('again'); await dclick('enter'); await W(300); q = await Q(); ok(q.on, '「設夜晚」＋「今晚可以再入夢」＋「入夢」→ 入到');
  await E(() => __qa.l6c.finish()); await dclick('force'); await W(300); q = await Q(); ok(q.on, '「入夢（唔理時間）」→ 入到');
  await E(() => __qa.l6c.finish());
  ok(!(await E(() => [...document.querySelectorAll('[data-testid^=s2-set],[data-testid^=toggle-]')].some(e => /6c|入夢|夢境/.test(e.textContent)))), '試玩掣唔喺設定');

  console.log('# 6b.2 風格：面板／字級／用途句／一次性提示');
  await fresh(); await E(() => __qa.l6c.start('qa')); await W(1400);
  const sty = await E(() => { const TY = () => { const ui = document.getElementById('ui'), u63 = ui.classList.contains('u63'), v3 = ui.classList.contains('v3'); const f = u63 ? Math.min(1, Math.round((ui.getBoundingClientRect().width / (ui.offsetWidth || 390) || 1) * 100) / 100) : 1; const B = u63 ? Math.max(16, Math.ceil(14 / f * 10) / 10) : 18, A = u63 ? Math.max(14, Math.ceil(14 / f * 10) / 10) : 16; return { u63, v3, T: u63 ? 20 : 24, TF: v3 ? 'v3' : 'fp', B: +B.toFixed(1), A: +A.toFixed(1) }; }; const EF = (e) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth, r = e.getBoundingClientRect(); return +(parseFloat(getComputedStyle(e).fontSize) * (r.width / (e.offsetWidth || 1)) / k).toFixed(1); }; const fs = (tid) => { const e = document.querySelector('[data-testid=' + tid + ']'); if (!e) return null; const c = getComputedStyle(e); return [EF(e), /GlimmerFP12/.test(c.fontFamily) ? 'fp' : /GlimmerV3/.test(c.fontFamily) ? 'v3' : 'sans']; };
    return { t: fs('l6c-title'), time: fs('l6c-time'), hint: fs('l6c-hint'), wake: fs('l6c-wake'), sub: [...document.querySelectorAll('#l6cov > [data-testid=u62-sub]')].map(e => e.textContent), u62: document.getElementById('ui').classList.contains('u62'), ...TY() }; });
  ok(sty.u62 && NR(sty.t[0], sty.T) && sty.t[1] === sty.TF && NR(sty.wake[0], sty.T) && NR(sty.time[0], sty.B) && sty.time[1] !== 'fp' && NR(sty.hint[0], sty.A), '字級：標題／掣 ' + (sty.u63 ? '有效 20' : 'FP12 24') + '、內文 ' + sty.B + '、輔助 ' + sty.A + '（6b.3 縮細／V3 字）', sty);
  ok(sty.sub.length === 1 && sty.sub[0] === (await E(() => Glimmer.ui62.SUB['夢境'])), '夢境有一句用途（＝ui62 SUB）', sty.sub);
  await E(() => __qa.l6c.end('wake')); await W(1600);
  const sm = await E(() => { const EF = (e) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth, r = e.getBoundingClientRect(); return +(parseFloat(getComputedStyle(e).fontSize) * (r.width / (e.offsetWidth || 1)) / k).toFixed(1); }, TY = () => { const ui = document.getElementById('ui'), u63 = ui.classList.contains('u63'), v3 = ui.classList.contains('v3'); const f = u63 ? Math.min(1, Math.round((ui.getBoundingClientRect().width / (ui.offsetWidth || 390) || 1) * 100) / 100) : 1; const B = u63 ? Math.max(16, Math.ceil(14 / f * 10) / 10) : 18, A = u63 ? Math.max(14, Math.ceil(14 / f * 10) / 10) : 16; return { u63, v3, T: u63 ? 20 : 24, TF: v3 ? 'v3' : 'fp', B: +B.toFixed(1), A: +A.toFixed(1) }; }; const b = document.querySelector('[data-testid=l6c-sum]'), c = getComputedStyle(b); return { pan: b.classList.contains('u62pan'), bc: c.borderTopColor, bw: c.borderTopWidth, sub: !!b.querySelector(':scope > [data-testid=u62-sub]'), line: EF(document.querySelector('[data-testid=l6c-sum-got]')), note: EF(document.querySelector('[data-testid=l6c-sum-note]')), ...TY() }; });
  ok(sm.pan && sm.bw === '1px' && /rgba\(232, 194, 122/.test(sm.bc) && sm.sub && NR(sm.line, sm.B) && NR(sm.note, sm.A), '小結：金邊半透明面板＋用途句＋內文 ' + sm.B + '／輔助 ' + sm.A, sm);
  await click('l6c-sum-dexbtn'); await W(500);
  const dx = await E(() => { const EF = (e) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth, r = e.getBoundingClientRect(); return +(parseFloat(getComputedStyle(e).fontSize) * (r.width / (e.offsetWidth || 1)) / k).toFixed(1); }, TY = () => { const ui = document.getElementById('ui'), u63 = ui.classList.contains('u63'), v3 = ui.classList.contains('v3'); const f = u63 ? Math.min(1, Math.round((ui.getBoundingClientRect().width / (ui.offsetWidth || 390) || 1) * 100) / 100) : 1; const B = u63 ? Math.max(16, Math.ceil(14 / f * 10) / 10) : 18, A = u63 ? Math.max(14, Math.ceil(14 / f * 10) / 10) : 16; return { u63, v3, T: u63 ? 20 : 24, TF: v3 ? 'v3' : 'fp', B: +B.toFixed(1), A: +A.toFixed(1) }; }; const p = document.querySelector('[data-testid=l6c-dex-panel]'); return { pan: p.classList.contains('u62pan'), sub: !!p.querySelector(':scope > [data-testid=u62-sub]'), th: EF(document.querySelector('[data-testid=l6c-dex-th-forest]')), det: EF(document.querySelector('[data-testid=l6c-dex-detail]')), ...TY() }; });
  ok(dx.pan && dx.sub && NR(dx.th, dx.T) && NR(dx.det, dx.B), '夢圖鑑：金邊面板＋用途句＋分組標題 ' + dx.T + '／內文 ' + dx.B, dx);
  await click('l6c-dex-close'); await W(300);
  // 一次性提示（?tips62=1）：第一次入夢先出；開住時夢嘅時間停
  await fresh(QS + '&tips62=1'); await E(() => { document.getElementById('u62tip') && document.getElementById('u62tip').remove(); }); await click('l6c-rail'); await W(2600);
  const tp = await E(() => { const t = document.getElementById('u62tip'); return t ? { k: t.dataset.k, r: t.getBoundingClientRect().right, W: document.getElementById('ui').getBoundingClientRect().right } : null; });
  ok(tp && tp.k === 'dream', '第一次入夢 → 小提示「夢境」', tp);
  const l0 = (await Q()).left; await W(1500); const l1 = (await Q()).left; ok(Math.abs(l1 - l0) < 0.35, '提示開住 → 夢嘅時間停', { l0, l1 });
  await page.screenshot({ path: SHOTS + '6c-06-first-tip.png' });
  await click('u62-tip-ok'); await W(300); await E(() => __qa.l6c.finish());
  await E(() => { Glimmer.long6c.resetNight(__glimmer.state); __glimmer.state.sleeping = true; __qa.l6c.start('qa'); }); await W(2200);
  ok(await E(() => !document.getElementById('u62tip')), '第二次入夢唔再出提示'); await E(() => __qa.l6c.finish());

  console.log('# 重疊檢查 360／390／412（rail、工作 rail、夢境、提示、小結、夢圖鑑）');
  for (const vp of [[360, 640], [390, 844], [412, 915]]) {
    const c2 = await browser.newContext({ viewport: { width: vp[0], height: vp[1] } }); const pg = await c2.newPage(); const E2 = (f, a) => pg.evaluate(f, a), W2 = (ms) => pg.waitForTimeout(ms);
    pg.on('pageerror', e => errs.push('pageerror: ' + e.message));
    await pg.goto(BASE + '?' + QS); await E2(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await pg.goto(BASE + '?' + QS);
    await pg.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await E2(() => __glimmer.liveLoad); await E2(() => __glimmer.houseLoad).catch(() => { }); await E2(() => __glimmer.s2Load).catch(() => { });
    await E2(() => { const s = __glimmer.state, M6 = Glimmer.long6a, t = __glimmer.now(); s.stage = 'adult'; s.form = 'moon'; s.poops = 0; Object.assign(s.needs, { mood: 70, energy: 20, hunger: 80, clean: 100 }); s.sleeping = true; for (let i = 0; i < 3; i++) M6.note(s, 'food', 'meal', 0, 0, 0, t); M6.note(s, 'care', 'rinse', 0, 0, 0, t); M6.note(s, 'care', 'play', 0, 0, 0, t); M6.note(s, 'care', 'play', 0, 0, 0, t); });
    await W2(1300); const tag = vp.join('x');
    for (const pgn of ['night', 'fam', 'dream', 'tip', 'sum', 'dex']) {
      await E2(() => { const t = document.getElementById('u62tip'); if (t) t.remove(); const b = document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]'); if (b) b.click(); try { __glimmer.nq.clear(); } catch (e) { } const s = __glimmer.state; s.sleeping = true; s.needs.energy = 20; }); await W2(300);
      await E2((p) => { const L = __qa.l6c; if (p === 'night') { L.finish(); L.closeDex(); L.railTick(); }
        else if (p === 'fam') { L.finish(); L.closeDex(); __qa.l5b.dev().items.find(i => i.k === 'prep').run(); try { __qa.house.close(); } catch (e) { } __glimmer.state.sleeping = true; __glimmer.state.needs.energy = 20; Glimmer.long6c.resetNight(__glimmer.state); }
        else if (p === 'dream') { L.finish(); L.closeDex(); Glimmer.long6c.resetNight(__glimmer.state); L.start('qa', true); }
        else if (p === 'tip') { if (!L.st().on) L.start('qa', true); __qa.ui62.showTip('dream', true); const n = document.getElementById('u62tip'); if (n) n.dataset.force = '1'; }
        else if (p === 'sum') { if (!L.st().on) L.start('qa', true); L.skip(30); for (const f of L.plan().frags.slice(0, 3)) L.walkTo(f.tile); L.end('wake'); }
        else if (p === 'dex') { L.finish(); L.openDex('qa'); } }, pgn);
      await W2(pgn === 'sum' ? 1900 : pgn === 'fam' ? 2200 : 1500);
      if (pgn === 'night' || pgn === 'fam') { await E2(() => { __qa.l6c.railTick(); try { __qa.work62.rail(); } catch (e) { } }); await W2(1200); }
      const o = await E2(() => { const o = __qa.ui62.overlap(); return { n: o.n, hits: o.hits, names: o.names, rail: !!document.getElementById('l6cbtn') && getComputedStyle(document.getElementById('l6cbtn')).display !== 'none' }; });
      const need = { night: ['#l6cbtn'], fam: ['#l6cbtn', '#u62workbtn'], dream: ['[l6c-wake]', '[l6c-time]'], tip: ['#u62tip'], sum: ['[l6c-sum]'], dex: ['[l6c-dex-panel]'] }[pgn];
      ok(o.hits.length === 0 && need.every(k => o.names.some(nm => nm.indexOf(k) >= 0)), tag + ' ' + pgn + '：' + o.n + ' 個框冇重疊', { hits: o.hits.slice(0, 4), miss: need.filter(k => !o.names.some(nm => nm.indexOf(k) >= 0)) });
      await pg.screenshot({ path: SHOTS + '6c-ov-' + tag + '-' + pgn + '.png' });
    }
    await c2.close();
  }

  console.log('# ?l6c=0');
  await fresh('q=high&seed=21&ev=0&hour=22&l6c=0'); await W(800);
  ok(await E(() => !window.__qa.l6c && !__glimmer.l6c && !document.getElementById('l6cbtn')), '?l6c=0：冇裝、冇「入夢」掣');
  ok(await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l6c') && !__glimmer.state.dream6), '?l6c=0：冇「6c」分組、冇 6c 資料');

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
