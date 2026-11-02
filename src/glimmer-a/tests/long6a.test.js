/* 突破 6a「團絨記得你」純邏輯（src/long6a.js）。遊測驗收：60 句冇重複超過 1 次／7 日（＝同一句 7 日內最多講 1 次）；30 日記錄 ≤200KB。
   記錄（時間／照顧／食物／小遊戲最好／訪客／細佬大事／冇嚟日數）、招呼、冇嚟句、日記句、心聲句、特別開心、sanitize。node tests/long6a.test.js */
const M = require('../src/long6a.js'), SIM = require('../src/sim.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
const NAMES = { food: (k) => ({ cookie: '星屑餅', meal: '暖菇飯', soup: '暖湯' })[k] || k, game: (k) => ({ bounce: '彈彈葉', catch: '接光點' })[k] || k, visitor: (k) => ({ snail_postman: '蝸牛郵差' })[k] || k };
const fresh = () => { const s = SIM.newState(at(-40, 12), 9); s.stage = 'sprout'; return s; };
let seed = 7; const rng = () => { seed = (seed * 1103515245 + 12345) >>> 0; return seed / 4294967296; };

console.log('⓪ 句庫');
ok(M.ALL.length === 60, '首批 60 句', M.ALL.length);
ok(new Set(M.ALL.map(l => l.t)).size === 60 && new Set(M.ALL.map(l => l.id)).size === 60, '60 句冇重複（文字＋id）');
ok(M.ALL.every(l => l.mood === 's' || l.mood === 'p'), '每句帶表情（得意／委屈）');
ok(M.BYID.a1_1.t === '你琴日去咗邊？' && M.BYID.a3_1.t === '我以為你搬咗屋。', 'spec 原句：1 日「你琴日去咗邊？」／3 日以上「我以為你搬咗屋。」');
ok(M.BYID.t_l1.t === '你{d} {h} 點先嚟，我扮瞓咗等你。', 'spec 例句（留空位）');
ok(M.fill(M.BYID.t_l1.t, { d: '琴日', h: '11' }) === '你琴日 11 點先嚟，我扮瞓咗等你。', '填空＝spec 例句原文');

console.log('① 記錄');
{ const s = fresh(); let r = M.visit(s, at(0, 9, 5)); ok(r.first && r.gap === 0, '第一次嚟：first、gap 0', r);
  r = M.visit(s, at(0, 9, 10)); ok(!r.first && M.rec(s, '2026-11-01').n === 1, '20 分鐘內再開唔計多次', M.rec(s, '2026-11-01'));
  M.visit(s, at(0, 23, 10)); const d = M.rec(s, '2026-11-01'); ok(d.n === 2 && d.o[0] === 545 && d.o[1] === 1390, '第一次／最後一次時間（分鐘）＋次數', d);
  M.note(s, 'care', 'feed', 0, 0, 0, at(0, 12)); M.note(s, 'care', 'rinse', 0, 0, 0, at(0, 12)); M.note(s, 'care', 'bogus', 0, 0, 0, at(0, 12)); ok(d.c.feed === 1 && d.c.rinse === 1 && !d.c.bogus, '照顧類型', d.c);
  M.note(s, 'food', 'meal', 0, 0, 0, at(0, 12)); M.note(s, 'food', 'meal', 0, 0, 0, at(0, 13)); ok(d.f.meal === 2, '食咗乜', d.f);
  M.note(s, 'game', 'bounce', 18, 1, 0, at(0, 14)); M.note(s, 'game', 'bounce', 25, 2, 1, at(0, 15)); ok(d.g.bounce[0] === 25 && d.g.bounce[1] === 2 && d.g.bounce[2] === 1, '小遊戲當日最好（分、星、破紀錄）', d.g);
  M.note(s, 'visitor', 'snail_postman', 0, 0, 0, at(0, 16)); M.note(s, 'visitor', 'snail_postman', 0, 0, 0, at(0, 17)); ok(d.vi.length === 1, '訪客（同日唔重複）', d.vi);
  M.scanKid(s, { ph: 'none', les: 0, res: 0, lv: 1, trips: 0, gen: 1 }, at(0, 18)); ok(!d.k.length, '細佬：第一次快照唔出事件');
  M.scanKid(s, { ph: 'egg', les: 0, res: 0, lv: 1, trips: 0, gen: 1, name: '細佬' }, at(0, 18)); M.scanKid(s, { ph: 'kid', kst: 'S1', les: 0, res: 0, lv: 1, trips: 0, gen: 1, name: '水系細佬' }, at(0, 19));
  M.scanKid(s, { ph: 'kid', kst: 'S2', kstZh: 'BB', les: 1, res: 1, lv: 2, trips: 1, gen: 1, name: '水系細佬' }, at(0, 20));
  ok(d.k.map(e => e[0]).join() === 'egg,hatch,grow,lesson,move,trip,lv', '細佬大事：蛋到／孵化／大咗／學課／搬入／遠足返／家族升級', d.k);
  M.visit(s, at(3, 10)); const d4 = M.rec(s, '2026-11-04'); ok(d4.gap === 2, '冇嚟嘅日數（返嚟嗰日記 gap）', d4);
}

console.log('② 招呼（每日第一次開 game）');
{ const s = fresh(); M.visit(s, at(0, 23, 2)); ok(!M.greetDue(s, at(0, 23, 3)), '第一日（未有上次）唔講');
  M.visit(s, at(1, 8)); ok(M.greetDue(s, at(1, 8)), '第二日第一次開 → 要講');
  seed = 3; const g = M.greet(s, at(1, 8), { names: NAMES, rng: () => 0 }); ok(g && g.cat === 'late' && /琴日/.test(g.line) && /11 點/.test(g.line), '琴日 23:02 嚟 →「你琴日 11 點…」類', g);
  ok(!M.greetDue(s, at(1, 9)) && M.greet(s, at(1, 9), { names: NAMES }) === null, '每日只講 1 句');
  const s2 = fresh(); M.visit(s2, at(0, 12)); M.visit(s2, at(2, 12)); const a = M.greet(s2, at(2, 12), { rng: () => 0 }); ok(a && a.id === 'a1_1' && a.line === '你琴日去咗邊？' && a.mood === 'p', '冇嚟 1 日 →「你琴日去咗邊？」（委屈）', a);
  const s3 = fresh(); M.visit(s3, at(0, 12)); M.visit(s3, at(5, 12)); const b = M.greet(s3, at(5, 12), { rng: () => 0 }); ok(b && b.id === 'a3_1' && b.line === '我以為你搬咗屋。', '冇嚟 4 日（≥3）→「我以為你搬咗屋。」', b);
  const s4 = fresh(); M.visit(s4, at(0, 12)); M.visit(s4, at(3, 12)); const c = M.greet(s4, at(3, 12), { rng: () => 0 }); ok(c && c.cat === 'absent2', '冇嚟 2 日 → 兩日句', c);
  ok(M.takeHappy(s3, at(5, 12)) && !M.takeHappy(s3, at(5, 13)), '冇嚟返嚟：第一下撳特別開心（一次）');
  ok(!M.takeHappy(s, at(1, 8)), '有嚟就唔使特別開心');
  const s5 = fresh(); M.visit(s5, at(0, 12)); M.note(s5, 'game', 'bounce', 31, 3, 1, at(0, 13)); M.visit(s5, at(1, 9)); const e = M.greet(s5, at(1, 9), { names: NAMES, rng: () => 0 }); ok(e && e.id === 'g_5' && /彈彈葉破咗紀錄，31 分/.test(e.line), '破紀錄最優先（權重）', e);
  const s6 = fresh(); s6.stage = 'egg'; M.visit(s6, at(0, 12)); M.visit(s6, at(1, 12)); ok(!M.greetDue(s6, at(1, 12)), '光卵唔講');
  const s7 = fresh(); M.visit(s7, at(0, 12), {}); const s8 = fresh(); M.visit(s8, at(4, 12), { lastSeen: at(0, 20) }); ok(M.rec(s8, '2026-11-05').gap === 3 && M.greetDue(s8, at(4, 12)), '5c 舊存檔升級：用 lastSeen 計冇嚟日數', M.summary(s8, at(4, 12)));
}

console.log('③ 日記句＋心聲句');
{ const s = fresh(); M.visit(s, at(0, 9)); M.note(s, 'food', 'soup', 0, 0, 0, at(0, 10)); const p = M.diaryPick(s, '2026-11-01', at(1, 9), { names: NAMES, rng: () => 0.99 });
  ok(p && /今日/.test(p.line) || (p && p.cat === 'general'), '日記句用「今日」', p); ok(M.diaryPick(s, '2026-10-01', at(1, 9)) === null, '冇記錄嗰日唔寫');
  const s2 = fresh(); M.visit(s2, at(0, 9)); M.note(s2, 'visitor', 'snail_postman', 0, 0, 0, at(0, 9)); let n = 0; for (let i = 0; i < 6; i++) if (M.voicePick(s2, at(0, 10 + i), { names: NAMES, force: true, rng })) n++;
  ok(n === M.CFG.voicePerDay, '心聲記憶句每日最多 ' + M.CFG.voicePerDay, n);
  const s3 = fresh(); s3.stage = 'egg'; M.visit(s3, at(0, 9)); ok(M.voicePick(s3, at(0, 10), { force: true }) === null, '光卵冇心聲記憶句');
}

console.log('④ 遊測：60 句 7 日內唔重複（模擬 120 日，每日 招呼＋日記＋心聲×2）');
{ const s = fresh(); const said = {}; let worst = 99, total = 0, miss = 0; seed = 11;
  for (let d = 0; d < 120; d++) {
    if (rng() < 0.18) continue;                                  // 有啲日冇嚟
    const h = 6 + Math.floor(rng() * 17); M.visit(s, at(d, h)); if (rng() < 0.5) M.visit(s, at(d, Math.min(23, h + 2)));
    for (let i = 0; i < 3; i++) M.note(s, 'care', M.CARE_K[Math.floor(rng() * 8)], 0, 0, 0, at(d, h));
    if (rng() < 0.7) M.note(s, 'food', ['cookie', 'meal', 'soup'][Math.floor(rng() * 3)], 0, 0, 0, at(d, h));
    if (rng() < 0.5) M.note(s, 'game', 'bounce', Math.floor(rng() * 40), Math.floor(rng() * 4), rng() < 0.2, at(d, h));
    if (rng() < 0.3) M.note(s, 'visitor', 'snail_postman', 0, 0, 0, at(d, h));
    const out = [M.greet(s, at(d, h), { names: NAMES, rng }), M.voicePick(s, at(d, h), { names: NAMES, force: true, rng }), M.voicePick(s, at(d, h), { names: NAMES, force: true, rng })];
    const pk = M.diaryPick(s, M.dayKey(at(d, h)), at(d, 23, 59), { names: NAMES, rng }); if (pk) out.push(M.commit(s, pk, 'diary', at(d, 23, 59)));
    for (const o of out) { if (!o) { miss++; continue; } total++; if (said[o.id] != null) worst = Math.min(worst, d - said[o.id]); said[o.id] = d; }
  }
  ok(worst >= 7, '同一句兩次之間 ≥7 日（最近 ' + worst + ' 日）', worst); ok(total > 200, '講咗 ' + total + ' 句（冇得講 ' + miss + ' 次）', total);
  ok(Object.keys(said).length >= 40, '用到 ' + Object.keys(said).length + '／60 句（細佬／訪客多款要真事件）');
  ok(Object.keys(M.st(s).d).length <= 30, '只留 30 日', Object.keys(M.st(s).d).length);
}

console.log('⑤ 遊測：30 日記錄 ≤200KB（塞滿上限）');
{ const s = fresh(); for (let d = 0; d < 45; d++) { for (let v = 0; v < 30; v++) M.visit(s, at(d, 0, v * 47)); for (const k of M.CARE_K) for (let i = 0; i < 50; i++) M.note(s, 'care', k, 0, 0, 0, at(d, 12));
    for (let i = 0; i < 20; i++) M.note(s, 'food', 'food_' + i, 0, 0, 0, at(d, 12)); for (let i = 0; i < 10; i++) M.note(s, 'game', 'g' + i, 999999, 3, 1, at(d, 12));
    for (let i = 0; i < 10; i++) M.note(s, 'visitor', '訪客訪客訪客訪客' + i, 0, 0, 0, at(d, 12)); for (let i = 0; i < 20; i++) M.note(s, 'kid', 'grow', '細佬細佬細佬細佬細佬細佬細佬細佬', '成年成年成年', 0, at(d, 12));
    M.greet(s, at(d, 12), { force: true }); M.voicePick(s, at(d, 12), { force: true }); M.voicePick(s, at(d, 12), { force: true }); }
  const b = M.sizeBytes(s); ok(Object.keys(M.st(s).d).length === 30, '45 日 → 留 30 日'); ok(b <= M.CFG.sizeMaxBytes, '30 日記錄 ' + (b / 1024).toFixed(1) + 'KB ≤ 200KB', b);
  const j = SIM.serialize(s), s2 = SIM.deserialize(j, at(44, 13)); ok(s2 && s2.mem6 && Object.keys(s2.mem6.d).length === 30, '存檔來回（mem6 保留）');
}

console.log('⑥ sanitize');
{ const s = fresh(); s.mem6 = { d: { 'bad': 1, '2026-11-01': { o: 'x', n: -3, c: { feed: 'a', hack: 3 }, f: { '<b>': 1 }, g: { x: 'y' }, vi: [1, 'a'], k: [['egg', 'n'], ['bad']] } }, said: { zz: 1, a1_1: 'q' }, last: 'nope', log: 'x' };
  const m = M.st(s); const r = m.d['2026-11-01']; ok(!m.d.bad && r && r.n === 0 && !r.c.hack && !r.f['<b>'] && !r.g.x && r.vi.length === 1 && r.k.length === 1, '壞資料清走', r); ok(m.last === null && !Object.keys(m.said).length && Array.isArray(m.log), '壞欄位重設', m);
  ok(M.reset(s) && !Object.keys(M.st(s).d).length, 'reset');
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
