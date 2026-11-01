/* systems12b 小圃 × 路線分佈（遊策 2026-11-01 #8）：node tests/route-garden.test.js
   開花 +bloomPts 經 systems.addRoutePts 入當階段路線分（判路時照 25% cap）；日菊冇路線分。
   tools/route-sweep.js --garden 用同一個 gardenHook；完整 1000 隻分佈見 sweep（呢度細樣本 smoke）。 */
const S = require('../src/sim.js'), X = require('../src/systems.js'), B = require('../src/systems2.js'), D = require('../src/data.js');
const SW = require('../tools/route-sweep.js'), G = D.PARAMS.systems12b.garden;
let pass = 0, fail = 0;
function ok(c, n, i) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? '  → ' + JSON.stringify(i) : '')); } }
const T0 = new Date(2026, 10, 2, 9, 0).getTime(), DAY = 864e5;
{
  const s = S.newState(T0, 77); s.stage = 'juvenile'; X.st(s).wallet.total = 30;
  const st = { gshards: 0 }, h = SW.gardenHook(5, 'lead', st), b5 = () => JSON.stringify((s.evo.b5sys || {}).juvenile || {});
  for (let d = 0; d < 3; d++) h(s, T0 + d * DAY);
  const pts = (s.evo.b5sys || {}).juvenile || {}, sum = Object.values(pts).reduce((a, b) => a + b, 0);
  ok(st.blooms === 3, '3 盆淋足 3 日 → 3 朵開花', st);
  const routed = Object.values(st.byRoute).reduce((a, b) => a + b, 0);
  ok(Math.abs(sum - routed * G.bloomPts) < 1e-9, '每朵有路線嘅花 +' + G.bloomPts + ' 入跳跳期路線分（日菊 0）', { pts, byRoute: st.byRoute });
  const s2 = S.newState(T0, 78); s2.stage = 'juvenile'; X.st(s2).wallet.total = 6; B.plant(s2, 0, 'daisy', T0); [0, 1, 2].forEach(d => B.water(s2, 0, T0 + d * DAY));
  ok(!((s2.evo.b5sys || {}).juvenile) && s2.dexHint.bright, '日菊：冇路線分，記燦光圖鑑提示');
}
{
  const r = SW.main(40, true, { garden: 'rand', drops: 5, fpats: 2, gshards: 999 });
  ok(r.garden && r.garden.blooms > 0, 'route sweep --garden 有開花（40×6 隻，壓力：種子任買）', r.garden);
  ok(D.BRANCHES.every(f => r.total[f] >= 0) && Math.abs(Object.values(r.total).reduce((a, b) => a + b, 0) - 100) < 0.5, '分佈加埋 100%', r.total);
}
{
  // 遊策 2026-11-01：route sweep --mg2 經真 gameFinish 玩小遊戲 v2；火苗路線分每日 routeGamesPerDay 局（同浮動局共用）
  const r = SW.main(40, true, { garden: 'rand', drops: 5, fpats: 2, mg2: true }), r1 = SW.main(40, true, { garden: 'rand', drops: 5, fpats: 2, mg2: true, mgcap: 'none' });
  ok(r.mg2 && r.mg2.games > 0 && r.mg2.route > 0 && r.mg2.route < r.mg2.games, 'route sweep --mg2：有玩 v2，上限 ' + D.PARAMS.minigames2.routeGamesPerDay + ' 局令部分唔計火苗', r.mg2);
  ok(r1.mg2.route === r1.mg2.games && r1.total.ember > r.total.ember && D.PARAMS.minigames2.routeGamesPerDay === 2, '--mgcap none 試算：全部計、火苗更高（跑完還原 config）', [r.total.ember, r1.total.ember]);
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
