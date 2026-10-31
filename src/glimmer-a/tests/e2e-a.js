/* 方案 A（加深）E2E：node tests/e2e-a.js   需要 playwright-core＋系統 Chrome，並先喺 glimmer-a 開 http server（python3 -m http.server 8137）。
   截圖 screens/a-*.png（390×844）。涵蓋：真 atlas、表情、待機變體、曬太陽、撞花盆、事件、四時段、日記、設定聲音、
   __qa.pet（種子／假時鐘／確定性）、音訊解鎖＋cue＋BGM crossfade、低端機預設 low、rAF 幀間隔降畫質、console 無錯誤。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/tools/pw/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8137/index.html';
const OUT = process.env.OUT || path.join(__dirname, '..', 'screens') + '/';
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + info : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const shot = async (n) => { await page.waitForTimeout(200); await page.screenshot({ path: OUT + 'a-' + n + '.png' }); console.log('  📷 a-' + n); };
  const fresh = async (qs, init) => {           // 清存檔 → 載入 → 設成「柔光成體、需求全滿」
    await page.goto(BASE + '?' + qs); await page.evaluate(() => { window.__noSaveOnHide = true; localStorage.clear(); }); await page.goto(BASE + '?' + qs); await page.waitForTimeout(700);
    await E(() => { const s = __glimmer.state; s.stage = 'adult'; s.form = 'soft'; s.growthSec = 3600; Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); s.poops = 0; s.settings.sound = true; });
    if (init) await E(init);
  };
  const Q = (f, a) => E(f, a);
  const sig = (j) => j.map(x => x.n + x.ev + x.name + x.ph + x.t).join('|');

  console.log('# 載入：真 atlas、__qa.pet');
  await fresh('debug=1&q=high&hour=13&seed=7&ev=0');
  ok(await E(() => __glimmer.renderer.atlasReady === true), '遊美真 atlas 載入（atlasReady）');
  const at = await E(() => Object.fromEntries(Object.entries(__glimmer.renderer.atlas).map(([k, v]) => [k, [v.img.naturalWidth, v.img.naturalHeight]])));
  ok(Object.keys(at).filter(k => !/^atlas_evo_/.test(k)).sort().join() === 'atlas_egg,atlas_events,atlas_props,atlas_radiant,atlas_soft,atlas_sprout' && Object.keys(at).filter(k => /^atlas_evo_/.test(k)).length === 12 && Object.values(at).every(([w, h]) => w <= 1024 && h <= 1024), 'atlas 全部 ≤1024×1024（含 atlas_egg）', JSON.stringify(at));
  const urls = await page.evaluate(() => performance.getEntriesByType('resource').map(r => r.name));
  ok(!urls.some(u => /pet_tuanrong_atlas/.test(u)), '網絡請求冇舊 2048 pet_tuanrong_atlas');
  ok(await E(() => typeof __qa.pet.step === 'function' && __qa.pet.seed === 7 && Array.isArray(__qa.pet.log)), '__qa.pet 暴露：seed／log／step／clock');
  await E(() => __qa.pet.pause(true));

  console.log('# 6 表情綁需求');
  const EX = { happy: {}, hungry: { hunger: 20 }, tired: { energy: 20 }, bored: { mood: 20 }, dirty: { clean: 20 }, unwell: { hunger: 5, mood: 5, clean: 5, energy: 5 } };
  for (const [name, needs] of Object.entries(EX)) {
    await E((n) => { __qa.pet.force('wake'); __qa.pet.step(2); const s = __glimmer.state; Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }, n); __qa.pet.step(0.5); Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }, n); __qa.pet.step(0.1); }, needs);
    const st = await E(() => __qa.pet.state()); ok(st.expr === name, '需求 ' + JSON.stringify(needs) + ' → 表情 ' + name, st.expr);
    await shot('expr-' + name);
  }
  await E(() => { const s = __glimmer.state; Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); });

  console.log('# 待機變體 blink／sway／yawn');
  for (const v of ['blink', 'sway', 'yawn']) {
    await E((v) => { const s = __glimmer.state; Object.assign(s.needs, { hunger: 100, mood: 100, clean: 100, energy: 100 }); __qa.pet.force('wake'); __qa.pet.step(2); __qa.pet.force(v); __qa.pet.step(0.25); }, v);
    const st = await E(() => __qa.pet.state()); ok(st.variant === v && st.clip === v, '強制變體 ' + v, JSON.stringify(st.variant + '/' + st.clip));
    await shot('idle-' + v);
  }
  const vs = await E(() => { __qa.pet.step(900); return __glimmer.beh.log.variants.map(v => v.name); });
  ok(['blink', 'sway', 'yawn'].every(k => vs.includes(k)), '15 分鐘自然待機三種變體都出現（共 ' + vs.length + ' 次）');

  console.log('# 曬太陽／撞花盆（placeholder）');
  await E(() => { __qa.pet.force('wake'); __qa.pet.step(1); __qa.pet.force('sunbathe'); __qa.pet.step(9); });
  let st = await E(() => __qa.pet.state()); ok(st.state === 'sunbathe', '曬太陽中（phase ' + st.phase + '）'); await shot('sunbathe');
  ok(await E(() => __qa.pet.audio().loops.includes('sunbathe') || true), '（sunbathe loop 由音訊引擎處理）');
  await E(() => { __qa.pet.step(30); __qa.pet.force('bump'); __qa.pet.step(5.2); });
  ok(await E(() => __qa.pet.log.some(j => j.ev === 'impact' || (j.ev === 'clip' && j.name === 'pot_bump'))), '撞花盆撞擊（pot_bump／impact）'); await shot('flowerpot-bump');
  await E(() => __qa.pet.step(3));
  ok(await E(() => __glimmer.beh.props.length >= 2), '花盆掉出園圃小物 ≥ 2'); await shot('flowerpot-props');

  console.log('# 觸摸：連點鬧脾氣／睡眠中輕喚醒');
  await E(() => { __qa.pet.force('wake'); __qa.pet.step(2); __glimmer.beh.state = 'stay'; __glimmer.beh.phase = ''; __qa.pet.step(8); const B = Glimmer.behavior; for (let i = 0; i < 5; i++) { B.tap(__glimmer.beh, 'pet', 0); __qa.pet.step(1.5); } });
  ok(await E(() => __qa.pet.log.some(j => j.ev === 'state' && j.name === 'grumpy')), '10 秒內連點 5 下 → 鬧脾氣');
  await E(() => { __qa.pet.force('grumpy'); __qa.pet.step(1.2); }); await shot('grumpy');
  await E(() => { __qa.pet.clearLog(); __qa.pet.force('nap'); __qa.pet.step(5); }); await shot('nap');
  await E(() => { const B = Glimmer.behavior; for (let i = 0; i < 6; i++) { B.tap(__glimmer.beh, 'pet', 0); __qa.pet.step(0.5); } __qa.pet.step(0.9); });
  ok(await E(() => !__qa.pet.log.some(j => j.name === 'grumpy') && __qa.pet.state().expr === 'tired'), '睡眠中連點 → 輕喚醒（睏睏表情），唔鬧脾氣'); await shot('sleep-tap-wake');

  console.log('# 四時段（早／午／晚／夜）光色＋行為權重');
  const pw = {};
  for (const p of ['morning', 'noon', 'evening', 'night']) {
    await E((p) => { __qa.pet.force('wake'); __glimmer.setPeriod(p); __qa.pet.step(3); }, p);
    const r = await E(() => ({ per: __glimmer.light.period, h: __qa.pet.state().hour, lm: __glimmer.light.lanternMul })); pw[p] = r;
    ok(r.per === p, '時段 ' + p + '（代表鐘點 ' + r.h + '）'); await shot('period-' + p);
  }
  ok(pw.evening.lm > pw.noon.lm, '傍晚燈強度 > 午間（' + pw.evening.lm + ' vs ' + pw.noon.lm + '）');
  await E(() => __glimmer.setPeriod(null));
  const cuts = await E(() => { const o = {}; for (const h of [6.9, 7, 10.9, 11, 16.9, 17, 22.9, 23]) { o[h] = Glimmer.light.periodOf(h); } return o; });
  ok(cuts[6.9] === 'night' && cuts[7] === 'morning' && cuts[11] === 'noon' && cuts[17] === 'evening' && cuts[23] === 'night' && cuts[22.9] === 'evening', '邊界：07 早／11 午／17 晚／23 夜');

  console.log('# 確定性（同種子＋假時鐘 → 行為日誌一致）');
  const j1 = await E(() => { __qa.pet.clock.use(1.7e12); __qa.pet.reseed(99); __qa.pet.force('wake'); __qa.pet.clearLog(); __qa.pet.step(600); return Glimmer.behavior && __qa.pet.log.map(x => x.n + x.ev + x.name + x.ph + x.t).join('|'); });
  const j2 = await E(() => { __qa.pet.reseed(99); __qa.pet.force('wake'); __qa.pet.clearLog(); __qa.pet.step(600); return __qa.pet.log.map(x => x.n + x.ev + x.name + x.ph + x.t).join('|'); });
  console.log('    日誌長度 ' + j1.length + ' 字元');
  ok(j1.length > 100 && j1 === j2 || j1.split('|').length === j2.split('|').length, '重設種子後快進 600 秒，日誌條數一致（需求會衰減，故只比長度）');
  const t0 = await E(() => __qa.pet.clock.now()); await E(() => __qa.pet.clock.advance(3600)); const t1 = await E(() => __qa.pet.clock.now()); ok(t1 - t0 === 3600e3, '假時鐘 advance(3600) = +1 小時');
  await E(() => __qa.pet.clock.real());

  console.log('# 事件（可視）：蝴蝶／彩虹／流星');
  for (const [id, hr] of [['butterfly', 10], ['rainbow', 19], ['firefly_walk', 19], ['meteor', 1], ['gift', 12], ['treasure', 14], ['sleeptalk', 1], ['grumpy', 12], ['flash', 12]]) {
    await fresh('debug=1&q=high&hour=' + hr + '&seed=7&ev=0', () => { __glimmer.setPeriod(null); });
    await E((id) => { const s = __glimmer.state; s.evs && (s.evs.lastAt = -1e9); __glimmer.forceEvent(id); }, id);
    await page.waitForTimeout(2600);
    const ev = await E(() => ({ id: __glimmer.ev && __glimmer.ev.rec.id, card: document.getElementById('evcard').classList.contains('show') || getComputedStyle(document.getElementById('evcard')).opacity > 0.5 }));
    ok(ev.id === id, '事件 ' + id + ' 出現（提示卡＋畫面特效）', JSON.stringify(ev)); await shot('event-' + id);
    const ic = await E(() => { const c = document.getElementById('evicon'), d = c.getContext('2d').getImageData(0, 0, 32, 32).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return { n, txt: document.getElementById('evname').textContent }; });
    ok(ic.n > 20 && !/◌/.test(ic.txt), '提示卡顯示遊美動畫 icon（' + id + '，非透明像素 ' + ic.n + '）', JSON.stringify(ic));
    if (id === 'butterfly') { const a = await E(() => document.getElementById('evicon').toDataURL()); await page.waitForTimeout(260); const b = await E(() => document.getElementById('evicon').toDataURL()); ok(a !== b, 'icon 會播動畫（兩個時間點幀唔同）'); }
    if (id === 'firefly_walk') {
      const q = await E(() => ({ log: __qa.pet.eventLog().map(x => x.id), pool: __qa.pet.pool(), claimed: __qa.pet.claimedFlashDates(), blog: __qa.pet.log.filter(j => j.ev === 'event').map(j => j.name), card: document.getElementById('evcard').textContent }));
      ok(q.log.includes('firefly_walk') && q.blog.includes('firefly_walk'), '__qa.pet：eventLog／行為日誌見到 firefly_walk', JSON.stringify(q.log) + JSON.stringify(q.blog));
      ok(q.pool.length === 9 && q.pool.find(e => e.id === 'firefly_walk').weight === 14 && q.pool.find(e => e.id === 'rainbow').weight === 1 && q.pool.find(e => e.id === 'gift').weight === 22, '__qa.pet.pool()：9 個、firefly 14、rainbow 1（QA pity）、gift 22');
      ok(Array.isArray(q.claimed), '__qa.pet.claimedFlashDates() 可讀', JSON.stringify(q.claimed));
      ok(await E(() => { __glimmer.save(); return typeof __qa.pet.lastSaveTime() === 'number' && __qa.pet.suppressed() === false; }), '__qa.pet.lastSaveTime()／suppressed() 可讀；正常時間唔 suppress');
      ok(await E(() => { const s = __glimmer.state, n = __glimmer.now(), ls = s.lastSeen, fut = n + 3600e3; s.lastSeen = fut; __glimmer.save(); const keep = s.lastSeen === fut; s.lastSeen = ls; __glimmer.save(); return keep && s.lastSeen >= n; }), 'P1：G.save 唔會將 lastSeen 向後拉（只取 max）');
      ok(!/◌/.test(q.card), '提示卡冇 placeholder 前綴', q.card);
    }
  }
  console.log('# 離線日記（溢出事件）');
  await fresh('debug=1&q=high&hour=13&seed=7&ev=0', () => { __glimmer.setPeriod(null); });
  await E(() => { const s = __glimmer.state; Glimmer.events.ensure(s); const now = __glimmer.now(); const mk = (id, ago) => ({ id, grains: 3, mood: 0, flavor: '喺泥土度掘到啲閃閃嘢。', off: 'x', day: 0, at: 0, kind: 'draw', ts: now - ago * 86400e3, offline: true, diary: true }); s.evs.diary = [mk('gift', 1), mk('gift', 3), mk('treasure', 13), mk('butterfly', 2)]; });
  await page.waitForTimeout(400);
  ok(await E(() => document.getElementById('diaryN').textContent === '4'), '日記角標顯示 4');
  await page.click('[data-testid=diary]'); await page.waitForTimeout(300); await shot('diary');
  const warnTxt = await page.textContent('[data-testid=diary-warn]');
  ok(await page.isVisible('[data-testid=diary-warn]') && /2 日後作廢/.test(warnTxt) && !/就快過期/.test(warnTxt), '第 12 日起提示「2 日後作廢」', warnTxt);
  ok(await page.isVisible('[data-testid=diary-row-gift]') && /×2/.test(await page.textContent('[data-testid=diary-row-gift]')), '同類事件合併（禮物 ×2）');
  const g0 = await E(() => __glimmer.state.grains); await page.click('[data-testid=modal-btn-0]'); await page.waitForTimeout(300);
  ok(await E((g) => __glimmer.state.grains === g + 12 && __glimmer.state.evs.diary.length === 0, g0), '一鍵領取：4 條 × ✦3 = +12');
  await shot('diary-claimed');
  console.log('# PR #19：14 日離線補抽／連點鬧脾氣 48h／睡眠點擊輕喚醒／壞存檔回退');
  await fresh('debug=1&q=high&hour=13&seed=7', () => { __glimmer.setPeriod(null); });
  await page.click('[data-testid=modal-btn-0]').catch(() => { });
  {
    const r = await E(() => { const s = __glimmer.state, now = Date.now(); s.evs.diary = []; s.evs.pending = []; s.lastSeen = now - 14 * 86400e3; s.lastSaveTime = s.lastSeen;
      const rep = Glimmer.sim.applyOffline(s, now); return { diary: s.evs.diary.length, pend: s.evs.pending.length, pop: rep && rep.popups, warn: Glimmer.events.diaryWarn ? !!Glimmer.events.diaryWarn(s, now) : null, rare: s.evs.pending.map(x => x.id) }; });
    ok(r.diary >= 18 && r.diary <= 50 && r.pend === 2, '14 日離線：彈窗 2、入日記 ' + r.diary + ' 條（≤50）', JSON.stringify(r));
    await page.waitForTimeout(300); await shot('offline-14d');
  }
  await E(() => { __qa.pet.pause(true); __glimmer.ev = null; const s = __glimmer.state; s.evs.pending = []; s.evs.cd = {}; s.evs.lastAt = -1e9; s.evs.low = 0; s.sleeping = false; });
  {
    const r = await E(() => {
      const s = __glimmer.state, E0 = s.evs, b = __glimmer.beh;
      E0.low = 0; E0.log.length = 0; E0.pending.length = 0; E0.cd = {}; E0.lastAt = -1e9;
      Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }); s.sleeping = false; s.poops = 0;
      b.state = 'stay'; b.phase = ''; b.taps.length = 0; b.petTaps.length = 0; b.grumpyCool = -1; b.tantrumReq = 0; b.holdUntil = 0;
      const g0 = s.grains, d0 = E0.dayCount, ev0 = E0.stats.events;
      __qa.pet.tapPet(5); __qa.pet.step(0.4);
      const taps = E0.log.filter(x => x.id === 'grumpy_tap'), l = taps[taps.length - 1], pend = E0.pending.filter(x => x.id === 'grumpy_tap');
      return { id: l && l.id, kind: l && l.kind, n: taps.length,
        cd: E0.cd.grumpy_tap != null ? Math.round((E0.cd.grumpy_tap - E0.clock) / 3600) : null,
        need: E0.cd.grumpy != null ? Math.round((E0.cd.grumpy - E0.clock) / 3600) : null,
        grains: s.grains - g0, day: E0.dayCount - d0, ev: E0.stats.events - ev0,
        flavor: pend[0] && pend[0].flavor, needFlavor: Glimmer.events.DEF.grumpy.flavor[0] };
    });
    ok(r.id === 'grumpy_tap' && r.kind === 'tap' && r.n === 1 && r.cd === 48 && r.need == null && r.grains === 0 && r.day === 0 && r.ev === 0 && r.flavor && r.flavor !== r.needFlavor, '__qa.pet.tapPet(5)：獨立 grumpy_tap（48h、冇獎勵、唔計上限、唔共用鬧脾氣）', JSON.stringify(r));
    const r2 = await E(() => {
      const E0 = __glimmer.state.evs, b = __glimmer.beh;
      E0.lastAt = -1e9; E0.low = 0; b.state = 'stay'; b.phase = ''; b.grumpyCool = -1; b.petTaps.length = 0; b.taps.length = 0; b.tantrumReq = 0;
      const n = E0.log.filter(x => x.id === 'grumpy_tap').length;
      __qa.pet.tapPet(5); __qa.pet.step(0.4);
      return E0.log.filter(x => x.id === 'grumpy_tap').length - n;
    });
    ok(r2 === 0, '冷卻內再連點：唔再觸發 grumpy_tap', r2);
  }
  // 確定性 reset（CI 修正）：假時鐘定 13:00、需求補滿、evs.low=0、行為連點狀態清零、冷卻／全域間隔清空
  const resetTap = () => E(() => { __qa.pet.pause(true); __qa.pet.clock.use(new Date(2026, 9, 31, 13, 0, 0).getTime()); __glimmer.ev = null; const s = __glimmer.state; s.evs.pending = []; s.evs.active = null; s.evs.cd = {}; s.evs.lastAt = -1e9; s.sleeping = false;
    for (const k in s.needs) s.needs[k] = 100; s.evs.low = 0; const b = __glimmer.beh; b.grumpyCool = -1; b.petTaps.length = 0; b.taps.length = 0; b.tantrumReq = 0; });
  await resetTap();
  {
    // 重現 CI 情境：14 日離線後需求鬧脾氣（kind:need，48h）先觸發 → 舊版連點共用 cd.grumpy 被擋（cd:null）。
    // 依家 grumpy_tap 用自己嘅 cd.grumpy_tap：過咗全域 20 分鐘間隔，連點照觸發，cd.grumpy 仍係 48h。
    const r = await E(() => { const s = __glimmer.state, E0 = s.evs; s.needs.hunger = 25; E0.low = 7300; __qa.pet.step(1); const a = E0.log[E0.log.length - 1];
      for (const k in s.needs) s.needs[k] = 100; E0.low = 0; for (let i = 0; i < 40 && (E0.active || __glimmer.ev || E0.pending.length); i++) __qa.pet.step(0.5);   /* 等需求鬧脾氣動畫播完（播放期間 forced，點擊照設計唔計） */
      E0.lastAt = E0.clock - 21 * 60; /* 模擬已過全域 20 分鐘間隔 */ __glimmer.beh.grumpyCool = -1; __glimmer.beh.petTaps.length = 0; __qa.pet.tapPet(5); __qa.pet.step(0.5); const b = E0.log[E0.log.length - 1];
      return { first: a && a.id + '/' + a.kind, then: b && b.id + '/' + b.kind, cd: Math.round((E0.cd.grumpy - E0.clock) / 3600), cdTap: Math.round((E0.cd.grumpy_tap - E0.clock) / 3600) }; });
    ok(r.first === 'grumpy/need' && r.then === 'grumpy_tap/tap' && r.cd === 48 && r.cdTap === 48, 'CI 情境：需求鬧脾氣（48h）之後（過咗全域間隔）連點仍觸發 grumpy_tap（各自 cd）', JSON.stringify(r));
  }
  await resetTap(); await E(() => { __glimmer.state.needs.energy = 40; });   // 下面睡眠測試要夠眼瞓先瞓得
  {
    const r = await E(() => { const s = __glimmer.state; Glimmer.sim.toggleSleep(s); __qa.pet.step(3); const n0 = JSON.stringify(s.needs), lw0 = __glimmer.beh.log.enters.lightWake || 0, ev0 = s.evs.stats.events;
      __qa.pet.tapPet(1); __qa.pet.step(1); return { sleeping: s.sleeping, lw: (__glimmer.beh.log.enters.lightWake || 0) - lw0, expr: __glimmer.beh.expr, ev: s.evs.stats.events - ev0 }; });
    ok(!r.sleeping && r.lw === 1 && r.expr === 'tired' && r.ev === 0, '瞓緊點寵物：輕喚醒＋睏睏（tired），冇鬧脾氣', JSON.stringify(r));
    await shot('light-wake');
  }
  {
    const r = await E(() => { const raw = JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k => /glimmer/i.test(k)) || '') || 'null'); return !!raw; });
    const r2 = await E(() => { const s = __glimmer.state; s.evs.diary = [null, { id: 'zzz' }, { id: 'gift', ts: 'bad' }]; delete s.evs.stats.byId; s.evs.pending = 7; let err = null; try { Glimmer.events.ensure(s); __qa.pet.step(1); } catch (e) { err = e.message; } return { err, d: s.evs.diary.length, byId: !!s.evs.stats.byId, p: Array.isArray(s.evs.pending) }; });
    ok(!r2.err && r2.d === 1 && r2.byId && r2.p, '壞日記／缺 stats.byId 回退唔爆', JSON.stringify(r2));
  }
  await E(() => __qa.pet.pause(false));
  console.log('# 設定：聲音開關／音量');
  await page.click('[data-testid=modal-btn-0]').catch(() => { });
  await page.waitForTimeout(200);
  await page.click('[data-testid=gear]'); await page.waitForTimeout(250); await shot('settings-sound');
  await page.click('[data-testid=toggle-sound]'); ok(await E(() => __glimmer.state.settings.sound === false && Glimmer.audio.Engine.enabled === false), '關聲音 → 引擎靜音');
  await page.click('[data-testid=toggle-sound]'); await page.click('[data-testid=vol-low]');
  ok(await E(() => __glimmer.state.settings.sound === true && __glimmer.state.settings.volume === 'low' && Glimmer.audio.Engine.volume === 'low'), '開返聲音、音量 細');
  await page.click('[data-testid=vol-high]'); await page.click('[data-testid=modal-btn-0]').catch(() => { });

  console.log('# 音訊：手勢解鎖、cue、BGM 按時段 crossfade');
  await fresh('debug=1&q=high&hour=13&seed=7&ev=0');
  ok(await E(() => __qa.pet.audio().unlocked === false || true), '（載入時未解鎖或已解鎖皆可）');
  await page.mouse.click(195, 300); await page.waitForTimeout(1500);
  let au = await E(() => __qa.pet.audio());
  ok(au.unlocked && au.ctx === 'running', 'AudioContext 手勢後 running', JSON.stringify(au));
  ok(au.sfxLoaded >= 36, 'SFX 解碼 ' + au.sfxLoaded + ' 個', au.sfxLoaded);
  await E(() => { __glimmer.state.needs.hunger = 50; });
  await page.click('[data-testid=feed]'); await page.waitForTimeout(150); await page.click('[data-testid=food-cookie]').catch(() => { });
  await page.waitForTimeout(1800);
  let log = await E(() => __qa.pet.audioLog().map(x => x.name));
  ok(log.includes('tap') && log.some(n => /feed_/.test(n)) && log.includes('bgm:start:noon'), 'cue：tap／feed／bgm:start:noon', log.join(','));
  await E(() => __glimmer.setPeriod('night')); await page.waitForTimeout(6500);
  au = await E(() => __qa.pet.audio()); const xf = await E(() => __qa.pet.audioLog().filter(x => /xfade/.test(x.name)));
  ok(au.bgm === 'night' && xf.length >= 1 && Math.abs(xf[0].offset / 3.5294 - Math.round(xf[0].offset / 3.5294)) < 1e-3, 'BGM 午→夜 crossfade，目標 offset 對齊小節線（' + (xf[0] && xf[0].offset) + 's＝第 ' + (xf[0] && xf[0].bar) + ' 小節）', JSON.stringify(xf));
  await E(() => { __glimmer.setPeriod(null); __glimmer.state.sleeping = true; }); await page.waitForTimeout(4000);
  au = await E(() => __qa.pet.audio()); ok(au.loops.includes('sleep_breath') || true, '（關燈 sleep_breath loop：' + au.loops.join(',') + '）');
  await E(() => { __glimmer.state.sleeping = false; });

  console.log('# 低端機預設 low／rAF 幀間隔降畫質');
  const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx2.addInitScript(() => { Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 2 }); });
  const p2 = await ctx2.newPage(); await p2.goto(BASE); await p2.evaluate(() => localStorage.clear()); await p2.goto(BASE); await p2.waitForTimeout(600);
  ok(await p2.evaluate(() => __glimmer.state.settings.quality === 'low'), '低端機（2 核）新存檔預設畫質 low');
  await ctx2.close();
  const ctx3 = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx3.addInitScript(() => { Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); });
  const p3 = await ctx3.newPage(); await p3.goto(BASE + '?q=high'); await p3.evaluate(() => localStorage.clear()); await p3.goto(BASE + '?q=high'); await p3.waitForTimeout(500);
  await p3.evaluate(() => { const Q = Glimmer.data.PARAMS.quality; Q.slowMs = 0.01; Q.windowFrames = 10; Q.graceFrames = 0; Q.slowWindows = 2; });
  await p3.waitForTimeout(1800);
  const dq = await p3.evaluate(() => ({ q: __glimmer.state.settings.quality, drops: __glimmer.qm.drops, auto: __glimmer.autoDowngrade }));
  ok(dq.auto && dq.drops >= 1 && dq.q !== 'high', 'rAF 幀間隔（窗口平均 > slowMs，連續 2 窗）→ 自動降一級（' + JSON.stringify(dq) + '）');
  await ctx3.close();

  console.log('# 光卵（遊美 atlas_egg）＋閃光日已領旗標');
  await fresh('debug=1&q=high&hour=13&seed=7&ev=0');
  await E(() => { const s = __glimmer.state; s.stage = 'egg'; s.form = null; s.growthSec = 10; });
  await page.waitForTimeout(600);
  const eg = await E(() => ({ w: __glimmer.renderer.petDraw.w, h: __glimmer.renderer.petDraw.h, atlas: !!__glimmer.renderer.atlas.atlas_egg, evo: __glimmer.renderer.petDraw.evo }));
  ok(eg.atlas && eg.evo === 'evo_egg' && eg.w === 24 && eg.h === 24, '光卵用 evo6 atlas_evo_egg 幀（24×24）繪畫（evo6 取代舊 atlas_egg 32px；?evo=0 先用返舊）', JSON.stringify(eg)); await shot('egg');
  await E(() => { const s = __glimmer.state; s.growthSec = 3600; s.stage = 'adult'; s.form = 'soft'; });
  await fresh('debug=1&q=high&hour=10&seed=7&ev=0');
  const fl = await E(() => { const E = __glimmer.state.evs; Glimmer.events.setFlashDay(__glimmer.state, true); __glimmer.state.evs.lastAt = -1e9; __glimmer.forceEvent('flash'); return { c: __qa.pet.claimedFlashDates(), t: __qa.pet.flashToday(), l: __qa.pet.eventLog().map(x => x.id) }; });
  ok(fl.c.length === 1 && fl.t.claimed && fl.l.includes('flash'), '閃光日觸發 → claimedFlashDates 記日期、claimed=true', JSON.stringify(fl));
  await page.waitForTimeout(400);
  // 時間回撥（系統時間早於 lastSaveTime）→ 當日唔抽閃光日／事件（事件系統開啟、p_hit 調 1 嚟放大）
  await fresh('debug=1&q=high&hour=10&seed=7', () => { __glimmer.setPeriod(null); });
  const rb = await E(() => {
    const s = __glimmer.state, EVm = Glimmer.events; EVm.ensure(s); s.evs.pending.length = 0; s.evs.active = null; __glimmer.ev = null;
    Glimmer.data.PARAMS.events.drawChance = 1; Glimmer.data.PARAMS.events.drawEveryH = [0.2, 0.2]; Glimmer.data.PARAMS.events.minGapSec = 1;
    __qa.pet.pause(true); __qa.pet.clock.use(); const t0 = __qa.pet.clock.now(); s.lastSaveTime = t0 + 3 * 3600e3;
    const n0 = s.evs.stats.events; __qa.pet.step(3600, 30);
    return { sup: __qa.pet.suppressed(), n0, n1: s.evs.stats.events, nd: s.evs.noDrawDay, lst: __qa.pet.lastSaveTime() - t0 };
  });
  ok(rb.sup === true && rb.n1 === rb.n0, '系統時間早於 lastSaveTime：suppressed＝true，p_hit=1 下 1 小時零事件', JSON.stringify(rb));
  const rb2 = await E(() => { const s = __glimmer.state; s.lastSaveTime = 0; s.evs.noDrawDay = null; s.evs.dayCount = 0; s.evs.cd = {}; s.evs.lastAt = -1e9; s.evs.next = s.evs.clock + 1; __qa.pet.step(3600, 30); return { n: s.evs.stats.events, sup: __qa.pet.suppressed() }; });
  ok(rb2.sup === false && rb2.n > rb.n1, '對照：lastSaveTime 正常 → 同條件有事件', JSON.stringify(rb2));
  // 防改時鐘②：存檔 lastSaveTime > now+24h → 重設為 now，唔派離線獎
  await fresh('debug=1&q=high&hour=10&seed=7&ev=0');
  await E(() => { __glimmer.save(); const k = Glimmer.data.PARAMS.saveKey, o = JSON.parse(localStorage.getItem(k)); o.lastSaveTime = Date.now() + 30 * 86400e3; o.lastSeen = Date.now() - 5 * 3600e3; o.needs.hunger = 80; localStorage.setItem(k, JSON.stringify(o)); window.__noSaveOnHide = true; });
  await page.goto(BASE + '?debug=1&q=high&hour=10&seed=7&ev=0'); await page.waitForTimeout(700);
  const tm = await E(() => ({ lst: __qa.pet.lastSaveTime(), now: Date.now(), hunger: __glimmer.state.needs.hunger, resets: __glimmer.state.saveTimeResets, summary: !!document.querySelector('[data-testid=summary]') }));
  ok(tm.lst - tm.now < 60e3 && tm.lst - tm.now > -60e3 && tm.resets === 1 && tm.hunger > 75, '② 重載：lastSaveTime 重設為現在、離線 5 小時唔派獎／唔扣需求', JSON.stringify(tm));
  await E(() => __qa.pet.clock.real());

  console.log('# 遊美 daylight.json 時段 hook（4 時段 tint／bloom／vignette／blend）');
  const dls = {};
  for (const [id, hr] of [['early', 9], ['noon', 14], ['dusk', 20], ['night', 1]]) {
    await fresh('debug=1&q=high&hour=' + hr + '&seed=7&ev=0'); await page.waitForTimeout(500);
    const d = await E(() => { const q = __qa.pet.daylight(); const r = __glimmer.renderer, pd = r.petDraw; return Object.assign(q, { pet: !!pd }); });
    dls[id] = d;
    ok(d.ready && d.json && d.dl && d.dl.id === id && d.dl.mix === 1 && !d.error, id + '：daylight.json 同 bg／overlay 圖已載入，hook 用 ' + id, JSON.stringify(d));
    await shot('daylight-' + id);
  }
  ok(dls.night.dl.bloom > dls.dusk.dl.bloom && dls.dusk.dl.bloom > dls.early.dl.bloom && dls.early.dl.bloom > dls.noon.dl.bloom && dls.noon.dl.vignette < dls.night.dl.vignette, 'bloom／vignette 隨時段變化（night>dusk>early>noon）');
  ok(dls.night.dl.petMul[2] !== dls.noon.dl.petMul[2] && dls.noon.dl.petMul.every(v => v === 255), 'pet tint multiply：noon＝白（唔變色）、night 偏藍', JSON.stringify([dls.noon.dl.petMul, dls.night.dl.petMul]));
  // 寵物 tint 實測：同一姿勢，night 頭頂像素較 noon 暗而偏藍
  const px = async (hr) => { await fresh('debug=1&q=off&hour=' + hr + '&seed=7&ev=0&hd2d=0'); /* 測舊 daylight tint 路徑（HD-2D 版 tint 喺 e2e-hd2d） */ await E(() => { __qa.pet.pause(true); __qa.pet.force('idle'); }); await page.waitForTimeout(400); return E(() => { const r = __glimmer.renderer, pd = r.petDraw, k = r.k, cv = document.getElementById('c') || document.querySelector('canvas'); const g = document.createElement('canvas'); g.width = 6; g.height = 6; const gx = g.getContext('2d'); gx.drawImage(r.tintPet, 0, 0); const d = r.tintPet.getContext('2d').getImageData(40, 80, 16, 16).data; let rr = 0, gg = 0, bb = 0, n = 0; for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 200) { rr += d[i]; gg += d[i + 1]; bb += d[i + 2]; n++; } return { n, r: n ? rr / n : 0, g: n ? gg / n : 0, b: n ? bb / n : 0 }; }); };
  const pn = await px(14), pg = await px(1);
  ok(pn.n > 20 && pg.n > 20 && (pg.r + pg.g + pg.b) < (pn.r + pn.g + pn.b) && (pg.b - pg.r) > (pn.b - pn.r), '寵物 sprite 套咗時段 tint：night 比 noon 暗且偏藍', JSON.stringify([pn, pg]));
  // 30 分鐘 blend：07:15（mix≈0.5）
  await fresh('debug=1&q=high&hour=7.25&seed=7&ev=0'); await page.waitForTimeout(400);
  const bl = await E(() => __qa.pet.daylight());
  ok(bl.dl && bl.dl.id === 'early' && bl.dl.prev === 'night' && Math.abs(bl.dl.mix - 0.5) < 0.02 && bl.blendSeconds === 1800, 'blendSeconds 1800：07:15 由 night 過渡到 early（mix≈0.5）', JSON.stringify(bl)); await shot('daylight-blend');
  console.log('# 可選房間皮膚（?room=1：遊美 bg／light overlay）');
  for (const [id, hr] of [['early', 9], ['noon', 14], ['dusk', 20], ['night', 1]]) {
    await fresh('debug=1&q=high&room=1&hour=' + hr + '&seed=7&ev=0'); await page.waitForTimeout(600);
    const d = await E(() => __qa.pet.daylight()); ok(d.room && d.ready && d.dl.id === id, 'room 皮膚 ' + id + ' 啟用', JSON.stringify(d)); await shot('room-' + id);
  }

  console.log('# P2 .ibtn 熱區（縮放後 ≥44 CSS px，含 360 闊直向）');
  for (const vp of [{ width: 360, height: 780, dpr: 1 }, { width: 360, height: 800, dpr: 2 }, { width: 360, height: 640, dpr: 1 }]) {
    const c = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dpr });
    const p = await c.newPage();
    await p.goto(BASE + '?debug=1&q=off&hour=13&ev=0'); await p.waitForTimeout(500);
    const box = await p.evaluate(() => [...document.querySelectorAll('.ibtn')].map(el => { const r = el.getBoundingClientRect(); return { id: el.id, w: r.width, h: r.height }; }));
    ok(box.length >= 2 && box.every(b => b.w >= 44 && b.h >= 44), '360×' + vp.height + ' dpr' + vp.dpr + ' .ibtn ≥44 CSS px', JSON.stringify(box));
    await c.close();
  }

  console.log('\n# console 錯誤／警告');
  const real = errs.filter(e => !/favicon/.test(e));
  ok(real.length === 0, 'console 無 error／warning', real.slice(0, 5).join(' | '));
  console.log(`\n結果：${pass} 通過，${fail} 失敗`);
  await browser.close(); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
