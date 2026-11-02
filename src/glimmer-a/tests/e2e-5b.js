/* 《微光小圃》 e2e-5b — 第 5 批 5b 遠足＋小職業（遊策 5a–5c spec §5b＋遊美 art/series2_long/5b）：
   屋仔「今日安排」掣、每日安排（遠足／工作／休息三段、鎖住原因）、遠足（只限靜光團絨＋S6 細佬、每日 2 次、24 小時／第二日開機返）、
   出發／返屋動畫＋頭頂手信、返屋 toast → 團絨日記、揀工作 2×2（Lv／+n 碎／家族 Lv7 開 Lv6）、工作帽、升級、守夜貼紙、每日 12 碎上限、
   字清晰度（FP12 24px、對比 ≥4.5）、🛠「5b」、存檔、?l5b=0。截圖 360×780 DPR3 → SHOTS（5b-*.png）。
   node tests/e2e-5b.js（BASE 預設 http://localhost:8240/index.html） */
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
const T0 = new Date(2026, 10, 2, 13, 0).getTime(), H = 3600e3, DAY = 86400e3;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '5b-' + n + '.png' });
  const Q = () => E(() => __qa.l5b.st());
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').first().isVisible().catch(() => false);
  const click = (tid) => page.locator('[data-testid=' + tid + ']').first().click();
  const txt = (tid) => page.locator('[data-testid=' + tid + ']').first().innerText().catch(() => '');
  const prep = () => E(() => { window.__noSaveOnHide = true; const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 50, energy: 100, hunger: 100, clean: 100 }); s.poops = 0; });
  const hookToast = () => E(() => { window.__toasts = []; const U = Glimmer.ui, t = U.toast; if (U._h5b) return; U._h5b = 1; U.toast = function (m) { window.__toasts.push(String(m)); return t.apply(this, arguments); }; });
  const toasts = () => E(() => window.__toasts.slice());
  const load = async (qs, clear) => {
    if (clear !== false) { await page.goto(BASE + '?' + qs); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); }
    await page.goto(BASE + '?' + qs); await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad);
    await E(() => __glimmer.s2Load); await E(() => __glimmer.houseLoad); await E(() => __glimmer.l5bLoad).catch(() => { }); await setT(T0); if (clear !== false) await prep(); await hookToast(); await W(400);
  };
  const devRun = (k) => E((k) => __qa.l5b.dev().items.find(i => i.k === k).run(), k);
  const rows = () => E(() => __qa.l5b.rows());
  const wallet = () => E(() => Glimmer.sys12.st(__glimmer.state).wallet.total);
  const readOk = async (name, sel) => { const a = await audit(page, sel); ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（FP12 24px、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); };

  // 5b.1：熱區 ≥48（同 e2e-5a2：48×48 四角＋四邊都要打中自己）
  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0, miss = [];
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; else miss.push(dx + ',' + dy + '→' + (t ? (t.dataset.testid || t.id || t.className || t.tagName) : '-')); }
        return { id: e.dataset.testid || e.id, n, miss: miss.slice(0, 2), lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1), label + '：搵到 ' + L.length + ' 個');
    const bad = L.filter(x => x.n < 8); ok(bad.length === 0, label + '：熱區 ≥48' + (bad.length ? ' ← ' + JSON.stringify(bad.slice(0, 3)) : '（' + L.slice(0, 3).map(x => x.id + ' ' + x.lay.join('×')).join('，') + '）')); };
  console.log('# 載入');
  await load('q=high&hour=13&seed=21&ev=0');
  ok(await E(() => !!(Glimmer.long5b && Glimmer.long5bui && window.__qa && __qa.l5b && __glimmer.h5x)), 'long5b＋long5bui 裝咗');
  ok(await E(() => Glimmer.data.PARAMS.series2.version === '5c'), '版本 5b');
  ok(await E(() => Glimmer.long5b.isOn() && !!Glimmer.long5a.LIVE.job_cap_plus1), '5b 開咗（job_cap_plus1 轉 LIVE）');
  ok((await Q()).json, 'long_5b.json 載入');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l5b' && s.title.includes('5b'))), '🛠 開發者模式有「5b」分組');
  ok(await E(() => !document.querySelector('#mbox [data-testid^=l5b]')), '設定冇 5b 測試掣');

  console.log('# 屋仔「今日安排」');
  ok(!(await vis('l5b-hud')), '未有成年住客 → 冇「今日安排」掣');
  let r = await devRun('prep'); ok(r.ok, '準備 3 隻住客＋開屋', r); await W(900);
  ok(await vis('l5b-hud'), '屋仔有「今日安排」掣'); ok((await txt('l5b-hud-label')).includes('安排'), '掣寫「安排」');
  ok(await vis('l5b-hud-dot'), '有未揀嘅住客 → 紅點');
  await click('l5b-hud'); await W(500);
  ok((await Q()).ov === 'plan', '撳掣 → 每日安排'); ok((await txt('l5b-plan-title')).includes('今日安排'), '標題「今日安排」');
  ok((await txt('l5b-chip-ex')).includes('遠足 0/2'), 'chip「遠足 0/2」'); ok(/今日 \d+\/12 碎/.test(await txt('l5b-chip-sh')), 'chip「今日 n/12 碎」');
  let R = await rows(); ok(R.length === 3, '3 行住客', R.length);
  const tr = R.find(x => x.kind === 'tr' && x.hike), kid = R.find(x => x.kind === 'kid'), tr2 = R.find(x => x.kind === 'tr' && x.hike && x.id !== tr.id);
  ok(tr && kid && tr2, '有靜光團絨 ×2＋S6 細佬');
  ok(await vis('l5b-seg-expedition-' + tr.id) && await vis('l5b-seg-job-' + tr.id) && await vis('l5b-seg-rest-' + tr.id), '三段：遠足／工作／休息');
  ok((await txt('l5b-st-' + tr.id)).includes('未揀'), '狀態「未揀」');
  await readOk('每日安排', '#l5bov');
  await hitOk('5b.1 三段掣', '#l5bov .l5bseg', 9); await hitOk('5b.1 「好！」＋閂', '[data-testid=l5b-ok],#l5bov [data-testid$=-close]', 2);
  await shot('plan');

  console.log('# 遠足');
  await click('l5b-seg-expedition-' + tr.id); await W(300);
  let q = await Q(); ok(q.away.includes(tr.id) && q.ex === 1, '撳「遠足」→ 出發（1/2）', q);
  ok(q.anims.includes(tr.id), '出發動畫（depart）');
  ok((await txt('l5b-chip-ex')).includes('遠足 1/2'), 'chip 變「遠足 1/2」');
  ok(/遠足中・仲有 2[34]:\d\d/.test(await txt('l5b-st-' + tr.id)), '狀態「遠足中・仲有 hh:mm」', await txt('l5b-st-' + tr.id));
  ok(await E((id) => document.querySelector('[data-testid=l5b-seg-job-' + id + ']').dataset.lk === '1', tr.id), '遠足中工作鎖住');
  await E(() => __qa.l5b.close()); await W(1800);
  q = await Q(); ok(!q.anims.includes(tr.id) && q.stat.anims > 0, '出發動畫播完（10 格）');
  ok(await E((id) => !__glimmer.house5.actors().some(a => a.id === id), tr.id), '遠足中嘅唔喺屋入面');
  r = await E((id) => __qa.l5b.choose(id, 'expedition'), tr.id); ok(!r.ok && r.reason === 'away', '遠足中再揀 → away');
  r = await E((id) => __qa.l5b.choose(id, 'expedition'), kid.id); ok(r.ok, 'S6 細佬都去得遠足');
  q = await Q(); ok(q.ex === 2, '今日 2/2');
  r = await E((id) => __qa.l5b.choose(id, 'expedition'), tr2.id); ok(!r.ok && r.reason === 'full', '第 3 次 → 今日滿咗', r);
  ok(await E(() => { const s = __glimmer.state, B = Glimmer.long5b; return !B.canHike({ kind: 'tr', fk: 'sprout' }) && !B.canHike({ kind: 'kid', fk: 'A2' }) && B.canHike({ kind: 'kid', fk: 'H3' }) && B.canHike({ kind: 'tr', fk: 'evo_still_moon' }); }), '遠足只限靜光團絨＋S6 細佬（S5 唔得）');
  const w0 = await wallet();
  await setT(T0 + 24 * H + 60e3); await E(() => __qa.l5b.tick()); await W(400);
  q = await Q(); ok(q.away.length === 0 && q.trips === 2, '24 小時後返屋（2 篇日記）', q);
  const tr0 = await E(() => __qa.l5b.raw().trips[0]);
  ok(tr0.sh >= 5 && tr0.sh <= 10 && tr0.lines.length === 3 && /^H[1-4]$/.test(tr0.scene), '帶返 5–10 碎＋3 行故事＋場景', tr0);
  ok((await wallet()) > w0, '碎入銀包');
  ok(q.q === 2 && !(await Q()).toast, '?ev=0 唔自動彈 toast（排隊 2 個）');
  ok(await E(() => __glimmer.house5.actors().some(a => a.id === __qa.l5b.raw().trips[0].id)), '返屋後喺屋入面');
  await E(() => { const o = Glimmer.long5b.st(__glimmer.state); __qa.l5b.toast(o.q.shift()); }); await W(500);
  ok(await vis('l5b-toast'), '返屋 toast'); await readOk('返屋 toast', '#l5btoast');
  await shot('toast');
  await click('l5b-toast'); await W(600);
  ok((await Q()).ov === 'diary', '撳 toast → 團絨日記');
  ok((await txt('l5b-diary-title')).includes('團絨日記'), '標題「團絨日記」');
  ok(/第 \d+ 日・.+嘅遠足/.test(await txt('l5b-diary-date')), '日期行「第 n 日・名嘅遠足」', await txt('l5b-diary-date'));
  ok((await txt('l5b-diary-l0')).includes('行到'), '故事 3 行'); ok(/\d \/ 2/.test(await txt('l5b-diary-n')), '頁數「n / 2」');
  ok((await txt('l5b-diary-sh')).startsWith('+'), '碎 chip');
  ok(await E(() => { const c = document.querySelector('[data-testid=l5b-diary-pic]'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i]) n++; return n > c.width * c.height * 0.9; }), '日記圖（場景＋返屋格＋手信）');
  await readOk('團絨日記', '#l5bov');
  await shot('diary');
  await hitOk('5b.1 日記揭頁', '[data-testid=l5b-diary-prev],[data-testid=l5b-diary-next]', 2);
  await click('l5b-diary-prev'); await W(300); ok((await Q()).ovData.ix === 0, '◀ 上一篇');
  await E(() => __qa.l5b.close());

  console.log('# 返屋動畫＋手信');
  await setT(T0 + 2 * DAY); await E(() => { Glimmer.long5b.devNewDay(__glimmer.state, __glimmer.now()); });
  const t2 = await E(() => __qa.l5b.rows().find(x => x.hike && !x.lock.expedition && x.room === __glimmer.house5.room()));
  r = await E((id) => __qa.l5b.choose(id, 'expedition'), t2.id); ok(r.ok, '再出發'); await W(1600);
  await E(() => __qa.l5b.back()); await W(800);
  q = await Q(); ok(q.stat.sv > 0, '返屋動畫：手信喺頭頂（格 5–9）'); await shot('return');
  await W(800);

  console.log('# 工作');
  await setT(T0 + 3 * DAY); await E(() => __qa.l5b.tick()); await E(() => __qa.l5b.plan()); await W(400);
  R = await rows(); const j1 = R.find(x => !x.away);
  await click('l5b-seg-job-' + j1.id); await W(400);
  ok((await Q()).ov === 'jobs', '撳「工作」→ 揀工作'); ok((await txt('l5b-jobs-title')).includes('揀工作'), '標題「揀工作」');
  for (const j of ['post', 'garden', 'watch', 'chef']) ok(await vis('l5b-job-' + j), '2×2 卡：' + j);
  ok((await txt('l5b-job-post')).includes('未做過') && (await txt('l5b-job-pay-post')).includes('+2 碎/日'), '未做過＋「+2 碎/日」');
  await readOk('揀工作', '#l5bov');
  await shot('jobs');
  const wj = await wallet(); await click('l5b-job-post'); await W(500);
  q = await Q(); ok(q.plan[j1.id] && q.plan[j1.id].job === 'post', '揀咗郵差助手'); ok((await wallet()) === wj + 2, 'Lv1 即日 +2 碎');
  ok((await Q()).ov === 'plan' && (await txt('l5b-st-' + j1.id)).includes('郵差助手 Lv1'), '返每日安排：「郵差助手 Lv1・再做 4 日升級」', await txt('l5b-st-' + j1.id));
  await E(() => __qa.l5b.close());
  r = await devRun('hats'); ok(r.ok, '全部住客返工', r); await W(1200);
  q = await Q(); ok(q.stat.hats > 0, '工作帽畫咗（' + q.stat.hats + '）');
  await shot('hats');
  r = await devRun('days5'); await W(200); R = await rows(); ok(R.filter(x => x.info).every(x => x.info.lv >= 2), '+5 日 → Lv2', R.map(x => x.info && x.info.lv));
  r = await devRun('lv5'); R = await rows(); const capped = R.find(x => x.info); ok(capped.info.lv === 5 && capped.info.lv6Locked, 'Lv5 封頂（家族 Lv7 開 Lv6）');
  await E((id) => __qa.l5b.jobs(id), capped.id); await W(300); ok((await txt('l5b-job-pay-' + capped.job)).includes('家族 Lv7 開 Lv6'), '卡寫「家族 Lv7 開 Lv6」'); await E(() => __qa.l5b.close());
  r = await devRun('fam7'); R = await rows(); ok(R.find(x => x.id === capped.id).info.lv === 6, '家族 Lv7 → Lv6', r);
  // 守夜：日頭唔出糧，夜晚出糧＋貼紙
  await setT(T0 + 4 * DAY); await E(() => { Glimmer.long5b.devNewDay(__glimmer.state, __glimmer.now()); __qa.l5b.tick(); });
  const watcher = await E(() => { const o = Glimmer.long5b.st(__glimmer.state); return Object.keys(o.plan).find(k => o.plan[k].job === 'watch'); });
  ok(watcher && !(await E((id) => Glimmer.long5b.today(__glimmer.state, __glimmer.now()).paid[id], watcher)), '守夜：日頭未出糧');
  const st0 = (await Q()).stk.length; r = await devRun('night'); ok(r.ok && (await Q()).stk.length === st0 + 1, '夜晚出糧＋1 張夢泡泡貼紙', r);
  // 上限 12
  ok((await Q()).sh <= 12, '每日 ≤12 碎');

  console.log('# 存檔');
  const before = await E(() => JSON.stringify(Glimmer.long5b.summary(__glimmer.state, __glimmer.now())));
  await E(() => __glimmer.save()); await load('q=high&hour=13&seed=21&ev=0', false); await setT(T0 + 4 * DAY);
  const after = await E(() => JSON.stringify(Glimmer.long5b.summary(__glimmer.state, __glimmer.now()))); ok(JSON.parse(before).trips === JSON.parse(after).trips && JSON.stringify(JSON.parse(before).jobs) === JSON.stringify(JSON.parse(after).jobs), '重開：日記／工作日數保留', [before, after]);

  console.log('# 🛠 5b 分組');
  const ks = await E(() => __qa.l5b.dev().items.map(i => i.k)); for (const k of ['prep', 'plan', 'hike', 'back', 'job', 'hats', 'days5', 'lv5', 'fam7', 'night', 'diary', 'toast', 'newday', 'reset']) ok(ks.includes(k), '5b 掣：' + k);
  r = await devRun('reset'); ok(r.ok && (await Q()).trips === 0, '重設 5b');

  console.log('# ?l5b=0');
  await load('q=high&hour=13&seed=21&ev=0&l5b=0');
  ok(await E(() => !(window.__qa && __qa.l5b) && !Glimmer.long5b.isOn() && !Glimmer.long5a.LIVE.job_cap_plus1), '?l5b=0：5b 全停');
  ok(await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l5b')), '?l5b=0：冇 5b 分組');
  ok(await E(() => Glimmer.long5b.choose(__glimmer.state, 'x', 'rest').reason === 'off'), '?l5b=0：choose → off');
  ok(await E(() => !!(window.__qa && __qa.l5)), '?l5b=0：5a 照用');

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
