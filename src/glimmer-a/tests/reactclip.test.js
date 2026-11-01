/* 遊美 batch3a 反應 clip 測試（Node 無依賴）：node tests/reactclip.test.js ——reactclip 純函數＋art/reactions 資料完整性＋MOTIONS 對應 */
const fs = require('fs'), path = require('path');
const RC = require('../src/reactclip.js'); const D = require('../src/data.js'); const T = require('../src/touch.js');
const ROOT = path.join(__dirname, '..'), RX = path.join(ROOT, 'art/reactions');
let pass = 0, fail = 0;
function ok(c, name, info) { if (c) { pass++; console.log('  ✓ ' + name); } else { fail++; console.log('  ✗ ' + name + (info !== undefined ? ' — ' + JSON.stringify(info) : '')); } }
const near = (a, b, e) => Math.abs(a - b) <= (e || 1e-6);
const J = (p) => JSON.parse(fs.readFileSync(path.join(RX, p), 'utf8'));
const pngWH = (p) => { const b = fs.readFileSync(p); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };

console.log('— reactclip 純函數');
const c1 = { dur: 1000, body: [{ t: 0 }, { t: 500, sx: 2, rot: 90, e: 'linear' }, { t: 1000, e: 'in' }] };
let b = RC.bodyAt(c1, 0); ok(b.sx === 1 && b.sy === 1 && b.rot === 0 && b.x === 0 && b.flip === 0, '第一格預設值');
b = RC.bodyAt(c1, 250); ok(near(b.sx, 1.5) && near(b.rot, 45), 'linear 中間插值', b);
b = RC.bodyAt(c1, 750); ok(near(b.sx, 2) && near(b.rot, 90), '缺欄沿用上一格（t1000 冇 sx／rot → 保持）', b);
const c2 = { dur: 100, body: [{ t: 0, y: 0 }, { t: 100, y: 10, e: 'in' }] };
ok(near(RC.bodyAt(c2, 50).y, 2.5), 'easing 用下一格 e（in：0.5²×10）', RC.bodyAt(c2, 50));
ok(near(RC.EASE.inout(0.5), 0.5) && near(RC.EASE.outBack(1), 1) && RC.EASE.step(0.99) === 0, 'EASE 端點');
const c3 = { dur: 1000, rotStep: 45, body: [{ t: 0 }, { t: 1000, rot: -360 }] };
ok(RC.bodyAt(c3, 300).rot % 45 === 0, 'rotStep 45 snap', RC.bodyAt(c3, 300));
ok(RC.evalClip(c3, 300, { rotStep: 90 }).body.rot % 90 === 0, 'opt.rotStep 90 覆蓋', RC.evalClip(c3, 300, { rotStep: 90 }).body);
ok(RC.trackAt([{ t: 0, f: ['a', 'b'], ms: 100 }, { t: 500, f: 'c' }], 150) === 'b' && RC.trackAt([{ t: 0, f: ['a', 'b'], ms: 100 }, { t: 500, f: 'c' }], 600) === 'c', 'face 軌（陣列輪播／切換）');
ok(RC.trackAt([{ t: 100, f: 'x' }], 50) === null, '軌未開始 → null');
const cl = { dur: 1000, loop: true, events: [{ id: 'pat', t: 300, repeatEvery: 1000 }, { id: 'line:x', t: 200 }] };
ok(RC.evalClip(cl, 2500).t === 500 && RC.evalClip(cl, 2500).done === false, 'loop clip 時間取餘');
ok(RC.evalClip({ dur: 400 }, 900).done === true, '非 loop clip 完咗 done');
const ev = RC.eventsBetween(cl, 0, 2400).filter(e => e.id === 'pat').map(e => e.t);
ok(JSON.stringify(ev) === '[300,1300,2300]', 'repeatEvery 事件', ev);
ok(RC.eventsBetween(cl, 0, 199).length === 0 && RC.eventsBetween(cl, 199, 200).some(e => e.id === 'line:x'), '一次性事件 (prev, ms]');
let X = RC.xform({ sx: 1, sy: 1, rot: 90, x: 0, y: 0, flip: 0 }, [0, -10]); let p = X.map([0, -10]);
ok(near(p[0], 0) && near(p[1], -10), 'xform：origin 點不動', p);
p = X.map([0, 0]); ok(near(p[0], -10) && near(p[1], -10), 'xform：順時針 90° 繞 origin', p);
X = RC.xform({ sx: 2, sy: 1, rot: 0, x: 3, y: 0, flip: 1 }, [0, 0]); p = X.map([1, 0]); ok(near(p[0], 1) && X.sx === -2, 'xform：flip＋scale＋平移', p);
const fx = RC.evalClip({ dur: 1000, fx: [{ id: 'fx_a', t0: 100, t1: 600, ms: 100, loop: false, move: [[0, 0, 0], [400, 10, -4]] }] }, 300, { frameInfo: () => ({ frames: 3 }) }).fx[0];
ok(fx && fx.frame === 2 && near(fx.dx, 5) && near(fx.dy, -2) && fx.z === 'front' && fx.follow === true, 'fx 幀（唔 loop 停最後）＋move 插值＋預設', fx);
ok(RC.evalClip({ dur: 1000, fx: [{ id: 'fx_a', t0: 100, t1: 200 }] }, 300).fx.length === 0, 'fx 時段外唔出');

console.log('— art/reactions 資料');
const R = J('reactions.json'), A = J('anchors.json'), FX = J('fx/fx.json'), SE = J('series/series.json');
const CL = R.clips, names = Object.keys(CL);
ok(names.length === 16, '16 個 clip', names.length);
const forms = Object.keys(A).filter(k => !k.startsWith('_'));
ok(forms.length === 25, '25 隻舊線 form 有 anchors', forms.length);
ok(forms.filter(f => /^evo_/.test(f)).every(f => D.FORMS[f] && D.FORMS[f].evo), '每個 evo_* anchors form 喺 D.FORMS（evo）', forms.filter(f => /^evo_/.test(f) && !D.FORMS[f]));
const missing = [];
for (const f of forms) { const a = A[f]; for (const p of [a.faces.file, a.wear.glasses, a.wear.hat, a.paw.file]) if (!fs.existsSync(path.join(RX, p))) missing.push(p); if (!SE[a.series]) missing.push('series ' + a.series); }
ok(missing.length === 0, '每隻 form 嘅 faces／wear／paw 圖同 series 存在', missing.slice(0, 5));
const badSz = forms.filter(f => { const a = A[f], [w, h] = pngWH(path.join(RX, a.faces.file)); return w % a.frameSize[0] || h % a.frameSize[1] || (w / a.frameSize[0]) * (h / a.frameSize[1]) < a.faces.order.length; });
ok(badSz.length === 0, 'faces 圖尺寸＝frameSize 格 × order 數', badSz);
const needA = ['headTop', 'face', 'pivot', 'center', 'side_l', 'side_r'];
ok(forms.every(f => needA.every(k => Array.isArray(A[f].anchors[k]))), '每隻 form 有基本 anchors');
const faceUsed = new Set(), fxUsed = new Set(), wearUsed = new Set(), ancUsed = new Set();
for (const n of names) { const c = CL[n]; for (const k of c.face || []) [].concat(k.f).forEach(x => x != null && faceUsed.add(x)); for (const f of c.fx || []) { fxUsed.add(f.id); ancUsed.add(f.anchor || 'pivot'); } for (const w of c.wear || []) wearUsed.add(w.id); if (c.origin) ancUsed.add(c.origin); }
const fBad = forms.map(f => [f, [...faceUsed].filter(x => !A[f].faces.order.includes(x))]).filter(x => x[1].length);
ok(fBad.length === 0, 'clip 用到嘅 face 名（' + faceUsed.size + '）每隻 form 都有', fBad.slice(0, 3));
const fxBad = [...fxUsed].filter(id => !(id === 'paw' || id === 'series_orbit' || id === 'series_puff' || FX[id]));
ok(fxBad.length === 0, 'clip 用到嘅 fx id 全部解析到', fxBad);
const fxFile = Object.keys(FX).filter(k => FX[k] && FX[k].file && !fs.existsSync(path.join(RX, 'fx', FX[k].file)) && !fs.existsSync(path.join(RX, FX[k].file)));
ok(fxFile.length === 0, 'fx.json 每個圖檔存在', fxFile.slice(0, 5));
ok([...wearUsed].every(w => w === 'glasses' || w === 'hat'), 'wear id 只係 glasses／hat', [...wearUsed]);
const aBad = [...ancUsed].filter(k => k !== 'touch' && !forms.every(f => A[f].anchors[k]));
ok(aBad.length === 0, 'clip 用到嘅 anchor 每隻 form 都有（touch 例外）', aBad);
const lines = names.filter(n => (CL[n].events || []).some(e => /^line:/.test(e.id)));
ok(names.every(n => !(CL[n].fx || []).some(f => /text|line/i.test(f.id))), '對白只經 line:* 事件（fx 冇字）');
console.log('    有 line 事件嘅 clip：' + lines.join(', '));
for (const n of names) { const c = CL[n], e = RC.evalClip(c, (c.dur || 0) / 2); if (!(e && e.body && isFinite(e.body.rot))) { ok(false, n + ' evalClip'); } }
ok(true, '16 個 clip evalClip 中段冇 NaN');
ok(CL.touch_tickle_roll.rotStep === 45 && CL.touch_tickle_roll.groundLock, '碌地 rotStep 45＋groundLock');

console.log('— MOTIONS ↔ clip');
const mk = Object.keys(T.MOTIONS).filter(k => T.MOTIONS[k].clip);
ok(mk.length >= 15, 'MOTIONS 有 clip 嘅動作 ≥15', mk.length);
ok(mk.every(k => CL[T.MOTIONS[k].clip]), '每個 MOTIONS.clip 喺 reactions.json', mk.filter(k => !CL[T.MOTIONS[k].clip]));
ok(names.every(n => mk.some(k => T.MOTIONS[k].clip === n)), '16 個 clip 全部有 MOTIONS 用', names.filter(n => !mk.some(k => T.MOTIONS[k].clip === n)));
const TA = D.PARAMS.touch.art;
ok(TA && TA.enabled === true && TA.rotStep === 45 && TA.base === 'art/reactions/', 'PARAMS.touch.art', TA);
ok(['nuzzle', 'nuzzle_purr', 'rush', 'reunion_happy'].every(k => TA.yieldTo.includes(k)), '反應 clip 讓位畀 s3 專屬 clip（yieldTo）', TA.yieldTo);
const m = T.motionAt('g_roll', 0, 1.2); ok(m && m.clip === 'touch_tickle_roll' && near(m.ms, 1200, 1), 'motionAt 回 clip＋ms', m);
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
