#!/usr/bin/env node
/* §7 平衡掃描 v10。外掛，唔改 code/glimmer-evo6。同 v9，完整重跑照顧。
 * 底：a7f0d878 decideBranch 次序（螢絨 → 燦光 → 新 5 條，差 <5pt 抽頭兩名 → 柔光 → 微塵）
 *     同 route-sweep 時間表、主 rng（seed*7919+13）、±90、漏 15%、動作跳 20%、加動作 30%、哄瞓 50%、每 6 小時天氣。
 * 外掛（文件蓋過 code）：
 *   螢絨上限 20%（跑之前改 sim 讀嘅 maxChancePct，唔改檔）
 *   柔光 CQ ≥18，低過 18 微塵
 *   新 5 條 CQ ≥ max(ceil(25 × span / 7), 18.5)。span 同 careDaysCheck 一樣由出世日計
 *   晴天餵食唔計菇傘；陰天餵食由 +1 改成 0.5；雨天餵食維持 1.0。其他照顧嘅陰 0.5／雨 1.0 照真 code
 *   哄瞓計到分嗰次，月眠再 +1（一共 +2），每晚最多 3 次照真 code
 *   晶角＝（即清上線 ÷ 有便便上線）×100×k×all，取消清潔 ≥60。主結果 k＝0.45，另出 0.40／0.50
 * 小遊戲假設（第 2 批未出，浮動團絨撳兩下＝一局）見 MG_AT。用獨立 rng，唔打亂主隨機。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('/tmp/glimmer-a7/src/glimmer-a/src/sim.js');
const D = require('/tmp/glimmer-a7/src/glimmer-a/src/data.js');
const P = D.PARAMS;
const C = P.evo6.branch;
C.lumi.maxChancePct = 20;
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
/* 表定鐘點先排一局。實際計分用上線嗰刻嘅鐘：晨露 6–9 只計水珠、月眠 20–3 只計月眠。
 * 勤力放 11、17（避開 8 點晨露同 20 點月眠）；夜貓只放 18（22／0／1 會被月眠窗食掉）；
 * 早起放 12；餵食狂放 15（一日一局，上線主要係食）；普通放 13；疏玩只有 20 點。
 * 到咗場再用獨立 rng 跳過 20%，同動作跳過一樣。一局當及格 40 分。時段外火苗再 +1，合計 +2。 */
const MG_AT = {
  勤力: [11, 17],
  普通: [13],
  疏玩: [20],
  夜貓: [18],
  早起: [12],
  餵食狂: [15],
};
const NAMES = Object.keys(SCHED);
const IDS = ['tide', 'shroom', 'crystal', 'moon', 'ember'];
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const KS = [0.40, 0.45, 0.50];
const B5_FULL = 25;

function hourOf(now) { return new Date(now).getHours() + new Date(now).getMinutes() / 60; }
function bump(s, key, d) {
  const b = s.evo && s.evo.b5 && s.evo.b5[s.stage];
  if (!b) return;
  b[key] = +((+b[key] || 0) + d).toFixed(4);
}
function patchFeed(s, now, wx) {
  if (S.careWindow(hourOf(now))) return;
  if (wx === 'clear') bump(s, 'shroom', -1);
  else if (wx === 'overcast') bump(s, 'shroom', -0.5);
}
function playMg(s, now) {
  S.mgApply(s, P.mg.passScore, now);
  if (!S.careWindow(hourOf(now))) bump(s, 'ember', 1);
}

function run(name, seed) {
  const sc = SCHED[name];
  const rng = S.makeRng(seed * 7919 + 13);
  const rngMg = S.makeRng(seed * 7919 + 97);
  const T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
  let now = T0 + 8 * 3600e3, wx = 'clear';
  S.setHourFn(() => hourOf(now));
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
      sess.push({ t: T0 + d * 864e5 + (h * 60 + Math.round((rng() * 2 - 1) * JIT)) * 60e3, h });
    }
  }
  sess.sort((a, b) => a.t - b.t);
  let k = 0, nVis = 0, nWith = 0, nQuick = 0, plays = 0, mgs = 0, lulls = 0, snap = null;
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
      lumiEv: ev && ev.lumi ? { ok: !!ev.lumi.ok, chance: ev.lumi.chance || 0, roll: ev.lumi.roll || 0 } : null,
      cq: ev ? ev.cq : s.cq,
      daysOk: days.ok, span: days.span,
      roll: S.branchRoll(s, 'b5draw'),
      T, nWith, nQuick, plays, mgs, lulls,
      shroomMin: T.shroom,
    };
  }
  while (s.stage === 'sprout' || s.stage === 'juvenile') {
    if (now - T0 > 10 * 864e5) break;
    if (Math.floor((now - T0) / 216e5) !== Math.floor((now - T0 - 1800e3) / 216e5)) {
      let r = rng(), w = 'clear';
      for (const [n, p] of WX) { if (r < p) { w = n; break; } r -= p; }
      wx = w;
    }
    while (k < sess.length && sess[k].t < now) k++;
    if (k < sess.length && sess[k].t < now + 1800e3) {
      const slot = sess[k++];
      s.lastSeen = now;
      if (s.sleeping) S.toggleSleep(s);
      const had = s.poops > 0;
      const acts = sc.acts.filter(() => rng() >= SKIP_ACT);
      if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
      let didPoop = false;
      for (const a of acts) {
        if (a === 'feed') {
          s.needs.hunger = Math.min(s.needs.hunger, 60);
          const r = S.feed(s, 'meal');
          if (r && r.ok) patchFeed(s, now, wx);
        } else if (a === 'play') {
          const r = S.play(s);
          if (r && r.ok) plays++;
        } else if (a === 'rinse') S.rinse(s);
        else { if (s.poops > 0) didPoop = true; while (s.poops > 0) S.clearPoop(s); }
      }
      if (MG_AT[name].includes(slot.h) && rngMg() >= SKIP_ACT) { playMg(s, now); mgs++; }
      const lull = S.isDrowsy(s) && rng() < LULL ? S.lullSleep(s) : null;
      if (lull && lull.counted) { bump(s, 'moon', 1); lulls++; }
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
  if (!snap) snap = { lumiEv: null, cq: s.cq, daysOk: false, span: 0, roll: 0, T: { tide: 0, shroom: 0, moon: 0, ember: 0, crystalRaw: 0, all: 0 }, nWith, nQuick, plays, mgs, lulls, shroomMin: 0 };
  return snap;
}
const B5_FLOOR = 18.5;
function needCQ(span) { return Math.max(Math.ceil(B5_FULL * (span || 0) / C.brightDays.window), B5_FLOOR); }
function judge(f, k) {
  if (f.lumiEv && f.lumiEv.ok) return 'lumi';
  const all = f.T.all;
  const rate = f.nWith ? f.nQuick / f.nWith : 0;
  const score = { tide: f.T.tide, shroom: Math.max(0, f.T.shroom), crystal: rate * k * all, moon: f.T.moon, ember: f.T.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  const top = rank[0], second = rank[1];
  const brightBlocked = all > 0 && top.n * 100 >= C.brightMaxTopPct * all;
  if (f.cq >= C.brightCQ && f.daysOk && !brightBlocked) return 'bright';
  const topOk = all > 0 && top.n * 100 >= C.b5TopPct * all;
  if (f.cq >= needCQ(f.span) && topOk) {
    const gapOk = (top.n - second.n) * 100 >= C.drawGapPt * all;
    if (!gapOk && top.n + second.n > 0) return f.roll < top.n / (top.n + second.n) ? top.id : second.id;
    return top.id;
  }
  return f.cq >= 18 ? 'soft' : 'dust';
}
function pctile(sorted, p) { return +sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))].toFixed(2); }
function evaluate(rows, k) {
  const tables = {};
  const total = {};
  for (const id of PATHS) total[id] = 0;
  const cqMed = {}, extra = {};
  let nAll = 0;
  for (const name of NAMES) {
    const list = rows[name];
    const acc = {};
    const cqs = list.map(f => f.cq).sort((a, b) => a - b);
    const spans = list.map(f => f.span).sort((a, b) => a - b);
    cqMed[name] = +cqs[cqs.length >> 1].toFixed(2);
    extra[name] = {
      cqP10: pctile(cqs, 0.1), cqP90: pctile(cqs, 0.9), cqMin: +cqs[0].toFixed(2),
      spanMed: spans[spans.length >> 1], needMed: needCQ(spans[spans.length >> 1]),
      plays: +(list.reduce((a, f) => a + f.plays, 0) / list.length).toFixed(2),
      mgs: +(list.reduce((a, f) => a + f.mgs, 0) / list.length).toFixed(2),
      lulls: +(list.reduce((a, f) => a + f.lulls, 0) / list.length).toFixed(2),
    };
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
  const shroomMax = Math.max(...NAMES.map(n => tables[n].shroom));
  const nine = PATHS.every(id => totalPct[id] >= 2 - 1e-9);
  const kindsOk = NAMES.every(n => PATHS.filter(id => tables[n][id] >= 2 - 1e-9).length >= 2);
  const capOk = NAMES.every(n => PATHS.every(id => tables[n][id] <= 85 + 1e-9));
  const softC = tables['疏玩'].soft, dustC = tables['疏玩'].dust;
  const checks = [
    ['9 條路出齊（每條≥2%）', mark(nine), PATHS.filter(id => totalPct[id] < 2 - 1e-9).map(id => id + ' ' + totalPct[id]).join(', ') || '齊'],
    ['每表≥2 結局（每個≥2%）', mark(kindsOk), null],
    ['單一≤85%', mark(capOk), null],
    ['螢絨 3–10%', mark(totalPct.lumi >= 3 - 1e-9 && totalPct.lumi <= 10 + 1e-9), totalPct.lumi],
    ['每表菇傘≤30%', mark(shroomMax <= 30 + 1e-9), shroomMax],
    ['晶角全體≥5%', mark(totalPct.crystal >= 5 - 1e-9), totalPct.crystal],
    ['月眠全體≥5%', mark(totalPct.moon >= 5 - 1e-9), totalPct.moon],
    ['每表燦光≤50%', mark(brightMax <= 50 + 1e-9), brightMax],
    ['疏玩柔光＋微塵', mark(softC >= 2 - 1e-9 && dustC >= 2 - 1e-9), softC + '/' + dustC],
    ['疏玩 CQ 15–35', mark(cqMed['疏玩'] >= 15 && cqMed['疏玩'] <= 35), cqMed['疏玩']],
  ];
  return { tables, totalPct, cqMed, extra, brightMax, checks, passN: checks.filter(c => c[1] === '✅').length, fail: checks.filter(c => c[1] === '❌').map(c => c[0]) };
}
function main() {
  const t0 = Date.now();
  const rows = {};
  const quick = {};
  let shroomNeg = 0;
  for (const name of NAMES) {
    rows[name] = [];
    let withP = 0, q = 0;
    for (let i = 1; i <= N; i++) {
      const f = run(name, i);
      rows[name].push(f);
      withP += f.nWith; q += f.nQuick;
      if (f.shroomMin < -1e-6) shroomNeg++;
    }
    quick[name] = { withPoopPerRun: +(withP / N).toFixed(2), quickPct: withP ? +((q / withP) * 100).toFixed(1) : 0 };
  }
  const sweep = KS.map(k => {
    const sc = evaluate(rows, k);
    return { k, sc };
  });
  const start = sweep.find(r => r.k === 0.45);
  const out = {
    doc: '§7 v10。同 v9 完整重跑。柔光 ≥18。專線 CQ ≥ max(ceil(25*span/7), 18.5)。',
    sim: 'a7f0d87878db15e09da426bed04d60f668bcbcac',
    N,
    assumptions: {
      lumiMax: 20, softCQ: 18, b5CQ: 'max(ceil(25*span/7), 18.5)', b5Floor: B5_FLOOR, lullMoon: 2, lullPerNight: 3,
      crystal: '(nQuick/nWith)*k*all', cleanGate: false, k: 0.45, alsoK: [0.40, 0.50], gapPt: 5,
      shroom: '晴天餵食 0；陰天餵食 0.5；雨天餵食 1.0；其他照顧陰 0.5／雨 1.0',
      mg: MG_AT,
      mgRule: '表定鐘點到場後，獨立 rng 20% 唔開。一局及格 40 分。時段外火苗 +2（all 只 +1），時段內跟真 code 只計水珠或月眠。',
      rng: '主 seed*7919+13 同 route-sweep；小遊戲 seed*7919+97',
    },
    quick, shroomNeg,
    sweep: sweep.map(r => ({ k: r.k, crystal: r.sc.totalPct.crystal, moon: r.sc.totalPct.moon, lumi: r.sc.totalPct.lumi, brightMax: r.sc.brightMax, passN: r.sc.passN, nChecks: r.sc.checks.length, fail: r.sc.fail })),
    start: { k: 0.45, checks: start.sc.checks, totalPct: start.sc.totalPct, tables: start.sc.tables, cqMed: start.sc.cqMed, extra: start.sc.extra, brightMax: start.sc.brightMax },
    ref: sweep.filter(r => r.k !== 0.45).map(r => ({ k: r.k, totalPct: r.sc.totalPct, tables: r.sc.tables, cqMed: r.sc.cqMed, checks: r.sc.checks })),
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v10-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    N, ms: out.ms, shroomNeg, passN: start.sc.passN, fail: start.sc.fail,
    total: start.sc.totalPct, cq: start.sc.cqMed, extra: start.sc.extra, quick,
    sweep: out.sweep,
  }));
}
main();
