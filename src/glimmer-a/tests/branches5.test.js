/* §7 新支線 ×5（tide／shroom／crystal／moon／ember）Node 無依賴測試：node tests/branches5.test.js
   覆蓋：① 判定次序 ② 門檻（CQ／最高分／差距／平手）③ 分數來源（芽崽＋跳跳期）④ 時段規則（21–03 只計月眠、06–09 只計水珠）＋落雨
         ⑦ 燦光最高分上限 ⑤ 靜光對應 ⑥ DEV 強制支線
   所有門檻／時段都讀 PARAMS.evo6.branch（config）；改 config 唔使改測試。 */
const fs = require('fs'), path = require('path');
const S = require('../src/sim.js');
const D = require('../src/data.js');
const P = D.PARAMS, EV6 = P.evo6, C = EV6.branch;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const inW = (w, h) => w.from <= w.to ? h >= w.from && h < w.to : h >= w.from || h < w.to;
const winAt = (h) => C.windows.find(w => inW(w, h)) || null;
const DAY = [12, 13, 14, 15, 16, 10, 11, 17, 18, 19, 20].find(h => !winAt(h));     // 冇時段規則嘅鐘點
const MOON = C.windows.find(w => w.id === 'moon'), DEW = C.windows.find(w => w.id === 'dew');
const MH = MOON.from, MH2 = (MOON.from + 1) % 24, DH = DEW.from;                    // 月眠／晨露時段內嘅鐘點
const LOWCLEAN = C.crystalCleanAvg - 10;                                             // 晶角唔計分嘅清潔平均
let HOUR = DAY, RAIN = false;
S.setHourFn(() => HOUR); S.setRainFn(() => RAIN);
const KIND = { shroom: 'feed', ember: 'play', tide: 'rinse', crystal: 'poop' };
function pet(stage) { const s = S.newState(1e12, 7); s.stage = stage || 'sprout'; Object.assign(s.needs, { hunger: 60, mood: 60, clean: 90, energy: 80 }); return s; }
function setClean(s, avg, st) { const E = s.evo || (s.evo = { evIn: {}, care: {} }); E.cl = E.cl || {}; E.cl[st || 'sprout'] = { sum: avg * 1e6, sec: 1e6 }; }
// counts：{ feed:n, play:n, rinse:n, poop:n, mg:n }（中午、冇雨，用 noteCare）
function build(counts, o) {
  o = o || {}; const s = pet(o.stage || 'sprout'); HOUR = o.h == null ? DAY : o.h; RAIN = !!o.rain;
  for (const k in counts) for (let i = 0; i < counts[k]; i++) S.noteCare(s, null, k);
  setClean(s, o.clean == null ? LOWCLEAN : o.clean); HOUR = DAY; RAIN = false; return s;
}
function toAdult(s, cq) { s.stage = 'juvenile'; s.cq = cq; s.growthSec = P.stageSec.juvenile - 1; HOUR = DAY; RAIN = false; S.step(s, 5, {}); return s; }
// 百分比 → 次數（總數 100）：菇傘 top%、火苗 second%，其餘用「清潔唔夠嘅清便便」填（入總數但唔計分）
const mk = (top, second) => ({ feed: top, play: second, poop: 100 - top - second });
const baseForm = (cq) => cq >= C.softCQ ? 'soft' : 'dust';   // 燦光／新 5 條都唔成立時
const evOf = (s) => s.ev.find(e => e.type === 'evolve') || {};

console.log('# 資料：9 條支線、config（PARAMS.evo6.branch）');
ok(D.BRANCH5.join() === 'tide,shroom,crystal,moon,ember', 'BRANCH5 = tide／shroom／crystal／moon／ember');
ok(D.BRANCHES.length === 9 && D.BRANCHES[0] === 'lumi' && D.BRANCHES.slice(-3).join() === 'bright,soft,dust', 'BRANCHES 9 條（螢絨＋新 5＋燦光／柔光／微塵）');
ok(['brightCQ', 'brightMaxTopPct', 'b5CQ', 'b5TopPct', 'b5GapPt', 'softCQ', 'crystalCleanAvg'].every(k => Number.isInteger(C[k])) && C.brightCQ > C.softCQ && C.b5TopPct < C.brightMaxTopPct
  && C.windows.every(w => Number.isInteger(w.from) && Number.isInteger(w.to) && D.BRANCH5.includes(w.only)) && MOON.only === 'moon' && DEW.only === 'tide',
  'config 齊（整數門檻＋時段 windows：moon→月眠、dew→水珠）', JSON.stringify(C));
ok(!('b5CQ' in EV6) && !('branchBright' in P) && !('branchSoft' in P), '舊散落門檻（evo6.b5*、branchBright／Soft）已收入 config');
{ const src = fs.readFileSync(path.join(__dirname, '../src/sim.js'), 'utf8').replace(/\/\/.*$/gm, '');
  const fn = (n) => (src.match(new RegExp('function ' + n + '\\([^]*?\\n  }')) || [''])[0];
  ok(['decideBranch', 'openBranch', 'branch5Check', 'noteB5', 'decideForm'].every(n => fn(n) && !/[^\w.](?:[2-9]\d|1\d\d)\b/.test(fn(n).replace(/\* 100/g, ''))), 'sim 判定函數冇寫死門檻數字（全部讀 config）'); }
ok(['水珠', '菇傘', '晶角', '月眠', '火苗'].every((n, i) => D.FORM_NAME[D.BRANCH5[i]] === n), 'FORM_NAME 水珠／菇傘／晶角／月眠／火苗');
console.log(`  · config：燦光 CQ ≥${C.brightCQ} 且最高 <${C.brightMaxTopPct}%；新 5 條 CQ ≥${C.b5CQ}／≥${C.b5TopPct}%／差 ≥${C.b5GapPt}pt；柔光 CQ ≥${C.softCQ}；晶角清潔 ≥${C.crystalCleanAvg}；時段 ${C.windows.map(w => w.id + ' ' + w.from + '–' + w.to + '→' + w.only).join('、')}`);

console.log('# ① 判定次序（§7 修訂）：螢絨 → 燦光（最高分 < 上限）→ 新 5 條 → 柔光 → 微塵');
{
  const hi = Math.max(C.brightCQ, C.b5CQ, EV6.lumiCQ) + 10;
  // 符合螢絨（夜晚照顧 ≥40%＋螢火散步＋CQ）同時又符合新 5 條 → 螢絨
  const s = build({ feed: 10, play: 2 }, { h: MH2 }); s.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 };
  ok(S.branch5Check(Object.assign(pet(), { evo: JSON.parse(JSON.stringify(s.evo)), cq: hi })).ok, '（前提）新 5 條本身成立');
  toAdult(s, hi); ok(s.form === 'lumi' && evOf(s).why === 'lumi', '螢絨優先過新 5 條', s.form);
  const t = toAdult(build({ feed: 10, play: 2 }), hi); ok(t.form === 'shroom' && evOf(t).why === 'b5', `專注（菇傘 83% ≥ ${C.brightMaxTopPct}%）＋CQ ${hi} → 新 5 條（菇傘）唔係燦光`, t.form);
  const flat = { feed: 3, play: 3, rinse: 3 };   // 三條平手（33%）→ 新 5 條唔成立
  for (const [cq, f] of [[100, 'bright'], [C.brightCQ, 'bright'], [C.brightCQ - 1, baseForm(C.brightCQ - 1)], [C.softCQ, 'soft'], [C.softCQ - 1, 'dust']]) {
    const u = toAdult(build(flat), cq); ok(u.form === f && evOf(u).why === 'cq', `全面照顧（平手 33%）→ CQ ${cq} → ${D.FORM_NAME[f]}`, u.form);
  }
  const lumiOnly = build(flat, { h: 18 }); lumiOnly.evo.evIn.sprout = { [EV6.lumiEvent]: 2 }; toAdult(lumiOnly, EV6.lumiCQ);
  ok(lumiOnly.form === 'lumi', '螢絨條件照舊（新 5 條唔郁到）', lumiOnly.form);
}

console.log(`# ② 新 5 條門檻：CQ ≥${C.b5CQ}、最高 ≥${C.b5TopPct}%、差 ≥${C.b5GapPt}pt；平手 → 柔光／微塵`);
{
  const T = C.b5TopPct, G = C.b5GapPt, c = (counts, cq, o) => { const s = build(counts, o); s.cq = cq; return S.branch5Check(s); };
  ok(!c(mk(T, T - G), C.b5CQ - 1).ok && c(mk(T, T - G), C.b5CQ).ok, `CQ ${C.b5CQ - 1} ✗／${C.b5CQ} ✓`);
  ok(toAdult(build(mk(T, T - G)), C.b5CQ - 1).form === baseForm(C.b5CQ - 1), `CQ ${C.b5CQ - 1} → ${D.FORM_NAME[baseForm(C.b5CQ - 1)]}（唔去新支線）`);
  let r = c(mk(T, T - G), C.b5CQ);
  ok(r.ok && r.form === 'shroom' && Math.round(r.topShare * 100) === T && Math.round(r.secondShare * 100) === T - G, `最高 = ${T}%、差 = ${G}pt（啱啱好）→ 成立`, JSON.stringify(r.score));
  r = c(mk(T - 1, T - 1 - G), C.b5CQ); ok(!r.ok && !r.topOk && r.top === 'shroom', `最高 ${T - 1}% → 唔成立`, r.topShare);
  r = c(mk(T, T - G + 1), C.b5CQ); ok(!r.ok && r.topOk && !r.gapOk, `差 ${G - 1}pt → 唔成立`, r.topShare + '/' + r.secondShare);
  r = c(mk(T, T), 90); ok(!r.ok && r.tie, `平手（${T}／${T}）→ 唔成立`, JSON.stringify(r.score));
  ok(toAdult(build(mk(T, T)), 90).form === (T < C.brightMaxTopPct ? 'bright' : 'soft'), '平手 → 照次序（最高 < 上限 → 燦光）');
  ok(toAdult(build({}), 90).form === 'bright' && !S.branch5Check(build({})).ok, '冇照顧（總數 0）→ 燦光（CQ 90）');
}

console.log('# ③ 分數來源（只計芽崽＋跳跳期）');
{
  const cq = C.b5CQ;
  for (const [b, k] of Object.entries(KIND)) {
    const s = build(b === 'ember' ? { play: 10, feed: 1 } : { [k]: 10, play: 1 }, { clean: 100 }); s.cq = cq; const r = S.branch5Check(s);
    ok(r.form === b, `${k} → ${D.FORM_NAME[b]}`, JSON.stringify(r.score));
  }
  { const s = build({ mg: 6, play: 4, feed: 3 }); s.cq = cq; ok(S.branch5Check(s).score.ember === 10 && S.branch5Check(s).form === 'ember', 'play＋mg → 火苗'); }
  { const s = build({ feed: 3 }, { rain: true }); s.cq = cq; const r = S.branch5Check(s); ok(r.score.tide === 3 && r.score.shroom === 3, '（平時鐘點）落雨時餵食 → 水珠＋菇傘都計'); }
  { const s = build({ feed: 3, rinse: 6 }); s.cq = cq; ok(S.branch5Check(s).form === 'tide', 'rinse → 水珠'); }
  // 晶角：清潔度平均 ≥ config 先計
  { const s = build({ poop: 8, feed: 2 }, { clean: C.crystalCleanAvg - 0.1 }); s.cq = cq; const r = S.branch5Check(s); ok(!r.crystalOk && r.score.crystal === 0 && r.raw.crystal === 8 && !r.ok, `清潔平均 ${C.crystalCleanAvg - 0.1} → 晶角 0 分（新 5 條唔成立）`, JSON.stringify(r)); }
  { const s = build({ poop: 8, feed: 2 }, { clean: C.crystalCleanAvg }); s.cq = cq; const r = S.branch5Check(s); ok(r.crystalOk && r.score.crystal === 8 && r.form === 'crystal', `清潔平均 ${C.crystalCleanAvg} → 晶角計分 → 晶角`); }
  { // 清潔平均 = 時間加權（step 每 tick 記），跨芽崽＋跳跳期
    const s = pet('sprout'); s.needs.clean = 100; S.noteClean(s, 100); s.stage = 'juvenile'; s.needs.clean = 40; S.noteClean(s, 100);
    ok(S.branch5Check(s).cleanAvg === 70, '清潔平均：時間加權（100×100s＋40×100s → 70）', S.branch5Check(s).cleanAvg);
    const t = pet('sprout'); t.needs.clean = 80; S.step(t, 30, {}); ok(t.evo.cl.sprout && t.evo.cl.sprout.sec === 30, 'step() 自動記清潔時間');
  }
  { const s = build({}); s.sleeping = true; ok(S.notePetSleep(s) === true && S.branch5Check(s).score.moon === 1 && S.branch5Check(s).all === 1, '瞓覺時撫摸 → 月眠（白天都計）');
    s.sleeping = false; ok(S.notePetSleep(s) === false && S.branch5Check(s).score.moon === 1, '醒緊撫摸唔計');
    ok(S.careShare(s).all === 0, '瞓覺撫摸唔郁螢絨嘅夜晚照顧比例'); }
  // 範圍：只計芽崽＋跳跳期
  { const s = build({ feed: 10 }, { stage: 'newborn' }); ok(S.branch5Check(s).all === 0, '絨點（newborn）照顧唔計'); }
  { const s = build({ feed: 5 }, { stage: 'juvenile' }); S.noteCare(Object.assign(s, { stage: 'sprout' }), null, 'feed'); ok(S.branch5Check(s).all === 6, '芽崽＋跳跳期加埋計'); }
  { const s = pet('adult'); s.form = 'soft'; S.noteCare(s, null, 'feed'); ok(S.branch5Check(s).all === 0, '成年後照顧唔計'); }
  { // 用真實動作（feed／play／rinse／clearPoop／mgApply）
    const s = pet('sprout'); s.needs.hunger = 10; S.feed(s, 'meal'); S.play(s); S.rinse(s); s.poops = 1; S.clearPoop(s); S.mgApply(s, 10, 1e12);
    const b = s.evo.b5.sprout; ok(b.all === 5 && b.shroom === 1 && b.ember === 2 && b.tide === 1 && b.crystal === 1 && b.moon === 0, '真實動作入分（feed／play＋mg／rinse／clearPoop）', JSON.stringify(b));
  }
}

console.log('# ④ 時段規則（config windows）：21–03 只計月眠（§7 修訂）、06–09 只計水珠（v2）；落雨 rinse 只計一次');
{
  for (const w of C.windows) {   // 每個時段：頭／尾一個鐘喺入面，前一個鐘／to 喺出面；入面淨計 only，唔計本身類型
    const prev = (w.from + 23) % 24, last = (w.to + 23) % 24;
    for (const [h, inside] of [[w.from, true], [last, true], [w.to, !!winAt(w.to) && winAt(w.to).only === w.only], [prev, !!winAt(prev) && winAt(prev).only === w.only]]) {
      const s = build({ feed: 1 }, { h }), b = s.evo.b5.sprout;
      ok(inside ? (b[w.only] === 1 && b.shroom === (w.only === 'shroom' ? 1 : 0) && b.all === 1) : (b[w.only] === 0 || w.only === 'shroom'), `${w.id}：${h}:00 餵 → ${inside ? '只計' + D.FORM_NAME[w.only] : '唔計' + D.FORM_NAME[w.only]}`, JSON.stringify(b));
    }
  }
  for (const [w, kinds] of [[MOON, ['feed', 'play', 'rinse', 'poop', 'mg']], [DEW, ['feed', 'play', 'poop', 'mg']]]) {
    for (const k of kinds) { const s = build({ [k]: 1 }, { h: w.from, rain: true, clean: 100 }), b = s.evo.b5.sprout;
      const others = D.BRANCH5.filter(x => x !== w.only).every(x => b[x] === 0);
      ok(b[w.only] === 1 && others && b.all === 1, `${w.id} ${w.from}:00 落雨 ${k} → 只計${D.FORM_NAME[w.only]} 1（唔計本身類型／落雨）`, JSON.stringify(b)); }
  }
  { const s = build({ rinse: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 1 && b.all === 1, '平時落雨 rinse → 水珠 +1（唔係 +2）', JSON.stringify(b)); }
  { const s = build({ play: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 1 && b.ember === 1 && b.all === 1, '平時落雨玩 → 水珠 +1、火苗 +1、總數 +1'); }
  { const s = build({}); HOUR = MH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; ok(s.evo.b5.sprout.moon === 1, `${MH}:00 瞓覺撫摸 → 月眠只 +1`); }
  { const s = build({}); HOUR = DH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; const b = s.evo.b5.sprout; ok(b.moon === 1 && b.tide === 0, `${DH}:00 瞓覺撫摸 → 仍然計月眠（唔係水珠）`, JSON.stringify(b)); }
  // 夜晚淫餵 → 月眠
  { const s = build({ feed: 10 }, { h: MH2 }); s.cq = C.b5CQ; const r = S.branch5Check(s); ok(r.ok && r.form === 'moon' && r.score.shroom === 0 && r.score.moon === 10, '夜晚淨係餵 → 月眠 100%（菇傘唔計）', JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 12, play: 2 }, { h: MH2 }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'moon' && evOf(s).why === 'b5', `夜晚淫餵（${MH2}:00 餵 12 玩 2，高 CQ）→ 月眠（≥ 上限唔去燦光）`, s.form); }
  { const s = build({ feed: 6 }, { h: MH }); HOUR = DAY; for (let i = 0; i < 4; i++) S.noteCare(s, null, 'feed'); s.cq = C.b5CQ; const r = S.branch5Check(s);
    ok(r.score.moon === 6 && r.score.shroom === 4 && r.form === (60 - 40 >= C.b5GapPt && 60 >= C.b5TopPct ? 'moon' : null), '夜晚 6 次＋白天 4 次餵 → 月眠 60%、菇傘 40%'); }
  { const s = build({ feed: 2, play: 8 }, { h: MH2 }); s.cq = C.b5CQ; ok(S.branch5Check(s).form === 'moon', `夜深陪玩（${MH2}:00 玩 8 餵 2）→ 月眠 100%（火苗唔計）`); }
  // 早起玩家 → 水珠
  { const s = build({ feed: 6, play: 4 }, { h: DH }); s.cq = C.b5CQ; const r = S.branch5Check(s); ok(r.form === 'tide' && r.score.tide === 10 && r.score.shroom === 0 && r.score.ember === 0, `晨露：${DH}:00 餵 6 玩 4 → 水珠 100%`, JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 8, play: 4 }, { h: DH }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'tide' && evOf(s).why === 'b5', '早起玩家（晨早照顧為主，高 CQ）→ 水珠', s.form); }
  { const s = build({ poop: 2 }, { h: MH, clean: 100 }); const r = S.branch5Check(s); ok(r.score.crystal === 0 && r.score.moon === 2, `${MH}:00 清便便 → 只計月眠`); }
}

console.log(`# ⑦ 燦光：CQ ≥${C.brightCQ} 且最高分 <${C.brightMaxTopPct}%（全面照顧）先過新 5 條`);
{
  const M = C.brightMaxTopPct, G = C.b5GapPt, hi = Math.max(C.brightCQ, C.b5CQ) + 10, go = (counts, cq, o) => toAdult(build(counts, o), cq);
  let s = go(mk(M - 1, M - 1 - G), hi); ok(s.form === 'bright' && evOf(s).b5.ok && Math.round(evOf(s).b5.topShare * 100) === M - 1, `最高 ${M - 1}%（新 5 條本身成立）＋CQ ${hi} → 燦光`, s.form);
  s = go(mk(M, M - G), hi); ok(s.form === 'shroom' && evOf(s).why === 'b5', `最高 ${M}%（啱啱好）＋CQ ${hi} → 菇傘`, s.form);
  s = go({ feed: 9, play: 4, rinse: 4, poop: 3 }, C.brightCQ); ok(s.form === (9 * 100 >= M * 20 ? 'shroom' : 'bright'), `9/20（45%）＋CQ ${C.brightCQ} → 照上限判`, s.form);
  if (C.brightCQ - 1 >= C.b5CQ) { s = go(mk(M - 1, M - 1 - G), C.brightCQ - 1); ok(s.form === 'shroom', `CQ ${C.brightCQ - 1}（唔夠燦光）＋最高 ${M - 1}% → 菇傘`, s.form); }
  s = go(mk(M - 1, M - 1 - G), C.brightCQ); ok(s.form === 'bright', `CQ ${C.brightCQ}（啱啱好）＋最高 ${M - 1}% → 燦光`, s.form);
  s = go({ feed: 8, poop: 2 }, hi, { clean: 100 }); ok(s.form === 'shroom', '清便便都計晶角，但最高係菇傘 80% → 菇傘', s.form);
  if (2 * M + 2 - G <= 100) { s = go(mk(M + 1, M + 2 - G), 90); ok(s.form === 'soft' && !evOf(s).b5.ok, `最高 ${M + 1}%（燦光唔合）＋差 ${G - 1}pt（新 5 條唔成立）→ 照次序落柔光（CQ 90）`, s.form); }
  s = go({ feed: 50, play: 50 }, 90); ok(s.form === 'soft' && evOf(s).b5.tie, '50／50 平手＋CQ 90 → 柔光（照次序）', s.form);
  s = go({}, 90); ok(s.form === 'bright', '冇照顧紀錄＋CQ 90 → 燦光', s.form);
}

console.log('# ⑤ 靜光：每條支線一個樣');
{
  const still = D.BRANCHES.map(b => D.evoForm('elder', b)), guard = D.BRANCHES.map(b => D.evoForm('adult', b));
  ok(new Set(still).size === 9 && still.every(k => D.FORMS[k] && D.FORMS[k].evo), '9 條支線 → 9 個唔同靜光 form', still.join());
  ok(new Set(guard).size === 9, '9 條支線 → 9 個唔同守夜者 form');
  for (const b of D.BRANCH5) ok(D.evoForm('adult', b) === 'evo_guard_' + b && D.evoForm('elder', b) === 'evo_still_' + b && fs.existsSync(path.join(__dirname, '../art/evo6/atlas_evo_still_' + b + '.png')), `${D.FORM_NAME[b]} → evo_guard_${b}／evo_still_${b}（有圖）`);
  for (const b of D.BRANCH5) { const s = toAdult(build(b === 'moon' ? { feed: 5, play: 5 } : { [KIND[b]]: 10 }, { h: b === 'moon' ? MH2 : DAY, clean: 100 }), C.b5CQ); ok(s.form === b, `跳跳期完 → ${D.FORM_NAME[b]}`, s.form); s.growthSec = P.stageSec.adult - 1; S.step(s, 5, {}); ok(s.stage === 'elder' && s.form === b && D.evoForm(s.stage, s.form) === 'evo_still_' + b, `${D.FORM_NAME[b]} 成年 → 靜光仍係 ${b}`); }
  for (const b of D.BRANCH5) { const s = pet('elder'); s.form = b; const t = S.deserialize(S.serialize(s), 1e12); ok(t && t.form === b, `存檔來回保留 ${b}`, t && t.form); }
}

console.log('# ⑥ DEV：強制去某支線（9 條）');
{
  for (const b of D.BRANCHES) { const s = build({ feed: 10, play: 2 }); s.evo.force = b; toAdult(s, 30); ok(s.form === b && evOf(s).why === 'dev' && !s.evo.force, `強制 ${D.FORM_NAME[b]} → 跳跳期完去 ${b}（用完清走）`, s.form); }
  { const s = build({ feed: 3 }); s.evo.force = 'nope'; toAdult(s, C.softCQ - 1); ok(s.form === 'dust', '亂嘢強制值唔理'); }
  const dp = fs.readFileSync(path.join(__dirname, '../src/devpanel.js'), 'utf8');
  ok(/data-testid="dev-force-row"/.test(dp) && /D\.BRANCHES\.map\(f => btn\(.*'forceBranch:' \+ f, 'dev-force-' \+ f\)/.test(dp) && /forceBranch\(f\)/.test(dp), 'devpanel：強制支線一行（D.BRANCHES 9 個掣 dev-force-<id>）＋ api.forceBranch');
  const mj = fs.readFileSync(path.join(__dirname, '../src/main.js'), 'utf8');
  ok(/D\.BRANCHES\.includes\(branch\)/.test(mj) && /notePetSleep/.test(mj) && /setRainFn\(\(\) => G\.weather === 'rain'\)/.test(mj), 'main：setStage 收 9 條、瞓覺撫摸掛月眠、落雨＝G.weather');
}

console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
