#!/usr/bin/env node
/* mg2.2 真參數掃描。唔改遊戲檔，掃描唔覆寫 routePtsPerGame／routeGamesPerDay。
 * 真模組 05157ca。路線同 tests/economy-v102.test.js：route-sweep main({ fpats:2, mg2:true })，
 * 用 tools/route-sweep.js mg2Hook（真 gameFinish）。經濟＝同一 hook＋每日掉 5 粒。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || '/tmp/glimmer-mg22/src/glimmer-a';
const S = require(path.join(ROOT, 'src/sim.js'));
const D = require(path.join(ROOT, 'src/data.js'));
require(path.join(ROOT, 'src/systems.js'));
const B = require(path.join(ROOT, 'src/systems2.js'));
const X = require(path.join(ROOT, 'src/systems.js'));
const SW = require(path.join(ROOT, 'tools/route-sweep.js'));
const P = D.PARAMS, M2 = P.minigames2, C = P.evo6.branch, Q = P.systems12.quests;
const N = +(process.env.N || 1000);
const ECON_N = +(process.env.ECON_N || 200);
const FP = 2, DROPS = 5;
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const NAMES = Object.keys(SW.SCHED);
const PROG = { ember: 13.80, soft: 11.02, dust: 4.95, moon: 18.73 };

function med(a) { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; }
function emberOf(s) { const b = s.evo && s.evo.b5 && s.evo.b5.juvenile; return b ? b.ember : 0; }
function arm(ms, h) { S.setNowFn(() => ms); S.setHourFn(() => h); S.setWeatherFn(() => 'clear'); }

function prove() {
  const out = { params: { routePtsPerGame: M2.routePtsPerGame, routeGamesPerDay: M2.routeGamesPerDay, kindsMgW: C.kinds.mg.w } };
  const t0 = new Date(2026, 10, 2, 13, 0, 0).getTime();
  arm(t0, 13);
  const s = S.newState(t0, 9); s.stage = 'juvenile'; s.cq = 50;
  const deltas = [], shards = [];
  for (let i = 0; i < 6; i++) {
    const e0 = emberOf(s);
    const r = B.gameFinish(s, 'bounce', 30, t0 + i * 60e3);
    deltas.push(+(emberOf(s) - e0).toFixed(4));
    shards.push(r.shards);
  }
  out.day = { deltas, shards, n: s.evo.mgRoute && s.evo.mgRoute.n };
  out.dayOk = deltas.slice(0, 4).every(d => d === 1) && deltas[4] === 0 && deltas[5] === 0 && shards.slice(0, 5).every(n => n > 0) && s.evo.mgRoute.n === 4;

  const t3 = t0 + 2 * 864e5;
  arm(t3, 13);
  const s2 = S.newState(t3, 9); s2.stage = 'juvenile'; s2.cq = 50;
  const e0 = emberOf(s2);
  const ov = [];
  for (let i = 0; i < 3; i++) {
    const x = emberOf(s2);
    const r = S.overlayOpenGame(s2, t3 + i * 700e3);
    ov.push({ ok: r.ok, ember: +(emberOf(s2) - x).toFixed(4), shards: r.sys12b ? r.sys12b.shards : null });
  }
  const g = B.gameFinish(s2, 'ghide', 8, t3 + 3 * 700e3, { firstHits: 1 });
  const g5 = B.gameFinish(s2, 'bounce', 30, t3 + 4 * 700e3);
  out.shared = { ov, gShards: g.shards, gEmber: +(emberOf(s2) - e0 - 3).toFixed(4), fifthEmber: +(emberOf(s2) - (e0 + 4)).toFixed(4), fifthShards: g5.shards, n: s2.evo.mgRoute.n };
  out.sharedOk = ov.every(o => o.ok && o.ember === 1 && o.shards > 0) && out.shared.gEmber === 1 && out.shared.fifthEmber === 0 && out.shared.fifthShards > 0 && s2.evo.mgRoute.n === 4;

  const tn = new Date(2026, 10, 3, 21, 0, 0).getTime();
  arm(tn, 21);
  const sn = S.newState(tn, 9); sn.stage = 'juvenile'; sn.cq = 50;
  const win = [];
  for (let i = 0; i < 4; i++) { const x = emberOf(sn); B.gameFinish(sn, 'bounce', 30, tn + i * 60e3); win.push(+(emberOf(sn) - x).toFixed(4)); }
  const day = new Date(2026, 10, 3, 13, 0, 0).getTime();
  arm(day, 13);
  const x = emberOf(sn);
  const after = B.gameFinish(sn, 'bounce', 30, day);
  out.window = { nightEmber: win, cap: sn.evo.mgRoute.n, dayEmber: +(emberOf(sn) - x).toFixed(4), dayShards: after.shards };
  out.windowEatsCap = win.every(d => d === 0) && sn.evo.mgRoute.n === 4 && out.window.dayEmber === 0 && after.shards > 0;
  S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
  const fx = S.newState(1, 7); fx.stage = 'sprout';
  fx.evo = { evIn: {}, care: {}, b5: { sprout: { all: 12, tide: 3, shroom: 0, crystal: 0, moon: 0, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 50 } } };
  const Br = S.branch5Check(fx);
  const pct = Br.score.tide ? (Br.sys.capped.tide / Br.score.tide) * 100 : 999;
  out.cap25 = Math.abs(pct - 25) < 0.05;
  out.configUntouched = M2.routePtsPerGame === 1 && M2.routeGamesPerDay === 4 && C.kinds.mg.w === 2;
  return out;
}

function economy() {
  const out = {};
  let over = 0;
  for (const name of NAMES) {
    const play = [], all = [];
    for (let sd = 1; sd <= ECON_N; sd++) {
      const r = SW.run(name, sd, { days: 7, drops: DROPS, fpats: FP, onSession: SW.mg2Hook(sd, name, {}) });
      for (let d = 0; d < 7; d++) {
        const k = S.dayKey(new Date(2026, 10, 2).getTime() + d * 864e5);
        const v = r.shards[k] || 0;
        all.push(v);
        if (r.played[k]) play.push(v);
        if (v > 30) over++;
      }
    }
    out[name] = { playMed: med(play), allMed: med(all), max: Math.max(...all) };
  }
  return { out, over };
}

function main() {
  const t0 = Date.now();
  const proof = prove();
  if (!proof.dayOk || !proof.sharedOk || !proof.configUntouched) {
    console.error(JSON.stringify(proof, null, 2));
    process.exit(1);
  }
  const econ = economy();
  const R = SW.main(N, true, { fpats: FP, mg2: true });
  const tables = {}, total = R.total;
  for (const n of NAMES) {
    tables[n] = {};
    for (const id of PATHS) tables[n][id] = R.tables[n].pct[id];
  }
  const cq = R.tables['疏玩'].cqMed;
  const mark = (ok) => ok ? '✅' : '❌';
  const brightMax = Math.max(...NAMES.map(n => tables[n].bright));
  const shroomMax = Math.max(...NAMES.map(n => tables[n].shroom));
  const others = NAMES.filter(n => n !== '疏玩');
  const checks = [
    ['9 條路出齊（每條≥2%）', mark(PATHS.every(id => total[id] >= 2)), PATHS.filter(id => total[id] < 2).join(',') || '齊'],
    ['每表≥2 結局（每個≥2%）', mark(NAMES.every(n => PATHS.filter(id => tables[n][id] >= 2).length >= 2)), null],
    ['單一≤85%', mark(NAMES.every(n => PATHS.every(id => tables[n][id] <= 85))), tables['夜貓'].moon],
    ['螢絨 3–10%', mark(total.lumi >= 3 && total.lumi <= 10), total.lumi],
    ['每表菇傘≤30%', mark(shroomMax <= 30), shroomMax],
    ['晶角全體≥5%', mark(total.crystal >= 5), total.crystal],
    ['月眠全體≥5%', mark(total.moon >= 5), total.moon],
    ['每表燦光≤50%', mark(brightMax <= 50), brightMax],
    ['疏玩柔光＋微塵', mark(tables['疏玩'].soft >= 2 && tables['疏玩'].dust >= 2), tables['疏玩'].soft + '/' + tables['疏玩'].dust],
    ['疏玩 CQ 15–35', mark(cq >= 15 && cq <= 35), cq],
    ['新系統路線分≤25%', mark(proof.cap25), 25],
    ['疏玩上線日星碎 15–30', mark(econ.out['疏玩'].playMed >= 15 && econ.out['疏玩'].playMed <= 30), econ.out['疏玩'].playMed],
    ['其他 5 表每日星碎 15–30', mark(others.every(n => econ.out[n].playMed >= 15 && econ.out[n].playMed <= 30 && econ.out[n].allMed >= 15 && econ.out[n].allMed <= 30)), others.map(n => n + ' ' + econ.out[n].playMed).join(' ')],
    ['冇一日穿 30', mark(econ.over === 0), econ.over],
    ['火苗全體 12–18%', mark(total.ember >= 12 && total.ember <= 18), total.ember],
    ['柔光全體≥10%', mark(total.soft >= 10), total.soft],
  ];
  const routeDiff = {};
  for (const id of Object.keys(PROG)) {
    const d = +(total[id] - PROG[id]).toFixed(2);
    if (Math.abs(d) > 3) routeDiff[id] = { qa: total[id], prog: PROG[id], d };
  }
  const near = {};
  for (const id of Object.keys(PROG)) near[id] = { qa: total[id], prog: PROG[id], d: +(total[id] - PROG[id]).toFixed(2) };
  const out = {
    doc: 'mg2.2 真參數。routePtsPerGame=1、routeGamesPerDay=4。冇掃描覆寫。',
    sim: '05157ca1c362bd4d25c054a84872895f44d894b0',
    tree: 'b10d5ff2e3565f900273bd08616ca9feb363758d',
    N, ECON_N, fpats: FP, drops: DROPS, mg2: 'route-sweep mg2Hook',
    proof, checks, passN: checks.filter(c => c[1] === '✅').length,
    fail: checks.filter(c => c[1] === '❌').map(c => c[0]),
    total, tables, cqMed: cq, cqs: Object.fromEntries(NAMES.map(n => [n, R.tables[n].cqMed])),
    nightMoon: tables['夜貓'].moon, shroomMax, brightMax,
    econ: econ.out, over30: econ.over, routeDiff, near,
    mg2: R.mg2, configAfter: { w: M2.routePtsPerGame, cap: M2.routeGamesPerDay, kinds: C.kinds.mg.w },
    ms: Date.now() - t0,
  };
  fs.writeFileSync(process.env.OUT || path.join(__dirname, 'scan-v10-6-result.json'), JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    ms: out.ms, passN: out.passN, fail: out.fail, total, cq, nightMoon: out.nightMoon,
    econ: econ.out, near, routeDiff, windowEatsCap: proof.windowEatsCap, configAfter: out.configAfter,
    light: { soft: tables['疏玩'].soft, dust: tables['疏玩'].dust },
  }, null, 2));
}
main();
