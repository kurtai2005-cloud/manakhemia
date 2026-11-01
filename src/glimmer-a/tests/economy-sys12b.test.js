/* systems12 第 2 批經濟測試（docs-gdd/systems12b-params.md）：node tests/economy-sys12b.test.js
   載入 systems.js＋systems2.js：浮動團絨撳兩下＝一局接光點 score 40（2★ +2）；
   tools/route-sweep.js 同一套 6 類玩家 × 200 seed × 7 日（委託、摸頭、懸浮執 5 粒＝遊測假設），每次上線再加（獨立 rng）：
   ・小遊戲 v2（docs-gdd/minigames-v2.md；舊接光點／捉迷藏 v1Enabled 閂咗）：40% 開一局（彈彈葉／花園捉迷藏各半；夜晚 17–07 三選一含追螢火）
     ＝真 minigames2 遊戲＋tests/mg2-bots.js bot（技術 0–1 隨機）
   ・小圃：一盆日菊循環（夠 6 粒就種、每次上線淋水）→ 開花 +2；散步：每次上線行 3 段（真 walkRoll）；每次上線 tick（徽章）。
   檢查：每日星星碎（唔計徽章）中位 ∈ [15, 30]、最高 ≤30；徽章星星碎另計（一次性、唔入每日計數）。 */
const S = require('../src/sim.js'), X = require('../src/systems.js'), B = require('../src/systems2.js');
const SW = require('../tools/route-sweep.js'), P = require('../src/data.js').PARAMS, M2 = require('../src/minigames2.js'), BOT = require('./mg2-bots.js');
let pass = 0, fail = 0;
function ok(c, n, i) { if (c) { pass++; console.log('  ✓ ' + n); } else { fail++; console.log('  ✗ ' + n + (i !== undefined ? '  → ' + JSON.stringify(i) : '')); } }
const med = a => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : 0; };
const keysOf = () => { const k = []; for (let d = 0; d < 7; d++) k.push(S.dayKey(new Date(2026, 10, 2).getTime() + d * 864e5)); return k; };
function playCatch(rng) {
  const g = new S.Minigame((rng() * 1e9) | 1, B.catchParams()), err = 10 + rng() * 30; let tgx = g.basketX, k = 0;
  while (!g.over) { if (k++ % 6 === 0) { const tg = g.items.filter(i => i.type !== 'stone' && i.y < g.M.basketY).sort((a, b) => b.y - a.y)[0]; tgx = tg ? tg.x + (rng() * 2 - 1) * err : g.basketX; } g.update(1 / 30, tgx); }
  return g.score;
}
function playHide(rng) { const h = new B.HideGame((rng() * 1e9) | 1); while (!h.over) { const free = h.spots.map((_, i) => i).filter(i => !h.tried.includes(i)); const i = h.tail && rng() < 0.7 ? h.at : free[Math.floor(rng() * free.length)]; h.pick(i); } return { v: h.score, first: h.firstHits }; }
function hookFor(seed, stat) {
  const rng = S.makeRng(seed * 7919 + 503);
  return (s, now) => {
    if (s.stage === 'egg') return;
    if (rng() < 0.4) {
      const ks = M2.fireflyOpen(new Date(now).getHours()) ? ['bounce', 'ghide', 'firefly'] : ['bounce', 'ghide'], k = ks[Math.floor(rng() * ks.length)];
      const g = BOT.playBot(M2, k, (rng() * 1e9) | 1, rng(), rng), r = B.gameFinish(s, k, g.score, now, k === 'ghide' ? { firstHits: g.firstHits } : {});
      (stat.by[k] = stat.by[k] || []).push(r.stars); (k === 'ghide' ? stat.hstars : stat.stars).push(r.stars);
    }
    const pots = () => B.st(s).garden.pots; if (!pots()[0] && X.wallet(s, now).total >= P.systems12b.garden.seedPrice) B.plant(s, 0, 'daisy', now); if (pots()[0]) B.water(s, 0, now);
    for (let i = 0; i < 3; i++) B.walkRoll(s, now, { rng });
    B.tick(s, now);
  };
}
console.log('① 7 日星星碎（唔計徽章；每日中位，200 seed／類型）');
const ECON = {}, allStars = [], allH = [], BY = {};
for (const name of Object.keys(SW.SCHED)) {
  const base = [], full = [], badge = []; let mx = 0;
  for (let sd = 1; sd <= 200; sd++) {
    const st = { stars: allStars, hstars: allH, by: BY };
    const r0 = SW.run(name, sd, { days: 7, drops: 5, fpats: 2 });
    let last = null; const r = SW.run(name, sd, { days: 7, drops: 5, fpats: 2, onSession: (s, now) => { last = s; hookFor(sd, st)(s, now); } });
    for (const k of keysOf()) { if (r.played[k]) { full.push(r.shards[k] || 0); base.push(r0.shards[k] || 0); } mx = Math.max(mx, r.shards[k] || 0); }
    if (last) badge.push(X.st(last).wallet.log.filter(l => l.src === 'badge').reduce((a, l) => a + l.n, 0));
  }
  const m = med(full), m0 = med(base);
  ECON[name] = { median: m, medianNoMinigames: m0, max: mx, badgeMedian7d: med(badge) };
  console.log(`  ${name}　上線日中位 ${m}（只有浮動局 ${m0}）｜最高 ${mx}｜7 日徽章星星碎中位 ${med(badge)}（另計）`);
  ok(m >= 15 && m <= 30, `${name}：每日星星碎中位 ${m} ∈ [15, 30]（唔計徽章）`);
  ok(mx <= 30, `${name}：每日唔超過上限 30（最高 ${mx}）`);
}
const dist = a => [0, 1, 2, 3].map(n => Math.round(a.filter(x => x === n).length / Math.max(1, a.length) * 100) + '%').join('／');
console.log('  v2 星數分佈 0／1／2／3★：' + Object.keys(BY).map(k => `${k} ${dist(BY[k])}（n=${BY[k].length}）`).join('｜'));
ok(['bounce', 'ghide', 'firefly'].every(k => BY[k] && BY[k].length > 100), '3 隻 v2 小遊戲都有玩到（sim 有效）', Object.keys(BY).map(k => k + ':' + BY[k].length));
if (process.env.ECON_JSON) require('fs').writeFileSync(process.env.ECON_JSON, JSON.stringify({ econ: ECON, v2Stars: Object.fromEntries(Object.keys(BY).map(k => [k, dist(BY[k])])) }, null, 1));
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exitCode = fail ? 1 : 0;
