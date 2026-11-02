/* long6c.test — 6c 夢境探險（遊策 breakthrough-6a6d-spec §6c）：入夢條件（瞓緊＋21:00–03:00＋每晚 1 次；蛋／細佬主養唔得）、
   3×5 地圖跟當日 6a 記錄（餵菇→蘑菇森林、淋水→水珠湖、玩得多→玩具房、夜晚→星空）、每晚 6 片碎片、5 片 1 張夢圖鑑（首批 20）、
   砌齊主題送 1 件家具（5a 擺設；全有就唔送）、唔郁錢包／需求／親密度／路線分、時長 ≤3 分鐘、存檔淨化。node tests/long6c.test.js */
const SIM = require('../src/sim.js'), X = require('../src/systems.js'), M6 = require('../src/long6a.js'), FAM = require('../src/long5a.js'), DR = require('../src/long6c.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const at = (d, h, m) => new Date(2026, 10, 2 + d, h, m || 0, 0).getTime();
const mk = () => { const s = SIM.newState(at(-10, 12), 9); s.stage = 'adult'; s.form = 'tide'; s.sleeping = true; return s; };
const H = (t) => DR.hourOf(t);
const rec = (s, t, meal, rinse, play, mg) => { for (let i = 0; i < meal; i++) M6.note(s, 'food', 'meal', 0, 0, 0, t); for (let i = 0; i < rinse; i++) M6.note(s, 'care', 'rinse', 0, 0, 0, t);
  for (let i = 0; i < play; i++) M6.note(s, 'care', 'play', 0, 0, 0, t); for (let i = 0; i < (mg || 0); i++) M6.note(s, 'care', 'mg', 0, 0, 0, t); };
const cnt = (g) => g.reduce((o, k) => (o[k] = (o[k] | 0) + 1, o), {});

console.log('① 入夢條件');
{ const s = mk(); let t = at(0, 22);
  ok(DR.canEnter(s, t, H(t)).ok, '22:00 瞓緊 → 入得');
  ok(DR.canEnter(s, at(0, 20, 59), 20.98).why === 'hours', '20:59 → 唔係夜晚');
  ok(DR.canEnter(s, at(1, 2, 59), 2.98).ok && DR.canEnter(s, at(1, 3), 3).why === 'hours', '02:59 得、03:00 唔得');
  ok(DR.canEnter(s, at(0, 21), 21).ok, '21:00 得');
  s.sleeping = false; ok(DR.canEnter(s, t, H(t)).why === 'awake', '醒咗 → 唔得'); s.sleeping = true;
  const e = mk(); e.stage = 'egg'; ok(DR.canEnter(e, t, H(t)).why === 'egg', '蛋 → 唔得');
  const k = mk(); k.fam = { km: true }; ok(DR.canEnter(k, t, H(t)).why === 'km', '細佬主養 → 唔得');
  const r = DR.enter(s, t, H(t)); ok(r.ok && r.night === '2026-11-02', '入夢 → 今晚＝11-02', r.night);
  ok(DR.enter(s, at(0, 23), 23).why === 'done' && DR.enter(s, at(1, 1), 1).why === 'done', '同一晚（23:00、翌日 01:00）再入 → done');
  ok(DR.canEnter(s, at(1, 21), 21).ok, '第二晚 21:00 → 又得');
  ok(DR.st(s).n.dreams === 1, '入夢次數 1'); }

console.log('② 地圖跟當日記錄');
{ const s = mk(), t = at(0, 22); rec(s, at(0, 9), 3, 1, 0); const p = DR.plan(s, t, 22), c = cnt(p.grid);
  ok(p.grid.length === 15 && p.grid.every(Boolean), '3×5＝15 格全部有主題');
  ok(c.forest === 7 && c.lake === 4 && c.star === 4 && !c.toy, '暖菇飯 3、淋水 1、冇玩 → 森林 7／湖 4／星 4／冇玩具房', c);
  ok(p.grid[p.start] === 'forest' && p.start === 13, '起點底中格＝最重主題');
  ok(p.grid.slice(0, 3).every(k => k === 'star'), '頂行＝星空');
  ok(p.frags.length === 6 && new Set(p.frags.map(f => f.tile)).size === 6 && p.frags.every(f => f.tile !== 13), '6 片碎片、唔同格、唔喺起點');
  ok(p.frags.every(f => p.grid[f.tile] === f.th), '碎片主題＝所在格主題');
  ok(['forest', 'lake', 'star'].every(k => p.frags.some(f => f.th === k)), '每個出現主題至少 1 片');
  ok(JSON.stringify(p.frags.map(f => f.at).sort((a, b) => a - b)) === JSON.stringify(DR.CFG.spawnAt), '出場時間 0/0/25/50/75/100', p.frags.map(f => f.at));
  ok(JSON.stringify(DR.plan(s, t, 22)) === JSON.stringify(p), '同晚同記錄 → 地圖一樣（seeded）');
  const s0 = mk(), p0 = DR.plan(s0, t, 22); ok(p0.grid.every(k => k === 'star'), '當日乜都冇做 → 全星空', cnt(p0.grid));
  const s1 = mk(); rec(s1, at(0, 9), 0, 0, 1, 0); ok(!cnt(DR.plan(s1, t, 22).grid).toy, '玩 1 次 → 未算玩得多');
  const s2 = mk(); rec(s2, at(0, 9), 0, 0, 1, 1); ok(cnt(DR.plan(s2, t, 22).grid).toy >= 2, '玩＋小遊戲 2 次 → 玩具房');
  const s3 = mk(); rec(s3, at(0, 9), 9, 9, 9, 9); const c3 = cnt(DR.plan(s3, t, 22).grid); ok(c3.forest === c3.lake && c3.lake === c3.toy && c3.star >= 2 && c3.forest + c3.lake + c3.toy + c3.star === 15, '樣樣做好多 → 封頂（4）平均分', c3);
  const s4 = mk(); rec(s4, at(0, 9), 1, 1, 1, 1); const c4 = cnt(DR.plan(s4, t, 22).grid); ok(['forest', 'lake', 'toy', 'star'].every(k => c4[k] >= DR.CFG.minTiles), '每個主題至少 ' + DR.CFG.minTiles + ' 格', c4);
  const s5 = mk(); rec(s5, at(0, 9), 2, 0, 0); rec(s5, at(1, 0, 30), 0, 3, 0); const c5 = cnt(DR.plan(s5, at(1, 1), 1).grid); ok(c5.forest >= 2 && c5.lake >= 2, '過咗 12 點：前一日＋今日凌晨記錄都計', c5);
  const s6 = mk(); rec(s6, at(-1, 9), 5, 5, 5); ok(cnt(DR.plan(s6, t, 22).grid).star === 15, '琴日記錄唔計入今晚'); }

console.log('③ 碎片 → 夢圖鑑（5 片 1 張，首批 20）');
{ const s = mk(); let r; for (let i = 0; i < 4; i++) r = DR.pick(s, 'lake', at(0, 22)); ok(!r.card && DR.toNext(s, 'lake') === 1, '4 片 → 未有卡、再 1 片');
  r = DR.pick(s, 'lake', at(0, 22)); ok(r.card === 'l1' && DR.st(s).cards.l1, '第 5 片 → 「' + DR.CK.l1.zh + '」');
  for (let i = 0; i < 5; i++) r = DR.pick(s, 'lake', at(0, 22)); ok(r.card === 'l2', '第 10 片 → 第 2 張（按次序）');
  ok(DR.st(s).frag.forest === 0, '主題分開計（湖嘅碎片唔幫森林）');
  ok(DR.CARDS.length === 20 && new Set(DR.CARDS.map(c => c.id)).size === 20 && DR.THEMES.every(k => DR.CARDS.filter(c => c.th === k).length === 5), '20 張、每主題 5 張');
  const a = mk(); for (const k of DR.THEMES) for (let i = 0; i < 40; i++) DR.pick(a, k, at(0, 22)); ok(Object.keys(DR.st(a).cards).length === 20 && DR.st(a).n.cards === 20, '碎片再多都係 20 張'); }

console.log('④ 砌齊主題送家具');
{ const s = mk(); let r, f = null; for (let i = 0; i < 25; i++) { r = DR.pick(s, 'forest', at(0, 22)); if (r.furn) f = r.furn; }
  ok(f === 'sv_mushroom' && FAM.st(s).sv.sv_mushroom, '蘑菇森林 5 張 → 送「細蘑菇」擺設', f);
  r = DR.pick(s, 'forest', at(0, 22)); ok(!r.furn && !r.card, '再拾唔會再送');
  const o = mk(); FAM.st(o).sv.sv_starstone = 1; for (let i = 0; i < 25; i++) { r = DR.pick(o, 'star', at(0, 22)); if (r.furn) f = r.furn; } ok(f && f !== 'sv_starstone' && FAM.SV[f], '已有首選 → 送另一件未有嘅', f);
  const n = mk(); for (const x of FAM.SOUV) FAM.st(n).sv[x.id] = 1; let got = null; for (let i = 0; i < 25; i++) { r = DR.pick(n, 'toy', at(0, 22)); if (r.furn) got = r.furn; } ok(!got && DR.st(n).furn.toy === 'none', '全部擺設都有 → 唔送（記 none）'); }

console.log('⑤ 唔加分、唔出碎、唔郁需求／親密度');
{ const s = mk(); rec(s, at(0, 9), 2, 2, 2); X.st(s); FAM.st(s);
  const strip = (x) => { const c = JSON.parse(JSON.stringify(x)); delete c.dream6; if (c.fam) c.fam.sv = {}; return JSON.stringify(c); };
  const b = strip(s), w0 = X.st(s).wallet.total; const p = DR.enter(s, at(0, 22), 22); for (const f of p.frags) DR.pick(s, f.th, at(0, 22)); for (let i = 0; i < 40; i++) DR.pick(s, 'forest', at(0, 22)); DR.endLog(s, p.night, 6, 140, ['forest']);
  ok(X.st(s).wallet.total === w0, '錢包（碎）唔變'); ok(strip(s) === b, '除 dream6／擺設外成個存檔一樣（需求、親密度、路線分、月眠）'); }

console.log('⑥ 時長 ≤3 分鐘');
{ const C = DR.CFG; ok(C.durSec + 2 * C.fadeSec <= 180 && C.maxSec <= 180, '夢 ' + C.durSec + ' 秒＋過場 ' + 2 * C.fadeSec + ' 秒 ≤ 180');
  ok(Math.max.apply(null, C.spawnAt) < C.durSec - 20, '最後一片 ' + Math.max.apply(null, C.spawnAt) + ' 秒出，仲有時間行過去');
  const s = mk(); DR.endLog(s, '2026-11-02', 99, 9999, ['x', 'star']); const e = DR.st(s).log[0]; ok(e.got === 6 && e.sec === 180 && e.th.join() === 'star', '記錄夾硬 ≤6 片、≤180 秒', e); }

console.log('⑦ 存檔淨化');
{ const s = mk(); s.dream6 = { night: 'evil<script>', frag: { forest: -5, lake: 'x', hack: 3 }, cards: { f1: 'a', zz: 1 }, furn: { star: 5, toy: 'sv_rainbow', bad: 'x' }, log: [{ d: 'x' }, { d: '2026-11-01', got: 50, sec: -1, th: ['lake', 'q'] }], n: { dreams: -1 }, junk: 1 };
  const o = DR.st(s); ok(o.night === null, '壞 night → null'); ok(o.frag.forest === 0 && o.frag.lake === 0 && !('hack' in o.frag), '壞碎片數 → 0、唔明主題刪');
  ok(o.cards.f1 === 1 && !o.cards.zz, '唔明卡刪'); ok(!('star' in o.furn) && o.furn.toy === 'sv_rainbow' && !o.furn.bad, '壞家具記錄刪');
  ok(o.log.length === 1 && o.log[0].got === 6 && o.log[0].sec === 0 && o.log[0].th.join() === 'lake', '壞 log 淨化', o.log); ok(o.n.dreams === 0 && !('junk' in o), '計數 ≥0、多餘 key 刪');
  DR.reset(s); ok(!s.dream6 || DR.st(s).n.frags === 0, 'reset 清晒'); }

console.log(`\n${pass} pass, ${fail} fail`); if (fail) process.exit(1);
