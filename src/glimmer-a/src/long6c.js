/* 《微光小圃》 long6c.js — 第 6 批 6c「夢境探險」（遊策 breakthrough-6a6d-spec §6c）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.dream6（sanitize）。唔加月眠／任何路線分、唔出碎、唔郁需求數值、唔郁系統 6 親密度。
   ・入夢：團絨瞓緊（s.sleeping）＋遊戲鐘 21:00–03:00＋唔係蛋／唔係細佬做主養 → 每晚 1 次（「一晚」＝21:00 嗰日；00:00–03:00 計返前一日）。
     入夢嗰刻已經用咗今晚（中途閂 app 都唔可以再入；已拾嘅碎片即時入帳，唔會冇咗）。
   ・夢長：150 秒（＋入／出夢過場各 1.2 秒），硬上限 180 秒（每晚 ≤3 分鐘）。
   ・直向小地圖 3×5 格（i＝行×3＋列，行 0＝頂），由當晚 6a 記錄（s.mem6；21:00 嗰日＋過咗午夜嗰日加埋）砌：
       餵菇（暖菇飯 meal）→ 蘑菇森林 forest；淋水（沖身 rinse）→ 水珠湖 lake；玩得多（玩耍＋小遊戲 ≥2 次）→ 玩具房 toy；夜晚嚟 → 星空 star（入得夢一定係夜晚嚟，永遠有）。
     每個主題最少 2 格，其餘按次數（每項最多計 4）比例分；由底（起點＝底行中間）蛇形排上去，星空喺最頂。
   ・夢碎片：每晚 6 片，每個有嘅主題最少 1 片，其餘按格數分；頭 2 片一入夢就有，之後每 25 秒浮多 1 片（最後一片 100 秒）。
     夢碎片唔係貨幣：每個主題每 5 片砌 1 張夢圖鑑（每主題 5 張，首批 20 張）；砌齊一個主題 5 張 → 送家具 1 件（5a「擺設」池）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./long6a.js'), require('./long5a.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6c = factory(root.Glimmer.long6a, root.Glimmer.long5a); }
})(typeof self !== 'undefined' ? self : this, function (M6, FAM) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const int = (v, d) => Number.isFinite(+v) ? Math.floor(+v) : d;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const CFG = { hours: [21, 3], cols: 3, rows: 5, start: 13, durSec: 150, fadeSec: 1.2, maxSec: 180, frags: 6, spawnAt: [0, 0, 25, 50, 75, 100], perCard: 5, cardsPerTheme: 5,
    minTiles: 2, wMax: 4, playMany: 2, keepLog: 14 };
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
    if (!obj(o.n)) o.n = {}; for (const k of ['dreams', 'frags', 'cards', 'furn']) o.n[k] = Math.max(0, int(o.n[k], 0));
    for (const k of Object.keys(o)) if (!['v', 'night', 'frag', 'cards', 'furn', 'log', 'n'].includes(k)) delete o[k];
    return o;
  }
  const kidMain = (s) => !!(s && s.fam && s.fam.km);
  /* 入唔入到夢：{ ok, why }（why：egg／km／awake／hours／done） */
  function canEnter(s, now, h) {
    if (h == null) h = hourOf(now);
    if (!s || s.stage === 'egg') return { ok: false, why: 'egg' }; if (kidMain(s)) return { ok: false, why: 'km' };
    if (!s.sleeping) return { ok: false, why: 'awake' }; if (!inHours(h)) return { ok: false, why: 'hours' };
    if (st(s).night === nightKey(now, h)) return { ok: false, why: 'done' };
    return { ok: true, why: 'ok', night: nightKey(now, h) };
  }
  /* 當晚記錄（6a）：21:00 嗰日＋（過咗午夜）今日，加埋 */
  function nightFacts(s, now, h) {
    if (h == null) h = hourOf(now); const nk = nightKey(now, h), keys = [nk]; const tk = dayKey(now); if (tk !== nk) keys.push(tk);
    const out = { meal: 0, rinse: 0, play: 0, night: 1, keys };
    const m = s.mem6 && obj(s.mem6.d) ? s.mem6.d : {};
    for (const k of keys) { const r = m[k]; if (!obj(r)) continue; const f = obj(r.f) ? r.f : {}, c = obj(r.c) ? r.c : {};
      out.meal += f.meal | 0; out.rinse += c.rinse | 0; out.play += (c.play | 0) + (c.mg | 0); }
    return out;
  }
  function weights(F) {
    const w = { forest: Math.min(CFG.wMax, F.meal), lake: Math.min(CFG.wMax, F.rinse), toy: F.play >= CFG.playMany ? Math.min(CFG.wMax, F.play) : 0, star: 1 };
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
  function plan(s, now, h) {
    if (h == null) h = hourOf(now); const F = nightFacts(s, now, h), w = weights(F), n = alloc(w), nk = nightKey(now, h);
    const order = THEMES.filter(k => k !== 'star' && n[k]).sort((a, b) => w[b] - w[a] || THEMES.indexOf(a) - THEMES.indexOf(b)).concat(['star']);
    const grid = new Array(CFG.cols * CFG.rows); let p = 0; for (const k of order) for (let i = 0; i < n[k]; i++) grid[SNAKE[p++]] = k;
    // 碎片主題：每個主題 1 片，其餘按格數
    const ks = order.slice(), fr = {}; let left = CFG.frags - ks.length; for (const k of ks) fr[k] = 1;
    const tot = ks.reduce((a, k) => a + n[k], 0), rem = [];
    for (const k of ks) { const x = left * n[k] / tot; fr[k] += Math.floor(x); rem.push([k, x - Math.floor(x)]); }
    let used = ks.reduce((a, k) => a + fr[k], 0); rem.sort((a, b) => b[1] - a[1] || THEMES.indexOf(a[0]) - THEMES.indexOf(b[0]));
    for (let i = 0; used < CFG.frags; i = (i + 1) % rem.length) { fr[rem[i][0]]++; used++; }
    const seed = ((s.seed >>> 0) || 1) + ':6c:' + nk, frags = [], taken = { [CFG.start]: 1 };
    for (const k of ks) { const tiles = grid.map((t, i) => (t === k ? i : -1)).filter(i => i >= 0 && !taken[i]);
      for (let j = 0; j < fr[k] && tiles.length; j++) { const i = tiles.splice(hash(seed + ':' + k + ':' + j) % tiles.length, 1)[0]; taken[i] = 1; frags.push({ tile: i, th: k }); } }
    // 出場次序（洗牌）→ at
    frags.sort((a, b) => hash(seed + ':o' + a.tile) - hash(seed + ':o' + b.tile)); frags.forEach((f, i) => { f.at = CFG.spawnAt[i] || 0; f.id = i; });
    return { night: nk, facts: F, w, n, grid, frags, start: CFG.start, dur: CFG.durSec };
  }
  /* 入夢：用咗今晚 */
  function enter(s, now, h) { const c = canEnter(s, now, h); if (!c.ok) return c; const o = st(s); o.night = c.night; o.n.dreams++; return Object.assign({ ok: true }, plan(s, now, h)); }
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
    return { can: c.ok, why: c.why, night: o.night, tonight: o.night === nightKey(now, h), frag: Object.assign({}, o.frag), cards: Object.keys(o.cards).length, total: CARDS.length,
      byTh: Object.fromEntries(THEMES.map(k => [k, themeCards(s, k).length])), furn: Object.assign({}, o.furn), n: Object.assign({}, o.n), log: o.log.slice(-5) };
  }
  function resetNight(s) { st(s).night = null; return st(s); }
  function reset(s) { delete s.dream6; return st(s); }
  return { CFG, THEMES, TH, CARDS, CK, SNAKE, dayKey, hourOf, inHours, nightKey, st, canEnter, nightFacts, weights, alloc, adj, plan, enter, themeCards, furnFor, pick, endLog, toNext, summary, resetNight, reset };
});
