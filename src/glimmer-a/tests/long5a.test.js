/* 第 5 批 5a（docs-gdd/series2-4a4b-spec.md v1.1 §5a＋5a–5c 玩法位定案）：長住＋家族等級 s.fam — 美術對數／經驗表／升級解鎖／開房送手信／新蛋二揀一／養 2 隻上限／住滿／做主養／搬房／家具一件一間／族譜／§7 唔郁。 */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), HS = require('../src/house.js'), F = require('../src/long5a.js'), T = require('../src/touch.js');
const fs = require('fs'), path = require('path'), ART = path.join(__dirname, '../art/series2_long');
const J = (f) => JSON.parse(fs.readFileSync(path.join(ART, f), 'utf8')), L = J('5a/long_5a.json'), L5b = J('5b/long_5b.json');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
const NOW = at(0, 12), env = { rebirth: SIM.rebirth, trFk: 'evo_still_moon' };
/* 4b 屋企：團絨靜光 → 細佬做咗家人（S6）；4b 屋已開 */
function fam(o) { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; s.dex = ['tide']; S2.noteElder(s, at(-25, 12)); S2.deliver(s, at(-24, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(-20, 12)); Object.assign(p, { intim: 90, rel: 'family' }, o || {}); HS.ensure(s, at(-5, 12)); return s; }
const routeSnap = (s) => JSON.stringify({ evo: s.evo, evs: s.evs, form: s.form });

console.log('⓪ 美術／資料對數');
{ ok(JSON.stringify(F.THRESH) === JSON.stringify(L.familyLevel.thresholds || L.familyLevel.xp || F.THRESH), '門檻 0/60/150/270/420/600/810/1050/1320/1620');
  const miss = []; const chk = (f) => { if (!fs.existsSync(path.join(ART, f))) miss.push(f); };
  for (const r of ['room2', 'room3', 'room4']) for (const v of ['day', 'night']) for (const f of ['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive_blur', 'vignette']) chk('5a/rooms/' + r + '/' + v + '/' + f + '.png');
  for (const x of F.SOUV) { chk(x.px); chk(x.icon); }
  ok(!miss.length, '房 2–4 日夜圖層＋10 件手信圖存在', miss.slice(0, 4));
  const sv = L5b.souvenirs || {}; const list = Array.isArray(sv) ? sv : Object.keys(sv).map(k => Object.assign({ id: k }, sv[k]));
  ok(list.length === 10 && F.SOUV.every(x => list.some(y => y.id === x.id && (!y.zh || y.zh === x.zh))), '手信池 10 件 id／名對 long_5b.json');
  ok(F.CAP === 4 && F.RAISE_MAX === 2, '每間房 4 隻；養緊最多 2 隻');
  ok(F.XP.raise_one === 50 && F.XP.dex_new_form === 10 && F.XP.furniture_new === 5 && F.XP.expedition_return === 3, '經驗：養大 +50、新形態 +10、新家具 +5（遠足 +3＝5b）');
  ok(F.lvOf(0) === 1 && F.lvOf(59) === 1 && F.lvOf(60) === 2 && F.lvOf(419) === 4 && F.lvOf(420) === 5 && F.lvOf(1620) === 10 && F.lvOf(99999) === 10, 'lvOf 邊界');
  ok(Object.keys(L.familyLevel.unlocks).every(k => JSON.stringify(L.familyLevel.unlocks[k].map(u => u.id + u.zh)) === JSON.stringify(F.UNLOCKS[k].map(u => u.id + u.zh))) && JSON.stringify(L.familyLevel.xp) === JSON.stringify(F.XP), '解鎖／經驗表對 long_5a.json');
  ok(['room2', 'room3', 'room4'].every(k => L.rooms[k].unlockLv === F.ROOM[k].lv && L.rooms[k].zh === F.ROOM[k].zh) && L.roomRules.capacity === F.CAP, '房名／開房等級對數');
  ok(F.UNLOCKS[2][0].id === 'room2' && F.UNLOCKS[5][0].id === 'room3' && F.UNLOCKS[8][0].id === 'room4' && F.UNLOCKS[10].map(x => x.id).join() === 'family_title,tree_gold', '解鎖表：Lv2/5/8 開房、Lv10 稱號＋金族譜');
  ok(/^(5[abc]|6[a-d])/.test(D.PARAMS.series2.version), '版本 5a', D.PARAMS.series2.version);
}
console.log('① 初始化＋追溯經驗');
{ const s = fam(); S2.st(s).hatchDay = S2.dayNum(NOW) - 5; const ev = F.scan(s, NOW, { kidFk: 'A2' }), o = F.st(s);
  ok(ev.some(e => e.k === 'init'), '第一次 scan＝init');
  ok(o.seen['raise:tr1'] && !o.seen['raise:k1'] && o.xp === 50 + 10 + 10 + 5 + 5, '追溯：團絨靜光 +50、圖鑑 tide +10、細佬 A2 +10、葉仔床 +5（＋開房手信 +5）', o.xp);
  ok(o.lv === 2 && o.rooms.room2.open && F.SV[o.rooms.room2.gift] && o.rooms.room2.deco === o.rooms.room2.gift, 'Lv2 → 開房 2 ＋送 1 件手信（擺好）', o.rooms.room2);
  const x0 = o.xp; F.scan(s, NOW + 1000, { kidFk: 'A2' }); ok(F.st(s).xp === x0, '同一樣嘢唔重複計');
  ok(!o.offer, '第一次靜光已經用咗 4a 細佬蛋 → 唔再排新蛋（細佬未成年）');
  const s0 = SIM.newState(NOW, 1); s0.stage = 'elder'; F.scan(s0, NOW); ok(F.st(s0).seen['raise:tr1'] && !F.st(s0).offer, '第一次靜光（pet2 none）：+50，但唔排 5a 新蛋（4a 直接送細佬蛋）');
}
console.log('② 細佬成年（S6＋家人）→ 翌日新蛋');
{ const s = fam(); const p = S2.st(s); p.hatchDay = S2.dayNum(NOW) - 20; ok(S2.stageOf(s, NOW) === 'S6' && F.kidAdult(s, NOW), '細佬 S6＋家人＝成年');
  F.scan(s, NOW, { kidFk: 'A3' }); const o = F.st(s);
  ok(o.seen['raise:' + p.fid] && o.offer && o.offer.due === S2.dayNum(NOW) + 1, '+50＋新蛋排喺翌日', o.offer);
  ok(!F.offerReady(s, NOW) && F.offerReady(s, at(1, 8)), '今日未到、聽日到');
  const c = F.choices(s, at(1, 8)); ok(c.tr.ok && c.kid.ok, '兩個都揀得（主養靜光＋細佬成年）', c);
  // 揀細佬蛋：成年細佬搬入屋，新細佬蛋（大佬＝而家主養）
  const h0 = JSON.stringify(HS.st(s)), r = F.pick(s, 'kid', at(1, 9), env), p2 = S2.st(s);
  ok(r.ok && r.moved && r.moved.kind === 'kid' && r.moved.room === 'room1', '細佬蛋：成年細佬搬入屋', r);
  ok(p2.phase === 'egg' && p2.bro === 'tr1' && p2.fid === 'k2' && JSON.stringify(HS.st(s)) === h0 && HS.unlocked(s), '新細佬蛋（大佬 tr1；屋保留、照開）', p2);
  ok(!F.st(s).offer && F.count(s, 'room1') === 2, '新蛋已揀；房 1＝主養＋住客細佬（蛋唔計）', F.occupants(s, 'room1'));
  const c2 = F.choices(s, at(1, 10)); ok(!c2.kid.ok && c2.kid.reason === 'raising' && c2.kid.zh === '細佬養緊', '有細佬養緊 → 細佬蛋灰「細佬養緊」');
  // 再成年 → 團絨蛋
  o.offer = { due: S2.dayNum(at(1, 10)), at: 1 }; const rs = routeSnap(s), g0 = s.gen;
  const r2 = F.pick(s, 'tr', at(1, 11), env);
  ok(r2.ok && s.stage === 'egg' && s.gen === g0 + 1 && !(s.memorial || []).length, '團絨蛋：新一代光卵（gen+1、冇化光紀念冊）', { gen: s.gen, m: s.memorial });
  ok(F.resOf(s, 'tr1') && F.resOf(s, 'tr1').snap.stage === 'elder' && F.resOf(s, 'tr1').snap.form === 'tide', '舊主養（靜光水珠）搬入屋', F.resOf(s, 'tr1') && F.resOf(s, 'tr1').fk);
  ok(JSON.stringify(s.evo) === JSON.stringify({ evIn: {}, care: {} }) && rs !== routeSnap(s), '新一代 §7 由零開始（evo 清）');
  const c3 = F.choices(s, at(1, 12)); ok(!c3.tr.ok && c3.tr.reason === 'mainYoung', '主養未成年 → 團絨蛋灰', c3.tr);
}
console.log('③ 住滿／開房');
{ const s = fam(); const p = S2.st(s); p.hatchDay = S2.dayNum(NOW) - 20; F.scan(s, NOW, { kidFk: 'A3' }); const o = F.st(s);
  ok(F.openRooms(s).join() === 'room1,room2', 'Lv2：房 1＋2');
  for (let i = 0; i < 6; i++) o.res.push({ id: 'trX' + i, kind: 'tr', gen: 90 + i, fk: 'sprout', name: 'x', room: i < 2 ? 'room1' : 'room2', at: 1, snap: { stage: 'elder' } });
  ok(F.count(s, 'room1') === 4 && F.count(s, 'room2') === 4 && F.houseFull(s), '房 1（主養＋細佬＋2）＋房 2（4）＝住滿');
  const c = F.choices(s, NOW); ok(!c.tr.ok && c.tr.reason === 'full' && !c.kid.ok && c.kid.reason === 'full', '住滿：兩隻蛋都灰（講升級開房）', c);
  ok(F.pick(s, 'tr', NOW, env).ok === false && s.stage === 'elder', '住滿揀唔到、主養唔郁');
  F.addXp(s, 'raise_one', 420 - o.xp, NOW); ok(o.lv === 5 && F.roomOpen(s, 'room3') && o.rooms.room3.gift && o.rooms.room3.gift !== o.rooms.room2.gift, 'Lv5 → 房 3（另一件手信）', [o.rooms.room2.gift, o.rooms.room3.gift]);
  ok(F.freeRoom(s) === 'room3' && F.choices(s, NOW).tr.ok, '開房後有位');
  ok(o.lvQ.includes(3) && o.lvQ.includes(4) && o.lvQ.includes(5), '升級彈窗隊列（Lv3–5）', o.lvQ);
  F.addXp(s, 'raise_one', 1620, NOW); ok(o.lv === 10 && F.roomOpen(s, 'room4') && F.tree(s, NOW).gold && F.lvInfo(s).title === F.TITLE && F.has(s, 'tree_gold'), 'Lv10：房 4＋金族譜＋稱號');
  ok(Object.keys(o.sv).length === 3, '3 間新房送咗 3 件唔同手信', Object.keys(o.sv));
}
console.log('④ 做主養／搬房');
{ const s = fam(); const p = S2.st(s); p.hatchDay = S2.dayNum(NOW) - 20; F.scan(s, NOW, { kidFk: 'A3' }); const o = F.st(s); o.offer = { due: 0, at: 1 };
  F.pick(s, 'kid', NOW, env); const kidOld = F.st(s).res.find(r => r.kind === 'kid');
  o.offer = { due: 0, at: 1 }; ok(!F.choices(s, NOW).kid.ok, '細佬蛋孵緊 → 唔揀得細佬'); F.pick(s, 'tr', NOW, env);
  s.stage = 'sprout'; ok(F.canMain(s, 'tr1', NOW).reason === 'mainYoung', '主養未成年：住客團絨唔做得主養');
  s.stage = 'elder'; s.form = 'moon'; s.growthSec = 5; const g2 = s.gen;
  const r = F.makeMain(s, 'tr1', NOW, env); ok(r.ok && s.gen === 1 && s.form === 'tide' && F.resOf(s, 'tr' + g2) && F.resOf(s, 'tr' + g2).snap.form === 'moon', '對調：水珠做返主養、月眠搬入同一間房', { gen: s.gen, form: s.form });
  ok(F.isMain(s, 'tr1') && F.tree(s, NOW).nodes.find(n => n.id === 'tr1').state === 'main', '族譜皇冠');
  // 5a.1：細佬做主養唔使等 pet2 蛋；pet2 嘅蛋唔郁
  const ph0 = S2.st(s).phase; ok(F.canMain(s, kidOld.id, NOW).ok, '5a.1：住客成年細佬可以做主養（pet2 有蛋都得）');
  const r2 = F.makeMain(s, kidOld.id, NOW, env); const o2 = F.st(s);
  ok(r2.ok && o2.km && o2.km.id === kidOld.id && o2.main === 'kid:' + kidOld.id && F.isMain(s, kidOld.id) && !F.resOf(s, kidOld.id), '細佬做主養（入花園中間位）', r2);
  ok(F.resOf(s, 'tr1') && F.resOf(s, 'tr1').kind === 'tr' && S2.st(s).phase === ph0, '原主養水珠搬入屋做住客；pet2 唔郁', S2.st(s).phase);
  ok(s.form === 'moon' && s.gen === g2 && s.stage === 'elder', '浮動：顯示屋企最新一代團絨（月眠）', { form: s.form, gen: s.gen });
  ok(F.tree(s, NOW).nodes.find(n => n.id === kidOld.id).state === 'main' && !F.tree(s, NOW).nodes.some(n => n.id === 'tr' + g2 && n.state === 'main'), '族譜皇冠跟細佬');
  ok(F.moveRoom(s, 'tr' + g2, 'room2').ok && F.resOf(s, 'tr' + g2).room === 'room2' && F.moveRoom(s, 'tr' + g2, 'room4').reason === 'locked', '搬房：已開房 OK、未開房鎖');
}
console.log('⑤ 家具一件一間房＋手信擺設');
{ const s = fam(); F.scan(s, NOW, {}); const st = T.memStore(); const o = F.st(s), g = o.rooms.room2.gift;
  ok(F.cardState(s, 'room1', 'bed_leaf') === 'equipped' && F.cardState(s, 'room2', 'bed_leaf') === 'elsewhere', '葉仔床喺房 1 → 房 2 顯示「喺第二間」');
  const r = F.place(s, 'room2', 'bed', 'bed_leaf', NOW, st); ok(r.ok && r.from === 'room1' && HS.st(s).slots.bed === null && o.rooms.room2.slots.bed === 'bed_leaf', '搬去房 2：房 1 收起');
  ok(F.place(s, 'room1', 'bed', 'bed_leaf', NOW, st).from === 'room2' && o.rooms.room2.slots.bed === null, '再擺返房 1');
  ok(F.cardState(s, 'room2', g) === 'equipped' && F.cardState(s, 'room1', g) === 'elsewhere', '手信擺咗喺房 2');
  s.needs.mood = 50; const r2 = F.place(s, 'room1', 'deco', g, NOW, st); ok(r2.ok && r2.first && s.needs.mood === 51 && o.rooms.room1.deco === g && !o.rooms.room2.deco, '手信擺房 1（第一次心情 +1）');
  ok(F.place(s, 'room1', 'deco', 'sv_rainbow', NOW, st).reason === 'notOwned' || o.sv.sv_rainbow, '冇嘅手信擺唔到');
  ok(F.blockers(s, 'room2', { slots: { bed: { anchor: [0, 0] } }, walk: { blockers: { bed: [0, 0, 1, 1] } } }).length === 0, '房 2 冇床 → 冇阻擋');
}
console.log('⑥ sanitize／序列化');
{ const s = fam(); F.scan(s, NOW, {}); const t = SIM.deserialize(SIM.serialize(s), NOW); ok(t.fam && t.fam.xp === F.st(s).xp && F.st(t).rooms.room2.open, '序列化保留 s.fam');
  const b = { fam: { xp: 'x', res: [1, null, { id: 3 }], rooms: 5, sv: { bad: 1 }, offer: 'no', lvQ: [1, 99, 'a'], main: 4 } }; F.st(b);
  ok(b.fam.xp === 0 && b.fam.res.length === 0 && b.fam.rooms.room2.open === 0 && !Object.keys(b.fam.sv).length && b.fam.offer === null && b.fam.main === null && JSON.stringify(b.fam.lvQ) === '[2,10]', '壞資料 → 預設', b.fam);
  const s2 = SIM.newState(NOW, 3); s2.stage = 'elder'; s2.fadeReady = true; s2.fam = { genMax: 6 }; SIM.fade(s2, NOW); ok(s2.gen === 7, '化光代數跳過住客已用嘅代數');
  ok(F.duoGap(30, 30) === 26 && F.duoGap(10, 10) === 22 && F.interactFrame(0) === 0 && F.interactFrame(5000) === 7, '打招呼 gap／幀');
}
console.log('⑦ 族譜');
{ const s = fam(); const p = S2.st(s); p.hatchDay = S2.dayNum(NOW) - 20; F.scan(s, NOW, { kidFk: 'A3' }); F.st(s).offer = { due: 0 }; F.pick(s, 'kid', NOW, env); F.st(s).offer = { due: 0 }; F.pick(s, 'tr', NOW, env);
  const t = F.tree(s, NOW); const ids = t.nodes.map(n => n.id);
  ok(ids.includes('tr1') && ids.includes('tr2') && ids.includes('k1') && ids.includes('k2'), '族譜有 2 代團絨＋2 隻細佬', ids);
  ok(t.links.some(l => l[0] === 'tr1' && l[1] === 'tr2') && t.links.some(l => l[0] === 'tr1' && l[1] === 'k1'), '連線：tr1→tr2、tr1→細佬', t.links);
  ok(t.nodes.find(n => n.id === 'tr2').raising && t.nodes.find(n => n.id === 'k2').raising && t.nodes.find(n => n.id === 'k1').row === 2, '養緊標記＋細佬喺第 2 代');
}
console.log('⑧ 節奏（Lv5 約 60–80 日）');
{ /* 每輪 16 日：靜光 +50、細佬 S6 +50、團絨圖鑑 +10、細佬 6 個形態 +60、2 件家具 +10 → 每輪約 180 → 420 要 2–3 輪（第 3 輪起重複形態減少） */
  let xp = 0, day = 0; const seen = new Set(); const kidForms = (i) => ['S1', 'S2', 'ABCDEFGH'[i % 8] + '1', 'S4' + 'ABCDEFGH'[i % 8], 'ABCDEFGH'[(i + 3) % 8] + '2', 'ABCDEFGH'[(i + 3) % 8] + '3'];
  const trForms = ['soft', 'tide', 'soft', 'moon', 'dust'];
  for (let i = 0; i < 9 && F.lvOf(xp) < 5; i++) { day += i === 0 ? 30 : 20; xp += 100; if (!seen.has('t' + trForms[i % 5])) { seen.add('t' + trForms[i % 5]); xp += 10; } for (const f of kidForms(i)) if (!seen.has(f)) { seen.add(f); xp += 10; } xp += i < 6 ? 10 : 0; }
  ok(day >= 55 && day <= 85, 'Lv5 約 ' + day + ' 日（60–80）', { day, xp });
}
console.log('⑨ 5a.1 細佬做主養（遊策裁定 3 條）');
{ const SYS = require('../src/systems.js');
  const s = fam(); const p = S2.st(s); p.hatchDay = S2.dayNum(NOW) - 20; F.scan(s, NOW, { kidFk: 'A3' }); const o = F.st(s);
  ok(F.isPet2Kid(s, p.fid) && F.canMain(s, p.fid, NOW).ok, '成年 pet2 細佬可以做主養');
  p.hatchDay = S2.dayNum(NOW) - 1; ok(F.canMain(s, p.fid, NOW).reason === 'kidYoung', '未成年細佬唔得（kidYoung）'); p.hatchDay = S2.dayNum(NOW) - 20;
  const fid = p.fid, r = F.makeMain(s, fid, NOW, Object.assign({ kidFk: 'B3' }, env));
  // 規則 1：細佬入主位、團絨搬入屋、pet2 空出嚟等新蛋
  ok(r.ok && r.from === 'garden' && o.km && o.km.id === fid && o.km.fk === 'B3' && S2.st(s).phase === 'none', '①細佬做主養：pet2 空返', S2.st(s));
  ok(F.resOf(s, 'tr1') && F.resOf(s, 'tr1').kind === 'tr' && F.resOf(s, 'tr1').room === 'room1', '①原主養團絨（靜光）搬入房 1 長住');
  ok(o.offer && o.offer.due === S2.dayNum(NOW) + 1 && F.choices(s, NOW).tr.reason === 'kidMain' && F.choices(s, NOW).kid.ok, '①聽日新蛋：只揀到細佬蛋（團絨蛋要團絨做返主養）', F.choices(s, NOW));
  F.st(s).offer = { due: 0, at: 1 }; ok(F.pick(s, 'tr', NOW, env).ok === false && F.pick(s, 'kid', NOW, env).ok && o.km && o.km.id === fid && S2.st(s).phase === 'egg', '①揀細佬蛋 → pet2 有新蛋、主養仍係細佬');
  // 規則 2：照顧循環（肚餓／便便／瞓）照行；冇 §7 路線分、冇碎、唔長大、唔化光
  const snap = routeSnap(s), g0 = s.growthSec, st0 = s.stage; s.needs.hunger = 60; s.poops = 0; s.poopTimer = 0;
  for (let i = 0; i < 360; i++) SIM.step(s, 60, {});
  ok(s.needs.hunger < 60 && s.stage === st0 && s.growthSec === g0, '②主養細佬：肚餓會跌、唔長大', { h: s.needs.hunger, g: s.growthSec });
  ok(s.poops > 0 || s.poopTimer > 0, '②便便循環照行', { poops: s.poops, t: s.poopTimer });
  s.needs.hunger = 30; const f = SIM.feed(s, D.FOODS[0].id); ok(f.ok && s.needs.hunger > 30 && routeSnap(s) === snap, '②餵食得、§7 路線唔郁');
  ok(SIM.fade(s, NOW).ok === false && SYS.grant(s, 5, 'mg', NOW) === 0 && SYS.grant(s, 5, 'quest', NOW) === 0, '②唔化光、小遊戲／委託唔出碎');
  ok(S2.noteElder(s, NOW) === false, '②唔觸發 4a 郵差送蛋');
  // 規則 3：浮動只顯示團絨（s 嘅團絨欄位＝屋企最新團絨）
  ok(s.stage === 'elder' && s.form === 'tide' && F.latestTr(o).id === 'tr1', '③浮動照顯示團絨（水珠靜光）', { st: s.stage, f: s.form });
  // 對調返團絨：細佬帶住照顧欄位返屋
  s.needs.hunger = 42; const back = F.makeMain(s, 'tr1', NOW, env);
  ok(back.ok && !o.km && o.main === null && F.resOf(s, fid) && F.resOf(s, fid).care.needs.hunger === 42 && s.form === 'tide' && F.isMain(s, 'tr1'), '揀返團絨做主養：細佬（連照顧狀態）返屋');
  ok(F.makeMain(s, fid, NOW, env).ok && s.needs.hunger === 42, '再做主養：照顧狀態還原');
  const t = SIM.deserialize(SIM.serialize(s), NOW); ok(t.fam.km && t.fam.km.id === fid && t.fam.main === 'kid:' + fid, '序列化保留細佬主養');
}
console.log((fail ? '✗' : '✓') + ' long5a ' + pass + '/' + (pass + fail));
if (fail) process.exit(1);
