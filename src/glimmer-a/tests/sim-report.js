/* PR #19 自跑模擬（Node，用真模組）：node tests/sim-report.js
   ① 14 日離線入日記條數（1000 種子）② 彩虹幾多日一次（1500 種子 × 28 日，每日 4／5 次開 app）③ 螢火散步喺傍晚 17–23 事件佔比 */
const SIM = require('../src/sim.js'); const D = require('../src/data.js'); require('../src/lighting.js'); const EV = require('../src/events.js');
const H = 3600, DAY = 86400e3, BASE = new Date(2026, 0, 5).getTime();
function adult(seed) { const s = SIM.newState(BASE, seed); s.stage = 'adult'; s.form = 'soft'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }); return s; }
const care = (s) => { for (const k of ['hunger', 'mood', 'clean', 'energy']) s.needs[k] = Math.max(s.needs[k], 80); s.poops = 0; s.sleeping = false; };
const q = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
// ①
{
  const c = [], tot = [], rareTop = []; let cdv = 0, maxPop = 0, maxDay = 0;
  for (let sd = 1; sd <= 1000; sd++) {
    const t = adult(sd), T1 = new Date(2026, 5, 1, 21, 0, 0).getTime(); t.createdAt = T1 - 9e9;
    SIM.advance(t, 30, { hour: 21, now: T1 }, 30); t.lastSeen = T1; t.lastSaveTime = T1;
    const rep = SIM.applyOffline(t, T1 + 14 * DAY); maxPop = Math.max(maxPop, rep.popups);
    { const last = {}, pd = {}; t.evs.offLog.slice().sort((a, b) => a.at - b.at).forEach(x => { const d = EV.DEF[x.id], need = (d.cooldownH || (d.rare ? 72 : 24)) * H; if (last[x.id] != null && x.at - last[x.id] < need - 1) cdv++; last[x.id] = x.at; const k = new Date(x.ts).toDateString(); pd[k] = (pd[k] || 0) + 1; }); maxDay = Math.max(maxDay, ...Object.values(pd)); }
    c.push(t.evs.diary.length); tot.push(t.evs.offLog.length);
    const anyRare = t.evs.offLog.some(x => x.rare); rareTop.push(!anyRare || t.evs.pending.some(x => EV.DEF[x.id].rare));
  }
  c.sort((a, b) => a - b); const m = c.reduce((a, b) => a + b, 0) / c.length, mt = tot.reduce((a, b) => a + b, 0) / tot.length;
  console.log(`① 14 日離線（1000 種子）：入日記 平均 ${m.toFixed(1)}、中位 ${q(c, .5)}、p95 ${q(c, .95)}、最多 ${c[c.length - 1]}；連彈窗共 ${mt.toFixed(1)} 個（${(mt / 14).toFixed(2)}／日）；有稀有時彈窗必含稀有 ${(rareTop.filter(Boolean).length / 10).toFixed(1)}%；彈窗最多 ${maxPop}；單日最多 ${maxDay} 個；冷卻違反 ${cdv}（offlineIgnoreDailyMax=${D.PARAMS.events.offlineIgnoreDailyMax}）`);
}
// ②③
for (const sess of [[8, 12.5, 18, 21.5], [8, 12.5, 18, 21, 23.5]]) {
  let evSt = 0, rbId = 0, rb = 0, days = 0, ev = 0, eve = 0, ff = 0, ffAll = 0, guar = 0, cdViol = 0;
  for (let sd = 1; sd <= 1500; sd++) {
    const s = adult(sd * 7919 + 13), recs = []; const L = (st, r) => { if (st === s) recs.push(r); }; EV.listeners.push(L); s.lastSeen = BASE;
    for (let d = 0; d < 28; d++) for (const h of sess) {
      const now = BASE + d * DAY + h * H * 1000; SIM.applyOffline(s, now); care(s); EV.noteOpen(s, { hour: SIM.hourOf(now), now });
      for (let k = 0; k < 180; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); while (EV.takePending(s)) { } }
      s.lastSeen = now + 180e3;
    }
    EV.listeners.splice(EV.listeners.indexOf(L), 1); days += 28; rbId += s.evs.stats.byId.rainbow || 0; evSt += s.evs.stats.events;
    const all = recs.concat(s.evs.diary.filter(x => !recs.includes(x)));
    const last = {};
    all.sort((a, b) => a.at - b.at).forEach(x => {
      ev++; if (x.id === 'rainbow') rb++; if (x.id === 'firefly_walk') ffAll++; if (x.kind === 'guarantee') guar++;
      if (x.hour >= 17 && x.hour < 23 && x.id !== 'flash' && x.id !== 'grumpy') { eve++; if (x.id === 'firefly_walk') ff++; }
      const d = EV.DEF[x.id]; if (last[x.id] != null && x.id !== 'flash') { const need = (d.cooldownH || (d.rare ? 72 : 24)) * H; if (x.at - last[x.id] < need - 1) cdViol++; } last[x.id] = x.at;
    });
  }
  console.log(`②③ 每日開 app ${sess.length} 次 × 28 日 × 1500 種子：事件 ${(ev / days).toFixed(2)}／日（stats ${(evSt / days).toFixed(2)}，≤2.95 ${evSt / days <= 2.95 ? '✓' : '✗'}）（保底 ${(guar / days).toFixed(2)}）；彩虹 ${rbId} 次 → 每 ${(days / rbId).toFixed(1)} 日一次；傍晚 17–23 事件中螢火散步 ${(ff / eve * 100).toFixed(1)}%（${ff}/${eve}），全部事件中 ${(ffAll / ev * 100).toFixed(1)}%；冷卻違反 ${cdViol}`);
}
// ④ QA 修正（PR #17）：QA 六種作息（pet_events_final.py）× 300 種子 × 56 日——池抽取／日（早鳥 2.2–2.4）、總數／日（≤2.95）、彩虹平均／最長間隔（≤14 日）、冷卻／間隔／閃光 72h 違反
{
  const PROF = [['勤力', [8, 10.5, 13, 16.5, 19.5, 22.5], .05], ['一般', [8, 12.5, 18.5, 22], .1], ['上班族', [7.5, 19, 22.5], .1], ['輕度', [8.5, 21.5], .15], ['早鳥', [7.5, 12.5], .1], ['隔日', [20], 0, 2]];
  const P = D.PARAMS.events; let allCd = 0, allGap = 0, allFlash = 0, worstGap = 0, worstTot = 0;
  for (const [nm, times, miss, every] of PROF) {
    let pool = 0, tot = 0, rb = 0, days = 0, maxGap = 0, pity = 0, cdv = 0, gapv = 0, flv = 0;
    for (let sd = 1; sd <= 300; sd++) {
      let rs = sd * 99991; const rnd = () => ((rs = (rs * 16807) % 2147483647) / 2147483647);
      const s = adult(sd * 7919 + 13), recs = []; const L = (st, r) => { if (st === s) recs.push(r); }; EV.listeners.push(L); s.lastSeen = BASE; let first = null;
      for (let d = 0; d < 56; d++) { if (every && d % every) continue; for (const h of times) { if (rnd() < miss) continue;
        const now = BASE + d * DAY + (h + (rnd() - .5) * .8) * H * 1000; if (first == null) first = now; SIM.applyOffline(s, now); care(s); EV.noteOpen(s, { hour: SIM.hourOf(now), now });
        for (let k = 0; k < 180; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); while (EV.takePending(s)) { } } s.lastSeen = now + 180e3; } }
      EV.listeners.splice(EV.listeners.indexOf(L), 1);
      const st = s.evs.stats; days += 56; tot += st.events; pool += st.events - st.guarantee - st.guaranteeOpen - (st.byId.flash || 0) - (st.byId.grumpy || 0); pity += st.rainbowPity || 0;
      const all = recs.concat(s.evs.diary.filter(x => !recs.includes(x))).sort((a, b) => a.ts - b.ts);
      let prev = first; const last = {}; let lastAt = null;
      all.forEach(x => { if (x.id === 'rainbow') { rb++; maxGap = Math.max(maxGap, (x.ts - prev) / DAY); prev = x.ts; }
        const d = EV.DEF[x.id], need = (d.cooldownH || (d.rare ? 72 : 24)) * H;
        if (last[x.id] != null && x.at - last[x.id] < need - 1) { if (x.id === 'flash') flv++; else cdv++; } last[x.id] = x.at;
        if (lastAt != null && x.at - lastAt < P.minGapSec - 1) gapv++; lastAt = x.at; });
    }
    allCd += cdv; allGap += gapv; allFlash += flv; worstGap = Math.max(worstGap, maxGap); worstTot = Math.max(worstTot, tot / days);
    console.log(`④ ${nm.padEnd(3, '　')}：池抽取 ${(pool / days).toFixed(2)}／日、總 ${(tot / days).toFixed(2)}／日；彩虹每 ${(days / rb).toFixed(1)} 日（最長間隔 ${maxGap.toFixed(2)} 日，pity ${(100 * pity / rb).toFixed(0)}%）；冷卻違反 ${cdv}、間隔違反 ${gapv}、閃光 72h 違反 ${flv}`);
  }
  console.log(`④ 合計：彩虹最長間隔 ${worstGap.toFixed(2)} 日（≤14 ${worstGap <= 14 ? '✓' : '✗'}）；最高總數 ${worstTot.toFixed(2)}／日（≤2.95 ${worstTot <= 2.95 ? '✓' : '✗'}）；冷卻違反 ${allCd}、間隔違反 ${allGap}、閃光 72h 違反 ${allFlash}（earlyBird.hitMul=${P.earlyBird.hitMul}、rainbow weight=${EV.DEF.rainbow.weight}、pity ${P.rainbowPityDays}d−${P.rainbowPityLeadH}h、rainbow cd ${P.rainbowCooldownH}h、p_hit ${P.drawChance}）`);
}
// ⑤ 彩虹 240h 冷卻：每種作息 4 種子 × 750 日＝3000 日。平均間隔目標 11–15 日；最長仍 ≤14（pity）
{
  const PROF = [['勤力', [8, 10.5, 13, 16.5, 19.5, 22.5], .05], ['一般', [8, 12.5, 18.5, 22], .1], ['上班族', [7.5, 19, 22.5], .1], ['輕度', [8.5, 21.5], .15], ['早鳥', [7.5, 12.5], .1], ['隔日', [20], 0, 2]];
  const P = D.PARAMS.events; const DAYS = 750, SEEDS = 4;
  for (const [nm, times, miss, every] of PROF) {
    let pool = 0, tot = 0, rb = 0, days = 0, maxGap = 0, pity = 0, cdv = 0, gaps = 0;
    for (let sd = 1; sd <= SEEDS; sd++) {
      let rs = sd * 99991; const rnd = () => ((rs = (rs * 16807) % 2147483647) / 2147483647);
      const s = adult(sd * 7919 + 501), recs = []; const L = (st, r) => { if (st === s) recs.push(r); }; EV.listeners.push(L); s.lastSeen = BASE; let first = null;
      for (let d = 0; d < DAYS; d++) { if (every && d % every) continue; for (const h of times) { if (rnd() < miss) continue;
        const now = BASE + d * DAY + (h + (rnd() - .5) * .8) * H * 1000; if (first == null) first = now; SIM.applyOffline(s, now); care(s); EV.noteOpen(s, { hour: SIM.hourOf(now), now });
        for (let k = 0; k < 180; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); while (EV.takePending(s)) { } } s.lastSeen = now + 180e3; } }
      EV.listeners.splice(EV.listeners.indexOf(L), 1);
      const st = s.evs.stats; days += DAYS; tot += st.events; pool += st.events - st.guarantee - st.guaranteeOpen - (st.byId.flash || 0) - (st.byId.grumpy || 0); pity += st.rainbowPity || 0;
      const all = recs.concat(s.evs.diary.filter(x => !recs.includes(x))).sort((a, b) => (a.ts - b.ts) || (a.at - b.at));
      let prev = first; const lastRb = { at: null };
      all.forEach(x => { if (x.id !== 'rainbow') return; rb++; const g = (x.ts - prev) / DAY; gaps += g; maxGap = Math.max(maxGap, g); prev = x.ts;
        if (lastRb.at != null && x.at - lastRb.at < (P.rainbowCooldownH || 240) * H - 1) cdv++; lastRb.at = x.at; });
    }
    const mean = days / rb;
    console.log(`⑤ ${nm.padEnd(3, '　')}：${SEEDS}×${DAYS}=${days} 日；池抽取 ${(pool / days).toFixed(3)}／日（2.2–2.4 ${pool / days >= 2.2 && pool / days <= 2.4 ? '✓' : '✗'}）、總 ${(tot / days).toFixed(3)}／日；彩虹每 ${mean.toFixed(2)} 日（11–15 ${mean >= 11 && mean <= 15 ? '✓' : '✗'}），最長 ${maxGap.toFixed(2)} 日（≤14 ${maxGap <= 14.001 ? '✓' : '✗'}），pity ${(100 * pity / rb).toFixed(0)}%，240h 違反 ${cdv}`);
  }
}
