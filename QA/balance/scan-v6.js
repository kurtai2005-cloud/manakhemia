#!/usr/bin/env node
/* §7 平衡掃描 v6。外掛，唔改 code/glimmer-evo6 @ 25e8c40。
 * 附件「§7 平衡修訂 v6」（2026-11-01 01:48）。
 * 沿 v5：玩家隨機、天氣、哄瞓、菇傘權重 陰 0.5／雨 1。
 * 鎖：螢絨 CQ 25、機會上限 20%、柔光 CQ 28、清潔 ≥60。
 * 晶角：上線一刻已有便便，2 分鐘內清晒，計 1，每次上線最多 1。
 * 上線期間新冧嘅便便文件冇寫，唔計。上線係即時結算，訪問入面唔再跑便便鐘。
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
  diligent: { feed: 0.95, play: 0.90, rinse: 0.95 },
  normal: { feed: 0.85, play: 0.75, rinse: 0.80 },
  office: { feed: 0.80, play: 0.70, rinse: 0.75 },
  light: { feed: 0.70, play: 0.65, rinse: 0.70 },
  early: { feed: 0.90, play: 0.70, rinse: 0.85 },
  eod: { feed: 0.75, play: 0.85, rinse: 0.65 },
};
const PROMPT = { diligent: 0.90, normal: 0.70, office: 0.50, light: 0.35, early: 0.75, eod: 0.30 };
const COAX = { diligent: 0.80, normal: 0.55, office: 0.45, light: 0.40, early: 0.15, eod: 0.10 };
const NAMES = Object.keys(SCH);
const IDS = ['tide', 'shroom', 'crystal', 'moon', 'ember'];
const PATHS = ['lumi', 'tide', 'shroom', 'crystal', 'moon', 'ember', 'bright', 'soft', 'dust'];
const LABEL = {
  diligent: '勤力', normal: '普通', office: '返工', light: '輕度', early: '早起', eod: '隔日',
  lumi: '螢絨', tide: '水珠', shroom: '菇傘', crystal: '晶角', moon: '月眠', ember: '火苗', bright: '燦光', soft: '柔光', dust: '微塵',
};
const LOCKED = ['lumiCq', 'pMax', 'softCq', 'cleanMin'];

function rngOf(seed) {
  let a = seed >>> 0 || 1;
  return () => { a = (a * 1664525 + 1013904223) >>> 0; return a / 4294967296; };
}
function morning(h) { return h >= 6 && h <= 9; }
function moonH(h) { return h >= 20 || h < 3; }
function nightH(h) { return h >= 17 || h < 7; }
function wetW(weather) { return weather === 'rain' ? 1 : weather === 'cloud' ? 0.5 : 0; }
function emptySc() { return { all: 0, night: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }; }
function addCare(sc, hour, kind, weather) {
  sc.all++;
  if (nightH(hour)) sc.night++;
  const wet = wetW(weather);
  if (morning(hour)) sc.tide++;
  else if (moonH(hour)) sc.moon++;
  else if (kind === 'feed') sc.shroom++;
  else if (kind === 'play') sc.ember++;
  else if (kind === 'rinse') sc.tide++;
  if (wet && kind !== 'feed') sc.shroom += wet;
}
function addCrystal(sc, hour, weather) {
  sc.all++;
  if (nightH(hour)) sc.night++;
  sc.crystal++;
  const wet = wetW(weather);
  if (wet) sc.shroom += wet;
}
function doVisit(s, hour, rng, name, weather, coaxLeft) {
  S.setHourFn(() => hour);
  if (s.sleeping) S.toggleSleep(s);
  const hadPoop = s.poops > 0;
  let crystal = 0;
  if (hadPoop && rng() < PROMPT[name]) {
    for (let i = 0; i < 4 && s.poops; i++) { if (!S.clearPoop(s).ok) break; }
    crystal = 1;
  }
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
  let coax = 0;
  if (moonH(hour) && s.needs.energy < 30 && !s.sleeping && coaxLeft > 0 && rng() < COAX[name]) {
    S.toggleSleep(s);
    coax = 1;
  } else if (s.needs.energy < 25 && !s.sleeping) S.toggleSleep(s);
  return { kinds, crystal, coax, hadPoop };
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
  const coaxNight = {};
  let ff = 0, sproutAt = null, adultAt = null;
  let nVis = 0, nPoop = 0, nPrompt = 0, coaxN = 0;
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
    let stop = false;
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
      if (s.stage === 'adult' || s.stage === 'elder') { adultAt = absH; stop = true; break; }
    }
    if (stop) break;
    const hour = ((absH % 24) + 24) % 24;
    const day = Math.floor(absH / 24);
    const weather = ensureWeather(day);
    const nightId = hour < 3 ? day - 1 : day;
    const coaxLeft = moonH(hour) ? Math.max(0, 3 - (coaxNight[nightId] || 0)) : 0;
    const vis = doVisit(s, hour, rng, name, weather, coaxLeft);
    if (vis.coax) coaxNight[nightId] = (coaxNight[nightId] || 0) + 1;
    const scoring = s.stage === 'sprout' || s.stage === 'juvenile';
    if (scoring) {
      nVis++;
      if (vis.hadPoop) nPoop++;
      if (vis.crystal) nPrompt++;
      if (sproutAt == null) sproutAt = absH;
      for (const k of vis.kinds) addCare(sc, hour, k, weather);
      if (vis.crystal) addCrystal(sc, hour, weather);
      if (vis.coax) { addCare(sc, hour, 'coax', weather); coaxN++; }
      const n = vis.kinds.length + vis.crystal + vis.coax;
      if (n) { visits.push({ t: absH, n }); careDay.add(day); }
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
    nVis, nPoop, nPrompt, coaxN,
  };
}
function cqOf(segs, p) {
  let cq = p.cq0;
  for (const seg of segs) {
    if (seg[0] > 0) cq = p.floor + (cq - p.floor) * Math.exp(-p.decay * seg[0]);
    if (seg[1]) cq += p.gain * seg[1];
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
  const checks = [];
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
  for (const id of PATHS) {
    if (id === 'crystal' || id === 'moon' || id === 'lumi') continue;
    if (totalPct[id] < 2 - 1e-9) fail.push(LABEL[id] + ' 全體 ' + totalPct[id] + '%<2');
  }
  const softC = (tables.light.soft + tables.eod.soft) / 2;
  const dustC = (tables.light.dust + tables.eod.dust) / 2;
  if (softC < 2 - 1e-9) fail.push('疏玩合計柔光 ' + +softC.toFixed(2) + '%<2');
  if (dustC < 2 - 1e-9) fail.push('疏玩合計微塵 ' + +dustC.toFixed(2) + '%<2');
  for (const name of ['light', 'eod']) {
    if (cqMed[name] < 15 || cqMed[name] > 35) fail.push(LABEL[name] + ' CQ中位 ' + cqMed[name] + ' 唔喺 15–35');
  }
  if (tables.eod.dust < 2 - 1e-9 || tables.eod.ember < 2 - 1e-9) fail.push('隔日未有微塵＋火苗');
  const mark = (ok) => ok ? '✅' : '❌';
  checks.push(['晶角全體≥5%', mark(totalPct.crystal >= 5 - 1e-9), totalPct.crystal]);
  checks.push(['月眠全體≥5%', mark(totalPct.moon >= 5 - 1e-9), totalPct.moon]);
  checks.push(['螢絨 3–10%', mark(lumiPct >= 3 - 1e-9 && lumiPct <= 10 + 1e-9), lumiPct]);
  const shroomOk = NAMES.every(n => tables[n].shroom <= 30 + 1e-9);
  checks.push(['每表菇傘≤30%', mark(shroomOk), Math.max(...NAMES.map(n => tables[n].shroom))]);
  const nine = PATHS.every(id => (id === 'crystal' || id === 'moon') ? totalPct[id] >= 5 - 1e-9 : (id === 'lumi' ? lumiPct >= 3 - 1e-9 : totalPct[id] >= 2 - 1e-9));
  checks.push(['9 條路出齊', mark(nine), null]);
  const kindsOk = NAMES.every(n => PATHS.filter(id => tables[n][id] >= 2 - 1e-9).length >= 2);
  checks.push(['每表≥2 結局', mark(kindsOk), null]);
  const capOk = NAMES.every(n => PATHS.every(id => tables[n][id] <= 85 + 1e-9));
  checks.push(['單一≤85%', mark(capOk), null]);
  checks.push(['疏玩柔光＋微塵', mark(softC >= 2 - 1e-9 && dustC >= 2 - 1e-9), softC.toFixed(2) + '/' + dustC.toFixed(2)]);
  checks.push(['隔日微塵＋火苗', mark(tables.eod.dust >= 2 - 1e-9 && tables.eod.ember >= 2 - 1e-9), tables.eod.dust + '/' + tables.eod.ember]);
  const cqOk = cqMed.light >= 15 && cqMed.light <= 35 && cqMed.eod >= 15 && cqMed.eod <= 35;
  checks.push(['疏玩 CQ 15–35', mark(cqOk), cqMed.light + '/' + cqMed.eod]);
  return { fail, tables, lumiPct, cqMed, totalPct, checks, sparse: { soft: +softC.toFixed(2), dust: +dustC.toFixed(2) } };
}
function distTo(p, base) {
  let s = 0, n = 0;
  for (const k in base) {
    if (p[k] !== base[k]) n++;
    s += Math.abs(p[k] - base[k]) / (Math.abs(base[k]) || 1);
  }
  return { s, n };
}
function promptStat(runs) {
  let vis = 0, poop = 0, hit = 0;
  for (const r of runs) { vis += r.nVis; poop += r.nPoop; hit += r.nPrompt; }
  return {
    setPct: null,
    whenPoop: poop ? +((hit / poop) * 100).toFixed(1) : 0,
    ofVisits: vis ? +((hit / vis) * 100).toFixed(1) : 0,
  };
}
function main() {
  const N = +(process.env.N || 1000);
  const t0 = Date.now();
  const byName = {};
  for (const name of NAMES) {
    const runs = [];
    for (let i = 1; i <= N; i++) runs.push(simulate(name, i));
    byName[name] = runs;
  }
  const base = {
    gapPt: 5, nightLo: 0.30, nightHi: 0.50, pMax: 0.20, lumiCq: 25,
    brightCq: 30, brightMax: 0.45, brightDays: 5,
    specShare: 0.45, specCq: 0, softCq: 28, cleanMin: 60,
    gain: 1.5, decay: 0.05, floor: 8, cq0: 50,
  };
  const start = evaluate(byName, base);
  let tried = 1;
  let best = { p: Object.assign({}, base), sc: start, dist: 0, changed: 0 };
  const reach = { crystal: start.totalPct.crystal, lumi: start.lumiPct, soft: start.sparse.soft };
  if (start.fail.length) {
    const grid = {
      specShare: [0.22, 0.28, 0.35, 0.45],
      brightMax: [0.22, 0.28, 0.35, 0.45],
      gapPt: [5, 8, 12, 18],
      brightCq: [30],
      brightDays: [5],
      specCq: [0],
      nightLo: [0.30],
      nightHi: [0.50],
    };
    function consider(p) {
      for (const k of LOCKED) if (p[k] !== base[k]) return;
      tried++;
      const sc = evaluate(byName, p);
      const d = distTo(p, base);
      if (sc.totalPct.crystal > reach.crystal) reach.crystal = sc.totalPct.crystal;
      if (sc.lumiPct > reach.lumi) reach.lumi = sc.lumiPct;
      if (sc.sparse.soft > reach.soft) reach.soft = sc.sparse.soft;
      const better = sc.fail.length < best.sc.fail.length
        || (sc.fail.length === best.sc.fail.length && (d.n < best.changed || (d.n === best.changed && d.s < best.dist - 1e-9)));
      if (better) best = { p: Object.assign({}, p), sc, dist: d.s, changed: d.n };
    }
    const keys = ['specShare', 'brightMax', 'gapPt'];
    (function cart(i, cur) {
      if (i === keys.length) { consider(cur); return; }
      for (const v of grid[keys[i]]) cart(i + 1, Object.assign({}, cur, { [keys[i]]: v }));
    })(0, Object.assign({}, base));
    if (best.sc.fail.length) {
      const extra = {
        brightCq: [25, 30, 40],
        brightDays: [4, 5, 6],
        specCq: [0, 15, 20],
        nightLo: [0.20, 0.25, 0.30],
        nightHi: [0.40, 0.50, 0.60],
        gain: [1.2, 1.5, 2.0, 2.8],
        decay: [0.03, 0.05, 0.08],
        floor: [5, 8, 12],
        cq0: [50, 60],
      };
      let cur = Object.assign({}, best.p);
      for (let pass = 0; pass < 2; pass++) {
        const before = best.sc.fail.length * 100 + best.changed + best.dist;
        for (const k of Object.keys(extra)) {
          for (const v of extra[k]) {
            if (cur[k] === v) continue;
            consider(Object.assign({}, cur, { [k]: v }));
          }
        }
        cur = Object.assign({}, best.p);
        if (best.sc.fail.length * 100 + best.changed + best.dist >= before - 1e-9) break;
      }
    }
    if (best.sc.fail.length) {
      const seed = Object.assign({}, best.p);
      const grid2 = {
        specShare: [0.15, 0.18, 0.22, 0.28, 0.35],
        brightMax: [0.15, 0.18, 0.22, 0.28, 0.35],
        gapPt: [8, 12, 18, 25],
      };
      const keys2 = ['specShare', 'brightMax', 'gapPt'];
      (function cart2(i, cur) {
        if (i === keys2.length) { consider(cur); return; }
        for (const v of grid2[keys2[i]]) cart2(i + 1, Object.assign({}, cur, { [keys2[i]]: v }));
      })(0, seed);
    }
  }
  const prompt = {};
  const crystalRank = {};
  for (const name of NAMES) {
    prompt[name] = promptStat(byName[name]);
    prompt[name].setPct = +(PROMPT[name] * 100).toFixed(0);
    let top = 0, share = 0;
    for (const r of byName[name]) {
      const crystal = r.clean != null && r.clean >= 60 ? r.crystal : 0;
      const sc = { tide: r.tide, shroom: r.shroom, crystal, moon: r.moon, ember: r.ember };
      const all = r.all || 1;
      share += crystal / all;
      const rank = IDS.map(id => ({ id, n: sc[id] })).sort((a, b) => b.n - a.n || IDS.indexOf(a.id) - IDS.indexOf(b.id));
      if (rank[0].id === 'crystal') top++;
    }
    crystalRank[name] = { meanShare: +((share / byName[name].length) * 100).toFixed(1), top1: +((top / byName[name].length) * 100).toFixed(1) };
  }
  const half = {};
  for (const name of NAMES) half[name] = byName[name].slice(0, Math.min(500, byName[name].length));
  const halfSc = evaluate(half, best.p);
  const drift = {};
  for (const id of PATHS) drift[id] = +(best.sc.totalPct[id] - halfSc.totalPct[id]).toFixed(2);
  const out = {
    doc: '附件 §7 平衡修訂 v6（2026-11-01 01:48）。',
    sim: 'code/glimmer-evo6 @ 25e8c40c2ca96d1a514042f4d4a8d9074eaeb718',
    N,
    prompt, coax: COAX, crystalRank,
    locked: { lumiCq: 25, pMax: 0.2, softCq: 28, cleanMin: 60, shroomW: { cloud: 0.5, rain: 1 } },
    v6start: { params: base, fail: start.fail, checks: start.checks, lumiPct: start.lumiPct, cqMed: start.cqMed, tables: start.tables, totalPct: start.totalPct, sparse: start.sparse },
    search: { tried, solved: best.sc.fail.length === 0, changed: best.changed },
    best: { params: best.p, dist: +best.dist.toFixed(4), fail: best.sc.fail, checks: best.sc.checks, lumiPct: best.sc.lumiPct, cqMed: best.sc.cqMed, tables: best.sc.tables, totalPct: best.sc.totalPct, sparse: best.sc.sparse },
    stability: { halfN: half[NAMES[0]].length, driftTotalPct: drift, halfFail: halfSc.fail.length, fullFail: best.sc.fail.length },
    ms: Date.now() - t0,
  };
  const file = process.env.OUT || path.join(__dirname, 'scan-v6-result.json');
  fs.writeFileSync(file, JSON.stringify(out, null, 2));
  console.log(JSON.stringify({
    N, tried, ms: out.ms, changed: best.changed,
    startFail: start.fail, startCrystal: start.totalPct.crystal, startMoon: start.totalPct.moon, startLumi: start.lumiPct,
    bestFail: best.sc.fail, bestCrystal: best.sc.totalPct.crystal, bestMoon: best.sc.totalPct.moon, bestLumi: best.sc.lumiPct, reach,
    bestParams: best.p, checks: best.sc.checks, drift, prompt, crystalRank, reach,
  }));
}
main();
