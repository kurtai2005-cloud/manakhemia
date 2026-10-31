/* §7 平衡修訂 v3 掃描（俾遊測調 config 用，唔係 gating test）：node tools/route-sweep.js [每表隻數=200]
   6 個代表時間表 × N 個 seed（每個 seed 抖動上線鐘點＋螢火散步），由芽崽行到守夜者，統計 9 條路分佈同 v3 目標。
   數值全部讀 PARAMS.evo6.branch；時間表係呢度自訂嘅近似（遊測正式表可替換 SCHED）。 */
const S = require('../src/sim.js'), D = require('../src/data.js'), P = D.PARAMS;
const N = +process.argv[2] || 200;
// 每個時間表：上線鐘點、每次做咩（feed／play／rinse／poop）
const SCHED = {
  勤力: { hours: [8, 11, 14, 17, 20], acts: ['feed', 'play', 'rinse', 'poop'] },
  普通: { hours: [8, 13, 19], acts: ['feed', 'play', 'poop'] },
  疏玩: { hours: [20], acts: ['feed', 'play'], everyOther: 0.5 },
  夜貓: { hours: [18, 22, 0, 1], acts: ['feed', 'play'] },
  早起: { hours: [6, 7, 8, 12], acts: ['feed', 'rinse', 'play'] },
  餵食狂: { hours: [9, 12, 15, 18], acts: ['feed', 'feed', 'feed', 'play'] },
};
function run(name, seed) {
  const sc = SCHED[name], rng = S.makeRng ? S.makeRng(seed * 7919 + 13) : Math.random;
  let now = new Date(2026, 10, 2, 8, 0, 0).getTime();
  S.setHourFn(() => new Date(now).getHours() + new Date(now).getMinutes() / 60);
  const s = S.newState(now, seed); s.stage = 'sprout'; s.growthSec = 0; s.cq = P.cqStart; s.needs = Object.assign({}, P.startNeedsSprout || s.needs);
  const jit = sc.hours.map(() => Math.floor(rng() * 3) - 1);
  for (let h = 0; h < 24 * 8 && (s.stage === 'sprout' || s.stage === 'juvenile'); h++) {
    const hr = new Date(now).getHours(), i = sc.hours.findIndex((x, k) => (x + jit[k] + 24) % 24 === hr);
    if (i >= 0 && !(sc.everyOther && rng() < sc.everyOther)) {
      s.lastSeen = now; if (s.sleeping) S.toggleSleep(s);
      for (const a of sc.acts) { if (a === 'feed') { s.needs.hunger = Math.min(s.needs.hunger, 60); S.feed(s, 'meal'); } else if (a === 'play') S.play(s); else if (a === 'rinse') S.rinse(s); else { s.poops = Math.max(1, s.poops); S.clearPoop(s); } }
      if ((hr >= 17 || hr < 7) && rng() < 0.25) { const E = s.evo || (s.evo = {}); E.evIn = E.evIn || {}; const b = E.evIn[s.stage] || (E.evIn[s.stage] = {}); b[P.evo6.lumiEvent] = (b[P.evo6.lumiEvent] || 0) + 1; }
      S.advance(s, 1800, {}, 60); now += 1800e3; s.lastSeen = now; now += 1800e3;
    } else { const t0 = now; now += 3600e3; s.lastSeen = t0; S.applyOffline(s, now); s.growthSec += 3600; S.checkStage && S.checkStage(s); }
  }
  S.setHourFn(null); const ev = (s.ev || []).find(e => e.type === 'evolve'); return { form: s.form, cq: ev ? ev.cq : s.cq };
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
  ['每個時間表最少 2 種結局', Object.values(out).every(o => Object.keys(o.dist).length >= 2)],
  ['單一結局 ≤85%', Object.values(out).every(o => Math.max(...Object.values(o.dist)) <= 0.85 * N)],
  [`螢絨全體 3–10%（實際 ${lumiPct.toFixed(1)}%）`, lumiPct >= 3 && lumiPct <= 10],
  ['疏玩表出到柔光＋微塵', !!(out['疏玩'].dist.soft && out['疏玩'].dist.dust)],
  [`疏玩 CQ 大約 15–35（中位 ${out['疏玩'].cqMed}）`, out['疏玩'].cqMed >= 15 && out['疏玩'].cqMed <= 35],
];
for (const [n, v] of chk) console.log((v ? '  ✓ ' : '  ✗ ') + n);
