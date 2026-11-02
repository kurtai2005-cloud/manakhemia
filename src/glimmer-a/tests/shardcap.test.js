/* 5b.1（遊策裁定）星星碎每日上限：兩個池分開 —— 舊來源（委託＋其他）≤30、long5b（工作＋遠足）≤12、合共 ≤ PARAMS.SHARD_DAILY_TOTAL_CAP（42）；
   填滿一個池唔會搶走另一個池嘅位。node tests/shardcap.test.js */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), HS = require('../src/house.js'), F = require('../src/long5a.js'), X = require('../src/systems.js'), B = require('../src/long5b.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
const NOW = at(0, 12);
function fam() { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; s.dex = ['tide']; S2.noteElder(s, at(-25, 12)); S2.deliver(s, at(-24, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(-20, 12)); Object.assign(p, { intim: 90, rel: 'family' }); HS.ensure(s, at(-5, 12));
  const o = F.st(s); o.init = at(-5, 12);
  const R = (id, kind, fk, name, gen) => ({ id, kind, fk, name, gen: gen || 0, form: kind === 'tr' ? 'moon' : null, room: 'room1', at: at(-3, 12), snap: {} });
  o.res.push(R('tr0', 'tr', 'evo_still_moon', '月月', 0), R('kidA', 'kid', 'A3', '星仔'), R('kidB', 'kid', 'B3', '棉棉'), R('trX', 'tr', 'tide', '潮潮', 0));
  return s; }
const W = (s) => X.st(s).wallet.total;
const LEG = D.PARAMS.evo6.branch.systems.stardustDailyCap, L5B = B.CFG.capPerDay, TOT = D.PARAMS.SHARD_DAILY_TOTAL_CAP;
const legToday = (s, t) => X.wallet(s, t).today, b5Today = (s, t) => B.today(s, t).sh;
const fillLeg = (s, t) => { let g = 0; for (let i = 0; i < 40; i++) { g += X.grant(s, 3, i % 2 ? 'drop' : 'quest', t); } return g; };
const fill5b = (s, t) => { let g = 0; for (let i = 0; i < 40; i++) g += B.earn(s, 4, t, 'post'); return g; };

console.log('⓪ 常數');
ok(TOT === 42, 'PARAMS.SHARD_DAILY_TOTAL_CAP＝42', TOT);
ok(LEG === 30 && L5B === 12, '舊來源 30、long5b 12', { LEG, L5B });
ok(LEG + L5B === TOT, '30＋12＝42（兩池分開，加埋＝合共上限）');

console.log('① 各自上限');
{ const s = fam(), t = at(0, 12), w0 = W(s); const g = fillLeg(s, t);
  ok(g === LEG && legToday(s, t) <= 30, '舊來源每日 ≤30', { g, today: legToday(s, t) }); ok(W(s) - w0 === g, '錢包加返舊來源嗰份'); }
{ const s = fam(), t = at(0, 12); const g = fill5b(s, t);
  ok(g === L5B && b5Today(s, t) <= 12, 'long5b 每日 ≤12', { g, sh: b5Today(s, t) }); }

console.log('② 互不搶位');
{ const s = fam(), t = at(0, 12), w0 = W(s); const a = fillLeg(s, t), b = fill5b(s, t);
  ok(a === 30 && b === 12, '先滿舊來源 → long5b 照有 12', { a, b }); ok(W(s) - w0 === 42 && W(s) - w0 <= TOT, '合共 42 ≤ 上限', W(s) - w0); }
{ const s = fam(), t = at(0, 12), w0 = W(s); const b = fill5b(s, t), a = fillLeg(s, t);
  ok(a === 30 && b === 12, '先滿 long5b → 舊來源照有 30', { a, b }); ok(W(s) - w0 === TOT, '合共＝42', W(s) - w0); }
{ const s = fam(), t = at(0, 12); let tot = 0; for (let i = 0; i < 60; i++) tot += (i % 3 ? X.grant(s, 2, 'drop', t) : B.earn(s, 2, t, 'job')) + (i % 5 ? 0 : X.grant(s, 4, 'quest', t));
  ok(legToday(s, t) <= 30 && b5Today(s, t) <= 12 && tot <= TOT, '交叉入帳：舊 ≤30、5b ≤12、合共 ≤42', { leg: legToday(s, t), b5: b5Today(s, t), tot }); }

console.log('③ 翌日重置');
{ const s = fam(), t = at(0, 12); fillLeg(s, t); fill5b(s, t); const t2 = at(1, 12); const a = fillLeg(s, t2), b = fill5b(s, t2);
  ok(a === 30 && b === 12, '第二日兩個池都重新開', { a, b }); }

console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
