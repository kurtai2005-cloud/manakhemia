/* node tools/fpet-bridge.test.js — snapshot v1/v2/v3/v4/v5＋狀態一變即寫（mock Capacitor、假計時器） */
const fs = require('fs'), vm = require('vm'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'fpet-bridge.js'), 'utf8');
let pass = 0, fail = 0;
const ok = (c, n, i) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? ' → ' + JSON.stringify(i) : '')); } };
function run(glimmer, items) {
  const timers = []; const writes = [];
  const win = { Capacitor: { isNativePlatform: () => true, Plugins: {
    Preferences: { set: (o) => { writes.push(JSON.parse(o.value)); return Promise.resolve(); } },
    FloatingPet: { drainQueue: () => Promise.resolve({ items: items || [] }) } } }, __glimmer: glimmer };
  const ctx = { window: win, document: { addEventListener() {}, visibilityState: 'visible' }, localStorage: { getItem: () => null, setItem() {} }, console: { log() {}, warn() {} },
    setInterval: (f, ms) => timers.push({ f, ms }), setTimeout: (f) => f(), Date, Math, JSON, Promise };
  vm.runInNewContext(src, ctx);
  return { win, writes, tick: (ms) => timers.filter(t => t.ms === ms).forEach(t => t.f()) };
}
const needs = (o) => Object.assign({ hunger: 80, mood: 80, clean: 80, energy: 80 }, o || {});
(async () => {
  // v1：冇 evo（舊 www）→ 照舊 form／mood，加 v3 簡單狀態
  let g = { state: { stage: 'sprout', needs: needs(), sleeping: false } };
  let r = run(g); await new Promise(s => setImmediate(s));
  let w = r.writes[r.writes.length - 1];
  ok(w && w.form === 'sprout' && w.mood === 80, '舊 www：form／mood 照寫', w);
  ok(w.v === 3 && w.moodBand === 'happy' && w.sleeping === false && w.needs.urgent === null && w.needs.rate === null, '舊 www：v3 簡單狀態（冇推算率）', w);
  // v2 欄：有 overlayInfo 冇 overlayStatus
  g = { state: { stage: 'adult', form: 'bright', needs: needs({ hunger: 12 }), sleeping: false }, evo: { overlayInfo: () => ({ stage: 'adult', evoForm: 'guard_bright', size: 64, pivot: [32, 61], sizeDp: 104 }) } };
  r = run(g); await new Promise(s => setImmediate(s)); w = r.writes[r.writes.length - 1];
  ok(w.form === 'radiant' && w.sizeDp === 104 && w.stage === 'adult', 'v2 欄保留（form／sizeDp／stage）', w);
  ok(w.needs.urgent === 'hunger' && w.needs.level === 12, '肚餓 12 → urgent hunger', w.needs);
  // v3：overlayStatus＋即寫
  const st = { egg: false, moodBand: 'happy', sleeping: false, urgent: null, level: 80, warnAt: 30, vals: needs(), rate: { hunger: -6, mood: -4, clean: -3.9, energy: -5 }, rateAwake: { hunger: -6, mood: -4, clean: -3.9, energy: -5 }, floor: 20, wakeAt: 100 };
  g = { state: { stage: 'juvenile', needs: needs(), sleeping: false }, evo: { overlayInfo: () => ({ stage: 'juvenile', size: 32, sizeDp: 52 }), overlayStatus: () => st } };
  r = run(g); await new Promise(s => setImmediate(s));
  const n0 = r.writes.length; w = r.writes[n0 - 1];
  ok(w.v === 3 && w.needs.rate.hunger === -6 && w.needs.floor === 20 && w.needs.wakeAt === 100, 'v3：推算率／floor／wakeAt', w.needs);
  r.tick(2000); ok(r.writes.length === n0, '狀態冇變 → 2 秒檢查唔寫');
  st.sleeping = true; r.tick(2000); ok(r.writes.length === n0 + 1 && r.writes[n0].sleeping === true, '瞓覺 → 即寫', r.writes.length);
  st.urgent = 'hunger'; st.level = 25; r.tick(2000); ok(r.writes.length === n0 + 2 && r.writes[n0 + 1].needs.urgent === 'hunger', '肚餓 → 即寫');
  st.moodBand = 'sad'; r.tick(2000); ok(r.writes.length === n0 + 3 && r.writes[n0 + 2].moodBand === 'sad', '唔開心 → 即寫');
  r.tick(30000); ok(r.writes.length === n0 + 4, '30 秒定時照寫（舊行為保留）');
  // v4：overlayStatus().info → snap.info；evoForm／日數一變即寫
  const info = { name: '團絨', gen: 1, stage: 'adult', stageName: '守夜者', sub: '柔光形態', form: 'soft', formName: '柔光', evoForm: 'evo_guard_soft', progress: 0.25, stageH: 168, leftH: 126, ageSec: 400000, days: 4, unwell: false, fadeReady: false };
  const st4 = Object.assign({}, st, { sleeping: false, urgent: null, moodBand: 'happy', info });
  let ev = 'evo_guard_soft';
  g = { state: { stage: 'adult', form: 'soft', needs: needs(), sleeping: false }, evo: { overlayInfo: () => ({ stage: 'adult', evoForm: ev, size: 44, sizeDp: 72 }), overlayStatus: () => st4 } };
  r = run(g); await new Promise(s => setImmediate(s));
  let m0 = r.writes.length; w = r.writes[m0 - 1];
  ok(w.v === 4 && w.info.stageName === '守夜者' && w.info.formName === '柔光' && w.info.days === 4 && w.evoForm === 'evo_guard_soft' && w.needs.vals, 'v4：info＋v3 欄照寫', w);
  ev = 'evo_guard_dust'; g.state.form = 'dust'; r.tick(2000); ok(r.writes.length === m0 + 1 && r.writes[m0].evoForm === 'evo_guard_dust', '同大細換分支（柔光→微塵）→ 即寫', r.writes.length);
  info.days = 5; r.tick(2000); ok(r.writes.length === m0 + 2 && r.writes[m0 + 1].info.days === 5, '幾日大變 → 即寫');
  r.tick(2000); ok(r.writes.length === m0 + 2, 'v4 冇變 → 唔寫');
  // evo6 v8：open_game（撳兩下開 game）→ overlayOpenGame(t)；唔佔 mood 上限；舊 www 冇 API → 當普通互動
  { const calls = []; let saved = 0;
    g = { state: { stage: 'juvenile', needs: needs({ mood: 50 }), sleeping: false }, save: () => { saved++; }, evo: { overlayInfo: () => ({ stage: 'juvenile', size: 38, sizeDp: 62 }), overlayOpenGame: (t) => { calls.push(t); return { ok: calls.length === 1 }; } } };
    r = run(g, [{ t: 1000, k: 'tap' }, { t: 2000, k: 'open_game' }, { t: 3000, k: 'open_game' }]); await new Promise(s => setImmediate(s)); await new Promise(s => setImmediate(s));
    ok(calls.join() === '2000,3000' && g.state.needs.mood === 51 && saved === 1, 'open_game → overlayOpenGame(t) ×2（遊戲管冷卻）；tap → mood +1', { calls, mood: g.state.needs.mood, saved });
    const g2 = { state: { stage: 'juvenile', needs: needs({ mood: 50 }), sleeping: false }, save() {} };
    r = run(g2, [{ t: 2000, k: 'open_game' }]); await new Promise(s => setImmediate(s)); await new Promise(s => setImmediate(s));
    ok(g2.state.needs.mood === 51, '舊 www（冇 overlayOpenGame）→ open_game 當普通互動 mood +1', g2.state.needs.mood); }
  // v5（systems12）：snap.sys12＋簽名（設定 ts／tier／room 一變即寫）
  const x12 = { v: 1, egg: false, bond: { v: 46, tier: 2 }, voice: { chance: 0.3, cooldownSec: 600, showSec: 4, newestTierPct: 50, lastAt: 0, lines: [['a'], ['b']] },
    surp: { on: { drop: true, water: false, sleep: false }, waterH: 2, sleepAt: '23:00', ts: 0, drop: { minH: 2, maxH: 4, perDay: 5, showSec: 30, day: '2026-11-01', room: 5 }, water: { fromH: 9, toH: 22 }, sleepWinMin: 60, showSec: 6, lines: {} }, shards: 3 };
  const applied = [];
  g = { state: { stage: 'adult', form: 'soft', needs: needs({ mood: 50 }), sleeping: false }, save() { g.saved = (g.saved || 0) + 1; },
    evo: { overlayInfo: () => ({ stage: 'adult', evoForm: 'evo_guard_soft', size: 44, sizeDp: 72 }), overlayStatus: () => st4, sys12Overlay: () => JSON.parse(JSON.stringify(x12)), sys12Apply: (items) => { applied.push(items); return { drop: 1, voice: 1, set: 1 }; } } };
  const q = [{ t: Date.now(), k: 'tap' }, { t: Date.now(), k: 'drop' }, { t: Date.now(), k: 'voice', line: 'a' }, { t: Date.now(), k: 'menu' }, { t: Date.now(), k: 'set', key: 'water', val: true }, { t: Date.now(), k: 'remind', what: 'water' }];
  r = run(g, q); await new Promise(s => setImmediate(s)); await new Promise(s => setImmediate(s));
  m0 = r.writes.length; w = r.writes[m0 - 1];
  ok(w.v === 5 && w.sys12 && w.sys12.bond.tier === 2 && w.sys12.surp.drop.room === 5 && w.sys12.voice.lines.length === 2 && w.info, 'v5：snap.sys12（親密／心聲句／小驚喜設定）＋v4 欄照寫', w);
  ok(applied.length === 1 && applied[0].map(i => i.k).join() === 'drop,voice,set,remind', 'replay：systems12 item 交俾 sys12Apply', applied);
  ok(g.state.needs.mood === 52, 'replay：只有舊互動計 mood（2 個 → +2；systems12 item 唔加）', g.state.needs.mood);
  x12.surp.ts = 123; r.tick(2000); ok(r.writes.length === m0 + 1 && r.writes[m0].sys12.surp.ts === 123, '設定改咗（ts）→ 即寫');
  x12.surp.drop.room = 4; r.tick(2000); ok(r.writes.length === m0 + 2, '今日星星碎餘額變 → 即寫');
  x12.bond.tier = 3; r.tick(2000); ok(r.writes.length === m0 + 3, '親密 tier 升 → 即寫');
  r.tick(2000); ok(r.writes.length === m0 + 3, 'v5 冇變 → 唔寫');
  x12.wx = { days: { '2026-11-01': 'clear' }, manual: null, season: 'autumn' }; r.tick(2000); ok(r.writes.length === m0 + 4 && r.writes[m0 + 3].sys12.wx.days['2026-11-01'] === 'clear', 'v10.2：snap.sys12.wx 天氣出現 → 即寫');
  x12.wx.manual = 'rain'; r.tick(2000); ok(r.writes.length === m0 + 5 && r.writes[m0 + 4].sys12.wx.manual === 'rain', 'v10.2：DEV 轉落雨（manual）→ 即寫（懸浮撐葉）');
  r.tick(2000); ok(r.writes.length === m0 + 5, 'v10.2：天氣冇變 → 唔寫');
  // 舊 www 冇 sys12Apply：systems12 item 照丟（唔當互動加 mood）
  g = { state: { stage: 'adult', form: 'soft', needs: needs({ mood: 50 }), sleeping: false }, save() {} };
  r = run(g, [{ t: Date.now(), k: 'drop' }, { t: Date.now(), k: 'tap' }]); await new Promise(s => setImmediate(s)); await new Promise(s => setImmediate(s));
  ok(g.state.needs.mood === 51 && r.writes[r.writes.length - 1].v === 3 && !r.writes[r.writes.length - 1].sys12, '舊 www：冇 sys12 → v3，drop 唔加 mood', g.state.needs.mood);
  console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})();
