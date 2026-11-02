/* long6b.test — 6b 真世界連動（遊策 breakthrough-6a6d-spec §6b）：步數差值（基準／重開機／上限）、1000 步 1 格、2000 步 1 碎每日 ≤5、
   散步路裝飾每日 ≤1、換日、天氣 WMO 對應、只改畫面（visWeather／visHour）、冇開＝原狀、存檔冇座標。node tests/long6b.test.js */
const SIM = require('../src/sim.js'), X = require('../src/systems.js'), RW = require('../src/long6b.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 2 + d, h, m || 0, 0).getTime();
const mk = () => { const s = SIM.newState(at(-10, 12), 9); s.stage = 'adult'; s.form = 'tide'; return s; };
const W = (s) => X.st(s).wallet.total;

console.log('① 冇開＝原狀');
{ const s = mk(), w0 = W(s), r = RW.ingest(s, 5000, 1, at(0, 9)); ok(!r.ok && r.why === 'off' && W(s) === w0 && RW.st(s).total === 0, '步數冇開 → 讀數唔入帳、錢包唔變', r);
  ok(RW.visWeather(s, 'rain', at(0, 9)) === 'rain' && RW.visHour(s, 13.5, at(0, 9)) === 13.5, '天氣冇開 → 畫面天氣／鐘＝遊戲原本'); }

console.log('② 步數差值');
{ const s = mk(); RW.setOn(s, 'steps', true); const t = at(0, 9);
  let r = RW.ingest(s, 120000, 1e9, t); ok(r.ok && r.why === 'baseline' && r.steps === 0, '第一次讀數＝基準（唔將開機至今步數當今日）', r);
  r = RW.ingest(s, 120999, 1e9, t + 6e4); ok(r.why === 'delta' && r.steps === 999 && r.tiles === 0, '+999 步 → 未夠 1 格', r);
  r = RW.ingest(s, 121000, 1e9, t + 12e4); ok(r.steps === 1 && r.tiles === 1 && RW.pos(s).tile === 1, '夠 1000 步 → 團絨行 1 格', r);
  r = RW.ingest(s, 122000, 1e9, t + 18e4); ok(r.tiles === 1 && r.shards === 1 && RW.summary(s, t).shards === 1, '2000 步 → 1 粒碎', r);
  r = RW.ingest(s, 300, 1e9 + 5e6, t + 24e4); ok(r.why === 'reboot' && r.steps === 300, '重開機（讀數細咗）→ 差值＝新讀數', r);
  r = RW.ingest(s, 300 + 99999, 1e9 + 5e6, t + 30e4); ok(r.steps === RW.CFG.maxDelta, '單次差值上限 ' + RW.CFG.maxDelta, r);
  ok(RW.summary(s, t).shards === 5, '一日最多 5 粒', RW.summary(s, t));
  r = RW.ingest(s, -1, 0, t); ok(!r.ok && r.why === 'bad', '壞讀數唔入帳');
  r = RW.ingest(s, 'abc', 0, t); ok(!r.ok, '非數字唔入帳'); }

console.log('③ 每日 ≤5 碎、換日');
{ const s = mk(); RW.setOn(s, 'steps', true); const w0 = W(s); let g = 0; for (let i = 0; i < 30; i++) g += RW.credit(s, 1000, at(0, 10)).shards;
  ok(g === 5 && W(s) - w0 === 5 && RW.day(s, at(0, 10)).sh === 5, '3 萬步 → 5 粒（上限）', { g });
  const g2 = RW.credit(s, 2000, at(1, 8)).shards; ok(g2 === 1 && RW.summary(s, at(1, 8)).today === 2000, '翌日重新計（2000 步 → 1 粒）', g2);
  ok(RW.summary(s, at(0, 23)).today === 30000, '舊日記錄保留');
  for (let d = 2; d < 30; d++) RW.credit(s, 100, at(d, 9)); ok(Object.keys(RW.st(s).d).length <= RW.CFG.keepDays, '日記錄最多 ' + RW.CFG.keepDays + ' 日', Object.keys(RW.st(s).d).length); }

console.log('④ 散步路裝飾');
{ let days = 0, got = 0; for (let k = 0; k < 40; k++) { const s = mk(); s.seed = 100 + k; RW.setOn(s, 'steps', true); const r = RW.credit(s, 12000, at(0, 10)); if (r.deco.length) days++; got += r.deco.length;
    if (r.deco.length > RW.CFG.decoPerDay) { ok(false, '每日 ≤1 件', r); break; } }
  ok(days > 5 && days < 40 && got === days, '偶爾執到（40 隻 × 12 格 → ' + days + ' 隻執到，每日最多 1 件）', { days, got }); }
{ const s = mk(); s.seed = 7; RW.setOn(s, 'steps', true); const a = RW.credit(s, 12000, at(0, 10)).deco; const s2 = mk(); s2.seed = 7; RW.setOn(s2, 'steps', true); const b = [];
  for (let i = 0; i < 12; i++) b.push(...RW.credit(s2, 1000, at(0, 10)).deco); ok(JSON.stringify(a) === JSON.stringify(b), '裝飾按格擲（一次過或者逐格都一樣）', { a, b }); }

console.log('⑤ 天氣（只改畫面）');
ok(RW.wmo(0) === 'clear' && RW.wmo(2) === 'clear' && RW.wmo(3) === 'overcast' && RW.wmo(45) === 'fog' && RW.wmo(48) === 'fog', 'WMO 0–2 晴／3 陰／45・48 霧');
ok([51, 55, 61, 65, 67, 80, 82, 95, 99].every(c => RW.wmo(c) === 'rain') && [71, 75, 77, 85, 86].every(c => RW.wmo(c) === 'overcast') && RW.wmo(null) === null, 'WMO 雨／雪→陰／冇 code');
{ const u = RW.url(22.3193, 114.1694); ok(/latitude=22\.3&longitude=114\.2&/.test(u) && /^https:\/\/api\.open-meteo\.com\/v1\/forecast\?/.test(u) && !/apikey|key=/i.test(u), 'Open-Meteo URL（座標四捨五入 0.1°、冇 key）', u); }
{ const s = mk(), t = at(0, 14); RW.setOn(s, 'wx', true); const j = { latitude: 22.3, longitude: 114.2, current: { weather_code: 63 }, daily: { sunrise: ['2026-11-02T06:24'], sunset: ['2026-11-02T17:45'] } };
  const w = RW.applyWx(s, j, t); ok(w && w.kind === 'rain' && Math.abs(w.rise - 6.4) < 1e-9 && Math.abs(w.set - 17.75) < 1e-9, 'applyWx → 雨、日出 6:24、日落 17:45', w);
  ok(RW.visWeather(s, 'clear', t) === 'rain', '畫面天氣＝真天氣（雨）');
  const raw = JSON.stringify(s.rw6); ok(!/22\.3|114\.2|latitude|longitude|lat|lon/.test(raw), '存檔冇座標', raw);
  ok(Math.abs(RW.visHour(s, 6.4, t) - 6.5) < 1e-9 && Math.abs(RW.visHour(s, 17.75, t) - 18.5) < 1e-9, '日出 → 6.5、日落 → 18.5');
  const h12 = RW.visHour(s, 12, t); ok(h12 > 11 && h12 < 13, '中午大致唔變', h12);
  const hs = []; for (let h = 0; h < 24; h += 0.25) hs.push(RW.visHour(s, h, t)); let mono = true; for (let i = 1; i < hs.length; i++) { const d = ((hs[i] - hs[i - 1]) + 24) % 24; if (!(d > 0 && d < 1)) mono = false; }
  ok(mono, '24 小時 remap 連續、單向（冇跳）');
  ok(RW.visWeather(s, 'clear', t + 7 * 3600e3) === 'clear' && RW.visHour(s, 12, t + 7 * 3600e3) === 12, '真天氣過咗 6 粒鐘（冇網）→ 返遊戲每日擲');
  ok(RW.fresh(s, t + 10 * 60e3) && !RW.fresh(s, t + 31 * 60e3), '30 分鐘內唔使再攞');
  RW.setOn(s, 'wx', false); ok(RW.st(s).wx === null && RW.visWeather(s, 'clear', t) === 'clear', '熄天氣 → 清走真天氣');
  ok(RW.applyWx(s, j, t) === null, '熄咗唔收天氣'); }

console.log('⑥ 存檔');
{ const s = mk(); RW.setOn(s, 'steps', true); RW.ingest(s, 1000, 5, at(0, 9)); RW.ingest(s, 9000, 5, at(0, 10)); const j = JSON.parse(JSON.stringify(s));
  j.rw6.junk = 1; j.rw6.got.fake = 3; j.rw6.d['bad'] = 1; const o = RW.st(j); ok(!o.junk && !o.got.fake && !o.d.bad && o.total === 8000 && o.last.raw === 9000, 'sanitize：只留已知欄位', o);
  ok(JSON.stringify(s.rw6).length < 4096, '存檔細（<4KB）', JSON.stringify(s.rw6).length);
  RW.setOn(s, 'steps', false); ok(RW.st(s).last === null, '熄步數 → 清走最後讀數（下次再開重新做基準）'); }

console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
