/* §7 新支線 ×5（tide／shroom／crystal／moon／ember）Node 無依賴測試：node tests/branches5.test.js
   覆蓋：① 判定次序 ② 門檻（CQ／最高分；v3 差 < drawGapPt → seed 比例抽）③ 分數來源（芽崽＋跳跳期）④ 時段規則（21–03 只計月眠、06–09 只計水珠）＋落雨
         ⑦ 燦光最高分上限 ⑤ 靜光對應 ⑥ DEV 強制支線
   ⑩ v8–v10：菇傘權重（晴 0／陰霧 0.5／雨 1；淨係餵唔入菇傘）、火苗（玩 +1、小遊戲 +2、浮動團絨開 game＝一局）、哄瞓 +2、新 5 條 CQ max(scaleToAge(25),18.5)、晶角上線即清
   所有門檻／時段都讀 PARAMS.evo6.branch（config）；改 config 唔使改測試。
   v8 起餵食本身唔計菇傘：counts.feed＝「一次菇傘照顧」＝落雨餵（落雨 1.0）；指定 o.wx 就全部照顧用嗰個天氣。counts.poop＝普通清便便（只入總數）；晶角用 setLogin（v7）。 */
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
const LOWCLEAN = 50;                                                                 // v7 清潔度唔再影響晶角（只係報告值）
let HOUR = DAY, WX = 'clear';
S.setHourFn(() => HOUR); S.setWeatherFn(() => WX);   // v4 天氣：clear／overcast／rain
let ROLL = {};                                                                        // v3：注入判定隨機數（tag → 0–1）；冇 → 用 seed
S.setBranchRoll((tag) => (tag in ROLL ? ROLL[tag] : null));
const KIND = { shroom: 'feed', ember: 'play', tide: 'rinse', crystal: 'poop' };   // 晶角：poop＋setLogin（v7）
function pet(stage) { const s = S.newState(1e12, 7); s.stage = stage || 'sprout'; Object.assign(s.needs, { hunger: 60, mood: 60, clean: 90, energy: 80 }); return s; }
// v7 晶角：直接寫上線統計（有便便上線 nWith、即清上線 nQuick）
function setLogin(s, nWith, nQuick, st) { const B = s.evo.b5 || (s.evo.b5 = {}), b = B[st || 'sprout'] || (B[st || 'sprout'] = { all: 0, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 0 }); b.loginPoop = nWith; b.quickLogin = nQuick == null ? nWith : nQuick; return s; }
const crystalPts = (s, st) => { const b = s.evo.b5[st || 'sprout']; return b.loginPoop ? b.quickLogin / b.loginPoop * C.crystal.k * b.all : 0; };
function setClean(s, avg, st) { const E = s.evo || (s.evo = { evIn: {}, care: {} }); E.cl = E.cl || {}; E.cl[st || 'sprout'] = { sum: avg * 1e6, sec: 1e6 }; }
// counts：{ feed:n, play:n, rinse:n, poop:n, mg:n }（中午、冇雨，用 noteCare）
function build(counts, o) {
  o = o || {}; const s = pet(o.stage || 'sprout'); HOUR = o.h == null ? DAY : o.h; WX = o.wx || (o.rain ? 'rain' : 'clear');
  const wx0 = WX;
  const RW = C.weather.route.rain, rw0 = RW.w;   // v10.3：落雨權重 0.8；fixture 嘅 feed 係「1 單位菇傘照顧」→ 呢度暫時當 1（只限 fixture，比例測試唔受權重影響）
  for (const k in counts) for (let i = 0; i < counts[k]; i++) { const fx = k === 'feed' && !o.wx && !o.rain && !o.clearFeed; WX = fx ? 'rain' : wx0; if (fx) RW.w = 1; try { S.noteCare(s, null, k); } finally { RW.w = rw0; } }   // v8：feed＝落雨餵（菇傘 +1 單位）
  setClean(s, o.clean == null ? LOWCLEAN : o.clean); HOUR = DAY; WX = 'clear'; return s;
}
function toAdult(s, cq) { s.stage = 'juvenile'; s.cq = cq; s.growthSec = P.stageSec.juvenile - 1; HOUR = DAY; WX = 'clear'; S.step(s, 5, {}); return s; }
// 百分比 → 次數（總數 100）：菇傘 top%、火苗 second%，其餘用「清潔唔夠嘅清便便」填（入總數但唔計分）
const mk = (top, second) => ({ feed: top, play: second, poop: 100 - top - second });
const baseForm = (cq) => cq >= C.softCQ ? 'soft' : 'dust';   // 燦光／新 5 條都唔成立時
const evOf = (s) => s.ev.find(e => e.type === 'evolve') || {};
const NEED = S.b5Need(build({ feed: 1 }));   // build() 嘅寵物今日出世（span 1）→ v10 門檻＝max(scaleToAge(b5CQ), b5CQFloor)

console.log('# 資料：9 條支線、config（PARAMS.evo6.branch）');
ok(D.BRANCH5.join() === 'tide,shroom,crystal,moon,ember', 'BRANCH5 = tide／shroom／crystal／moon／ember');
ok(D.BRANCHES.length === 9 && D.BRANCHES[0] === 'lumi' && D.BRANCHES.slice(-3).join() === 'bright,soft,dust', 'BRANCHES 9 條（螢絨＋新 5＋燦光／柔光／微塵）');
ok(['brightCQ', 'brightMaxTopPct', 'b5CQ', 'b5TopPct', 'drawGapPt', 'softCQ'].every(k => Number.isInteger(C[k])) && Number.isFinite(C.b5CQFloor) && typeof C.b5CQScaleToAge === 'boolean'
  && ['windowSec', 'k', 'loginGapSec'].every(k => Number.isFinite(C.crystal[k])) && !('crystalCleanAvg' in C) && !('crystalQuickSec' in C) && C.brightCQ > C.softCQ && C.b5TopPct < C.brightMaxTopPct
  && C.windows.every(w => Number.isInteger(w.from) && Number.isInteger(w.to) && D.BRANCH5.includes(w.only)) && MOON.only === 'moon' && DEW.only === 'tide',
  'config 齊（整數門檻＋時段 windows：moon→月眠、dew→水珠）', JSON.stringify(C));
ok(C.lumi && ['fromPct', 'toPct', 'maxChancePct', 'minCQ'].every(k => Number.isFinite(C.lumi[k])) && C.lumi.toPct > C.lumi.fromPct && C.cq && ['careGain', 'careGainPerHourMax', 'partialMax', 'decayAfterH', 'decayPerH', 'floor'].every(k => Number.isFinite(C.cq[k])),
  'config v3：drawGapPt、lumi（機率）、cq（部分照顧＋衰減）', JSON.stringify({ d: C.drawGapPt, l: C.lumi, q: C.cq }));
ok(!('lumiCQ' in EV6) && !('lumiNightShare' in EV6) && !('b5GapPt' in C), '舊螢絨門檻（lumiCQ／lumiNightShare）同 b5GapPt 已移除');
ok(C.systems && C.systems.enabled === true && C.systems.maxRouteSharePct === 25 && C.systems.stardustDailyCap === 30 && C.systems.sources.questRoute && C.systems.sources.questRoute.pts === 1, 'config systems（systems12-v1 第 1 批：每路線新系統分 ≤25%、星星碎每日 30；委託路線分 1）', JSON.stringify(C.systems));
{ const a = (() => { const s = S.newState(1e12, 1); s.stage = 'sprout'; S.noteCare(s, null, 'feed'); s.cq = 80; return JSON.stringify(S.branch5Check(s)); })();
  const keep = C.systems.enabled, keepS = C.systems.sources; C.systems.enabled = true; C.systems.sources = { x: { route: 'moon', pts: 99 } };
  const b = (() => { const s = S.newState(1e12, 1); s.stage = 'sprout'; S.noteCare(s, null, 'feed'); s.cq = 80; return JSON.stringify(S.branch5Check(s)); })();
  C.systems.enabled = keep; C.systems.sources = keepS; ok(a === b, '冇新系統分（E.b5sys）→ 判定同舊版一樣（config sources 本身唔加分）'); }
ok(!('b5CQ' in EV6) && !('branchBright' in P) && !('branchSoft' in P), '舊散落門檻（evo6.b5*、branchBright／Soft）已收入 config');
{ const src = fs.readFileSync(path.join(__dirname, '../src/sim.js'), 'utf8').replace(/\/\/.*$/gm, '');
  const fn = (n) => (src.match(new RegExp('function ' + n + '\\([^]*?\\n  }')) || [''])[0];
  ok(['decideBranch', 'openBranch', 'branch5Check', 'noteB5', 'decideForm'].every(n => fn(n) && !/[^\w.](?:[2-9]\d|1\d\d)\b/.test(fn(n).replace(/\* 100/g, ''))), 'sim 判定函數冇寫死門檻數字（全部讀 config）'); }
ok(['水珠', '菇傘', '晶角', '月眠', '火苗'].every((n, i) => D.FORM_NAME[D.BRANCH5[i]] === n), 'FORM_NAME 水珠／菇傘／晶角／月眠／火苗');
console.log(`  · config：燦光 CQ ≥${C.brightCQ} 且最高 <${C.brightMaxTopPct}%；新 5 條 CQ ≥${C.b5CQ}／≥${C.b5TopPct}%／差 <${C.drawGapPt}pt 比例抽；柔光 CQ ≥${C.softCQ}；晶角 上線 ${C.crystal.windowSec}s 即清×${C.crystal.k}；新 5 條門檻（今日出世）${NEED}；時段 ${C.windows.map(w => w.id + ' ' + w.from + '–' + w.to + '→' + w.only).join('、')}`);

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
  for (const cq of [100, C.brightCQ, C.brightCQ - 1, NEED, C.softCQ, C.softCQ - 1]) {
    const u = toAdult(build(flat), cq), B = evOf(u).b5, f = cq >= C.brightCQ ? 'bright' : cq >= NEED ? B.form : baseForm(cq);
    ok(u.form === f && (cq >= NEED && cq < C.brightCQ ? evOf(u).why === 'b5' && !!B.draw && ['feed', 'play', 'rinse'].map(k => ({ feed: 'shroom', play: 'ember', rinse: 'tide' })[k]).includes(f) : evOf(u).why === 'cq'), `全面照顧（平手 33%）→ CQ ${cq} → ${D.FORM_NAME[f] || f}`, u.form);
  }
  const lumiOnly = build(flat, { h: 18 }); lumiOnly.evo.evIn.sprout = { [EV6.lumiEvent]: 2 }; ROLL.lumi = 0; toAdult(lumiOnly, C.lumi.minCQ); delete ROLL.lumi;
  ok(lumiOnly.form === 'lumi', `螢絨（CQ ${C.lumi.minCQ}＋夜晚 100%＋抽中）→ 螢絨`, lumiOnly.form);
}

console.log(`# ② 新 5 條門檻：CQ ≥${NEED}（v10 今日出世）、最高 ≥${C.b5TopPct}%；v3：差 <${C.drawGapPt}pt（包括平手）→ 兩者分數比例抽（seed）`);
{
  const T = C.b5TopPct, G = C.drawGapPt, c = (counts, cq, o) => { const s = build(counts, o); s.cq = cq; return S.branch5Check(s); };
  ok(!c(mk(T, T - G), NEED - 0.5).ok && c(mk(T, T - G), NEED).ok, `CQ ${NEED - 0.5} ✗／${NEED} ✓`);
  { const q = NEED - 0.5, f = q >= C.brightCQ && T < C.brightMaxTopPct ? 'bright' : baseForm(q); ok(toAdult(build(mk(T, T - G)), q).form === f, `CQ ${q} → ${D.FORM_NAME[f]}（唔去新支線；v4 燦光門檻 ${C.brightCQ} 低過新支線）`); }
  let r = c(mk(T, T - G), NEED);
  ok(r.ok && r.form === 'shroom' && Math.round(r.topShare * 100) === T && Math.round(r.secondShare * 100) === T - G, `最高 = ${T}%、差 = ${G}pt（啱啱好）→ 成立`, JSON.stringify(r.score));
  r = c(mk(T - 1, T - 1 - G), NEED); ok(!r.ok && !r.topOk && r.top === 'shroom', `最高 ${T - 1}% → 唔成立`, r.topShare);
  ok(!r.draw, `差 = ${G}pt → 唔抽（最高分贏）`);
  { const pT = T / (2 * T - G + 1);
    ROLL.b5draw = pT - 0.001; r = c(mk(T, T - G + 1), NEED); ok(r.ok && !r.gapOk && r.draw && r.form === 'shroom' && Math.abs(r.draw.pTop - pT) < 1e-3, `差 ${G - 1}pt → 抽：roll < ${pT.toFixed(3)} → 第一名（菇傘）`, JSON.stringify(r.draw));
    ROLL.b5draw = pT + 0.001; r = c(mk(T, T - G + 1), NEED); ok(r.ok && r.form === 'ember', `差 ${G - 1}pt → roll ≥ ${pT.toFixed(3)} → 第二名（火苗）`, r.form); delete ROLL.b5draw; }
  r = c(mk(T, T), 90); ok(r.ok && r.tie && r.draw && r.draw.pTop === 0.5 && [r.draw.a, r.draw.b].sort().join() === 'ember,shroom' && r.form === (r.draw.roll < 0.5 ? r.draw.a : r.draw.b), `平手（${T}／${T}）→ 50／50 抽`, JSON.stringify(r.draw));
  { // seed 決定：同一隻寵物重複判都一樣；唔同 seed 大致按比例
    const one = (seed) => { const s = build(mk(T, T - G + 1)); s.seed = seed; s.cq = NEED; return S.branch5Check(s).form; };
    ok([1, 2, 3].every(() => one(42) === one(42)), 'seed 一樣 → 抽嘅結果一樣（可重現）');
    const N = 400; let top = 0; for (let i = 1; i <= N; i++) if (one(i * 7919) === 'shroom') top++;
    const pT = T / (2 * T - G + 1); ok(Math.abs(top / N - pT) < 0.08, `唔同 seed：第一名機率 ≈ ${pT.toFixed(2)}（實際 ${(top / N).toFixed(2)}）`); }
  r = c(mk(T - G, T - G - 1), NEED); ok(!r.ok && !r.topOk, `抽都要最高 ≥ ${T}%（${T - G}% → 唔成立）`);
  ok(toAdult(build(mk(T, T)), 90).form === (T < C.brightMaxTopPct ? 'bright' : 'soft'), '平手 → 照次序（最高 < 上限 → 燦光）');
  ok(toAdult(build({}), 90).form === 'soft' && !S.branch5Check(build({})).ok, '冇照顧（總數 0）→ 冇照顧日 → 唔係燦光 → 柔光（CQ 90；v4）');
}

console.log('# ③ 分數來源（只計芽崽＋跳跳期）');
{
  const cq = NEED;
  for (const [b, k] of Object.entries(KIND)) {
    const s = build(b === 'ember' ? { play: 10, feed: 1 } : { [k]: 10, play: 1 }, { clean: 100 }); if (b === 'crystal') setLogin(s, 10, 10); s.cq = cq; const r = S.branch5Check(s);
    ok(r.form === b, `${k} → ${D.FORM_NAME[b]}`, JSON.stringify(r.score));
  }
  { const s = build({ mg: 6, play: 4, feed: 3 }); s.cq = cq; ok(S.branch5Check(s).score.ember === 6 * C.kinds.mg.w + 4 * C.kinds.play.w && S.branch5Check(s).form === 'ember', `play＋mg → 火苗（玩 +${C.kinds.play.w}、小遊戲 +${C.kinds.mg.w}）`, S.branch5Check(s).score.ember); }
  { const s = build({ feed: 3 }, { rain: true }); s.cq = cq; const r = S.branch5Check(s); ok(r.score.tide === 0 && Math.abs(r.score.shroom - 3 * C.weather.route.rain.w) < 1e-9, `（平時鐘點）落雨時餵食 → 菇傘只計一次（×${C.weather.route.rain.w}）、唔計水珠（v4／v10.3）`); }
  { const s = build({ feed: 3, rinse: 6 }); s.cq = cq; ok(S.branch5Check(s).form === 'tide', 'rinse → 水珠'); }
  // v7 晶角：清潔度唔再係門檻；分＝即清上線 ÷ 有便便上線 × k × 總數
  { const s = build({ poop: 8, feed: 2 }, { clean: 0 }); s.cq = cq; const r = S.branch5Check(s); ok(r.score.crystal === 0 && !r.ok && r.raw.loginPoop === 0, '冇上線紀錄 → 晶角 0 分（清便便本身唔計）', JSON.stringify(r.score)); }
  { const s = setLogin(build({ poop: 8, feed: 2 }, { clean: 0 }), 4, 4); s.cq = cq; const r = S.branch5Check(s); ok(Math.abs(r.score.crystal - C.crystal.k * 10) < 1e-9 && r.form === 'crystal' && r.raw.quickRate === 1, `清潔平均 0 都得（v7 取消 ≥60）：4/4 即清 → 晶角 ${C.crystal.k * 10} → 晶角`, JSON.stringify(r.score)); }
  { const s = setLogin(build({ poop: 8, feed: 2 }), 4, 2); s.cq = cq; const r = S.branch5Check(s); ok(Math.abs(r.score.crystal - 0.5 * C.crystal.k * 10) < 1e-9 && r.raw.quickRate === 0.5, '2/4 即清 → 比率 0.5 × k × 總數', JSON.stringify(r.raw)); }
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
    const s = pet('sprout'); s.needs.hunger = 10; S.feed(s, 'meal'); S.play(s); S.rinse(s); s.poops = 1; s.poopAge = [0]; S.clearPoop(s); S.mgApply(s, 10, 1e12);   // 晴天
    const b = s.evo.b5.sprout; ok(b.all === 5 && b.shroom === 0 && b.ember === C.kinds.play.w + C.kinds.mg.w && b.tide === 1 && b.crystal === 0 && b.moon === 0, '真實動作入分（晴天：feed 0／play＋mg／rinse／clearPoop 只入總數）', JSON.stringify(b));
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
  { const s = build({ play: 1 }, { rain: true }); const b = s.evo.b5.sprout; ok(b.tide === 0 && b.shroom === C.weather.route.rain.w && b.ember === 1 && b.all === 1, `平時落雨玩 → 菇傘 +${C.weather.route.rain.w}、火苗 +1、水珠 0（v4／v10.3）`); }
  { const s = build({}); HOUR = MH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; ok(s.evo.b5.sprout.moon === 1, `${MH}:00 瞓覺撫摸 → 月眠只 +1`); }
  { const s = build({}); HOUR = DH; s.sleeping = true; S.notePetSleep(s); HOUR = DAY; const b = s.evo.b5.sprout; ok(b.moon === 1 && b.tide === 0, `${DH}:00 瞓覺撫摸 → 仍然計月眠（唔係水珠）`, JSON.stringify(b)); }
  // 夜晚淫餵 → 月眠
  { const s = build({ feed: 10 }, { h: MH2 }); s.cq = NEED; const r = S.branch5Check(s); ok(r.ok && r.form === 'moon' && r.score.shroom === 0 && r.score.moon === 10, '夜晚淨係餵 → 月眠 100%（菇傘唔計）', JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 12, play: 2 }, { h: MH2 }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'moon' && evOf(s).why === 'b5', `夜晚淫餵（${MH2}:00 餵 12 玩 2，高 CQ）→ 月眠（≥ 上限唔去燦光）`, s.form); }
  { const s = build({ feed: 6 }, { h: MH }); HOUR = DAY; WX = 'rain'; const rw0 = C.weather.route.rain.w; C.weather.route.rain.w = 1; for (let i = 0; i < 4; i++) S.noteCare(s, null, 'feed'); C.weather.route.rain.w = rw0; WX = 'clear'; /* fixture：1 單位菇傘照顧 */ s.cq = NEED; const r = S.branch5Check(s);
    ok(r.score.moon === 6 && r.score.shroom === 4 && r.form === (60 - 40 >= C.drawGapPt && 60 >= C.b5TopPct ? 'moon' : null), '夜晚 6 次＋白天 4 次餵 → 月眠 60%、菇傘 40%'); }
  { const s = build({ feed: 2, play: 8 }, { h: MH2 }); s.cq = NEED; ok(S.branch5Check(s).form === 'moon', `夜深陪玩（${MH2}:00 玩 8 餵 2）→ 月眠 100%（火苗唔計）`); }
  // 早起玩家 → 水珠
  { const s = build({ feed: 6, play: 4 }, { h: DH }); s.cq = NEED; const r = S.branch5Check(s); ok(r.form === 'tide' && r.score.tide === 10 && r.score.shroom === 0 && r.score.ember === 0, `晨露：${DH}:00 餵 6 玩 4 → 水珠 100%`, JSON.stringify(r.score)); }
  { const s = toAdult(build({ feed: 8, play: 4 }, { h: DH }), Math.max(C.brightCQ, C.b5CQ) + 20); ok(s.form === 'tide' && evOf(s).why === 'b5', '早起玩家（晨早照顧為主，高 CQ）→ 水珠', s.form); }
  { const s = build({ poop: 2 }, { h: MH, clean: 100 }); const r = S.branch5Check(s); ok(r.score.crystal === 0 && r.score.moon === 2, `${MH}:00 清便便 → 只計月眠`); }
}

console.log(`# ⑦ 燦光：CQ ≥${C.brightCQ} 且最高分 <${C.brightMaxTopPct}%（全面照顧）先過新 5 條`);
{
  const M = C.brightMaxTopPct, G = C.drawGapPt, hi = Math.max(C.brightCQ, C.b5CQ) + 10, go = (counts, cq, o) => toAdult(build(counts, o), cq);
  let s = go(mk(M - 1, M - 1 - G), hi); ok(s.form === 'bright' && evOf(s).b5.ok && Math.round(evOf(s).b5.topShare * 100) === M - 1, `最高 ${M - 1}%（新 5 條本身成立）＋CQ ${hi} → 燦光`, s.form);
  s = go(mk(M, M - G), hi); ok(s.form === 'shroom' && evOf(s).why === 'b5', `最高 ${M}%（啱啱好）＋CQ ${hi} → 菇傘`, s.form);
  s = go({ feed: 9, play: 4, rinse: 4, poop: 3 }, C.brightCQ); ok(s.form === (9 * 100 >= M * 20 ? (C.brightCQ >= NEED ? 'shroom' : baseForm(C.brightCQ)) : 'bright'), `9/20（45%）＋CQ ${C.brightCQ} → 照上限判（唔係燦光）`, s.form);
  if (C.brightCQ - 1 >= NEED) { s = go(mk(M - 1, M - 1 - G), C.brightCQ - 1); ok(s.form === 'shroom', `CQ ${C.brightCQ - 1}（唔夠燦光）＋最高 ${M - 1}% → 菇傘`, s.form); }
  s = go(mk(M - 1, M - 1 - G), C.brightCQ); ok(s.form === 'bright', `CQ ${C.brightCQ}（啱啱好）＋最高 ${M - 1}% → 燦光`, s.form);
  { const t = setLogin(build({ feed: 8, poop: 2 }, { clean: 100 }), 2, 2); s = toAdult(t, hi); ok(s.form === 'shroom', '晶角 2/2 即清（45%），但最高係菇傘 80% → 菇傘', s.form); }
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
  for (const b of D.BRANCH5) { const s0 = build(b === 'moon' ? { feed: 5, play: 5 } : { [KIND[b]]: 10 }, { h: b === 'moon' ? MH2 : DAY, clean: 100 }); if (b === 'crystal') setLogin(s0, 5, 5); const s = toAdult(s0, NEED); ok(s.form === b, `跳跳期完 → ${D.FORM_NAME[b]}`, s.form); s.growthSec = P.stageSec.adult - 1; S.step(s, 5, {}); ok(s.stage === 'elder' && s.form === b && D.evoForm(s.stage, s.form) === 'evo_still_' + b, `${D.FORM_NAME[b]} 成年 → 靜光仍係 ${b}`); }
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
  ok(ST.join() === 'clear,overcast,fog,rain', '天氣狀態：clear／overcast／fog／rain（v10 加霧）', ST.join());
  ok(W.route.overcast.to === 'shroom' && W.route.rain.to === 'shroom' && W.route.fog.to === 'shroom' && W.route.overcast.w === 0.4 && W.route.fog.w === W.route.overcast.w && W.route.rain.w === 0.8 && !W.route.clear, 'config：晴 0／陰 0.4／霧（當陰）0.4／落雨 0.8 → 菇傘（v10.3）');
  { const pr = Object.fromEntries(W.probs); ok(W.probs.length === 4 && pr.clear === 60 && pr.overcast === 20 && pr.fog === 5 && pr.rain === 15 && W.probs.every(([w]) => ST.includes(w)), 'config 天氣機率：晴60／陰20／雨15／霧5（v10.1 遊策；systems12 系統 7）', JSON.stringify(W.probs));
    ok(W.probs.reduce((t, [, p]) => t + p, 0) === 100 && pr.rain > pr.fog, 'v10.1：機率加埋 100、雨（15）多過霧（5）— 唔好倒轉', JSON.stringify(W.probs)); }
  WX = 'fog'; ok(S.weatherNow() === 'fog' && !S.isRaining(), 'fog：weatherNow／isRaining'); WX = 'clear';
  WX = 'bogus'; ok(S.weatherNow() === 'clear', '唔識嘅天氣 → clear'); WX = 'overcast'; ok(S.weatherNow() === 'overcast' && !S.isRaining(), 'overcast：weatherNow／isRaining'); WX = 'clear';
  let b = build({ feed: 2 }, { wx: 'overcast' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.overcast.w && b.tide === 0, `陰天餵 ×2 → 菇傘 +${2 * W.route.overcast.w}（v8 餵食本身 0）`, JSON.stringify(b));
  b = build({ feed: 2 }, { wx: 'fog' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.fog.w, `霧天餵 ×2 → 菇傘 +${2 * W.route.fog.w}（霧當陰）`, JSON.stringify(b));
  b = build({ feed: 2 }, { wx: 'rain' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.rain.w, `落雨餵 ×2 → 菇傘 +${2 * W.route.rain.w}`, JSON.stringify(b));
  b = build({ feed: 5 }, { clearFeed: true }).evo.b5.sprout; ok(b.shroom === 0 && b.all === 5, '晴天淨係餵 ×5 → 菇傘 0（v8：多餵唔會入菇傘）', JSON.stringify(b));
  b = build({ play: 2 }, { wx: 'fog' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.fog.w && b.ember === 2, '霧天玩 → 火苗＋菇傘（霧）', JSON.stringify(b));
  b = build({ play: 1 }, { wx: 'overcast' }).evo.b5.sprout; ok(b.shroom === W.route.overcast.w && b.ember === 1 && b.all === 1, `陰天玩 → 菇傘 +${W.route.overcast.w}、火苗 +1`, JSON.stringify(b));
  b = build({ play: 2 }, { wx: 'rain' }).evo.b5.sprout; ok(b.shroom === 2 * W.route.rain.w && b.ember === 2, `落雨玩 ×2 → 菇傘 +${2 * W.route.rain.w}`, JSON.stringify(b));
  b = build({ rinse: 1 }, { wx: 'rain' }).evo.b5.sprout; ok(b.tide === 1 && b.shroom === W.route.rain.w, '落雨沖洗 → 水珠（本身）＋菇傘', JSON.stringify(b));
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
console.log('⑨ v5／v8：月眠 20–03＋哄瞓（每晚 ≤3、每次 +2）、螢絨 CQ 25');
{
  const L = C.lull;
  ok(MOON.from === 20 && MOON.to === 3, `月眠時段 ${MOON.from}:00–0${MOON.to}:00`);
  { const b = build({ feed: 1, play: 1 }, { h: 20 }).evo.b5.sprout; ok(b.moon === 2 && !b.shroom && !b.ember, '20:00 照顧 → 只計月眠'); }
  ok(C.lumi.minCQ === 25 && C.lumi.maxChancePct === 20, '螢絨 minCQ 25、機率上限 20%（v8）');
  { const s = pet('sprout'); s.poops = 0; s.poopAge = []; s.poopTimer = 1e9; S.step(s, 1, {}); const n = s.poops; ok(n >= 1 && S.poopAges(s).length === n && S.poopAges(s)[n - 1] <= 1, 'step 出便便 → 記低 age 0', JSON.stringify([n, s.poopAge])); S.clearPoop(s); ok(!s.evo.b5.sprout.crystal && S.poopAges(s).length === s.poops, '清便便（冇上線窗口）→ 唔計晶角；age 同 poops 對齊'); }
  // 哄瞓
  const T0 = new Date(2026, 9, 20, 22).getTime(); let T = T0; S.setNowFn(() => T);
  const drowsy = (s) => { s.sleeping = false; s.needs.energy = L.drowsyEnergy - 5; return s; };
  ok(L.pts === 2 && L.perNight === 3 && L.nightCutH === 12, 'config 哄瞓：每次 +2、每晚 3 次、中午分界（v8）');
  let s = pet('sprout'); s.needs.energy = L.drowsyEnergy; ok(!S.isDrowsy(s) && !S.lullSleep(s).ok, `精力 ${L.drowsyEnergy} → 唔眼瞓、哄唔到`);
  drowsy(s); ok(S.isDrowsy(s), `精力 ${L.drowsyEnergy - 5} → 眼瞓`);
  let r = S.lullSleep(s, DAY); ok(r.ok && r.counted && s.sleeping && s.evo.b5.sprout.moon === L.pts && s.evo.b5.sprout.all === 1 && s.ev.some(e => e.type === 'lull'), `哄瞓 → 瞓著＋月眠 +${L.pts}（任何鐘點；總數 +1）`, JSON.stringify(r));
  ok(!S.lullSleep(s).ok, '瞓緊 → 唔使再哄');
  for (let i = 1; i < L.perNight + 2; i++) { T = T0 + i * 3600e3; drowsy(s); r = S.lullSleep(s, DAY); }
  ok(s.evo.b5.sprout.moon === L.perNight * L.pts && r.ok && !r.counted && s.sleeping, `同一晚哄 ${L.perNight + 2} 次 → 月眠只計 ${L.perNight} 次（${L.perNight * L.pts} 分；照瞓）`, JSON.stringify([s.evo.b5.sprout, r]));
  T = T0 + 24 * 3600e3; drowsy(s); r = S.lullSleep(s, DAY); ok(r.counted && s.evo.b5.sprout.moon === (L.perNight + 1) * L.pts, '第二晚 → 重新計', JSON.stringify(r));
  { T = T0; const t = pet('sprout'); drowsy(t); S.lullSleep(t, MH); const b = t.evo.b5.sprout; ok(b.moon === L.pts && !b.tide, `${MH}:00 哄瞓 → 月眠 +${L.pts}（時段唔影響）`); T = new Date(2026, 9, 21, DH).getTime(); drowsy(t); S.lullSleep(t, DH); ok(t.evo.b5.sprout.moon === 2 * L.pts && !t.evo.b5.sprout.tide, `${DH}:00 哄瞓 → 仍然月眠（唔係水珠）`); }
  { const e = pet('egg'); e.needs.energy = 1; ok(!S.isDrowsy(e) && !S.lullSleep(e).ok, '光卵 → 唔得'); }
  S.setNowFn(null);
}
console.log('⑩ v7／v8：晶角上線即清（窗口 crystal.windowSec、每次上線最多 1）');
{
  const Wn = C.crystal.windowSec; let T = new Date(2026, 9, 20, 12).getTime(); S.setNowFn(() => T);
  ok(Wn === 120 && C.crystal.k === 0.45, 'config：窗口 2 分鐘、k 0.45（v7／v10）');
  const login = (poops) => { const s = pet('sprout'); s.poops = poops; s.poopAge = Array(poops).fill(0); S.noteLogin(s, T); return s; };
  let s = login(1); T += (Wn - 1) * 1000; S.clearPoop(s); let b = s.evo.b5.sprout; ok(b.loginPoop === 1 && b.quickLogin === 1 && b.all === 1, `上線有 1 粒、${Wn - 1}s 清到 0 → 即清上線 +1`, JSON.stringify(b));
  s = login(1); T += Wn * 1000; S.clearPoop(s); ok(s.evo.b5.sprout.quickLogin === 1, `${Wn}s（啱啱好）→ 計`);
  s = login(1); T += (Wn + 1) * 1000; S.clearPoop(s); b = s.evo.b5.sprout; ok(b.loginPoop === 1 && !b.quickLogin, `${Wn + 1}s 先清 → 唔計（只係有便便上線 +1）`, JSON.stringify(b));
  s = login(2); S.clearPoop(s); ok(!s.evo.b5.sprout.quickLogin, '2 粒清 1 粒（未到 0）→ 未計'); S.clearPoop(s); ok(s.evo.b5.sprout.quickLogin === 1, '清埋第 2 粒 → 計');
  s.poops = 1; s.poopAge = [0]; S.clearPoop(s); ok(s.evo.b5.sprout.quickLogin === 1, '同一次上線再出再清 → 唔再計（每次上線最多 1）');
  s = login(0); s.poops = 1; s.poopAge = [0]; S.clearPoop(s); b = s.evo.b5.sprout; ok(!b.loginPoop && !b.quickLogin, '上線時冇便便 → 唔入分母／分子', JSON.stringify(b));
  { const t = login(1); S.noteLogin(t, T); S.clearPoop(t); const c = t.evo.b5.sprout; ok(c.loginPoop === 2 && c.quickLogin === 1, '再上線（新窗口）→ 分母 +1；即清 1/2', JSON.stringify(c));
    t.cq = 90; const r = S.branch5Check(t); ok(Math.abs(r.score.crystal - 0.5 * C.crystal.k * r.all) < 1e-9 && r.raw.quickRate === 0.5, '晶角分＝即清 ÷ 有便便上線 × k × 總數', JSON.stringify(r.raw)); }
  { const e = pet('egg'); e.poops = 1; ok(S.noteLogin(e, T) === null, '光卵 → 唔記上線'); }
  { const t = pet('sprout'); t.poops = 1; t.poopAge = [0]; S.noteLogin(t, T); t.stage = 'juvenile'; S.clearPoop(t); ok(t.evo.b5.sprout.quickLogin === 1 && t.evo.b5.sprout.loginPoop === 1, '窗口內轉階段 → 記返上線嗰階段'); }
  { const t = S.deserialize(S.serialize(login(1)), T); S.clearPoop(t); ok(t.evo.b5.sprout.quickLogin === 1, '上線窗口跟存檔'); }
  { const t = pet('sprout'); t.evo.b5 = { sprout: { all: 3, tide: 0, shroom: 0, crystal: 0, moon: 0, ember: 3 } }; t.poops = 1; t.poopAge = [0]; S.noteLogin(t, T); S.clearPoop(t); const c = t.evo.b5.sprout;
    ok(c.loginPoop === 1 && c.quickLogin === 1 && Number.isFinite(S.branch5Check(t).score.crystal), '舊存檔 bucket（冇 loginPoop／quickLogin 欄）→ 由 0 計', JSON.stringify(c)); }
  S.setNowFn(null);
}
console.log('⑪ v8／v10：新 5 條 CQ ＝ max(scaleToAge(b5CQ), b5CQFloor)');
{
  const BD = C.brightDays, T0 = new Date(2026, 9, 20, 12).getTime(); S.setNowFn(() => T0);
  ok(C.b5CQ === 25 && C.b5CQFloor === 18.5 && C.b5CQScaleToAge === true && BD.scaleToAge === true, 'config：b5CQ 25、floor 18.5、按年齡縮短（預設開）');
  const aged = (ageDays) => { const s = pet('sprout'); S.noteCare(s, null, 'play'); s.evo.day0 = S.dayKey(T0 - ageDays * 864e5); return s; };
  const want = (span) => Math.max(Math.ceil(C.b5CQ * span / BD.window), C.b5CQFloor);
  for (const [age, span] of [[0, 1], [3, 4], [4, 5], [5, 6], [6, 7], [20, 7]]) { const s = aged(age); ok(S.careDaysCheck(s).span === span && S.b5Need(s) === want(span), `出世 ${span} 日 → 門檻 ${want(span)}`, S.b5Need(s)); }
  { const s = aged(20); s.cq = C.b5CQ - 1; ok(!S.branch5Check(s).cqOk, `足 ${BD.window} 日：CQ ${C.b5CQ - 1} ✗`); s.cq = C.b5CQ; ok(S.branch5Check(s).cqOk && S.branch5Check(s).cqNeed === C.b5CQ, `CQ ${C.b5CQ} ✓`); }
  { const s = aged(3); s.cq = C.b5CQFloor - 0.1; ok(!S.branch5Check(s).cqOk, `出世 4 日：CQ ${C.b5CQFloor - 0.1} ✗（floor）`); s.cq = C.b5CQFloor; ok(S.branch5Check(s).cqOk, `CQ ${C.b5CQFloor} ✓`); }
  { const k = C.b5CQScaleToAge; C.b5CQScaleToAge = false; const s = aged(0); ok(S.b5Need(s) === C.b5CQ, '唔按年齡 → 固定 b5CQ'); C.b5CQScaleToAge = k; }
  { const s = setLogin(aged(5), 0, 0); s.evo.b5.sprout.ember = 10; s.evo.b5.sprout.all = 10; s.cq = 21; const r = S.branch5Check(s); ok(r.cqNeed === want(6) && !r.ok, `出世 6 日 CQ 21 < ${want(6)} → 唔成立`, JSON.stringify([r.cqNeed, r.cq])); }
  S.setNowFn(null);
}
console.log('⑫ v8 火苗：浮動團絨撳兩下開 game ＝ 一局小遊戲');
{
  const O = C.overlayMg; let T = new Date(2026, 9, 20, 12).getTime(); S.setNowFn(() => T); HOUR = DAY;
  ok(O.enabled === true && O.score == null && O.cooldownSec > 0, 'config overlayMg：開、及格分、cooldown', JSON.stringify(O));
  const s = pet('sprout'); let r = S.overlayOpenGame(s, T); const b = s.evo.b5.sprout;
  ok(r.ok && b.ember === C.kinds.mg.w && b.all === 1 && r.reward.score === P.mg.passScore && s.mg.plays === 1, `一局 → 火苗 +${C.kinds.mg.w}、獎勵＝及格一局`, JSON.stringify([b, r]));
  r = S.overlayOpenGame(s, T + (O.cooldownSec - 1) * 1000); ok(!r.ok && r.reason === 'cooldown' && s.evo.b5.sprout.ember === C.kinds.mg.w, `${O.cooldownSec - 1}s 內再開 → 唔計`);
  r = S.overlayOpenGame(s, T + O.cooldownSec * 1000); ok(r.ok && s.evo.b5.sprout.ember === 2 * C.kinds.mg.w, `${O.cooldownSec}s 後 → 再計一局`);
  ok(!S.overlayOpenGame(pet('egg'), T).ok, '光卵 → 唔計');
  { O.enabled = false; ok(S.overlayOpenGame(pet('sprout'), T).reason === 'off', 'config 關 → 唔計'); O.enabled = true; }
  { const t = pet('sprout'); S.overlayOpenGame(t, T); const u = S.deserialize(S.serialize(t), T); ok(u.mg.overlayAt === T, 'cooldown 跟存檔'); }
  S.setNowFn(null);
}
console.log(`結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
