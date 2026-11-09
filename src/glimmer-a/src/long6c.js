/* 《微光小圃》 long6c.js — 第 6 批 6c「夢境探險」（遊策 breakthrough-6a6d-spec §6c）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.dream6（sanitize）。唔加月眠／任何路線分、唔出碎、唔郁需求數值、唔郁系統 6 親密度。
   ・入夢：團絨瞓緊（s.sleeping）＋遊戲鐘 21:00–03:00（6d A：19:00 後上線都計 → 19:00–03:00）＋唔係蛋／唔係細佬做主養 → 每晚 1 次（「一晚」＝21:00 嗰日；00:00–03:00 計返前一日）。
     6d B：錯過咗嘅一晚存 1 個，下次上線（瞓緊；6d.1 夜晚都得，先補後入當晚）補做。
     入夢嗰刻已經用咗今晚（中途閂 app 都唔可以再入；已拾嘅碎片即時入帳，唔會冇咗）。
   ・夢長：150 秒（＋入／出夢過場各 1.2 秒），硬上限 180 秒（每晚 ≤3 分鐘）。
   ・直向小地圖 3×5 格（i＝行×3＋列，行 0＝頂），由當晚 6a 記錄（s.mem6；21:00 嗰日＋過咗午夜嗰日加埋）砌：
       餵菇（暖菇飯 meal）→ 蘑菇森林 forest；6d C：餵食／淋水／執便便／小遊戲 各 +1 → 水珠湖 lake；玩耍＋小遊戲 → 玩具房 toy（修2b 冇門檻、最少 1）；夜晚嚟 → 星空 star（入得夢一定係夜晚嚟，永遠有）。
     每個主題最少 2 格，其餘按次數（每項最多計 4）比例分；由底（起點＝底行中間）蛇形排上去，星空喺最頂。
   ・夢碎片（6d）：每晚 1 片、20% 多 1 片（第 2 片 40 秒浮出）；按主題權重抽，齊 5 張嘅主題唔再抽（修1）；四主題齊 → 冇片。
     夢碎片唔係貨幣：每個主題每 5 片砌 1 張夢圖鑑（每主題 5 張，首批 20 張）；砌齊一個主題 5 張 → 送家具 1 件（5a「擺設」池）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./long6a.js'), require('./long5a.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6c = factory(root.Glimmer.long6a, root.Glimmer.long5a); }
})(typeof self !== 'undefined' ? self : this, function (M6, FAM) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const int = (v, d) => Number.isFinite(+v) ? Math.floor(+v) : d;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  /* 6d（遊策 6c 夢境平衡 A／B／C＋修1＋修2b）：
     A 窗口 21:00–03:00；當晚最後一次上線喺 19:00 後開始都計（lateFrom 19 → 19:00–03:00 瞓緊入得），每晚最多 1 次。
     B 錯過咗嘅一晚存 1 個（bankCap 1），下次上線（瞓緊；6d.1：夜晚窗口內外都得，有存先補）補做；補做唔佔當晚，補完同一次上線仍可入當晚。
     C 水珠湖權重＝餵食／淋水／執便便／小遊戲 各 +1。
     片數：每晚 1 片，20% 再多 1 片（湖片都喺同一個額度）；修1 主題 5 張齊 → 權重 0（唔再出嗰主題嘅片）；修2b 玩具房冇門檻、最低權重 1。
     夢碎片唔入錢包／唔計 47 碎上限。 */
  const CFG = { hours: [21, 3], lateFrom: 19, bankCap: 1, cols: 3, rows: 5, start: 13, durSec: 150, fadeSec: 1.2, maxSec: 180, frags: 2, frag2: 0.2, spawnAt: [0, 40], perCard: 5, cardsPerTheme: 5,
    minTiles: 2, wMax: 4, keepLog: 14 };
  const THEMES = ['forest', 'lake', 'toy', 'star'];
  const TH = {
    forest: { zh: '蘑菇森林', why: '餵咗暖菇飯', furn: 'sv_mushroom' },
    lake: { zh: '水珠湖', why: '幫佢淋咗水', furn: 'sv_shell' },
    toy: { zh: '玩具房', why: '陪佢玩得多', furn: 'sv_rainbow' },
    star: { zh: '星空', why: '夜晚嚟咗', furn: 'sv_starstone' },
  };
  /* 夢圖鑑首批 20 張（每主題 5 張，按次序解鎖；id 唔好改） */
  const CARDS = [
    ['f1', 'forest', '會唱歌嘅菇'], ['f2', 'forest', '菇傘下避雨'], ['f3', 'forest', '森林博士上堂'], ['f4', 'forest', '巨型暖菇飯'], ['f5', 'forest', '菇菇捉迷藏'],
    ['l1', 'lake', '水珠浮浮'], ['l2', 'lake', '湖底月光'], ['l3', 'lake', '游水冠軍'], ['l4', 'lake', '雨點合唱團'], ['l5', 'lake', '倒影另一隻我'],
    ['t1', 'toy', '積木城堡'], ['t2', 'toy', '發條團絨'], ['t3', 'toy', '波波池'], ['t4', 'toy', '玩具火車'], ['t5', 'toy', '拼圖少一塊'],
    ['s1', 'star', '數星星'], ['s2', 'star', '流星許願'], ['s3', 'star', '月亮韆鞦'], ['s4', 'star', '團絨星座'], ['s5', 'star', '銀河散步'],
  ].map(([id, th, zh]) => ({ id, th, zh }));
  const CK = Object.fromEntries(CARDS.map(c => [c.id, c]));
  const DAY = 86400e3;
  const dayKey = (t) => M6.dayKey(t);
  const hourOf = (t) => { const d = new Date(t); return d.getHours() + d.getMinutes() / 60; };
  const inHours = (h) => h >= CFG.hours[0] || h < CFG.hours[1];
  const inLate = (h) => h >= CFG.lateFrom || h < CFG.hours[1];   // A：19:00 後開始嘅上線都計
  /* 「今晚」：21:00 嗰日（鐘數 < 12 → 前一日） */
  function nightKey(now, h) { if (h == null) h = hourOf(now); const k = dayKey(now); return h < 12 ? M6.dayKeyOfDn(M6.dn(k) - 1) : k; }

  function st(s) {
    let o = s.dream6; if (!obj(o)) o = s.dream6 = {};
    o.v = 1;
    if (o.night != null && !/^\d{4}-\d\d-\d\d$/.test(o.night)) o.night = null; if (o.night === undefined) o.night = null;
    if (!obj(o.frag)) o.frag = {}; for (const k of Object.keys(o.frag)) if (!TH[k]) delete o.frag[k]; for (const k of THEMES) o.frag[k] = Math.max(0, Math.min(9999, int(o.frag[k], 0)));
    if (!obj(o.cards)) o.cards = {}; for (const k of Object.keys(o.cards)) if (!CK[k]) delete o.cards[k]; else o.cards[k] = int(o.cards[k], 1) || 1;
    if (!obj(o.furn)) o.furn = {}; for (const k of Object.keys(o.furn)) if (!TH[k] || typeof o.furn[k] !== 'string') delete o.furn[k];
    if (!Array.isArray(o.log)) o.log = []; o.log = o.log.filter(e => obj(e) && /^\d{4}-\d\d-\d\d$/.test(e.d)).slice(-CFG.keepLog).map(e => ({ d: e.d, got: Math.max(0, Math.min(CFG.frags, int(e.got, 0))), sec: Math.max(0, Math.min(CFG.maxSec, int(e.sec, 0))), th: Array.isArray(e.th) ? e.th.filter(k => TH[k]).slice(0, 4) : [] }));
    if (!obj(o.n)) o.n = {}; for (const k of ['dreams', 'frags', 'cards', 'furn', 'bank']) o.n[k] = Math.max(0, int(o.n[k], 0));
    const DK = (v) => (typeof v === 'string' && /^\d{4}-\d\d-\d\d$/.test(v) ? v : null);
    o.bank = Math.max(0, Math.min(CFG.bankCap, int(o.bank, 0))); o.bankNight = DK(o.bankNight); o.bankDone = DK(o.bankDone); o.since = DK(o.since); if (!o.bankNight) o.bank = 0;
    for (const k of Object.keys(o)) if (!['v', 'night', 'frag', 'cards', 'furn', 'log', 'n', 'bank', 'bankNight', 'bankDone', 'since'].includes(k)) delete o[k];
    return o;
  }
  const kidMain = (s) => !!(s && s.fam && s.fam.km);
  /* B：最近一晚（窗口已完）冇入過夢 → 存 1 個（上限 bankCap；第一次見嗰晚之前唔計；o.since＝已判到邊晚） */
  function lastEnded(now, h) { if (h == null) h = hourOf(now); return M6.dayKeyOfDn(M6.dn(dayKey(now)) - (h < CFG.hours[1] ? 2 : 1)); }
  function accrue(s, now, h) {
    const o = st(s); if (!s || s.stage === 'egg' || kidMain(s)) return o; const L = lastEnded(now, h);
    if (!o.since) { o.since = L; return o; } if (L <= o.since) return o;
    /* 6d.1：由上次判到嗰晚之後逐晚判（最多 30 晚），存最早嗰個冇入過嘅一晚 —— 中間嘅空日唔會蓋過真正錯過嗰晚；
       每晚只判一次（o.night 只記最近一晚；入咗今晚之後再 accrue 唔會當琴晚錯過） */
    for (let dn = Math.max(M6.dn(o.since) + 1, M6.dn(L) - 29); dn <= M6.dn(L) && o.bank < CFG.bankCap; dn++) { const k = M6.dayKeyOfDn(dn);
      if (o.night !== k && o.bankDone !== k && o.bankNight !== k) { o.bank++; o.bankNight = k; } }
    o.since = L;
    return o;
  }
  /* 入唔入到夢：{ ok, why }（why：egg／km／awake／hours／done；ok／bank） */
  function canEnter(s, now, h) {
    if (h == null) h = hourOf(now);
    if (!s || s.stage === 'egg') return { ok: false, why: 'egg' }; if (kidMain(s)) return { ok: false, why: 'km' };
    if (!s.sleeping) return { ok: false, why: 'awake' };
    const o = accrue(s, now, h);
    if (o.bank > 0) return { ok: true, why: 'bank', night: o.bankNight };   // 6d.1 B：有存低嘅一晚 → 先補做（夜晚窗口內都係；補做唔寫 o.night，同一次上線之後仍可再入當晚）
    if (!inLate(h)) return { ok: false, why: 'hours' };
    if (o.night === nightKey(now, h)) return { ok: false, why: 'done' };
    return { ok: true, why: 'ok', night: nightKey(now, h) };
  }
  /* 當晚記錄（6a）：21:00 嗰日＋（過咗午夜）今日，加埋；補做（bankNight）＝淨係存低嗰晚嗰日 */
  function nightFacts(s, now, h, bankNight) {
    if (h == null) h = hourOf(now); const nk = bankNight || nightKey(now, h), keys = [nk]; const tk = dayKey(now); if (!bankNight && tk !== nk) keys.push(tk);   // 6d.1：補做用存低嗰晚（21:00 嗰日）嘅記錄
    const out = { meal: 0, rinse: 0, play: 0, feed: 0, poop: 0, mg: 0, night: 1, keys };
    const m = s.mem6 && obj(s.mem6.d) ? s.mem6.d : {};
    for (const k of keys) { const r = m[k]; if (!obj(r)) continue; const f = obj(r.f) ? r.f : {}, c = obj(r.c) ? r.c : {};
      out.meal += f.meal | 0; out.rinse += c.rinse | 0; out.play += (c.play | 0) + (c.mg | 0);
      out.feed += (c.feed | 0) + Object.keys(f).reduce((a, x) => a + (f[x] | 0), 0); out.poop += (c.poop | 0) + (c.poopQuick | 0); out.mg += c.mg | 0; }
    return out;
  }
  function weights(F) {
    const lake = (F.feed ? 1 : 0) + (F.rinse ? 1 : 0) + (F.poop ? 1 : 0) + (F.mg ? 1 : 0);   // C
    const w = { forest: Math.min(CFG.wMax, F.meal | 0), lake: Math.min(CFG.wMax, lake), toy: Math.max(1, Math.min(CFG.wMax, F.play | 0)), star: 1 };   // 修2b：玩具房冇門檻、最低 1
    for (const k of THEMES) if (!(w[k] > 0)) delete w[k]; return w;
  }
  /* 格數：每主題最少 minTiles，其餘按權重（最大餘數法；同分按 THEMES 次序） */
  function alloc(w) {
    const ks = THEMES.filter(k => w[k] > 0), N = CFG.cols * CFG.rows, out = {}; let left = N - ks.length * CFG.minTiles;
    const W = ks.reduce((a, k) => a + w[k], 0); const rem = [];
    for (const k of ks) { const x = left * w[k] / W; out[k] = CFG.minTiles + Math.floor(x); rem.push([k, x - Math.floor(x)]); }
    let used = ks.reduce((a, k) => a + out[k], 0); rem.sort((a, b) => b[1] - a[1] || THEMES.indexOf(a[0]) - THEMES.indexOf(b[0]));
    for (let i = 0; used < N; i = (i + 1) % rem.length) { out[rem[i][0]]++; used++; }
    return out;
  }
  const SNAKE = (() => { const o = []; for (let r = CFG.rows - 1, j = 0; r >= 0; r--, j++) for (let c = 0; c < CFG.cols; c++) o.push(r * CFG.cols + (j % 2 ? CFG.cols - 1 - c : c)); return o; })();
  const adj = (a, b) => { const ra = Math.floor(a / CFG.cols), ca = a % CFG.cols, rb = Math.floor(b / CFG.cols), cb = b % CFG.cols; return Math.abs(ra - rb) + Math.abs(ca - cb) === 1; };
  /* 今晚張地圖：grid[15]＝主題；frags[6]＝{ tile, th, at（秒） } */
  function rngOf(str) { let x = hash(str) || 1; return () => { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; return x / 4294967296; }; }
  function drawTheme(w, u) { const ks = THEMES.filter(k => w[k] > 0); let tot = 0; for (const k of ks) tot += w[k]; let x = u * tot; for (const k of ks) { x -= w[k]; if (x < 0) return k; } return ks[ks.length - 1]; }
  function plan(s, now, h, opt) {
    if (h == null) h = hourOf(now); const bk = opt && typeof opt.bank === 'string' ? opt.bank : null, F = nightFacts(s, now, h, bk), w = weights(F), n = alloc(w), nk = bk || nightKey(now, h);
    const order = THEMES.filter(k => k !== 'star' && n[k]).sort((a, b) => w[b] - w[a] || THEMES.indexOf(a) - THEMES.indexOf(b)).concat(['star']);
    const grid = new Array(CFG.cols * CFG.rows); let p = 0; for (const k of order) for (let i = 0; i < n[k]; i++) grid[SNAKE[p++]] = k;
    // 碎片：每晚 1 片，frag2 機會多 1 片；每片按權重抽主題，已齊 5 張（連今晚前面嗰片）嘅主題剔走（修1）；四主題都齊 → 0 片
    const seed = ((s.seed >>> 0) || 1) + ':6c:' + (opt && opt.bank ? 'b' + opt.bank : nk), rng = rngOf(seed), frags = [], taken = { [CFG.start]: 1 };
    const o = st(s), vf = Object.assign({}, o.frag), vc = Object.fromEntries(THEMES.map(k => [k, themeCards(s, k).length]));
    const openW = () => { const x = {}; for (const k of THEMES) if (w[k] > 0 && vc[k] < CFG.cardsPerTheme) x[k] = w[k]; return x; };
    const nF = Object.keys(openW()).length ? 1 + (rng() < CFG.frag2 ? 1 : 0) : 0;
    for (let j = 0; j < nF; j++) { const ow = openW(), ks = THEMES.filter(k => ow[k] > 0); if (!ks.length) break;
      const th = drawTheme(ow, rng()), tiles = grid.map((t, i) => (t === th ? i : -1)).filter(i => i >= 0 && !taken[i]); if (!tiles.length) break;
      const i = tiles[Math.floor(rng() * tiles.length)]; taken[i] = 1; frags.push({ tile: i, th });
      vf[th]++; if (Math.min(CFG.cardsPerTheme, Math.floor(vf[th] / CFG.perCard)) > vc[th]) vc[th]++; }
    frags.forEach((f, i) => { f.at = CFG.spawnAt[i] || 0; f.id = i; });
    return { night: nk, facts: F, w, n, grid, frags, start: CFG.start, dur: CFG.durSec };
  }
  /* 入夢：用咗今晚 */
  function enter(s, now, h) { const c = canEnter(s, now, h); if (!c.ok) return c; const o = st(s);
    if (c.why === 'bank') { o.bank = Math.max(0, o.bank - 1); o.bankDone = lastEnded(now, h);   // 補做＝清埋截至而家錯過嘅晚（唔會同日再補）
      o.n.bank++; o.n.dreams++; return Object.assign({ ok: true, bank: c.night }, plan(s, now, h, { bank: c.night })); }   // B：補做（唔佔當晚）
    o.night = c.night; o.n.dreams++; return Object.assign({ ok: true }, plan(s, now, h)); }
  function themeCards(s, th) { const o = st(s); return CARDS.filter(c => c.th === th && o.cards[c.id]); }
  /* 家具：主題首選（5a 擺設池）；有咗 → 擺設池第一件未有；全部有 → null */
  function furnFor(s, th) {
    if (!FAM || !FAM.SOUV) return null; const sv = FAM.st(s).sv, pref = TH[th].furn;
    if (FAM.SV[pref] && !sv[pref]) return pref; const x = FAM.SOUV.find(v => !sv[v.id]); return x ? x.id : null;
  }
  /* 拾一片（th）：入帳 → 夠 5 片砌新卡 → 主題齊 5 張送家具 */
  function pick(s, th, now) {
    if (!TH[th]) return { ok: false };
    const o = st(s); o.frag[th]++; o.n.frags++; const out = { ok: true, th, frag: o.frag[th], card: null, furn: null, done: false };
    const have = themeCards(s, th).length, want = Math.min(CFG.cardsPerTheme, Math.floor(o.frag[th] / CFG.perCard));
    if (want > have) { const c = CARDS.filter(x => x.th === th && !o.cards[x.id])[0]; if (c) { o.cards[c.id] = now || 1; o.n.cards++; out.card = c.id; } }
    if (themeCards(s, th).length >= CFG.cardsPerTheme && !o.furn[th]) {
      const id = furnFor(s, th); o.furn[th] = id || 'none'; out.done = true;
      if (id) { FAM.st(s).sv[id] = now || 1; o.n.furn++; out.furn = id; }
    }
    return out;
  }
  function endLog(s, nk, got, sec, ths) { const o = st(s); o.log.push({ d: nk, got: Math.max(0, Math.min(CFG.frags, got | 0)), sec: Math.max(0, Math.min(CFG.maxSec, Math.round(sec))), th: (ths || []).filter(k => TH[k]) }); if (o.log.length > CFG.keepLog) o.log.shift(); }
  const toNext = (s, th) => { const o = st(s); if (themeCards(s, th).length >= CFG.cardsPerTheme) return 0; return CFG.perCard - (o.frag[th] % CFG.perCard); };
  function summary(s, now, h) {
    const o = st(s), c = canEnter(s, now, h);
    return { can: c.ok, why: c.why, bank: o.bank, bankNight: o.bankNight, night: o.night, tonight: o.night === nightKey(now, h), frag: Object.assign({}, o.frag), cards: Object.keys(o.cards).length, total: CARDS.length,
      byTh: Object.fromEntries(THEMES.map(k => [k, themeCards(s, k).length])), furn: Object.assign({}, o.furn), n: Object.assign({}, o.n), log: o.log.slice(-5) };
  }
  function resetNight(s) { st(s).night = null; return st(s); }
  function reset(s) { delete s.dream6; return st(s); }
  return { CFG, THEMES, TH, CARDS, CK, SNAKE, dayKey, hourOf, inHours, inLate, nightKey, lastEnded, accrue, rngOf, drawTheme, st, canEnter, nightFacts, weights, alloc, adj, plan, enter, themeCards, furnFor, pick, endLog, toNext, summary, resetNight, reset };
});
