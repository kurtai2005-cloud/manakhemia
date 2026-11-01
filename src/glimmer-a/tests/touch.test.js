/* 第 3 批 3a（docs-gdd/batch3-fun-spec.md §①②）：提示排隊、手勢辨識、心情每日上限（同浮動共用 ≤5）、搖機、扮醒呆排程、呆呆時刻徽章。node tests/touch.test.js */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), T = require('../src/touch.js'), X = require('../src/systems.js'), B = require('../src/systems2.js');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const P = D.PARAMS.touch, T0 = new Date(2026, 10, 1, 15, 0, 0).getTime(), H = 3600e3;
const fresh = () => { const s = SIM.newState(T0, 7); s.stage = 'sprout'; s.needs.mood = 50; return s; };

console.log('⓪ 提示排隊（同一時間一個）');
{ const Q = T.createQueue(); let t = 0;
  Q.push({ line: 'A', sec: 4 }, t); let r = Q.tick(t); ok(r.show && r.show.line === 'A' && Q.busy(t), '第一句即刻出');
  ok(Q.push({ line: 'B', sec: 4 }, t + 100).queued === true, '第二句排隊（唔頂走）'); r = Q.tick(t + 200); ok(!r.show && Q.cur.line === 'A', '出緊 A 嗰陣 B 唔出');
  ok(Q.push({ line: 'B', sec: 4 }, t + 300).ok === false, '同一句唔重覆排');
  r = Q.tick(4000); ok(r.hide && r.hide.line === 'A' && !r.show && !Q.busy(4000), 'A 完 → 隔 0.25s 先出下一句');
  r = Q.tick(4300); ok(r.show && r.show.line === 'B', '之後輪到 B');
  Q.push({ line: 'C', sec: 4 }, 4400); Q.push({ line: 'U', sec: 2, urgent: true }, 4500); r = Q.tick(4500); ok(r.hide && r.hide.line === 'B' && r.show && r.show.line === 'U', 'urgent（尷尬句）頂走現時');
  r = Q.tick(6500); r = Q.tick(6800); ok(r.show && r.show.line === 'C', 'urgent 完 → 返去排緊嗰句');
  const Q2 = T.createQueue(); Q2.push({ line: 'x0', sec: 30 }, 0); Q2.tick(0); for (let i = 1; i <= 5; i++) Q2.push({ line: 'x' + i }, 10); ok(Q2.list.length === P.queue.max && Q2.dropped === 2, '排隊最多 3 個（舊嘅掉）', Q2.list.length);
  Q2.cur.until = 25000; Q2.tick(25000); const r2 = Q2.tick(25300); ok(!r2.show && Q2.list.length === 0, '等 >20s 作廢（唔出過時嘅句）'); }

console.log('① 心情：每種手勢每日第一次 +1，同浮動團絨共用每日 ≤5');
{ const s = fresh(), st = T.memStore();
  let r = T.moodGrant(s, 'poke', T0, st); ok(r.ok && s.needs.mood === 51, '戳 第一次 +1');
  r = T.moodGrant(s, 'poke', T0 + 60e3, st); ok(!r.ok && r.reason === 'repeat' && s.needs.mood === 51, '同日再戳唔加');
  ['hold', 'tickle', 'pull', 'shake'].forEach((k, i) => T.moodGrant(s, k, T0 + i * 1000, st)); ok(s.needs.mood === 55, '5 種手勢各 +1 ＝ +5', s.needs.mood);
  ok(JSON.parse(st.get('fpet_daily_v1'))[T.bridgeDay(T0)] === 5, '寫入 fpet-bridge 共用 key（冇補 0 嘅 dayKey）', st.m);
  r = T.moodGrant(s, 'poke', T0 + 24 * H, st); ok(r.ok && s.needs.mood === 56, '第二日重新計');
  const s2 = fresh(), st2 = T.memStore(); st2.set('fpet_daily_v1', JSON.stringify({ [T.bridgeDay(T0)]: 4 }));
  ok(T.moodGrant(s2, 'poke', T0, st2).ok && s2.needs.mood === 51, '浮動已 +4 → 手勢仲有 1');
  r = T.moodGrant(s2, 'hold', T0, st2); ok(!r.ok && r.reason === 'cap' && s2.needs.mood === 51, '共用 5 滿咗 → 唔加', r);
  ok(T.moodGrant(s2, 'hold', T0, st2).reason === 'repeat', '滿額時嘅第一次都算用咗');
  const s3 = fresh(), st3 = T.memStore(); s3.sleeping = true; ok(T.moodGrant(s3, 'shake', T0, st3).reason === 'sleep' && s3.needs.mood === 50 && !st3.get('fpet_daily_v1'), '瞓覺中唔加心情、唔食共用額');
  const s4 = fresh(); s4.stage = 'egg'; ok(T.moodGrant(s4, 'poke', T0, T.memStore()).reason === 'egg', '光卵唔加');
  const s5 = fresh(), rp0 = JSON.stringify(s5.evo), cq0 = JSON.stringify(s5.evs); T.moodGrant(s5, 'poke', T0, T.memStore()); ok(JSON.stringify(s5.evo) === rp0 && JSON.stringify(s5.evs) === cq0, '唔加路線分／唔郁照顧品質（冇經 noteCare）');
  ok(T.moodGrant(fresh(), 'xx', T0, T.memStore()).reason === 'kind', '未知手勢唔計'); }

console.log('① 手勢辨識');
{ const R = T.createRecognizer(); let o;
  R.down(0, 100, 100); R.up(0.12, 100, 100); o = R.drain(); ok(o.length === 1 && o[0].k === 'poke', '短 tap ＝ 戳');
  R.down(0, 100, 100); R.tick(0.5); ok(!R.drain().length, '0.5s 未算長按'); R.tick(0.61); o = R.drain(); ok(o.length === 1 && o[0].k === 'hold', '≥0.6s ＝ 長按瞇眼');
  R.tick(2.9); ok(!R.drain().length, '未夠 3s 唔算摸頭'); R.tick(3.01); o = R.drain(); ok(o[0] && o[0].k === 'pat', '持續 3s ＝ 一次摸頭'); R.tick(6.5); ok(!R.drain().length, '同一下長按只計一次');
  R.up(7, 100, 100); o = R.drain(); ok(o[0].k === 'release' && o[0].pat, '鬆手（已計摸頭）');
  R.down(0, 100, 100); let x = 100, t = 0; for (let i = 0; i < 6; i++) { t += 0.15; x = i % 2 ? 100 : 112; R.move(t, x, 100); } o = R.drain(); ok(o.some(e => e.k === 'tickle'), '1s 內 ≥4 次來回擦 ＝ 搔癢', o);
  for (let i = 0; i < 24; i++) { t += 0.15; x = i % 2 ? 100 : 112; R.move(t, x, 100); R.tick(t); } o = R.drain(); ok(o.some(e => e.k === 'roll') && !o.some(e => e.k === 'hold'), '再擦 3s ＝ 碌地笑（唔當長按）', o.map(e => e.k));
  R.up(t, 100, 100); R.drain();
  R.down(0, 100, 100); R.move(0.1, 125, 100); R.move(0.2, 150, 100); R.up(0.3, 150, 100); o = R.drain(); ok(o.length === 1 && o[0].k === 'pull' && o[0].dx === 50, '拖離 >40px 放手 ＝ 拉開彈返');
  R.down(0, 100, 100); R.move(0.1, 130, 100); R.up(0.2, 130, 100); o = R.drain(); ok(o[0].k === 'release', '拖 30px 唔算拉開');
  R.down(0, 100, 100); R.move(0.1, 160, 100); R.up(0.2, 160, 100, true); ok(!R.drain().length, 'pointercancel 唔出手勢'); }

console.log('① 搖機');
{ const S = T.createShake(); let r;
  ok(!S.sample(0, 2.4) && !S.sample(0.2, 2.4), '≤2.5g 唔算'); ok(!S.sample(1, 2.8), '一個峰唔算'); r = S.sample(1.5, 3); ok(r && r.dizzy, '1s 內兩個 >2.5g ＝ 暈 2s');
  S.sample(3, 3); r = S.sample(3.4, 3); ok(r && !r.dizzy && !r.brag, '冷卻 30s 內再搖：唔再暈');
  S.sample(10, 3); r = S.sample(10.4, 3); ok(r && r.brag, '1 分鐘內搖 3 次 → 扮冇事心聲'); S.sample(12, 3); r = S.sample(12.4, 3); ok(r && !r.brag, '同一分鐘唔再講');
  S.sample(40, 3); r = S.sample(40.5, 3); ok(r && r.dizzy, '30s 後可以再暈'); }

console.log('② 扮醒呆排程＋呆呆時刻');
{ const s = fresh(); let rnd = () => 0.1;
  ok(T.dumbRoll(s, T0, rnd), '25% 抽中（rnd 0.1）'); ok(!T.dumbRoll(s, T0, () => 0.3), '抽唔中（rnd 0.3）');
  const r = T.dumbStart(s, 'glasses', T0, () => 0); ok(r.first && T.LINES.dumb.glasses.includes(r.line), '開始：第一次＋句子嚟自規格 6×3 表');
  ok(!T.dumbCan(s, T0 + 170e3).ok && T.dumbCan(s, T0 + 180e3).ok, '最少隔 3 分鐘');
  for (let i = 1; i < 8; i++) T.dumbStart(s, T.DUMB[i % 6], T0 + i * 200e3, () => 0); ok(T.dumbCan(s, T0 + 9 * 200e3).reason === 'day', '每日最多 8 次');
  ok(T.dumbCan(s, T0 + 24 * H).ok, '第二日重設'); const sl = fresh(); sl.sleeping = true; ok(!T.dumbRoll(sl, T0, rnd), '瞓覺唔扮醒');
  ok(Object.keys(T.LINES.dumb).length === 6 && T.DUMB.every(k => T.LINES.dumb[k].length === 3), '文案表 6×3');
  const s2 = fresh(); X.st(s2); B.st(s2); ['glasses', 'book', 'wall', 'mirror', 'finger'].forEach((k, i) => T.dumbStart(s2, k, T0 + i * 200e3, () => 0));
  let g = B.badgeCheck(s2, T0); ok(!g.some(b => b.k === 'dumb_all') && T.dumbDex(s2).filter(d => d.got).length === 5, '5 格未發徽章');
  const w0 = X.wallet(s2, T0).total; T.dumbStart(s2, 'prof', T0 + 2e6, () => 0); g = B.badgeCheck(s2, T0 + 2e6);
  ok(g.some(b => b.k === 'dumb_all' && b.shards === 5) && X.wallet(s2, T0 + 2e6).total === w0 + 5 && X.wallet(s2, T0 + 2e6).today === X.wallet(s2, T0).today, '收齊 6 格 → 普通徽章 5 碎（唔食日上限）'); }

console.log('① 動作表（程序化，key 預留 art）');
{ const keys = Object.keys(T.MOTIONS); ok(['g_poke', 'g_hold', 'g_tickle', 'g_roll', 'g_pull', 'g_spring', 'g_dizzy', 'g_rub'].every(k => keys.includes(k)) && T.DUMB.every(k => keys.includes('d_' + k)) && keys.includes('d_caught'), '手勢 8＋呆 6＋尷尬 1');
  ok(keys.every(k => typeof T.MOTIONS[k].art === 'string' && T.MOTIONS[k].art), '每個都有 art 疊層名（遊美換圖用）');
  const m = T.motionAt('g_poke', 0, 0.075); ok(m.sy < 0.9 && m.sx > 1.1 && m.face.eyes === 'sleepy', '戳：squash＋眨眼'); ok(T.motionAt('g_poke', 0, 0.2) === null, '0.15s 完');
  ok(T.motionAt('g_dizzy', 0, 1).fx.includes('stars') && T.motionAt('g_dizzy', 0, 2.1) === null, '暈 2s＋轉星');
  const sp = T.motionAt('g_spring', 0, 0.85, { d: 1 }); ok(sp.sy < 1, '彈返落地 squash');
  const EY = D.PARAMS.face.eyes, MO = D.PARAMS.face.mouths; let bad = [];
  for (const k of keys) for (let u = 0; u <= 1; u += 0.1) { const r = T.motionAt(k, 0, (T.MOTIONS[k].sec || 1) * u, { d: 0.5 }); if (r && r.face && ((r.face.eyes && !EY.includes(r.face.eyes)) || (r.face.mouth && !MO.includes(r.face.mouth)))) bad.push(k); }
  ok(!bad.length, '表情全部喺現有五官 kit 入面', bad); }

console.log('摸頭委託（長按 3s → notePat；懸浮 12 上限唔郁）');
{ ok(D.PARAMS.systems12.quests.overlayPatPerDay === 12, '懸浮每日 12 上限照舊'); }
console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
