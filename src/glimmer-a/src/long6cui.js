/* 《微光小圃》 long6cui.js — 第 6 批 6c「夢境探險」介面（遊策 breakthrough-6a6d-spec §6c）。原創代碼。
   邏輯全部喺 long6c.js（s.dream6）；呢度只做：
   ・花園 rail「入夢」掣：團絨瞓緊＋19:00–03:00（6d：19:00 後上線都計）＋今晚未入過先出（有紅點）；錯過咗嘅一晚（存 1 個）白天瞓緊都出「入夢」補做；其他時間有夢碎片之後變「夢簿」（睇夢圖鑑）。
   ・夢境疊層（全螢幕直向）：入夢過場 → 3×5 小地圖（當晚 6a 記錄砌）→ 撳格陪團絨行（逐格行，霧散開）→ 拾夢碎片（頭 2 片即有，之後每 25 秒浮 1 片）
     → 150 秒到／當晚 1–2 片拾晒／撳「醒返」→ 出夢過場 → 今晚小結（新夢圖鑑、送家具）。硬上限 180 秒。
   ・唔加月眠／路線分、唔出碎、唔郁需求、唔郁系統 6 親密度；團絨夢完照瞓。
   ・美術（art/breakthrough/6c：af5b4821 dream6c.json；V3-A ba0d4345 v3/dream6c_v3.json）：格 56 art＝112 CSS（x0 22、間 4）、tileset 4 款、
     V3 開：dream_bg_v3（預合成）、tile_v3＋glow（lighter 呼吸）＋湖 caustic、fog_v3 流霧 8 幀＋fog_reveal 揭開、tile_reveal_glow、過場 v3 10 幀、卡 v3；
     V3 關／v1：dream_bg、tile、fog、transition_in 橫條、卡 1x。團絨 dream_walk 6 幀 6fps（1 art px＝2 CSS；向左 flipX）＋睡帽另一層（json 逐幀 xy）；
     夢入面寵物光＝0（G.v3.dream → petGlow dreaming）。入夢過場 0→9 → 地圖；出夢 0→9 收埋 → 小結 9→0 打開。
   ・美術載唔到／?l6cart=0 → placeholder（洋紅虛線＋data-ph）：6c:tile_*、6c:dream_walk、6c:nightcap、6c:card_<id>、6c:transition、6c:frag。
   ・🛠 開發者模式「6c」；?l6c=0 全停。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6cui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const DR = NS.long6c, UI = NS.ui, FAM = NS.long5a; if (!DR || !UI) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l6c') === '0') return false;
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), hour = () => (G.hour ? G.hour() : DR.hourOf(now())), pnow = () => performance.now();
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2200); };
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const F8 = () => (U() ? '"GlimmerFP8",' : '') + FALL, F12 = () => (U() ? '"GlimmerFP12",' : '') + FALL;
    const CREAM = '#FFF5DC', GOLD = '#FFE08A', MINT = '#B8F0C8', LAV = '#E6D8FF';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || FB[n] || ''; };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const TXT = (size, color, extra) => `font:${U() ? (size <= 24 ? 24 : 36) : Math.max(size, 20)}px/1.25 ${U() ? F12() : F8()};color:${color || CREAM};${OL}-webkit-font-smoothing:none;` + (extra || '');
    const LB5 = 'art/series2_long/5b/ui/';
    // 6b.2 風格（ui62 開住）：金邊半透明面板（.u62pan）、標題 FP12 24、內文 18／輔助 16（hd2dui2 read62 嘅 Z62 區會轉）、間距 4/8/12/16、每個面板一句用途
    const V62 = () => { const u = document.getElementById('ui'); return !!(u && u.classList.contains('u62') && u.classList.contains('v2')); };
    const SUBT = { dream: '陪團絨喺夢入面行，拾夢碎片砌夢圖鑑。', sum: '今晚個夢拾到嘅嘢，聽晚可以再嚟。', dex: '夢碎片砌成嘅卡，每個主題 5 張。' };
    const PAN = () => (V62() ? '' : bi('panel_navy'));
    const INSET = () => (V62() ? 'background:rgba(20,16,44,.72);border:1px solid rgba(232,194,122,.45);border-radius:10px;' : bi('panel_inset'));
    const subEl = (t, css) => { const d = mk('div', css || '', t, 'u62-sub'); d.className = 'u62sub'; return d; };

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l6ccss';
    css.textContent = `#l6cov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:60;user-select:none;-webkit-user-select:none;touch-action:manipulation;overflow:hidden;background:linear-gradient(#141033,#2B2160 55%,#3B2C6E)}
body.l6c-on #toast{z-index:73 !important}
#l6cov [data-ph],#l6cdex [data-ph]{outline:2px dashed #FF2BD6;outline-offset:-2px}
#l6cdex .card6[data-ph]{outline-offset:1px}
#l6cov .tile{position:absolute;width:112px;height:112px;box-sizing:border-box;cursor:pointer}
#l6cov .tile canvas{position:absolute;left:0;top:0;width:112px;height:112px;image-rendering:pixelated;pointer-events:none}
#l6cov .tile canvas.gl,#l6cov .tile canvas.cau{mix-blend-mode:plus-lighter;display:none}
#l6cov .tile.v3 canvas.gl,#l6cov .tile.v3[data-th="lake"] canvas.cau{display:block}
#l6cov .tile canvas.gl{animation:l6cbr var(--bp,2.86s) ease-in-out infinite}
#l6cov .tile .rg{position:absolute;left:-16px;top:-16px;width:144px;height:144px;pointer-events:none;opacity:0;transition:opacity 1.2s;mix-blend-mode:plus-lighter;display:none;z-index:1}
#l6cov .tile .fog{position:absolute;inset:0;border-radius:inherit;background:rgba(10,8,26,.82);transition:opacity .4s;pointer-events:none;z-index:2}
#l6cov .tile canvas.fog.art{background:none;transition:none}
#l6cov .tile[data-rev="1"] .fog:not(.art){opacity:0}
#ui.hd.v2.u62 #l6cov .tile.art{border-radius:0;overflow:visible;box-shadow:none}
#l6cov .frag{position:absolute;width:48px;height:48px;pointer-events:none;animation:l6ctw 1.2s steps(3) infinite}
#l6cov .pet{position:absolute;width:0;height:0;pointer-events:none;transition:left .28s linear,top .28s linear;z-index:3}
#l6cov .pet canvas.pc,#l6cov .pet .cap{position:absolute;image-rendering:pixelated}
#l6cov .pet.ph canvas.pc{left:-40px;top:-80px;width:80px;height:80px;animation:l6cbob 1s steps(2) infinite}
#l6cov .pet.ph .cap{left:-16px;top:-84px;width:36px;height:28px;animation:l6cbob 1s steps(2) infinite}
#l6cov .pet .sh{position:absolute;height:8px;margin-top:-4px;border-radius:50%;background:rgba(8,6,24,.4)}
#l6cov .tr{position:absolute;left:0;top:0;width:390px;height:844px;z-index:9;pointer-events:none;opacity:0;transition:opacity 1.2s;background:radial-gradient(circle at 50% 45%,#FFF5DC 0,#B9A2FF 18%,#3B2C6E 52%,#0C0920 100%)}
#l6cov canvas.tr.art{background:none;transition:opacity .35s;image-rendering:auto}
#l6cov.pre > :not(.tr){visibility:hidden}
#l6cov.pre{background:transparent !important}
#l6cov .bgi{position:absolute;left:0;top:0;width:390px;height:844px;pointer-events:none;image-rendering:pixelated}
#l6cov .bgi.v3{image-rendering:auto}
#l6cov .btn{position:relative;box-sizing:border-box;min-height:56px;display:flex;align-items:center;justify-content:center;padding:4px 16px;cursor:pointer;text-align:center}
#ui.hd.v2.u62 #l6cov .tile{border-radius:8px;overflow:hidden;box-shadow:0 0 0 1px rgba(232,194,122,.35)}
#ui.hd.v2.u62 #l6cov .u62sub,#ui.hd.v2.u62 #l6cdex .u62sub{margin:0 !important}
#ui.hd.v2.u62 #l6cov small,#ui.hd.v2.u62 #l6cdex small{display:block;color:#D9CFBC}
body.l6c-dr.u62ov #ui.hd.v2.u62 #toast{top:150px !important;left:195px !important;max-width:358px !important}
body.l6c-dr.u62ov #ui.hd.v2.u62 #toast.sm2{max-width:358px !important}
body.l6c-dr.u62ov #ui.hd.v2.u62 #s12gain{opacity:0 !important}
body.l6c-dr #ui.hd.v2.u62 #u62tip{right:16px !important;bottom:120px !important}
#l6cdex .card6{position:relative;flex:0 0 56px;width:56px;height:72px;box-sizing:border-box;cursor:pointer}
#l6cdex .card6 canvas{position:absolute;left:0;top:0;width:56px;height:72px;image-rendering:pixelated;pointer-events:none}
#l6cbtn{cursor:pointer}
#l6cbtn > i.i{position:absolute;left:50%;top:50%;width:36px;height:36px;margin:-18px 0 0 -18px;pointer-events:none}
@keyframes l6cbr{0%,100%{opacity:var(--b0,.82)}50%{opacity:1}}
@keyframes l6cbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes l6ctw{0%{transform:scale(1)}50%{transform:scale(1.15)}100%{transform:scale(1)}}`;
    document.head.appendChild(css);

    // ── placeholder 繪圖（程序畫；有美術就換） ──
    const TCOL = { forest: ['#2F5A36', '#3E7444', '#C8463C', '#F3E2C0'], lake: ['#24507A', '#3A78A8', '#9FD4F2', '#E9F6FF'], toy: ['#7A3E6E', '#A85A92', '#F2C14E', '#7FD1C7'], star: ['#1B1846', '#2C2868', '#FFE08A', '#B9A2FF'] };
    function drawTile(cv, th, i) {
      const g = cv.getContext('2d'), C = TCOL[th]; g.imageSmoothingEnabled = false; const W = cv.width;
      g.fillStyle = C[0]; g.fillRect(0, 0, W, W); g.fillStyle = C[1]; for (let k = 0; k < 9; k++) { const x = (k * 23 + i * 7) % 50, y = (k * 17 + i * 11) % 50; g.fillRect(x, y, 4, 2); }
      if (th === 'forest') { for (const [x, y] of [[12, 34], [38, 18]]) { g.fillStyle = C[3]; g.fillRect(x + 3, y + 6, 4, 8); g.fillStyle = C[2]; g.fillRect(x, y, 10, 6); g.fillStyle = C[3]; g.fillRect(x + 2, y + 1, 2, 2); } }
      else if (th === 'lake') { g.fillStyle = C[2]; for (const [x, y] of [[8, 14], [28, 30], [14, 42]]) { g.fillRect(x, y, 16, 2); g.fillRect(x + 4, y - 2, 8, 2); } g.fillStyle = C[3]; g.fillRect(40, 10, 4, 4); }
      else if (th === 'toy') { g.fillStyle = C[2]; g.fillRect(8, 30, 12, 12); g.fillStyle = C[3]; g.fillRect(20, 34, 10, 8); g.fillStyle = C[1]; g.fillRect(34, 14, 12, 12); g.fillStyle = C[2]; g.fillRect(38, 10, 4, 4); }
      else { g.fillStyle = C[2]; for (const [x, y] of [[10, 10], [40, 16], [24, 34], [46, 44], [8, 46]]) { g.fillRect(x, y, 2, 2); g.fillRect(x - 2, y, 6, 2); g.fillRect(x, y - 2, 2, 6); } g.fillStyle = C[3]; g.fillRect(30, 8, 6, 6); g.fillStyle = C[0]; g.fillRect(32, 8, 4, 4); }
    }
    function drawFrag(cv, th) {
      const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, 24, 24); const C = TCOL[th];
      g.fillStyle = '#FFF5DC'; g.fillRect(10, 2, 4, 20); g.fillRect(2, 10, 20, 4); g.fillStyle = C[2]; g.fillRect(8, 8, 8, 8); g.fillStyle = '#FFFFFF'; g.fillRect(10, 10, 2, 2);
    }
    function drawCap(cv) { const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, 18, 14);
      g.fillStyle = '#6E7FD8'; g.fillRect(2, 8, 14, 4); g.fillRect(5, 4, 9, 4); g.fillRect(9, 1, 5, 3); g.fillStyle = '#FFF5DC'; g.fillRect(1, 11, 16, 3); g.fillRect(14, 0, 4, 4); }
    function petDraw(c) {
      const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, c.width, c.height); const SA = G.s2Art, s = S(); let src = null;
      try { if (SA && SA.atlasSrc && G.renderer) { const a = SA.atlasSrc(G.renderer.fkOf(s), 'idle', 0, true); if (a && a.src && a.src.img && a.src.img.width) src = a.src; } } catch (e) { }
      if (!src) { g.fillStyle = '#FFF5DC'; g.beginPath(); g.arc(c.width / 2, c.height / 2 + 4, c.width / 3, 0, 7); g.fill(); g.fillStyle = '#24172C'; g.fillRect(c.width / 2 - 6, c.height / 2 + 2, 3, 2); g.fillRect(c.width / 2 + 3, c.height / 2 + 2, 3, 2); return false; }
      const k = Math.min(c.width / src.sw, c.height / src.sh); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, (c.width - src.sw * k) / 2, c.height - src.sh * k, src.sw * k, src.sh * k); return true;
    }
    function drawCard(cv, c, have) {
      const g = cv.getContext('2d'), C = TCOL[c.th]; g.imageSmoothingEnabled = false; g.clearRect(0, 0, 28, 36);
      g.fillStyle = have ? C[1] : '#2A2450'; g.fillRect(0, 0, 28, 36); g.fillStyle = have ? '#FFF5DC' : '#4A4370'; g.fillRect(2, 2, 24, 32); g.fillStyle = have ? C[0] : '#2A2450'; g.fillRect(4, 4, 20, 20);
      if (have) { const n = +c.id.slice(1); g.fillStyle = C[2]; g.fillRect(8 + n, 8 + (n % 3) * 2, 6, 6); g.fillStyle = C[3]; g.fillRect(6, 26, 16, 2); g.fillRect(6, 30, 10, 2); }
      else { g.fillStyle = '#6A6296'; g.fillRect(12, 9, 4, 2); g.fillRect(15, 11, 2, 4); g.fillRect(13, 15, 2, 3); g.fillRect(13, 20, 2, 2); }
    }

    // ── 6c 美術（dream6c.json＋V3-A v3/dream6c_v3.json）：載唔到／?l6cart=0 → 上面 placeholder ──
    const B6C = 'art/breakthrough/6c/', NOART = qs.get('l6cart') === '0';
    const A = { j: null, v: null, img: {}, want: {}, err: [], dirty: 0 };
    // QA P2：圖 decode 埋先當載好（第一次入夢唔會有 decode long task）
    const aimg = (f) => { if (NOART) return null; if (A.img[f]) return A.img[f]; if (!A.want[f]) { A.want[f] = 1; const i = new Image(); i.onload = () => { const ok = () => { if (i.naturalWidth) { A.img[f] = i; A.dirty = 1; } }; if (i.decode) i.decode().then(ok, ok); else ok(); }; i.onerror = () => A.err.push(f); i.src = B6C + f; } return null; };
    const jget = (f) => fetch(B6C + f).then(r => (r.ok ? r.json() : null)).catch(() => { A.err.push(f); return null; });
    const A6c = NOART ? Promise.resolve() : Promise.all([jget('dream6c.json'), jget('v3/dream6c_v3.json')]).then(([j, v]) => { A.j = j && j.keys && j.pets ? j : null; A.v = v && v.tiles ? v : null; A.dirty = 1; });
    const isV3 = () => { const u = document.getElementById('ui'); return !!(A.v && u && u.classList.contains('v3') && G.v3 && G.v3.on && G.v3.on()); };
    const fkNow = () => { const s = S(); if (!s || s.stage === 'egg') return null; try { return G.renderer && G.renderer.fkOf ? G.renderer.fkOf(s) : null; } catch (e) { return null; } };
    const ART = {   // 每樣嘢喺而家個模式用邊個檔：[file, 每幀 src 闊, 幀數]
      bg: () => (isV3() ? 'v3/dream_bg/dream_bg_v3@3x.png' : 'fx/dream_bg.png'),
      tile: (th) => (isV3() ? ['v3/tiles/tile_' + th + '_v3@3x.png', 168] : ['tiles/tile_' + th + '.png', 56]),
      glow: (th) => 'v3/tiles/tile_' + th + '_glow@3x.png', cau: 'v3/tiles/tile_lake_caustic@3x.png', rg: 'v3/tiles/tile_reveal_glow@3x.png',
      fog: () => (isV3() ? ['v3/tiles/fog_v3@3x.png', 168, 8] : ['tiles/fog.png', 56, 1]), fogRev: 'v3/tiles/fog_reveal@3x.png',
      frag: (th) => 'icons/frag_' + th + '@3x.png',
      card: (id, have) => (isV3() ? 'v3/cards/card_' + (have ? id : 'back') + '_v3@3x.png' : 'cards/card_' + (have ? id : 'back') + '.png'),
      tr: (k) => (isV3() ? 'v3/transition/transition_in_v3_' + String(k).padStart(2, '0') + '@3x.png' : 'fx/transition_in.png'),
      icon: (n) => 'icons/' + n + '.png',
    };
    const tvar = (i) => { const n = R.plan ? String(R.plan.night || '') : ''; let h = 0; for (const ch of n) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return (i + h) % 4; };
    const flick = (th) => { const t = A.v && A.v.tiles['6c:tile_' + th + '_v3']; return (t && t.flicker) || { hz: 0.35, amp: 0.15 }; };
    // 畫格（tileset／glow／caustic）；有圖返 true
    function tileArt(t, i) {
      const th = t.dataset.th, [f, w] = ART.tile(th), im = aimg(f), v3 = isV3(); if (!im || !A.j) return false;
      const cv = t.querySelector('canvas.base'); if (cv.width !== w) { cv.width = w; cv.height = w; }
      const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, w, w); g.drawImage(im, tvar(i) * w, 0, w, w, 0, 0, w, w);
      t.classList.add('art'); t.classList.toggle('v3', v3); delete t.dataset.ph; t.dataset.art = '6c:tile_' + th + (v3 ? '_v3' : '');
      if (v3) { const gi = aimg(ART.glow(th)), gl = t.querySelector('canvas.gl'); if (gi) { gl.width = 168; gl.height = 168; const q = gl.getContext('2d'); q.clearRect(0, 0, 168, 168); q.drawImage(gi, tvar(i) * 168, 0, 168, 168, 0, 0, 168, 168); const fl = flick(th); t.style.setProperty('--bp', (1 / (fl.hz || 0.35)).toFixed(2) + 's'); t.style.setProperty('--b0', (1 - 2 * (fl.amp || 0.15)).toFixed(2)); gl.dataset.art = '6c:tile_glow'; }
        const ri = aimg(ART.rg), rg = t.querySelector('img.rg'); if (ri && !rg.src) { rg.src = B6C + ART.rg; rg.style.display = 'block'; } }
      return true;
    }
    // QA P2：霧幀切好放 offscreen canvas（每張圖切一次）；anim 淨係幀數變／揭格先重畫
    const FOGC = {};
    function fogFrames(f, im, w, n) { const key = f + ':' + w; let a = FOGC[key]; if (a) return a; a = FOGC[key] = [];
      for (let k = 0; k < n; k++) { const c = document.createElement('canvas'); c.width = w; c.height = w; const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(im, k * w, 0, w, w, 0, 0, w, w); a.push(c); } return a; }
    function fogDraw(t, i, ms) {   // 未揭：流霧（V3 8 幀 4fps）；啱啱揭：fog_reveal 8 幀 16fps；之後清走
      const fc = t._fc || (t._fc = t.querySelector('.fog')), [f, w, n] = ART.fog(), im = aimg(f); if (!im || !A.j) return;
      if (!fc.classList.contains('art')) { fc.classList.add('art'); fc.width = w; fc.height = w; fc.dataset.art = '6c:fog' + (isV3() ? '_v3' : ''); }
      if (fc.width !== w) { fc.width = w; fc.height = w; }
      const g = fc.getContext('2d'); g.imageSmoothingEnabled = false; let src = im, k = Math.floor(ms / 250) % n, key;
      if (R.rev[i]) { const dt = ms - (R.revT[i] || -1e9), ri = isV3() ? aimg(ART.fogRev) : null;
        if (ri && dt < 500) { src = ri; k = Math.min(7, Math.floor(dt / 62.5)); key = 'r' + k; } else { if (fc._k !== 'off') { g.clearRect(0, 0, w, w); fc._k = 'off'; fc.style.display = 'none'; const rg = t.querySelector('img.rg'); if (rg && isV3()) { rg.style.opacity = '1'; setTimeout(() => { rg.style.opacity = '0'; }, 400); } } return; } }
      else key = 'f' + k;
      if (fc._k === key) return; fc._k = key; fc.style.display = ''; g.clearRect(0, 0, w, w); const fr = fogFrames(src === im ? f : ART.fogRev, src, w, src === im ? n : 8); g.drawImage(fr[k], 0, 0);
    }
    function cauDraw(t, i, ms) { if (!isV3() || t.dataset.th !== 'lake') return; const im = aimg(ART.cau), c = t.querySelector('canvas.cau'); if (!im) return; const k = Math.floor(ms / 250) % 4; if (c._k === k) return; c._k = k; if (c.width !== 168) { c.width = 168; c.height = 168; } const g = c.getContext('2d'); g.clearRect(0, 0, 168, 168); g.drawImage(im, tvar(i) * 168, k * 168, 168, 168, 0, 0, 168, 168); }
    // 團絨 dream_walk（6 幀 6fps；1 art px＝2 CSS；pivot 企喺格中）＋睡帽另一層（json 逐幀 xy；向左成組 flipX）
    function petArt(P, ms) {
      const fk = fkNow(), pj = fk && A.j && A.j.pets[fk], im = pj && aimg(pj['1x']), nc = pj && pj.nightcap, ck = nc && A.j.keys[nc.key], ci = ck && aimg(ck['1x']);
      if (!im) return false;
      const [fw, fh] = pj.frameSize, [px, py] = pj.pivot, n = pj.frames || 6, f = Math.floor(ms / (1000 / (pj.fps || 6))) % n;
      const pc = P.pc; if (pc.width !== fw || pc.height !== fh) { pc.width = fw; pc.height = fh; pc.style.width = fw * 2 + 'px'; pc.style.height = fh * 2 + 'px'; }
      pc.style.left = -px * 2 + 'px'; pc.style.top = -py * 2 + 'px';
      if (pc._f !== f || pc._fk !== fk) { const g = pc.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, fw, fh); g.drawImage(im, f * fw, 0, fw, fh, 0, 0, fw, fh); pc._f = f; pc._fk = fk; }
      P.pet.classList.remove('ph'); delete P.pet.dataset.ph; P.pet.dataset.art = '6c:dream_walk'; P.pet.dataset.fk = fk; P.pet.dataset.frame = f; P.pet.dataset.dir = R.dir < 0 ? 'L' : 'R';
      P.pf.style.transform = R.dir < 0 ? 'scaleX(-1)' : '';
      const sw = Math.max(20, Math.round(fw * 1.1)); P.sh.style.display = ''; P.sh.style.width = sw + 'px'; P.sh.style.left = -sw / 2 + 'px';
      if (ci && nc.xy && nc.xy[f]) { const [cw, chh] = ck.size, cap = P.cap; if (cap.width !== cw || cap.height !== chh) { cap.width = cw; cap.height = chh; cap.style.width = cw * 2 + 'px'; cap.style.height = chh * 2 + 'px'; const g = cap.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, cw, chh); g.drawImage(ci, 0, 0); }
        cap.style.left = (nc.xy[f][0] - px) * 2 + 'px'; cap.style.top = (nc.xy[f][1] - py) * 2 + 'px'; delete cap.dataset.ph; cap.dataset.art = ck === A.j.keys[nc.key] ? nc.key : '6c:nightcap'; }
      return true;
    }
    // 過場：入夢 0→9（收埋花園）→ 地圖；出夢 0→9 收埋地圖 → 小結 9→0；每幀 125ms（8fps）
    function trFrame(c, k) {
      const v3 = isV3(), im = aimg(ART.tr(k)); if (!im) return false;
      if (!c.classList.contains('art')) { c.classList.add('art'); c.style.background = 'none'; delete c.dataset.ph; c.dataset.art = '6c:transition' + (v3 ? '_v3' : ''); }
      const W = v3 ? 585 : 195, H = v3 ? 1266 : 422; if (c.width !== W) { c.width = W; c.height = H; }
      const g = c.getContext('2d'); g.imageSmoothingEnabled = !v3 ? false : true; g.clearRect(0, 0, W, H); if (v3) g.drawImage(im, 0, 0); else g.drawImage(im, k * 195, 0, 195, 422, 0, 0, 195, 422); return true;
    }
    const trReady = () => { if (!A.j) return false; if (isV3()) { let ok = true; for (let k = 0; k < 10; k++) if (!aimg(ART.tr(k))) ok = false; return ok; } return !!aimg(ART.tr(0)); };
    function trPlay(dir, done) {   // dir 1：0→9；-1：9→0
      const P = R.P; if (!P) { if (done) done(); return false; } const c = P.tr; R.trT = { t0: pnow(), dir, done };
      if (!c.classList.contains('art')) return false; c.style.transition = 'none'; c.style.opacity = '1'; trFrame(c, dir > 0 ? 0 : 9); return true;
    }
    function trTick(ms) {
      const T2 = R.trT, P = R.P; if (!T2 || !P) return; const e = pnow() - T2.t0, k = Math.min(9, Math.floor(e / 125)), fr = T2.dir > 0 ? k : 9 - k;
      if (P.tr.classList.contains('art') && P.tr._k !== fr) { P.tr._k = fr; trFrame(P.tr, fr); }
      if (e >= 1250) { R.trT = null; const d = T2.done; if (d) d(); }
    }
    // 每 frame（夢開住）：霧、caustic、團絨、過場
    function anim() {
      if (!R.el || !R.P) { R.raf = 0; return; } const ms = pnow();
      if (A.dirty) { A.dirty = 0; artAll(); R.fogDirty = 1; }
      { const fk = Math.floor(ms / 250) + ':' + ART.fog()[0], anim2 = Object.keys(R.revT).some(j => ms - R.revT[j] < 700);   // 霧：幀變／揭格動畫中／美術啱載 先行一轉
        if (R.fogK !== fk || anim2 || R.fogDirty) { R.fogK = fk; R.fogDirty = 0; R.P.tiles.forEach((t, i) => fogDraw(t, i, ms)); } }
      if (isV3()) R.P.tiles.forEach((t, i) => cauDraw(t, i, ms)); petArt(R.P, ms); trTick(ms);
      R.raf = requestAnimationFrame(anim);
    }
    function artAll() {
      const P = R.P; if (P) { const bf = ART.bg(), bi2 = aimg(bf); if (bi2 && A.j) { if (P.bgi.dataset.f !== bf) { P.bgi.src = B6C + bf; P.bgi.dataset.f = bf; } P.bgi.style.display = ''; P.bgi.classList.toggle('v3', isV3()); P.bgi.dataset.art = isV3() ? '6c:dream_bg_v3' : '6c:dream_bg'; P.bg.style.display = 'none'; }
        P.tiles.forEach((t, i) => tileArt(t, i));
        P.frs.forEach((d) => { const f = ART.frag(d.dataset.th), im = aimg(f); if (im && A.j && !d.dataset.art) { d.innerHTML = ''; d.appendChild(img(B6C + f, 'left:0;top:0;width:48px;height:48px')); delete d.dataset.ph; d.dataset.art = '6c:frag_' + d.dataset.th; } });
        if (!R.trT && !P.tr.classList.contains('art') && trReady()) { P.tr.classList.add('art'); P.tr.style.background = 'none'; delete P.tr.dataset.ph; P.tr.dataset.art = '6c:transition' + (isV3() ? '_v3' : ''); } }
      if (R.dexEl) dexArt();
      railIcon();
    }

    // ── 夢境狀態（唔存檔；已拾碎片即時入帳） ──
    const R = { on: false, el: null, plan: null, pos: DR.CFG.start, rev: {}, revT: {}, dir: 1, trT: null, raf: 0, got: {}, t0: 0, off: 0, phase: 'off', path: [], walkT: 0, seen: {}, res: [], endWhy: null, endAt: 0, sec: 0, P: null, dexEl: null, force: false };
    const elapsed = () => (R.on ? Math.max(0, (pnow() - R.t0) / 1000 + R.off) : 0);
    const left = () => Math.max(0, DR.CFG.durSec - elapsed());
    const TS = 112, TX = (i) => 22 + (i % 3) * (TS + 4), TY = (i) => 164 + Math.floor(i / 3) * (TS + 4);   // 3×5：格 112（56 art ×2）、間 4、x0 22（art 11）；地圖 164–740（頂留俾標題／時間／用途句）
    const mmss = (sec) => { sec = Math.ceil(sec); return Math.floor(sec / 60) + ':' + String(sec % 60).padStart(2, '0'); };
    const busy = () => R.on || !!R.dexEl || !!document.getElementById('l6bov') || !!document.getElementById('l5bov') || !!document.getElementById('l5ov') || !!document.getElementById('l5cov') || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene');
    function host() { return document.getElementById('ui') || document.body; }
    function shell(tid) {
      const el = mk('div', '', null, tid); el.id = 'l6cov';
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      host().appendChild(el); document.body.classList.add('l6c-on', 'l6c-dr'); return el;
    }
    G.coverRender = () => !!(R.el && R.P && document.body.classList.contains('l6c-dr'));   // QA P2：夢境開住 main loop 唔使逐幀畫花園
    function unshell() { if (R.el) R.el.remove(); R.el = null; R.P = null; document.body.classList.remove('l6c-dr'); if (!R.dexEl) document.body.classList.remove('l6c-on'); }

    function start(why, force) {
      const s = S(), h = hour(); if (R.on) return { ok: false, why: 'on' };
      let p;
      if (force) { const o = DR.st(s); o.night = DR.nightKey(now(), h); o.n.dreams++; p = Object.assign({ ok: true }, DR.plan(s, now(), h)); }
      else p = DR.enter(s, now(), h);
      if (!p.ok) { note('deny', { why: p.why }); return p; }
      save(); closeDex(true);
      Object.assign(R, { on: true, plan: p, pos: p.start, rev: {}, revT: {}, dir: 1, trT: null, got: {}, t0: pnow(), off: 0, phase: 'in', path: [], walkT: 0, seen: {}, res: [], endWhy: null, endAt: 0, sec: 0, force: !!force });
      reveal(p.start); R.revT = {}; build(); note('enter', { why, night: p.night, n: p.n, facts: p.facts }); UIS('tap'); if (G.v3) G.v3.dream = true;   // 夢入面寵物光＝0
      const tr = R.P.tr, el0 = R.el;
      if (tr.classList.contains('art')) { el0.classList.add('pre'); trPlay(1, () => { if (R.el !== el0) return; el0.classList.remove('pre'); tr.style.transition = ''; void tr.offsetWidth; tr.style.opacity = '0'; }); }   // 夜幕收埋花園 → 地圖
      else { tr.style.transition = 'none'; tr.style.opacity = '1'; void tr.offsetWidth; tr.style.transition = ''; setTimeout(() => { if (R.P && R.P.tr === tr) tr.style.opacity = '0'; }, 60); }
      setTimeout(() => { if (R.on && R.phase === 'in') R.phase = 'play'; }, DR.CFG.fadeSec * 1000);
      return { ok: true, plan: p };
    }
    function reveal(i) { R.fogDirty = 1; const t = pnow(), rv = (j) => { if (!R.rev[j]) { R.rev[j] = 1; R.revT[j] = t; } }; rv(i); for (let j = 0; j < 15; j++) if (DR.adj(i, j)) rv(j); }
    function build() {
      if (R.el) R.el.remove(); const el = R.el = shell('l6c-ov'); const p = R.plan;
      // 星星背景
      const bg = mk('canvas', 'position:absolute;left:0;top:0;width:390px;height:844px;image-rendering:pixelated;pointer-events:none'); bg.width = 195; bg.height = 422; { const g = bg.getContext('2d'); for (let k = 0; k < 70; k++) { g.fillStyle = k % 5 ? 'rgba(255,245,220,.5)' : '#FFE08A'; g.fillRect((k * 53) % 195, (k * 97) % 422, 1, 1); } } el.appendChild(bg);
      const bgi = mk('img', 'display:none', null, 'l6c-bg'); bgi.className = 'bgi u63no'; bgi.alt = ''; bgi.draggable = false; el.appendChild(bgi);
      // 頂：標題＋時間＋碎片
      el.appendChild(mk('div', `position:absolute;left:50%;top:16px;transform:translateX(-50%);min-width:160px;height:48px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '夢境', 'l6c-title'));
      el.appendChild(subEl(SUBT.dream, 'position:absolute;left:16px;right:16px;top:116px;text-align:center;'));
      const tTime = mk('div', `position:absolute;left:16px;top:72px;height:40px;box-sizing:border-box;display:flex;align-items:center;padding:0 12px;white-space:nowrap;${INSET()}` + TXT(24, CREAM), '', 'l6c-time');
      const tFrag = mk('div', `position:absolute;right:16px;top:72px;height:40px;box-sizing:border-box;display:flex;align-items:center;padding:0 12px;white-space:nowrap;${INSET()}` + TXT(24, GOLD), '', 'l6c-frags');
      el.appendChild(tTime); el.appendChild(tFrag);
      // 地圖 3×5
      const tiles = [];
      for (let i = 0; i < 15; i++) { const th = p.grid[i], t = mk('div', `left:${TX(i)}px;top:${TY(i)}px`, null, 'l6c-tile-' + i); t.className = 'tile u63no'; t.dataset.th = th; t.dataset.ph = '6c:tile_' + th;
        const cv = mk('canvas'); cv.className = 'base'; cv.width = 50; cv.height = 50; drawTile(cv, th, i); t.appendChild(cv);
        t.appendChild(mk('canvas')).className = 'gl'; t.appendChild(mk('canvas')).className = 'cau'; const rg = mk('img'); rg.className = 'rg'; rg.alt = ''; t.appendChild(rg); t.appendChild(mk('canvas')).className = 'fog';
        t.addEventListener('click', (e) => { e.stopPropagation(); tap(i); }); el.appendChild(t); tiles.push(t); }
      // 碎片
      const frs = p.frags.map(f => { const d = mk('div', `left:${TX(f.tile) + 48}px;top:${TY(f.tile) + 4}px;display:none`, null, 'l6c-frag-' + f.id); d.className = 'frag u63no'; d.dataset.ph = '6c:frag'; d.dataset.th = f.th;
        const cv = mk('canvas', 'position:absolute;left:0;top:0;width:48px;height:48px;image-rendering:pixelated'); cv.width = 24; cv.height = 24; drawFrag(cv, f.th); d.appendChild(cv); el.appendChild(d); return d; });
      // 團絨（夢中行 clip placeholder＋睡帽）
      const pet = mk('div', '', null, 'l6c-pet'); pet.className = 'pet ph u63no'; pet.dataset.ph = '6c:dream_walk'; const pf = mk('div', 'position:absolute;left:0;top:0;width:0;height:0'); pf.className = 'pf'; pet.appendChild(pf);   // pf：向左 flipX（圍 pivot）
      const sh = mk('div', 'display:none'); sh.className = 'sh'; pf.appendChild(sh); const pc = mk('canvas'); pc.className = 'pc'; pc.width = 80; pc.height = 80; pf.appendChild(pc); petDraw(pc);
      const cap = mk('canvas', '', null, 'l6c-cap'); cap.className = 'cap'; cap.width = 18; cap.height = 14; cap.dataset.ph = '6c:nightcap'; drawCap(cap); pf.appendChild(cap); el.appendChild(pet);
      // 底：提示＋醒返
      const hint = mk(V62() ? 'small' : 'div', 'position:absolute;left:16px;right:16px;top:748px;text-align:center;' + TXT(24, LAV), '撳格仔，陪團絨喺夢入面行', 'l6c-hint'); el.appendChild(hint);
      const wake = mk('div', `position:absolute;left:115px;top:776px;width:160px;${bi('btn_sec')}` + TXT(24, CREAM), '醒返', 'l6c-wake'); wake.className = 'btn';
      wake.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); end('wake'); }); el.appendChild(wake);
      const tr = mk('canvas', '', null, 'l6c-tr'); tr.className = 'tr'; tr.width = 1; tr.height = 1; tr.dataset.ph = '6c:transition'; el.appendChild(tr);
      R.P = { tiles, frs, pet, pf, pc, cap, sh, tTime, tFrag, hint, wake, tr, bg, bgi }; R.fogK = null; R.fogDirty = 1; place(true); render(); artAll(); if (!R.raf) R.raf = requestAnimationFrame(anim);
    }
    function place() { const P = R.P; if (!P) return; P.pet.style.left = (TX(R.pos) + 56) + 'px'; P.pet.style.top = (TY(R.pos) + 90) + 'px'; }
    function render() {
      const P = R.P, p = R.plan; if (!P || !p) return; const e = elapsed();
      P.tiles.forEach((t, i) => { t.dataset.rev = R.rev[i] ? '1' : '0'; });
      p.frags.forEach((f, k) => { const d = P.frs[k]; const show = e >= f.at && !R.got[f.id]; d.style.display = show ? '' : 'none'; d.dataset.on = show ? '1' : '0'; });
      P.tTime.textContent = '剩 ' + mmss(left()); P.tFrag.textContent = '夢碎片 ' + Object.keys(R.got).length + '／' + p.frags.length;
    }
    // 撳格：逐格行過去（先上落後左右）
    function tap(i) {
      if (!R.on || R.phase !== 'play') return false; if (i === R.pos && !R.path.length) return false;
      const path = []; let r = Math.floor(R.pos / 3), c = R.pos % 3; const tr = Math.floor(i / 3), tc = i % 3;
      while (r !== tr) { r += r < tr ? 1 : -1; path.push(r * 3 + c); } while (c !== tc) { c += c < tc ? 1 : -1; path.push(r * 3 + c); }
      R.path = path; UIS('tap'); note('tap', { i, n: path.length }); return true;
    }
    function step() {
      const i = R.path.shift(); if (i == null) return; if (i % 3 !== R.pos % 3) R.dir = i % 3 < R.pos % 3 ? -1 : 1; R.pos = i; reveal(i); place();
      const th = R.plan.grid[i]; if (!R.seen[th]) { R.seen[th] = 1; if (Object.keys(R.seen).length > 1 || th !== R.plan.grid[R.plan.start]) toast(DR.TH[th].zh + '（' + DR.TH[th].why + '）', 1800); }
      collect();
    }
    function collect() {
      const e = elapsed(), s = S();
      for (const f of R.plan.frags) if (f.tile === R.pos && e >= f.at && !R.got[f.id]) {
        R.got[f.id] = 1; const r = DR.pick(s, f.th, now()); R.res.push(r); save(); UIS('reward'); note('pick', { th: f.th, card: r.card, furn: r.furn });
        if (r.card) toast('砌好夢圖鑑「' + DR.CK[r.card].zh + '」！', 2400); else toast('拾到夢碎片（' + DR.TH[f.th].zh + '・再 ' + DR.toNext(s, f.th) + ' 片砌 1 張）', 1800);
        if (r.furn) setTimeout(() => toast('砌齊' + DR.TH[f.th].zh + '：送你家具「' + FAM.SV[r.furn].zh + '」', 2800), 900);
      }
      render();
    }
    // 收尾：出夢過場 → 小結
    function end(why) {
      if (!R.on || R.phase === 'out' || R.phase === 'sum') return false; R.phase = 'out'; R.endWhy = why; R.sec = elapsed(); R.path = [];
      const got = Object.keys(R.got).length; DR.endLog(S(), R.plan.night, got, R.sec, Object.keys(R.plan.n)); save(); note('end', { why, got, sec: Math.round(R.sec) });
      if (R.P) { if (R.P.tr.classList.contains('art')) trPlay(1); else R.P.tr.style.opacity = '1'; }   // 出夢：夜幕收埋地圖
      R.endAt = pnow(); setTimeout(() => { if (R.on && R.phase === 'out') summaryCard(); }, DR.CFG.fadeSec * 1000);
      return true;
    }
    function summaryCard() {
      R.phase = 'sum'; const s = S(), got = Object.keys(R.got).length, el = R.el; if (!el) return finish();
      const P = R.P; if (P) { if (P.tr.classList.contains('art')) trPlay(-1, () => { P.tr.style.transition = 'none'; P.tr.style.opacity = '0'; }); else P.tr.style.opacity = '0'; } el.appendChild(mk('div', 'position:absolute;inset:0;z-index:8;background:rgba(12,9,32,.78)'));   // 小結：9→0 打開
      const box = mk('div', `position:absolute;left:24px;top:212px;width:342px;box-sizing:border-box;z-index:10;padding:36px 16px 16px;${PAN()}`, null, 'l6c-sum'); if (V62()) box.className = 'u62pan'; el.appendChild(box);
      box.appendChild(mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:180px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '夢醒喇', 'l6c-sum-title'));
      box.appendChild(subEl(SUBT.sum, 'position:relative;margin:0 0 12px !important;text-align:center;'));
      const line = (t, c, tid, tag) => box.appendChild(mk(tag || 'div', 'position:relative;margin:4px 0;' + TXT(24, c || CREAM), t, tid));
      line(R.endWhy === 'time' ? '天光喇，夢完咗。' : R.endWhy === 'all' ? '夢碎片拾晒！' : '你叫醒咗團絨（佢繼續瞓）。', LAV, 'l6c-sum-why');
      line('今晚拾到 ' + got + '／' + R.plan.frags.length + ' 片夢碎片', GOLD, 'l6c-sum-got');
      for (const r of R.res) if (r.card) line('新夢圖鑑：「' + DR.CK[r.card].zh + '」', MINT, 'l6c-sum-card');
      for (const r of R.res) if (r.furn) line('砌齊' + DR.TH[r.th].zh + '：送家具「' + FAM.SV[r.furn].zh + '」', MINT, 'l6c-sum-furn');
      line('夢圖鑑 ' + DR.summary(s, now(), hour()).cards + '／' + DR.CARDS.length + ' 張', CREAM, 'l6c-sum-dex');
      line('唔會加分、唔會出碎，團絨照瞓。', CREAM, 'l6c-sum-note', V62() ? 'small' : 'div');
      const row = mk('div', 'position:relative;display:flex;gap:12px;margin-top:16px'); box.appendChild(row);
      const b1 = mk('div', `flex:1 1 0;${bi('btn_sec')}` + TXT(24, CREAM), '睇夢圖鑑', 'l6c-sum-dexbtn'); b1.className = 'btn'; b1.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); finish(); openDex('sum'); }); row.appendChild(b1);
      const b2 = mk('div', `flex:1 1 0;${bi('btn_pri')}` + TXT(24, CREAM), '好', 'l6c-sum-ok'); b2.className = 'btn'; b2.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); finish(); }); row.appendChild(b2);
    }
    function finish() { if (!R.on) return false; R.on = false; R.phase = 'off'; R.trT = null; if (G.v3) G.v3.dream = false; if (R.raf) cancelAnimationFrame(R.raf); R.raf = 0; unshell(); note('close'); railTick(); return true; }

    // ── 夢圖鑑（4 主題 × 5 張） ──
    function closeDex(quiet) { if (!R.dexEl) return false; R.dexEl.remove(); R.dexEl = null; if (!R.el) document.body.classList.remove('l6c-on'); if (!quiet) note('dexClose'); return true; }
    function openDex(why) {
      closeDex(true); const s = S(), sm = DR.summary(s, now(), hour());
      const el = R.dexEl = mk('div', 'position:absolute;left:0;top:0;width:390px;height:844px;z-index:61;user-select:none;-webkit-user-select:none', null, 'l6c-dex'); el.id = 'l6cdex';
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      const bd = mk('div', 'position:absolute;inset:0;background:rgba(18,12,30,.7)'); bd.addEventListener('click', () => { UIS('tap'); closeDex(); }); el.appendChild(bd);
      const p = mk('div', `position:absolute;left:16px;top:80px;width:358px;box-sizing:border-box;padding:36px 16px 16px;${PAN()}`, null, 'l6c-dex-panel'); if (V62()) p.className = 'u62pan'; el.appendChild(p);
      p.appendChild(mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:180px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '夢圖鑑 ' + sm.cards + '／' + sm.total, 'l6c-dex-title'));
      p.appendChild(subEl(SUBT.dex, 'position:relative;margin:0 0 4px !important;text-align:center;'));
      const x0 = mk('div', `position:absolute;right:-23px;top:-25px;z-index:5;width:52px;height:52px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center` + TXT(24, CREAM), null, 'l6c-dex-close');
      x0.appendChild(mk('div', `position:relative;flex:0 0 auto;width:30px;height:30px;pointer-events:none;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}`, sp('close') ? '' : '✕'));
      x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeDex(); }); p.appendChild(x0);
      const det = mk('div', `position:relative;margin-top:12px;min-height:44px;padding:8px 12px;box-sizing:border-box;${INSET()}` + TXT(24, CREAM), '撳一張睇名', 'l6c-dex-detail');
      for (const th of DR.THEMES) {
        const n = sm.byTh[th], f = DR.toNext(s, th);
        const hd = p.appendChild(mk('div', 'position:relative;margin:8px 0 4px;' + TXT(24, GOLD), DR.TH[th].zh + ' ' + n + '／5' + (n >= 5 ? (sm.furn[th] && sm.furn[th] !== 'none' ? '・送咗家具' : '・齊晒') : '・再 ' + f + ' 片'), 'l6c-dex-th-' + th)); hd.className = 'ttl';
        const row = mk('div', 'position:relative;display:flex;gap:12px;padding:0 4px'); p.appendChild(row);
        for (const c of DR.CARDS.filter(c => c.th === th)) { const have = !!DR.st(s).cards[c.id], e = mk('div', '', null, 'l6c-card-' + c.id); e.className = 'card6'; e.dataset.ph = '6c:card_' + c.id; e.dataset.have = have ? '1' : '0';
          const cv = mk('canvas'); cv.width = 28; cv.height = 36; drawCard(cv, c, have); e.appendChild(cv); e._c = c;
          e.addEventListener('click', (ev) => { ev.stopPropagation(); UIS('tap'); det.textContent = have ? '「' + c.zh + '」（' + DR.TH[th].zh + '）' : '未砌到（' + DR.TH[th].zh + '）'; }); row.appendChild(e); }
      }
      p.appendChild(det);
      p.appendChild(mk(V62() ? 'small' : 'div', 'position:relative;margin:8px 0 0;' + TXT(24, MINT), '每 5 片夢碎片砌 1 張；砌齊一個主題送家具 1 件。', 'l6c-dex-note'));
      host().appendChild(el); document.body.classList.add('l6c-on'); dexArt(); note('dex', { why }); return el;
    }

    function dexArt() {   // 夢卡：V3 84×108 @3x／1x 28×36 → 56×72 CSS；未砌到 → card_back；標題由 code 寫（撳睇名）
      if (!R.dexEl || !A.j) return; const v3 = isV3();
      R.dexEl.querySelectorAll('.card6').forEach((e) => { const c = e._c, have = e.dataset.have === '1', f = ART.card(c.id, have), im = aimg(f); if (!im || e.dataset.f === f) return;
        const cv = e.querySelector('canvas'), w = v3 ? 84 : 28, h = v3 ? 108 : 36; cv.width = w; cv.height = h; const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, w, h); g.drawImage(im, 0, 0, w, h);
        e.dataset.f = f; delete e.dataset.ph; e.dataset.art = '6c:card_' + (have ? c.id : 'back') + (v3 ? '_v3' : ''); });
    }
    function railIcon() {   // rail：ic_dream（入夢）／ic_dreambook（夢簿），16 art ×2＝32 CSS 置中
      const el = RB.el; if (!el || !A.j) return; const n = RB.mode === 'enter' ? 'ic_dream' : 'ic_dreambook', f = ART.icon(n); if (el.dataset.art === n || !aimg(f)) return;
      const box = el.querySelector('i.i'); box.innerHTML = ''; box.appendChild(img(B6C + f, 'left:2px;top:2px;width:32px;height:32px')); el.dataset.art = n;
    }
    function preload() {   // 入夢前預載而家模式要用嘅圖（第一次入夢唔使等）
      if (!A.j) return; aimg(ART.bg()); for (const th of DR.THEMES) { aimg(ART.tile(th)[0]); aimg(ART.frag(th)); if (isV3()) aimg(ART.glow(th)); } aimg(ART.fog()[0]);
      if (isV3()) { aimg(ART.cau); aimg(ART.fogRev); aimg(ART.rg); for (let k = 0; k < 10; k++) aimg(ART.tr(k)); } else aimg(ART.tr(0));
      const fk = fkNow(), pj = fk && A.j.pets[fk]; if (pj) { aimg(pj['1x']); const ck = pj.nightcap && A.j.keys[pj.nightcap.key]; if (ck) aimg(ck['1x']); }
      aimg(ART.icon('ic_dream')); aimg(ART.icon('ic_dreambook'));
    }

    // ── 花園 rail「入夢」／「夢簿」 ──
    const RB = { el: null, mode: null };
    function railTick() {
      const s = S(); if (!s) return; const c = DR.canEnter(s, now(), hour()), any = DR.st(s).n.frags > 0;
      const show = !document.body.classList.contains('s2-scene') && s.stage !== 'egg' && (c.ok || any); let el = RB.el;
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), hst = rail || document.getElementById('top-r'); if (!hst) return;
        el = RB.el = mk('div', '', null, 'l6c-rail'); el.id = 'l6cbtn'; el.className = 'ibtn panel';
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l"></i><i class="rd"></i>'; el.querySelector('i.i').appendChild(img(LB5 + 'icon_rest@3x.png', 'left:0;top:0;width:36px;height:36px'));
        el.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); if (RB.mode === 'enter') start('rail'); else openDex('rail'); }); hst.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return;
      RB.mode = c.ok ? 'enter' : 'dex'; railIcon(); if (c.ok && !RB.pre && A.j) { RB.pre = 1; preload(); } const lb = el.querySelector('i.l'); const t = c.ok ? '入夢' : '夢簿'; if (lb.textContent !== t) lb.textContent = t; el.title = t; el.dataset.mode = RB.mode;
      const rd = el.querySelector('i.rd'); if (rd) rd.style.display = c.ok ? '' : 'none';
      const vis = (id) => { const e = document.getElementById(id); return !!(e && e.style.display !== 'none' && e.offsetParent !== null); };
      el.setAttribute('aria-label', t);
      const st = 1 + (vis('l5egg') ? 1 : 0) + (vis('l5cbtn') ? 1 : 0) + (vis('l6bbtn') ? 1 : 0) + (vis('u62workbtn') ? 1 : 0), u = U(), rl = u && u.rail;
      const above = ['u62workbtn', 'l6bbtn'].map(id => document.getElementById(id)).find(e => e && vis(e.id) && e.style.top);   // 6b.2：排喺「工作」／「散步」下面（70px 一格）
      if (above && parseFloat(above.style.top) + 70 <= 620) { el.style.left = above.style.left; el.style.top = (parseFloat(above.style.top) + 70) + 'px'; }
      else if (rl && rl.kid && rl.dex) { const dy = rl.kid.y - rl.dex.y; let x = rl.kid.x, y = rl.kid.y + st * dy; if (y > 620) { x = rl.kid.x - 76; y = rl.kid.y + (st - 1) * dy; } el.style.left = x + 'px'; el.style.top = y + 'px'; }
      else { el.style.left = '360px'; el.style.top = (320 + st * 64) + 'px'; }
    }
    // ── 每 200ms：夢入面行路／計時；每秒：rail ──
    const T = { last: 0, n: 0 };
    function tick() {
      const t = pnow();
      const dt = T.pt ? (t - T.pt) / 1000 : 0; T.pt = t;
      if (R.on) {
        if (R.phase === 'play' && document.getElementById('u62tip') && dt > 0 && dt < 1) R.off -= dt;   // 一次性提示開住：夢嘅時間暫停
        if (R.phase === 'play') {
          if (R.path.length && t - R.walkT >= 300) { R.walkT = t; step(); }
          const e = elapsed(); if (Math.floor(e * 5) !== R._e) { R._e = Math.floor(e * 5); collect(); }
          const allSpawned = e >= Math.max.apply(null, R.plan.frags.map(f => f.at));
          if (Object.keys(R.got).length >= R.plan.frags.length && allSpawned) end('all');
          else if (e >= DR.CFG.durSec) end('time');
        } else if (R.phase === 'sum' && elapsed() > DR.CFG.maxSec + 600) finish();
        if (R.phase !== 'sum' && R.phase !== 'off' && elapsed() >= DR.CFG.maxSec - DR.CFG.fadeSec) end('time');
      }
      if (A.dirty && !R.raf) { A.dirty = 0; try { artAll(); } catch (e) { } }
      if (t - T.last >= 1000) { T.last = t; T.n++; try { railTick(); } catch (e) { } }
    }
    { const loop = () => { try { tick(); } catch (e) { } setTimeout(loop, 100); }; setTimeout(loop, 400); }

    // ── 🛠 開發者模式「6c」 ──
    const WHY = { ok: '可以', egg: '蛋', km: '細佬主養', awake: '未瞓', hours: '唔係夜晚', done: '今晚入過', bank: '補做錯過嗰晚' };
    const fakeLog = () => { const M6 = NS.long6a, s = S(), t = now(); if (!M6) return { ok: false, msg: '冇 6a' }; for (let i = 0; i < 3; i++) M6.note(s, 'food', 'meal', 0, 0, 0, t); for (let i = 0; i < 2; i++) M6.note(s, 'care', 'rinse', 0, 0, 0, t); for (let i = 0; i < 3; i++) M6.note(s, 'care', 'play', 0, 0, 0, t); save(); return { ok: true, msg: '今日：暖菇飯 3、淋水 2、玩 3' }; };
    const addFr = (th, n) => { const s = S(); let r = null, cards = 0, furn = null; for (let i = 0; i < n; i++) { r = DR.pick(s, th, now()); if (r.card) cards++; if (r.furn) furn = r.furn; } save(); railTick(); return { ok: true, msg: DR.TH[th].zh + ' +' + n + ' 片 → 新卡 ' + cards + (furn ? '、家具「' + FAM.SV[furn].zh + '」' : '') }; };
    const DEV = { id: 'l6c', title: '6c（夢境探險）', order: 47,
      status: () => { const m = DR.summary(S(), now(), hour()); return '入夢 ' + (WHY[m.why] || m.why) + '・圖鑑 ' + m.cards + '／' + m.total + '・碎片 菇' + m.frag.forest + ' 水' + m.frag.lake + ' 玩' + m.frag.toy + ' 星' + m.frag.star + (R.on ? '・夢緊 ' + Math.round(elapsed()) + ' 秒' : ''); },
      items: [
        ['night', '設夜晚 22:00＋瞓緊', () => { G.hourOverride = 22; const s = S(); s.sleeping = true; save(); railTick(); return { ok: true, msg: '22:00、團絨瞓咗' }; }],
        ['log', '模擬記錄（菇／水／玩）', fakeLog],
        ['enter', '入夢（照規則）', () => { const r = start('dev'); return { ok: r.ok, msg: r.ok ? '入咗夢' : '入唔到：' + (WHY[r.why] || r.why) }; }],
        ['force', '入夢（唔理時間）', () => { const r = start('dev', true); return { ok: r.ok, msg: r.ok ? '入咗夢' : '夢緊' }; }],
        ['again', '今晚可以再入夢', () => { DR.resetNight(S()); save(); railTick(); return { ok: true, msg: '今晚未用' }; }],
        ['p5', '加 5 片（星空）', () => addFr('star', 5)],
        ['theme', '砌齊蘑菇森林', () => addFr('forest', DR.CFG.perCard * DR.CFG.cardsPerTheme - DR.st(S()).frag.forest > 0 ? DR.CFG.perCard * DR.CFG.cardsPerTheme - DR.st(S()).frag.forest : 1)],
        ['all', '夢圖鑑全開', () => { for (const th of DR.THEMES) { const k = DR.CFG.perCard * DR.CFG.cardsPerTheme - DR.st(S()).frag[th]; if (k > 0) addFr(th, k); } return { ok: true, msg: '20 張' }; }],
        ['skip', '夢：快轉 30 秒', () => { if (!R.on) return { ok: false, msg: '未入夢' }; R.off += 30; render(); return { ok: true, msg: '剩 ' + mmss(left()) }; }],
        ['end', '夢：時間到', () => { if (!R.on) return { ok: false, msg: '未入夢' }; R.off += DR.CFG.durSec; return { ok: true, msg: '天光' }; }],
        ['dex', '睇夢圖鑑', () => { openDex('dev'); return { ok: true, msg: '開咗' }; }],
        ['reset', '重設 6c', () => { if (R.on) finish(); DR.reset(S()); save(); railTick(); return { ok: true, msg: '6c 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l6c = { start, end, finish, openDex, closeDex };
    window.__qa = window.__qa || {};
    window.__qa.l6c = {
      st: () => Object.assign(DR.summary(S(), now(), hour()), { on: R.on, phase: R.phase, pos: R.pos, path: R.path.slice(), got: Object.keys(R.got).length, elapsed: elapsed(), left: left(), endWhy: R.endWhy, sec: R.sec,
        rev: Object.keys(R.rev).length, dex: !!R.dexEl, v3: isV3(), art: !!A.j, artErr: A.err.slice(0, 5), rail: !!(RB.el && RB.el.style.display !== 'none'), railMode: RB.mode, seen: Object.keys(R.seen) }),
      plan: () => (R.plan ? JSON.parse(JSON.stringify(R.plan)) : null), artLoad: () => A6c.then(() => { preload(); return !!A.j; }), artN: () => Object.keys(A.img).length, raw: () => JSON.parse(JSON.stringify(DR.st(S()))), log: () => log.slice(), toasts: () => toasts.slice(), dev: () => DEV,
      start, end, finish, tap, openDex, closeDex, skip: (sec) => { R.off += +sec || 0; render(); return elapsed(); }, railTick,
      walkTo: (i) => { tap(i); while (R.path.length) step(); return R.pos; },
    };
    note('install', {});
    return true;
  }
  return { install };
});
