#!/usr/bin/env node
/* §7 v10.3 鎖定掃描。外掛，唔改 code branch。
 * 真 sim 669bc46：decideBranch、一日一抽天氣、systems.js 委託／星星碎。
 * 時間表、主 rng、小遊戲同 scan-v10。懸浮假設同遊程經濟測試：每日摸頭 2 下、星星碎 5 粒。
 * N=1000 路線；星星碎 200 seed × 7 日。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || '/tmp/glimmer-v103/src/glimmer-a';
const S = require(path.join(ROOT, 'src/sim.js'));
const D = require(path.join(ROOT, 'src/data.js'));
const X = require(path.join(ROOT, 'src/systems.js'));
const SW = require(path.join(ROOT, 'tools/route-sweep.js'));
const P = D.PARAMS, C = P.evo6.branch, Q = P.systems12.quests, W = C.weather.route;
const N = +(process.env.N || 1000);
const ECON_N = +(process.env.ECON_N || 200);
const FP = 2, DROPS = 5;
const PROG = { shroom: 7.57, bright: 6.73, crystal: 14.00, feedShroom: 25.3, sparseMed: 17, otherMed: 20 };
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];

let maxSys = 0;
const orig = S.decideBranch;
S.decideBranch = function (s) {
  const r = orig(s);
  const b = r && r.b5;
  if (b && b.sys && b.score) {
    for (const k of Object.keys(b.score)) {
      const tot = +b.score[k] || 0, cap = +(b.sys.capped && b.sys.capped[k]) || 0;
      if (tot > 0) maxSys = Math.max(maxSys, cap / tot * 100);
    }
  }
  return r;
};

function checkCode() {
  const items = [];
  const mark = (name, ok, info) => items.push({ name, ok, info });
  mark('菇傘雨 0.8', W.rain && W.rain.w === 0.8, W.rain);
  mark('菇傘陰 0.4', W.overcast && W.overcast.w === 0.4, W.overcast);
  mark('菇傘霧 0.4', W.fog && W.fog.w === 0.4, W.fog);
  mark('委託池餵／玩／摸頭', JSON.stringify(Q.pool) === JSON.stringify(['feed', 'play', 'pat']), Q.pool);
  mark('淋水只係水珠領先', Q.rinseIfLead === 'tide' && !Q.pool.includes('rinse'), Q.rinseIfLead);
  mark('每張 4 碎', Q.perItem === 4, Q.perItem);
  mark('3 張齊 +3', Q.allBonus === 3 && Q.perDay === 3, Q.allBonus);
  mark('委託日上限 15', P.systems12.wallet.questCap === 15, P.systems12.wallet.questCap);
  mark('總上限 30', C.systems.stardustDailyCap === 30, C.systems.stardustDailyCap);
  mark('未完成留 1 日、最多 6 張', Q.keepDays === 1 && Q.maxHeld === 6, { keepDays: Q.keepDays, maxHeld: Q.maxHeld });
  mark('每張路線分 ⅓', Q.routeBonus === 'perItem' && C.systems.sources.questRoute.pts === 1 && Q.perDay === 3, Q.routeBonus);
  mark('懸浮摸頭每日最多 12', Q.overlayPatPerDay === 12, Q.overlayPatPerDay);
  const pr = Object.fromEntries(C.weather.probs);
  mark('天氣一日一抽 60/20/15/5', P.systems12.weather.perDay === true && pr.clear === 60 && pr.overcast === 20 && pr.rain === 15 && pr.fog === 5, { perDay: P.systems12.weather.perDay, pr });
  const floatRoot = process.env.FLOAT || '/tmp/float-v103/src/floating-pet-mvp/android/app/src/main/assets/pet/evo';
  let clips = 0, files = 0;
  if (fs.existsSync(floatRoot)) {
    for (const f of fs.readdirSync(floatRoot)) {
      if (!f.endsWith('.json')) continue;
      files++;
      const j = fs.readFileSync(path.join(floatRoot, f), 'utf8');
      if (j.includes('leaf_umbrella') && j.includes('shiver')) clips++;
    }
  }
  mark('懸浮有撐葉／打冷震', files > 0 && clips === files, { files, withBoth: clips });
  return items;
}

function med(a) { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; }

function economy() {
  const out = {};
  let over = 0;
  for (const name of Object.keys(SW.SCHED)) {
    const play = [], all = [];
    for (let sd = 1; sd <= ECON_N; sd++) {
      const r = SW.run(name, sd, { days: 7, drops: DROPS, fpats: FP });
      for (let d = 0; d < 7; d++) {
        const k = S.dayKey(new Date(2026, 10, 2).getTime() + d * 864e5);
        const v = r.shards[k] || 0;
        all.push(v);
        if (r.played[k]) play.push(v);
        if (v > 30) over++;
      }
    }
    out[name] = { playMed: med(play), allMed: med(all), max: Math.max(...all), nPlay: play.length };
  }
  return { out, over };
}

function main() {
  const t0 = Date.now();
  const code = checkCode();
  const econ = economy();
  {
    const fx = S.newState(1, 7); fx.stage = 'sprout';
    fx.evo = { evIn: {}, care: {}, b5: { sprout: { all: 12, tide: 3, shroom: 6, crystal: 0, moon: 3, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 50 } } };
    const B = S.branch5Check(fx);
    const tot = B.score.tide || 0, cap = (B.sys.capped && B.sys.capped.tide) || 0;
    if (tot > 0) maxSys = Math.max(maxSys, cap / tot * 100);
  }
  const R = SW.main(N, true, { fpats: FP });
  const tables = {};
  for (const name of Object.keys(R.tables)) {
    const pc = {};
    for (const id of PATHS) pc[id] = R.tables[name].pct[id] || 0;
    tables[name] = pc;
  }
  const total = {};
  for (const id of PATHS) total[id] = R.total[id] || 0;
  const cq = R.tables['疏玩'].cqMed;
  const brightMax = Math.max(...Object.keys(tables).map(n => tables[n].bright));
  const shroomMax = Math.max(...Object.keys(tables).map(n => tables[n].shroom));
  const mark = (ok) => ok ? '✅' : '❌';
  const nine = PATHS.every(id => total[id] >= 2 - 1e-9);
  const kindsOk = Object.keys(tables).every(n => PATHS.filter(id => tables[n][id] >= 2 - 1e-9).length >= 2);
  const capOk = Object.keys(tables).every(n => PATHS.every(id => tables[n][id] <= 85 + 1e-9));
  const others = Object.keys(econ.out).filter(n => n !== '疏玩');
  const checks = [
    ['9 條路出齊（每條≥2%）', mark(nine), PATHS.filter(id => total[id] < 2).map(id => id + ' ' + total[id]).join(', ') || '齊'],
    ['每表≥2 結局（每個≥2%）', mark(kindsOk), null],
    ['單一≤85%', mark(capOk), null],
    ['螢絨 3–10%', mark(total.lumi >= 3 && total.lumi <= 10), total.lumi],
    ['每表菇傘≤30%', mark(shroomMax <= 30), shroomMax],
    ['晶角全體≥5%', mark(total.crystal >= 5), total.crystal],
    ['月眠全體≥5%', mark(total.moon >= 5), total.moon],
    ['每表燦光≤50%', mark(brightMax <= 50), brightMax],
    ['疏玩柔光＋微塵', mark(tables['疏玩'].soft >= 2 && tables['疏玩'].dust >= 2), tables['疏玩'].soft + '/' + tables['疏玩'].dust],
    ['疏玩 CQ 15–35', mark(cq >= 15 && cq <= 35), cq],
    ['新系統路線分≤25%', mark(maxSys <= 25 + 1e-6), +maxSys.toFixed(2)],
    ['疏玩上線日星碎 15–30', mark(econ.out['疏玩'].playMed >= 15 && econ.out['疏玩'].playMed <= 30), econ.out['疏玩'].playMed],
    ['其他 5 表每日星碎 15–30', mark(others.every(n => econ.out[n].allMed >= 15 && econ.out[n].allMed <= 30)), others.map(n => n + ' ' + econ.out[n].allMed).join(' ')],
    ['冇一日穿 30', mark(econ.over === 0 && Object.values(econ.out).every(e => e.max <= 30)), econ.over],
  ];
  const prog = {
    shroom: { prog: PROG.shroom, qa: total.shroom, d: +(total.shroom - PROG.shroom).toFixed(2) },
    bright: { prog: PROG.bright, qa: total.bright, d: +(total.bright - PROG.bright).toFixed(2) },
    crystal: { prog: PROG.crystal, qa: total.crystal, d: +(total.crystal - PROG.crystal).toFixed(2) },
    feedShroom: { prog: PROG.feedShroom, qa: tables['餵食狂'].shroom, d: +(tables['餵食狂'].shroom - PROG.feedShroom).toFixed(2) },
    sparseMed: { prog: PROG.sparseMed, qa: econ.out['疏玩'].playMed },
    otherMed: { prog: PROG.otherMed, qa: others.map(n => econ.out[n].allMed) },
  };
  const out = {
    doc: '§7 v10.3。真 sim 669bc46 decideBranch＋systems.js。',
    sim: '669bc46efd27402e4a6411643816b9276eb8c143',
    float: '19ebcc9adbfd14f51f19a84be3a16c2ac5e99301',
    N, ECON_N, fpats: FP, drops: DROPS,
    code, checks, passN: checks.filter(c => c[1] === '✅').length,
    total, tables, cqMed: cq, brightMax, shroomMax, maxSys: +maxSys.toFixed(2),
    econ: econ.out, over30: econ.over, prog, ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v10-3-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    ms: out.ms, passN: out.passN, fail: checks.filter(c => c[1] === '❌').map(c => c[0]),
    codeBad: code.filter(c => !c.ok).map(c => c.name),
    total, cq, econ: econ.out, maxSys: out.maxSys, prog, shroomMax, brightMax,
  }, null, 2));
  process.exitCode = (checks.some(c => c[1] === '❌') || code.some(c => !c.ok)) ? 1 : 0;
}
main();
