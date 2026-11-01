/* systems12 第 2 批 Node 測試：node tests/systems12b.test.js
   系統 5 小遊戲 → 2 小圃種花 → 4 散步收集＋收藏櫃＋飾品 → 11 成就（docs-gdd/systems12-v1.md；數值＝docs-gdd/systems12b-params.md）。數值讀 PARAMS.systems12b。 */
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

console.log('⓪ 冇 TBD：第 2 批數值全部入 config');
{
  const src = require('fs').readFileSync(__dirname + '/../src/data.js', 'utf8'), a = src.indexOf('systems12b: {'), b = src.indexOf('systems12: {', a);
  ok(a > 0 && b > a && !/TBD/.test(src.slice(a, b)), 'PARAMS.systems12b 冇 TBD 標記');
  ok(!/TBD/.test(require('fs').readFileSync(__dirname + '/../src/systems2.js', 'utf8')), 'systems2.js 冇 TBD');
}
console.log('① 系統 5 小遊戲');
{
  const H = C.games.hide, K = C.games.catch;
  ok(C.games.dailyRewarded === 5 && K.durationSec === 30 && H.spots === 5 && H.rounds === 3 && H.triesPerRound === 3 && H.timeLimitSec <= 45, '接光點 30 秒；捉迷藏 5 位、3 回合、每回合 ≤3 下、≤45 秒；每日頭 5 局有獎');
  ok(K.dots.small === 1 && K.dots.big === 3 && K.dots.dark === -2 && K.bigStarProb === 0.10 && K.stoneProb === 0.15, '光點：普通 +1／金 +3（10%）／暗 −2（15%）');
  ok([0, 14, 15, 29, 30, 44, 45, 99].map(v => B.gameStars('catch', v)).join() === '0,0,1,1,2,2,3,3', '接光點：15／30／45 → 1／2／3★', [0, 14, 15, 29, 30, 44, 45, 99].map(v => B.gameStars('catch', v)).join());
  ok([0, 1, 3, 4, 6, 7, 9].map(v => B.gameStars('hide', v)).join() === '0,1,1,2,2,3,3', '捉迷藏：1／4／7 分 → 1／2／3★');
  const s = mk(); const mood0 = s.needs.mood, gr0 = s.grains, mg0 = s.stats.mgPlays, care0 = JSON.stringify(s.evo);
  const r = B.gameFinish(s, 'catch', 45, T0);
  ok(r.stars === 3 && r.shards === 3 && r.rewarded && X.wallet(s, T0).o === 3, '45 分 3★ → 3 星星碎（星星碎＝星數）', JSON.stringify(r));
  ok(s.needs.mood === mood0 && s.grains === gr0, '唔加心情／光粒（新系統唔加心情池）');
  ok(s.stats.mgPlays === mg0 + 1 && JSON.stringify(s.evo) !== care0 && r.counted, '計一局 mg（mgPlays＋noteCare mg → 火苗 +2）');
  const r0 = B.gameFinish(s, 'catch', 10, T0 + 1); ok(r0.stars === 0 && r0.shards === 0 && r0.rewarded && r0.counted, '未夠 15 分：0★＝0 星星碎（照計有獎局、照計 mg）');
  for (let i = 0; i < 3; i++) B.gameFinish(s, 'hide', 9, T0 + 2 + i);
  const r6 = B.gameFinish(s, 'hide', 9, T0 + 9);
  ok(!r6.rewarded && r6.shards === 0 && r6.counted && X.wallet(s, T0).o === 12, '第 6 局冇星星碎（照計 mg）；頭 5 局 3+0+3+3+3＝12', X.wallet(s, T0).o);
  const r7 = B.gameFinish(s, 'catch', 45, T0 + DAY); ok(r7.rewarded && r7.playIndex === 1, '第二日重新計');
  const e = mk('egg'); const re = B.gameFinish(e, 'catch', 45, T0); ok(!re.counted, '光卵：唔計 mg');
  const s2 = mk(); X.grant(s2, 14, 'dev', T0); const r8 = B.gameFinish(s2, 'catch', 45, T0); ok(r8.shards === 1, '經 wallet 其他上限 15（已有 14 → 只得 1）', r8.shards);
  const cp = B.catchParams(); ok(cp.durationSec === 30 && cp.starScore === 1 && cp.bigStarScore === 3 && cp.stonePenalty === 2 && cp.bigStarProb === 0.1 && cp.stoneProb === 0.15, '接光點 Minigame 覆寫參數');
  const m = new S.Minigame(5, cp); let n = 0; while (!m.over && n < 5000) { m.update(1 / 30, m.basketX); n++; }
  ok(m.over && Math.abs(m.t - 30) < 0.01 && m.M.durationSec === 30, '接光點 30 秒完場', m.t);
  const bot = sd => { const g = new S.Minigame(sd, cp); while (!g.over) { const tg = g.items.filter(i => i.type !== 'stone' && i.y < g.M.basketY).sort((a, b) => b.y - a.y)[0]; g.update(1 / 30, tg ? tg.x : g.basketX); } return g.score; };
  const sc = []; for (let sd = 1; sd <= 30; sd++) sc.push(bot(sd)); sc.sort((a, b) => a - b);
  ok(sc[sc.length - 1] >= 45 && sc[0] >= 15, `貪心 bot 30 局：最低 ${sc[0]}／中位 ${sc[15]}／最高 ${sc[29]}（3★ 拎得到，1★ 唔難）`);
  const m2 = new S.Minigame(5); ok(m2.M === P.mg && m2.M.durationSec === 45, '接星屑（舊）唔變：45 秒');
  // 捉迷藏
  const h = new B.HideGame(99); ok(h.spots.join() === H.spotNames.join() && h.spots.length === 5, '每回合 5 個固定位');
  let res = h.pick(h.at); ok(res.hit && res.pts === 3 && h.score === 3 && h.round === 1 && h.firstHits === 1, '第 1 下搵到 → 3 分');
  const o1 = (h.at + 1) % 5, o2 = (h.at + 2) % 5, o3 = (h.at + 3) % 5;
  res = h.pick(o1); ok(res.ok && !res.hit && !res.roundOver, '撳錯一下 → 仲有機會');
  res = h.pick(o1); ok(!res.ok, '同一個位唔可以再撳');
  res = h.pick(h.at); ok(res.hit && res.pts === 2 && h.score === 5, '第 2 下搵到 → 2 分');
  const at3 = h.at; h.pick((at3 + 1) % 5); h.pick((at3 + 2) % 5); res = h.pick((at3 + 3) % 5);
  ok(res.roundOver && !res.hit && res.over && h.score === 5 && h.found === 2, '3 下都唔中＝0 分（團絨自己行出嚟）→ 3 回合完場');
  const h3 = new B.HideGame(7); h3.pick((h3.at + 1) % 5); h3.pick((h3.at + 2) % 5); res = h3.pick(h3.at); ok(res.hit && res.pts === 1 && res.tryN === 3, '第 3 下搵到 → 1 分');
  const h2 = new B.HideGame(3); h2.update(46); ok(h2.over && h2.left === 0, '限時 45 秒');
  let tails = 0, NT = 0; for (let sd = 1; sd <= 3000; sd++) { const g = new B.HideGame(sd); for (let k = 0; k < 3; k++) { NT++; if (g.tail) tails++; g.pick(g.at); } }
  ok(Math.abs(tails / NT - 0.30) < 0.02, `露尾 ≈30%（${(tails / NT * 100).toFixed(1)}%）`);
  // 浮動團絨撳兩下＝一局 score 40＝2★
  const so = mk('juvenile'); so.ev = []; const mgp = so.stats.mgPlays; const ro = S.overlayOpenGame(so, T0);
  ok(ro.ok && ro.sys12b && ro.sys12b.stars === 2 && ro.sys12b.shards === 2 && so.stats.mgPlays === mgp + 1 && B.gamesToday(so, T0).plays === 1, '浮動撳兩下開 game：score 40＝2★（+2，計一局有獎；mg 只計一次）', JSON.stringify(ro.sys12b));
  ok(!S.overlayOpenGame(so, T0 + 1000).ok && B.gamesToday(so, T0).plays === 1, '浮動 cooldown 內唔重複計');
}
console.log('② 系統 2 小圃種花');
{
  ok(C.garden.pots === 3 && C.garden.flowers.length === 6 && C.garden.seedPrice === 6 && C.garden.bloomPts === 3 && C.garden.droopDryDays === 1 && C.garden.wiltDryDays === 2, '3 盆、6 種花；種子 6；開花 +3；1 日垂頭、2 日枯');
  ok(C.garden.flowers.map(f => f.name + f.route).join() === '藍鈴moon,日菊bright,苔菇shroom,晶草crystal,火鈴ember,露草tide', '花 → 路線');
  const s = mk(); let r = B.plant(s, 0, 'bluebell', T0); ok(!r.ok && r.reason === 'shards', '冇星星碎買唔到種子');
  X.grant(s, 15, 'dev', T0); r = B.plant(s, 0, 'bluebell', T0); ok(r.ok && X.wallet(s, T0).total === 9, '6 星星碎買一粒種子');
  ok(!B.plant(s, 0, 'daisy', T0).ok && !B.plant(s, 3, 'daisy', T0).ok && !B.plant(mk('egg'), 0, 'daisy', T0).ok, '有花／冇呢格／光卵 → 唔得');
  ok(B.potInfo(S.deserialize(S.serialize(s)).sys12b.garden.pots[0], T0).k === 'bluebell', '存檔保留');
  const pi = t => B.potInfo(s.sys12b.garden.pots[0], t);
  ok(pi(T0).stage === 0, '剛種：種子');
  ok(B.water(s, 0, T0).ok && !B.water(s, 0, T0 + 3600e3).ok && pi(T0).stage === 1, '淋水 → 即升芽；一日淋一次');
  ok(pi(T0 + DAY).stage === 1 && !pi(T0 + DAY).droop, '第 2 日未淋：仲係芽（未垂頭）');
  B.water(s, 0, T0 + DAY); ok(pi(T0 + DAY).stage === 2, '第 2 日淋 → 花苞');
  const b5 = () => JSON.stringify((s.evo.b5sys || {})[s.stage] || {});
  s.ev = []; r = B.water(s, 0, T0 + 2 * DAY); const I = pi(T0 + 2 * DAY);
  ok(I.bloomed && I.stage === 3 && r.bloom && r.bloom.route === 'moon' && r.bloom.pts === 3 && b5().includes('moon'), '第 3 次淋（第 2 日後）→ 開花，月眠 +3（addRoutePts，25% cap）＝最快 2 日', b5());
  ok(s.ev.some(e => e.sys === 'garden' && e.what === 'bloom' && e.pts === 3), '開花通知');
  ok(B.gardenTick(s, T0 + 3 * DAY).length === 0 && pi(T0 + 9 * DAY).bloomed, '路線分只加一次；開咗唔會枯');
  r = B.harvest(s, 0, T0 + 3 * DAY); ok(r.ok && r.vase && s.sys12b.garden.vase.bluebell === 1 && !s.sys12b.garden.pots[0], '開咗嘅花剪落花瓶（第 3 批房間擺）');
  B.plant(s, 1, 'firebell', T0); B.water(s, 1, T0);
  const q = t => B.potInfo(s.sys12b.garden.pots[1], t);
  ok(q(T0 + 2 * DAY).droop && q(T0 + 2 * DAY).stage === 1 && !q(T0 + 2 * DAY).wilted, '連續 1 日冇淋 → 垂頭（提示）');
  ok(B.water(s, 1, T0 + 2 * DAY).ok && !q(T0 + 2 * DAY).droop && q(T0 + 2 * DAY).stage === 2, '垂頭淋返水 → 冇事、升階');
  ok(q(T0 + 5 * DAY).wilted && q(T0 + 5 * DAY).stage === -1 && !B.water(s, 1, T0 + 5 * DAY).ok, '連續 2 日冇淋 → 枯，淋唔返');
  s.ev = []; const tot = X.wallet(s, T0).total; B.gardenTick(s, T0 + 5 * DAY);
  ok(!s.sys12b.garden.pots[1] && s.ev.some(e => e.what === 'wilt') && X.wallet(s, T0).total === tot && s.stage === 'juvenile' && !s.dead, '枯咗：花冇咗（清盆、種子唔退）；團絨冇事');
  const s3 = mk(); s3.ev = []; X.grant(s3, 15, 'dev', T0); B.plant(s3, 0, 'daisy', T0); B.water(s3, 0, T0); B.water(s3, 0, T0 + DAY);
  const w0 = X.wallet(s3, T0 + 2 * DAY).o, b50 = JSON.stringify(s3.evo.b5sys || {}); r = B.water(s3, 0, T0 + 2 * DAY);
  ok(r.bloom && r.bloom.pts === 0 && r.bloom.shards === 2 && X.wallet(s3, T0 + 2 * DAY).o === w0 + 2 && JSON.stringify(s3.evo.b5sys || {}) === b50, '日菊開花：+2 星星碎（照計上限）、冇路線分');
  ok(r.bloom.hint && r.bloom.hint.route === 'bright' && r.bloom.hint.text === D.ROUTE_HINT.bright && B.garden(s3, T0).hint[0].route === 'bright', '日菊：燦光圖鑑提示', JSON.stringify(r.bloom.hint));
  { const dl = S.dexList(s3).find(d => d.id === 'bright'); ok(s3.dexHint && s3.dexHint.bright && s3.dexHint.bright.src === 'daisy' && dl.hintRec === 'daisy' && !dl.unlocked && S.dexList(s3).filter(d => d.hintRec).length === 1, '日菊提示記入圖鑑燦光頁（未解鎖都記；淨係燦光）', JSON.stringify(dl));
    const t2 = S.deserialize(S.serialize(s3), T0 + 2 * DAY); ok(t2 && S.dexList(t2).find(d => d.id === 'bright').hintRec === 'daisy', '圖鑑提示記錄：存檔讀返仲喺度');
    const t3 = S.deserialize(JSON.stringify(Object.assign(JSON.parse(S.serialize(s3)), { dexHint: { bright: { src: 'daisy', t: 1 }, bogus: { src: 'x' } } })), T0); ok(Object.keys(t3.dexHint).join() === 'bright', '壞 key 清走');
    const old = mk(); B.st(old).garden.hint = {}; delete old.dexHint; old.sys12b.garden.hint = { bright: T0 }; B.st(old); ok(old.dexHint && old.dexHint.bright && old.dexHint.bright.src === 'daisy', '舊存檔：小圃已有燦光提示 → 補入圖鑑');
    const el = mk('elder'); el.form = 'tide'; el.fadeReady = true; el.dexHint = { bright: { src: 'daisy', t: T0 } }; S.fade(el, T0); ok(el.stage === 'egg' && el.dexHint.bright, '化光重養：圖鑑提示保留'); }
  const s4 = mk(); X.grant(s4, 15, 'dev', T0); B.plant(s4, 2, 'firebell', T0 + 11 * 3600e3); B.water(s4, 2, T0 + 12 * 3600e3); B.water(s4, 2, T0 + DAY + 3600e3);
  ok(!B.potInfo(s4.sys12b.garden.pots[2], T0 + DAY + 3600e3).bloomed && B.water(s4, 2, T0 + 2 * DAY).bloom, '每日最多升 1 階：夜晚種都要第 3 個淋水日先開（3 日內一定開）');
}
console.log('③ 系統 4 散步收集＋收藏櫃＋飾品');
{
  const W = C.walk, fs = require('fs');
  ok(W.chance === 0.10 && W.perDay === 5 && W.slots === 30 && W.items.length === 30, '10%／每日 5 件／30 格＝30 件');
  ok(new Set(W.items.map(i => i.name)).size === 30 && new Set(W.items.map(i => i.k)).size === 30, '30 件冇撞名');
  const ph = W.items.filter(i => i.ph); ok(ph.length === 18 && ph.filter(i => i.route).length === 9 && ph.filter(i => !i.route).length === 9, '補 18 件：9 件路線限定＋9 件天氣／季節／時段（佔位 icon）');
  ok(D.BRANCHES.every(f => W.items.some(i => i.route === f)), '9 條路線各 1 件');
  ok(W.items.every(i => ['16', '32', '16_sil', '32_sil'].every(z => fs.existsSync(__dirname + '/../art/collectibles/col_' + i.k + '_' + z + '.png'))), '30 件 16／32 px 圖＋剪影（18 件佔位）喺 art/collectibles/');
  const E = (ctx, st) => W.items.filter(i => B.eligible(i, Object.assign({ dn: 0, form: null }, ctx), B.st(st || mk()))).map(i => i.k).sort().join();
  const has = (ctx, k) => E(ctx).split(',').includes(k);
  ok(E({ month: 4, hour: 12, hourOfDay: 12, weather: 'clear', prevWeather: 'clear' }) === 'clover,goldbulb,petal,sakurabud,seedhusk', '4 月晴天中午：櫻花瓣、櫻花蕾、種子殼（＋四葉草／金燈泡）', E({ month: 4, hour: 12, hourOfDay: 12, weather: 'clear', prevWeather: 'clear' }));
  ok(E({ month: 4, hour: 7, hourOfDay: 7, weather: 'rain', prevWeather: 'clear' }) === 'dewleaf,goldbulb,raindrop,sakurabud,snail', '落雨清早：蝸牛殼、雨滴石、露葉、櫻花蕾', E({ month: 4, hour: 7, hourOfDay: 7, weather: 'rain', prevWeather: 'clear' }));
  ok(has({ month: 4, hour: 0, hourOfDay: 0.5, weather: 'clear', prevWeather: 'rain' }, 'marble') && has({ month: 4, hour: 1, hourOfDay: 1.5, weather: 'clear', prevWeather: 'rain' }, 'snail') && !has({ month: 4, hour: 3, hourOfDay: 3, weather: 'clear', prevWeather: 'rain' }, 'snail'), '雨停後：玻璃珠（1h）／蝸牛殼（2h）');
  ok(E({ month: 7, hour: 22, hourOfDay: 22, weather: 'overcast', prevWeather: 'clear' }) === 'cicadawing,glowstone,goldbulb,meteor', '夏天夜晚陰天：蟬翼、螢光石、流星碎');
  ok(has({ month: 1, hour: 2, hourOfDay: 2, weather: 'fog', prevWeather: 'clear' }, 'glowstone') && !has({ month: 1, hour: 3, hourOfDay: 3, weather: 'fog', prevWeather: 'clear' }, 'glowstone') && has({ month: 1, hour: 3, hourOfDay: 3, weather: 'fog', prevWeather: 'clear' }, 'fogbead') && has({ month: 1, hour: 3, hourOfDay: 3, weather: 'fog', prevWeather: 'clear' }, 'icicle'), '螢光石 20:00–03:00；霧珠（霧）；冰凌（冬）');
  ok(has({ month: 10, hour: 6, hourOfDay: 6, weather: 'overcast', prevWeather: 'clear' }, 'dewleaf') && !has({ month: 10, hour: 9, hourOfDay: 9, weather: 'overcast', prevWeather: 'clear' }, 'dewleaf') && has({ month: 10, hour: 9, hourOfDay: 9, weather: 'overcast', prevWeather: 'clear' }, 'ginkgo'), '露葉 06–09；銀杏葉（秋）');
  const sm = mk(); [0, 1, 2].forEach(i => B.seen(sm, T0 + i * DAY)); ok(B.eligible(W.items.find(i => i.k === 'snowman'), { month: 1, hour: 12, dn: X.dayNum(T0 + 2 * DAY), weather: 'clear' }, B.st(sm)), '連續 3 日上線 → 迷你雪人');
  const nov = { month: 11, hour: 11, hourOfDay: 11, weather: 'overcast', prevWeather: 'clear', lead: null };
  const ad = mk('adult'); ad.form = 'tide'; let cx = B.walkCtx(ad, T0, nov); ok(cx.form === 'tide' && B.eligible(W.items.find(i => i.k === 'dewglass'), cx, B.st(ad)) && !B.eligible(W.items.find(i => i.k === 'mushcap'), cx, B.st(ad)), '守夜者水珠 → 露珠玻璃（其他路線唔得）');
  const ju = mk('juvenile'); ju.form = 'tide'; ok(B.walkCtx(ju, T0, nov).form === null, '守夜者之前冇路線限定');
  const lu = mk('elder'); lu.form = 'lumi'; const gp = W.items.find(i => i.k === 'glowpowder');
  ok(B.eligible(gp, B.walkCtx(lu, T0, Object.assign({}, nov, { hour: 22 })), B.st(lu)) && !B.eligible(gp, B.walkCtx(lu, T0, nov), B.st(lu)), '螢光粉：螢絨＋淨係夜晚');
  { const gs = W.items.find(i => i.k === 'glowstone'), at = (it, h) => B.eligible(it, B.walkCtx(lu, T0, Object.assign({}, nov, { hour: h, hourOfDay: h })), B.st(lu));
    const hrs = [17, 19, 20, 23, 0, 2, 3, 6, 7], pat = hrs.map(h => +at(gp, h)).join('') + '/' + hrs.map(h => +at(gs, h)).join('');
    ok(pat === '001111000/001111000', '螢光粉＋螢光石：夜晚＝20:00–03:00（17／19 唔得、3 點唔得）', pat);
    const mw = P.evo6.branch.windows.find(w => w.id === 'moon');
    ok(W.nightHours.join() === [mw.from, mw.to].join() && gp.night && gs.night && !gp.hours && !gs.hours, 'walk.nightHours＝月眠時段（20–03），兩件小物都讀呢個 key');
    ok(P.evo6.nightFrom === 17 && P.evo6.nightTo === 7, '螢絨進化夜晚 key 唔變（evo6.nightFrom／nightTo＝17–07）'); }
  const s = mk();
  let r = B.walkRoll(s, T0, Object.assign({}, nov, { rng: seq([0.10, 0.0]) })); ok(r === null, '擲唔中（≥10%）→ 冇');
  r = B.walkRoll(s, T0, Object.assign({}, nov, { rng: seq([0.05, 0.99, 0.0]) })); ok(r && ['maple', 'acorn', 'ginkgo'].includes(r.k) && r.first, '11 月 → 秋天小物', JSON.stringify(r));
  const night = { month: 7, hour: 22, hourOfDay: 22, weather: 'clear', prevWeather: 'clear' };
  r = B.walkRoll(mk(), T0, Object.assign({}, night, { lead: 'moon', rng: seq([0.05, 0.15, 0.99]) })); ok(r && r.k === 'meteor', '月眠領先 ×2：流星碎 1% → 2%（10% 入面條件 20%）');
  r = B.walkRoll(mk(), T0, Object.assign({}, night, { lead: 'ember', rng: seq([0.05, 0.15, 0.99, 0.99]) })); ok(r && r.k !== 'meteor', '非月眠 1%');
  const s5 = mk(); let got = 0; for (let i = 0; i < 9; i++) if (B.walkRoll(s5, T0 + i, Object.assign({}, nov, { rng: seq([0.0, 0.99, 0.0]) }))) got++;
  ok(got === 5 && B.walkRoll(s5, T0 + DAY, Object.assign({}, nov, { rng: seq([0.0, 0.99, 0.0]) })), '每日最多 5 件；第二日再執得');
  const s6 = mk(); B.st(s6).walk.total = 49; r = B.walkRoll(s6, T0, Object.assign({}, nov, { rng: seq([0.0, 0.99, 0.0]) })); ok(r && r.k === 'goldbulb' && r.pity, '累計第 50 件保底金燈泡');
  let hits = 0, rare = 0; const N = 60000, s7 = mk(), rr = S.makeRng(31337), clr = Object.assign({}, nov, { weather: 'clear' });
  for (let i = 0; i < N; i++) { B.st(s7).walk.count = 0; const x = B.walkRoll(s7, T0, Object.assign({}, clr, { rng: rr })); if (x) { hits++; if (W.items.find(it => it.k === x.k).rare) rare++; } }
  ok(hits / N <= 0.10 + 0.004 && Math.abs(hits / N - 0.10) < 0.004, `總執到率 ≤10%（含稀有；${(hits / N * 100).toFixed(2)}%）`);
  ok(Math.abs(rare / N - 0.012) < 0.002, `稀有絕對機率（11 月晴：四葉草 1%＋金燈泡 0.2%）≈1.2%（${(rare / N * 100).toFixed(2)}%）`);
  // 飾品
  ok(W.accPer === 5 && W.accessories.map(a => a.name).join() === '葉帽,露珠頸鏈,小眼鏡,披肩,蝴蝶結,星星髮夾', '湊 5 解鎖飾品：6 件');
  const sa = mk(); sa.ev = []; const Wg = B.st(sa).walk; W.items.slice(0, 4).forEach(i => { Wg.got[i.k] = 1; });
  B.walkRoll(sa, T0, Object.assign({}, nov, { rng: seq([0.0, 0.99, 0.0]) })); B.st(sa).walk.got.maple = 1;
  const a1 = B.accCheck(sa); const acc = B.accessories(sa);
  ok(acc.filter(a => a.got).length === 1 && acc[0].got && acc[0].name === '葉帽' && sa.ev.some(e => e.sys === 'walk' && e.what === 'acc'), '5 件唔同小物 → 葉帽（通知）', JSON.stringify(acc.map(a => a.got)));
  W.items.forEach(i => { Wg.got[i.k] = 2; }); B.accCheck(sa); ok(B.accessories(sa).every(a => a.got) && B.st(sa).walk.acc === 6, '30 件 → 6 件飾品全解鎖');
  const cab = B.cabinet(s5); ok(cab.slots.length === 30 && cab.slots.filter(x => x.locked).length === 0 && cab.slots.filter(x => x.ph).length === 18 && cab.slots.filter(x => !x.got).every(x => x.name === '？') && cab.acc.length === 6, '收藏櫃 30 格剪影（18 格佔位 icon）＋飾品列');
  ok(B.walkRoll(mk('egg'), T0, Object.assign({}, nov, { rng: () => 0 })) === null, '光卵唔散步');
}
console.log('④ 系統 11 成就徽章（30 個）');
{
  const L = C.badges.list; ok(C.badges.total === 30 && L.length === 30 && new Set(L.map(b => b.k)).size === 30, '30 個徽章、冇重覆');
  ok(D.BRANCHES.every(id => L.some(b => b.when.dex === id)), '9 條路徽章＝路線圖鑑 9 條');
  ok(C.badges.reward === 5 && C.badges.bigReward === 10 && L.filter(b => b.big).map(b => b.k).join() === 'routes_all,collect_30' && L.filter(b => b.big).every(b => b.title), '一般 5；大成就（9 條路齊／收藏 30 件）10＋稱號');
  ok(L.filter(b => b.title).map(b => b.title).sort().join() === ['自稱天才飼主', '雲朵研究員', '執屎專家', '收藏界權威', '園藝大師（自封）', '夜貓哄瞓師'].sort().join(), '6 個稱號＝遊策清單');
  const e = mk('egg'); ok(B.badgeCheck(e, T0).length === 0, '光卵冇徽章');
  const s = mk('newborn'); let r = B.badgeCheck(s, T0); ok(r.length === 1 && r[0].k === 'first_evolve' && r[0].shards === 5, '孵化成初生 → 第一次進化（新手第一個）', JSON.stringify(r));
  ok(B.badgeCheck(s, T0 + 1).length === 0, '唔重覆給');
  s.stage = 'adult'; S.unlockDex(s, 'moon'); r = B.badgeCheck(s, T0); ok(r.map(x => x.k).sort().join() === 'first_variant,route_moon', '第一次到守夜者 → 第一次變種＋月眠圖鑑');
  const w0 = X.wallet(s, T0); ok(w0.total === 15 && w0.today === 0 && w0.o === 0, '徽章星星碎直接入錢包，唔計每日上限（今日計數 0）', JSON.stringify(w0));
  X.grant(s, 15, 'dev', T0); X.grant(s, 15, 'quest', T0); S.unlockDex(s, 'lumi'); r = B.badgeCheck(s, T0);
  ok(r[0].shards === 5 && X.wallet(s, T0).total === 50 && X.wallet(s, T0).today === 30, '今日上限 30 爆咗都照發徽章（一次性）');
  ok(X.st(s).wallet.log.filter(l => l.src === 'badge').length === 4, '錢包 log src＝badge');
  D.BRANCHES.forEach(f => S.unlockDex(s, f)); r = B.badgeCheck(s, T0); const big = r.find(x => x.k === 'routes_all');
  ok(big && big.shards === 10 && big.title === '自稱天才飼主' && B.badges(s).title === '自稱天才飼主' && r.length === 8, '9 條路齊（大）→ 10＋稱號「自稱天才飼主」');
  const s2 = mk(); const Wg = B.st(s2).walk; C.walk.items.slice(0, 10).forEach(i => { Wg.got[i.k] = 1; }); r = B.badgeCheck(s2, T0).map(x => x.k); ok(r.includes('collect_10') && !r.includes('collect_20'), '收藏 10 件');
  C.walk.items.forEach(i => { Wg.got[i.k] = 1; }); B.accCheck(s2); r = B.badgeCheck(s2, T0); ok(['collect_20', 'collect_30', 'acc_all'].every(k => r.some(x => x.k === k)) && r.find(x => x.k === 'collect_30').shards === 10 && B.badges(s2).titles.includes('收藏界權威'), '收藏 20／30（大＋稱號「收藏界權威」）／全部飾品');
  // 其他條件
  const c = mk(); const T = B.st(c).stats;
  c.careDays = ['2026-11-01', '2026-11-02', '2026-11-04', '2026-11-05', '2026-11-06']; ok(B.careStreak(c) === 3 && B.met(c, { careStreak: 3 }) && !B.met(c, { careStreak: 7 }), '連續照顧 3 日（斷咗重計）');
  c.careDays = Array.from({ length: 8 }, (_, i) => S.dayKey(T0 + i * DAY)); ok(B.met(c, { careStreak: 7 }), '連續照顧 7 日');
  c.stage = 'juvenile'; c.needs.energy = 10; c.sleeping = false; const lr = S.lullSleep(c); ok(lr.ok && T.lull === 1 && B.met(c, { lull: 1 }), '哄瞓成功 → 第一次哄瞓成功（care hook）', JSON.stringify(lr));
  for (let i = 0; i < 2; i++) { c.sleeping = false; c.needs.energy = 10; S.lullSleep(c); } ok(T.lullNight === 3 && B.met(c, { lullNight: 3 }), '一晚哄瞓 3 次', T.lullNight);
  T.quick = 9; ok(!B.met(c, { quick: 10 }) && (T.quick++, B.met(c, { quick: 10 })), '即清 10 次（poopQuick hook 計數）');
  ok(B.met(c, { quick: 1 }), '第一次即清便便');
  B.gameFinish(c, 'catch', 50, T0); ok(B.met(c, { catchStars: 3 }), '接光點 3★');
  B.gameFinish(c, 'hide', 3, T0, { firstHits: 1 }); ok(B.met(c, { hideFirst: 1 }), '捉迷藏一次就搵到');
  B.st(c).garden.bloomed = { bluebell: 1, daisy: 1, mossshroom: 1, crystalgrass: 1, firebell: 1 }; ok(!B.met(c, { bloomKinds: 6 }) && (B.st(c).garden.bloomed.dewgrass = 1, B.met(c, { bloomKinds: 6 })), '開齊 6 種花');
  X.st(c).quests.paidN = 10; ok(B.met(c, { quests: 10 }) && !B.met(c, { quests: 50 }), '完成 10 次委託（systems.payItem 累計 paidN）');
  B.st(c).wx = { clear: 1, rain: 1, fog: 1 }; ok(!B.met(c, { weathers: 4 }) && (B.st(c).wx.overcast = 1, B.met(c, { weathers: 4 })), '遇到 4 種天氣');
  X.st(c).diary.list = Array.from({ length: 7 }, (_, i) => ({ d: S.dayKey(T0 + i * DAY), lines: ['x'], gen: 1 })); ok(B.met(c, { diary: 7 }), '寫滿 7 篇日記');
  ok(!B.met(c, { fade: 1 }) && (c.gen = 2, B.met(c, { fade: 1 })), '化光一次（新一代）');
  const qd = mk(); X.genQuests && X.questTick && (X.questTick(qd, T0)); const ql = X.st(qd).quests.list; if (ql.length) { ql[0].n = ql[0].need; X.payItem(qd, ql[0], T0, null); }
  ok(!ql.length || X.st(qd).quests.paidN === 1, '委託發錢 → paidN +1');
  const s3 = S.deserialize(S.serialize(s)), had = Object.keys(B.st(s3).badges.got); ok(had.length >= 12 && B.badgeCheck(s3, T0 + 2 * DAY).every(x => !had.includes(x.k)), '存檔後唔重覆');
  const old = mk('newborn'); B.st(old).badges.pending = 5; B.badgeCheck(old, T0); ok(B.st(old).badges.pending === 0 && X.wallet(old, T0).total === 10, '舊版待補發 → 一次過入錢包');
  const ev = mk('adult'); ev.ev = []; B.tick(ev, T0); ok(ev.ev.some(e => e.type === 'sys12' && e.sys === 'badge' && e.what === 'got'), '通知：sys12 badge 事件');
}
console.log('⑤ 經濟：每日（唔計徽章）≤30；徽章一次性另計');
{
  const s = mk('adult'); for (let i = 0; i < 10; i++) B.gameFinish(s, 'bounce', 99, T0 + i);   // 徽章「彈彈葉 3★」只計彈彈葉
  for (let q = 0; q < 30; q++) X.grant(s, 3, 'quest', T0);
  X.grant(s, 2, 'garden', T0); S.unlockDex(s, 'moon'); B.badgeCheck(s, T0);
  const w = X.wallet(s, T0), bad = X.st(s).wallet.log.filter(l => l.src === 'badge').reduce((a, l) => a + l.n, 0);
  ok(w.today === 30 && w.o === 15 && w.q === 15 && bad === 20 && w.total >= 50, `今日 ${w.today}（委託 ${w.q}＋其他 ${w.o}）＋徽章 ${bad}（唔計上限）`);
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
