#!/usr/bin/env node
/* §7 平衡掃描。外掛參數，唔改 code/glimmer-evo6。
 * 模擬邏輯：code/glimmer-evo6 @ 25e8c40（require 嗰份 sim／data）。
 * 文件：已 fetch 全部分支，pet-template-v1.md 最新係 origin/code/glimmer-evo6 @ 25e8c40，
 * 冇「§7 平衡修訂 v2」段。v2 起始值跟今次遊策訊息：最高分 <45% 唔入新 5 條（CQ≥70 去燦光）。
 * 鎖中午＝唔用跑機真實時間；照顧用時間表鐘點（22:00 仍然算月眠／夜晚）。 */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('/tmp/glimmer-evo6/src/glimmer-a/src/sim.js');
const D = require('/tmp/glimmer-evo6/src/glimmer-a/src/data.js');
const P = D.PARAMS;
const H = 3600;
const SCH = {
  diligent: [7, 10, 13, 16, 19, 22],
  normal: [8, 12, 18, 22],
  office: [8, 13, 21],
  light: [9, 21],
  early: [6, 7],
  eod: [12],
};
const NAMES = Object.keys(SCH);
const IDS = ['tide', 'shroom', 'crystal', 'moon', 'ember'];
const OUTS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust', 'none'];
function rngOf(seed) {
  let a = seed >>> 0 || 1;
  return () => { a = (a * 1664525 + 1013904223) >>> 0; return a / 4294967296; };
}
function visit(s, hour, rain) {
  S.setHourFn(() => hour);
  S.setRainFn(() => !!rain);
  if (s.needs.hunger < 75) S.feed(s, 'meal');
  if (s.needs.mood < 70) S.play(s);
  if (s.needs.clean < 75) S.rinse(s);
  if (s.poops) S.clearPoop(s);
  if (s.needs.energy < 25 && !s.sleeping) S.toggleSleep(s);
}
function simulate(name, seed) {
  const rng = rngOf(seed * 1009 + NAMES.indexOf(name) * 17 + 3);
  const s = S.newState(Date.UTC(2026, 0, 1), seed);
  const opens = SCH[name];
  let absH = 0, dayMark = -1, rain = false;
  const maxH = 400 * 24;
  while (absH < maxH && s.stage !== 'adult' && s.stage !== 'elder') {
    const day = Math.floor(absH / 24);
    if (day !== dayMark) {
      dayMark = day; rain = rng() < 0.2;
      if ((s.stage === 'sprout' || s.stage === 'juvenile') && rng() < 0.34) S.noteEvent(s, 'firefly_walk');
    }
    let next = null;
    for (let d = day; d < day + 4 && next == null; d++) {
      if (name === 'eod' && d % 2 === 1) continue;
      for (const h of opens) { const t = d * 24 + h; if (t > absH + 1e-6) { next = t; break; } }
    }
    if (next == null) break;
    let left = Math.min(next - absH, maxH - absH);
    while (left > 1e-9) {
      const hourNow = ((absH % 24) + 24) % 24;
      const toBoundary = Math.min(left, Math.max(0.05, 24 - hourNow));
      const d2 = Math.floor((absH + toBoundary) / 24);
      if (d2 !== dayMark) {
        dayMark = d2; rain = rng() < 0.2;
        if ((s.stage === 'sprout' || s.stage === 'juvenile') && rng() < 0.34) S.noteEvent(s, 'firefly_walk');
      }
      S.setHourFn(() => hourNow);
      S.advance(s, toBoundary * H, {}, 3600);
      absH += toBoundary; left -= toBoundary;
      if (s.stage === 'adult' || s.stage === 'elder') { left = 0; break; }
    }
    if (s.stage === 'adult' || s.stage === 'elder') break;
    visit(s, absH % 24, rain);
  }
  const E = s.evo || {};
  const T = { all: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 };
  let cs = 0, cn = 0, night = 0, careAll = 0;
  for (const st of ['sprout', 'juvenile']) {
    const b = E.b5 && E.b5[st]; if (b) for (const k in T) T[k] += +b[k] || 0;
    const c = E.cl && E.cl[st]; if (c) { cs += c.sum; cn += c.sec; }
    const care = E.care && E.care[st]; if (care) { careAll += care.all; night += care.night; }
  }
  let firefly = 0;
  for (const st of ['sprout', 'juvenile']) firefly += (E.evIn && E.evIn[st] && E.evIn[st].firefly_walk) || 0;
  const ev = (s.ev || []).find(e => e.type === 'evolve');
  return {
    adult: s.stage === 'adult' || s.stage === 'elder',
    cq: ev ? ev.cq : s.cq,
    firefly, nightShare: careAll ? night / careAll : 0, nightAll: careAll,
    all: T.all, tide: T.tide, shroom: T.shroom, crystal: T.crystal, moon: T.moon, ember: T.ember,
    cleanAvg: cn > 0 ? cs / cn : null,
  };
}
function judge(f, p) {
  if (!f.adult) return 'none';
  if (f.firefly > 0 && f.cq >= p.lumiCQ && f.nightAll > 0 && f.nightShare >= p.lumiNight) return 'lumi';
  const crystal = f.cleanAvg != null && f.cleanAvg >= p.clean ? f.crystal : 0;
  const score = { tide: f.tide, shroom: f.shroom, crystal, moon: f.moon, ember: f.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  const N = f.all, top = rank[0], second = rank[1];
  const share = N ? top.n / N : 0;
  const gap = N ? (top.n - second.n) / N : 0;
  const b5 = f.cq >= p.b5CQ && N > 0 && share >= p.top && gap >= p.gap && top.n !== second.n;
  /* v2：最高分低過 top（起始 45%）唔入新 5 條；CQ 夠就去燦光。高過先至新 5 條贏過燦光。 */
  if (share < p.top || !b5) {
    if (f.cq >= p.bright) return 'bright';
    if (f.cq >= p.soft) return 'soft';
    return 'dust';
  }
  return top.id;
}
function distOf(rows, p) {
  const by = {};
  for (const n of NAMES) by[n] = {};
  let lumi = 0, n = 0;
  for (const row of rows) {
    const o = judge(row.f, p);
    by[row.name][o] = (by[row.name][o] || 0) + 1;
    n++; if (o === 'lumi') lumi++;
  }
  return { by, lumi: lumi / n };
}
function pct(map, total) {
  const o = {};
  for (const k of OUTS) if (map[k]) o[k] = +(map[k] / total * 100).toFixed(2);
  return o;
}
function score(rows, p, per) {
  const d = distOf(rows, p);
  const fail = [];
  const tables = {};
  for (const name of NAMES) {
    const map = d.by[name];
    const total = Object.values(map).reduce((a, b) => a + b, 0);
    const pc = pct(map, total);
    tables[name] = pc;
    const kinds = OUTS.filter(k => (pc[k] || 0) >= 2);
    if (kinds.length < 3) fail.push(name + ' 結局' + kinds.length + '<3');
    for (const k of OUTS) if ((pc[k] || 0) > 60) fail.push(name + ' ' + k + ' ' + pc[k] + '%>60');
  }
  const lumiPct = +(d.lumi * 100).toFixed(2);
  if (lumiPct < 3 || lumiPct > 10) fail.push('螢絨 ' + lumiPct + '% 唔喺 3–10');
  const dustN = tables.normal.dust || 0;
  if (dustN > 25) fail.push('普通微塵 ' + dustN + '%>25');
  const br = tables.diligent.bright || 0;
  if (br < 30) fail.push('勤力燦光 ' + br + '%<30');
  return { fail, tables, lumiPct, per };
}
function distToV2(p, base) {
  const keys = ['top', 'gap', 'b5CQ', 'clean', 'lumiCQ', 'lumiNight', 'bright', 'soft'];
  let s = 0;
  for (const k of keys) s += Math.abs(p[k] - base[k]) / (Math.abs(base[k]) || 1);
  return s;
}
function main() {
  const N = +(process.env.N || 500);
  const t0 = Date.now();
  const rows = [];
  for (const name of NAMES) for (let i = 1; i <= N; i++) rows.push({ name, f: simulate(name, i) });
  const base = { top: 0.45, gap: 0.05, b5CQ: 55, clean: 70, lumiCQ: 55, lumiNight: 0.4, bright: 70, soft: 40 };
  const start = score(rows, base, N);
  const grid = {
    top: [0.3, 0.35, 0.4, 0.45, 0.5],
    gap: [0.02, 0.05, 0.1],
    b5CQ: [0, 40, 50, 55],
    clean: [60, 70, 85],
    lumiNight: [0.3, 0.35, 0.37, 0.38, 0.4],
    lumiCQ: [0, 50, 55],
    bright: [60, 70],
    soft: [0, 40],
  };
  let best = null, bestFail = 1e9, bestDist = 1e9, tried = 0, hits = 0;
  let lumiBand = null, lumiBandFail = 1e9, lumiBandDist = 1e9;
  function consider(p) {
    tried++;
    const sc = score(rows, p, N);
    const dist = distToV2(p, base);
    if (sc.fail.length === 0) {
      hits++;
      if (!best || dist < bestDist - 1e-9) { best = { p, sc, dist }; bestDist = dist; bestFail = 0; }
    } else if (hits === 0 && (sc.fail.length < bestFail || (sc.fail.length === bestFail && dist < bestDist))) {
      best = { p, sc, dist }; bestFail = sc.fail.length; bestDist = dist;
    }
    if (sc.lumiPct >= 3 && sc.lumiPct <= 10 && (sc.fail.length < lumiBandFail || (sc.fail.length === lumiBandFail && dist < lumiBandDist))) {
      lumiBand = { p, sc, dist }; lumiBandFail = sc.fail.length; lumiBandDist = dist;
    }
  }
  const keys = Object.keys(grid);
  function rec(i, cur) {
    if (i === keys.length) { consider(cur); return; }
    for (const v of grid[keys[i]]) rec(i + 1, Object.assign({}, cur, { [keys[i]]: v }));
  }
  rec(0, {});
  const out = {
    doc: { found: false, latestBranch: 'origin/code/glimmer-evo6', latestSha: '25e8c40c2ca96d1a514042f4d4a8d9074eaeb718', note: '已 fetch 全部分支。pet-template-v1.md 冇「§7 平衡修訂 v2」。v2 起始跟今次訊息：最高分門檻 45%。' },
    sim: 'code/glimmer-evo6 @ 25e8c40',
    assumptions: 'N=' + N + '。唔用跑機時間。照顧用時間表鐘點。每日 20% 落雨、芽崽／跳跳期每日 34% 記一次螢火（池權重約數）。肚餓先餵、心情低先玩、清潔低先沖、有便便先清。',
    v2start: { params: base, fail: start.fail, lumiPct: start.lumiPct, tables: start.tables },
    search: { tried, hits, solved: hits > 0 },
    best: best && { params: best.p, dist: +best.dist.toFixed(4), fail: best.sc.fail, lumiPct: best.sc.lumiPct, tables: best.sc.tables },
    lumiBand: lumiBand && { params: lumiBand.p, dist: +lumiBand.dist.toFixed(4), fail: lumiBand.sc.fail, lumiPct: lumiBand.sc.lumiPct, tables: lumiBand.sc.tables },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v2-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({ tried, hits, v2fail: start.fail, lumi: start.lumiPct, bestFail: best && best.sc.fail, bestLumi: best && best.sc.lumiPct, band: lumiBand && { p: lumiBand.p, fail: lumiBand.sc.fail, lumi: lumiBand.sc.lumiPct }, ms: out.ms }));
}
main();
