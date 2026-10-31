/* 浮動 overlay snapshot v3：node tests/overlay-status.test.js（心情／瞌覺／需求＋推算率同 step() 一致） */
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
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
