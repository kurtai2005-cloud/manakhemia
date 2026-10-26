/* 《微光小圃》 lighting.js — 時段光照 hook（DOM-free）。
   早／午／晚／深夜（按本機時間；?debug=1 可覆寫）→ 燈籠色溫／強度、色調疊層、環境暗度、寵物行為權重。
   預留 weather hook：addModifier(name, fn)，fn(light, ctx) 可改寫 light（例如雨天：lanternMul×0.8、grade 偏藍、beh.sunbathe=0）。原創代碼。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.light = factory(root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (D) {
  'use strict';
  const L = D.PARAMS.light;
  const ORDER = ['morning', 'noon', 'evening', 'night'];
  const modifiers = [];

  function periodOf(hour) {
    const h = ((hour % 24) + 24) % 24, st = L.periodStarts;
    if (h >= st.night || h < st.morning) return 'night';
    if (h >= st.evening) return 'evening';
    if (h >= st.noon) return 'noon';
    return 'morning';
  }
  function copy(p) {
    return { lantern: p.lantern.slice(), lanternMix: p.lanternMix, lanternMul: p.lanternMul, grade: p.grade.slice(), gradeA: p.gradeA, ambient: p.ambient, sun: p.sun, beh: Object.assign({}, p.beh) };
  }
  /* ctx 預留：{ weather: 'clear'|'rain'|…, … }（天氣模組日後經 modifier 讀取） */
  function compute(hour, ctx) {
    ctx = ctx || {};
    const id = periodOf(hour), p = L.periods[id];
    const out = Object.assign({ period: id, name: p.name, hour: ((hour % 24) + 24) % 24 }, copy(p));
    out.daylight = daylightAt(out.hour, id);
    for (let i = 0; i < modifiers.length; i++) { const r = modifiers[i].fn(out, Object.assign({ hour: out.hour, period: id }, ctx)); if (r && r !== out) Object.assign(out, r); }
    return out;
  }
  /* ── 遊美 daylight.json（art/daylight/）：4 時段色彩參數。遊策時段（早 07／午 11／晚 17／夜 23）決定「邊個時段」，
        daylight.json 嘅 hours 欄只作參考（偏差已入報告）；跨時段用 blendSeconds 淡入（新時段開始後 blendSeconds 內由上一時段 mix 0→1）。 */
  const DL_MAP = { morning: 'early', noon: 'noon', evening: 'dusk', night: 'night' };
  let DL = null;
  function hex(c) { const n = parseInt(String(c).replace('#', ''), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
  function mixc(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  function setDaylight(json) {
    if (!json || !json.periods) { DL = null; return false; }
    const out = { blendSeconds: json.blendSeconds || 1800, size: json.logicalSize || [480, 270], p: {} };
    for (const k in json.periods) {
      const q = json.periods[k];
      out.p[k] = { id: k, zh: q.zh, bg: q.bg, overlay: q.overlay, ambient: hex(q.ambientMultiply), bloom: q.bloom, vignette: q.vignette, lamp: q.lamp ? q.lamp.intensity : 0, lampPos: q.lamp ? q.lamp.pos : null,
        pet: { mul: hex(q.pet.multiply), add: hex(q.pet.add), rim: hex(q.pet.rimColor), shadow: hex(q.pet.shadowColor) }, sky: q.sky ? [hex(q.sky.top), hex(q.sky.bottom)] : null };
    }
    DL = out; return true;
  }
  const PREV = { morning: 'night', noon: 'morning', evening: 'noon', night: 'evening' };
  function daylightAt(hour, period) {
    if (!DL) return null;
    const st = L.periodStarts; let since = ((hour - st[period]) % 24 + 24) % 24;       // 新時段開始後過咗幾多小時
    const mix = Math.max(0, Math.min(1, since * 3600 / DL.blendSeconds));
    const cur = DL.p[DL_MAP[period]], prev = DL.p[DL_MAP[PREV[period]]];
    const m = (a, b) => mixc(a, b, mix), n = (a, b) => a + (b - a) * mix;
    return { id: cur.id, prev: prev.id, mix, bg: cur.bg, bgPrev: prev.bg, overlay: cur.overlay, overlayPrev: prev.overlay,
      ambient: m(prev.ambient, cur.ambient), bloom: n(prev.bloom, cur.bloom), vignette: n(prev.vignette, cur.vignette), lamp: n(prev.lamp, cur.lamp),
      pet: { mul: m(prev.pet.mul, cur.pet.mul), add: m(prev.pet.add, cur.pet.add), rim: m(prev.pet.rim, cur.pet.rim), shadow: cur.pet.shadow } };
  }
  function addModifier(name, fn) { removeModifier(name); modifiers.push({ name, fn }); }
  function removeModifier(name) { const i = modifiers.findIndex(m => m.name === name); if (i >= 0) modifiers.splice(i, 1); }
  function modifierNames() { return modifiers.map(m => m.name); }
  function representativeHour(period) { return L.periodHour[period]; }

  return { ORDER, setDaylight, daylightAt, DL_MAP, hasDaylight: () => !!DL, periodOf, compute, addModifier, removeModifier, modifierNames, representativeHour };
});
