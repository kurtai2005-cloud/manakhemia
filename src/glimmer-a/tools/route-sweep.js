/* §7 平衡修訂 v4 掃描（俾遊測調 config 用，唔係 gating test）：node tools/route-sweep.js [每表隻數=200]
   6 個代表時間表 × N 個 seed，由芽崽行到守夜者，統計 9 條路分佈同目標。
   v5：清便便只清真實便便（即清 ≤crystalQuickSec 先計晶角）、眼瞓時 LULL 機會哄瞓；目標每表菇傘 ≤30%。
   v4 玩家隨機性：每次上線 ±90 分鐘、漏上線（MISS）、每個動作有機會唔做＋隨機加一個動作；天氣每 6 個鐘隨機（晴／陰／雨）；照顧日用模擬時鐘。
   數值全部讀 PARAMS.evo6.branch；時間表係呢度自訂嘅近似（遊測正式表可替換 SCHED）。 */
const S = require('../src/sim.js'), D = require('../src/data.js'), P = D.PARAMS;
const N = +process.argv[2] || 200;
const JIT = 90, MISS = 0.15, LULL = 0.5, SKIP_ACT = 0.2, EXTRA_ACT = 0.3, WX = [['clear', 0.6], ['overcast', 0.25], ['rain', 0.15]];
const ACTS = ['feed', 'play', 'rinse', 'poop'];
// 每個時間表：上線鐘點、每次做咩（feed／play／rinse／poop）；everyOtherDay＝隔日先上
const SCHED = {
  勤力: { hours: [8, 11, 14, 17, 20], acts: ['feed', 'play', 'rinse', 'poop'] },
  普通: { hours: [8, 13, 19], acts: ['feed', 'play', 'poop'] },
  疏玩: { hours: [20], acts: ['feed', 'play'], everyOtherDay: true },
  夜貓: { hours: [18, 22, 0, 1], acts: ['feed', 'play'] },
  早起: { hours: [6, 7, 8, 12], acts: ['feed', 'rinse', 'play'] },
  餵食狂: { hours: [9, 12, 15, 18], acts: ['feed', 'feed', 'feed', 'play'] },
};
function run(name, seed) {
  const sc = SCHED[name], rng = S.makeRng ? S.makeRng(seed * 7919 + 13) : Math.random, T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
  let now = T0 + 8 * 3600e3, wx = 'clear';
  S.setHourFn(() => new Date(now).getHours() + new Date(now).getMinutes() / 60); S.setNowFn(() => now); S.setWeatherFn(() => wx);
  const s = S.newState(now, seed); s.stage = 'sprout'; s.growthSec = 0; s.cq = P.cqStart; s.needs = Object.assign({}, P.startNeedsSprout || s.needs); s.evo.day0 = S.dayKey(now);
  // 預先排好 9 日嘅上線時間（分鐘）
  const sess = [];
  for (let d = 0; d < 9; d++) { if (sc.everyOtherDay && (d + (seed & 1)) % 2) continue; for (const h of sc.hours) { if (rng() < MISS) continue; sess.push(T0 + d * 864e5 + (h * 60 + Math.round((rng() * 2 - 1) * JIT)) * 60e3); } }
  sess.sort((a, b) => a - b); let k = 0;
  while (s.stage === 'sprout' || s.stage === 'juvenile') {
    if (now - T0 > 10 * 864e5) break;
    if (Math.floor((now - T0) / 216e5) !== Math.floor((now - T0 - 1800e3) / 216e5)) { let r = rng(), w = 'clear'; for (const [n, p] of WX) { if (r < p) { w = n; break; } r -= p; } wx = w; }
    while (k < sess.length && sess[k] < now) k++;
    if (k < sess.length && sess[k] < now + 1800e3) {
      k++; s.lastSeen = now; if (s.sleeping) S.toggleSleep(s);
      const acts = sc.acts.filter(() => rng() >= SKIP_ACT); if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
      for (const a of acts) { if (a === 'feed') { s.needs.hunger = Math.min(s.needs.hunger, 60); S.feed(s, 'meal'); } else if (a === 'play') S.play(s); else if (a === 'rinse') S.rinse(s); else { while (s.poops > 0) S.clearPoop(s); } }   // v5：只清真實便便（出咗幾耐決定係咪即清）
      if (S.isDrowsy(s) && rng() < LULL) S.lullSleep(s);   // v5 哄瞓：眼瞓時有機會哄佢瞓
      const hr = new Date(now).getHours();
      if ((hr >= 17 || hr < 7) && rng() < 0.25) { const E = s.evo || (s.evo = {}); E.evIn = E.evIn || {}; const b = E.evIn[s.stage] || (E.evIn[s.stage] = {}); b[P.evo6.lumiEvent] = (b[P.evo6.lumiEvent] || 0) + 1; }
      S.advance(s, 1800, {}, 60); now += 1800e3; s.lastSeen = now;
    } else { const t0 = now; now += 1800e3; s.lastSeen = t0; S.applyOffline(s, now); s.growthSec += 1800; S.checkStage && S.checkStage(s); }
  }
  S.setHourFn(null); S.setNowFn(null); S.setWeatherFn(null); const ev = (s.ev || []).find(e => e.type === 'evolve'); return { form: s.form, cq: ev ? ev.cq : s.cq };
}
const all = {}, out = {};
for (const name of Object.keys(SCHED)) {
  const c = {}, cqs = []; for (let i = 1; i <= N; i++) { const r = run(name, i); c[r.form] = (c[r.form] || 0) + 1; all[r.form] = (all[r.form] || 0) + 1; cqs.push(r.cq); }
  cqs.sort((a, b) => a - b); out[name] = { dist: c, cqMed: +cqs[N >> 1].toFixed(1), cqP10: +cqs[Math.floor(N * 0.1)].toFixed(1), cqP90: +cqs[Math.floor(N * 0.9)].toFixed(1) };
  console.log(name.padEnd(4, '　'), JSON.stringify(c), 'CQ p10/中/p90', out[name].cqP10, out[name].cqMed, out[name].cqP90);
}
const tot = N * Object.keys(SCHED).length, lumiPct = 100 * (all.lumi || 0) / tot;
console.log('全體', JSON.stringify(all));
const chk = [
  ['6 個時間表合共出齊 9 條路', D.BRANCHES.every(f => all[f])],
  ['每表菇傘 ≤30%（v5）', Object.values(out).every(o => (o.dist.shroom || 0) <= 0.3 * N)],
  ['每個時間表最少 2 種結局', Object.values(out).every(o => Object.keys(o.dist).length >= 2)],
  ['單一結局 ≤85%', Object.values(out).every(o => Math.max(...Object.values(o.dist)) <= 0.85 * N)],
  [`螢絨全體 3–10%（實際 ${lumiPct.toFixed(1)}%）`, lumiPct >= 3 && lumiPct <= 10],
  ['疏玩（隔日）表最少 2 種結局（v4：微塵＋火苗可接受）', Object.keys(out['疏玩'].dist).length >= 2],
  [`疏玩 CQ 大約 15–35（中位 ${out['疏玩'].cqMed}）`, out['疏玩'].cqMed >= 15 && out['疏玩'].cqMed <= 35],
];
for (const [n, v] of chk) console.log((v ? '  ✓ ' : '  ✗ ') + n);
