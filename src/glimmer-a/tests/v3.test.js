/* v3.test — #83 HD-2D V3 接入：petGlow 狀態機（瞓／夢 0＋600ms 淡出、醒 400ms 淡入＋1→1.15→1、眼瞓 .6）、?v3=0 開關、
   散步 walk_bg 日／黃昏／夜跟鐘、屋仔寵物光（醒 1／眼瞓 .6／床 0）、窗光 petAtten .6、UI kit 對比＋字最細 18@3x、美術齊（四季×H1–H4、
   icon 冇 @2x、OFL 字型 subset）。node tests/v3.test.js */
const fs = require('fs'), path = require('path');
const V3 = require('../src/v3.js'), WK = require('../src/walkv3.js'), HV = require('../src/housev3.js'), UI = require('../src/uiv3.js');
const ART = path.join(__dirname, '../art/v3');
let pass = 0, fail = 0; const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const near = (a, b, e) => Math.abs(a - b) <= (e || 0.01);
const J = (p) => JSON.parse(fs.readFileSync(path.join(ART, p), 'utf8'));

console.log('① petGlow 狀態值');
ok(V3.STATES.awake === 1 && V3.STATES.sleepy === 0.6 && V3.STATES.drowsy === 0.6 && V3.STATES.sleep === 0 && V3.STATES.dreaming === 0 && V3.STATES.dreamEnter === 0, '醒 1／眼瞓 .6／瞓、夢 0');
ok(V3.T.out === 600 && V3.T.in === 400 && V3.T.pulseK === 1.15, '淡出 600ms／淡入 400ms／脈衝 1.15');
console.log('② 淡出／淡入曲線');
{ const g = new V3.Glow('awake', 0); g.set('sleep', 1000);
  ok(near(g.value(1000), 1) && g.value(1300) < 1 && g.value(1300) > 0 && near(g.value(1600), 0) && near(g.value(5000), 0), '醒→瞓：600ms 淡到 0', [g.value(1300)]);
  g.set('awake', 6000); const v = (t) => g.value(6000 + t);
  ok(near(v(0), 0) && v(200) > 0.5 && v(200) < 1 && near(v(400), 1), '瞓→醒：400ms easeOutQuad 0→1', [v(200)]);
  ok(near(v(475), 1.15) && near(v(550), 1) && near(v(2000), 1), '之後 1→1.15→1', [v(475), v(550)]);
  const d = new V3.Glow('awake', 0); d.set('drowsy', 0); ok(near(d.value(300), 0.6) && near(d.value(9999), 0.6), '眼瞓 → 60%');
  const z = new V3.Glow('awake', 0); z.set('bogus', 0); ok(z.state === 'awake', '唔識嘅狀態唔郁'); }
console.log('③ 團絨／細佬狀態對應');
ok(V3.petState({ sleeping: true }, {}) === 'sleep' && V3.petState({}, {}, { dreaming: true }) === 'dreaming', '瞓覺／夢遊 → 0 狀態');
ok(V3.petState({}, { clip: 'yawn' }) === 'sleepy' && V3.petState({}, { clip: 'fall_asleep' }) === 'sleepClip' && V3.petState({}, { clip: 'idle' }) === 'awake', 'yawn → .6；入瞓 clip → 0；idle → 1');
ok(V3.kidState('sleep') === 'sleep' && V3.kidState('walk', true) === 'sleep' && V3.kidState('walk') === 'awake', '細佬：瞓 → 0');
console.log('④ ?v3=0');
ok(V3.wanted(new URLSearchParams('')) && !V3.wanted(new URLSearchParams('v3=0')) && V3.wanted(new URLSearchParams('v3=1')) && V3.wanted(null), '預設開；?v3=0 返 6b.3 樣');
console.log('⑤ 散步 walk_bg 跟現實時間');
ok(WK.variantOf(6) === 'day' && WK.variantOf(13) === 'day' && WK.variantOf(16.99) === 'day' && WK.variantOf(17) === 'dusk' && WK.variantOf(18.5) === 'dusk' && WK.variantOf(19) === 'night' && WK.variantOf(2) === 'night' && WK.variantOf(5.9) === 'night' && WK.variantOf(-1) === 'night', '6–17 日／17–19 黃昏／其他夜');
for (const v of ['day', 'dusk', 'night']) { const d = path.join(ART, 'walk/walk_bg', v); ok(fs.existsSync(d) && fs.readdirSync(d).length > 0, 'walk_bg ' + v + ' 有圖'); }
{ const s = WK.stoneOf(5, 6); ok(s.cur === 2 && WK.stoneOf(99, 6).cur === 5, '石光：而家格 floor(tile/2)，封頂'); }
console.log('⑥ 屋仔寵物光／窗光');
ok(HV.houseState({ mode: 'sleep' }) === 'sleep' && HV.houseState({ mode: 'free' }, true) === 'sleepy' && HV.houseState({ mode: 'free' }) === 'awake', '床 0／眼瞓 .6／醒 1');
ok(V3.STATES[HV.houseState({ mode: 'sleep' })] === 0 && V3.STATES[HV.houseState({}, true)] === 0.6 && V3.STATES[HV.houseState({})] === 1, '屋仔光值 1／.6／0');
ok(HV.inPoly(5, 5, [[0, 0], [10, 0], [10, 10], [0, 10]]) && !HV.inPoly(15, 5, [[0, 0], [10, 0], [10, 10], [0, 10]]), '粒子多邊形 inPoly');
{ let bad = []; for (const r of fs.readdirSync(path.join(ART, 'house/rooms'))) for (const v of ['day', 'night']) { const g = J('house/rooms/' + r + '/' + v + '/grade.json'); const wb = g.v3 && g.v3.windowBeam; if (!wb || wb.petAtten !== 0.6) bad.push(r + v); }
  ok(!bad.length, '每間房 grade petAtten .6', bad); }
{ const F = J('house/furniture_v3.json'), wins = Object.entries(F.furniture).filter(([, m]) => m.slot === 'window' && m.windowLight); ok(wins.length + (F.windowNone ? 1 : 0) >= 3, '窗光 3 款（窗位家具／冇窗）', wins.length);
  const lamps = Object.entries(F.furniture).filter(([, m]) => m.light); ok(lamps.length > 0 && lamps.every(([, m]) => m.light.petGlow === false || m.light.petGlow == null), '燈／場景光唔跟 petGlow（唔熄）'); }
console.log('⑦ UI kit：字＋對比');
ok(UI.MIN3X === 18 && Object.values(UI.TYPE).every(t => t.px3x >= 18), '字最細 18@3x');
ok(UI.cr(UI.C.cream, UI.C.navy) >= 4.5 && UI.cr(UI.C.ink, UI.C.gold) >= 4.5 && UI.cr(UI.C.mute, UI.C.navy) >= 4.5 && UI.cr(UI.C.goldhi, UI.C.navy) >= 4.5, '主要字色對比 ≥4.5');
ok(UI.textOn(UI.C.gold, 'btn_primary') === 'ink' && UI.textOn(UI.C.navy, 'panel') === 'cream' && UI.textOn(UI.C.gold, 'btn_primary_dis') === 'cream', '彩色掣 ink、深底 cream、dis cream');
{ const M = J('ui/atlas/v2_to_v3_map.json').map, FR = J('ui/atlas/ui_hd2d_v3@3x.json').frames, IC = J('ui/atlas/icons_hd2d_v3@3x.json').frames;
  const bad = Object.keys(M).filter(n => M[n].v3 && UI.v3name(M, FR, IC, n) == null && UI.v3name(M, FR, IC, n, true) == null);
  ok(!bad.length, 'v2→v3 對照表每個目標都喺 atlas（' + Object.keys(M).length + '）', bad.slice(0, 5)); }
ok(!fs.readdirSync(path.join(ART, 'ui/atlas')).some(f => /@2x/.test(f)), 'icon 冇 @2x');
for (const f of ['GenWanMin2TC-R.subset.otf', 'GenWanMin2TC-SB.subset.otf', 'OFL_GenWanMin2.txt']) ok(fs.existsSync(path.join(ART, 'ui/fonts', f)), 'OFL 字型 ' + f);
console.log('⑧ 花園 V3：H1–H4＋四季 16 款');
for (const h of ['H1', 'H2', 'H3', 'H4']) ok(fs.existsSync(path.join(ART, 'garden', h)), '花園 ' + h);
{ const miss = []; for (const s of ['spring', 'summer', 'autumn', 'winter']) for (const h of ['H1', 'H2', 'H3', 'H4']) if (!fs.existsSync(path.join(ART, 'garden/seasons', s, h))) miss.push(s + h); ok(!miss.length, '四季 × H1–H4 ＝ 16 款', miss); }
for (const p of ['tuanrong', 'kid']) ok(fs.existsSync(path.join(ART, 'petglow', p)), 'petGlow ' + p);
console.log('⑨ 唔用第三方素材');
{ const src = fs.readFileSync(path.join(ART, 'SOURCE.txt'), 'utf8'); ok(/art\/workscenes-v3/.test(src) && !/octopath|八方旅人/i.test(src), '來源：自家 art/workscenes-v3'); }

console.log('\n' + pass + ' passed, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
