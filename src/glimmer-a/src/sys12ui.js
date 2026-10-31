/* 《微光小圃》 sys12ui.js — systems12 第 1 批：瀏覽器膠水（main.js 掛入；DOM／renderer／hd2d）。原創代碼。
   系統 7：自動天氣寫入 G.weather（DEV 抽屜／?weather=／__qa.hd2d.weather 一改就 manual，DEV「自動」掣還原）；季節 → hd2d 季節層；
   團絨：落雨 idle 撐葉、霧／冬打冷震機率加大（renderer.sysPet overlay clip）。
   測試確定性：navigator.webdriver（Playwright）預設唔開自動天氣／季節層（?wxauto=1、?season=auto|spring|… 先開）。 */
(function () {
  'use strict';
  function install(G, NS) {
    const D = NS.data, P = D.PARAMS, X = NS.sys12, C = P.systems12, qs = new URLSearchParams(location.search), wd = !!(navigator && navigator.webdriver);
    const wq = qs.get('weather'), sq = qs.get('season');
    const wx = G.wx = {
      auto: C.weather.auto !== false && qs.get('wxauto') !== '0' && (!wd || qs.get('wxauto') === '1'),
      manual: !!(wq && P.evo6.branch.weather.states.includes(wq)),
      seasonMode: sq && (sq === 'auto' || sq === 'none' || X.SEASON_NAME[sq]) ? sq : (wd ? 'none' : 'auto'),
      season: null, autoWeather: null, acc: 1e9, shiverAt: null, log: [],
    };
    if (wx.manual) G.weather = wq === 'clear' ? null : wq;
    G.wxTick = function (force) {
      const now = G.now(), w = X.weatherAt(now, G.state.seed >>> 0);
      wx.autoWeather = w;
      if (wx.auto && !wx.manual) { const nw = w === 'clear' ? null : w; if ((G.weather || null) !== nw) { wx.log.push({ t: now, from: G.weather || 'clear', to: w }); if (wx.log.length > 50) wx.log.shift(); } G.weather = nw; }
      const ss = wx.seasonMode === 'auto' ? X.seasonOf(now) : wx.seasonMode === 'none' ? null : wx.seasonMode;
      wx.season = ss; if (G.hd) G.hd.season = ss;
      return { weather: G.weather || 'clear', auto: w, manual: wx.manual, season: ss };
    };
    /* DEV／QA：'auto' → 跟返自動；其他（clear／overcast／rain／fog）→ manual 覆蓋 */
    G.weatherSet = function (w) {
      if (w === 'auto') { wx.manual = false; wx.auto = true; } else { wx.manual = true; G.weather = w && w !== 'clear' && P.evo6.branch.weather.states.includes(w) ? w : null; }
      return G.wxTick(true);
    };
    G.seasonSet = function (m) { wx.seasonMode = m === 'auto' || m === 'none' || X.SEASON_NAME[m] ? m : 'auto'; if (G.hd && wx.seasonMode !== 'none' && wx.seasonMode !== 'auto') G.hd.loadSeason(wx.seasonMode); return G.wxTick(true); };
    /* 團絨天氣小動作：落雨 → 撐葉（idle 循環）；每 shiverEverySec 擲一次打冷震（霧／冬 ×倍數） */
    const rd = G.renderer, SP = rd.sysPet = rd.sysPet || { umbrella: false, one: null };
    G.sysPlay = function (clip, o) { const Cd = D.SYS_CLIPS[clip]; if (!Cd) return false; o = o || {}; SP.one = { clip, start: rd.t || 0, dur: o.dur || Cd.frames / Cd.fps * (Cd.repeat || 1), tell: !!Cd.tell || !!o.any }; return true; };
    function petTick(dt) {
      const s = G.state, W = C.weather, rain = (G.weather || 'clear') === 'rain' && s.stage !== 'egg' && !s.sleeping;
      SP.umbrella = rain;
      if (s.stage === 'egg' || s.sleeping) return;
      const t = rd.t || 0; if (wx.shiverAt == null) wx.shiverAt = t + W.shiverEverySec[0] + Math.random() * (W.shiverEverySec[1] - W.shiverEverySec[0]);
      if (t >= wx.shiverAt) {
        wx.shiverAt = t + W.shiverEverySec[0] + Math.random() * (W.shiverEverySec[1] - W.shiverEverySec[0]);
        const mul = X.shiverMul(G.weather || 'clear', wx.season), p = mul > 1 ? Math.min(1, W.shiverBaseChance * mul) : 0;   // 只喺霧／冬先打冷震
        if (!SP.one && !rain && Math.random() < p) G.sysPlay('shiver');
      }
    }
    G.sysTick = function (dt) { wx.acc += dt; if (wx.acc >= 1) { wx.acc = 0; G.wxTick(); } petTick(dt); };
    G.wxTick(true);
    window.__qa = window.__qa || {};
    window.__qa.sys12 = Object.assign(window.__qa.sys12 || {}, {
      weather: (w) => (w !== undefined ? G.weatherSet(w) : G.wxTick()), season: (m) => (m !== undefined ? G.seasonSet(m) : G.wxTick()),
      wx: () => Object.assign({}, wx, { weatherNow: NS.sim.weatherNow(), scene: G.hd ? G.hd.current().variant : null, umbrella: SP.umbrella, one: SP.one && SP.one.clip, shown: rd.sysShown || null, sysLog: rd.sysLog || [] }),
      play: (c, o) => G.sysPlay(c, o), simulate: (seed, from, days) => X.simulate(seed, from, days),
    });
  }
  window.Glimmer = window.Glimmer || {}; window.Glimmer.sys12ui = { install };
})();
