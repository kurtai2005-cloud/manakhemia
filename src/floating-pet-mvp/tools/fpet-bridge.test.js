/* node tools/fpet-bridge.test.js — snapshot v1/v2/v3/v4＋狀態一變即寫（mock Capacitor、假計時器） */
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
  console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
})();
