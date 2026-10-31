/* 寵物行為測試（Node 無依賴）：node tests/behavior.test.js */
const fs = require('fs'), path = require('path');
const SIM = require('../src/sim.js');
const D = require('../src/data.js');
const LT = require('../src/lighting.js');
const BEH = require('../src/behavior.js');
const P = D.PARAMS.beh;
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? '  → ' + info : '')); } }
const FIX = BEH.FIX; const root0 = path.join(__dirname, '..');
function mkS(needs, o) { const s = SIM.newState(1e12, 5); s.stage = 'adult'; s.form = 'soft'; Object.assign(s.needs, { hunger: 90, mood: 90, clean: 90, energy: 90 }, needs || {}); Object.assign(s, o || {}); return s; }
function ctxAt(s, hour) { const pw = LT.compute(hour); return { s, pw, sun: pw.sun, override: null, event: null }; }
function run(b, ctx, sec) { const n = Math.round(sec / FIX); for (let i = 0; i < n; i++) BEH.step(b, ctx); }
function timeShare(seed, hour, sec, needs) {
  const b = BEH.create(seed), s = mkS(needs), ctx = ctxAt(s, hour), t = {};
  for (let i = 0; i < sec / FIX; i++) { BEH.step(b, ctx); t[b.state] = (t[b.state] || 0) + 1; }
  const tot = sec / FIX; for (const k in t) t[k] /= tot; return { t, b };
}
const sig = (b) => b.journal.map(j => j.n + ':' + j.ev + ':' + j.name + ':' + j.ph + '@' + j.t).join('|');

console.log('# 確定性／DOM-free');
{
  const src = fs.readFileSync(path.join(__dirname, '../src/behavior.js'), 'utf8');
  ok(!/Math\.random|Date\.now|new Date|performance\.now|document\.|window\./.test(src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '').replace(/typeof window[^;]*;?/g, '').replace(/root\s*=\s*[^;]*window[^;]*;?/g, '')), 'behavior.js 冇 Math.random／Date／DOM 依賴');
  const run1 = (seed) => { const b = BEH.create(seed), s = mkS(), ctx = ctxAt(s, 14); run(b, ctx, 900); return b; };
  const a = run1(3), b = run1(3), c = run1(4);
  ok(sig(a) === sig(b) && a.journal.length > 20, '同種子 → 日誌完全一致（' + a.journal.length + ' 條）');
  ok(sig(a) !== sig(c), '不同種子 → 日誌不同');
  const d1 = BEH.create(9), d2 = BEH.create(9), s = mkS(), ctx = ctxAt(s, 14);
  for (let i = 0; i < 600; i++) BEH.update(d1, 1 / 60, ctx);
  for (let i = 0; i < 300; i++) BEH.update(d2, 1 / 30, ctx);
  ok(sig(d1) === sig(d2), '固定步長：不同幀率（60／30 fps）餵入 → 結果一致');
}

console.log('# 待機變體 ×3（眨眼／搖擺／呵欠），間隔 6–15 秒');
{
  const b = BEH.create(21), s = mkS(), ctx = ctxAt(s, 14);
  run(b, ctx, 3600);
  const v = b.log.variants, kinds = {}; v.forEach(x => kinds[x.name] = (kinds[x.name] || 0) + 1);
  ok(['blink', 'sway', 'yawn'].every(k => kinds[k] > 0), '三種變體都出現：' + JSON.stringify(kinds));
  const gaps = []; for (let i = 1; i < v.length; i++) if (v[i].start - v[i - 1].end > 0) gaps.push(v[i].start - v[i - 1].end);
  const sorted = gaps.slice().sort((a, b) => a - b);
  console.log('    間隔（變體結束→下一個開始）：最短 ' + sorted[0].toFixed(1) + 's，中位 ' + sorted[sorted.length >> 1].toFixed(1) + 's');
  const inside = v.filter((x, i) => i && x.start - v[i - 1].end >= 6 - 1e-6).length / (v.length - 1);
  ok(inside > 0.5, '多數變體間隔 ≥ 6s（其餘為被別嘅動作打斷後重設）', inside.toFixed(2));
  ok(v.every(x => x.end == null || x.end - x.start <= 3), '每個變體 ≤ 3 秒');
  ok(Math.max(...gaps) < 400, '冇卡死（最長間隔 ' + Math.max(...gaps).toFixed(0) + 's，包括其他活動）');
  const sh = (hr) => { let w = 0; for (let sd = 1; sd <= 8; sd++) { const bb = BEH.create(sd), ss = mkS({ energy: 25 }), cc = ctxAt(ss, hr); run(bb, cc, 1200); w += bb.log.variants.filter(x => x.name === 'yawn').length / Math.max(1, bb.log.variants.length); } return w / 8; };
  const bn = (e) => { let w = 0; for (let sd = 1; sd <= 8; sd++) { const bb = BEH.create(sd), ss = mkS({ energy: e }), cc = ctxAt(ss, 14); run(bb, cc, 1500); w += bb.log.variants.filter(x => x.name === 'yawn').length / Math.max(1, bb.log.variants.length); } return w / 8; };
  ok(bn(55) > bn(95), '精力 <60 呵欠比例上升（' + bn(95).toFixed(2) + ' → ' + bn(55).toFixed(2) + '）');
}

console.log('# 6 表情綁需求狀態（優先序 unwell(sick) > hungry > tired > wantplay > …）');
{
  const E = (n) => BEH.exprFor(mkS(n));
  ok(Object.keys(D.EXPRESSIONS).length >= 6, '表情表 ≥ 6 種：' + Object.keys(D.EXPRESSIONS).join(','));
  const got = new Set([E({}), E({ hunger: 20 }), E({ energy: 20 }), E({ mood: 20 }), E({ clean: 20 }), E({ hunger: 5, mood: 5, clean: 5, energy: 5 })]);
  console.log('    需求→表情：' + [...got].join(','));
  ok(got.size >= 5, '不同需求狀態可到達 ≥ 5 種表情');
  ok(E({ hunger: 20, energy: 20 }) === 'hungry' || E({ hunger: 20, energy: 20 }) === 'sick', '同時餓同睏 → 餓（hungry）優先於 tired');
  ok(BEH.exprFor(mkS({ hunger: 3, mood: 3, clean: 3, energy: 3 })) === 'unwell', '極低需求 → unwell（sick clip）最優先');
  ok(D.EXPRESSIONS.hungry.clip === 'emo_hungry' && D.EXPRESSIONS.tired.clip === 'emo_sleepy', '表情→ clip 對應 art：hungry＝emo_hungry、tired＝emo_sleepy');
}

console.log('# 個性權重（團絨：黏人、愛睏、膽小）');
{
  const s = mkS(), ctx = ctxAt(s, 14), b = BEH.create(1), w = BEH.weights(b, ctx);
  const nb = BEH.create(1, { personality: { sticky: 0, sleepy: 0, timid: 0 } }), wn = BEH.weights(nb, ctx);
  ok(w.stay > wn.stay && w.nap > wn.nap && w.jump < wn.jump && w.walk < wn.walk, '個性：黏人→多停留、愛睏→多小睡、膽小→少跳／少行');
  const cm = (name, hr) => { let a = 0; for (let sd = 1; sd <= 6; sd++) a += timeShare(sd, hr, 1800).t[name] || 0; return a / 6; };
  ok(cm('stay', 14) > 0.35, '日間大部分時間喺原地（stay ' + cm('stay', 14).toFixed(2) + '）');
}

console.log('# 時段權重（早／午／晚／夜）');
{
  const share = (name, hr) => { let a = 0; for (let sd = 1; sd <= 10; sd++) a += timeShare(sd, hr, 1800).t[name] || 0; return a / 10; };
  const wN = BEH.weights(BEH.create(1), ctxAt(mkS(), 1)), wD = BEH.weights(BEH.create(1), ctxAt(mkS(), 14));
  ok(wN.nap > wD.nap && wN.walk < wD.walk, '深夜：小睡權重上升、行走下降');
  ok(share('nap', 1) > share('nap', 9), '深夜小睡時間比例 > 早上（' + share('nap', 1).toFixed(2) + ' vs ' + share('nap', 9).toFixed(2) + '）');
  ok(share('sunbathe', 20) === 0 && share('sunbathe', 1) === 0, '傍晚／深夜冇日光 → 唔曬太陽');
  ok(share('sunbathe', 14) > 0, '午間會曬太陽（' + share('sunbathe', 14).toFixed(3) + '）');
  ok(share('play', 20) > share('play', 1), '傍晚玩得多過深夜');
}

console.log('# 環境互動：曬太陽＋撞花盆（冷卻 260 秒）');
{
  const s = mkS(), ctx = ctxAt(s, 14);
  let b = BEH.create(2); BEH.force(b, 'sunbathe', ctx); run(b, ctx, 2);
  ok(b.state === 'sunbathe', '曬太陽狀態');
  run(b, ctx, 40);
  ok(b.journal.some(j => j.ev === 'phase' && j.name === 'sunbathe' && j.ph === 'lie'), '走到日照位置並躺低');
  ok(b.cool.sunbathe - b.t > P.envCooldown - 45 && b.cool.sunbathe > 0, '曬完設冷卻 ≈ ' + P.envCooldown + 's（剩 ' + (b.cool.sunbathe - b.t).toFixed(0) + 's）');
  ok(BEH.weights(b, ctx).sunbathe === 0, '冷卻中權重＝0');
  b = BEH.create(2); BEH.force(b, 'bump', ctx); run(b, ctx, 30);
  ok(b.journal.some(j => j.ev === 'impact') || b.journal.some(j => j.ev === 'clip' && j.name === 'pot_bump'), '撞花盆：播 pot_bump／撞擊');
  ok(b.props.length >= P.bumpProps[0], '撞花盆掉出 ' + b.props.length + ' 件園圃小物（目標 ' + P.bumpProps.join('–') + '）');
  ok(b.cool.bump - b.t > P.envCooldown - 45 && BEH.weights(b, ctx).bump === 0, '撞完冷卻 ' + P.envCooldown + 's，冷卻內唔再自主觸發');
  ok(b.props.every(p => p.life <= P.propLife[1]), '小物有壽命，會自行消失');
  const bb = BEH.create(3); const ss = mkS(); run(bb, ctxAt(ss, 14), 5000);
  const bumps = bb.journal.filter(j => j.ev === 'state' && j.name === 'bump').map(j => j.t), suns = bb.journal.filter(j => j.ev === 'state' && j.name === 'sunbathe').map(j => j.t);
  const mg = (a) => a.length < 2 ? 1e9 : Math.min(...a.slice(1).map((t, i) => t - a[i]));
  ok(mg(bumps) >= P.envCooldown - 1 && mg(suns) >= P.envCooldown - 1, '5000 秒內任何兩次環境互動間隔 ≥ ' + P.envCooldown + 's（bump ' + bumps.length + ' 次／sun ' + suns.length + ' 次）');
}

console.log('# 觸摸：摸、連點、睡眠中連點');
{
  const s = mkS(), ctx = ctxAt(s, 14);
  const fresh = (seed) => { const b = BEH.create(seed || 1); BEH.force(b, 'wake', ctx); run(b, ctx, 2); b.state = 'stay'; b.phase = ''; return b; };
  let b = fresh(); run(b, ctx, 10); BEH.tap(b, 'pet', 0); run(b, ctx, 0.2);
  ok(b.state === 'react' || b.state === 'startle', '單點摸：反應（' + b.state + '）');
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 3; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 0.3); }
  ok(b.state === 'cuddly' || b.journal.some(j => j.ev === 'state' && j.name === 'cuddly'), '2 秒內連摸 3 下 → 撒嬌（cuddly）');
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 1.9); }
  ok(b.journal.some(j => j.ev === 'state' && j.name === 'grumpy'), '10 秒內連點 5 下 → 鬧脾氣（grumpy）');
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 4; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 1.9); }
  ok(!b.journal.some(j => j.ev === 'state' && j.name === 'grumpy'), '只點 4 下 → 唔鬧脾氣');
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 3.2); }
  ok(!b.journal.some(j => j.ev === 'state' && j.name === 'grumpy'), '點得慢（>10 秒先 5 下）→ 唔鬧脾氣');
  // 鬧脾氣冷卻
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 1.0); } run(b, ctx, 3.3);
  const g1 = b.log.enters.grumpy || 0; for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 0.5); } ok((b.log.enters.grumpy || 0) === g1, '鬧完有冷卻 ' + P.tap.grumpyCooldown + 's，唔會連環鬧');
  // 點地面 → 部分機率跟隨（黏人）
  let fol = 0; for (let sd = 1; sd <= 60; sd++) { const bb = fresh(sd); run(bb, ctx, 12); BEH.tap(bb, 'ground', 50); run(bb, ctx, 0.2); if (bb.state === 'follow') fol++; }
  ok(fol > 15 && fol < 55, '點地面：黏人→多數但非全部跟隨（' + fol + '/60）');
  // 小睡中連點 → 輕喚醒＋睏睏表情，唔鬧脾氣
  b = BEH.create(5); BEH.force(b, 'nap', ctx); run(b, ctx, 6);
  ok(b.state === 'nap', '入咗小睡');
  for (let i = 0; i < 6; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 0.5); }
  ok(!b.journal.some(j => j.ev === 'state' && j.name === 'grumpy'), '小睡中連點 6 下：唔鬧脾氣');
  ok(b.journal.some(j => j.ev === 'state' && j.name === 'wake') && b.journal.some(j => j.name === 'sleepWake'), '輕喚醒（wake）');
  run(b, ctx, 1.0); ok(b.expr === 'tired' && b.base === 'emo_sleepy', '醒後睏睏表情（emo_sleepy）仍喺 ' + P.tap.sleepyHold + 's 內');
  run(b, ctx, 5); ok(b.expr !== 'tired', '之後回復正常表情（' + b.expr + '）');
  // sim 睡眠（關燈）中連點
  const ss = mkS({ energy: 40 }, { sleeping: true }), cs = ctxAt(ss, 23); b = BEH.create(6); run(b, cs, 20);
  for (let i = 0; i < 7; i++) { BEH.tap(b, 'pet', 0); run(b, cs, 0.4); }
  ok(!b.journal.some(j => j.ev === 'state' && j.name === 'grumpy') && b.state === 'simsleep', '關燈瞓覺中連點 7 下：維持睡眠、唔鬧脾氣（翻身 ' + (b.log.enters.sleepStir || 0) + ' 次）');
  // PR #19 P1：連點 5 下 → tantrumReq（main 交俾 events.tapTantrum，48h 冷卻）
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 1.0); }
  ok(b.tantrumReq === 1 && b.journal.some(j => j.name === 'tantrum'), '連點 5 下：發出 1 次鬧脾氣事件請求（tantrumReq）');
  b = fresh(); run(b, ctx, 10); for (let i = 0; i < 4; i++) { BEH.tap(b, 'pet', 0); run(b, ctx, 1.0); } ok(!b.tantrumReq, '4 下：冇事件請求');
  // 不適（強制狀態）都會吞普通觸摸，但 5 下連點仍然要出請求（e2e 唔好睇當下狀態）
  const su = mkS({ hunger: 5, mood: 5, clean: 5, energy: 5 }), cu = ctxAt(su, 14);
  b = BEH.create(8); run(b, cu, 2); ok(b.state === 'unwell', '需求 <15 → 不適');
  for (let i = 0; i < 5; i++) { BEH.tap(b, 'pet', 0); run(b, cu, 0.2); }
  ok(b.tantrumReq === 1, '不適中連點 5 下仍然發出 tantrumReq');
  // PR #19 P1：關燈瞓覺中點寵物 → UI 輕喚醒（sim 起身）＋ 'wake' tap → 睏睏 sleepyHold 秒、唔鬧脾氣
  const sw = mkS({ energy: 40 }, { sleeping: true }), cw = ctxAt(sw, 23); b = BEH.create(7); run(b, cw, 20);
  const n0 = Object.assign({}, sw.needs); sw.sleeping = false; BEH.tap(b, 'wake', 0); run(b, cw, 0.5);
  ok(b.log.enters.lightWake === 1 && b.journal.some(j => j.name === 'lightWake') && !b.tantrumReq, '睡眠點擊＝輕喚醒（lightWake），冇鬧脾氣請求');
  run(b, cw, 1.0); ok(b.expr === 'tired' && b.state !== 'simsleep', '輕喚醒後起身＋睏睏表情（' + b.state + '／' + b.expr + '）');
  ok(JSON.stringify(sw.needs) === JSON.stringify(n0), '輕喚醒唔扣需求');
  run(b, cw, P.tap.sleepyHold + 1); ok(b.expr !== 'tired' || sw.needs.energy < 30, sleepyHoldMsg());
  function sleepyHoldMsg() { return P.tap.sleepyHold + 's 後睏睏表情完結（' + b.expr + '）'; }
}

console.log('# clip 表同 遊美 art/CLIPS.json 對齊');
{
  const art = JSON.parse(fs.readFileSync(path.join(__dirname, '../art/CLIPS.json'), 'utf8')).clips;
  ok(art.length === 23, 'art CLIPS.json 有 23 個 clip');
  let bad = [];
  art.forEach(a => {
    const c = D.CLIPS[a.name]; if (!c) { bad.push(a.name + ':缺'); return; }
    if (c.frames !== a.frames || c.fps !== a.fps || !!c.loop !== !!a.loop || c.priority !== a.priority || (c.cooldown || 0) !== (a.cooldown_s || 0) || c.ready !== (a.status === '已交付')) bad.push(a.name);
  });
  ok(bad.length === 0, 'data.js CLIPS 同 art 一致（frames／fps／loop／priority／cooldown／ready）', bad.join(','));
  const extras = Object.keys(D.CLIPS).filter(k => !art.find(a => a.name === k) && !D.CLIPS[k].live);
  ok(extras.every(k => D.CLIPS[k].extra), '額外 clip（' + extras.join(',') + '）全部標 extra:true');
  const atl = {}; ['egg', 'sprout', 'radiant', 'soft', 'props'].forEach(n => { atl[n] = JSON.parse(fs.readFileSync(path.join(__dirname, '../art/atlas_' + n + '.json'), 'utf8')); });
  ok(Object.values(atl).every(a => a.meta.size.w <= 1024 && a.meta.size.h <= 1024), '全部圖集 ≤ 1024×1024');
  ok(atl.egg.meta.size.w === 1024 && atl.egg.animations.egg_idle.frames.length === 4 && atl.egg.animations.egg_glow.frames.length === 2, 'atlas_egg（遊美 atlas_legacy，1024 寬）：egg_idle ×4／egg_glow ×2');
  const stale = [];
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).forEach(e => { const f = path.join(d, e.name); if (e.isDirectory()) { if (!/node_modules|\.git|screens/.test(e.name)) walk(f); } else if (/\.(js|html|json)$/.test(e.name) && !/tests[\\/]/.test(f) && fs.readFileSync(f, 'utf8').includes('pet_tuanrong_atlas')) stale.push(f); });
  walk(root0);
  ok(stale.length === 0 && !fs.existsSync(path.join(__dirname, '../art/pet_tuanrong_atlas.png')), '冇引用／冇附帶舊 2048 寬 pet_tuanrong_atlas', stale.join());
  const miss = []; ['sprout', 'radiant', 'soft'].forEach(f => Object.keys(D.CLIPS).filter(k => D.CLIPS[k].ready).forEach(k => { const an = atl[f].animations[k]; if (!an || an.frames.length !== D.CLIPS[k].frames) miss.push(f + '/' + k); }));
  ok(miss.length === 0, '每個 ready clip 喺三個形態圖集都有、幀數一致', miss.join(','));
  const pend = Object.keys(D.CLIPS).filter(k => !D.CLIPS[k].ready && !D.CLIPS[k].extra && !D.CLIPS[k].live);
  ok(pend.length === 0 && art.every(a => D.CLIPS[a.name].ready), '遊美 23 個 clip 已全數交付（ready:true，冇待定／placeholder）', pend.join());
  ok(extras.every(k => !D.CLIPS[k].ready), '額外 clip（' + extras.join(',') + '）仍冇美術 → 保持程序化 placeholder');
  const rmp = D.PARAMS.art.playRootMotion; ok(rmp && rmp.frames.join() === '3,4' && rmp.dx64 === 4 && rmp.dx32 === 2, 'play root-motion：frame4–5（idx 3,4）64px +4／32px +2（遊美 play 位移為 0）');
  const props = atl.props.animations; ok(['flowerpot_idle', 'sun_patch'].every(k => Object.keys(props).some(n => n.startsWith(k.split('_')[0]))), 'atlas_props 有 flowerpot／sun_patch 系列');
}

console.log('# 螢火散步（firefly_walk）事件腳本');
{
  const E = require('../src/events.js');
  const s = mkS(); const ctx = ctxAt(s, 19); const b = BEH.create(11);
  const vis = E.visual('firefly_walk', 0, 7); ctx.event = { id: 'firefly_walk', t: 0, vis };
  const clips = new Set(); const n = Math.round(7 / FIX); let moved = 0;
  for (let i = 0; i < n; i++) { ctx.event.t = i * FIX; ctx.event.vis = E.visual('firefly_walk', i * FIX, 7); BEH.step(b, ctx); clips.add(b.clip); }
  ok(b.journal.some(j => j.ev === 'event' && j.name === 'firefly_walk'), '日誌有 event:firefly_walk');
  ok(clips.has('play') || clips.has('walk'), '用現有 walk／play clip：' + [...clips].join());
  ok([...clips].every(c => !!D.CLIPS[c]), '所有用到嘅 clip 喺 clip 表有定義');
}

console.log('# 生命感第一段（F1 表情 overlay／F2 gaze／A1 邊行邊望／D2 點一下回頭）');
{
  const Q = BEH.quantGaze, LK = P.look;
  ok(Q(0, 0) === 'C' && Q(-0.3, 0) === 'CL' && Q(-0.9, 0) === 'L' && Q(0.3, 0) === 'CR' && Q(0.9, 0) === 'R' && Q(0, -0.8) === 'U' && Q(0, 0.8) === 'D' && Q(0.2, 0.1) === 'C', 'F2 gaze 量化：L/CL/C/CR/R/U/D（含中心死區）');
  ok(Q(-0.7, -0.6) === 'L' && Q(0.5, -0.7) === 'U', 'F2 量化：斜角以較大分量為準');
  ok(BEH.MIRROR.L === 'R' && BEH.MIRROR.CL === 'CR' && BEH.MIRROR.U === 'U' && BEH.MIRROR.C === 'C', 'MIRROR：朝左時 sprite 空間 L↔R');
  // A1：行路時望行進方向，間中望鏡頭
  { const b = BEH.create(11), s = mkS(), ctx = ctxAt(s, 14); run(b, ctx, 1); BEH.force(b, 'walk', ctx); let fwd = 0, cam = 0, n = 0, ok1 = true;
    for (let i = 0; i < 60 * 40; i++) { BEH.step(b, ctx); if (b.clip !== 'walk') { if (b.state !== 'walk') { BEH.force(b, 'walk', ctx); } continue; } n++; const src = b.look.src; if (src === 'walk') { fwd++; if (b.look.tx * b.dir <= 0) ok1 = false; } if (src === 'camera') cam++; }
    ok(n > 300 && fwd / n > 0.6 && cam > 0 && ok1, 'A1 walk：大部分時間望行進方向（' + (100 * fwd / Math.max(1, n)).toFixed(0) + '%），間中望鏡頭（' + (100 * cam / Math.max(1, n)).toFixed(0) + '%）', JSON.stringify([n, fwd, cam, ok1])); }
  // dwell：轉格後最少停 0.25s
  { const b = BEH.create(12), s = mkS(), ctx = ctxAt(s, 14); let last = b.look.q, lastT = 0, minD = 99, ch = 0;
    for (let i = 0; i < 60 * 120; i++) { BEH.step(b, ctx); if (i % 90 === 0) BEH.tap(b, 'ground', (i % 7 - 3) * 20, -20); if (b.look.q !== last) { if (ch) minD = Math.min(minD, b.t - lastT); ch++; last = b.look.q; lastT = b.t; } }
    ok(ch > 10 && minD >= LK.dwellSec - 1e-6, 'F2 gaze 轉格最少停 ' + LK.dwellSec + 's（' + ch + ' 次轉格，最短 ' + minD.toFixed(3) + 's）', minD); }
  // D2：點觸點 → gaze 望觸點；觸點喺背後 → 轉身
  const mk = () => { const b = BEH.create(13), s = mkS(), ctx = ctxAt(s, 14); run(b, ctx, 2); b.state = 'stay'; b.phase = ''; b.variant = null; b.x = 0; b.dir = 1; b.clip = 'idle'; return { b, ctx }; };
  { const { b, ctx } = mk(); BEH.tap(b, 'ground', -60, -20); run(b, ctx, 0.6);
    ok(b.look.src === 'tap' && (b.look.q === 'L' || b.look.q === 'CL'), 'D2 點地下左邊 → gaze 望左（' + b.look.q + '）'); }
  { const { b, ctx } = mk(); BEH.tap(b, 'pet', 30, -60); run(b, ctx, 0.5); ok(b.look.q === 'U' || b.look.q === 'CR' || b.look.q === 'R', 'D2 點寵物頭頂右上 → gaze 望 U／右（' + b.look.q + '）'); }
  { const was = D.CLIPS.turn_back.ready; D.CLIPS.turn_back.ready = false;
    const { b, ctx } = mk(); BEH.tap(b, 'pet', -10, -20); BEH.step(b, ctx);
    ok(b.dir === -1 && b.turn && !b.turn.clip && b.show.clip !== 'turn_back' && b.journal.some(j => j.ev === 'turn' && j.name === 'L'), 'D2 冇 turn_back 美術：即刻翻轉（dir −1）＋記 turn');
    D.CLIPS.turn_back.ready = true;
    const B = mk(); B.b.journal.length = 0; BEH.tap(B.b, 'pet', -10, -20); BEH.step(B.b, B.ctx); const f0 = B.b.show.frame, c0 = B.b.show.clip, fv0 = B.b.face.clip;
    const seen = new Set(); for (let i = 0; i < 40; i++) { BEH.step(B.b, B.ctx); if (B.b.show.clip === 'turn_back') seen.add(B.b.show.frame); }
    ok(c0 === 'turn_back' && f0 === 0 && fv0 === 'turn_back' && B.b.dir === -1 && B.b.journal.some(j => j.ev === 'clip' && j.name === 'turn_back'), 'D2 有 turn_back：播 turn_back（frame0 起）、dir −1、face 跟 clip');
    ok(seen.has(3) && B.b.show.clip !== 'turn_back' && !B.b.turn, 'D2 turn_back 播齊 4 幀（0.5s）後返回原 clip（' + B.b.show.clip + '）');
    const C = mk(); BEH.tap(C.b, 'pet', 12, -20); BEH.step(C.b, C.ctx); ok(C.b.dir === 1 && !C.b.turn && C.b.show.clip !== 'turn_back', 'D2 點寵物前面：唔轉身、唔播 turn_back');
    D.CLIPS.turn_back.ready = was; }
  // F1：表情由 clip／需求決定；閉眼款 gaze 固定 C；faceForce（QA）
  { const { b, ctx } = mk(); BEH.force(b, 'grumpy', ctx); BEH.step(b, ctx); ok(b.face.eyes === 'angry' && b.face.mouth === 'angry', 'F1 鬧脾氣 → angry 眼＋口');
    b.faceForce = { eyes: 'happy' }; BEH.step(b, ctx); ok(b.face.eyes === 'happy' && b.face.closed && b.face.gaze === 'C', 'F1 閉眼款（happy）gaze 固定 C');
    b.faceForce = null; b.look.force = 'R'; BEH.step(b, ctx); ok(b.look.q === 'R' && b.face.gaze === (b.dir < 0 ? 'L' : 'R'), 'QA 強制 gaze R（sprite 空間跟 dir 鏡像）'); }
  // 生命感美術（遊美 10-31）：noface 身體、kit 五官、錨點齊
  { const LV = path.join(root0, 'art/liveliness'); const fa = JSON.parse(fs.readFileSync(path.join(LV, 'face_anchors.json'), 'utf8')); const bad = [];
    for (const f of ['sprout', 'radiant', 'soft']) { const A = JSON.parse(fs.readFileSync(path.join(LV, 'atlas_' + f + '_live.json'), 'utf8'));
      Object.keys(D.CLIPS).filter(k => D.CLIPS[k].ready || k === 'turn_back').forEach(k => { const an = A.animations[k + '_noface']; const anc = fa.anchors[f][k]; if (!an || an.frames.length !== D.CLIPS[k].frames || !anc || anc.length !== D.CLIPS[k].frames) bad.push(f + '/' + k); });
      D.PARAMS.face.eyes.forEach(st => (D.PARAMS.face.closedEyes.includes(st) ? ['C'] : D.PARAMS.face.gazeBins).forEach(g => ['l', 'r'].forEach(s => { if (!A.frames['eyes_' + st + '_' + g + '_' + s]) bad.push(f + '/eyes_' + st + '_' + g + '_' + s); })));
      D.PARAMS.face.mouths.forEach(m => { if (!A.frames['mouth_' + m]) bad.push(f + '/mouth_' + m); }); ['bulb_base', 'bulb_glow'].forEach(n => { if (!A.frames[n] || !A.frames[n].pivotPx) bad.push(f + '/' + n); });
      if (fa.anchors[f].turn_back[0].faceVisible !== false) bad.push(f + '/turn_back0 faceVisible'); }
    ok(bad.length === 0, '生命感 atlas：全部 ready clip＋turn_back 有 _noface（幀數同錨點一致）、kit 眼 8 款×gaze×l/r、口 8、燈泡 2；turn_back frame0 faceVisible=false', bad.slice(0, 8).join()); }
}

console.log('# 遊美 daylight.json 時段 hook（lighting.setDaylight／daylightAt）');
{
  const L = require('../src/lighting.js');
  const j = JSON.parse(fs.readFileSync(path.join(__dirname, '../art/daylight/daylight.json'), 'utf8'));
  ok(L.hasDaylight() === false && L.compute(9).daylight === null, '未載入 daylight.json → daylight:null（fallback 舊 grade）');
  ok(L.setDaylight(j) === true && L.hasDaylight(), 'setDaylight 載入 daylight.json');
  ok(j.blendSeconds === 1800 && Object.keys(j.periods).sort().join() === 'dusk,early,night,noon', 'JSON：4 時段、blendSeconds 1800');
  ok(L.DL_MAP.morning === 'early' && L.DL_MAP.noon === 'noon' && L.DL_MAP.evening === 'dusk' && L.DL_MAP.night === 'night', '遊策時段 → daylight：早→early／午→noon／晚→dusk／夜→night');
  const at = (h) => L.compute(h).daylight;
  ok(at(9).id === 'early' && at(14).id === 'noon' && at(20).id === 'dusk' && at(1).id === 'night' && at(23.5).id === 'night' && at(6.9).id === 'night', '各鐘點對應時段（以遊策 07／11／17／23 為界）');
  ok(at(9).mix === 1 && at(14).mix === 1, '時段穩定後 mix=1');
  ok(Math.abs(at(7.25).mix - 0.5) < 1e-9 && at(7).mix === 0 && at(7.5).mix === 1, 'blendSeconds 1800：新時段開始後 30 分鐘 mix 0→1（07:15＝0.5）');
  const a0 = at(7), a1 = at(7.25), a2 = at(7.5), hx = (c) => [parseInt(c.slice(1, 3), 16), parseInt(c.slice(3, 5), 16), parseInt(c.slice(5, 7), 16)];
  const nightA = hx(j.periods.night.ambientMultiply), earlyA = hx(j.periods.early.ambientMultiply);
  ok(a0.ambient.every((v, i) => Math.abs(v - nightA[i]) < 1e-6) && a2.ambient.every((v, i) => Math.abs(v - earlyA[i]) < 1e-6) && a1.ambient.every((v, i) => v > Math.min(nightA[i], earlyA[i]) - 1e-6 && v < Math.max(nightA[i], earlyA[i]) + 1e-6), 'ambientMultiply 由夜色線性過渡到早色（mix 0／0.5／1）');
  ok(Math.abs(a1.bloom - (j.periods.night.bloom + j.periods.early.bloom) / 2) < 1e-9 && Math.abs(a1.vignette - (j.periods.night.vignette + j.periods.early.vignette) / 2) < 1e-9, 'bloom／vignette 同步 blend');
  ok(at(1).bloom === 0.65 && at(14).vignette === 0.1 && at(20).bloom === 0.45, '穩定時直接採用 JSON 數值（night bloom .65／noon vignette .1／dusk bloom .45）');
  ok(at(14).pet.mul.every(v => v >= 0) && at(1).pet.rim.length === 3 && at(14).bg === 'bg_noon.png' && at(14).overlay === 'light_noon.png', 'pet tint（multiply／add／rim）＋ bg／overlay 檔名');
  for (const id of ['early', 'noon', 'dusk', 'night']) ok(fs.existsSync(path.join(__dirname, '../art/daylight/bg_' + id + '.png')) && fs.existsSync(path.join(__dirname, '../art/daylight/light_' + id + '.png')), 'art/daylight bg／light_' + id + '.png 存在');
  ok(L.setDaylight(null) === false && L.compute(9).daylight === null, 'JSON 缺失 → 退返舊 grade（唔爆）');
  L.setDaylight(j);
}

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
