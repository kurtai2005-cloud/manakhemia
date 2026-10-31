/* 浮動團絨最細 bridge（冇 Capacitor 時乜都唔做）。
 * - 寫 snapshot：Preferences 'glimmer.snapshot' = {v,form,mood,ts}（form 只限 sprout／radiant／soft，螢絨唔入）
 *   evo6（v2）：加 stage／evoForm／size（px）／pivot／sizeDp（跟 __glimmer.evo.overlayInfo()；舊 Kotlin 照讀 form，唔識新欄都唔會壞）
 *   v3（Kurt 10-31 批：懸浮同步心情／瞌覺／需求）：加 moodBand（happy／ok／sad）、sleeping、needs{urgent,level,warnAt,vals,rate,rateAwake,floor,wakeAt}
 *   （跟 __glimmer.evo.overlayStatus()；舊 www 冇呢個就由 state.needs 簡單計，冇推算率）。狀態一變（每 2 秒比較簽名）即寫，唔止靠 30 秒。
 *   v4（Kurt 10-31 22:50：長按顯示遊戲狀態）：加 info{name,gen,stage,stageName,sub,form,formName,evoForm,progress,stageH,leftH,ageSec,days,unwell,fadeReady}
 *   （overlayStatus().info；冇就保持 v3）。evoForm／階段／日數一變都即寫（懸浮即刻換同遊戲一樣嘅形態）。
 * - 返 app 時 replay overlay queue：每次互動 mood +1，每日最多 +5（按互動發生嗰日，本地時間），冇獎勵、冇事件。 */
(function () {
  var C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  var P = C.Plugins || {}, Pref = P.Preferences, FP = P.FloatingPet;
  if (!Pref || !FP) return;
  var DAILY_KEY = 'fpet_daily_v1', CAP = 5;
  function G() { return window.__glimmer; }
  function formOf(s) {
    if (!s || (s.stage !== 'adult' && s.stage !== 'elder')) return 'sprout';   // evo6：靜光當成年
    if (s.form === 'bright') return 'radiant';
    return 'soft';   // soft；其他（含螢絨／dust）一律柔光
  }
  function dayKey(t) { var d = new Date(t); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function writeSnapshot() {
    var g = G(); if (!g || !g.state) return;
    var s = g.state;
    var snap = { v: 1, form: formOf(s), mood: Math.round((s.needs && s.needs.mood) || 0), ts: Date.now() };
    var ov = g.evo && g.evo.overlayInfo ? g.evo.overlayInfo() : null;
    if (ov) { snap.v = 2; snap.stage = ov.stage; snap.evoForm = ov.evoForm; snap.size = ov.size; snap.pivot = ov.pivot; snap.sizeDp = ov.sizeDp; }
    var st = statusOf(g);
    if (st) { snap.v = 3; snap.moodBand = st.moodBand; snap.sleeping = !!st.sleeping; snap.egg = !!st.egg;
      snap.needs = { urgent: st.urgent || null, level: st.level, warnAt: st.warnAt, vals: st.vals || null, rate: st.rate || null, rateAwake: st.rateAwake || null, floor: st.floor, wakeAt: st.wakeAt };
      if (st.info && typeof st.info === 'object') { snap.v = 4; snap.info = st.info; } }
    lastSig = sigOf(g);
    Pref.set({ key: 'glimmer.snapshot', value: JSON.stringify(snap) }).catch(function () {});
  }
  function statusOf(g) {
    try {
      if (g.evo && g.evo.overlayStatus) return g.evo.overlayStatus();
      var s = g.state, n = s.needs; if (!n) return null;
      if (s.stage === 'egg') return { egg: true, moodBand: 'ok', sleeping: false, urgent: null, warnAt: 30 };
      var lk = null; ['hunger', 'mood', 'clean', 'energy'].forEach(function (k) { if (lk === null || n[k] < n[lk]) lk = k; });
      return { egg: false, moodBand: n.mood > 60 ? 'happy' : n.mood < 30 ? 'sad' : 'ok', sleeping: !!s.sleeping, urgent: n[lk] < 30 ? lk : null, level: Math.round(n[lk]), warnAt: 30 };
    } catch (e) { return null; }
  }
  var lastSig = '';
  function sigOf(g) {
    var st = statusOf(g) || {}, ov = g.evo && g.evo.overlayInfo ? g.evo.overlayInfo() : {}, s = g.state || {};
    var inf = st.info || {};
    return [formOf(s), ov.sizeDp, ov.evoForm || '-', st.moodBand, !!st.sleeping, st.urgent || '-', !!st.egg, inf.stage || '-', inf.days == null ? '-' : inf.days, !!inf.unwell, !!inf.fadeReady].join('|');
  }
  function maybeWrite() { var g = G(); if (!g || !g.state) return; if (sigOf(g) !== lastSig) writeSnapshot(); }
  var busy = false;
  function replay() {
    var g = G(); if (!g || !g.state || busy) return;
    busy = true;
    FP.drainQueue().then(function (r) {
      var items = (r && r.items) || [];
      if (items.length) {
        var daily = {}; try { daily = JSON.parse(localStorage.getItem(DAILY_KEY) || '{}') || {}; } catch (e) {}
        var s = g.state, applied = 0;
        items.forEach(function (it) {
          var k = dayKey(+it.t || Date.now()), n = daily[k] || 0;
          if (n >= CAP) return;
          daily[k] = n + 1; applied++;
          if (s.needs) s.needs.mood = Math.min(100, (+s.needs.mood || 0) + 1);
        });
        var keep = {}, today = dayKey(Date.now()); Object.keys(daily).slice(-7).forEach(function (k) { keep[k] = daily[k]; }); keep[today] = keep[today] || daily[today] || 0;
        try { localStorage.setItem(DAILY_KEY, JSON.stringify(keep)); } catch (e) {}
        if (applied && g.save) g.save();
        console.log('[fpet] replay', items.length, 'interactions, mood +' + applied);
      }
      writeSnapshot();
    }).catch(function (e) { console.warn('[fpet] replay fail', e); }).then(function () { busy = false; });
  }
  function boot(n) { if (G() && G().state) { replay(); setInterval(writeSnapshot, 30000); setInterval(maybeWrite, 2000); return; } if (n < 100) setTimeout(function () { boot(n + 1); }, 200); }
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') replay(); else writeSnapshot(); });
  window.__fpetBridge = { replay: replay, writeSnapshot: writeSnapshot, maybeWrite: maybeWrite, statusOf: function () { return statusOf(G()); } };
  boot(0);
})();
