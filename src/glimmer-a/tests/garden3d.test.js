/* garden3d.test — #89 3D 花園 H1／H1.2／H1.3／H1.4 純邏輯（座標、鏡頭、可見區、碰撞、方向、日夜、畫質、行速、自主行、世界物件）。node tests/garden3d.test.js */
const G3 = require('../src/garden3d.js');
const D = require('../src/data.js');
const BEH = require('../src/behavior.js');
const fs = require('fs');
const path = require('path');
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m + (x !== undefined ? '  → ' + JSON.stringify(x) : '')); } };
const near = (a, b, e) => Math.abs(a - b) <= (e == null ? 1e-6 : e);

console.log('① 座標');
{
  ok(G3.CX === 97 && G3.GROUND_Y === 292 && G3.ZSCALE === 1.6 && G3.W === 195 && G3.H === 422, '美術格 195×422、原點 (97,292)、z 倍率 1.6');
  const w = G3.artToWorld(97, 292); ok(w.x === 0 && w.z === 0, '腳底 → 世界原點', w);
  const w2 = G3.artToWorld(97 + 10, 292 + 10); ok(w2.x === 10 && near(w2.z, 16), 'art +10,+10 → x=10, z=16', w2);
  const a = G3.worldToArtFlat(10, 16); ok(a.x === 107 && near(a.y, 302), '來回轉換', a);
  const p = G3.petWorld({ x: -20, depth: 5 }); ok(p.x === -20 && near(p.z, 8), 'beh.x／depth → 世界', p);
}

console.log('② 日夜光');
{
  ok(G3.nightMix(8) === 0 && G3.nightMix(13) === 0, '朝／午＝日');
  ok(near(G3.nightMix(17.5), 0.5), '17:30 黃昏 0.5', G3.nightMix(17.5));
  ok(G3.nightMix(22) === 1 && G3.nightMix(3) === 1, '夜＝1');
  const L = { sun: { dir: [0, -1, 0], color: '#ffffff', intensity: 1, ambient: { color: '#cfe0f0', intensity: 0.55 }, shadowIntensity: 0.3 },
    fill: { dir: [0, 0, -1], color: '#ffe2c4', intensity: 0.38, intensityNight: 0 },
    night: { sun: 0.12, ambient: '#4a5a90', ambientIntensity: 0.35 },
    lights: [{ id: 'lamp', x: 0, y: 1, z: 0, color: '#ffd890', radius: 70, intensity: 0, intensityNight: 1.2, flicker: 0 },
      { id: 'window_side', x: 114, y: 57, z: -72, color: '#ffc870', radius: 40, intensity: 0, intensityNight: 0.7, flicker: 0 }] };
  const D = G3.mixLights(L, 0), N = G3.mixLights(L, 1);
  ok(D.sun === 1 && N.sun === 0.12 && D.fill === 0.38 && N.fill === 0, '日／夜 sun＋fill', { D: [D.sun, D.fill], N: [N.sun, N.fill] });
  ok(D.byId.lamp === 0 && N.byId.lamp === 1.2 && N.byId.window_side === 0.7 && D.byId.window_side === 0, '燈：日 0、夜 intensityNight（含 window_side）', { D: D.byId, N: N.byId });
  ok(D.shadowIntensity === 0.3, 'shadowIntensity 0.3');
}

console.log('③ 鏡頭 sway／follow');
{
  const cam = { target: [0, 30, -72], pitchDeg: 30, dist: 580, fovDeg: 40, orbitMinDeg: -10, orbitMaxDeg: 10,
    swayAmplitudeDeg: 5, swayHalfPeriodSec: 6, followDamping: 2, followWeight: [0.25, 0.3], followOffset: [-20, 0], followOrigin: [-110, -40] };
  ok(near(G3.swayYaw(0, cam), -5) && near(G3.swayYaw(3, cam), 0) && near(G3.swayYaw(6, cam), 5) && near(G3.swayYaw(12, cam), -5), 'yaw＝−A·cos(πt/T) 0→−5、3s→0、6s→+5、12s→−5', [G3.swayYaw(0, cam), G3.swayYaw(3, cam), G3.swayYaw(6, cam), G3.swayYaw(12, cam)]);
  const camOld = Object.assign({}, cam, { followEstablish: false });
  const des0 = G3.followDesired(camOld, { x: 0, z: 0 });
  ok(near(des0[0], 7.5) && des0[1] === 30 && near(des0[2], -60), 'followEstablish:false 原點 desired＝target＋offset＋weight·(0−origin)', des0);
  const step = G3.followStep([0, 30, -72], [10, 30, -60], 0.5, 2);
  const k = 1 - Math.exp(-2 * 0.5);
  ok(near(step[0], 0 + 10 * k) && near(step[2], -72 + 12 * k), '跟拍 cam+=(desired−cam)·(1−exp(−2dt))', step);
  const P0 = G3.camPos([0, 30, -72], 0, cam);
  ok(near(P0[0], 0) && P0[1] > 30 && P0[2] > -72, 'yaw 0：鏡頭喺 target 右上前方（+Y+Z）', P0);
  ok(G3.clampYaw(8, cam, 5) === 10 && G3.clampYaw(-8, cam, -5) === -10, '手拉＋自動擺夾喺 ±10°');
}

console.log('④ dir4 方向');
{
  const s = G3.dirOf(10, 0, true); ok(s.dir === 'side' && s.flip === false && s.clip === 'walk', '向右行＝side', s);
  const l = G3.dirOf(-4, 1, true); ok(l.dir === 'side' && l.flip === true, '向左行＝side 鏡像', l);
  const f = G3.dirOf(0, 5, false); ok(f.dir === 'front' && f.flip === false && f.clip === 'idle', '向鏡頭停＝front idle', f);
  const b = G3.dirOf(1, -8, true); ok(b.dir === 'back' && b.clip === 'walk', '向屋行＝back walk', b);
  ok(G3.frameName({ dir: 'front', clip: 'idle' }, 0) === 'front_idle_01', 't=0 → 01');
  ok(G3.frameName({ dir: 'side', clip: 'walk' }, 0.5) === 'side_walk_06', 'walk 10fps、0.5s → 第 6 幀', G3.frameName({ dir: 'side', clip: 'walk' }, 0.5));
}

console.log('⑤ 碰撞 footprint');
{
  const objs = [
    { id: 'tree', footprint: { type: 'rect', x: [-98, -78], z: [-53, -35], pad: 3 } },
    { id: 'cottage', footprint: { type: 'rect', x: [53, 112], z: [-94, -50], pad: 4 } },
    { id: 'pot_S', footprint: { type: 'poly', points: [[49, 27], [52.54, 25.54], [54, 22], [52.54, 18.46], [49, 17], [45.46, 18.46], [44, 22], [45.46, 25.54]], pad: 2 } },
    { id: 'lanterns', backfill: false },
    { id: 'bush_bR', backfill: true, footprint: { type: 'rect', x: [0, 10], z: [0, 10], pad: 0 } }
  ];
  ok(G3.blocked(objs, 0, 0, 10).length === 0, '原點唔撞', G3.blocked(objs, 0, 0, 10));
  ok(G3.blocked(objs, -88, -44, 10).indexOf('tree') >= 0, '企入樹幹會被擋', G3.blocked(objs, -88, -44, 10));
  ok(G3.blocked(objs, 82.5, -72, 10).indexOf('cottage') >= 0, '企入屋會被擋', G3.blocked(objs, 82.5, -72, 10));
  ok(G3.blocked(objs, 49, 22, 10).indexOf('pot_S') >= 0, '花盆多邊形碰撞', G3.blocked(objs, 49, 22, 10));
  ok(G3.blocked(objs, 5, 5, 10).indexOf('bush_bR') < 0 && G3.blocked(objs, 0, -46, 10).indexOf('lanterns') < 0, '補位件／吊燈冇 footprint');
}

console.log('⑤b XZ 走位／繞障／揀目標');
{
  const oj = require('../art/garden3d/H1/objects.json');
  const objs = oj.objects;
  const RX = G3.RANGE3.x, RZ = G3.RANGE3.z;
  const s0 = G3.stepXZ(objs, 0, 0, 10, 0, 2, 10, RX, RZ);
  ok(s0.x > 0 && Math.abs(s0.z) < 0.01 && !s0.arrived, '沿 +X 行一步', s0);
  const sZ = G3.stepXZ(objs, 0, 0, 0, 20, 2, 10, RX, RZ);
  ok(sZ.z > 0 && Math.abs(sZ.x) < 0.01, '沿 +Z（向鏡頭）行一步', sZ);
  const sB = G3.stepXZ(objs, 0, 10, 0, 0, 2, 10, RX, RZ);
  ok(sB.z < 10 && sB.dz < 0, '沿 −Z（向屋）行', sB);
  // 唔可以踏入樹幹（由樹前方一步步行近）
  const into = G3.stepXZ(objs, -88, -10, -88, -44, 2, 10, RX, RZ);
  ok(G3.blocked(objs, into.x, into.z, 10).indexOf('tree') < 0, '一步唔會踏入樹 footprint', into);
  // 由原點繞去小屋後／樹後（A* 路徑）
  function followTo(tx, tz) {
    const path = G3.buildPath(objs, 0, 0, tx, tz, 10, RX, RZ);
    let x = 0, z = 0, pi = 0, arr = false, hit = false;
    for (let i = 0; i < 2500; i++) {
      const fol = G3.followPath(objs, x, z, path, { x: tx, z: tz }, 2, 10, RX, RZ, pi);
      pi = fol.pi; x = fol.step.x; z = fol.step.z;
      if (G3.blocked(objs, x, z, 10).length) { hit = true; break; }
      if (fol.step.arrived) { arr = true; break; }
    }
    return { x: x, z: z, arr: arr, hit: hit, n: path && path.length };
  }
  const c = followTo(82, -110);
  ok(c.arr && !c.hit && Math.hypot(c.x - 82, c.z + 110) < 3, '繞過圍欄／小屋到達 (82,−110)', c);
  const tr = followTo(-88, -80);
  ok(tr.arr && !tr.hit && Math.hypot(tr.x + 88, tr.z + 80) < 3, '繞到樹後 (−88,−80)', tr);
  const pw = G3.petWorld({ x: 10, z: -40 });
  ok(pw.x === 10 && pw.z === -40, 'petWorld 用 3D z（唔使 depth×1.6）', pw);
  const pw2 = G3.petWorld({ x: 4, depth: 5 });
  ok(pw2.z === 5 * G3.ZSCALE, '冇 z 時仍用 depth×ZSCALE', pw2);
  const rng = (function () { let i = 0; return function () { i = (i * 1103515245 + 12345) & 0x7fffffff; return (i >>> 0) / 0x7fffffff; }; }());
  const pick = G3.pickWalk(objs, rng, { x: 0, z: 0 }, 10, G3.RANGE3);
  ok(pick && G3.blocked(objs, pick.x, pick.z, 10).length === 0, 'pickWalk 落喺可企位', pick);
}

console.log('⑥ 畫質自動');
{
  ok(G3.detectQuality({ qs: { '3d': '0' }, webgl: true }).want === false && G3.detectQuality({ qs: { '3d': '0' } }).reason === 'off', '?3d=0 → 2D');
  ok(G3.detectQuality({ webgl: false }).quality === 'low' && G3.detectQuality({ webgl: false }).reason === 'nowebgl', '冇 WebGL → 2D');
  const lo = G3.detectQuality({ webgl: true, hardwareConcurrency: 4, deviceMemory: 3 });
  ok(lo.want === false && lo.quality === 'low' && lo.reason === 'lowend', '低端機（≤4 核或 ≤4GB）自動 2D', lo);
  const hi = G3.detectQuality({ webgl: true, hardwareConcurrency: 8, deviceMemory: 8 });
  ok(hi.want === true && hi.quality === 'high', '中高階自動 3D high', hi);
  ok(G3.detectQuality({ qs: { '3d': 'mid' }, webgl: true, hardwareConcurrency: 2 }).quality === 'mid', '?3d=mid 覆蓋低端');
  ok(G3.QSET.high.tex3x && !G3.QSET.mid.tex3x && G3.QSET.high.shadow > G3.QSET.mid.shadow, 'high＝@3x＋大影圖、mid＝1x＋細影');
}

console.log('⑦ H1.2 可見區構圖／跟拍建立鏡頭');
{
  const cam = { target: [0, 30, -72], pitchDeg: 30, dist: 580, fovDeg: 40, orbitMinDeg: -10, orbitMaxDeg: 10,
    swayAmplitudeDeg: 5, swayHalfPeriodSec: 6, followDamping: 2, followWeight: [0.25, 0.3], followOffset: [-20, 0], followOrigin: [-110, -40] };
  const or = G3.followOriginOf(cam);
  ok(near(or[0], -80) && near(or[1], 0), '預設 origin＝home＋offset/weight → (−80, 0)', or);
  const des = G3.followDesired(cam, { x: 0, z: 0 });
  ok(near(des[0], 0) && des[1] === 30 && near(des[2], -72), '寵物喺家時 look＝建立鏡頭 target', des);
  const far = G3.followDesired(cam, { x: 200, z: -200 });
  ok(near(far[0], 18) && near(far[2], -84), '跟拍鉗制 ±18x／±12z', far);
  const noc = G3.followDesired(Object.assign({}, cam, { followClamp: false }), { x: 200, z: -200 });
  ok(noc[0] > 18 && noc[2] < -84, 'followClamp:false 唔鉗', noc);
  ok(G3.VIS.x === 2 && G3.VIS.y === 64 && G3.VIS.w === 152 && G3.VIS.h === 278, 'VIS 讓過頂欄／頭像／rail／底欄', G3.VIS);
  const vf = G3.visFov();
  ok(near(vf.hfovDeg, 29) && vf.vfovDeg > 49 && vf.vfovDeg < 52, '可見區 hFOV 29° → vFOV ~50.6°', vf);
  const vo = G3.viewOffset();
  ok(vo.fullWidth === 152 && vo.fullHeight === 278 && vo.x === -2 && vo.y === -64 && vo.width === 195 && vo.height === 422, 'setViewOffset 參數：optical center 喺 VIS 中心', vo);
}

console.log('⑧ H1.2 光影／行速／網格常數');
{
  ok(near(G3.srgbToLinear(1), 1) && G3.srgbToLinear(0) === 0 && G3.srgbToLinear(0.5) > 0.2 && G3.srgbToLinear(0.5) < 0.25, 'sRGB→linear 轉折');
  const si = G3.shadowIntensityLin(0.3);
  ok(si > 0.54 && si < 0.56, 'shadowIntensity 0.3 → linear ~0.552', si);
  const n1 = G3.nightBackdropFactor(1);
  ok(near(n1[0], G3.srgbToLinear(0.22)) && near(n1[1], G3.srgbToLinear(0.26)) && near(n1[2], G3.srgbToLinear(0.42)), '夜空 sRGB 乘 [.22,.26,.42] 再轉 linear', n1);
  const n0 = G3.nightBackdropFactor(0);
  ok(near(n0[0], 1) && near(n0[1], 1) && near(n0[2], 1), '日間背景乘數＝1', n0);
  ok(G3.WALK_SPEED_2D === 15 && G3.WALK_SPEED_3D === 20 && near(G3.walkStep3d(15), 20) && near(G3.walkStep3d(1), 20/15), '3D 行速 20；g3dWalk 將 2D 步長 ×20/15');
  ok(G3.pointScale('jar') < G3.pointScale('lamp') && G3.emissiveScale('jar') < 1 && G3.emissiveScale('lamp') > 1 && G3.emissiveScale('lantern_1') > 1.5, '夜燈：燈籠／燈柱加強、螢火瓶減弱');
}

console.log('⑨ H1.2／QA：擋住目標吸位、hook 掛 beh、behavior.step 行 3D');
{
  const oj = require('../art/garden3d/H1/objects.json');
  const objs = oj.objects, RX = G3.RANGE3.x, RZ = G3.RANGE3.z;
  const snH = G3.snapDest(objs, 82.5, -72, 10, RX, RZ);
  ok(snH.snapped && !G3.blocked(objs, snH.x, snH.z, 10).length, '小屋中心吸到可企位', snH);
  ok(Math.hypot(snH.x - 82.5, snH.z + 72) <= G3.NEAR_FREE_R * 8 + 1, '吸位喺 12 格內', snH);
  const pathH = G3.buildPath(objs, 0, 0, 82.5, -72, 10, RX, RZ);
  const endH = pathH[pathH.length - 1];
  ok(pathH.length >= 2 && !G3.blocked(objs, endH.x, endH.z, 10).length, '小屋路徑唔退化、終點可企', { n: pathH.length, end: endH });
  let x = 0, z = 0, pi = 0, arr = false, hit = false, stall = 0;
  for (let i = 0; i < 2500; i++) {
    const fol = G3.followPath(objs, x, z, pathH, { x: 82.5, z: -72 }, 2, 10, RX, RZ, pi, stall);
    pi = fol.pi; stall = fol.stall || 0; x = fol.step.x; z = fol.step.z;
    if (G3.blocked(objs, x, z, 10).length) { hit = true; break; }
    if (fol.step.arrived) { arr = true; break; }
  }
  ok(arr && !hit, '行到小屋附近可企位（唔喺圍欄前打轉）', { arr: arr, hit: hit, x: x, z: z, d: Math.hypot(x - snH.x, z - snH.z) });

  const snP = G3.snapDest(objs, 49, 22, 10, RX, RZ);
  ok(snP.snapped && !G3.blocked(objs, snP.x, snP.z, 10).length, '花盆中心吸到可企位', snP);

  const behP = D.PARAMS.beh;
  const prev = { g3dOn: behP.g3dOn, g3dWalk: behP.g3dWalk, g3dPickWalk: behP.g3dPickWalk, g3dSpot: behP.g3dSpot, g3dClampX: behP.g3dClampX };
  const parent = D.PARAMS;
  const prevP = { g3dOn: parent.g3dOn, g3dWalk: parent.g3dWalk, g3dPickWalk: parent.g3dPickWalk, g3dSpot: parent.g3dSpot, g3dClampX: parent.g3dClampX };
  const S = { on: function () { return true; }, objects: objs, objJ: oj };
  G3.bindBehHooks(behP, S);
  ok(typeof behP.g3dWalk === 'function' && typeof parent.g3dWalk !== 'function', '五個 hook 掛喺 PARAMS.beh，唔喺 PARAMS');
  const b = BEH.create(11);
  const s = require('../src/sim.js').newState(1e12, 5);
  s.stage = 'adult'; s.form = 'radiant'; s.sleeping = false;
  Object.assign(s.needs, { mood: 90, energy: 90, hunger: 90, clean: 90 });
  const ctx = { s: s, pw: {}, sun: 1, override: null, event: null };
  b.x = 0; b.z = 0; b.tx = 20; b.tz = 36; b.speed = behP.walkSpeed; b.state = 'walk'; b.phase = '';
  const z0 = b.z;
  for (let i = 0; i < 90; i++) BEH.step(b, ctx);
  ok(b.z > z0 + 4 && Math.abs(b.x - 20) < 18, 'behavior.step 經 g3dWalk 用 XZ 走位（z 會變）', { x: b.x, z: b.z, state: b.state });
  const spd = Math.hypot(b.x, b.z - z0) / (90 * BEH.FIX);
  ok(spd > 16 && spd < 24, '3D 行速約 20 u/s（經 behavior.step）', spd);

  const b2 = BEH.create(3, { personality: { sticky: 1, sleepy: 0, timid: 0 } });
  b2.x = 0; b2.z = 0; b2.rng = function () { return 0; };
  BEH.tap(b2, 'ground', 20, 0, { z: 36 });
  BEH.step(b2, ctx);
  ok(b2.tx === 20 && b2.tz === 36 && b2.state === 'follow', '點地寫 tz（唔淨係 tx）', { tx: b2.tx, tz: b2.tz, state: b2.state });

  S.on = function () { return false; };
  const clamped = behP.g3dClampX(999);
  ok(Number.isFinite(clamped) && clamped === behP.rangeX[1], 'g3dClampX 2D 分支用 beh.rangeX（唔係 NaN）', clamped);

  ['g3dOn', 'g3dWalk', 'g3dPickWalk', 'g3dSpot', 'g3dClampX'].forEach(function (k) {
    if (prev[k] === undefined) delete behP[k]; else behP[k] = prev[k];
    if (prevP[k] === undefined) delete parent[k]; else parent[k] = prevP[k];
  });
}

console.log('⑩ H1.3／H1.4 自主行／世界物件／影圖／LICENSE／雨');
{
  ok(G3.QSET.mid.shadow === 256 && G3.QSET.mid.shadowEvery === 1 && G3.QSET.mid.softShadow === false, 'mid 影圖 256、每幀、PCF', G3.QSET.mid);
  ok(G3.QSET.high.shadow === 2048 && G3.QSET.high.shadowEvery === 3 && G3.QSET.high.softShadow === false, 'high 影圖 2048、每 3 幀、關 soft shadow', G3.QSET.high);
  ok(G3.ACTOR_ALPHA_SOFT === 0.1, '半透明 actor alphaTest 0.1', G3.ACTOR_ALPHA_SOFT);
  const soft = G3.actorMatOpts({ alpha: 0.45 }), hard = G3.actorMatOpts({ kind: 'poop' });
  ok(soft.alphaTest === 0.1 && soft.transparent && !soft.depthWrite, '影子 material：alphaTest 0.1＋transparent', soft);
  ok(hard.alphaTest === 0.5 && !hard.transparent && hard.depthWrite, '實心 actor 仍 alphaTest 0.5', hard);
  ok(G3.RAIN && G3.RAIN.size >= 4 && G3.RAIN.sizeAttenuation === false && G3.RAIN.n >= 180, '雨點加大、螢幕像素、數量 ≥180', G3.RAIN);
  ok(G3.WORLD_ITEMS.length >= 20, 'WORLD_ITEMS 盤點齊', G3.WORLD_ITEMS.length);
  const garden = G3.worldInGarden();
  const ids = garden.map(x => x.id);
  ['pet', 'kid', 'poop', 'visitor', 'shadow', 'weather', 'decor', 'ball', 'food', 'event'].forEach(function (id) {
    ok(ids.indexOf(id) >= 0, '花園清單有 ' + id);
  });
  ok(G3.worldItem('souvenir') && G3.worldItem('souvenir').inGarden === false, '手信唔落地（屋仔家具）');
  ok(G3.worldItem('foodBowl') && G3.worldItem('foodBowl').inGarden === false, '2D 冇常駐食碗');
  const pw = G3.poopWorld(0);
  ok(pw && near(pw.x, 50 - 97) && near(pw.z, (304 - 292) * 1.6), 'poopWorld(0) 對應槽位', pw);
  ok(!G3.shouldForceWalk({ state: 'stay', lastWalkAt: 0, stateT: 2 }, 2), '企未夠 3.2s 唔強制行');
  ok(G3.shouldForceWalk({ state: 'stay', lastWalkAt: 0, stateT: 2 }, 4), '企超過 3.2s 強制行');
  ok(!G3.shouldForceWalk({ state: 'stay', variant: 'sniff', lastWalkAt: 0, stateT: 5 }, 10), 'variant 中唔打斷');
  ok(!G3.shouldForceWalk({ state: 'sleep', lastWalkAt: 0, stateT: 5 }, 10), '非 stay 唔強制行');
  const ww = G3.wanderWeights({ walk: 15, stay: 40, sniff: 10 });
  ok(near(ww.walk, 15 * 2.6) && near(ww.stay, 40 * 0.4) && ww.sniff === 10, '3D wander 權重：walk×2.6 stay×0.4', ww);
  const lic = path.join(__dirname, '../src/vendor/LICENSE.three.txt');
  ok(fs.existsSync(lic) && fs.statSync(lic).size > 200, 'repo 有 three.js LICENSE', lic);
}

console.log('—' + (fail ? ' 失敗 ' + fail : ' 通過') + '／' + (pass + fail) + '—');
process.exit(fail ? 1 : 0);
