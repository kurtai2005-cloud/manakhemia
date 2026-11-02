/* 《微光小圃》 ui63.js — 6b.3「UI 縮細＋收埋」（Kurt 2026-11-02 19:54）。原創代碼；只喺 v2（#ui.hd.v2.u62）生效，v1 唔郁。
   ① 全部 ui62 UI 縮細一級：標題／掣 FP12 24→有效 20、內文 18→16、輔助 16→14（hd2dui2 read62 跟 .u63s 補返倍數）；
      按鈕、rail、面板、HUD、頭像用 CSS `scale` 同比例縮（唔郁 layout、唔撞原本 transform）；每組有錨點（左上 HUD、右上錢包、右 rail、底 dock…），
      面板／全畫面層入面嘅元件按位置揀錨（頂／底／左右邊或者自己中心）。FP12 CSS 字號照係 12 嘅倍數（像素字唔糊）。
      撳位 ≥48：縮完唔夠 48 嘅可撳元件加透明 hit area（<i class="u63hit">，唔郁外觀）。
   ② 「收埋」掣（左下角、細、半透明、有字）：撳一下淡出 HUD／rail／掣／dock，淨低寵物同場景；再撳或者撳空位即返；狀態記住（localStorage）。
      對白（心聲／泡泡）、toast、彈窗、全畫面層照出。
   ?ui63=0 全停；🛠「6b.3」。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.ui63 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const S = 20 / 24;                       // 縮細一級：24→20、18→15（read62 補到 16）、16→13.3（補到 14）
  const TYPE = { title: 20, body: 16, aux: 14, lhBody: 24, lhAux: 20 };
  const HK = 'glimmer.u63hide';
  // 錨點：設計座標 390×844；回 [ox, oy]（相對 #ui）
  function anchorOf(L, T, W, H) {
    const cx = L + W / 2, cy = T + H / 2, B = T + H;
    const oy = T < 120 ? 0 : B > 760 ? 844 : cy;
    const ox = W >= 300 ? 195 : cx < 120 ? 0 : cx > 270 ? 390 : cx;
    return [ox, oy];
  }
  function install(G, NS) {
    const qs = new URLSearchParams(location.search);
    if (qs.get('ui63') === '0') return false;
    const ui = document.getElementById('ui'); if (!ui || !NS.ui62) return false;
    const $ = (s) => document.querySelector(s), pnow = () => performance.now();
    const on = () => !!(G.ui2 && G.ui2.on && ui.classList.contains('v2') && ui.classList.contains('u62'));
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const STAT = { scaled: 0, hits: 0, hide: 0, show: 0 };
    let sizeOn = true; const syncCls = () => { const v = sizeOn && on(); if (ui.classList.contains('u63') !== v) { ui.classList.toggle('u63', v); if (G.ui2 && G.ui2.readAll) try { G.ui2.readAll(); } catch (e) { } } };   // v1／未開 v2：唔加 class（v1 唔郁）
    syncCls(); if (G.ui2) { G.ui2.u63 = S; }
    const H = '#ui.hd.v2.u62.u63 ';
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const HIDE = ['#hud', '#bar', '#s12chip', '#hdRail', '#hdDock', '#devBtn', '#s12gain'];
    const css = document.createElement('style'); css.id = 'ui63css';
    css.textContent = `
${H}.u63s { scale:${S.toFixed(4)}; transform-origin:var(--u63o, 50% 50%) !important; }
${H}.u63hit { position:absolute; display:block; background:transparent; pointer-events:auto; font-style:normal; z-index:0; }
${H}.u62sub { font-size:var(--u63a, ${TYPE.aux}px) !important; line-height:var(--u63al, ${TYPE.lhAux}px) !important; }
${H}.u63s .u62sub, ${H}.u62sub.u63s { font-size:var(--u63as, ${(TYPE.aux / S).toFixed(1)}px) !important; line-height:var(--u63asl, ${(TYPE.lhAux / S).toFixed(1)}px) !important; }
${H}#u62tip .b { font-size:${(TYPE.body / S).toFixed(1)}px; line-height:${(TYPE.lhBody / S).toFixed(1)}px; }
${HIDE.map(s => H + s).join(', ')} { transition:opacity 280ms ease; }
${H}#u62work > .grid { top:134px; bottom:auto; height:667px; grid-auto-rows:max-content; }   /* 縮後由 134 排到 690（底下留俾 toast 696／gain） */
${H}#u62work .hd .u62sub { top:72px; pointer-events:none; } ${H}#u62work .hd .sum { top:136px; }   /* 細機用途句兩行都唔撞進度行 */
${HIDE.map(s => 'body.u63hid ' + H + s).join(', ')} { opacity:0 !important; pointer-events:none !important; }
#u63hide { display:none; }
${H}#u63hide { display:flex; position:absolute; left:6px; top:620px; z-index:7; width:48px; height:52px; box-sizing:border-box; flex-direction:column; align-items:center; justify-content:flex-start; gap:2px;
  cursor:pointer; opacity:.62; transition:opacity 200ms ease; -webkit-tap-highlight-color:transparent; }
${H}#u63hide:active { opacity:.9; }
${H}#u63hide .c { width:30px; height:30px; border-radius:15px; box-sizing:border-box; border:1px solid rgba(232,194,122,.8); background:rgba(15,17,34,.62); display:flex; align-items:center; justify-content:center; }
${H}#u63hide .c canvas { width:20px; height:14px; image-rendering:pixelated; }
${H}#u63hide .l { font:500 14px/18px ${FALL}; letter-spacing:.5px; color:#F7EEDB; text-shadow:0 0 2px #000,0 1px 0 #000,1px 0 0 #000,-1px 0 0 #000,0 -1px 0 #000; white-space:nowrap; font-style:normal; }
body.u63hid ${H}#u63hide { opacity:.42; }
body.u62ov ${H}#u63hide, body.u62w-on ${H}#u63hide, body.s2-house ${H}#u63hide, body.l6c-on ${H}#u63hide, body.u63tip ${H}#u63hide { display:none; }   /* 一次性小提示喺左下：讓位 */
`;
    document.head.appendChild(css);

    // ── ① 縮細：每組錨點 ──
    const GROUPS = [   // [selector, 錨點（#ui 座標）或者 'self:x y'（相對自己）]
      ['#hdBan2', [195, 0]], ['#chip', [0, 0]], ['#needs', [0, 0]], ['#top-r', [390, 0]], ['#s12chip', [390, 0]], ['#devBtn', [0, 0]],
      ['#hdRail', [390, 160]], ['#bar', [195, 844]], ['#hdDock', [195, 844]],
      ['#toast', 'self:50% 0'], ['#s12gain', 'self:0 0'], ['#s12voice', 'self:50% 100%'], ['#bubble', 'self:50% 100%'], ['#u62tip', 'self:0 100%'], ['#mbox', 'self:50% 50%'],
    ];
    const OVS = ['#l5bov', '#l6bov', '#l5ov', '#u62work', '#s2houseV', '#l6cov', '#l6cdex'];
    const SKIP = (e) => e.tagName === 'CANVAS' || e.tagName === 'STYLE' || (e.dataset.testid || '').indexOf('house-pin-') === 0 || e.classList.contains('hb') || e.classList.contains('u63hit') || e.classList.contains('u63no');   // u63no：遊戲內容（6c 夢地圖格／團絨／碎片）唔縮，保持 art 整數倍
    function posOf(e) { let L = 0, T = 0, p = e; while (p && p !== ui) { L += p.offsetLeft; T += p.offsetTop; p = p.offsetParent; } return p === ui ? [L, T] : null; }
    function unScale(e) { if (!e.classList.contains('u63s')) return; e.classList.remove('u63s'); e.querySelectorAll('i.u63hit').forEach(h => h.remove()); e.querySelectorAll('[data-u63m]').forEach(x => { for (const k of ['margin-top', 'margin-right', 'margin-bottom', 'margin-left']) x.style.removeProperty(k); delete x.dataset.u63m; }); e.querySelectorAll('[data-u63c]').forEach(x => { x.style.removeProperty('overflow'); x.style.removeProperty('overflow-clip-margin'); delete x.dataset.u63c; }); }
    function setScale(e, o) {
      let v; if (typeof o === 'string') v = o.slice(5); else { const pt = posOf(e); if (!pt) return; v = (o[0] - pt[0]).toFixed(1) + 'px ' + (o[1] - pt[1]).toFixed(1) + 'px'; }
      if (e.style.getPropertyValue('--u63o') !== v) e.style.setProperty('--u63o', v);
      if (!e.classList.contains('u63s')) { e.classList.add('u63s'); STAT.scaled++; }
    }
    // 個別覆寫：工作 grid 縮咗之後由頂排落、拉長到 footer 上面（唔會頂排留大空位／卡內字被裁）
    const OVR = [['#u62work > .grid', 'self 50% 0']];
    function ovScale(ov, d) {
      for (const c of ov.children) {
        if (SKIP(c)) continue; const W = c.offsetWidth, Hh = c.offsetHeight; if (!W && !Hh && !c.children.length) continue;
        if (W >= 380 && Hh >= 800) { if (d < 2 && c.children.length) ovScale(c, d + 1); continue; }   // 全畫面底／層：入去搵元件
        const ow = OVR.find((r) => c.matches(r[0])); if (ow) { setScale(c, ow[1]); continue; }
        const pt = posOf(c); if (!pt) continue; setScale(c, anchorOf(pt[0], pt[1], W, Hh));
      }
    }
    // 細機（fit < 1）：rail 掣排得密，縮 0.833 之後透明 48 熱區會疊住隔離；rail 就唔縮咁多，等每格實際 ≥49 CSS px
    function railFit() {
      const rl = $('#hdRail'); if (!rl) return; const k = ui.getBoundingClientRect().width / (ui.offsetWidth || 1) || 1;
      const ys = [...rl.querySelectorAll('.ibtn')].filter(e => e.offsetWidth && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden').map(e => posOf(e)).filter(Boolean).map(p => p[1]).sort((a, b) => a - b);
      let P = Infinity; for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] > 1) P = Math.min(P, ys[i] - ys[i - 1]);
      const sR = isFinite(P) ? Math.min(1, Math.max(S, Math.ceil(49.5 / (P * k) * 1000) / 1000)) : S;
      const v = sR > S + 0.001 ? sR.toFixed(3) : ''; if (rl.style.scale !== v) { if (v) rl.style.setProperty('scale', v); else rl.style.removeProperty('scale'); note('railFit', { sR, P: Math.round(P), k: +k.toFixed(3) }); }
    }
    function scaleTick() {
      if (!on()) return;
      for (const [sel, o] of GROUPS) { const e = $(sel); if (!e) continue; if (sel === '#mbox' && e.dataset.kind === 'devmode') { unScale(e); continue; } setScale(e, o); }   // 🛠 開發者面板唔縮（測試用、唔係玩家 UI）
      railFit();
      for (const sel of OVS) { const ov = $(sel); if (ov) ovScale(ov, 0); }
      hitTick(); auxTick(); document.body.classList.toggle('u63tip', !!document.getElementById('u62tip'));
    }
    // ── 撳位 ≥48：縮完唔夠就加透明 hit area ──
    const CLK = '.ibtn, .abtn, .hdTab, .btn, .k, [role="button"], [data-testid$="-close"], [data-testid*="-btn"], [data-testid^="house-"], .card6, .card, .l5bseg, .l5bhit, #u63hide';   // 5b 三段掣／好！／揭頁：原本 ::after 熱區跟住縮，要補
    // 細機（360）成個 #ui 再縮：輔助字實際仍 ≥14（同 read62 一樣計法）
    let fLast = 0;
    function auxTick() {
      const f = Math.min(1, Math.round((ui.getBoundingClientRect().width / (ui.offsetWidth || 390) || 1) * 100) / 100); if (f === fLast) return; fLast = f;
      const fa = Math.max(TYPE.aux, Math.ceil(TYPE.aux / f * 10) / 10), la = Math.round(fa * 10 / 7);
      ui.style.setProperty('--u63a', fa + 'px'); ui.style.setProperty('--u63al', la + 'px');
      ui.style.setProperty('--u63as', (fa / S).toFixed(1) + 'px'); ui.style.setProperty('--u63asl', (la / S).toFixed(1) + 'px');
    }
    // 排得密嘅細掣（flex／grid／inline 行入面）：加 margin 撐開間距，等兩粒掣嘅 hit area 唔會疊埋（每粒都有自己 48）
    function room(e, cs, need, root) {
      if (cs.position === 'absolute' || cs.position === 'fixed' || e === root) return; const par = e.parentElement; if (!par) return;
      const pd = getComputedStyle(par).display, row = /flex|grid/.test(pd) || /inline/.test(cs.display); if (!row && cs.display !== 'block') return;
      if (!e.dataset.u63m) e.dataset.u63m = [cs.marginTop, cs.marginRight, cs.marginBottom, cs.marginLeft].map(v => parseFloat(v) || 0).join(',');
      const m0 = e.dataset.u63m.split(',').map(Number), mx = Math.max(0, (need - e.offsetWidth) / 2), my = Math.max(0, (need - e.offsetHeight) / 2) * (row ? 1 : 2);   // block 上下 margin 會疊（collapse）：要成份
      const set = (k, v) => { const t = v.toFixed(1) + 'px'; if (e.style.getPropertyValue(k) !== t) e.style.setProperty(k, t, 'important'); };
      if (my > 0) { set('margin-top', Math.max(m0[0], my)); set('margin-bottom', Math.max(m0[2], my)); }
      if (row && mx > 0) { set('margin-left', Math.max(m0[3], mx)); set('margin-right', Math.max(m0[1], mx)); }
    }
    // hit area 俾 overflow:hidden 裁咗：改用 overflow:clip＋overflow-clip-margin（只放 hit area 出去，捲動容器唔郁）
    function unclip(e, hb, root) {
      const hr = hb.getBoundingClientRect();
      for (let a = e; a && a !== ui; a = a.parentElement) {
        const cs = getComputedStyle(a); if (!(cs.overflowX === 'hidden' && cs.overflowY === 'hidden') && !(cs.overflowX === 'clip' && a.dataset.u63c)) { if (a === root) break; continue; }
        const r = a.getBoundingClientRect(), sc = r.width / (a.offsetWidth || 1) || 1, ext = Math.max(r.left - hr.left, hr.right - r.right, r.top - hr.top, hr.bottom - r.bottom) / sc;
        if (ext > 0.5) { const want = Math.ceil(ext + 1), cur = +(a.dataset.u63c || 0); if (want > cur) { a.dataset.u63c = want; a.style.setProperty('overflow', 'clip', 'important'); a.style.setProperty('overflow-clip-margin', want + 'px', 'important'); } }
        if (a === root) break;
      }
    }
    function hitTick() {
      const k = ui.getBoundingClientRect().width / (ui.offsetWidth || 390) || 1;
      document.querySelectorAll('#ui .u63s').forEach((root) => {
        const list = root.matches(CLK) ? [root] : []; root.querySelectorAll(CLK).forEach(e => list.push(e));
        for (const e of list) {
          if (!e.offsetWidth || e.classList.contains('u63hit')) continue; const cs = getComputedStyle(e); if (cs.cursor !== 'pointer' && !e.matches('.ibtn, .abtn, .hdTab, #u63hide')) continue;
          const r = e.getBoundingClientRect(), w = r.width / k, h = r.height / k; let hb = e.querySelector(':scope > i.u63hit');
          if (w >= 48.5 && h >= 48.5 && r.width >= 48.5 && r.height >= 48.5) { if (hb) hb.remove(); continue; }   // 設計 ≥48、實際 CSS 都 ≥48（細機都撳得中）
          if (cs.position === 'static') { if (e.querySelector('*') && [...e.querySelectorAll('*')].some(x => getComputedStyle(x).position === 'absolute')) continue; e.style.position = 'relative'; }
          const sc = r.width / e.offsetWidth || 1, need = Math.max(49 * k, 49) / sc;   // 自己座標要幾大先夠 49 設計 px
          const dx = Math.max(0, (need - e.offsetWidth) / 2) + e.clientLeft, dy = Math.max(0, (need - e.offsetHeight) / 2) + e.clientTop;   // 絕對定位由 padding box 計：補返邊框
          if (!hb) { hb = document.createElement('i'); hb.className = 'u63hit'; hb.setAttribute('aria-hidden', 'true'); e.appendChild(hb); STAT.hits++; }
          const st = `left:${-dx}px;right:${-dx}px;top:${-dy}px;bottom:${-dy}px`; if (hb.style.cssText.replace(/\s/g, '') !== st.replace(/\s/g, '')) hb.style.cssText = st;
          room(e, cs, need, root); unclip(e, hb, root);
        }
      });
    }

    // ── ② 收埋 UI ──
    let hidden = false; try { hidden = localStorage.getItem(HK) === '1'; } catch (e) { }
    const btn = document.createElement('div'); btn.id = 'u63hide'; btn.dataset.testid = 'u63-hide'; btn.setAttribute('role', 'button');
    btn.innerHTML = '<span class="c"><canvas width="10" height="7"></canvas></span><i class="l"></i>';
    function drawEye(open) { const c = btn.querySelector('canvas'), g = c.getContext('2d'); g.clearRect(0, 0, 10, 7); g.fillStyle = '#F7EEDB';
      if (open) { g.fillRect(2, 1, 6, 1); g.fillRect(1, 2, 1, 3); g.fillRect(8, 2, 1, 3); g.fillRect(2, 5, 6, 1); g.fillStyle = '#E8C27A'; g.fillRect(4, 2, 2, 3); }
      else { g.fillRect(1, 3, 8, 1); g.fillRect(2, 4, 1, 1); g.fillRect(4, 4, 1, 2); g.fillRect(6, 4, 1, 2); g.fillRect(8, 4, 1, 1); } }
    function apply() { document.body.classList.toggle('u63hid', hidden && on()); btn.querySelector('.l').textContent = hidden ? '顯示' : '收埋'; btn.setAttribute('aria-label', hidden ? '顯示介面' : '收埋介面'); btn.title = btn.getAttribute('aria-label'); drawEye(hidden); }
    function setHidden(v, why) { v = !!v; if (v === hidden) { apply(); return hidden; } hidden = v; try { localStorage.setItem(HK, v ? '1' : '0'); } catch (e) { } apply(); STAT[v ? 'hide' : 'show']++; note(v ? 'hide' : 'show', { why });
      const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui('tap', {}); } catch (e) { } return hidden; }
    btn.addEventListener('pointerdown', (e) => e.stopPropagation());
    btn.addEventListener('click', (e) => { e.stopPropagation(); setHidden(!hidden, 'btn'); });
    ui.appendChild(btn); apply();
    // 收埋緊：撳空位（#hit）即返；呢一下唔當摸寵物
    let swallow = 0;
    window.addEventListener('pointerdown', (e) => { if (!hidden || !on()) return; const t = e.target; if (t && t.id === 'hit') { e.stopPropagation(); e.preventDefault(); swallow = pnow(); setHidden(false, 'tap'); } }, true);
    for (const ev of ['pointerup', 'click']) window.addEventListener(ev, (e) => { if (swallow && pnow() - swallow < 600 && e.target && e.target.id === 'hit') { e.stopPropagation(); e.preventDefault(); } }, true);

    function tick() { try { syncCls(); apply(); scaleTick(); } catch (e) { note('err', { m: String(e && e.message || e) }); } }
    let mq = 0; setInterval(tick, 300); setTimeout(tick, 200);
    try { new MutationObserver(() => { if (!mq) mq = requestAnimationFrame(() => { mq = 0; tick(); }); }).observe(ui, { childList: true }); } catch (e) { }

    // ── 🛠「6b.3」──
    const DEV = { id: 'ui63', title: '6b.3（UI 縮細＋收埋）', order: 48,
      status: () => '縮細 ' + (ui.classList.contains('u63') ? '開' : '閂') + '・收埋 ' + (hidden ? '收咗' : '冇') + '・縮咗 ' + document.querySelectorAll('#ui .u63s').length + ' 組・hit area ' + document.querySelectorAll('#ui .u63hit').length,
      items: [
        ['hide', '收埋 UI', () => { setHidden(true, 'dev'); return { ok: true, msg: '收埋咗（撳空位或者「顯示」返嚟）' }; }],
        ['show', '顯示 UI', () => { setHidden(false, 'dev'); return { ok: true, msg: '返嚟喇' }; }],
        ['size', '縮細 開／閂（比較用）', () => { const v = !sizeOn; sizeOn = v; syncCls(); document.querySelectorAll('#ui [data-r62]').forEach(e => { delete e.dataset.r62; }); if (G.ui2 && G.ui2.readAll) G.ui2.readAll(); return { ok: true, msg: '縮細：' + (v ? '開' : '閂') }; }],
        ['ov', '量 UI 重疊', () => { const o = G.ui62 && G.ui62.overlap ? G.ui62.overlap() : { n: 0, hits: [] }; return { ok: !o.hits.length, msg: o.n + ' 個框・重疊 ' + o.hits.length }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.ui63 = { S, TYPE, setHidden, hidden: () => hidden };
    window.__qa = window.__qa || {};
    window.__qa.ui63 = { st: () => ({ on: on(), u63: ui.classList.contains('u63'), hidden, bodyHid: document.body.classList.contains('u63hid'), scaled: document.querySelectorAll('#ui .u63s').length, hits: document.querySelectorAll('#ui .u63hit').length, stat: Object.assign({}, STAT) }),
      setHidden, tick, dev: () => DEV, log: () => log.slice(), anchorOf };
    note('install', {});
    return true;
  }
  return { install, S, TYPE, anchorOf, HK };
});
