/* fengye_harness.js — 由 balance_fengye.py 呼叫：用遊程原型嘅真實 sim.js／data.js 跑 Monte Carlo。
 * 用法：node fengye_harness.js <windrun-src 目錄> <scenario.json>   → stdout 輸出 JSON
 * scenario: { overrides:{P:{}, creatures:{id:{base:{},apt:[],skill,trait,star}}, stages:{n:{...}}},
 *             exp:'field'|'stage'|'flip', ... } */
'use strict';
const path = require('path');
const src = path.resolve(process.argv[2]);
const sc = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const Data = require(path.join(src, 'data.js'));
const Sim = require(path.join(src, 'sim.js'));
const P = Data.PARAMS;
const ov = sc.overrides || {};
Object.assign(P, JSON.parse(JSON.stringify(ov.P || {})));
for (const [id, o] of Object.entries(ov.creatures || {})) {
  const c = Data.CREATURES_BY_ID[id];
  if (o.base) Object.assign(c.base, o.base);
  if (o.apt) c.apt = o.apt.slice();
  for (const k of ['skill', 'trait', 'star']) if (k in o) c[k] = o[k];
}
for (const [n, o] of Object.entries(ov.stages || {})) {
  const s = Data.STAGES[+n - 1];
  if (o.oppLv != null) s.opp.team.forEach(t => { t.lv = o.oppLv; });
  if (o.counter != null && s.opp.script) s.opp.script.counter = o.counter;
  if (o.terrains) s.terrains = o.terrains;
  if (o.oppTeam) s.opp.team = o.oppTeam.map(x => ({ id: x[0], lv: x[1] }));
}
const CIDS = Data.CREATURES.map(c => c.id);
const NAME = {}; Data.CREATURES.forEach(c => { NAME[c.id] = c.name; });
const TRACKS = { main: Data.TRACK_MAIN, s1: Data.STAGES[0].terrains, s2: Data.STAGES[1].terrains, s3: Data.STAGES[2].terrains };

function pickTeam(rng, lv, n) {
  const pool = CIDS.slice(), out = [];
  for (let i = 0; i < n; i++) out.push({ id: pool.splice(Math.floor(rng() * pool.length), 1)[0], lv });
  return out;
}
function runStage(stage, team, lv, seed) {
  const race = Sim.createRace({ terrains: stage.terrains, seed, P,
    teams: [Sim.unitsFromDef(team.map(id => ({ id, lv })), P), Sim.unitsFromDef(stage.opp.team, P)],
    ctrls: [{ kind: 'ai', next: 0 }, Sim.makeOppCtrl(JSON.parse(JSON.stringify(stage.opp)))] });
  while (!race.over) Sim.step(race, P.sim_dt);
  return race;
}

let out = {};
if (sc.exp === 'field') {
  // 隨機 3v3（或 teamSize）AI 對 AI；每隻野靈「出場勝率」＝佢喺嘅隊贏嘅比例
  const rng = Sim.makeRng(sc.seed || 7), N = sc.n || 2000, ts = sc.teamSize || 3;
  const per = {}, perTrack = {};
  CIDS.forEach(c => { per[c] = { w: 0, n: 0 }; perTrack[c] = {}; });
  let sumD = 0, aWin = 0;
  for (let i = 0; i < N; i++) {
    const lv = sc.lv || (sc.lvRange ? sc.lvRange[0] + Math.floor(rng() * (sc.lvRange[1] - sc.lvRange[0] + 1)) : 5);
    const tk = sc.tracks[Math.floor(rng() * sc.tracks.length)];
    const teams = [pickTeam(rng, lv, ts), pickTeam(rng, lv, ts)];
    // 兩邊名單唔可以有重複同一隻（避免同名混淆）
    const r = Sim.runMatch({ terrains: TRACKS[tk], teams, seed: 100000 + i, P });
    sumD += r.duration; if (r.winner === 0) aWin++;
    teams[0].concat(teams[1]).forEach((u, k) => {
      const side = k < ts ? 0 : 1, w = r.winner === side ? 1 : 0;
      per[u.id].n++; per[u.id].w += w;
      const pt = perTrack[u.id][tk] = perTrack[u.id][tk] || { w: 0, n: 0 }; pt.n++; pt.w += w;
    });
  }
  out = { N, avgDur: sumD / N, sideAWin: aWin / N, per, perTrack, names: NAME };
} else if (sc.exp === 'flip') {
  // 反事實：同種子禁換人／禁技能，勝負改變比例＋「玩家式」差異
  const rng = Sim.makeRng(sc.seed || 11), N = sc.n || 1000;
  let fs = 0, fk = 0, fb = 0, swaps = 0, skills = 0, durSum = 0;
  for (let i = 0; i < N; i++) {
    const lv = sc.lv || 6, tk = sc.tracks[Math.floor(rng() * sc.tracks.length)];
    const teams = [pickTeam(rng, lv, 3), pickTeam(rng, lv, 3)], seed = 200000 + i;
    const b = Sim.runMatch({ terrains: TRACKS[tk], teams, seed, P });
    const ns = Sim.runMatch({ terrains: TRACKS[tk], teams, seed, P, noSwap: [true, true] });
    const nk = Sim.runMatch({ terrains: TRACKS[tk], teams, seed, P, noSkill: [true, true] });
    const nb = Sim.runMatch({ terrains: TRACKS[tk], teams, seed, P, noSwap: [true, true], noSkill: [true, true] });
    if (ns.winner !== b.winner) fs++; if (nk.winner !== b.winner) fk++; if (nb.winner !== b.winner) fb++;
    swaps += b.swaps[0] + b.swaps[1]; skills += b.skills[0] + b.skills[1]; durSum += b.duration;
  }
  out = { N, flipNoSwap: fs / N, flipNoSkill: fk / N, flipNoBoth: fb / N, swapsPerMatch: swaps / N, skillsPerMatch: skills / N, avgDur: durSum / N };
} else if (sc.exp === 'stage') {
  // 關卡：AI 代打玩家隊（全部有序組合）對該關對手；回傳每隊勝率
  const stage = Data.STAGES[sc.stage - 1], lvs = sc.lvs, K = sc.seeds || 4, res = {};
  const teams = [];
  if (stage.teamSize === 2) { for (const a of CIDS) for (const b of CIDS) if (a !== b) teams.push([a, b]); }
  else { for (const a of CIDS) for (const b of CIDS) for (const c of CIDS) if (a !== b && a !== c && b !== c) teams.push([a, b, c]); }
  for (const lv of lvs) {
    const rows = teams.map(t => {
      let w = 0; for (let s = 0; s < K; s++) if (runStage(stage, t, lv, 900 + s).winner === 0) w++;
      const rc = runStage(stage, t, lv, 900); return { team: t.map(x => NAME[x]), wr: w / K, margin: rc.sides[0].pos - rc.sides[1].pos };
    });
    res[lv] = rows;
  }
  out = { stage: sc.stage, oppLv: stage.opp.team[0].lv, res };
}
if (sc.exp === 'static') {
  out = { rows: Data.CREATURES.map(c => {
    const A = c.apt.map(a => P.aptitude_mult[a - 1]);
    const meanA = A.reduce((x, y) => x + y, 0) / A.length;
    return { name: c.name, speed: c.base.speed, stamina: c.base.stamina, meanA, mean: c.base.speed * P.speed_scale_K * meanA, best: c.base.speed * P.speed_scale_K * Math.max(...A) };
  }) };
}
process.stdout.write(JSON.stringify(out));
