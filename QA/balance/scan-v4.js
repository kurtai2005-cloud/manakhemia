#!/usr/bin/env node
/* §7 平衡掃描 v4。外掛參數，唔改 code/glimmer-evo6。
 * 模擬：code/glimmer-evo6 @ 25e8c40。
 * 規格：附件 pet-template-v1.md「§7 平衡修訂 v4」（2026-11-01 01:30）。
 * 玩家隨機（QA 模型，v4 要求先算數）：上線 ±90 分鐘；每日按性格漏一次上線；
 * 餵／玩／沖／清各自按性格 60–95% 先做。隔日表仍然只排單日。冇週末加場（v4 正文冇寫）。
 * 天氣成日一種：晴 60／陰 20／雨 15／霧 5%。系統 7 嘅雨段 1–3h 今次未拆。
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
const MISS = { diligent: 0.10, normal: 0.15, office: 0.15, light: 0.18, early: 0.12, eod: 0.15 };
const ACT = {
  diligent: { feed: 0.95, play: 0.90, rinse: 0.95, poop: 0.95 },
  normal: { feed: 0.85, play: 0.75, rinse: 0.80, poop: 0.80 },
  office: { feed: 0.80, play: 0.70, rinse: 0.75, poop: 0.70 },
  light: { feed: 0.70, play: 0.65, rinse: 0.70, poop: 0.65 },
  early: { feed: 0.90, play: 0.70, rinse: 0.85, poop: 0.80 },
  eod: { feed: 0.75, play: 0.85, rinse: 0.65, poop: 0.60 },
};
const NAMES = Object.keys(SCH);
const IDS = ['tide', 'shroom', 'crystal', 'moon', 'ember'];
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const LABEL = {
  diligent: '勤力', normal: '普通', office: '返工', light: '輕度', early: '早起', eod: '隔日',
  lumi: '螢絨', tide: '水珠', shroom: '菇傘', crystal: '晶角', moon: '月眠', ember: '火苗', bright: '燦光', soft: '柔光', dust: '微塵',
};

function rngOf(seed) {
  let a = seed >>> 0 || 1;
  return () => { a = (a * 1664525 + 1013904223) >>> 0; return a / 4294967296; };
}
function morning(h) { return h >= 6 && h <= 9; }
function moonH(h) { return h >= 21 || h < 3; }
function nightH(h) { return h >= 17 || h < 7; }
function emptySc() { return { all: 0, night: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0, shroomWet: 0 }; }
function addKind(sc, hour, kind, weather) {
  sc.all++;
  if (nightH(hour)) sc.night++;
  const wet = weather === 'cloud' || weather === 'rain';
  const wetShroom = () => { if (wet) { sc.shroom++; sc.shroomWet++; } };
  if (morning(hour)) { sc.tide++; wetShroom(); return; }
  if (moonH(hour)) { sc.moon++; wetShroom(); return; }
  if (kind === 'feed') sc.shroom++;
  else if (kind === 'play') sc.ember++;
  else if (kind === 'rinse') sc.tide++;
  else if (kind === 'poop') sc.crystal++;
  if (wet && kind !== 'feed') wetShroom();
}
function doVisit(s, hour, rng, name) {
  S.setHourFn(() => hour);
  if (s.sleeping) S.toggleSleep(s);
  const pr = ACT[name];
  const kinds = [];
  if (rng() < pr.feed) {
    for (let i = 0; i < 6 && s.needs.hunger < 75; i++) { if (!S.feed(s, 'meal').ok) break; kinds.push('feed'); }
  }
  if (rng() < pr.play) {
    for (let i = 0; i < 8 && s.needs.mood < 70; i++) { if (!S.play(s).ok) break; kinds.push('play'); }
  }
  if (rng() < pr.rinse) {
    for (let i = 0; i < 6 && s.needs.clean < 75; i++) { if (!S.rinse(s).ok) break; kinds.push('rinse'); }
  }
  if (rng() < pr.poop) {
    for (let i = 0; i < 4 && s.poops; i++) { if (!S.clearPoop(s).ok) break; kinds.push('poop'); }
  }
  if (s.needs.energy < 25 && !s.sleeping) S.toggleSleep(s);
  return kinds;
}
function simulate(name, seed) {
  const rng = rngOf(seed * 1009 + NAMES.indexOf(name) * 17 + 3);
  const s = S.newState(Date.UTC(2026, 0, 1), seed);
  let absH = 0;
  const maxH = 400 * 24;
  const sc = emptySc();
  const visits = [];
  const careDay = new Set();
  const weatherOf = {};
  const dayVisits = {};
  const ffRolled = {};
  let ff = 0, sproutAt = null, adultAt = null;
  function ensureWeather(day) {
    if (weatherOf[day] != null) return weatherOf[day];
    const u = rng();
    weatherOf[day] = u < 0.60 ? 'sun' : u < 0.80 ? 'cloud' : u < 0.95 ? 'rain' : 'fog';
    return weatherOf[day];
  }
  function planDay(day) {
    if (dayVisits[day]) return dayVisits[day];
    ensureWeather(day);
    let hours = SCH[name].slice();
    if (name === 'eod' && day % 2 === 1) hours = [];
    if (hours.length && rng() < MISS[name]) hours.splice(Math.floor(rng() * hours.length), 1);
    const times = [];
    for (const h of hours) {
      let t = day * 24 + h + (rng() * 3 - 1.5);
      if (t < day * 24) t = day * 24 + 0.02;
      if (t >= (day + 1) * 24) t = (day + 1) * 24 - 0.02;
      times.push(t);
    }
    times.sort((a, b) => a - b);
    dayVisits[day] = times;
    return times;
  }
  function onEnterDay(day) {
    ensureWeather(day);
    if (ffRolled[day]) return;
    ffRolled[day] = true;
    if ((s.stage === 'sprout' || s.stage === 'juvenile') && rng() < 0.34) { S.noteEvent(s, 'firefly_walk'); ff++; }
  }
  function nextVisit(fromH) {
    const day0 = Math.floor(fromH / 24);
    for (let d = day0; d < day0 + 10; d++) {
      for (const t of planDay(d)) if (t > fromH + 1e-6) return t;
    }
    return null;
  }
  while (absH < maxH && s.stage !== 'adult' && s.stage !== 'elder') {
    onEnterDay(Math.floor(absH / 24));
    const next = nextVisit(absH);
    if (next == null || next >= maxH) break;
    let left = next - absH;
    while (left > 1e-9) {
      const hourNow = ((absH % 24) + 24) % 24;
      const toB = Math.min(left, Math.max(0.05, 24 - hourNow));
      const before = s.stage;
      S.setHourFn(() => hourNow);
      S.advance(s, toB * H, {}, 3600);
      absH += toB; left -= toB;
      const dayNow = Math.floor(absH / 24 + 1e-9);
      if (dayNow !== Math.floor((absH - toB) / 24 + 1e-9)) onEnterDay(dayNow);
      if (sproutAt == null && (s.stage === 'sprout' || s.stage === 'juvenile') && before !== 'sprout' && before !== 'juvenile') sproutAt = absH;
      if (s.stage === 'adult' || s.stage === 'elder') { adultAt = absH; left = 0; break; }
    }
    if (s.stage === 'adult' || s.stage === 'elder') break;
    const hour = ((absH % 24) + 24) % 24;
    const day = Math.floor(absH / 24);
    const weather = ensureWeather(day);
    const kinds = doVisit(s, hour, rng, name);
    if ((s.stage === 'sprout' || s.stage === 'juvenile') && kinds.length) {
      if (sproutAt == null) sproutAt = absH;
      for (const k of kinds) addKind(sc, hour, k, weather);
      visits.push({ t: absH, n: kinds.length });
      careDay.add(day);
    }
  }
  if (adultAt == null) adultAt = absH;
  const segs = [];
  if (sproutAt != null) {
    let t = sproutAt;
    for (const v of visits) { segs.push([Math.max(0, v.t - t), v.n]); t = v.t; }
    segs.push([Math.max(0, adultAt - t), 0]);
  }
  const endDay = Math.floor(adultAt / 24);
  let days7 = 0;
  for (let d = endDay - 6; d <= endDay; d++) if (careDay.has(d)) days7++;
  const E = s.evo || {};
  let cs = 0, cn = 0;
  for (const st of ['sprout', 'juvenile']) { const c = E.cl && E.cl[st]; if (c) { cs += c.sum; cn += c.sec; } }
  return {
    adult: s.stage === 'adult' || s.stage === 'elder', ff, segs, days7,
    clean: cn > 0 ? cs / cn : null,
    all: sc.all, night: sc.all ? sc.night / sc.all : 0,
    tide: sc.tide, shroom: sc.shroom, crystal: sc.crystal, moon: sc.moon, ember: sc.ember, shroomWet: sc.shroomWet,
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
function ranked(f, p) {
  const crystal = f.clean != null && f.clean >= p.cleanMin ? f.crystal : 0;
  const score = { tide: f.tide, shroom: f.shroom, crystal, moon: f.moon, ember: f.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  return { rank, all: f.all, score };
}
function branchOf(f, cq, p) {
  if (!f.adult) return { a: 'none', b: null, wa: 1 };
  const { rank, all } = ranked(f, p);
  const top = rank[0], second = rank[1];
  const share = all ? top.n / all : 0;
  const gap = all ? (top.n - second.n) / all * 100 : 100;
  if (cq >= p.brightCq && f.days7 >= p.brightDays && share < p.brightMax - 1e-12) return { a: 'bright', b: null, wa: 1 };
  if (all > 0 && top.n > 0 && share + 1e-12 >= p.specShare && cq >= p.specCq) {
    if (second.n > 0 && gap < p.gapPt - 1e-9) {
      const wa = top.n / (top.n + second.n);
      return { a: top.id, b: second.id, wa };
    }
    return { a: top.id, b: null, wa: 1 };
  }
  if (cq >= p.softCq) return { a: 'soft', b: null, wa: 1 };
  return { a: 'dust', b: null, wa: 1 };
}
function mixRun(f, cq, p) {
  const w = {};
  const pL = f.ff > 0 && cq >= p.lumiCq ? nightP(f.night, p) : 0;
  if (pL > 0) w.lumi = pL;
  const br = branchOf(f, cq, p);
  const rest = 1 - (w.lumi || 0);
  w[br.a] = (w[br.a] || 0) + rest * br.wa;
  if (br.b) w[br.b] = (w[br.b] || 0) + rest * (1 - br.wa);
  return w;
}
function median(xs) {
  const a = xs.slice().sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}
function evaluate(byName, p) {
  const tables = {};
  const cqMed = {};
  const cqMax = {};
  const total = {};
  for (const id of PATHS) total[id] = 0;
  let nAll = 0;
  const fail = [];
  for (const name of NAMES) {
    const runs = byName[name];
    const acc = {};
    const cqs = [];
    for (const f of runs) {
      const cq = cqOf(f.segs, p);
      cqs.push(cq);
      const w = mixRun(f, cq, p);
      for (const k in w) acc[k] = (acc[k] || 0) + w[k];
    }
    const n = runs.length;
    const pc = {};
    for (const id of PATHS) {
      pc[id] = +(((acc[id] || 0) / n) * 100).toFixed(2);
      total[id] += acc[id] || 0;
    }
    tables[name] = pc;
    nAll += n;
    cqMed[name] = +median(cqs).toFixed(2);
    cqMax[name] = +Math.max(...cqs).toFixed(2);
    const kinds = PATHS.filter(id => pc[id] >= 2 - 1e-9);
    if (kinds.length < 2) fail.push(LABEL[name] + ' 結局' + kinds.length + '<2');
    for (const id of PATHS) if (pc[id] > 85 + 1e-9) fail.push(LABEL[name] + ' ' + LABEL[id] + ' ' + pc[id] + '%>85');
  }
  const lumiPct = +((total.lumi / nAll) * 100).toFixed(2);
  const totalPct = {};
  for (const id of PATHS) {
    totalPct[id] = +((total[id] / nAll) * 100).toFixed(2);
    if (totalPct[id] < 2 - 1e-9) fail.push(LABEL[id] + ' 全體 ' + totalPct[id] + '%<2');
  }
  if (lumiPct < 3 - 1e-9 || lumiPct > 10 + 1e-9) fail.push('螢絨全體 ' + lumiPct + '% 唔喺 3–10');
  const softC = (tables.light.soft + tables.eod.soft) / 2;
  const dustC = (tables.light.dust + tables.eod.dust) / 2;
  if (softC < 2 - 1e-9) fail.push('疏玩合計柔光 ' + +softC.toFixed(2) + '%<2');
  if (dustC < 2 - 1e-9) fail.push('疏玩合計微塵 ' + +dustC.toFixed(2) + '%<2');
  for (const name of ['light', 'eod']) {
    if (cqMed[name] < 15 || cqMed[name] > 35) fail.push(LABEL[name] + ' CQ中位 ' + cqMed[name] + ' 唔喺 15–35');
  }
  return { fail, tables, lumiPct, cqMed, cqMax, totalPct, sparse: { soft: +softC.toFixed(2), dust: +dustC.toFixed(2) } };
}
function distTo(p, base) {
  let s = 0;
  for (const k in base) s += Math.abs(p[k] - base[k]) / (Math.abs(base[k]) || 1);
  return s;
}
function shroomStat(runs, cleanMin) {
  const n = runs.length;
  let top1 = 0, top2 = 0, feedTop2 = 0;
  const top2Of = { tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 };
  const share = { tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0, shroomFeed: 0 };
  const ahead = { tide: 0, crystal: 0, moon: 0, ember: 0 };
  for (const r of runs) {
    const crystal = r.clean != null && r.clean >= cleanMin ? r.crystal : 0;
    const sc = { tide: r.tide, shroom: r.shroom, crystal, moon: r.moon, ember: r.ember };
    const all = r.all || 1;
    for (const k of IDS) share[k] += sc[k] / all;
    share.shroomFeed += Math.max(0, r.shroom - r.shroomWet) / all;
    const rank = IDS.map(id => ({ id, n: sc[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
    if (rank[0].id === 'shroom') top1++;
    if (rank[0].id === 'shroom' || rank[1].id === 'shroom') top2++;
    top2Of[rank[0].id]++; top2Of[rank[1].id]++;
    for (const k of ['tide', 'crystal', 'moon', 'ember']) if (sc[k] > sc.shroom) ahead[k]++;
    const feed = Math.max(0, r.shroom - r.shroomWet);
    const sc2 = { tide: r.tide, shroom: feed, crystal, moon: r.moon, ember: r.ember };
    const rank2 = IDS.map(id => ({ id, n: sc2[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
    if (rank2[0].id === 'shroom' || rank2[1].id === 'shroom') feedTop2++;
  }
  const pct = (x) => +((x / n) * 100).toFixed(1);
  const mean = {};
  for (const k in share) mean[k] = +((share[k] / n) * 100).toFixed(1);
  const aheadPct = {};
  for (const k in ahead) aheadPct[k] = pct(ahead[k]);
  const top2Pct = {};
  for (const k in top2Of) top2Pct[k] = pct(top2Of[k]);
  return { n, top1: pct(top1), top2: pct(top2), feedOnlyTop2: pct(feedTop2), meanShare: mean, aheadOfShroom: aheadPct, top2Pct };
}
function cqStat(runs, p) {
  const cqs = runs.map(r => cqOf(r.segs, p)).sort((a, b) => a - b);
  const n = cqs.length;
  const p95 = cqs[Math.min(n - 1, Math.floor(n * 0.95))];
  const days = runs.filter(r => r.days7 >= 5).length;
  return {
    med: +median(cqs).toFixed(2), max: +cqs[n - 1].toFixed(2), p95: +p95.toFixed(2),
    ge30: +((cqs.filter(x => x >= 30).length / n) * 100).toFixed(1),
    ge60: +((cqs.filter(x => x >= 60).length / n) * 100).toFixed(1),
    days5: +((days / n) * 100).toFixed(1),
  };
}
function main() {
  const N = +(process.env.N || 500);
  const t0 = Date.now();
  const byName = {};
  const uniq = {};
  for (const name of NAMES) {
    const runs = [];
    const sig = new Set();
    for (let i = 1; i <= N; i++) {
      const r = simulate(name, i);
      runs.push(r);
      sig.add([r.tide, r.shroom, r.crystal, r.moon, r.ember, r.days7].join(','));
    }
    byName[name] = runs;
    uniq[name] = sig.size;
  }
  const base = {
    gapPt: 5, nightLo: 0.30, nightHi: 0.50, pMax: 0.25, lumiCq: 40,
    brightCq: 30, brightMax: 0.45, brightDays: 5,
    specShare: 0.45, specCq: 0, softCq: 20, cleanMin: 60,
    gain: 1.5, decay: 0.05, floor: 8, cq0: 50,
  };
  const grid = {
    gapPt: [5, 12, 20, 30],
    nightLo: [0.15, 0.20, 0.25, 0.30],
    nightHi: [0.40, 0.50, 0.65],
    pMax: [0.25, 0.40, 0.60],
    lumiCq: [20, 25, 30, 40],
    brightCq: [20, 30, 40],
    brightMax: [0.40, 0.45, 0.55],
    brightDays: [4, 5, 6],
    specShare: [0.30, 0.35, 0.45],
    specCq: [0, 20, 30],
    softCq: [15, 20, 28],
    cleanMin: [50, 60, 75],
    gain: [0.6, 1.0, 1.5, 2.5],
    decay: [0.02, 0.05, 0.08, 0.12],
    floor: [5, 8, 15],
    cq0: [40, 50],
  };
  const start = evaluate(byName, base);
  let tried = 1, hits = start.fail.length === 0 ? 1 : 0;
  let best = { p: Object.assign({}, base), sc: start, dist: 0 };
  function consider(p) {
    if (!(p.nightHi > p.nightLo)) return;
    tried++;
    const sc = evaluate(byName, p);
    const dist = distTo(p, base);
    if (sc.fail.length === 0) hits++;
    const betterFail = sc.fail.length < best.sc.fail.length;
    const tieCloser = sc.fail.length === best.sc.fail.length && dist < best.dist - 1e-9;
    if (betterFail || tieCloser) best = { p: Object.assign({}, p), sc, dist };
  }
  const lumiKeys = ['lumiCq', 'nightLo', 'nightHi', 'pMax'];
  const rankKeys = ['gapPt', 'specShare', 'brightMax'];
  function cart(keys, seed) {
    function rec(i, cur) {
      if (i === keys.length) { consider(cur); return; }
      for (const v of grid[keys[i]]) rec(i + 1, Object.assign({}, cur, { [keys[i]]: v }));
    }
    rec(0, Object.assign({}, seed));
  }
  cart(lumiKeys.concat(rankKeys), base);
  const cqKeys = ['gain', 'decay', 'floor', 'cq0', 'brightCq', 'softCq', 'cleanMin', 'brightDays', 'specCq'];
  let cur = Object.assign({}, best.p);
  for (let pass = 0; pass < 2; pass++) {
    let moved = false;
    const before = best.sc.fail.length + best.dist;
    for (const k of cqKeys.concat(rankKeys, lumiKeys)) {
      for (const v of grid[k]) {
        if (cur[k] === v) continue;
        consider(Object.assign({}, cur, { [k]: v }));
      }
    }
    cur = Object.assign({}, best.p);
    if (best.sc.fail.length + best.dist >= before - 1e-9) { if (!moved) break; }
    moved = true;
  }
  const shroom = {};
  const cq0 = {};
  for (const name of NAMES) {
    shroom[name] = shroomStat(byName[name], 60);
    cq0[name] = cqStat(byName[name], base);
  }
  const allRuns = NAMES.reduce((a, n) => a.concat(byName[n]), []);
  const night = {};
  for (const name of NAMES) {
    const xs = byName[name].map(r => r.night).sort((a, b) => a - b);
    const q = (p) => xs[Math.min(xs.length - 1, Math.floor((xs.length - 1) * p))];
    night[name] = { med: +q(0.5).toFixed(3), p90: +q(0.9).toFixed(3) };
  }
  const out = {
    doc: '附件 §7 平衡修訂 v4（2026-11-01 01:30）。',
    sim: 'code/glimmer-evo6 @ 25e8c40c2ca96d1a514042f4d4a8d9074eaeb718',
    stars: '無。sim 冇星星碎欄位。',
    player: {
      jitterMin: 90,
      miss: MISS,
      act: ACT,
      weather: { sun: 0.60, cloud: 0.20, rain: 0.15, fog: 0.05, scope: '成日' },
      weekendExtra: false,
      eod: '單日先排 12:00，可以漏呢一次，唔會改成日日上線',
    },
    uniq,
    shroomAtClean60: shroom,
    shroomAll: shroomStat(allRuns, 60),
    night,
    cqAtStart: cq0,
    v4start: { params: base, fail: start.fail, lumiPct: start.lumiPct, cqMed: start.cqMed, cqMax: start.cqMax, tables: start.tables, totalPct: start.totalPct, sparse: start.sparse },
    search: { tried, hits, solved: best.sc.fail.length === 0, method: 'lumi×rank cartesian，再沿最佳點逐個參數' },
    best: { params: best.p, dist: +best.dist.toFixed(4), fail: best.sc.fail, lumiPct: best.sc.lumiPct, cqMed: best.sc.cqMed, cqMax: best.sc.cqMax, tables: best.sc.tables, totalPct: best.sc.totalPct, sparse: best.sc.sparse },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v4-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    tried, hits, ms: out.ms, uniq,
    startFailN: start.fail.length, startLumi: start.lumiPct, startCq: start.cqMed, startFail: start.fail,
    bestFailN: best.sc.fail.length, bestDist: +best.dist.toFixed(3), bestLumi: best.sc.lumiPct, bestCq: best.sc.cqMed, bestFail: best.sc.fail,
    shroomTop2: out.shroomAll.top2, feedOnlyTop2: out.shroomAll.feedOnlyTop2, top2Pct: out.shroomAll.top2Pct,
    bestParams: best.p,
  }));
}
main();
