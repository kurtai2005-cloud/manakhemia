/* 《微光小圃》 long6dui.js — 第 6 批 6d「朋友探訪＋交換蛋」介面（遊策 breakthrough-6a6d-spec §6d；冇伺服器、全離線）。原創代碼。
   邏輯全部喺 long6d.js（s.share6）；QR 用 qrlib.js（npm qr 0.7.2，MIT）喺本機編／解，冇網絡。
   ・花園 rail「朋友」→ 朋友面板：我嘅名片（分享圖＋QR＋複製碼／存圖／分享）、入朋友碼（貼上／揀相解 QR → 校驗 → 請佢嚟玩／收蛋碼）、
     交換蛋碼（家族 Lv4、每 7 日 1 個）、朋友簿；面板頂有今日「請咗 n／3 個朋友・手信 n／3」同而家嚟緊嘅影子。
   ・影子：朋友隻團絨 idle 幀 → 剪影（kit vi0／vi1／vi2 按亮度），整隻 globalAlpha 半透明（6d.2：Kurt 揀跟規格，唔再用 4×4 棋盤；spec 冇寫數 → 0.45），輪廓完整（唔抽像素）；頭頂 6d:friend_badge（唔跟住淡）；
     喺花園地面行來行去，每 40–70 秒走埋去同你隻團絨互動（泡泡一句＋心心）；撳影子睇朋友資料／早啲送佢返屋企。24 小時後自己走，留 1 件手信（每日 ≤3）。
   ・分享圖：share_card_bg 165×252（存相 @3x 495×756）；字（名／家族／形態／3 句記憶／短碼）由 code 落（V3 開＝源雲明體）；QR 模組用整數 px 畫入白位。
   ・原生（APK）：Capacitor Share6d plugin（複製／貼上／存相去 Pictures／分享）；冇 plugin → 瀏覽器 clipboard／下載。
   ・美術載唔到／?l6dart=0 → placeholder（洋紅虛線＋data-ph）。🛠 開發者模式「6d」；?l6d=0 全停。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6dui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const D6 = NS.long6d, UI = NS.ui, FAM = NS.long5a, QR = NS.qrlib, DATA = NS.data; if (!D6 || !UI) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l6d') === '0') return false;
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now();
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2400); };
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const V3F = () => !!(G.v3 && G.v3.want);
    const F12 = () => (U() ? (V3F() ? '"GlimmerV3Sans",' : '"GlimmerFP12",') : '') + FALL;
    const CREAM = '#FFF5DC', GOLD = '#FFE08A', MINT = '#B8F0C8', LAV = '#E6D8FF';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      btn16_dis: 'background:#8C8796;border:3px solid #4A4656;border-radius:8px;', panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || FB[n] || ''; };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const TXT = (size, color, extra) => `font:${U() ? 24 : Math.max(size, 20)}px/1.25 ${F12()};color:${color || CREAM};${OL}-webkit-font-smoothing:none;` + (extra || '');
    const V62 = () => { const u = document.getElementById('ui'); return !!(u && u.classList.contains('u62') && u.classList.contains('v2')); };
    const PAN = () => (V62() ? '' : bi('panel_navy'));
    const INSET = () => (V62() ? 'background:rgba(20,16,44,.72);border:1px solid rgba(232,194,122,.45);border-radius:10px;' : bi('panel_inset'));
    const subEl = (t, css) => { const d = mk('div', css || '', t, 'u62-sub'); d.className = 'u62sub'; return d; };
    const tx = (e) => { e.classList.add('l6dx'); return e; };   // 重疊檢查（ui62 overlap）用
    const SUBT = { main: '用朋友碼請朋友隻團絨嚟玩，冇網都得。', card: '俾朋友睇呢張名片或者複製個碼。', enter: '貼上朋友碼，或者揀一張有 QR 嘅相。', egg: '朋友入咗你個蛋碼，下一隻細佬蛋會帶你嘅花紋。', book: '嚟過嘅朋友都記低喺度。' };

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l6dcss';
    css.textContent = `#l6dov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:62;user-select:none;-webkit-user-select:none;touch-action:manipulation}
body.l6d-on #toast{z-index:73 !important}
#l6dov [data-ph],#l6dlay [data-ph]{outline:2px dashed #FF2BD6;outline-offset:-2px}
#l6dov .b6{position:relative;box-sizing:border-box;min-height:56px;display:flex !important;flex-direction:row !important;line-height:1.2 !important;align-items:center;justify-content:center;gap:8px;padding:4px 12px;cursor:pointer;text-align:center;white-space:nowrap}
#l6dov .b6.dis{filter:grayscale(.6);opacity:.75}
#l6dov .b6 i.ic{display:block;position:relative;flex:0 0 32px;width:32px;height:32px;pointer-events:none;background:center/contain no-repeat}
#l6dov textarea{display:block;width:100%;box-sizing:border-box;resize:none;border:0;outline:0;background:transparent;padding:10px 14px;word-break:break-all;overflow:hidden}
#l6dov .tabs{display:flex;gap:8px}
#l6dov .tabs .b6{flex:1 1 0;min-width:0;padding:4px 6px}
#l6dov .tabs .b6[data-on="1"]{box-shadow:0 0 0 3px #FFE08A}
#l6dov .scr{overflow-y:auto;overscroll-behavior:contain}
#l6dlay{position:absolute;left:0;top:0;width:390px;height:844px;pointer-events:none;z-index:1}
#l6dlay .sh6{position:absolute;width:0;height:0;pointer-events:none}
#l6dlay .sh6 canvas{position:absolute;image-rendering:pixelated;pointer-events:none}
#l6dlay .sh6 .ht{position:absolute;left:-28px;top:-76px;width:56px;height:76px;pointer-events:auto;cursor:pointer}
#l6dlay .sh6 .bdg{position:absolute;width:32px;height:32px;left:-16px;image-rendering:pixelated;pointer-events:none;animation:l6dbob 1.6s steps(2) infinite}
#l6dlay .bub{position:absolute;transform:translate(-50%,-100%);white-space:nowrap;padding:6px 12px;pointer-events:none;opacity:0;transition:opacity .3s}
#l6dlay .bub.on{opacity:1}
body.s2-scene #l6dlay,body.s2-house #l6dlay,body.l6c-on #l6dlay,body.l6d-hide #l6dlay{display:none}
#l6dbtn{cursor:pointer}
body.u62tipon #l6dbtn,#l6dbtn.l6d-yield{opacity:0 !important;pointer-events:none !important}
#l6dbtn > i.i{position:absolute;left:50%;top:50%;width:36px;height:36px;margin:-18px 0 0 -18px;pointer-events:none;background:center/contain no-repeat}
@keyframes l6dbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}`;
    document.head.appendChild(css);

    // ── 美術（art/breakthrough/6d：6030ff79 share6d.json；V3 開 icon 用 kit_hd2d_v3 atlas）──
    const B6D = 'art/breakthrough/6d/', NOART = qs.get('l6dart') === '0';
    const A = { j: null, img: {}, want: {}, err: [], dirty: 0, mask: null };
    const aimg = (f) => { if (NOART) return null; if (A.img[f]) return A.img[f]; if (!A.want[f]) { A.want[f] = 1; const i = new Image(); i.onload = () => { if (i.naturalWidth) { A.img[f] = i; A.dirty = 1; } }; i.onerror = () => A.err.push(f); i.src = B6D + f; } return null; };
    const A6d = NOART ? Promise.resolve() : fetch(B6D + 'share6d.json').then(r => (r.ok ? r.json() : null)).catch(() => null).then(j => { A.j = j && j.keys ? j : null; if (A.j) { aimg('parts/share_card_bg@3x.png'); aimg('parts/shadow_mask.png'); aimg('icons/friend_badge@3x.png'); } A.dirty = 1; });
    const isV3 = () => { const u = document.getElementById('ui'); return !!(u && u.classList.contains('v3') && G.v3 && G.v3.on && G.v3.on()); };
    const ICF = { share: 'icons/ic_share@3x.png', copy: 'icons/ic_copy@3x.png', paste: 'icons/ic_paste@3x.png', photo: 'icons/ic_photo@3x.png', qr: 'icons/ic_qr@3x.png', friend: 'icons/ic_friend@3x.png', egg_code: 'icons/ic_egg_code@3x.png', friend_badge: 'icons/friend_badge@3x.png' };
    /* icon URL：V3 開 → kit V3 atlas（share／copy／paste／photo／qr／friend／egg_code／friend_badge／gift）；否則 6d 美術；冇 → '' */
    function icon(n) {
      const u = U(), V = u && u.v3x; if (isV3() && V && V.has(n, true)) return V.iurl(n);
      if (ICF[n] && A.j && !NOART) { const im = aimg(ICF[n]); return im ? im.src : '';   /* im.src＝shim 已解析 URL（外置 _x webp／內嵌 data）；直接寫原路徑去 CSS 會喺 APK 404 */ }
      if (n === 'gift' && u && u.iurl) return u.iurl('gift') || '';
      return '';
    }
    const setIc = (el, n) => { const u = icon(n); if (u) { el.style.backgroundImage = 'url("' + u + '")'; delete el.dataset.ph; el.dataset.art = (isV3() ? 'v3:' : '6d:') + n; } else { el.dataset.ph = '6d:icon_' + n; } };
    const SHADOW_A = 0.45;   // 6d.2：規格「code 做半透明」冇寫數 → 約 0.45
    function maskBits() {   // 舊 4×4 棋盤（只用喺對比／備份；正式影子唔再 ∧ 棋盤）
      if (A.mask) return A.mask; const im = aimg('parts/shadow_mask.png'); if (!im) return null;
      try { const c = document.createElement('canvas'); c.width = 4; c.height = 4; const g = c.getContext('2d'); g.drawImage(im, 0, 0); const d = g.getImageData(0, 0, 4, 4).data, m = []; for (let i = 0; i < 16; i++) m.push(d[i * 4 + 3] > 127 && d[i * 4] > 127 ? 1 : 0); A.mask = m; } catch (e) { A.mask = null; }
      return A.mask;
    }

    // ── 原生／瀏覽器：複製、貼上、存相、分享 ──
    const NAT = () => { const C = window.Capacitor; if (C && C.isNativePlatform && C.isNativePlatform() && C.Plugins && C.Plugins.Share6d) return C.Plugins.Share6d; return window.__share6native || null; };
    async function copyText(t) {
      const N = NAT(); if (N) { try { await N.copy({ text: t }); return true; } catch (e) { } }
      try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(t); return true; } } catch (e) { }
      try { const ta = mk('textarea', 'position:fixed;left:-999px;top:0'); ta.value = t; document.body.appendChild(ta); ta.select(); const ok = document.execCommand('copy'); ta.remove(); return !!ok; } catch (e) { return false; }
    }
    async function pasteText() {
      const N = NAT(); if (N) { try { const r = await N.paste(); if (r && typeof r.text === 'string') return r.text; } catch (e) { } }
      try { if (navigator.clipboard && navigator.clipboard.readText) return await navigator.clipboard.readText(); } catch (e) { }
      return null;
    }
    async function saveImage(cv, name) {
      const url = cv.toDataURL('image/png'), N = NAT(); LAST.saved = { name, w: cv.width, h: cv.height, len: url.length };
      if (N) { try { const r = await N.saveImage({ data: url.split(',')[1], name }); return { ok: true, native: true, r }; } catch (e) { return { ok: false, err: String(e && e.message || e) }; } }
      try { const a = mk('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove(); return { ok: true, native: false }; } catch (e) { return { ok: false }; }
    }
    async function shareImage(cv, name, text) {
      const N = NAT(); if (N) { try { await N.share({ data: cv.toDataURL('image/png').split(',')[1], name, text }); return { ok: true, native: true }; } catch (e) { return { ok: false, err: String(e && e.message || e) }; } }
      try { if (navigator.canShare && cv.toBlob) { const b = await new Promise(r => cv.toBlob(r, 'image/png')); const f = new File([b], name, { type: 'image/png' }); if (navigator.canShare({ files: [f] })) { await navigator.share({ files: [f], text }); return { ok: true }; } } } catch (e) { }
      const c = await copyText(text); const s = await saveImage(cv, name); return { ok: c || s.ok, fallback: true };
    }
    const LAST = { saved: null };

    // ── QR（qrlib：ECC M；模組用整數 px 畫） ──
    function qrMatrix(text) { if (!QR) return null; try { const m = QR.encodeQR(text, 'raw', { ecc: 'medium', border: 1 }); return m.slice(1, -1).map(r => r.slice(1, -1)); } catch (e) { note('qrErr', { e: String(e && e.message || e) }); return null; } }
    function decodeImageData(id) { if (!QR) return null; try { return QR.decodeQR(id); } catch (e) { return null; } }
    async function decodeFile(file) {
      const url = URL.createObjectURL(file); try {
        const im = await new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('img')); i.src = url; });
        for (const max of [1600, 900, 2400]) { const k = Math.min(1, max / Math.max(im.naturalWidth, im.naturalHeight)), w = Math.max(1, Math.round(im.naturalWidth * k)), h = Math.max(1, Math.round(im.naturalHeight * k));
          const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d', { willReadFrequently: true }); g.imageSmoothingEnabled = k < 1; g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.drawImage(im, 0, 0, w, h);
          const t = decodeImageData(g.getImageData(0, 0, w, h)); if (t) return t; }
        return null;
      } catch (e) { return null; } finally { URL.revokeObjectURL(url); }
    }

    // ── 寵物幀（friend 用佢個 fk；冇 → 自己個）＋影子剪影 ──
    const fkNow = () => { const s = S(); if (!s || s.stage === 'egg') return null; try { return G.renderer && G.renderer.fkOf ? G.renderer.fkOf(s) : null; } catch (e) { return null; } };
    function petSrc(fk, ms) { const SA = G.s2Art; try { if (SA && SA.atlasSrc && fk) { const a = SA.atlasSrc(fk, 'idle', ms || 0, true); if (a && a.src && a.src.img && a.src.img.width) return a; } } catch (e) { } return null; }
    const VI = [[0xEE, 0xE2, 0xFF], [0xA9, 0x8B, 0xF0], [0x5C, 0x3F, 0xB0]];
    const SHC = new Map();
    function shadowCanvas(fk, ms, opt) {   // 回 { cv, px, py, w, h, frame }；冇 atlas → null。opt.dither＝舊棋盤（淨係對比圖用）
      const a = petSrc(fk, ms); if (!a) return null; const dither = !!(opt && opt.dither), m = dither ? (maskBits() || 'cb') : null;
      const s0 = a.src, key = fk + ':' + a.clip + ':' + a.frame + (dither ? ':d' : ':a');
      let c = SHC.get(key); if (c) return { cv: c, px: s0.px, py: s0.py, w: s0.sw, h: s0.sh, frame: a.frame, key };
      c = document.createElement('canvas'); c.width = s0.sw; c.height = s0.sh; const g = c.getContext('2d', { willReadFrequently: true }); g.imageSmoothingEnabled = false; g.drawImage(s0.img, s0.sx, s0.sy, s0.sw, s0.sh, 0, 0, s0.sw, s0.sh);
      try { const d = g.getImageData(0, 0, s0.sw, s0.sh), p = d.data;
        for (let y = 0; y < s0.sh; y++) for (let x = 0; x < s0.sw; x++) { const i = (y * s0.sw + x) * 4; const lit = p[i + 3] >= 128; const on = lit && (!dither || (m && m !== 'cb' ? m[(y % 4) * 4 + (x % 4)] : (x + y) % 2 === 0));
          if (!on) { p[i + 3] = 0; continue; } const L = p[i] * 0.299 + p[i + 1] * 0.587 + p[i + 2] * 0.114, col = L >= 120 ? VI[0] : L >= 60 ? VI[1] : VI[2]; p[i] = col[0]; p[i + 1] = col[1]; p[i + 2] = col[2]; p[i + 3] = 255; }
        g.putImageData(d, 0, 0); } catch (e) { }
      if (SHC.size > 120) SHC.clear(); SHC.set(key, c); return { cv: c, px: s0.px, py: s0.py, w: s0.sw, h: s0.sh, frame: a.frame, key };
    }
    function paintShadow(cv, sh) {   // 整隻寵物半透明（alpha 0.45）；只改影子自己張 canvas 嘅 alpha，RGB 保持三階紫（唔用 ctx.globalAlpha 疊透明底，免預乘取整偏色）；唔郁花園／發光／粒子／徽章
      cv.width = sh.w; cv.height = sh.h; const g = cv.getContext('2d', { willReadFrequently: true }); g.imageSmoothingEnabled = false; g.clearRect(0, 0, sh.w, sh.h); g.drawImage(sh.cv, 0, 0);
      try { const d = g.getImageData(0, 0, sh.w, sh.h), p = d.data, a = Math.round(255 * SHADOW_A); for (let i = 3; i < p.length; i += 4) if (p[i]) p[i] = a; g.putImageData(d, 0, 0); } catch (e) { }
      cv.style.width = sh.w * 2 + 'px'; cv.style.height = sh.h * 2 + 'px';
    }

    // ── 分享圖（165×252 art；k＝每 art px 幾多 px：存相 3＝495×756、畫面 6） ──
    const FORMZ = (form) => (DATA && DATA.FORM_NAME && DATA.FORM_NAME[form]) || '團絨';
    async function fontsReady() {   // 6d.2：等 font 真係 check 到（光 load 喺 FontFace 未 add 時會用後備字提早完）
      try { if (!document.fonts || !document.fonts.load) return; const names = ['GlimmerV3Serif', 'GlimmerV3Sans', 'GlimmerFP12'];
        const need = () => (V3F() ? ['GlimmerV3Sans'] : ['GlimmerFP12']);
        const t0 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
        while (((typeof performance !== 'undefined' ? performance.now() : Date.now()) - t0) < 4000) {
          await Promise.all(names.map(n => document.fonts.load((n.indexOf('Serif') >= 0 ? '700 ' : '400 ') + '24px ' + n).catch(() => {})));
          if (need().every(n => document.fonts.check('24px ' + n))) return;
          await new Promise(r => setTimeout(r, 50));
        }
      } catch (e) { } }
    function drawCard(cv, k, snap, code, kind) {
      const W = 165, H = 252; cv.width = W * k; cv.height = H * k; const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, cv.width, cv.height);
      const bg = A.j && aimg('parts/share_card_bg@3x.png'); let art = false;
      if (bg) { g.drawImage(bg, 0, 0, bg.naturalWidth, bg.naturalHeight, 0, 0, W * k, H * k); art = true; }
      else { g.fillStyle = '#1E2347'; g.fillRect(0, 0, W * k, H * k); g.strokeStyle = '#E8C27A'; g.lineWidth = 2 * k; g.strokeRect(k, k, (W - 2) * k, (H - 2) * k); g.fillStyle = '#FFFFFF'; g.fillRect(53 * k, 164 * k, 58 * k, 58 * k); }
      const v3 = V3F(), FS = (w) => (w ? '700 ' : '400 ') + Math.round(10.5 * k) + 'px ' + (v3 ? (w ? '"GlimmerV3Serif",' : '"GlimmerV3Sans",') : '"GlimmerFP12",') + FALL;
      const txt = (t, x, y, opt) => { opt = opt || {}; g.save(); g.font = FS(opt.b); g.textBaseline = 'middle'; g.textAlign = opt.c ? 'center' : 'left'; let s = String(t); const mw = (opt.mw || 999) * k;
        while (s.length > 1 && g.measureText(s).width > mw) s = s.slice(0, -1); if (s !== String(t)) s = s.slice(0, -1) + '…';
        g.lineJoin = 'round'; g.lineWidth = Math.max(2, Math.round(k * 1.2)); g.strokeStyle = '#24172C'; g.strokeText(s, x * k, y * k); g.fillStyle = opt.col || CREAM; g.fillText(s, x * k, y * k); g.restore(); return s; };
      txt(kind === 'egg' ? '交換蛋碼' : '朋友名片', 82.5, 9, { c: 1, b: 1, col: '#FFFFFF', mw: 92 });
      // 頭像：idle 第 0 幀，整數倍，底中
      { const R = (x, y, w, h, c) => { g.fillStyle = c; g.fillRect(x * k, y * k, w * k, h * k); }; R(10, 24, 54, 56, '#E8C27A'); R(11, 25, 52, 54, '#6B4A1E'); R(12, 26, 50, 52, '#2C3466'); R(12, 26, 50, 2, '#3A447E'); }   // 頭像框（kit portrait 金邊；@1x art px）
      const a = petSrc(snap.fk, 0); if (a) { const s0 = a.src, sc = Math.max(1, Math.floor(Math.min(46 / s0.sw, 46 / s0.sh))); const w = s0.sw * sc, h = s0.sh * sc; g.drawImage(s0.img, s0.sx, s0.sy, s0.sw, s0.sh, Math.round((10 + (54 - w) / 2) * k), Math.round((24 + 52 - h) * k), w * k, h * k); }
      txt(snap.name || '團絨', 70, 34, { mw: 86 }); txt('家族 Lv' + (snap.lv || 1), 70, 52, { col: '#FFE29A', mw: 80 }); txt('形態：' + FORMZ(snap.form), 70, 70, { mw: 86 });
      const mm = (snap.mem || []).map(id => D6.MEM[id] && D6.MEM[id].zh).filter(Boolean); mm.forEach((t, i) => txt(t, 24, 101 + i * 18, { mw: 126 }));
      // QR：白位 (53,164) 58×58；模組 1 art px（k px，整數）；置中
      const M = qrMatrix(code); let qrN = 0;
      if (M) { qrN = M.length; const per = qrN <= 29 ? 2 : 1, side = qrN * per, ox = 53 + Math.floor((58 - side) / 2), oy = 164 + Math.floor((58 - side) / 2); g.fillStyle = '#FFFFFF'; g.fillRect(53 * k, 164 * k, 58 * k, 58 * k); g.fillStyle = '#000000';
        for (let y = 0; y < qrN; y++) for (let x = 0; x < qrN; x++) if (M[y][x]) g.fillRect((ox + x * per) * k, (oy + y * per) * k, per * k, per * k); }
      txt(D6.shortOf(code), 82.5, 236, { c: 1, mw: 150 });
      return { art, qrN, k, w: cv.width, h: cv.height, mem: mm.length };
    }

    // ── 朋友面板 ──
    const OV = { el: null, tab: 'main', pre: null, code: null, egg: null, last: null, inp: '' };
    const busy = () => !!OV.el || !!INFO.el || !!document.getElementById('l6cov') || !!document.getElementById('l6cdex') || !!document.getElementById('l6bov') || !!document.getElementById('l5bov') || !!document.getElementById('l5ov') || !!document.getElementById('l5cov') || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene');
    const host = () => document.getElementById('ui') || document.body;
    function btn(label, kind, ic, tid, fn, css) {
      const b = tx(mk('div', `${bi(kind || 'btn_sec')}` + TXT(24, CREAM) + (css || ''), null, tid)); b.className = 'b6 l6dx'; b.setAttribute('role', 'button');
      if (ic) { const i = mk('i'); i.className = 'ic'; setIc(i, ic); b.appendChild(i); } b.appendChild(mk('span', 'position:relative;pointer-events:none', label));
      b.addEventListener('click', (e) => { e.stopPropagation(); if (b.classList.contains('dis')) { UIS('error'); if (b._why) toast(b._why); return; } UIS('tap'); fn(e); }); return b;
    }
    function close(why) { if (!OV.el) return false; OV.el.remove(); OV.el = null; document.body.classList.remove('l6d-on'); note('close', { why }); return true; }
    function open(tab, why) {
      if (OV.el) OV.el.remove(); OV.tab = tab || 'main'; const el = OV.el = mk('div', '', null, 'l6d-ov'); el.id = 'l6dov';
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      const bd = mk('div', 'position:absolute;inset:0;background:rgba(18,12,30,.74)'); bd.addEventListener('click', () => { UIS('tap'); close('bd'); }); el.appendChild(bd);
      host().appendChild(el); document.body.classList.add('l6d-on'); render(); fontsReady().then(() => { if (OV.el === el) render(); }); note('open', { tab: OV.tab, why }); return el;   // 6d.2：字型載完再畫一次，免 ?v3=0 主面板落系統字
    }
    function frame(title, sub, tid) {
      const p = mk('div', `position:absolute;left:16px;top:112px;width:358px;max-height:700px;box-sizing:border-box;padding:36px 16px 16px;display:flex;flex-direction:column;gap:12px;${PAN()}`, null, tid || 'l6d-panel'); if (V62()) p.className = 'u62pan';
      p.appendChild(tx(mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:180px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), title, 'l6d-title')));
      if (sub) p.appendChild(tx(subEl(sub, 'position:relative;margin:0 !important;text-align:center;')));
      const x0 = mk('div', `position:absolute;right:-23px;top:-25px;z-index:5;width:52px;height:52px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center`, null, 'l6d-close'); x0.setAttribute('role', 'button');
      x0.appendChild(mk('div', `position:relative;flex:0 0 auto;width:30px;height:30px;pointer-events:none;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}` + TXT(24, CREAM), sp('close') ? '' : '✕'));
      x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); if (OV.tab === 'main') close('x'); else { OV.pre = null; go('main'); } }); p.appendChild(x0);
      OV.el.appendChild(p); return p;
    }
    const line = (p, t, c, tid, tag) => p.appendChild(tx(mk(tag || 'div', 'position:relative;margin:0;' + TXT(24, c || CREAM), t, tid)));
    function go(tab) { OV.tab = tab; render(); }
    function render() {
      const el = OV.el; if (!el) return; [...el.children].slice(1).forEach(c => c.remove()); const s = S(), t = now(), sm = D6.summary(s, t);
      if (OV.tab === 'main') {
        const p = frame('朋友', SUBT.main, 'l6d-panel');
        const st = tx(mk('div', `position:relative;padding:8px 12px;box-sizing:border-box;${INSET()}` + TXT(24, GOLD), '今日請咗 ' + sm.today + '／' + sm.perDay + ' 個朋友・手信 ' + sm.gifts + '／3', 'l6d-today')); p.appendChild(st);
        const g1 = mk('div', 'position:relative;display:grid;grid-template-columns:1fr 1fr;gap:12px'); p.appendChild(g1);
        g1.appendChild(btn('我嘅名片', 'btn_pri', 'share', 'l6d-tab-card', () => go('card')));
        g1.appendChild(btn('入朋友碼', 'btn_sec', 'paste', 'l6d-tab-enter', () => go('enter')));
        const eb = btn('交換蛋碼', 'btn_sec', 'egg_code', 'l6d-tab-egg', () => go('egg')); g1.appendChild(eb);
        g1.appendChild(btn('朋友簿', 'btn_sec', 'friend', 'l6d-tab-book', () => go('book')));
        if (s.stage === 'egg') { const cb = p.querySelector('[data-testid=l6d-tab-card]'); cb.classList.add('dis'); cb._why = '孵咗先有名片'; }
        if (sm.visits.length) { line(p, '而家嚟緊（' + sm.visits.length + '）', GOLD, 'l6d-now-h');
          for (const v of sm.visits) { const r = tx(mk('div', `position:relative;display:flex;align-items:center;gap:8px;padding:6px 10px;box-sizing:border-box;${INSET()}` + TXT(24, CREAM), null, 'l6d-now-' + v.id)); const i = mk('i', 'position:relative;flex:0 0 32px;width:32px;height:32px;background:center/contain no-repeat'); setIc(i, 'friend_badge'); r.appendChild(i);
            r.appendChild(mk('span', 'position:relative;flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap', v.name + '嘅影子')); r.appendChild(mk('span', 'position:relative;flex:0 0 auto;color:' + MINT, '仲有 ' + v.leftH + ' 粒鐘')); p.appendChild(r); } }
        else line(p, '未有朋友嚟緊。入個朋友碼請佢嚟玩！', LAV, 'l6d-now-none', V62() ? 'small' : 'div');
        if (sm.egg && !sm.egg.used) line(p, '收到' + sm.egg.name + '嘅蛋碼：下一隻細佬蛋帶「' + (D6.PATZ[sm.egg.pat] || sm.egg.pat) + '」花紋', MINT, 'l6d-egg-pend');
      } else if (OV.tab === 'card') cardView();
      else if (OV.tab === 'enter') enterView();
      else if (OV.tab === 'egg') eggView();
      else if (OV.tab === 'book') bookView();
    }
    function cardBlock(p, code, snap, kind, tidp) {
      const cv = mk('canvas', 'position:relative;display:block;margin:0 auto;width:330px;height:504px;image-rendering:pixelated;flex:0 0 auto', null, tidp + '-canvas'); p.appendChild(cv);
      const r = drawCard(cv, 6, snap, code, kind); cv.dataset.qr = r.qrN; cv.dataset.art = r.art ? '6d:share_card_bg' : ''; if (!r.art) cv.dataset.ph = '6d:share_card_bg';
      fontsReady().then(() => { if (cv.isConnected) drawCard(cv, 6, snap, code, kind); });
      const row = mk('div', 'position:relative;display:flex;gap:8px'); p.appendChild(row);
      const fname = (kind === 'egg' ? '微光小圃-蛋碼-' : '微光小圃-朋友名片-') + code.slice(-4) + '.png';
      row.appendChild(btn('複製', 'btn_sec', 'copy', tidp + '-copy', async () => { const ok = await copyText(code); LAST.copied = ok ? code : null; toast(ok ? '複製咗，貼俾朋友' : '複製唔到，請長撳'); note('copy', { ok, kind }); }, 'flex:1 1 0;min-width:0;padding:4px 6px;gap:4px'));
      row.appendChild(btn('存圖', 'btn_sec', 'photo', tidp + '-save', async () => { const c2 = mk('canvas'); await fontsReady(); drawCard(c2, 3, snap, code, kind); const r2 = await saveImage(c2, fname); toast(r2.ok ? '存咗分享圖' : '存唔到圖'); note('save', { ok: r2.ok, kind, w: c2.width, h: c2.height }); }, 'flex:1 1 0;min-width:0;padding:4px 6px;gap:4px'));
      row.appendChild(btn('分享', 'btn_pri', 'share', tidp + '-share', async () => { const c2 = mk('canvas'); await fontsReady(); drawCard(c2, 3, snap, code, kind); const r2 = await shareImage(c2, fname, code); note('share', { ok: r2.ok, kind }); if (!r2.ok) toast('分享唔到'); }, 'flex:1 1 0;min-width:0;padding:4px 6px;gap:4px'));
      return cv;
    }
    function cardView() {
      const s = S(); const p = frame('我嘅名片', null, 'l6d-card'); p.style.top = '112px'; p.style.gap = '8px';
      if (s.stage === 'egg') { line(p, '孵咗先有名片。', LAV, 'l6d-card-egg'); return; }
      const me = D6.myCode(s, now(), { fk: fkNow() }); OV.code = me.code; cardBlock(p, me.code, me.snap, 'visit', 'l6d-card');
    }
    function eggView() {
      const s = S(), e = D6.eggState(s, now()); const p = frame('交換蛋碼', e.ok && e.why !== 'new' ? null : SUBT.egg, 'l6d-eggp');
      if (!e.ok) { line(p, '家族 Lv' + D6.CFG.eggLv + ' 先可以出蛋碼（而家 Lv' + e.lv + '）', LAV, 'l6d-egg-lock'); line(p, '每 7 日可以出 1 個。', CREAM, 'l6d-egg-rule', V62() ? 'small' : 'div'); return; }
      if (e.why === 'new') { line(p, '每 7 日可以出 1 個蛋碼。', CREAM, 'l6d-egg-rule'); p.appendChild(btn('出蛋碼', 'btn_pri', 'egg_code', 'l6d-egg-make', () => { const r = D6.eggCode(S(), now(), { fk: fkNow() }); save(); note('eggMake', { why: r.why }); render(); })); return; }
      p.style.top = '112px'; p.style.gap = '8px'; const snap = D6.decode(e.code).snap; OV.egg = e.code; cardBlock(p, e.code, snap, 'egg', 'l6d-egg');
      line(p, '再過 ' + e.left + ' 日可以出新蛋碼', MINT, 'l6d-egg-left');
    }
    function bookView() {
      const s = S(), o = D6.st(s), fr = Object.keys(o.friends).map(k => o.friends[k]).sort((a, b) => b.last - a.last); const p = frame('朋友簿 ' + fr.length, SUBT.book, 'l6d-book');
      if (!fr.length) { line(p, '未有朋友嚟過。', LAV, 'l6d-book-none'); return; }
      const box = mk('div', 'position:relative;display:flex;flex-direction:column;gap:8px;max-height:520px', null, 'l6d-book-list'); box.className = 'scr'; p.appendChild(box);
      for (const f of fr) { const r = tx(mk('div', `position:relative;flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:6px 10px;box-sizing:border-box;${INSET()}` + TXT(24, CREAM), null, 'l6d-book-' + f.uid)); const i = mk('i', 'position:relative;flex:0 0 32px;width:32px;height:32px;background:center/contain no-repeat'); setIc(i, 'friend'); r.appendChild(i);
        const c = mk('div', 'position:relative;flex:1 1 auto;min-width:0;display:flex;flex-direction:column'); c.appendChild(mk('span', 'position:relative;overflow:hidden;text-overflow:ellipsis;white-space:nowrap', f.name + '・Lv' + f.lv));
        c.appendChild(mk('span', 'position:relative;white-space:nowrap;color:' + MINT, '嚟過 ' + f.n + ' 次' + (f.eggs ? '・蛋碼 ' + f.eggs : '') + '・' + NS.long6a.dayKey(f.last).slice(5).replace('-', '/'))); r.appendChild(c); box.appendChild(r); }
    }
    // 入碼：貼上／揀相 → 預覽（校驗 OK）→ 請佢嚟玩／收蛋碼
    function enterView() {
      const p = frame('入朋友碼', SUBT.enter, 'l6d-enter');
      const fld = mk('div', `position:relative;box-sizing:border-box;min-height:116px;${INSET()}`, null, 'l6d-field'); const ta = mk('textarea', TXT(24, CREAM) + 'height:112px;', null, 'l6d-input'); ta.rows = 3; ta.placeholder = '貼上朋友碼（GL6D…）'; ta.value = OV.inp || ''; ta.spellcheck = false; ta.autocomplete = 'off'; fld.appendChild(ta); p.appendChild(fld);
      ta.addEventListener('input', () => { OV.inp = ta.value; OV.pre = null; showPre(); }); ta.addEventListener('pointerdown', (e) => e.stopPropagation());
      const row = mk('div', 'position:relative;display:flex;gap:8px'); p.appendChild(row);
      row.appendChild(btn('貼上', 'btn_sec', 'paste', 'l6d-paste', async () => { const t = await pasteText(); if (t == null) { toast('讀唔到剪貼簿'); return; } OV.inp = t; ta.value = t; check(); }, 'flex:1 1 0;min-width:0;padding:4px 6px;gap:4px'));
      const file = mk('input', 'display:none', null, 'l6d-file'); file.type = 'file'; file.accept = 'image/*'; p.appendChild(file);
      file.addEventListener('change', async () => { const f = file.files && file.files[0]; file.value = ''; if (!f) return; const t = await decodeFile(f); note('photo', { ok: !!t }); if (!t) { toast('相入面搵唔到 QR'); return; } OV.inp = D6.extract(t) || t; ta.value = OV.inp; check(); });
      row.appendChild(btn('揀相', 'btn_sec', 'photo', 'l6d-photo', () => file.click(), 'flex:1 1 0;min-width:0'));
      row.appendChild(btn('睇吓', 'btn_pri', 'qr', 'l6d-check', () => check(), 'flex:1 1 0;min-width:0'));
      OV.preBox = mk('div', 'position:relative;display:flex;flex-direction:column;gap:8px', null, 'l6d-pre'); p.appendChild(OV.preBox); showPre();
    }
    const WHY = { bad: D6.LINES.bad, sum: D6.LINES.sum, ver: D6.LINES.ver, self: D6.LINES.self, dup: D6.LINES.dup, friendToday: D6.LINES.friendToday, max: D6.LINES.max, here: D6.LINES.here };
    function check(text) { const t = text != null ? text : OV.inp; const d = D6.decode(t); OV.pre = d; note('check', { ok: d.ok, why: d.why }); if (!d.ok) UIS('error'); else UIS('tap'); showPre(); return d; }
    function showPre() {
      const b = OV.preBox; if (!b || !b.isConnected) return; b.innerHTML = ''; const d = OV.pre; if (!d) return;
      if (!d.ok) { b.appendChild(tx(mk('div', 'position:relative;' + TXT(24, '#FFB4B4'), WHY[d.why] || D6.LINES.bad, 'l6d-pre-bad'))); return; }
      const sn = d.snap, r = tx(mk('div', `position:relative;display:flex;gap:12px;align-items:center;padding:8px 12px;box-sizing:border-box;${INSET()}`, null, 'l6d-pre-card'));
      const cv = mk('canvas', 'position:relative;flex:0 0 auto;image-rendering:pixelated', null, 'l6d-pre-shadow'); const sh = shadowCanvas(sn.fk, 0);
      if (sh) { paintShadow(cv, sh); cv.dataset.art = 'shadow:alpha'; } else { cv.width = 24; cv.height = 24; cv.style.width = '48px'; cv.style.height = '48px'; cv.dataset.ph = '6d:shadow'; }
      r.appendChild(cv); const c = mk('div', 'position:relative;flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:2px'); r.appendChild(c);
      c.appendChild(mk('div', 'position:relative;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;' + TXT(24, GOLD), sn.name, 'l6d-pre-name'));
      c.appendChild(mk('div', 'position:relative;white-space:nowrap;' + TXT(24, CREAM), '家族 Lv' + sn.lv + '・' + (D6.PATZ[sn.pat] || sn.pat) + '紋', 'l6d-pre-lv'));
      c.appendChild(mk('div', 'position:relative;white-space:nowrap;' + TXT(24, MINT), sn.kind === 'egg' ? '蛋碼・校驗 OK' : '朋友碼・校驗 OK', 'l6d-pre-ok'));
      b.appendChild(r);
      for (const id of sn.mem) b.appendChild(tx(mk('div', 'position:relative;padding-left:12px;' + TXT(24, CREAM), '・' + D6.MEM[id].zh, 'l6d-pre-mem-' + id)));
      b.appendChild(btn(sn.kind === 'egg' ? '收蛋碼' : '請佢嚟玩', 'btn_pri', sn.kind === 'egg' ? 'egg_code' : 'friend', 'l6d-go', () => commit()));
    }
    function commit() {
      const s = S(), r = D6.enter(s, OV.inp, now(), {}); OV.last = r; note('enter', { ok: r.ok, why: r.why, kind: r.kind });
      if (!r.ok) { UIS('error'); toast(D6.fill(D6.SHORT[r.why] || D6.SHORT.bad, { name: r.name || '' })); OV.pre = Object.assign({}, OV.pre, { ok: false, why: r.why }); showPre(); return r; }
      save(); UIS('reward'); toast(r.line, 3000); OV.inp = ''; OV.pre = null; close('enter'); if (r.kind === 'visit') { layTick(true); } return r;
    }

    // ── 花園影子 ──
    const LAY = { el: null, nodes: {}, bub: null, nextAct: 0, actId: null, actT: 0 };
    // 6 個位：前排（地面）避開團絨（x 156–230）同右邊 rail（x≥334）；後排高 80（團絨頭頂之上）；撳位 56×76 唔撞
    const SLOTS = [[36, 0], [290, 0], [100, 0], [70, 1], [195, 1], [280, 1]], GROUND = 584, ROWY = [0, -80];
    const SLOTX = SLOTS.map(a => a[0]);
    function layer() { if (LAY.el && LAY.el.isConnected) return LAY.el; const ui = document.getElementById('ui'); if (!ui) return null; const el = LAY.el = mk('div', '', null, 'l6d-layer'); el.id = 'l6dlay'; const hit = document.getElementById('hit'); if (hit && hit.parentNode === ui) hit.after(el); else ui.prepend(el); LAY.nodes = {}; return el; }
    function petX() { try { const R = G.renderer; if (R && R.petRect && R.petRect.w > 0) return (R.petRect.x + R.petRect.w / 2) * 2; } catch (e) { } return 195; }
    function layTick(force) {
      const s = S(); if (!s) return; const vs = D6.st(s).visits, el = layer(); if (!el) return; const t = pnow();
      for (const id of Object.keys(LAY.nodes)) if (!vs.some(v => v.id === id)) { LAY.nodes[id].el.remove(); delete LAY.nodes[id]; }
      for (const v of vs) {
        let N = LAY.nodes[v.id]; if (!N) { const d = mk('div', '', null, 'l6d-shadow-' + v.id); d.className = 'sh6 u63no'; const cv = mk('canvas', '', null, 'l6d-shadow-cv-' + v.id); cv.width = 1; cv.height = 1; d.appendChild(cv);
          const ht = mk('i', '', null, 'l6d-shadow-hit-' + v.id); ht.className = 'ht'; d.appendChild(ht); const b = mk('i', '', null, 'l6d-badge-' + v.id); b.className = 'bdg'; d.appendChild(b); el.appendChild(d); ht.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); info(v.id); });
          N = LAY.nodes[v.id] = { el: d, cv, b, x: SLOTX[v.slot] || 80, tx: SLOTX[v.slot] || 80, dir: 1, ph: (v.slot * 977) % 4000, k: null }; }
        // 行：平時喺自己位 ±24 晃；互動緊 → 行去團絨隔籬
        const home = SLOTX[v.slot] || 80, acting = LAY.actId === v.id && t - LAY.actT < 4200; N.tx = acting ? petX() + (home < 195 ? -64 : 64) : home + Math.sin((t + N.ph) / 3200) * 8;
        const dx = N.tx - N.x; if (Math.abs(dx) > 0.5) { N.dir = dx < 0 ? -1 : 1; N.x += Math.sign(dx) * Math.min(Math.abs(dx), acting ? 2.4 : 0.6); }
        const sh = shadowCanvas(v.fk, t + N.ph);
        if (sh) { if (N.k !== sh.key) { N.k = sh.key; paintShadow(N.cv, sh); delete N.el.dataset.ph; N.el.dataset.art = 'shadow:alpha'; N.el.dataset.frame = sh.frame; }
          N.cv.style.left = (-sh.px * 2) + 'px'; N.cv.style.top = (-sh.py * 2) + 'px'; N.cv.style.transform = N.dir < 0 ? 'scaleX(-1)' : ''; N.cv.style.transformOrigin = (sh.px * 2) + 'px 0'; N.b.style.top = (-sh.py * 2 - 36) + 'px'; }
        else if (!N.el.dataset.ph) { N.el.dataset.ph = '6d:shadow'; N.cv.width = 24; N.cv.height = 24; N.cv.style.cssText = 'left:-24px;top:-48px;width:48px;height:48px;background:#A98BF0'; N.b.style.top = '-84px'; }
        if (!N.b.dataset.art) setIc(N.b, 'friend_badge'), N.b.style.background = N.b.style.backgroundImage ? N.b.style.backgroundImage + ' center/contain no-repeat' : '';
        N.el.style.left = Math.round(N.x) + 'px'; N.el.style.top = (GROUND + ROWY[(SLOTS[v.slot] || [0, 0])[1]]) + 'px'; N.el.dataset.x = Math.round(N.x);
      }
      // 互動：每 40–70 秒揀一個影子走埋去（泡泡＋計數）
      if (vs.length && !s.sleeping && (force === 'act' || t >= LAY.nextAct)) {
        if (LAY.nextAct && force !== true) { const v = vs[Math.floor((t / 1000) % vs.length)]; const ln = D6.act(s, v.id, now()); if (ln) { LAY.actId = v.id; LAY.actT = t; bubble(v, D6.fill(ln, { pet: petName() })); note('act', { id: v.id }); save(); } }
        LAY.nextAct = t + 40000 + ((t * 7) % 30000);
      }
      if (LAY.bub && t - LAY.bubT > 3200) { LAY.bub.classList.remove('on'); if (t - LAY.bubT > 3600) { LAY.bub.remove(); LAY.bub = null; } }
      else if (LAY.bub && LAY.nodes[LAY.bubId]) LAY.bub.style.left = Math.max(110, Math.min(280, LAY.nodes[LAY.bubId].x)) + 'px';
    }
    const petName = () => { const s = S(); return s && s.stage !== 'egg' && FAM ? FAM.trName(s.form) : '團絨'; };
    function bubble(v, text) {
      const el = layer(); if (!el) return; if (LAY.bub) LAY.bub.remove(); const b = LAY.bub = mk('div', `left:${Math.max(110, Math.min(280, (LAY.nodes[v.id] || {}).x || 195))}px;top:${GROUND - 120}px;${bi('panel_inset')}` + TXT(24, CREAM), '♥ ' + text, 'l6d-bubble'); b.className = 'bub';
      el.appendChild(b); LAY.bubT = pnow(); LAY.bubId = v.id; requestAnimationFrame(() => b.classList.add('on'));
    }
    // 撳影子：朋友資料＋早啲送佢返屋企
    const INFO = { el: null, id: null };
    function closeInfo() { if (!INFO.el) return false; INFO.el.remove(); INFO.el = null; INFO.id = null; document.body.classList.remove('l6d-on'); return true; }
    function info(id) {
      closeInfo(); const s = S(), v = D6.st(s).visits.find(x => x.id === id); if (!v) return null; const el = INFO.el = mk('div', 'position:absolute;inset:0;z-index:62', null, 'l6d-info'); el.id = 'l6dov'; INFO.id = id;
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      const bd = mk('div', 'position:absolute;inset:0;background:rgba(18,12,30,.6)'); bd.addEventListener('click', () => { UIS('tap'); closeInfo(); }); el.appendChild(bd);
      const p = mk('div', `position:absolute;left:24px;top:200px;width:342px;box-sizing:border-box;padding:36px 16px 16px;display:flex;flex-direction:column;gap:8px;${PAN()}`, null, 'l6d-info-panel'); if (V62()) p.className = 'u62pan'; el.appendChild(p);
      p.appendChild(tx(mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:180px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '朋友嘅影子', 'l6d-info-title')));
      const L = (t, c, tid) => p.appendChild(tx(mk('div', 'position:relative;' + TXT(24, c || CREAM), t, tid)));
      L(v.name + '嚟探你！', GOLD, 'l6d-info-name'); L('仲有 ' + D6.leftH(v, now()) + ' 粒鐘・家族 Lv' + v.lv, MINT, 'l6d-info-left'); L('形態：' + FORMZ(v.form) + '・' + (D6.PATZ[v.pat] || v.pat) + '紋', CREAM, 'l6d-info-form');
      for (const m of v.mem) L('・' + D6.MEM[m].zh, CREAM, 'l6d-info-mem-' + m);
      const row = mk('div', 'position:relative;display:flex;gap:12px;margin-top:8px'); p.appendChild(row);
      row.appendChild(btn('送佢返屋企', 'btn_sec', 'gift', 'l6d-info-bye', () => { const r = D6.leave(S(), id, now(), true); save(); closeInfo(); if (r) { afterLeave(r); } layTick(true); }, 'flex:1 1 0;min-width:0;padding:4px 6px;gap:4px'));
      row.appendChild(btn('好', 'btn_pri', null, 'l6d-info-ok', () => closeInfo(), 'flex:0 0 96px'));
      host().appendChild(el); document.body.classList.add('l6d-on'); note('info', { id }); return el;
    }
    function afterLeave(r) { note('leave', { id: r.id, gift: r.gift, early: r.early }); toast(r.line, 3000); if (r.gift) UIS('reward'); }

    // ── 花園 rail「朋友」──
    const RB = { el: null };
    function railTick() {
      const s = S(); if (!s) return; const show = !document.body.classList.contains('s2-scene') && !document.body.classList.contains('s2-house'); let el = RB.el;
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), hst = rail || document.getElementById('top-r'); if (!hst) return;
        el = RB.el = mk('div', '', null, 'l6d-rail'); el.id = 'l6dbtn'; el.className = 'ibtn panel'; el.title = '朋友';
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l">朋友</i><i class="rd"></i>';
        el.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); open('main', 'rail'); }); hst.appendChild(el); }
      { const rail = document.getElementById('hdRail'); if (rail && el.parentNode !== rail) rail.appendChild(el); }   // 早過 hdRail 起咗 → 搬入去
      el.style.display = show ? '' : 'none'; if (!show) return; el.setAttribute('aria-label', '朋友');
      const ic = el.querySelector('i.i'); if (ic.dataset.v3 !== String(isV3()) || !ic.dataset.art) { setIc(ic, 'friend'); ic.dataset.v3 = String(isV3()); }
      const rd = el.querySelector('i.rd'); if (rd) rd.style.display = 'none';
      const vis = (id) => { const e = document.getElementById(id); return !!(e && e.style.display !== 'none' && e.offsetParent !== null); };
      // 排喺 rail 最底嗰粒（工作／散步／入夢）下面，70px 一格；落唔到（>620）→ 左邊一行
      const col = ['l6cbtn', 'u62workbtn', 'l6bbtn'].map(id => document.getElementById(id)).filter(e => e && vis(e.id) && e.style.top);
      const u = U(), rl = u && u.rail;
      if (col.length) {   // 主列（最右）同左邊列（6c 落唔到會去 x−76）分開計
        const L = (e) => parseFloat(e.style.left) || 0, Tp = (e) => parseFloat(e.style.top) || 0, mx = Math.max(...col.map(L)), main = col.filter(e => L(e) >= mx - 20), side = col.filter(e => L(e) < mx - 20);
        const lo = main.reduce((a, b) => (Tp(b) > Tp(a) ? b : a)), y = Tp(lo) + 70;
        if (y <= 620 && !side.length) { el.style.left = lo.style.left; el.style.top = y + 'px'; }
        else if (side.length) { const sh = side.reduce((a, b) => (Tp(b) < Tp(a) ? b : a)); el.style.left = sh.style.left; el.style.top = (Tp(sh) - 70) + 'px'; }   // 左邊列再上一格
        else { el.style.left = (mx - 76) + 'px'; el.style.top = (Tp(lo) - 70) + 'px'; } }   // 留最低嗰格俾 6c「入夢」
      else if (rl && rl.kid && rl.dex) { const st = 1 + (vis('l5egg') ? 1 : 0) + (vis('l5cbtn') ? 1 : 0) + (vis('l6bbtn') ? 1 : 0), dy = rl.kid.y - rl.dex.y; let x = rl.kid.x, y = rl.kid.y + st * dy; if (y > 620) { x = rl.kid.x - 76; y = rl.kid.y + (st - 1) * dy; } el.style.left = x + 'px'; el.style.top = y + 'px'; }
      else { el.style.left = '360px'; el.style.top = '520px'; }
    }

    // ── 每 100ms：影子；每秒：rail、到時走、蛋碼套 5c ──
    // 心聲泡泡（#s12voice）疊到「朋友」掣 → 掣暫時讓位（同心聲讓小提示一樣；泡泡走咗即刻返）
    function yieldTick() {
      const el = RB.el; if (!el) return; const v = document.getElementById('s12voice'); let y = false;
      if (v && !v._l6dmo && typeof MutationObserver !== 'undefined') { try { v._l6dmo = new MutationObserver(() => { try { yieldTick(); } catch (e) { } }); v._l6dmo.observe(v, { attributes: true, attributeFilter: ['style', 'class'] }); } catch (e) { } }   // 6d.1 P2b：心聲一出／一郁即刻判（唔等 100ms 輪詢）
      // 6d.1：淡入緊（inline opacity 已經 1、computed 仲係 0）都當出咗
      if (v && el.style.display !== 'none') { const cs = getComputedStyle(v), op = Math.max(+cs.opacity || 0, v.style.opacity === '' ? 0 : +v.style.opacity || 0); if (cs.display !== 'none' && cs.visibility !== 'hidden' && op >= 0.15) { const a = el.getBoundingClientRect(), b = v.getBoundingClientRect(); y = b.width > 1 && a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom; } }
      if (el.classList.contains('l6d-yield') !== y) { el.classList.toggle('l6d-yield', y); note('yield', { on: y }); }
    }
    const T = { last: 0 };
    function tick() {
      const t = pnow(), s = S(); if (!s) return;
      try { layTick(); } catch (e) { note('layErr', { e: String(e && e.message || e) }); }
      try { yieldTick(); } catch (e) { }
      if (A.dirty) { A.dirty = 0; A.mask = null; SHC.clear(); for (const id of Object.keys(LAY.nodes)) { LAY.nodes[id].k = null; delete LAY.nodes[id].b.dataset.art; } if (OV.el && OV.tab !== 'enter') render(); }
      if (t - T.last >= 1000) { T.last = t; try { railTick(); } catch (e) { } try { yieldTick(); } catch (e) { }   // 6d.1 P2b：rail 排完位即刻再判讓位（唔會疊住心聲一拍）
        const ev = D6.process(s, now()); for (const r of ev) afterLeave(r); if (ev.length) { try { layTick(); } catch (e) { } }   /* 6d.1 P2a：影子到時走 → 即刻清花園節點 */ const eg = D6.applyEgg(s, now()); if (eg) note('egg', eg); if (ev.length || eg) save(); }
    }
    { const loop = () => { try { tick(); } catch (e) { } setTimeout(loop, 100); }; setTimeout(loop, 500); }

    // ── 🛠 開發者模式「6d」 ──
    let fakeN = 0;
    function fakeCode(kind, o) {   // 假朋友（隨機 uid、用現有形態）
      o = o || {}; const forms = ['moon', 'soft', 'tide', 'ember', 'shroom', 'crystal', 'radiant', 'lumi'], f = o.form || forms[(fakeN++) % forms.length];
      const fk = (DATA && DATA.FORMS && DATA.FORMS['evo_still_' + f]) ? 'evo_still_' + f : (fkNow() || f);
      return D6.encode({ kind: kind || 'visit', uid: o.uid || ((Math.random() * 4294967295) >>> 0) || 7, day: 2500, fk, form: f, pat: o.pat || D6.PATS[fakeN % 8], lv: o.lv || 4, gen: 1, mem: [11, 9, 2] });
    }
    const runEnter = (code) => { const r = D6.enter(S(), code, now(), {}); save(); if (r.ok) { toast(r.line); layTick(true); } return { ok: r.ok, msg: r.ok ? r.line : '入唔到：' + D6.fill(WHY[r.why] || r.why, { name: r.name || '' }) }; };
    const DEV = { id: 'l6d', title: '6d（朋友探訪＋交換蛋）', order: 48,
      status: () => { const m = D6.summary(S(), now()); return '今日朋友 ' + m.today + '／3・手信 ' + m.gifts + '／3・影子 ' + m.visits.length + '・朋友簿 ' + m.friends + (m.egg && !m.egg.used ? '・蛋碼待用' : ''); },
      items: [
        ['open', '開朋友面板', () => { open('main', 'dev'); return { ok: true, msg: '開咗' }; }],
        ['card', '我嘅名片', () => { open('card', 'dev'); return { ok: true, msg: '開咗' }; }],
        ['visit', '假朋友嚟探（影子）', () => runEnter(fakeCode('visit'))],
        ['three', '3 個假朋友嚟', () => { let n = 0; for (let i = 0; i < 3; i++) if (runEnter(fakeCode('visit')).ok) n++; return { ok: n > 0, msg: '嚟咗 ' + n + ' 個' }; }],
        ['act', '影子即刻互動', () => { layTick('act'); return { ok: true, msg: '互動' }; }],
        ['expire', '影子全部到時走', () => { const o = D6.st(S()); o.visits.forEach(v => { v.until = now() - 1; }); const ev = D6.process(S(), now()); ev.forEach(afterLeave); save(); layTick(true); return { ok: true, msg: '走咗 ' + ev.length + ' 個' }; }],
        ['newday', '當新一日（今日次數清）', () => { const o = D6.st(S()); o.day = { d: '', uids: [], gifts: 0 }; o.seen = {}; save(); return { ok: true, msg: '清咗' }; }],
        ['lv4', '家族升到 Lv4', () => { const F = FAM.st(S()); if (F.lv < 4) { F.xp = FAM.THRESH[3]; F.lv = 4; } save(); return { ok: true, msg: 'Lv' + FAM.st(S()).lv }; }],
        ['egg', '出蛋碼（唔理 7 日）', () => { D6.st(S()).eggOut = null; const r = D6.eggCode(S(), now(), { fk: fkNow() }); save(); return { ok: r.ok, msg: r.ok ? '出咗 ' + r.short : '出唔到（Lv' + (r.lv || '?') + '）' }; }],
        ['eggin', '收假朋友蛋碼', () => runEnter(fakeCode('egg', { pat: 'star' }))],
        ['tamper', '改壞碼試吓', () => { const c = fakeCode('visit'), i = 10, bad = c.slice(0, i) + (c[i] === 'A' ? 'B' : 'A') + c.slice(i + 1); const d = D6.decode(bad); return { ok: !d.ok, msg: d.ok ? '改咗都入到（錯）' : '無效（' + d.why + '）' }; }],
        ['self', '入自己個碼', () => runEnter(D6.myCode(S(), now(), { fk: fkNow() }).code)],
        ['reset', '重設 6d', () => { closeInfo(); close('dev'); D6.reset(S()); save(); layTick(true); return { ok: true, msg: '6d 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l6d = { open, close, info, closeInfo };
    window.__qa = window.__qa || {};
    window.__qa.l6d = {
      st: () => Object.assign(D6.summary(S(), now()), { ov: !!OV.el, tab: OV.tab, info: !!INFO.el, rail: !!(RB.el && RB.el.style.display !== 'none'), art: !!A.j, artErr: A.err.slice(0, 5), mask: !!A.mask, alpha: SHADOW_A, shadows: Object.keys(LAY.nodes).length, v3: isV3(), native: !!NAT() }),
      raw: () => JSON.parse(JSON.stringify(D6.st(S()))), log: () => log.slice(), toasts: () => toasts.slice(), dev: () => DEV, last: () => Object.assign({}, LAST, { enter: OV.last }),
      open, close, info, closeInfo, go, check, commit, railTick, layTick, fakeCode, setInput: (t) => { OV.inp = t; const ta = document.querySelector('[data-testid=l6d-input]'); if (ta) ta.value = t; },
      artLoad: () => A6d.then(() => fontsReady()).then(() => !!A.j), drawCard: (k, kind) => { const c = document.createElement('canvas'); const s = S(), me = kind === 'egg' ? null : D6.myCode(s, now(), { fk: fkNow() }); const r = drawCard(c, k || 3, me.snap, me.code, 'visit'); return Object.assign(r, { url: c.toDataURL('image/png'), code: me.code }); },
      decodeFile, qrMatrix, shadowCanvas, paintShadow, SHADOW_A, maskBits, nodes: () => Object.keys(LAY.nodes).map(id => ({ id, x: LAY.nodes[id].x, art: LAY.nodes[id].el.dataset.art || null, ph: LAY.nodes[id].el.dataset.ph || null, badge: LAY.nodes[id].b.dataset.art || null })),
    };
    note('install', {});
    return true;
  }
  return { install };
});
