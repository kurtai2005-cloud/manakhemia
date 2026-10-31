/* §7 新支線 ×5（tide／shroom／crystal／moon／ember）Node 無依賴測試：node tests/branches5.test.js
   覆蓋：① 判定次序 ② 門檻（CQ／35%／5pp／平手）③ 分數來源（芽崽＋跳跳期）④ 落雨 rinse／21–03 雙計規則 ⑤ 靜光對應 ⑥ DEV 強制支線 */
const fs = require('fs'), path = require('path');
const S = require('../src/sim.js');
const D = require('../src/data.js');
const P = D.PARAMS, EV6 = P.evo6;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
let HOUR = 12, RAIN = false;
S.setHourFn(() => HOUR); S.setRainFn(() => RAIN);
const KIND = { shroom: 'feed', ember: 'play', tide: 'rinse', crystal: 'poop' };
function pet(stage) { const s = S.newState(1e12, 7); s.stage = stage || 'sprout'; Object.assign(s.needs, { hunger: 60, mood: 60, clean: 90, energy: 80 }); return s; }
function setClean(s, avg, st) { const E = s.evo || (s.evo = { evIn: {}, care: {} }); E.cl = E.cl || {}; E.cl[st || 'sprout'] = { sum: avg * 1e6, sec: 1e6 }; }
// counts：{ feed:n, play:n, rinse:n, poop:n, mg:n }（中午、冇雨，用 noteCare）
function build(counts, o) {
  o = o || {}; const s = pet(o.stage || 'sprout'); HOUR = o.h == null ? 12 : o.h; RAIN = !!o.rain;
  for (const k in counts) for (let i = 0; i < counts[k]; i++) S.noteCare(s, null, k);
  setClean(s, o.clean == null ? 50 : o.clean); HOUR = 12; RAIN = false; return s;
}
function toAdult(s, cq) { s.stage = 'juvenile'; s.cq = cq; s.growthSec = P.stageSec.juvenile - 1; HOUR = 12; RAIN = false; S.step(s, 5, {}); return s; }
const evOf = (s) => s.ev.find(e => e.type === 'evolve') || {};

console.log('# 資料：9 條支線、參數照 §7');
ok(D.BRANCH5.join() === 'tide,shroom,crystal,moon,ember', 'BRANCH5 = tide／shroom／crystal／moon／ember');
ok(D.BRANCHES.length === 9 && D.BRANCHES[0] === 'lumi' && D.BRANCHES.slice(-3).join() === 'bright,soft,dust', 'BRANCHES 9 條（螢絨＋新 5＋燦光／柔光／微塵）');
ok(EV6.b5CQ === 55 && EV6.b5TopShare === 0.35 && EV6.b5Gap === 0.05 && EV6.b5CrystalCleanAvg === 70 && EV6.b5MoonFrom === 21 && EV6.b5MoonTo === 3, 'PARAMS.evo6 b5* = 55／35%／5pp／清潔 70／21–03');
ok(['水珠', '菇傘', '晶角', '月眠', '火苗'].every((n, i) => D.FORM_NAME[D.BRANCH5[i]] === n), 'FORM_NAME 水珠／菇傘／晶角／月眠／火苗');

console.log('# ① 判定次序：螢絨 → 新 5 條 → 燦光／柔光／微塵');
{
  // 符合螢絨（夜晚照顧 ≥40%＋螢火散步＋CQ≥55）同時又符合新 5 條（菇傘）→ 螢絨
  const s = build({ feed: 10, play: 2 }, { h: 22 });   // 22:00 → 夜晚照顧 100%；月眠亦計 → 月眠 12/12
  s.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 };
  ok(S.branch5Check(Object.assign(pet(), { evo: JSON.parse(JSON.stringify(s.evo)), cq: 80 })).ok, '（前提）新 5 條本身成立');
  toAdult(s, 80); ok(s.form === 'lumi' && evOf(s).why === 'lumi', '螢絨優先過新 5 條', s.form);
  const t = toAdult(build({ feed: 10, play: 2 }), 80); ok(t.form === 'shroom' && evOf(t).why === 'b5', '新 5 條（菇傘）優先過燦光（CQ 80）', t.form);
  for (const [cq, f] of [[80, 'bright'], [70, 'bright'], [60, 'soft'], [40, 'soft'], [30, 'dust']]) {
    const u = toAdult(build({ feed: 3, play: 3, rinse: 3 }), cq);   // 三條平手 → 行返原本
    ok(u.form === f && evOf(u).why === 'cq', `新 5 條唔成立 → CQ ${cq} → ${D.FORM_NAME[f]}`, u.form);
  }
  const lumiOnly = build({ feed: 3, play: 3, rinse: 3 }, { h: 18 }); lumiOnly.evo.evIn.sprout = { [EV6.lumiEvent]: 2 }; toAdult(lumiOnly, 60);
  ok(lumiOnly.form === 'lumi', '螢絨條件照舊（新 5 條唔郁到）', lumiOnly.form);
}

console.log('# ② 門檻：CQ ≥55、最高 ≥35%、差 ≥5 個百分點；平手 → 原本 4 條');
{
  const c = (counts, cq, o) => { const s = build(counts, o); s.cq = cq; return S.branch5Check(s); };
  ok(!c({ feed: 10, play: 2 }, 54).ok && c({ feed: 10, play: 2 }, 55).ok, 'CQ 54 ✗／55 ✓');
  ok(toAdult(build({ feed: 10, play: 2 }), 54).form === 'soft', 'CQ 54 → 柔光（唔去新支線）');
  let r = c({ feed: 7, play: 6, rinse: 4, poop: 3 }, 60);   // 20 次：菇傘 35%、火苗 30%（晶角清潔唔夠 → 0）
  ok(r.ok && r.form === 'shroom' && r.topShare === 0.35 && r.secondShare === 0.3, '最高 = 35%、差 = 5pp（啱啱好）→ 成立', JSON.stringify(r.score));
  r = c({ feed: 34, play: 20, rinse: 23, poop: 23 }, 60); ok(!r.ok && !r.topOk && r.top === 'shroom', '最高 34% → 唔成立', r.topShare);
  r = c({ feed: 35, play: 31, rinse: 17, poop: 17 }, 60); ok(!r.ok && r.topOk && !r.gapOk, '差 4pp → 唔成立', r.topShare + '/' + r.secondShare);
  r = c({ feed: 35, play: 30, rinse: 18, poop: 17 }, 60); ok(r.ok && r.gapOk, '差 5pp → 成立');
  r = c({ feed: 7, play: 7, rinse: 3, poop: 3 }, 90); ok(!r.ok && r.tie, '平手（7／7）→ 唔成立', JSON.stringify(r.score));
  ok(toAdult(build({ feed: 7, play: 7, rinse: 3, poop: 3 }), 90).form === 'bright', '平手 → 行返燦光（CQ 90）');
  ok(toAdult(build({}), 90).form === 'bright' && !S.branch5Check(build({})).ok, '冇照顧（總數 0）→ 原本 4 條');
}

console.log('# ③ 分數來源（只計芽崽＋跳跳期）');
{
  for (const [b, k] of Object.entries(KIND)) {
    const s = build(b === 'ember' ? { play: 10, feed: 1 } : { [k]: 10, play: 1 }, { clean: 90 }); s.cq = 60; const r = S.branch5Check(s);
    ok(r.form === b, `${k} → ${D.FORM_NAME[b]}`, JSON.stringify(r.score));
  }
  { const s = build({ mg: 6, play: 4, feed: 3 }); s.cq = 60; ok(S.branch5Check(s).score.ember === 10 && S.branch5Check(s).form === 'ember', 'play＋mg → 火苗'); }
  { const s = build({ feed: 3 }, { rain: true }); s.cq = 60; const r = S.branch5Check(s); ok(r.score.tide === 3 && r.score.shroom === 3, '落雨時餵食 → 水珠＋菇傘都計'); }
  { const s = build({ feed: 3, rinse: 6 }); s.cq = 60; ok(S.branch5Check(s).form === 'tide', 'rinse → 水珠'); }
  // 晶角：清潔度平均 ≥70 先計
  { const s = build({ poop: 8, feed: 2 }, { clean: 69.9 }); s.cq = 60; const r = S.branch5Check(s); ok(!r.crystalOk && r.score.crystal === 0 && r.raw.crystal === 8 && !r.ok, '清潔平均 69.9 → 晶角 0 分（新 5 條唔成立）', JSON.stringify(r)); }
  { const s = build({ poop: 8, feed: 2 }, { clean: 70 }); s.cq = 60; const r = S.branch5Check(s); ok(r.crystalOk && r.score.crystal === 8 && r.form === 'crystal', '清潔平均 70 → 晶角計分 → 晶角'); }
  { // 清潔平均 = 時間加權（step 每 tick 記），跨芽崽＋跳跳期
    const s = pet('sprout'); s.needs.clean = 100; S.noteClean(s, 100); s.stage = 'juvenile'; s.needs.clean = 40; S.noteClean(s, 100);
    ok(S.branch5Check(s).cleanAvg === 70, '清潔平均：時間加權（100×100s＋40×100s → 70）', S.branch5Check(s).cleanAvg);
    const t = pet('sprout'); t.needs.clean = 80; S.step(t, 30, {}); ok(t.evo.cl.sprout && t.evo.cl.sprout.sec === 30, 'step() 自動記清潔時間');
  }
  // 月眠：21:00–03:00；邊界
  for (const [h, want] of [[20, 0], [21, 1], [23, 1], [0, 1], [2, 1], [3, 0], [12, 0]]) { const s = build({ feed: 1 }, { h }); ok(S.branch5Check(s).score.moon === want, `${h}:00 照顧 → 月眠 ${want}`); }
  { const s = build({}); HOUR = 12; s.sleeping = true; ok(S.notePetSleep(s) === true && S.branch5Check(s).score.moon === 1 && S.branch5Check(s).all === 1, '瞓覺時撫摸 → 月眠（白天都計）');
    s.sleeping = false; ok(S.notePetSleep(s) === false && S.branch5Check(s).score.moon === 1, '醒緊撫摸唔計');
    ok(S.careShare(s).all === 0, '瞓覺撫摸唔郁螢絨嘅夜晚照顧比例'); }
  { const s = build({ feed: 10 }, { h: 22 }); s.cq = 60; const r = S.branch5Check(s); ok(r.tie && !r.ok, '21–03 淨係餵 → 月眠＝菇傘平手 → 唔成立（§7 雙計嘅後果，已報）'); }
  { const s = build({ feed: 2, play: 8 }, { h: 23 }); s.cq = 60; ok(S.branch5Check(s).form === 'moon', '夜深陪玩（23:00 玩 8 餵 2）→ 月眠 100% 勝火苗 80%'); }
  // 範圍：只計芽崽＋跳跳期
  { const s = build({ feed: 10 }, { stage: 'newborn' }); ok(S.branch5Check(s).all === 0, '絨點（newborn）照顧唔計'); }
  { const s = build({ feed: 5 }, { stage: 'juvenile' }); S.noteCare(Object.assign(s, { stage: 'sprout' }), null, 'feed'); ok(S.branch5Check(s).all === 6, '芽崽＋跳跳期加埋計'); }
  { const s = pet('adult'); s.form = 'soft'; S.noteCare(s, null, 'feed'); ok(S.branch5Check(s).all === 0, '成年後照顧唔計'); }
  { // 用真實動作（feed／play／rinse／clearPoop／mgApply）
    const s = pet('sprout'); s.needs.hunger = 10; S.feed(s, 'meal'); S.play(s); S.rinse(s); s.poops = 1; S.clearPoop(s); S.mgApply(s, 10, 1e12);
    const b = s.evo.b5.sprout; ok(b.all === 5 && b.shroom === 1 && b.ember === 2 && b.tide === 1 && b.crystal === 1 && b.moon === 0, '真實動作入分（feed／play＋mg／rinse／clearPoop）', JSON.stringify(b));
  }
}

console.log('# ④ 落雨 rinse 只計一次；21–03 雙計');
{
  { const s = build({ rinse: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 1 && b.all === 1, '落雨 rinse → 水珠 +1（唔係 +2）', JSON.stringify(b)); }
  { const s = build({ play: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 1 && b.ember === 1 && b.all === 1, '落雨玩 → 水珠 +1、火苗 +1、總數 +1'); }
  { const s = build({ feed: 1 }, { h: 22 }); const b = s.evo.b5.sprout; ok(b.moon === 1 && b.shroom === 1 && b.all === 1, '22:00 餵 → 月眠 +1、菇傘 +1（兩邊都計）'); }
  { const s = build({ rinse: 1 }, { h: 1, rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 1 && b.moon === 1 && b.all === 1, '01:00 落雨 rinse → 水珠 1、月眠 1'); }
  { const s = build({}); HOUR = 22; s.sleeping = true; S.notePetSleep(s); HOUR = 12; ok(s.evo.b5.sprout.moon === 1, '22:00 瞓覺撫摸 → 月眠只 +1'); }
  { const s = build({ poop: 2 }, { h: 2, clean: 90 }); const r = S.branch5Check(s); ok(r.score.crystal === 2 && r.score.moon === 2, '02:00 清便便 → 晶角＋月眠'); }
}

console.log('# ⑤ 靜光：每條支線一個樣');
{
  const still = D.BRANCHES.map(b => D.evoForm('elder', b)), guard = D.BRANCHES.map(b => D.evoForm('adult', b));
  ok(new Set(still).size === 9 && still.every(k => D.FORMS[k] && D.FORMS[k].evo), '9 條支線 → 9 個唔同靜光 form', still.join());
  ok(new Set(guard).size === 9, '9 條支線 → 9 個唔同守夜者 form');
  for (const b of D.BRANCH5) ok(D.evoForm('adult', b) === 'evo_guard_' + b && D.evoForm('elder', b) === 'evo_still_' + b && fs.existsSync(path.join(__dirname, '../art/evo6/atlas_evo_still_' + b + '.png')), `${D.FORM_NAME[b]} → evo_guard_${b}／evo_still_${b}（有圖）`);
  for (const b of D.BRANCH5) { const s = toAdult(build(b === 'moon' ? { feed: 5, play: 5 } : { [KIND[b]]: 10 }, { h: b === 'moon' ? 22 : 12, clean: 90 }), 60); ok(s.form === b, `跳跳期完 → ${D.FORM_NAME[b]}`, s.form); s.growthSec = P.stageSec.adult - 1; S.step(s, 5, {}); ok(s.stage === 'elder' && s.form === b && D.evoForm(s.stage, s.form) === 'evo_still_' + b, `${D.FORM_NAME[b]} 成年 → 靜光仍係 ${b}`); }
  for (const b of D.BRANCH5) { const s = pet('elder'); s.form = b; const t = S.deserialize(S.serialize(s), 1e12); ok(t && t.form === b, `存檔來回保留 ${b}`, t && t.form); }
}

console.log('# ⑥ DEV：強制去某支線（9 條）');
{
  for (const b of D.BRANCHES) { const s = build({ feed: 10, play: 2 }); s.evo.force = b; toAdult(s, 30); ok(s.form === b && evOf(s).why === 'dev' && !s.evo.force, `強制 ${D.FORM_NAME[b]} → 跳跳期完去 ${b}（用完清走）`, s.form); }
  { const s = build({ feed: 3 }); s.evo.force = 'nope'; toAdult(s, 30); ok(s.form === 'dust', '亂嘢強制值唔理'); }
  const dp = fs.readFileSync(path.join(__dirname, '../src/devpanel.js'), 'utf8');
  ok(/data-testid="dev-force-row"/.test(dp) && /D\.BRANCHES\.map\(f => btn\(.*'forceBranch:' \+ f, 'dev-force-' \+ f\)/.test(dp) && /forceBranch\(f\)/.test(dp), 'devpanel：強制支線一行（D.BRANCHES 9 個掣 dev-force-<id>）＋ api.forceBranch');
  const mj = fs.readFileSync(path.join(__dirname, '../src/main.js'), 'utf8');
  ok(/D\.BRANCHES\.includes\(branch\)/.test(mj) && /notePetSleep/.test(mj) && /setRainFn\(\(\) => G\.weather === 'rain'\)/.test(mj), 'main：setStage 收 9 條、瞓覺撫摸掛月眠、落雨＝G.weather');
}

console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
