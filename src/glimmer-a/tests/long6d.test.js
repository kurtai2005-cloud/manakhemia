/* long6d.test — 6d 朋友探訪＋交換蛋（遊策 breakthrough-6a6d-spec §6d；冇伺服器）：朋友碼編／解＋checksum（逐字改都無效）、入自己碼唔計、
   同一個碼 24 小時只計 1 次、每個朋友每日 1 次、每日最多 3 個朋友、影子住 24 小時、走嗰陣留手信（每日 ≤3；5a 擺設池）、
   蛋碼（家族 Lv4、每 7 日 1 個）→ 下一隻細佬蛋帶朋友花紋（5c 揀上一代 hook／未孵套落／孵咗＝用咗）、唔郁錢包／路線分、存檔淨化、
   QR（qrlib MIT）本機編→解一樣、碼長度喺 QR v≤5（37 模組）。node tests/long6d.test.js */
const SIM = require('../src/sim.js'), M6 = require('../src/long6a.js'), FAM = require('../src/long5a.js'), C5 = require('../src/long5c.js'), D6 = require('../src/long6d.js'), QR = require('../src/qrlib.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 9 + d, h, m || 0, 0).getTime();
const HOUR = 3600e3, DAY = 86400e3;
let rs = 1; const rnd = () => { rs = (rs * 16807) % 2147483647; return rs / 2147483647; };
const mk = (form) => { const s = SIM.newState(at(-10, 12), 9); s.stage = 'adult'; s.form = form || 'tide'; return s; };
const friend = (uid, o) => D6.encode(Object.assign({ kind: 'visit', uid, day: 2504, fk: 'evo_still_moon', form: 'moon', pat: 'crescent', lv: 4, gen: 2, mem: [11, 9, 2] }, o || {}));

console.log('① 朋友碼：編／解／checksum');
{ const s = mk('moon'); D6.uidOf(s, rnd); const me = D6.myCode(s, at(0, 12), { fk: 'evo_still_moon' });
  ok(/^GL6D[A-Za-z0-9_-]+$/.test(me.code), '碼＝GL6D＋base64url', me.code);
  const d = D6.decode(me.code); ok(d.ok && d.snap.uid === D6.st(s).uid && d.snap.fk === 'evo_still_moon' && d.snap.form === 'moon' && d.snap.kind === 'visit', '解返＝快照（uid／形態／種類）', d.snap);
  ok(d.snap.name === '月眠團絨' && d.snap.pat === C5.patternOf({ kind: 'tr', fk: 'evo_still_moon', form: 'moon' }) && d.snap.lv === 1 && d.snap.gen === 1, '名＝形態名、花紋＝5c、家族 Lv、代', d.snap);
  ok(d.snap.mem.length >= 1 && d.snap.mem.length <= 3 && d.snap.mem.every(id => D6.MEM[id]), '3 句記憶＝固定 id（冇自由文字）', d.snap.mem);
  ok(D6.decode('  請入呢個碼：\n' + me.code + ' 多謝 ').ok, '前後有字／空白都搵到個碼');
  let bad = 0, total = 0; const body = me.code.slice(4), CH = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  for (let i = 4; i < me.code.length; i++) for (const c of [CH[(CH.indexOf(me.code[i]) + 1) % 64], CH[(CH.indexOf(me.code[i]) + 33) % 64]]) { total++; const t = me.code.slice(0, i) + c + me.code.slice(i + 1); if (D6.decode(t).ok) bad++; }
  ok(bad === 0 && total > 80, '逐個字改（' + total + ' 個變化）全部無效', bad);
  ok(!D6.decode(me.code.slice(0, -2)).ok && !D6.decode(me.code + 'AA').ok && !D6.decode('GL6D').ok && !D6.decode('hello').ok, '截短／加長／亂碼無效');
  ok(D6.decode(me.code.slice(0, -1) + (me.code.slice(-1) === 'A' ? 'B' : 'A')).why === 'sum', '改尾字 → why＝sum');
  const v2 = D6.unb64(body); v2[0] = 2; const by = v2.slice(0, -4); const c2 = 'GL6D' + D6.b64(by.concat(D6.sumOf(by))); ok(D6.decode(c2).why === 'ver', '新版本碼 → why＝ver（要更新遊戲）');
  ok(me.code.length <= 84, '碼長 ≤84 字（QR v5-M byte 容量）', me.code.length);
  const M = QR.encodeQR(me.code, 'raw', { ecc: 'medium', border: 1 }); const n = M.length - 2; ok(n <= 37, 'QR ≤37 模組（白位 58 art px 入面 1px／模組＋≥4 quiet）', n);
  const k = 3, b = 4, N = (n + 2 * b) * k, px = new Uint8ClampedArray(N * N * 4).fill(255);
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) if (M[y + 1][x + 1]) for (let dy = 0; dy < k; dy++) for (let dx = 0; dx < k; dx++) { const i = (((y + b) * k + dy) * N + (x + b) * k + dx) * 4; px[i] = px[i + 1] = px[i + 2] = 0; }
  ok(QR.decodeQR({ width: N, height: N, data: px }) === me.code, 'QR 本機編 → 解（@3x 整數 px）＝原碼'); }

console.log('② 探訪規則');
{ const s = mk(); D6.uidOf(s, rnd); let t = at(0, 10);
  const self = D6.myCode(s, t, { fk: 'evo_still_tide' }).code; ok(D6.enter(s, self, t).why === 'self', '入自己個碼 → 唔計'); ok(D6.st(s).visits.length === 0 && D6.st(s).day.uids.length === 0, '自己碼冇影子、唔佔名額');
  const r1 = D6.enter(s, friend(111), t); ok(r1.ok && r1.kind === 'visit' && D6.st(s).visits.length === 1, '朋友碼 → 影子嚟咗', r1.why);
  const v = D6.st(s).visits[0]; ok(v.until - v.at === 24 * HOUR, '影子住 24 小時');
  ok(D6.enter(s, friend(111), t + HOUR).why === 'dup', '同一個碼 24 小時內再入 → dup');
  ok(D6.enter(s, friend(111, { day: 2505 }), t + HOUR).why === 'here', '同一個朋友（另一個碼）影子仲喺度 → here');
  ok(D6.enter(s, friend(222), t).ok && D6.enter(s, friend(333), t).ok, '第 2、3 個朋友 OK');
  ok(D6.enter(s, friend(444), t).why === 'max', '第 4 個朋友 → 今日滿（3 個）'); ok(D6.st(s).visits.length === 3, '影子 3 個');
  const tamp = friend(555).replace(/.$/, (c) => (c === 'A' ? 'B' : 'A')); ok(D6.enter(s, tamp, t).why === 'sum' && D6.st(s).visits.length === 3, '改過嘅碼無效、冇影子');
  // 第二日：同一朋友（影子走咗之後）可以再嚟一次
  t = at(1, 10, 30); const ev = D6.process(s, t); ok(ev.length === 3 && D6.st(s).visits.length === 0, '24 小時後 3 個影子自己走', ev.length);
  ok(ev.every(e => e.gift && FAM.SV[e.gift]) && D6.st(s).day.gifts === 3, '每個留 1 件手信（5a 擺設池）', ev.map(e => e.gift));
  ok(new Set(ev.map(e => e.gift)).size === 3 && ev.every(e => e.isNew), '未有嘅手信優先（3 件唔同）');
  ok(D6.enter(s, friend(111, { day: 2505 }), t).ok, '第二日同一個朋友再嚟 OK');
  ok(D6.enter(s, friend(111, { day: 2506 }), t + HOUR).why === 'here', '仲喺度 → 唔可以再請');
  const o = D6.st(s); o.visits[0].until = t + 2 * HOUR; D6.process(s, t + 2 * HOUR); ok(D6.enter(s, friend(111, { day: 2507 }), t + 3 * HOUR).why === 'friendToday', '今日嚟過（走咗）→ 每個朋友每日 1 次'); }

console.log('③ 手信每日 ≤3');
{ const s = mk(); D6.uidOf(s, rnd); const t0 = at(0, 9);
  for (const u of [11, 12, 13]) D6.enter(s, friend(u), t0); for (const u of [14, 15, 16]) D6.enter(s, friend(u), at(1, 8));
  ok(D6.st(s).visits.length === 6, '跨日 6 個影子（每日 3 個）');
  const ev = D6.process(s, at(2, 12)); const g = ev.filter(e => e.gift).length; ok(ev.length === 6 && g === 3, '同日走 6 個 → 只有 3 件手信', [ev.length, g]);
  ok(ev.filter(e => !e.gift).every(e => e.line === D6.fill(D6.LINES.leaveNo, { name: e.name })) && ev.filter(e => e.gift).every(e => e.line.includes(e.giftZh)), '有手信講手信名；手信滿咗淨係講返咗屋企');
  const s2 = mk(); D6.uidOf(s2, rnd); D6.enter(s2, friend(21), t0); const id = D6.st(s2).visits[0].id; const r = D6.leave(s2, id, t0 + HOUR, true); ok(r && r.early && r.gift, '早啲送佢返屋企 → 照留手信');
  const s3 = mk(); D6.uidOf(s3, rnd); const sv = FAM.st(s3).sv; for (const x of FAM.SOUV) sv[x.id] = 1; D6.enter(s3, friend(31), t0); const r3 = D6.process(s3, at(1, 12))[0]; ok(r3.gift && !r3.isNew, '全部有晒 → 照送（重複，唔加新）'); }

console.log('④ 交換蛋碼（家族 Lv4、7 日 1 個）＋5c 花紋');
{ const s = mk('moon'); D6.uidOf(s, rnd); let t = at(0, 12);
  ok(D6.eggState(s, t).why === 'lock' && D6.eggCode(s, t).ok === false, 'Lv1 → 出唔到蛋碼');
  const F = FAM.st(s); F.xp = FAM.THRESH[3]; F.lv = 4;
  const e1 = D6.eggCode(s, t, { fk: 'evo_still_moon' }); ok(e1.ok && e1.why === 'made' && D6.decode(e1.code).snap.kind === 'egg', 'Lv4 → 出到蛋碼（kind egg）');
  const e2 = D6.eggCode(s, t + 3 * DAY); ok(e2.why === 'have' && e2.code === e1.code && e2.left === 4, '7 日內再撳＝同一個碼（剩 4 日）', [e2.why, e2.left]);
  const e3 = D6.eggCode(s, t + 7 * DAY + 1, { fk: 'evo_still_moon' }); ok(e3.why === 'made' && e3.code !== e1.code, '7 日後 → 新蛋碼');
  // 朋友（另一部機）入蛋碼
  const b = mk('tide'); D6.uidOf(b, rnd); b.stage = 'elder';
  ok(D6.enter(b, e1.code, t).ok && D6.st(b).egg.pat === 'crescent', '朋友入蛋碼 → 待用花紋＝我嘅（月牙）');
  ok(D6.enter(b, e1.code, t + HOUR).why === 'dup', '同一蛋碼 24 小時內再入 → dup');
  ok(D6.enter(s, e1.code, t).why === 'self', '入自己蛋碼唔計');
  // 細佬蛋：揀上一代（hook）→ 花紋＝朋友
  const C = C5.st(b); C.pend.k1 = { kind: 'kid', at: t }; C.seen.k1 = 'pend';
  const cands = C5.candidates(b, t, {}, 'k1'); ok(cands.length >= 1, '有上一代可以揀', cands.length);
  const ch = C5.choose(b, 'k1', cands[0].id, t, {}); ok(ch.ok && ch.inh.pattern === 'crescent' && ch.inh.f6d === '月眠團絨', '揀上一代嗰刻 → 細佬蛋花紋＝朋友（f6d 記朋友名）', ch.inh);
  ok(cands[0].pattern !== 'crescent', '（上一代本身唔係月牙）', cands[0].pattern);
  C.inh.k1.hatched = t + HOUR; const u = D6.applyEgg(b, t + HOUR); ok(u && u.k === 'used' && D6.st(b).egg.used > 0, '孵咗 → 蛋碼用咗');
  C.pend.k2 = { kind: 'kid', at: t }; const ch2 = C5.choose(b, 'k2', cands[0].id, t + 2 * HOUR, {}); ok(ch2.inh.pattern === cands[0].pattern && !ch2.inh.f6d, '下下隻細佬蛋 → 返用上一代花紋');
  // 已經揀咗、未孵 → 入蛋碼都套落
  const c = mk('tide'); D6.uidOf(c, rnd); c.stage = 'elder'; const Cc = C5.st(c); Cc.pend.k1 = { kind: 'kid', at: t }; const cc = C5.candidates(c, t, {}, 'k1'); C5.choose(c, 'k1', cc[0].id, t, {});
  const r = D6.enter(c, e3.code, t + DAY); ok(r.ok && r.applied === 'k1' && Cc.inh.k1.pattern === 'crescent', '揀咗未孵 → 入蛋碼即刻套落', [r.applied, Cc.inh.k1.pattern]);
  const tr = mk('tide'); D6.uidOf(tr, rnd); tr.stage = 'elder'; D6.enter(tr, e3.code, t + DAY); const Ct = C5.st(tr); Ct.pend.tr2 = { kind: 'tr', at: t }; const ct = C5.candidates(tr, t, {}, 'tr2');
  if (ct.length) { const x = C5.choose(tr, 'tr2', ct[0].id, t, {}); ok(!x.inh.f6d, '團絨蛋唔套（淨係細佬蛋）'); } else ok(true, '團絨蛋唔套（冇候選，略）'); }

console.log('⑤ 唔郁經濟／路線分');
{ const s = mk(); D6.uidOf(s, rnd); const w0 = JSON.stringify(s.sys12 || null), r0 = JSON.stringify(s.routePts || s.route || null), n0 = JSON.stringify(s.needs);
  for (const u of [1, 2, 3]) D6.enter(s, friend(u), at(0, 9)); D6.process(s, at(1, 12)); for (let i = 0; i < 9; i++) D6.act(s, D6.st(s).visits[0] ? D6.st(s).visits[0].id : 'x', at(1, 13));
  ok(JSON.stringify(s.sys12 || null) === w0 && JSON.stringify(s.routePts || s.route || null) === r0 && JSON.stringify(s.needs) === n0, '錢包／路線分／需求冇郁');
  ok(!('shards' in D6.summary(s, at(1, 13))) && D6.st(s).n.gifts === 3, '冇碎、冇新貨幣（手信＝家具）'); }

console.log('⑥ 存檔淨化');
{ const s = mk(); s.share6 = { uid: 'x', visits: [{ uid: 5, name: 'A'.repeat(40), fk: 'BAD!', form: 'moon', pat: 'zzz', lv: 99, mem: [1, 999, 2], at: 1, until: 2 }, 'junk'], friends: { abc: {}, 7: { name: 'B', lv: 0 } }, seen: { 'bad key!': 1, abc: 'x', ok1: 5 },
    day: 'x', eggOut: { at: 0 }, egg: { pat: 'nope' }, log: [1, { k: 'a' }], n: { codes: -5 }, junk: 1 };
  const o = D6.st(s); ok(o.uid === 0 && o.visits.length === 1 && o.visits[0].name.length === 16 && o.visits[0].fk === '' && o.visits[0].pat === 'spot' && o.visits[0].lv === 10 && o.visits[0].mem.join() === '1,2', '影子欄位淨化', o.visits[0]);
  ok(Object.keys(o.friends).join() === '7' && o.friends[7].lv === 1, '朋友簿淨化'); ok(Object.keys(o.seen).join() === 'ok1', 'seen 淨化');
  ok(o.day.uids.length === 0 && o.eggOut === null && o.egg === null && o.log.length === 1 && o.n.codes === 0 && !('junk' in o), '其他欄位淨化');
  const s2 = mk(); for (let i = 0; i < 3; i++) D6.enter(s2, friend(100 + i), at(0, 9)); ok(JSON.stringify(s2.share6).length < 4000, '3 個影子存檔細（<4KB）', JSON.stringify(s2.share6).length);
  D6.reset(s2); ok(D6.st(s2).visits.length === 0, 'reset 清晒'); }

console.log(`\n${pass} pass, ${fail} fail`); if (fail) process.exit(1);
