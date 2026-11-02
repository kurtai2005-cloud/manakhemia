/* 《微光小圃》 long6aui.js — 第 6 批 6a「團絨記得你」介面（遊策 breakthrough-6a6d-spec §6a）。原創代碼。
   邏輯全部喺 long6a.js（s.mem6）；呢度只做：
   ・記錄：開 app／返前台（≥20 分鐘當新一次）／過咗午夜；照顧（sim care hook＋摸頭）、食咗乜（G.sysFed）、小遊戲（sys12b.gameFinish）、
     訪客（visit.startVisit）、細佬大事（每秒快照比較）
   ・講出口：每日第一次開 game → 招呼 1 句（等冇彈窗／小遊戲／重逢先講）；系統 3 日記每日自動加 1 句（擺喺收尾句前面；今日草稿預覽）；
     心聲泡泡：心聲成功出泡時 50% 換成記憶句（每日最多 2 句）。三處共用「7 日內唔重複」。浮動團絨唔改。
   ・冇嚟：1 日／2 日／3 日以上句；冇懲罰；返嚟第一下撳 → 特別開心（g_tickle＋心心＋得意表情；純視覺，唔郁數值／路線分）
   ・表情疊層：得意／委屈 → 6a.1 遊美 per_pet 圖（art/breakthrough/6a/faces6a.json，49 隻形態，key smug6a／pout6a；renderer 疊喺 idle 幀 0 上、眼鏡／帽之下）；冇圖嘅形態（蛋、細佬 S 線）→ 程序畫 placeholder（洋紅虛線框＋data-ph）
   ・🛠 開發者模式「6a」；?l6a=0 全停（唔記錄、唔講）；webdriver 下自動招呼／記憶心聲預設閂（?l6a=1 開），?ev=0 唔自動講。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6aui = factory(root.Glimmer); }
})(typeof self !== 'undefined' ? self : this, function (NS0) {
  'use strict';
  // 開機 applyOffline 會將 lastSeen 推到而家 → 喺 offline hook 先記低上次嚟（5c 舊存檔升級用）
  const BOOT = { from: 0 };
  try { if (NS0 && NS0.sim && NS0.sim.addOfflineHook) NS0.sim.addOfflineHook((s, i) => { if (i && +i.from > 0 && !BOOT.from) BOOT.from = +i.from; }); } catch (e) { }

  function install(G, NS) {
    const M = NS.long6a, X = NS.sys12, X2 = NS.sys12b, UI = NS.ui, D = NS.data, SIM = NS.sim; if (!M || !X || !UI || !SIM || !D) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l6a') === '0') return false;
    const wd = !!(navigator && navigator.webdriver), QUIET = qs.get('ev') === '0';
    const AUTO = { on: qs.get('l6a') === '1' || !wd };
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now();
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const P = D.PARAMS || {};
    const GN = { catch: '接光點', hide: '捉迷藏' };
    const names = {
      food: (id) => { const f = (D.FOODS || []).find(x => x.id === id); return f ? f.name : null; },
      game: (k) => GN[k] || (P.minigames2 && P.minigames2[k] && P.minigames2[k].name) || null,
      visitor: (v) => v,
    };
    const MOOD = new Map();   // 句 → 's'（得意）／'p'（委屈）

    // ── 記錄 ──
    const st0 = S(); const v0 = M.visit(st0, now(), { lastSeen: BOOT.from || null }); note('boot', v0);
    let lastKey = M.dayKey(now()), bootAt = pnow();
    document.addEventListener('visibilitychange', () => { if (document.visibilityState !== 'visible') return; const v = M.visit(S(), now()); lastKey = v.day; note('vis', v); save(); });
    SIM.addCareHook((s, kind) => { if (s === S()) try { M.note(s, 'care', kind, 0, 0, 0, now()); } catch (e) { } });
    { const f0 = X.notePat; X.notePat = function (s) { const r = f0.apply(this, arguments); try { if (r && s === S()) M.note(s, 'care', 'pat', 0, 0, 0, now()); } catch (e) { } return r; }; }
    { const f0 = G.sysFed; G.sysFed = function (id) { const r = f0 ? f0.apply(this, arguments) : undefined; try { M.note(S(), 'food', id, 0, 0, 0, now()); } catch (e) { } return r; }; }
    if (X2 && X2.gameFinish) { const f0 = X2.gameFinish; X2.gameFinish = function (s, kind, v) { let prev = 0; try { prev = +((X2.st(s).games.best || {})[kind]) || 0; } catch (e) { }
      const r = f0.apply(this, arguments); try { if (s === S()) M.note(s, 'game', kind, +v || 0, r && r.stars | 0, (+v || 0) > prev && prev > 0 ? 1 : 0, now()); } catch (e) { } return r; }; }
    if (NS.visit && NS.visit.startVisit) { const f0 = NS.visit.startVisit; NS.visit.startVisit = function (s) { const r = f0.apply(this, arguments); try { if (r && r.ok && s === S()) M.note(s, 'visitor', r.name || r.who, 0, 0, 0, now()); } catch (e) { } return r; }; }
    function kidEnv(s) {
      const SR = NS.series2, FAM = NS.long5a, B = NS.long5b, e = { ph: 'none', gen: s.gen || 1 };
      try { if (SR) { const p = SR.st(s); e.ph = p.phase; if (p.phase === 'kid') { e.kst = SR.stageOf(s, now()); e.kstZh = SR.STAGE_ZH[e.kst] || ''; e.les = (p.lessons || []).length; } e.name = FAM && FAM.kidName ? FAM.kidName(p.line) : '細佬'; } } catch (x) { }
      try { if (FAM) { const F = FAM.st(s); e.res = F.res.length; e.lv = F.lv; const r = F.res[F.res.length - 1]; if (r) e.resName = r.name; } } catch (x) { }
      try { if (B) { const o = B.st(s); e.trips = o.n.trips; const t = o.trips[o.trips.length - 1]; if (t && t.name) e.tripName = t.name; } } catch (x) { }
      return e;
    }

    // ── 日記：已寫好嘅篇加 1 句（收尾句前）；今日草稿預覽 ──
    const hashS = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h; };
    const rngOf = (seed) => { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
    const dia0 = X.diary;
    function annotate() {
      const s = S(); if (!s || s.stage === 'egg') return 0; let n = 0; const L = dia0(s, now()).list;
      for (const e of L) { if (e.m6 || !Array.isArray(e.lines) || !e.lines.length || !M.rec(s, e.d)) continue;
        const pk = M.diaryPick(s, e.d, now(), { names, rng: rngOf(hashS('d6:' + e.d + ':' + (s.seed | 0))) });
        if (!pk) { e.m6 = '-'; continue; } M.commit(s, pk, 'diary', now()); e.lines.splice(e.lines.length - 1, 0, pk.line); e.m6 = pk.id; MOOD.set(pk.line, pk.mood); n++; note('diary', { d: e.d, id: pk.id }); }
      if (n) save(); return n;
    }
    const PV = { key: null, pk: null };
    X.diary = function (s, nowMs) {
      const d = dia0.apply(this, arguments); try {
        if (d && d.today && s === S() && s.stage !== 'egg') { const k = M.dayKey(nowMs), r = M.rec(s, k);
          if (r) { const key = k + ':' + JSON.stringify(r).length; if (PV.key !== key) { PV.key = key; PV.pk = M.diaryPick(s, k, nowMs, { names, rng: rngOf(hashS('d6:' + k + ':' + (s.seed | 0))) }); }
            if (PV.pk && Array.isArray(d.today.lines) && d.today.lines.length) { d.today.lines = d.today.lines.slice(); d.today.lines.splice(d.today.lines.length - 1, 0, PV.pk.line); d.today.m6 = PV.pk.id; } } }
      } catch (e) { } return d;
    };

    // ── 心聲：成功出泡 → 50% 換記憶句（每日最多 2；同招呼／日記共用 7 日唔重複） ──
    const vt0 = X.voiceTry;
    X.voiceTry = function (s, nowMs, o) {
      const r = vt0.apply(this, arguments); o = o || {};
      try { if (!r || !r.ok || s !== S() || o.mem6 === false || !(o.mem6 || (AUTO.on && !QUIET))) return r;
        const pk = M.voicePick(s, nowMs, { names, force: o.mem6 === 'force', rng: o.rng }); if (!pk) return r;
        const b = X.bondOf(s); if (b.heard[b.heard.length - 1] === r.line) b.heard.pop();   // 記憶句唔佔心聲收集
        r.tierLine = r.line; r.line = pk.line; r.src = 'mem6'; r.mem = pk; delete r.icon; MOOD.set(pk.line, pk.mood); note('voice', { id: pk.id }); save();
      } catch (e) { } return r;
    };

    // ── 樣式＋表情疊層 ──
    const css = document.createElement('style'); css.id = 'l6acss';
    css.textContent = `#ui #s12voice[data-src="mem6"]{font:24px/28px ${(G.v3 && G.v3.want) ? '"GlimmerV3Sans"' : '"GlimmerFP12"'},"Noto Sans HK","Noto Sans CJK TC",sans-serif !important;max-width:300px;white-space:normal}
#l6aface{position:absolute;width:48px;height:48px;z-index:31;pointer-events:none;display:none;image-rendering:pixelated;transition:opacity 160ms}
#l6aface[data-ph]{outline:2px dashed #FF2BD6;outline-offset:1px}
#l6aface canvas,#l6aface img{width:48px;height:48px;image-rendering:pixelated;display:block}
.l6aheart{position:absolute;width:32px;height:32px;z-index:31;pointer-events:none;image-rendering:pixelated;animation:l6ah 1.1s ease-out forwards}
@keyframes l6ah{0%{transform:translateY(0) scale(.6);opacity:0}20%{opacity:1}100%{transform:translateY(-70px) scale(1.1);opacity:0}}`;
    document.head.appendChild(css);
    const host = () => document.getElementById('ui') || document.body;
    const FACE = { el: null, kind: null, until: 0, mode: null, why: '', fk: null, bub: null, ph: {} };
    // 6a.1 遊美表情（art/breakthrough/6a，FACES_6A.md）：49 隻形態逐隻 per_pet/<pet>/face_{smug,pout}.png，全幀 patch（同該形態 idle 幀 0 一樣大、左上對齊）。
    // 引擎 key：smug6a／pout6a（3a reactions 已經有 smug＝扮醒，唔撞）。由 renderer（團絨）／s2ui（細佬做主養）喺 body transform 之前蓋：base→表情→眼鏡／帽。
    // 預設 face_*.png 只啱 evo_still_radiant → 唔用嚟頂其他形態；形態冇圖（例如蛋、S1／S2）→ 照舊 placeholder 疊層。
    const F6 = { base: 'art/breakthrough/6a/', json: null, img: {}, want: {}, err: [] };
    function f6fk() { const s = S(); if (s.stage === 'egg') return null; if (s.fam && s.fam.km && s.fam.km.fk) return s.fam.km.fk; try { return G.renderer && G.renderer.fkOf ? G.renderer.fkOf(s) : null; } catch (e) { return null; } }
    function f6img(fk, kind) {            // 有圖就 {img,fw,fh,key}；未載 → lazy 載入、回 null
      const p = F6.json && F6.json.pets[fk], f = p && p.files[kind] && p.files[kind]['1x']; if (!f) return null; const id = fk + ':' + kind;
      if (F6.img[id]) return { img: F6.img[id], fw: p.frameSize[0], fh: p.frameSize[1], key: kind + '6a', fk };
      if (!F6.want[id]) { F6.want[id] = 1; const i = new Image(); i.onload = () => { if (i.naturalWidth) F6.img[id] = i; }; i.onerror = () => F6.err.push(f); i.src = F6.base + f; }
      return null;
    }
    const f6has = (fk) => !!(fk && F6.json && F6.json.pets[fk]);
    const F6load = fetch(F6.base + 'faces6a.json').then(r => r.ok ? r.json() : null).then(j => { if (j && j.pets) { F6.json = j; const fk = f6fk(); if (fk) { f6img(fk, 'smug'); f6img(fk, 'pout'); } } }).catch(e => F6.err.push(String(e && e.message || e)));
    if (G.renderer) G.renderer.face6a = { get: (fk) => (FACE.kind && FACE.mode === 'art' && pnow() <= FACE.until) ? f6img(fk, FACE.kind) : null };
    // placeholder（16×16 art px → 48 CSS px）：奶油圓面＋墨色五官；得意＝瞇眼＋歪嘴笑＋閃星；委屈＝八字眉＋淚眼＋波浪嘴＋水滴
    function phCanvas(kind) {
      if (FACE.ph[kind]) return FACE.ph[kind];
      const c = document.createElement('canvas'); c.width = 16; c.height = 16; const g = c.getContext('2d'); const px = (x, y, col) => { g.fillStyle = col; g.fillRect(x, y, 1, 1); };
      const INK = '#24172C', CR = '#FFF5DC', PK = '#F59BB0', BL = '#7EC8F0', GD = '#FFE08A';
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const d = Math.hypot(x - 7.5, y - 8); if (d < 7.2) px(x, y, d > 6.2 ? INK : CR); }
      if (kind === 'smug') {
        [[4, 7], [5, 6], [6, 7], [9, 7], [10, 6], [11, 7]].forEach(([x, y]) => px(x, y, INK));        // ^ ^
        [[6, 11], [7, 11], [8, 11], [9, 10], [10, 9]].forEach(([x, y]) => px(x, y, INK));              // 歪嘴笑
        px(3, 9, PK); px(4, 9, PK); px(11, 9, PK); px(12, 9, PK);
        [[13, 1], [13, 3], [12, 2], [14, 2], [13, 2]].forEach(([x, y]) => px(x, y, GD));               // 閃星
      } else {
        [[4, 5], [5, 6], [11, 5], [10, 6]].forEach(([x, y]) => px(x, y, INK));                         // 八字眉
        [[5, 8], [10, 8]].forEach(([x, y]) => { px(x, y, INK); px(x, y + 1, BL); });                  // 淚眼
        [[5, 12], [6, 11], [7, 12], [8, 11], [9, 12], [10, 11]].forEach(([x, y]) => px(x, y, INK));     // 波浪嘴
        px(12, 10, BL); px(12, 11, BL); px(13, 11, BL); px(12, 12, BL);                                 // 水滴
      }
      FACE.ph[kind] = c; return c;
    }
    function faceEl() {
      if (FACE.el && FACE.el.isConnected) return FACE.el; const e = document.createElement('div'); e.id = 'l6aface'; e.dataset.testid = 'l6a-face'; host().appendChild(e); FACE.el = e; return e;
    }
    function petBox() { try { return UI.petHitBox ? UI.petHitBox() : null; } catch (e) { return null; } }
    function placeFace() {
      const e = FACE.el; if (!e || e.style.display === 'none') return; const b = petBox(); if (!b) return; const body = b.body || b;
      const x = Math.max(4, Math.min(390 - 52, (body.x + body.w) * 2 - 14)), y = Math.max(96, body.y * 2 - 30); e.style.left = x + 'px'; e.style.top = y + 'px';
    }
    function showFace(kind, ms, why) {
      if (kind !== 'smug' && kind !== 'pout') return null; const fk = f6fk(); FACE.kind = kind; FACE.until = pnow() + (ms || 1600); FACE.why = why || ''; FACE.fk = fk;
      if (f6has(fk)) { FACE.mode = 'art'; f6img(fk, kind); if (FACE.el) FACE.el.style.display = 'none'; note('face', { kind, why, key: kind + '6a', fk }); return kind; }
      FACE.mode = 'ph'; const e = faceEl(); e.innerHTML = ''; const c = document.createElement('canvas'); c.width = 16; c.height = 16; c.getContext('2d').drawImage(phCanvas(kind), 0, 0); e.appendChild(c); e.dataset.ph = '6a:face_' + kind;
      e.dataset.kind = kind; e.dataset.why = why || ''; e.style.display = 'block'; e.style.opacity = 1; placeFace(); note('face', { kind, why, ph: true }); return kind;
    }
    function hideFace() { if (FACE.el) { FACE.el.style.display = 'none'; } FACE.kind = null; FACE.until = 0; FACE.mode = null; }
    function faceTick() {
      const vb = document.getElementById('s12voice'); const memOn = vb && vb.dataset.src === 'mem6' && +vb.style.opacity > 0;
      if (memOn) { const t = (vb.querySelector('span') || vb).textContent, mo = MOOD.get(t); const k = mo === 'p' ? 'pout' : 'smug'; if (FACE.bub !== t) { FACE.bub = t; showFace(k, 1800, 'bubble'); } } else FACE.bub = null;   // 每句講一次、1.8 秒後返 idle（FACES_6A：1200–1800ms）
      if (FACE.kind && pnow() > FACE.until) hideFace(); else placeFace();
    }
    { const loop = () => { try { faceTick(); } catch (e) { } requestAnimationFrame(loop); }; requestAnimationFrame(loop); }

    // ── 講：招呼 ──
    const busy = () => (UI.isModalOpen && UI.isModalOpen()) || !!G.mg2Busy || !!G.reunionPending || ['l5ov', 'l5bov', 'l5cov'].some(id => document.getElementById(id)) ||
      document.body.classList.contains('s2-scene') || !!(S().evs && S().evs.active) || (UI.mgState && UI.mgState() && UI.mgState().on);
    function say(pk, why) { if (!pk || !G.say) return null; MOOD.set(pk.line, pk.mood); const r = G.say({ line: pk.line, src: 'mem6', sec: 6, urgent: true }); note('say', { why, id: pk.id }); return r; }
    function greetNow(force) {
      const s = S(); const pk = M.greet(s, now(), { names, force: !!force }); if (!pk) return null; say(pk, 'greet');
      s.ev.push({ type: 'l6a', what: 'greet', id: pk.id, line: pk.line }); save(); return pk;
    }
    const TK = { n: 0, last: 0 };
    function tick() {
      const s = S(); if (!s) return; TK.n++;
      const k = M.dayKey(now()); if (k !== lastKey) { const v = M.visit(s, now()); lastKey = k; note('day', v); }
      try { const ev = M.scanKid(s, kidEnv(s), now()); if (ev.length) note('kid', { ev: ev.map(e => e[0]) }); } catch (e) { }
      annotate();
      if (AUTO.on && !QUIET && pnow() - bootAt > 2500 && !s.sleeping && M.greetDue(s, now()) && !busy()) greetNow(false);
    }
    setInterval(() => { try { tick(); } catch (e) { note('err', { e: String(e) }); } }, 1000);

    // ── 冇嚟返嚟：第一下撳特別開心（純視覺） ──
    function happy(why) {
      try { if (G.touchPlay) setTimeout(() => G.touchPlay('g_tickle'), 60); } catch (e) { }
      showFace('smug', 1600, why || 'happy'); UIS('medal');
      const b = petBox(); if (b) { const body = b.body || b, cx = (body.x + body.w / 2) * 2, cy = body.y * 2;
        for (let i = 0; i < 4; i++) { const h = new Image(); h.className = 'l6aheart'; h.alt = ''; h.dataset.testid = 'l6a-heart'; h.src = 'art/systems12/sticker_heart.png'; h.style.left = (cx - 16 + (i - 1.5) * 26) + 'px'; h.style.top = (cy + 10 - (i % 2) * 14) + 'px'; h.style.animationDelay = (i * 90) + 'ms'; host().appendChild(h); setTimeout(() => h.remove(), 1400 + i * 90); } }
      S().ev.push({ type: 'l6a', what: 'happy' }); note('happy', { why }); return true;
    }
    // 6a.1（遊測 P1）：返嚟第一下撳＝純視覺。ui.js 撳落團絨時先問 G.petTapGate：特別開心等緊 → 成個手勢（按落＋鬆手）唔跑觸摸手勢（mood grant）、
    // 唔跑 G.sysPress（摸頭委託／親密／心聲）、唔記 mem6 摸頭；只播 g_tickle＋心心＋得意臉，播完先 takeHappy。
    G.petTapGate = function () { try { const s = S(), t = now(); if (!M.happyDue(s, t)) return false; happy('tap'); M.takeHappy(s, t); save(); return true; } catch (e) { return false; } };

    // ── 🛠 開發者模式「6a」 ──
    const DAY = 864e5;
    function fillDay(key, o) {
      const s = S(), m = M.st(s); o = o || {}; const r = m.d[key] = { o: [o.from != null ? o.from : 19 * 60, o.to != null ? o.to : 23 * 60 + 5], n: o.n || 2, c: { feed: 2, play: 1, pat: 3 }, f: { meal: 1, cookie: 1 }, g: { bounce: [31, 3, 1] }, vi: ['蝸牛郵差'], k: [['hatch', '細佬', '']], gap: 0 };
      return r;
    }
    function setupYday(gap) {
      const s = S(), m = M.st(s), t = now(), k = M.dayKey(t), pk = M.dayKey(t - (gap + 1) * DAY);
      fillDay(pk); m.last = pk; m.prev = pk; m.greet = null; if (m.d[k]) { m.d[k].gap = gap; } else M.visit(s, t, { session: false });
      m.d[k].gap = gap; m.happy = gap >= 1 ? k : null; for (let i = 1; i <= gap; i++) delete m.d[M.dayKey(t - i * DAY)]; return pk;
    }
    const DEV = { id: 'l6a', title: '6a（團絨記得你）', order: 45,
      status: () => { const m = M.summary(S(), now()); return '記錄 ' + m.days + ' 日・' + (M.sizeBytes(S()) / 1024).toFixed(1) + 'KB・上次 ' + (m.prev || '—') + '・冇嚟 ' + m.gap + ' 日・7 日內講過 ' + m.said7 + ' 句・特別開心 ' + (m.happy ? '等緊' : '—') + '・自動講 ' + (AUTO.on && !QUIET ? '開' : '閂'); },
      items: [
        ['yday', '填「琴日」記錄（23:05 先走、食咗、彈彈葉破紀錄、訪客、細佬孵化）', () => { const pk = setupYday(0); save(); return { ok: true, msg: '琴日＝' + pk }; }],
        ['greet', '今日第一次開 game（講招呼）', () => { const s = S(); if (!M.st(s).prev) setupYday(0); M.st(s).greet = null; const pk = greetNow(true); return pk ? { ok: true, msg: pk.line } : { ok: false, msg: '冇句講（蛋／細佬做主角？）' }; }],
        ['abs1', '冇嚟 1 日 → 返嚟（招呼＋第一下撳特別開心）', () => { setupYday(1); const pk = greetNow(true); return pk ? { ok: true, msg: pk.line } : { ok: false, msg: '冇句講' }; }],
        ['abs3', '冇嚟 3 日 → 返嚟', () => { setupYday(3); const pk = greetNow(true); return pk ? { ok: true, msg: pk.line } : { ok: false, msg: '冇句講' }; }],
        ['voice', '心聲（記憶句）', () => { const s = S(), td = M.today(s, now()); if (!Object.keys(td.c).length && !Object.keys(td.f).length) { td.c.feed = 2; td.c.pat = 2; td.f.soup = 1; } const m = M.st(s); if (m.vday === M.dayKey(now())) m.vn = 0; const r = G.sysVoice ? G.sysVoice({ force: true, src: 'dev', mem6: 'force' }) : null; return r && r.ok && r.src === 'mem6' ? { ok: true, msg: r.line } : { ok: false, msg: r && r.ok ? '冇記憶句（7 日內講晒）→ 普通心聲' : '講唔到（' + (r && r.why) + '）' }; }],
        ['diary', '寫日記句（琴日一篇）', () => { const s = S(), k = M.dayKey(now() - DAY), L = dia0(s, now()).list, e = L.find(x => x.d === k); if (!e) { const tr = X.diaryTrack(s, now(), s.ev); tr.day = k; tr.done = false; tr.n = Math.max(tr.n || 0, 2); X.diaryTrack(s, now(), s.ev); }
          if (!M.rec(s, k)) fillDay(k); const n = annotate(); const e2 = dia0(s, now()).list.find(x => x.d === k); return e2 && e2.m6 ? { ok: true, msg: (n ? '寫咗：' : '已有：') + (M.BYID[e2.m6] ? e2.lines[e2.lines.length - 2] : '—') } : { ok: false, msg: '寫唔到' }; }],
        ['smug', '表情疊層：得意（預覽 3 秒）', () => ({ ok: true, msg: showFace('smug', 3000, 'dev') + (FACE.mode === 'art' ? '（smug6a・' + FACE.fk + '）' : '（placeholder）') })],
        ['pout', '表情疊層：委屈（預覽 3 秒）', () => ({ ok: true, msg: showFace('pout', 3000, 'dev') + (FACE.mode === 'art' ? '（pout6a・' + FACE.fk + '）' : '（placeholder）') })],
        ['happy', '特別開心（第一下撳）預覽', () => ({ ok: happy('dev'), msg: '開心反應' })],
        ['fill30', '填滿 30 日記錄（測大細）', () => { const s = S(), t = now(); for (let i = 0; i < 30; i++) fillDay(M.dayKey(t - i * DAY), { n: 9 }); M.prune(s, t); save(); return { ok: true, msg: Object.keys(M.st(s).d).length + ' 日・' + (M.sizeBytes(s) / 1024).toFixed(1) + 'KB' }; }],
        ['auto', '自動招呼／記憶心聲 開／閂', () => { AUTO.on = !AUTO.on; return { ok: true, msg: AUTO.on ? '開' : '閂' }; }],
        ['reset', '重設 6a（清 30 日記錄）', () => { M.reset(S()); hideFace(); PV.key = null; save(); return { ok: true, msg: '6a 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l6a = { greet: greetNow, happy, face: showFace, annotate };
    window.__qa = window.__qa || {};
    window.__qa.l6a = {
      st: () => Object.assign(M.summary(S(), now()), { auto: AUTO.on, quiet: QUIET, face: FACE.kind, faceMode: FACE.mode, faceKey: FACE.kind ? FACE.kind + '6a' : null, faceFk: FACE.fk, faceArt: { json: !!F6.json, pets: F6.json ? Object.keys(F6.json.pets).length : 0, loaded: Object.keys(F6.img).length, err: F6.err.slice(0, 3) }, facePh: (FACE.mode === 'ph' && FACE.el) ? FACE.el.dataset.ph || null : null, ticks: TK.n, bytes: M.sizeBytes(S()), boot: v0, bootFrom: BOOT.from }),
      raw: () => JSON.parse(JSON.stringify(M.st(S()))), log: () => log.slice(), dev: () => DEV, tick, greet: greetNow, happy, face: showFace, hideFace, annotate, auto: (v) => { AUTO.on = !!v; return AUTO.on; },
      setupYday, fillDay, mood: (t) => MOOD.get(t) || null, lines: () => M.ALL.map(L => L.t), visit: (o) => M.visit(S(), now(), o || {}),
    };
    note('install', { auto: AUTO.on, quiet: QUIET });
    return true;
  }
  return { install };
});
