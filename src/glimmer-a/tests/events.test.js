/* 事件系統測試（Node 無依賴）：node tests/events.test.js
   涵蓋：參數（遊策定案 v2）、確定性、全域間隔、單事件冷卻、保底、閃光日 3%（hash）、彩虹傍晚、鬧脾氣門檻、
   離線唔傷害＋最多彈 2 個＋日記（合併／+3／上限 60／14 日）、200×7 日分佈、存檔續玩 */
const SIM = require('../src/sim.js');
const D = require('../src/data.js');
require('../src/lighting.js');
const EV = require('../src/events.js');
const P = D.PARAMS.events;
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const H = 3600, DAY = 86400e3;
const BASE = new Date(2026, 0, 5, 0, 0, 0).getTime();       // 本機 2026-01-05 00:00
function adult(seed) { const s = SIM.newState(BASE, seed || 7); s.stage = 'adult'; s.form = 'soft'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }); return s; }
function care(s) { s.needs.hunger = Math.max(s.needs.hunger, 80); s.needs.mood = Math.max(s.needs.mood, 80); s.needs.clean = Math.max(s.needs.clean, 80); s.needs.energy = Math.max(s.needs.energy, 80); s.poops = 0; s.sleeping = false; }

/* 模擬 days 日；每日 sessions（鐘點）上線 onlineSec，之間用 applyOffline 結算。回傳 { s, recs, popups } */
function simulate(seed, days, sessions, o) {
  o = o || {}; const s = adult(seed); const recs = []; let now = BASE;
  EV.listeners.push(onRec); function onRec(st, r) { if (st === s) recs.push(r); }
  s.lastSeen = now;
  const opens = [];
  for (let d = 0; d < days; d++) for (const h of sessions) opens.push(BASE + d * DAY + h * H * 1000);
  let nOpen = 0;
  for (const t of opens) {
    now = t;
    const rep = SIM.applyOffline(s, now);
    if (!o.noCare) care(s);
    EV.noteOpen(s, { hour: SIM.hourOf(now), now });
    const dur = o.onlineSec || 180;
    for (let k = 0; k < dur; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); if (s.evs) { while (EV.takePending(s)) { } } }
    s.lastSeen = now + dur * 1000; nOpen++;
  }
  EV.listeners.splice(EV.listeners.indexOf(onRec), 1);
  return { s, recs, days, opens: nOpen };
}
const SESS = [8, 12.5, 18, 21, 23.5];

console.log('# 參數（遊策定案 v2）');
ok(P.drawChance === 0.34 && P.minGapSec === 1200 && P.cooldownH === 24 && P.cooldownRareH === 72 && P.repeatWeightMul === 0.25, 'p_hit 0.34／全域間隔 20 分鐘／冷卻 24h／稀有 72h／防重複 ×0.25');
ok(P.guaranteeHour === 16 && P.guaranteeOpens === 1 && P.flashDayRate === 0.03 && P.offlinePopupMax === 2, '保底 16:00／首次開 app／閃光日 3%／離線最多彈 2');
ok(P.grumpyLowNeed === 30 && P.grumpyLowSec === 7200 && D.EVENTS.find(e => e.id === 'grumpy').cooldownH === 48, '鬧脾氣：需求<30 持續 2h，冷卻 48h');
ok(P.diaryKeepDays === 14 && P.diaryWarnDays === 12 && P.diaryGrains === 3 && P.diaryClaimMax === 60, '日記：14 日／12 日提示／每條 +3／上限 60');
ok(D.EVENTS.filter(e => e.rare).map(e => e.id).sort().join() === 'flash,meteor,rainbow', '稀有＝流星夜＋彩虹（＋閃光日特殊）');
ok(D.EVENTS.length === 9 && D.EVENTS.filter(e => !e.special && !e.lowNeed).length === 7 && D.PARAMS.beh.envCooldown === 260, '事件池＝7 個一般＋鬧脾氣＋閃光日（共 9）；環境互動冷卻 260 秒');
ok(D.PARAMS.light.periodStarts.morning === 7 && D.PARAMS.light.periodStarts.noon === 11 && D.PARAMS.light.periodStarts.evening === 17 && D.PARAMS.light.periodStarts.night === 23, '時段 早07／午11／晚17／夜23');

console.log('# 確定性');
{
  const a = simulate(11, 5, SESS), b = simulate(11, 5, SESS), c = simulate(12, 5, SESS);
  const sig = (r) => r.recs.map(x => x.id + '@' + x.day + ':' + Math.round(x.at)).join('|');
  ok(sig(a) === sig(b) && a.recs.length > 0, '同種子同流程 → 完全相同嘅事件序列（' + a.recs.length + ' 個）');
  ok(sig(a) !== sig(c), '不同種子 → 序列不同');
}

console.log('# 200 × 7 日（每日 5 次開 app）分佈／間隔／冷卻／保底／彩虹');
{
  const perDay = [], gaps = [], hist = {}; let back = 0, pairs = 0, cdViol = 0, cdPairs = 0, guarOnly = 0, zeroDays = 0, daysTot = 0, rainbowBad = 0, rainbow = 0, flashEv = 0, evTot = 0, grumpy = 0;
  const byId = {}; const cooldownBreakGuar = [];
  for (let seed = 1; seed <= 200; seed++) {
    const r = simulate(seed, 7, SESS);
    const days = {}; r.recs.forEach(x => { days[x.day] = (days[x.day] || 0) + 1; });
    for (let d = 0; d < 7; d++) { const n = days[d] || 0; perDay.push(n); hist[n] = (hist[n] || 0) + 1; if (!n) zeroDays++; daysTot++; }
    const last = {}; let prev = null;
    r.recs.forEach(x => {
      evTot++; byId[x.id] = (byId[x.id] || 0) + 1;
      if (prev) { gaps.push(x.at - prev.at); pairs++; if (prev.id === x.id) back++; }
      if (last[x.id] != null) { cdPairs++; const need = (D.EVENTS.find(e => e.id === x.id).cooldownH || (D.EVENTS.find(e => e.id === x.id).rare ? 72 : 24)) * H; if (x.at - last[x.id] < need - 1 && x.kind !== 'guarantee' && x.kind !== 'flash') cdViol++; if (x.at - last[x.id] < need - 1 && x.kind === 'guarantee') cooldownBreakGuar.push(x.id); }
      last[x.id] = x.at; prev = x;
      if (x.id === 'rainbow') { rainbow++; if (!(x.hour >= 17 && x.hour < 23)) rainbowBad++; }
      if (x.id === 'flash') flashEv++;
      if (x.id === 'grumpy') grumpy++;
    });
  }
  const mean = perDay.reduce((a, b) => a + b, 0) / perDay.length;
  console.log('    事件／日 分佈：' + Object.keys(hist).sort().map(k => k + '個:' + (hist[k] / daysTot * 100).toFixed(1) + '%').join('  ') + '  平均 ' + mean.toFixed(2));
  console.log('    事件總數 ' + evTot + '，各類：' + JSON.stringify(byId) + '；保底破冷卻 ' + cooldownBreakGuar.length);
  ok(Math.min(...gaps) >= P.minGapSec - 1, '任何兩個事件間隔 ≥ ' + P.minGapSec / 60 + ' 分鐘（最小 ' + Math.round(Math.min(...gaps)) + ' s）');
  ok(cdViol === 0, '單事件冷卻 24h／稀有 72h／鬧脾氣 48h（抽選路徑零違反；' + cdPairs + ' 對重複）', cdViol);
  ok(zeroDays === 0, '每日保底：1400 日冇一日零事件', zeroDays);
  ok(mean >= 1 && mean <= 3, '平均每日事件數 1–3（' + mean.toFixed(2) + '）');
  ok(Math.max(...perDay) <= P.dailyMax + 2, '單日上限（' + P.dailyMax + '，保底／閃光額外）→ 最大 ' + Math.max(...perDay));
  ok(back / pairs < 0.06, '連續重複同一事件比例 < 6%（' + (back / pairs * 100).toFixed(1) + '%，防重複×0.25＋冷卻）');
  ok(rainbowBad === 0 && rainbow > 0, '彩虹只喺 17–23 時出現（' + rainbow + ' 次）', rainbowBad);
  ok(cooldownBreakGuar.length / evTot < 0.05, '保底只喺別無選擇先破冷卻（' + cooldownBreakGuar.length + '/' + evTot + '）');
  // 忽略照顧嘅玩家（需求落到 20 底）→ 鬧脾氣（需持續 ≥2h）
  let gr = 0, grBad = 0;
  for (let seed = 1; seed <= 60; seed++) {
    const r = simulate(seed, 7, [8, 20], { noCare: true });
    r.recs.forEach(x => { if (x.id === 'grumpy') { gr++; } });
    const gs = r.recs.filter(x => x.id === 'grumpy'); for (let i = 1; i < gs.length; i++) if (gs[i].at - gs[i - 1].at < 48 * H - 1) grBad++;
  }
  console.log('    忽略照顧 60 個種子×7 日：鬧脾氣 ' + gr + ' 次');
  ok(gr > 0 && grBad === 0, '長期低需求 → 鬧脾氣出現，且冷卻 ≥ 48h', gr + '/' + grBad);
  ok(Object.keys(byId).filter(k => k !== 'flash').length === 7 && gr > 0, '事件池 9 個全部出現過（一般 7 個＋flash；grumpy 見上）', Object.keys(byId).join());
}

console.log('# 閃光日＝hash(存檔種子, 日期) 每日 3%');
{
  let flash = 0, days = 0;
  for (let seed = 1; seed <= 400; seed++) {
    const s = adult(seed * 7919); SIM.advance(s, 60, { hour: 6, now: BASE }, 30); const E = s.evs;
    for (let d = 0; d < 250; d++) { days++; if (E.flashToday) flash++; SIM.advance(s, 3600, { hour: 22, now: BASE + d * DAY + 22 * H * 1000 }, 3600); SIM.advance(s, 3600, { hour: 6, now: BASE + (d + 1) * DAY + 6 * H * 1000 }, 3600); }
  }
  const rate = flash / days;
  ok(Math.abs(rate - 0.03) < 0.004, '10 萬個存檔日內閃光日比率 ' + (rate * 100).toFixed(2) + '%（目標 3% ±0.4）', rate);
  // 防改日期：同種子＋同日期永遠同結果；重載（重算）唔會換
  const a = adult(5), b = adult(5);
  SIM.advance(a, 60, { hour: 9, now: BASE + 40 * DAY }, 30); SIM.advance(b, 60, { hour: 9, now: BASE + 40 * DAY }, 30);
  ok(a.evs.flashToday === b.evs.flashToday, '同種子同日期 → 閃光日結果一致（唔可以靠重載刷）');
  // 找一個閃光日 → 一定出閃光事件，且存檔還原後維持
  let seed = 1, f = null;
  for (; seed < 4000; seed++) { const t = adult(seed); SIM.advance(t, 60, { hour: 9, now: BASE }, 30); if (t.evs.flashToday) { f = t; break; } }
  ok(!!f, '搵到閃光日存檔（seed ' + seed + '）');
  const g0 = f.grains; SIM.advance(f, 4 * H, { hour: 10, now: BASE }, 60);
  ok(f.evs.hist.includes('flash') && EV.flashActive(f), '閃光日內出閃光事件');
  const r = SIM.deserialize(SIM.serialize(f), BASE + 100); ok(r.evs.flashToday === true && r.evs.flashDone === true, '閃光日狀態存檔還原');
  const g = D.EVENTS.find(e => e.id === 'flash'); ok(g.grains[0] >= 8, '閃光日獎勵 ≥ 8 光粒');
}


console.log('# 事件池權重表（遊策 v3）＋螢火散步');
{
  const W = {}; D.EVENTS.forEach(e => W[e.id] = e);
  console.log('    池：' + D.EVENTS.map(e => e.id + '(w' + e.weight + (e.hours ? ' ' + e.hours.join('-') : '') + (e.rare ? ' rare' : '') + (e.lowNeed ? ' lowNeed' : '') + ')').join(' '));
  ok(W.firefly_walk.weight === 20 && W.firefly_walk.hours.join() === '17,23' && W.firefly_walk.grains[0] === 5 && W.firefly_walk.grains[1] === 5 && W.firefly_walk.mood[0] === 10 && W.firefly_walk.mood[1] === 10, '螢火散步：傍晚 17–23、權重 20、✦+5、心情 +10');
  ok(W.firefly_walk.iconPlaceholder === undefined && W.firefly_walk.icon === 'firefly_walk' && W.firefly_walk.clipHint === 'play', '已用遊美真 icon（冇 placeholder）＋用現有 play clip');
  ok(W.rainbow.weight === 4 && W.rainbow.rare && W.meteor.rare && D.EVENTS.filter(e => e.rare && !e.special).length === 2, '彩虹權重 4；稀有＝流星夜＋彩虹');
  const cue = D.AUDIO.cues[D.AUDIO.eventCue.firefly_walk];
  ok(cue.file === D.AUDIO.cues.event_butterfly.file && Math.abs(cue.fixedRate - Math.pow(2, -3 / 12)) < 1e-9 && cue.temp === true, '音效：暫借蝴蝶提示音，playbackRate＝2^(-3/12)≈0.841（temp＝暫用）');
  const rec = (() => { const s = adult(5); SIM.advance(s, 60, { hour: 19, now: BASE }, 30); s.evs.flashToday = false; const g0 = s.grains, m0 = s.needs.mood; s.needs.mood = 50; const r = EV.force(s, 'firefly_walk'); return { r, dg: s.grains - g0, dm: s.needs.mood - 50 }; })();
  ok(rec.r.id === 'firefly_walk' && rec.dg === 5 && rec.dm === 10, '觸發獎勵：光粒 +5、心情 +10', JSON.stringify([rec.dg, rec.dm]));
  const v = EV.visual('firefly_walk', 2, 7); ok(v.flies.length === 5 && typeof v.rx === 'number', '視覺資料：5 隻螢火＋寵物跟隨 x');
  // 傍晚抽選份額（17–23 一般抽選）：螢火應佔大多數
  let ff = 0, all = 0, out = 0;
  for (let seed = 1; seed <= 300; seed++) { const s = adult(seed); SIM.advance(s, 60, { hour: 17, now: BASE }, 30); s.evs.flashToday = false; s.evs.next = 0; s.evs.cd = {}; s.evs.lastAt = -1e9;
    for (let i = 0; i < 6; i++) { s.evs.cd = {}; s.evs.lastAt = -1e9; s.evs.next = s.evs.clock; s.evs.dayCount = 0; const n = s.evs.hist.length; const before = s.evs.stats.events; EV.advance(s, 1, { hour: 17 + i, now: BASE }); if (s.evs.stats.events > before) { const id = s.evs.hist[s.evs.hist.length - 1]; all++; if (id === 'firefly_walk') ff++; } } }
  console.log('    傍晚命中事件中 firefly_walk 佔 ' + (ff / all * 100).toFixed(1) + '%（' + ff + '/' + all + '）');
  ok(ff / all > 0.45 && ff / all < 0.8, '傍晚命中事件中螢火散步佔多數（權重 20／池總權重）');
  let outside = 0, ffTot = 0;
  for (let seed = 1; seed <= 100; seed++) { const r = simulate(seed, 7, SESS); r.recs.forEach(x => { if (x.id === 'firefly_walk') { ffTot++; if (!(x.hour >= 17 && x.hour < 23)) outside++; } }); }
  ok(ffTot > 50 && outside === 0, '700 日內螢火散步只喺 17–23 出現（' + ffTot + ' 次）', outside);
}

console.log('# 閃光日「已領」旗標（claimedFlashDates，按日期，同日唔重領）');
{
  let f = null; for (let seed = 1; seed < 4000 && !f; seed++) { const t = adult(seed); SIM.advance(t, 60, { hour: 9, now: BASE }, 30); if (t.evs.flashToday) f = t; }
  const E0 = f.evs; ok(E0.claimedFlashDates.length === 0 && !EV.flashClaimed(E0), '領之前旗標空');
  SIM.advance(f, 4 * H, { hour: 10, now: BASE }, 60);
  const key = EV.dateKey(f.evs); ok(f.evs.claimedFlashDates.includes(key) && EV.flashClaimed(f.evs), '閃光事件觸發 → claimedFlashDates 記低日期 ' + key);
  const cnt = () => f.evs.log.filter(x => x.id === 'flash').length; ok(cnt() === 1, '當日閃光 ×1');
  const r = SIM.deserialize(SIM.serialize(f), BASE + 100); ok(r.evs.claimedFlashDates.join() === f.evs.claimedFlashDates.join(), '旗標隨存檔保存');
  r.evs.flashToday = true; r.evs.flashDone = false; r.evs.cd = {}; r.evs.lastAt = -1e9;     // 模擬「重載／改狀態想再領」
  SIM.advance(r, 6 * H, { hour: 14, now: BASE }, 60); ok(r.evs.log.filter(x => x.id === 'flash').length === 1, '同一日強行重置 flashToday／flashDone 都唔會再出閃光（已領）');
  // 實時日期：同日 hash 命中 → 領 → 重新載入同日 → 唔再出現；翌日（新日期）可再命中
  const T0 = new Date(2026, 5, 1, 9, 0, 0).getTime(); let seedF = null, nextHit = null;
  for (let sd = 1; sd < 20000 && !seedF; sd++) { const t = adult(sd); SIM.advance(t, 60, { hour: 9, now: T0 }, 30); if (t.evs.flashToday) seedF = sd; }
  const t = adult(seedF); SIM.advance(t, 60, { hour: 9, now: T0 }, 30); SIM.advance(t, 5 * H, { hour: 14, now: T0 + 5 * H * 1000 }, 60);
  ok(t.evs.log.some(x => x.id === 'flash') && t.evs.claimedFlashDates[0] === '2026-06-01', '實時日期鍵＝2026-06-01');
  const t2 = SIM.deserialize(SIM.serialize(t), T0 + 1000); EV.noteOpen(t2, { hour: 14.5, now: T0 + 5.5 * 3600e3 }); SIM.advance(t2, 3 * H, { hour: 16, now: T0 + 8 * H * 1000 }, 60);
  ok(t2.evs.log.filter(x => x.id === 'flash').length === 1 && EV.flashClaimed(t2.evs), '重載同日再玩 → 閃光只得 1 次（已領旗標）');
}

console.log('# 日記：螢火散步每條 +3 光粒（唔係 +5）');
{
  const s = adult(21); SIM.advance(s, 60, { hour: 19, now: BASE }, 30); s.evs.flashToday = false;
  const E = s.evs; const mk = (id) => ({ id, grains: 3, mood: 0, flavor: 'x', off: 'y', day: 0, at: 0, kind: 'draw', ts: BASE, offline: true, diary: true });
  E.diary.push(mk('firefly_walk'), mk('firefly_walk'), mk('gift'));
  const g = EV.diaryGroups(s).find(x => x.id === 'firefly_walk'); ok(g.n === 2 && g.grains === 6, '日記合併：螢火散步 ×2＝+6', JSON.stringify(g));
  const g0 = s.grains; const c = EV.claim(s, 'firefly_walk'); ok(c.n === 2 && s.grains - g0 === 6 && c.mood === 0, '領取螢火散步：每條 +3（共 +6），心情 0');
  // 真・離線路徑：傍晚離線 20 小時，溢出入日記嘅螢火散步 rec.grains 必須係 3（popup 嗰啲先係 5）
  let inDiary = 0, bad = 0, popupFF = 0; const pHit0 = P.drawChance; P.drawChance = 1; const dc0 = P.drawEveryH.slice(); P.drawEveryH[0] = P.drawEveryH[1] = 1;     // 臨時 p_hit＝1、每小時抽，確保溢出入日記
  for (let sd = 1; sd <= 400; sd++) {
    const t = adult(sd), T1 = new Date(2026, 5, 5, 17, 0, 0).getTime(); t.lastSeen = T1; t.createdAt = T1 - 9e9; SIM.advance(t, 30, { hour: 17, now: T1 }, 30);
    t.lastSeen = T1; const rep = SIM.applyOffline(t, T1 + 20 * H * 1000);
    t.evs.diary.forEach(d => { if (d.id === 'firefly_walk') { inDiary++; if (d.grains !== 3 || d.mood !== 0) bad++; } });
    t.evs.offLog.forEach(d => { if (d.id === 'firefly_walk' && !d.diary) popupFF++; });
  }
  P.drawChance = pHit0; P.drawEveryH[0] = dc0[0]; P.drawEveryH[1] = dc0[1];
  console.log('    離線 400 局：入日記螢火 ' + inDiary + ' 條；彈出螢火 ' + popupFF + ' 條');
  ok(inDiary > 5 && bad === 0, '離線溢出入日記嘅螢火散步：全部 grains＝3、mood＝0', inDiary + '/' + bad);
}

console.log('# lastSaveTime：系統時間早於存檔時間 → 當日唔抽閃光日同事件');
{
  const T0 = new Date(2026, 5, 10, 12, 0, 0).getTime();
  const s = adult(5); SIM.advance(s, 60, { hour: 12, now: T0 }, 30);
  EV.markSave(s, T0 + 3 * H * 1000); ok(s.lastSaveTime === T0 + 3 * H * 1000, 'markSave 記低 lastSaveTime');
  EV.markSave(s, T0); ok(s.lastSaveTime === T0 + 3 * H * 1000, 'lastSaveTime 只增唔減（回撥唔可拉低）');
  const r = SIM.deserialize(SIM.serialize(s), T0 + 10); ok(r.lastSaveTime === s.lastSaveTime, 'lastSaveTime 隨存檔保存');
  // 回撥：now = T0 - 5h（10 日 07:00）
  const tN = T0 - 5 * H * 1000;
  r.evs.next = r.evs.clock + 1; r.evs.dayCount = 0; r.evs.gDone = false; r.evs.lastAt = -1e9; r.evs.flashToday = true; r.evs.flashDone = false; r.evs.cd = {};
  const rec = EV.noteOpen(r, { hour: 7, now: tN }); ok(rec === null && r.evs.dayCount === 0 && EV.suppressed(r, r.evs), '回撥後開 app：唔觸發保底，標記 suppressed');
  const n0 = r.evs.stats.events;
  for (let i = 0; i < 12; i++) SIM.advance(r, H, { hour: 7 + i * 0.1, now: tN + i * 600e3 }, 60);
  ok(r.evs.stats.events === n0 && r.evs.dayCount === 0, '回撥期間 12 小時有效時間：零事件（含抽選／保底）', r.evs.stats.events - n0);
  ok(!r.evs.log.some(x => x.id === 'flash') && r.evs.flashDone === false, '回撥當日：閃光日唔觸發（即使 flashToday 為 true）');
  // 時間追返過 lastSaveTime 但仍同一日：noDrawDay 仍然生效
  SIM.advance(r, 2 * H, { hour: 16, now: T0 + 4 * H * 1000 }, 60);
  ok(r.evs.stats.events === n0, '追返 lastSaveTime 但仍係回撥嗰日：繼續唔抽');
  // 翌日（本機日序號前進）→ 恢復
  const nextDay = T0 + 24 * H * 1000;
  EV.markSave(r, T0 + 4 * H * 1000);
  const rec2 = EV.noteOpen(r, { hour: 9, now: nextDay }); ok(!EV.suppressed(r, r.evs) && !!rec2, '翌日（時間 > lastSaveTime）→ 恢復，首次開 app 保底觸發');
  // 新一日嘅閃光日 roll 唔受 suppress 影響（正常時間）
  let hit = 0; for (let sd = 1; sd < 3000; sd++) { const t = adult(sd); SIM.advance(t, 60, { hour: 9, now: T0 }, 30); if (t.evs.flashToday) hit++; } ok(hit > 30 && hit < 130, '正常時間：閃光日照常約 3%（' + hit + '/2999）');
  // 回撥日 roll 新日：suppress → 閃光日 false
  let flashSup = 0;
  for (let sd = 1; sd < 3000; sd++) { const t = adult(sd); t.lastSaveTime = T0 + 10 * H * 1000; SIM.advance(t, 60, { hour: 9, now: T0 }, 30); if (t.evs.flashToday) flashSup++; }
  ok(flashSup === 0, '系統時間早於 lastSaveTime：開局判定閃光日 0/2999（正常約 3%）');
}

console.log('# 防改時鐘三點（UTC 比較）：容差 120 秒／lastSaveTime > now+24h 無效／前撥與改時區 M1 唔處理');
{
  ok(P.lastSaveTolSec === 120 && P.lastSaveMaxAheadH === 24, '參數：lastSaveTolSec 120、lastSaveMaxAheadH 24');
  const T0 = Date.UTC(2026, 5, 10, 4, 0, 0);          // UTC 04:00
  const mk = (seed) => { const s = adult(seed); SIM.advance(s, 60, { hour: 12, now: T0 }, 30); s.lastSaveTime = T0; s.evs.flashToday = false; return s; };
  // ① 容差
  let a = mk(1); EV.noteOpen(a, { hour: 12, now: T0 - 60e3 }); ok(!EV.suppressed(a, a.evs) && a.evs.noDrawDay === null, '① 早 60 秒（網絡校時）→ 唔判篡改');
  a = mk(1); EV.noteOpen(a, { hour: 12, now: T0 - 120e3 }); ok(!EV.suppressed(a, a.evs), '① 早剛好 120 秒 → 唔判篡改（邊界）');
  a = mk(1); const rr = EV.noteOpen(a, { hour: 12, now: T0 - 121e3 }); ok(EV.suppressed(a, a.evs) && rr === null && a.evs.dayCount === 0, '① 早 121 秒 → 判回撥：當日唔抽、唔保底');
  const ok2 = mk(3); const r2 = EV.noteOpen(ok2, { hour: 12, now: T0 - 30e3 }); ok(!!r2 && ok2.evs.dayCount === 1, '① 容差內：首次開 app 正常觸發保底');
  // UTC 日：回撥跨 UTC 午夜，noDrawDay＝UTC 日序號
  a = mk(1); const tb = T0 - 6 * H * 1000; EV.noteOpen(a, { hour: 22, now: tb });
  ok(a.evs.noDrawDay === Math.floor(tb / 86400e3), '回撥日以 UTC 日序號記錄（' + a.evs.noDrawDay + '）');
  // ② lastSaveTime > now+24h → 無效
  const f = adult(7); f.lastSeen = T0 - 3 * H * 1000; f.lastSaveTime = T0 + 30 * 24 * H * 1000;      // 曾撥前 30 日再改返
  const need0 = f.needs.hunger, gr0 = f.grains;
  const rep = SIM.applyOffline(f, T0);
  ok(rep.tampered === true && f.lastSaveTime === T0 && f.lastSeen === T0 && rep.T === 0 && rep.E === 0, '② lastSaveTime > now+24h → 重設為 now，離線時長 0（唔派離線獎）', JSON.stringify([rep.tampered, rep.T, rep.E]));
  ok(f.grains === gr0 && f.needs.hunger === need0 && (f.evs ? f.evs.offLog.length : 0) === 0, '② 該段冇離線事件／光粒／需求變化');
  ok(f.saveTimeResets === 1, '② 記錄重設次數');
  const g = adult(7); g.lastSeen = T0 - 3 * H * 1000; g.lastSaveTime = T0 + 23 * H * 1000; const rg = SIM.applyOffline(g, T0);
  ok(rg.tampered === false && g.lastSaveTime === T0 + 23 * H * 1000 && rg.T === 3 * H, '② 剛好 +23h（≤24h）→ 唔當無效，離線照派');
  const h2 = adult(8); SIM.advance(h2, 60, { hour: 12, now: T0 }, 30); h2.lastSaveTime = T0 + 40 * H * 1000;
  EV.noteOpen(h2, { hour: 12, now: T0 }); ok(h2.lastSaveTime === T0 && !EV.suppressed(h2, h2.evs), '② 開 app 時 lastSaveTime > now+24h → 重設，唔當回撥、唔 suppress');
  const g2 = adult(7); g2.lastSeen = T0 - 3 * H * 1000; g2.lastSaveTime = T0 + 24 * H * 1000 + 1; ok(SIM.applyOffline(g2, T0).tampered === true, '② 邊界：+24h+1ms → 無效');
  // ③ 前撥（≤24h）／改時區：唔處理（M1）
  const fw = mk(4); EV.noteOpen(fw, { hour: 18, now: T0 + 20 * H * 1000 }); ok(!EV.suppressed(fw, fw.evs), '③ 前撥 20 小時：M1 唔處理（唔 suppress）');
  const tz = mk(5); EV.noteOpen(tz, { hour: 20, now: T0 + 60e3 }); ok(!EV.suppressed(tz, tz.evs), '③ 改時區（UTC ms 不變、本機 hour 跳變）：唔受影響');
  // markSave 只增唔減；存檔往返保持
  EV.markSave(a, T0 + 5); ok(a.lastSaveTime === T0 + 5, 'markSave 前進');
  // 抽選回撥：zero events（p_hit=1）
  const q = mk(9); const pc = P.drawChance; P.drawChance = 1; const de = P.drawEveryH.slice(); P.drawEveryH[0] = P.drawEveryH[1] = 0.5;
  EV.noteOpen(q, { hour: 10, now: T0 - 600e3 }); const n0 = q.evs.stats.events; for (let i = 0; i < 20; i++) SIM.advance(q, 1800, { hour: 10 + i / 2, now: T0 - 600e3 + i * 1800e3 - 0 }, 60);
  P.drawChance = pc; P.drawEveryH[0] = de[0]; P.drawEveryH[1] = de[1];
  ok(q.evs.noDrawDay === Math.floor((T0 - 600e3) / 86400e3) && q.evs.stats.events === n0, '回撥日（UTC 日）p_hit=1、10 小時：零事件，即使時間追過 lastSaveTime', q.evs.stats.events - n0);
}

console.log('# 保底（16:00 後／當日第 1 次開 app 即觸發）');
{
  const s = adult(3); SIM.advance(s, 60, { hour: 8, now: BASE }, 30); s.evs.flashToday = false; s.evs.next = 1e12;   // 禁止抽選，只剩保底
  SIM.advance(s, 3 * H, { hour: 14, now: BASE }, 60); ok(s.evs.dayCount === 0, '16:00 前（draw 被禁）仍冇事件');
  SIM.advance(s, 60, { hour: 16.1, now: BASE }, 30); ok(s.evs.dayCount === 1 && s.evs.stats.guarantee === 1, '16:00 後觸發保底');
  SIM.advance(s, 3 * H, { hour: 20, now: BASE }, 60); ok(s.evs.dayCount === 1, '保底每日只一次');
  const t = adult(4); SIM.advance(t, 60, { hour: 9, now: BASE }, 30); t.evs.flashToday = false; t.evs.next = 1e12;
  const rec = EV.noteOpen(t, { hour: 9, now: BASE }); ok(!!rec && t.evs.dayCount === 1 && t.evs.stats.guaranteeOpen === 1, '當日第 1 次開 app（冇事件）→ 即觸發保底');
  EV.noteOpen(t, { hour: 9.5, now: BASE + 1800e3 }); ok(t.evs.dayCount === 1 && t.evs.stats.guaranteeOpen === 1, '第 2 次開 app 唔再觸發（保底每日一次）');
  const u = adult(4); SIM.advance(u, 60, { hour: 9, now: BASE }, 30); u.evs.next = 1e12; u.evs.flashToday = false; u.evs.dayCount = 1;
  EV.noteOpen(u, { hour: 9, now: BASE }); EV.noteOpen(u, { hour: 9.2, now: BASE }); ok(u.evs.dayCount === 1, '當日已有事件 → 開 app 唔再觸發');
  const gp = adult(9); SIM.advance(gp, 60, { hour: 17, now: BASE }, 30); gp.evs.next = 1e12; gp.evs.lastAt = gp.evs.clock - 10; gp.evs.dayCount = 0; gp.evs.gDone = false; gp.evs.flashToday = false;
  SIM.advance(gp, 5, { hour: 17, now: BASE }, 5); ok(gp.evs.dayCount === 0 && !gp.evs.gDone, '20 分鐘間隔未夠 → 保底延後（唔浪費）');
  SIM.advance(gp, 1300, { hour: 17.4, now: BASE }, 60); ok(gp.evs.dayCount === 1, '間隔夠咗之後保底觸發');
}

console.log('# 鬧脾氣＝任一需求 <30 持續 ≥ 2 小時（有效時間）');
{
  const s = adult(21); SIM.advance(s, 60, { hour: 12, now: BASE }, 30); const E = s.evs; E.next = 1e12; E.flashToday = false;
  const g = D.EVENTS.find(e => e.id === 'grumpy');
  s.needs.hunger = 20; SIM.advance(s, 3600 + 600, { hour: 12, now: BASE }, 60); s.needs.hunger = 20;
  ok(!EV.condOk(g, s, 13, E), '低需求 1 小時多：未符合條件（需 2 小時）');
  s.needs.hunger = 20; SIM.advance(s, 3600, { hour: 14, now: BASE }, 60); s.needs.hunger = 20;
  const t = adult(22); SIM.advance(t, 60, { hour: 12, now: BASE }, 30); t.evs.low = 7300; ok(EV.condOk(g, t, 12, t.evs), '低需求 ≥2h → 條件符合');
  t.needs.hunger = 90; t.evs.low = 0; ok(!EV.condOk(g, t, 12, t.evs), '需求回升 → 累積歸零');
  // 只喺條件符合先出，冷卻 48h
  const u = adult(23); SIM.advance(u, 60, { hour: 12, now: BASE }, 30); u.evs.flashToday = false; u.evs.low = 7300; u.evs.hist = [];
  EV.force(u, 'grumpy'); ok(u.evs.cd.grumpy - u.evs.clock === 48 * H, '鬧脾氣事件冷卻 48 小時');
  EV.force(u, 'meteor'); ok(u.evs.cd.meteor - u.evs.clock === 72 * H, '流星夜（稀有）冷卻 72 小時');
}

console.log('# 離線：唔傷害、最多彈 2、其餘入日記、日記領取');
{
  let harmed = 0, runs = 0, maxPop = 0, diarySum = 0, sumLines = 0, bad = 0;
  for (let seed = 1; seed <= 120; seed++) {
    const mk = (on) => { const s = adult(seed); s.lastSeen = BASE; Object.assign(s.needs, { hunger: 70, mood: 70, clean: 70, energy: 70 }); EV.enabled = on; return s; };
    const A = mk(true); const repA = SIM.applyOffline(A, BASE + 20 * H * 1000);
    const B = mk(false); SIM.applyOffline(B, BASE + 20 * H * 1000); EV.enabled = true;
    runs++;
    for (const k of ['hunger', 'mood', 'clean', 'energy']) if (A.needs[k] < B.needs[k] - 1e-6) harmed++;
    if (A.grains < B.grains || A.stage !== B.stage) harmed++;
    maxPop = Math.max(maxPop, repA.popups); diarySum += repA.diaryNew;
    if (repA.summary.length > 3) sumLines++;
    if (/扣|罰|懲|冇人理|唔理|病|死/.test(repA.summary.join(''))) bad++;
  }
  ok(harmed === 0, '開／閂事件各 120 個種子：離線後需求、光粒、階段，有事件嘅永遠 ≥ 冇事件（零傷害）', harmed);
  ok(maxPop <= P.offlinePopupMax, '離線最多彈出 ' + P.offlinePopupMax + ' 個（最大 ' + maxPop + '）');
  ok(sumLines === 0 && bad === 0, '離線摘要 ≤ 3 句、冇懲罰字眼', sumLines + '/' + bad);
  // 多事件離線 → 溢出入日記（搵一個會溢出嘅種子）
  let found = null;
  for (let seed = 1; seed < 400 && !found; seed++) { const s = adult(seed); s.lastSeen = BASE; const g0 = s.grains; const rep = SIM.applyOffline(s, BASE + 24 * H * 1000); if (rep.diaryNew > 0) found = { s, rep, seed, g0 }; }
  ok(!!found, '有種子離線事件 >2 個 → 溢出入日記（seed ' + (found && found.seed) + '）');
  if (found) {
    const { s, rep } = found, E = s.evs;
    ok(rep.popups === 2 && E.diary.length === rep.diaryNew, '彈 2 個＋日記 ' + rep.diaryNew + ' 條', rep.popups);
    ok(E.diary.every(d => d.grains === 3 && d.mood === 0 && d.diary), '日記條目：每條 ✦3、冇心情（領咗先入帳）');
    const popG = E.pending.reduce((a, r) => a + r.grains, 0);
    ok(s.grains === found.g0 + rep.gift + popG, '未領日記唔計入光粒（只有禮物＋彈出事件）', s.grains - found.g0 + ' vs ' + (rep.gift + popG));
    ok(rep.summary.length <= 3 && /日記/.test(rep.summary.join('')), '摘要提到日記、≤3 句：' + rep.summary.join(' / '));
    const before = s.grains, n = E.diary.length; const r = EV.claim(s); ok(r.grains === Math.min(60, n * 3) && s.grains === before + r.grains, '領取後先入帳');
  }
}

console.log('# 日記：合併、每條 +3、上限 60、14 日過期、12 日提示');
{
  const s = adult(41); SIM.advance(s, 60, { hour: 9, now: BASE }, 30); const E = s.evs;
  const mk = (id, ts) => ({ id, grains: 3, mood: 0, flavor: 'x', off: 'x', day: 0, at: 0, kind: 'draw', ts, offline: true, diary: true });
  const now = BASE + 30 * DAY;
  E.diary = [mk('gift', now - 13 * DAY), mk('gift', now - 2 * DAY), mk('treasure', now - 1 * DAY), mk('butterfly', now - 15 * DAY)];
  ok(EV.pruneDiary(s, now) === 1 && E.diary.length === 3, '超過 14 日嘅條目過期（移除 1 條）');
  ok(EV.diaryWarn(s, now) === 1, '第 12 日起提示：1 條（13 日前）快過期');
  const gp = EV.diaryGroups(s); ok(gp.length === 2 && gp.find(x => x.id === 'gift').n === 2 && gp.find(x => x.id === 'gift').grains === 6, '同類合併（gift ×2＝✦6）');
  const g0 = s.grains; let r = EV.claim(s, 'gift'); ok(r.n === 2 && r.grains === 6 && s.grains === g0 + 6 && E.diary.length === 1, '按類領取：+6 光粒、剩 1 條');
  E.diary = []; for (let i = 0; i < 30; i++) E.diary.push(mk('gift', now));
  const g1 = s.grains; r = EV.claim(s); ok(r.grains === 60 && r.n === 20 && r.left === 10 && s.grains === g1 + 60, '一鍵領取單次上限 60（20 條），餘 10 條留低');
  r = EV.claim(s); ok(r.grains === 30 && E.diary.length === 0, '再領一次領走餘下 10 條（+30）');
  ok(E.diary.length === 0 && EV.claim(s).n === 0, '日記領空後再領＝0');
  // 唔領就唔計獎勵
}

console.log('# 事件獎勵只加唔減；存檔續玩一致');
{
  const a = simulate(5, 3, SESS);
  ok(a.recs.every(r => r.grains >= 0 && r.mood >= 0), '所有事件 grains／mood ≥ 0');
  // 存檔中途還原 → 同未存檔嘅後續序列一致
  const s1 = adult(77), s2 = adult(77); const run = (s, t0, n) => { const out = []; const f = (st, r) => { if (st === s) out.push(r.id + ':' + Math.round(r.at)); }; EV.listeners.push(f); for (let i = 0; i < n; i++) { SIM.advance(s, 600, { hour: (8 + (t0 + i) * 600 / 3600) % 24, now: BASE + (t0 + i) * 600e3 }, 60); while (EV.takePending(s)) { } } EV.listeners.splice(EV.listeners.indexOf(f), 1); return out; };
  const full = run(s1, 0, 400);
  const part1 = run(s2, 0, 150); const s3 = SIM.deserialize(SIM.serialize(s2), BASE); const part2 = run(s3, 150, 250);
  ok(JSON.stringify(full) === JSON.stringify(part1.concat(part2)), '中途序列化／還原後，事件序列同一氣呵成一致（' + full.length + ' 個）');
}

console.log('# 遊美事件 icon（atlas_events）');
{
  const fsx = require('fs'), pth = require('path');
  const A = JSON.parse(fsx.readFileSync(pth.join(__dirname, '../art/atlas_events.json'), 'utf8'));
  ok(A.meta.size.w <= 1024 && A.meta.size.h <= 1024 && fsx.existsSync(pth.join(__dirname, '../art/atlas_events.png')), 'atlas_events ≤1024×1024，png 存在');
  const defs = D.EVENTS; const noIcon = defs.filter(e => !e.icon || !A.animations[e.icon]);
  ok(defs.length === 9 && noIcon.length === 0, '9 個事件全部有 icon 動畫', noIcon.map(e => e.id).join());
  const map = {}; defs.forEach(e => map[e.id] = e.icon);
  const exp = { gift: 'gift_return', butterfly: 'butterfly', meteor: 'meteor_night', rainbow: 'rainbow', sleeptalk: 'sleep_talk', grumpy: 'tantrum', treasure: 'treasure', flash: 'shiny_day', firefly_walk: 'firefly_walk' };
  ok(Object.keys(exp).every(k => map[k] === exp[k]), 'id→icon 對應（EVENT_ICONS.md）');
  const bad = []; defs.forEach(e => { const an = A.animations[e.icon]; an.frames.forEach(f => { const fr = A.frames[f]; if (!fr || fr.frame.w !== 32 || fr.frame.h !== 32) bad.push(f); }); });
  ok(bad.length === 0, 'icon 每幀 32×32', bad.join());
  ok(defs.every(e => A.animations[e.icon].fps > 0 && A.animations[e.icon].frames.length >= 2), '每個 icon 動畫 ≥2 幀、fps>0');
  ok(!defs.some(e => e.iconPlaceholder) && !/iconPlaceholder|◌/.test(fsx.readFileSync(pth.join(__dirname, '../src/ui.js'), 'utf8')), '已冇 icon placeholder／◌ 前綴');
}

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
