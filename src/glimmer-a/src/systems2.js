/* 《微光小圃》 systems2.js — systems12 第 2 批（docs-gdd/systems12-v1.md 第 2 批；數值＝docs-gdd/systems12b-params.md）。原創代碼。
   系統 5 小遊戲（接光點／捉迷藏）→ 系統 2 小圃種花 → 系統 4 散步收集＋收藏櫃＋飾品 → 系統 11 成就徽章（30 個）。
   DOM-free、Node 可 require；狀態喺 s.sys12b；數值全部喺 data.js PARAMS.systems12b。
   星星碎：小遊戲／日菊經 systems.js grant（非委託 → 其他上限 15／日，總 30）；成就星星碎一次性、唔計每日上限（直接入錢包，log src 'badge'）。
   路線分經 systems.addRoutePts（25% cap 照舊）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'), require('./systems.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.sys12b = factory(root.Glimmer.data, root.Glimmer.sim, root.Glimmer.sys12); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM, X) {
  'use strict';
  const P = D.PARAMS, C = () => P.systems12b;
  const obj = v => v && typeof v === 'object' && !Array.isArray(v);
  const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);
  const now = t => (t == null ? SIM.nowMs() : t);
  const cnt = v => Math.max(0, num(v, 0) | 0);

  function st(s) {
    let o = s.sys12b; if (!obj(o)) o = s.sys12b = {};
    o.v = 2;
    const g = obj(o.games) ? o.games : (o.games = {}); g.day = typeof g.day === 'string' ? g.day : ''; g.plays = cnt(g.plays);
    g.total = cnt(g.total); if (!obj(g.best)) g.best = {}; if (!obj(g.stars)) g.stars = {}; g.hideFirst = cnt(g.hideFirst); if (!Array.isArray(g.log)) g.log = [];
    const G = obj(o.garden) ? o.garden : (o.garden = {}); if (!Array.isArray(G.pots)) G.pots = [];
    while (G.pots.length < C().garden.pots) G.pots.push(null); G.pots.length = C().garden.pots;
    G.pots = G.pots.map(p => (obj(p) && typeof p.k === 'string' && isFinite(p.planted) ? Object.assign({ w: [], paid: false }, p, { w: Array.isArray(p.w) ? p.w.filter(isFinite) : [] }) : null));
    if (!obj(G.vase)) G.vase = {}; if (!obj(G.bloomed)) G.bloomed = {}; if (!obj(G.hint)) G.hint = {}; G.wilts = cnt(G.wilts);
    for (const r of Object.keys(G.hint)) if (!(s.dexHint && s.dexHint[r])) SIM.noteDexHint(s, r, C().garden.daisy.k, G.hint[r]);   /* 舊存檔：小圃提示補入圖鑑 */
    const W = obj(o.walk) ? o.walk : (o.walk = {}); W.day = typeof W.day === 'string' ? W.day : ''; W.count = cnt(W.count);
    W.total = cnt(W.total); if (!obj(W.got)) W.got = {}; if (!Array.isArray(W.log)) W.log = []; W.acc = cnt(W.acc);
    const B = obj(o.badges) ? o.badges : (o.badges = {}); if (!obj(B.got)) B.got = {}; B.pending = cnt(B.pending);
    B.title = typeof B.title === 'string' ? B.title : ''; if (!Array.isArray(B.titles)) B.titles = [];
    const T = obj(o.stats) ? o.stats : (o.stats = {}); T.lull = cnt(T.lull); T.lullNight = cnt(T.lullNight); T.quick = cnt(T.quick);
    if (!obj(o.wx)) o.wx = {};
    if (!Array.isArray(o.seen)) o.seen = [];
    return o;
  }
  function note(o, arr, e, max) { arr.push(e); if (arr.length > (max || 30)) arr.shift(); }
  function wxNow(s, t) { return SIM.weatherNow ? SIM.weatherNow() : X.weatherAt(t, (s.seed >>> 0) || 1); }

  // ── 系統 5：小遊戲 ──
  /* 星數 0–3：接光點按分數、捉迷藏按總分（starsAt＝1／2／3★ 門檻） */
  const V2 = { bounce: 1, ghide: 1, firefly: 1 };   // 小遊戲 v2（PARAMS.minigames2）
  function gameStars(kind, v) { const a = (V2[kind] ? D.PARAMS.minigames2[kind] : kind === 'catch' ? C().games.catch : C().games.hide).starsAt; let n = 0; for (let i = 0; i < a.length; i++) if (v >= a[i]) n = i + 1; return Math.min(3, n); }
  /* 一局完：頭 dailyRewarded 局（兩隻合計）有星星碎（＝星數）；每局都計 mg（火苗分）；唔加光粒／心情
     o.noMg：浮動團絨嗰局（mg 已由 overlayOpenGame 計）；o.firstHits：捉迷藏第 1 下就搵到嘅回合數（成就） */
  function gameFinish(s, kind, v, nowMs, opt) {
    if (kind !== 'catch' && kind !== 'hide' && !V2[kind]) throw new Error('sys12b.gameFinish: kind');
    opt = opt || {};
    const t = now(nowMs), G = C().games, o = st(s), g = o.games, key = SIM.dayKey(t);
    if (g.day !== key) { g.day = key; g.plays = 0; }
    const stars = gameStars(kind, v), rewarded = g.plays < G.dailyRewarded; g.plays++; g.total++;
    g.best[kind] = Math.max(num(g.best[kind], 0), v); g.stars[kind] = Math.max(num(g.stars[kind], 0), stars);
    if ((kind === 'hide' || kind === 'ghide') && opt.firstHits > 0) g.hideFirst += opt.firstHits | 0;
    const want = rewarded ? (G.shardsByStars[stars] | 0) : 0, shards = want ? X.grant(s, want, 'mg', t) : 0;
    const counted = G.countsMg && !opt.noMg ? SIM.mgCount(s, t) : false;   // 火苗路線分：每局 minigames2.routePtsPerGame、每日 routeGamesPerDay 局（同浮動局共用）
    const r = { kind, value: v, stars, rewarded, want, shards, playIndex: g.plays, left: Math.max(0, G.dailyRewarded - g.plays), counted, overlay: !!opt.overlay };
    note(o, g.log, { t, kind, v, stars, shards }); s.ev && s.ev.push({ type: 'sys12', sys: 'game', what: 'done', game: kind, n: shards, stars, rewarded, overlay: !!opt.overlay });
    return r;
  }
  function gamesToday(s, nowMs) { const g = st(s).games, key = SIM.dayKey(now(nowMs)), plays = g.day === key ? g.plays : 0; return { plays, left: Math.max(0, C().games.dailyRewarded - plays), cap: C().games.dailyRewarded }; }
  /* 接光點參數（SIM.Minigame 覆寫）：30 秒；普通／金／暗光點 */
  function catchParams() { const c = C().games.catch; return { durationSec: c.durationSec, starScore: c.dots.small, bigStarScore: c.dots.big, stonePenalty: -c.dots.dark, stoneProb: c.stoneProb, bigStarProb: c.bigStarProb }; }
  /* 捉迷藏：3 回合；每回合團絨匿喺 5 個固定位其中 1 個；每回合最多撳 3 次（第 1／2／3 次搵到 3／2／1 分）；30% 露尾；限時 45 秒 */
  class HideGame {
    constructor(seed) {
      const H = C().games.hide; this.H = H; this.rng = SIM.makeRng(seed || 777); this.round = 0; this.found = 0; this.score = 0; this.firstHits = 0; this.t = 0; this.over = false; this.log = [];
      this.spots = H.spotNames.slice(0, H.spots); this.next();
    }
    next() { this.at = Math.floor(this.rng() * this.spots.length); this.tries = this.H.triesPerRound; this.tried = []; this.tail = this.rng() < this.H.tailChance; }
    pick(i) {
      if (this.over || i < 0 || i >= this.spots.length || this.tried.includes(i)) return { ok: false };
      this.tried.push(i); const hit = i === this.at, tryN = this.tried.length; this.tries--;
      const pts = hit ? (this.H.ptsByTry[tryN - 1] | 0) : 0;
      const r = { ok: true, hit, at: this.at, tryN, pts, tail: this.tail, round: this.round, roundOver: hit || this.tries <= 0 };
      if (hit) { this.found++; this.score += pts; if (tryN === 1) this.firstHits++; }
      if (r.roundOver) { this.log.push({ hit, tryN, pts, tail: this.tail }); this.round++; if (this.round >= this.H.rounds) this.over = true; else this.next(); }
      r.over = this.over; r.score = this.score; return r;
    }
    update(dt) { if (this.over) return; this.t += dt; if (this.t >= this.H.timeLimitSec) { this.t = this.H.timeLimitSec; this.over = true; } }
    get left() { return Math.max(0, this.H.timeLimitSec - this.t); }
  }
  /* 浮動團絨撳兩下開 game（SIM.overlayOpenGame）＝一局接光點 score overlayScore（40＝2★）：照計有獎局數＋星星碎；mg 已計，唔重複 */
  if (SIM.overlayOpenGame && !SIM.overlayOpenGame.__s12b) {
    const orig = SIM.overlayOpenGame;
    SIM.overlayOpenGame = function (s, t) { const r = orig.apply(this, arguments); if (r && r.ok) r.sys12b = gameFinish(s, 'catch', C().games.overlayScore, t == null ? SIM.nowMs() : +t, { noMg: true, overlay: true }); return r; };
    SIM.overlayOpenGame.__s12b = true;
  }

  // ── 系統 2：小圃種花 ──
  const FL = k => C().garden.flowers.find(f => f.k === k) || null;
  /* 花盆狀態（純計算）：每個有淋水嘅日子升 1 階（今日淋咗即升）；growSteps 階 → 開花；
     今日之前連續冇淋水 dry 日：≥droopDryDays＝垂頭（今日淋咗就冇事）、≥wiltDryDays＝枯 */
  function potInfo(p, nowMs) {
    if (!p) return { empty: true };
    const Gc = C().garden, today = X.dayNum(now(nowMs)), w = new Set(p.w), f = FL(p.k);
    let growth = 0, dry = 0, wilted = false, bloomDay = null;
    for (let d = p.planted; d <= today; d++) {
      if (w.has(d)) { growth++; dry = 0; if (growth >= Gc.growSteps) { bloomDay = d; break; } }
      else if (d < today && ++dry >= Gc.wiltDryDays) { wilted = true; break; }
    }
    const bloomed = bloomDay != null, wateredToday = w.has(today), droop = !bloomed && !wilted && dry >= Gc.droopDryDays;
    const stage = bloomed ? 3 : wilted ? -1 : Math.min(Gc.stages - 2, growth);
    return { empty: false, k: p.k, name: f ? f.name : p.k, route: f ? f.route : null, growth, need: Gc.growSteps, dry, droop, wilted, bloomed, bloomDay, wateredToday, stage, paid: !!p.paid };
  }
  function plant(s, i, k, nowMs) {
    const o = st(s), Gc = C().garden, t = now(nowMs);
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (!(i >= 0 && i < Gc.pots)) return { ok: false, reason: 'pot' };
    if (o.garden.pots[i]) return { ok: false, reason: 'busy' };
    if (!FL(k)) return { ok: false, reason: 'seed' };
    if (!X.spend(s, Gc.seedPrice)) return { ok: false, reason: 'shards' };
    o.garden.pots[i] = { k, planted: X.dayNum(t), w: [], paid: false };
    return { ok: true, price: Gc.seedPrice };
  }
  function water(s, i, nowMs) {
    const o = st(s), p = o.garden.pots[i]; if (!p) return { ok: false, reason: 'empty' };
    const I = potInfo(p, nowMs); if (I.wilted) return { ok: false, reason: 'wilted' }; if (I.bloomed) return { ok: false, reason: 'bloomed' };
    const d = X.dayNum(now(nowMs)); if (p.w.includes(d)) return { ok: false, reason: 'done' };
    p.w.push(d); if (p.w.length > 10) p.w.shift();
    const bloom = gardenTick(s, nowMs).filter(b => b.pot === i)[0] || null;
    return { ok: true, info: potInfo(p, nowMs), bloom };
  }
  /* tick：新開花 → 路線 +bloomPts（一次）；日菊 → +2 星星碎＋燦光圖鑑提示。枯咗 → 花冇咗（清盆，種子唔退） */
  function gardenTick(s, nowMs) {
    const o = st(s), Gc = C().garden, t = now(nowMs), out = [];
    o.garden.pots.forEach((p, i) => {
      if (!p) return; const I = potInfo(p, t);
      if (I.wilted) { o.garden.pots[i] = null; o.garden.wilts++; s.ev && s.ev.push({ type: 'sys12', sys: 'garden', what: 'wilt', k: p.k, name: I.name, n: 0 }); return; }
      if (p.paid || !I.bloomed) return;
      p.paid = true; o.garden.bloomed[p.k] = (o.garden.bloomed[p.k] | 0) + 1;
      const r = { pot: i, k: p.k, name: I.name, route: I.route, pts: 0, shards: 0, hint: null };
      if (p.k === Gc.daisy.k) { r.shards = X.grant(s, Gc.daisy.shards, 'garden', t); o.garden.hint[Gc.daisy.hint] = t; SIM.noteDexHint(s, Gc.daisy.hint, Gc.daisy.k, t); r.hint = { route: Gc.daisy.hint, text: D.ROUTE_HINT[Gc.daisy.hint] || '' }; }
      else if (X.addRoutePts(s, I.route, Gc.bloomPts)) r.pts = Gc.bloomPts;
      out.push(r);
      s.ev && s.ev.push({ type: 'sys12', sys: 'garden', what: 'bloom', k: p.k, name: I.name, route: I.route, n: r.shards, pts: r.pts, hint: r.hint });
    });
    return out;
  }
  /* 開咗嘅花剪落花瓶（第 3 批房間先擺得）；枯咗嘅清走（團絨冇事） */
  function harvest(s, i, nowMs) {
    const o = st(s), p = o.garden.pots[i]; if (!p) return { ok: false, reason: 'empty' };
    const I = potInfo(p, nowMs);
    if (I.bloomed) { gardenTick(s, nowMs); o.garden.vase[p.k] = (o.garden.vase[p.k] | 0) + 1; o.garden.pots[i] = null; return { ok: true, k: p.k, vase: true }; }
    if (I.wilted) { o.garden.pots[i] = null; return { ok: true, k: p.k, cleared: true }; }
    return { ok: false, reason: 'growing' };
  }
  function garden(s, nowMs) { const o = st(s); return { pots: o.garden.pots.map(p => potInfo(p, nowMs)), vase: Object.assign({}, o.garden.vase), bloomed: Object.assign({}, o.garden.bloomed), hint: Object.keys(o.garden.hint).map(r => ({ route: r, text: D.ROUTE_HINT[r] || '' })), price: C().garden.seedPrice, flowers: C().garden.flowers }; }

  // ── 系統 4：散步收集＋收藏櫃＋飾品 ──
  const IT = k => C().walk.items.find(x => x.k === k) || null;
  function inHours(h, a) { if (!a) return true; return a[0] <= a[1] ? h >= a[0] && h < a[1] : h >= a[0] || h < a[1]; }
  function streak(o, today) { let n = 0; const set = new Set(o.seen); while (set.has(today - n)) n++; return n; }
  /* 合唔合條件（ctx：weather、month、hour、dn、form＝守夜者之後嘅路線） */
  function eligible(it, ctx, o) {
    if (it.route && ctx.form !== it.route) return false;
    if (it.months && !it.months.includes(ctx.month)) return false;
    if (it.hours && !inHours(ctx.hour, it.hours)) return false;
    if (it.night && !inHours(ctx.hour, C().walk.nightHours)) return false;   /* 夜晚小物＝月眠時段 20–03（唔係螢絨進化嘅 17–07） */
    if (it.loginStreak && streak(o, ctx.dn) < it.loginStreak) return false;
    const afterRain = it.afterRainH != null && ctx.prevWeather === 'rain' && ctx.weather !== 'rain' && ctx.hourOfDay < it.afterRainH;
    if (it.onlyAfterRain) return afterRain;
    if (it.weather && !(it.weather.includes(ctx.weather) || afterRain)) return false;
    return true;
  }
  function walkCtx(s, nowMs, extra) {
    const t = now(nowMs), d = new Date(t), seed = (s.seed >>> 0) || 1, dn = X.dayNum(t), Sx = SIM.STAGES;
    const c = { t, dn, month: d.getMonth() + 1, hour: d.getHours(), hourOfDay: d.getHours() + d.getMinutes() / 60, weather: wxNow(s, t),
      prevWeather: X.dayWeatherN(seed, dn - 1), lead: SIM.routeLead && s.stage !== 'egg' ? (SIM.routeLead(s) || {}).form || null : null,
      form: Sx.indexOf(s.stage) >= Sx.indexOf('adult') ? s.form || null : null, rng: Math.random };
    return Object.assign(c, extra || {});
  }
  function seen(s, nowMs) { const o = st(s), dn = X.dayNum(now(nowMs)); if (!o.seen.includes(dn)) { o.seen.push(dn); o.seen.sort((a, b) => a - b); if (o.seen.length > 14) o.seen.shift(); } }
  const uniqueOf = w => Object.keys(w.got).filter(k => IT(k) && w.got[k] > 0).length;
  /* 團絨開始行一段路 → 擲一次：總執到率 ≤ chance（10%）。中咗 → 稀有逐件（條件機率 pct×routeMul÷chance，即絕對機率＝pct）→ 否則合條件普通小物抽一件；
     每日最多 perDay；保底 pity；每 accPer 件唔同小物解鎖 1 件飾品 */
  function walkRoll(s, nowMs, extra) {
    const Wc = C().walk, o = st(s), w = o.walk, c = walkCtx(s, nowMs, extra), key = SIM.dayKey(c.t);
    if (s.stage === 'egg') return null;
    seen(s, c.t); o.wx[c.weather] = 1;
    if (w.day !== key) { w.day = key; w.count = 0; }
    if (w.count >= Wc.perDay) return null;
    const rng = c.rng; if (!c.force && !(rng() < Wc.chance)) return null;
    const el = Wc.items.filter(it => eligible(it, c, o));
    let got = null;
    if (!c.noRare) for (const it of el) if (it.rare && it.pct) { const mul = it.routeMul && c.lead && it.routeMul[c.lead] ? it.routeMul[c.lead] : 1; if (rng() < it.pct * mul / Wc.chance) { got = it; break; } }
    if (!got) { const com = el.filter(it => !it.rare); if (com.length) got = com[Math.floor(rng() * com.length)]; }
    if (!got) return null;
    const pityIt = Wc.items.find(it => it.pity && !w.got[it.k] && w.total + 1 >= it.pity); if (pityIt) got = pityIt;
    w.count++; w.total++; const first = !w.got[got.k]; w.got[got.k] = (w.got[got.k] | 0) + 1;
    note(o, w.log, { t: c.t, k: got.k });
    s.ev && s.ev.push({ type: 'sys12', sys: 'walk', what: 'pickup', k: got.k, name: got.name, first, n: 0 });
    const acc = accCheck(s);
    return { k: got.k, name: got.name, first, count: w.count, left: Wc.perDay - w.count, total: w.total, pity: !!pityIt, acc };
  }
  /* 飾品：unique ÷ accPer（最多 6）；新解鎖 → 通知 */
  function accCheck(s) {
    const Wc = C().walk, w = st(s).walk, n = Math.min(Wc.accessories.length, Math.floor(uniqueOf(w) / Wc.accPer)), out = [];
    while (w.acc < n) { const a = Wc.accessories[w.acc++]; out.push(a); s.ev && s.ev.push({ type: 'sys12', sys: 'walk', what: 'acc', k: a.k, name: a.name, n: 0 }); }
    return out;
  }
  function accessories(s) { const Wc = C().walk, w = st(s).walk, u = uniqueOf(w); return Wc.accessories.map((a, i) => ({ k: a.k, name: a.name, note: a.note || '', got: i < w.acc, need: (i + 1) * Wc.accPer, unique: u })); }
  /* 收藏櫃：30 格；未收集＝剪影；ph＝佔位 icon（未有美術） */
  function cabinet(s) {
    const Wc = C().walk, w = st(s).walk, out = [];
    for (let i = 0; i < Wc.slots; i++) { const it = Wc.items[i]; out.push(it ? { k: it.k, name: w.got[it.k] ? it.name : '？', got: w.got[it.k] | 0, rare: !!it.rare, route: it.route || null, ph: !!it.ph } : { k: null, name: '？', got: 0, locked: true }); }
    return { slots: out, unique: uniqueOf(w), total: w.total, today: w.day === SIM.dayKey(SIM.nowMs()) ? w.count : 0, perDay: Wc.perDay, acc: accessories(s) };
  }

  // ── 系統 11：成就徽章 ──
  function keyDn(k) { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(k || ''); return m ? X.dayNum(new Date(+m[1], +m[2] - 1, +m[3], 12).getTime()) : null; }
  function careStreak(s) { const a = (Array.isArray(s.careDays) ? s.careDays : []).map(keyDn).filter(v => v != null).sort((x, y) => x - y); let best = 0, run = 0, prev = null; for (const d of a) { run = prev != null && d === prev + 1 ? run + 1 : d === prev ? run : 1; prev = d; best = Math.max(best, run); } return best; }
  function met(s, when) {
    const o = st(s), Sx = SIM.STAGES, dex = s.dex || [];
    if (when.stageAtLeast) return Sx.indexOf(s.stage) >= Sx.indexOf(when.stageAtLeast) || dex.length > 0 || (s.memorial || []).length > 0 || (s.gen | 0) > 1 ||
      (when.stageAtLeast === 'newborn' && (s.stats && s.stats.hatches > 0));
    if (when.dex) return dex.includes(when.dex);
    if (when.dexAll) return D.BRANCHES.every(f => dex.includes(f));
    if (when.collected) return uniqueOf(o.walk) >= when.collected;
    if (when.careStreak) return careStreak(s) >= when.careStreak;
    if (when.lull) return o.stats.lull >= when.lull;
    if (when.lullNight) return o.stats.lullNight >= when.lullNight;
    if (when.quick) return o.stats.quick >= when.quick;
    if (when.catchStars) return num(o.games.stars.catch, 0) >= when.catchStars;
    if (when.bounceStars) return num(o.games.stars.bounce, 0) >= when.bounceStars;   // v2：徽章「彈彈葉 3★」只計彈彈葉
    if (when.hideFirst) return o.games.hideFirst >= when.hideFirst;
    if (when.bloomKinds) return Object.keys(o.garden.bloomed).filter(k => FL(k)).length >= when.bloomKinds;
    if (when.acc) return o.walk.acc >= when.acc;
    if (when.quests) return cnt(X.st(s).quests.paidN) >= when.quests;
    if (when.weathers) return Object.keys(o.wx).length >= when.weathers;
    if (when.diary) return (X.st(s).diary.list || []).length >= when.diary;
    if (when.dumbAll) { const sn = s.touch && s.touch.seen; return !!sn && typeof sn === 'object' && Object.keys(sn).filter(k => sn[k]).length >= when.dumbAll; }   // 3a 圖鑑「呆呆時刻」6 格
    if (when.friend) { const v = s.b3b && s.b3b.vis && s.b3b.vis[when.friend]; return !!(v && typeof v === 'object' && (v.fr | 0) >= 5); }   // 3b 朋友訪客友好度滿 5
    if (when.fade) return (s.memorial || []).length >= when.fade || (s.gen | 0) > when.fade;
    return false;
  }
  /* 成就星星碎：一次性、唔計每日 30 上限 → 直接入錢包（total／earned＋log），唔郁今日 q／o 計數 */
  function payBadge(s, n, t) { const w = X.st(s).wallet; n = Math.max(0, Math.floor(n)); if (!n) return 0; w.total += n; w.earned += n; w.log.push({ t, d: SIM.dayKey(t), src: 'badge', n }); if (w.log.length > 40) w.log.shift(); return n; }
  /* 檢查新徽章（唔重覆給）：一般 reward、大成就 bigReward＋稱號 */
  function badgeCheck(s, nowMs) {
    const t = now(nowMs), Bc = C().badges, o = st(s), B = o.badges, out = [];
    if (B.pending) { payBadge(s, B.pending, t); B.pending = 0; }   // 舊版（徽章食上限）待補發 → 一次過入錢包
    for (const b of Bc.list) {
      if (B.got[b.k] || !met(s, b.when)) continue;
      B.got[b.k] = t; const g = payBadge(s, b.big ? Bc.bigReward : Bc.reward, t);
      const title = b.title || ''; if (title) { B.title = title; if (!B.titles.includes(title)) B.titles.push(title); }
      out.push({ k: b.k, name: b.name, big: !!b.big, title, shards: g });
      s.ev && s.ev.push({ type: 'sys12', sys: 'badge', what: 'got', k: b.k, name: b.name, big: !!b.big, title, n: g });
    }
    return out;
  }
  function badges(s) { const Bc = C().badges, B = st(s).badges; return { list: Bc.list.map(b => ({ k: b.k, name: b.name, big: !!b.big, title: b.title || '', reward: b.big ? Bc.bigReward : Bc.reward, got: !!B.got[b.k], at: B.got[b.k] || null })), total: Bc.total, have: Bc.list.filter(b => B.got[b.k]).length, title: B.title, titles: B.titles.slice() }; }

  /* 照顧 hook：哄瞓（每晚第幾次＝s.evo.lull.n）、即清便便 → 成就計數 */
  if (SIM.addCareHook) SIM.addCareHook((s, kind) => {
    if (!s || (kind !== 'lull' && kind !== 'poopQuick')) return; const T = st(s).stats;
    if (kind === 'lull') { T.lull++; T.lullNight = Math.max(T.lullNight, (s.evo && s.evo.lull && s.evo.lull.n) | 0); } else T.quick++;
  });

  function tick(s, nowMs) { if (!s || s.stage === undefined) return null; const t = now(nowMs); seen(s, t); st(s).wx[wxNow(s, t)] = 1; return { bloom: gardenTick(s, t), badges: badgeCheck(s, t) }; }

  return { st, gameStars, gameFinish, gamesToday, catchParams, HideGame, potInfo, plant, water, gardenTick, harvest, garden, eligible, walkCtx, walkRoll, accCheck, accessories, cabinet, streak, seen, careStreak, met, payBadge, badgeCheck, badges, tick };
});
