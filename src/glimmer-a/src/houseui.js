/* 《微光小圃》 houseui.js — 第 4 批 4b 屋仔畫面（docs-gdd/series2-4a4b-spec.md v1.1 §4b；遊美 art/series2_house HOUSE_4B.md）。原創代碼。
   花園 rail「屋仔」掣（家人前上鎖）→ 全畫面 HD-2D 房間（日夜 crossfade、lightmap／light_add／bloom／燈 glow／vignette）、6 擺位家具 ysort、
   兩隻自己生活（周圍行、坐埋一齊、整蠱每日 ≤3、21:00–03:00 同床瞓）、撳團絨＝3a 觸摸反應（G.tch）、撳細佬＝跳一跳；
   佈置模式（房間上移 36、底部 sheet：6 tab／每位 2 件＋收起／pin／買嘢用 HD popup 確認／完成）。
   邏輯全部喺 house.js（s.pet2.house）；唔加路線分、唔出碎；團絨成長／浮動唔郁；?house=0 全停。
   圖一律用 Image.src（單檔 build shim 攔截），唔用 CSS url()。
   5a（long5a.js s.fam；遊美 art/series2_long/5a）：房 1–4（左右箭咀／圓點；未開＝「家族 LvN 開」）、每間房各自擺位（家具一件一間）＋第 7 個「擺設」tab（手信）、
   長住成年（周圍行／瞓／撳 → 寵物卡）、打招呼（interact strip；兩隻面對面；閒住 1/90s）、HUD 家族等級／住幾多隻／族譜。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.houseui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  function install(G, NS) {
    const HS = NS.house, SR = NS.series2, D = NS.data, P = D.PARAMS.house; if (!HS || !SR || !P || P.enabled === false || !G.s2Art) return false;
    const qs = new URLSearchParams(location.search); if (qs.get('house') === '0' || qs.get('s2') === '0') return false;
    const FAM = NS.long5a, LBASE = 'art/series2_long/', UI = NS.ui, X = NS.sys12, R = G.renderer, SA = G.s2Art, BASE = P.art.base, S = () => G.state, pnow = () => performance.now();
    const store = { get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { } } };
    const SND = (k, i) => { const a = NS.audio; if (a && a.Engine) a.Engine.notify(k, i || {}); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const fmt = (t, o) => t.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m));
    const save = () => { if (G.save) G.save(); };
    const log = []; const note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const W = 195, H = 422, KP = 2, LX = -14, LY = -12;

    // ── 載圖 ──
    const A = { ready: false, errors: [], img: {}, H: null, ACT: null };
    const img = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = () => rej(new Error(src)); i.src = src; });
    const jget = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const want = new Set();
    const srcOf = (f) => (f.startsWith('L:') ? LBASE + f.slice(2) : BASE + f);
    function need(f) { if (!f || A.img[f] || want.has(f)) return A.img[f] || null; want.add(f); img(srcOf(f)).then(i => { A.img[f] = i; }).catch(() => A.errors.push(f)); return null; }
    const im = (f) => (f ? A.img[f] || need(f) : null);
    const mkImg = (f, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = srcOf(f); return i; };
    const LAYERS = ['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive_blur', 'vignette'];
    G.houseLoad = Promise.all([jget(BASE + 'house.json'), jget(BASE + 'actions/actions_house.json'), jget(BASE + 'room/day/grade.json'), jget(BASE + 'room/night/grade.json'),
      FAM ? jget(LBASE + '5a/long_5a.json').catch(() => null) : null])
      .then(([Hj, ACT, gd, gn, L5]) => {
        Object.assign(A, { H: Hj, ACT, L5, grade: { day: gd, night: gn } }); const files = new Set();
        if (FAM) { for (const x of FAM.SOUV) { files.add('L:' + x.px); files.add('L:' + x.icon); } for (const n of ['btn_room_l_idle', 'btn_room_l_locked', 'btn_room_r_idle', 'btn_room_r_locked', 'btn_tree', 'dot_room_cur', 'dot_room_open', 'dot_room_locked', 'icon_crown', 'icon_family_level', 'icon_pets']) files.add('L:5a/ui/' + n + '@3x.png'); }
        for (const v of ['day', 'night']) for (const l of LAYERS) files.add('room/' + v + '/' + l + '.png');
        for (const id in Hj.furniture) { const f = Hj.furniture[id]; for (const k of ['png', 'front', 'glow', 'emissive']) if (f[k]) files.add(f[k]); }
        for (const k in Hj.ui.assets) files.add(Hj.ui.assets[k]);
        return Promise.all([...files].map(f => img(srcOf(f)).then(i => { A.img[f] = i; }).catch(() => A.errors.push(f))));
      }).then(() => { A.ready = true; note('loaded'); if (FAM) setTimeout(() => { for (const k of FAM.ROOMS) if (k !== 'room1' && FAM.roomOpen(S(), k)) loadRoom(k); }, 800); return A; }).catch(e => { A.errors.push(String(e && e.message || e)); return null; });

    // ── 5a 房 2–4（lazy：開咗房／入房先載）──
    A.roomP = {};
    const roomDir = (k, v) => (k === 'room1' ? 'room/' + v + '/' : 'L:5a/rooms/' + k + '/' + v + '/');
    const gradeOf = (k, v) => (k === 'room1' ? A.grade[v] : A.grade[k + ':' + v]) || A.grade[v];
    function loadRoom(k) {
      if (k === 'room1') return Promise.resolve(true); if (A.roomP[k]) return A.roomP[k];
      return (A.roomP[k] = Promise.all(['day', 'night'].map(v => jget(LBASE + '5a/rooms/' + k + '/' + v + '/grade.json').then(g => { A.grade[k + ':' + v] = g; })
        .then(() => Promise.all(LAYERS.map(l => { const f = roomDir(k, v) + l + '.png'; return A.img[f] ? null : img(srcOf(f)).then(i => { A.img[f] = i; }).catch(() => A.errors.push(f)); })))))
        .then(() => { note('roomLoaded', { k }); return true; }).catch(e => { A.errors.push(String(e && e.message || e)); A.roomP[k] = null; return false; }));
    }

    // ── 色調（家具 × ambientTint；寵物 × petTint × ambientTint）──
    const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
    const mulHex = (a, b) => { const x = hex(a), y = hex(b); return '#' + x.map((v, i) => Math.round(v * y[i] / 255).toString(16).padStart(2, '0')).join(''); };
    const TC = new Map();
    function tinted(image, tint) {
      if (!image || !tint || tint === '#ffffff') return image; let m = TC.get(image); if (!m) TC.set(image, m = {}); if (m[tint]) return m[tint];
      const c = document.createElement('canvas'); c.width = image.width; c.height = image.height; const g = c.getContext('2d');
      g.drawImage(image, 0, 0); g.globalCompositeOperation = 'multiply'; g.fillStyle = tint; g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = 'destination-in'; g.drawImage(image, 0, 0); return (m[tint] = c);
    }

    // ── 畫面狀態 ──
    const V = { room: 'room1', el: null, cv: null, ctx: null, off: {}, open: false, deco: false, sel: 'bed', offY: 0, offFrom: 0, offTo: 0, offT0: 0, raf: 0, last: 0, mix: null, nightOv: null, sleepOv: null, from: null,
      stats: { frames: 0, furn: 0, pets: 0, glow: 0, layers: 0, hearts: 0, zzz: 0, wah: 0, variant: null, res: 0, greets: 0, deco: 0 }, hud: null, dk: null, pins: {}, tabs: {}, cards: null, chip: null };
    const Z = { mode: 'free', t: 0, nextDuo: 0, sit: null, prank: null, hearts: [], wah: 0, forcePrank: false, greet: null };
    const ACT = (who) => ({ who, x: who === 'tr' ? 80 : 116, y: 300, dir: who === 'tr' ? 1 : -1, mode: 'idle', clip: 'idle', ct: 0, tgt: null, until: 0, speed: 10, onArrive: null, hop: 0, sortY: 300, box: null, dx: 0 });
    const PET = { tr: ACT('tr'), kid: ACT('kid') };
    const nowMs = () => G.now();
    const rnd = (a, b) => a + Math.random() * (b - a);
    const night = () => (V.nightOv != null ? V.nightOv : (() => { const h = HS.hourOf(nowMs()); return h >= 19 || h < 6; })());
    const sleepWanted = () => (V.sleepOv != null ? V.sleepOv : HS.sleepTime(nowMs()) || !!S().sleeping);
    const Hj = () => A.H;
    const slotAnchor = (k) => Hj().slots[k].anchor;
    const slotsNow = () => (FAM ? FAM.slotsOf(S(), V.room) : HS.st(S()).slots);
    const furnOf = (k) => { const id = slotsNow()[k]; return id ? Hj().furniture[id] : null; };
    const decoNow = () => (FAM ? FAM.st(S()).rooms[V.room].deco : null);
    /* 房 1 先有主養團絨（光卵唔出）＋細佬（孵咗先出）；其他房只有住客 */
    const kmNow = () => (FAM && FAM.kmOf ? FAM.kmOf(S()) : null);   // 5a.1：細佬做主養 → 屋企 room1 個主位係細佬（住客式畫）；團絨係住客
    const vis = (k) => V.room === 'room1' && (k === 'tr' ? S().stage !== 'egg' && !kmNow() : SR.st(S()).phase === 'kid');
    const rugSpot = () => { const f = furnOf('rug'); return f ? slotAnchor('rug') : [100, 290]; };
    const walkRect = () => Hj().walk.rect;
    const bl = () => (FAM ? FAM.blockers(S(), V.room, Hj()) : HS.blockers(S(), Hj()));

    // ── 寵物行為 ──
    function goTo(p, x, y, cb, speed) { p.tgt = [x, y]; p.mode = 'walk'; p.clip = 'walk'; p.onArrive = cb || null; p.speed = speed || 10; }
    function idle(p, sec) { p.mode = 'idle'; p.clip = 'idle'; p.tgt = null; p.until = pnow() + (sec != null ? sec : rnd(2, 5)) * 1000; p.onArrive = null; }
    function playClip(p, clip, loopMs) { p.mode = 'clip'; p.clip = clip; p.ct = 0; p.tgt = null; p.until = pnow() + (loopMs || 1000); }
    function free() { Z.mode = 'free'; Z.sit = null; Z.prank = null; for (const k in PET) { PET[k].dx = 0; idle(PET[k], rnd(0.5, 2)); } Z.nextDuo = pnow() + rnd(12, 22) * 1000; }
    function startSit(force) {
      const r = rugSpot(); Z.mode = 'sit'; Z.sit = { t0: 0, x: r[0], y: r[1], seated: false, lastHeart: 0 }; const tr = PET.tr, kd = PET.kid;
      if (force) { tr.x = r[0] - 18; tr.y = r[1] + 2; kd.x = r[0] + 18; kd.y = r[1] + 2; }
      goTo(tr, r[0] - 18, r[1] + 2, () => { tr.dir = 1; idle(tr, 99); }); goTo(kd, r[0] + 18, r[1] + 2, () => { kd.dir = -1; idle(kd, 99); }); note('sit', { force: !!force }); return true;
    }
    function startPrank(force) {
      if (!force && !HS.canPrank(S(), nowMs())) return false;
      const kidP = Math.random() < 0.7, p = kidP ? PET.kid : PET.tr, v = kidP ? PET.tr : PET.kid, B = bl(), rect = walkRect();
      let vx = v.x, vy = v.y; if (!HS.walkable(vx - 30, vy, rect, B) || !HS.walkable(vx, vy, rect, B)) { for (let i = 0; i < 40; i++) { const s = HS.pickSpot(rect, B); if (HS.walkable(s[0] - 30, s[1], rect, B)) { vx = s[0]; vy = s[1]; break; } } }
      if (force) { v.x = vx; v.y = vy; p.x = vx - 30; p.y = vy; }
      Z.mode = 'prank'; Z.prank = { p: p.who, v: v.who, ready: 0, t: -1, counted: false, force: !!force };
      goTo(v, vx, vy, () => { v.dir = 1; idle(v, 99); Z.prank.ready |= 1; }); goTo(p, vx - 30, vy, () => { p.dir = 1; idle(p, 99); Z.prank.ready |= 2; }); note('prank', { p: p.who, force: !!force }); return true;
    }
    function sleepSpots() { const f = furnOf('bed'); if (f && f.sleepSpots) { const a = slotAnchor('bed'); return { bed: true, tr: [a[0] + f.sleepSpots[0][0], a[1] + f.sleepSpots[0][1]], kid: [a[0] + f.sleepSpots[1][0], a[1] + f.sleepSpots[1][1]] }; }
      const r = rugSpot(); return { bed: false, tr: [r[0] - 10, r[1] + 2], kid: [r[0] + 10, r[1] + 2] }; }
    function startSleep(instant) {
      Z.mode = 'sleep'; Z.sit = null; Z.prank = null; const sp = sleepSpots(); Z.bed = sp.bed;
      for (const k of ['tr', 'kid']) { const p = PET[k], at = sp[k]; p.dx = 0; const fin = () => { p.x = at[0]; p.y = at[1]; p.dir = k === 'tr' ? 1 : -1; p.mode = 'sleep'; p.clip = 'sleep'; p.tgt = null; };
        if (instant || sp.bed) fin(); else goTo(p, at[0], at[1], fin); }
      note('sleep', { bed: sp.bed });
    }
    function stepPet(p, dt) {
      p.ct += dt * 1000; if (p.hop > 0) p.hop = Math.max(0, p.hop - dt * 1000);
      if (p.mode === 'walk' && p.tgt) { const dx = p.tgt[0] - p.x, dy = p.tgt[1] - p.y, d = Math.hypot(dx, dy), s = p.speed * dt;
        if (Math.abs(dx) > 0.3) p.dir = dx < 0 ? -1 : 1;
        if (d <= s) { p.x = p.tgt[0]; p.y = p.tgt[1]; p.tgt = null; const cb = p.onArrive; p.onArrive = null; idle(p); if (cb) cb(); } else { p.x += dx / d * s; p.y += dy / d * s; } }
      else if (p.mode === 'idle' && (p.who === 'res' || Z.mode === 'free') && pnow() > p.until) { const s = HS.pickSpot(walkRect(), bl()); goTo(p, s[0], s[1]); }
      else if (p.mode === 'clip' && pnow() > p.until && (p.who === 'res' || Z.mode === 'free')) idle(p);
    }
    function behave(dt) {
      const now = pnow(); if (!A.ready) return;
      const wantSleep = sleepWanted();
      if (wantSleep && Z.mode !== 'sleep') startSleep(false); else if (!wantSleep && Z.mode === 'sleep') { free(); }
      if (Z.mode === 'sleep') { const sp = sleepSpots(); if (sp.bed !== Z.bed) startSleep(true); }
      if (Z.mode === 'free' && now > Z.nextDuo && Z.nextDuo) { if (Z.greet || !vis('tr') || !vis('kid')) Z.nextDuo = now + rnd(8, 14) * 1000; else if (HS.canPrank(S(), nowMs()) && Math.random() < 0.4) startPrank(false); else startSit(false); }
      syncRes(); for (const p of RS.values()) { if (wantSleep && p.mode !== 'sleep' && !(Z.greet && (Z.greet.a === p || Z.greet.b === p))) { p.mode = 'sleep'; p.clip = 'sleep'; p.tgt = null; p.onArrive = null; } else if (!wantSleep && p.mode === 'sleep') idle(p, rnd(0.5, 3)); }
      greetTick(now, dt, wantSleep);
      if (Z.mode === 'sit' && Z.sit) { const c = Z.sit, tr = PET.tr, kd = PET.kid;
        if (!c.seated && !tr.tgt && !kd.tgt) { c.seated = true; c.t0 = now; tr.dir = 1; kd.dir = -1; playClip(tr, 'sit', 99e3); playClip(kd, 'sit', 99e3); c.lastHeart = now - 1800; }
        if (c.seated) { if (now - c.lastHeart >= 2400) { c.lastHeart = now; Z.hearts.push({ x: c.x, y: c.y - 30, t0: now }); V.stats.hearts++; } if (now - c.t0 > 6000) free(); } }
      if (Z.mode === 'prank' && Z.prank) { const c = Z.prank, p = PET[c.p], v = PET[c.v];
        if (c.t < 0 && c.ready === 3) { c.t = 0; c.t0 = now; if (!c.force) { HS.notePrank(S(), nowMs()); save(); } c.counted = true; playClip(p, 'prank_do', 99e3); playClip(v, 'prank_got', 99e3); p.dir = 1; v.dir = 1; }
        if (c.t >= 0) { c.t = now - c.t0; const f = Math.min(7, Math.floor(c.t / 120)); p.dx = f >= 3 ? 6 : f * 2;
          if (c.t >= 480 && !c.wah) { c.wah = true; Z.wah = now; V.stats.wah++; UIS('tap'); }
          if (c.t >= 960 && !c.sat) { c.sat = true; v.dir = -1; p.x += p.dx; p.dx = 0; playClip(p, 'sit', 99e3); playClip(v, 'sit', 99e3); c.satT = now; }
          if (c.sat && now - c.satT > 900) free(); } }
      for (const k in PET) if (vis(k)) stepPet(PET[k], dt);
      for (const p of RS.values()) if (p.mode !== 'sleep') stepPet(p, dt); else p.ct += dt * 1000;
      Z.hearts = Z.hearts.filter(h => now - h.t0 < 900);
    }

    // ── 5a 長住（住客 actor）＋打招呼 ──
    const RS = new Map(); let rsKey = '';
    function syncRes(force) {
      if (!FAM) return; const K = kmNow(), HX = G.h5x, list = FAM.st(S()).res.filter(r => r.room === V.room && !(HX && HX.hide && HX.hide(r.id))).concat(K && V.room === 'room1' ? [{ id: K.id, kind: 'kid', fk: K.fk, km: 1 }] : []), key = V.room + '|' + list.map(r => r.id + ':' + r.fk).join(',');
      if (!force && key === rsKey) return; rsKey = key; const keep = new Map(RS); RS.clear();
      list.forEach((r, i) => { let p = keep.get(r.id); if (!p || p.fk !== r.fk) { const s = A.ready ? HS.pickSpot(walkRect(), bl()) : [60 + i * 24, 300];
        p = Object.assign(ACT('res'), { id: r.id, kind: r.kind, fk: r.fk, x: s[0], y: s[1], dir: Math.random() < 0.5 ? 1 : -1 }); idle(p, rnd(0.5, 4)); } p.km = !!r.km; RS.set(r.id, p); });
      if (Z.greet && ![Z.greet.a, Z.greet.b].every(a => a.who !== 'res' || RS.get(a.id) === a)) Z.greet = null;
      note('res', { room: V.room, n: RS.size });
    }
    const actors = () => { const o = []; for (const k of ['tr', 'kid']) if (vis(k)) o.push(PET[k]); for (const p of RS.values()) o.push(p); return o; };
    const actorOf = (id) => { if (!id) return null; if (RS.get(id)) return RS.get(id); if (id === 'tr' || (FAM && id === FAM.trId(S()))) return vis('tr') ? PET.tr : null; if (id === 'kid' || id === SR.st(S()).fid) return vis('kid') ? PET.kid : null; return RS.get(id) || null; };
    const fkOfA = (p) => (p.who === 'res' ? p.fk : p.who === 'tr' ? trForm() : SA.formNow());
    const isTrA = (p) => p.who === 'tr' || (p.who === 'res' && p.kind === 'tr');
    const BW = {};
    function sitW(p) {   // sit 第 0 格 bbox 闊（冇 sit strip → idle 估）
      const fk = fkOfA(p); if (BW[fk] != null) return BW[fk]; const c = A.ACT && A.ACT.forms[fk] && A.ACT.forms[fk].sit, i = c && im(c.png); if (!i) return 24;
      try { const cv = document.createElement('canvas'); cv.width = c.frameW; cv.height = c.frameH; const g = cv.getContext('2d'); g.drawImage(i, 0, 0, c.frameW, c.frameH, 0, 0, c.frameW, c.frameH);
        const d = g.getImageData(0, 0, c.frameW, c.frameH).data; let a = c.frameW, b = -1; for (let y = 0; y < c.frameH; y++) for (let x = 0; x < c.frameW; x++) if (d[(y * c.frameW + x) * 4 + 3] > 20) { if (x < a) a = x; if (x > b) b = x; }
        return (BW[fk] = b >= a ? b - a + 1 : 24); } catch (e) { return (BW[fk] = 24); }
    }
    function startGreet(a, b, force) {
      if (!FAM || !a || !b || a === b || (Z.greet && !force)) return false; if (a.mode === 'sleep' || b.mode === 'sleep') { if (!force) return false; }
      if ((a.who !== 'res' || b.who !== 'res') && Z.mode !== 'free') { if (!force) return false; free(); }
      if (a.x > b.x) { const t = a; a = b; b = t; }
      const gap = FAM.duoGap(sitW(a), sitW(b)), B = bl(), rect = walkRect(); let bx = b.x, by = b.y;
      if (!HS.walkable(bx - gap, by, rect, B) || !HS.walkable(bx, by, rect, B)) for (let i = 0; i < 40; i++) { const s = HS.pickSpot(rect, B); if (HS.walkable(s[0] - gap, s[1], rect, B)) { bx = s[0]; by = s[1]; break; } }
      if (force) { b.x = bx; b.y = by; a.x = bx - gap; a.y = by; }
      const g = Z.greet = { a, b, gap, t0: 0, ready: 0, start: pnow(), force: !!force, heart: false };
      goTo(b, bx, by, () => { b.dir = -1; idle(b, 99); if (Z.greet === g) g.ready |= 1; }, 14); goTo(a, bx - gap, by, () => { a.dir = 1; idle(a, 99); if (Z.greet === g) g.ready |= 2; }, 14);
      note('greet', { a: a.id || a.who, b: b.id || b.who, gap, force: !!force }); return true;
    }
    function greetTick(now, dt, wantSleep) {
      const g = Z.greet;
      if (!g) { if (!FAM || wantSleep || Z.mode !== 'free' || V.deco) return; const xs = actors().filter(p => p.mode === 'idle' || p.mode === 'walk'); if (xs.length >= 2 && Math.random() < dt / 90) { const a = xs[Math.floor(Math.random() * xs.length)], rest = xs.filter(p => p !== a); startGreet(a, rest[Math.floor(Math.random() * rest.length)], false); } return; }
      if (!g.t0) { if (g.ready === 3) { g.t0 = now; g.a.dir = 1; g.b.dir = -1; playClip(g.a, 'interact', 99e3); playClip(g.b, 'interact', 99e3); V.stats.greets++; UIS('tap'); } else if (now - g.start > 9000) { Z.greet = null; idle(g.a); idle(g.b); } return; }
      const u = now - g.t0; if (u >= 480 && !g.heart) { g.heart = true; Z.hearts.push({ x: (g.a.x + g.b.x) / 2, y: g.a.y - 40, t0: now }); V.stats.hearts++; }
      if (u >= 1000) { Z.greet = null; idle(g.a, rnd(1.5, 3)); idle(g.b, rnd(1.5, 3)); g.a.ct = 0; g.b.ct = 0; }
    }
    function interactSrc(p, fk) { const c = A.L5 && A.L5.actions && A.L5.actions.interact.forms[fk]; if (!c) return null; const c2 = Object.assign({}, c, { png: 'L:5a/' + c.png }), ii = im(c2.png); if (!ii) return null; return { img: ii, ...stripFrame(c2, { frameMs: 120 }, p) }; }

    // ── 畫 ──
    const trForm = () => (R && R.fkOf ? R.fkOf(S()) : 'sprout');
    function trSrc(p) {
      const fk = p.who === 'res' ? p.fk : trForm(), AF = A.ACT && A.ACT.forms[fk];
      if (p.clip === 'interact') { const s = interactSrc(p, fk); if (s) return s; }
      if ((p.clip === 'sit' || p.clip === 'prank_do' || p.clip === 'prank_got') && AF && AF[p.clip]) { const c = AF[p.clip], cl = A.ACT.clips[p.clip], ii = im(c.png); if (ii) return { img: ii, ...stripFrame(c, cl, p) }; }
      const clip = p.clip === 'walk' ? 'walk' : p.clip === 'sleep' ? 'sleep_loop' : p.clip === 'sit' ? 'emo_cuddly' : p.clip === 'prank_got' ? 'emo_surprised' : p.clip === 'prank_do' ? 'cheer_jump' : p.clip === 'interact' ? 'emo_happy' : 'idle';
      const a = SA.atlasSrc(fk, clip, p.ct, true); return a && a.src ? a.src : null;
    }
    function stripFrame(c, cl, p) {
      const n = Math.max(1, Math.round((im(c.png) || { width: c.frameW }).width / c.frameW)), ms = (cl && (cl.frameMs || cl.ms)) || (p.clip === 'sit' ? 150 : 120), fm = Array.isArray(ms) ? ms[0] : ms;
      let f = Math.floor(p.ct / fm); if (p.clip === 'sit') f = f < 2 ? f : 2 + ((f - 2) % Math.max(1, n - 2)); else f = Math.min(n - 1, f);
      f = clamp(f, 0, n - 1); return { sx: f * c.frameW, sy: 0, sw: c.frameW, sh: c.frameH, px: c.pivot[0], py: c.pivot[1], frame: f };
    }
    function kidSrc(p) {
      const fk = p.who === 'res' ? p.fk : SA.formNow(); if (!fk || fk === 'egg') return null; const AF = A.ACT && A.ACT.forms[fk];
      if (p.clip === 'interact') { const s = interactSrc(p, fk); if (s) return s; }
      if ((p.clip === 'sit' || p.clip === 'prank_do' || p.clip === 'prank_got') && AF && AF[p.clip]) { const c = AF[p.clip], cl = A.ACT.clips[p.clip], ii = im(c.png); if (ii) return { img: ii, ...stripFrame(c, cl, p) }; }
      const clip = p.clip === 'walk' ? 'walk' : p.clip === 'sleep' ? 'sleep' : 'idle', sp = SA.strip(fk, clip); if (!sp) return null; const f = SA.kidFrame(fk, clip, p.ct);
      return { img: sp, sx: f * 48, sy: 0, sw: 48, sh: 48, px: 24, py: 45, frame: f };
    }
    /* 6b.1：未有圖嘅家具（house.json png:null＋placeholder）→ 洋紅虛線框（size art 單位） */
    function phFurn(x, f, a) { if (!f.size) return; const l = Math.round(a[0] - f.pivot[0]), t = Math.round(a[1] - f.pivot[1]); x.save(); x.fillStyle = 'rgba(255,0,255,0.14)'; x.fillRect(l, t, f.size[0], f.size[1]); x.strokeStyle = '#ff00ff'; x.lineWidth = 1; x.setLineDash([3, 2]); x.strokeRect(l + 0.5, t + 0.5, f.size[0] - 1, f.size[1] - 1); x.restore(); V.stats.furn++; V.stats.ph = (V.stats.ph | 0) + 1; }
    function drawFurn(x, f, a, tint, part) { if (!f.png && part !== 'front') return phFurn(x, f, a); const i = im(part === 'front' ? f.front : f.png); if (!i) return; x.drawImage(tinted(i, tint), Math.round(a[0] - f.pivot[0]), Math.round(a[1] - f.pivot[1])); V.stats.furn++; }
    function shadowAt(x, cx, cy, w, h) { if (!(w > 0)) return; x.save(); x.fillStyle = 'rgba(60,36,40,0.27)'; x.beginPath(); x.ellipse(Math.round(cx), Math.round(cy), w / 2, Math.max(1, h / 2), 0, 0, Math.PI * 2); x.fill(); x.restore(); }
    function drawPet(x, p, tint) {
      const src = isTrA(p) ? trSrc(p) : kidSrc(p); if (!src) { p.box = null; return; }
      let ox = 0, oy = 0, sx = 1, sy = 1; const g = p.who === 'tr' && G.beh && G.beh.gest; if (g) { ox = g.dx || 0; oy = g.dy || 0; sx = g.sx || 1; sy = g.sy || 1; }
      if (p.hop > 0) oy -= Math.round(Math.sin((1 - p.hop / 400) * Math.PI) * 5);
      const X0 = Math.round(p.x + p.dx + ox), Y0 = Math.round(p.y + oy), flip = p.dir < 0;
      p.at = [X0, Y0, flip ? -1 : 1, src.frame != null ? src.frame : 0, src.px, src.py]; x.save(); x.translate(X0, Y0); x.scale((flip ? -1 : 1) * sx, sy); x.drawImage(tinted(src.img, tint), src.sx, src.sy, src.sw, src.sh, -src.px, -src.py, src.sw, src.sh); if (G.pat5c) G.pat5c.house(x, p, src, tint, tinted); x.restore();
      p.box = [X0 - Math.min(src.px, 20), Y0 - Math.min(src.py, 34), X0 + Math.min(src.sw - src.px, 20), Y0 + 3]; p.last = { clip: p.clip, frame: src.frame != null ? src.frame : src.name, w: src.sw }; V.stats.pets++;
    }
    function composeRoom(v, x) {
      const L = (n) => A.img[roomDir(V.room, v) + n + '.png'] || A.img['room/' + v + '/' + n + '.png'], gr = gradeOf(V.room, v), amb = gr.ambientTint, pt = mulHex(gr.petTint, amb), Hd = Hj(), o = HS.st(S());
      x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; x.clearRect(0, 0, W, H); x.imageSmoothingEnabled = false;
      const lay = (n, op, a) => { const i = L(n); if (!i) return; x.globalCompositeOperation = op || 'source-over'; x.globalAlpha = a == null ? 1 : a; if (i.width === W) x.drawImage(i, 0, 0); else x.drawImage(i, LX, LY); x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; V.stats.layers++; };
      lay('sky'); lay('far');
      for (const k of ['window', 'wall']) { const f = furnOf(k); if (f) drawFurn(x, f, slotAnchor(k), amb); }
      lay('mid');
      { const f = furnOf('rug'); if (f) drawFurn(x, f, slotAnchor('rug'), amb); }
      for (const k of ['bed', 'table', 'lamp']) { const f = furnOf(k); if (f && f.shadow) { const a = slotAnchor(k); shadowAt(x, a[0], a[1], f.shadow[0], f.shadow[1]); } }
      for (const k in PET) { const p = PET[k]; if (!vis(k)) { p.box = null; continue; } if (p.mode !== 'sleep' || !Z.bed) shadowAt(x, p.x + p.dx, p.y, k === 'kid' ? 18 : 20, 4); }
      for (const p of RS.values()) shadowAt(x, p.x + p.dx, p.y, p.kind === 'kid' ? 18 : 20, 4);
      const dv = decoNow(), dvI = dv && FAM.SV[dv] ? im('L:' + FAM.SV[dv].px) : null; if (dvI) shadowAt(x, FAM.DECO_ANCHOR[0], FAM.DECO_ANCHOR[1], 12, 3);
      const ys = []; for (const k of ['lamp', 'bed', 'table']) { const f = furnOf(k); if (f) { const a = slotAnchor(k); ys.push({ y: a[1], d: () => drawFurn(x, f, a, amb) }); if (k === 'bed' && f.front) ys.push({ y: a[1] + 0.1, d: () => drawFurn(x, f, a, amb, 'front') }); } }
      const bedY = furnOf('bed') ? slotAnchor('bed')[1] : 0;
      for (const k of ['tr', 'kid']) { const p = PET[k]; if (vis(k)) ys.push({ y: p.mode === 'sleep' && Z.bed ? bedY + (k === 'tr' ? 0.01 : 0.02) : p.y, d: () => drawPet(x, p, pt) }); }
      for (const p of RS.values()) ys.push({ y: p.y, d: () => { const HX = G.h5x; if (!(HX && HX.draw && HX.draw(x, p, pt, tinted))) drawPet(x, p, pt); if (HX && HX.post) HX.post(x, p, pt, tinted); V.stats.res++; if (p.km && p.box) { const cr = im('L:5a/ui/icon_crown@3x.png'); if (cr) { x.save(); x.imageSmoothingEnabled = true; x.drawImage(cr, Math.round((p.box[0] + p.box[2]) / 2) - 7, p.box[1] - 13 + Math.round(Math.sin(pnow() / 600)), 14, 14); x.restore(); V.stats.crown = (V.stats.crown | 0) + 1; } } } });   // 5a.1：主養細佬頭頂細皇冠
      if (dvI) { const S0 = FAM.SV[dv], a = FAM.DECO_ANCHOR; ys.push({ y: a[1], d: () => { x.drawImage(tinted(dvI, amb), Math.round(a[0] - S0.pv[0]), Math.round(a[1] - S0.pv[1])); V.stats.deco++; } }); }
      ys.sort((a, b) => a.y - b.y); for (const e of ys) e.d();
      if (Z.mode === 'sleep' && !Z.bed) { const I = SA.fxInfo('ov_blanket'); if (I && I.img) { const m = (PET.tr.x + PET.kid.x) / 2; x.drawImage(I.img, 0, 0, I.w, I.h, Math.round(m) - I.pv[0], Math.round(PET.tr.y + 1) - I.pv[1], I.w, I.h); } }
      lay('fore'); lay('lightmap', 'multiply'); lay('light_add', 'lighter'); lay('emissive_blur', 'lighter', gr.bloom ? gr.bloom.intensity : 0.4);
      { const f = furnOf('lamp'); if (f) { const a = slotAnchor('lamp'), ga = v === 'night' ? 1 : 0.35, e = im(f.emissive), gl = im(f.glow);
        x.globalCompositeOperation = 'lighter'; if (e) { x.globalAlpha = (gr.bloom ? gr.bloom.intensity : 0.4); x.drawImage(e, Math.round(a[0] - f.pivot[0]), Math.round(a[1] - f.pivot[1])); }
        if (gl) { x.globalAlpha = ga; const gc = f.glowCenter || [f.pivot[0], 10]; x.drawImage(gl, Math.round(a[0] - f.pivot[0] + gc[0] - gl.width / 2), Math.round(a[1] - f.pivot[1] + gc[1] - gl.height / 2)); V.stats.glow++; }
        x.globalCompositeOperation = 'source-over'; x.globalAlpha = 1; } }
      if (gr.fog) { x.globalAlpha = gr.fog.density; x.fillStyle = gr.fog.color; x.fillRect(0, 0, W, H); x.globalAlpha = 1; }
      lay('vignette');
    }
    function offCv(k) { let c = V.off[k]; if (!c) { c = V.off[k] = document.createElement('canvas'); c.width = W; c.height = H; } return c; }
    function render() {
      const x = V.ctx; if (!x || !A.ready) return; const tgt = night() ? 1 : 0; if (V.mix == null) V.mix = tgt;
      const dt = Math.min(0.1, (pnow() - (V.lastR || pnow())) / 1000); V.lastR = pnow(); V.mix += clamp(tgt - V.mix, -dt / 3, dt / 3);
      x.setTransform(1, 0, 0, 1, 0, 0); x.imageSmoothingEnabled = false; x.fillStyle = '#20182a'; x.fillRect(0, 0, V.cv.width, V.cv.height);
      const oy = Math.round(V.offY * KP);
      if (V.mix < 1) { const c = offCv('day'); composeRoom('day', c.getContext('2d')); x.drawImage(c, 0, 0, W, H, 0, oy, W * KP, H * KP); }
      if (V.mix > 0) { const c = offCv('night'); composeRoom('night', c.getContext('2d')); x.globalAlpha = V.mix; x.drawImage(c, 0, 0, W, H, 0, oy, W * KP, H * KP); x.globalAlpha = 1; }
      V.stats.variant = V.mix >= 0.5 ? 'night' : 'day';
      // fx（心心／zzz／哇）喺放大後畫（2x nearest）
      const now = pnow(), fx2 = (id, f, ax, ay) => { const I = SA.fxInfo(id); if (!I || !I.img) return false; x.drawImage(I.img, clamp(f, 0, I.n - 1) * I.w, 0, I.w, I.h, Math.round((ax - I.pv[0]) * KP), Math.round((ay - I.pv[1]) * KP + oy), I.w * KP, I.h * KP); return true; };
      for (const h of Z.hearts) { const u = (now - h.t0) / 900; x.globalAlpha = u > 0.7 ? 1 - (u - 0.7) / 0.3 : 1; fx2('fx_heart', u < 0.25 ? 0 : 1, h.x, h.y - u * 10); x.globalAlpha = 1; }
      { const fr = Math.floor(now / 300); for (const p of RS.values()) if (p.mode === 'sleep' && fx2('fx_zzz', (fr + (p.kind === 'kid' ? 2 : 1)) % 4, p.x + 6, p.y - (p.kind === 'kid' ? 30 : 26))) V.stats.zzz++; }
      if (Z.mode === 'sleep') { const fr = Math.floor(now / 300); for (const k of ['tr', 'kid']) { const p = PET[k]; if (vis(k) && p.mode === 'sleep' && fx2('fx_zzz', (fr + (k === 'kid' ? 2 : 0)) % 4, p.x + 6, p.y - (k === 'kid' ? 30 : 26))) V.stats.zzz++; } }
      if (Z.wah && now - Z.wah < 700 && Z.prank) { const v = PET[Z.prank.v]; x.save(); x.font = '900 16px sans-serif'; x.textAlign = 'center'; x.lineWidth = 4; x.strokeStyle = '#3a2440'; x.fillStyle = '#ffe9a8'; const yy = (v.y - 40) * KP + oy - (now - Z.wah) / 30; x.strokeText(HS.LINES.prank, v.x * KP, yy); x.fillText(HS.LINES.prank, v.x * KP, yy); x.restore(); }
      V.stats.frames++;
    }
    function loop() {
      if (!V.open) { V.raf = 0; return; } V.raf = requestAnimationFrame(loop); const t = pnow(), dt = Math.min(0.1, (t - (V.last || t)) / 1000); V.last = t;
      if (V.offT0) { const u = clamp((t - V.offT0) / 300, 0, 1), e = 1 + 2.70158 * Math.pow(u - 1, 3) + 1.70158 * Math.pow(u - 1, 2); V.offY = V.offFrom + (V.offTo - V.offFrom) * (V.offTo < V.offFrom ? e : u); if (u >= 1) { V.offT0 = 0; V.offY = V.offTo; } placePins(); }
      try { behave(dt); render(); } catch (e) { note('err', { e: String(e && e.message || e) }); }
      if (V.deco && V.chip) V.chip.textContent = String(wallet());
      if (FAM && t - (V.h5T || 0) > 300) { V.h5T = t; try { hud5(); } catch (e) { note('err', { e: String(e && e.message || e) }); } }
    }

    // ── DOM ──
    const CREAM = '#FFF3D6', OL = 'text-shadow:-1px -1px 0 #2a1d3a,1px -1px 0 #2a1d3a,-1px 1px 0 #2a1d3a,1px 1px 0 #2a1d3a,0 2px 0 #2a1d3a;';
    const css = document.createElement('style');
    css.textContent = 'body.s2-house #modal{z-index:60!important}body.s2-house #toast{z-index:61!important}body.s2-house #bubble{z-index:61!important}body.s2-house #s12gain{z-index:61!important}body.s2-house #devBtn{z-index:62!important}' +
      '#s2houseV .hb{position:absolute;cursor:pointer;-webkit-tap-highlight-color:transparent}#s2houseV .hb:active{filter:brightness(1.12)}' +
      '#s2houseV .ttl{position:absolute;height:30px;box-sizing:border-box;border-radius:15px;background:linear-gradient(#a99af0,#7b69d0);border:2px solid #e8c77a;box-shadow:0 2px 0 #3b2c66,0 0 0 2px #3b2c66;color:#fff;font:900 16px/26px serif;text-align:center;letter-spacing:2px;' + OL + 'pointer-events:none}' +
      '#s2houseV .lbl{position:absolute;transform:translateX(-50%);font:700 11px/14px sans-serif;color:' + CREAM + ';white-space:nowrap;' + OL + 'pointer-events:none}' +
      '#s2houseV .card{position:absolute;width:108px;height:132px;box-sizing:border-box;border-radius:10px;background:linear-gradient(#2f3566,#232850);border:2px solid #c9a35e;box-shadow:inset 0 0 0 2px #1a1d3d;overflow:hidden;cursor:pointer}' +
      '#s2houseV .card[data-state=equipped]{border-color:#ffd977;box-shadow:inset 0 0 0 2px #1a1d3d,0 0 10px #ffd97799}#s2houseV .card[data-state=locked]{background:linear-gradient(#45465a,#33344a);border-color:#7d7c8c}' +
      '#s2houseV .card .nm{position:absolute;left:0;right:0;top:84px;text-align:center;font:700 12px/16px sans-serif;color:' + CREAM + ';' + OL + '}' +
      '#s2houseV .card .pill{position:absolute;left:8px;right:8px;top:102px;height:22px;border-radius:11px;font:800 12px/22px sans-serif;text-align:center;color:#4a2a10;background:linear-gradient(#ffd08a,#f3a54e);border:1px solid #7a4a1c}' +
      '#s2houseV .card[data-state=equipped] .pill{background:linear-gradient(#a6f0e6,#5fc6bb);color:#163c3c;border-color:#1f5c58}#s2houseV .card .pill.poor{filter:grayscale(1) brightness(.85)}#s2houseV .card[data-state=locked] .pill{background:#5a5a6a;color:#ddd;border-color:#2a2a3a;font-size:10px}' +
      '#s2houseV .card[data-clear] .pill{background:linear-gradient(#3d4478,#2b3060);color:' + CREAM + ';border-color:#c9a35e}' +
      '#s2houseV .gem{position:absolute;right:5px;top:5px;width:8px;height:8px;transform:rotate(45deg);background:#ff7fa8;border:1px solid #fff}#s2houseV .rd{position:absolute;right:-2px;top:-4px;width:12px;height:12px;border-radius:50%;background:#ff4d5e;border:2px solid #fff}' +
      '#s2houseV .h5b{cursor:pointer;-webkit-tap-highlight-color:transparent}#s2houseV .h5b:active{filter:brightness(1.12)}#s2houseV .h5b[data-locked="1"]{filter:saturate(.7)}' +
      '#s2houseV .h5chip{box-sizing:border-box;border-radius:13px;background:#262b55;border:2px solid #c9a35e}' +
      '#s2houseV .svrow{position:absolute;display:flex;gap:8px;overflow-x:auto;overflow-y:hidden;pointer-events:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}#s2houseV .svrow::-webkit-scrollbar{display:none}' +
      '#s2houseV .svrow .card.svc{position:relative !important;left:auto !important;top:auto !important;flex:0 0 auto}' +
      '#s2houseV .card[data-state=elsewhere] .pill{background:linear-gradient(#cfc4ff,#9c8ce6);color:#2a1d4a;border-color:#4a3a8a;font-size:11px}' +
      '#s2houseV .tab5{border-radius:50%;background:radial-gradient(#3d4478,#262b55);border:3px solid #c9a35e;box-sizing:border-box}#s2houseV .tab5[data-sel="1"]{border-color:#ffd977;box-shadow:0 0 8px #ffd977}' +
      '#s2house .rd{position:absolute;left:calc(50% + 10px);top:calc(50% - 24px);width:12px;height:12px;border-radius:50%;background:#ff4d5e;border:2px solid #fff;pointer-events:none}';
    document.head.appendChild(css);
    const AP = (n) => n * KP;   // art → ui px
    function hb(id, f, cx, cy, w, h, onClick) { const e = document.createElement('div'); e.className = 'hb'; e.dataset.testid = id; e.style.cssText = 'left:' + (AP(cx) - w / 2) + 'px;top:' + (AP(cy) - h / 2) + 'px;width:' + w + 'px;height:' + h + 'px';
      if (f) e.appendChild(mkImg(f, 'left:0;top:0;width:100%;height:100%')); e.addEventListener('click', (ev) => { ev.stopPropagation(); onClick(ev); }); return e; }
    function build() {
      const host = document.getElementById('ui') || document.body; const el = V.el = document.createElement('div'); el.id = 's2houseV'; el.dataset.testid = 'house-view';
      el.style.cssText = 'position:absolute;left:0;top:0;width:390px;height:844px;z-index:50;background:#20182a;overflow:hidden;display:none;touch-action:none;user-select:none';
      const cv = V.cv = document.createElement('canvas'); cv.width = W * KP; cv.height = H * KP; cv.dataset.testid = 'house-canvas'; cv.style.cssText = 'position:absolute;left:0;top:0;width:390px;height:844px;image-rendering:pixelated'; el.appendChild(cv); V.ctx = cv.getContext('2d');
      // 平時 HUD
      const hud = V.hud = document.createElement('div'); hud.style.cssText = 'position:absolute;inset:0;pointer-events:none'; el.appendChild(hud);
      const L = Hj().ui, hh = L.houseHud;
      const back = hb('house-back', 'ui/btn_back@3x.png', hh.back.cx, hh.back.cy, 60, 60, () => close('back')); back.style.pointerEvents = 'auto'; hud.appendChild(back);
      const tt = document.createElement('div'); tt.className = 'ttl'; tt.dataset.testid = 'house-title'; tt.textContent = hh.title.label; V.title = tt; tt.style.cssText = 'left:' + (AP(hh.title.cx) - 80) + 'px;top:' + AP(hh.title.y) + 'px;width:160px'; hud.appendChild(tt);
      const dc = L.decorate ? hh.decorate : null; const de = document.createElement('div'); de.className = 'hb'; de.dataset.testid = 'house-decorate'; de.style.cssText = 'left:' + AP(dc.cx - 20) + 'px;top:' + AP(dc.cy - 15) + 'px;width:80px;height:83px;pointer-events:auto';
      de.appendChild(mkImg('ui/btn_decorate@3x.png', 'left:0;top:0;width:80px;height:83px')); de.addEventListener('click', (e) => { e.stopPropagation(); decorate(true); }); hud.appendChild(de);
      if (FAM) buildHud5(hud);
      const hint = document.createElement('div'); hint.dataset.testid = 'house-hint'; hint.style.cssText = (FAM ? 'position:absolute;left:0;right:0;text-align:center;top:744px;' : 'position:absolute;left:16px;top:800px;') + 'font:700 11px/14px sans-serif;color:' + CREAM + ';opacity:.85;' + OL; hud.appendChild(hint); V.hint = hint;
      // 佈置
      const dk = V.dk = document.createElement('div'); dk.style.cssText = 'position:absolute;inset:0;display:none'; el.appendChild(dk); const DL = L.decorate;
      const pinsL = document.createElement('div'); pinsL.style.cssText = 'position:absolute;inset:0'; dk.appendChild(pinsL);
      for (const k of HS.SLOTS) { const e = document.createElement('div'); e.className = 'hb'; e.dataset.testid = 'house-pin-' + k; e.addEventListener('click', (ev) => { ev.stopPropagation(); selTab(k); UIS('tap'); }); pinsL.appendChild(e); V.pins[k] = e; }
      const sh = document.createElement('div'); sh.dataset.testid = 'house-sheet'; sh.style.cssText = 'position:absolute;left:' + AP(DL.sheet.x - 6.5) + 'px;top:' + AP(DL.sheet.y - 6) + 'px;width:400px;height:300px'; sh.appendChild(mkImg('ui/sheet_panel@3x.png', 'left:0;top:0;width:400px;height:300px')); dk.appendChild(sh);
      DL.tabs.order.forEach((k, i) => { const e = document.createElement('div'); e.className = 'hb'; e.dataset.testid = 'house-tab-' + k; e.style.cssText = 'left:' + (AP(DL.tabs.cx[i]) - 34) + 'px;top:' + (AP(DL.tabs.cy) - 34) + 'px;width:68px;height:68px';
        e._i = mkImg('ui/tab_' + k + '_idle@3x.png', 'left:0;top:0;width:68px;height:68px'); e._s = mkImg('ui/tab_' + k + '_sel@3x.png', 'left:0;top:0;width:68px;height:68px'); e.appendChild(e._i); e.appendChild(e._s);
        const lb = document.createElement('div'); lb.className = 'lbl'; lb.style.cssText = 'left:34px;top:' + (AP(DL.tabs.labelY) - AP(DL.tabs.cy) + 34 - 7) + 'px'; lb.textContent = HS.SLOT_ZH[k]; e.appendChild(lb);
        e.addEventListener('click', (ev) => { ev.stopPropagation(); selTab(k); UIS('tap'); }); dk.appendChild(e); V.tabs[k] = e; });
      if (FAM) { /* 5a 第 7 個 tab「擺設」（手信） */ const cx = DL.tabs.cx, x7 = Math.min(188, cx[cx.length - 1] + (cx[cx.length - 1] - cx[cx.length - 2]) * 0.8), e = document.createElement('div'); e.className = 'hb tab5'; e.dataset.testid = 'house-tab-deco';
        e.style.cssText = 'left:' + (AP(x7) - 26) + 'px;top:' + (AP(DL.tabs.cy) - 26) + 'px;width:52px;height:52px'; e._i = mkImg('L:' + FAM.SOUV[0].icon, 'left:8px;top:8px;width:30px;height:30px'); e._s = e._i; e.appendChild(e._i);
        const lb = document.createElement('div'); lb.className = 'lbl'; lb.style.cssText = 'left:26px;top:' + (AP(DL.tabs.labelY) - AP(DL.tabs.cy) + 26 - 7) + 'px'; lb.textContent = FAM.DECO_ZH; e.appendChild(lb);
        e.addEventListener('click', (ev) => { ev.stopPropagation(); selTab('deco'); UIS('tap'); }); dk.appendChild(e); V.tabs.deco = e;
        const pe = document.createElement('div'); pe.className = 'hb'; pe.dataset.testid = 'house-pin-deco'; pe.addEventListener('click', (ev) => { ev.stopPropagation(); selTab('deco'); UIS('tap'); }); pinsL.appendChild(pe); V.pins.deco = pe; }
      const tr = document.createElement('div'); tr.dataset.testid = 'house-tabtitle'; tr.style.cssText = 'position:absolute;left:' + AP(DL.titleRow.x) + 'px;top:' + (AP(DL.titleRow.y) - 9) + 'px;font:900 13px/16px sans-serif;color:#ffd977;' + OL; dk.appendChild(tr); V.tabT = tr;
      const tr2 = document.createElement('div'); tr2.style.cssText = 'position:absolute;right:' + (390 - AP(DL.titleRow.hintX)) + 'px;top:' + (AP(DL.titleRow.y) - 8) + 'px;font:700 10px/14px sans-serif;color:' + CREAM + ';opacity:.9;' + OL; tr2.textContent = '撳一下就擺，換擺唔使碎'; dk.appendChild(tr2);
      const cards = V.cards = document.createElement('div'); cards.style.cssText = 'position:absolute;inset:0;pointer-events:none'; dk.appendChild(cards);
      const done = hb('house-done', 'ui/btn_done@3x.png', DL.done.x + DL.done.w / 2, DL.done.y + DL.done.h / 2, 160, 48, () => decorate(false)); dk.appendChild(done);
      const tb = DL.topBar, b2 = hb('house-deco-back', 'ui/btn_back@3x.png', tb.back.cx, tb.back.cy, 60, 60, () => decorate(false)); dk.appendChild(b2);
      const t2 = document.createElement('div'); t2.className = 'ttl'; t2.textContent = tb.title.label; V.dtt = t2; V.dtt0 = tb.title.label; t2.style.cssText = 'left:' + (AP(tb.title.cx) - 90) + 'px;top:' + AP(tb.title.y) + 'px;width:180px'; dk.appendChild(t2);
      const ch = document.createElement('div'); ch.dataset.testid = 'house-chip'; ch.style.cssText = 'position:absolute;left:' + (AP(tb.chip.x) + 4) + 'px;top:' + (AP(tb.chip.y) + 6) + 'px;width:76px;height:28px;box-sizing:border-box;padding-left:30px;border-radius:14px;background:#262b55;border:2px solid #c9a35e;font:800 13px/24px sans-serif;color:' + CREAM + ';' + OL;
      const st = document.createElement('span'); st.textContent = '★'; st.style.cssText = 'position:absolute;left:6px;top:0;color:#ffd24a;font-size:18px'; ch.appendChild(st); const n = document.createElement('span'); ch.appendChild(n); V.chip = n; dk.appendChild(ch);
      cv.addEventListener('pointerdown', onDown); host.appendChild(el);
    }
    /* 5a HUD（遊美 5a/ui/layout.json houseHud；1 art px ＝ 2 CSS px） */
    const H5 = {};
    function el5(tag, id, css, txt) { const e = document.createElement(tag || 'div'); if (id) e.dataset.testid = id; e.style.cssText = css || ''; if (txt != null) e.textContent = txt; return e; }
    function buildHud5(hud) {
      const L = (n) => 'L:5a/ui/' + n + '@3x.png';
      const fam = H5.fam = el5('div', 'house-fam', 'position:absolute;left:272px;top:18px;width:108px;height:34px;pointer-events:auto;cursor:pointer'); fam.className = 'h5b h5chip';
      fam.appendChild(mkImg(L('icon_family_level'), 'left:-6px;top:-4px;width:40px;height:40px;z-index:2')); H5.famLv = el5('b', 'house-fam-lv', 'position:absolute;left:34px;top:2px;font:900 14px/16px sans-serif;color:#FFE08A'); fam.appendChild(H5.famLv);
      H5.famBar = el5('i', 'house-fam-bar', 'position:absolute;left:34px;top:21px;width:68px;height:8px;background:#1d1838;border-radius:4px;overflow:hidden'); H5.famFill = el5('i', null, 'position:absolute;left:0;top:0;bottom:0;width:0;background:linear-gradient(#ffe9a8,#f3b54e)'); H5.famBar.appendChild(H5.famFill); fam.appendChild(H5.famBar);
      fam.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); if (G.l5 && G.l5.tree) G.l5.tree(); }); hud.appendChild(fam);
      H5.dots = el5('div', 'house-dots', 'position:absolute;left:0;width:390px;top:56px;height:8px;text-align:center;pointer-events:none;font-size:0'); hud.appendChild(H5.dots);
      const arrow = (side, cx) => { const e = el5('div', 'house-room-' + side, 'position:absolute;left:' + (cx * 2 - 22) + 'px;top:' + (214 * 2 - 22) + 'px;width:44px;height:44px;pointer-events:auto;cursor:pointer'); e.className = 'h5b h5arrow';
        e._i = mkImg(L('btn_room_' + side + '_idle'), 'left:0;top:0;width:44px;height:44px'); e._l = mkImg(L('btn_room_' + side + '_locked'), 'left:0;top:0;width:44px;height:44px'); e.appendChild(e._i); e.appendChild(e._l);
        e.addEventListener('click', (ev) => { ev.stopPropagation(); stepRoom(side === 'l' ? -1 : 1); }); hud.appendChild(e); return e; };
      H5.l = arrow('l', 11); H5.r = arrow('r', 184);
      const cap = H5.cap = el5('div', 'house-cap', 'position:absolute;left:12px;top:66px;width:84px;height:26px;pointer-events:none'); cap.className = 'h5chip';
      cap.appendChild(mkImg(L('icon_pets'), 'left:-4px;top:-4px;width:32px;height:32px;z-index:2')); H5.capT = el5('b', null, 'position:absolute;left:30px;top:4px;font:800 13px/18px sans-serif;color:#FFF3D6'); cap.appendChild(H5.capT); hud.appendChild(cap);
      const tr = H5.tree = el5('div', 'house-tree', 'position:absolute;left:' + (23 * 2 - 44) + 'px;top:' + (392 * 2 - 42) + 'px;width:88px;height:83px;pointer-events:auto;cursor:pointer'); tr.className = 'h5b';
      tr.appendChild(mkImg(L('btn_tree'), 'left:0;top:0;width:88px;height:83px')); tr.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); if (G.l5 && G.l5.tree) G.l5.tree(); }); hud.appendChild(tr);
    }
    function hud5() {
      if (!FAM || !H5.fam || !V.open) return; const s = S(), info = FAM.lvInfo(s), rooms = FAM.ROOMS, i = rooms.indexOf(V.room);
      if (G.l5bHud) try { G.l5bHud(V.hud, V.room); } catch (e) { }   /* 5b：「今日安排」掣 */
      V.title.textContent = FAM.ROOM[V.room].zh; H5.famLv.textContent = 'Lv' + info.lv + (info.max ? ' MAX' : ''); H5.famFill.style.width = Math.round(info.pct * 100) + '%'; H5.fam.dataset.lv = String(info.lv); H5.fam.dataset.max = info.max ? '1' : '0';
      const n = FAM.count(s, V.room); H5.capT.textContent = n + '/' + FAM.CAP + ' 隻'; H5.cap.dataset.n = String(n);
      const dk = rooms.map(k => (k === V.room ? 'cur' : FAM.roomOpen(s, k) ? 'open' : 'locked')).join(); if (H5.dots._k !== dk) { H5.dots._k = dk; H5.dots.innerHTML = '';
        rooms.forEach((k) => { const st = k === V.room ? 'cur' : FAM.roomOpen(s, k) ? 'open' : 'locked', d = el5('i', 'house-dot-' + k, 'display:inline-block;position:relative;width:' + (st === 'cur' ? 10 : 8) + 'px;height:' + (st === 'cur' ? 10 : 8) + 'px;margin:0 3px;vertical-align:middle'); d.dataset.state = st;
          d.appendChild(mkImg('L:5a/ui/dot_room_' + st + '@3x.png', 'left:0;top:0;width:100%;height:100%')); H5.dots.appendChild(d); }); }
      for (const [e, j] of [[H5.l, i - 1], [H5.r, i + 1]]) { const k = rooms[j], show = !!k, lock = show && !FAM.roomOpen(s, k); e.style.display = show ? '' : 'none'; e.dataset.locked = lock ? '1' : '0'; e._i.style.display = lock ? 'none' : ''; e._l.style.display = lock ? '' : 'none'; }
    }
    function stepRoom(d) { const rooms = FAM.ROOMS, k = rooms[rooms.indexOf(V.room) + d]; if (!k) return false; return goRoom(k); }
    function goRoom(k, quiet) {
      if (!FAM || !FAM.ROOMS.includes(k)) return false; const s = S();
      if (!FAM.roomOpen(s, k)) { UI.toast('家族 Lv' + FAM.ROOM[k].lv + ' 開', 1800); UIS('tap'); note('roomLocked', { k }); return false; }
      if (k === V.room) return true; UIS('tap');
      return loadRoom(k).then((ok) => { if (!ok || !V.open) return false; V.room = k; Z.greet = null; syncRes(true); if (k === 'room1') free(); else Z.mode = 'free'; V.mix = null; hud5(); if (V.deco) { fillCards(); placePins(); }
        if (V.cv) V.cv.animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: 260 }); note('room', { k }); if (!quiet && G.l5 && G.l5.onRoom) G.l5.onRoom(k); return true; });
    }
    const wallet = () => (X && X.st ? X.st(S()).wallet.total : 0);
    function placePins() {
      if (!V.deco || !A.ready) return; const DL = Hj().ui.decorate, o = HS.st(S());
      const sl = slotsNow(), K7 = FAM ? HS.SLOTS.concat(['deco']) : HS.SLOTS; void o;
      for (const k of K7) { const e = V.pins[k]; if (!e) continue; const p = k === 'deco' ? FAM.DECO_PIN : Hj().slots[k].pin, sel = V.sel === k, d = sel ? 56 : 46, filled = k === 'deco' ? !!decoNow() : !!sl[k], bob = sel ? Math.round(Math.sin(pnow() / 160) * 2) : 0;
        e.style.cssText = 'left:' + (AP(p[0]) - d / 2) + 'px;top:' + (AP(p[1] + V.offY) - d / 2 + bob) + 'px;width:' + d + 'px;height:' + d + 'px;' + (sel ? 'filter:drop-shadow(0 0 6px #ffd977)' : '');
        const key = (filled ? 'f' : 'p') + (sel ? 's' : 'i'); if (e._k !== key) { e._k = key; e.dataset.filled = filled ? '1' : '0'; e.dataset.sel = sel ? '1' : '0'; e.innerHTML = '';
          e.appendChild(mkImg('ui/pin_' + (filled ? 'filled' : 'plus') + '_' + (sel ? 'sel' : 'idle') + '@3x.png', 'left:0;top:0;width:100%;height:100%')); if (filled) e.appendChild(mkImg(k === 'deco' ? 'L:' + FAM.SV[decoNow()].icon : 'ui/icon_' + k + '@3x.png', 'left:22%;top:22%;width:56%;height:56%')); } }
      void DL;
    }
    function selTab(k) { V.sel = k; for (const t in V.tabs) { const e = V.tabs[t], s = t === k; if (e._i !== e._s) { e._i.style.display = s ? 'none' : ''; e._s.style.display = s ? '' : 'none'; } e.dataset.sel = s ? '1' : '0'; } fillCards(); placePins(); note('tab', { k }); }
    function thumb(id) { const f = Hj().furniture[id], i = A.img[f.png], c = document.createElement('canvas'); c.width = 92; c.height = 60; c.style.cssText = 'position:absolute;left:8px;top:10px;width:92px;height:60px;image-rendering:pixelated';
      if (!f.png) { c.dataset.ph = f.placeholder || ('house:' + id); c.style.outline = '2px dashed #ff00ff'; c.style.outlineOffset = '-2px'; const g = c.getContext('2d'); g.fillStyle = 'rgba(255,0,255,0.14)'; g.fillRect(0, 0, 92, 60); g.fillStyle = '#c000c0'; g.font = '12px sans-serif'; g.textAlign = 'center'; g.fillText((f.size || []).join('×'), 46, 34); return c; }
      if (i) { const g = c.getContext('2d'); g.imageSmoothingEnabled = false; const s = Math.max(1, Math.floor(Math.min(92 / i.width, 60 / i.height))) * (i.width * 2 <= 92 && i.height * 2 <= 60 ? 1 : 1); const sc = Math.min(s, Math.max(0.5, Math.min(92 / i.width, 60 / i.height)));
        const w = Math.round(i.width * sc), h = Math.round(i.height * sc); g.drawImage(i, Math.round((92 - w) / 2), Math.round((60 - h) / 2), w, h); if (f.front && A.img[f.front]) g.drawImage(A.img[f.front], Math.round((92 - w) / 2), Math.round((60 - h) / 2), w, h); }
      return c; }
    function fillCards() {
      const box = V.cards; if (!box) return; box.innerHTML = ''; if (V.sel === 'deco') return fillDeco(box); const DL = Hj().ui.decorate, k = V.sel, ids = HS.IDS.filter(i => HS.FURN[i].slot === k), o = HS.st(S()), wl = wallet();
      V.tabT.textContent = HS.SLOT_ZH[k] + '・' + ids.length + ' 件';
      /* 6b.1：一個擺位多過 2 件（牆＋散步鞋架）→ 同擺設 tab 一樣用橫向捲動行（唔縮細卡） */
      const many = ids.length + 1 > DL.cards.x.length; let row = null;
      if (many) { row = document.createElement('div'); row.className = 'svrow'; row.dataset.testid = 'house-slotrow'; row.style.left = AP(DL.cards.x[0]) + 'px'; row.style.top = AP(DL.cards.y) + 'px'; row.style.width = (AP(DL.cards.x[2]) - AP(DL.cards.x[0]) + 108 + 8) + 'px'; row.style.height = '140px'; box.appendChild(row); }
      ids.concat(['__clear']).forEach((id, i) => { const e = document.createElement('div'); e.className = many ? 'card svc' : 'card'; if (!many) { e.style.left = AP(DL.cards.x[i]) + 'px'; e.style.top = AP(DL.cards.y) + 'px'; } e.style.pointerEvents = 'auto';
        const nm = document.createElement('div'), pill = document.createElement('div'); nm.className = 'nm'; pill.className = 'pill';
        if (id === '__clear') { e.dataset.testid = 'house-card-clear'; e.dataset.clear = '1'; e.appendChild(mkImg('ui/icon_clear@3x.png', 'left:24px;top:10px;width:60px;height:60px')); nm.textContent = '收起'; pill.textContent = '清空'; pill.dataset.testid = 'house-pill-clear'; }
        else { const f = HS.FURN[id], stt = cstate(id); e.dataset.testid = 'house-card-' + id; e.dataset.state = stt; const th = thumb(id); if (stt === 'locked') th.style.filter = 'brightness(0) opacity(.35)'; e.appendChild(th); nm.textContent = f.zh; pill.dataset.testid = 'house-pill-' + id;
          if (stt === 'equipped') { pill.textContent = '擺緊'; const gm = document.createElement('div'); gm.className = 'gem'; e.appendChild(gm); }
          else if (stt === 'owned') pill.textContent = '擺上去';
          else if (stt === 'elsewhere') { const w = FAM.whereIs(S(), id); pill.textContent = '喺' + (w ? FAM.ROOM[w].zh : '第二間'); e.dataset.where = w || ''; }
          else if (stt === 'buy') { pill.textContent = '★ ' + f.price; if (wl < f.price) pill.classList.add('poor'); }
          else { pill.textContent = f.src === 'commission' ? '委託獎' : '訪客禮'; e.appendChild(mkImg('ui/icon_lock@3x.png', 'left:36px;top:18px;width:36px;height:36px')); } }
        e.appendChild(nm); e.appendChild(pill); e.addEventListener('click', (ev) => { ev.stopPropagation(); cardTap(id); }); (row || box).appendChild(e); });
    }
    const cstate = (id) => (FAM ? FAM.cardState(S(), V.room, id) : HS.cardState(S(), id));
    function svThumb(sv) { const i = A.img['L:' + sv.px], c = document.createElement('canvas'); c.width = 92; c.height = 60; c.style.cssText = 'position:absolute;left:8px;top:10px;width:92px;height:60px;image-rendering:pixelated';
      if (i) { const g = c.getContext('2d'); g.imageSmoothingEnabled = false; const sc = Math.max(1, Math.floor(Math.min(84 / i.width, 54 / i.height))); g.drawImage(i, Math.round((92 - i.width * sc) / 2), Math.round((60 - i.height * sc) / 2), i.width * sc, i.height * sc); } return c; }
    function fillDeco(box) {   /* 擺設：收起＋10 件手信（有＝擺；冇＝上鎖：開房／遠足手信） */
      const DL = Hj().ui.decorate, o = FAM.st(S()), n = FAM.SOUV.filter(x => o.sv[x.id]).length; V.tabT.textContent = FAM.DECO_ZH + '・' + n + '／' + FAM.SOUV.length + ' 件';
      const row = document.createElement('div'); row.className = 'svrow'; row.dataset.testid = 'house-svrow'; row.style.left = AP(DL.cards.x[0]) + 'px'; row.style.top = AP(DL.cards.y) + 'px'; row.style.width = (AP(DL.cards.x[2]) - AP(DL.cards.x[0]) + 108 + 8) + 'px'; row.style.height = '140px'; box.appendChild(row);
      const list = ['__clear'].concat(FAM.SOUV.map(x => x.id).sort((a, b) => (o.sv[b] ? 1 : 0) - (o.sv[a] ? 1 : 0)));
      for (const id of list) { const e = document.createElement('div'); e.className = 'card svc'; const nm = document.createElement('div'), pill = document.createElement('div'); nm.className = 'nm'; pill.className = 'pill';
        if (id === '__clear') { e.dataset.testid = 'house-card-clear'; e.dataset.clear = '1'; e.appendChild(mkImg('ui/icon_clear@3x.png', 'left:24px;top:10px;width:60px;height:60px')); nm.textContent = '收起'; pill.textContent = '清空'; }
        else { const sv = FAM.SV[id], stt = FAM.cardState(S(), V.room, id); e.dataset.testid = 'house-card-' + id; e.dataset.state = stt; const th = svThumb(sv); if (stt === 'locked') th.style.filter = 'brightness(0) opacity(.35)'; e.appendChild(th); nm.textContent = sv.zh;
          if (stt === 'equipped') { pill.textContent = '擺緊'; const gm = document.createElement('div'); gm.className = 'gem'; e.appendChild(gm); } else if (stt === 'owned') pill.textContent = '擺上去';
          else if (stt === 'elsewhere') { const w = FAM.whereIs(S(), id); pill.textContent = '喺' + FAM.ROOM[w].zh; } else pill.textContent = '手信'; }
        e.appendChild(nm); e.appendChild(pill); e.addEventListener('click', (ev) => { ev.stopPropagation(); cardTap(id); }); row.appendChild(e); }
    }
    function firstToast(r) { if (r && r.first) { UI.toast(r.mood ? HS.LINES.firstMood : HS.LINES.firstCap, 2400); SND('reward'); } }
    const zhOf = (id) => (FAM && FAM.SV[id] ? FAM.SV[id].zh : HS.FURN[id].zh), slotZh = (k) => (k === 'deco' ? FAM.DECO_ZH : HS.SLOT_ZH[k]);
    function doPlace(slot, id) { const r = FAM ? FAM.place(S(), V.room, slot, id, nowMs(), store) : HS.place(S(), slot, id, nowMs(), store); if (r.ok) { firstToast(r); if (!r.first) UI.toast(id ? '擺好「' + zhOf(id) + '」' + (r.from ? '（由' + FAM.ROOM[r.from].zh + '搬過嚟）' : '') : '收起咗' + slotZh(slot), 1600); UIS('tap'); save(); fillCards(); placePins(); if (Z.mode === 'sleep') startSleep(true); } note('place', { slot, id, ok: r.ok, first: !!r.first }); return r; }
    function cardTap(id) {
      const k = V.sel; if (id === '__clear') return doPlace(k, null);
      if (FAM && FAM.SV[id]) { const st5 = FAM.cardState(S(), V.room, id); if (st5 === 'equipped') { UI.toast('擺緊「' + FAM.SV[id].zh + '」', 1400); return null; } if (st5 === 'locked') { UI.toast(FAM.SV[id].zh + '：開新房送／遠足手信（5b）', 2400); UIS('tap'); return null; } return doPlace('deco', id); }
      const stt = cstate(id), f = HS.FURN[id];
      if (stt === 'equipped') { UI.toast('擺緊「' + f.zh + '」', 1400); return null; }
      if (stt === 'owned' || stt === 'elsewhere') return doPlace(k, id);
      if (stt === 'locked') { const left = f.src === 'commission' ? '（仲差 ' + HS.commissionLeft(S(), id) + ' 張委託）' : ''; UI.toast(f.zh + '：' + HS.SRC_ZH(id).replace(/（.*）/, '') + left, 2600); UIS('tap'); return null; }
      if (wallet() < f.price) { UI.toast(HS.LINES.poor + '（要 ' + f.price + '，有 ' + wallet() + '）', 2000); UIS('tap'); return null; }
      return buyAsk(id);
    }
    function buyAsk(id) {
      const f = HS.FURN[id], node = document.createElement('div'); node.dataset.testid = 'house-buy'; node.style.cssText = 'text-align:center;font-size:13px;line-height:1.7';
      node.textContent = '用 ' + f.price + ' 碎買「' + f.zh + '」？（而家有 ' + wallet() + ' 碎）';
      UI.modal({ title: '買家具', kind: 'houseBuy', node, buttons: [{ text: '買', primary: true, onClick: () => { const r = HS.buy(S(), id, X.spend, nowMs()); if (r.ok) { UI.toast(fmt(HS.LINES.bought, { name: r.name }), 1800); UIS('toast', { currency: true }); SND('reward'); save(); setTimeout(() => doPlace(f.slot, id), 300); } else UI.toast(HS.LINES.poor, 1600); note('buy', { id, ok: r.ok }); fillCards(); } }, { text: '唔買' }] });
      UIS('popupOpen'); return true;
    }
    function decorate(on) {
      if (on && V.dtt && FAM && FAM.ROOM && FAM.ROOM[V.room]) V.dtt.textContent = (V.room === 'room1' ? V.dtt0 : FAM.ROOM[V.room].zh);
      if (!V.open) return false; on = !!on; if (V.deco === on) return true; V.deco = on; V.dk.style.display = on ? '' : 'none'; V.hud.style.display = on ? 'none' : '';
      V.offFrom = V.offY; V.offTo = on ? Hj().ui.decorate.roomOffsetY : 0; V.offT0 = pnow(); if (on) { selTab(V.sel || 'bed'); V.chip.textContent = String(wallet()); }
      UIS('tap'); note('decorate', { on }); return true;
    }
    // ── 撳寵物 ──
    function artAt(ev) { const r = V.cv.getBoundingClientRect(); return { x: (ev.clientX - r.left) / r.width * W, y: (ev.clientY - r.top) / r.height * H - V.offY }; }
    const inB = (a, b) => b && a.x >= b[0] - 3 && a.x <= b[2] + 3 && a.y >= b[1] - 3 && a.y <= b[3] + 3;
    function onDown(ev) {
      if (V.deco) return; const a = artAt(ev);
      if (FAM) { const hit = [...RS.values()].filter(p => inB(a, p.box)).sort((p, q) => q.y - p.y)[0]; if (hit && !(vis('kid') && inB(a, PET.kid.box)) && !(vis('tr') && inB(a, PET.tr.box) && PET.tr.y > hit.y)) { hit.hop = 400; UIS('tap'); note('resTap', { id: hit.id }); if (G.l5 && G.l5.card) G.l5.card(hit.id); return; } }
      if (vis('kid') && inB(a, PET.kid.box)) { PET.kid.hop = 400; Z.hearts.push({ x: PET.kid.x, y: PET.kid.y - 36, t0: pnow() }); UIS('tap'); note('kidTap'); return; }
      if (vis('tr') && inB(a, PET.tr.box) && G.tch) { G.tch.down(ev.clientX, ev.clientY); const id = ev.pointerId;
        const mv = (e) => { if (e.pointerId === id) G.tch.move(e.clientX, e.clientY); }, up = (e) => { if (e.pointerId !== id) return; window.removeEventListener('pointermove', mv); window.removeEventListener('pointerup', up); window.removeEventListener('pointercancel', up); G.tch.up(e.clientX, e.clientY, e.type === 'pointercancel'); };
        window.addEventListener('pointermove', mv); window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up); note('trTouch'); }
    }

    // ── 開／關 ──
    function open(from) {
      if (!A.ready) { UI.toast('屋仔載入緊…', 1200); return false; }
      if (!HS.unlocked(S())) { UI.toast(HS.LINES.locked, 2400); UIS('tap'); note('lockedTap', { from }); return false; }
      if (!V.el) build(); const r = HS.enter(S(), nowMs(), store); save();
      V.open = true; G.houseIsOpen = true; V.from = from || 'rail'; V.el.style.display = ''; document.body.classList.add('s2-house'); V.mix = null; V.last = 0; V.lastR = 0;
      if (V.deco) decorate(false); if (V.room !== 'room1' && !(FAM && FAM.roomOpen(S(), V.room))) V.room = 'room1'; Z.greet = null; syncRes(true); free(); PET.tr.x = 78; PET.tr.y = 300; PET.kid.x = 112; PET.kid.y = 302; Z.nextDuo = pnow() + rnd(6, 12) * 1000;
      if (r.fresh || (r.welcome && r.welcome.first)) { UI.toast(HS.LINES.welcome, 2600); setTimeout(() => firstToast(r.welcome), 2700); }
      for (const id of r.got || []) setTimeout(() => UI.toast(fmt(HS.LINES.got, { name: HS.FURN[id].zh, src: HS.SRC_ZH(id) }), 2600), 600);
      V.hint.textContent = FAM ? '撳團絨＝摸摸・撳細佬＝跳跳・撳住客＝寵物卡' : '撳團絨＝觸摸反應・撳細佬＝跳一跳'; V.h5T = 0; UIS('popupOpen'); SND('reward'); if (!V.raf) V.raf = requestAnimationFrame(loop); note('open', { from: V.from }); return true;
    }
    function close(why) { if (!V.open) return false; if (V.deco) decorate(false); V.open = false; G.houseIsOpen = false; V.el.style.display = 'none'; document.body.classList.remove('s2-house'); UIS('tap'); note('close', { why }); save(); return true; }
    G.houseOpen = open; G.houseClose = close;
    // 返回鍵：瀏覽器 Esc
    window.addEventListener('keydown', (e) => { if (e.key === 'Escape' && V.open && !(UI.isModalOpen && UI.isModalOpen())) { if (V.deco) decorate(false); else close('esc'); } });

    // ── 花園 rail「屋仔」掣＋解鎖／獎勵 tick ──
    const RB = { el: null, lock: null, forceLock: 0 };
    function railTick() {
      const o = SR.st(S()), show = (o.phase === 'kid' || HS.unlocked(S())) && A.ready; let el = RB.el;
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), host = rail || document.getElementById('top-r'); if (!host) return;
        el = RB.el = document.createElement('div'); el.id = 's2house'; el.className = 'ibtn panel'; el.dataset.testid = 's2-rail-house'; el.title = '屋仔';
        el.style.cssText = rail ? 'left:360px;top:336px;width:48px;height:48px' : 'position:relative;display:inline-block;width:40px;height:40px;margin-left:4px';
        const sz = rail ? 48 : 40; el._u = mkImg('ui/btn_house@3x.png', 'left:50%;top:50%;width:' + sz + 'px;height:' + sz + 'px;margin:' + (-sz / 2) + 'px 0 0 ' + (-sz / 2) + 'px'); el._l = mkImg('ui/btn_house_locked@3x.png', 'left:50%;top:50%;width:' + sz + 'px;height:' + sz + 'px;margin:' + (-sz / 2) + 'px 0 0 ' + (-sz / 2) + 'px');
        el.appendChild(el._u); el.appendChild(el._l); const lb = document.createElement('i'); lb.className = 'l'; lb.textContent = '屋仔'; if (!rail) lb.style.display = 'none'; el.appendChild(lb);
        const rd = document.createElement('b'); rd.className = 'rd'; rd.dataset.testid = 's2-rail-house-dot'; el.appendChild(rd); el._d = rd;
        el.addEventListener('click', (e) => { e.stopPropagation(); if (UI.isModalOpen && UI.isModalOpen()) return; UIS('tap'); if (RB.forceLock > pnow() || !HS.unlocked(S())) { UI.toast(HS.LINES.locked, 2400); note('lockedTap', { from: 'rail' }); return; } open('rail'); });
        host.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return;
      const un = HS.unlocked(S()) && !(RB.forceLock > pnow()); el.dataset.locked = un ? '0' : '1'; el._u.style.display = un ? '' : 'none'; el._l.style.display = un ? 'none' : '';
      if (un) { const e = HS.ensure(S(), nowMs()); if (e.fresh) { HS.st(S()).seen = false; save(); note('unlock'); } const got = HS.syncRewards(S(), nowMs()); if (got.length) { HS.st(S()).seen = false; save(); for (const id of got) UI.toast(fmt(HS.LINES.got, { name: HS.FURN[id].zh, src: HS.SRC_ZH(id) }), 2600); note('got', { got }); } }
      el._d.style.display = un && !HS.st(S()).seen ? '' : 'none';
    }
    let rtT = 0; const s2t = G.s2Tick; G.s2Tick = function (dt) { const r = s2t ? s2t.apply(this, arguments) : undefined; const t = pnow(); if (t - rtT > 500) { rtT = t; try { railTick(); } catch (e) { note('err', { e: String(e && e.message || e) }); } } return r; };

    // ── 🛠 開發者模式「家 4b」 ──
    const prep = () => { const o = SR.st(S()); if (o.phase === 'kid' && o.rel === 'family') return null; const r = G.s2Test && G.s2Test.family ? G.s2Test.family() : { ok: false, msg: '冇細佬試玩' }; return r.ok ? null : r; };
    const openP = (fn) => { const e = prep(); if (e) return e; if (!A.ready) return { ok: false, msg: '屋仔載入緊' }; if (!V.open && !open('dev')) return { ok: false, msg: '開唔到屋仔' }; return fn ? fn() : { ok: true, msg: '入咗屋仔' }; };
    const giveAll = (only) => { const o = HS.st(S()); for (const id of HS.IDS) if (!only || only.includes(id)) o.owned[id] = o.owned[id] || nowMs(); save(); if (V.deco) fillCards(); };
    const putSet = (k) => { const set = Hj().sets[k]; giveAll(Object.values(set.items)); for (const s in set.items) HS.place(S(), s, set.items[s], nowMs(), store); save(); if (Z.mode === 'sleep') startSleep(true); if (V.deco) { fillCards(); placePins(); } return set.zh; };
    const DEV = { id: 'house', title: '家 4b（屋仔）', order: 41,
      status: () => { const o = SR.st(S()); if (o.phase !== 'kid') return '未有細佬'; if (o.rel !== 'family') return SR.REL_ZH[o.rel] + '（未開）'; const h = HS.st(S()); return HS.IDS.filter(i => h.owned[i]).length + '／12 件・整蠱剩 ' + HS.prankLeft(S(), nowMs()); },
      items: [
        ['prep', '準備：細佬變家人', () => { const e = prep(); return e || { ok: true, msg: '細佬已經係家人（入口開咗）' }; }],
        ['entry', '睇花園入口掣', () => { const e = prep(); if (e) return e; if (V.open) close('dev'); railTick(); if (RB.el) { RB.el.animate([{ transform: 'translate(-50%,-50%) scale(1)' }, { transform: 'translate(-50%,-50%) scale(1.35)' }, { transform: 'translate(-50%,-50%) scale(1)' }], { duration: 600, iterations: 3 }); } return { ok: true, msg: '右邊「屋仔」掣（細佬掣下面）' }; }],
        ['locked', '睇上鎖入口（10 秒）', () => { if (V.open) close('dev'); RB.forceLock = pnow() + 10000; railTick(); if (RB.el && RB.el.style.display !== 'none') RB.el.click(); return { ok: true, msg: '上鎖版：撳出「' + HS.LINES.locked + '」' }; }],
        ['open', '入屋仔', () => openP()],
        ['deco', '開佈置', () => openP(() => { decorate(true); return { ok: true, msg: '佈置模式' }; })],
        ['shards', '加 200 碎（試買）', () => { if (!X) return { ok: false, msg: '冇錢包' }; X.st(S()).wallet.total += 200; save(); if (V.deco) fillCards(); return { ok: true, msg: '碎 +200（而家 ' + wallet() + '）' }; }],
        ['rewards', '攞委託＋訪客獎', () => { const e = prep(); if (e) return e; HS.ensure(S(), nowMs()); giveAll(['wall_frame', 'win_star', 'lamp_mushroom', 'lamp_firefly']); return { ok: true, msg: '團絨相框、星星窗、蘑菇燈、螢火瓶燈' }; }],
        ['setA', '擺森林組（A）', () => openP(() => ({ ok: true, msg: '擺好' + putSet('A') }))],
        ['setB', '擺夢幻組（B）', () => openP(() => ({ ok: true, msg: '擺好' + putSet('B') }))],
        ['sit', '坐埋一齊', () => openP(() => { V.sleepOv = false; if (Z.mode === 'sleep') free(); startSit(true); return { ok: true, msg: '坐埋一齊（6 秒）' }; })],
        ['prank', '整蠱（唔計次數）', () => openP(() => { V.sleepOv = false; if (Z.mode === 'sleep') free(); startPrank(true); return { ok: true, msg: '整蠱！（今日剩 ' + HS.prankLeft(S(), nowMs()) + '）' }; })],
        ['sleep', '同床瞓（夜晚）', () => openP(() => { V.sleepOv = true; V.nightOv = true; V.mix = 1; startSleep(true); return { ok: true, msg: '21:00–03:00：兩隻一齊瞓床' }; })],
        ['night', '日／夜切換', () => openP(() => { V.nightOv = !night(); return { ok: true, msg: V.nightOv ? '夜晚' : '日間' }; })],
        ['touch', '摸團絨（3a 反應）', () => openP(() => { V.sleepOv = false; if (Z.mode === 'sleep') free(); const q = window.__qa && window.__qa.touch; if (q) q.gesture('tickle'); return { ok: true, msg: '撳團絨＝3a 觸摸反應（搔癢）' }; })],
        ['auto', '還原自動時間', () => { V.nightOv = null; V.sleepOv = null; if (V.open) free(); return { ok: true, msg: '跟返時間' }; }],
        ['close', '返花園', () => (close('dev') ? { ok: true, msg: '返咗花園' } : { ok: false, msg: '唔喺屋仔' })],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    /* 5a 介面（long5aui.js 用） */
    G.house5 = { open: (f) => open(f || 'l5'), close: () => close('l5'), room: () => V.room, goRoom: (k, q) => (V.open ? goRoom(k, q) : false), loadRoom, isOpen: () => V.open, refresh: () => { syncRes(true); hud5(); if (V.deco) { fillCards(); placePins(); } },
      greet: (id, other) => { const a = actorOf(id); if (!a) return { ok: false, reason: 'notHere' }; let b = other ? actorOf(other) : null; if (!b) { const xs = actors().filter(p => p !== a); if (!xs.length) return { ok: false, reason: 'alone' }; b = xs.sort((p, q) => Math.hypot(p.x - a.x, p.y - a.y) - Math.hypot(q.x - a.x, q.y - a.y))[0]; }
        V.sleepOv = V.sleepOv === true ? false : V.sleepOv; for (const p of [a, b]) if (p.mode === 'sleep') idle(p, 1); return startGreet(a, b, true) ? { ok: true } : { ok: false, reason: 'busy' }; },
      actors: () => actors().map(p => ({ id: p.id || p.who, who: p.who, kind: p.kind || p.who, fk: fkOfA(p), x: +p.x.toFixed(1), y: +p.y.toFixed(1), dir: p.dir, mode: p.mode, clip: p.clip, box: p.box, last: p.last || null })),
      greetSt: () => (Z.greet ? { a: Z.greet.a.id || Z.greet.a.who, b: Z.greet.b.id || Z.greet.b.who, gap: Z.greet.gap, t0: Z.greet.t0, ready: Z.greet.ready } : null),
      css: (id) => { const p = actorOf(id); if (!p || !V.cv) return null; const b = p.box || [p.x - 8, p.y - 16, p.x + 8, p.y], r = V.cv.getBoundingClientRect(); return { x: r.left + (b[0] + b[2]) / 2 / W * r.width, y: r.top + ((b[1] + b[3]) / 2 + V.offY) / H * r.height }; },
      trFk: () => trForm(), sitW: (id) => { const p = actorOf(id); return p ? sitW(p) : null; }, hud: () => hud5() };

    window.__qa = window.__qa || {};
    window.__qa.house = {
      st: () => ({ ready: A.ready, errors: A.errors.slice(), open: V.open, room: V.room, res: G.house5.actors().filter(a => a.who === 'res'), greet: G.house5.greetSt(), deco: V.deco, sel: V.sel, offY: V.offY, mix: V.mix, night: night(), sleepWanted: sleepWanted(), mode: Z.mode, bed: !!Z.bed,
        pets: Object.fromEntries(Object.entries(PET).map(([k, p]) => [k, { x: +p.x.toFixed(1), y: +p.y.toFixed(1), dir: p.dir, mode: p.mode, clip: p.clip, box: p.box, last: p.last || null }])),
        prank: Z.prank ? { p: Z.prank.p, v: Z.prank.v, t: Math.round(Z.prank.t), counted: Z.prank.counted } : null, stats: Object.assign({}, V.stats), save: HS.summary(S(), nowMs()), wallet: wallet(), log: log.slice(), gest: G.beh && G.beh.gest ? { key: G.beh.gest.key } : null,
        rail: RB.el ? { shown: RB.el.style.display !== 'none', locked: RB.el.dataset.locked, dot: RB.el._d.style.display !== 'none' } : null }),
      open: (f) => open(f || 'qa'), close: () => close('qa'), decorate: (v) => decorate(v !== false), tab: (k) => selTab(k), card: (id) => cardTap(id), place: (s, id) => doPlace(s, id), give: (ids) => giveAll(ids), set: (k) => putSet(k),
      sit: () => startSit(true), prank: (force) => startPrank(force !== false), sleep: (v) => { V.sleepOv = v == null ? true : v; if (V.sleepOv) startSleep(true); else free(); return Z.mode; }, night: (v) => { V.nightOv = v; V.mix = v == null ? null : (v ? 1 : 0); return night(); },
      free: () => free(), duoAt: (ms) => { Z.nextDuo = pnow() + (ms || 0); }, rail: () => railTick(), petCss: (who) => { const p = PET[who || 'tr'], b = p.box || [p.x - 8, p.y - 16, p.x + 8, p.y], r = V.cv.getBoundingClientRect(); return { x: r.left + (b[0] + b[2]) / 2 / W * r.width, y: r.top + ((b[1] + b[3]) / 2 + V.offY) / H * r.height }; },
      lockFor: (ms) => { RB.forceLock = pnow() + (ms || 0); railTick(); }, petAt: (who, x, y) => { const p = PET[who]; p.x = x; p.y = y; p.tgt = null; }, freeze: () => { free(); Z.nextDuo = Infinity; for (const k in PET) idle(PET[k], 999); },
    };
    note('install'); return true;
  }
  return { install };
});
