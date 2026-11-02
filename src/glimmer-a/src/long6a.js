/* 《微光小圃》 long6a.js — 突破 6a「團絨記得你」（docs-gdd/breakthrough-6a6d-spec.md §6a）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.mem6（sanitize；唔加團絨路線分、唔郁 §7、唔出碎、冇懲罰）。
   ・本機記最近 30 日（每日一格 d[YYYY-MM-DD]）：嚟嘅時間（第一次／最後一次分鐘＋次數）、照顧類型、食咗乜、小遊戲當日最好（＋破紀錄）、
     訪客、細佬大事（蛋到／孵化／大咗／學課／搬入屋／遠足返／家族升級／新一代）、冇嚟嘅日數（返嚟嗰日記 gap）。
   ・講出口：每日第一次開 game 招呼 1 句（參考上次嚟嗰日）；日記每日自動寫 1 句（嗰日嘅記錄）；心聲泡泡（有機會換成記憶句，每日最多 2 句）。
   ・首批 60 句（LINES；按類型留空位 {d}{h}{n}{food}{game}{visitor}{kid}{stage}）；同一句 7 日內唔會講第二次（招呼／日記／心聲共用）。
   ・冇嚟：1 日「你琴日去咗邊？」、2 日、3 日以上「我以為你搬咗屋。」；冇懲罰；返嚟第一下撳＝特別開心（UI 做，happy 旗）。
   ・每句帶表情疊層 mood：s＝得意、p＝委屈（遊美未出圖 → UI 用標明 placeholder）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6a = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const DAY = 86400e3;
  const CFG = { keepDays: 30, noRepeatDays: 7, voicePerDay: 2, voiceChance: 0.5, sessionGapMin: 20, kMax: 8, viMax: 4, sizeMaxBytes: 200 * 1024, streakFrom: 3, manyOpens: 4, careMany: 5 };

  /* ── 首批 60 句（遊策可整張換；id 唔好改）。語氣：蠢蠢地但覺得自己好醒。[id, 句, 表情 s 得意／p 委屈] ── */
  const LINES = {
    late: [['t_l1', '你{d} {h} 點先嚟，我扮瞓咗等你。', 's'], ['t_l2', '{d}咁夜你都嚟，我知，我嘅魅力太大。', 's'], ['t_l3', '你{d}夜晚 {h} 點先出現，我眼光光數咗好多粒星。', 'p']],
    early: [['t_e1', '你{d}朝早 {h} 點就嚟，係咪掛住我掛到瞓唔著？', 's'], ['t_e2', '{d}你咁早嚟，我仲未梳頭，不過我天生靚。', 's'], ['t_e3', '朝早 {h} 點見到你，我決定{d}係好日。', 's']],
    day: [['t_d1', '你{d}下晝嚟，啱啱好係我最醒嗰陣。', 's'], ['t_d2', '{d}你 {h} 點嚟，我計過，係最啱探我嘅時間。', 's']],
    eve: [['t_v1', '你{d}夜晚 {h} 點嚟，我一早擺好晒 pose。', 's'], ['t_v2', '{d}收工時間你就嚟，我估中咗，我估嘢好準。', 's']],
    many: [['n_1', '你{d}嚟咗 {n} 次，我數咗，冇數錯（應該）。', 's'], ['n_2', '{d}你返嚟 {n} 次，我覺得你好鍾意我，我冇估錯。', 's'], ['n_3', '{d}開咗我 {n} 次，下次可以開多次，我唔介意。', 's']],
    food: [['f_1', '你{d}餵我食{food}，我決定佢係我最鍾意嘅…之一。', 's'], ['f_2', '{d}食咗{food}，我而家仲記得個味，我記性好好。', 's'], ['f_3', '{d}你俾{food}我食，我分咗一半俾自己。', 's'],
      ['f_4', '我研究過，{d}嗰個{food}係圓嘅，所以好食。', 's'], ['f_6', '{food}！{d}食過，我宣佈佢係我發明嘅。', 's']],
    meals: [['f_5', '{d}食咗 {n} 餐，我個肚話佢好滿意。', 's']],
    play: [['c_play1', '你{d}陪我玩，我贏咗…我話贏咗就贏咗。', 's'], ['c_play2', '{d}玩完之後我好攰，不過我扮唔攰。', 's']],
    rinse: [['c_rinse1', '你{d}幫我沖涼，我而家香到自己都暈。', 's'], ['c_rinse2', '{d}沖完涼，我覺得自己發光多咗兩成。', 's']],
    poop: [['c_poop1', '你{d}幫我執便便，我…我唔知你講緊乜。', 'p'], ['c_poop2', '{d}嗰啲便便唔係我嘅，係隔籬嘅。', 'p']],
    lull: [['c_lull1', '你{d}哄我瞓，我其實好快就瞓著，係咪好叻？', 's'], ['c_lull2', '{d}你陪我瞓，我發咗個夢，夢見我好醒。', 's']],
    pat: [['c_pat1', '你{d}摸咗我個頭 {n} 下，我個頭而家好有福氣。', 's']],
    care: [['c_many1', '你{d}照顧咗我 {n} 次，我決定原諒你所有嘢。', 's']],
    gbest: [['g_5', '{d}{game}破咗紀錄，{n} 分！我要寫入族譜。', 's']],
    game: [['g_1', '你{d}{game}打咗 {n} 分！其實係我暗中教你嘅。', 's'], ['g_2', '{d}{game} {n} 分，我話我一早知你得。', 's'], ['g_4', '{d}你玩{game}好認真，我睇住你都學識咗（未）。', 's']],
    glow: [['g_6', '{d}{game}得 {n} 分，唔緊要，我都唔識玩。', 'p']],
    visitor: [['v_1', '{visitor}{d}嚟過，佢話我好可愛，我話我知。', 's'], ['v_2', '{d}{visitor}嚟探我哋，我扮成熟招呼佢。', 's'], ['v_3', '{visitor}{d}同我傾咗好耐，其實我淨係識點頭。', 's'],
      ['v_4', '{d}有客人：{visitor}！我記住咗佢個樣，大概。', 's'], ['v_5', '{visitor}{d}走咗，我有少少唔捨得，少少啫。', 'p']],
    k_egg: [['k_egg', '{d}屋企嚟咗隻蛋，我負責睇住佢，好專業。', 's']],
    k_hatch: [['k_hatch', '{kid}{d}出世喇！佢個樣似我，靚仔嗰邊。', 's']],
    k_grow: [['k_grow', '{kid}{d}大咗做{stage}，係我教得好。', 's']],
    k_lesson: [['k_lesson', '{kid}{d}學咗嘢，雖然學錯咗，不過係我嘅錯…唔係，係佢嘅。', 'p']],
    k_move: [['k_move', '{kid}{d}搬咗入屋仔，間房我幫佢揀嘅（我諗）。', 's']],
    k_trip: [['k_trip', '{kid}{d}去完遠足返嚟，我都想去，不過我要睇屋。', 'p']],
    k_lv: [['k_lv', '{d}我哋家族升咗級，我覺得係因為我。', 's']],
    k_gen: [['k_gen', '{d}我啱啱出世，不過我乜都記得（大概）。', 's']],
    absent1: [['a1_1', '你琴日去咗邊？', 'p'], ['a1_2', '你琴日冇嚟，我坐喺度等，等到變咗石頭（差少少）。', 'p'], ['a1_3', '琴日冇見你，我以為你跟咗朵雲走咗。', 'p']],
    absent2: [['a2_1', '你兩日冇嚟，我數咗兩次星…定係三次？', 'p'], ['a2_2', '兩日喎！我差啲以為你唔記得我個名。', 'p']],
    absent3: [['a3_1', '我以為你搬咗屋。', 'p'], ['a3_2', '你 {n} 日冇嚟，我自己學識咗發呆，好叻。', 'p'], ['a3_3', '{n} 日喎！我已經寫好尋人啟事，不過唔識寫字。', 'p']],
    streak: [['s_1', '你連續 {n} 日都嚟，我計過，係紀錄。', 's'], ['s_2', '第 {n} 日見到你，我開始覺得你住喺我隔籬。', 's'], ['s_4', '你日日都嚟，我好醒，一早知你會嚟。', 's']],
    general: [['x_1', '我記得你㗎，我記性好好，你係…我最好嘅朋友。', 's'], ['x_3', '我腦入面有本簿，寫滿晒你。（得兩頁）', 's']],
  };
  const ALL = [], BYID = {}, CAT = {};
  for (const cat of Object.keys(LINES)) { CAT[cat] = []; for (const [id, t, mood] of LINES[cat]) { const L = { id, t, mood, cat }; ALL.push(L); BYID[id] = L; CAT[cat].push(L); } }
  /* 類型權重（越大越優先講；同類句平分） */
  const W = { gbest: 9, k_hatch: 9, k_gen: 9, k_grow: 8, k_egg: 8, k_move: 7, k_trip: 7, k_lv: 7, k_lesson: 6, visitor: 7, game: 5, glow: 5, streak: 5, food: 4, meals: 3, play: 4, rinse: 4, poop: 4, lull: 4, pat: 3, care: 3, late: 4, early: 4, day: 3, eve: 3, many: 3, general: 1 };
  const MOOD_ZH = { s: '得意', p: '委屈' };
  const KID_EV = ['egg', 'hatch', 'grow', 'lesson', 'move', 'trip', 'lv', 'gen'];
  const CARE_K = ['feed', 'play', 'mg', 'rinse', 'poop', 'poopQuick', 'lull', 'petSleep', 'pat'];

  function dayKey(ms) { const d = new Date(ms); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function dn(key) { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(key || ''); return m ? Math.round(Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY) : NaN; }
  const isKey = (k) => Number.isFinite(dn(k));
  const minOf = (ms) => { const d = new Date(ms); return d.getHours() * 60 + d.getMinutes(); };
  const cnt = (v, max) => Math.max(0, Math.min(max || 9999, v | 0));
  const str = (v, n) => (typeof v === 'string' ? v.slice(0, n || 24) : '');

  function cleanDay(r) {
    if (!obj(r)) return null;
    const o = Array.isArray(r.o) && r.o.length === 2 ? [cnt(r.o[0], 1439), cnt(r.o[1], 1439)] : null;
    const out = { o: o || [0, 0], n: cnt(r.n, 999), c: {}, f: {}, g: {}, vi: [], k: [], gap: cnt(r.gap, 999) };
    if (obj(r.c)) for (const k of Object.keys(r.c)) if (CARE_K.includes(k)) out.c[k] = cnt(r.c[k], 999);
    if (obj(r.f)) for (const k of Object.keys(r.f).slice(0, 12)) if (/^[a-z0-9_]{1,24}$/.test(k)) out.f[k] = cnt(r.f[k], 999);
    if (obj(r.g)) for (const k of Object.keys(r.g).slice(0, 8)) if (/^[a-z0-9_]{1,16}$/.test(k) && Array.isArray(r.g[k])) out.g[k] = [Math.max(0, Math.min(1e6, +r.g[k][0] || 0)), cnt(r.g[k][1], 3), r.g[k][2] ? 1 : 0];
    if (Array.isArray(r.vi)) for (const v of r.vi) if (typeof v === 'string' && out.vi.length < CFG.viMax && !out.vi.includes(v)) out.vi.push(str(v, 24));
    if (Array.isArray(r.k)) for (const e of r.k) if (Array.isArray(e) && KID_EV.includes(e[0]) && out.k.length < CFG.kMax) out.k.push([e[0], str(e[1], 16), str(e[2], 12)]);
    if (!o) out.o = [0, 0];
    return out;
  }
  const SAN = typeof WeakSet === 'function' ? new WeakSet() : null;   // 每個 mem6 物件只 sanitize 一次（讀檔後係新物件 → 再 sanitize）
  function st(s) {
    let m = s.mem6; if (!obj(m)) m = s.mem6 = {};
    if (SAN && SAN.has(m)) return m;
    m.v = 1;
    if (!obj(m.d)) m.d = {}; for (const k of Object.keys(m.d)) { const r = isKey(k) ? cleanDay(m.d[k]) : null; if (r) m.d[k] = r; else delete m.d[k]; }
    for (const k of ['last', 'prev', 'greet', 'happy', 'vday']) if (m[k] != null && !isKey(m[k])) m[k] = null;
    for (const k of ['last', 'prev', 'greet', 'happy', 'vday']) if (m[k] === undefined) m[k] = null;
    m.vn = cnt(m.vn, 99); m.at = +m.at || 0;
    if (!obj(m.said)) m.said = {}; for (const k of Object.keys(m.said)) if (!BYID[k] || !Number.isFinite(+m.said[k])) delete m.said[k]; else m.said[k] = +m.said[k];
    if (!Array.isArray(m.log)) m.log = []; m.log = m.log.filter(x => Array.isArray(x) && BYID[x[1]]).slice(-40);
    if (!obj(m.ks)) m.ks = null;
    if (!obj(m.n)) m.n = {}; for (const k of ['greet', 'diary', 'voice', 'happy', 'visits']) m.n[k] = cnt(m.n[k], 1e6);
    if (SAN) SAN.add(m); return m;
  }
  function prune(s, nowMs) {
    const m = st(s), t = dn(dayKey(nowMs)); for (const k of Object.keys(m.d)) if (t - dn(k) >= CFG.keepDays || dn(k) > t + 1) delete m.d[k];
    for (const k of Object.keys(m.said)) if (t - m.said[k] >= 14) delete m.said[k];
  }
  function rec(s, key) { const m = st(s); return m.d[key] || null; }

  /* 嚟咗（開 app／返前台／過咗午夜）：返 { first, gap, day } — first＝今日第一次 */
  function visit(s, nowMs, o) {
    o = o || {}; const m = st(s), key = dayKey(nowMs), min = minOf(nowMs);
    if (!m.last && o.lastSeen && +o.lastSeen < nowMs) { const lk = dayKey(+o.lastSeen); if (lk < key) m.last = lk; }   // 5c 舊存檔升級：用 lastSeen 當上次嚟
    let r = m.d[key], first = false, gap = 0;
    if (!r) {
      first = true; if (m.last && m.last < key) { gap = Math.max(0, dn(key) - dn(m.last) - 1); m.prev = m.last; }
      r = m.d[key] = { o: [min, min], n: 1, c: {}, f: {}, g: {}, vi: [], k: [], gap };
      if (gap >= 1) m.happy = key;
      m.last = key; m.n.visits++;
    } else if (o.session !== false) {
      if (!m.at || nowMs - m.at >= CFG.sessionGapMin * 60e3) r.n = Math.min(999, r.n + 1);
      r.o[1] = Math.max(r.o[1], min); if (min < r.o[0]) r.o[0] = min;
    }
    m.at = nowMs; prune(s, nowMs);
    return { first, gap: r.gap, day: key };
  }
  function today(s, nowMs) { const key = dayKey(nowMs); if (!rec(s, key)) visit(s, nowMs, { session: false }); const r = rec(s, key); r.o[1] = Math.max(r.o[1], minOf(nowMs)); return r; }
  /* 記事：care（kind）／food（id）／game（kind, v, stars, best）／visitor（名）／kid（事件, 名, 階段） */
  function note(s, what, a, b, c, d, nowMs) {
    const r = today(s, nowMs);
    if (what === 'care') { if (CARE_K.includes(a)) r.c[a] = Math.min(999, (r.c[a] | 0) + 1); }
    else if (what === 'food') { const k = String(a || '').slice(0, 24); if (/^[a-z0-9_]+$/.test(k) && (r.f[k] || Object.keys(r.f).length < 12)) r.f[k] = Math.min(999, (r.f[k] | 0) + 1); }
    else if (what === 'game') { const k = String(a || ''); if (!/^[a-z0-9_]{1,16}$/.test(k)) return r; const g = r.g[k] || (r.g[k] = [0, 0, 0]); g[0] = Math.max(g[0], +b || 0); g[1] = Math.max(g[1], c | 0); if (d) g[2] = 1; }
    else if (what === 'visitor') { const v = str(a, 24); if (v && !r.vi.includes(v) && r.vi.length < CFG.viMax) r.vi.push(v); }
    else if (what === 'kid') { if (KID_EV.includes(a) && r.k.length < CFG.kMax) r.k.push([a, str(b, 16), str(c, 12)]); }
    return r;
  }
  /* 細佬大事：UI 每秒俾快照 env（phase／kst／les／res／lv／trips／gen／name）；同上次比較 → 記事。第一次只記低唔出事件 */
  function scanKid(s, env, nowMs) {
    const m = st(s), o = m.ks, out = [];
    if (o) {
      const nm = env.name || '細佬';
      if (env.ph === 'egg' && o.ph !== 'egg' && o.ph !== 'kid') out.push(['egg', nm, '']);
      if (env.ph === 'kid' && o.ph === 'egg') out.push(['hatch', nm, '']);
      else if (env.ph === 'kid' && o.ph === 'kid' && env.kst && o.kst && env.kst !== o.kst) out.push(['grow', nm, env.kstZh || env.kst]);
      if (env.ph === 'kid' && o.ph === 'kid' && env.les > o.les) out.push(['lesson', nm, '']);
      if (env.res > o.res) out.push(['move', env.resName || nm, '']);
      if (env.trips > o.trips) out.push(['trip', env.tripName || nm, '']);
      if (env.lv > o.lv) out.push(['lv', '', String(env.lv)]);
      if (env.gen > o.gen) out.push(['gen', '', '']);
    }
    m.ks = { ph: env.ph || 'none', kst: env.kst || null, les: env.les | 0, res: env.res | 0, lv: env.lv | 0, trips: env.trips | 0, gen: env.gen | 0 };
    for (const e of out) note(s, 'kid', e[0], e[1], e[2], null, nowMs);
    return out;
  }

  /* ── 揀句 ── */
  function streakTo(s, key) { const m = st(s); let n = 0, t = dn(key); while (m.d[dayKeyOfDn(t)]) { n++; t--; } return n; }
  function dayKeyOfDn(n) { const d = new Date(n * DAY); return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0') + '-' + String(d.getUTCDate()).padStart(2, '0'); }
  const h12 = (min) => { const h = Math.floor(min / 60) % 12; return String(h || 12); };
  /* 一日記錄 → 可講嘅類型＋填空值。names：{ food(id)→名, game(kind)→名, visitor(id)→名 } */
  function factsOf(r, names) {
    names = names || {}; const F = [], nm = (t, k) => (names[t] && names[t](k)) || k;
    if (!r) return F;
    const gk = Object.keys(r.g); if (gk.length) { const best = gk.find(k => r.g[k][2]); if (best) F.push(['gbest', { game: nm('game', best), n: r.g[best][0] }]);
      const top = gk.sort((a, b) => r.g[b][0] - r.g[a][0])[0], g = r.g[top]; F.push([g[1] <= 1 ? 'glow' : 'game', { game: nm('game', top), n: g[0] }]); }
    const seenK = {}; for (const e of r.k) { const c = 'k_' + e[0]; if (seenK[c]) continue; seenK[c] = 1; F.push([c, { kid: e[1] || '細佬', stage: e[2] || '' }]); }
    if (r.vi.length) F.push(['visitor', { visitor: nm('visitor', r.vi[r.vi.length - 1]) }]);
    const fk = Object.keys(r.f); if (fk.length) { const top = fk.sort((a, b) => r.f[b] - r.f[a])[0], meals = fk.reduce((a, k) => a + r.f[k], 0); F.push(['food', { food: nm('food', top) }]); if (meals >= 2) F.push(['meals', { n: meals }]); }
    const c = r.c; if ((c.play | 0) + (c.mg | 0)) F.push(['play', {}]); if (c.rinse) F.push(['rinse', {}]); if ((c.poop | 0) + (c.poopQuick | 0)) F.push(['poop', {}]); if ((c.lull | 0) + (c.petSleep | 0)) F.push(['lull', {}]);
    if (c.pat >= 2) F.push(['pat', { n: c.pat }]); const tot = CARE_K.reduce((a, k) => a + (k === 'poopQuick' ? 0 : (c[k] | 0)), 0); if (tot >= CFG.careMany) F.push(['care', { n: tot }]);
    const [a, b] = r.o; if (b >= 21 * 60 || a < 5 * 60) F.push(['late', { h: h12(b >= 21 * 60 ? b : a) }]); else if (a < 10 * 60) F.push(['early', { h: h12(a) }]); else if (b >= 17 * 60) F.push(['eve', { h: h12(b) }]); else F.push(['day', { h: h12(a) }]);
    if (r.n >= CFG.manyOpens) F.push(['many', { n: r.n }]);
    return F;
  }
  function fill(t, v) { return t.replace(/\{(\w+)\}/g, (m0, k) => (v[k] != null && v[k] !== '' ? String(v[k]) : m0)); }
  const fresh = (m, id, tdn) => !(id in m.said) || tdn - m.said[id] >= CFG.noRepeatDays;
  /* facts → 一句（7 日唔重複；類型權重／同類平分；rng 0–1） */
  function choose(s, facts, o) {
    const m = st(s), tdn = dn(dayKey(o.nowMs)), r = o.rng || Math.random, pool = [];
    for (const [cat, v] of facts) { const Ls = (CAT[cat] || []).filter(L => fresh(m, L.id, tdn)); const vv = Object.assign({ d: o.d || '' }, v);
      const okL = Ls.filter(L => !/\{(\w+)\}/.test(fill(L.t, vv))); for (const L of okL) pool.push({ L, v: vv, w: (o.w && o.w[cat] != null ? o.w[cat] : W[cat] || 1) / okL.length }); }
    if (!pool.length) return null;
    const tot = pool.reduce((a, p) => a + p.w, 0); let x = r() * tot, p = pool[pool.length - 1]; for (const q of pool) { x -= q.w; if (x <= 0) { p = q; break; } }
    return { id: p.L.id, cat: p.L.cat, mood: p.L.mood, line: fill(p.L.t, p.v) };
  }
  function commit(s, pk, use, nowMs) { if (!pk) return pk; const m = st(s); m.said[pk.id] = dn(dayKey(nowMs)); m.log.push([dayKey(nowMs), pk.id, use]); if (m.log.length > 40) m.log.shift(); if (m.n[use] != null) m.n[use]++; return pk; }
  const can = (s) => s && s.stage !== 'egg' && !(s.fam && s.fam.km);
  /* 每日第一次開 game：招呼 1 句（上次嚟嗰日嘅記錄／冇嚟日數）；未有上次記錄（第一日）→ 唔講 */
  function greetDue(s, nowMs) { const m = st(s), key = dayKey(nowMs); return can(s) && !!rec(s, key) && m.greet !== key && !!m.prev; }
  function greetPick(s, nowMs, o) {
    o = o || {}; const m = st(s), key = dayKey(nowMs), r = rec(s, key), gap = r ? r.gap : 0; let pk = null;
    if (gap >= 1) { const cat = gap >= 3 ? 'absent3' : gap === 2 ? 'absent2' : 'absent1'; pk = choose(s, [[cat, { n: gap }]], { nowMs, rng: o.rng, d: '' }); if (!pk) pk = choose(s, [['general', {}]], { nowMs, rng: o.rng }); if (pk) pk.gap = gap; }
    else { const prev = m.prev && rec(s, m.prev); const F = factsOf(prev, o.names), sk = streakTo(s, key); if (sk >= CFG.streakFrom) F.push(['streak', { n: sk }]); F.push(['general', {}]); pk = choose(s, F, { nowMs, rng: o.rng, d: '琴日' }); }
    return pk;
  }
  function greet(s, nowMs, o) { if (!greetDue(s, nowMs) && !(o && o.force)) return null; const pk = greetPick(s, nowMs, o); st(s).greet = dayKey(nowMs); return commit(s, pk, 'greet', nowMs); }
  /* 日記：嗰日（key）自動寫 1 句（{d}＝今日）；preview＝唔記低（今日草稿用） */
  function diaryPick(s, key, nowMs, o) { o = o || {}; const r = rec(s, key); if (!r) return null; const F = factsOf(r, o.names); F.push(['general', {}]); return choose(s, F, { nowMs, rng: o.rng, d: '今日' }); }
  /* 心聲：有機會換成記憶句（每日最多 voicePerDay；今日有嘢講用今日，否則琴日） */
  function voicePick(s, nowMs, o) {
    o = o || {}; const m = st(s), key = dayKey(nowMs), r = o.rng || Math.random; if (!can(s)) return null;
    if (m.vday !== key) { m.vday = key; m.vn = 0; } if (m.vn >= CFG.voicePerDay) return null; if (!o.force && r() >= CFG.voiceChance) return null;
    const tF = factsOf(rec(s, key), o.names).filter(f => !['late', 'early', 'day', 'eve'].includes(f[0]) || rec(s, key).n > 1);   // 今日啱啱嚟嗰下唔講「你今日 X 點嚟」
    let pk = tF.length ? choose(s, tF, { nowMs, rng: r, d: '今日' }) : null;
    if (!pk && m.prev && dn(key) - dn(m.prev) === 1) pk = choose(s, factsOf(rec(s, m.prev), o.names), { nowMs, rng: r, d: '琴日' });
    if (!pk) return null; m.vn++; return commit(s, pk, 'voice', nowMs);
  }
  function takeHappy(s, nowMs) { const m = st(s); if (m.happy && m.happy === dayKey(nowMs) && can(s)) { m.happy = null; m.n.happy++; return true; } return false; }
  function sizeBytes(s) { const j = JSON.stringify(st(s)); let n = 0; for (let i = 0; i < j.length; i++) { const c = j.charCodeAt(i); n += c < 0x80 ? 1 : c < 0x800 ? 2 : (c >= 0xd800 && c < 0xdc00) ? (i++, 4) : 3; } return n; }
  function summary(s, nowMs) { const m = st(s), key = dayKey(nowMs), tdn = dn(key); return { days: Object.keys(m.d).length, last: m.last, prev: m.prev, greet: m.greet, happy: m.happy, today: m.d[key] || null, gap: m.d[key] ? m.d[key].gap : 0, said7: Object.keys(m.said).filter(k => tdn - m.said[k] < CFG.noRepeatDays).length, vn: m.vday === key ? m.vn : 0, bytes: sizeBytes(s), n: Object.assign({}, m.n), log: m.log.slice(-10) }; }
  function reset(s) { delete s.mem6; return st(s); }
  return { CFG, LINES, ALL, BYID, W, MOOD_ZH, KID_EV, CARE_K, dayKey, dn, dayKeyOfDn, st, prune, rec, visit, today, note, scanKid, factsOf, fill, choose, commit, greetDue, greetPick, greet, diaryPick, voicePick, takeHappy, streakTo, sizeBytes, summary, reset };
});
