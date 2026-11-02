/* 《微光小圃》 touchui.js — 第 3 批 3a 瀏覽器膠水（docs-gdd/batch3-fun-spec.md §①②）。原創代碼。
   ui.js 寵物觸控 → G.tch.down/move/up（手勢辨識＝touch.js）；devicemotion → 搖機；每幀 G.touchTick → 動作寫入 G.beh.gest／faceGest（render 有遊美反應圖就播 clip，冇就程序化）。
   扮醒呆：idle ≥20s 後每 60s 抽 25%（最少隔 3 分鐘、每日 8 次）；Playwright（navigator.webdriver）預設唔自動抽（?dumb=1 先開），__qa.touch 直接觸發。
   心情：每種手勢每日第一次 +1，同浮動團絨共用每日 ≤5（localStorage fpet_daily_v1）；唔加路線分。所有句經 G.say（提示排隊）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.touchui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const T = NS.touch, D = NS.data, P = D.PARAMS.touch, X = NS.sys12, BEH = NS.behavior;
    if (!T || !P || P.enabled === false) return false;
    const qs = new URLSearchParams(location.search), wd = !!(navigator && navigator.webdriver);
    const store = { get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { } } };
    const sec = () => performance.now() / 1000, S = () => G.state;
    const rec = T.createRecognizer(), shk = T.createShake(), RC = NS.reactclip;
    const RX = () => (G.renderer && G.renderer.rx && G.renderer.rx.ready ? G.renderer.rx : null);   // 遊美 batch3a 反應圖（載完先用）
    const clipOf = (key) => { const M = T.MOTIONS[key], rx = RX(); return (M && M.clip && rx && rx.clips[M.clip]) || null; };
    const clipSec = (key) => { const c = clipOf(key); return c && !c.loop ? c.dur / 1000 : null; };
    const lineAt = (key) => { const c = clipOf(key), ev = c && (c.events || []).find(e => /^line:/.test(e.id)); return ev ? ev.t / 1000 : null; };   // 對白只經 clip 嘅 line:* event（冇就用 35%）
    const TS = G.touchSt = { act: null, log: [], grants: [], lastInput: sec(), lastRoll: -1e9, autoDumb: qs.get('dumb') === '1' || (!wd && qs.get('dumb') !== '0'), press: null, rolls: 0 };
    const busyWorld = () => G.mode === 'minigame' || !!G.mg2Busy || (NS.ui && NS.ui.isModalOpen && NS.ui.isModalOpen()) || !!(G.s12 && G.s12.open);
    const say = (line, o) => (G.say ? G.say(Object.assign({ line, src: 'touch' }, o || {})) : null);
    function setAct(key, x, extra) { TS.act = Object.assign({ key, t0: sec(), x: x || {}, secOv: clipSec(key), lastMs: -1 }, extra || {}); TS.log.push({ key, t: Date.now() }); if (TS.log.length > 40) TS.log.shift(); return TS.act; }
    function hush(s) { const b = G.beh; if (b) b.hushUntil = b.t + s; }
    function grant(kind) { const r = T.moodGrant(S(), kind, G.now(), store); TS.grants.push({ kind, ok: r.ok, reason: r.reason || null }); if (TS.grants.length > 40) TS.grants.shift(); if (r.ok && G.save) G.save(); return r; }
    const dumbOn = () => TS.act && TS.act.dumb;
    function caught() { TS.act = null; setAct('d_caught'); hush(P.dumb.caughtSec); say(T.LINES.caught, { urgent: true, sec: 2.5, src: 'dumb' }); }
    function onGesture(e) {
      const s = S(); if (!s || s.stage === 'egg' || busyWorld()) return;
      if (s.sleeping) { setAct('g_rub'); return; }                         // 瞓覺中：揉眼翻身，唔加心情
      switch (e.k) {
        case 'poke': grant('poke'); if (dumbOn()) caught(); else if (!TS.act || /^g_(poke|hold)$/.test(TS.act.key)) setAct('g_poke'); break;
        case 'hold': grant('hold'); if (dumbOn()) caught(); else setAct('g_hold', null, { held: true }); break;
        case 'pat': if (X && X.notePat) X.notePat(s, G.now(), s.ev); if (TS.press) TS.press.patDone = true; if (NS.ui && NS.ui.processEvents) NS.ui.processEvents(); break;   // 持續 3s ＝ 一次摸頭（委託；唔計路線分）
        case 'tickle': grant('tickle'); if (dumbOn()) caught(); else setAct('g_tickle'); break;
        case 'roll': setAct('g_roll'); say(T.LINES.tickle, { src: 'tickle' }); break;
        case 'pull': grant('pull'); setAct('g_spring', { d: Math.max(-1, Math.min(1, e.dx / 120)) }); break;
        case 'release': if (TS.act && TS.act.held) TS.act = null; break;
        case 'shake': grant('shake'); if (e.dizzy) { if (dumbOn()) TS.act = null; setAct('g_dizzy'); hush(P.shake.dizzySec); }
          if (e.brag) { if (!e.dizzy && !dumbOn()) { const at = lineAt('g_brag'); setAct('g_brag', null, { line: T.LINES.brag, said: at == null, sayAt: at }); if (at == null) say(T.LINES.brag, { src: 'shake' }); } else say(T.LINES.brag, { src: 'shake' }); } break;   // 60s 內第 3 次：扮冇事（touch_shake_pretend；句跟 line:shake_pretend）
      }
    }
    const drain = () => { for (const e of rec.drain()) onGesture(e); };
    /* ui.js 寵物觸控（CSS px） */
    G.tch = {
      down(x, y) { TS.lastInput = sec(); TS.press = { patDone: false }; rec.down(sec(), x, y); },
      move(x, y) { const p = rec.active(); if (!p) return; rec.move(sec(), x, y); drain(); const d = Math.hypot(x - p.x0, y - p.y0);
        if (!p.tickle && d > P.pull.px && !S().sleeping) { const n = Math.max(-1, Math.min(1, (x - p.x0) / 120)); if (TS.act && TS.act.key === 'g_pull') TS.act.x.d = n; else setAct('g_pull', { d: n }, { held: true }); } },
      up(x, y, cancel) { const pr = TS.press; TS.press = null; rec.up(sec(), x, y, cancel); drain(); if (TS.act && TS.act.key === 'g_pull') TS.act = null; return pr || { patDone: false }; },
      sleepTouch() { TS.lastInput = sec(); setAct('g_rub'); },
    };
    window.addEventListener('pointerdown', () => { TS.lastInput = sec(); }, true);
    window.addEventListener('devicemotion', (ev) => {
      const a = ev.accelerationIncludingGravity; if (!a || a.x == null) return;
      const g = Math.hypot(a.x || 0, a.y || 0, a.z || 0) / 9.81; G.touchShake(g);
    });
    G.touchShake = function (g, t) { const r = shk.sample(t == null ? sec() : t, g); if (r) { TS.lastInput = sec(); onGesture(r); } return r; };
    /* 扮醒呆 */
    function dumbGo(k, force) {
      const s = S(), b = G.beh; if (!b) return null;
      if (!force && (b.state !== 'stay' || b.variant)) return null;
      if (b.state !== 'stay' && BEH && BEH.force) BEH.force(b, 'stay', G.behCtx || { s });
      const r = T.dumbStart(s, k, G.now(), Math.random), M = T.MOTIONS['d_' + k], ds = clipSec('d_' + k) || M.sec, la = lineAt('d_' + k);
      setAct('d_' + k, null, { dumb: k, said: false, line: r.line, sayAt: la != null ? la : ds * 0.35 }); hush(ds + 0.3);
      s.ev && s.ev.push({ type: 'touch', what: 'dumb', k, first: r.first, n: r.n });
      if (G.save) G.save(); return r;
    }
    function dumbTick() {
      const now = sec(), s = S(); if (!TS.autoDumb || TS.act || busyWorld() || G.ev || G.reunionPending || !s || s.stage === 'egg' || s.sleeping) return null;
      if (now - TS.lastInput < P.dumb.idleSec || now - TS.lastRoll < P.dumb.everySec) return null;
      const b = G.beh; if (!b || b.state !== 'stay' || b.variant) return null;
      TS.lastRoll = now; TS.rolls++;
      const k = T.dumbRoll(s, G.now(), Math.random); return k ? dumbGo(k) : null;
    }
    /* 每幀（main loop，實時 dt） */
    G.touchTick = function () {
      const b = G.beh; if (!b) return;
      if (G.mode === 'minigame' || G.mg2Busy) { TS.act = null; b.gest = null; b.faceGest = null; return; }
      rec.tick(sec()); drain(); dumbTick();
      const a = TS.act; let m = null;
      if (a) { m = T.motionAt(a.key, a.t0, sec(), a.x, a.secOv); if (!m) TS.act = null; else { if (a.line && !a.said && sec() - a.t0 >= a.sayAt) { a.said = true; say(a.line, { src: a.dumb ? 'dumb' : 'shake', sec: 3.5 }); }
        if (a.key === 'g_pull') m.drag = (a.x.d || 0) * 120; m.rx = !!(clipOf(a.key) && G.renderer.rxForm && G.renderer.rxForm(G.renderer.fkOf(S()))); } }
      if (S().stage === 'egg') m = null;
      b.gest = m; b.faceGest = m && m.face && !m.rx ? m.face : null;   // 有反應圖：面由 face patch 軌負責（null＝原面）
    };
    G.touchDex = () => T.dumbDex(S());
    G.touchClipOf = clipOf;
    G.touchPlay = (key, x) => (T.MOTIONS && T.MOTIONS[key] ? setAct(key, x) : null);   // 6a：特別開心（第一下撳）等外部模組播動作
    window.__qa = window.__qa || {};
    window.__qa.touch = {
      st: () => ({ act: TS.act ? { key: TS.act.key, dumb: TS.act.dumb || null } : null, grants: TS.grants.slice(), log: TS.log.slice(), mood: T.moodToday(S(), G.now(), store), dumb: Object.assign({}, T.st(S()).dumb), seen: Object.keys(T.st(S()).seen), rolls: TS.rolls, autoDumb: TS.autoDumb, queue: G.nq ? { cur: G.nq.cur ? G.nq.cur.line : null, n: G.nq.size(), log: G.nq.log.slice() } : null, gest: G.beh && G.beh.gest ? { key: G.beh.gest.key, art: G.beh.gest.art, clip: G.beh.gest.clip, rx: G.beh.gest.rx, ms: G.beh.gest.ms, sx: G.beh.gest.sx, sy: G.beh.gest.sy, dx: G.beh.gest.dx, rot: G.beh.gest.rot, fx: G.beh.gest.fx } : null, face: G.beh ? Object.assign({}, G.beh.face) : null }),
      gesture: (k, o) => onGesture(Object.assign({ k }, o || {})),
      shake: (g, t) => G.touchShake(g, t),
      dumb: (k) => dumbGo(k, true),
      roll: () => { TS.lastInput = -1e9; TS.lastRoll = -1e9; const was = TS.autoDumb; TS.autoDumb = true; const r = dumbTick(); TS.autoDumb = was; return r; },
      autoDumb: (on) => { TS.autoDumb = !!on; return TS.autoDumb; },
      idle: (s) => { TS.lastInput = sec() - (s || 0); },
      reset: () => { TS.act = null; },
    };
    return true;
  }
  return { install };
});
