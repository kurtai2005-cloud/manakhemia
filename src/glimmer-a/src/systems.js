/* 《微光小圃》 systems.js — systems12 第 1 批（docs-gdd/systems12-v1.md）。原創代碼。
   DOM-free、Node 可 require（純邏輯＋狀態）；main.js 掛入遊戲迴圈，devpanel 加觸發掣。數值全部喺 data.js PARAMS.systems12／evo6.branch.systems。
   系統 7 天氣／季節：v10.2 每日一抽（真實日期＋seed；晴60／陰20／雨15／霧5，成日不變）；季節跟香港月份。 */
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

  // ── 系統 7：天氣（v10.2：一日一抽）──
  /* 每日（本機 00:00 起）用 seed＋日數抽一次：晴 60／陰 20／雨 15／霧 5（evo6.branch.weather.probs），成日都係呢個天氣。
     抽法喺 sim.js dayWeatherN（遊戲／日記／route-sweep 共用）；舊「每週落雨 1–3 次、每次 1–3h」已刪。
     天氣冇入存檔（純 seed＋日期計）→ 舊存檔讀入即跟當日抽籤，唔會殘留雨窗。 */
  function weekOf(dn) { return Math.floor((dn + 3) / 7); }
  function dayWeatherN(seed, dn) { return SIM.dayWeatherN(seed >>> 0, dn); }
  function weatherAt(ms, seed) { return SIM.dayWeather(seed >>> 0, ms); }
  /* 驗收：連續 N 日（每 stepMin 分鐘取樣）→ 每日天氣（檢查成日一致）＋樣本 hist＋日數 dayHist */
  function simulate(seed, fromMs, days, stepMin) {
    stepMin = stepMin || 60; const steps = Math.round(days * 24 * 60 / stepMin), hist = {}, byDay = {}, order = [];
    let mixed = 0;
    for (let i = 0; i < steps; i++) {
      const t = fromMs + i * stepMin * 60000, w = weatherAt(t, seed), k = SIM.dayKey(t); hist[w] = (hist[w] || 0) + 1;
      if (!(k in byDay)) { byDay[k] = w; order.push(k); } else if (byDay[k] !== w) mixed++;
    }
    const dayHist = {}; order.forEach(k => { dayHist[byDay[k]] = (dayHist[byDay[k]] || 0) + 1; });
    return { days: order.map(k => ({ day: k, w: byDay[k] })), dayHist, hist, mixed };
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
    const dy = o.diary && typeof o.diary === 'object' && !Array.isArray(o.diary) ? o.diary : (o.diary = {});
    if (!Array.isArray(dy.list)) dy.list = []; dy.list = dy.list.filter(e => e && typeof e === 'object' && typeof e.d === 'string' && Array.isArray(e.lines)).slice(-C().diary.keepDays);
    if (dy.tr && (typeof dy.tr !== 'object' || typeof dy.tr.day !== 'string')) dy.tr = null; if (dy.tr === undefined) dy.tr = null;
    if (dy.tr) { const r = dy.tr; for (const k of ['foods', 'care', 'wx']) if (!r[k] || typeof r[k] !== 'object' || Array.isArray(r[k])) r[k] = {}; if (!Array.isArray(r.stages)) r.stages = []; if (!Array.isArray(r.mood) || r.mood.length !== 2) r.mood = [0, 0]; r.n = num(r.n, 0); r.mt = num(r.mt, 0); r.wt = num(r.wt, 0); r.gen = Math.max(1, Math.floor(num(r.gen, s.gen || 1))); }
    for (const k of ['wx', 'rain', 'rainWin', 'weather']) if (k in o) delete o[k];   // v10.2：天氣＝一日一抽（seed＋日期計，唔入存檔）→ 舊／外來雨窗欄位清走
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
  /* v10.2：路線委託平均分晒 5 條（唔再跟領先路線 → 火苗唔會因為領先而日日攞分）。
     每隻團絨（seed）有個起點，之後逐日輪：tide→shroom→crystal→moon→ember→…；任何連續 5 日每條路線剛好 1 次。 */
  function questRoute(s, key) {
    if (s.stage === 'egg') return null;
    const R = D.BRANCH5, dn = key ? dayNum(keyDate(key).getTime()) : dayNum(SIM.nowMs ? SIM.nowMs() : Date.now());
    return R[(((dn + hash(s.seed >>> 0, 0x51, 5) % R.length) % R.length) + R.length) % R.length];
  }
  function genQuests(s, key) {
    const Q = C().quests, route = questRoute(s, key), rk = route && Q.routeKind[route], pool = Q.base.filter(k => k !== rk), list = [];
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

  // ── 系統 3：團絨日記（每日 1 篇：範本＋當日事件；進化／化光有特別頁；離線日一句；留 30 日；化光入紀念冊）──
  const DC = () => C().diary;
  function dy(s) { return st(s).diary; }
  function keyDate(k) { const [y, m, d] = k.split('-').map(Number); return new Date(y, m - 1, d); }
  function newTr(s, key, nowMs, gen) { return { day: key, gen: gen || s.gen || 1, foods: {}, care: {}, n: 0, stages: [], st0: s.stage, stLast: s.stage, mood: [0, 0], mt: 0, wt: 0, wx: {}, fade: false }; }
  function fill(str, o) { return str.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m)); }
  function dayWeather(s, key, tr) {
    const ks = Object.keys(tr && tr.wx || {}); if (ks.length) return ks.sort((a, b) => tr.wx[b] - tr.wx[a])[0];
    return dayWeatherN(s.seed >>> 0, dayNum(keyDate(key).getTime()));
  }
  function buildEntry(s, tr) {
    const Dc = DC(), r = rngFor(s.seed >>> 0, +tr.day.replace(/-/g, ''), 0xd1 + (tr.gen | 0)), pick = (a) => a[Math.floor(r() * a.length)];
    const dt = keyDate(tr.day), date = (dt.getMonth() + 1) + ' 月 ' + dt.getDate() + ' 日', lines = [], stickers = [];
    lines.push(fill(pick(Dc.open), { date }));
    const wx = dayWeather(s, tr.day, tr); lines.push(pick(Dc.weather[wx] || Dc.weather.clear)); stickers.push(wx === 'rain' ? 'rain' : wx === 'clear' ? 'sun' : null);
    const fk = Object.keys(tr.foods), nf = fk.reduce((a, k) => a + tr.foods[k], 0), fname = fk.map(k => (D.FOODS.find(f => f.id === k) || { name: k }).name).join('、');
    if (tr.st0 !== 'egg' || tr.stLast !== 'egg') { lines.push(fill(pick(nf ? (nf > 1 ? Dc.food.many : Dc.food.one) : Dc.food.none), { food: fname, n: nf })); if (nf) stickers.push('food'); }
    const mv = tr.mood[1] ? tr.mood[0] / tr.mood[1] : null, band = mv == null ? 'ok' : mv > 60 ? 'happy' : mv < 30 ? 'sad' : 'ok'; lines.push(pick(Dc.mood[band]));
    if (tr.n >= 6) lines.push(pick(Dc.care.many)); else if (tr.n >= 1) lines.push(pick(Dc.care.few)); if (band === 'happy' || tr.n >= 6) stickers.push('heart');
    for (const sg of tr.stages) lines.push(fill(pick(Dc.evolve), { stage: D.STAGE_NAME[sg] || sg })); if (tr.stages.length) stickers.push('evolve');
    if (tr.fade) lines.push(pick(Dc.fade)); else lines.push(pick(Dc.close));
    if (tr.care.lull || tr.care.petSleep) stickers.push('sleep');
    const kind = tr.fade ? 'fade' : tr.stages.length ? 'evolve' : 'normal';
    return { d: tr.day, gen: tr.gen, kind, special: kind !== 'normal', lines, stickers: stickers.filter(Boolean), stage: tr.stLast, wx, mood: mv == null ? null : Math.round(mv), care: tr.n };
  }
  function pushEntry(s, e) { const L = dy(s).list; L.push(e); L.sort((a, b) => (a.d < b.d ? -1 : a.d > b.d ? 1 : a.gen - b.gen)); while (L.length > DC().keepDays) L.shift(); return e; }
  function worth(tr) { return tr.fade || tr.stages.length || tr.n > 0 || Object.keys(tr.foods).length || tr.st0 !== 'egg' || tr.stLast !== 'egg'; }
  /* 日界：舊日 tracker → 寫一篇；中間冇開 app 嘅日（離線日）→ 每日一句（光卵期唔寫） */
  function diaryTrack(s, nowMs, ev) {
    const o = dy(s), key = SIM.dayKey(nowMs); let tr = o.tr;
    if (!tr) { o.tr = newTr(s, key, nowMs); return o.tr; }
    if (tr.day === key) return tr;
    if (tr.day > key) { o.tr = newTr(s, key, nowMs); return o.tr; }        // 時鐘倒退：重開
    if (!tr.done && worth(tr)) { const e = pushEntry(s, buildEntry(s, tr)); if (ev) ev.push({ type: 'sys12', sys: 'diary', what: 'write', d: e.d, kind: e.kind }); }
    if (s.stage !== 'egg') {
      const Dc = DC(), d = keyDate(tr.day); let n = 0, wrote = 0;
      for (d.setDate(d.getDate() + 1); n < Dc.offlineMax; d.setDate(d.getDate() + 1), n++) {
        const k = SIM.dayKey(d.getTime()); if (k >= key) break;
        const r = rngFor(s.seed >>> 0, +k.replace(/-/g, ''), 0xd0), dt = keyDate(k);
        pushEntry(s, { d: k, gen: s.gen || 1, kind: 'offline', special: false, lines: [(dt.getMonth() + 1) + ' 月 ' + dt.getDate() + ' 日。' + Dc.offline[Math.floor(r() * Dc.offline.length)]], stickers: [], stage: s.stage, wx: null, mood: null, care: 0 }); wrote++;
      }
      if (wrote && ev) ev.push({ type: 'sys12', sys: 'diary', what: 'offline', n: wrote });
    }
    o.tr = newTr(s, key, nowMs); return o.tr;
  }
  /* 記事：food（id）／care（kind）／wx（天氣）／mood（取樣）；stage 由 step hook 偵測 */
  function diaryNote(s, what, val, nowMs) {
    const tr = diaryTrack(s, nowMs, Array.isArray(s.ev) ? s.ev : null);
    if (what === 'food') tr.foods[val] = (tr.foods[val] || 0) + 1;
    else if (what === 'care') { tr.care[val] = (tr.care[val] || 0) + 1; tr.n++; }
    else if (what === 'wx') { if (nowMs - tr.wt >= 60000 || !tr.wt) { tr.wx[val] = (tr.wx[val] || 0) + 1; tr.wt = nowMs; } }
    else if (what === 'mood') { tr.mood[0] += +val || 0; tr.mood[1]++; tr.mt = nowMs; }
    return tr;
  }
  function diaryStep(s, nowMs) {
    const tr = diaryTrack(s, nowMs, Array.isArray(s.ev) ? s.ev : null);
    if (tr.stLast !== s.stage) { if (s.stage !== 'egg' && SIM.STAGES.indexOf(s.stage) > SIM.STAGES.indexOf(tr.stLast)) tr.stages.push(s.stage); tr.stLast = s.stage; }
    if (s.stage !== 'egg' && s.needs && nowMs - tr.mt >= DC().moodSampleMin * 60000) diaryNote(s, 'mood', s.needs.mood, nowMs);
  }
  function diary(s, nowMs) { const tr = diaryTrack(s, nowMs, null), L = dy(s).list.filter(e => e.gen === (s.gen || 1)); return { list: L.slice(), all: dy(s).list.length, today: worth(tr) || s.stage !== 'egg' ? Object.assign(buildEntry(s, tr), { draft: true }) : null, keepDays: DC().keepDays }; }

  // sim 照顧 hook：遊戲時鐘（sim.setNowFn）計日
  SIM.addCareHook((s, kind) => { const now = SIM.nowMs(), ev = Array.isArray(s.ev) ? s.ev : null; onCare(s, kind, now, ev); if (kind === 'poopQuick') return;   /* v10 即清上線：只推委託；親密／日記已經由 'poop' 計 */ bondAdd(s, BC().care, now, 'care', ev); diaryNote(s, 'care', kind, now); });
  SIM.addStepHook((s) => { if (s && s.stage) diaryStep(s, SIM.nowMs()); });
  // 化光：紀念冊記低親密度（靜光入面嗰陣＋化光嗰陣）
  SIM.addFadeHook((s, m) => { const b = bondOf(s); m.bond = Math.round(b.v); if (b.elder != null) m.bondElder = b.elder; });
  // 化光：今日寫特別頁（化光）→ 呢代嘅日記入紀念冊；新一代由空白日記開始
  SIM.addFadeHook((s, m) => { const now = SIM.nowMs(), o = dy(s), tr = diaryTrack(s, now, null), g = s.gen || 1; tr.fade = true; tr.stLast = s.stage; pushEntry(s, buildEntry(s, tr));
    m.diary = o.list.filter(e => e.gen === g).map(e => ({ d: e.d, kind: e.kind, special: !!e.special, lines: e.lines.slice(), stickers: e.stickers.slice() })); o.list = o.list.filter(e => e.gen !== g);
    o.tr = newTr(s, tr.day, now, g + 1); o.tr.st0 = o.tr.stLast = 'egg'; });

  return { dayNum, dayStart, weekOf, hash, rngFor, dayWeatherN, weatherAt, simulate, questRoute, seasonOf, shiverMul, SEASON_NAME, WEATHER_NAME,
    st, grant, wallet, spend, bondOf, tierOf, bondAdd, bondTick, voiceLines, voicePick, voiceTry, bond, onLongPress, diaryTrack, diaryNote, diaryStep, diary, buildEntry, surp, surpSet, dropNext, waterDue, sleepDue, applyOverlay, overlaySys12, questRoute, genQuests, questTick, onCare, payQuests, addRoutePts, quests };
});
