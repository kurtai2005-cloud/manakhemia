/* 《微光小圃》 long6d.js — 第 6 批 6d「朋友探訪＋交換蛋」（遊策 breakthrough-6a6d-spec §6d；冇伺服器）。原創代碼。
   DOM-free、Node 可 require（純邏輯）：存檔 s.share6（sanitize）。唔加路線分、唔郁 §7、唔出碎、冇新貨幣。
   ・朋友碼（GL6D＋base64url）：打包團絨快照＝形態（fk／form）、花紋（5c）、名（形態名，冇玩家私人資料）、家族等級、代、3 句記憶（id，唔帶自由文字）＋玩家隨機 id（uid）＋發碼日，
     尾 4 byte checksum（加鹽 FNV）→ 改任何一個字都無效。
   ・探訪：入朋友碼 → 佢隻團絨嘅「影子」嚟你屋仔住 24 小時（同你啲寵物互動，UI 做）；每個朋友每日 1 次、每日最多 3 個朋友；
     影子走嗰陣留 1 件手信（5a 擺設池隨機；未有嘅優先），手信每日最多 3 件（走嗰日計）。可以早啲送佢返屋企（照留手信）。
   ・交換蛋：家族 Lv4 起，每 7 日可以出 1 個蛋碼（7 日內再撳＝同一個碼）。朋友入咗 → 下一隻細佬蛋帶你嗰邊嘅花紋（承接 5c：揀上一代嗰刻套落 inh.pattern，記 f6d＝朋友名）。
   ・防濫用：同一個碼 24 小時內只計 1 次；入自己個碼唔計；碼篡改（checksum 唔啱）無效。
   ・8 新點子 idea 8（鄰居：性格／最愛／信）未做：要等性格系統（#79）；碼有版本號（v1），到時升 v2。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./long6a.js'), require('./long5a.js'), require('./long5c.js'));
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long6d = factory(root.Glimmer.long6a, root.Glimmer.long5a, root.Glimmer.long5c); }
})(typeof self !== 'undefined' ? self : this, function (M6, FAM, C5) {
  'use strict';
  const obj = (o) => o && typeof o === 'object' && !Array.isArray(o);
  const int = (v, d) => Number.isFinite(+v) ? Math.floor(+v) : d;
  const HOUR = 3600e3, DAY = 86400e3;
  const fnv = (bytes, seed) => { let h = (seed >>> 0) || 2166136261; for (let i = 0; i < bytes.length; i++) { h ^= bytes[i] & 255; h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const hashStr = (str) => { let h = 2166136261 >>> 0; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h >>> 0; };
  const CFG = { prefix: 'GL6D', ver: 1, stayH: 24, perDay: 3, giftsPerDay: 3, dupH: 24, eggLv: 4, eggDays: 7, keepFriends: 40, keepSeenH: 72, keepLog: 30, minLen: 24, maxLen: 220 };
  const KIND = ['visit', 'egg'];
  const PATS = C5 ? C5.PATTERNS.map(p => p.id) : ['wave', 'bubble', 'spark', 'spot', 'flame', 'star', 'diamond', 'crescent'];
  const PATZ = C5 ? Object.fromEntries(C5.PATTERNS.map(p => [p.id, p.zh])) : {};
  /* 3 句記憶（id 唔好改；碼入面只帶 id → 冇自由文字、冇私人資料）。次序＝揀嘅優先次序（越少見越前） */
  const MEMS = [
    [11, '砌到夢圖鑑'], [10, '喺夢入面散步'], [9, '細佬出世喇'], [14, '朋友嚟過我屋企'], [8, '屋企嚟咗隻蛋'], [7, '有客人嚟探我'], [12, '家族升到 Lv3'], [13, '開咗新房'],
    [6, '你哄我瞓覺'], [5, '摸頭摸到暈'], [4, '沖涼沖到發光'], [3, '同你玩小遊戲'], [2, '食過暖菇飯'], [15, '夜晚一齊數星'], [16, '一齊等日出'], [1, '第一次孵出嚟'],
  ].map(([id, zh]) => ({ id, zh }));
  const MEM = Object.fromEntries(MEMS.map(m => [m.id, m]));
  const SHADOW_LINES = ['同{pet}轉圈圈', '同{pet}比賽跳高', '教{pet}一個新姿勢', '同{pet}捉迷藏', '同{pet}一齊望天', '同{pet}碰碰鼻', '扮{pet}行路', '同{pet}分享秘密'];
  const LINES = {
    bad: '呢個唔係朋友碼', sum: '個碼唔啱（可能抄錯咗）', ver: '個碼版本太新，要更新遊戲', self: '呢個係你自己嘅碼', dup: '呢個碼 24 小時內入過喇',
    friendToday: '{name}今日嚟過喇，聽日再請佢', max: '今日已經請咗 3 個朋友，聽日再嚟', here: '{name}嘅影子仲喺度',
    arrive: '{name}嘅影子嚟咗！住 24 粒鐘', leave: '{name}嘅影子返屋企喇，留低咗手信「{gift}」', leaveNo: '{name}嘅影子返屋企喇（今日手信滿咗）',
    eggIn: '收到{name}嘅蛋碼！下一隻細佬蛋會帶「{pat}」花紋', eggLock: '家族 Lv4 先可以出蛋碼', eggWait: '再過 {d} 日可以出新蛋碼',
  };
  const fill = (t, v) => String(t).replace(/\{(\w+)\}/g, (m, k) => (v && v[k] != null ? v[k] : ''));
  const dayKey = (t) => M6.dayKey(t), dnOf = (t) => M6.dn(M6.dayKey(t));
  const DN0 = M6.dn('2020-01-01');

  // ── base64url ──
  const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  const B64I = (() => { const o = {}; for (let i = 0; i < 64; i++) o[B64[i]] = i; return o; })();
  function b64(bytes) { let s = ''; for (let i = 0; i < bytes.length; i += 3) { const a = bytes[i], b = bytes[i + 1], c = bytes[i + 2], n = (a << 16) | ((b | 0) << 8) | (c | 0);
    s += B64[(n >> 18) & 63] + B64[(n >> 12) & 63]; if (i + 1 < bytes.length) s += B64[(n >> 6) & 63]; if (i + 2 < bytes.length) s += B64[n & 63]; } return s; }
  function unb64(str) { const out = []; let buf = 0, bits = 0; for (const ch of str) { const v = B64I[ch]; if (v == null) return null; buf = (buf << 6) | v; bits += 6; if (bits >= 8) { bits -= 8; out.push((buf >> bits) & 255); } } if (bits >= 6) return null; return out; }
  const SALT = hashStr('微光小圃6d·朋友碼');
  const sumOf = (bytes) => { const a = fnv(bytes, SALT), b = fnv(bytes.slice().reverse(), a ^ 0x9E3779B9); return [(a ^ b) >>> 24 & 255, (a ^ b) >>> 16 & 255, (b >>> 8) & 255, a & 255]; };
  const asc = (v) => (typeof v === 'string' && /^[a-z0-9_]{1,24}$/.test(v) ? v : '');

  /* 快照 → 碼。snap：{ kind, uid, day, fk, form, pat, lv, gen, mem[3] } */
  function encode(snap) {
    const k = KIND.indexOf(snap.kind); if (k < 0) throw new Error('kind'); const fk = asc(snap.fk), form = asc(snap.form);
    const uid = (snap.uid >>> 0), day = Math.max(0, Math.min(65535, int(snap.day, 0))), mem = (snap.mem || []).slice(0, 3);
    const by = [CFG.ver, k, (uid >>> 24) & 255, (uid >>> 16) & 255, (uid >>> 8) & 255, uid & 255, (day >> 8) & 255, day & 255,
      Math.max(0, PATS.indexOf(snap.pat)), Math.max(1, Math.min(10, int(snap.lv, 1))), Math.max(1, Math.min(255, int(snap.gen, 1))), MEM[mem[0]] ? mem[0] : 0, MEM[mem[1]] ? mem[1] : 0, MEM[mem[2]] ? mem[2] : 0, fk.length];
    for (const ch of fk) by.push(ch.charCodeAt(0)); by.push(form.length); for (const ch of form) by.push(ch.charCodeAt(0));
    return CFG.prefix + b64(by.concat(sumOf(by)));
  }
  /* 貼上嘅文字 → 第一個朋友碼（容許前後有字／換行） */
  function extract(text) { const m = new RegExp(CFG.prefix + '[A-Za-z0-9_-]{' + CFG.minLen + ',' + CFG.maxLen + '}').exec(String(text || '').replace(/\s+/g, '')); return m ? m[0] : null; }
  /* 碼 → { ok, why（bad／sum／ver）, snap } */
  function decode(text) {
    const code = extract(text); if (!code) return { ok: false, why: 'bad' };
    const all = unb64(code.slice(CFG.prefix.length)); if (!all || all.length < 21) return { ok: false, why: 'bad' };
    if (b64(all) !== code.slice(CFG.prefix.length)) return { ok: false, why: 'sum' };   // 尾字未用 bit 都唔准改（嚴格）
    const by = all.slice(0, -4), cs = all.slice(-4), want = sumOf(by); if (cs.some((v, i) => v !== want[i])) return { ok: false, why: 'sum' };
    if (by[0] !== CFG.ver) return { ok: false, why: by[0] > CFG.ver ? 'ver' : 'bad' };
    if (!KIND[by[1]]) return { ok: false, why: 'bad' };
    let p = 15; const fl = by[14]; if (fl > 24 || p + fl >= by.length) return { ok: false, why: 'bad' }; const fk = String.fromCharCode.apply(null, by.slice(p, p + fl)); p += fl;
    const ml = by[p++]; if (ml > 24 || p + ml !== by.length) return { ok: false, why: 'bad' }; const form = String.fromCharCode.apply(null, by.slice(p, p + ml));
    if ((fk && !asc(fk)) || (form && !asc(form)) || by[8] >= PATS.length) return { ok: false, why: 'bad' };
    const snap = { kind: KIND[by[1]], uid: ((by[2] << 24) | (by[3] << 16) | (by[4] << 8) | by[5]) >>> 0, day: (by[6] << 8) | by[7], pat: PATS[by[8]], lv: Math.max(1, Math.min(10, by[9])), gen: Math.max(1, by[10]),
      mem: [by[11], by[12], by[13]].filter(id => MEM[id]), fk, form };
    snap.name = nameOf(snap); return { ok: true, code, snap, h: codeHash(code) };
  }
  const codeHash = (code) => (hashStr(code) >>> 0).toString(36);
  function nameOf(snap) { return FAM && FAM.trName ? FAM.trName(snap.form || '') : '團絨'; }

  // ── 存檔 ──
  const cleanSnap = (v) => obj(v) ? { uid: (+v.uid >>> 0), name: typeof v.name === 'string' ? v.name.slice(0, 16) : '團絨', fk: asc(v.fk), form: asc(v.form), pat: PATS.includes(v.pat) ? v.pat : 'spot',
    lv: Math.max(1, Math.min(10, int(v.lv, 1))), gen: Math.max(1, Math.min(255, int(v.gen, 1))), mem: Array.isArray(v.mem) ? v.mem.filter(id => MEM[id]).slice(0, 3) : [] } : null;
  function st(s) {
    let o = s.share6; if (!obj(o)) o = s.share6 = {};
    o.v = 1; o.uid = (+o.uid >>> 0) || 0;
    if (!Array.isArray(o.visits)) o.visits = [];
    o.visits = o.visits.filter(obj).slice(-12).map(v => Object.assign(cleanSnap(v), { id: typeof v.id === 'string' ? v.id.slice(0, 16) : 'v' + (+v.at || 0), at: +v.at || 0, until: +v.until || 0, n: Math.max(0, int(v.n, 0)), slot: Math.max(0, Math.min(5, int(v.slot, 0))) }));
    if (!obj(o.friends)) o.friends = {}; const fk = Object.keys(o.friends);
    for (const k of fk) { const f = o.friends[k]; if (!/^\d+$/.test(k) || !obj(f)) { delete o.friends[k]; continue; } o.friends[k] = Object.assign(cleanSnap(f), { first: +f.first || 0, last: +f.last || 0, n: Math.max(0, int(f.n, 0)), eggs: Math.max(0, int(f.eggs, 0)) }); }
    if (Object.keys(o.friends).length > CFG.keepFriends) Object.keys(o.friends).sort((a, b) => o.friends[a].last - o.friends[b].last).slice(0, Object.keys(o.friends).length - CFG.keepFriends).forEach(k => delete o.friends[k]);
    if (!obj(o.seen)) o.seen = {}; for (const k of Object.keys(o.seen)) if (!/^[0-9a-z]{1,8}$/.test(k) || !Number.isFinite(+o.seen[k])) delete o.seen[k]; else o.seen[k] = +o.seen[k];
    if (!obj(o.day) || typeof o.day.d !== 'string') o.day = { d: '', uids: [], gifts: 0 }; o.day.uids = Array.isArray(o.day.uids) ? o.day.uids.map(u => +u >>> 0).slice(0, 9) : []; o.day.gifts = Math.max(0, int(o.day.gifts, 0));
    if (o.eggOut != null && !(obj(o.eggOut) && +o.eggOut.at > 0 && typeof o.eggOut.code === 'string')) o.eggOut = null; if (o.eggOut === undefined) o.eggOut = null;
    if (o.egg != null && !(obj(o.egg) && PATS.includes(o.egg.pat))) o.egg = null; if (o.egg === undefined) o.egg = null;
    if (o.egg) { o.egg.at = +o.egg.at || 0; o.egg.uid = +o.egg.uid >>> 0; o.egg.name = typeof o.egg.name === 'string' ? o.egg.name.slice(0, 16) : '朋友'; o.egg.used = +o.egg.used || 0; if (o.egg.child != null && typeof o.egg.child !== 'string') o.egg.child = null; }
    if (!Array.isArray(o.log)) o.log = []; o.log = o.log.filter(obj).slice(-CFG.keepLog);
    if (!obj(o.n)) o.n = {}; for (const k of ['codes', 'visits', 'gifts', 'eggOut', 'eggIn', 'eggUsed', 'bad', 'acts']) o.n[k] = Math.max(0, int(o.n[k], 0));
    for (const k of Object.keys(o)) if (!['v', 'uid', 'visits', 'friends', 'seen', 'day', 'eggOut', 'egg', 'log', 'n'].includes(k)) delete o[k];
    return o;
  }
  /* 玩家 id：第一次用先抽（隨機 32 bit；唔係私人資料） */
  function uidOf(s, rnd) { const o = st(s); if (!o.uid) { const r = rnd || Math.random; let u = 0; while (!u) u = (Math.floor(r() * 4294967296) >>> 0); o.uid = u; } return o.uid; }
  function dayRoll(s, now) { const o = st(s), k = dayKey(now); if (o.day.d !== k) o.day = { d: k, uids: [], gifts: 0 }; return o.day; }
  const logEv = (o, k, x, now) => { o.log.push(Object.assign({ k, at: now || 0 }, x || {})); if (o.log.length > CFG.keepLog) o.log.shift(); };

  /* 3 句記憶（由 6a 30 日記錄＋6c 夢＋5a 家族＋6d 朋友揀；冇自由文字） */
  function memsOf(s) {
    const m = s.mem6 && obj(s.mem6.d) ? s.mem6.d : {}, c = {}, f = {}; let vi = 0, kEgg = 0, kHatch = 0, late = 0, early = 0, games = 0;
    for (const k of Object.keys(m)) { const r = m[k]; if (!obj(r)) continue; if (obj(r.c)) for (const x of Object.keys(r.c)) c[x] = (c[x] | 0) + (r.c[x] | 0); if (obj(r.f)) for (const x of Object.keys(r.f)) f[x] = (f[x] | 0) + (r.f[x] | 0);
      if (Array.isArray(r.vi)) vi += r.vi.length; if (Array.isArray(r.k)) for (const e of r.k) { if (e[0] === 'egg') kEgg++; if (e[0] === 'hatch') kHatch++; }
      if (obj(r.g)) games += Object.keys(r.g).length; if (Array.isArray(r.o)) { if (r.o[1] >= 21 * 60) late++; if (r.o[0] < 7 * 60) early++; } }
    const d6 = s.dream6 && obj(s.dream6.n) ? s.dream6.n : {}, lv = s.fam && s.fam.lv | 0, sh = s.share6 && s.share6.n ? s.share6.n.visits | 0 : 0;
    const has = { 11: d6.cards > 0, 10: d6.dreams > 0, 9: kHatch > 0, 14: sh > 0, 8: kEgg > 0, 7: vi > 0, 12: lv >= 3, 13: lv >= 2, 6: c.lull > 0, 5: (c.pat | 0) >= 3, 4: c.rinse > 0, 3: (c.mg | 0) > 0 || games > 0, 2: f.meal > 0, 15: late > 0, 16: early > 0, 1: true };
    return MEMS.filter(x => has[x.id]).slice(0, 3).map(x => x.id);
  }
  /* 自己個快照（ctx：{ fk（畫用 form key）} ） */
  function patOf(s, fk) {
    if (!C5) return 'spot'; const km = s.fam && s.fam.km;
    if (km) return C5.patternOf({ kind: 'kid', fk: km.fk, line: km.line }, null);
    return C5.patternOf({ kind: 'tr', fk: fk || null, form: s.form }, null);
  }
  function mySnap(s, now, ctx, kind) {
    ctx = ctx || {}; const fk = asc(ctx.fk) || asc(s.form) || '';
    return { kind: kind || 'visit', uid: uidOf(s, ctx.rnd), day: Math.max(0, dnOf(now) - DN0), fk, form: asc(s.form), pat: patOf(s, ctx.fk), lv: FAM ? FAM.st(s).lv : 1, gen: s.gen || 1, mem: memsOf(s) };
  }
  function myCode(s, now, ctx) { const o = st(s), sn = mySnap(s, now, ctx, 'visit'), code = encode(sn); return { code, snap: Object.assign(sn, { name: nameOf(sn) }), short: shortOf(code) }; }
  const shortOf = (code) => code.slice(0, 8) + '…' + code.slice(-4);

  /* 蛋碼：家族 Lv4；每 7 日 1 個（7 日內＝同一個碼） */
  function eggState(s, now) {
    const o = st(s), lv = FAM ? FAM.st(s).lv : 1; if (lv < CFG.eggLv) return { ok: false, why: 'lock', lv };
    if (o.eggOut && now - o.eggOut.at < CFG.eggDays * DAY) return { ok: true, why: 'have', code: o.eggOut.code, at: o.eggOut.at, left: Math.ceil((CFG.eggDays * DAY - (now - o.eggOut.at)) / DAY), short: shortOf(o.eggOut.code) };
    return { ok: true, why: 'new', lv };
  }
  function eggCode(s, now, ctx) {
    const e = eggState(s, now); if (!e.ok) return e; if (e.why === 'have') return e;
    const o = st(s), sn = mySnap(s, now, ctx, 'egg'), code = encode(sn); o.eggOut = { at: now, code }; o.n.eggOut++; logEv(o, 'eggOut', {}, now);
    return { ok: true, why: 'made', code, at: now, left: CFG.eggDays, short: shortOf(code), snap: Object.assign(sn, { name: nameOf(sn) }) };
  }

  /* 入碼：{ ok, why, kind, visit|egg, name } */
  function enter(s, text, now, ctx) {
    const o = st(s), d = decode(text); dayRoll(s, now);
    if (!d.ok) { o.n.bad++; return { ok: false, why: d.why }; }
    const sn = d.snap, me = uidOf(s, ctx && ctx.rnd), nm = { name: sn.name };
    if (sn.uid === me) return { ok: false, why: 'self', kind: sn.kind, name: sn.name };
    for (const k of Object.keys(o.seen)) if (now - o.seen[k] >= CFG.keepSeenH * HOUR || o.seen[k] > now + DAY) delete o.seen[k];
    if (o.seen[d.h] != null && now - o.seen[d.h] < CFG.dupH * HOUR) return { ok: false, why: 'dup', kind: sn.kind, name: sn.name };
    const F = o.friends[sn.uid] || null;
    if (sn.kind === 'visit') {
      process(s, now);
      if (o.visits.some(v => v.uid === sn.uid)) return { ok: false, why: 'here', kind: 'visit', name: sn.name };
      if (o.day.uids.includes(sn.uid)) return { ok: false, why: 'friendToday', kind: 'visit', name: sn.name };
      if (o.day.uids.length >= CFG.perDay) return { ok: false, why: 'max', kind: 'visit', name: sn.name };
      o.seen[d.h] = now; o.day.uids.push(sn.uid);
      const used = new Set(o.visits.map(v => v.slot)); let slot = 0; while (used.has(slot) && slot < 5) slot++;
      const v = Object.assign(cleanSnap(sn), { id: 'v' + now.toString(36) + (sn.uid % 1296).toString(36), at: now, until: now + CFG.stayH * HOUR, n: 0, slot });
      o.visits.push(v); o.n.visits++; o.n.codes++;
      o.friends[sn.uid] = Object.assign(cleanSnap(sn), { first: F ? F.first : now, last: now, n: (F ? F.n : 0) + 1, eggs: F ? F.eggs : 0 });
      logEv(o, 'arrive', { uid: sn.uid, name: sn.name }, now);
      if (M6) try { M6.note(s, 'visitor', sn.name + '嘅影子', 0, 0, 0, now); } catch (e) { }
      return { ok: true, why: 'arrive', kind: 'visit', visit: Object.assign({}, v), name: sn.name, line: fill(LINES.arrive, nm) };
    }
    // 蛋碼
    o.seen[d.h] = now; o.n.codes++; o.n.eggIn++;
    const prev = o.egg && !o.egg.used ? o.egg : null;
    o.egg = { pat: sn.pat, uid: sn.uid, name: sn.name, at: now, used: 0, child: null };
    o.friends[sn.uid] = Object.assign(cleanSnap(sn), { first: F ? F.first : now, last: now, n: F ? F.n : 0, eggs: (F ? F.eggs : 0) + 1 });
    logEv(o, 'eggIn', { uid: sn.uid, name: sn.name, pat: sn.pat }, now);
    const r = { ok: true, why: 'egg', kind: 'egg', name: sn.name, pat: sn.pat, patZh: PATZ[sn.pat] || sn.pat, replaced: !!prev, line: fill(LINES.eggIn, { name: sn.name, pat: PATZ[sn.pat] || sn.pat }) };
    applyEgg(s, now, r); return r;
  }

  /* 5c：揀上一代嗰刻（hook）＋每 tick：未孵嘅細佬蛋套朋友花紋；孵咗 → 用咗 */
  function applyEgg(s, now, out) {
    const o = st(s), E = o.egg; if (!E || E.used || !C5) return null; const inh = C5.st(s).inh; let ev = null;
    if (E.child && inh[E.child] && inh[E.child].hatched && inh[E.child].f6d) { E.used = inh[E.child].hatched || now || 1; o.n.eggUsed++; logEv(o, 'eggUsed', { child: E.child, pat: E.pat }, now); return { k: 'used', child: E.child, pat: E.pat, name: E.name }; }
    for (const id of Object.keys(inh)) { const h = inh[id]; if (h.kind !== 'kid' || h.hatched) continue;
      if (h.pattern !== E.pat || h.f6d !== E.name) { h.pattern = E.pat; h.f6d = E.name; E.child = id; ev = { k: 'apply', child: id, pat: E.pat, name: E.name }; } else E.child = id; break; }
    if (out && ev) out.applied = ev.child; return ev;
  }
  if (C5 && C5.onChoose) C5.onChoose((s, h, child, now) => { if (!h || h.kind !== 'kid' || !s.share6) return; const E = st(s).egg; if (!E || E.used) return; h.pattern = E.pat; h.f6d = E.name; E.child = child; });

  /* 影子走：到時（或者早送）→ 手信（每日 ≤3；5a 擺設池，未有嘅優先） */
  function giftPick(s, v) {
    const sv = FAM.st(s).sv, left = FAM.SOUV.filter(x => !sv[x.id]), pool = left.length ? left : FAM.SOUV;
    return pool[hashStr(v.id + ':' + v.uid + ':' + ((s.seed >>> 0) || 0)) % pool.length].id;
  }
  function leave(s, id, now, early) {
    const o = st(s), i = o.visits.findIndex(v => v.id === id); if (i < 0) return null; const v = o.visits[i], day = dayRoll(s, now); o.visits.splice(i, 1);
    let gift = null, isNew = false;
    if (FAM && day.gifts < CFG.giftsPerDay) { gift = giftPick(s, v); const sv = FAM.st(s).sv; isNew = !sv[gift]; if (isNew) sv[gift] = now || 1; day.gifts++; o.n.gifts++; }
    logEv(o, 'leave', { uid: v.uid, name: v.name, gift, early: !!early }, now);
    const gz = gift && FAM.SV[gift] ? FAM.SV[gift].zh : '';
    return { k: 'leave', id: v.id, uid: v.uid, name: v.name, gift, giftZh: gz, isNew, early: !!early, n: v.n, line: gift ? fill(LINES.leave, { name: v.name, gift: gz }) : fill(LINES.leaveNo, { name: v.name }) };
  }
  function process(s, now) { const o = st(s), out = []; for (const v of o.visits.slice().sort((a, b) => a.until - b.until)) if (now >= v.until) { const r = leave(s, v.id, Math.max(v.until, now), false); if (r) out.push(r); } return out; }
  function act(s, id, now) { const v = st(s).visits.find(x => x.id === id); if (!v) return null; v.n++; st(s).n.acts++; return SHADOW_LINES[hashStr(v.id + ':' + v.n) % SHADOW_LINES.length]; }
  const leftH = (v, now) => Math.max(0, Math.ceil((v.until - now) / HOUR));
  function summary(s, now) {
    const o = st(s), day = dayRoll(s, now), e = eggState(s, now);
    return { uid: o.uid, visits: o.visits.map(v => Object.assign({}, v, { leftH: leftH(v, now) })), today: day.uids.length, gifts: day.gifts, perDay: CFG.perDay, friends: Object.keys(o.friends).length,
      egg: o.egg ? Object.assign({}, o.egg) : null, eggOut: e, n: Object.assign({}, o.n), log: o.log.slice(-6) };
  }
  function reset(s) { delete s.share6; return st(s); }
  return { CFG, KIND, PATS, PATZ, MEMS, MEM, LINES, SHADOW_LINES, fill, b64, unb64, sumOf, encode, extract, decode, codeHash, nameOf, st, uidOf, dayRoll, memsOf, patOf, mySnap, myCode, shortOf, eggState, eggCode, enter, applyEgg, giftPick, leave, process, act, leftH, summary, reset };
});
