/* 《微光小圃》 events.js — 日常事件系統（DOM-free）。
   - 事件池 9 個（data.js EVENTS：7 個一般＋鬧脾氣＋閃光日）；每 2–4 小時「有效時間」抽一次；每個事件有冷卻；每日保底 ≥1（16:00 後或當日首次開 app）；閃光日 3%；系統時間早於 lastSaveTime → 當日唔抽。
   - 有效時間：上線 = 100%；離線 = GDD 第 7 節 E（由 sim.applyOffline 經 step hook 傳入，事件喺離線期間即時結算，只會加光粒／心情，唔會扣）。
   - 全部隨機只用存檔內可還原嘅種子 RNG（state.evs.rs）；不用 Date／Math.random。
   - 掛喺 sim.step（addStepHook），亦可直接 EV.advance(s, dt, ctx) 單獨測試。原創代碼。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.events = factory(root.Glimmer.data, root.Glimmer.sim); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const P = D.PARAMS.events, SICK = D.PARAMS.sickThreshold;
  const CX = 97;                       // 同 render.CX 一致（事件視覺座標用）
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const DEF = {}; D.EVENTS.forEach(e => { DEF[e.id] = e; });
  const listeners = [];

  const rf = (r, a) => a[0] + (a[1] - a[0]) * r();
  const ri = (r, a) => a[0] + Math.floor(r() * (a[1] - a[0] + 1));

  function fresh(seed) {
    return {
      v: 1, rs: (Math.imul((seed >>> 0) || 1, 2654435761) >>> 0) || 7,
      clock: 0, dayClock: 0, next: -1, cd: {}, last: null, lastAt: -1e9, hist: [],
      day: 0, dayIdx: null, dayCount: 0, gDone: false, flashToday: false, flashDone: false,
      claimedFlashDates: [], log: [], noDrawDay: null,
      lastHour: null, hour0: 12, pending: [], active: null, offLog: [], offPop: 0,
      opens: 0, low: 0, diary: [], nowMs: 0,
      stats: { draws: 0, events: 0, flashDays: 0, days: 1, guarantee: 0, guaranteeOpen: 0, byId: {}, popups: 0, diaryAdded: 0, diaryClaimed: 0, diaryExpired: 0, gapBlocked: 0 },
    };
  }
  function ensure(s) {
    if (s.evs && s.evs.v === 1) {
      const E = s.evs, F = fresh(1);
      for (const k in F) if (E[k] === undefined) E[k] = F[k];      // 舊存檔補欄位
      return E;
    }
    const E = s.evs = fresh(s.seed);
    const r = SIM.makeRng(E.rs);
    E.next = rf(r, P.drawEveryH) * 3600;        // 閃光日喺第一次 advance／noteOpen 知道日期後先判定（hash(seed, 日期)）
    E.rs = r.getSeed();
    return E;
  }

  // 閃光日：hash(存檔種子, 日期) < flashDayRate。日期＝本機日序號（有 now 用實時，冇就用邏輯日計數）
  function mix32(h) { h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35); h ^= h >>> 16; return h >>> 0; }
  function dayHash(seed, dayIdx) { return mix32(mix32((seed >>> 0) ^ 0x9e3779b9) ^ Math.imul(dayIdx >>> 0, 0x27d4eb2f)) / 4294967296; }
  function localDay(ms) { const d = new Date(ms); return Math.floor((ms - d.getTimezoneOffset() * 60000) / 86400000); }
  function dateKey(E) { const i = E.dayIdx == null ? 0 : E.dayIdx; return i > 10000 ? new Date(i * 86400000).toISOString().slice(0, 10) : 'd' + i; }   // 日期鍵（本機日序號 → YYYY-MM-DD）
  const flashClaimed = (E) => E.claimedFlashDates.indexOf(dateKey(E)) >= 0;
  // 系統時間回撥（早於存檔記低嘅 lastSaveTime 逾 120 秒；UTC 比較）→ 記低「當日」(noDrawDay，UTC 日)，當日唔抽閃光日同事件（含保底／開 app）。前撥／改時區唔處理（M1）
  const utcDay = (ms) => Math.floor(ms / 86400000);
  function checkRollback(s, E, now) {
    if (now == null) return;
    SIM.sanitizeSaveTime(s, now);                                                            // ② lastSaveTime > now+24h → 無效，重設為 now
    if (s.lastSaveTime && now < s.lastSaveTime - P.lastSaveTolSec * 1000) { E.noDrawDay = utcDay(now); E.stats.rollbacks = (E.stats.rollbacks || 0) + 1; }   // ① 容差 120 秒（網絡校時）
  }
  function suppressed(s, E) { const n = E.nowMs; if (!n) return false; return !!((s.lastSaveTime && n < s.lastSaveTime - P.lastSaveTolSec * 1000) || (E.noDrawDay != null && E.noDrawDay === utcDay(n))); }
  function markSave(s, now) { if (now != null && !(s.lastSaveTime >= now)) s.lastSaveTime = now; }     // 只增唔減（回撥唔可以拉低）
  function rollFlash(s, E) { E.flashToday = dayHash(s.seed, E.dayIdx) < P.flashDayRate && !flashClaimed(E) && !suppressed(s, E); if (E.flashToday) E.stats.flashDays++; }
  function syncDay(s, E, now, offline) {       // 第一次見到日期：定 dayIdx＋判定閃光；上線時如實時日序號前進咗（隔幾日開 app），跟上
    if (E.dayIdx == null) { E.dayIdx = now != null ? localDay(now) : 0; rollFlash(s, E); return; }
    if (now != null && !offline) { const d = localDay(now); if (d > E.dayIdx) { E.dayIdx = d; E.flashDone = false; rollFlash(s, E); } }
  }
  function minNeed(s) { return Math.min(s.needs.hunger, s.needs.mood, s.needs.clean, s.needs.energy); }
  function inHours(h, a, b) { return a < b ? (h >= a && h < b) : (h >= a || h < b); }
  function condOk(def, s, hour, E) {
    if (def.hours && !inHours(hour, def.hours[0], def.hours[1])) return false;
    if (def.sleeping === false && s.sleeping) return false;
    if (def.moodAtLeast != null && s.needs.mood < def.moodAtLeast) return false;
    if (def.energyAtLeast != null && s.needs.energy < def.energyAtLeast) return false;
    if (def.lowNeed && !(E && E.low >= P.grumpyLowSec)) return false;      // 任一需求 <30 持續 ≥1 小時
    const mn = minNeed(s);
    if (def.visual && mn < SICK) return false;       // 不適時唔搞視覺事件
    return true;
  }
  function weightOf(def, s, E) {
    let w = def.weight;
    if (def.id === E.last) w *= P.repeatWeightMul;   // 防重複
    return w;
  }
  const cdLeft = (E, id) => (E.cd[id] || 0) - E.clock;
  function pick(s, E, r, hour, relaxed) {
    let c = [];
    for (const def of D.EVENTS) {
      if (def.special) continue;
      if (relaxed) { if (!def.fallback || !condOk(def, s, hour, E)) continue; }
      else if (!condOk(def, s, hour, E) || cdLeft(E, def.id) > 0) continue;
      c.push(def);
    }
    if (relaxed) {   // 保底：優先「條件符合＋冷卻已過」，其次只忽略冷卻，最後忽略條件
      const cool = c.filter(d => cdLeft(E, d.id) <= 0); if (cool.length) c = cool;
      else if (!c.length) c = D.EVENTS.filter(d => d.fallback);
    }
    if (relaxed && c.length > 1) { const k = c.findIndex(d => d.id === E.last); if (k >= 0) c.splice(k, 1); }
    if (!c.length) return null;
    let tot = 0; const ws = c.map(d => { const w = Math.max(0.0001, weightOf(d, s, E)); tot += w; return w; });
    let x = r() * tot;
    for (let i = 0; i < c.length; i++) { x -= ws[i]; if (x <= 0) return c[i]; }
    return c[c.length - 1];
  }
  const gapOk = (E) => E.clock - E.lastAt >= P.minGapSec;

  /* 離線：頭 offlinePopupMax 個變事件卡（即時領獎）；其餘入日記（要玩家喺日記領，留 diaryKeepDays 日） */
  function trigger(s, E, def, r, offline, kind) {
    let grains = ri(r, def.grains), mood = ri(r, def.mood);
    const flavor = def.flavor[Math.floor(r() * def.flavor.length)];
    const toDiary = !!offline && E.offPop >= P.offlinePopupMax;
    if (toDiary) { grains = P.diaryGrains; mood = 0; }        // 日記：每條固定 +diaryGrains 光粒
    const rec = { id: def.id, grains, mood, flavor, off: def.off, day: E.day, at: E.clock, hour: E.lastHour == null ? null : +E.lastHour.toFixed(2), kind: kind || 'draw', ts: E.nowMs || 0, offline: !!offline, diary: toDiary };
    if (!toDiary) { s.grains += grains; s.needs.mood = clamp(s.needs.mood + mood, 0, 100); }   // 只加唔減
    if (def.id === 'flash') { const k = dateKey(E); if (E.claimedFlashDates.indexOf(k) < 0) E.claimedFlashDates.push(k); while (E.claimedFlashDates.length > 60) E.claimedFlashDates.shift(); }   // 已領旗標：同一日唔可重領
    E.log.push({ id: def.id, kind: kind || 'draw', day: E.day, date: dateKey(E), hour: rec.hour, at: Math.round(E.clock), offline: !!offline, diary: toDiary }); if (E.log.length > 80) E.log.shift();
    E.last = def.id; E.lastAt = E.clock; E.hist.push(def.id); if (E.hist.length > P.historyLen) E.hist.shift();
    E.cd[def.id] = E.clock + (def.cooldownH || (def.rare ? P.cooldownRareH : P.cooldownH)) * 3600;
    E.dayCount++; E.stats.events++; E.stats.byId[def.id] = (E.stats.byId[def.id] || 0) + 1;
    if (s.stats) s.stats.events = (s.stats.events || 0) + 1;
    if (offline) {
      E.offLog.push(rec);
      if (toDiary) { E.diary.push(rec); E.stats.diaryAdded++; while (E.diary.length > P.diaryMax) E.diary.shift(); }
      else { E.offPop++; E.stats.popups++; E.pending.push(rec); while (E.pending.length > P.pendingMax) E.pending.shift(); }
    } else { E.stats.popups++; E.pending.push(rec); while (E.pending.length > P.pendingMax) E.pending.shift(); }
    for (let i = 0; i < listeners.length; i++) listeners[i](s, rec, { offline: !!offline });
    return rec;
  }

  function newDay(s, E) {
    E.day++; E.dayIdx = (E.dayIdx == null ? 0 : E.dayIdx) + 1; E.dayCount = 0; E.gDone = false; E.flashDone = false; E.dayClock = 0; E.opens = 0; E.stats.days++;
    rollFlash(s, E);
  }
  function guarantee(s, E, r, hour, off, why) {
    if (E.gDone) return false;
    if (E.dayCount > 0) { E.gDone = true; return false; }
    if (!gapOk(E)) { E.stats.gapBlocked++; return false; }     // 間隔未夠，下一步再試
    E.gDone = true;
    if (off && E.offLog.length >= P.offlineMaxEvents) return false;
    E.stats[why === 'open' ? 'guaranteeOpen' : 'guarantee']++;
    const def = (E.flashToday && !E.flashDone && !flashClaimed(E)) ? DEF.flash : pick(s, E, r, hour, true);
    if (!def) return false;
    if (def.id === 'flash') E.flashDone = true;
    trigger(s, E, def, r, off, 'guarantee'); return true;
  }

  /* ctx: { hour (本機鐘點，可選), offline, now (實時 ms，可選) } */
  function advance(s, dt, ctx) {
    if (!api.enabled || !P.enabled || s.stage === 'egg') return;
    ctx = ctx || {};
    const E = ensure(s), r = SIM.makeRng(E.rs);
    if (ctx.now != null) { E.nowMs = ctx.now; if (!ctx.offline) checkRollback(s, E, ctx.now); }
    E.clock += dt; E.dayClock += dt;
    const sup = suppressed(s, E);
    const hour = ctx.hour != null ? ((ctx.hour % 24) + 24) % 24 : (E.hour0 + E.clock / 3600) % 24;
    if (E.dayIdx == null) syncDay(s, E, ctx.now, !!ctx.offline);
    if (E.lastHour != null && hour < E.lastHour - 0.5) newDay(s, E);
    syncDay(s, E, ctx.now, !!ctx.offline);
    E.lastHour = hour;
    E.low = minNeed(s) < P.grumpyLowNeed ? E.low + dt : 0;
    const off = !!ctx.offline;
    const cap = () => off && E.offLog.length >= P.offlineMaxEvents;
    // 每日保底：16:00 後仍未有事件
    if (!sup && !E.gDone && hour >= P.guaranteeHour) guarantee(s, E, r, hour, off, 'hour');
    // 抽選
    while (E.clock >= E.next) {
      E.next += rf(r, P.drawEveryH) * 3600;
      if (sup) { E.stats.suppressed = (E.stats.suppressed || 0) + 1; continue; }     // 時間回撥：當日唔抽
      E.stats.draws++;
      if (cap()) continue;
      if (!gapOk(E)) { E.stats.gapBlocked++; continue; }
      if (E.flashToday && !E.flashDone && !flashClaimed(E)) { E.flashDone = true; trigger(s, E, DEF.flash, r, off, 'flash'); continue; }
      if (E.dayCount >= P.dailyMax) continue;
      if (r() >= P.drawChance) continue;
      const def = pick(s, E, r, hour, false);
      if (def) trigger(s, E, def, r, off, 'draw');
    }
    E.rs = r.getSeed();
  }

  /* 開 app：當日第 1 次開（P.guaranteeOpens）仍冇事件 → 保底觸發。ctx: { hour, now }。回傳觸發嘅 rec 或 null。 */
  function noteOpen(s, ctx) {
    if (!api.enabled || !P.enabled || s.stage === 'egg') return null;
    ctx = ctx || {};
    const E = ensure(s), r = SIM.makeRng(E.rs);
    if (ctx.now != null) { E.nowMs = ctx.now; pruneDiary(s, ctx.now); checkRollback(s, E, ctx.now); }
    const hour = ctx.hour != null ? ((ctx.hour % 24) + 24) % 24 : (E.lastHour != null ? E.lastHour : 12);
    if (E.dayIdx == null) syncDay(s, E, ctx.now, false);
    if (E.lastHour != null && hour < E.lastHour - 0.5) newDay(s, E);
    syncDay(s, E, ctx.now, false);
    E.lastHour = hour; E.opens++;
    let rec = null;
    if (!suppressed(s, E) && E.opens >= P.guaranteeOpens) { if (guarantee(s, E, r, hour, false, 'open')) rec = E.pending[E.pending.length - 1] || null; }
    E.rs = r.getSeed();
    return rec;
  }

  // ── 日記（離線溢出事件；可領獎，留 diaryKeepDays 日）──
  function pruneDiary(s, nowMs) {
    const E = s.evs; if (!E || !E.diary.length) return 0;
    const lim = P.diaryKeepDays * 86400e3, n0 = E.diary.length;
    E.diary = E.diary.filter(d => !d.ts || nowMs - d.ts <= lim);
    const gone = n0 - E.diary.length; E.stats.diaryExpired += gone; return gone;
  }
  function diary(s) { return (s.evs && s.evs.diary) || []; }
  function diaryGroups(s) {          // 同類事件合併：[{id,name,n,grains,flavor,ts}]（按最舊嗰條排）
    const g = {}, out = [];
    diary(s).forEach(d => { let x = g[d.id]; if (!x) { x = g[d.id] = { id: d.id, name: DEF[d.id] ? DEF[d.id].name : d.id, n: 0, grains: 0, flavor: d.flavor, ts: d.ts }; out.push(x); } x.n++; x.grains += P.diaryGrains; });
    return out;
  }
  function diaryWarn(s, nowMs) {      // 第 diaryWarnDays 日起提示：回傳快過期嘅條數
    const lim = P.diaryWarnDays * 86400e3;
    return diary(s).filter(d => d.ts && nowMs - d.ts >= lim).length;
  }
  function claim(s, which) {         // which：事件 id＝只領嗰類；省略／'all'＝一鍵全部。每條 +diaryGrains，單次上限 diaryClaimMax（餘下留低）
    const E = ensure(s); let g = 0, n = 0; const keep = [];
    for (const d of E.diary) {
      const mine = !which || which === 'all' || d.id === which;
      if (mine && g + P.diaryGrains <= P.diaryClaimMax) { g += P.diaryGrains; n++; } else keep.push(d);
    }
    E.diary = keep; s.grains += g; E.stats.diaryClaimed += n;
    return { n, grains: g, mood: 0, left: keep.length, capped: g + P.diaryGrains > P.diaryClaimMax && keep.some(d => !which || which === 'all' || d.id === which) };
  }

  // ── sim step hook ──
  function nowFromOpts(opts) { return opts.off ? opts.off.now : (opts.now != null ? opts.now : null); }
  function hourFromOpts(E, opts) {
    if (opts.off) { const o = opts.off; return (o.hour0 + (o.E > 0 ? o.done / o.E : 0) * o.T / 3600) % 24; }
    return opts.hour != null ? opts.hour : null;
  }
  function stepHook(s, dt, opts) {
    if (!api.enabled || s.stage === 'egg') return;
    const E = ensure(s);
    advance(s, dt, { offline: !!opts.offline, hour: hourFromOpts(E, opts), now: nowFromOpts(opts) });
  }
  SIM.addStepHook(stepHook);

  // ── 即時事件流程（UI 用）──
  function takePending(s) {
    const E = ensure(s);
    if (E.active || !E.pending.length) return null;
    const rec = E.pending.shift();
    E.active = { rec, t: 0, dur: Math.max(DEF[rec.id].dur, P.cardSec) };
    return E.active;
  }
  function tickActive(s, dt) {
    const E = s.evs; if (!E || !E.active) return null;
    E.active.t += dt;
    if (E.active.t >= E.active.dur) { const a = E.active; E.active = null; return a; }
    return null;
  }
  // debug／測試：強制觸發（唔影響冷卻以外嘅規則）
  function force(s, id) {
    const E = ensure(s), r = SIM.makeRng(E.rs), def = DEF[id];
    if (!def) return null;
    const rec = trigger(s, E, def, r, false, 'force');
    E.rs = r.getSeed(); return rec;
  }
  function setFlashDay(s, on) { const E = ensure(s); E.flashToday = !!on; E.flashDone = false; }
  function flashActive(s) { const E = s.evs; return !!(E && E.flashToday && E.flashDone); }

  // ── 事件視覺（純函數；renderer／behavior 共用）。t = 事件開始後秒數。座標：art px。──
  function visual(id, t, dur) {
    dur = dur || (DEF[id] && DEF[id].dur) || 5;
    if (id === 'butterfly') {
      const u = clamp(t / dur, 0, 1), away = clamp((t - (dur - 1.2)) / 1.2, 0, 1);
      const bx = 36 + u * 120 + Math.sin(t * 1.7) * 16, by = 240 + Math.sin(t * 2.3) * 12 - away * 90;
      return { bx, by, rx: bx - CX, flap: Math.floor(t * 9) % 2, near: Math.abs(Math.sin(t * 0.9)) };
    }
    if (id === 'treasure') {
      const digX = 28, digEnd = 3.6, found = t >= digEnd + 0.2;
      return { digX, digEnd, found, mound: clamp(t / digEnd, 0, 1), pop: clamp((t - digEnd - 0.2) / 0.6, 0, 1) };
    }
    if (id === 'rainbow') {
      return { rain: t < 2.6 ? clamp(t / 0.5, 0, 1) * clamp((2.6 - t) / 0.6, 0, 1) : 0, arc: clamp((t - 1.8) / 1.6, 0, 1) * clamp((dur - t) / 1.2, 0, 1) };
    }
    if (id === 'meteor') {
      const streaks = [];
      for (let i = 0; i < 3; i++) { const t0 = 0.4 + i * 1.5, u = (t - t0) / 1.0; if (u >= 0 && u <= 1) streaks.push({ i, u, x0: 170 - i * 34, y0: 22 + i * 20, x1: 70 - i * 26, y1: 96 + i * 26 }); }
      return { streaks };
    }
    if (id === 'firefly_walk') {     // 5 隻螢火沿園圃飄；寵物跟住最近一隻慢行（用現有 play clip，placeholder）
      const flies = [];
      for (let i = 0; i < 5; i++) { const ph = i * 1.3; flies.push({ x: 40 + ((t * (10 + i * 2) + i * 37) % 150), y: 236 + Math.sin(t * 1.6 + ph) * 14 - (i % 3) * 10, tw: 0.5 + 0.5 * Math.sin(t * 5 + ph) }); }
      const lead = flies[0], away = clamp((t - (dur - 1.2)) / 1.2, 0, 1);
      return { flies, rx: clamp(lead.x - CX - 6, -50, 50), away };
    }
    if (id === 'gift') return { show: clamp((t - 0.7) / 0.4, 0, 1), bounce: Math.abs(Math.sin(Math.max(0, t - 0.7) * 6)) * Math.max(0, 1 - (t - 0.7) / 2.2), x: -16 };
    return {};
  }

  const api = {
    enabled: true, DEF, ensure, advance, stepHook, takePending, tickActive, force, setFlashDay, flashActive, visual, condOk, listeners, dateKey, flashClaimed, markSave, suppressed, inHours, noteOpen, diary, diaryGroups, diaryWarn, claim, pruneDiary,
  };
  return api;
});
