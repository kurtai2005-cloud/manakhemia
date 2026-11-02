#!/usr/bin/env node
/* 對 PR #17 真頁面（index.html + window.__qa.pet）做無頭檢查：時鐘、DST、日光、觸控、壞檔、console。
 *   PW_PATH=/tmp/pw/node_modules/playwright-core node tests/pet/qa_glimmer_playwright.js --url http://127.0.0.1:8137/index.html --json tests/pet/out/glimmer_pw.json
 */
'use strict';
const fs = require('fs');
const path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i >= 0 ? process.argv[i + 1] : d; }
function loadPW() {
  for (const p of [process.env.PW_PATH, '/tmp/pw/node_modules/playwright-core', 'playwright-core']) {
    if (!p) continue;
    try { return require(p); } catch (e) {}
  }
  console.error('搵唔到 playwright-core'); process.exit(2);
}
const { chromium } = loadPW();
const URL = arg('url', 'http://127.0.0.1:8137/index.html?debug=1&seed=7');
const OUT = arg('json', path.join(__dirname, 'out', 'glimmer_pw.json'));
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';

function adultEval() {
  return `(() => {
    const s = __glimmer.state;
    s.stage = 'adult'; s.form = 'soft';
    s.needs = { hunger: 90, mood: 90, clean: 90, energy: 90 };
    s.sleeping = false; s.poops = 0;
    __qa.pet.pause(true);
    return true;
  })()`;
}

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const results = [];
  function add(id, pass, extra) { results.push(Object.assign({ id, pass: !!pass }, extra || {})); console.log((pass ? 'PASS ' : 'FAIL ') + id); }

  async function newPage(opts) {
    const ctx = await browser.newContext(Object.assign({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 }, opts || {}));
    const page = await ctx.newPage();
    const errors = [], warns = [];
    page.on('pageerror', e => errors.push(String(e.message || e)));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); else if (m.type() === 'warning') warns.push(m.text()); });
    return { ctx, page, errors, warns };
  }

  // ── 正常載入、日光、時段 ──
  {
    const { ctx, page, errors, warns } = await newPage();
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800);
    const boot = await page.evaluate(async () => {
      const t0 = performance.now();
      while (!__qa.pet.daylight().ready && performance.now() - t0 < 4000) await new Promise(r => setTimeout(r, 50));
      __qa.pet.pause(true);
      const bands = {};
      for (const h of [6.98, 7, 10.99, 11, 16.99, 17, 22.99, 23, 0, 3]) {
        __qa.pet.clock.setHour(h); __qa.pet.step(0.05);
        const dl = __qa.pet.daylight();
        bands[h] = { period: __qa.pet.state().period, hour: __qa.pet.state().hour, dl: dl.dl && { id: dl.dl.id, mix: dl.dl.mix, bloom: dl.dl.bloom, vignette: dl.dl.vignette }, ready: dl.ready, error: dl.error };
      }
      return { qa: typeof __qa.pet.daylight === 'function', bands, pool: __qa.pet.pool() };
    });
    add('載入無 pageerror', errors.length === 0, { errors: errors.slice(0, 8), warns: warns.slice(0, 8) });
    add('__qa.pet.daylight 就緒', boot.qa && boot.bands[9] && boot.bands[9].ready && !boot.bands[9].error, { sample: boot.bands[9] });
    const expect = { 6.98: 'night', 7: 'morning', 10.99: 'morning', 11: 'noon', 16.99: 'noon', 17: 'evening', 22.99: 'evening', 23: 'night', 0: 'night', 3: 'night' };
    const map = { morning: 'early', noon: 'noon', evening: 'dusk', night: 'night' };
    let bandOk = true; const bad = [];
    for (const h of Object.keys(expect)) {
      const b = boot.bands[h];
      if (!b || b.period !== expect[h] || !b.dl || b.dl.id !== map[expect[h]]) { bandOk = false; bad.push(h + '=' + JSON.stringify(b)); }
    }
    add('時段邊界＋daylight id', bandOk, { bad });
    add('池權重（出貨）螢火 20／彩虹 4', boot.pool.some(e => e.id === 'firefly_walk' && e.weight === 20) && boot.pool.some(e => e.id === 'rainbow' && e.weight === 4), { pool: boot.pool });
    await ctx.close();
  }

  // ── 時鐘：119／120／121、+23h59m、+25h、存檔倒退 lastSeen ──
  {
    const { ctx, page, errors } = await newPage();
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(300);
    const clock = await page.evaluate(() => {
      const G = __glimmer, EV = Glimmer.events, SIM = Glimmer.sim;
      const out = [];
      function setup(now) {
        const s = G.state;
        s.stage = 'adult'; s.form = 'soft';
        s.needs = { hunger: 90, mood: 90, clean: 90, energy: 90 };
        s.sleeping = false; s.grains = 0; s.poops = 0;
        s.evs = null;
        __qa.pet.pause(true);
        __qa.pet.clock.use(now);
        s.lastSeen = now; s.lastSaveTime = now;
        return s;
      }
      const T0 = Date.parse('2026-06-15T04:00:00Z'); // HKT 12:00
      for (const [id, back, tamper] of [['119s', 119000, false], ['120s', 120000, false], ['121s', 121000, true]]) {
        const s = setup(T0);
        __qa.pet.clock.set(T0 - back);
        EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        const sup = __qa.pet.suppressed();
        out.push({ id, pass: sup === tamper && s.lastSaveTime === T0, sup, lastSaveTime: s.lastSaveTime, rollbacks: s.evs && s.evs.stats.rollbacks || 0 });
      }
      // G.save 會把 lastSeen 拉返去被回撥嘅而家
      {
        const s = setup(T0);
        G.save();
        __qa.pet.clock.set(T0 - 121000);
        EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        const before = s.lastSeen;
        G.save();
        out.push({ id: 'save-rewinds-lastSeen', pass: s.lastSaveTime === T0 && s.lastSeen === T0 - 121000, lastSaveTime: s.lastSaveTime, lastSeen: s.lastSeen, before });
      }
      // +23h59m 仍然有效
      {
        const s = setup(T0);
        const ahead = T0 + (23 * 3600 + 59 * 60) * 1000;
        s.lastSaveTime = ahead; s.lastSeen = ahead; s.grains = 0;
        __qa.pet.clock.set(T0);
        const rep = SIM.applyOffline(s, G.now());
        const g0 = s.grains;
        const rec = EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        out.push({ id: '+23h59m', pass: !rep.tampered && s.lastSaveTime === ahead && __qa.pet.suppressed() && rep.gift === 0 && g0 === 0, tampered: rep.tampered, sup: __qa.pet.suppressed(), gift: rep.gift, grainsAfterNote: s.grains, note: rec && rec.id });
      }
      // +25h 無效
      {
        const s = setup(T0);
        s.lastSaveTime = T0 + 25 * 3600e3; s.lastSeen = T0 - 10 * 3600e3; s.grains = 0;
        __qa.pet.clock.set(T0);
        const rep = SIM.applyOffline(s, G.now());
        const g0 = s.grains;
        const rec = EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        out.push({ id: '+25h', pass: !!rep.tampered && rep.T === 0 && rep.gift === 0 && g0 === 0 && s.lastSaveTime === T0 && !__qa.pet.suppressed(), tampered: rep.tampered, T: rep.T, gift: rep.gift, grainsOffline: g0, grainsAfterNote: s.grains, note: rec && rec.id, sup: __qa.pet.suppressed() });
      }
      return { out, errors: [] };
    });
    for (const r of clock.out) add('PW ' + r.id, r.pass, r);
    add('PW 時鐘頁無 pageerror', errors.length === 0, { errors: errors.slice(0, 5) });
    await ctx.close();
  }

  // ── DST／時區（browser context timezoneId）──
  async function tzCase(id, tz, tSave, tNow, expectTamper) {
    const { ctx, page, errors } = await newPage({ timezoneId: tz });
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(200);
    const r = await page.evaluate(({ tSave, tNow }) => {
      const s = __glimmer.state; const EV = Glimmer.events; const SIM = Glimmer.sim;
      s.stage = 'adult'; s.form = 'soft'; s.needs = { hunger: 90, mood: 90, clean: 90, energy: 90 }; s.grains = 0;
      __qa.pet.pause(true);
      __qa.pet.clock.use(tSave);
      s.lastSeen = tSave; s.lastSaveTime = tSave; s.evs = null;
      Glimmer.events.markSave(s, tSave);
      __qa.pet.clock.set(tNow);
      const wallSave = new Date(tSave).toString();
      const wallNow = new Date(tNow).toString();
      const rep = SIM.applyOffline(s, __glimmer.now());
      EV.noteOpen(s, { hour: __glimmer.hour(), now: __glimmer.now() });
      return { sup: __qa.pet.suppressed(), tampered: !!rep.tampered, rollbacks: s.evs && s.evs.stats.rollbacks || 0, wallSave, wallNow, hour: __glimmer.hour(), gift: rep.gift, T: rep.T };
    }, { tSave, tNow });
    const tamper = r.sup || r.rollbacks > 0;
    add(id, tamper === expectTamper && errors.length === 0, Object.assign(r, { errors: errors.slice(0, 3) }));
    await ctx.close();
  }
  const edt = Date.parse('2026-11-01T05:30:00Z');
  const est = Date.parse('2026-11-01T06:10:00Z');
  await tzCase('PW DST 秋回撥 美東（UTC 前進）', 'America/New_York', edt, est, false);
  const sprA = Date.parse('2026-03-08T06:30:00Z');
  const sprB = Date.parse('2026-03-08T07:30:00Z');
  await tzCase('PW DST 春前撥 美東', 'America/New_York', sprA, sprB, false);
  const utc = Date.parse('2026-06-15T02:00:00Z');
  await tzCase('PW 時區 HKT 牆鐘', 'Asia/Hong_Kong', utc, utc + 60000, false);
  await tzCase('PW 時區洛杉矶 同一 UTC', 'America/Los_Angeles', utc, utc + 60000, false);

  // ── 觸控：睡眠輕喚醒、連點鬧脾氣、餵食掣 ──
  {
    const { ctx, page, errors } = await newPage();
    await page.goto(URL, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(400);
    await page.evaluate(adultEval());
    const box = await page.locator('#gl').boundingBox();
    const px = box.x + box.width * (97 / 195);
    const py = box.y + box.height * (250 / 422);
    // 睡眠
    await page.evaluate(() => { __glimmer.state.sleeping = true; __qa.pet.step(0.4); __qa.pet.clearLog(); });
    await page.mouse.click(px, py);
    await page.mouse.click(px, py);
    await page.mouse.click(px, py);
    const sleep = await page.evaluate(() => {
      __qa.pet.step(0.6);
      const toast = document.getElementById('toast');
      return { toast: toast && toast.style.display !== 'none' ? toast.textContent : '', expr: __qa.pet.state().expr, state: __qa.pet.state().state, log: __qa.pet.log.filter(j => j.ev === 'tap').map(j => j.name), sleeping: __glimmer.state.sleeping };
    });
    add('睡眠點寵物冇輕喚醒（UI 只吐司）', sleep.toast.indexOf('瞓') >= 0 && !sleep.log.includes('sleepStir'), sleep);

    // 清醒連點 5 下
    await page.evaluate(() => { __glimmer.state.sleeping = false; __qa.pet.force('wake'); __qa.pet.step(0.3); __qa.pet.clearLog(); if (__glimmer.state.evs) __glimmer.state.evs.log = []; });
    for (let i = 0; i < 5; i++) { await page.mouse.click(px, py); await page.evaluate(() => __qa.pet.step(0.4)); }
    const taps = await page.evaluate(() => ({ state: __qa.pet.state().state, taps: __qa.pet.log.filter(j => j.ev === 'tap').map(j => j.name + ':' + j.ph), events: (__qa.pet.eventLog() || []).map(e => e.id) }));
    add('清醒 5 下 → 行為鬧脾氣、但唔係 48h 事件', taps.state === 'grumpy' && !taps.events.includes('grumpy'), taps);

    // 餵食掣可以點到（唔被 #hit 食咗）
    await page.evaluate(() => { __glimmer.state.sleeping = false; __qa.pet.force('wake'); });
    await page.locator('#btn-feed').click();
    const fed = await page.evaluate(() => document.getElementById('pop').style.display);
    add('餵食掣打開選單', fed === 'flex' || fed === 'block', { display: fed });
    add('觸控段無 pageerror', errors.length === 0, { errors: errors.slice(0, 5) });
    await ctx.close();
  }

  // ── 壞檔 ──
  async function bootSave(id, raw) {
    const { ctx, page, errors } = await newPage();
    if (raw !== null) await page.addInitScript(([k, v]) => { localStorage.setItem(k, v); }, ['glimmer_save_v1', raw]);
    let navErr = null;
    try { await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 8000 }); await page.waitForTimeout(400); }
    catch (e) { navErr = String(e.message || e); }
    const alive = await page.evaluate(() => {
      try { return { qa: !!(window.__qa && __qa.pet), stage: __glimmer && __glimmer.state && __glimmer.state.stage, raf: !!__glimmer }; }
      catch (e) { return { evalError: String(e.message || e) }; }
    }).catch(e => ({ evalError: String(e.message || e) }));
    add(id, errors.length === 0 && !navErr && alive.qa, { errors: errors.slice(0, 4), navErr, alive });
    await ctx.close();
  }
  const goodNeeds = { hunger: 80, mood: 80, clean: 80, energy: 80 };
  await bootSave('壞檔 非 JSON', '{');
  await bootSave('壞檔 diary 字串', JSON.stringify({ v: 1, seed: 7, stage: 'adult', form: 'soft', needs: goodNeeds, lastSeen: Date.now(), evs: { v: 1, diary: 'bad', claimedFlashDates: [], stats: { events: 0, byId: {} }, cd: {}, log: [], pending: [], hist: [], rs: 7 } }));
  await bootSave('壞檔 diary [null]', JSON.stringify({ v: 1, seed: 7, stage: 'adult', form: 'soft', needs: goodNeeds, lastSeen: Date.now(), evs: { v: 1, diary: [null], claimedFlashDates: [], stats: { events: 0, byId: {} }, cd: {}, log: [], pending: [], hist: [], rs: 7 } }));
  await bootSave('壞檔 stats 缺 byId', JSON.stringify({ v: 1, seed: 7, stage: 'adult', form: 'soft', needs: goodNeeds, lastSeen: Date.now(), evs: { v: 1, diary: [], claimedFlashDates: [], stats: { events: 1 }, cd: {}, log: [], pending: [], hist: [], rs: 7, next: 0, clock: 0, lastAt: -1e9, dayCount: 0, gDone: false, opens: 0 } }));

  await browser.close();
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(results, null, 1));
  const fail = results.filter(r => !r.pass).length;
  console.log(`\n${results.length - fail}/${results.length} pass`);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
