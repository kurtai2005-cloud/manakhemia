'use strict';
/* 6d.1：夢境六表（真 long6c.enter／pick），跟遊測 QA/sim-6c-dream.js 嘅上線模型（route-sweep SCHED、漏 15%、±90 分、跳動作 20%、加動作 30%、N 200、180 日）。
   每節上線：M6.note 入 6a；當晚最後一節（≥19:00 或 <03:00）→ 瞓緊，連續 DR.enter 到入唔到（有存低先補、再入當晚）；
   03:00–19:00 第一節 → canEnter 係 bank 就補做。入咗就拾晒 plan.frags。node tools/sim-6c-dream-real.js [N] */
const S = require('../src/sim.js'), M6 = require('../src/long6a.js'), DR = require('../src/long6c.js'), X = require('../src/systems.js'), D = require('../src/data.js');
const { SCHED, MG_AT } = require('./route-sweep.js');
const JIT = 90, MISS = 0.15, SKIP_ACT = 0.2, EXTRA_ACT = 0.3, ACTS = ['feed', 'play', 'rinse', 'poop'], MAXD = 180, DAY = 86400e3;
const N = +(process.argv[2] || process.env.N || 200), T0 = new Date(2026, 10, 2, 0, 0, 0).getTime();
const hr = (t) => { const d = new Date(t); return d.getHours() + d.getMinutes() / 60; };
function one(name, seed) {
  const sc = SCHED[name], rng = S.makeRng(seed * 7919 + 13), rngMg = S.makeRng(seed * 7919 + 97);
  const s = S.newState(T0 + 8 * 3600e3, seed); s.stage = 'adult'; s.form = 'dust'; s.sleeping = true; const w0 = X.st(s).wallet.total;
  const ev = [];
  for (let d = 0; d < MAXD; d++) { if (sc.everyOtherDay && (d + (seed & 1)) % 2) continue;
    for (const h0 of sc.hours) { if (rng() < MISS) continue; const t = T0 + d * DAY + (h0 * 60 + Math.round((rng() * 2 - 1) * JIT)) * 60e3; ev.push({ t }); } }
  ev.sort((a, b) => a.t - b.t);
  for (const e of ev) { const h = hr(e.t); e.h = h; e.nk = DR.nightKey(e.t, h); e.dk = DR.dayKey(e.t); e.late = h >= 19 || h < 3; }
  ev.forEach((e, i) => { e.lastLate = e.late && !ev.slice(i + 1).some(x => x.late && x.nk === e.nk); e.firstDay = !e.late && !ev.slice(0, i).some(x => !x.late && x.dk === e.dk); });
  let dreams = 0, bank = 0, done = null, waste = 0;
  const take = (r, t) => { dreams++; if (r.bank) bank++; for (const f of r.frags) { if (DR.themeCards(s, f.th).length >= DR.CFG.cardsPerTheme) waste++; DR.pick(s, f.th, t); } };
  for (const e of ev) {
    const acts = sc.acts.filter(() => rng() >= SKIP_ACT); if (rng() < EXTRA_ACT) acts.push(ACTS[Math.floor(rng() * ACTS.length)]);
    for (const a of acts) { if (a === 'feed') M6.note(s, 'food', 'meal', 0, 0, 0, e.t); else if (a === 'play') M6.note(s, 'care', 'play', 0, 0, 0, e.t); else if (a === 'rinse') M6.note(s, 'care', 'rinse', 0, 0, 0, e.t); else M6.note(s, 'care', 'poop', 0, 0, 0, e.t); }
    if (MG_AT[name].includes(Math.floor(e.h)) && rngMg() >= SKIP_ACT) M6.note(s, 'care', 'mg', 0, 0, 0, e.t);
    if (e.lastLate) { for (let k = 0; k < 3; k++) { const r = DR.enter(s, e.t + k * 60e3, e.h); if (!r.ok) break; take(r, e.t); } }
    else if (e.firstDay && DR.canEnter(s, e.t, e.h).why === 'bank') take(DR.enter(s, e.t, e.h), e.t);
    if (done == null && Object.keys(DR.st(s).cards).length >= 20) done = Math.floor((e.t - T0) / DAY) + 1;
  }
  return { day: done, cards: Object.keys(DR.st(s).cards).length, dreams, bank, waste, wallet: X.st(s).wallet.total - w0 };
}
const med = (a) => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : null; };
const p10 = (a) => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[Math.floor(b.length * 0.1)] : null; };
function run() { const out = {};
  for (const name of Object.keys(SCHED)) { const rows = []; for (let i = 1; i <= N; i++) rows.push(one(name, i)); const fin = rows.map(r => r.day).filter(d => d != null);
    out[name] = { done: fin.length, n: N, rate: +(fin.length / N).toFixed(3), med: med(fin), p10: p10(fin), slow: fin.length ? Math.max(...fin) : null, cardsMed: med(rows.map(r => r.cards)), dreamsMed: med(rows.map(r => r.dreams)), bankMed: med(rows.map(r => r.bank)), waste: rows.reduce((a, r) => a + r.waste, 0), wallet: rows.reduce((a, r) => a + r.wallet, 0) }; }
  return { N, MAXD, cap47: D.PARAMS.SHARD_DAILY_TOTAL_CAP, table: out }; }
module.exports = { one, run };
if (require.main === module) console.log(JSON.stringify(run(), null, 2));
