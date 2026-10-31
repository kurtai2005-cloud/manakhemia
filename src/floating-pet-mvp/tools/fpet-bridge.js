/* 浮動團絨最細 bridge（冇 Capacitor 時乜都唔做）。
 * - 寫 snapshot：Preferences 'glimmer.snapshot' = {v,form,mood,ts}（form 只限 sprout／radiant／soft，螢絨唔入）
 * - 返 app 時 replay overlay queue：每次互動 mood +1，每日最多 +5（按互動發生嗰日，本地時間），冇獎勵、冇事件。 */
(function () {
  var C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  var P = C.Plugins || {}, Pref = P.Preferences, FP = P.FloatingPet;
  if (!Pref || !FP) return;
  var DAILY_KEY = 'fpet_daily_v1', CAP = 5;
  function G() { return window.__glimmer; }
  function formOf(s) {
    if (!s || s.stage !== 'adult') return 'sprout';
    if (s.form === 'bright') return 'radiant';
    return 'soft';   // soft；其他（含螢絨／dust）一律柔光
  }
  function dayKey(t) { var d = new Date(t); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function writeSnapshot() {
    var g = G(); if (!g || !g.state) return;
    var s = g.state;
    var snap = { v: 1, form: formOf(s), mood: Math.round((s.needs && s.needs.mood) || 0), ts: Date.now() };
    Pref.set({ key: 'glimmer.snapshot', value: JSON.stringify(snap) }).catch(function () {});
  }
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
  function boot(n) { if (G() && G().state) { replay(); setInterval(writeSnapshot, 30000); return; } if (n < 100) setTimeout(function () { boot(n + 1); }, 200); }
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') replay(); else writeSnapshot(); });
  window.__fpetBridge = { replay: replay, writeSnapshot: writeSnapshot };
  boot(0);
})();
