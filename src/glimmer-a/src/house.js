/* 《微光小圃》 house.js — 第 4 批 4b（docs-gdd/series2-4a4b-spec.md v1.1 §4b＋「4b 家具定案 2026-11-01」）：屋仔。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.pet2.house（sanitize；唔郁團絨成長／路線）。
   入口：細佬做咗家人先開；入屋預設送葉仔床（唔收碎、計新家具心情 +1）；6 擺位（床／檯／牆／地氈／窗／燈）各 2 件＝12 件：
   碎商店 7 件（15–40 碎，共 165）、委託獎 2 件（家人後完成委託 3／9 張）、訪客友誼 5 獎 2 件（蘑菇婆婆蘑菇燈、螢火小販螢火瓶燈；舊裝飾獎照送，唔拎走）。
   隨時換擺唔使碎；每件第一次擺：心情 +1（同觸摸／浮動團絨共用每日上限 5）；整蠱每日最多 3 次、唔加親密；21:00–03:00 同床瞓；冇路線分、唔出碎。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./series2.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.house = factory(root.Glimmer.series2); }
})(typeof self !== 'undefined' ? self : this, function (SR) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const SLOTS = ['bed', 'table', 'wall', 'rug', 'window', 'lamp'];
  const SLOT_ZH = { bed: '床', table: '檯', wall: '牆', rug: '地氈', window: '窗', lamp: '燈' };
  /* 同 art/series2_house/house.json furniture 一致（house.test.js 對數） */
  const FURN = {
    bed_leaf: { slot: 'bed', zh: '葉仔床', price: 0, src: 'default' },
    bed_cloud: { slot: 'bed', zh: '雲朵床', price: 40, src: 'shop' },
    table_stump: { slot: 'table', zh: '樹樁檯', price: 20, src: 'shop' },
    table_round: { slot: 'table', zh: '格仔布圓檯', price: 25, src: 'shop' },
    wall_shelf: { slot: 'wall', zh: '小盆栽層架', price: 18, src: 'shop' },
    wall_frame: { slot: 'wall', zh: '團絨相框', price: null, src: 'commission' },
    rug_round: { slot: 'rug', zh: '粉粉圓地氈', price: 22, src: 'shop' },
    rug_leaf: { slot: 'rug', zh: '葉仔地氈', price: 15, src: 'shop' },
    win_curtain: { slot: 'window', zh: '蕾絲窗簾', price: 25, src: 'shop' },
    win_star: { slot: 'window', zh: '星星窗', price: null, src: 'commission' },
    lamp_mushroom: { slot: 'lamp', zh: '蘑菇燈', price: null, src: 'visitor:mushroom_granny' },
    lamp_firefly: { slot: 'lamp', zh: '螢火瓶燈', price: null, src: 'visitor:firefly_vendor' },
  };
  const IDS = Object.keys(FURN);
  const CFG = {
    commission: { wall_frame: 3, win_star: 9 },     // 家人之後完成委託張數（每日 3 張 → 第 1 日／第 3 日）
    prankPerDay: 3, sleepHours: [21, 3], moodAdd: 1, sharedCap: 5, sharedKey: 'fpet_daily_v1',
  };
  const SRC_ZH = (id) => { const f = FURN[id]; if (!f) return ''; if (f.src === 'shop') return f.price + ' 碎'; if (f.src === 'default') return '入屋預設'; if (f.src === 'commission') return '委託獎（家人後完成 ' + CFG.commission[id] + ' 張委託）';
    return f.src === 'visitor:mushroom_granny' ? '蘑菇婆婆友誼 5' : '螢火小販友誼 5'; };
  const LINES = {
    locked: '同細佬做咗家人就可以一齊住', welcome: '細佬同團絨搬咗入屋仔！送咗張葉仔床', firstMood: '第一次擺：心情 +1', firstCap: '第一次擺（今日心情加夠喇）',
    bought: '買咗「{name}」', poor: '碎唔夠', got: '收到新家具「{name}」（{src}）', prank: '哇！', sleep: '兩隻一齊瞓緊床',
  };
  const dayKey = (t) => { const d = new Date(t); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  const hourOf = (t) => { const d = new Date(t); return d.getHours() + d.getMinutes() / 60; };
  const sleepTime = (t) => { const h = hourOf(t); return h >= CFG.sleepHours[0] || h < CFG.sleepHours[1]; };

  function st(s) {
    const p = SR.st(s); let o = p.house; if (!obj(o)) o = p.house = {};
    o.v = 1; o.at = +o.at || 0; o.q0 = Math.max(0, o.q0 | 0); o.qb = Math.max(0, o.qb | 0);   /* qb：5b 郵差助手幫手嘅委託進度 */
    if (!obj(o.owned)) o.owned = {}; for (const k of Object.keys(o.owned)) if (!FURN[k]) delete o.owned[k];
    if (!obj(o.placed)) o.placed = {}; for (const k of Object.keys(o.placed)) if (!FURN[k]) delete o.placed[k];
    if (!obj(o.slots)) o.slots = {}; for (const k of Object.keys(o.slots)) if (!SLOTS.includes(k)) delete o.slots[k];
    for (const k of SLOTS) { const v = o.slots[k]; if (v != null && !(FURN[v] && FURN[v].slot === k && o.owned[v])) o.slots[k] = null; if (o.slots[k] === undefined) o.slots[k] = null; }
    if (!obj(o.prank)) o.prank = {}; if (typeof o.prank.d !== 'string') o.prank.d = ''; o.prank.n = Math.max(0, o.prank.n | 0); o.prank.total = Math.max(0, o.prank.total | 0);
    o.seen = !!o.seen; o.welcomed = !!o.welcomed; o.visits = Math.max(0, o.visits | 0);
    return o;
  }
  const unlocked = (s) => { const p = SR.st(s); return (p.phase === 'kid' && p.rel === 'family') || !!(p.house && p.house.at) || !!(s.fam && Array.isArray(s.fam.res) && s.fam.res.length);   /* 5a：開咗屋就一直開（新細佬蛋都唔會鎖返）；有長住成年都開 */ };
  const paidN = (s) => { const q = s && s.sys12 && s.sys12.quests; return q ? q.paidN | 0 : 0; };
  const visitMax = (s, who) => { const v = s && s.b3b && s.b3b.vis && s.b3b.vis[who]; return !!(v && v.max); };

  /* 家人解鎖嗰刻：記低委託基數（之後完成嘅先計）＋送葉仔床（擺好；第一次擺心情喺入屋嗰陣計） */
  function ensure(s, now) {
    const o = st(s); if (!unlocked(s)) return { ok: false, reason: 'locked' };
    let fresh = false;
    if (!o.at) { o.at = now || 1; o.q0 = paidN(s); o.owned.bed_leaf = o.owned.bed_leaf || o.at; if (!o.slots.bed) o.slots.bed = 'bed_leaf'; fresh = true; }
    return { ok: true, fresh };
  }
  /* 委託／訪客獎：條件達到 → 入 owned（回新得到嘅 id） */
  function syncRewards(s, now) {
    const o = st(s); if (!o.at) return [];
    const out = [], n = paidN(s) - o.q0 + o.qb;
    for (const id of ['wall_frame', 'win_star']) if (!o.owned[id] && n >= CFG.commission[id]) { o.owned[id] = now || 1; out.push(id); }
    if (!o.owned.lamp_mushroom && visitMax(s, 'mushroom_granny')) { o.owned.lamp_mushroom = now || 1; out.push('lamp_mushroom'); }
    if (!o.owned.lamp_firefly && visitMax(s, 'firefly_vendor')) { o.owned.lamp_firefly = now || 1; out.push('lamp_firefly'); }
    return out;
  }
  const commissionLeft = (s, id) => { const o = st(s); return Math.max(0, CFG.commission[id] - (paidN(s) - o.q0 + o.qb)); };
  /* 卡狀態：equipped／owned／buy／locked */
  function cardState(s, id) { const o = st(s), f = FURN[id]; if (!f) return null; if (o.slots[f.slot] === id) return 'equipped'; if (o.owned[id]) return 'owned'; return f.src === 'shop' ? 'buy' : 'locked'; }
  /* 買（spend＝sys12 錢包 spend(s, n) → bool）*/
  function buy(s, id, spend, now) {
    const o = st(s), f = FURN[id]; if (!o.at) return { ok: false, reason: 'locked' }; if (!f || f.src !== 'shop') return { ok: false, reason: 'notShop' };
    if (o.owned[id]) return { ok: false, reason: 'owned' }; if (!spend || !spend(s, f.price)) return { ok: false, reason: 'poor' };
    o.owned[id] = now || 1; return { ok: true, price: f.price, name: f.zh };
  }
  /* 共用每日心情額（同 touch.js／fpet-bridge 一樣 key＋dayKey 冇補 0） */
  const bridgeDay = (t) => { const d = new Date(t); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); };
  function sharedTake(store, t) {
    let m = {}; try { m = JSON.parse((store && store.get(CFG.sharedKey)) || '{}') || {}; } catch (e) { m = {}; } if (!obj(m)) m = {};
    const k = bridgeDay(t), n = +m[k] || 0; if (n >= CFG.sharedCap) return { ok: false, shared: n };
    const keep = {}; Object.keys(m).slice(-7).forEach(x => { keep[x] = m[x]; }); keep[k] = n + 1;
    try { store && store.set(CFG.sharedKey, JSON.stringify(keep)); } catch (e) { } return { ok: true, shared: n + 1 };
  }
  /* 擺／換／收起（id＝null 收起）；第一次擺呢件 → 心情 +1（共用上限） */
  function place(s, slot, id, now, store) {
    const o = st(s); if (!o.at) return { ok: false, reason: 'locked' }; if (!SLOTS.includes(slot)) return { ok: false, reason: 'slot' };
    if (id == null) { const was = o.slots[slot]; o.slots[slot] = null; return { ok: true, cleared: was }; }
    const f = FURN[id]; if (!f || f.slot !== slot) return { ok: false, reason: 'slot' }; if (!o.owned[id]) return { ok: false, reason: 'notOwned' };
    o.slots[slot] = id; let first = false, mood = null;
    if (!o.placed[id]) { o.placed[id] = now || 1; first = true; const r = sharedTake(store, now); mood = r.ok; if (r.ok && s.needs) s.needs.mood = Math.min(100, (+s.needs.mood || 0) + CFG.moodAdd); }
    return { ok: true, first, mood };
  }
  /* 第一次入屋：葉仔床當新家具擺（計心情） */
  function enter(s, now, store) {
    const e = ensure(s, now); if (!e.ok) return e; const o = st(s); o.visits++; let welcome = null;
    if (!o.welcomed) { o.welcomed = true; welcome = o.slots.bed && !o.placed[o.slots.bed] ? place(s, 'bed', o.slots.bed, now, store) : { ok: true, first: false, mood: null }; }
    o.seen = true; return { ok: true, fresh: e.fresh, welcome, got: syncRewards(s, now) };
  }
  /* 整蠱：每日最多 3 次 */
  function canPrank(s, now) { const o = st(s); if (!o.at) return false; const d = dayKey(now); return o.prank.d !== d || o.prank.n < CFG.prankPerDay; }
  function notePrank(s, now) { const o = st(s); if (!canPrank(s, now)) return false; const d = dayKey(now); if (o.prank.d !== d) { o.prank.d = d; o.prank.n = 0; } o.prank.n++; o.prank.total++; return true; }
  const prankLeft = (s, now) => { const o = st(s), d = dayKey(now); return o.prank.d === d ? Math.max(0, CFG.prankPerDay - o.prank.n) : CFG.prankPerDay; };
  /* 行走區：walk.rect 減有擺嘅 bed／table／lamp blocker（anchor＋blocker） */
  function blockers(s, H) { const o = st(s), out = []; for (const k of ['bed', 'table', 'lamp']) if (o.slots[k] && H.walk.blockers[k]) { const a = H.slots[k].anchor, b = H.walk.blockers[k]; out.push([a[0] + b[0], a[1] + b[1], a[0] + b[2], a[1] + b[3]]); } return out; }
  function walkable(x, y, rect, bl) { if (x < rect[0] || x > rect[2] || y < rect[1] || y > rect[3]) return false; for (const b of bl) if (x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]) return false; return true; }
  function pickSpot(rect, bl, rnd) { rnd = rnd || Math.random; for (let i = 0; i < 40; i++) { const x = Math.round(rect[0] + rnd() * (rect[2] - rect[0])), y = Math.round(rect[1] + rnd() * (rect[3] - rect[1])); if (walkable(x, y, rect, bl)) return [x, y]; } return [Math.round((rect[0] + rect[2]) / 2), rect[3]]; }
  /* 狀態摘要（QA／卡） */
  function summary(s, now) { const o = st(s); return { unlocked: unlocked(s), at: o.at, owned: IDS.filter(k => o.owned[k]), slots: Object.assign({}, o.slots), placed: Object.keys(o.placed), prankLeft: prankLeft(s, now), seen: o.seen, visits: o.visits, commissionN: paidN(s) - o.q0 }; }

  return { SLOTS, SLOT_ZH, FURN, IDS, CFG, LINES, SRC_ZH, dayKey, hourOf, sleepTime, st, unlocked, ensure, syncRewards, commissionLeft, cardState, buy, sharedTake, place, enter, canPrank, notePrank, prankLeft, blockers, walkable, pickSpot, summary };
});
