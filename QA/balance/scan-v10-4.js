#!/usr/bin/env node
/* §7 v10.4 掃描（sys12 第 2 批＋小遊戲 v2）。唔改 code branch。
 * 真模組 bf57cb2：decideBranch、一日一抽、委託、小圃隨機花、散步、徽章、mg2 路線分。
 * 時間表／主 rng／小遊戲槽同 scan-v10。懸浮：摸頭 2／日、星星碎 5 粒。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || '/tmp/glimmer-b2/src/glimmer-a';
const S = require(path.join(ROOT, 'src/sim.js'));
const D = require(path.join(ROOT, 'src/data.js'));
const X = require(path.join(ROOT, 'src/systems.js'));
const B = require(path.join(ROOT, 'src/systems2.js'));
const M2 = require(path.join(ROOT, 'src/minigames2.js'));
const BOT = require(path.join(ROOT, 'tests/mg2-bots.js'));
const SW = require(path.join(ROOT, 'tools/route-sweep.js'));
const P = D.PARAMS, C = P.evo6.branch, Q = P.systems12.quests, G = P.systems12b, W = C.weather.route;
const N = +(process.env.N || 1000);
const ECON_N = +(process.env.ECON_N || 200);
const FP = 2, DROPS = 5;
const PROG = {
  econ: { 勤力: 24, 普通: 22, 疏玩: 19, 夜貓: 22, 早起: 22, 餵食狂: 22 },
  routes: { lumi: 5.32, tide: 15.13, shroom: 7.57, crystal: 14.12, moon: 16.65, ember: 14.57, bright: 6.73, soft: 12.33, dust: 7.58 },
  max: 30,
};
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const NAMES = Object.keys(SW.SCHED);

function med(a) { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; }

function sessionHook(seed, gst) {
  const garden = SW.gardenHook(seed, 'rand', gst);
  const rng = S.makeRng(seed * 7919 + 503);
  return (s, now) => {
    garden(s, now);
    if (s.stage === 'egg') return;
    if (rng() < 0.4) {
      const night = M2.fireflyOpen(new Date(now).getHours());
      const ks = night ? ['bounce', 'ghide', 'firefly'] : ['bounce', 'ghide'];
      const k = ks[Math.floor(rng() * ks.length)];
      const g = BOT.playBot(M2, k, (rng() * 1e9) | 1, rng(), rng);
      B.gameFinish(s, k, g.score, now, k === 'ghide' ? { firstHits: g.firstHits } : {});
    }
    for (let i = 0; i < 3; i++) B.walkRoll(s, now, { rng });
    B.tick(s, now);
  };
}

function checkCode() {
  const items = [];
  const mark = (name, ok, info) => items.push({ name, ok, info });
  const pr = Object.fromEntries(C.weather.probs);
  mark('菇傘雨 0.8／陰霧 0.4', W.rain.w === 0.8 && W.overcast.w === 0.4 && W.fog.w === 0.4, W);
  mark('天氣一日一抽 60/20/15/5', P.systems12.weather.perDay === true && pr.clear === 60 && pr.overcast === 20 && pr.rain === 15 && pr.fog === 5, pr);
  mark('委託池餵玩摸頭、淋水只水珠', JSON.stringify(Q.pool) === '["feed","play","pat"]' && Q.rinseIfLead === 'tide', Q.pool);
  mark('每張4、齊+3、上限15/30、留1日最多6、摸頭12', Q.perItem === 4 && Q.allBonus === 3 && Q.perDay === 3 && P.systems12.wallet.questCap === 15 && C.systems.stardustDailyCap === 30 && Q.keepDays === 1 && Q.maxHeld === 6 && Q.overlayPatPerDay === 12, Q);
  mark('火苗 mg +2', C.kinds.mg.w === 2 && G.games.countsMg === true, C.kinds.mg);
  mark('v1 預設閂', G.games.v1Enabled === false, G.games.v1Enabled);
  mark('追螢火夜窗', M2.fireflyOpen(16.983) === false && M2.fireflyOpen(17) === true && M2.fireflyOpen(6.983) === true && M2.fireflyOpen(7) === false, { from: P.evo6.nightFrom, to: P.evo6.nightTo });
  mark('冷卻 600s', C.overlayMg.cooldownSec === 600, C.overlayMg.cooldownSec);
  mark('小物 30、每日 5、10%', G.walk.items.length === 30 && G.walk.perDay === 5 && G.walk.chance === 0.1 && G.walk.nightHours[0] === 20 && G.walk.nightHours[1] === 3, G.walk.items.length);
  mark('徽章 30、日菊唔加路線分', G.badges.list.length === 30 && G.badges.total === 30 && G.garden.daisy.shards === 2 && G.garden.bloomPts === 3, G.badges.list.length);
  const fx = S.newState(1, 7); fx.stage = 'sprout';
  fx.evo = { evIn: {}, care: {}, b5: { sprout: { all: 12, tide: 3, shroom: 0, crystal: 0, moon: 0, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 50 } } };
  const Br = S.branch5Check(fx);
  const pct = Br.score.tide ? (Br.sys.capped.tide / Br.score.tide) * 100 : 999;
  mark('新系統分封頂 25%', Math.abs(pct - 25) < 0.05, +pct.toFixed(2));
  return items;
}

function economy() {
  const out = {};
  let over = 0;
  for (const name of NAMES) {
    const play = [], all = [];
    for (let sd = 1; sd <= ECON_N; sd++) {
      const r = SW.run(name, sd, { days: 7, drops: DROPS, fpats: FP, onSession: sessionHook(sd, { blooms: 0, byRoute: {} }) });
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

function routes() {
  const gst = { blooms: 0, byRoute: {} };
  const all = {}, tables = {}, cqs = {};
  for (const name of NAMES) {
    const c = {}; const cq = [];
    for (let i = 1; i <= N; i++) {
      const r = SW.run(name, i, { fpats: FP, drops: DROPS, onSession: sessionHook(i, gst) });
      c[r.form] = (c[r.form] || 0) + 1;
      all[r.form] = (all[r.form] || 0) + 1;
      cq.push(r.cq);
    }
    cq.sort((a, b) => a - b);
    const pc = {};
    for (const id of PATHS) pc[id] = +(((c[id] || 0) / N) * 100).toFixed(2);
    tables[name] = pc;
    cqs[name] = +cq[N >> 1].toFixed(2);
  }
  const total = {};
  const nAll = N * NAMES.length;
  for (const id of PATHS) total[id] = +(((all[id] || 0) / nAll) * 100).toFixed(2);
  return { tables, total, cqs, blooms: gst.blooms, byRoute: gst.byRoute };
}

function main() {
  const t0 = Date.now();
  const code = checkCode();
  const econ = economy();
  const R = routes();
  const tables = R.tables, total = R.total, cq = R.cqs['疏玩'];
  const brightMax = Math.max(...NAMES.map(n => tables[n].bright));
  const shroomMax = Math.max(...NAMES.map(n => tables[n].shroom));
  const mark = (ok) => ok ? '✅' : '❌';
  const others = NAMES.filter(n => n !== '疏玩');
  const docBand = [15, 30];
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
    ['新系統路線分≤25%', mark(code.find(c => c.name.startsWith('新系統')).ok), code.find(c => c.name.startsWith('新系統')).info],
    ['疏玩上線日星碎 15–30', mark(econ.out['疏玩'].playMed >= docBand[0] && econ.out['疏玩'].playMed <= docBand[1]), econ.out['疏玩'].playMed],
    ['其他 5 表每日星碎 15–30', mark(others.every(n => econ.out[n].allMed >= docBand[0] && econ.out[n].allMed <= docBand[1] && econ.out[n].playMed >= docBand[0] && econ.out[n].playMed <= docBand[1])), others.map(n => n + ' ' + econ.out[n].allMed).join(' ')],
    ['冇一日穿 30', mark(econ.over === 0), econ.over],
  ];
  const routeDiff = {};
  for (const id of PATHS) {
    const d = +(total[id] - PROG.routes[id]).toFixed(2);
    if (Math.abs(d) > 3) routeDiff[id] = { qa: total[id], prog: PROG.routes[id], d };
  }
  const econDiff = {};
  for (const n of NAMES) {
    const d = econ.out[n].playMed - PROG.econ[n];
    if (Math.abs(d) > 3) econDiff[n] = { qa: econ.out[n].playMed, prog: PROG.econ[n], d };
  }
  const out = {
    doc: '§7 v10.4。真 sim bf57cb2。小圃隨機花＋散步＋徽章＋mg2。',
    sim: 'bf57cb23a4fc743c8b89c6d9ea596f0c582f0407',
    tree: 'b6e89349fcd7b06d7aac090bd8f620039eda6f76',
    N, ECON_N, fpats: FP, drops: DROPS, garden: 'rand',
    docBand: 'pet-template-v1／systems12-v1 仍然寫每日 15–30，冇改遊策定數',
    code, checks, passN: checks.filter(c => c[1] === '✅').length,
    total, tables, cqMed: R && cq, cqs: R.cqs, brightMax, shroomMax,
    nightMoon: tables['夜貓'].moon, blooms: R.blooms, bloomByRoute: R.byRoute,
    econ: econ.out, over30: econ.over, routeDiff, econDiff,
    ms: Date.now() - t0,
  };
  fs.writeFileSync(process.env.OUT || path.join(__dirname, 'scan-v10-4-result.json'), JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    ms: out.ms, passN: out.passN, fail: checks.filter(c => c[1] === '❌').map(c => c[0]),
    codeBad: code.filter(c => !c.ok).map(c => c.name),
    total, cq, nightMoon: tables['夜貓'].moon, econ: econ.out, routeDiff, econDiff, blooms: R.blooms, shroomMax, brightMax,
  }, null, 2));
}
main();
