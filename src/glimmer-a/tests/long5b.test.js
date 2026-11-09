/* 第 5 批 5b（docs-gdd/series2-4a4b-spec.md v1.1 §5b＋5a–5c 定案）：遠足＋小職業 s.fam.b5 — 對數／遠足限成年 S6＋靜光／每日 2 隻／24h 或翌日開返／碎 5–10＋經驗 +3＋日記＋30% 手信入家具庫／
   4 款工作出糧（Lv＋1）／5 日升級／Lv5 封頂、家族 Lv7 開 Lv6／守夜夜晚＋貼紙／廚師親密 +1（上限 10）／每日 12 碎上限／經濟淨值／§7 唔郁。 */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), HS = require('../src/house.js'), F = require('../src/long5a.js'), X = require('../src/systems.js'), VS = require('../src/visit.js'), B = require('../src/long5b.js');
const fs = require('fs'), path = require('path'), ART = path.join(__dirname, '../art/series2_long');
const J = (f) => JSON.parse(fs.readFileSync(path.join(ART, f), 'utf8')), L = J('5b/long_5b.json'), LAY = J('5b/ui/layout.json');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime();
const NOW = at(0, 12);
function fam() { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; s.dex = ['tide']; S2.noteElder(s, at(-25, 12)); S2.deliver(s, at(-24, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(-20, 12)); Object.assign(p, { intim: 90, rel: 'family' }); HS.ensure(s, at(-5, 12));
  const o = F.st(s); o.init = at(-5, 12);
  const R = (id, kind, fk, name, gen) => ({ id, kind, fk, name, gen: gen || 0, form: kind === 'tr' ? 'moon' : null, room: 'room1', at: at(-3, 12), snap: {} });
  o.res.push(R('tr0', 'tr', 'evo_still_moon', '月月', 0), R('kidA', 'kid', 'A3', '星仔'), R('kidB', 'kid', 'B3', '棉棉'), R('trX', 'tr', 'tide', '潮潮', 0));
  return s; }
const W = (s) => X.st(s).wallet.total;
const route = (s) => JSON.stringify({ evo: s.evo, evs: s.evs, form: s.form });

console.log('⓪ 美術／資料對數');
{ ok(B.CFG.maxPerDay === L.expedition.maxPerDay && B.CFG.durationH === L.expedition.durationH && JSON.stringify(B.CFG.shards) === JSON.stringify(L.expedition.shards) && B.CFG.furnitureChance === L.expedition.furnitureChance, '遠足：每日 2、24h、碎 5–10、30% 家具');
  ok(B.CFG.capPerDay === L.daily.shardCapPerDay && B.CFG.daysPerLevel === L.jobs.levels.daysPerLevel && B.CFG.maxLv === L.jobs.levels.max && B.CFG.maxLvFam7 === L.jobs.levels.maxWithFamilyLv7, '每日 12 碎、5 日升級、Lv5／Lv6');
  ok(JSON.stringify(B.JOBS.map(j => j.id + j.zh + j.icon)) === JSON.stringify(L.jobs.list.map(j => j.id + j.zh + j.icon)), '4 款工作 id／名／icon 對數');
  ok(JSON.stringify(L.expedition.souvenirPool) === JSON.stringify(F.SOUV.map(x => x.id)) && F.SOUV.every(x => B.PLACE[x.id]), '手信池 10 件＋每件有地點故事');
  const miss = []; const chk = (f) => { if (!fs.existsSync(path.join(ART, '5b', f))) miss.push(f); };
  for (const k in L.expedition.forms) { const f = L.expedition.forms[k]; chk(f.depart.png); chk(f.return.png); }
  for (const k in L.jobs.forms) for (const j in L.jobs.forms[k]) chk(L.jobs.forms[k][j].png);
  for (const k in LAY.assets) chk(LAY.assets[k]); for (const x of L.souvenirs) { chk(x.icon); chk(x.medal); chk(x.px); }
  ok(!miss.length, '25 形態出發／返屋 strip、100 張帽、UI 零件、手信 medal 全部喺 repo', miss.slice(0, 4));
  ok(Object.keys(L.expedition.forms).filter(k => /^[A-H]2$/.test(k)).length === 8 && !B.canHike({ kind: 'kid', fk: 'A2' }), 'S5 strip 保留但唔用（S5 唔可以遠足）');
  for (const st of [{ kind: 'tr', fk: 'evo_still_lumi' }, { kind: 'kid', fk: 'H3' }]) ok(B.canHike(st), '可以遠足：' + st.fk);
  ok(!B.canHike({ kind: 'tr', fk: 'tide' }), '非靜光團絨唔可以遠足');
  ok(F.LIVE.job_cap_plus1 === 1 && !F.LATER.job_cap_plus1, '家族 Lv7「工作上限 +1」而家生效');
  ok(/^6[a-d]$/.test(D.PARAMS.series2.version), '版本 5b', D.PARAMS.series2.version);
}
console.log('① 遠足');
{ const s = fam(), r0 = route(s), w0 = W(s), xp0 = F.st(s).xp;
  ok(B.plan(s, NOW).rows.length === 4 && !B.plan(s, NOW).rows.some(r => r.id === F.trId(s)), '每日安排：4 隻住客（主養唔出現）');
  ok(B.choose(s, 'trX', 'expedition', null, NOW).reason === 'notHike', '非靜光團絨：唔去得');
  const a = B.choose(s, 'tr0', 'expedition', null, NOW); ok(a.ok && a.ev[0].what === 'depart' && B.away(s, 'tr0'), '靜光出發');
  ok(B.choose(s, 'kidA', 'expedition', null, NOW).ok, 'S6 細佬出發');
  ok(B.choose(s, 'kidB', 'expedition', null, NOW).reason === 'full', '第 3 隻：今日 2/2 用晒');
  ok(B.plan(s, NOW).rows.find(r => r.id === 'kidB').lock.expedition, '2/2 → 遠足 segment 鎖');
  ok(B.choose(s, 'tr0', 'job', 'post', NOW).reason === 'away', '遠足中唔揀得');
  ok(B.scan(s, at(0, 23)).filter(e => e.what === 'back').length === 0, '同日夜晚未返');
  const ev = B.scan(s, at(1, 9), { boot: true }), bk = ev.filter(e => e.what === 'back'); ok(bk.length === 2, '翌日第一次開遊戲 → 返屋', ev);
  ok(bk.every(e => e.n >= 5 && e.n <= 10) && W(s) - w0 === bk.reduce((a, e) => a + e.n, 0), '碎 5–10 入錢包', bk.map(e => e.n));
  ok(F.st(s).xp - xp0 === 6, '家族經驗 +3 ×2');
  const o = B.st(s); ok(o.trips.length === 2 && o.trips.every(t => t.lines.length === 3 && F.SV[t.sv] && /^H[1-4]$/.test(t.scene)), '團絨日記：每次一格故事（3 行＋手信＋場景）');
  ok(o.q.length === 2, '返屋 toast 排隊');
  ok(route(s) === r0, '§7 路線唔郁');
  const s2 = fam(); B.choose(s2, 'tr0', 'expedition', null, at(0, 10)); ok(!B.scan(s2, at(1, 9)).some(e => e.what === 'back'), '翌日但唔係開機（唔 boot）而未夠 24h：未返');
  ok(B.scan(s2, at(1, 10)).some(e => e.what === 'back'), '24 小時後返');
  ok(B.choose(s2, 'tr0', 'expedition', null, at(1, 10, 5)).ok, '返嚟之後翌日可以再去');
}
console.log('② 30% 手信入家具庫');
{ let furn = 0, N = 200; const s = fam();
  for (let i = 0; i < N; i++) { const t = at(0, 12) + i * 2 * 86400000; B.st(s).day.k = 0; const r = B.choose(s, 'tr0', 'expedition', null, t); if (!r.ok) continue; const e = B.devReturn(s, 'tr0', t + 1000)[0]; if (e.furn) furn++; F.st(s).sv = {}; }
  ok(furn / N > 0.2 && furn / N < 0.4, '約 30% 手信入家具庫', furn / N);
  const s2 = fam(); for (const x of F.SOUV) F.st(s2).sv[x.id] = 1; B.choose(s2, 'tr0', 'expedition', null, NOW); const e = B.devReturn(s2, 'tr0', NOW + 5)[0]; ok(e.furn === null, '全部有晒 → 冇家具（只係日記手信）');
}
console.log('③ 小職業');
{ const s = fam(), w0 = W(s);
  const r = B.choose(s, 'kidA', 'job', 'post', NOW); ok(r.ok && r.ev[0].what === 'pay' && r.ev[0].n === 2, '郵差助手 Lv1：+2 碎', r.ev);
  ok(B.choose(s, 'kidA', 'job', 'garden', NOW).reason === 'done' && B.choose(s, 'kidA', 'rest', null, NOW).reason === 'done', '今日做咗：唔轉得（每日 1 樣）');
  ok(B.choose(s, 'kidA', 'expedition', null, NOW).reason === 'done', '做咗工作唔可以再遠足');
  ok(!B.scan(s, NOW + 60000).some(e => e.what === 'pay'), '同日唔會出兩次糧');
  let lv = null; for (let d = 1; d <= 4; d++) { const ev = B.scan(s, at(d, 9)); const up = ev.find(e => e.what === 'lvUp'); if (up) lv = up; }
  ok(lv && lv.lv === 2, '做滿 5 日升 Lv2', lv);
  ok(B.scan(s, at(5, 9)).find(e => e.what === 'pay').n === 3, 'Lv2：+3 碎');
  B.devDays(s, 'kidA', 'post', 40); ok(B.jobInfo(s, 'kidA', 'post').lv === 5 && B.jobInfo(s, 'kidA', 'post').lv6Locked, 'Lv5 封頂（家族 Lv7 前）');
  F.st(s).xp = F.THRESH[6]; ok(B.jobInfo(s, 'kidA', 'post').lv === 6 && B.jobInfo(s, 'kidA', 'post').pay === 7 && !B.jobInfo(s, 'kidA', 'post').lv6Locked, '家族 Lv7 → 開 Lv6（+7 碎）');
  ok(W(s) > w0, '碎入 sys12 錢包');
}
console.log('④ 守夜／園丁／郵差／廚師');
{ const s = fam();
  const r = B.choose(s, 'kidB', 'job', 'watch', NOW); ok(r.ok && !r.ev.length, '守夜：日頭揀咗唔出糧');
  const ev = B.scan(s, at(0, 21, 30)); const p = ev.find(e => e.what === 'pay'), k = ev.find(e => e.what === 'perk' && e.stk); ok(p && p.n === 2 && k && B.STICKERS.includes(k.stk), '夜晚 21:00 後：+2 碎＋夢泡泡貼紙', ev);
  const s2 = fam(); B.choose(s2, 'kidB', 'job', 'watch', NOW); const e2 = B.scan(s2, at(1, 9)); ok(e2.some(e => e.what === 'pay' && e.id === 'kidB'), '冇開夜晚 → 翌日補返舊晚');
  const s3 = fam(); let dec = 0; for (let d = 0; d < 60; d++) { B.choose(s3, 'kidA', 'job', 'garden', at(d, 12)); B.scan(s3, at(d, 12)); } dec = Object.keys(VS.st(s3).decor).length;
  ok(dec >= 1 && dec <= 3, '園丁：有機會送花圃擺設（螢火小販 3 件，送晒就停）', dec);
  const s4 = fam(), c0 = HS.commissionLeft(s4, 'win_star'); for (let d = 0; d < 30; d++) { B.choose(s4, 'kidA', 'job', 'post', at(d, 12)); B.scan(s4, at(d, 12)); }
  ok(HS.commissionLeft(s4, 'win_star') < c0 || HS.st(s4).owned.win_star, '郵差：委託家具進度提早', [c0, HS.commissionLeft(s4, 'win_star')]);
  const s5 = fam(); const p5 = S2.st(s5); p5.phase = 'kid'; p5.rel = 'friend'; S2.today(s5, NOW).n = 0; const i0 = p5.intim; S2.eatTogether(s5, NOW); const one = p5.intim - i0;
  B.choose(s5, 'kidA', 'job', 'chef', NOW); const i1 = p5.intim; const rr = S2.eatTogether(s5, NOW + 1000); ok(p5.intim - i1 === one + 1 && rr.chef === 1, '廚師：細佬一齊食飯親密 +1', [one, p5.intim - i1]);
  S2.today(s5, NOW).n = 10; const i2 = p5.intim; S2.eatTogether(s5, NOW + 2000); ok(p5.intim === i2, '每日親密上限 10 不變');
}
console.log('⑤ 每日 12 碎上限＋經濟');
{ const s = fam(); let max = 0, tot = 0; const w0 = W(s);
  for (const id of ['kidA', 'kidB', 'trX']) B.devDays(s, id, 'post', 20);
  for (let d = 0; d < 30; d++) { const t = at(d, 12); B.scan(s, t, { boot: true }); B.choose(s, 'tr0', 'expedition', null, t); for (const id of ['kidA', 'kidB', 'trX']) B.choose(s, id, 'job', 'post', t); B.scan(s, t + 1000); B.scan(s, at(d, 22)); max = Math.max(max, B.st(s).day.sh); }
  tot = W(s) - w0; ok(max <= 12, '遠足＋工作每日最多 12 碎', max);
  const sink = Object.values(HS.FURN).filter(f => f.src === 'shop').reduce((a, f) => a + f.price, 0) + VS.CFG.shop.reduce((a, x) => a + x.price, 0);
  ok(tot >= sink, '30 日 5b 收入 ≥ 全部家具＋小販擺設（淨值 ≥0）', { tot, sink });
}
console.log('⑥ sanitize／停用');
{ const s = fam(); F.st(s).b5 = { day: 'x', plan: { a: 3, kidA: { a: 'job', job: 'zz' } }, away: { kidA: { at: 'q' } }, jobs: { kidA: { post: -3, zz: 1 } }, trips: [1, { sv: 'no' }], stk: { no: 1 } };
  const o = B.st(s); ok(o.plan.kidA.job === 'post' && !o.plan.a && !o.away.kidA && o.jobs.kidA.post === 0 && !o.jobs.kidA.zz && !o.trips.length && !Object.keys(o.stk).length, '壞存檔 sanitize');
  B.setOn(false); ok(B.choose(s, 'kidA', 'job', 'post', NOW).reason === 'off' && !B.scan(s, NOW).length && !F.LIVE.job_cap_plus1, '?l5b=0：停用（Lv6 解鎖返做「5b」）'); B.setOn(true);
  F.st(s).km = { id: 'kidB', kind: 'kid', fk: 'B3', name: '棉棉', snap: {} }; ok(!B.plan(s, NOW).rows.some(r => r.id === 'kidB') && B.choose(s, 'kidB', 'rest', null, NOW).reason === 'main', '細佬做主養：唔出現喺每日安排');
}
console.log('⑦ 時鐘倒退');
{ const s = fam(), w0 = W(s); B.choose(s, 'kidA', 'job', 'post', at(2, 12)); const w1 = W(s); ok(w1 > w0, '第 2 日返工出糧');
  B.scan(s, at(0, 12)); B.scan(s, at(2, 13)); ok(W(s) === w1, '撥鐘返去再撥返嚟：唔會重收糧', [w1, W(s)]);
  B.scan(s, at(3, 12)); ok(W(s) > w1, '真係第 3 日先出糧'); }
console.log(`\n${pass} 過 / ${fail} 唔過`); process.exit(fail ? 1 : 0);
