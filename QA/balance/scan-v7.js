#!/usr/bin/env node
/* §7 平衡掃描 v7。外掛，唔改 code/glimmer-evo6。
 * 真 sim：a7f0d878（route-sweep.js 同一套時間表、隨機、CQ、scaleToAge）。
 * 外掛只改：晶角分＝有便便嘅上線入面即清比例 ×100×k（取消清潔 ≥60）；
 * 螢絨機會按 20/25 縮（CQ 仍然 25）；柔光門檻 28。差距 5pt、專線、scaleToAge 跟真 code。只掃 k。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('/tmp/glimmer-a7/src/glimmer-a/src/sim.js');
const D = require('/tmp/glimmer-a7/src/glimmer-a/src/data.js');
const P = D.PARAMS;
const C = P.evo6.branch;
const N = +(process.env.N || 1000);
const JIT = 90, MISS = 0.15, LULL = 0.5, SKIP_ACT = 0.2, EXTRA_ACT = 0.3;
const WX = [['clear', 0.6], ['overcast', 0.25], ['rain', 0.15]];
const ACTS = ['feed', 'play', 'rinse', 'poop'];
const SCHED = {
  勤力: { hours: [8, 11, 14, 17, 20], acts: ['feed', 'play', 'rinse', 'poop'] },
  普通: { hours: [8, 13, 19], acts: ['feed', 'play', 'poop'] },
  疏玩: { hours: [20], acts: ['feed', 'play'], everyOtherDay: true },
  夜貓: { hours: [18, 22, 0, 1], acts: ['feed', 'play'] },
  早起: { hours: [6, 7, 8, 12], acts: ['feed', 'rinse', 'play'] },
  餵食狂: { hours: [9, 12, 15, 18], acts: ['feed', 'feed', 'feed', 'play'] },
};
const NAMES = Object.keys(SCHED);
const IDS = ['tide', 'shroom', 'crystal', 'moon', 'ember'];
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const KS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60];

function run(name, seed) {
  const sc = SCHED[name];
  const rng = S.makeRng(seed * 7919 + 13);
  const T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
  let now = T0 + 8 * 3600e3, wx = 'clear';
  S.setHourFn(() => new Date(now).getHours() + new Date(now).getMinutes() / 60);
  S.setNowFn(() => now);
  S.setWeatherFn(() => wx);
  const s = S.newState(now, seed);
  s.stage = 'sprout'; s.growthSec = 0; s.cq = P.cqStart;
  s.needs = Object.assign({}, P.startNeedsSprout || s.needs);
  s.evo.day0 = S.dayKey(now);
  const sess = [];
  for (let d = 0; d < 9; d++) {
    if (sc.everyOtherDay && (d + (seed & 1)) % 2) continue;
    for (const h of sc.hours) {
      if (rng() < MISS) continue;
      sess.push(T0 + d * 864e5 + (h * 60 + Math.round((rng() * 2 - 1) * JIT)) * 60e3);
    }
  }
  sess.sort((a, b) => a - b);
  let k = 0, nVis = 0, nWith = 0, nQuick = 0, snap = null;
  function grab() {
    if (snap || s.stage !== 'adult') return;
    const ev = (s.ev || []).find(e => e.type === 'evolve');
    const days = S.careDaysCheck(s);
    const T = { tide: 0, shroom: 0, moon: 0, ember: 0, crystalRaw: 0, all: 0 };
    for (const st of P.evo6.careStages) {
      const b = s.evo && s.evo.b5 && s.evo.b5[st];
      if (!b) continue;
      T.all += +b.all || 0; T.tide += +b.tide || 0; T.shroom += +b.shroom || 0; T.moon += +b.moon || 0; T.ember += +b.ember || 0; T.crystalRaw += +b.crystal || 0;
    }
    snap = {
      lumiEv: ev && ev.lumi ? { ok: !!ev.lumi.ok, chance: ev.lumi.chance || 0, roll: ev.lumi.roll || 0, cqOk: !!ev.lumi.cqOk, fireflyOk: !!ev.lumi.fireflyOk } : null,
      cq: ev ? ev.cq : s.cq,
      daysOk: days.ok, days: days.days, span: days.span, need: days.need,
      roll: S.branchRoll(s, 'b5draw'),
      T, nWith, nQuick,
      simForm: s.form,
    };
  }
  while (s.stage === 'sprout' || s.stage === 'juvenile') {
    if (now - T0 > 10 * 864e5) break;
    if (Math.floor((now - T0) / 216e5) !== Math.floor((now - T0 - 1800e3) / 216e5)) {
      let r = rng(), w = 'clear';
      for (const [n, p] of WX) { if (r < p) { w = n; break; } r -= p; }
      wx = w;
    }
    while (k < sess.length && sess[k] < now) k++;
    if (k < sess.length && sess[k] < now + 1800e3) {
      k++; s.lastSeen = now;
      if (s.sleeping) S.toggleSleep(s);
      const had = s.poops > 0;
      const acts = sc.acts.filter(() => rng() >= SKIP_ACT);
      if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
      let didPoop = false;
      for (const a of acts) {
        if (a === 'feed') { s.needs.hunger = Math.min(s.needs.hunger, 60); S.feed(s, 'meal'); }
        else if (a === 'play') S.play(s);
        else if (a === 'rinse') S.rinse(s);
        else { if (s.poops > 0) didPoop = true; while (s.poops > 0) S.clearPoop(s); }
      }
      if (S.isDrowsy(s) && rng() < LULL) S.lullSleep(s);
      const hr = new Date(now).getHours();
      if ((hr >= 17 || hr < 7) && rng() < 0.25) S.noteEvent(s, P.evo6.lumiEvent);
      nVis++; if (had) nWith++; if (had && didPoop) nQuick++;
      S.advance(s, 1800, {}, 60); now += 1800e3; s.lastSeen = now;
      grab();
    } else {
      const t0 = now; now += 1800e3; s.lastSeen = t0;
      S.applyOffline(s, now); s.growthSec += 1800;
      if (S.checkStage) S.checkStage(s);
      grab();
    }
  }
  S.setHourFn(null); S.setNowFn(null); S.setWeatherFn(null);
  if (!snap) snap = { lumiEv: null, cq: s.cq, daysOk: false, days: 0, span: 0, need: 0, roll: 0, T: { tide: 0, shroom: 0, moon: 0, ember: 0, crystalRaw: 0, all: 0 }, nWith, nQuick, simForm: s.form || 'none' };
  return snap;
}
function lumiOk(f) {
  const L = f.lumiEv; if (!L || !L.fireflyOk || !L.cqOk) return false;
  const chance = (L.chance || 0) * (20 / C.lumi.maxChancePct);
  return L.roll < chance;
}
function judge(f, k) {
  if (lumiOk(f)) return 'lumi';
  if (!f.T || f.simForm === 'none') return f.simForm || 'none';
  const all = f.T.all;
  const rate = f.nWith ? f.nQuick / f.nWith : 0;
  const score = { tide: f.T.tide, shroom: f.T.shroom, crystal: rate * k * all, moon: f.T.moon, ember: f.T.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  const top = rank[0], second = rank[1];
  const sharePct = all ? top.n / all * 100 : 0;
  const gap = all ? (top.n - second.n) / all * 100 : 100;
  if (f.cq >= C.brightCQ && f.daysOk && sharePct < C.brightMaxTopPct) return 'bright';
  if (f.cq >= C.b5CQ && all > 0 && sharePct >= C.b5TopPct) {
    if (gap < C.drawGapPt && top.n + second.n > 0) {
      const pTop = top.n / (top.n + second.n);
      return f.roll < pTop ? top.id : second.id;
    }
    return top.id;
  }
  return f.cq >= 28 ? 'soft' : 'dust';
}
function evaluate(rows, k) {
  const tables = {};
  const total = {};
  for (const id of PATHS) total[id] = 0;
  const cqMed = {};
  let nAll = 0;
  for (const name of NAMES) {
    const list = rows[name];
    const acc = {};
    const cqs = list.map(f => f.cq).sort((a, b) => a - b);
    cqMed[name] = +cqs[cqs.length >> 1].toFixed(2);
    for (const f of list) {
      const form = judge(f, k);
      acc[form] = (acc[form] || 0) + 1;
      total[form] = (total[form] || 0) + 1;
    }
    const pc = {};
    for (const id of PATHS) pc[id] = +(((acc[id] || 0) / list.length) * 100).toFixed(2);
    tables[name] = pc;
    nAll += list.length;
  }
  const totalPct = {};
  for (const id of PATHS) totalPct[id] = +(((total[id] || 0) / nAll) * 100).toFixed(2);
  const brightMax = Math.max(...NAMES.map(n => tables[n].bright));
  const mark = (ok) => ok ? '✅' : '❌';
  const shroomOk = NAMES.every(n => tables[n].shroom <= 30 + 1e-9);
  const nine = PATHS.every(id => totalPct[id] >= 2 - 1e-9);
  const kindsOk = NAMES.every(n => PATHS.filter(id => tables[n][id] >= 2 - 1e-9).length >= 2);
  const capOk = NAMES.every(n => PATHS.every(id => tables[n][id] <= 85 + 1e-9));
  const softC = tables['疏玩'].soft, dustC = tables['疏玩'].dust;
  const checks = [
    ['晶角全體≥5%', mark(totalPct.crystal >= 5 - 1e-9), totalPct.crystal],
    ['燦光任何一表≤50%', mark(brightMax <= 50 + 1e-9), brightMax],
    ['月眠全體≥5%', mark(totalPct.moon >= 5 - 1e-9), totalPct.moon],
    ['螢絨 3–10%', mark(totalPct.lumi >= 3 - 1e-9 && totalPct.lumi <= 10 + 1e-9), totalPct.lumi],
    ['每表菇傘≤30%', mark(shroomOk), Math.max(...NAMES.map(n => tables[n].shroom))],
    ['9 條路出齊', mark(nine), null],
    ['每表≥2 結局', mark(kindsOk), null],
    ['單一≤85%', mark(capOk), null],
    ['疏玩柔光＋微塵', mark(softC >= 2 - 1e-9 && dustC >= 2 - 1e-9), softC + '/' + dustC],
    ['隔日微塵＋火苗', mark(tables['疏玩'].dust >= 2 - 1e-9 && tables['疏玩'].ember >= 2 - 1e-9), tables['疏玩'].dust + '/' + tables['疏玩'].ember],
    ['疏玩 CQ 15–35', mark(cqMed['疏玩'] >= 15 && cqMed['疏玩'] <= 35), cqMed['疏玩']],
  ];
  return { tables, totalPct, cqMed, brightMax, checks, passN: checks.filter(c => c[1] === '✅').length, fail: checks.filter(c => c[1] === '❌').map(c => c[0]) };
}
function main() {
  const t0 = Date.now();
  const rows = {};
  const quick = {};
  for (const name of NAMES) {
    rows[name] = [];
    let vis = 0, withP = 0, q = 0;
    for (let i = 1; i <= N; i++) {
      const f = run(name, i);
      rows[name].push(f);
      withP += f.nWith; q += f.nQuick; vis += 1;
    }
    quick[name] = { withPoopPerRun: +(withP / N).toFixed(2), quickPct: withP ? +((q / withP) * 100).toFixed(1) : 0 };
    void vis;
  }
  const sweep = KS.map(k => {
    const sc = evaluate(rows, k);
    return { k, crystal: sc.totalPct.crystal, brightMax: sc.brightMax, passN: sc.passN, nChecks: sc.checks.length, fail: sc.fail, sc };
  });
  const passed = sweep.filter(r => r.fail.length === 0);
  const pick = passed.length ? passed.slice().sort((a, b) => Math.abs(a.k - 0.45) - Math.abs(b.k - 0.45))[0] : null;
  const start = sweep.find(r => r.k === 0.45);
  const simDist = {};
  const legacyDist = {};
  function legacy(f) {
    if (f.lumiEv && f.lumiEv.ok) return 'lumi';
    const all = f.T.all || 0;
    const score = { tide: f.T.tide, shroom: f.T.shroom, crystal: f.T.crystalRaw, moon: f.T.moon, ember: f.T.ember };
    const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
    const top = rank[0], second = rank[1];
    const share = all ? top.n / all : 0;
    const gap = all ? (top.n - second.n) / all * 100 : 100;
    if (f.cq >= 30 && f.days >= 5 && share < 0.45) return 'bright';
    if (all > 0 && share >= 0.45) {
      if (gap < 5 && top.n + second.n > 0) return f.roll < top.n / (top.n + second.n) ? top.id : second.id;
      return top.id;
    }
    return f.cq >= 28 ? 'soft' : 'dust';
  }
  const diffs = [];
  for (const name of NAMES) {
    const c = {}, L = {};
    for (const f of rows[name]) {
      c[f.simForm] = (c[f.simForm] || 0) + 1;
      const g = legacy(f); L[g] = (L[g] || 0) + 1;
    }
    simDist[name] = c; legacyDist[name] = L;
    const n = rows[name].length;
    for (const id of PATHS) {
      const a = ((c[id] || 0) / n) * 100, b = ((L[id] || 0) / n) * 100;
      if (Math.abs(a - b) > 3) diffs.push({ name, id, real: +a.toFixed(1), qaV5rules: +b.toFixed(1), d: +(a - b).toFixed(1) });
    }
  }
  const out = {
    doc: '附件 §7 平衡修訂 v7。真 sim a7f0d878 route-sweep。',
    sim: 'a7f0d87878db15e09da426bed04d60f668bcbcac',
    N, quick, simDist, legacyDist, diffs,
    codeParams: { brightCQ: C.brightCQ, softCQ: C.softCQ, b5CQ: C.b5CQ, b5TopPct: C.b5TopPct, drawGapPt: C.drawGapPt, lumiMax: C.lumi.maxChancePct, lumiCQ: C.lumi.minCQ, scaleToAge: C.brightDays.scaleToAge },
    sweep: sweep.map(r => ({ k: r.k, crystal: r.crystal, brightMax: r.brightMax, passN: r.passN, nChecks: r.nChecks, fail: r.fail })),
    solved: !!pick,
    start: { k: 0.45, checks: start.sc.checks, totalPct: start.sc.totalPct, tables: start.sc.tables, cqMed: start.sc.cqMed, brightMax: start.brightMax },
    recommended: pick && { k: pick.k, checks: pick.sc.checks, totalPct: pick.sc.totalPct, tables: pick.sc.tables, cqMed: pick.sc.cqMed, brightMax: pick.brightMax },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v7-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    N, ms: out.ms, solved: out.solved, k: pick && pick.k, quick,
    sweep: out.sweep.map(r => ({ k: r.k, crystal: r.crystal, brightMax: r.brightMax, passN: r.passN })),
    startLumi: start.sc.totalPct.lumi, startBright: start.brightMax, cq: start.sc.cqMed['疏玩'], diffs: diffs.length,
  }));
}
main();
