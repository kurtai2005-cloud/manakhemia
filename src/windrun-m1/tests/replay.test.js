/* 重播測試：node tests/replay.test.js [場數=200]
   檢查：①sim/api 純度（靜態掃描＋執行時封鎖 Date/Math.random）②同種子兩次完全一致③唔同種子有差異
        ④錄製→回放（決策記錄模式／AI 重生模式）逐步雜湊同最終雜湊一致⑤JSON 往返⑥竄改偵測⑦影子隊關卡重播 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const Data = require('../src/data.js');
const Sim = require('../src/sim.js');
const Api = require('../src/api.js');
const P = Data.PARAMS;
const N = parseInt(process.argv[2] || '200', 10);

// ---------- 1. 純度 ----------
(function purity() {
  ['sim.js', 'api.js'].forEach(f => {
    const src = fs.readFileSync(path.join(__dirname, '../src', f), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
    [/\bDate\b/, /Math\.random/, /\bdocument\b/, /\bwindow\b/, /\bperformance\b/, /requestAnimationFrame/, /setTimeout|setInterval/, /localStorage/].forEach(re => {
      assert(!re.test(src), f + ' 含禁用 API：' + re);
    });
  });
  console.log('純度（靜態掃描 sim.js／api.js）：通過');
})();
// 表現層唔可直接操作 Sim（只可經 Api）
(function layering() {
  ['ui.js', 'main.js'].forEach(f => {
    const src = fs.readFileSync(path.join(__dirname, '../src', f), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
    [/Sim\.(step|createRace|requestSwap|requestSkill|canSwap|canSkill|runMatch|computeSide|hashState)\b/, /\.sim\.(sides|t|over|winner)\b/].forEach(re => {
      assert(!re.test(src), f + ' 違反分層：' + re);
    });
  });
  console.log('分層（ui.js／main.js 只經 Api 操作比賽）：通過');
})();
// 執行時封鎖：若 sim 路徑碰 Date／Math.random 即拋錯
const realRandom = Math.random, realNow = Date.now;
Math.random = function () { throw new Error('sim 路徑呼叫 Math.random'); };
Date.now = function () { throw new Error('sim 路徑呼叫 Date.now'); };

const CIDS = Data.CREATURES.map(c => c.id);
const tracks = [Data.TRACK_MAIN].concat(Data.STAGES.map(s => s.terrains));
const rng = Sim.makeRng(424242);
function pickTeam(lv, size) {
  const pool = CIDS.slice(), out = [];
  for (let i = 0; i < size; i++) out.push({ id: pool.splice(Math.floor(rng() * pool.length), 1)[0], lv, bonus: { speed: Math.floor(rng() * 5), power: 0, calm: Math.floor(rng() * 10), stamina: Math.floor(rng() * 10) }, cond: 60 + Math.floor(rng() * 41) });
  return out;
}
function randomSetup(i) {
  return { seed: 7000 + i * 13, terrains: tracks[Math.floor(rng() * tracks.length)],
    teams: [pickTeam(3 + Math.floor(rng() * 8), 2 + Math.floor(rng() * 2)), pickTeam(3 + Math.floor(rng() * 8), 3)],
    ctrls: [{ kind: 'player' }, { kind: 'ai' }] };
}
// 「玩家」隨機決策（用獨立 rng，唔影響 sim）：每步以小機率換人／放技
function playRecorded(setup, decRng) {
  const m = Api.createMatch(setup);
  let guard = 0;
  while (!m.race.over && guard++ < 100000) {
    const r = decRng();
    if (r < 0.004) Api.submit(m, 0, { type: 'skill' });
    else if (r < 0.010) Api.submit(m, 0, { type: 'swap', i: Math.floor(decRng() * setup.teams[0].length) });
    // 對手側亦偶爾由「外部輸入」介入無意義；AI 已自動
    Api.stepOnce(m);
  }
  return m;
}
function stepHashes(setup, decisions, mode, rp) {
  // 逐步雜湊：用回放模式重跑，每步收集
  const m = rp ? Api.createPlayback(rp, { mode }) : null;
  const out = [Sim.hashState(m.race)];
  while (!m.race.over) { Api.stepOnce(m); out.push(Sim.hashState(m.race)); }
  assert(!m.verifyError, m.verifyError);
  return { hashes: out, m };
}

// ---------- 2. 錄製 → 回放 ----------
const decRng = Sim.makeRng(99);
let totalSteps = 0, totalDec = 0, swapsSeen = 0, skillsSeen = 0, wins = [0, 0];
const winnersByIdx = [];
const t0 = process.hrtime.bigint();
for (let i = 0; i < N; i++) {
  const setup = randomSetup(i);
  // 錄製，同時收集逐步雜湊
  const m = Api.createMatch(setup);
  const recHashes = [Sim.hashState(m.race)];
  let guard = 0;
  while (!m.race.over && guard++ < 100000) {
    const r = decRng();
    if (r < 0.004) Api.submit(m, 0, { type: 'skill' });
    else if (r < 0.010) Api.submit(m, 0, { type: 'swap', i: Math.floor(decRng() * setup.teams[0].length) });
    Api.stepOnce(m); recHashes.push(Sim.hashState(m.race));
  }
  assert(m.race.over, '場 ' + i + ' 未結束');
  const rp = Api.getReplay(m);
  totalSteps += rp.result.steps; totalDec += rp.decisions.length; wins[rp.result.winner]++;
  winnersByIdx.push(rp.result.winner);
  rp.decisions.forEach(d => { if (d.a === 'swap') swapsSeen++; else skillsSeen++; });
  // JSON 往返（模擬存檔／上傳）
  const rp2 = JSON.parse(JSON.stringify(rp));
  // 回放 A：只按決策記錄（含 AI 決策）
  const a = stepHashes(setup, null, 'log', rp2);
  assert.strictEqual(a.hashes.length, recHashes.length, '場 ' + i + ' log 回放步數不同');
  for (let k = 0; k < recHashes.length; k++) assert.strictEqual(a.hashes[k], recHashes[k], '場 ' + i + ' log 回放第 ' + k + ' 步雜湊不同');
  assert.strictEqual(Api.hex8(Sim.hashState(a.m.race)), rp.result.finalHash, '最終雜湊');
  assert.strictEqual(a.m.race.winner, rp.result.winner);
  // 回放 B：AI 邊重新生成（只用玩家決策＋種子）
  const b = stepHashes(setup, null, 'regen', rp2);
  assert.strictEqual(b.hashes.length, recHashes.length, '場 ' + i + ' regen 回放步數不同');
  for (let k = 0; k < recHashes.length; k++) assert.strictEqual(b.hashes[k], recHashes[k], '場 ' + i + ' regen 回放第 ' + k + ' 步雜湊不同');
  // verifyReplay（含檢查點）
  const v = Api.verifyReplay(rp2); assert(v.ok, '場 ' + i + ' verify：' + v.error);
  const v2 = Api.verifyReplay(rp2, { mode: 'regen' }); assert(v2.ok, '場 ' + i + ' verify regen：' + v2.error);
}
const secs = Number(process.hrtime.bigint() - t0) / 1e9;
console.log('錄製→回放：' + N + ' 場全部通過（逐步雜湊 log／regen 兩種模式＋JSON 往返＋檢查點）。');
console.log('  總步數 ' + totalSteps + '（平均 ' + (totalSteps / N).toFixed(0) + ' 步／場），玩家決策共 ' + totalDec + '（換人 ' + swapsSeen + '、技能 ' + skillsSeen + '，含 AI），甲方勝 ' + wins[0] + '／乙方勝 ' + wins[1] + '，耗時 ' + secs.toFixed(1) + ' s');
assert(swapsSeen > N && skillsSeen > N, '決策樣本太少');

// ---------- 3. 同種子兩次一致／唔同種子有差異 ----------
(function determinism() {
  const dr1 = Sim.makeRng(5), dr2 = Sim.makeRng(5);
  let diffSeed = 0, tot = 0, sameAll = true;
  for (let i = 0; i < Math.min(N, 200); i++) {
    const setup = randomSetup(1000 + i);
    const x = playRecorded(setup, Sim.makeRng(1000 + i)), y = playRecorded(setup, Sim.makeRng(1000 + i));
    const rx = Api.getReplay(x), ry = Api.getReplay(y);
    if (JSON.stringify(rx) !== JSON.stringify(ry)) sameAll = false;
    assert.strictEqual(rx.result.finalHash, ry.result.finalHash, '同種子兩次最終雜湊不同');
    // 唔同種子（只改種子；其餘同決策來源）
    const s2 = Object.assign({}, setup, { seed: setup.seed + 1 });
    const z = playRecorded(s2, Sim.makeRng(1000 + i)), rz = Api.getReplay(z);
    tot++; if (rz.result.finalHash !== rx.result.finalHash) diffSeed++;
  }
  assert(sameAll, '同種子兩次 replay JSON 不一致');
  // 種子只影響 AI 思考間隔抖動：絕大多數場次應該唔同（容許極少撞）
  assert(diffSeed / tot > 0.95, '唔同種子差異率太低 ' + diffSeed + '/' + tot);
  // 直接比較 RNG
  const a = Sim.makeRng(123), b = Sim.makeRng(123), c = Sim.makeRng(124);
  let same = true, diff = false; for (let i = 0; i < 100; i++) { const va = a(), vb = b(), vc = c(); if (va !== vb) same = false; if (va !== vc) diff = true; }
  assert(same && diff, 'RNG 種子行為');
  console.log('確定性：同種子兩次 ' + tot + ' 場 replay JSON 完全一致；唔同種子最終雜湊相異 ' + diffSeed + '/' + tot);
})();

// ---------- 4. 竄改偵測 ----------
(function tamper() {
  const setup = randomSetup(77), m = playRecorded(setup, Sim.makeRng(3));
  const rp = Api.getReplay(m);
  assert(rp.decisions.length > 0);
  const bad = JSON.parse(JSON.stringify(rp)); bad.decisions.push({ k: 10, s: 0, a: 'skill', i: -1 }); bad.decisions.sort((p, q) => p.k - q.k);
  // 加入一個多餘技能決策 → 最終雜湊必唔同（或套用失敗）
  assert(!Api.verifyReplay(bad).ok, '竄改決策應被偵測');
  const bad2 = JSON.parse(JSON.stringify(rp)); bad2.result.finalHash = '00000000';
  assert(!Api.verifyReplay(bad2).ok, '竄改結果應被偵測');
  const bad3 = JSON.parse(JSON.stringify(rp)); bad3.teams[0][0].lv += 1;
  assert(!Api.verifyReplay(bad3).ok, '竄改隊伍應被偵測');
  const bad4 = JSON.parse(JSON.stringify(rp)); bad4.v = 99;
  assert.throws(() => Api.createPlayback(bad4), /版本/);
  const bad5 = JSON.parse(JSON.stringify(rp)); bad5.sim.paramsHash = 'deadbeef';
  assert.throws(() => Api.createPlayback(bad5), /參數/);
  console.log('竄改偵測：決策／結果／隊伍／版本／參數雜湊皆被拒絕：通過');
})();

// ---------- 5. 影子隊關卡（腳本控制器）重播 ----------
(function shadow() {
  const st = Data.STAGES[2], mine = ['narrowcat', 'tingyu', 'mistfern'].map(id => ({ id, lv: 6, cond: 100 }));
  for (let i = 0; i < 20; i++) {
    const setup = { seed: 31 + i, terrains: st.terrains, teams: [mine, st.opp.team.map(d => ({ id: d.id, lv: d.lv }))], ctrls: [{ kind: 'player' }, { kind: 'shadow', script: st.opp.script }] };
    const m = playRecorded(setup, Sim.makeRng(i + 1)), rp = JSON.parse(JSON.stringify(Api.getReplay(m)));
    assert(Api.verifyReplay(rp).ok && Api.verifyReplay(rp, { mode: 'regen' }).ok, '影子隊重播 ' + i);
  }
  console.log('影子隊關卡（script 控制器）20 場重播：通過');
})();

// ---------- 6. 固定步長／插值 API ----------
(function fixedStep() {
  // 同一場以唔同「真實幀長」推進，最終狀態必須一致（累加器只決定步數，唔影響結果）
  const setup = randomSetup(5);
  const fin = [];
  [1 / 60, 1 / 30, 1 / 144, 0.1, 0.0123].forEach(fr => {
    const m = Api.createMatch(setup); let g2 = 0;
    while (!m.race.over && g2++ < 1e6) { Api.advance(m, fr, 1); const v = Api.view(m); assert(v.sides[0].pos >= 0); }
    fin.push(Api.hex8(Sim.hashState(m.race)));
  });
  assert(fin.every(h => h === fin[0]), '唔同幀長結果唔同：' + fin.join(','));
  // 插值：view 位置介乎 prev／curr
  const m = Api.createMatch(setup); Api.advance(m, 0.05, 1);
  const v = Api.view(m); assert(v.sides[0].pos >= m.prev.sides[0].pos - 1e-9 && v.sides[0].pos <= m.curr.sides[0].pos + 1e-9, '插值範圍');
  console.log('固定步長：5 種幀長（60／30／144 fps、100 ms、12.3 ms）推進同一場 → 最終雜湊一致；view 插值範圍正確：通過');
})();

Math.random = realRandom; Date.now = realNow;
console.log('\nPASS：replay.test.js 全部通過');
