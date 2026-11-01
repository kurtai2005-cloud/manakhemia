/* 《微光小圃》 long5aui.js — 第 5 批 5a 長線養成介面（docs-gdd/series2-4a4b-spec.md §5a＋定案；遊美 art/series2_long/5a）。原創代碼。
   邏輯全部喺 long5a.js（s.fam）；呢度只做：每秒 scan（經驗／升級／開房／排新蛋）、新蛋二揀一、寵物卡（做主養／打招呼／搬房）、
   家族升級彈窗、族譜（Lv10 金色）、花園 rail「新蛋」掣、🛠 開發者模式「5a」。UI v2 皮（G.ui2）；v1 有簡單後備樣。
   圖一律用 Image.src（單檔 build shim 攔截）；v2 kit 用 dataURL。?l5=0／?house=0／?s2=0 全停；?ev=0（測試）唔自動彈窗、唔出 toast。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5aui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const FAM = NS.long5a, SR = NS.series2, HS = NS.house, UI = NS.ui, SIM = NS.sim; if (!FAM || !SR || !HS || !UI || !G.s2Art) return false;
    const qs = new URLSearchParams(location.search); if (qs.get('l5') === '0' || qs.get('house') === '0' || qs.get('s2') === '0') return false;
    const QUIET = qs.get('ev') === '0';
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now(), SA = G.s2Art, R = G.renderer, LB = 'art/series2_long/';
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const SND = (k, i) => { const a = NS.audio; if (a && a.Engine) try { a.Engine.notify(k, i || {}); } catch (e) { } };
    const fmt = (t, o) => t.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m));
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2000); };
    const trFk = () => (G.house5 && G.house5.trFk ? G.house5.trFk() : R && R.fkOf ? R.fkOf(S()) : 'sprout');
    const kidFk = () => { try { const f = SA.formNow(); return f && f !== 'egg' ? f : null; } catch (e) { return null; } };
    const env = () => ({ rebirth: SIM && SIM.rebirth ? (s, t, g) => SIM.rebirth(s, t, g) : null, trFk: trFk(), kidFk: kidFk() });
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const ui5 = (n) => LB + '5a/ui/' + n + '@3x.png';
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const F8 = () => (U() ? '"GlimmerFP8",' : '') + FALL, F12 = () => (U() ? '"GlimmerFP12",' : '') + FALL;
    const CREAM = '#FFF5DC', LINE = '#24172C', GOLD = '#FFE08A', INK = '#3A2840';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const a2 = (v) => Math.round(v * 2);
    // v2 kit 九宮格；v1 後備
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;', card_sel: 'background:#3A3466;border:3px solid #FFE08A;border-radius:8px;',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', plaque: 'background:#E9D7A8;border:3px solid #6B4A2E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      btn_violet: 'background:#9C86D8;border:3px solid #3C2E6A;border-radius:8px;', btn_dis: 'background:#8C8796;border:3px solid #4A4656;border-radius:8px;', btn16_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn16_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      btn16_violet: 'background:#9C86D8;border:3px solid #3C2E6A;border-radius:8px;', btn16_dis: 'background:#8C8796;border:3px solid #4A4656;border-radius:8px;', tree_node: 'background:#2E2A58;border:3px solid #C9B27A;border-radius:8px;', tree_node_gold: 'background:#5A4320;border:3px solid #FFE08A;border-radius:8px;',
      tree_node_sel: 'background:#21485A;border:3px solid #6FE0D0;border-radius:8px;', pill_pri: 'background:#F3A64A;border-radius:10px;', pill_sec: 'background:#69B7C9;border-radius:10px;', pill_violet: 'background:#9C86D8;border-radius:10px;', pill_dis: 'background:#8C8796;border-radius:10px;', pill_navy: 'background:#2A2450;border-radius:10px;',
      med40_gold: 'background:#F6C85A;border:4px solid #6B3A1E;border-radius:50%;', close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;', chip: 'background:#2A2450;border:2px solid #C9B27A;border-radius:8px;', panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', bar_trough_h7: 'background:#1E1A3E;border-radius:4px;', card_locked: 'background:#4A4656;border:3px solid #6E6A7A;border-radius:8px;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || FB[n] || ''; };
    const icCss = (n, px) => { const u = U(); const c = u ? u.ic(n) : ''; if (!c) return ''; return c + (px ? `transform:scale(${px / 32});transform-origin:0 0;` : ''); };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const icon = (n, size, css) => { const d = mk('i', `position:absolute;display:block;pointer-events:none;width:${size}px;height:${size}px;` + (css || '')); const c = icCss(n, 0); if (c) { d.style.cssText += c + `width:${size}px !important;height:${size}px !important;background-size:${size}px ${size}px !important;`; } else { const im = img(ui5('icon_' + n), `left:0;top:0;width:${size}px;height:${size}px`); d.appendChild(im); } return d; };
    const TXT = (size, color, extra) => `font:${size}px/1.2 ${size >= 22 ? F12() : F8()};color:${color || CREAM};${color === INK ? '' : OL}-webkit-font-smoothing:none;` + (extra || '');
    function btn(label, kind, w, h, tid, onClick, icn) {
      const b = mk('div', `position:absolute;width:${w}px;height:${h}px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;${bi(kind)}` + TXT(h >= 34 ? 18 : 16), null, tid);
      if (icn) { const ii = icon(icn, 22, 'position:relative'); b.appendChild(ii); } b.appendChild(mk('span', 'position:relative', label));
      b.addEventListener('click', (e) => { e.stopPropagation(); if (b.dataset.dis === '1') { if (b._why) toast(b._why, 1600); UIS('tap'); return; } UIS('tap'); onClick && onClick(e); });
      return b;
    }

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l5css';
    css.textContent = `#l5ov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:58;user-select:none;-webkit-user-select:none;touch-action:manipulation}
#l5ov .bd{position:absolute;inset:0;background:rgba(18,12,30,.62)}
body.l5-on #toast{z-index:70 !important}
#l5ov .rays{position:absolute;left:55px;top:160px;width:280px;height:280px;border-radius:50%;background:repeating-conic-gradient(rgba(255,224,138,.35) 0 10deg,rgba(255,224,138,0) 10deg 22deg);-webkit-mask:radial-gradient(circle,#000 30%,transparent 70%);mask:radial-gradient(circle,#000 30%,transparent 70%);animation:l5spin 8s linear infinite;pointer-events:none}
@keyframes l5spin{to{transform:rotate(360deg)}}
@keyframes l5pop{0%{transform:translate(-50%,-50%) scale(.6)}70%{transform:translate(-50%,-50%) scale(1.08)}100%{transform:translate(-50%,-50%) scale(1)}}
@keyframes l5mote{0%{opacity:0;transform:translateY(0)}30%{opacity:1}100%{opacity:0;transform:translateY(-60px)}}
@keyframes l5bob{0%,100%{transform:translate(-50%,-50%)}50%{transform:translate(-50%,calc(-50% - 4px))}}
#l5ov .mote{position:absolute;width:6px;height:6px;background:${GOLD};box-shadow:0 0 6px ${GOLD};animation:l5mote 2.4s ease-out infinite;pointer-events:none}
#l5ov .scr{position:absolute;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none}
#l5ov .scr::-webkit-scrollbar{display:none}
#l5ov .row{position:relative;display:flex;gap:14px 10px;justify-content:center;flex-wrap:wrap;padding:30px 6px 14px}
#l5ov .node{position:relative;flex:0 0 168px;width:168px;height:112px;box-sizing:border-box;cursor:pointer}
#l5ov .node.mem{filter:saturate(.35) brightness(.8)}
#l5egg{cursor:pointer}
#l5egg > i.i{position:absolute;left:50%;top:50%;width:36px;height:36px;margin:-18px 0 0 -18px;pointer-events:none}
#l5egg > i.i > img{animation:l5egb 1.6s ease-in-out infinite}
@keyframes l5egb{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}`;
    document.head.appendChild(css);

    // ── 疊層 ──
    const OV = { el: null, kind: null, data: null, opened: 0 };
    function ov(kind, data) {
      closeOv(true); const host = document.getElementById('ui') || document.body;
      const el = OV.el = mk('div', '', null, 'l5-' + kind); el.id = 'l5ov'; el.dataset.kind = kind; OV.kind = kind; OV.data = data || null; OV.opened = pnow();
      el.appendChild(mk('div', '', null)).className = 'bd'; el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      host.appendChild(el); document.body.classList.add('l5-on'); note('ov', { kind }); return el;
    }
    function closeOv(quiet) { if (!OV.el) return false; const k = OV.kind; OV.el.remove(); OV.el = null; OV.kind = null; OV.data = null; document.body.classList.remove('l5-on'); if (!quiet) note('ovClose', { kind: k }); return true; }
    const busy = () => !!OV.el || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene') || (G.house5 && G.house5.isOpen() && window.__qa && __qa.house && __qa.house.st().deco);

    // ── 頭像（canvas；團絨 atlas／細佬 strip／蛋 icon） ──
    function fkOfNode(n) {
      if (n.fk) return n.fk; if (n.kind === 'kid') return n.id === FAM.kidId(S()) ? kidFk() : null;
      if (n.id === FAM.trId(S())) return trFk(); try { return R && R.fkOf ? R.fkOf({ stage: 'elder', form: n.form, gen: n.gen }) : null; } catch (e) { return null; }
    }
    const TRIM = new Map();
    function trim(src) {   // 透明邊裁走（頭像放大啲）
      const key = (src.img.src || '').slice(-40) + ':' + src.sx + ':' + src.sy + ':' + src.sw + ':' + src.sh; if (TRIM.has(key)) return TRIM.get(key); let r = { x: 0, y: 0, w: src.sw, h: src.sh };
      try { const c = document.createElement('canvas'); c.width = src.sw; c.height = src.sh; const g = c.getContext('2d'); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 0, 0, src.sw, src.sh); const d = g.getImageData(0, 0, src.sw, src.sh).data;
        let x0 = src.sw, y0 = src.sh, x1 = -1, y1 = -1; for (let y = 0; y < src.sh; y++) for (let x = 0; x < src.sw; x++) if (d[(y * src.sw + x) * 4 + 3] > 16) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
        if (x1 >= x0) r = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 }; } catch (e) { }
      TRIM.set(key, r); return r;
    }
    function portrait(n, size) {
      const c = mk('canvas', `position:absolute;width:${size}px;height:${size}px;image-rendering:pixelated;pointer-events:none`); c.width = size; c.height = size; c.dataset.fk = '';
      const egg = /蛋$/.test(n.name || ''); let tries = 0;
      const draw = () => {
        const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, size, size);
        if (egg) { const i = new Image(); i.onload = () => { g.imageSmoothingEnabled = false; g.drawImage(i, 0, 0, size, size); }; i.src = ui5(n.kind === 'kid' ? 'icon_egg_kid' : 'icon_egg_tr'); c.dataset.fk = 'egg'; return true; }
        const fk = fkOfNode(n); if (!fk) return false; let src = null;
        if (n.kind === 'kid') { const im = SA.strip(fk, 'idle'); if (im && im.complete !== false && im.width) src = { img: im, sx: 0, sy: 0, sw: 48, sh: 48 }; }
        else { const a = SA.atlasSrc(fk, 'idle', 0, true); if (a && a.src && a.src.img && a.src.img.width) src = a.src; }
        if (!src) return false; const bb = trim(src); const k = Math.max(1, Math.floor((size * 0.86) / Math.max(bb.w, bb.h))), w = bb.w * k, h = bb.h * k;
        g.drawImage(src.img, src.sx + bb.x, src.sy + bb.y, bb.w, bb.h, Math.round((size - w) / 2), Math.round((size - h) / 2), w, h); c.dataset.fk = fk; return true;
      };
      const go = () => { if (!c.isConnected && tries > 0 && !OV.el) return; if (!draw() && ++tries < 16) setTimeout(go, 250); }; setTimeout(go, 0); return c;
    }

    // ── 每秒 scan ──
    const T = { last: 0, n: 0, evs: [], snz: null, autoOffer: -1, lastLvShow: 0 };
    function tick(force) {
      const t = pnow(); if (!force && t - T.last < 1000) return; T.last = t; const s = S(); if (!s) return; T.n++;
      let ev; try { ev = FAM.scan(s, now(), { kidFk: kidFk() }); } catch (e) { note('scanErr', { e: String(e && e.message || e) }); return; }
      const o = FAM.st(s); let dirty = ev.length > 0, rooms = [];
      for (const e of ev) {
        T.evs.push(Object.assign({ at: Math.round(t) }, e)); if (T.evs.length > 60) T.evs.shift();
        if (e.k === 'init') { o.lvQ.length = 0; o.lvSeen = o.lv; if (o.lv > 1 && !QUIET) toast('家族等級 Lv' + o.lv + '（按以前養過嘅計）', 2400); note('init', { lv: o.lv, xp: o.xp }); }
        else if (e.k === 'rooms') rooms = rooms.concat(e.opened);
        else if (e.k === 'offer' && !QUIET) toast('細佬大咗！明日蝸牛郵差會送新蛋嚟', 2400);
      }
      if (rooms.length && !ev.some(e => e.k === 'init')) note('rooms', { rooms: rooms.map(r => r.room) });
      if (dirty) { save(); if (G.house5 && G.house5.isOpen()) G.house5.refresh(); }
      eggTick();
      if (!QUIET && !busy()) {
        if (o.lvQ.length) levelUp(); else if (FAM.offerReady(s, now()) && T.autoOffer !== SR.dayNum(now()) && !(o.offer && o.offer.snz === SR.dayNum(now()))) { T.autoOffer = SR.dayNum(now()); offer('auto'); }
      }
    }

    // ── 花園 rail「新蛋」掣 ──
    const EB = { el: null };
    function eggTick() {
      const s = S(), show = FAM.offerReady(s, now()) && !document.body.classList.contains('s2-scene'); let el = EB.el;
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), host = rail || document.getElementById('top-r'); if (!host) return;
        el = EB.el = mk('div', '', null, 'l5-rail-egg'); el.id = 'l5egg'; el.className = 'ibtn panel'; el.title = '新蛋';
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l">新蛋</i><i class="rd"></i>';
        el.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); offer('rail'); }); host.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return;
      const u = U(), ic = el.querySelector('i.i'), rl = u && u.rail; if (rl && rl.kid && rl.dex) { el.style.left = rl.kid.x + 'px'; el.style.top = (rl.kid.y + (rl.kid.y - rl.dex.y)) + 'px'; } else { el.style.left = '360px'; el.style.top = '320px'; }
      const k = u ? 'v2' : 'v1'; if (ic && ic.dataset.k !== k) { ic.dataset.k = k; ic.innerHTML = ''; ic.appendChild(img(ui5('icon_egg_kid'), 'left:0;top:0;width:36px;height:36px')); }
    }

    // ── 新蛋二揀一 ──
    function offer(from) {
      const s = S(), c = FAM.choices(s, now()), el = ov('offer', { from });
      const P = mk('div', `position:absolute;left:${a2(14)}px;top:${a2(104)}px;width:${a2(167)}px;height:${a2(196)}px;box-sizing:border-box;${bi('panel_navy')}`); el.appendChild(P);
      const pl = mk('div', `position:absolute;left:50%;top:${a2(96) - 20}px;transform:translateX(-50%);width:${a2(104)}px;height:40px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;${bi('plaque_pri')}` + TXT(20), '新蛋嚟咗！', 'l5-offer-title'); el.appendChild(pl);
      el.appendChild(mk('div', `position:absolute;left:0;width:390px;top:${a2(124) - 10}px;text-align:center;` + TXT(14), '揀一隻嚟養（最多養 2 隻）'));
      const card = (which, x, ok, why) => {
        const png = which === 'tr' ? 'egg_choice_tr' : (!ok && c.kid.reason === 'raising' ? 'egg_choice_kid_disabled' : 'egg_choice_kid');
        const d = mk('div', `position:absolute;left:${a2(x)}px;top:${a2(134)}px;width:${a2(72)}px;height:${a2(128)}px;cursor:pointer`, null, 'l5-pick-' + which); d.dataset.ok = ok ? '1' : '0'; d.dataset.reason = ok ? '' : why.reason;
        const im = img(LB + '5a/ui/' + png + '@3x.png', `left:-4px;top:-4px;width:${a2(72) + 8}px;height:${a2(128) + 8}px;object-fit:fill;` + (!ok && png !== 'egg_choice_kid_disabled' ? 'filter:grayscale(1) brightness(.72);' : '')); d.appendChild(im);
        if (!ok && png !== 'egg_choice_kid_disabled') d.appendChild(mk('div', `position:absolute;left:8px;right:8px;top:${a2(244 - 134) - 8}px;height:40px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;${bi('btn16_dis')}` + TXT(13), why.reason === 'full' ? '屋企住滿' : why.reason === 'mainYoung' ? '主養未到靜光' : why.zh, 'l5-pick-' + which + '-why'));
        if (!ok) d.appendChild(icon('lock', 28, `left:${a2(72) / 2 - 14}px;top:16px`));
        d.addEventListener('click', (e) => { e.stopPropagation(); if (!ok) { toast(why.zh, 2000); UIS('tap'); return; } doPick(which); });
        P.parentNode.appendChild(d);
      };
      card('tr', 22, c.tr.ok, c.tr); card('kid', 101, c.kid.ok, c.kid);
      const later = btn('遲啲先', 'btn16_violet', 160, 40, 'l5-later', () => { const o = FAM.st(S()); if (o.offer) o.offer.snz = SR.dayNum(now()); save(); closeOv(); note('later'); });
      later.style.left = (195 - 80) + 'px'; later.style.top = a2(306) + 'px'; el.appendChild(later);
      SND('reward'); note('offer', { from, tr: c.tr.ok, kid: c.kid.ok, why: [c.tr.reason || '', c.kid.reason || ''] }); return { ok: true, choices: c };
    }
    function doPick(which) {
      const s = S(), r = FAM.pick(s, which, now(), env()); note('pick', { which, ok: r.ok, reason: r.reason || '' });
      if (!r.ok) { toast(r.zh || '揀唔到', 2000); return r; }
      save(); closeOv(); SND('reward');
      const mv = r.moved ? fmt(r.moved.kind === 'tr' ? FAM.LINES.moveTr : FAM.LINES.moveKid, { name: r.moved.name, room: FAM.ROOM[r.moved.room].zh }) : '';
      toast((which === 'tr' ? FAM.LINES.newTr : FAM.LINES.newKid) + (mv ? '・' + mv : ''), 3000);
      if (G.house5 && G.house5.isOpen()) G.house5.refresh(); tick(true); return r;
    }

    // ── 寵物卡 ──
    function nodeOf(id) { const t = FAM.tree(S(), now(), { trFk: trFk(), kidFk: kidFk() }); return t.nodes.find(n => n.id === id) || null; }
    function card(id) {
      const s = S(), n = nodeOf(id); if (!n) return { ok: false, reason: 'none' };
      if (n.state === 'memorial') { toast(n.name + '（第 ' + n.gen + ' 代）已經化光，留喺族譜度', 2000); return { ok: false, reason: 'memorial' }; }
      const r = FAM.resOf(s, id), main = FAM.isMain(s, id), el = ov('card', { id });
      const P = mk('div', `position:absolute;left:${a2(20)}px;top:${a2(112)}px;width:${a2(155)}px;height:${a2(168)}px;box-sizing:border-box;${bi('panel_navy')}`); el.appendChild(P);
      const pr = mk('div', `position:absolute;left:${a2(97.5 - 25)}px;top:${a2(152 - 25)}px;width:${a2(50)}px;height:${a2(50)}px;border-radius:50%;box-sizing:border-box;background:radial-gradient(circle at 50% 40%,#4A4790,#1E1A3E);border:4px solid ${main ? GOLD : '#C9B27A'};box-shadow:0 0 0 3px ${LINE}`, null, 'l5-card-portrait');
      const pc = portrait(n, 84); pc.style.left = '4px'; pc.style.top = '4px'; pr.appendChild(pc); el.appendChild(pr);
      if (main) { const cr = img(ui5('icon_crown'), `left:${a2(97.5) - 22}px;top:${a2(152 - 25) - 30}px;width:44px;height:44px`); cr.dataset.testid = 'l5-card-crown'; el.appendChild(cr); }
      const nm = mk('div', `position:absolute;left:0;width:390px;top:${a2(186) - 12}px;text-align:center;` + TXT(22), n.name, 'l5-card-name'); el.appendChild(nm);
      const kindZh = n.kind === 'tr' ? '團絨・第 ' + n.gen + ' 代' : '細佬' + (n.line ? '・' + n.line + ' 系' : '');
      const tg = mk('div', `position:absolute;left:50%;transform:translateX(-50%);top:${a2(199) - 12}px;height:26px;padding:0 14px;box-sizing:border-box;display:flex;align-items:center;white-space:nowrap;${bi('pill_violet')}` + TXT(13), kindZh, 'l5-card-tag'); el.appendChild(tg);
      const where = r ? '住喺' + FAM.ROOM[r.room].zh : main ? (n.kind === 'kid' ? '喺花園（主養）' : '主養・花園＋屋仔') : '喺花園';
      const age = r ? '成年' : n.kind === 'tr' ? (n.tag || '') : (n.raising ? (n.tag || '養緊') : '成年');
      el.appendChild(mk('div', `position:absolute;left:0;width:390px;top:${a2(214) - 10}px;text-align:center;` + TXT(13, '#E8DDBE'), [age, where].filter(Boolean).join('・'), 'l5-card-info'));
      const cm = main ? { ok: false, zh: '' } : FAM.canMain(s, id, now());   // 5a.1：成年 pet2 細佬／住客都可以做主養
      const bm = btn(main ? '主養緊' : '做主養', main || !cm.ok ? 'btn_dis' : 'btn_pri', a2(131), a2(18), 'l5-card-main', () => doMain(id), 'crown');
      bm.style.left = a2(32) + 'px'; bm.style.top = a2(232) + 'px'; if (main || !cm.ok) { bm.dataset.dis = '1'; bm._why = main ? '佢已經係主養' : cm.zh || '而家做唔到主養'; } el.appendChild(bm);
      const bg = btn('打招呼', 'btn16_sec', a2(63), a2(15), 'l5-card-greet', () => doGreet(id)); bg.style.left = a2(32) + 'px'; bg.style.top = a2(254) + 'px'; el.appendChild(bg);
      const bv = btn('搬房', r ? 'btn16_violet' : 'btn16_dis', a2(63), a2(15), 'l5-card-move', () => movePick(id)); bv.style.left = a2(100) + 'px'; bv.style.top = a2(254) + 'px'; if (!r) { bv.dataset.dis = '1'; bv._why = '主養／養緊嘅住屋仔（房 1）'; } el.appendChild(bv);
      const cl = mk('div', `position:absolute;left:${a2(168) - 15}px;top:${a2(117) - 15}px;width:30px;height:30px;cursor:pointer;${sp('close')}`, null, 'l5-card-close'); cl.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); el.appendChild(cl);
      el.querySelector('.bd').addEventListener('click', () => closeOv());
      note('card', { id, main, res: !!r }); return { ok: true, id, main, res: !!r, can: cm.ok };
    }
    function doMain(id) {
      const s = S(), r = FAM.makeMain(s, id, now(), env()); note('main', { id, ok: r.ok, reason: r.reason || '' });
      if (!r.ok) { toast(r.zh || '做唔到主養', 2000); return r; }
      save(); closeOv(); SND('reward'); toast(fmt(r.kind === 'kid' && r.tr ? FAM.LINES.kidOut : FAM.LINES.madeMain, { name: r.name, tr: r.tr || '' }), 2600);
      if (G.house5 && G.house5.isOpen()) G.house5.refresh(); return r;
    }
    function doGreet(id) {
      const H5 = G.house5; if (!H5) return { ok: false, reason: 'house' }; const r = FAM.resOf(S(), id), room = r ? r.room : 'room1';
      closeOv(); const go = () => { const g = H5.greet(id); if (!g.ok) toast(g.reason === 'alone' ? '呢間房得佢一隻，冇人打招呼' : g.reason === 'busy' ? '佢哋忙緊，等陣先' : '佢唔喺度', 1800); note('greet', { id, ok: g.ok, reason: g.reason || '' }); return g; };
      if (!H5.isOpen()) { if (!H5.open()) return { ok: false, reason: 'house' }; }
      if (H5.room() !== room) { H5.goRoom(room, true); setTimeout(go, 700); return { ok: true, later: true }; }
      return go();
    }
    function movePick(id) {
      const s = S(), r = FAM.resOf(s, id); if (!r) return { ok: false };
      const el = ov('move', { id }); const P = mk('div', `position:absolute;left:${a2(28)}px;top:${a2(130)}px;width:${a2(139)}px;height:${a2(150)}px;box-sizing:border-box;${bi('panel_navy')}`); el.appendChild(P);
      el.appendChild(mk('div', `position:absolute;left:0;width:390px;top:${a2(140)}px;text-align:center;` + TXT(18), '搬去邊間？'));
      FAM.ROOMS.forEach((k, i) => {
        const open = FAM.roomOpen(s, k), n = FAM.count(s, k), here = r.room === k, full = n >= FAM.CAP, ok = open && !here && !full;
        const b = btn(FAM.ROOM[k].zh + '　' + (open ? n + '/' + FAM.CAP : 'Lv' + FAM.ROOM[k].lv), ok ? 'btn16_sec' : 'btn16_dis', a2(115), a2(18), 'l5-move-' + k, () => { const m = FAM.moveRoom(S(), id, k); note('move', { id, k, ok: m.ok }); if (m.ok) { save(); closeOv(); toast(r.name + '搬咗去' + FAM.ROOM[k].zh, 1800); if (G.house5 && G.house5.isOpen()) G.house5.refresh(); } });
        b.style.left = a2(40) + 'px'; b.style.top = a2(162 + i * 24) + 'px'; if (!ok) { b.dataset.dis = '1'; b._why = here ? '佢已經住喺度' : !open ? '家族 Lv' + FAM.ROOM[k].lv + ' 開' : '住滿咗（4 隻）'; } el.appendChild(b);
      });
      const cl = mk('div', `position:absolute;left:${a2(160) - 15}px;top:${a2(135) - 15}px;width:30px;height:30px;cursor:pointer;${sp('close')}`, null, 'l5-move-close'); cl.addEventListener('click', (e) => { e.stopPropagation(); closeOv(); }); el.appendChild(cl);
      el.querySelector('.bd').addEventListener('click', () => closeOv()); return { ok: true };
    }

    // ── 家族升級 ──
    const UIC = { room2: 'house', room3: 'house', room4: 'house', family_title: 'title', tree_gold: 'family_tree', visitor_new: 'visitor', inherit_fast: 'fast', furniture_pack1: 'furniture', furniture_pack2: 'furniture', kid_series_E: 'egg_kid', job_cap_plus1: 'job_chef' };
    function levelUp(lvArg) {
      const s = S(), o = FAM.st(s), lv = lvArg || o.lvQ[0]; if (!lv) return { ok: false };
      const el = ov('lvup', { lv, preview: !!lvArg }); el.appendChild(mk('div', 'position:absolute;left:55px;top:160px;width:280px;height:280px')).className = 'rays';
      for (let i = 0; i < 10; i++) { const m = mk('i', `left:${120 + ((i * 37) % 150)}px;top:${250 + ((i * 53) % 110)}px;animation-delay:${(i * 0.23).toFixed(2)}s`); m.className = 'mote'; el.appendChild(m); }
      const md = mk('div', `position:absolute;left:${a2(97.5)}px;top:${a2(150)}px;width:112px;height:112px;transform:translate(-50%,-50%);animation:l5pop .42s cubic-bezier(.34,1.56,.64,1) both`, null, 'l5-lvup-medal');
      const mi = mk('div', `position:absolute;left:16px;top:16px;width:80px;height:80px;box-sizing:border-box;transform:scale(1.4);${sp('med40_gold')}`); md.appendChild(mi);
      md.appendChild(mk('div', 'position:absolute;left:0;top:30px;width:112px;text-align:center;' + TXT(16), 'Lv'));
      md.appendChild(mk('div', 'position:absolute;left:0;top:50px;width:112px;text-align:center;' + TXT(32, GOLD), String(lv), 'l5-lvup-lv')); el.appendChild(md);
      el.appendChild(mk('div', `position:absolute;left:50%;top:${a2(98) - 20}px;transform:translateX(-50%);width:${a2(92)}px;height:40px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;${bi('plaque_pri')}` + TXT(20), '家族升級！', 'l5-lvup-title'));
      const us = FAM.unlockList(lv), C = mk('div', `position:absolute;left:${a2(26)}px;top:${a2(196)}px;width:${a2(143)}px;min-height:${a2(54)}px;box-sizing:border-box;padding:12px 14px;display:flex;flex-direction:column;gap:8px;justify-content:center;${bi('card')}`, null, 'l5-lvup-unlock');
      for (const u of us) {
        const rw = mk('div', 'position:relative;display:flex;align-items:center;gap:10px;min-height:34px'); const ii = icon(UIC[u.id] || 'star', 32, 'position:relative;flex:0 0 32px'); rw.appendChild(ii);
        rw.appendChild(mk('span', 'flex:1;' + TXT(14), u.id === 'family_title' ? '家族稱號「' + FAM.TITLE + '」' : u.zh));
        if (u.later) rw.appendChild(mk('span', `flex:0 0 auto;padding:2px 8px;${bi('pill_dis')}` + TXT(11), u.later)); C.appendChild(rw);
      }
      el.appendChild(C);
      const ok = btn('好嘢！', 'btn_pri', a2(81), a2(18), 'l5-lvup-ok', () => { const o2 = FAM.st(S()); if (!lvArg) { const i = o2.lvQ.indexOf(lv); if (i >= 0) o2.lvQ.splice(i, 1); o2.lvSeen = Math.max(o2.lvSeen || 1, lv); save(); } closeOv(); note('lvOk', { lv }); });
      ok.style.left = a2(57) + 'px'; ok.style.top = Math.max(a2(262), a2(196) + C.offsetHeight + 20) + 'px'; el.appendChild(ok); requestAnimationFrame(() => { ok.style.top = Math.max(a2(262), C.offsetTop + C.offsetHeight + 16) + 'px'; });
      SND('reward'); note('lvup', { lv, preview: !!lvArg }); return { ok: true, lv, unlocks: us.map(u => u.id) };
    }

    // ── 族譜 ──
    function tree() {
      const s = S(), t = FAM.tree(s, now(), { trFk: trFk(), kidFk: kidFk() }), gold = t.gold, el = ov('tree', { gold });
      const bd = el.querySelector('.bd'); bd.style.background = gold ? 'linear-gradient(#5A3E1C,#2E2010 60%,#1C130A)' : 'linear-gradient(#232250,#15122E 60%,#0E0B20)';
      if (gold) { const fr = mk('div', 'position:absolute;inset:6px;border:6px double ' + GOLD + ';border-radius:14px;box-shadow:0 0 18px rgba(255,224,138,.55) inset;pointer-events:none', null, 'l5-tree-goldframe'); el.appendChild(fr); }
      for (let i = 0; i < 18; i++) { const m = mk('i', `position:absolute;left:${(i * 89) % 380}px;top:${(i * 137) % 830}px;width:2px;height:2px;background:${gold ? GOLD : '#BFD4FF'};opacity:${0.3 + (i % 4) * 0.15};pointer-events:none`); el.appendChild(m); }
      const back = mk('div', `position:absolute;left:${a2(16) - 22}px;top:${a2(18) - 22}px;width:44px;height:44px;cursor:pointer;${bi('med22_navy') || FB.chip}`, null, 'l5-tree-close'); back.appendChild(icon('back', 28, 'left:8px;top:8px')); back.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); el.appendChild(back);
      el.appendChild(mk('div', `position:absolute;left:50%;top:${a2(8)}px;transform:translateX(-50%);min-width:${a2(70)}px;height:40px;padding:0 16px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;white-space:nowrap;${bi('plaque_pri')}` + TXT(20, gold ? GOLD : CREAM), gold ? '族譜・' + FAM.TITLE : '族譜', 'l5-tree-title'));
      // 等級卡
      const L = t.lv, LC = mk('div', `position:absolute;left:${a2(8)}px;top:${a2(32)}px;width:${a2(179)}px;height:${a2(40)}px;box-sizing:border-box;${bi(gold ? 'card_sel' : 'card')}`, null, 'l5-tree-level'); el.appendChild(LC);
      LC.appendChild(icon('family_level', 40, 'left:12px;top:10px'));
      LC.appendChild(mk('div', 'position:absolute;left:62px;top:8px;' + TXT(18, gold ? GOLD : CREAM), '家族 Lv' + L.lv + (L.max ? '（最高）' : '')));
      const bw = 170, tr = mk('div', `position:absolute;left:62px;top:36px;width:${bw}px;height:12px;box-sizing:border-box;background:#1E1A3E;border:2px solid ${LINE};border-radius:3px;overflow:hidden`); tr.appendChild(mk('div', `position:absolute;left:0;top:0;bottom:0;width:${Math.round(L.pct * 100)}%;background:linear-gradient(#FFE9A8,#F3B33E)`, null, 'l5-tree-bar')); LC.appendChild(tr);
      LC.appendChild(mk('div', `position:absolute;left:${62 + bw + 8}px;top:33px;` + TXT(12), L.max ? L.xp + ' XP' : L.xp + '/' + L.to, 'l5-tree-xp'));
      const nx = L.max ? '全部解鎖晒！稱號「' + FAM.TITLE + '」' : '下一級：' + FAM.unlockList(L.lv + 1).map(u => u.zh + (u.later ? '（' + u.later + '）' : '')).join('、');
      LC.appendChild(mk('div', 'position:absolute;left:12px;right:10px;top:56px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;' + TXT(11, '#E8DDBE'), nx, 'l5-tree-next'));
      // rows
      const SC = mk('div', `left:0;top:${a2(80)}px;width:390px;height:${a2(400) - a2(80) - 12}px`, null, 'l5-tree-rows'); SC.className = 'scr'; el.appendChild(SC);
      const IN = mk('div', 'position:relative;width:390px;padding-bottom:20px'); SC.appendChild(IN);
      const pos = {};
      for (const row of t.rows) {
        const RW = mk('div', '', null, 'l5-tree-row-' + row); RW.className = 'row'; RW.appendChild(mk('div', 'position:absolute;left:12px;top:2px;' + TXT(14, GOLD), '第 ' + row + ' 代'));
        for (const n of t.nodes.filter(x => x.row === row)) {
          const fr = n.raising ? 'tree_node_sel' : gold ? 'tree_node_gold' : 'tree_node';
          const d = mk('div', bi(fr), null, 'l5-node-' + n.id); d.className = 'node' + (n.state === 'memorial' ? ' mem' : ''); d.dataset.state = n.state; d.dataset.kind = n.kind;
          const pc = portrait(n, 68); pc.style.left = '6px'; pc.style.top = '18px'; d.appendChild(pc);
          d.appendChild(mk('div', 'position:absolute;left:80px;top:14px;right:6px;white-space:nowrap;overflow:hidden;' + TXT(14), n.name));
          d.appendChild(mk('div', 'position:absolute;left:80px;top:38px;right:6px;white-space:nowrap;overflow:hidden;' + TXT(11, '#E8DDBE'), (n.kind === 'kid' && n.line ? n.line + ' 系・' : '') + (n.tag || '')));
          const pills = mk('div', 'position:absolute;left:80px;top:62px;right:4px;display:flex;gap:4px;flex-wrap:wrap'); d.appendChild(pills);
          if (n.state === 'main') pills.appendChild(img(ui5('icon_crown'), 'position:relative;width:26px;height:26px'));
          if (n.raising) pills.appendChild(mk('span', `padding:2px 8px;${bi('pill_sec')}` + TXT(11), '養緊'));
          if (n.state === 'memorial') pills.appendChild(mk('span', `padding:2px 8px;${bi('pill_dis')}` + TXT(11), '化光'));
          if (n.lessons && n.lessons.length) for (const ln of n.lessons.slice(0, 3)) pills.appendChild(mk('span', `padding:2px 6px;${bi('pill_navy')}` + TXT(10), ln));
          d.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); card(n.id); }); RW.appendChild(d); pos[n.id] = d;
        }
        IN.appendChild(RW);
      }
      const drawLinks = () => {
        for (const [a, b] of t.links) {
          const A = pos[a], B = pos[b]; if (!A || !B) continue; const ir = IN.getBoundingClientRect(), ar = A.getBoundingClientRect(), br = B.getBoundingClientRect(), k = 390 / (ir.width || 390);
          const x1 = (ar.left + ar.width / 2 - ir.left) * k, y1 = (ar.bottom - ir.top) * k, x2 = (br.left + br.width / 2 - ir.left) * k, y2 = (br.top - ir.top) * k, ym = Math.round((y1 + y2) / 2);
          const ln = (x, y, w, h) => { const l = mk('i', `position:absolute;left:${Math.round(x)}px;top:${Math.round(y)}px;width:${Math.max(4, Math.round(w))}px;height:${Math.max(4, Math.round(h))}px;background:${GOLD};box-shadow:${gold ? '0 0 8px ' + GOLD : '0 0 0 1px ' + LINE};pointer-events:none`); l.dataset.link = a + '>' + b; IN.insertBefore(l, IN.firstChild); };
          ln(x1 - 2, y1, 4, ym - y1); ln(Math.min(x1, x2) - 2, ym - 2, Math.abs(x2 - x1) + 4, 4); ln(x2 - 2, ym, 4, y2 - ym);
        }
      };
      requestAnimationFrame(drawLinks);
      el.appendChild(mk('div', `position:absolute;left:0;width:390px;top:${a2(400) - 6}px;text-align:center;` + TXT(12, '#E8DDBE'), '金冠＝主養・藍綠框＝養緊・撳寵物睇寵物卡', 'l5-tree-legend'));
      el.appendChild(mk('div', `position:absolute;left:0;width:390px;top:${a2(400) + 18}px;text-align:center;` + TXT(11, '#BFB49A'), '經驗：養大一隻 +50・新圖鑑形態 +10・新家具 +5・遠足 +3（5b）'));
      note('tree', { gold, nodes: t.nodes.length }); return { ok: true, gold, nodes: t.nodes.map(n => n.id), links: t.links.length };
    }

    // ── tick hook ──
    const s2t = G.s2Tick; G.s2Tick = function () { const r = s2t ? s2t.apply(this, arguments) : undefined; try { tick(); } catch (e) { note('tickErr', { e: String(e && e.message || e) }); } return r; };
    setTimeout(() => { try { tick(true); } catch (e) { } }, 600);

    G.l5 = { tree, card, offer, levelUp, close: () => closeOv(), pick: doPick, main: doMain, greet: doGreet, move: movePick, tick: () => tick(true), onRoom: (k) => note('room', { k }), open: () => OV.kind };

    // ── 🛠 開發者模式「5a」 ──
    const H5 = () => G.house5;
    const prep = () => { const o = SR.st(S()); if (o.phase === 'kid' && o.rel === 'family') return null; if (o.phase !== 'kid' && FAM.st(S()).res.length) return null; const r = G.s2Test && G.s2Test.family ? G.s2Test.family() : { ok: false, msg: '冇細佬試玩' }; return r.ok ? null : r; };
    const elder = () => { const s = S(); if (s.stage === 'elder') return; if (G.evo && G.evo.setStage) G.evo.setStage('elder', s.form || 'soft'); else s.stage = 'elder'; };
    const xpTo = (lv) => { const s = S(), o = FAM.st(s), need = FAM.THRESH[lv - 1]; if (o.xp < need) FAM.addXp(s, 'dev', need - o.xp, now(), 'dev'); save(); if (H5() && H5().isOpen()) H5().refresh(); };
    const houseIn = (room) => { const e = prep(); if (e) return e; const h = H5(); if (!h) return { ok: false, msg: '冇屋仔' }; if (!h.isOpen() && !h.open()) return { ok: false, msg: '開唔到屋仔' }; if (room && h.room() !== room) h.goRoom(room, true); return null; };
    let devN = 0;
    const addRes = (kind, room) => { const s = S(), o = FAM.st(s), rm = room ? (FAM.roomOpen(s, room) && FAM.count(s, room) < FAM.CAP ? room : null) : FAM.freeRoom(s, 'room1'); if (!rm) return null;
      const TRF = ['evo_still_moon', 'evo_still_tide', 'evo_still_crystal', 'evo_still_ember', 'evo_still_lumi'], TRN = { evo_still_moon: '月眠團絨', evo_still_tide: '潮汐團絨', evo_still_crystal: '晶晶團絨', evo_still_ember: '餘燼團絨', evo_still_lumi: '微光團絨' }, KIDF = ['A3', 'B3', 'G3', 'D3'];
      const id = 'dev' + kind + (++devN) + '_' + (now() % 1e5);
      const tf = TRF[(devN - 1) % TRF.length], kf = KIDF[(devN - 1) % KIDF.length];
      const r = kind === 'tr' ? { id, kind: 'tr', gen: Math.max(1, (S().gen || 1) - 1), form: null, fk: tf, name: TRN[tf], room: rm, at: now(), snap: FAM.snapTr(s) }
        : { id, kind: 'kid', gen: 0, line: kf[0], fk: kf, name: FAM.kidName(kf[0]) + devN, bro: FAM.trId(s), room: rm, at: now(), snap: Object.assign(FAM.snapKid(s), { phase: 'kid', rel: 'family', line: kf[0], fid: id }) };
      o.res.push(r); o.adults[id] = now(); return r; };
    const DEV = { id: 'l5', title: '5a（家族長線）', order: 42,
      status: () => { const s = S(), o = FAM.st(s), rm = H5() && H5().isOpen() ? H5().room() : 'room1'; return 'Lv' + o.lv + '・' + o.xp + ' XP・住客 ' + o.res.length + '・' + FAM.ROOM[rm].zh + ' ' + FAM.count(s, rm) + '/' + FAM.CAP + (FAM.offerReady(s, now()) ? '・有新蛋' : ''); },
      items: [
        ['prep', '準備：細佬成年＋家人（開屋）', () => { const e = prep(); if (e) return e; tick(true); return { ok: true, msg: '細佬成年家人；家族 Lv' + FAM.st(S()).lv }; }],
        ['offer', '新蛋二揀一（即刻送）', () => { const e = prep(); if (e) return e; elder(); const o = FAM.st(S()); o.offer = { due: SR.dayNum(now()), at: now(), why: 'dev' }; save(); return offer('dev').ok ? { ok: true, msg: '彈咗新蛋二揀一（團絨已到靜光）' } : { ok: false, msg: '彈唔到' }; }],
        ['offerKidOff', '新蛋：細佬蛋灰（細佬養緊）', () => { const s = S(), p = SR.st(s); if (p.phase === 'kid' && SR.stageOf(s, now()) === 'S6') { p.hatchDay = SR.dayNum(now()) - 2; } else if (p.phase === 'none' || p.phase === 'due') { const e = prep(); if (e) return e; SR.st(s).hatchDay = SR.dayNum(now()) - 2; } elder(); FAM.st(s).offer = { due: SR.dayNum(now()), at: now(), why: 'dev' }; save(); offer('dev'); return { ok: true, msg: '細佬蛋灰咗（細佬養緊）' }; }],
        ['offerFull', '新蛋：屋企爆滿（兩邊都灰）', () => { const e = prep(); if (e) return e; const s = S(); for (const k of FAM.openRooms(s)) while (FAM.count(s, k) < FAM.CAP) if (!addRes('tr', k)) break; elder(); FAM.st(s).offer = { due: SR.dayNum(now()), at: now(), why: 'dev' }; save(); offer('dev'); return { ok: true, msg: '已開嘅房全部住滿' }; }],
        ['pickTr', '揀團絨蛋（主養搬入屋）', () => { const e = prep(); if (e) return e; elder(); const s = S(); FAM.st(s).offer = { due: SR.dayNum(now()), at: now(), why: 'dev' }; const r = doPick('tr'); return r.ok ? { ok: true, msg: '第 ' + r.gen + ' 代團絨蛋；' + r.moved.name + '住' + FAM.ROOM[r.moved.room].zh } : { ok: false, msg: r.zh || r.reason }; }],
        ['pickKid', '揀細佬蛋（成年細佬搬入屋）', () => { const e = prep(); if (e) return e; const s = S(); FAM.st(s).offer = { due: SR.dayNum(now()), at: now(), why: 'dev' }; const r = doPick('kid'); return r.ok ? { ok: true, msg: '新細佬蛋' + (r.moved ? '；' + r.moved.name + '搬入屋' : '') } : { ok: false, msg: r.zh || r.reason }; }],
        ['kidMain', '5a.1 細佬做主養（皇冠＋團絨入屋）', () => { const e = prep(); if (e) return e; const s = S(); if (FAM.kmOf(s)) return { ok: true, msg: FAM.kmOf(s).name + '已經係主養' }; elder();
          const p = SR.st(s); if (p.phase === 'kid' && SR.stageOf(s, now()) !== 'S6') p.hatchDay = SR.dayNum(now()) - 20; if (p.phase === 'kid') { p.rel = 'family'; p.intim = Math.max(p.intim | 0, 90); } tick(true);
          const ids = [p.phase === 'kid' ? p.fid : null].concat(FAM.st(s).res.filter(r => r.kind === 'kid').map(r => r.id)).filter(Boolean), id = ids.find(i => FAM.canMain(s, i, now()).ok);
          if (!id) return { ok: false, msg: '冇成年細佬（撳「準備」或「加細佬住客」）' }; const r = doMain(id); if (!r.ok) return { ok: false, msg: r.zh || r.reason }; tick(true);
          return { ok: true, msg: r.name + '做咗主養' + (r.tr ? '；' + r.tr + '搬入屋' : '') + (r.from === 'garden' ? '；pet2 空出嚟等新蛋' : '') }; }],
        ['trMain', '5a.1 揀返團絨做主養', () => { const s = S(), K = FAM.kmOf(s); if (!K) return { ok: false, msg: '主養已經係團絨' }; const lt = FAM.latestTr(FAM.st(s)); if (!lt) return { ok: false, msg: '屋企冇團絨' }; const r = doMain(lt.id); return r.ok ? { ok: true, msg: r.name + '做返主養；' + K.name + '返屋' } : { ok: false, msg: r.zh || r.reason }; }],
        ['xp', '家族經驗 +60', () => { const s = S(), r = FAM.addXp(s, 'dev', 60, now(), 'dev'); save(); tick(true); return { ok: true, msg: '+60 → Lv' + r.lv + '（' + FAM.st(s).xp + ' XP）' }; }],
        ['lv5', '跳去 Lv5（開房 2、3）', () => { xpTo(5); tick(true); return { ok: true, msg: 'Lv' + FAM.st(S()).lv }; }],
        ['lv10', '跳去 Lv10（全開＋金族譜）', () => { xpTo(10); tick(true); return { ok: true, msg: 'Lv' + FAM.st(S()).lv + '・' + FAM.TITLE }; }],
        ['lvup', '睇升級彈窗（預覽 Lv2）', () => { const r = levelUp(Math.max(2, FAM.st(S()).lv)); return r.ok ? { ok: true, msg: '升級彈窗 Lv' + r.lv } : { ok: false, msg: '冇' }; }],
        ['room2', '入房 2 森林閣樓', () => { xpTo(2); const e = houseIn('room2'); return e || { ok: true, msg: '森林閣樓' }; }],
        ['room3', '入房 3 星夜書房', () => { xpTo(5); const e = houseIn('room3'); return e || { ok: true, msg: '星夜書房' }; }],
        ['room4', '入房 4 海風小屋', () => { xpTo(8); const e = houseIn('room4'); return e || { ok: true, msg: '海風小屋' }; }],
        ['resTr', '加 1 隻成年團絨住客', () => { const e = prep(); if (e) return e; const h = H5(), rm = h && h.isOpen() ? h.room() : null, r = addRes('tr', rm); if (!r) return { ok: false, msg: '住滿咗' }; save(); tick(true); if (h && h.isOpen()) h.refresh(); return { ok: true, msg: r.name + '住' + FAM.ROOM[r.room].zh }; }],
        ['resKid', '加 1 隻成年細佬住客', () => { const e = prep(); if (e) return e; const h = H5(), rm = h && h.isOpen() ? h.room() : null, r = addRes('kid', rm); if (!r) return { ok: false, msg: '住滿咗' }; save(); tick(true); if (h && h.isOpen()) h.refresh(); return { ok: true, msg: r.name + '住' + FAM.ROOM[r.room].zh }; }],
        ['fill', '而家間房住滿（4/4）', () => { const e = houseIn(); if (e) return e; const h = H5(), rm = h.room(); let n = 0; while (FAM.count(S(), rm) < FAM.CAP) { if (!addRes(n % 2 ? 'kid' : 'tr', rm)) break; n++; } save(); h.refresh(); return { ok: true, msg: FAM.ROOM[rm].zh + ' ' + FAM.count(S(), rm) + '/4' }; }],
        ['card', '寵物卡（第 1 隻住客）', () => { const r = FAM.st(S()).res[0]; if (!r) return { ok: false, msg: '未有住客（撳「加住客」）' }; card(r.id); return { ok: true, msg: r.name + '嘅寵物卡' }; }],
        ['greet', '打招呼（兩隻面對面）', () => { const e = houseIn(); if (e) return e; const h = H5(), xs = h.actors(); if (xs.length < 2) { const r = addRes('tr', h.room()); if (r) { save(); h.refresh(); } } const ys = h.actors(); if (ys.length < 2) return { ok: false, msg: '房入面唔夠兩隻' }; const g = h.greet(ys[0].id, ys[1].id); return g.ok ? { ok: true, msg: '打招呼！' } : { ok: false, msg: g.reason }; }],
        ['tree', '睇族譜', () => { const r = tree(); return { ok: true, msg: '族譜 ' + r.nodes.length + ' 隻' }; }],
        ['treeGold', '睇金色族譜（Lv10）', () => { xpTo(10); tick(true); closeOv(true); const r = tree(); return { ok: r.gold, msg: r.gold ? '金色族譜' : '未到 Lv10' }; }],
        ['sv', '送晒 10 件手信', () => { const o = FAM.st(S()); for (const x of FAM.SOUV) o.sv[x.id] = o.sv[x.id] || now(); save(); tick(true); if (H5() && H5().isOpen()) H5().refresh(); return { ok: true, msg: '10 件手信（佈置 → 擺設）' }; }],
        ['reset', '重設 5a（清家族資料）', () => { const s = S(); delete s.fam; FAM.st(s); FAM.st(s).init = now(); closeOv(true); save(); if (H5() && H5().isOpen()) { H5().goRoom('room1', true); H5().refresh(); } return { ok: true, msg: '5a 資料清咗（Lv1）' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    window.__qa = window.__qa || {};
    window.__qa.l5 = {
      st: () => Object.assign(FAM.summary(S(), now()), { ov: OV.kind, ovData: OV.data, quiet: QUIET, ticks: T.n, egg: !!(EB.el && EB.el.style.display !== 'none') }),
      log: () => log.slice(), evs: () => T.evs.slice(), toasts: () => toasts.slice(), tick: () => tick(true), close: () => closeOv(), tree, card, offer, levelUp, pick: doPick, main: doMain, greet: doGreet, move: movePick,
      xp: (n) => { const r = FAM.addXp(S(), 'qa', n, now(), 'qa'); save(); return r; }, xpTo, addRes: (k, room) => { const r = addRes(k || 'tr', room); save(); if (H5() && H5().isOpen()) H5().refresh(); return r && { id: r.id, room: r.room, name: r.name }; },
      dev: () => DEV, elder, fam: () => JSON.parse(JSON.stringify(FAM.st(S()))) };
    return true;
  }
  return { install };
});
