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

  SIM.setHourFn(() => (G.hour ? G.hour() : new Date().getHours()));   // evo6：夜晚照顧（17:00–07:00）用遊戲本地鐘
  if (SIM.setRainFn) SIM.setRainFn(() => G.weather === 'rain');      // §7 水珠：落雨時照顧（天氣＝G.weather，DEV 時段「H3 雨」／?weather=rain）
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
  // ── evo6 ──
  G.fade = function () { const r = SIM.fade(G.state, G.now()); G.save(); return r; };
  G.evo = {
    info() { const s = G.state, fk = G.renderer && G.renderer.fkOf ? G.renderer.fkOf(s) : null; return { stage: s.stage, form: s.form, evoForm: D.evoForm(s.stage, s.form), drawForm: fk, gen: s.gen, fadeReady: !!s.fadeReady, growthH: +(s.growthSec / 3600).toFixed(3), stageH: P.stageSec[s.stage] / 3600, progress: +SIM.stageProgress(s).toFixed(4), lumi: SIM.lumiCheck(s), b5: SIM.branch5Check(s), force: (s.evo && s.evo.force) || null, care: SIM.careShare(s), migrated: s.migrated || null, memorial: s.memorial }; },
    // 浮動 overlay：只傳大細（Kotlin 照讀 form；sizeDp／size／pivot 係新欄）
    overlayInfo() { const s = G.state, ek = D.evoForm(s.stage, s.form), F = D.FORMS[ek], fs = F ? F.frameSize : 32;
      return { stage: s.stage, form: s.stage === 'egg' ? 'egg' : D.isBig(s.stage) ? (s.form === 'bright' ? 'radiant' : 'soft') : 'sprout', evoForm: ek, size: fs, pivot: [fs / 2, fs - 3], sizeDp: Math.round(fs * P.overlayDpPerPx) }; },
    overlayStatus() { return SIM.overlayStatus(G.state); },   // snapshot v3：心情／瞌覺／需求；v4：info（名／階段名／形態名／進度／幾日大）（fpet-bridge 讀，只讀）
    setStage(st, branch) {          // DEV：跳去某階段（成年／靜光可指定分支）；保留需求，成長歸零
      const s = G.state; if (!D.STAGES.includes(st)) throw new Error('evo.setStage: ' + st);
      if (branch && !D.BRANCHES.includes(branch)) throw new Error('evo.setStage branch: ' + branch);
      s.stage = st; s.growthSec = 0; s.fadeReady = false; s.sleeping = false;
      s.form = D.isBig(st) ? (branch || s.form || 'soft') : null;
      if (st !== 'egg' && s.needs.hunger <= 0) s.needs = Object.assign({}, P.startNeedsSprout);
      G.save(); return this.info(); },
    next() { const s = G.state; if (s.stage === 'elder') { s.growthSec = P.stageSec.elder; SIM.checkStage(s); return this.info(); } s.growthSec = P.stageSec[s.stage]; SIM.checkStage(s); G.save(); return this.info(); },   // DEV：下一階段（照正常規則判分支）
  };
  G.simOffline = function (h) { G.state.lastSeen = G.now() - h * 3600e3; const rep = SIM.applyOffline(G.state, G.now()); G.save(); UI.showSummary(rep); return rep; };

  // ── 縮放（整數倍像素）──
  const canvas = document.getElementById('gl');
  G.renderer = new R.Renderer(canvas);
  function layout() {
    const vw = window.innerWidth, vh = window.innerHeight, dpr = window.devicePixelRatio || 1;
    // P1-5：按短邊 fit（直向＝闊度、闊螢幕＝高度；唔再 floor 到整數倍而留大黑邊），畫面外由 #bgfill 延伸填滿
    const f = Math.min(vw / R.W, vh / R.H), fd = f * dpr;
    let kdev = Math.abs(fd - Math.round(fd)) < 0.02 && Math.round(fd) >= 2 ? Math.round(fd) : 0;
    const kb = kdev ? Math.min(kdev, 4) : Math.max(2, Math.min(4, Math.ceil(fd)));
    const cssW = R.W * f, cssH = R.H * f;
    if (G.renderer.k !== kb) G.renderer.setScale(kb);
    canvas.style.width = cssW + 'px'; canvas.style.height = cssH + 'px';
    canvas.style.imageRendering = (kdev && kb === kdev) || fd >= 3 ? 'pixelated' : 'auto';
    if (qs.get('orient') === 'landscape') document.documentElement.classList.add('force-landscape');
    const wrap = document.getElementById('stagewrap'); wrap.style.width = cssW + 'px'; wrap.style.height = cssH + 'px';
    const uiScale = cssW / 390;
    document.getElementById('ui').style.transform = 'scale(' + uiScale + ')';
    // 熱區以縮放後嘅 CSS px 計。390 版面再乘 uiScale；360 闊直向（含整數倍像素縮放）都要 ≥44。
    const hit = Math.ceil((44 + 0.5) / uiScale);
    document.querySelectorAll('.ibtn').forEach((el) => { el.style.width = hit + 'px'; el.style.height = hit + 'px'; });
    G.layoutInfo = { vw, vh, dpr, kdev, kb, cssW, cssH, hit, fit: vw / R.W <= vh / R.H ? 'width' : 'height', barsX: vw - cssW, barsY: vh - cssH };
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
  // 生命感（F1）：?live=0 停用；?face=off|native 臉模式；?bulb=0 關燈泡
  if (qs.get('face')) P.face.mode = qs.get('face');
  if (qs.get('bulb') === '0') P.face.bulb.enabled = false;
  G.liveReady = false;
  G.liveLoad = (P.face.liveliness.enabled && qs.get('live') !== '0') ? G.renderer.loadLive(P.face.liveliness).then((lv) => {
    Object.keys(D.CLIPS).filter(k => D.CLIPS[k].live).forEach(k => { D.CLIPS[k].ready = !!(lv && ['sprout', 'radiant', 'soft'].every(f => lv.atlas[f] && lv.atlas[f].json.animations[k + '_noface'])); });   // turn_back＋第二段 7 clip（live atlas 有先 ready）
    G.liveReady = !!lv; return lv;
  }) : Promise.resolve(null);
  // evo6：遊美 evo 形態 atlas（?evo=0 停用）；live atlas 載完先掛入 lv（evo form 有齊 std23＋生命感 clip）
  if (qs.get('evo') === '0') P.art.evo.enabled = false;
  G.evoReady = false;
  G.evoLoad = P.art.evo.enabled ? Promise.all([G.renderer.loadEvo(P.art.evo), G.liveLoad.catch(() => null)]).then(() => { G.renderer.attachEvoLive(); G.evoReady = Object.keys(G.renderer.evoOK || {}).length > 0; }) : Promise.resolve();
  G.liveSettled = false; G.liveLoad.then(() => { G.liveSettled = true; }, () => { G.liveSettled = true; });   // s3：重逢等 live atlas 載完先衝（rush 用真 clip）
  // HD-2D 場景（src/hd2d.js；?hd2d=0 → 舊程序化背景）：經 lighting addModifier（weather hook）＋ renderer.hd
  if (NS.hd2d) NS.hd2d.install(G, NS);
  UI.init(G);
  AUD.init(G);
  EV.noteOpen(G.state, { hour: G.hour(), now: G.now() });          // 當日第 2 次開 app 仍冇事件 → 保底
  { const w = EV.diaryWarn(G.state, G.now()); if (w) setTimeout(() => UI.toast('日記有 ' + w + ' 件小事 2 日後作廢，記得領'), 1500); }
  if (boot.rep && boot.rep.show) UI.showSummary(boot.rep);
  G.save();
  G.bootReport = boot.rep;
  if (G.state.fadeReady && G.state.stage === 'elder') G.state.ev.push({ type: 'fadeReady', form: G.state.form });   // evo6：上次揀「再陪多陣」→ 下次開 app 再問
  if (G.state.migrated && !G.state.migrated.told) { G.state.migrated.told = true; setTimeout(() => UI.toast('團絨而家係「' + D.STAGE_NAME[G.state.stage] + '」階段（成長表更新咗）'), 1200); }

  // ── 主迴圈 ──
  let last = performance.now(), saveT = 0;
  const qm = { sum: 0, n: 0, slow: 0, grace: P.quality.graceFrames, lastAvg: 0, drops: 0 };   // rAF 幀間隔量度
  G.qm = qm;
  G.paused = false;
  const bgfill = document.getElementById('bgfill'), bgx = bgfill ? bgfill.getContext('2d') : null; let bgN = 0;
  function loop(ts) {
    const rawMs = ts - last, dtReal = Math.min(0.25, rawMs / 1000); last = ts;
    const s = G.state;
    if (!document.hidden) {
      const dtW = G.paused ? 0 : dtReal;
      if (G.clockRun && G.clock.fake) G.clock.t += dtW * G.timeScale * 1000;   // 開發模式快進：假時鐘跟 ×N 行 → 時段／HD-2D 場景跟住變
      SIM.advance(s, dtW * G.timeScale, { hour: (G.hourOverride != null || G.timeScale === 1 || G.clockRun) ? G.hour() : null, now: G.now() }, 30);
      saveT += dtReal; if (saveT >= P.autosaveSec) { saveT = 0; G.save(); }
      UI.update(dtW);
      const view = G.tickWorld(dtW);
      AUD.update(dtW, G.audioWorld);
      G.renderer.frame(dtReal, view);
      if (bgfill && (++bgN % 6 === 0 || bgN < 3)) {   // P1-5：每 6 幀將畫面「cover」縮細入 24×52 → CSS 放大＝模糊延伸背景（極平）
        const want = Math.max(8, Math.round(52 * window.innerWidth / Math.max(1, window.innerHeight))); if (bgfill.width !== want) bgfill.width = want;
        const bw = bgfill.width, bh = bgfill.height, sc = Math.max(bw / canvas.width, bh / canvas.height), dw = canvas.width * sc, dh = canvas.height * sc;
        bgx.imageSmoothingEnabled = true; bgx.drawImage(canvas, (bw - dw) / 2, (bh - dh) / 2, dw, dh); G.bgfillN = bgN;
      }
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
    if (SIM.notePetSleep) SIM.notePetSleep(s);       // §7 月眠：瞓覺時撫摸
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
    G.beh.demo = G.liveDemo;
    if (!mg && G.reunionPending) G.reunionTick();                                  // s3 D5：離線 ≥6h 返嚟 → 衝埋嚟重逢
    if (!mg) { BEH.update(G.beh, dt, G.behCtx); rd.behFx(G.beh); }
    if (G.beh && G.beh.tantrumReq) { G.beh.tantrumReq = 0; EV.tapTantrum(s, { now: G.now(), hour: hr }); }   // 10 秒連點 5 下 → 獨立事件 grumpy_tap（唔共用需求鬧脾氣冷卻）
    if (!mg) G.audioWorld = { beh: G.beh, s, period: G.light.period, ev: G.ev ? { id: G.ev.rec.id, t: G.ev.t, dur: G.ev.dur } : null, mode: G.mode, rain: !!(G.hd && G.hd.on() && G.hd.st && G.hd.st.cur === 'H3rain') };
    else G.audioWorld = { beh: G.beh, s, period: G.light.period, ev: null, mode: G.mode };
    G.view = { state: s, quality: s.settings.quality, hour: hr, mode: G.mode, mg: UI.mgState() && UI.mgState().mg, light: G.light, beh: mg ? null : G.beh, event: evView };
    return G.view;
  };
  G.forceBeh = function (name) { BEH.force(G.beh, name, G.behCtx); };
  // 生命感 s2b：開發者「即刻觸發」＋「展示模式」（頻率 ×5／冷卻 ÷5；localStorage，預設關）
  { const LVP = P.beh.live;
    G.liveDemo = (() => { try { return localStorage.getItem(LVP.demoKey) === '1'; } catch (e) { return false; } })();
    G.setLiveDemo = function (on) { G.liveDemo = !!on; try { if (G.liveDemo) localStorage.setItem(LVP.demoKey, '1'); else localStorage.removeItem(LVP.demoKey); } catch (e) { } G.beh.demo = G.liveDemo; return G.liveDemo; };
    G.liveNow = function (k) {
      if (k === 'bulb') return G.bulbCycle();                                                       // s3 G1：循環 5 心情
      if (k === 'reunion') { G.reunionCheck({ T: LVP.nowAwayH * 3600, tampered: false }, { force: true, src: 'dev' }); G.reunionTick(); return true; }   // s3 D5：模擬久未開（唔郁需求／存檔）
      if (BEH.NOW.indexOf(k) < 0) return false; G.beh.demo = G.liveDemo; BEH.force(G.beh, 'now_' + k, G.behCtx || {}); return true; };
    G.beh.demo = G.liveDemo;
    // ── 生命感第三段 ──
    // G1：燈泡心情強制（null＝跟心情自動）；循環 happy→neutral→sleepy→hungry→grumpy→自動
    G.bulbCycle = function () { const C = LVP.bulbCycle, i = C.indexOf(G.beh.bulbForce); G.beh.bulbForce = i < 0 ? C[0] : i + 1 < C.length ? C[i + 1] : null; return G.beh.bulbForce || 'auto'; };
    // D5：sim applyOffline 報告（lastSeen 存喺 localStorage 存檔；P1 只向前）離線 ≥reunionAwayH 小時、冇改時鐘、唔係蛋 → 等冇彈窗／事件／瞓覺先衝埋嚟；每日最多 1 次（日子存 localStorage）
    const dayOf = (ms) => { const d = new Date(ms); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); };
    G.reunionPending = null; G.reunionLast = null; G.reunionSkip = null;
    G.reunionCheck = function (rep, o) {
      o = o || {}; G.reunionSkip = null;
      if (!rep || rep.tampered || !(rep.T >= LVP.reunionAwayH * 3600)) { G.reunionSkip = rep ? (rep.tampered ? 'tampered' : 'short') : 'none'; return false; }
      if (G.state.stage === 'egg') { G.reunionSkip = 'egg'; return false; }
      let day = null; try { day = localStorage.getItem(LVP.reunionDayKey); } catch (e) { }
      if (!o.force && day === dayOf(G.now())) { G.reunionSkip = 'today'; return false; }
      G.reunionPending = { T: Math.round(rep.T), at: performance.now(), src: o.src || 'offline' }; return true;
    };
    G.reunionTick = function () {
      const q = G.reunionPending; if (!q) return false;
      if (performance.now() - q.at > 120000) { G.reunionPending = null; G.reunionSkip = 'expired'; return false; }   // 2 分鐘內做唔到就算
      if (G.mode === 'minigame' || UI.isModalOpen() || G.ev || G.state.sleeping || G.state.stage === 'egg' || (G.beh && G.beh.expr === 'unwell') || !G.liveSettled || (G.renderer.pet.act && G.renderer.t < G.renderer.pet.until)) return false;   // 等摘要「收下光粒」嘅開心反應做完先衝
      G.reunionPending = null; if (q.src !== 'dev') try { localStorage.setItem(LVP.reunionDayKey, dayOf(G.now())); } catch (e) { }
      G.reunionLast = { T: q.T, src: q.src, at: G.now() }; G.beh.demo = G.liveDemo; BEH.force(G.beh, 'now_reunion', G.behCtx || {}); return true;
    };
  }
  G.reunionCheck(boot.rep);                                          // s3 D5：開 app 時離線 ≥6h → 摘要關咗之後衝埋嚟
  G.forceEvent = function (id) { return EV.force(G.state, id); };
  G.setPeriod = function (p) { G.hourOverride = p ? LIGHT.representativeHour(p) : null; };

  // ── 離開／返嚟 ──
  function onHide() { if (!window.__noSaveOnHide) G.save(); }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) onHide();
    else { const rep = SIM.applyOffline(G.state, G.now()); if (rep.show) EV.noteOpen(G.state, { hour: G.hour(), now: G.now() }); G.save(); last = performance.now(); if (rep.show) UI.showSummary(rep); G.reunionCheck(rep); }
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
        ev: G.ev ? G.ev.rec.id : null, pending: E ? E.pending.length : 0, diary: E ? E.diary.length : 0, needs: Object.assign({}, G.state.needs), t: +b.t.toFixed(2),
        show: b.show.clip, showFrame: b.show.frame, gait: b.walkStyle, micro: b.state === 'micro' && b.seq && b.seq[b.seqI] ? (b.seq[b.seqI].tag || b.seq[b.seqI].clip) : null, bug: b.bug ? b.bug.st : null, pose: b.pose ? +b.pose.rot.toFixed(3) : 0, face: Object.assign({}, b.face) };
    },
    force(name) { G.forceBeh(name); },
    now(k) { return G.liveNow(k); },                                              // s2b 即刻觸發：sniff／lookup／swat／scratch／sneeze／happy／drag／smug
    demo(on) { if (on != null) G.setLiveDemo(on); return G.liveDemo; },
    // ── 生命感第三段（D3／D5／G1）──
    nuzzle(x, y) { BEH.nuzzle(G.beh, x == null ? G.beh.x + G.beh.dir * 16 : x, y == null ? -24 : y); }, nuzzleEnd() { BEH.nuzzleEnd(G.beh); },
    reunion() { return { pending: G.reunionPending ? Object.assign({}, G.reunionPending) : null, last: G.reunionLast, skip: G.reunionSkip, day: (() => { try { return localStorage.getItem(P.beh.live.reunionDayKey); } catch (e) { return null; } })() }; },
    bulb(m) { if (m !== undefined) G.beh.bulbForce = m || null; const l = G.renderer.faceStat.last || {}; return { force: G.beh.bulbForce, drawn: l.bulb ? Object.assign({}, l.bulb) : null, auto: G.renderer.bulbMood(Object.assign({}, G.beh, { bulbForce: null })) }; },
    gaitForce() { const g = G.beh.gaitForce; return g ? { g: g.g, left: +(g.until - G.beh.t).toFixed(2) } : null; },
    forceEvent(id) { return G.forceEvent(id); },
    tapPet(n) { for (let i = 0; i < (n || 1); i++) { if (G.state.sleeping) G.lightWake(); else BEH.tap(G.beh, 'pet', G.beh.x + G.beh.dir * 5, -20); } },   // 點寵物前面（唔觸發 D2 轉身）
    // ── 生命感第一段（F1／F2／D2）──
    tap(x, y) { BEH.tap(G.beh, 'pet', x, y == null ? -20 : y); },               // 指定觸點（相對地面中心 CX／GROUND_Y，art px）
    gaze() { const L = G.beh.look; return { q: L.q, ql: L.ql, src: L.src, x: +L.x.toFixed(3), y: +L.y.toFixed(3), tx: +L.tx.toFixed(3), ty: +L.ty.toFixed(3), force: L.force, dir: G.beh.dir, turn: G.beh.turn ? Object.assign({}, G.beh.turn) : null }; },
    face() { const f = G.beh.face, r = G.renderer, l = r.faceStat.last || {}; return { eyes: f.eyes, mouth: f.mouth, gaze: f.gaze, closed: f.closed, clip: f.clip, frame: f.frame, blink: f.blink, mode: P.face.mode, live: !!l.live, bugArt: l.bugArt, liveReady: !!G.liveReady, liveError: r.lvError, drawnClip: l.clip, drawnFrame: l.frame, faceVisible: !!l.faceVisible, pieces: l.eyes ? l.eyes.concat([l.mouth]) : [], placeholder: (l.placeholder || []).slice(), derived: !!l.derived, bulb: l.bulb || null, form: l.form || null, evo: !!l.evo, fallbackFrom: l.fallbackFrom || null, stat: { draws: r.faceStat.draws, tints: r.faceStat.tints, overlays: r.faceStat.overlays, faceDrawn: r.faceStat.faceDrawn, faceHidden: r.faceStat.faceHidden, placeholder: r.faceStat.placeholder, bulb: r.faceStat.bulb } }; },
    setGaze(q) { G.beh.look.force = q || null; return q; },
    hitBox() {                                          // P2：寵物觸控區（art 座標＋CSS px 尺寸）
      const h = NS.ui.petHitBox ? NS.ui.petHitBox() : null; if (!h) return null; const r = canvas.getBoundingClientRect(), k = r.width / R.W;
      return Object.assign({}, h, { css: { x: r.left + h.x * k, y: r.top + h.y * k, w: h.w * k, h: h.h * k }, bodyCss: h.body ? { x: r.left + h.body.x * k, y: r.top + h.body.y * k, w: h.body.w * k, h: h.body.h * k } : null });
    },
    drag(x, y) { BEH.drag(G.beh, x, y); }, dragEnd() { BEH.dragEnd(G.beh); },                    // QA：強制 gaze 格（null＝自動）
    setFace(o) { G.beh.faceForce = o || null; return o; },                     // QA：強制 {eyes, mouth}（null＝自動）
    faceMode(m) { P.face.mode = m || 'auto'; return P.face.mode; },             // auto｜native（舊 atlas 原臉）｜off（唔畫臉）
    faceStatReset() { const fs = G.renderer.faceStat; for (const k in fs) if (typeof fs[k] === 'number') fs[k] = 0; },   // 模擬點寵物（睡眠中＝輕喚醒）
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
  // 隱藏開發模式（src/devpanel.js）：標題／左上角 1.5 秒內點 5 下開關；?dev=1 預設打開
  if (NS.devpanel) NS.devpanel.install(G, NS);
})();
