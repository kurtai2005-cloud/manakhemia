/* 《微光小圃》 e2e-sys12 — systems12 第 1 批：系統 7 天氣／季節（自動天氣寫入 G.weather、DEV／?weather= 覆蓋、H3 陰／霧／雨、季節層、撐葉／打冷震、tell）。
   截圖 → SHOTS sys12-*.png。直向 390×844。數值讀 config（D.PARAMS.systems12）。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8238/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
const ONLY = (process.env.ONLY || '').split(',').filter(Boolean), want = (k) => !ONLY.length || ONLY.includes(k);
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info).slice(0, 600) : '')); } };

const Glimmer_lines_ok = (txt, L) => L.some(l => txt.includes(l));
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.evoLoad && __glimmer.hdReady).catch(() => { }); await E(() => Promise.all([__glimmer.liveLoad, __glimmer.evoLoad, __glimmer.hdReady])); await page.waitForTimeout(300); };
  const shot = async (n, crop) => {
    await page.waitForTimeout(150); let clip;
    if (crop) clip = await E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, b = window.Glimmer.ui.petHitBox(); const w = 150, h = 170;
      return { x: Math.max(0, r.left + (b.x + b.w / 2) * k - w / 2), y: Math.max(0, r.top + (b.y + b.h / 2) * k - h / 2 - 20), width: w, height: h }; });
    await page.screenshot({ path: SHOTS + 'sys12-' + n + '.png', clip }); console.log('  📷 sys12-' + n);
  };
  const closeModals = async () => { for (let i = 0; i < 6; i++) { const v = await E(() => getComputedStyle(document.getElementById('modal')).display !== 'none'); if (!v) break; await E(() => { const b = document.querySelectorAll('#mbox .btn'); (b[b.length > 1 ? 1 : 0] || b[0]).click(); }); await page.waitForTimeout(150); } };
  const jc = (tid) => E((tid) => document.querySelector('[data-testid="' + tid + '"]').click(), tid);
  const dev = async (tid) => { await E(() => { const p = document.getElementById('devp'); if (p && p.classList.contains('fold')) p.classList.remove('fold'); }); await page.click('[data-testid="' + tid + '"]'); };
  const go = async (q) => { await page.goto(BASE + q); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + q); await ready(); await E(() => { window.__noSaveOnHide = true; }); };
  const juv = () => E(() => { const s = __glimmer.state; s.stage = 'juvenile'; s.form = null; s.sleeping = false; s.growthSec = 10; Object.assign(s.needs, { hunger: 100, mood: 80, clean: 100, energy: 100 }); s.poops = 0; __qa.pet.force('stay'); __glimmer.beh.x = 0; });

  if (want('wx')) {
    console.log('# ① 系統 7：自動天氣 → G.weather（DEV／?weather= 覆蓋）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1&wxauto=1');
    const C = await E(() => Glimmer.data.PARAMS.systems12);
    // 假時鐘：搵一個落緊雨嘅時刻（用遊戲 seed）
    const r = await E(() => { const G = __glimmer, X = Glimmer.sys12, seed = G.state.seed >>> 0, t0 = new Date(2026, 10, 2, 0, 0).getTime();
      let rainT = null, clearT = null; for (let m = 0; m < 14 * 24 * 60 && (rainT == null || clearT == null); m += 10) { const t = t0 + m * 60000, h = new Date(t).getHours(); const w = X.weatherAt(t, seed); if (w === 'rain' && rainT == null && h >= 10 && h < 16) rainT = t; if (w === 'clear' && clearT == null && h >= 10 && h < 16) clearT = t; }
      return { rainT, clearT, seed, sim: X.simulate(seed, t0, 14) }; });
    ok(r.rainT && r.clearT && Object.values(r.sim.weeks).every(n => n >= C.weather.rainPerWeek[0] && n <= C.weather.rainPerWeek[1]), '遊戲 seed 14 日：每週 1–3 場雨', r.sim.weeks);
    await E((t) => { const G = __glimmer; G.clock.fake = true; G.clock.t = t; G.hourOverride = null; __qa.sys12.weather(); }, r.rainT); await page.waitForTimeout(2600);
    let w = await E(() => __qa.sys12.wx());
    ok(w.auto && !w.manual && w.autoWeather === 'rain' && w.weatherNow === 'rain' && w.scene === 'H3rain', '自動：落雨時段 → G.weather＝rain、H3rain', w);
    await juv(); await page.waitForTimeout(1500); w = await E(() => __qa.sys12.wx());
    ok(w.umbrella && w.shown === 'leaf_umbrella', '落雨 → 團絨 idle 撐葉（leaf_umbrella）', w);
    await shot('wx-rain-auto'); await shot('wx-umbrella', true);
    await E((t) => { __glimmer.clock.t = t; }, r.clearT); await page.waitForTimeout(2600);
    w = await E(() => __qa.sys12.wx()); ok(w.weatherNow === 'clear' && w.scene === 'H3' && !w.umbrella, '自動：轉晴 → clear、H3、收葉', w);
    await dev('dev-weather-rain'); await page.waitForTimeout(2600); w = await E(() => __qa.sys12.wx());
    ok(w.manual && w.weatherNow === 'rain' && w.autoWeather === 'clear', 'DEV 雨 → 覆蓋自動（自動仍係 clear）', w);
    await dev('dev-weather-auto'); await page.waitForTimeout(1300); w = await E(() => __qa.sys12.wx());
    ok(!w.manual && w.weatherNow === 'clear', 'DEV 自動 → 跟返自動', w);
    for (const k of ['overcast', 'fog']) {
      await dev('dev-weather-' + k); await page.waitForTimeout(2600); w = await E(() => __qa.sys12.wx());
      ok(w.weatherNow === k && w.scene === 'H3' + k, `DEV ${k} → H3${k} 場景`, w); await shot('wx-' + k);
    }
    { const sh = await E(() => { __qa.sys12.play('shiver'); return new Promise(res => setTimeout(() => res(__qa.sys12.wx()), 300)); }); ok(sh.one === 'shiver' && sh.shown === 'shiver', '打冷震 clip 可播（霧天）', sh); await shot('wx-shiver', true); }
    const sp = await E(() => ({ fog: Glimmer.sys12.shiverMul('fog', 'autumn'), clear: Glimmer.sys12.shiverMul('clear', 'autumn') })); ok(sp.fog > sp.clear, '霧天打冷震機率加大', sp);
    // ?weather= 覆蓋
    await go('?q=high&hour=13&seed=21&ev=0&dev=1&wxauto=1&weather=overcast'); w = await E(() => __qa.sys12.wx());
    ok(w.manual && w.weatherNow === 'overcast', '?weather=overcast → 覆蓋自動', w);
    // 雨暗 18%
    const dim = await E(() => __glimmer.hd && Glimmer.hd2d.CFG.rainDim); ok(Math.abs(dim - C.weather.rainDim) < 1e-9, `H3 雨再暗 ${C.weather.rainDim * 100}%（config）`, dim);
    console.log('# ② 季節（香港月份）＋ DEV 強制');
    await go('?q=high&hour=8&seed=21&ev=0&dev=1&season=auto');
    for (const m of ['spring', 'summer', 'autumn', 'winter']) {
      await dev('dev-season-' + m); await page.waitForTimeout(400); await E(() => __glimmer.hd.loadSeason(__glimmer.wx.season)); await page.waitForTimeout(3600);
      w = await E(() => __qa.sys12.wx()); ok(w.season === m && w.scene === 'H1@' + m, `DEV 季節 ${m} → H1@${m}`, w); await shot('season-' + m);
    }
    await dev('dev-season-none'); await page.waitForTimeout(3500); w = await E(() => __qa.sys12.wx()); ok(!w.season && w.scene === 'H1', '季節 none → 基本款', w);
    await dev('dev-season-auto'); await E((t) => { __glimmer.clock.fake = true; __glimmer.clock.t = t; }, new Date(2026, 0, 10, 9).getTime()); await page.waitForTimeout(1300);
    w = await E(() => __qa.sys12.wx()); ok(w.season === 'winter', '自動：1 月 → 冬', w);
    // tell clip（遊美 G）
    console.log('# ③ §7 G tell clip（絨跳預告）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-juvenile'); await closeModals(); await juv(); await page.waitForTimeout(400);
    await E(() => { __glimmer.foreLog = []; __glimmer.state.ev.push({ type: 'foreshadow', form: 'tide', act: Glimmer.data.PARAMS.evo6.route.foreshadow.tide }); }); await page.waitForTimeout(250);
    w = await E(() => ({ log: __glimmer.foreLog, wx: __qa.sys12.wx() })); ok(w.log.length === 1 && w.log[0].tell === 'tell_tide' && w.wx.shown === 'tell_tide', '預告 tide → 播 tell_tide（行為照舊）', w); await shot('tell-tide', true);
  }
  if (want('quest')) {
    console.log('# ④ 系統 1：每日小委託（3 個、每個 5、齊即發；00:00 重置；補發；DEV）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-sprout'); await closeModals(); await juv(); await E(() => { __glimmer.state.stage = 'sprout'; });
    await dev('dev-s12-qreset'); await page.waitForTimeout(1200);
    let q = await E(() => __qa.sys12.quests()); const Q = await E(() => Glimmer.data.PARAMS.systems12.quests);
    ok(q.list.length === 3 && q.list.every(x => Q.kinds[x.k]), '芽崽 → 3 個委託', q.list);
    const chip = await E(() => { const c = document.querySelector('[data-testid="s12-chip"]'), r = c.getBoundingClientRect(); return { vis: r.width > 0 && getComputedStyle(c).display !== 'none', txt: c.textContent, r: [r.x, r.y, r.width, r.height] }; });
    ok(chip.vis && /委託 0\/3/.test(chip.txt), 'HUD 星星碎＋委託進度 chip', chip);
    // 真照顧（sim.feed／play／rinse）
    const doK = (k) => E((k) => { const S = Glimmer.sim, s = __glimmer.state; s.sleeping = false; s.needs.hunger = 20; s.needs.clean = 30; s.needs.energy = 100;
      if (k === 'feed') return S.feed(s, Glimmer.data.FOODS[0].id).ok; if (k === 'play') return S.play(s).ok; if (k === 'rinse') return S.rinse(s).ok; return false; }, k);
    const w0 = await E(() => __qa.sys12.wallet().total);
    for (const x of q.list.slice(0, 2)) for (let i = 0; i < x.need; i++) await doK(x.k);
    await page.waitForTimeout(1300); q = await E(() => __qa.sys12.quests());
    ok(q.list.slice(0, 2).every(x => x.n >= x.need) && !q.paid && (await E(() => __qa.sys12.wallet().total)) === w0, '做咗 2 個 → 未發獎', q);
    await page.click('[data-testid="s12-chip"]'); await page.waitForTimeout(400);
    const pv = await E(() => ({ open: getComputedStyle(document.querySelector('[data-testid="s12-panel"]')).display, rows: document.querySelectorAll('.s12q').length, done: [...document.querySelectorAll('.s12q')].map(r => r.dataset.done).join(''), bi: getComputedStyle(document.getElementById('s12box')).borderImageSource }));
    ok(pv.open === 'flex' && pv.rows === 3 && pv.done === '110' && /^url\("data:image\/png/.test(pv.bi), '撳 chip → 委託面板（遊美 9-slice、勾選 2/3）', pv);
    await shot('quest-panel');
    for (let i = 0; i < q.list[2].need; i++) await doK(q.list[2].k);
    await page.waitForTimeout(1300); q = await E(() => __qa.sys12.quests()); let w = await E(() => __qa.sys12.wallet());
    ok(q.done && q.paid && w.total === w0 + Q.reward * 3 && w.q === 15, `3 個齊 → 即刻 +${Q.reward * 3} 星星碎`, w);
    const gain = await E(() => document.querySelector('[data-testid="s12-gain"]').textContent); ok(/\+15 星星碎/.test(gain), '浮字「+15 星星碎（委託完成）」', gain);
    await shot('quest-done');
    await E(() => __qa.sys12.close());
    // 路線委託（領先水珠）
    await E(() => { const s = __glimmer.state; s.evo.b5 = { sprout: { all: 10, tide: 8, shroom: 1, crystal: 0, moon: 1, ember: 0 } }; s.evo.b5sys = {}; s.cq = 60; });
    await dev('dev-s12-qreset'); q = await E(() => __qa.sys12.quests()); const rq = q.list.find(x => x.route);
    ok(rq && rq.k === Q.routeKind[rq.route], '有領先路線 → 1 個委託偏向該路線', q.list);
    await dev('dev-s12-qall'); const b = await E(() => ({ sys: __glimmer.state.evo.b5sys, B: Glimmer.sim.branch5Check(__glimmer.state).sys }));
    ok(rq && b.sys.sprout && b.sys.sprout[rq.route] === 1 && b.B.capped[rq.route] <= 8 / 3 + 1e-6, '路線委託完成 → 路線新系統分 +1（≤25% cap）', b);
    w = await E(() => __qa.sys12.wallet()); ok(w.q === 15, '同日第二輪（DEV 重抽）唔會超過委託每日 15', w);
    // 存檔＋斷線補發
    await E(() => { const x = Glimmer.sys12.st(__glimmer.state).quests; x.list.forEach(y => { y.n = y.need; }); x.paid = false; const d = new Date(__glimmer.now() - 86400e3); x.day = Glimmer.sim.dayKey(d.getTime()); __glimmer.save && __glimmer.save(); });
    const tot1 = await E(() => __qa.sys12.wallet().total);
    await E(() => { localStorage.setItem(Glimmer.data.PARAMS.saveKey, Glimmer.sim.serialize(__glimmer.state)); window.__noSaveOnHide = true; });
    await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&dev=1'); await ready(); await page.waitForTimeout(1500);
    w = await E(() => __qa.sys12.wallet()); q = await E(() => __qa.sys12.quests());
    ok(w.total === tot1 + 15 && q.day === (await E(() => Glimmer.sim.dayKey(__glimmer.now()))) && !q.done, '重開：舊日 3 個齊未發 → 補發 15＋今日新委託', { w, q });
    const lg = await E(() => __qa.sys12.log().filter(e => e.what === 'paid')); ok(lg.some(e => e.late), '補發有記錄（late）', lg);
    await dev('dev-s12-shard5'); ok((await E(() => __qa.sys12.wallet().total)) === tot1 + 20, 'DEV +5 星星碎');
  }
  if (want('bond')) {
    console.log('# ⑤ 系統 6：親密度＋心聲（照顧 +1、長撳 +2、每日上限、唔理 −2、心聲 30%／冷卻、面板、化光紀念）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-sprout'); await closeModals(); await juv(); await E(() => { __glimmer.state.stage = 'sprout'; });
    const BC = await E(() => Glimmer.data.PARAMS.systems12.bond);
    let b = await E(() => __qa.sys12.bond()); ok(b.v === BC.start && b.tier === 1, `起步 ${BC.start}（第 1 段心聲）`, b);
    await E(() => { const S = Glimmer.sim, s = __glimmer.state; s.needs.hunger = 20; S.feed(s, Glimmer.data.FOODS[0].id); });
    b = await E(() => __qa.sys12.bond()); ok(b.v === BC.start + BC.care, '照顧一次 → +' + BC.care, b);
    const c = await E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, h = Glimmer.ui.petHitBox(); return { x: r.left + (h.x + h.w / 2) * k, y: r.top + (h.y + h.h / 2) * k }; });
    await page.mouse.move(c.x, c.y); await page.mouse.down(); await page.waitForTimeout(900); await page.mouse.up(); await page.waitForTimeout(500);
    b = await E(() => __qa.sys12.bond()); ok(b.v === BC.start + BC.care + BC.longPress, '真長撳寵物 → +' + BC.longPress, b);
    await E(() => { for (let i = 0; i < 12; i++) Glimmer.sys12.onLongPress(__glimmer.state, __glimmer.now(), __glimmer.state.ev); });
    b = await E(() => __qa.sys12.bond()); ok(b.todayGain === BC.dailyGainCap && b.v === BC.start + BC.dailyGainCap, `每日最多 +${BC.dailyGainCap}`, b);
    const ig = await E(() => __qa.sys12.ignoreDay()); b = await E(() => __qa.sys12.bond()); ok(ig.lost === BC.ignoreDecay && b.v === BC.start + BC.dailyGainCap - BC.ignoreDecay, `一日冇照顧 → −${BC.ignoreDecay}`, { ig, b });
    await dev('dev-s12-bond-down'); await dev('dev-s12-bond-down'); await E(() => __qa.sys12.ignoreDay()); b = await E(() => __qa.sys12.bond()); ok(b.v >= BC.floor, `跌唔落 ${BC.floor} 以下`, b);
    // 心聲：真短撳（Math.random 鎖死做 0.1 → 中；0.9 → 唔中），冷卻
    await E(() => { __qa.sys12.bondSet(66); Glimmer.sys12.bondOf(__glimmer.state).lastVoice = 0; window.__mr = Math.random; Math.random = () => 0.9; });
    await page.mouse.click(c.x, c.y); await page.waitForTimeout(400); let tr = await E(() => __qa.sys12.lastTry()); ok(tr && tr.why === 'roll', '短撳：抽唔中（> 30%）→ 冇心聲', tr);
    await E(() => { Math.random = () => 0.1; }); await page.mouse.click(c.x, c.y); await page.waitForTimeout(500);
    tr = await E(() => __qa.sys12.lastTry()); const vb = await E(() => { const v = document.querySelector('[data-testid="s12-voice"]'), r = v.getBoundingClientRect(); return { op: getComputedStyle(v).opacity, txt: v.textContent, bi: getComputedStyle(v).borderImageSource.slice(0, 26), r: [r.x, r.y, r.width, r.height] }; });
    const unlocked = BC.lines.slice(0, 3).flat();
    ok(tr && tr.ok && unlocked.includes(tr.line) && vb.op === '1' && vb.txt.includes(tr.line) && /data:image\/png/.test(vb.bi), '短撳抽中 → 頭頂心聲泡（遊美 bubble_thought、已解鎖段）', { tr, vb });
    await shot('bond-voice');
    await page.waitForTimeout(300); await page.mouse.click(c.x, c.y); await page.waitForTimeout(300); tr = await E(() => __qa.sys12.lastTry()); ok(tr && tr.why === 'cooldown' && tr.left > BC.voice.cooldownSec - 30, `冷卻 ${BC.voice.cooldownSec / 60} 分鐘`, tr);
    await E(() => { Math.random = window.__mr; });
    await dev('dev-s12-bond-open'); await page.waitForTimeout(400);
    const pv = await E(() => ({ tab: __glimmer.s12.tab, lk: document.querySelectorAll('.s12line.lock').length, un: document.querySelectorAll('.s12line:not(.lock)').length, v: document.querySelector('[data-testid="s12-bond-v"]').textContent }));
    ok(pv.tab === 'bond' && pv.un === 18 && pv.lk === 12 && /66/.test(pv.v), '親密面板：66 → 解鎖 3 段（18 句），其餘 ？？？', pv);
    await shot('bond-panel'); await E(() => __qa.sys12.close());
    const tier = await E(() => { __qa.sys12.bondSet(79); Glimmer.sys12.bondOf(__glimmer.state).day = ''; Glimmer.sys12.onLongPress(__glimmer.state, __glimmer.now(), __glimmer.state.ev); return new Promise(r => setTimeout(() => r({ b: __qa.sys12.bond(), g: document.querySelector('[data-testid="s12-gain"]').textContent }), 1300)); });
    ok(tier.b.tier === 4 && /解鎖第 4 段/.test(tier.g), '升段 → 浮字「解鎖第 4 段心聲」', tier);
    // 化光：紀念冊記親密度
    const fm = await E(() => { const s = __glimmer.state; s.stage = 'elder'; s.fadeReady = true; Glimmer.sys12.bondTick(s, __glimmer.now(), s.ev); Glimmer.sim.fade(s); return { m: s.memorial[s.memorial.length - 1], b: __qa.sys12.bond() }; });
    ok(fm.m.bond === 81 && fm.m.bondElder === 81 && fm.b.v === BC.start, '化光 → 紀念冊記親密度 81；新一代由 20 起', fm);
    await page.waitForTimeout(1200); const md = await E(() => document.getElementById('mbox') && document.getElementById('mbox').textContent); ok(/親密度 81/.test(md || ''), '化光彈窗多一句「紀念冊記低：親密度 81」', md && md.slice(0, 200));
    await shot('bond-fade'); await closeModals();
    await E(() => __qa.sys12.open('bond')); await page.waitForTimeout(300); ok(await E(() => document.querySelectorAll('[data-testid="s12-mem"]').length >= 1), '親密面板紀念冊列出上一代');
  }
  if (want('surp')) {
    console.log('# ⑥ 系統 12：懸浮小驚喜（設定逐項開閂、預設碎開提醒閂、懸浮 replay 入帳每日 5、提醒泡預覽、snapshot）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-sprout'); await closeModals(); await juv(); await E(() => { __glimmer.state.stage = 'sprout'; });
    let u = await E(() => __qa.sys12.surp()); ok(u.on.drop && !u.on.water && !u.on.sleep, '預設：星星碎開、飲水／早瞓閂', u.on);
    await E(() => { const p = document.getElementById('devp'); if (p) p.classList.add('fold'); }); await page.click('#gear'); await page.waitForTimeout(400);
    const tg = await E(() => ['drop', 'water', 'sleep'].map(k => { const b = document.querySelector('[data-testid="toggle-surp-' + k + '"]'); return b ? b.textContent : null; }));
    ok(tg.join() === '開,關,關', '設定彈窗有 3 個開關（碎開、水關、瞓關）', tg);
    await jc('toggle-surp-water'); await jc('surp-waterH-1'); await jc('toggle-surp-sleep'); await jc('surp-sleepAt-2330');
    u = await E(() => __qa.sys12.surp()); ok(u.on.water && u.waterH === 1 && u.on.sleep && u.sleepAt === '23:30' && u.ts > 0, '撳開飲水（1h）＋早瞓（23:30）→ 存入 s.sys12.surp', u);
    await shot('surp-settings');
    await E(() => [...document.querySelectorAll('#mbox .btn')].find(b => b.textContent === '關閉').click()); await page.waitForTimeout(300);
    let ov = await E(() => __glimmer.evo.sys12Overlay()); ok(ov.surp.on.water && ov.surp.waterH === 1 && ov.surp.sleepAt === '23:30' && ov.surp.drop.perDay === 5 && ov.surp.lines.water.length >= 3, 'overlay snapshot（sys12Overlay）帶設定／config', ov.surp);
    const w0 = await E(() => __qa.sys12.wallet().total);
    await dev('dev-s12-drop'); await page.waitForTimeout(1300);
    let w = await E(() => __qa.sys12.wallet()); const g = await E(() => document.querySelector('[data-testid="s12-gain"]').textContent);
    ok(w.total === w0 + 1 && /\+1 星星碎/.test(g), '懸浮送 1 粒（DEV 模擬 replay）→ +1、浮字', { w, g });
    await dev('dev-s12-drop6'); w = await E(() => __qa.sys12.wallet()); ov = await E(() => __glimmer.evo.sys12Overlay());
    ok(w.total === w0 + 5 && ov.surp.drop.room === 0, '同日再送 6 粒 → 每日最多 5（尚餘 0）', { w, room: ov.surp.drop.room });
    await dev('dev-s12-tg-drop'); await E(() => { const d = __glimmer.state.sys12.surp.drops; for (const k in d) d[k] = 0; });
    const r = await E(() => __glimmer.evo.sys12Apply([{ k: 'drop', t: __glimmer.now() }])); ok(r.drop === 0 && !(await E(() => __qa.sys12.surp().on.drop)), '閂咗星星碎 → 懸浮送嚟都唔入帳', r);
    await dev('dev-s12-tg-drop');
    await dev('dev-s12-water'); await page.waitForTimeout(500);
    const vb = await E(() => { const v = document.querySelector('[data-testid="s12-voice"]'); return { op: getComputedStyle(v).opacity, txt: v.textContent, img: !!v.querySelector('span img[src^="art/"], span img[src^="data:"], span img[src^="blob:"]') }; });
    ok(vb.op === '1' && vb.img && Glimmer_lines_ok(vb.txt, await E(() => Glimmer.data.PARAMS.systems12.surprise.lines.water)), '飲水提醒泡（遊美 icon_remind_water）', vb);
    await shot('surp-water'); await page.waitForTimeout(6500);
    await dev('dev-s12-sleep'); await page.waitForTimeout(500); await shot('surp-sleep');
    await dev('dev-s12-surp-open'); await page.waitForTimeout(400);
    const pv = await E(() => ({ tab: __glimmer.s12.tab, rows: [...document.querySelectorAll('[data-testid^="s12-surp-"]')].map(r => r.dataset.done).join('') }));
    ok(pv.tab === 'surp' && pv.rows === '111', '小驚喜面板（3 行，勾選）', pv);
    await jc('s12-surp-water'); await page.waitForTimeout(200); u = await E(() => __qa.sys12.surp()); ok(!u.on.water, '面板撳一行 → 閂飲水', u.on);
    await shot('surp-panel'); await E(() => __qa.sys12.close());
    // 存檔
    await E(() => { localStorage.setItem(Glimmer.data.PARAMS.saveKey, Glimmer.sim.serialize(__glimmer.state)); window.__noSaveOnHide = true; });
    await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&dev=1'); await ready(); u = await E(() => __qa.sys12.surp());
    ok(!u.on.water && u.on.sleep && u.sleepAt === '23:30' && u.waterH === 1, '重開：設定保留', u);
  }
  if (want('diary')) {
    console.log('# ⑦ 系統 3：團絨日記（每日 1 篇、特別頁、離線日、翻 30 日、化光入紀念冊）');
    await go('?q=high&hour=13&seed=21&ev=0&dev=1'); await dev('dev-stage-sprout'); await closeModals(); await juv(); await E(() => { __glimmer.state.stage = 'sprout'; });
    await E(() => { __glimmer.state.sys12.diary.tr = null; });   // DEV 跳階段唔當今日進化
    await E(() => { const S = Glimmer.sim, s = __glimmer.state; s.needs.hunger = 20; S.feed(s, 'meal'); }); await page.waitForTimeout(600);
    let d = await E(() => __qa.sys12.diary()); ok(d.today && d.today.lines.some(l => l.includes('暖菇飯')), '真餵暖菇飯 → 今日草稿記低（ui fed 事件）', d.today);
    await dev('dev-s12-diary-open'); await page.waitForTimeout(500);
    let pg = await E(() => __qa.sys12.diaryPage()); const bi = await E(() => getComputedStyle(document.querySelector('[data-testid="s12-diary-page"]')).borderImageSource.slice(0, 26));
    ok(pg && /今日・寫緊/.test(pg.pos) && pg.special === '0' && /data:image\/png/.test(bi), '日記面板：今日頁（遊美 diary_page_9s）', { pg, bi });
    await shot('diary-today');
    await dev('dev-s12-diary-evolve'); await E(() => __glimmer.s12draw()); await page.waitForTimeout(400); pg = await E(() => __qa.sys12.diaryPage());
    ok(pg.special === '1' && /進化日/.test(pg.txt), '進化 → 特別頁（diary_page_special）', pg); await shot('diary-evolve');
    await dev('dev-s12-diary-offline'); await E(() => { __glimmer.s12.dpage = null; __glimmer.s12draw(); }); d = await E(() => __qa.sys12.diary());
    ok(d.list.filter(x => x.kind === 'offline').length === 3 && d.list.some(x => x.kind === 'evolve'), 'DEV 離線 3 日 → 寫低舊日＋3 句離線', d.list.map(x => x.kind));
    await E(() => { __glimmer.s12.dpage = __qa.sys12.diary().list.findIndex(x => x.kind === 'offline'); __glimmer.s12draw(); }); pg = await E(() => __qa.sys12.diaryPage()); ok(pg.kind === 'offline', '離線日頁（一句）', pg); await shot('diary-offline');
    await dev('dev-s12-diary-fill'); await E(() => { __glimmer.s12.dpage = 0; __glimmer.s12draw(); }); d = await E(() => __qa.sys12.diary());
    ok(d.list.length === 30, '填 40 日 → 只留 30 篇', d.list.length);
    for (let i = 0; i < 3; i++) { await page.click('[data-testid="s12-diary-next"]'); await page.waitForTimeout(80); }
    pg = await E(() => __qa.sys12.diaryPage()); ok(/4／31/.test(pg.pos), '撳 ▶ 翻頁（30 篇＋今日）', pg.pos);
    await page.click('[data-testid="s12-diary-prev"]'); pg = await E(() => __qa.sys12.diaryPage()); ok(/3／31/.test(pg.pos), '撳 ◀ 翻返', pg.pos);
    await shot('diary-browse'); await E(() => __qa.sys12.close());
    const fm = await E(() => { const s = __glimmer.state; s.stage = 'elder'; s.fadeReady = true; Glimmer.sim.fade(s); const m = s.memorial[s.memorial.length - 1]; return { n: m.diary.length, last: m.diary[m.diary.length - 1].kind, cur: __qa.sys12.diary().list.length }; });
    ok(fm.n === 30 && fm.last === 'fade' && fm.cur === 0, '化光 → 化光日特別頁＋日記入紀念冊；今代清空', fm);
    await page.waitForTimeout(1000); await closeModals();
    await E(() => { __glimmer.s12.dsrc = 'cur'; __qa.sys12.open('diary'); }); await page.waitForTimeout(300);
    await page.click('[data-testid="s12-dsrc-mem"]'); await page.waitForTimeout(300); pg = await E(() => __qa.sys12.diaryPage());
    ok(pg && pg.kind === 'fade' && /化光日/.test(pg.txt), '日記面板揀「紀念冊・第 1 代」→ 翻到化光日', pg); await shot('diary-memorial');
    await E(() => __qa.sys12.close());
  }
  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
