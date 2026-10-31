/* §7 平衡掃描（v10，俾遊測對數用，唔係 gating test）：node tools/route-sweep.js [每表隻數=1000] [--json out.json]
   6 個代表時間表 × N 個 seed，由芽崽行到守夜者，用真 code（sim.decideBranch）統計 9 條路分佈，同遊測鎖定目標（QA/balance/scan-v10.js，PR #19）比較。
   玩家隨機性同 scan-v10 一樣：主 rng（seed*7919+13）、±90 分鐘、漏上線 15%、動作跳 20%、加動作 30%、眼瞓時 50% 哄瞓、天氣一日一抽（v10.2，同遊戲共用 sim.dayWeather）；
   小遊戲用獨立 rng（seed*7919+97）：表定鐘點（MG_AT）到場 80% 開一局（第 2 批未出 → 浮動團絨撳兩下＝一局，走 sim.overlayOpenGame 同一條 mgApply 路）。
   天氣讀 config weather.probs（晴60／陰20／雨15／霧5；霧當陰 0.5）。每次上線 sim.noteLogin（v7 晶角即清窗口）。
   --quests：載入 systems.js（systems12 每日委託路線分，v10.2 平均輪 5 條路線、受 25% cap；v10.3 逐張 ⅓）。
   --fpats N：v10.3 懸浮團絨每日 12:00 摸頭 N 下（經 applyOverlay {k:'pat'}，同 fpet-bridge 一條路；要 --quests）。
   數值全部讀 PARAMS.evo6.branch；唔改 config。 */
const S = require('../src/sim.js'), D = require('../src/data.js'), P = D.PARAMS, C = P.evo6.branch;
const args = process.argv.slice(2); if (args.includes('--quests')) require('../src/systems.js');
const FPATS = args.includes('--fpats') ? +args[args.indexOf('--fpats') + 1] || 0 : 0;
const NARG = +(args.find((a, i) => /^\d+$/.test(a) && args[i - 1] !== '--fpats')) || 1000, jsonOut = args.includes('--json') ? args[args.indexOf('--json') + 1] : null;
const JIT = 90, MISS = 0.15, LULL = 0.5, SKIP_ACT = 0.2, EXTRA_ACT = 0.3;
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
const MG_AT = { 勤力: [11, 17], 普通: [13], 疏玩: [20], 夜貓: [18], 早起: [12], 餵食狂: [15] };   // 同 scan-v10
// 遊測 v10 鎖定（QA 767229a，k＝0.45，N＝1000）全體 %
const TARGET = { lumi: 5.47, tide: 16.17, shroom: 6.4, crystal: 15.25, moon: 16.5, ember: 14.9, bright: 5.12, soft: 12.43, dust: 7.77 };
const FLAG_PT = 3;
/* o.days → 固定行 N 日（經濟 sim 用，唔理進化）；o.drops → 懸浮每日執幾粒星星碎（遊測假設 5）；o.fpats → v10.3 懸浮每日摸頭幾下（12:00，overlay 回傳）；X＝systems.js（有載先有委託／摸頭） */
function run(name, seed, o) {
  o = o || {}; const X = SYS12();
  const sc = SCHED[name], rng = S.makeRng(seed * 7919 + 13), rngMg = S.makeRng(seed * 7919 + 97), rngPat = S.makeRng(seed * 7919 + 211), T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
  let now = T0 + 8 * 3600e3, wx = 'clear';
  S.setHourFn(() => new Date(now).getHours() + new Date(now).getMinutes() / 60); S.setNowFn(() => now); S.setWeatherFn(() => wx);
  const s = S.newState(now, seed); s.stage = 'sprout'; s.growthSec = 0; s.cq = P.cqStart; s.needs = Object.assign({}, P.startNeedsSprout || s.needs); s.evo.day0 = S.dayKey(now);
  const sess = [];
  for (let d = 0; d < 9; d++) { if (sc.everyOtherDay && (d + (seed & 1)) % 2) continue; for (const h of sc.hours) { if (rng() < MISS) continue; sess.push({ t: T0 + d * 864e5 + (h * 60 + Math.round((rng() * 2 - 1) * JIT)) * 60e3, h }); } }
  sess.sort((a, b) => a.t - b.t); let k = 0, mgs = 0, lulls = 0;
  const played = {}, dropped = {}, fpatted = {}, shards = {};
  while (o.days ? now - T0 < o.days * 864e5 : (s.stage === 'sprout' || s.stage === 'juvenile')) {
    if (!o.days && now - T0 > 10 * 864e5) break;
    if (X && o.days) { const wl = X.wallet(s, now); shards[S.dayKey(now - 1)] = Math.max(shards[S.dayKey(now - 1)] || 0, X.wallet(s, now - 1).today); shards[S.dayKey(now)] = wl.today; }
    if (X && o.drops) { const dk = S.dayKey(now); if (!dropped[dk] && new Date(now).getHours() >= 12) { dropped[dk] = 1; for (let i = 0; i < o.drops; i++) X.grant(s, P.systems12.surprise.drop.amt, 'drop', now); } }
    if (X && o.fpats) { const dk = S.dayKey(now); if (!fpatted[dk] && new Date(now).getHours() >= 12 && s.stage !== 'egg') { fpatted[dk] = 1; const it = []; for (let i = 0; i < o.fpats; i++) it.push({ t: now - (o.fpats - i) * 60e3, k: 'pat' }); X.applyOverlay(s, it, now, s.ev); } }
    wx = S.dayWeather(s.seed >>> 0, now);                 // v10.2：同遊戲一樣一日一抽（sim.dayWeatherN；seed＝隻團絨 seed）
    while (k < sess.length && sess[k].t < now) k++;
    if (k < sess.length && sess[k].t < now + 1800e3) {
      const slot = sess[k++]; s.lastSeen = now; if (s.sleeping) S.toggleSleep(s);
      S.noteLogin(s, now);                                   // v7：上線 → 晶角即清窗口
      const acts = sc.acts.filter(() => rng() >= SKIP_ACT); if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
      played[S.dayKey(now)] = 1;
      if (X) for (let i = 0; i < 2; i++) if (rngPat() >= SKIP_ACT) X.notePat(s, now);   // v10.2 摸頭：每次上線撳 2 下（獨立 rng，唔影響其他抽籤）
      for (const a of acts) { if (a === 'feed') { s.needs.hunger = Math.min(s.needs.hunger, 60); S.feed(s, 'meal'); } else if (a === 'play') S.play(s); else if (a === 'rinse') S.rinse(s); else { while (s.poops > 0) S.clearPoop(s); } }
      if (MG_AT[name].includes(slot.h) && rngMg() >= SKIP_ACT) { const r = S.overlayOpenGame(s, now); if (r.ok) mgs++; }   // v8：浮動團絨撳兩下＝一局
      if (S.isDrowsy(s) && rng() < LULL) { const r = S.lullSleep(s); if (r.counted) lulls++; }
      const hr = new Date(now).getHours();
      if ((hr >= 17 || hr < 7) && rng() < 0.25) S.noteEvent(s, P.evo6.lumiEvent);
      S.advance(s, 1800, {}, 60); now += 1800e3; s.lastSeen = now;
    } else { const t0 = now; now += 1800e3; s.lastSeen = t0; S.applyOffline(s, now); s.growthSec += 1800; S.checkStage && S.checkStage(s); }
  }
  S.setHourFn(null); S.setNowFn(null); S.setWeatherFn(null);
  const ev = (s.ev || []).find(e => e.type === 'evolve');
  if (X && o.days) shards[S.dayKey(now)] = X.wallet(s, now).today;
  return { shards, played, form: s.form, cq: ev ? ev.cq : s.cq, mgs, lulls, need: ev && ev.b5 ? ev.b5.cqNeed : null, quick: ev && ev.b5 ? ev.b5.raw : null };
}
function SYS12() { try { return require.cache[require.resolve('../src/systems.js')] ? require('../src/systems.js') : null; } catch (e) { return null; } }
module.exports = { SCHED, MG_AT, TARGET, FLAG_PT, run, main };
if (require.main === module) main();
function main(n, quiet, ro) {
  ro = ro || (FPATS ? { fpats: FPATS } : {});
  const N = n || NARG, log = quiet ? () => {} : console.log;
const all = {}, out = {}, NAMES = Object.keys(SCHED);
for (const name of NAMES) {
  const c = {}, cqs = []; let mg = 0, lu = 0;
  for (let i = 1; i <= N; i++) { const r = run(name, i, ro); c[r.form] = (c[r.form] || 0) + 1; all[r.form] = (all[r.form] || 0) + 1; cqs.push(r.cq); mg += r.mgs; lu += r.lulls; }
  cqs.sort((a, b) => a - b);
  const pct = {}; for (const f of D.BRANCHES) pct[f] = +(100 * (c[f] || 0) / N).toFixed(2);
  out[name] = { dist: c, pct, cqMed: +cqs[N >> 1].toFixed(2), cqP10: +cqs[Math.floor(N * 0.1)].toFixed(2), cqP90: +cqs[Math.floor(N * 0.9)].toFixed(2), mgs: +(mg / N).toFixed(2), lulls: +(lu / N).toFixed(2) };
  log(name.padEnd(4, '　'), D.BRANCHES.map(f => D.FORM_NAME[f] + ' ' + pct[f]).join('  '), '｜CQ p10/中/p90', out[name].cqP10, out[name].cqMed, out[name].cqP90, '｜小遊戲', out[name].mgs, '哄瞓', out[name].lulls);
}
const tot = N * NAMES.length, total = {};
for (const f of D.BRANCHES) total[f] = +(100 * (all[f] || 0) / tot).toFixed(2);
log('\n全體 vs 遊測 v10 目標（差 >' + FLAG_PT + 'pt 標 ⚠）');
const flags = [];
for (const f of D.BRANCHES) { const d = +(total[f] - TARGET[f]).toFixed(2), bad = Math.abs(d) > FLAG_PT; if (bad) flags.push(f); log(`  ${(D.FORM_NAME[f] + '　').slice(0, 2)} ${String(total[f]).padStart(6)}%  目標 ${String(TARGET[f]).padStart(6)}%  差 ${(d >= 0 ? '+' : '') + d}${bad ? '  ⚠' : ''}`); }
const max = (f) => Math.max(...NAMES.map(n => out[n].pct[f]));
const chk = [
  ['9 條路出齊（每條 ≥2%）', D.BRANCHES.every(f => total[f] >= 2)],
  ['每表 ≥2 結局（每個 ≥2%）', NAMES.every(n => D.BRANCHES.filter(f => out[n].pct[f] >= 2).length >= 2)],
  ['單一結局 ≤85%', NAMES.every(n => D.BRANCHES.every(f => out[n].pct[f] <= 85))],
  [`螢絨全體 3–10%（${total.lumi}%）`, total.lumi >= 3 && total.lumi <= 10],
  [`每表菇傘 ≤30%（最高 ${max('shroom')}%）`, max('shroom') <= 30],
  [`晶角全體 ≥5%（${total.crystal}%）`, total.crystal >= 5],
  [`月眠全體 ≥5%（${total.moon}%）`, total.moon >= 5],
  [`每表燦光 ≤50%（最高 ${max('bright')}%）`, max('bright') <= 50],
  [`疏玩柔光＋微塵（${out['疏玩'].pct.soft}/${out['疏玩'].pct.dust}）`, out['疏玩'].pct.soft >= 2 && out['疏玩'].pct.dust >= 2],
  [`疏玩 CQ 15–35（中位 ${out['疏玩'].cqMed}）`, out['疏玩'].cqMed >= 15 && out['疏玩'].cqMed <= 35],
];
for (const [n, v] of chk) log((v ? '  ✓ ' : '  ✗ ') + n);
log(`  ${chk.filter(c => c[1]).length}/${chk.length} 達標；差 >${FLAG_PT}pt：${flags.length ? flags.map(f => D.FORM_NAME[f]).join('、') : '冇'}`);
if (jsonOut && !quiet) require('fs').writeFileSync(jsonOut, JSON.stringify({ N, ro, total, target: TARGET, flags, tables: out, checks: chk }, null, 2));
return { total, flags, tables: out, checks: chk };
}
