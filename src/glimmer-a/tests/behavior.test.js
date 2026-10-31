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


console.log('# 生命感第二段（F3／A2／A3／B1／B2＋個性「蠢蠢地但覺得自己好醒」）');
{
  const LVP = P.live, mk2 = (needs, hour, seed) => { const b = BEH.create(seed || 13), s = mkS(needs), ctx = ctxAt(s, hour == null ? 14 : hour); run(b, ctx, 0.5); b.state = 'stay'; b.phase = ''; b.variant = null; b.x = 0; b.dir = 1; b.clip = 'idle'; return { b, s, ctx }; };
  // ── 資料：clip 對齊 art liveliness（幀數／fps／interruptible／冷卻），逐幀五官＝face_anchors ──
  { const LVD = path.join(root0, 'art/liveliness'), fa = JSON.parse(fs.readFileSync(path.join(LVD, 'face_anchors.json'), 'utf8')), cj = JSON.parse(fs.readFileSync(path.join(LVD, 'CLIPS.json'), 'utf8')); const bad = [];
    const NEW = ['walk_happy', 'walk_drag', 'sniff', 'lookup', 'swat', 'scratch', 'sneeze'];
    for (const k of NEW) { const a = cj.clips.find(c => c.name === k), d = D.CLIPS[k];
      if (!a || !d || !d.live || a.frames !== d.frames || a.fps !== d.fps || !!a.loop !== !!d.loop || a.interruptible !== d.interruptible || (a.cooldown_s || 0) !== (d.cooldown || 0)) bad.push('spec/' + k);
      for (const f of ['sprout', 'radiant', 'soft']) { const A = JSON.parse(fs.readFileSync(path.join(LVD, 'atlas_' + f + '_live.json'), 'utf8')); const an = A.animations[k + '_noface'], anc = fa.anchors[f][k];
        if (!an || an.frames.length !== d.frames || !anc || anc.length !== d.frames) bad.push(f + '/' + k);
        else anc.forEach((x, i) => { const e = D.PARAMS.face.clipFrames[k][i]; if (!x.face || x.face.eyes !== e[0] || x.face.gaze !== e[1] || x.face.mouth !== e[2]) bad.push(f + '/' + k + '#' + i + ' face'); }); } }
    ok(bad.length === 0, '7 個生命感第二段 clip：art 規格（幀／fps／loop／可中斷／冷卻）一致、3 形態 _noface＋錨點齊、逐幀五官＝face_anchors', bad.slice(0, 8).join()); }
  // ── A3 心情步姿 ──
  { const g = (n) => BEH.gaitOf(BEH.create(1), mkS(n));
    ok(g({ mood: 90 }) === 'walk_happy' && g({ mood: 50, energy: 30 }) === 'walk_drag' && g({ mood: 50, hunger: 30 }) === 'walk_drag' && g({ mood: 50 }) === null && g({ mood: 70 }) === 'walk_happy' && g({ mood: 69 }) === null, 'A3 映射：心情 ≥70 → walk_happy；精力／飽腹 <40 → walk_drag；其餘 walk（art 次序）');
    const { b, ctx } = mk2({ mood: 50 }); BEH.force(b, 'react', ctx); run(b, ctx, 2.5); ok(BEH.gaitOf(b, ctx.s) === 'walk_happy', 'A3：emo_happy 後 10s 內 → walk_happy');
    run(b, ctx, 10); ok(BEH.gaitOf(b, ctx.s) === null, 'A3：emo_happy 10s 後回 walk');
    const sp = (n) => { const { b, ctx } = mk2(n); b.x = -60; BEH.force(b, 'walk', ctx); b.tx = 60; b.stopAt = null; const x0 = b.x, sh = new Set(); for (let i = 0; i < 60; i++) { BEH.step(b, ctx); sh.add(b.show.clip + '/' + b.clip); } return { v: (b.x - x0), sh: [...sh] }; };
    const n0 = sp({ mood: 55 }), nh = sp({ mood: 95 }), nd = sp({ mood: 55, energy: 20 });
    ok(Math.abs(nh.v / n0.v - 1.15) < 0.02 && Math.abs(nd.v / n0.v - 0.6) < 0.02, 'A3 位移：蓬跳 ×1.15、拖步 ×0.6（' + (nh.v / n0.v).toFixed(2) + '／' + (nd.v / n0.v).toFixed(2) + '）');
    ok(nh.sh.join() === 'walk_happy/walk' && nd.sh.join() === 'walk_drag/walk' && n0.sh.join() === 'walk/walk', 'A3 顯示層替身：狀態機 clip 仍係 walk（舊 gaze／A1 邏輯照用），show.clip＝walk_happy／walk_drag', JSON.stringify([nh.sh, nd.sh, n0.sh]));
    { const { b, ctx } = mk2({ mood: 95 }); BEH.force(b, 'walk', ctx); b.tx = b.x + 40; b.stopAt = null; BEH.step(b, ctx); BEH.step(b, ctx); ok(b.face.eyes === 'happy' && b.show.clip === 'walk_happy', 'A3 walk_happy 逐幀五官（happy 眼）'); }
  }
  // ── F3 小動作排程（2 小時 × 6 種子）──
  { let ok10 = true, okRep = true, kinds = {}, worst = 1e9, nv = 0;
    for (let sd = 1; sd <= 6; sd++) { const b = BEH.create(sd), s = mkS({ mood: 80 }), ctx = ctxAt(s, 14); run(b, ctx, 7200);
      const last = {}; for (const m of b.log.micro) { kinds[m.name] = (kinds[m.name] || 0) + 1; if (last[m.name] != null) { worst = Math.min(worst, m.t - last[m.name]); if (m.t - last[m.name] < 600 - 1e-6) ok10 = false; } last[m.name] = m.t; }
      // 抽籤出嚟嘅 idle 變體（唔計強制）唔連續兩次同一個
      const v = b.log.variants; nv += v.length; for (let i = 1; i < v.length; i++) if (v[i].name === v[i - 1].name) okRep = false; }
    ok(ok10, 'F3：同一小動作（scratch／sneeze／sniff／lookup／swat）≥10 分鐘唔重複（最短 ' + worst.toFixed(0) + 's）', JSON.stringify(kinds));
    ok(okRep && nv > 300, 'F3：唔連續兩次同一 idle 變體（' + nv + ' 次變體）');
    ok(kinds.scratch > 0 && kinds.sneeze > 0 && kinds.sniff > 0 && kinds.lookup > 0 && kinds.swat > 0, 'F3：5 款小動作都有出：' + JSON.stringify(kinds)); }
  { const b = BEH.create(1), hi = BEH.idleWeights(b, ctxAt(mkS({ mood: 90 }), 14)), lo = BEH.idleWeights(b, ctxAt(mkS({ mood: 30 }), 14)), mid = BEH.idleWeights(b, ctxAt(mkS({ mood: 55 }), 14));
    ok(hi.sway > mid.sway && lo.sway < mid.sway && hi.scratch > mid.scratch && lo.yawn > mid.yawn && mid.scratch === 12 && mid.sneeze === 8 && mid.blink === 50, 'F3 心情驅動變體：心情高 sway／scratch ↑，低 sway ↓ yawn ↑（基礎 50/30/20＋12/8）', JSON.stringify({ hi, mid, lo }));
    const pot = BEH.create(1); pot.x = P.potX + 5; const wp = BEH.idleWeights(pot, ctxAt(mkS({ mood: 55 }), 14)); const sun = BEH.create(1); sun.t = 100; sun.sunEndAt = 80; const wsun = BEH.idleWeights(sun, ctxAt(mkS({ mood: 55 }), 14));
    const nt = BEH.idleWeights(BEH.create(1), ctxAt(mkS({ mood: 55 }), 1));
    ok(wp.sneeze === 16 && wsun.sneeze === 16 && Math.abs(nt.sneeze - 12) < 1e-9, 'B2：近花盆／曬太陽後噴嚏 ×2、深夜（冷）×1.5');
    const cd = BEH.create(1); cd.t = 100; cd.microAt.scratch = 0; const wc = BEH.idleWeights(cd, ctxAt(mkS({ mood: 55 }), 14)); cd.t = 600.01; const wc2 = BEH.idleWeights(cd, ctxAt(mkS({ mood: 55 }), 14));
    ok(wc.scratch === 0 && wc2.scratch > 0, 'F3 冷卻：scratch 600s 內權重 0，過咗先返嚟');
    const rp = BEH.create(1); rp.lastIdle = 'sway'; ok(BEH.idleWeights(rp, ctxAt(mkS({ mood: 55 }), 14)).sway === 0, 'F3：上一個 idle 係 sway → 今次 sway 權重 0'); }
  // ── A2 中途停低：每段 walk 15%；夜晚 lookup ×3 ──
  { const save = LVP.microCooldown, cds = {}; LVP.microCooldown = 0; ['sniff', 'lookup', 'swat'].forEach(k => { cds[k] = D.CLIPS[k].cooldown; D.CLIPS[k].cooldown = 0; });
    const rate = (hr) => { let walks = 0, stops = 0, lk = 0; for (let sd = 1; sd <= 12; sd++) { const b = BEH.create(sd), s = mkS({ mood: 60 }), ctx = ctxAt(s, hr); run(b, ctx, 1800); walks += b.journal.length ? 0 : 0;
      walks += (b.log.enters.walk || 0) - b.log.micro.filter(m => m.from === 'walk').length; const st = b.log.micro.filter(m => m.from === 'walk'); stops += st.length; lk += st.filter(m => m.name === 'lookup').length; } return { r: stops / walks, lk: lk / Math.max(1, stops), stops, walks }; };
    const day = rate(14), night = rate(1);
    LVP.microCooldown = save; Object.keys(cds).forEach(k => D.CLIPS[k].cooldown = cds[k]);
    ok(day.r > 0.09 && day.r < 0.22, 'A2：每段 walk 約 15% 中途停低（日 ' + (day.r * 100).toFixed(1) + '%，' + day.stops + '/' + day.walks + '）');
    ok(day.lk > 0.2 && day.lk < 0.48 && night.lk > 0.5, 'A2：3 款平均抽（日 lookup ' + (day.lk * 100).toFixed(0) + '%）；深夜 lookup ×3（' + (night.lk * 100).toFixed(0) + '%）'); }
  { const { b, ctx } = mk2({ mood: 55 }); b.x = -50; BEH.force(b, 'walk', ctx); b.tx = 50; b.stopDir = 1; b.stopAt = -10; const seen = [];
    for (let i = 0; i < 60 * 12 && !(b.state === 'stay' && seen.includes('micro')); i++) { BEH.step(b, ctx); if (seen[seen.length - 1] !== b.state) seen.push(b.state); }
    ok(seen.join('>').indexOf('walk>micro>walk') === 0 && Math.abs(b.x - 50) < 1, 'A2：停低完繼續行去原目的地（' + seen.join('>') + '，x ' + b.x.toFixed(1) + '）'); }
  // ── 個性組合 ──
  const play = (name, needs, sec) => { const { b, ctx } = mk2(needs || { mood: 55 }); BEH.force(b, name, ctx); const tl = []; for (let i = 0; i < Math.round((sec || 6) / FIX); i++) { BEH.step(b, ctx); const k = b.show.clip + (b.seq && b.seq[b.seqI] && b.seq[b.seqI].tag ? ':' + b.seq[b.seqI].tag : ''); if (tl[tl.length - 1] !== k) tl.push(k); if (b.state !== 'micro') break; } return { b, ctx, tl }; };
  { const r = play('swat_miss'); const j = r.b.journal.filter(x => x.ev === 'micro').map(x => x.name + ':' + x.ph);
    ok(r.tl.join('>') === 'idle:notice>swat>emo_happy:smug>idle' && j.some(x => x === 'swat:miss'), '拍蟲撲空 → 得意擺 pose（' + r.tl.join('>') + '）');
    const { b, ctx } = mk2({ mood: 55 }); BEH.force(b, 'swat_miss', ctx); let smug = null, bugFlee = false, bugSeen = false;
    for (let i = 0; i < 240; i++) { BEH.step(b, ctx); if (b.bug) { bugSeen = true; if (b.bug.st === 'flee') bugFlee = true; } if (b.seq && b.seq[b.seqI].tag === 'smug' && !smug) smug = Object.assign({}, b.face); }
    ok(bugSeen && bugFlee && smug && smug.eyes === 'squint' && smug.mouth === 'squint' && smug.head === 'CR', '得意 pose：ω 嘴＋瞇眼＋頭微轉（缺 smug_pose 美術 → emo_happy 身體＋臉）；蟲仔飛走', JSON.stringify(smug));
    const h = play('swat_hit'); ok(h.tl.join('>') === 'idle:notice>swat>emo_happy:happy>idle', '拍中 → 開心（' + h.tl.join('>') + '）'); }
  { const r = play('sniff_sneeze'); const t = r.tl.join('>');
    ok(/^sniff>sneeze>(emo_surprised:surprised>)?sway:act_cool>idle$/.test(t), '嗅地 → 打噴嚏 → 扮冷靜（' + t + '）');
    const { b, ctx } = mk2(); BEH.force(b, 'sniff_sneeze', ctx); let cool = null; for (let i = 0; i < 400 && b.state === 'micro'; i++) { BEH.step(b, ctx); if (b.seq && b.seq[b.seqI].tag === 'act_cool') cool = Object.assign({}, b.face); }
    ok(cool && cool.eyes === 'squint' && cool.gaze === 'L' && cool.mouth === 'neutral', '扮冷靜：瞇眼望開（gaze L）（缺 act_cool 美術 → sway 身體）'); }
  { const r = play('lookup_tip'); const t = r.tl.join('>');
    ok(t === 'lookup>lookup:tip>wake:getup>sway:act_cool>idle', '望天 → 向後倒少少 → 起返身 → 扮冷靜（' + t + '）');
    const { b, ctx } = mk2(); BEH.force(b, 'lookup_tip', ctx); let maxRot = 0, held = 0; for (let i = 0; i < 300 && b.state === 'micro'; i++) { BEH.step(b, ctx); if (b.pose) maxRot = Math.max(maxRot, b.pose.rot); if (b.show.clip === 'lookup' && b.show.frame === 2 && !b.pose) held += FIX; }
    ok(maxRot > 0.15 && held >= 0.8, 'lookup 第 2 幀 hold ' + held.toFixed(2) + 's（≥0.8）；後仰程序化 pose（rot ' + maxRot.toFixed(2) + ' rad）'); }
  { const r = play('scratch'); const { b, ctx } = mk2(); BEH.force(b, 'scratch', ctx); const fr = []; for (let i = 0; i < 90 && b.state === 'micro'; i++) { BEH.step(b, ctx); if (b.state === 'micro' && fr[fr.length - 1] !== b.show.frame) fr.push(b.show.frame); }
    ok(fr.join('') === '0123452345', 'B1 抓癢：6 幀＋第 2–5 幀重播 1 次（' + fr.join('') + '）'); }
  { const n = { a: 0, s: 0 }; for (let sd = 1; sd <= 200; sd++) { const b = BEH.create(sd), s = mkS(), ctx = ctxAt(s, 14); run(b, ctx, 0.1); BEH.force(b, 'sneeze', ctx); n.a++; if (b.seq.some(x => x.clip === 'emo_surprised')) n.s++; }
    ok(n.s / n.a > 0.2 && n.s / n.a < 0.4, 'B2：噴嚏後 ~30% 接 emo_surprised（' + (n.s / n.a * 100).toFixed(0) + '%）'); }
  // ── 中斷規則 ──
  { const { b, ctx } = mk2(); b.lastTouch = b.t; BEH.force(b, 'scratch', ctx); run(b, ctx, 0.3); BEH.tap(b, 'pet', b.x + 5, -20); BEH.step(b, ctx); ok(b.state === 'react' && !b.seq && !b.faceAct, '抓癢可中斷：點寵物 → react（序列清走）');
    const B = mk2(); BEH.force(B.b, 'swat_miss', B.ctx); run(B.b, B.ctx, 0.55); BEH.tap(B.b, 'pet', B.b.x + 5, -20); BEH.step(B.b, B.ctx); ok(B.b.state === 'micro' && B.b.clip === 'swat', 'swat／sneeze 段不可中斷（忽略觸摸）');
    const C = mk2(); BEH.force(C.b, 'lookup', C.ctx); run(C.b, C.ctx, 0.3); C.s.sleeping = true; BEH.step(C.b, C.ctx); C.s.sleeping = false; ok(C.b.state === 'simsleep' && !C.b.seq, '事件／睡覺優先：小動作即刻讓路（F4 優先序）'); }
  // ── 確定性 ──
  { const r1 = (seed) => { const b = BEH.create(seed), s = mkS({ mood: 80 }), ctx = ctxAt(s, 14); run(b, ctx, 1800); return JSON.stringify(b.log.micro); };
    ok(r1(7) === r1(7) && r1(7) !== r1(8), '生命感排程：同種子一致、唔同種子唔同（mrng 獨立）'); }
}

console.log('# 生命感 s2b（遊美 live_s2 真 clip／步佐幀／即刻觸發／展示模式）');
{
  const LVP = P.live, S2C = ['smug_pose', 'act_cool', 'lookup_tip', 'getup', 'sniff_itch'];
  const mk2 = (needs, hour, seed) => { const b = BEH.create(seed || 13), s = mkS(needs), ctx = ctxAt(s, hour == null ? 14 : hour); run(b, ctx, 0.5); b.state = 'stay'; b.phase = ''; b.variant = null; b.x = 0; b.dir = 1; b.clip = 'idle'; return { b, s, ctx }; };
  const withReady = (fn) => { const sv = S2C.map(k => D.CLIPS[k].ready); S2C.forEach(k => D.CLIPS[k].ready = true); try { return fn(); } finally { S2C.forEach((k, i) => D.CLIPS[k].ready = sv[i]); } };
  const play = (name, needs, sec, seed) => { const { b, ctx } = mk2(needs || { mood: 55 }, 14, seed); BEH.force(b, name, ctx); const tl = []; for (let i = 0; i < Math.round((sec || 8) / FIX); i++) { BEH.step(b, ctx); const k = b.show.clip + (b.seq && b.seq[b.seqI] && b.seq[b.seqI].tag ? ':' + b.seq[b.seqI].tag : ''); if (tl[tl.length - 1] !== k) tl.push(k); if (b.state !== 'micro') break; } return { b, ctx, tl }; };
  // ── 資料：5 個 s2 clip 對齊 art CLIPS.json＋atlas_<form>_live_s2＋face_anchors ──
  { const LVD = path.join(root0, 'art/liveliness'), fa = JSON.parse(fs.readFileSync(path.join(LVD, 'face_anchors.json'), 'utf8')), cj = JSON.parse(fs.readFileSync(path.join(LVD, 'CLIPS.json'), 'utf8')); const bad = [];
    for (const k of S2C) { const a = cj.clips.find(c => c.name === k), d = D.CLIPS[k];
      if (!a || !d || !d.live || a.frames !== d.frames || a.fps !== d.fps || !!a.loop !== !!d.loop || a.interruptible !== d.interruptible || (a.cooldown_s || 0) !== (d.cooldown || 0) || a.next !== d.next || (a.holdLast_s || 0) !== (d.holdLast || 0)) bad.push('spec/' + k);
      for (const f of ['sprout', 'radiant', 'soft']) { const A = JSON.parse(fs.readFileSync(path.join(LVD, 'atlas_' + f + '_live_s2.json'), 'utf8')); const an = A.animations[k + '_noface'], anc = fa.anchors[f][k];
        if (!an || an.frames.length !== d.frames || !anc || anc.length !== d.frames) bad.push(f + '/' + k);
        else anc.forEach((x, i) => { const e = D.PARAMS.face.clipFrames[k][i]; if (!x.face || x.face.eyes !== e[0] || x.face.gaze !== e[1] || x.face.mouth !== e[2]) bad.push(f + '/' + k + '#' + i + ' face'); }); } }
    const ps = cj.faceKit && cj.faceKit.presets && cj.faceKit.presets.smug, mine = D.PARAMS.face.presets.smug;
    ok(bad.length === 0 && ps && ps.eyes === mine[0] && ps.mouth === mine[2] && D.PARAMS.face.clipFrames.smug_pose[3].join() === mine.join(), '5 個 s2 clip（smug_pose／act_cool／lookup_tip／getup／sniff_itch）：規格＋holdLast＋next 一致、3 形態 _live_s2 _noface＋錨點齊、逐幀五官＝face_anchors；preset smug＝sleepy＋C＋squint', bad.slice(0, 8).join() + JSON.stringify(ps));
    const lc = D.PARAMS.face.liveliness; ok(['sprout', 'radiant', 'soft'].every(f => lc.atlases[f].join() === 'atlas_' + f + '_live,atlas_' + f + '_live_s2' && (cj.forms[f].liveAtlas || []).join() === 'atlas_' + f + '_live.png,atlas_' + f + '_live_s2.png') && lc.fx === 'fx/atlas_fx_live', '引擎每 form 載 _live＋_live_s2（同 CLIPS.json forms[f].liveAtlas）；fx atlas＝fx/atlas_fx_live'); }
  { const fx = JSON.parse(fs.readFileSync(path.join(root0, 'art/liveliness/fx/atlas_fx_live.json'), 'utf8')), an = fx.animations.fx_bug;
    ok(an && an.frames.join() === 'fx_bug_01,fx_bug_02,fx_bug_03,fx_bug_02' && an.fps === 10 && an.loop && ['fx_bug_01', 'fx_bug_02', 'fx_bug_03'].every(k => fx.frames[k].frame.w === 8 && fx.frames[k].frame.h === 8 && fx.frames[k].pivotPx.x === 4 && fx.frames[k].pivotPx.y === 4), 'fx bug：8×8、3 幀、pivot (4,4)、01→02→03→02 loop 10fps'); }
  // ── 真 clip 取代 fallback（ready＝3 形態 atlas 齊；node 入面模擬 ready）──
  withReady(() => {
    { const r = play('swat_miss'); ok(r.tl.join('>') === 'idle:notice>swat>smug_pose:smug>idle', '真 clip：拍蟲撲空 → smug_pose（' + r.tl.join('>') + '）');
      const { b, ctx } = mk2(); BEH.force(b, 'swat_miss', ctx); const fr = []; let hold = 0, face = null, spark = false;
      for (let i = 0; i < 400 && b.state === 'micro'; i++) { BEH.step(b, ctx); if (b.show.clip === 'smug_pose') { if (fr[fr.length - 1] !== b.show.frame) fr.push(b.show.frame); if (b.show.frame === 3) { hold += FIX; face = Object.assign({}, b.face); } } if (b.fx.some(f => f.type === 'spark')) spark = true; }
      ok(fr.join('') === '0123' && hold >= 0.8 + 1 / 6 - 0.03 && hold < 1.2, 'smug_pose 4 幀 6fps，尾幀 hold（' + hold.toFixed(2) + 's ＝ 1/6＋holdLast 0.8）');
      ok(face && face.eyes === 'sleepy' && face.mouth === 'squint' && face.gaze === 'C' && !spark, 'smug_pose 尾幀臉＝preset smug（sleepy／C／squint）；唔再加程序化 spark（閃已烙入幀）', JSON.stringify(face)); }
    { const r = play('sniff_sneeze'); const t = r.tl.join('>');
      ok(/^sniff>sniff_itch:itch>sneeze>(emo_surprised:surprised>)?act_cool:act_cool>idle$/.test(t), '真 clip：sniff → sniff_itch → sneeze → act_cool（' + t + '）');
      const { b, ctx } = mk2(); BEH.force(b, 'sniff_sneeze', ctx); const seen = []; for (let i = 0; i < 400 && b.state === 'micro'; i++) { BEH.step(b, ctx); const k = b.show.clip + b.show.frame; if (seen[seen.length - 1] !== k) seen.push(k); }
      const j = seen.join(' '); ok(/sniff2 sniff_itch0 sniff_itch1 sneeze0/.test(j) && !/sniff3/.test(j), 'sniff 第 3 幀（索引 2）→ sniff_itch 2 幀 → 直接接 sneeze_01', j.slice(0, 120)); }
    { const r = play('lookup_tip'); const t = r.tl.join('>');
      ok(t === 'lookup>lookup_tip:tip>getup:getup>act_cool:act_cool>idle', '真 clip：望天 → lookup_tip → getup → act_cool（' + t + '）');
      const { b, ctx } = mk2(); BEH.force(b, 'lookup_tip', ctx); let pose = 0, gf = []; for (let i = 0; i < 600 && b.state === 'micro'; i++) { BEH.step(b, ctx); if (b.pose) pose++; if (b.show.clip === 'getup' && gf[gf.length - 1] !== b.show.frame) gf.push(b.show.frame); }
      ok(pose === 0 && gf.join('') === '0123', '真 lookup_tip／getup 唔再用程序化後仰 pose；getup 4 幀播晒'); }
  });
  { const r = play('swat_miss'); ok(r.tl.join('>') === 'idle:notice>swat>emo_happy:smug>idle', '未 ready（dust／?live=0）：smug 仍用 emo_happy fallback'); }
  // ── 步佐幀（0-based）──
  { const steps = (needs) => { const { b, ctx } = mk2(needs); b.x = -60; BEH.force(b, 'walk', ctx); b.tx = 60; b.stopAt = null; const out = {}; for (let i = 0; i < 60 * 4; i++) { const n0 = b.journal.length; BEH.step(b, ctx); for (const e of b.journal.slice(n0)) if (e.ev === 'sfx') (out[e.name] = out[e.name] || new Set()).add(b.show.frame); } const o = {}; for (const k in out) o[k] = [...out[k]].sort().join(','); return o; };
    const h = steps({ mood: 95 }), d = steps({ mood: 55, energy: 20 });
    ok(h.step_hop === '0,3' && !h.step_drag, 'walk_happy 落地聲喺幀 0、3（2、5 係最高點）', JSON.stringify(h));
    ok(d.step_drag === '1,4' && d.step_plod === '2,5', 'walk_drag：拖地聲 1、4；踏地聲 2、5', JSON.stringify(d)); }
  // ── 即刻觸發（唔理冷卻／機率）──
  { const want = { sniff: 'sniff', lookup: 'lookup', swat: 'swat', scratch: 'scratch', sneeze: 'sneeze', smug: 'emo_happy' }, bad = [];
    for (const k of Object.keys(want)) { const { b, ctx } = mk2(); b.t = 50; for (const m of ['scratch', 'sneeze', 'sniff', 'lookup', 'swat']) b.microAt[m] = 49;   // 全部啱啱做完（冷卻中）
      BEH.force(b, 'now_' + k, ctx); const seen = new Set(); for (let i = 0; i < 90 && b.state === 'micro'; i++) { BEH.step(b, ctx); seen.add(b.show.clip); } if (!seen.has(want[k])) bad.push(k + ':' + [...seen].join('/')); }
    ok(bad.length === 0, '即刻觸發 6 個小動作掣：冷卻中照即刻出對應 clip（smug 未 ready → emo_happy fallback）', bad.join());
    const okR = withReady(() => { const { b, ctx } = mk2(); BEH.force(b, 'now_smug', ctx); BEH.step(b, ctx); return b.show.clip === 'smug_pose' && b.seq[b.seqI].tag === 'smug'; }); ok(okR, 'smug 掣：ready 時出真 smug_pose');
    let miss = 0, n = 0, sn = 0, tip = 0; for (let sd = 1; sd <= 60; sd++) { const a = play('now_swat', null, 8, sd); n++; if (a.tl.some(x => /:smug$/.test(x))) miss++; const c = play('now_sniff', null, 8, sd); if (c.tl.includes('sneeze')) sn++; const l = play('now_lookup', null, 8, sd); if (l.tl.some(x => /:tip$/.test(x))) tip++; }
    ok(miss / n > 0.6 && miss / n < 0.95 && sn / n > 0.25 && sn / n < 0.65 && tip / n > 0.3 && tip / n < 0.7, '個性鏈照接：拍蟲撲空→得意 ' + miss + '/60、嗅地→噴嚏 ' + sn + '/60、望天→後倒 ' + tip + '/60（機率照 LV）'); }
  { const gait = (k, needs) => { const { b, ctx } = mk2(needs || { mood: 55 }); b.x = 0; BEH.force(b, 'now_' + k, ctx); let walkT = 0, sh = new Set(), x0 = b.x, moved = 0, last = b.x; for (let i = 0; i < 60 * 8; i++) { BEH.step(b, ctx); if (b.state === 'walk') { walkT += FIX; sh.add(b.show.clip); moved += Math.abs(b.x - last); } last = b.x; if (b.state !== 'walk' && walkT > 0) break; } return { walkT, sh: [...sh].join(), moved, inRange: b.x >= P.rangeX[0] && b.x <= P.rangeX[1] }; };
    const h = gait('happy'), d = gait('drag'), h2 = gait('happy', { mood: 20, energy: 20 });
    ok(h.sh === 'walk_happy' && h.walkT >= 4 - 0.05 && h.walkT <= 6 + 0.05 && h.moved > 60 && h.inRange, '開心步掣：即刻用 walk_happy 行 ' + h.walkT.toFixed(2) + 's（4–6s，行 ' + h.moved.toFixed(0) + 'px，到盡頭掉頭）');
    ok(d.sh === 'walk_drag' && d.walkT >= 4 - 0.05 && d.walkT <= 6 + 0.05 && d.inRange, '拖步掣：即刻用 walk_drag 行 ' + d.walkT.toFixed(2) + 's');
    ok(h2.sh === 'walk_happy', '步姿掣蓋過需求（攰都照蓬跳）');
    const { b, ctx } = mk2(); BEH.force(b, 'now_happy', ctx); run(b, ctx, 1); BEH.tap(b, 'pet', b.x + b.dir * 5, -20); BEH.step(b, ctx); ok(!b.gaitForce, '步姿掣行緊被點 → 交返正常流程（gaitForce 清走）'); }
  // ── 展示模式（頻率 ×5／冷卻 ÷5）──
  const hour2 = (demo) => { let micro = 0, stops = 0, walks = 0, worst = 1e9; for (let sd = 1; sd <= 6; sd++) { const b = BEH.create(sd), s = mkS({ mood: 60 }), ctx = ctxAt(s, 14); b.demo = demo; run(b, ctx, 3600);
    micro += b.log.micro.length; const st = b.log.micro.filter(m => m.from === 'walk').length; stops += st; walks += (b.log.enters.walk || 0) - st;
    const last = {}; for (const m of b.log.micro) { if (last[m.name] != null) worst = Math.min(worst, m.t - last[m.name]); last[m.name] = m.t; } } return { micro, stops, walks, r: stops / Math.max(1, walks), worst }; };
  { const off = hour2(false), on = hour2(true);
    ok(on.micro >= off.micro * 3, '展示模式：小動作頻率大升（6 種子 × 1 小時：' + off.micro + ' → ' + on.micro + '，×' + (on.micro / off.micro).toFixed(1) + '）');
    ok(on.worst >= 600 / 5 - 1e-6 && on.worst < 600, '展示模式：同一小動作冷卻 ÷5（最短 ' + on.worst.toFixed(0) + 's ≥120）');
    const b = BEH.create(1), c = ctxAt(mkS({ mood: 55 }), 14); const w0 = BEH.idleWeights(b, c); b.demo = true; const w1 = BEH.idleWeights(b, c); b.t = 130; b.microAt.scratch = 0; const rdy = BEH.idleWeights(b, c).scratch > 0; b.demo = false; const w2 = BEH.idleWeights(b, c);
    ok(w1.scratch === w0.scratch * 5 && w1.sneeze === w0.sneeze * 5 && w1.blink === w0.blink && rdy && w2.scratch === 0 && BEH.idleWeights(BEH.create(1), c).scratch === w0.scratch, '展示模式：scratch／sneeze 權重 ×5、130s 已過冷卻；關返即刻回 600s 冷卻＋原權重', JSON.stringify({ w0, w1 }));
    const sv = LVP.microCooldown, cds = {}; LVP.microCooldown = 0; ['sniff', 'lookup', 'swat'].forEach(k => { cds[k] = D.CLIPS[k].cooldown; D.CLIPS[k].cooldown = 0; });
    const offS = hour2(false), onS = hour2(true); LVP.microCooldown = sv; Object.keys(cds).forEach(k => D.CLIPS[k].cooldown = cds[k]);
    ok(onS.r > 0.6 && offS.r < 0.22, '展示模式：中途停步 15% → ×5（' + (offS.r * 100).toFixed(0) + '% → ' + (onS.r * 100).toFixed(0) + '%）');
    const base = (() => { const b = BEH.create(7), s = mkS({ mood: 80 }), ctx = ctxAt(s, 14); run(b, ctx, 1800); return JSON.stringify(b.log.micro.map(m => m.name)); })(), base2 = (() => { const b = BEH.create(7), s = mkS({ mood: 80 }), ctx = ctxAt(s, 14); run(b, ctx, 1800); return JSON.stringify(b.log.micro.map(m => m.name)); })();
    ok(base === base2 && BEH.create(1).demo === false && off.micro * 3 <= on.micro, '展示模式預設關（create().demo＝false）：正常排程不變＋確定性（6 種子 1 小時 ' + off.micro + ' 個小動作）'); }
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

console.log('# 生命感第三段（D3 長按磨蹭／D5 久別重逢衝埋嚟／G1 燈泡）');
{
  const LVP = P.live, S3C = ['nuzzle', 'rush', 'act_cool'];
  const mk3 = (needs, seed) => { const b = BEH.create(seed || 21), s = mkS(needs || { mood: 55 }), ctx = ctxAt(s, 14); run(b, ctx, 0.5); b.state = 'stay'; b.phase = ''; b.variant = null; b.x = 0; b.dir = 1; b.clip = 'idle'; return { b, s, ctx }; };
  const withReady = (fn, on) => { const sv = S3C.map(k => D.CLIPS[k].ready); S3C.forEach(k => D.CLIPS[k].ready = on !== false); try { return fn(); } finally { S3C.forEach((k, i) => D.CLIPS[k].ready = sv[i]); } };
  const tagOf = (b) => b.show.clip + (b.state === 'micro' && b.seq && b.seq[b.seqI] && b.seq[b.seqI].tag ? ':' + b.seq[b.seqI].tag : b.state === 'nuzzle' ? ':' + b.phase : '');
  // ── 資料：nuzzle／rush 對齊 art CLIPS.json＋atlas_<form>_live＋face_anchors；缺 nuzzle_purr／reunion_happy ──
  { const LVD = path.join(root0, 'art/liveliness'), fa = JSON.parse(fs.readFileSync(path.join(LVD, 'face_anchors.json'), 'utf8')), cj = JSON.parse(fs.readFileSync(path.join(LVD, 'CLIPS.json'), 'utf8')); const bad = [];
    for (const k of ['nuzzle', 'rush']) { const a = cj.clips.find(c => c.name === k), d = D.CLIPS[k];
      if (!a || !d || !d.live || a.frames !== d.frames || a.fps !== d.fps || !!a.loop !== !!d.loop || a.priority !== d.priority || a.interruptible !== d.interruptible || (a.cooldown_s || 0) !== (d.cooldown || 0) || a.next !== d.next) bad.push('spec/' + k);
      if (k === 'rush' && (d.loopRange || []).join() !== (a.loopRange || []).join()) bad.push('loopRange');
      if (k === 'nuzzle') { const at = a.attachments[0], m = d.attach[0]; if (!at || !m || at.prop !== m.prop || at.anchor !== m.anchor || at.startFrame !== m.from) bad.push('attach'); }
      for (const f of ['sprout', 'radiant', 'soft']) { const A = JSON.parse(fs.readFileSync(path.join(LVD, 'atlas_' + f + '_live.json'), 'utf8')); const an = A.animations[k + '_noface'], anc = fa.anchors[f][k];
        if (!an || an.frames.length !== d.frames || !anc || anc.length !== d.frames) bad.push(f + '/' + k);
        else anc.forEach((x, i) => { const e = D.PARAMS.face.clipFrames[k][i]; if (!x.face || x.face.eyes !== e[0] || x.face.gaze !== e[1] || x.face.mouth !== e[2] || !x.bulb) bad.push(f + '/' + k + '#' + i); }); } }
    ok(bad.length === 0, 'nuzzle／rush：規格（幀／fps／loop／priority／next／loopRange／heart attach）＝art CLIPS.json；3 形態 _live atlas _noface 6 幀＋逐幀五官＝face_anchors＋燈泡錨點', bad.slice(0, 8).join());
    ok(!cj.clips.find(c => c.name === 'nuzzle_purr') && !cj.clips.find(c => c.name === 'reunion_happy') && !D.CLIPS.nuzzle_purr && !D.CLIPS.reunion_happy, '缺美術（轉遊美）：nuzzle_purr／reunion_happy 冇 clip → 用 fallback'); 
    ok(BEH.NOW.includes('nuzzle') && BEH.NOW.includes('reunion') && LVP.reunionAwayH === 6 && LVP.nuzzleHoldMs === 400, 'NOW 加 nuzzle／reunion；離線門檻 6h（art trigger）；長按 0.4s'); }
  withReady(() => {
    // ── D3：撳住 → 轉向手指、挨埋、nuzzle 循環＋heart（第 1 幀起）→ 1.2s 呼嚕 → 鬆手播完當前幀 → 扮冇事 ──
    { const { b, ctx } = mk3(); run(b, ctx, 0.1);
      const x0 = b.x; BEH.nuzzle(b, -14, -20); BEH.step(b, ctx);
      ok(b.state === 'nuzzle' && b.dir === -1 && b.clip === 'nuzzle' && !b.turn, '撳住 0.4s（手指喺左）→ nuzzle，轉向手指（scaleX −1；唔計 D2 回頭）', JSON.stringify({ s: b.state, d: b.dir, c: b.clip }));
      let heart0 = null, heart1 = false, purrT = null, moved = 0, face = null; const fr = [];
      for (let i = 0; i < Math.round(2 / FIX); i++) { BEH.step(b, ctx); if (fr[fr.length - 1] !== b.frame) fr.push(b.frame); if (b.frame === 0 && heart0 == null) heart0 = b.attach.some(a => a.prop === 'heart'); if (b.frame >= 1 && b.attach.some(a => a.prop === 'heart')) heart1 = true; if (purrT == null && b.phase === 'purr') { purrT = b.t; } if (b.phase === 'purr') face = Object.assign({}, b.face); moved = Math.max(moved, Math.abs(b.x - x0)); }
      const purrSfx = b.journal.filter(j => j.ev === 'sfx' && j.name === 'nuzzle_purr').length;
      ok(fr.slice(0, 7).join('') === '0123450' && heart0 === false && heart1, 'nuzzle 6 幀 6fps 循環；heart 由第 1 幀起（head_r）', fr.join(''));
      ok(moved > 2 && moved <= LVP.nuzzleStep + 0.01 && b.dir === -1, '挨埋手指（行 ' + moved.toFixed(1) + 'px ≤ 10，保持望住手指）');
      ok(purrT != null && purrSfx >= 1 && face && face.eyes === 'happy' && face.mouth === 'happy', '撳 ≥1.2s → 呼嚕：purr 聲＋閉眼開心臉（缺 nuzzle_purr 美術 → nuzzle 身體＋臉）', JSON.stringify(face));
      ok(BEH.weights && b.state === 'nuzzle', '撳住期間持續磨蹭（2s 後仍然 nuzzle）');
      const relFr = b.frame; BEH.nuzzleEnd(b); BEH.step(b, ctx); const endT = b.t; let left = null;
      for (let i = 0; i < 60 && left == null; i++) { BEH.step(b, ctx); if (b.state !== 'nuzzle') left = b.t; }
      ok(left != null && left - endT <= 1 / 6 + 0.02, '鬆手 → 播完當前幀（第 ' + relFr + ' 幀）先離開（' + ((left - endT) * 1000).toFixed(0) + 'ms ≤ 1 幀）'); }
    { let cool = 0, idle = 0, chains = new Set();
      for (let seed = 1; seed <= 40; seed++) { const { b, ctx } = mk3(null, seed); BEH.nuzzle(b, b.x + 14, -20); run(b, ctx, 1.4); BEH.nuzzleEnd(b); const tl = [];
        for (let i = 0; i < 400; i++) { BEH.step(b, ctx); const k = tagOf(b); if (tl[tl.length - 1] !== k) tl.push(k); if (b.state === 'stay') break; }
        if (tl.join('>').includes('act_cool')) { cool++; chains.add(tl.join('>')); } else idle++; }
      ok(cool >= 22 && cool <= 38 && idle >= 2, '個性：磨蹭完 ~75% 扮冇事（呆一呆 → act_cool）（' + cool + '/40；' + [...chains][0] + '）');
      ok([...chains].every(c => /idle:blank>act_cool:act_cool/.test(c)), '扮冇事鏈＝blank（望鏡頭冇表情）→ 真 act_cool', [...chains].join(' | ')); }
    { const { b, ctx } = mk3(); BEH.nuzzle(b, 14, -20); run(b, ctx, 0.3); BEH.nuzzleEnd(b); run(b, ctx, 2);
      ok(b.journal.filter(j => j.ev === 'micro' && j.name === 'nuzzle_end' && j.ph === 'idle').length === 1, '磨蹭 <0.8s 就鬆手 → 唔扮冇事，直接回 idle'); }
    { const { b, ctx } = mk3(); BEH.force(b, 'now_nuzzle', ctx); const st0 = b.state; run(b, ctx, LVP.nowNuzzleSec + 0.3); const tl = b.log.micro.map(m => m.name);
      ok(st0 === 'nuzzle' && tl.includes('nuzzle_cool'), '即刻觸發 nuzzle：自動撳住 ' + LVP.nowNuzzleSec + 's 再鬆手 → 一定扮冇事', tl.join()); }
    // 唔得磨蹭：瞓覺（sim）／鬧脾氣／蛋 → 撳住等；鬆手取消
    { const { b, ctx } = mk3(); BEH.force(b, 'grumpy', ctx); BEH.nuzzle(b, 14, -20); run(b, ctx, 0.3); const g = b.state; BEH.nuzzleEnd(b); run(b, ctx, 5);
      ok(g === 'grumpy' && b.state !== 'nuzzle' && !b.nuzzleReq, '鬧脾氣中撳住唔會磨蹭；鬆手就取消（唔會遲咗先蹭）');
      const m = mk3(); m.s.sleeping = true; BEH.nuzzle(m.b, 14, -20); run(m.b, m.ctx, 0.5); ok(m.b.state !== 'nuzzle', '瞓覺（sim）唔磨蹭'); BEH.nuzzleEnd(m.b); }
    // ── D5：rush 第 1 幀起步 → 2–5 循環跑 → 衝過頭 → 第 6 幀煞停 → act_cool → 行返中間 → 重逢（cheer_jump 跳 2 下＋心心＋reunion 聲）──
    { const { b, ctx } = mk3(); b.x = 20; BEH.force(b, 'now_reunion', ctx); const x0 = b.x, d0 = b.dir; const tl = [], runFr = new Set(); let minX = 99, maxLift = 0, brakeFr = null, hearts = 0, T = 0, startFr = null;
      for (let i = 0; i < Math.round(8 / FIX) && b.state === 'micro'; i++) { BEH.step(b, ctx); T += FIX; const k = tagOf(b); if (tl[tl.length - 1] !== k) tl.push(k);
        const tg = b.seq && b.seq[b.seqI] && b.seq[b.seqI].tag; if (tg === 'rush_start' && startFr == null) startFr = b.frame; if (tg === 'rush') runFr.add(b.frame); if (tg === 'brake') brakeFr = b.frame;
        minX = Math.min(minX, b.x); maxLift = Math.min(maxLift, b.lift); hearts += b.fx.filter(f => f.type === 'heart').length; b.fx.length = 0; }
      ok(x0 === P.rangeX[1] && d0 === -1, '由場邊（遠嗰邊 x=' + x0 + '）向中間衝');
      ok(tl.join('>') === 'rush:rush_start>rush:rush>rush:brake>act_cool:act_cool>walk:back>cheer_jump:reunion_happy>idle', '重逢鏈：' + tl.join('>'));
      ok(startFr === 0 && [...runFr].sort().join('') === '1234' && brakeFr === 5, 'rush：第 1 幀起步、2–5 幀循環（loopRange [1,4]）、第 6 幀煞停', startFr + '/' + [...runFr].join('') + '/' + brakeFr);
      ok(minX <= -LVP.rushOvershoot + 0.1 && Math.abs(b.x) <= P.arriveEps + 0.01, '衝過頭（去到 x=' + minX.toFixed(1) + '）→ 煞停 → 行返中間（x=' + b.x.toFixed(1) + '）');
      ok(maxLift < -3 && hearts >= 2, '開心重逢（缺 reunion_happy → cheer_jump 跳 ' + LVP.reunionHops + ' 下＋心心 ' + hearts + '）');
      const sf = b.journal.filter(j => j.ev === 'sfx').map(j => j.name);
      ok(sf.filter(n => n === 'reunion_happy').length === 1 && sf.includes('step_drag') && sf.filter(n => n === 'step_hop').length >= 3, 'sfx：跑步 step_hop、煞停 step_drag、重逢 reunion_happy ×1');
      ok(T < 7 && b.state === 'stay', '全程 ' + T.toFixed(1) + 's 完返 stay'); }
    { const { b, ctx } = mk3(); b.x = -30; BEH.force(b, 'now_reunion', ctx); BEH.step(b, ctx); ok(b.x === P.rangeX[0] && b.dir === 1, '喺左邊 → 由左邊場邊衝入（向右）'); }
    { const { b, ctx } = mk3(); BEH.force(b, 'now_reunion', ctx); run(b, ctx, 1); const n0 = b.log.enters.tapIgnored || 0; BEH.tap(b, 'pet', b.x, -20); run(b, ctx, 0.1);
      ok((b.log.enters.tapIgnored || 0) === n0 + 1 && b.state === 'micro', '衝緊／煞停中唔可中斷（點佢只會望）'); }
  });
  // fallback（?live=0／dust）：冇 nuzzle／rush 美術
  withReady(() => {
    const { b, ctx } = mk3(); BEH.nuzzle(b, 14, -20); BEH.step(b, ctx); ok(b.state === 'nuzzle' && b.clip === 'emo_cuddly', 'fallback：缺 nuzzle → emo_cuddly 身體');
    BEH.nuzzleEnd(b); run(b, ctx, 3);
    const m = mk3(); BEH.force(m.b, 'now_reunion', m.ctx); const tl = []; for (let i = 0; i < 600 && m.b.state === 'micro'; i++) { BEH.step(m.b, m.ctx); const k = tagOf(m.b); if (tl[tl.length - 1] !== k) tl.push(k); }
    ok(tl.join('>') === 'walk:rush_start>walk:rush>walk:brake>sway:act_cool>walk:back>cheer_jump:reunion_happy>idle', 'fallback：缺 rush → 快行（walk）＋煞停 squash＋扮冷靜（sway）', tl.join('>'));
  }, false);
}

console.log(`\n結果：${pass} 通過，${fail} 失敗`);
process.exit(fail ? 1 : 0);
