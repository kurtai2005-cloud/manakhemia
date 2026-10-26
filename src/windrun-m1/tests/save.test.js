// node tests/save.test.js —— 存檔 v1：預設、清洗、冪等、遷移、存檔碼、儲存轉接器、衝突、惡意輸入
const assert = require('assert'); const S = require('../src/save.js');
let n = 0; const ok = (c, m) => { assert(c, m); n++; }; const eq = (a, b, m) => { assert.deepStrictEqual(a, b, m); n++; };
const ser = S.serialize;
// 1. 預設存檔：經 normalize 後不變（冪等）、鍵序固定
const d = S.create({ now: 1000, deviceId: 'dev-test1', name: '阿風' }); const nd = S.normalize(d);
ok(nd.ok && nd.from === 1 && nd.warnings.length === 0, '預設存檔係 v1'); eq(nd.save.player.name, '阿風'); eq(ser(S.normalize(nd.save).save), ser(nd.save), 'normalize 冪等');
// 2. 隨機存檔 fuzz：normalize 冪等、限制、參照完整
let seed = 99; const rnd = () => (seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296, ri = (a, b) => a + Math.floor(rnd() * (b - a + 1));
const SP = ['mochi', 'namifin', 'narrowcat', 'frostdeer', 'gravelbadger', 'tingyu', 'windweasel', 'mistfern'];
function randSave() {
  const s = S.create({ now: ri(0, 1e12), deviceId: 'dev-' + ri(100, 999), name: '玩家' + ri(0, 99) }); s.rev = ri(0, 500); let id = 1;
  const mk = () => S.newCreature(SP[ri(0, 7)], 'c' + (id++), { lv: ri(1, 30), exp: ri(0, 999), bonus: { speed: ri(0, 20), power: ri(0, 20), calm: ri(0, 20), stamina: ri(0, 20) }, cond: ri(0, 100), skills: ['boost', 'recover'].slice(0, ri(0, 2)) });
  for (let i = 0; i < ri(1, 6); i++) s.party.push(mk()); for (let i = 0; i < ri(0, 60); i++) s.habitat.push(mk());
  s.presets = [0, 1, 2].map(() => s.party.slice(0, ri(0, 3)).map(c => c.iid)); s.seq = id; s.player.leaf = ri(0, 99999); s.player.seals = ['seal_1', 'seal_2', 'seal_3'].slice(0, ri(0, 3));
  s.cleared = ['cup.leaf.m1', 'cup.leaf.m2', 'cup.leaf.m3'].slice(0, ri(0, 3)).sort(); for (let i = 0; i < ri(0, 20); i++) s.flags['story.ch1.f' + i] = [true, false, ri(0, 9), 'x'][ri(0, 3)];
  s.player.pos = { map: 'route_fernshade', x: ri(0, 700) + 0.5, y: ri(0, 200), dir: 'dlru'[ri(0, 3)] }; s.dex = { seen: [], owned: [] }; return S.normalize(s).save;
}
for (let i = 0; i < 300; i++) {
  const a = randSave(), r = S.normalize(JSON.parse(JSON.stringify(a)));
  ok(r.ok, 'ok'); eq(ser(r.save), ser(a), 'fuzz #' + i + ' 往返不變'); ok(a.party.length <= 6 && a.habitat.length <= 60, '上限');
  const have = new Set(a.party.concat(a.habitat).map(c => c.iid)); ok(have.size === a.party.length + a.habitat.length, 'iid 唯一'); a.presets.forEach(p => p.forEach(x => ok(have.has(x), '預設隊參照有效'))); ok(a.seq > Math.max(0, ...[...have].map(x => +x.slice(1))), 'seq 大於全部 iid');
  ok(a.dex.owned.every((x, k, arr) => !k || arr[k - 1] < x), 'dex 排序');
  // 碼往返
  const code = S.toCode(a); const back = S.fromCode(code); ok(back.ok && ser(back.save) === ser(a), '存檔碼往返 #' + i);
}
// 3. 惡意／垃圾輸入：唔拋錯、輸出合法
const junk = [null, undefined, 0, 1, 'x', [], [1, 2], {}, { version: 1 }, { version: 1, party: 'x', habitat: 5, flags: [], player: 3 }, { version: 1, player: { leaf: -5, name: 'x'.repeat(500) } }, { version: 1, player: { leaf: 1e30 } }, { version: 1, player: { leaf: NaN } },
  JSON.parse('{"version":1,"__proto__":{"polluted":1},"player":{"__proto__":{"x":1}},"flags":{"__proto__":1,"story.ok":true,"BAD KEY":1,"constructor":2}}'), { version: 1, party: Array(500).fill({ iid: 'c1', species: 'mochi' }) }, { version: 1, party: [{ iid: 'c1', species: 'MOCHI' }, { iid: 'x', species: 'mochi' }, null, 5] },
  { version: 1, settings: { lang: 'xx', touchMode: 7, fxQuality: {}, textSpeed: 99 } }, { version: 1, player: { pos: { x: Infinity, y: -9, map: '../../etc' } } }];
for (const j of junk) { let r; try { r = S.normalize(j); } catch (e) { assert.fail('拋錯：' + e.message + ' 輸入 ' + JSON.stringify(j)); } ok(r.ok, 'junk ok'); if (r.save) { const a = S.normalize(r.save).save; eq(ser(a), ser(r.save), 'junk 輸出冪等'); ok(r.save.player.leaf >= 0 && r.save.player.leaf <= S.LIM.leaf, 'leaf 範圍'); ok(/^[a-z]/.test(r.save.player.pos.map), 'map 名合法'); ok(Number.isFinite(r.save.player.pos.x), 'x 有限'); } }
ok(({}).polluted === undefined && ({}).x === undefined, '無原型污染');
eq(S.normalize({ version: 1, party: Array(500).fill({ iid: 'c1', species: 'mochi' }) }).save.party.length, 1, 'iid 重複只留 1 個');
eq(S.normalize({ version: 1, player: { name: 'x'.repeat(500) } }).save.player.name.length, S.LIM.name, '名字截斷');
// 4. 遷移 v0（MVP）→ v1
const legacy = { v: 1, creatures: { mochi: { lv: 5, exp: 0, bonus: { speed: 1, power: 0, calm: 0, stamina: 6 }, cond: 95 }, namifin: { lv: 3, exp: 0, bonus: { speed: 0, power: 0, calm: 0, stamina: 0 }, cond: 100 }, narrowcat: { lv: 3 }, frostdeer: { lv: 2 }, gravelbadger: { lv: 3 }, tingyu: { lv: 3 }, windweasel: { lv: 3 }, mistfern: { lv: 3 } }, ribbons: 7, turn: 4, actionsLeft: 1, cleared: { 1: true, 2: true }, races: 9, sound: false };
const m = S.normalize(legacy); ok(m.ok && m.from === 0 && m.warnings[0] === 'migrated v0→v1', '偵測到 v0'); eq(m.save.version, 1); eq(m.save.party.length, 6); eq(m.save.habitat.length, 2); eq(m.save.stats.ribbons, 7); eq(m.save.cleared, ['legacy.stage1', 'legacy.stage2']); eq(m.save.settings.sound, false);
eq(m.save.party.find(c => c.species === 'mochi').bonus.stamina, 6); ok(m.save.dex.owned.length === 8, '圖鑑補齊'); eq(ser(S.normalize(m.save).save), ser(m.save), '遷移結果冪等'); eq(legacy.v, 1, '唔改輸入'); ok(legacy.cleared[1] === true);
ok(S.normalize({ v: 1, creatures: 'bad' }).ok, '壞舊檔唔崩潰'); eq(S.normalize({ v: 2 }).fresh, true, '無法辨識→全新');
// 5. 版本太新：唔讀、唔覆寫
const tn = S.normalize({ version: 99, party: [] }); eq(tn.ok, false); eq(tn.reason, 'too_new');
// 6. 存檔碼：校驗／殘缺／空白容忍
const sv = randSave(), code = S.toCode(sv); ok(/^WRS1\.[A-Za-z0-9_-]+\.[0-9a-f]{8}$/.test(code), '碼格式'); ok(S.fromCode(' ' + code.slice(0, 20) + '\n' + code.slice(20) + ' ').ok, '容忍空白換行');
eq(S.fromCode(code.slice(0, -10) + code.slice(-9)).ok, false, '殘缺'); const mid = 8 + 40; const flip = code.slice(0, mid) + (code[mid] === 'A' ? 'B' : 'A') + code.slice(mid + 1); eq(S.fromCode(flip).ok, false, '竄改被校驗擋');
for (const bad of ['', null, 'WRS1.', 'WRS2.abc.00000000', 'hello', 'WRS1.!!!.00000000']) eq(S.fromCode(bad).ok, false, '壞碼 ' + bad);
const big = S.create({ now: 1, deviceId: 'dev-big' }); for (let i = 1; i <= 66; i++) { const c = S.newCreature('mochi', 'c' + i, { lv: 50, skills: ['boost', 'recover'] }); (i <= 6 ? big.party : big.habitat).push(c); } big.seq = 67; for (let i = 0; i < 100; i++) big.flags['story.ch1.flag_' + i] = true; const bigc = S.toCode(S.normalize(big).save);
console.log('滿載存檔（6+60 隻、100 旗標）碼長 ' + bigc.length + ' 字元；空存檔 ' + S.toCode(d).length + ' 字元；規範化 JSON ' + ser(S.normalize(big).save).length + ' bytes');
// 7. 儲存轉接器
function fake(opt) { opt = opt || {}; const m = {}; return { m, getItem: k => { if (opt.throwGet) throw new Error('x'); return k in m ? m[k] : null; }, setItem: (k, v) => { if (opt.full) throw new Error('QuotaExceededError'); m[k] = String(v); }, removeItem: k => { delete m[k]; } }; }
let ad = fake(), st = S.Store(ad); let L = st.load(5); eq(L.source, 'new'); const r1 = st.save(L.save, 10); ok(r1.ok && r1.rev === 1, '首次存 rev=1'); const r2 = st.save(r1.save, 20); eq(r2.rev, 2); ok(ad.m['windrun_save.bak'], '第 2 次存產生備份'); eq(S.parse(ad.m['windrun_save.bak']).save.rev, 1, '備份係上一版');
ad.m['windrun_save'] = '{"broken'; L = st.load(); eq(L.source, 'backup', '主檔損壞→讀備份'); eq(L.save.rev, 1);
const r3 = st.save(L.save, 30); ok(r3.ok); ok(S.parse(ad.m['windrun_save.bak']).ok, '損壞主檔唔會覆蓋有效備份'); eq(S.parse(ad.m['windrun_save.bak']).save.rev, 1);
ad = fake(); ad.m['windrun_save_v1'] = JSON.stringify(legacy); L = S.Store(ad).load(); eq(L.source, 'legacy', '無新檔→讀 MVP 舊鍵'); eq(L.from, 0); ok(!('windrun_save' in ad.m), '載入唔改舊鍵');
ad = fake({ full: true }); eq(S.Store(ad).save(S.create({ now: 1 })).ok, false, 'quota 滿唔拋錯'); ad = fake({ throwGet: true }); eq(S.Store(ad).load(1).source, 'new', 'getItem 拋錯→新存檔');
ad = fake(); ad.m['windrun_save'] = JSON.stringify({ version: 7 }); L = S.Store(ad).load(); ok(L.tooNew && !L.save, '太新：標記 tooNew，唔回傳存檔'); eq(S.Store(ad).save(S.create({ now: 1 })).ok, true, '（呼叫方應根據 tooNew 阻止存檔；轉接器本身唔判斷）');
// 8. 雲端衝突判斷
const A = S.create({ now: 1, deviceId: 'dev-A' }), B = JSON.parse(JSON.stringify(A)); B.rev = 3; eq(S.conflict(A, B).winner, 'remote'); eq(S.conflict(B, A).winner, 'local');
const C = S.normalize(Object.assign(JSON.parse(JSON.stringify(A)), { deviceId: 'dev-C', cleared: ['cup.leaf.m1'] })).save, D = S.normalize(Object.assign(JSON.parse(JSON.stringify(A)), { deviceId: 'dev-D', cleared: ['cup.leaf.m2'] })).save;
eq(S.conflict(C, A).winner, 'local', '超集勝'); eq(S.conflict(C, D).winner, 'ask', '分叉→問玩家'); ok(S.progressScore(C) > S.progressScore(A));
// 9. 決定論：序列化唔受鍵插入次序影響
eq(S.serialize({ b: 1, a: { d: 1, c: 2 } }), '{"a":{"c":2,"d":1},"b":1}');
console.log('save 測試通過，斷言', n);
