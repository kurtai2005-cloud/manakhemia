/* 《微光小圃》 systems.js — systems12 第 1 批（docs-gdd/systems12-v1.md）。原創代碼。
   DOM-free、Node 可 require（純邏輯＋狀態）；main.js 掛入遊戲迴圈，devpanel 加觸發掣。數值全部喺 data.js PARAMS.systems12／evo6.branch.systems。
   系統 7 天氣／季節：每日天氣（真實日期＋seed）＋每週 1–3 場雨（每場 1–3h）；季節跟香港月份。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.sys12 = factory(root.Glimmer.data, root.Glimmer.sim); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM) {
  'use strict';
  const P = D.PARAMS, C = () => P.systems12, DAY = 86400000;

  // ── 共用：本機日數（epoch 起計，跟本機時區）＋ seed 雜湊 ──
  function dayNum(ms) { const d = new Date(ms); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / DAY); }
  function dayStart(ms) { const d = new Date(ms); return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime(); }
  function hash(seed, a, b) { let h = (seed >>> 0) ^ 0x9e3779b9; h = Math.imul(h ^ (a >>> 0), 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h ^ ((b | 0) >>> 0), 0xc2b2ae35); h ^= h >>> 16; return h >>> 0; }
  function rngFor(seed, a, b) { return SIM.makeRng(hash(seed, a, b)); }

  // ── 系統 7：天氣 ──
  /* 週＝由星期一起（dayNum 0＝1970-01-01 星期四 → +3）。每週 1–3 場雨：n＝clamp(Binomial(7, 雨%)), rainPerWeek)；
     每場揀唔同日、起始 rainFromH–rainToH、長 1–3h（整點＋分鐘隨機）。其餘時間＝當日底色天氣（晴／陰／霧按權重；落雨日＝陰）。 */
  function weekOf(dn) { return Math.floor((dn + 3) / 7); }
  const wkCache = new Map();
  function rainSpells(seed, wk) {
    const key = seed + ':' + wk; if (wkCache.has(key)) return wkCache.get(key);
    const W = C().weather, r = rngFor(seed, wk, 7), pr = W.weights.rain / 100;
    let n = 0; for (let i = 0; i < 7; i++) if (r() < pr) n++;
    n = Math.max(W.rainPerWeek[0], Math.min(W.rainPerWeek[1], n));
    const days = [0, 1, 2, 3, 4, 5, 6]; for (let i = 6; i > 0; i--) { const j = Math.floor(r() * (i + 1)); const t = days[i]; days[i] = days[j]; days[j] = t; }
    const out = days.slice(0, n).sort((a, b) => a - b).map(di => {
      const dur = W.rainHours[0] + r() * (W.rainHours[1] - W.rainHours[0]), from = W.rainFromH + r() * Math.max(0, W.rainToH - W.rainFromH - dur);
      return { dn: wk * 7 - 3 + di, from: +from.toFixed(3), to: +(from + dur).toFixed(3), hours: +dur.toFixed(3) };
    });
    if (wkCache.size > 64) wkCache.clear(); wkCache.set(key, out); return out;
  }
  function dayBase(seed, dn) {
    const W = C().weather, sp = rainSpells(seed, weekOf(dn));
    if (sp.some(x => x.dn === dn)) return W.rainDayBase || 'overcast';
    const w = W.weights, ks = Object.keys(w).filter(k => k !== 'rain'), tot = ks.reduce((a, k) => a + w[k], 0);
    let u = rngFor(seed, dn, 1)() * tot; for (const k of ks) { u -= w[k]; if (u < 0) return k; } return 'clear';
  }
  function hourIn(ms) { const d = new Date(ms); return d.getHours() + d.getMinutes() / 60 + d.getSeconds() / 3600; }
  /* 某時刻天氣：落緊雨（喺某場雨入面）→ 'rain'；否則當日底色 */
  function weatherAt(ms, seed) {
    seed = seed >>> 0; const dn = dayNum(ms), h = hourIn(ms);
    const sp = rainSpells(seed, weekOf(dn)).find(x => x.dn === dn && h >= x.from && h < x.to);
    return sp ? 'rain' : dayBase(seed, dn);
  }
  /* 驗收：連續 N 日（每 10 分鐘取樣）統計雨場（連續落雨段）＋每週場數 */
  function simulate(seed, fromMs, days, stepMin) {
    stepMin = stepMin || 10; const steps = Math.round(days * 24 * 60 / stepMin), spells = [], hist = {};
    let cur = null;
    for (let i = 0; i < steps; i++) {
      const t = fromMs + i * stepMin * 60000, w = weatherAt(t, seed); hist[w] = (hist[w] || 0) + 1;
      if (w === 'rain') { if (!cur) { cur = { start: t, end: t }; spells.push(cur); } cur.end = t + stepMin * 60000; } else cur = null;
    }
    const weeks = {}; spells.forEach(x => { const k = weekOf(dayNum(x.start)); weeks[k] = (weeks[k] || 0) + 1; });
    return { spells: spells.map(x => ({ day: SIM.dayKey(x.start), from: +hourIn(x.start).toFixed(2), hours: +((x.end - x.start) / 3600e3).toFixed(2) })), weeks, hist };
  }

  // ── 系統 7：季節（香港月份）──
  function seasonOf(ms) { const m = new Date(ms).getMonth() + 1, S = C().seasons; for (const k in S) if (S[k].includes(m)) return k; return 'autumn'; }
  const SEASON_NAME = { spring: '春', summer: '夏', autumn: '秋', winter: '冬' };
  const WEATHER_NAME = { clear: '晴', overcast: '陰', rain: '雨', fog: '霧' };

  /* 打冷震機率倍數（霧／冬 ×2，兩樣都係 ×4） */
  function shiverMul(weather, season) { const W = C().weather; return (weather === 'fog' ? W.shiverFogMul : 1) * (season === 'winter' ? W.shiverWinterMul : 1); }

  // ── 共用狀態 s.sys12（存檔入面；sanitize 喺 st()）──
  const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);
  function st(s) {
    let o = s.sys12; if (!o || typeof o !== 'object' || Array.isArray(o)) o = s.sys12 = {};
    o.v = 1;
    const w = o.wallet && typeof o.wallet === 'object' ? o.wallet : (o.wallet = {});
    w.total = Math.max(0, Math.floor(num(w.total, 0))); w.earned = Math.max(0, Math.floor(num(w.earned, 0)));
    if (!w.days || typeof w.days !== 'object' || Array.isArray(w.days)) w.days = {};
    for (const k of Object.keys(w.days)) { const e = w.days[k]; if (!/^\d{4}-\d\d-\d\d$/.test(k) || !e || typeof e !== 'object') { delete w.days[k]; continue; } e.q = Math.max(0, num(e.q, 0)); e.o = Math.max(0, num(e.o, 0)); }
    delete w.day; delete w.q; delete w.o;
    if (!Array.isArray(w.log)) w.log = []; if (w.log.length > 40) w.log = w.log.slice(-40);
    const q = o.quests && typeof o.quests === 'object' ? o.quests : (o.quests = {});
    if (typeof q.day !== 'string') q.day = ''; if (!Array.isArray(q.list)) q.list = [];
    q.list = q.list.filter(x => x && typeof x === 'object' && C().quests.kinds[x.k]).map(x => ({ k: x.k, need: Math.max(1, num(x.need, 1)), n: Math.max(0, num(x.n, 0)), route: D.BRANCH5.includes(x.route) ? x.route : null }));
    q.paid = !!q.paid; q.routePaid = !!q.routePaid;
    const B = C().bond, b = o.bond && typeof o.bond === 'object' ? o.bond : (o.bond = {});
    b.v = Math.max(0, Math.min(B.max, num(b.v, B.start))); b.gain = Math.max(0, num(b.gain, 0)); if (typeof b.day !== 'string') b.day = ''; if (typeof b.chk !== 'string') b.chk = '';
    b.gen = Math.max(1, Math.floor(num(b.gen, s.gen || 1))); b.lastVoice = Math.max(0, num(b.lastVoice, 0)); b.elder = b.elder == null ? null : num(b.elder, null);
    if (!Array.isArray(b.heard)) b.heard = []; b.heard = b.heard.filter(x => typeof x === 'string').slice(-60);
    const U = C().surprise, u = o.surp && typeof o.surp === 'object' ? o.surp : (o.surp = {});
    if (!u.on || typeof u.on !== 'object') u.on = {}; for (const k in U.defaults) u.on[k] = typeof u.on[k] === 'boolean' ? u.on[k] : U.defaults[k];
    if (!U.water.hours.includes(u.waterH)) u.waterH = U.water.def; if (!U.sleep.times.includes(u.sleepAt)) u.sleepAt = U.sleep.def;
    u.ts = Math.max(0, num(u.ts, 0)); if (!u.drops || typeof u.drops !== 'object' || Array.isArray(u.drops)) u.drops = {};
    for (const k of Object.keys(u.drops)) if (!/^\d{4}-\d\d-\d\d$/.test(k)) delete u.drops[k]; else u.drops[k] = Math.max(0, num(u.drops[k], 0));
    if (!Array.isArray(u.seen)) u.seen = []; u.seen = u.seen.filter(x => typeof x === 'string').slice(-40);
    return o;
  }
  const SYS = () => P.evo6.branch.systems;

  // ── 星星碎錢包：每日上限 30（委託 questCap＋其他 otherCap）；日界＝本機 00:00 ──
  function walletDay(s, key) { const w = st(s).wallet; if (!w.days[key]) { w.days[key] = { q: 0, o: 0 }; const ks = Object.keys(w.days).sort(); while (ks.length > 4) delete w.days[ks.shift()]; } return w.days[key] || { q: 0, o: 0 }; }
  /* src：'quest' 或其他（'drop'／'mg'…）；回實際入帳數（可能 0）。dayKey 可指定（補發舊日委託 → 計返嗰日嘅上限，唔食今日） */
  function grant(s, amt, src, nowMs, dayKey) {
    const W = C().wallet, key = dayKey || SIM.dayKey(nowMs), e = walletDay(s, key), w = st(s).wallet;
    const isQ = src === 'quest', sub = isQ ? W.questCap - e.q : W.otherCap - e.o, tot = SYS().stardustDailyCap - (e.q + e.o);
    const g = Math.max(0, Math.min(Math.floor(amt), sub, tot)); if (!g) return 0;
    if (isQ) e.q += g; else e.o += g; w.total += g; w.earned += g;
    w.log.push({ t: nowMs, d: key, src, n: g }); if (w.log.length > 40) w.log.shift();
    return g;
  }
  function wallet(s, nowMs) { const e = walletDay(s, SIM.dayKey(nowMs)), w = st(s).wallet; return { total: w.total, today: e.q + e.o, q: e.q, o: e.o, cap: SYS().stardustDailyCap, questCap: C().wallet.questCap, otherCap: C().wallet.otherCap }; }
  /* 用星星碎（之後：家具／種子）；唔夠 → false */
  function spend(s, n) { const w = st(s).wallet; n = Math.floor(n); if (!(n > 0) || w.total < n) return false; w.total -= n; return true; }

  // ── 系統 1：每日小委託 ──
  function questRoute(s) {                               // 領先路線（新 5 條之一）；未有領先 → 最高分嗰條；冇分 → null
    if (s.stage === 'egg') return null;
    try { const L = SIM.routeLead(s); if (D.BRANCH5.includes(L.form)) return L.form; return L.b5 && L.b5.topN > 0 ? L.b5.top : null; } catch (e) { return null; }
  }
  function genQuests(s, key) {
    const Q = C().quests, route = questRoute(s), rk = route && Q.routeKind[route], pool = Q.base.filter(k => k !== rk), list = [];
    const r = rngFor(s.seed >>> 0, +key.replace(/-/g, ''), 0x51);
    if (rk) list.push({ k: rk, need: Q.kinds[rk].n, n: 0, route });
    const p = pool.slice(); for (let i = p.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [p[i], p[j]] = [p[j], p[i]]; }
    for (const k of p) { if (list.length >= Q.perDay) break; list.push({ k, need: Q.kinds[k].n, n: 0, route: null }); }
    return list;
  }
  function questsDone(q) { return q.list.length > 0 && q.list.every(x => x.n >= x.need); }
  /* 每日檢查：補發舊日（3 個齊但未發）→ 00:00 換新委託；冇得出（光卵）→ 空 */
  function questTick(s, nowMs, ev) {
    const o = st(s), q = o.quests, key = SIM.dayKey(nowMs), out = { paid: 0, late: false, reset: false };
    if (q.day && questsDone(q) && !q.paid) { out.paid = payQuests(s, nowMs, q.day !== key ? q.day : null, ev); out.late = true; }
    if (q.day !== key && s.stage !== 'egg') { q.day = key; q.list = genQuests(s, key); q.paid = false; q.routePaid = false; out.reset = true; if (ev) ev.push({ type: 'sys12', sys: 'quest', what: 'new', list: q.list.map(x => x.k) }); }
    return out;
  }
  function payQuests(s, nowMs, oldKey, ev) {
    const Q = C().quests, q = st(s).quests; if (q.paid) return 0; q.paid = true;
    const g = grant(s, Q.reward * q.list.length, 'quest', nowMs, oldKey || null);
    if (ev) ev.push({ type: 'sys12', sys: 'quest', what: 'paid', n: g, late: !!oldKey });
    return g;
  }
  /* 照顧 hook（sim.addCareHook）：數委託進度；路線委託完成 → E.b5sys 加分（受 branch5Check 25% cap）；3 個齊 → 即刻發獎 */
  function onCare(s, kind, nowMs, ev) {
    if (s.stage === 'egg') return null; const o = st(s), q = o.quests; questTick(s, nowMs, ev);
    let hit = null; const K = C().quests.kinds;
    for (const x of q.list) if (x.n < x.need && K[x.k].counts.includes(kind)) { x.n++; hit = x; break; }
    if (!hit) return null;
    if (hit.n >= hit.need && hit.route && !q.routePaid) { q.routePaid = true; addRoutePts(s, hit.route, SYS().sources.questRoute.pts); }
    if (ev) ev.push({ type: 'sys12', sys: 'quest', what: 'step', k: hit.k, n: hit.n, need: hit.need });
    if (questsDone(q)) payQuests(s, nowMs, null, ev);
    return hit;
  }
  function addRoutePts(s, route, pts) {
    if (!SYS().enabled || !D.BRANCH5.includes(route) || s.stage === 'egg') return false;
    const E = s.evo && typeof s.evo === 'object' ? s.evo : (s.evo = { evIn: {}, care: {} });
    const m = E.b5sys || (E.b5sys = {}), b = m[s.stage] || (m[s.stage] = {}); b[route] = +((b[route] || 0) + pts).toFixed(4); return true;
  }
  function quests(s, nowMs) { const q = st(s).quests; return { day: q.day, paid: q.paid, done: questsDone(q), list: q.list.map(x => Object.assign({ label: C().quests.kinds[x.k].label, icon: C().quests.kinds[x.k].icon }, x)), reward: C().quests.reward }; }

  // ── 系統 6：親密度＋心聲 ──
  const BC = () => C().bond;
  function bondOf(s) { const b = st(s).bond; if (b.gen !== (s.gen || 1)) { b.gen = s.gen || 1; b.v = BC().start; b.gain = 0; b.day = ''; b.chk = ''; b.elder = null; b.heard = []; } return b; }   // 新一代由 start 開始
  function tierOf(v) { return Math.max(0, Math.min(BC().lines.length, Math.floor(v / BC().tierEvery))); }
  /* 加親密度（照顧 +1／長撳 +2）：每日加最多 dailyGainCap；回實際加咗幾多 */
  function bondAdd(s, n, nowMs, why, ev) {
    if (s.stage === 'egg') return 0; const B = BC(), b = bondOf(s), key = SIM.dayKey(nowMs);
    if (b.day !== key) { b.day = key; b.gain = 0; }
    const g = Math.max(0, Math.min(n, B.dailyGainCap - b.gain, B.max - b.v)); if (!g) return 0;
    const t0 = tierOf(b.v); b.v = +(b.v + g).toFixed(2); b.gain += g;
    const t1 = tierOf(b.v); if (ev && t1 > t0) ev.push({ type: 'sys12', sys: 'bond', what: 'tier', tier: t1, v: b.v });
    return g;
  }
  /* 每日檢查（tick／開 app）：由上次檢查到琴日，每個「完全冇照顧」嘅日 −ignoreDecay（最低 floor）；光卵唔計 */
  function bondTick(s, nowMs, ev) {
    const B = BC(), b = bondOf(s), today = dayNum(nowMs), out = { lost: 0, days: 0 };
    if (s.stage === 'elder' && b.elder == null) b.elder = Math.round(b.v);
    if (!b.chk) { b.chk = SIM.dayKey(nowMs - DAY); return out; }
    const care = new Set(Array.isArray(s.careDays) ? s.careDays : []);
    let dn = Math.round(Date.parse(b.chk + 'T00:00:00Z') / DAY) + 1; const maxN = 60;
    for (let n = 0; dn < today && n < maxN; dn++, n++) {
      const k = new Date(dn * DAY).toISOString().slice(0, 10);   // dayNum ↔ 本機日期 key
      if (s.stage !== 'egg' && !care.has(k)) { const nv = Math.max(B.floor, b.v - B.ignoreDecay); out.lost += b.v - nv; out.days++; b.v = nv; }
    }
    b.chk = SIM.dayKey(nowMs - DAY);
    if (out.lost && ev) ev.push({ type: 'sys12', sys: 'bond', what: 'decay', lost: out.lost, days: out.days, v: b.v });
    return out;
  }
  /* 心聲：撳一下 → chance 機會（冷卻 cooldownSec，懸浮＋主程式共用 b.lastVoice）；已解鎖段落入面抽，newestTierPct% 抽最新嗰段 */
  function voiceLines(s) { const b = bondOf(s), T = tierOf(b.v); return BC().lines.slice(0, T); }
  function voicePick(s, r) {
    const L = voiceLines(s); if (!L.length) return null; r = r || Math.random;
    const tier = r() * 100 < BC().voice.newestTierPct ? L.length - 1 : Math.floor(r() * L.length), arr = L[tier];
    return { tier: tier + 1, line: arr[Math.floor(r() * arr.length)] };
  }
  function voiceTry(s, nowMs, o) {
    o = o || {}; const V = BC().voice, b = bondOf(s), r = o.rng || Math.random;
    if (s.stage === 'egg') return { ok: false, why: 'egg' };
    if (!o.force && nowMs - b.lastVoice < V.cooldownSec * 1000) return { ok: false, why: 'cooldown', left: Math.ceil((V.cooldownSec * 1000 - (nowMs - b.lastVoice)) / 1000) };
    if (!o.force && r() >= V.chance) return { ok: false, why: 'roll' };
    const p = voicePick(s, r); if (!p) return { ok: false, why: 'locked' };
    b.lastVoice = nowMs; b.heard.push(p.line); if (b.heard.length > 60) b.heard.shift();
    return Object.assign({ ok: true, src: o.src || 'app' }, p);
  }
  function bond(s, nowMs) { const B = BC(), b = bondOf(s); return { v: b.v, tier: tierOf(b.v), tiers: B.lines.length, todayGain: b.day === SIM.dayKey(nowMs) ? b.gain : 0, cap: B.dailyGainCap, floor: B.floor, lastVoice: b.lastVoice, cooldownSec: B.voice.cooldownSec, chance: B.voice.chance, elder: b.elder, heard: b.heard.length }; }
  function onLongPress(s, nowMs, ev) { return bondAdd(s, BC().longPress, nowMs, 'press', ev); }

  // ── 系統 12：懸浮小驚喜（懸浮 native 自己計時；JS：設定＋入帳＋俾懸浮嘅 snapshot）──
  const UC = () => C().surprise;
  function surp(s) { return st(s).surp; }
  /* 改設定（主程式設定／懸浮設定同步，後改贏：ts） */
  function surpSet(s, key, val, nowMs) {
    const U = UC(), u = surp(s);
    if (key in U.defaults) u.on[key] = !!val; else if (key === 'waterH' && U.water.hours.includes(+val)) u.waterH = +val; else if (key === 'sleepAt' && U.sleep.times.includes(val)) u.sleepAt = val; else return false;
    u.ts = nowMs; return true;
  }
  function parseHM(t) { const m = /^(\d\d):(\d\d)$/.exec(t); return m ? +m[1] * 60 + +m[2] : 0; }
  /* 純函數（Kotlin PetSurprise 照抄＋單元測試）：下一粒星星碎時間（last 起計 minH–maxH；r∈[0,1)） */
  function dropNext(lastMs, r) { const D2 = UC().drop; return lastMs + (D2.minH + r * (D2.maxH - D2.minH)) * 3600e3; }
  /* 飲水提醒：而家應唔應該出（距上次 ≥ waterH、喺 fromH–toH 之間） */
  function waterDue(lastMs, waterH, nowMs) { const W = UC().water, h = new Date(nowMs).getHours(); return h >= W.fromH && h < W.toH && nowMs - lastMs >= waterH * 3600e3; }
  /* 早瞓提醒：今晚（sleepAt 起 winMin 分鐘內）未出過 → 出；00:00 當翌日凌晨（屬前一晚） */
  function sleepDue(sleepAt, lastNightKey, nowMs) {
    const W = UC().sleep, d = new Date(nowMs), m = d.getHours() * 60 + d.getMinutes(), at = parseHM(sleepAt), t = (m - at + 1440) % 1440;
    if (t >= W.winMin) return { due: false };
    const night = SIM.dayKey(nowMs - (at < 720 && m < 720 ? DAY : 0)); return { due: night !== lastNightKey, night };
  }
  /* 懸浮 queue replay：drop → 星星碎（每日 5 粒＋otherCap；閂咗唔入）；voice → 同步冷卻／記低；set → 設定（後改贏） */
  function applyOverlay(s, items, nowMs, ev) {
    const U = UC(), u = surp(s), out = { drop: 0, dropped: 0, voice: 0, set: 0, skip: 0 };
    for (const it of Array.isArray(items) ? items : []) {
      if (!it || typeof it !== 'object') { out.skip++; continue; } const t = Math.min(nowMs, num(+it.t, nowMs));
      if (it.k === 'drop') {
        const key = SIM.dayKey(t); out.dropped++;
        if (!u.on.drop || s.stage === 'egg' || (u.drops[key] || 0) >= U.drop.perDay) { out.skip++; continue; }
        const g = grant(s, U.drop.amt, 'drop', t, key); if (g) { u.drops[key] = (u.drops[key] || 0) + 1; out.drop += g; const ks = Object.keys(u.drops).sort(); while (ks.length > 4) delete u.drops[ks.shift()]; } else out.skip++;
      } else if (it.k === 'voice') {
        const b = bondOf(s); if (t > b.lastVoice) b.lastVoice = t; if (typeof it.line === 'string') { b.heard.push(it.line); if (b.heard.length > 60) b.heard.shift(); } out.voice++;
      } else if (it.k === 'set') {
        if (t >= u.ts && surpSet(s, it.key, it.val, t)) out.set++; else out.skip++;
      } else if (it.k === 'remind') { u.seen.push(it.what + '@' + SIM.dayKey(t)); if (u.seen.length > 40) u.seen.shift(); }
      else out.skip++;
    }
    if (ev && (out.drop || out.voice || out.set)) ev.push({ type: 'sys12', sys: 'surp', what: 'replay', drop: out.drop, voice: out.voice, set: out.set });
    return out;
  }
  /* 俾懸浮嘅 snapshot（fpet-bridge 寫入 snapshot.sys12）：親密／心聲（已解鎖句）＋小驚喜設定＋今日剩幾多粒 */
  function overlaySys12(s, nowMs) {
    const U = UC(), u = surp(s), b = bondOf(s), B = BC(), tier = tierOf(b.v), key = SIM.dayKey(nowMs), wl = wallet(s, nowMs), egg = s.stage === 'egg';
    const room = Math.max(0, Math.min(U.drop.perDay - (u.drops[key] || 0), wl.otherCap - wl.o, wl.cap - wl.today));
    return { v: 1, egg, bond: { v: Math.round(b.v), tier }, voice: { chance: B.voice.chance, cooldownSec: B.voice.cooldownSec, showSec: B.voice.showSec, newestTierPct: B.voice.newestTierPct, lastAt: b.lastVoice, lines: egg ? [] : B.lines.slice(0, tier) },
      surp: { on: Object.assign({}, u.on), waterH: u.waterH, sleepAt: u.sleepAt, ts: u.ts, drop: { minH: U.drop.minH, maxH: U.drop.maxH, perDay: U.drop.perDay, showSec: U.drop.showSec, day: key, room },
        water: { fromH: U.water.fromH, toH: U.water.toH }, sleepWinMin: U.sleep.winMin, showSec: U.showSec, lines: U.lines }, shards: wl.total };
  }

  // sim 照顧 hook：遊戲時鐘（sim.setNowFn）計日
  SIM.addCareHook((s, kind) => { const now = SIM.nowMs(), ev = Array.isArray(s.ev) ? s.ev : null; onCare(s, kind, now, ev); bondAdd(s, BC().care, now, 'care', ev); });
  // 化光：紀念冊記低親密度（靜光入面嗰陣＋化光嗰陣）
  SIM.addFadeHook((s, m) => { const b = bondOf(s); m.bond = Math.round(b.v); if (b.elder != null) m.bondElder = b.elder; });

  return { dayNum, dayStart, weekOf, hash, rngFor, rainSpells, dayBase, weatherAt, simulate, seasonOf, shiverMul, SEASON_NAME, WEATHER_NAME,
    st, grant, wallet, spend, bondOf, tierOf, bondAdd, bondTick, voiceLines, voicePick, voiceTry, bond, onLongPress, surp, surpSet, dropNext, waterDue, sleepDue, applyOverlay, overlaySys12, questRoute, genQuests, questTick, onCare, payQuests, addRoutePts, quests };
});
