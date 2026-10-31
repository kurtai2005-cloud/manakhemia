/* §7 新支線 ×5（tide／shroom／crystal／moon／ember）Node 無依賴測試：node tests/branches5.test.js
   覆蓋：① 判定次序 ② 門檻（CQ／最高分；v3 差 < drawGapPt → seed 比例抽）③ 分數來源（芽崽＋跳跳期）④ 時段規則（21–03 只計月眠、06–09 只計水珠）＋落雨
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
let HOUR = DAY, WX = 'clear';
S.setHourFn(() => HOUR); S.setWeatherFn(() => WX);   // v4 天氣：clear／overcast／rain
let ROLL = {};                                                                        // v3：注入判定隨機數（tag → 0–1）；冇 → 用 seed
S.setBranchRoll((tag) => (tag in ROLL ? ROLL[tag] : null));
const KIND = { shroom: 'feed', ember: 'play', tide: 'rinse', crystal: 'poopQuick' };   // v5：晶角只計即清便便
function pet(stage) { const s = S.newState(1e12, 7); s.stage = stage || 'sprout'; Object.assign(s.needs, { hunger: 60, mood: 60, clean: 90, energy: 80 }); return s; }
function setClean(s, avg, st) { const E = s.evo || (s.evo = { evIn: {}, care: {} }); E.cl = E.cl || {}; E.cl[st || 'sprout'] = { sum: avg * 1e6, sec: 1e6 }; }
// counts：{ feed:n, play:n, rinse:n, poop:n, mg:n }（中午、冇雨，用 noteCare）
function build(counts, o) {
  o = o || {}; const s = pet(o.stage || 'sprout'); HOUR = o.h == null ? DAY : o.h; WX = o.wx || (o.rain ? 'rain' : 'clear');
  for (const k in counts) for (let i = 0; i < counts[k]; i++) S.noteCare(s, null, k === 'poop' ? 'poopQuick' : k);   // v5：counts.poop＝即清便便
  setClean(s, o.clean == null ? LOWCLEAN : o.clean); HOUR = DAY; WX = 'clear'; return s;
}
function toAdult(s, cq) { s.stage = 'juvenile'; s.cq = cq; s.growthSec = P.stageSec.juvenile - 1; HOUR = DAY; WX = 'clear'; S.step(s, 5, {}); return s; }
// 百分比 → 次數（總數 100）：菇傘 top%、火苗 second%，其餘用「清潔唔夠嘅清便便」填（入總數但唔計分）
const mk = (top, second) => ({ feed: top, play: second, poop: 100 - top - second });
const baseForm = (cq) => cq >= C.softCQ ? 'soft' : 'dust';   // 燦光／新 5 條都唔成立時
const evOf = (s) => s.ev.find(e => e.type === 'evolve') || {};

console.log('# 資料：9 條支線、config（PARAMS.evo6.branch）');
ok(D.BRANCH5.join() === 'tide,shroom,crystal,moon,ember', 'BRANCH5 = tide／shroom／crystal／moon／ember');
ok(D.BRANCHES.length === 9 && D.BRANCHES[0] === 'lumi' && D.BRANCHES.slice(-3).join() === 'bright,soft,dust', 'BRANCHES 9 條（螢絨＋新 5＋燦光／柔光／微塵）');
ok(['brightCQ', 'brightMaxTopPct', 'b5CQ', 'b5TopPct', 'drawGapPt', 'softCQ', 'crystalCleanAvg'].every(k => Number.isInteger(C[k])) && C.brightCQ > C.softCQ && C.b5TopPct < C.brightMaxTopPct
  && C.windows.every(w => Number.isInteger(w.from) && Number.isInteger(w.to) && D.BRANCH5.includes(w.only)) && MOON.only === 'moon' && DEW.only === 'tide',
  'config 齊（整數門檻＋時段 windows：moon→月眠、dew→水珠）', JSON.stringify(C));
ok(C.lumi && ['fromPct', 'toPct', 'maxChancePct', 'minCQ'].every(k => Number.isFinite(C.lumi[k])) && C.lumi.toPct > C.lumi.fromPct && C.cq && ['careGain', 'careGainPerHourMax', 'partialMax', 'decayAfterH', 'decayPerH', 'floor'].every(k => Number.isFinite(C.cq[k])),
  'config v3：drawGapPt、lumi（機率）、cq（部分照顧＋衰減）', JSON.stringify({ d: C.drawGapPt, l: C.lumi, q: C.cq }));
ok(!('lumiCQ' in EV6) && !('lumiNightShare' in EV6) && !('b5GapPt' in C), '舊螢絨門檻（lumiCQ／lumiNightShare）同 b5GapPt 已移除');
ok(C.systems && C.systems.enabled === false && C.systems.maxRouteSharePct === 25 && C.systems.stardustDailyCap === 30 && Object.keys(C.systems.sources).length === 0, 'config 預留 systems（systems12-v1：每路線新系統分 ≤25%、星星碎每日 30；未用）', JSON.stringify(C.systems));
{ const a = (() => { const s = S.newState(1e12, 1); s.stage = 'sprout'; S.noteCare(s, null, 'feed'); s.cq = 80; return JSON.stringify(S.branch5Check(s)); })();
  const keep = C.systems.enabled; C.systems.enabled = true; C.systems.sources = { x: { route: 'moon', pts: 99 } };
  const b = (() => { const s = S.newState(1e12, 1); s.stage = 'sprout'; S.noteCare(s, null, 'feed'); s.cq = 80; return JSON.stringify(S.branch5Check(s)); })();
  C.systems.enabled = keep; C.systems.sources = {}; ok(a === b, 'systems 預留未接入判定（開咗都唔影響分數）'); }
ok(!('b5CQ' in EV6) && !('branchBright' in P) && !('branchSoft' in P), '舊散落門檻（evo6.b5*、branchBright／Soft）已收入 config');
{ const src = fs.readFileSync(path.join(__dirname, '../src/sim.js'), 'utf8').replace(/\/\/.*$/gm, '');
  const fn = (n) => (src.match(new RegExp('function ' + n + '\\([^]*?\\n  }')) || [''])[0];
  ok(['decideBranch', 'openBranch', 'branch5Check', 'noteB5', 'decideForm'].every(n => fn(n) && !/[^\w.](?:[2-9]\d|1\d\d)\b/.test(fn(n).replace(/\* 100/g, ''))), 'sim 判定函數冇寫死門檻數字（全部讀 config）'); }
ok(['水珠', '菇傘', '晶角', '月眠', '火苗'].every((n, i) => D.FORM_NAME[D.BRANCH5[i]] === n), 'FORM_NAME 水珠／菇傘／晶角／月眠／火苗');
console.log(`  · config：燦光 CQ ≥${C.brightCQ} 且最高 <${C.brightMaxTopPct}%；新 5 條 CQ ≥${C.b5CQ}／≥${C.b5TopPct}%／差 <${C.drawGapPt}pt 比例抽；柔光 CQ ≥${C.softCQ}；晶角清潔 ≥${C.crystalCleanAvg}；時段 ${C.windows.map(w => w.id + ' ' + w.from + '–' + w.to + '→' + w.only).join('、')}`);

console.log('# ① 判定次序（§7 修訂）：螢絨 → 燦光（最高分 < 上限）→ 新 5 條 → 柔光 → 微塵');
{
  const hi = Math.max(C.brightCQ, C.b5CQ, C.lumi.minCQ) + 10;
  // 符合螢絨（夜晚照顧 ≥40%＋螢火散步＋CQ）同時又符合新 5 條 → 螢絨
  const s = build({ feed: 10, play: 2 }, { h: MH2 }); s.evo.evIn.juvenile = { [EV6.lumiEvent]: 1 };
  ok(S.branch5Check(Object.assign(pet(), { evo: JSON.parse(JSON.stringify(s.evo)), cq: hi })).ok, '（前提）新 5 條本身成立');
  const s0 = JSON.parse(JSON.stringify(s)); ROLL.lumi = 0; toAdult(s, hi); ok(s.form === 'lumi' && evOf(s).why === 'lumi', '螢絨（抽中）優先過新 5 條', s.form);
  ROLL.lumi = 0.999; toAdult(s0, hi); ok(s0.form === 'moon' && evOf(s0).lumi.chance > 0 && !evOf(s0).lumi.ok, '螢絨有資格但抽唔中 → 照落新 5 條（夜晚 → 月眠）', s0.form); delete ROLL.lumi;
  const t = toAdult(build({ feed: 10, play: 2 }), hi); ok(t.form === 'shroom' && evOf(t).why === 'b5', `專注（菇傘 83% ≥ ${C.brightMaxTopPct}%）＋CQ ${hi} → 新 5 條（菇傘）唔係燦光`, t.form);
  const flat = { feed: 3, play: 3, rinse: 3 };   // 三條平手（33%）：v3 → 新 5 條會喺頭兩名之間抽
  for (const cq of [100, C.brightCQ, C.brightCQ - 1, C.b5CQ, C.softCQ, C.softCQ - 1]) {
    const u = toAdult(build(flat), cq), B = evOf(u).b5, f = cq >= C.brightCQ ? 'bright' : cq >= C.b5CQ ? B.form : baseForm(cq);
    ok(u.form === f && (cq >= C.b5CQ && cq < C.brightCQ ? evOf(u).why === 'b5' && !!B.draw && ['feed', 'play', 'rinse'].map(k => ({ feed: 'shroom', play: 'ember', rinse: 'tide' })[k]).includes(f) : evOf(u).why === 'cq'), `全面照顧（平手 33%）→ CQ ${cq} → ${D.FORM_NAME[f] || f}`, u.form);
  }
  const lumiOnly = build(flat, { h: 18 }); lumiOnly.evo.evIn.sprout = { [EV6.lumiEvent]: 2 }; ROLL.lumi = 0; toAdult(lumiOnly, C.lumi.minCQ); delete ROLL.lumi;
  ok(lumiOnly.form === 'lumi', `螢絨（CQ ${C.lumi.minCQ}＋夜晚 100%＋抽中）→ 螢絨`, lumiOnly.form);
}

console.log(`# ② 新 5 條門檻：CQ ≥${C.b5CQ}、最高 ≥${C.b5TopPct}%；v3：差 <${C.drawGapPt}pt（包括平手）→ 兩者分數比例抽（seed）`);
{
  const T = C.b5TopPct, G = C.drawGapPt, c = (counts, cq, o) => { const s = build(counts, o); s.cq = cq; return S.branch5Check(s); };
  ok(!c(mk(T, T - G), C.b5CQ - 1).ok && c(mk(T, T - G), C.b5CQ).ok, `CQ ${C.b5CQ - 1} ✗／${C.b5CQ} ✓`);
  { const q = C.b5CQ - 1, f = q >= C.brightCQ && T < C.brightMaxTopPct ? 'bright' : baseForm(q); ok(toAdult(build(mk(T, T - G)), q).form === f, `CQ ${q} → ${D.FORM_NAME[f]}（唔去新支線；v4 燦光門檻 ${C.brightCQ} 低過新支線）`); }
  let r = c(mk(T, T - G), C.b5CQ);
  ok(r.ok && r.form === 'shroom' && Math.round(r.topShare * 100) === T && Math.round(r.secondShare * 100) === T - G, `最高 = ${T}%、差 = ${G}pt（啱啱好）→ 成立`, JSON.stringify(r.score));
  r = c(mk(T - 1, T - 1 - G), C.b5CQ); ok(!r.ok && !r.topOk && r.top === 'shroom', `最高 ${T - 1}% → 唔成立`, r.topShare);
  ok(!r.draw, `差 = ${G}pt → 唔抽（最高分贏）`);
  { const pT = T / (2 * T - G + 1);
    ROLL.b5draw = pT - 0.001; r = c(mk(T, T - G + 1), C.b5CQ); ok(r.ok && !r.gapOk && r.draw && r.form === 'shroom' && Math.abs(r.draw.pTop - pT) < 1e-3, `差 ${G - 1}pt → 抽：roll < ${pT.toFixed(3)} → 第一名（菇傘）`, JSON.stringify(r.draw));
    ROLL.b5draw = pT + 0.001; r = c(mk(T, T - G + 1), C.b5CQ); ok(r.ok && r.form === 'ember', `差 ${G - 1}pt → roll ≥ ${pT.toFixed(3)} → 第二名（火苗）`, r.form); delete ROLL.b5draw; }
  r = c(mk(T, T), 90); ok(r.ok && r.tie && r.draw && r.draw.pTop === 0.5 && [r.draw.a, r.draw.b].sort().join() === 'ember,shroom' && r.form === (r.draw.roll < 0.5 ? r.draw.a : r.draw.b), `平手（${T}／${T}）→ 50／50 抽`, JSON.stringify(r.draw));
  { // seed 決定：同一隻寵物重複判都一樣；唔同 seed 大致按比例
    const one = (seed) => { const s = build(mk(T, T - G + 1)); s.seed = seed; s.cq = C.b5CQ; return S.branch5Check(s).form; };
    ok([1, 2, 3].every(() => one(42) === one(42)), 'seed 一樣 → 抽嘅結果一樣（可重現）');
    const N = 400; let top = 0; for (let i = 1; i <= N; i++) if (one(i * 7919) === 'shroom') top++;
    const pT = T / (2 * T - G + 1); ok(Math.abs(top / N - pT) < 0.08, `唔同 seed：第一名機率 ≈ ${pT.toFixed(2)}（實際 ${(top / N).toFixed(2)}）`); }
  r = c(mk(T - G, T - G - 1), C.b5CQ); ok(!r.ok && !r.topOk, `抽都要最高 ≥ ${T}%（${T - G}% → 唔成立）`);
  ok(toAdult(build(mk(T, T)), 90).form === (T < C.brightMaxTopPct ? 'bright' : 'soft'), '平手 → 照次序（最高 < 上限 → 燦光）');
  ok(toAdult(build({}), 90).form === 'soft' && !S.branch5Check(build({})).ok, '冇照顧（總數 0）→ 冇照顧日 → 唔係燦光 → 柔光（CQ 90；v4）');
}

console.log('# ③ 分數來源（只計芽崽＋跳跳期）');
{
  const cq = C.b5CQ;
  for (const [b, k] of Object.entries(KIND)) {
    const s = build(b === 'ember' ? { play: 10, feed: 1 } : { [k]: 10, play: 1 }, { clean: 100 }); s.cq = cq; const r = S.branch5Check(s);
    ok(r.form === b, `${k} → ${D.FORM_NAME[b]}`, JSON.stringify(r.score));
  }
  { const s = build({ mg: 6, play: 4, feed: 3 }); s.cq = cq; ok(S.branch5Check(s).score.ember === 10 && S.branch5Check(s).form === 'ember', 'play＋mg → 火苗'); }
  { const s = build({ feed: 3 }, { rain: true }); s.cq = cq; const r = S.branch5Check(s); ok(r.score.tide === 0 && r.score.shroom === 3, '（平時鐘點）落雨時餵食 → 菇傘只計一次、唔計水珠（v4）'); }
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
    const s = pet('sprout'); s.needs.hunger = 10; S.feed(s, 'meal'); S.play(s); S.rinse(s); s.poops = 1; s.poopAge = [0]; S.clearPoop(s); S.mgApply(s, 10, 1e12);   // v5：啱啱出嘅便便＝即清
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
  { const s = build({ play: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 0 && b.shroom === 1 && b.ember === 1 && b.all === 1, '平時落雨玩 → 菇傘 +1、火苗 +1、水珠 0（v4）'); }
  { const s = build({}); HOUR = MH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; ok(s.evo.b5.sprout.moon === 1, `${MH}:00 瞓覺撫摸 → 月眠只 +1`); }
  { const s = build({}); HOUR = DH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; const b = s.evo.b5.sprout; ok(b.moon === 1 && b.tide === 0, `${DH}:00 瞓覺撫摸 → 仍然計月眠（唔係水珠）`, JSON.stringify(b)); }
  // 夜晚淫餵 → 月眠
  { const s = build({ feed: 10 }, { h: MH2 }); s.cq = C.b5CQ; const r = S.branch5Check(s); ok(r.ok && r.form === 'moon' && r.score.shroom === 0 && r.score.moon === 10, '夜晚淨係餵 → 月眠 100%（菇傘唔計）', JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 12, play: 2 }, { h: MH2 }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'moon' && evOf(s).why === 'b5', `夜晚淫餵（${MH2}:00 餵 12 玩 2，高 CQ）→ 月眠（≥ 上限唔去燦光）`, s.form); }
  { const s = build({ feed: 6 }, { h: MH }); HOUR = DAY; for (let i = 0; i < 4; i++) S.noteCare(s, null, 'feed'); s.cq = C.b5CQ; const r = S.branch5Check(s);
    ok(r.score.moon === 6 && r.score.shroom === 4 && r.form === (60 - 40 >= C.drawGapPt && 60 >= C.b5TopPct ? 'moon' : null), '夜晚 6 次＋白天 4 次餵 → 月眠 60%、菇傘 40%'); }
  { const s = build({ feed: 2, play: 8 }, { h: MH2 }); s.cq = C.b5CQ; ok(S.branch5Check(s).form === 'moon', `夜深陪玩（${MH2}:00 玩 8 餵 2）→ 月眠 100%（火苗唔計）`); }
  // 早起玩家 → 水珠
  { const s = build({ feed: 6, play: 4 }, { h: DH }); s.cq = C.b5CQ; const r = S.branch5Check(s); ok(r.form === 'tide' && r.score.tide === 10 && r.score.shroom === 0 && r.score.ember === 0, `晨露：${DH}:00 餵 6 玩 4 → 水珠 100%`, JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 8, play: 4 }, { h: DH }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'tide' && evOf(s).why === 'b5', '早起玩家（晨早照顧為主，高 CQ）→ 水珠', s.form); }
  { const s = build({ poop: 2 }, { h: MH, clean: 100 }); const r = S.branch5Check(s); ok(r.score.crystal === 0 && r.score.moon === 2, `${MH}:00 清便便 → 只計月眠`); }
}

console.log(`# ⑦ 燦光：CQ ≥${C.brightCQ} 且最高分 <${C.brightMaxTopPct}%（全面照顧）先過新 5 條`);
{
  const M = C.brightMaxTopPct, G = C.drawGapPt, hi = Math.max(C.brightCQ, C.b5CQ) + 10, go = (counts, cq, o) => toAdult(build(counts, o), cq);
  let s = go(mk(M - 1, M - 1 - G), hi); ok(s.form === 'bright' && evOf(s).b5.ok && Math.round(evOf(s).b5.topShare * 100) === M - 1, `最高 ${M - 1}%（新 5 條本身成立）＋CQ ${hi} → 燦光`, s.form);
  s = go(mk(M, M - G), hi); ok(s.form === 'shroom' && evOf(s).why === 'b5', `最高 ${M}%（啱啱好）＋CQ ${hi} → 菇傘`, s.form);
  s = go({ feed: 9, play: 4, rinse: 4, poop: 3 }, C.brightCQ); ok(s.form === (9 * 100 >= M * 20 ? (C.brightCQ >= C.b5CQ ? 'shroom' : baseForm(C.brightCQ)) : 'bright'), `9/20（45%）＋CQ ${C.brightCQ} → 照上限判（唔係燦光）`, s.form);
  if (C.brightCQ - 1 >= C.b5CQ) { s = go(mk(M - 1, M - 1 - G), C.brightCQ - 1); ok(s.form === 'shroom', `CQ ${C.brightCQ - 1}（唔夠燦光）＋最高 ${M - 1}% → 菇傘`, s.form); }
  s = go(mk(M - 1, M - 1 - G), C.brightCQ); ok(s.form === 'bright', `CQ ${C.brightCQ}（啱啱好）＋最高 ${M - 1}% → 燦光`, s.form);
  s = go({ feed: 8, poop: 2 }, hi, { clean: 100 }); ok(s.form === 'shroom', '清便便都計晶角，但最高係菇傘 80% → 菇傘', s.form);
  if (2 * M + 2 - G <= 100) { ROLL.b5draw = 0.999; s = go(mk(M + 1, M + 2 - G), 90); ok(s.form === 'ember' && evOf(s).b5.draw, `最高 ${M + 1}%（燦光唔合）＋差 ${G - 1}pt → 抽（roll 大 → 第二名火苗）`, s.form); delete ROLL.b5draw; }
  for (const u of [0, 0.999]) { ROLL.b5draw = u; s = go({ feed: 50, play: 50 }, 90); const d = evOf(s).b5.draw; ok(evOf(s).b5.tie && d && s.form === (u < 0.5 ? d.a : d.b), `50／50 平手＋CQ 90 → 抽（roll ${u} → ${s.form}）`, s.form); } delete ROLL.b5draw;
  s = go({}, 90); ok(s.form === 'soft', '冇照顧紀錄＋CQ 90 → 冇照顧日 → 柔光（v4）', s.form);
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
  ok(/D\.BRANCHES\.includes\(branch\)/.test(mj) && /notePetSleep/.test(mj) && /setWeatherFn\(\(\) => G\.weather/.test(mj), 'main：setStage 收 9 條、瞓覺撫摸掛月眠、天氣＝G.weather');
}

console.log('⑧ v4：天氣（陰天／落雨 → 菇傘、落雨唔計水珠）＋燦光連續照顧日（config weather／brightDays）');
{
  const W = C.weather, ST = W.states;
  ok(ST.includes('clear') && ST.includes('overcast') && ST.includes('rain'), '天氣狀態：clear／overcast／rain');
  ok(W.route.overcast.to === 'shroom' && W.route.rain.to === 'shroom' && W.route.overcast.w === 0.5 && W.route.rain.w === 1, 'config：陰天 0.5／落雨 1.0 → 菇傘（v5）');
  WX = 'bogus'; ok(S.weatherNow() === 'clear', '唔識嘅天氣 → clear'); WX = 'overcast'; ok(S.weatherNow() === 'overcast' && !S.isRaining(), 'overcast：weatherNow／isRaining'); WX = 'clear';
  let b = build({ feed: 2 }, { wx: 'overcast' }).evo.b5.sprout; ok(b.shroom === 2 && b.tide === 0, '陰天餵食 → 菇傘只計一次', JSON.stringify(b));
  b = build({ play: 1 }, { wx: 'overcast' }).evo.b5.sprout; ok(b.shroom === W.route.overcast.w && b.ember === 1 && b.all === 1, `陰天玩 → 菇傘 +${W.route.overcast.w}、火苗 +1`, JSON.stringify(b));
  b = build({ play: 2 }, { wx: 'rain' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.rain.w && b.ember === 2, `落雨玩 ×2 → 菇傘 +${2 * W.route.rain.w}`, JSON.stringify(b));
  b = build({ rinse: 1 }, { wx: 'rain' }).evo.b5.sprout; ok(b.tide === 1 && b.shroom === 1, '落雨沖洗 → 水珠（本身）＋菇傘', JSON.stringify(b));
  b = build({ play: 1 }).evo.b5.sprout; ok(!b.shroom && !b.tide, '晴天玩 → 冇菇傘／水珠', JSON.stringify(b));
  b = build({ play: 1, feed: 1 }, { wx: 'rain', h: DH }).evo.b5.sprout; ok(b.tide === 2 && !b.shroom && !b.ember, `${DEW.from}–${DEW.to} 落雨 → 時段規則優先：只計水珠`, JSON.stringify(b));
  b = build({ feed: 1 }, { wx: 'overcast', h: MH }).evo.b5.sprout; ok(b.moon === 1 && !b.shroom, `${MOON.from}–${MOON.to} 陰天 → 只計月眠`, JSON.stringify(b));
  // 照顧日
  const BD = C.brightDays, T0 = new Date(2026, 9, 20, 12).getTime(), dk = (i) => S.dayKey(T0 - i * 86400000);
  S.setNowFn(() => T0);
  const withDays = (s, n, age) => { s.careDays = []; for (let i = 0; i < n; i++) s.careDays.push(dk(i)); s.careDays.sort(); s.evo.day0 = age == null ? dk(30) : dk(age); return s; };
  const bal = { feed: 3, play: 3, rinse: 3, poop: 3 };
  let q = build(bal); ok(q.careDays.includes(dk(0)) && q.evo.day0 === dk(0), 'noteCare 記低今日做照顧日＋day0');
  const sc = BD.scaleToAge; BD.scaleToAge = false;
  let r = S.careDaysCheck(withDays(build(bal), BD.min)); ok(r.ok && r.days === BD.min && r.span === BD.window, `（唔按年齡）最近 ${BD.window} 日有 ${BD.min} 日 → ✓`, JSON.stringify(r));
  r = S.careDaysCheck(withDays(build(bal), BD.min - 1)); ok(!r.ok, `（唔按年齡）${BD.min - 1} 日 → ✗`, JSON.stringify(r));
  BD.scaleToAge = true;
  r = S.careDaysCheck(withDays(build(bal), 30, 3)); const need3 = Math.ceil(BD.min * 4 / BD.window); ok(r.span === 4 && r.need === need3, `（按年齡）出世 4 日 → 要 ${need3}/4 日`, JSON.stringify(r));
  r = S.careDaysCheck(withDays(build(bal), need3, 3)); ok(r.ok, `出世 4 日、${need3} 日有照顧 → ✓`); r = S.careDaysCheck(withDays(build(bal), need3 - 1, 3)); ok(!r.ok, `${need3 - 1} 日 → ✗`);
  r = S.careDaysCheck(withDays(build(bal), BD.min, 30)); ok(r.ok && r.span === BD.window, '出世夠耐 → 用返完整 window');
  BD.scaleToAge = sc;
  // 判定
  ok(toAdult(withDays(build(bal), BD.window), C.brightCQ).form === 'bright', `CQ ${C.brightCQ}＋照顧日夠＋最高分 < ${C.brightMaxTopPct}% → 燦光`);
  ok(toAdult(withDays(build(bal), 1), C.brightCQ + 20).form === 'soft', `照顧日唔夠 → 唔係燦光（CQ ${C.brightCQ + 20} → 柔光）`);
  ok(toAdult(withDays(build(bal), BD.window), C.brightCQ - 1).form === 'soft', `CQ ${C.brightCQ - 1} → 柔光`);
  ok(toAdult(withDays(build(bal), BD.window), C.softCQ).form === 'soft' && toAdult(withDays(build(bal), BD.window), C.softCQ - 1).form === 'dust', `柔光 CQ ≥ ${C.softCQ}；以下微塵`);
  q = withDays(build(bal), BD.window); ok(S.branch5Check(q).ok === false && toAdult(q, C.brightCQ).ev.some(e => e.type === 'evolve' && e.form === 'bright'), '新 5 條唔成立（最高分 25%）→ evolve 燦光');
  S.setNowFn(null);
}
console.log('⑨ v5：晶角即清、月眠 20–03＋哄瞓（每晚 ≤3）、螢絨 CQ 25');
{
  const Q = C.crystalQuickSec, L = C.lull;
  ok(MOON.from === 20 && MOON.to === 3, `月眠時段 ${MOON.from}:00–0${MOON.to}:00`);
  { const b = build({ feed: 1, play: 1 }, { h: 20 }).evo.b5.sprout; ok(b.moon === 2 && !b.shroom && !b.ember, '20:00 照顧 → 只計月眠'); }
  ok(C.lumi.minCQ === 25, '螢絨 minCQ 25');
  // 即清：用 step 令便便老化
  const poopIn = (age) => { const s = pet('sprout'); s.poops = 1; s.poopAge = [0]; HOUR = DAY; if (age) S.step(s, age, {}); s.poops = Math.max(1, s.poops); const a = S.poopAges(s); a[a.length - 1] = Math.min(a[a.length - 1], age); S.clearPoop(s); return s.evo.b5.sprout; };
  let b = poopIn(Q - 1); ok(b.crystal === 1 && b.all === 1, `便便出咗 ${Q - 1}s 清 → 晶角 +1`, JSON.stringify(b));
  b = poopIn(Q); ok(b.crystal === 1, `${Q}s（啱啱好）→ 晶角 +1`, JSON.stringify(b));
  b = poopIn(Q + 1); ok(!b.crystal && b.all === 1, `${Q + 1}s 先清 → 唔計晶角（只計總數）`, JSON.stringify(b));
  { const s = pet('sprout'); s.poops = 2; ok(S.poopAges(s).every(x => x >= 1e9), '舊存檔便便（冇時間）→ 當舊便便'); S.clearPoop(s); ok(!s.evo.b5.sprout.crystal, '舊便便清 → 唔計晶角'); }
  { const s = pet('sprout'); s.poops = 0; s.poopAge = []; s.poopTimer = 1e9; S.step(s, 1, {}); const n = s.poops; ok(n >= 1 && S.poopAges(s).length === n && S.poopAges(s)[n - 1] <= 1, 'step 出便便 → 記低 age 0', JSON.stringify([n, s.poopAge])); S.clearPoop(s); ok(s.evo.b5.sprout.crystal === 1, '啱啱出嘅便便即清 → 晶角'); }
  // 哄瞓
  const T0 = new Date(2026, 9, 20, 22).getTime(); let T = T0; S.setNowFn(() => T);
  const drowsy = (s) => { s.sleeping = false; s.needs.energy = L.drowsyEnergy - 5; return s; };
  let s = pet('sprout'); s.needs.energy = L.drowsyEnergy; ok(!S.isDrowsy(s) && !S.lullSleep(s).ok, `精力 ${L.drowsyEnergy} → 唔眼瞓、哄唔到`);
  drowsy(s); ok(S.isDrowsy(s), `精力 ${L.drowsyEnergy - 5} → 眼瞓`);
  let r = S.lullSleep(s, DAY); ok(r.ok && r.counted && s.sleeping && s.evo.b5.sprout.moon === 1 && s.ev.some(e => e.type === 'lull'), '哄瞓 → 瞓著＋月眠 +1（任何鐘點）', JSON.stringify(r));
  ok(!S.lullSleep(s).ok, '瞓緊 → 唔使再哄');
  for (let i = 1; i < L.perNight + 2; i++) { T = T0 + i * 3600e3; drowsy(s); r = S.lullSleep(s, DAY); }
  ok(s.evo.b5.sprout.moon === L.perNight && r.ok && !r.counted && s.sleeping, `同一晚哄 ${L.perNight + 2} 次 → 月眠只計 ${L.perNight}（照瞓）`, JSON.stringify([s.evo.b5.sprout, r]));
  T = T0 + 24 * 3600e3; drowsy(s); r = S.lullSleep(s, DAY); ok(r.counted && s.evo.b5.sprout.moon === L.perNight + 1, '第二晚 → 重新計', JSON.stringify(r));
  { const e = pet('egg'); e.needs.energy = 1; ok(!S.isDrowsy(e) && !S.lullSleep(e).ok, '光卵 → 唔得'); }
  S.setNowFn(null);
}
console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
