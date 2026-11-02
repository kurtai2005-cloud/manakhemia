/* 《微光小圃》 v3.js — #83 新派 HD-2D V3（Kurt 2026-11-02：V3-A）核心：開關＋petGlow 控制器。原創代碼。
   開關：預設開（只喺 v2 UI；v1 凍結唔郁）；`?v3=0` → 成套返 6b.3 樣（唔 load V3 美術）。
   petGlow（ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow；Kurt：「除左佢訓就會關」）：
     awake 1、sleepy／drowsy .6、sleep／sleepClip／dreamEnter／dreaming 0；
     入瞓：由而家值 600ms easeInQuad 淡去 0；醒：400ms easeOutQuad 淡返 1，再 150ms pulse 1→1.15→1。
     keyframes [0,1] [600,0] … [wake,0] [wake+400,1] [wake+475,1.15] [wake+550,1]。
     只乘寵物自己嘅光（光池、光暈、core、粒子、emissive），sprite 本體同場景燈唔變。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.v3 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const STATES = { awake: 1, sleepy: 0.6, drowsy: 0.6, sleep: 0, sleepClip: 0, dreamEnter: 0, dreaming: 0 };
  const T = { out: 600, in: 400, pulse: 150, pulseK: 1.15, soft: 300 };
  const inQuad = (u) => u * u, outQuad = (u) => u * (2 - u), clamp01 = (v) => Math.max(0, Math.min(1, v));
  /* petGlow：純邏輯（node 單測得）；now = ms */
  class Glow {
    constructor(state, now) { this.state = state || 'awake'; this.v0 = STATES[this.state]; this.v1 = this.v0; this.t0 = now || 0; this.kind = 'hold'; this.dur = 0; this.n = 0; }
    value(now) {
      const u = this.dur > 0 ? clamp01((now - this.t0) / this.dur) : 1;
      if (this.kind === 'out') return this.v0 + (this.v1 - this.v0) * inQuad(u);
      if (this.kind === 'wake') {                      // 400ms easeOutQuad 0→1，之後 75ms 1→1.15、75ms 1.15→1
        const e = now - this.t0;
        if (e < T.in) return this.v0 + (1 - this.v0) * outQuad(clamp01(e / T.in));
        const p = e - T.in; if (p < T.pulse / 2) return 1 + (T.pulseK - 1) * (p / (T.pulse / 2));
        if (p < T.pulse) return T.pulseK - (T.pulseK - 1) * ((p - T.pulse / 2) / (T.pulse / 2));
        return 1;
      }
      if (this.kind === 'soft') return this.v0 + (this.v1 - this.v0) * u;
      return this.v1;
    }
    set(state, now) {
      if (!(state in STATES) || state === this.state) return this;
      const cur = this.value(now), tgt = STATES[state], wasOff = STATES[this.state] === 0;
      this.state = state; this.t0 = now; this.v0 = cur; this.v1 = tgt; this.n++;
      if (tgt === 0) { this.kind = 'out'; this.dur = T.out; }
      else if (wasOff || cur < 0.05) { this.kind = 'wake'; this.dur = T.in + T.pulse; this.v1 = tgt; if (tgt < 1) { this.kind = 'soft'; this.dur = T.in; } }
      else { this.kind = 'soft'; this.dur = T.soft; }
      return this;
    }
    done(now) { return now - this.t0 >= this.dur; }
  }
  /* 團絨狀態 → petGlow 狀態（瞓／入瞓 clip／夢遊 → 0；yawn／emo_sleepy／退縮呆／睏 → .6） */
  function petState(s, beh, extra) {
    extra = extra || {};
    if (extra.dreaming) return 'dreaming';
    if (s && s.sleeping) return 'sleep';
    const clip = (beh && beh.clip) || '';
    if (/^(fall_asleep|sleep)/.test(clip)) return 'sleepClip';
    if (/yawn|sleepy|drowsy/.test(clip) || (s && s.withdrawn && s.withdrawn.on) || extra.sleepy) return 'sleepy';
    return 'awake';
  }
  function kidState(clip, sleeping) { return clip === 'sleep' || sleeping ? 'sleep' : 'awake'; }
  /* V3 開唔開：?v3=0 → 永遠關；v1 UI（?ui=1／localStorage glimmer.ui=1）→ 關（v1 凍結）；其他 → 開 */
  function wanted(qs) { return !qs || qs.get('v3') !== '0'; }
  function install(G, NS) {
    const qs = new URLSearchParams(location.search), want = wanted(qs);
    const V = G.v3 = {
      want, glow: new Glow('awake', performance.now()), kid: new Glow('awake', performance.now()),
      on() { return want && !!(G.ui2 && G.ui2.on); },   // v2 UI 先開（v1／?hdui=0 凍結）
      petGlow(now) { return V.glow.value(now == null ? performance.now() : now); },
      kidGlow(now) { return V.kid.value(now == null ? performance.now() : now); },
      tick(s, beh, extra) { const now = performance.now(); V.glow.set(V.force || petState(s, beh, extra), now); return V.glow.value(now); },
      kidTick(clip, sleeping) { const now = performance.now(); V.kid.set(V.forceKid || kidState(clip, sleeping), now); return V.kid.value(now); },
      force: null, forceKid: null,
    };
    if (want) document.documentElement.classList.add('v3want');
    window.__qa = window.__qa || {};
    window.__qa.v3 = {
      on: () => V.on(), want: () => want, glow: () => +V.petGlow().toFixed(3), kidGlow: () => +V.kidGlow().toFixed(3), state: () => V.glow.state, kidState: () => V.kid.state,
      force(st) { V.force = st || null; return V.glow.state; }, forceKid(st) { V.forceKid = st || null; return V.kid.state; },
    };
    // 開發者模式（唔放設定）：V3 試玩掣
    const SEAS = ['spring', 'summer', 'autumn', 'winter', 'auto'], SZ = { spring: '春', summer: '夏', autumn: '秋', winter: '冬', auto: '自動' };
    const HRS = [[8, 'H1 朝'], [13, 'H2 午'], [18, 'H3 黃昏'], [22, 'H4 夜'], [null, '跟現實']];
    let si = -1, hi = -1;
    const glowIt = (k, zh) => ({ k: 'glow_' + k, label: '寵物光：' + zh, run() { V.force = k === 'auto' ? null : k; V.forceKid = k === 'auto' ? null : k; return { ok: true, msg: '團絨＋細佬光 → ' + zh }; } });
    const DEV = { id: 'v3', title: 'HD-2D V3', order: 12, status: () => (want ? (V.on() ? 'V3 開' : 'V3 等 v2 UI') : '?v3=0（6b.3 樣）') + '・光 ' + V.petGlow().toFixed(2) + '（' + (V.force || V.glow.state) + '）',
      items: [glowIt('awake', '醒'), glowIt('drowsy', '眼瞓 60%'), glowIt('sleep', '瞓（0）'), glowIt('dreaming', '夢（0）'), glowIt('auto', '自動'),
        { k: 'season', label: '季節輪轉（春夏秋冬自動）', run() { si = (si + 1) % SEAS.length; const m = SEAS[si]; if (G.seasonSet) G.seasonSet(m); return { ok: !!G.seasonSet, msg: '季節 → ' + SZ[m] }; } },
        { k: 'hour', label: '時段輪轉（H1–H4／現實）', run() { hi = (hi + 1) % HRS.length; G.hourOverride = HRS[hi][0]; return { ok: true, msg: '時段 → ' + HRS[hi][1] }; } },
        { k: 'rain', label: '落雨／天晴', run() { G.weather = G.weather === 'rain' ? null : 'rain'; if (G.wx) G.wx.manual = true; return { ok: true, msg: G.weather ? '落雨' : '天晴' }; } },
        { k: 'toggle', label: want ? '轉返 6b.3 樣（?v3=0）' : '轉 V3 樣', run() { const q = new URLSearchParams(location.search); if (want) q.set('v3', '0'); else q.delete('v3'); setTimeout(() => location.search = q.toString(), 50); return { ok: true, msg: '重新載入…' }; } }] };
    if (NS) { if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV); }
    return V;
  }
  return { STATES, T, Glow, petState, kidState, wanted, inQuad, outQuad, install };
});
