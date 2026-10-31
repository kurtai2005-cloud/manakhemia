#!/usr/bin/env node
/* §7 平衡掃描 v3。外掛參數，唔改 code/glimmer-evo6。
 * 模擬：code/glimmer-evo6 @ 25e8c40（require 嗰份 sim）。
 * 規格：附件 pet-template-v1.md「§7 平衡修訂 v3」（2026-11-01 01:20，未 push）。
 *
 * 文件同代碼嘅分別（掃描跟文件）：
 * - 分支：最高分贏；第一同第二差 < gapPt（起始 5）先按兩名分數比例抽。唔做五路 softmax。
 * - 螢絨：有 firefly_walk 先有資格；夜晚佔比 nightLo→nightHi 線性對應 0→pMax（起始 30%→50%＝0→25%）；CQ < lumiCq（起始 40）冇機會。高過 nightHi 維持 pMax，低過 nightLo 係 0。
 * - 分數沿 v2 自然路徑（v3 冇改分數表）：06:00–09:00（含 9:00）只計水珠；21:00–03:00 只計月眠；菇傘＝feed；晶角＝clearPoop 而且清潔平均 ≥ cleanMin（v2 起始 60）；火苗＝play（自然路徑唔開迷你遊戲）。自動落雨係 v2 backlog，呢次唔落雨。
 * - v3 冇寫專線 CQ／最高分下限。字面「最高分永遠贏」會令疏玩表（領先係月眠或水珠或火苗）去唔到柔光／微塵，同 v3 目標衝突。起始後備沿 v2：CQ ≥ specCq（40）而且最高分 ≥ specTop（30%）先算專線；否則燦光＝CQ ≥ brightCq（60）而且最高分 < brightMax（45%）；否則柔光＝CQ ≥ softCq（30）；否則微塵。
 * - CQ 公式文件冇數字。外掛：芽崽＋跳跳期，cq 由 cq0（50）開始，每小時向 floor 指數衰減，每次照顧 +gain。起始 gain 1.5、decay 0.05／時、floor 8。
 * - v2 寫過「判定鎖中午」係正式規格（測試避開真實時間）。v3 要計晨露同月眠，掃描用時間表鐘點。鎖死 12:00 會令夜晚佔比變 0，螢絨機會恆為 0。
 * - 星星碎：sim 冇呢個數。光粒唔當星星碎。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('/tmp/glimmer-evo6/src/glimmer-a/src/sim.js');
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
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const LABEL = { diligent: '勤力', normal: '普通', office: '返工', light: '輕度', early: '早起', eod: '隔日',
  lumi: '螢絨', tide: '水珠', shroom: '菇傘', crystal: '晶角', moon: '月眠', ember: '火苗', bright: '燦光', soft: '柔光', dust: '微塵' };

function rngOf(seed) {
  let a = seed >>> 0 || 1;
  return () => { a = (a * 1664525 + 1013904223) >>> 0; return a / 4294967296; };
}
function morning(h) { return h >= 6 && h <= 9; }
function moonH(h) { return h >= 21 || h < 3; }
function nightH(h) { return h >= 17 || h < 7; }
function visit(s, hour) {
  S.setHourFn(() => hour);
  if (s.sleeping) S.toggleSleep(s);
  const kinds = [];
  for (let i = 0; i < 6 && s.needs.hunger < 75; i++) { if (!S.feed(s, 'meal').ok) break; kinds.push('feed'); }
  for (let i = 0; i < 8 && s.needs.mood < 70; i++) { if (!S.play(s).ok) break; kinds.push('play'); }
  for (let i = 0; i < 6 && s.needs.clean < 75; i++) { if (!S.rinse(s).ok) break; kinds.push('rinse'); }
  for (let i = 0; i < 4 && s.poops; i++) { if (!S.clearPoop(s).ok) break; kinds.push('poop'); }
  if (s.needs.energy < 25 && !s.sleeping) S.toggleSleep(s);
  return kinds;
}
function emptySc() { return { all: 0, night: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }; }
function addKind(sc, hour, kind) {
  sc.all++; if (nightH(hour)) sc.night++;
  if (morning(hour)) { sc.tide++; return; }
  if (moonH(hour)) { sc.moon++; return; }
  if (kind === 'feed') sc.shroom++;
  else if (kind === 'play') sc.ember++;
  else if (kind === 'rinse') sc.tide++;
  else if (kind === 'poop') sc.crystal++;
}
function simulate(name, seed) {
  const rng = rngOf(seed * 1009 + NAMES.indexOf(name) * 17 + 3);
  const s = S.newState(Date.UTC(2026, 0, 1), seed);
  const opens = SCH[name];
  let absH = 0, dayMark = -1;
  const maxH = 400 * 24;
  const sc = emptySc();
  const visits = [];
  let ff = 0, sproutAt = null, adultAt = null;
  while (absH < maxH && s.stage !== 'adult' && s.stage !== 'elder') {
    const day = Math.floor(absH / 24);
    if (day !== dayMark) {
      dayMark = day;
      if ((s.stage === 'sprout' || s.stage === 'juvenile') && rng() < 0.34) { S.noteEvent(s, 'firefly_walk'); ff++; }
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
      const toB = Math.min(left, Math.max(0.05, 24 - hourNow));
      const d2 = Math.floor((absH + toB) / 24);
      if (d2 !== dayMark) {
        dayMark = d2;
        if ((s.stage === 'sprout' || s.stage === 'juvenile') && rng() < 0.34) { S.noteEvent(s, 'firefly_walk'); ff++; }
      }
      const before = s.stage;
      S.setHourFn(() => hourNow);
      S.advance(s, toB * H, {}, 3600);
      absH += toB; left -= toB;
      if (sproutAt == null && (s.stage === 'sprout' || s.stage === 'juvenile') && before !== 'sprout' && before !== 'juvenile') sproutAt = absH;
      if (s.stage === 'adult' || s.stage === 'elder') { adultAt = absH; left = 0; break; }
    }
    if (s.stage === 'adult' || s.stage === 'elder') break;
    const hour = ((absH % 24) + 24) % 24;
    const kinds = visit(s, hour);
    if (s.stage === 'sprout' || s.stage === 'juvenile') {
      if (sproutAt == null) sproutAt = absH;
      for (const k of kinds) addKind(sc, hour, k);
      visits.push({ t: absH, n: kinds.length });
    }
  }
  if (adultAt == null) adultAt = absH;
  const segs = [];
  if (sproutAt != null) {
    let t = sproutAt;
    for (const v of visits) { segs.push([Math.max(0, v.t - t), v.n]); t = v.t; }
    segs.push([Math.max(0, adultAt - t), 0]);
  }
  const E = s.evo || {};
  let cs = 0, cn = 0;
  for (const st of ['sprout', 'juvenile']) { const c = E.cl && E.cl[st]; if (c) { cs += c.sum; cn += c.sec; } }
  return {
    adult: s.stage === 'adult' || s.stage === 'elder', ff, segs, clean: cn > 0 ? cs / cn : null,
    all: sc.all, nightN: sc.night, night: sc.all ? sc.night / sc.all : 0,
    tide: sc.tide, shroom: sc.shroom, crystal: sc.crystal, moon: sc.moon, ember: sc.ember,
  };
}
function cqOf(segs, p) {
  let cq = p.cq0;
  for (const seg of segs) {
    const h = seg[0], n = seg[1];
    if (h > 0) cq = p.floor + (cq - p.floor) * Math.exp(-p.decay * h);
    if (n) cq += p.gain * n;
    if (cq > 100) cq = 100;
    if (cq < 0) cq = 0;
  }
  return cq;
}
function nightP(share, p) {
  if (!(p.nightHi > p.nightLo)) return 0;
  if (share <= p.nightLo) return 0;
  if (share >= p.nightHi) return p.pMax;
  return (share - p.nightLo) / (p.nightHi - p.nightLo) * p.pMax;
}
function branchOf(f, cq, p) {
  const crystal = f.clean != null && f.clean >= p.cleanMin ? f.crystal : 0;
  const score = { tide: f.tide, shroom: f.shroom, crystal, moon: f.moon, ember: f.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  const top = rank[0], second = rank[1], all = f.all;
  const share = all ? top.n / all : 0;
  const gap = all ? (top.n - second.n) / all * 100 : 100;
  const spec = cq >= p.specCq && all > 0 && top.n > 0 && share + 1e-12 >= p.specTop;
  if (spec) {
    if (second.n > 0 && gap < p.gapPt - 1e-9) {
      const wa = top.n / (top.n + second.n);
      return { a: top.id, b: second.id, wa };
    }
    return { a: top.id, b: null, wa: 1 };
  }
  if (cq >= p.brightCq && share < p.brightMax - 1e-12) return { a: 'bright', b: null, wa: 1 };
  if (cq >= p.softCq) return { a: 'soft', b: null, wa: 1 };
  return { a: 'dust', b: null, wa: 1 };
}
function mixRun(f, cq, p, hasFf) {
  const w = {};
  const pL = hasFf && cq >= p.lumiCq ? nightP(f.night, p) : 0;
  if (pL > 0) w.lumi = pL;
  const br = branchOf(f, cq, p);
  const rest = 1 - (w.lumi || 0);
  w[br.a] = (w[br.a] || 0) + rest * br.wa;
  if (br.b) w[br.b] = (w[br.b] || 0) + rest * (1 - br.wa);
  return w;
}
function evaluate(arch, p) {
  const tables = {};
  const cqMed = {};
  const total = {};
  for (const id of PATHS) total[id] = 0;
  let nAll = 0;
  const fail = [];
  for (const name of NAMES) {
    const f = arch[name];
    const cq = cqOf(f.segs, p);
    cqMed[name] = +cq.toFixed(2);
    const w0 = mixRun(f, cq, p, false);
    const w1 = mixRun(f, cq, p, true);
    const n0 = f.ffs.length - f.ffPos;
    const acc = {};
    for (const k in w0) acc[k] = (acc[k] || 0) + w0[k] * n0;
    for (const k in w1) acc[k] = (acc[k] || 0) + w1[k] * f.ffPos;
    const n = f.ffs.length;
    const pc = {};
    for (const id of PATHS) {
      const v = (acc[id] || 0) / n * 100;
      pc[id] = +v.toFixed(2);
      total[id] += acc[id] || 0;
    }
    tables[name] = pc;
    nAll += n;
    const kinds = PATHS.filter(id => pc[id] >= 2 - 1e-9);
    if (kinds.length < 2) fail.push(LABEL[name] + ' 結局' + kinds.length + '<2');
    for (const id of PATHS) if (pc[id] > 85 + 1e-9) fail.push(LABEL[name] + ' ' + LABEL[id] + ' ' + pc[id] + '%>85');
  }
  const lumiPct = +((total.lumi / nAll) * 100).toFixed(2);
  for (const id of PATHS) {
    const pct = total[id] / nAll * 100;
    if (pct < 2 - 1e-9) fail.push(LABEL[id] + ' 全體 ' + +pct.toFixed(2) + '%<2');
  }
  if (lumiPct < 3 - 1e-9 || lumiPct > 10 + 1e-9) fail.push('螢絨全體 ' + lumiPct + '% 唔喺 3–10');
  for (const name of ['light', 'eod']) {
    if (tables[name].soft < 2 - 1e-9) fail.push(LABEL[name] + ' 柔光 ' + tables[name].soft + '%<2');
    if (tables[name].dust < 2 - 1e-9) fail.push(LABEL[name] + ' 微塵 ' + tables[name].dust + '%<2');
    if (cqMed[name] < 15 || cqMed[name] > 35) fail.push(LABEL[name] + ' CQ中位 ' + cqMed[name] + ' 唔喺 15–35');
  }
  return { fail, tables, lumiPct, cqMed, totalPct: PATHS.reduce((o, id) => { o[id] = +((total[id] / nAll) * 100).toFixed(2); return o; }, {}) };
}
function distTo(p, base) {
  let s = 0;
  for (const k in base) s += Math.abs(p[k] - base[k]) / (Math.abs(base[k]) || 1);
  return s;
}
function main() {
  const N = +(process.env.N || 500);
  const t0 = Date.now();
  const arch = {};
  for (const name of NAMES) {
    const ffs = [];
    let proto = null, segKey = null;
    for (let i = 1; i <= N; i++) {
      const r = simulate(name, i);
      const sk = JSON.stringify(r.segs);
      if (!proto) { proto = r; segKey = sk; }
      else {
        for (const k of ['all', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'nightN']) {
          if (r[k] !== proto[k]) throw new Error(name + ' score varied ' + k);
        }
        if (sk !== segKey) throw new Error(name + ' cq segments varied');
      }
      ffs.push(r.ff);
    }
    arch[name] = Object.assign({}, proto, { ffs, ffPos: ffs.filter(x => x > 0).length });
  }
  const base = {
    gapPt: 5, nightLo: 0.30, nightHi: 0.50, pMax: 0.25, lumiCq: 40,
    specCq: 40, specTop: 0.30, brightCq: 60, brightMax: 0.45, softCq: 30, cleanMin: 60,
    gain: 1.5, decay: 0.05, floor: 8, cq0: 50,
  };
  const start = evaluate(arch, base);
  const grid = {
    gapPt: [5, 15, 25, 40],
    nightLo: [0.2, 0.3],
    nightHi: [0.45, 0.6, 0.9],
    pMax: [0.25, 0.5],
    lumiCq: [15, 25, 40],
    specCq: [15, 30, 45, 70],
    specTop: [0, 0.35, 0.5],
    brightCq: [60, 80],
    brightMax: [0.45, 1],
    softCq: [20, 30, 45],
    cleanMin: [60, 101],
    gain: [0.5, 1.5, 2.5],
    decay: [0.02, 0.05, 0.1],
    floor: [0, 10],
    cq0: [50],
  };
  const keys = Object.keys(grid);
  let tried = 0, hits = 0, best = null, bestFail = 1e9, bestDist = 1e9;
  const pathMax = {};
  for (const id of PATHS) pathMax[id] = 0;
  function consider(p) {
    if (!(p.nightHi > p.nightLo)) return;
    tried++;
    const sc = evaluate(arch, p);
    const dist = distTo(p, base);
    for (const id of PATHS) if (sc.totalPct[id] > pathMax[id]) pathMax[id] = sc.totalPct[id];
    if (sc.fail.length === 0) {
      hits++;
      if (!best || dist < bestDist - 1e-9) { best = { p, sc, dist }; bestDist = dist; bestFail = 0; }
    } else if (hits === 0 && (sc.fail.length < bestFail || (sc.fail.length === bestFail && dist < bestDist))) {
      best = { p, sc, dist }; bestFail = sc.fail.length; bestDist = dist;
    }
  }
  function rec(i, cur) {
    if (i === keys.length) { consider(cur); return; }
    for (const v of grid[keys[i]]) rec(i + 1, Object.assign({}, cur, { [keys[i]]: v }));
  }
  rec(0, {});
  const snap = {};
  for (const name of NAMES) {
    const f = arch[name];
    snap[name] = {
      n: f.ffs.length, adult: f.adult, ffPos: f.ffPos,
      night: +f.night.toFixed(3), clean: f.clean == null ? null : +f.clean.toFixed(1), all: f.all,
      share: {
        tide: +(f.tide / f.all).toFixed(3), shroom: +(f.shroom / f.all).toFixed(3),
        crystal: +(f.crystal / f.all).toFixed(3), moon: +(f.moon / f.all).toFixed(3), ember: +(f.ember / f.all).toFixed(3),
      },
    };
  }
  const out = {
    doc: '附件 §7 平衡修訂 v3（2026-11-01 01:20）。repo 未有呢段。',
    sim: 'code/glimmer-evo6 @ 25e8c40c2ca96d1a514042f4d4a8d9074eaeb718',
    stars: '無。sim 冇星星碎欄位。',
    snap, v2modelNote: '專線門檻 specCq/specTop/bright/soft/cleanMin 係 v2 殘留起始值，v3 正文冇寫。',
    v3start: { params: base, fail: start.fail, lumiPct: start.lumiPct, cqMed: start.cqMed, tables: start.tables, totalPct: start.totalPct },
    search: { tried, hits, solved: hits > 0, pathMax },
    best: best && { params: best.p, dist: +best.dist.toFixed(4), fail: best.sc.fail, lumiPct: best.sc.lumiPct, cqMed: best.sc.cqMed, tables: best.sc.tables, totalPct: best.sc.totalPct },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v3-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    tried, hits, ms: out.ms, pathMax,
    startFail: start.fail.length, startLumi: start.lumiPct, startCq: start.cqMed,
    bestFailN: best && best.sc.fail.length, bestDist: best && +best.dist.toFixed(3),
    bestLumi: best && best.sc.lumiPct, bestCq: best && best.sc.cqMed, bestFail: best && best.sc.fail,
  }));
}
main();
