/* 《微光小圃》 b3bui.js — 第 3 批 3b 瀏覽器膠水（docs-gdd/batch3-fun-spec.md §③④；遊美 art/batch3b）。原創代碼。
   ③ 朋友訪客：每日最多 1 位（visit.js 排程）→ walk 入、團絨得意帶佢行一圈（puppet）、企喺花圃；拖禮物（花瓶花／重覆收集品）落佢身＝送禮；滿 5 → 擺設＋徽章。
      蝸牛郵差＝信（撳信 → 一句日記）、蘑菇婆婆＝種子（下次種花免費）＋貼士、螢火小販＝賣擺設（10–20 碎，17–07）。
   ④ 進化大場面：hatch／grow／evolve／elder → 8s 全畫面（暗場→光點→剪影→光繭→爆→剪影閃換→現身→名卡），2s 後撳＝跳；播完先出原本彈窗。
      預兆（達下一階前最後窗口）：閃剪影／胃口大（一句＋得意面）／怪夢泡泡。圖鑑「團絨日記」四格小故事（進化節點解鎖）。
   Playwright（navigator.webdriver）預設唔自動出訪客／大場面／預兆（?visit=1／?evoscene=1／?omen=1 先開）；__qa.b3b 直接觸發。?b3b=0 全停。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.b3bui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const MX = 14, MY = 12, CX = 97, GY = 292;     // render.js 層邊距／寵物腳底（art 座標）
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  function install(G, NS) {
    const V = NS.visit, D = NS.data, P = D.PARAMS.b3b; if (!V || !P || P.enabled === false) return false;
    const qs = new URLSearchParams(location.search); if (qs.get('b3b') === '0') return false;
    const wd = !!(navigator && navigator.webdriver), R = G.renderer, UI = NS.ui, X = NS.sys12, X2 = NS.sys12b, BEH = NS.behavior, C = V.CFG;
    const on = (k) => qs.get(k) === '1' || (!wd && qs.get(k) !== '0');
    const AUTO = { visit: on('visit'), scene: on('evoscene'), omen: on('omen') };
    const BASE = P.art.base, S = () => G.state, pnow = () => performance.now();
    const say = (line, o) => (G.say ? G.say(Object.assign({ line, src: 'b3b', sec: 3.5 }, o || {})) : UI.toast(line, 2600));
    const SND = (k, i) => { const a = NS.audio; if (a && a.Engine) a.Engine.notify(k, i || {}); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const fmt = (t, o) => t.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m));
    const log = [];
    const note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 60) log.shift(); };

    // ── 載圖（遊美 batch3b.json；逐檔容錯）──
    const A = { json: null, clips: null, img: {}, ready: false, errors: [] };
    const img = (src) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error(src)); im.src = src; });
    const jget = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    G.b3bLoad = Promise.all([jget(BASE + 'batch3b.json'), jget(BASE + 'visit_pet_clips.json').catch(() => null)]).then(([j, vc]) => {
      A.json = j; A.clips = vc && vc.clips; const files = new Set();
      for (const k in j.visitors) { const v = j.visitors[k]; for (const c in v.clips) { files.add(v.clips[c].file); if (v.clips[c].emissive) files.add(v.clips[c].emissive); } files.add(v.portrait.file); if (v.badge) files.add(v.badge.file); files.add(v.decor.file); if (v.decor.emissive) files.add(v.decor.emissive); }
      for (const k in j.visitorProps) files.add(j.visitorProps[k].file);
      for (const k in j.evolution.assets) if (k[0] !== '_') files.add(j.evolution.assets[k].file);
      for (const k in j.evolution.cards.files) files.add(j.evolution.cards.files[k].file);
      return Promise.all([...files].map(f => img(BASE + f).then(im => { A.img[f] = im; }).catch(() => A.errors.push(f))));
    }).then(() => { A.ready = !!A.json; return A; }).catch(e => { A.errors.push(String(e && e.message || e)); return null; });
    // 3a 反應圖載完 → 掛 visit_lead_start／strut／gift_cheer（舊 25 形態有錨點先用；evo 形態用 atlas smug_pose／cheer）
    Promise.all([G.b3bLoad, G.rxLoad || Promise.resolve(null)]).then(() => { const rx = R.rx; if (rx && rx.clips && A.clips) for (const k in A.clips) if (!rx.clips[k]) rx.clips[k] = A.clips[k]; });
    const VJ = (who) => A.json && A.json.visitors[who];
    const strip = (file, i, fw, fh) => { const im = A.img[file]; return im ? { img: im, sx: (i | 0) * fw, sy: 0, sw: fw, sh: fh } : null; };
    const asset = (id, i) => { const a = A.json && A.json.evolution.assets[id]; if (!a) return null; const n = a.frames || 1, s = strip(a.file, ((i % n) + n) % n, a.frameW, a.frameH); if (s) { s.px = a.pivot[0]; s.py = a.pivot[1]; } return s; };

    // ── 存檔／狀態 ──
    const st = () => V.st(S());
    const VS = { cur: null };                     // 而家喺度嘅訪客
    const sess = { t0: pnow(), delay: (C.delaySec[0] + Math.random() * (C.delaySec[1] - C.delaySec[0])) * 1000, tried: false };
    const PHASES = ['enter', 'join', 'lead', 'stand', 'leave'];
    function petBusy() { return G.mode === 'minigame' || !!G.mg2Busy; }
    function release() { const b = G.beh; if (b && b.puppet) { b.puppet = null; b.depth = 0; b.faceAct = null; try { if (BEH.force) BEH.force(b, 'stay', G.behCtx || { s: S() }); } catch (e) { } } }
    function spawn(who, o) {
      o = o || {}; const s = S(), now = G.now(); if (VS.cur) leave(true);
      if (!o.force) { const c = V.canVisit(s, now); if (!c.ok) return { ok: false, reason: c.reason }; }
      if (s.stage === 'egg') return { ok: false, reason: 'egg' };
      who = who || V.pickVisitor(s, G.hour(), Math.random);
      const r = V.startVisit(s, who, now); if (!r.ok) return r;
      const side = o.side === 'right' ? 1 : o.side === 'left' ? -1 : (Math.random() < 0.5 ? -1 : 1), v = VJ(who);
      const x0 = side < 0 ? C.enterX[0] : C.enterX[1];
      VS.cur = { who, side, rev: side > 0, phase: 'enter', pt: 0, x: x0, y: GY, dir: -side, clip: 'walk', ct: 0, happyT: -1, arriveAt: now, until: pnow() + C.staySec * 1000,
        standX: CX + side * C.standDx, speed: (v && v.walkSpeed) || C.walkSpeed[who] || 12, letter: null, seed: null, hearts: [], meter: 0, said: false, petX0: G.beh ? G.beh.x : 0 };
      note('spawn', { who, side }); SND('cue', { name: 'event_butterfly' }); say(V.LINES.arrive[who], { sec: 4 }); if (G.save) G.save();
      return { ok: true, who, side };
    }
    function leave(now) {
      const c = VS.cur; if (!c) return false; note('leave', { who: c.who, now: !!now });
      if (c.phase === 'enter' || c.phase === 'join' || c.phase === 'lead') release();
      if (now) { VS.cur = null; tray(false); return true; }
      c.phase = 'leave'; c.pt = 0; c.dir = c.side; c.clip = 'walk'; tray(false); say(fmt(V.LINES.leave, { name: V.NAME[c.who] }), { sec: 2.5 }); return true;
    }
    function setPhase(c, ph) { c.phase = ph; c.pt = 0; note('phase', { ph }); }
    const petFaceSmug = () => { const p = (P.face && P.face.presets) || (D.PARAMS.face && D.PARAMS.face.presets) || {}; const sm = p.smug || ['sleepy', 'C', 'squint']; return { eyes: sm[0], gaze: sm[1], mouth: sm[2] }; };
    const clipFps = (clip) => { const d = D.CLIPS[clip]; return (d && d.fps) || 8; };

    /* 每幀（main loop，實時 dt；touchTick 之後、tickWorld 之前） */
    function visitTick(dt) {
      const c = VS.cur, s = S(), b = G.beh, ms = dt * 1000;
      if (!c) {
        if (AUTO.visit && !SC.cur && !petBusy() && !UI.isModalOpen() && !G.ev && s.stage !== 'egg' && !s.sleeping && pnow() - sess.t0 >= sess.delay && V.canVisit(s, G.now()).ok) spawn(null);
        return;
      }
      c.pt += ms; c.ct += ms; const v = VJ(c.who);
      if (petBusy() && (c.phase === 'enter' || c.phase === 'join' || c.phase === 'lead')) { release(); c.x = c.standX; c.y = GY; setPhase(c, 'stand'); }
      if (c.phase !== 'leave' && pnow() >= c.until) leave();
      const toward = (tx, sp) => { const d = tx - c.x, st0 = sp * dt; if (Math.abs(d) <= st0) { c.x = tx; return true; } c.x += Math.sign(d) * st0; c.dir = Math.sign(d); return false; };
      if (c.phase === 'enter') {
        c.clip = 'walk'; const done = toward(c.standX, c.speed * 1.6);
        if (b && !petBusy()) { const px = b.puppet ? b.puppet.x : b.x, d = 0 - px, st0 = 23 * dt, nx = Math.abs(d) <= st0 ? 0 : px + Math.sign(d) * st0;   // 團絨行返中間（帶路起點）
          b.puppet = { x: nx, dir: nx === 0 ? -c.side * -1 * 1 * (c.side < 0 ? -1 : 1) : Math.sign(d), clip: nx === 0 ? 'idle' : 'walk', frame: Math.floor(c.pt / 110) % 6, depth: 0 }; if (nx === 0) b.puppet.dir = c.side; }
        if (done) { c.clip = 'idle'; c.dir = -c.side; setPhase(c, 'join'); }
      } else if (c.phase === 'join') {                // 企定 400ms → 團絨得意 pose（visit_lead_start 900ms）＋訪客行去跟尾點
        const L = V.leadAt(0, c.rev), go = c.pt >= C.lead.afterArriveMs;
        if (go) { c.clip = toward(L.vis.x, 30) ? 'idle' : 'walk'; c.y += (L.vis.y - c.y) * Math.min(1, dt * 4); c.dir = L.vis.dir; }
        if (b) b.puppet = { x: L.pet.x - CX, dir: go ? L.pet.dir : c.side, clip: go ? 'smug_pose' : 'idle', frame: go ? Math.floor((c.pt - C.lead.afterArriveMs) / 1000 * clipFps('smug_pose')) : 0, face: go ? petFaceSmug() : null, depth: L.pet.y - GY };
        if (go && !c.said) { c.said = true; setTimeout(() => say(V.LINES.lead, { sec: 3 }), 300); }
        if (c.pt >= C.lead.afterArriveMs + C.lead.startMs) setPhase(c, 'lead');
      } else if (c.phase === 'lead') {
        const L = V.leadAt(c.pt, c.rev);
        c.x = L.vis.x; c.y = L.vis.y; c.dir = L.vis.dir; c.clip = 'walk';
        if (b) b.puppet = { x: L.pet.x - CX, dir: L.pet.dir, clip: 'walk_happy', frame: Math.floor(c.pt / 1000 * clipFps('walk_happy')), face: petFaceSmug(), depth: L.pet.y - GY };
        if (c.pt >= C.lead.lapMs) { release(); c.clip = 'idle'; setPhase(c, 'stand'); arrived(c); }
      } else if (c.phase === 'stand') {
        const px = CX + (b ? b.x : 0); let walking = false;
        if (Math.abs(c.x - c.standX) > 0.5 && c.happyT < 0) { walking = !toward(c.standX, c.speed * 1.4); c.y += (GY - c.y) * Math.min(1, dt * 3); }   // 帶完路行返去企位（唔好黐住團絨）
        if (!walking) c.dir = px >= c.x ? 1 : -1;
        if (c.happyT >= 0) { c.happyT += ms; if (c.happyT >= 600) c.happyT = -1; }
        c.clip = c.happyT >= 0 ? 'happy' : walking ? 'walk' : 'idle';
      } else if (c.phase === 'leave') {
        c.clip = 'walk'; c.y += (GY - c.y) * Math.min(1, dt * 2);
        if (toward(c.side < 0 ? C.enterX[0] - 20 : C.enterX[1] + 20, c.speed * 2)) { VS.cur = null; note('gone'); return; }
      }
      // 道具
      if (c.letter && c.letter.st === 'fly') { c.letter.t += ms; if (c.letter.t >= 400) c.letter.st = 'wait'; }
      if (c.seed) { c.seed.t += ms; if (c.seed.t >= 1600) c.seed = null; }
      c.hearts = c.hearts.filter(h => (h.t += ms) < 900);
      if (c.meter > 0) c.meter = Math.max(0, c.meter - ms);
      const gd = st().day; tray((c.phase === 'stand' || c.phase === 'lead' || c.phase === 'join') && !(gd.k === V.dayKey(G.now()) && (gd.gift[c.who] | 0) >= C.giftPerDay));   // 今日送咗就收埋托盤
    }
    function arrived(c) {
      const s = S(), now = G.now();
      if (c.who === 'snail_postman' && G.s2Arrived && G.s2Arrived(c.who)) { /* 4a：今次送細佬蛋（唔派信）*/ }
      else if (c.who === 'snail_postman') { c.letter = { st: 'fly', t: 0 }; }
      else if (c.who === 'mushroom_granny') { c.seed = { t: 0 }; V.seedGift(s); const tip = V.LINES.tips[Math.floor(Math.random() * V.LINES.tips.length)]; UI.toast(V.LINES.seed, 2400); setTimeout(() => say(tip, { sec: 4 }), 900); if (G.save) G.save(); }
      else if (c.who === 'firefly_vendor') { say(V.LINES.vendor, { sec: 3 }); }
      note('arrived', { who: c.who });
    }
    /* 訪客錨點（art；朝左＝pivot 鏡像 W−1−x） */
    function anchor(c, name) {
      const v = VJ(c.who); if (!v) return { x: c.x, y: c.y - 20 }; const a = v.anchors[name] || [v.pivot[0], 0];
      return { x: c.x + (c.dir < 0 ? v.pivot[0] - a[0] : a[0] - v.pivot[0]), y: c.y + a[1] - v.pivot[1] };
    }
    function hitRect(c) {
      const v = VJ(c.who), r = v ? v.hitbox.rel : [-18, -24, 18, 1], pv = R.par ? R.par.x * -1.5 : 0;
      const x0 = c.dir < 0 ? -r[2] : r[0], x1 = c.dir < 0 ? -r[0] : r[2];
      return { x: c.x + x0 + pv - 3, y: c.y + r[1] - 3, w: x1 - x0 + 6, h: r[3] - r[1] + 6 };
    }
    function letterRect(c) { if (!c.letter || c.letter.st !== 'wait') return null; const h = anchor(c, 'head'), pv = R.par ? R.par.x * -1.5 : 0; return { x: h.x - 9 + pv, y: h.y - 22, w: 18, h: 16 }; }
    const inR = (a, r) => r && a.x >= r.x && a.x <= r.x + r.w && a.y >= r.y && a.y <= r.y + r.h;

    // ── 送禮 ──
    const SB = () => (X2 && X2.st ? X2.st(S()) : null);
    function itemName(it) {
      if (it.kind === 'free') return V.LINES.freeFlower;
      const P2 = D.PARAMS.systems12b || {};
      if (it.kind === 'vase') { const f = ((P2.garden && P2.garden.flowers) || []).find(x => x.k === it.k); return (f ? f.name : it.k); }
      const w = ((P2.walk && P2.walk.items) || []).find(x => x.k === it.k); return (w ? w.name : it.k);
    }
    function doGift(it) {
      const c = VS.cur, s = S(), now = G.now(); if (!c || c.phase === 'leave') return { ok: false, reason: 'none' };
      const o = V.st(s); if ((o.day.k === V.dayKey(now)) && (o.day.gift[c.who] | 0) >= C.giftPerDay) { say(V.LINES.giftDone, { sec: 2.5 }); return { ok: false, reason: 'daily' }; }
      if (!V.takeItem(s, SB(), it)) { UI.toast('送唔到'); return { ok: false, reason: 'item' }; }
      const r = V.gift(s, c.who, now); if (!r.ok) return r;
      c.happyT = 0; c.clip = 'happy'; c.hearts.push({ t: 0, x: 0 }); c.meter = 2600;
      const b = G.beh; if (b && !b.puppet && !(G.touchSt && G.touchSt.act) && R.act) R.act('celebrate', 1.0);   // 團絨 visit_gift_cheer（evo 形態：celebrate）
      if (b && !b.puppet && !(G.touchSt && G.touchSt.act)) GEST.cheer = pnow();
      SND('cue', { name: 'event_gift' }); say(fmt(V.LINES.gift, { name: V.NAME[c.who], fr: r.fr }), { sec: 3 });
      if (r.reward) { UI.toast(fmt(V.LINES.friendMax, { name: V.NAME[c.who], decor: r.reward.decorName }), 3200); if (X2 && X2.badgeCheck) { X2.badgeCheck(s, now); if (UI.processEvents) UI.processEvents(); } }
      note('gift', { who: c.who, item: it.kind + ':' + it.k, fr: r.fr }); if (G.save) G.save(); refreshTray(true);
      return Object.assign({ item: it }, r);
    }
    // 托盤（DOM；拖落訪客＝送）
    let trayEl = null, trayOn = false, trayKey = '';
    function tray(show) {
      if (!trayEl) {
        trayEl = document.createElement('div'); trayEl.id = 'b3bTray'; trayEl.dataset.testid = 'b3b-tray';
        trayEl.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:calc(178px + env(safe-area-inset-bottom,0px));display:none;gap:4px;z-index:6;max-width:94%;overflow-x:auto;padding:4px 6px;border-radius:10px;background:rgba(30,22,48,.72);color:#fff;font-size:11px;align-items:center;touch-action:none';
        (document.getElementById('ui') || document.body).appendChild(trayEl);
      }
      const want = !!show && !SC.cur && !UI.isModalOpen(); if (want !== trayOn) { trayOn = want; trayEl.style.display = want ? 'flex' : 'none'; if (want) refreshTray(true); }
    }
    function refreshTray(force) {
      if (!trayEl) return; const items = V.giftItems(S(), SB()), key = items.map(i => i.kind + i.k + i.n).join('|'); if (!force && key === trayKey) return; trayKey = key;
      trayEl.innerHTML = '<span style="opacity:.8;white-space:nowrap">拖去送 →</span>';
      for (const it of items.slice(0, 8)) {
        const ch = document.createElement('div'); ch.className = 'b3b-chip'; ch.dataset.testid = 'b3b-gift-' + it.kind + '-' + it.k;
        ch.style.cssText = 'white-space:nowrap;padding:4px 7px;border-radius:8px;background:#f3e1b8;color:#4a2e1a;cursor:grab;user-select:none;touch-action:none';
        ch.textContent = (it.kind === 'vase' ? '✿ ' : it.kind === 'walk' ? '◆ ' : '❀ ') + itemName(it) + (it.kind === 'free' ? '' : ' ×' + it.n);
        ch.addEventListener('pointerdown', (e) => dragStart(e, it, ch)); trayEl.appendChild(ch);
      }
    }
    let drag = null;
    function dragStart(e, it, ch) {
      e.preventDefault(); e.stopPropagation(); const g = ch.cloneNode(true); g.dataset.testid = 'b3b-drag-ghost';
      g.style.cssText += ';position:fixed;pointer-events:none;z-index:99;opacity:.9;left:' + (e.clientX - 20) + 'px;top:' + (e.clientY - 14) + 'px'; document.body.appendChild(g);
      drag = { it, g, id: e.pointerId }; try { ch.setPointerCapture(e.pointerId); } catch (er) { }
      const mv = (ev) => { if (!drag) return; drag.g.style.left = (ev.clientX - 20) + 'px'; drag.g.style.top = (ev.clientY - 14) + 'px'; };
      const up = (ev) => { ch.removeEventListener('pointermove', mv); ch.removeEventListener('pointerup', up); ch.removeEventListener('pointercancel', up); const d = drag; drag = null; if (!d) return; d.g.remove();
        if (ev.type === 'pointercancel') return; const a = R.screenToArt(ev.clientX, ev.clientY), c = VS.cur; if (c && inR(a, hitRect(c))) doGift(d.it); else note('dropMiss', { x: Math.round(a.x), y: Math.round(a.y) }); };
      ch.addEventListener('pointermove', mv); ch.addEventListener('pointerup', up); ch.addEventListener('pointercancel', up);
    }
    // 撳訪客／信
    function readLetter(c) { const line = V.letter(S(), G.now(), Math.random); c.letter = null; if (X && X.diaryNote) try { X.diaryNote(S(), 'b3b', 'letter', G.now()); } catch (e) { } say(line, { sec: 5, urgent: true }); note('letter', { line }); if (G.save) G.save(); return line; }
    function visitorCard(c) {
      const v = VJ(c.who), o = st(), fr = o.vis[c.who].fr, node = document.createElement('div'); node.dataset.testid = 'b3b-visitor-card';
      const por = v ? BASE + v.portrait.file : '';
      node.innerHTML = '<div style="display:flex;gap:10px;align-items:center"><img src="' + por + '" width="52" height="52" style="image-rendering:pixelated;border-radius:8px;background:rgba(255,255,255,.15)"><div><b>' + V.NAME[c.who] + '</b><div data-testid="b3b-fr" data-fr="' + fr + '" style="letter-spacing:2px;color:#e05a7a">' + '♥'.repeat(fr) + '<span style="opacity:.35">' + '♥'.repeat(5 - fr) + '</span></div><small>拖托盤嘅禮物落佢身＝送禮（每日 1 次）</small></div></div>';
      if (c.who === 'firefly_vendor') {
        const sh = document.createElement('div'); sh.style.cssText = 'margin-top:8px;display:grid;gap:4px'; sh.dataset.testid = 'b3b-shop';
        for (const it of C.shop) { const own = !!o.decor[it.id], bt = document.createElement('div'); bt.className = 'btn' + (own ? ' sec' : ''); bt.dataset.testid = 'b3b-buy-' + it.id; bt.textContent = V.DECOR_NAME[it.id] + (own ? '（已有）' : '　' + it.price + ' 碎');
          bt.addEventListener('click', () => { const r = buyDecor(it.id); bt.textContent = V.DECOR_NAME[it.id] + (r.ok || r.reason === 'owned' ? '（已有）' : '　' + it.price + ' 碎'); }); sh.appendChild(bt); }
        node.appendChild(sh);
      }
      UI.modal({ title: V.NAME[c.who], kind: 'b3bVisitor', node, buttons: [{ text: '好', primary: true }] });
      c.meter = 2600; note('card', { who: c.who });
    }
    function buyDecor(id) {
      const r = V.buy(S(), id, X.spend, G.now()); if (r.ok) { UI.toast(fmt(V.LINES.bought, { decor: r.name }), 2400); UIS('toast', { currency: true }); if (G.save) G.save(); }
      else UI.toast(r.reason === 'owned' ? V.LINES.owned : r.reason === 'shards' ? V.LINES.shards : '買唔到'); note('buy', { id, ok: r.ok, reason: r.reason || null }); return r;
    }
    G.b3bTap = function (a) {
      if (SC.cur) { sceneTap(); return true; }
      const c = VS.cur; if (!c || c.phase === 'leave') return false;
      if (G.g3d && typeof G.g3d.on === 'function' && G.g3d.on() && typeof G.g3d.hitActor === 'function') {
        const h = G.g3d.hitActor(a.x, a.y);
        if (h && (h.kind === 'visitProp' || (h.id && String(h.id).indexOf('letter') >= 0)) && c.letter && c.letter.st === 'wait') { readLetter(c); return true; }
        if (h && h.kind === 'visitor') { visitorCard(c); return true; }
      }
      if (inR(a, letterRect(c))) { readLetter(c); return true; }
      if (inR(a, hitRect(c))) { visitorCard(c); return true; }
      return false;
    };
    document.addEventListener('visibilitychange', () => { if (document.hidden && VS.cur) leave(true); });   // 落線＝走

    // ── 預兆 ──
    const OM = { kind: null, force: null, chk: -1e9, flick0: -1e9, flickNext: 0, dream0: -1e9, dreamNext: 0, icon: 0, smugUntil: 0 };
    function omenTick() {
      const t = pnow(), s = S();
      if (t - OM.chk > 1000) { OM.chk = t; const o = V.omen(s, D.PARAMS.stageSec); const k = OM.force || (AUTO.omen && o ? o.kind : null); if (k !== OM.kind) { OM.kind = k; if (k) { S().b3b && (st().stats.omens++); note('omen', { k }); } } }
      if (OM.kind === 'flicker' && !s.sleeping && t >= OM.flickNext) { OM.flick0 = t; OM.flickNext = t + 4000 + Math.random() * 3000; }
      if (OM.kind === 'dream' && s.sleeping && t >= OM.dreamNext) { OM.dream0 = t; OM.dreamNext = t + V.DREAM.every; OM.icon = Math.floor(Math.random() * 6); }
      if (OM.smugUntil > t && G.beh && !(G.touchSt && G.touchSt.act) && !G.beh.puppet) { const f = petFaceSmug(); G.beh.faceGest = { eyes: f.eyes, mouth: f.mouth }; }
    }
    { const f0 = G.sysFed; G.sysFed = function () { const r = f0 ? f0.apply(this, arguments) : undefined; if (OM.kind === 'appetite') omenFed(); return r; }; }
    function omenFed() {   // 胃口大：食多陣（eat ×1.5）→ 一句 → 得意面 600ms（sim 飽肚唔變）
      setTimeout(() => { if (R.food && R.food.until > R.t) { R.food.until = R.t + 1.1 * 1.5; R.food.dur = 1.1 * 1.5; } if (R.act) R.act('eat', 1.1 * 1.5); }, 0);   // ui.js 喺 sysFed 之後先 set rd.food
      setTimeout(() => { say(V.LINES.omenStrong, { sec: 3 }); OM.smugUntil = pnow() + 600; }, 1650); note('omenFed');
    }

    // ── render 層（drawL2 入面；art 座標 → ox／oy 加邊距）──
    const ox = (px) => px + MX, oy = (py) => py + MY;
    const GEST = { cheer: -1e9 };
    function drawVisitor(x, c, cc) {
      const v = VJ(c.who); if (!v) return; const cl = v.clips[c.clip] || v.clips.idle, fw = v.frameW, fh = v.frameH;
      const fms = cl.ms * (c.phase === 'lead' && c.clip === 'walk' ? C.lead.walkMul : 1);
      const f = c.clip === 'happy' ? Math.min(cl.frames - 1, Math.floor(Math.max(0, c.happyT) / cl.ms)) : Math.floor(c.ct / fms) % cl.frames;
      const sp = strip(cl.file, f, fw, fh); const vx = Math.round(c.x), vy = Math.round(c.y);
      if (cc && cc.g3d) {
        if (!sp) return;
        const ZS = (Glimmer.garden3d && Glimmer.garden3d.ZSCALE) || 1.6, GY = (Glimmer.garden3d && Glimmer.garden3d.GROUND_Y) || 292, CX = (Glimmer.garden3d && Glimmer.garden3d.CX) || 97;
        R.worldPush({ id: 'visitor', kind: 'visitor', x: vx - CX, z: (vy - GY) * ZS, src: { img: sp.img, sx: sp.sx, sy: sp.sy, sw: fw, sh: fh, px: v.pivot[0], py: v.pivot[1] }, flip: c.dir < 0, shadow: true, hit: true, w: fw * 0.7, h: fh });
        return;
      }
      x.fillStyle = 'rgba(10,20,20,0.3)'; const sw = Math.round(fw * (v.hover ? 0.22 : 0.3));
      for (let dy = -2; dy <= 2; dy++) { const w = Math.round(sw * Math.sqrt(1 - dy * dy / 9)); x.fillRect(ox(vx - w), oy(vy - 1 + dy), w * 2, 1); }
      if (!sp) return;
      x.save(); x.imageSmoothingEnabled = false;
      if (c.dir < 0) { x.translate(ox(vx) + 1, oy(vy)); x.scale(-1, 1); } else x.translate(ox(vx), oy(vy));
      x.drawImage(sp.img, sp.sx, sp.sy, fw, fh, -v.pivot[0], -v.pivot[1], fw, fh); x.restore();
      if (cl.emissive && A.img[cl.emissive] && cc.em) { const e = cc.em, o2 = cc.offs[2][0]; e.save(); e.globalAlpha = 0.85; if (c.dir < 0) { e.translate(vx + o2 + 1, vy); e.scale(-1, 1); } else e.translate(vx + o2, vy); e.drawImage(A.img[cl.emissive], f * fw, 0, fw, fh, -v.pivot[0], -v.pivot[1], fw, fh); e.restore(); }
      if (v.glow) { const g = v.glow, ax = vx + (c.dir < 0 ? v.pivot[0] - g.anchor[0] : g.anchor[0] - v.pivot[0]), ay = vy + g.anchor[1] - v.pivot[1], pu = 0.5 + 0.5 * Math.sin(pnow() / g.pulseMs * Math.PI * 2);
        cc.lights.push({ x: ax + cc.offs[2][0], y: ay, r: g.radius + pu * 3, col: [255, 230, 138], a: 0.45 + 0.35 * pu }); }
    }
    function wzOf(ax, ay) { const ZS = (Glimmer.garden3d && Glimmer.garden3d.ZSCALE) || 1.6, GY = (Glimmer.garden3d && Glimmer.garden3d.GROUND_Y) || 292, CX = (Glimmer.garden3d && Glimmer.garden3d.CX) || 97; return { x: ax - CX, z: (ay - GY) * ZS }; }
    function drawProps(x, c, cc) {
      const PJ = A.json.visitorProps;
      const g3 = cc && cc.g3d;
      if (c.letter) { const L = PJ.letter, im = A.img[L.file], b0 = anchor(c, 'bag'), h = anchor(c, 'head'); let lx, ly;
        if (c.letter.st === 'fly') { const u = clamp(c.letter.t / 400, 0, 1), e = V.E.oCubic(u); lx = b0.x + (h.x - b0.x) * e; ly = b0.y + (h.y - 8 - b0.y) * e - Math.sin(u * Math.PI) * 6; } else { lx = h.x; ly = h.y - 8 + (Math.floor(pnow() / 400) % 2 ? -1 : 0); }
        if (im) { if (g3) { const w = wzOf(lx, c.y); R.worldPush({ id: 'letter', kind: 'visitProp', x: w.x, z: w.z, yLift: Math.max(0, (c.y - ly)), src: { img: im, sx: 0, sy: 0, sw: im.width, sh: im.height, px: L.pivot[0], py: L.pivot[1] }, shadow: false, hit: c.letter.st === 'wait' }); } else x.drawImage(im, ox(Math.round(lx) - L.pivot[0]), oy(Math.round(ly) - L.pivot[1])); } }
      if (c.seed) { const L = PJ.seed, im = A.img[L.file], b0 = anchor(c, 'bag'), h = anchor(c, 'head'), t = c.seed.t; let lx, ly, al = 1;
        if (t < 400) { const e = V.E.oCubic(t / 400); lx = b0.x + (h.x - b0.x) * e; ly = b0.y + (h.y - 8 - b0.y) * e; } else if (t < 1000) { lx = h.x; ly = h.y - 8; } else { const u = (t - 1000) / 600; lx = h.x + (175 - h.x) * u; ly = h.y - 8 + (20 - (h.y - 8)) * u - Math.sin(u * Math.PI) * 20; al = 1 - u * 0.6; }   // 彈去背包（右上星星碎）
        if (im) { if (g3) { const w = wzOf(lx, c.y); R.worldPush({ id: 'seed', kind: 'visitProp', x: w.x, z: w.z, yLift: Math.max(0, (c.y - ly)), src: { img: im, sx: 0, sy: 0, sw: im.width, sh: im.height, px: L.pivot[0], py: L.pivot[1] }, alpha: al, shadow: false, hit: false }); } else { x.globalAlpha = al; x.drawImage(im, ox(Math.round(lx) - L.pivot[0]), oy(Math.round(ly) - L.pivot[1])); x.globalAlpha = 1; } } }
      const rx = R.rx, fh = rx && rx.fx && rx.fx.fx_heart, him = fh && rx.img[fh.file], h = anchor(c, 'head');
      for (const hh of c.hearts) { const u = hh.t / 900, hy = h.y - 4 - u * 16, fr = u < 0.25 ? 0 : 1;
        if (him) { if (g3) { const w = wzOf(h.x, c.y); R.worldPush({ id: 'vheart-' + Math.round(hh.t), kind: 'visitProp', x: w.x, z: w.z, yLift: Math.max(0, (c.y - hy)), src: { img: him, sx: fr * fh.frameW, sy: 0, sw: fh.frameW, sh: fh.frameH, px: fh.pivot[0], py: fh.pivot[1] }, alpha: u > 0.7 ? 1 - (u - 0.7) / 0.3 : 1, shadow: false, hit: false }); } else { x.globalAlpha = u > 0.7 ? 1 - (u - 0.7) / 0.3 : 1; x.drawImage(him, fr * fh.frameW, 0, fh.frameW, fh.frameH, ox(Math.round(h.x) - fh.pivot[0]), oy(Math.round(hy) - fh.pivot[1]), fh.frameW, fh.frameH); x.globalAlpha = 1; } } }
      if (c.meter > 0) { const F = PJ.friend_heart, im = A.img[F.file], fr = st().vis[c.who].fr, x0 = Math.round(h.x) - 24, y0 = Math.round(h.y) - 22;
        if (im) { if (g3) { const w = wzOf(h.x, c.y); for (let i = 0; i < 5; i++) R.worldPush({ id: 'fmeter-' + i, kind: 'visitProp', x: w.x + (i - 2) * 4, z: w.z, yLift: Math.max(8, (c.y - y0)), src: { img: im, sx: (i < fr ? 1 : 0) * F.frameW, sy: 0, sw: F.frameW, sh: F.frameH, px: F.frameW / 2, py: F.frameH }, shadow: false, hit: false }); } else { for (let i = 0; i < 5; i++) x.drawImage(im, (i < fr ? 1 : 0) * F.frameW, 0, F.frameW, F.frameH, ox(x0 + i * 10), oy(y0), F.frameW, F.frameH); } } }
    }
    function drawDecor(x, cc, z, base) {
      const o = st(); const night = G.light && G.light.sun != null ? 1 - G.light.sun : 0.5;
      for (const id of Object.keys(o.decor)) {
        const at = C.decorAt[id], who = Object.keys(C.decor).find(k => C.decor[k] === id), dj = who && VJ(who) && VJ(who).decor; if (!at || !dj) continue;
        if ((z === 'back') !== (at[1] <= base)) continue; const im = A.img[dj.file]; if (!im) continue;
        if (cc && cc.g3d) {
          const meshes = G.g3d && G.g3d.meshObj; const skip = (id === 'deco_firefly_jar' && meshes && (meshes.jar || meshes.can)) || (id === 'deco_mushroom_lamp' && meshes && (meshes.mushroom || meshes.mushrooms));
          if (!skip) {
            const ZS = (Glimmer.garden3d && Glimmer.garden3d.ZSCALE) || 1.6, GY = (Glimmer.garden3d && Glimmer.garden3d.GROUND_Y) || 292, CX = (Glimmer.garden3d && Glimmer.garden3d.CX) || 97;
            R.worldPush({ id: 'decor-' + id, kind: 'decor', x: at[0] - CX, z: (at[1] - GY) * ZS, src: { img: im, sx: 0, sy: 0, sw: im.width, sh: im.height, px: dj.pivot[0], py: dj.pivot[1] }, shadow: true, hit: false });
          }
          continue;
        }
        x.drawImage(im, ox(at[0] - dj.pivot[0]), oy(at[1] - dj.pivot[1]));
        if (dj.emissive) { const em = A.img[dj.emissive]; if (em && cc.em) { cc.em.globalAlpha = 0.8; cc.em.drawImage(em, at[0] - dj.pivot[0] + cc.offs[2][0], at[1] - dj.pivot[1]); cc.em.globalAlpha = 1; }
          cc.lights.push({ x: at[0] + cc.offs[2][0], y: at[1] - dj.pivot[1] * 0.55, r: id === 'deco_firefly_jar' ? 12 : 15, col: id === 'deco_firefly_jar' ? [255, 230, 138] : [255, 190, 130], a: 0.25 + 0.5 * clamp(night, 0, 1) }); }
      }
    }
    let silC = null;
    function drawFlicker(x) {   // 預兆：團絨剪影 #FFF6DA α0.6 閃 2 下（同進化 silhouette 做法）
      const pb = R.petBlit; if (!pb || !V.flickerOn(pnow() - OM.flick0)) return false;
      if (!silC) silC = document.createElement('canvas'); silC.width = pb.sw; silC.height = pb.sh; const g = silC.getContext('2d'); g.clearRect(0, 0, pb.sw, pb.sh);
      g.globalCompositeOperation = 'source-over'; g.drawImage(pb.img, pb.sx, pb.sy, pb.sw, pb.sh, 0, 0, pb.sw, pb.sh); g.globalCompositeOperation = 'source-in'; g.fillStyle = V.FLICK.color; g.fillRect(0, 0, pb.sw, pb.sh); g.globalCompositeOperation = 'source-over';
      if (R._b3bCc && R._b3bCc.g3d) { const beh = G.beh || {}; R.worldPush({ id: 'omen-flicker', kind: 'omen', x: beh.x || 0, z: beh.z || 0, yLift: 4, src: { img: silC, sx: 0, sy: 0, sw: silC.width, sh: silC.height, px: pb.px, py: pb.py }, alpha: V.FLICK.alpha, shadow: false, hit: false }); return true; }
      x.save(); x.imageSmoothingEnabled = false; x.globalAlpha = V.FLICK.alpha; x.translate(pb.X, pb.Y); x.scale(pb.scx, pb.scy); if (pb.rot) x.rotate(-pb.rot); x.drawImage(silC, -pb.px, -pb.py); x.restore(); return true;
    }
    function drawDream(x) {
      const d = V.dreamAt(pnow() - OM.dream0); if (!d || !S().sleeping) return false; const pr = R.petRect; if (!pr) return false;
      const B = asset('omen_dream_bubble', d.f), hx = Math.round(pr.x + pr.w / 2) + V.DREAM.dx, hy = Math.round(pr.y) + V.DREAM.dy;
      if (d.puff != null) { const rx = R.rx, fp = rx && rx.fx && rx.fx.fx_puff, im = fp && rx.img[fp.file]; if (im) x.drawImage(im, Math.min(2, d.puff) * fp.frameW, 0, fp.frameW, fp.frameH, ox(hx + 16 - fp.pivot[0]), oy(hy - 12 - fp.pivot[1]), fp.frameW, fp.frameH); return true; }
      if (B) {
        if (R._b3bCc && R._b3bCc.g3d) { R.worldPush({ id: 'omen-dream', kind: 'omen', x: 0, z: 0, yLift: 52, src: { img: B.img, sx: B.sx, sy: 0, sw: B.sw, sh: B.sh, px: B.px, py: B.py }, shadow: false, hit: false }); return true; }
        x.drawImage(B.img, B.sx, 0, B.sw, B.sh, ox(hx - B.px), oy(hy - B.py), B.sw, B.sh);
      }
      if (d.icon) { const I = asset('omen_dream_icons', OM.icon), c0 = V.DREAM.center; if (I) x.drawImage(I.img, I.sx, 0, I.sw, I.sh, ox(hx - B.px + c0[0] - I.px), oy(hy - B.py + c0[1] - I.py + d.bob), I.sw, I.sh); }
      return true;
    }
    const RST = { flick: 0, dream: 0, visitor: 0 };
    R.b3bLayer = function (x, z, cc, base) {
      R._b3bCc = cc;
      if (!A.ready) return; const c = VS.cur;
      drawDecor(x, cc, z, base);
      if (c) { const front = c.y > base; if ((z === 'front') === front) { drawVisitor(x, c, cc); RST.visitor++; } if (z === 'front') drawProps(x, c, cc); }
      if (z === 'front' && !SC.cur) { if (OM.kind === 'flicker' && drawFlicker(x)) RST.flick++; if (OM.kind === 'dream' && drawDream(x)) RST.dream++; }
    };

    // ── ④ 進化大場面 ──
    const SC = { q: [], cur: null, force: false, hold: false, played: [] };
    const LAV_D = '#967EDC', SIL = '#FFF6DA', DIM = '30,22,48';
    function sceneOk(pr) { return !!(pr && A.ready && R.evoOK && R.evoOK[pr.from] && R.evoOK[pr.to] && D.FORMS[pr.from] && D.FORMS[pr.to]); }
    G.b3bEvo = function (e) {
      const pr = V.evoPair(e); if (!pr) return false;
      if (V.unlockComic(S(), pr.node, pr.route, G.now())) { note('comic', { node: pr.node, route: pr.route }); if (G.save) G.save(); }
      if (!(AUTO.scene || SC.force) || !sceneOk(pr)) return false;
      SC.q.push(e); note('sceneQ', { type: e.type }); return true;
    };
    function busyScene() { return petBusy() || UI.isModalOpen() || (UI.activePointers && UI.activePointers().length > 0) || !!(G.touchSt && G.touchSt.press) || !!drag || document.hidden; }
    function sceneStart() {
      const all = SC.q.splice(0), e = all[all.length - 1], pr = V.evoPair(e);
      if (VS.cur && (VS.cur.phase === 'enter' || VS.cur.phase === 'join' || VS.cur.phase === 'lead')) { release(); VS.cur.x = VS.cur.standX; VS.cur.y = GY; setPhase(VS.cur, 'stand'); }
      const oS = srcOf(pr.from, 'idle', 0), nS = srcOf(pr.to, 'idle', 0);
      SC.cur = { e, all, pr, t: 0, skip: false, oldH: oS ? oS.sh : 30, newH: nS ? nS.sh : 30, cues: {}, card: null };
      document.body.classList.add('b3b-evo'); catcher(true); tray(false);
      const b = G.beh; if (b) b.puppet = { x: 0, dir: 1, clip: 'idle', frame: 0, hidden: true };
      st().stats.scenes++; note('scene', { type: e.type, from: pr.from, to: pr.to, n: all.length });
    }
    function sceneEnd() {
      const c = SC.cur; if (!c) return; SC.cur = null; SC.hold = false; document.body.classList.remove('b3b-evo'); catcher(false); release();
      SC.played.push({ from: c.pr.from, to: c.pr.to, skip: c.skip }); if (SC.played.length > 10) SC.played.shift();
      const s = S(); for (const e of c.all) s.ev.push(Object.assign({}, e, { _b3b: true })); if (UI.processEvents) UI.processEvents(); if (G.save) G.save();
      note('sceneEnd', { skip: c.skip });
    }
    function sceneTap() {
      const c = SC.cur; if (!c) return; const to = V.skipTo(effT(c)); if (to == null) return;
      if (to === V.TL.reveal) { c.t = to; c.skip = true; st().stats.skips++; } else c.t = c.skip ? to - 100 : to; note('skip', { to });   // effT 喺跳過後快 100ms
    }
    const effT = (c) => c.skip && c.t >= V.TL.reveal ? c.t + 100 * clamp((c.t - V.TL.reveal) / 300, 0, 1) : c.t;   // 跳過：現身後 300ms 出名卡（原本 400）
    function sceneTick(dt) {
      if (!SC.cur) { if (SC.q.length && !busyScene()) sceneStart(); return; }
      const c = SC.cur; if (!SC.hold) c.t += dt * 1000; const t = effT(c);
      const cue = (k, at, fn) => { if (t >= at && !c.cues[k]) { c.cues[k] = 1; fn(); } };
      cue('reveal', 5600, () => SND(c.e.type === 'hatch' ? 'hatch' : 'evolve'));
      cue('card', 6000, () => UIS('cards', { n: 1 }));
      if (t >= V.TL.dur) sceneEnd();
    }
    let catchEl = null;
    function catcher(show) {
      if (!catchEl) { catchEl = document.createElement('div'); catchEl.id = 'b3bCatch'; catchEl.dataset.testid = 'b3b-evo-catch'; catchEl.style.cssText = 'position:fixed;inset:0;z-index:40;display:none;background:transparent';
        catchEl.addEventListener('pointerdown', (e) => { e.preventDefault(); sceneTap(); }); document.body.appendChild(catchEl); }
      catchEl.style.display = show ? 'block' : 'none';
    }
    function srcOf(fk, clip, i) {
      const F = D.FORMS[fk]; if (!F) return null; const A0 = R.atlas && R.atlas[F.atlas]; if (!A0) return null; const an = A0.json.animations;
      const fb = { emo_surprised: ['emo_surprised', 'glow', 'idle'], smug_pose: ['smug_pose', 'emo_happy', 'idle'], celebrate: ['celebrate', 'cheer_jump', 'emo_happy', 'idle'], idle: ['idle'] }[clip] || [clip, 'idle'];
      const k = fb.find(n => an[n]); if (!k) return null; return R.atlasSrc(F.atlas, k, i);
    }
    const fpsOf = (fk, clip) => { const F = D.FORMS[fk], A0 = F && R.atlas && R.atlas[F.atlas], an = A0 && A0.json.animations[clip]; return (an && an.fps) || 8; };
    const silCache = new Map();
    function silOf(src, outline) {   // 剪影（#FFF6DA）＋ 1px LAV_D 外框；cache by 幀
      const key = src.sx + ',' + src.sy + ',' + src.sw + ',' + src.sh + ',' + (outline ? 1 : 0) + ',' + (src.img.src || '').slice(-40); let c = silCache.get(key); if (c) return c;
      const w = src.sw + 2, h = src.sh + 2, a = document.createElement('canvas'); a.width = w; a.height = h; const g = a.getContext('2d');
      g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 1, 1, src.sw, src.sh); g.globalCompositeOperation = 'source-in'; g.fillStyle = SIL; g.fillRect(0, 0, w, h);
      let out = a;
      if (outline) { const o = document.createElement('canvas'); o.width = w; o.height = h; const q = o.getContext('2d'), t2 = document.createElement('canvas'); t2.width = w; t2.height = h; const tq = t2.getContext('2d');
        tq.drawImage(a, 0, 0); tq.globalCompositeOperation = 'source-in'; tq.fillStyle = LAV_D; tq.fillRect(0, 0, w, h);
        for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) q.drawImage(t2, dx, dy); q.drawImage(a, 0, 0); out = o; }
      c = { img: out, sx: 0, sy: 0, sw: w, sh: h, px: src.px + 1, py: src.py + 1 }; if (silCache.size > 400) silCache.clear(); silCache.set(key, c); return c;
    }
    const blit = (g, s0, x, y, sx, sy) => { if (!s0) return; g.save(); g.translate(Math.round(x), Math.round(y)); if (sx != null) g.scale(sx, sy); g.drawImage(s0.img, s0.sx, s0.sy, s0.sw, s0.sh, -s0.px, -s0.py, s0.sw, s0.sh); g.restore(); };
    let cardC = null;
    function cardCanvas(c, fr) {
      const J = A.json.evolution.cards, rk = (J.formToCard[c.pr.to] || 'card_base').replace('card_', ''), cf = J.files[rk] || J.files.base, im = A.img[cf.file], K = 4;
      if (!cardC) { cardC = document.createElement('canvas'); cardC.width = J.w * K; cardC.height = J.h * K; }
      const g = cardC.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, cardC.width, cardC.height); g.imageSmoothingEnabled = false;
      if (im) g.drawImage(im, 0, 0, J.w * K, J.h * K); else { g.fillStyle = '#2b2140'; g.fillRect(0, 0, J.w * K, J.h * K); }
      const ns = srcOf(c.pr.to, 'idle', 0), pp = J.portrait.petPivot;
      if (ns) { g.save(); g.scale(K, K); g.drawImage(ns.img, ns.sx, ns.sy, ns.sw, ns.sh, pp[0] - ns.px, pp[1] - ns.py, ns.sw, ns.sh); g.restore(); }
      const name = (J.formName[c.pr.to] || '').slice(0, fr.nameN), line = (V.CARD_LINE[c.pr.to] || '').slice(0, fr.lineN), nb = J.textBoxes.name, lb = J.textBoxes.line;
      g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.font = 'bold ' + (11 * K) + 'px ' + (G.v3 && G.v3.on && G.v3.on() ? '"GlimmerV3Sans",' : '') + '"Noto Sans HK","PingFang HK","Microsoft JhengHei",sans-serif';
      g.fillText(name, nb[0] * K, (nb[1] + nb[3]) / 2 * K, (nb[2] - nb[0]) * K);
      g.fillStyle = '#5a3a22'; g.font = (7.5 * K) + 'px ' + (G.v3 && G.v3.on && G.v3.on() ? '"GlimmerV3Sans",' : '') + '"Noto Sans HK","PingFang HK","Microsoft JhengHei",sans-serif'; g.textBaseline = 'top';
      const maxW = (lb[2] - lb[0]) * K; let ln = '', y = lb[1] * K + 1 * K; for (const ch of line) { if (g.measureText(ln + ch).width > maxW && !/[。，、！？」…）]/.test(ch)) {   // 標點唔好孤零零落第二行
         g.fillText(ln, lb[0] * K, y); ln = ch; y += 10 * K; } else ln += ch; } if (ln) g.fillText(ln, lb[0] * K, y);
      c.card = { name, line, nameN: fr.nameN, lineN: fr.lineN }; return cardC;
    }
    R.b3bOverlay = function (ctx, k) {
      const c = SC.cur; if (!c) return; const t = effT(c), PX = CX, PY = GY, F = V.evoFrame(t, PX, PY, c.oldH, c.newH), W = 195, H = 422;
      ctx.save(); ctx.setTransform(k, 0, 0, k, 0, 0); ctx.imageSmoothingEnabled = false;
      ctx.fillStyle = 'rgba(' + DIM + ',' + F.dim.toFixed(3) + ')'; ctx.fillRect(0, 0, W, H);
      if (F.rays) blit(ctx, asset('evo_rays', F.rays.f), F.cx, F.cy);
      const p = F.pet, fo = c.pr.from, fn = c.pr.to;
      if (p.show === 'old' || p.show === 'new') {
        const fk = p.show === 'old' ? fo : fn, clip = p.clip || 'idle', i = Math.floor((p.show === 'new' ? t - 5600 : t) / 1000 * fpsOf(fk, clip));
        let s0 = srcOf(fk, p.sil ? 'idle' : clip, p.sil ? 0 : i); if (s0 && p.sil) s0 = silOf(s0, t >= 1500);
        blit(ctx, s0, PX + p.dx, PY, p.sx, p.sy);
      } else if (p.show === 'cocoon' && t < 2700) { const s0 = srcOf(fo, 'idle', 0); if (s0) blit(ctx, silOf(s0, true), PX, PY); }
      if (F.cocoon) blit(ctx, asset(F.cocoon.id, F.cocoon.f), PX, PY, F.cocoon.sx, F.cocoon.sy);
      for (const m of F.motes) blit(ctx, asset('evo_mote', m.f), m.x, m.y);
      for (const m of F.shards) blit(ctx, asset('evo_shard', m.f), m.x, m.y);
      if (F.ring) blit(ctx, asset('evo_ring', F.ring.f), F.ring.x, F.ring.y);
      for (const m of F.confetti) if (m.y < 430) blit(ctx, asset('evo_confetti', m.f), m.x, m.y);
      if (F.flash > 0) { ctx.fillStyle = 'rgba(255,255,255,' + F.flash.toFixed(3) + ')'; ctx.fillRect(0, 0, W, H); }
      if (F.skip) blit(ctx, asset('evo_skip_hint', F.skip.f), F.skip.x, F.skip.y);
      if (F.card && F.card.sc > 0.05) { const cv = cardCanvas(c, F.card), J = A.json.evolution.cards; ctx.save(); ctx.imageSmoothingEnabled = true; ctx.globalAlpha = clamp(F.card.al, 0, 1);
        ctx.translate(F.card.x, F.card.y); ctx.rotate(F.card.rot * Math.PI / 180); ctx.scale(F.card.sc, F.card.sc); ctx.drawImage(cv, -J.w / 2, -J.h / 2, J.w, J.h); ctx.restore(); }
      c.last = { t: Math.round(t), dim: +F.dim.toFixed(3), pet: p.show, sil: !!p.sil, cocoon: F.cocoon ? F.cocoon.id : null, motes: F.motes.length, shards: F.shards.length, ring: !!F.ring, rays: !!F.rays, confetti: F.confetti.length, flash: +F.flash.toFixed(2), skipHint: !!F.skip, card: F.card ? { sc: +F.card.sc.toFixed(3), al: +F.card.al.toFixed(2) } : null };
      ctx.restore();
    };

    // ── 圖鑑「團絨日記」──
    G.b3bDex = function () {
      const o = st(), sec = document.createElement('div'); sec.dataset.testid = 'dex-comics'; sec.style.cssText = 'grid-column:1/-1;margin-top:8px';
      const n = V.NODES.filter(k => o.comics[k]).length;
      sec.innerHTML = '<b style="font-size:12px">團絨日記 ' + n + '／' + V.NODES.length + '</b>';
      const row = document.createElement('div'); row.style.cssText = 'display:grid;grid-template-columns:repeat(5,1fr);gap:4px;margin-top:4px';
      V.NODES.forEach((k, i) => {
        const cm = o.comics[k], cell = document.createElement('div'); cell.dataset.testid = 'dex-comic-' + k; cell.dataset.got = cm ? '1' : '0';
        cell.style.cssText = 'font-size:10px;padding:3px 1px;border-radius:6px;text-align:center;cursor:' + (cm ? 'pointer' : 'default') + ';background:' + (cm ? '#f3e1b8;color:#4a2e1a' : 'rgba(255,255,255,.12)');
        if (cm && A.json) { const pn = V.comicPanels(k, cm.routes[cm.routes.length - 1], A.json.comics); cell.innerHTML = '<img src="' + BASE + pn[0].file + '" style="width:100%;image-rendering:pixelated;border-radius:4px;display:block"><span>第 ' + (i + 1) + ' 話</span>'; cell.addEventListener('click', () => openComic(k)); }
        else cell.innerHTML = '<div style="padding:12px 0">？？？</div><span>第 ' + (i + 1) + ' 話</span>';
        row.appendChild(cell);
      });
      sec.appendChild(row); return sec;
    };
    let comicEl = null;
    function openComic(node, route) {
      const o = st(), cm = o.comics[node]; if (!cm || !A.json) return false; const J = A.json.comics, rt = route || cm.routes[cm.routes.length - 1] || null, pn = V.comicPanels(node, rt, J);
      if (!comicEl) { comicEl = document.createElement('div'); comicEl.id = 'b3bComic'; comicEl.dataset.testid = 'b3b-comic'; comicEl.style.cssText = 'position:fixed;inset:0;z-index:60;display:none;align-items:center;justify-content:center;background:rgba(20,14,32,.82)'; document.body.appendChild(comicEl);
        comicEl.addEventListener('click', (e) => { if (e.target === comicEl || (e.target.dataset && e.target.dataset.close)) closeComic(); }); }
      const vw = Math.min(window.innerWidth * 0.96, (window.innerHeight * 0.94) * 195 / 422, 420), k = vw / 195, L = J.layout.pos, idx = V.NODES.indexOf(node) + 1;
      let h = '<div data-testid="b3b-comic-page" data-node="' + node + '" data-route="' + (rt || '') + '" style="position:relative;width:' + vw + 'px;height:' + (422 * k) + 'px;background:#fbf3e2;border-radius:' + (6 * k) + 'px;box-shadow:0 6px 24px rgba(0,0,0,.4);color:#4a2e1a;font-family:inherit">';
      h += '<div style="position:absolute;left:0;right:0;top:' + (18 * k) + 'px;text-align:center;font-weight:bold;font-size:' + (11 * k) + 'px">團絨日記・第 ' + idx + ' 話</div>';
      if (node === 'n4' || node === 'n5') { h += '<div style="position:absolute;left:0;right:0;top:' + (36 * k) + 'px;text-align:center;font-size:' + (6.5 * k) + 'px">' + cm.routes.map(r => '<span data-testid="b3b-comic-route-' + r + '" data-route="' + r + '" style="margin:0 ' + (2 * k) + 'px;padding:0 ' + (3 * k) + 'px;border-radius:' + (3 * k) + 'px;cursor:pointer;' + (r === rt ? 'background:#8a4f2a;color:#fff' : 'background:rgba(138,79,42,.15)') + '">' + (V.ROUTE_ZH[r] || r) + '</span>').join('') + '</div>'; }
      pn.forEach((p, i) => { const [x, y] = L[i];
        h += '<img data-testid="b3b-comic-panel-' + (i + 1) + '" src="' + BASE + p.file + '" style="position:absolute;left:' + (x * k) + 'px;top:' + (y * k) + 'px;width:' + (J.panelW * k) + 'px;height:' + (J.panelH * k) + 'px;image-rendering:pixelated">';
        h += '<div data-testid="b3b-comic-cap-' + (i + 1) + '" style="position:absolute;left:' + (x * k) + 'px;top:' + ((y + 86) * k) + 'px;width:' + (92 * k) + 'px;height:' + (18 * k) + 'px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:' + (6.2 * k) + 'px;line-height:1.15">' + p.cap.replace(/</g, '&lt;') + '</div>'; });
      h += '<div data-close="1" data-testid="b3b-comic-close" style="position:absolute;left:50%;transform:translateX(-50%);top:' + (392 * k) + 'px;padding:' + (3 * k) + 'px ' + (14 * k) + 'px;border-radius:' + (8 * k) + 'px;background:#8a4f2a;color:#fff;font-size:' + (8 * k) + 'px;cursor:pointer">關閉</div></div>';
      comicEl.innerHTML = h; comicEl.style.display = 'flex';
      comicEl.querySelectorAll('[data-route]').forEach(el => { if (el.dataset.testid && el.dataset.testid.indexOf('b3b-comic-route-') === 0) el.addEventListener('click', (e) => { e.stopPropagation(); openComic(node, el.dataset.route); }); });
      UIS('cards', { n: 4 }); note('comicOpen', { node, route: rt }); return true;
    }
    function closeComic() { if (comicEl) comicEl.style.display = 'none'; }

    // ── 種子：蘑菇婆婆送嘅免費種子（下次種花唔使碎）──
    if (X2 && X2.plant && X && X.st) { const p0 = X2.plant; X2.plant = function (s, i, k, t) {
      const o = V.st(s), price = (D.PARAMS.systems12b.garden || {}).seedPrice || 0; if (o.seeds < 1 || !price) return p0.apply(this, arguments);
      const w = X.st(s).wallet; w.total += price; const r = p0.apply(this, arguments); if (r && r.ok) { V.useSeed(s); r.free = true; r.price = 0; } else w.total -= price; return r; }; }

    // ── CSS ──
    { const css = document.createElement('style'); css.textContent = 'body.b3b-evo #ui>*:not(#hit):not(#hdFx),body.b3b-evo #b3bTray{visibility:hidden!important}'; document.head.appendChild(css); }

    /* 每幀 */
    G.b3bSpawn = (who, o) => spawn(who, o);   // 4a：蝸牛郵差送細佬蛋
    G.b3bTick = function (dt) {
      dt = Math.min(0.1, dt || 0); sceneTick(dt);
      if (!SC.cur) visitTick(dt); else if (VS.cur) VS.cur.ct += dt * 1000;
      omenTick();
      const b = G.beh, cg = pnow() - GEST.cheer;   // 送禮後團絨 visit_gift_cheer（舊形態有反應圖先播；evo 形態 celebrate）
      if (b && cg < 1200 && !b.puppet && !(G.touchSt && G.touchSt.act) && !b.gest) b.gest = { key: 'v_gift_cheer', clip: 'visit_gift_cheer', ms: cg, sx: 1, sy: 1, dx: 0, dy: 0, rot: 0, rx: true };
    };

    window.__qa = window.__qa || {};
    window.__qa.b3b = {
      st: () => { const c = VS.cur; return { ready: A.ready, errors: A.errors.slice(), auto: Object.assign({}, AUTO), vs: c ? { who: c.who, phase: c.phase, x: +c.x.toFixed(1), y: +c.y.toFixed(1), dir: c.dir, clip: c.clip, side: c.side, letter: c.letter ? c.letter.st : null, seed: !!c.seed, meter: c.meter > 0, hit: hitRect(c), letterRect: letterRect(c), head: anchor(c, 'head'), bag: anchor(c, 'bag') } : null,
        save: JSON.parse(JSON.stringify(st())), scene: SC.cur ? { t: Math.round(SC.cur.t), eff: Math.round(effT(SC.cur)), skip: SC.cur.skip, from: SC.cur.pr.from, to: SC.cur.pr.to, last: SC.cur.last || null, card: SC.cur.card } : null, q: SC.q.length, played: SC.played.slice(),
        omen: { kind: OM.kind, force: OM.force }, render: Object.assign({}, RST), tray: trayOn, items: V.giftItems(S(), SB()), log: log.slice(), puppet: G.beh && G.beh.puppet ? Object.assign({}, G.beh.puppet) : null, hud: document.body.classList.contains('b3b-evo') }; },
      spawn: (who, side, force) => spawn(who, { side, force: force !== false }),
      phase: (ph) => { const c = VS.cur; if (!c || PHASES.indexOf(ph) < 0) return false; if (ph === 'stand') { release(); c.x = c.standX; c.y = GY; setPhase(c, 'stand'); arrived(c); } else setPhase(c, ph); return true; },
      leave: (now) => leave(!!now), gift: (it) => doGift(it || V.giftItems(S(), SB())[0]), card: () => VS.cur && visitorCard(VS.cur), buy: (id) => buyDecor(id), letter: () => VS.cur && VS.cur.letter ? readLetter(VS.cur) : null,
      until: (ms) => { if (VS.cur) VS.cur.until = pnow() + ms; },
      evo: (e, force) => { if (force !== false) SC.force = true; const r = G.b3bEvo(Object.assign({}, e)); return r; },
      sceneAt: (ms, hold) => { if (!SC.cur && SC.q.length) sceneStart(); if (!SC.cur) return false; SC.cur.t = ms; SC.hold = hold !== false; return true; },
      hold: (h) => { SC.hold = !!h; }, skip: () => sceneTap(), sceneOk: (e) => sceneOk(V.evoPair(e)),
      omen: (k) => { OM.force = k || null; OM.chk = -1e9; OM.flickNext = 0; OM.dreamNext = 0; return true; }, fed: () => omenFed(),
      comic: (node, route) => openComic(node, route), closeComic: () => closeComic(), unlock: (node, route) => { const r = V.unlockComic(S(), node, route, G.now()); if (G.save) G.save(); return r; },
      props: (o) => { const c = VS.cur; if (!c) return false; if (o.letter) c.letter = { st: o.letter, t: 0 }; if (o.heart) c.hearts.push({ t: o.heartT || 300 }); if (o.meter) c.meter = 2600; return true; },
      css: (x, y) => { const r = R.canvas.getBoundingClientRect(); return { x: r.left + x / 195 * r.width, y: r.top + y / 422 * r.height }; },
      auto: (k, v) => { AUTO[k] = !!v; return Object.assign({}, AUTO); }, sess: (ms) => { sess.t0 = pnow() - (ms || 0); sess.delay = 0; },
    };
    return true;
  }
  return { install };
});
