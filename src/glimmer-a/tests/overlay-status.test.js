/* 浮動 overlay snapshot v3／v4：node tests/overlay-status.test.js（心情／瞌覺／需求＋推算率同 step() 一致） */
const S = require('../src/sim.js');
const D = require('../src/data.js');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + JSON.stringify(info) : '')); } }
S.setHourFn(() => 12);
const at = (stage, needs, extra) => { const s = S.newState(1e12, 7); s.stage = stage; s.form = D.isBig(stage) ? 'soft' : null; s.poops = 0; s.sleeping = false; Object.assign(s.needs, { hunger: 80, mood: 80, clean: 80, energy: 80 }, needs || {}); return Object.assign(s, extra || {}); };

let o = S.overlayStatus(S.newState(1e12, 1));
ok(o.egg === true && o.urgent === null && o.sleeping === false, '光卵：冇表情／冇需求提示', o);
o = S.overlayStatus(at('juvenile'));
ok(!o.egg && o.moodBand === 'happy' && o.urgent === null && !o.sleeping, '需求 80 → 開心、冇提示', o);
o = S.overlayStatus(at('juvenile', { mood: 50 })); ok(o.moodBand === 'ok', '心情 50 → ok');
o = S.overlayStatus(at('juvenile', { mood: 20 })); ok(o.moodBand === 'sad' && o.urgent === 'mood', '心情 20 → 唔開心＋提示想玩', o);
o = S.overlayStatus(at('adult', { hunger: 20 })); ok(o.urgent === 'hunger' && o.level === 20 && o.moodBand === 'happy', '肚餓 20 → 提示 hunger（最急）', o);
o = S.overlayStatus(at('adult', { hunger: 25, clean: 10 })); ok(o.urgent === 'clean' && o.level === 10, '兩項低 → 提最低嗰項（clean 10）', o);
o = S.overlayStatus(at('adult', { hunger: 30 })); ok(o.urgent === null, '剛好 30 唔提（<30 先提，同 HUD 一致）');
o = S.overlayStatus(at('adult', { energy: 40 }, { sleeping: true }));
ok(o.sleeping && o.rate.energy > 0 && o.rateAwake.energy < 0 && o.rate.hunger > o.rateAwake.hunger, '瞓緊：精力回升、其他衰減慢（×0.3）', o.rate);
ok(o.wakeAt === D.PARAMS.sleepWakeAt && o.floor === D.PARAMS.offlineNeedFloor && o.warnAt === 30, 'wakeAt／floor／warnAt 跟 PARAMS');
// 推算率 = step() 實際每小時變化（醒／瞓、有便便、各階段）
for (const [st, slp, poops] of [['sprout', false, 0], ['juvenile', false, 2], ['adult', true, 1], ['elder', false, 0], ['newborn', true, 0]]) {
  const s = at(st, { hunger: 70, mood: 70, clean: 70, energy: slp ? 40 : 70 }, { sleeping: slp, poops, poopTimer: 0 });
  const r = S.overlayStatus(s), before = Object.assign({}, s.needs);
  S.advance(s, 3600, {}, 60);
  const diff = D.NEED_KEYS.map(k => Math.abs((s.needs[k] - before[k]) - r.rate[k]));
  ok(diff.every(d => d < 0.01), `${st}${slp ? '（瞓）' : ''} poops=${poops}：rate＝step 1h 實際變化`, { rate: r.rate, got: D.NEED_KEYS.map(k => +(s.needs[k] - before[k]).toFixed(3)) });
}
// v4：info（長按選單狀態：名／階段名／形態名／進度／幾日大），只讀
{ const s0 = S.newState(1e12, 3); const j0 = JSON.stringify(s0); const i0 = S.overlayStatus(s0).info;
  ok(i0 && i0.name === '團絨' && i0.stageName === '光卵' && i0.evoForm === 'evo_egg' && i0.days === 0 && i0.form === null, 'v4 光卵 info', i0);
  ok(JSON.stringify(s0) === j0, 'v4 overlayStatus 只讀（唔改 state）'); }
for (const [st, name, sub, ev] of [['newborn', '絨點', '絨點仔', 'evo_dot'], ['sprout', '芽崽', '絨芽', 'evo_sprout'], ['juvenile', '跳跳期', '跳跳絨', 'evo_hop']]) {
  const i = S.overlayStatus(at(st)).info; ok(i.stageName === name && i.sub === sub && i.evoForm === ev && i.formName === null, `v4 ${name} 階段名＋sub`, i); }
{ const s = at('adult', {}, { form: 'dust', growthSec: 3.5 * 86400, ageSec: 5.2 * 86400 }); const i = S.overlayStatus(s).info;
  ok(i.stageName === '守夜者' && i.formName === '微塵' && i.sub === '微塵形態' && i.evoForm === 'evo_guard_dust', 'v4 守夜者・微塵', i);
  ok(Math.abs(i.progress - 0.5) < 0.001 && i.stageH === 168 && Math.abs(i.leftH - 84) < 0.01 && i.days === 5, 'v4 進度 50%／剩 84h／5 日大', i); }
{ const s = at('elder', {}, { form: 'lumi', fadeReady: true }); const i = S.overlayStatus(s).info;
  ok(i.stageName === '靜光' && i.formName === '螢絨' && i.sub === '螢絨形態 · 準備化光' && i.evoForm === 'evo_still_lumi', 'v4 靜光・螢絨（準備化光）', i); }
{ const s = at('adult', {}, { form: 'bright' }); const i = S.overlayStatus(s).info; ok(i.formName === '燦光' && i.evoForm === 'evo_guard_radiant', 'v4 燦光 → evo_guard_radiant', i); }
{ const i = S.overlayStatus(at('adult', { hunger: 5 })).info; ok(i.unwell === (5 < D.PARAMS.sickThreshold), 'v4 unwell 跟 isUnwell', i); }
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
