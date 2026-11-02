/* 《微光小圃》 uiv3.js — #83 UI kit V3 換皮（遊美 ui/kit_hd2d_v3：UI_KIT_V3.md）。原創代碼。
   做法：hd2dui2（v2 換膚層）照舊出 layout／DOM／6b.3 縮細＋收埋；V3 開 → 每個 v2 零件經 atlas/v2_to_v3_map.json 換做 V3 @3x 零件：
     9／3-slice → border-image（slice＝nine @3x，闊度 ×2/3 CSS；stretch），sprite／icon → 原 v2 框內 contain（@3x 圖，smooth；icon 冇 @2x）；
     絲帶／牌匾 → V3 金線（title_rule）放底；字 → Noto Sans／Serif CJK TC（OFL subset），陰影用 blur（冇描邊）；磨砂 → 開面板嗰刻預烘一張模糊場景圖（唔用 backdrop-filter）。
   字最細 18@3x（＝12 CSS @390）；掣 ≥48 照 6b.3 hit area。v1 凍結；?v3=0 → 6b.3 樣。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.uiv3 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const K = 2 / 3;                                  // @3x px → CSS px（585 → 390）
  const C = { ink: [36, 34, 52], cream: [250, 244, 230], mute: [206, 212, 230], gold: [232, 200, 128], goldhi: [255, 236, 184], golddk: [66, 40, 4], navy: [18, 24, 48], navy2: [30, 40, 74], navy3: [44, 58, 104], amber: [246, 176, 72], sky: [110, 190, 230], rose: [240, 126, 150], violet: [156, 132, 230], mint: [120, 206, 160], red: [214, 62, 72], dis: [84, 88, 108] };
  const TYPE = { title: { f: 'serif', px3x: 30 }, h2: { f: 'sansb', px3x: 24 }, body: { f: 'sans', px3x: 21 }, value: { f: 'sansb', px3x: 21 }, button: { f: 'sansb', px3x: 20 }, label: { f: 'sansb', px3x: 18 }, caption: { f: 'sans', px3x: 18 } };
  const MIN3X = 18;
  const rgb = (c, a) => a == null ? 'rgb(' + c.join(',') + ')' : 'rgba(' + c.join(',') + ',' + a + ')';
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  /* 字色：彩色掣用 ink、dis 用 cream；其他按底色揀對比高嗰個 */
  function textOn(fill, name) { if (/_dis(_p)?$/.test(name || '')) return 'cream'; if (!fill) return 'cream'; return cr(fill, C.ink) >= cr(fill, C.cream) ? 'ink' : 'cream'; }
  function v3name(map, FR3, IC3, n, icon) {
    const m = map[n]; if (m && m.v3) { if (/^icon:/.test(m.v3)) return IC3[m.v3.slice(5)] ? 'icon:' + m.v3.slice(5) : null; return FR3[m.v3] ? m.v3 : (IC3[m.v3] ? 'icon:' + m.v3 : null); }
    if (icon) return IC3[n] ? 'icon:' + n : null; return FR3[n] ? n : null;
  }
  function prep(G, NS) {
    const B = ((NS.data.PARAMS.art && NS.data.PARAMS.art.base) || 'art/') + 'v3/ui/';
    const img = (u) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('img ' + u)); i.src = u; });
    const js = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const fonts = {}, errs = [];
    const font = (file, fam, w) => fetch(B + 'fonts/' + file).then(r => r.arrayBuffer()).then(b => new FontFace(fam, b, { weight: w, ascentOverride: '88%', descentOverride: '12%', lineGapOverride: '0%' })   /* Noto CJK 字框 1em（subset hhea 偏大 → 文字框高過掣） */.load()).then(f => { document.fonts.add(f); fonts[fam + ':' + w] = true; }).catch(e => { errs.push('font ' + file + ': ' + (e && e.message)); });
    return Promise.all([js(B + 'atlas/ui_hd2d_v3@3x.json'), img(B + 'atlas/ui_hd2d_v3@3x.png'), js(B + 'atlas/icons_hd2d_v3@3x.json'), img(B + 'atlas/icons_hd2d_v3@3x.png'), js(B + 'atlas/v2_to_v3_map.json'), js(B + 'layout_hd2d_v3.json'),
      font('NotoSansCJKtc-Regular.subset.otf', 'GlimmerV3Sans', '400'), font('NotoSansCJKtc-Bold.subset.otf', 'GlimmerV3Sans', '700'), font('NotoSerifCJKtc-Bold.subset.otf', 'GlimmerV3Serif', '700')])
      .then(([aj, ai, ij, ii, mp, lay]) => ({ aj, ai, ij, ii, map: mp.map || {}, layout: lay, fonts, errs }))
      .catch(e => { errs.push(String(e && e.message || e)); return null; });
  }
  function make(d, U) {
    const FR3 = d.aj.frames, IC3 = d.ij.frames, cache = {}, used = new Set(), miss = new Set();
    const crop = (im, f) => { const c = document.createElement('canvas'); c.width = f.w; c.height = f.h; c.getContext('2d').drawImage(im, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h); return c.toDataURL(); };
    const nm = (n, icon) => { const k = (icon ? 'i:' : 'p:') + n; if (k in cache) return cache[k]; const v = v3name(d.map, FR3, IC3, n, icon); if (!v) miss.add(n); return (cache[k] = v); };
    const src = (v) => { if (cache['u:' + v]) return cache['u:' + v]; const ic = /^icon:/.test(v), f = ic ? IC3[v.slice(5)] : FR3[v]; used.add(v); return (cache['u:' + v] = crop(ic ? d.ii : d.ai, f)); };
    const frame = (v) => /^icon:/.test(v) ? IC3[v.slice(5)] : FR3[v];
    let AG = null; const fillOf = (v) => { const k = 'f:' + v; if (k in cache) return cache[k]; const f = frame(v); let c = null;
      try { if (!AG) { const cv = document.createElement('canvas'); cv.width = d.ai.width; cv.height = d.ai.height; AG = cv.getContext('2d', { willReadFrequently: true }); AG.drawImage(d.ai, 0, 0); }
        if (f && !/^icon:/.test(v)) { const px = AG.getImageData(f.x + (f.w >> 1), f.y + (f.h >> 1), 1, 1).data; if (px[3] > 128) c = [px[0], px[1], px[2]]; } } catch (e) { }
      return (cache[k] = c); };
    const RULE = (v) => v === 'title_rule';
    const X = {
      shadow: `text-shadow:0 1px 2px ${rgb(C.navy, 0.95)}, 0 0 5px ${rgb(C.navy, 0.75)} !important;`,
      d, used, miss, fillOf, textOn: (n) => { const v = nm(n); return v ? textOn(fillOf(v), v) : 'cream'; },
      has: (n, icon) => !!nm(n, icon),
      url: (n) => { const v = nm(n); return v ? src(v) : ''; }, iurl: (n) => { const v = nm(n, true); return v ? src(v) : ''; },
      bi(n) {
        const v = nm(n); if (!v) return ''; const f = frame(v), u = src(v);
        if (RULE(v)) return `border-image:none !important; background:url(${u}) center bottom / 100% ${Math.round(f.h * K)}px no-repeat, linear-gradient(90deg, ${rgb(C.navy, 0)} 0, ${rgb(C.navy, 0.86)} 10%, ${rgb(C.navy, 0.86)} 90%, ${rgb(C.navy, 0)} 100%) !important; border-radius:6px;`;   /* 金線＋底板：標題跨面板邊都有 ≥4.5 */
        if (!f.nine) return `border-image:none !important; background:url(${u}) center / 100% 100% no-repeat !important; image-rendering:auto;`;
        const [l, t, r, b] = f.nine, w = (x) => +(x * K).toFixed(2);
        const tc = X.textOn(n), col = tc === 'ink' ? ` color:${rgb(C.ink)} !important; text-shadow:none !important;` : '';
        return `border-style:solid !important; border-color:transparent !important; border-width:0 !important; border-image:url(${u}) ${t} ${r} ${b} ${l} fill / ${w(t)}px ${w(r)}px ${w(b)}px ${w(l)}px / 0 stretch !important; image-rendering:auto;` + col;
      },
      sp(n, f2, icon) { const v = nm(n, icon); if (!v) return ''; const u = src(v), w = f2 ? f2.w * 2 : Math.round(frame(v).w * K), h = f2 ? f2.h * 2 : Math.round(frame(v).h * K);
        const imp = icon ? '' : ' !important'; return `width:${w}px${imp}; height:${h}px${imp}; background:url(${u}) center / contain no-repeat !important; border:0 !important; border-image:none !important; image-rendering:auto;`; },
      spBg(n, icon) { const v = nm(n, icon); if (!v) return ''; return `background:url(${src(v)}) center / contain no-repeat !important; border-image:none !important; image-rendering:auto;`; },
      tile(n) { const v = nm(n); if (!v) return ''; const f = frame(v), u = src(v);
        if (f.nine) { const [l, t, r, b] = f.nine; return `background:none !important; border-style:solid !important; border-width:0 !important; border-image:url(${u}) ${t} ${r} ${b} ${l} fill / ${(t * K).toFixed(2)}px ${(r * K).toFixed(2)}px ${(b * K).toFixed(2)}px ${(l * K).toFixed(2)}px / 0 stretch !important; image-rendering:auto;`; }
        return `background:url(${u}) 0 0 / ${Math.round(f.w * K)}px ${Math.round(f.h * K)}px repeat !important; image-rendering:auto;`; },
      css(H) {
        const S = '#ui.hd.v2.v3', A = S + ' ', SANS = '"GlimmerV3Sans","Noto Sans CJK TC","Noto Sans HK","PingFang HK",sans-serif', SERIF = '"GlimmerV3Serif","Noto Serif CJK TC",' + SANS;
        const SH = `0 1px 2px ${rgb(C.navy, 0.95)}, 0 0 5px ${rgb(C.navy, 0.75)}`;
        return `
/* ── #83 UI kit V3（uiv3.js）── */
${S}, ${A}* { font-family:${SANS} !important; -webkit-font-smoothing:antialiased !important; font-kerning:normal !important; }
#ui.hd.v2.v3:not(.sysf) :is([data-fbk="1"], #_z#_z#_z) { font-family:${SANS} !important; }   /* Noto CJK TC subset＋系統 Noto 逐字補，唔使成句轉系統字（系統字設定照贏） */
${A}h1, ${A}h2, ${A}.hdl, ${A}#stagename, ${A}[data-r62="t"], ${A}.u62title { font-family:${SERIF} !important; font-weight:700 !important; letter-spacing:1px !important; }
${A}b, ${A}strong, ${A}.btn, ${A}.abtn, ${A}.ibtn, ${A}[data-r62="v"] { font-weight:700; }
${A}.panel, ${A}#mbox, ${A}#s12p .s12in, ${A}.u62panel { -webkit-backdrop-filter:none !important; backdrop-filter:none !important; }
${A}#mbox h2, ${A}.u62title { color:${rgb(C.goldhi)} !important; }
${A}#mbox, ${A}#mbox p, ${A}#mbox li, ${A}#mbox div { color:${rgb(C.cream)}; }
${A}.u62sub, ${A}[data-r62="a"] { color:${rgb(C.mute)} !important; }
${A}#modal.v3frost::before { content:''; position:absolute; inset:0; background:var(--v3frost) center / cover no-repeat; opacity:.9; pointer-events:none; z-index:-1; }
${A}#mbox[data-kind="devmode"] [data-testid^="dev-sec-"] .btn { height:auto !important; min-height:52px !important; display:flex !important; align-items:center; justify-content:center; white-space:normal !important; overflow-wrap:anywhere; text-align:center !important; line-height:1.25 !important; padding:6px 20px !important; text-overflow:clip !important; overflow:visible !important; }   /* V3：掣 ≥48（360 寬面板縮 .92 都夠）；長字換行唔出界 */
${A}#mbox .btn[data-tall="1"] { color:${rgb(C.cream)} !important; text-shadow:${SH} !important; }   /* 長字掣轉深色卡（card_sel）→ cream 字 */
${A}.seg .btn { height:34px !important; line-height:34px !important; }   /* 揀咗嘅金膠囊包住成個字框（系統字 Noto Sans HK 字框高） */
${A}.hdTg { color:${rgb(C.cream)} !important; text-shadow:${SH} !important; }   /* 開／關 字喺掣外（text-indent），唔跟彩色軌用 ink */
${A}.v3ink, ${A}.v3ink * { color:${rgb(C.ink)} !important; text-shadow:none !important; }
`;
      },
    };
    return X;
  }
  /* 磨砂：開面板嗰刻將遊戲畫面縮細再放大（一次過「預烘」），唔係每幀 backdrop-filter */
  function frost(canvas) {
    try { const s = document.createElement('canvas'); s.width = 49; s.height = 106; const g = s.getContext('2d'); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; g.drawImage(canvas, 0, 0, s.width, s.height);
      g.fillStyle = rgb(C.navy, 0.35); g.fillRect(0, 0, s.width, s.height); return s.toDataURL('image/png'); } catch (e) { return ''; }
  }
  return { K, C, TYPE, MIN3X, cr, textOn, v3name, prep, make, frost };
});
