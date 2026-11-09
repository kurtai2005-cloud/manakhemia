/* long6c.test — 6c 夢境探險（遊策 breakthrough-6a6d-spec §6c＋6d 夢境平衡 A／B／C＋修1＋修2b）：入夢條件（瞓緊＋21:00–03:00、19:00 後上線都計＋每晚 1 次；錯過存 1 晚補做；蛋／細佬主養唔得）、
   3×5 地圖跟當日 6a 記錄（餵菇→蘑菇森林、餵食／淋水／執便便／小遊戲→水珠湖、玩→玩具房（最少 1）、夜晚→星空）、每晚 1 片（20% 2 片；齊咗嘅主題唔出）、模擬 84／151 日、5 片 1 張夢圖鑑（首批 20）、
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
  ok(DR.canEnter(s, at(0, 18, 59), 18.98).why === 'hours', '18:59 → 唔係夜晚');
  ok(DR.canEnter(s, at(0, 19), 19).ok && DR.canEnter(s, at(0, 20, 59), 20.98).ok, 'A：19:00 後上線都計（19:00、20:59 得）');
  ok(DR.canEnter(s, at(1, 2, 59), 2.98).ok, '02:59 得');
  ok(DR.canEnter(s, at(0, 21), 21).ok, '21:00 得');
  s.sleeping = false; ok(DR.canEnter(s, t, H(t)).why === 'awake', '醒咗 → 唔得'); s.sleeping = true;
  const e = mk(); e.stage = 'egg'; ok(DR.canEnter(e, t, H(t)).why === 'egg', '蛋 → 唔得');
  const k = mk(); k.fam = { km: true }; ok(DR.canEnter(k, t, H(t)).why === 'km', '細佬主養 → 唔得');
  const r = DR.enter(s, t, H(t)); ok(r.ok && r.night === '2026-11-02', '入夢 → 今晚＝11-02', r.night);
  ok(DR.enter(s, at(0, 23), 23).why === 'done' && DR.enter(s, at(1, 1), 1).why === 'done', '同一晚（23:00、翌日 01:00）再入 → done');
  ok(DR.canEnter(s, at(1, 21), 21).ok, '第二晚 21:00 → 又得');
  ok(DR.canEnter(s, at(1, 3), 3).why === 'hours' && DR.st(s).bank === 0, '03:00（今晚入咗）→ 唔得、冇補做');
  ok(DR.st(s).n.dreams === 1, '入夢次數 1'); }

console.log('①b 錯過嘅一晚存 1 個（B）');
{ const s = mk(); ok(DR.canEnter(s, at(0, 14), 14).why === 'hours' && DR.st(s).bank === 0, '新存檔第一次見 → 唔補舊數');
  ok(DR.canEnter(s, at(1, 14), 14).why === 'bank' && DR.st(s).bank === 1 && DR.st(s).bankNight === '2026-11-02', '11-02 晚冇入 → 第二日下晝補做得', DR.st(s));
  ok(DR.canEnter(s, at(3, 14), 14).why === 'bank' && DR.st(s).bank === 1 && DR.st(s).bankNight === '2026-11-02', '錯過幾晚都係最多存 1 個');
  const r = DR.enter(s, at(3, 14), 14); ok(r.ok && r.bank === '2026-11-02' && r.frags.length >= 1 && DR.st(s).bank === 0 && DR.st(s).night === null, '補做 → 用咗銀行、唔佔當晚');
  ok(DR.canEnter(s, at(3, 15), 15).why === 'hours', '補完 → 下晝冇得再入');
  ok(DR.canEnter(s, at(3, 22), 22).ok, '補完當晚照入得'); DR.enter(s, at(3, 22), 22);
  ok(DR.canEnter(s, at(4, 14), 14).why === 'hours' && DR.st(s).bank === 0, '琴晚入咗 → 冇補做');
  ok(DR.canEnter(s, at(5, 14), 14).why === 'bank', '再錯過一晚 → 又有');
  const e = mk(); e.stage = 'egg'; DR.canEnter(e, at(0, 14), 14); ok(DR.canEnter(e, at(2, 14), 14).why === 'egg' && DR.st(e).bank === 0, '蛋期唔存');
  const n = mk(); DR.canEnter(n, at(0, 14), 14); n.sleeping = false; ok(DR.canEnter(n, at(2, 14), 14).why === 'awake', '醒咗 → 唔入得（補做都要瞓緊）'); }

console.log('② 地圖跟當日記錄');
{ const s = mk(), t = at(0, 22); rec(s, at(0, 9), 3, 1, 0); const p = DR.plan(s, t, 22), c = cnt(p.grid);
  ok(p.grid.length === 15 && p.grid.every(Boolean), '3×5＝15 格全部有主題');
  ok(p.w.forest === 3 && p.w.lake === 2 && p.w.toy === 1 && p.w.star === 1, '權重：森林＝暖菇飯 3、湖＝餵食＋淋水 2（C）、玩具房冇玩都最少 1（修2b）、星 1', p.w);
  ok(c.forest >= 2 && c.lake >= 2 && c.toy >= 2 && c.star >= 2 && c.forest > c.lake, '每個主題 ≥2 格、森林最多', c);
  ok(p.grid[p.start] === 'forest' && p.start === 13, '起點底中格＝最重主題');
  ok(p.grid.slice(0, 3).every(k => k === 'star'), '頂行＝星空');
  ok(p.frags.length >= 1 && p.frags.length <= 2 && new Set(p.frags.map(f => f.tile)).size === p.frags.length && p.frags.every(f => f.tile !== 13), '每晚 1–2 片、唔同格、唔喺起點', p.frags);
  ok(p.frags.every(f => p.grid[f.tile] === f.th), '碎片主題＝所在格主題');
  ok(p.frags.every((f, i) => f.at === DR.CFG.spawnAt[i]), '出場時間 0／40 秒', p.frags.map(f => f.at));
  { let two = 0, N = 4000; for (let i = 0; i < N; i++) { const x = mk(); x.seed = 1000 + i; if (DR.plan(x, t, 22).frags.length === 2) two++; } ok(Math.abs(two / N - 0.2) < 0.025, '再多 1 片嘅機會 ≈20%（' + (two / N * 100).toFixed(1) + '%）'); }
  { const x = mk(); for (const k of ['forest', 'lake', 'toy']) for (let i = 0; i < 25; i++) DR.pick(x, k, t); let bad = 0; for (let i = 0; i < 300; i++) { x.seed = 50 + i; for (const f of DR.plan(x, t, 22).frags) if (f.th !== 'star') bad++; } ok(bad === 0, '修1：齊 5 張嘅主題唔再出片（淨係星空）'); }
  { const x = mk(); for (const k of DR.THEMES) for (let i = 0; i < 25; i++) DR.pick(x, k, t); ok(DR.plan(x, t, 22).frags.length === 0, '四主題都齊 → 0 片'); }
  { const x = mk(); for (let i = 0; i < 24; i++) DR.pick(x, 'star', t); let ok2 = true; for (let i = 0; i < 300; i++) { x.seed = 900 + i; const fr = DR.plan(x, t, 22).frags; if (fr.length === 2 && fr[0].th === 'star' && fr[1].th === 'star') ok2 = false; } ok(ok2, '修1：同一晚第 1 片砌齊咗個主題 → 第 2 片唔會再係佢'); }
  ok(JSON.stringify(DR.plan(s, t, 22)) === JSON.stringify(p), '同晚同記錄 → 地圖一樣（seeded）');
  const s0 = mk(), p0 = DR.plan(s0, t, 22); ok(!cnt(p0.grid).forest && !cnt(p0.grid).lake && cnt(p0.grid).toy && cnt(p0.grid).star, '當日乜都冇做 → 淨係星空＋玩具房', cnt(p0.grid));
  const s1 = mk(); rec(s1, at(0, 9), 0, 0, 1, 0); ok(DR.plan(s1, t, 22).w.toy === 1 && cnt(DR.plan(s1, t, 22).grid).toy >= 2, '修2b：玩 1 次都有玩具房（冇門檻）');
  const s2 = mk(); rec(s2, at(0, 9), 0, 0, 1, 1); ok(DR.plan(s2, t, 22).w.toy === 2 && DR.plan(s2, t, 22).w.lake === 1, '玩＋小遊戲 → 玩具房 2；小遊戲都幫湖 +1（C）');
  const s7 = mk(); rec(s7, at(0, 9), 1, 1, 0, 1); M6.note(s7, 'care', 'poop', 0, 0, 0, at(0, 9)); ok(DR.plan(s7, t, 22).w.lake === 4, 'C：餵食＋淋水＋執便便＋小遊戲 → 湖 4（每樣 +1，唔疊次數）', DR.plan(s7, t, 22).w);
  const s8 = mk(); rec(s8, at(0, 9), 0, 5, 0, 0); ok(DR.plan(s8, t, 22).w.lake === 1, 'C：淋水 5 次都係 +1');
  const s3 = mk(); rec(s3, at(0, 9), 9, 9, 9, 9); const c3 = cnt(DR.plan(s3, t, 22).grid); ok(c3.forest === c3.lake && c3.lake === c3.toy && c3.star >= 2 && c3.forest + c3.lake + c3.toy + c3.star === 15, '樣樣做好多 → 封頂（4）平均分', c3);
  const s4 = mk(); rec(s4, at(0, 9), 1, 1, 1, 1); const c4 = cnt(DR.plan(s4, t, 22).grid); ok(['forest', 'lake', 'toy', 'star'].every(k => c4[k] >= DR.CFG.minTiles), '每個主題至少 ' + DR.CFG.minTiles + ' 格', c4);
  const s5 = mk(); rec(s5, at(0, 9), 2, 0, 0); rec(s5, at(1, 0, 30), 0, 3, 0); const c5 = cnt(DR.plan(s5, at(1, 1), 1).grid); ok(c5.forest >= 2 && c5.lake >= 2, '過咗 12 點：前一日＋今日凌晨記錄都計', c5);
  const s6 = mk(); rec(s6, at(-1, 9), 5, 5, 5); ok(!cnt(DR.plan(s6, t, 22).grid).forest && !cnt(DR.plan(s6, t, 22).grid).lake, '琴日記錄唔計入今晚'); }

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
  const b = strip(s), w0 = X.st(s).wallet.total; const p = DR.enter(s, at(0, 22), 22); for (const f of p.frags) DR.pick(s, f.th, at(0, 22)); for (let i = 0; i < 40; i++) DR.pick(s, 'forest', at(0, 22)); DR.endLog(s, p.night, 2, 140, ['forest']);
  ok(X.st(s).wallet.total === w0 && !(X.st(s).day && X.st(s).day.shards), '錢包（碎）唔變、唔計 47 碎上限'); ok(strip(s) === b, '除 dream6／擺設外成個存檔一樣（需求、親密度、路線分、月眠）'); }

console.log('⑥ 時長 ≤3 分鐘');
{ const C = DR.CFG; ok(C.durSec + 2 * C.fadeSec <= 180 && C.maxSec <= 180, '夢 ' + C.durSec + ' 秒＋過場 ' + 2 * C.fadeSec + ' 秒 ≤ 180');
  ok(Math.max.apply(null, C.spawnAt) < C.durSec - 20, '最後一片 ' + Math.max.apply(null, C.spawnAt) + ' 秒出，仲有時間行過去');
  const s = mk(); DR.endLog(s, '2026-11-02', 99, 9999, ['x', 'star']); const e = DR.st(s).log[0]; ok(e.got === 2 && e.sec === 180 && e.th.join() === 'star', '記錄夾硬 ≤2 片、≤180 秒', e); }

console.log('⑦ 存檔淨化');
{ const s = mk(); s.dream6 = { night: 'evil<script>', frag: { forest: -5, lake: 'x', hack: 3 }, cards: { f1: 'a', zz: 1 }, furn: { star: 5, toy: 'sv_rainbow', bad: 'x' }, log: [{ d: 'x' }, { d: '2026-11-01', got: 50, sec: -1, th: ['lake', 'q'] }], n: { dreams: -1 }, junk: 1 };
  const o = DR.st(s); ok(o.night === null, '壞 night → null'); ok(o.frag.forest === 0 && o.frag.lake === 0 && !('hack' in o.frag), '壞碎片數 → 0、唔明主題刪');
  ok(o.cards.f1 === 1 && !o.cards.zz, '唔明卡刪'); ok(!('star' in o.furn) && o.furn.toy === 'sv_rainbow' && !o.furn.bad, '壞家具記錄刪');
  ok(o.log.length === 1 && o.log[0].got === 2 && o.log[0].sec === 0 && o.log[0].th.join() === 'lake', '壞 log 淨化', o.log); ok(o.n.dreams === 0 && !('junk' in o), '計數 ≥0、多餘 key 刪');
  DR.reset(s); ok(!s.dream6 || DR.st(s).n.frags === 0, 'reset 清晒'); }

console.log('⑧ 模擬（seeded）：天天玩／疏玩 → 集齊 4 主題 20 張要幾多日');
{ /* 玩家模型（遊策 6c 夢境平衡目標）：
     天天玩：每日夜晚 20–22 點上線 1 次（入夢）；疏玩：每日 55% 機會上線，一半 19–22 點（當晚入夢）、一半 9–17 點（有錯過嘅一晚就補做）。
     每次上線：暖菇飯 1–3、淋水 70%、執便便 60%、玩耍 60%、小遊戲 40%；入夢就拾晒當晚嘅片。上限 180 日。 */
  const at0 = (d, h, m) => new Date(2026, 0, 1 + d, h, m || 0, 0).getTime();
  const R0 = (seed) => { let x = seed >>> 0 || 1; return () => { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; return x / 4294967296; }; };
  const run = (kind, seed, p, Hz) => { const r = R0(seed * 7919 + 13), s = SIM.newState(at0(0, 9), seed); s.stage = 'adult'; s.form = 'tide'; const w0 = X.st(s).wallet.total; let fr = 0;
    for (let d = 0; d < Hz; d++) { if (kind !== 'daily' && !(r() < p)) continue;
      const hr = kind === 'daily' ? 20 + Math.floor(r() * 3) : (r() < 0.5 ? 19 + Math.floor(r() * 4) : 9 + Math.floor(r() * 9)), t = at0(d, hr, 10);
      const n = 1 + Math.floor(r() * 3); for (let i = 0; i < n; i++) M6.note(s, 'food', 'meal', 0, 0, 0, t);
      if (r() < .7) M6.note(s, 'care', 'rinse', 0, 0, 0, t); if (r() < .6) M6.note(s, 'care', 'poop', 0, 0, 0, t); if (r() < .6) M6.note(s, 'care', 'play', 0, 0, 0, t); if (r() < .4) M6.note(s, 'care', 'mg', 0, 0, 0, t);
      s.sleeping = true; const e = DR.enter(s, t + 60e3, hr + 0.2); s.sleeping = false; if (e.ok) for (const f of e.frags) { DR.pick(s, f.th, t); fr++; }
      if (Object.keys(DR.st(s).cards).length >= 20) return { d: d + 1, fr, w: X.st(s).wallet.total - w0 }; }
    return { d: null, fr, w: X.st(s).wallet.total - w0 }; };
  const stat = (kind, p) => { const all = []; for (let i = 1; i <= 400; i++) all.push(run(kind, i, p, 180)); const ds = all.filter(x => x.d != null).map(x => x.d).sort((a, b) => a - b), q = (f) => ds[Math.floor(f * (ds.length - 1))];
    return { done: ds.length / all.length * 100, med: q(0.5), p10: q(0.1), waste: all.filter(x => x.d != null && x.fr !== 100).length, wallet: all.some(x => x.w !== 0) }; };
  const D = stat('daily', 1), L = stat('light', 0.55);
  ok(D.done === 100 && Math.abs(D.med - 84) <= 3 && Math.abs(D.p10 - 80) <= 3, '天天玩：100% 集齊、中位 ' + D.med + ' 日（目標 84）、P10 ' + D.p10 + '（目標 80）', D);
  ok(Math.abs(L.done - 98.5) <= 2 && Math.abs(L.med - 151) <= 6, '疏玩：' + L.done.toFixed(1) + '% 集齊（目標 98.5）、中位 ' + L.med + ' 日（目標 151）', L);
  ok(D.waste === 0 && L.waste === 0, '修1：集齊嘅人啱啱好用 100 片（冇嘥片）');
  ok(!D.wallet && !L.wallet, '夢碎片冇入錢包'); }

console.log(`\n${pass} pass, ${fail} fail`); if (fail) process.exit(1);
