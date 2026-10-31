#!/usr/bin/env node
/* 對 PR #17 真 build（src/glimmer-a 的 events.js／sim.js）做驗收。
 * Round 2：離線按實時日補抽；日記事件唔經 listener，要由 offLog 計。
 * 唔改遊戲檔。用法：
 *   TZ=Asia/Hong_Kong node tests/pet/qa_glimmer_build.js \
 *     --src /path/to/src/glimmer-a --days 3000 --seeds 7,3,5,11,13,17,19,23 \
 *     --json tests/pet/out/glimmer_build.json --whatif 0
 */
'use strict';
const fs = require('fs');
const path = require('path');

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 ? process.argv[i + 1] : dflt;
}
const SRC = path.resolve(arg('src', process.env.GLIMMER_SRC || '/tmp/glimmer-a/src/glimmer-a'));
const DAYS = +arg('days', '3000');
const SEEDS = String(arg('seeds', '7,3,5,11,13,17,19,23')).split(',').map(s => +s);
const JSON_OUT = arg('json', '');
const WHATIF = arg('whatif', '1') !== '0';

const D = require(path.join(SRC, 'src/data.js'));
const SIM = require(path.join(SRC, 'src/sim.js'));
const EV = require(path.join(SRC, 'src/events.js'));
const P = D.PARAMS.events;
const H = 3600;
const DAYMS = 86400000;

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function pad(n) { return String(n).padStart(2, '0'); }
function dateKey(ms) {
  const d = new Date(ms);
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
}
function adult(seed, now) {
  const s = SIM.newState(now, seed);
  s.stage = 'adult'; s.form = 'soft';
  s.needs = { hunger: 90, mood: 90, clean: 90, energy: 90 };
  s.lastSeen = now; s.lastSaveTime = now; s.poops = 0; s.sleeping = false;
  return s;
}
function cdNeedSec(id) {
  const def = D.EVENTS.find(e => e.id === id);
  return (def.cooldownH || (def.rare ? P.cooldownRareH : P.cooldownH)) * H;
}
const RARE_POP = { meteor: 1, rainbow: 1 };

const PROFILES = [
  { id: 'diligent', name: '勤力 6次/日', times: [8, 10.5, 13, 16.5, 19.5, 22.5], miss: 0.05, opens: 6 },
  { id: 'normal', name: '一般 4次/日', times: [8, 12.5, 18.5, 22], miss: 0.10, opens: 4 },
  { id: 'office', name: '上班族 3次/日', times: [7.5, 19, 22.5], miss: 0.10, opens: 3 },
  { id: 'light', name: '輕度 2次/日', times: [8.5, 21.5], miss: 0.15, opens: 2 },
  { id: 'early', name: '早鳥朝午', times: [7.5, 12.5], miss: 0.10, opens: 2 },
  { id: 'eod', name: '隔日 1次', times: [20], miss: 0, everyOther: true, opens: 1 },
];

function makeSessions(profile, days, rng, base) {
  const out = [];
  for (let d = 0; d < days; d++) {
    if (profile.everyOther && (d % 2)) continue;
    for (const h of profile.times) {
      if (rng() < profile.miss) continue;
      out.push(base + d * DAYMS + (h + (rng() * 0.8 - 0.4)) * 3600000);
    }
  }
  out.sort((a, b) => a - b);
  return out;
}
function care(s, rng) {
  for (const k of ['hunger', 'mood', 'clean', 'energy']) {
    if (rng() < 0.85) s.needs[k] = 80 + rng() * 20;
  }
  if (rng() < 0.85) s.poops = 0;
  s.sleeping = false;
}
function freshBucket() {
  return {
    pool: 0, grumpy: 0, guar: 0, flash: 0, other: 0, n: 0,
    eveN: 0, eve: {}, rainbow: 0, fireflyOut: 0,
    openDates: new Set(), seenDay: {}, shinySeen: new Set(), shinyEval: 0, shinyYes: 0,
    lastAt: {}, minSame: {}, prevAt: null, prevId: null, minGap: Infinity,
    cdViol: 0, gapViol: 0, cdByKind: {}, cdById: {}, cdSamples: [], gapSamples: [],
    pity: 0, lastRbTs: 0, rainbowMaxGapD: 0, lastFlashTs: 0, flashWallViol: 0, flashMinGapH: Infinity,
    returns: 0, maxPop: 0, popOver: 0, rareViol: 0, rareSamples: [],
    diaryNew: 0, popN: 0, rollbacks: 0,
    curDay: '', skipListen: false,
    onlineDrawByDay: {},
  };
}
function score(bucket, r) {
    const id = r.id, isFlash = id === 'flash', isGrumpy = id === 'grumpy';
    const isGuar = r.kind === 'guarantee' && !isFlash;
    const isPity = r.kind === 'pity';
    const isPool = (r.kind === 'draw' || isPity) && !isGrumpy && !isFlash;
    if (isPool) bucket.pool++;
    else if (isGrumpy) bucket.grumpy++;
    else if (isGuar) bucket.guar++;
    else if (isFlash) bucket.flash++;
    else bucket.other++;
    if (!isFlash) bucket.seenDay[bucket.curDay] = (bucket.seenDay[bucket.curDay] || 0) + 1;
    if (!isFlash && r.hour != null && r.hour >= 17 && r.hour < 23) {
      bucket.eveN++; bucket.eve[id] = (bucket.eve[id] || 0) + 1;
    }
    if (isPity) bucket.pity++;
    if (id === 'rainbow') {
      bucket.rainbow++;
      if (r.ts) {
        if (bucket.lastRbTs) bucket.rainbowMaxGapD = Math.max(bucket.rainbowMaxGapD, (r.ts - bucket.lastRbTs) / 86400000);
        bucket.lastRbTs = r.ts;
      }
    }
    if (isFlash && r.ts) {
      if (bucket.lastFlashTs) {
        const gapH = (r.ts - bucket.lastFlashTs) / 3600000;
        if (gapH < (P.flashCooldownH || 72) - 0.02) bucket.flashWallViol++;
        if (gapH < bucket.flashMinGapH) bucket.flashMinGapH = gapH;
      }
      bucket.lastFlashTs = r.ts;
    }
    if (id === 'firefly_walk' && r.hour != null && !(r.hour >= 17 && r.hour < 23)) bucket.fireflyOut++;
    const need = cdNeedSec(id);
    if (bucket.lastAt[id] != null) {
      const dlt = r.at - bucket.lastAt[id];
      if (dlt < need - 0.5) {
        bucket.cdViol++;
        bucket.cdByKind[r.kind] = (bucket.cdByKind[r.kind] || 0) + 1;
        bucket.cdById[id] = (bucket.cdById[id] || 0) + 1;
        if (bucket.cdSamples.length < 6) bucket.cdSamples.push({ id, kind: r.kind, gapH: +(dlt / H).toFixed(3), needH: need / H });
      }
      if (bucket.minSame[id] == null || dlt < bucket.minSame[id]) bucket.minSame[id] = dlt;
    }
    bucket.lastAt[id] = r.at;
    if (bucket.prevAt != null) {
      const g = r.at - bucket.prevAt;
      if (g < P.minGapSec - 0.5) {
        bucket.gapViol++;
        if (bucket.gapSamples.length < 6) bucket.gapSamples.push({ id, kind: r.kind, prev: bucket.prevId, gapMin: +(g / 60).toFixed(2) });
      }
      if (g < bucket.minGap) bucket.minGap = g;
    }
    bucket.prevAt = r.at; bucket.prevId = id; bucket.n++;
    if (!r.offline && r.kind === 'draw' && !isFlash && !isGrumpy) {
      bucket.onlineDrawByDay[bucket.curDay] = (bucket.onlineDrawByDay[bucket.curDay] || 0) + 1;
    }
}
function rareFirstOk(offLog) {
  const all = (offLog || []).filter(x => x && x.offline);
  if (!all.length) return { ok: true, pops: 0, expect: [], got: [] };
  const rank = (x) => x.id === 'flash' ? 2 : (RARE_POP[x.id] ? 1 : 0);
  const expect = all.slice().sort((a, b) => (rank(b) - rank(a)) || ((b.ts || 0) - (a.ts || 0)) || (b.at - a.at)).slice(0, Math.min(P.offlinePopupMax, all.length));
  const pops = all.filter(x => !x.diary);
  const key = (x) => x.id + '@' + x.ts + '@' + x.at;
  const set = new Set(pops.map(key));
  return { ok: pops.length <= P.offlinePopupMax && expect.every(e => set.has(key(e))), pops: pops.length, expect: expect.map(e => e.id), got: pops.map(e => e.id) };
}
function attach(s, bucket) {
  const fn = (st, r) => { if (st !== s || bucket.skipListen) return; score(bucket, r); };
  EV.listeners.push(fn);
  return () => { const i = EV.listeners.indexOf(fn); if (i >= 0) EV.listeners.splice(i, 1); };
}
function noteReturn(rep, bucket, offLog) {
  const ev = (rep && rep.events) || [];
  if (!ev.length && !(offLog && offLog.length)) return;
  bucket.returns++;
  const rf = rareFirstOk(offLog);
  if (rf.pops > bucket.maxPop) bucket.maxPop = rf.pops;
  if (rf.pops > 2) bucket.popOver++;
  if (!rf.ok) {
    bucket.rareViol++;
    if (bucket.rareSamples.length < 5) bucket.rareSamples.push({ expect: rf.expect, got: rf.got });
  }
  bucket.diaryNew += ev.filter(e => e.diary).length;
  bucket.popN += rf.pops;
}
function runProfile(profile, days, seed, base) {
  const rngS = mulberry32(seed * 1000 + profile.times.length * 17 + (profile.everyOther ? 9 : 0));
  const rngC = mulberry32(seed * 777 + 13);
  const sess = makeSessions(profile, days, rngS, base);
  const s = adult(seed, base);
  const bucket = freshBucket();
  const off = attach(s, bucket);
  try {
    for (const now of sess) {
      bucket.curDay = dateKey(now);
      bucket.openDates.add(bucket.curDay);
      bucket.skipListen = true;
      const rep = SIM.applyOffline(s, now);
      bucket.skipListen = false;
      const offLog = (s.evs && s.evs.offLog) ? s.evs.offLog.slice().sort((a, b) => a.at - b.at) : [];
      for (const rec of offLog) score(bucket, rec);
      noteReturn(rep, bucket, offLog);
      if (s.evs && s.evs.diary.length && rngC() < 0.70) EV.claim(s);
      care(s, rngC);
      EV.noteOpen(s, { hour: SIM.hourOf(now), now });
      if (!bucket.shinySeen.has(bucket.curDay)) {
        bucket.shinySeen.add(bucket.curDay); bucket.shinyEval++;
        if (s.evs && s.evs.flashToday) bucket.shinyYes++;
      }
      SIM.advance(s, 180, { hour: SIM.hourOf(now + 90000), now: now + 180000 }, 30);
      s.lastSeen = now + 180000;
      EV.markSave(s, s.lastSeen);
      if (s.evs) bucket.rollbacks = s.evs.stats.rollbacks || 0;
    }
  } finally { off(); }
  const active = bucket.openDates.size;
  let zero = 0;
  for (const d of bucket.openDates) if (!bucket.seenDay[d]) zero++;
  const totalEv = bucket.pool + bucket.grumpy + bucket.guar;
  const eveShare = {};
  for (const k of Object.keys(bucket.eve)) eveShare[k] = bucket.eveN ? +(100 * bucket.eve[k] / bucket.eveN).toFixed(2) : 0;
  const minSameH = {};
  for (const k of Object.keys(bucket.minSame)) minSameH[k] = +(bucket.minSame[k] / H).toFixed(2);
  return {
    profile: profile.id, name: profile.name, seed, days, activeDays: active,
    poolPerDay: +(bucket.pool / days).toFixed(4),
    grumpyPerDay: +(bucket.grumpy / days).toFixed(4),
    guarPerDay: +(bucket.guar / days).toFixed(4),
    totalPerDay: +(totalEv / days).toFixed(4),
    flashPerDay: +(bucket.flash / days).toFixed(4),
    zeroActivePct: active ? +(100 * zero / active).toFixed(3) : 0,
    zeroLimit: (profile.opens >= 3 || profile.everyOther) ? 1 : 3,
    rainbowEveryDays: bucket.rainbow ? +(days / bucket.rainbow).toFixed(2) : null,
    rainbowN: bucket.rainbow,
    rainbowMaxGapD: +bucket.rainbowMaxGapD.toFixed(3),
    pity: bucket.pity,
    flashWallViol: bucket.flashWallViol,
    flashMinGapH: bucket.flashMinGapH === Infinity ? null : +bucket.flashMinGapH.toFixed(3),
    fireflyOutOfWindow: bucket.fireflyOut,
    eveningN: bucket.eveN,
    eveningSharePct: eveShare,
    eveningCounts: bucket.eve,
    cdViol: bucket.cdViol, cdByKind: bucket.cdByKind, cdById: bucket.cdById, gapViol: bucket.gapViol,
    cdSamples: bucket.cdSamples, gapSamples: bucket.gapSamples,
    minGapMin: bucket.minGap === Infinity ? null : +(bucket.minGap / 60).toFixed(2),
    minSameH,
    maxPop: bucket.maxPop, popOver: bucket.popOver, rareViol: bucket.rareViol, rareSamples: bucket.rareSamples,
    shinyPct: bucket.shinyEval ? +(100 * bucket.shinyYes / bucket.shinyEval).toFixed(3) : 0,
    shinyEval: bucket.shinyEval, shinyYes: bucket.shinyYes,
    rollbacks: bucket.rollbacks,
    sessions: sess.length,
    maxOnlineDraws: Math.max(0, ...Object.values(bucket.onlineDrawByDay)),
  };
}

function snapEvents() {
  return D.EVENTS.map(e => ({ id: e.id, weight: e.weight, hours: e.hours ? e.hours.slice() : null, moodAtLeast: e.moodAtLeast, energyAtLeast: e.energyAtLeast }));
}
function restoreEvents(snap) {
  for (const s of snap) {
    const e = D.EVENTS.find(x => x.id === s.id);
    e.weight = s.weight;
    e.hours = s.hours ? s.hours.slice() : null;
    if (s.moodAtLeast == null) delete e.moodAtLeast; else e.moodAtLeast = s.moodAtLeast;
    if (s.energyAtLeast == null) delete e.energyAtLeast; else e.energyAtLeast = s.energyAtLeast;
  }
}
function applyV51Weights() {
  const w = { gift: 22, butterfly: 20, meteor: 10, rainbow: 4, firefly_walk: 20, sleeptalk: 11, treasure: 18, grumpy: 3 };
  const hours = { gift: [7, 23], butterfly: [7, 17], meteor: [19, 5], rainbow: [17, 23], firefly_walk: [17, 23], sleeptalk: [23, 7], treasure: [8, 22] };
  for (const e of D.EVENTS) {
    if (w[e.id] != null) e.weight = w[e.id];
    if (hours[e.id]) e.hours = hours[e.id].slice();
  }
}
function theoreticalEvening() {
  const acc = {}, hourShare = [];
  let tot = 0;
  for (let h = 17; h < 23; h++) {
    let sub = 0; const row = {};
    for (const e of D.EVENTS) {
      if (e.special || e.lowNeed || !e.weight) continue;
      if (e.hours && !EV.inHours(h + 0.5, e.hours[0], e.hours[1])) continue;
      row[e.id] = e.weight; sub += e.weight; acc[e.id] = (acc[e.id] || 0) + e.weight;
    }
    tot += sub;
    const ff = row.firefly_walk || 0;
    hourShare.push({ hour: h, fireflyPct: sub ? +(100 * ff / sub).toFixed(1) : 0, weights: row });
  }
  const share = {};
  for (const k of Object.keys(acc)) share[k] = tot ? +(100 * acc[k] / tot).toFixed(2) : 0;
  return { byHour: hourShare, sharePct: share };
}

function absenceTrial(nDays, seed, base) {
  const prof = PROFILES[1];
  const rngS = mulberry32(seed + nDays * 17);
  const rngC = mulberry32(seed + 99 + nDays);
  const s = adult(seed, base);
  const warm = makeSessions(prof, 14, rngS, base);
  for (const now of warm) {
    SIM.applyOffline(s, now);
    if (s.evs && s.evs.diary.length && rngC() < 0.70) EV.claim(s);
    care(s, rngC);
    EV.noteOpen(s, { hour: SIM.hourOf(now), now });
    SIM.advance(s, 180, { hour: SIM.hourOf(now), now: now + 180000 }, 30);
    s.lastSeen = now + 180000; EV.markSave(s, s.lastSeen);
  }
  const back = base + (14 + nDays) * DAYMS + 8.5 * 3600000;
  const diaryBefore = s.evs ? s.evs.diary.length : 0;
  const rep = SIM.applyOffline(s, back);
  const ev = rep.events || [];
  const pops = ev.filter(e => !e.diary);
  const diary = ev.filter(e => e.diary);
  const rf = rareFirstOk(s.evs && s.evs.offLog);
  const tsSet = {};
  (s.evs ? s.evs.diary : []).forEach(d => { tsSet[d.ts] = (tsSet[d.ts] || 0) + 1; });
  const ages = (s.evs ? s.evs.diary : []).map(d => d.ts ? (back - d.ts) / DAYMS : null);
  return {
    nDays, gen: ev.length, popups: pops.length, diaryNew: diary.length,
    diaryTotal: s.evs ? s.evs.diary.length : 0, diaryBefore,
    maxPopOk: pops.length <= 2,
    rareViol: !rf.ok,
    rareExpect: rf.expect, rareGot: rf.got,
    order: ev.map(e => e.id + (e.diary ? '/d' : '/p')),
    gift: rep.gift, tampered: !!rep.tampered, EHours: +(rep.E / H).toFixed(2), THours: +(rep.T / H).toFixed(2),
    diaryTsUnique: Object.keys(tsSet).length,
    diaryTsAllEqualReturn: Object.keys(tsSet).length === 1 && +Object.keys(tsSet)[0] === back,
    diaryAgeDaysMax: ages.length ? +Math.max(...ages.filter(a => a != null)).toFixed(3) : 0,
    offLogCap: ev.length >= P.offlineMaxEvents,
  };
}

function clockCases(base) {
  const rows = [];
  function fresh(now) {
    const s = adult(7, now);
    EV.ensure(s);
    s.evs.dayIdx = null;
    return s;
  }
  function probe(label, setup) {
    const now = base + 20 * DAYMS + 15 * H * 1000;
    const s = fresh(now);
    const grains0 = s.grains;
    const r = setup(s, now);
    rows.push(Object.assign({ id: label }, r, { grainsDelta: s.grains - grains0 }));
  }
  // 回撥容差：直接 noteOpen（同 boot 路徑）
  for (const [id, back, expectTamper] of [['CG-18', 119000, false], ['CG-19', 120000, false], ['CG-21', 121000, true]]) {
    probe(id + ' 回撥 ' + (back / 1000) + 's', (s, now) => {
      s.lastSaveTime = now; s.lastSeen = now;
      const rolled = now - back;
      EV.noteOpen(s, { hour: SIM.hourOf(rolled), now: rolled });
      const sup = EV.suppressed(s, s.evs);
      return {
        expect: expectTamper ? '篡改、lastSaveTime 唔變、suppressed' : '唔篡改',
        pass: sup === expectTamper && s.lastSaveTime === now && (s.evs.stats.rollbacks || 0) === (expectTamper ? 1 : 0),
        sup, lastSaveTimeDeltaMs: s.lastSaveTime - now, rollbacks: s.evs.stats.rollbacks || 0, noDrawDay: s.evs.noDrawDay,
      };
    });
  }
  // 回撥之後追回同一 UTC 日：121s 當日仍然唔抽；119／120 可以抽
  const savedChance = P.drawChance, savedEvery = P.drawEveryH.slice();
  P.drawChance = 1; P.drawEveryH = [0.05, 0.05];
  try {
    for (const [id, back, expectBlock] of [['CG-18b', 119000, false], ['CG-19b', 120000, false], ['CG-21b', 121000, true]]) {
      probe(id + ' 追回後當日抽唔抽', (s, now) => {
        s.lastSaveTime = now; s.lastSeen = now;
        EV.noteOpen(s, { hour: 12, now: now - back });
        const later = now + 6 * H * 1000;
        const recs = [];
        const fn = (st, r) => { if (st === s) recs.push(r.id); };
        EV.listeners.push(fn);
        s.lastSeen = later - 5 * H * 1000;
        SIM.applyOffline(s, later);
        EV.noteOpen(s, { hour: SIM.hourOf(later), now: later });
        SIM.advance(s, 3 * H, { hour: SIM.hourOf(later), now: later }, 60);
        EV.listeners.splice(EV.listeners.indexOf(fn), 1);
        const blocked = recs.length === 0;
        return {
          expect: expectBlock ? '當日 0 事件' : '當日有事件',
          pass: blocked === expectBlock,
          events: recs.length, sup: EV.suppressed(s, s.evs), sample: recs.slice(0, 6),
        };
      });
    }
  } finally { P.drawChance = savedChance; P.drawEveryH = savedEvery; }

  probe('CG-15 lastSaveTime=now+23h59m', (s, now) => {
    const ahead = 23 * H * 1000 + 59 * 60 * 1000;
    s.lastSaveTime = now + ahead; s.lastSeen = now + ahead;
    const rep = SIM.applyOffline(s, now);
    EV.noteOpen(s, { hour: SIM.hourOf(now), now });
    const reset = (s.saveTimeResets || 0) > 0;
    return {
      expect: '仍有效＝判篡改、唔重設、該次唔派離線獎',
      pass: !reset && !rep.tampered && s.lastSaveTime === now + ahead && EV.suppressed(s, s.evs) && rep.gift === 0 && rep.T === 0,
      reset, tampered: rep.tampered, sup: EV.suppressed(s, s.evs), gift: rep.gift, T: rep.T,
      lastSaveUnchanged: s.lastSaveTime === now + ahead,
    };
  });
  probe('CG-16 lastSaveTime=now+24h00m00s', (s, now) => {
    const ahead = 24 * H * 1000;
    s.lastSaveTime = now + ahead; s.lastSeen = now + ahead;
    const rep = SIM.applyOffline(s, now);
    EV.noteOpen(s, { hour: 12, now });
    const reset = (s.saveTimeResets || 0) > 0;
    return {
      expect: '剛好 24h 仍然有效＝篡改、唔重設',
      pass: !reset && s.lastSaveTime === now + ahead && EV.suppressed(s, s.evs),
      reset, sup: EV.suppressed(s, s.evs), tampered: rep.tampered,
    };
  });
  probe('CG-17 lastSaveTime=now+24h00m10s', (s, now) => {
    const ahead = 24 * H * 1000 + 10000;
    s.lastSaveTime = now + ahead; s.lastSeen = now - 10 * H * 1000; s.grains = 0;
    const rep = SIM.applyOffline(s, now);
    const grainsAfterOffline = s.grains;
    const rec = EV.noteOpen(s, { hour: 12, now });
    return {
      expect: '無效→重設為 now、離線段 T=0 唔派離線獎、唔再鎖',
      pass: !!rep.tampered && s.lastSaveTime === now && s.lastSeen === now && rep.gift === 0 && rep.T === 0 && grainsAfterOffline === 0 && !EV.suppressed(s, s.evs) && s.grains === 0 && !rec,
      tampered: rep.tampered, gift: rep.gift, T: rep.T, grainsAfterOffline, grainsAfterNoteOpen: s.grains,
      noteOpenEvent: rec && rec.id, sup: EV.suppressed(s, s.evs),
      lastSaveIsNow: s.lastSaveTime === now, resets: s.saveTimeResets || 0,
    };
  });
  probe('CG-08 lastSaveTime=now+25h', (s, now) => {
    s.lastSaveTime = now + 25 * H * 1000; s.lastSeen = now - 10 * H * 1000; s.grains = 0;
    const rep = SIM.applyOffline(s, now);
    const grainsAfterOffline = s.grains;
    const rec = EV.noteOpen(s, { hour: 12, now });
    const grainsAfterNote = s.grains;
    const later = now + 8 * H * 1000;
    s.lastSeen = now; EV.markSave(s, now);
    const rep2 = SIM.applyOffline(s, later);
    EV.noteOpen(s, { hour: SIM.hourOf(later), now: later });
    return {
      expect: '+25h 無效重設、10h 缺口唔派離線獎；下一次開 app 唔再被鎖',
      pass: !!rep.tampered && rep.gift === 0 && rep.T === 0 && grainsAfterOffline === 0 && grainsAfterNote === 0 && !rec && !EV.suppressed(s, s.evs) && !rep2.tampered && rep2.T > 7 * H,
      tampered: rep.tampered, gift: rep.gift, T: rep.T, grainsAfterOffline, grainsAfterNote, noteOpenEvent: rec && rec.id,
      supAfter: EV.suppressed(s, s.evs), nextTampered: rep2.tampered, nextTh: +(rep2.T / H).toFixed(2),
    };
  });

  // DST／時區：UTC 前進就算牆鐘倒退都唔篡改
  function wall(ms, tz) {
    return new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(ms));
  }
  probe('CG-10 DST 秋季回撥（美東）', (s, now) => {
    const edt = Date.parse('2026-11-01T05:30:00Z'); // 01:30 EDT
    const est = Date.parse('2026-11-01T06:10:00Z'); // 01:10 EST
    s.lastSaveTime = edt; s.lastSeen = edt;
    const rep = SIM.applyOffline(s, est);
    EV.noteOpen(s, { hour: 1.17, now: est });
    return {
      expect: 'UTC 05:30→06:10 唔篡改（牆鐘 01:30→01:10 會誤判）',
      pass: !EV.suppressed(s, s.evs) && (s.evs.stats.rollbacks || 0) === 0 && !rep.tampered,
      sup: EV.suppressed(s, s.evs), rollbacks: s.evs.stats.rollbacks || 0,
      wallEDT: wall(edt, 'America/New_York'), wallEST: wall(est, 'America/New_York'),
      utcDeltaMin: (est - edt) / 60000,
    };
  });
  probe('CG-11 DST 春季前撥（美東）', (s, now) => {
    const a = Date.parse('2026-03-08T06:30:00Z'); // 01:30 EST
    const b = Date.parse('2026-03-08T07:30:00Z'); // 03:30 EDT
    s.lastSaveTime = a; s.lastSeen = a;
    SIM.applyOffline(s, b);
    EV.noteOpen(s, { hour: 3.5, now: b });
    return {
      expect: 'UTC 正常前進，唔篡改',
      pass: !EV.suppressed(s, s.evs) && (s.evs.stats.rollbacks || 0) === 0,
      sup: EV.suppressed(s, s.evs),
      wallA: wall(a, 'America/New_York'), wallB: wall(b, 'America/New_York'),
    };
  });
  probe('CG-09 時區 HKT→UTC−8（UTC 只 +60s）', (s, now) => {
    const t0 = Date.parse('2026-06-15T02:00:00Z'); // HKT 10:00；LA 前日 19:00
    const t1 = t0 + 60000;
    s.lastSaveTime = t0; s.lastSeen = t0;
    SIM.applyOffline(s, t1);
    EV.noteOpen(s, { hour: 19, now: t1 });
    return {
      expect: 'UTC 前進 60s 唔篡改；牆鐘由 10:00 變 19:00（前日）亦唔判',
      pass: !EV.suppressed(s, s.evs) && (s.evs.stats.rollbacks || 0) === 0,
      sup: EV.suppressed(s, s.evs),
      wallHKT: wall(t0, 'Asia/Hong_Kong'), wallLA: wall(t1, 'America/Los_Angeles'),
    };
  });
  probe('CG-12 NTP 回撥 30s', (s, now) => {
    s.lastSaveTime = now; s.lastSeen = now;
    EV.noteOpen(s, { hour: 12, now: now - 30000 });
    return {
      expect: '30s 唔篡改',
      pass: !EV.suppressed(s, s.evs) && (s.evs.stats.rollbacks || 0) === 0 && s.lastSaveTime === now,
      sup: EV.suppressed(s, s.evs),
    };
  });
  return rows;
}

function diaryCases(base) {
  const rows = [];
  const s = adult(7, base);
  EV.ensure(s);
  const E = s.evs;
  for (let i = 0; i < 25; i++) E.diary.push({ id: 'firefly_walk', ts: base - i * H * 1000, flavor: 'x', grains: 5, mood: 10 });
  const beforeMood = s.needs.mood;
  const c1 = EV.claim(s);
  rows.push({
    id: 'FF-12/13 日記螢火 ×25',
    pass: c1.grains === 60 && c1.n === 20 && c1.mood === 0 && E.diary.length === 5 && s.needs.mood === beforeMood,
    got: c1, left: E.diary.length, mood: s.needs.mood,
  });
  const c2 = EV.claim(s);
  rows.push({ id: 'FF-12 餘 5 條', pass: c2.grains === 15 && c2.n === 5 && E.diary.length === 0, got: c2 });

  const s2 = adult(7, base);
  EV.ensure(s2);
  s2.evs.diary.push({ id: 'gift', ts: base - 11.99 * DAYMS, flavor: 'a' });
  s2.evs.diary.push({ id: 'gift', ts: base - 12 * DAYMS, flavor: 'b' });
  s2.evs.diary.push({ id: 'gift', ts: base - 13.2 * DAYMS, flavor: 'c' });
  const warn = EV.diaryWarn(s2, base);
  rows.push({ id: 'DT 第12日起提示條數', pass: warn === 2, warn, note: 'API 只回條數，文案唔分「2 日後／1 日後」' });
  const gone = EV.pruneDiary(s2, base);
  rows.push({ id: 'DY 14.0 日保留、超過先刪', pass: gone === 0 && s2.evs.diary.length === 3, gone, left: s2.evs.diary.length });
  s2.evs.diary.push({ id: 'gift', ts: base - (14 * DAYMS + 0.01 * H * 1000), flavor: 'old' });
  const gone2 = EV.pruneDiary(s2, base);
  rows.push({ id: 'DY 14日+0.01h 作廢', pass: gone2 === 1, gone: gone2 });

  // 損毀
  const crashes = [];
  function tryBoot(label, mutate) {
    const st = adult(3, base);
    EV.ensure(st);
    mutate(st.evs);
    try { EV.noteOpen(st, { hour: 12, now: base }); crashes.push({ label, threw: false }); }
    catch (e) { crashes.push({ label, threw: true, error: String(e.message || e) }); }
  }
  tryBoot('diary 字串', (E) => { E.diary = 'bad'; });
  tryBoot('diary [null]', (E) => { E.diary = [null]; });
  tryBoot('diary 正常', (E) => { E.diary = []; });
  tryBoot('stats 缺 byId', (E) => { E.stats = { events: 0 }; });
  tryBoot('claimedFlashDates 數字', (E) => { E.claimedFlashDates = 5; });
  rows.push({
    id: 'EV-22 損毀日記／已領旗',
    pass: crashes.filter(c => c.threw).length === 0,
    crashes,
  });
  const bad = SIM.deserialize('{', base);
  const bad2 = SIM.deserialize('{"v":1}', base);
  const ok = SIM.deserialize(JSON.stringify({ v: 1, seed: 7, stage: 'adult', needs: { hunger: 10, mood: 10, clean: 10, energy: 10 }, lastSaveTime: 'nope' }), base);
  rows.push({
    id: 'deserialize 壞 JSON／缺 needs',
    pass: bad === null && bad2 === null && ok && ok.needs.hunger === 10,
    bad: bad === null, bad2: bad2 === null, hunger: ok && ok.needs.hunger, lastSaveTime: ok && ok.lastSaveTime,
  });
  return rows;
}

function coldAbsence(nSeeds, nDays) {
  const diaries = [], tots = [], dayMaxes = [];
  let rareFail = 0, popOver = 0, tsCollapsed = 0, daysOver4 = 0, grainsGot = 0;
  const T1 = new Date(2026, 5, 1, 21, 0, 0).getTime();
  for (let sd = 1; sd <= nSeeds; sd++) {
    const s = adult(sd, T1);
    SIM.advance(s, 30, { hour: 21, now: T1 }, 30);
    s.lastSeen = T1; s.lastSaveTime = T1; s.grains = 0;
    const back = T1 + nDays * DAYMS;
    SIM.applyOffline(s, back);
    diaries.push(s.evs.diary.length);
    tots.push(s.evs.offLog.length);
    const by = {};
    for (const e of s.evs.offLog) {
      const d = e.ts ? dateKey(e.ts) : 'na';
      by[d] = (by[d] || 0) + 1;
    }
    const vals = Object.values(by);
    dayMaxes.push(vals.length ? Math.max(...vals) : 0);
    daysOver4 += vals.filter(n => n > P.dailyMax).length;
    const rf = rareFirstOk(s.evs.offLog);
    if (!rf.ok) rareFail++;
    if (rf.pops > 2) popOver++;
    const ages = s.evs.diary.map(d => (d.ts ? (back - d.ts) / DAYMS : 0));
    if (s.evs.diary.length && ages.every(a => a < 0.05)) tsCollapsed++;
    const g0 = s.grains;
    EV.claim(s); EV.claim(s); EV.claim(s);
    grainsGot += s.grains - g0;
  }
  diaries.sort((a, b) => a - b); tots.sort((a, b) => a - b);
  const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
  const q = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
  return {
    n: nSeeds, nDays,
    diaryMean: +mean(diaries).toFixed(2), diaryMed: q(diaries, 0.5), diaryP95: q(diaries, 0.95), diaryMax: diaries[diaries.length - 1], diaryMin: diaries[0],
    totMean: +mean(tots).toFixed(2), totMed: q(tots, 0.5), totMax: tots[tots.length - 1],
    perDay: +(mean(tots) / nDays).toFixed(3),
    offlineDayMax: Math.max(...dayMaxes),
    daysOver4, rareFail, popOver, tsCollapsed,
    claimGrainsMean: +(grainsGot / nSeeds).toFixed(2),
    diaryCap: P.diaryMax, dailyMax: P.dailyMax,
  };
}
function onlineCapProbe(base) {
  const savedC = P.drawChance, savedE = P.drawEveryH.slice();
  P.drawChance = 1; P.drawEveryH = [0.5, 0.5];
  try {
    const s = adult(7, base);
    const by = {};
    const fn = (st, r) => {
      if (st !== s || r.offline || r.kind !== 'draw' || r.id === 'flash' || r.id === 'grumpy') return;
      const day = dateKey(r.ts || base);
      by[day] = (by[day] || 0) + 1;
    };
    EV.listeners.push(fn);
    let now = base + 19 * H * 1000;
    s.lastSeen = now; s.lastSaveTime = now;
    EV.ensure(s);
    s.evs.gDone = true; s.evs.flashToday = false; s.evs.flashDone = true; s.evs.dayCount = 0; s.evs.next = 0; s.evs.dayIdx = null;
    for (let i = 0; i < 10; i++) {
      const nxt = now + 0.25 * H * 1000;
      SIM.advance(s, 0.25 * H, { hour: SIM.hourOf(nxt), now: nxt }, 60);
      now = nxt; s.lastSeen = now; EV.markSave(s, now);
    }
    EV.listeners.splice(EV.listeners.indexOf(fn), 1);
    const counts = Object.values(by);
    const max = counts.length ? Math.max(...counts) : 0;
    const eligible = ['gift', 'meteor', 'rainbow', 'firefly_walk', 'treasure'];
    return { id: '上線傍晚池抽取封頂 4（5 個事件喺時段內）', pass: max === P.dailyMax, max, by, dayCount: s.evs.dayCount, dailyMax: P.dailyMax, eligible, hours: 2.5 };
  } finally { P.drawChance = savedC; P.drawEveryH = savedE; }
}
function behaviorCases(base) {
  const BEH = require(path.join(SRC, 'src/behavior.js'));
  const rows = [];
  const ctxOf = (s) => ({ s, pw: { period: 'noon' }, sun: 1, override: null, event: null });
  {
    const s = adult(11, base);
    EV.ensure(s); s.evs.lastAt = -1e9; s.evs.cd = {};
    const b = BEH.create(s.seed);
    for (let i = 0; i < 5; i++) BEH.tap(b, 'pet', 0);
    BEH.update(b, 0.2, ctxOf(s));
    const req = b.tantrumReq || 0;
    let rec = null;
    if (req) { b.tantrumReq = 0; rec = EV.tapTantrum(s, { now: base + 12 * H * 1000, hour: 12 }); }
    const cdH = s.evs.cd.grumpy != null ? (s.evs.cd.grumpy - s.evs.clock) / H : null;
    rows.push({
      id: 'tapPet(5) 同一幀（<10秒）→ 鬧脾氣事件 48h',
      pass: req >= 1 && rec && rec.id === 'grumpy' && rec.kind === 'tap' && b.state === 'grumpy' && cdH != null && Math.abs(cdH - 48) < 0.05,
      state: b.state, tantrumReq: req, event: rec && rec.id, cdH: cdH == null ? null : +cdH.toFixed(3),
    });
  }
  {
    const s = adult(12, base);
    EV.ensure(s);
    s.sleeping = true;
    const needs = Object.assign({}, s.needs);
    const grains = s.grains;
    const b = BEH.create(s.seed);
    SIM.toggleSleep(s);
    BEH.tap(b, 'wake', 0);
    BEH.update(b, 0.2, ctxOf(s));
    const needsSame = ['hunger', 'mood', 'clean', 'energy'].every(k => s.needs[k] === needs[k]);
    rows.push({
      id: '睡眠 lightWake：睏睏、唔鬧脾氣、唔扣需求',
      pass: s.sleeping === false && (b.log.enters.lightWake || 0) >= 1 && b.expr === 'tired' && !(b.tantrumReq) && needsSame && s.grains === grains && !(s.evs.log || []).some(x => x.id === 'grumpy'),
      sleeping: s.sleeping, lightWake: b.log.enters.lightWake || 0, expr: b.expr, state: b.state, needsSame,
    });
  }
  {
    const s = adult(13, base);
    s.sleeping = true;
    const needs = Object.assign({}, s.needs);
    const b = BEH.create(s.seed);
    for (let i = 0; i < 5; i++) BEH.tap(b, 'pet', 0);
    BEH.update(b, 0.2, ctxOf(s));
    const needsSame = ['hunger', 'mood', 'clean', 'energy'].every(k => s.needs[k] === needs[k]);
    rows.push({
      id: '睡眠中連點 5 下：只翻身、唔鬧脾氣、唔扣需求',
      pass: (b.tantrumReq || 0) === 0 && b.state !== 'grumpy' && needsSame && (b.log.enters.sleepStir || 0) >= 1,
      state: b.state, stir: b.log.enters.sleepStir || 0, tantrum: b.tantrumReq || 0, needsSame,
    });
  }
  return rows;
}
function offlineCapProbe(base) {
  const savedC = P.drawChance, savedE = P.drawEveryH.slice();
  P.drawChance = 1; P.drawEveryH = [0.4, 0.4];
  try {
    const start = new Date(2026, 5, 10, 6, 0, 0).getTime();
    const s = adult(9, start);
    EV.ensure(s);
    s.evs.gDone = true; s.evs.flashToday = false; s.evs.flashDone = true;
    s.evs.next = 0; s.evs.dayCount = 0; s.evs.dayIdx = null; s.evs.lastAt = -1e9;
    s.lastSeen = start; s.lastSaveTime = start;
    const back = start + 20 * H * 1000;
    SIM.applyOffline(s, back);
    const by = {};
    for (const e of (s.evs.offLog || [])) {
      if (e.id === 'flash' || e.id === 'grumpy') continue;
      const d = e.ts ? dateKey(e.ts) : 'na';
      by[d] = (by[d] || 0) + 1;
    }
    const counts = Object.values(by);
    const max = counts.length ? Math.max(...counts) : 0;
    return {
      id: '離線補抽唔計每日上限 4',
      pass: !!P.offlineIgnoreDailyMax && max > P.dailyMax,
      max, by, n: (s.evs.offLog || []).length, ignore: !!P.offlineIgnoreDailyMax, dailyMax: P.dailyMax,
      ids: (s.evs.offLog || []).map(e => e.id),
    };
  } finally { P.drawChance = savedC; P.drawEveryH = savedE; }
}
function lastSeenRewind(base) {
  const now = base + 20 * DAYMS + 15 * H * 1000;
  const s = adult(7, now);
  EV.ensure(s);
  s.lastSaveTime = now; s.lastSeen = now; s.grains = 0;
  const rolled = now - 30 * 60 * 1000;
  // 同 main.js G.save：lastSeen 只可向前；markSave 唔拉低 lastSaveTime
  s.lastSeen = Math.max(+s.lastSeen || 0, rolled);
  EV.markSave(s, rolled);
  const saved = { lastSeen: s.lastSeen, lastSaveTime: s.lastSaveTime };
  const rep = SIM.applyOffline(s, now);
  const rec = EV.noteOpen(s, { hour: 15, now });
  const offN = (s.evs.offLog || []).length;
  // applyOffline 本身：而家早過 lastSeen 都唔可以拉後
  const s2 = adult(8, now);
  s2.lastSeen = now; s2.lastSaveTime = now; s2.grains = 0;
  const rep2 = SIM.applyOffline(s2, rolled);
  return {
    id: '回撥 30 分鐘 G.save 唔拉低 lastSeen，恢復後冇離線禮物',
    pass: saved.lastSeen === now && saved.lastSaveTime === now && rep.gift === 0 && rep.T === 0 && offN === 0 && s.grains === 0 && !rec
      && s2.lastSeen === now && rep2.T === 0 && rep2.gift === 0 && (s2.evs.offLog || []).length === 0,
    saved, Tmin: +(rep.T / 60).toFixed(1), gift: rep.gift, grains: s.grains, noteOpen: rec && rec.id, offN,
    applyBack: { lastSeenDelta: s2.lastSeen - now, T: rep2.T, gift: rep2.gift, off: (s2.evs && s2.evs.offLog || []).length },
  };
}
function summarize(rows) {
  const by = {};
  for (const r of rows) {
    if (!by[r.profile]) by[r.profile] = [];
    by[r.profile].push(r);
  }
  const out = [];
  for (const p of PROFILES) {
    const list = by[p.id] || [];
    const avg = (k) => list.reduce((a, r) => a + r[k], 0) / list.length;
    const min = (k) => Math.min(...list.map(r => r[k] == null ? Infinity : r[k]));
    const max = (k) => Math.max(...list.map(r => r[k] == null ? -Infinity : r[k]));
    const eveKeys = {};
    for (const r of list) for (const k of Object.keys(r.eveningSharePct)) eveKeys[k] = 1;
    const eve = {};
    for (const k of Object.keys(eveKeys)) {
      eve[k] = +((list.reduce((a, r) => a + (r.eveningSharePct[k] || 0), 0) / list.length).toFixed(2));
    }
    const seed7 = list.find(r => r.seed === 7) || list[0];
    out.push({
      profile: p.id, name: p.name,
      seeds: list.length,
      pool: [+min('poolPerDay').toFixed(3), +max('poolPerDay').toFixed(3), +avg('poolPerDay').toFixed(3)],
      total: [+min('totalPerDay').toFixed(3), +max('totalPerDay').toFixed(3), +avg('totalPerDay').toFixed(3)],
      grumpy: [+min('grumpyPerDay').toFixed(3), +max('grumpyPerDay').toFixed(3)],
      guar: [+min('guarPerDay').toFixed(3), +max('guarPerDay').toFixed(3)],
      zero: [+min('zeroActivePct').toFixed(3), +max('zeroActivePct').toFixed(3)],
      zeroLimit: p.opens >= 3 || p.everyOther ? 1 : 3,
      rainbow: [min('rainbowEveryDays'), max('rainbowEveryDays'), +avg('rainbowEveryDays').toFixed(3)],
      rainbowMaxGapD: +max('rainbowMaxGapD').toFixed(3),
      pity: list.reduce((a, r) => a + (r.pity || 0), 0),
      flashWallViol: list.reduce((a, r) => a + (r.flashWallViol || 0), 0),
      flashMinGapH: (() => { const xs = list.map(r => r.flashMinGapH).filter(x => x != null); return xs.length ? +Math.min(...xs).toFixed(3) : null; })(),
      shiny: [+min('shinyPct').toFixed(3), +max('shinyPct').toFixed(3)],
      cdViol: list.reduce((a, r) => a + r.cdViol, 0),
      cdByKind: list.reduce((a, r) => { for (const k of Object.keys(r.cdByKind || {})) a[k] = (a[k] || 0) + r.cdByKind[k]; return a; }, {}),
      cdById: list.reduce((a, r) => { for (const k of Object.keys(r.cdById || {})) a[k] = (a[k] || 0) + r.cdById[k]; return a; }, {}),
      gapViol: list.reduce((a, r) => a + r.gapViol, 0),
      rareViol: list.reduce((a, r) => a + r.rareViol, 0),
      maxPop: Math.max(...list.map(r => r.maxPop)),
      rollbacks: list.reduce((a, r) => a + r.rollbacks, 0),
      fireflyOut: list.reduce((a, r) => a + r.fireflyOutOfWindow, 0),
      maxOnlineDraws: Math.max(...list.map(r => r.maxOnlineDraws || 0)),
      eveningShareAvg: eve,
      eveningNSeed7: seed7 ? seed7.eveningN : 0,
      seed7: seed7 ? {
        pool: seed7.poolPerDay, total: seed7.totalPerDay, grumpy: seed7.grumpyPerDay, guar: seed7.guarPerDay,
        zero: seed7.zeroActivePct, rainbow: seed7.rainbowEveryDays, shiny: seed7.shinyPct,
        eveningShare: seed7.eveningSharePct, eveningN: seed7.eveningN, minGapMin: seed7.minGapMin,
        cdSamples: seed7.cdSamples, gapSamples: seed7.gapSamples, rareSamples: seed7.rareSamples,
      } : null,
    });
  }
  return out;
}

function main() {
  const base = new Date(2026, 0, 5, 0, 0, 0).getTime();
  const t0 = Date.now();
  let commit = null;
  try { commit = require('child_process').execSync('git rev-parse HEAD', { cwd: path.resolve(SRC, '../..'), encoding: 'utf8' }).trim(); } catch (e) { commit = null; }
  console.log('# qa_glimmer_build');
  console.log('src', SRC);
  console.log('commit', commit);
  console.log('tz', process.env.TZ || '(unset)', 'baseLocal', new Date(base).toString());
  console.log('weights', D.EVENTS.map(e => e.id + ':' + e.weight + (e.hours ? '@' + e.hours.join('-') : '')).join(' '));
  console.log('params', JSON.stringify({
    p: P.drawChance, gap: P.minGapSec, cd: P.cooldownH, rare: P.cooldownRareH, tol: P.lastSaveTolSec,
    ahead: P.lastSaveMaxAheadH, guarOpens: P.guaranteeOpens, dailyMax: P.dailyMax, offMax: P.offlineMaxEvents,
    popup: P.offlinePopupMax, diary: P.diaryKeepDays, warn: P.diaryWarnDays, grains: P.diaryGrains, cap: P.diaryClaimMax,
  }));

  const weightShareShipped = theoreticalEvening();
  console.log('\n# 理論傍晚權重佔比（唔計冷卻／門檻）', JSON.stringify(weightShareShipped.sharePct));
  console.log('  逐小時螢火%', weightShareShipped.byHour.map(h => h.hour + ':' + h.fireflyPct + '%').join(' '));

  console.log('\n# 時鐘案例');
  const clock = clockCases(base);
  for (const c of clock) console.log((c.pass ? 'PASS ' : 'FAIL ') + c.id);

  console.log('\n# 日記／損毀');
  const diary = diaryCases(base);
  for (const c of diary) console.log((c.pass ? 'PASS ' : 'FAIL ') + c.id);

  console.log('\n# 連點／輕喚醒');
  const behavior = behaviorCases(base);
  for (const c of behavior) console.log((c.pass ? 'PASS ' : 'FAIL ') + c.id, JSON.stringify(c));

  console.log('\n# 上線每日上限');
  const onlineCap = onlineCapProbe(base);
  console.log((onlineCap.pass ? 'PASS ' : 'FAIL ') + onlineCap.id, JSON.stringify(onlineCap));
  const offlineCap = offlineCapProbe(base);
  console.log((offlineCap.pass ? 'PASS ' : 'FAIL ') + offlineCap.id, JSON.stringify(offlineCap));

  const rewind = lastSeenRewind(base);
  console.log((rewind.pass ? 'PASS ' : 'FAIL ') + rewind.id, JSON.stringify(rewind));

  console.log('\n# 冷啟動 14 日離線 ×1000（同 sim-report ①）');
  const cold14 = coldAbsence(1000, 14);
  console.log(JSON.stringify(cold14));

  console.log('\n# 缺席（一般玩家暖機 14 日後）×40');
  const absLengths = [1, 3, 7, 14, 21, 30];
  const abs = {};
  for (const n of absLengths) {
    const trials = [];
    for (let i = 0; i < 40; i++) trials.push(absenceTrial(n, 1000 + i * 13 + n, base));
    const mean = (k) => +(trials.reduce((a, t) => a + t[k], 0) / trials.length).toFixed(2);
    abs[n] = {
      n: trials.length,
      gen: mean('gen'), popups: mean('popups'), diaryNew: mean('diaryNew'),
      maxPop: Math.max(...trials.map(t => t.popups)),
      popOver: trials.filter(t => !t.maxPopOk).length,
      rareViol: trials.filter(t => t.rareViol).length,
      EHours: mean('EHours'), THours: mean('THours'),
      capped: trials.filter(t => t.offLogCap).length,
      tsCollapsed: trials.filter(t => t.diaryTsAllEqualReturn).length,
      sampleOrder: (trials.find(t => t.rareViol) || trials.find(t => t.gen >= 3) || trials[0]).order,
      sample: trials[0],
    };
    console.log('  缺席', n, '日 gen', abs[n].gen, 'pop', abs[n].popups, 'diary', abs[n].diaryNew, 'E', abs[n].EHours, 'h rareViol', abs[n].rareViol + '/' + trials.length, 'cap', abs[n].capped);
  }

  console.log('\n# 作息模擬', DAYS, '日 ×', SEEDS.length, 'seed');
  const shippedSnap = snapEvents();
  const runs = [];
  for (const seed of SEEDS) {
    for (const p of PROFILES) {
      const t1 = Date.now();
      const r = runProfile(p, DAYS, seed, base);
      runs.push(r);
      console.log('  ', seed, p.id, 'pool', r.poolPerDay, 'tot', r.totalPerDay, 'zero', r.zeroActivePct, 'rb', r.rainbowEveryDays, 'rbGap', r.rainbowMaxGapD, 'pity', r.pity, 'eveFF', (r.eveningSharePct.firefly_walk || 0) + '%', 'nEve', r.eveningN, 'cd', r.cdViol, 'gap', r.gapViol, 'fWall', r.flashWallViol, (Date.now() - t1) + 'ms');
    }
  }
  const shippedSummary = summarize(runs);

  let whatif = null;
  if (WHATIF) {
    applyV51Weights();
    console.log('\n# 對照：改成 v5.1 權重＋時段（只係記憶體，冇改檔）', D.EVENTS.map(e => e.id + ':' + e.weight + '@' + (e.hours || []).join('-')).join(' '));
    const wshare = theoreticalEvening();
    console.log('  理論傍晚%', JSON.stringify(wshare.sharePct));
    const wruns = [];
    for (const p of PROFILES) {
      const r = runProfile(p, DAYS, 7, base);
      wruns.push(r);
      console.log('  v51', p.id, 'pool', r.poolPerDay, 'tot', r.totalPerDay, 'rb', r.rainbowEveryDays, 'eveFF', (r.eveningSharePct.firefly_walk || 0) + '%', 'zero', r.zeroActivePct);
    }
    whatif = { theoretical: wshare, seed7: summarize(wruns) };
    restoreEvents(shippedSnap);
  }

  const out = {
    src: SRC, days: DAYS, seeds: SEEDS, tz: process.env.TZ || null,
    commit, commitNote: 'measured against events.js/sim.js of the given --src tree',
    params: {
      drawChance: P.drawChance, minGapSec: P.minGapSec, cooldownH: P.cooldownH, cooldownRareH: P.cooldownRareH,
      lastSaveTolSec: P.lastSaveTolSec, lastSaveMaxAheadH: P.lastSaveMaxAheadH, guaranteeOpens: P.guaranteeOpens,
      dailyMax: P.dailyMax, offlineMaxEvents: P.offlineMaxEvents, offlinePopupMax: P.offlinePopupMax,
      diaryKeepDays: P.diaryKeepDays, diaryWarnDays: P.diaryWarnDays, diaryGrains: P.diaryGrains, diaryClaimMax: P.diaryClaimMax,
      weights: shippedSnap,
    },
    theoreticalEveningShipped: weightShareShipped,
    clock, diary, behavior, onlineCap, offlineCap, rewind, cold14, absence: abs,
    shippedSummary, whatif,
    ms: Date.now() - t0,
  };
  if (JSON_OUT) {
    fs.mkdirSync(path.dirname(JSON_OUT), { recursive: true });
    fs.writeFileSync(JSON_OUT, JSON.stringify(out, null, 1));
    console.log('\n寫入', JSON_OUT);
  }
  const clockFail = clock.filter(c => !c.pass).length;
  const diaryFail = diary.filter(c => !c.pass).length;
  console.log('\n時鐘', clock.length - clockFail + '/' + clock.length, '日記案例', diary.length - diaryFail + '/' + diary.length, '耗時', out.ms + 'ms');
  process.exit(0);
}
main();
