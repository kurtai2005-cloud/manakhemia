'use strict';
/* QA 模型：6c 夢境 A/B/C。唔改 long6c.js。
 * 上線隨機同 route-sweep／上輪 qa-dream-days：漏 15%、±90 分鐘、跳動作 20%、加動作 30%。
 * 卡用真 long6c.pick。
 * A：21:00–03:00，另加當夜 19:00 後最後一次上線；每晚最多 1 夢。
 * B：冇上線入到嘅夜存入銀行，上限 bankCap，下次上線一次補做晒。
 * C：湖權重＝餵食、淋水、執屎、小遊戲，每樣每日最多 1。
 * 第二輪：每晚 1 片，p2 機會再 1 片；主題按權重抽，湖同其他主題共用呢個額度。
 */
const path = require('path');
const ROOT = '/tmp/glimmer-6c/src/glimmer-a';
const S = require(path.join(ROOT, 'src/sim.js'));
const M6 = require(path.join(ROOT, 'src/long6a.js'));
const DR = require(path.join(ROOT, 'src/long6c.js'));
const X = require(path.join(ROOT, 'src/systems.js'));
const D = require(path.join(ROOT, 'src/data.js'));
const FAM = require(path.join(ROOT, 'src/long5a.js'));
const SW = require(path.join(ROOT, 'tools/route-sweep.js'));
const SCHED = SW.SCHED;
const MG_AT = { 勤力: [11, 17], 普通: [13], 疏玩: [20], 夜貓: [18], 早起: [12], 餵食狂: [15] };
const JIT = 90, MISS = 0.15, SKIP_ACT = 0.2, EXTRA_ACT = 0.3;
const ACTS = ['feed', 'play', 'rinse', 'poop'];
const N = +(process.env.N || 200);
const MAXD = 180;
const T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
const DAY = 86400e3;
const THEMES = DR.THEMES;
const CFG = DR.CFG;

function med(a) { const b = a.filter(x => x != null).slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : null; }
function p10(a) { const b = a.filter(x => x != null).slice().sort((x, y) => x - y); return b.length ? b[Math.floor(b.length * 0.1)] : null; }
function dayStart(d) { return T0 + d * DAY; }
function atHour(d, h) { return dayStart(d) + h * 3600e3; }

function alloc(w, frags) {
  const ks = THEMES.filter(k => w[k] > 0), nTiles = CFG.cols * CFG.rows, out = {};
  let left = nTiles - ks.length * CFG.minTiles;
  const W = ks.reduce((a, k) => a + w[k], 0) || 1; const rem = [];
  for (const k of ks) { const x = left * w[k] / W; out[k] = CFG.minTiles + Math.floor(x); rem.push([k, x - Math.floor(x)]); }
  let used = ks.reduce((a, k) => a + out[k], 0);
  rem.sort((a, b) => b[1] - a[1] || THEMES.indexOf(a[0]) - THEMES.indexOf(b[0]));
  for (let i = 0; used < nTiles && rem.length; i = (i + 1) % rem.length) { out[rem[i][0]]++; used++; }
  return out;
}
function fragThemes(w, frags) {
  const n = alloc(w, frags);
  const order = THEMES.filter(k => k !== 'star' && n[k]).sort((a, b) => w[b] - w[a] || THEMES.indexOf(a) - THEMES.indexOf(b)).concat(n.star ? ['star'] : []);
  const ks = order.slice(0, frags); if (!ks.length) return [];
  const fr = {}; let left = frags - ks.length; for (const k of ks) fr[k] = 1;
  const tot = ks.reduce((a, k) => a + n[k], 0) || 1; const rem = [];
  for (const k of ks) { const x = left * n[k] / tot; fr[k] += Math.floor(x); rem.push([k, x - Math.floor(x)]); }
  let used = ks.reduce((a, k) => a + fr[k], 0);
  rem.sort((a, b) => b[1] - a[1] || THEMES.indexOf(a[0]) - THEMES.indexOf(b[0]));
  for (let i = 0; used < frags && rem.length; i = (i + 1) % rem.length) { fr[rem[i][0]]++; used++; }
  const out = [];
  for (const k of ks) for (let i = 0; i < fr[k]; i++) out.push(k);
  return out;
}
function weightsOf(F, opt) {
  const lake = opt.ruleC ? ((F.feed ? 1 : 0) + (F.rinse ? 1 : 0) + (F.poop ? 1 : 0) + (F.mg ? 1 : 0)) : F.rinse;
  let toy = 0;
  if (opt.toy === 'ge1') toy = (F.play >= 1 || F.mg >= 1) ? Math.min(CFG.wMax, Math.max(1, F.play)) : 0;
  else if (opt.toy === 'min1') toy = Math.max(1, Math.min(CFG.wMax, F.play));
  else if (F.play >= CFG.playMany) toy = Math.min(CFG.wMax, F.play);
  const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, lake), toy, star: 1 };
  for (const k of THEMES) if (!(w[k] > 0)) delete w[k];
  return w;
}
function emptyF() { return { meal: 0, rinse: 0, play: 0, mg: 0, feed: 0, poop: 0 }; }
function addF(a, b) { for (const k of Object.keys(a)) a[k] += b[k] || 0; return a; }

function verifyCopy() {
  const s = S.newState(atHour(0, 9), 9); s.stage = 'adult';
  for (let i = 0; i < 3; i++) M6.note(s, 'food', 'meal', 0, 0, 0, atHour(0, 9));
  M6.note(s, 'care', 'rinse', 0, 0, 0, atHour(0, 9));
  const p = DR.plan(s, atHour(0, 22), 22);
  const F = { meal: 3, rinse: 1, play: 0, mg: 0, feed: 1, poop: 0 };
  const mine = fragThemes(weightsOf(F, { ruleC: false }), 6).slice().sort();
  const real = p.frags.map(f => f.th).slice().sort();
  if (JSON.stringify(mine) !== JSON.stringify(real)) {
    console.error('FRAG_COPY_MISMATCH', mine, real);
    process.exit(1);
  }
}
verifyCopy();

function summarize(name, rows) {
  const days = rows.map(r => r.day);
  const fin = days.filter(d => d != null);
  const cards = rows.map(r => r.cards);
  const dreams = rows.map(r => r.dreams);
  const live = rows.map(r => r.live);
  const makeup = rows.map(r => r.makeup);
  const dreamSum = dreams.reduce((a, b) => a + b, 0);
  const makeupSum = makeup.reduce((a, b) => a + b, 0);
  return {
    n: rows.length,
    done: fin.length,
    rate: +(fin.length / rows.length).toFixed(3),
    med: med(fin),
    p10: p10(fin),
    slow: fin.length ? Math.max(...fin) : null,
    cardsMed: med(cards),
    cardsMax: Math.max(...cards),
    dreamsMed: med(dreams),
    liveMed: med(live),
    makeupMed: med(makeup),
    makeupShare: dreamSum ? +(makeupSum / dreamSum).toFixed(3) : 0,
    lastCardMean: (() => { const g = rows.map(r => r.lastCard).filter(x => x != null); return g.length ? +(g.reduce((a, b) => a + b, 0) / g.length).toFixed(2) : null; })(),
    lastWasteMean: (() => { const g = rows.filter(r => r.day != null).map(r => r.wasteLast); return g.length ? +(g.reduce((a, b) => a + b, 0) / g.length).toFixed(2) : null; })(),
    wasteMean: (() => { const g = rows.map(r => r.waste); return +(g.reduce((a, b) => a + b, 0) / g.length).toFixed(2); })(),
    wallet: rows.reduce((a, r) => a + r.wallet, 0),
  };
}
function weightedTheme(w, rng) {
  const ks = THEMES.filter(k => w[k] > 0);
  let tot = ks.reduce((a, k) => a + w[k], 0), u = rng() * tot;
  for (const k of ks) { u -= w[k]; if (u <= 0) return k; }
  return ks[ks.length - 1];
}

function one(name, seed, opt) {
  const sc = SCHED[name];
  const rng = S.makeRng(seed * 7919 + 13);
  const rngMg = S.makeRng(seed * 7919 + 97);
  const s = S.newState(T0 + 8 * 3600e3, seed);
  s.stage = 'adult'; s.form = 'dust'; s.sleeping = true;
  const w0 = X.st(s).wallet.total;
  const events = []; // {t, h, f}
  for (let d = 0; d < MAXD; d++) {
    if (sc.everyOtherDay && (d + (seed & 1)) % 2) continue;
    const slots = [];
    for (const h0 of sc.hours) {
      if (rng() < MISS) continue;
      const jit = Math.round((rng() * 2 - 1) * JIT);
      const t = dayStart(d) + (h0 * 60 + jit) * 60e3;
      slots.push({ t, h: new Date(t).getHours() + new Date(t).getMinutes() / 60 });
    }
    slots.sort((a, b) => a.t - b.t);
    for (const slot of slots) {
      const acts = sc.acts.filter(() => rng() >= SKIP_ACT);
      if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
      const f = emptyF();
      for (const a of acts) {
        if (a === 'feed') { f.meal++; f.feed = 1; M6.note(s, 'food', 'meal', 0, 0, 0, slot.t); }
        else if (a === 'play') { f.play++; M6.note(s, 'care', 'play', 0, 0, 0, slot.t); }
        else if (a === 'rinse') { f.rinse++; M6.note(s, 'care', 'rinse', 0, 0, 0, slot.t); }
        else f.poop = 1;
      }
      if (MG_AT[name].includes(Math.floor(slot.h)) && rngMg() >= SKIP_ACT) {
        f.mg++; f.play++; M6.note(s, 'care', 'mg', 0, 0, 0, slot.t);
      }
      events.push({ t: slot.t, h: slot.h, f });
    }
  }
  const fragsN = opt.frags == null ? CFG.frags : opt.frags;
  const bankCap = opt.bankCap || 0;
  const afterHour = opt.afterHour; // null = 關閉 A 的 19:00 規則
  const rngRoll = S.makeRng(seed * 7919 + 887);
  let dreams = 0, live = 0, makeup = 0, doneDay = null, cards = 0, snap = null, day19 = null, waste = 0, wasteLast = 0;
  const bank = [];
  function grab(F, t, kind) {
    let themes;
    if (opt.roll) {
      const open = () => {
        const w = weightsOf(F, opt);
        if (opt.skipFull) for (const k of THEMES) if (DR.themeCards(s, k).length >= CFG.cardsPerTheme) delete w[k];
        return w;
      };
      const w0 = open();
      themes = [];
      if (Object.keys(w0).length) {
        const n = 1 + (rngRoll() < opt.roll.p2 ? 1 : 0);
        for (let i = 0; i < n; i++) {
          const w = open();
          if (!Object.keys(w).length) break;
          themes.push(weightedTheme(w, rngRoll));
        }
      }
    } else {
      themes = fragThemes(weightsOf(F, opt), fragsN);
      if (opt.lakeCap != null) {
        let n = 0; const cut = [];
        for (const th of themes) { if (th === 'lake' && n >= opt.lakeCap) continue; if (th === 'lake') n++; cut.push(th); }
        themes = cut;
      }
    }
    const before = X.st(s).wallet.total;
    const dayNum = Math.floor((t - T0) / DAY) + 1;
    for (const th of themes) {
      const full = DR.themeCards(s, th).length >= CFG.cardsPerTheme;
      const at19 = DR.summary(s, t, new Date(t).getHours()).cards === 19;
      if (full) { waste++; if (at19) wasteLast++; }
      DR.pick(s, th, t);
    }
    if (X.st(s).wallet.total !== before) throw new Error('wallet changed');
    if (!themes.length) return;
    dreams++; if (kind === 'live') live++; else makeup++;
    cards = DR.summary(s, t, new Date(t).getHours()).cards;
    if (day19 == null && cards >= 19) day19 = dayNum;
    if (doneDay == null && cards >= 20) {
      doneDay = dayNum;
      snap = { dreams, live, makeup };
    }
  }
  function factsUntil(t, nightIndex) {
    const F = emptyF();
    const end = atHour(nightIndex + 1, 3);
    for (const e of events) {
      if (e.t > t || e.t >= end) continue;
      const dk = M6.dayKey(e.t);
      const nk = M6.dayKey(atHour(nightIndex, 21));
      const next = M6.dayKey(atHour(nightIndex + 1, 1));
      if (dk === nk || dk === next) addF(F, e.f);
    }
    return F;
  }
  for (let d = 0; d < MAXD; d++) {
    const win0 = atHour(d, 21), win1 = atHour(d + 1, 3), a0 = atHour(d, afterHour == null ? 21 : afterHour);
    const qual = events.filter(e => e.t >= a0 && e.t < win1 && (afterHour == null ? e.t >= win0 : true));
    const inWin = events.some(e => e.t >= win0 && e.t < win1);
    const okLive = afterHour == null ? inWin : (inWin || qual.length > 0);
    // 補做：呢晚窗開始之前、上一次結算之後嘅第一個上線
    const firstAfterPrev = events.find(e => e.t >= atHour(d, 3) && e.t < win0);
    if (firstAfterPrev && bank.length) {
      const queued = bank.splice(0, bank.length);
      for (const b of queued) grab(b.F, firstAfterPrev.t, 'makeup');
    }
    if (okLive) {
      const pool = afterHour == null ? events.filter(e => e.t >= win0 && e.t < win1) : qual;
      const entry = afterHour == null ? pool[0] : pool[pool.length - 1];
      grab(factsUntil(entry.t, d), entry.t, 'live');
    } else if (bank.length < bankCap) {
      bank.push({ d, F: factsUntil(win1 - 1, d) });
    }
  }
  const till = snap || { dreams, live, makeup };
  const themesLeft = {};
  for (const k of THEMES) themesLeft[k] = DR.themeCards(s, k).length;
  return { day: doneDay, cards, dreams: till.dreams, live: till.live, makeup: till.makeup, lastCard: doneDay != null && day19 != null ? doneDay - day19 : null, waste, wasteLast, themes: themesLeft, wallet: X.st(s).wallet.total - w0 };
}

function run(opt) {
  const table = {};
  for (const name of Object.keys(SCHED)) {
    const rows = [];
    for (let i = 1; i <= N; i++) rows.push(one(name, i, opt));
    const row = summarize(name, rows);
    if (name === '疏玩') {
      const freq = {}, avg = {};
      for (const k of THEMES) avg[k] = 0;
      let unfinished = 0;
      for (const r of rows) {
        for (const k of THEMES) avg[k] += r.themes[k];
        if (r.cards >= 20) continue;
        unfinished++;
        let min = 99, ks = [];
        for (const k of THEMES) {
          if (r.themes[k] < min) { min = r.themes[k]; ks = [k]; }
          else if (r.themes[k] === min) ks.push(k);
        }
        const label = ks.join('+');
        freq[label] = (freq[label] || 0) + 1;
      }
      const top = Object.entries(freq).sort((a, b) => b[1] - a[1])[0] || [null, 0];
      for (const k of THEMES) avg[k] = +(avg[k] / rows.length).toFixed(2);
      row.stuck = { unfinished, top: top[0], topN: top[1], avg };
    }
    table[name] = row;
  }
  return table;
}

const schemes = [];
for (const p2 of [0.2, 0.3, 0.4]) {
  const tag = Math.round(p2 * 100);
  for (const fx of [
    { id: 'f1', toy: null, label: '修1' },
    { id: 'f1a', toy: 'ge1', label: '修1+修2a 玩或小遊戲≥1' },
    { id: 'f1b', toy: 'min1', label: '修1+修2b 玩具房最低 1' },
  ]) {
    schemes.push({ id: 'p' + tag + '-' + fx.id, label: 'p=' + tag + '% ' + fx.label, bankCap: 1, afterHour: 19, ruleC: true, skipFull: true, toy: fx.toy, roll: { p2 } });
  }
}

const only = process.env.SCHEME;
const list = only ? schemes.filter(s => s.id === only) : schemes;
const out = {
  base: '4f66a834',
  N, MAXD, seed: 'route-sweep seed*7919+13 / mg +97',
  miss: MISS, jitMin: JIT, skipAct: SKIP_ACT, extraAct: EXTRA_ACT,
  cap47: D.PARAMS.SHARD_DAILY_TOTAL_CAP,
  lv5xp: FAM.XP ? FAM.XP[4] : (FAM.THRESH && FAM.THRESH[4]),
  schemes: {},
};
for (const sc of list) {
  console.error('RUN', sc.id);
  out.schemes[sc.id] = { opt: sc, table: run(sc) };
  console.error(JSON.stringify(out.schemes[sc.id].table, null, 2));
}
if (!only) console.log(JSON.stringify(out, null, 2));
else console.log(JSON.stringify(out.schemes[only], null, 2));
