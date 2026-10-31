/* PR #19 自跑模擬（Node，用真模組）：node tests/sim-report.js
   ① 14 日離線入日記條數（1000 種子）② 彩虹幾多日一次（1500 種子 × 28 日，每日 4／5 次開 app）③ 螢火散步喺傍晚 17–23 事件佔比 */
const SIM = require('../src/sim.js'); const D = require('../src/data.js'); require('../src/lighting.js'); const EV = require('../src/events.js');
const H = 3600, DAY = 86400e3, BASE = new Date(2026, 0, 5).getTime();
function adult(seed) { const s = SIM.newState(BASE, seed); s.stage = 'adult'; s.form = 'soft'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }); return s; }
const care = (s) => { for (const k of ['hunger', 'mood', 'clean', 'energy']) s.needs[k] = Math.max(s.needs[k], 80); s.poops = 0; s.sleeping = false; };
const q = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
// ①
{
  const c = [], tot = [], rareTop = [];
  for (let sd = 1; sd <= 1000; sd++) {
    const t = adult(sd), T1 = new Date(2026, 5, 1, 21, 0, 0).getTime(); t.createdAt = T1 - 9e9;
    SIM.advance(t, 30, { hour: 21, now: T1 }, 30); t.lastSeen = T1; t.lastSaveTime = T1;
    SIM.applyOffline(t, T1 + 14 * DAY); c.push(t.evs.diary.length); tot.push(t.evs.offLog.length);
    const anyRare = t.evs.offLog.some(x => x.rare); rareTop.push(!anyRare || t.evs.pending.some(x => EV.DEF[x.id].rare));
  }
  c.sort((a, b) => a - b); const m = c.reduce((a, b) => a + b, 0) / c.length, mt = tot.reduce((a, b) => a + b, 0) / tot.length;
  console.log(`① 14 日離線（1000 種子）：入日記 平均 ${m.toFixed(1)}、中位 ${q(c, .5)}、p95 ${q(c, .95)}、最多 ${c[c.length - 1]}；連彈窗共 ${mt.toFixed(1)} 個（${(mt / 14).toFixed(2)}／日）；有稀有時彈窗必含稀有 ${(rareTop.filter(Boolean).length / 10).toFixed(1)}%`);
}
// ②③
for (const sess of [[8, 12.5, 18, 21.5], [8, 12.5, 18, 21, 23.5]]) {
  let rbId = 0, rb = 0, days = 0, ev = 0, eve = 0, ff = 0, ffAll = 0, guar = 0, cdViol = 0;
  for (let sd = 1; sd <= 1500; sd++) {
    const s = adult(sd * 7919 + 13), recs = []; const L = (st, r) => { if (st === s) recs.push(r); }; EV.listeners.push(L); s.lastSeen = BASE;
    for (let d = 0; d < 28; d++) for (const h of sess) {
      const now = BASE + d * DAY + h * H * 1000; SIM.applyOffline(s, now); care(s); EV.noteOpen(s, { hour: SIM.hourOf(now), now });
      for (let k = 0; k < 180; k += 30) { SIM.advance(s, 30, { hour: SIM.hourOf(now + k * 1000), now: now + k * 1000 }, 30); while (EV.takePending(s)) { } }
      s.lastSeen = now + 180e3;
    }
    EV.listeners.splice(EV.listeners.indexOf(L), 1); days += 28; rbId += s.evs.stats.byId.rainbow || 0;
    const all = recs.concat(s.evs.diary.filter(x => !recs.includes(x)));
    const last = {};
    all.sort((a, b) => a.at - b.at).forEach(x => {
      ev++; if (x.id === 'rainbow') rb++; if (x.id === 'firefly_walk') ffAll++; if (x.kind === 'guarantee') guar++;
      if (x.hour >= 17 && x.hour < 23 && x.id !== 'flash' && x.id !== 'grumpy') { eve++; if (x.id === 'firefly_walk') ff++; }
      const d = EV.DEF[x.id]; if (last[x.id] != null && x.id !== 'flash') { const need = (d.cooldownH || (d.rare ? 72 : 24)) * H; if (x.at - last[x.id] < need - 1) cdViol++; } last[x.id] = x.at;
    });
  }
  console.log(`②③ 每日開 app ${sess.length} 次 × 28 日 × 1500 種子：事件 ${(ev / days).toFixed(2)}／日（保底 ${(guar / days).toFixed(2)}）；彩虹 ${rbId} 次 → 每 ${(days / rbId).toFixed(1)} 日一次；傍晚 17–23 事件中螢火散步 ${(ff / eve * 100).toFixed(1)}%（${ff}/${eve}），全部事件中 ${(ffAll / ev * 100).toFixed(1)}%；冷卻違反 ${cdViol}`);
}
