/* 《微光小圃》 touch.js — 第 3 批 3a（docs-gdd/batch3-fun-spec.md §①②）：觸摸互動＋扮醒呆反應包＋提示排隊。原創代碼。
   DOM-free、Node 可 require（純邏輯）：手勢辨識（tap／長按／搔癢／拉開／搖機）、心情每日上限（同浮動團絨共用）、扮醒呆排程、
   提示排隊（同一時間一個氣泡／心聲）、程序化動作表 MOTIONS（每個 key 預留 art 疊層名，遊美交圖後換）。
   唔加路線分、唔經 sim.noteCare（唔計 CQ／路線照顧分）→ §7 平衡唔郁。數值＝data.js PARAMS.touch。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.touch = factory(root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (D) {
  'use strict';
  const C = () => D.PARAMS.touch;
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const KINDS = ['poke', 'hold', 'tickle', 'pull', 'shake'];
  const DUMB = ['glasses', 'book', 'wall', 'mirror', 'finger', 'prof'];

  // ── 文案表（一張表：遊策可以整張替換）──────────────────────────────
  // 遊策定稿：docs-gdd/batch3-fun-spec.md「② 心聲文案（自信錯誤，6×3）」原文照搬。之後改文案＝只改呢張表（key 唔好改）。
  const LINES = {
    dumb: {
      glasses: ['一加一……即係三，好易啫。', '我戴咗眼鏡，即係我識數。', '呢條數我早就計晒，只係未講。'],
      book: ['我唔係瞓，我係用夢嚟溫書。', '呢本書太淺，我閉埋眼都睇得明。', 'Zzz……（我醒㗎）'],
      wall: ['呢度本來應該有條路㗎。', '我係試緊面牆夠唔夠硬。', '完全計劃之內。'],
      mirror: ['喂！你學我？', '呢隻好靚，一定係我朋友。', '我哋兩個一齊眨眼，好有默契。'],
      finger: ['一、二、四……嗯，夠晒。', '我有十隻手指，大概。', '數錯？冇可能，係手指郁咗。'],
      prof: ['雲係天空嘅棉花糖，科學講㗎。', '落雨即係天空喊，因為佢唔夠我醒。', '月光係太陽夜晚着睡衣。'],
    },
    caught: '我係試緊你咋',                  // 扮醒呆做緊時戳佢
    tickle: '我…我一啲都唔怕癢㗎！',          // 搔癢 → 碌地笑
    brag: '頭先係我故意轉嘅',                // 1 分鐘內搖暈 3 次
  };
  const DUMB_NAME = { glasses: '戴眼鏡計數', book: '睇書睇到瞓著', wall: '一本正經撞牆', mirror: '照鏡認錯人', finger: '數手指數錯', prof: '扮教授講錯嘢' };

  // ── 存檔狀態 s.touch（sanitize）──
  function st(s) {
    let o = s.touch; if (!obj(o)) o = s.touch = {};
    if (typeof o.d !== 'string') o.d = ''; if (!obj(o.k)) o.k = {};
    if (!obj(o.seen)) o.seen = {}; for (const k of Object.keys(o.seen)) if (!DUMB.includes(k)) delete o.seen[k];
    if (!obj(o.dumb)) o.dumb = {}; const m = o.dumb; if (typeof m.d !== 'string') m.d = ''; m.n = Math.max(0, m.n | 0); m.last = +m.last || 0;
    o.stats = obj(o.stats) ? o.stats : {}; return o;
  }
  /* fpet-bridge 嘅 dayKey（冇補 0：2026-11-1）— 同浮動團絨共用每日 mood 額要用同一個 key */
  function bridgeDay(t) { const d = new Date(t); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function simDay(t) { const d = new Date(t); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  /* store：{ get(k)→string|null, set(k,v) }（瀏覽器＝localStorage；測試＝記憶體） */
  function memStore() { const m = {}; return { get: (k) => (k in m ? m[k] : null), set: (k, v) => { m[k] = String(v); }, m }; }
  function sharedRead(store, t) { let o = {}; try { o = JSON.parse((store && store.get(C().mood.sharedKey)) || '{}') || {}; } catch (e) { o = {}; } if (!obj(o)) o = {}; return { o, k: bridgeDay(t), n: +o[bridgeDay(t)] || 0 }; }
  function sharedLeft(store, t) { return Math.max(0, C().mood.sharedCap - sharedRead(store, t).n); }

  /* 心情：每種手勢每日第一次 +1（同浮動團絨共用每日 ≤5）；瞓覺／光卵唔加；冇路線分、冇事件、唔經 noteCare */
  function moodGrant(s, kind, t, store) {
    if (!s || !KINDS.includes(kind)) return { ok: false, reason: 'kind' };
    if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (s.sleeping) return { ok: false, reason: 'sleep' };
    const o = st(s), day = simDay(t); if (o.d !== day) { o.d = day; o.k = {}; }
    if (o.k[kind]) return { ok: false, reason: 'repeat' };
    o.k[kind] = 1;                                   // 今日第一次（就算共用額滿咗都算用咗「第一次」）
    const sh = sharedRead(store, t); if (sh.n >= C().mood.sharedCap) return { ok: false, reason: 'cap', shared: sh.n };
    sh.o[sh.k] = sh.n + 1; const keep = {}; Object.keys(sh.o).slice(-7).forEach(k => { keep[k] = sh.o[k]; }); keep[sh.k] = sh.n + 1;
    try { store && store.set(C().mood.sharedKey, JSON.stringify(keep)); } catch (e) { }
    const add = C().mood.perKind; if (s.needs) s.needs.mood = Math.min(100, (+s.needs.mood || 0) + add);
    o.stats[kind] = (o.stats[kind] | 0) + 1;
    return { ok: true, add, shared: sh.n + 1 };
  }
  function moodToday(s, t, store) { const o = st(s), day = simDay(t); return { kinds: o.d === day ? Object.keys(o.k) : [], shared: sharedRead(store, t).n, cap: C().mood.sharedCap }; }

  // ── 手勢辨識（單指；座標 CSS px、時間秒）──
  function createRecognizer() {
    const R = { p: null, out: [] };
    const emit = (k, x) => { const e = Object.assign({ k }, x || {}); R.out.push(e); return e; };
    R.down = function (t, x, y) { R.p = { t0: t, x0: x, y0: y, x, y, maxD: 0, dir: 0, lastX: x, turns: [], hold: false, pat: false, tickle: false, tickleT: 0, roll: false, moved: false }; };
    R.move = function (t, x, y) {
      const p = R.p; if (!p) return; const T = C();
      p.x = x; p.y = y; const d = Math.hypot(x - p.x0, y - p.y0); p.maxD = Math.max(p.maxD, d); if (d > T.hold.moveTolPx) p.moved = true;
      const dx = x - p.lastX;
      if (Math.abs(dx) >= T.tickle.minSwingPx) { const dir = Math.sign(dx); if (p.dir && dir !== p.dir) p.turns.push(t); p.dir = dir; p.lastX = x; }
      while (p.turns.length && t - p.turns[0] > T.tickle.winSec) p.turns.shift();
      if (p.turns.length >= T.tickle.rubs) { if (!p.tickle) { p.tickle = true; p.tickleT = t; emit('tickle'); } p.lastRub = t; }
      if (p.tickle && !p.roll && t - p.tickleT >= T.tickle.rollSec && p.lastRub && t - p.lastRub < T.tickle.winSec) { p.roll = true; emit('roll'); }
    };
    R.tick = function (t) {
      const p = R.p; if (!p) return; const T = C(), held = t - p.t0;
      if (!p.hold && !p.moved && !p.tickle && held >= T.hold.sec) { p.hold = true; emit('hold'); }
      if (p.hold && !p.pat && !p.moved && !p.tickle && held >= T.hold.patSec) { p.pat = true; emit('pat'); }
    };
    R.up = function (t, x, y, cancel) {
      const p = R.p; R.p = null; if (!p || cancel) return null; const T = C();
      if (x != null) { p.x = x; p.y = y; }
      const d = Math.hypot(p.x - p.x0, p.y - p.y0), ms = (t - p.t0) * 1000;
      if (!p.tickle && d > T.pull.px) return emit('pull', { dx: p.x - p.x0, dy: p.y - p.y0, d });
      if (!p.tickle && !p.hold && !p.moved && ms < T.poke.maxMs) return emit('poke');
      return emit('release', { hold: p.hold, pat: p.pat, tickle: p.tickle });
    };
    R.active = () => R.p;
    R.drain = () => { const o = R.out; R.out = []; return o; };
    return R;
  }

  /* 搖機：|a| > 2.5g 嘅峰（≥0.15s 一個），1s 內兩個 → 一次「搖」。暈 2s、冷卻 30s；1 分鐘內搖 3 次（包括冷卻中嗰啲）→ 扮冇事心聲（每窗口一次） */
  function createShake() {
    const S = { peaks: [], shakes: [], dizzyAt: -1e9, bragAt: -1e9, lastPeak: -1e9 };
    S.sample = function (t, g) {
      const K = C().shake; if (!(g > K.g)) return null; if (t - S.lastPeak < K.peakGapSec) return null; S.lastPeak = t;
      S.peaks.push(t); while (S.peaks.length && t - S.peaks[0] > K.winSec) S.peaks.shift();
      if (S.peaks.length < K.peaks) return null; S.peaks = [];
      S.shakes.push(t); while (S.shakes.length && t - S.shakes[0] > K.bragWinSec) S.shakes.shift();
      const r = { k: 'shake', dizzy: false, brag: false };
      if (t - S.dizzyAt >= K.cooldownSec) { S.dizzyAt = t; r.dizzy = true; }
      if (S.shakes.length >= K.bragN && t - S.bragAt >= K.bragWinSec) { S.bragAt = t; r.brag = true; S.shakes = []; }
      return r;
    };
    return S;
  }

  // ── 扮醒呆排程：idle ≥20s 後每 60s 抽 25%；最少隔 3 分鐘；每日最多 8 次 ──
  function dumbCan(s, t) {
    if (!s || s.stage === 'egg' || s.sleeping) return { ok: false, reason: 'state' };
    const K = C().dumb, m = st(s).dumb, day = simDay(t); if (m.d !== day) { m.d = day; m.n = 0; }
    if (m.n >= K.perDay) return { ok: false, reason: 'day' };
    if (m.last && t - m.last < K.gapSec * 1000 && t >= m.last) return { ok: false, reason: 'gap' };
    return { ok: true };
  }
  function dumbRoll(s, t, rnd, force) {
    const c = dumbCan(s, t); if (!c.ok && !force) return null;
    if (!force && !(rnd() < C().dumb.chance)) return null;
    return DUMB[Math.min(DUMB.length - 1, Math.floor(rnd() * DUMB.length))];
  }
  /* 開始一次：計數＋圖鑑「呆呆時刻」；收齊 6 格由 systems2 徽章 dumb_all 發（5 碎，日上限外） */
  function dumbStart(s, k, t, rnd) {
    const o = st(s), m = o.dumb, day = simDay(t); if (m.d !== day) { m.d = day; m.n = 0; }
    m.n++; m.last = t; const first = !o.seen[k]; o.seen[k] = o.seen[k] || t;
    const L = LINES.dumb[k] || ['……']; return { k, first, line: L[Math.min(L.length - 1, Math.floor(rnd() * L.length))], n: m.n, all: dumbSeenN(s) >= DUMB.length };
  }
  function dumbSeenN(s) { const o = st(s); return DUMB.filter(k => o.seen[k]).length; }
  function dumbDex(s) { const o = st(s); return DUMB.map(k => ({ k, name: DUMB_NAME[k], got: !!o.seen[k] })); }

  // ── 提示排隊：同一時間只出一個氣泡／心聲（FIFO；urgent 頂走現時；同句唔重覆排；等太耐作廢）──
  function createQueue(opt) {
    const Q = { cur: null, list: [], log: [], dropped: 0 };
    const cfg = () => Object.assign({}, C().queue, opt || {});
    Q.push = function (item, now) {
      const K = cfg(); item = Object.assign({ sec: 4 }, item, { at: now });
      if (Q.cur && Q.cur.line === item.line && !item.urgent) return { ok: false, reason: 'dup' };
      if (Q.list.some(x => x.line === item.line)) return { ok: false, reason: 'dup' };
      if (item.urgent) { if (Q.cur) Q.cur.until = now; Q.list.unshift(item); }
      else { if (Q.list.length >= K.max) { Q.list.shift(); Q.dropped++; } Q.list.push(item); }
      return { ok: true, queued: !!Q.cur && !item.urgent };
    };
    /* 每幀：返 { show: item|null（啱啱輪到）, hide: item|null（啱啱完） } */
    Q.tick = function (now) {
      const K = cfg(), r = { show: null, hide: null };
      if (Q.cur && now >= Q.cur.until) { r.hide = Q.cur; Q.cur = null; Q.gapUntil = now + K.gapSec * 1000 * (Q.list.length && Q.list[0].urgent ? 0 : 1); }
      while (Q.list.length && now - Q.list[0].at > K.maxWaitSec * 1000) { Q.list.shift(); Q.dropped++; }
      if (!Q.cur && Q.list.length && !(Q.gapUntil && now < Q.gapUntil)) { const it = Q.list.shift(); it.start = now; it.until = now + it.sec * 1000; Q.cur = it; r.show = it; Q.log.push({ line: it.line, src: it.src, start: now }); if (Q.log.length > 40) Q.log.shift(); }
      return r;
    };
    Q.busy = (now) => !!Q.cur && (now == null || now < Q.cur.until);
    Q.size = () => Q.list.length + (Q.cur ? 1 : 0);
    Q.clear = () => { Q.list = []; Q.cur = null; };
    return Q;
  }

  // ── 程序化動作（squash／offset／rotate＋表情＋疊層）：遊美交圖後，art 欄＝將來換嘅疊層／clip 名 ──
  // f(u: 0–1 進度, e: 已過秒, x: 參數) → { sx, sy, dx, dy, rot, face:{eyes,mouth}, fx:[...] }
  const sinP = (u) => Math.sin(Math.PI * clamp(u, 0, 1));
  const MOTIONS = {
    g_poke: { sec: 0.15, art: 'fx_touch_poke', f: (u) => ({ sx: 1 + 0.14 * sinP(u), sy: 1 - 0.18 * sinP(u), face: { eyes: 'sleepy' } }) },
    g_hold: { sec: 0, loop: true, art: 'face_touch_squint', f: (u, e) => ({ sy: 1 + 0.025 * Math.sin(e * 2.6), rot: 0.04 * Math.sin(e * 1.6), face: { eyes: 'happy', mouth: 'squint' }, fx: ['heart'] }) },
    g_tickle: { sec: 1.2, art: 'fx_touch_laugh', f: (u, e) => ({ rot: 0.12 * Math.sin(e * 30), sy: 1 + 0.05 * Math.abs(Math.sin(e * 15)), face: { eyes: 'happy', mouth: 'happy' }, fx: ['laugh'] }) },
    g_roll: { sec: 2.6, art: 'clip_touch_roll_laugh', f: (u, e) => ({ rot: 0.55 * Math.sin(e * 6) * (1 - 0.4 * u), dy: -2 * Math.abs(Math.sin(e * 6)), sx: 1.06, sy: 0.92, face: { eyes: 'happy', mouth: 'happy' }, fx: ['laugh'] }) },
    g_pull: { sec: 0, loop: true, art: 'clip_touch_stretch', f: (u, e, x) => { const d = clamp((x && x.d) || 0, -1, 1); return { dx: d * C().pull.maxArt, sx: 1 + 0.18 * Math.abs(d), sy: 1 - 0.1 * Math.abs(d), rot: -0.15 * d, face: { eyes: 'surprised', mouth: 'surprised' } }; } },
    g_spring: { sec: 0.9, art: 'clip_touch_spring', f: (u, e, x) => { const d = clamp((x && x.d) || 0, -1, 1), k = Math.exp(-5 * u) * Math.cos(u * 18); const land = u > 0.78 ? sinP((u - 0.78) / 0.22) : 0; return { dx: d * C().pull.maxArt * k, rot: -0.15 * d * k, sx: 1 + 0.12 * land, sy: 1 - 0.16 * land, face: { eyes: 'surprised', mouth: 'happy' } }; } },
    g_dizzy: { sec: 2, art: 'fx_dizzy_stars', f: (u, e) => ({ rot: 0.16 * Math.sin(e * 8), dx: 2 * Math.sin(e * 4), face: { eyes: 'squint', mouth: 'wink' }, fx: ['stars'] }) },
    g_rub: { sec: 1.6, art: 'clip_sleep_rub_turn', f: (u) => ({ rot: 0.28 * sinP(u), sy: 1 - 0.05 * sinP(u), face: { eyes: 'sleepy', mouth: 'sleepy' }, fx: ['zzz'] }) },
    d_glasses: { sec: 6, art: 'fx_dumb_glasses+fx_qmark', f: (u, e) => ({ rot: 0.07 * Math.sin(e * 2), face: { eyes: 'squint', mouth: u > 0.5 ? 'happy' : 'neutral' }, fx: u > 0.25 ? ['glasses', 'qmark'] : ['glasses'] }) },
    d_book: { sec: 7, art: 'fx_dumb_book', f: (u, e) => (u < 0.45 ? { rot: 0.03 * Math.sin(e * 3), face: { eyes: 'neutral' }, fx: ['book'] } : { sy: 0.96, rot: 0.08, face: { eyes: 'sleepy', mouth: 'sleepy' }, fx: ['book', 'zzz'] }) },
    d_wall: { sec: 6, art: 'fx_dumb_bump', f: (u, e) => { const w = clamp(u / 0.42, 0, 1), b = u >= 0.42 && u < 0.52 ? sinP((u - 0.42) / 0.1) : 0; return { dx: 14 * w - 3 * b, dy: u < 0.42 ? -(Math.sin(e * 11) > 0.5 ? 1 : 0) : 0, sx: 1 - 0.18 * b, sy: 1 + 0.08 * b, face: u < 0.42 ? { eyes: 'neutral', mouth: 'neutral' } : u < 0.7 ? { eyes: 'squint', mouth: 'surprised' } : { eyes: 'happy', mouth: 'happy' }, fx: u >= 0.42 && u < 0.75 ? ['stars', 'sweat'] : u >= 0.75 ? ['sweat'] : [] }; } },
    d_mirror: { sec: 6, art: 'fx_dumb_mirror', f: (u, e) => ({ dy: u > 0.3 && u < 0.4 ? -2 : 0, face: u < 0.3 ? { eyes: 'surprised', mouth: 'surprised' } : { eyes: 'happy', mouth: 'happy' }, fx: ['mirror'] }) },
    d_finger: { sec: 6, art: 'fx_dumb_nums', f: (u, e) => ({ dy: -(Math.floor(u * 6) % 2), face: { eyes: 'squint', mouth: u > 0.66 ? 'happy' : 'neutral' }, fx: ['nums'], n: Math.min(3, Math.floor(u * 4)) }) },
    d_prof: { sec: 6, art: 'fx_dumb_prof_hat', f: (u, e) => ({ rot: -0.06, dy: -(Math.sin(e * 3) > 0.7 ? 1 : 0), face: { eyes: 'squint', mouth: 'happy' }, fx: ['hat'] }) },
    d_caught: { sec: 1.6, art: 'face_dumb_caught+fx_sweat', f: (u) => ({ sx: 1 - 0.05 * sinP(u), sy: 1 + 0.03 * sinP(u), face: { eyes: 'sad', mouth: 'wink' }, fx: ['sweat'] }) },
  };
  /* 計一個動作嘅一格（t、t0 秒）；完咗返 null（loop 款一直有） */
  function motionAt(key, t0, t, x) {
    const M = MOTIONS[key]; if (!M) return null; const e = Math.max(0, t - t0);
    if (!M.loop && e > M.sec) return null;
    const u = M.loop ? 0 : clamp(e / M.sec, 0, 1), r = Object.assign({ sx: 1, sy: 1, dx: 0, dy: 0, rot: 0, face: null, fx: [] }, M.f(u, e, x || {}));
    r.key = key; r.art = M.art; r.u = u; return r;
  }

  return { KINDS, DUMB, DUMB_NAME, LINES, MOTIONS, st, bridgeDay, simDay, memStore, sharedLeft, moodGrant, moodToday, createRecognizer, createShake, dumbCan, dumbRoll, dumbStart, dumbSeenN, dumbDex, createQueue, motionAt };
});
