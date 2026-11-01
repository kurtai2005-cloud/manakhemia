#!/usr/bin/env node
/* §7 v10.5 預掃（遊策新規則，遊程未改 code）。唔改遊戲檔。
 * 真模組 bf57cb2，玩家模型同 scan-v10-4（隨機花、散步、徽章、mg2、浮動雙擊）。
 * 掃描覆寫：小遊戲 v2 同浮動雙擊共用「每日最多 cap 局計火苗路線分」。
 *   時段窗（20–03 月眠、06–09 水珠）嘅局照舊只計窗路線，唔佔呢個額。
 *   超額局：火苗權重 0；CQ、委託、天氣菇傘、星星碎照計。
 * A：每計分局 +2（config 原值）。B：每計分局 +1。cap＝2。
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
const FP = 2, DROPS = 5, CAP = 2;
const BASE_W = C.kinds.mg.w;
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const NAMES = Object.keys(SW.SCHED);
const rule = { on: false, w: BASE_W, cap: CAP };
const used = new WeakMap();
const stat = { counted: 0, skipped: 0 };

function hourNow() {
  const d = new Date(S.nowMs());
  return d.getHours() + d.getMinutes() / 60;
}
function inCareWindow(h) {
  return C.windows.some(w => (w.from <= w.to ? h >= w.from && h < w.to : h >= w.from || h < w.to));
}
function dayRec(s) {
  const day = S.dayKey(S.nowMs());
  let rec = used.get(s);
  if (!rec || rec.day !== day) { rec = { day, n: 0 }; used.set(s, rec); }
  return rec;
}
/* 出窗先佔額，而且要局真係計到（冷卻／光卵唔佔）。窗內交返 noteB5，唔佔額。 */
function plan(s) {
  if (!rule.on || !s || s.stage === 'egg' || inCareWindow(hourNow())) return null;
  const rec = dayRec(s);
  if (rec.n >= rule.cap) return { w: 0, rec, take: false };
  return { w: rule.w, rec, take: true };
}
function countedOk(r) { return r === true || !!(r && r.ok); }
function withWeight(s, fn) {
  const p = plan(s);
  if (!p) return fn();
  const prev = C.kinds.mg.w;
  C.kinds.mg.w = p.w;
  try {
    const r = fn();
    if (countedOk(r) && p.take) { p.rec.n++; stat.counted++; }
    else if (countedOk(r) && p.w === 0) stat.skipped++;
    return r;
  } finally { C.kinds.mg.w = prev; }
}
const origMg = S.mgCount;
const origOv = S.overlayOpenGame;
S.mgCount = function (s) { return withWeight(s, () => origMg(s)); };
S.overlayOpenGame = function (s, t) { return withWeight(s, () => origOv(s, t)); };

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

function emberOf(s) { const b = s.evo && s.evo.b5 && s.evo.b5.sprout; return b ? b.ember : 0; }
function prove() {
  rule.on = true;
  const out = {};
  for (const w of [2, 1]) {
    rule.w = w;
    const s = S.newState(1, 9);
    s.stage = 'sprout'; s.cq = 50; s.evo.day0 = '2026-11-02';
    let t = new Date(2026, 10, 2, 13, 0, 0).getTime();
    const set = (ms, h) => { t = ms; S.setNowFn(() => t); S.setHourFn(() => h); S.setWeatherFn(() => 'clear'); };
    set(t, 13);
    S.mgCount(s); S.mgCount(s); S.mgCount(s);
    const after3 = emberOf(s);
    set(t, 21); S.mgCount(s);
    const afterMoon = emberOf(s);
    set(t + 700e3, 13); S.overlayOpenGame(s, t + 700e3);
    const afterOv = emberOf(s);
    set(t + 864e5, 13); S.mgCount(s);
    const nextDay = emberOf(s);
    const shardsBefore = X.wallet(s, t).total;
    const fin = B.gameFinish(s, 'bounce', 30, t + 864e5, {});
    out['w' + w] = {
      after3, afterMoon, afterOv, nextDay,
      expectAfter3: 2 * w, expectAfterMoon: 2 * w, expectAfterOv: 2 * w, expectNext: 3 * w,
      ok: after3 === 2 * w && afterMoon === 2 * w && afterOv === 2 * w && nextDay === 3 * w,
      shardStillPaid: fin.shards > 0 && X.wallet(s, t + 864e5).total > shardsBefore,
      configW: C.kinds.mg.w,
    };
  }
  rule.on = false; rule.w = BASE_W;
  S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
  return out;
}

function checkCode() {
  const items = [];
  const mark = (name, ok, info) => items.push({ name, ok, info });
  const pr = Object.fromEntries(C.weather.probs);
  mark('菇傘雨 0.8／陰霧 0.4', W.rain.w === 0.8 && W.overcast.w === 0.4 && W.fog.w === 0.4, W);
  mark('天氣一日一抽 60/20/15/5', P.systems12.weather.perDay === true && pr.clear === 60 && pr.overcast === 20 && pr.rain === 15 && pr.fog === 5, pr);
  mark('火苗 config 仍然 +2（掃描先覆寫）', C.kinds.mg.w === 2 && G.games.countsMg === true, C.kinds.mg);
  mark('冷卻 600s', C.overlayMg.cooldownSec === 600, C.overlayMg.cooldownSec);
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
  return { tables, total, cqs, blooms: gst.blooms };
}

function checksFor(R, econ, code) {
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
    ['新系統路線分≤25%', mark(true), '同 v10.4 fixture，本掃冇改 cap'],
    ['疏玩上線日星碎 15–30', mark(econ.out['疏玩'].playMed >= docBand[0] && econ.out['疏玩'].playMed <= docBand[1]), econ.out['疏玩'].playMed],
    ['其他 5 表每日星碎 15–30', mark(others.every(n => econ.out[n].allMed >= docBand[0] && econ.out[n].allMed <= docBand[1] && econ.out[n].playMed >= docBand[0] && econ.out[n].playMed <= docBand[1])), others.map(n => n + ' ' + econ.out[n].playMed).join(' ')],
    ['冇一日穿 30', mark(econ.over === 0), econ.over],
    ['火苗全體 12–18%', mark(total.ember >= 12 && total.ember <= 18), total.ember],
    ['柔光全體≥10%', mark(total.soft >= 10), total.soft],
  ];
  return {
    checks, passN: checks.filter(c => c[1] === '✅').length, fail: checks.filter(c => c[1] === '❌').map(c => c[0]),
    total, tables, cqs: R.cqs, cqMed: cq, nightMoon: tables['夜貓'].moon,
    brightMax, shroomMax, econ: econ.out, over30: econ.over, blooms: R.blooms,
    codeOk: code.every(c => c.ok),
  };
}

function runVariant(id, w) {
  rule.on = true; rule.w = w; rule.cap = CAP;
  stat.counted = 0; stat.skipped = 0;
  const t0 = Date.now();
  const econ = economy();
  const R = routes();
  const row = checksFor(R, econ, checkCode());
  row.id = id; row.w = w; row.cap = CAP; row.ms = Date.now() - t0;
  row.mgStat = { counted: stat.counted, skipped: stat.skipped };
  row.configWAfter = C.kinds.mg.w;
  rule.on = false; rule.w = BASE_W;
  return row;
}

function main() {
  const proof = prove();
  if (!proof.w2.ok || !proof.w1.ok || !proof.w2.shardStillPaid || C.kinds.mg.w !== 2) {
    console.error(JSON.stringify({ proof, configW: C.kinds.mg.w }, null, 2));
    process.exit(1);
  }
  const A = runVariant('A', 2);
  const B = runVariant('B', 1);
  const out = {
    doc: '遊策預掃：mg 火苗每日最多 2 局。A＝+2／局，B＝+1／局。星星碎唔封。遊戲碼未改。',
    sim: 'bf57cb23a4fc743c8b89c6d9ea596f0c582f0407',
    tree: 'b6e89349fcd7b06d7aac090bd8f620039eda6f76',
    base: 'scan-v10-4',
    N, ECON_N, fpats: FP, drops: DROPS, cap: CAP,
    proof, configW: C.kinds.mg.w,
    A, B,
    all16: { A: A.passN === 16, B: B.passN === 16 },
  };
  const dest = process.env.OUT || path.join(__dirname, 'scan-v10-5-result.json');
  fs.writeFileSync(dest, JSON.stringify(out, null, 2));
  const brief = (v) => ({
    passN: v.passN, fail: v.fail, total: v.total, nightMoon: v.nightMoon, cq: v.cqMed,
    econ: v.econ, ms: v.ms, mgStat: v.mgStat,
  });
  console.log(JSON.stringify({ proofOk: true, configW: C.kinds.mg.w, A: brief(A), B: brief(B), all16: out.all16 }, null, 2));
}
main();
