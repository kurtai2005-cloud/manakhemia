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
  ok(JSON.stringify(M.create('bounce', 9, { mods: ['wind', 'gold'] }).mods.map(m => [m.cat, m.k, m.hard])) === '[["weather","wind",true],["special","gold",false]]', 'QA 可指定變化');
  { let bad = 0, sOk = true, n = 0, easyOnly = 0; for (const k of G2.order) for (let sd = 1; sd <= 600; sd++) { const g = M.create(k, sd), h = g.mods.filter(m => m.hard); n++; if (h.length > G2.maxHard) bad++; if (!h.length) easyOnly++; h.forEach(m => { if (m.s < 0.2 || m.s > 0.25) sOk = false; }); g.mods.filter(m => !m.hard).forEach(m => { const d = G2[k].mods[m.cat][m.k]; if (!['gold', 'time', 'sneak'].includes(d.easy)) sOk = false; }); }
    ok(bad === 0, '最多 1 個難（' + n + ' 局）'); ok(sOk && easyOnly > 0, '難強度 20–25%；易＝金 ×1.5／時間 +5s（捉迷藏另有冷靜 6s）'); }
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
  const B0 = G2.bounce; ok(B0.durationSec === 40 && JSON.stringify(B0.starsAt) === '[10,20,30]' && B0.dot === 1 && B0.gold === 3 && B0.goldProb === 0.18 && B0.chargeSec === 0.8 && B0.vMin === 220 && B0.vMax === 470 && B0.gravity === 780 && B0.flipPower === 0.85, '彈彈葉定稿：40s、10/20/30、+1／金 +3、金 0.18、儲力 0.8s→220–470、重力 780、翻筋斗 ≥85%');
  const g = M.create('bounce', 3, { mods: ['time', 'gold'] }), L = G2.bounce.leaf;
  { const air = v => 2 * v * g.unit / (B0.gravity * g.unit), hMax = B0.vMax * B0.vMax * g.unit * g.unit / (2 * B0.gravity * g.unit);
    ok(Math.abs(air(220) - 0.564) < 0.01 && Math.abs(air(470) - 1.205) < 0.01, '空中 0.56–1.2 秒', [air(220), air(470)]);
    ok(hMax >= 0.45 * G2.fieldH - 1e-6 && g.unit > 1 && g.unit < 1.05, '最大跳高 ≥45% 畫面（唔夠 → 單位 ×' + g.unit.toFixed(3) + '）', hMax); }
  ok(g.phase === 'ready' && g.pet.x === L.x && g.pet.y === L.y, '開局團絨企喺葉片');
  g.press(L.x, L.y); run(g, 0.4); ok(g.phase === 'charge' && Math.abs(g.power - 0.5) < 0.03 && g.clip === R.charge, '撳住儲力（0.4s ＝ 50%，線性）＋儲力反應', { p: g.power, c: g.clip });
  run(g, 0.5); ok(g.power === 1 && g.bend === 1, '0.8 秒儲滿 = 1（葉片彎到盡）');
  g.release(); ok(g.phase === 'air' && Math.abs(-g.pet.vy - 470 * g.unit) < 1e-6 && g.flipping && g.clip === R.proud, '放手彈起（滿力 470）；≥85% → 翻筋斗＋得意表情', { vy: g.pet.vy, c: g.clip });
  run(g, 0.3); ok(g.flip > 0 && g.pet.y < L.y - 40, '半空翻緊');
  { const ga = M.create('bounce', 3, { mods: ['time', 'gold'] }), gb = M.create('bounce', 3, { mods: ['time', 'gold'] }); ga.dots = []; gb.dots = []; ga.newDot = gb.newDot = () => ({ x: -99, y: -99 });
    ga.press(L.x, L.y); run(ga, 0.67); gb.press(L.x, L.y); run(gb, 0.7); ok(!ga.flipping || ga.power < 0.85, ''+'84% 唔翻'); ga.power = 0.849; gb.power = 0.851; ga.release(); gb.release();
    let ya = [], yb = []; run(ga, 1.3, x => ya.push(x.pet.x)); run(gb, 1.3, x => yb.push(x.pet.x)); ok(!ga.flipping && gb.flips === 1 && ga.lands === 1 && gb.lands === 1 && ga.score === 0 && gb.score === 0 && ya.every(x => x === L.x) && yb.every(x => x === L.x), '翻筋斗純演出：唔郁落點、唔加分'); }
  const x0 = g.pet.x; g.move(20, 0); run(g, 0.3); ok(g.pet.x < x0 - 15, '半空左右拖（追手指 x）', { x0, x: g.pet.x });
  run(g, 1.5, (gg) => gg.move(170, 0)); ok(g.falls === 1 && ['fallen', 'walk'].includes(g.phase), '跌出葉外 → 跌低', { ph: g.phase, f: g.falls });
  const g2 = M.create('bounce', 3, { mods: ['time', 'gold'] }); g2.press(L.x, L.y); run(g2, 1); g2.release(); let clips = new Set(); run(g2, 3.4, (gg) => { gg.move(170, 0); clips.add(gg.clip); });
  ok(clips.has(R.fall) && clips.has(R.getup) && clips.has(R.cool), '跌低 → 起身 → 扮冇事（droop→getup→act_cool）', [...clips]);
  run(g2, 2); ok(g2.phase === 'ready' && g2.pet.x === L.x, '自己行返葉片');
  const g3 = M.create('bounce', 4, { mods: ['time', 'gold'] }); g3.dots = [{ x: L.x, y: 230, gold: false, ph: 0 }, { x: L.x, y: 190, gold: true, ph: 0 }]; g3.press(L.x, L.y); run(g3, 0.6); g3.release(); let pc = false; run(g3, 2.5, gg => { gg.move(L.x, 0); if (gg.clip === R.proud) pc = true; });
  ok(g3.score >= 4 && g3.fx.some(f => f.type === 'gold'), '掂光點 +1、金光點 +3', { s: g3.score });
  ok(g3.lands >= 1 && pc, '一跳 ≥2 粒 → 落返葉 → 得意（smug_pose）');
  { const dp = M.create('bounce', 9); let ok1 = true; for (let i = 0; i < 300; i++) { const d = dp.newDot(); if (d.y < B0.dotY[0] || d.y > B0.dotY[1]) ok1 = false; } ok(ok1 && L.y - 14 - 144 <= B0.dotY[0], '光點喺跳得到嘅高度'); }
  const gw = M.create('bounce', 5, { mods: ['wind', 'gold'] }); ok(Math.abs(Math.abs(gw.windAx) / B0.steerMax - gw.mods[0].s) < 1e-9 && gw.goldP === 0.18 * 1.5, '難：橫風漂移 ±20–25%；易：金 0.18×1.5');
  const gfs = M.create('bounce', 5, { mods: ['fast', 'gold'] }); ok(gfs.spd === 1 + gfs.mods[0].s && gfs.spd >= 1.2 && gfs.spd <= 1.25, '難：速度 ×1.2–1.25');
  const gsm = M.create('bounce', 5, { mods: ['small', 'time'] }), sm = gsm.mods.find(m => m.hard).s; ok(gsm.tgt === 1 - sm && gsm.tgt >= 0.75 && gsm.tgt <= 0.8 && gsm.dur === 45, '難：光點細 0.75–0.8；易：時間 +5s');
  const gt = M.create('bounce', 6); run(gt, gt.dur + 1); ok(gt.over && gt.t === gt.dur, '時間到完局');
}
// 3 花園捉迷藏
{
  const GH = G2.ghide; ok(JSON.stringify(GH.peekEvery) === '[2.5,4]' && GH.peekSec === 0.6 && GH.tapShake === 0.3 && GH.sneakSec === 4 && GH.mods.speed.sneaky.sneakSec === 2.6 && GH.mods.speed.calm.sneakSec === 6, '捉迷藏定稿：探頭 2.5–4s、搖尾 0.6s、撳搖 0.3s、4s 轉位（狡猾 2.6／冷靜 6）');
  const g = M.create('ghide', 11, { mods: ['calm', 'time'] });
  ok(g.covers.length === GH.covers && g.covers.every(c => GH.coverTypes.includes(c.type)), '5 個遮擋物（花盆／葉堆／石頭／草叢／燈籠）');
  const pos0 = JSON.stringify(g.covers.map(c => [c.x, c.y, c.type]));
  const wrong = g.covers.findIndex((c, i) => i !== g.at); const r1 = g.pick(wrong);
  ok(r1.ok && !r1.hit && g.covers[wrong].shake === 0.3 && g.tries === 2, '撳錯＝搖嗰樣嘢 0.3s、少一次機會');
  run(g, 0.31); ok(g.covers[wrong].shake === 0, '搖 0.3 秒就停');
  const r2 = g.pick(g.at); ok(r2.hit && r2.pts === 2 && g.phase === 'reveal', '第 2 下搵到 = 2 分');
  let cl = new Set(); run(g, 1.6, gg => cl.add(gg.clip)); ok(cl.has(R.surprised) && cl.has(R.cool), '搵到 → 嚇一跳 → 扮冇事行出嚟', [...cl]);
  ok(g.round === 1 && JSON.stringify(g.covers.map(c => [c.x, c.y, c.type])) !== pos0, '下一回合：位置＋遮擋物換晒');
  const at0 = g.at, sn = g.sneaks; run(g, 5.9); ok(g.sneaks === sn, '冷靜：6 秒內唔轉位'); run(g, 0.2); ok(g.sneaks === sn + 1 && g.at !== at0, '太慢冇撳 → 佢偷偷轉位', { at0, at: g.at });
  const gd = M.create('ghide', 12, { mods: ['small', 'time'] }); { const n0 = gd.sneaks; run(gd, 3.95); const a = gd.sneaks; run(gd, 0.1); ok(a === n0 && gd.sneaks === n0 + 1, '冇變化：等 4 秒轉位'); }
  const gs = M.create('ghide', 12, { mods: ['wind', 'sneaky'] }); ok(gs.sneakSec === 2.6 && gs.sway > 0, '狡猾：2.6 秒轉位；風：遮擋物擺');
  run(gs, 0.5); ok(gs.covers.some(c => Math.abs(c.dx) > 0.5) && gs.covers.every(c => Math.abs(c.dx) <= gs.mods[0].s * GH.area.minDist + 1e-9), '風漂移：遮擋物左右擺 ±s×minDist');
  ok(Math.abs(gd.hitR / GH.hitR - (1 - gd.mods.find(m => m.hard).s)) < 1e-9 && gd.hitR / GH.hitR >= 0.75 && gd.hitR / GH.hitR <= 0.8 && gd.dur === 50, '難：目標細 0.75–0.8；易：時間 +5s（50s）');
  { let ivs = [], wigs = 0, peeks = 0; for (let sd = 1; sd < 40; sd++) { const gg = M.create('ghide', sd, { mods: ['calm', 'time'] }); let last = 0, prev = false; for (let i = 0; i < 660; i++) { gg.update(1 / 60); const on = gg.peeking || gg.covers[gg.at].wig > 0; if (on && !prev) { if (last) ivs.push(gg.t - last); last = gg.t; gg.tail ? peeks++ : wigs++; } prev = on; } }
    ok(ivs.length > 10 && ivs.every(v => v >= 2.49 && v <= 4.02) && peeks > 0 && wigs > 0, '探頭／自己郁每 2.5–4 秒一次（露尾燈泡回合 + 其餘回合郁）', { n: ivs.length, mn: Math.min(...ivs), mx: Math.max(...ivs) }); }
  { let pk = 0; const gg = M.create('ghide', 1, { mods: ['calm', 'time'] }); gg.tail = true; gg.peekT = 0.01; run(gg, 0.02); for (let i = 0; i < 60; i++) { if (gg.peeking) pk++; gg.update(1 / 60); } ok(Math.abs(pk / 60 - 0.6) < 0.05, '搖尾 0.6 秒', pk / 60); }
  { const kinds = new Set(); for (let sd = 1; sd < 30; sd++) kinds.add(M.create('ghide', sd).peekKind); ok(kinds.has('tail') && kinds.has('bulb'), '露尾巴或燈泡'); }
  const gm = M.create('ghide', 14, { mods: ['calm', 'time'] }); let cl2 = new Set(); [0, 1, 2, 3, 4].filter(i => i !== gm.at).slice(0, 3).forEach(i => gm.pick(i)); run(gm, 1, x => cl2.add(x.clip)); ok(cl2.has(R.proud) && gm.score === 0, '3 下都撳錯 → 團絨得意出嚟（0 分）');
  const gf = M.create('ghide', 15, { mods: ['calm', 'time'] }); for (let r = 0; r < 3; r++) { gf.pick(gf.at); run(gf, 1.6); } ok(gf.over && gf.score === 9 && gf.firstHits === 3 && gf.stars === 3, '3 回合都第 1 下搵到 = 9 分 3★', { s: gf.score });
}
// 5 追螢火
{
  const E6 = D.PARAMS.evo6; ok(M.fireflyOpen(21) && M.fireflyOpen(3) && !M.fireflyOpen(12) && M.fireflyOpen(17) && !M.fireflyOpen(7), '夜晚限定：' + E6.nightFrom + '–' + E6.nightTo + ' 點（evo6 夜窗）');
  { const f0 = E6.nightFrom; E6.nightFrom = 19; const o18 = M.fireflyOpen(18); E6.nightFrom = f0; ok(!o18 && M.fireflyOpen(18), '同螢絨夜窗共用常數（改 evo6.nightFrom 即跟住變）'); }
  ok(G2.firefly.durationSec === 40 && JSON.stringify(G2.firefly.starsAt) === '[8,16,26]' && G2.firefly.fly === 1 && G2.firefly.gold === 3 && G2.firefly.goldProb === 0.2, '追螢火定稿：40s、8/16/26、+1／金 +3、金 0.2');
  const g = M.create('firefly', 21, { mods: ['time', 'gold'] }); g.branches = []; g.flies = [{ x: 90, y: 180, vx: 0, vy: 0, ph: 0, gold: false }];
  g.press(90, 270); for (let y = 266; y >= 170; y -= 6) g.move(90, y); g.release(); ok(g.path.length > 10, '手指畫路');
  run(g, 1.2); ok(g.caught >= 1 && g.score >= 1, '團絨跟住條路走、捉到螢火 +1', { s: g.score, p: g.pet });
  const g2 = M.create('firefly', 22, { mods: ['time', 'gold'] }); g2.flies = []; g2.branches = [{ x1: 60, y1: 220, x2: 120, y2: 220 }];
  g2.press(90, 270); for (let y = 266; y >= 150; y -= 6) g2.move(90, y); g2.release(); let cl = new Set(); run(g2, 1.6, x => cl.add(x.clip));
  ok(g2.bumps === 1 && g2.path.length === 0 && cl.has(R.bump) && cl.has(R.cool), '撞樹枝 → 停低、條路清咗、扮冇痛（pot_bump→act_cool）', { b: g2.bumps, cl: [...cl] });
  ok(g2.pet.y > 220, '撞到唔會穿過樹枝');
  const gf = M.create('firefly', 23, { mods: ['fast', 'gold'] }), sf = gf.mods[0].s; ok(gf.flySpd === 1 + sf && sf >= 0.2 && sf <= 0.25 && gf.goldP === 0.2 * 1.5, '難：螢火快 ×1.2–1.25；易：金 ×1.5', { s: sf, gp: gf.goldP });
  const gs = M.create('firefly', 23, { mods: ['small', 'time'] }), ss = gs.mods.find(m => m.hard).s; ok(gs.tgt === 1 - ss && gs.tgt >= 0.75 && gs.tgt <= 0.8 && gs.dur === 45, '難：螢火判定細 0.75–0.8；易：時間 +5s（45s）');
  const gw = M.create('firefly', 23, { mods: ['breeze', 'gold'] }); ok(Math.abs(Math.abs(gw.windX) / G2.firefly.petSpeed - gw.mods[0].s) < 1e-9, '難：微風漂移 ±20–25% 團絨速度');
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
  { const def = JSON.stringify(D.PARAMS.systems12b).includes('"catch_3star"'); const s2 = S.newState(T0, 6); s2.stage = 'juvenile'; X.st(s2); B.gameFinish(s2, 'catch', 50, T0);
    const onlyCatch = B.met(s2, { bounceStars: 3 }); B.gameFinish(s2, 'bounce', 30, T0); ok(def && !onlyCatch && B.met(s2, { bounceStars: 3 }), '徽章 catch_3star「彈彈葉 3★」只計彈彈葉（接光點 3★ 唔算）'); }
  let threw = false; try { B.gameFinish(s, 'xxx', 1, T0); } catch (e) { threw = true; } ok(threw, '未知 kind 照拒');
}
console.log((fail ? '✗' : '✓') + ' minigames2: ' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
