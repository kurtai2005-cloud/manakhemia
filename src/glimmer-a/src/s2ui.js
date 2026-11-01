/* 《微光小圃》 s2ui.js — 第 4 批 4a 瀏覽器膠水：細佬（docs-gdd/series2-4a4b-spec.md v1.1 §4a；遊美 art/series2-4a）。原創代碼。
   攞蛋（團絨首次靜光 → 翌日蝸牛郵差送）→ 蛋 3 晚（團絨瞓 → 攬蛋＋夢泡泡＝當日最多照顧）→ 孵化第一眼（全畫面 2s，撳跳）→ 跟班升級小場面。
   細佬（S1–S6，遊美 5 clip strip）：跟住團絨行／一齊食／一齊瞓、每日喊 2–3 次（拖團絨過去哄 → 哄喊 clip）、S1–S2 撳細佬 → 道具托盤 → 拖畀團絨 → 團絨示範錯 3s（3a 反應 clip 形變＋道具疊層）→ 細佬照抄 2s。
   S3 揭曉系（series2.settle）；親密度（每日上限 10）→ 朋友（雙人彈彈葉：mg2ui opt.duo，唔出碎唔食額）→ 家人（4b 屋仔：只顯示「即將開放」）。
   團絨 §7／路線分／浮動 overlay 全部唔掂；只讀 s.stats／sys12b 計照顧類型（夢用）。Playwright 預設唔自動送蛋／喊（?s2x=1 開）；__qa.s2 直接觸發。?s2=0 全停。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.s2ui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const MX = 14, MY = 12, CX = 97, GY = 292;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function install(G, NS) {
    const SR = NS.series2, D = NS.data, P = D.PARAMS.series2; if (!SR || !P || P.enabled === false) return false;
    const qs = new URLSearchParams(location.search); if (qs.get('s2') === '0') return false;
    const wd = !!(navigator && navigator.webdriver), R = G.renderer, UI = NS.ui, X2 = NS.sys12b, BEH = NS.behavior, RC = NS.reactclip, C = SR.CFG, L_ = SR.LINES_OUT;
    const native = !!(window.Capacitor && (typeof window.Capacitor.isNativePlatform === 'function' ? window.Capacitor.isNativePlatform() : window.Capacitor.isNative));   // 4a.1：APK（Capacitor）一定開自動送蛋／喊
    const on = (k) => qs.get(k) === '1' || qs.get('s2x') === '1' || ((native || !wd) && qs.get(k) !== '0' && qs.get('s2x') !== '0');
    const VERSION = P.version || '4a.1';
    const AUTO = { deliver: on('s2deliver'), cry: on('s2cry') };
    const BASE = P.art.base, S = () => G.state, pnow = () => performance.now();
    const say = (line, o) => (G.say ? G.say(Object.assign({ line, src: 's2', sec: 3.5 }, o || {})) : UI.toast(line, 2600));
    const SND = (k, i) => { const a = NS.audio; if (a && a.Engine) a.Engine.notify(k, i || {}); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const fmt = (t, o) => t.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m));
    const log = []; const note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const st = () => SR.st(S());

    // ── 載圖（遊美 series2：json＋圖逐檔容錯；形態 strip 用到先載）──
    const A = { ready: false, errors: [], img: {}, act: null, faces: null, les: null, ui: null, duo: null, lv: null, ka: null };
    const img = (src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(src)); im.src = src; });
    const jget = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const want = new Set();
    function need(f) { if (!f || A.img[f] || want.has(f)) return A.img[f] || null; want.add(f); img(BASE + f).then(im => { A.img[f] = im; }).catch(() => A.errors.push(f)); return null; }
    const im = (f) => A.img[f] || need(f);
    G.s2Load = Promise.all(['actions/actions.json', 'faces/faces.json', 'lessons/lessons.json', 'ui/ui_series2_4a.json', 'duo/duo.json', 'levelup/levelup.json', 'kid_anchors.json'].map(f => jget(BASE + f)))
      .then(([act, faces, les, ui, duo, lv, ka]) => {
        Object.assign(A, { act, faces, les, ui, duo, lv, ka }); const files = new Set(['egg/egg_48.png', 'egg/egg_crack.png']);
        for (const k of ['S1', 'S2']) for (const c of ['idle', 'walk', 'cry', 'eat', 'sleep']) files.add(act.forms[k][c]);
        for (const k in faces) if (faces[k] && faces[k].png) files.add(faces[k].png);
        for (const k in duo.overlays) if (duo.overlays[k].png) files.add(duo.overlays[k].png);
        for (const k in les.fx2) files.add(les.fx2[k].png); for (const L in les.propsBySeries) files.add(les.propsBySeries[L].png);
        for (const L in ui.dreams) files.add(ui.dreams[L].png);
        return Promise.all([...files].map(f => img(BASE + f).then(i => { A.img[f] = i; }).catch(() => A.errors.push(f))));
      }).then(() => { A.ready = true; return A; }).catch(e => { A.errors.push(String(e && e.message || e)); return null; });
    // 3a 反應圖載完 → 注入示範錯 clip（s2_demo_A–H）＋道具／fx2 圖（rx.fx／rx.img；rx base＝art/reactions/）
    const RXK = (f) => '../series2/' + f;
    Promise.all([G.s2Load, G.rxLoad || Promise.resolve(null)]).then(() => {
      const rx = R.rx; if (!rx || !A.les) return; const L0 = A.les;
      for (const L of SR.LINES) { const d = L0.demo[L]; if (d && !rx.clips['s2_demo_' + L]) rx.clips['s2_demo_' + L] = Object.assign({}, d, { dur: d.durationMs }); }
      const add = (id, o) => { if (rx.fx[id]) return; const f = RXK(o.png); rx.fx[id] = { file: f, frameW: o.frameW, frameH: o.frameH, frames: o.frames || 1, pivot: o.pivot || [0, 0] }; if (A.img[o.png]) rx.img[f] = A.img[o.png]; };
      for (const L in L0.propsBySeries) add(L0.propsBySeries[L].id, L0.propsBySeries[L]); for (const k in L0.fx2) add(k, L0.fx2[k]);
      A.rxOk = true; note('rxInject');
    });
    const fxInfo = (id) => {                      // 細佬 clip／疊層用 fx：series2 道具／fx2／duo 疊層／3a fx
      if (A.les) { for (const L in A.les.propsBySeries) { const p = A.les.propsBySeries[L]; if (p.id === id) return { img: A.img[p.png], w: p.frameW, h: p.frameH, n: p.frames || 1, pv: p.pivot }; } const f2 = A.les.fx2[id]; if (f2) return { img: A.img[f2.png], w: f2.frameW, h: f2.frameH, n: f2.frames || 1, pv: f2.pivot }; }
      const o = A.duo && A.duo.overlays[id]; if (o && o.png) return { img: A.img[o.png], w: o.frameW, h: o.frameH, n: o.frames || 1, pv: o.pivot };
      const rx = R.rx, f = rx && rx.fx && rx.fx[id]; if (f) return { img: rx.img[f.file], w: f.frameW, h: f.frameH, n: f.frames || 1, pv: f.pivot || [0, 0] };
      return null;
    };

    // ── 狀態（顯示用；存檔喺 s.pet2）──
    const K = { x: 34, dir: -1, clip: 'idle', ct: 0, mode: 'follow', lag: 0, cry: null, eatUntil: 0, sleepHeart: -1e9, hearts: [], flip: false, hidden: false };
    const EGG = { x: 30, bob: 0 };
    const SC = { cur: null, q: [] };            // 細佬場面：hatch（全畫面）／level／comfort／lesson
    const sess = { t0: pnow(), nextCry: pnow() + (C.cry.firstDelaySec[0] + Math.random() * (C.cry.firstDelaySec[1] - C.cry.firstDelaySec[0])) * 1000, deliverAt: 0, deliverTry: 0 };
    let lastStage = null;
    const busyOther = () => G.mode === 'minigame' || !!G.mg2Busy || UI.isModalOpen() || document.body.classList.contains('b3b-evo') || document.hidden || !!(G.beh && G.beh.puppet && !MINE.p);
    const MINE = { p: false };
    function puppet(p) { const b = G.beh; if (!b) return; b.puppet = p; MINE.p = true; }
    function release() { const b = G.beh; if (b && MINE.p) { MINE.p = false; if (b.puppet) { b.puppet = null; b.depth = 0; b.faceAct = null; try { if (BEH.force) BEH.force(b, 'stay', G.behCtx || { s: S() }); } catch (e) { } } } }
    const trX = () => (G.beh && S().stage !== 'egg' ? G.beh.x : 0);
    const trHalf = () => { const pr = R.petRect; return clamp(pr && pr.w ? Math.round(pr.w / 2) : 20, 10, 28); };   // 團絨半身闊（隔開細佬）
    const formNow = () => SR.formOf(S(), G.now());
    function strip(fk, clip) { const F = A.act && A.act.forms[fk]; if (!F) return null; const f = F[clip] || F.idle; return im(f); }
    const CLIPMS = () => (A.act ? A.act.clips : {});
    function kidFrame(fk, clip, ct, loop) {
      const cl = CLIPMS()[clip], ims = clip === 'idle' ? (A.act && A.act.idleClip) : null;
      if (clip === 'idle' && ims) { const ms = ims.ms, tot = ms.reduce((a, b) => a + b, 0); let t = ((ct % tot) + tot) % tot, i = 0; while (t >= ms[i]) { t -= ms[i]; i++; } return i; }
      const n = (cl && cl.frames) || 4, fm = (cl && (cl.ms || cl.frameMs)) || 120, f = Math.floor(ct / (Array.isArray(fm) ? fm[0] : fm)); return loop === false ? Math.min(n - 1, f) : f % n;
    }

    // ── 照顧類型（只讀計數差；唔入 sim.noteCare）──
    const CW = { k: null };
    function careSnap() { const s = S(), x = X2 && X2.st ? X2.st(s) : null, ts = G.touchSt; return { feed: s.stats.feeds | 0, play: s.stats.plays | 0, rinse: s.stats.rinses | 0, poop: s.stats.poopsCleared | 0, mg: s.stats.mgPlays | 0,
      walk: x ? x.walk.total | 0 : 0, lull: x ? x.stats.lull | 0 : 0, sleep: s.sleeping ? 1 : 0, touch: ts && ts.log.length ? ts.log[ts.log.length - 1].t : 0, touchKey: ts && ts.log.length ? ts.log[ts.log.length - 1].key : '' }; }
    function careTick() {
      const c = careSnap(), p = CW.k; CW.k = c; if (!p) return; const now = G.now();
      for (const k of ['feed', 'play', 'rinse', 'poop', 'mg', 'walk', 'lull']) for (let i = 0; i < Math.min(5, c[k] - p[k]); i++) { const L = SR.careNote(S(), k, now); if (L) note('care', { k, L }); }
      if (c.sleep && !p.sleep) SR.careNote(S(), 'sleep', now);
      if (c.touch && c.touch !== p.touch) SR.careNote(S(), /pet|rub|nuzzle|hold|pull|purr/.test(c.touchKey) ? 'hold' : 'pat', now);
    }
    if (X2 && X2.water) { const w0 = X2.water; X2.water = function (s) { const r = w0.apply(this, arguments); if (r && r.ok) try { SR.careNote(s, 'water', G.now()); } catch (e) { } return r; }; }

    // ── 攞蛋 ──
    function deliverEgg(how) { const r = SR.deliver(S(), G.now()); if (!r.ok) return r; EGG.x = 30; note('deliver', { how }); UI.toast(L_.deliverToast, 3200); UIS('toast', {}); SND('reward'); if (G.save) G.save(); return r; }
    G.s2Arrived = function (who) { if (who !== 'snail_postman' || !SR.canDeliver(S(), G.now())) return false; setTimeout(() => { say(L_.deliver, { sec: 4.5, urgent: true }); deliverEgg('snail'); }, 600); return true; };
    function deliverTick() {
      const s = S(), now = G.now(); if (s.stage === 'elder') SR.noteElder(s, now);
      if (!SR.canDeliver(s, now) || !AUTO.deliver || busyOther() || SC.cur || s.sleeping) return;
      if (pnow() - sess.t0 < C.deliverDelaySec * 1000 || pnow() < sess.deliverAt) return;
      sess.deliverAt = pnow() + 60000; sess.deliverTry++;
      const r = G.b3bSpawn ? G.b3bSpawn('snail_postman', { force: true, side: 'right' }) : null;
      if (!r || !r.ok) { say(L_.deliver, { sec: 4.5 }); deliverEgg('fallback'); }   // 3b 停咗／訪客出唔到 → 直接收到
    }

    // ── 孵夢 ──
    const DR = { show: null, t0: -1e9 };
    function dreamTick() {
      const s = S(), o = st(), now = G.now(); if (o.phase !== 'egg') return;
      for (const d of SR.dreamDue(s, now, !!s.sleeping)) { const r = SR.dream(s, d.day, now, d.live); if (r) { note('dream', { day: r.day, line: r.line, live: d.live }); if (d.live) { DR.t0 = pnow(); } if (G.save) G.save(); } }
      if (SR.hatchReady(s, now) && !SC.cur && !busyOther() && !s.sleeping) hatchStart();
    }
    function dreamLine() {                       // 而家個夢泡泡（瞓緊＋夜晚）：今晚記咗嗰個；未記 → 今晚照顧最多
      const s = S(), o = st(), now = G.now(), h = SR.hourOf(now); if (o.phase !== 'egg' || !s.sleeping || !(h >= C.dreamFrom || h < C.dreamCatchup)) return null;
      const n = SR.nightOf(now), d = o.dreams.find(x => x.day === n); return d ? d.line : SR.topCare(s, n);
    }

    // ── 孵化第一眼（全畫面 2s；撳 → 跳去最後一格）──
    function hatchStart() { SC.cur = { kind: 'hatch', t: 0, skip: false, end: 0 }; catcher(true); document.body.classList.add('s2-scene'); tray(false); SND('hatch'); note('hatchScene'); }
    function hatchEnd() {
      const c = SC.cur; SC.cur = null; catcher(false); document.body.classList.remove('s2-scene'); const s = S(), now = G.now(); SR.hatch(s, now);
      K.x = clamp(trX() + 26, -70, 70); K.mode = 'follow'; K.clip = 'idle'; say(L_.hatch, { sec: 3.5 }); note('hatched', { skip: c && c.skip }); if (G.save) G.save();
    }
    let catchEl = null;
    function catcher(show) {
      if (!catchEl) { catchEl = document.createElement('div'); catchEl.id = 's2Catch'; catchEl.dataset.testid = 's2-catch'; catchEl.style.cssText = 'position:fixed;inset:0;z-index:40;display:none;background:transparent';
        catchEl.addEventListener('pointerdown', (e) => { e.preventDefault(); sceneTap(); }); document.body.appendChild(catchEl); }
      catchEl.style.display = show ? 'block' : 'none';
    }
    function sceneTap() { const c = SC.cur; if (!c || c.kind !== 'hatch') return; if (c.t < 2000) { c.t = 2000; c.skip = true; note('hatchSkip'); } else c.end = 1e9; }
    function atlasSrc(fk, clip, ct, loop) {     // 團絨（evo 形態）atlas 幀；冇呢個 clip → 後備
      const F = D.FORMS[fk], A0 = F && R.atlas && R.atlas[F.atlas]; if (!A0) return null; const an = A0.json.animations;
      const fb = { emo_surprised: ['emo_surprised', 'idle'], smug_pose: ['smug_pose', 'emo_happy', 'idle'], cheer_jump: ['cheer_jump', 'emo_happy', 'idle'], nuzzle_purr: ['nuzzle_purr', 'nuzzle', 'emo_cuddly', 'idle'], nuzzle: ['nuzzle', 'emo_cuddly', 'idle'], sleep_loop: ['sleep_loop', 'idle'] }[clip] || [clip, 'idle'];
      const k = fb.find(n => an[n]); if (!k) return null; const a = an[k], n = (a.frames || []).length || 1, f = Math.floor(ct / 1000 * (a.fps || 8)), i = (loop === false || a.loop === false) ? Math.min(n - 1, f) : f % n;
      return { src: R.atlasSrc(F.atlas, k, i), clip: k, frame: i };
    }
    function blit(ctx, image, sx, sy, sw, sh, x, y, px, py, sc, flip) { if (!image) return; ctx.save(); ctx.translate(x, y); ctx.scale((flip ? -1 : 1) * (sc || 1), sc || 1); ctx.drawImage(image, sx, sy, sw, sh, -px, -py, sw, sh); ctx.restore(); }
    R.s2Overlay = function (ctx, k) {
      const c = SC.cur; if (!c || c.kind !== 'hatch') return; const F = SR.hatchFrame(c.t), W = 195, H = 422, AX = 97, AY = 292;
      ctx.save(); ctx.setTransform(k, 0, 0, k, 0, 0); ctx.imageSmoothingEnabled = false;
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3C3460'); g.addColorStop(1, '#78689C'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      if (F.rays) { const r = fxInfo('ov_rays'); if (r && r.img) { ctx.globalAlpha = F.rays.a; blit(ctx, r.img, F.rays.f * r.w, 0, r.w, r.h, AX, AY - 30, r.pv[0], r.pv[1], 2); ctx.globalAlpha = 1; } }
      if (F.egg) { const e = A.img['egg/egg_crack.png']; blit(ctx, e, F.egg.crack * 48, 0, 48, 48, AX + F.egg.dx, AY, 24, 45, 2); }
      if (F.kid) { const s1 = strip('S1', 'idle'); const fr = F.kid.blink ? 3 : kidFrame('S1', 'idle', c.t - 800); blit(ctx, s1, fr * 48, 0, 48, 48, AX, AY, 24, 45, 2); }
      for (const b of F.shell) { const r = fxInfo('ov_shell_bits'); if (r && r.img) { ctx.globalAlpha = clamp(b.a, 0, 1); blit(ctx, r.img, b.f * r.w, 0, r.w, r.h, AX + b.x, AY - 40 + b.y, r.pv[0], r.pv[1], 2); ctx.globalAlpha = 1; } }
      if (F.tr) { const fk = R.fkOf(S()), a = atlasSrc(fk, F.tr.clip, F.tr.ct, false); if (a && a.src) { const s0 = a.src; blit(ctx, s0.img, s0.sx, s0.sy, s0.sw, s0.sh, F.tr.x, AY, s0.px, s0.py, 2); } }
      if (F.heart) { const h = fxInfo('fx_heart'); if (h && h.img) blit(ctx, h.img, F.heart.f * h.w, 0, h.w, h.h, 67, 202 + F.heart.dy, h.pv[0], h.pv[1], 2); }
      if (F.flash > 0) { ctx.fillStyle = 'rgba(255,255,255,' + clamp(F.flash, 0, 1).toFixed(3) + ')'; ctx.fillRect(0, 0, W, H); }
      if (c.t < 2000 && c.t > 300) { ctx.globalAlpha = 0.5 + 0.3 * Math.sin(c.t / 200); ctx.fillStyle = '#fff6dc'; ctx.font = '7px sans-serif'; ctx.textAlign = 'center'; ctx.fillText('撳一下跳過', W / 2, H - 30); ctx.globalAlpha = 1; }
      c.last = { t: Math.round(c.t), egg: !!F.egg, kid: !!F.kid, tr: !!F.tr, rays: !!F.rays, heart: !!F.heart, shell: F.shell.length };
      ctx.restore();
    };

    // ── 場面（in-world）：升級小場面／哄喊／一齊食（雙人 clip 時間軸；團絨 puppet＋細佬 strip＋疊層）──
    const fcount = (id) => { const f = fxInfo(id); return f ? f.n : 1; };
    function sceneOrigin(trDx, kidDx) { const bx = trX(), o = bx - trDx; const lo = -70 - Math.min(trDx, kidDx), hi = 70 - Math.max(trDx, kidDx); return clamp(o, lo, hi); }
    function playClip(kind, clip, o) {
      if (!clip) return false; const ac = clip.actors || {}, trd = ac.tr ? ac.tr.dx || 0 : 0, kd = ac.kid ? ac.kid.dx || 0 : 0;
      SC.cur = Object.assign({ kind, clip, t: 0, ox: sceneOrigin(trd, kd), cues: {} }, o || {}); tray(false); note('scene', { kind }); return true;
    }
    function sceneTick(dt) {
      const c = SC.cur; if (!c) return; c.t += dt * 1000;
      if (c.kind === 'hatch') { if (c.t >= 2000) { c.end += dt * 1000; if (c.end >= (c.skip ? 900 : 700)) hatchEnd(); } return; }
      if (c.kind === 'lesson') return lessonTick(c, dt);
      const F = SR.sceneAt(c.clip, c.t, fcount), b = G.beh; c.F = F;
      const tr = F.actors.tr; if (tr && b && !c.noTr) { const fk = R.fkOf(S()), a = atlasSrc(fk, tr.clip, tr.ct, tr.loop); puppet({ x: c.ox + tr.x, dir: c.trDir || 1, clip: a ? a.clip : 'idle', frame: a ? a.frame : 0, depth: 0 }); }
      const kd = F.actors.kid; if (kd) { K.x = c.ox + kd.x; K.clip = kd.clip; K.ct = kd.ct; K.flip = kd.flip; K.dir = kd.flip ? -1 : 1; }
      if (c.kind === 'level' && c.t >= 300 && !c.cues.snd) { c.cues.snd = 1; SND('reward'); UIS('badge', {}); }
      if (F.done || c.t >= F.dur) sceneEnd();
    }
    function sceneEnd() {
      const c = SC.cur; if (!c) return; SC.cur = null; if (!c.noTr) release(); K.mode = 'follow'; K.flip = false; note('sceneEnd', { kind: c.kind });
      if (c.after) try { c.after(); } catch (e) { }
    }
    function levelTick() {
      const o = st(); if (o.phase !== 'kid' || SC.cur || !o.relQ.length || busyOther() || S().sleeping || !A.ready) return;
      const rel = o.relQ.shift(), clip = A.lv.scenes['lv_' + rel]; if (G.save) G.save();
      playClip('level', clip, { rel, after: () => { say(rel === 'friend' ? L_.lvFriend : rel === 'family' ? L_.lvFamily : L_.lvFollow, { sec: 4 }); UI.toast((rel === 'friend' ? '朋友' : rel === 'family' ? '家人' : '跟班') + '！' + (rel === 'family' ? '屋仔即將開放（4b）' : ''), 2600); } });
    }

    // ── 喊／哄喊（拖團絨過去）──
    function cryTick(dt) {
      const s = S(), o = st(), now = G.now(); if (o.phase !== 'kid') return;
      if (K.cry) { K.cry.t += dt * 1000; if (K.cry.t >= C.cry.timeoutSec * 1000 || s.sleeping) { K.cry = null; SR.cryTimeout(s); K.mode = 'follow'; say(L_.cryStop, { sec: 2.5 }); note('cryTimeout'); } return; }
      if (!AUTO.cry || SC.cur || busyOther() || pnow() < sess.nextCry || !SR.cryWanted(s, now)) return;
      cryStart();
    }
    function cryStart() { const s = S(); SR.cryStart(s, G.now()); K.cry = { t: 0 }; K.mode = 'cry'; K.ct = 0; sess.nextCry = pnow() + (C.cry.gapSec[0] + Math.random() * (C.cry.gapSec[1] - C.cry.gapSec[0])) * 1000; say(L_.cry, { sec: 4 }); SND('cue', { name: 'pet_uncomfortable' }); note('cry'); if (G.save) G.save(); return true; }
    const DRAG = { on: false, id: null, x: 0, ct: 0 };
    function dragStart(a, e) {
      DRAG.on = true; DRAG.id = e && e.pointerId; DRAG.ct = 0; DRAG.x = a.x - CX; puppet({ x: trX(), dir: K.x >= trX() ? 1 : -1, clip: 'picked_up', frame: 0, depth: -4 }); note('dragStart');
      const mv = (ev) => { if (!DRAG.on) return; const p = R.screenToArt(ev.clientX, ev.clientY); DRAG.x = clamp(p.x - CX, -70, 70); };
      const up = (ev) => { window.removeEventListener('pointermove', mv, true); window.removeEventListener('pointerup', up, true); window.removeEventListener('pointercancel', up, true); dragEnd(ev && ev.type === 'pointercancel'); };
      window.addEventListener('pointermove', mv, true); window.addEventListener('pointerup', up, true); window.addEventListener('pointercancel', up, true);
    }
    function dragTick(dt) { if (!DRAG.on) return; DRAG.ct += dt * 1000; const b = G.beh, px = b && b.puppet ? b.puppet.x : trX(), nx = px + clamp(DRAG.x - px, -90 * dt, 90 * dt); puppet({ x: nx, dir: DRAG.x >= px ? 1 : -1, clip: Math.abs(DRAG.x - px) > 1 ? 'walk' : 'idle', frame: Math.floor(DRAG.ct / 100) % 6, depth: 0 }); }
    function dragEnd(cancel) {
      if (!DRAG.on) return; DRAG.on = false; const b = G.beh, px = b && b.puppet ? b.puppet.x : trX();
      if (!cancel && K.cry && Math.abs(px - K.x) <= 26) return comfortStart(px);
      release(); if (K.cry) say('再拖近啲細佬（放喺佢隔籬）', { sec: 2.5 }); note('dragEnd', { near: Math.abs(px - K.x) | 0 });
    }
    function comfortStart(px) {
      const s = S(); K.cry = null; const clip = A.duo && A.duo.clips.comfort_cry; const dir = K.x >= px ? 1 : -1;
      if (dir < 0) { const c2 = mirrorClip(clip); playClip('comfort', c2, { ox: K.x + 14, trDir: -1 }); } else playClip('comfort', clip, { ox: K.x - 14, trDir: 1 });
      SC.cur.after = () => { const r = SR.comfort(s, G.now()); say(r.n ? L_.comfort : L_.capFull, { sec: 3 }); heart(); note('comfort', { n: r.n }); if (G.save) G.save(); };
      SND('cue', { name: 'pet_nuzzle_purr_a' });
    }
    function mirrorClip(c) { const o = JSON.parse(JSON.stringify(c)); for (const k in o.actors) { const a = o.actors[k]; a.dx = -(a.dx || 0); for (const t of a.track || []) if (t.x != null) t.x = -t.x; a.flip = a.flip ? 0 : 1; } for (const v of o.overlays || []) v.x = -(v.x || 0); return o; }
    function heart() { K.hearts.push({ t: 0 }); }

    // ── 一齊食（ui sysFed 之後）＋一齊瞓 ──
    { const f0 = G.sysFed; G.sysFed = function () { const r = f0 ? f0.apply(this, arguments) : undefined; try { eatTogether(); } catch (e) { } return r; }; }
    function eatTogether() {
      const o = st(); if (o.phase !== 'kid' || K.cry || (SC.cur && SC.cur.kind !== 'eat')) return false; const r = SR.eatTogether(S(), G.now());
      K.eatUntil = pnow() + 1500; K.ct = 0; K.mode = 'eat'; K.x = clamp(trX() + (K.x >= trX() ? 1 : -1) * (trHalf() + 14), -70, 70); K.dir = K.x >= trX() ? -1 : 1;
      if (r && r.n) { heart(); setTimeout(() => say(L_.eat, { sec: 2.2 }), 900); } note('eat', { n: r ? r.n : 0 }); if (G.save) G.save(); return true;
    }
    function sleepTick() {
      const s = S(), o = st(); if (o.phase !== 'kid' || !s.sleeping) return; const r = SR.sleepTogether(s, G.now());
      if (r) { K.sleepHeart = pnow(); if (r.n) say(L_.sleep, { sec: 2.5 }); note('sleepTogether', { n: r.n }); if (G.save) G.save(); }
    }

    // ── 細佬行為（跟住團絨）──
    function kidTick(dt) {
      const s = S(), o = st(), ms = dt * 1000, now = G.now(); K.ct += ms; K.hearts = K.hearts.filter(h => (h.t += ms) < 900);
      if (o.phase === 'egg') { const tx = s.sleeping ? clamp(trX() + 18, -70, 70) : 30; EGG.x += clamp(tx - EGG.x, -20 * dt, 20 * dt); return; }
      if (o.phase !== 'kid' || (SC.cur && SC.cur.kind !== 'eat')) return;
      const sk = SR.stageOf(s, now); if (sk !== lastStage) { if (lastStage && sk !== lastStage) { note('stage', { sk }); if (o.stageSeen !== sk) { o.stageSeen = sk; if (SR.stageIdx(sk) >= 3 && !o.line) { const r = SR.settle(s, now); say(fmt(L_.reveal, { zh: SR.LINE_ZH[o.line] }), { sec: 4 }); note('reveal', { line: o.line, how: r && r.how }); } SR.checkLevel(s, now); if (G.save) G.save(); } } lastStage = sk; }
      if (SR.stageIdx(sk) >= 3 && !o.line) { SR.settle(s, now); if (G.save) G.save(); }
      const bx = trX(), fr = o.rel === 'friend' || o.rel === 'family', walkSp = fr ? 26 : 22;
      const go = (tx, sp) => { const d = tx - K.x; if (Math.abs(d) <= 1.5) return true; K.x += clamp(d, -sp * dt, sp * dt); K.dir = d > 0 ? 1 : -1; return false; };
      if (K.cry) { K.clip = 'cry'; return; }
      if (K.mode === 'eat' && pnow() < K.eatUntil) { K.clip = 'eat'; return; }
      if (s.sleeping) { const tx = clamp(bx + trHalf() + 4, -70, 70); if (go(tx, walkSp)) { K.clip = 'sleep'; K.dir = -1; } else K.clip = 'walk'; K.mode = 'sleep'; return; }
      K.mode = 'follow'; const bd = G.beh ? G.beh.dir || 1 : 1, gap = trHalf() + (fr ? 12 : 20), tx = clamp(bx - bd * gap, -70, 70);
      if (Math.abs(tx - K.x) > (fr ? 3 : 6)) { K.lag += ms; if (K.lag >= 300) { go(tx, walkSp); K.clip = 'walk'; } else K.clip = 'idle'; } else { K.lag = 0; K.clip = 'idle'; K.dir = bx >= K.x ? 1 : -1; }
    }

    // ── 教錯課（撳細佬 → 道具托盤 → 拖畀團絨 → 示範 3s → 照抄 2s）──
    let trayEl = null, trayOn = false;
    function tray(show) {
      if (!trayEl) {
        trayEl = document.createElement('div'); trayEl.id = 's2Tray'; trayEl.dataset.testid = 's2-tray';
        trayEl.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:calc(178px + env(safe-area-inset-bottom,0px));display:none;gap:3px;z-index:6;max-width:96%;overflow-x:auto;padding:4px 6px;border-radius:10px;background:rgba(30,22,48,.78);color:#fff;font-size:10px;align-items:center';
        (document.getElementById('ui') || document.body).appendChild(trayEl);
      }
      const want = !!show && !SC.cur && !UI.isModalOpen(); if (want !== trayOn) { trayOn = want; trayEl.style.display = want ? 'flex' : 'none'; if (want) fillTray(); }
    }
    function fillTray() {
      const left = SR.canLesson(S(), G.now()).left || 0; trayEl.innerHTML = '<span style="opacity:.85;white-space:nowrap" data-testid="s2-tray-left" data-left="' + left + '">拖畀團絨（今日剩 ' + left + ' 堂）</span>';
      for (const L of SR.LINES) { const u = A.ui && A.ui.props[L]; const ch = document.createElement('div'); ch.className = 's2-chip'; ch.dataset.testid = 's2-prop-' + L; ch.title = SR.PROP_ZH[L];
        ch.style.cssText = 'width:30px;height:30px;flex:0 0 auto;border-radius:8px;background:#f3e1b8;cursor:grab;user-select:none;touch-action:none;display:flex;align-items:center;justify-content:center';
        ch.innerHTML = u ? '<img src="' + BASE + u.png + '" width="28" height="28" draggable="false" style="image-rendering:pixelated;pointer-events:none">' : SR.PROP_ZH[L];
        ch.addEventListener('pointerdown', (e) => propDrag(e, L, ch)); trayEl.appendChild(ch); }
      const x = document.createElement('div'); x.dataset.testid = 's2-tray-close'; x.textContent = '✕'; x.style.cssText = 'padding:4px 6px;cursor:pointer'; x.addEventListener('click', () => { tray(false); UIS('cancel'); }); trayEl.appendChild(x);
    }
    let pd = null;
    function propDrag(e, L, ch) {
      e.preventDefault(); e.stopPropagation(); const g = ch.cloneNode(true); g.dataset.testid = 's2-drag-ghost';
      g.style.cssText += ';position:fixed;pointer-events:none;z-index:99;opacity:.92;left:' + (e.clientX - 15) + 'px;top:' + (e.clientY - 15) + 'px'; document.body.appendChild(g); UIS('press');
      pd = { L, g }; try { ch.setPointerCapture(e.pointerId); } catch (er) { }
      const mv = (ev) => { if (!pd) return; pd.g.style.left = (ev.clientX - 15) + 'px'; pd.g.style.top = (ev.clientY - 15) + 'px'; };
      const up = (ev) => { ch.removeEventListener('pointermove', mv); ch.removeEventListener('pointerup', up); ch.removeEventListener('pointercancel', up); const d = pd; pd = null; if (!d) return; d.g.remove();
        if (ev.type === 'pointercancel') return; const a = R.screenToArt(ev.clientX, ev.clientY); if (inBox(a, UI.petHitBox())) lessonStart(d.L); else { note('propMiss', { x: Math.round(a.x), y: Math.round(a.y) }); UIS('cancel'); } };
      ch.addEventListener('pointermove', mv); ch.addEventListener('pointerup', up); ch.addEventListener('pointercancel', up);
    }
    const inBox = (a, b) => b && a.x >= b.x && a.x <= b.x + b.w && a.y >= b.y && a.y <= b.y + b.h;
    function lessonStart(L) {
      const s = S(), now = G.now(), c = SR.canLesson(s, now); if (!c.ok) { say(c.reason === 'today' ? L_.lessonFull : c.reason === 'max' ? L_.lessonDone6 : L_.lessonNot, { sec: 2.5 }); UIS('disabled'); return { ok: false, reason: c.reason }; }
      if (SC.cur || busyOther()) return { ok: false, reason: 'busy' };
      const r = SR.lesson(s, L, now); if (!r.ok) return r; tray(false);
      const bx = trX(), side = K.x >= bx ? 1 : -1; SC.cur = { kind: 'lesson', L, t: 0, bx, side, kx: clamp(bx + side * (trHalf() + 16), -70, 70), r, rxOk: !!(R.rxForm && R.rxForm(R.fkOf(s)) && R.rx.clips['s2_demo_' + L]) };
      SND('cue', { name: 'pet_curious' }); UIS('stamp'); note('lesson', { L, rx: SC.cur.rxOk }); if (G.save) G.save(); return { ok: true, n: r.n };
    }
    function lessonTick(c, dt) {
      const b = G.beh, demo = c.t < 3000; K.x += clamp(c.kx - K.x, -40 * dt, 40 * dt); K.dir = -c.side; K.clip = 'idle';
      if (b) { puppet({ x: c.bx, dir: c.side, clip: 'idle', frame: 0, depth: 0 }); if (demo && c.rxOk) b.gest = { key: 's2_demo', clip: 's2_demo_' + c.L, ms: c.t, sx: 1, sy: 1, dx: 0, dy: 0, rot: 0, rx: true }; else b.gest = null; }
      if (c.t >= 3000 && !c.cueCopy) { c.cueCopy = 1; SND('cue', { name: 'pet_turn_huh_a' }); }
      if (c.t >= 5000) { SC.cur = null; release(); if (b) b.gest = null; K.mode = 'follow'; heart(); say(fmt(L_.lessonDone, { prop: SR.PROP_ZH[c.L] }) + '（' + SR.WRONG[c.L] + '）', { sec: 3.5 }); note('lessonEnd', { L: c.L }); }
    }

    // ── 細佬卡（撳細佬；S1–S2 有堂 → 直接開托盤）──
    function kidTap() {
      const s = S(), o = st(), now = G.now();
      if (o.phase === 'egg') { say('細佬蛋暖暖…（孵夢 ' + o.dreams.length + '／' + C.eggNights + ' 晚）', { sec: 2.5 }); UIS('tap'); note('eggTap'); return true; }
      if (K.cry) { say(L_.cry, { sec: 2.5 }); return true; }
      const cl = SR.canLesson(s, now); if (cl.ok) { tray(!trayOn); UIS('tap'); if (trayOn) say('揀一樣道具，拖畀團絨示範（佢會教錯）', { sec: 3 }); note('kidTap', { tray: trayOn }); return true; }
      card(); return true;
    }
    function card() {
      const s = S(), o = st(), now = G.now(), sk = SR.stageOf(s, now), d = SR.today(s, now), node = document.createElement('div'); node.dataset.testid = 's2-card';
      const fk = formNow(), F = A.act && A.act.forms[fk];
      node.innerHTML = '<div style="display:flex;gap:10px;align-items:center">' + (F ? '<div style="width:56px;height:56px;border-radius:8px;background:rgba(255,255,255,.15);overflow:hidden;flex:0 0 auto"><div style="width:48px;height:48px;margin:4px;background:url(' + BASE + F.idle + ') 0 0/192px 48px;image-rendering:pixelated;transform:scale(1.0)"></div></div>' : '') +
        '<div style="font-size:12px;line-height:1.6"><b>細佬</b>　' + SR.STAGE_ZH[sk] + (o.line ? '・' + SR.LINE_ZH[o.line] + '系' : '') + '<div data-testid="s2-intim" data-v="' + o.intim + '" data-today="' + d.n + '">親密 ' + o.intim + '（今日 ' + d.n + '／' + C.intimacyCap + '）</div>' +
        '<div data-testid="s2-rel" data-rel="' + o.rel + '">關係：' + SR.REL_ZH[o.rel] + (o.rel === 'follow' ? '（' + C.friendAt + ' 做朋友）' : o.rel === 'friend' ? '（' + C.familyAt + '＋成年做家人）' : '') + '</div></div></div>';
      const bt = [];
      const du = SR.canDuo(s, now); if (du.ok) bt.push({ text: '雙人彈彈葉（' + du.left + '）', primary: true, onClick: () => { duoStart(); } });
      if (o.rel === 'family') { const h = document.createElement('div'); h.dataset.testid = 's2-house'; h.style.cssText = 'margin-top:8px;font-size:11px;opacity:.85'; h.textContent = '🔒 屋仔：即將開放（4b）'; node.appendChild(h); }
      bt.push({ text: '好', primary: !bt.length });
      UI.modal({ title: '細佬', kind: 's2Card', node, buttons: bt }); UIS('popupOpen'); note('card');
    }

    // ── 雙人彈彈葉（mg2ui opt.duo：唔出碎、唔食額、唔加火苗）──
    function duoStart() { const c = SR.canDuo(S(), G.now()); if (!c.ok) { say(L_.duoFull, { sec: 2.5 }); return false; } if (!G.mg2) return false; const ok = G.mg2.start('bounce', 0, null, { duo: true }); note('duoStart', { ok }); return ok; }
    G.s2DuoDone = function (score) { const r = SR.duoDone(S(), G.now(), score); note('duoDone', { n: r.n, ok: r.ok }); if (r.ok && r.n) setTimeout(() => say(fmt(L_.duoDone, { n: r.n }), { sec: 3 }), 400); if (G.save) G.save(); return r; };
    G.s2DrawKid = function (ctx, x, y, cheer, T) {   // 彈彈葉畫面（mg2 canvas 邏輯座標）：細佬喺葉旁邊打氣
      const fk = formNow(); if (!fk || fk === 'egg') return; const sp = strip(fk, cheer ? 'eat' : 'idle'); if (!sp) return; const f = kidFrame(fk, cheer ? 'eat' : 'idle', T * 1000);
      const hop = cheer ? -Math.abs(Math.sin(T * 9)) * 4 : 0; ctx.save(); ctx.imageSmoothingEnabled = false; ctx.translate(x, y + hop); ctx.scale(-1, 1); ctx.drawImage(sp, f * 48, 0, 48, 48, -24, -45, 48, 48); ctx.restore();
    };

    // ── 撳（ui.js pointerdown；b3bTap 之後）──
    function kidRect() { const o = st(), pv = R.par ? R.par.x * -1.5 : 0; if (o.phase === 'egg') return { x: CX + EGG.x - 12 + pv, y: GY - 30, w: 24, h: 32 };
      const ka = A.ka && A.ka.forms[formNow()], bx = ka ? ka.box : [12, 18, 36, 46]; return { x: CX + K.x + (bx[0] - 24) - 4 + pv, y: GY + (bx[1] - 45) - 4, w: bx[2] - bx[0] + 8, h: bx[3] - bx[1] + 8 }; }
    G.s2Tap = function (a, e) {
      if (SC.cur && SC.cur.kind === 'hatch') { sceneTap(); return true; }
      const o = st(); if (o.phase !== 'egg' && o.phase !== 'kid') return false;
      if (SC.cur) return SC.cur.kind === 'lesson' || SC.cur.kind === 'comfort';
      if (K.cry && !S().sleeping && inBox(a, UI.petHitBox())) { dragStart(a, e); return true; }
      if (!K.hidden && inBox(a, kidRect())) return kidTap();
      return false;
    };

    // ── 畫（drawL2；art 座標 → ox／oy 加邊距）──
    const ox = (px) => px + MX, oy = (py) => py + MY, RST = { kid: 0, egg: 0, dream: 0, fx: 0, copy: 0, prop: 0 };
    const off = { c: null };
    function kidBase(fk, faceName) {               // idle 幀 0＋face patch（faces.json）→ 48×48 canvas
      const id = A.img[A.act.forms[fk].idle]; if (!id) return null; const F = A.faces[fk], fi = F && faceName ? F.order.indexOf(faceName) : -1, fp = F && A.img[F.png];
      if (!off.c) { off.c = document.createElement('canvas'); off.c.width = 48; off.c.height = 48; } const g = off.c.getContext('2d'); g.clearRect(0, 0, 48, 48); g.imageSmoothingEnabled = false;
      g.drawImage(id, 0, 0, 48, 48, 0, 0, 48, 48); if (fi >= 0 && fp) g.drawImage(fp, fi * 48, 0, 48, 48, 0, 0, 48, 48); return off.c;
    }
    function drawCopy(x, c, base) {             // 細佬照抄：reactclip evalClip（copy clip）→ body xform＋face＋fx（錨點 kid_anchors）
      const fk = formNow(), cl = A.les.copy[c.L]; if (!cl || !A.act.forms[fk]) return false; const clip = c.copyClip || (c.copyClip = Object.assign({}, cl, { dur: cl.durationMs }));
      const ev = RC.evalClip(clip, c.t - 3000, { frameInfo: (id) => { const f = fxInfo(id); return f ? { frames: f.n } : null; } }), xf = RC.xform(ev.body), mir = K.dir < 0 ? -1 : 1;
      const an = (A.ka.forms[fk] || A.ka.forms.S2), pv = an.pivot, px = CX + K.x, py = base;
      const fxd = (z) => { for (const f of ev.fx) { if ((f.z || 'front') !== z) continue; const I = fxInfo(f.id); if (!I || !I.img) continue; const L = an[f.anchor] || pv, l = [L[0] - pv[0], L[1] - pv[1]], m = f.follow ? xf.map(l) : l;
        const sx = ox(px + mir * (m[0] + f.dx)), sy = oy(py + m[1] + f.dy), fr = clamp(f.frame | 0, 0, I.n - 1); x.save(); x.translate(Math.round(sx), Math.round(sy)); if (mir < 0) x.scale(-1, 1); x.drawImage(I.img, fr * I.w, 0, I.w, I.h, -I.pv[0], -I.pv[1], I.w, I.h); x.restore(); RST.fx++; } };
      fxd('back'); const bc = kidBase(fk, ev.face); if (!bc) return false;
      x.save(); x.imageSmoothingEnabled = false; x.translate(ox(px) + xf.tx * mir, oy(py) + xf.ty); x.scale(mir * xf.sx, xf.sy); x.rotate(xf.rad); x.drawImage(bc, -pv[0], -pv[1]); x.restore(); fxd('front'); RST.copy++; c.copyEv = { t: Math.round(ev.t), face: ev.face, fx: ev.fx.map(f => f.id) }; return true;
    }
    function drawKid(x, base) {
      const fk = formNow(); if (!fk || fk === 'egg' || !A.act) return; const c = SC.cur;
      x.fillStyle = 'rgba(10,20,20,0.3)'; for (let dy = -2; dy <= 2; dy++) { const w = Math.round(9 * Math.sqrt(1 - dy * dy / 9)); x.fillRect(ox(Math.round(CX + K.x) - w), oy(base - 1 + dy), w * 2, 1); }
      if (c && c.kind === 'lesson' && c.t >= 3000 && drawCopy(x, c, base)) return;
      const sp = strip(fk, K.clip); if (!sp) return; const loop = !(c && c.F && c.F.actors.kid && c.F.actors.kid.loop === false), f = kidFrame(fk, K.clip, K.ct, loop);
      const mir = K.dir < 0; x.save(); x.imageSmoothingEnabled = false; const X0 = ox(Math.round(CX + K.x)), Y0 = oy(base); if (mir) { x.translate(X0 + 1, Y0); x.scale(-1, 1); } else x.translate(X0, Y0);
      x.drawImage(sp, f * 48, 0, 48, 48, -24, -45, 48, 48); x.restore(); RST.kid++;
      if (K.clip === 'sleep') { const z = fxInfo('fx_zzz'); if (z && z.img) { const fr = Math.floor(pnow() / 300) % z.n, ka = A.ka.forms[fk] || A.ka.forms.S2; x.drawImage(z.img, fr * z.w, 0, z.w, z.h, ox(Math.round(CX + K.x + (ka.headTop[0] - 24) + 6) - z.pv[0]), oy(base + ka.headTop[1] - 45 - 1) - z.pv[1], z.w, z.h); } }
    }
    function drawEgg(x, base) {
      const e = A.img['egg/egg_48.png']; if (!e) return; const t = pnow() % 2000, bob = t > 1000 && t < 1150 ? -1 : 0, X0 = ox(Math.round(CX + EGG.x)), Y0 = oy(base + bob);
      x.fillStyle = 'rgba(10,20,20,0.3)'; for (let dy = -2; dy <= 2; dy++) { const w = Math.round(8 * Math.sqrt(1 - dy * dy / 9)); x.fillRect(X0 - w, oy(base - 1 + dy), w * 2, 1); }
      x.drawImage(e, 0, 0, 48, 48, X0 - 24, Y0 - 45, 48, 48); RST.egg++;
    }
    function drawDream(x) {
      const L = dreamLine(); if (!L || !A.ui) return; const d = A.img[A.ui.dreams[L].png], pr = R.petRect; if (!d || !pr) return;
      const hx = Math.round(pr.x + pr.w / 2) + 10, hy = Math.round(pr.y) - 8, sz = 44, pop = clamp((pnow() - DR.t0) / 300, 0, 1), s = DR.t0 > pnow() - 300 ? 0.6 + 0.4 * pop : 1, bob = Math.round(Math.sin(pnow() / 700) * 1.5);
      x.save(); x.imageSmoothingEnabled = false; x.drawImage(d, ox(hx), oy(hy - sz * s + bob), Math.round(sz * s), Math.round(sz * s)); x.restore(); RST.dream++; DR.show = L;
    }
    function drawOverlays(x, base) {
      const c = SC.cur; if (!c || !c.F) return;
      for (const v of c.F.overlays) { const I = fxInfo(v.id); if (!I || !I.img) continue; const X0 = ox(Math.round(CX + c.ox + v.x)), Y0 = oy(Math.round(base + v.y)), fr = clamp(v.frame | 0, 0, I.n - 1);
        x.drawImage(I.img, fr * I.w, 0, I.w, I.h, X0 - I.pv[0], Y0 - I.pv[1], I.w, I.h); RST.fx++;
        if (v.id === 'ov_ribbon' && c.rel) { x.save(); x.fillStyle = '#4a2e1a'; x.font = 'bold 6px sans-serif'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(c.rel === 'friend' ? '朋友' : c.rel === 'family' ? '家人' : '跟班', X0, Y0); x.restore(); } }
    }
    function drawHearts(x, base) {
      const h = fxInfo('fx_heart'); if (!h || !h.img) return; const fk = formNow(), ka = A.ka && (A.ka.forms[fk] || A.ka.forms.S2); if (!ka) return;
      for (const q of K.hearts) { const u = q.t / 900, X0 = ox(Math.round(CX + K.x)), Y0 = oy(Math.round(base + ka.headTop[1] - 45 - 4 - u * 14)); x.globalAlpha = u > 0.7 ? 1 - (u - 0.7) / 0.3 : 1; x.drawImage(h.img, (u < 0.25 ? 0 : 1) * h.w, 0, h.w, h.h, X0 - h.pv[0], Y0 - h.pv[1], h.w, h.h); x.globalAlpha = 1; }
    }
    function drawBlanket(x, base) {
      const o = st(); if (!(o.rel === 'friend' || o.rel === 'family') || K.clip !== 'sleep' || !S().sleeping) return; const I = fxInfo('ov_blanket'); if (!I || !I.img) return;
      const mid = (trX() + K.x) / 2; x.drawImage(I.img, 0, 0, I.w, I.h, ox(Math.round(CX + mid)) - I.pv[0], oy(base + 1) - I.pv[1], I.w, I.h); RST.blanket = (RST.blanket || 0) + 1;
    }
    function drawPropFallback(x) {               // 團絨冇 3a 反應錨點（舊形態）→ 道具喺頭頂搖
      const c = SC.cur; if (!c || c.kind !== 'lesson' || c.rxOk || c.t >= 3000) return; const p = A.les.propsBySeries[c.L], I = p && A.img[p.png], pr = R.petRect; if (!I || !pr) return;
      const w = Math.sin(c.t / 120) * 2; x.drawImage(I, 0, 0, p.frameW, p.frameH, ox(Math.round(pr.x + pr.w / 2 + w)) - p.pivot[0], oy(Math.round(pr.y) - 2) - p.pivot[1], p.frameW, p.frameH); RST.prop++;
    }
    R.s2Layer = function (x, z, cc, base) {
      if (!A.ready || (SC.cur && SC.cur.kind === 'hatch')) return; const o = st(); base = GY;
      if (o.phase === 'egg') { if (z === 'front') { drawEgg(x, base); drawDream(x); } return; }
      if (o.phase !== 'kid' || K.hidden) return;
      const c = SC.cur, kz = c && c.F && c.F.actors.kid && c.F.actors.tr ? (c.F.actors.kid.z > c.F.actors.tr.z ? 'front' : 'back') : 'back';
      if (z === kz) drawKid(x, base);
      if (z === 'front') { drawBlanket(x, base); drawOverlays(x, base); drawHearts(x, base); drawPropFallback(x); }
    };

    // ── 圖鑑「團絨教錯咗乜」──
    G.s2Dex = function () {
      const o = st(), s = S(), now = G.now(), sec = document.createElement('div'); sec.dataset.testid = 'dex-s2'; sec.style.cssText = 'grid-column:1/-1;margin-top:' + (o.phase === 'none' || o.phase === 'due' ? 2 : 8) + 'px;font-size:11px;line-height:1.35';
      const sil = (src) => '<span style="display:inline-block;width:22px;height:22px">' + (src ? '<img src="' + BASE + src + '" width="22" height="22" style="image-rendering:pixelated;filter:brightness(0);opacity:.35">' : '') + '</span>';
      const lockRow = (t, src, tid) => '<div data-testid="' + tid + '" data-locked="1" style="display:flex;gap:6px;align-items:center;padding:3px 4px;border-radius:6px;background:rgba(255,255,255,.06);margin-top:3px;opacity:.8"><span style="width:34px">' + t + '</span>' + sil(src) + '<span>未遇見</span></div>';
      const propSrc = (i) => { const L = SR.LINES[i % SR.LINES.length], u = A.ui && A.ui.props[L]; return u ? u.png : null; }, dreamSrc = (i) => { const L = SR.LINES[i % SR.LINES.length], u = A.ui && A.ui.dreams[L]; return u ? u.png : null; };
      if (o.phase === 'none' || o.phase === 'due') {   // 4a.1：未有蛋都顯示（全部「未遇見」剪影）
        let h0 = '<b style="font-size:12px">新寵物系列・團絨教錯咗乜</b><div data-testid="dex-s2-status" data-stage="" data-line="" data-rel="" data-locked="1" style="opacity:.85">細佬：未遇見' + (o.phase === 'due' ? '（明日蝸牛郵差送蛋）' : '（團絨到「靜光」先會有蛋）') + '</div>';
        const chip = (t, src, tid) => '<span data-testid="' + tid + '" data-locked="1" title="' + t + '：未遇見" style="display:flex;flex-direction:column;align-items:center;width:26px;font-size:8.5px;line-height:10px;opacity:.85">' + sil(src) + '<span>' + t + '</span></span>';   // 細格：未有蛋都塞得落一版
        h0 += '<div data-testid="dex-s2-locked" style="display:flex;justify-content:space-between;margin-top:3px;padding:2px 2px;border-radius:6px;background:rgba(255,255,255,.06)">' + chip('細佬', 'egg/egg_48.png', 'dex-s2-lock-kid');
        for (let i = 0; i < C.eggNights; i++) h0 += chip('夢' + (i + 1), dreamSrc(i), 'dex-s2-lock-dream-' + (i + 1));
        for (let i = 0; i < C.lessonsMax; i++) h0 += chip('堂' + (i + 1), propSrc(i), 'dex-s2-lock-lesson-' + (i + 1));
        h0 += '</div>';
        sec.innerHTML = h0; return sec;
      }
      const sk = SR.stageOf(s, now), row = (t, inner, tid) => '<div data-testid="' + tid + '" style="display:flex;gap:6px;align-items:center;padding:3px 4px;border-radius:6px;background:rgba(255,255,255,.1);margin-top:3px">' + t + inner + '</div>';
      const icon = (L, kind) => { const u = A.ui && (kind === 'dream' ? A.ui.dreams[L] : A.ui.props[L]); return u ? '<img src="' + BASE + u.png + '" width="22" height="22" style="image-rendering:pixelated">' : ''; };
      let h = '<b style="font-size:12px">團絨教錯咗乜</b>　<span data-testid="dex-s2-status" data-stage="' + sk + '" data-line="' + (o.line || '') + '" data-rel="' + o.rel + '">細佬：' + SR.STAGE_ZH[sk] + (o.line ? '・' + SR.LINE_ZH[o.line] + '系' : '') + '・親密 ' + o.intim + '・' + SR.REL_ZH[o.rel] + '</span>';
      for (let i = 0; i < C.eggNights; i++) { const d = o.dreams[i]; h += d ? row('<span style="width:34px">夢 ' + (i + 1) + '</span>', d.line ? icon(d.line, 'dream') + SR.CARE_ZH[d.line] + '（' + SR.LINE_ZH[d.line] + ' +1）' : '瞓得好熟，冇發夢', 'dex-s2-dream-' + (i + 1)) : lockRow('夢 ' + (i + 1), dreamSrc(i), 'dex-s2-lock-dream-' + (i + 1)); }
      o.lessons.forEach((l, i) => { h += row('<span style="width:34px">堂 ' + (i + 1) + '</span>', icon(l.line, 'prop') + SR.PROP_ZH[l.line] + '：' + SR.WRONG[l.line] + '（' + SR.LINE_ZH[l.line] + ' +1）', 'dex-s2-lesson-' + (i + 1)); });
      for (let i = o.lessons.length; i < C.lessonsMax; i++) h += lockRow('堂 ' + (i + 1), propSrc(i), 'dex-s2-lock-lesson-' + (i + 1));
      if (!o.lessons.length) h += '<div data-testid="dex-s2-lesson-hint" style="opacity:.7;margin-top:3px">（蛋殼仔／BB 期撳細佬上堂）</div>';
      if (o.settle) h += '<div data-testid="dex-s2-settle" data-how="' + o.settle.how + '" style="margin-top:4px;opacity:.85">結算：' + ({ max: '最高分', tieLesson: '打和 → 最近一堂', tieDream: '打和 → 最近一個夢', random: '冇分 → 隨機' }[o.settle.how] || o.settle.how) + ' → ' + SR.LINE_ZH[o.line] + '系</div>';
      sec.innerHTML = h; return sec;
    };

    // ── 4a.1 設定「試玩：新寵物系列」（永遠顯示；唔掂團絨成長／碎／路線／懸浮）──
    function closeSettings() { const b = document.querySelector('#mbox[data-kind=settings] [data-testid=modal-btn-0]') || (document.getElementById('mbox').dataset.kind === 'settings' ? document.querySelector('#mbox [data-testid=modal-btn-0]') : null); if (b) b.click(); }
    const TEST = {
      deliver() { const o = st(), now = G.now(); if (o.phase === 'egg' || o.phase === 'kid') return { ok: false, msg: '已經有細佬（最多 1 隻）' };
        if (o.phase === 'none') { o.phase = 'due'; o.elderAt = now; o.test = true; } o.dueDay = SR.dayNum(now); const r = deliverEgg('test'); if (r.ok) say(L_.deliver, { sec: 4 }); return { ok: !!r.ok, msg: r.ok ? '細佬蛋送到！' : '送唔到' }; },
      hatch() { let o = st(); const now = G.now(); if (o.phase === 'kid') return { ok: false, msg: '細佬已經孵咗' }; if (o.phase !== 'egg') { const r = TEST.deliver(); if (!r.ok) return r; o = st(); }
        if (SC.cur) return { ok: false, msg: '而家播緊場面' }; for (let i = o.dreams.length; i < C.eggNights; i++) o.dreams.push({ day: SR.nightOf(now) - (C.eggNights - 1 - i), line: SR.topCare(S(), SR.nightOf(now)) || null, at: now, live: false, test: true });
        o.test = true; S().sleeping = false; hatchStart(); return { ok: true, msg: '孵化！' }; },
      level() { const o = st(); if (o.phase !== 'kid') return { ok: false, msg: '要先孵化細佬' }; if (o.rel === 'family') return { ok: false, msg: '已經係家人（屋仔即將開放（4b））' };
        const to = o.rel === 'follow' ? 'friend' : 'family'; o.intim = Math.max(o.intim, to === 'friend' ? C.friendAt : C.familyAt); o.rel = to; o.relQ.push(to); o.test = true; if (G.save) G.save(); note('testLevel', { to }); return { ok: true, msg: '關係 → ' + SR.REL_ZH[to] }; },
      cry() { const o = st(); if (o.phase !== 'kid') return { ok: false, msg: '要先孵化細佬' }; if (K.cry) return { ok: false, msg: '細佬喊緊' }; if (SC.cur) return { ok: false, msg: '而家播緊場面' }; if (S().sleeping) S().sleeping = false; { const bx = trX(), gap = trHalf() + 16; if (Math.abs(K.x - bx) < gap) { const sd = bx + gap <= 70 ? 1 : -1; K.x = clamp(bx + sd * gap, -70, 70); K.dir = -sd; } } /* 試玩：唔好匿喺團絨後面 */ cryStart(); return { ok: true, msg: '細佬喊喇！拖團絨過去哄佢' }; },
    };
    G.s2Settings = function (node) {
      const o = st(), sec = document.createElement('div'); sec.dataset.testid = 's2-test'; sec.style.cssText = 'margin:2px 0 10px;padding:8px;border-radius:10px;background:rgba(255,214,110,.16);border:1px solid rgba(255,214,110,.55);text-align:left';
      sec.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:13px">試玩：新寵物系列</b><span data-testid="s2-version" style="font-size:11px;opacity:.85">版本 ' + VERSION + '</span></div>' +
        '<div data-testid="s2-test-status" data-phase="' + o.phase + '" style="font-size:11px;opacity:.8;margin:3px 0 6px">細佬：' + ({ none: '未有蛋', due: '明日送蛋', egg: '蛋（孵夢 ' + o.dreams.length + '／' + C.eggNights + '）', kid: SR.STAGE_ZH[SR.stageOf(S(), G.now())] + '・' + SR.REL_ZH[o.rel] }[o.phase] || o.phase) + '</div>';
      const grid = document.createElement('div'); grid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:6px';
      for (const [k, t] of [['deliver', '即刻送蛋'], ['hatch', '即刻孵化'], ['level', '升一級關係'], ['cry', '觸發喊']]) {
        const b = document.createElement('div'); b.className = 'btn'; b.dataset.testid = 's2-test-' + k; b.textContent = t; b.style.cssText = 'margin:0;padding:8px 4px;font-size:13px';
        b.addEventListener('click', () => { closeSettings(); setTimeout(() => { let r; try { r = TEST[k](); } catch (e) { r = { ok: false, msg: String(e && e.message || e) }; } note('test', { k, ok: r.ok }); UI.toast(r.msg, 2400); UIS(r.ok ? 'confirm' : 'disabled'); }, 60); });
        grid.appendChild(b); }
      sec.appendChild(grid); const n = document.createElement('div'); n.style.cssText = 'font-size:10px;opacity:.65;margin-top:5px'; n.textContent = '試玩用：唔會改團絨成長、星屑、路線同懸浮寵物'; sec.appendChild(n);
      node.insertBefore(sec, node.firstChild);
    };

    // ── CSS ──
    { const css = document.createElement('style'); css.textContent = 'body.s2-scene #ui>*:not(#hit):not(#hdFx),body.s2-scene #s2Tray{visibility:hidden!important}'; document.head.appendChild(css); }

    /* 每幀（main loop，b3bTick 之後） */
    G.s2Tick = function (dt) {
      dt = Math.min(0.1, dt || 0); if (!A.ready) return;
      try { careTick(); } catch (e) { }
      deliverTick(); dreamTick(); sceneTick(dt); dragTick(dt); levelTick(); cryTick(dt); sleepTick(); kidTick(dt);
      if (trayOn && (SC.cur || UI.isModalOpen() || !SR.canLesson(S(), G.now()).ok)) tray(false);
    };

    window.__qa = window.__qa || {};
    window.__qa.s2 = {
      st: () => ({ ready: A.ready, errors: A.errors.slice(), auto: Object.assign({}, AUTO), save: JSON.parse(JSON.stringify(st())), stage: SR.stageOf(S(), G.now()), form: formNow(),
        kid: { x: +K.x.toFixed(1), dir: K.dir, clip: K.clip, mode: K.mode, cry: !!K.cry, hearts: K.hearts.length }, egg: { x: +EGG.x.toFixed(1) }, scene: SC.cur ? { kind: SC.cur.kind, t: Math.round(SC.cur.t), skip: !!SC.cur.skip, last: SC.cur.last || null, rel: SC.cur.rel || null, rxOk: SC.cur.rxOk, copy: SC.cur.copyEv || null } : null,
        tray: trayOn, render: Object.assign({}, RST), dream: DR.show, rxOk: !!A.rxOk, puppet: G.beh && G.beh.puppet ? Object.assign({}, G.beh.puppet) : null, gest: G.beh && G.beh.gest ? { key: G.beh.gest.key, clip: G.beh.gest.clip } : null, drag: DRAG.on, log: log.slice() }),
      elder: () => SR.noteElder(S(), G.now()), deliver: () => deliverEgg('qa'), arrive: () => G.s2Arrived('snail_postman'),
      set: (o) => { Object.assign(st(), o || {}); SR.st(S()); if (G.save) G.save(); return JSON.parse(JSON.stringify(st())); },
      hatch: () => { if (!SC.cur) hatchStart(); return !!SC.cur; }, tap: () => sceneTap(), sceneAt: (ms) => { if (SC.cur) SC.cur.t = ms; return !!SC.cur; },
      cry: () => cryStart(), comfort: () => comfortStart(trX()), lesson: (L) => lessonStart(L), eat: () => eatTogether(), card: () => card(), kidTap: () => kidTap(), duo: () => duoStart(),
      level: (rel) => { st().relQ.push(rel || 'follow'); return true; }, tray: (v) => { tray(v !== false); return trayOn; }, dex: () => { const n = G.s2Dex(); return n ? n.outerHTML : null; },
      kidCss: () => { const r = kidRect(), b = R.canvas.getBoundingClientRect(); return { x: b.left + (r.x + r.w / 2) / 195 * b.width, y: b.top + (r.y + r.h / 2) / 422 * b.height }; },
      petCss: () => { const r = UI.petHitBox(), b = R.canvas.getBoundingClientRect(); return { x: b.left + (r.x + r.w / 2) / 195 * b.width, y: b.top + (r.y + r.h / 2) / 422 * b.height }; },
      css: (x, y) => { const r = R.canvas.getBoundingClientRect(); return { x: r.left + x / 195 * r.width, y: r.top + y / 422 * r.height }; },
      auto: (k, v) => { AUTO[k] = !!v; return Object.assign({}, AUTO); }, test: (k) => TEST[k](), version: VERSION, native, nextCry: (ms) => { sess.nextCry = pnow() + (ms || 0); }, kidX: (x) => { K.x = x; },
    };
    note('install'); return true;
  }
  return { install };
});
