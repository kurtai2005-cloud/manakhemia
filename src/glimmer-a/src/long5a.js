/* 《微光小圃》 long5a.js — 第 5 批 5a（docs-gdd/series2-4a4b-spec.md v1.1 §5a＋「5a–5c 玩法位定案 2026-11-01 17:50」；遊美 art/series2_long/5a/long_5a.json）：長住＋家族等級。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.fam（sanitize；唔郁 §7 判定、唔加團絨路線分、唔出碎）。
   ・養緊最多 2 隻（1 主養團絨＋1 細佬）；成年（團絨靜光／細佬 S6＋家人）先可以搬入屋；每間房住 4 隻（房 1 計埋主養同養緊嘅細佬）。
   ・成年翌日郵差送新蛋（二揀一）：團絨蛋＝新主養（舊主養搬入屋，新一代照 9 路線×6 階＋§7）；細佬蛋＝大佬係而家主養，行返 4a 孵夢＋教錯課（有細佬養緊就灰「細佬養緊」）。
     第一次靜光照舊 4a 直接送細佬蛋（唔使揀）。
   ・屋內撳成年 →「做主養」：團絨＝同而家主養對調（主養要已成年；成年主養唔再進化，照樣摸／餵／教錯課）；細佬＝帶出花園做主養位（團絨照做大佬；浮動照舊只顯示團絨）。
   ・家族等級 Lv1–10：養大 1 隻 +50、新圖鑑形態 +10、新家具 +5（遠足返 +3 係 5b）；Lv2／5／8 開房 2／3／4（新房空房＋送 1 件隨機手信，手信入家具庫、可以擺）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./series2.js'), require('./house.js'), require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5a = factory(root.Glimmer.series2, root.Glimmer.house, root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (SR, HS, D) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const hash = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const clone = (o) => JSON.parse(JSON.stringify(o));

  /* 同 art/series2_long/5a/long_5a.json 一致（long5a.test.js 對數） */
  const THRESH = [0, 60, 150, 270, 420, 600, 810, 1050, 1320, 1620];
  const XP = { raise_one: 50, dex_new_form: 10, furniture_new: 5, expedition_return: 3 };
  const UNLOCKS = {
    2: [{ id: 'room2', zh: '第 2 間房（森林閣樓）' }],
    3: [{ id: 'visitor_new', zh: '新訪客' }, { id: 'inherit_fast', zh: '遺傳加速（細佬頭 2 階段快 20%）' }],
    4: [{ id: 'furniture_pack1', zh: '6 件新家具' }],
    5: [{ id: 'room3', zh: '第 3 間房（星夜書房）' }],
    6: [{ id: 'kid_series_E', zh: '細佬 E 系' }],
    7: [{ id: 'job_cap_plus1', zh: '工作等級上限 +1（Lv6）' }],
    8: [{ id: 'room4', zh: '第 4 間房（海風小屋）' }],
    9: [{ id: 'furniture_pack2', zh: '6 件新家具' }],
    10: [{ id: 'family_title', zh: '家族稱號' }, { id: 'tree_gold', zh: '金色族譜' }],
  };
  /* 5a 有效（其餘係之後批次：5b 遠足／職業、5c 遺傳；新訪客／家具包／E 系未有美術＝記低解鎖，下批先生效） */
  const LIVE = { room2: 1, room3: 1, room4: 1, family_title: 1, tree_gold: 1 };
  const LATER = { visitor_new: '下批', inherit_fast: '5c', furniture_pack1: '下批', kid_series_E: '4a 已有', job_cap_plus1: '5b', furniture_pack2: '下批' };
  const ROOMS = ['room1', 'room2', 'room3', 'room4'];
  const ROOM = {
    room1: { zh: '屋仔', lv: 1, motif: 'house' },
    room2: { zh: '森林閣樓', lv: 2, motif: 'leaf' },
    room3: { zh: '星夜書房', lv: 5, motif: 'star' },
    room4: { zh: '海風小屋', lv: 8, motif: 'wave' },
  };
  const CAP = 4, RAISE_MAX = 2;
  /* 手信池（遊美 5b/long_5b.json souvenirs；_1x 小擺設 pivot＝底中，擺落地） */
  const SOUV = [
    ['sv_shell', '七彩貝殼', [6, 10]], ['sv_pinecone', '松果', [6, 11]], ['sv_starstone', '星星石', [6, 9]], ['sv_feather', '藍羽毛', [5, 11]], ['sv_mushroom', '細蘑菇', [6, 10]],
    ['sv_maple', '紅楓葉', [6, 10]], ['sv_bottle', '樽中信', [6, 10]], ['sv_cloud', '雲朵糖', [6, 10]], ['sv_lantern', '螢火燈', [6, 10]], ['sv_rainbow', '彩虹糖', [6, 12]],
  ].map(([id, zh, pv]) => ({ id, zh, pv, px: '5b/souvenir/' + id + '_1x.png', icon: '5b/souvenir/' + id + '@3x.png' }));
  const SV = Object.fromEntries(SOUV.map(x => [x.id, x]));
  const DECO_SLOT = 'deco', DECO_ZH = '擺設', DECO_ANCHOR = [72, 284], DECO_PIN = [72, 262];
  const TITLE = '微光大家族';
  const LINES = {
    offer: '蝸牛郵差：「有新蛋！」揀一隻嚟養（最多養 2 隻）', moveTr: '{name}搬咗入{room}', moveKid: '{name}搬咗入{room}', newTr: '新一代團絨蛋嚟咗！', newKid: '新細佬蛋嚟咗！今晚團絨會攬住佢瞓',
    full: '屋企住滿咗（每間房 4 隻）— 升家族等級開新房', raising: '細佬養緊', mainYoung: '主養未成年（團絨到靜光先可以）', notAdult: '未成年',
    madeMain: '{name}做咗主養！', kidOut: '{name}做咗主養！{tr}搬咗入屋住', kidMain: '細佬做緊主養（揀返團絨做主養先孵團絨蛋）', kidYoung: '細佬未成年（成年家人先可以做主養）', mainAlready: '佢已經係主養', roomGift: '新房「{room}」開咗！送咗 1 件手信「{sv}」', lvUp: '家族升到 Lv{lv}！',
  };
  const DAY = 86400000;
  const dayNum = SR.dayNum;

  /* 團絨主養嘅「寵物」欄位（對調／搬入屋用；光粒、設定、統計、圖鑑、花圃等世界資料唔郁） */
  const TR_KEYS = ['stage', 'form', 'gen', 'evo', 'needs', 'sleeping', 'poops', 'poopTimer', 'poopAge', 'growthSec', 'ageSec', 'cq', 'cqTimer', 'withdrawn', 'fadeReady', 'careDays'];

  function st(s) {
    let o = s.fam; if (!obj(o)) o = s.fam = {};
    o.v = 1; o.xp = Math.max(0, +o.xp || 0); o.lv = lvOf(o.xp); o.lvSeen = clamp(o.lvSeen == null ? o.lv : o.lvSeen | 0, 1, 10);
    o.init = +o.init || 0; o.kidN = Math.max(0, o.kidN | 0); o.genMax = Math.max(1, o.genMax | 0);
    if (!obj(o.seen)) o.seen = {}; if (!obj(o.adults)) o.adults = {};
    if (!Array.isArray(o.res)) o.res = [];
    o.res = o.res.filter(r => obj(r) && typeof r.id === 'string' && (r.kind === 'tr' || r.kind === 'kid') && obj(r.snap));
    for (const r of o.res) { if (!ROOMS.includes(r.room)) r.room = 'room1'; r.at = +r.at || 0; r.fk = String(r.fk || (r.kind === 'tr' ? 'sprout' : 'S2')); r.gen = r.gen | 0; }
    if (!obj(o.rooms)) o.rooms = {};
    for (const k of ROOMS) { let r = o.rooms[k]; if (!obj(r)) r = o.rooms[k] = {}; r.open = k === 'room1' ? 1 : (+r.open || 0); if (!obj(r.slots)) r.slots = {};
      for (const sl of Object.keys(r.slots)) if (!HS.SLOTS.includes(sl)) delete r.slots[sl]; if (r.deco != null && !SV[r.deco]) r.deco = null; if (r.deco === undefined) r.deco = null; r.gift = SV[r.gift] ? r.gift : null; }
    if (!obj(o.sv)) o.sv = {}; for (const k of Object.keys(o.sv)) if (!SV[k]) delete o.sv[k];
    if (!obj(o.svPlaced)) o.svPlaced = {};
    if (o.offer != null && !(obj(o.offer) && Number.isFinite(+o.offer.due))) o.offer = null; if (o.offer === undefined) o.offer = null;
    if (o.main != null && typeof o.main !== 'string') o.main = null; if (o.main === undefined) o.main = null;
    if (o.km != null && !(obj(o.km) && typeof o.km.id === 'string' && obj(o.km.snap))) o.km = null; if (o.km === undefined) o.km = null;   // 5a.1：細佬做主養（花園中間＝主養位）
    if (o.km) { o.km.kind = 'kid'; o.km.fk = String(o.km.fk || 'S2'); o.main = 'kid:' + o.km.id; } else if (o.main && o.main.startsWith('kid:')) o.main = null;   // 5a 舊「細佬喺 pet2 做主養」→ 冇效
    if (!Array.isArray(o.lvQ)) o.lvQ = []; o.lvQ = o.lvQ.filter(x => Number.isFinite(+x)).map(x => clamp(x | 0, 2, 10)).slice(-9);
    if (!Array.isArray(o.mem)) o.mem = [];
    if (!Array.isArray(o.log)) o.log = []; if (o.log.length > 60) o.log.splice(0, o.log.length - 60);
    if (!Array.isArray(o.xpLog)) o.xpLog = []; if (o.xpLog.length > 40) o.xpLog.splice(0, o.xpLog.length - 40);
    return o;
  }
  const note = (o, k, x, now) => { o.log.push(Object.assign({ k, at: now || 0 }, x || {})); if (o.log.length > 60) o.log.shift(); };
  function lvOf(xp) { let lv = 1; for (let i = 1; i < THRESH.length; i++) if (xp >= THRESH[i]) lv = i + 1; return lv; }
  function lvInfo(s) { const o = st(s), lv = o.lv, a = THRESH[lv - 1], b = lv >= 10 ? null : THRESH[lv]; return { lv, xp: o.xp, from: a, to: b, max: lv >= 10, pct: b == null ? 1 : clamp((o.xp - a) / (b - a), 0, 1), title: lv >= 10 ? TITLE : null }; }
  const unlockList = (lv) => (UNLOCKS[lv] || []).map(u => Object.assign({ live: !!LIVE[u.id], later: LATER[u.id] || null }, u));
  const unlockedIds = (s) => { const lv = st(s).lv, out = []; for (let i = 2; i <= lv; i++) for (const u of UNLOCKS[i] || []) out.push(u.id); return out; };
  const has = (s, id) => unlockedIds(s).includes(id);
  const roomOpen = (s, k) => k === 'room1' || !!st(s).rooms[k].open;

  /* 經驗：加 → 升級 → 開房（送手信） */
  function addXp(s, key, n, now, why) {
    const o = st(s), lv0 = o.lv; o.xp += n; o.lv = lvOf(o.xp); o.xpLog.push({ key, n, why: why || null, at: now || 0 }); if (o.xpLog.length > 40) o.xpLog.shift();
    const ups = []; for (let L = lv0 + 1; L <= o.lv; L++) { ups.push(L); o.lvQ.push(L); note(o, 'lv', { lv: L }, now); }
    const opened = syncRooms(s, now);
    return { n, lv: o.lv, ups, opened };
  }
  function syncRooms(s, now) {
    const o = st(s), out = [];
    for (const k of ROOMS) { if (k === 'room1') continue; const r = o.rooms[k]; if (r.open || o.lv < ROOM[k].lv) continue;
      r.open = now || 1; const g = giftPick(s, k); if (g) { r.gift = g; o.sv[g] = now || 1; if (!r.deco) { take(s, g); r.deco = g; } }
      note(o, 'room', { room: k, gift: g }, now); out.push({ room: k, gift: g }); }
    return out;
  }
  function giftPick(s, room) {   // 手信池入面未有嘅隨機揀 1 件（種子＋房；全部有晒 → 隨機）
    const o = st(s), left = SOUV.filter(x => !o.sv[x.id]), pool = left.length ? left : SOUV;
    return pool[hash(room + ':' + ((s.seed >>> 0) || 0) + ':' + Object.keys(o.sv).length) % pool.length].id;
  }

  /* 身份：團絨＝'tr'+代；細佬＝pet2.fid（第一次見就派） */
  const trId = (s) => 'tr' + (s.gen || 1);
  function kidId(s) { const p = SR.st(s); if (p.phase === 'none' || p.phase === 'due') return null; const o = st(s); if (!p.fid) { p.fid = 'k' + (++o.kidN); } if (!p.bro) p.bro = trId(s); return p.fid; }
  const kidAdult = (s, now) => { const p = SR.st(s); return p.phase === 'kid' && p.rel === 'family' && SR.stageOf(s, now) === 'S6'; };
  const kidRaising = (s, now) => { const p = SR.st(s); return p.phase === 'egg' || p.phase === 'due' || (p.phase === 'kid' && !kidAdult(s, now)); };
  const trAdult = (s) => s.stage === 'elder';
  /* 5a.1 細佬做主養：o.km＝{ id, line, fk, name, bro, snap（pet2 細佬資料）}；s 嘅團絨欄位凍結（＝屋企最新嗰隻團絨，畀浮動顯示），
     照顧欄位（肚餓／便便／瞓）由細佬用；sim 見 s.fam.km 就唔長大、唔加 §7 路線分、唔出碎 */
  const kmOf = (s) => st(s).km || null;
  const CARE_KEYS = ['needs', 'sleeping', 'poops', 'poopTimer', 'poopAge', 'withdrawn'];
  function snapCare(s) { const o = {}; for (const k of CARE_KEYS) if (s[k] !== undefined) o[k] = clone(s[k]); return o; }
  function applyCare(s, c) {
    if (obj(c) && obj(c.needs)) { for (const k of CARE_KEYS) if (c[k] !== undefined) s[k] = clone(c[k]); return; }
    s.needs = { hunger: 100, mood: 100, clean: 100, energy: 100 }; s.sleeping = false; s.poops = 0; s.poopTimer = 0; s.poopAge = []; s.withdrawn = { on: false, fed: false, played: false };
  }
  const latestTr = (o) => o.res.filter(r => r.kind === 'tr').sort((a, b) => (b.gen | 0) - (a.gen | 0) || (b.at || 0) - (a.at || 0))[0] || null;
  const kidRow = (bro) => (parseInt(String(bro || 'tr1').slice(2), 10) || 1) + 1;

  /* 每 tick：補派身份、成年（+50＋排新蛋）、新圖鑑形態（+10）、新家具（+5）；ctx.kidFk＝而家細佬美術 key；回傳發生咗乜 */
  function scan(s, now, ctx) {
    const o = st(s), ev = []; ctx = ctx || {}; const first = !o.init; if (first) o.init = now || 1;
    o.genMax = Math.max(o.genMax, s.gen || 1, ...o.res.filter(r => r.kind === 'tr').map(r => r.gen || 1), ...((s.memorial || []).map(m => m.gen || 1)));
    const kid = kidId(s);
    const xp = (key, seenKey, why) => { if (o.seen[seenKey]) return; o.seen[seenKey] = now || 1; const r = addXp(s, key, XP[key], now, why); ev.push({ k: 'xp', key, n: r.n, why, ups: r.ups, opened: r.opened }); };
    // 成年
    const adult = (id, kind) => { if (o.adults[id]) return; o.adults[id] = now || 1; xp('raise_one', 'raise:' + id, id); note(o, 'adult', { id, kind }, now);
      const p = SR.st(s); if (kind === 'tr' && (p.phase === 'none' || p.phase === 'due' || p.bro === id)) return;   // 第一次靜光：4a 照舊直接送細佬蛋（佢已經係大佬）
      if (!o.offer) { o.offer = { due: dayNum(now) + 1, at: now || 1, why: id }; ev.push({ k: 'offer', due: o.offer.due }); } };
    if (trAdult(s)) adult(trId(s), 'tr');
    if (kid && kidAdult(s, now)) adult(kid, 'kid');
    for (const r of o.res) if (!o.adults[r.id]) { o.adults[r.id] = r.at || now || 1; if (!o.seen['raise:' + r.id]) xp('raise_one', 'raise:' + r.id, r.id); }
    // 圖鑑
    for (const f of s.dex || []) xp('dex_new_form', 'dex:tr:' + f, f);
    for (const m of s.memorial || []) if (m.form) xp('dex_new_form', 'dex:tr:' + m.form, m.form);
    if (ctx.kidFk && ctx.kidFk !== 'egg') xp('dex_new_form', 'dex:kid:' + ctx.kidFk, ctx.kidFk);
    for (const r of o.res) if (r.kind === 'kid') xp('dex_new_form', 'dex:kid:' + r.fk, r.fk);
    // 家具（4b 家具＋手信）
    const h = HS.st(s); for (const id of HS.IDS) if (h.owned[id]) xp('furniture_new', 'furn:' + id, id);
    for (const id of Object.keys(o.sv)) xp('furniture_new', 'furn:' + id, id);
    const op = syncRooms(s, now); if (op.length) ev.push({ k: 'rooms', opened: op });
    if (first) ev.push({ k: 'init' });
    return ev;
  }

  /* 房：邊個住邊間（房 1：主養團絨＋養緊／出咗花園嘅細佬＋住客） */
  function occupants(s, room) {
    const o = st(s), p = SR.st(s), out = [];
    if (room === 'room1') { const K = o.km; out.push(K ? { id: K.id, kind: 'kid', live: 'main' } : { id: trId(s), kind: 'tr', live: 'main' }); if (p.phase === 'kid') out.push({ id: p.fid || 'kid', kind: 'kid', live: 'kid' }); }
    for (const r of o.res) if (r.room === room) out.push({ id: r.id, kind: r.kind, live: null });
    return out;
  }
  const count = (s, room) => occupants(s, room).length;
  const openRooms = (s) => ROOMS.filter(k => roomOpen(s, k));
  function freeRoom(s, prefer) {   // 有位嘅已開房（優先 prefer → 房 1 → 2 → …）
    const list = openRooms(s); if (prefer && list.includes(prefer) && count(s, prefer) < CAP) return prefer;
    return list.find(k => count(s, k) < CAP) || null;
  }
  const houseFull = (s) => !freeRoom(s);

  /* 新蛋二揀一 */
  const offerReady = (s, now) => { const f = st(s).offer; return !!f && dayNum(now) >= f.due; };
  function choices(s, now) {
    const p = SR.st(s), full = houseFull(s);
    const tr = kmOf(s) ? { ok: false, reason: 'kidMain', zh: LINES.kidMain } : !trAdult(s) ? { ok: false, reason: 'mainYoung', zh: LINES.mainYoung } : full ? { ok: false, reason: 'full', zh: LINES.full } : { ok: true };
    let kid; if (kidRaising(s, now)) kid = { ok: false, reason: 'raising', zh: LINES.raising };
    else if (p.phase === 'kid' && full) kid = { ok: false, reason: 'full', zh: LINES.full };   // 成年細佬要搬入屋先有位
    else kid = { ok: true };
    return { tr, kid, raising: (trAdult(s) ? 0 : 1) + (kidRaising(s, now) ? 1 : 0), max: RAISE_MAX };
  }
  function snapTr(s) { const o = {}; for (const k of TR_KEYS) if (s[k] !== undefined) o[k] = clone(s[k]); if (s.sys12 && s.sys12.bond) o._bond = clone(s.sys12.bond); return o; }
  function applyTr(s, snap) { for (const k of TR_KEYS) if (snap[k] !== undefined) s[k] = clone(snap[k]); if (snap._bond && s.sys12) s.sys12.bond = clone(snap._bond); s.sleeping = false; s.poops = 0; s.poopAge = []; s.poopTimer = 0; }
  function snapKid(s) { const p = SR.st(s), o = clone(p); delete o.house; return o; }
  function applyKid(s, snap) { const house = SR.st(s).house; s.pet2 = clone(snap); if (house) s.pet2.house = house; SR.st(s); }
  function trName(form) { const n = D && D.FORM_NAME && D.FORM_NAME[form]; return n ? n + '團絨' : '團絨'; }
  const kidName = (line) => (line && SR.LINE_ZH[line] ? SR.LINE_ZH[line] + '系細佬' : '細佬');
  function moveInTr(s, now, fk, room) {
    const rm = freeRoom(s, room || 'room1'); if (!rm) return { ok: false, reason: 'full' }; const o = st(s), id = trId(s);
    const r = { id, kind: 'tr', gen: s.gen || 1, form: s.form, fk: fk || 'sprout', name: trName(s.form), room: rm, at: now || 1, snap: snapTr(s) };
    o.res = o.res.filter(x => x.id !== id); o.res.push(r); o.adults[id] = o.adults[id] || now || 1; note(o, 'moveIn', { id, room: rm }, now); return { ok: true, res: r };
  }
  function moveInKid(s, now, fk, room) {
    const p = SR.st(s); if (p.phase !== 'kid') return { ok: false, reason: 'phase' }; const rm = freeRoom(s, room || 'room1'); if (!rm) return { ok: false, reason: 'full' };
    const o = st(s), id = kidId(s), r = { id, kind: 'kid', gen: 0, line: p.line, fk: fk || (p.line ? p.line + '3' : 'S2'), name: kidName(p.line), bro: p.bro || null, room: rm, at: now || 1, snap: snapKid(s) };
    o.res = o.res.filter(x => x.id !== id); o.res.push(r); o.adults[id] = o.adults[id] || now || 1; if (o.main === 'kid:' + id) o.main = null; note(o, 'moveIn', { id, room: rm }, now); return { ok: true, res: r };
  }
  /* 揀蛋；env＝{ rebirth(s, now, gen)（sim 新光卵）, trFk, kidFk } */
  function pick(s, which, now, env) {
    const o = st(s), c = choices(s, now); env = env || {};
    if (which === 'tr') {
      if (!c.tr.ok || o.km) return { ok: false, reason: c.tr.reason || 'kidMain', zh: c.tr.zh || LINES.kidMain };
      const mv = moveInTr(s, now, env.trFk); if (!mv.ok) return mv;
      const g = Math.max(o.genMax, s.gen || 1) + 1; o.genMax = g; if (env.rebirth) env.rebirth(s, now, g); else { s.gen = g; s.stage = 'egg'; s.form = null; s.growthSec = 0; s.fadeReady = false; }
      o.offer = null; o.main = o.main && o.main.startsWith('kid:') ? o.main : null; note(o, 'pick', { which, moved: mv.res.id, gen: g }, now);
      return { ok: true, which, moved: mv.res, gen: g };
    }
    if (which === 'kid') {
      if (!c.kid.ok) return { ok: false, reason: c.kid.reason, zh: c.kid.zh };
      const p = SR.st(s); let moved = null; if (p.phase === 'kid') { const mv = moveInKid(s, now, env.kidFk); if (!mv.ok) return mv; moved = mv.res; }
      const house = p.house, bro = trId(s); s.pet2 = { phase: 'egg', gotAt: now || 1, d0: dayNum(now), elderAt: p.elderAt || now || 1, fid: 'k' + (++o.kidN), bro }; if (house) s.pet2.house = house; SR.st(s);
      o.offer = null; note(o, 'pick', { which, moved: moved && moved.id }, now);
      return { ok: true, which, moved };
    }
    return { ok: false, reason: 'which' };
  }
  const resOf = (s, id) => st(s).res.find(r => r.id === id) || null;
  const entryOf = (s, id) => resOf(s, id) || (kmOf(s) && kmOf(s).id === id ? kmOf(s) : null);
  const isPet2Kid = (s, id) => { const p = SR.st(s); return p.phase === 'kid' && !!id && id === kidId(s); };
  /* 做主養（屋內住客／花園成年細佬）。5a.1 遊策：細佬做主養 → 佔主養位（花園中間），舊主養團絨（靜光）搬入屋長住，pet2 空返等新蛋 */
  function canMain(s, id, now) {
    const K = kmOf(s); if (K ? K.id === id : id === trId(s)) return { ok: false, reason: 'already', zh: LINES.mainAlready };
    const r = resOf(s, id), p2 = !r && isPet2Kid(s, id); if (!r && !p2) return { ok: false, reason: 'notRes' };
    if (r && r.kind === 'tr') return K || trAdult(s) ? { ok: true } : { ok: false, reason: 'mainYoung', zh: LINES.mainYoung };
    if (p2 && !kidAdult(s, now)) return { ok: false, reason: 'kidYoung', zh: LINES.kidYoung };
    if (!K && !trAdult(s)) return { ok: false, reason: 'mainYoung', zh: LINES.mainYoung };
    return { ok: true };
  }
  function makeMain(s, id, now, env) {
    const c = canMain(s, id, now); if (!c.ok) return Object.assign({ ok: false }, c); const o = st(s), K = o.km, r = resOf(s, id); env = env || {};
    if (r && r.kind === 'tr') {
      const room = r.room; o.res = o.res.filter(x => x !== r);
      if (K) {   // 細佬主養返入屋（佢嘅照顧欄位跟埋走）→ 揀嗰隻團絨返主養
        const kr = Object.assign({}, K, { room, at: now || 1, care: snapCare(s) }); applyTr(s, r.snap); s.gen = r.gen || s.gen; o.res.push(kr); o.adults[kr.id] = o.adults[kr.id] || now || 1; o.km = null; o.main = null;
        note(o, 'main', { id, swap: kr.id }, now); return { ok: true, kind: 'tr', name: r.name, swapped: kr };
      }
      const old = { id: trId(s), kind: 'tr', gen: s.gen || 1, form: s.form, fk: env.trFk || 'sprout', name: trName(s.form), room, at: now || 1, snap: snapTr(s) };
      applyTr(s, r.snap); s.gen = r.gen || s.gen; o.res.push(old); o.adults[old.id] = o.adults[old.id] || now || 1; o.main = null;
      note(o, 'main', { id, swap: old.id }, now); return { ok: true, kind: 'tr', name: r.name, swapped: old };
    }
    const p = SR.st(s); let ent, room = null, from;
    if (r) { o.res = o.res.filter(x => x !== r); ent = r; room = r.room; from = 'house'; }
    else { ent = { id, kind: 'kid', gen: 0, line: p.line, fk: env.kidFk || (p.line ? p.line + '3' : 'S2'), name: kidName(p.line), bro: p.bro || null, at: now || 1, snap: snapKid(s) }; from = 'garden';
      const house = p.house; s.pet2 = { phase: 'none', freedAt: now || 1 }; if (house) s.pet2.house = house; SR.st(s); if (!o.offer) o.offer = { due: dayNum(now) + 1, at: now || 1, why: id }; }   // pet2 空返：聽日新蛋（5a 新蛋二揀一）
    let old;
    if (K) old = Object.assign({}, K, { at: now || 1, care: snapCare(s) });
    else old = { id: trId(s), kind: 'tr', gen: s.gen || 1, form: s.form, fk: env.trFk || 'sprout', name: trName(s.form), at: now || 1, snap: snapTr(s) };
    old.room = room && count(s, room) < CAP ? room : (freeRoom(s, 'room1') || room || 'room1');
    o.res = o.res.filter(x => x.id !== old.id); o.res.push(old); o.adults[old.id] = o.adults[old.id] || now || 1;
    if (!K) { const lt = latestTr(o); if (lt && lt.id !== trId(s)) { applyTr(s, lt.snap); s.gen = lt.gen || s.gen; } }   // 浮動：顯示屋企最新嗰隻團絨
    o.km = { id: ent.id, kind: 'kid', gen: 0, line: ent.line || null, fk: ent.fk, name: ent.name, bro: ent.bro || null, at: now || 1, snap: ent.snap };
    applyCare(s, ent.care || null); s.sleeping = false; o.main = 'kid:' + ent.id;
    note(o, 'main', { id, swap: old.id, from }, now); return { ok: true, kind: 'kid', name: ent.name, swapped: old, from, tr: old.kind === 'tr' ? old.name : null };
  }
  const isMain = (s, id) => { const o = st(s); return o.km ? o.km.id === id : !o.main && id === trId(s); };
  function moveRoom(s, id, room) {
    const r = resOf(s, id); if (!r) return { ok: false, reason: 'notRes' }; if (!ROOMS.includes(room) || !roomOpen(s, room)) return { ok: false, reason: 'locked' };
    if (r.room === room) return { ok: false, reason: 'same' }; if (count(s, room) >= CAP) return { ok: false, reason: 'full' }; r.room = room; return { ok: true, room };
  }

  /* 家具通用：每間房 6 slot＋1 個擺設位；一件同時只擺一間 */
  function slotsOf(s, room) { return room === 'room1' ? HS.st(s).slots : st(s).rooms[room].slots; }
  function whereIs(s, id) {
    if (SV[id]) { for (const k of ROOMS) if (st(s).rooms[k].deco === id) return k; return null; }
    for (const k of ROOMS) { const sl = slotsOf(s, k); for (const x of HS.SLOTS) if (sl[x] === id) return k; } return null;
  }
  function take(s, id) {   // 由所有房收起呢件
    if (SV[id]) { for (const k of ROOMS) if (st(s).rooms[k].deco === id) st(s).rooms[k].deco = null; return; }
    for (const k of ROOMS) { const sl = slotsOf(s, k); for (const x of HS.SLOTS) if (sl[x] === id) sl[x] = null; }
  }
  function cardState(s, room, id) {
    if (SV[id]) { if (!st(s).sv[id]) return 'locked'; const w = whereIs(s, id); return w === room ? 'equipped' : w ? 'elsewhere' : 'owned'; }
    const base = HS.cardState(s, id); if (room === 'room1') { if (base === 'equipped') return 'equipped'; if (base !== 'owned') return base; const w = whereIs(s, id); return w && w !== 'room1' ? 'elsewhere' : 'owned'; }
    if (!HS.st(s).owned[id]) return base; const w = whereIs(s, id); return w === room ? 'equipped' : w ? 'elsewhere' : 'owned';
  }
  /* 擺：房 1 行返 house.js（第一次擺心情 +1）；其他房自己記，第一次擺同樣計心情 */
  function place(s, room, slot, id, now, store) {
    if (slot === DECO_SLOT) { const R = st(s).rooms[room]; if (!R || !roomOpen(s, room)) return { ok: false, reason: 'locked' }; if (id == null) { const was = R.deco; R.deco = null; return { ok: true, cleared: was }; }
      if (!SV[id] || !st(s).sv[id]) return { ok: false, reason: 'notOwned' }; const from = whereIs(s, id); take(s, id); R.deco = id; let first = false, mood = null;
      if (!st(s).svPlaced[id]) { st(s).svPlaced[id] = now || 1; first = true; const r = HS.sharedTake(store, now); mood = r.ok; if (r.ok && s.needs) s.needs.mood = Math.min(100, (+s.needs.mood || 0) + HS.CFG.moodAdd); }
      return { ok: true, first, mood, from: from && from !== room ? from : null }; }
    if (room === 'room1') { if (id != null) { const from = whereIs(s, id); if (from && from !== 'room1') { take(s, id); const r = HS.place(s, slot, id, now, store); r.from = from; return r; } } return HS.place(s, slot, id, now, store); }
    if (!roomOpen(s, room)) return { ok: false, reason: 'locked' }; if (!HS.SLOTS.includes(slot)) return { ok: false, reason: 'slot' }; const sl = slotsOf(s, room);
    if (id == null) { const was = sl[slot]; sl[slot] = null; return { ok: true, cleared: was }; }
    const f = HS.FURN[id], h = HS.st(s); if (!f || f.slot !== slot) return { ok: false, reason: 'slot' }; if (!h.owned[id]) return { ok: false, reason: 'notOwned' };
    const from = whereIs(s, id); take(s, id); sl[slot] = id; let first = false, mood = null;
    if (!h.placed[id]) { h.placed[id] = now || 1; first = true; const r = HS.sharedTake(store, now); mood = r.ok; if (r.ok && s.needs) s.needs.mood = Math.min(100, (+s.needs.mood || 0) + HS.CFG.moodAdd); }
    return { ok: true, first, mood, from: from && from !== room ? from : null };
  }
  function blockers(s, room, H) { const sl = slotsOf(s, room), out = []; for (const k of ['bed', 'table', 'lamp']) if (sl[k] && H.walk.blockers[k]) { const a = H.slots[k].anchor, b = H.walk.blockers[k]; out.push([a[0] + b[0], a[1] + b[1], a[0] + b[2], a[1] + b[3]]); } return out; }

  /* 打招呼（遊美 actions.interact.duo）：gap＝max(22, (兩隻 sit 第 0 格 bbox 闊相加)/2 − 4) */
  const duoGap = (w1, w2) => Math.max(22, Math.round((w1 + w2) / 2 - 4));
  const interactFrame = (ms) => clamp(Math.floor(ms / 120), 0, 7);

  /* 族譜：第 N 代 row（團絨第 g 代 → row g；細佬嘅大佬係第 g 代 → row g＋1） */
  function tree(s, now, ctx) {
    const o = st(s), p = SR.st(s), nodes = [], links = []; ctx = ctx || {};
    const add = (n) => { if (!nodes.some(x => x.id === n.id)) nodes.push(n); };
    for (const m of s.memorial || []) add({ id: 'tr' + (m.gen || 1), kind: 'tr', gen: m.gen || 1, row: m.gen || 1, name: trName(m.form), form: m.form, tag: '化光', state: 'memorial' });
    for (const r of o.res) add({ id: r.id, kind: r.kind, gen: r.gen, row: r.kind === 'tr' ? r.gen : (parseInt(String(r.bro || 'tr1').slice(2), 10) || 1) + 1, name: r.name, fk: r.fk, form: r.form || null, line: r.line || null, room: r.room, tag: ROOM[r.room].zh, state: isMain(s, r.id) ? 'main' : 'house', bro: r.bro || null });
    const K = o.km; if (K) add({ id: K.id, kind: 'kid', gen: 0, row: kidRow(K.bro), name: K.name, fk: K.fk, line: K.line, tag: '主養', state: 'main', raising: false, bro: K.bro || null });
    if (!K) add({ id: trId(s), kind: 'tr', gen: s.gen || 1, row: s.gen || 1, name: s.stage === 'egg' ? '團絨蛋' : trName(s.form), form: s.form, fk: ctx.trFk || null, tag: s.stage === 'elder' ? '靜光' : '養緊', state: 'main', raising: !trAdult(s) });
    if (p.phase === 'egg' || p.phase === 'kid') { const id = kidId(s); add({ id, kind: 'kid', gen: 0, row: (parseInt(String(p.bro || trId(s)).slice(2), 10) || 1) + 1, name: p.phase === 'egg' ? '細佬蛋' : kidName(p.line), line: p.line, fk: ctx.kidFk || null, tag: p.phase === 'egg' ? '孵緊' : SR.STAGE_ZH[SR.stageOf(s, now)] || '', state: isMain(s, id) ? 'main' : 'garden', raising: kidRaising(s, now), bro: p.bro || null, lessons: (p.lessons || []).map(l => l.line) }); }
    for (const n of nodes) { if (n.kind === 'tr' && n.gen > 1) { const par = nodes.find(x => x.kind === 'tr' && x.gen === n.gen - 1); if (par) links.push([par.id, n.id]); } if (n.kind === 'kid') { const bro = n.bro || 'tr' + (n.row - 1); if (nodes.some(x => x.id === bro)) links.push([bro, n.id]); } }
    const rows = [...new Set(nodes.map(n => n.row))].sort((a, b) => a - b);
    return { nodes, links, rows, lv: lvInfo(s), gold: o.lv >= 10, title: o.lv >= 10 ? TITLE : null };
  }
  function summary(s, now) {
    const o = st(s); return { lv: o.lv, xp: o.xp, info: lvInfo(s), unlocked: unlockedIds(s), rooms: Object.fromEntries(ROOMS.map(k => [k, { open: roomOpen(s, k), n: count(s, k), deco: o.rooms[k].deco, gift: o.rooms[k].gift, slots: Object.assign({}, slotsOf(s, k)) }])),
      res: o.res.map(r => ({ id: r.id, kind: r.kind, fk: r.fk, name: r.name, room: r.room })), offer: o.offer ? Object.assign({}, o.offer) : null, ready: offerReady(s, now), main: o.main, km: o.km ? { id: o.km.id, fk: o.km.fk, name: o.km.name, line: o.km.line } : null, sv: Object.keys(o.sv), lvQ: o.lvQ.slice(), choices: choices(s, now) };
  }

  return { THRESH, XP, UNLOCKS, LIVE, LATER, ROOMS, ROOM, CAP, RAISE_MAX, SOUV, SV, DECO_SLOT, DECO_ZH, DECO_ANCHOR, DECO_PIN, TITLE, LINES, TR_KEYS, DAY,
    st, lvOf, lvInfo, unlockList, unlockedIds, has, roomOpen, addXp, syncRooms, giftPick, trId, kidId, kidAdult, kidRaising, trAdult, scan,
    occupants, count, openRooms, freeRoom, houseFull, offerReady, choices, snapTr, applyTr, snapKid, applyKid, trName, kidName, moveInTr, moveInKid, pick, resOf, entryOf, isPet2Kid, kmOf, snapCare, applyCare, latestTr, canMain, makeMain, isMain, moveRoom,
    slotsOf, whereIs, take, cardState, place, blockers, duoGap, interactFrame, tree, summary };
});
