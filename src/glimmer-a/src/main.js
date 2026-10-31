/* 《微光小圃》 main.js — 啟動、主迴圈、存檔、離線結算、縮放。原創代碼。 */
(function () {
  'use strict';
  const NS = window.Glimmer, D = NS.data, SIM = NS.sim, R = NS.render, UI = NS.ui, LIGHT = NS.light, EV = NS.events, BEH = NS.behavior, AUD = NS.audio.Engine;
  const P = D.PARAMS;
  const qs = new URLSearchParams(location.search);
  const G = { debug: qs.get('debug') === '1', timeScale: 1, hourOverride: qs.has('hour') ? +qs.get('hour') : null, mode: 'garden', autoDowngrade: qs.get('debug') !== '1', openDbg: qs.get('dbg') === 'open' };
  if (qs.get('period') && LIGHT.representativeHour(qs.get('period')) != null && !qs.has('hour')) G.hourOverride = LIGHT.representativeHour(qs.get('period'));   // ?period=morning|noon|evening|night
  if (qs.get('ev') === '0') EV.enabled = false;                       // ?ev=0 關閉事件（舊流程測試用）
  if (qs.get('atlas') === '0') D.PARAMS.art.useAtlas = false;         // ?atlas=0 強制程序化精靈
  if (qs.get('pending') === '1') D.PARAMS.art.usePending = true;      // ?pending=1 用圖集內待定 clip
  window.__glimmer = G; // 方便測試／除錯（只喺 ?debug=1 先有 UI 面板）
  // 假時鐘（遊測）：G.clock.fake=true 後 G.now() 只受 __qa.pet.clock 控制
  G.clock = { fake: false, t: 0 };
  G.now = () => (G.clock.fake ? G.clock.t : Date.now());
  G.hour = () => { if (G.hourOverride != null) return G.hourOverride; const d = new Date(G.now()); return d.getHours() + d.getMinutes() / 60; };

  // 低端機判定（預設畫質 low）：核心數或記憶體偏低
  G.lowEnd = function () { const Q = P.quality, n = navigator, hc = n.hardwareConcurrency, dm = n.deviceMemory; return (hc != null && hc <= Q.lowEndCores) || (dm != null && dm <= Q.lowEndMemGB); };

  // ── 存檔 ──
  function load() {
    let s = null, rep = null;
    try { const str = localStorage.getItem(P.saveKey); if (str) s = SIM.deserialize(str, G.now()); } catch (e) { /* 無法讀取 */ }
    if (!s) { s = SIM.newState(G.now()); const coarse = window.matchMedia && matchMedia('(pointer:coarse)').matches; s.settings.quality = qs.get('q') || (G.lowEnd() ? 'low' : coarse ? 'mid' : 'high'); }
    else { if (s.evs) s.evs.active = null; rep = SIM.applyOffline(s, G.now()); }   // 存檔內未完嘅 active 事件唔可續播：丟棄，否則 takePending 永遠被擋住
    if (qs.get('q')) s.settings.quality = qs.get('q');
    return { s, rep };
  }
  G.save = function () { try { G.state.lastSeen = Math.max(+G.state.lastSeen || 0, G.now());   // P1：lastSeen 只可向前（max），回撥時鐘唔可以拉後
    EV.markSave(G.state, G.now()); localStorage.setItem(P.saveKey, SIM.serialize(G.state)); } catch (e) { /* 私隱模式等 */ } };
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
    const uiScale = cssW / 390;
    document.getElementById('ui').style.transform = 'scale(' + uiScale + ')';
    // 熱區以縮放後嘅 CSS px 計。390 版面再乘 uiScale；360 闊直向（含整數倍像素縮放）都要 ≥44。
    const hit = Math.ceil((44 + 0.5) / uiScale);
    document.querySelectorAll('.ibtn').forEach((el) => { el.style.width = hit + 'px'; el.style.height = hit + 'px'; });
    G.layoutInfo = { vw, vh, dpr, kdev, kb, cssW, cssH };
  }
  window.addEventListener('resize', layout); layout();

  // ── 啟動 ──
  const boot = load(); G.state = boot.s;
  G.seed = qs.has('seed') ? (+qs.get('seed') >>> 0) : ((boot.s.seed >>> 0) || 1);
  G.beh = BEH.create(G.seed);
  G.light = LIGHT.compute(G.hour());
  G.ev = null; G.view = {};
  if (qs.get('room') === '1') P.art.daylightBg = true;                      // 可選房間皮膚（遊美 daylight bg）
  G.daylightReady = false;
  fetch(P.art.base + 'daylight/daylight.json').then(r => r.json()).then(j => { LIGHT.setDaylight(j); G.daylightJson = j; return G.renderer.loadDaylight(P.art.base); }).then(() => { G.daylightReady = G.renderer.dlReady; }).catch(e => { G.daylightError = String(e); });
  G.renderer.loadAtlases(P.art.base).then(() => { G.atlasReady = G.renderer.atlasReady; });
  UI.init(G);
  AUD.init(G);
  EV.noteOpen(G.state, { hour: G.hour(), now: G.now() });          // 當日第 2 次開 app 仍冇事件 → 保底
  { const w = EV.diaryWarn(G.state, G.now()); if (w) setTimeout(() => UI.toast('日記有 ' + w + ' 件小事 2 日後作廢，記得領'), 1500); }
  if (boot.rep && boot.rep.show) UI.showSummary(boot.rep);
  G.save();
  G.bootReport = boot.rep;

  // ── 主迴圈 ──
  let last = performance.now(), saveT = 0;
  const qm = { sum: 0, n: 0, slow: 0, grace: P.quality.graceFrames, lastAvg: 0, drops: 0 };   // rAF 幀間隔量度
  G.qm = qm;
  G.paused = false;
  function loop(ts) {
    const rawMs = ts - last, dtReal = Math.min(0.25, rawMs / 1000); last = ts;
    const s = G.state;
    if (!document.hidden) {
      const dtW = G.paused ? 0 : dtReal;
      SIM.advance(s, dtW * G.timeScale, { hour: (G.hourOverride != null || G.timeScale === 1) ? G.hour() : null, now: G.now() }, 30);
      saveT += dtReal; if (saveT >= P.autosaveSec) { saveT = 0; G.save(); }
      UI.update(dtW);
      const view = G.tickWorld(dtW);
      AUD.update(dtW, G.audioWorld);
      G.renderer.frame(dtReal, view);
      // 自動降畫質（非 debug）：用 rAF 幀間隔（唔再用連續掉幀計）。每 windowFrames 幀取平均間隔，連續 slowWindows 個窗口 > slowMs 先降一級
      if (G.autoDowngrade && s.settings.quality !== 'off') {
        if (qm.grace > 0) qm.grace--;
        else if (rawMs < 1000) {
          qm.sum += rawMs; qm.n++;
          if (qm.n >= P.quality.windowFrames) {
            qm.lastAvg = qm.sum / qm.n; qm.sum = 0; qm.n = 0;
            qm.slow = qm.lastAvg > P.quality.slowMs ? qm.slow + 1 : 0;
            if (qm.slow >= P.quality.slowWindows) {
              const order = ['high', 'mid', 'low', 'off']; const nq = order[Math.min(3, order.indexOf(s.settings.quality) + 1)];
              G.setQuality(nq); UI.toast('效能較低，已自動降低畫質'); qm.slow = 0; qm.drops++; qm.grace = P.quality.graceFrames;
            }
          }
        }
      }
    } else { qm.sum = 0; qm.n = 0; }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // ── 世界狀態：時段光、事件、寵物行為 ──
  G.lightWake = function () {                       // 睡眠中點寵物：輕喚醒（開燈起身＋睏睏表情），唔鬧脾氣、唔扣需求
    const s = G.state; if (!s.sleeping) return false;
    SIM.toggleSleep(s); if (G.beh) BEH.tap(G.beh, 'wake', 0);
    if (s.evs) s.evs.stats.tapSleepWake = (s.evs.stats.tapSleepWake || 0) + 1;
    G.save(); return true;
  };
  G.tickWorld = function (dt) {
    const s = G.state, hr = G.hour();
    G.light = LIGHT.compute(hr, G.weather ? { weather: G.weather } : null);
    const rd = G.renderer, mg = G.mode === 'minigame';
    // 事件：取出 pending → active（畫面提示卡＋視覺）
    if (!mg && !UI.isModalOpen() && !G.ev) { const a = EV.takePending(s); if (a) { G.ev = a; UI.showEventCard(a.rec); if (a.rec.id === 'flash') rd.flash = 0.8; } }
    if (G.ev) { G.renderer.drawEventIcon(document.getElementById('evicon'), G.ev.rec.id, G.ev.t); const done = EV.tickActive(s, dt); if (done) { G.ev = null; UI.hideEventCard(); } }
    const evView = G.ev ? { id: G.ev.rec.id, t: G.ev.t, dur: G.ev.dur, vis: EV.visual(G.ev.rec.id, G.ev.t, G.ev.dur) } : null;
    const act = rd.pet.act && rd.t < rd.pet.until ? rd.pet.act : null;
    G.behCtx = { s, pw: G.light, sun: G.light.sun, override: act, event: evView };
    if (!mg) { BEH.update(G.beh, dt, G.behCtx); rd.behFx(G.beh); }
    if (G.beh && G.beh.tantrumReq) { G.beh.tantrumReq = 0; EV.tapTantrum(s, { now: G.now(), hour: hr }); }   // 10 秒連點 5 下 → 獨立事件 grumpy_tap（唔共用需求鬧脾氣冷卻）
    if (!mg) G.audioWorld = { beh: G.beh, s, period: G.light.period, ev: G.ev ? { id: G.ev.rec.id, t: G.ev.t, dur: G.ev.dur } : null, mode: G.mode };
    else G.audioWorld = { beh: G.beh, s, period: G.light.period, ev: null, mode: G.mode };
    G.view = { state: s, quality: s.settings.quality, hour: hr, mode: G.mode, mg: UI.mgState() && UI.mgState().mg, light: G.light, beh: mg ? null : G.beh, event: evView };
    return G.view;
  };
  G.forceBeh = function (name) { BEH.force(G.beh, name, G.behCtx); };
  G.forceEvent = function (id) { return EV.force(G.state, id); };
  G.setPeriod = function (p) { G.hourOverride = p ? LIGHT.representativeHour(p) : null; };

  // ── 離開／返嚟 ──
  function onHide() { if (!window.__noSaveOnHide) G.save(); }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) onHide();
    else { const rep = SIM.applyOffline(G.state, G.now()); if (rep.show) EV.noteOpen(G.state, { hour: G.hour(), now: G.now() }); G.save(); last = performance.now(); if (rep.show) UI.showSummary(rep); }
  });
  window.addEventListener('pagehide', onHide);
  window.addEventListener('beforeunload', onHide);

  // ── 效能量度（測試用）──
  G.bench = function (quality, n) {
    const s = G.state, old = s.settings.quality; s.settings.quality = quality; const r = G.renderer; r.perfReset();
    const view = { state: s, quality, hour: G.hour(), mode: 'garden', light: G.light, beh: G.beh };
    for (let i = 0; i < 20; i++) r.frame(1 / 60, view); r.perfReset();
    for (let i = 0; i < n; i++) r.frame(1 / 60, view);
    const res = { quality, frames: r.perf.n, avgMs: +(r.perf.sum / r.perf.n).toFixed(2), maxMs: +r.perf.max.toFixed(2) };
    s.settings.quality = old; return res;
  };

  // ── 遊測介面：window.__qa.pet（行為日誌、種子、假時鐘、確定性快進）──
  window.__qa = window.__qa || {};
  window.__qa.pet = {
    get seed() { return G.seed; },
    get log() { return G.beh.journal; },                 // 行為日誌 [{n,t,ev,name,ph}]；ev＝state|phase|variant|clip|impact|tap
    clearLog() { G.beh.journal.length = 0; },
    reseed(seed) { G.seed = seed >>> 0; G.beh = BEH.create(G.seed); AUD.dir = NS.audio.createDirector(G.seed); return G.seed; },
    clock: {                                              // 假時鐘：use() 之後 G.now() 只跟 set／advance
      use(ms) { G.clock.fake = true; G.clock.t = ms == null ? Date.now() : ms; return G.clock.t; },
      set(ms) { G.clock.fake = true; G.clock.t = ms; return ms; },
      advance(sec) { G.clock.fake = true; G.clock.t += sec * 1000; return G.clock.t; },
      real() { G.clock.fake = false; },
      now() { return G.now(); },
      setHour(h) { G.hourOverride = h; },
    },
    pause(on) { G.paused = on !== false; },
    step(sec, chunk) {                                    // 確定性快進（暫停實時迴圈時用）：sim＋事件＋行為＋音訊導演
      chunk = chunk || 0.05; let left = sec;
      while (left > 1e-9) {
        const d = Math.min(chunk, left); left -= d;
        if (G.clock.fake) G.clock.t += d * 1000;
        SIM.advance(G.state, d, { hour: G.hour(), now: G.now() }, 30);
        G.tickWorld(d); AUD.update(d, G.audioWorld);
      }
      return this.state();
    },
    state() {
      const b = G.beh, E = G.state.evs;
      return { state: b.state, phase: b.phase, clip: b.clip, frame: b.frame, expr: b.expr, x: +b.x.toFixed(2), dir: b.dir, variant: b.variant, period: G.light.period, hour: +G.hour().toFixed(2),
        ev: G.ev ? G.ev.rec.id : null, pending: E ? E.pending.length : 0, diary: E ? E.diary.length : 0, needs: Object.assign({}, G.state.needs), t: +b.t.toFixed(2) };
    },
    force(name) { G.forceBeh(name); },
    forceEvent(id) { return G.forceEvent(id); },
    tapPet(n) { for (let i = 0; i < (n || 1); i++) { if (G.state.sleeping) G.lightWake(); else BEH.tap(G.beh, 'pet', 0); } },   // 模擬點寵物（睡眠中＝輕喚醒）
    lightWake() { return G.lightWake(); },
    events() { return G.state.evs; },
    eventLog() { return G.state.evs ? G.state.evs.log : []; },                    // 事件觸發紀錄 [{id,kind,day,date,hour,at,offline,diary}]
    claimedFlashDates() { return G.state.evs ? G.state.evs.claimedFlashDates.slice() : []; },   // 閃光日「已領」旗標（存檔內）
    daylight() { const d = G.light && G.light.daylight; return { ready: !!G.daylightReady, json: !!G.daylightJson, room: !!P.art.daylightBg, blendSeconds: G.daylightJson ? G.daylightJson.blendSeconds : null, dl: d ? { id: d.id, prev: d.prev, mix: +d.mix.toFixed(3), ambient: d.ambient.map(Math.round), bloom: +d.bloom.toFixed(3), vignette: +d.vignette.toFixed(3), petMul: d.pet.mul.map(Math.round) } : null, error: G.daylightError || G.renderer.dlError || null }; },
    lastSaveTime() { return G.state.lastSaveTime || null; },
    suppressed() { return G.state.evs ? EV.suppressed(G.state, G.state.evs) : false; },     // 時間回撥 → 當日唔抽事件／閃光
    flashToday() { const E = G.state.evs; return E ? { flashToday: E.flashToday, flashDone: E.flashDone, date: EV.dateKey(E), claimed: EV.flashClaimed(E) } : null; },
    pool() { return D.EVENTS.map(e => ({ id: e.id, weight: e.weight, hours: e.hours || null, rare: !!e.rare, cooldownH: e.cooldownH || (e.rare ? D.PARAMS.events.cooldownRareH : D.PARAMS.events.cooldownH), special: !!e.special, lowNeed: !!e.lowNeed })); },
    audio() { return AUD.status(); },
    audioLog() { return AUD.log; },
  };
})();
