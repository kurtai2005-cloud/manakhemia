/* 《微光小圃》 long5cui.js — 第 5 批 5c 承傳介面（遊策 5a–5c spec §5c＋遊美 art/series2_long/5c：long_5c.json＋patterns／ui）。原創代碼。
   邏輯全部喺 long5c.js（s.fam.c5）；呢度只做：
   ・新蛋一到 →「揀上一代」（2×3 成年卡，可捲；底部「會遺傳」：花紋＋招式＋加速 pill）；閂咗可以喺 rail「上一代」掣再開；未揀就孵 → 自動揀（toast）
   ・孵化 →「遺傳咗！」結果（新 BB 已染花紋＋花紋／招式兩行＋加速 pill）
   ・花紋：runtime 用上一代 tint 染 mask（R≥190→hi，其餘→lo；alpha 照 mask）→ 畫喺細佬 strip（花園／屋仔）、照抄 clip、細佬蛋、出發／返屋、
     團絨主養（花園＋屋仔 atlas 幀：base 行剪入剪影）；浮動團絨唔畫
   ・家傳招式：花園 idle 每 45–90 秒做一次（細佬照抄 clip／團絨 s2_demo）；族譜卡加「上一代」花紋＋招式
   ・🛠 開發者模式「5c」；?l5c=0（或 ?l5=0／?house=0／?s2=0）全停；?ev=0 唔自動彈、唔自動做招式。字一律 FP12 24px（唔縮細字，改換行）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5cui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const C = NS.long5c, FAM = NS.long5a, SR = NS.series2, UI = NS.ui; if (!C || !FAM || !SR || !UI || !G.s2Art) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l5c') === '0' || qs.get('l5') === '0' || qs.get('house') === '0' || qs.get('s2') === '0') { delete FAM.LIVE.inherit_fast; return false; }
    FAM.LIVE.inherit_fast = 1; delete FAM.LATER.inherit_fast;
    const QUIET = qs.get('ev') === '0';
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now(), SA = G.s2Art, R = G.renderer, LB = 'art/series2_long/5c/';
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2000); };
    const H5 = () => G.house5;
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const ui5c = (n) => LB + 'ui/' + n + '@3x.png', ui5a = (n) => 'art/series2_long/5a/ui/' + n + '@3x.png', ui5b = (n) => 'art/series2_long/5b/ui/' + n + '@3x.png';
    const SW = { wave: 'A3', bubble: 'B3', spark: 'C3', spot: 'D3', flame: 'E3', star: 'F3', diamond: 'G3', crescent: 'H3' }, swatch = (p) => ui5c('swatch_' + p + '_' + (SW[p] || 'A3'));
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const F8 = () => (U() ? ((G.v3 && G.v3.want) ? '"GlimmerV3Sans",' : '"GlimmerFP8",') : '') + FALL, F12 = () => (U() ? ((G.v3 && G.v3.want) ? '"GlimmerV3Sans",' : '"GlimmerFP12",') : '') + FALL;   // #83 V3 → Noto Sans CJK TC
    const CREAM = '#FFF5DC', GOLD = '#FFE08A', SUB = '#E8DDBE';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;', card_sel: 'background:#4A3F7A;border:3px solid #FFE08A;border-radius:8px;box-shadow:0 0 12px rgba(255,224,138,.75);',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', chip: 'background:#2A2450;border:2px solid #C9B27A;border-radius:8px;',
      panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;', med40_gold: 'background:#F6C85A;border:4px solid #6B3A1E;border-radius:50%;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || ''; };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const TXT = (size, color, extra) => `font:${U() ? (size <= 24 ? 24 : 36) : Math.max(size, 24)}px/1.2 ${U() ? F12() : F8()};color:${color || CREAM};${OL}-webkit-font-smoothing:none;` + (extra || '');
    function btn(label, kind, w, h, tid, onClick) {
      const b = mk('div', `position:absolute;width:${w}px;min-height:${h}px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:4px;cursor:pointer;padding:2px 6px;${bi(kind)}` + TXT(24), null, tid);
      b.appendChild(mk('span', 'position:relative;text-align:center', label));
      b.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); onClick && onClick(e); }); return b;
    }
    const IMC = new Map(); function imI(src) { let i = IMC.get(src); if (!i) { i = new Image(); i.src = src; IMC.set(src, i); } return i.complete && i.naturalWidth ? i : null; }
    let J = null; G.l5cLoad = fetch(LB + 'long_5c.json').then(r => (r.ok ? r.json() : null)).then(j => { if (j) { J = j; note('json'); } return J; }).catch(e => { note('jsonErr', { e: String(e) }); return null; });
    const trFk = () => (G.house5 && G.house5.trFk ? G.house5.trFk() : R && R.fkOf ? R.fkOf(S()) : 'sprout');
    const kidFk = () => { try { const f = SA.formNow(); return f && f !== 'egg' ? f : null; } catch (e) { return null; } };
    const ctx = () => ({ art: J, trFk: trFk(), kidFk: kidFk() });
    const TR = (L) => (J && J.tricks && J.tricks[L]) || { title: C.TRICK[L] || L, propZh: '', propPng: null };
    const lessonZh = (L) => String(TR(L).title || '').split(/\s*→\s*/)[0] || L;
    const patZh = (p) => (C.PAT[p] ? C.PAT[p].zh : p), patN = (p) => { const z = patZh(p); return /紋$/.test(z) ? z : z + '紋'; };

    // ── 花紋：染色 cache（形態＋花紋＋hi＋lo）──
    const STAT = { built: 0, strip: 0, base: 0, egg: 0, house: 0, row: 0, tr: 0 };
    const PC = new Map();
    function patCv(png, rows, pat, hi, lo) {
      const key = png + '|' + pat + '|' + hi + '|' + lo; if (PC.has(key)) return PC.get(key);
      const I = imI(LB + png); if (!I) return null; const rs = rows.filter(r => r.pattern === pat); if (!rs.length) { PC.set(key, null); return null; }
      const y0 = Math.min(...rs.map(r => r.y)), y1 = Math.max(...rs.map(r => r.y + r.frameH)), w = I.naturalWidth, h = y1 - y0;
      const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); g.drawImage(I, 0, y0, w, h, 0, 0, w, h);
      try { const d = g.getImageData(0, 0, w, h), A = d.data, H = C.hx(hi), L = C.hx(lo); for (let i = 0; i < A.length; i += 4) { if (!A[i + 3]) continue; const q = A[i] >= 190 ? H : L; A[i] = q[0]; A[i + 1] = q[1]; A[i + 2] = q[2]; } g.putImageData(d, 0, 0); } catch (e) { note('patErr', { e: String(e) }); }
      const r = { cv: c, y0 }; PC.set(key, r); STAT.built++; if (PC.size > 64) PC.delete(PC.keys().next().value); return r;
    }
    const inhId = (who) => { const s = S(); if (!s || !s.fam) return null; if (who === 'km') return s.fam.km ? s.fam.km.id : null; if (who === 'tr') return FAM.trId(s); return FAM.kidId(s); };
    function look(id, childFk) { if (!J || !id) return null; const s = S(), h = C.inhOf(s, id); if (!h) return null; const t = C.tintPair(J, h, childFk); return { h, hi: t.hi, lo: t.lo }; }
    function rowOf(fk, pat, clip) { const F = J && J.overlay.forms[fk]; if (!F) return null; const r = F.rows.find(q => q.pattern === pat && q.clip === clip); return r ? { F, r } : null; }
    function drawRow(x, fk, L, clip, f, dx, dy, tint, tinted) {
      const m = rowOf(fk, L.h.pattern, clip); if (!m) return false; const P = patCv(m.F.png, m.F.rows, L.h.pattern, L.hi, L.lo); if (!P) return false; const r = m.r, fr = Math.max(0, Math.min(r.frames - 1, f | 0));
      x.drawImage(tinted && tint ? tinted(P.cv, tint) : P.cv, fr * r.frameW, r.y - P.y0, r.frameW, r.frameH, dx, dy, r.frameW, r.frameH); return true;
    }
    // 剪影：pattern base 行對齊 pivot、只畫喺來源幀不透明位（團絨 atlas／照抄 composite）
    const OFF = { c: null };
    function silo(srcImg, sx, sy, sw, sh, px, py, fk, L, clip, tint, tinted) {
      const m = rowOf(fk, L.h.pattern, clip) || rowOf(fk, L.h.pattern, 'base') || rowOf(fk, L.h.pattern, 'idle'); if (!m) return null; const P = patCv(m.F.png, m.F.rows, L.h.pattern, L.hi, L.lo); if (!P) return null;
      if (!OFF.c) OFF.c = document.createElement('canvas'); const c = OFF.c; if (c.width < sw) c.width = sw; if (c.height < sh) c.height = sh; const g = c.getContext('2d'); g.globalCompositeOperation = 'source-over'; g.clearRect(0, 0, c.width, c.height); g.imageSmoothingEnabled = false;
      g.drawImage(srcImg, sx, sy, sw, sh, 0, 0, sw, sh); g.globalCompositeOperation = 'source-in'; const r = m.r;
      g.drawImage(tinted && tint ? tinted(P.cv, tint) : P.cv, 0, r.y - P.y0, r.frameW, r.frameH, Math.round(px - r.pivot[0]), Math.round(py - r.pivot[1]), r.frameW, r.frameH); g.globalCompositeOperation = 'source-over'; return c;
    }
    const BASEC = { c: null };
    G.pat5c = {
      strip(x, who, fk, clip, f, dx, dy) { const L = look(inhId(who), fk); if (!L || L.h.kind !== 'kid' || !L.h.hatched) return; if (drawRow(x, fk, L, clip, f, dx, dy)) STAT.strip++; },
      base(bc, who, fk, pv) { const L = look(inhId(who), fk); if (!L || L.h.kind !== 'kid' || !L.h.hatched) return bc; const c = silo(bc, 0, 0, bc.width, bc.height, pv[0], pv[1], fk, L, 'idle'); if (!c) return bc;
        if (!BASEC.c) BASEC.c = document.createElement('canvas'); const o = BASEC.c; o.width = bc.width; o.height = bc.height; const g = o.getContext('2d'); g.clearRect(0, 0, o.width, o.height); g.drawImage(bc, 0, 0); g.drawImage(c, 0, 0, bc.width, bc.height, 0, 0, bc.width, bc.height); STAT.base++; return o; },
      egg(x, who, X, Y) { const s = S(); if (!J || !s) return; const id = inhId(who), h = C.inhOf(s, id); if (!h || h.hatched || h.kind !== 'kid') return; const E = J.overlay.eggs.egg_kid, t = C.tintPair(J, h, null), P = patCv(E.png, E.rows, h.pattern, t.hi, t.lo); if (!P) return;
        const r = E.rows.find(q => q.pattern === h.pattern); x.drawImage(P.cv, 0, r.y - P.y0, r.frameW, r.frameH, X, Y, r.frameW, r.frameH); STAT.egg++; },
      house(x, p, src, tint, tinted) {
        const s = S(); if (!s || !src || !src.img) return; const res = p.who === 'res', kind = res ? p.kind : p.who === 'tr' ? 'tr' : 'kid', id = res ? p.id : inhId(kind === 'tr' ? 'tr' : 'pet2'), fk = res ? p.fk : (kind === 'tr' ? trFk() : kidFk()); if (!fk) return; const L = look(id, fk); if (!L || !L.h.hatched) return;
        const m = rowOf(fk, L.h.pattern, p.clip); if (m && m.r.frameW === src.sw && m.r.frameH === src.sh) { const fr = src.frame != null ? src.frame : Math.round(src.sx / m.r.frameW); if (drawRow(x, fk, L, p.clip, fr, -src.px, -src.py, tint, tinted)) { STAT.house++; return; } }
        const c = silo(src.img, src.sx, src.sy, src.sw, src.sh, src.px, src.py, fk, L, kind === 'tr' ? 'base' : 'idle', tint, tinted); if (c) { x.drawImage(c, 0, 0, src.sw, src.sh, -src.px, -src.py, src.sw, src.sh); STAT.house++; }
      },
      row(x, id, fk, k, f, X, Y, tint, tinted) { const L = look(id, fk); if (!L || !L.h.hatched) return; if (drawRow(x, fk, L, k, f, X, Y, tint, tinted)) STAT.row++; },
    };
    if (R) R.pat5c = function (x, draw, fk, s) { if (!s || s.stage === 'egg' || !draw || !draw.img || (s.fam && s.fam.km)) return; const L = look(FAM.trId(s), fk); if (!L || L.h.kind !== 'tr' || !L.h.hatched) return;
      const c = silo(draw.img, draw.sx, draw.sy, draw.sw, draw.sh, draw.px, draw.py, fk, L, 'base'); if (c) { x.drawImage(c, 0, 0, draw.sw, draw.sh, -draw.px, -draw.py, draw.sw, draw.sh); STAT.tr++; } };

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l5ccss';
    css.textContent = `#l5cov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:60;user-select:none;-webkit-user-select:none;touch-action:manipulation}
#l5cov .bd{position:absolute;inset:0;background:rgba(18,12,30,.66)}
#l5cov[data-kind=result] .bd{background:rgba(14,10,26,.9)}
body.l5c-on #toast{z-index:72 !important}
#l5cov .scr{position:absolute;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none}
#l5cov .scr::-webkit-scrollbar{display:none}
#l5cov .l5ccard{position:relative;width:155px;height:116px;box-sizing:border-box;cursor:pointer;flex:0 0 155px}
#l5cov .l5crays{position:absolute;left:75px;top:180px;width:240px;height:240px;border-radius:50%;background:radial-gradient(circle,rgba(255,240,180,.85) 0,rgba(255,224,138,.45) 38%,rgba(255,224,138,0) 70%);animation:l5cray 2.4s ease-in-out infinite;pointer-events:none}
#l5cov .l5crow{position:relative;width:330px;box-sizing:border-box;display:flex;align-items:center;gap:10px;padding:6px 10px;opacity:0;transform:translateY(8px);transition:opacity 200ms,transform 200ms}
#l5cov .l5crow.in{opacity:1;transform:none}
#l5cov .l5cpet{transition:clip-path 300ms linear}
#l5cbtn{cursor:pointer}
#l5cbtn > i.i{position:absolute;left:50%;top:50%;width:36px;height:36px;margin:-18px 0 0 -18px;pointer-events:none}
@keyframes l5cray{0%,100%{transform:scale(.92);opacity:.85}50%{transform:scale(1.06);opacity:1}}`;
    document.head.appendChild(css);

    // ── 疊層 ──
    const OV = { el: null, kind: null, data: null };
    function ov(kind, data) {
      closeOv(true); const host = document.getElementById('ui') || document.body;
      const el = OV.el = mk('div', '', null, 'l5c-' + kind); el.id = 'l5cov'; el.dataset.kind = kind; OV.kind = kind; OV.data = data || null;
      const bd = mk('div', ''); bd.className = 'bd'; bd.addEventListener('click', () => { UIS('tap'); closeOv(); }); el.appendChild(bd);
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      host.appendChild(el); document.body.classList.add('l5c-on'); note('ov', { kind }); return el;
    }
    function closeOv(quiet) { if (!OV.el) return false; const k = OV.kind; OV.el.remove(); OV.el = null; OV.kind = null; OV.data = null; document.body.classList.remove('l5c-on'); if (!quiet) note('ovClose', { kind: k }); try { railTick(); } catch (e) { } return true; }
    const busy = () => !!OV.el || !!document.getElementById('l5ov') || !!document.getElementById('l5bov') || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene');
    function closeX(p, tid) { const x0 = mk('div', `position:absolute;right:-14px;top:-16px;z-index:5;width:52px;height:52px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center` + TXT(24, CREAM), null, tid);
      const xi = mk('div', `position:relative;width:40px;height:40px;pointer-events:none;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}`, sp('close') ? '' : '✕'); xi.style.width = '40px'; xi.style.height = '40px'; x0.appendChild(xi);
      x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); p.appendChild(x0); return x0; }
    function plaque(p, label, tid) { p.appendChild(mk('div', `position:absolute;left:50%;top:-24px;transform:translateX(-50%);min-width:208px;height:48px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 16px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), label, tid)); }

    // 頭像：細佬 strip idle 0／團絨 atlas idle；加花紋（候選上一代：有遺傳就照畫）
    const TRIM = new Map();
    function trim(I, sx, sy, sw, sh) { const key = (I.src || '').slice(-40) + ':' + sx + ':' + sy + ':' + sw + ':' + sh; if (TRIM.has(key)) return TRIM.get(key); let r = { x: 0, y: 0, w: sw, h: sh };
      try { const c = document.createElement('canvas'); c.width = sw; c.height = sh; const g = c.getContext('2d'); g.drawImage(I, sx, sy, sw, sh, 0, 0, sw, sh); const d = g.getImageData(0, 0, sw, sh).data; let x0 = sw, y0 = sh, x1 = -1, y1 = -1;
        for (let y = 0; y < sh; y++) for (let x = 0; x < sw; x++) if (d[(y * sw + x) * 4 + 3] > 16) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } if (x1 >= x0) r = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 }; } catch (e) { } TRIM.set(key, r); return r; }
    function petCanvas(c, size, kind, fk, look0, ox0) {
      const draw = () => { const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, c.width, c.height); let src = null;
        if (kind === 'kid') { const im = SA.strip(fk, 'idle'); if (im && im.complete !== false && im.width) src = { img: im, sx: 0, sy: 0, sw: 48, sh: 48, px: 24, py: 45 }; }
        else { const a = SA.atlasSrc(fk, 'idle', 0, true); if (a && a.src && a.src.img && a.src.img.width) src = a.src; }
        if (!src) return false; const t = document.createElement('canvas'); t.width = src.sw; t.height = src.sh; const tg = t.getContext('2d'); tg.imageSmoothingEnabled = false; tg.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 0, 0, src.sw, src.sh);
        if (look0 && J) { if (kind === 'kid') { const m = rowOf(fk, look0.h.pattern, 'idle'); const P = m && patCv(m.F.png, m.F.rows, look0.h.pattern, look0.hi, look0.lo); if (!P) return false; tg.drawImage(P.cv, 0, m.r.y - P.y0, 48, 48, 0, 0, 48, 48); }
          else { const sc = silo(src.img, src.sx, src.sy, src.sw, src.sh, src.px != null ? src.px : src.sw / 2, src.py != null ? src.py : src.sh - 3, fk, look0, 'base'); if (!sc) return false; tg.drawImage(sc, 0, 0, src.sw, src.sh, 0, 0, src.sw, src.sh); } }
        const bb = trim(t, 0, 0, src.sw, src.sh), k = Math.max(1, Math.floor((size * 0.9) / Math.max(bb.w, bb.h))), w = bb.w * k, h = bb.h * k;
        g.drawImage(t, bb.x, bb.y, bb.w, bb.h, Math.round((c.width - w) / 2), Math.round((c.height - h) / 2 + (ox0 || 0)), w, h); c.dataset.fk = fk || ''; c.dataset.pat = look0 ? look0.h.pattern : ''; return true; };
      let tries = 0; const go = () => { if (!c.isConnected && tries > 0) return; if (!draw() && ++tries < 24) setTimeout(go, 200); }; setTimeout(go, 0); return c;
    }
    function portrait(cand, size) { const c = mk('canvas', `position:absolute;width:${size}px;height:${size}px;image-rendering:pixelated;pointer-events:none`); c.width = size; c.height = size;
      const L = cand.id ? look(cand.id, cand.fk) : null; return petCanvas(c, size, cand.kind, cand.fk, L && L.h.hatched ? L : null); }

    // ── 揀上一代 ──
    const PK = { sel: {} };
    const childOf = () => { const p = C.pendOf(S()); if (p.length) return p[0].child; const s = S(), o = C.st(s); for (const e of C.eggs(s)) if (o.inh[e.id] && !o.inh[e.id].hatched) return e.id; return null; };
    const kindOf = (child) => { const s = S(), o = C.st(s); return (o.pend[child] && o.pend[child].kind) || (o.inh[child] && o.inh[child].kind) || (C.eggs(s).find(e => e.id === child) || {}).kind || 'kid'; };
    function pickView(child, from) {
      const s = S(); child = child || childOf(); if (!child) return { ok: false, reason: 'none' }; const cs = C.candidates(s, now(), ctx(), child); if (!cs.length) return { ok: false, reason: 'noCand' };
      const kind = kindOf(child), cur = C.inhOf(s, child); let sel = PK.sel[child] || (cur && cur.parent) || cs[0].id; if (!cs.some(c => c.id === sel)) sel = cs[0].id; PK.sel[child] = sel;
      const el = ov('pick', { child, from: from || '' }), pn = mk('div', `position:absolute;left:20px;top:190px;width:350px;height:572px;box-sizing:border-box;${bi('panel_navy')}`, null, 'l5c-pick'); el.appendChild(pn);
      plaque(pn, '揀上一代', 'l5c-pick-title'); closeX(pn, 'l5c-pick-close');
      const hd = mk('div', 'position:absolute;left:14px;right:14px;top:30px;height:44px;display:flex;align-items:center;gap:8px'); pn.appendChild(hd);
      hd.appendChild(img(kind === 'tr' ? ui5a('icon_egg_tr') : ui5a('icon_egg_kid'), 'position:relative;width:40px;height:40px;flex:0 0 40px'));
      hd.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), '邊隻做 BB 嘅上一代？', 'l5c-pick-sub'));
      const sc = mk('div', 'left:12px;right:12px;top:80px;height:300px', null, 'l5c-pick-grid'); sc.className = 'scr'; pn.appendChild(sc);
      const grid = mk('div', 'position:relative;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;padding:4px 0 8px'); sc.appendChild(grid);
      for (const c of cs) {
        const on = c.id === sel, d = mk('div', bi(on ? 'card_sel' : 'card'), null, 'l5c-card-' + c.id); d.className = 'l5ccard'; d.dataset.sel = on ? '1' : '0'; d.dataset.pattern = c.pattern; d.dataset.trick = c.trick; grid.appendChild(d);
        d.appendChild(mk('div', 'position:absolute;left:6px;right:6px;top:4px;text-align:center;white-space:nowrap;overflow:hidden;' + TXT(24, on ? GOLD : CREAM), c.name || (c.kind === 'tr' ? '團絨' : '細佬'), 'l5c-card-name-' + c.id));
        const pc = portrait(c, 52); pc.style.left = '8px'; pc.style.top = '34px'; d.appendChild(pc);
        if (c.main) d.appendChild(img(ui5a('icon_crown'), 'left:2px;top:28px;width:24px;height:24px'));
        if (c.away) d.appendChild(img(ui5b('icon_expedition'), 'left:40px;top:66px;width:24px;height:24px'));
        d.appendChild(img(swatch(c.pattern), 'left:70px;top:40px;width:34px;height:34px'));
        d.appendChild(img(ui5c('chip_trick_' + c.trick), 'left:110px;top:40px;width:34px;height:34px'));
        const pz = patZh(c.pattern), tz = TR(c.trick).propZh || lessonZh(c.trick), tg = pz.length + tz.length <= 4 ? pz + '・' + tz : patN(c.pattern);   // 24px 一行只夠 5 字：長就淨係寫花紋（招式睇 chip／下面預覽）
        d.appendChild(mk('div', 'position:absolute;left:2px;right:2px;top:82px;text-align:center;white-space:nowrap;' + TXT(24, SUB), tg, 'l5c-card-tag-' + c.id));
        d.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); PK.sel[child] = c.id; const st0 = sc.scrollTop; pickView(child, from); const g2 = OV.el && OV.el.querySelector('[data-testid=l5c-pick-grid]'); if (g2) g2.scrollTop = st0; note('sel', { child, id: c.id }); });
      }
      const C0 = cs.find(c => c.id === sel), fs = C.fastState(s, kind);
      const bar = mk('div', `position:absolute;left:12px;right:12px;top:388px;height:104px;box-sizing:border-box;padding:6px 10px;display:flex;flex-direction:column;gap:4px;${bi('panel_inset')}`, null, 'l5c-preview'); pn.appendChild(bar);
      const r1 = mk('div', 'position:relative;display:flex;align-items:center;gap:6px;height:44px'); bar.appendChild(r1);
      r1.appendChild(mk('span', 'position:relative;' + TXT(24, GOLD), '會遺傳：'));
      r1.appendChild(img(swatch(C0.pattern), 'position:relative;width:32px;height:32px;flex:0 0 32px')); r1.appendChild(mk('span', 'position:relative;white-space:nowrap;' + TXT(24, CREAM), patN(C0.pattern), 'l5c-preview-pat'));
      const r2 = mk('div', 'position:relative;display:flex;align-items:center;gap:6px;height:44px'); bar.appendChild(r2);
      r2.appendChild(img(ui5c('chip_trick_' + C0.trick), 'position:relative;width:32px;height:32px;flex:0 0 32px')); r2.appendChild(mk('span', 'position:relative;white-space:nowrap;' + TXT(24, CREAM), lessonZh(C0.trick), 'l5c-preview-trick'));
      r2.appendChild(mk('span', 'position:relative;flex:1 1 auto'));
      r2.appendChild(pill(fs, 'l5c-preview-fast'));
      const go = btn('就佢喇！', 'btn_pri', 200, 52, 'l5c-pick-ok', () => { const r = C.choose(S(), child, sel, now(), ctx()); note('choose', { child, id: sel, ok: r.ok, reason: r.reason }); if (!r.ok) { toast('揀唔到', 1800); return; } save(); closeOv(); SND('reward'); toast((C0.name || '佢') + '做咗上一代', 2000); });
      go.style.left = '75px'; go.style.top = '504px'; pn.appendChild(go);
      return { ok: true, child, n: cs.length, sel, kind };
    }
    function pill(fs, tid) {
      const P = { on: ['成長快 20%', '#2F7F92', '#6FE0D0'], locked: ['Lv3 先解鎖', '#4A4656', '#8C8796'], tr: ['團絨蛋唔計', '#4A4656', '#8C8796'] }[fs] || ['', '#4A4656', '#8C8796'];
      const d = mk('div', `position:relative;flex:0 0 auto;display:flex;align-items:center;gap:4px;min-height:40px;padding:2px 10px 2px 4px;box-sizing:border-box;background:${P[1]};border:3px solid ${P[2]};border-radius:20px;white-space:nowrap` + ';' + TXT(24, CREAM), null, tid);
      d.dataset.fast = fs; d.appendChild(img(ui5c('icon_fast'), 'position:relative;width:30px;height:30px;flex:0 0 30px;' + (fs === 'on' ? '' : 'filter:grayscale(1) brightness(.9);'))); d.appendChild(mk('span', 'position:relative', P[0])); return d;
    }
    const SND = (k) => { const a = NS.audio; if (a && a.Engine && a.Engine.sfx) try { a.Engine.sfx(k); } catch (e) { } };

    // ── 遺傳咗！──
    function resultView(child, opt) {
      opt = opt || {}; const s = S(); child = child || lastInh(); const h = child && C.inhOf(s, child); if (!h) return { ok: false, reason: 'none' };
      const kind = h.kind, fk = opt.fk || (kind === 'tr' ? trFk() : (kidFk() || 'S1')), t = J ? C.tintPair(J, h, fk) : null, L = t ? { h: Object.assign({}, h, { hatched: 1 }), hi: t.hi, lo: t.lo } : null;
      const el = ov('result', { child }); el.appendChild(mk('div', '', null, 'l5c-rays')).className = 'l5crays';
      const col = mk('div', 'position:absolute;left:20px;top:200px;width:350px;display:flex;flex-direction:column;align-items:center;gap:10px', null, 'l5c-result'); el.appendChild(col);
      const pl = mk('div', `position:relative;min-width:208px;height:48px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 16px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '遺傳咗！', 'l5c-result-title'); col.appendChild(pl);
      const cv = mk('canvas', 'position:relative;width:192px;height:192px;image-rendering:pixelated', null, 'l5c-result-pet'); cv.width = 192; cv.height = 192; cv.className = 'l5cpet'; cv.style.clipPath = 'inset(100% 0 0 0)'; col.appendChild(cv); petCanvas(cv, 192, kind, fk, L);
      setTimeout(() => { cv.style.clipPath = 'inset(0 0 0 0)'; }, 60);
      const gen = kind === 'tr' ? (s.gen || 1) : null; col.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), kind === 'tr' ? '新團絨（第 ' + gen + ' 代）' : 'BB 細佬', 'l5c-result-name'));
      const row = (icn, t1, t2, tid) => { const r = mk('div', bi('card'), null, tid); r.className = 'l5crow'; r.appendChild(img(icn, 'position:relative;width:40px;height:40px;flex:0 0 40px'));
        const c2 = mk('div', 'position:relative;flex:1 1 auto;min-width:0;display:flex;flex-direction:column'); c2.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), t1)); c2.appendChild(mk('div', 'position:relative;' + TXT(24, CREAM), t2, tid + '-sub')); r.appendChild(c2); col.appendChild(r); return r; };
      const ra = row(swatch(h.pattern), patN(h.pattern), (h.f6d ? '朋友 ' + h.f6d + ' 嘅色（蛋碼）' : '上一代 ' + (h.pname || '') + ' 嘅色'), 'l5c-result-pat'), rb = row(ui5c('chip_trick_' + h.trick), '家傳招式：' + lessonZh(h.trick), (String(TR(h.trick).title || '').match(/→.*$/) || [''])[0], 'l5c-result-trick');
      setTimeout(() => ra.classList.add('in'), 360); setTimeout(() => rb.classList.add('in'), 480);
      const fs = kind === 'tr' ? 'tr' : h.hatched ? (h.fast ? 'on' : 'locked') : C.fastState(s, kind); col.appendChild(pill(fs, 'l5c-result-fast'));
      const okb = btn('好可愛！', 'btn_pri', 200, 52, 'l5c-result-ok', () => closeOv()); okb.style.position = 'relative'; col.appendChild(okb);
      SND('reward'); return { ok: true, child, kind, pattern: h.pattern, trick: h.trick, fast: fs };
    }
    const lastInh = () => { const o = C.st(S()); let best = null; for (const id of Object.keys(o.inh)) if (!best || (o.inh[id].at || 0) >= (o.inh[best].at || 0)) best = id; return best; };

    // ── 花園 rail「上一代」掣（有蛋等緊揀） ──
    const RB = { el: null };
    function railTick() {
      const s = S(), pend = !!C.pendOf(s).length, show = !!childOf() && !document.body.classList.contains('s2-scene'); let el = RB.el;   // 未孵都可以再開改揀；紅點＝未揀
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), host = rail || document.getElementById('top-r'); if (!host) return;
        el = RB.el = mk('div', '', null, 'l5c-rail'); el.id = 'l5cbtn'; el.className = 'ibtn panel'; el.title = '上一代';
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l">上一代</i><i class="rd"></i>'; el.querySelector('i.i').appendChild(img(ui5c('icon_inherit'), 'left:0;top:0;width:36px;height:36px'));
        el.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); pickView(null, 'rail'); }); host.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return; const rd = el.querySelector('i.rd'); if (rd) rd.style.display = pend ? '' : 'none';
      const u = U(), rl = u && u.rail, egg = document.getElementById('l5egg'), eggOn = egg && egg.style.display !== 'none', st = eggOn ? 2 : 1;
      if (rl && rl.kid && rl.dex) { el.style.left = rl.kid.x + 'px'; el.style.top = (rl.kid.y + st * (rl.kid.y - rl.dex.y)) + 'px'; } else { el.style.left = '360px'; el.style.top = (320 + (st - 1) * 64) + 'px'; }
    }

    // ── 族譜卡：上一代花紋＋招式 ──
    G.l5cNode = function (d, n) {
      const s = S(), h = n && n.id && C.inhOf(s, n.id); if (!h) return; const pills = [...d.children].find(c => c.style && c.style.top === '62px'); const host = pills || d;
      const w = mk('span', 'position:relative;display:inline-flex;gap:2px;align-items:center', null, 'l5c-node-' + n.id); w.dataset.pattern = h.pattern; w.dataset.trick = h.trick; w.dataset.parent = h.parent; w.title = '上一代：' + (h.pname || '') + '・' + patZh(h.pattern) + '・' + lessonZh(h.trick);
      w.appendChild(img(swatch(h.pattern), 'position:relative;width:26px;height:26px')); w.appendChild(img(ui5c('chip_trick_' + h.trick), 'position:relative;width:26px;height:26px')); host.appendChild(w);
    };

    // ── 家傳招式：花園 idle 每 45–90 秒 ──
    const TK = { next: 0, n: 0, last: null };
    const nextGap = () => 45000 + Math.random() * 45000;
    function performer() {
      const s = S(); if (!s || !s.fam) return null; const p = SR.st(s), k = p.phase === 'kid' ? C.inhOf(s, FAM.kidId(s)) : null, t = s.stage !== 'egg' && !s.fam.km ? C.inhOf(s, FAM.trId(s)) : null;
      const xs = []; if (k && k.hatched && k.kind === 'kid') xs.push({ who: 'kid', L: k.trick }); if (t && t.hatched && t.kind === 'tr') xs.push({ who: 'tr', L: t.trick }); if (!xs.length) return null; return xs[TK.n % xs.length];
    }
    function doTrick(who, L) {
      const s = S(); let pf = performer(); if (who || L) pf = { who: who || (pf && pf.who) || 'kid', L: L || (pf && pf.L) || 'A' }; if (!pf) return { ok: false, reason: 'none' };
      const r = SA.trick ? SA.trick(pf.L, pf.who) : { ok: false, reason: 'api' }; note('trick', Object.assign({ ok: r.ok, reason: r.reason }, pf)); if (r.ok) { TK.n++; TK.last = pf; C.st(s).n.tricks++; save(); } return Object.assign({}, r, pf);
    }
    function trickTick() {
      const t = pnow(); if (!TK.next) TK.next = t + nextGap(); if (t < TK.next) return; TK.next = t + nextGap(); if (QUIET || busy()) return; const h = H5(); if (h && h.isOpen && h.isOpen()) return; const s = S(); if (!s || s.sleeping) return;
      if (SA.scene && SA.scene()) return; if (performer()) doTrick();
    }

    // ── 事件 ──
    const T = { n: 0, last: 0, evs: [], q: [] };
    function handle(ev) {
      for (const e of ev) { T.evs.push(Object.assign({ at: Math.round(pnow()) }, e)); if (T.evs.length > 60) T.evs.shift();
        if (e.k === 'pend') { if (!QUIET) T.q.push({ k: 'pick', child: e.child }); }
        else if (e.k === 'auto') { T.q = T.q.filter(q => !(q.k === 'pick' && q.child === e.child)); if (OV.kind === 'pick' && OV.data && OV.data.child === e.child) closeOv(true); if (!QUIET) toast(C.LINES.auto.replace('{name}', e.name || '佢'), 2400); }
        else if (e.k === 'hatched') { T.q = T.q.filter(q => !(q.k === 'pick' && q.child === e.child)); if (!QUIET) T.q.push({ k: 'result', child: e.child }); }
      }
    }
    function tick(force) {
      const t = pnow(); if (!force && t - T.last < 1000) return; T.last = t; const s = S(); if (!s || !s.fam) { railTick(); return; } T.n++;
      let ev; try { ev = C.scan(s, now(), ctx()); } catch (e) { note('scanErr', { e: String(e && e.message || e) }); return; }
      if (ev.length) { handle(ev); save(); if (H5() && H5().isOpen()) try { H5().refresh(); } catch (e) { } }
      if (T.q.length && !busy()) { const q = T.q.shift(); if (q.k === 'pick') { if (C.st(s).pend[q.child]) pickView(q.child, 'auto'); } else if (q.k === 'result') resultView(q.child); }
      railTick(); try { trickTick(); } catch (e) { }
    }
    const s2t = G.s2Tick; G.s2Tick = function () { const r = s2t ? s2t.apply(this, arguments) : undefined; try { tick(); } catch (e) { note('tickErr', { e: String(e && e.message || e) }); } return r; };
    setTimeout(() => { try { tick(true); } catch (e) { } }, 800);

    // ── 🛠 開發者模式「5c」 ──
    const q5 = () => (window.__qa && __qa.l5) || null;
    const d5 = (k) => { const q = q5(); if (!q) return { ok: false, msg: '冇 5a' }; const it = q.dev().items.find(i => i.k === k); return it ? it.run() : { ok: false, msg: '冇 ' + k }; };
    const adults = (n) => { const q = q5(); if (!q) return { ok: false, msg: '冇 5a' }; const e = d5('prep'); if (e && e.ok === false) return e; const s = S(); if (!FAM.trAdult(s) && !FAM.st(s).km && q.elder) q.elder();   /* 主團絨都要成年先揀得 */ let k = 0; while (FAM.st(s).res.length < (n || 2) && k++ < 6) if (!q.addRes(FAM.st(s).res.length % 2 ? 'kid' : 'tr')) break; return null; };
    const newEgg = (which) => { const e = adults(2); if (e) return e; const r = d5(which === 'tr' ? 'pickTr' : 'pickKid'); if (r && r.ok === false) return r; tick(true); T.q = []; return null; };
    const pickRes = (r) => (r.ok ? { ok: true, msg: '揀上一代：' + r.n + ' 隻成年' } : { ok: false, msg: r.reason === 'none' ? '冇蛋等緊（撳「準備」）' : '屋企冇成年' });
    function hatchNow() {
      const s = S(), c = childOf(); if (!c) return { ok: false, msg: '冇蛋等緊' }; const kind = kindOf(c);
      if (kind === 'kid') { const p = SR.st(s); if (p.phase !== 'egg') return { ok: false, msg: '細佬唔係蛋' }; SR.hatch(s, now()); }
      else { if (G.evo && G.evo.setStage) G.evo.setStage('newborn'); else s.stage = 'newborn'; }
      T.q = []; const ev = C.scan(s, now(), ctx()); handle(ev); T.q = T.q.filter(q => q.k !== 'result'); save(); const h = C.inhOf(s, c); resultView(c); return { ok: !!h, msg: h ? '孵咗：' + patZh(h.pattern) + '・' + lessonZh(h.trick) + (h.fast ? '・快 20%' : '') + (h.auto ? '（自動揀）' : '') : '冇遺傳' };
    }
    const DEV = { id: 'l5c', title: '5c（承傳）', order: 44,
      status: () => { const m = C.summary(S()); return '等緊揀 ' + m.pend.length + '・已遺傳 ' + Object.keys(m.inh).length + '・自動 ' + m.n.auto + '・招式 ' + m.n.tricks + '・加速 ' + (m.fastOk ? '開' : '鎖') + (m.fast ? '（而家 ×' + m.fast + '）' : ''); },
      items: [
        ['prep', '準備：屋企有成年＋新細佬蛋（等揀上一代）', () => { const e = newEgg('kid'); if (e) return e; return pickRes(pickView(null, 'dev')); }],
        ['prepTr', '準備：新團絨蛋（第二代；等揀上一代）', () => { const e = newEgg('tr'); if (e) return e; return pickRes(pickView(null, 'dev')); }],
        ['pick', '開「揀上一代」', () => pickRes(pickView(null, 'dev'))],
        ['hatch', '即刻孵（未揀就自動揀）→ 遺傳結果', () => hatchNow()],
        ['result', '睇「遺傳咗！」（最近一隻）', () => { const r = resultView(); return r.ok ? { ok: true, msg: patZh(r.pattern) + '・' + lessonZh(r.trick) } : { ok: false, msg: '未有遺傳（撳「準備」→「孵」）' }; }],
        ['trick', '細佬做家傳招式', () => { closeOv(true); const r = doTrick('kid'); return r.ok ? { ok: true, msg: '招式 ' + lessonZh(r.L) } : { ok: false, msg: '做唔到（' + r.reason + '）' }; }],
        ['trickTr', '團絨做家傳招式（示範）', () => { closeOv(true); const r = doTrick('tr'); return r.ok ? { ok: true, msg: '示範 ' + lessonZh(r.L) } : { ok: false, msg: '做唔到（' + r.reason + '）' }; }],
        ['demo', '團絨示範 +1（隨機一課）', () => { const s = S(), L = SR.LINES[(Math.random() * SR.LINES.length) | 0]; C.noteDemo(s, FAM.trId(s), L, now()); save(); const t = C.trickOf(s, { kind: 'tr', id: FAM.trId(s) }); return { ok: true, msg: '示範 ' + lessonZh(L) + '；而家傳：' + lessonZh(t.L) }; }],
        ['fast', '家族 Lv3（開成長快 20%）', () => { const q = q5(); if (!q) return { ok: false, msg: '冇 5a' }; q.xpTo(3); tick(true); return { ok: true, msg: '家族 Lv' + FAM.st(S()).lv + '・加速 ' + (C.fastOk(S()) ? '開' : '鎖') }; }],
        ['reset', '重設 5c（清承傳資料）', () => { C.reset(S()); PK.sel = {}; T.q = []; closeOv(true); save(); return { ok: true, msg: '5c 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l5c = { pick: pickView, result: resultView, close: () => closeOv(), open: () => OV.kind, tick: () => tick(true), trick: doTrick };
    window.__qa = window.__qa || {};
    window.__qa.l5c = {
      st: () => Object.assign(C.summary(S()), { ov: OV.kind, ovData: OV.data, quiet: QUIET, ticks: T.n, q: T.q.slice(), json: !!J, stat: Object.assign({}, STAT), rail: !!(RB.el && RB.el.style.display !== 'none'), tricks: TK.n, cache: PC.size }),
      pick: pickView, result: resultView, close: () => closeOv(), choose: (child, id) => { const r = C.choose(S(), child, id, now(), ctx()); save(); return r; }, cands: (child) => C.candidates(S(), now(), ctx(), child || childOf()),
      child: () => childOf(), hatch: hatchNow, trick: doTrick, tick: () => tick(true), log: () => log.slice(), evs: () => T.evs.slice(), toasts: () => toasts.slice(), dev: () => DEV, raw: () => JSON.parse(JSON.stringify(C.st(S()))), trickNext: (ms) => { TK.next = pnow() + (ms || 0); } };
    return true;
  }
  return { install };
});
