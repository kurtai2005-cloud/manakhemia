/* 《微光小圃》 e2e-route — §7 路線清晰化：跳跳期燈泡路線色（螢絨隱藏）、圖鑑（剪影＋提示）、判定前 12h 預告小動作。
   截圖 → SHOTS（預設 /workspace/live-s2/screens/）route-*.png。直向 390×844。數值全部讀 config（D.PARAMS.evo6.route／branch）。 */
const path = require('path');
let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
if (!chromium) { console.error('找不到 playwright-core'); process.exit(2); }
const BASE = process.env.BASE || 'http://localhost:8238/index.html';
const SHOTS = process.env.SHOTS || process.env.OUT || path.join(__dirname, '..', '..', '..', 'screens') + '/';
require('fs').mkdirSync(SHOTS, { recursive: true });
let pass = 0, fail = 0;
const ok = (c, n, info) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (info !== undefined ? ' → ' + JSON.stringify(info) : '')); } };

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  const E = (fn, arg) => page.evaluate(fn, arg);
  const ready = async () => { await page.waitForFunction(() => window.__glimmer && __glimmer.evoLoad).catch(() => { }); await E(() => Promise.all([__glimmer.liveLoad, __glimmer.evoLoad])); await page.waitForTimeout(300); };
  const shot = async (n, crop) => {
    await page.waitForTimeout(150); let clip;
    if (crop) clip = await E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, b = window.Glimmer.ui.petHitBox(); const w = 150, h = 170;
      return { x: Math.max(0, r.left + (b.x + b.w / 2) * k - w / 2), y: Math.max(0, r.top + (b.y + b.h / 2) * k - h / 2 - 20), width: w, height: h }; });
    await page.screenshot({ path: SHOTS + 'route-' + n + '.png', clip }); console.log('  📷 route-' + n);
  };
  const closeModals = async () => { for (let i = 0; i < 6; i++) { const v = await E(() => getComputedStyle(document.getElementById('modal')).display !== 'none'); if (!v) break; await E(() => { const n = document.querySelectorAll('#mbox .btn').length > 1 ? 1 : 0, b = document.querySelector('[data-testid="modal-btn-' + n + '"]'); b && b.click(); }); await page.waitForTimeout(250); } };   // DEV 面板開住會遮住彈窗掣 → 用 DOM click
  const dev = (tid) => page.click('[data-testid="' + tid + '"]');
  // 跳跳期：直接寫 §7 分數（芽崽＋跳跳期）、CQ、進度
  const juv = (o) => E((o) => { const G = __glimmer, s = G.state, D = Glimmer.data, J = D.PARAMS.stageSec.juvenile;
    s.stage = 'juvenile'; s.form = null; s.sleeping = false; s.cq = o.cq; s.growthSec = o.growthSec != null ? o.growthSec : J * o.prog;
    s.evo = { evIn: o.lumi ? { juvenile: { [D.PARAMS.evo6.lumiEvent]: 1 } } : {}, care: o.lumi ? { juvenile: { all: 10, night: 10 } } : {}, b5: { juvenile: Object.assign({ all: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }, o.b5) }, cl: { juvenile: { sum: 100, sec: 1 } } };
    { const now = G.now(), dk = Glimmer.sim.dayKey; s.careDays = o.noDays ? [] : [0, 1, 2, 3, 4, 5, 6].map(i => dk(now - i * 864e5)).sort(); s.evo.day0 = dk(now - 6 * 864e5); }   // v4 燦光：最近 7 日都有照顧
    Object.assign(s.needs, { hunger: 100, mood: 70, clean: 100, energy: 100 }); s.poops = 0; __qa.pet.force('stay'); G.beh.x = 0; G.beh.dir = 1; }, o);

  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&dev=1'); await E(() => { window.__noSaveOnHide = true; localStorage.clear(); });
  await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&dev=1'); await ready(); await E(() => { window.__noSaveOnHide = true; });
  const CFG = await E(() => ({ R: Glimmer.data.PARAMS.evo6.route, C: Glimmer.data.PARAMS.evo6.branch, J: Glimmer.data.PARAMS.stageSec.juvenile, hint: Glimmer.data.ROUTE_HINT }));
  const hi = Math.max(CFG.C.brightCQ, CFG.C.b5CQ) + 15, hx = (h) => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));

  console.log('# ① 跳跳期燈泡：慢慢轉做領先路線色（螢絨唔顯示）');
  await dev('dev-stage-juvenile'); await closeModals();
  const routes = [['shroom', { all: 20, shroom: 16, ember: 4 }], ['moon', { all: 20, moon: 15, shroom: 5 }], ['ember', { all: 20, ember: 16, tide: 4 }], ['tide', { all: 20, tide: 15, ember: 5 }], ['bright', { all: 30, tide: 8, shroom: 8, ember: 7, moon: 7 }]];
  for (const [f, b5] of routes) {
    await juv({ cq: hi, prog: 0.9, b5 }); await page.waitForTimeout(6500);
    const r = await E(() => { const b = __qa.pet.bulb(); return { drawn: b.drawn, lead: __qa.dev.routeLead() }; });
    const want = hx(CFG.R.colors[f]), rt = r.drawn && r.drawn.route;
    ok(r.lead.lead === f && rt && rt.form === f && Math.abs(rt.mix - CFG.R.bulbMaxMix) < 0.05 && rt.rgb.every((v, i) => Math.abs(v - want[i]) <= 6), `領先 ${f} → 燈泡畫路線色 ${CFG.R.colors[f]}（mix ≈${CFG.R.bulbMaxMix}）`, r);
    await shot('bulb-' + f, true);
  }
  { await juv({ cq: hi, prog: 0.02, b5: { all: 20, shroom: 16, ember: 4 } }); await page.waitForTimeout(6500);
    const r = await E(() => __qa.pet.bulb().drawn); ok(r && r.route && r.route.mix < 0.1, '跳跳期頭（進度 2%）→ 路線色仲好淡（慢慢轉）', r); await shot('bulb-early', true); }
  { await juv({ cq: hi, prog: 0.9, b5: { all: 20, shroom: 16, ember: 4 } }); await page.waitForTimeout(6500);
    await E(() => { __glimmer.state.evo.b5.juvenile = { all: 20, tide: 0, shroom: 2, crystal: 0, moon: 0, ember: 18 }; });
    const seq = []; for (let i = 0; i < 4; i++) { await page.waitForTimeout(700); seq.push(await E(() => { const r = __qa.pet.bulb().drawn.route; return [r.form, r.rgb]; })); }
    const g = seq.map(x => x[1][1]); ok(seq[3][0] === 'ember' && g[0] > g[1] && g[1] > g[2], '領先路線轉咗 → 色慢慢過（唔係即跳）', seq); }
  { await juv({ cq: hi, prog: 0.9, b5: { all: 12, shroom: 10, ember: 2 }, lumi: true }); await page.waitForTimeout(1500);
    const r = await E(() => ({ d: (Glimmer.sim.setBranchRoll(() => 0), Glimmer.sim.decideBranch(__glimmer.state).form) + (Glimmer.sim.setBranchRoll(null), ''), b: __qa.pet.bulb().drawn })); ok(r.d === 'lumi' && r.b.route && r.b.route.form === 'shroom', '符合螢絨：燈泡唔顯示螢絨（顯示菇傘色）', r); }
  { await dev('dev-stage-sprout'); await closeModals(); await page.waitForTimeout(800); const r = await E(() => __qa.pet.bulb().drawn); ok(!r || !r.route, '芽崽：冇路線色', r); }

  console.log('# ② 圖鑑：未解鎖剪影＋一句提示');
  await E(() => __qa.dev.dexUnlock('none')); await page.click('[data-testid="dex"]'); await page.waitForTimeout(300);
  let dx = await E(() => [...document.querySelectorAll('[data-testid^="dex-"].dexCell')].map(c => { const cv = c.querySelector('canvas'), d = cv.getContext('2d').getImageData(0, 0, 48, 48).data, cols = new Set(); let n = 0;
    for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 0) { n++; cols.add(d[i] + ',' + d[i + 1] + ',' + d[i + 2]); }
    return { id: c.dataset.testid.slice(4), un: c.dataset.unlocked, name: c.querySelector('b').textContent, hint: c.querySelector('small').textContent, px: n, cols: cols.size, col: [...cols][0] }; }));
  const sil = hx(CFG.R.silhouette).join(',');
  ok(dx.length === 9 && dx.every(d => d.un === '0' && d.name === '？？？' && d.hint === CFG.hint[d.id] && d.px > 100 && d.cols === 1 && d.col === sil), '9 格全部剪影（單色、現有圖嘅形）＋一句提示', dx);
  ok(dx.find(d => d.id === 'lumi').hint === '？？？', '螢絨提示＝？？？');
  ok(await E(() => document.getElementById('mbox').dataset.kind === 'dex' && document.querySelector('#mbox').getBoundingClientRect().bottom <= innerHeight), '圖鑑彈窗喺畫面內');
  await page.screenshot({ path: SHOTS + 'route-dex-locked.png' }); console.log('  📷 route-dex-locked');
  await closeModals();
  await E(() => { ['shroom', 'moon', 'bright', 'ember'].forEach(f => __qa.dev.dexUnlock(f)); }); await page.click('[data-testid="dex"]'); await page.waitForTimeout(300);
  dx = await E(() => [...document.querySelectorAll('.dexCell')].map(c => { const d = c.querySelector('canvas').getContext('2d').getImageData(0, 0, 48, 48).data, cols = new Set();
    for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 0) cols.add(d[i] + ',' + d[i + 1] + ',' + d[i + 2]); return { id: c.dataset.testid.slice(4), un: c.dataset.unlocked, name: c.querySelector('b').textContent, cols: cols.size }; }));
  const U = ['shroom', 'moon', 'bright', 'ember'];
  ok(dx.filter(d => U.includes(d.id)).every(d => d.un === '1' && d.name === { shroom: '菇傘', moon: '月眠', bright: '燦光', ember: '火苗' }[d.id] && d.cols > 4) && dx.filter(d => !U.includes(d.id)).every(d => d.un === '0' && d.cols === 1), '解鎖格顯示名＋原圖；其餘仍係剪影', dx);
  await page.screenshot({ path: SHOTS + 'route-dex-some.png' }); console.log('  📷 route-dex-some');
  await closeModals();
  { // 真判定解鎖：跳跳期完 → 圖鑑多一格
    await E(() => __qa.dev.dexUnlock('none')); await juv({ cq: hi, growthSec: CFG.J - 2, b5: { all: 20, tide: 16, ember: 4 } }); await E(() => __glimmer.fastForward(5)); await page.waitForTimeout(300); await closeModals();
    const r = await E(() => ({ form: __glimmer.state.form, dex: __glimmer.state.dex.slice() })); ok(r.form === 'tide' && r.dex.join() === 'tide', '跳跳期完成為水珠 → 圖鑑解鎖水珠', r); }

  console.log('# ③ 判定前 12h 預告小動作');
  for (const [f, b5] of [['ember', { all: 20, ember: 16, tide: 4 }], ['moon', { all: 20, moon: 15, shroom: 5 }], ['shroom', { all: 20, shroom: 16, ember: 4 }]]) {
    await dev('dev-stage-juvenile'); await closeModals();
    await juv({ cq: hi, growthSec: CFG.J - CFG.R.foreshadowLeadSec - 3, b5 }); await E(() => { __glimmer.foreLog = []; }); await page.waitForTimeout(300);
    const before = await E(() => (__glimmer.foreLog || []).length);
    await E(() => __glimmer.fastForward(5)); await page.waitForTimeout(f === 'ember' ? 350 : 500);
    const r = await E(() => ({ yawns: (__glimmer.beh.log.variants || []).filter(v => v.name === 'yawn' && v.start >= __glimmer.beh.t - 2).length, log: __glimmer.foreLog, fore: __glimmer.state.evo.fore, act: __glimmer.renderer.pet.act, variant: __glimmer.beh.variant, clip: __glimmer.beh.clip, state: __glimmer.beh.state }));
    const a = CFG.R.foreshadow[f];
    ok(before === 0 && r.log.length === 1 && r.log[0].form === f && r.fore && r.fore.form === f, `${f}：跨過判定前 12h → 預告一次`, r);
    ok(a.beh ? (a.beh === 'yawn' ? (r.variant === 'yawn' || r.yawns > 0) : r.log[0].act === a.beh) : r.act === a.act, `${f}：做 ${JSON.stringify(a)}`, r);
    await shot('foreshadow-' + f, true);
    await E(() => __glimmer.fastForward(600)); await page.waitForTimeout(200);
    ok(await E(() => __glimmer.foreLog.length) === 1, `${f}：之後唔再預告`);
  }
  { // 瞓緊覺 → 醒咗先做
    await juv({ cq: hi, growthSec: CFG.J - CFG.R.foreshadowLeadSec - 3, b5: { all: 20, ember: 16, tide: 4 } }); await E(() => { __glimmer.foreLog = []; __glimmer.state.sleeping = true; const P = Glimmer.data.PARAMS; __glimmer.state.needs.energy = Math.max(P.sickThreshold + 10, P.sleepWakeAt - 40); });   // 唔可以低過 sickThreshold（不適唔長大）亦唔可以夠醒
    await E(() => __glimmer.fastForward(5)); await page.waitForTimeout(400); const fired = await E(() => !!(__glimmer.state.evo.fore)), a = await E(() => __glimmer.foreLog.length), slp = await E(() => __glimmer.state.sleeping);
    if (!slp) console.log('  · 注意：fastForward 後寵物已醒');
    await E(() => { __glimmer.state.sleeping = false; __glimmer.state.needs.energy = 90; }); await closeModals(); await page.waitForTimeout(900); const b = await E(() => __glimmer.foreLog.length), dbg = await E(() => ({ pend: !!Glimmer.ui.pendingFore, modal: getComputedStyle(document.getElementById('modal')).display, slp: __glimmer.state.sleeping }));
    ok(fired && a === 0 && b === 1, '瞓緊覺唔做（預告已觸發但押後）；醒咗先做', [fired, a, b, dbg]);
  }

  console.log('# ④ v4 天氣（DEV 抽屜／?weather=）＋燦光照顧日');
  { const dclick = (tid) => E((t) => document.querySelector('[data-testid="' + t + '"]').click(), tid);
    const care = (k) => E((k) => { const S = Glimmer.sim, s = __glimmer.state; s.stage = 'sprout'; s.evo = { evIn: {}, care: {} }; Glimmer.sim.setHourFn(() => 12); S.noteCare(s, 12, k); const b = Object.assign({}, s.evo.b5.sprout); Glimmer.sim.setHourFn(() => (__glimmer.hour ? __glimmer.hour() : new Date().getHours())); return b; }, k);
    ok(await E(() => !!document.querySelector('[data-testid="dev-weather-row"]')), 'DEV 抽屜有天氣列');
    await dclick('dev-weather-overcast'); await page.waitForTimeout(150);
    let r = await E(() => ({ w: Glimmer.sim.weatherNow(), g: __glimmer.weather, txt: (document.querySelector('[data-testid="dev-weather-state"]') || {}).textContent || '', on: document.querySelector('[data-testid="dev-weather-overcast"]').classList.contains('on') }));
    ok(r.w === 'overcast' && r.g === 'overcast' && /overcast/.test(r.txt) && r.on, 'DEV「陰」→ overcast', r);
    let b = await care('play'); ok(b.shroom === 0.5 && b.ember === 1 && !b.tide, '陰天玩 → 菇傘 +0.5（v5 權重）＋火苗', b);
    await dclick('dev-weather-rain'); b = await care('rinse'); ok(b.tide === 1 && b.shroom === 1, '落雨沖洗 → 水珠＋菇傘', b);
    b = await care('play'); ok(!b.tide && b.shroom === 1, '落雨玩 → 唔計水珠（v4）', b);
    await dclick('dev-weather-clear'); b = await care('play'); r = await E(() => Glimmer.sim.weatherNow()); ok(r === 'clear' && !b.shroom, 'DEV「晴」→ clear、玩唔計菇傘', [r, b]);
    await dclick('dev-care-days-7'); r = await E(() => Glimmer.sim.careDaysCheck(__glimmer.state)); ok(r.ok && r.days >= r.need, 'DEV「照顧日 7」→ 燦光照顧日 ✓', r);
    await dclick('dev-care-days-0'); r = await E(() => Glimmer.sim.careDaysCheck(__glimmer.state)); ok(!r.ok && r.days === 0, 'DEV「清照顧日」→ ✗', r);
    await page.goto(BASE + (BASE.includes('?') ? '&' : '?') + 'weather=overcast'); await ready();
    r = await E(() => ({ w: Glimmer.sim.weatherNow(), g: __glimmer.weather })); ok(r.w === 'overcast', '?weather=overcast → overcast', r);
    await page.goto(BASE + (BASE.includes('?') ? '&' : '?') + 'weather=bogus'); await ready();
    r = await E(() => Glimmer.sim.weatherNow()); ok(r === 'clear', '?weather=bogus → clear', r);
  }

  console.log('# ⑤ v5 哄瞓（DEV 眼瞓 → 長撳團絨 → 瞓著、月眠 +1）');
  { await page.goto(BASE + '?q=high&hour=13&seed=21&ev=0&dev=1'); await ready(); await E(() => { window.__noSaveOnHide = true; });
    await juv({ cq: 40, prog: 0.3, b5: {} }); await closeModals();
    const dclick = (tid) => E((t) => document.querySelector('[data-testid="' + t + '"]').click(), tid);
    ok(await E(() => !!document.querySelector('[data-testid="dev-lull-row"]')), 'DEV 抽屜有月眠列（眼瞓／哄瞓）');
    await dclick('dev-drowsy'); await page.waitForTimeout(200);
    let r = await E(() => ({ d: Glimmer.sim.isDrowsy(__glimmer.state), e: __glimmer.state.needs.energy, txt: document.querySelector('[data-testid="dev-lull-state"]').textContent }));
    ok(r.d && /眼瞓/.test(r.txt), 'DEV「眼瞓」→ 團絨眼瞓', r);
    await shot('drowsy', true);
    const c = await E(() => { const r = document.getElementById('gl').getBoundingClientRect(), k = r.width / 195, b = window.Glimmer.ui.petHitBox(); return { x: r.left + (b.x + b.w / 2) * k, y: r.top + (b.y + b.h / 2) * k }; });
    await E(() => { const dp = document.getElementById('devp'); if (dp) dp.style.pointerEvents = 'none'; });
    const m0 = await E(() => ((__glimmer.state.evo.b5 || {}).juvenile || {}).moon || 0);
    await page.mouse.move(c.x, c.y); await page.mouse.down(); await page.waitForTimeout(900); await page.mouse.move(c.x + 6, c.y + 2); await page.waitForTimeout(150); await page.mouse.up(); await page.waitForTimeout(400);
    r = await E(() => ({ slp: __glimmer.state.sleeping, moon: ((__glimmer.state.evo.b5 || {}).juvenile || {}).moon || 0, lull: __glimmer.state.evo.lull, press: __glimmer.lastPetPress }));
    ok(r.slp && r.moon === m0 + 1 && r.lull && r.lull.n === 1, '長撳眼瞓團絨 → 瞓著＋月眠 +1', r);
    await page.waitForTimeout(800); await shot('lull-asleep', true);
    const per = await E(() => Glimmer.data.PARAMS.evo6.branch.lull.perNight);
    for (let i = 0; i < per + 1; i++) { await dclick('dev-drowsy'); await dclick('dev-lull'); }
    r = await E(() => ({ moon: __glimmer.state.evo.b5.juvenile.moon, n: __glimmer.state.evo.lull.n })); ok(r.n === per && r.moon === m0 + per, `每晚最多 ${per} 次計月眠`, r);
    await E(() => { const dp = document.getElementById('devp'); if (dp) dp.style.pointerEvents = ''; });
  }

  ok(!errs.length, '冇 console error', errs.slice(0, 5));
  await browser.close();
  console.log(`結果：${pass} 通過，${fail} 失敗`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('Error', e); process.exit(1); });
