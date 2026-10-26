/* 無 DOM 模擬測試：node tests/sim.test.js [場數=200] */
'use strict';
const assert = require('assert');
const Data = require('../src/data.js');
const Sim = require('../src/sim.js');
const P = Data.PARAMS;
const N = parseInt(process.argv[2] || '200', 10);
const near = (a, b, e) => Math.abs(a - b) < (e || 1e-9);

// ---------- 1. 公式單元檢查 ----------
function unit(cid, lv) { return Sim.makeUnit(cid, Sim.newCreatureState(lv || 1), P); }
(function formulaChecks() {
  // 速度例子（一頁設計 4.7）：以固定基礎速度覆寫
  const mk = (base, apt, terrain) => {
    const u = unit('mochi'); u.stats.speed = base; u.apt = [3, 3, 3, 3, 3]; u.apt[Data.TERRAIN_INDEX[terrain]] = apt;
    const e = unit('namifin'); e.stats.speed = 1;
    const race = Sim.createRace({ terrains: [terrain, terrain, terrain, terrain, terrain], teams: [[u, unit('mochi')], [e, unit('mochi')]] });
    race.sides[1].pos = -1e6; // 令追趕 C 唔生效（0 號領先）
    return Sim.computeSide(race, 0);
  };
  assert(near(mk(70, 3, 'gravel'), 10.5, 1e-6), '例1 10.5');
  assert(near(mk(64, 4, 'shallows'), 10.752, 1e-6), '例2 10.75');
  assert(near(mk(80, 1, 'frost'), 7.8, 1e-6), '例3 7.8');
  // 換人減速時間
  assert(near(Sim.swapOutTime(50, P), 1.1), 'swap out calm50');
  assert(near(Sim.swapOutTime(0, P), 1.4) && near(Sim.swapOutTime(999, P), 0.5), 'swap out clamp');
  // 追趕
  const tough = { trait: 'tough' };
  assert(near(Sim.catchupC(10, {}, P), 1.04) && near(Sim.catchupC(100, {}, P), 1.08) && near(Sim.catchupC(-5, {}, P), 1), 'catchup');
  assert(near(Sim.catchupC(100, tough, P), 1.11), 'catchup tough cap');
  // 氣勢
  const g = (p) => Sim.gustoOfStamina({ stamina: p * 100, max: 100 }, P);
  assert(g(0.5) === 1 && near(g(0.3), 1) && near(g(0.2), 0.95) && near(g(0.1), 0.9) && near(g(0.05), 0.85) && g(0) === 0.7, 'gusto');
  // 升級經驗
  assert(Sim.expToNext(1, P) === 42 && Sim.expToNext(10, P) === 150, 'exp');
  const st = Sim.newCreatureState(1); assert(Sim.addExp(st, 42 + 54 + 5, P) === 2 && st.lv === 3 && st.exp === 5, 'addExp');
  const cap = Sim.newCreatureState(19); Sim.addExp(cap, 99999, P); assert(cap.lv === 20, 'level cap');
  // 換人流程：冷卻、入場期、技能鎖
  const r = Sim.createRace({ terrains: Data.TRACK_MAIN, teams: [[unit('mochi'), unit('narrowcat'), unit('tingyu')], [unit('namifin'), unit('mochi')]] });
  assert(Sim.requestSwap(r, 0, 1) && !Sim.requestSwap(r, 0, 2), '換人期間唔可再換');
  assert(!Sim.requestSkill(r, 0), '交棒期間唔可放技能');
  for (let i = 0; i < 2 * 30; i++) Sim.step(r, 1 / 30);
  assert(r.sides[0].active === 1 && r.sides[0].phase === 'in', '2s 後已入場（calm50→1.1s 交棒，入場 1.5s）' + r.sides[0].phase);
  for (let i = 0; i < 30; i++) Sim.step(r, 1 / 30);
  assert(r.sides[0].phase === 'run', '入場完成');
  assert(Sim.requestSkill(r, 0) && !Sim.requestSkill(r, 0), '技能每隻只一次');
  assert(r.sides[0].team[0].stamina > 0, '後備回耐力');
  console.log('公式檢查：全部通過');
})();

// ---------- 2. 200 場 AI vs AI ----------
const CIDS = Data.CREATURES.map(c => c.id);
const tracks = [Data.TRACK_MAIN].concat(Data.STAGES.map(s => s.terrains));
function pickTeam(rng, lv) {
  const pool = CIDS.slice(), out = [];
  for (let i = 0; i < 3; i++) out.push({ id: pool.splice(Math.floor(rng() * pool.length), 1)[0], lv });
  return out;
}
const rng = Sim.makeRng(20261026);
let sumD = 0, minD = 1e9, maxD = 0, inRange = 0, aWins = 0;
let swapOnly = [0, 0], skillOnly = [0, 0], swapTot = 0, skillTot = 0, flipSwap = 0, flipSkill = 0, flipAny = 0;
const perC = {}; CIDS.forEach(c => perC[c] = { w: 0, n: 0 });
const durs = [];
for (let i = 0; i < N; i++) {
  const lv = 3 + Math.floor(rng() * 8);                 // Lv3–10
  const terr = tracks[Math.floor(rng() * tracks.length)];
  const teams = [pickTeam(rng, lv), pickTeam(rng, lv)];
  const seed = 1000 + i;
  const base = Sim.runMatch({ terrains: terr, teams, seed });
  durs.push(base.duration);
  sumD += base.duration; minD = Math.min(minD, base.duration); maxD = Math.max(maxD, base.duration);
  if (base.duration >= 80 && base.duration <= 130) inRange++;
  if (base.winner === 0) aWins++;
  swapTot += base.swaps[0] + base.swaps[1]; skillTot += base.skills[0] + base.skills[1];
  // 只一邊用過
  [['swaps', swapOnly], ['skills', skillOnly]].forEach(([k, acc]) => {
    const a = base[k][0], b = base[k][1];
    if (a !== b) { acc[1]++; const user = a > b ? 0 : 1; if (base.winner === user) acc[0]++; }
  });
  // 反事實：兩邊都唔換人／唔放技能，勝負會否改變
  const nsw = Sim.runMatch({ terrains: terr, teams, seed, noSwap: [true, true] });
  const nsk = Sim.runMatch({ terrains: terr, teams, seed, noSkill: [true, true] });
  const nboth = Sim.runMatch({ terrains: terr, teams, seed, noSwap: [true, true], noSkill: [true, true] });
  if (nsw.winner !== base.winner) flipSwap++;
  if (nsk.winner !== base.winner) flipSkill++;
  if (nboth.winner !== base.winner) flipAny++;
  teams[0].concat(teams[1]).forEach((u, k) => { const w = k < 3 ? 0 : 1; perC[u.id].n++; if (base.winner === w) perC[u.id].w++; });
}
durs.sort((a, b) => a - b);
const pct = (v) => (100 * v / N).toFixed(1) + '%';
console.log('\n===== ' + N + ' 場 AI vs AI（3v3，Lv3–10，5 條賽道隨機）=====');
console.log('平均時長 ' + (sumD / N).toFixed(1) + ' s｜中位 ' + durs[N >> 1].toFixed(1) + '｜最短 ' + minD.toFixed(1) + '｜最長 ' + maxD.toFixed(1));
console.log('時長喺 80–130 s：' + pct(inRange) + '（' + inRange + '/' + N + '）');
console.log('甲方（先手位）勝率 ' + pct(aWins) + '（應近 50%）');
console.log('每場平均換人 ' + (swapTot / N).toFixed(2) + ' 次、技能 ' + (skillTot / N).toFixed(2) + ' 次（兩邊合計）');
console.log('兩邊換人次數唔同嘅場數 ' + swapOnly[1] + '：「換得多」一邊勝率 ' + (swapOnly[1] ? (100 * swapOnly[0] / swapOnly[1]).toFixed(1) + '%' : 'n/a'));
console.log('兩邊放技能次數唔同嘅場數 ' + skillOnly[1] + '：「放得多」一邊勝率 ' + (skillOnly[1] ? (100 * skillOnly[0] / skillOnly[1]).toFixed(1) + '%' : 'n/a'));
console.log('反事實（同種子，兩邊都禁用）→ 勝負改變：禁換人 ' + pct(flipSwap) + '｜禁技能 ' + pct(flipSkill) + '｜兩者皆禁 ' + pct(flipAny) + '（驗收：≥30%）');
const rows = CIDS.map(c => [Data.CREATURES_BY_ID[c].name, perC[c].n ? 100 * perC[c].w / perC[c].n : 0, perC[c].n]);
console.log('各野靈出場勝率：' + rows.map(r => r[0] + ' ' + r[1].toFixed(0) + '%').join('｜'));


// ---------- 3. 關卡難度檢查（AI 代打玩家隊，對真實關卡對手） ----------
(function stageCheck() {
  console.log('\n===== 關卡難度檢查（玩家隊由 AI 代打；對手＝該關設定）=====');
  function winRate(stage, team, lv, seeds) {
    let w = 0;
    for (let s = 0; s < seeds; s++) {
      const race = Sim.createRace({ terrains: stage.terrains, seed: 500 + s,
        teams: [Sim.unitsFromDef(team.map(id => ({ id, lv })), P), Sim.unitsFromDef(stage.opp.team, P)],
        ctrls: [{ kind: 'ai', next: 0 }, Sim.makeOppCtrl(stage.opp)] });
      while (!race.over) Sim.step(race, P.sim_dt);
      if (race.winner === 0) w++;
    }
    return w / seeds;
  }
  function* orderedTeams(n) {
    const ids = CIDS;
    if (n === 2) { for (const a of ids) for (const b of ids) if (a !== b) yield [a, b]; }
    else { for (const a of ids) for (const b of ids) for (const c of ids) if (a !== b && a !== c && b !== c) yield [a, b, c]; }
  }
  Data.STAGES.forEach(stage => {
    const oLv = stage.opp.team[0].lv, res = {};
    [oLv - 2, oLv].forEach(lv => {
      let tot = 0, n = 0, best = 0;
      for (const team of orderedTeams(stage.teamSize)) { const r = winRate(stage, team, lv, 2); tot += r; n++; if (r > best) best = r; }
      res[lv] = { avg: tot / n, best };
    });
    console.log('第 ' + stage.id + ' 關 ' + stage.name + '（對手 Lv' + oLv + '）：' + Object.keys(res).map(lv => '玩家 Lv' + lv + ' → 全部組合平均勝率 ' + (100 * res[lv].avg).toFixed(0) + '%、最佳組合 ' + (100 * res[lv].best).toFixed(0) + '%').join('｜'));
  });
})();

// 驗收斷言
const avg = sumD / N;
assert(avg >= 80 && avg <= 130, '平均時長 ' + avg.toFixed(1) + ' 超出 80–130 s');
assert(inRange / N >= 0.9, '多過 10% 場次唔喺 80–130 s');
console.log('\nPASS：平均時長 ' + avg.toFixed(1) + ' s 喺 80–130 s 內');
