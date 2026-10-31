/* v10.2→v10.3 經濟＋路線測試（遊策 A／§7 v10.3）：node tests/economy-v102.test.js [N 分佈隻數=1000]
   v10.3：委託逐張 +4、3 張齊 +3、未完成留多 1 日；懸浮團絨每日摸頭 2 下（overlay {k:pat}，計入摸頭委託）＝遊測假設。
   ① 6 個玩家類型（tools/route-sweep.js 同一套時間表／隨機性）各 200 seed × 7 日：每日星星碎中位 15–30
      （委託＝餵／玩／摸頭池；每次上線撳團絨 2 下；懸浮每日執 5 粒＝遊測假設；疏玩隔日上 → 計「有上線嗰日」，另列全 7 日）。
   ② 路線分佈（載入 systems.js＝有委託路線分，N×6 表）：9 條路全體 vs 遊測 v10 鎖定目標 ±3pt。 */
require('../src/systems.js');
const SW = require('../tools/route-sweep.js'), D = require('../src/data.js');
const NARG = +(process.argv.slice(2).find(a => /^\d+$/.test(a))) || 1000;
let pass = 0, fail = 0; const FP = 2;   // v10.3 懸浮摸頭／日
function ok(c, n, i) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? '  → ' + (typeof i === 'string' ? i : JSON.stringify(i)) : '')); } }
const med = (a) => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; };
console.log('① 7 日星星碎（每日中位，200 seed／類型）');
const ECON = {};
for (const name of Object.keys(SW.SCHED)) {
  const playDays = [], allDays = [], noDrop = [];
  for (let sd = 1; sd <= 200; sd++) {
    const r = SW.run(name, sd, { days: 7, drops: 5, fpats: FP }), r0 = SW.run(name, sd, { days: 7, drops: 0, fpats: FP });
    const keys = []; for (let d = 0; d < 7; d++) keys.push(require('../src/sim.js').dayKey(new Date(2026, 10, 2).getTime() + d * 864e5));
    for (const k of keys) { const v = r.shards[k] || 0; allDays.push(v); if (r.played[k]) { playDays.push(v); noDrop.push(r0.shards[k] || 0); } }
  }
  const m = med(playDays), ma = med(allDays), m0 = med(noDrop), mx = Math.max(...allDays);
  ECON[name] = { median: m, medianAll7: ma, medianNoDrop: m0, max: mx };
  console.log(`  ${name}　上線日中位 ${m}｜全 7 日中位 ${ma}｜冇懸浮粒 ${m0}｜最高 ${mx}`);
  ok(m >= 15 && m <= 30, `${name}：每日星星碎中位 ${m} ∈ [15, 30]`);
  ok(mx <= 30, `${name}：每日唔超過上限 30（最高 ${mx}）`);
}
console.log(`② 路線分佈（N=${NARG}×6 表，有委託路線分）vs 遊測鎖定目標 ±${SW.FLAG_PT}pt`);
const R = SW.main(NARG, true, { fpats: FP });
for (const f of D.BRANCHES) { const d = +(R.total[f] - SW.TARGET[f]).toFixed(2); ok(Math.abs(d) <= SW.FLAG_PT, `${D.FORM_NAME[f]} ${R.total[f]}%（目標 ${SW.TARGET[f]}，差 ${d >= 0 ? '+' : ''}${d}）`); }
const shMax = Math.max(...Object.values(R.tables).map(t => t.pct.shroom)); ok(shMax <= 30, `每表菇傘 ≤30%（最高 ${shMax}%：${Object.entries(R.tables).map(([n, t]) => n + ' ' + t.pct.shroom).join('／')}）`);
console.log(`  疏玩實數：上線日中位 ${ECON['疏玩'].median}｜全 7 日中位 ${ECON['疏玩'].medianAll7}｜冇懸浮粒 ${ECON['疏玩'].medianNoDrop}`);
if (process.env.ECON_JSON) require('fs').writeFileSync(process.env.ECON_JSON, JSON.stringify({ econ: ECON, total: R.total, target: SW.TARGET, tables: R.tables, fpats: FP }, null, 1));
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exitCode = fail ? 1 : 0;
