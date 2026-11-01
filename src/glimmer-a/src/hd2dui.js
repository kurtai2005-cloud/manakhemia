/* 《微光小圃》 hd2dui.js — HD-2D UI 換膚（遊美 art/ui-kit-hd2d：ui_hd2d@3x 9-slice／icons／layout_hd2d／MOTION_HD2D）＋ 遊音 ui8 v3 hook（uisfx.js）。原創代碼，只用 kit 自家圖。
   做法：唔改遊戲邏輯／DOM id／testid；載 atlas → 裁 dataURL → 生成 CSS（border-image 9／3-slice，1 art = 2 CSS px，@3x → k = 2/3）＋ 少量裝飾節點（dock／圓章／icon）。
   版面（art）：頂 HUD 38｜園景 38–348｜底 74（action 圓章 cy362、dock y386）。?hdui=0 → 停用（舊 UI）。
   動態：MOTION_HD2D §1 tab 240｜§2 popup 420（close 200）｜§3 press 60/120｜§4 toast 220｜§5 紅點 wiggle 6 s｜§6 轉場 900（返回 600）｜§7 toggle 120／stamp。
   reduced motion（quality low／off 或 prefers-reduced-motion）→ 150 ms 淡入淡出、冇 veil。
   音效（0 ms ＝ hook）：見 uisfx.js；呢度只負責喺正確時刻叫 Engine.ui(hook)。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.hd2dui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const K = 2 / 3;                                   // CSS px ／ @3x sprite px
  const NEED = { hunger: ['feed', 'need_fill_feed'], mood: ['heart_bunny', 'need_fill_mood'], clean: ['clean', 'need_fill_clean'], energy: ['sleep', 'need_fill_energy'] };
  const ACT = { 'btn-feed': ['feed', 'med28_pri'], 'btn-play': ['play_cat', 'med28_rose'], 'btn-clean': ['clean', 'med28_sec'], 'btn-sleep': ['sleep', 'med28_violet'] };
  const TABS = [['home', '照顧', 'heart'], ['play', '玩', 'play'], ['garden', '小圃', 'sprout'], ['journal', '手帳', 'book'], ['set', '設定', 'gear']];
  const CUR_RE = /✦|星星碎|光粒|\+\s?\d/;

  function install(G, NS) {
    if (typeof document === 'undefined') return false;
    const qs = new URLSearchParams(location.search); if (qs.get('hdui') === '0') return false;
    const D = NS.data, AUD = NS.audio, UIS = NS.uisfx; if (!UIS || !AUD || !AUD.Engine) return false;
    const E = AUD.Engine; E.UIS = UIS; E.uis = UIS.create(((G.state && G.state.seed) | 0) || 7);
    const ui = document.getElementById('ui'), $ = (s) => document.querySelector(s);
    const BASE = ((D.PARAMS.art && D.PARAMS.art.base) || 'art/') + 'ui_hd2d/';
    const now = () => performance.now();
    const HD = G.hdui = { ready: false, screen: 'home', fx: [], SFX: (h, i) => E.ui(h, i || {}) };
    const SFX = HD.SFX;
    G.hd2dUI = true;
    let lastFace = -1e9, lastWig = now(), lastStageTxt = '';

    // ── 載 kit ─────────────────────────────────────────────
    const img = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });
    const atlas = (n) => fetch(BASE + n + '.json').then(r => r.json()).then(j => img(BASE + (j.image || n + '.png')).then(im => ({ j, im })));
    HD.load = Promise.all([atlas('ui_hd2d@3x'), atlas('icons_hd2d@3x')]).then(([A, I]) => { build(A, I); }).catch(e => { console.warn('hd2dui: kit 載唔到', e); HD.error = String(e); });

    function build(A, I) {
      const FR = A.j.frames, IC = I.j.icons || I.j.frames, cache = {};
      const crop = (src, f) => { const c = document.createElement('canvas'); c.width = f.w; c.height = f.h; c.getContext('2d').drawImage(src, f.x, f.y, f.w, f.h, 0, 0, f.w, f.h); return c.toDataURL(); };
      const fr = (n) => { const f = FR[n]; if (!f) { (HD.missing = HD.missing || []).push(n); } return f; };
      const url = (n) => cache[n] || (cache[n] = FR[n] ? crop(A.im, FR[n]) : '');
      const iurl = (n) => cache['ic:' + n] || (cache['ic:' + n] = IC[n] ? crop(I.im, IC[n]) : '');
      HD.url = url; HD.iurl = iurl;
      const px = (v) => +v.toFixed(2) + 'px';
      // border-image：元素 box ＝ 邏輯 box（× s），glow pad 用 outset 畫出去
      const bi = (n, s) => {
        const f = fr(n); if (!f) return ''; s = s || K;
        const b = f.box || [0, 0, f.w, f.h], pl = Math.max(0, b[0]), pt = Math.max(0, b[1]), pr = Math.max(0, f.w - b[0] - b[2]), pb = Math.max(0, f.h - b[1] - b[3]);
        let sl = '0 fill', wd = '0';
        if (f.nine && f.slice) { const [l, t, r, bo] = f.nine; sl = `${t} ${r} ${bo} ${l} fill`; wd = [t, r, bo, l].map(v => px(v * s)).join(' '); }
        return `border-style:solid !important; border-color:transparent !important; border-width:0 !important; border-image:url(${url(n)}) ${sl} / ${wd} / ${[pt, pr, pb, pl].map(v => px(v * s)).join(' ')} stretch !important;`;
      };
      const bD = (n, d) => { const f = fr(n); return f ? bi(n, d / (f.box || [0, 0, f.w])[2]) : ''; };          // 圓章：直徑 d CSS px
      const bS = (n, s) => { const f = fr(n); s = s || K; return f ? `width:${px(f.w * s)}; height:${px(f.h * s)}; border:0 solid transparent !important; border-image:url(${url(n)}) 0 fill / 0 / 0 stretch !important;` : ''; };   // 成張 sprite
      const ic = (n, d) => { const f = IC[n]; if (!f) { (HD.missing = HD.missing || []).push('icon:' + n); return ''; } const s = d / (f.box || [0, 0, f.w])[2], b = f.box || [0, 0, f.w, f.h]; return `border:0 solid transparent !important; border-image:url(${iurl(n)}) 0 fill / 0 / ${[b[1], f.w - b[0] - b[2], f.h - b[1] - b[3], b[0]].map(v => px(Math.max(0, v) * s)).join(' ')} stretch !important;`; };
      HD.bi = bi; HD.ic = ic;
      const INK = '#3A2840', CREAM = '#FFF5DC', OL = 'text-shadow:-1px 0 #2A2050,1px 0 #2A2050,0 -1px #2A2050,0 1px #2A2050,0 2px 0 rgba(20,14,40,.55);';
      const FONT = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif', SERIF = '"Noto Serif HK","Noto Serif CJK TC","Noto Serif TC","Songti TC",serif';
      const oBack = 'cubic-bezier(.34,1.56,.64,1)', oCubic = 'cubic-bezier(.33,1,.68,1)', ioSine = 'cubic-bezier(.37,0,.63,1)', iCubic = 'cubic-bezier(.32,0,.67,0)';
      const H = '#ui.hd ';
      const tabCx = (i) => 37.8 + 75.6 * i;

      const css = `
${H}{ font-family:${FONT}; }
${H}.panel { background:none; box-shadow:none; backdrop-filter:none; border-radius:0; ${bi('panel_glass_plain')} }
/* ── 頂 HUD（y 0–38 art）── */
${H}#hud { left:0; right:auto; top:0; width:390px; height:0; transition:opacity 240ms ${iCubic} 40ms, transform 240ms ${iCubic} 40ms; }
${H}#chip { position:absolute; left:6px; top:6px; width:184px; height:40px; min-width:0; max-width:none; padding:0; box-sizing:border-box; ${bi('nameplate')} pointer-events:none; }
${H}#chip .hdFace { position:absolute; left:7px; top:7px; width:38px; height:38px; ${bD('med19_paper', 38)} }
${H}#chip .hdFace canvas { position:absolute; left:4px; top:3px; width:30px; height:30px; image-rendering:pixelated; }
${H}#stagename { position:absolute; left:51px; top:4px; margin:0; font:900 15px/20px ${SERIF}; color:${CREAM}; letter-spacing:1px; white-space:nowrap; ${OL} }
${H}#substage { position:absolute; left:var(--subL,110px); top:5px; height:18px; max-width:var(--subW,72px); box-sizing:border-box; padding:0 7px; font:700 var(--subF,10px)/18px ${FONT}; color:${CREAM}; white-space:nowrap; overflow:hidden; opacity:1; ${bi('stage_tag', K * 0.9)} }
${H}#substage:empty { display:none; }
${H}#prog { position:absolute; left:50px; top:30px; width:128px; height:10px; margin:0; padding:2px 3px; box-sizing:border-box; background:none; border-radius:0; overflow:visible; ${bi('exp_trough')} }
${H}#progf { height:6px; background:none; border-radius:0; box-shadow:none; ${bi('exp_fill')} }
${H}#top-r { left:198px; top:10px; right:auto; gap:0; }
${H}#grains { position:relative; width:88px; height:32px; padding:0 9px 0 30px; box-sizing:border-box; display:flex; align-items:center; justify-content:flex-end; font:800 16px/32px ${FONT}; color:#FFE9A8; ${OL} ${bi('chip')} }
${H}#grains::before { content:''; position:absolute; left:2px; top:1px; width:30px; height:30px; ${ic('light', 30)} }
${H}#s12chip { position:absolute !important; left:302px !important; top:10px !important; right:auto !important; width:76px; height:32px; padding:0 9px 0 28px !important; box-sizing:border-box; display:flex !important; align-items:center; justify-content:flex-end; gap:0 !important; background:none !important; box-shadow:none !important; font:800 15px/32px ${FONT} !important; color:#FFE9A8 !important; ${OL} ${bi('chip')} }
${H}#s12chip > img { display:none !important; }
${H}#s12chip::before { content:''; position:absolute; left:0; top:1px; width:30px; height:30px; ${ic('star', 30)} }
${H}#s12chip.pulse { animation:hdGlow .5s 2 !important; }
${H}#s12chip .q { position:absolute; left:36px; top:72px; width:44px; height:44px; box-sizing:border-box; padding-top:44px; display:flex; justify-content:center; align-items:flex-start; font:700 11px/15px ${FONT}; color:${CREAM}; opacity:1 !important; white-space:nowrap; ${OL} ${bD('med22_navy', 44)} animation:none; }
${H}#s12chip .q::before { content:''; position:absolute; left:6px; top:6px; width:32px; height:32px; ${ic('gift', 32)} }
${H}#s12chip .q[data-n]:not([data-n="0"])::after { content:attr(data-n); position:absolute; right:-5px; top:-5px; width:17px; height:17px; font:800 10px/17px ${FONT}; color:#fff; text-align:center; text-shadow:none; ${bD('red_dot_num', 17)} }
${H}#s12chip.hdDone .q::before { ${ic('check', 32)} }
/* 右側 rail（mail／dex）＋ needs */
${H}#hdRail { position:absolute; left:0; top:0; width:0; height:0; z-index:4; transition:opacity 240ms ${iCubic} 40ms, transform 240ms ${iCubic} 40ms; }
${H}#hdRail .ibtn { position:absolute; transform:translate(-50%,-50%); background:none; box-shadow:none; font-size:0 !important; color:transparent; ${'border:0 !important; border-image:none !important;'} }
${H}#diary { left:360px; top:162px; } ${H}#dex { left:360px; top:220px; }
${H}#hdRail .ibtn > i.m { position:absolute; left:50%; top:50%; width:38px; height:38px; margin:-19px 0 0 -19px; ${bD('med19_navy', 38)} pointer-events:none; }
${H}#hdRail .ibtn > i.i { position:absolute; left:50%; top:50%; width:28px; height:28px; margin:-14px 0 0 -14px; pointer-events:none; }
${H}#diary > i.i { ${ic('mail', 28)} } ${H}#dex > i.i { ${ic('dex', 28)} }
${H}#hdRail .ibtn > i.l { position:absolute; left:50%; top:calc(50% + 17px); transform:translateX(-50%); font:700 11px/14px ${FONT}; font-style:normal; color:${CREAM}; white-space:nowrap; ${OL} pointer-events:none; }
${H}#diaryN { position:absolute; left:calc(50% + 8px); top:calc(50% - 22px); right:auto; min-width:0; width:17px; height:17px; padding:0; box-sizing:border-box; border-radius:0; background:none; font:800 10px/17px ${FONT} !important; color:#fff; text-align:center; ${bD('red_dot_num', 17)} }
${H}#needs { left:0; right:auto; top:0; width:390px; height:0; display:block; }
${H}.need { position:absolute; top:52px; width:91px; height:20px; min-width:0; padding:0; box-sizing:border-box; flex:none; background:none; box-shadow:none; ${bi('need_trough')} }
${H}.need[data-need="hunger"] { left:6px; } ${H}.need[data-need="mood"] { left:101px; } ${H}.need[data-need="clean"] { left:196px; } ${H}.need[data-need="energy"] { left:291px; }
${H}.need > span { position:absolute !important; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }
${H}.need > i.m { position:absolute; left:0; top:-1px; width:22px; height:22px; ${bD('med11_navy', 22)} }
${H}.need > i.i { position:absolute; left:3px; top:2px; width:16px; height:16px; }
${Object.keys(NEED).map(k => `${H}.need[data-need="${k}"] > i.i { ${ic(NEED[k][0], 16)} } ${H}.need[data-need="${k}"] .fill { ${bi(NEED[k][1])} }`).join('\n')}
${H}.need.hdLow > i.i { animation:hdBob 2s ${ioSine} infinite; }
${H}.need .track { position:absolute; left:23px; right:4px; top:6px; height:8px; margin:0; padding:0; background:none; border:0; border-radius:0; box-shadow:none; overflow:hidden; }
${H}.need .fill { height:8px; background:none !important; border-radius:0; box-shadow:none; transition:width .3s ${oCubic}; }
${H}.need .fill.warn { ${bi('need_fill_low')} animation:none; }
/* ── action 圓章（cy 362 art）── */
${H}#bar { left:0; right:auto; top:0; bottom:auto; width:390px; height:0; display:block; gap:0; transition:opacity 240ms ${iCubic} 40ms, transform 240ms ${iCubic} 40ms; }
${H}.abtn { position:absolute; top:696px; width:64px; height:72px; margin:0 0 0 -32px; padding:0; flex:none; background:none !important; box-shadow:none !important; border:0 !important; border-image:none !important; font-size:0 !important; overflow:visible; display:block; }
${['btn-feed', 'btn-play', 'btn-clean', 'btn-sleep'].map((id, i) => `${H}#${id} { left:${px(52 + 95.4 * i)}; } ${H}#${id} > i.m { ${bD(ACT[id][1], 56)} } ${H}#${id}:active > i.m, ${H}#${id}.hdDn > i.m { ${bD(ACT[id][1] + '_p', 56)} } ${H}#${id} > i.i { ${ic(ACT[id][0], 40)} }`).join('\n')}
${H}#btn-sleep.hdLight > i.i { ${ic('light', 40)} }
${H}.abtn > canvas { display:none !important; }
${H}.abtn > i.m { position:absolute; left:4px; top:0; width:56px; height:56px; pointer-events:none; }
${H}.abtn > i.i { position:absolute; left:12px; top:8px; width:40px; height:40px; pointer-events:none; }
${H}.abtn .hdl { position:absolute; left:2px; top:48px; width:60px; height:21px; box-sizing:border-box; padding:0; font:800 12px/21px ${FONT} !important; color:${CREAM}; text-align:center; white-space:nowrap; ${OL} ${bi('label_plate')} pointer-events:none; }
${H}.abtn.dis > i.m { ${bD('med28_dis', 56)} } ${H}.abtn.dis > i.i { filter:grayscale(.7) opacity(.55); }
${H}.abtn.hint > i.m { animation:hdHint 1.6s ${ioSine} infinite; } ${H}.abtn.hint { animation:none !important; }
/* ── dock（y 386 art）── */
${H}#hdDock { position:absolute; left:6px; top:772px; width:378px; height:68px; z-index:42; ${bi('dock_bar')} transition:filter 200ms; }
${H}#hdDock.under { z-index:19; }
${H}#hdDock .dv { position:absolute; top:14px; ${bS('dock_div')} pointer-events:none; }
${H}#hdDock .hdTab { position:absolute; top:0; width:75.6px; height:68px; cursor:pointer; -webkit-tap-highlight-color:transparent; }
${H}#hdDock .hdTab > i { position:absolute; display:block; pointer-events:none; font-style:normal; transition:all 240ms ${oBack}; }
${H}#hdDock .hdTab > i.p { left:calc(50% - ${px(39 * K)}); top:-36px; ${bS('dock_pillar')} opacity:0; transform:translateY(10px); }
${H}#hdDock .hdTab.on > i.p { opacity:1; transform:none; }
${H}#hdDock .hdTab > i.m { left:calc(50% - 18px); top:6px; width:36px; height:36px; ${bD('med18_navy_in', 36)} }
${H}#hdDock .hdTab.on > i.m { left:calc(50% - 24px); top:-10px; width:48px; height:48px; ${bD('med24_pri', 48)} }
${H}#hdDock .hdTab > i.i { left:calc(50% - 14px); top:10px; width:28px; height:28px; }
${H}#hdDock .hdTab.on > i.i { left:calc(50% - 19px); top:-5px; width:38px; height:38px; }
${TABS.map(([k, l, icn]) => `${H}#hdDock .hdTab[data-k="${k}"] > i.i { ${ic(icn, 28)} } ${H}#hdDock .hdTab[data-k="${k}"].on > i.i { ${ic(icn, 38)} } ${H}#hdDock .hdTab[data-k="${k}"] > i.l { ${labelCss('lbl_tab_' + l)} } ${H}#hdDock .hdTab[data-k="${k}"].on > i.l { ${labelCss('lbl_tab_on_' + l)} }`).join('\n')}
${H}#hdDock .hdTab:active > i.m { scale:.94; }
${H}#gear { position:absolute !important; left:0 !important; top:0 !important; width:100% !important; height:100% !important; min-width:0 !important; min-height:0 !important; background:none !important; box-shadow:none !important; border:0 !important; border-image:none !important; font-size:0 !important; color:transparent !important; z-index:2; }
/* ── 對白／toast／banner ── */
${H}#bubble { height:40px; box-sizing:border-box; padding:0 14px; font:700 13px/40px ${FONT}; color:${INK}; background:none !important; border-radius:0; box-shadow:none; ${bi('bubble')} }
${H}#bubble::after, ${H}#bubble::before { content:''; position:absolute; left:50%; top:auto; bottom:-15px; margin-left:-10px; ${bS('bubble_tail')} border-width:0 !important; }
${H}#bubble::before { display:none; }
${H}#toast { left:50%; top:88px; transform:translateX(-50%); min-width:264px; max-width:356px; height:36px; box-sizing:border-box; padding:0 16px 0 42px; font:700 var(--tF,13px)/36px ${FONT}; color:${CREAM}; white-space:nowrap; overflow:visible; text-align:center; background:none; ${OL} ${bi('toast')} z-index:30; }
${H}#toast::before { content:''; position:absolute; left:4px; top:3px; width:30px; height:30px; ${bD('med19_pri', 30)} }
${H}#toast::after { content:''; position:absolute; left:8px; top:7px; width:22px; height:22px; ${ic('heart', 22)} animation:inherit; }
${H}#toast.cur::after { ${ic('light', 22)} } ${H}#toast.star::after { ${ic('star', 22)} } ${H}#toast.night::after { ${ic('bedtime', 22)} }
${H}#toast.hdIn { animation:hdToastIn 220ms ${oBack} both; }
${H}#s12gain { left:63px !important; right:auto !important; width:264px !important; top:128px !important; height:36px; box-sizing:border-box; padding:0 12px 0 40px !important; font:800 13px/36px ${FONT} !important; color:#FFE9A8 !important; text-align:center; white-space:nowrap; background:none !important; box-shadow:none !important; ${OL} ${bi('toast')} }
${H}#s12gain::before { content:''; position:absolute; left:6px; top:4px; width:28px; height:28px; ${ic('star', 28)} }
${H}#evcard { background:none; box-shadow:none; color:${CREAM}; ${bi('banner_event')} padding:10px 18px; }
${H}#s12voice { background:none !important; border-width:0 !important; padding:8px 14px !important; color:${INK} !important; ${bi('bubble')} }
${H}#s12voice img, ${H}#s12voice .tail { display:none !important; }
${H}#s12voice::after { content:''; position:absolute; left:50%; bottom:-22px; margin-left:-14px; ${bS('thought_dots')} }
/* ── popup／按鈕（§2／§3）── */
${H}#modal { background:rgba(20,26,54,.43); }
${H}#mbox { position:relative; margin-top:22px; width:314px; max-width:94%; box-sizing:border-box; padding:32px 18px 20px; color:${CREAM}; background:none; box-shadow:none; border-radius:0; ${bi('panel_glass')} }
${H}#mbox > h2 { position:absolute; left:50%; top:-20px; transform:translateX(-50%); margin:0; height:34px; padding:0 30px; box-sizing:border-box; font:900 16px/34px ${SERIF}; color:${CREAM}; white-space:nowrap; letter-spacing:1px; ${OL} ${bi('plaque')} }
${H}#mbox p, ${H}#mbox small, ${H}#mbox .row { color:${CREAM}; }
${H}#mbox .row:has(> .btn), ${H}#mbox .row:has(> .seg) { min-height:46px; padding:4px 12px; margin:6px 0 0; box-sizing:border-box; ${bi('panel_inset')} }
${H}.btn { position:relative; display:inline-block; height:40px; min-width:92px; box-sizing:border-box; padding:0 22px; margin:12px 4px 0; font:800 15px/40px ${FONT}; color:#5A2A10; text-shadow:0 1px 0 rgba(255,240,200,.7); background:none !important; box-shadow:none !important; border-radius:0 !important; ${bi('btn_pri')} }
${H}.btn:active, ${H}.btn.hdDn { ${bi('btn_pri_p')} }
${H}.btn.sec { color:#0F3846; text-shadow:0 1px 0 rgba(220,255,250,.6); ${bi('btn_sec')} }
${H}.btn.sec:active, ${H}.btn.sec.hdDn { ${bi('btn_sec_p')} }
${H}.btn.sec[data-testid="reset-save"] { color:#fff !important; text-shadow:0 1px 0 rgba(90,20,40,.6) !important; ${bi('btn_rose')} }
${H}.btn.sec[data-testid="reset-save"]:active { ${bi('btn_rose_p')} }
${H}.btn[disabled], ${H}.btn.dis { color:#5B566B; ${bi('btn_dis')} }
${H}.seg { display:inline-flex; align-items:center; height:32px; padding:0 4px; gap:0; box-sizing:border-box; background:none; ${bi('seg_bg')} }
${H}.seg .btn { height:24px; min-width:0; margin:0 1px !important; padding:0 9px !important; font:700 12px/24px ${FONT} !important; color:${CREAM} !important; text-shadow:none !important; border-image:none !important; border:0 !important; background:none !important; }
${H}.seg .btn.on { color:#5A2A10 !important; ${bi('seg_on')} }
${H}.hdTg { position:relative; width:52px !important; min-width:0 !important; height:26px !important; margin:0 !important; padding:0 !important; font-size:0 !important; color:transparent !important; text-shadow:none !important; ${bi('toggle_track_on')} }
${H}.hdTg.sec { ${bi('toggle_track_off')} }
${H}.hdTg::before { content:''; position:absolute; left:-10px; right:-10px; top:-11px; bottom:-11px; }
${H}.hdTg::after { content:''; position:absolute; top:2px; left:28px; width:22px; height:22px; ${bD('toggle_knob_on', 22)} transition:left 120ms ${oBack}; }
${H}.hdTg.sec::after { left:2px; ${bD('toggle_knob_off', 22)} }
${H}#pop { left:16px; right:16px; bottom:152px; padding:14px 12px; gap:8px; background:none; box-shadow:none; ${bi('panel_glass_plain')} }
${H}#pop .pitem { min-height:56px; box-sizing:border-box; padding:4px 12px; color:${CREAM}; background:none !important; border-radius:0; box-shadow:none; ${bi('panel_inset')} }
${H}#pop .pitem:active, ${H}#pop .pitem.hdDn { ${bi('panel_inset_sel')} }
${H}.dexCell { background:none !important; border-radius:0; color:${CREAM}; ${bi('card_locked', 0.45)} }
${H}.dexCell.on { ${bi('card', 0.45)} }
/* ── §7 小委託／手帳頁（#s12p） ── */
${H}#s12p { background:rgba(20,26,54,.42); align-items:flex-start; padding-top:110px; box-sizing:border-box; }
${H}#s12box { width:342px !important; padding:30px 14px 16px !important; color:${CREAM} !important; ${bi('panel_glass')} }
${H}#s12box > h3 { left:50%; right:auto; top:-20px; transform:translateX(-50%); height:34px; padding:0 30px; box-sizing:border-box; font:900 16px/34px ${SERIF}; color:${CREAM}; white-space:nowrap; letter-spacing:1px; ${OL} ${bi('plaque')} }
${H}#s12body { max-height:520px; overflow:auto; scrollbar-width:none; -webkit-mask-image:linear-gradient(transparent 0, #000 10px, #000 calc(100% - 14px), transparent 100%); mask-image:linear-gradient(transparent 0, #000 10px, #000 calc(100% - 14px), transparent 100%); }
${H}.s12tabs { gap:2px !important; flex-wrap:wrap; }
${H}.s12tabs b { height:30px; box-sizing:border-box; padding:0 9px !important; font:700 12px/30px ${FONT} !important; color:${CREAM} !important; background:none !important; border-radius:0 !important; box-shadow:none !important; ${OL} ${bi('subtab')} }
${H}.s12tabs b.on { ${bi('subtab_on')} }
${H}.s12row { min-height:52px; box-sizing:border-box; padding:6px 12px !important; margin:6px 0 !important; color:${CREAM} !important; background:none !important; border-radius:0 !important; box-shadow:none !important; ${bi('panel_inset')} }
${H}.s12row[data-done="1"], ${H}.s12row.done { ${bi('panel_inset_sel')} }
${H}.s12row small, ${H}.s12row .s12q, ${H}.s12row b { color:${CREAM} !important; }
${H}.s12q > img:last-child { content:url(${iurl('check')}); width:24px !important; height:24px !important; opacity:.35; filter:grayscale(1); }
${H}.s12q[data-done="1"] > img:last-child { opacity:1; filter:none; }
${H}.s12page { color:${INK} !important; background:none !important; ${bi('panel_paper')} padding:16px 18px !important; }
${H}.s12x { left:auto !important; right:12px !important; top:96px !important; width:44px; height:44px; font-size:0 !important; color:transparent !important; }
${H}.s12x::before { content:''; position:absolute; left:7px; top:7px; width:30px; height:30px; ${bD('close', 30)} }
${H}.s12x:active::before { ${bD('close_p', 30)} }
${H}.s12b-btn { position:relative; background:none !important; border:0 !important; border-image:none !important; box-shadow:none !important; color:#5A2A10 !important; font-weight:800 !important; text-shadow:0 1px 0 rgba(255,240,200,.7); isolation:isolate; }
${H}.s12b-btn::before { content:''; position:absolute; left:0; right:0; top:calc(50% - 16px); height:32px; z-index:-1; ${bi('btn16_pri')} }
${H}.s12b-btn.off { color:#5B566B !important; } ${H}.s12b-btn.off::before { ${bi('btn16_dis')} }
${H}.s12bar { background:none !important; border-radius:0 !important; height:12px !important; ${bi('prog_trough')} overflow:visible !important; }
${H}.s12bar > i { background:none !important; border-radius:0 !important; ${bi('prog_fill_gold')} }
/* ── 轉場 veil（§6）／fx ── */
${H}#hdVeil { position:absolute; left:0; top:0; width:390px; height:844px; z-index:41; pointer-events:none; overflow:hidden; display:none; }
${H}#hdVeil .dim { position:absolute; inset:0; background:#141A36; opacity:0; }
${H}#hdVeil .v { position:absolute; width:128px; height:128px; margin:-64px 0 0 -64px; ${bD('fx_veil', 128)} opacity:0; filter:brightness(1.25); }
${H}#hdVeil.go .v { animation:hdVeil 540ms ${ioSine} 160ms both; } ${H}#hdVeil.go .dim { animation:hdDim 540ms ${ioSine} 160ms both; }
${H}#hdVeil.back .v { animation:hdVeil 600ms ${ioSine} 0ms both reverse; } ${H}#hdVeil.back .dim { animation:hdDim 600ms ${ioSine} both reverse; }
#ui.hd #devp.fold { right:92px; }   /* dev 面板（?dev=1）摺埋時唔遮 dock 設定（#gear） */
${H}#hdFx { position:absolute; left:0; top:0; width:390px; height:844px; z-index:60; pointer-events:none; overflow:visible; }
${H}#hdFx .sp { position:absolute; width:20px; height:20px; margin:-10px 0 0 -10px; ${bD('fx_spark', 20)} animation:hdSpark 520ms ${oCubic} both; }
${H}#hdFx .stamp { position:absolute; width:44px; height:44px; margin:-22px 0 0 -22px; ${bD('stamp_done', 44)} animation:hdStamp 1500ms linear both; }
${H}#hdFx .stamp::after { content:''; position:absolute; left:8px; top:8px; width:28px; height:28px; ${ic('check', 28)} }
${H}#hdFx .ghost { position:absolute !important; pointer-events:none !important; animation:hdGhostOut 200ms ${iCubic} both; }
${H}#hdFx .ghost.long { animation-duration:300ms; }
/* 頁面模式：action／rail 落場（HUD 留低，跟 kit mockup） */
#ui.hd.hdPage #bar { opacity:0; transform:translateY(24px); pointer-events:none; }
#ui.hd.hdPage #hdRail, #ui.hd.hdPage #bubble { opacity:0; transform:translateY(-20px); pointer-events:none; }
#ui.hd.hdPage #s12chip .q { opacity:0 !important; pointer-events:none; }
${H}#mbox.hdOpen { animation:hdPopIn 320ms ${oCubic} 40ms both; }
${H}#mbox.hdOpen > h2 { animation:hdPlq 180ms ${oBack} 120ms both; }
${H}#pop.hdOpen { animation:hdPopIn 320ms ${oCubic} 0ms both; }
${H}.hdRow { animation:hdRow 200ms ${oCubic} both; }
${H}.hdBtnPop { animation:hdBtnPop 320ms ${oBack} 300ms both; }
${H}#s12box.hdEnter { animation:hdPageIn 280ms ${oCubic} 420ms both; }
${H}#s12box.hdEnter .s12row { animation:hdCard 240ms ${oBack} both; }
${Array.from({ length: 8 }, (_, i) => `${H}#s12box.hdEnter .s12row:nth-of-type(${i + 1}) { animation-delay:${520 + 40 * i}ms; }`).join(' ')}
${H}#s12box.hdTabL { animation:hdTabL 240ms ${oCubic} both; } ${H}#s12box.hdTabR { animation:hdTabR 240ms ${oCubic} both; }
${H}#s12body.hdTabR { animation:hdTabR 240ms ${oCubic} both; }
${H}.hdDn { scale:.97; transition:scale 60ms ${oCubic}; } ${H}.hdUp { animation:hdUp 120ms ${oBack}; }
${H}.hdShake { animation:hdShake 160ms linear; }
${H}.hdWig { animation:hdWig 360ms ${ioSine}; } ${H}.hdPopDot { animation:hdDot 240ms ${oBack}; }
@keyframes hdPopIn { 0% { transform:translateY(20px) scale(.78); opacity:0; } 35% { opacity:1; } 55% { transform:translateY(4px) scale(1.05); } 80% { transform:scale(.985); } 100% { transform:none; opacity:1; } }
@keyframes hdPlq { 0% { transform:translate(-50%,-12px); opacity:0; } 100% { transform:translate(-50%,0); opacity:1; } }
@keyframes hdRow { 0% { transform:translateY(8px); opacity:0; } 100% { transform:none; opacity:1; } }
@keyframes hdBtnPop { 0% { scale:.5; opacity:0; } 40% { scale:1.12; opacity:1; } 70% { scale:.96; } 100% { scale:1; opacity:1; } }
@keyframes hdPageIn { 0% { transform:translateY(8px) scale(1.06); opacity:0; } 40% { opacity:1; } 75% { transform:scale(.99); } 100% { transform:none; opacity:1; } }
@keyframes hdCard { 0% { scale:.5; opacity:0; } 50% { scale:1.1; opacity:1; } 75% { scale:.97; } 100% { scale:1; opacity:1; } }
@keyframes hdTabL { 0% { transform:translateX(-16px); opacity:0; } 100% { transform:none; opacity:1; } }
@keyframes hdTabR { 0% { transform:translateX(16px); opacity:0; } 100% { transform:none; opacity:1; } }
@keyframes hdUp { 0% { scale:.97; } 50% { scale:1.03; } 100% { scale:1; } }
@keyframes hdShake { 25% { translate:-3px 0; } 75% { translate:3px 0; } }
@keyframes hdWig { 25% { rotate:-14deg; } 75% { rotate:12deg; } }
@keyframes hdDot { 0% { scale:0; } 60% { scale:1.25; } 100% { scale:1; } }
@keyframes hdVeil { 0% { transform:scale(.9); opacity:0; } 35% { opacity:.88; } 65% { opacity:.88; } 100% { transform:scale(9); opacity:0; } }
@keyframes hdDim { 0% { opacity:0; } 40% { opacity:.45; } 80% { opacity:.3; } 100% { opacity:0; } }
@keyframes hdSpark { 0% { scale:.4; opacity:0; } 30% { scale:1.2; opacity:1; } 100% { scale:.6; opacity:0; translate:var(--dx,0) var(--dy,-14px); } }
@keyframes hdStamp { 0% { scale:1.6; opacity:0; } 6.6% { scale:.9; opacity:1; } 10.6% { scale:1; } 85% { opacity:1; } 100% { scale:1; opacity:0; } }
@keyframes hdGhostOut { 0% { opacity:1; transform:none; } 100% { opacity:0; transform:scale(.94); } }
@keyframes hdToastIn { 0% { transform:translate(-50%,-20px) scaleX(.6); opacity:0; } 60% { transform:translate(-50%,0) scaleX(1.04); opacity:1; } 100% { transform:translate(-50%,0) scaleX(1); opacity:1; } }
@keyframes hdGlow { 50% { filter:brightness(1.45) drop-shadow(0 0 6px #FFDC8C); } }
@keyframes hdHint { 50% { filter:brightness(1.25) drop-shadow(0 0 8px #FFDC8C); } }
@keyframes hdBob { 0%,80%,100% { translate:0 0; } 90% { translate:0 -2px; } }
@keyframes hdFade { 0% { opacity:0; } 100% { opacity:1; } }
/* reduced motion：150 ms 淡入淡出、冇 veil */
#ui.hd.hdReduce #hdVeil { display:none !important; }
#ui.hd.hdReduce .hdOpen, #ui.hd.hdReduce .hdRow, #ui.hd.hdReduce .hdBtnPop, #ui.hd.hdReduce #s12box.hdEnter, #ui.hd.hdReduce #s12box.hdEnter .s12row, #ui.hd.hdReduce .hdTabL, #ui.hd.hdReduce .hdTabR, #ui.hd.hdReduce #toast.hdIn { animation:hdFade 150ms linear both !important; }
#ui.hd.hdReduce #mbox.hdOpen > h2 { animation:none !important; }
#ui.hd.hdReduce .hdWig, #ui.hd.hdReduce .hdShake, #ui.hd.hdReduce .hdUp, #ui.hd.hdReduce .need > i.i, #ui.hd.hdReduce .abtn.hint > i.m { animation:none !important; }
#ui.hd.hdReduce #hdFx .ghost { animation:hdFade 150ms linear both reverse !important; }
#ui.hd.hdReduce #hud, #ui.hd.hdReduce #bar, #ui.hd.hdReduce #hdRail { transition:opacity 150ms linear !important; transform:none !important; }
`;
      function labelCss(n) { const f = FR[n]; if (!f) { (HD.missing = HD.missing || []).push(n); return ''; } return `left:calc(50% - ${px(f.w * K / 2)}); top:${px(56 - f.h * K / 2)}; ${bS(n)}`; }
      const st = document.createElement('style'); st.id = 'hd2dui-css'; st.textContent = css; document.head.appendChild(st);
      dom(); hooks(); ui.classList.add('hd'); HD.ready = true; HD.readyAt = now();
      setInterval(tick, 250); tick();
    }

    // ── 裝飾節點（唔改原有 id／testid／事件）──────────────────────
    function dom() {
      const mk = (tag, cls, par, before) => { const e = document.createElement(tag); if (cls) e.className = cls; if (par) par.insertBefore(e, before || null); return e; };
      // 名牌頭像
      const chip = $('#chip'); if (chip) { const f = mk('div', 'hdFace', chip, chip.firstChild); HD.face = mk('canvas', '', f); HD.face.width = 30; HD.face.height = 30; }
      // needs icon
      document.querySelectorAll('.need').forEach(n => { mk('i', 'm', n, n.firstChild); mk('i', 'i', n, n.children[1]); });
      // action 圓章
      document.querySelectorAll('.abtn').forEach(b => {
        mk('i', 'm', b, b.firstChild); mk('i', 'i', b, b.children[1]);
        let lab = b.querySelector('span'); if (!lab) { lab = mk('span', 'hdl', null); [...b.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).forEach(n => lab.appendChild(n)); b.appendChild(lab); } else lab.classList.add('hdl');
      });
      // rail：mail／dex 由 #top-r 搬去右側 rail
      const rail = mk('div', '', ui); rail.id = 'hdRail';
      [['diary', '信件'], ['dex', '圖鑑']].forEach(([id, l]) => { const b = document.getElementById(id); if (!b) return; rail.appendChild(b); mk('i', 'm', b, b.firstChild); mk('i', 'i', b, b.children[1]); const t = mk('i', 'l', b); t.textContent = l; });
      // dock
      const dock = mk('div', '', ui); dock.id = 'hdDock'; dock.dataset.testid = 'hd-dock';
      for (let i = 1; i < 5; i++) { const d = mk('i', 'dv', dock); d.style.left = (75.6 * i - 1) + 'px'; }
      HD.tabs = {};
      TABS.forEach(([k], i) => { const t = mk('div', 'hdTab', dock); t.dataset.k = k; t.dataset.testid = 'hd-tab-' + k; t.style.left = (75.6 * i) + 'px'; ['p', 'm', 'i', 'l'].forEach(c => mk('i', c, t)); HD.tabs[k] = t; });
      const gear = $('#gear'); if (gear) HD.tabs.set.appendChild(gear);
      const veil = mk('div', '', ui); veil.id = 'hdVeil'; mk('div', 'dim', veil); HD.veilV = mk('div', 'v', veil); HD.veil = veil;
      const fx = mk('div', '', ui); fx.id = 'hdFx'; HD.fxEl = fx;
    }

    // ── 狀態 tick（250 ms）：頁面、dock active、toast 字號、needs 低、紅點 wiggle、頭像 ──
    function tick() {
      const t = now(), s = G.state, q = (s && s.settings && s.settings.quality) || 'high';
      const reduce = q === 'low' || q === 'off' || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
      ui.classList.toggle('hdReduce', !!reduce); HD.reduce = !!reduce;
      const modal = $('#modal'), mOpen = modal && modal.style.display === 'flex', pan = $('#s12p'), sOpen = !!(pan && pan.style.display === 'flex');
      const kind = mOpen ? ($('#mbox') && $('#mbox').dataset.kind) || '' : '';
      const tab = G.s12 && G.s12.tab, act = mOpen && /setting/i.test(kind) ? 'set' : sOpen ? (tab === 'garden' ? 'garden' : tab === 'games' ? 'play' : 'journal') : 'home';
      for (const k in HD.tabs) HD.tabs[k].classList.toggle('on', k === act);
      HD.active = act; $('#hdDock').classList.toggle('under', !!mOpen);
      ui.classList.toggle('hdPage', sOpen);
      const gr = $('#grains'); if (gr && gr.textContent.indexOf('✦') === 0) gr.textContent = gr.textContent.replace(/^✦\s*/, '');
      // quest rail 數字
      const qq = $('#s12chip .q'); if (qq) { const m = /(\d+)\s*\/\s*(\d+)/.exec(qq.textContent || ''); const n = m ? Math.max(0, +m[2] - +m[1]) : 0; if (qq.dataset.n !== String(n)) { if (+qq.dataset.n === 0 && n > 0) pop(qq); qq.dataset.n = n; } $('#s12chip').classList.toggle('hdDone', !!m && n === 0); }
      // 名牌：substage 自動縮字
      const nm = $('#stagename'), sb = $('#substage');
      if (nm && sb) { const key = nm.textContent + '|' + sb.textContent; if (key !== lastStageTxt) { lastStageTxt = key; const L = 51 + nm.offsetWidth + 5, W = Math.max(30, 184 - 8 - L); sb.style.setProperty('--subL', L + 'px'); sb.style.setProperty('--subW', W + 'px'); let f = 10; sb.style.setProperty('--subF', f + 'px'); while (f > 7 && sb.scrollWidth > W) { f -= 0.5; sb.style.setProperty('--subF', f + 'px'); } } }
      document.querySelectorAll('.need').forEach(n => { const f = n.querySelector('.fill'); n.classList.toggle('hdLow', !!f && parseFloat(f.style.width) < 20); });
      const sl = $('#btn-sleep'); if (sl) sl.classList.toggle('hdLight', !!(s && s.sleeping));
      // 設定 toggle
      document.querySelectorAll('#mbox .btn:not(.seg .btn)').forEach(b => { if (/^(開|關)$/.test(b.textContent.trim())) b.classList.add('hdTg'); });
      // 紅點 wiggle（主頁靜止、每 6 s）＋ badge 聲（≥5 s 冷卻、一畫面一次：uisfx 管）
      if (act === 'home' && !mOpen && !sOpen && t - lastWig >= 6000) {
        const dots = [...document.querySelectorAll('#diaryN, #s12chip .q')].filter(d => d.offsetParent !== null && (d.id === 'diaryN' ? d.style.display !== 'none' && d.textContent.trim() : +d.dataset.n > 0));
        if (dots.length) { lastWig = t; dots.forEach(d => replay(d, 'hdWig', 380)); SFX('badge', { screen: HD.screen }); }
      } else if (act !== 'home' || mOpen) lastWig = Math.max(lastWig, t - 3000);
      if (t - lastFace > 2000) { lastFace = t; face(); }
    }
    function face() {
      const c = HD.face, R = G.renderer; if (!c || !R || !R.atlasSrc || !G.state) return;
      try {
        const s = G.state; let src = null;
        if (s.stage === 'egg') src = R.atlasSrc('atlas_evo_egg', 'egg_idle', 0) || R.atlasSrc('atlas_egg', 'egg_idle', 0);
        else { const fk = R.fkOf(s), F = D.FORMS[fk]; if (F) src = R.atlasSrc(F.atlas, 'idle', 0); }
        const x = c.getContext('2d'); x.clearRect(0, 0, 30, 30); x.imageSmoothingEnabled = false;
        if (src && src.img) { const sc = Math.min(30 / src.sw, 30 / src.sh); const w = src.sw * sc, h = src.sh * sc; x.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, (30 - w) / 2, 30 - h, w, h); }
      } catch (e) { }
    }
    function replay(el, cls, ms) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); setTimeout(() => el.classList.remove(cls), ms); }
    function pop(el) { replay(el, 'hdPopDot', 260); SFX('appear'); }
    const uiXY = (r) => { const u = ui.getBoundingClientRect(), sc = u.width / 390; return { x: (r.left - u.left) / sc, y: (r.top - u.top) / sc, w: r.width / sc, h: r.height / sc }; };
    function sparks(x, y, n) { if (HD.reduce) return; for (let i = 0; i < (n || 3); i++) { const e = document.createElement('i'); e.className = 'sp'; e.style.left = (x + (i - 1) * 9) + 'px'; e.style.top = (y + (i % 2) * 6) + 'px'; e.style.setProperty('--dx', ((i - 1) * 10) + 'px'); e.style.setProperty('--dy', (-10 - 6 * i) + 'px'); e.style.animationDelay = (i * 40) + 'ms'; HD.fxEl.appendChild(e); setTimeout(() => e.remove(), 700); } }
    function ghost(el, long) {   // close／返回：複製一份淡出（原本元素已即時收起，邏輯唔等動畫）
      if (!el || !el.getBoundingClientRect) return; const r = el.getBoundingClientRect(); if (!r.width) return;
      const g = el.cloneNode(true); g.querySelectorAll('[id],[data-testid]').forEach(n => { n.removeAttribute('id'); n.removeAttribute('data-testid'); }); g.removeAttribute('id'); g.removeAttribute('data-testid');
      const p = uiXY(r); g.className = (el.className || '') + ' ghost' + (long ? ' long' : ''); g.classList.remove('hdOpen', 'hdEnter');
      const cs = getComputedStyle(el); g.style.cssText = `left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;margin:0;display:${cs.display === 'none' ? 'block' : cs.display};`;
      if (el.id) g.dataset.hdOf = el.id;
      HD.fxEl.appendChild(g); setTimeout(() => g.remove(), long ? 320 : 220);
    }
    HD.stamp = function (target) {   // §7 委託完成：stamp_done 1.6→.9（0–100）→1（100–160）＋ fx_spark；聲：sparkle 0、confirm 20
      let el = target || null;
      if (!el) { const pan = $('#s12p'); if (pan && pan.style.display === 'flex') { const done = [...pan.querySelectorAll('.s12q[data-done="1"]')], rows = done.length ? done : [...pan.querySelectorAll('.s12q')].slice(0, 1); el = rows.length ? rows[rows.length - 1].querySelector('img:last-child') || rows[rows.length - 1] : null; } }
      if (!el || !el.offsetParent) el = $('#s12chip .q') || $('#s12chip');
      SFX('stamp');
      if (!el) return;
      const p = uiXY(el.getBoundingClientRect()), x = p.x + p.w / 2, y = p.y + Math.min(p.h, 44) / 2;
      const s = document.createElement('i'); s.className = 'stamp'; s.style.left = x + 'px'; s.style.top = y + 'px'; HD.fxEl.appendChild(s); setTimeout(() => s.remove(), 1600);
      sparks(x + 14, y - 14, 3);
      return { x, y };
    };

    // ── 事件 hook（capture，喺 sys12 stopPropagation 之前收到）─────────────
    function hooks() {
      const SKIP = '#mg2, #devp, #dbg, #dbgT, #hit, #mgHud';
      let lastDn = null, lastDnT = 0, userClose = 0;
      ui.addEventListener('pointerdown', (e) => {
        const t = e.target; if (!t.closest || t.closest(SKIP)) return;
        lastDnT = now();
        const tab = t.closest('#hdDock .hdTab'); if (tab) { press(tab); return; }
        if (t.closest('.s12x') || t.id === 's12p') { userClose = now(); press(t.closest('.s12x') || t); return; }
        if (t.id === 'modal') { userClose = now(); return; }
        const ab = t.closest('.abtn'); if (ab) { if (ab.classList.contains('dis')) { SFX('disabled'); replay(ab, 'hdShake', 170); } else { SFX('medal'); press(ab); } return; }
        const rb = t.closest('#hdRail .ibtn, #s12chip .q'); if (rb) { SFX('medal'); press(rb); return; }
        if (t.closest('#s12chip')) { SFX('medal'); press(t.closest('#s12chip')); return; }
        const sg = t.closest('.seg .btn'); if (sg) { SFX('medal', { seg: true }); press(sg); return; }
        const tg = t.closest('.hdTg'); if (tg) { press(tg); return; }
        const sb = t.closest('.s12tabs b[data-tab]'); if (sb) { return; }
        const b = t.closest('.btn, .pitem, .s12b-btn'); if (b) { if (b.classList.contains('off') || b.disabled) { SFX('disabled'); replay(b, 'hdShake', 170); return; } SFX('press'); press(b); lastDn = b; return; }
      }, true);
      function press(el) {
        el.classList.add('hdDn');
        const up = () => { el.classList.remove('hdDn'); if (!HD.reduce) replay(el, 'hdUp', 130); SFX('cardUp'); window.removeEventListener('pointerup', up, true); window.removeEventListener('pointercancel', up, true); };
        window.addEventListener('pointerup', up, true); window.addEventListener('pointercancel', up, true);
      }
      ui.addEventListener('click', (e) => {
        const t = e.target; if (!t.closest || t.closest(SKIP)) return;
        const tg = t.closest('.hdTg'); if (tg) { setTimeout(() => SFX('toggle', { on: !tg.classList.contains('sec') }), 0); }
        const sb = t.closest('.s12tabs b[data-tab]'); if (sb && !sb.classList.contains('on')) { SFX('tab'); setTimeout(() => { const bd = $('#s12body'); if (bd && !HD.reduce) replay(bd, 'hdTabR', 260); }, 0); }
        const tab = t.closest('#hdDock .hdTab'); if (tab) dockTap(tab.dataset.k, e);
      }, true);
      // 主掣確認 sparkle（視覺；聲由 legacy confirm → primary 出）
      const origNotify = E.notify.bind(E);
      E.notify = function (kind, info) {
        if (kind === 'confirm' && lastDn && now() - lastDnT < 1500) { const p = uiXY(lastDn.getBoundingClientRect()); if (p.w) sparks(p.x + p.w - 10, p.y + 4, 3); }
        return origNotify(kind, info);
      };
      // dock
      function dockTap(k, e) {
        const pan = $('#s12p'), sOpen = !!(pan && pan.style.display === 'flex'), keys = (G.s12 && G.s12.tabs || []).map(x => x[0]);
        if (k === 'set') { if (sOpen) { HD.silentClose = true; G.s12close(); HD.silentClose = false; } if (HD.active !== 'set') SFX('tab'); return; }   // #gear 自己 click → openSettings
        if (k === 'home') { if (sOpen) { userClose = now(); G.s12close(); } else { if (UI().closePop && $('#pop') && $('#pop').style.display === 'flex') UI().closePop(); if (HD.active !== 'home') SFX('tab'); } return; }
        const want = k === 'play' ? 'games' : k === 'garden' ? 'garden' : 'quest';
        if (!G.s12open) return;
        if (want !== 'quest' && keys.length && !keys.includes(want)) { UI().toast && UI().toast('呢頁未開放'); return; }
        HD.openStyle = k === 'play' ? 'tab' : 'transition'; HD.openFrom = HD.tabs[k];
        if (sOpen && G.s12.tab === want) { HD.openStyle = null; return; }
        G.s12open(want); HD.openStyle = null;
      }
      const UI = () => NS.ui || {};
      // s12 開／關 包一層（轉場／tab／返回）
      const o0 = G.s12open, c0 = G.s12close;
      if (o0) G.s12open = function (tab) {
        const pan = $('#s12p'), was = !!(pan && pan.style.display === 'flex'), prev = G.s12 && G.s12.tab;
        const r = o0.apply(this, arguments);
        const box = $('#s12box'); if (!box) return r;
        const style = HD.openStyle || 'transition', screen = 'page:' + (G.s12.tab || tab || 'quest');
        if (was) { if (prev !== G.s12.tab) { SFX('tab'); SFX('screen', { screen }); HD.screen = screen; if (!HD.reduce) replay(box, 'hdTabR', 260); } return r; }
        HD.screen = screen;
        const ev = window.event, userEv = !!(ev && ev.isTrusted && /^(click|pointerup|pointerdown|mouseup|touchend|keydown|keyup)$/.test(ev.type));
        if (!userEv && !HD.openStyle) { SFX('screen', { screen }); if (!HD.reduce) replay(box, 'hdTabR', 260); return r; }   // 程式開（QA／通知）：唔做 veil／卡 pop
        if (style === 'tab') { SFX('tab'); SFX('screen', { screen }); if (!HD.reduce) replay(box, 'hdTabR', 260); return r; }
        const rows = box.querySelectorAll('.s12row').length;
        SFX('transition', { screen, cards: HD.reduce ? 0 : rows });
        veil('go', HD.openFrom || $('#s12chip .q') || $('#s12chip')); HD.openFrom = null;
        if (!HD.reduce) replay(box, 'hdEnter', 1000);
        return r;
      };
      if (c0) G.s12close = function () {
        const pan = $('#s12p'), was = !!(pan && pan.style.display === 'flex'), box = $('#s12box');
        const user = !HD.silentClose && now() - userClose < 1000;
        if (was && box && !HD.silentClose) ghost(box, true);
        const r = c0.apply(this, arguments);
        if (was) { HD.screen = 'home'; if (user) { SFX('back', { screen: 'home' }); veil('back', HD.tabs.home); } else SFX('screen', { screen: 'home' }); }
        return r;
      };
      function veil(mode, from) {
        if (HD.reduce) return; const v = HD.veil; let x = 195, y = 420;
        if (from && from.getBoundingClientRect) { const p = uiXY(from.getBoundingClientRect()); if (p.w) { x = p.x + p.w / 2; y = p.y + p.h / 2; } }
        HD.veilV.style.left = x + 'px'; HD.veilV.style.top = y + 'px'; v.style.display = 'block'; v.classList.remove('go', 'back'); void v.offsetWidth; v.classList.add(mode);
        clearTimeout(HD.veilT); HD.veilT = setTimeout(() => { v.style.display = 'none'; v.classList.remove('go', 'back'); }, mode === 'go' ? 760 : 640);
      }
      HD.veilPlay = veil;
      // popup（#modal）：開 → popupOpen＋§2 動畫；關 → popup_close（✕／背景）＋ ghost 200 ms
      const modal = $('#modal'), mbox = $('#mbox');
      let mWas = false, mSnap = null;
      if (modal && mbox) {
        const onM = () => {
          const open = modal.style.display === 'flex';
          if (open && !mWas) { SFX('popupOpen'); openAnim(); }
          else if (open && mWas && mSnap !== mbox.firstChild) { SFX('popupOpen'); openAnim(); }   // 排隊下一個 modal
          else if (!open && mWas) { if (now() - userClose < 600) SFX('popupClose'); }
          mWas = open; mSnap = mbox.firstChild;
        };
        new MutationObserver(onM).observe(modal, { attributes: true, attributeFilter: ['style'] });
        new MutationObserver(() => { if (mWas && modal.style.display === 'flex' && mSnap !== mbox.firstChild) onM(); }).observe(mbox, { childList: true });
        // 關閉前影低（click capture：按掣會即刻收 modal）
        mbox.addEventListener('click', (e) => { if (e.target.closest('.btn') && !e.target.closest('.seg')) { const snap = mbox; requestAnimationFrame(() => { if (modal.style.display !== 'flex') ghostModal(snap); }); } }, true);
        modal.addEventListener('click', (e) => { if (e.target === modal) requestAnimationFrame(() => { if (modal.style.display !== 'flex') { ghostModal(mbox); } }); }, true);
      }
      let lastMClone = null;
      mbox && mbox.addEventListener('pointerdown', () => { lastMClone = mbox.cloneNode(true); }, true);
      function ghostModal() { if (HD.reduce || !lastMClone) return; const g = lastMClone; lastMClone = null; g.querySelectorAll('[id],[data-testid]').forEach(n => { n.removeAttribute('id'); n.removeAttribute('data-testid'); }); g.removeAttribute('id'); g.className = 'ghost'; const p = HD.mRect; if (!p) return; g.style.cssText = `left:${p.x}px;top:${p.y}px;width:${p.w}px;margin:0;color:#FFF5DC;box-sizing:border-box;padding:32px 18px 20px;${HD.bi('panel_glass')}`; HD.fxEl.appendChild(g); setTimeout(() => g.remove(), 230); }
      function openAnim() {
        requestAnimationFrame(() => { const r = mbox.getBoundingClientRect(); if (r.width) HD.mRect = uiXY(r); });
        if (HD.reduce) { replay(mbox, 'hdOpen', 200); return; }
        replay(mbox, 'hdOpen', 700);
        const kids = [...mbox.children].filter(c => c.tagName !== 'H2');
        kids.forEach((c, i) => { if (c.querySelector && c.querySelector('.btn') && c === kids[kids.length - 1]) { c.querySelectorAll('.btn:not(.sec)').forEach(b => replay(b, 'hdBtnPop', 680)); return; } c.style.animationDelay = (220 + 60 * Math.min(i, 6)) + 'ms'; replay(c, 'hdRow', 220 + 60 * Math.min(i, 6) + 260); setTimeout(() => { c.style.animationDelay = ''; }, 220 + 60 * Math.min(i, 6) + 270); });
      }
      // #pop（餵食／玩耍選單）
      const popEl = $('#pop'); let pWas = false;
      if (popEl) new MutationObserver(() => { const o = popEl.style.display === 'flex'; if (o && !pWas) { SFX('popupOpen'); if (!HD.reduce) replay(popEl, 'hdOpen', 400); } pWas = o; }).observe(popEl, { attributes: true, attributeFilter: ['style'] });
      // toast
      const toastEl = $('#toast'); let tTxt = '', tAt = -1e9, tVis = false;
      if (toastEl) new MutationObserver(() => {
        const vis = toastEl.style.display !== 'none' && toastEl.style.display !== '', txt = toastEl.textContent;
        if (vis && (txt !== tTxt || !tVis)) {
          const t = now(), same = txt === tTxt && t - tAt < 1500; tTxt = txt; tAt = t;
          const cur = CUR_RE.test(txt); toastEl.classList.toggle('cur', cur && !/星星碎/.test(txt)); toastEl.classList.toggle('star', /星星碎|委託/.test(txt)); toastEl.classList.toggle('night', /晚安|瞓/.test(txt));
          let f = 13; toastEl.style.setProperty('--tF', f + 'px'); while (f > 10 && toastEl.scrollWidth > 356) { f -= 0.5; toastEl.style.setProperty('--tF', f + 'px'); }
          if (!same) { SFX('toast', { currency: cur }); if (!HD.reduce) replay(toastEl, 'hdIn', 240); }
        } else if (!vis && tVis && !HD.reduce) ghost(toastEl);
        tVis = vis;
      }).observe(toastEl, { attributes: true, attributeFilter: ['style'], childList: true, characterData: true, subtree: true });
      // s12 星星碎 gain（貨幣 toast）
      const gainObs = () => { const g = $('#s12gain'); if (!g) return setTimeout(gainObs, 500); let last = ''; new MutationObserver(() => { const tx = g.textContent; if (tx && tx !== last) { last = tx; SFX('toast', { currency: true }); setTimeout(() => { last = ''; }, 1500); } }).observe(g, { childList: true, characterData: true, subtree: true }); };
      gainObs();
      // §7 委託完成 → stamp
      (G.sysListeners = G.sysListeners || []).push((e) => { if (e && e.sys === 'quest' && e.what === 'paid' && e.n > 0) HD.stamp(); });
      // 紅點出現（#diaryN）
      const dn = $('#diaryN'); let dVis = false;
      if (dn) new MutationObserver(() => { const v = dn.style.display !== 'none' && !!dn.textContent.trim(); if (v && !dVis) pop(dn); dVis = v; }).observe(dn, { attributes: true, childList: true, characterData: true, subtree: true });
    }
    return true;
  }
  return { install };
});
