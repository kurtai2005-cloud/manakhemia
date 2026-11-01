/* systems12 第 2 批 Node 測試：node tests/systems12b.test.js
   系統 5 小遊戲 → 2 小圃種花 → 4 散步收集＋收藏櫃 → 11 成就（docs-gdd/systems12-v1.md）。數值讀 PARAMS.systems12b。 */
const S = require('../src/sim.js');
const D = require('../src/data.js');
const X = require('../src/systems.js');
const B = require('../src/systems2.js');
const P = D.PARAMS, C = P.systems12b;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const T0 = new Date(2026, 10, 2, 9, 0).getTime(), DAY = 864e5;
function mk(stage, t) { const s = S.newState(t || T0, 4242); s.stage = stage || 'juvenile'; return s; }
const seq = a => { let i = 0; return () => a[Math.min(i++, a.length - 1)]; };

console.log('① 系統 5 小遊戲：config＝規格');
{
  ok(C.games.dailyRewarded === 5 && C.games.catch.durationSec === 30 && C.games.hide.spots[0] === 3 && C.games.hide.spots[1] === 5 && C.games.hide.timeLimitSec <= 45, '接光點 30 秒；捉迷藏 3–5 位、≤45 秒；每日頭 5 局有獎');
  ok([0, 26, 27, 66, 67, 200].map(v => B.gameStars('catch', v)).join() === '1,1,2,2,3,3', '接光點星數（分數線 config）', [0, 26, 27, 66, 67, 200].map(v => B.gameStars('catch', v)).join());
  ok([0, 1, 2, 3].map(v => B.gameStars('hide', v)).join() === '1,1,2,3', '捉迷藏星數：搵到 0–3 輪 → 1–3 星');
  const s = mk(); const mood0 = s.needs.mood, gr0 = s.grains, mg0 = s.stats.mgPlays, care0 = JSON.stringify(s.evo);
  const r = B.gameFinish(s, 'catch', 80, T0);
  ok(r.stars === 3 && r.shards === 3 && r.rewarded && X.wallet(s, T0).o === 3, '一局 3 星 → 3 星星碎', JSON.stringify(r));
  ok(s.needs.mood === mood0 && s.grains === gr0, '唔加心情／光粒（規格：新系統唔加心情池）');
  ok(s.stats.mgPlays === mg0 + 1 && JSON.stringify(s.evo) !== care0 && r.counted, '計一局 mg（mgPlays＋noteCare mg → 火苗）');
  for (let i = 0; i < 4; i++) B.gameFinish(s, 'hide', 3, T0 + i);
  const r6 = B.gameFinish(s, 'hide', 3, T0 + 9);
  ok(!r6.rewarded && r6.shards === 0 && r6.counted && X.wallet(s, T0).o === 15, '第 6 局冇星星碎（照計 mg）；頭 5 局全 3 星＝15＝其他上限', X.wallet(s, T0).o);
  const r7 = B.gameFinish(s, 'catch', 80, T0 + DAY);
  ok(r7.rewarded && r7.playIndex === 1, '第二日重新計');
  const e = mk('egg'); const re = B.gameFinish(e, 'catch', 80, T0); ok(!re.counted, '光卵：唔計 mg');
  const s2 = mk(); X.grant(s2, 14, 'dev', T0); const r8 = B.gameFinish(s2, 'catch', 80, T0); ok(r8.shards === 1, '經 wallet 其他上限 15（已有 14 → 只得 1）', r8.shards);
  const cp = B.catchParams(); ok(cp.durationSec === 30 && cp.starScore === C.games.catch.dots.small && cp.stonePenalty === 10, '接光點 Minigame 覆寫參數');
  const m = new S.Minigame(5, cp); let n = 0; while (!m.over && n < 5000) { m.update(1 / 30, m.basketX); n++; }
  ok(m.over && Math.abs(m.t - 30) < 0.01 && m.M.durationSec === 30, '接光點 30 秒完場', m.t);
  const m2 = new S.Minigame(5); ok(m2.M === P.mg && m2.M.durationSec === 45, '接星屑（舊）唔變：45 秒');
  const h = new B.HideGame(99); let sizes = new Set(); for (let sd = 1; sd < 200; sd++) sizes.add(new B.HideGame(sd).spots.length);
  ok([...sizes].sort().join() === '3,4,5', '捉迷藏每輪 3／4／5 個位', [...sizes].join());
  let res; res = h.pick(h.at); ok(res.hit && h.found === 1 && h.round === 1, '揀中 → 搵到');
  const miss = (h.at + 1) % h.spots.length; res = h.pick(miss); ok(res.ok && !res.hit && !res.roundOver, '揀錯一次 → 仲有機會');
  res = h.pick(miss); ok(!res.ok, '同一個位唔可以再揀');
  res = h.pick((h.at + 2) % h.spots.length === h.at ? (h.at + 3) % h.spots.length : (h.at + 2) % h.spots.length); ok(res.roundOver && !res.hit, '兩次都錯 → 下一輪');
  res = h.pick(h.at); ok(res.over && h.found === 2, '3 輪完場（搵到 2）');
  const h2 = new B.HideGame(3); h2.update(41); ok(h2.over && h2.left === 0, '限時 40 秒（≤45）');
}
console.log('② 系統 2 小圃種花');
{
  ok(C.garden.pots === 3 && C.garden.flowers.length === 6, '3 格花盆、6 種花');
  ok(C.garden.flowers.map(f => f.name + f.route).join() === '藍鈴moon,日菊bright,苔菇shroom,晶草crystal,火鈴ember,露草tide', '花 → 路線＝規格');
  const s = mk(); let r = B.plant(s, 0, 'bluebell', T0); ok(!r.ok && r.reason === 'shards', '冇星星碎買唔到種子');
  X.grant(s, 15, 'dev', T0); r = B.plant(s, 0, 'bluebell', T0); ok(r.ok && X.wallet(s, T0).total === 15 - C.garden.seedPrice, '星星碎買種子（' + C.garden.seedPrice + '）');
  ok(!B.plant(s, 0, 'daisy', T0).ok && !B.plant(s, 3, 'daisy', T0).ok && !B.plant(mk('egg'), 0, 'daisy', T0).ok, '有花／冇呢格／光卵 → 唔得');
  ok(B.potInfo(S.deserialize(S.serialize(s)).sys12b.garden.pots[0], T0).k === 'bluebell', '存檔保留');
  ok(B.potInfo(s.sys12b.garden.pots[0], T0).stage === 0, '剛種：種子');
  ok(B.water(s, 0, T0).ok && !B.water(s, 0, T0 + 3600e3).ok, '一日淋一次');
  ok(B.potInfo(s.sys12b.garden.pots[0], T0).stage === 1, '淋咗水：芽');
  ok(B.potInfo(s.sys12b.garden.pots[0], T0 + DAY).stage === 2, '第 2 日：花苞');
  B.water(s, 0, T0 + DAY); const I = B.potInfo(s.sys12b.garden.pots[0], T0 + 2 * DAY);
  ok(I.bloomed && I.stage === 3, '淋 2 日 → 第 3 日開花（2–3 日）');
  const b5 = () => JSON.stringify((s.evo.b5sys || {})[s.stage] || {});
  const bl = B.gardenTick(s, T0 + 2 * DAY); ok(bl.length === 1 && bl[0].route === 'moon' && bl[0].pts === C.garden.bloomPts && b5().includes('moon'), '開花 → 月眠 +' + C.garden.bloomPts + '（addRoutePts，受 25% cap）', b5());
  ok(B.gardenTick(s, T0 + 3 * DAY).length === 0, '路線分只加一次');
  r = B.harvest(s, 0, T0 + 3 * DAY); ok(r.ok && r.vase && s.sys12b.garden.vase.bluebell === 1 && !s.sys12b.garden.pots[0], '開咗嘅花剪落花瓶（第 3 批房間擺）');
  B.plant(s, 1, 'daisy', T0); const I2 = B.potInfo(s.sys12b.garden.pots[1], T0 + 2 * DAY);
  ok(I2.wilted && I2.stage === -1 && !B.water(s, 1, T0 + 2 * DAY).ok, '連續 ' + C.garden.dryDaysToWilt + ' 日冇淋 → 枯，淋唔返');
  const lifeOk = s.stage === 'juvenile' && !s.dead; ok(lifeOk && B.harvest(s, 1, T0 + 2 * DAY).cleared, '枯咗唔死團絨，清走得');
  const s3 = mk(); X.grant(s3, 15, 'dev', T0); B.plant(s3, 0, 'daisy', T0); B.water(s3, 0, T0); B.water(s3, 0, T0 + DAY);
  const bl3 = B.gardenTick(s3, T0 + 2 * DAY); ok(bl3.length === 1 && bl3[0].pts === 0, '日菊（燦光）：燦光唔喺 §7 分池 → 開花但冇分（報告：待遊策）');
  const s4 = mk(); X.grant(s4, 15, 'dev', T0); B.plant(s4, 2, 'firebell', T0 + 20 * 3600e3); B.water(s4, 2, T0 + 21 * 3600e3);
  ok(!B.potInfo(s4.sys12b.garden.pots[2], T0 + DAY + 3600e3).bloomed, '夜晚種：第 2 日未開');
}
console.log('③ 系統 4 散步收集＋收藏櫃');
{
  ok(C.walk.chance === 0.10 && C.walk.perDay === 5 && C.walk.slots === 30, '10%／每日 5 件／30 格');
  const keys = C.walk.items.map(i => i.k).sort().join(); ok(keys === 'acorn,cicada,clover,goldbulb,maple,marble,meteor,petal,snail,snowflake,snowman,sunflower', '小物＝遊美 ACC1 12 件（有圖）');
  const fs = require('fs'); ok(C.walk.items.every(i => ['16', '32', '16_sil', '32_sil'].every(z => fs.existsSync(__dirname + '/../art/collectibles/col_' + i.k + '_' + z + '.png'))), '12 件 16／32 px 圖＋剪影喺 art/collectibles/');
  const s = mk(), nov = { month: 11, hour: 11, hourOfDay: 11, weather: 'clear', prevWeather: 'clear', lead: null };
  let r = B.walkRoll(s, T0, Object.assign({}, nov, { rng: seq([0.99, 0.99, 0.5]) })); ok(r === null, '擲唔中（>10%）→ 冇');
  r = B.walkRoll(s, T0, Object.assign({}, nov, { rng: seq([0.99, 0.05, 0.0]) })); ok(r && ['maple', 'acorn'].includes(r.k) && r.first, '11 月 → 秋天小物（紅楓葉／橡果）', JSON.stringify(r));
  const elig = ctx => C.walk.items.filter(i => B.eligible(i, Object.assign({ dn: 0 }, ctx), B.st(mk()))).map(i => i.k).sort().join();
  ok(elig({ month: 4, hour: 7, hourOfDay: 7, weather: 'clear', prevWeather: 'clear' }) === 'clover,goldbulb,petal', '4 月晴天朝早：櫻花瓣（＋四葉草／金燈泡）', elig({ month: 4, hour: 7, hourOfDay: 7, weather: 'clear', prevWeather: 'clear' }));
  ok(elig({ month: 4, hour: 12, hourOfDay: 12, weather: 'rain', prevWeather: 'clear' }) === 'goldbulb,snail', '落雨：蝸牛殼');
  ok(elig({ month: 4, hour: 0, hourOfDay: 0.5, weather: 'clear', prevWeather: 'rain' }).split(',').includes('marble') && elig({ month: 4, hour: 1, hourOfDay: 1.5, weather: 'clear', prevWeather: 'rain' }).split(',').includes('snail') && !elig({ month: 4, hour: 3, hourOfDay: 3, weather: 'clear', prevWeather: 'rain' }).split(',').includes('snail'), '雨停後：玻璃珠（1h）／蝸牛殼（2h）');
  ok(elig({ month: 7, hour: 22, hourOfDay: 22, weather: 'overcast', prevWeather: 'clear' }) === 'goldbulb,meteor', '夏天夜晚陰天：流星碎（H4 夜）');
  ok(elig({ month: 1, hour: 12, hourOfDay: 12, weather: 'fog', prevWeather: 'clear' }) === 'goldbulb,snowflake', '冬天霧：雪花（雪人要連續 3 日上線）');
  const sm = mk(); [0, 1, 2].forEach(i => B.seen(sm, T0 + i * DAY)); ok(B.eligible(C.walk.items.find(i => i.k === 'snowman'), { month: 1, hour: 12, dn: X.dayNum(T0 + 2 * DAY), weather: 'clear' }, B.st(sm)), '連續 3 日上線 → 迷你雪人');
  const mt = C.walk.items.find(i => i.k === 'meteor'), night = { month: 7, hour: 22, hourOfDay: 22, weather: 'clear', prevWeather: 'clear' };
  r = B.walkRoll(mk(), T0, Object.assign({}, night, { lead: 'moon', rng: seq([0.015, 0.99, 0.99]) })); ok(r && r.k === 'meteor', '月眠領先 ×2：流星碎 1% → 2%');
  r = B.walkRoll(mk(), T0, Object.assign({}, night, { lead: 'ember', rng: seq([0.015, 0.99, 0.99]) })); ok(!r || r.k !== 'meteor', '非月眠 1%');
  const s5 = mk(); let got = 0; for (let i = 0; i < 9; i++) if (B.walkRoll(s5, T0 + i, Object.assign({}, nov, { rng: seq([0.99, 0.0, 0.0]) }))) got++;
  ok(got === 5 && B.walkRoll(s5, T0 + DAY, Object.assign({}, nov, { rng: seq([0.99, 0.0, 0.0]) })), '每日最多 5 件；第二日再執得');
  const s6 = mk(); B.st(s6).walk.total = 49; r = B.walkRoll(s6, T0, Object.assign({}, nov, { rng: seq([0.99, 0.0, 0.0]) })); ok(r && r.k === 'goldbulb' && r.pity, '累計第 50 件保底金燈泡');
  let hits = 0, hitsN = 0; const N = 40000, s7 = mk(), rr = S.makeRng(31337), exp = 1 - (1 - 0.01) * (1 - 0.002) * (1 - C.walk.chance);
  for (let i = 0; i < N; i++) { B.st(s7).walk.count = 0; if (B.walkRoll(s7, T0, Object.assign({}, nov, { rng: rr }))) hits++; if (B.walkRoll(s7, T0, Object.assign({}, nov, { rng: rr, noRare: true }))) hitsN++; }
  ok(Math.abs(hitsN / N - C.walk.chance) < 0.006, `普通小物機率 ≈ 10%（${(hitsN / N * 100).toFixed(2)}%）`);
  ok(Math.abs(hits / N - exp) < 0.006, `連稀有（11 月晴：四葉草 1%＋金燈泡 0.2%）≈ ${(exp * 100).toFixed(2)}%（${(hits / N * 100).toFixed(2)}%）`);
  const cab = B.cabinet(s5); ok(cab.slots.length === 30 && cab.slots.filter(x => x.locked).length === 18 && cab.slots.filter(x => !x.locked && !x.got).every(x => x.name === '？'), '收藏櫃 30 格剪影（18 格未有規格 → 鎖）');
  ok(B.walkRoll(mk('egg'), T0, Object.assign({}, nov, { rng: () => 0 })) === null, '光卵唔散步');
}
console.log('④ 系統 11 成就徽章');
{
  ok(C.badges.total === 30 && C.badges.list.length === 11 && C.badges.list.filter(b => b.when.dex).length === 9, '30 個徽章（規格列 11 個：第一次進化／9 條路／收藏 10 件）');
  ok(D.BRANCHES.every(id => C.badges.list.some(b => b.when.dex === id)), '9 條路徽章＝路線圖鑑 9 條');
  const s = mk('juvenile'); ok(B.badgeCheck(s, T0).length === 0, '幼年冇徽章');
  s.stage = 'adult'; let r = B.badgeCheck(s, T0); ok(r.length === 1 && r[0].k === 'first_evolve' && r[0].shards === C.badges.reward && B.badges(s).title === '第一次進化', '成為守夜者 → 第一次進化（星星碎＋稱號）', JSON.stringify(r));
  ok(B.badgeCheck(s, T0 + 1).length === 0, '唔重覆給');
  S.unlockDex(s, 'moon'); S.unlockDex(s, 'lumi'); r = B.badgeCheck(s, T0); ok(r.map(x => x.k).sort().join() === 'route_lumi,route_moon', '圖鑑解鎖 → 路線徽章');
  ok(X.wallet(s, T0).o === 15 && B.badges(s).pending === 0, '3 個 × 5 ＝ 15（其他上限）');
  S.unlockDex(s, 'tide'); r = B.badgeCheck(s, T0); ok(r[0].shards === 0 && B.badges(s).pending === 5, '爆上限 → pending 5');
  B.badgeCheck(s, T0 + DAY); ok(B.badges(s).pending === 0 && X.wallet(s, T0 + DAY).o === 5, '第二日補發');
  const s2 = mk(); B.st(s2).walk.got = Object.fromEntries(C.walk.items.slice(0, 10).map(i => [i.k, 1])); r = B.badgeCheck(s2, T0); ok(r.some(x => x.k === 'collect_10'), '收藏 10 件');
  const s3 = S.deserialize(S.serialize(s)), had = Object.keys(B.st(s3).badges.got); ok(had.length === 4 && B.badgeCheck(s3, T0 + 2 * DAY).every(x => !had.includes(x.k)), '存檔後唔重覆');
  const ev = mk('adult'); ev.ev = []; B.tick(ev, T0); ok(ev.ev.some(e => e.type === 'sys12' && e.sys === 'badge' && e.what === 'got'), '通知：sys12 badge 事件');
}
console.log('⑤ 經濟：第 2 批全部經 wallet → 每日總 ≤30');
{
  const s = mk('adult'); for (let i = 0; i < 10; i++) B.gameFinish(s, 'catch', 99, T0 + i); S.unlockDex(s, 'moon'); B.badgeCheck(s, T0);
  for (let q = 0; q < 30; q++) X.grant(s, 3, 'quest', T0);
  const w = X.wallet(s, T0); ok(w.today <= 30 && w.o <= 15 && w.q <= 15, `今日 ${w.today}（委託 ${w.q}＋其他 ${w.o}）`);
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
