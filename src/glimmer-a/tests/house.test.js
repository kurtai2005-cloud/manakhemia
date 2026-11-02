/* 第 4 批 4b（docs-gdd/series2-4a4b-spec.md v1.1 §4b）：屋仔 s.pet2.house — 美術對數／解鎖／預設床／商店／委託獎／訪客獎／擺位心情（共用上限 5）／整蠱上限／同床瞓時段／行走區／唔郁團絨路線。 */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), HS = require('../src/house.js'), T = require('../src/touch.js'), X = require('../src/systems.js');
const fs = require('fs'), path = require('path'), ART = path.join(__dirname, '../art/series2_house');
const J = (f) => JSON.parse(fs.readFileSync(path.join(ART, f), 'utf8')), H = J('house.json'), ACT = J('actions/actions_house.json');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
function fam(o) { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; S2.noteElder(s, at(-25, 12)); S2.deliver(s, at(-24, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(-20, 12)); Object.assign(p, { intim: 90, rel: 'family' }, o || {}); return s; }
const routeSnap = (s) => JSON.stringify({ evo: s.evo, evs: s.evs, stage: s.stage, form: s.form });

console.log('⓪ 美術／資料');
{ const miss = []; const chk = (f) => { if (!f || !fs.existsSync(path.join(ART, f))) miss.push(f); };
  ok(HS.IDS.length === 13 && Object.keys(H.furniture).length === 13, '家具 13 件（6b.1 加散步鞋架）');
  for (const id of HS.IDS) { const a = H.furniture[id], b = HS.FURN[id]; ok(a && a.slot === b.slot && a.zh === b.zh, id + ' slot／名對 house.json'); if (a.png) chk(a.png); else ok(id === 'wall_shoes' && a.placeholder && a.size && a.size[0] === 40 && a.size[1] === 32, id + '：未有圖 → 洋紅 placeholder 40×32', a); if (a.front) chk(a.front); if (a.glow) chk(a.glow);
    if (b.src === 'shop') ok(a.price === b.price && b.price >= 15 && b.price <= 40, id + ' 價 ' + b.price + '（15–40）'); }
  for (const k of HS.SLOTS) { const n = k === 'wall' ? 3 : 2; ok(HS.IDS.filter(i => HS.FURN[i].slot === k).length === n && H.slots[k].items.length === n, k + ' ' + n + ' 件'); }
  const shop = HS.IDS.filter(i => HS.FURN[i].src === 'shop'); ok(shop.length === 8 && shop.reduce((a, i) => a + HS.FURN[i].price, 0) === 190 && H.economy.shopTotal === 190 && H.economy.shopItems.length === 8 && shop.every(i => H.economy.shopItems.includes(i)), '商店 8 件共 190 碎（house.json economy 一致）');
  ok(HS.FURN.wall_shoes && HS.FURN.wall_shoes.zh === '散步鞋架' && HS.FURN.wall_shoes.price === 25 && HS.FURN.wall_shoes.slot === 'wall', '6b.1：散步鞋架 25 碎（牆）');
  ok(JSON.stringify(['bed_cloud', 'table_stump', 'table_round', 'wall_shelf', 'rug_round', 'rug_leaf', 'win_curtain'].map(i => HS.FURN[i].price)) === '[40,20,25,18,22,15,25]', '舊 7 件價錢不變');
  ok(HS.FURN.wall_frame.src === 'commission' && HS.FURN.win_star.src === 'commission', '委託獎＝團絨相框、星星窗');
  ok(HS.FURN.lamp_mushroom.src === 'visitor:mushroom_granny' && HS.FURN.lamp_firefly.src === 'visitor:firefly_vendor', '訪客友誼 5＝蘑菇燈、螢火瓶燈');
  for (const v of ['day', 'night']) for (const f of ['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive_blur', 'vignette']) chk('room/' + v + '/' + f + '.png');
  for (const f in H.ui.assets) chk(H.ui.assets[f]);
  for (const k in ACT.forms) for (const c of ['sit', 'prank_do', 'prank_got']) chk(ACT.forms[k][c] && ACT.forms[k][c].png);
  ok(!miss.length, '所有引用圖檔存在', miss.slice(0, 5));
  ok(['S1', 'S2', 'A3', 'H3', 'S4A'].every(k => ACT.forms[k]) && ['sprout', 'radiant', 'soft', 'lumi'].every(k => ACT.forms[k]), '細佬＋團絨形態有 sit／prank strip');
  ok(/^(5[abc]|6[abc])/.test(D.PARAMS.series2.version), 'PARAMS.series2.version＝5a', D.PARAMS.series2.version);
}
console.log('① 解鎖／預設床');
{ const s = fam({ rel: 'friend' }); ok(!HS.unlocked(s) && HS.ensure(s, at(0, 12)).reason === 'locked' && HS.enter(s, at(0, 12), T.memStore()).ok === false, '未做家人：鎖');
  const s2 = fam(); s2.sys12 = { quests: { paidN: 7 } }; X.st(s2); const st = T.memStore(); s2.needs.mood = 50;
  const r = HS.enter(s2, at(0, 12), st), o = HS.st(s2);
  ok(r.ok && r.fresh && o.slots.bed === 'bed_leaf' && o.owned.bed_leaf && o.q0 === 7, '家人：入屋送葉仔床、擺好、記委託基數', HS.summary(s2, at(0, 12)));
  ok(r.welcome && r.welcome.first && r.welcome.mood === true && s2.needs.mood === 51, '葉仔床計新家具心情 +1');
  ok(X.st(s2).wallet.total === 0, '送床唔收碎');
  const r2 = HS.enter(s2, at(0, 13), st); ok(!r2.fresh && !r2.welcome && s2.needs.mood === 51, '第二次入屋唔再送／唔再加');
  ok(Object.values(o.slots).filter(Boolean).length === 1, '其餘 5 位空');
}
console.log('② 商店／換擺');
{ const s = fam(), st = T.memStore(); s.needs.mood = 50; HS.enter(s, at(0, 12), st); const w = X.st(s).wallet; w.total = 30;
  ok(HS.buy(s, 'bed_cloud', X.spend, at(0, 12)).reason === 'poor' && w.total === 30, '碎唔夠買唔到、唔扣');
  ok(HS.buy(s, 'wall_frame', X.spend, at(0, 12)).reason === 'notShop', '委託獎唔賣');
  const b = HS.buy(s, 'rug_leaf', X.spend, at(0, 12)); ok(b.ok && w.total === 15, '買葉仔地氈 15 碎');
  ok(HS.buy(s, 'rug_leaf', X.spend, at(0, 12)).reason === 'owned', '買過唔再買');
  ok(HS.cardState(s, 'rug_leaf') === 'owned' && HS.cardState(s, 'rug_round') === 'buy' && HS.cardState(s, 'bed_leaf') === 'equipped' && HS.cardState(s, 'win_star') === 'locked', '卡狀態');
  ok(HS.place(s, 'rug', 'rug_round', at(0, 12), st).reason === 'notOwned' && HS.place(s, 'bed', 'rug_leaf', at(0, 12), st).reason === 'slot', '未擁有／錯位唔擺得');
  const m0 = s.needs.mood, p = HS.place(s, 'rug', 'rug_leaf', at(0, 12), st); ok(p.ok && p.first && p.mood && s.needs.mood === m0 + 1, '第一次擺 +1 心情');
  const c = HS.place(s, 'rug', null, at(0, 12), st); ok(c.ok && c.cleared === 'rug_leaf' && HS.st(s).slots.rug === null, '收起');
  const w0 = w.total, p2 = HS.place(s, 'rug', 'rug_leaf', at(0, 12), st); ok(p2.ok && !p2.first && s.needs.mood === m0 + 1 && w.total === w0, '換擺／再擺唔使碎、唔再加心情');
}
console.log('③ 心情共用每日上限 5');
{ const s = fam(), st = T.memStore(); st.set('fpet_daily_v1', JSON.stringify({ [T.bridgeDay(at(0, 12))]: 4 })); s.needs.mood = 50;
  const r = HS.enter(s, at(0, 12), st); ok(r.welcome.mood === true && s.needs.mood === 51, '共用額剩 1：床 +1');
  const w = X.st(s).wallet; w.total = 100; HS.buy(s, 'rug_leaf', X.spend, at(0, 12)); const p = HS.place(s, 'rug', 'rug_leaf', at(0, 12), st);
  ok(p.first && p.mood === false && s.needs.mood === 51, '額滿：記第一次但唔加');
  ok(T.moodGrant(s, 'poke', at(0, 12), st).reason === 'cap', '觸摸同樣食共用額（已滿）');
  const s2 = fam(), st2 = T.memStore(); for (const k of ['poke', 'hold', 'tickle', 'pull']) T.moodGrant(s2, k, at(0, 12), st2); HS.enter(s2, at(0, 12), st2);
  ok(JSON.parse(st2.get('fpet_daily_v1'))[T.bridgeDay(at(0, 12))] === 5, '觸摸 4＋擺床 1＝5（同一個 key）');
}
console.log('④ 委託獎／訪客獎');
{ const s = fam(); X.st(s).quests.paidN = 10; HS.enter(s, at(0, 12), T.memStore());
  ok(HS.syncRewards(s, at(0, 12)).length === 0 && HS.commissionLeft(s, 'wall_frame') === 3, '解鎖前完成嘅委託唔計');
  X.st(s).quests.paidN = 13; ok(HS.syncRewards(s, at(1, 12)).join() === 'wall_frame', '家人後 3 張 → 團絨相框');
  X.st(s).quests.paidN = 19; ok(HS.syncRewards(s, at(3, 12)).join() === 'win_star', '9 張 → 星星窗');
  ok(HS.syncRewards(s, at(3, 12)).length === 0, '唔重複送');
  const s2 = fam(); HS.enter(s2, at(0, 12), T.memStore()); s2.b3b = { vis: { mushroom_granny: { fr: 5, max: true } } };
  ok(HS.syncRewards(s2, at(0, 12)).join() === 'lamp_mushroom', '蘑菇婆婆友誼 5 → 蘑菇燈（追溯）');
  s2.b3b.vis.firefly_vendor = { fr: 5, max: true }; ok(HS.syncRewards(s2, at(0, 12)).join() === 'lamp_firefly', '螢火小販友誼 5 → 螢火瓶燈');
  ok(HS.place(s2, 'lamp', 'lamp_firefly', at(0, 12), T.memStore()).ok, '訪客燈擺得');
}
console.log('⑤ 整蠱／同床瞓／行走區');
{ const s = fam(); HS.enter(s, at(0, 12), T.memStore());
  ok(HS.notePrank(s, at(0, 12)) && HS.notePrank(s, at(0, 13)) && HS.notePrank(s, at(0, 14)) && !HS.notePrank(s, at(0, 15)) && HS.prankLeft(s, at(0, 15)) === 0, '每日最多 3 次');
  ok(HS.canPrank(s, at(1, 9)) && HS.prankLeft(s, at(1, 9)) === 3, '翌日重置');
  const i0 = S2.st(s).intim; HS.notePrank(s, at(1, 9)); ok(S2.st(s).intim === i0, '整蠱唔加親密');
  ok(HS.sleepTime(at(0, 21)) && HS.sleepTime(at(0, 2, 59)) && !HS.sleepTime(at(0, 3)) && !HS.sleepTime(at(0, 20, 59)), '21:00–03:00 同床瞓');
  const bl = HS.blockers(s, H); ok(bl.length === 1 && !HS.walkable(138, 262, H.walk.rect, bl) && HS.walkable(60, 300, H.walk.rect, bl), '床 blocker 擋住');
  let bad = 0; for (let i = 0; i < 200; i++) { const p = HS.pickSpot(H.walk.rect, bl); if (!HS.walkable(p[0], p[1], H.walk.rect, bl)) bad++; } ok(!bad, 'pickSpot 只揀行得嘅位');
}
console.log('⑥ 唔郁團絨');
{ const s = fam(), r0 = routeSnap(s), st = T.memStore(); X.st(s).wallet.total = 200; HS.enter(s, at(0, 12), st);
  for (const id of HS.IDS.filter(i => HS.FURN[i].src === 'shop')) { HS.buy(s, id, X.spend, at(0, 12)); HS.place(s, HS.FURN[id].slot, id, at(0, 12), st); }
  HS.notePrank(s, at(0, 12)); ok(routeSnap(s) === r0, '路線分／進化資料冇郁');
  ok(X.st(s).wallet.total === 200 - 190 && HS.st(s).owned.wall_shoes, '商店 8 件買晒用 190 碎', X.st(s).wallet.total);
  const raw = JSON.parse(JSON.stringify(s)); raw.pet2.house.slots.bed = 'nope'; raw.pet2.house.owned.zzz = 1; const o = HS.st(raw); ok(o.slots.bed === null && !o.owned.zzz, 'sanitize 壞存檔');
}
console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
