/* 小遊戲 v2（docs-gdd/minigames-v2.md）：node tests/minigames2.test.js
   彈彈葉／花園捉迷藏（重做）／追螢火（夜晚限定）邏輯＋每局 2 變化＋團絨反應＋獎勵經 systems2.gameFinish（錢包／每日上限）。 */
const D = require('../src/data.js'), S = require('../src/sim.js'), X = require('../src/systems.js'), B = require('../src/systems2.js');
const M = require('../src/minigames2.js'), BOT = require('./mg2-bots.js');
const P = D.PARAMS.systems12b, G2 = D.PARAMS.minigames2, R = G2.reactions;
let pass = 0, fail = 0;
function ok(c, n, i) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? '  → ' + JSON.stringify(i) : '')); } }
const T0 = new Date(2026, 10, 2, 21, 0).getTime();
const run = (g, sec, f) => { for (let i = 0; i < Math.round(sec * 60); i++) { if (f) f(g, i); g.update(1 / 60); } };
// 設定／旗
ok(P.games.v1Enabled === false, '舊接光點／舊捉迷藏：games.v1Enabled=false（config 閂，code 保留）');
ok(JSON.stringify(G2.order) === '["bounce","ghide","firefly"]', 'v2 三隻：彈彈葉／花園捉迷藏／追螢火（冇 2、4）');
ok(['bounce', 'ghide', 'firefly'].every(k => (G2[k].durationSec || G2[k].timeLimitSec) <= 45), '每局 ≤45 秒（規格）');
// 變化
{
  let okAll = true, seen = {};
  for (const k of G2.order) for (let sd = 1; sd <= 120; sd++) { const g = M.create(k, sd), cats = g.mods.map(m => m.cat); if (g.mods.length !== 2 || new Set(cats).size !== 2 || !g.mods.every(m => G2[k].mods[m.cat][m.k])) okAll = false; g.mods.forEach(m => { seen[k + ':' + m.k] = 1; }); }
  ok(okAll, '每局 2 個變化：3 類（天氣／速度／特別物）揀 2 類、每類 1 個');
  const all = G2.order.reduce((n, k) => n + Object.values(G2[k].mods).reduce((a, c) => a + Object.keys(c).length, 0), 0);
  ok(Object.keys(seen).length === all, '120 局內每個變化都出過（' + all + ' 個）', Object.keys(seen));
  ok(JSON.stringify(M.create('bounce', 9).mods) === JSON.stringify(M.create('bounce', 9).mods), '同 seed 同變化（可重播）');
  ok(JSON.stringify(M.create('bounce', 9, { mods: ['wind', 'gold'] }).mods) === '[{"cat":"weather","k":"wind"},{"cat":"special","k":"gold"}]', 'QA 可指定變化');
}
// 反應 clip 全部係現有 clip（evo atlas）
{
  const fs = require('fs'), path = require('path'), dir = path.join(__dirname, '../art/evo6'), files = fs.readdirSync(dir).filter(f => /^atlas_evo_.*\.json$/.test(f));
  const clips = new Set(); files.forEach(f => { const j = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')); Object.keys(j.clips || j.animations || {}).forEach(c => clips.add(c)); });
  const miss = Object.values(R).filter(c => !clips.has(c));
  ok(files.length > 0 && miss.length === 0, '團絨反應全部用現有 clip（' + Object.values(R).length + ' 個；atlas ' + files.length + '）', miss);
}
// 1 彈彈葉
{
  const g = M.create('bounce', 3, { mods: ['slow', 'bigleaf'] }), L = G2.bounce.leaf;
  ok(g.phase === 'ready' && g.pet.x === L.x && g.pet.y === L.y, '開局團絨企喺葉片');
  g.press(L.x, L.y); run(g, 0.45); ok(g.phase === 'charge' && g.power > 0.4 && g.power < 0.6 && g.clip === R.charge, '撳住儲力（0.45s ≈ 50%）＋儲力反應', { p: g.power, c: g.clip });
  run(g, 1); ok(g.power === 1 && g.bend === 1, '儲滿 = 1（葉片彎到盡）');
  g.release(); ok(g.phase === 'air' && g.pet.vy < 0 && g.flipping, '放手彈起；滿力 → 自信翻筋斗');
  run(g, 0.3); ok(g.flip > 0 && g.pet.y < L.y - 40, '半空翻緊');
  const x0 = g.pet.x; g.move(20, 0); run(g, 0.3); ok(g.pet.x < x0 - 15, '半空左右拖（追手指 x）', { x0, x: g.pet.x });
  run(g, 3, (gg) => gg.move(170, 0)); ok(g.falls === 1 && ['fallen', 'walk'].includes(g.phase), '跌出葉外 → 跌低', { ph: g.phase, f: g.falls });
  const g2 = M.create('bounce', 3, { mods: ['slow', 'bigleaf'] }); g2.press(L.x, L.y); run(g2, 1); g2.release(); let clips = new Set(); run(g2, 4.5, (gg) => { gg.move(170, 0); clips.add(gg.clip); });
  ok(clips.has(R.fall) && clips.has(R.getup) && clips.has(R.cool), '跌低 → 起身 → 扮冇事（droop→getup→act_cool）', [...clips]);
  run(g2, 2); ok(g2.phase === 'ready' && g2.pet.x === L.x, '自己行返葉片');
  const g3 = M.create('bounce', 4, { mods: ['fast', 'gold'] }); g3.dots = [{ x: L.x, y: 200, gold: false, ph: 0 }, { x: L.x, y: 150, gold: true, ph: 0 }]; g3.press(L.x, L.y); run(g3, 0.6); g3.release(); let pc = false; run(g3, 2.5, gg => { gg.move(L.x, 0); if (gg.clip === R.proud) pc = true; });
  ok(g3.score >= 4 && g3.fx.some(f => f.type === 'gold'), '掂光點 +1、金光點 +3', { s: g3.score });
  ok(g3.lands === 1 && pc, '一跳 ≥2 粒 → 落返葉 → 得意（smug_pose）');
  const gw = M.create('bounce', 5, { mods: ['wind', 'fast'] }); ok(Math.abs(gw.windAx) === G2.bounce.mods.weather.wind.ax, '風向變化（左或右）');
  const gr = M.create('bounce', 5, { mods: ['rain', 'gold'] }); ok(gr.cloud && gr.cloud.w > 0, '雨雲變化（會郁）');
  const gb = M.create('bounce', 5, { mods: ['rain', 'bigleaf'] }); ok(gb.leafW > G2.bounce.leaf.w, '大葉變化');
  const gt = M.create('bounce', 6); run(gt, 41); ok(gt.over && gt.t === G2.bounce.durationSec, '時間到完局');
}
// 3 花園捉迷藏
{
  const g = M.create('ghide', 11, { mods: ['fog', 'calm'] });
  ok(g.covers.length === G2.ghide.covers && g.covers.every(c => G2.ghide.coverTypes.includes(c.type)), '5 個遊遮擋物（花盆／葉堆／石頭／草叢／燈籠）');
  const pos0 = JSON.stringify(g.covers.map(c => [c.x, c.y, c.type]));
  const wrong = g.covers.findIndex((c, i) => i !== g.at); const r1 = g.pick(wrong);
  ok(r1.ok && !r1.hit && g.covers[wrong].shake > 0 && g.tries === 2, '撳錯＝搖嗰樣嘢、少一次機會');
  const r2 = g.pick(g.at); ok(r2.hit && r2.pts === 2 && g.phase === 'reveal', '第 2 下搵到 = 2 分');
  let cl = new Set(); run(g, 1.6, gg => cl.add(gg.clip)); ok(cl.has(R.surprised) && cl.has(R.cool), '搵到 → 嚇一跳 → 扮冇事行出嚟', [...cl]);
  ok(g.round === 1 && JSON.stringify(g.covers.map(c => [c.x, c.y, c.type])) !== pos0, '下一回合：位置＋遮擋物換晒');
  const at0 = g.at, sn = g.sneaks; run(g, G2.ghide.mods.speed.calm.sneakSec + 0.1); ok(g.sneaks === sn + 1 && g.at !== at0, '太慢冇撳 → 佢偷偷轉位', { at0, at: g.at });
  const gs = M.create('ghide', 12, { mods: ['wind', 'sneaky'] }); ok(gs.sneakSec === G2.ghide.mods.speed.sneaky.sneakSec, '鬼祟變化：更快轉位');
  const ge = M.create('ghide', 12, { mods: ['fog', 'extra'] }); ok(ge.covers.length === 6, '多一個遮擋物變化');
  const gt = M.create('ghide', 13, { mods: ['fog', 'bulb'] }); ok(gt.tailChance === G2.ghide.mods.special.bulb.tailChance && gt.peekA < 1, '燈泡變化（易露）＋霧（露得淡）');
  let peeked = false; for (let sd = 1; sd < 30 && !peeked; sd++) { const gg = M.create('ghide', sd, { mods: ['wind', 'bulb'] }); if (gg.tail) { run(gg, 4, x => { if (x.peeking) peeked = true; }); } } ok(peeked, '間中露尾／燈泡');
  const gm = M.create('ghide', 14, { mods: ['fog', 'calm'] }); let cl2 = new Set(); [0, 1, 2, 3, 4].filter(i => i !== gm.at).slice(0, 3).forEach(i => gm.pick(i)); run(gm, 1, x => cl2.add(x.clip)); ok(cl2.has(R.proud) && gm.score === 0, '3 下都撳錯 → 團絨得意出嚟（0 分）');
  const gf = M.create('ghide', 15, { mods: ['fog', 'calm'] }); for (let r = 0; r < 3; r++) { gf.pick(gf.at); run(gf, 1.6); } ok(gf.over && gf.score === 9 && gf.firstHits === 3 && gf.stars === 3, '3 回合都第 1 下搵到 = 9 分 3★', { s: gf.score });
}
// 5 追螢火
{
  ok(M.fireflyOpen(21) && M.fireflyOpen(3) && !M.fireflyOpen(12) && M.fireflyOpen(17) && !M.fireflyOpen(7), '夜晚限定：' + G2.firefly.nightHours.join('–') + ' 點');
  const g = M.create('firefly', 21, { mods: ['breeze', 'dash'] }); g.branches = []; g.flies = [{ x: 90, y: 180, vx: 0, vy: 0, ph: 0, gold: false }];
  g.press(90, 270); for (let y = 266; y >= 170; y -= 6) g.move(90, y); g.release(); ok(g.path.length > 10, '手指畫路');
  run(g, 1.2); ok(g.caught >= 1 && g.score >= 1, '團絨跟住條路走、捉到螢火 +1', { s: g.score, p: g.pet });
  const g2 = M.create('firefly', 22, { mods: ['mist', 'sleepy'] }); g2.flies = []; g2.branches = [{ x1: 60, y1: 220, x2: 120, y2: 220 }];
  g2.press(90, 270); for (let y = 266; y >= 150; y -= 6) g2.move(90, y); g2.release(); let cl = new Set(); run(g2, 1.6, x => cl.add(x.clip));
  ok(g2.bumps === 1 && g2.path.length === 0 && cl.has(R.bump) && cl.has(R.cool), '撞樹枝 → 停低、條路清咗、扮冇痛（pot_bump→act_cool）', { b: g2.bumps, cl: [...cl] });
  ok(g2.pet.y > 220, '撞到唔會穿過樹枝');
  const gl = M.create('firefly', 23, { mods: ['mist', 'thicket'] }); ok(gl.branches.length === G2.firefly.branches + 2, '樹叢變化：多 2 枝');
  const gd = M.create('firefly', 23, { mods: ['breeze', 'dash'] }); ok(gd.spd === 1.3 && gd.driftMul > 1, '衝刺＋微風變化');
  const gp = M.create('firefly', 24); gp.press(10, 300); for (let i = 0; i < 400; i++) gp.move(10 + (i % 2) * 160, 300 - i); ok(gp.pathLen <= G2.firefly.maxPath, '路長上限 ' + G2.firefly.maxPath);
}
// bot：有技術差＋星數分佈
{
  for (const k of G2.order) {
    const lo = [], hi = []; const r = S.makeRng(77);
    for (let i = 0; i < 40; i++) { lo.push(BOT.playBot(M, k, 500 + i, 0, r).score); hi.push(BOT.playBot(M, k, 900 + i, 0.6, r).score); }
    const med = a => a.slice().sort((x, y) => x - y)[a.length >> 1], hs = hi.map(v => M.stars(k, v));
    ok(med(hi) > med(lo) && hs.filter(s => s >= 1).length >= 30 && hs.filter(s => s === 3).length < 40, k + '：熟手 bot 分數 > 亂撳（' + med(lo) + '→' + med(hi) + '），有星又唔係全 3★');
  }
}
// 獎勵：經 systems2.gameFinish（錢包＋每日上限共用）
{
  const s = S.newState(T0, 5); s.stage = 'juvenile'; X.st(s);
  const w0 = X.st(s).wallet.total, mg0 = s.mg ? JSON.stringify(s.mg) : '';
  const r = B.gameFinish(s, 'bounce', 22, T0, {}); ok(r.stars === 2 && r.shards === 2 && X.st(s).wallet.total >= w0 + 2, '彈彈葉 22 分 = 2★ = 2 碎入錢包（錢包 grant）', r);
  const r2 = B.gameFinish(s, 'ghide', 9, T0, { firstHits: 3 }); ok(r2.stars === 3 && B.st(s).games.hideFirst === 3, '花園捉迷藏 firstHits → 成就計數');
  const r3 = B.gameFinish(s, 'firefly', 30, T0, {}); ok(r3.stars === 3 && r3.counted !== undefined, '追螢火 3★；計 mg（火苗）');
  B.gameFinish(s, 'bounce', 40, T0); B.gameFinish(s, 'bounce', 40, T0); const r6 = B.gameFinish(s, 'bounce', 40, T0);
  ok(!r6.rewarded && r6.shards === 0, '第 ' + (P.games.dailyRewarded + 1) + ' 局冇碎（每日 ' + P.games.dailyRewarded + ' 局上限，舊新共用）');
  ok(B.st(s).games.stars.bounce === 3 && (B.badgeCheck ? true : true), '最佳星數記錄');
  let threw = false; try { B.gameFinish(s, 'xxx', 1, T0); } catch (e) { threw = true; } ok(threw, '未知 kind 照拒');
}
console.log((fail ? '✗' : '✓') + ' minigames2: ' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
