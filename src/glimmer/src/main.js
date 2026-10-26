/* 《微光小圃》 main.js — 啟動、主迴圈、存檔、離線結算、縮放。原創代碼。 */
(function () {
  'use strict';
  const NS = window.Glimmer, D = NS.data, SIM = NS.sim, R = NS.render, UI = NS.ui;
  const P = D.PARAMS;
  const qs = new URLSearchParams(location.search);
  const G = { debug: qs.get('debug') === '1', timeScale: 1, hourOverride: qs.has('hour') ? +qs.get('hour') : null, mode: 'garden', autoDowngrade: qs.get('debug') !== '1', openDbg: qs.get('dbg') === 'open' };
  window.__glimmer = G; // 方便測試／除錯（只喺 ?debug=1 先有 UI 面板）
  G.now = () => Date.now();
  G.hour = () => { if (G.hourOverride != null) return G.hourOverride; const d = new Date(G.now()); return d.getHours() + d.getMinutes() / 60; };

  // ── 存檔 ──
  function load() {
    let s = null, rep = null;
    try { const str = localStorage.getItem(P.saveKey); if (str) s = SIM.deserialize(str, G.now()); } catch (e) { /* 無法讀取 */ }
    if (!s) { s = SIM.newState(G.now()); const coarse = window.matchMedia && matchMedia('(pointer:coarse)').matches; s.settings.quality = qs.get('q') || (coarse ? 'mid' : 'high'); }
    else rep = SIM.applyOffline(s, G.now());
    if (qs.get('q')) s.settings.quality = qs.get('q');
    return { s, rep };
  }
  G.save = function () { try { G.state.lastSeen = G.now(); localStorage.setItem(P.saveKey, SIM.serialize(G.state)); } catch (e) { /* 私隱模式等 */ } };
  G.resetSave = function () { try { localStorage.removeItem(P.saveKey); } catch (e) { } window.__noSaveOnHide = true; location.reload(); };
  G.setQuality = function (q) { G.state.settings.quality = q; G.renderer.blurEvery = 1; G.save(); };
  G.fastForward = function (sec) { SIM.advance(G.state, sec, {}, 30); };
  G.simOffline = function (h) { G.state.lastSeen = G.now() - h * 3600e3; const rep = SIM.applyOffline(G.state, G.now()); G.save(); UI.showSummary(rep); return rep; };

  // ── 縮放（整數倍像素）──
  const canvas = document.getElementById('gl');
  G.renderer = new R.Renderer(canvas);
  function layout() {
    const vw = window.innerWidth, vh = window.innerHeight, dpr = window.devicePixelRatio || 1;
    let kdev = Math.floor(Math.min(vw * dpr / R.W, vh * dpr / R.H));
    let cssW, cssH, kb;
    if (kdev >= 2) { kb = Math.min(kdev, 4); cssW = R.W * kdev / dpr; cssH = R.H * kdev / dpr; }
    else { const f = Math.min(vw / R.W, vh / R.H); cssW = R.W * f; cssH = R.H * f; kb = 2; kdev = 0; }
    if (G.renderer.k !== kb) G.renderer.setScale(kb);
    canvas.style.width = cssW + 'px'; canvas.style.height = cssH + 'px';
    canvas.style.imageRendering = (kdev && kb === kdev) ? 'pixelated' : 'auto';
    const wrap = document.getElementById('stagewrap'); wrap.style.width = cssW + 'px'; wrap.style.height = cssH + 'px';
    document.getElementById('ui').style.transform = 'scale(' + (cssW / 390) + ')';
    G.layoutInfo = { vw, vh, dpr, kdev, kb, cssW, cssH };
  }
  window.addEventListener('resize', layout); layout();

  // ── 啟動 ──
  const boot = load(); G.state = boot.s;
  UI.init(G);
  if (boot.rep && boot.rep.show) UI.showSummary(boot.rep);
  G.save();
  G.bootReport = boot.rep;

  // ── 主迴圈 ──
  let last = performance.now(), saveT = 0, slow = 0, frames = 0;
  function loop(ts) {
    const dtReal = Math.min(0.25, (ts - last) / 1000); last = ts;
    const s = G.state;
    if (!document.hidden) {
      SIM.advance(s, dtReal * G.timeScale, {}, 30);
      saveT += dtReal; if (saveT >= P.autosaveSec) { saveT = 0; G.save(); }
      UI.update(dtReal);
      G.renderer.frame(dtReal, { state: s, quality: s.settings.quality, hour: G.hour(), mode: G.mode, mg: UI.mgState() && UI.mgState().mg });
      // 自動降畫質（非 debug）：連續過慢先降一級
      if (G.autoDowngrade && s.settings.quality !== 'off' && ++frames > 60) {
        slow = G.renderer.perf.last > 26 ? slow + 1 : Math.max(0, slow - 1);
        if (slow > 90) { const order = ['high', 'mid', 'low', 'off']; const nq = order[Math.min(3, order.indexOf(s.settings.quality) + 1)]; G.setQuality(nq); UI.toast('效能較低，已自動降低畫質'); slow = 0; }
      }
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ── 離開／返嚟 ──
  function onHide() { if (!window.__noSaveOnHide) G.save(); }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) onHide();
    else { const rep = SIM.applyOffline(G.state, G.now()); G.save(); last = performance.now(); if (rep.show) UI.showSummary(rep); }
  });
  window.addEventListener('pagehide', onHide);
  window.addEventListener('beforeunload', onHide);

  // ── 效能量度（測試用）──
  G.bench = function (quality, n) {
    const s = G.state, old = s.settings.quality; s.settings.quality = quality; const r = G.renderer; r.perfReset();
    const view = { state: s, quality, hour: G.hour(), mode: 'garden' };
    for (let i = 0; i < 20; i++) r.frame(1 / 60, view); r.perfReset();
    for (let i = 0; i < n; i++) r.frame(1 / 60, view);
    const res = { quality, frames: r.perf.n, avgMs: +(r.perf.sum / r.perf.n).toFixed(2), maxMs: +r.perf.max.toFixed(2) };
    s.settings.quality = old; return res;
  };
})();
