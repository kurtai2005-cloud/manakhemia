/* systems12 第 1 批 Node 無依賴測試：node tests/systems12.test.js
   系統 7 天氣／季節（v10.2 一日一抽：晴60／陰20／雨15／霧5；季節＝香港月份）。數值讀 PARAMS.systems12。 */
const S = require('../src/sim.js');
const D = require('../src/data.js');
const X = require('../src/systems.js');
const P = D.PARAMS, C = P.systems12, W = C.weather;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }

console.log('① 系統 7 天氣：v10.2 一日一抽（晴60／陰20／雨15／霧5，成日不變；舊每週雨場已刪）');
{
  const mon = new Date(2026, 10, 2).getTime(), PR = Object.fromEntries(P.evo6.branch.weather.probs);
  ok(PR.clear === 60 && PR.overcast === 20 && PR.rain === 15 && PR.fog === 5, '機率 config：晴60／陰20／雨15／霧5', JSON.stringify(PR));
  ok(W.perDay === true && !('rainPerWeek' in W) && !('rainHours' in W) && !('rainDayBase' in W) && !('weights' in W) && !X.rainSpells && !X.dayBase, '舊「每週落雨 1–3 次、每次 1–3h」config／函數已刪');
  let mixed = 0, tot = { clear: 0, overcast: 0, rain: 0, fog: 0 }, days = 0, rainWk0 = 0, wks = 0;
  for (let seed = 1; seed <= 400; seed++) {
    const r = X.simulate(seed * 7919, mon, 28, 20); mixed += r.mixed; days += r.days.length;
    for (const k in r.dayHist) tot[k] += r.dayHist[k];
    for (let w = 0; w < 4; w++) { wks++; if (!r.days.slice(w * 7, w * 7 + 7).some(d => d.w === 'rain')) rainWk0++; }
  }
  ok(mixed === 0 && days === 400 * 28, `400 seed × 28 日（每 20 分鐘取樣）：每日天氣全日一致（混雜樣本 ${mixed}）`);
  for (const k of ['clear', 'overcast', 'rain', 'fog']) { const pc = tot[k] / days * 100; ok(Math.abs(pc - PR[k]) < (PR[k] >= 15 ? 1.5 : 0.8), `${X.WEATHER_NAME[k]}日 ≈ ${PR[k]}%（實際 ${pc.toFixed(2)}%）`); }
  ok(rainWk0 > 0, `冇保底每週雨場（成週無雨 ${(rainWk0 / wks * 100).toFixed(1)}% ≈ 0.85^7≈32%）`);
  const t = mon + 5 * 3600e3 + 123456; ok(X.weatherAt(t, 99) === X.weatherAt(t, 99) && X.weatherAt(t, 99) === S.dayWeather(99, mon + 23.9 * 3600e3), '同 seed 同日 → 同天氣（決定性；00:00–23:59 同一個）');
  ok(X.weatherAt(t, 99) === X.dayWeatherN(99, X.dayNum(t)) && S.dayWeatherN === S.dayWeatherN && typeof S.dayWeather === 'function', '遊戲／日記／sweep 共用 sim.dayWeatherN');
  { let diff = 0; for (let d = 0; d < 200; d++) if (S.dayWeatherN(1, 20000 + d) !== S.dayWeatherN(2, 20000 + d)) diff++; ok(diff > 40, `唔同 seed → 唔同日程（200 日 ${diff} 日唔同）`); }
  { // 舊存檔：v10.1 前 rain 窗只係 seed＋時間計（冇入存檔）；diary 今日 tr.wx 記住雨 → 讀入唔殘留、唔 crash
    const s0 = S.newState(mon, 4242), k0 = S.dayKey(mon + 13 * 3600e3); s0.sys12 = { diary: { list: [], tr: { day: k0, gen: 1, foods: {}, care: {}, n: 0, stages: [], st0: 'sprout', stLast: 'sprout', mood: [0, 0], mt: 0, wt: 0, wx: { rain: 4, overcast: 2 } } }, wx: { rainUntil: mon + 14 * 3600e3 } };
    const s1 = S.deserialize(S.serialize(s0)); X.st(s1);
    ok(s1.sys12.diary.tr.wx.rain === 4 && X.weatherAt(mon + 13 * 3600e3, s1.seed) === S.dayWeather(s1.seed >>> 0, mon) && X.weatherAt(mon + 14.5 * 3600e3, s1.seed) === X.weatherAt(mon + 13 * 3600e3, s1.seed), '舊存檔（落緊雨中途）讀入：天氣即跟當日抽籤、成日一致；日記已見天氣保留');
    ok(!('wx' in s1.sys12), '舊存檔多餘 sys12.wx（雨窗）欄位 → 遷移清走', JSON.stringify(Object.keys(s1.sys12)));
  }
  ok(P.evo6.branch.weather.states.includes('fog') && P.evo6.branch.weather.route.fog && P.evo6.branch.weather.route.fog.w === P.evo6.branch.weather.route.overcast.w, 'fog 喺天氣狀態；v10：霧當陰（菇傘 0.5）');
  ok(P.evo6.branch.weather.route.rain.to === 'shroom', '落雨路線照 v4/v5 config（菇傘）— 見報告詮釋');
}
console.log('② 系統 7 季節：香港月份');
{
  const m = (mo) => X.seasonOf(new Date(2026, mo - 1, 15).getTime());
  ok([3, 4, 5].every(k => m(k) === 'spring') && [6, 7, 8].every(k => m(k) === 'summer') && [9, 10, 11].every(k => m(k) === 'autumn') && [12, 1, 2].every(k => m(k) === 'winter'), '春3–5／夏6–8／秋9–11／冬12–2');
  ok(X.shiverMul('fog', 'winter') === W.shiverFogMul * W.shiverWinterMul && X.shiverMul('clear', 'summer') === 1, '打冷震：霧／冬機率倍數');
}

console.log('③ 系統 1 每日小委託＋星星碎錢包（每日 30＝委託 15＋其他 15）');
{
  const Q = C.quests, SY = P.evo6.branch.systems, day0 = new Date(2026, 10, 2, 10, 0).getTime();
  let now = day0; S.setNowFn(() => now); S.setHourFn(() => new Date(now).getHours() + new Date(now).getMinutes() / 60); S.setWeatherFn(() => null);
  const mk = (stage) => { const s = S.newState(day0, 4242); s.stage = stage || 'sprout'; s.cq = 60; s.ev = []; return s; };
  let s = mk(); X.questTick(s, now, s.ev); let q = X.quests(s, now);
  ok(q.list.length === Q.perDay && q.list.every(x => Q.kinds[x.k]) && new Set(q.list.map(x => x.k)).size === Q.perDay, `每日 ${Q.perDay} 個委託（唔重覆）`, JSON.stringify(q.list));
  ok(q.list.every(x => Q.pool.includes(x.k) && !x.route) && Q.pool.slice().sort().join() === 'feed,pat,play', 'v10.2 A：3 個由 餵／玩／摸頭 池抽（冇硬包淋水）', JSON.stringify(q.list.map(x => x.k)));
  ok(!q.list.some(x => x.k === 'rinse') && Q.rinseIfLead === 'tide', '水珠冇領先 → 冇淋水委託');
  { const sT = mk(); sT.evo = { evIn: {}, care: {}, b5: { sprout: { all: 10, tide: 8, shroom: 1, crystal: 0, moon: 1, ember: 0 } }, cl: { sprout: { sum: 95 * 100, sec: 100 } } };
    let tideOk = 0, otherRinse = 0; for (let d = 0; d < 30; d++) { const k = S.dayKey(day0 + d * 864e5); if (X.genQuests(sT, k).some(x => x.k === 'rinse')) tideOk++; }
    for (const r of ['shroom', 'crystal', 'moon', 'ember']) { const s2 = mk(); s2.evo = { evIn: {}, care: {}, b5: { sprout: Object.assign({ all: 10, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0, [r]: 8 }, r === 'crystal' ? { crystal: 0, loginPoop: 5, quickLogin: 5 } : {}) }, cl: { sprout: { sum: 95 * 100, sec: 100 } } };
      for (let d = 0; d < 30; d++) if (X.genQuests(s2, S.dayKey(day0 + d * 864e5)).some(x => x.k === 'rinse')) otherRinse++; }
    ok(X.leadRoute(sT) === 'tide' && tideOk === 30, `水珠領先 → 每日都有淋水委託（30/30＝${tideOk}），取代池中一個`, X.leadRoute(sT));
    ok(otherRinse === 0, '其他路線領先 → 0 個淋水委託', otherRinse);
    const L = X.genQuests(sT, '2026-11-05'); ok(L.length === 3 && new Set(L.map(x => x.k)).size === 3 && L.filter(x => Q.pool.includes(x.k)).length === 2, '水珠領先：淋水＋池入面 2 個（唔重覆）', JSON.stringify(L.map(x => x.k))); }
  { // 路線分：今日輪值路線（逐日平均輪 5 條），3 個齊先 +pts；任何連續 5 日每條各 1 次
    let rot = true, cnt = {}, n = 0; const R = D.BRANCH5;
    for (let sd = 1; sd <= 200; sd++) { const s2 = S.newState(day0, sd * 31); s2.stage = 'sprout'; const seq = [];
      for (let d = 0; d < 100; d++) { const k = S.dayKey(day0 + d * 86400e3), r = X.questRoute(s2, k); seq.push(r); cnt[r] = (cnt[r] || 0) + 1; n++; }
      for (let i = 0; i + 5 <= seq.length; i++) if (new Set(seq.slice(i, i + 5)).size !== 5) rot = false; }
    ok(rot, '任何連續 5 日：5 條路線各輪值 1 次');
    ok(R.every(r => cnt[r] === n / 5), '200 seed × 100 日：每條路線 20%', JSON.stringify(cnt));
    const sA = mk(); for (let i = 0; i < 9; i++) S.noteCare(sA, 12, 'play'); const sB = mk();
    ok(X.questRoute(sA, '2026-11-05') === X.questRoute(sB, '2026-11-05'), '領先火苗都唔會改輪值路線（唔跟領先）');
    ok(typeof SY.sources.questRoute.pts === 'number' && SY.sources.questRoute.pts === 1 && !SY.sources.questRoute.perRoute, '路線委託分：5 條路線同一個 pts（1），火苗唔多攞', JSON.stringify(SY.sources.questRoute));
    ok(SY.maxRouteSharePct === 25, '25% 單路線 cap 保留');
    ok(Q.kinds.pat && Q.kinds.pat.counts.includes('pat') && Q.kinds.poopQuick.label === '返嚟 2 分鐘內執晒便便', '摸頭委託 kind（pat）；晶角舊文案保留俾舊存檔');
  }
  { const s3 = mk(); s3.poops = 1; S.poopAges(s3).push(0); const got = []; S.addCareHook((x, k) => { if (x === s3) got.push(k); }); const b0 = X.bond(s3, now).v;
    S.noteLogin(s3, now); S.clearPoop(s3); const b1 = X.bond(s3, now).v;
    ok(got.join() === 'poop,poopQuick', 'v10 即清上線 → hook 收 poop 再收 poopQuick（推委託）', got.join());
    ok(b1 - b0 === P.systems12.bond.care, '即清只當 1 次照顧計親密度（poopQuick 唔重覆加）', b0 + '→' + b1); }
  ok(JSON.stringify(X.genQuests(s, '2026-11-09')) === JSON.stringify(X.genQuests(s, '2026-11-09')), '同 seed 同日 → 委託一樣');
  // 做齊 → 即刻發 15（部份完成唔發）
  s = mk(); now = day0; X.questTick(s, now, s.ev); const before = X.wallet(s, now).total;
  const kindsOf = (x) => Q.kinds[x.k].counts[0];
  const L0 = X.quests(s, now).list; S.noteCare(s, 12, kindsOf(L0[0])); if (L0[0].need > 1) S.noteCare(s, 12, kindsOf(L0[0]));
  ok(X.wallet(s, now).total === before && !X.quests(s, now).paid, '未做齊 → 唔發獎（唔罰）');
  for (const x of L0.slice(1)) for (let i = 0; i < x.need; i++) S.noteCare(s, 12, kindsOf(x));
  let w = X.wallet(s, now); ok(X.quests(s, now).done && X.quests(s, now).paid && w.total === Q.reward * Q.perDay && w.q === 15, `3 個齊 → 即刻 +${Q.reward * Q.perDay} 星星碎`, JSON.stringify(w));
  ok(s.ev.some(e => e.type === 'sys12' && e.what === 'paid' && e.n === 15), 'ev：sys12 quest paid');
  for (const x of L0) S.noteCare(s, 12, kindsOf(x)); ok(X.wallet(s, now).total === 15, '同日再做 → 唔重覆發');
  // 錢包上限
  let g = 0; for (let i = 0; i < 10; i++) g += X.grant(s, 4, 'drop', now); w = X.wallet(s, now);
  ok(g === C.wallet.otherCap && w.today === SY.stardustDailyCap && w.today === 30, `其他來源每日 ≤ ${C.wallet.otherCap}；總 ≤ ${SY.stardustDailyCap}`, JSON.stringify(w));
  ok(X.grant(s, 5, 'quest', now) === 0, '委託分帳滿 → 0');
  now = day0 + 86400e3; ok(X.grant(s, 3, 'drop', now) === 3 && X.wallet(s, now).today === 3 && X.wallet(s, now).total === 33, '00:00 後重置每日上限（總數保留）');
  // 00:00 重置：新委託；斷線補發（3 個齊但未發）
  s = mk(); now = day0; X.questTick(s, now, s.ev); const q1 = X.st(s).quests; q1.list.forEach(x => { x.n = x.need; }); q1.paid = false;
  now = day0 + 86400e3 + 3600e3; const r1 = X.questTick(s, now, s.ev);
  ok(r1.late && r1.paid === 15 && r1.reset && X.quests(s, now).day === S.dayKey(now) && !X.quests(s, now).done, '斷線補發：舊日 3 個齊未發 → 下次開補 15、再換新委託', JSON.stringify(r1));
  ok(X.st(s).wallet.log.some(l => l.d === S.dayKey(day0) && l.n === 15), '補發計返嗰日（唔食今日上限）');
  ok(X.questTick(s, now + 1000, s.ev).paid === 0, '補發唔會重覆');
  { const s6 = mk(); const t1 = day0 + 86400e3; X.grant(s6, 15, 'quest', t1); X.grant(s6, 15, 'quest', t1, S.dayKey(day0)); const w6 = X.wallet(s6, t1);
    ok(w6.q === 15 && w6.total === 30 && X.grant(s6, 1, 'quest', t1) === 0, '補發舊日唔影響今日分帳（每日各自計）', JSON.stringify(w6)); }
  // 光卵冇委託
  s = mk('egg'); X.questTick(s, now, s.ev); ok(X.quests(s, now).list.length === 0, '光卵：未有委託');
  // 路線分：完成路線委託 → E.b5sys +1；branch5Check 每條 ≤ 25%
  s = mk(); for (let i = 0; i < 9; i++) S.noteCare(s, 12, 'rinse'); s.sys12 = null; now = day0 + 2 * 86400e3; X.questTick(s, now, s.ev);
  { const q2 = X.quests(s, now), rt = q2.route, L2 = q2.list; let mid = null;
    L2.forEach((x, j) => { for (let i = 0; i < x.need; i++) { if (x.k === 'pat') X.notePat(s, now, s.ev); else S.noteCare(s, 12, Q.kinds[x.k].counts[0]); } if (j === 1) mid = JSON.stringify(s.evo.b5sys || {}); });
    ok(D.BRANCH5.includes(rt) && mid === '{}' || (mid && !(JSON.parse(mid).sprout || {})[rt]), '未齊 3 個 → 輪值路線未加分', mid);
    ok(s.evo.b5sys && s.evo.b5sys.sprout && s.evo.b5sys.sprout[rt] === SY.sources.questRoute.pts && X.quests(s, now).paid, `3 個齊 → 今日輪值路線 ${rt} 新系統分 +${SY.sources.questRoute.pts}（＋15 星星碎）`, JSON.stringify(s.evo.b5sys));
    X.notePat(s, now, s.ev); ok(s.evo.b5sys.sprout[rt] === SY.sources.questRoute.pts, '同日唔會重覆加路線分'); }
  { const sP = mk(); X.questTick(sP, now, sP.ev); const c0 = JSON.stringify(sP.evo.care), b0 = X.bond(sP, now).v; X.notePat(sP, now, sP.ev);
    const pq = X.quests(sP, now).list.find(x => x.k === 'pat');
    ok(pq && pq.n === 1 && JSON.stringify(sP.evo.care) === c0 && X.bond(sP, now).v === b0, '摸頭 → 推「摸摸佢個頭」委託；唔計照顧／CQ／親密照顧分', JSON.stringify(pq));
    sP.sleeping = true; X.notePat(sP, now, sP.ev); ok(X.quests(sP, now).list.find(x => x.k === 'pat').n === 1, '瞓緊覺撳唔計摸頭'); }
  { // 舊存檔：今日委託仲係舊式（淋水／路線委託帶 route）→ 照做照計；聽日換新式
    const sO = mk(); sO.sys12 = { quests: { day: S.dayKey(now), list: [{ k: 'poopQuick', need: 1, n: 0, route: 'crystal' }, { k: 'rinse', need: 1, n: 0, route: null }, { k: 'feed', need: 2, n: 0, route: null }], paid: false, routePaid: false } }; X.st(sO);
    S.noteCare(sO, 12, 'poopQuick'); ok(sO.evo.b5sys && sO.evo.b5sys.sprout && sO.evo.b5sys.sprout.crystal === SY.sources.questRoute.pts, '舊存檔路線委託（晶角）照加分', JSON.stringify(sO.evo.b5sys));
    X.questTick(sO, now + 864e5, sO.ev); const nq = X.quests(sO, now + 864e5); ok(nq.list.every(x => Q.pool.includes(x.k) || x.k === 'rinse') && D.BRANCH5.includes(nq.route), '舊存檔聽日 → 新式（池＋輪值路線）', JSON.stringify(nq)); }
  { const s3 = mk(); s3.evo = { evIn: {}, care: {}, b5: { sprout: { all: 12, tide: 3, shroom: 6, crystal: 0, moon: 3, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 50, moon: 0.5 } } };
    const B = S.branch5Check(s3), capT = 3 * SY.maxRouteSharePct / (100 - SY.maxRouteSharePct);
    ok(Math.abs(B.sys.capped.tide - capT) < 1e-3 && B.sys.capped.moon === 0.5 && Math.abs(B.score.tide - 4) < 1e-3, `新系統分每條 ≤ 25%（照顧 3 → 新系統最多 ${capT}；佔 ${(capT / (3 + capT) * 100).toFixed(0)}%）`, JSON.stringify(B.sys));
    ok(Math.abs(B.all - (12 + capT + 0.5)) < 1e-3, '新系統分加入總分', B.all);
    const keep = SY.enabled; SY.enabled = false; const B2 = S.branch5Check(s3); SY.enabled = keep; ok(B2.score.tide === 3 && B2.all === 12, 'systems.enabled=false → 唔計新系統分'); }
  { const s4 = mk(); s4.evo = { evIn: {}, care: {}, b5: { sprout: { all: 5, tide: 0, shroom: 5, crystal: 0, moon: 0, ember: 0 } }, cl: {}, b5sys: { sprout: { tide: 9 } } }; ok(S.branch5Check(s4).score.tide === 0, '冇照顧分嘅路線 → 新系統分＝0（唔可以淨靠委託開路線）'); }
  // sanitize
  s = mk(); s.sys12 = { wallet: { total: 'x', q: -5, log: 'bad', days: { 'bad': 1, '2026-11-02': { q: -3, o: 'x' } } }, quests: { list: [{ k: 'zzz' }, { k: 'feed', need: 2, n: 1, route: 'evil' }] } }; X.st(s);
  ok(s.sys12.wallet.total === 0 && s.sys12.wallet.q === undefined && Object.keys(s.sys12.wallet.days).join() === '2026-11-02' && s.sys12.wallet.days['2026-11-02'].q === 0 && s.sys12.wallet.days['2026-11-02'].o === 0 && Array.isArray(s.sys12.wallet.log) && s.sys12.quests.list.length === 1 && s.sys12.quests.list[0].route === null, '存檔 sanitize（錢包／委託）');
  const s5 = S.deserialize(S.serialize(Object.assign(mk(), { sys12: { wallet: { total: 7 } } })), now); ok(X.wallet(s5, now).total === 7, '存檔來回保留星星碎');
  S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
}
console.log('④ 系統 6 親密度＋心聲');
{
  const B = C.bond, day0 = new Date(2026, 10, 2, 10, 0).getTime(); let now = day0;
  S.setNowFn(() => now); S.setHourFn(() => 12); S.setWeatherFn(() => null);
  const mk = () => { const s = S.newState(day0, 99); s.stage = 'sprout'; s.cq = 60; s.ev = []; s.needs.hunger = 10; return s; };
  let s = mk(); ok(X.bond(s, now).v === B.start && B.start === 20, `新團絨親密度 ${B.start}`);
  ok(B.lines.length === 5 && B.lines.every(a => a.length >= 6 && a.every(l => typeof l === 'string' && l.length >= 6)) && new Set(B.lines.flat()).size === 30, '5 段心聲 × 各 6 句（唔重覆）');
  S.rinse(s); ok(X.bond(s, now).v === B.start + B.care, '照顧 +1（經 sim hook）');
  X.onLongPress(s, now, s.ev); ok(X.bond(s, now).v === B.start + B.care + B.longPress, '長撳 +2');
  for (let i = 0; i < 30; i++) S.rinse(s); ok(X.bond(s, now).v === B.start + B.dailyGainCap && X.bond(s, now).todayGain === B.dailyGainCap, `每日最多 +${B.dailyGainCap}`, X.bond(s, now).v);
  now += 86400e3; S.rinse(s); ok(X.bond(s, now).v === B.start + B.dailyGainCap + 1, '第二日再加得');
  // 冇照顧嘅日 −2（最低 20）
  X.bondTick(s, now, s.ev); const v0 = X.bond(s, now).v; now += 4 * 86400e3; const r = X.bondTick(s, now, s.ev);
  ok(r.days === 3 && X.bond(s, now).v === v0 - 3 * B.ignoreDecay, '3 日冇照顧 → −6（今日唔計）', JSON.stringify(r));
  ok(X.bondTick(s, now + 3600e3, s.ev).days === 0, '同日再檢查唔重扣');
  now += 30 * 86400e3; X.bondTick(s, now, s.ev); ok(X.bond(s, now).v === B.floor, `長期唔理 → 最低 ${B.floor}`);
  { const s2 = mk(); X.bondTick(s2, now, s2.ev); s2.careDays = [S.dayKey(now), S.dayKey(now + 86400e3)]; now += 2 * 86400e3; S.rinse(s2); const v = X.bond(s2, now).v; X.bondTick(s2, now, s2.ev); ok(X.bond(s2, now).v === Math.max(B.floor, v), '有照顧嘅日唔扣'); }
  // 段落
  s = mk(); X.bondOf(s).v = 19; ok(X.voiceLines(s).length === 0, '親密度 < 20 → 未有心聲');
  X.bondOf(s).v = 20; ok(X.voiceLines(s).length === 1, '20 → 解鎖第 1 段');
  X.bondOf(s).v = 100; ok(X.voiceLines(s).length === 5, '100 → 5 段全解鎖');
  // 30%＋冷卻 10 分鐘
  { let hit = 0, n = 0, t0 = day0; const s3 = mk(); X.bondOf(s3).v = 60; let seed = 1; const rng = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < 4000; i++) { t0 += B.voice.cooldownSec * 1000; n++; if (X.voiceTry(s3, t0, { rng }).ok) hit++; }
    ok(Math.abs(hit / n - B.voice.chance) < 0.03, `撳一下 ≈ ${B.voice.chance * 100}% 出心聲（${(hit / n * 100).toFixed(1)}%）`);
    const s4 = mk(); const a = X.voiceTry(s4, day0, { force: true }), b = X.voiceTry(s4, day0 + 599e3, { rng: () => 0 }), c = X.voiceTry(s4, day0 + 600e3, { rng: () => 0 });
    ok(a.ok && !b.ok && b.why === 'cooldown' && c.ok, `冷卻 ${B.voice.cooldownSec / 60} 分鐘`, JSON.stringify([a.ok, b, c.ok]));
    ok(B.lines[a.tier - 1].includes(a.line), '心聲出自已解鎖段落'); }
  // 紀念冊＋新一代
  s = mk(); s.stage = 'elder'; s.form = 'soft'; s.fadeReady = true; X.bondOf(s).v = 77; X.bondTick(s, now, s.ev); X.bondOf(s).v = 80;
  const f = S.fade(s, now); ok(f.ok && f.memorial.bond === 80 && f.memorial.bondElder === 77, '化光紀念冊記低親密度（靜光＋化光）', JSON.stringify(f.memorial));
  ok(X.bond(s, now).v === B.start, '新一代親密度由 20 開始');
  s = mk(); s.stage = 'egg'; ok(X.bondAdd(s, 5, now) === 0 && !X.voiceTry(s, now, { force: true }).ok, '光卵：唔加親密、冇心聲');
  s = mk(); s.sys12 = { bond: { v: 'x', heard: 5, lastVoice: -1 } }; X.st(s); ok(s.sys12.bond.v === B.start && Array.isArray(s.sys12.bond.heard) && s.sys12.bond.lastVoice === 0, '存檔 sanitize（親密）');
  S.setNowFn(null); S.setHourFn(null); S.setWeatherFn(null);
}
console.log('⑤ 系統 12：懸浮小驚喜（設定、replay 入帳、每日 5 粒、提醒時間）');
{
  const U = C.surprise, base = new Date(2026, 10, 3, 14, 0, 0).getTime(), now = base;
  const mk = () => { const s = S.newState(base - 86400e3 * 3, 5); s.stage = 'sprout'; return s; };
  let s = mk(); let u = X.surp(s);
  ok(u.on.drop === true && u.on.water === false && u.on.sleep === false, '預設：星星碎開、提醒閂');
  ok(u.waterH === U.water.def && u.sleepAt === U.sleep.def, '預設間隔／時間讀 config');
  ok(X.surpSet(s, 'water', true, now) && u.on.water && u.ts === now, '開飲水提醒（記 ts）');
  ok(!X.surpSet(s, 'waterH', 5, now) && X.surpSet(s, 'waterH', 3, now) && u.waterH === 3, '飲水間隔只限 1–3h');
  ok(!X.surpSet(s, 'sleepAt', '21:00', now) && X.surpSet(s, 'sleepAt', '00:00', now), '早瞓時間只限 config 選項');
  // replay drop
  s = mk(); let r = X.applyOverlay(s, [0, 1, 2, 3, 4, 5, 6].map(i => ({ k: 'drop', t: now - i * 1000 })), now);
  ok(r.drop === 5 && X.wallet(s, now).total === 5 && X.wallet(s, now).o === 5, '懸浮 7 粒 → 今日最多入 5 粒（計 otherCap）', JSON.stringify(r));
  ok(X.overlaySys12(s, now).surp.drop.room === 0, 'snapshot：今日尚餘 0');
  r = X.applyOverlay(s, [{ k: 'drop', t: now - 86400e3 }], now); ok(r.drop === 1, '尋日嘅（遲咗 drain）計返尋日上限');
  s = mk(); X.grant(s, 13, 'mg', now); r = X.applyOverlay(s, [1, 2, 3].map(i => ({ k: 'drop', t: now - i })), now); ok(r.drop === 2 && X.wallet(s, now).o === 15, 'otherCap 15 同小遊戲共用');
  s = mk(); X.surpSet(s, 'drop', false, now); r = X.applyOverlay(s, [{ k: 'drop', t: now }], now); ok(r.drop === 0 && X.wallet(s, now).total === 0, '閂咗星星碎 → 唔入帳');
  ok(X.overlaySys12(s, now).surp.on.drop === false, 'snapshot 帶埋開關（懸浮閂咗就完全唔掉）');
  s = mk(); s.stage = 'egg'; r = X.applyOverlay(s, [{ k: 'drop', t: now }], now); ok(r.drop === 0, '光卵唔掉');
  // voice sync
  s = mk(); r = X.applyOverlay(s, [{ k: 'voice', t: now - 5000, line: C.bond.lines[0][0] }], now);
  ok(r.voice === 1 && X.bondOf(s).lastVoice === now - 5000 && X.voiceTry(s, now, { rng: () => 0 }).why === 'cooldown', '懸浮心聲 → 主程式共用冷卻');
  const ov = X.overlaySys12(s, now); ok(ov.voice.lines.length === 1 && ov.voice.chance === C.bond.voice.chance && ov.voice.cooldownSec === C.bond.voice.cooldownSec, 'snapshot 心聲：已解鎖段＋30%／10 分鐘');
  // set sync（後改贏）
  s = mk(); X.surpSet(s, 'water', true, now); r = X.applyOverlay(s, [{ k: 'set', key: 'water', val: false, t: now - 1000 }], now); ok(r.set === 0 && X.surp(s).on.water, '懸浮舊設定（早過主程式改）唔覆蓋');
  r = X.applyOverlay(s, [{ k: 'set', key: 'water', val: false, t: now + 1 }], now + 10); ok(r.set === 1 && !X.surp(s).on.water, '懸浮新設定 → 同步落主程式');
  // timers
  ok(X.dropNext(0, 0) === U.drop.minH * 3600e3 && X.dropNext(0, 0.999999) < U.drop.maxH * 3600e3, '掉落間隔 2–4h');
  const at = (h, m) => new Date(2026, 10, 3, h, m).getTime();
  ok(X.waterDue(at(10, 0) - 2 * 3600e3, 2, at(10, 0)) && !X.waterDue(at(10, 0) - 3600e3, 2, at(10, 0)), '飲水：夠鐘先出');
  ok(!X.waterDue(0, 1, at(23, 0)) && !X.waterDue(0, 1, at(7, 0)), '飲水：夜晚／清早唔出');
  let d = X.sleepDue('23:00', '', at(23, 20)); ok(d.due && d.night === '2026-11-03', '早瞓 23:00 → 23:20 出');
  ok(!X.sleepDue('23:00', d.night, at(23, 40)).due && !X.sleepDue('23:00', '', at(22, 40)).due && !X.sleepDue('23:00', '', at(0, 10)).due, '一晚一次；未到／過咗 60 分鐘唔出');
  d = X.sleepDue('00:00', '', at(0, 30)); ok(d.due && d.night === '2026-11-02', '00:00 提醒當前一晚');
  s = mk(); s.sys12 = { surp: { on: { drop: 'x' }, waterH: 9, drops: { bad: 3, '2026-11-03': -2 } } }; X.st(s); u = s.sys12.surp;
  ok(u.on.drop === true && u.waterH === U.water.def && !('bad' in u.drops) && u.drops['2026-11-03'] === 0, '存檔 sanitize（小驚喜）');
}
console.log('⑥ 系統 3：團絨日記（每日 1 篇、範本＋事件、特別頁、離線日一句、30 日、化光入紀念冊）');
{
  const DC = C.diary; let T = new Date(2026, 10, 3, 10, 0).getTime(); S.setNowFn(() => T);
  const mk = () => { const s = S.newState(T - 86400e3 * 3, 9); s.stage = 'sprout'; return s; };
  let s = mk(); X.diaryStep(s, T); s.needs.hunger = 20; S.feed(s, 'meal'); X.diaryNote(s, 'food', 'meal', T); S.play(s);
  let d = X.diary(s, T); ok(d.list.length === 0 && d.today && d.today.draft, '當日：未寫（草稿）');
  ok(d.today.lines.some(l => l.includes('暖菇飯')), '草稿有食咗乜（暖菇飯）', JSON.stringify(d.today.lines));
  T += 86400e3; X.diaryStep(s, T); d = X.diary(s, T);
  ok(d.list.length === 1 && d.list[0].d === '2026-11-03' && d.list[0].kind === 'normal', '過咗 00:00 → 寫低尋日一篇');
  const e = d.list[0], all = [].concat(...Object.values(DC.weather));
  ok(all.includes(e.lines[1]) && e.lines.length >= 5, '範本：開頭＋天氣＋食＋心情＋照顧＋結尾', JSON.stringify(e.lines));
  ok(e.stickers.includes('food') && e.stickers.every(k => ['sun', 'rain', 'food', 'heart', 'evolve', 'sleep'].includes(k)), '貼紙（遊美 6 款）', e.stickers.join());
  // 進化
  S.enterStage(s, 'juvenile'); X.diaryStep(s, T); T += 86400e3; X.diaryStep(s, T); d = X.diary(s, T);
  const ev = d.list[d.list.length - 1]; ok(ev.kind === 'evolve' && ev.special && ev.lines.some(l => l.includes('跳跳期')) && ev.stickers.includes('evolve'), '進化嗰日 → 特別頁（跳跳期）', JSON.stringify(ev));
  // 離線
  T += 86400e3 * 4; X.diaryStep(s, T); d = X.diary(s, T); const off = d.list.filter(x => x.kind === 'offline');
  ok(off.length === 3 && off.every(x => x.lines.length === 1 && DC.offline.some(l => x.lines[0].includes(l))), '4 日冇開 → 3 個離線日各一句', off.length);
  // 30 日
  for (let i = 0; i < 40; i++) { T += 86400e3; X.diaryNote(s, 'care', 'feed', T); }
  X.diaryStep(s, T); d = X.diary(s, T); ok(d.list.length === DC.keepDays, '最多留 30 篇', d.list.length);
  // 光卵期唔寫
  let s2 = mk(); s2.stage = 'egg'; X.diaryStep(s2, T); T += 86400e3 * 3; X.diaryStep(s2, T); ok(X.diary(s2, T).list.length === 0, '光卵期冇日記（冇離線句）');
  // 化光
  s.stage = 'elder'; s.fadeReady = true; X.diaryStep(s, T); const f = S.fade(s, T);
  ok(f.ok && Array.isArray(f.memorial.diary) && f.memorial.diary.length === DC.keepDays && f.memorial.diary[f.memorial.diary.length - 1].kind === 'fade', '化光 → 特別頁（化光日）＋成本日記入紀念冊', f.memorial.diary && f.memorial.diary.length);
  d = X.diary(s, T); ok(d.list.length === 0, '新一代日記由空白開始');
  T += 86400e3; X.diaryStep(s, T); ok(X.diary(s, T).list.length === 0, '化光當日（光卵）唔再寫多篇');
  s = mk(); s.sys12 = { diary: { list: [5, { d: 1 }, { d: '2026-11-01', lines: ['x'] }], tr: 'bad' } }; X.st(s); ok(s.sys12.diary.list.length === 1 && s.sys12.diary.tr === null, '存檔 sanitize（日記）');
  S.setNowFn(null);
}
console.log('⑧ seasons v2 素材：particleOverlay（sheet＋particles.json）');
{
  const fs = require('fs'), path = require('path'), B = path.join(__dirname, '../art/hd2d/seasons/'), SJ = JSON.parse(fs.readFileSync(B + 'seasons.json', 'utf8'));
  for (const se of ['spring', 'summer', 'autumn', 'winter']) {
    const po = (SJ.seasons[se] || {}).particleOverlay, d = B + se + '/particles/';
    const j = JSON.parse(fs.readFileSync(d + 'particles.json', 'utf8')), png = fs.readFileSync(d + 'sheet.png');
    const sw = png.readUInt32BE(16), sh = png.readUInt32BE(20);
    const frOk = Object.values(j.frames).every(f => f.x + f.w <= sw && f.y + f.h <= sh), anOk = Object.values(j.anims).every(a => a.every(n => j.frames[n]));
    const tyOk = j.types.every(T => T.variants.every(v => j.anims[v] && j.anims[v].length === T.frames) && T.emitter.max > 0 && T.emitter.lifeSec > 0 && ['H1', 'H2', 'H3', 'H4'].every(h => T.emitter.perVariant[h] != null));
    ok(po && po.dir === 'seasons/' + se + '/particles/' && frOk && anOk && tyOk && j.types.map(T => T.name).join() === (po.types || []).join(), `seasons v2 ${se}：粒子 ${j.types.map(T => T.name).join('+')}（frames 喺 sheet 內、anims／emitter 齊）`);
    ok(['H1', 'H2', 'H3', 'H4'].every(h => ['sky', 'far', 'mid', 'fore', 'lightmap'].every(n => fs.existsSync(B + se + '/' + h + '/' + n + '.png')) && fs.existsSync(B + se + '/' + h + '/grade.json')), `seasons v2 ${se}：H1–H4 層＋grade 齊`);
  }
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
