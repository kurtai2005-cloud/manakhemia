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

  return { dayNum, dayStart, weekOf, hash, rngFor, rainSpells, dayBase, weatherAt, simulate, seasonOf, shiverMul, SEASON_NAME, WEATHER_NAME };
});
