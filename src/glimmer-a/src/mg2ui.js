/* 《微光小圃》 mg2ui.js — 小遊戲 v2 畫面（docs-gdd/minigames-v2.md）。原創代碼。
   全螢幕 <canvas>（邏輯 180×320 直向，×2 畫，pixelated），冇文字掣：手勢＋icon（計時條、分數像素數字、× 離開、變化 icon、結果星＋星星碎 icon）。
   邏輯＝minigames2.js；獎勵＝systems2.gameFinish（錢包＋每日上限）。由 G.sysTick 驅動（同主迴圈同一 rAF）；玩緊時主世界行為／事件暫停（main.js mg2Busy）。
   美術：團絨＝現有 evo atlas clip；背景＝HD-2D H1（日）／H2（捉迷藏）／H4（夜）sky＋far＋mid；螢火＝H4 particles firefly_*；花盆＝atlas_props flowerpot；
   情緒泡＝atlas_props sweat／exclaim／heart／question；星星碎＝systems12 icon_star_shard_16。其餘（葉彈床、光點、雨雲、遮擋物、尾／燈泡、樹枝、變化 icon、星）程序化佔位 → 待遊美。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.mg2ui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const W = 180, H = 320, K = 2;
  const DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001', '111100111001111', '111100111101111', '111001010010010', '111101111101111', '111101111001111'];
  function install(G, NS) {
    const D = NS.data, P2 = D.PARAMS.systems12b, C2 = D.PARAMS.minigames2, M = NS.mg2, X2 = NS.sys12b, UI = NS.ui;
    if (!C2 || !M || !X2) return false;
    const S = () => G.state, now = () => G.now(), base = (D.PARAMS.art && D.PARAMS.art.base) || 'art/';
    const SND = (k, i) => { const a = NS.audio; if (a && a.Engine) a.Engine.notify(k, i || {}); };
    const css = document.createElement('style'); css.textContent = `
      #mg2 { position:absolute; inset:0; z-index:65; display:none; pointer-events:auto; align-items:center; justify-content:center; background:#0b0a1a; touch-action:none; user-select:none; -webkit-user-select:none; }
      #mg2 canvas { image-rendering:pixelated; image-rendering:crisp-edges; touch-action:none; display:block; }`;
    document.head.appendChild(css);
    const box = document.createElement('div'); box.id = 'mg2'; box.dataset.testid = 'mg2';
    const cv = document.createElement('canvas'); cv.width = W * K; cv.height = H * K; cv.dataset.testid = 'mg2-canvas'; box.appendChild(cv);
    (document.getElementById('ui') || document.body).appendChild(box);
    const ctx = cv.getContext('2d'); ctx.imageSmoothingEnabled = false;
    ['pointerdown', 'pointermove', 'pointerup', 'touchstart', 'touchmove', 'mousedown', 'click', 'dblclick', 'wheel'].forEach(tp => box.addEventListener(tp, e => e.stopPropagation(), { passive: tp !== 'pointerdown' }));
    // ── 圖 ──
    const IMG = {}; const img = (k, u) => { if (!IMG[k]) { const im = new Image(); im.onload = () => { im.ok = true; }; im.src = base + u; IMG[k] = im; } return IMG[k].ok ? IMG[k] : null; };
    let PART = null; try { fetch(base + 'hd2d/particles/particles.json').then(r => r.json()).then(j => { PART = j.frames || j; }).catch(() => {}); } catch (e) { }
    const SCN = { bounce: 'H1', ghide: 'H2', firefly: 'H4' };
    function drawBg(kind) {
      const sc = SCN[kind], s = W / 195, oy = 300 - 292 * s, L = n => img(sc + n, 'hd2d/' + sc + '/' + n + '.png');
      const sky = L('sky'); ctx.fillStyle = kind === 'firefly' ? '#141634' : '#9fc8e8'; ctx.fillRect(0, 0, W, H);
      if (sky) ctx.drawImage(sky, 14, 12, 195, 60, 0, 0, W, oy + 4);
      ['sky', 'far', 'mid'].forEach(n => { const im = L(n); if (im) ctx.drawImage(im, 0, 0, 223, 446, -14 * s, oy - 12 * s, 223 * s, 446 * s); });
    }
    // ── 團絨 ──
    let T = 0;
    function petSrc(clip, t) {
      const rd = G.renderer; if (!rd || !rd.atlasSrc) return null; const fk = rd.fkOf(S()), F = D.FORMS[fk]; if (!F || !F.atlas) return null;
      const A = rd.atlas && rd.atlas[F.atlas], an = A && A.json.animations[clip], fps = (an && an.fps) || 8;
      return rd.atlasSrc(F.atlas, clip, Math.floor(t * fps)) || rd.atlasSrc(F.atlas, 'idle', Math.floor(t * 6));
    }
    function drawPet(x, y, clip, rot, face, alpha) {
      const src = petSrc(clip, T); ctx.save(); ctx.globalAlpha = alpha == null ? 1 : alpha; ctx.translate(x, y);
      if (src) { const hh = src.sh * 0.45; if (rot) { ctx.translate(0, -hh); ctx.rotate(rot * (face || 1)); ctx.translate(0, hh); } ctx.scale(face < 0 ? -1 : 1, 1); ctx.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, -src.px, -src.py, src.sw, src.sh); }
      else { if (rot) { ctx.translate(0, -10); ctx.rotate(rot); ctx.translate(0, 10); } ctx.fillStyle = '#ffe7a8'; ctx.beginPath(); ctx.ellipse(0, -10, 11, 10, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#3a2a1a'; ctx.fillRect(-4, -12, 2, 2); ctx.fillRect(2, -12, 2, 2); }
      ctx.restore(); return src;
    }
    function emote(name, x, y) { const rd = G.renderer; const s = rd && rd.atlasSrc ? rd.atlasSrc('atlas_props', name, Math.floor(T * 6)) : null; if (s) ctx.drawImage(s.img, s.sx, s.sy, s.sw, s.sh, Math.round(x - s.sw / 2), Math.round(y - s.sh), s.sw, s.sh); }
    const EMO = { fall: 'sweat', bump: 'sweat', cool: null, proud: 'heart', surprised: 'exclaim', shiver: 'sweat', sad: 'question', win: 'heart' };
    // ── 小工具 ──
    function digits(n, x, y, px, col, right) { const s = String(Math.max(0, n | 0)); let cx = right ? x - s.length * 4 * px + px : x; ctx.fillStyle = col || '#fff6dc'; for (const ch of s) { const b = DIG[+ch]; for (let i = 0; i < 15; i++) if (b[i] === '1') ctx.fillRect(cx + (i % 3) * px, y + Math.floor(i / 3) * px, px, px); cx += 4 * px; } }
    function glow(x, y, r, col, a) { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.globalAlpha = a == null ? 1 : a; ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.globalAlpha = 1; }
    function star(x, y, r, on) { ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } ctx.closePath(); ctx.fillStyle = on ? '#ffd35a' : 'rgba(255,246,220,.18)'; ctx.fill(); ctx.strokeStyle = on ? '#a86a10' : 'rgba(255,246,220,.35)'; ctx.lineWidth = 1; ctx.stroke(); }
    function dot(x, y, gold, ph, sc) { const r = (gold ? 6 : 4.5) * (sc || 1), p = 1 + Math.sin(ph) * 0.15; glow(x, y, r * 3 * p, gold ? 'rgba(255,200,60,.8)' : 'rgba(255,246,170,.7)'); ctx.fillStyle = gold ? '#ffcf3a' : '#fff6b0'; ctx.beginPath(); ctx.arc(x, y, r * p, 0, 7); ctx.fill(); if (gold) { ctx.fillStyle = '#fff'; ctx.fillRect(x - 1, y - r - 3, 2, 3); ctx.fillRect(x - 1, y + r, 2, 3); ctx.fillRect(x - r - 3, y - 1, 3, 2); ctx.fillRect(x + r, y - 1, 3, 2); } }
    function modIcon(k, x, y, s, hard) {
      ctx.save(); ctx.translate(x, y); ctx.scale(s || 1, s || 1); ctx.fillStyle = 'rgba(20,16,40,.55)'; ctx.beginPath(); ctx.arc(0, 0, 8, 0, 7); ctx.fill(); ctx.strokeStyle = '#fff6dc'; ctx.fillStyle = '#fff6dc'; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
      const L = (a, b, c, d) => { ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c, d); ctx.stroke(); };
      const wind = H0 && H0.g && H0.g.windAx < 0 ? -1 : 1;
      switch (k) {
        case 'wind': case 'breeze': L(-5, -2, 4, -2); L(-3, 2, 5, 2); if (k === 'wind') { L(4 * wind, -2, 2 * wind, -4); L(4 * wind, -2, 2 * wind, 0); } break;
        case 'fast': case 'sneaky': L(-5, -4, -1, 0); L(-1, 0, -5, 4); L(0, -4, 4, 0); L(4, 0, 0, 4); break;
        case 'calm': L(-4, -4, 4, -4); L(4, -4, -4, 4); L(-4, 4, 4, 4); break;
        case 'gold': ctx.fillStyle = '#ffcf3a'; ctx.beginPath(); ctx.arc(0, 0, 3.5, 0, 7); ctx.fill(); ctx.fillRect(-0.7, -7, 1.4, 3); ctx.fillRect(-0.7, 4, 1.4, 3); ctx.fillRect(-7, -0.7, 3, 1.4); ctx.fillRect(4, -0.7, 3, 1.4); break;
        case 'small': ctx.fillStyle = '#fff6b0'; ctx.beginPath(); ctx.arc(0, 0, 2, 0, 7); ctx.fill(); L(-6, -6, -3, -3); L(6, -6, 3, -3); L(-6, 6, -3, 3); L(6, 6, 3, 3); break;
        case 'time': ctx.beginPath(); ctx.arc(-1, 1, 4.5, 0, 7); ctx.stroke(); L(-1, 1, -1, -2); L(-1, 1, 1.5, 1); L(4, -6, 4, -2); L(2, -4, 6, -4); break;
      }
      ctx.restore();
      if (hard) { ctx.save(); ctx.translate(x, y); ctx.scale(s || 1, s || 1); ctx.strokeStyle = '#ff8a6a'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(0, 0, 8.4, 0, 7); ctx.stroke(); ctx.restore(); }   // 難＝紅圈（冇文字）
    }
    // ── 遊戲狀態 ──
    let H0 = null;   // { kind, g, ph:'ready'|'play'|'result', rt, res, seed, ptr }
    function canStart(kind) {
      const s = S(); if (s.stage === 'egg') return 'egg'; if (s.sleeping) return 'sleep';
      if (H0 || G.mode === 'minigame') return 'busy'; if (kind === 'firefly' && !M.fireflyOpen(G.hour())) return 'night'; return null;
    }
    const WHY = { egg: '光卵仲未孵化', sleep: '團絨瞓緊，先開燈', busy: '玩緊另一個遊戲', night: '追螢火夜晚先有（' + [D.PARAMS.evo6.nightFrom, D.PARAMS.evo6.nightTo].map(h => String(h).padStart(2, '0') + ':00').join('–') + '）' };
    function start(kind, seed, mods, opt) {
      opt = opt || {}; if (!C2[kind]) return false; const why = opt.force ? (H0 ? 'busy' : null) : canStart(kind);
      if (why) { if (UI.toast) UI.toast(WHY[why]); return false; }
      if (G.s12close && G.s12 && G.s12.open) G.s12close(); const pop = document.getElementById('pop'); if (pop) pop.style.display = 'none';
      const sd = (seed >>> 0) || G.fixedMg2Seed || ((Date.now() & 0xffffff) | 1);
      H0 = { kind, g: M.create(kind, sd, mods ? { mods } : null), ph: 'ready', rt: 0, res: null, seed: sd, ptr: null, quitR: false, duo: !!opt.duo };   // 4a：opt.duo＝細佬雙人（唔出碎、唔食額）
      G.mg2Busy = true; box.style.display = 'flex'; fit(); SND('mg-start'); draw(); return true;
    }
    function finish(quit) {
      if (!H0 || H0.ph === 'result') return null; const g = H0.g;
      if (quit) { close(); return null; }
      let r;
      if (H0.duo) { const a = (C2[H0.kind] && C2[H0.kind].starsAt) || []; let st = 0; for (let i = 0; i < a.length; i++) if (g.score >= a[i]) st = i + 1;   // 4a 雙人：唔經 gameFinish（冇碎、冇額、冇紀錄）
        const d = G.s2DuoDone ? G.s2DuoDone(g.score) : null; r = { kind: H0.kind, value: g.score, stars: Math.min(3, st), rewarded: false, want: 0, shards: 0, duo: true, duoN: d && d.n | 0 }; }
      else r = X2.gameFinish(S(), H0.kind, g.score, now(), H0.kind === 'ghide' ? { firstHits: g.firstHits } : {});
      r.mods = g.mods.map(m => m.k); r.hard = g.mods.filter(m => m.hard).map(m => m.k); r.seed = H0.seed; H0.res = r; H0.ph = 'result'; H0.rt = 0; G.lastMg2 = r;
      SND('mg-result', { win: r.stars >= 2 }); if (UI.processEvents) UI.processEvents(); G.save(); return r;
    }
    function close() { H0 = null; G.mg2Busy = false; box.style.display = 'none'; if (G.save) G.save(); }
    function fit() { const r = box.getBoundingClientRect(), s = Math.max(0.5, Math.min(r.width / W, r.height / H)); cv.style.width = Math.floor(W * s) + 'px'; cv.style.height = Math.floor(H * s) + 'px'; }
    window.addEventListener('resize', () => { if (H0) fit(); });
    // ── 輸入（邏輯座標）──
    const lp = e => { const r = cv.getBoundingClientRect(); return { x: (e.clientX - r.left) / r.width * W, y: (e.clientY - r.top) / r.height * H }; };
    function inQuit(p) { const s = (cv.getBoundingClientRect().width / W) || K; return Math.abs(p.x - 167) <= Math.max(13, 26 / s) && Math.abs(p.y - 15) <= Math.max(13, 26 / s); }   // 遊測 P2：× 撳位 ≥ 52 CSS px 方格（任何畫面縮放）
    function down(p) {
      if (!H0) return false;
      if (H0.ph === 'result') { if (H0.rt > 0.6) close(); return true; }
      if (inQuit(p)) { finish(true); return true; }
      if (H0.ph === 'ready') { H0.ph = 'play'; }
      H0.ptr = p; return H0.g.press(p.x, p.y);
    }
    function mv(p) { if (H0 && H0.ph === 'play' && H0.ptr) { H0.ptr = p; H0.g.move(p.x, p.y); } }
    function up() { if (H0 && H0.ptr) { H0.ptr = null; if (H0.ph === 'play') H0.g.release(); } }
    cv.addEventListener('pointerdown', e => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch (x) { } down(lp(e)); });
    cv.addEventListener('pointermove', e => { if (H0 && H0.ptr) mv(lp(e)); });
    cv.addEventListener('pointerup', e => up(lp(e))); cv.addEventListener('pointercancel', () => up());
    // ── 更新 ──
    const SMAP = { catch: 'mg-catch', big: 'mg-big', stone: 'mg-stone', jump: 'tap', rustle: 'tap' };
    function step(dt) {
      if (!H0) return; T += dt; H0.rt += dt; const g = H0.g;
      if (H0.ph === 'ready') { if (H0.rt >= 1.4) { H0.ph = 'play'; H0.rt = 0; } }
      else if (H0.ph === 'play') { g.update(dt); for (const s of g.snd) if (SMAP[s]) SND(SMAP[s]); g.snd.length = 0; if (g.over) finish(false); }
      else if (H0.ph === 'result') { g.tickReact(dt); }
      for (const f of (H0.fxl = H0.fxl || [])) f.t += dt; while (g.fx.length) { const f = g.fx.shift(); H0.fxl.push(Object.assign({ t: 0 }, f)); } H0.fxl = H0.fxl.filter(f => f.t < 0.8);
    }
    // ── 畫 ──
    function hud(g) {
      const left = g.left, tot = g.dur; ctx.fillStyle = 'rgba(10,8,30,.55)'; ctx.fillRect(0, 0, W, 30);
      ctx.fillStyle = 'rgba(255,246,220,.2)'; ctx.fillRect(34, 8, 112, 5); ctx.fillStyle = left < 8 ? '#ff8a5a' : '#ffd35a'; ctx.fillRect(34, 8, 112 * left / tot, 5);
      dot(10, 12, false, T * 3); digits(g.score, 18, 8, 2, '#fff6dc');
      if (g.kind === 'ghide') for (let i = 0; i < g.M.rounds; i++) { ctx.fillStyle = i < g.round ? '#ffd35a' : i === g.round ? '#fff6dc' : 'rgba(255,246,220,.3)'; ctx.fillRect(34 + i * 8, 17, 5, 5); }
      if (g.kind === 'ghide' && g.phase === 'seek') for (let i = 0; i < g.tries; i++) { ctx.fillStyle = '#ffb0c0'; ctx.beginPath(); ctx.arc(140 - i * 8, 20, 2.6, 0, 7); ctx.fill(); }
      g.mods.forEach((m, i) => modIcon(m.k, 64 + i * 18, 21, 0.8, m.hard));
      ctx.fillStyle = 'rgba(255,246,220,.18)'; ctx.beginPath(); ctx.arc(167, 15, 10, 0, 7); ctx.fill(); ctx.strokeStyle = '#fff6dc'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(163, 11); ctx.lineTo(171, 19); ctx.moveTo(171, 11); ctx.lineTo(163, 19); ctx.stroke();
    }
    function fxDraw() {
      for (const f of H0.fxl || []) { const a = 1 - f.t / 0.8, y = f.y - f.t * 24; ctx.globalAlpha = a;
        if (f.v) { ctx.fillStyle = f.type === 'gold' ? '#ffcf3a' : '#fff6b0'; ctx.fillRect(f.x - 6, y + 2, 3, 1); ctx.fillRect(f.x - 5, y + 1, 1, 3); digits(f.v, f.x - 1, y, 1, f.type === 'gold' ? '#ffcf3a' : '#fff6dc'); }
        else if (f.type === 'thud' || f.type === 'bump') { ctx.strokeStyle = '#fff6dc'; ctx.lineWidth = 1; for (let i = 0; i < 5; i++) { const an = -Math.PI * (0.1 + i * 0.2); ctx.beginPath(); ctx.moveTo(f.x + Math.cos(an) * 6, f.y + Math.sin(an) * 6 - 4); ctx.lineTo(f.x + Math.cos(an) * (9 + f.t * 12), f.y + Math.sin(an) * (9 + f.t * 12) - 4); ctx.stroke(); } }
        else if (f.type === 'miss') { ctx.fillStyle = '#c8b090'; for (let i = 0; i < 4; i++) ctx.fillRect(f.x - 8 + i * 5, f.y - 18 - f.t * 10 - (i % 2) * 3, 2, 2); }
        ctx.globalAlpha = 1; }
    }
    function petEmote(g, x, y) { const e = EMO[g.react]; if (e) emote(e, x + 8, y - 26); }
    function drawBounce(g) {
      const M2 = g.M, L = M2.leaf, p = g.pet;
      if (g.windAx) { ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1; for (let i = 0; i < 6; i++) { const yy = 50 + i * 37, xx = ((T * 60 * Math.sign(g.windAx) + i * 53) % 200 + 200) % 200 - 10; ctx.beginPath(); ctx.moveTo(xx, yy); ctx.lineTo(xx + 14 * Math.sign(g.windAx), yy); ctx.stroke(); } }
      for (const d of g.dots) dot(d.x, d.y, d.gold, d.ph, g.tgt);
      // 葉彈床：莖＋葉（儲力彎低）
      const bend = g.bend * 7, lw = g.leafW; ctx.strokeStyle = '#3d7a34'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(L.x, M2.groundY + 2); ctx.lineTo(L.x, L.y + 4 + bend * 0.5); ctx.stroke();
      ctx.fillStyle = '#2f6a2a'; ctx.beginPath(); ctx.ellipse(L.x, L.y + 3 + bend, lw / 2 + 2, 5 + bend * 0.6, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#6cc35a'; ctx.beginPath(); ctx.moveTo(L.x - lw / 2, L.y - 1); ctx.quadraticCurveTo(L.x, L.y + 8 + bend * 2, L.x + lw / 2, L.y - 1); ctx.quadraticCurveTo(L.x, L.y + 2 + bend, L.x - lw / 2, L.y - 1); ctx.fill();
      ctx.strokeStyle = '#3d7a34'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(L.x - lw / 2 + 3, L.y); ctx.quadraticCurveTo(L.x, L.y + 5 + bend * 1.5, L.x + lw / 2 - 3, L.y); ctx.stroke();
      const py = g.phase === 'ready' || g.phase === 'charge' ? L.y + 2 + bend * 1.2 : p.y;
      if (g.phase === 'charge') { ctx.strokeStyle = g.power >= M2.flipPower ? '#ffcf3a' : '#fff6dc'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, py - 14, 20, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * g.power); ctx.stroke(); }
      if (g.phase === 'air' && p.y < 0) { ctx.fillStyle = '#fff6dc'; ctx.beginPath(); ctx.moveTo(p.x, 32); ctx.lineTo(p.x - 4, 38); ctx.lineTo(p.x + 4, 38); ctx.fill(); }
      drawPet(p.x, py, g.clip, g.flip, g.face); petEmote(g, p.x, py);
      if (H0.duo && G.s2DrawKid) G.s2DrawKid(ctx, Math.min(170, L.x + lw / 2 + 22), M2.groundY, g.phase === 'air', T);   // 4a 細佬喺葉邊打氣
    }
    function cover(c, i, g) {
      const sh = c.shake > 0 ? Math.sin(T * 60) * 2 * Math.min(1, c.shake * 4) : c.wig > 0 ? Math.sin(T * 30) * 1.5 : 0, x = c.x + c.dx + sh, y = c.y; ctx.save(); if (c.tried && !(g.phase === 'reveal' && i === g.at)) ctx.globalAlpha = 0.55;
      ctx.fillStyle = 'rgba(0,0,0,.22)'; ctx.beginPath(); ctx.ellipse(c.x + c.dx, y, 15, 4, 0, 0, 7); ctx.fill();
      const rd = G.renderer, pot = c.type === 'pot' && rd && rd.atlasSrc ? rd.atlasSrc('atlas_props', c.shake > 0 || c.wig > 0 ? 'flowerpot_bump' : 'flowerpot_idle', Math.floor(T * 8)) : null;
      if (pot) { const s2 = 26 / Math.max(pot.sw, pot.sh) * 1.2; ctx.drawImage(pot.img, pot.sx, pot.sy, pot.sw, pot.sh, x - pot.sw * s2 / 2, y - pot.sh * s2 + 2, pot.sw * s2, pot.sh * s2); }
      else switch (c.type) {
        case 'pot': ctx.fillStyle = '#c0663a'; ctx.beginPath(); ctx.moveTo(x - 12, y - 22); ctx.lineTo(x + 12, y - 22); ctx.lineTo(x + 9, y); ctx.lineTo(x - 9, y); ctx.fill(); ctx.fillStyle = '#d9824f'; ctx.fillRect(x - 13, y - 24, 26, 5); break;
        case 'leaves': [[-9, -6, '#c7742e'], [8, -6, '#e0a040'], [0, -11, '#b85a2a'], [-3, -4, '#d98a30'], [5, -14, '#e8b850']].forEach(([dx, dy, col]) => { ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(x + dx, y + dy, 9, 6, dx * 0.05, 0, 7); ctx.fill(); }); break;
        case 'rock': ctx.fillStyle = '#8a8a96'; ctx.beginPath(); ctx.ellipse(x, y - 9, 15, 11, 0, Math.PI, 0); ctx.lineTo(x + 15, y); ctx.lineTo(x - 15, y); ctx.fill(); ctx.fillStyle = '#a8a8b4'; ctx.beginPath(); ctx.ellipse(x - 4, y - 14, 6, 3, -0.3, 0, 7); ctx.fill(); break;
        case 'bush': [[-8, -9, 9], [8, -9, 9], [0, -16, 10], [0, -7, 10]].forEach(([dx, dy, r]) => { ctx.fillStyle = dy < -12 ? '#4f9a44' : '#3e8238'; ctx.beginPath(); ctx.arc(x + dx, y + dy, r, 0, 7); ctx.fill(); }); ctx.fillStyle = '#ff9ab0'; ctx.fillRect(x - 6, y - 17, 2, 2); ctx.fillRect(x + 5, y - 12, 2, 2); break;
        case 'lantern': ctx.fillStyle = '#5a4030'; ctx.fillRect(x - 2, y - 26, 4, 26); ctx.fillRect(x - 9, y - 4, 18, 4); glow(x, y - 30, 14, 'rgba(255,190,90,.6)'); ctx.fillStyle = '#e8a050'; ctx.fillRect(x - 7, y - 36, 14, 12); ctx.fillStyle = '#ffe0a0'; ctx.fillRect(x - 4, y - 33, 8, 6); ctx.fillStyle = 'rgba(0,0,0,0)'; break;
      }
      ctx.restore();
    }
    function drawHide(g) {
      const peekC = g.peeking ? g.covers[g.at] : null, revealing = g.phase === 'reveal', rc = g.covers[g.at];
      g.covers.forEach((c, i) => {
        if (peekC === c && g.peekKind !== 'bulb') { const a = Math.min(1, g.peek * 4), cx = c.x + c.dx; ctx.globalAlpha = a; ctx.fillStyle = '#ffe9b8'; const wag = Math.sin(T * 14) * 2; ctx.beginPath(); ctx.ellipse(cx + 14 + wag, c.y - 6, 5, 3.5, 0.4, 0, 7); ctx.fill(); ctx.globalAlpha = 1; }
        cover(c, i, g);
        if (peekC === c && g.peekKind === 'bulb') { const a = Math.min(1, g.peek * 4), cx = c.x + c.dx; glow(cx, c.y - 30, 10, 'rgba(255,235,120,.9)', a); ctx.globalAlpha = a; ctx.fillStyle = '#ffe36a'; ctx.beginPath(); ctx.arc(cx, c.y - 30, 3, 0, 7); ctx.fill(); ctx.globalAlpha = 1; }
      });
      if (revealing && rc) { const u = Math.min(1, g.rt / (g.M.revealSec * 0.6)), x = rc.x + (rc.x < 90 ? 1 : -1) * 22 * u, y = rc.y + 6; drawPet(x, y, g.clip, 0, rc.x < 90 ? 1 : -1); petEmote(g, x, y); }
      if (g.has('wind')) { ctx.fillStyle = '#d98a30'; for (let i = 0; i < 4; i++) { const xx = ((T * 50 + i * 47) % 200) - 10, yy = 180 + i * 28 + Math.sin(T * 3 + i) * 6; ctx.fillRect(xx, yy, 3, 2); } }
    }
    function drawFirefly(g) {
      const p = g.pet;
      for (const b of g.branches) { ctx.strokeStyle = '#4a3020'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(b.x1, b.y1); ctx.lineTo(b.x2, b.y2); ctx.stroke(); ctx.strokeStyle = '#6a4a30'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.fillStyle = '#2f5a30'; ctx.beginPath(); ctx.ellipse((b.x1 + b.x2) / 2 + 3, (b.y1 + b.y2) / 2 - 3, 4, 2.5, 0.5, 0, 7); ctx.fill(); }
      if (g.path.length) { ctx.strokeStyle = 'rgba(200,255,170,.55)'; ctx.lineWidth = 2; ctx.setLineDash([3, 4]); ctx.beginPath(); ctx.moveTo(p.x, p.y); for (const q of g.path) ctx.lineTo(q.x, q.y); ctx.stroke(); ctx.setLineDash([]); }
      const pim = img('part', 'hd2d/particles/particles.png');
      for (const f of g.flies) {
        const br = 0.6 + 0.4 * Math.sin(f.ph * 4), a = br;
        glow(f.x, f.y, (f.gold ? 16 : 12) * g.tgt, f.gold ? 'rgba(255,210,80,.9)' : 'rgba(190,255,120,.85)', a);
        const fr = PART && pim ? PART['firefly_0' + (1 + (Math.floor(f.ph * 7) % 6))] : null;
        if (fr) { const q = fr.frame || fr; ctx.globalAlpha = Math.max(0.3, a); ctx.drawImage(pim, q.x, q.y, q.w, q.h, Math.round(f.x - q.w / 2), Math.round(f.y - q.h / 2), q.w, q.h); ctx.globalAlpha = 1; }
        else { ctx.fillStyle = f.gold ? '#ffd35a' : '#d8ff9a'; ctx.fillRect(Math.round(f.x) - 1, Math.round(f.y) - 1, 3, 3); }
      }
      drawPet(p.x, p.y, g.clip, 0, g.face); petEmote(g, p.x, p.y);
    }
    function drawReady(g) {
      ctx.fillStyle = 'rgba(10,8,30,.45)'; ctx.fillRect(0, 30, W, H - 30);
      g.mods.forEach((m, i) => modIcon(m.k, 66 + i * 48, 110, 2.2, m.hard));
      const ph = (T * 1.5) % 1; ctx.strokeStyle = '#fff6dc'; ctx.fillStyle = '#fff6dc'; ctx.lineWidth = 2;
      const hand = (x, y) => { ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fill(); ctx.fillRect(x - 2, y, 4, 10); };
      if (g.kind === 'bounce') { const L = g.M.leaf; ctx.beginPath(); ctx.arc(L.x, L.y - 14, 8 + ph * 12, 0, 7); ctx.stroke(); hand(L.x + 4, L.y - 10 + (ph < 0.5 ? 0 : 3)); ctx.beginPath(); ctx.moveTo(L.x, 200); ctx.lineTo(L.x, 160); ctx.moveTo(L.x - 5, 166); ctx.lineTo(L.x, 160); ctx.lineTo(L.x + 5, 166); ctx.stroke(); }
      else if (g.kind === 'ghide') { const c = g.covers[0]; ctx.beginPath(); ctx.arc(c.x, c.y - 10, 6 + ph * 10, 0, 7); ctx.stroke(); hand(c.x + 3, c.y - 6); }
      else { ctx.setLineDash([3, 4]); ctx.beginPath(); ctx.moveTo(90, 266); ctx.quadraticCurveTo(140, 200, 90, 150); ctx.stroke(); ctx.setLineDash([]); const u = ph, x = (1 - u) * (1 - u) * 90 + 2 * (1 - u) * u * 140 + u * u * 90, y = (1 - u) * (1 - u) * 266 + 2 * (1 - u) * u * 200 + u * u * 150; hand(x + 3, y + 3); }
    }
    function drawResult(g, r) {
      ctx.fillStyle = 'rgba(10,8,30,.72)'; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 3; i++) { const on = i < r.stars, pop = on ? Math.min(1, Math.max(0, (H0.rt - i * 0.25) * 4)) : 1; star(50 + i * 40, 92 - (i === 1 ? 8 : 0), (on ? 14 * (0.6 + 0.4 * pop) : 12), on && pop > 0); }
      digits(r.value, 90 + String(r.value).length * 6 - 4, 124, 4, '#fff6dc', true);
      const sh = img('shard', 'systems12/icon_star_shard_16.png'), n = r.rewarded ? r.shards : 0;
      if (r.duo) { ctx.fillStyle = '#ff9ab8'; ctx.font = 'bold 12px ' + (G.v3 && G.v3.on && G.v3.on() ? '"GlimmerV3Sans",' : '') + 'sans-serif'; ctx.textAlign = 'center'; ctx.fillText('♥ 細佬親密 +' + (r.duoN | 0), 90, 170); ctx.textAlign = 'left'; }
      else if (r.rewarded) { for (let i = 0; i < Math.max(1, n); i++) { const x = 90 - (Math.max(1, n) - 1) * 10 + i * 20; ctx.globalAlpha = n ? 1 : 0.3; if (sh) ctx.drawImage(sh, x - 8, 156, 16, 16); else { ctx.fillStyle = '#9fe0ff'; ctx.fillRect(x - 5, 159, 10, 10); } ctx.globalAlpha = 1; } }
      else { ctx.globalAlpha = 0.35; if (sh) ctx.drawImage(sh, 82, 156, 16, 16); ctx.globalAlpha = 1; ctx.strokeStyle = '#ff8a8a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(80, 174); ctx.lineTo(100, 154); ctx.stroke(); }
      drawPet(90, 262, g.clip, 0, 1); petEmote(g, 90, 262);
      if (H0.duo && G.s2DrawKid) G.s2DrawKid(ctx, 130, 262, true, T);
      if (H0.rt > 0.6) { const a = 0.5 + 0.5 * Math.sin(T * 5); ctx.globalAlpha = a; ctx.fillStyle = '#fff6dc'; ctx.beginPath(); ctx.arc(90, 296, 5, 0, 7); ctx.fill(); ctx.fillRect(88, 296, 4, 10); ctx.globalAlpha = 1; }
    }
    function draw() {
      if (!H0) return; const g = H0.g; ctx.setTransform(K, 0, 0, K, 0, 0); ctx.imageSmoothingEnabled = false;
      drawBg(H0.kind);
      if (H0.ph !== 'result') { if (H0.kind === 'bounce') drawBounce(g); else if (H0.kind === 'ghide') drawHide(g); else drawFirefly(g); fxDraw(); }
      hud(g);
      if (H0.ph === 'ready') drawReady(g); else if (H0.ph === 'result') drawResult(g, H0.res);
    }
    // ── 掛：tick／選單／遊戲 tab／DEV／QA ──
    const origTick = G.sysTick;
    G.sysTick = function (dt) { if (origTick) origTick(dt); if (H0) { step(Math.min(dt, 1 / 20)); draw(); } };
    G.mg2 = { start, active: () => !!H0, quit: () => finish(true), canStart };
    const nm = k => C2[k].name;
    G.mg2menu = function (item, note) {   // ui.js 玩樂選單
      C2.order.forEach(k => { const why = k === 'firefly' && !M.fireflyOpen(G.hour()) ? WHY.night : null; item(k === 'firefly' ? 'sleep' : k === 'ghide' ? 'play' : 'feed', nm(k), why || note, () => { if (start(k)) { const pop = document.getElementById('pop'); if (pop) pop.style.display = 'none'; } }, 'play-' + k); });
    };
    G.mg2rows = function (btn) {   // sys12ui2 小遊戲 tab
      const b = X2.st(S()).games.best, st = X2.st(S()).games.stars;
      return C2.order.map(k => { const why = canStart(k); return `<div class="s12row"><span class="t">${nm(k)}<small> ${C2[k].durationSec || C2[k].timeLimitSec} 秒・每局 2 個隨機變化・${C2[k].starsAt.join('／')} 分＝1／2／3★・最高 ${b[k] || 0}（${'★'.repeat(st[k] || 0)}）${k === 'firefly' ? '・夜晚限定' : ''}</small></span>${btn('開始', 'mg2:' + k, 's12b-play-' + k, why !== 'night' && why !== 'egg')}</div>`; }).join('');
    };
    G.s12dev = Object.assign(G.s12dev || {}, { bounce: () => start('bounce', 0, null, { force: true }), ghide: () => start('ghide', 0, null, { force: true }), firefly: () => start('firefly', 0, null, { force: true }), mg2quit: () => finish(true) });
    const snap = () => { if (!H0) return null; const g = H0.g, o = { kind: H0.kind, ph: H0.ph, seed: H0.seed, mods: g.mods.map(m => m.k), score: g.score, t: +g.t.toFixed(3), left: +g.left.toFixed(3), over: g.over, clip: g.clip, react: g.react, stars: g.stars };
      if (g.kind === 'bounce') Object.assign(o, { phase: g.phase, power: g.power, pet: Object.assign({}, g.pet), jumps: g.jumps, lands: g.lands, falls: g.falls, dots: g.dots.map(d => ({ x: d.x, y: d.y, gold: d.gold })), leafW: g.leafW, wind: g.windAx, unit: g.unit, tgt: g.tgt, spd: g.spd, flips: g.flips || 0, flipping: g.flipping });
      if (g.kind === 'ghide') Object.assign(o, { phase: g.phase, round: g.round, at: g.at, tries: g.tries, found: g.found, firstHits: g.firstHits, sneaks: g.sneaks, tail: g.tail, peekKind: g.peekKind, peeking: g.peeking, hitR: g.hitR, sneakSec: g.sneakSec, covers: g.covers.map(c => ({ x: c.x + c.dx, y: c.y, type: c.type, tried: c.tried, shake: c.shake, wig: c.wig })) });
      if (g.kind === 'firefly') Object.assign(o, { tgt: g.tgt, flySpd: g.flySpd, windX: g.windX, pet: Object.assign({}, g.pet), path: g.path.length, caught: g.caught, bumps: g.bumps, stun: g.stun, flies: g.flies.map(f => ({ x: f.x, y: f.y, gold: f.gold })), branches: g.branches.map(b => Object.assign({}, b)) });
      return o; };
    window.__qa = window.__qa || {};
    window.__qa.mg2 = { start: (k, seed, mods) => start(k, seed, mods, { force: true }), startNormal: (k, seed, mods) => start(k, seed, mods), state: snap, game: () => H0 && H0.g,
      press: (x, y) => down({ x, y }), move: (x, y) => mv({ x, y }), release: () => up(), tap: (x, y) => { const r = down({ x, y }); up(); return r; },
      step: (sec, f) => { const n = Math.round(sec * 60); for (let i = 0; i < n && H0; i++) { if (f) f(H0.g); step(1 / 60); } draw(); return snap(); }, skipReady: () => { if (H0 && H0.ph === 'ready') { H0.ph = 'play'; H0.rt = 0; } return !!H0; },
      quit: () => finish(true), close: () => { if (H0 && H0.ph === 'result') { H0.rt = 1; down({ x: 90, y: 160 }); } return !H0; }, last: () => G.lastMg2 || null, bench: n => { const t0 = performance.now(); for (let i = 0; i < n && H0; i++) { step(1 / 60); draw(); } return (performance.now() - t0) / n; }, rect: () => { const r = cv.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }, open: () => !!H0, fireflyOpen: h => M.fireflyOpen(h == null ? G.hour() : h), coverXY: i => H0 && H0.g.covers[i] ? { x: H0.g.covers[i].x, y: H0.g.covers[i].y - 8 } : null };
    return true;
  }
  return { install };
});
