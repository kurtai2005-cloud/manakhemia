#!/usr/bin/env node
/* §7 平衡掃描 v5。外掛參數，唔改 code/glimmer-evo6。
 * 模擬：code/glimmer-evo6 @ 25e8c40。
 * 規格：附件 pet-template-v1.md「§7 平衡修訂 v5」（2026-11-01 01:40）。
 * 玩家隨機同天氣沿 v4。晶角只計便便出現後 10 分鐘內清（sim poopIntervalH＝3）。
 * 眼瞓＝精力 <30 而且未瞓（EXPR tired）。哄瞓只喺 20:00–03:00。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('/tmp/glimmer-evo6/src/glimmer-a/src/sim.js');
const D = require('/tmp/glimmer-evo6/src/glimmer-a/src/data.js');
const H = 3600;
const PI = D.PARAMS.poopIntervalH * H;
const FRESH = 10 * 60;
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
const COAX = { diligent: 0.80, normal: 0.55, office: 0.45, light: 0.40, early: 0.15, eod: 0.10 };
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
function moonH(h) { return h >= 20 || h < 3; }
function nightH(h) { return h >= 17 || h < 7; }
function wetW(weather) { return weather === 'rain' ? 1 : weather === 'cloud' ? 0.5 : 0; }
function emptySc() { return { all: 0, night: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }; }
function addCare(sc, hour, kind, weather, freshCrystal) {
  sc.all++;
  if (nightH(hour)) sc.night++;
  const wet = wetW(weather);
  if (morning(hour)) sc.tide++;
  else if (moonH(hour)) sc.moon++;
  else if (kind === 'feed') sc.shroom++;
  else if (kind === 'play') sc.ember++;
  else if (kind === 'rinse') sc.tide++;
  if (freshCrystal) sc.crystal++;
  if (wet && kind !== 'feed') sc.shroom += wet;
}
function doVisit(s, hour, rng, name, weather, queue, absSec, coaxLeft) {
  S.setHourFn(() => hour);
  if (s.sleeping) S.toggleSleep(s);
  const pr = ACT[name];
  const kinds = [];
  const ages = [];
  let immediate = 0;
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
    for (let i = 0; i < 4 && s.poops; i++) {
      if (!S.clearPoop(s).ok) break;
      const born = queue.length ? queue.shift() : -1e15;
      const age = absSec - born;
      ages.push(age);
      if (age <= FRESH) immediate++;
      kinds.push('poop');
    }
  }
  let coax = 0;
  if (moonH(hour) && s.needs.energy < 30 && !s.sleeping && coaxLeft > 0 && rng() < COAX[name]) {
    S.toggleSleep(s);
    coax = 1;
  } else if (s.needs.energy < 25 && !s.sleeping) S.toggleSleep(s);
  return { kinds, immediate, ages, coax };
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
  const queue = [];
  const coaxNight = {};
  let ff = 0, sproutAt = null, adultAt = null;
  let spawns = 0, clears = 0, immediate = 0, ageSum = 0, coaxN = 0;
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
  function advanceTo(target) {
    let left = (target - absH) * H;
    while (left > 1e-6) {
      const hourNow = ((absH % 24) + 24) % 24;
      const toBoundary = Math.max(30, (24 - hourNow) * H);
      const dt = Math.min(left, toBoundary, 120);
      const before = s.stage;
      const timer0 = s.poopTimer, poops0 = s.poops;
      const base = absH * H;
      S.setHourFn(() => hourNow);
      S.step(s, dt);
      if (s.poops > poops0) {
        let timer = timer0, elapsed = 0;
        for (let i = 0; i < s.poops - poops0; i++) {
          elapsed += PI - timer;
          queue.push(base + elapsed);
          timer = 0;
        }
      }
      if (queue.length !== s.poops) throw new Error(name + ' poop desync ' + queue.length + ' vs ' + s.poops + ' dt ' + dt);
      absH += dt / H; left -= dt;
      const dayNow = Math.floor(absH / 24 + 1e-9);
      if (dayNow !== Math.floor((absH - dt / H) / 24 + 1e-9)) onEnterDay(dayNow);
      if (sproutAt == null && (s.stage === 'sprout' || s.stage === 'juvenile') && before !== 'sprout' && before !== 'juvenile') sproutAt = absH;
      if (s.stage === 'adult' || s.stage === 'elder') { adultAt = absH; return true; }
    }
    return false;
  }
  while (absH < maxH && s.stage !== 'adult' && s.stage !== 'elder') {
    onEnterDay(Math.floor(absH / 24));
    const next = nextVisit(absH);
    if (next == null || next >= maxH) break;
    if (advanceTo(next)) break;
    const hour = ((absH % 24) + 24) % 24;
    const day = Math.floor(absH / 24);
    const weather = ensureWeather(day);
    const nightId = hour < 3 ? day - 1 : day;
    const left = moonH(hour) ? Math.max(0, 3 - (coaxNight[nightId] || 0)) : 0;
    const vis = doVisit(s, hour, rng, name, weather, queue, absH * H, left);
    if (vis.coax) coaxNight[nightId] = (coaxNight[nightId] || 0) + 1;
    if (queue.length !== s.poops) throw new Error(name + ' poop desync after clear');
    const scoring = s.stage === 'sprout' || s.stage === 'juvenile';
    if (scoring) {
      if (sproutAt == null && (vis.kinds.length || vis.coax)) sproutAt = absH;
      spawns += 0;
      for (const k of vis.kinds) {
        const fresh = k === 'poop' ? vis.ages[vis.kinds.filter(x => x === 'poop').indexOf(k)] : null;
        // ages aligned to poop kinds in order; consume below
      }
      let ai = 0;
      for (const k of vis.kinds) {
        let fresh = false;
        if (k === 'poop') {
          const age = vis.ages[ai++];
          ageSum += age; clears++;
          if (age <= FRESH) { immediate++; fresh = true; }
        }
        addCare(sc, hour, k, weather, fresh);
      }
      if (vis.coax) { addCare(sc, hour, 'coax', weather, false); coaxN++; }
      if (vis.kinds.length || vis.coax) {
        visits.push({ t: absH, n: vis.kinds.length + vis.coax });
        careDay.add(day);
      }
    } else if (vis.kinds.length || vis.coax) {
      /* 芽崽前都清走咗，統計唔計 */
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
    tide: sc.tide, shroom: sc.shroom, crystal: sc.crystal, moon: sc.moon, ember: sc.ember,
    clears, immediate, ageSum, coaxN,
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
  if (!f.adult) return { a: 'none', b: null, wa: 1 };
  const crystal = f.clean != null && f.clean >= p.cleanMin ? f.crystal : 0;
  const score = { tide: f.tide, shroom: f.shroom, crystal, moon: f.moon, ember: f.ember };
  const rank = IDS.map(id => ({ id, n: score[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
  const top = rank[0], second = rank[1], all = f.all;
  const share = all ? top.n / all : 0;
  const gap = all ? (top.n - second.n) / all * 100 : 100;
  if (cq >= p.brightCq && f.days7 >= p.brightDays && share < p.brightMax - 1e-12) return { a: 'bright', b: null, wa: 1 };
  if (all > 0 && top.n > 0 && share + 1e-12 >= p.specShare && cq >= p.specCq) {
    if (second.n > 0 && gap < p.gapPt - 1e-9) return { a: top.id, b: second.id, wa: top.n / (top.n + second.n) };
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
    const kinds = PATHS.filter(id => pc[id] >= 2 - 1e-9);
    if (kinds.length < 2) fail.push(LABEL[name] + ' 結局' + kinds.length + '<2');
    for (const id of PATHS) if (pc[id] > 85 + 1e-9) fail.push(LABEL[name] + ' ' + LABEL[id] + ' ' + pc[id] + '%>85');
    if (pc.shroom > 30 + 1e-9) fail.push(LABEL[name] + ' 菇傘 ' + pc.shroom + '%>30');
  }
  const totalPct = {};
  for (const id of PATHS) totalPct[id] = +((total[id] / nAll) * 100).toFixed(2);
  const lumiPct = totalPct.lumi;
  if (lumiPct < 3 - 1e-9 || lumiPct > 10 + 1e-9) fail.push('螢絨全體 ' + lumiPct + '% 唔喺 3–10');
  if (totalPct.crystal < 5 - 1e-9) fail.push('晶角全體 ' + totalPct.crystal + '%<5');
  if (totalPct.moon < 5 - 1e-9) fail.push('月眠全體 ' + totalPct.moon + '%<5');
  for (const id of PATHS) if (id !== 'crystal' && id !== 'moon' && id !== 'lumi' && totalPct[id] < 2 - 1e-9) fail.push(LABEL[id] + ' 全體 ' + totalPct[id] + '%<2');
  const softC = (tables.light.soft + tables.eod.soft) / 2;
  const dustC = (tables.light.dust + tables.eod.dust) / 2;
  if (softC < 2 - 1e-9) fail.push('疏玩合計柔光 ' + +softC.toFixed(2) + '%<2');
  if (dustC < 2 - 1e-9) fail.push('疏玩合計微塵 ' + +dustC.toFixed(2) + '%<2');
  for (const name of ['light', 'eod']) {
    if (cqMed[name] < 15 || cqMed[name] > 35) fail.push(LABEL[name] + ' CQ中位 ' + cqMed[name] + ' 唔喺 15–35');
  }
  return { fail, tables, lumiPct, cqMed, totalPct, sparse: { soft: +softC.toFixed(2), dust: +dustC.toFixed(2) } };
}
function distTo(p, base) {
  let s = 0;
  for (const k in base) s += Math.abs(p[k] - base[k]) / (Math.abs(base[k]) || 1);
  return s;
}
function freshStat(runs) {
  let clears = 0, immediate = 0, ageSum = 0, coax = 0;
  for (const r of runs) { clears += r.clears; immediate += r.immediate; ageSum += r.ageSum; coax += r.coaxN; }
  return {
    clears, immediate,
    freshPct: clears ? +((immediate / clears) * 100).toFixed(2) : 0,
    ageMin: clears ? +(ageSum / clears / 60).toFixed(1) : null,
    coaxPerRun: +(coax / runs.length).toFixed(2),
  };
}
function main() {
  const N = +(process.env.N || 500);
  const t0 = Date.now();
  const byName = {};
  const uniq = {};
  const fresh = {};
  for (const name of NAMES) {
    const runs = [];
    const sig = new Set();
    for (let i = 1; i <= N; i++) {
      const r = simulate(name, i);
      runs.push(r);
      sig.add([Math.round(r.tide), Math.round(r.shroom * 2), r.crystal, Math.round(r.moon), Math.round(r.ember)].join(','));
    }
    byName[name] = runs;
    uniq[name] = sig.size;
    fresh[name] = freshStat(runs);
  }
  const base = {
    gapPt: 5, nightLo: 0.30, nightHi: 0.50, pMax: 0.25, lumiCq: 25,
    brightCq: 30, brightMax: 0.45, brightDays: 5,
    specShare: 0.45, specCq: 0, softCq: 20, cleanMin: 60,
    gain: 1.5, decay: 0.05, floor: 8, cq0: 50,
  };
  const start = evaluate(byName, base);
  let tried = 1, hits = start.fail.length === 0 ? 1 : 0;
  let best = { p: Object.assign({}, base), sc: start, dist: 0 };
  if (start.fail.length) {
    const grid = {
      gapPt: [5, 12, 20, 30],
      nightLo: [0.15, 0.25, 0.30],
      nightHi: [0.45, 0.50, 0.65],
      pMax: [0.20, 0.25, 0.40],
      lumiCq: [20, 25, 30],
      brightCq: [25, 30, 40],
      brightMax: [0.35, 0.45, 0.55],
      brightDays: [4, 5, 6],
      specShare: [0.28, 0.35, 0.45],
      specCq: [0, 20],
      softCq: [15, 20, 28],
      cleanMin: [50, 60, 70],
      gain: [1.0, 1.5, 2.5],
      decay: [0.03, 0.05, 0.08],
      floor: [5, 8, 12],
      cq0: [50],
    };
    function consider(p) {
      if (!(p.nightHi > p.nightLo)) return;
      tried++;
      const sc = evaluate(byName, p);
      const dist = distTo(p, base);
      if (sc.fail.length === 0) hits++;
      const better = sc.fail.length < best.sc.fail.length || (sc.fail.length === best.sc.fail.length && dist < best.dist - 1e-9);
      if (better) best = { p: Object.assign({}, p), sc, dist };
    }
    const keysA = ['lumiCq', 'nightLo', 'nightHi', 'pMax', 'gapPt', 'specShare', 'brightMax'];
    (function cart(i, cur) {
      if (i === keysA.length) { consider(cur); return; }
      for (const v of grid[keysA[i]]) cart(i + 1, Object.assign({}, cur, { [keysA[i]]: v }));
    })(0, Object.assign({}, base));
    let cur = Object.assign({}, best.p);
    for (let pass = 0; pass < 2; pass++) {
      const before = best.sc.fail.length + best.dist;
      for (const k of Object.keys(grid)) {
        for (const v of grid[k]) {
          if (cur[k] === v) continue;
          consider(Object.assign({}, cur, { [k]: v }));
        }
      }
      cur = Object.assign({}, best.p);
      if (best.sc.fail.length + best.dist >= before - 1e-9) break;
    }
  }
  const out = {
    doc: '附件 §7 平衡修訂 v5（2026-11-01 01:40）。',
    sim: 'code/glimmer-evo6 @ 25e8c40c2ca96d1a514042f4d4a8d9074eaeb718',
    poop: { intervalH: D.PARAMS.poopIntervalH, freshMin: 10, max: D.PARAMS.poopMax },
    coax: COAX,
    drowsy: '精力 <30 而且未瞓（EXPR tired）',
    player: { jitterMin: 90, miss: MISS, act: ACT, weather: { sun: 0.60, cloud: 0.20, rain: 0.15, fog: 0.05 }, shroomW: { cloud: 0.5, rain: 1 } },
    uniq, fresh,
    v5start: { params: base, fail: start.fail, lumiPct: start.lumiPct, cqMed: start.cqMed, tables: start.tables, totalPct: start.totalPct, sparse: start.sparse },
    search: { tried, hits, solved: best.sc.fail.length === 0, ran: start.fail.length > 0 },
    best: { params: best.p, dist: +best.dist.toFixed(4), fail: best.sc.fail, lumiPct: best.sc.lumiPct, cqMed: best.sc.cqMed, tables: best.sc.tables, totalPct: best.sc.totalPct, sparse: best.sc.sparse },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v5-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    tried, ms: out.ms, uniq, fresh,
    startFail: start.fail, startLumi: start.lumiPct, startTotal: start.totalPct, startCq: start.cqMed,
    bestFailN: best.sc.fail.length, bestDist: +best.dist.toFixed(3), bestLumi: best.sc.lumiPct,
    bestCrystal: best.sc.totalPct.crystal, bestMoon: best.sc.totalPct.moon, bestFail: best.sc.fail, bestParams: best.p,
  }));
}
main();
