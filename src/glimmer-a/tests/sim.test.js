/* Node 無依賴測試：node tests/sim.test.js */
const S = require('../src/sim.js');
const D = require('../src/data.js');
const P = D.PARAMS;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info ? '  → ' + info : '')); } }
function near(a, b, tol, name) { ok(Math.abs(a - b) <= tol, name, `got ${a.toFixed(3)} expect ${b.toFixed(3)} ±${tol}`); }
const H = 3600;
function adult(needs) { const s = S.newState(1e12, 7); s.stage = 'adult'; s.form = 'soft'; if (needs) Object.assign(s.needs, needs); return s; }
function sprout(needs) { const s = S.newState(1e12, 7); s.stage = 'sprout'; Object.assign(s.needs, needs || { hunger: 100, mood: 100, clean: 100, energy: 100 }); return s; }

console.log('# 衰減率（守夜者，清醒，1 小時內無便便）');
{
  const s = adult(); S.advance(s, H, {}, 30);
  near(s.needs.hunger, 100 - 6, 0.01, '飽腹 −6/h');
  near(s.needs.mood, 100 - 4, 0.01, '心情 −4/h');
  near(s.needs.clean, 100 - 3 * P.traitCleanDecayMul, 0.01, '清潔 −3×團絨係數 /h (=' + (3 * P.traitCleanDecayMul) + ')');
  near(s.needs.energy, 100 - 5, 0.01, '精力 −5/h');
}
console.log('# 芽崽衰減較快');
{
  const s = sprout(); S.advance(s, H, {}, 30);
  near(s.needs.hunger, 100 - 6 * P.stageDecayMul.sprout, 0.01, '芽崽飽腹 −6×' + P.stageDecayMul.sprout);
}
console.log('# 睡眠 ×0.3、精力 +12/h（團絨 +20%）');
{
  const s = adult({ energy: 40 }); s.sleeping = true; S.advance(s, H, {}, 30);
  near(s.needs.hunger, 100 - 6 * 0.3, 0.01, '睡眠飽腹 −1.8/h');
  near(s.needs.mood, 100 - 4 * 0.3, 0.01, '睡眠心情 −1.2/h');
  near(s.needs.clean, 100 - 3 * P.traitCleanDecayMul * 0.3, 0.01, '睡眠清潔 ×0.3');
  near(s.needs.energy, 40 + 12 * P.traitSleepRegenMul, 0.01, '睡眠精力 +' + (12 * P.traitSleepRegenMul) + '/h');
  const t = adult({ energy: 90 }); t.sleeping = true; S.advance(t, H, {}, 30);
  ok(t.sleeping === false && t.needs.energy > 95, '精力到 100 自動醒（之後再正常衰減）', t.needs.energy);
  const u = adult({ energy: 95 }); ok(S.toggleSleep(u).ok === false, '精力 ≥90 瞓唔著');
}
console.log('# 便便');
{
  const s = adult(); S.advance(s, 3 * H, {}, 30); ok(s.poops === 1, '3h 後 1 個便便');
  S.advance(s, 20 * H, {}, 60); ok(s.poops === P.poopMax, '便便上限 ' + P.poopMax);
  const c = adult(); c.poops = 2; S.advance(c, H, {}, 30);
  near(c.needs.clean, 100 - (3 * P.traitCleanDecayMul + 2), 0.01, '每個便便令清潔衰減 +1/h');
}
console.log('# 離線 E 公式');
{
  near(S.effectiveOffline(6 * H) / H, 6, 1e-9, 'T=6h → E=6h');
  near(S.effectiveOffline(8 * H) / H, 8, 1e-9, 'T=8h → E=8h');
  near(S.effectiveOffline(12 * H) / H, 8 + 4 * 0.25, 1e-9, 'T=12h → E=9h');
  near(S.effectiveOffline(24 * H) / H, 8 + 16 * 0.25, 1e-9, 'T=24h → E=12h');
  near(S.effectiveOffline(30 * H) / H, 12, 1e-9, 'T=30h → E=12h（超過 24h 唔計）');
  near(S.effectiveOffline(-50), 0, 1e-9, '時間回撥 → E=0');
}
console.log('# 離線推算（守夜者 6h）');
{
  const s = adult(); s.lastSeen = 1e12 - 6 * H * 1000; const r = S.applyOffline(s, 1e12);
  near(r.E / H, 6, 1e-9, 'E=6h');
  near(s.needs.hunger, 64, 0.5, '飽腹 100−36'); near(s.needs.mood, 76, 0.5, '心情 100−24');
  near(s.needs.energy, 70, 0.5, '精力 100−30'); near(s.needs.clean, 100 - (3.9 * 3 + 4.9 * 3), 0.7, '清潔連便便');
  ok(s.poops === 2, '便便按 E 計 = 2'); ok(r.show && r.summary.length <= 3 && r.summary.length >= 1, '摘要 ≤3 句（' + r.summary.length + '）');
  ok(r.gift >= 1 && s.grains === r.gift, '有光粒禮物 ' + r.gift);
}
console.log('# 離線保底 20 / 無死亡');
{
  const s = adult({ hunger: 40, mood: 40, clean: 40, energy: 40 }); s.lastSeen = 1e12 - 30 * H * 1000; const r = S.applyOffline(s, 1e12);
  ok(['hunger', 'mood', 'clean', 'energy'].every(k => s.needs[k] >= 20 - 1e-9), '所有需求 ≥ 20（保底）', JSON.stringify(s.needs));
  ok(s.needs.hunger === 20 && s.needs.mood === 20, '飽腹／心情落到保底 20');
  ok(r.withdrawn && s.withdrawn.on, '觸發「睏倦退縮」');
  ok(!S.isUnwell(s), '離線唔會令寵物「不適」');
  ok(!('dead' in s) && s.stage === 'adult', '無死亡狀態');
  const low = adult({ hunger: 10, mood: 100, clean: 100, energy: 100 }); low.lastSeen = 1e12 - 30 * H * 1000; S.applyOffline(low, 1e12);
  ok(low.needs.hunger === 10, '原本已低過保底就唔再降（10 保持 10）');
  // 退縮恢復：餵食＋玩耍各一次
  S.feed(s, 'cookie'); ok(s.withdrawn.on, '只餵食未恢復'); S.play(s); ok(!s.withdrawn.on, '餵食＋玩耍各一次即恢復');
  // 連續 100 次離線循環
  const z = sprout(); let t = 1e12; for (let i = 0; i < 100; i++) { z.lastSeen = t; t += 30 * H * 1000; S.applyOffline(z, t); }
  ok(Object.values(z.needs).every(v => isFinite(v) && v >= 0 && v <= 100), '連續 100 次離線仍然有效，無死亡');
}
console.log('# 離線睡眠 / 成長（evo6：真實時間、上限 24h、最多升 1 階）');
{
  const s = adult({ energy: 50 }); s.sleeping = true; s.lastSeen = 1e12 - 6 * H * 1000; S.applyOffline(s, 1e12);
  const wakeH = (100 - 50) / (12 * P.traitSleepRegenMul);
  near(s.needs.energy, 100 - 5 * (6 - wakeH), 0.6, '離線睡到 100 自動醒後再衰減'); ok(!s.sleeping, '離線後已醒');
  const g = sprout(); g.lastSeen = 1e12 - 6 * H * 1000; S.applyOffline(g, 1e12);
  near(g.growthSec, 6 * H, 1, 'T=6h 離線成長 = 真實 6h（evo6：唔再 ×50%）');
  const g2 = sprout(); g2.lastSeen = 1e12 - 12 * H * 1000; S.applyOffline(g2, 1e12);
  near(g2.growthSec, 12 * H, 1, 'T=12h 成長 = 12h（芽崽未夠 18h）');
  const g3 = sprout(); g3.lastSeen = 1e12 - 30 * H * 1000; S.applyOffline(g3, 1e12);
  ok(g3.stage === 'juvenile' && g3.growthSec === 0, 'T=30h（上限 24h ≥ 芽崽 18h）→ 升跳跳期、進度 0', [g3.stage, g3.growthSec]);
  const on = sprout(); S.advance(on, 6 * H, {}, 60); ok(on.growthSec >= 6 * H - 1 || on.stage !== 'sprout', '線上成長 100%（對比）', on.growthSec);
  const e = S.newState(1e12, 1); e.lastSeen = 1e12 - 1000 * 1000; const r = S.applyOffline(e, 1e12); ok(e.stage === 'newborn' && e.growthSec === 0, '光卵離線 1000s ≥ 10 分 → 孵化做絨點、進度 0', [e.stage, e.growthSec]);
  const sh = adult(); sh.lastSeen = 1e12 - 60 * 1000; const r2 = S.applyOffline(sh, 1e12); ok(!r2.show, '離開 <5 分鐘唔彈摘要');
}
console.log('# 不適（<15）停止成長');
{
  const s = sprout({ hunger: 10, mood: 100, clean: 100, energy: 100 }); ok(S.isUnwell(s), '需求 <15 → 不適');
  const g0 = s.growthSec; S.advance(s, 600, {}, 30); ok(s.growthSec === g0, '不適時成長停止');
  const u = sprout({ hunger: 100, mood: 100, clean: 100, energy: 100 }); S.advance(u, 600, {}, 30); near(u.growthSec, 600, 1, '正常成長 1:1');
}
console.log('# CQ 規則');
{
  const mk = (v) => { const s = sprout({ hunger: v, mood: v, clean: v, energy: v }); s.cq = 50; return s; };
  let s = mk(80); S.settleCQ(s); ok(s.cq === 51, '平均 ≥60 → +1');
  s = mk(60); S.settleCQ(s); ok(s.cq === 51, '平均 =60 → +1');
  const Q = P.evo6.branch.cq, near2 = (a, b) => Math.abs(a - b) < 1e-6;
  s = mk(45); S.settleCQ(s); ok(near2(s.cq, 50 + Q.partialMax * (45 - P.cqBadBelow) / (P.cqGoodAt - P.cqBadBelow)), `v3 部分照顧：平均 45 → +${Q.partialMax}×比例`, s.cq);
  s = mk(P.cqBadBelow); S.settleCQ(s); ok(s.cq === 50, `平均 =${P.cqBadBelow} → +0`);
  s = mk(20); S.settleCQ(s); ok(s.cq === 49, '平均 <30 → −1');
  s = mk(10); S.settleCQ(s); ok(s.cq === 48, '病中再 −1（<30 −1，不適 −1）');
  s = sprout({ hunger: 100, mood: 100, clean: 100, energy: 100 }); S.advance(s, H, {}, 30); ok(s.cq === 51, '每小時結算一次（線上）');
  // v3：底線（扣分唔跌穿 floor）
  s = mk(20); s.cq = Q.floor; S.settleCQ(s); ok(s.cq === Q.floor, `CQ ${Q.floor}（floor）＋平均 <30 → 唔再跌`, s.cq);
  s = mk(10); s.cq = Q.floor + 1; S.settleCQ(s); ok(s.cq === Q.floor, `CQ ${Q.floor + 1}＋病 → 最多跌到 ${Q.floor}`, s.cq);
  s = mk(10); s.cq = Q.floor - 5; S.settleCQ(s); ok(s.cq === Q.floor - 5, '本身低過 floor → 唔再扣（亦唔會自動補返）', s.cq);
  // v3：每次照顧都計分（每個鐘上限）
  s = mk(50); s.needs.hunger = 10; S.feed(s, 'meal'); ok(near2(s.cq, 50 + Q.careGain) && s.cqIdleSec === 0, `餵一次 → +${Q.careGain}`, s.cq);
  for (let i = 0; i < 20; i++) S.play(s); ok(near2(s.cq, 50 + Q.careGainPerHourMax), `一個鐘內照顧好多次 → 最多 +${Q.careGainPerHourMax}`, s.cq);
  S.settleCQ(s); const c1 = s.cq; S.play(s); ok(near2(s.cq, c1 + Q.careGain), '每小時結算後上限重計');
  { const e = S.newState(1e12, 1); const c0 = e.cq; S.play(e); ok(e.cq === c0, '光卵期照顧唔加 CQ'); }
  // v3：衰減（連續 decayAfterH 個鐘冇照顧 → 每個鐘 −decayPerH；線上＋離線；唔跌穿 floor）
  s = sprout(); s.cq = 50; s.cqIdleSec = 0; s.lastSeen = 1e12 - 8 * H * 1000; S.applyOffline(s, 1e12);
  ok(near2(s.cq, 50 - Q.decayPerH * Math.max(0, 8 - Q.decayAfterH)), `離線 8 個鐘冇照顧 → −${Q.decayPerH}×${8 - Q.decayAfterH}（頭 ${Q.decayAfterH} 個鐘唔扣）`, s.cq);
  s = sprout(); s.cq = 50; s.cqIdleSec = 0; s.lastSeen = 1e12 - (Q.decayAfterH - 1) * H * 1000; S.applyOffline(s, 1e12); ok(s.cq === 50, `離線 ${Q.decayAfterH - 1} 個鐘 → 唔扣`, s.cq);
  s = sprout(); s.cq = 50; s.cqIdleSec = 0; s.lastSeen = 1e12 - 400 * H * 1000; S.applyOffline(s, 1e12); ok(s.cq >= Q.floor, `離線好耐 → 跌到 floor ${Q.floor} 為止（疏玩唔會 0）`, s.cq);
  s = sprout(); s.cq = 50; s.cqIdleSec = (Q.decayAfterH + 1) * H; S.cqDecay(s, H); ok(near2(s.cq, 50 - Q.decayPerH), '線上冇理都會跌（每個鐘）', s.cq);
  s.needs.hunger = 10; S.feed(s, 'meal'); const c2 = s.cq; S.cqDecay(s, H); ok(s.cq === c2, '照顧後重新計時（頭幾個鐘唔扣）');
  { // v3 目標：疏玩（每日上線一次、餵＋玩）唔會直接 0，CQ 大約 15–35（文件目標）
    const t = S.newState(1e12, 5); t.stage = 'juvenile'; t.growthSec = 0; t.cq = P.cqStart; t.needs = { hunger: 70, mood: 70, clean: 70, energy: 80 }; let now = 1e12;
    for (let d = 0; d < 10 && t.stage === 'juvenile'; d++) { t.needs.hunger = Math.min(t.needs.hunger, 50); S.feed(t, 'meal'); S.play(t); S.advance(t, 600, {}, 30); now += 600e3; t.lastSeen = now; now += (24 * H - 600) * 1000; S.applyOffline(t, now); }
    const ev = t.ev.find(e => e.type === 'evolve'); ok(ev && ev.cq >= Math.max(Q.floor, 15) && ev.cq <= 35 && ev.cq > 0, `疏玩（每日一次）→ 判定 CQ ${ev && ev.cq.toFixed(1)}（15–35，唔係 0）`, ev && ev.cq); }
}
console.log('# 分支門檻（config evo6.branch：燦光 ' + P.evo6.branch.brightCQ + '／柔光 ' + P.evo6.branch.softCQ + '；evo6：跳跳期完先分支）');
{
  const evo = (cq) => { const s = sprout(); s.stage = 'juvenile'; s.cq = cq; s.growthSec = P.stageSec.juvenile - 1; S.step(s, 5, {}); return s; };
  for (const [cq, f] of (({ brightCQ: hi, softCQ: lo }) => [[100, 'bright'], [hi, 'bright'], [hi - 1, 'soft'], [lo, 'soft'], [lo - 1, 'dust'], [0, 'dust']])(P.evo6.branch)) {
    const s = evo(cq); ok(s.stage === 'adult' && s.form === f, `CQ=${cq} → ${f}`, s.form);
  }
  const s = evo(75); ok(s.ev.some(e => e.type === 'evolve' && e.form === 'bright'), '產生 evolve 事件'); ok(s.cq === P.cqStart, '進入新階段 CQ 重置');
}
console.log('# 光卵孵化');
{
  const s = S.newState(1e12, 3); let n = 0; while (s.stage === 'egg' && n < 20) { S.tapEgg(s); n++; }
  ok(s.stage === 'newborn' && n === Math.ceil(P.stageSec.egg / P.eggTapBoostSec), '點 ' + n + ' 下孵化（evo6 → 絨點 newborn）');
  ok(s.needs.hunger === P.startNeedsSprout.hunger, '孵化後需求初始化');
  const t = S.newState(1e12, 3); S.advance(t, 600, {}, 30); ok(t.stage === 'newborn', '10 分鐘自然孵化（→ 絨點）');
}
console.log('# 好／差照顧（芽崽 18h＋跳跳期 3 日）→ 分支');
{
  const careBot = (care) => {
    // care=true 勤力；care=false 只喺需求 <20 先勉強補到 30（否則唔會成長）
    const s = sprout({ hunger: 80, mood: 80, clean: 80, energy: 100 }); s.cq = P.cqStart;
    for (let h = 0; h < 140 && (s.stage === 'sprout' || s.stage === 'juvenile'); h++) {
      for (let q = 0; q < 4; q++) {
        if (care) { if (s.needs.hunger < 70) S.feed(s, 'meal'); if (s.needs.mood < 70) S.play(s); if (s.needs.clean < 70) S.rinse(s); S.clearPoop(s); if (s.needs.energy < 30 && !s.sleeping) S.toggleSleep(s); }
        if (!care) for (const k of ['hunger', 'mood', 'clean', 'energy']) if (s.needs[k] < 20) s.needs[k] = 30;
        S.advance(s, 900, {}, 30);
      }
    }
    return s;
  };
  if (S.setHourFn) S.setHourFn(() => 12);   // §7 月眠計 21–03 照顧：鎖定遊戲鐘中午，唔再受跑測試嘅真實時間影響
  const a = careBot(true), b = careBot(false);
  if (S.setHourFn) S.setHourFn(null);
  if (a.ev) { const ev = a.ev.find(e => e.type === 'evolve'); if (ev && ev.b5) console.log('  · 勤力照顧 §7 分數', JSON.stringify(ev.b5.score), 'all', ev.b5.all, 'top', ev.b5.top, ev.b5.topShare, ev.b5.secondShare, 'clean', ev.b5.cleanAvg); }
  ok(a.stage === 'adult' && a.form === 'bright', '勤力照顧 → 燦光', a.form + ' cq=' + a.cq);
  { const ev = a.ev.find(e => e.type === 'evolve') || {};   // §7 修訂：清便便 39%＋清潔 85 → 全面照顧（最高 <45%）→ 燦光先過新 5 條
    ok(ev.cq >= P.evo6.branch.brightCQ && ev.b5 && ev.b5.top === 'crystal' && ev.b5.topShare * 100 < P.evo6.branch.brightMaxTopPct && ev.b5.ok, '勤力照顧：晶角 39%（新 5 條本身成立）但 < 燦光上限 → 燦光優先', ev.b5 && ev.b5.topShare); }
  ok(b.stage === 'adult' && b.form === 'dust', '極少照顧（<20 先補到 30）→ 微塵（可重養，非失敗）', b.form);
}
console.log('# 迷你遊戲');
{
  const idle = new S.Minigame(5); while (!idle.over) idle.update(1 / 30, 97);
  ok(idle.over && Math.abs(idle.t - 45) < 1e-9, '45 秒完結'); 
  const bot = new S.Minigame(5); let n = 0;
  while (!bot.over) {
    let tgt = bot.basketX; let best = 1e9;
    for (const it of bot.items) if (it.type !== 'stone' && it.y < P.mg.basketY && P.mg.basketY - it.y < best) { best = P.mg.basketY - it.y; tgt = it.x; }
    bot.update(1 / 30, tgt); n++;
  }
  ok(bot.score >= 100 && bot.caught > 20, '機械人接星屑得分 ' + bot.score + '（接 ' + bot.caught + '）');
  const s = adult({ mood: 10 }); s.withdrawn.on = false;
  let r = S.mgReward(s, 95, 1e12); ok(r.grains === 9 && r.mood === 8 && r.ratio === 1, '95 分 → floor(95/10)=9 光粒，心情 +8');
  r = S.mgReward(s, 100, 1e12); ok(r.mood === 20 && r.grains === 10, '100 分高分 → 心情 +20');
  r = S.mgReward(s, 999, 1e12); ok(r.grains === 20, '光粒上限 20');
  r = S.mgReward(s, 30, 1e12); ok(r.mood === P.mg.moodFail, '低於及格 → 心情 +' + P.mg.moodFail);
  const t = adult({ mood: 0 }); const rs = [];
  for (let i = 0; i < 7; i++) rs.push(S.mgApply(t, 200, 1e12));
  ok(rs.slice(0, 5).every(x => x.ratio === 1 && x.grains === 20), '首 5 次全額');
  ok(rs[5].ratio === 0.5 && rs[5].grains === 10 && rs[6].mood === 10, '第 6 次起 50%（光粒 10、心情 10）');
  ok(t.grains === 100 + 20, '光粒累計 ' + t.grains);
  const nd = S.mgReward(t, 200, 1e12 + 86400e3 * 1.2); ok(nd.ratio === 1 && nd.playIndex === 1, '翌日重置額度');
  const A = new S.Minigame(99), B = new S.Minigame(99); for (let i = 0; i < 300; i++) { A.update(1 / 30, 50); B.update(1 / 30, 50); }
  ok(A.score === B.score && A.items.length === B.items.length, '同種子可重現');
}
console.log('# 存檔');
{
  const s = adult({ hunger: 33.3 }); s.grains = 12; const j = S.serialize(s); const r = S.deserialize(j, 5);
  ok(r && r.needs.hunger === 33.3 && r.grains === 12 && r.stage === 'adult' && r.ev.length === 0, '序列化／還原一致');
  ok(S.deserialize('{oops', 1) === null && S.deserialize('{"v":2}', 1) === null, '壞檔返回 null');
  const a = S.makeRng(42), b = S.makeRng(42); ok(a() === b() && a() === b(), 'RNG 可設種子');
}
console.log('# QA P1：lastSeen 只可向前');
{ const T = Date.UTC(2026, 5, 10, 4, 0, 0); const s = S.newState(T, 3); s.lastSeen = T; s.lastSaveTime = T;
  S.applyOffline(s, T - 121e3); ok(s.lastSeen === T, '回撥 121 秒開 app：applyOffline 唔將 lastSeen 拉後');
  S.applyOffline(s, T + 3600e3); ok(s.lastSeen === T + 3600e3, '正常前進：lastSeen 跟住 now');
  s.lastSaveTime = T + 40 * 3600e3; s.lastSeen = T + 40 * 3600e3; S.applyOffline(s, T + 7200e3); ok(s.lastSeen === T + 7200e3 && s.saveResetAt === T + 7200e3, '超前 >24h 重設：lastSeen／saveResetAt＝now（唯一例外）'); }
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
