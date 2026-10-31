/* node tools/fpet-bridge.test.js — snapshot v1/v2/v3＋狀態一變即寫（mock Capacitor、假計時器） */
const fs = require('fs'), vm = require('vm'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, 'fpet-bridge.js'), 'utf8');
let pass = 0, fail = 0;
const ok = (c, n, i) => { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? ' → ' + JSON.stringify(i) : '')); } };
function run(glimmer) {
  const timers = []; const writes = [];
  const win = { Capacitor: { isNativePlatform: () => true, Plugins: {
    Preferences: { set: (o) => { writes.push(JSON.parse(o.value)); return Promise.resolve(); } },
    FloatingPet: { drainQueue: () => Promise.resolve({ items: [] }) } } }, __glimmer: glimmer };
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
  console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})();
