#!/usr/bin/env node
/* Round 3：headless Chrome，window.__qa.pet。唔改遊戲碼。
 *   node qa_glimmer_pw_r3.js --url http://127.0.0.1:8137/index.html --json /tmp/qa-r3/pw.json --shots /tmp/qa-r3/shots
 */
'use strict';
const fs = require('fs');
const path = require('path');
function arg(n, d) { const i = process.argv.indexOf('--' + n); return i >= 0 ? process.argv[i + 1] : d; }
function loadPW() {
  for (const p of [process.env.PW_PATH, '/home/ubuntu/.npm/_npx/e41f203b7505f1fb/node_modules/playwright-core', 'playwright-core']) {
    if (!p) continue;
    try { return require(p); } catch (e) {}
  }
  console.error('搵唔到 playwright-core'); process.exit(2);
}
const { chromium } = loadPW();
const URL = arg('url', 'http://127.0.0.1:8137/index.html?seed=7');
const OUT = arg('json', '/tmp/qa-r3/pw.json');
const SHOTS = arg('shots', '/tmp/qa-r3/shots');
const CHROME = process.env.CHROME || '/usr/bin/google-chrome';

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const results = [];
  function add(id, pass, extra) { results.push(Object.assign({ id, pass: !!pass }, extra || {})); console.log((pass ? 'PASS ' : 'FAIL ') + id); }

  async function newPage(opts) {
    const ctx = await browser.newContext(Object.assign({
      viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true, isMobile: true,
    }, opts || {}));
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(String(e.message || e)));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    return { ctx, page, errors };
  }

  async function boot(page, url) {
    await page.goto(url || URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForFunction(() => window.__qa && __qa.pet && window.__glimmer, { timeout: 8000 });
    await page.waitForTimeout(400);
  }

  // ── __qa.pet：時鐘、保底、save、連點、睡眠、壞檔路徑 ──
  {
    const { ctx, page, errors } = await newPage();
    await boot(page);
    const r = await page.evaluate(() => {
      const G = __glimmer, EV = Glimmer.events, SIM = Glimmer.sim;
      const out = [];
      function setup(now) {
        const s = G.state;
        s.stage = 'adult'; s.form = 'soft';
        s.needs = { hunger: 90, mood: 90, clean: 90, energy: 90 };
        s.sleeping = false; s.grains = 0; s.poops = 0; s.evs = null;
        __qa.pet.pause(true);
        __qa.pet.clock.use(now);
        s.lastSeen = now; s.lastSaveTime = now;
        return s;
      }
      const T0 = Date.parse('2026-06-15T04:00:00Z'); // HKT 12:00
      const pool = __qa.pet.pool();
      out.push({
        id: '池權重 螢火14 彩虹1',
        pass: pool.some(e => e.id === 'firefly_walk' && e.weight === 14) && pool.some(e => e.id === 'rainbow' && e.weight === 1),
        ff: (pool.find(e => e.id === 'firefly_walk') || {}).weight,
        rb: (pool.find(e => e.id === 'rainbow') || {}).weight,
      });
      for (const [id, back, tamper] of [['119s', 119000, false], ['120s', 120000, false], ['121s', 121000, true]]) {
        const s = setup(T0);
        __qa.pet.clock.set(T0 - back);
        EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        const sup = __qa.pet.suppressed();
        out.push({ id: '回撥 ' + id, pass: sup === tamper && s.lastSaveTime === T0, sup, lastSave: s.lastSaveTime === T0, noDraw: s.evs && s.evs.noDrawDay });
      }
      // P0：noDrawDay 當日離線補抽 0（p_hit=1）
      {
        const P = Glimmer.data.PARAMS.events;
        const savedC = P.drawChance, savedE = P.drawEveryH.slice();
        P.drawChance = 1; P.drawEveryH = [0.05, 0.05];
        try {
          const s = setup(T0);
          __qa.pet.clock.set(T0 - 121000);
          EV.noteOpen(s, { hour: 12, now: G.now() });
          const later = T0 + 6 * 3600e3;
          s.lastSeen = later - 5 * 3600e3;
          __qa.pet.clock.set(later);
          const rep = SIM.applyOffline(s, later);
          const rec = EV.noteOpen(s, { hour: G.hour(), now: later });
          const n = (s.evs.offLog || []).length;
          out.push({
            id: 'P0 noDrawDay 離線補抽 0',
            pass: n === 0 && !rec && __qa.pet.suppressed() && s.grains === 0,
            n, note: rec && rec.id, grains: s.grains, sup: __qa.pet.suppressed(), gift: rep.gift,
          });
        } finally { P.drawChance = savedC; P.drawEveryH = savedE; }
      }
      // P1：G.save 唔拉後 lastSeen；恢復後冇離線禮物
      {
        const s = setup(T0);
        G.save();
        __qa.pet.clock.set(T0 - 30 * 60 * 1000);
        const before = s.lastSeen;
        G.save();
        const mid = { lastSeen: s.lastSeen, lastSave: s.lastSaveTime };
        __qa.pet.clock.set(T0);
        s.grains = 0;
        const rep = SIM.applyOffline(s, G.now());
        const rec = EV.noteOpen(s, { hour: G.hour(), now: G.now() });
        out.push({
          id: 'P1 G.save 唔拉後 lastSeen／恢復後冇離線禮物',
          pass: mid.lastSeen === T0 && mid.lastSave === T0 && before === T0 && rep.T === 0 && rep.gift === 0 && s.grains === 0 && !(s.evs.offLog || []).length,
          mid, T: rep.T, gift: rep.gift, grains: s.grains, off: (s.evs.offLog || []).length, note: rec && rec.id,
        });
      }
      // P1：超前 >24h 重設，同一次開啟冇保底 +3
      {
        const s = setup(T0);
        s.lastSaveTime = T0 + 25 * 3600e3; s.lastSeen = T0 - 10 * 3600e3; s.grains = 0;
        __qa.pet.clock.set(T0);
        const rep = SIM.applyOffline(s, G.now());
        const g0 = s.grains;
        const rec = EV.noteOpen(s, { hour: 12, now: G.now() });
        out.push({
          id: 'P1 超前重設同一次開啟冇 +3',
          pass: !!rep.tampered && rep.T === 0 && rep.gift === 0 && g0 === 0 && s.grains === 0 && !rec,
          tampered: rep.tampered, T: rep.T, gift: rep.gift, grains: s.grains, note: rec && rec.id,
        });
      }
      // 連點 5 → 48h 鬧脾氣（__qa.pet.tapPet）
      {
        const s = setup(T0);
        __qa.pet.clock.set(T0);
        const needs = Object.assign({}, s.needs);
        __qa.pet.tapPet(5);
        __qa.pet.step(0.3);
        const E = s.evs;
        const cdH = E && E.cd.grumpy != null ? (E.cd.grumpy - E.clock) / 3600 : null;
        const ids = (E && E.log || []).map(e => e.id + ':' + e.kind);
        out.push({
          id: 'tapPet(5) → grumpy 48h',
          pass: __qa.pet.state().state === 'grumpy' && ids.some(x => x.indexOf('grumpy') === 0) && cdH != null && Math.abs(cdH - 48) < 0.05,
          state: __qa.pet.state().state, ids, cdH, needsSame: ['hunger', 'mood', 'clean', 'energy'].every(k => s.needs[k] === needs[k]),
        });
      }
      // 睡眠輕喚醒
      {
        const s = setup(T0 + 86400000);
        s.sleeping = true;
        const needs = Object.assign({}, s.needs);
        const grains = s.grains;
        const woke = __qa.pet.tapPet(1);
        __qa.pet.step(0.4);
        const st = __qa.pet.state();
        out.push({
          id: '睡眠 tapPet → lightWake 睏睏',
          pass: s.sleeping === false && st.expr === 'tired' && st.state !== 'grumpy' && !(s.evs && (s.evs.log || []).some(e => e.id === 'grumpy'))
            && ['hunger', 'mood', 'clean', 'energy'].every(k => s.needs[k] === needs[k]) && s.grains === grains,
          sleeping: s.sleeping, expr: st.expr, state: st.state, woke,
        });
      }
      return out;
    });
    for (const row of r) add('PW ' + row.id, row.pass, row);
    add('PW 行為頁無 pageerror', errors.length === 0, { errors: errors.slice(0, 6) });
    await ctx.close();
  }

  // 壞檔
  async function bootSave(id, raw) {
    const { ctx, page, errors } = await newPage();
    if (raw !== null) await page.addInitScript(([k, v]) => { localStorage.setItem(k, v); }, ['glimmer_save_v1', raw]);
    let navErr = null;
    try { await boot(page); } catch (e) { navErr = String(e.message || e); }
    const alive = await page.evaluate(() => {
      try { return { qa: !!(window.__qa && __qa.pet), stage: __glimmer.state.stage }; }
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

  // 版面
  const views = [
    { id: '360x640', w: 360, h: 640, land: false },
    { id: '390x844', w: 390, h: 844, land: false },
    { id: '412x915', w: 412, h: 915, land: false },
    { id: '844x390', w: 844, h: 390, land: true },
  ];
  for (const v of views) {
    const { ctx, page, errors } = await newPage({ viewport: { width: v.w, height: v.h }, deviceScaleFactor: 1, hasTouch: true, isMobile: true });
    await boot(page, 'http://127.0.0.1:8137/index.html?seed=7');
    await page.evaluate(() => {
      const s = __glimmer.state;
      s.stage = 'adult'; s.form = 'soft';
      s.needs = { hunger: 72, mood: 80, clean: 64, energy: 55 };
      __qa.pet.pause(true);
      __qa.pet.step(0.5);
    });
    await page.waitForTimeout(200);
    const lay = await page.evaluate(() => {
      const vw = window.innerWidth, vh = window.innerHeight;
      const doc = document.documentElement;
      const sels = ['#diary', '#gear', '#btn-feed', '#btn-play', '#btn-clean', '#btn-sleep', '#chip', '#needs', '#bar', '#grains', '#top-r'];
      const box = (el) => {
        const r = el.getBoundingClientRect();
        return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1), r: +r.right.toFixed(1), b: +r.bottom.toFixed(1) };
      };
      const nodes = {};
      for (const sel of sels) {
        const el = document.querySelector(sel);
        if (!el) { nodes[sel] = null; continue; }
        nodes[sel] = box(el);
      }
      const taps = ['#diary', '#gear', '#btn-feed', '#btn-play', '#btn-clean', '#btn-sleep'].map(sel => {
        const b = nodes[sel];
        const clip = !b || b.x < -1 || b.y < -1 || b.r > vw + 1 || b.b > vh + 1;
        return { sel, w: b && b.w, h: b && b.h, ok44: !!(b && b.w >= 44 && b.h >= 44), clip, box: b };
      });
      function overlap(a, b) {
        if (!a || !b) return 0;
        const x = Math.max(0, Math.min(a.r, b.r) - Math.max(a.x, b.x));
        const y = Math.max(0, Math.min(a.b, b.b) - Math.max(a.y, b.y));
        return +(x * y).toFixed(1);
      }
      const pairs = [];
      const keys = ['#diary', '#gear', '#btn-feed', '#btn-play', '#btn-clean', '#btn-sleep', '#chip', '#needs'];
      for (let i = 0; i < keys.length; i++) for (let j = i + 1; j < keys.length; j++) {
        const area = overlap(nodes[keys[i]], nodes[keys[j]]);
        if (area > 4) pairs.push({ a: keys[i], b: keys[j], area });
      }
      const ui = document.getElementById('ui');
      const stage = document.getElementById('stagewrap');
      const text = document.body.innerText || '';
      const rotate = /轉直|請轉|橫向|rotate|landscape/i.test(text);
      return {
        vw, vh,
        scroll: { sw: doc.scrollWidth, sh: doc.scrollHeight, overflow: doc.scrollWidth > vw + 1 || doc.scrollHeight > vh + 1 },
        layout: __glimmer.layoutInfo,
        ui: box(ui), stage: box(stage),
        taps, pairs, rotate,
        transform: ui.style.transform,
        portraitStrip: box(stage).h > box(stage).w,
      };
    });
    const shot = path.join(SHOTS, 'r3-' + v.id + '.png');
    await page.screenshot({ path: shot, fullPage: false });
    const tapFail = lay.taps.filter(t => !t.ok44);
    const clipFail = lay.taps.filter(t => t.clip);
    const care = lay.taps.filter(t => t.sel.indexOf('btn-') === 1);
    const icon = lay.taps.filter(t => t.sel === '#diary' || t.sel === '#gear');
    if (!v.land) {
      const noOverflow = !lay.scroll.overflow && clipFail.length === 0;
      const noOverlap = lay.pairs.length === 0;
      const tapsOk = tapFail.length === 0;
      add('直向 ' + v.id + ' 無溢出／裁切', noOverflow, { scroll: lay.scroll, clip: clipFail, ui: lay.ui, stage: lay.stage });
      add('直向 ' + v.id + ' 無重疊', noOverlap, { pairs: lay.pairs });
      add('直向 ' + v.id + ' 點擊目標 ≥44px', tapsOk, { taps: lay.taps.map(t => ({ sel: t.sel, w: t.w, h: t.h })) });
      add('直向 ' + v.id + ' 四個照顧掣 ≥44', care.every(t => t.ok44) && icon.length === 2, { care: care.map(t => t.w + 'x' + t.h), icons: icon.map(t => t.sel + ' ' + t.w + 'x' + t.h) });
    } else {
      const landscapeLayout = lay.stage.w > lay.stage.h + 2 || lay.ui.w > lay.ui.h + 2;
      const bug = landscapeLayout && !lay.rotate;
      add('橫向 844x390 唔係橫向排版', !landscapeLayout, {
        stage: lay.stage, ui: lay.ui, rotatePrompt: lay.rotate, portraitStrip: lay.portraitStrip,
        transform: lay.transform, taps: lay.taps.map(t => ({ sel: t.sel, w: t.w, h: t.h })),
        bugIfLandscape: bug,
      });
    }
    add('版面 ' + v.id + ' 無 pageerror', errors.length === 0, { errors: errors.slice(0, 4) });
    await ctx.close();
  }

  // 390 開餵食選單，睇下有冇疊住底欄
  {
    const { ctx, page, errors } = await newPage();
    await boot(page, 'http://127.0.0.1:8137/index.html?seed=7');
    await page.evaluate(() => { __glimmer.state.stage = 'adult'; __glimmer.state.form = 'soft'; __qa.pet.pause(true); __qa.pet.step(0.2); });
    await page.locator('#btn-feed').click();
    await page.waitForTimeout(150);
    const pop = await page.evaluate(() => {
      const b = (sel) => { const r = document.querySelector(sel).getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, b: r.bottom }; };
      const popEl = document.getElementById('pop');
      const items = [...popEl.querySelectorAll('.pitem')].map(el => { const r = el.getBoundingClientRect(); return { w: +r.width.toFixed(1), h: +r.height.toFixed(1), y: +r.y.toFixed(1) }; });
      const bar = b('#bar'), popb = b('#pop');
      const overlap = Math.max(0, Math.min(popb.b, bar.b) - Math.max(popb.y, bar.y));
      return { display: popEl.style.display, items, overlap: +overlap.toFixed(1), popb, bar };
    });
    await page.screenshot({ path: path.join(SHOTS, 'r3-390x844-feed.png') });
    add('餵食選單打開且唔嚴重疊底欄', (pop.display === 'flex' || pop.display === 'block') && pop.overlap < 8 && pop.items.length > 0 && pop.items.every(i => i.h >= 44), pop);
    add('餵食頁無 pageerror', errors.length === 0, { errors: errors.slice(0, 3) });
    await ctx.close();
  }

  await browser.close();
  fs.writeFileSync(OUT, JSON.stringify(results, null, 1));
  const fail = results.filter(r => !r.pass).length;
  console.log(`\n${results.length - fail}/${results.length} pass`);
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
