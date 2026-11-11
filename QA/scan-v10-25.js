#!/usr/bin/env node
/* 3d-h1.4 回歸掃描（真參數，唔覆寫）。唔改遊戲檔。
 * 真模組 ea64ad29（tree 6ca0b083，基 6d.2 ecb2c3a3）。
 * 路線同 economy-v102：route-sweep main({ fpats:2, mg2:true })。經濟＝mg2Hook＋每日掉 5 粒。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || '/tmp/glimmer-3d14/src/glimmer-a';
const S = require(path.join(ROOT, 'src/sim.js'));
const D = require(path.join(ROOT, 'src/data.js'));
require(path.join(ROOT, 'src/systems.js'));
const B = require(path.join(ROOT, 'src/systems2.js'));
const X = require(path.join(ROOT, 'src/systems.js'));
const SW = require(path.join(ROOT, 'tools/route-sweep.js'));
const P = D.PARAMS, M2 = P.minigames2, C = P.evo6.branch;
const N = +(process.env.N || 1000);
const ECON_N = +(process.env.ECON_N || 200);
const FP = 2, DROPS = 5;
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const NAMES = Object.keys(SW.SCHED);
const PROG = { ember: 14.03, soft: 10.92, dust: 4.95, moon: 18.73 };
const LOCK = { lumi: 5.47, crystal: 15.32, moon: 18.72, ember: 14.00, soft: 10.92, dust: 4.95, nightMoon: 82.4, lightShards: 19 };

function med(a) { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; }
function juv(t) { const s = S.newState(t, 9); s.stage = 'juvenile'; s.cq = 50; s.ev = []; return s; }
function em(s) { const b = s.evo && s.evo.b5 && s.evo.b5.juvenile; return b ? b.ember || 0 : 0; }
function bk(s) { return (s.evo && s.evo.b5 && s.evo.b5.juvenile) || {}; }
function nRoute(s) { return s.evo && s.evo.mgRoute ? s.evo.mgRoute.n : 0; }
function arm(ms, h) { S.setNowFn(() => ms); S.setHourFn(() => h); S.setWeatherFn(() => 'clear'); }

function prove() {
  const out = { params: { routePtsPerGame: M2.routePtsPerGame, routeGamesPerDay: M2.routeGamesPerDay, kindsMgW: C.kinds.mg.w } };
  const night = new Date(2026, 10, 3, 21, 0, 0).getTime();
  const day = new Date(2026, 10, 3, 13, 0, 0).getTime();
  arm(night, 21);
  const sn = juv(night);
  const moon0 = bk(sn).moon || 0;
  for (let i = 0; i < 4; i++) B.gameFinish(sn, 'bounce', 30, night + i * 60e3);
  const afterNight = { ember: em(sn), n: nRoute(sn), moon: (bk(sn).moon || 0) - moon0 };
  arm(day, 13);
  const e0 = em(sn);
  const dayRound = B.gameFinish(sn, 'bounce', 30, day);
  out.repro = { afterNight, dayEmber: +(em(sn) - e0).toFixed(4), dayShards: dayRound.shards, n: nRoute(sn) };
  out.reproOk = afterNight.ember === 0 && afterNight.n === 0 && afterNight.moon === 4 && out.repro.dayEmber === 1 && dayRound.shards > 0 && nRoute(sn) === 1;

  const dawn = new Date(2026, 10, 4, 7, 0, 0).getTime();
  arm(dawn, 7);
  const sd = juv(dawn);
  const tide0 = bk(sd).tide || 0;
  B.gameFinish(sd, 'bounce', 30, dawn);
  out.dew = { ember: em(sd), n: nRoute(sd), tide: (bk(sd).tide || 0) - tide0 };
  out.dewOk = out.dew.ember === 0 && out.dew.n === 0 && out.dew.tide === 1;

  arm(day, 13);
  const sm = juv(day);
  const steps = [];
  const push = (label, emberDelta, extra) => steps.push(Object.assign({ label, ember: emberDelta }, extra));
  let x = em(sm);
  let r = B.gameFinish(sm, 'bounce', 30, day);
  push('v2', +(em(sm) - x).toFixed(4), { shards: r.shards });
  x = em(sm); r = B.gameFinish(sm, 'ghide', 8, day + 60e3, { firstHits: 1 });
  push('v2', +(em(sm) - x).toFixed(4), { shards: r.shards });
  x = em(sm); const gr = sm.grains; const sh = X.wallet(sm, day).today;
  r = S.mgApply(sm, 100, day + 120e3);
  push('v1', +(em(sm) - x).toFixed(4), { grains: sm.grains - gr, walletSame: X.wallet(sm, day).today === sh });
  x = em(sm); sm.ev = []; sm.mg.overlayAt = 0;
  const ov = S.overlayOpenGame(sm, day + 800e3);
  push('float', +(em(sm) - x).toFixed(4), { ok: ov.ok, shards: ov.sys12b ? ov.sys12b.shards : null, ev: sm.ev.some(e => e.type === 'overlayMg' && e.grains === ov.reward.grains) });
  x = em(sm); r = B.gameFinish(sm, 'bounce', 30, day + 900e3);
  push('5th', +(em(sm) - x).toFixed(4), { shards: r.shards, n: nRoute(sm) });
  out.mixed = steps;
  out.mixedOk = steps[0].ember === 1 && steps[1].ember === 1 && steps[2].ember === 1 && steps[2].grains > 0 && steps[2].walletSame
    && steps[3].ember === 1 && steps[3].ev && steps[3].shards > 0
    && steps[4].ember === 0 && steps[4].shards > 0 && steps[4].n === 4;

  const fx = S.newState(1, 7); fx.stage = 'sprout';
  fx.evo = { evIn: {}, care: {}, b5: { sprout: { all: 12, tide: 3, shroom: 0, crystal: 0, moon: 0, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 50 } } };
  const Br = S.branch5Check(fx);
  const pct = Br.score.tide ? (Br.sys.capped.tide / Br.score.tide) * 100 : 999;
  out.cap25 = Math.abs(pct - 25) < 0.05;
  out.configUntouched = M2.routePtsPerGame === 1 && M2.routeGamesPerDay === 4 && C.kinds.mg.w === 2;
  S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
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
  if (!proof.reproOk || !proof.dewOk || !proof.mixedOk || !proof.cap25 || !proof.configUntouched) {
    console.error(JSON.stringify(proof, null, 2));
    process.exit(1);
  }
  const econ = economy();
  const R = SW.main(N, true, { fpats: FP, mg2: true });
  const tables = {};
  const total = R.total;
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
  const lockDiff = {};
  for (const id of ['lumi', 'crystal', 'moon', 'ember', 'soft', 'dust']) {
    const d = +(total[id] - LOCK[id]).toFixed(2);
    if (Math.abs(d) > 3) lockDiff[id] = { qa: total[id], lock: LOCK[id], d };
  }
  const nmD = +(tables['夜貓'].moon - LOCK.nightMoon).toFixed(2);
  if (Math.abs(nmD) > 3) lockDiff.nightMoon = { qa: tables['夜貓'].moon, lock: LOCK.nightMoon, d: nmD };
  const shD = econ.out['疏玩'].playMed - LOCK.lightShards;
  if (Math.abs(shD) > 3) lockDiff.lightShards = { qa: econ.out['疏玩'].playMed, lock: LOCK.lightShards, d: shD };

  const near = {};
  for (const id of Object.keys(PROG)) {
    const d = +(total[id] - PROG[id]).toFixed(2);
    near[id] = { qa: total[id], prog: PROG[id], d };
    if (Math.abs(d) > 3) routeDiff[id] = near[id];
  }
  const out = {
    doc: '3d-h1.4 回歸。真參數。對 scan-v10-21 鎖定 16 項。權限閂。',
    sim: 'ea64ad29056735dbdf0e884be50aa8ab5f2ba8fe',
    tree: '6ca0b083fa7209c1fd4bb77007249255377048e4',
    N, ECON_N, fpats: FP, drops: DROPS,
    proof, checks, passN: checks.filter(c => c[1] === '✅').length,
    fail: checks.filter(c => c[1] === '❌').map(c => c[0]),
    total, tables, cqMed: cq, cqs: Object.fromEntries(NAMES.map(n => [n, R.tables[n].cqMed])),
    nightMoon: tables['夜貓'].moon, shroomMax, brightMax,
    econ: econ.out, over30: econ.over, routeDiff, lockDiff, near,
    mg2stat: R.mg2, configAfter: { w: M2.routePtsPerGame, cap: M2.routeGamesPerDay, kinds: C.kinds.mg.w },
    ms: Date.now() - t0,
  };
  fs.writeFileSync(process.env.OUT || path.join(__dirname, 'scan-v10-25.json'), JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    ms: out.ms, passN: out.passN, fail: out.fail, total, cq, nightMoon: out.nightMoon,
    econ: econ.out, near, routeDiff, lockDiff, repro: proof.repro, mixed: proof.mixed,
    light: { soft: tables['疏玩'].soft, dust: tables['疏玩'].dust }, configAfter: out.configAfter,
  }, null, 2));
}
main();
