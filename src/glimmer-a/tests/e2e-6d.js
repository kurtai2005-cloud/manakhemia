/* 《微光小圃》 e2e-6d — 第 6 批 6d「朋友碼／影子探訪／交換蛋碼」（遊策 breakthrough-6a6d-spec §6d）：
   我嘅名片（分享圖 495×756＋QR，揀相解返）；入朋友碼（貼上／揀相 → 校驗 OK 預覽 → 請佢嚟玩）；重複／自己／每日 3 個／改壞碼；
   花園影子（三階紫剪影＋整隻 globalAlpha 0.45 半透明，唔用棋盤；friend_badge、互動泡泡、撳開資料、早啲送走＋手信 ≤3）；24 粒鐘到時走；
   家族 Lv4 先出蛋碼、每 7 日 1 個；收蛋碼 → 5c 細佬蛋用朋友嘅色；🛠「6d」；?l6d=0；?l6dart=0 placeholder；
   字清晰度（只審 ≥12px node）、熱區 ≥48、360／390／412／768 冇重疊。日子用 page.clock 定死。node tests/e2e-6d.js */
const path = require('path'), fs = require('fs');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const { audit } = require('./readaudit');
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
fs.mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };
const T0 = new Date('2026-11-02T14:00:00+08:00').getTime(), HOUR = 3600e3, DAY = 24 * HOUR;

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  const page = await ctx.newPage(); await page.clock.install({ time: T0 });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.type() + ': ' + m.text() + ' ' + ((m.location() || {}).url || '')); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '6d-' + n + '.png' });
  const Q = () => E(() => __qa.l6d.st());
  const QS = 'q=high&seed=21&ev=0&hour=14';
  const setT = (t) => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, t);
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load).catch(() => { }); await E(() => __glimmer.houseLoad).catch(() => { }); };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) break; await E(() => { const b = document.querySelector('[data-testid=dev-close]') || document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]') || [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(250); } await E(() => { const t = document.getElementById('u62tip'); if (t) t.remove(); }); };
  const prep = () => E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; const s = __glimmer.state; s.stage = 'adult'; s.form = 'moon'; s.poops = 0; s.sleeping = false; Object.assign(s.needs, { mood: 70, energy: 90, hunger: 80, clean: 100 }); if (s.share6 && Glimmer.long6d) Glimmer.long6d.reset(s); __glimmer.save && __glimmer.save(); }, T0);
  const fresh = async (qs) => { await page.goto(BASE + '?' + (qs || QS)); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + (qs || QS)); await ready(); await prep(); await W(1300); await closeModals(); await W(400); };
  const click = (tid) => page.locator('[data-testid=' + tid + ']').first().click();
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').first().isVisible().catch(() => false);
  const D = (k) => E((k) => __qa.l6d.dev().items.find(i => i.k === k).run(), k);
  const fontOn = async (sel) => {
    try { await page.evaluate(() => (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve()); } catch (e) { }
    const r = await page.waitForFunction((sel) => {
      try {
        if (document.fonts && document.fonts.status && document.fonts.status !== 'loaded') return false;
        const nodes = [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; });
        if (!nodes.length) return false;
        const v3 = !!(window.__glimmer && __glimmer.v3 && __glimmer.v3.want);
        const want = v3 ? 'GlimmerV3Sans' : 'GlimmerFP12';
        return nodes.some(e => {
          const cs = getComputedStyle(e), fam = cs.fontFamily || '', size = parseFloat(cs.fontSize) || 0;
          return fam.indexOf(want) >= 0 && size >= 12;
        });
      } catch (e) { return false; }
    }, sel, { timeout: 8000 }).then(() => true).catch(() => false);
    return r;
  };
  const readOk = async (name, sel) => {
    const on = await fontOn(sel);
    if (!on) { ok(false, name + '：等 document.fonts.ready 後仍未見到目標字型', sel); return; }
    const a = await audit(page, sel, { skipBelow: 12, minEff: 12 });
    ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（只審 ≥12px；FP12 24px／V3、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam]));
  };
  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0;
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; }
        return { id: e.dataset.testid || e.id, n, lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1) && L.every(x => x.n === 8), label + ' 熱區 ≥48（' + L.length + ' 個）', L.filter(x => x.n < 8).slice(0, 3)); };

  console.log('# 載入＋rail「朋友」');
  await fresh();
  ok(await E(() => !!(Glimmer.long6d && Glimmer.long6dui && Glimmer.qrlib && window.__qa && __qa.l6d && __glimmer.l6d)), 'long6d＋long6dui＋qrlib 裝咗');
  ok(await E(() => Glimmer.data.PARAMS.series2.version === '6d'), '版本 6d');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l6d' && s.title.includes('6d'))), '🛠 開發者模式有「6d」分組');
  await E(() => __qa.l6d.railTick()); await W(300);
  let q = await Q(); ok(q.rail && await E(() => document.querySelector('#l6dbtn i.l').textContent === '朋友'), 'rail「朋友」', q.rail);
  await hitOk('rail「朋友」', '[data-testid=l6d-rail]');
  ok(await E(() => __qa.l6d.artLoad()), '6d 美術 manifest 載入'); await W(400);
  q = await Q(); ok(q.art && q.artErr.length === 0, '冇美術錯', { err: q.artErr });
  await shot('01-garden-rail');

  console.log('# 朋友面板');
  await click('l6d-rail'); await W(500); q = await Q();
  ok(q.ov && q.tab === 'main', '撳「朋友」→ 開面板');
  ok(await E(() => document.querySelector('[data-testid=l6d-today]').textContent.includes('0／3')), '今日請咗 0／3');
  ok(await vis('l6d-tab-card') && await vis('l6d-tab-enter') && await vis('l6d-tab-egg') && await vis('l6d-tab-book'), '4 粒：名片／入碼／蛋碼／朋友簿');
  await hitOk('面板掣', '#l6dov .b6', 4); await readOk('主面板', '#l6dov');
  await shot('02-main');

  console.log('# 我嘅名片＋分享圖＋QR');
  await click('l6d-tab-card'); await W(800);
  ok(await vis('l6d-card') && await E(() => !!document.querySelector('#l6dov canvas')), '名片 canvas');
  ok(await vis('l6d-card-copy') && await vis('l6d-card-save') && await vis('l6d-card-share'), '複製／存圖／分享');
  await hitOk('名片掣', '#l6dov .b6', 3); await readOk('名片', '#l6dov');
  await shot('03-card');
  const card = await E(() => __qa.l6d.drawCard(3));
  ok(card.w === 495 && card.h === 756 && card.art && card.qrN >= 21 && card.qrN <= 37 && card.mem >= 1 && card.mem <= 3, '存圖 495×756＋share_card_bg＋QR ' + card.qrN + '×' + card.qrN + '＋' + card.mem + ' 個回憶', { w: card.w, h: card.h, art: card.art, qrN: card.qrN, mem: card.mem });
  const myDec = await E((c) => { const d = Glimmer.long6d.decode(c); return { ok: d.ok, uid: d.ok && d.snap.uid, me: __qa.l6d.st().uid, kind: d.ok && d.snap.kind, len: c.length }; }, card.code);
  ok(myDec.ok && myDec.uid === myDec.me && myDec.kind === 'visit' && myDec.len < 80, '自己個碼校驗 OK（' + myDec.len + ' 字）', myDec);
  const pngPath = '/tmp/e2e6d-card.png'; fs.writeFileSync(pngPath, Buffer.from(card.url.split(',')[1], 'base64'));
  ok(await E(async (u) => { const b = await (await fetch(u)).blob(); const t = await __qa.l6d.decodeFile(b); return Glimmer.long6d.extract(t || ''); }, card.url) === card.code, '存出嚟張圖 → QR 解返同一個碼');
  { const qm = await E((c) => { const M = __qa.l6d.qrMatrix(c); return M && M.length; }, card.code); ok(qm === card.qrN, 'QR 整數 px 模組（' + qm + '）'); }

  console.log('# 入朋友碼：揀相／預覽／請佢嚟');
  await E(() => __qa.l6d.go('enter')); await W(400);
  ok(await vis('l6d-input') && await vis('l6d-paste') && await vis('l6d-photo') && await vis('l6d-check'), '入碼格＋貼上／揀相／睇吓');
  await hitOk('入碼掣', '#l6dov .b6', 3); await readOk('入碼', '#l6dov');
  await page.locator('[data-testid=l6d-file]').setInputFiles(pngPath); await W(1500);
  ok(await E((c) => document.querySelector('[data-testid=l6d-input]').value === c, card.code) && await vis('l6d-pre-ok'), '揀相（名片圖）→ 解到碼、校驗 OK');
  await click('l6d-go'); await W(400); ok(await E(() => { const r = __qa.l6d.last().enter; return r && !r.ok && r.why === 'self'; }) && await vis('l6d-pre-bad'), '自己張名片 → 「請佢嚟玩」唔得（自己）');
  await E(() => { __qa.l6d.setInput('垃圾 GL6Dxxxx'); __qa.l6d.check(); }); await W(200); ok(await vis('l6d-pre-bad'), '亂碼 → 無效');
  const F1 = await E(() => __qa.l6d.fakeCode('visit', { uid: 1111, form: 'soft' }));
  { const bad = F1.slice(0, 12) + (F1[12] === 'A' ? 'B' : 'A') + F1.slice(13); await E((b) => { __qa.l6d.setInput(b); __qa.l6d.check(); }, bad); await W(200);
    ok(await vis('l6d-pre-bad') && !(await vis('l6d-go')), '改咗 1 個字 → 校驗唔過、冇「請佢嚟玩」'); }
  await E((c) => { __qa.l6d.setInput('朋友碼：' + c + ' 快啲嚟！'); __qa.l6d.check(); }, F1); await W(400);
  ok(await vis('l6d-pre-ok') && await vis('l6d-pre-name') && await vis('l6d-go') && await E(() => document.querySelectorAll('[data-testid^=l6d-pre-mem-]').length === 3), '連字貼上都搵到碼 → 校驗 OK：名、Lv、紋、3 個回憶');
  ok(await E(() => { const c = document.querySelector('[data-testid=l6d-pre-shadow]'); return !!c && !c.dataset.ph; }), '預覽有影子剪影');
  await readOk('預覽', '#l6dov'); await shot('04-enter-preview');
  const w0 = await E(() => JSON.stringify({ w: __glimmer.state.sys12 && __glimmer.state.sys12.wallet, b: __glimmer.state.sys12 && __glimmer.state.sys12.bond }));
  await click('l6d-go'); await W(600); q = await Q();
  ok(!q.ov && q.visits.length === 1 && q.today === 1 && q.friends === 1, '請佢嚟玩 → 1 個影子、今日 1／3', { v: q.visits.length, today: q.today });
  ok(await E(() => (__qa.l6d.toasts().slice(-1)[0] || '').includes('嘅影子嚟咗')), '提示「…嘅影子嚟咗！」', await E(() => __qa.l6d.toasts().slice(-2)));
  ok(q.visits[0] && q.visits[0].leftH === 24, '住 24 粒鐘', q.visits[0] && q.visits[0].leftH);
  await W(800); let nd = await E(() => __qa.l6d.nodes());
  ok(nd.length === 1 && nd[0].art === 'shadow:alpha' && !nd[0].ph && nd[0].badge && (await Q()).alpha === 0.45, '花園影子：半透明剪影（alpha 0.45）＋friend_badge', nd);
  const pix = await E(() => { const c = document.querySelector('#l6dlay canvas'); const g = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; const cols = new Set(); let on = 0, adj = 0; const W = c.width, op = +getComputedStyle(c).opacity;
      for (let i = 0, n = 0; i < g.length; i += 4, n++) if (g[i + 3] >= 128) { on++; cols.add(g[i] + ',' + g[i + 1] + ',' + g[i + 2]); const x = n % W, y = (n / W) | 0; if (x + 1 < W && g[(y * W + x + 1) * 4 + 3] >= 128) adj++; }
      return { on, adj, op, cols: [...cols], ok: on > 20 && adj > 0 && Math.abs(op - 0.45) < 0.011 && [...cols].every(c => ['238,226,255', '169,139,240', '92,63,176'].includes(c)) }; }); ok(pix.ok, '影子：3 階紫、相鄰像素齊（唔係格仔）、canvas opacity 0.45', pix);
  await shot('05-garden-shadow');

  console.log('# 規則：重複／自己／每日 3 個');
  let r = await E((c) => Glimmer.long6d.enter(__glimmer.state, c, __glimmer.now(), {}), F1); ok(!r.ok && r.why === 'dup', '同一個碼 24 粒鐘內 → 重複', r.why);
  r = await E(() => Glimmer.long6d.enter(__glimmer.state, Glimmer.long6d.myCode(__glimmer.state, __glimmer.now(), {}).code, __glimmer.now(), {})); ok(!r.ok && r.why === 'self', '自己個碼 → 唔得', r.why);
  r = await E(() => Glimmer.long6d.enter(__glimmer.state, __qa.l6d.fakeCode('visit', { uid: 1111, form: 'tide' }), __glimmer.now(), {})); ok(!r.ok && (r.why === 'here' || r.why === 'friendToday'), '同一個朋友新碼 → 已經喺度', r.why);
  await D('visit'); await D('visit'); q = await Q(); ok(q.today === 3 && q.visits.length === 3, '再嚟 2 個 → 3／3');
  r = await E(() => Glimmer.long6d.enter(__glimmer.state, __qa.l6d.fakeCode('visit'), __glimmer.now(), {})); ok(!r.ok && r.why === 'max', '第 4 個 → 今日滿', r.why);
  await W(1200); nd = await E(() => __qa.l6d.nodes()); ok(nd.length === 3 && nd.every(n => n.art === 'shadow:alpha') && new Set(nd.map(n => n.x)).size === 3, '3 個影子分開企（避開團絨／rail）', nd.map(n => n.x));
  ok(await E((w) => JSON.stringify({ w: __glimmer.state.sys12 && __glimmer.state.sys12.wallet, b: __glimmer.state.sys12 && __glimmer.state.sys12.bond }) === w, w0), '探訪唔郁錢包／親密度');
  await hitOk('影子', '#l6dlay .ht', 3);

  console.log('# 互動＋撳影子＋早啲送走');
  await D('act'); await W(500); ok(await vis('l6d-bubble') && (await E(() => __qa.l6d.log().some(l => l.k === 'act'))), '影子走埋團絨 → 泡泡');
  await shot('06-act');
  const vid = (await Q()).visits[0].id;
  await click('l6d-shadow-hit-' + vid); await W(500);
  ok(await vis('l6d-info-panel') && await vis('l6d-info-bye') && await E(() => document.querySelector('[data-testid=l6d-info-left]').textContent.includes('24')), '撳影子 → 資料（仲有 24 粒鐘）');
  await hitOk('資料掣', '#l6dov .b6', 2); await readOk('影子資料', '#l6dov'); await shot('07-info');
  const sv0 = await E(() => Object.keys(Glimmer.long5a.st(__glimmer.state).sv).length);
  await click('l6d-info-bye'); await W(500); q = await Q();
  ok(q.visits.length === 2 && q.gifts === 1 && !q.info, '送佢返屋企 → 走咗、手信 1', { v: q.visits.length, g: q.gifts });
  ok(await E((n) => Object.keys(Glimmer.long5a.st(__glimmer.state).sv).length === n + 1, sv0), '手信入咗 5a 紀念品（新）');

  console.log('# 24 粒鐘到時走（page.clock＋遊戲鐘）');
  await setT(T0 + 25 * HOUR);
  await E((t) => {
    const ev = Glimmer.long6d.process(__glimmer.state, t);
    if (window.__qa && __qa.l6d && typeof __qa.l6d.layTick === 'function') __qa.l6d.layTick(true);
    return ev && ev.length;
  }, T0 + 25 * HOUR);
  await page.waitForFunction(() => {
    try {
      const st = __qa.l6d.st();
      const gifts = Glimmer.long6d.st(__glimmer.state).n.gifts;
      const shadows = document.querySelectorAll('#l6dlay .sh6').length;
      return st.visits.length === 0 && gifts === 3 && shadows === 0;
    } catch (e) { return false; }
  }, { timeout: 8000 }).catch(() => { });
  q = await Q();
  ok(q.visits.length === 0 && await E(() => document.querySelectorAll('#l6dlay .sh6').length === 0), '過咗 24 粒鐘 → 影子全部走', q.visits.length);
  ok(await E(() => Glimmer.long6d.st(__glimmer.state).n.gifts === 3), '手信合共 3（今日 ≤3）');
  q = await Q(); ok(q.today === 0, '新一日 → 今日 0／3', q.today);
  await D('three'); q = await Q(); ok(q.today === 3 && q.visits.length === 3, '新一日再請 3 個（滿）', q.today);
  await D('expire'); q = await Q(); ok(q.gifts === 3 && q.visits.length === 0, '3 個走 → 手信 3／3', q.gifts);
  await D('newday'); await D('visit'); await D('expire'); q = await Q(); ok(q.gifts <= 3, '手信每日 ≤3', q.gifts);
  await E(() => { __qa.l6d.open('book'); }); await W(400);
  ok(await E(() => document.querySelectorAll('[data-testid^=l6d-book-]:not([data-testid=l6d-book-list]):not([data-testid=l6d-book-none])').length >= 5), '朋友簿有記錄');
  await readOk('朋友簿', '#l6dov'); await shot('08-book'); await E(() => __qa.l6d.close());

  console.log('# 交換蛋碼：Lv4、每 7 日 1 個、5c 用朋友色');
  await E(() => __qa.l6d.open('egg')); await W(400);
  const lv = await E(() => Glimmer.long5a.st(__glimmer.state).lv);
  ok(lv >= 4 ? await vis('l6d-egg-make') : await vis('l6d-egg-lock'), lv >= 4 ? 'Lv' + lv + ' → 可以出蛋碼' : 'Lv' + lv + ' → 鎖住（要 Lv4）');
  await readOk('蛋碼（鎖）', '#l6dov'); await shot('09-egg-lock');
  await D('lv4'); await E(() => __qa.l6d.go('egg')); await W(400); ok(await vis('l6d-egg-make'), 'Lv4 → 「出蛋碼」');
  const tE = await E(() => __glimmer.now()); await click('l6d-egg-make'); await W(800);
  ok(await vis('l6d-egg-left') && await E(() => document.querySelector('[data-testid=l6d-egg-left]').textContent.includes('7')), '出咗蛋碼卡＋再過 7 日');
  const eg = await E(() => __qa.l6d.st().eggOut); ok(eg.why === 'have' && eg.left === 7 && await E((c) => Glimmer.long6d.decode(c).snap.kind === 'egg', eg.code), '蛋碼 kind egg', eg.why);
  await readOk('蛋碼卡', '#l6dov'); await shot('10-egg-card');
  await setT(tE + 4 * DAY); ok(await E(() => __qa.l6d.st().eggOut.left === 3), '過 3 日 → 同一個蛋碼、仲有 3 日');
  await setT(tE + 7 * DAY + 60e3); ok(await E(() => __qa.l6d.st().eggOut.why === 'new'), '過 7 日 → 可以出新');
  await E(() => __qa.l6d.close());
  const FE = await E(() => __qa.l6d.fakeCode('egg', { uid: 2222, pat: 'star', form: 'tide' }));
  await E((c) => { __qa.l6d.open('enter'); __qa.l6d.setInput(c); __qa.l6d.check(); }, FE); await W(400);
  ok(await E(() => document.querySelector('[data-testid=l6d-pre-ok]').textContent.includes('蛋碼') && document.querySelector('[data-testid=l6d-go]').textContent.includes('收蛋碼')), '蛋碼預覽 → 「收蛋碼」');
  await click('l6d-go'); await W(500);
  q = await Q(); ok(q.egg && q.egg.pat === 'star' && !q.egg.used && q.visits.length === 0, '收咗蛋碼（星紋待用、唔係影子）', q.egg);
  ok(await E(() => Glimmer.long5c && typeof Glimmer.long5c.onChoose === 'function'), '5c onChoose hook 有');
  await E(() => __qa.l6d.open('main')); await W(400); ok(await vis('l6d-egg-pend') && await E(() => document.querySelector('[data-testid=l6d-egg-pend]').textContent.includes('星')), '主面板：下一隻細佬蛋帶「星」花紋'); await readOk('主面板（蛋碼待用）', '#l6dov'); await E(() => __qa.l6d.close());

  console.log('# 🛠 開發者模式「6d」');
  { const d = await E(() => { const S = Glimmer.devmode.sections().find(s => s.id === 'l6d'); return { n: S.items.length, ks: __qa.l6d.dev().items.map(i => i.k), st: __qa.l6d.dev().status() }; });
    ok(['open', 'card', 'visit', 'three', 'act', 'expire', 'newday', 'lv4', 'egg', 'eggin', 'tamper', 'self', 'reset'].every(k => d.ks.includes(k)) && /今日朋友/.test(d.st), '13 個掣＋狀態', d); }
  ok(await E(() => __qa.l6d.dev().items.find(i => i.k === 'tamper').run().ok), '改壞碼 → 無效');
  ok(await E(() => !__qa.l6d.dev().items.find(i => i.k === 'self').run().ok), '入自己碼 → 唔得');
  await D('reset'); q = await Q(); ok(q.visits.length === 0 && q.friends === 0 && !q.egg, '重設 6d');

  console.log('# 重疊檢查 360／390／412／768（rail、影子、提示、面板、名片、預覽、蛋碼、資料、朋友簿）');
  for (const vp of [[360, 640], [390, 844], [412, 915], [768, 1024]]) {
    const c2 = await browser.newContext({ viewport: { width: vp[0], height: vp[1] } }); const pg = await c2.newPage(); await pg.clock.install({ time: T0 }); const E2 = (f, a) => pg.evaluate(f, a), W2 = (ms) => pg.waitForTimeout(ms);
    pg.on('pageerror', e => errs.push('pageerror: ' + e.message));
    await pg.goto(BASE + '?' + QS); await E2(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await pg.goto(BASE + '?' + QS);
    await pg.waitForFunction(() => window.__glimmer && __glimmer.liveLoad); await E2(() => __glimmer.liveLoad); await E2(() => __glimmer.houseLoad).catch(() => { }); await E2(() => __glimmer.s2Load).catch(() => { });
    await E2((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; const s = __glimmer.state; s.stage = 'adult'; s.form = 'moon'; s.poops = 0; s.sleeping = false; Object.assign(s.needs, { mood: 70, energy: 90, hunger: 80, clean: 100 }); }, T0);
    await W2(1500); await E2(() => __qa.l6d.artLoad()); const tag = vp.join('x');
    for (const pgn of ['garden', 'toast', 'main', 'card', 'pre', 'egg', 'info', 'book', 'toast2']) {
      await E2(() => { const t = document.getElementById('u62tip'); if (t) t.remove(); for (let i = 0; i < 5; i++) { const b = document.querySelector('#modal[style*="flex"] [data-testid=modal-btn-0]'); if (b) b.click(); } });
      await E2((p) => { const L = __qa.l6d, R = (k) => L.dev().items.find(i => i.k === k).run(); L.close(); L.closeInfo();
        if (p === 'garden') { R('three'); L.railTick(); }
        else if (p === 'toast') { R('newday'); R('visit'); }
        else if (p === 'toast2') { R('expire'); }
        else if (p === 'main') L.open('main');
        else if (p === 'card') L.open('card');
        else if (p === 'pre') { L.open('enter'); L.setInput(L.fakeCode('visit')); L.check(); }
        else if (p === 'egg') { R('lv4'); R('egg'); L.open('egg'); }
        else if (p === 'info') L.info(L.st().visits[0].id);
        else if (p === 'book') L.open('book'); }, pgn);
      await W2(/^toast/.test(pgn) ? 500 : 1200);
      const o = await E2(() => { const o = __qa.ui62.overlap(); return { n: o.n, hits: o.hits, names: o.names }; });
      const need = { garden: ['#l6dbtn'], toast: ['#l6dbtn'], toast2: ['#toast'], main: ['[l6d-tab-card]', '[l6d-tab-book]'], card: ['[l6d-card-save]'], pre: ['[l6d-go]'], egg: ['[l6d-egg-save]'], info: ['[l6d-info-bye]'], book: [] }[pgn];
      ok(o.hits.length === 0 && need.every(k => o.names.some(nm => nm.indexOf(k) >= 0)), tag + ' ' + pgn + '：' + o.n + ' 個框冇重疊', { hits: o.hits.slice(0, 4), miss: need.filter(k => !o.names.some(nm => nm.indexOf(k) >= 0)) });
      if (/^toast/.test(pgn)) ok(await E2(() => { const t = document.getElementById('toast'); if (!t || getComputedStyle(t).display === 'none') return false; const r = t.getBoundingClientRect(); return [...t.querySelectorAll('*')].concat([t]).every(e => { const q = e.getBoundingClientRect(); return q.right <= r.right + 1 && q.bottom <= r.bottom + 1; }) && t.scrollWidth <= t.clientWidth + 1 && t.scrollHeight <= t.clientHeight + 1; }), tag + ' ' + pgn + ' 提示見到、字冇出界', await E2(() => { const t = document.getElementById('toast'); return t && [t.textContent, t.scrollWidth, t.clientWidth, t.scrollHeight, t.clientHeight, t.innerHTML.slice(0, 200)]; }));
      await pg.screenshot({ path: SHOTS + '6d-ov-' + tag + '-' + pgn + '.png' });
    }
    await c2.close();
  }

  console.log('# ?l6dart=0 → placeholder；?v3=0');
  await fresh(QS + '&l6dart=0&v3=0'); await D('visit'); await W(1200);
  { const n = await E(() => __qa.l6d.nodes()); ok(n.length === 1 && n[0].art === 'shadow:alpha' && !n[0].ph, '?l6dart=0：影子照用半透明剪影（寵物 atlas 照用，唔靠 shadow_mask）', n); }
  await E(() => __qa.l6d.open('card')); await W(600);
  { const a = await E(() => { const c = document.querySelector('#l6dov canvas'), ph = [...document.querySelectorAll('#l6dov [data-ph]')].map(e => e.dataset.ph); return { ph, dash: !!c && getComputedStyle(c).outlineStyle === 'dashed' }; });
    ok(a.ph.includes('6d:share_card_bg') && a.ph.some(k => /^6d:icon_/.test(k)) && a.dash, '?l6dart=0：名片底／icon placeholder（洋紅虛線）', a); }
  ok((await E(() => __qa.l6d.drawCard(3))).qrN >= 21, '?l6dart=0：QR 照出（code 畫）'); await shot('12-noart-card'); await E(() => __qa.l6d.close());
  await fresh(QS + '&v3=0'); await E(() => __qa.l6d.artLoad()); await D('visit'); await W(1200);
  { const n = await E(() => __qa.l6d.nodes()), v3 = await E(() => document.getElementById('ui').classList.contains('v3')); ok(n.length === 1 && n[0].art === 'shadow:alpha' && !v3, 'v3=0：影子照用半透明剪影', { n, v3 }); }
  await E(() => __qa.l6d.open('main')); await W(400); await readOk('v3=0 主面板', '#l6dov'); await shot('11-v3off-main'); await E(() => __qa.l6d.close());

  console.log('# ?l6d=0');
  await fresh('q=high&seed=21&ev=0&hour=14&l6d=0'); await W(800);
  ok(await E(() => !(window.__qa && __qa.l6d) && !__glimmer.l6d && !document.getElementById('l6dbtn') && !document.getElementById('l6dlay')), '?l6d=0：冇裝、冇「朋友」掣');
  ok(await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l6d') && !__glimmer.state.share6), '?l6d=0：冇「6d」分組、冇 6d 資料');

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
