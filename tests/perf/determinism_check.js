#!/usr/bin/env node
/* determinism_check.js — 驗收「同種子重播一致」＋「一場 ≤120 秒」（Node，無 DOM）
 * 用法：node determinism_check.js <windrun src 目錄，例如 ../../windrun-proto/src> [場數=300]
 * 檢查：
 *  1) 同種子同隊伍連跑 2 次 → winner／duration／換人／技能次數／終點差必須完全相同
 *  2) 同一場用「不同步長切分」（模擬幀率 30／60／144fps：每個 rAF 累積多個 sim_dt）→ 結果必須相同（模擬同表現分離）
 *  3) 帶輸入日誌重播（指定時間點換人／放技能）→ 兩次相同
 *  4) 全部場次時長 ≤120 秒（一頁設計驗收）
 */
'use strict';
const path = require('path');
const src = path.resolve(process.argv[2] || '../../windrun-proto/src');
const N = parseInt(process.argv[3] || '300', 10);
const Data = require(path.join(src, 'data.js')), Sim = require(path.join(src, 'sim.js')), P = Data.PARAMS;
const ids = Data.CREATURES.map(c => c.id), rng = Sim.makeRng(424242);
const tracks = [Data.TRACK_MAIN].concat(Data.STAGES.map(s => s.terrains));
const pick = () => { const p = ids.slice(), o = []; for (let i = 0; i < 3; i++) o.push({ id: p.splice(Math.floor(rng() * p.length), 1)[0], lv: 3 + Math.floor(rng() * 8) }); return o; };
const key = r => JSON.stringify([r.winner, +r.duration.toFixed(6), r.swaps, r.skills, +r.margin.toFixed(6)]);
let bad = { same: 0, chunk: 0, log: 0, long: 0 }, maxDur = 0;
// 以「幀」驅動：每幀 frameDt 秒，累積器每 sim_dt 走一步（同 main.js 主迴圈）
function runFramed(o, frameDt, inputs) {
  const race = Sim.createRace({ terrains: o.terrains, seed: o.seed, P, teams: [Sim.unitsFromDef(o.a, P), Sim.unitsFromDef(o.b, P)],
    ctrls: [inputs ? null : { kind: 'ai', next: 0 }, { kind: 'ai', next: 0 }] });
  let acc = 0, k = 0, steps = 0; const h = P.sim_dt;
  while (!race.over && steps < 20000) {
    acc += frameDt;
    while (acc >= h - 1e-12 && !race.over) {
      if (inputs) while (k < inputs.length && inputs[k].step <= steps) { const e = inputs[k++]; if (e.swap != null) Sim.requestSwap(race, 0, e.swap); else Sim.requestSkill(race, 0); }
      Sim.step(race, h); acc -= h; steps++;
    }
  }
  return JSON.stringify([race.winner, +race.duration.toFixed(6), race.sides[0].swaps, race.sides[1].swaps, +(race.sides[0].pos - race.sides[1].pos).toFixed(6)]);
}
for (let i = 0; i < N; i++) {
  const o = { terrains: tracks[Math.floor(rng() * tracks.length)], a: pick(), b: pick(), seed: 5000 + i };
  const mk = () => Sim.runMatch({ terrains: o.terrains, teams: [o.a, o.b], seed: o.seed, P });
  const r1 = mk(), r2 = mk();
  if (key(r1) !== key(r2)) bad.same++;
  maxDur = Math.max(maxDur, r1.duration); if (r1.duration > 120) bad.long++;
  const f30 = runFramed(o, 1 / 30), f60 = runFramed(o, 1 / 60), f144 = runFramed(o, 1 / 144), fjit = runFramed(o, 1 / 47);
  if (!(f30 === f60 && f60 === f144 && f144 === fjit)) bad.chunk++;
  const inputs = [{ step: 300, swap: 1 }, { step: 600, skill: true }, { step: 1200, swap: 2 }, { step: 1500, skill: true }];
  if (runFramed(o, 1 / 60, inputs) !== runFramed(o, 1 / 30, inputs)) bad.log++;
}
console.log(JSON.stringify({ matches: N, maxDurationSec: +maxDur.toFixed(1), nonDeterministicSameSeed: bad.same, differsByFrameRate: bad.chunk, differsOnInputReplay: bad.log, over120s: bad.long }));
const ok = !bad.same && !bad.chunk && !bad.log && !bad.long;
console.log(ok ? 'PASS' : 'FAIL'); process.exit(ok ? 0 : 1);
