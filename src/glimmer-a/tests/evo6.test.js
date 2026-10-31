/* evo6 六階段：node tests/evo6.test.js（時長／分支判定／螢絨條件／舊存檔遷移／DEV 跳階段資料層） */
const S = require('../src/sim.js');
const D = require('../src/data.js');
const EV = require('../src/events.js');
const fs = require('fs'), path = require('path');
const P = D.PARAMS, H = 3600, DAY = 86400;
let pass = 0, fail = 0;
function ok(cond, name, info) { if (cond) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const full = (s) => { for (const k of D.NEED_KEYS) s.needs[k] = 100; s.poops = 0; s.sleeping = false; };
function at(stage, extra) { const s = S.newState(1e12, 7); s.stage = stage; s.form = D.isBig(stage) ? 'soft' : null; full(s); return Object.assign(s, extra || {}); }
// 線上推進（需求維持滿，唔病 → 成長 100%）；返回 {s, h}（用咗幾多個鐘）
function runUntil(s, pred, maxH) { let h = 0; while (!pred(s) && h < maxH) { full(s); S.advance(s, 1800, {}, 60); h += 0.5; } return h; }
S.setHourFn(() => 12);

console.log('# 時長表（pet-template-v1 §6）');
{
  const T = P.stageSec;
  ok(T.egg === 600 && T.newborn === 6 * H && T.sprout === 18 * H && T.juvenile === 3 * DAY && T.adult === 7 * DAY && T.elder === 4 * DAY, '光卵 10 分／絨點 6h／芽崽 18h／跳跳期 3 日／守夜者 7 日／靜光 4 日', JSON.stringify(T));
  ok(JSON.stringify(S.STAGES) === JSON.stringify(['egg', 'newborn', 'sprout', 'juvenile', 'adult', 'elder']) && JSON.stringify(D.STAGES) === JSON.stringify(S.STAGES), '6 階段次序 sim＝data');
  ok(D.STAGES.every(st => D.STAGE_NAME[st] && P.stageDecayMul[st] != null), '每階段有名＋衰減倍率');
  const s = S.newState(1e12, 3); S.advance(s, 599, {}, 1); ok(s.stage === 'egg', '599s 仲係光卵'); S.advance(s, 2, {}, 1); ok(s.stage === 'newborn', '600s 孵化 → 絨點');
  const seq = []; const t = at('newborn'); let h = 0, last = t.stage;
  while (t.stage !== 'elder' && h < 400) { full(t); S.advance(t, 1800, {}, 60); h += 0.5; if (t.stage !== last) { seq.push([t.stage, h]); last = t.stage; } }
  const want = [['sprout', 6], ['juvenile', 24], ['adult', 96], ['elder', 264]];
  ok(JSON.stringify(seq.map(x => x[0])) === JSON.stringify(want.map(x => x[0])), '絨點→芽崽→跳跳期→守夜者→靜光（唔跳級）', JSON.stringify(seq));
  want.forEach(([st, wh], i) => ok(seq[i] && Math.abs(seq[i][1] - wh) <= 0.5, `${D.STAGE_NAME[st]} 喺累計 ${wh}h 入`, seq[i] && seq[i][1]));
  ok(t.ev.some(e => e.type === 'grow' && e.stage === 'sprout') && t.ev.some(e => e.type === 'grow' && e.stage === 'juvenile') && t.ev.some(e => e.type === 'evolve') && t.ev.some(e => e.type === 'elder'), 'grow／evolve／elder 事件齊');
  const e = at('elder', { form: 'bright' }); runUntil(e, x => x.fadeReady, 200);
  ok(e.fadeReady && e.stage === 'elder' && Math.abs(e.growthSec - 4 * DAY) < 1, '靜光 4 日完 → fadeReady（唔自動消失）', e.growthSec / H);
  ok(e.ev.filter(x => x.type === 'fadeReady').length === 1, 'fadeReady 事件只出一次'); S.advance(e, 10 * H, {}, 60); ok(e.ev.filter(x => x.type === 'fadeReady').length === 1 && e.stage === 'elder', '等確認期間唔重複／唔變');
  const r = S.fade(e, 2e12); ok(r.ok && e.stage === 'egg' && e.gen === 2 && e.memorial.length === 1 && e.memorial[0].form === 'bright' && !e.fadeReady, '化光 → 新光卵 gen 2＋紀念（燦光）');
  ok(!S.fade(at('adult')).ok, '未到靜光唔可以化光');
  // 遊策 10-31：離線成長真實計、單次上限 24h、每次最多升 1 階、升後進度 0、唔夠唔升
  const offAt = (stage, g, hrs, extra) => { const x = at(stage, Object.assign({ growthSec: g }, extra || {})); x.lastSeen = 1e12 - hrs * H * 1000; const r = S.applyOffline(x, 1e12); return { x, r }; };
  ok(P.offlineGrowCapH === 24, 'offlineGrowCapH = 24');
  let o = offAt('juvenile', 0, 23.9); ok(o.x.stage === 'juvenile' && Math.abs(o.x.growthSec - 23.9 * H) < 1, '23.9h → 成長 23.9h（未到 cap）', o.x.growthSec / H);
  o = offAt('juvenile', 0, 24); ok(o.x.stage === 'juvenile' && Math.abs(o.x.growthSec - 24 * H) < 1, '24h → 成長 24h', o.x.growthSec / H);
  o = offAt('juvenile', 0, 30); ok(o.x.stage === 'juvenile' && Math.abs(o.x.growthSec - 24 * H) < 1 && o.r.grow.G === 24 * H, '30h → cap 24h', o.x.growthSec / H);
  o = offAt('juvenile', 0, 200); ok(Math.abs(o.x.growthSec - 24 * H) < 1, '200h → 仍係 24h', o.x.growthSec / H);
  o = offAt('newborn', 0, 30); ok(o.x.stage === 'sprout' && o.x.growthSec === 0 && o.r.grow.up && o.r.grow.from === 'newborn' && o.r.grow.to === 'sprout', '絨點 6h 階段＋離線 30h（24h 夠升 2 階）→ 只升 1 階到芽崽、進度 0（唔跳去跳跳期）', [o.x.stage, o.x.growthSec]);
  o = offAt('egg', 0, 24); ok(o.x.stage === 'newborn' && o.x.growthSec === 0, '光卵 + 24h → 只到絨點、進度 0', [o.x.stage, o.x.growthSec]);
  o = offAt('newborn', 5 * H, 0.99); ok(o.x.stage === 'newborn' && Math.abs(o.x.growthSec - 5.99 * H) < 1, '唔夠時間（差 0.01h）→ 唔升、累積', o.x.growthSec / H);
  o = offAt('newborn', 5 * H, 1); ok(o.x.stage === 'sprout' && o.x.growthSec === 0, '啱啱夠（5h + 1h = 6h）→ 升、進度 0', [o.x.stage, o.x.growthSec]);
  ok(S.stageProgress(o.x) === 0, '升後 stageProgress = 0');
  o = offAt('juvenile', 2.5 * DAY, 24, { cq: 80 }); ok(o.x.stage === 'adult' && o.x.form === 'bright' && o.x.growthSec === 0 && o.x.ev.some(e => e.type === 'evolve'), '跳跳期尾離線 → 照舊判分支（CQ 80 燦光）、進度 0', [o.x.stage, o.x.form]);
  o = offAt('adult', 6.5 * DAY, 24); ok(o.x.stage === 'elder' && o.x.growthSec === 0 && o.x.form === 'soft', '守夜者 → 靜光 1 階、進度 0', [o.x.stage, o.x.growthSec]);
  o = offAt('elder', 3.5 * DAY, 24); ok(o.x.stage === 'elder' && o.x.fadeReady && o.x.ev.filter(e => e.type === 'fadeReady').length === 1 && o.r.grow.to === 'fade', '靜光尾離線 → 只設 fadeReady（化光等玩家確認），最多一次');
  { const x = o.x; x.lastSeen = 1e12 - 24 * H * 1000; S.applyOffline(x, 1e12); ok(x.stage === 'elder' && x.ev.filter(e => e.type === 'fadeReady').length === 1, '再離線唔會重複 fadeReady／自動化光'); }
  // 需求：照舊用有效時間 E（cap 12h、保底 20）→ 24h／30h 離線唔會比之前更極端
  for (const hrs of [24, 30, 200]) { o = offAt('juvenile', 0, hrs); ok(D.NEED_KEYS.every(k => o.x.needs[k] >= P.offlineNeedFloor - 1e-9) && Math.abs(o.r.E - 12 * H) < 1, `${hrs}h 離線：需求保底 ≥20、需求用 E=12h（同 evo6 前一樣）`, JSON.stringify(o.x.needs)); }
  ok(Math.abs(S.stageProgress(Object.assign(at('juvenile'), { growthSec: 1.5 * DAY })) - 0.5) < 1e-9, 'stageProgress 通用（跳跳期一半＝0.5）');
}

console.log('# 分支判定（跳跳期完先判；次序 螢絨 → 燦光 ≥70 → 柔光 ≥40 → 微塵）');
{
  const evo = (cq, lumi) => { const s = at('juvenile', { cq, growthSec: P.stageSec.juvenile - 1 });
    if (lumi) { s.evo.evIn.juvenile = { firefly_walk: 1 }; s.evo.care.juvenile = { all: 10, night: 4 }; }
    S.step(s, 5, {}); return s; };
  for (const [cq, f] of [[100, 'bright'], [70, 'bright'], [69, 'soft'], [40, 'soft'], [39, 'dust'], [0, 'dust']]) { const s = evo(cq); ok(s.stage === 'adult' && s.form === f, `CQ ${cq} → ${D.FORM_NAME[f]}`, s.form); }
  const a = evo(90, true); ok(a.form === 'lumi', '螢絨優先過燦光（CQ 90＋條件齊）', a.form);
  const b = evo(55, true); ok(b.form === 'lumi', 'CQ 55 啱啱夠 → 螢絨', b.form);
  const c = evo(54, true); ok(c.form === 'soft', 'CQ 54 → 唔夠螢絨 → 柔光', c.form);
  const ev = a.ev.find(e => e.type === 'evolve'); ok(ev && ev.why === 'lumi' && ev.lumi && ev.lumi.ok, 'evolve 事件記低 why＋螢絨檢查');
  ok(a.cq === P.cqStart, '入守夜者 CQ 重設');
  const sp = at('sprout', { cq: 80, growthSec: P.stageSec.sprout - 1 }); S.step(sp, 5, {}); ok(sp.stage === 'juvenile' && sp.form === null && sp.cq === 80, '芽崽 → 跳跳期：未分支、CQ 延續');
}

console.log('# 螢絨條件（芽崽／跳跳期 firefly_walk、CQ ≥55、夜晚照顧 ≥40%）');
{
  const mk = () => at('sprout', { cq: 60 });
  let s = mk(); ok(!S.lumiCheck(s).ok && !S.lumiCheck(s).fireflyOk, '冇螢火 → 唔得');
  // 經真事件系統：sprout 期觸發 firefly_walk → evIn.sprout 記到
  s = mk(); EV.ensure ? EV.ensure(s) : 0; const rec = EV.force(s, 'firefly_walk'); ok(rec && s.evo.evIn.sprout && s.evo.evIn.sprout.firefly_walk === 1, 'events.trigger → evo.evIn.sprout.firefly_walk +1', JSON.stringify(s.evo.evIn));
  const nb = at('newborn'); EV.force(nb, 'firefly_walk'); ok(!S.lumiCheck(nb).fireflyOk, '絨點期見螢火唔計（只計芽崽／跳跳期）');
  const ad = at('adult'); EV.force(ad, 'firefly_walk'); ok(ad.evo.evIn.adult.firefly_walk === 1 && !S.lumiCheck(ad).fireflyOk, '守夜者期記錄但唔計');
  // 夜晚佔比：noteCare 用鐘點（17:00–07:00＝夜）
  s = mk(); s.evo.evIn.sprout = { firefly_walk: 1 };
  const care = (h, n) => { S.setHourFn(() => h); for (let i = 0; i < n; i++) { s.needs.hunger = 10; S.feed(s, 'meal'); } };
  care(12, 6); care(22, 4); let L = S.lumiCheck(s); ok(L.nightAll === 10 && Math.abs(L.night - 0.4) < 1e-9 && L.nightOk && L.ok, '夜 4／總 10 ＝40% → 螢絨 ✓', JSON.stringify(L));
  care(12, 1); L = S.lumiCheck(s); ok(!L.nightOk && !L.ok, '夜 4／總 11 ＜40% → ✗', L.night);
  ok(S.isNightHour(17) && S.isNightHour(6.99) && !S.isNightHour(7) && !S.isNightHour(16.99), '夜晚＝17:00–07:00');
  s = mk(); S.setHourFn(() => 23); S.play(s); s.needs.clean = 10; S.rinse(s); s.poops = 1; S.clearPoop(s); S.mgApply(s, 100, 1e12);
  ok(s.evo.care.sprout.all === 4 && s.evo.care.sprout.night === 4, '照顧＝餵／玩／沖洗／清便便／接星屑（4 種都記）', JSON.stringify(s.evo.care));
  const n2 = at('newborn'); S.setHourFn(() => 23); S.play(n2); ok(S.careShare(n2).all === 0, '絨點期照顧唔計入佔比（只計芽崽＋跳跳期）');
  s = mk(); s.cq = 54; s.evo.evIn.sprout = { firefly_walk: 2 }; s.evo.care.sprout = { all: 2, night: 2 }; ok(!S.lumiCheck(s).ok && !S.lumiCheck(s).cqOk, 'CQ 54 → ✗');
  // 全程：芽崽期夜晚照顧＋螢火 → 跳跳期完自動螢絨
  const z = at('sprout', { cq: 70 }); z.evo.evIn.sprout = { firefly_walk: 1 }; S.setHourFn(() => 21);
  runUntil(z, x => x.stage === 'adult', 200); ok(z.stage === 'adult', '芽崽→守夜者（自動）'); S.setHourFn(() => 12);
  // 冇照顧紀錄（all=0）→ 夜晚 ✗
  ok(z.form === 'bright', '有螢火但冇照顧紀錄 → 唔係螢絨（燦光）', z.form);
  S.setHourFn(() => 12);
}

console.log('# 舊存檔（v1）遷移 → 最近階段');
{
  const v1 = (stage, form, gH) => { const s = S.newState(1e12, 9); s.v = 1; s.stage = stage; s.form = form; s.growthSec = gH * H; delete s.evo; delete s.gen; delete s.memorial; delete s.fadeReady; return JSON.stringify(s); };
  let r = S.deserialize(v1('egg', null, 0.05), 1e12); ok(r && r.v === 2 && r.stage === 'egg' && Math.abs(r.growthSec - 180) < 1, '光卵 → 光卵（進度保留）');
  r = S.deserialize(v1('sprout', null, 2), 1e12); ok(r && r.stage === 'newborn' && Math.abs(r.growthSec - 2 * H) < 1, '芽崽 2h → 絨點（2h）', r && r.stage);
  r = S.deserialize(v1('sprout', null, 10), 1e12); ok(r && r.stage === 'sprout' && Math.abs(r.growthSec - 4 * H) < 1, '芽崽 10h → 芽崽（10−6＝4h）', r && r.growthSec / H);
  r = S.deserialize(v1('sprout', null, 23.9), 1e12); ok(r && r.stage === 'sprout' && r.growthSec < P.stageSec.sprout, '芽崽 23.9h → 芽崽（唔會一開即跳）', r && r.growthSec / H);
  r = S.deserialize(v1('adult', 'bright', 200), 1e12); ok(r && r.stage === 'adult' && r.form === 'bright' && Math.abs(r.growthSec - 6 * DAY) < 1, '守夜者 200h → 守夜者 144h（最多留到 7 日−1 日）', r && r.growthSec / H);
  r = S.deserialize(v1('adult', 'bright', 100), 1e12); ok(r && r.stage === 'adult' && Math.abs(r.growthSec - 100 * H) < 1, '守夜者 100h → 守夜者 100h', r && r.growthSec / H);
  r = S.deserialize(v1('adult', 'soft', 5), 1e12); ok(r && r.stage === 'adult' && r.form === 'soft' && Math.abs(r.growthSec - 5 * H) < 1, '守夜者 5h → 守夜者 5h（形態保留）');
  r = S.deserialize(v1('adult', 'lumi', 1), 1e12); ok(r && r.form === 'lumi', '螢絨保留');
  r = S.deserialize(v1('adult', 'radiant', 1), 1e12); ok(r && r.form === 'bright', '舊 id radiant → bright');
  r = S.deserialize(v1('adult', null, 1), 1e12); ok(r && r.form === 'dust', '冇形態 → 微塵（保底）');
  ok(r.migrated && r.migrated.from === 1 && r.migrated.stage === 'adult', 'migrated 標記');
  ok(r.gen === 1 && Array.isArray(r.memorial) && r.evo && r.evo.evIn && !r.fadeReady, '補 evo6 欄位（gen／memorial／evo）');
  const v2 = S.newState(1e12, 4); v2.stage = 'juvenile'; v2.growthSec = 5 * H; v2.evo.evIn.sprout = { firefly_walk: 1 };
  r = S.deserialize(S.serialize(v2), 1e12); ok(r && r.stage === 'juvenile' && r.evo.evIn.sprout.firefly_walk === 1 && !r.migrated, 'v2 存檔原樣還原（含 evo 紀錄）');
  for (const st of D.STAGES) { const q = S.newState(1e12, 1); q.stage = st; q.form = D.isBig(st) ? 'dust' : null; ok(S.deserialize(S.serialize(q), 1e12).stage === st, 'deserialize 接受 ' + st); }
  const bad = S.newState(1e12, 1); bad.stage = 'zzz'; ok(S.deserialize(S.serialize(bad), 1e12) === null, '未知階段 → null');
  r = S.deserialize(v1('adult', 'bright', 200), 1e12); const hh = runUntil(r, x => x.stage === 'elder', 100); ok(r.stage === 'elder' && r.form === 'bright' && Math.abs(hh - 24) <= 0.5, '遷移後守夜者再 1 日先變靜光', hh);
}

console.log('# DEV 跳階段（資料層：evo 形態對應＋美術檔）');
{
  const map = { egg: 'evo_egg', newborn: 'evo_dot', sprout: 'evo_sprout', juvenile: 'evo_hop' };
  for (const st in map) ok(D.evoForm(st, null) === map[st], `${st} → ${map[st]}`);
  for (const [f, k] of [['lumi', 'lumi'], ['bright', 'radiant'], ['soft', 'soft'], ['dust', 'dust']]) { ok(D.evoForm('adult', f) === 'evo_guard_' + k && D.evoForm('elder', f) === 'evo_still_' + k, `${D.FORM_NAME[f]} → evo_guard_${k}／evo_still_${k}`); }
  const size = { evo_egg: 24, evo_dot: 28, evo_sprout: 32, evo_hop: 38, evo_guard_lumi: 44, evo_still_soft: 48 };
  for (const k in size) ok(D.FORMS[k].frameSize === size[k] && D.FORMS[k].pivot[0] === size[k] / 2 && D.FORMS[k].pivot[1] === size[k] - 3, `${k} ${size[k]}px pivot (w/2, h−3)`);
  const dir = path.join(__dirname, '../art/evo6');
  for (const k of D.EVO_FORMS) {
    const j = JSON.parse(fs.readFileSync(path.join(dir, 'atlas_' + k + '.json'), 'utf8')), fa = JSON.parse(fs.readFileSync(path.join(dir, 'face_anchors_' + k + '.json'), 'utf8'));
    const an = j.animations, n = Object.keys(an).filter(c => !c.endsWith('_noface')).length;
    const want = k === 'evo_egg' ? 5 : (k === 'evo_guard_dust' || k.startsWith('evo_still_')) ? 41 : 39;
    ok(fs.existsSync(path.join(dir, 'atlas_' + k + '.png')) && j.meta.frameSize === D.FORMS[k].frameSize && n === want && fa.anchors, `${k}：atlas＋anchors，${n} clip（要 ${want}）`, n);
    if (k !== 'evo_egg') ok(Object.keys(an).filter(c => !c.endsWith('_noface')).every(c => an[c + '_noface']) && D.CLIPS.idle && an.idle_noface, `${k}：每 clip 有 noface（kit 五官）`);
  }
  // still 全套（batch D）：唔再靠 MVP 7 clip
  const st = JSON.parse(fs.readFileSync(path.join(dir, 'atlas_evo_still_soft.json'), 'utf8'));
  ok(['nuzzle_purr', 'reunion_happy', 'walk', 'play', 'act_cool'].every(c => st.animations[c]), 'evo_still_* 有 nuzzle_purr／reunion_happy／walk／play／act_cool（batch D 全套）');
  ok(D.isBig('elder') && D.isBig('adult') && !D.isBig('juvenile') && D.legacyStage('newborn') === 'sprout' && D.legacyStage('elder') === 'adult', 'legacyStage／isBig');
  ok(D.EVO_CLIP_FALLBACK.nuzzle_purr === 'nuzzle' && D.EVO_CLIP_FALLBACK.reunion_happy === 'emo_happy', '缺 clip fallback：nuzzle_purr→nuzzle、reunion_happy→emo_happy');
  // 遊策 17:34：靜光（elder）每項需求消耗唔可以高過守夜者（adult）— 慢慢品
  ok(P.stageDecayMul.elder <= P.stageDecayMul.adult, `stageDecayMul elder ${P.stageDecayMul.elder} ≤ adult ${P.stageDecayMul.adult}`);
  for (const slp of [false, true]) for (const poops of [0, 2]) {
    const drop = (stg) => { const x = S.newState(0); x.stage = stg; x.form = 'soft'; x.growthSec = 3600; for (const k of D.NEED_KEYS) x.needs[k] = 90; x.poops = poops; x.sleeping = slp; x.poopTimer = 0; const b = Object.assign({}, x.needs); S.step(x, 60); const o = {}; for (const k of D.NEED_KEYS) o[k] = b[k] - x.needs[k]; return o; };
    const A = drop('adult'), El = drop('elder');
    ok(D.NEED_KEYS.every(k => El[k] <= A[k] + 1e-9), `靜光每項需求 1 分鐘消耗 ≤ 守夜者（sleeping=${slp} poops=${poops}）`, JSON.stringify({ adult: A, elder: El }));
  }
  // HD-2D rim mask：每個 evo 形態（除光卵）有 rim_<form>_live，覆蓋全部 noface 幀、rect 一致
  for (const k of D.EVO_FORMS.filter(k => k !== 'evo_egg')) {
    const rp = path.join(__dirname, '..', 'art', 'rim', 'rim_' + k + '_live.json'), aj = JSON.parse(fs.readFileSync(path.join(dir, 'atlas_' + k + '.json'), 'utf8'));
    const rj = fs.existsSync(rp) ? JSON.parse(fs.readFileSync(rp, 'utf8')) : { frames: {} }, nf = Object.keys(aj.frames).filter(f => f.includes('_noface'));
    ok(nf.length > 0 && nf.every(f => rj.frames[f] && JSON.stringify(rj.frames[f].frame) === JSON.stringify(aj.frames[f].frame)), `${k}：rim mask 覆蓋 ${nf.length} noface 幀`);
  }
  // DEV setStage 用嘅 enterStage：跳跳期 → 成年用正常判定
  const s = at('juvenile', { cq: 45 }); s.growthSec = P.stageSec.juvenile; S.checkStage(s); ok(s.stage === 'adult' && s.form === 'soft', 'next()：跳跳期 → 守夜者（CQ 45 柔光）');
}
console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
