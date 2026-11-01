/* 《微光小圃》 systems2.js — systems12 第 2 批（docs-gdd/systems12-v1.md 第 2 批）。原創代碼。
   系統 5 小遊戲（接光點／捉迷藏）→ 系統 2 小圃種花 → 系統 4 散步收集＋收藏櫃 → 系統 11 成就徽章。
   DOM-free、Node 可 require；狀態喺 s.sys12b；數值全部喺 data.js PARAMS.systems12b（規格冇寫嘅標 TBD 遊策）。
   星星碎經 systems.js grant（非委託 → 其他上限 15／日，總 30）；路線分經 systems.addRoutePts（25% cap 照舊）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'), require('./sim.js'), require('./systems.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.sys12b = factory(root.Glimmer.data, root.Glimmer.sim, root.Glimmer.sys12); }
})(typeof self !== 'undefined' ? self : this, function (D, SIM, X) {
  'use strict';
  const P = D.PARAMS, C = () => P.systems12b;
  const obj = v => v && typeof v === 'object' && !Array.isArray(v);
  const num = (v, d) => (typeof v === 'number' && isFinite(v) ? v : d);
  const now = t => (t == null ? SIM.nowMs() : t);

  function st(s) {
    let o = s.sys12b; if (!obj(o)) o = s.sys12b = {};
    o.v = 1;
    const g = obj(o.games) ? o.games : (o.games = {}); g.day = typeof g.day === 'string' ? g.day : ''; g.plays = Math.max(0, num(g.plays, 0) | 0);
    g.total = Math.max(0, num(g.total, 0) | 0); if (!obj(g.best)) g.best = {}; if (!Array.isArray(g.log)) g.log = [];
    const G = obj(o.garden) ? o.garden : (o.garden = {}); if (!Array.isArray(G.pots)) G.pots = [];
    while (G.pots.length < C().garden.pots) G.pots.push(null); G.pots.length = C().garden.pots;
    G.pots = G.pots.map(p => (obj(p) && typeof p.k === 'string' && isFinite(p.planted) ? Object.assign({ w: [], paid: false }, p, { w: Array.isArray(p.w) ? p.w.filter(isFinite) : [] }) : null));
    if (!obj(G.vase)) G.vase = {};
    const W = obj(o.walk) ? o.walk : (o.walk = {}); W.day = typeof W.day === 'string' ? W.day : ''; W.count = Math.max(0, num(W.count, 0) | 0);
    W.total = Math.max(0, num(W.total, 0) | 0); if (!obj(W.got)) W.got = {}; if (!Array.isArray(W.log)) W.log = [];
    const B = obj(o.badges) ? o.badges : (o.badges = {}); if (!obj(B.got)) B.got = {}; B.pending = Math.max(0, num(B.pending, 0) | 0);
    B.title = typeof B.title === 'string' ? B.title : '';
    if (!Array.isArray(o.seen)) o.seen = [];
    return o;
  }
  function note(o, arr, e, max) { arr.push(e); if (arr.length > (max || 30)) arr.shift(); }

  // ── 系統 5：小遊戲 ──
  /* 星數：接光點按分數線；捉迷藏按搵到幾輪。最少 1 星（規格：每局 1–3 星星碎） */
  function gameStars(kind, v) {
    const G = C().games;
    if (kind === 'catch') { const a = G.catch.starsAt; let n = 1; for (let i = 1; i < a.length; i++) if (v >= a[i]) n = i + 1; return Math.min(3, Math.max(1, n)); }
    const a = G.hide.starsByFound; return Math.min(3, Math.max(1, a[Math.max(0, Math.min(a.length - 1, v | 0))] | 0));
  }
  /* 一局完：頭 dailyRewarded 局（兩隻合計）有星星碎；每局都計 mg（火苗分）；唔加光粒／心情 */
  function gameFinish(s, kind, v, nowMs) {
    if (kind !== 'catch' && kind !== 'hide') throw new Error('sys12b.gameFinish: kind');
    const t = now(nowMs), G = C().games, o = st(s), g = o.games, key = SIM.dayKey(t);
    if (g.day !== key) { g.day = key; g.plays = 0; }
    const stars = gameStars(kind, v), rewarded = g.plays < G.dailyRewarded; g.plays++; g.total++;
    g.best[kind] = Math.max(num(g.best[kind], 0), v);
    const want = rewarded ? (G.shardsByStars[stars] | 0) : 0, shards = want ? X.grant(s, want, 'mg', t) : 0;
    const counted = G.countsMg ? SIM.mgCount(s) : false;
    const r = { kind, value: v, stars, rewarded, want, shards, playIndex: g.plays, left: Math.max(0, G.dailyRewarded - g.plays), counted };
    note(o, g.log, { t, kind, v, stars, shards }); s.ev && s.ev.push({ type: 'sys12', sys: 'game', what: 'done', game: kind, n: shards, stars, rewarded });
    return r;
  }
  function gamesToday(s, nowMs) { const g = st(s).games, key = SIM.dayKey(now(nowMs)), plays = g.day === key ? g.plays : 0; return { plays, left: Math.max(0, C().games.dailyRewarded - plays), cap: C().games.dailyRewarded }; }
  /* 接光點參數（SIM.Minigame 覆寫）：30 秒；3 種光點＝細／大／暗（分數用 config） */
  function catchParams() { const c = C().games.catch; return { durationSec: c.durationSec, starScore: c.dots.small, bigStarScore: c.dots.big, stonePenalty: -c.dots.dark, stoneProb: c.stoneProb, bigStarProb: c.bigStarProb }; }
  /* 捉迷藏：每輪 3–5 個匿位（rng），團絨匿喺其中一個；每輪 triesPerRound 次；限時 timeLimitSec */
  class HideGame {
    constructor(seed) {
      const H = C().games.hide; this.H = H; this.rng = SIM.makeRng(seed || 777); this.round = 0; this.found = 0; this.t = 0; this.over = false; this.log = [];
      this.next();
    }
    next() {
      const H = this.H, n = H.spots[0] + Math.floor(this.rng() * (H.spots[1] - H.spots[0] + 1));
      const names = H.spotNames.slice(); for (let i = names.length - 1; i > 0; i--) { const j = Math.floor(this.rng() * (i + 1)); [names[i], names[j]] = [names[j], names[i]]; }
      this.spots = names.slice(0, n); this.at = Math.floor(this.rng() * n); this.tries = H.triesPerRound; this.tried = [];
    }
    pick(i) {
      if (this.over || i < 0 || i >= this.spots.length || this.tried.includes(i)) return { ok: false };
      this.tried.push(i); const hit = i === this.at; this.tries--;
      const r = { ok: true, hit, at: this.at, round: this.round, roundOver: hit || this.tries <= 0 };
      if (hit) this.found++;
      if (r.roundOver) { this.log.push(hit); this.round++; if (this.round >= this.H.rounds) this.over = true; else this.next(); }
      r.over = this.over; return r;
    }
    update(dt) { if (this.over) return; this.t += dt; if (this.t >= this.H.timeLimitSec) { this.t = this.H.timeLimitSec; this.over = true; } }
    get left() { return Math.max(0, this.H.timeLimitSec - this.t); }
  }

  // ── 系統 2：小圃種花 ──
  const FL = k => C().garden.flowers.find(f => f.k === k) || null;
  /* 花盆狀態（純計算）：growth＝今日之前有淋水嘅日數；連續 dryDaysToWilt 日（今日之前）冇淋水 → 枯；growth ≥ growDays → 開花 */
  function potInfo(p, nowMs) {
    if (!p) return { empty: true };
    const Gc = C().garden, today = X.dayNum(now(nowMs)), w = new Set(p.w), f = FL(p.k);
    let growth = 0, dry = 0, wilted = false, bloomDay = null;
    for (let d = p.planted; d < today; d++) {
      if (w.has(d)) { growth++; dry = 0; if (growth >= Gc.growDays) { bloomDay = d + 1; break; } }
      else if (++dry >= Gc.dryDaysToWilt) { wilted = true; break; }
    }
    const bloomed = bloomDay != null, wateredToday = w.has(today);
    const stage = bloomed ? 3 : wilted ? -1 : growth === 0 ? (wateredToday ? 1 : 0) : 2;
    return { empty: false, k: p.k, name: f ? f.name : p.k, route: f ? f.route : null, growth, need: Gc.growDays, dry, wilted, bloomed, bloomDay, wateredToday, stage, paid: !!p.paid };
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
    p.w.push(d); if (p.w.length > 10) p.w.shift(); return { ok: true, info: potInfo(p, nowMs) };
  }
  /* 每秒 tick：新開花 → 路線分（一次）。燦光（日菊）唔喺 §7 分池（addRoutePts 只收 5 條新支線）→ 記低開花，冇分（規格待遊策） */
  function gardenTick(s, nowMs) {
    const o = st(s), out = [];
    o.garden.pots.forEach((p, i) => {
      if (!p || p.paid) return; const I = potInfo(p, nowMs); if (!I.bloomed) return;
      p.paid = true; const ok = X.addRoutePts(s, I.route, C().garden.bloomPts);
      out.push({ pot: i, k: p.k, name: I.name, route: I.route, pts: ok ? C().garden.bloomPts : 0 });
      s.ev && s.ev.push({ type: 'sys12', sys: 'garden', what: 'bloom', k: p.k, name: I.name, route: I.route, n: 0 });
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
  function garden(s, nowMs) { const o = st(s); return { pots: o.garden.pots.map(p => potInfo(p, nowMs)), vase: Object.assign({}, o.garden.vase), price: C().garden.seedPrice, flowers: C().garden.flowers }; }

  // ── 系統 4：散步收集＋收藏櫃 ──
  const IT = k => C().walk.items.find(x => x.k === k) || null;
  function inHours(h, a) { if (!a) return true; return a[0] <= a[1] ? h >= a[0] && h < a[1] : h >= a[0] || h < a[1]; }
  function streak(o, today) { let n = 0; const set = new Set(o.seen); while (set.has(today - n)) n++; return n; }
  /* 合唔合條件（ctx：weather、month、hour、dn、seed、lead） */
  function eligible(it, ctx, o) {
    if (it.months && !it.months.includes(ctx.month)) return false;
    if (it.hours && !inHours(ctx.hour, it.hours)) return false;
    if (it.loginStreak && streak(o, ctx.dn) < it.loginStreak) return false;
    const afterRain = it.afterRainH != null && ctx.prevWeather === 'rain' && ctx.weather !== 'rain' && ctx.hourOfDay < it.afterRainH;
    if (it.onlyAfterRain) return afterRain;
    if (it.weather && !(it.weather.includes(ctx.weather) || afterRain)) return false;
    return true;
  }
  function walkCtx(s, nowMs, extra) {
    const t = now(nowMs), d = new Date(t), seed = (s.seed >>> 0) || 1, dn = X.dayNum(t);
    const c = { t, dn, month: d.getMonth() + 1, hour: d.getHours(), hourOfDay: d.getHours() + d.getMinutes() / 60, weather: SIM.weatherNow ? SIM.weatherNow() : X.weatherAt(t, seed),
      prevWeather: X.dayWeatherN(seed, dn - 1), lead: SIM.routeLead && s.stage !== 'egg' ? (SIM.routeLead(s) || {}).form || null : null, rng: Math.random };
    return Object.assign(c, extra || {});
  }
  function seen(s, nowMs) { const o = st(s), dn = X.dayNum(now(nowMs)); if (!o.seen.includes(dn)) { o.seen.push(dn); o.seen.sort((a, b) => a - b); if (o.seen.length > 14) o.seen.shift(); } }
  /* 團絨開始行一段路 → 擲一次：稀有逐件獨立 pct（領先路線 ×routeMul）→ 否則 chance 執一件合條件嘅普通小物；每日最多 perDay；保底 pity */
  function walkRoll(s, nowMs, extra) {
    const Wc = C().walk, o = st(s), w = o.walk, c = walkCtx(s, nowMs, extra), key = SIM.dayKey(c.t);
    if (s.stage === 'egg') return null;
    seen(s, c.t);
    if (w.day !== key) { w.day = key; w.count = 0; }
    if (w.count >= Wc.perDay) return null;
    const rng = c.rng, el = Wc.items.filter(it => eligible(it, c, o));
    let got = null;
    if (!c.noRare) for (const it of el) if (it.rare && it.pct) { const mul = it.routeMul && c.lead && it.routeMul[c.lead] ? it.routeMul[c.lead] : 1; if (rng() < it.pct * mul) { got = it; break; } }
    if (!got && (c.force || rng() < Wc.chance)) {   /* force／noRare：DEV 即執一件普通小物 */ const com = el.filter(it => !it.rare); if (com.length) got = com[Math.floor(rng() * com.length)]; }
    if (!got) return null;
    const pityIt = Wc.items.find(it => it.pity && !w.got[it.k] && w.total + 1 >= it.pity); if (pityIt) got = pityIt;
    w.count++; w.total++; const first = !w.got[got.k]; w.got[got.k] = (w.got[got.k] | 0) + 1;
    note(o, w.log, { t: c.t, k: got.k });
    s.ev && s.ev.push({ type: 'sys12', sys: 'walk', what: 'pickup', k: got.k, name: got.name, first, n: 0 });
    return { k: got.k, name: got.name, first, count: w.count, left: Wc.perDay - w.count, total: w.total, pity: !!pityIt };
  }
  /* 收藏櫃：30 格；config 有嘅小物（有圖）＝剪影／已收集；其餘格未有規格 → locked */
  function cabinet(s) {
    const Wc = C().walk, w = st(s).walk, out = [];
    for (let i = 0; i < Wc.slots; i++) { const it = Wc.items[i]; out.push(it ? { k: it.k, name: w.got[it.k] ? it.name : '？', got: w.got[it.k] | 0, rare: !!it.rare } : { k: null, name: '？', got: 0, locked: true }); }
    return { slots: out, unique: Object.keys(w.got).filter(k => IT(k) && w.got[k] > 0).length, total: w.total, today: w.day === SIM.dayKey(SIM.nowMs()) ? w.count : 0, perDay: Wc.perDay };
  }

  // ── 系統 11：成就徽章 ──
  function met(s, when) {
    if (when.stageAtLeast) { const S = SIM.STAGES; return S.indexOf(s.stage) >= S.indexOf(when.stageAtLeast) || (s.dex || []).length > 0 || (s.memorial || []).length > 0; }
    if (when.dex) return (s.dex || []).includes(when.dex);
    if (when.collected) return cabinet(s).unique >= when.collected;
    return false;
  }
  /* 檢查新徽章（唔重覆給）：星星碎經 wallet（'badge'＝其他上限）；爆上限嘅數留 pending，之後補發 */
  function badgeCheck(s, nowMs) {
    const t = now(nowMs), Bc = C().badges, o = st(s), B = o.badges, out = [];
    if (B.pending) B.pending -= X.grant(s, B.pending, 'badge', t);
    for (const b of Bc.list) {
      if (B.got[b.k] || !met(s, b.when)) continue;
      B.got[b.k] = t; const g = X.grant(s, Bc.reward, 'badge', t); B.pending += Bc.reward - g;
      const title = b.title || b.name; B.title = title;
      out.push({ k: b.k, name: b.name, title, shards: g, pending: Bc.reward - g });
      s.ev && s.ev.push({ type: 'sys12', sys: 'badge', what: 'got', k: b.k, name: b.name, title, n: g });
    }
    return out;
  }
  function badges(s) { const Bc = C().badges, B = st(s).badges; return { list: Bc.list.map(b => ({ k: b.k, name: b.name, title: b.title || b.name, got: !!B.got[b.k], at: B.got[b.k] || null })), total: Bc.total, have: Object.keys(B.got).length, title: B.title, pending: B.pending }; }

  function tick(s, nowMs) { if (!s || s.stage === undefined) return null; seen(s, nowMs); return { bloom: gardenTick(s, nowMs), badges: badgeCheck(s, nowMs) }; }

  return { st, gameStars, gameFinish, gamesToday, catchParams, HideGame, potInfo, plant, water, gardenTick, harvest, garden, eligible, walkCtx, walkRoll, cabinet, streak, seen, badgeCheck, badges, tick };
});
