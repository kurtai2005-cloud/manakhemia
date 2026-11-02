/* economy-6b1.test — 6b.1 遊測 P1：屋仔碎商店買齊要幾多日（目標 ≥5 日）。node tests/economy-6b1.test.js [seed 數=200]
   收入三個池（每日上限 30＋12＋5＝47，data.js SHARD_DAILY_TOTAL_CAP）：
   ・舊來源：tools/route-sweep.js 真 sim（同 economy-sys12b 一樣：委託、摸頭 2、懸浮執 5 粒；每次上線 40% 開一局小遊戲 v2 bot＋3 段散步＋徽章 tick）；
     唔種花（唔使碎）→ 收入偏高＝保守。上線日先計；唔上線嗰日 0。
   ・5b 遠足／工作：當每日都攞足 12（保守，最快）。
   ・6b 步數：真 long6b.CFG（2000 步 1 碎、每日 ≤5）；步數每日抽：勤力 N(9000, 2500)、夜貓 N(6000, 2500)（≥0）。
   由屋仔開咗嗰日（第 1 日，錢包 0）開始儲，第幾日累積 ≥ 商店總價＝買齊日。P10＝最快嗰 10%。 */
const S = require('../src/sim.js'), X = require('../src/systems.js'), B = require('../src/systems2.js'), HS = require('../src/house.js'), RW = require('../src/long6b.js');
const SW = require('../tools/route-sweep.js'), P = require('../src/data.js').PARAMS, M2 = require('../src/minigames2.js'), BOT = require('./mg2-bots.js');
let pass = 0, fail = 0;
function ok(c, n, i) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? '  → ' + JSON.stringify(i) : '')); } }
const N = +process.argv[2] || 200, DAYS = 12, T0 = new Date(2026, 10, 2).getTime(), keys = []; for (let d = 0; d < DAYS; d++) keys.push(S.dayKey(T0 + d * 864e5));
const TOTAL = Object.values(HS.FURN).filter(f => f.src === 'shop').reduce((a, f) => a + f.price, 0), OLD = TOTAL - HS.FURN.wall_shoes.price;
const STEPS = { 勤力: [9000, 2500], 夜貓: [6000, 2500] }, L5B = 12;
const hookFor = (seed) => { const rng = S.makeRng(seed * 7919 + 503); return (s, now) => { if (s.stage === 'egg') return;
  if (rng() < 0.4) { const ks = M2.fireflyOpen(new Date(now).getHours()) ? ['bounce', 'ghide', 'firefly'] : ['bounce', 'ghide'], k = ks[Math.floor(rng() * ks.length)]; const g = BOT.playBot(M2, k, (rng() * 1e9) | 1, rng(), rng); B.gameFinish(s, k, g.score, now, k === 'ghide' ? { firstHits: g.firstHits } : {}); }
  for (let i = 0; i < 3; i++) B.walkRoll(s, now, { rng }); B.tick(s, now); }; };
const gauss = (r) => Math.sqrt(-2 * Math.log(1 - r())) * Math.cos(2 * Math.PI * r());
const dayOf = (inc, need) => { let c = 0; for (let d = 0; d < inc.length; d++) { c += inc[d]; if (c >= need) return d + 1; } return 99; };
const pct = (a, q) => { const b = a.slice().sort((x, y) => x - y); return b[Math.min(b.length - 1, Math.floor(b.length * q))]; };
console.log('① 規格：總價、上限');
ok(TOTAL === 190 && OLD === 165, '商店總價 190（舊 7 件 165＋散步鞋架 25）', { TOTAL, OLD });
ok(P.SHARD_DAILY_TOTAL_CAP === 30 + L5B + RW.CFG.shardCap, '每日上限 47＝30＋12＋5');
ok(Math.ceil(TOTAL / P.SHARD_DAILY_TOTAL_CAP) >= 5 && Math.ceil(OLD / P.SHARD_DAILY_TOTAL_CAP) === 4, '理論最快：190 → 第 ' + Math.ceil(TOTAL / 47) + ' 日（165 → 第 4 日＝遊測 P1 問題）');
console.log('② sim：勤力／夜貓 × ' + N + ' seed');
for (const name of ['勤力', '夜貓']) {
  const dn = [], d0 = [], daily = [];
  for (let sd = 1; sd <= N; sd++) {
    const r = SW.run(name, sd, { days: DAYS, drops: 5, fpats: 2, onSession: hookFor(sd) }), rs = S.makeRng(sd * 7919 + 601), [mu, sg] = STEPS[name];
    const inc = keys.map(k => { const steps = Math.max(0, mu + sg * gauss(rs)), b6 = Math.min(RW.CFG.shardCap, Math.floor(steps / RW.CFG.stepsPerShard)), leg = r.played[k] ? Math.min(30, r.shards[k] || 0) : 0; return leg + L5B + b6; });
    inc.forEach(v => daily.push(v)); dn.push(dayOf(inc, TOTAL)); d0.push(dayOf(inc, OLD));
  }
  const p10 = pct(dn, 0.1), p10o = pct(d0, 0.1), med = pct(dn, 0.5), mx = Math.max(...daily);
  console.log(`  ${name}　每日收入中位 ${pct(daily, 0.5)}（最高 ${mx}）｜買齊 190：P10 第 ${p10} 日、中位 ${med}、P90 ${pct(dn, 0.9)}｜舊 165：P10 第 ${p10o} 日`);
  ok(mx <= 47, `${name}：每日收入 ≤47（最高 ${mx}）`);
  ok(p10 >= 5, `${name}：買齊 190 P10 ≥5 日（第 ${p10} 日）`, { p10, med });
  ok(Math.max(...dn) < 99, `${name}：${DAYS} 日內全部買得齊（唔會太慢）`, Math.max(...dn));
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exitCode = fail ? 1 : 0;
