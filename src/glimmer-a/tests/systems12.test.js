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

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
