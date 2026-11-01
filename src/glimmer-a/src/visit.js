/* 《微光小圃》 visit.js — 第 3 批 3b（docs-gdd/batch3-fun-spec.md §③④）：朋友訪客＋進化大場面＋小故事。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.b3b（sanitize）、訪客排程（存檔第 3 日起、每日最多 1 位、螢火小販 17–07）、友好度／送禮（每位每日 1 次、滿 5 → 擺設＋徽章）、
   帶路 loop 路徑、進化大場面時間軸（遊美 batch3b.json evolution.timeline 嘅數學）、進化預兆（達下一階前最後 min(24h, 25%) 窗口，隨機 1 款）、四格小故事解鎖。
   唔加路線分、唔經 sim.noteCare（唔計 CQ）→ §7 平衡唔郁；預兆「胃口大」只係視覺＋一句（sim 飽肚唔變）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./data.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.visit = factory(root.Glimmer.data); }
})(typeof self !== 'undefined' ? self : this, function (D) {
  'use strict';
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const DAY = 86400000;
  const dayNum = (ms) => { const d = new Date(ms); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / DAY); };
  const dayKey = (ms) => { const d = new Date(ms); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };

  // ── 設定（遊美 batch3b.json visitRules／visitors；遊策 batch3-fun-spec §③④）──
  const VISITORS = ['snail_postman', 'mushroom_granny', 'firefly_vendor'];
  const CFG = {
    startDay: 3, perDay: 1, staySec: 600, vendorHours: [17, 7], enterX: [-30, 225], standDx: 46, groundY: 292,
    delaySec: [20, 90],                   // 上線後隨機 20–90s 先嚟（spec「隨機一次上線時出」）
    friendMax: 5, giftPerDay: 1,
    lead: { loop: [[97, 296], [128, 300], [150, 292], [132, 284], [97, 282], [62, 284], [44, 292], [66, 300], [97, 296]], lapMs: 8000, followGap: 30, walkMul: 0.7, startMs: 900, afterArriveMs: 400 },
    decor: { snail_postman: 'deco_mailbox', mushroom_granny: 'deco_mushroom_lamp', firefly_vendor: 'deco_firefly_jar' },
    decorAt: { deco_mailbox: [22, 300], deco_mushroom_lamp: [174, 298], deco_firefly_jar: [150, 280] },   // 花圃固定位（art 座標 pivot）
    shop: [{ id: 'deco_mailbox', price: 12 }, { id: 'deco_mushroom_lamp', price: 16 }, { id: 'deco_firefly_jar', price: 20 }],   // 螢火小販：10–20 碎
    walkSpeed: { snail_postman: 10, mushroom_granny: 14, firefly_vendor: 20 },
  };
  const NAME = { snail_postman: '蝸牛郵差', mushroom_granny: '蘑菇婆婆', firefly_vendor: '螢火小販' };
  const DECOR_NAME = { deco_mailbox: '郵筒仔', deco_mushroom_lamp: '蘑菇燈', deco_firefly_jar: '螢火瓶燈' };
  const BADGE = { snail_postman: 'friend_snail', mushroom_granny: 'friend_granny', firefly_vendor: 'friend_vendor' };
  // 文案表（遊策可整張替換；key 唔好改）。自信錯誤、短句。
  const LINES = {
    arrive: { snail_postman: '蝸牛郵差慢慢爬咗入嚟：「有你嘅信！」', mushroom_granny: '蘑菇婆婆嚟探你：「後生仔，種花未？」', firefly_vendor: '螢火小販飄咗入嚟：「平嘢！夜晚先有㗎！」' },
    lead: '跟我嚟，我帶你參觀！（我好熟路）',
    leave: '{name}揮揮手走咗。',
    gift: '{name}好開心！友好度 {fr}/5',
    giftDone: '今日送過喇，聽日再嚟啦',
    friendMax: '{name}同你係好朋友喇！送咗「{decor}」俾你',
    letters: [
      '信：「你好，我係一封信。完。」',
      '信：「團絨，你今日都好醒。」（寄件人：團絨）',
      '信：「落雨記得帶遮，或者帶片葉。」',
      '信：「我寫咗好耐，因為我係蝸牛。」',
      '信：「聽講你識數到十？好犀利。」',
      '信：「花圃嘅螢火蟲話你好得意。」',
      '信：「呢封信本來係俾月亮嘅，寄錯咗。」',
      '信：「多謝你昨日望咗我一眼。」',
    ],
    tips: [
      '婆婆：「種落去要日日淋水，唔好偷懶。」',
      '婆婆：「兩日唔淋水，花會垂頭㗎。」',
      '婆婆：「開咗花可以剪落花瓶，好靚。」',
      '婆婆：「唔同花有唔同路，團絨會跟住變。」',
      '婆婆：「種子免費，下次種花唔使錢。」',
    ],
    seed: '蘑菇婆婆送咗 1 粒種子（下次種花免費）',
    vendor: '小販：「擺設，平賣！」',
    bought: '買咗「{decor}」，擺咗喺花圃',
    owned: '已經有喇',
    shards: '星星碎唔夠',
    omenStrong: '我覺得自己就嚟好勁',
    freeFlower: '路邊小花',
  };
  // 名卡呆介紹（遊策待審：自信錯誤一句；名＝batch3b.json cards.formName）
  const CARD_LINE = {
    evo_dot: '啱啱出世，已經覺得自己好有經驗。', evo_sprout: '頭頂有片葉，所以宜家係植物學家。', evo_hop: '跳得唔高，但落地好有氣勢。',
    evo_guard_tide: '自稱游水冠軍，其實未落過水。', evo_guard_moon: '夜晚先開工，企住都瞓得著。', evo_guard_shroom: '落雨最開心，覺得自己係菇。',
    evo_guard_crystal: '好鍾意乾淨，連影都要閃。', evo_guard_ember: '心入面有團火，有時其實係肚餓。', evo_guard_radiant: '全身發光，因為自己好叻。',
    evo_guard_soft: '軟綿綿，自認係全花園最強。', evo_guard_dust: '細細粒，但諗嘢好大。', evo_guard_lumi: '夜晚會發光，方便你搵到佢。',
    evo_still_tide: '睇過好多潮水，識得唔郁。', evo_still_moon: '同月光好熟，成日傾偈。', evo_still_shroom: '靜靜咁長大，好有智慧咁。',
    evo_still_crystal: '一塵不染，連諗嘢都好透明。', evo_still_ember: '火細咗，但仲係好暖。', evo_still_radiant: '光柔咗，自己話係成熟。',
    evo_still_soft: '更加軟，仲識得安慰人。', evo_still_dust: '似一粒塵，其實係一粒星。', evo_still_lumi: '光好穩定，似一盞小夜燈。',
  };
  const ROUTE_ZH = { tide: '潮汐', moon: '月影', shroom: '菇菇', crystal: '晶石', ember: '餘燼', radiant: '燦光', soft: '柔光', dust: '微塵', lumi: '螢光' };
  const NODES = ['n1', 'n2', 'n3', 'n4', 'n5'];

  // ── 存檔 s.b3b ──
  function st(s) {
    let o = s.b3b; if (!obj(o)) o = s.b3b = {};
    o.v = 1;
    if (!obj(o.day)) o.day = {}; const d = o.day; if (typeof d.k !== 'string') d.k = ''; if (d.who != null && !VISITORS.includes(d.who)) d.who = null; if (d.who === undefined) d.who = null; d.at = +d.at || 0;
    if (!obj(d.gift)) d.gift = {};
    if (!obj(o.vis)) o.vis = {}; for (const k of Object.keys(o.vis)) if (!VISITORS.includes(k)) delete o.vis[k];
    for (const k of VISITORS) { let v = o.vis[k]; if (!obj(v)) v = o.vis[k] = {}; v.fr = clamp(v.fr | 0, 0, CFG.friendMax); v.met = Math.max(0, v.met | 0); v.last = +v.last || 0; v.max = !!v.max; }
    if (!obj(o.decor)) o.decor = {}; for (const k of Object.keys(o.decor)) if (!DECOR_NAME[k]) delete o.decor[k];
    o.seeds = Math.max(0, Math.min(9, o.seeds | 0));
    if (!Array.isArray(o.letters)) o.letters = []; o.letters = o.letters.filter(x => obj(x) && typeof x.line === 'string').slice(-30);
    if (!obj(o.comics)) o.comics = {}; for (const k of Object.keys(o.comics)) if (!NODES.includes(k)) delete o.comics[k];
    for (const k of Object.keys(o.comics)) { const c = o.comics[k]; if (!obj(c)) { delete o.comics[k]; continue; } c.at = +c.at || 0; if (!Array.isArray(c.routes)) c.routes = []; c.routes = c.routes.filter(r => ROUTE_ZH[r]); }
    if (!obj(o.stats)) o.stats = {}; const S = o.stats; S.visits = Math.max(0, S.visits | 0); S.gifts = Math.max(0, S.gifts | 0); S.scenes = Math.max(0, S.scenes | 0); S.skips = Math.max(0, S.skips | 0); S.omens = Math.max(0, S.omens | 0);
    return o;
  }
  const saveDay = (s, now) => dayNum(now) - dayNum(+s.createdAt || now) + 1;
  const vendorOpen = (hour) => { const h = ((+hour % 24) + 24) % 24; return h >= CFG.vendorHours[0] || h < CFG.vendorHours[1]; };
  /* 今日可唔可以有訪客：{ok, reason}（egg／early／done） */
  function canVisit(s, now) {
    const o = st(s); if (s.stage === 'egg') return { ok: false, reason: 'egg' };
    if (saveDay(s, now) < CFG.startDay) return { ok: false, reason: 'early' };
    if (o.day.k === dayKey(now) && o.day.who) return { ok: false, reason: 'done' };
    return { ok: true };
  }
  /* 揀邊位：未見過任何訪客 → 蝸牛郵差（先做呢隻）；其餘隨機（小販只 17–07），見得少嘅優先 */
  function pickVisitor(s, hour, rng) {
    const o = st(s), r = rng || Math.random;
    if (!VISITORS.some(k => o.vis[k].met > 0)) return 'snail_postman';
    const c = VISITORS.filter(k => k !== 'firefly_vendor' || vendorOpen(hour));
    const w = c.map(k => 1 / (1 + o.vis[k].met * 0.25)), tot = w.reduce((a, b) => a + b, 0);
    let x = r() * tot; for (let i = 0; i < c.length; i++) { x -= w[i]; if (x <= 0) return c[i]; } return c[c.length - 1];
  }
  function startVisit(s, who, now) {
    const o = st(s); if (!VISITORS.includes(who)) return { ok: false, reason: 'who' };
    o.day = { k: dayKey(now), who, at: now, gift: {} }; const v = o.vis[who]; v.met++; v.last = now; o.stats.visits++;
    return { ok: true, who, name: NAME[who] };
  }
  /* 送禮：每位每日 1 次 → 友好度 +1；滿 5（第一次）→ 擺設＋徽章 */
  function gift(s, who, now) {
    const o = st(s); if (!VISITORS.includes(who)) return { ok: false, reason: 'who' };
    const dk = dayKey(now); if (o.day.k !== dk) o.day = { k: dk, who: o.day.who && o.day.k === dk ? o.day.who : null, at: o.day.at, gift: {} };
    if ((o.day.gift[who] | 0) >= CFG.giftPerDay) return { ok: false, reason: 'daily' };
    const v = o.vis[who]; o.day.gift[who] = (o.day.gift[who] | 0) + 1; o.stats.gifts++;
    if (v.fr >= CFG.friendMax) return { ok: true, fr: v.fr, max: true, reward: null };
    v.fr++; let reward = null;
    if (v.fr >= CFG.friendMax && !v.max) { v.max = true; const dc = CFG.decor[who]; const had = !!o.decor[dc]; o.decor[dc] = o.decor[dc] || now; reward = { decor: dc, decorName: DECOR_NAME[dc], had, badge: BADGE[who] }; }
    return { ok: true, fr: v.fr, max: v.fr >= CFG.friendMax, reward };
  }
  /* 禮物：花瓶花（消耗 1）／散步收集品（重覆 ≥2 先送，消耗 1）；乜都冇 → 免費「路邊小花」（唔消耗） */
  function giftItems(s, sb) {
    const out = []; const g = sb || {};
    const vase = (g.garden && g.garden.vase) || {}; for (const k of Object.keys(vase)) if ((vase[k] | 0) > 0) out.push({ kind: 'vase', k, n: vase[k] | 0 });
    const got = (g.walk && g.walk.got) || {}; for (const k of Object.keys(got)) if ((got[k] | 0) >= 2) out.push({ kind: 'walk', k, n: (got[k] | 0) - 1 });
    if (!out.length) out.push({ kind: 'free', k: 'roadside', n: 1 });
    return out;
  }
  function takeItem(s, sb, it) {
    if (!it) return false; if (it.kind === 'free') return true;
    if (it.kind === 'vase') { const v = sb && sb.garden && sb.garden.vase; if (!v || (v[it.k] | 0) < 1) return false; v[it.k]--; if (!v[it.k]) delete v[it.k]; return true; }
    if (it.kind === 'walk') { const g = sb && sb.walk && sb.walk.got; if (!g || (g[it.k] | 0) < 2) return false; g[it.k]--; return true; }
    return false;
  }
  /* 蝸牛信：一句日記（輪住抽，唔重覆到抽晒） */
  function letter(s, now, rng) {
    const o = st(s), L = LINES.letters, used = new Set(o.letters.slice(-(L.length - 1)).map(x => x.line));
    const c = L.filter(l => !used.has(l)), line = (c.length ? c : L)[Math.floor((rng || Math.random)() * (c.length || L.length))];
    o.letters.push({ line, t: now }); if (o.letters.length > 30) o.letters.shift(); return line;
  }
  /* 蘑菇婆婆種子（每次探 1 粒，最多存 9）：下次種花免費 */
  function seedGift(s) { const o = st(s); o.seeds = Math.min(9, o.seeds + 1); return o.seeds; }
  function useSeed(s) { const o = st(s); if (o.seeds < 1) return false; o.seeds--; return true; }
  /* 螢火小販：擺設 10–20 碎（spend 由呼叫者傳入 sys12.spend） */
  function buy(s, id, spend, now) {
    const o = st(s), it = CFG.shop.find(x => x.id === id); if (!it) return { ok: false, reason: 'item' };
    if (o.decor[id]) return { ok: false, reason: 'owned' };
    if (!spend(s, it.price)) return { ok: false, reason: 'shards' };
    o.decor[id] = now || 1; return { ok: true, price: it.price, name: DECOR_NAME[id] };
  }

  // ── 帶路 loop（art 座標；團絨行頭、訪客落後 path 距離 followGap）──
  const LOOP = CFG.lead.loop;
  const SEG = (() => { const a = [0]; for (let i = 1; i < LOOP.length; i++) a.push(a[i - 1] + Math.hypot(LOOP[i][0] - LOOP[i - 1][0], LOOP[i][1] - LOOP[i - 1][1])); return a; })();
  const LOOP_LEN = SEG[SEG.length - 1];
  /* d＝path 距離（可負，loop 循環）→ {x,y,dir}（dir：行進方向 ±1） */
  function pathPt(d) {
    d = ((d % LOOP_LEN) + LOOP_LEN) % LOOP_LEN;
    let i = 1; while (i < SEG.length - 1 && SEG[i] < d) i++;
    const a = LOOP[i - 1], b = LOOP[i], L = SEG[i] - SEG[i - 1] || 1, u = (d - SEG[i - 1]) / L;
    return { x: a[0] + (b[0] - a[0]) * u, y: a[1] + (b[1] - a[1]) * u, dir: b[0] >= a[0] ? 1 : -1 };
  }
  /* 帶路 ms → 團絨／訪客位置（一圈 lapMs）。rev＝由右邊入嘅訪客：成條 loop 以 x=97 鏡像（先向左行），訪客跟尾點就喺右邊 */
  function leadAt(ms, rev) {
    const sp = LOOP_LEN / CFG.lead.lapMs, d = ms * sp, m = (p) => rev ? { x: 194 - p.x, y: p.y, dir: -p.dir } : p;
    return { pet: m(pathPt(d)), vis: m(pathPt(d - CFG.lead.followGap)), speed: sp * 1000, lap: Math.floor(ms / CFG.lead.lapMs) };
  }

  // ── 進化大場面時間軸（遊美 batch3b.json evolution.timeline；8000ms，2000ms 後可跳）──
  const TL = { dur: 8000, skipAfter: 2000, skipTo: 5600, cardDelay: 300, reveal: 5600, cardIn: 6000, cardOut: 7500, cardEnd: 7700,
    swaps: [4400, 4620, 4800, 4940, 5050, 5140, 5210, 5270, 5320, 5360, 5400, 5440, 5480, 5520, 5560], nameAt: 6400, lineAt: 6600, typeMs: 30 };
  const E = { ioSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2, oCubic: (t) => 1 - Math.pow(1 - t, 3), iBack: (t) => { const c = 1.70158; return (c + 1) * t * t * t - c * t * t; } };
  function keys(u, ks, vs, ease) {
    if (u <= ks[0]) return vs[0]; for (let i = 1; i < ks.length; i++) if (u <= ks[i]) { let f = (u - ks[i - 1]) / (ks[i] - ks[i - 1]); if (ease) f = ease(f); return vs[i - 1] + (vs[i] - vs[i - 1]) * f; }
    return vs[vs.length - 1];
  }
  function dimAt(t) { return t < 600 ? 0.7 * E.ioSine(t / 600) : t < 5600 ? 0.7 : t < 6000 ? 0.7 - 0.25 * (t - 5600) / 400 : t < 7700 ? 0.45 : t < 8000 ? 0.45 * (1 - (t - 7700) / 300) : 0; }
  /* 寵物軌：{show:'old'|'new'|'cocoon'|null, sil:剪影?, dx, sx, sy, face, clip} */
  function petAt(t) {
    if (t < 1500) {
      const k = clamp((t - 300) / 1200, 0, 1) * 1.5, dx = Math.round(Math.sin(t * 0.09) * k);
      let sil = false; if (t >= 900) { const iv = t < 1200 ? 120 : 60; sil = Math.floor((t - 900) / iv) % 2 === 0; }
      return { show: 'old', sil, dx, sx: 1, sy: 1, clip: t < 300 ? 'idle' : 'emo_surprised' };
    }
    if (t < 4400) return { show: 'cocoon', sil: true, dx: 0, sx: 1, sy: 1 };
    if (t < 5600) {
      let n = 0, last = TL.swaps[0]; for (const w of TL.swaps) if (w <= t) { n++; last = w; }
      const nw = n % 2 === 1 || n === TL.swaps.length, u = clamp((t - last) / 90, 0, 1);
      return { show: nw ? 'new' : 'old', sil: true, dx: 0, sx: 1.15 + (1 - 1.15) * u, sy: 0.88 + (1 - 0.88) * u, swaps: n };
    }
    const u = t - 5600;
    return { show: 'new', sil: false, dx: 0, sx: keys(u, [0, 120, 260, 380, 500], [1.3, 0.9, 1.06, 0.98, 1]), sy: keys(u, [0, 120, 260, 380, 500], [0.7, 1.12, 0.96, 1.01, 1]), face: u > 300 ? 'smug' : null, clip: u < 300 ? 'idle' : u < 1700 ? 'smug_pose' : 'celebrate' };
  }
  function cocoonAt(t) {
    if (t >= 1500 && t < 2700) return { id: 'evo_cocoon_form', f: Math.min(5, Math.floor((t - 1500) / 200)), sx: 1, sy: 1 };
    if (t >= 2700 && t < 3900) { const u = t - 2700, ms = 150 - 60 * u / 1200; return { id: 'evo_cocoon_pulse', f: Math.floor(u / ms) % 4, sx: keys(u, [0, 300, 600, 900, 1200], [1, 1.04, 0.98, 1.06, 1]), sy: keys(u, [0, 300, 600, 900, 1200], [1, 0.97, 1.03, 0.95, 1]), beat: Math.floor(u / ms) }; }
    if (t >= 3900 && t < 4400) return { id: 'evo_cocoon_crack', f: Math.min(3, Math.floor((t - 3900) / 125)), sx: 1, sy: 1 };
    return null;
  }
  function motesAt(t, PX, PY, oldH) {
    const out = []; if (t < 400 || t >= 2200) return out;
    for (let k = 0; k < 14; k++) { const st0 = 400 + k * 600 / 14, u = (t - st0) / 1100; if (u < 0 || u >= 1) continue;
      const r = 90 * (1 - E.oCubic(u)), th = k * 2.4 + 2.5 * Math.PI * u; out.push({ x: PX + r * Math.cos(th), y: PY - oldH / 2 + r * Math.sin(th) * 0.8, f: Math.floor(t / 80 + k) % 3 }); }
    return out;
  }
  function shardsAt(t, PX, PY) {
    const out = []; if (t < 4400 || t >= 4900) return out; const u = (t - 4400) / 500;
    if (u > 0.8 && Math.floor(t / 60) % 2) return out;
    for (let k = 0; k < 8; k++) { const th = k * Math.PI / 4 + 0.3, d = 40 * E.oCubic(u); out.push({ x: PX + d * Math.cos(th), y: PY - 30 + d * Math.sin(th) + 30 * Math.pow(u * 0.5, 2) * 4, f: k % 3 }); }
    return out;
  }
  function rng32(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const CONF = (() => { const r = rng32(3), a = []; for (let k = 0; k < 28; k++) a.push({ vx: -60 + r() * 120, vy: -140 + r() * 50, fm: 120 + r() * 60, kind: k % 4 }); return a; })();
  function confettiAt(t, PX, PY) {
    if (t < 5600 || t >= 7400) return []; const s = (t - 5600) / 1000;
    return CONF.map(c => ({ x: PX + c.vx * s, y: PY - 24 + c.vy * s + 80 * s * s, f: c.kind * 2 + Math.floor(t / c.fm) % 2 }));
  }
  /* 全部軌（一個時間點）：render 用 */
  function evoFrame(t, PX, PY, oldH, newH) {
    const pet = petAt(t), h = t >= 5600 ? newH : oldH;
    const rays = t >= 4400 && t < 7000 && !(t > 6500 && Math.floor(t / 80) % 2) ? { f: Math.floor((t - 4400) / 90) % 6 } : null;
    const ring = t >= 4400 && t < 4750 ? { f: Math.min(4, Math.floor((t - 4400) / 70)), x: PX, y: PY - 28 } : null;
    const flash = t >= 5600 && t < 5900 ? 0.85 * (1 - E.oCubic((t - 5600) / 300)) : 0;
    const skip = t >= 2000 && t < 5600 ? { f: Math.floor(t / 450) % 2, x: 180, y: 400 } : null;
    let card = null;
    if (t >= TL.cardIn && t < TL.cardEnd) {
      const u = clamp((t - 6000) / 500, 0, 1); let sc = keys(u, [0, 0.45, 0.7, 0.85, 1], [0.01, 1.1, 0.96, 1.02, 1], E.oCubic); const rot = keys(u, [0, 0.45, 0.7, 0.85, 1], [-8, 4, -2, 1, 0]);
      let al = 1; if (t >= 7500) { const v = clamp((t - 7500) / 200, 0, 1); sc *= 1 - 0.4 * E.iBack(v); al = 1 - v; }
      card = { sc, rot, al, u, x: 97, y: 352, nameN: Math.max(0, Math.floor((t - TL.nameAt) / TL.typeMs) + 1) * (t >= TL.nameAt ? 1 : 0), lineN: t >= TL.lineAt ? Math.floor((t - TL.lineAt) / TL.typeMs) + 1 : 0 };
    }
    return { t, dim: dimAt(t), cx: PX, cy: PY - h / 2, pet, cocoon: cocoonAt(t), motes: motesAt(t, PX, PY, oldH), shards: shardsAt(t, PX, PY), ring, rays, flash, confetti: confettiAt(t, PX, PY), skip, card };
  }
  /* 撳畫面：2000ms 前冇反應；之後 → 跳去 5600（現身），名卡 +300ms；名卡出咗（≥6000）再撳 → 收（去 7500 收卡） */
  function skipTo(t) { if (t < TL.skipAfter) return null; if (t < TL.reveal) return TL.reveal; if (t >= TL.cardIn && t < TL.cardOut) return TL.cardOut; return null; }
  /* 跳過後嘅時間映射：reveal 之後 300ms 出卡（原本 400ms）→ 用 skip 偏移 */
  function cardInAfterSkip() { return TL.reveal + TL.cardDelay; }
  /* 進化事件 → 前後形態＋小故事節點 */
  function evoPair(e) {
    const br = (f) => (D.EVO_BRANCH && D.EVO_BRANCH[f]) || 'dust';
    if (!e) return null;
    if (e.type === 'hatch') return { from: 'evo_egg', to: 'evo_dot', node: 'n1', route: null };
    if (e.type === 'grow' && e.stage === 'sprout') return { from: 'evo_dot', to: 'evo_sprout', node: 'n2', route: null };
    if (e.type === 'grow' && e.stage === 'juvenile') return { from: 'evo_sprout', to: 'evo_hop', node: 'n3', route: null };
    if (e.type === 'evolve') { const r = br(e.form); return { from: 'evo_hop', to: 'evo_guard_' + r, node: 'n4', route: r }; }
    if (e.type === 'elder') { const r = br(e.form); return { from: 'evo_guard_' + r, to: 'evo_still_' + r, node: 'n5', route: r }; }
    return null;
  }
  function unlockComic(s, node, route, now) {
    const o = st(s); if (!NODES.includes(node)) return false; const had = o.comics[node], c = had || (o.comics[node] = { at: now || 1, routes: [] });
    let nw = !had; if (route && ROUTE_ZH[route] && !c.routes.includes(route)) { c.routes.push(route); nw = true; } return nw;
  }
  /* 四格：節點＋路線 → 4 個 panel 檔名＋字幕（遊策 comics.caption；{route}→ROUTE_ZH） */
  function comicPanels(node, route, comics) {
    const N = comics.nodes[node]; if (!N) return null; const r = route || 'dust';
    const cap = (comics.caption || comics.captionDraft || {})[node] || [];
    return N.panels.map((p, i) => ({ file: 'comics/' + p.replace('{route}', r) + '.png', cap: String(cap[i] || '').replace('{route}', ROUTE_ZH[r] || '') }));
  }

  // ── 進化預兆（達下一階前最後 min(24h, 25%) 窗口；egg／elder 冇）──
  const OMENS = ['flicker', 'appetite', 'dream'];
  function hash(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function omen(s, stageSec) {
    if (!s || s.stage === 'egg' || s.stage === 'elder') return null; const sec = stageSec && stageSec[s.stage]; if (!sec) return null;
    const win = Math.min(24 * 3600, sec * 0.25), left = sec - (+s.growthSec || 0); if (!(left > 0 && left <= win)) return null;
    const kind = OMENS[hash((s.seed || 0) + ':' + (s.gen || 1) + ':' + s.stage) % 3];
    return { kind, left, win };
  }
  const FLICK = { every: [4000, 7000], n: 2, ms: 80, gap: 100, color: '#FFF6DA', alpha: 0.6 };
  /* flicker：t（ms 由上次排程開始）→ 而家閃唔閃 */
  function flickerOn(ms) { for (let i = 0; i < FLICK.n; i++) { const a = i * (FLICK.ms + FLICK.gap); if (ms >= a && ms < a + FLICK.ms) return true; } return false; }
  const DREAM = { every: 20000, f0: 220, f1: 220, hold: 2200, bob: 400, dx: 4, dy: -2, center: [19, 13], icons: 6 };
  /* dream 泡泡：ms（由冒出開始）→ {f, bob, done, puff} */
  function dreamAt(ms) {
    if (ms < 0) return null; if (ms < DREAM.f0) return { f: 0, icon: false }; if (ms < DREAM.f0 + DREAM.f1) return { f: 1, icon: false };
    const u = ms - DREAM.f0 - DREAM.f1; if (u < DREAM.hold) return { f: 2, icon: true, bob: Math.floor(u / DREAM.bob) % 2 ? -1 : 0 };
    if (u < DREAM.hold + 360) return { f: 2, icon: false, puff: Math.floor((u - DREAM.hold) / 120) }; return null;
  }

  return { VISITORS, CFG, NAME, DECOR_NAME, BADGE, LINES, CARD_LINE, ROUTE_ZH, NODES, OMENS, TL, E, FLICK, DREAM, st, dayKey, dayNum, saveDay, vendorOpen, canVisit, pickVisitor, startVisit, gift, giftItems, takeItem, letter, seedGift, useSeed, buy,
    pathPt, leadAt, LOOP_LEN, keys, dimAt, petAt, cocoonAt, motesAt, shardsAt, confettiAt, evoFrame, skipTo, cardInAfterSkip, evoPair, unlockComic, comicPanels, omen, flickerOn, dreamAt, hash };
});
