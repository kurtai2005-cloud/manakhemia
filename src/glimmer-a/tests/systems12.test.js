/* systems12 第 1 批 Node 無依賴測試：node tests/systems12.test.js
   系統 7 天氣／季節（14 日連續模擬：每週 1–3 場雨、每場 1–3h；季節＝香港月份）。數值讀 PARAMS.systems12。 */
const S = require('../src/sim.js');
const D = require('../src/data.js');
const X = require('../src/systems.js');
const P = D.PARAMS, C = P.systems12, W = C.weather;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }

console.log('① 系統 7 天氣：14 日連續模擬（每週 1–3 場雨、每場 1–3h）');
{
  const mon = new Date(2026, 10, 2).getTime();   // 2026-11-02 星期一 → 14 日＝兩個完整週
  let allOk = true, lenOk = true, bad = '', tot = { clear: 0, overcast: 0, rain: 0, fog: 0 }, nSp = 0, days = 0, rainDays = 0;
  for (let seed = 1; seed <= 200; seed++) {
    const r = X.simulate(seed * 7919, mon, 14, 5), wk = Object.values(r.weeks);
    if (Object.keys(r.weeks).length !== 2 || wk.some(n => n < W.rainPerWeek[0] || n > W.rainPerWeek[1])) { allOk = false; bad = bad || seed + ':' + JSON.stringify(r.weeks); }
    r.spells.forEach(x => { nSp++; if (x.hours < W.rainHours[0] - 0.09 || x.hours > W.rainHours[1] + 0.09) { lenOk = false; bad = bad || 'len ' + JSON.stringify(x); } });
    for (const k in r.hist) tot[k] += r.hist[k];
    for (let d = 0; d < 14; d++) { days++; if (X.dayBase(seed * 7919, X.dayNum(mon) + d) === W.rainDayBase && X.rainSpells(seed * 7919, X.weekOf(X.dayNum(mon) + d)).some(s => s.dn === X.dayNum(mon) + d)) rainDays++; }
  }
  ok(allOk, `200 個 seed × 14 日：每週雨場數 ∈ [${W.rainPerWeek}]`, bad);
  ok(lenOk, `每場雨 ${W.rainHours[0]}–${W.rainHours[1]}h（${nSp} 場）`, bad);
  const rdp = rainDays / days * 100; ok(rdp >= 12 && rdp <= 25, `落雨日比例 ≈ 雨 ${W.weights.rain}%（實際 ${rdp.toFixed(1)}%）`);
  const n = Object.values(tot).reduce((a, b) => a + b, 0), fogP = tot.fog / n * 100, ovP = tot.overcast / n * 100, clP = tot.clear / n * 100;
  ok(fogP > 2 && fogP < 9, `霧 ≈ ${W.weights.fog}%（${fogP.toFixed(1)}%）`); ok(clP > 50 && clP < 70, `晴 ≈ ${W.weights.clear}%（${clP.toFixed(1)}%）`); ok(ovP > 18 && ovP < 40, `陰（含落雨日底色）（${ovP.toFixed(1)}%）`);
  const t = mon + 5 * 3600e3 + 123456; ok(X.weatherAt(t, 99) === X.weatherAt(t, 99) && X.simulate(99, mon, 14).spells.length === X.simulate(99, mon, 14).spells.length, '同 seed 同時刻 → 同天氣（決定性）');
  const one = X.simulate(4242, mon, 14, 10); ok(one.spells.every(x => x.from >= W.rainFromH - 0.01 && x.from + x.hours <= W.rainToH + 0.01), `雨只喺 ${W.rainFromH}:00–${W.rainToH}:00`, JSON.stringify(one.spells));
  ok(P.evo6.branch.weather.states.includes('fog') && !P.evo6.branch.weather.route.fog, 'fog 加入天氣狀態，唔計路線分');
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
  ok(!q.list.some(x => x.route), '冇照顧分 → 冇路線委託（3 個基本）', JSON.stringify(q.list.map(x => x.k)));
  ok(q.list.map(x => x.k).sort().join() === Q.base.slice().sort().join(), '基本委託＝餵 2／淋水 1／陪玩 1（spec 例）');
  // 偏向領先路線：先做 rinse 照顧令水珠領先
  s = mk(); for (let i = 0; i < 6; i++) S.noteCare(s, 12, 'rinse'); s.evo.b5sys = null; s.sys12 = null; X.st(s); now = day0 + 86400e3; X.questTick(s, now, s.ev); q = X.quests(s, now);
  const rq = q.list.find(x => x.route);
  ok(rq && rq.route === S.routeLead(s).form || (rq && rq.route === 'tide'), '領先水珠 → 其中 1 個委託偏向（淋水，標路線）', JSON.stringify(q.list));
  for (const r of ['shroom', 'crystal', 'moon', 'ember']) { const s2 = mk(); s2.evo = { evIn: {}, care: {}, b5: { sprout: { all: 10, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0, [r]: 8 } }, cl: { sprout: { sum: 95 * 100, sec: 100 } } }; const L = X.genQuests(s2, '2026-11-05'); ok(L[0].route === r && L[0].k === Q.routeKind[r] && L.length === 3 && new Set(L.map(x => x.k)).size === 3, `領先 ${r} → 委託 ${Q.routeKind[r]}`, JSON.stringify(L)); }
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
  const rq2 = X.quests(s, now).list.find(x => x.route); for (let i = 0; i < rq2.need; i++) S.noteCare(s, 12, Q.kinds[rq2.k].counts[0]);
  ok(s.evo.b5sys && s.evo.b5sys.sprout && s.evo.b5sys.sprout[rq2.route] === SY.sources.questRoute.pts, `路線委託完成 → ${rq2.route} 新系統分 +${SY.sources.questRoute.pts}`, JSON.stringify(s.evo.b5sys));
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
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
