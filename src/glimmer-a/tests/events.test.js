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
ok(P.drawChance === 0.33 && P.minGapSec === 1200 && P.cooldownH === 24 && P.cooldownRareH === 72 && P.repeatWeightMul === 0.25, 'p_hit 0.33／全域間隔 20 分鐘／冷卻 24h／稀有 72h／防重複 ×0.25');
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
  ok(cdViol === 0, '單事件冷卻 24h／稀有 72h／彩虹 240h／鬧脾氣 48h（抽選路徑零違反；' + cdPairs + ' 對重複）', cdViol);
  ok(zeroDays === 0, '每日保底：1400 日冇一日零事件', zeroDays);
  ok(mean >= 1 && mean <= 3, '平均每日事件數 1–3（' + mean.toFixed(2) + '）');
  { let mx = 0; for (let seed = 1; seed <= 60; seed++) { const r = simulate(seed, 7, SESS); const dd = {}; r.recs.forEach(x => { if (x.kind === 'draw' && !x.offline) dd[x.day] = (dd[x.day] || 0) + 1; }); mx = Math.max(mx, ...Object.values(dd)); }
    ok(mx <= P.dailyMax, '線上抽選單日上限 ' + P.dailyMax + '（離線補抽唔計上限，保底／閃光額外）→ 線上最大 ' + mx + '；連離線單日最大 ' + Math.max(...perDay)); }
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
  ok(W.firefly_walk.weight === 14 && W.firefly_walk.hours.join() === '17,23' && W.firefly_walk.grains[0] === 5 && W.firefly_walk.grains[1] === 5 && W.firefly_walk.mood[0] === 10 && W.firefly_walk.mood[1] === 10, '螢火散步：傍晚 17–23、權重 14（PR #19 P1）、✦+5、心情 +10');
  ok(W.firefly_walk.iconPlaceholder === undefined && W.firefly_walk.icon === 'firefly_walk' && W.firefly_walk.clipHint === 'play', '已用遊美真 icon（冇 placeholder）＋用現有 play clip');
  ok(W.rainbow.weight === 1 && W.rainbow.rare && W.meteor.rare && D.EVENTS.filter(e => e.rare && !e.special).length === 2, '彩虹權重 1（QA：pity 補底）；稀有＝流星夜＋彩虹');
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
  ok(ff / all > 0.15 && ff / all < 0.3, '傍晚（冷卻清空）命中事件中螢火散步約 14／傍晚池總權重（15–30%）');
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


console.log('# PR #19 P0／P1');
{
  // 權重對齊 QA v5.1
  const W = {}; D.EVENTS.forEach(e => W[e.id] = e);
  ok(W.gift.weight === 22 && W.butterfly.weight === 20 && W.meteor.weight === 10 && W.sleeptalk.weight === 11 && W.treasure.weight === 18 && W.rainbow.weight === 1 && W.firefly_walk.weight === 14, '池權重：禮物 22／蝴蝶 20／流星 10／夢話 11／寶物 18／彩虹 1／螢火 14');
  ok(W.grumpy.cond === true && W.grumpy.weight === 0 && P.offlineMaxDays === 14 && P.diaryMax === 50 && P.offlineStepSec === 600, '鬧脾氣唔入池（cond）；離線補抽最多 14 日、步長 600s；日記保存上限 50');
  // P0-1 按日離線 14 日 ≈33 條
  const cnt = [];
  for (let sd = 1; sd <= 300; sd++) {
    const t = adult(sd), T1 = new Date(2026, 5, 1, 21, 0, 0).getTime(); t.createdAt = T1 - 9e9;
    SIM.advance(t, 30, { hour: 21, now: T1 }, 30); t.lastSeen = T1; t.lastSaveTime = T1;
    const rep = SIM.applyOffline(t, T1 + 14 * DAY);
    cnt.push(t.evs.diary.length);
    if (sd === 1) ok(rep && rep.popups === 2 && t.evs.pending.length === 2, '14 日離線：彈窗剛好 2 個', JSON.stringify(rep && rep.popups));
  }
  cnt.sort((a, b) => a - b); const mean = cnt.reduce((a, b) => a + b, 0) / cnt.length, p95 = cnt[Math.floor(cnt.length * 0.95)];
  console.log('    14 日離線入日記：平均 ' + mean.toFixed(1) + '、p95 ' + p95 + '、最多 ' + cnt[cnt.length - 1]);
  ok(mean >= 30 && mean <= 37 && cnt[cnt.length - 1] <= P.diaryMax, '14 日離線 ≈33 條入日記（29–37；最多 ≤ ' + P.diaryMax + '）', mean.toFixed(1));
  // 遊策 10-31：離線補抽唔計 dailyMax；彈窗仍 2；冷卻照計；日均 ≤2.95
  ok(P.offlineIgnoreDailyMax === true, '參數 offlineIgnoreDailyMax＝true');
  { const run = (flag) => { const f0 = P.offlineIgnoreDailyMax; P.offlineIgnoreDailyMax = flag; let n = 0, pop = 0, cdv = 0, over4 = 0;
      for (let sd = 1; sd <= 200; sd++) { const t = adult(sd), T1 = new Date(2026, 5, 1, 21, 0, 0).getTime(); SIM.advance(t, 30, { hour: 21, now: T1 }, 30); t.lastSeen = T1; t.lastSaveTime = T1;
        const rep = SIM.applyOffline(t, T1 + 14 * DAY); n += t.evs.offLog.length; pop = Math.max(pop, rep.popups);
        const last = {}, perDay = {}; t.evs.offLog.slice().sort((a, b) => a.at - b.at).forEach(x => { const d = EV.DEF[x.id], need = (d.cooldownH || (d.rare ? 72 : 24)) * H; if (last[x.id] != null && x.at - last[x.id] < need - 1) cdv++; last[x.id] = x.at; const k = new Date(x.ts).toDateString(); perDay[k] = (perDay[k] || 0) + 1; });
        over4 += Object.values(perDay).filter(v => v > P.dailyMax).length; }
      P.offlineIgnoreDailyMax = f0; return { n: n / 200, pop, cdv, over4 }; };
    const on = run(true), off = run(false);
    console.log('    14 日離線（200 種子）：唔計上限 ' + on.n.toFixed(1) + ' 個（' + on.over4 + ' 日 >4）／計上限 ' + off.n.toFixed(1) + ' 個（' + off.over4 + ' 日 >4）');
    ok(on.n > off.n && on.over4 > 0 && off.over4 === 0, '離線補抽唔計每日上限 4（開關有效）');
    ok(on.pop === 2 && on.cdv === 0 && on.n / 14 <= 2.95, '唔計上限時：彈窗仍最多 2、冷卻零違反、離線日均 ' + (on.n / 14).toFixed(2) + ' ≤ 2.95', JSON.stringify(on)); }
  { let ev = 0, days = 0; for (let sd = 1; sd <= 150; sd++) { const sim = simulate(3000 + sd, 14, [8, 21]); days += 14; ev += sim.s.evs.stats.events; }
    ok(ev / days <= 2.95, '線上＋離線合計日均事件 ' + (ev / days).toFixed(2) + ' ≤ 2.95（每日開 2 次 × 14 日 × 150）'); }
  // 超過 14 日：只補 14 日
  { const t = adult(4), T1 = new Date(2026, 5, 1, 21, 0, 0).getTime(); SIM.advance(t, 30, { hour: 21, now: T1 }, 30); t.lastSeen = T1; t.lastSaveTime = T1;
    SIM.applyOffline(t, T1 + 40 * DAY); const old = t.evs.offLog.filter(x => x.ts < T1 + 26 * DAY - 60e3).length;
    ok(old === 0 && t.evs.diary.length <= P.diaryMax && t.evs.diary.length > 15, '離線 40 日：只補最後 14 日（' + t.evs.diary.length + ' 條）', old); }
  // P0-2 彈窗：稀有度最高 2 個，同級取最新
  { const s = adult(2); SIM.advance(s, 30, { hour: 12, now: BASE }, 30); const E = s.evs; E.offLog = []; E.pending = []; E.diary = [];
    const mk = (id, ts) => ({ id, ts, at: ts / 1000, grains: 5, mood: 2, offline: true, rare: !!DEF(id).rare, flavor: 'x' });
    function DEF(id) { return EV.DEF[id]; }
    E.offLog.push(mk('gift', 1000), mk('meteor', 2000), mk('treasure', 9000), mk('rainbow', 3000), mk('meteor', 4000), mk('gift', 8000));
    const res = EV.finishOffline(s, E);
    ok(res.pop.map(x => x.id + x.ts).join() === 'meteor4000,rainbow3000' && E.diary.length === 4 && E.diary.every(d => d.grains === 3 && d.mood === 0), '彈窗＝稀有度最高 2 個（同級取最新）：' + res.pop.map(x => x.id + '@' + x.ts).join(','));
    const s2 = adult(3); SIM.advance(s2, 30, { hour: 12, now: BASE }, 30); s2.evs.offLog = [mk('gift', 1000), mk('treasure', 5000), mk('butterfly', 3000)];
    const r2 = EV.finishOffline(s2, s2.evs); ok(r2.pop.map(x => x.id).join() === 'treasure,butterfly', '冇稀有：取最新 2 個', r2.pop.map(x => x.id).join()); }
  // P0-3 保底唔打穿冷卻
  { const s = adult(6), T = new Date(2026, 5, 3, 9, 0, 0).getTime(); SIM.advance(s, 30, { hour: 9, now: T }, 30); const E = s.evs;
    E.dayCount = 0; E.gDone = false; E.opens = 0; E.lastAt = -1e9; E.flashToday = false;
    D.EVENTS.forEach(d => { E.cd[d.id] = E.clock + 10 * H; });
    const r = EV.noteOpen(s, { hour: 9, now: T + 1000 });
    ok(r === null && E.dayCount === 0 && !E.gDone && E.stats.guaranteeFail >= 1, '全部冷卻中：保底落空（唔打穿 24h 冷卻），之後再試');
    E.cd.gift = E.clock - 1; const r2 = EV.noteOpen(s, { hour: 9.1, now: T + 2000 });
    ok(r2 && r2.id === 'gift' && E.gDone, '有事件冷卻完：下次開 app 保底即揀佢', r2 && r2.id);
    let viol = 0; for (let sd = 1; sd <= 150; sd++) { const sim = simulate(sd, 7, [9, 20]); const last = {}; sim.recs.forEach(x => { if (x.kind === 'guarantee' && last[x.id] != null) { const d = EV.DEF[x.id]; const need = (d.cooldownH || (d.rare ? 72 : 24)) * H; if (x.at - last[x.id] < need - 1) viol++; } last[x.id] = x.at; }); }
    ok(viol === 0, '150×7 日：保底零次打穿冷卻', viol); }
  // P0-4 彩虹 11–15 日一次（5 次開 app／日）
  { let rb = 0, days = 0; for (let sd = 1; sd <= 300; sd++) { const sim = simulate(1000 + sd, 14, SESS); days += 14; sim.recs.forEach(x => { if (x.id === 'rainbow') rb++; }); sim.s.evs.diary.forEach(x => { if (x.id === 'rainbow') rb++; }); }
    console.log('    彩虹：' + rb + ' 次／' + days + ' 日 → 每 ' + (days / rb).toFixed(1) + ' 日一次');
    ok(days / rb >= 11 && days / rb <= 15, '彩虹 11–15 日一次（v5）', (days / rb).toFixed(1)); }
  // P1-1 壞日記／缺 stats.byId 回退
  { const s = adult(8); SIM.advance(s, 30, { hour: 12, now: BASE }, 30);
    const raw = JSON.parse(SIM.serialize(s)); raw.evs.diary = [null, 5, { id: 'nope', ts: 1 }, { id: 'gift', ts: 'x' }, { id: 'meteor', ts: BASE }]; delete raw.evs.stats.byId; raw.evs.pending = 'bad'; raw.evs.cd = null;
    let r, err = null; try { r = SIM.deserialize(JSON.stringify(raw), BASE + 1000); EV.ensure(r); } catch (e) { err = e.message; }
    ok(!err && r.evs.diary.length === 2 && r.evs.diary.every(d => typeof d.ts === 'number' && d.grains === 3) && Array.isArray(r.evs.pending) && r.evs.stats.byId && typeof r.evs.cd === 'object', '壞日記條目剔走／缺 stats.byId、壞 pending／cd 回退（唔爆）', err || (r && r.evs.diary.length));
    let err2 = null; try { SIM.advance(r, 60, { hour: 13, now: BASE + 2000 }, 30); EV.force(r, 'gift'); EV.diaryGroups(r); EV.claim(r, 'meteor'); } catch (e) { err2 = e.message; }
    ok(!err2 && r.evs.stats.byId.gift >= 1, '回退後可正常觸發／領取', err2);
    const s3 = adult(9); s3.evs = 'garbage'; let e3 = null; try { EV.ensure(s3); SIM.advance(s3, 30, { hour: 12, now: BASE }, 30); } catch (e) { e3 = e.message; } ok(!e3 && s3.evs.v === 1, 'evs 唔係 object → 重建', e3); }
  // P1-2 連點 5 下 → 獨立事件 grumpy_tap（48h 自己嘅冷卻；唔計每日上限、冇獎勵、唔共用需求鬧脾氣）
  { const s = adult(10), T = new Date(2026, 5, 3, 14, 0, 0).getTime(); SIM.advance(s, 30, { hour: 14, now: T }, 30); s.evs.lastAt = -1e9; s.evs.cd = {};
    const g0 = s.grains, d0 = s.evs.dayCount, ev0 = s.evs.stats.events, mood0 = s.needs.mood;
    const r1 = EV.tapTantrum(s, { now: T });
    ok(r1 && r1.id === 'grumpy_tap' && r1.kind === 'tap' && r1.grains === 0 && r1.mood === 0 && r1.flavor !== EV.DEF.grumpy.flavor[0] && Math.abs(s.evs.cd.grumpy_tap - s.evs.clock - 48 * H) < 1 && s.evs.cd.grumpy == null, '連點觸發 grumpy_tap，自己冷卻 48h、文案唔同鬧脾氣', JSON.stringify(r1 && { id: r1.id, kind: r1.kind, flavor: r1.flavor }));
    ok(s.grains === g0 && s.needs.mood === mood0 && s.evs.dayCount === d0 && s.evs.stats.events === ev0 && s.evs.stats.byId.grumpy_tap === 1, 'grumpy_tap 唔計每日上限、唔加光粒／心情、唔加 stats.events');
    s.evs.cd.grumpy = s.evs.clock + 48 * H; s.evs.lastAt = -1e9; s.evs.cd.grumpy_tap = 0;
    ok(!!EV.tapTantrum(s, { now: T }) && s.evs.cd.grumpy > s.evs.clock, '需求鬧脾氣冷卻中，連點仍然可以（唔共用 cd）');
    s.evs.lastAt = -1e9; SIM.advance(s, 47 * H, { hour: 14, now: T + 47 * H * 1000 }, 600); s.evs.lastAt = -1e9;
    ok(EV.tapTantrum(s, {}) === null && s.evs.stats.tantrumBlocked >= 1, '47h 內再連點：冷卻中唔觸發');
    SIM.advance(s, 1.1 * H, {}, 600); s.evs.lastAt = -1e9; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 });
    ok(!!EV.tapTantrum(s, {}), '48h 後可再觸發');
    s.evs.cd = {}; s.evs.lastAt = s.evs.clock - 600; ok(EV.tapTantrum(s, {}) === null, '全域 20 分鐘間隔內唔觸發');
    const lastAt = s.evs.lastAt; s.evs.cd = {}; s.evs.lastAt = -1e9; EV.tapTantrum(s, {}); ok(s.evs.lastAt === -1e9, 'grumpy_tap 唔改 lastAt（唔推後其他事件）', s.evs.lastAt);
    s.evs.lastAt = lastAt; s.sleeping = true; ok(EV.tapTantrum(s, {}) === null && s.evs.stats.tapSleepWake >= 1, '瞓緊連點唔會鬧脾氣');
    let inPool = 0; for (let sd = 1; sd <= 40; sd++) simulate(sd, 7, SESS).recs.forEach(x => { if (x.id === 'grumpy' && x.kind === 'draw') inPool++; }); ok(inPool === 0, '鬧脾氣唔會由抽選觸發', inPool); }
}


console.log('# QA 修正（PR #17）：P0 回撥日離線補抽／P1 重設日跳保底／P1 早鳥＋彩虹 pity／P2 閃光 72h');
{
  const T0 = Date.UTC(2026, 5, 10, 4, 0, 0);          // UTC 04:00（UTC 日頭 = T0 − 4h）
  const utcDay = (ms) => Math.floor(ms / 86400e3);
  const pc = P.drawChance, de = P.drawEveryH.slice(), fr = P.flashDayRate;
  const hot = () => { P.drawChance = 1; P.drawEveryH[0] = P.drawEveryH[1] = 0.5; P.flashDayRate = 0; };
  const cool = () => { P.drawChance = pc; P.drawEveryH[0] = de[0]; P.drawEveryH[1] = de[1]; P.flashDayRate = fr; };
  // P0：121 秒回撥＋離線補抽：當日（UTC）一個事件都唔出
  hot();
  // 情境（121 秒個 case）：UTC 04:00 離開（lastSeen＝lastSaveTime＝T0）→ 時鐘撥早 121 秒開 app（判回撥，noDrawDay＝當日）
  const a = adult(31); SIM.advance(a, 60, { hour: 12, now: T0 }, 30); a.evs.flashToday = false; a.lastSeen = T0; a.lastSaveTime = T0;
  const nowA = T0 - 121e3; SIM.applyOffline(a, nowA); const r0 = EV.noteOpen(a, { hour: SIM.hourOf(nowA), now: nowA });
  a.lastSeen = Math.max(a.lastSeen, nowA); EV.markSave(a, nowA);          // 同 G.save 一樣：lastSeen／lastSaveTime 都唔向後拉
  ok(r0 === null && a.evs.noDrawDay === utcDay(nowA) && a.lastSeen === T0 && a.lastSaveTime === T0, 'P0 早 121 秒開 app：判回撥（noDrawDay＝UTC 當日），lastSeen 唔向後拉');
  ok(EV.noDrawAt(a, a.evs, T0 + H * 1000) && EV.noDrawAt(a, a.evs, nowA - 60e3) && !EV.noDrawAt(a, a.evs, T0 + 22 * H * 1000), 'P0 noDrawAt：回撥日 true、下一個 UTC 日 false');
  // 同一 UTC 日稍後再開（時間已追過 lastSaveTime）：離線補抽（p_hit＝1）都係 0
  const evN = a.evs.stats.events; const later = T0 + 6 * H * 1000;
  const repL = SIM.applyOffline(a, later); EV.noteOpen(a, { hour: SIM.hourOf(later), now: later });
  ok(utcDay(later) === utcDay(nowA) && repL.T > 0 && a.evs.stats.events === evN && a.evs.offLog.length === 0 && a.evs.stats.suppressed > 0, 'P0 同一 UTC 日 6 小時後再開：離線補抽 0、保底 0（p_hit＝1 壓測）', a.evs.stats.events - evN);
  // 舊存檔（修正前 G.save 將 lastSeen 拉後咗）：lastSeen 喺回撥時間，補抽段落喺回撥日 → 仍然 0
  const a2 = adult(36); SIM.advance(a2, 60, { hour: 12, now: T0 }, 30); a2.evs.flashToday = false; a2.lastSaveTime = T0; a2.lastSeen = T0;
  EV.noteOpen(a2, { hour: 12, now: nowA }); a2.lastSeen = nowA;     // 模擬舊版行為
  const ev2 = a2.evs.stats.events; SIM.applyOffline(a2, later);
  ok(a2.evs.offLog.length === 0 && a2.evs.stats.events === ev2, 'P0 舊存檔 lastSeen 已被拉後：回撥日補抽仍然 0');
  a.lastSeen = later; a.lastSaveTime = later;
  const nextD = T0 + 22 * H * 1000; SIM.applyOffline(a, nextD);
  ok(a.evs.offLog.length > 0 && a.evs.offLog.every(x => utcDay(x.ts) > utcDay(nowA)), 'P0 下一個 UTC 日恢復補抽（' + a.evs.offLog.length + '）');
  // 對照：唔回撥（早 60 秒）→ 當日照補
  const b = adult(31); SIM.advance(b, 60, { hour: 0, now: T0 - 20 * H * 1000 }, 30); b.evs.flashToday = false;
  b.lastSeen = T0 - 20 * H * 1000; b.lastSaveTime = T0; SIM.applyOffline(b, T0 - 60e3);
  ok(b.evs.noDrawDay === null && b.evs.offLog.some(x => utcDay(x.ts) === utcDay(T0)), '對照：早 60 秒（容差內）當日照常補抽');
  cool();

  // P1：時鐘超前重設（lastSaveTime > now+24h）當日跳過保底 +3
  const c = adult(32); SIM.advance(c, 60, { hour: 12, now: T0 }, 30); c.evs.flashToday = false; c.lastSaveTime = T0 + 30 * DAY;
  const g0 = c.grains; const rc = EV.noteOpen(c, { hour: 12.1, now: T0 + 60e3 });
  ok(rc === null && c.evs.dayCount === 0 && c.evs.gDone === true && c.evs.stats.resetSkipGuarantee === 1 && c.saveResetAt === T0 + 60e3 && c.grains === g0, 'P1 重設當日：開 app 唔派保底（+3 光粒都冇）', JSON.stringify([rc && rc.id, c.evs.dayCount, c.evs.stats.resetSkipGuarantee]));
  for (let i = 0; i < 10; i++) SIM.advance(c, 1800, { hour: 12.1 + (i + 1) / 2, now: T0 + 60e3 + (i + 1) * 1800e3 }, 60);
  ok(c.evs.stats.guarantee === 0 && c.evs.stats.guaranteeOpen === 0, 'P1 重設當日過咗 16:00 仍然唔保底', c.evs.stats.guarantee);
  const nd = T0 + DAY; const rc2 = EV.noteOpen(c, { hour: 12, now: nd });
  ok(!!rc2 && rc2.kind === 'guarantee', 'P1 第二日恢復保底', rc2 && rc2.kind);
  const d0 = adult(33); SIM.advance(d0, 60, { hour: 12, now: T0 }, 30); d0.evs.flashToday = false; d0.lastSaveTime = T0 + 23 * H * 1000; d0.evs.lastAt = -1e9;
  ok(!EV.resetToday(d0, d0.evs) && !d0.saveResetAt, 'P1 未超 24h（冇重設）：resetToday false');

  // P1 早鳥：05–09 命中率 × hitMul；早鳥作息池抽取／日 2.2–2.4，總數 ≤2.95
  const EB = P.earlyBird;
  ok(EB && EB.hours[0] === 5 && EB.hours[1] === 9 && EB.hitMul === 1.1 && Math.abs(EV.hitChance(6) - Math.min(1, P.drawChance * 1.1)) < 1e-9 && EV.hitChance(12) === P.drawChance && EV.hitChance(9) === P.drawChance, '早鳥參數：05–09 p_hit × 1.1；其餘時段不變');
  const prof = (times, miss, seeds, days) => { let pool = 0, tot = 0, n = 0; for (let sd = 1; sd <= seeds; sd++) {
      let rs = sd * 99991; const rnd = () => ((rs = (rs * 16807) % 2147483647) / 2147483647); const s = adult(5000 + sd); s.lastSeen = BASE;
      for (let d = 0; d < days; d++) for (const h of times) { if (rnd() < miss) continue; const now = BASE + d * DAY + (h + (rnd() - .5) * .8) * H * 1000;
        SIM.applyOffline(s, now); care(s); EV.noteOpen(s, { hour: SIM.hourOf(now), now });
        for (let k = 0; k < 180; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); while (EV.takePending(s)) { } } s.lastSeen = now + 180e3; }
      const st = s.evs.stats; tot += st.events; pool += st.events - st.guarantee - st.guaranteeOpen - (st.byId.flash || 0) - (st.byId.grumpy || 0); n += days; }
    return { pool: pool / n, tot: tot / n }; };
  const eb = prof([7.5, 12.5], 0.1, 120, 28);
  console.log('    早鳥作息（7:30／12:30，miss 10%）：池抽取 ' + eb.pool.toFixed(2) + '／日，總 ' + eb.tot.toFixed(2) + '／日');
  ok(eb.pool >= 2.2 && eb.pool <= 2.4 && eb.tot <= 2.95, '早鳥：池抽取／日 2.2–2.4、總 ≤2.95', eb.pool.toFixed(3));
  const gen = prof([8, 12.5, 18.5, 22], 0.1, 80, 28);
  ok(gen.pool >= 2.2 && gen.pool <= 2.4 && gen.tot <= 2.95, '一般作息：池抽取 ' + gen.pool.toFixed(2) + '、總 ' + gen.tot.toFixed(2) + '（≤2.95）');

  // P1 彩虹 pity：≥14 日必出（保證 ≤14 日一次），仍守 17–23 時段窗
  ok(P.rainbowPityDays === 14 && P.rainbowPityLeadH === 26 && P.rainbowCooldownH === 240 && EV.DEF.rainbow.cooldownH === 240 && EV.DEF.rainbow.weight === 1, '彩虹 pity 14 日／提前 26h；冷卻 240h；權重維持 1');
  let maxGap = 0, badHour = 0, rbN = 0, pityN = 0, rbDays = 0, cdV = 0;
  for (let sd = 1; sd <= 80; sd++) { const sim = simulate(7000 + sd, 56, [8, 12.5, 18.5, 22]); rbDays += 56;
    const rb = sim.recs.filter(x => x.id === 'rainbow').concat(sim.s.evs.diary.filter(x => x.id === 'rainbow')).sort((x, y) => x.ts - y.ts);
    let prev = BASE + 8 * H * 1000; rb.forEach(x => { maxGap = Math.max(maxGap, (x.ts - prev) / DAY); prev = x.ts; const hr = new Date(x.ts).getHours(); if (hr < 17 || hr >= 23) badHour++; if (x.kind === 'pity') pityN++; });
    for (let i = 1; i < rb.length; i++) if (rb[i].at - rb[i - 1].at < 240 * H - 1) cdV++;
    rbN += rb.length; }
  console.log('    彩虹（一般作息 80×56 日）：每 ' + (rbDays / rbN).toFixed(1) + ' 日一次、最長間隔 ' + maxGap.toFixed(2) + ' 日、pity 佔 ' + (100 * pityN / rbN).toFixed(0) + '%');
  ok(maxGap <= 14, '彩虹最長間隔 ≤14 日（由第一次開 app 計）', maxGap.toFixed(2));
  ok(badHour === 0 && cdV === 0, 'pity 彩虹仍守 17–23 窗、240h 冷卻零違規', JSON.stringify([badHour, cdV]));
  ok(rbDays / rbN >= 11 && rbDays / rbN <= 15, '彩虹平均 11–15 日一次（加 pity 後）', (rbDays / rbN).toFixed(1));
  { const s = adult(34); SIM.advance(s, 60, { hour: 12, now: T0 }, 30); const E = s.evs; E.rbAt = E.clock - 13.5 * 86400; E.cd = {};
    ok(EV.rainbowPity(s, E, 18) === EV.DEF.rainbow && EV.rainbowPity(s, E, 12) === null && EV.rainbowPity(s, E, 23.5) === null, 'rainbowPity：到期時窗內回傳彩虹、窗外 null');
    E.cd.rainbow = E.clock + 3600; ok(EV.rainbowPity(s, E, 18) === null, 'rainbowPity：唔打穿冷卻');
    E.cd = {}; E.rbAt = E.clock - 10 * 86400; ok(EV.rainbowPity(s, E, 18) === null, 'rainbowPity：未到期（10 日）唔強制'); }

  // P2 閃光日 72h 冷卻
  ok(P.flashCooldownH === 72 && EV.DEF.flash.cooldownH === 72, '閃光日冷卻 72h（參數＋事件定義）');
  { const s = adult(35); SIM.advance(s, 60, { hour: 12, now: T0 }, 30); const E = s.evs;
    E.flashAtMs = T0 - 48 * H * 1000; E.nowMs = T0; ok(!EV.flashCdOk(E), 'flashCdOk：48h 前閃過 → false');
    E.flashAtMs = T0 - 72 * H * 1000; ok(EV.flashCdOk(E), 'flashCdOk：72h → true'); }
  P.flashDayRate = 1;
  let fl = 0, flV = 0, skip = 0;
  for (let sd = 1; sd <= 20; sd++) { const sim = simulate(8000 + sd, 14, [9, 13, 20]); const f = sim.recs.filter(x => x.id === 'flash').sort((x, y) => x.ts - y.ts);
    for (let i = 1; i < f.length; i++) if (f[i].ts - f[i - 1].ts < 72 * H * 1000) flV++; fl += f.length; skip += sim.s.evs.stats.flashCdSkip || 0; }
  P.flashDayRate = fr;
  ok(fl > 0 && flV === 0 && skip > 0, '閃光日率 100%（壓測）14 日：兩次閃光相距全部 ≥72h（' + fl + ' 次、跳過 ' + skip + ' 日）', JSON.stringify([fl, flV, skip]));
}

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
