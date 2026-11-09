/* 《微光小圃》 e2e-6b — 第 6 批 6b「真世界連動」（遊策 breakthrough-6a6d-spec §6b）：
   冇權限／冇原生 → 遊戲完全照舊；計步（模擬原生 RealWorld plugin：拒絕／批准、基線、重開機）→ 每 1000 步 1 格、每 2000 步 1 碎、每日 ≤5；
   真天氣（大概位置 0.1° → Open-Meteo，攔截做假回應）只改畫面（G.view），計分天氣（SIM.weatherNow）唔變；日出日落 → 晝夜色調重映；冇網 → 返遊戲天氣；
   字清晰度（FP12 24px、對比 ≥4.5）、熱區 ≥48、🛠「6b」、?l6b=0、浮動團絨唔受影響；6b.1 散步美術（walk_bg 踏腳石、walk clip 幀／pivot、flipX、deco、ic_walk）。截圖 360×780 DPR3 → SHOTS（6b-*.png）。node tests/e2e-6b.js */
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

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 });
  // 模擬原生 RealWorld plugin（只喺 ?nat=1）：權限由 __rw6fake.grant 控制；步數由測試推
  await ctx.addInitScript(() => {
    if (!/[?&]nat=1/.test(location.search)) return;
    const F = window.__rw6fake = { grant: { steps: 'denied', location: 'denied' }, perm: { steps: 'prompt', location: 'prompt' }, sensor: true, steps: 5000, boot: 1000, loc: { lat: 22.3, lon: 114.2 }, calls: [] };
    const P = (k) => (F.calls.push(k), Promise.resolve());
    window.__rw6native = {
      status: () => P('status').then(() => ({ steps: F.perm.steps, location: F.perm.location, sensor: F.sensor })),
      requestSteps: () => P('requestSteps').then(() => (F.perm.steps = F.grant.steps, { steps: F.perm.steps })),
      requestLocation: () => P('requestLocation').then(() => (F.perm.location = F.grant.location, { location: F.perm.location })),
      steps: () => P('steps').then(() => { if (F.perm.steps !== 'granted') throw new Error('no permission'); return { steps: F.steps, bootMs: F.boot }; }),
      location: () => P('location').then(() => { if (F.perm.location !== 'granted') throw new Error('no permission'); return Object.assign({}, F.loc); }),
    };
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' && !/open-meteo|ERR_FAILED|net::/.test(m.text())) errs.push(m.type() + ': ' + m.text() + ' ' + ((m.location() || {}).url || '')); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  // Open-Meteo 攔截：WX.mode＝'rain'／'fail'
  const WX = { mode: 'rain', urls: [] };
  await page.route('**/api.open-meteo.com/**', (r) => { WX.urls.push(r.request().url()); if (WX.mode === 'fail') return r.abort();
    const code = { rain: 63, fog: 45, clear: 0 }[WX.mode]; return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ current: { weather_code: code }, daily: { sunrise: ['2026-11-02T07:30'], sunset: ['2026-11-02T16:30'] } }) }); });
  const E = (fn, arg) => page.evaluate(fn, arg);
  const W = (ms) => page.waitForTimeout(ms);
  const shot = (n) => page.screenshot({ path: SHOTS + '6b-' + n + '.png' });
  const Q = () => E(() => __qa.l6b.st());
  const QS = 'q=high&seed=21&ev=0';
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.liveLoad).catch(() => { }); await E(() => __glimmer.liveLoad); await E(() => __glimmer.s2Load).catch(() => { }); await E(() => __glimmer.houseLoad).catch(() => { }); }
  const prep = () => E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'dust'; s.sleeping = false; Object.assign(s.needs, { mood: 70, energy: 100, hunger: 80, clean: 100 }); s.poops = 0; });
  const fresh = async (qs) => { await page.goto(BASE + '?' + (qs || QS)); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + (qs || QS)); await ready(); await prep(); await W(1300); };
  const vis = (tid) => page.locator('[data-testid=' + tid + ']').first().isVisible().catch(() => false);
  const click = (tid) => page.locator('[data-testid=' + tid + ']').first().click();
  const readOk = async (name, sel) => { const a = await audit(page, sel); ok(a.items.length > 0 && a.bad.length === 0, name + '：字 ' + a.items.length + ' 段全部合格（FP12 24px、對比 ≥4.5）', a.bad.slice(0, 3).map(b => [b.t, b.eff, b.cr, b.fam])); };
  const hit = (sel) => E((sel) => { const ui = document.getElementById('ui'), k = ui.getBoundingClientRect().width / ui.offsetWidth;
      return [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }).map(e => {
        e.scrollIntoView({ block: 'center', inline: 'nearest' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, h = 24 * k - 0.75; let n = 0;
        for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]]) { const t = document.elementFromPoint(cx + dx * h, cy + dy * h); if (t && (t === e || e.contains(t))) n++; }
        return { id: e.dataset.testid || e.id, n, lay: [Math.round(r.width / k), Math.round(r.height / k)] }; }); }, sel);
  const hitOk = async (label, sel, min) => { const L = await hit(sel); ok(L.length >= (min || 1) && L.every(x => x.n === 8), label + ' 熱區 ≥48（' + L.length + ' 個）', L.filter(x => x.n < 8).slice(0, 3)); };
  const closeModals = async () => { for (let i = 0; i < 10; i++) { const open = await E(() => Glimmer.ui.isModalOpen()); if (!open) return; await E(() => { const b = document.querySelector('[data-testid=dev-close]') || [...document.querySelectorAll('#mbox .btn')].pop(); if (b) b.click(); }); await W(250); } };
  const look = () => E(() => { const G = __glimmer, v = G.view || {}, L = v.light || {}; return { game: G.weather || 'clear', score: Glimmer.sim.weatherNow ? Glimmer.sim.weatherNow() : null, view: (L.hd2d && L.hd2d.weather) || null, vHour: v.hour, hour: G.hour(), same: G.visLight === G.light, period: L.period || L.phase || null, gPeriod: (G.light || {}).period || (G.light || {}).phase || null }; });
  const wallet = () => E(() => { const w = __glimmer.state.sys12 && __glimmer.state.sys12.wallet; return w ? { total: w.total, earned: w.earned } : null; });

  console.log('# 載入：預設全部閂（冇權限）→ 遊戲照舊');
  await fresh();
  ok(await E(() => !!(Glimmer.long6b && Glimmer.long6bui && window.__qa && __qa.l6b && __glimmer.l6b)), 'long6b＋long6bui 裝咗');
  ok(await E(() => /^6[b-d]$/.test(Glimmer.data.PARAMS.series2.version)), '版本 6b+');
  ok(await E(() => Glimmer.data.PARAMS.SHARD_DAILY_TOTAL_CAP === 47), '星星碎每日總上限 47（30＋12＋5）');
  ok(await E(() => Glimmer.devmode.sections().some(s => s.id === 'l6b' && s.title.includes('6b'))), '🛠 開發者模式有「6b」分組');
  let q = await Q(); ok(!q.on.steps && !q.on.wx && !q.native && q.auto === false, '預設：計步閂、真天氣閂、冇原生、webdriver 唔自動', q);
  let lk = await look(); ok(lk.same && lk.vHour === lk.hour && lk.score === lk.game && (lk.view === null || lk.view === lk.game), '冇權限：畫面天氣／時間＝遊戲（同一個 light 物件）', lk);
  for (const w of ['rain', 'fog', 'clear']) { await E(w => __glimmer.weatherSet ? __glimmer.weatherSet(w) : (__glimmer.weather = w), w); await W(250); lk = await look(); ok(lk.game === w && lk.score === w && lk.same, '冇權限：遊戲擲「' + w + '」→ 畫面、計分照舊跟遊戲', lk); }
  await E(() => __glimmer.weatherSet ? __glimmer.weatherSet('clear') : (__glimmer.weather = 'clear')); await W(200);
  ok(await vis('l6b-rail'), '花園 rail「散步」掣');
  await hitOk('rail「散步」', '[data-testid=l6b-rail]');
  await click('l6b-rail'); await W(500); ok((await Q()).ov, '撳「散步」→ 散步路面板');
  await E(() => __qa.l6b.artLoad()); await W(400);
  const V3 = await E(() => document.getElementById('ui').classList.contains('v3'));   // #83：V3 換 walk_bg_v3＋deco @3x（顯示仍 16）
  ok(await E((V3) => [V3 ? '6b:walk_bg_v3' : '6b:walk_bg', '6b:walk_clip'].every(k => document.querySelector('#l6bov [data-art="' + k + '"]')) && !document.querySelector('#l6bov [data-ph]'), V3), '6b.1 美術：walk_bg' + (V3 ? '（V3）' : '') + '＋walk_clip 取代 placeholder');
  { const A = await E(() => __qa.l6b.art()); const J = await E(() => fetch('art/breakthrough/6b/walk6b.json').then(r => r.json()));
    const st = J.keys['6b:walk_bg'].stones.slice().reverse(); ok(A.json && A.err.length === 0 && A.path.length === 12 && st.every((p, i) => A.path[i * 2][0] === p[0] && A.path[i * 2][1] === p[1]), '12 格＝6 粒踏腳石（json 座標，由近到遠）＋中點', A.path);
    const pet = await E(() => { const c = document.querySelector('[data-testid=l6b-walkpet]'); return { fk: c.dataset.fk, w: c.width, h: c.height, cw: c.offsetWidth }; }); const pj = J.pets[pet.fk];
    ok(pj && pet.w === pj.frameSize[0] && pet.h === pj.frameSize[1] && pet.cw === pj.frameSize[0], 'walk clip 幀大細跟該形態 idle（' + pet.fk + ' ' + pet.w + '×' + pet.h + '）', { pet, pj: pj && pj.frameSize });
    const fr = new Set(); for (let i = 0; i < 8; i++) { fr.add(await E(() => document.querySelector('[data-testid=l6b-walkpet]').dataset.frame)); await W(70); } ok(fr.size >= 3, '6 幀 10fps loop（見到 ' + fr.size + ' 幀）');
    ok(await E(() => document.querySelector('[data-testid=l6b-walkshadow]').style.display !== 'none'), '地影由引擎畫（橢圓）');
    ok(await E(() => /ic_walk@3x\.png$/.test(document.querySelector('#l6bbtn i.i img').src)), 'rail icon＝ic_walk'); }
  await readOk('散步路面板', '#l6bov');
  await hitOk('開關／✕', '[data-testid=l6b-tg-steps],[data-testid=l6b-tg-wx],[data-testid=l6b-close]', 3);
  await shot('01-panel-off');
  const w0 = await wallet();
  await click('l6b-tg-steps'); await W(400); q = await Q();
  ok(!q.on.steps && (await E(() => __qa.l6b.toasts().some(t => /計步器/.test(t)))), '瀏覽器冇計步器：撳開 → 保持閂＋提示「照舊玩」', q.on);
  ok(JSON.stringify(await wallet()) === JSON.stringify(w0), '冇權限：錢包冇變', [w0, await wallet()]);
  await click('l6b-close'); await W(300); ok(!(await Q()).ov, '✕ 閂');
  await click('l6b-rail'); await W(300); await page.mouse.click(30, 760); await W(300); ok(!(await Q()).ov, '撳背景閂');

  console.log('# 計步：模擬原生 plugin（?nat=1）— 拒絕 → 照舊；批准 → 基線、1000 步 1 格、2000 步 1 碎、每日 ≤5');
  await fresh('q=high&seed=21&ev=0&nat=1');
  q = await Q(); ok(q.native, '有原生 RealWorld（模擬）');
  await click('l6b-rail'); await W(400);
  await click('l6b-tg-steps'); await W(500); q = await Q();
  ok(!q.on.steps && (await E(() => __rw6fake.calls.includes('requestSteps'))) && (await E(() => __qa.l6b.toasts().some(t => /冇計步權限/.test(t)))), '拒絕 ACTIVITY_RECOGNITION → 保持閂、提示照舊玩', q.on);
  await E(() => { __rw6fake.grant.steps = 'granted'; }); const wa = await wallet();
  await click('l6b-tg-steps'); await W(600); q = await Q();
  ok(q.on.steps && q.today === 0 && q.n.reads === 1, '批准 → 開；第一次讀數只做基線（唔當今日步數）', { on: q.on, today: q.today, n: q.n });
  await E(() => { __rw6fake.steps += 2500; }); await E(() => __qa.l6b.readSteps('e2e')); await W(200); q = await Q();
  ok(q.today === 2500 && q.tile === 2 && q.shards === 1, '+2500 步 → 行 2 格、1 粒碎', { today: q.today, tile: q.tile, sh: q.shards });
  let wb = await wallet(); ok(wb.total - wa.total === 1, '星星碎入錢包（+1）', [wa, wb]);
  await E(() => { __rw6fake.steps += 30000; }); await E(() => __qa.l6b.readSteps('e2e')); await W(200); q = await Q();
  wb = await wallet(); ok(q.shards === 5 && wb.total - wa.total === 5, '再 +30000 步 → 今日碎封頂 5（錢包只 +5）', { sh: q.shards, d: wb.total - wa.total });
  ok(q.today === 32500 && q.tile === 32 % 12 && q.decoToday <= 1, '步數照記（32500）、格數＝32 格（路 12 格一圈）、小物每日 ≤1', { today: q.today, tile: q.tile, deco: q.decoToday });
  await E(() => { __rw6fake.steps += 4000; }); await E(() => __qa.l6b.readSteps('e2e')); q = await Q(); ok(q.shards === 5, '夠晒 5 粒：再行都唔再入碎', q.shards);
  await E(() => { __rw6fake.steps = 800; __rw6fake.boot = 9e6; }); await E(() => __qa.l6b.readSteps('e2e')); q = await Q();
  ok(q.today === 37300 && q.n.reboots === 1, '重開機（計數器歸零）→ 由新計數器計，冇負數', { today: q.today, n: q.n });
  await shot('02-panel-steps');
  await E(() => { const r = __qa.l6b.raw(); return r; }).then(r => ok(JSON.stringify(r).length < 4096 && !/lat|lon/.test(JSON.stringify(r)), '6b 存檔細（' + JSON.stringify(r).length + ' B）、冇位置', JSON.stringify(r).slice(0, 200)));
  await page.goto(BASE + '?q=high&seed=21&ev=0&nat=1'); await ready(); await W(800); q = await Q();
  ok(q.on.steps && q.today === 37300 && q.shards === 5, '重開 app：步數／碎保留（只存本機）', { on: q.on, today: q.today, sh: q.shards });

  console.log('# 真天氣（只改畫面）＋日出日落');
  await E(() => { __glimmer.hourOverride = 12; __glimmer.weatherSet ? __glimmer.weatherSet('clear') : (__glimmer.weather = 'clear'); }); await W(300);
  await click('l6b-rail'); await W(300);
  await click('l6b-tg-wx'); await W(500); q = await Q(); ok(!q.on.wx && WX.urls.length === 0, '拒絕位置 → 真天氣保持閂、冇上網', { on: q.on, n: WX.urls.length });
  await E(() => { __rw6fake.grant.location = 'granted'; }); WX.mode = 'rain';
  await click('l6b-tg-wx'); await W(900); q = await Q();
  ok(q.on.wx && q.wx && q.wx.kind === 'rain', '批准大概位置 → Open-Meteo → 真天氣＝落雨', q.wx);
  ok(WX.urls.length === 1 && /latitude=22\.3&longitude=114\.2/.test(WX.urls[0]) && !/apikey|key=/.test(WX.urls[0]), 'URL 只帶 0.1° 位置、冇 key', WX.urls);
  await click('l6b-close'); await W(500); lk = await look();
  ok(lk.view === 'rain' && lk.game === 'clear' && lk.score === 'clear', '畫面落雨；遊戲／計分天氣仍然晴', lk);
  await shot('03-real-rain');
  ok(await E(() => { const o = __glimmer.evo.sys12Overlay ? __glimmer.evo.sys12Overlay() : {}; return !JSON.stringify(o).includes('rw6') && (!o.wx || o.wx.manual !== 'rain'); }), '浮動團絨 snapshot 唔受影響（冇 rw6、唔跟真天氣）');
  // 日出 7:30／日落 16:30（遊戲參考 6:30／18:30）：真 7:00 未日出 → 畫面當 6:30 前（夜）；真 16:30 → 畫面 18:30
  await E(() => { __glimmer.hourOverride = 7.0; }); await W(300); lk = await look();
  ok(lk.hour === 7 && lk.vHour < 6.5, '真 7:00（未日出）→ 畫面時間 ' + (+lk.vHour).toFixed(2) + '（日出前色調）', lk);
  await E(() => __qa.l6b.wx({ current: { weather_code: 0 }, daily: { sunrise: ['2026-11-02T07:30'], sunset: ['2026-11-02T16:30'] } }));
  await E(() => { __glimmer.hourOverride = 16.5; }); await W(300); lk = await look();
  ok(Math.abs(lk.vHour - 18.5) < 0.02, '真 16:30（日落）→ 畫面 18:30 日落色調', lk);
  await W(2500); await shot('04-sunset-remap');
  await E(() => { __glimmer.hourOverride = 23; }); await W(300); lk = await look(); ok(lk.vHour > 21 && lk.period === 'night' && lk.gPeriod === 'night', '真 23:00 → 畫面 ' + (+lk.vHour).toFixed(2) + '：仍然係夜', lk);
  ok(await E(() => { const m = Glimmer.long6b; return m.visHour({ rw6: { v: 1, on: { wx: true } } }, 3, Date.now()) === 3; }), '冇日照數據 → 時間唔改');
  // 冇網：天氣過期 → 返遊戲天氣
  WX.mode = 'fail'; await E(() => { const r = __glimmer.state.rw6; r.wx.at -= 7 * 3600e3; }); await E(() => __qa.l6b.refreshWx(true)); await W(400); q = await Q(); lk = await look();
  ok(q.wxs.err && lk.view !== 'rain' && lk.same === (lk.vHour === lk.hour), '冇網＋天氣過期（>6 小時）→ 畫面返遊戲天氣', { err: q.wxs.err, lk });
  WX.mode = 'fog'; await E(() => __qa.l6b.refreshWx(true)); await W(400); lk = await look(); ok(lk.view === 'fog' && lk.score === 'clear', '有網再攞：霧（計分仍然晴）', lk);
  await click('l6b-rail'); await W(300); await click('l6b-tg-wx'); await W(300); lk = await look(); q = await Q();
  ok(!q.on.wx && !q.wx && lk.view !== 'fog', '閂真天氣 → 清走、返遊戲天氣', { on: q.on, lk });
  await click('l6b-close'); await E(() => { __glimmer.hourOverride = null; }); await W(200);

  console.log('# 🛠 開發者模式「6b」');
  await closeModals(); await E(() => __qa.devmode.setShown(true)); await W(100); await page.locator('[data-testid=dev-btn]').click(); await W(400);
  ok(await page.locator('[data-testid=dev-sec-l6b]').isVisible(), '分組「6b（真世界連動）」喺開發者模式');
  await hitOk('6b 掣', '[data-testid^=dev-l6b-]', 10);
  await E(() => document.querySelector('[data-testid=dev-sec-l6b]').scrollIntoView({ block: 'start' })); await W(150); await readOk(   /* #83：V3 長字換行令組變高；hitOk 捲到尾之後頭一粒掣會俾面板裁走一半 → 捲返組頂先審 */ '開發者「6b」', '[data-testid=dev-sec-l6b]');
  const dclick = async (k) => { if (!(await page.locator('[data-testid=dev-sec-l6b]').isVisible().catch(() => false))) { await closeModals(); await page.locator('[data-testid=dev-btn]').click(); await W(400); } await page.locator('[data-testid=dev-l6b-' + k + ']').scrollIntoViewIfNeeded(); await page.locator('[data-testid=dev-l6b-' + k + ']').click(); await W(150); };
  await dclick('reset'); await W(200); await dclick('s12k'); await W(300);
  q = await Q(); ok(q.today === 12000 && q.shards === 5, '撳「+12000 步」→ 碎 5（上限）', { today: q.today, sh: q.shards });
  await dclick('rain'); await W(400); lk = await look(); ok(lk.view === 'rain' && lk.score === lk.game, '撳「模擬落雨」→ 只改畫面', lk);
  ok(!(await E(() => [...document.querySelectorAll('[data-testid^=s2-set],[data-testid^=toggle-]')].some(e => /6b|散步/.test(e.textContent)))), '試玩掣唔喺設定');
  await closeModals(); await W(400); await shot('05-dev-rain');

  console.log('# 6b.1 散步美術：向左 flipX、小物');
  await closeModals(); await E(() => { const RW = Glimmer.long6b, s = __glimmer.state; delete s.rw6; RW.setOn(s, 'steps', true); RW.credit(s, 8300, __glimmer.now()); const o = RW.st(s), t = __glimmer.now(); o.log.push({ t, k: 'leaf', tile: 3 }, { t, k: 'acorn', tile: 6 }, { t, k: 'clover', tile: 10 }); });
  await click('l6b-rail'); await W(600);
  { const P = await E(() => { const c = document.querySelector('[data-testid=l6b-walkpet]'); return { dir: c.dataset.dir, tf: c.style.transform, tile: Glimmer.long6b.pos(__glimmer.state).tile }; });
    ok(P.dir === 'L' && /scaleX\(-1\)/.test(P.tf), '下一格喺左 → flipX（第 ' + (P.tile + 1) + ' 格）', P);
    const D = await E(() => [...document.querySelectorAll('img[data-testid^=l6b-deco-]')].map(e => e.dataset.art)); ok(['6b:deco_maple_leaf', '6b:deco_acorn', '6b:deco_clover4'].every(k => D.includes(k)), '今日執到小物用 deco 圖（16×16）', D);
    await W(300); { const L = await E(() => [...document.querySelectorAll('img[data-testid^=l6b-deco-]')].map(e => [e.dataset.art, e.offsetWidth, e.complete, e.naturalWidth])); const V3d = await E(() => document.getElementById('ui').classList.contains('v3')), NW = V3d ? 48 : 16; ok(L.length >= 3 && L.every(x => x[1] === 16 && x[2] && x[3] === NW), 'deco 16×16 載到' + (V3d ? '（V3 @3x 原圖 48）' : ''), L); } }
  await readOk('散步路（新美術）', '#l6bov'); await shot('06-walk-art'); await click('l6b-close'); await W(200);

  console.log('# ?l6b=0');
  await fresh('q=high&seed=21&ev=0&l6b=0&nat=1'); await W(800);
  ok(await E(() => !window.__qa.l6b && !__glimmer.l6b && !__glimmer.visWeather && !__glimmer.visHour), '?l6b=0：冇裝、冇畫面 hook');
  ok(!(await vis('l6b-rail')) && (await E(() => !Glimmer.devmode.sections().some(s => s.id === 'l6b'))), '?l6b=0：冇「散步」掣、冇「6b」分組');
  await E(() => __glimmer.weatherSet ? __glimmer.weatherSet('rain') : (__glimmer.weather = 'rain')); await W(300); lk = await look(); ok(lk.same && lk.score === 'rain', '?l6b=0：天氣照舊', lk);
  ok(await E(() => !__glimmer.state.rw6 && __rw6fake.calls.length === 0), '?l6b=0：冇 6b 資料、冇叫原生');

  console.log('# webdriver 預設：唔自動讀計步器／攞天氣；?l6b=1 先自動');
  await fresh('q=high&seed=21&ev=0&nat=1'); await W(1800); ok(await E(() => __rw6fake.calls.length === 0), 'webdriver：冇自動叫原生');
  await fresh('q=high&seed=21&ev=0&nat=1&l6b=1'); await W(1800); ok(await E(() => __rw6fake.calls.includes('status') && !__rw6fake.calls.includes('steps')), '?l6b=1：自動查權限；未開唔讀步數', await E(() => __rw6fake.calls));

  ok(errs.length === 0, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
