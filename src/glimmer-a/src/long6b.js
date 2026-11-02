/* 《微光小圃》 long6b.js — 第 6 批 6b「真世界連動」（遊策 breakthrough-6a6d-spec §6b）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.rw6（sanitize）。權限全部可以唔開：唔開／冇網 → 遊戲同而家一樣。
   ・步數：手機計步器（Android TYPE_STEP_COUNTER，開機至今累計）→ 每次讀數變差值；每 1000 步 團絨散步路行 1 格；每 2000 步 1 粒星星碎，
     每日最多 5 粒（遊策裁定：自己一個池，唔食舊來源 30／long5b 12；合共上限 PARAMS.SHARD_DAILY_TOTAL_CAP＝47）；散步路偶爾執到裝飾（每日最多 1 件）。
     步數只存本機（每日步數、累計、最後讀數）；冇上傳。
   ・天氣：大概位置 → Open-Meteo（免 key）真天氣 → 只改畫面（雨／陰／霧／晴）；計分照用遊戲內每日擲（菇傘雨天分唔變）。
     座標只用嚟砌 URL（四捨五入到 0.1°），唔存。
   ・日出日落：按位置調晝夜色調（畫面用 hour 做分段 remap）；月眠／水珠時段唔變（嗰啲用真鐘）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./sim.js'), require('./systems.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6b = factory(root.Glimmer.sim, root.Glimmer.sys12); }
})(typeof self !== 'undefined' ? self : this, function (SIM, X) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const int = (v, d) => Number.isFinite(+v) ? Math.floor(+v) : d;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const CFG = { stepsPerTile: 1000, stepsPerShard: 2000, shardCap: 5, pathTiles: 12, decoChance: 0.08, decoPerDay: 1, maxDelta: 40000, keepDays: 14,
    bootSlackMs: 120000, wxTtlMs: 30 * 60000, sunRef: [6.5, 18.5], riseClamp: [3, 10], setClamp: [15, 22], coordRound: 1 };
  /* 散步路小物（6b 自己一套收藏，唔郁系統 4 散步收集嘅每日數／保底） */
  const DECO = [
    { id: 'pebble', zh: '圓石仔' }, { id: 'leaf', zh: '紅葉' }, { id: 'acorn', zh: '橡果' }, { id: 'feather', zh: '羽毛' },
    { id: 'shell', zh: '蝸牛殼' }, { id: 'clover', zh: '四葉草' }, { id: 'button', zh: '鈕扣' }, { id: 'ribbon', zh: '絲帶' },
  ];
  const DK = Object.fromEntries(DECO.map(d => [d.id, d]));
  const WX = ['clear', 'overcast', 'rain', 'fog'];
  const dayKey = (t) => SIM.dayKey(t);

  function st(s) {
    let o = s.rw6; if (!obj(o)) o = s.rw6 = {};
    o.v = 1;
    if (!obj(o.on)) o.on = {}; o.on.steps = o.on.steps === true; o.on.wx = o.on.wx === true;
    if (!obj(o.last) || !Number.isFinite(+o.last.raw)) o.last = null; else o.last = { raw: Math.max(0, int(o.last.raw, 0)), boot: int(o.last.boot, 0), t: int(o.last.t, 0) };
    o.total = Math.max(0, int(o.total, 0));
    if (!obj(o.d)) o.d = {};
    for (const k of Object.keys(o.d)) { const d = o.d[k]; if (!/^\d{4}-\d\d-\d\d$/.test(k) || !obj(d)) { delete o.d[k]; continue; } d.st = Math.max(0, int(d.st, 0)); d.sh = clamp(int(d.sh, 0), 0, CFG.shardCap); d.dc = clamp(int(d.dc, 0), 0, CFG.decoPerDay); }
    const ks = Object.keys(o.d).sort(); while (ks.length > CFG.keepDays) delete o.d[ks.shift()];
    if (!obj(o.got)) o.got = {}; for (const k of Object.keys(o.got)) if (!DK[k]) delete o.got[k]; else o.got[k] = Math.max(0, int(o.got[k], 0));
    if (!Array.isArray(o.log)) o.log = []; o.log = o.log.filter(e => obj(e) && DK[e.k]).slice(-20);
    if (!obj(o.wx) || !WX.includes(o.wx.kind)) o.wx = null;
    else { const w = o.wx; o.wx = { kind: w.kind, code: int(w.code, -1), at: int(w.at, 0), rise: Number.isFinite(+w.rise) ? +w.rise : null, set: Number.isFinite(+w.set) ? +w.set : null }; }
    if (!obj(o.n)) o.n = {}; for (const k of ['shards', 'decos', 'reads', 'reboots']) o.n[k] = Math.max(0, int(o.n[k], 0));
    for (const k of Object.keys(o)) if (!['v', 'on', 'last', 'total', 'd', 'got', 'log', 'wx', 'n'].includes(k)) delete o[k];   // 只留呢啲（冇座標、冇原始感應器資料）
    return o;
  }
  function day(s, now) { const o = st(s), k = dayKey(now); if (!o.d[k]) { o.d[k] = { st: 0, sh: 0, dc: 0 }; const ks = Object.keys(o.d).sort(); while (ks.length > CFG.keepDays) delete o.d[ks.shift()]; } return o.d[k]; }
  function setOn(s, what, v) { const o = st(s); if (what !== 'steps' && what !== 'wx') return false; o.on[what] = !!v; if (what === 'steps' && !v) o.last = null; if (what === 'wx' && !v) o.wx = null; return o.on[what]; }

  /* 入碎：6b 自己一個池（每日 ≤5），直接入 sys12 錢包（同 long5b 一樣記 log；src '6b:steps'） */
  function earn(s, n, now, d) {
    d = d || day(s, now); const g = Math.max(0, Math.min(Math.floor(n), CFG.shardCap - d.sh)); if (!g) return 0;
    d.sh += g; const w = X.st(s).wallet; w.total += g; w.earned = (w.earned | 0) + g;
    if (Array.isArray(w.log)) { w.log.push({ t: now || 0, d: dayKey(now || 0), src: '6b:steps', n: g }); if (w.log.length > 40) w.log.shift(); }
    st(s).n.shards += g; return g;
  }
  /* 步數入帳（n＝新步數，記入今日）→ 行格、執裝飾、出碎 */
  function credit(s, n, now) {
    const o = st(s), d = day(s, now); n = clamp(int(n, 0), 0, CFG.maxDelta); const out = { steps: n, tiles: 0, deco: [], shards: 0 };
    if (!n) return out;
    const t0 = Math.floor(o.total / CFG.stepsPerTile); o.total += n; d.st += n; const t1 = Math.floor(o.total / CFG.stepsPerTile); out.tiles = t1 - t0;
    const seed = (s.seed >>> 0) || 1;
    for (let i = t0 + 1; i <= t1 && i <= t0 + 60; i++) {
      if (d.dc >= CFG.decoPerDay) break;
      if ((hash(seed + ':6b:' + i) % 10000) / 10000 < CFG.decoChance) {
        const it = DECO[hash(seed + ':6bd:' + i) % DECO.length]; d.dc++; o.got[it.id] = (o.got[it.id] | 0) + 1; o.n.decos++;
        o.log.push({ t: now, k: it.id, tile: i % CFG.pathTiles }); if (o.log.length > 20) o.log.shift(); out.deco.push(it.id);
        s.ev && s.ev.push({ type: 'l6b', what: 'deco', k: it.id, name: it.zh });
      }
    }
    const want = Math.min(CFG.shardCap, Math.floor(d.st / CFG.stepsPerShard)); if (want > d.sh) out.shards = earn(s, want - d.sh, now, d);
    if (out.shards) s.ev && s.ev.push({ type: 'l6b', what: 'shards', n: out.shards });
    return out;
  }
  /* 感應器讀數（TYPE_STEP_COUNTER：開機至今累計）→ 差值。第一次＝基準（0）；重開機（讀數細咗／開機時間變）→ 差值＝讀數；每次最多 maxDelta */
  function ingest(s, raw, bootMs, now) {
    const o = st(s); if (!o.on.steps) return { ok: false, why: 'off' };
    raw = +raw; if (!Number.isFinite(raw) || raw < 0) return { ok: false, why: 'bad' }; raw = Math.floor(raw); bootMs = int(bootMs, 0);
    const L = o.last; o.n.reads++;
    if (!L) { o.last = { raw, boot: bootMs, t: now }; return Object.assign({ ok: true, why: 'baseline' }, credit(s, 0, now)); }
    const reboot = raw < L.raw || (bootMs && L.boot && Math.abs(bootMs - L.boot) > CFG.bootSlackMs);
    if (reboot) o.n.reboots++;
    const delta = reboot ? raw : raw - L.raw; o.last = { raw, boot: bootMs || L.boot, t: now };
    return Object.assign({ ok: true, why: reboot ? 'reboot' : 'delta' }, credit(s, delta, now));
  }
  function pos(s) { const o = st(s), tiles = Math.floor(o.total / CFG.stepsPerTile); return { tile: tiles % CFG.pathTiles, lap: Math.floor(tiles / CFG.pathTiles), frac: (o.total % CFG.stepsPerTile) / CFG.stepsPerTile, tiles }; }
  function summary(s, now) {
    const o = st(s), d = o.d[dayKey(now)] || { st: 0, sh: 0, dc: 0 }, p = pos(s);
    return { on: Object.assign({}, o.on), today: d.st, shards: d.sh, cap: CFG.shardCap, toShard: d.sh >= CFG.shardCap ? 0 : CFG.stepsPerShard - (d.st % CFG.stepsPerShard),
      toTile: CFG.stepsPerTile - (o.total % CFG.stepsPerTile), tile: p.tile, lap: p.lap, pathTiles: CFG.pathTiles, decoToday: d.dc, got: Object.keys(o.got).length, total: o.total,
      wx: o.wx ? Object.assign({}, o.wx) : null, n: Object.assign({}, o.n) };
  }

  /* ── 天氣（只改畫面）── WMO weather_code → 遊戲天氣種類 */
  function wmo(code) {
    if (code === null || code === undefined || code === '') return null; code = int(code, -1); if (code < 0) return null;
    if (code <= 2) return 'clear'; if (code === 3) return 'overcast'; if (code === 45 || code === 48) return 'fog';
    if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82) || code >= 95) return 'rain';
    if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'overcast';   // 雪 → 陰（未有雪景）
    return 'clear';
  }
  const round1 = (v) => Math.round(+v * 10) / 10;
  function url(lat, lon) {
    if (!Number.isFinite(+lat) || !Number.isFinite(+lon)) return null;
    return 'https://api.open-meteo.com/v1/forecast?latitude=' + round1(clamp(+lat, -90, 90)).toFixed(1) + '&longitude=' + round1(clamp(+lon, -180, 180)).toFixed(1) + '&current=weather_code&daily=sunrise,sunset&timezone=auto&forecast_days=1';
  }
  const hhmm = (iso) => { const m = /T(\d\d):(\d\d)/.exec(String(iso || '')); return m ? +m[1] + +m[2] / 60 : null; };
  /* Open-Meteo 回應 → s.rw6.wx（只存天氣種類、WMO code、日出日落鐘數、時間；唔存座標） */
  function applyWx(s, j, now) {
    const o = st(s); if (!o.on.wx || !obj(j)) return null;
    const code = obj(j.current) ? j.current.weather_code : null, kind = wmo(code); if (!kind) return null;
    const D = obj(j.daily) ? j.daily : {}, rise = hhmm(Array.isArray(D.sunrise) ? D.sunrise[0] : null), set = hhmm(Array.isArray(D.sunset) ? D.sunset[0] : null);
    o.wx = { kind, code: int(code, -1), at: now, rise, set }; return Object.assign({}, o.wx);
  }
  const fresh = (s, now) => { const w = st(s).wx; return !!(w && now - w.at >= 0 && now - w.at < CFG.wxTtlMs); };
  const stale = (s, now) => { const w = st(s).wx; return !!(w && now - w.at >= 0 && now - w.at < 6 * 3600e3); };   // 冇網：最多用返 6 粒鐘前嘅真天氣，之後返每日擲
  /* 畫面天氣：開咗＋有（6 粒鐘內）真天氣 → 真天氣；否則 → 遊戲內每日擲（fallback） */
  function visWeather(s, gameWx, now) { const o = st(s); return (o.on.wx && stale(s, now)) ? o.wx.kind : gameWx; }
  /* 日出日落 remap：真日出 → 6.5、真日落 → 18.5（遊戲晝夜分段），中間線性；冇資料 → 原鐘 */
  function visHour(s, h, now) {
    const o = st(s), w = o.wx; if (!o.on.wx || !w || !stale(s, now) || w.rise == null || w.set == null) return h;
    const r = clamp(w.rise, CFG.riseClamp[0], CFG.riseClamp[1]), z = clamp(w.set, CFG.setClamp[0], CFG.setClamp[1]), R0 = CFG.sunRef[0], Z0 = CFG.sunRef[1];
    let x = ((h % 24) + 24) % 24, y;
    if (x >= r && x <= z) y = R0 + (x - r) * (Z0 - R0) / (z - r);
    else { const nx = x > z ? x - z : x + 24 - z, nl = 24 - (z - r), nl0 = 24 - (Z0 - R0); y = Z0 + nx * nl0 / nl; }
    return ((y % 24) + 24) % 24;
  }
  function reset(s) { delete s.rw6; return st(s); }

  return { CFG, DECO, DK, WX, dayKey, st, day, setOn, earn, credit, ingest, pos, summary, wmo, url, applyWx, fresh, stale, visWeather, visHour, reset, round1 };
});
