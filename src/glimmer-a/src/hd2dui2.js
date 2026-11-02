/* 《微光小圃》 hd2dui2.js — HD-2D UI kit v2（遊美 art/ui_hd2d_v2：UI_KIT_V2.md／PORTRAIT_SYNC.md／layout_hd2d_v2.json）。原創代碼，只用 kit 自家圖＋Fusion Pixel（OFL 1.1）。
   做法：疊喺 v1 hd2dui.js 上面嘅換膚層（#ui.hd.v2）：唔改遊戲邏輯／DOM id／testid／v1 動態同 ui8 v3 音效 hook；只換零件、排位、字、頭像。
   - 零件：ui_hd2d_v2@1x 每個 frame 用 canvas ×2 nearest 裁成 dataURL（1 art px ＝ 2 CSS px，整數倍）；9／3-slice 一律 border-image「repeat」（tile，唔 stretch）、image-rendering:pixelated。
   - 排位：全部由 layout_hd2d_v2.json（1x）× 2。
   - 字：Fusion Pixel 8／10／12（子集 TTF，FontFace＋fetch 載，單檔 build 都得）：CSS 16／20／24 px；10／12 描邊＋影、8 喺深色面板唔描邊、泡泡用 ink 唔描邊。
   - 頭像：portrait_rects.json 即場裁 22×22 → ×2 入 portrait_frame 窗（bg_<心情> → 寵物 → mask → 框 → mood_badge）。
   - 切換：?ui=1 → v1（kit_hd2d 原封保留）；?ui=2 → v2；冇 flag → localStorage glimmer.ui（預設 v2）。🛠 開發者模式「UI v2」即時切換＋逐個彈窗睇。
   QA：window.__qa.uiv2。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.hd2dui2 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const KEY = 'glimmer.ui';
  const NEED = { hunger: ['feed', 'pri'], mood: ['heart', 'rose'], clean: ['clean', 'sec'], energy: ['sleep', 'violet'] };
  const ACT = { 'btn-feed': ['feed', 'pri'], 'btn-play': ['play_cat', 'rose'], 'btn-clean': ['clean', 'sec'], 'btn-sleep': ['sleep', 'violet'] };
  const TABK = ['home', 'play', 'garden', 'journal', 'set'];
  const SLOT_IC = { bed: 'furniture', table: 'cabinet', wall: 'pattern', rug: 'd_leaf', window: 'house', lamp: 'light', deco: 'gift' };   // deco＝5a 第 7 個 tab「擺設」（手信）
  const MOODS = ['normal', 'happy', 'hungry', 'sleepy', 'sick', 'sleep'];
  // 純函數（unit test 用）
  function pref(qsUi, stored) { if (qsUi === '1') return 1; if (qsUi === '2') return 2; return stored === '1' ? 1 : 2; }
  function moodOf(s) {
    if (!s || !s.needs) return 'normal'; const n = s.needs;
    if (s.sleeping) return 'sleep'; if (s.sick || s.ill) return 'sick';
    if (n.hunger < 30) return 'hungry'; if (n.energy < 30) return 'sleepy'; if (n.mood >= 70) return 'happy'; return 'normal';
  }
  function rectOf(R, fk, frame) {   // PORTRAIT_SYNC §1／§4：forms[fk] → aliases → 冇就用 frame 中上（眼約 45% 高）
    const F = R && R.forms || {}, al = R && R.aliases || {};
    const r = F[fk] || (al[fk] && F[al[fk]]) || null; if (r) return { rect: r.rect.slice(), frame: r.frame, acc: r.acc || {}, hit: true };
    const fs = frame || 32, pad = (R && R.pad) || 8, ex = pad + fs / 2, ey = pad + fs * 0.45;
    return { rect: [Math.round(ex - 11), Math.round(ey - 11), 22], frame: fs, acc: {}, hit: false };
  }
  function accAdj(rect, a) { const r = rect.slice(); if (a) r[1] -= a.shift || 0; return { rect: r, badge: !!(a && a.badge), pop: a ? a.pop || 0 : 0 }; }
  // border-image 片段（數字已 ×2）
  function biCss(u, f) {
    const nn = f.nine || [0, 0, 0, 0], [l, t, r, b] = nn.map(v => v * 2);
    return `border-style:solid !important; border-color:transparent !important; border-width:0 !important; border-image:url(${u}) ${t} ${r} ${b} ${l} fill / ${t}px ${r}px ${b}px ${l}px / 0 repeat !important; image-rendering:pixelated;`;
  }

  // TTF cmap（format 4／12）→ Set(codepoint)：用嚟判斷 FP12 子集有冇呢個字
  function cmapOf(buf) {
    const v = new DataView(buf), n = v.getUint16(4); let cm = -1;
    for (let i = 0; i < n; i++) { const o = 12 + i * 16; if (String.fromCharCode(v.getUint8(o), v.getUint8(o + 1), v.getUint8(o + 2), v.getUint8(o + 3)) === 'cmap') cm = v.getUint32(o + 8); }
    if (cm < 0) throw new Error('冇 cmap'); const out = new Set(), nt = v.getUint16(cm + 2); let best = -1, bf = 0;
    for (let i = 0; i < nt; i++) { const off = cm + v.getUint32(cm + 8 + i * 8), f = v.getUint16(off); if (f === 12 || (f === 4 && bf !== 12)) { best = off; bf = f; } }
    if (best < 0) throw new Error('冇 format 4/12');
    if (bf === 12) { const g = v.getUint32(best + 12); for (let i = 0; i < g; i++) { const o = best + 16 + i * 12, a = v.getUint32(o), b = v.getUint32(o + 4); for (let c = a; c <= b; c++) out.add(c); } }
    else { const sx = v.getUint16(best + 6) / 2; for (let i = 0; i < sx; i++) { const e = v.getUint16(best + 14 + i * 2), st = v.getUint16(best + 16 + sx * 2 + i * 2); for (let c = st; c <= e && c !== 0xFFFF; c++) out.add(c); } }
    return out;
  }
  // v2 CSS：FP8／FP10 → FP12，字號 floor 24px（FP12 嘅 2×），超過就去 36（3×）；line-height ≥ 28，同 line-height 一樣高嘅固定高度一齊升
  function readable(css) {
    const sz = (s) => s <= 0 ? s : s <= 24 ? 24 : s <= 36 ? 36 : Math.round(s / 12) * 12;
    return css.split('\n').map((ln) => {
      ln = ln.replace(/"GlimmerFP(8|10)"/g, '"GlimmerFP12"'); const ups = [];
      ln = ln.replace(/font:(var\(--sub2F,)?(\d+(?:\.\d+)?)px(\))?\/(\d+(?:\.\d+)?)px/g, (m, v, s, c, l) => { s = +s; l = +l; if (!s) return m; const ns = sz(s), nl = Math.max(l, Math.round(ns * 7 / 6)); if (nl > l) ups.push([l, nl]); return 'font:' + (v ? 'var(--sub2F,' + ns + 'px)' : ns + 'px') + '/' + nl + 'px'; });
      ln = ln.replace(/font-size:(\d+(?:\.\d+)?)px/g, (m, s) => +s ? 'font-size:' + sz(+s) + 'px' : m);
      for (const [l, nl] of ups) ln = ln.replace(new RegExp('([;{ ])height:' + l + 'px', 'g'), '$1height:' + nl + 'px');
      return ln;
    }).join('\n');
  }
  function readCss(H, FALL, F12, OL8, INK, CREAM, LINE) {
    return `
/* 5a.1 清晰度 */
#ui.hd.v2, #ui.hd.v2 * { -webkit-font-smoothing:none; font-smooth:never; font-synthesis:none; text-rendering:optimizeSpeed; }
#ui.hd.v2 :is([data-fbk="1"], #_z#_z#_z) { font-family:${FALL} !important; -webkit-font-smoothing:antialiased !important; }
${H}[data-rol="1"] { ${OL8} }
${H}.hdTg { padding:0 !important; margin-left:40px !important; text-indent:-34px; line-height:22px !important; text-align:left; white-space:nowrap; overflow:visible !important; }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] > div[style*="grid"] { grid-template-columns:1fr !important; gap:6px !important; }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] > div:first-child, ${H}#mbox[data-kind="devmode"] > div:first-child { flex-wrap:wrap; gap:0 12px; }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn { text-align:left; padding:0 12px !important; }
${H}.dexGrid > p { grid-column:1 / -1; }
${H}#s2houseV [data-testid="house-hint"] { left:72px !important; right:72px !important; }
${H}#substage { overflow:hidden !important; text-overflow:ellipsis !important; white-space:nowrap !important; }
${H}#modal { padding:14px 0 24px; box-sizing:border-box; }
${H}.s12tabs { flex-wrap:wrap; }
${H}.s12tabs b { flex:1 0 auto !important; white-space:nowrap; padding:0 6px !important; }
${H}.s12foot { flex-wrap:wrap; }
${H}.rt { white-space:nowrap; display:inline-block; }
#ui.hd.v2.sysf, #ui.hd.v2.sysf :is(*, #_z#_z#_z) { font-family:${FALL} !important; -webkit-font-smoothing:antialiased !important; text-rendering:auto !important; }
`;
  }
  function install(G, NS) {
    if (typeof document === 'undefined') return false;
    const HD = G.hdui; if (!HD || !HD.load) return false;          // 冇 v1 換膚（?hdui=0）→ v2 都唔掛
    const qs = new URLSearchParams(location.search), D = NS.data;
    const BASE = ((D.PARAMS.art && D.PARAMS.art.base) || 'art/') + 'ui_hd2d_v2/';
    const ui = document.getElementById('ui'), $ = (s) => document.querySelector(s);
    let stored = null; try { stored = localStorage.getItem(KEY); } catch (e) { }
    const U = G.ui2 = { ready: false, on: false, want: pref(qs.get('ui'), stored) === 2, forced: qs.get('ui'), errors: [], missing: [], fonts: {}, moodOv: null, accOv: null, face: null, log: [] };
    const note = (k, o) => { U.log.push(Object.assign({ k, t: Math.round(performance.now()) }, o || {})); if (U.log.length > 60) U.log.shift(); };
    const img = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('img ' + src)); i.src = src; });
    const json = (n) => fetch(BASE + n).then(r => { if (!r.ok) throw new Error(n + ' ' + r.status); return r.json(); });
    const atlas = (n) => json(n + '.json').then(j => img(BASE + (j.image ? j.image.replace(/^.*\//, '') : n + '.png')).then(im => ({ j, im })));
    const font = (n, fam) => fetch(BASE + 'fonts/' + n).then(r => r.arrayBuffer()).then(b => { if (fam === 'GlimmerFP12') { try { U.cov = cmapOf(b); } catch (e) { U.errors.push('cmap ' + e.message); } } const f = new FontFace(fam, b); return f.load(); }).then(f => { document.fonts.add(f); U.fonts[fam] = true; }).catch(e => { U.errors.push('font ' + n + ': ' + (e && e.message || e)); });
    U.load = Promise.all([HD.load, atlas('ui_hd2d_v2@1x'), atlas('icons_hd2d_v2@1x'), json('layout_hd2d_v2.json'), json('portrait_rects.json'),
      font('fp8-subset.ttf', 'GlimmerFP8'), font('fp10-subset.ttf', 'GlimmerFP10'), font('fp12-subset.ttf', 'GlimmerFP12')])
      .then(([, A, I, L, PR]) => { if (!HD.ready) throw new Error('v1 未 ready'); build(A, I, L, PR); })
      .catch(e => { U.errors.push(String(e && e.message || e)); console.warn('hd2dui2: kit v2 載唔到', e); });

    function build(A, I, L, PR) {
      const FR = A.j.frames, IC = I.j.frames, cache = {};
      U.layout = L; U.rects = PR; U.FR = FR; U.atlasImg = A.im;
      const crop2 = (src, f) => { const c = document.createElement('canvas'); c.width = f.w * 2; c.height = f.h * 2; const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.drawImage(src, f.x, f.y, f.w, f.h, 0, 0, f.w * 2, f.h * 2); return c.toDataURL(); };
      const fr = (n) => { const f = FR[n]; if (!f && !U.missing.includes(n)) U.missing.push(n); return f; };
      const url = (n) => cache[n] || (cache[n] = fr(n) ? crop2(A.im, FR[n]) : '');
      const iurl = (n) => { const k = 'ic:' + n; if (cache[k]) return cache[k]; if (!IC[n]) { if (!U.missing.includes('icon:' + n)) U.missing.push('icon:' + n); return ''; } return (cache[k] = crop2(I.im, IC[n])); };
      const bi = (n) => { const f = fr(n); return f ? biCss(url(n), f) : ''; };
      const sp = (n) => { const f = fr(n); return f ? `width:${f.w * 2}px !important; height:${f.h * 2}px !important; background:url(${url(n)}) 0 0 / ${f.w * 2}px ${f.h * 2}px no-repeat !important; border:0 !important; border-image:none !important; image-rendering:pixelated;` : ''; };
      const spBg = (n) => { const f = fr(n); return f ? `background:url(${url(n)}) 0 0 / ${f.w * 2}px ${f.h * 2}px no-repeat !important; border-image:none !important; image-rendering:pixelated;` : ''; };
      const ic = (n) => { const f = IC[n], u = iurl(n); return f ? `width:${f.w * 2}px; height:${f.h * 2}px; background:url(${u}) 0 0 / ${f.w * 2}px ${f.h * 2}px no-repeat !important; border:0 !important; border-image:none !important; image-rendering:pixelated;` : ''; };
      const icBg = (n) => { const f = IC[n], u = iurl(n); return f ? `background:url(${u}) 0 0 / ${f.w * 2}px ${f.h * 2}px no-repeat !important; border-image:none !important;` : ''; };
      const tile = (n) => { const f = fr(n); return f ? `background:url(${url(n)}) 0 0 / ${f.w * 2}px ${f.h * 2}px repeat !important; image-rendering:pixelated;` : ''; };
      U.url = url; U.iurl = iurl; U.bi = bi; U.sp = sp; U.ic = ic;
      const a2 = (v) => Math.round(v * 2);
      const INK = '#3A2840', CREAM = '#FFF5DC', LINE = '#24172C', GOLD = '#FFE08A';
      const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
      const F8 = `"GlimmerFP8",${FALL}`, F10 = `"GlimmerFP10",${FALL}`, F12 = `"GlimmerFP12",${FALL}`;
      const o8 = [[-2, 0], [2, 0], [0, -2], [0, 2], [-2, -2], [2, -2], [-2, 2], [2, 2]];
      const OL8 = 'text-shadow:' + o8.map(([x, y]) => `${x}px ${y}px 0 ${LINE}`).join(',') + ' !important;';
      const OL = 'text-shadow:' + o8.map(([x, y]) => `${x}px ${y}px 0 ${LINE}`).concat([`-2px 4px 0 ${LINE}`, `0 4px 0 ${LINE}`, `2px 4px 0 ${LINE}`]).join(',') + ' !important;';
      const NOL = 'text-shadow:none !important;';
      const PX = '-webkit-font-smoothing:none; font-smooth:never; font-kerning:none;';
      const H = '#ui.hd.v2 ';
      const P = L.portrait, NP = L.nameplate, ND = L.needs, CH = L.chips, TO = L.toast, AC = L.acts, DK = L.dock, PU = L.popup, HB = L.house4b;
      const tabW = DK.w * 2 / 5;
      // rail：layout 有 gift／mail／house；dex、細佬順住向下排（同間距）
      const RL = {}; L.rail.forEach(r => { RL[r.icon] = r; });
      const RS = 24, railC = (y) => ({ x: a2(RL.gift.x + RS / 2), y: a2(y + RS / 2) });
      const RAIL = { gift: railC(RL.gift.y), mail: railC(RL.mail.y), house: railC(RL.house.y), dex: railC(RL.house.y + 42), kid: railC(RL.house.y + 84) };
      U.rail = RAIL;
      const needXY = (i) => ({ x: a2(ND.x + ND.dx * (i % 2)), y: a2(ND.y + ND.dy * Math.floor(i / 2)) });
      const NEEDK = ['hunger', 'mood', 'clean', 'energy'];
      const actCx = (i) => +(AC.cx0 * 2 + AC.dx * 2 * i).toFixed(1);
      const d30 = AC.d * 2;
      let css = `
${H}{ font-family:${F10}; ${PX} }
${H}.panel { ${bi('panel_navy_flat')} }
/* ── 頂旗 banner_top（y −5，全闊）＋頭像 ── */
${H}#hdBan2 { display:block; position:absolute; left:${a2(L.banner.x)}px; top:${a2(L.banner.y)}px; width:${a2(L.banner.w)}px; height:${a2(L.banner.h)}px; ${bi('banner_top')} pointer-events:none; z-index:0; }
${H}#hdBan2 > i { position:absolute; display:block; }
${H}#hdBan2 > i.rv { ${sp('rivet')} margin:-3px 0 0 -3px; } ${H}#hdBan2 > i.gm { ${sp('gem_pri_7')} margin:-7px 0 0 -7px; }
#hdBan2 { display:none; }
${H}#hud { z-index:3; }
${H}#chip { left:0 !important; top:0 !important; width:0 !important; height:0 !important; padding:0; border-image:none !important; background:none !important; overflow:visible; }
${H}#chip .hdFace { display:none !important; }
#chip .hdFace2 { display:none; }
${H}#chip .hdFace2 { display:block; position:absolute; left:${a2(P.x)}px; top:${a2(P.y)}px; width:${a2(P.w)}px; height:${a2(P.h)}px; z-index:2; }
${H}#chip .hdFace2 canvas { position:absolute; left:0; top:0; width:${a2(P.w)}px; height:${a2(P.h)}px; image-rendering:pixelated; }
${H}#stagename { left:${a2(NP.name[0])}px; top:${a2(NP.name[1]) - 12}px; font:${a2(NP.nameSize)}px/24px ${F12} !important; letter-spacing:0; color:${CREAM}; ${OL} }
${H}#substage { left:var(--sub2L,180px) !important; top:${a2(NP.stage[1])}px; height:24px; max-width:var(--sub2W,100px) !important; padding:0 10px; font:var(--sub2F,20px)/24px ${F10} !important; color:${CREAM}; ${OL} ${bi('stage_tag')} }
${H}#prog { left:${a2(NP.xp[0])}px; top:${a2(NP.xp[1])}px; width:${a2(NP.xp[2])}px; height:${a2(NP.xp[3])}px; padding:4px 4px; box-sizing:border-box; ${bi('bar_trough_h5')} }
${H}#progf { height:2px; ${tile('bar_fill_gold_h5')} border-image:none !important; }
/* needs：2×2（x57 y22 dx41 dy10 w39）：mini icon＋bar_trough_h7＋bar_fill_<色>_h7（tile） */
${H}#needs { z-index:2; }
${H}.need { width:${a2(ND.w)}px; height:20px; border-image:none !important; background:none !important; }
${NEEDK.map((k, i) => { const p = needXY(i); return `${H}.need[data-need="${k}"] { left:${p.x}px !important; top:${p.y}px !important; } ${H}.need[data-need="${k}"] > i.i { ${icBg('mini_' + NEED[k][0])} } ${H}.need[data-need="${k}"] .fill { ${tile('bar_fill_' + NEED[k][1] + '_h7')} }`; }).join('\n')}
${H}.need > i.m { display:none !important; }
${H}.need > i.i { left:-2px; top:-2px; width:22px; height:22px; image-rendering:pixelated; }
${H}.need .track { left:22px; right:auto; top:2px; width:${a2(ND.w) - 22 - 8}px; height:6px; padding:4px; overflow:hidden; ${bi('bar_trough_h7')} }
${H}.need .fill { height:6px; border-image:none !important; }
${H}.need .fill.warn { ${tile('bar_fill_rose_h7')} }
${H}.need.hdLow .track { filter:brightness(1.15); }
/* chips（光點／星星）：chip 3h h13＋med13_navy＋icon；光點右端 chip_plus */
${H}#top-r { left:${a2(CH[0].x)}px !important; top:${a2(CH[0].y)}px !important; }
${H}#grains { width:${a2(CH[0].w)}px; height:26px; padding:0 22px 0 28px; font:20px/26px ${F10}; color:${GOLD}; ${OL} ${bi('chip')} }
${H}#grains::before { left:0; top:0; ${sp('med13_navy')} }
${H}#grains::after { content:''; position:absolute; left:5px; top:5px; ${ic('mini_light')} }
${H}#grains > i.pl { display:block; position:absolute; right:-9px; top:4px; ${sp('chip_plus')} pointer-events:none; }
#grains > i.pl { display:none; }
${H}#s12chip { left:${a2(CH[1].x)}px !important; top:${a2(CH[1].y)}px !important; width:${a2(CH[1].w)}px; height:26px; padding:0 12px 0 28px !important; font:20px/26px ${F10} !important; color:${GOLD} !important; ${OL} ${bi('chip')} }
${H}#s12chip::before { left:0; top:0; ${sp('med13_navy')} }
${H}#s12chip::after { content:''; position:absolute; left:5px; top:5px; ${ic('mini_star')} }
/* 右側 rail：card_sel 24×24＋16px icon（×2）＋ribbon_navy 字牌 */
${H}#s2kid, ${H}#s2house { width:48px !important; height:48px !important; transform:translate(-50%,-50%); ${bi('card_sel')} }
${H}#hdRail .ibtn:not(#s2house):not(#s2kid) { width:66px !important; height:66px !important; transform:translate(-50%,-50%); }
${H}#hdRail .ibtn:not(#s2house):not(#s2kid) > i.m { display:block !important; left:9px !important; top:9px !important; width:48px !important; height:48px !important; margin:0 !important; background:none !important; ${bi('card_sel')} }
${H}#diary { left:${RAIL.mail.x}px !important; top:${RAIL.mail.y}px !important; }
${H}#dex { left:${RAIL.dex.x}px !important; top:${RAIL.dex.y}px !important; }
${H}#s2kid { left:${RAIL.kid.x}px !important; top:${RAIL.kid.y}px !important; }
${H}#s2house { left:${RAIL.house.x}px !important; top:${RAIL.house.y}px !important; }
${H}#hdRail .ibtn > i.i { width:32px !important; height:32px !important; margin:-16px 0 0 -16px !important; image-rendering:pixelated; }
${H}#diary > i.i { ${icBg('mail')} } ${H}#dex > i.i { ${icBg('dex')} }
${H}#s2kid > i.i { border-radius:0 !important; width:36px !important; height:36px !important; margin:-18px 0 0 -18px !important; }
${H}#s2house > img { width:32px !important; height:32px !important; margin:-16px 0 0 -16px !important; opacity:0; }
${H}#s2house::after { content:''; position:absolute; left:8px; top:8px; ${ic('house')} pointer-events:none; }
${H}#s2house[data-locked="1"]::after { filter:grayscale(.6) brightness(.8); }
${H}#s2house[data-locked="1"]::before { content:''; position:absolute; right:-6px; bottom:-6px; ${ic('mini_lock')} pointer-events:none; z-index:2; }
${H}#hdRail .ibtn:not(#s2house):not(#s2kid) > i.l { top:calc(50% + 20px) !important; }
${H}#s2house > i.l, ${H}#s2kid > i.l { top:calc(100% - 4px) !important; }
${H}#hdRail .ibtn > i.l, ${H}#s2house > i.l, ${H}#s2kid > i.l { height:28px; padding:0 8px; box-sizing:border-box; font:16px/28px ${F8} !important; color:${CREAM}; ${OL8} ${bi('ribbon_navy')} }
${H}#diaryN { left:auto !important; right:1px; top:1px !important; width:22px; height:22px; font:16px/22px ${F8} !important; ${sp('red_dot_num')} ${OL8} }
${H}#s2house .rd, ${H}#s2kid .rd { left:auto !important; right:-6px; top:-6px !important; border:0 !important; border-radius:0 !important; ${sp('red_dot')} }
/* 委託（gift，s12chip .q）＝rail 第一格 */
${H}#s12chip .q { left:${RAIL.gift.x - 24 - a2(CH[1].x)}px !important; top:${RAIL.gift.y - 24 - a2(CH[1].y)}px !important; width:48px; height:48px; padding-top:48px; font:16px/28px ${F8} !important; ${OL8} ${bi('card_sel')} }
${H}#s12chip .q::before { left:8px; top:8px; ${ic('gift')} }
${H}#s12chip.hdDone .q::before { ${icBg('check')} }
${H}#s12chip .q { color:transparent !important; text-shadow:none !important; font-size:0 !important; }
${H}#s12chip > i.hd2gl { position:absolute; left:${RAIL.gift.x - a2(CH[1].x)}px; top:${RAIL.gift.y + 20 - a2(CH[1].y)}px; transform:translateX(-50%); height:28px; padding:0 8px; box-sizing:border-box; white-space:nowrap; font:16px/28px ${F8}; color:${CREAM}; ${OL8} ${bi('ribbon_navy')} pointer-events:none; }
body:not(.uiv2) .uiv2Font { display:none !important; }
#ui:not(.v2) #s12chip > i.hd2gl, #ui.hd.hdPage #s12chip > i.hd2gl { display:none !important; }
/* 信件同屋仔距離得 12px，信件唔出字牌（layout：mail 只有 dot） */
${H}#diary > i.l { display:none !important; }
${H}#s12chip .q[data-n]:not([data-n="0"])::after { right:-8px; top:-8px; width:22px; height:22px; font:16px/22px ${F8} !important; ${sp('red_dot_num')} ${OL8} }
/* ── 動作勳章（cy357 d30 間距 47.7＋ribbon y375 w32）── */
${H}.abtn { top:${a2(AC.cy) - d30 / 2}px; width:64px; height:94px; margin:0 0 0 -32px; }
${Object.keys(ACT).map((id, i) => `${H}#${id} { left:${actCx(i)}px; } ${H}#${id} > i.m { ${spBg('med30_' + ACT[id][1])} } ${H}#${id}:active > i.m, ${H}#${id}.hdDn > i.m { ${spBg('med30_' + ACT[id][1] + '_p')} } ${H}#${id} > i.i { ${icBg(ACT[id][0])} } ${H}#${id} .hdl { ${bi('ribbon_' + ACT[id][1])} }`).join('\n')}
${H}#btn-sleep.hdLight > i.i { ${icBg('light')} }
${H}.abtn > i.m { left:2px; top:0; width:${d30}px; height:${d30}px; image-rendering:pixelated; }
${H}.abtn > i.i { left:16px; top:14px; width:32px; height:32px; image-rendering:pixelated; }
${H}.abtn .hdl { left:0; top:${a2(AC.ribbonY) - (a2(AC.cy) - d30 / 2) - 14}px; width:${a2(AC.ribbonW)}px; height:28px; font:20px/28px ${F10} !important; color:${CREAM}; ${OL} }
${H}.abtn.dis > i.m { ${spBg('med30_dis')} } ${H}.abtn.dis .hdl { ${bi('ribbon_navy')} }
/* ── dock（x1 y385 193×37；選中 tab 升高＋dock_pillar 金框）── */
${H}#hdDock { left:${a2(DK.x)}px; top:${a2(DK.y)}px; width:${a2(DK.w)}px; height:${a2(DK.h)}px; ${bi('dock_bar')} }
${H}#hdDock .dv { display:none; }
${TABK.map((k, i) => `${H}#hdDock .hdTab[data-k="${k}"] { left:${(tabW * i).toFixed(1)}px !important; } ${H}#hdDock .hdTab[data-k="${k}"] > i.i { ${icBg(DK.tabs[i][0])} } ${H}#hdDock .hdTab[data-k="${k}"] > i.l::after { content:'${DK.tabs[i][1]}'; }`).join('\n')}
${H}#hdDock .hdTab { width:${tabW.toFixed(1)}px; height:${a2(DK.h)}px; }
${H}#hdDock .hdTab > i.p { left:calc(50% - 26px); top:-16px; width:52px; height:${a2(DK.h) + 12}px; transform:translateY(8px); ${bi('dock_pillar')} }
${H}#hdDock .hdTab.on > i.p { transform:none; }
${H}#hdDock .hdTab > i.m { left:calc(50% - 22px); top:2px; ${sp('med22_navy')} }
${H}#hdDock .hdTab.on > i.m { left:calc(50% - 28px); top:-14px; ${sp('med28_pri')} }
${H}#hdDock .hdTab > i.i { left:calc(50% - 16px); top:8px; width:32px; height:32px; image-rendering:pixelated; }
${H}#hdDock .hdTab.on > i.i { left:calc(50% - 16px); top:-2px; }
${H}#hdDock .hdTab > i.l { left:0 !important; right:0; top:46px !important; width:auto !important; height:24px !important; background:none !important; border-image:none !important; text-align:center; font:20px/24px ${F10}; color:${CREAM}; ${OL} }
${H}#hdDock .hdTab.on > i.l { color:${GOLD}; }
/* ── 泡泡／toast ── */
${H}#bubble { height:auto; min-height:36px; max-width:320px; padding:8px 12px; box-sizing:border-box; font:16px/20px ${F8} !important; color:${INK}; ${NOL} white-space:normal; ${bi('bubble')} }
${H}#bubble::after { bottom:-10px !important; margin-left:-5px !important; ${sp('bubble_tail')} }
${H}#toast { left:${a2(TO.x + TO.w / 2)}px; top:${a2(TO.y)}px; min-width:${a2(TO.w)}px; max-width:340px; height:${a2(TO.h)}px; padding:0 22px 0 30px; font:20px/${a2(TO.h)}px ${F10} !important; color:${CREAM}; ${OL} ${bi('toast')} }
${H}#toast.sm2 { height:auto !important; min-height:${a2(TO.h)}px; width:max-content; max-width:300px; padding:3px 14px 3px 30px; white-space:normal !important; font:24px/28px ${F12} !important; text-align:left; ${OL8} ${bi('panel_navy_flat')} }   /* 5a.1：太長唔縮字 → 換行，轉 9-slice */
${H}#toast::before { left:4px; top:4px; ${sp('med13_pri')} }
${H}#toast::after { left:9px; top:9px; ${ic('mini_heart')} }
${H}#toast.cur::after { ${icBg('mini_light')} } ${H}#toast.star::after { ${icBg('mini_star')} } ${H}#toast.night::after { ${icBg('mini_sleep')} }
${H}#s12gain { top:${a2(TO.y) + 40}px !important; height:${a2(TO.h)}px; font:20px/${a2(TO.h)}px ${F10} !important; ${OL} ${bi('toast')} }
${H}#s12gain::before { left:8px; top:9px; ${ic('mini_star')} }
${H}#evcard { ${bi('panel_navy')} font-family:${F8}; }
${H}#s12voice { font:16px/20px ${F8} !important; ${NOL} ${bi('bubble')} }
/* ── popup（闊 171 x12；標題 plaque 坐框頂；veil＝fx_veil_tile 棋盤，冇 alpha）── */
${H}#modal { background:none !important; ${tile('fx_veil_tile')} }
${H}#mbox { width:${a2(PU.w)}px; max-width:${a2(PU.w)}px; margin-top:26px; padding:${a2(PU.titleH) + 12}px 18px 18px; font:16px/22px ${F8}; color:${CREAM}; ${bi('panel_navy')} }
${H}#mbox > h2 { top:-${a2(PU.titleH) / 2}px; height:${a2(PU.titleH)}px; padding:0 18px; font:24px/${a2(PU.titleH)}px ${F12} !important; letter-spacing:0; color:${CREAM}; ${OL} ${bi('plaque')} overflow:visible; }
${H}#mbox > h2::before, ${H}#mbox > h2::after { content:''; position:absolute; top:4px; ${sp('plaque_tail_l')} }
${H}#mbox > h2::before { left:-14px; } ${H}#mbox > h2::after { right:-14px; ${spBg('plaque_tail_r')} }
${H}#mbox > p { font:20px/26px ${F10}; color:${CREAM}; ${OL} margin:6px 0; }
${H}#mbox small, ${H}#mbox .row, ${H}#mbox div { font-family:${F8}; }
${H}#mbox .row:has(> .btn), ${H}#mbox .row:has(> .seg) { min-height:48px; padding:4px 12px; font-size:16px; ${bi('panel_inset')} }
${H}.btn { height:40px; min-width:92px; padding:0 18px; box-sizing:border-box; font:20px/40px ${F10} !important; color:${CREAM} !important; ${OL} ${bi('btn_pri')} background:none !important; border-radius:0 !important; box-shadow:none !important; }
${H}.btn:active, ${H}.btn.hdDn { ${bi('btn_pri_p')} }
${H}.btn.sec { ${bi('btn_sec')} } ${H}.btn.sec:active, ${H}.btn.sec.hdDn { ${bi('btn_sec_p')} }
${H}.btn.sec[data-testid="reset-save"] { ${bi('btn_rose')} } ${H}.btn.sec[data-testid="reset-save"]:active { ${bi('btn_rose_p')} }
${H}.btn[disabled], ${H}.btn.dis, ${H}.btn.off { color:#C9C3D6 !important; ${bi('btn_dis')} }
${H}.seg { height:28px; padding:0 4px; ${bi('seg_bg')} }
${H}.seg .btn { height:20px; min-width:0; padding:0 8px !important; font:16px/20px ${F8} !important; color:${CREAM} !important; ${NOL} border-image:none !important; }
${H}.seg .btn.on { color:#4A2410 !important; ${bi('seg_on')} }
${H}.seg { height:40px !important; width:auto !important; max-width:none !important; padding:0 6px !important; flex:none; ${bi('panel_inset')} }
${H}.seg .btn { height:32px !important; flex:none !important; margin:0 2px !important; padding:0 10px !important; line-height:32px !important; ${OL8} }
${H}.seg .btn.on { color:${CREAM} !important; ${OL8} ${bi('btn16_pri')} }
${H}.hdTg { width:44px !important; height:22px !important; ${spBg('toggle_track_on')} }
${H}.hdTg.sec { ${spBg('toggle_track_off')} }
${H}.hdTg::after { top:0; left:22px; ${sp('toggle_knob_on')} }
${H}.hdTg.sec::after { left:0; ${spBg('toggle_knob_off')} }
${H}#pop { ${bi('panel_navy')} }
${H}#pop .pitem { font:20px/26px ${F10}; ${OL} ${bi('panel_inset')} }
${H}#pop .pitem small { font:16px/20px ${F8}; ${NOL} }
${H}#pop .pitem:active, ${H}#pop .pitem.hdDn { ${bi('panel_inset_sel')} }
${H}.dexCell { font-family:${F8}; ${bi('card_locked')} }
/* 圖鑑：成個塞得落一版（v1 一樣）→ 行距收細 */
${H}#mbox[data-kind="dex"] { margin-top:10px; padding-bottom:12px; font:16px/18px ${F8}; }
${H}#mbox[data-kind="dex"] .dexGrid { gap:4px; margin:2px 0; }
${H}#mbox[data-kind="dex"] .dexCell, ${H}#mbox[data-kind="dex"] .dexCell * { line-height:16px !important; }
${H}#mbox[data-kind="dex"] .dexGrid > :not(.dexCell), ${H}#mbox[data-kind="dex"] .dexGrid > :not(.dexCell) * { line-height:18px !important; }
${H}.dexCell.on { ${bi('card')} }
/* 細佬卡（s2Card）／設定版本行 */
${H}#mbox[data-kind="s2Card"] img { image-rendering:pixelated; }
${H}[data-testid="s2-version"], ${H}[data-testid="dev-version"] { font:16px/20px ${F8} !important; color:${GOLD}; }
${H}#mbox .uiv2Font { font:16px/20px ${F8}; opacity:.9; text-align:center; margin-top:8px; }
/* ── §7 小委託／手帳頁 ── */
${H}#s12p { background:none !important; ${tile('fx_veil_tile')} }
${H}#s12box { font-family:${F8}; ${bi('panel_navy')} }
${H}#s12box > h3 { height:${a2(PU.titleH)}px; padding:0 18px; font:24px/${a2(PU.titleH)}px ${F12} !important; letter-spacing:0; ${OL} ${bi('plaque')} }
${H}.s12tabs b { height:30px; padding:0 10px !important; font:16px/30px ${F8} !important; ${OL8} ${bi('subtab')} }
${H}.s12tabs b.on { ${bi('subtab_on')} }
${H}.s12row { font-size:16px; ${bi('panel_inset')} }
${H}.s12row[data-done="1"], ${H}.s12row.done { ${bi('panel_inset_sel')} }
${H}.s12q > img:last-child { content:url(${url('check_on')}); width:22px !important; height:22px !important; image-rendering:pixelated; }
${H}.s12page { ${bi('panel_paper')} }
${H}.s12x::before { left:7px; top:7px; ${sp('close')} }
${H}.s12x:active::before { ${spBg('close_p')} }
${H}.s12b-btn { font-family:${F8} !important; }
${H}.s12b-btn::before { top:calc(50% - 16px); height:32px; ${bi('btn16_pri')} }
${H}.s12b-btn.off::before { ${bi('btn16_dis')} }
${H}.s12bar { height:14px !important; padding:4px; box-sizing:border-box; ${bi('bar_trough_h7')} }
${H}.s12bar > i { height:6px !important; ${tile('bar_fill_gold_h7')} border-image:none !important; }
/* ── fx ── */
${H}#hdVeil .v { ${spBg('fx_ripple')} background-size:100% 100% !important; }
${H}#hdFx .sp { ${spBg('sparkle_7')} background-size:100% 100% !important; }
${H}#hdFx .stamp { ${spBg('stamp_done')} background-size:100% 100% !important; }
${H}#hdFx .stamp::after { ${icBg('check')} }
${H}#hdFx > .ghost:not([data-hd-of]) { ${bi('panel_navy')} }
/* ── 🛠 開發者掣＋面板 ── */
${H}#devBtn { top:${a2(P.y + P.h) + 8}px !important; height:22px; padding:0 10px !important; box-sizing:border-box; border:0 !important; border-radius:0 !important; background:none !important; font:16px/22px ${F8} !important; color:${CREAM} !important; ${OL8} ${bi('pill_navy')} }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] { border:0 !important; border-radius:0 !important; background:none !important; padding:10px !important; ${bi('panel_inset')} }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] b { font:20px/24px ${F10}; color:${GOLD}; ${OL} }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-status-"] { font:16px/20px ${F8} !important; }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn, ${H}#mbox[data-kind="devmode"] [data-testid="dev-toggle-btn"] { height:32px !important; min-width:0; padding:0 6px !important; font:16px/32px ${F8} !important; ${OL8} white-space:nowrap; overflow:hidden; ${bi('btn16_pri')} }
${H}#mbox .btn[data-tall="1"], ${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn[data-tall="1"] { height:auto !important; min-height:44px; padding:6px 14px !important; line-height:28px !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; ${bi('card_sel')} }
${H}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn:active { ${bi('btn16_pri_p')} }
${H}#mbox[data-kind="devmode"] [data-testid="dev-toggle-btn"] { ${bi('btn16_sec')} }
${H}#mbox[data-kind="devmode"] [data-testid="dev-sec-uiv2"] .btn[data-on="1"] { ${bi('btn16_violet')} }
/* ── 4b 屋仔（house4b：back／title／decorate／sheet／tabs／cards／done）── */
${H}#s2houseV .hb > img { opacity:0 !important; }
${H}#s2houseV [data-testid="house-back"], ${H}#s2houseV [data-testid="house-deco-back"] { left:${a2(HB.back[0] - HB.back[2] / 2)}px !important; top:${a2(HB.back[1] - HB.back[2] / 2)}px !important; ${sp('med22_navy')} }
${H}#s2houseV [data-testid="house-back"]::after, ${H}#s2houseV [data-testid="house-deco-back"]::after { content:''; position:absolute; left:6px; top:6px; ${ic('back')} }
${H}#s2houseV .ttl { left:${a2(HB.title[0] - HB.title[2] / 2)}px !important; top:${a2(HB.title[1]) - 14}px !important; width:${a2(HB.title[2])}px !important; height:28px; border:0; border-radius:0; box-shadow:none; background:none; font:20px/28px ${F10}; letter-spacing:0; ${OL} ${bi('ribbon_navy')} }
${H}#s2houseV [data-testid="house-decorate"] { left:${a2(HB.decorate[0] - HB.decorate[2] / 2)}px !important; top:${a2(HB.decorate[1] - HB.decorate[2] / 2)}px !important; ${sp('med30_violet')} }
${H}#s2houseV [data-testid="house-decorate"]:active { ${spBg('med30_violet_p')} }
${H}#s2houseV [data-testid="house-decorate"]::after { content:''; position:absolute; left:14px; top:14px; ${ic('decorate')} }
${H}#s2houseV [data-testid="house-sheet"] { left:${a2(HB.sheet[0])}px !important; top:${a2(HB.sheet[1])}px !important; width:${a2(HB.sheet[2])}px !important; height:${a2(HB.sheet[3])}px !important; ${bi('panel_navy')} }
${H}#s2houseV [data-testid="house-sheet"]::after { content:''; position:absolute; left:calc(50% - 24px); top:2px; ${sp('sheet_handle')} }
${H}#s2houseV [data-testid="house-sheet"] > img { display:none !important; }
${(NS.long5a ? ['bed', 'table', 'wall', 'rug', 'window', 'lamp', 'deco'] : ['bed', 'table', 'wall', 'rug', 'window', 'lamp']).map((k, i, L7) => `${H}#s2houseV [data-testid="house-tab-${k}"] { left:${a2(HB.sheet[0] + HB.sheet[2] / 2 + (L7.length > 6 ? (i - 3) * 26 : (i - 2.5) * 30)) - 22}px !important; top:${a2(HB.tabsCy) - 22}px !important; ${sp('med22_navy')} } ${H}#s2houseV [data-testid="house-tab-${k}"][data-sel="1"] { ${spBg('med22_pri')} } ${H}#s2houseV [data-testid="house-tab-${k}"]::after { content:''; position:absolute; left:6px; top:6px; ${ic(SLOT_IC[k])} }`).join('\n')}
${H}#s2houseV .hb[data-testid^="house-tab-"] .lbl { display:none; }
${H}#s2houseV [data-testid="house-tabtitle"] { left:${a2(HB.sheet[0]) + 14}px !important; top:${a2(HB.tabsCy) + 24}px !important; font:16px/20px ${F8} !important; color:${GOLD} !important; ${OL8} }
${H}#s2houseV [data-testid="house-tabtitle"] + div { top:${a2(HB.tabsCy) + 24}px !important; right:${390 - a2(HB.sheet[0] + HB.sheet[2]) + 14}px !important; font:16px/20px ${F8} !important; ${NOL} }
${HB.cards.map((c, i) => `${H}#s2houseV .card:nth-child(${i + 1}) { left:${a2(c[0])}px !important; top:${a2(c[1])}px !important; }`).join('\n')}
${H}#s2houseV .svrow { left:${a2(HB.cards[0][0])}px !important; top:${a2(HB.cards[0][1])}px !important; width:${a2(HB.cards[2][0] + HB.cardWH[0] - HB.cards[0][0])}px !important; height:${a2(HB.cardWH[1]) + 6}px !important; gap:${a2(HB.cards[1][0] - HB.cards[0][0] - HB.cardWH[0])}px !important; }
${H}#s2houseV .svrow .card.svc:nth-child(n) { position:relative !important; left:auto !important; top:auto !important; flex:0 0 auto; }
${H}#s2houseV .card { width:${a2(HB.cardWH[0])}px !important; height:${a2(HB.cardWH[1])}px !important; border:0; border-radius:0; box-shadow:none; background:none; ${bi('card')} }
${H}#s2houseV .card[data-state="equipped"] { ${bi('card_sel')} }
${H}#s2houseV .card[data-state="locked"] { ${bi('card_locked')} }
${H}#s2houseV .card > img { opacity:0 !important; }
${H}#s2houseV .card[data-state="locked"]::after { content:''; position:absolute; left:38px; top:24px; ${ic('lock')} }
${H}#s2houseV .card[data-clear]::after { content:''; position:absolute; left:38px; top:24px; ${ic('clear')} }
${H}#s2houseV .card > canvas { left:8px !important; top:8px !important; }
${H}#s2houseV .card .nm { top:76px; font:16px/20px ${F8}; ${NOL} }
${H}#s2houseV .card .pill { left:10px; right:10px; top:100px; height:22px; border:0; border-radius:0; background:none !important; font:16px/22px ${F8}; color:${CREAM}; ${OL8} ${bi('pill_pri')} }
${H}#s2houseV .card[data-state="equipped"] .pill { ${bi('pill_sec')} }
${H}#s2houseV .card[data-state="locked"] .pill { font-size:16px; ${bi('pill_dis')} }
${H}#s2houseV .card[data-clear] .pill { ${bi('pill_navy')} }
${H}#s2houseV .card .pill.poor { filter:none; ${bi('pill_dis')} }
${H}#s2houseV .gem { transform:none; border:0; background:none; ${sp('gem_rose_7')} }
${H}#s2houseV [data-testid="house-done"] { left:${a2(HB.done[0])}px !important; top:${a2(HB.done[1])}px !important; width:${a2(HB.done[2])}px !important; height:${a2(HB.done[3])}px !important; ${bi('btn16_pri')} }
${H}#s2houseV [data-testid="house-done"]::after { content:'完成'; position:absolute; inset:0; text-align:center; font:20px/32px ${F10}; color:${CREAM}; ${OL} }
${H}#s2houseV [data-testid="house-chip"] { height:26px !important; border:0 !important; border-radius:0 !important; background:none !important; padding-left:30px !important; font:20px/26px ${F10} !important; color:${GOLD} !important; ${OL} ${bi('chip')} }
${H}#s2houseV [data-testid="house-chip"] > span:first-child { left:0 !important; top:0 !important; font-size:0 !important; ${sp('med13_navy')} }
${H}#s2houseV [data-testid="house-chip"]::after { content:''; position:absolute; left:5px; top:5px; ${ic('mini_star')} }
${H}#s2houseV .hb[data-testid^="house-pin-"] > img { opacity:0 !important; }
${H}#s2houseV .hb[data-testid^="house-pin-"] { ${spBg('med24_navy')} background-size:100% 100% !important; }
${H}#s2houseV .hb[data-testid^="house-pin-"][data-sel="1"] { ${spBg('med24_pri')} background-size:100% 100% !important; }
${H}#s2houseV .hb[data-testid^="house-pin-"]::after { content:''; position:absolute; left:calc(50% - 11px); top:calc(50% - 11px); ${ic('mini_plus')} }
${H}#s2houseV .hb[data-testid^="house-pin-"][data-filled="1"]::after { ${icBg('mini_check')} }
${H}#s2houseV [data-testid="house-hint"] { font:16px/20px ${F8} !important; ${OL8} }
`;
      css = readable(css) + readCss(H, FALL, F12, OL8, INK, CREAM, LINE);
      const st = document.createElement('style'); st.id = 'hd2dui2-css'; st.textContent = css; document.head.appendChild(st); U.css = css;
      dom(); U.ready = true; U.readyAt = performance.now(); set(U.want, 'boot'); note('ready', { on: U.on });
      readInit();
      setInterval(tick, 400); tick();
    }

    function dom() {
      const hud = $('#hud'); if (hud && !$('#hdBan2')) { const b = document.createElement('div'); b.id = 'hdBan2'; b.dataset.testid = 'uiv2-banner'; hud.insertBefore(b, hud.firstChild);
        const B = U.layout.banner; B.rivets.forEach(([x, y]) => { const r = document.createElement('i'); r.className = 'rv'; r.style.left = Math.round((x - B.x) * 2) + 'px'; r.style.top = Math.round((y - B.y) * 2) + 'px'; b.appendChild(r); });
        const g = document.createElement('i'); g.className = 'gm'; g.style.left = Math.round((B.gem[0] - B.x) * 2) + 'px'; g.style.top = Math.round((B.gem[1] - B.y) * 2) + 'px'; b.appendChild(g); }
      const chip = $('#chip'); if (chip && !chip.querySelector('.hdFace2')) { const f = document.createElement('div'); f.className = 'hdFace2'; f.dataset.testid = 'uiv2-portrait'; const c = document.createElement('canvas'); c.width = U.layout.portrait.w; c.height = U.layout.portrait.h; f.appendChild(c); chip.insertBefore(f, chip.firstChild); U.face = c; }
      const sc = $('#s12chip'); if (sc && !sc.querySelector('.hd2gl')) { const l = document.createElement('i'); l.className = 'hd2gl'; l.textContent = '委託'; sc.appendChild(l); }
      const gr = $('#grains'); if (gr && !gr.querySelector('.pl')) { const p = document.createElement('i'); p.className = 'pl'; gr.appendChild(p); }
    }
    // ── 切換 v1／v2（即時；CSS 層開關，DOM／事件冇變）──
    function set(on, why) {
      on = !!on; U.want = on; if (!U.ready) return on;
      U.on = on; ui.classList.toggle('v2', on); document.body.classList.toggle('uiv2', on);
      if (why === 'dev' || why === 'qa') { try { localStorage.setItem(KEY, on ? '2' : '1'); } catch (e) { } }
      lastSub = ''; if (on) { face(true); tick(); } readPass(true);
      note('set', { on, why: why || '' }); return on;
    }
    U.set = set; U.toggle = (why) => set(!U.on, why || 'dev');
    // ── tick：名牌 stage tag 位、toast 字號、頭像 ──
    let lastSub = '', lastFace = -1e9, lastToast = '';
    function tick() {
      if (!U.on) return; U.tallPass();
      const nm = $('#stagename'), sb = $('#substage');
      if (nm && sb) { const k = nm.textContent + '|' + sb.textContent + '|' + (U.fonts.GlimmerFP12 ? 1 : 0); if (k !== lastSub) { lastSub = k; const Lx = 116 + nm.offsetWidth + 6, W = Math.max(40, 284 - Lx); sb.style.setProperty('--sub2L', Lx + 'px'); sb.style.setProperty('--sub2W', W + 'px'); sb.style.setProperty('--sub2F', '24px'); } }
      const t = $('#toast'); if (t) { const k = t.textContent; if (k !== lastToast) { lastToast = k; t.classList.remove('sm2'); if (t.scrollWidth > 338) t.classList.add('sm2'); } }
      const tn = performance.now(); if (tn - lastFace > 1000) { lastFace = tn; face(); }
    }
    // ── 頭像（PORTRAIT_SYNC）──
    function face(force) {
      const c = U.face, R = G.renderer, s = G.state; if (!c || !R || !R.atlasSrc || !s || !U.rects) return;
      try {
        let src = null, fk = 'egg';
        if (s.stage === 'egg') src = R.atlasSrc('atlas_evo_egg', 'egg_idle', 0) || R.atlasSrc('atlas_egg', 'egg_idle', 0);
        else if (s.fam && s.fam.km && R.s2MainFace && (src = R.s2MainFace())) fk = 'km:' + src.fk;   // 5a.1 細佬做主養
        else { fk = R.fkOf(s); const F = D.FORMS[fk]; if (F) src = R.atlasSrc(F.atlas, 'idle', 0); }
        const mood = U.moodOv || moodOf(s), sig = fk + '|' + mood + '|' + (U.accOv || '') + '|' + (src ? src.sx + ',' + src.sy : '-');
        if (!force && sig === U.faceSig) return; U.faceSig = sig;
        const x = c.getContext('2d'), W = c.width, Hh = c.height; x.imageSmoothingEnabled = false; x.clearRect(0, 0, W, Hh);
        const part = (g, n, dx, dy) => { const f = U.FR[n]; if (f) g.drawImage(PIMG(), f.x, f.y, f.w, f.h, dx, dy, f.w, f.h); };
        const lay = document.createElement('canvas'); lay.width = W; lay.height = Hh; const g = lay.getContext('2d'); g.imageSmoothingEnabled = false;
        part(g, 'portrait_bg_' + mood, 0, 0);
        let info = { fk, hit: false, rect: null, badge: false };
        if (src && src.img) {
          const pad = U.rects.pad || 8, rr = src.km ? { rect: [pad + 24 - 17, pad + src.headY - 5, 34], frame: 48, acc: {}, hit: true } : rectOf(U.rects, fk, Math.max(src.sw, src.sh)), fs = rr.frame || Math.max(src.sw, src.sh);
          const cv = document.createElement('canvas'); cv.width = fs + pad * 2; cv.height = fs + pad * 2; const q = cv.getContext('2d'); q.imageSmoothingEnabled = false;
          q.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, pad + Math.round((fs - src.sw) / 2), pad + (fs - src.sh), src.sw, src.sh);
          const ad = accAdj(rr.rect, U.accOv ? rr.acc[U.accOv] : null), [rx, ry, n] = ad.rect, win = U.layout.portrait.win;
          if (s.stage === 'egg') { const sc = Math.max(1, Math.floor(Math.min(win[2] / src.sw, win[3] / src.sh))); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, win[0] + Math.round((win[2] - src.sw * sc) / 2), win[1] + win[3] - src.sh * sc, src.sw * sc, src.sh * sc); }
          else g.drawImage(cv, rx, ry, n, n, win[0], win[1], win[2], win[3]);
          info = { fk, hit: rr.hit, rect: ad.rect, badge: ad.badge };
        }
        g.globalCompositeOperation = 'destination-in'; part(g, 'portrait_mask', 0, 0); g.globalCompositeOperation = 'source-over';
        x.drawImage(lay, 0, 0); part(x, 'portrait_frame', 0, 0);
        if (mood !== 'normal') { const f = U.FR['mood_badge_' + mood]; if (f) part(x, 'mood_badge_' + mood, W - f.w, Hh - f.h); }
        if (info.badge) { const m = U.FR.med13_paper, th = U.FR['acc_thumb_' + U.accOv]; if (m) part(x, 'med13_paper', W - m.w, 0); if (th) part(x, 'acc_thumb_' + U.accOv, W - 13 + Math.round((13 - th.w) / 2), Math.round((13 - th.h) / 2)); }
        U.faceInfo = Object.assign(info, { mood });
      } catch (e) { U.errors.push('face ' + (e && e.message || e)); }
    }
    const PIMG = () => U.atlasImg;

    // ── 5a.1 清晰度（Kurt：「d字完全睇唔清楚」）──
    //  ① 唔准細過 FP12：v2 CSS 入面 FP8／FP10 全部換 FP12，字號＝24px（FP12×2，整數倍）；line-height ≥ 28
    //  ② 其他模組 inline 細字（圖鑑／細佬卡／開發者／手帳／屋仔…）→ readPass 逐個 floor 到 24px
    //  ③ 子集冇嘅字 → 成句轉系統中文字型（data-fbk）；淺色字冇描邊 → 補 1 art px 深色描邊（data-rol）
    //  ④ 開發者「清晰字型（系統字）」：成個 UI 用系統字（localStorage glimmer.sysf）
    const SYSK = 'glimmer.sysf';
    try { U.sysf = localStorage.getItem(SYSK) === '1'; } catch (e) { U.sysf = false; }
    function sysFont(on) { U.sysf = !!on; ui.classList.toggle('sysf', U.sysf); try { localStorage.setItem(SYSK, U.sysf ? '1' : '0'); } catch (e) { } readPass(true); note('sysf', { on: U.sysf }); return U.sysf; }
    const SKIP = /[\s\u200b-\u200f\ufe00-\ufe0f\u2600-\u27bf\u2b00-\u2bff\u{1F000}-\u{1FFFF}]/u;
    const lum = (c) => { const m = String(c).match(/[\d.]+/g); if (!m) return 0; const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(+m[0]) + 0.7152 * f(+m[1]) + 0.0722 * f(+m[2]); };
    let rq = 0, rAll = true; const rSet = new Set();
    function readInit() {
      ui.classList.toggle('sysf', !!U.sysf);
      try { new MutationObserver((ms) => { if (!U.on) return; for (const m of ms) { const t = m.target.nodeType === 1 ? m.target : m.target.parentElement; if (t && !(m.type === 'attributes' && m.attributeName === 'style' && t.dataset.rf)) rSet.add(t); } if (!rq) rq = requestAnimationFrame(() => { rq = 0; readPass(false); }); })
        .observe(ui, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['class'] }); } catch (e) { }
      readPass(true);
    }
    function readEl(el) {
      if (!el || el.nodeType !== 1 || el.tagName === 'CANVAS' || el.tagName === 'STYLE' || el.tagName === 'SCRIPT') return;
      let txt = ''; for (const n of el.childNodes) if (n.nodeType === 3) txt += n.nodeValue;
      txt = txt.trim(); if (!txt) return;
      const cs = getComputedStyle(el), fs = parseFloat(cs.fontSize) || 0;
      if (fs > 0 && fs < 23.5) { el.style.setProperty('font-size', '24px', 'important'); el.dataset.rf = '1'; const lh = parseFloat(cs.lineHeight); if (!(lh >= 27)) el.style.setProperty('line-height', '28px', 'important'); if (cs.position === 'absolute' && txt.length <= 8) el.style.setProperty('white-space', 'nowrap'); }
      if (/GlimmerFP(8|10)\b/.test(cs.fontFamily)) { el.style.setProperty('font-family', cs.fontFamily.replace(/GlimmerFP(8|10)\b/g, 'GlimmerFP12'), 'important'); el.dataset.rf = '1'; }
      tallBtn(el);   // 長字掣：唔縮字，轉做 9-slice 卡（kit 3h 掣唔拉高）
      let miss = false; if (U.cov) for (const ch of txt) { if (SKIP.test(ch)) continue; if (!U.cov.has(ch.codePointAt(0))) { miss = true; break; } }
      if (miss) el.dataset.fbk = '1'; else if (el.dataset.fbk) delete el.dataset.fbk;
      if (lum(cs.color) > 0.35 && (!cs.textShadow || cs.textShadow === 'none')) el.dataset.rol = '1';
    }
    function tallBtn(el) {
      if (!el.classList.contains('btn') || el.classList.contains('hdTg') || el.closest('.seg') || !el.closest('#mbox')) return;
      const w = el.clientWidth; if (!w) { el._tk = ''; return; }                       // 未顯示（modal 未開）→ 下次 tick 再量
      const k = el.textContent + '|' + w; if (el._tk === k) return; el._tk = k;
      delete el.dataset.tall; const tops = new Set(); for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) { const rg = document.createRange(); rg.selectNodeContents(n); for (const r of rg.getClientRects()) if (r.width > 1) tops.add(Math.round(r.top)); } const over = tops.size > 1;   // 自然換咗行 ＝ 太長
      if (over) { el.dataset.tall = '1'; el._tk = el.textContent + '|' + el.clientWidth; }
    }
    U.tallPass = () => { if (U.on) document.querySelectorAll('#mbox .btn').forEach(tallBtn); };
    function readPass(all) {
      if (!U.on) return;
      const list = (all || rAll) ? [ui] : Array.from(rSet); rAll = false; rSet.clear();
      for (const r of list) { if (!r.isConnected) continue; readEl(r); const w = r.getElementsByTagName('*'); for (let i = 0; i < w.length; i++) readEl(w[i]); }
    }
    // ── 🛠 開發者模式「UI v2」──
    const UIm = () => NS.ui || {};
    const sample = () => { const U2 = UIm(); if (!U2.modal) return { ok: false, msg: '冇 modal' }; U2.modal({ title: '收到小禮物', kind: 'uiv2Sample', lines: ['鄰居松鼠送咗嘢俾團絨！', '附上一封信：「多謝你嘅花！」'], buttons: [{ text: '睇信' }, { text: '收下', primary: true }] }); return { ok: true, msg: '示範彈窗' }; };
    const DEV = { id: 'uiv2', title: 'UI v2（HD-2D kit v2）', order: 5,
      status: () => (U.on ? '而家：v2' : '而家：v1') + (U.ready ? '' : '（載入緊）'),
      items: [
        ['toggle', 'UI v1／v2 切換', () => { if (!U.ready) return { ok: false, msg: 'UI v2 載入緊' }; set(!U.on, 'dev'); return { ok: true, msg: U.on ? '用緊 UI v2' : '用緊 UI v1（kit_hd2d）' }; }],
        ['settings', '睇設定', () => { const g = document.getElementById('gear'); if (!g) return { ok: false, msg: '冇設定掣' }; g.click(); return { ok: true, msg: '設定' }; }],
        ['dex', '睇圖鑑', () => { if (!UIm().openDex) return { ok: false, msg: '冇圖鑑' }; UIm().openDex(); return { ok: true, msg: '圖鑑' }; }],
        ['journal', '睇手帳（委託）', () => { if (!G.s12open) return { ok: false, msg: '冇手帳' }; G.s12open('quest'); return { ok: true, msg: '手帳' }; }],
        ['garden', '睇小圃頁', () => { if (!G.s12open) return { ok: false, msg: '冇小圃' }; G.s12open('garden'); return { ok: true, msg: '小圃' }; }],
        ['feed', '睇餵食選單', () => { const b = document.getElementById('btn-feed'); if (!b) return { ok: false, msg: '冇餵食掣' }; b.click(); return { ok: true, msg: '餵食選單' }; }],
        ['popup', '睇示範彈窗', sample],
        ['toast', '睇 toast', () => { if (UIm().toast) UIm().toast('收到小禮物 +5', 2200); return { ok: true, msg: '收到小禮物 +5' }; }],
        ['kid', '睇細佬卡', () => { const q = window.__qa && window.__qa.s2; if (!q || !q.card) return { ok: false, msg: '冇細佬系統' }; q.card(); return { ok: true, msg: '細佬卡' }; }],
        ['house', '睇屋仔', () => { const q = window.__qa && window.__qa.house; if (!q) return { ok: false, msg: '冇屋仔' }; const r = q.open('dev'); return r ? { ok: true, msg: '屋仔' } : { ok: false, msg: '入唔到屋仔（細佬要先變家人：「家 4b」→ 準備）' }; }],
        ['deco', '睇佈置', () => { const q = window.__qa && window.__qa.house; if (!q) return { ok: false, msg: '冇屋仔' }; if (!q.st().open && !q.open('dev')) return { ok: false, msg: '入唔到屋仔（細佬要先變家人）' }; q.decorate(true); return { ok: true, msg: '佈置' }; }],
        ['mood', '頭像心情輪住睇', () => { const i = MOODS.indexOf(U.moodOv || moodOf(G.state)); U.moodOv = MOODS[(i + 1) % MOODS.length]; face(true); return { ok: true, msg: '頭像：' + U.moodOv + '（再撳「還原」跟返狀態）' }; }],
        ['sysf', '清晰字型（系統字）', () => { const v = sysFont(!U.sysf); return { ok: true, msg: v ? '清晰字型：開（系統中文字型）' : '清晰字型：關（像素字 FP12）' }; }],
        ['reset', '頭像還原', () => { U.moodOv = null; U.accOv = null; face(true); return { ok: true, msg: '頭像跟返團絨狀態' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);
    // 設定：字體授權行（UI_KIT_V2 settings mockup）— v2 先顯示
    const s2s = G.s2Settings; G.s2Settings = function (node) { const r = s2s ? s2s.apply(this, arguments) : undefined; try { const d = document.createElement('div'); d.className = 'uiv2Font'; d.dataset.testid = 'uiv2-font-credit'; d.textContent = '字型：Fusion Pixel（OFL 1.1）'; node.appendChild(d); } catch (e) { } return r; };

    window.__qa = window.__qa || {};
    window.__qa.uiv2 = {
      st: () => ({ ready: U.ready, on: U.on, want: U.want, forced: U.forced, errors: U.errors.slice(), missing: U.missing.slice(), fonts: Object.assign({}, U.fonts), face: U.faceInfo || null, moodOv: U.moodOv, rail: U.rail, log: U.log.slice(-10) }),
      set: (v) => set(v, 'qa'), toggle: () => U.toggle('qa'), face: () => { face(true); return U.faceInfo; }, mood: (m) => { U.moodOv = m || null; face(true); return U.faceInfo; }, acc: (k) => { U.accOv = k || null; face(true); return U.faceInfo; },
      sysFont: (v) => sysFont(v === undefined ? !U.sysf : !!v), read: () => { readPass(true); return { sysf: !!U.sysf, cov: U.cov ? U.cov.size : 0, fbk: document.querySelectorAll('#ui [data-fbk="1"]').length, floor: document.querySelectorAll('#ui [data-rf]').length }; },
      layout: () => U.layout, sample, part: (n) => U.FR && U.FR[n] ? Object.assign({}, U.FR[n]) : null,
    };
    note('install', { want: U.want });
    return true;
  }
  return { install, pref, moodOf, rectOf, accAdj, biCss, KEY };
});
