/* 《微光小圃》 long6bui.js — 第 6 批 6b「真世界連動」介面（遊策 breakthrough-6a6d-spec §6b）。原創代碼。
   邏輯全部喺 long6b.js（s.rw6）；呢度只做：
   ・花園 rail「散步」掣 → 散步路面板：團絨喺 12 格散步路行到邊、今日步數、下一格、星星碎 n/5、執到嘅裝飾、兩個開關（計步／真天氣）。
   ・權限全部可以唔開（預設閂）：計步＝Android ACTIVITY_RECOGNITION（原生 RealWorld plugin，TYPE_STEP_COUNTER）；真天氣＝大概位置（ACCESS_COARSE_LOCATION；
     瀏覽器用 navigator.geolocation 低精度）→ Open-Meteo（免 key）。唔畀／冇感應器／冇網 → 遊戲同而家一樣（每日擲天氣、原本晝夜）。
   ・真天氣只改畫面：G.visWeather／G.visHour 只俾 renderer（G.view）同撐葉；計分（SIM 天氣、菇傘雨天分）照用 G.weather；月眠／水珠時段用真鐘唔變。
   ・6b.1 遊美散步美術（art/breakthrough/6b，WALK_6B.md／walk6b.json）：walk_bg 100×120（×2 顯示）、12 格＝6 粒踏腳石＋石與石之間中點（由近到遠）；
     團絨 per_pet/<形態>/walk.png 6 幀 10fps loop（幀大細／pivot 跟 idle；1 art px＝1 CSS px，pivot 企喺格位；向左 flipX，pivot x＝W−1−px；地影引擎畫橢圓）；
     執到嘅小物 deco_*.png 16×16 擺喺格位；rail icon＝ic_walk。圖未載到／形態冇圖 → 照舊 placeholder（洋紅虛線＋data-ph）。
   ・🛠 開發者模式「6b」；?l6b=0 全停；webdriver 下自動讀計步器／攞天氣預設閂（?l6b=1 開）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6bui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const RW = NS.long6b, UI = NS.ui; if (!RW || !UI) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l6b') === '0') return false;
    const wd = !!(navigator && navigator.webdriver);
    const AUTO = { on: qs.get('l6b') === '1' || !wd };
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now();
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2200); };
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const LB5 = 'art/series2_long/5b/ui/', B6 = 'art/breakthrough/6b/';
    // 6b.1 美術：walk6b.json（pets／keys）＋圖 lazy 載入
    const A6 = { json: null, img: {}, want: {}, err: [] };
    const a6img = (f) => { if (A6.img[f]) return A6.img[f]; if (!A6.want[f]) { A6.want[f] = 1; const i = new Image(); i.onload = () => { if (i.naturalWidth) { A6.img[f] = i; if (OV.el) refresh(); } }; i.onerror = () => A6.err.push(f); i.src = B6 + f; } return null; };
    const DECO_F = { pebble: 'pebble', leaf: 'maple_leaf', acorn: 'acorn', feather: 'feather', shell: 'snail_shell', clover: 'clover4', button: 'button', ribbon: 'ribbon' };
    const fkNow = () => { const s = S(); if (!s || s.stage === 'egg') return null; if (s.fam && s.fam.km && s.fam.km.fk) return s.fam.km.fk; try { return G.renderer && G.renderer.fkOf ? G.renderer.fkOf(s) : null; } catch (e) { return null; } };
    const A6load = fetch(B6 + 'walk6b.json').then(r => r.ok ? r.json() : null).then(j => { if (j && j.pets && j.keys) { A6.json = j; PATH = mkPath(); a6img('walk_bg.png'); const fk = fkNow(); if (fk && j.pets[fk]) a6img(j.pets[fk]['1x']); if (OV.el) refresh(); } }).catch(e => A6.err.push(String(e && e.message || e)));
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const F8 = () => (U() ? '"GlimmerFP8",' : '') + FALL, F12 = () => (U() ? '"GlimmerFP12",' : '') + FALL;
    const CREAM = '#FFF5DC', GOLD = '#FFE08A', MINT = '#B8F0C8';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      btn16_dis: 'background:#8C8796;border:3px solid #4A4656;border-radius:8px;', panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || FB[n] || ''; };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const TXT = (size, color, extra) => `font:${U() ? (size <= 24 ? 24 : 36) : Math.max(size, 20)}px/1.2 ${U() ? F12() : F8()};color:${color || CREAM};${OL}-webkit-font-smoothing:none;` + (extra || '');

    // ── 原生（Capacitor RealWorld plugin）／瀏覽器 ──
    const NAT = () => { const C = window.Capacitor; if (C && C.isNativePlatform && C.isNativePlatform() && C.Plugins && C.Plugins.RealWorld) return C.Plugins.RealWorld; return window.__rw6native || null; };
    const PERM = { steps: null, location: null, sensor: null, err: null };
    async function natStatus() { const N = NAT(); if (!N) return null; try { const r = await N.status(); Object.assign(PERM, { steps: r.steps || null, location: r.location || null, sensor: r.sensor !== false }); return r; } catch (e) { PERM.err = String(e && e.message || e); return null; } }
    async function readSteps(why) {
      const o = RW.st(S()); if (!o.on.steps) return { ok: false, why: 'off' }; const N = NAT(); if (!N) return { ok: false, why: 'nonative' };
      let r; try { r = await N.steps(); } catch (e) { PERM.err = String(e && e.message || e); note('stepsErr', { e: PERM.err }); return { ok: false, why: 'err' }; }
      if (!r || r.steps == null) return { ok: false, why: 'nodata' };
      const g = RW.ingest(S(), r.steps, r.bootMs, now()); note('steps', { why, raw: r.steps, d: g.steps, sh: g.shards, deco: g.deco }); after(g); save(); return g;
    }
    function after(g) {
      if (!g || !g.ok && g.ok !== undefined && !g.steps) return;
      const d = RW.day(S(), now());
      if (g.shards) toast('散步：+' + g.shards + ' 星星碎（今日 ' + d.sh + '／' + RW.CFG.shardCap + '）');
      for (const k of g.deco || []) { toast('散步路執到「' + RW.DK[k].zh + '」！'); RB.dot = true; }
      if (g.tiles) note('tiles', { n: g.tiles }); refresh();
    }
    // 位置：只用嚟砌 Open-Meteo URL（0.1°），唔存
    function locate() {
      const N = NAT();
      if (N) return N.location().then(r => (r && Number.isFinite(+r.lat) && Number.isFinite(+r.lon)) ? { lat: +r.lat, lon: +r.lon } : null).catch(() => null);
      if (!navigator.geolocation) return Promise.resolve(null);
      return new Promise((res) => { try { navigator.geolocation.getCurrentPosition((p) => res({ lat: p.coords.latitude, lon: p.coords.longitude }), () => res(null), { enableHighAccuracy: false, maximumAge: 3600e3, timeout: 12000 }); } catch (e) { res(null); } });
    }
    const WXZ = { clear: '晴', overcast: '陰', rain: '落雨', fog: '霧' };
    const WXS = { busy: false, last: null, err: null, n: 0 };
    async function refreshWx(force) {
      const s = S(); if (!RW.st(s).on.wx || WXS.busy) return null; if (!force && RW.fresh(s, now())) return RW.st(s).wx;
      WXS.busy = true; WXS.n++;
      try {
        const p = await locate(); if (!p) { WXS.err = 'noloc'; note('wxErr', { e: 'noloc' }); return null; }
        const u = RW.url(p.lat, p.lon); const r = await fetch(u, { cache: 'no-store' }); if (!r.ok) throw new Error('http ' + r.status);
        const w = RW.applyWx(S(), await r.json(), now()); WXS.err = w ? null : 'parse'; WXS.last = w ? w.kind : null; note('wx', { kind: w && w.kind }); save(); refresh(); return w;
      } catch (e) { WXS.err = String(e && e.message || e); note('wxErr', { e: WXS.err }); return null; }
      finally { WXS.busy = false; }
    }
    // 開關（UI）：開 → 問權限；唔畀 → 保持閂，照舊玩
    async function toggle(what) {
      const s = S(), o = RW.st(s);
      if (o.on[what]) { RW.setOn(s, what, false); save(); note('off', { what }); toast(what === 'steps' ? '計步閂咗（步數記錄留喺部機）' : '真天氣閂咗：返遊戲天氣'); refresh(); return false; }
      const N = NAT();
      if (what === 'steps') {
        if (!N) { toast('呢部機用唔到計步器：照舊玩'); note('deny', { what, why: 'nonative' }); refresh(); return false; }
        const st0 = await natStatus(); if (st0 && st0.sensor === false) { toast('部機冇計步感應器：照舊玩'); note('deny', { what, why: 'nosensor' }); refresh(); return false; }
        let g = st0 && st0.steps; if (g !== 'granted') { try { const r = await N.requestSteps(); g = r && r.steps; PERM.steps = g || null; } catch (e) { g = 'denied'; } }
        if (g !== 'granted') { toast('冇計步權限：照舊玩，隨時可以再開'); note('deny', { what, why: 'perm' }); refresh(); return false; }
        RW.setOn(s, 'steps', true); save(); note('on', { what }); toast('計步開咗：每 1000 步團絨行 1 格'); await readSteps('on'); refresh(); return true;
      }
      if (N) { const st0 = await natStatus(); let g = st0 && st0.location; if (g !== 'granted') { try { const r = await N.requestLocation(); g = r && r.location; PERM.location = g || null; } catch (e) { g = 'denied'; } }
        if (g !== 'granted') { toast('冇位置權限：照舊用遊戲天氣'); note('deny', { what, why: 'perm' }); refresh(); return false; } }
      else if (!navigator.geolocation) { toast('呢部機攞唔到位置：照舊用遊戲天氣'); note('deny', { what, why: 'nogeo' }); refresh(); return false; }
      RW.setOn(s, 'wx', true); save(); note('on', { what }); const w = await refreshWx(true);
      if (!w) { toast('暫時攞唔到天氣：照舊用遊戲天氣'); } else toast('真天氣：' + WXZ[w.kind] + '（只改畫面）');
      refresh(); return true;
    }

    // 畫面 hook（main.js tickWorld → G.view）：只改畫面
    G.visWeather = (gw) => { try { return RW.visWeather(S(), gw, now()); } catch (e) { return gw; } };
    G.visHour = (h) => { try { return RW.visHour(S(), h, now()); } catch (e) { return h; } };

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l6bcss';
    css.textContent = `#l6bov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:59;user-select:none;-webkit-user-select:none;touch-action:manipulation}
#l6bov .bd{position:absolute;inset:0;background:rgba(18,12,30,.62)}
body.l6b-on #toast{z-index:72 !important}
#l6bov .row{position:relative;display:flex;align-items:center;gap:8px;box-sizing:border-box;padding:2px 10px;min-height:36px}
#l6bov .tg{position:relative;display:flex;align-items:center;gap:8px;box-sizing:border-box;min-height:56px;padding:4px 10px;cursor:pointer;margin:6px 0 0}
#l6bov .pill{flex:0 0 auto;min-width:72px;height:40px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;border-radius:20px}
#l6bov [data-ph]{outline:2px dashed #FF2BD6;outline-offset:-2px}
#l6bbtn{cursor:pointer}
#l6bbtn > i.i{position:absolute;left:50%;top:50%;width:36px;height:36px;margin:-18px 0 0 -18px;pointer-events:none}
@keyframes l6bbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}`;
    document.head.appendChild(css);

    // ── 散步路（placeholder：直向背景＋12 格路＋團絨縮圖） ──
    const PATH0 = (() => { const pts = []; for (let i = 0; i < RW.CFG.pathTiles; i++) { const r = Math.floor(i / 3), c = i % 3, cc = r % 2 ? 2 - c : c; pts.push([22 + cc * 28, 104 - r * 26]); } return pts; })();   // 蛇形（art px 100×120；未有美術）
    // 6b.1：12 格＝6 粒踏腳石（json 由遠到近 → 反轉做由近到遠）＋每粒石同下一粒之間中點；最遠嗰粒之後嘅中點向地平線（pathCenter 最頂）
    function mkPath() { const k = A6.json && A6.json.keys['6b:walk_bg']; if (!k || !Array.isArray(k.stones) || k.stones.length < 2) return PATH0;
      const st = k.stones.slice().reverse(), pc = k.pathCenter || {}, ys = Object.keys(pc).map(Number).sort((a, b) => a - b), top = ys.length ? [pc[ys[0]], ys[0]] : st[st.length - 1], pts = [];
      for (let i = 0; i < st.length && pts.length < RW.CFG.pathTiles; i++) { const a = st[i], b = st[i + 1] || top; pts.push([a[0], a[1]]); pts.push([Math.round((a[0] + b[0]) / 2), Math.round((a[1] + b[1]) / 2)]); }
      while (pts.length < RW.CFG.pathTiles) pts.push(pts[pts.length - 1]); return pts.slice(0, RW.CFG.pathTiles); }
    let PATH = PATH0;
    function drawPath(cv) {
      const g = cv.getContext('2d'); g.imageSmoothingEnabled = false; const W = 100, H = 120; g.clearRect(0, 0, W, H);
      const bg = A6.json && a6img('walk_bg.png');
      if (bg) { g.drawImage(bg, 0, 0, W, H); delete cv.dataset.ph; cv.dataset.art = '6b:walk_bg'; return; }
      cv.dataset.ph = '6b:walk_bg'; delete cv.dataset.art;
      const grd = g.createLinearGradient(0, 0, 0, H); grd.addColorStop(0, '#7FB6D8'); grd.addColorStop(0.35, '#BFE3C0'); grd.addColorStop(1, '#6FA86A'); g.fillStyle = grd; g.fillRect(0, 0, W, H);
      g.fillStyle = '#5E9A5A'; for (let i = 0; i < 26; i++) { const x = (i * 37) % W, y = 40 + (i * 53) % 78; g.fillRect(x, y, 2, 1); }
      g.strokeStyle = '#E8D3A0'; g.lineWidth = 6; g.lineJoin = 'round'; g.beginPath(); PATH.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.stroke();
      g.strokeStyle = '#C9AE74'; g.lineWidth = 1; g.stroke();
      const s = S(), o = RW.st(s), today = RW.dayKey(now());
      PATH.forEach(([x, y], i) => { g.fillStyle = '#A88A55'; g.fillRect(x - 1, y - 1, 3, 3); });
      for (const e of o.log) if (RW.dayKey(e.t) === today && !(A6.json && a6img('deco/deco_' + DECO_F[e.k] + '.png'))) { const p = PATH[e.tile % PATH.length]; g.fillStyle = '#FF2BD6'; g.fillRect(p[0] + 3, p[1] - 6, 4, 4); }   // 今日執到：未有圖 → 洋紅 placeholder 小物
      g.fillStyle = '#FFE08A'; const fl = PATH[PATH.length - 1]; g.fillRect(fl[0] - 1, fl[1] - 10, 2, 9); g.fillRect(fl[0] + 1, fl[1] - 10, 5, 3);   // 終點旗
    }
    function petAt() { const p = RW.pos(S()), a = PATH[p.tile], b = PATH[(p.tile + 1) % PATH.length]; return [a[0] + (b[0] - a[0]) * p.frac, a[1] + (b[1] - a[1]) * p.frac]; }
    // 6b.1：walk clip（6 幀 10fps loop、向右；向左 flipX）；pivot 企喺格位（CSS px＝art px×2 嘅格位座標；團絨 1 art px＝1 CSS px）
    const WK = { t0: pnow(), fk: null, dir: 1 };
    function walkClip(P) {
      const fk = fkNow(), p = fk && A6.json && A6.json.pets[fk], im = p && a6img(p['1x']);
      const [x, y] = petAt(), pp = RW.pos(S()), a = PATH[pp.tile], b = PATH[(pp.tile + 1) % PATH.length], dx = b[0] - a[0];
      if (dx) WK.dir = dx < 0 ? -1 : 1;
      if (!im) { P.pc.dataset.ph = '6b:walk_clip'; delete P.pc.dataset.art; P.pc.width = 48; P.pc.height = 48; P.pc.style.width = '48px'; P.pc.style.height = '48px'; P.pc.style.transform = ''; P.pc.style.animation = 'l6bbob 900ms steps(2) infinite';
        P.pc.style.left = Math.round(x * 2 - 24) + 'px'; P.pc.style.top = Math.round(y * 2 - 44) + 'px'; P.sh.style.display = 'none'; petThumb(P.pc); return false; }
      const [fw, fh] = p.frameSize, [px, py] = p.pivot, n = p.frames || 6, fps = p.fps || 10, f = Math.floor((pnow() - WK.t0) / (1000 / fps)) % n;
      if (P.pc.width !== fw || P.pc.height !== fh) { P.pc.width = fw; P.pc.height = fh; P.pc.style.width = fw + 'px'; P.pc.style.height = fh + 'px'; }
      const g = P.pc.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, fw, fh); g.drawImage(im, f * fw, 0, fw, fh, 0, 0, fw, fh);
      const X = Math.round(x * 2), Y = Math.round(y * 2), pvx = WK.dir < 0 ? fw - 1 - px : px;
      P.pc.style.left = (X - pvx) + 'px'; P.pc.style.top = (Y - py) + 'px'; P.pc.style.transform = WK.dir < 0 ? 'scaleX(-1)' : ''; P.pc.style.animation = 'none';
      delete P.pc.dataset.ph; P.pc.dataset.art = '6b:walk_clip'; P.pc.dataset.fk = fk; P.pc.dataset.frame = f; P.pc.dataset.dir = WK.dir < 0 ? 'L' : 'R';
      const sw = Math.max(10, Math.round(fw * 0.55)); P.sh.style.display = ''; P.sh.style.width = sw + 'px'; P.sh.style.left = (X - sw / 2) + 'px'; P.sh.style.top = (Y - 3) + 'px';   // 地影：引擎畫橢圓
      WK.fk = fk; return true;
    }
    function decoArt(P) {   // 今日執到嘅小物：16×16（1 art px＝1 CSS px），擺喺格位隔籬
      const o = RW.st(S()), today = RW.dayKey(now()), want = o.log.filter(e => RW.dayKey(e.t) === today && DECO_F[e.k]).slice(-8), key = want.map(e => e.k + e.tile).join();
      if (P.dk === key && P.dl.childElementCount === want.length) return; P.dk = key; P.dl.textContent = '';
      want.forEach(e => { const f = 'deco/deco_' + DECO_F[e.k] + '.png', im = A6.json && a6img(f); if (!im) { P.dk = null; return; } const pt = PATH[e.tile % PATH.length];
        const d = img(B6 + f, `left:${Math.round(pt[0] * 2 + 10)}px;top:${Math.round(pt[1] * 2 - 14)}px;width:16px;height:16px`); d.dataset.art = '6b:deco_' + DECO_F[e.k]; d.dataset.testid = 'l6b-deco-' + e.k; P.dl.appendChild(d); });
    }
    function petThumb(c) {   // 團絨散步縮圖（未有 walk clip → idle 幀 0）
      const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, c.width, c.height); const SA = G.s2Art, s = S(); let src = null;
      try { if (SA && SA.atlasSrc && G.renderer) { const a = SA.atlasSrc(G.renderer.fkOf(s), 'idle', 0, true); if (a && a.src && a.src.img && a.src.img.width) src = a.src; } } catch (e) { }
      if (!src) { g.fillStyle = '#FFF5DC'; g.beginPath(); g.arc(c.width / 2, c.height / 2 + 2, c.width / 3, 0, 7); g.fill(); g.fillStyle = '#24172C'; g.fillRect(c.width / 2 - 4, c.height / 2, 2, 2); g.fillRect(c.width / 2 + 2, c.height / 2, 2, 2); return false; }
      const k = Math.min(c.width / src.sw, c.height / src.sh); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, (c.width - src.sw * k) / 2, c.height - src.sh * k, src.sw * k, src.sh * k); return true;
    }

    // ── 疊層 ──
    const OV = { el: null, parts: null };
    const busy = () => !!OV.el || !!document.getElementById('l5bov') || !!document.getElementById('l5ov') || !!document.getElementById('l5cov') || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene');
    function closeOv(quiet) { if (!OV.el) return false; OV.el.remove(); OV.el = null; OV.parts = null; document.body.classList.remove('l6b-on'); if (!quiet) note('ovClose'); return true; }
    function openOv(why) {
      closeOv(true); const host = document.getElementById('ui') || document.body;
      const el = OV.el = mk('div', '', null, 'l6b-ov'); el.id = 'l6bov';
      const bd = mk('div', ''); bd.className = 'bd'; bd.addEventListener('click', () => { UIS('tap'); closeOv(); }); el.appendChild(bd);
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      const p = mk('div', `position:absolute;left:14px;top:96px;width:362px;box-sizing:border-box;padding:30px 10px 12px;${bi('panel_navy')}`, null, 'l6b-panel'); el.appendChild(p);
      p.appendChild(mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:200px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), '散步路', 'l6b-title'));
      const x0 = mk('div', `position:absolute;right:-23px;top:-25px;z-index:5;width:52px;height:52px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center` + TXT(24, CREAM), null, 'l6b-close');
      x0.appendChild(mk('div', `position:relative;flex:0 0 auto;width:30px;height:30px;pointer-events:none;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}`, sp('close') ? '' : '✕'));
      x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); p.appendChild(x0);
      // 散步路（placeholder 背景 200×240＝100×120 art px ×2）
      const box = mk('div', 'position:relative;width:200px;height:240px;margin:0 auto 6px;', null, 'l6b-path'); p.appendChild(box);
      const cv = mk('canvas', 'position:absolute;left:0;top:0;width:200px;height:240px;image-rendering:pixelated;', null, 'l6b-walkbg'); cv.width = 100; cv.height = 120; cv.dataset.ph = '6b:walk_bg'; box.appendChild(cv);
      const dl = mk('div', 'position:absolute;inset:0;pointer-events:none', null, 'l6b-decos'); box.appendChild(dl);
      const sh = mk('div', 'position:absolute;height:6px;border-radius:50%;background:rgba(36,23,44,.32);pointer-events:none;display:none', null, 'l6b-walkshadow'); box.appendChild(sh);
      const pc = mk('canvas', 'position:absolute;width:48px;height:48px;image-rendering:pixelated;animation:l6bbob 900ms steps(2) infinite;pointer-events:none;', null, 'l6b-walkpet'); pc.width = 48; pc.height = 48; pc.dataset.ph = '6b:walk_clip'; box.appendChild(pc);
      const info = mk('div', `position:relative;${bi('panel_inset')}padding:4px 0;`, null, 'l6b-info'); p.appendChild(info);
      const row = (tid, icn) => { const r = mk('div', '', null, tid); r.className = 'row'; if (icn) r.appendChild(img(icn, 'position:relative;width:32px;height:32px;flex:0 0 32px')); const t = mk('span', 'position:relative;' + TXT(24, CREAM), '', tid + '-t'); r.appendChild(t); info.appendChild(r); return t; };
      const tSteps = row('l6b-steps'), tTile = row('l6b-tile'), tSh = row('l6b-shards', LB5 + 'icon_shards@3x.png'), tDeco = row('l6b-deco');
      const tg = (what, label, tid) => { const r = mk('div', bi('card'), null, tid); r.className = 'tg'; const c2 = mk('div', 'position:relative;flex:1 1 auto;min-width:0;display:flex;flex-direction:column');
        c2.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), label)); const sub = mk('div', 'position:relative;' + TXT(24, CREAM), '', tid + '-sub'); c2.appendChild(sub); r.appendChild(c2);
        const pill = mk('div', TXT(24, CREAM), '', tid + '-pill'); pill.dataset.css = pill.style.cssText; pill.className = 'pill'; r.appendChild(pill);
        r.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); toggle(what); }); p.appendChild(r); return { sub, pill, r }; };
      const gS = tg('steps', '計步', 'l6b-tg-steps'), gW = tg('wx', '真天氣＋日照', 'l6b-tg-wx');
      p.appendChild(mk('div', 'position:relative;margin:8px 4px 0;' + TXT(24, MINT), '步數只存喺部機・唔開照舊玩', 'l6b-note'));
      OV.parts = { cv, pc, sh, dl, dk: null, tSteps, tTile, tSh, tDeco, gS, gW };
      host.appendChild(el); document.body.classList.add('l6b-on'); RB.dot = false; note('ov', { why }); refresh(); return el;
    }
    const hm = (h) => { const H = Math.floor(h), M = Math.round((h - H) * 60); return H + ':' + String(M === 60 ? 59 : M).padStart(2, '0'); };
    function refresh() {
      const P = OV.parts; if (!P) return; const s = S(), m = RW.summary(s, now()), o = RW.st(s);
      drawPath(P.cv); walkClip(P); decoArt(P);
      P.tSteps.textContent = '今日 ' + m.today + ' 步'; P.tTile.textContent = '第 ' + (m.tile + 1) + '／' + m.pathTiles + ' 格・差 ' + m.toTile + ' 步';
      P.tSh.textContent = '星星碎 ' + m.shards + '／' + m.cap + (m.shards >= m.cap ? '・今日夠晒' : '・再 ' + m.toShard + ' 步');
      const td = o.log.filter(e => RW.dayKey(e.t) === RW.dayKey(now())).map(e => RW.DK[e.k].zh); P.tDeco.textContent = '執到：' + (td.length ? td.join('、') : '未有') + '・收藏 ' + m.got + '／' + RW.DECO.length;
      const setTg = (g, on, sub) => { g.pill.textContent = on ? '開' : '閂'; g.pill.style.cssText = g.pill.dataset.css + ';' + (on ? bi('btn_pri') : bi('btn16_dis')); g.r.dataset.on = on ? '1' : '0'; g.sub.textContent = sub; };
      setTg(P.gS, o.on.steps, o.on.steps ? (NAT() ? '1000 步行 1 格' : '開咗（模擬）') : (NAT() ? '撳一下問權限' : '呢部機冇計步器'));
      const w = o.wx; setTg(P.gW, o.on.wx, o.on.wx ? (w && RW.stale(s, now()) ? WXZ[w.kind] + (w.rise != null ? '・' + hm(w.rise) + '–' + hm(w.set) : '') : '暫時用遊戲天氣') : '用遊戲天氣');
    }

    // ── 花園 rail「散步」掣 ──
    const RB = { el: null, dot: false };
    function railTick() {
      const s = S(), show = s && s.stage !== 'egg' && !document.body.classList.contains('s2-scene'); let el = RB.el;
      if (!el) { if (!show) return; const rail = document.getElementById('hdRail'), host = rail || document.getElementById('top-r'); if (!host) return;
        el = RB.el = mk('div', '', null, 'l6b-rail'); el.id = 'l6bbtn'; el.className = 'ibtn panel'; el.title = '散步';
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l">散步</i><i class="rd"></i>'; el.querySelector('i.i').appendChild(img(B6 + 'ic_walk@3x.png', 'left:0;top:0;width:36px;height:36px'));
        el.addEventListener('click', (e) => { e.stopPropagation(); if (busy()) return; UIS('tap'); openOv('rail'); }); host.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return; const rd = el.querySelector('i.rd'); if (rd) rd.style.display = RB.dot ? '' : 'none';
      const vis = (id) => { const e = document.getElementById(id); return !!(e && e.style.display !== 'none' && e.offsetParent !== null); };
      const st = 1 + (vis('l5egg') ? 1 : 0) + (vis('l5cbtn') ? 1 : 0), u = U(), rl = u && u.rail;
      if (rl && rl.kid && rl.dex) { el.style.left = rl.kid.x + 'px'; el.style.top = (rl.kid.y + st * (rl.kid.y - rl.dex.y)) + 'px'; } else { el.style.left = '360px'; el.style.top = (320 + (st - 1) * 64) + 'px'; }
    }
    // ── 每秒：rail；每 60 秒（前台）：讀計步器／天氣過期再攞 ──
    const T = { last: 0, poll: 0, n: 0 };
    function tick(force) {
      const t = pnow(); if (!force && t - T.last < 1000) return; T.last = t; T.n++; try { railTick(); } catch (e) { }
      if (OV.el) refresh();
      if (AUTO.on && document.visibilityState !== 'hidden' && (force || t - T.poll > 60000)) { T.poll = t; const o = RW.st(S()); if (o.on.steps) readSteps('poll'); if (o.on.wx && !RW.fresh(S(), now())) refreshWx(false); }
    }
    { const loop = () => { try { tick(); } catch (e) { } setTimeout(loop, 500); }; setTimeout(loop, 400); }
    { const anim = () => { try { if (OV.el && OV.parts) walkClip(OV.parts); } catch (e) { } setTimeout(anim, 100); }; setTimeout(anim, 400); }   // walk clip 10fps
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') { T.poll = 0; try { tick(true); } catch (e) { } } });
    if (AUTO.on) setTimeout(() => { natStatus(); tick(true); }, 1500);

    // ── 🛠 開發者模式「6b」 ──
    const wxJ = (code, rise, set) => ({ current: { weather_code: code }, daily: { sunrise: ['2026-11-02T' + rise], sunset: ['2026-11-02T' + set] } });
    const sim = (n) => { const s = S(); const g = RW.credit(s, n, now()); after(g); save(); return { ok: true, msg: '+' + n + ' 步 → 行 ' + g.tiles + ' 格、+' + g.shards + ' 碎' + (g.deco.length ? '、執到 ' + g.deco.map(k => RW.DK[k].zh).join('、') : '') + '（今日 ' + RW.day(s, now()).st + ' 步）' }; };
    const fake = (code, rise, set, label) => { const s = S(); RW.setOn(s, 'wx', true); const w = RW.applyWx(s, wxJ(code, rise, set), now()); save(); refresh(); return { ok: !!w, msg: label + '（只改畫面；計分仍然係' + WXZ[G.weather || 'clear'] + '）' }; };
    const DEV = { id: 'l6b', title: '6b（真世界連動）', order: 46,
      status: () => { const m = RW.summary(S(), now()); return '計步 ' + (m.on.steps ? '開' : '閂') + '・真天氣 ' + (m.on.wx ? (m.wx ? m.wx.kind : '未有') : '閂') + '・今日 ' + m.today + ' 步・碎 ' + m.shards + '／' + m.cap + '・第 ' + (m.tile + 1) + ' 格・原生 ' + (NAT() ? '有' : '冇') + '・自動 ' + (AUTO.on ? '開' : '閂'); },
      items: [
        ['open', '打開散步路', () => { openOv('dev'); return { ok: true, msg: '開咗' }; }],
        ['s1k', '模擬 +1000 步（行 1 格）', () => sim(1000)],
        ['s2k', '模擬 +2000 步（1 粒碎）', () => sim(2000)],
        ['s12k', '模擬 +12000 步（封頂）', () => sim(12000)],
        ['read', '讀一次計步器（原生）', () => { readSteps('dev'); return { ok: !!NAT(), msg: NAT() ? '讀緊' : '冇原生計步器（瀏覽器）' }; }],
        ['rain', '模擬真天氣：落雨', () => fake(63, '06:20', '17:45', '真天氣＝落雨')],
        ['fog', '模擬真天氣：霧', () => fake(45, '06:20', '17:45', '真天氣＝霧')],
        ['clear', '模擬真天氣：晴', () => fake(0, '06:20', '17:45', '真天氣＝晴')],
        ['winter', '模擬日照 7:30–16:30', () => fake(1, '07:30', '16:30', '冬天日照')],
        ['wxnow', '即刻攞真天氣（要位置）', () => { refreshWx(true); return { ok: true, msg: RW.st(S()).on.wx ? '攞緊' : '真天氣未開' }; }],
        ['wxoff', '熄真天氣（返遊戲天氣）', () => { RW.setOn(S(), 'wx', false); save(); refresh(); return { ok: true, msg: '熄咗' }; }],
        ['auto', '自動讀取 開／閂', () => { AUTO.on = !AUTO.on; return { ok: true, msg: AUTO.on ? '開' : '閂' }; }],
        ['reset', '重設 6b（清步數記錄）', () => { RW.reset(S()); save(); refresh(); return { ok: true, msg: '6b 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l6b = { open: openOv, close: closeOv, toggle, readSteps, refreshWx };
    window.__qa = window.__qa || {};
    window.__qa.l6b = {
      art: () => ({ json: !!A6.json, err: A6.err.slice(), loaded: Object.keys(A6.img), fk: fkNow(), has: !!(A6.json && A6.json.pets[fkNow()]), path: PATH.map(p => p.slice()), dir: WK.dir }), artLoad: () => A6load,
      st: () => Object.assign(RW.summary(S(), now()), { auto: AUTO.on, native: !!NAT(), perm: Object.assign({}, PERM), ov: !!OV.el, rail: !!(RB.el && RB.el.style.display !== 'none'), dot: RB.dot, wxs: Object.assign({}, WXS),
        visWx: G.visWeather(G.weather), gameWx: G.weather || 'clear', hour: G.hour ? G.hour() : null, visHour: G.hour ? G.visHour(G.hour()) : null }),
      raw: () => JSON.parse(JSON.stringify(RW.st(S()))), log: () => log.slice(), toasts: () => toasts.slice(), dev: () => DEV, tick, open: openOv, close: closeOv, toggle, readSteps, refreshWx, refresh,
      feed: (raw, boot) => { const g = RW.ingest(S(), raw, boot || 1, now()); after(g); save(); return g; }, credit: (n) => { const g = RW.credit(S(), n, now()); after(g); save(); return g; },
      force: (what, v) => { RW.setOn(S(), what, v); save(); refresh(); return RW.st(S()).on; }, wx: (j) => { const w = RW.applyWx(S(), j, now()); refresh(); return w; }, auto: (v) => { AUTO.on = !!v; return AUTO.on; },
    };
    note('install', { auto: AUTO.on, native: !!NAT() });
    return true;
  }
  return { install };
});
