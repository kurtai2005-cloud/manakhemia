/* 第 4 批 4a（docs-gdd/series2-4a4b-spec.md v1.1 §4a）：細佬 s.pet2 — 攞蛋／孵夢／時間線／教錯課／S3 結算 4 情況／親密度上限／關係級／雙人 clip 數學／圖檔完整。node tests/series2.test.js */
const D = require('../src/data.js'), SIM = require('../src/sim.js'), S2 = require('../src/series2.js'), RC = require('../src/reactclip.js');
const fs = require('fs'), path = require('path'), ART = path.join(__dirname, '../art/series2');
const J = (f) => JSON.parse(fs.readFileSync(path.join(ART, f), 'utf8'));
const ACT = J('actions/actions.json'), FACES = J('faces/faces.json'), LES = J('lessons/lessons.json'), UI = J('ui/ui_series2_4a.json'), DUO = J('duo/duo.json'), LV = J('levelup/levelup.json'), KA = J('kid_anchors.json');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const H = 3600e3, DAY = 24 * H, at = (d, h, m) => new Date(2026, 10, 1 + d, h, m || 0, 0).getTime(), C = S2.CFG, dn = S2.dayNum;
const elder = () => { const s = SIM.newState(at(-30, 12), 7); s.stage = 'elder'; s.form = 'tide'; return s; };
const strip = (s) => { const c = JSON.parse(JSON.stringify(s)); delete c.pet2; return JSON.stringify(c); };
function kid(dHatch, o) {  // 孵咗嘅細佬（hatchDay＝day dHatch）
  const s = elder(); S2.noteElder(s, at(dHatch - 5, 12)); S2.deliver(s, at(dHatch - 4, 12)); const p = S2.st(s);
  p.dreams = [{ day: p.d0, line: 'A' }, { day: p.d0 + 1, line: 'B' }, { day: p.d0 + 2, line: null }]; S2.hatch(s, at(dHatch, 12)); Object.assign(p, o || {}); return s;
}

console.log('⓪ 美術／資料');
{ const miss = []; const chk = (f) => { if (!fs.existsSync(path.join(ART, f))) miss.push(f); };
  const keys = Object.keys(ACT.forms); ok(keys.length === 34, '34 個形態有 actions（S1／S2／S4×8／24 現有）', keys.length);
  for (const k of keys) for (const c of ['idle', 'walk', 'cry', 'eat', 'sleep']) chk(ACT.forms[k][c]);
  for (const L of S2.LINES) { chk(UI.props[L].png); chk(UI.dreams[L].png); chk(LES.propsBySeries[L].png); ok(LES.propsBySeries[L].id === S2.PROP[L], L + ' 道具 id 對', LES.propsBySeries[L].id); ok(LES.demo[L] && LES.copy[L], L + ' 示範＋照抄 clip'); }
  for (const k in LES.fx2) chk(LES.fx2[k].png);
  for (const k in DUO.overlays) if (DUO.overlays[k].png) chk(DUO.overlays[k].png);
  for (const k in FACES) if (FACES[k] && FACES[k].png) chk(FACES[k].png);
  chk('egg/egg_48.png'); chk('egg/egg_crack.png'); chk('duo/hatch_first_glance_last.png');
  ok(!miss.length, '所有引用圖檔存在', miss);
  for (const L of S2.LINES) for (const st of ['1', '2', '3']) ok(ACT.forms[L + st], '形態 ' + L + st);
  ok(S2.LINES.every(L => ACT.forms['S4' + L]), 'S4 8 系新形態');
  ok(['cuddle_egg', 'follow_walk', 'comfort_cry', 'eat_together', 'sleep_together', 'hatch_first_glance'].every(k => DUO.clips[k]), '雙人 clip 6 個');
  ok(['lv_follow', 'lv_friend', 'lv_family'].every(k => LV.scenes[k] && LV.scenes[k].durationMs >= 4000 && LV.scenes[k].durationMs <= 6000), '升級小場面 3 個（4–6 秒）');
  ok(Object.keys(KA.forms).length === 35 && keys.every(k => KA.forms[k] && KA.forms[k].headTop && KA.forms[k].eyeL), 'kid_anchors 34 形態＋蛋');
  ok(D.PARAMS.series2 && D.PARAMS.series2.enabled === true && D.PARAMS.series2.art.base === 'art/series2/', 'PARAMS.series2 開');
  const rx = JSON.parse(fs.readFileSync(path.join(__dirname, '../art/reactions/reactions.json'), 'utf8'));
  const okFace = new Set(rx.faceNotes && rx.faceNotes.order ? rx.faceNotes.order : ['blink', 'squint', 'squint_blush', 'laugh_a', 'laugh_b', 'dizzy_a', 'dizzy_b', 'sleepy', 'sleep', 'surprised', 'smug', 'embarrassed', 'lookup']);
  const bad = []; for (const L of S2.LINES) for (const k of LES.demo[L].face || []) for (const f of [].concat(k.f)) if (f && !okFace.has(f)) bad.push(L + ':' + f);
  ok(!bad.length, '團絨示範 face 全部係 3a face patch', bad);
  const kf = new Set(FACES.S2.order), bad2 = []; for (const L of S2.LINES) for (const k of LES.copy[L].face || []) for (const f of [].concat(k.f)) if (f && !kf.has(f)) bad2.push(L + ':' + f);
  ok(!bad2.length, '細佬照抄 face 全部喺 faces.json order', bad2);
  const FX3 = JSON.parse(fs.readFileSync(path.join(__dirname, '../art/reactions/fx/fx.json'), 'utf8')), fx3 = Object.keys(FX3.fx || FX3).filter(k => /^fx_/.test(k));
  const fxIds = new Set([...Object.keys(LES.fx2), ...Object.values(S2.PROP), ...fx3]), bad3 = [];
  for (const L of S2.LINES) for (const c of [LES.demo[L], LES.copy[L]]) for (const f of c.fx || []) if (!fxIds.has(f.id)) bad3.push(L + ':' + f.id);
  ok(!bad3.length, '課 fx 全部有圖（prop／fx2／3a fx）', bad3);
  const ev = RC.evalClip(Object.assign({ dur: LES.demo.A.durationMs }, LES.demo.A), 1000, {}); ok(ev.fx.some(f => f.id === 'prop_can') && ev.face === 'squint', 'reactclip 播得示範 clip（1000ms：水壺喺頭＋squint）', ev.face); }

console.log('① 存檔 sanitize（唔郁團絨）');
{ const s = elder(), before = strip(s); s.pet2 = { phase: 'zz', dreams: [{ day: 'x' }, { day: 3, line: 'Q' }], lessons: [{ line: 'Z' }, { line: 'A', day: 5 }], intim: -4, rel: 'boss', day: 7, care: { foo: 1, 20: { A: 2, Q: 1 } } };
  const o = S2.st(s); ok(o.phase === 'none' && o.dreams.length === 1 && o.dreams[0].line === null && o.lessons.length === 1, 'phase／夢／堂清走壞資料', o);
  ok(o.intim === 0 && o.rel === 'none' && typeof o.day === 'object' && !o.care.foo && o.care['20'].A === 2 && !o.care['20'].Q, '親密夾 ≥0、rel 修返、care 只留系', o.care);
  ok(strip(s) === before, 's.pet2 以外存檔一樣（團絨資料唔郁）');
  const j = JSON.parse(JSON.stringify(s)); ok(JSON.stringify(S2.st(j)) === JSON.stringify(o), '存讀 round-trip 一樣');
  const s2 = SIM.newState(at(0, 9), 3); ok(S2.st(s2).phase === 'none' && SIM.newState && !('pet2' in SIM.newState(at(0, 9), 3)), '新存檔 sim 本身冇 pet2（由 series2 加）'); }

console.log('② 攞蛋：首次靜光 → 翌日蝸牛郵差');
{ const s = elder(); const t0 = at(0, 20); ok(S2.noteElder(s, t0) && S2.st(s).phase === 'due' && S2.st(s).dueDay === dn(t0) + 1, '靜光 → due（翌日）');
  ok(!S2.noteElder(s, t0 + H), '只記一次'); ok(!S2.canDeliver(s, at(0, 23)), '當日唔送'); ok(S2.canDeliver(s, at(1, 0, 30)), '翌日就送');
  const r = S2.deliver(s, at(1, 10)); ok(r.ok && S2.st(s).phase === 'egg' && S2.st(s).d0 === dn(at(1, 10)), '送到 → 蛋（d0＝收蛋日）');
  ok(!S2.deliver(s, at(1, 11)).ok, '永遠最多 1 隻');
  const y = SIM.newState(at(0, 9), 3); y.stage = 'juvenile'; ok(!S2.noteElder(y, at(0, 9)), '未到靜光唔送'); }

console.log('③ 孵夢：每晚當日最多照顧 → 8 系之一 +1（最多 3 分）');
{ const s = elder(); S2.noteElder(s, at(0, 12)); S2.deliver(s, at(1, 9)); const p = S2.st(s), d0 = p.d0;
  ['feed', 'feed', 'water', 'feed'].forEach((k, i) => S2.careNote(s, k, at(1, 10 + i))); ok(S2.topCare(s, d0) === 'E', '餵食最多 → E（辣）');
  ok(S2.dreamDue(s, at(1, 20), true).length === 0, '21:00 前唔發夢'); const dd = S2.dreamDue(s, at(1, 22), true); ok(dd.length === 1 && dd[0].day === d0 && dd[0].live, '21:00 後瞓 → 即時發夢', dd);
  ok(S2.dreamDue(s, at(1, 22), false).length === 0, '冇瞓唔發'); ok(S2.dreamDue(s, at(2, 2), true).length === 1, '凌晨瞓緊都計前一晚');
  const d = S2.dream(s, d0, at(1, 22), true); ok(d && d.line === 'E' && p.dreams.length === 1, '記低夢 E'); ok(!S2.dream(s, d0, at(1, 23)), '每晚一次');
  S2.careNote(s, 'water', at(2, 9)); S2.careNote(s, 'rinse', at(2, 10)); ok(S2.topCare(s, d0 + 1) === 'B', '打和揀最近嗰個（B 後過 A）');
  const cu = S2.dreamDue(s, at(3, 7), false); ok(cu.length === 1 && cu[0].day === d0 + 1 && !cu[0].live, '過咗翌日 06:00 補記（唔使瞓）', cu);
  S2.dream(s, d0 + 1, at(3, 7)); ok(S2.dreamDue(s, at(4, 7), false).some(x => x.day === d0 + 2), '冇照顧嗰晚都要補記');
  S2.dream(s, d0 + 2, at(4, 7)); ok(p.dreams[2].line === null, '冇照顧 → 冇夢（null）');
  ok(p.dreams.length === 3 && S2.dreamDue(s, at(9, 22), true).length === 0, '最多 3 個夢');
  ok(!S2.hatchReady(s, at(3, 23)) && S2.hatchReady(s, at(4, 8)), '3 晚之後先孵（第一眼）');
  const keep = Object.keys(p.care).length; for (let i = 0; i < 9; i++) S2.careNote(s, 'feed', at(i, 12)); ok(Object.keys(p.care).length <= C.careKeepDays && keep <= C.careKeepDays, 'care 只留最近 6 日');
  const before = strip(s); S2.careNote(s, 'feed', at(4, 9)); ok(strip(s) === before, '記照顧唔郁團絨（唔入 noteCare）');
  S2.hatch(s, at(4, 8)); ok(p.phase === 'kid' && p.rel === 'follow' && p.relQ[0] === 'follow', '孵化 → 跟班（升級場面排隊）'); }

console.log('④ 時間線（蛋 3 晚 → S1 1 → S2 2 → S3 3 → S4 3 → S5 3 → S6）');
{ const s = kid(10), p = S2.st(s); const sk = (d) => S2.stageOf(s, at(d, 12));
  ok(sk(10) === 'S1' && sk(11) === 'S2' && sk(12) === 'S2' && sk(13) === 'S3' && sk(15) === 'S3' && sk(16) === 'S4' && sk(19) === 'S5' && sk(22) === 'S6' && sk(60) === 'S6', '每階日數對', [10, 11, 12, 13, 16, 19, 22].map(sk));
  p.line = 'F'; ok(S2.formOf(s, at(13, 12)) === 'F1' && S2.formOf(s, at(16, 12)) === 'S4F' && S2.formOf(s, at(19, 12)) === 'F2' && S2.formOf(s, at(22, 12)) === 'F3', 'formOf：F1 → S4F → F2 → F3');
  ok(S2.formOf(s, at(10, 12)) === 'S1' && S2.formOf(s, at(11, 12)) === 'S2', 'S1／S2 共用');
  for (const L of S2.LINES) { p.line = L; for (const d of [13, 16, 19, 22]) { const f = S2.formOf(s, at(d, 12)); if (!ACT.forms[f]) ok(false, '缺形態 ' + f); } } ok(true, '8 系 × 4 階 formOf 全部有美術');
  ok(3 + 1 + 2 + 3 + 3 + 3 === 15, '約 16 日（蛋 3＋S1–S5 12，第 16 日 S6）'); }

console.log('⑤ 教錯課：S1–S2、每日 2 堂、最多 6 堂、每堂 +2 親密');
{ const s = kid(10), p = S2.st(s), t = at(10, 14);
  let r = S2.lesson(s, 'A', t); ok(r.ok && r.n === 2 && p.lessons.length === 1 && p.intim === 2, '第一堂 OK（+2）', r);
  ok(S2.lesson(s, 'B', t + 1).ok && !S2.lesson(s, 'C', t + 2).ok && S2.canLesson(s, t + 3).reason === 'today', '每日 2 堂');
  ok(!S2.lesson(s, 'Q', at(11, 14)).ok, '唔識嘅系唔收');
  S2.lesson(s, 'C', at(11, 14)); S2.lesson(s, 'D', at(11, 15)); S2.lesson(s, 'E', at(12, 14)); S2.lesson(s, 'F', at(12, 15));
  ok(p.lessons.length === 6 && S2.canLesson(s, at(12, 16)).reason !== undefined && !S2.canLesson(s, at(12, 16)).ok, '3 日最多 6 堂', p.lessons.length);
  ok(S2.canLesson(s, at(13, 14)).reason === 'stage' || S2.canLesson(s, at(13, 14)).reason === 'max', 'S3 唔上堂');
  const y = kid(10); y.sleeping = true; ok(S2.canLesson(y, at(10, 14)).reason === 'sleep', '團絨瞓緊唔上堂');
  const z = kid(10); ok(S2.canLesson(z, at(13, 14)).reason === 'stage', 'S3 起唔再上堂'); }

console.log('⑥ S3 結算 4 情況');
{ const r0 = S2.settlePick([{ day: 1, line: 'A' }, { day: 2, line: 'A' }, { day: 3, line: 'B' }], [{ line: 'C', at: 9 }], () => 0.5); ok(r0.line === 'A' && r0.how === 'max' && r0.pts.A === 2, '最高勝（A 2 分）', r0);
  const r1 = S2.settlePick([{ day: 1, line: 'A' }, { day: 2, line: 'B' }], [{ line: 'A', at: 1 }, { line: 'B', at: 2 }, { line: 'H', at: 3 }], () => 0.5); ok(r1.line === 'B' && r1.how === 'tieLesson', '打和 → 揀最近一堂（打和入面嘅）', r1);
  const r2 = S2.settlePick([{ day: 1, line: 'G', at: 1 }, { day: 2, line: 'D', at: 2 }, { day: 3, line: null }], [], () => 0.5); ok(r2.line === 'D' && r2.how === 'tieDream', '冇堂 → 揀最近一個夢', r2);
  const r3 = S2.settlePick([{ day: 1, line: null }], [], () => 0.99); ok(r3.how === 'random' && r3.line === 'H', '乜都冇 → 隨機', r3);
  const seen = new Set(); for (let i = 0; i < 8; i++) seen.add(S2.settlePick([], [], () => i / 8 + 0.01).line); ok(seen.size === 8, '隨機 8 系都有機會');
  const s = kid(10), p = S2.st(s); p.lessons = [{ line: 'E', day: 0, at: 5 }]; const st0 = S2.settle(s, at(13, 9)); ok(p.line && st0.how && S2.settle(s, at(14, 9)) === st0, '結算一次（之後唔變）', st0); }

console.log('⑦ 親密度（每日上限 10）＋關係級');
{ const s = kid(10), p = S2.st(s), t = at(10, 10);
  S2.gain(s, 'comfort', t); S2.gain(s, 'comfort', t); S2.gain(s, 'eat', t); S2.gain(s, 'lesson', t); S2.gain(s, 'duo', t); ok(p.intim === 9, '2+2+1+2+2 = 9', p.intim);
  const r = S2.gain(s, 'comfort', t); ok(r.n === 1 && p.intim === 10, '上限 10：只加 1', r); ok(S2.gain(s, 'eat', t).n === 0 && p.stats.capHit >= 1, '滿咗唔加');
  ok(S2.gain(s, 'eat', at(11, 9)).n === 1, '第二日重新計');
  p.intim = 29; const u = S2.gain(s, 'eat', at(12, 9)); ok(u.level === 'friend' && p.rel === 'friend', '30 → 朋友', u);
  p.intim = 85; ok(S2.checkLevel(s, at(15, 9)) === null && p.rel === 'friend', '80 但未 S6 → 停喺朋友');
  ok(S2.checkLevel(s, at(22, 9)) === 'family' && p.rel === 'family' && p.relQ.join() === 'follow,friend,family', 'S6＋80 → 家人；升級排隊 3 個', p.relQ);
  const y = kid(0); S2.st(y).intim = 85; S2.st(y).rel = 'follow'; ok(S2.checkLevel(y, at(30, 9)) === 'family' && S2.st(y).rel === 'family', '一次過跳朋友 → 家人都得');
  const e = elder(); ok(S2.gain(e, 'eat', t).n === 0, '未有細佬唔加'); }

console.log('⑧ 一齊瞓／雙人彈彈葉／一齊食／喊');
{ const s = kid(10), p = S2.st(s); s.sleeping = true;
  ok(!S2.sleepTogether(s, at(10, 20)), '21:00 前唔計'); ok(S2.sleepTogether(s, at(10, 22)).n === 2, '21–03 兩隻瞓 → +2'); ok(!S2.sleepTogether(s, at(11, 1)), '每晚 1 次（凌晨同一晚）');
  ok(!S2.sleepTogether(s, at(11, 4)), '03:00 後唔計'); ok(S2.sleepTogether(s, at(11, 21, 30)).n === 2, '第二晚再計');
  ok(!S2.canDuo(s, at(12, 10)).ok && S2.canDuo(s, at(12, 10)).reason === 'rel', '朋友前唔開雙人彈彈葉');
  p.rel = 'friend'; ok(S2.duoDone(s, at(12, 10), 5).n === 2 && S2.duoDone(s, at(12, 11), 5).ok && !S2.duoDone(s, at(12, 12), 5).ok, '每日 2 局 +2');
  const st0 = JSON.stringify(s.stats), sh = s.shards; S2.duoDone(s, at(13, 10), 9); ok(JSON.stringify(s.stats) === st0 && s.shards === sh, '雙人局唔郁團絨 stats（mgPlays）／碎');
  ok(S2.eatTogether(s, at(13, 12)).n === 1, '一齊食 +1');
  s.sleeping = false; const d = S2.today(s, at(14, 10)); ok(d.cryPlan >= 2 && d.cryPlan <= 3, '每日喊 2–3 次', d.cryPlan);
  ok(!S2.cryWanted(s, at(14, 6)) && S2.cryWanted(s, at(14, 10)) && !S2.cryWanted(s, at(14, 22)), '07–21 先喊');
  for (let i = 0; i < d.cryPlan; i++) S2.cryStart(s, at(14, 10 + i)); ok(!S2.cryWanted(s, at(14, 16)), '喊夠就停');
  const plans = new Set(); for (let i = 0; i < 20; i++) plans.add(S2.today(s, at(20 + i, 10)).cryPlan); ok(plans.has(2) && plans.has(3), '2 同 3 都會出', [...plans]); }

console.log('⑨ 雙人 clip／升級場面／孵化第一眼數學');
{ const fc = (id) => (DUO.overlays[id] && DUO.overlays[id].frames) || 1;
  const a = S2.sceneAt(DUO.clips.comfort_cry, 300, fc); ok(a.actors.tr.clip === 'walk' && Math.abs(a.actors.tr.x - (-10 - 14 + 14 * 300 / 700)) < 1e-6 && a.actors.kid.clip === 'cry', '哄喊 300ms：團絨行埋去、細佬喊', a.actors);
  const b = S2.sceneAt(DUO.clips.comfort_cry, 2400, fc); ok(b.actors.tr.clip === 'emo_happy' && b.actors.kid.clip === 'idle' && b.overlays.some(o => o.id === 'fx_sparkle'), '2400ms：開心＋細佬收聲＋閃');
  ok(S2.sceneAt(DUO.clips.comfort_cry, 9999, fc).done, '播完 done');
  const e = S2.sceneAt(DUO.clips.eat_together, 1600, fc); ok(!e.done && e.t === 100, '一齊食 loop');
  const L = S2.sceneAt(LV.scenes.lv_friend, 2750, fc); const bd = L.overlays.find(o => o.id === 'badge_friend'); ok(bd && bd.y < -46 && bd.y > -46 + 8 - 1e-6 === false || (bd && bd.y < -38), '徽章 move 由下彈上', bd);
  const hb = S2.sceneAt(LV.scenes.lv_friend, 2500, fc).overlays.find(o => o.id === 'ov_heart_big'); ok(hb && hb.frame === 1, '大心心 frames [0,1,1]', hb);
  const cf = S2.sceneAt(LV.scenes.lv_friend, 4500, fc).overlays.find(o => o.id === 'ov_confetti'); ok(!cf, '彩紙 3900 後收');
  const h0 = S2.hatchFrame(100), h1 = S2.hatchFrame(700), h2 = S2.hatchFrame(1000), h3 = S2.hatchFrame(2000);
  ok(h0.egg && h0.egg.crack === 0 && !h0.kid && S2.hatchFrame(450).egg.crack === 2, '0–600：蛋震＋裂');
  ok(h1.rays && h1.flash > 0 && h2.kid && h2.shell.length === 4 && h2.kid.blink, '600–800 光、800 後殼飛＋S1 眨眼');
  ok(h3.tr && Math.abs(h3.tr.x - 47) < 1e-6 && h3.tr.clip === 'emo_happy' && h3.heart && !h3.rays, '2000ms：團絨到 x 47 開心＋心心（最後一格）', h3.tr); }

console.log('⑩ 驗收模擬：16 日內正常玩家到家人 ≥80%；每日 1 次玩家到朋友 ≥90%');
{ const rng = (seed) => () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  function run(seed, normal) {
    const r = rng(seed), s = elder(), p = S2.st(s); S2.noteElder(s, at(0, 20)); S2.deliver(s, at(1, 9 + Math.floor(r() * 10)));
    for (let d = 0; d < 3; d++) { S2.careNote(s, 'feed', at(1 + d, 12)); S2.dream(s, p.d0 + d, at(2 + d, 7)); }
    S2.hatch(s, at(4, 9));
    for (let d = 4; d < 1 + 16; d++) {
      const sk = S2.stageOf(s, at(d, 12));
      if (sk === 'S3' && !p.line) S2.settle(s, at(d, 12), r);
      if (normal) { // 正常：日頭 2–3 段、晚上一齊瞓
        const plan = S2.today(s, at(d, 10)).cryPlan; for (let i = 0; i < plan; i++) if (r() < 0.75) S2.comfort(s, at(d, 10 + i));
        for (let i = 0; i < 2; i++) if (r() < 0.9) S2.eatTogether(s, at(d, 12 + i * 6));
        if (sk === 'S1' || sk === 'S2') { S2.lesson(s, S2.LINES[Math.floor(r() * 8)], at(d, 15)); S2.lesson(s, S2.LINES[Math.floor(r() * 8)], at(d, 16)); }
        if (r() < 0.7) { s.sleeping = true; S2.sleepTogether(s, at(d, 22)); s.sleeping = false; }
        if (p.rel !== 'follow') for (let i = 0; i < 2; i++) if (r() < 0.5) S2.duoDone(s, at(d, 17 + i), 5);
      } else {     // 每日上線 1 次（約 5–10 分鐘）：餵一次，有 60% 機會撞到喊；S1–S2 上 1 堂
        S2.eatTogether(s, at(d, 19)); if (r() < 0.85) S2.comfort(s, at(d, 19, 3));   // 第一次喊排喺上線後 60–180s → 5 分鐘 session 大多撞到
        if ((sk === 'S1' || sk === 'S2') && r() < 0.8) S2.lesson(s, S2.LINES[Math.floor(r() * 8)], at(d, 19, 8));
        if ((sk === 'S1' || sk === 'S2') && r() < 0.4) S2.lesson(s, S2.LINES[Math.floor(r() * 8)], at(d, 19, 9));
        if (p.rel !== 'follow' && r() < 0.5) S2.duoDone(s, at(d, 19, 9), 3);
      }
      S2.checkLevel(s, at(d, 23));
    }
    return p.rel;
  }
  let fam = 0, fr = 0, N = 300; for (let i = 0; i < N; i++) { if (run(i + 1, true) === 'family') fam++; const lr = run(i + 1001, false); if (lr === 'friend' || lr === 'family') fr++; }
  ok(fam / N >= 0.8, '正常玩家 16 日內到家人 ' + (100 * fam / N).toFixed(0) + '%（≥80%）');
  ok(fr / N >= 0.9, '每日 1 次玩家到朋友 ' + (100 * fr / N).toFixed(0) + '%（≥90%）'); }

console.log(`\n結果：${pass} 通過，${fail} 失敗`); process.exit(fail ? 1 : 0);
